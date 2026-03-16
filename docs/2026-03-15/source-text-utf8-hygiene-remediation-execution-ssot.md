<!-- [폐기] -->
# source-text-utf8-hygiene-remediation Execution SSOT

Date: 2026-03-15
Status: superseded-by-source-text-and-runtime-encoding-hygiene
Successor: `docs/2026-03-15/source-text-and-runtime-encoding-hygiene-remediation-execution-ssot.md`
Canonical Path: `docs/2026-03-15/source-text-utf8-hygiene-remediation-execution-ssot.md`
Temp Mirror Path: `none`
Queue Disposition: `historical cleanroom predecessor only; excluded from active queue`
Authority Class: `historical predecessor; do not use as live execution authority`
Commit State:
- Baseline Commit: `d2982aa2790f5ab81529f1e8d87cf6f6006f13c9`
- Baseline Dirty Summary: `dirty: unrelated investment/style/docs/log artifacts already present`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs: `docs/2026-03-15/codebase-global-cleanroom-source-only-3pass-audit.md`; `docs/2026-03-15/codebase-global-cleanroom-source-only-deep-global-survey.md`
Evidence Artifacts: `docs/2026-03-15/codebase-global-cleanroom-source-only-source-inventory.txt`; `docs/2026-03-15/codebase-global-cleanroom-source-only-surface-anchor-inventory.txt`; `docs/2026-03-15/codebase-global-cleanroom-source-only-side-effects.txt`
Side-Effect Coverage: covered

## Historical Supersession Notice

- This cleanroom execution SSOT is retained as a historical predecessor only.
- Live execution authority moved to `docs/2026-03-15/source-text-and-runtime-encoding-hygiene-remediation-execution-ssot.md`, which was later realized and closed under the post-remediation roadmap.
- Any `execution-ready`, temp-path, or roadmap semantics below are historical snapshot content, not current queue state.

## 1. Intent
- Repair real mojibake/corrupted source text in active Python and desktop JS files.
- Restore trust in the touched-file UTF-8 gate by separating true corruption from legitimate Korean question prompts.

## 2. Baseline Facts
- Direct source reads show mojibake-like strings/comments in `main_a.py`, `modules/core/services/ui_service.py`, `modules/core/studio_visualizer.py`, `modules/api/bridge_server.py`, and `geuldobi-desktop/src/main.js`.
- `scripts/check_utf8_hygiene.py` currently flags both real corruption and some legitimate question prompts, so it is not yet a clean authority.
- This area is `P1` because it affects operator-visible strings, transport messages, and edit safety for future work.

## 3. Scope
Included:
- `main_a.py`
- `modules/core/services/ui_service.py`
- `modules/core/studio_visualizer.py`
- `modules/api/bridge_server.py`
- `geuldobi-desktop/src/main.js`
- `scripts/check_utf8_hygiene.py`
- targeted regression tests for the hygiene gate

Excluded:
- historical docs and archived evidence
- runtime logs and DB content
- broad asset-library cleanup

## 4. Pass 1. Inventory Summary
- source-text hygiene issue is present in both Python runtime files and Electron JS surfaces
- the gate already exists, so this is a repair-and-tighten lane, not a greenfield lane
- the blast radius includes prompt strings, warning/error messages, comments, and tooling output

## 5. Pass 2. Semantic Classification
- Class A: real corrupted operator-visible strings
- Class B: corrupted comments/docstrings that degrade maintenance safety
- Class C: hygiene-gate false positives that block clean Korean prompt edits

## 6. Side-Effect Map
- file writes / artifacts:
  - touched source files and gate/tests only
- DB / schema / transaction boundaries:
  - not applicable
- JSONL / log / audit sinks:
  - indirect only through future runtime readability; no direct sink mutation in this lane
- console / UI / operator output:
  - direct impact; corrupted prompt and error text must be repaired
- rollback / recovery / retry:
  - not applicable
- cache / global state:
  - not applicable
- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture
- Define one allowed-path policy:
  - repair source text at the file level
  - keep all new text UTF-8 clean
  - update `check_utf8_hygiene.py` so it catches real corruption without tripping on ordinary Korean question prompts
- Use regression tests as the contract for detector behavior.

## 8. Execution Tranches
1. Enumerate corrupted literals/comments in active runtime and desktop surfaces.
2. Repair source text with stable UTF-8-safe literals and comments.
3. Narrow the hygiene detector and add regression tests for both true-positive and false-positive examples.

## 9. Acceptance Criteria
- No active runtime/control-plane source file in scope contains confirmed mojibake.
- The hygiene checker passes on legitimate Korean prompts that should remain valid.
- The hygiene checker still fails on representative corrupted tokens.

## 10. Verification Plan
- `python scripts/check_utf8_hygiene.py <touched files>`
- targeted pytest for `scripts/check_utf8_hygiene.py`
- `python -m py_compile` for touched Python files

## 11. Guardrails
- Do not silently mass-rewrite unrelated docs or archives in this lane.
- Do not weaken the gate so far that true corruption passes undetected.

## 12. Temp Queue Notes
- temp status: pending
- cleanup condition: remove temp mirror only after realization is validated and closed
- roadmap dependency: first item in `docs/2026-03-15/codebase-global-cleanroom-source-only-execution-roadmap.md`

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document
