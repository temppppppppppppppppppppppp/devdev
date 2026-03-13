# [MDH-T5] Call Graph / Runtime Artifact / Regression Findings

> 작성일: 2026-03-13
> 상태: `executed / PASS3 re-audited`
> 조사 모드: `static / read-only / code-and-test verification / source-report cross-check / UTF-8 only`
> 기준 오더: `main_a-dormant-helper-live-consumer-detail-full-survey-audit-order.md`
> 작성자: `codex`
> 재감리 메모: `opus` 1차 초안의 exact-name grep 결과를 dynamic DI, `getattr` wiring, targeted test로 재검증했다.
> 최종 판정: `retained P2 3건, PASS2 제거 3건, helper ledger corrected`

이 문서는 T1~T4 범위 25개 helper에 대해 repo 전역 검색, 실제 orchestrator/context wiring, e2e/smoke/canary artifact, 기존 감리 문서를 다시 대조한 T5 재감리본이다.
코드 직접 수정은 수행하지 않았다.

---

## 조사 범위

- repo 전역 검색 결과
- `main_a.py`
- `modules/core/stage2_context.py`
- `modules/core/stage2_preflight.py`
- `modules/core/stage2_validation_pipeline.py`
- `modules/core/stage3_context.py`
- `modules/core/stage4_context.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/services/project_service.py`
- `modules/core/services/state_service.py`
- `modules/core/prompt_builder.py`
- `tests/e2e/test_l3_golden_route.py`
- `tests/e2e/test_l3_stage3_smoke.py`
- `tests/e2e/test_l3_stage4_smoke.py`
- `tests/e2e/test_retry_recovery_e2e.py`
- `tests/test_run_stage4_canary.py`
- `scripts/run_stage2_smoke.py`
- `scripts/run_stage3_smoke.py`
- `scripts/run_stage4_smoke.py`
- `scripts/run_stage4_canary.py`
- 기존 감리 문서
  - `MDH-T1-retry-guidance-helper-liveness-findings.md`
  - `MDH-T3-stage01-npc-ui-helper-liveness-findings.md`
  - `MDH-T4-bootstrap-history-cache-helper-liveness-findings.md`
  - `main_a-retry-feedback-detail-consolidated-findings.md`
  - `main_a-facade-shim-detail-consolidated-findings.md`
  - `main_a-persistence-narrative-detail-consolidated-findings.md`

### 추가 실행 검증

- PASS
  - `pytest tests/test_stage4_context_builder.py::TestBuildMandatoryContext::test_writer_guidance_is_injected_into_live_prompt_path tests/test_stage4_orchestrator.py::TestHandleRoundOutcomeErrorPaths::test_handle_round_outcome_injects_stage4_to_3_feedback_into_inplace_patch tests/test_run_stage4_canary.py::test_run_canary_saves_and_flushes_before_analyze -q`
  - 결과: `3 passed`
- FAIL
  - `pytest tests/test_stage4_context.py::TestStage4Context::test_from_app_extracts_callbacks -q`
  - 결과: `AttributeError: 'Stage4Context' object has no attribute 'generate_writer_guidance_v60_8'`
  - 해석: `Stage4Context.from_app()`는 신규 callback wiring을 시도하지만 `__slots__`가 이를 따라가지 못해 Stage4 callback extraction 자체가 현재 worktree에서 깨져 있다.

---

## PASS 기록

### PASS 1 - 표면 수집

후보 6건을 잡았다.

- 후보 A: OPUS 초안이 `dead/dormant`로 분류한 helper 중 일부가 dynamic DI 또는 `getattr` 경로로 실제 live consumer를 가질 가능성
- 후보 B: `_classify_rejection_feedback()` dormant 여부
- 후보 C: e2e/smoke/canary가 helper live contract를 실제로 검증하는지 여부
- 후보 D: `_load_v50_history()`는 dead인지, live one-shot no-op인지 여부
- 후보 E: T3 NPC/archetype facade 4종에 hidden runtime caller가 있는지 여부
- 후보 F: `_restore_preset_registry()` / bootstrap 계열이 runtime artifact에서 다른 hidden consumer를 갖는지 여부

### PASS 2 - 교차 검증

후보 3건을 제거하거나 재분류했다.

- RC-1 제거
  - 기존 OPUS 초안의 `dead cluster` 안에 있던 `_generate_writer_guidance_v60_8`, `_enrich_director_result`는 제거했다.
  - 근거: `main_a.py:3544`에서 `Stage4Context.from_app(self)`가 runtime에 연결되고, `modules/core/stage4_context_builder.py:2514-2533`, `modules/core/stage4_interview_round.py:839-870,1902`가 해당 callback을 실제 소비한다.
  - 단, 현재 worktree에서는 `modules/core/stage4_context.py:148-149`가 `__slots__` 불일치로 실패하므로 상태는 `dead/dormant`가 아니라 `live-wired / runtime-gated`다.

- RC-2 제거
  - 기존 OPUS 초안의 `_generate_reverse_feedback_stage4_to_3` dormant claim은 제거했다.
  - 근거: `modules/core/stage4_orchestrator.py:267-305,1166-1228`가 `self.app._generate_reverse_feedback_stage4_to_3`를 직접 호출한다.
  - targeted test `tests/test_stage4_orchestrator.py::TestHandleRoundOutcomeErrorPaths::test_handle_round_outcome_injects_stage4_to_3_feedback_into_inplace_patch`도 통과했다.

- RC-3 제거
  - `_load_v50_history()`를 T5 신규 dormant finding으로 다시 열지 않았다.
  - 근거: `main_a.py:1955-1956`에서 live bootstrap caller가 존재하고, 현재 본체는 no-op stub이다.
  - 분류는 `live / no-op legacy`로 바로잡되, defect 자체는 `MDH-T4-003`으로 이미 잠겨 있으므로 T5 신규 finding으로 재오픈하지 않는다.

후보 B, C는 retained finding으로 유지했다.
후보 E, F는 hidden runtime caller가 없음을 확인했으므로 finding 대신 corrected ledger에 반영했다.

---

## PASS 3 - 최종 확정 Findings

### Finding Ledger

| ID | Sev | 상태 | 파일/함수 | 요약 | duplicate status |
|----|-----|------|-----------|------|------------------|
| `MDH-T5-001` | `P2` | confirmed | `main_a.py`, `stage4_context.py`, `stage4_context_builder.py`, `stage4_interview_round.py`, `stage4_orchestrator.py` | exact-name grep만으로는 Stage4/boot helper live consumer를 복원할 수 없고, 실제로 OPUS 초안의 dead/dormant 분류 일부가 false negative였다 | `related-but-new-live-consumer-surface` |
| `MDH-T5-002` | `P2` | confirmed | `main_a.py::_classify_rejection_feedback`, `state_service.py`, `feedback_system.py` | `_classify_rejection_feedback()`는 구현과 하위 테스트는 있으나 production caller와 DI export가 없는 dormant surface다 | `related-but-new-live-consumer-surface` |
| `MDH-T5-003` | `P2` | confirmed | `tests/e2e/*.py`, `scripts/run_stage*_smoke.py`, `tests/test_run_stage4_canary.py` | e2e/smoke/canary artifact는 real app-bound helper wiring을 충분히 pin하지 못해 live consumer drift와 dormant misclassification을 잡지 못한다 | `related-but-new-live-consumer-surface` |

---

## 상세 Findings

### [MDH-T5-001] P2 | dynamic DI / getattr 경로를 빼면 Stage4/boot helper live consumer inventory가 틀어진다

1. ID
   - `MDH-T5-001`
2. Severity
   - `P2`
3. 현상 요약
   - OPUS 1차 초안은 exact-name grep 중심으로 helper liveness를 분류했지만, 현재 codebase에는 literal helper 이름이 아니라 `from_app()`, `getattr()`, callback name indirection으로 소비되는 live surface가 있다.
   - 그 결과 `_generate_writer_guidance_v60_8`, `_generate_reverse_feedback_stage4_to_3`, `_enrich_director_result`, `_build_item_acquisition_timeline`, `_load_v50_history` 중 최소 5개가 dead/dormant 쪽으로 잘못 기울었다.
   - 이 오분류는 "삭제해도 되는 helper"와 "실제 배선은 있는데 현재 runtime gate가 깨진 helper"를 구분하지 못하게 만든다.
4. 코드 근거
   - `main_a.py:3544`
     - Stage4 진입 시 `self._stage4_orch.ctx = Stage4Context.from_app(self)`로 callback wiring을 건다.
   - `modules/core/stage4_context.py:111-118,148-149,191-197`
     - `build_item_acquisition_timeline`, `generate_writer_guidance_v60_8`, `enrich_director_result`, `flush_audit_buffer`를 app-bound callback으로 주입하려고 시도한다.
   - `modules/core/stage4_context_builder.py:1864,2514-2533`
     - `self.ctx.build_item_acquisition_timeline(...)`
     - `self.ctx.generate_writer_guidance_v60_8(...)`
   - `modules/core/stage4_interview_round.py:839-870,1902`
     - `self.ctx.enrich_director_result(...)`를 통해 Director 결과 enrich 경로를 실제로 소비한다.
   - `modules/core/stage4_orchestrator.py:267-305,1166-1228`
     - `self.app._generate_reverse_feedback_stage4_to_3`를 직접 조회·호출한다.
   - `main_a.py:1955-1956`
     - `_init_v50_modules()` 말미에서 `_load_v50_history()`를 실제 호출한다.
   - targeted test PASS
     - `tests/test_stage4_context_builder.py::TestBuildMandatoryContext::test_writer_guidance_is_injected_into_live_prompt_path`
     - `tests/test_stage4_orchestrator.py::TestHandleRoundOutcomeErrorPaths::test_handle_round_outcome_injects_stage4_to_3_feedback_into_inplace_patch`
     - `tests/test_run_stage4_canary.py::test_run_canary_saves_and_flushes_before_analyze`
   - targeted test FAIL
     - `tests/test_stage4_context.py::TestStage4Context::test_from_app_extracts_callbacks`
     - 실패 원인: `Stage4Context.__slots__`가 `generate_writer_guidance_v60_8`, `enrich_director_result`를 포함하지 않아 callback extraction이 깨진다.
5. downstream 영향 경계
   - 잘못된 inventory를 기준으로 dead-code cleanup을 하면 Stage4 retry guidance, blueprint reverse feedback, Director enrich, item timeline helper를 잘못 제거할 수 있다.
   - 반대로 현재 문제의 본질은 dead helper가 아니라 `live wiring은 있는데 Stage4Context gate가 깨진 상태`라는 점인데, exact-name grep-only inventory는 이를 놓친다.
   - bootstrap 측면에서도 `_load_v50_history()`는 caller가 있으므로 dead가 아니라 `live/no-op legacy`로 다뤄야 한다.
6. 현재 테스트 근거 또는 테스트 부재
   - positive unit coverage는 일부 존재한다.
     - writer guidance 주입 경로: `1 passed`
     - Stage4→3 reverse feedback 주입 경로: `1 passed`
     - canary flush 경로: `1 passed`
   - 그러나 Stage4 callback extraction의 핵심 factory test는 현재 실패한다.
     - `tests/test_stage4_context.py::TestStage4Context::test_from_app_extracts_callbacks`
     - 즉, live consumer inventory는 `존재함`이 맞지만 runtime health는 별도 FAIL gate를 가진다.
7. 기존 문서와의 중복 여부
   - `related-but-new-live-consumer-surface`
   - 기존 T1/T4 문서가 개별 helper를 dormant/dead로 적었지만, T5 재감리의 책임은 그 문서들을 runtime artifact와 dynamic wiring으로 다시 교차 검증해 inventory 자체를 바로잡는 데 있다.
8. 권장 후속 조치
   - consolidated 문서 작성 시 `dead/dormant`와 `live-wired / runtime-gated`를 분리한다.
   - `Stage4Context.__slots__`와 callback 필드를 맞춰 runtime gate failure를 remediation 단계에서 별도 처리한다.
   - 이후 helper 정리 작업은 literal grep이 아니라 `from_app()` / `getattr()` / callback name indirection을 포함한 inventory를 기준으로 수행한다.

### [MDH-T5-002] P2 | `_classify_rejection_feedback()`는 하위 구현만 검증되고 main_a 표면은 dormant다

1. ID
   - `MDH-T5-002`
2. Severity
   - `P2`
3. 현상 요약
   - `main_a.py:2825-2829`의 `_classify_rejection_feedback()`는 `StateService -> FeedbackSystem`으로 위임하는 thin delegate다.
   - 하지만 `main_a.py` wrapper 자체를 호출하는 production code가 repo 전역에 없고, Stage2/3/4 context 어느 곳에도 DI export되지 않는다.
   - 하위 구현 테스트가 풍부하더라도 app surface 관점에서는 dormant export다.
4. 코드 근거
   - `main_a.py:2825-2829`
     - thin delegate 정의
   - `modules/core/services/state_service.py:236-239`
     - `classify_rejection_feedback()` thin delegate
   - `modules/core/feedback_system.py:791`
     - 실제 구현
   - repo 전역 검색
     - `_classify_rejection_feedback` literal ref는 `main_a.py` 정의 1건만 존재
     - `stage2_context.py`, `stage3_context.py`, `stage4_context.py`에 callback slot 없음
5. downstream 영향 경계
   - 현재 runtime은 rejection reason taxonomy를 app surface에서 직접 소비하지 못한다.
   - retry strategy가 reason bucket에 따라 달라져야 한다면, 그 기능은 main_a boundary에서 사실상 닫혀 있다.
   - 즉 "구현은 있지만 consumer가 없다"는 dormant surface이며, future cleanup 또는 배선 결정이 필요하다.
6. 현재 테스트 근거 또는 테스트 부재
   - 하위 구현 테스트는 있다.
     - `tests/test_feedback_system.py`의 분류 테스트 다수
     - `tests/test_state_service.py:235-236`의 위임 테스트
   - main_a wrapper 직접 테스트는 없다.
   - production caller 테스트도 없다.
7. 기존 문서와의 중복 여부
   - `related-but-new-live-consumer-surface`
   - 기존 문서는 coverage gap 또는 하위 구현 관점에 머물렀고, T5가 main_a boundary에서 dormant 확정을 잠근다.
8. 권장 후속 조치
   - 기능이 필요하면 Stage2 또는 Stage4 retry loop에서 명시적으로 callback export를 추가한다.
   - 기능이 불필요하면 main_a wrapper를 정리하고 하위 구현만 유지할지 결정한다.

### [MDH-T5-003] P2 | e2e/smoke/canary는 real app-bound helper contract를 충분히 pin하지 못한다

1. ID
   - `MDH-T5-003`
2. Severity
   - `P2`
3. 현상 요약
   - 현재 e2e/smoke/canary artifact는 real `SovereignApp` helper surface를 직접 소비하기보다 `lambda`, `MagicMock`, `SimpleNamespace`로 callback을 대체해 조립한다.
   - 이 패턴은 helper signature, binding source, side effect가 drift해도 green을 유지하게 만든다.
   - 특히 이번 재감리에서 live로 바로잡은 Stage4 helper들(`_generate_writer_guidance_v60_8`, `_generate_reverse_feedback_stage4_to_3`, `_enrich_director_result`, `_build_item_acquisition_timeline`)은 runtime artifact에서 직접 pin되지 않는다.
4. 코드 근거
   - `tests/e2e/test_l3_golden_route.py:237-253`
     - Stage2Context를 lambda 묶음으로 수동 조립한다.
   - `scripts/run_stage2_smoke.py:253-269`
     - 동일한 lambda 기반 Stage2Context 조립
   - `tests/e2e/test_l3_stage3_smoke.py:133-146`
     - `_get_arc_context_for_episode`, `_validate_arc_data_fields`, `_validate_blueprint_integrity`, `_audit_event`, `_write_audit_summary`를 `MagicMock`으로 직접 주입
   - `scripts/run_stage3_smoke.py:118-129`
     - 동일한 MagicMock 패턴
   - `tests/e2e/test_l3_stage4_smoke.py:115-123`
     - Stage4Context를 `SimpleNamespace` + lambda callback으로 조립
   - `scripts/run_stage4_smoke.py:100-107`
     - 동일한 Stage4 smoke 조립
   - `tests/test_run_stage4_canary.py:8-17`
     - canary는 `_flush_audit_buffer` / pass-rate monitor save 순서만 pin하고, writer guidance / enrich / reverse feedback 경로는 직접 검증하지 않는다.
5. downstream 영향 경계
   - helper가 live consumer와 맞게 연결돼 있는지에 대한 회귀망이 약하다.
   - exact-name grep 오분류, bound-method drift, callback slot 누락, Stage4Context slot regression 같은 문제가 runtime artifact만으로는 빨리 드러나지 않는다.
   - dead helper를 mock으로 채워 넣어도 smoke가 통과할 수 있으므로, "테스트가 green"이 live consumer proof가 되지 않는다.
6. 현재 테스트 근거 또는 테스트 부재
   - helper-specific unit proof는 일부 존재한다.
     - writer guidance live prompt path: `1 passed`
     - Stage4→3 reverse feedback injection: `1 passed`
     - canary flush path: `1 passed`
   - 하지만 `from_app()` callback extraction 자체는 현재 fail이다.
     - `tests/test_stage4_context.py::TestStage4Context::test_from_app_extracts_callbacks`
   - 즉, unit 단위 일부 증거는 있으나, app-bound wiring을 통합적으로 고정하는 e2e/smoke proof는 부족하다.
7. 기존 문서와의 중복 여부
   - `related-but-new-live-consumer-surface`
   - 기존 MRF/MFS/MPN 트랙이 각각 부분 blind spot을 지적했지만, T5는 runtime artifact 전체를 묶어 "real app-bound helper contract를 pin하지 못한다"는 구조 문제를 통합한다.
8. 권장 후속 조치
   - 최소 1개 Stage4 smoke/e2e에서 real `Stage4Context.from_app(app)`를 사용해 callback extraction을 직접 검증한다.
   - Stage2/3 smoke도 lambda/MagicMock 수동 조립본과 real `from_app()` 경로를 분리해 검증한다.
   - mock 사용 시 `spec_set` 또는 stricter protocol을 써서 drift 흡수를 줄인다.

---

## Corrected Helper Ledger

아래는 오더 범위 25개 helper의 corrected inventory다.

### dead (4건)

| Helper | 정의 위치 | 근거 |
|--------|-----------|------|
| `_generate_arc_position_guide` | `main_a.py:685` | 정의 외 caller 0건 |
| `_simplify_prompt_for_retry` | `main_a.py:669` | 정의 외 caller 0건 |
| `_ignite_quad_cache_system` | `main_a.py:1193` | 정의 외 caller 0건 |
| `_is_cache_alive` | `main_a.py:1338` | caller가 dead helper 내부 3건뿐 |

### dormant (5건)

| Helper | 정의 위치 | 근거 |
|--------|-----------|------|
| `_classify_rejection_feedback` | `main_a.py:2825` | 구현과 하위 테스트만 있고 production caller/DI export 0건 |
| `_extract_npc_profiles` | `main_a.py:2809` | 정의 외 caller 0건 |
| `_get_character_traits` | `main_a.py:2813` | 정의 외 caller 0건 |
| `_load_character_archetypes` | `main_a.py:2817` | 정의 외 caller 0건 |
| `_get_archetype_reference_for_npcs` | `main_a.py:2821` | 정의 외 caller 0건 |

### bypassed-live (1건)

| Helper | 정의 위치 | 근거 |
|--------|-----------|------|
| `_restore_preset_registry` | `main_a.py:379` | `ProjectService` callback 경로는 live, boot는 인라인 복제본으로 bypass |

### live (12건)

| Helper | 정의 위치 | 근거 |
|--------|-----------|------|
| `_build_focused_context` | `main_a.py:677` | `Stage2Context` dynamic callback resolution → `stage2_validation_pipeline.py:897-898` |
| `_build_minimal_arc_context` | `main_a.py:681` | `Stage2Context` dynamic callback resolution → `stage2_preflight.py:928-929` |
| `_generate_reverse_feedback_stage4_to_3` | `main_a.py:752` | `stage4_orchestrator.py:267-305,1166-1228`에서 직접 조회·호출 |
| `_audit_event` | `main_a.py:2831` | main + service/orchestrator 다수 caller |
| `_flush_audit_buffer` | `main_a.py:2835` | `atexit`, shutdown, canary 경로 live |
| `_write_audit_summary` | `main_a.py:2839` | Stage2/3/4 callback surface로 live |
| `_get_arc_context_for_episode` | `main_a.py:2843` | `Stage3Context` export 후 Stage3 consumer live |
| `_validate_arc_data_fields` | `main_a.py:2892` | `Stage3Context` export 후 Stage3 consumer live |
| `_validate_blueprint_integrity` | `main_a.py:2904` | `Stage3Context` export 후 Stage3 consumer live |
| `_validate_volume_boundaries` | `main_a.py:2730` | `stage01_helpers.py:776` live caller |
| `_show_volume_table` | `main_a.py:2908` | `stage01_helpers.py:838-839` live caller |
| `_load_v50_history` | `main_a.py:2128` | `main_a.py:1955-1956` live bootstrap caller 존재, 현재 본체는 no-op legacy stub |

### live-wired / runtime-gated (3건)

| Helper | 정의 위치 | 근거 |
|--------|-----------|------|
| `_generate_writer_guidance_v60_8` | `main_a.py:733` | `Stage4Context.from_app()` wiring + `stage4_context_builder.py:2514-2533` 소비, 단 `Stage4Context.__slots__` mismatch로 factory test FAIL |
| `_enrich_director_result` | `main_a.py:432` | `Stage4Context.from_app()` wiring + `stage4_interview_round.py:839-870,1902` 소비, 단 동일 slot regression 영향 |
| `_build_item_acquisition_timeline` | `main_a.py:2763` | `Stage4Context.from_app()` wiring + `stage4_context_builder.py:1864` 소비, 단 동일 slot regression 영향 |

### unknown (0건)

- 전 항목이 `dead / dormant / bypassed-live / live / live-wired-runtime-gated` 중 하나로 분류되었다.

---

## T5 관점 핵심 검사 결과

### 1. static grep과 runtime artifact가 같은 caller inventory를 가리키는가

- **아니다.**
- exact-name grep만 쓰면 `from_app()` / callback name indirection / `getattr()` 기반 live consumer를 놓친다.
- corrected inventory는 literal grep에 dynamic wiring 해석을 추가해야만 복원된다.

### 2. e2e / smoke / canary에서만 살아 있는 helper가 있는가

- **없다.**
- 반대로 문제는 "runtime artifact가 live helper를 증명해 주지 못하는 것"이다.
- hidden e2e-only helper는 없고, 검증이 약한 mock-driven path가 대부분이다.

### 3. 문서상 dead처럼 보였지만 runtime/production code가 live consumer를 갖는 helper가 있는가

- **있다.**
- `_generate_writer_guidance_v60_8`
- `_generate_reverse_feedback_stage4_to_3`
- `_enrich_director_result`
- `_build_item_acquisition_timeline`
- `_load_v50_history`

### 4. 이미 닫힌 finding을 dormant-helper inventory 명목으로 다시 여는 오탐은 없는가

- **거의 제거했다.**
- `_load_v50_history`는 T4에서 이미 잡힌 no-op legacy stub이므로 T5 신규 finding으로 재오픈하지 않았다.
- `_restore_preset_registry`는 bypassed-live 상태를 ledger에만 반영하고, 신규 T5 finding으로 다시 열지 않았다.

### 5. 최종 통합 시 ledger를 재구성할 수 있는가

- **가능하다.**
- corrected ledger가 25개 helper 전량을 재분류했다.
- 특히 `live-wired / runtime-gated` 범주를 별도로 둬서 "consumer 없음"과 "consumer는 있으나 factory/runtime gate가 깨짐"을 분리했다.

---

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| Stage4 callback extraction full suite | FAIL | `Stage4Context.__slots__`와 callback field 정렬 후 `tests/test_stage4_context.py` 재실행 |
| `_classify_rejection_feedback` product intent | 불명확 | retry loop가 실제로 rejection taxonomy를 소비해야 하는지 제품 의도 확인 |
| real app-bound Stage2/3 smoke parity | 부족 | lambda/MagicMock 조립 대신 `from_app()` 경로를 직접 pin하는 smoke/e2e 추가 |
| `live-wired / runtime-gated` 3건의 end-to-end health | 부족 | real `SovereignApp -> Stage4Context.from_app -> Stage4 consumer` 통합 실행 근거 |

---

## PASS 요약

- PASS1 후보: 6건
- PASS2 제거 또는 재분류: 3건
  - OPUS dead cluster 중 Stage4 helper 2건 제거
  - `_generate_reverse_feedback_stage4_to_3` dormant claim 제거
  - `_load_v50_history` 신규 T5 finding 재오픈 제거
- PASS3 확정: 3건
  - `MDH-T5-001` P2 (dynamic DI / getattr false-negative로 인한 inventory drift)
  - `MDH-T5-002` P2 (`_classify_rejection_feedback` dormant)
  - `MDH-T5-003` P2 (e2e/smoke/canary contract blind spot)

---

## 마감 체크

- 코드 근거 포함: 완료
- 테스트 근거 또는 테스트 부재 포함: 완료
- runtime artifact cross-check 포함: 완료
- 기존 문서와의 중복 여부 포함: 완료
- PASS1 -> PASS2 -> PASS3 요약 포함: 완료
- corrected helper ledger 포함: 완료
