# Interactive Prompt Contract Refresh 3-Pass Audit

Date: 2026-03-15
Status: final
Canonical Path: `docs/2026-03-15/interactive-prompt-contract-refresh-3pass-audit.md`
Commit State:
- Baseline Commit: `083c86d9bbbef7ace001732b2f422eae25bd2038`
- Baseline Dirty Summary: `dirty: 79 tracked, 4 untracked; hotspots: main_a.py, docs/2026-03-14/*, docs/implementation/*, modules/core/*, tests/*`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Evidence Artifacts:
- `docs/2026-03-15/interactive-prompt-contract-refresh-evidence.txt`
Primary References:
- `main_a.py`
- `modules/core/studio_visualizer.py`
- `modules/core/services/ui_service.py`
- `logs/session_20260315_123149.log`
- `docs/2026-03-14/frontier-lag-nonstop-contract-remediation-execution-ssot.md`
Confidence: `97%`

## 1. Intent
- Re-open the interactive operator surface for two fresh live-run findings without inflating into a new global survey.
- Produce one compact execution item for menu `7` initial tranche policy and shared prompt duplication.

## 2. Scope
Included:
- menu `7` Frontier Lag initial interactive policy
- shared prompt rendering and prompt log duplication on the CLI path
- side-effects on session logs and operator event sinks

Excluded:
- Stage 2 shutdown race and closed-database write failures
- encoding/mojibake remediation outside prompt duplication
- broader queue, DB, or roadmap re-open

## 3. Baseline and Predecessor Authority
- The previously closed Frontier Lag SSOT in `docs/2026-03-14/frontier-lag-nonstop-contract-remediation-execution-ssot.md` remains an accurate record of what was implemented.
- It is no longer a sufficient operator-surface authority because the fresh live run shows the removed initial prompt now conflicts with the desired operating pattern.
- No active temp queue exists before this audit; `docs/temp/` only contains `README.md`.

## 4. Pass 1. Structure and Inventory
- Runtime policy anchors inspected: `4`
  - `main_a.py:4188-4201`
  - `main_a.py:4467-4475`
  - `modules/core/studio_visualizer.py:133-145`
  - `modules/core/services/ui_service.py:187-205`
- Live evidence anchors inspected: `2`
  - user-supplied fresh terminal transcript
  - `logs/session_20260315_123149.log:36-38,52,54,56`
- Predecessor docs contradicted or reopened: `1`
  - `docs/2026-03-14/frontier-lag-nonstop-contract-remediation-execution-ssot.md`

Pass 1 result:
- The issue is bounded and execution-doc sized.
- A roadmap is not required because only one new execution item is justified.

## 5. Pass 2. Evidence and Semantic Classification
- Class A. Frontier Lag policy mismatch
  - `main_a.py:4188-4201` now hard-codes auto-selection of `min(remaining_design, 3)` when `batch_size_override` is absent.
  - This matches the earlier closed contract, but conflicts with the fresh operator preference to choose the tranche size once at start.
- Class B. Shared prompt duplication
  - `modules/core/studio_visualizer.py:133-145` prints the same prompt via `log(...)` and `console.input(...)`.
  - `modules/core/services/ui_service.py:187-205` logs the same prompt string again as a hidden selection label.
  - `logs/session_20260315_123149.log:36-38,52,54,56` confirms repeated identical prompt strings in the live session log.
- Class C. Side-effect-bearing collateral
  - Any fix changes console output, session-log shape, operator event stream shape, and related prompt-surface tests.
- Class D. Explicit exclusion
  - The shutdown race seen later in the fresh run is real but orthogonal; bundling it here would over-expand the item.

Pass 2 result:
- Evidence is sufficient to justify a targeted execution SSOT.
- The remediation should be compact but cross-cutting across one menu policy and one shared prompt primitive.

## 6. Pass 3. Execution Shape
- One compact execution SSOT is the correct shape.
- Canonical doc path should live under `docs/2026-03-15/`.
- A temp mirror is justified after this audit because the item is implementation-ready and confidence exceeds `95%`.
- No aggregate roadmap is needed because there will be exactly one active execution mirror.

Execution consequence:
- create `docs/2026-03-15/interactive-prompt-contract-refresh-execution-ssot.md`
- mirror it to `docs/temp/interactive-prompt-contract-refresh-execution-ssot.md`
- treat the new execution item as the only active temp queue artifact

## 7. Side-Effect Audit
- file writes / artifacts:
  - session logs and UI event artifacts will change shape because duplicate prompt text should decrease
- DB / schema / transaction boundaries:
  - no schema change justified
  - `ui_events` content may become less redundant, but persistence contracts should remain intact
- JSONL / log / audit sinks:
  - prompt, prompt_response, and selection sink semantics are directly implicated
- console / UI / operator output:
  - primary affected surface
- rollback / recovery / retry:
  - not applicable for this item
- cache / global state:
  - not applicable
- bootstrap fallback / config-env mutation:
  - not applicable

## 8. Final Audit Decision
- Save as final: yes
- Execution SSOT required: yes
- Temp mirror allowed after this save gate: yes
- Estimated confidence: `97%`

## 9. Open Questions Resolved
- Should this reopen a global survey?
  - no; the scope is too bounded
- Should this create a roadmap?
  - no; only one execution item is justified
- Should the shutdown race be bundled with this item?
  - no; keep it separate to avoid mixing policy/UI work with async shutdown handling
