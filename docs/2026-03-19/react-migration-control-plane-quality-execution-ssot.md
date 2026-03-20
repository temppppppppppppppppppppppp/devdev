# React Migration Control Plane Quality Execution SSOT

Date: 2026-03-19
Status: active
Canonical Path: `docs/2026-03-19/react-migration-control-plane-quality-execution-ssot.md`
Temp Mirror Path: `docs/temp/react-migration-control-plane-quality-execution-ssot.md`
Commit State:
- Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
- Baseline Dirty Summary: `dirty: broad in-flight remediation tree; desktop/runtime/tests/docs all already active`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `same working session; first user-visible React lane execution SSOT opened after foundational substrate docs`
Source Survey Docs:
- `docs/2026-03-19/react-migration-program-charter-3pass-audit.md`
- `docs/2026-03-19/react-migration-full-survey-audit-order.md`
- `docs/2026-03-19/react-migration-frontend-full-survey-3pass-audit.md`
- `docs/2026-03-19/react-migration-preload-bridge-execution-ssot.md`
- `docs/2026-03-19/react-migration-test-harness-packaging-execution-ssot.md`
Evidence Artifacts:
- direct live file reading only; no separate evidence txt created yet
Side-Effect Coverage: covered

## 1. Intent

- Define the first user-visible React realization lane around quality and operator control-plane panels.
- Migrate read-heavy, panelized surfaces before office/canvas-heavy renderer ownership.
- Preserve current bridge-managed reads, operator signal semantics, and runtime-health visibility while improving component boundaries.

## 2. Baseline Facts

- Live quality/operator panel roots already exist inside `geuldobi-desktop/src/index.html`:
  - `qualityRadar`
  - `artifactLadderPanel`
  - `retrievalInspectorPanel`
  - `resultSummaryPanel`
  - `trendPanel`
  - `failureWatchPanel`
  - `calibrationPanel`
- Quality/operator rendering is currently driven by imperative functions:
  - `renderSafeOpsPreview()`
  - `renderArtifactLadder()`
  - `renderRetrievalInspector()`
  - `renderQualityRadar()`
  - `renderResultSummary()`
  - `renderTrendCompare()`
  - `renderFailureWatch()`
  - `renderCalibrationDesk()`
- These panels already consume summarized state through `officeState.qualityInsights` and `officeState.qualitySummary`.
- Current contract/test evidence already pins:
  - `/quality/summary`
  - `/quality/dashboard`
  - `/quality/review`
  - `/safe-ops/preview`
  - `runtime_health`
  - `proof_status`
  - `quality_signal_snapshot`
  - `persistence_health`
  - `contract_safe`

## 3. Scope

Included:

- quality/operator panels in `geuldobi-desktop/src/index.html`
- bridge-managed quality reads and operator writes that back those panels
- `tests/test_bridge_quality_summary.py`
- `tests/test_quality_regression.py`
- `tests/test_bridge_server_http_contract.py`
- `tests/test_regression_validation_tier_contract.py`

Excluded:

- office canvas / agent board / mission board ownership
- global workspace layout rewrite in `initializeWorkspaceLayout()`
- preload channel redesign
- package/build authority changes
- raw log stream and prompt modal ownership beyond what is needed to keep operator panels coherent

## 4. Pass 1. Inventory Summary

- The quality lane already has dedicated DOM roots and one dominant render function per panel.
- The current read path is bridge-managed, not ad-hoc direct fetch for most quality panels.
- Operator signal surfaces already expose:
  - quality radar summary
  - artifact ladder and next action hints
  - retrieval warning/observation summaries
  - result headline and rationale
  - trend comparison
  - failure pattern watch
  - calibration and operator review tools
- Runtime and regression tests already inspect the same semantic payloads that the UI shows.

## 5. Pass 2. Semantic Classification

- Class A. Best early React-island candidates
  - `qualityRadar`
  - `artifactLadderPanel`
  - `retrievalInspectorPanel`
  - `resultSummaryPanel`
  - `trendPanel`
  - `failureWatchPanel`
  - `calibrationPanel`
- Class B. Nearby but still hybrid-bound surfaces
  - safe-ops preview
  - operator settings/review actions
  - log/operator shell chrome around the panels
- Class C. Deferred surfaces
  - office canvas
  - rAF-driven areas
  - mission/agent board and broader workspace host reparenting

Operational interpretation:

- This lane is the best first React island because the panel roots already exist and the data is already summarized.
- It should still remain contract-preserving: panel replacement first, not transport or runtime-authority redesign.

## 6. Side-Effect Map

- file writes / artifacts:
  - `geuldobi-desktop/src/index.html`
  - later React renderer files or component roots authorized by roadmap
  - quality/operator test files
- DB / schema / transaction boundaries:
  - not primary in this lane
- JSONL / log / audit sinks:
  - quality metrics
  - soft failure surfacing
  - quality review persistence
- console / UI / operator output:
  - quality dashboard
  - runtime health
  - proof status
  - persistence health
  - calibration/operator notes
- rollback / recovery / retry:
  - panels must be removable without breaking the legacy shell
  - operator actions must still degrade visibly if a React island is disabled
- cache / global state:
  - `officeState.qualityInsights`
  - `officeState.qualitySummary`
  - project selection/config state that scopes panel content
- bootstrap fallback / config-env mutation:
  - not primary
  - this lane should not mutate package/env/bootstrap ownership

## 7. Realization Architecture

- Treat each quality/operator panel as a React island candidate, not the whole shell.
- Keep the current bridge-managed quality data sources and operator write paths as-is at first.
- Feed React islands from a compatibility adapter over existing `officeState` and bridge reads before attempting larger state rewrites.
- Preserve current DOM anchors until the roadmap explicitly authorizes a different mounting strategy.
- Keep `initializeWorkspaceLayout()` and workspace reparenting out of the first tranche.

## 8. Execution Tranches

1. Read-only quality island tranche
   - migrate the radar/summary/trend-style panels first while preserving the same DOM anchors and data contract
2. Interactive operator tranche
   - migrate calibration/review/safe-ops-adjacent panels that include operator actions
3. Shell integration tranche
   - only after the first two tranches stabilize, clean up hybrid render ownership around the quality lane

## 9. Acceptance Criteria

- The quality/operator panels continue to show the same semantic payloads:
  - `runtime_health`
  - `proof_status`
  - `quality_signal_snapshot`
  - `persistence_health`
- `/quality/summary`, `/quality/dashboard`, `/quality/review`, and `/safe-ops/preview` remain contract-compatible.
- `contract_safe` remains explicit and observable during hybrid rollout.
- A failed or disabled React island must not blank the entire office shell.
- Legacy and React render ownership for this lane remains clear enough to rollback panel-by-panel.

## 10. Verification Plan

- `python -m pytest tests/test_bridge_quality_summary.py -q`
- `python -m pytest tests/test_quality_regression.py -q`
- `python -m pytest tests/test_bridge_server_http_contract.py -q`
- `python -m pytest tests/test_regression_validation_tier_contract.py -q`
- later realization tranches should also re-run the roadmap-selected desktop subset gate and user-visible runtime smoke path

## 11. Guardrails

- Do not start by rewriting the entire office shell.
- Do not move quality/operator data fetches off the current bridge-managed contract in the first tranche.
- Do not hide `runtime_health` or `persistence_health` regressions behind prettier UI.
- Do not let React island mounting depend on canvas/rAF ownership stabilization.
- Do not delete the legacy panel roots until the roadmap explicitly authorizes consolidation.

## 12. Temp Queue Notes

- temp status: pending
- cleanup condition: no temp mirror until React realization queue is activated by the single roadmap
- roadmap dependency: must be ordered after preload-bridge and test-harness-packaging substrate work

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## Confidence Gate

Estimated confidence for this execution-SSOT purpose: **95%**

Why this clears the gate:

- the panel roots and render functions were read directly from the live renderer
- the lane already has strong contract/test evidence for its data semantics
- the user-visible migration target is bounded and more isolated than office/canvas ownership

Residual uncertainty:

- exact first component tranche inside the lane still needs roadmap sequencing
- some operator-shell chrome may belong partly to this lane and partly to the later renderer-state-view lane
