# Active Temp Execution Roadmap

Date: 2026-04-01
Status: active (3-pass audited, single-episode Stage34 demo utility code-landed; Stage4 consumer-contract aggregate still active)
Canonical Path: `docs/2026-04-01/active-temp-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Baseline Commit: `fd1707372bd7eb8ad23a5d4506ef556e3f72cc51`
Baseline Dirty Summary: `dirty: 0_0 runtime logs/db/artifacts active; legacy temp queue mirrors present; 2026-03-31 0_0 survey docs untracked`
Resume Commit: `c32717ffc511389636c65edf2845bef6113b97c3`
Resume Drift Summary: `operator-directed demo prep added a single-episode Stage34 runner ahead of broader closure work; aggregate Stage4 consumer stack remains active underneath`
Supersedes:
- `docs/2026-03-31/active-temp-execution-roadmap.md`

Queue Snapshot:
- `docs/temp/0_0-stage34-ep2-single-episode-demo-canary-execution-ssot.md`
- `docs/temp/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
- `docs/temp/0_0-stage4-flashback-continuity-localfix-remediation-execution-ssot.md`
- `docs/temp/0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation-execution-ssot.md`
- `docs/temp/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md`
- `docs/temp/0_0-stage4-post-select-continuity-contract-normalization-remediation-execution-ssot.md`
- `docs/temp/0_0-stage4-fixpack-finalization-remediation-execution-ssot.md`
- `docs/temp/0_0-stage4-canonical-entity-postselect-remediation-execution-ssot.md`
- `docs/temp/0_0-stage4-ep2-advisory-escalation-loop-remediation-execution-ssot.md`
- `docs/temp/0_0-stage4-repair-contract-normalization-remediation-execution-ssot.md`
- `docs/temp/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md`
- `docs/temp/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
- `docs/temp/0_0-stage3-opening-transition-contract-normalization-remediation-execution-ssot.md`
- `docs/temp/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
- `docs/temp/stage0-treatment-enrich-retirement-remediation-execution-ssot.md`
- `docs/temp/stage0-bi-tr-production-harness-normalization-remediation-execution-ssot.md`
- `docs/temp/frontier-lag-soak-canary-wave1-execution-ssot.md`
- `docs/temp/npc-martial-state-substrate-wave1-execution-ssot.md`

## 1. Purpose

This roadmap is the active controller for the current `docs/temp/` execution queue.

This refresh inserts the new single-episode Stage34 demo utility ahead of the broader closure stack:

1. `0_0-stage34-ep2-single-episode-demo-canary` (new highest priority operator-directed demo utility; frozen ep1 authority + fresh ep2 blueprint/draft only)
2. `0_0-stage4-consumer-contract-normalization-remediation` (aggregate Stage4 wave)
3. `0_0-stage4-flashback-continuity-localfix-remediation` (direct child lane; fresh full run isolated this as the higher-authority immediate blocker)
4. `0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation` (secondary bounded child lane; real seam remains, but contaminated Stage4-only evidence no longer outranks fresh full run)
5. `0_0-stage4-post-select-continuity-contract-normalization-remediation` (partial substrate; solved subtype persistence but not the broader consumer contract family)
6. `0_0-stage4-fixpack-finalization-remediation` (partial substrate; solved missing-fix-pack flattening but not the broader consumer contract family)
7. `0_0-stage4-canonical-entity-postselect-remediation` (partial substrate; moved the blocker forward but did not close Stage4)
8. `0_0-stage2-stage3-stage4-readiness-remediation` (blocked; Stage4 still not closure-ready)
9. `0_0-stage4-ep2-advisory-escalation-loop-remediation` (partial substrate; Flashback FP suppression landed, but fresh full run exposed a real flashback continuity local-fix gap)
10. `0_0-stage4-repair-contract-normalization-remediation` (parked future wave; promoted from the Stage4 repair-contract grammar survey, intended for shared naming/sink/provenance normalization after the immediate ep2 runtime blocker is settled)
11. `0_0-stage234-cross-stage-contract-normalization-remediation` (parked future wave; long-term shared contract substrate)
12. `0_0-stage3-contract-tightening-remediation` (parked future wave; static survey-backed, explicit canary proof pending)
13. `0_0-stage3-opening-transition-contract-normalization-remediation` (parked future wave; BP should eventually distinguish direct continuation vs explicit transition vs jump opening, but this is below current Stage4 runtime work)
14. `0_0-stage2-contract-normalization-remediation` (parked future wave; survey-backed, below active Stage4 seams and below the nearer Stage3 future waves)
15. `stage0-treatment-enrich-retirement-remediation` (parked future wave; optional Stage0 semantic-rewrite workaround retirement, below active runtime work and below Stage2/3 future waves)
16. `stage0-bi-tr-production-harness-normalization-remediation` (parked future wave; Stage0 source-of-truth and dual-artifact production harness normalization, below active runtime work and below nearer Stage0/2/3 hygiene waves)

The new lane outranks all other items because:

- the operator now needs `ep1 frozen + ep2 regenerated` demo proof rather than arc-frontier closure proof
- `run_stage34_canary.py` cannot stop at `ep2` because it is arc-frontier bound
- `Stage4-only canary` remains non-authoritative because blueprint baseline contamination has been proven
- the new runner is a bounded utility, not a replacement for the broader Stage4 closure stack
- the latest global Stage4 consumer-finalization survey showed the dominant residual blocker is broader than any one existing Stage4 seam
- the contaminated Stage4-only ep2 canary isolated one real Stage4 child seam inside that broader family: `NpcDrift relation_to_protag` compressed-tag drift plus missing local-fix synthesis
- the later fresh full run is higher-authority runtime evidence and elevated `Flashback continuity contradiction -> local-fix synthesis` ahead of the contaminated Stage4-only interpretation
- the remaining debt clusters into one aggregate family: intake prose flattening, finalization contract loss, and post-pass split truth
- the parent upstream lane is now blocked by Stage4 finalization, not by Stage2/3 hierarchy
- the existing Stage4 lanes produced useful substrate, but none alone closes the aggregate consumer-side contract family
- the new cross-stage matrix survey proved a real long-term substrate wave is needed, but it remains parked behind the active Stage4 queue
- the remaining legacy temp items were already `parked` or `blocked`
- the new Stage3 and Stage2 future waves are intentionally parked and do not reorder the active Stage4 stack
- the Stage0 enrich path is now explicitly treated as a temporary workaround retirement lane rather than active canonical path work
- the Stage0 BI/TR production harness itself is now explicitly treated as a long-term normalization lane rather than an immediate upstream blocker

## 2. Queue Inventory

| Item | Canonical Path | Temp Path | Status | Notes |
| --- | --- | --- | --- | --- |
| `0_0-stage34-ep2-single-episode-demo-canary` | `docs/2026-04-02/0_0-stage34-ep2-single-episode-demo-canary-execution-ssot.md` | `docs/temp/0_0-stage34-ep2-single-episode-demo-canary-execution-ssot.md` | partial | operator-directed demo utility; code landed; static validation pending runtime demo proof |
| `0_0-stage4-consumer-contract-normalization-remediation` | `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md` | partial | aggregate Stage4 contract wave active; flashback child lane code-landed, runtime proof pending |
| `0_0-stage4-flashback-continuity-localfix-remediation` | `docs/2026-04-02/0_0-stage4-flashback-continuity-localfix-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-flashback-continuity-localfix-remediation-execution-ssot.md` | partial | code landed; static validation closed; fresh full run isolated this as the immediate child seam |
| `0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation` | `docs/2026-04-02/0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation-execution-ssot.md` | partial | code landed; static validation closed; ep2 runtime proof still pending |
| `0_0-stage234-cross-stage-contract-normalization-remediation` | `docs/2026-04-02/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md` | `docs/temp/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md` | parked | long-term shared vocabulary and source-of-truth substrate; survey-backed; held below active Stage4 work |
| `0_0-stage4-post-select-continuity-contract-normalization-remediation` | `docs/2026-04-02/0_0-stage4-post-select-continuity-contract-normalization-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-post-select-continuity-contract-normalization-remediation-execution-ssot.md` | partial | code landed; static validation closed; runtime proof deferred |
| `0_0-stage4-fixpack-finalization-remediation` | `docs/2026-04-02/0_0-stage4-fixpack-finalization-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-fixpack-finalization-remediation-execution-ssot.md` | partial | code landed; static validation closed; runtime proof deferred |
| `0_0-stage4-canonical-entity-postselect-remediation` | `docs/2026-04-01/0_0-stage4-canonical-entity-postselect-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-canonical-entity-postselect-remediation-execution-ssot.md` | partial | runtime partial proof captured; moved the blocker forward into Stage4 finalization |
| `0_0-stage2-stage3-stage4-readiness-remediation` | `docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md` | `docs/temp/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md` | blocked | Stage3 no longer dominant blocker; parent lane still blocked by unresolved Stage4 finalization seams |
| `0_0-stage4-ep2-advisory-escalation-loop-remediation` | `docs/2026-04-01/0_0-stage4-ep2-advisory-escalation-loop-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-ep2-advisory-escalation-loop-remediation-execution-ssot.md` | partial | T1-T3 show positive runtime signal at ep2, but combined Stage4 closure still pending |
| `0_0-stage4-repair-contract-normalization-remediation` | `docs/2026-04-02/0_0-stage4-repair-contract-normalization-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-repair-contract-normalization-remediation-execution-ssot.md` | parked | promoted from the Stage4 repair-contract grammar survey; shared grammar, sink, and provenance normalization lane below the active ep2 runtime stack |
| `0_0-stage3-contract-tightening-remediation` | `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md` | `docs/temp/0_0-stage3-contract-tightening-remediation-execution-ssot.md` | parked | narrowed future wave; binding and semantic-handoff enforcement only; tier-2.5 canary prepared but not executed |
| `0_0-stage3-opening-transition-contract-normalization-remediation` | `docs/2026-04-02/0_0-stage3-opening-transition-contract-normalization-remediation-execution-ssot.md` | `docs/temp/0_0-stage3-opening-transition-contract-normalization-remediation-execution-ssot.md` | parked | opening transition type should eventually be structurally owned by blueprint contract, but this remains a deferred upstream refinement |
| `0_0-stage2-contract-normalization-remediation` | `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md` | `docs/temp/0_0-stage2-contract-normalization-remediation-execution-ssot.md` | parked | narrowed future upstream wave; Stage2 packet extraction and keep-drop normalization only |
| `stage0-treatment-enrich-retirement-remediation` | `docs/2026-04-02/stage0-treatment-enrich-retirement-remediation-execution-ssot.md` | `docs/temp/stage0-treatment-enrich-retirement-remediation-execution-ssot.md` | parked | Stage0 enrich is a temporary semantic-rewrite workaround, not a canonical pair-pass requirement; future retirement/quarantine lane only |
| `stage0-bi-tr-production-harness-normalization-remediation` | `docs/2026-04-02/stage0-bi-tr-production-harness-normalization-remediation-execution-ssot.md` | `docs/temp/stage0-bi-tr-production-harness-normalization-remediation-execution-ssot.md` | parked | Stage0 BI/TR dual-artifact production and source-of-truth split normalization; long-term canonical material contract lane only |
| `frontier-lag-soak-canary-wave1` | `docs/2026-03-27/frontier-lag-soak-canary-wave1-execution-ssot.md` | `docs/temp/frontier-lag-soak-canary-wave1-execution-ssot.md` | parked | non-critical soak lane |
| `npc-martial-state-substrate-wave1` | `docs/2026-03-27/npc-martial-state-substrate-wave1-execution-ssot.md` | `docs/temp/npc-martial-state-substrate-wave1-execution-ssot.md` | blocked | awaits fresh evidence and explicit reactivation |

## 3. Dependency Notes

- `0_0-stage34-ep2-single-episode-demo-canary` is a temporary operator-directed utility lane. It depends on the existing Stage4 consumer-contract substrate but does not replace any closure lane.
- `0_0-stage4-consumer-contract-normalization-remediation` is now the aggregate Stage4 contract wave and the highest-level dependency for any parent-lane advancement.
- `0_0-stage4-flashback-continuity-localfix-remediation` is now the immediate live child seam under the aggregate Stage4 wave because the fresh full run is higher-authority runtime evidence than the contaminated Stage4-only ep2 canary.
- `0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation` remains the next bounded child seam under the aggregate Stage4 wave because the contaminated Stage4-only ep2 canary still isolated a real contract gap there.
- `0_0-stage234-cross-stage-contract-normalization-remediation` is a parked long-term substrate wave; it should not outrank active Stage4 work, but it now outranks ad hoc simplification discussion because the matrix survey proved the debt structure explicitly.
- `0_0-stage4-post-select-continuity-contract-normalization-remediation` is now the direct active seam for advancing Stage4 beyond the residual ep4 final-round downgrade boundary.
- `0_0-stage4-fixpack-finalization-remediation` remains substrate for this new lane.
- `0_0-stage4-canonical-entity-postselect-remediation` produced positive runtime signal but did not close; it now serves as substrate for the new finalization lane.
- `0_0-stage2-stage3-stage4-readiness-remediation` is no longer waiting on upstream Stage3 normalization evidence; it is blocked by unresolved Stage4 finalization seams.
- `0_0-stage4-ep2-advisory-escalation-loop-remediation` remains useful substrate and now has positive ep2 runtime signal, but it still cannot be closed independently of the broader Stage4 finalization outcome.
- `0_0-stage4-repair-contract-normalization-remediation` is parked directly below the active Stage4 runtime seams; it should normalize shared naming, provenance, and sink visibility once immediate ep2 correction-path verification is no longer the dominant blocker.
- `0_0-stage3-contract-tightening-remediation` is intentionally parked; the immediate next artifact is a tier-2.5 canary proof, not execution realization.
- `0_0-stage3-opening-transition-contract-normalization-remediation` is intentionally parked; it is a later blueprint-contract refinement for direct continuation vs explicit transition vs jump opening, not an active runtime blocker.
- `0_0-stage2-contract-normalization-remediation` is intentionally parked; the immediate upstream action is Stage3 static survey, not Stage2 realization.
- `stage0-treatment-enrich-retirement-remediation` is intentionally parked; Golden Canary pair pass does not depend on enrich, and this lane is long-term Stage0 hygiene rather than an active runtime blocker.
- `stage0-bi-tr-production-harness-normalization-remediation` is intentionally parked; the underlying concern is real, but it is a long-term Stage0 source-of-truth refactor, not an active runtime blocker.
- `0_0-stage3-semantic-fidelity-remediation` is closed via `docs/2026-04-01/0_0-stage3-semantic-fidelity-runtime-closure-audit.md`.
- `frontier-lag-soak-canary-wave1` stays parked; it is not a prerequisite for the active 0_0 lanes.
- `npc-martial-state-substrate-wave1` stays blocked and does not constrain any active lane.

## 4. Execution Order

1. `0_0-stage34-ep2-single-episode-demo-canary`
2. `0_0-stage4-consumer-contract-normalization-remediation`
3. `0_0-stage4-flashback-continuity-localfix-remediation`
4. `0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation`
5. `0_0-stage4-post-select-continuity-contract-normalization-remediation`
6. `0_0-stage4-fixpack-finalization-remediation`
7. `0_0-stage4-canonical-entity-postselect-remediation`
8. `0_0-stage2-stage3-stage4-readiness-remediation`
9. `0_0-stage4-ep2-advisory-escalation-loop-remediation`
10. `0_0-stage4-repair-contract-normalization-remediation`
11. `0_0-stage234-cross-stage-contract-normalization-remediation`
12. `0_0-stage3-contract-tightening-remediation`
13. `0_0-stage3-opening-transition-contract-normalization-remediation`
14. `0_0-stage2-contract-normalization-remediation`
15. `stage0-treatment-enrich-retirement-remediation`
16. `stage0-bi-tr-production-harness-normalization-remediation`
17. `frontier-lag-soak-canary-wave1`
18. `npc-martial-state-substrate-wave1`

Order rationale:

- priority 1 is the new single-episode demo utility because the operator explicitly needs fast `ep2` proof without frontier cost
- priority 2 is the aggregate Stage4 consumer-contract wave because the latest survey proved the residual blocker is broader than any one existing Stage4 patch lane
- priority 3 is the Flashback continuity child lane because the fresh full run is the highest-authority current runtime evidence
- priority 4 is the NpcDrift relation-tag child lane because the contaminated Stage4-only ep2 canary still isolated a real secondary seam
- priority 5 is the post-select continuity-contract substrate lane
- priority 6 is the fix-pack/finalization substrate lane
- priority 7 is the canonical-entity/postselect substrate lane
- priority 8 is the parent upstream lane, still blocked specifically by unresolved Stage4 seams
- priority 9 is the already-landed ep2 advisory substrate lane
- priority 10 is the parked Stage4 repair-contract normalization wave; it is the shared grammar/sink substrate surfaced by the latest Stage4 survey, but it remains below the immediate ep2 runtime blocker
- priority 11 is the parked cross-stage contract substrate wave, justified by the completed matrix survey but still below active Stage4 work
- priority 12 is the parked Stage3 future wave, closer to current evidence than the Stage2 future wave but still not active
- priority 13 is the parked Stage3 opening-transition refinement wave; it is narrower than general Stage3 tightening and intentionally deferred below it
- priority 14 is the parked Stage2 future wave
- priority 15 is the parked Stage0 enrich retirement wave; it is real hygiene debt but not an active runtime blocker
- priority 16 is the parked Stage0 BI/TR production harness normalization wave; it is a larger upstream refactor and remains below nearer hygiene lanes
- priority 17 remains a parked soak lane
- priority 18 remains blocked and cannot outrank an executable lane

## 5. Per-Item Status Ledger

### 0_0-stage34-ep2-single-episode-demo-canary

- execution SSOT: `partially_realized`
- primary seams:
  - `run_stage34_canary.py` cannot stop at `ep2`
  - `Stage4-only canary` is non-authoritative after blueprint contamination audit
  - demo needs `frozen ep1 authority + fresh ep2 regeneration` as a bounded utility
- next action:
  - keep this lane bounded to demo proof
  - do not treat it as Stage4 closure proof
  - runtime demo proof remains pending
- temp cleanup action:
  - remove mirror after demo runtime proof is captured or the utility is superseded

### 0_0-stage4-consumer-contract-normalization-remediation

- global Stage4 consumer-finalization survey completed (2026-04-02)
- execution SSOT: `partially_realized`
- primary seams:
  - intake prose flattening of canonical truth
  - fix-pack provenance and routing ambiguity
  - post-select bounded-repair flattening
  - post-pass split truth across `final_state_updates`, `actual_truth`, and `world_state`
- next action:
  - keep Stage4 paused
  - treat the new Flashback continuity local-fix lane as the immediate active child seam
  - treat the NpcDrift relation-tag lane as the next bounded child seam
  - treat existing Stage4 partial lanes as substrate
  - do not start realization from this document until explicit operator direction
- temp cleanup action:
  - keep mirror while this remains the aggregate Stage4 contract lane; remove only on explicit closure or replacement

### 0_0-stage4-flashback-continuity-localfix-remediation

- bounded survey completed (2026-04-02)
- execution SSOT: `partially_realized`
- primary seams:
  - real flashback continuity contradictions are detected but flattened into advisory-only text
  - Flashback structured metadata was not retained across Stage4 fix-pack synthesis
  - locally repairable flashback contradictions could not synthesize bounded local fix contracts from zero
- next action:
  - keep Stage4 paused
  - treat this as the immediate active child seam under the aggregate Stage4 wave
  - runtime proof still pending; do not treat contaminated Stage4-only ep2 canary as closure evidence
- temp cleanup action:
  - do not remove mirror until code landed, focused static validation, and later runtime proof all close

### 0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation

- bounded survey completed (2026-04-02)
- execution SSOT: `partially_realized`
- primary seams:
  - compressed `relation_to_protag` canonical tags have no semantic-expansion bridge
  - `NpcDrift` relation-tag drift is escalated too coarsely for this subtype
  - advisory-only relation-tag drift cannot synthesize bounded local fix contracts from zero
- next action:
  - keep Stage4 paused
  - treat this as the next bounded child seam under the aggregate Stage4 wave after flashback continuity local-fix
  - do not widen into broad NpcDrift rewrite before bounded realization is attempted
- temp cleanup action:
  - keep mirror while this remains the live secondary child seam; remove only on explicit closure or replacement

### 0_0-stage234-cross-stage-contract-normalization-remediation

- matrix survey completed (2026-04-02)
- execution SSOT: `parked`
- primary seams:
  - shared vocabulary absence across Stage2/3/4
  - owner ambiguity for repair/finalization and post-pass truth
  - strength inversion and structure-to-prose loss at major boundaries
- next action:
  - do not activate now
  - use as long-term substrate for future simplification and contract work
  - keep active Stage4 remediation above this item
- temp cleanup action:
  - keep mirror while this remains the canonical parked substrate wave; remove only on explicit closure or replacement

### 0_0-stage4-post-select-continuity-contract-normalization-remediation

- bounded survey completed (2026-04-02)
- execution SSOT: `partially_realized`
- primary seams:
  - post-select conflict contract preserves too little contradiction subtype precision
  - bounded proper-noun/timeline continuity cases are flattened too similarly to broader rewrite-class collapse
- next action:
  - contract normalization code landed in Stage4
  - keep Stage4 paused
  - defer runtime proof to a later focused canary/order
- temp cleanup action:
  - do not remove mirror until code lands, focused validation passes, and a later closure audit completes

### 0_0-stage4-fixpack-finalization-remediation

- bounded survey completed (2026-04-02)
- execution SSOT: `partially_realized`
- primary seams:
  - runtime fix-pack backfill when strong advisory escalation creates the first local repair obligation
  - selective fix-pack preservation/classification when post-select conflict downgrades a provisional pass
- next action:
  - bounded Stage4 patch landed
  - focused static validation closed
  - keep Stage4 paused
  - defer runtime proof to a later focused canary/order
- temp cleanup action:
  - do not remove mirror until code lands, focused validation passes, and a later closure audit completes

### 0_0-stage4-canonical-entity-postselect-remediation

- bounded survey completed (2026-04-01)
- execution SSOT: `partially_realized`
- primary seams:
  - Stage4 post-pass active-pressure alignment to final accepted manuscript truth
  - Stage3 fact-lock institution canonical source priority
- next action:
  - bounded code patch landed
  - focused static validation closed
  - runtime partial proof captured via `docs/2026-04-02/0_0-stage4-canonical-entity-postselect-runtime-closure-audit.md`
  - keep Stage4 paused
  - keep this lane as substrate while the new Stage4 finalization lane runs
- temp cleanup action:
  - do not remove mirror until the follow-up Stage4 seam is addressed and a later closure audit completes

### 0_0-stage2-stage3-stage4-readiness-remediation

- ctxnorm_r1 canary complete (2026-04-01)
- Stage3 sub-verdict improved materially and remains non-dominant in the latest canary
- parent lane verdict: `blocked`
- next action:
  - do not reopen Stage2/3 hierarchy work
  - wait for the next bounded Stage4 finalization seam to land
  - reassess the parent lane only after Stage4 can progress beyond the ep3/ep4 blockers
- temp cleanup action:
  - do not remove mirror until the parent lane advances beyond `blocked/partial`

### 0_0-stage4-ep2-advisory-escalation-loop-remediation

- bounded survey completed (2026-04-01)
- execution SSOT: `partially_realized`
- T1-T3 landed:
  - FlashbackVerifier precision
  - strong advisory operator persistence
  - post_select_conflict detail persistence
- next action:
  - keep Stage4 paused
  - retain as substrate lane
  - runtime signal is now positive on Flashback false-positive suppression, but the fresh full run exposed a separate flashback continuity local-fix seam
  - still defer final closure until the flashback child seam, the NpcDrift child seam, and the broader Stage4 finalization seam are closed
- temp cleanup action:
  - do not remove mirror until combined closure audit completes

### 0_0-stage3-contract-tightening-remediation

- static global Stage3 survey completed (2026-04-02)
- execution SSOT: `parked`
- primary seams:
  - binding scope gap
  - advisory-heavy enforcement
  - semantically lossy Stage3 -> Stage4 handoff
  - targeted timeline and institution contract coverage gaps
- next action:
  - do not execute now
  - keep as survey-backed future wave
  - prepare and later run explicit tier-2.5 canary proof before reprioritization
- temp cleanup action:
  - keep mirror while this remains a parked future wave; remove only on explicit closure or replacement

### 0_0-stage3-opening-transition-contract-normalization-remediation

- execution SSOT: `parked`
- primary seams:
  - blueprint opening contract does not yet structurally distinguish direct continuation vs explicit transition vs jump opening
  - Stage4 still has to infer too much opening movement/path semantics from prose and prior ending
  - this is an upstream refinement, not the current direct runtime blocker
- next action:
  - do not activate now
  - keep as context-only future wave
  - revisit only after active Stage4 opening/runtime seams are reduced or explicit reprioritization occurs
- temp cleanup action:
  - keep mirror while this remains a parked future wave; remove only on explicit closure or replacement

### 0_0-stage2-contract-normalization-remediation

- global Stage2 production-consumption survey completed (2026-04-02)
- execution SSOT: `parked`
- primary seams:
  - mission truth trapped in `tactical_doc` prose
  - Stage2-owned packet alias ambiguity at emission time
  - low-signal or dropped fields (`beat_sequence`, `hybrid_composition`, `semantic_carryover`)
- next action:
  - do not activate now
  - keep as survey-backed future wave
  - keep this wave behind the nearer Stage3 future wave and the active Stage4 seams
  - revisit only after active Stage4 seams are reduced or explicit reprioritization occurs
- temp cleanup action:
  - keep mirror while this remains a parked future wave; remove only on explicit closure or replacement

### stage0-treatment-enrich-retirement-remediation

- Stage0 BI generation / DNA sync / Stage2 consume survey completed (2026-04-02)
- execution SSOT: `parked`
- primary seams:
  - `enrich` is an optional semantic rewrite helper, not a canonical Stage0 pair-pass requirement
  - legacy/manual Stage0 flow can still invoke it via opt-in prompt
  - operator-facing contract does not yet demote it clearly enough to a non-canonical salvage utility
- next action:
  - do not activate now
  - keep as Stage0 hygiene and retirement/quarantine future wave
  - keep this wave below the parked Stage3 and Stage2 normalization waves
  - revisit only after active Stage4 work is reduced or explicit reprioritization occurs
- temp cleanup action:
  - keep mirror while this remains a parked future wave; remove only on explicit closure or replacement

### stage0-bi-tr-production-harness-normalization-remediation

- Stage0 BI generation / DNA sync / Stage2 consume survey completed (2026-04-02)
- execution SSOT: `parked`
- primary seams:
  - BI file / treatment / DB bible anchor split-truth
  - dual-artifact production with unstable authoritative boundary
  - Stage2 consume contract depends more on runtime handoff than raw artifact truth
- next action:
  - do not activate now
  - keep as long-term Stage0 source-of-truth and production harness normalization wave
  - keep this wave below the parked Stage0 enrich retirement lane and below the parked Stage3 and Stage2 normalization waves
  - revisit only after active Stage4 work is reduced or explicit reprioritization occurs
- temp cleanup action:
  - keep mirror while this remains a parked future wave; remove only on explicit closure or replacement

### frontier-lag-soak-canary-wave1

- next action:
  - stay parked
- temp cleanup action:
  - remove mirror on explicit closure or replacement

### npc-martial-state-substrate-wave1

- next action:
  - stay blocked pending fresh evidence
- temp cleanup action:
  - remove mirror only after reactivation decision or formal closure

## 6. Cleanup Rule

- canonical execution SSOTs remain in dated `docs/`
- temp mirrors remain the active queue only until each item is realized or formally closed
- when the queue is exhausted, remove:
  - temp execution SSOT mirrors
  - `docs/temp/execution-roadmap.md`
  - `docs/temp/queue-state.json`

## 7. 3-Pass Audit Record (Refresh)

### Pass 1. Structure and Scope

- queue inventory updated to include the new aggregate Stage4 contract lane
- queue inventory updated again to include the new single-episode demo utility ahead of broader closure work
- new Flashback continuity child lane added directly under the aggregate Stage4 lane
- NpcDrift child lane kept directly below it as the next bounded seam
- existing Stage4 lanes kept as substrate rather than removed
- parent readiness lane remains blocked behind Stage4

### Pass 2. Evidence and Consistency

- canonical and temp paths for the new aggregate lane verified against filesystem
- canonical and temp paths for the new single-episode demo lane verified against filesystem
- ordering is consistent with the latest Stage4 consumer-finalization survey and the latest ep2 bounded canary failure
- parked/blocked legacy items remain unchanged

### Pass 3. Execution and Readability

- per-item status ledger updated with concrete next actions
- dependency chain is explicit: demo utility -> aggregate Stage4 contract wave -> Flashback child lane -> NpcDrift child lane -> substrate lanes -> parent readiness -> later runtime proof -> Stage4 resume decision
- new parked Stage2 future wave inserted without disturbing active Stage4 order
- new parked Stage3 future wave inserted ahead of the Stage2 future wave without disturbing active Stage4 order
- no overreach: demo utility not promoted to closure proof, Stage4 resume not declared

Confidence: `96%`
