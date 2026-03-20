# React Migration Test Harness Packaging Execution SSOT

Date: 2026-03-19
Status: active
Canonical Path: `docs/2026-03-19/react-migration-test-harness-packaging-execution-ssot.md`
Temp Mirror Path: `docs/temp/react-migration-test-harness-packaging-execution-ssot.md`
Commit State:
- Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
- Baseline Dirty Summary: `dirty: broad in-flight remediation tree; desktop/runtime/tests/docs all already active`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `same working session; second foundational React lane execution SSOT opened after frontend full survey`
Source Survey Docs:
- `docs/2026-03-19/react-migration-program-charter-3pass-audit.md`
- `docs/2026-03-19/react-migration-full-survey-audit-order.md`
- `docs/2026-03-19/react-migration-frontend-full-survey-3pass-audit.md`
Evidence Artifacts:
- direct live file reading only; no separate evidence txt created yet
Side-Effect Coverage: covered

## 1. Intent

- Define how React migration can evolve desktop packaging, runtime authority, and contract-test gates without breaking shipping reality.
- Lock the packaging/test lane as a prerequisite substrate lane, not a cleanup after panel work.
- Preserve the current source-bundle runtime model until the roadmap authorizes a controlled switch.

## 2. Baseline Facts

- `geuldobi-desktop/package.json` currently pins:
  - `main: "src/main.js"`
  - `type: "commonjs"`
  - `start` and `start:spike` to `electron .`
  - `build` and `build:dir` to workspace-seed staging before `electron-builder --win`
- Current packaging still assumes:
  - `build.files` includes `src/**/*`
  - `extraResources` includes `../dist/backend`, `../dist/engine`, `../python-embed`, `../dist/workspace-seed`
- `desktop-runtime-contract-v1.json` still defines the runtime model as source-bundle-primary with authoritative packaged Electron entry `src/main.js`.
- `surface-containment-contract-v1.json` and shipping/runtime tests still classify `geuldobi-desktop/src/main.js` as live entry and root shims as shadow only.
- `regression-validation-tier-contract-v1.json` and related tests already define an official `contract_safe` gate.

## 3. Scope

Included:

- `geuldobi-desktop/package.json`
- `docs/implementation/desktop-runtime-contract-v1.json`
- `docs/implementation/surface-containment-contract-v1.json`
- `docs/implementation/regression-validation-tier-contract-v1.json`
- `tests/test_desktop_packaging_contract.py`
- `tests/test_desktop_shadow_hygiene.py`
- `tests/test_runtime_authority_contract.py`
- `tests/test_surface_containment_contract.py`
- `tests/test_shipping_reality_live_surface_guide.py`
- `tests/test_desktop_contract_refresh.py`

Excluded:

- preload channel semantics beyond file/path authority
- renderer component decomposition
- React panel implementation itself
- backend packaging beyond the already-declared extra-resources inventory

## 4. Pass 1. Inventory Summary

- Current live shipping model is still `src/`-first, not `dist/renderer`-first.
- Official desktop gate list is currently tied to `package.json` scripts and mirrored by `tests/test_desktop_contract_refresh.py`.
- Packaging/runtime tests already freeze:
  - `main: src/main.js`
  - `src/**/*` packaging
  - source-bundle runtime docs
  - live-vs-shadow path classification
  - shipping guide/runtime authority narrative
- `start:spike` remains the minimum runtime proof path mentioned in live shipping guidance.

## 5. Pass 2. Semantic Classification

- Class A. Runtime authority contracts
  - `desktop-runtime-contract-v1.json`
  - `surface-containment-contract-v1.json`
  - shipping reality/runtime authority tests
- Class B. Packaging shape contracts
  - `package.json`
  - `build.files`
  - `extraResources`
  - workspace-seed staging assumptions
- Class C. Validation gates
  - `package.json` desktop subset test list
  - `regression-validation-tier-contract-v1.json`
  - `contract_safe` and related regression tests

Operational interpretation:

- This lane is the release/governance substrate for React migration.
- React cannot safely introduce a new renderer output path until this lane defines how authority, packaging, and gates move together.

## 6. Side-Effect Map

- file writes / artifacts:
  - `geuldobi-desktop/package.json`
  - runtime/containment contract docs
  - shipping guide references
  - packaging/runtime tests
- DB / schema / transaction boundaries:
  - not applicable
- JSONL / log / audit sinks:
  - not primary for this lane
- console / UI / operator output:
  - `start:spike` runtime behavior
  - installer/package launch expectations
  - operator-visible desktop subset gate reporting
- rollback / recovery / retry:
  - package entry rollback
  - path-authority rollback
  - shipping-guide/runtime-doc rollback
- cache / global state:
  - not primary
- bootstrap fallback / config-env mutation:
  - packaged env names and launch paths remain authority-bearing
  - workspace-seed staging remains part of build semantics

## 7. Realization Architecture

- Keep source-bundle-primary as the live runtime model until the roadmap authorizes a switch.
- If React introduces renderer build output later, it must first coexist with explicit authority docs/tests instead of silently replacing `src/**/*`.
- Package entry, preload authority, and surface-containment docs must move together in one tranche.
- `contract_safe` remains a migration gate, not an optional post-hoc clean check.
- The lane should prefer a dual-layout transition plan over a silent path flip.

## 8. Execution Tranches

1. Contract and gate normalization
   - align package scripts, runtime docs, and contract tests around one explicit migration posture
2. Dual-layout packaging plan
   - define how any future React renderer output coexists with current `src/` authority during hybrid rollout
3. Gate flip authorization
   - only after roadmap approval, convert runtime authority and shipping docs/tests together

## 9. Acceptance Criteria

- `package.json`, runtime contracts, shipping guide, and packaging/runtime tests remain mutually aligned.
- No new renderer output path ships without same-change updates to packaging tests and authority docs.
- `contract_safe` remains explicit during React rollout; it is not silently weakened.
- `start:spike` and the official desktop subset test gate stay documented and reproducible.
- Live-vs-shadow path classification remains unambiguous through hybrid phases.

## 10. Verification Plan

- `python -m pytest tests/test_desktop_packaging_contract.py -q`
- `python -m pytest tests/test_desktop_shadow_hygiene.py -q`
- `python -m pytest tests/test_runtime_authority_contract.py -q`
- `python -m pytest tests/test_surface_containment_contract.py -q`
- `python -m pytest tests/test_shipping_reality_live_surface_guide.py -q`
- `python -m pytest tests/test_desktop_contract_refresh.py -q`
- later realization tranches should also exercise the roadmap-selected runtime smoke path such as `npm run start:spike`

## 11. Guardrails

- Do not ship a new React renderer output directory before packaging docs and tests are updated in the same tranche.
- Do not change `main: src/main.js` or `src/**/*` packaging by implication; any such change must be explicit and contract-backed.
- Do not weaken `contract_safe` to get React moving faster.
- Do not treat shadow-entry cleanup as separate from runtime-authority documentation.
- Do not create a second roadmap for packaging/testing; this lane stays under the single React roadmap.

## 12. Temp Queue Notes

- temp status: pending
- cleanup condition: no temp mirror until React realization queue is activated by the single roadmap
- roadmap dependency: must be ordered by the future canonical React execution roadmap

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## Confidence Gate

Estimated confidence for this execution-SSOT purpose: **96%**

Why this clears the gate:

- live package/build/runtime authority files were read directly
- packaging/runtime/shadow/gate tests were treated as first-class evidence
- the lane boundary is substrate-level and narrow enough to reason about without realization yet
- rollback posture is strongly constrained by current shipping reality

Residual uncertainty:

- the exact dual-layout strategy for future React output is intentionally deferred
- some final gate composition may evolve after lane B and lane C realization details exist
