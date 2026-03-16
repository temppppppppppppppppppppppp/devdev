<!-- [완료] -->
# Menu7 Desired Arc Input Contract Remediation Execution SSOT

Date: 2026-03-15
Status: closed
Canonical Path: `docs/2026-03-15/menu7-desired-arc-input-contract-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/menu7-desired-arc-input-contract-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `bbb00a77c7356a32fe6358642cff0d3d445b7e8e`
- Baseline Dirty Summary: `dirty: harness/test edits plus unrelated investment/style/pdf/log artifacts and untracked projects/000/`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `realized in live workspace: menu7 now prompts once for desired Arc total, maps that value to requested_arc_limit, and preserves prompt-free harness bypass semantics`
Source Survey Docs:
- `docs/2026-03-15/menu7-desired-arc-input-contract-remediation-3pass-audit.md`
- `docs/2026-03-15/codebase-global-log-evidence-merged-deep-global-survey.md`
Evidence Artifacts:
- `docs/2026-03-15/menu7-desired-arc-input-contract-remediation-evidence.txt`
Side-Effect Coverage: covered

## 1. Intent
- Let the operator enter the desired Arc count from menu `7`.
- Keep Frontier Lag automatic after that one-time choice.
- If the operator simply presses Enter, accept default `3` immediately and run those `3` Arc nonstop on the normal path.
- Preserve bounded harness behavior and existing failure-path safety prompts.

## 2. Baseline Facts
- `main_a.py:4234-4250`
  - interactive menu `7` now asks exactly once for the desired Arc total through `_get_int_input(...)` with default `min(remaining_design, 3)`
- `main_a.py:4234-4245`
  - the prompted value is stored as `requested_arc_limit`; Enter or `None` falls back to the default without an extra confirmation gate
- `main_a.py:4246-4254` and `main_a.py:4440-4446`
  - internal tranche size remains the default batch, but it is clamped to the remaining requested Arc count so the run stops cleanly at the requested total
- `main_a.py:4227-4233`
  - `batch_size_override` still bypasses the prompt and remains the harness-only seam
- `tests/test_one_stop_frontier_lag_auto_continue.py`
  - interactive normal-path tests now assert exactly one `_get_int_input(...)` call and cover an explicit requested-limit stop case
- `tests/test_auto_frontier_lag_harness.py:246-255`
  - harnessed runs still assert prompt-free behavior when `batch_size_override` is supplied

## 3. Authority And Supersession
- This item supersedes prior menu `7` operator-contract conclusions in:
  - `docs/2026-03-14/frontier-lag-nonstop-contract-remediation-execution-ssot.md`
  - `docs/2026-03-15/interactive-prompt-contract-refresh-execution-ssot.md`
- Supersession scope is narrow:
  - only the operator-facing Arc-count interaction contract for menu `7`
  - not the historical closure evidence, harness seams, prompt dedup behavior, or failure-path guardrails recorded by those predecessor docs

## 4. Scope
Included:
- `main_a.py` menu `7` Arc-count interaction contract
- targeted Frontier Lag regression tests
- harness bypass semantics for `batch_size_override`
- aggregate roadmap and lane-boundary updates needed to keep queue authority coherent

Excluded:
- Stage 3 and Stage 4 generation logic
- per-tranche approval prompts
- shutdown/persistence finalization work
- backend-front connectivity work
- source-text/output encoding lane

## 5. Pass 1. Inventory Summary
- interactive authority sites to govern: `1`
  - menu `7` entry
- reusable internal seams already present: `2`
  - requested total stop via `requested_arc_limit`
  - prompt-free harness bypass via `batch_size_override`
- direct regression surfaces to refresh: `2`
  - Frontier Lag CLI behavior tests
  - bounded harness tests

## 6. Pass 2. Semantic Classification
- Class A:
  - operator-visible menu `7` Arc-count prompt contract
- Class B:
  - internal control mapping between operator-entered desired total and existing requested-limit stop semantics
- Class C:
  - bounded non-interactive harness exemption via `batch_size_override`

## 7. Side-Effect Map
- file writes / artifacts:
  - prompt-contract docs and targeted tests only during realization
- DB / schema / transaction boundaries:
  - none directly
- JSONL / log / audit sinks:
  - operator-visible prompt text and prompt telemetry will change
- console / UI / operator output:
  - direct primary effect
- rollback / recovery / retry:
  - current Stage 3 abort and exception prompts remain intact as safety prompts
- cache / global state:
  - not primary
- bootstrap fallback / config-env mutation:
  - not applicable

## 8. Realization Architecture
- Interactive path:
  - if `batch_size_override` is absent, ask exactly once at menu `7` entry for how many Arc to process in this invocation
  - prompt meaning: total Arc count for this run of menu `7`
  - prompt default: `min(remaining_design, 3)`
  - empty input keeps the default
  - valid range: `1..remaining_design`
  - after the operator enters a value or just presses Enter, begin immediately with no second confirmation gate
- Internal control mapping:
  - the prompted value becomes the interactive `requested_arc_limit`
  - preserve the current automatic Frontier Lag tranche behavior after the prompt
  - pressing Enter means "use 3 right now" rather than "ask again" or "wait for another Enter"
  - internal automatic batch size remains the current auto-selected default, clamped to the requested limit when the requested total is smaller than that default
  - stop must reuse the existing `requested_arc_limit` / `requested_limit_hit` mechanism instead of inventing a second stop authority
- Harness path:
  - if `batch_size_override` is provided, keep current bounded behavior and do not prompt
  - preserve `max_arc_advances` and `wait_for_menu_return` semantics for harnessed callers
- Failure-path behavior:
  - do not remove Stage 3 abort or exception prompts
  - those prompts remain safety prompts and are not part of the normal-path contract

## 9. Execution Tranches
1. Replace the current no-prompt menu `7` normal path with a one-time total-Arc prompt whose default is `3`.
2. Map that prompted value onto the existing requested-limit stop path while preserving current automatic tranche progression.
3. Refresh Frontier Lag regression tests from “zero `_get_int_input` calls” to “exactly one interactive `_get_int_input` call”.
4. Keep bounded harness tests prompt-free when `batch_size_override` is supplied.
5. Refresh roadmap and lane authority so the broad runtime/operator lane no longer owns menu `7` Arc-count semantics.

## 10. Acceptance Criteria
- Interactive menu `7` asks exactly once for the desired Arc total.
- Pressing Enter uses default `3` or the smaller remaining value.
- Pressing Enter does not trigger any extra confirmation prompt before the run starts.
- The run stops once the requested Arc total is reached.
- No per-tranche confirmation prompt appears on the normal path.
- `batch_size_override` still bypasses the prompt.
- Existing failure/abort prompts still behave as safety prompts only.

## 11. Verification Plan
- Update targeted Frontier Lag tests so interactive normal-path assertions change from zero `_get_int_input(...)` calls to exactly one call.
- Keep bounded harness tests asserting prompt-free behavior when `batch_size_override` is supplied.
- Run manual CLI smoke through:
  - genre selection
  - project selection
  - menu `7`
  - enter desired Arc count or just press Enter for default `3`
  - confirm immediate start without extra Enter prompt
  - confirm bounded stop after the requested total
- Run `python -m py_compile` for touched Python files and targeted `pytest` for Frontier Lag and harness surfaces.

## 12. Guardrails
- Do not reinterpret the prompt value as tranche size.
- Do not introduce a second prompt for tranche size.
- Do not reintroduce per-tranche confirmations.
- Do not remove `batch_size_override`, `max_arc_advances`, or `wait_for_menu_return`.
- Do not mix shutdown/persistence or backend-front fixes into this item.

## 13. Temp Queue Notes
- temp status: completed
- cleanup condition: satisfied after canonical status refresh, roadmap refresh, validator pass, and temp mirror removal
- roadmap dependency: closed in `docs/2026-03-15/codebase-global-post-remediation-execution-roadmap.md`

## 14. Validation And Closure Hooks
- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- execution-start rule: re-run this document through the 3-pass audit and reconfirm at least `95%` confidence against the current workspace state before patching code

## 15. Closure Note
- realized scope:
  - `main_a.py` now prompts once at menu `7` entry for the desired Arc total and maps that value to `requested_arc_limit`
  - the interactive path starts immediately after the answer or Enter, without reintroducing per-tranche confirmations
  - `tests/test_one_stop_frontier_lag_auto_continue.py` was updated to reflect one interactive `_get_int_input(...)` call and to cover an interactive requested-limit stop case
- verification summary:
  - `python -m py_compile main_a.py tests/test_one_stop_frontier_lag_auto_continue.py tests/test_auto_frontier_lag_harness.py`
  - `python -m pytest tests/test_one_stop_frontier_lag_auto_continue.py`
  - `python -m pytest tests/test_auto_frontier_lag_harness.py -k frontier`
- residual risks:
  - manual CLI smoke was not run in this turn, so the operator-visible prompt text was verified by code and targeted tests rather than by a fresh terminal session
  - broader prompt-authority cleanup and backend-front/runtime lanes remain separate pending work
- temp cleanup:
  - the temp mirror for this item was removed after the canonical roadmap refresh and strict queue validation pass
