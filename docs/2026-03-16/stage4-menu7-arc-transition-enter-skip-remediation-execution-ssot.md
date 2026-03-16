<!-- [완료] -->
<\!-- [완료] -->
# Stage4 Menu7 Arc Transition Enter Skip Remediation Execution SSOT

Date: 2026-03-16
Status: closed
Canonical Path: `docs/2026-03-16/stage4-menu7-arc-transition-enter-skip-remediation-execution-ssot.md`
Temp Mirror Path: `none`
Queue Disposition: `closed after targeted runtime patch and regression proof; no active temp mirror remains`
Commit State:
- Baseline Commit: `d6c81c1976d9812d447c2a78e2aeb36f7aed666a`
- Baseline Dirty Summary: `dirty: runtime/stage modules and tests, desktop packaging files, project artifacts, OPUS docs, and 2026-03-16 manuscript docs already present`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `re-audit found one remaining menu 7 final-close Stage 4 call without skip_pause; this turn patched the branch and added dedicated final-close regression proof`
Source Survey Docs:
- `docs/2026-03-16/opus/stage4-menu7-arc-transition-enter-skip-3pass-audit.md`
- `docs/2026-03-16/stage4-menu7-arc-transition-enter-skip-opus-revalidation.md`
- `docs/2026-03-15/menu7-desired-arc-input-contract-remediation-execution-ssot.md`
Evidence Artifacts:
- `docs/2026-03-16/stage4-menu7-arc-transition-enter-skip-opus-revalidation-evidence.txt`
Side-Effect Coverage: covered

## 1. Intent

- Preserve the Stage 4 per-arc Enter-skip contract for menu 7 as canonical authority.
- Prevent the older Arc-count menu 7 document from being over-read as if it also covered the post-episode Enter-skip path.

## 2. Baseline Facts

- The OPUS memo identified a valid issue class: menu 7 auto-progression should not stop for a per-arc Stage 4 Enter prompt.
- At the start of this turn, live code already contained most of the expected fix shape:
  - `main_a.py` calls Stage 4 with `skip_pause=True` from the menu 7 frontier path
  - `main_a.py` calls Stage 4 with `skip_pause=True` from the one-stop arc-range path
  - `main_a.py` forwards `skip_pause` into the Stage 4 orchestrator
  - `stage4_orchestrator.py` forwards `skip_pause` into both normal and early-return post-episode cleanup paths
  - `stage4_post_processor.py` skips the raw Enter prompt when `skip_pause=True`
- One remaining menu 7 branch was still wrong:
  - `_one_stop_pipeline_frontier_lag()` called `_stage_4_v2_chief_writer(target_ep=final_plan["stage4_target"])` without `skip_pause=True` in the `remaining_design <= 0` final-close path
- The final `[Enter] return to menu` pause remains separately governed by `wait_for_menu_return` and is not part of this issue.
- This turn closes the remaining branch gap and adds dedicated regression proof.

## 3. Scope

Included:

- `main_a.py` menu 7 frontier Stage 4 call path
- `modules/core/stage4_orchestrator.py` skip_pause forwarding
- `modules/core/stage4_post_processor.py` post-episode Enter bypass
- focused regression tests for this chain
- canonical authority documentation for this issue class

Excluded:

- menu 7 desired Arc-count input semantics
- final return-to-menu pause semantics
- backend-front prompt transport
- broad prompt-authority or continuity work

## 4. Validity And Realization Decision

Validity judgment:

- issue class: valid
- root cause chain: valid
- proposed fix shape: valid

Realization judgment:

- a targeted runtime code fix was required in `main_a.py` for the menu 7 final-close branch
- the runtime fix is now landed and this execution item closes with regression proof plus corrected canonical authority documentation

## 5. Acceptance Criteria

- menu 7 frontier path sends `skip_pause=True` into the Stage 4 wrapper
- menu 7 final-close path sends `skip_pause=True` into the Stage 4 wrapper
- one-stop arc-range path sends `skip_pause=True` into the Stage 4 wrapper
- the Stage 4 wrapper forwards `skip_pause` into the orchestrator
- the orchestrator forwards `skip_pause` into the post-episode cleanup path
- the post processor does not call raw `input(...)` when `skip_pause=True`
- the final menu-return pause remains separately controlled

## 6. Verification Plan

- `python -m py_compile main_a.py tests/test_stage4_post_processor.py tests/test_main_a_stage_entry_contracts.py tests/test_one_stop_frontier_lag_auto_continue.py tests/test_stage4_orchestrator.py`
- `python -m pytest tests/test_stage4_post_processor.py`
- `python -m pytest tests/test_main_a_stage_entry_contracts.py`
- `python -m pytest tests/test_one_stop_frontier_lag_auto_continue.py`
- `python -m pytest tests/test_stage4_orchestrator.py`

## 7. Guardrails

- do not confuse this issue with the separate menu 7 desired Arc-count contract
- do not remove the final return-to-menu pause under `wait_for_menu_return` when addressing this issue
- do not reopen this lane unless the live chain breaks or a fresh run disproves the current contract

## 8. Closure Note

Realized scope:

- this turn patched the remaining menu 7 final-close Stage 4 call in `main_a.py` so all menu 7 Stage 4 entry sites now propagate `skip_pause=True`
- this turn added dedicated regression coverage in:
  - `tests/test_stage4_post_processor.py`
  - `tests/test_main_a_stage_entry_contracts.py`
  - `tests/test_one_stop_frontier_lag_auto_continue.py`
  - `tests/test_stage4_orchestrator.py`
- this turn also added canonical revalidation and execution authority docs for the issue class

Verification summary:

- `python -m py_compile main_a.py tests/test_stage4_post_processor.py tests/test_main_a_stage_entry_contracts.py tests/test_one_stop_frontier_lag_auto_continue.py tests/test_stage4_orchestrator.py`
- `python -m pytest tests/test_stage4_post_processor.py`
- `python -m pytest tests/test_main_a_stage_entry_contracts.py`
- `python -m pytest tests/test_one_stop_frontier_lag_auto_continue.py`
- `python -m pytest tests/test_stage4_orchestrator.py`

Residual risks:

- no fresh terminal smoke was run in this turn, so the operator-visible prompt flow is validated by code-path inspection and regression tests rather than by a new interactive session
- the OPUS source file remains a low-trust historical lead and should not be used directly as execution authority
