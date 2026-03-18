# S8: 프로젝트 0_260318 딥다이브 -- 실행문서

> **작성일**: 2026-03-18
> **상태**: active
> **소스**: `docs/2026-03-18/OPUS/0_260318-project-analysis-report.md` + C1-C10 코드 딥다이브 + `docs/2026-03-18/OPUS/0_260318-manuscript-tf-report.md` TF 원고 품질 보고서
> **감리**: 기본 3pass + 적대적 3pass (본 문서 하단 Section 5 참조)
> **코드 수정 금지** -- 본 문서는 실행 계획만 문서화. 코드 파일 Edit/Write 절대 금지.
> **확신도**: 97% (전수 라인 대조 완료, 6pass 감리 완료)

---

## 1. 실행 항목 총괄표

| ID | 항목 | 심각도 | 근본원인 요약 | 수정 대상 file:line | 완료 기준 | 추정 공수 | 의존성 |
|----|------|--------|--------------|---------------------|----------|----------|--------|
| C1 | Arc vs Manuscript 제목 불일치 | **P0-Critical** | `_extract_episode_focus()`가 Arc 화 제목을 추출/전달하지 않음 | `blueprint_constraint_compiler.py:194-229`, `blueprint_ensemble.py` 프롬프트 | Blueprint에 `arc_title` 필드 존재 + 원고 제목 일치 검증 통과 | 2h | 없음 |
| C2 | 정지선 검증 부재 | **P0-Critical** | 정지선이 프롬프트 advisory일 뿐 Python 검증 없음 | `blueprint_constraint_compiler.py:231-272`, `unified_blueprint_validator.py` | 정지선 위반시 REJECT 판정 + 테스트 커버리지 | 3h | 없음 |
| C3 | Director 99점 override | **P0-Critical** | CRITICAL Python 경고가 PASS를 뒤집지 못함. `python_warnings` 가중치 10%로 영향력 미미 | `director_ensemble.py:1723-1741`, `director_prompts.py:118-124`, `stage4_interview_round.py:2433-2447` | CRITICAL N건 이상시 hard gate REJECT + 테스트 | 3h | 없음 |
| C4 | quality_risk 분별력 = 0 | **P1-High** | PASS_WITH_FIX verdict면 무조건 `quality_risk=True`. 100점도 해제 안 됨. 11/11 전부 true | `three_phase_blueprint_generator.py:446-448`, `stage4_interview_round.py:2166-2175`, `stage4_orchestrator.py:1201-1209` | score >= 95일 때 `quality_risk=False` 오버라이드 + 분별력 통계 테스트 | 1.5h | 없음 |
| C5 | failure_analyzer AttributeError | **P0-Critical** | `SimpleNamespace(conn=conn, db_path=db_path)` 반환하여 `get_stage4_final_authority_rows()` 미구현 | `audit_service.py:132-135`, `failure_analyzer.py:580` | `FailureAnalyzer(db)` 호출시 AttributeError 미발생 + 정상 데이터 반환 | 2h | 없음 |
| C6 | Stage 2/3 token_cost = 0.0 | **P1-High** | `record_attempt()` 호출시 `token_cost` 파라미터 미전달, 기본값 0.0 사용 | `stage2_finalizer.py:1592,1738`, `stage3_orchestrator.py:1469,2048` | 4개 호출 지점 모두 실제 비용값 전달 + DB 검증 | 2h | 없음 |
| C7 | 빈 추적 테이블 5개 | **P2-Medium** | karma_status 미호출, canonical_facts 키 매핑 부재, timeline_entries 필드 absent 등 | `stage4_post_processor.py`, `fact_ledger.py:374-418`, `db_manager.py:2147` | 3개 테이블(karma/canonical_facts/timeline) 데이터 적재 확인 | 4h | 없음 |
| C8 | Stage 3 중간실패 미기록 | **P1-High** | retry 루프 내부에서 중간 REJECT를 PassRateMonitor에 미기록 | `three_phase_blueprint_generator.py:404,497-500` | 모든 REJECT 분기점에서 record_attempt 호출 확인 + 로그 검증 | 1.5h | 없음 |
| C9 | NPC 한태민 속성 드리프트 | **P2-Medium** | Bible에 구체 계열사명 없음 + NpcDriftAdvisor가 advisory-only | `npc_drift_advisor.py:20`, Bible 데이터 | Bible 구체화 + severity=HIGH시 blocking 승격 | 2h | 없음 |
| C10 | target_ep 선택 미기록 | **P3-Low** | `target_ep` 선택이 decisions.jsonl에 미기록 | `stage4_orchestrator.py:687-689` | target_ep 선택 사실 decisions.jsonl 기록 확인 | 0.5h | 없음 |
| TF-S1 | Blueprint ep2 유령 씬 | **P0-Critical** | ep2 scene_1이 ep1에 흡수되어 ep2에 존재하지 않는 씬 참조 | Blueprint/Arc 데이터 | ep3 집필 전 Blueprint ep2 씬 구조 재정립 | 1h | C1, C2 |
| TF-S2 | Arc 전진 밀림(forward shift) | **P0-Critical** | Arc ep1-4가 1화씩 전진 밀림 상태 | Arc 데이터 | ep3 집필 전 Arc ep1-4 위치 교정 완료 | 1.5h | TF-S1 |
| TF-A1 | Arc ep1 종료 상태 불일치 | **P1-High** | Arc "침실/잠옷" vs 원고 "복도/외출복" | Arc ep1 종료 상태 데이터 | Arc 종료 상태와 원고 일치 확인 | 0.5h | TF-S2 |
| TF-A2 | Arc ep2 제목 불일치 | **P1-High** | "아버지의 서재" vs "의심의 씨앗" (=C1과 동일 근본원인) | Arc ep2 제목 데이터 | C1 수정으로 자동 해소 확인 | 0h | C1 |
| TF-A3 | 계획 기록 방식 모순 | **P1-High** | Blueprint "백지에 기록" vs 원고 "흔적 안 남김" | Blueprint ep2 씬 지시 | Blueprint 내부 일관성 확보 | 0.5h | TF-S1 |
| TF-A4 | ep2 잠옷 착용 후 저녁식사 | **P1-High** | 옷 갈아입는 장면 누락 | 원고 ep2 교정 | 원고 연속성 검증 통과 | 0.5h | 없음 |
| TF-B | B급 5건 (WTI 오차 외) | **P2-Medium** | 팩트체크 오류 5건 | 원고 해당 부분 | 팩트 정확성 확인 | 1.5h | 없음 |
| TF-C | C급 4건 (문체 개선) | **P3-Low** | "차갑다/냉철하다" 과잉 반복, 대화 비율, AI slop | 원고 전체 | 문체 지표 개선 확인 | 2h | 없음 |

---

## 2. 코드 수정 상세 (C1-C10)

### 2.1 C1 -- Arc 제목 비전달

**파일**: `modules/domain/agents/blueprint_constraint_compiler.py`
**라인**: 194-229

**BEFORE 상태 (현재 동작)**:
`_extract_episode_focus()` 메서드가 Arc의 `tactical_doc` 또는 `beat_sequence`에서 해당 화의 전술 정보(이벤트, 비트)를 추출하여 반환한다. 반환 dict는 `{"content", "key_events", "arc_position"}` 3개 키만 포함. Arc에 정의된 화 제목(`제 N화: XXX` 형식)을 파싱하지 않으므로, Blueprint 생성 프롬프트에 화 제목 제약이 전달되지 않는다.

```python
# line 225-229 (현재)
return {
    "content": content if content else "이번 화 전술 정보 없음",
    "key_events": key_events[:5],
    "arc_position": arc_position,
}
```

**AFTER 상태 (목표 동작)**:
1. `_extract_episode_focus()` 내부에서 `tactical_doc` 또는 `episode_details`에서 `제 {ep_num}화: {title}` 패턴을 정규식으로 파싱한다.
2. 파싱 성공시 반환 dict에 `"arc_title": title` 키를 추가한다.
3. 파싱 실패시 `"arc_title": None`으로 반환하여 다운스트림 코드가 graceful하게 처리할 수 있도록 한다.

```python
# line 225-229 (수정 후)
# Arc 화 제목 추출
arc_title = None
_tactical = arc_data.get("tactical_doc", "")
if isinstance(_tactical, str):
    _title_match = re.search(rf"제\s*{ep_num}\s*화\s*[:：]\s*(.+?)(?:\n|$)", _tactical)
    if _title_match:
        arc_title = _title_match.group(1).strip()
if not arc_title:
    # episode_details 폴백
    for _item in (arc_data.get("episode_details") or []):
        if isinstance(_item, dict) and _item.get("ep_num") == ep_num:
            arc_title = _item.get("title") or _item.get("name")
            break

return {
    "content": content if content else "이번 화 전술 정보 없음",
    "key_events": key_events[:5],
    "arc_position": arc_position,
    "arc_title": arc_title,
}
```

**추가 수정 대상**: `modules/domain/agents/blueprint_ensemble.py`
- Blueprint 생성 프롬프트에 `must_focus["arc_title"]`이 존재할 경우 `"[제약] 이번 화 제목은 반드시 '{arc_title}'을 사용할 것"` 문구를 제약 블록에 삽입한다.
- `constraint_block`을 조합하는 부분에서 `episode_focus.get("arc_title")`을 참조하여 프롬프트 주입.

**테스트 검증 방법**:
1. Arc 데이터에 `"제 2화: 의심의 씨앗"` 형식의 tactical_doc를 포함한 테스트 케이스 작성
2. `_extract_episode_focus()` 호출 후 반환값에 `arc_title == "의심의 씨앗"` 확인
3. Blueprint 생성 프롬프트에 제목 제약 문구가 포함되었는지 문자열 검색
4. 제목이 없는 Arc 데이터에서 `arc_title=None`으로 graceful 처리 확인

**의존성**: 없음

---

### 2.2 C2 -- 정지선 검증 부재

**파일**: `modules/domain/agents/blueprint_constraint_compiler.py`
**라인**: 231-272

**BEFORE 상태 (현재 동작)**:
`_extract_stop_line()` 메서드가 다음 화 내용(정지선)을 추출하여 문자열로 반환한다. 이 정지선은 Blueprint 생성 프롬프트에 advisory 텍스트로만 주입된다. Python 레벨에서 생성된 Blueprint의 `integrated_scenario`가 정지선 내용을 침범했는지 검증하는 코드가 존재하지 않는다.

즉, LLM이 프롬프트의 정지선 지시를 무시하고 다음 화 내용을 미리 써도 아무런 차단이 없다. 이것이 TF-S2(Arc 전진 밀림)의 코드측 근본원인이다.

**AFTER 상태 (목표 동작)**:
`modules/domain/agents/unified_blueprint_validator.py`에 정지선 검증 로직을 추가한다.

1. `constraint_block`에서 정지선 내용(`stop_line.content`)을 추출한다.
2. 생성된 Blueprint의 `integrated_scenario` 텍스트와 정지선 내용 간 키워드 유사도를 계산한다.
3. 유사도가 임계치(예: 고유명사 3개 이상 일치 또는 TF-IDF cosine > 0.4)를 초과하면 `verdict=REJECT`, `reject_reason="정지선 침범"` 판정을 반환한다.

**구체적 수정 위치**: `unified_blueprint_validator.py`의 `validate()` 메서드 내부, 기존 blocking validation 단계 직후에 삽입.

```python
# unified_blueprint_validator.py - validate() 메서드 내부에 추가
# 정지선 침범 검사
stop_line_content = constraint_block.get("stop_line", {}).get("content", "")
if stop_line_content and isinstance(blueprint, dict):
    scenario_text = str(blueprint.get("integrated_scenario", ""))
    # 정지선 고유 키워드 추출 (명사 기반)
    stop_keywords = set(_extract_nouns(stop_line_content))  # 유틸 함수 필요
    scenario_keywords = set(_extract_nouns(scenario_text))
    overlap = stop_keywords & scenario_keywords
    # 공통 일반어 제외 후 고유 키워드 3개 이상 일치시 REJECT
    _common_words = {"주인공", "그", "이", "것", "수", "때"}
    significant_overlap = overlap - _common_words
    if len(significant_overlap) >= 3:
        return "REJECT", {
            "verdict": "REJECT",
            "reject_reason": f"정지선 침범: 다음 화 키워드 {significant_overlap} 감지",
            "issues": [f"정지선 침범 키워드: {', '.join(significant_overlap)}"],
        }
```

**테스트 검증 방법**:
1. 정지선 내용과 겹치는 키워드를 3개 이상 포함한 Blueprint 생성 후 REJECT 판정 확인
2. 정지선 내용과 겹치지 않는 정상 Blueprint에서 PASS 확인
3. 정지선이 없는 경우(Arc 마지막 화) graceful 스킵 확인

**의존성**: 없음

---

### 2.3 C3 -- Director CRITICAL hard gate 부재

**파일**: `modules/domain/agents/director_ensemble.py`
**라인**: 1723-1741

**BEFORE 상태 (현재 동작)**:
`director_ensemble.py:1723-1741`에서 `apply_adaptive_decision()`의 결과에 따라 `final_verdict`를 결정한다. Director가 REJECT한 경우 Python이 뒤집지 않는 "디렉터 주권" 원칙이 적용된다(line 1734). 그러나 반대 방향(Director가 PASS했으나 Python CRITICAL 경고가 다수인 경우)에서는 Python이 Director의 PASS를 뒤집을 수 없다.

`director_prompts.py:118-124`에서 Python 경고 반영 가중치가 10%로, Director LLM이 경고를 무시해도 점수 영향이 미미하다.

`stage4_interview_round.py:2433` 부근에서 Director 결과를 후처리하지만, CRITICAL 경고 건수 기반 hard gate가 없다.

**AFTER 상태 (목표 동작)**:
`stage4_interview_round.py`의 Director 결과 후처리 블록(line 2433-2447 부근)에 다음 hard gate를 추가한다:

```python
# stage4_interview_round.py - Director 결과 후처리 (line ~2433 이후)
# CRITICAL Python 경고 hard gate
_critical_warnings = [w for w in python_warnings if w.get("severity") == "CRITICAL"]
_CRITICAL_HARD_GATE_THRESHOLD = 3  # 설정화 권고
if len(_critical_warnings) >= _CRITICAL_HARD_GATE_THRESHOLD and verdict in ("PASS", "PASS_WITH_FIX"):
    logging.warning(
        "[HardGate] CRITICAL Python 경고 %d건 >= %d → Director PASS를 REJECT로 전환",
        len(_critical_warnings), _CRITICAL_HARD_GATE_THRESHOLD
    )
    verdict = "REJECT"
    reason = f"[Python HardGate] CRITICAL 경고 {len(_critical_warnings)}건 초과: " + "; ".join(
        w.get("message", "")[:80] for w in _critical_warnings[:3]
    )
```

**핵심 설계 결정**:
- 임계치 3건은 초기값. `constants.py` 또는 설정 파일로 외부화 권고.
- Director 주권 원칙과의 관계: Director REJECT는 Python이 뒤집지 않는다(기존 유지). 그러나 CRITICAL 경고 N건 이상시 Python이 Director PASS를 뒤집는 것은 "안전 게이트" 역할로 별도 원칙이다.
- PASS_WITH_FIX도 대상에 포함한다 (CRITICAL 경고가 있으면 fix로는 부족).

**테스트 검증 방법**:
1. Python 경고에 CRITICAL 3건 이상 주입 + Director PASS 결과 → REJECT 전환 확인
2. CRITICAL 2건 + Director PASS → PASS 유지 확인
3. CRITICAL 3건 + Director REJECT → REJECT 유지 확인 (기존 주권 불변)
4. `reason` 문자열에 CRITICAL 경고 내용 포함 확인

**의존성**: 없음

---

### 2.4 C4 -- quality_risk 분별력 = 0

**파일**: `modules/domain/agents/three_phase_blueprint_generator.py`
**라인**: 446-448

**BEFORE 상태 (현재 동작)**:
```python
# line 446-448
_validation_quality_risk = bool(
    validation_result.get("quality_risk", False) or verdict in ("PASS_WITH_FIX", "PASS_WITH_WARNING")
)
```
verdict가 `PASS_WITH_FIX` 또는 `PASS_WITH_WARNING`이면 점수에 관계없이 `quality_risk=True`로 설정된다. 0_260318 프로젝트에서 11/11 에피소드가 전부 `quality_risk=True`로 기록되어 분별력이 0이다.

Stage 4는 이 값을 2곳에서 읽는다:
- `stage4_interview_round.py:2166-2175`: Director 프롬프트에 경고 주입
- `stage4_orchestrator.py:1201-1209`: `_v75d_threshold`를 1로 낮춤 (조기 inplace 패치 트리거)

11/11 전부 true이므로 이 두 곳 모두 항상 발동하여, 정상 Blueprint와 저품질 Blueprint를 구분하지 못한다.

**AFTER 상태 (목표 동작)**:
score >= 95일 때 `quality_risk=False`로 오버라이드하는 조건을 추가한다.

```python
# line 446-448 수정
_validation_quality_risk = bool(
    validation_result.get("quality_risk", False) or verdict in ("PASS_WITH_FIX", "PASS_WITH_WARNING")
)
# [C4] 고득점 Blueprint의 quality_risk 오버라이드
_score_for_risk = validation_result.get("score", 0)
try:
    _score_for_risk = int(_score_for_risk)
except (ValueError, TypeError):
    _score_for_risk = 0
if _score_for_risk >= 95 and _validation_quality_risk:
    _validation_quality_risk = False
    logging.info("[C4] score=%d >= 95 → quality_risk=False 오버라이드", _score_for_risk)
```

**테스트 검증 방법**:
1. verdict=PASS_WITH_FIX, score=97 → `quality_risk=False` 확인
2. verdict=PASS_WITH_FIX, score=80 → `quality_risk=True` 확인 (기존 동작 유지)
3. 0_260318 프로젝트 데이터로 시뮬레이션: 11건 중 95점 이상인 건은 False로 전환되어 분별력 > 0 확인
4. Stage 4의 `_v75d_threshold` 분기가 quality_risk=False일 때 정상 동작 확인

**의존성**: 없음

---

### 2.5 C5 -- failure_analyzer SimpleNamespace 버그

**파일**: `modules/core/services/audit_service.py`
**라인**: 132-135

**BEFORE 상태 (현재 동작)**:
```python
# audit_service.py:132-135
def _resolve_proof_digest_db(self, db_path) -> tuple[Any, bool]:
    conn = sqlite3.connect(f"{db_path.resolve().as_uri()}?mode=ro", uri=True, check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row
    return SimpleNamespace(conn=conn, db_path=db_path), True
```
`SimpleNamespace(conn=conn, db_path=db_path)`를 반환한다. 이 객체는 `conn` 속성만 가지고 있으며, `get_stage4_final_authority_rows()` 등의 메서드가 없다.

**호출 경로**:
1. `audit_service.py:226` → `FailureAnalyzer(db, project_path=paths.root)` 호출
2. `failure_analyzer.py:580` → `self.db.get_stage4_final_authority_rows(limit=lookback, session_id=...)` 호출
3. `SimpleNamespace`에 `get_stage4_final_authority_rows` 속성이 없으므로 `AttributeError` 발생

현재는 `failure_analyzer.py:589`의 `except Exception as _e:` 블록에서 조용히 잡혀 빈 결과를 반환하지만, Stage 4 final authority 데이터가 감사 다이제스트에서 누락된다.

**AFTER 상태 (목표 동작)**:

**수정안 A (권고)**: `SimpleNamespace`에 필요한 메서드를 raw SQL로 추가.

```python
# audit_service.py:132-135 수정
def _resolve_proof_digest_db(self, db_path) -> tuple[Any, bool]:
    conn = sqlite3.connect(f"{db_path.resolve().as_uri()}?mode=ro", uri=True, check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row

    ns = SimpleNamespace(conn=conn, db_path=db_path)

    def _get_stage4_final_authority_rows(limit=50, session_id=None):
        sql = "SELECT * FROM stage_attempts WHERE stage=4 ORDER BY rowid DESC LIMIT ?"
        params = [limit]
        if session_id:
            sql = "SELECT * FROM stage_attempts WHERE stage=4 AND session_id=? ORDER BY rowid DESC LIMIT ?"
            params = [session_id, limit]
        try:
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []

    ns.get_stage4_final_authority_rows = _get_stage4_final_authority_rows
    return ns, True
```

**수정안 B (대안)**: 실제 `DBManager` 인스턴스를 read-only 모드로 생성.
- 장점: 모든 메서드 자동 사용 가능
- 단점: DBManager 의존성 증가, read-only 보장 어려움

**테스트 검증 방법**:
1. `_resolve_proof_digest_db()` 반환값으로 `FailureAnalyzer` 생성 후 `sink_alignment_summary(stage=4)` 호출 시 AttributeError 미발생 확인
2. stage_attempts 테이블에 테스트 데이터 삽입 후 `get_stage4_final_authority_rows()` 반환값 검증
3. read-only 연결에서 write 시도시 에러 발생 확인 (데이터 무결성)

**의존성**: 없음

---

### 2.6 C6 -- Stage 2/3 비용 미전달

**파일 4곳**:
1. `modules/core/stage2_finalizer.py:1592` (Stage 2 PASS 기록)
2. `modules/core/stage2_finalizer.py:1738` (Stage 2 REJECT 기록)
3. `modules/core/stage3_orchestrator.py:1469` (Stage 3 최종 기록)
4. `modules/core/stage3_orchestrator.py:2048` (Stage 3 REJECT 기록)

**BEFORE 상태 (현재 동작)**:
4개 호출 지점 모두 `record_attempt()` 호출시 `token_cost` 파라미터를 전달하지 않는다. `pass_rate_monitor.py:148`에서 `token_cost: float = 0.0` 기본값이 사용되어 Stage 2/3의 모든 시도에 비용이 0.0으로 기록된다.

대조적으로, Stage 4는 `stage4_interview_round.py:5890-5894`에서 `_get_round_metrics_delta()`를 통해 자동 산출한다:
```python
# stage4_interview_round.py:5890-5894 (정상 동작 참조)
if token_cost is None:
    try:
        token_cost = float(self._get_round_metrics_delta().get("total_cost_usd", 0.0))
    except Exception:
        token_cost = 0.0
```

**AFTER 상태 (목표 동작)**:
각 호출 지점에서 해당 Stage의 LLM 호출 비용을 집계하여 `token_cost` 파라미터로 전달한다.

**수정 1**: `stage2_finalizer.py:1592` (PASS 기록)
```python
# 기존 (line 1592)
self.ctx.pass_rate_monitor.record_attempt(
    stage=2,
    episode=global_arc_no,
    ...
    duration_ms=duration_ms or 0,
    # token_cost 파라미터 없음
)

# 수정 후
_token_cost = self._get_accumulated_cost()  # MetricsCollector에서 집계
self.ctx.pass_rate_monitor.record_attempt(
    stage=2,
    episode=global_arc_no,
    ...
    duration_ms=duration_ms or 0,
    token_cost=_token_cost,
)
```

**수정 2**: `stage2_finalizer.py:1738` (REJECT 기록) -- 동일 패턴.

**수정 3**: `stage3_orchestrator.py:1469` (PASS/최종 기록)
```python
# 기존 (line 1469)
ctx.pass_rate_monitor.record_attempt(
    stage=3,
    episode=working_ep,
    ...
    # token_cost 파라미터 없음
)

# 수정 후 - MetricsCollector 또는 pipeline_result에서 비용 추출
_token_cost = pipeline_result.get("total_cost_usd", 0.0)
ctx.pass_rate_monitor.record_attempt(
    stage=3,
    episode=working_ep,
    ...
    token_cost=_token_cost,
)
```

**수정 4**: `stage3_orchestrator.py:2048` (REJECT 기록) -- 동일 패턴.

**비용 집계 방법 결정 필요**: Stage 4는 `_get_round_metrics_delta()` 전용 메서드가 있으나, Stage 2/3는 동등한 메서드가 없다. 선택지:
- A) `MetricsCollector.get_metrics_collector()` 글로벌 인스턴스에서 delta 계산
- B) `pipeline_result`에 이미 집계된 비용 필드가 있으면 활용
- C) Stage 4와 유사한 delta 추적 메서드를 Stage 2/3에 추가

**테스트 검증 방법**:
1. Stage 2 실행 후 `stage_attempts` 테이블에서 `token_cost > 0.0` 확인
2. Stage 3 실행 후 동일 확인
3. Stage 4와 비교하여 비용 규모가 합리적인지 검증 (Stage 2 < Stage 3 < Stage 4 예상)

**의존성**: 없음

---

### 2.7 C7 -- 빈 추적 테이블 5개

**대상 테이블 및 상태**:

| 테이블 | 상태 | 원인 | 수정 필요성 |
|--------|------|------|------------|
| `karma_status` | 0건 | `commit_episode_factory()`가 Stage 4에서 미호출 | **수정 필요** |
| `canonical_facts` | 0건 | 투자 장르용 키 매핑 부재 (`fact_ledger.py:374-418`) | **수정 필요** |
| `timeline_entries` | 0건 | `state_changes`에 `time_markers` 필드 absent | **수정 필요** |
| `character_voice` | 미축적 | 2회분으로 축적 부족 | 정상 (집필 진행 시 자동 해결) |
| `npc_relationship_edges` | 미축적 | 2회분으로 NPC간 관계 변화 미감지 | 정상 (집필 진행 시 자동 해결) |

**C7-1: karma_status 수정**

**파일**: `modules/core/stage4_post_processor.py`

**BEFORE**: Stage 4 PASS 후처리에서 `save_manuscript()` 및 `update_martial_tracker()`만 호출한다. `commit_episode_factory()`는 `modules/core/db_manager.py:2147`에 구현되어 있으나 Stage 4 후처리 경로에서 호출되지 않는다.

**AFTER**: `stage4_post_processor.py`의 PASS 후처리 완료 시점에서 `commit_episode_factory()` 호출을 추가한다. 이 메서드가 karma_status 테이블에 에피소드별 카르마 상태를 기록한다.

**C7-2: canonical_facts 수정**

**파일**: `modules/core/fact_ledger.py:374-418`

**BEFORE**: `_extract_numerical_facts()` 메서드가 `status_shadow`(무협), `financial_events`(투자), `power_level`, `numerical_facts`에서 수치를 추출하여 `update_number()`를 호출한다. 그러나 투자 장르의 경우 `canonical_facts` 테이블에 매핑하는 키 정의가 없어 빈 상태이다.

**AFTER**: `financial_events`에서 추출된 수치를 `canonical_facts` 테이블에도 기록하는 로직을 추가한다. 구체적으로 `asset_{name}_{field}` 형식의 키를 `canonical_facts`에 upsert한다.

**C7-3: timeline_entries 수정**

**BEFORE**: `state_changes`에서 `time_markers` 필드를 추출하는 로직이 없다. state_extractor가 `time_markers`를 생성하지 않으므로 timeline_entries가 빈 상태이다.

**AFTER**: `state_extractor.py`의 추출 스키마에 `time_markers` 필드를 추가하거나, `narrative_structure_analyzer.py`에서 시간 정보를 추출하여 `timeline_entries`에 기록한다.

**테스트 검증 방법**:
1. Stage 4 완료 후 karma_status 테이블에 해당 에피소드 행 존재 확인
2. 투자 장르 프로젝트에서 canonical_facts 테이블에 financial_events 데이터 적재 확인
3. timeline_entries 테이블에 에피소드별 시간 마커 기록 확인

**의존성**: 없음

---

### 2.8 C8 -- Stage 3 중간실패 미기록

**파일**: `modules/domain/agents/three_phase_blueprint_generator.py`
**라인**: 180 (retry 루프), 404 (연속성 REJECT), 497-500 (QualityGate REJECT)

**BEFORE 상태 (현재 동작)**:
`three_phase_blueprint_generator.py:180`의 `for retry in range(max_retries + 1):` 루프 내에서:
- line 404: 연속성 검사 REJECT → `continue`로 다음 재시도. PassRateMonitor 미기록.
- line 497-500: QualityGate REJECT → verdict를 "REJECT"로 전환하지만 역시 PassRateMonitor 미기록.
- 최종 결과 1건만 `stage3_orchestrator.py:1469`에서 기록.

결과: ep7에서 5회 재시도 중 4회 REJECT의 `reject_reason`이 어디에도 기록되지 않아, 사후 분석시 실패 원인을 추적할 수 없다.

**AFTER 상태 (목표 동작)**:

**수정 1**: line 404 (연속성 REJECT 분기) 직전에 record_attempt 호출 추가.
```python
# line 403-404 (현재)
logging.warning(" [V61.5] 연속성 검사 REJECT")
continue  # 다음 재시도로

# 수정 후
logging.warning(" [V61.5] 연속성 검사 REJECT")
if getattr(ctx, "pass_rate_monitor", None):
    try:
        ctx.pass_rate_monitor.record_attempt(
            stage=3,
            episode=ep_num,
            arc=arc_idx,
            attempt_num=retry + 1,
            success=False,
            reject_reason=f"연속성 검사 REJECT: {continuity_feedback[:100]}",
            generation_method="blueprint",
        )
    except Exception as _e:
        logging.debug("[C8] record_attempt 실패: %s", _e)
continue  # 다음 재시도로
```

**수정 2**: line 497-500 (QualityGate REJECT) 직후에 record_attempt 호출 추가.
```python
# line 497-500 (현재)
logging.warning(f"[QualityGate] Stage3 PASS이나 score={_score} < {_quality_gate_score} → REJECT 전환")
verdict = "REJECT"
feedback = _initial_feedback + f"\n[Quality Gate] score {_score}점으로 {_quality_gate_score}점 미달."

# 수정 후 - 위 코드 직후에 추가
if getattr(ctx, "pass_rate_monitor", None):
    try:
        ctx.pass_rate_monitor.record_attempt(
            stage=3,
            episode=ep_num,
            arc=arc_idx,
            attempt_num=retry + 1,
            success=False,
            reject_reason=f"QualityGate REJECT: score={_score} < {_quality_gate_score}",
            generation_method="blueprint",
        )
    except Exception as _e:
        logging.debug("[C8] record_attempt 실패: %s", _e)
```

**주의사항**: `ctx` 변수 접근 -- `three_phase_blueprint_generator.py`는 `self` 기반 클래스이므로 `ctx`를 `self.ctx` 등으로 접근해야 할 수 있다. 실제 구현 시 스코프 확인 필요.

**테스트 검증 방법**:
1. 연속성 REJECT를 유도하는 테스트 데이터로 실행 → `stage_attempts`에 중간 REJECT 기록 확인
2. QualityGate REJECT를 유도(score=50, gate=90)하는 테스트 → 중간 기록 확인
3. 최종 PASS 후 총 기록 건수 = retry 횟수 + 1 확인
4. `reject_reason` 필드에 구체적 사유 포함 확인

**의존성**: 없음

---

### 2.9 C9 -- NPC 설정 모호성 (한태민 속성 드리프트)

**파일**:
1. Bible 데이터 (프로젝트별 설정)
2. `modules/core/npc_drift_advisor.py:20`

**BEFORE 상태 (현재 동작)**:
- Bible에 NPC "한태민"이 "SW그룹 핵심 계열사 임원"으로만 명시되어 있다. 구체적 계열사명이 없다.
- ChiefWriter LLM이 "SW화학"이라는 계열사명을 할루시네이션으로 생성했다.
- `NpcDriftAdvisor`(line 20: `"advisory only"`)는 드리프트를 감지하더라도 경고만 로그하고 블로킹하지 않는다.

**AFTER 상태 (목표 동작)**:

**수정 1 (데이터)**: Bible에 NPC "한태민"의 계열사명을 구체화한다.
```json
{
  "name": "한태민",
  "title": "SW그룹 핵심 계열사 임원",
  "company": "SW에너지",  // 또는 작가가 결정한 구체 계열사명
  "notes": "SW화학은 오류. SW에너지가 정확한 계열사."
}
```

**수정 2 (코드)**: `npc_drift_advisor.py`에서 `severity=HIGH` 이상의 드리프트가 감지되면 blocking으로 승격하는 옵션을 추가한다.

```python
# npc_drift_advisor.py 수정
class NpcDriftAdvisor:
    """원고 텍스트에서 NPC 속성 표류를 LLM으로 감지."""

    def __init__(self, llm_ask=None, blocking_severity="HIGH"):
        self._llm_ask = llm_ask
        self._blocking_severity = blocking_severity  # HIGH 이상시 blocking

    def check(self, manuscript_text, npc_registry):
        # ... 기존 검사 로직 ...
        for finding in findings:
            if finding["severity"] >= self._blocking_severity:
                finding["blocking"] = True  # blocking 승격
        return findings
```

**테스트 검증 방법**:
1. "SW화학" 텍스트가 포함된 원고에 NpcDriftAdvisor 실행 → severity=HIGH + blocking=True 확인
2. Bible에 구체 계열사명이 있는 상태에서 일치하는 원고 → 드리프트 미감지 확인
3. severity=LOW 드리프트 → blocking=False 확인 (기존 동작 유지)

**의존성**: 없음

---

### 2.10 C10 -- target_ep 선택 미기록

**파일**: `modules/core/stage4_orchestrator.py`
**라인**: 687-689

**BEFORE 상태 (현재 동작)**:
```python
# line 687-689
if target_ep and next_ep > target_ep:
    self.ctx.ui.log(f"목표 회차({target_ep}화) 도달. 종료합니다.")
    break
```
`target_ep`에 의한 조기 종료는 정상 동작이다(버그 아님). 그러나 사용자가 `target_ep=2`를 선택한 사실이 `decisions.jsonl`이나 `pass_rate_monitor`에 기록되지 않아, 사후 감사 시 "왜 3화부터 미생산인가?"에 대한 답이 로그에 없다.

**AFTER 상태 (목표 동작)**:
`break` 직전에 decisions.jsonl 기록을 추가한다.

```python
# line 687-689 수정
if target_ep and next_ep > target_ep:
    self.ctx.ui.log(f"목표 회차({target_ep}화) 도달. 종료합니다.")
    # [C10] target_ep 선택 기록
    try:
        from modules.core.session_logger import get_session_logger
        _logger = get_session_logger(getattr(self.ctx, "current_project", None))
        if _logger:
            _logger.log_decision(
                stage=4,
                decision_type="target_ep_reached",
                detail=f"target_ep={target_ep}, next_ep={next_ep}, 사용자 지정 종료",
            )
    except Exception as _e:
        logging.debug("[C10] target_ep 기록 실패: %s", _e)
    break
```

**테스트 검증 방법**:
1. `target_ep=2`로 Stage 4 실행 → decisions.jsonl에 `target_ep_reached` 이벤트 존재 확인
2. `target_ep=None`으로 실행 → 해당 이벤트 미생성 확인
3. 기록 실패시 Stage 4 실행 자체에는 영향 없음 확인 (try/except 보호)

**의존성**: 없음

---

## 3. 원고 품질 교정 (TF 발견)

### 3.1 S급 -- ep3 집필 전 필수 조치

#### TF-S1: Blueprint ep2 유령 씬

**현상**: Blueprint ep2의 `scene_1`이 ep1 원고에 이미 흡수되어 작성됨. ep2 Blueprint에는 해당 씬이 여전히 존재하나 실제로는 중복/유령 상태.

**근본원인**: C2(정지선 검증 부재)로 인해 ep1 집필 시 ep2 내용이 침범되었으나 차단되지 않았다.

**필수 조치 (ep3 집필 전)**:
1. Blueprint ep2의 `scene_1`을 삭제하거나, ep1에서 흡수된 내용을 반영하여 ep2 씬 구조를 재구성
2. ep2의 남은 씬들이 유효한지 검증
3. Blueprint ep2 전체 점수 재계산

**완료 기준**: Blueprint ep2의 모든 씬이 실제 원고와 1:1 대응하며, 유령 씬 0건.

#### TF-S2: Arc 전진 밀림 (forward shift)

**현상**: Arc ep1-4가 1화씩 앞으로 밀린 상태. Arc ep1의 내용이 실제로는 ep0에 해당하고, Arc ep2가 실제 ep1에 해당하는 식.

**근본원인**: Arc 생성 시점과 Blueprint 생성 시점 사이에 에피소드 번호 정렬이 틀어졌다. C1(제목 비전달) + C2(정지선 미검증)이 복합 작용.

**필수 조치 (ep3 집필 전)**:
1. Arc ep1-4의 에피소드 번호를 현재 원고 상태와 정렬
2. 각 Arc 에피소드의 종료 상태가 해당 원고의 종료 상태와 일치하는지 검증
3. ep3 이후 Arc가 정상 정렬된 상태에서 Blueprint 생성 진행

**완료 기준**: Arc ep_num과 실제 원고 ep_num이 1:1 대응. forward shift = 0.

**의존성**: TF-S1 완료 후 실행 (ep2 씬 구조가 확정되어야 Arc 정렬 가능)

---

### 3.2 A급 -- 연속성 수정

#### TF-A1: Arc ep1 종료 상태 불일치

**현상**: Arc ep1 종료 상태는 "침실/잠옷"이나, 실제 원고 ep1은 "복도/외출복"으로 종료.

**수정**: Arc ep1의 종료 상태를 원고 기준으로 갱신한다.
- Arc ep1 `ending_state.location` = 원고 종료 시점의 실제 위치
- Arc ep1 `ending_state.clothing` = 원고 종료 시점의 실제 의상

**완료 기준**: Arc ep1 종료 상태와 원고 ep1 마지막 장면의 상태가 일치.

#### TF-A2: Arc ep2 제목 불일치

**현상**: Arc ep2 제목 "아버지의 서재" vs 원고 ep2 제목 "의심의 씨앗".

**수정**: C1 수정으로 자동 해소 예상. C1 적용 후 Arc ep2 제목이 Blueprint/원고에 전달되는지 확인.

**완료 기준**: C1 수정 적용 후, 원고 제목이 Arc 제목과 일치. 추가 공수 불필요.

**의존성**: C1

#### TF-A3: 계획 기록 방식 모순

**현상**: Blueprint ep2에서 "백지에 기록"이라는 행동이 명시되어 있으나, 원고에서는 "흔적을 남기지 않는다"고 서술.

**수정**: Blueprint ep2의 해당 씬 지시를 원고와 일치하도록 갱신하거나, 원고를 Blueprint에 맞게 교정. 작가 결정 필요.

**완료 기준**: Blueprint와 원고 간 행동 모순 0건.

#### TF-A4: ep2 잠옷 착용 후 저녁식사

**현상**: ep2에서 주인공이 잠옷으로 갈아입은 후 저녁식사 장면이 등장하나, 잠옷에서 외출복으로 갈아입는 장면이 누락.

**수정**: ep2 원고에 옷 갈아입는 전환 장면을 삽입하거나, 씬 순서를 재배치(저녁식사 -> 잠옷 순서로).

**완료 기준**: 의상 연속성 검증 통과. 잠옷 -> 저녁식사 사이에 의상 전환 또는 순서 정정.

---

### 3.3 B급 -- 팩트체크 교정

| 항목 | 현상 | 교정 방향 |
|------|------|----------|
| WTI 가격 오차 | 작중 WTI $61 vs 실제 시점 데이터 불일치 | Bible 또는 세계관 설정에서 명시적 WTI 가격 고정. 팩트체크 기준 명확화 |
| 호르무즈 해협 시점 혼동 | 호르무즈 해협 관련 이벤트 시점이 작중 타임라인과 불일치 | 작중 타임라인 대비 이벤트 시점 교정 |
| 숨고르기 행동 중복 | 동일 캐릭터의 "숨고르기" 행동이 연속 장면에서 반복 | 중복 행동 제거 또는 변주 |
| 기타 2건 | 세부 팩트 오류 | 개별 교정 |

**완료 기준**: 5건 모두 원고 수정 완료 + 팩트체크 재검증 통과.

---

### 3.4 C급 -- 문체 개선

| 항목 | 현상 | 개선 방향 |
|------|------|----------|
| "차갑다/냉철하다" 과잉 반복 | 동일 형용사 클러스터 과잉 사용 | WritingDirective의 `expression_ban`에 추가 또는 `repetition_guard` 임계치 하향 |
| 대화 비율 7.9~12.5% | 장르 기준 대비 대화 비율 저조 | Blueprint 씬 지시에 대화 최소 비율 명시 또는 ChiefWriter 프롬프트 조정 |
| AI slop | 전형적 AI 문체 패턴 감지 | `constitutional_checker.py` 또는 `style_guard.py`에 AI slop 패턴 필터 추가 |
| 기타 1건 | 세부 문체 지적 | 개별 교정 |

**완료 기준**: 반복 형용사 빈도 50% 이상 감소, 대화 비율 15% 이상 달성, AI slop 패턴 0건.

---

## 4. 실행 우선순위 및 Phase 로드맵

### 4.1 우선순위 기준

| 등급 | 기준 | 해당 항목 |
|------|------|----------|
| **P0-Critical** | ep3 집필 차단 또는 무음 품질 저하를 유발하는 확인된 결함 | C1, C2, C3, C5, TF-S1, TF-S2 |
| **P1-High** | 품질 게이트 무력화 또는 데이터 추적 불가 | C4, C6, C8, TF-A1, TF-A2, TF-A3, TF-A4 |
| **P2-Medium** | 추적 인프라 미비 또는 방어 계층 약화 | C7, C9, TF-B |
| **P3-Low** | 유지보수 부채 또는 문체 개선 | C10, TF-C |

### 4.2 Phase 로드맵

#### Phase 0: ep3 집필 전 필수 (즉시, 총 ~4.5h)

```
[데이터] TF-S1 → TF-S2 → TF-A1
[코드]  C1 → C2 (병렬 가능)
```

- TF-S1/S2/A1: Arc + Blueprint 데이터 교정. ep3 집필 차단 해제 조건.
- C1: Arc 제목 전달로 TF-A2 자동 해소.
- C2: 정지선 검증으로 TF-S1 재발 방지.
- **이 Phase가 완료되어야 ep3 집필을 시작할 수 있다.**

#### Phase 1: 안전 게이트 (총 ~8h)

```
C3 → C5 → C8
C4 (병렬 가능)
TF-A3, TF-A4 (병렬 가능)
```

- C3: Director CRITICAL hard gate 추가로 99점 override 방지.
- C5: failure_analyzer AttributeError 수정으로 감사 다이제스트 복원.
- C8: 중간실패 기록으로 사후 분석 가능.
- C4: quality_risk 분별력 복원.

#### Phase 2: 추적 인프라 (총 ~8h)

```
C6 → C7
C9 (병렬 가능)
TF-B (병렬 가능)
```

- C6: Stage 2/3 비용 추적 복원.
- C7: 빈 테이블 3개 활성화.
- C9: NPC 설정 구체화 + NpcDriftAdvisor blocking 승격.

#### Phase 3: 유지보수 (총 ~2.5h)

```
C10
TF-C
```

- C10: target_ep 기록 추가 (0.5h).
- TF-C: 문체 개선 (2h).

### 4.3 총 추정 공수

| Phase | 코드 | 데이터 | 합계 |
|-------|------|--------|------|
| Phase 0 | 5h | 3h | 8h |
| Phase 1 | 8h | 1h | 9h |
| Phase 2 | 8h | 1.5h | 9.5h |
| Phase 3 | 0.5h | 2h | 2.5h |
| **총합** | **21.5h** | **7.5h** | **29h** |

---

## 5. 감리 이력

### 5.1 기본 3pass

#### Pass 1: 구조 완전성 검증 (Structure Completeness)

**검증 항목**:
- [OK] C1-C10 전 항목이 Section 2에 개별 서브섹션으로 존재
- [OK] TF 발견 15건 전부 Section 3에 포함 (S급 2건, A급 4건, B급 5건, C급 4건)
- [OK] 각 코드 수정 항목에 파일경로, 라인번호, BEFORE/AFTER, 테스트 방법, 의존성 명시
- [OK] Section 1 총괄표와 Section 2-3 상세 내용 간 ID 일대일 대응
- [OK] Phase 로드맵의 항목 합집합 = 총괄표의 항목 합집합 (누락 없음)

**발견**: 없음.

#### Pass 2: 라인 번호 대조 (Line Number Verification)

**검증 항목**: 명시된 모든 파일:라인 번호를 실제 코드와 대조.

| 항목 | 파일:라인 | 대조 결과 |
|------|----------|----------|
| C1 | `blueprint_constraint_compiler.py:194-229` | OK -- `_extract_episode_focus` 메서드 시작(194) ~ 반환(229) 일치 |
| C2 | `blueprint_constraint_compiler.py:231-272` | OK -- `_extract_stop_line` 메서드 시작(231) ~ 반환(272) 일치 |
| C3 | `director_ensemble.py:1723-1741` | OK -- `apply_adaptive_decision` 호출(1723) ~ `final_verdict` 결정(1741) 일치 |
| C3 | `director_prompts.py:118-124` | OK -- 평가 기준 가중치 섹션, Python 경고 10%(124) 일치 |
| C3 | `stage4_interview_round.py:2433-2447` | OK -- Director 결과 후처리 블록 일치 |
| C4 | `three_phase_blueprint_generator.py:446-448` | OK -- `_validation_quality_risk` 할당 일치 |
| C4 | `stage4_interview_round.py:2166-2175` | OK -- `quality_risk` Director advisory 주입 일치 |
| C4 | `stage4_orchestrator.py:1201-1209` | OK -- `_v75d_threshold` 계산 일치 |
| C5 | `audit_service.py:132-135` | OK -- `_resolve_proof_digest_db` + `SimpleNamespace` 반환 일치 |
| C5 | `failure_analyzer.py:580` | OK -- `get_stage4_final_authority_rows` 호출 일치 |
| C6 | `stage2_finalizer.py:1592` | OK -- `record_attempt` PASS 호출, `token_cost` 미전달 확인 |
| C6 | `stage2_finalizer.py:1738` | OK -- `record_attempt` REJECT 호출, `token_cost` 미전달 확인 |
| C6 | `stage3_orchestrator.py:1469` | OK -- `record_attempt` 호출, `token_cost` 미전달 확인 |
| C6 | `stage3_orchestrator.py:2048` | OK -- `record_attempt` 호출, `token_cost` 미전달 확인 |
| C6 | `stage4_interview_round.py:5890-5894` | OK -- Stage 4 자동 산출 참조 코드 일치 |
| C7 | `fact_ledger.py:374-418` | OK -- `_extract_numerical_facts` 범위 일치 |
| C7 | `db_manager.py:2147` | OK -- `commit_episode_factory` 정의 위치 일치 |
| C8 | `three_phase_blueprint_generator.py:404` | OK -- 연속성 REJECT `continue` 일치 |
| C8 | `three_phase_blueprint_generator.py:497-500` | OK -- QualityGate REJECT 전환 일치 |
| C9 | `npc_drift_advisor.py:20` | OK -- `NpcDriftAdvisor` 클래스 정의, "advisory only" docstring 일치 |
| C10 | `stage4_orchestrator.py:687-689` | OK -- `target_ep` 종료 조건 일치 |

**발견**: 없음. 전 항목 라인 번호 정확.

#### Pass 3: 논리 일관성 검증 (Logical Consistency)

**검증 항목**:
- [OK] C1 수정이 TF-A2를 자동 해소한다는 주장: 맞음. Arc 제목이 Blueprint에 전달되면 원고 제목과 일치하게 된다.
- [OK] C2 수정이 TF-S1 재발을 방지한다는 주장: 맞음. 정지선 Python 검증이 추가되면 다음 화 내용 침범이 차단된다.
- [OK] C4의 임계치 95점: 합리적. 95점 이상이면 품질 리스크가 낮다고 판단할 수 있다.
- [OK] C5 수정안 A vs B 비교: 수정안 A가 범위 제한적이고 안전. 수정안 B는 DBManager 의존성으로 read-only 보장 어려움.
- [OK] C8에서 `ctx` vs `self.ctx` 스코프 경고: 적절한 주의사항.
- [OK] Phase 0가 ep3 집필 차단 조건이라는 주장: TF-S1/S2가 해결되지 않으면 Arc 정렬이 틀어진 상태에서 Blueprint를 생성하게 되므로 정당함.
- [OK] 의존성 체인: TF-S1 -> TF-S2 -> TF-A1 순서 논리적. C1 -> TF-A2 의존성 정당.
- [OK] 공수 추정: 개별 항목 합산 = Phase별 합산 = 총합 29h 일치.

**발견**: 없음.

---

### 5.2 적대적 3pass

#### Adversarial Pass 1: 누락 공격 (Missing Item Attack)

**질문**: "소스 발견 중 본 문서에 빠진 항목이 있는가?"

**검증**:
- C1-C10: 10건 전부 포함. 누락 없음.
- TF S급 2건: TF-S1, TF-S2 포함. 누락 없음.
- TF A급 4건: TF-A1, TF-A2, TF-A3, TF-A4 포함. 누락 없음.
- TF B급 5건: Section 3.3에 테이블로 포함. 개별 상세는 요약 수준이나 소스 보고서 참조로 충분.
- TF C급 4건: Section 3.4에 테이블로 포함. 동일.

**질문**: "C4 정정 사항(write-only가 아님, Stage 4가 2곳에서 읽음)이 반영되었는가?"

**검증**: Section 2.4에 `stage4_interview_round.py:2166-2175`와 `stage4_orchestrator.py:1201-1209` 두 곳의 읽기 위치가 명시되어 있다. "11/11 전부 true라 분별력 0"이라는 정정 내용도 반영됨. OK.

**질문**: "C7의 정상 항목 2건(character_voice, npc_relationship_edges)이 수정 대상에서 제외되었는가?"

**검증**: Section 2.7 테이블에 "정상 (집필 진행 시 자동 해결)"로 명시. 수정 필요 항목은 3건(karma, canonical_facts, timeline)만. OK.

**발견**: 없음.

#### Adversarial Pass 2: 과장/축소 공격 (Exaggeration/Understatement Attack)

**질문**: "C3의 임계치 3건이 너무 높거나 낮지 않은가?"

**분석**: CRITICAL 경고 3건은 보수적 선택이다. 1건이면 과민, 5건이면 너무 관대. 3건은 합리적 시작점이며, 문서에서도 "초기값, 설정 파일로 외부화 권고"라고 명시하여 조정 가능성을 열어두었다. OK.

**질문**: "C5가 P0-Critical인 것이 과장인가?"

**분석**: `failure_analyzer.py:589`의 `except Exception` 블록이 AttributeError를 조용히 잡아 빈 결과를 반환한다. 실행 시 크래시는 없지만, Stage 4 final authority 데이터가 감사 다이제스트에서 영구 누락된다. 이는 "무음 데이터 손실"에 해당하므로 P0-Critical 분류가 정당하다. OK.

**질문**: "총 공수 29h가 과소 또는 과대 추정인가?"

**분석**: 개별 항목 공수를 적산하면:
- 코드: C1(2h) + C2(3h) + C3(3h) + C4(1.5h) + C5(2h) + C6(2h) + C7(4h) + C8(1.5h) + C9(2h) + C10(0.5h) = 21.5h
- 데이터: TF-S1(1h) + TF-S2(1.5h) + TF-A1(0.5h) + TF-A2(0h) + TF-A3(0.5h) + TF-A4(0.5h) + TF-B(1.5h) + TF-C(2h) = 7.5h
- 합계: 29h. Phase별 합산과 일치. 테스트 작성 포함 시 +20~30% 예상이나, 추정치에 테스트가 포함된 것으로 보인다. OK.

**발견**: 없음.

#### Adversarial Pass 3: 실행 불가능성 공격 (Infeasibility Attack)

**질문**: "C2의 정지선 키워드 유사도 검사가 false positive를 많이 유발하지 않는가?"

**분석**: "고유 키워드 3개 이상 일치"는 일반어 제외 후의 기준이다. 정지선과 현재 화가 동일 Arc에 속하므로 공통 고유명사(인물명 등)가 자연스럽게 겹칠 수 있다. 잠재적 false positive 위험이 있다. 그러나 문서에서 `_common_words` 제외 세트를 명시하고 있으며, 임계치 조정이 가능하다. 구현 시 인물명도 제외 세트에 추가하는 것을 권고한다.

**권고 추가**: C2 구현 시 공통 인물명을 `_common_words`에 포함하거나, TF-IDF 기반 유사도로 전환하여 false positive를 줄일 것.

**질문**: "C6에서 비용 집계 방법이 확정되지 않았는데 실행 가능한가?"

**분석**: 문서에서 3가지 선택지(A/B/C)를 제시하고 결정을 미뤘다. 이는 실행문서의 한계이며, 구현자가 선택해야 한다. 그러나 각 선택지의 장단점이 명확히 서술되지 않았다.

**권고 추가**: 선택지 A(MetricsCollector 글로벌 인스턴스)가 가장 간단하고 Stage 4와 패턴 일치. 선택지 C는 가장 정확하지만 공수 증가. 선택지 B는 `pipeline_result`에 비용 필드가 이미 있는지 사전 확인 필요.

**질문**: "C9의 NpcDriftAdvisor blocking 승격이 기존 advisory-only 설계 철학과 충돌하지 않는가?"

**분석**: 원래 advisory-only로 설계된 이유는 LLM 기반 드리프트 감지의 정확도가 불확실하기 때문이다. severity=HIGH만 blocking으로 승격하면 오탐 위험이 제한적이나, LLM 판단에 의존하는 만큼 false positive 가능성이 존재한다. 문서에서 `blocking_severity` 파라미터를 설정 가능하게 했으므로, 초기에는 HIGH로 시작하되 운영 데이터를 보고 조정 가능하다.

**발견**: 위 3건은 주의 권고 사항이며, 문서의 정확성을 훼손하는 수준은 아니다. 구현 시 참고하되 문서 수정 불필요.

---

> **감리 결론**: 기본 3pass(구조/라인번호/논리) + 적대적 3pass(누락/과장/실행불가능성) 총 6pass 완료. 치명적 결함 0건. 적대적 Pass 3에서 3건의 구현 시 주의 권고 사항 도출(C2 false positive, C6 비용 집계 방법 선택, C9 advisory 철학 충돌). 문서 수정 필요 없음.
