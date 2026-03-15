# TF-014 Console Print Audit

Date: 2026-03-16
Status: final
Canonical Path: `docs/2026-03-16/tf-014-console-print-audit.md`
Parent Lane: `docs/2026-03-15/post-remediation-unqueued-survey-followups-execution-ssot.md`
Commit State:
- Baseline Commit: `bbb00a77c7356a32fe6358642cff0d3d445b7e8e`
- Baseline Dirty Summary: `dirty: active post-remediation docs/temp edits, desktop/runtime/stage4 patches, tests, projects/000 artifacts, and untracked post-remediation reports`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `TF-014 is being realized as the first later-hardening item; TF-015, TF-016, and TF-019 remain queued behind it`
Source Evidence:
- `docs/2026-03-15/post-remediation-unqueued-survey-followups-execution-ssot.md`
- `docs/2026-03-15/post-remediation-unqueued-survey-followups-3pass-audit.md`
- `docs/2026-03-15/codebase-global-post-remediation-tf-composition.md`
- live runtime raw-print inventory over `main_a.py` and `modules/`
- `tests/test_runtime_print_allowlist.py`

## 1. Intent
- Re-audit the runtime-facing raw `print()` surface before any code-health churn starts.
- Remove only the diagnostic raw prints that are still unjustified in the live runtime path.
- Preserve explicit operator-facing bootstrap notices and spinner spacing where the console contract still requires them.

## 2. Live Findings
- Regex inventory over `main_a.py` plus `modules/` reports `64` `print(` hits, but that includes `console.print(...)` Rich calls and comments.
- AST inventory over builtin `print(...)` calls is the authoritative boundary:
  - `main_a.py`: `4`
  - `modules/core/stage2_finalizer.py`: `2`
  - `modules/core/vec_memory.py`: `1`
  - `modules/core/stage0/spinner.py`: `8`
- The `8` prints in `modules/core/stage0/spinner.py` are blank-line spacing for operator-facing spinner teardown and are intentionally preserved.
- The `2` bootstrap prints in `main_a.py` are also intentionally preserved:
  - faulthandler enabled notice
  - faulthandler initialization failure notice
- The remaining `5` builtin prints were diagnostic-only and duplicated or bypassed existing logging/UI surfaces:
  - `main_a.py`: Stage 0 lazy-import failure, V50 optional-module availability warning
  - `modules/core/stage2_finalizer.py`: Director audit start/status notices
  - `modules/core/vec_memory.py`: fallback `ui_log` print shim

## 3. Realization
- `main_a.py`
  - replaced the Stage 0 and V50 lazy-import `print(...)` calls with `logging.getLogger(__name__).warning(...)`
- `modules/core/stage2_finalizer.py`
  - removed the duplicate raw Director status prints and kept `self.ctx.ui.log(...)` as the visible operator surface
- `modules/core/vec_memory.py`
  - replaced the default `ui_log` fallback print shim with structured logging through the `VecMemory` logger
- `tests/test_runtime_print_allowlist.py`
  - tightened the `main_a.py` allowlist to only the two bootstrap prints
  - added explicit zero-print guards for `modules/core/stage2_finalizer.py` and `modules/core/vec_memory.py`
  - added an explicit allowlist entry for `modules/core/stage0/spinner.py` so the retained blank-line spacing stays bounded and intentional

## 4. Result
- Runtime builtin `print(...)` count dropped from `15` to `10`.
- The remaining runtime builtin prints are now only:
  - `main_a.py`: `2` bootstrap notices
  - `modules/core/stage0/spinner.py`: `8` operator-facing blank-line prints
- No broad repo-wide script/test cleanup was attempted here; this landed only the bounded runtime side of `TF-014`.

## 5. Verification
- `python -m py_compile main_a.py modules/core/stage2_finalizer.py modules/core/vec_memory.py tests/test_runtime_print_allowlist.py`
- `python -m pytest tests/test_runtime_print_allowlist.py` -> `1 passed`
- `python -m pytest tests/test_stage2_finalizer.py -k "director_pass_returns_break or director_reject_returns_retry"` -> `2 passed, 22 deselected`
- `python -m pytest tests/test_vec_memory.py -k "test_in_memory_operational or test_status_fields or test_no_sqlite_vec_graceful"` -> `3 passed, 64 deselected`
- AST recount after patch:
  - `main_a.py` -> `2`
  - `modules/core/stage2_finalizer.py` -> `0`
  - `modules/core/vec_memory.py` -> `0`
  - `modules/core/stage0/spinner.py` -> `8`

## 6. Follow-On
- Close `TF-014` inside the residual lane.
- Continue with `TF-015` as the next later-hardening item.
