# TF-019 Guard Chain Config Validation

Date: 2026-03-16
Status: final
Canonical Path: `docs/2026-03-16/tf-019-guard-chain-config-validation.md`
Parent Lane: `docs/2026-03-15/post-remediation-unqueued-survey-followups-execution-ssot.md`
Commit State:
- Baseline Commit: `bbb00a77c7356a32fe6358642cff0d3d445b7e8e`
- Baseline Dirty Summary: `dirty: active post-remediation docs/temp edits, desktop/runtime/stage4 patches, tests, projects/000 artifacts, and untracked post-remediation reports`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `TF-019 is realized as the final residual hardening item after TF-014, TF-015, and TF-016 closure`
Source Evidence:
- `docs/2026-03-15/post-remediation-unqueued-survey-followups-execution-ssot.md`
- `modules/core/genre_guards/work_guard.py`
- `modules/core/project_support.py`
- `main_a.py`
- live `projects/**/config/work_guard.yaml` inventory

## 1. Intent
- Fail fast when a present `work_guard.yaml` is malformed or structurally invalid.
- Keep missing or zero-byte guard files non-fatal so existing default boot behavior remains stable.
- Surface invalid guard configs through support-summary helpers instead of silently treating them as ready.

## 2. Live Findings
- Before this patch, `WorkGuard._load_yaml()` swallowed malformed YAML and wrong root/container shapes by returning `{}`.
- That meant boot could silently downgrade to the base guard even when `work_guard.yaml` existed but was invalid.
- `load_work_guard_summary()` only reported existence and list counts, so invalid configs could still look operator-ready.
- Live project inventory currently shows only `1` zero-byte `work_guard.yaml` under an archival UI-test project; no populated active-project guard file needed migration before this change.

## 3. Realization
- Added `WorkGuardConfigError`, `validate_work_guard_config(...)`, and `load_work_guard_config(...)` in `modules/core/genre_guards/work_guard.py`.
- Present guard files now fail on:
  - YAML parse errors
  - non-mapping top-level payloads
  - wrong container types for the known list/mapping sections used by `WorkGuard`
- `main_a.py` now logs `invalid work_guard.yaml` and re-raises the config error during boot instead of silently continuing.
- `modules/core/project_support.py` now reports:
  - `work_guard_valid`
  - `work_guard_error`
  - `ready=False` for invalid present configs

## 4. Result
- Invalid present guard configs are now explicit startup failures instead of silent baseline fallbacks.
- Missing files still resolve to default behavior, and zero-byte files remain non-ready rather than fatal.
- Support surfaces can now distinguish `missing` from `invalid`.

## 5. Verification
- `python -m py_compile modules/core/genre_guards/work_guard.py modules/core/project_support.py main_a.py tests/test_work_guard.py tests/test_project_support.py tests/test_main_a_boot_binding.py`
- `ruff check modules/core/genre_guards/work_guard.py modules/core/project_support.py main_a.py tests/test_work_guard.py tests/test_project_support.py tests/test_main_a_boot_binding.py` -> `All checks passed!`
- `python -m pytest tests/test_work_guard.py -k "invalid_yaml or invalid_work_identity_shape"` -> `2 passed, 31 deselected`
- `python -m pytest tests/test_project_support.py -k "invalid_yaml or invalid_work_guard_not_ready or handles_missing_file"` -> `3 passed, 6 deselected`
- `python -m pytest tests/test_main_a_boot_binding.py -k "invalid_work_guard or has_no_bare_input_calls or routes_prompt_helpers"` -> `3 passed, 8 deselected`
- `python -m pytest tests/test_quality_sidecar_bootstrap.py -k "bootstrap_quality_sidecars_backfills_legacy_stage4_rows or quality_dashboard_endpoint_is_read_only_for_legacy_quality_sidecars"` -> `2 passed`
- `python -m pytest tests/test_bridge_quality_summary.py -k "quality_dashboard_endpoint_combines_result_and_patterns"` -> `1 passed, 7 deselected`

## 6. Follow-On
- Close `TF-019` inside the residual lane.
- Close the residual lane itself and remove its temp mirror from `docs/temp/`.
