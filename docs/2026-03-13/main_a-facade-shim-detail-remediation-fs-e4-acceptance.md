# main_a Facade Shim Detail Remediation FS-E4 Acceptance

> 작성일: 2026-03-13
> 상태: `executed / accepted`
> work package: `FS-E4. Stage4 NPC Facade / Validation Parity`
> 기준 문서: `main_a-facade-shim-detail-remediation-execution-ssot.md`

## 요약

`FS-E4`는 현재 코드 기준 acceptance를 만족한다.

- `Stage4Context.from_app()`가 `main_a._extract_npc_profiles` facade를 `extract_npc_profiles` callback으로 노출한다.
- `Stage4InterviewRound` live validation path는 `npc_profiles={}` 고정값을 제거하고, facade callback을 우선 사용한다.
- facade callback이 없는 경로에서도 `PromptBuilder.extract_npc_profiles()`와 같은 `KeyNPCs/Key_NPCs + arc_data text filter` 규칙으로 fallback populate 한다.
- `_run_pre_director_validation()`은 current round의 `arc_data`를 `_god1` session slot으로 넘겨 `ConsistencyValidator` input parity를 유지한다.
- Stage4 실경로 회귀는 facade binding과 `_build_cv_context()`의 `npc_profiles` population을 둘 다 잠근다.

## 코드 스코프

- `modules/core/stage4_context.py`
- `modules/core/stage4_interview_round.py`
- `tests/test_stage4_context.py`
- `tests/test_stage4_cv_context.py`

## 검증

- `pytest -q tests/test_stage4_context.py tests/test_stage4_cv_context.py tests/test_stage4_interview_round.py tests/test_prompt_builder.py`
  - `168 passed`
- `pytest -q tests/test_stage4_context.py tests/test_stage4_cv_context.py tests/test_stage4_interview_round.py tests/test_stage4_context_builder.py tests/test_stage4_orchestrator.py tests/test_prompt_builder.py tests/test_main_a_persistence_helpers.py`
  - `280 passed`

## 판정

- `MFS-T4-001`: accepted

## 다음 단위

- execution SSOT 잔여는 `FS-E5. Observability / Presentation Hygiene`만 남는다.
