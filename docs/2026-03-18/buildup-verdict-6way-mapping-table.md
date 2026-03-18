# Verdict 상태 통합 매핑표

**문서 유형**: 빌드업 (S6-EX-10 + S7-OPP-01/02 선행 설계)
**작성일**: 2026-03-18
**상태**: MAPPING — 코드 미착수
**감리**: 3회 전면 재조사 + 적대적 3-pass 완료 (6 TF 병렬 투입)
**교정 이력**: 초판 6개 → 2차 9개 → **3차 9 Core + 7 Contextual = 16개** (CONFLICT/WARNING/RETRY/AGREE/DISMISS/UNKNOWN/FAIL 추가)

---

## 1. Verdict 전수 조사 결과

### 1.1 스키마 정의 verdict (LLM이 반환하는 값)

| 값 | 정의 위치 | 스키마명 |
|----|----------|---------|
| **PASS** | `response_schemas.py:132` | DIRECTOR_AUDIT_SCHEMA |
| **PASS_WITH_FIX** | `response_schemas.py:132` | DIRECTOR_AUDIT_SCHEMA |
| **REJECT** | `response_schemas.py:132` | DIRECTOR_AUDIT_SCHEMA |

동일 enum이 `STRATEGIC_AUDIT_SCHEMA` (L181)에도 반복 정의.

> **주의**: LLM 스키마에 정의된 verdict는 이 3개뿐. 나머지는 전부 Python 내부 로직에서 생성.

### 1.2 Python 내부 verdict (코드에서 생성하는 값)

| 값 | SET 위치 | 용도 |
|----|---------|------|
| **CONDITIONAL_PASS** | `validation_orchestrator.py:701,1402` | 점수 60-84 구간 |
| **PASS_WITH_WARNING** | `three_phase_blueprint_generator.py:745` | quality_gate_failed + 충분한 점수 시 |
| **FAILED** | `three_phase_blueprint_generator.py:737,752`, `four_phase_arc_generator.py:1128,1356,1361,1452` | 모든 재시도 소진 |
| **ERROR** | `stage3_orchestrator.py:1366,1369` | 스키마 호환/파싱 실패 (※ :736,:129는 비교문, SET 아님) |
| **EMPTY** | `stage4_interview_round.py:2025,2045` | Stage 4 유효 후보 없음 |
| **SKIP** | `director_continuity.py:637` | 연속성 판단 보류 |

### 1.3 컨텍스트별 decision 값 (verdict와 별도 시스템 — 3차 재조사 발견)

| 값 | SET 위치 | 컨텍스트 | verdict 여부 |
|----|---------|---------|-------------|
| **CONFLICT** | LLM 응답에서 추출 (`director_continuity.py:494,611,839` `result.get("decision")`) | 원고 이력 충돌 판정 | X — 연속성 전용 decision (※ :501,:616,:844는 비교문) |
| **WARNING** | `primitive_guard.py:147`, `director_continuity.py:724` | 비차단 경고 | X — advisory decision |
| **RETRY** | `story_expander.py:241` (SET), `stage01_helpers.py:446` (CHECK) | Stage 0 재시도 | X — Stage 0 전용 decision |
| **AGREE** | `director_ensemble.py:1641` | NCR 합의 응답 | X — NCR 전용 |
| **DISMISS** | `director_ensemble.py:1648` | NCR 기각 응답 | X — NCR 전용 |
| **UNKNOWN** | `quality_sidecar_bootstrap.py:192` | 판정 불능 폴백 | X — 사이드카 전용 |
| **FAIL** | f-string 보간 (`scoring_validator.py:165,978` `f"{'PASS' if passed else 'FAIL'}"`) | 로그 메시지 내 문자열 | X — verdict 변수 할당 아님, 표시용 문자열 |

### 1.4 전량 목록

**Core Verdict (9개 — 파이프라인 흐름 결정)**

| # | 값 | 출처 | 스키마 | 스코프 |
|---|---|------|--------|--------|
| 1 | PASS | LLM + Python | O | Director, ValidationOrch, 전역 |
| 2 | PASS_WITH_FIX | LLM + Python | O | Director — fix_scope 필수 |
| 3 | REJECT | LLM + Python | O | Director, ValidationOrch, 전역 |
| 4 | CONDITIONAL_PASS | Python only | X | ValidationOrchestrator 전용 |
| 5 | PASS_WITH_WARNING | Python only | X | Blueprint 생성 — quality_gate 연동 |
| 6 | FAILED | Python only | X | Arc/Blueprint 생성 — 재시도 소진 |
| 7 | ERROR | Python only | X | 스키마 호환/파싱 실패 |
| 8 | EMPTY | Python only | X | Stage 4 후보 부재 |
| 9 | SKIP | Python only | X | ContinuityInspector 보류 |

**Contextual Decision (7개 — 특정 서브시스템 전용, 파이프라인 verdict 아님)**

| # | 값 | 서브시스템 |
|---|---|----------|
| 10 | CONFLICT | director_continuity (연속성) |
| 11 | WARNING | primitive_guard / director_continuity |
| 12 | RETRY | Stage 0 (story_expander, stage01_helpers) |
| 13 | AGREE | director_ensemble NCR |
| 14 | DISMISS | director_ensemble NCR |
| 15 | UNKNOWN | quality_sidecar_bootstrap |
| 16 | FAIL | scoring_validator / block_enricher (검증 메시지) |

> **초판 오류 교정**: DEGRADED는 verdict가 아님 (코드에서 verdict로 사용된 적 없음). 삭제.
> **2차 교정에서 누락된 7개**: CONFLICT, WARNING, RETRY, AGREE, DISMISS, UNKNOWN, FAIL — 3차 전면 재조사에서 발견. 단, 이들은 Core Verdict가 아닌 Contextual Decision으로 분류.

---

## 2. 점수 → Verdict 변환 규칙

### 2.1 ValidationOrchestrator

```
score >= _UNCONDITIONAL_PASS_FLOOR (85)  → PASS
60 <= score < 85                          → CONDITIONAL_PASS
score < 60                                → REJECT
```

`_UNCONDITIONAL_PASS_FLOOR = 85` (`validation_orchestrator.py:174`)

### 2.2 장르별 pass_threshold (base_threshold)

| 장르 | 임계값 | 위치 |
|------|--------|------|
| wuxia | 70 | `validation_orchestrator.py:85` |
| hunter | 68 | L92 |
| investment | 72 | L99 |
| fantasy | 69 | L106 |
| composer | 71 | L113 |
| cooking | 70 | L120 |
| alt_history | 72 | L127 |
| actor | 70 | L134 |
| sports | 69 | L141 |
| medical | 73 | L148 |

### 2.3 Director Ensemble 투표

```python
pass_votes = count(decision == "PASS")
pwf_votes = count(decision == "PASS_WITH_FIX")

if pass_votes > len(evaluations) // 2:
    final_decision = "PASS_WITH_FIX" if pwf_votes > 0 else "PASS"
else:
    final_decision = "REJECT"
```

### 2.4 레거시 매핑 (director_auditor.py:334-335)

```python
if final_decision in ["PASS", "CONDITIONAL_PASS"]:
    legacy_result["decision"] = "PASS"  # CONDITIONAL_PASS → PASS 손실 변환
```

---

## 3. 부울 플래그 전수 목록 (초판 1개 → 교정 7개)

| 플래그 | 타입 | SET 위치 | Stage 4 영향 |
|--------|------|---------|-------------|
| **quality_risk** | bool | `director_ensemble.py:114,768`, `three_phase_blueprint_generator.py:447`, `stage3_orchestrator.py:1393` | `patch_threshold` 2→1 하향 |
| **quality_gate_failed** | bool | `stage3_orchestrator.py:2028` | 폴백 동작 활성화 |
| **force_reject** | bool | `director_ensemble.py:530` | REJECT 강제 |
| **force_pass_with_fix** | bool | `director_ensemble.py:534` | PASS_WITH_FIX 강제 |
| **asp_used** | bool | pipeline_result | 적응형 전략 사용 표시 |
| **patch_used** | bool | pipeline_result | 패치 모드 사용 표시 |
| **patch_fallback** | bool | pipeline_result | 패치 폴백 사용 표시 |

### 3.1 quality_risk 연동

| Verdict | quality_risk 가능? | Stage 4 동작 |
|---------|-------------------|-------------|
| PASS | O (validation 경고 시) | patch_threshold=1 |
| PASS_WITH_FIX | O (항상) | 패치 모드 + fix_scope |
| PASS_WITH_WARNING | O (항상) | patch_threshold=1 |
| CONDITIONAL_PASS | O | Advisory 주입 |
| REJECT | N/A | Stage 4 미진입 (재시도) |
| FAILED | N/A | Stage 4 미진입 |
| ERROR | N/A | Stage 4 미진입 |
| EMPTY | N/A | 재생성 |
| SKIP | N/A | 건너뜀 |

---

## 4. 불일치 지점 (교정판)

### 불일치 #1: PASS_WITH_WARNING — 스키마 미정의, 실제 SET됨

- `three_phase_blueprint_generator.py:745`에서 `pipeline_result["final_verdict"] = "PASS_WITH_WARNING"` SET
- `stage3_orchestrator.py:843,1474`에서 성공 조건으로 CHECK
- `failure_analyzer.py:1040,1270,1343,1410`에서 합격으로 집계
- **그러나** Director LLM 스키마에는 없음 → LLM이 반환하는 게 아니라 Python 후처리

### 불일치 #2: CONDITIONAL_PASS 손실 변환

- `validation_orchestrator.py`에서 생성 (60-84점)
- `director_auditor.py:334-335`에서 `CONDITIONAL_PASS → PASS` 변환
- Stage 4에 CONDITIONAL_PASS 정보가 전달되지 않음

### 불일치 #3: FAILED/ERROR — 내부 verdict인데 외부 노출

- `test_blueprint_patch_mode.py:156,193`에서 `final_verdict == "FAILED"` 검증
- `test_stage3_orchestrator.py:727`에서 `final_verdict == "ERROR"` 검증
- pipeline_result에 그대로 노출됨 → 다운스트림 소비자가 처리해야 함

---

## 5. 연관 필드 참조

### fix_scope (PASS_WITH_FIX 전용)

| 값 | 의미 | 위치 |
|----|------|------|
| `inplace` | 단일 위치 수정 | `response_schemas.py:135` |
| `partial` | 섹션 수정 | `response_schemas.py:136` |
| `full` | 전면 재작성 | `response_schemas.py:137` |

### severity

| 값 | 위치 |
|----|------|
| NONE, MINOR, MAJOR, CRITICAL | `response_schemas.py:217` |

### error_category

| 값 | 위치 |
|----|------|
| QUALITY_ISSUE, LOGIC_ERROR | `response_schemas.py:143` |

### 일관성 체크리스트 (20항목, `response_schemas.py:151-170`)

모든 항목 `["OK", "ISSUE"]` enum:
```
numeric_accuracy, arithmetic, title_consistency, scene_overlap,
percent_calculation, event_ordering, space_continuity, npc_identity,
time_progression, opening_diversity, timeline_arc_consistency,
fiction_term_leak, scene_variety, pacing_quality, dialogue_naturalness,
pov_discipline, emotional_authenticity, npc_knowledge_boundary,
secret_consistency, identity_consistency
```

---

## 6. 코드 착수 시 실행 계획 (교정판)

### Phase 1: Verdict 상수 중앙화 (3시간)
- `modules/core/verdict.py` 신규 — 9개 verdict 상수 + 7개 플래그 정의
- 문자열 리터럴 → 상수 참조로 교체 (grep 기반)
- PASS_WITH_WARNING을 스키마에 추가할지 여부 결정 필요

### Phase 2: 레거시 매핑 수정 (1시간)
- `director_auditor.py:334-335`: `CONDITIONAL_PASS → PASS` 제거 검토
- CONDITIONAL_PASS를 Stage 4까지 전달할지 결정 필요

### Phase 3: FAILED/ERROR 정규화 (2시간)
- pipeline_result 반환 전 정규화 게이트 추가
- 또는 다운스트림에서 명시적 처리

### Phase 4: 테스트 (2시간)
- 9개 verdict 각각에 대한 경로 테스트
- 7개 부울 플래그 조합 테스트
