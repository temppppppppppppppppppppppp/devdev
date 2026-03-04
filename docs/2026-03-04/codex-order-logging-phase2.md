# Codex Order: 로깅 Phase 2 — 실패 스니펫 저장 + Stage 2/3 경로 보강

> **목적**: "어떤 자료를 왜 잘못받았는가"를 역추적할 수 있게 만든다.
>   Phase 1(로깅 강화)에서 llm_calls/stage_attempts 테이블을 신설했으나, 실패 시 프롬프트·응답 원문이 없어 원인 분석 불가.
>   또한 Stage 2/3의 stage_attempts 기록이 불완전하여 실패 경로 일부가 누락됨.
> **금지**: 기존 LLM 프롬프트 내용 변경. 기존 DB 컬럼 삭제. 성공 호출에 스니펫 저장 (DB 폭발 방지).
> **출력 보고서**: `docs/2026-03-04/logging-phase2-result.md`

---

## 0) 강제 제약

- `python -m py_compile <수정파일>` 각 Phase 후 통과 필수.
- `pytest tests/ -q` 기준선: **3,236 passed, 0 failed**.
- `ruff check modules/ tests/` 위반 0건.
- **비치명 원칙**: 로깅 실패가 파이프라인을 절대 중단하면 안 됨. 모든 로깅 코드는 `try/except Exception`으로 보호.
- **실패 한정 저장**: `prompt_snippet`/`response_snippet`은 `success=0`인 호출만 저장. 성공 호출은 NULL.

---

## 0.5) 참고: B항목(LM L1~L7) 현황

`docs/2026-02-27/LM-enhancement-implementation-spec.md`의 장기 기억 강화 L1~L7은 **전량 구현 완료**:

| 항목 | 모듈 | 상태 |
|------|------|------|
| L1 NPC Drift | `npc_drift_advisor.py` (LM-B) | ✅ 완료 |
| L2 World Laws | `truth_gate.py` (LM-A) | ✅ 완료 |
| L3 Relationship Drift | `relationship_drift_advisor.py` (LM-D) | ✅ 완료 |
| L4 Numeric Drift | `numeric_drift_advisor.py` (LM-C) | ✅ 완료 |
| L5 Flashback Verification | `flashback_verifier.py` (LM-E+H) | ✅ 완료 |
| L6 Info Paradox | `info_paradox_checker.py` (LM-F) | ✅ 완료 |
| L7 Narrative Structure | `narrative_context_formatter.py` (LM-G) | ✅ 완료 |

**이 오더에서 B항목은 별도 작업 없음.** 추후 실운영 데이터 기반 튜닝 필요 시 별도 오더.

---

## 1) 현재 상태 파악 (수동 검사 필수)

구현 전 아래를 직접 읽어라:

```
파일: modules/core/db_manager.py
읽을 범위:
  - llm_calls 테이블 DDL (L475 근방) — 현재 14개 컬럼 확인
  - save_llm_call() 메서드 (L2452 근방) — 현재 시그니처 + INSERT 문 확인
  - stage_attempts 테이블 DDL (L501 근방)
  - save_stage_attempt() 메서드 (L2499 근방)

파일: modules/domain/agents/base_agent.py
읽을 범위:
  - ask() 메서드 내부의 save_llm_call() 호출 지점
  - 실패 시 save_llm_call(success=False, ...) 호출 지점
  - 어떤 변수에 prompt/response 원문이 담겨 있는지 확인

파일: modules/core/stage2_finalizer.py
읽을 범위:
  - _record_s2_pass_metrics() (L856 근방) — save_stage_attempt 호출 확인
  - _record_s2_reject_metrics() (L939 근방) — save_stage_attempt 호출 확인

파일: modules/core/stage2_validation_pipeline.py
읽을 범위:
  - 전체 파일에서 save_stage_attempt 검색 — 호출 없음 확인
  - run_validation() 메서드의 실패 반환 경로 파악

파일: modules/core/stage3_orchestrator.py
읽을 범위:
  - save_stage_attempt 호출 2곳 (L697 PASS, L896 REJECT)
  - REJECT 경로에서 arc_num=None 설정 확인
  - attempt_num=1 하드코딩 확인

파일: modules/core/stage4_interview_round.py
읽을 범위:
  - _record_s4_attempt() (L2419 근방) — 가장 완성도 높은 참조 구현
  - duration_ms 자동 계산 방식 (_round_start_ts)
  - advisory_flags 전달 방식

파일: modules/core/failure_analyzer.py
읽을 범위:
  - 현재 메서드 목록 (11개) 확인
  - agent_error_types() — 실패 분석 기존 쿼리 확인
```

확인 사항:
- `base_agent.py`에서 실패 시 `prompt` 원문과 `response` 원문에 접근 가능한 변수명
- `stage2_validation_pipeline.py`에 별도 verdict 반환 경로가 있는지 (있다면 save_stage_attempt 누락)
- `stage3_orchestrator.py` REJECT 경로에서 arc_num을 가져올 수 있는 변수가 있는지
- `stage3_orchestrator.py`의 실제 재시도 루프 구조 (attempt_num 추적 가능 여부)

---

## 2) Phase A-1 — `llm_calls` 테이블에 스니펫 컬럼 추가

### 목적
실패한 LLM 호출의 프롬프트 앞 3000자 + 응답 전체를 저장하여 원인 역추적 가능하게 함.

### 변경 대상: `modules/core/db_manager.py`

#### DDL 마이그레이션 추가

`initialize_db()` 안, `llm_calls` CREATE TABLE 이후에 마이그레이션 추가:

```python
# llm_calls에 prompt_snippet/response_snippet 컬럼 추가 (없으면)
for _col in ("prompt_snippet", "response_snippet"):
    try:
        self.cursor.execute(
            f"ALTER TABLE llm_calls ADD COLUMN {_col} TEXT"
        )
        self.conn.commit()
    except Exception:
        pass  # 이미 존재하면 무시
```

#### `save_llm_call()` 시그니처 확장

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
    prompt_snippet: str | None = None,    # ← 추가
    response_snippet: str | None = None,  # ← 추가
) -> None:
```

#### INSERT 문 수정

기존 INSERT 문의 컬럼 목록과 VALUES 플레이스홀더에 2개 컬럼 추가:

```python
# 실패 한정 저장: success=True이면 snippet은 무조건 NULL
_prompt_snip = prompt_snippet[:3000] if (not success and prompt_snippet) else None
_response_snip = response_snippet if (not success and response_snippet) else None

self.cursor.execute(
    """INSERT INTO llm_calls
       (session_id, ts, stage, ep_num, agent_name, model,
        prompt_chars, response_chars, duration_ms,
        success, error_type, error_msg, verdict, context_tag,
        prompt_snippet, response_snippet)
       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
    (session_id, ts, stage, ep_num, agent_name, model,
     prompt_chars, response_chars, duration_ms,
     1 if success else 0, error_type,
     (error_msg or "")[:80], verdict, context_tag,
     _prompt_snip, _response_snip),
)
```

**핵심 제약**:
- `prompt_snippet`: 실패 시만 저장, 앞 **3000자** 잘라냄. 성공 시 NULL.
- `response_snippet`: 실패 시만 저장, **전체** 저장 (실패 응답은 보통 짧음). 성공 시 NULL.
- DB 폭발 방지: 성공 호출(대다수)은 snippet NULL → 추가 저장 0바이트.

---

## 3) Phase A-2 — `base_agent.py` 실패 시 스니펫 전달

### 변경 대상: `modules/domain/agents/base_agent.py`

**Phase 1(로깅 강화)에서 이미 `save_llm_call()` 호출 지점이 있음.** 실패 경로의 호출에 `prompt_snippet`/`response_snippet` 인자만 추가.

#### 실패 경로 수정

`save_llm_call(success=False, ...)` 호출 지점을 찾아 아래 인자 추가:

```python
# 실패 경로 — 기존 save_llm_call 호출에 2개 인자 추가:
_db.save_llm_call(
    agent_name=...,
    model=...,
    prompt_chars=...,
    response_chars=...,
    duration_ms=...,
    success=False,
    error_type=type(_api_err).__name__,
    error_msg=str(_api_err)[:80],
    # ↓ 추가
    prompt_snippet=str(prompt)[:3000] if prompt else None,
    response_snippet=str(response) if response else None,
)
```

**주의**:
- `prompt` 변수명은 실제 코드에서 확인 후 적용. `ask()` 메서드의 파라미터명 또는 지역변수명이 다를 수 있음.
- `response` 변수는 실패 시점에 부분 응답이 있을 수도, 없을 수도 있음. 있으면 전달, 없으면 None.
- 성공 경로의 `save_llm_call(success=True, ...)` 호출은 **수정하지 않음** (기본값 None 유지).

---

## 4) Phase A-3 — `FailureAnalyzer` 스니펫 조회 메서드 추가

### 변경 대상: `modules/core/failure_analyzer.py`

기존 클래스에 메서드 2개 추가:

```python
def failed_call_snippets(
    self, agent_name: str | None = None, top_n: int = 20
) -> list[dict]:
    """실패 호출의 프롬프트/응답 스니펫 조회. '어떤 자료를 왜 잘못받았는가'."""
    try:
        if agent_name:
            rows = self.db.conn.execute(
                """SELECT ts, agent_name, model, ep_num, stage,
                          error_type, error_msg,
                          prompt_snippet, response_snippet,
                          prompt_chars, response_chars, duration_ms
                   FROM llm_calls
                   WHERE success=0 AND prompt_snippet IS NOT NULL
                     AND agent_name=?
                   ORDER BY ts DESC LIMIT ?""",
                (agent_name, top_n),
            ).fetchall()
        else:
            rows = self.db.conn.execute(
                """SELECT ts, agent_name, model, ep_num, stage,
                          error_type, error_msg,
                          prompt_snippet, response_snippet,
                          prompt_chars, response_chars, duration_ms
                   FROM llm_calls
                   WHERE success=0 AND prompt_snippet IS NOT NULL
                   ORDER BY ts DESC LIMIT ?""",
                (top_n,),
            ).fetchall()
        return [dict(r) for r in rows]
    except Exception as _e:
        logging.debug("[FailureAnalyzer] failed_call_snippets: %s", _e)
        return []

def failure_prompt_patterns(self, top_n: int = 10) -> list[dict]:
    """실패 프롬프트의 공통 패턴 분석 — 길이 분포, 에이전트별 평균."""
    try:
        rows = self.db.conn.execute(
            """SELECT agent_name,
                      COUNT(*) as fail_count,
                      AVG(prompt_chars) as avg_prompt_chars,
                      MAX(prompt_chars) as max_prompt_chars,
                      AVG(response_chars) as avg_resp_chars
               FROM llm_calls
               WHERE success=0
               GROUP BY agent_name
               ORDER BY fail_count DESC LIMIT ?""",
            (top_n,),
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as _e:
        logging.debug("[FailureAnalyzer] failure_prompt_patterns: %s", _e)
        return []
```

`summary()` 메서드에도 추가:

```python
def summary(self) -> dict:
    ...
    # 기존 항목 유지, 아래 추가:
    result["failure_prompt_patterns"] = self.failure_prompt_patterns(top_n=5)
    ...
```

---

## 5) Phase C-1 — Stage 2 로깅 경로 보강

### 현재 상태

| 파일 | save_stage_attempt 호출 | 누락 |
|------|------------------------|------|
| `stage2_finalizer.py` | ✅ PASS(L856) + REJECT(L939) | `duration_ms`, `advisory_flags`, `failure_category` 누락 |
| `stage2_validation_pipeline.py` | ❌ 호출 없음 | 별도 실패 경로 존재 여부 확인 필요 |

### 작업 내용

#### C-1a: `stage2_validation_pipeline.py` 실패 경로 확인

`run_validation()` 메서드를 읽고:
1. 이 메서드가 자체적으로 verdict를 반환하는 경로가 있는지 확인
2. 있다면 → `save_stage_attempt()` 호출 추가
3. 없다면 (단순히 `stage2_finalizer`에 위임만 한다면) → 수정 불필요

**판단 기준**: `run_validation()`이 직접 `{"decision": "REJECT", ...}` 같은 verdict dict를 반환하는 경로가 있으면 → 거기에 `save_stage_attempt` 추가. `stage2_finalizer`로 위임하고 그쪽에서 기록한다면 → 중복 기록 방지를 위해 추가하지 않음.

#### C-1b: `stage2_finalizer.py` 기존 호출 보강

PASS 경로 (`_record_s2_pass_metrics`, L856 근방):

```python
# 기존 호출에 duration_ms 추가
# _record_s2_pass_metrics 메서드 내에서 시간 측정이 가능한 변수가 있는지 확인
# 있으면 duration_ms=... 전달, 없으면 생략 (현행 유지)
```

REJECT 경로 (`_record_s2_reject_metrics`, L939 근방):

```python
# 기존 호출에 누락 필드 보강 (가능한 범위에서):
# reject_reason은 이미 전달 중
# failure_category → Director 응답에서 추출 가능하면 전달, 아니면 NULL 유지
```

**주의**: 무리하게 필드를 채우지 말 것. 데이터가 자연스럽게 존재하는 경우만 전달. 없는 데이터를 억지로 만들지 않음.

---

## 6) Phase C-2 — Stage 3 로깅 경로 보강

### 현재 상태

| 경로 | 문제 |
|------|------|
| PASS (L697) | `attempt_num=1` 하드코딩. 실제 재시도 횟수 미반영 |
| REJECT (L896) | `arc_num=None`. 사용 가능한 arc_num 변수가 스코프에 있는지 확인 필요 |

### 작업 내용

#### C-2a: REJECT 경로 arc_num 복원

```python
# L896 근방 REJECT 경로
# 현재: arc_num=None
# 변경: arc_num 변수가 스코프에 있으면 전달
#   - 후보: arc_no, arc_data.get("arc_no"), 등
#   - 스코프에 없으면 None 유지 (무리하지 않음)
```

#### C-2b: attempt_num 실제 값 전달

```python
# PASS/REJECT 양쪽에서 attempt_num=1 하드코딩 → 실제 재시도 카운터 전달
# Stage 3의 재시도 루프 변수명 확인 필요 (예: _attempt, retry_count 등)
# 루프 변수가 있으면: attempt_num=_attempt + 1
# 루프 변수가 없으면 (재시도 없이 1회만 실행): 현행 유지 (attempt_num=1)
```

#### C-2c: REJECT 경로 reject_reason 보강

```python
# 현재: reject_reason=pipeline_result["error"][:500]
# 확인: pipeline_result에 더 상세한 rejection 사유가 있는지 (score, specific issues 등)
# 있으면 reject_reason에 풍부하게 포함, 없으면 현행 유지
```

---

## 7) 테스트 추가

파일: `tests/test_logging_phase2.py` (신규)

```python
"""[Log-Phase2] 실패 스니펫 저장 + Stage 2/3 로깅 보강 테스트."""
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


# ── Phase A: 스니펫 컬럼 존재 확인 ──────────────────────────────────────

def test_llm_calls_has_snippet_columns(tmp_db):
    """llm_calls 테이블에 prompt_snippet, response_snippet 컬럼 존재."""
    cols = [
        r[1] for r in tmp_db.conn.execute("PRAGMA table_info(llm_calls)").fetchall()
    ]
    assert "prompt_snippet" in cols
    assert "response_snippet" in cols


# ── Phase A: 실패 시 스니펫 저장 ──────────────────────────────────────────

def test_save_llm_call_failure_with_snippet(tmp_db):
    """실패 호출 시 prompt_snippet/response_snippet 저장."""
    long_prompt = "A" * 5000  # 3000자로 잘려야 함
    tmp_db.save_llm_call(
        agent_name="director",
        model="gemini-2.5-pro",
        prompt_chars=5000,
        response_chars=50,
        duration_ms=800,
        success=False,
        error_type="JSONDecodeError",
        error_msg="파싱 실패",
        prompt_snippet=long_prompt,
        response_snippet="malformed json response",
    )
    row = tmp_db.conn.execute(
        "SELECT prompt_snippet, response_snippet FROM llm_calls WHERE success=0"
    ).fetchone()
    assert row is not None
    assert len(row["prompt_snippet"]) == 3000  # 3000자 절단
    assert row["response_snippet"] == "malformed json response"  # 전체 저장


def test_save_llm_call_success_no_snippet(tmp_db):
    """성공 호출 시 snippet은 NULL (DB 폭발 방지)."""
    tmp_db.save_llm_call(
        agent_name="analyst",
        model="gemini-2.0-flash",
        prompt_chars=3000,
        response_chars=500,
        duration_ms=600,
        success=True,
        prompt_snippet="이것은 저장되면 안 됨",
        response_snippet="이것도 저장되면 안 됨",
    )
    row = tmp_db.conn.execute(
        "SELECT prompt_snippet, response_snippet FROM llm_calls WHERE success=1"
    ).fetchone()
    assert row is not None
    assert row["prompt_snippet"] is None
    assert row["response_snippet"] is None


def test_save_llm_call_failure_no_snippet_provided(tmp_db):
    """실패 호출이지만 snippet 미전달 시 NULL."""
    tmp_db.save_llm_call(
        agent_name="writer",
        model="gemini-2.5-pro",
        prompt_chars=2000,
        response_chars=0,
        duration_ms=500,
        success=False,
        error_type="TimeoutError",
    )
    row = tmp_db.conn.execute(
        "SELECT prompt_snippet, response_snippet FROM llm_calls WHERE success=0"
    ).fetchone()
    assert row is not None
    assert row["prompt_snippet"] is None
    assert row["response_snippet"] is None


def test_save_llm_call_snippet_noncritical(tmp_db):
    """DB 오류 시 예외 미발생 (비치명)."""
    tmp_db.conn.close()
    # 닫힌 DB에 저장 시도 — 예외 없이 통과해야 함
    tmp_db.save_llm_call(
        agent_name="writer",
        model="gemini-2.5-pro",
        prompt_chars=1000,
        response_chars=500,
        duration_ms=800,
        success=False,
        prompt_snippet="test",
        response_snippet="test",
    )


# ── Phase A: FailureAnalyzer 스니펫 조회 ─────────────────────────────────

def test_failure_analyzer_failed_call_snippets(tmp_db):
    """failed_call_snippets() 메서드 동작."""
    from modules.core.failure_analyzer import FailureAnalyzer

    tmp_db.save_llm_call(
        agent_name="director",
        model="gemini-2.5-pro",
        prompt_chars=5000,
        response_chars=50,
        duration_ms=800,
        success=False,
        error_type="JSONDecodeError",
        prompt_snippet="프롬프트 내용...",
        response_snippet="깨진 응답...",
    )
    fa = FailureAnalyzer(tmp_db)
    results = fa.failed_call_snippets()
    assert len(results) == 1
    assert results[0]["prompt_snippet"] == "프롬프트 내용..."
    assert results[0]["response_snippet"] == "깨진 응답..."


def test_failure_analyzer_failed_call_snippets_by_agent(tmp_db):
    """agent_name 필터링."""
    from modules.core.failure_analyzer import FailureAnalyzer

    tmp_db.save_llm_call(
        agent_name="director", model="m", prompt_chars=100,
        response_chars=0, duration_ms=100, success=False,
        prompt_snippet="dir prompt",
    )
    tmp_db.save_llm_call(
        agent_name="analyst", model="m", prompt_chars=100,
        response_chars=0, duration_ms=100, success=False,
        prompt_snippet="ana prompt",
    )
    fa = FailureAnalyzer(tmp_db)
    results = fa.failed_call_snippets(agent_name="director")
    assert len(results) == 1
    assert results[0]["agent_name"] == "director"


def test_failure_analyzer_failure_prompt_patterns(tmp_db):
    """failure_prompt_patterns() 메서드 동작."""
    from modules.core.failure_analyzer import FailureAnalyzer

    for i in range(3):
        tmp_db.save_llm_call(
            agent_name="director", model="m", prompt_chars=5000 + i * 1000,
            response_chars=0, duration_ms=800, success=False,
        )
    fa = FailureAnalyzer(tmp_db)
    results = fa.failure_prompt_patterns()
    assert len(results) == 1
    assert results[0]["fail_count"] == 3
    assert results[0]["agent_name"] == "director"


def test_failure_analyzer_snippets_empty_db(tmp_db):
    """빈 DB에서 스니펫 조회 비치명."""
    from modules.core.failure_analyzer import FailureAnalyzer
    fa = FailureAnalyzer(tmp_db)
    assert fa.failed_call_snippets() == []
    assert fa.failure_prompt_patterns() == []
```

---

## 8) 실행 순서

```bash
# Phase A-1: DB 스키마 + save_llm_call 확장
python -m py_compile modules/core/db_manager.py

# Phase A-2: base_agent 실패 경로 스니펫 전달
python -m py_compile modules/domain/agents/base_agent.py

# Phase A-3: FailureAnalyzer 메서드 추가
python -m py_compile modules/core/failure_analyzer.py

# Phase C-1: Stage 2 로깅 보강
python -m py_compile modules/core/stage2_finalizer.py
python -m py_compile modules/core/stage2_validation_pipeline.py  # 수정한 경우만

# Phase C-2: Stage 3 로깅 보강
python -m py_compile modules/core/stage3_orchestrator.py

# 신규 테스트
pytest tests/test_logging_phase2.py -v

# ruff
ruff check modules/core/db_manager.py \
  modules/domain/agents/base_agent.py \
  modules/core/failure_analyzer.py \
  modules/core/stage2_finalizer.py \
  modules/core/stage2_validation_pipeline.py \
  modules/core/stage3_orchestrator.py \
  tests/test_logging_phase2.py

# 전체 회귀
pytest tests/ -q
```

---

## 9) 런타임 검증 (보고서에 포함)

```python
# 실패 스니펫 저장 + 조회 통합 검증
python -c "
import tempfile, os
from modules.core.db_manager import DBManager
from modules.core.failure_analyzer import FailureAnalyzer

with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
    path = f.name
try:
    db = DBManager(path)
    db.initialize_db()

    # 실패 호출 + 스니펫
    db.save_llm_call(
        'director', 'gemini-2.5-pro', 8000, 50, 1200,
        success=False,
        error_type='JSONDecodeError',
        error_msg='Expecting value: line 1 column 1',
        stage=4, ep_num=5,
        prompt_snippet='시스템 프롬프트: 당신은 웹소설 감독입니다... (앞 3000자)',
        response_snippet='{\"score\": 85, \"decision\": \"PAS',  # 잘린 JSON
    )

    # 성공 호출 (스니펫 없음)
    db.save_llm_call(
        'analyst', 'gemini-2.0-flash', 3000, 800, 600,
        success=True, stage=2, ep_num=5,
    )

    fa = FailureAnalyzer(db)

    # 스니펫 조회
    snippets = fa.failed_call_snippets()
    assert len(snippets) == 1
    assert snippets[0]['prompt_snippet'] is not None
    assert snippets[0]['response_snippet'] is not None

    # 패턴 분석
    patterns = fa.failure_prompt_patterns()
    assert len(patterns) == 1

    # summary에 포함 확인
    summary = fa.summary()
    assert 'failure_prompt_patterns' in summary

    print('[OK] 실패 스니펫 저장 + 조회 정상 동작')
    print(f'  스니펫 수: {len(snippets)}')
    print(f'  prompt_snippet 길이: {len(snippets[0][\"prompt_snippet\"])}')
    print(f'  response_snippet: {snippets[0][\"response_snippet\"][:50]}...')
finally:
    os.unlink(path)
"
```

---

## 10) 보고서 형식

출력: `docs/2026-03-04/logging-phase2-result.md`

```markdown
# 로깅 Phase 2 결과

> 구현일: 2026-03-04

## 추가 내역

| Phase | 대상 | 내용 | 완료 |
|-------|------|------|------|
| A-1 | db_manager.py | llm_calls에 prompt_snippet/response_snippet 컬럼 + 실패 한정 저장 | ✅/❌ |
| A-2 | base_agent.py | 실패 경로에서 prompt/response 원문 전달 | ✅/❌ |
| A-3 | failure_analyzer.py | failed_call_snippets() + failure_prompt_patterns() 2개 메서드 | ✅/❌ |
| C-1 | stage2_*.py | Stage 2 로깅 경로 확인 + 보강 (해당 시) | ✅/❌/해당없음 |
| C-2 | stage3_orchestrator.py | REJECT arc_num 복원 + attempt_num 실제값 + reject_reason 보강 | ✅/❌ |

## Stage 2/3 경로 조사 결과

- `stage2_validation_pipeline.py` 별도 verdict 반환 경로: 있음/없음
  - 있으면: save_stage_attempt 추가 여부 + 근거
  - 없으면: 수정 불필요 (stage2_finalizer에서 기록)
- `stage3_orchestrator.py` REJECT arc_num: 복원함/불가(변수 스코프 밖)
- `stage3_orchestrator.py` attempt_num: 실제값 전달/재시도 루프 없어 1 유지

## 검증 결과

- py_compile: 통과/실패
- 신규 테스트: N passed, 0 failed
- ruff: 0건
- 전체 테스트: N passed, 0 failed
- 런타임 검증: [OK]/[FAIL]
```

---

## 11) 합격 기준

- `llm_calls` 테이블에 `prompt_snippet`, `response_snippet` 컬럼 **존재**
- `save_llm_call(success=False, prompt_snippet="...", response_snippet="...")` → DB에 **저장됨**
- `save_llm_call(success=True, prompt_snippet="...")` → DB에 **NULL로 저장** (성공 시 미저장)
- `prompt_snippet`은 **3000자 절단** 확인
- `FailureAnalyzer.failed_call_snippets()` → **list[dict] 반환** (예외 없음)
- `FailureAnalyzer.failure_prompt_patterns()` → **list[dict] 반환** (예외 없음)
- Stage 2/3 로깅 경로 조사 결과 **보고서에 명시**
- 신규 테스트 **전량 PASS**
- 전체 테스트 **3,236+ passed, 0 failed**
- ruff 위반 **0건**
- 모든 로깅 코드 **파이프라인 중단 없음** (비치명 보장)
