# TF-015 Ruff Auto-Fix

Date: 2026-03-16
Status: final
Canonical Path: `docs/2026-03-16/tf-015-ruff-auto-fix.md`
Parent Lane: `docs/2026-03-15/post-remediation-unqueued-survey-followups-execution-ssot.md`
Commit State:
- Baseline Commit: `bbb00a77c7356a32fe6358642cff0d3d445b7e8e`
- Baseline Dirty Summary: `dirty: active post-remediation docs/temp edits, desktop/runtime/stage4 patches, tests, projects/000 artifacts, and untracked post-remediation reports`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `TF-015 is being realized after TF-014 closure; TF-016 and TF-019 remain behind it`
Source Evidence:
- `docs/2026-03-15/post-remediation-unqueued-survey-followups-execution-ssot.md`
- `docs/2026-03-15/codebase-global-post-remediation-tf-composition.md`
- live `ruff check modules scripts main_a.py`
- live `ruff check modules scripts main_a.py --fix`

## 1. Intent
- Apply only the auto-fixable Ruff changes inside `modules/`, `scripts/`, and `main_a.py`.
- Stop as soon as the remaining lint set becomes manual-only.
- Record any validation-caught contract regression instead of silently leaving it for `TF-016`.

## 2. Live Findings
- Before auto-fix, the residual lint backlog still contained auto-fixable import-order, annotation-modernization, UTC alias, and unused-import issues.
- Running `ruff check modules scripts main_a.py --fix` resolved `70` issues and left only `9` `E402` violations.
- The remaining `E402` findings are all script entrypoint import-position cases after deliberate `sys.path.insert(...)` bootstrapping and therefore belong to manual disposition under `TF-016`.

## 3. Realization
- Applied `ruff check modules scripts main_a.py --fix`.
- Accepted the mechanical changes across runtime and ops-support files, including:
  - import sorting
  - `typing` to builtin/`collections.abc` modernization
  - `datetime.UTC` alias upgrades
  - quoted-annotation cleanup
  - unused-import removal
- Validation exposed one contract regression:
  - `modules.api.run_validator` no longer re-exported `RISK_KEYS`
  - fixed by restoring `RISK_KEYS` as an explicit module constant sourced from `modules.api.control_plane_contract`
  - updated `modules/api/__init__.py` to import `RISK_KEYS` from the control-plane contract directly

## 4. Result
- Auto-fixable Ruff backlog is now `0`.
- The live lint backlog is reduced to only `9` `E402` findings.
- `TF-016` can now focus only on those explicit script-entrypoint import-order cases.

## 5. Verification
- `python -m py_compile main_a.py modules/api/__init__.py modules/api/bridge_server.py modules/api/prompt_broker.py modules/api/prompt_classifier.py modules/api/risk_approval.py modules/api/run_validator.py modules/core/arc_state_utils.py modules/core/db_manager.py modules/core/investment_arithmetic_checker.py modules/core/investment_math_verifier.py modules/core/services/project_service.py modules/core/services/ui_service.py modules/core/stage2_finalizer.py modules/core/stage3_orchestrator.py modules/core/stage4_context_builder.py modules/core/stage4_interview_round.py modules/core/vec_memory.py modules/domain/agents/blueprint_ensemble.py modules/domain/agents/chief_writer_context.py modules/validation/validation_orchestrator.py scripts/audit_bi_5pass.py scripts/build_execution_roadmap.py scripts/build_investment_epub_corpus.py scripts/check_utf8_hygiene.py scripts/ops_support.py scripts/ops_validator.py scripts/process_and_audit_tr_bi_loop.py scripts/repair_tr_korean_utf8.py scripts/run_auto_frontier_lag_harness.py scripts/run_pytest_lowmem.py scripts/run_stale_reference_sweep.py scripts/sync_temp_queue_state.py scripts/tr_batch_harness.py scripts/validate_deep_global_survey_bundle.py`
- `python -m pytest tests/test_run_validator.py tests/test_risk_approval.py tests/test_bridge_server_http_contract.py tests/test_bridge_server_desktop_risk_gate.py tests/test_control_plane_approval_provenance_ssot.py` -> `88 passed`
- `python -m pytest tests/test_desktop_transport_contract.py tests/test_desktop_shadow_hygiene.py tests/test_main_a_boot_binding.py tests/test_project_service.py tests/test_ui_service.py` -> `54 passed`
- `python -m pytest tests/test_stage2_finalizer.py tests/test_stage4_context_builder.py tests/test_validation_orchestrator_soft_failure.py tests/test_vec_memory.py -k "not slow"` -> `144 passed`
- `ruff check modules scripts main_a.py --statistics` -> `9 E402 remaining`

## 6. Follow-On
- Close `TF-015` inside the residual lane.
- Move to `TF-016` for the remaining `E402` script-entrypoint cases.
