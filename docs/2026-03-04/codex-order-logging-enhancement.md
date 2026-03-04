# Codex Order: 로깅 강화 — 실패 학습 기반 진단 시스템

> **목적**: "어떤 스테이지가 왜 어떻게 실패하는가. 어떤 LLM이 어떤 자료를 왜 잘못받았는가."
>   현재 로깅은 무엇이 일어났는지는 기록하나 왜 반복 실패하는지 역추적 불가.
>   이 오더 완료 후 `python -c "from modules.core.failure_analyzer import FailureAnalyzer; ..."` 한 줄로 실패 패턴 분석 가능해야 함.
> **금지**: 기존 LLM 프롬프트 내용 변경. 기존 DB 컬럼 삭제. 기존 테이블 스키마 파괴적 변경.
> **출력 보고서**: `docs/2026-03-04/logging-enhancement-result.md`

---

## 0) 강제 제약

- `python -m py_compile <수정파일>` 각 Phase 후 통과 필수.
- `pytest tests/ -q` 기준선: **3227 passed, 0 failed**.
- `ruff check modules/ tests/` 위반 0건.
- **비치명 원칙**: 로깅 실패가 파이프라인을 절대 중단하면 안 됨. 모든 로깅 코드는 `try/except Exception` 으로 보호.

---

## 1) 현재 상태 파악 (수동 검사 필수)

구현 전 아래를 직접 읽어라:

```
파일: modules/core/db_manager.py
읽을 범위:
  - initialize_db() 전체 (DDL 정의 확인)
  - cost_log 테이블 DDL 존재 여부 확인

파일: modules/domain/agents/base_agent.py
읽을 범위:
  - ask() 메서드 전체 (LLM 호출 지점 확인)
  - _ask_with_* 메서드들 (실제 API 호출 지점)

파일: modules/core/session_logger.py
읽을 범위:
  - log_llm_io() 메서드 시그니처와 기록 필드
  - log_decision() 메서드 시그니처와 기록 필드
```

확인 사항:
- `base_agent.ask()`의 실제 API 호출 완료 시점 (응답 수신 후 어디서 return?)
- `session_logger`가 `base_agent`에 이미 연결되어 있는지 여부
- `director_selections` 테이블 DDL의 현재 컬럼 목록
- `quality_metrics.jsonl`에 Stage 2/3 레코드가 실제로 기록되는 코드 경로 존재 여부

---

## 2) Phase 1 — `llm_calls` 테이블 신설 + BaseAgent 계측

### 목적
모든 LLM 호출을 DB에 기록. "어떤 에이전트가 어떤 모델로 몇 토큰을 써서 얼마나 걸렸고 성공했는가."

### 변경 대상 A: `modules/core/db_manager.py`

`initialize_db()` 안에 테이블 DDL 추가:

```sql
CREATE TABLE IF NOT EXISTS llm_calls (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT,
    ts          TEXT NOT NULL,
    stage       INTEGER,          -- 0/2/3/4 (알 수 없으면 NULL)
    ep_num      INTEGER,
    agent_name  TEXT NOT NULL,    -- "director", "chief_writer", "analyst" 등
    model       TEXT NOT NULL,    -- 실제 model id 문자열
    prompt_chars INTEGER,         -- 프롬프트 문자 수 (토큰 추정용)
    response_chars INTEGER,       -- 응답 문자 수
    duration_ms  INTEGER,         -- 호출 소요 시간
    success      INTEGER NOT NULL DEFAULT 1,  -- 1=성공, 0=실패
    error_type   TEXT,            -- 예외 클래스명 (실패 시)
    error_msg    TEXT,            -- 예외 메시지 요약 80자
    verdict      TEXT,            -- 응답에서 파싱된 verdict (있는 경우만)
    context_tag  TEXT             -- 호출 목적 레이블 (예: "arc_draft", "manuscript_audit")
)
```

인덱스 추가:
```sql
CREATE INDEX IF NOT EXISTS idx_llm_calls_agent ON llm_calls(agent_name);
CREATE INDEX IF NOT EXISTS idx_llm_calls_ep ON llm_calls(ep_num);
CREATE INDEX IF NOT EXISTS idx_llm_calls_ts ON llm_calls(ts);
```

저장 메서드 추가:

```python
def save_llm_call(
    self,
    agent_name: str,
    model: str,
    prompt_chars: int,
    response_chars: int,
    duration_ms: int,
    success: bool = True,
    error_type: str | None = None,
    error_msg: str | None = None,
    stage: int | None = None,
    ep_num: int | None = None,
    verdict: str | None = None,
    context_tag: str | None = None,
    session_id: str | None = None,
) -> None:
    """[Log-1] LLM 호출 1건 기록. 비치명 — 실패 시 debug 로그만."""
    try:
        ts = datetime.now().isoformat(timespec="seconds")
        with self._lock:
            self.cursor.execute(
                """INSERT INTO llm_calls
                   (session_id, ts, stage, ep_num, agent_name, model,
                    prompt_chars, response_chars, duration_ms,
                    success, error_type, error_msg, verdict, context_tag)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (session_id, ts, stage, ep_num, agent_name, model,
                 prompt_chars, response_chars, duration_ms,
                 1 if success else 0, error_type,
                 (error_msg or "")[:80], verdict, context_tag),
            )
            self.conn.commit()
    except Exception as _e:
        logging.debug("[llm_calls] save_llm_call 실패 (비치명): %s", _e)
```

### 변경 대상 B: `modules/domain/agents/base_agent.py`

`ask()` 메서드 (또는 실제 API 호출 완료 지점)에 계측 추가:

**패턴**: API 호출 직전 `time.monotonic()` 시작, 완료 후 경과 시간 계산, DB 기록.

```python
# ask() 또는 _ask_with_retry() 등 실제 응답 수신 지점에 삽입:
_t0 = time.monotonic()
try:
    response = <기존 API 호출>
    _duration_ms = int((time.monotonic() - _t0) * 1000)
    _db = getattr(getattr(self, "project", None), "db", None)
    if _db and hasattr(_db, "save_llm_call"):
        try:
            _prompt_chars = len(str(prompt)) if prompt else 0
            _resp_chars = len(str(response)) if response else 0
            _db.save_llm_call(
                agent_name=self.__class__.__name__.lower(),
                model=self._model or "",
                prompt_chars=_prompt_chars,
                response_chars=_resp_chars,
                duration_ms=_duration_ms,
                success=True,
                context_tag=getattr(self, "_current_context_tag", None),
            )
        except Exception:
            pass
except Exception as _api_err:
    _duration_ms = int((time.monotonic() - _t0) * 1000)
    _db = getattr(getattr(self, "project", None), "db", None)
    if _db and hasattr(_db, "save_llm_call"):
        try:
            _db.save_llm_call(
                agent_name=self.__class__.__name__.lower(),
                model=self._model or "",
                prompt_chars=len(str(prompt)) if prompt else 0,
                response_chars=0,
                duration_ms=_duration_ms,
                success=False,
                error_type=type(_api_err).__name__,
                error_msg=str(_api_err)[:80],
            )
        except Exception:
            pass
    raise
```

**주의**:
- `base_agent.py`의 실제 API 호출 지점 구조 확인 후 적용. 여러 경로(`_ask_with_cached_context`, `_ask_with_retry` 등)가 있으면 **공통 최하단 호출 1곳에만 삽입** (중복 기록 방지).
- `self._model` 또는 `self.model_tier` 또는 실제 사용 모델명 추출 방법 확인 후 적용.
- `time` 모듈이 base_agent.py에 이미 import되어 있는지 확인.

---

## 3) Phase 2 — `stage_attempts` 테이블 신설

### 목적
스테이지별 시도 단위 기록. "Stage 2가 Arc 5에서 3번 REJECT된 이유가 뭔가."

### 변경 대상: `modules/core/db_manager.py`

DDL:

```sql
CREATE TABLE IF NOT EXISTS stage_attempts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT,
    ts              TEXT NOT NULL,
    stage           INTEGER NOT NULL,   -- 2/3/4
    ep_num          INTEGER,
    arc_num         INTEGER,
    attempt_num     INTEGER NOT NULL DEFAULT 1,
    verdict         TEXT NOT NULL,      -- PASS/REJECT/PASS_WITH_FIX/ERROR
    score           INTEGER,
    failure_category TEXT,              -- FailureLearner 카테고리 or NULL
    reject_reason   TEXT,              -- Director reject reason 원문 (500자)
    fix_scope       TEXT,              -- inplace/partial/full/null
    model           TEXT,              -- 주 에이전트 모델
    duration_ms     INTEGER,           -- 스테이지 전체 소요 시간
    advisory_flags  TEXT               -- JSON: {"truth_gate":1,"npc_drift":0,...}
)
```

인덱스:
```sql
CREATE INDEX IF NOT EXISTS idx_stage_attempts_stage_ep ON stage_attempts(stage, ep_num);
CREATE INDEX IF NOT EXISTS idx_stage_attempts_verdict ON stage_attempts(verdict);
CREATE INDEX IF NOT EXISTS idx_stage_attempts_category ON stage_attempts(failure_category);
```

저장 메서드:

```python
def save_stage_attempt(
    self,
    stage: int,
    verdict: str,
    attempt_num: int = 1,
    ep_num: int | None = None,
    arc_num: int | None = None,
    score: int | None = None,
    failure_category: str | None = None,
    reject_reason: str | None = None,
    fix_scope: str | None = None,
    model: str | None = None,
    duration_ms: int | None = None,
    advisory_flags: dict | None = None,
    session_id: str | None = None,
) -> None:
    """[Log-2] 스테이지 시도 1건 기록. 비치명."""
    import json as _json
    try:
        ts = datetime.now().isoformat(timespec="seconds")
        _advisory_json = _json.dumps(advisory_flags, ensure_ascii=False) if advisory_flags else None
        with self._lock:
            self.cursor.execute(
                """INSERT INTO stage_attempts
                   (session_id, ts, stage, ep_num, arc_num, attempt_num,
                    verdict, score, failure_category, reject_reason,
                    fix_scope, model, duration_ms, advisory_flags)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (session_id, ts, stage, ep_num, arc_num, attempt_num,
                 verdict, score, failure_category,
                 (reject_reason or "")[:500], fix_scope, model,
                 duration_ms, _advisory_json),
            )
            self.conn.commit()
    except Exception as _e:
        logging.debug("[stage_attempts] save_stage_attempt 실패 (비치명): %s", _e)
```

### 호출 지점 추가

아래 파일의 verdict 확정 직후에 `save_stage_attempt()` 호출 추가:

| 파일 | 위치 | 기록 시점 |
|------|------|----------|
| `stage2_validation_pipeline.py` | Arc 최종 verdict 반환 직전 | stage=2 |
| `stage3_orchestrator.py` | Blueprint 최종 verdict 반환 직전 | stage=3 |
| `stage4_interview_round.py` | `_record_s4_attempt()` 호출 직후 | stage=4 |

**Stage 4 예시** (`_record_s4_attempt()` 직후에 추가):

```python
# 기존 _record_s4_attempt() 호출 직후:
try:
    _db = getattr(getattr(self.ctx, "current_project", None), "db", None)
    if _db and hasattr(_db, "save_stage_attempt"):
        _adv_flags = {
            "truth_gate": int(bool(_advisory_parts)),  # advisory chain 발동 여부
        }
        _db.save_stage_attempt(
            stage=4,
            verdict=verdict,
            attempt_num=round_num + 1,
            ep_num=next_ep,
            arc_num=round_ctx.arc_data.get("arc_no") if hasattr(round_ctx, "arc_data") else None,
            score=score,
            reject_reason=director_result.get("reason", "")[:500] if isinstance(director_result, dict) else "",
            fix_scope=director_result.get("fix_scope") if isinstance(director_result, dict) else None,
            advisory_flags=_adv_flags,
        )
except Exception as _sa_err:
    logging.debug("[stage_attempts] Stage4 기록 실패 (비치명): %s", _sa_err)
```

---

## 4) Phase 3 — `director_selections` 테이블 `advisory_warnings` 컬럼 추가

### 목적
"어떤 advisory 경고가 Director REJECT와 상관관계가 있는가."

### 변경 대상: `modules/core/db_manager.py`

`initialize_db()` 에 마이그레이션 추가:

```python
# director_selections에 advisory_warnings 컬럼 추가 (없으면)
try:
    self.cursor.execute(
        "ALTER TABLE director_selections ADD COLUMN advisory_warnings TEXT"
    )
    self.conn.commit()
except Exception:
    pass  # 이미 존재하면 무시
```

`save_director_selection()` 시그니처에 `advisory_warnings: dict | None = None` 파라미터 추가:

```python
def save_director_selection(
    self,
    ...,  # 기존 파라미터 유지
    advisory_warnings: dict | None = None,  # 추가
) -> None:
```

INSERT 문에 `advisory_warnings` 컬럼 추가 (JSON 직렬화):
```python
_adv_json = json.dumps(advisory_warnings, ensure_ascii=False) if advisory_warnings else None
# INSERT 문에 추가
```

### 호출 지점 수정

`stage4_interview_round.py`의 `save_director_selection()` 호출부에 `advisory_warnings` 전달:

```python
# _director_mc_parts에서 어떤 advisory가 발동됐는지 추출
_adv_summary = {}
for _part in (_advisory_parts or []):
    if "[TruthGate]" in str(_part):
        _adv_summary["truth_gate"] = 1
    if "[LM-B]" in str(_part) or "NpcDrift" in str(_part):
        _adv_summary["npc_drift"] = 1
    if "[LM-C]" in str(_part) or "NumericDrift" in str(_part):
        _adv_summary["numeric_drift"] = 1
    if "[LM-D]" in str(_part) or "RelDrift" in str(_part):
        _adv_summary["rel_drift"] = 1
    if "[LM-E]" in str(_part) or "Flashback" in str(_part):
        _adv_summary["flashback"] = 1
    if "[LM-F]" in str(_part) or "InfoParadox" in str(_part):
        _adv_summary["info_paradox"] = 1
    if "[LM-P1]" in str(_part) or "LongTerm" in str(_part):
        _adv_summary["long_term_rep"] = 1

self.ctx.current_project.db.save_director_selection(
    ...,  # 기존 인자
    advisory_warnings=_adv_summary or None,
)
```

---

## 5) Phase 4 — `FailureAnalyzer` 유틸리티 신설

### 목적
DB에서 실패 패턴을 사후 분석하는 쿼리 도구. Codex/Claude가 "이번 런에서 왜 실패했나" 한 줄로 확인 가능.

### 변경 대상: `modules/core/failure_analyzer.py` (신규)

```python
"""[Log-4] 실패 패턴 사후 분석 유틸리티.

사용법:
    from modules.core.failure_analyzer import FailureAnalyzer
    fa = FailureAnalyzer(db)
    print(fa.summary())
    print(fa.most_failed_agents(top_n=5))
    print(fa.advisory_reject_correlation())
"""
from __future__ import annotations

import json
import logging
from collections import Counter, defaultdict


class FailureAnalyzer:
    """DB에서 실패 패턴을 분석하는 읽기 전용 유틸리티."""

    def __init__(self, db) -> None:
        self.db = db

    # ── 종합 요약 ─────────────────────────────────────────────────────────

    def summary(self) -> dict:
        """전체 실패 현황 종합 요약."""
        result = {}
        try:
            # Stage별 통과율
            result["stage_pass_rates"] = self.stage_pass_rates()
            # 가장 많이 실패한 에이전트
            result["top_failed_agents"] = self.most_failed_agents(top_n=5)
            # 가장 흔한 실패 카테고리
            result["top_failure_categories"] = self.top_failure_categories(top_n=5)
            # advisory → REJECT 상관관계
            result["advisory_correlations"] = self.advisory_reject_correlation()
            # 평균 시도 횟수
            result["avg_attempts_by_stage"] = self.avg_attempts_by_stage()
        except Exception as _e:
            logging.debug("[FailureAnalyzer] summary 실패: %s", _e)
        return result

    # ── Stage별 분석 ──────────────────────────────────────────────────────

    def stage_pass_rates(self) -> dict:
        """Stage 2/3/4별 첫 시도 통과율 및 최종 통과율."""
        try:
            rows = self.db.conn.execute(
                """SELECT stage, verdict, COUNT(*) as cnt
                   FROM stage_attempts GROUP BY stage, verdict"""
            ).fetchall()
            by_stage: dict[int, dict] = defaultdict(lambda: defaultdict(int))
            for r in rows:
                by_stage[r["stage"]][r["verdict"]] += r["cnt"]
            result = {}
            for stage, counts in sorted(by_stage.items()):
                total = sum(counts.values())
                passes = counts.get("PASS", 0) + counts.get("PASS_WITH_FIX", 0)
                result[f"stage_{stage}"] = {
                    "total_attempts": total,
                    "pass": passes,
                    "reject": counts.get("REJECT", 0),
                    "pass_rate_pct": round(passes / total * 100, 1) if total else 0,
                }
            return result
        except Exception as _e:
            logging.debug("[FailureAnalyzer] stage_pass_rates: %s", _e)
            return {}

    def avg_attempts_by_stage(self) -> dict:
        """에피소드당 평균 시도 횟수 (stage별)."""
        try:
            rows = self.db.conn.execute(
                """SELECT stage, ep_num, MAX(attempt_num) as max_attempt
                   FROM stage_attempts GROUP BY stage, ep_num"""
            ).fetchall()
            by_stage: dict[int, list] = defaultdict(list)
            for r in rows:
                by_stage[r["stage"]].append(r["max_attempt"])
            return {
                f"stage_{s}": round(sum(v) / len(v), 2) if v else 0
                for s, v in sorted(by_stage.items())
            }
        except Exception as _e:
            logging.debug("[FailureAnalyzer] avg_attempts_by_stage: %s", _e)
            return {}

    # ── LLM 에이전트 분석 ──────────────────────────────────────────────────

    def most_failed_agents(self, top_n: int = 10) -> list[dict]:
        """실패율 높은 에이전트 top N."""
        try:
            rows = self.db.conn.execute(
                """SELECT agent_name, model,
                          SUM(CASE WHEN success=0 THEN 1 ELSE 0 END) as failures,
                          COUNT(*) as total,
                          AVG(duration_ms) as avg_ms
                   FROM llm_calls
                   GROUP BY agent_name, model
                   ORDER BY failures DESC
                   LIMIT ?""",
                (top_n,),
            ).fetchall()
            return [
                {
                    "agent": r["agent_name"],
                    "model": r["model"],
                    "failures": r["failures"],
                    "total": r["total"],
                    "fail_rate_pct": round(r["failures"] / r["total"] * 100, 1) if r["total"] else 0,
                    "avg_duration_ms": int(r["avg_ms"] or 0),
                }
                for r in rows
            ]
        except Exception as _e:
            logging.debug("[FailureAnalyzer] most_failed_agents: %s", _e)
            return []

    def slowest_agents(self, top_n: int = 10) -> list[dict]:
        """평균 응답 시간 상위 에이전트."""
        try:
            rows = self.db.conn.execute(
                """SELECT agent_name, model,
                          AVG(duration_ms) as avg_ms,
                          MAX(duration_ms) as max_ms,
                          COUNT(*) as total
                   FROM llm_calls WHERE success=1
                   GROUP BY agent_name, model
                   ORDER BY avg_ms DESC LIMIT ?""",
                (top_n,),
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception as _e:
            logging.debug("[FailureAnalyzer] slowest_agents: %s", _e)
            return []

    def agent_error_types(self) -> dict:
        """에이전트별 에러 타입 분포."""
        try:
            rows = self.db.conn.execute(
                """SELECT agent_name, error_type, COUNT(*) as cnt
                   FROM llm_calls WHERE success=0 AND error_type IS NOT NULL
                   GROUP BY agent_name, error_type
                   ORDER BY cnt DESC"""
            ).fetchall()
            result: dict[str, dict] = defaultdict(dict)
            for r in rows:
                result[r["agent_name"]][r["error_type"]] = r["cnt"]
            return dict(result)
        except Exception as _e:
            logging.debug("[FailureAnalyzer] agent_error_types: %s", _e)
            return {}

    # ── 실패 카테고리 분석 ─────────────────────────────────────────────────

    def top_failure_categories(self, top_n: int = 10, stage: int | None = None) -> list[dict]:
        """가장 흔한 실패 카테고리 top N."""
        try:
            if stage is not None:
                rows = self.db.conn.execute(
                    """SELECT failure_category, COUNT(*) as cnt
                       FROM stage_attempts
                       WHERE verdict='REJECT' AND failure_category IS NOT NULL AND stage=?
                       GROUP BY failure_category ORDER BY cnt DESC LIMIT ?""",
                    (stage, top_n),
                ).fetchall()
            else:
                rows = self.db.conn.execute(
                    """SELECT failure_category, COUNT(*) as cnt
                       FROM stage_attempts
                       WHERE verdict='REJECT' AND failure_category IS NOT NULL
                       GROUP BY failure_category ORDER BY cnt DESC LIMIT ?""",
                    (top_n,),
                ).fetchall()
            return [{"category": r["failure_category"], "count": r["cnt"]} for r in rows]
        except Exception as _e:
            logging.debug("[FailureAnalyzer] top_failure_categories: %s", _e)
            return []

    def failure_trend_by_episode(self) -> list[dict]:
        """에피소드 진행에 따른 실패율 추이."""
        try:
            rows = self.db.conn.execute(
                """SELECT ep_num,
                          SUM(CASE WHEN verdict='REJECT' THEN 1 ELSE 0 END) as rejects,
                          COUNT(*) as total
                   FROM stage_attempts
                   WHERE ep_num IS NOT NULL
                   GROUP BY ep_num ORDER BY ep_num"""
            ).fetchall()
            return [
                {
                    "ep": r["ep_num"],
                    "rejects": r["rejects"],
                    "total": r["total"],
                    "reject_rate_pct": round(r["rejects"] / r["total"] * 100, 1) if r["total"] else 0,
                }
                for r in rows
            ]
        except Exception as _e:
            logging.debug("[FailureAnalyzer] failure_trend_by_episode: %s", _e)
            return []

    # ── Advisory 상관관계 분석 ─────────────────────────────────────────────

    def advisory_reject_correlation(self) -> dict:
        """Advisory 경고 발동 시 REJECT 비율 vs 미발동 시 REJECT 비율 비교."""
        try:
            rows = self.db.conn.execute(
                """SELECT advisory_warnings, verdict
                   FROM director_selections
                   WHERE advisory_warnings IS NOT NULL"""
            ).fetchall()
            if not rows:
                return {}

            advisory_types = ["truth_gate", "npc_drift", "numeric_drift",
                              "rel_drift", "flashback", "info_paradox", "long_term_rep"]
            result = {}
            for adv_type in advisory_types:
                with_adv_pass = with_adv_reject = without_adv_pass = without_adv_reject = 0
                for r in rows:
                    try:
                        flags = json.loads(r["advisory_warnings"] or "{}")
                    except (json.JSONDecodeError, TypeError):
                        continue
                    has_flag = bool(flags.get(adv_type))
                    is_reject = r["verdict"] == "REJECT"
                    if has_flag:
                        if is_reject:
                            with_adv_reject += 1
                        else:
                            with_adv_pass += 1
                    else:
                        if is_reject:
                            without_adv_reject += 1
                        else:
                            without_adv_pass += 1

                total_with = with_adv_pass + with_adv_reject
                total_without = without_adv_pass + without_adv_reject
                if total_with == 0:
                    continue
                result[adv_type] = {
                    "triggered_count": total_with,
                    "reject_rate_when_triggered_pct": round(with_adv_reject / total_with * 100, 1),
                    "reject_rate_when_not_triggered_pct": (
                        round(without_adv_reject / total_without * 100, 1) if total_without else 0
                    ),
                    "signal_lift": round(
                        (with_adv_reject / total_with) / (without_adv_reject / total_without)
                        if total_without and without_adv_reject else 0,
                        2,
                    ),  # 1.0 = 상관없음, >1.0 = advisory가 REJECT 예측
                }
            return result
        except Exception as _e:
            logging.debug("[FailureAnalyzer] advisory_reject_correlation: %s", _e)
            return {}

    # ── 모델별 분석 ───────────────────────────────────────────────────────

    def model_performance(self) -> dict:
        """모델별 성공률, 평균 응답 시간, 평균 응답 길이."""
        try:
            rows = self.db.conn.execute(
                """SELECT model,
                          SUM(CASE WHEN success=1 THEN 1 ELSE 0 END) as successes,
                          COUNT(*) as total,
                          AVG(duration_ms) as avg_ms,
                          AVG(response_chars) as avg_resp_chars
                   FROM llm_calls
                   GROUP BY model ORDER BY total DESC"""
            ).fetchall()
            return {
                r["model"]: {
                    "total_calls": r["total"],
                    "success_rate_pct": round(r["successes"] / r["total"] * 100, 1) if r["total"] else 0,
                    "avg_duration_ms": int(r["avg_ms"] or 0),
                    "avg_response_chars": int(r["avg_resp_chars"] or 0),
                }
                for r in rows
            }
        except Exception as _e:
            logging.debug("[FailureAnalyzer] model_performance: %s", _e)
            return {}

    # ── 입력 품질 분석 ────────────────────────────────────────────────────

    def large_prompt_calls(self, threshold_chars: int = 50000, top_n: int = 20) -> list[dict]:
        """비정상적으로 큰 프롬프트를 보낸 호출 목록. '어떤 자료를 너무 많이 받았는가'."""
        try:
            rows = self.db.conn.execute(
                """SELECT ts, agent_name, model, ep_num, stage,
                          prompt_chars, response_chars, duration_ms, context_tag
                   FROM llm_calls
                   WHERE prompt_chars >= ?
                   ORDER BY prompt_chars DESC LIMIT ?""",
                (threshold_chars, top_n),
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception as _e:
            logging.debug("[FailureAnalyzer] large_prompt_calls: %s", _e)
            return []

    def empty_response_calls(self) -> list[dict]:
        """응답이 거의 없는 호출 목록. 'LLM이 아무것도 안 반환한 경우'."""
        try:
            rows = self.db.conn.execute(
                """SELECT ts, agent_name, model, ep_num, stage,
                          prompt_chars, response_chars, error_type, error_msg
                   FROM llm_calls
                   WHERE success=1 AND (response_chars IS NULL OR response_chars < 50)
                   ORDER BY ts DESC LIMIT 50"""
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception as _e:
            logging.debug("[FailureAnalyzer] empty_response_calls: %s", _e)
            return []

    # ── 편의 출력 ─────────────────────────────────────────────────────────

    def print_report(self) -> None:
        """콘솔에 요약 보고서 출력."""
        import pprint
        pprint.pprint(self.summary(), width=100, sort_dicts=False)
```

---

## 6) Phase 5 — `episode_production.jsonl` 강화

### 변경 대상: `modules/core/stage4_interview_round.py`

`_append_episode_log()` 메서드의 기록 dict에 필드 추가:

```python
# 기존 필드 유지, 아래 필드 추가:
"model": getattr(getattr(round_ctx, "chief_writer", None), "model_tier", None),
"duration_ms": int((time.monotonic() - _round_start_ts) * 1000) if hasattr(self, "_round_start_ts") else None,
"ep_attempt_total": round_num + 1,  # 이 에피소드의 누적 시도 횟수
```

**`_round_start_ts` 설정**: `run()` 메서드 진입 직후:

```python
self._round_start_ts = time.monotonic()
```

---

## 7) 테스트 추가

파일: `tests/test_logging_enhancement.py` (신규)

```python
"""[Log-Enhancement] 로깅 강화 테스트."""
import json
import os
import tempfile

import pytest


@pytest.fixture
def tmp_db():
    from modules.core.db_manager import DBManager
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    db = DBManager(path)
    db.initialize_db()
    yield db
    db.conn.close()
    os.unlink(path)


def test_llm_calls_table_exists(tmp_db):
    """llm_calls 테이블이 초기화됨."""
    tables = [r[0] for r in tmp_db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()]
    assert "llm_calls" in tables


def test_save_llm_call_success(tmp_db):
    """정상 LLM 호출 기록."""
    tmp_db.save_llm_call(
        agent_name="director",
        model="gemini-2.5-pro",
        prompt_chars=5000,
        response_chars=800,
        duration_ms=1200,
        success=True,
        stage=4,
        ep_num=3,
        verdict="PASS",
    )
    rows = tmp_db.conn.execute("SELECT * FROM llm_calls").fetchall()
    assert len(rows) == 1
    assert rows[0]["agent_name"] == "director"
    assert rows[0]["success"] == 1
    assert rows[0]["verdict"] == "PASS"


def test_save_llm_call_failure(tmp_db):
    """실패 LLM 호출 기록."""
    tmp_db.save_llm_call(
        agent_name="analyst",
        model="gemini-2.0-flash",
        prompt_chars=3000,
        response_chars=0,
        duration_ms=500,
        success=False,
        error_type="ConnectionError",
        error_msg="네트워크 오류",
    )
    rows = tmp_db.conn.execute(
        "SELECT * FROM llm_calls WHERE success=0"
    ).fetchall()
    assert len(rows) == 1
    assert rows[0]["error_type"] == "ConnectionError"


def test_save_llm_call_noncritical(tmp_db):
    """DB 오류 시 예외 미발생 (비치명)."""
    tmp_db.conn.close()
    # 닫힌 DB에 저장 시도 — 예외 없이 통과해야 함
    tmp_db.save_llm_call(
        agent_name="writer",
        model="gemini-2.5-pro",
        prompt_chars=1000,
        response_chars=500,
        duration_ms=800,
    )


def test_stage_attempts_table_exists(tmp_db):
    """stage_attempts 테이블이 초기화됨."""
    tables = [r[0] for r in tmp_db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()]
    assert "stage_attempts" in tables


def test_save_stage_attempt(tmp_db):
    """스테이지 시도 기록."""
    tmp_db.save_stage_attempt(
        stage=4,
        verdict="REJECT",
        attempt_num=2,
        ep_num=5,
        arc_num=2,
        score=72,
        failure_category="CONTINUITY",
        reject_reason="주인공 동선 모순",
        advisory_flags={"truth_gate": 1, "npc_drift": 0},
    )
    rows = tmp_db.conn.execute("SELECT * FROM stage_attempts").fetchall()
    assert len(rows) == 1
    assert rows[0]["verdict"] == "REJECT"
    flags = json.loads(rows[0]["advisory_flags"])
    assert flags["truth_gate"] == 1


def test_failure_analyzer_summary(tmp_db):
    """FailureAnalyzer.summary() 반환 구조 확인."""
    from modules.core.failure_analyzer import FailureAnalyzer
    fa = FailureAnalyzer(tmp_db)
    result = fa.summary()
    assert isinstance(result, dict)


def test_failure_analyzer_empty_db(tmp_db):
    """빈 DB에서 FailureAnalyzer 비치명."""
    from modules.core.failure_analyzer import FailureAnalyzer
    fa = FailureAnalyzer(tmp_db)
    assert fa.stage_pass_rates() == {}
    assert fa.most_failed_agents() == []
    assert fa.advisory_reject_correlation() == {}
    assert fa.model_performance() == {}


def test_advisory_reject_correlation(tmp_db):
    """advisory_warnings가 있을 때 상관관계 계산."""
    from modules.core.failure_analyzer import FailureAnalyzer

    # advisory 있는 REJECT
    tmp_db.conn.execute(
        """INSERT INTO director_selections
           (ep_num, round_num, selected_label, selected_strategy, verdict, score,
            selection_reason, candidate_count, fix_scope, advisory_warnings)
           VALUES (1,0,'A','balanced','REJECT',60,'이유',3,'full',?)""",
        (json.dumps({"truth_gate": 1}),),
    )
    # advisory 없는 PASS
    tmp_db.conn.execute(
        """INSERT INTO director_selections
           (ep_num, round_num, selected_label, selected_strategy, verdict, score,
            selection_reason, candidate_count, fix_scope, advisory_warnings)
           VALUES (2,0,'B','balanced','PASS',90,'이유',3,null,?)""",
        (json.dumps({"truth_gate": 0}),),
    )
    tmp_db.conn.commit()

    fa = FailureAnalyzer(tmp_db)
    corr = fa.advisory_reject_correlation()
    assert "truth_gate" in corr
    assert corr["truth_gate"]["triggered_count"] == 1
    assert corr["truth_gate"]["reject_rate_when_triggered_pct"] == 100.0
```

---

## 8) 실행 순서

```bash
# Phase 1
python -m py_compile modules/core/db_manager.py
python -m py_compile modules/domain/agents/base_agent.py

# Phase 2
python -m py_compile modules/core/db_manager.py

# Phase 3
python -m py_compile modules/core/db_manager.py

# Phase 4
python -m py_compile modules/core/failure_analyzer.py

# Phase 5
python -m py_compile modules/core/stage4_interview_round.py

# 테스트
pytest tests/test_logging_enhancement.py -v

# ruff
ruff check modules/core/db_manager.py \
  modules/domain/agents/base_agent.py \
  modules/core/failure_analyzer.py \
  modules/core/stage4_interview_round.py \
  tests/test_logging_enhancement.py

# 전체 회귀
pytest tests/ -q
```

---

## 9) 런타임 검증 (보고서에 포함)

```python
# 설치 후 확인
python -c "
import tempfile, os
from modules.core.db_manager import DBManager
from modules.core.failure_analyzer import FailureAnalyzer

with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
    path = f.name
try:
    db = DBManager(path)
    db.initialize_db()

    # 테스트 데이터 삽입
    db.save_llm_call('director', 'gemini-2.5-pro', 5000, 800, 1200, True, stage=4, ep_num=1, verdict='REJECT')
    db.save_llm_call('analyst', 'gemini-2.0-flash', 3000, 0, 500, False, error_type='TimeoutError', stage=2)
    db.save_stage_attempt(4, 'REJECT', ep_num=1, score=60, failure_category='CONTINUITY',
                          advisory_flags={'truth_gate': 1})
    db.save_stage_attempt(4, 'PASS', ep_num=2, score=92)

    fa = FailureAnalyzer(db)
    import pprint
    pprint.pprint(fa.summary())
    print('[OK] FailureAnalyzer 정상 동작')
finally:
    os.unlink(path)
"
```

---

## 10) 보고서 형식

출력: `docs/2026-03-04/logging-enhancement-result.md`

```markdown
# 로깅 강화 결과

> 구현일: 2026-03-04

## 추가 내역

| Phase | 대상 | 내용 | 완료 |
|-------|------|------|------|
| 1 | db_manager.py + base_agent.py | llm_calls 테이블 + BaseAgent 계측 | ✅/❌ |
| 2 | db_manager.py + stage_*_*.py | stage_attempts 테이블 + 호출 지점 | ✅/❌ |
| 3 | db_manager.py + stage4_interview_round.py | advisory_warnings 컬럼 연결 | ✅/❌ |
| 4 | failure_analyzer.py (신규) | 쿼리 유틸리티 9개 메서드 | ✅/❌ |
| 5 | stage4_interview_round.py | episode_production model/duration 추가 | ✅/❌ |

## 검증 결과

- py_compile: 통과
- 신규 테스트: N passed, 0 failed
- ruff: 0건
- 전체 테스트: N passed, 0 failed
```

---

## 11) 합격 기준

- `llm_calls`, `stage_attempts` 테이블 **DB에 존재**
- `director_selections.advisory_warnings` 컬럼 **존재**
- `FailureAnalyzer` 클래스 **import 가능**
- `FailureAnalyzer(db).summary()` **dict 반환 (예외 없음)**
- 신규 테스트 **전량 PASS**
- 전체 테스트 **3227+ passed, 0 failed**
- ruff 위반 **0건**
- 모든 로깅 코드 **파이프라인 중단 없음** (비치명 보장)
