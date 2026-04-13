# Polaris Cross-Stage North Star Operating Note

- Date: 2026-04-13
- Status: draft-live-run-pending
- Scope: long-horizon cross-stage future-state anchor for Stage0, Stage2, Stage3, and Stage4 across contract authority, decision flow, proof flow, and queue semantics on current `main`
- Mode: architecture-note support during live-merge; this note fixes the cross-stage target state without claiming that the active live run is already closed
- Canonical Path: `docs/2026-04-13/stage0-stage2-stage3-stage4-cross-stage-north-star-operating-note.md`
- Baseline Commit: `347acac374f7246cca433d4be9c7466e802c9883`
- Baseline Dirty Summary: `dirty: active live-run artifacts plus current Stage3 runtime/tests/docs patches already present in worktree`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none at note capture; the active run is still mutating evidence and must be merged later`
- Confidence: `96% for the future-state anchor itself; not a claim about current runtime closure`

## Purpose

This note defines the current canonical `Polaris` anchor above the current stage-local notes.

The intended hierarchy is:

1. this document defines the cross-stage spine
2. stage-local north-star notes inherit from this spine
3. execution lanes later realize the spine in bounded tranches

Current child anchor:

- [stage3-decision-kernel-queue-semantics-operating-note.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-13/stage3-decision-kernel-queue-semantics-operating-note.md:1)

Current queue-compaction companion:

- [polaris-queue-compaction-live-run-watchlist.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-13/polaris-queue-compaction-live-run-watchlist.md:1)

Current grounding companion:

- [polaris-cross-stage-grounding-parallel-survey.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-13/polaris-cross-stage-grounding-parallel-survey.md:1)

This note is not an execution SSOT.

This note does not open a `docs/temp/` mirror while the current live run remains active.

## Why The Parent Anchor Is Necessary

The repo already points toward a broader system-level direction:

- queue control matters more than adding broad new features: [clickup-system-development-direction-operating-note.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-10/clickup-system-development-direction-operating-note.md:50)
- the desired near-term wave is proof closure, then contract normalization, then architecture reduction: [clickup-system-development-direction-operating-note.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-10/clickup-system-development-direction-operating-note.md:343)
- the active roadmap is already carrying live Stage0, Stage2, Stage3, and Stage4 lanes at the same time: [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md:66), [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md:71), [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md:78), [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md:79)

If each stage gets its own private “north star,” the system will drift back into local optimization:

- Stage0 will optimize handoff in its own language
- Stage2 will optimize producer truth in its own language
- Stage3 will optimize decision/repair in its own language
- Stage4 will optimize verification/readback in its own language

That would recreate exactly the ambiguity we are trying to retire.

## Non-Negotiable Cross-Stage Future State

When this direction is realized, the pipeline should behave like this:

1. each stage has one clear role and does not silently steal another stage's authority
2. every important decision is represented by a stable shared contract, not reinterpreted ad hoc at each stage boundary
3. proof surfaces tell the same story as runtime surfaces
4. queue status reflects current action load rather than historical memory
5. operator ambiguity per run keeps decreasing, even if the codebase stays large

## Stage Roles

### Stage0: Source-of-Truth Packaging

Stage0 should own:

- upstream source-of-truth declaration
- handoff normalization
- bounded packaging of facts and guidance for downstream stages

Stage0 should not own:

- downstream repair policy
- late proof bookkeeping
- active queue reinterpretation

Desired outcome:

- Stage0 emits a clean, stable handoff packet instead of a loosely implied bag of fields

Grounding:

- the current roadmap already treats Stage0 as a source-of-truth and handoff-normalization family rather than a front proof lane: [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md:78), [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md:79)
- the broader direction note already names `Stage0 handoff normalization` as a core contract-normalization wave: [clickup-system-development-direction-operating-note.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-10/clickup-system-development-direction-operating-note.md:357)
- current code already has concrete Stage0 packet/provenance surfaces in `_stage0_contract`, `opening_bundle_contract`, and `planning_seed_authority`, while the runtime handoff owner remains `db_anchor:bible`: [stage0_handoff.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage0_handoff.py:83), [stage0_opening_contract.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage0_opening_contract.py:223), [stage0_phase0_seed.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage0_phase0_seed.py:307)

### Stage2: Producer Truth and Contract Persistence

Stage2 should own:

- producer-side normalization
- persisted contract truth for downstream stages
- carryover authority and bounded state truth

Stage2 should not own:

- final quality/disposition policy
- downstream verifier semantics

Desired outcome:

- Stage2 becomes the stable producer of normalized state and contract truth, not another place where late-stage policy gets re-decided

Grounding:

- the active roadmap already describes Stage2 as a broader proof-pending normalization lane centered on persistence-authority and carryover truth: [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md:71), [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md:74)
- the broader direction note explicitly points to `Stage2/3/4 contract alignment` as a core epic group: [clickup-system-development-direction-operating-note.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-10/clickup-system-development-direction-operating-note.md:358)
- current code already enforces producer-truth packet merge and carryover persistence, but Polaris should still describe Stage2 as partially structured today because meaningful mission/carryover truth still remains in prose/prompt surfaces: [stage2_contracts.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage2_contracts.py:19), [stage2_finalizer.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage2_finalizer.py:2615), [audit_service.py](/c:/Users/wjjo/Desktop/글도비/modules/core/services/audit_service.py:428)

### Stage3: Decision and Repair Kernel

Stage3 should own:

- semantic evaluation intake from normalized upstream truth
- policy decision about accept/retry/fail
- repair locality planning

Stage3 should not own:

- ad hoc sink-specific reinterpretation after the decision is already made

Desired outcome:

- Stage3 emits one authoritative decision and one authoritative repair plan

Grounding:

- current child anchor: [stage3-decision-kernel-queue-semantics-operating-note.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-13/stage3-decision-kernel-queue-semantics-operating-note.md:43)

### Stage4: Verification, Readback, and Proof Projection

Stage4 should own:

- downstream verification
- readback and repair-contract consumption
- proof-facing and operator-facing projection

Stage4 should not own:

- retroactive semantic authorship of upstream facts
- hidden re-decision of the authoritative Stage3 outcome

Desired outcome:

- Stage4 becomes a clean verifier/projection stage rather than a second semi-authoritative judge

Grounding:

- the active roadmap now describes Stage4 primarily as downstream verifier/bookkeeping near the front of the queue: [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md:68), [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md:69), [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md:72)
- the broader direction note already points to `proof_status`, `runtime_health`, and `control_plane_provenance` as the right operator cockpit surfaces: [clickup-system-development-direction-operating-note.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-10/clickup-system-development-direction-operating-note.md:71), [clickup-system-development-direction-operating-note.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-10/clickup-system-development-direction-operating-note.md:373)
- current code already separates companion proof projections from authoritative sinks: `proof_status`, `runtime_health`, and `gate_repair_summary` are projection builders, while `control_plane_provenance` remains an authoritative sink and `artifact_ladder` behaves as a cross-stage inventory projection rather than a Stage4-only proof surface: [control_plane_contract.py](/c:/Users/wjjo/Desktop/글도비/modules/api/control_plane_contract.py:41), [bridge_server.py](/c:/Users/wjjo/Desktop/글도비/modules/api/bridge_server.py:1591), [bridge_server.py](/c:/Users/wjjo/Desktop/글도비/modules/api/bridge_server.py:2120), [bridge_server.py](/c:/Users/wjjo/Desktop/글도비/modules/api/bridge_server.py:2207), [bridge_server.py](/c:/Users/wjjo/Desktop/글도비/modules/api/bridge_server.py:2567)
- current code is strongest today at Stage4 settlement/persistence plus read-only proof projection; Polaris should not overclaim a fully hard structural verifier until more of the current advisory/reactive repair semantics are retired: [stage4_post_processor.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage4_post_processor.py:1094), [stage4_post_pass_runtime.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage4_post_pass_runtime.py:1160), [stage4_canary_tools.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage4_canary_tools.py:560)

## Shared Cross-Stage Spine

The parent north star needs shared contracts that all four stages can align around.

### 1. `StageContractEnvelope`

Purpose:

- the normalized packet that crosses stage boundaries

Expected use:

- Stage0 authors the envelope shape
- Stage2 enriches and persists its truth-bearing fields
- Stage3 consumes it without ad hoc reinterpretation
- Stage4 reads it back for verification/projection

### 2. `StageDecisionReport`

Purpose:

- the shared decision object family

Expected use:

- Stage3 is the first concrete owner through `Stage3DecisionReport`
- later stages project this object, not rewrite it

### 3. `StageRepairPlan`

Purpose:

- the shared repair/locality contract family

Expected use:

- target paths, locality, fallback mode, preservation guard, success checks

### 4. `StageProofRecord`

Purpose:

- the shared proof-facing record that ties runtime result, sink result, and operator-facing result together

Expected use:

- one proof story across runtime, dashboard, readback, and queue closure

### 5. `ActiveQueueRecord`

Purpose:

- the shared queue-facing classification of what is active, what is proof debt, and what is historical only

Expected use:

- roadmap, temp queue, and ClickUp all mirror the same meaning instead of improvising

Current boundary:

- queue-state v1 can honestly express `historical_backing`, but cannot yet express `proof_pending` or `deferred_debt` as first-class repo-side truth, so low-loss compaction should remove historical backing first and defer richer repo-state compression to a later contract revision: [temp-queue-state-contract-v1.json](/c:/Users/wjjo/Desktop/글도비/docs/implementation/temp-queue-state-contract-v1.json:3), [docs/temp/queue-state.json](/c:/Users/wjjo/Desktop/글도비/docs/temp/queue-state.json:1), [sync_clickup_queue.py](/c:/Users/wjjo/Desktop/글도비/scripts/sync_clickup_queue.py:235)

## Controlled Loss Model

This parent refactor is allowed to cause bounded loss, but the losses must be explicit.

### Acceptable controlled losses

- field and terminology churn as stage-local aliases are normalized under shared cross-stage contracts
- short-term shadow-mode duplication while old and new contracts coexist
- reclassification churn in the roadmap as active/proof/historical states are made explicit
- slower short-term delivery if it materially lowers future operator ambiguity

### Not acceptable

- each stage inventing a new near-equivalent contract name for the same idea
- proof surfaces disagreeing with runtime surfaces without explicit migration notes
- queue cleanup achieved by deleting historical evidence rather than classifying it honestly
- Stage4 or Stage2 silently re-deciding outcomes that should belong to Stage3 policy
- Stage3 keeping faux-local repair behavior under a prettier name

## Migration Waves

### Wave A. Vocabulary Freeze

Goal:

- freeze shared cross-stage names before more local debt accretes

Required outputs:

- stable definitions for `StageContractEnvelope`, `StageDecisionReport`, `StageRepairPlan`, `StageProofRecord`, and `ActiveQueueRecord`

### Wave B. Stage Boundary Freeze

Goal:

- make the role of each stage explicit and stop authority bleed across stages

Required outputs:

- Stage0 packaging authority note
- Stage2 producer-truth authority note
- Stage3 decision/repair authority note
- Stage4 verifier/projection authority note

### Wave C. Stage3 Kernel Realization

Goal:

- realize the first concrete shared decision object at the Stage3 level

Required outputs:

- the Stage3 `DecisionKernel` tranche described in the current child note

### Wave D. Stage0 and Stage2 Envelope Normalization

Goal:

- stabilize the upstream packet that Stage3 and Stage4 consume

Required outputs:

- normalized handoff and carryover contract
- alias retirement for cross-stage vocabulary drift

### Wave E. Stage4 Proof Projection Normalization

Goal:

- make proof/readback surfaces project the same authoritative story as runtime

Required outputs:

- shared proof record
- clearer operator cockpit around `proof_status`, `runtime_health`, `gate_repair_summary`, and `control_plane_provenance`

### Wave F. Queue Closure Hygiene

Goal:

- make the execution queue visually honest and operationally cheap

Required outputs:

- honest active/proof/historical classification
- `docs/temp/` cleanup rule applied consistently
- historical backing retained canonically but removed from active temp semantics

## Relationship To Existing Notes

This is the parent anchor.

The following note is currently the first local child:

- [stage3-decision-kernel-queue-semantics-operating-note.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-13/stage3-decision-kernel-queue-semantics-operating-note.md:1)

The following note is the live-run watchlist that should feed the next merge audit:

- [stage3-long-horizon-refactor-and-queue-hygiene-live-run-watchlist.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-13/stage3-long-horizon-refactor-and-queue-hygiene-live-run-watchlist.md:1)

## Activation Gate

This note becomes execution-relevant only after the current live run reaches a terminal state and a post-run merge audit decides:

1. which wave becomes the first active architecture tranche
2. whether queue-hygiene work should be opened as a sibling or child
3. which existing active lanes can be closed, downgraded to proof debt, or reclassified as historical backing

## Practical Rule Until Promotion

Until this note is promoted into execution:

1. do not approve local stage fixes that deepen cross-stage vocabulary drift
2. do not let a stage-local note contradict this parent spine without an explicit reason
3. do not treat temp-mirror count as active work count unless historical backing has been separated out

## 3-Pass Audit Notes

Pass 1:

- document type is an operating note, not an execution SSOT
- scope explicitly covers Stage0, Stage2, Stage3, and Stage4

Pass 2:

- claims are grounded in current roadmap state, the existing final system-direction note, and the current Stage3 child anchor
- no final closure or implementation claim is made while the live run is active

Pass 3:

- the note is actionable because it fixes the hierarchy, shared contracts, and migration waves for future execution
- no temp mirror or ClickUp reflection is authorized from this draft
