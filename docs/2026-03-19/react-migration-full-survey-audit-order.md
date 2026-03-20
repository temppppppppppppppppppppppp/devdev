## React Migration Full Survey Audit Order

Date: 2026-03-19
Status: final
Canonical Path: `docs/2026-03-19/react-migration-full-survey-audit-order.md`
Commit State:
- Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
- Baseline Dirty Summary: `dirty: broad in-flight remediation tree; desktop/runtime/tests/docs all already active`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `same working session; survey order opened immediately after React program charter`
Source Governance:
- `AGENTS.md`
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/execution-synthesis-harness.md`
- `docs/implementation/document-3pass-audit-harness.md`
- `docs/implementation/evidence-triangulation-contract.md`
- `docs/implementation/canonical-naming-contract.md`
Source Program Doc:
- `docs/2026-03-19/react-migration-program-charter-3pass-audit.md`
Source OPUS React Inputs:
- `docs/2026-03-18/OPUS/geuldobi-v2-react-adoption-feasibility-report.md`
- `docs/2026-03-18/OPUS/react 도입/react-adoption-deepdive-full-survey.md`
- `docs/2026-03-18/OPUS/react 도입/react-migration-execution-roadmap.md`
Current Live Basis:
- `geuldobi-desktop/package.json`
- `geuldobi-desktop/src/index.html`
- `geuldobi-desktop/src/main.js`
- `geuldobi-desktop/src/preload.js`
- `geuldobi-desktop/src/desktop_control_plane_contract.js`
- `tests/test_desktop_direct_surface_contract.py`
- `tests/test_desktop_contract_refresh.py`
- `tests/test_desktop_preload_bridge_behavior.js`
- `tests/test_desktop_transport_contract.py`
- `tests/test_desktop_packaging_contract.py`
- `tests/test_desktop_shadow_hygiene.py`
- `tests/test_bridge_quality_summary.py`
- `tests/test_quality_regression.py`
- `docs/2026-03-19/opus-remaining-high-roi-screening-3pass-audit.md`
Temp Queue State:
- `docs/temp/README.md` only
- no active React execution SSOT mirror
- no active React roadmap
Scope:
- define the fresh live survey order required before any React realization docs are written
- separate current live truth from stale OPUS React assumptions
- fix the lane coverage, evidence classes, and output set for the React survey bundle
- non-goal: create execution SSOTs
- non-goal: create the master roadmap
- non-goal: begin code realization

---

## Pass 1. Fresh Survey Question

This document answers one bounded question:

- what exactly must be re-surveyed, against the live 2026-03-19 workspace, before React execution SSOTs are allowed to exist?

This is a survey order, not a roadmap and not an execution SSOT.

It exists because the OPUS React documents are directionally useful but no longer safe to promote directly into execution authority.

The survey that follows this order must produce:

- one current-state React frontend survey
- then lane execution SSOTs
- then one master roadmap

---

## Pass 2. Live Baseline And Stale-Claim Cleanup

### 1. Current live frontend baseline

Current live React-relevant baseline rechecked from workspace:

- `geuldobi-desktop/package.json`
  - still CommonJS
  - still `main: "src/main.js"`
  - still no React/Vite/TypeScript/electron-vite/zustand dependencies
- `geuldobi-desktop/src/index.html`
  - still the primary renderer monolith
  - currently `8,478` lines
- `geuldobi-desktop/src/main.js`
  - current Electron entry
  - currently `1,236` lines
- `geuldobi-desktop/src/preload.js`
  - current preload bridge
  - currently `91` lines
- `geuldobi-desktop/src/desktop_control_plane_contract.js`
  - current bridge/preload channel contract authority

This means the fresh survey must use live 2026-03-19 counts and paths, not the older OPUS counts.

### 2. OPUS React inputs that remain usable

The old OPUS React docs are still useful for:

- candidate lane split
- broad risk themes
- rough effort envelope
- panel decomposition ideas

The following ideas remain reusable:

- React is a separate program, not the next bugfix
- big bang rewrite is lower priority than lane-by-lane migration
- shared state migration and DOM ownership collisions are top risks
- quality/control-plane panels are better early candidates than canvas-heavy panels

### 3. OPUS React inputs that are stale or must be downgraded

The fresh survey must explicitly downgrade or replace these old OPUS assumptions:

- old file counts such as `8,266 / 1,009 / 96`
- hardcoded workstation paths under another user directory
- package-pin assumptions such as old `Vite 6` guidance
- mixed schedule claims:
  - `5-7주`
  - `6-10주`
  - `4-5.5주`

Operational rule for the new survey:

- keep `160-220h` only as a rough inherited planning envelope
- do not treat any old week estimate as authoritative until lane scopes are recalculated against live code

### 4. Live contract surfaces that the survey cannot ignore

React migration is not only a renderer rewrite.

The fresh survey must include these live contract surfaces:

- renderer path authority
  - current contracts still point to `geuldobi-desktop/src/index.html`
- Electron entry authority
  - current contracts still point to `geuldobi-desktop/src/main.js`
- preload method shape
  - current tests assume the live `window.geuldobiDesktop` surface in `src/preload.js`
- packaging/build shape
  - current contracts still assume `src/**/*` packaging and `src/main.js` entry

If the survey ignores those surfaces, later SSOTs will drift immediately.

---

## Pass 2A. Required Survey Coverage By Lane

The fresh React survey must cover four lanes.

### Lane A. Renderer State And View Layer

Live survey targets:

- `geuldobi-desktop/src/index.html`
- renderer-global state such as `officeState`, `settingsStore`, prompt queue state, WebSocket state
- direct DOM ownership patterns:
  - `innerHTML`
  - `addEventListener`
  - `requestAnimationFrame`
  - modal ownership
  - canvas ownership

Required output from survey:

- renderer surface inventory
- component decomposition candidates
- hybrid-risk map
- renderer-first tranches

### Lane B. Preload And Desktop Bridge Contract

Live survey targets:

- `geuldobi-desktop/src/preload.js`
- `geuldobi-desktop/src/desktop_control_plane_contract.js`
- `geuldobi-desktop/src/main.js`

Required focus:

- preload method inventory
- channel authority and ownership
- app-ready lifecycle timing
- run/stop/status and prompt-resolve flows
- settings/project/work-guard bridge surface

Required output from survey:

- typed-bridge migration map
- preload/renderer boundary risks
- main/preload changes that are unavoidable vs deferrable

### Lane C. Control-Plane And Quality UI

Live survey targets:

- quality dashboard surfaces in `index.html`
- control-plane panels
- run panel
- log panel
- operator signal views

Required focus:

- panels with high rendering value and lower canvas coupling
- panels already tied to runtime-health, quality-summary, and operator signals
- places where React gives immediate maintainability/testability return

Required output from survey:

- early-migration candidate list
- panel dependency graph
- what can move before office canvas

### Lane D. Test/Harness/Packaging

Live survey targets:

- desktop contract tests
- preload bridge behavior tests
- runtime authority tests
- packaging/build contract tests
- shipping guide / authority guide dependencies

Required focus:

- which tests assume direct `src/` path truth
- which tests parse `index.html` directly
- which tests enforce current packaging shape
- what must be rewritten vs preserved as contract anchors

Required output from survey:

- test migration map
- packaging/build migration guard list
- rollout gates that block lane realization

---

## Pass 2B. Test And Contract Surface Inventory

The fresh survey must treat the current tests as live authority, not as cleanup afterthought.

### 1. Renderer/View-dependent tests

These tests directly read `geuldobi-desktop/src/index.html` and therefore constrain lane A:

- `tests/test_desktop_direct_surface_contract.py`
- `tests/test_desktop_contract_refresh.py`
- `tests/test_desktop_transport_contract.py`
- `tests/test_frontend_stage0_connectivity.py`
- `tests/test_frontend_frontier_lag_wiring.py`
- `tests/test_ui_renderer_sanitization.py`
- `tests/test_desktop_material_offline_behavior.js`

### 2. Preload/Bridge-dependent tests

These tests constrain lane B:

- `tests/test_desktop_preload_bridge_behavior.js`
- `tests/test_desktop_work_guard_template_contract.py`
- `tests/test_desktop_direct_surface_contract.py`
- `tests/test_desktop_shadow_hygiene.py`

### 3. Control-plane/quality-facing tests

These tests constrain lane C:

- `tests/test_bridge_quality_summary.py`
- `tests/test_quality_regression.py`
- `tests/test_bridge_server_http_contract.py`

### 4. Packaging/runtime-authority tests

These tests constrain lane D:

- `tests/test_desktop_packaging_contract.py`
- `tests/test_runtime_authority_contract.py`
- `tests/test_shipping_reality_live_surface_guide.py`
- `tests/test_surface_containment_contract.py`
- `tests/test_desktop_shadow_hygiene.py`

Survey consequence:

- React migration must be surveyed as a contract-preserving program
- the tests are not merely post-hoc verification; they define live migration constraints

---

## Pass 3. Ordered Survey Outputs And Acceptance Gates

### 1. Required next canonical outputs

After this survey order, the next outputs must be:

1. one fresh React frontend current-state survey
2. lane execution SSOTs
   - renderer-state-view
   - preload-bridge
   - control-plane-quality
   - test-harness-packaging
3. one single canonical React execution roadmap

No temp mirror should exist before step 2.

### 2. Minimum evidence classes required in the fresh survey

The fresh survey should meet at least these evidence minima:

- class A: direct live-code reading
- class B: structured inventory/search evidence
- class C: test or verification surfaces
- class D: contract/config authority
- class E: OPUS/governance lineage only as supporting evidence

Critical claims that must not be single-sourced:

- renderer authority claims
- preload ownership claims
- packaging/build migration claims
- lane dependency claims

### 3. Survey completion gates

The fresh React survey is only complete when it provides:

- live counts and paths, not inherited OPUS numbers
- stale-claim ledger for reused OPUS material
- lane-specific risk inventory
- side-effect map for:
  - file paths
  - packaging/build output
  - bridge contracts
  - operator-visible UI/runtime health
- test migration dependency map
- recommendation of first execution lane

### 4. Initial recommendation for likely first execution lane

The fresh survey should begin with a bias, not a command:

- likely earliest lane: control-plane-quality
- likely latest lane: office/canvas-heavy renderer surfaces

Why this is only a bias:

- the current survey still must prove the dependency graph
- preload/main changes might pull some bridge substrate work earlier than expected

### 5. Explicit non-goals for the fresh survey

The fresh survey must not:

- output a second roadmap
- silently adopt old OPUS week estimates as current authority
- assume `src/renderer/` or Vite paths already exist
- assume packaging can change before test/harness implications are mapped
- over-specify implementation steps before area execution SSOTs exist

### 6. Operational consequence

This document authorizes the next React document, and only that:

- `react-migration-frontend-full-survey-3pass-audit.md`
  or equivalent current-state React survey doc with the same scope and role

It does not authorize realization yet.

---

## Confidence Gate

Estimated confidence for this survey-order purpose: **96%**

Why this clears the gate:

- live desktop entry, preload, contract, packaging, and renderer surfaces were rechecked directly
- current test surface was rechecked directly instead of inferred from OPUS only
- stale OPUS claims were bounded explicitly rather than discarded silently
- output sequence is consistent with the React program charter and single-roadmap rule

Residual uncertainty:

- exact first execution lane still needs the fresh survey to score dependency weight
- some control-plane subpanels may split differently once renderer decomposition is done in detail
