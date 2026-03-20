## React Migration Program Charter 3-Pass Audit

Date: 2026-03-19
Status: final
Canonical Path: `docs/2026-03-19/react-migration-program-charter-3pass-audit.md`
Commit State:
- Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
- Baseline Dirty Summary: `dirty: broad in-flight remediation tree; hotspots: geuldobi-desktop/, modules/, tests/, docs/2026-03-19/`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `same working session; charter opened after bounded remediation screening`
Source Governance:
- `AGENTS.md`
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/document-3pass-audit-harness.md`
- `docs/implementation/commit-state-minimal-contract.md`
- `docs/implementation/single-ssot-roadmap-contract.md`
- `docs/implementation/canonical-naming-contract.md`
- `docs/implementation/execution-roadmap-template.md`
Source OPUS React Inputs:
- `docs/2026-03-18/OPUS/geuldobi-v2-react-adoption-feasibility-report.md`
- `docs/2026-03-18/OPUS/react 도입/react-adoption-deepdive-full-survey.md`
- `docs/2026-03-18/OPUS/react 도입/react-migration-execution-roadmap.md`
Current Live Basis:
- `geuldobi-desktop/package.json`
- `geuldobi-desktop/src/index.html`
- `geuldobi-desktop/src/main.js`
- `geuldobi-desktop/src/preload.js`
- `docs/2026-03-19/opus-remaining-high-roi-screening-3pass-audit.md`
- `docs/2026-03-19/opus-modification-current-status-3pass-audit.md`
Temp Queue State:
- `docs/temp/README.md` only
- no active React execution SSOT mirror
- no active roadmap
Scope:
- define the program boundary for React migration as a separate long-term system-track program
- fix the doc set shape, authority chain, lane split, and entry criteria
- non-goal: create the execution roadmap
- non-goal: start code realization
- non-goal: treat OPUS React docs as live execution authority

---

## Pass 1. Program Boundary

### 1. What this document is

This document is the first canonical program charter for React migration.

It is not:

- a bugfix continuation note
- an execution SSOT
- an execution roadmap
- a temp queue artifact

Its only job is to lock the boundary of the program before survey and realization documents branch out.

### 2. Why React is a separate program

The 2026-03-19 bounded remediation stream has already burned down the last clear narrow high-ROI defects that were worth doing before React.

That means React is no longer "the next bugfix."

React is now a separate program because it changes:

- renderer architecture
- build pipeline
- desktop shell loading
- preload and bridge typing strategy
- test surface and packaging expectations

That is materially different from the bounded remediation stream, which mostly dealt with:

- observability
- degraded contracts
- narrow routing/fallback policy
- prompt truncation cleanup
- high-ROI runtime correctness gaps

### 3. Why OPUS React docs are not execution authority

The old OPUS React documents remain useful as survey inputs, but not as governing execution docs.

Why:

- they were written before the current 2026-03-19 remediation stream
- some counts are already stale against the live workspace
- they mix survey, proposal, and execution wording too freely
- they over-specify direct realization steps before a current-state charter and re-audit exist

Operational rule for this program:

- OPUS React docs may be mined for candidate phases, lanes, and risks
- only new 2026-03-19 canonical docs may govern realization

---

## Pass 2. Current-State Basis And Program Shape

### 1. Current live baseline

Current live frontend state, re-checked against workspace code:

- framework: none; still plain Electron + vanilla JS
- bundler: none
- TypeScript: none
- React/Vite/electron-vite/zustand: not installed in `geuldobi-desktop/package.json`
- current main renderer surface still lives in:
  - `geuldobi-desktop/src/index.html`
  - `geuldobi-desktop/src/main.js`
  - `geuldobi-desktop/src/preload.js`

Current live file sizes checked at charter start:

- `geuldobi-desktop/src/index.html`: 8,478 lines
- `geuldobi-desktop/src/main.js`: 1,236 lines
- `geuldobi-desktop/src/preload.js`: 91 lines

This matters because the OPUS React docs still cite earlier counts such as `8,266 / 1,009 / 96`.
Those counts are useful as historical survey evidence, but not as current execution truth.

### 2. Program-level goal

The goal of this program is not "adopt React because React is modern."

The goal is:

- reduce renderer monolith pressure
- create typed boundary surfaces around preload and renderer state
- improve testability and maintainability
- preserve current desktop operational behavior while migrating in bounded lanes

### 3. Non-goals

This program does not, by default, imply:

- immediate big-bang rewrite
- backend rewrite
- desktop shell security model rewrite
- narrative-pipeline logic redesign
- reopening already-closed bounded remediation items

This program also does not assume that React must absorb every surface immediately.
Canvas-heavy or shell-owned surfaces may remain hybrid or later-phase targets if the lane design justifies it.

### 4. Migration method

The approved default method is:

- `strangler-lane migration`

Not approved as default:

- `big bang rewrite`

Reason:

- current renderer is operationally coupled to preload, WebSocket events, and desktop process semantics
- bounded replacement by lane keeps rollback and blame boundaries cleaner
- this matches the current workspace posture, where risk is managed in small audited slices

### 5. Canonical lane split

The initial lane split for this program is:

#### Lane A. Renderer State And View Layer

Surfaces:

- `index.html` renderer monolith
- renderer-local state decomposition
- component boundary planning
- React root and renderer directory topology

Primary outcome:

- renderer surfaces become decomposable without yet changing desktop bridge authority

#### Lane B. Preload And Desktop Bridge Contract

Surfaces:

- `preload.js`
- `desktop_control_plane_contract.js`
- renderer-facing typed bridge contract
- lifecycle/app-ready semantics

Primary outcome:

- renderer migration does not blur desktop shell authority or channel ownership

#### Lane C. Quality Dashboard And Control-Plane UI

Surfaces:

- quality summary/dashboard panels
- logs/control-plane panels
- operator-facing runtime health views

Primary outcome:

- move the most dashboard-like renderer panels first, where state and rendering value is high and canvas coupling is lower

#### Lane D. Test/Harness/Packaging

Surfaces:

- existing desktop contract tests
- new renderer-component tests
- packaging/build contract updates
- build pipeline gates

Primary outcome:

- migration never outruns verifiable contract coverage

### 6. Document-set shape

The approved document shape is:

- `1` program charter
- `n` area execution SSOTs
- `1` master roadmap

That means:

- this charter comes first
- next comes a fresh React full survey / audit-order style doc or equivalent evidence bundle
- then area execution SSOTs for the lanes
- only then a single master roadmap

Roadmap authority rule:

- there must be exactly one canonical React roadmap for the active React bundle
- no per-lane competing roadmaps

### 7. Temp policy

`docs/temp/` is intentionally not used yet.

Reason:

- the program is still in design and survey setup
- no live React execution queue exists yet
- temp mirrors should begin only when area execution SSOTs become active realization items

Operational rule:

- create only canonical dated docs at this stage
- defer temp mirrors until execution queue activation

---

## Pass 3. Operating Consequence And Immediate Next Docs

### 1. Immediate operating consequence

React may proceed, but only as a separate program with its own documentation spine.

The current bounded remediation stream should not be stretched into React execution authority.

### 2. Required next document order

Approved next document order:

1. `react-migration-program-charter-3pass-audit.md`
   - this document
2. `react-migration-full-survey-audit-order.md`
   - current-state re-audit of live frontend surfaces
   - must separate reusable OPUS evidence from stale claims
3. lane execution SSOTs
   - at minimum:
     - renderer-state-view lane
     - preload-bridge lane
     - control-plane-quality lane
     - test-harness-packaging lane
4. `react-migration-execution-roadmap.md`
   - single canonical roadmap only

### 3. Entry criteria before any React realization

Before code realization starts, the React document set must have:

- current-state React survey finalized at 95% confidence or higher
- area execution SSOTs finalized at 95% confidence or higher
- one canonical roadmap
- explicit lane dependency order
- explicit rollback stance per lane
- explicit test gate expectations per lane

### 4. Baseline success criteria for the program

Program-level success means:

- renderer monolith pressure is materially reduced
- preload bridge ownership remains explicit and testable
- migration does not weaken current desktop contract coverage
- packaging/build steps are explicit and reproducible
- lane-by-lane rollback remains possible until late consolidation

It does not require:

- immediate elimination of every vanilla surface
- early removal of canvas-specialized logic
- all-at-once replacement of the desktop UI shell

### 5. Initial risk posture

Known high program risks that must be kept explicit in later docs:

- renderer ownership collisions during hybrid periods
- preload/app-ready timing drift
- WebSocket singleton behavior under React lifecycle
- build/packaging contract drift
- stale contract tests that still assume `src/index.html` as the whole renderer truth

These are survey-order risks, not immediate patch commands.

### 6. Program decision

Decision locked by this charter:

- React migration is approved as a separate program
- default method is strangler-lane, not big bang
- OPUS React docs remain references only
- no temp queue mirror yet
- no roadmap yet
- next artifact is a fresh React survey/audit-order doc

---

## Confidence Gate

Estimated confidence for this charter purpose: **96%**

Why this clears the gate:

- the governance path was re-checked against live harness docs
- current live frontend baseline was re-checked against workspace files, not OPUS counts alone
- the program/document separation rule is bounded and explicit
- non-goals, lane split, and roadmap authority are all stated operationally

Residual uncertainty:

- exact lane boundaries may shift after the fresh React survey
- some OPUS React phase details may still be reusable, but only after re-audit against current live code
