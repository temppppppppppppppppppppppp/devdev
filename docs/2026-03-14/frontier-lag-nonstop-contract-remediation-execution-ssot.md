# Frontier Lag Nonstop Contract Remediation Execution SSOT

Date: 2026-03-14
Status: closed
Canonical Path: `docs/2026-03-14/frontier-lag-nonstop-contract-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/frontier-lag-nonstop-contract-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `2a4d45a4896282d9cf96e67e8daff9dd0287ef4f`
- Baseline Dirty Summary: `dirty: 7 tracked, 3 untracked; hotspots: docs/implementation/*, 260314-print.txt`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `realized in live workspace with main_a.py normal-path prompt removal and targeted frontier regression updates`
Source Survey Docs:
- `docs/2026-03-14/codebase-global-rol-db-log-frontier-lag-3pass-audit.md`
- `docs/2026-03-14/codebase-global-rol-db-log-frontier-lag-reaudit.md`
Evidence Artifacts:
- `docs/2026-03-14/db-log-frontier-lag-reaudit-prompt-sites.txt`
Side-Effect Coverage: covered
Primary References:
- `260314-print.txt`
- `main_a.py`
- `projects/00_20260314/logs/session_20260314_213845.log`
- `docs/2026-03-14/auto-frontier-lag-n-arc-test-harness-ssot.md`

## 1. Intent
- Align interactive menu `7` with the current operator contract: normal-path non-stop behavior.
- Preserve bounded harness control (`batch_size_override`) and failure-path safety prompts.

## 2. Baseline Facts
- `main_a.py:4186-4193` still asks for the initial Arc count on the normal path.
- `main_a.py:4295` and `main_a.py:4317` still prompt only on Stage 3 failure or exception.
- `main_a.py:4386-4388` still guards the final `[Enter]` wait behind `wait_for_menu_return`.
- `260314-print.txt:255-256` and `session_20260314_213845.log:335-339` confirm that the initial Arc-count prompt fired during the observed run.
- The predecessor harness doc only guarantees that `batch_size_override` and `wait_for_menu_return=False` exist for bounded test runs.

## 3. Scope
Included:
- `main_a.py` Frontier Lag entry flow
- `tests/test_one_stop_frontier_lag_auto_continue.py`
- `tests/test_auto_frontier_lag_harness.py`
- related operator contract docs that mention Frontier Lag semantics

Excluded:
- Stage 3 or Stage 4 generation logic itself
- unrelated One-Stop mode `6`
- harness timeout policy changes

## 4. Pass 1. Inventory Summary
- interactive sites in current Frontier Lag flow: `4`
- normal-path prompt sites to remove: `1`
- failure or exception prompts to preserve: `2`
- menu-return wait gate to preserve: `1`

## 5. Pass 2. Semantic Classification
- Class A:
  - source call sites in `main_a.py`
- Class B:
  - live print/log evidence showing current prompt behavior
- Class C:
  - predecessor harness doc that documents bounded test seams without defining interactive operator policy

## 6. Side-Effect Map
- file writes / artifacts:
  - none directly from the contract change; downstream Stage 2/3/4 artifact writes must remain unchanged
- DB / schema / transaction boundaries:
  - none directly; downstream project DB writes continue as-is
- JSONL / log / audit sinks:
  - operator-visible prompt logs will change because the initial prompt disappears on the normal path
- console / UI / operator output:
  - yes; this is the primary surface being changed
- rollback / recovery / retry:
  - failure and exception prompts remain as safety controls
- cache / global state:
  - not applicable
- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture
- Interactive menu `7` must no longer call `_get_int_input(...)` on the normal path.
- If `batch_size_override` is provided, keep current behavior: clamp it to the remaining design range and log the applied override.
- If `batch_size_override` is absent, compute `batch_size = min(remaining_design, 3)` and proceed immediately after logging the auto-selected default.
- Keep Stage 3 failure and exception prompts intact; those are safety prompts, not normal-path prompts.
- Keep `wait_for_menu_return` semantics intact for harnesses and optional menu-return blocking.
- Update tests and docs so “Frontier Lag non-stop” means no normal-path batch-size question, not “remove all prompts under every failure mode.”

## 8. Execution Tranches
1. Replace the normal-path initial Arc-count prompt with automatic default selection.
2. Refresh Frontier Lag tests to assert zero normal-path `_get_int_input` calls while preserving failure-path prompts.
3. Refresh operator and harness docs so interactive policy and bounded harness seams are explicitly separated.

## 9. Acceptance Criteria
- Selecting menu `7` interactively no longer asks the initial Arc-count question on the normal path.
- The default batch size remains `min(remaining_design, 3)` when no override is provided.
- `batch_size_override` still works for bounded harness runs.
- Failure and exception prompts remain available on Stage 3 error paths.
- Existing batch-boundary auto-continue behavior remains intact.

## 10. Verification Plan
- Run `tests/test_one_stop_frontier_lag_auto_continue.py`.
- Run `tests/test_auto_frontier_lag_harness.py`.
- Re-check prompt-site inventory against `main_a.py` to confirm the normal-path prompt is gone while failure prompts remain.
- Confirm that operator docs no longer imply the older “ask once at start” behavior.

## 11. Guardrails
- Do not remove failure or exception prompts from this execution item.
- Do not change the bounded harness stop-boundary contract.
- Do not change downstream Stage 2/3/4 sequencing or backlog semantics as part of this item.

## 12. Temp Queue Notes
- temp status: completed
- cleanup condition: satisfied on `2026-03-15` after canonical closure and roadmap sync
- roadmap dependency: `docs/2026-03-14/codebase-global-rol-db-log-frontier-lag-execution-roadmap.md`

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run this document through the 3-pass audit and reconfirm 95% confidence against the live workspace before patching code

## 14. Closure Note
- closure date: `2026-03-15`
- closure status: `closed`
- implementation result:
  - `main_a.py` normal path no longer asks the initial Arc-count question and now auto-selects `min(remaining_design, 3)` unless `batch_size_override` is provided
  - Stage 3 abort and exception exits now stop the enclosing Frontier Lag tranche cleanly instead of re-entering the outer loop
- verification evidence:
  - `python -m pytest tests/test_one_stop_frontier_lag_auto_continue.py -q` with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` -> `4 passed`
  - `python -m pytest tests/test_auto_frontier_lag_harness.py -q` with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` -> `9 passed`
  - prompt-site reinspection confirmed the normal-path `_get_int_input(...)` call is gone while Stage 3 failure prompts and `wait_for_menu_return` remain
- residual risk:
  - no active residual risk inside this item
  - earlier low-memory runner stalls were traced to watchdog memory waits and one real Frontier Lag abort-loop bug; the abort-loop bug is fixed and a pytest orphan-cleanup rule was added to workspace governance
