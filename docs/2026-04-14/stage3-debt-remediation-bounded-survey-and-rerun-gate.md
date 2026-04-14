# Stage3 Debt-Remediation Bounded Survey And Rerun Gate

Date: 2026-04-14
Status: final (3-pass audited; current-head bounded survey)
Canonical Path: `docs/2026-04-14/stage3-debt-remediation-bounded-survey-and-rerun-gate.md`
Commit State:
- Baseline Commit: `81b426a688c2a5b6279d254c7746baac1261235b`
- Baseline Dirty Summary: `dirty: Stage3 runtime/docs/tests plus live 000_260412_a logs/db/artifacts already present in worktree; hotspots: stage3_orchestrator, failure_analyzer, three_phase_blueprint_runtime, blueprint_ensemble, director_ensemble, active Stage3 docs`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-04-13/s2-s3-s4-runtime-improvement-synthesis.md`
- `docs/2026-04-13/0_0-stage3-quality-closure-five-tranche-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
- `docs/2026-04-01/active-temp-execution-roadmap.md`
- `docs/2026-04-14/stage3-runtime-retry-structural-debt-survey.md`
Evidence Artifacts:
- `0_temp.txt`
- `projects/000_260412_a/project_data.db`
- `projects/000_260412_a/logs/session/llm_io.jsonl`
- `projects/000_260412_a/logs/session/ui_events.jsonl`
- `projects/000_260412_a/logs/quality_metrics.jsonl`
- `projects/000_260412_a/logs/pass_rate_monitor.json`
- `projects/000_260412_a/logs/runtime_audit_summary.json`
Side-Effect Coverage: covered (code contract surfaces, runtime/retry surfaces, persistence sinks, queue docs, operator-visible wording)
Confidence: `96%`

## 1. Intent

Re-audit the current `HEAD` Stage3 debt picture without opening a big-bang refactor lane.

This survey exists to answer one operational question only:

- is Stage3 rerun-ready under a debt-first reading, or must the workspace stay on bounded debt-remediation first?

This is a bounded survey, not a global re-audit.

## 2. Scope

Included:

- Stage3 contract surfaces:
  - `modules/core/rationale_contract.py`
  - `modules/core/tactical_intrusion_contract.py`
  - `modules/core/stage3_orchestrator.py`
  - `modules/core/failure_analyzer.py`
- Stage3 runtime/retry structural surfaces:
  - `modules/domain/agents/three_phase_blueprint_runtime.py`
  - `modules/domain/agents/three_phase_blueprint_generator.py`
  - `modules/domain/agents/blueprint_ensemble.py`
  - `modules/domain/agents/director_ensemble.py`
- active Stage3 execution docs and queue controller:
  - `docs/2026-04-01/active-temp-execution-roadmap.md`
  - `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
  - `docs/2026-04-13/0_0-stage3-quality-closure-five-tranche-remediation-execution-ssot.md`
  - `docs/2026-04-13/stage3-cross-pc-proof-rerun-handoff-context.md`

Excluded:

- `Polaris` / `DecisionKernel` migration
- broad owner-surface or module-boundary refactor beyond bounded seam recommendations
- new runtime features
- Stage4 writer-surface redesign
- model/vendor/tier swaps

## 3. Pass 1. Current Inventory

### Contract surface

The current Stage3 decision and sink contract is now materially more normalized than the older rerun-first docs assume:

- shared rationale normalization exists at [rationale_contract.py](/c:/Users/wjjo/Desktop/글도비/modules/core/rationale_contract.py:1)
- Stage3 validate rationale resolves through one shared path at [stage3_orchestrator.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage3_orchestrator.py:122)
- session / stage_attempt / director-selection payload builders now share the same Stage3 rationale family:
  - [stage3_orchestrator.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage3_orchestrator.py:2858)
  - [stage3_orchestrator.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage3_orchestrator.py:2991)
  - [stage3_orchestrator.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage3_orchestrator.py:3107)
- sink alignment now audits `comparison_notes` and structured advisory drift explicitly at [failure_analyzer.py](/c:/Users/wjjo/Desktop/글도비/modules/core/failure_analyzer.py:2369), [failure_analyzer.py](/c:/Users/wjjo/Desktop/글도비/modules/core/failure_analyzer.py:2460)
- tactical intrusion surface parity now runs through one shared collector at [tactical_intrusion_contract.py](/c:/Users/wjjo/Desktop/글도비/modules/core/tactical_intrusion_contract.py:156)

### Runtime / retry surface

The remaining structural pressure is concentrated, not diffuse:

- retry routing remains centralized in [three_phase_blueprint_runtime.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py:2498) (`326 LOC`)
- Stage3 retry feedback shaping is bounded and explicit at [three_phase_blueprint_runtime.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py:960)
- candidate admission, screening, and repair still cohabit one owner at [blueprint_ensemble.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/blueprint_ensemble.py:1004), [blueprint_ensemble.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/blueprint_ensemble.py:1614)
- director compare prompt assembly, gate logic, and sink shaping still cohabit one owner at [director_ensemble.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/director_ensemble.py:1442), [director_ensemble.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/director_ensemble.py:1780), [director_ensemble.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/director_ensemble.py:2083)
- `Stage3Orchestrator` still carries `52` direct methods, and Stage3 sink builders remain separate owner-local families:
  - [stage3_orchestrator.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage3_orchestrator.py:2257) (`121 LOC`)
  - [stage3_orchestrator.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage3_orchestrator.py:2858) (`71 LOC`)
  - [stage3_orchestrator.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage3_orchestrator.py:2991) (`82 LOC`)
  - [stage3_orchestrator.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage3_orchestrator.py:3107) (`110 LOC`)

## 4. Pass 2. Debt Ledger

### 4.1 Resolved contract-debt families

1. Rationale fallback drift is closed.
   - shared helper: [rationale_contract.py](/c:/Users/wjjo/Desktop/글도비/modules/core/rationale_contract.py:1)
   - Stage3 / analyzer consumers: [stage3_orchestrator.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage3_orchestrator.py:122), [failure_analyzer.py](/c:/Users/wjjo/Desktop/글도비/modules/core/failure_analyzer.py:818)

2. Tactical intrusion producer/validator parity is closed for the audited family.
   - shared collector: [tactical_intrusion_contract.py](/c:/Users/wjjo/Desktop/글도비/modules/core/tactical_intrusion_contract.py:156)
   - producer / validator usage: [blueprint_ensemble.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/blueprint_ensemble.py:1121), [unified_blueprint_validator.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py:2444)

3. `comparison_notes` and structured advisory round-trip is now explicit.
   - Stage3 payload surfaces: [stage3_orchestrator.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage3_orchestrator.py:2890), [stage3_orchestrator.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage3_orchestrator.py:3018), [stage3_orchestrator.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage3_orchestrator.py:3168)
   - analyzer mismatch audit: [failure_analyzer.py](/c:/Users/wjjo/Desktop/글도비/modules/core/failure_analyzer.py:2369), [failure_analyzer.py](/c:/Users/wjjo/Desktop/글도비/modules/core/failure_analyzer.py:2863)

4. Retry feedback is now contract-first instead of praise-first.
   - [three_phase_blueprint_runtime.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py:960)

### 4.2 Residual contract debt

1. `selected_candidate_advisory` still carries a dual surface.
   - structured path persists as `selected_candidate_advisory_struct`
   - legacy warning list remains for compatibility at [stage3_orchestrator.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage3_orchestrator.py:3173)
   - analyzer still accepts both shapes at [failure_analyzer.py](/c:/Users/wjjo/Desktop/글도비/modules/core/failure_analyzer.py:1461)
   - this is compatibility debt, not a current rerun blocker

2. `selection_reason` still soft-couples to `comparison_notes`.
   - backfill path still exists at [stage3_orchestrator.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage3_orchestrator.py:125)
   - current tests show it is stable, but it remains soft semantic coupling rather than a hard schema split

### 4.3 Residual structural debt

1. Retry coordination is still over-centralized.
   - primary seam: [three_phase_blueprint_runtime.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py:2498)
   - bounded extraction target: `Stage3RetryCoordinator`

2. Candidate admission still mixes rejection and repair mutation.
   - primary seam: [blueprint_ensemble.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/blueprint_ensemble.py:1614)
   - bounded extraction target: `BlueprintCandidateAdmission`

3. Director compare prompt assembly, gate logic, and sink shaping remain one owner family.
   - primary seams: [director_ensemble.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/director_ensemble.py:1442), [director_ensemble.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/director_ensemble.py:2083)
   - bounded extraction target: `DirectorCompareSurface` / `DirectorDecisionSurfaceBuilder`

### 4.4 Explicit non-goals

- `Polaris` / `DecisionKernel` migration remains out of scope for this lane
- broad Stage3 owner-map rewrite remains out of scope for this lane

## 5. Pass 3. Predictive Estimate

### Contract-debt resolution estimate

Current-head predictive estimate: `93% resolved`

Bounded interpretation:

- `resolved`: the audited rerun-blocking contract families that previously drove false replay, tactical-authority drift, rationale drift, and sink drift are now materially closed on the current branch
- `unresolved`: the remaining contract debt is compatibility / normalization debt, not a newly observed must-before-rerun blocker

Why the estimate is above the gate:

1. no new must-before-rerun contract blocker was found in the bounded current-head survey
2. the remaining unresolved contract debt is residual shape debt, not active go/no-go debt
3. the relevant targeted validations are green on the current workspace

Important caveat:

- `93% resolved` is a predictive contract-debt estimate, not a promise that the next rerun will pass
- runtime can still fail on model behavior, semantic judgment, or non-contract content generation

## 6. Validation Basis

Current-turn validation basis includes:

- `pytest tests/test_stage3_orchestrator.py -q`
- `pytest tests/test_failure_analyzer.py -q`
- `python -m py_compile modules/core/rationale_contract.py modules/core/stage3_orchestrator.py modules/core/failure_analyzer.py`
- `python scripts/ops_validator.py --strict`

The contract-side targeted tests now explicitly keep:

- `comparison_notes` sink parity at [tests/test_failure_analyzer.py](/c:/Users/wjjo/Desktop/글도비/tests/test_failure_analyzer.py:3243)
- structured advisory sink parity at [tests/test_failure_analyzer.py](/c:/Users/wjjo/Desktop/글도비/tests/test_failure_analyzer.py:3244)
- Stage3 payload builder persistence at [tests/test_stage3_orchestrator.py](/c:/Users/wjjo/Desktop/글도비/tests/test_stage3_orchestrator.py:1707)

## 7. Policy Result

### 7.1 Today’s Stage3 rerun gate

Effective today, Stage3 rerun authorization follows this rule:

1. do not auto-authorize or auto-present a fresh Stage3 rerun unless a canonical current-head bounded survey records a predictive contract-debt resolution estimate of at least `90%`
2. if the estimate is below `90%`, the only authorized next step is bounded debt-remediation survey / SSOT refresh
3. even if the estimate is at or above `90%`, rerun is still not automatic; it requires explicit operator re-authorization

### 7.2 Current gate status

- current estimate: `93%`
- current policy state: `threshold met, authorization not yet consumed`

Meaning:

- the current workspace is no longer blocked by the absence of a contract-debt estimate
- the current workspace should also stop describing rerun as the automatic immediate-next action
- rerun is now `operator-gated`, not `queue-forced`

## 8. Execution Consequence

This survey changes current Stage3 execution language as follows:

1. refresh the canonical Stage3 roadmap and parent/child SSOTs so they stop presenting rerun as automatic next action
2. encode today’s rerun gate in the Stage3 queue docs, not in global governance or `Polaris` docs
3. keep the remaining bounded structural seams as optional debt-first work, not as proof that rerun is still forbidden

## 9. 3-Pass Audit Notes

Pass 1:

- scope rechecked against current `HEAD`
- subsystem-specific gate kept out of global governance on purpose

Pass 2:

- contract and structural claims anchored to current code and live Stage3 docs
- queue wording checked against current roadmap and parent/child SSOTs

Pass 3:

- operating consequence reduced to one clear rule: no auto-rerun without explicit `>=90%` canonical estimate, and no automatic rerun even after that floor is met

