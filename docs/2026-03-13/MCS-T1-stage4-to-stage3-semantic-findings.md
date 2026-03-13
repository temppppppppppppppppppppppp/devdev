# [MCS-T1] Stage4 -> Stage3 Semantic Findings

> 작성일: 2026-03-13
> 상태: `executed / PASS3 finalized`
> 조사 모드: `static / read-only / code-and-test verification / UTF-8 only`
> 기준 오더: `docs/2026-03-13/main_a-cross-stage-semantic-preservation-detail-full-survey-audit-order.md`
> 최종 판정: `retained P1 2건, retained P2 1건, duplicate 1건 제거`

이 문서는 `Stage4 -> Stage3` handoff가 동일한 실패 의미, 동일한 narrative 경계, 동일한 수정 책임을 실제 runtime에서 보존하는지 조사한 PASS3 결과다.
코드 직접 수정은 수행하지 않았다.

---

## 조사 범위

- `main_a.py`
  - `_enrich_director_result()`
  - `_generate_reverse_feedback_stage4_to_3()`
- 직접 runtime 경계
  - `modules/core/stage4_interview_round.py`
  - `modules/core/stage4_orchestrator.py`
  - `modules/core/stage3_context.py`
  - `modules/core/stage3_orchestrator.py`
  - `modules/domain/agents/three_phase_blueprint_generator.py`
- 저장 경계
  - `modules/core/db_manager.py`
- 테스트 / 기존 문서
  - `tests/test_feedback_system.py`
  - `tests/test_v75b_escalation.py`
  - `tests/test_stage3_orchestrator.py`
  - `tests/test_stage4_interview_round.py`
  - `tests/test_director_feedback_loop.py`
  - `docs/2026-03-13/MRF-T4-cross-stage-reverse-feedback-findings.md`
  - `docs/2026-03-13/stage4-director-cw-feedback-loop-full-survey-3pass-audit.md`

---

## 실행 확인

실제 실행한 테스트:

- `pytest tests/test_director_feedback_loop.py tests/test_stage3_orchestrator.py tests/test_db_manager.py -q`
  - 결과: `87 passed`
- `pytest tests/test_feedback_system.py tests/test_v75b_escalation.py tests/test_stage4_interview_round.py -q`
  - 결과: `139 passed, 1 failed`
  - 단일 실패:
    - `tests/test_stage4_interview_round.py::TestModuleStructure::test_main_a_stage4_context_includes_pass_rate_monitor`
  - 판정:
    - `main_a.py`의 문자열 형태를 직접 기대하는 구조 테스트이며,
      이번 `Stage4 -> Stage3 semantic preservation` finding 채택 근거로는 사용하지 않았다.

---

## PASS 1 - 후보 수집

초기 후보는 4건이었다.

1. `main_a.py`의 `_generate_reverse_feedback_stage4_to_3()` helper가 실제 Stage 3 runtime consumer에 연결되지 않았을 가능성
2. `Stage4`의 full blueprint regeneration 경로가 Stage 3 semantic contract 자체를 우회할 가능성
3. `Stage4`의 inplace blueprint patch 경로가 structured reject semantics를 단일 문자열로 축소할 가능성
4. `_enrich_director_result()`가 dead surface일 뿐 아니라 live consumer 계약과도 맞지 않을 가능성

---

## PASS 2 - 교차 검증

PASS 2에서 아래 1건은 제거했다.

- `duplicate candidate`
  - 내용: `_generate_reverse_feedback_stage4_to_3()` helper가 실제 Stage 3 consumer에 연결되지 않음
  - 판정: `already-covered-do-not-reopen`
  - 근거:
    - `docs/2026-03-13/MRF-T4-cross-stage-reverse-feedback-findings.md`의 `[MRF-T4-001]`이 이미 동일 사실을 확정했다.
  - 이번 T1 문서에서는 그보다 더 runtime 가까운 문제인
    - `full regeneration semantic bypass`
    - `inplace patch semantic rewrite`
    - `dead enrich surface의 contract drift`
    만 유지했다.

나머지 3건은 `Stage4 -> Stage3 semantic preservation` 범위의 신규 retained finding으로 유지 가능하다고 판단했다.

---

## PASS 3 - 확정 Findings

### [MCS-T1-001]

1. ID
   - `[MCS-T1-001]`
2. Severity
   - `P1`
3. 현상 요약
   - `Stage4`의 logic-error escalation 중 `V75-B full regeneration` 경로는 실제로 `Stage3 consumer`를 통과하지 않는다.
   - `Stage4Orchestrator._regenerate_blueprint()`는 `Stage3Context`나 `Stage3Orchestrator`를 거치지 않고 `three_phase_blueprint_generator.generate()`를 직접 호출한다.
   - 더 중요한 점은, generator가 `external_feedback` 인자를 지원함에도 `Stage4` reject semantics를 그 인자로 넘기지 않는다.
   - 결과적으로 `Stage4 -> Stage3` handoff는 full regeneration 시점에서 semantic-preserving translation이 아니라 semantic bypass가 된다.
4. 코드 근거
   - `modules/core/stage4_orchestrator.py:1162-1172`는 `LOGIC_ERROR` 연속 시 `_regenerate_blueprint(next_ep, round_ctx.arc_data, round_ctx)`를 호출한다.
   - `modules/core/stage4_orchestrator.py:1267-1314`의 `_regenerate_blueprint()`는 `bp_agent.generate(...)`를 직접 호출하고 `save_episode_blueprint()`만 수행한다.
   - 같은 함수는 `external_feedback`, `selection_reason`, `verdict_reason`, `open_review`, `fix_scope_reasoning`, `error_category` 중 아무 것도 넘기지 않는다.
   - `modules/domain/agents/three_phase_blueprint_generator.py:58-73`은 `generate(..., external_feedback: str = "", semantic_context: str = "", ...)` 시그니처를 가진다.
   - `modules/domain/agents/three_phase_blueprint_generator.py:137-141`은 `external_feedback`가 오면 `[Director 외부 피드백 - 반드시 반영]` 블록으로 실제 prompt에 주입한다.
   - 대조적으로 정상 `Stage3` 경로는 `modules/core/stage3_orchestrator.py:1372-1407`, `modules/core/stage3_orchestrator.py:1888-1919`에서 `save_stage_attempt`와 `save_director_selection`을 기록한다.
   - `modules/core/stage3_context.py:10-13`, `modules/core/stage3_context.py:32-42`, `modules/core/stage3_context.py:101-127`에는 `Stage4->3` handoff callback slot 자체가 없다.
5. downstream 영향 경계
   - `Stage4 manuscript reject -> Stage3 blueprint full regeneration` 경계 전체
   - 가장 강한 escalation 상황인 `LOGIC_ERROR` 연속 실패에서 오히려 reject meaning이 다음 stage로 전달되지 않는다.
   - 이 경로에서는 `category`, `responsibility`, `open_review`, `score_breakdown`, `retry directives`뿐 아니라 `Stage3` 관측/감사 경로도 함께 우회된다.
6. 현재 테스트 근거 또는 테스트 부재
   - 존재하는 테스트:
     - `tests/test_v75b_escalation.py:345-396`은 `_regenerate_blueprint()`의 `no_agent / success / invalid` 반환만 검증한다.
     - `tests/test_stage3_orchestrator.py:279-368`은 `Stage3` 자체 실행 시 stage3 기록이 남는지만 본다.
   - 부재:
     - `Stage4 rejection payload -> _regenerate_blueprint -> three_phase generate(external_feedback=...)` 통합 테스트가 없다.
     - `Stage4-triggered Stage3 regen`이 `Stage3` audit / selection logging을 남기는지 검증하는 테스트도 없다.
7. 기존 문서와의 중복 여부
   - `related-but-new`
   - `MRF-T4-001`은 helper dead wiring을 다뤘고, 이번 finding은 실제 live recovery path가 `Stage3` 자체를 우회한다는 더 강한 runtime bypass를 채택한다.
8. 권장 후속 조치
   - `V75-B` regeneration을 `Stage3Orchestrator` 경유 경로로 재배선하거나,
   - 최소한 `external_feedback`, `error_category`, `fix_scope_reasoning` 등 Stage4 reject payload를 `bp_agent.generate()`에 결정적으로 전달해야 한다.
   - `Stage4 LOGIC_ERROR 2연속 -> Stage3 regen prompt` 통합 테스트를 추가해 semantic payload 존재를 잠가야 한다.

### [MCS-T1-002]

1. ID
   - `[MCS-T1-002]`
2. Severity
   - `P1`
3. 현상 요약
   - 현재 살아 있는 `Stage4 -> Stage3` 경로인 `V75-D inplace blueprint patch`는 structured reject semantics를 단일 `director_feedback` 문자열로 압축한다.
   - `Stage4`는 실제로 `selection_reason`, `verdict_reason`, `open_review`, `fix_scope_reasoning`, `runtime_advisory`, `retry_directives`를 저장할 수 있지만,
     `Stage3` 쪽 patch consumer는 `director_feedback` 문자열만 받는다.
   - 이 문자열 조립 과정도 `error_category`, `verdict_reason`, `fix_scope_reasoning`을 명시적 필드로 보존하지 않는다.
   - 결과적으로 `same rejection meaning`이 `same string blob`으로만 전달되어 semantic rewrite가 발생한다.
4. 코드 근거
   - `modules/core/stage4_interview_round.py:273-358`의 `_build_retry_feedback_provenance()`는
     - `action_items`
     - `feedback.issues`
     - evidence summary
     - runtime advisory
     - retry directives
     를 합쳐 `merged_feedback`를 만든다.
   - 같은 함수는 `error_category`, `verdict_reason`, `fix_scope_reasoning`을 독립 필드로 포함하지 않는다.
   - `modules/core/stage4_orchestrator.py:1117-1121`은 `_inplace_patch_blueprint(original_blueprint=..., director_feedback=director_feedback, ...)` 형태로 문자열 하나만 넘긴다.
   - `modules/domain/agents/three_phase_blueprint_generator.py:673-729`의 `_inplace_patch_blueprint()`는 `director_feedback` 문자열만 prompt에 주입한다.
   - 반면 `Stage4`는 `modules/core/stage4_interview_round.py:4510-4533`과 `modules/core/db_manager.py:3096-3162`를 통해
     - `selection_reason`
     - `verdict_reason`
     - `open_review`
     - `fix_scope_reasoning`
     - `runtime_advisory`
     - `retry_directives`
     를 별도 필드로 저장한다.
5. downstream 영향 경계
   - `Stage4 reject -> Stage3 inplace blueprint patch` 경계
   - reject cause의 강도와 책임 경계가 `category/severity/responsibility`가 아니라 단일 자연어 문자열의 포함 여부에 의존하게 된다.
   - 이후 patch prompt에서는 어떤 부분이 Director의 자유 리뷰인지, 어떤 부분이 구조적 책임인지, 어떤 부분이 runtime advisory인지 명확히 구분되지 않는다.
6. 현재 테스트 근거 또는 테스트 부재
   - 존재하는 테스트:
     - `tests/test_stage4_interview_round.py:1596-1622`는 `runtime_advisory`, `retry_directives`, `open_review`, `fix_scope_reasoning`이 `stage_attempts`에 저장되는지만 확인한다.
     - `tests/test_pass_with_fix.py:2122-2161`은 `Stage4` 내부 `PASS_WITH_FIX` 루프에서 reasoning/open_review가 patch feedback 문자열에 포함되는지만 본다.
   - 부재:
     - `Stage4 V75-D blueprint patch prompt`가 `error_category`, `fix_scope_reasoning`, `verdict_reason`을 의미 손실 없이 받는지 검증하는 테스트가 없다.
     - `Stage4 persisted rationale fields`와 `Stage3 blueprint patch prompt`를 교차 검증하는 테스트도 없다.
7. 기존 문서와의 중복 여부
   - `related-but-new`
   - 기존 `stage4-director-cw-feedback-loop` 감리는 `Director -> ChiefWriter` 루프를 다뤘고, 이번 finding은 `Director/Stage4 -> Blueprint patch` 경계의 semantic rewrite를 다룬다.
8. 권장 후속 조치
   - `_inplace_patch_blueprint()`의 입력을 문자열 하나가 아니라 structured payload로 확장해야 한다.
   - 최소한 `error_category`, `fix_scope_reasoning`, `open_review`, `verdict_reason`을 별도 prompt 섹션으로 분리 주입해야 한다.
   - `Stage4 reject result -> blueprint patch prompt` 통합 테스트에서 각 필드가 실제 prompt에 살아 있는지 확인해야 한다.

### [MCS-T1-003]

1. ID
   - `[MCS-T1-003]`
2. Severity
   - `P2`
3. 현상 요약
   - `main_a.py`의 `_enrich_director_result()`는 `Stage4 -> Stage3 semantic preservation` 관점에서 dead surface일 뿐 아니라 live consumer 계약과도 맞지 않는다.
   - helper는 `action_items`를 `type/description/severity/suggestion` dict 리스트로 만들고, `responsibility`, `responsibility_guide`, `breakdown_feedback`, `quantified_feedback`까지 추가한다.
   - 그러나 실제 Director/Stage4 consumer는 `feedback`를 문자열 또는 string list 중심으로 다루고, `action_items`도 최종적으로 `str(...)`로 취급한다.
   - 따라서 이 helper는 현재 호출되지 않으며, 설령 배선하더라도 semantic field가 구조적으로 보존되기보다 dict stringification으로 붕괴될 가능성이 높다.
4. 코드 근거
   - `main_a.py:432-569`의 `_enrich_director_result()`는
     - `action_items` dict 생성
     - `breakdown_feedback`
     - `responsibility`
     - `responsibility_guide`
     - `quantified_feedback`
     를 추가한다.
   - repo 전역 검색 기준 `_enrich_director_result(`의 call site는 `main_a.py:432` 정의부뿐이다.
   - `modules/core/response_schemas.py:130-175`의 `DIRECTOR_AUDIT_SCHEMA`는 `feedback`를 문자열로 정의하며, helper가 상정한 structured `action_items`/`responsibility` 계약을 명시하지 않는다.
   - `modules/domain/agents/director_ensemble.py:1343-1360`은 최종 결과에 `selection_reason`, `verdict_reason`, `feedback`, `action_items`, `open_review`, `error_category`, `fix_scope_reasoning`를 싣지만 `responsibility*` 계열은 다루지 않는다.
   - `modules/core/stage4_interview_round.py:307-309`와 `modules/core/stage4_interview_round.py:4138-4155`는 `action_items`와 `issues`를 모두 `str(...)`로 평탄화해 문자열 섹션으로 합친다.
5. downstream 영향 경계
   - 현재는 dead surface라 live corruption은 일으키지 않지만,
   - 문서/테스트/개발자 기대상으로는 richer semantic helper가 존재하는 것처럼 보이기 때문에 semantic-preservation 보장 수준을 과대평가하게 만든다.
   - 이후 무리하게 재배선될 경우 `severity`, `responsibility`, `suggestion`이 구조 필드가 아니라 dict 문자열로 Stage3 prompt에 섞일 위험이 있다.
6. 현재 테스트 근거 또는 테스트 부재
   - 존재하는 테스트:
     - `tests/test_feedback_system.py:408-427`은 `_generate_reverse_feedback_stage4_to_3()` pure helper만 검증한다.
     - `tests/test_stage4_interview_round.py:1596-1622`는 stage4 저장 필드만 확인한다.
   - 부재:
     - `_enrich_director_result()`의 live wiring 테스트가 없다.
     - helper가 만든 structured `action_items`가 실제 Stage4/Stage3 consumer와 호환되는지 검증하는 테스트도 없다.
7. 기존 문서와의 중복 여부
   - `related-but-new`
   - `MRF-T4-003`은 `_enrich_director_result()`의 dead/live 미연결을 `Stage4->2` 압축 경계에서 다뤘고,
     이번 finding은 `Stage4->3` consumer 계약과의 shape drift를 별도로 고정한다.
8. 권장 후속 조치
   - `_enrich_director_result()`를 살릴지 버릴지 먼저 결정해야 한다.
   - 살릴 경우 `DIRECTOR_AUDIT_SCHEMA`, `director_ensemble`, `stage4_interview_round`, `blueprint patch/regenerate` 소비 경계를 모두 동일한 structured 계약으로 재정렬해야 한다.
   - 버릴 경우 dead helper와 관련된 과도한 의미 기대를 문서와 테스트에서 제거해야 한다.

---

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| `Stage4 LOGIC_ERROR -> V75-B regen` semantic payload | 미검증 | `_regenerate_blueprint()`가 `external_feedback` 또는 동등 payload를 실제 넘기는지 보는 통합 테스트 |
| `Stage4 reject -> V75-D blueprint patch prompt` | 미검증 | `error_category`, `fix_scope_reasoning`, `open_review`, `verdict_reason`가 patch prompt에 살아 있는지 확인하는 테스트 |
| `_enrich_director_result()` live wiring | 미검증 | helper 호출 경로 존재 여부와 consumer shape 호환성 테스트 |
| `Stage4-triggered Stage3 recovery` observability | 미검증 | stage4-triggered regen이 stage3 audit / selection logging을 남기는지 보는 회귀 테스트 |

---

## PASS 요약

- PASS1 후보: `4`
- PASS2 제거: `1`
- PASS3 확정: `3`

정리하면, 이번 범위의 핵심 문제는 단순히 `helper가 안 꽂혔다`가 아니다.

- `full regeneration`은 아예 `Stage3` semantic contract를 우회한다.
- `inplace patch`는 살아 있지만 structured reject meaning을 단일 문자열로 압축한다.
- `enrich helper`는 richer contract를 약속하는 듯 보이지만 현재는 dead이고, shape 자체도 live consumer와 맞지 않는다.

즉 `Stage4 -> Stage3`는 일부 경로에서 `semantic-loss`가 아니라 `semantic-bypass`이고,
나머지 경로에서도 `semantic-rewrite`가 일어나는 상태다.

