# MCS-T2 Stage3->Stage2 Semantic Findings

> 작성일: 2026-03-13
> 범위: `main_a.py` / `modules/core/stage2_context.py` / `modules/core/stage2_preflight.py` / `modules/core/stage2_orchestrator.py`
> 상태: `PASS3 confirmed`
> 실행 모드: `static`, `read-only`, `code-and-test verification`

---

## 요약

| ID | Sev | 상태 | 파일 / 함수 | 요약 |
|----|-----|------|-------------|------|
| `MCS-T2-001` | `P1` | confirmed | `modules/core/stage2_preflight.py`, `modules/core/stage2_finalizer.py`, `modules/core/stage3_orchestrator.py` | `Stage3->2` reverse feedback consumer는 `stage==3` 이력을 요구하지만 live runtime에는 그 producer가 없어 semantic handoff가 사실상 우회된다 |
| `MCS-T2-002` | `P1` | confirmed | `modules/core/stage3_orchestrator.py`, `modules/core/feedback_system.py`, `modules/core/stage2_preflight.py` | Stage3 reject가 가진 `failure_category`, `verdict_reason`, `fix_scope`, `contradictions`류 의미가 Stage2 경계에서 reason-count 문자열과 고정 조언으로 납작해진다 |
| `MCS-T2-003` | `P2` | confirmed | `main_a.py`, `modules/core/feedback_system.py`, `modules/core/stage2_orchestrator.py`, `modules/core/stage2_preflight.py` | Stage2 self-retry 분석과 `Stage3->2` reverse feedback가 서로 다른 분류 체계를 써 같은 실패 의미를 다른 guidance semantics로 번역한다 |

---

## 조사 범위

- `main_a.py`
  - `_generate_reverse_feedback_stage3_to_2()`
  - `_analyze_rejection_pattern_v60()`
  - `_normalize_rejection_reason()`
  - `_get_rejection_fix_guide()`
- `modules/core/stage2_context.py`
- `modules/core/stage2_preflight.py`
- `modules/core/stage2_orchestrator.py`
- `tests/test_stage2_preflight.py`
- `tests/test_stage2_preflight_helpers.py`
- `tests/test_feedback_system.py`
- `tests/e2e/test_l3_stage2_realproject.py`
- `tests/e2e/test_l3_golden_route.py`
- 중복 대조:
  - `docs/2026-03-13/MRF-T1-stage2-callback-binding-findings.md`
  - `docs/2026-03-13/MRF-T2-rejection-analysis-intensity-findings.md`
  - `docs/2026-03-13/MRF-T4-cross-stage-reverse-feedback-findings.md`
  - `docs/2026-03-13/MRF-T5-consumer-tests-regression-findings.md`

---

## 검증 메모

- 실행:
  - `pytest tests/test_feedback_system.py tests/test_stage2_context.py tests/test_stage2_preflight.py tests/test_stage2_preflight_helpers.py -q`
- 결과:
  - `144 passed in 3.62s`

---

## PASS 1 후보

- 후보 A: `Stage3->2` reverse feedback callback optionality가 semantic gap을 만든다
- 후보 B: `analyze_rejection_pattern_v60` optional binding과 hard-call이 충돌한다
- 후보 C: `Stage3->2` reverse feedback는 `stage==3` reject producer가 없어 live path에서 사실상 비활성이다
- 후보 D: live path가 존재하더라도 Stage3 reject 의미가 Stage2 경계에서 구조화 의미를 잃는다
- 후보 E: `Stage3->2` reverse feedback와 Stage2 self-retry triage가 서로 다른 분류 체계를 사용한다
- 후보 F: 테스트 스위트가 `Stage3 REJECT -> Stage2 retry planning` semantic contract를 잠그지 않는다

---

## PASS 2 제거

### 제거 1. callback optionality silent drop

- 제거 사유:
  - `docs/2026-03-13/MRF-T4-cross-stage-reverse-feedback-findings.md`의 `MRF-T4-002`가 이미 `generate_reverse_feedback_stage3_to_2`의 optional callback + broad except silent drop surface를 닫고 있다.
- 판정:
  - `already-covered-do-not-reopen`

### 제거 2. `analyze_rejection_pattern_v60` hard-call

- 제거 사유:
  - `docs/2026-03-13/MRF-T1-stage2-callback-binding-findings.md`의 `MRF-T1-001`이 이미 optional binding 대비 consumer hard-call 문제를 확정했다.
- 판정:
  - `already-covered-do-not-reopen`

### 제거 3. 테스트 blind spot 일반론

- 제거 사유:
  - `docs/2026-03-13/MRF-T5-consumer-tests-regression-findings.md`가 helper direct test 부재와 e2e lambda 대체 패턴을 이미 일반론으로 정리했다.
  - 다만 이번 트랙에서는 해당 blind spot을 각 finding의 테스트 근거에만 종속 증거로 사용한다.
- 판정:
  - `already-covered-do-not-reopen`

---

## PASS 3 확정 Findings

### [MCS-T2-001] P1 - `Stage3->2` reverse feedback는 live producer 부재로 semantic handoff가 우회된다

1. ID
   - `MCS-T2-001`
2. Severity
   - `P1`
3. 현상 요약
   - `modules/core/stage2_preflight.py`는 `stage_rejection_history`에서 `stage == 3`인 항목이 Arc당 3회 이상 누적되면 `Stage3->2` reverse feedback를 주입한다.
   - 그러나 repo 전체 검색 기준 `stage_rejection_history.append(...)`의 유일한 live writer는 `modules/core/stage2_finalizer.py`이며, 여기서 기록되는 값은 항상 `"stage": 2`다.
   - Stage3 reject path는 같은 실패를 `pass_rate_monitor`와 DB `stage_attempts/director_selections`로만 남기고 `stage_rejection_history`에는 넣지 않는다.
   - 결과적으로 현재 runtime에서는 Stage3 실패 의미가 Stage2 retry planning으로 내려가지 못하고, reverse feedback branch는 수동 주입 없이는 사실상 dead surface다.
4. 코드 근거
   - `main_a.py:263`은 공유 컨테이너로 `self.stage_rejection_history = []`를 초기화한다.
   - `modules/core/stage2_preflight.py:897-904`는 `stage_rejection_history` 중 `r.get("stage") == 3`만 모아 `generate_reverse_feedback_stage3_to_2(...)`에 전달한다.
   - `modules/core/stage2_finalizer.py:1690-1697`은 reject history에 append하는 유일한 live writer인데 `"stage": 2`, `reason`, `attempt`만 기록한다.
   - `modules/core/stage3_orchestrator.py:1850-1919`의 Stage3 reject path는 `_failure_category` 계산 후 `pass_rate_monitor.record_attempt(...)`, `save_stage_attempt(...)`, `save_director_selection(...)`에는 기록하지만 `stage_rejection_history` write는 없다.
5. downstream 영향 경계
   - 영향 경계는 `Stage3 Blueprint REJECT 누적 -> Stage2 arc 재설계 preflight` handoff다.
   - Stage2는 원래 받아야 할 "이 Arc는 Blueprint 단계에서 구조적으로 반복 실패 중"이라는 경고를 받지 못한 채 동일 Arc를 재생성한다.
   - 즉 callback optionality 이전에, live producer 자체가 없어 semantic-preservation contract가 bypass된다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_feedback_system.py:431-456`은 helper 단독 동작만 검증하고 live producer/consumer alignment는 검증하지 않는다.
   - `tests/test_stage2_preflight.py:64-65`는 fixture에서 `stage_rejection_history=[]`, `generate_reverse_feedback_stage3_to_2=MagicMock(...)`로 시작해 Stage3 reject 누적 data를 만들지 않는다.
   - `tests/e2e/test_l3_stage2_realproject.py:212-227`, `tests/e2e/test_l3_golden_route.py:236-251`은 `stage_rejection_history=[]`와 empty lambda를 주입해 live contract를 우회한다.
   - 이번 조사에서 관련 pytest 144건은 모두 통과했지만, 그 사실은 오히려 현재 스위트가 Stage3 producer 부재를 놓치고 있음을 보여준다.
7. 기존 문서와의 중복 여부
   - `related-but-new-cross-stage-semantic-surface`
   - 기존 문서는 callback missing branch와 consumer hard-call을 다뤘지만, `stage==3` reject producer 부재로 handoff 자체가 비활성이라는 surface는 별도 확정되어 있지 않았다.
8. 권장 후속 조치
   - Stage3 REJECT path가 `stage_rejection_history`에 최소 `stage=3`, `arc_no`, `reason` 이상을 일관되게 기록하게 하거나, Stage2 preflight가 별도 Stage3 reject ledger를 참조하도록 계약을 재설계한다.
   - 회귀 테스트를 추가한다:
     - `Stage3 REJECT x3 -> Stage2 preflight warning injection`
     - `from_app()` real binding 기준 Stage3 reject history producer/consumer alignment`

### [MCS-T2-002] P1 - Stage3 reject의 구조화 의미가 Stage2 경계에서 reason-count 문자열로 붕괴한다

1. ID
   - `MCS-T2-002`
2. Severity
   - `P1`
3. 현상 요약
   - Stage3 reject path는 단순 사유 문자열보다 풍부한 의미를 계산한다. 예를 들어 `failure_category`, `validate_verdict`, `issues_count`, `comparison_notes`, `contradictions`, `selection_reason`, `verdict_reason`, `fix_scope`, `fix_scope_reasoning`이 개별 sink로 남는다.
   - 반면 `Stage3->2` reverse feedback helper는 실패 목록에서 `reason`만 세고, Arc 공통 3개 조언을 덧붙인 문자열만 반환한다.
   - Stage2 consumer도 그 문자열을 `[Blueprint 실패 패턴 분석]` 블록으로 prepend할 뿐 구조화 필드로 해석하지 않는다.
   - 따라서 Stage3가 이미 알고 있는 "무슨 종류의 실패인지", "어디를 고쳐야 하는지", "검증/생성/품질 중 어느 경계에서 깨졌는지"가 Stage2 retry planning 경계에서 보존되지 않는다.
4. 코드 근거
   - `modules/core/stage3_orchestrator.py:71-89`는 `_classify_stage3_failure_category()`에서 `generation_error`, `quality_gate`, `validation_contradiction`, `validation_issue`, `continuity`, `reject` 등을 구분한다.
   - `modules/core/stage3_orchestrator.py:1592-1634`는 `_build_stage3_reject_reason()`에서 `error`, `score`, `quality_gate_failed`, `strategy`, `validate_verdict`, `issues`, `notes`, `contradictions`를 조합한다.
   - `modules/core/stage3_orchestrator.py:1680-1730`는 `selection_reason`, `verdict_reason`, `fix_scope`, `fix_scope_reasoning`을 director selection payload에 싣는다.
   - `modules/core/stage3_orchestrator.py:1850-1919`는 reject 시 `failure_category`를 DB에 저장하고 director selection payload도 남긴다.
   - 대조적으로 `modules/core/feedback_system.py:626-657`의 `generate_reverse_feedback_stage3_to_2()`는 `failure.get("reason")` count와 고정된 3개 Arc 수정 권장 사항만 출력한다.
   - `modules/core/stage2_preflight.py:904-912`는 그 반환값을 단순 텍스트 블록으로 `enhanced_context` 앞에 붙인다.
5. downstream 영향 경계
   - 영향 경계는 `Stage3 reject semantic payload -> Stage2 retry prompt planning`이다.
   - Stage2는 `validation_contradiction`과 `generation_error`를 구분하지 못하고, `fix_scope`나 `contradictions`에 따라 수정 범위를 달리 잡을 수도 없다.
   - 결과적으로 다음 retry는 실제 실패 책임 경계를 재현하지 못한 generic Arc 조언으로 유도될 수 있다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_feedback_system.py:443-456`은 3회 이상 실패 시 문자열이 생기고 reason substring이 남는지만 본다. 구조화 semantic field 보존은 고정하지 않는다.
   - `tests/test_stage2_preflight.py:64-65`는 reverse feedback callback 결과를 `"reverse"`로 단순 mock 처리한다.
   - `tests/e2e/test_l3_stage2_realproject.py:221-227`, `tests/e2e/test_l3_golden_route.py:245-251`은 helper를 empty lambda로 대체한다.
   - 따라서 현재 테스트는 `failure_category`, `fix_scope`, `contradictions`, `selection_reason` 등이 Stage2 경계에서 어떻게 다뤄지는지 전혀 잠그지 않는다.
7. 기존 문서와의 중복 여부
   - `related-but-new-cross-stage-semantic-surface`
   - 기존 retry-feedback 문서는 callback drift와 Stage2 내부 normalization bucket을 다뤘지만, Stage3의 구조화 reject payload가 Stage2 경계에서 reason-count text로 붕괴하는 handoff contract는 별도로 닫히지 않았다.
8. 권장 후속 조치
   - `Stage3->2` contract를 문자열이 아니라 구조화 payload로 승격한다.
   - 최소 필드 후보:
     - `failure_category`
     - `verdict_reason`
     - `selection_reason`
     - `fix_scope`
     - `contradictions`
     - `issues_count`
   - 회귀 테스트를 추가한다:
     - `Stage3 reject structured payload -> Stage2 preflight prompt block`
     - `validation_contradiction`와 `generation_error`가 서로 다른 retry guidance로 이어지는지 검증`

### [MCS-T2-003] P2 - `Stage3->2` reverse feedback와 Stage2 self-retry triage가 다른 taxonomy를 써 같은 실패 의미를 다르게 번역한다

1. ID
   - `MCS-T2-003`
2. Severity
   - `P2`
3. 현상 요약
   - Stage2 자기 자신의 REJECT history는 `_analyze_rejection_pattern_v60()`로 들어가며 `_normalize_rejection_reason()`와 `_get_rejection_fix_guide()`를 통해 continuity/length/json류 버킷과 대응 수정 가이드를 얻는다.
   - 반면 `Stage3->2` reverse feedback는 별도 helper를 타며 reason normalization을 전혀 거치지 않고 raw reason count와 고정 Arc 조언만 생성한다.
   - 즉 동일하거나 유사한 실패 의미라도 Stage2 self-history로 들어오면 category-specific guidance가 붙고, Stage3 upstream failure로 들어오면 generic Arc 조언으로 바뀐다.
   - 이는 같은 실패 원인이 handoff 경로에 따라 다른 의미로 재번역되는 taxonomy drift다.
4. 코드 근거
   - `main_a.py:774-833`의 `_analyze_rejection_pattern_v60()`는 reject history를 정규화하고 top reason별 guide를 붙인다.
   - `main_a.py:836-875`의 `_normalize_rejection_reason()` / `_get_rejection_fix_guide()`는 `중복`, `수여`, `부상`, `위치`, `소지`, `내공`, `JSON`, `길이`, `범위` 버킷을 기준으로 수정 가이드를 제공한다.
   - `modules/core/stage2_orchestrator.py:488-497`은 Stage2 reject history가 있으면 그 normalized pattern analysis를 `current_feedback` 앞에 prepend한다.
   - 대조적으로 `modules/core/feedback_system.py:626-657`의 `generate_reverse_feedback_stage3_to_2()`는 reason normalization을 호출하지 않고, 모든 경우에 동일한 3개 Arc 수정 권장 사항을 덧붙인다.
   - `modules/core/stage2_preflight.py:904-912`는 이 generic reverse feedback를 별도의 warning 블록으로 주입한다.
5. downstream 영향 경계
   - 영향 경계는 `upstream Stage3 failure meaning`과 `local Stage2 repeated reject meaning`이 한 Stage2 retry prompt 안에서 만나는 지점이다.
   - 같은 continuity류 문제라도 Stage2 self-history는 세부 guide를 주고, Stage3 upstream failure는 일반적 Arc 재검토 조언으로 끝나므로 prompt 내부 guidance semantics가 일관되지 않다.
   - hard failure는 아니지만, retry planning에서 어떤 피드백을 우선 신뢰해야 하는지 애매하게 만들어 semantic drift를 키운다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_feedback_system.py:431-456`은 `Stage3->2` helper 단독 출력 존재만 확인한다.
   - `tests/test_stage2_preflight_helpers.py:224-238`은 Stage2 reject history shape만 고정하고, Stage3 reverse feedback와의 taxonomy alignment는 검증하지 않는다.
   - `tests/test_stage2_preflight.py`, `tests/e2e/test_l3_stage2_realproject.py`, `tests/e2e/test_l3_golden_route.py` 어디에서도 두 guidance path를 같은 fixture reason으로 비교하는 테스트가 없다.
7. 기존 문서와의 중복 여부
   - `related-but-new-cross-stage-semantic-surface`
   - `MRF-T2-02`는 Stage2 내부 normalization bucket coverage를 다뤘지만, 이번 항목처럼 `Stage3->2` reverse feedback taxonomy와의 불일치는 cross-stage semantic contract 문제로 별도다.
8. 권장 후속 조치
   - `Stage3->2` reverse feedback도 Stage2 self-retry triage와 같은 normalization/guide taxonomy를 공유하게 만든다.
   - 한 fixture reason set을 기준으로 두 경로의 output이 최소한 같은 category와 같은 수정 방향을 내는지 golden test를 추가한다.

---

## Coverage Gaps / Open Questions

- live `Stage3 REJECT -> Stage2 preflight` 통합 테스트가 없다.
  - 현재 e2e는 `generate_reverse_feedback_stage3_to_2=lambda ""`, `analyze_rejection_pattern_v60=lambda ""`로 semantic contract를 우회한다.
- Stage3 reject producer가 어떤 storage를 SSOT로 삼아야 하는지 결정이 없다.
  - `stage_rejection_history`를 확장할지, `pass_rate_monitor`나 DB를 Stage2 consumer가 직접 읽을지 계약이 명시돼 있지 않다.
- Stage3 구조화 reject payload 중 어느 필드를 Stage2 retry planning이 반드시 보존해야 하는지 SSOT schema가 없다.

---

## PASS 1 -> PASS 2 -> PASS 3 요약

- PASS1 후보: `6건`
  - callback optionality silent drop
  - optional callback hard-call
  - live producer 부재
  - structured semantic payload 붕괴
  - taxonomy drift
  - test blind spot
- PASS2 제거: `3건`
  - `callback optionality silent drop`
  - `optional callback hard-call`
  - `test blind spot 일반론`
- PASS3 확정: `3건`
  - `MCS-T2-001` semantic-bypass
  - `MCS-T2-002` semantic-loss
  - `MCS-T2-003` semantic-rewrite

