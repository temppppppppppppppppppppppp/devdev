# Stage3 Polaris Decision Kernel Queue Semantics Operating Note

- Date: 2026-04-13
- Status: draft-live-run-pending
- Scope: long-horizon Stage3 future-state anchor covering decision authority, structured repair locality, and active-queue semantics on current `main`
- Mode: architecture-note support during live-merge; this note fixes the target state but does not claim that the current live run is already resolved
- Canonical Path: `docs/2026-04-13/stage3-decision-kernel-queue-semantics-operating-note.md`
- Baseline Commit: `347acac374f7246cca433d4be9c7466e802c9883`
- Baseline Dirty Summary: `dirty: active live-run artifacts plus current Stage3 runtime/tests/docs patches already present in worktree`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none at note capture; live-run evidence is still moving and must be merged later`
- Confidence: `96% for the target-state note itself; not a claim about current runtime closure`

## Purpose

This note fixes the Stage3-local `Polaris` child target state that future Stage3 work should converge toward.

Parent cross-stage anchor:

- [stage0-stage2-stage3-stage4-cross-stage-north-star-operating-note.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-13/stage0-stage2-stage3-stage4-cross-stage-north-star-operating-note.md:1)

It is intentionally stronger than a watchlist and narrower than an execution SSOT:

- it defines the desired architecture
- it names the controlled migration path
- it states which losses are acceptable during refactor
- it does not yet open a temp-queue execution mirror while the current live run is still in flight

Companion draft:

- [stage3-long-horizon-refactor-and-queue-hygiene-live-run-watchlist.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-13/stage3-long-horizon-refactor-and-queue-hygiene-live-run-watchlist.md:1)

## Why This Needs To Exist Now

The current system has improved tactically, but the underlying control plane is still layered in a way that makes closure expensive to reason about:

- validator mutates apparently successful compare results into repair-bearing verdicts: [unified_blueprint_validator.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py:420), [unified_blueprint_validator.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py:468)
- runtime still owns quality-gate, retry, fallback, and acceptance policy: [three_phase_blueprint_runtime.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py:1056), [three_phase_blueprint_runtime.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py:1724), [three_phase_blueprint_runtime.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py:2260)
- orchestrator still remaps the result for persistence and dashboard semantics: [stage3_orchestrator.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage3_orchestrator.py:2030), [stage3_orchestrator.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage3_orchestrator.py:2578)
- the path called `inplace` is still whole-blueprint regeneration with preservation merge rather than a true field-targeted repair contract: [three_phase_blueprint_generator.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_generator.py:158), [three_phase_blueprint_generator.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_generator.py:173), [three_phase_blueprint_generator.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_generator.py:231)
- queue semantics still visually mix active work, proof debt, and historical backing inside the same active order: [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md:66), [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md:83)

The right long-term move is not “more patch logic.”

The right move is “one decision authority, one repair contract, one credible queue.”

## Non-Negotiable Future State

When this direction is realized, Stage3 should behave like this:

1. validator emits facts and issue families, not final operational policy
2. one policy kernel decides the outcome and next action
3. runtime executes that action without reinterpretation
4. persistence and dashboard surfaces project the same authoritative decision
5. local repairs are represented as explicit target paths, not whole-blueprint rewrites
6. `docs/temp/` shows active queue only, while historical proof remains canonical but non-active

## Architecture Target

### 1. Four-layer decision pipeline

Target layering:

- `Fact Layer`
  - owner: validator and bounded prevalidation
  - output: normalized issues, hard/advisory class, locality, evidence, repair affordances
- `Policy Layer`
  - owner: new `Stage3DecisionKernel`
  - output: single authoritative decision report
- `Execution Layer`
  - owner: runtime
  - output: generate / patch / retry / stop according to the decision report
- `Projection Layer`
  - owner: orchestrator and sinks
  - output: persistence payload, dashboard payload, operator summary, queue-facing proof signals

The key contract is that only the policy layer chooses the action.

### 2. Canonical decision object

Target object:

- `Stage3DecisionReport`

Suggested stable fields:

- `semantic_verdict`
  - `pass`, `warning`, `repair_required`, `fail`
- `operational_disposition`
  - `accept`, `accept_warning`, `retry_inplace`, `retry_full`, `terminal_fail`
- `repair_authority`
  - which owner supplied the authoritative scope
- `repair_scope`
  - `none`, `field_patch`, `local_patch`, `full_regenerate`
- `retry_budget_state`
  - remaining attempts, terminality, plateau flags
- `quality_signals`
  - `quality_gate_failed`, `quality_risk`, `revision_required`
- `issue_families`
  - normalized categories with hard/advisory split
- `projection_contract`
  - exact persistence and dashboard mapping

Required rule:

- once this object exists for an attempt, downstream layers may project it but may not reinterpret it into a different action

### 3. Structured repair locality

Target object:

- `Stage3PatchPlan`

Suggested stable fields:

- `target_kind`
  - `field`, `path`, `scene`, `section`, `global`
- `targets`
  - explicit paths such as `ending_state.timeline`
- `repair_mode`
  - `patch_ir`, `local_rewrite`, `full_regenerate`
- `authority_reason`
  - why this scope is authoritative
- `preservation_guard`
  - fields that must not drift
- `success_check`
  - what exact post-patch invariant must pass

Required rule:

- the path currently called `inplace` should eventually become `patch_ir` or be renamed
- a whole-blueprint JSON rewrite may remain as a fallback, but it must stop pretending to be a locality-preserving patch

### 4. Queue target model

Target states:

- `active_patch`
- `proof_pending`
- `deferred_debt`
- `historical_backing`
- `blocked`
- `closed`

Target temp policy:

- `docs/temp/` contains only `active_patch` and `proof_pending`
- `historical_backing` remains in canonical dated docs and roadmap history, but not as active temp mirrors
- `closed` removes temp mirrors

This aligns better with the stronger workspace rule that active temp mirrors represent active queue artifacts: [AGENTS.md](/c:/Users/wjjo/Desktop/글도비/AGENTS.md:184), [AGENTS.md](/c:/Users/wjjo/Desktop/글도비/AGENTS.md:185)

## Controlled Loss Model

This refactor is allowed to cause some bounded loss. Pretending otherwise will only create more hidden debt.

### Acceptable controlled losses

- one-time doc churn as `partially_realized` is split into real operational states
- one-time sink payload churn where legacy flags are normalized under the new decision object
- temporary shadow-mode duplication while old and new decision surfaces coexist
- small proof cadence slowdown during migration if it buys a much clearer closure model

### Not acceptable

- silent loss of operator-visible verdict reasoning
- silent loss of persistence fields already used by proofs or dashboards
- runtime behavior changes without a traceable migration note
- deleting historical backing evidence just to make the queue look shorter
- introducing a new faux-local repair path with a different name but the same whole-blueprint behavior

## Migration Tranches

### Tranche 0. Vocabulary freeze

Goal:

- freeze the target terms before more local fixes accrete around the old language

Deliverables:

- stable definitions for `semantic_verdict`, `operational_disposition`, `repair_scope`, `historical_backing`, and `proof_pending`

### Tranche 1. Decision kernel in shadow mode

Goal:

- compute a `Stage3DecisionReport` alongside the current runtime without changing the live action path yet

Deliverables:

- decision report builder
- parity logging against current runtime decisions
- targeted proof that the report explains current accept/retry/fail outcomes without ambiguity

### Tranche 2. Projection takeover

Goal:

- make runtime, orchestrator, and dashboard consume the same authoritative decision report

Deliverables:

- runtime executes only the chosen disposition
- orchestrator projects only the chosen disposition
- dashboard/persistence read from the same projected contract

### Tranche 3. Structured patch IR activation

Goal:

- replace the faux-inplace lane for bounded local repairs

Deliverables:

- explicit `Stage3PatchPlan`
- patch-target selection from normalized issue families
- field/path-scoped patch execution for locality-safe families
- hard fallback to `full_regenerate` when locality is not trustworthy

### Tranche 4. Queue closure hygiene sweep

Goal:

- make the active queue visually honest

Deliverables:

- status split rollout in roadmap and execution SSOTs
- `docs/temp/` cleanup for historical backing items
- separate historical index or canonical backing references where needed

### Tranche 5. Legacy removal

Goal:

- delete the old multi-owner reinterpretation path after proof is sufficient

Deliverables:

- remove duplicate verdict rewrites
- remove misleading `inplace` naming if it no longer reflects behavior
- close migration-specific compatibility shims

## Activation Gate

This note is authoritative as a future-state anchor, but not yet as an implementation queue item.

It should be promoted into execution only after the current live run reaches a terminal state and the post-run merge audit answers:

1. whether `ep7` creates a truly new Stage3 family or merely strengthens the locality case
2. which bounded parent lane should own the `DecisionKernel` tranche first
3. whether queue-hygiene promotion should be a separate lane or the first child of the same parent

## Practical Use

Until promotion happens, use this note in exactly three ways:

1. reject ad-hoc fixes that deepen multi-owner decision mutation
2. reject new repair logic that still serializes whole-blueprint JSON while claiming locality
3. reject queue wording that keeps historical backing inside the active temp semantics without saying so explicitly

## 3-Pass Audit Notes

Pass 1:

- document type is an operating note, not an execution SSOT
- scope is explicit and bounded to future-state architecture plus queue semantics

Pass 2:

- claims are grounded in current code surfaces, current roadmap semantics, and active governance rules
- no final runtime-closure or queue-closure claim is made

Pass 3:

- the note is actionable because it constrains future design choices and defines migration tranches
- no temp mirror or ClickUp reflection is authorized while the live run is active
