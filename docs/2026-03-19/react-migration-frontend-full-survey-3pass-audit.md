## React Migration Frontend Full Survey 3-Pass Audit

Date: 2026-03-19
Status: final
Canonical Path: `docs/2026-03-19/react-migration-frontend-full-survey-3pass-audit.md`
Commit State:
- Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
- Baseline Dirty Summary: `dirty: broad in-flight remediation tree; desktop/runtime/tests/docs all already active`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `same working session; fresh React survey opened from the React survey-order doc`
Source Governance:
- `AGENTS.md`
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/execution-synthesis-harness.md`
- `docs/implementation/document-3pass-audit-harness.md`
- `docs/implementation/evidence-triangulation-contract.md`
- `docs/implementation/integrity-confidence-scoring-contract.md`
- `docs/implementation/canonical-naming-contract.md`
Source React Program Docs:
- `docs/2026-03-19/react-migration-program-charter-3pass-audit.md`
- `docs/2026-03-19/react-migration-full-survey-audit-order.md`
Source OPUS React Inputs:
- `docs/2026-03-18/OPUS/geuldobi-v2-react-adoption-feasibility-report.md`
- `docs/2026-03-18/OPUS/react 도입/react-adoption-deepdive-full-survey.md`
- `docs/2026-03-18/OPUS/react 도입/react-migration-execution-roadmap.md`
Live Code Basis:
- `geuldobi-desktop/package.json`
- `geuldobi-desktop/src/index.html`
- `geuldobi-desktop/src/main.js`
- `geuldobi-desktop/src/preload.js`
- `geuldobi-desktop/src/desktop_control_plane_contract.js`
Live Contract/Test Basis:
- `docs/implementation/desktop-ipc-surface-contract-v1.json`
- `docs/implementation/desktop-runtime-contract-v1.json`
- `docs/implementation/regression-validation-tier-contract-v1.json`
- `docs/implementation/surface-containment-contract-v1.json`
- `docs/implementation/api-contract-v1.yaml`
- `tests/test_desktop_direct_surface_contract.py`
- `tests/test_desktop_contract_refresh.py`
- `tests/test_desktop_preload_bridge_behavior.js`
- `tests/test_desktop_transport_contract.py`
- `tests/test_desktop_settings_recovery.py`
- `tests/test_desktop_work_guard_template_contract.py`
- `tests/test_desktop_packaging_contract.py`
- `tests/test_desktop_shadow_hygiene.py`
- `tests/test_runtime_authority_contract.py`
- `tests/test_shipping_reality_live_surface_guide.py`
- `tests/test_surface_containment_contract.py`
- `tests/test_regression_validation_tier_contract.py`
- `tests/test_splash_runtime_behavior.js`
- `tests/test_bridge_quality_summary.py`
- `tests/test_quality_regression.py`
Related Status Docs:
- `docs/2026-03-19/opus-remaining-high-roi-screening-3pass-audit.md`
- `docs/2026-03-19/opus-modification-current-status-3pass-audit.md`
Temp Queue State:
- `docs/temp/README.md` only
- no active React execution SSOT mirror
- no active React roadmap
Scope:
- current-state full survey of the desktop frontend surfaces relevant to React migration
- classify what is live, what is stale in OPUS, what is easy vs hard, and what must be treated as substrate first
- define the minimum execution-doc split that should follow this survey
- non-goal: author the execution SSOTs
- non-goal: author the roadmap
- non-goal: start code realization

---

## Pass 1. Live Inventory

### 1. Runtime entry and build baseline

Current live desktop runtime baseline:

- package loader: `geuldobi-desktop/package.json`
- Electron entry: `src/main.js`
- preload entry: `src/preload.js`
- main renderer entry: `src/index.html`
- current build/files packaging assumption: `src/**/*`
- current release build prep still depends on workspace-seed staging before `electron-builder --win`
- current packaged extra resources still include:
  - `../dist/backend`
  - `../dist/engine`
  - `../python-embed`
  - `../dist/workspace-seed`
- current desktop package type: `commonjs`
- current desktop dependencies:
  - dev: `electron`, `electron-builder`
  - runtime: `lucide`
- current desktop scripts:
  - `start`
  - `start:spike`
  - `build`
  - `build:dir`
  - `test`

Not present in the live package today:

- React
- ReactDOM
- TypeScript
- Vite
- electron-vite
- zustand
- Vitest

Operational meaning:

- React migration starts from a true no-infra baseline
- there is still no renderer build output directory in the live shipping shape
- packaging still assumes `src/` is the shipped renderer payload
- any OPUS execution text that assumes `src/renderer/`, `out/`, or Vite scripts already exist is forward-looking only

### 2. Current live file sizes

Rechecked at survey start:

- `geuldobi-desktop/src/index.html`: `8,478` lines
- `geuldobi-desktop/src/main.js`: `1,236` lines
- `geuldobi-desktop/src/preload.js`: `91` lines
- `geuldobi-desktop/src/desktop_control_plane_contract.js`: `92` lines

These replace old OPUS counts such as:

- `8,266`
- `1,009`
- `96`

Those old counts are now stale for execution use.

### 3. Renderer hotspot baseline

Current live renderer hotspot counts from `geuldobi-desktop/src/index.html`:

- `innerHTML`: `50`
- `addEventListener`: `63`
- `requestAnimationFrame`: `2`
- `officeState` references: `143`
- `settingsStore` references: `57`
- `qualityInsights` references: `29`
- `qualitySummary` references: `16`
- `new WebSocket`: `1`
- `resolvePrompt` references: `2`
- `safeOps` references: `63`
- `genreModal` references: `20`

Interpretation:

- this renderer is still a direct-DOM ownership surface
- state is still split between one large office-state object and multiple side stores/locals
- there is still one central WebSocket runtime stream in the renderer
- Safe Ops, settings, project, prompt, and quality surfaces are all still strongly coupled into the monolith

### 4. Bridge and shell baseline

Current live bridge/shell facts:

- `ipcMain.handle` occurrences in `geuldobi-desktop/src/main.js`: `23`
- `new BrowserWindow` occurrences: `2`
  - main window
  - splash window
- preload live bridge method references: `25`
- current bridge/project channel references in contract file:
  - `IPC_CHANNELS.bridge.*`: `12`
  - `IPC_CHANNELS.project.*`: `6`

Current contract authority says:

- authoritative Electron entry: `geuldobi-desktop/src/main.js`
- authoritative preload entry: `geuldobi-desktop/src/preload.js`
- active renderer consumers:
  - `geuldobi-desktop/src/index.html`
  - `geuldobi-desktop/src/splash/splash.js`

The React survey must therefore treat splash as a separate consumer and not accidentally fold it into the main renderer migration.

### 5. Network and direct-surface baseline

From `docs/implementation/api-contract-v1.yaml`, the live renderer/network ownership split is:

- approved direct renderer surfaces:
  - splash status poll
  - runtime WebSocket `/events`
  - Gemini API-key validation
- bridge-managed backend routes:
  - `/run`
  - `/run/{run_id}/input`
  - `/stop`
  - `/status`
  - `/quality/summary`
  - `/quality/dashboard`
  - `/quality/review`
  - `/safe-ops/preview`

Operational meaning:

- React migration cannot flatten transport ownership casually
- direct network surfaces and bridge-managed surfaces are already part of a documented contract

### 6. Live test/contract surface inventory

Current tests/contracts still directly assume the current `src/` desktop shape.

Renderer/view-heavy:

- `tests/test_desktop_direct_surface_contract.py`
- `tests/test_desktop_contract_refresh.py`
- `tests/test_desktop_transport_contract.py`
- `tests/test_frontend_stage0_connectivity.py`
- `tests/test_frontend_frontier_lag_wiring.py`
- `tests/test_ui_renderer_sanitization.py`
- `tests/test_desktop_material_offline_behavior.js`
- `tests/test_splash_runtime_behavior.js`

These tests pin:

- direct DOM IDs and inline markup fragments
- splash DOM wiring and fallback-timeout behavior
- raw-HTML office renderer structure
- current CSP/network and direct-surface assumptions inside the shipped renderer files

Preload/bridge-heavy:

- `tests/test_desktop_preload_bridge_behavior.js`
- `tests/test_desktop_work_guard_template_contract.py`
- `tests/test_desktop_shadow_hygiene.py`

These tests/contracts pin:

- the live `window.geuldobiDesktop` method set
- current preload file location and channel names
- active consumer paths in `src/index.html` and `src/splash/splash.js`
- the split between live `src/` authority and shadow entry surfaces

Packaging/runtime-authority-heavy:

- `tests/test_desktop_packaging_contract.py`
- `tests/test_runtime_authority_contract.py`
- `tests/test_shipping_reality_live_surface_guide.py`
- `tests/test_surface_containment_contract.py`

These tests/contracts pin:

- `main: src/main.js`
- `src/**/*` packaging
- current extra-resources shape
- live-vs-shadow entry classification
- the requirement that shipping/runtime docs stay aligned with packaged reality

Operator/control-plane-heavy:

- `tests/test_bridge_quality_summary.py`
- `tests/test_quality_regression.py`
- `tests/test_bridge_server_http_contract.py`
- `tests/test_desktop_settings_recovery.py`
- `tests/test_regression_validation_tier_contract.py`

These tests/contracts pin:

- transport/error UX wording
- settings recovery messaging and renderer resync behavior
- the official `contract_safe` regression gate
- operator/runtime-health payload expectations

Operational meaning:

- React migration is constrained by existing contract tests from day one
- path/layout changes cannot be treated as a later cleanup detail

### 6A. Cross-lane choke points

The strongest cross-lane choke points already visible from live evidence are:

- `docs/implementation/api-contract-v1.yaml`
- `docs/implementation/desktop-ipc-surface-contract-v1.json`
- `docs/implementation/regression-validation-tier-contract-v1.json`
- `tests/test_desktop_direct_surface_contract.py`
- `tests/test_desktop_transport_contract.py`

Operational meaning:

- renderer, bridge, operator UX, and contract-safe gating already overlap
- lane execution docs cannot assume the four lanes are independent from day one
- preload/bridge and test-harness/packaging remain the first substrate docs for a reason

### 7. Side-effect baseline

Relevant side-effect surfaces for React migration are already clear even before implementation:

- file/path authority:
  - `geuldobi-desktop/src/index.html`
  - `geuldobi-desktop/src/main.js`
  - `geuldobi-desktop/src/preload.js`
  - `geuldobi-desktop/package.json`
- build/package outputs:
  - Electron `main`
  - package `files`
  - extra resources
- runtime contracts:
  - desktop IPC surface
  - desktop runtime contract
  - surface containment contract
  - API contract
- operator-visible surfaces:
  - quality dashboard
  - logs
  - run control
  - prompt loop
  - safe-ops preview
- bootstrap/fallback:
  - splash handoff
  - app-ready timing
  - WebSocket reconnect

This is why React migration is a program, not a renderer-only refactor.

---

## Pass 2. Semantic Classification

### 1. What is easiest first

The easiest early migration candidates are the panels that are:

- already data-display heavy
- lower in canvas coupling
- already contract-visible to operators
- already fed through bridge-managed reads

Best early candidates:

- quality/control-plane surfaces
  - quality radar
  - artifact ladder
  - retrieval inspector
  - result summary
  - trend compare
  - failure watch
  - calibration desk
- log/operator surfaces
- settings/project shells that are structurally bounded

Why:

- they already consume summarized state
- they have clearer render boundaries
- they benefit quickly from componentization and testability

### 2. What is hardest last

The hardest late candidates are the surfaces tied to:

- canvas ownership
- animation loops
- office-state mutation density
- WebSocket-lifecycle adjacency
- mission/agent board co-render behavior

Hardest area:

- office/canvas-heavy renderer surfaces

Why:

- `requestAnimationFrame` loop remains live
- `officeState` and mission/agent rendering are still tightly coupled
- canvas, event feed, mission board, and agent board are still operationally entangled

### 3. What is true substrate, not panel work

Some work is not "convert panel X to React."

It is substrate:

- typed preload bridge plan
- authoritative path strategy
- compatibility-shim plan
- packaging/build plan
- contract-test migration plan

These substrate items sit below visible UI conversion and must be surveyed explicitly.

### 4. Live stale-claim ledger for OPUS React docs

Still usable from OPUS:

- `160-220h` as a rough envelope
- strangler migration preference
- risk themes:
  - global state migration
  - DOM ownership collision
  - test rewrite burden
  - freeze window

Must be downgraded or replaced:

- old line counts
- old hardcoded workstation paths
- old package pins
- old direct file-move instructions
- week estimates presented as execution authority

### 5. Contract-preserving migration implication

Because the current test and contract surface is strong, React migration should be treated as:

- contract-preserving first
- panel-replacement second

That means:

- the first execution SSOTs should not be written as "rewrite the UI"
- they should be written as bounded lane docs with path, contract, and rollback rules

---

## Pass 3. Execution Implication

### 1. Recommended execution-doc split

The next React execution docs should be split like this:

1. `react-migration-preload-bridge-execution-ssot.md`
2. `react-migration-test-harness-packaging-execution-ssot.md`
3. `react-migration-control-plane-quality-execution-ssot.md`
4. `react-migration-renderer-state-view-execution-ssot.md`

Reason:

- bridge and packaging constraints are already authority-bearing
- control-plane-quality is the best first user-facing realization lane
- full renderer-state/view decomposition should not go first

### 2. Recommended likely first realized lane

First likely realized lane:

- control-plane-quality

But only after minimum substrate is fixed in docs:

- preload/bridge authority assumptions
- packaging/test migration guardrails

In other words:

- first user-visible React target: lane C
- first foundational execution docs to write: lane B and lane D

### 3. Recommended deferred lane

Latest lane to realize:

- renderer-state-view around office/canvas-heavy surfaces

This should stay late because:

- it carries the strongest ownership-collision risk
- it has the densest state coupling
- it is the easiest place for hybrid-mode regressions to hide

### 4. Rollback stance implied by the survey

The survey strongly implies this rollback posture:

- keep `src/main.js`, `src/preload.js`, and `src/index.html` authoritative until late consolidation
- if new renderer paths appear, they must coexist with explicit authority docs/tests until the roadmap authorizes the switch
- no early deletion of current desktop authority paths

That is not yet an implementation order, but it is the correct default stance for the next SSOTs.

### 5. What this survey does not yet settle

This survey does not yet settle:

- exact package pin set for React toolchain
- exact Vite/electron-vite version policy
- exact compatibility-shim shape
- exact contract-safe gate evolution during hybrid React/legacy coexistence
- exact first component tranche inside the control-plane-quality lane
- final consolidation point for switching runtime authority away from `src/`

Those belong in the lane execution SSOTs and the final roadmap.

### 6. Operational consequence

This survey authorizes the next documentation cycle:

- lane execution SSOTs for:
  - preload-bridge
  - test-harness-packaging
  - control-plane-quality
  - renderer-state-view

It still does not authorize direct React realization work without those SSOTs and a single roadmap.

---

## Confidence Gate

Estimated confidence for this survey purpose: **95%**

Why this clears the gate:

- live renderer, bridge, package, and contract surfaces were read directly
- current test constraints were included as first-class evidence
- stale OPUS claims were bounded and replaced where current live truth differed
- the execution split recommendation follows the current live dependency shape, not OPUS prose alone

Why the score is not higher:

- the exact first component tranche inside lane C still needs lane-level execution design
- version-policy details for React/Vite remain intentionally deferred
