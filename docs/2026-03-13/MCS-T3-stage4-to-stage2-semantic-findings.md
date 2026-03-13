# [MCS-T3] Stage4 -> Stage2 Semantic Preservation Findings

> 작성일: 2026-03-13
> 상태: `executed / PASS3 completed`
> 조사 모드: `static / read-only / code-and-test verification / UTF-8 only`
> 기준 오더: `docs/2026-03-13/main_a-cross-stage-semantic-preservation-detail-full-survey-audit-order.md`
> 최종 판정: `retained P1 1건, retained P2 1건, duplicate candidate 1건 제거, coverage gap 1건 분리`

이 문서는 `main_a.py`의 `Stage4 -> Stage2` semantic preservation 경계를 전용 조사한 결과다.
핵심 관심사는 `hard/normal gate` 존재 여부가 아니라, Stage 4가 이미 만들고 저장한 실패 의미가
Stage 2 retry planning에 같은 의미로 전달되는지 여부다.

---

## 조사 범위

- `main_a.py`
  - `_generate_reverse_feedback_stage4_to_2()`
  - `_enrich_director_result()`
- 직접 downstream
  - `modules/core/stage2_context.py`
  - `modules/core/stage2_preflight.py`
  - `modules/core/stage4_post_processor.py`
- 실제 handoff carrier / producer
  - `modules/core/feedback_system.py`
  - `modules/core/pass_rate_monitor.py`
  - `modules/core/stage4_interview_round.py`
  - `modules/core/db_manager.py`

## 필수 근거

- `tests/test_feedback_system.py`
- `tests/test_stage2_preflight_helpers.py`
- `tests/test_stage2_context.py`
- `tests/test_arc_difficulty.py`
- `tests/test_stage4_context.py`
- `tests/test_stage4_interview_round.py`
- `docs/2026-03-13/MRF-T4-cross-stage-reverse-feedback-findings.md`
- `docs/2026-03-13/stage4-director-cw-feedback-loop-full-survey-3pass-audit.md`

## 실행 확인

아래 테스트를 실제 실행했다.

- `pytest tests/test_feedback_system.py -q` -> `59 passed`
- `pytest tests/test_stage2_preflight_helpers.py -q` -> `44 passed`
- `pytest tests/test_arc_difficulty.py -q` -> `3 passed`
- `pytest tests/test_stage2_context.py -q` -> `16 passed`
- `pytest tests/test_stage4_context.py -q` -> `31 passed`
- `pytest tests/test_stage4_interview_round.py -q` -> `68 passed, 1 failed`

실패한 1건은 `tests/test_stage4_interview_round.py::TestModuleStructure::test_main_a_stage4_context_includes_pass_rate_monitor`다.
현재 런타임 배선은 `main_a.py` 인라인 문자열이 아니라 `Stage4Context.from_app()` 경유로 존재하므로,
이 테스트는 semantic corruption 증거라기보다 proof quality drift 신호로 분리했다.

---

## PASS 1 - 후보 수집

초기 후보는 4건이었다.

1. Stage 4가 이미 저장하는 구조화 reject 의미가 `PassRateMonitor` carrier로 바뀌는 순간 거의 전부 사라질 가능성
2. `Stage4 -> 2` helper가 `hard`가 아니면 빈 문자열을 반환해, semantic issue가 있어도 Stage 2에서 완전히 bypass될 가능성
3. `_enrich_director_result()` dead helper 때문에 semantic-rich payload가 live chain에 연결되지 않을 가능성
4. 관련 테스트가 injection/gating만 검증하고 semantic preservation은 증명하지 못할 가능성

## PASS 2 - 교차 검증

PASS 2에서 아래 1건은 제거했다.

- `duplicate candidate`
  - 내용: `_enrich_director_result()` dead helper
  - 판정: `already-covered-do-not-reopen`
  - 근거: `docs/2026-03-13/MRF-T4-cross-stage-reverse-feedback-findings.md`의 `[MRF-T4-003]`이 이미 같은 helper dead-surface 문제를 다룬다.

또 아래 1건은 finding이 아니라 `coverage gap`으로 내렸다.

- 내용: 관련 테스트 proof quality가 semantic-preservation까지 닿지 못함
- 판정: `coverage gap`
- 이유: 현재 증거는 실제 blind spot을 강화하지만, 그 자체만으로 semantic corruption 현상을 직접 만들지는 않는다.

나머지 2건은 `Stage4 -> Stage2 live handoff contract` 책임 경계에서 신규 `MCS-T3` finding으로 유지 가능하다고 판단했다.

---

## PASS 3 - 확정 Findings

### [MCS-T3-001]

1. ID
   - `[MCS-T3-001]`
2. Severity
   - `P1`
3. 현상 요약
   - 현재 live `Stage4 -> Stage2` bridge는 Stage 4 reject의 의미를 전달하지 않고, 거의 전적으로 `집필 난이도 비용`만 전달한다.
   - Stage 4는 runtime 중 이미 `error_category`, `action_items`, `score_breakdown`, `open_review`, `selection_reason`을 여러 sink에 저장한다.
   - 그러나 Stage 2가 실제 읽는 carrier는 `PassRateMonitor.get_arc_difficulty()`가 만든 `difficulty / avg_attempts / hard_episodes`뿐이다.
   - 결과적으로 같은 실패 원인이 다음 stage에서 같은 의미로 내려가는 것이 아니라, `generic simplification advice`로 semantic rewrite 된다.
   - 분류상 이는 `semantic-rewrite`다.
4. 코드 근거
   - `modules/core/stage4_interview_round.py:3124-3145`는 REJECT `previous_attempt`에 `action_items`, `score_breakdown`, `selection_reason`, `open_review`, `error_category`, `contradiction_types`를 보존한다.
   - `modules/core/stage4_interview_round.py:4364-4370`는 episode log payload에 `error_category`, `action_items`, `score_breakdown`, `open_review`를 남긴다.
   - `modules/core/stage4_post_processor.py:306-347`는 `final_state_updates["_director_quality_labels"]`를 꺼내 `save_episode_quality_label()`로 저장한다.
   - `modules/core/db_manager.py:2700-2717`는 `episode_quality_labels`에 `selection_reason`, `open_review`, `score_breakdown`을 저장한다.
   - 반면 `modules/core/pass_rate_monitor.py:33-49`의 `AttemptRecord`에는 위 semantic fields가 없다.
   - `modules/core/pass_rate_monitor.py:129-180`의 `record_attempt()`도 `reject_reason` 문자열과 patch 메타 정도만 저장한다.
   - `modules/core/pass_rate_monitor.py:478-533`의 `get_arc_difficulty()`는 기록 중 시도 횟수만 모아 `difficulty`, `avg_attempts`, `hard_episodes`만 반환한다.
   - `main_a.py:762-764`와 `modules/core/feedback_system.py:667-682`의 `Stage4->2` helper 시그니처도 `arc_difficulty`만 받는다.
   - `modules/core/stage2_preflight.py:922-944`는 실제로 그 `prev_difficulty` dict만 Stage 2 feedback source로 사용한다.
5. downstream 영향 경계
   - Stage 4가 `LOGIC_ERROR`, `quality issue`, `continuity conflict`, 저점 `score_breakdown`, 자유 리뷰를 구분해도,
     Stage 2는 다음 Arc 설계 시 결국 `씬 구조를 단순화하라`는 generic guidance만 받는다.
   - 즉 Stage 2가 이어받는 것은 `same failure meaning`이 아니라 `same retry cost`다.
   - 영향 범위는 `Stage4 manuscript reject/post-processing -> Stage2 next-arc retry planning` 경계다.
6. 현재 테스트 근거 또는 테스트 부재
   - 존재하는 테스트:
     - `tests/test_stage4_interview_round.py:1557-1619`는 `selection_reason`, `open_review`, `fix_scope_reasoning`이 DB sink로 저장됨을 확인한다.
     - `tests/test_stage4_interview_round.py:1711-1782`는 episode log payload에 `selection_reason`, `verdict_reason`, `score_breakdown`, `open_review`, `reject_bucket`가 남는 것을 확인한다.
     - `tests/test_arc_difficulty.py:7-43`는 `get_arc_difficulty()`가 시도 횟수 평균과 hard episode 목록만으로 난이도를 계산함을 확인한다.
   - 부재:
     - `error_category`, `action_items`, `score_breakdown`, `open_review` 중 어느 것도 Stage 2 injected feedback에 반영되는지 검증하는 통합 테스트가 없다.
     - Stage 4에서 저장된 richer sink(`episode_quality_labels`, episode log, stage_attempts`)를 Stage 2가 읽는 테스트도 없다.
7. 기존 문서와의 중복 여부
   - `related-but-new-cross-stage-semantic-surface`
   - 기존 `MRF-T4-003`은 dead helper와 callback surface를 다뤘다.
   - 이번 항목은 `Stage4 post-processing / persistence가 richer payload를 이미 만들고도 live Stage4->2 carrier가 difficulty-only라 semantic rewrite가 구조적으로 고정된다`는 별도 handoff 계약 문제다.
8. 권장 후속 조치
   - `PassRateMonitor` 기반 difficulty summary를 버리라는 뜻은 아니다.
   - 다만 `difficulty`는 intensity modifier로만 쓰고, 별도 semantic payload를 함께 넘겨야 한다.
   - 최소한 `error_category`, `reject_bucket`, 축약 `score_breakdown`, `open_review` 요약을 담는 `stage4_to_stage2_feedback_payload`가 필요하다.
   - 대안으로는 `Stage2`가 `episode_quality_labels` 또는 `stage_attempts`에서 최근 Stage 4 reject semantics를 읽도록 계약을 바꿀 수 있다.

### [MCS-T3-002]

1. ID
   - `[MCS-T3-002]`
2. Severity
   - `P2`
3. 현상 요약
   - 현재 live `Stage4 -> Stage2` 경로는 semantic payload가 빈약한 데서 끝나지 않고, `difficulty == hard`가 아니면 아예 아무 피드백도 주지 않는다.
   - `avg_attempts <= 3.0`인 Arc는 `normal`로 분류되고, helper는 빈 문자열을 반환한다.
   - 따라서 Stage 4에서 의미 있는 reject semantics가 반복돼도, retry cost가 hard 임계치에 못 미치면 Stage 2는 그 사실을 전혀 모른 채 넘어간다.
   - 분류상 이는 `semantic-bypass`다.
4. 코드 근거
   - `modules/core/pass_rate_monitor.py:512-526`은 `avg_attempts <= 1.5`면 `easy`, `<= 3.0`이면 `normal`, 그 외만 `hard`로 분류한다.
   - `modules/core/feedback_system.py:667-670`은 `difficulty != "hard"`면 즉시 빈 문자열을 반환한다.
   - `modules/core/stage2_preflight.py:930-944`는 helper 결과가 비어 있지 않을 때만 warning injection과 `s4_to_s2_feedback` audit event를 남긴다.
   - 결과적으로 `normal`이나 `unknown`은 semantic issue가 있어도 Stage 2 consumer에서 관측 불가 상태가 된다.
5. downstream 영향 경계
   - 예를 들어 같은 Arc가 `2~3회` 재시도를 거치며 지속적으로 continuity, structure, or open-review 문제를 냈더라도,
     평균 시도 횟수가 hard 경계 아래면 다음 Arc 설계는 아무 Stage4 교훈도 받지 않는다.
   - 이는 `semantic preservation 실패`이면서 동시에 `difficulty gate가 feedback existence gate`로 잘못 쓰이는 문제다.
   - 영향 범위는 `moderate but repeated Stage4 reject history -> Stage2 next-arc planning` 경계다.
6. 현재 테스트 근거 또는 테스트 부재
   - 존재하는 테스트:
     - `tests/test_feedback_system.py:464-477`은 `hard`일 때만 문구가 나오고 `normal`이면 빈 문자열이 반환됨을 확인한다.
     - `tests/test_stage2_preflight_helpers.py:1011-1045`는 hard일 때 audit event가 찍히고, empty feedback면 주입이 없음을 확인한다.
   - 부재:
     - `normal difficulty + semantically consistent reject history`에서 fallback semantic guidance가 존재하는지 확인하는 테스트가 없다.
     - `hard/normal`과 별개로 `error_category` 또는 `reject_bucket`만으로 보조 guidance를 주는 테스트도 없다.
7. 기존 문서와의 중복 여부
   - `related-but-new-cross-stage-semantic-surface`
   - 기존 문서는 Stage4->2가 difficulty-only라는 점을 다뤘지만,
     이번 항목은 그 위에 `hard-only cutoff`가 실제로 semantic signal 존재 자체를 binary gate로 바꾼다는 점을 별도 확인한 것이다.
8. 권장 후속 조치
   - `difficulty`는 피드백 강도 조절에만 쓰고, 존재 여부를 결정하는 gate로 쓰지 않는 편이 낫다.
   - 최소한 `normal`이어도 `recent error_category`, `recent reject_bucket`, `recent open_review summary` 중 하나가 있으면 축약 advisory를 주입해야 한다.
   - `normal difficulty but repeated semantic issue` 회귀 테스트를 추가해 `empty string`이 기본값이 아닌지 검증해야 한다.

---

## Rejected / Removed Candidates

### RC-1. `_enrich_director_result()` dead helper가 곧바로 T3 신규 finding이다

- 판정: `already-covered-do-not-reopen`
- 이유:
  - `docs/2026-03-13/MRF-T4-cross-stage-reverse-feedback-findings.md`의 `[MRF-T4-003]`이 이미 같은 문제를 다뤘다.
  - 이번 문서는 helper 존재 여부보다 `Stage4 -> Stage2 live carrier contract`를 본다.

---

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| `Stage4->2` semantic preservation | helper hard/normal gate와 injection 여부만 검증 | semantic field 보존을 보는 end-to-end 통합 테스트 |
| richer sink 활용 여부 | `episode_quality_labels`, episode log, `stage_attempts`는 richer payload 저장 | Stage 2가 실제로 이 sink들을 참조하는지 또는 의도적으로 무시하는지 SSOT 문서화 |
| Stage4 wiring proof quality | `tests/test_stage4_interview_round.py -q`에서 source-string assertion 1건 실패 | `main_a.py` 문자열 대신 `Stage4Context.from_app()` runtime wiring을 검증하는 테스트로 교체 |

---

## PASS 요약

- PASS1 후보: `4`
- PASS2 제거: `1`
- PASS2 coverage gap 분리: `1`
- PASS3 확정: `2`

정리하면 이번 T3 범위의 핵심 문제는 단순히 `피드백이 약하다`가 아니다.

- `Stage4`는 이미 richer reject semantics를 만든다.
- 하지만 `Stage2`로 가는 live carrier는 그 의미를 거의 전부 버리고 `difficulty`로 축약한다.
- 그리고 그마저도 `hard`가 아니면 아예 사라진다.

즉 현재 `Stage4 -> Stage2` handoff는 `semantic-loss`를 넘어,
`semantic-rewrite`와 `semantic-bypass`가 함께 존재하는 상태로 판정한다.

## 마감 체크

- 코드 근거 포함
- downstream 영향 경계 포함
- 현재 테스트 근거 또는 테스트 부재 포함
- 기존 문서와의 중복 여부 포함
- `PASS1 -> PASS2 -> PASS3` 요약 포함
