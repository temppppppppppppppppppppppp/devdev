<!-- [완료] -->
# Interactive Prompt Contract Refresh Execution SSOT

Date: 2026-03-15
Status: closed
Canonical Path: `docs/2026-03-15/interactive-prompt-contract-refresh-execution-ssot.md`
Temp Mirror Path: `docs/temp/interactive-prompt-contract-refresh-execution-ssot.md`
Commit State:
- Baseline Commit: `083c86d9bbbef7ace001732b2f422eae25bd2038`
- Baseline Dirty Summary: `dirty: 79 tracked, 4 untracked; hotspots: main_a.py, docs/2026-03-14/*, docs/implementation/*, modules/core/*, tests/*`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `later superseded for menu7 arc-count policy by docs/2026-03-15/menu7-desired-arc-input-contract-remediation-execution-ssot.md`
Source Survey Docs:
- `docs/2026-03-15/interactive-prompt-contract-refresh-3pass-audit.md`
Evidence Artifacts:
- `docs/2026-03-15/interactive-prompt-contract-refresh-evidence.txt`
Side-Effect Coverage: covered

## 1. Intent
- Refresh the interactive CLI contract after the fresh `python main_a.py` live run exposed two operator-surface mismatches:
  - menu `7` removed the initial tranche-size choice too aggressively
  - shared prompts are rendered and logged redundantly
- Keep this execution item compact and isolated from unrelated shutdown-race work.

## 2. Baseline Facts
- `main_a.py:4188-4201`
  - menu `7` normal path currently auto-selects `min(remaining_design, 3)` and does not ask the operator for the initial tranche size
- `main_a.py:4467-4475`
  - menu `6` already implements a one-time initial Arc-count prompt with default `3`
- `modules/core/studio_visualizer.py:133-145`
  - `prompt()` logs the prompt and then renders the same prompt again through `console.input(...)`
- `modules/core/services/ui_service.py:187-205`
  - `get_int_input()` records a hidden selection event using the raw prompt text again, which inflates log duplication
- `logs/session_20260315_123149.log:36-38`
  - the genre-choice prompt appears three times with the same message text
- `logs/session_20260315_123149.log:52,54,56`
  - the project-choice prompt appears three times with the same message text
- `docs/2026-03-14/frontier-lag-nonstop-contract-remediation-execution-ssot.md`
  - prior closed policy intentionally removed the menu `7` prompt; this new item supersedes that operator contract for interactive runs

## 3. Scope
Included:
- `main_a.py` Frontier Lag initial operator prompt policy
- `modules/core/studio_visualizer.py` shared prompt rendering behavior
- `modules/core/services/ui_service.py` prompt/selection logging semantics
- targeted tests covering Frontier Lag prompt policy and prompt rendering/logging duplication

Excluded:
- `batch_size_override` harness semantics
- Stage 3 or Stage 4 failure-path prompts
- shutdown race, closed-database writes, or async event-loop teardown
- broader process-runner prompt broker behavior unless required by the local fix

## 4. Pass 1. Inventory Summary
- policy anchors to modify: `3`
  - one Frontier Lag entry path
  - one shared prompt renderer
  - one shared integer-input helper
- live evidence clusters: `2`
  - one menu `7` policy mismatch from the fresh transcript
  - one prompt duplication cluster from the fresh session log
- predecessor contract docs to update or supersede: `1`

## 5. Pass 2. Semantic Classification
- Class A:
  - interactive operator contract refresh for menu `7`
- Class B:
  - shared prompt rendering/logging normalization
- Class C:
  - side-effect-bearing sink changes on session logs and `ui_events`

## 6. Side-Effect Map
- file writes / artifacts:
  - session log line counts and prompt text patterns will change
- DB / schema / transaction boundaries:
  - no schema change
  - `ui_events` payload frequency or message text may change
- JSONL / log / audit sinks:
  - prompt/prompt_response/selection output will be normalized
- console / UI / operator output:
  - primary target; duplicate prompt rendering must be removed
- rollback / recovery / retry:
  - preserve existing failure/exception prompts in Frontier Lag
- cache / global state:
  - not applicable
- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture
- menu `7` operator path:
  - when `batch_size_override` is absent, ask exactly once at Frontier Lag start for the initial tranche size
  - default remains `min(remaining_design, 3)`
  - pressing Enter must keep the default
  - after that first answer, continue without per-tranche re-prompts; keep current auto-shrink-to-remaining behavior
- harness path:
  - if `batch_size_override` is provided, preserve current no-prompt bounded behavior
  - preserve `max_arc_advances` and `wait_for_menu_return` semantics
- shared prompt surface:
  - operator-visible prompt text should render exactly once per interaction
  - machine-readable prompt telemetry may remain, but hidden prompt-response or selection events must not reuse the exact same user-visible prompt text in a way that recreates triple prompt lines in session logs
- predecessor authority:
  - this item supersedes the prior `frontier-lag-nonstop` normal-path contract only for interactive operator behavior; bounded harness seams remain unchanged

## 8. Execution Tranches
1. Reintroduce a one-time initial batch prompt for interactive menu `7`, defaulting to `3` and preserving auto-continue afterward.
2. Normalize shared prompt rendering so `StudioVisualizer.prompt()` no longer double-renders the same prompt on the console.
3. Normalize hidden prompt-response / selection sink messages so session logs do not contain repeated identical prompt strings for a single interaction.
4. Refresh targeted tests and update predecessor docs if the implementation changes the interactive contract text.

## 9. Acceptance Criteria
- Selecting menu `7` interactively asks the initial tranche size exactly once.
- The menu `7` default remains `min(remaining_design, 3)`.
- Pressing Enter on that prompt keeps the default.
- `batch_size_override` continues to bypass the interactive prompt for harnessed or bounded runs.
- Genre/project selection prompts appear once on the console, not twice.
- Session logs no longer show three identical prompt lines for a single genre or project input interaction.
- Stage 3 failure/exception prompts remain intact.

## 10. Verification Plan
- Run targeted Frontier Lag tests and update them to reflect the new one-time interactive prompt rule.
- Add or refresh tests around `StudioVisualizer.prompt()` / `UIService.get_int_input()` so duplicate visible prompt rendering and triple identical log lines regress cleanly.
- Do one fresh local CLI smoke run through:
  - genre selection
  - project selection
  - menu `7` entry
- Confirm:
  - one visible prompt for each selection
  - one initial Frontier Lag batch prompt
  - no re-prompt between successful tranches unless an existing failure path is hit

## 11. Guardrails
- Do not revert to per-tranche approval prompts on menu `7`.
- Do not remove `batch_size_override`, `max_arc_advances`, or `wait_for_menu_return`.
- Do not drop prompt telemetry entirely; normalize it.
- Do not mix the shutdown-race fix into this execution item.

## 12. Temp Queue Notes
- temp status: completed
- cleanup condition:
  - remove the temp mirror after implementation, targeted verification, and canonical closure
- roadmap dependency:
  - none; this is a single-item queue

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run this document through the 3-pass audit and reconfirm at least `95%` confidence against the current workspace state before patching code

## 14. Closure Note
- closure date: `2026-03-15`
- closure status: `closed`
- implementation result:
  - `main_a.py` menu `7` now asks the initial tranche size exactly once for interactive runs and keeps default `min(remaining_design, 3)`
  - `batch_size_override` still bypasses the interactive prompt for bounded harness runs
  - `StudioVisualizer.prompt()` no longer double-renders the same prompt on the console
  - `UIService.get_int_input()` now records hidden selection telemetry without repeating the raw prompt text as the selection message
- verification evidence:
  - `python -m py_compile main_a.py modules/core/studio_visualizer.py modules/core/services/ui_service.py`
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_studio_visualizer.py tests/test_ui_service.py -q` -> `17 passed`
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_one_stop_frontier_lag_auto_continue.py tests/test_auto_frontier_lag_harness.py -q` -> `13 passed`
- residual risk:
  - a fresh full CLI live smoke run was not repeated in this turn
  - shutdown-race behavior observed in the earlier fresh run remains outside this closed item
- authority note:
  - superseded for menu `7` Arc-count interaction policy by `docs/2026-03-15/menu7-desired-arc-input-contract-remediation-execution-ssot.md`
  - prompt dedup and hidden telemetry normalization results recorded here remain valid predecessor evidence for later prompt-surface work
