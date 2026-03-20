# React Migration Renderer State View Execution SSOT

Date: 2026-03-19
Status: active
Canonical Path: `docs/2026-03-19/react-migration-renderer-state-view-execution-ssot.md`
Temp Mirror Path: `docs/temp/react-migration-renderer-state-view-execution-ssot.md`
Commit State:
- Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
- Baseline Dirty Summary: `dirty: broad in-flight remediation tree; desktop/runtime/tests/docs all already active`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `same working session; late-stage renderer lane execution SSOT opened after foundational and quality lanes`
Source Survey Docs:
- `docs/2026-03-19/react-migration-program-charter-3pass-audit.md`
- `docs/2026-03-19/react-migration-full-survey-audit-order.md`
- `docs/2026-03-19/react-migration-frontend-full-survey-3pass-audit.md`
- `docs/2026-03-19/react-migration-control-plane-quality-execution-ssot.md`
Evidence Artifacts:
- direct live file reading only; no separate evidence txt created yet
Side-Effect Coverage: covered

## 1. Intent

- Define the late renderer-state-view lane that must absorb the current `index.html` monolith only after the substrate and quality lanes stabilize.
- Make explicit why office/canvas-heavy ownership is not a first React tranche.
- Preserve current shell/run/office/log behavior while shrinking monolithic state and DOM ownership over time.

## 2. Baseline Facts

- `geuldobi-desktop/src/index.html` is currently `8,478` lines and remains the primary renderer monolith.
- The live shell still groups three top-level surfaces:
  - Run
  - Office
  - Log
- Office currently owns:
  - canvas HUD
  - mission cards
  - pipeline strip
  - quality radar and six quality insight panels
  - agent board
  - event feed
  - footer badges
- Overlay roots remain separate and live:
  - settings
  - genre modal and confirm
  - new-project confirm
  - safe-ops confirm
  - prompt dialog
- `initializeWorkspaceLayout()` still reparents existing DOM nodes instead of mounting isolated subapps.
- Global mutable state still includes:
  - `officeState`
  - `agentRuntime`
  - WebSocket/status flags
  - prompt queue/current prompt
  - settings stores
  - `projectConfig`
- Imperative ownership counts remain high:
  - `document.getElementById`: `198`
  - `createElement`: `83`
  - `innerHTML`: `50`
  - `addEventListener`: `63`
  - `requestAnimationFrame`: `2`

## 3. Scope

Included:

- `geuldobi-desktop/src/index.html`
- renderer-global state decomposition around `officeState`, `agentRuntime`, prompt/runtime/project state
- workspace host/layout ownership
- office/canvas-heavy renderer surfaces
- modal/overlay ownership where it touches shell-wide state

Excluded:

- preload/main channel authority redesign
- package/build/runtime authority changes
- dedicated quality/operator islands already covered by the control-plane-quality lane, except where they remain entangled with office ownership
- backend route semantics

## 4. Pass 1. Inventory Summary

- The current shell is not yet a set of isolated apps; it is one reparenting renderer with multiple live regions.
- The office lane mixes:
  - canvas/rAF ownership
  - event feed rebuilds
  - mission and agent rendering
  - quality panels
  - prompt/runtime/project state
- `innerHTML` rebuild hotspots cluster around:
  - quality panels
  - agent board
  - event feed
  - log-like streams
- `addEventListener` and `requestAnimationFrame` ownership are spread across:
  - canvas interaction
  - project/run controls
  - settings and modal flows
  - materials and log filters
  - continuous draw loop

## 5. Pass 2. Semantic Classification

- Class A. Hardest late surfaces
  - office canvas
  - workspace host/layout reparenting
  - global runtime/prompt/project state
  - rAF-driven rendering
- Class B. Medium hybrid surfaces
  - overlays and modal groups
  - shell chrome around run/office/log
  - mission and agent board surfaces
- Class C. Easier subareas already carved out
  - quality/operator panels with dedicated roots
  - some log/operator summaries that can move earlier under other lanes

Operational interpretation:

- This lane is late not because it is unimportant, but because it is the highest ownership-collision risk.
- The first problem here is state and ownership containment, not component styling or JSX conversion.

## 6. Side-Effect Map

- file writes / artifacts:
  - `geuldobi-desktop/src/index.html`
  - later React renderer files or state modules authorized by roadmap
  - renderer/view tests
- DB / schema / transaction boundaries:
  - not primary
- JSONL / log / audit sinks:
  - not primary, but UI may reflect operator/runtime logs
- console / UI / operator output:
  - shell layout
  - office canvas
  - mission/agent board
  - prompt dialog
  - settings/project overlays
- rollback / recovery / retry:
  - shell-level rollback is critical because ownership is still shared
  - hybrid failures can strand live DOM nodes or event handlers
- cache / global state:
  - `officeState`
  - `agentRuntime`
  - prompt queue/current prompt
  - `projectConfig`
  - WebSocket/status flags
- bootstrap fallback / config-env mutation:
  - WebSocket bootstrap
  - shell layout initialization
  - prompt/runtime flow bootstrapping

## 7. Realization Architecture

- Do not attack this lane first.
- Decompose it after preload-bridge, test-harness-packaging, and control-plane-quality have already reduced uncertainty.
- Prioritize state containment and ownership boundaries before any large render-tree rewrite.
- Prefer staged islanding or host-boundary extraction over shell-wide big bang replacement.
- Keep canvas/rAF ownership isolated until there is a clear late-roadmap tranche for it.

## 8. Execution Tranches

1. State containment map
   - isolate and document the current renderer-global state buckets and ownership boundaries
2. Shell/overlay disentanglement
   - separate modal/overlay and non-canvas shell ownership from the deepest office runtime coupling
3. Late office/canvas consolidation
   - only after earlier lanes stabilize, address host reparenting, office canvas, and rAF-heavy surfaces
   - begin with non-React runtime isolation, not direct React ownership of canvas or prompt-adjacent state

## 9. Acceptance Criteria

- Run/Office/Log shell behavior remains intact during hybrid rollout.
- Global prompt/runtime/project flows do not break when any renderer sub-area is migrated.
- Canvas/rAF behavior is not accidentally coupled to early React islands.
- Hybrid ownership remains explicit enough to rollback per tranche.
- No tranche silently depends on changing preload or packaging authority.

## 10. Verification Plan

- `python -m pytest tests/test_desktop_direct_surface_contract.py -q`
- `python -m pytest tests/test_desktop_transport_contract.py -q`
- `python -m pytest tests/test_frontend_stage0_connectivity.py -q`
- `python -m pytest tests/test_frontend_frontier_lag_wiring.py -q`
- `python -m pytest tests/test_ui_renderer_sanitization.py -q`
- `node tests/test_desktop_material_offline_behavior.js`
- `node tests/test_splash_runtime_behavior.js`
- later realization tranches should also re-run the roadmap-selected desktop subset gate and runtime smoke path

## 11. Guardrails

- Do not combine workspace host reparenting changes with major React-root changes in one tranche.
- Do not start this lane before the preload-bridge and packaging/test lanes are stabilized in docs and roadmap order.
- Do not treat quality/operator panel migration success as proof that office/canvas migration is safe.
- Do not weaken prompt/runtime/project flows to force component boundaries early.
- Do not let canvas/rAF ownership become implicit inside generic React lifecycle code without explicit late-lane design.
- Preferred high-risk entry is documented in:
  - `docs/2026-03-20/react-office-animation-runtime-isolation-audit.md`

## 12. Temp Queue Notes

- temp status: pending
- cleanup condition: no temp mirror until React realization queue is activated by the single roadmap
- roadmap dependency: this lane should remain later than preload-bridge, test-harness-packaging, and control-plane-quality

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## Confidence Gate

Estimated confidence for this execution-SSOT purpose: **95%**

Why this clears the gate:

- the live renderer shell, state buckets, and imperative ownership hotspots were rechecked directly
- this lane is clearly later and higher-risk than the other three lanes
- the document stays bounded to execution sequencing and guardrails, not speculative implementation detail

Residual uncertainty:

- the exact split between shell chrome and office-state ownership will need later lane refinement
- some late subareas may merit additional sub-lane docs once the roadmap is written
