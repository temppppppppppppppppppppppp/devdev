# FrontierLag Nonstop UTF-8 Hygiene Remediation Execution SSOT

Date: 2026-03-15
Status: closed
Canonical Path: `docs/2026-03-15/frontierlag-nonstop-utf8-hygiene-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/frontierlag-nonstop-utf8-hygiene-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `083c86d9`
- Baseline Dirty Summary: `modified=31, deleted=54, untracked=9`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-15/codebase-global-live-merge-00_260315-post-run-merge-audit.md`
- `docs/2026-03-15/frontierlag-nonstop-utf8-hygiene-remediation-3pass-audit.md`
Evidence Artifacts:
- `docs/2026-03-15/frontierlag-nonstop-utf8-hygiene-remediation-evidence.txt`
Side-Effect Coverage: covered

## 1. Intent
- Realign interactive menu `7` with the user-required `무입력 nonstop` contract.
- Repair the UTF-8 hygiene tool so it blocks actual mojibake without breaking valid Korean prompts or crashing in the default Windows PowerShell host.
- Keep this as one compact item because both defects were found in the same fresh live-merge audit and both are self-contained.

## 2. Baseline Facts
- `main_a.py:4197` still asks the operator how many initial arcs/tranches to run.
- `main_a.py:4206` still logs `initial batch_size selected`, so the interaction is part of the normal path.
- `main_a.py:4070` still exposes `batch_size_override`; bounded harnesses depend on that seam.
- The fresh run in `projects/00_260315` proves the current live contract is “ask once, Enter keeps `3`”, not “start immediately with `3`”.
- `scripts/check_utf8_hygiene.py:50` flags any non-ASCII-adjacent `?`, which catches real Korean question prompts.
- `scripts/check_utf8_hygiene.py:177` prints raw findings directly, which crashes on cp949 PowerShell when snippets contain emoji.
- `tests/test_one_stop_frontier_lag_auto_continue.py` and `tests/test_check_utf8_hygiene.py` currently lock the undesired behavior and must be updated.

## 3. Scope
Included:
- `main_a.py`
- `scripts/check_utf8_hygiene.py`
- `tests/test_one_stop_frontier_lag_auto_continue.py`
- `tests/test_auto_frontier_lag_harness.py`
- `tests/test_check_utf8_hygiene.py`
- predecessor docs whose authority must be explicitly superseded in closure notes

Excluded:
- `modules/core/studio_visualizer.py`
- `modules/core/services/ui_service.py`
- shutdown-race / teardown handling
- audit summary or DB sink alignment work
- any new roadmap file

## 4. Pass 1. Inventory Summary
- runtime prompt-policy anchor: `1`
- harness seam to preserve: `1`
- UTF-8 hygiene regex anchor: `1`
- UTF-8 hygiene output-path anchor: `1`
- direct regression files to update: `3`
- predecessor closed execution docs in conflict or partial overlap: `2`

## 5. Pass 2. Semantic Classification
- Class A:
  - interactive runtime contract restoration for menu `7`
- Class B:
  - tooling gate correction for UTF-8 hygiene scanning and CLI emission
- Class C:
  - regression and authority sync so the next live run validates the intended behavior rather than the superseded one

## 6. Side-Effect Map
- file writes / artifacts:
  - no runtime artifact schema changes
  - session log and UI telemetry will lose the initial menu `7` prompt lines on the normal path
- DB / schema / transaction boundaries:
  - not applicable
- JSONL / log / audit sinks:
  - `ui_events.jsonl` and the plain session log will no longer record the normal-path initial FrontierLag prompt
  - UTF-8 hygiene CLI output format may change to a shell-safe form
- console / UI / operator output:
  - primary target; menu `7` must stop waiting for input
  - hygiene CLI must remain legible on Windows shells
- rollback / recovery / retry:
  - keep failure-path prompts and exception handling untouched
- cache / global state:
  - not applicable
- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture
- FrontierLag runtime path:
  - if `batch_size_override` is provided, keep current harness semantics and do not prompt
  - if `batch_size_override` is absent, compute `batch_size = min(remaining_design, 3)` and begin immediately
  - preserve all later failure/abort prompts and tranche auto-shrink behavior
- UTF-8 hygiene path:
  - replace the broad `nonascii_adjacent_question_mark` heuristic with a narrower signal that does not treat normal Korean question prompts as corruption
  - keep the stronger signals such as invalid UTF-8, `U+FFFD`, and explicit mojibake token patterns
  - make CLI emission shell-safe, for example by escaping or backslash-encoding snippets before printing on Windows hosts
- Authority handling:
  - this item supersedes the interactive menu `7` prompt policy in `docs/2026-03-15/interactive-prompt-contract-refresh-execution-ssot.md`
  - it restores the user-facing intention of `docs/2026-03-14/frontier-lag-nonstop-contract-remediation-execution-ssot.md` while preserving the later prompt-dedup fixes

## 8. Execution Tranches
1. Remove the normal-path initial menu `7` prompt and restore immediate default batch `3` behavior for interactive runs.
2. Keep `batch_size_override` and existing harness semantics intact so bounded test flows remain deterministic.
3. Narrow the UTF-8 hygiene detection logic to stop flagging valid Korean `?` prompts.
4. Make UTF-8 hygiene findings emission safe on cp949 PowerShell without hiding actual offending content.
5. Update regression tests and closure notes so they reflect the restored runtime contract and corrected hygiene semantics.

## 9. Acceptance Criteria
- Selecting menu `7` interactively no longer asks for the initial tranche size on the normal path.
- The default interactive batch remains `min(remaining_design, 3)`.
- `batch_size_override` continues to bypass prompting for harnessed runs.
- Existing prompt dedup behavior for visible prompts remains intact.
- `scripts/check_utf8_hygiene.py` no longer reports a legitimate Korean question prompt as `nonascii_adjacent_question_mark`.
- `scripts/check_utf8_hygiene.py` can emit findings on the default Windows PowerShell host without crashing on emoji-bearing snippets.
- Relevant tests reflect the new runtime/tooling behavior.

## 10. Verification Plan
- `python -m py_compile main_a.py scripts/check_utf8_hygiene.py`
- targeted pytest shard:
  - `tests/test_one_stop_frontier_lag_auto_continue.py`
  - `tests/test_auto_frontier_lag_harness.py`
  - `tests/test_check_utf8_hygiene.py`
- bounded live smoke after patch:
  - `python main_a.py`
  - choose latest project folder
  - enter menu `7`
  - confirm immediate start with no initial Enter prompt
- direct CLI smoke for the hygiene tool against representative files containing Korean prompts and emoji-bearing lines

## 11. Guardrails
- Do not reintroduce visible prompt duplication while removing the menu `7` prompt.
- Do not remove Stage 3/Stage 4 failure or exception prompts as part of this item.
- Do not neuter the UTF-8 hygiene tool into a no-op; it still must catch real corruption.
- Do not mix shutdown-race, audit-summary, or DB-sink work into this execution item.

## 12. Temp Queue Notes
- temp status: pending
- cleanup condition:
  - remove the temp mirror after implementation, targeted verification, and canonical closure
- roadmap dependency:
  - none; single-item queue

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run this document through the 3-pass audit and confirm at least `95%` confidence against the current workspace state before patching code from this document

## 14. Closure
Implementation status:
- completed

Verification:
- `python -m py_compile main_a.py scripts/check_utf8_hygiene.py tests/test_one_stop_frontier_lag_auto_continue.py tests/test_check_utf8_hygiene.py`
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_one_stop_frontier_lag_auto_continue.py tests/test_auto_frontier_lag_harness.py tests/test_check_utf8_hygiene.py -q` -> `22 passed`

Delivered behavior:
- interactive menu `7` no longer asks for the initial tranche size on the normal path
- default interactive tranche remains `min(remaining_design, 3)`
- `batch_size_override` still keeps harness runs deterministic and prompt-free
- UTF-8 hygiene no longer flags a legitimate Korean question prompt under the old broad `?` adjacency rule
- UTF-8 hygiene output is backslash-coerced for shell-safe emission when the terminal encoding cannot represent the snippet directly

Authority updates:
- supersedes the menu `7` prompt policy portion of `docs/2026-03-15/interactive-prompt-contract-refresh-execution-ssot.md`
- restores the operator-facing intent of `docs/2026-03-14/frontier-lag-nonstop-contract-remediation-execution-ssot.md`

Residual risk:
- full interactive `python main_a.py` live smoke was not rerun in this closure pass; operator-path behavior is verified by targeted regression tests rather than a fresh manual transcript
