# Active Temp Execution Roadmap

Date: 2026-04-01
Status: active (3-pass re-audited 2026-04-06; fresh full run plus r2 Stage4-only sinkproof confirm ep2 can PASS through Stage4, bounded Stage4 P1 patches narrowed the front debt further, the Stage2 persistence-authority child tranche has landed with focused Stage2 family validation, and the 2026-04-07 workspace reinspection reconfirmed that the new non-wuxia state-lock overreach lane has only its Stage2 producer tranche landed while Stage4 intake/post-pass work remains pending; no new P0 surfaced)
Canonical Path: `docs/2026-04-01/active-temp-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Baseline Commit: `fd1707372bd7eb8ad23a5d4506ef556e3f72cc51`
Baseline Dirty Summary: `dirty: 0_0 runtime logs/db/artifacts active; legacy temp queue mirrors present; 2026-03-31 0_0 survey docs untracked`
Resume Commit: `5c71b81a36ab2cbae824c630bb63219354b913a8`
Resume Drift Summary: `2026-04-06 Opus global P0-P1 survey plus bounded Stage4 and Stage2 sink work sharpened the queue: no new P0 surfaced, Stage4 consumer remains front on numeric carryover baseline-promotion/owner-boundary, Stage4 repair remains next on repair/readback phantom mismatch normalization, the Stage2 persistence-authority child tranche is landed and verification-backed across preflight/validation/finalizer, and the 2026-04-07 workspace reinspection confirmed the non-wuxia state-lock overreach lane still sits between the active Stage4 pair and the broader residual Stage2 queue item because its Stage4 tranche has not yet landed`
Supersedes:
- `docs/2026-03-31/active-temp-execution-roadmap.md`

Queue Snapshot:
- `docs/temp/0_0-stage34-ep2-single-episode-demo-canary-execution-ssot.md`
- `docs/temp/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
- `docs/temp/0_0-stage4-flashback-continuity-localfix-remediation-execution-ssot.md`
- `docs/temp/0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation-execution-ssot.md`
- `docs/temp/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md`
- `docs/temp/0_0-stage4-canonical-entity-postselect-remediation-execution-ssot.md`
- `docs/temp/0_0-stage4-ep2-advisory-escalation-loop-remediation-execution-ssot.md`
- `docs/temp/0_0-stage4-repair-contract-normalization-remediation-execution-ssot.md`
- `docs/temp/0_0-stage234-nonwuxia-state-lock-overreach-remediation-execution-ssot.md`
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

This refresh folds in the `r2` Stage4-only sinkproof result, the later analyzer/readback backfill, the numeric authority re-audit, the 2026-04-05 `Stage3 ep2 cutoff accepted` note, the 2026-04-06 Stage2 persistence-authority promotion, the later bounded Stage2 implementation/verification pass, and the new 2026-04-06 non-wuxia state-lock overreach execution lane. The queue is now intentionally sorted as:

1. active front-owner work (`Stage4 consumer` -> `Stage4 repair` -> `non-wuxia state-lock overreach` -> `broader Stage2 residual` -> blocked parent readiness lane)
2. parked future-wave work (`cross-stage`, `Stage3`, `Stage0`)
3. historical runtime-positive substrate and utility references (demo canary plus landed Stage4 child lanes)

Working order:

1. `0_0-stage4-consumer-contract-normalization-remediation` (aggregate Stage4 wave; PASS proof captured, residual seam narrowed to numeric carryover baseline-promotion / owner-boundary)
2. `0_0-stage4-repair-contract-normalization-remediation` (shared repair-contract grammar lane; next open Stage4 substrate for repair/readback phantom mismatch normalization after the child-lane closures)
3. `0_0-stage234-nonwuxia-state-lock-overreach-remediation` (new bounded P1 lane; dual-owner Stage2 + Stage4 fix for false hard-fail pressure on non-wuxia fatigue / recovery / opening carryover)
4. `0_0-stage2-contract-normalization-remediation` (verification-backed Stage2 residual lane; bounded `world_joint` / `status_shadow` persistence-authority child tranche has landed across preflight/validation/finalizer sinks, while broader Stage2 normalization remains deferred inside the same SSOT)
5. `0_0-stage2-stage3-stage4-readiness-remediation` (blocked parent lane; do not reopen broad readiness/hierarchy work while Stage4 front seams, the new non-wuxia P1 lane, and the promoted Stage2 persistence tranche remain open)
6. `0_0-stage234-cross-stage-contract-normalization-remediation` (parked future wave; long-term shared contract substrate)
7. `0_0-stage3-contract-tightening-remediation` (parked future wave; static survey-backed, explicit canary proof pending)
8. `0_0-stage3-opening-transition-contract-normalization-remediation` (parked future wave; BP should eventually distinguish direct continuation vs explicit transition vs jump opening, but this is below current Stage4 runtime work)
9. `stage0-treatment-enrich-retirement-remediation` (parked future wave; optional Stage0 semantic-rewrite workaround retirement, below active runtime work and below the current Stage2/3 future waves)
10. `stage0-bi-tr-production-harness-normalization-remediation` (parked future wave; Stage0 source-of-truth and dual-artifact production harness normalization, below active runtime work and below nearer Stage0/2/3 hygiene waves)
11. `frontier-lag-soak-canary-wave1` (parked soak lane)
12. `npc-martial-state-substrate-wave1` (blocked soak/substrate lane)
13. `0_0-stage34-ep2-single-episode-demo-canary` (completed utility lane; retained only as historical backing)
14. `0_0-stage4-ep2-advisory-escalation-loop-remediation` (runtime-positive substrate; no longer active queue work)
15. `0_0-stage4-canonical-entity-postselect-remediation` (runtime-positive substrate; no longer active queue work)
16. `0_0-stage4-flashback-continuity-localfix-remediation` (completed runtime-positive substrate; historical backing only)
17. `0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation` (runtime-positive substrate lane; historical backing only)

This order now reflects the stronger runtime picture:

- the fresh full run plus `r2` sinkproof canary prove `ep2` can PASS through Stage4
- the earlier sink hard-fail reading no longer governs the queue
- the `__000403` fresh run closes the post-select continuity and fixpack-finalization child lanes with runtime proof rather than static-only confidence
- the surviving active debt is numeric asset authority / carryover owner-boundary plus the still-open repair-contract grammar lane, not NPC false reject, patch-trace non-exercise, or missing final Stage4 rows
- the 2026-04-06 global P0-P1 sweep found no new cross-pipeline P0; the live P1 picture remains the existing Stage4 front seams plus residual Stage2 contract debt, but the bounded Stage2 persistence truth-loss child tranche itself is now landed and verification-backed
- the new non-wuxia state-lock overreach lane is a fresh survey-backed P1 and now sits ahead of the broader residual Stage2 queue item because it is narrower, operator-facing, and verification-ready while still remaining below the current Stage4 pair
- the Stage4 repair-contract family now sits closest to the front of the open queue as substrate for the residual Stage4 numeric seam
- the broader Stage2 residual SSOT now sits behind the new non-wuxia lane because the validation/finalizer overwrite shells were already revalidated and patched, while the new overreach seam remains unimplemented
- flashback and NpcDrift remain runtime-positive substrate lanes, but neither is the current immediate blocker
- the parent upstream lane is still blocked by the remaining Stage4 consumer-side seams, the new non-wuxia P1 lane, plus the newly promoted Stage2 persistence tranche, not by broad Stage2/3 hierarchy
- the 2026-04-05 `0000000000_0405_s2fresh_r1` Stage3 ep2 cutoff confirms the temporary S2 detour can stand down without promoting a new Stage3 front blocker
- the remaining legacy temp items were already `parked` or `blocked`
- the new Stage3 future waves remain intentionally parked
- the Stage0 enrich path remains a temporary workaround retirement lane rather than active canonical path work
- the Stage0 BI/TR production harness remains a long-term normalization lane rather than an immediate upstream blocker
- the completed demo/substrate lanes remain in the roadmap only as historical runtime backing; they should not outrank parked future-wave work

## 2. Queue Inventory

| Item | Canonical Path | Temp Path | Status | Notes |
| --- | --- | --- | --- | --- |
| `0_0-stage4-consumer-contract-normalization-remediation` | `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md` | partial | aggregate Stage4 contract wave active; fresh full run plus r2 sinkproof captured positive runtime proof; remaining seam is numeric asset authority / carryover baseline-promotion gap |
| `0_0-stage4-repair-contract-normalization-remediation` | `docs/2026-04-02/0_0-stage4-repair-contract-normalization-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-repair-contract-normalization-remediation-execution-ssot.md` | partial | shared grammar, sink, provenance, and repair readback phantom-mismatch normalization lane remains the next queued Stage4 substrate |
| `0_0-stage234-nonwuxia-state-lock-overreach-remediation` | `docs/2026-04-06/0_0-stage234-nonwuxia-state-lock-overreach-remediation-execution-ssot.md` | `docs/temp/0_0-stage234-nonwuxia-state-lock-overreach-remediation-execution-ssot.md` | partial | new bounded P1 lane; 2026-04-07 reinspection confirmed Stage2 producer tranche landed while Stage4 intake/post-pass normalization still remains pending |
| `0_0-stage2-contract-normalization-remediation` | `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md` | `docs/temp/0_0-stage2-contract-normalization-remediation-execution-ssot.md` | partial | active bounded Stage2 tranche; preserves `joint_docs.world_joint` / `status_shadow` through validation/finalizer sinks while leaving broader Stage2 normalization deferred |
| `0_0-stage2-stage3-stage4-readiness-remediation` | `docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md` | `docs/temp/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md` | blocked | Stage3 no longer dominant blocker; parent lane is now blocked by unresolved Stage4 front seams, the new non-wuxia P1 lane, and the newly promoted Stage2 persistence tranche |
| `0_0-stage234-cross-stage-contract-normalization-remediation` | `docs/2026-04-02/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md` | `docs/temp/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md` | parked | long-term shared vocabulary and source-of-truth substrate; survey-backed; held below active Stage4 work |
| `0_0-stage3-contract-tightening-remediation` | `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md` | `docs/temp/0_0-stage3-contract-tightening-remediation-execution-ssot.md` | parked | narrowed future wave; binding and semantic-handoff enforcement only; tier-2.5 canary prepared but not executed |
| `0_0-stage3-opening-transition-contract-normalization-remediation` | `docs/2026-04-02/0_0-stage3-opening-transition-contract-normalization-remediation-execution-ssot.md` | `docs/temp/0_0-stage3-opening-transition-contract-normalization-remediation-execution-ssot.md` | parked | opening transition type should eventually be structurally owned by blueprint contract, but this remains a deferred upstream refinement |
| `stage0-treatment-enrich-retirement-remediation` | `docs/2026-04-02/stage0-treatment-enrich-retirement-remediation-execution-ssot.md` | `docs/temp/stage0-treatment-enrich-retirement-remediation-execution-ssot.md` | parked | Stage0 enrich is a temporary semantic-rewrite workaround, not a canonical pair-pass requirement; future retirement/quarantine lane only |
| `stage0-bi-tr-production-harness-normalization-remediation` | `docs/2026-04-02/stage0-bi-tr-production-harness-normalization-remediation-execution-ssot.md` | `docs/temp/stage0-bi-tr-production-harness-normalization-remediation-execution-ssot.md` | parked | Stage0 BI/TR dual-artifact production and source-of-truth split normalization; long-term canonical material contract lane only |
| `frontier-lag-soak-canary-wave1` | `docs/2026-03-27/frontier-lag-soak-canary-wave1-execution-ssot.md` | `docs/temp/frontier-lag-soak-canary-wave1-execution-ssot.md` | parked | non-critical soak lane |
| `npc-martial-state-substrate-wave1` | `docs/2026-03-27/npc-martial-state-substrate-wave1-execution-ssot.md` | `docs/temp/npc-martial-state-substrate-wave1-execution-ssot.md` | blocked | awaits fresh evidence and explicit reactivation |
| `0_0-stage34-ep2-single-episode-demo-canary` | `docs/2026-04-02/0_0-stage34-ep2-single-episode-demo-canary-execution-ssot.md` | `docs/temp/0_0-stage34-ep2-single-episode-demo-canary-execution-ssot.md` | completed | operator-directed demo utility; bounded ep2 proof captured; historical backing only |
| `0_0-stage4-ep2-advisory-escalation-loop-remediation` | `docs/2026-04-01/0_0-stage4-ep2-advisory-escalation-loop-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-ep2-advisory-escalation-loop-remediation-execution-ssot.md` | partial | runtime-positive substrate; still useful for history, but no longer active queue work |
| `0_0-stage4-canonical-entity-postselect-remediation` | `docs/2026-04-01/0_0-stage4-canonical-entity-postselect-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-canonical-entity-postselect-remediation-execution-ssot.md` | partial | runtime-positive substrate; moved the blocker forward but is no longer current queue work |
| `0_0-stage4-flashback-continuity-localfix-remediation` | `docs/2026-04-02/0_0-stage4-flashback-continuity-localfix-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-flashback-continuity-localfix-remediation-execution-ssot.md` | completed | code landed; static validation closed; completed runtime-positive historical substrate |
| `0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation` | `docs/2026-04-02/0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation-execution-ssot.md` | partial | code landed; static validation closed; runtime-positive historical substrate |

## 3. Dependency Notes

- `0_0-stage34-ep2-single-episode-demo-canary` is a temporary operator-directed utility lane. It already produced the bounded ep2 proof needed for this question and now sits below the active closure stack.
- `0_0-stage4-consumer-contract-normalization-remediation` is now the aggregate Stage4 contract wave and the highest-level dependency for any parent-lane advancement.
- `0_0-stage4-post-select-continuity-contract-normalization-remediation` and `0_0-stage4-fixpack-finalization-remediation` are now closed runtime-positive child lanes; their runtime proof remains relevant historical backing for the surviving numeric authority / carryover seam.
- `0_0-stage4-repair-contract-normalization-remediation` is now the closest remaining open substrate after those child-lane closures.
- `0_0-stage234-nonwuxia-state-lock-overreach-remediation` is a new bounded P1 lane. It should stay below the current Stage4 consumer/repair pair, but it now outranks the broader residual Stage2 SSOT because it is narrower, directly operator-facing, and already has clear producer/consumer owners plus targeted test coverage.
- `0_0-stage4-flashback-continuity-localfix-remediation` is now a completed runtime-positive substrate lane rather than an active blocker.
- `0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation` now sits as a runtime-positive substrate lane because r2 removed it as the immediate live blocker.
- `0_0-stage234-cross-stage-contract-normalization-remediation` is a parked long-term substrate wave; it should not outrank active Stage4 work, but it now outranks ad hoc simplification discussion because the matrix survey proved the debt structure explicitly.
- `0_0-stage4-post-select-continuity-contract-normalization-remediation` is closed and no longer an active queue item; retain it only as historical proof that typed contradiction lineage now survives the post-select downgrade.
- `0_0-stage4-fixpack-finalization-remediation` is closed and no longer an active queue item; retain it only as historical proof that bounded local fix-pack traces survive the finalization sinks.
- `0_0-stage4-canonical-entity-postselect-remediation` produced positive runtime signal but did not close; it now serves as substrate for the new finalization lane.
- `0_0-stage2-stage3-stage4-readiness-remediation` is no longer waiting on upstream Stage3 normalization evidence; it is blocked by the remaining Stage4 consumer-side seams, the new non-wuxia P1 lane, plus the active Stage2 persistence-authority tranche.
- `projects/0000000000_0405_s2fresh_r1` Stage3 ep2 cutoff confirms the temporary S2 detour can stop here; do not reopen Stage2/3 priority from early-gate anxiety alone.
- `0_0-stage4-ep2-advisory-escalation-loop-remediation` remains useful substrate and now has positive ep2 runtime signal, but it still cannot be closed independently of the broader Stage4 finalization outcome.
- `0_0-stage4-repair-contract-normalization-remediation` should normalize shared naming, provenance, and sink visibility when the queue returns from residual quality/finalization work to grammar cleanup.
- the 2026-04-06 revalidation sharpens that repair lane further: readback phantom mismatches and metadata-absence artifacts are now the concrete open substrate under shared repair grammar.
- `0_0-stage2-contract-normalization-remediation` remains an active bounded tranche, but its broader residual work now sits behind the new non-wuxia state-lock overreach lane.
- `0_0-stage3-contract-tightening-remediation` is intentionally parked; the immediate next artifact is a tier-2.5 canary proof, not execution realization.
- `0_0-stage3-opening-transition-contract-normalization-remediation` is intentionally parked; it is a later blueprint-contract refinement for direct continuation vs explicit transition vs jump opening, not an active runtime blocker.
- `stage0-treatment-enrich-retirement-remediation` is intentionally parked; Golden Canary pair pass does not depend on enrich, and this lane is long-term Stage0 hygiene rather than an active runtime blocker.
- `stage0-bi-tr-production-harness-normalization-remediation` is intentionally parked; the underlying concern is real, but it is a long-term Stage0 source-of-truth refactor, not an active runtime blocker.
- `0_0-stage3-semantic-fidelity-remediation` is closed via `docs/2026-04-01/0_0-stage3-semantic-fidelity-runtime-closure-audit.md`.
- `frontier-lag-soak-canary-wave1` stays parked; it is not a prerequisite for the active 0_0 lanes.
- `npc-martial-state-substrate-wave1` stays blocked and does not constrain any active lane.

## 4. Execution Order

1. `0_0-stage4-consumer-contract-normalization-remediation`
2. `0_0-stage4-repair-contract-normalization-remediation`
3. `0_0-stage234-nonwuxia-state-lock-overreach-remediation`
4. `0_0-stage2-contract-normalization-remediation`
5. `0_0-stage2-stage3-stage4-readiness-remediation`
6. `0_0-stage234-cross-stage-contract-normalization-remediation`
7. `0_0-stage3-contract-tightening-remediation`
8. `0_0-stage3-opening-transition-contract-normalization-remediation`
9. `stage0-treatment-enrich-retirement-remediation`
10. `stage0-bi-tr-production-harness-normalization-remediation`
11. `frontier-lag-soak-canary-wave1`
12. `npc-martial-state-substrate-wave1`
13. `0_0-stage34-ep2-single-episode-demo-canary`
14. `0_0-stage4-ep2-advisory-escalation-loop-remediation`
15. `0_0-stage4-canonical-entity-postselect-remediation`
16. `0_0-stage4-flashback-continuity-localfix-remediation`
17. `0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation`

Order rationale:

- priority 1 is the aggregate Stage4 consumer-contract wave because it now contains the surviving bounded seam after PASS proof capture
- priority 2 is the repair-contract grammar lane because scope/provenance clarity and readback truth still matter for numeric carryover remediation after the post-select and fixpack child lanes closed
- priority 3 is the new survey-backed non-wuxia state-lock overreach lane because it is a bounded P1 with clear Stage2 + Stage4 owners, direct operator impact, and targeted verification paths, while still remaining below the active Stage4 pair
- priority 4 is the verification-backed broader Stage2 residual lane because the bounded persistence-authority child tranche has already landed, but the SSOT still holds deferred normalization and Golden follow-up debt
- priority 5 is the parent upstream lane, still blocked specifically by the remaining Stage4 consumer-side seams, the new non-wuxia lane, and the broader Stage2 residual queue item
- priority 6 is the parked cross-stage contract substrate wave, justified by the completed matrix survey but still below active Stage4 and near-front Stage2/Stage234 work
- priority 7 is the parked Stage3 future wave, now below the current Stage2 and non-wuxia residual lanes
- priority 8 is the parked Stage3 opening-transition refinement wave; it is narrower than general Stage3 tightening and intentionally deferred below it
- priority 9 is the parked Stage0 enrich retirement wave; it is real hygiene debt but not an active runtime blocker
- priority 10 is the parked Stage0 BI/TR production harness normalization wave; it is a larger upstream refactor and remains below nearer hygiene lanes
- priority 11 remains a parked soak lane
- priority 12 remains blocked and cannot outrank an executable lane
- priorities 13-17 are completed or runtime-positive historical backing lanes; retain them for evidence, but do not treat them as active work ahead of the parked future-wave stack

## 5. Per-Item Status Ledger

### 0_0-stage34-ep2-single-episode-demo-canary

- execution SSOT: `completed`
- primary seams:
  - `run_stage34_canary.py` cannot stop at `ep2`
  - `Stage4-only canary` is non-authoritative after blueprint contamination audit
  - demo needs `frozen ep1 authority + fresh ep2 regeneration` as a bounded utility
- next action:
  - do not resume this lane unless a new operator-directed demo question appears
  - do not treat it as Stage4 closure proof
  - the current ep2 proof question is already served; retain as historical utility only
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
  - keep Stage4 paused for broad resume claims
  - record the `projects/00_20260403` fresh full run as positive proof that `ep2` can now reach `PASS` through bounded inplace correction
  - record the `r2` Stage4-only sinkproof canary as positive proof that authoritative Stage4 rows now land in `stage_attempts`
  - stop treating Flashback and NpcDrift as the immediate live blocker pair
  - keep opening-authority alignment bounded to declared transition / replay-suppression enforcement without converting the ep2 local-fix into a global same-location hard lock
  - treat numeric asset authority / carryover owner-boundary across the post-select, fix-pack, repair-contract, and carryover packet family as the next bounded consumer-side subtask
  - use the 2026-04-06 Opus revalidation as confirmation that this seam is a baseline-promotion/readback pressure problem, not a revived final-sink failure
  - keep the parked Stage3 opening-transition lane deferred unless later runtime evidence shifts the owner boundary
- temp cleanup action:
  - keep mirror while this remains the aggregate Stage4 contract lane; remove only on explicit closure or replacement

### 0_0-stage4-flashback-continuity-localfix-remediation

- bounded survey completed (2026-04-02)
- execution SSOT: `completed`
- primary seams:
  - real flashback continuity contradictions are detected but flattened into advisory-only text
  - Flashback structured metadata was not retained across Stage4 fix-pack synthesis
  - locally repairable flashback contradictions could not synthesize bounded local fix contracts from zero
- next action:
  - keep Stage4 paused
  - treat this as completed runtime-positive substrate under the aggregate Stage4 wave, not an active blocker
  - do not treat this seam as license for unconditional same-location opening locks; declared transitions and allowed alternate openings remain valid
  - use the merged runtime evidence as closure backing for this lane's bounded contract, while keeping any broader replay wording below the new numeric carryover seam
- temp cleanup action:
  - remove mirror on the next queue cleanup pass once the aggregate consumer lane no longer needs it as an active child reference

### 0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation

- bounded survey completed (2026-04-02)
- execution SSOT: `partially_realized`
- primary seams:
  - compressed `relation_to_protag` canonical tags have no semantic-expansion bridge
  - `NpcDrift` relation-tag drift is escalated too coarsely for this subtype
  - advisory-only relation-tag drift cannot synthesize bounded local fix contracts from zero
- next action:
  - keep Stage4 paused
  - treat this as a runtime-positive substrate/reference seam under the aggregate Stage4 wave
  - use the `r2` sinkproof canary as positive proof that this lane no longer blocks ep2 convergence
  - do not widen into broad NpcDrift rewrite before bounded realization is attempted
- temp cleanup action:
  - keep mirror while this remains a referenced runtime-positive substrate lane; remove only on explicit closure or replacement

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
- execution SSOT: `completed`
- primary seams:
  - post-select conflict contract preserves too little contradiction subtype precision
  - bounded proper-noun/timeline continuity cases are flattened too similarly to broader rewrite-class collapse
- next action:
  - runtime proof is now captured via `projects/__000403`
  - keep this lane closed as historical backing for typed contradiction lineage through the post-select downgrade
  - do not reopen unless a later fresh run shows subtype/detail loss again
- temp cleanup action:
  - mirror removed on the 2026-04-04 closure pass

### 0_0-stage4-fixpack-finalization-remediation

- bounded survey completed (2026-04-02)
- execution SSOT: `completed`
- primary seams:
  - runtime fix-pack backfill when strong advisory escalation creates the first local repair obligation
  - selective fix-pack preservation/classification when post-select conflict downgrades a provisional pass
- next action:
  - runtime proof is now captured via `projects/__000403`
  - keep this lane closed as historical backing for bounded local fix-pack persistence through the finalization sinks
  - do not reopen unless a later fresh run shows bounded fix-pack loss again
- temp cleanup action:
  - mirror removed on the 2026-04-04 closure pass

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
- `0000000000_0405_s2fresh_r1` Stage3 ep2 cutoff accepted (2026-04-05)
- parent lane verdict: `blocked`
- next action:
  - do not reopen Stage2/3 hierarchy work
  - wait for the remaining Stage4 consumer-side numeric authority / repair-contract seams and the promoted Stage2 persistence tranche to clear
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
  - runtime signal is now positive on Flashback false-positive suppression
  - keep this lane below the newer numeric asset authority / carryover seam
- temp cleanup action:
  - do not remove mirror until combined closure audit completes

### 0_0-stage4-repair-contract-normalization-remediation

- survey/execution seed completed (2026-04-02)
- execution SSOT: `partially_realized`
- primary seams:
  - shared naming and sink visibility for repair-contract metadata
  - provenance persistence for repair/gate surfaces
  - operator-visible scope-authority hygiene
  - phantom mismatch inflation when repair metadata is missing or inconsistently surfaced at readback time
- next action:
  - keep Stage4 paused
  - treat this as a near-front follow-up lane after the consumer umbrella because numeric carryover remediation still depends on clear repair scope/provenance and operator-visible authority
  - treat readback phantom mismatch normalization as the concrete next substrate inside this lane
  - re-audit this execution SSOT against the current workspace state before implementation
- temp cleanup action:
  - keep mirror while this remains a queued metadata/sink follow-up lane; remove only on explicit closure or replacement

### 0_0-stage234-nonwuxia-state-lock-overreach-remediation

- bounded survey and execution SSOT completed (2026-04-06)
- execution SSOT: `partially_realized`
- primary seams:
  - Stage2 producer-side hardening of non-wuxia soft fatigue into `recovery_scene_required` and opening recovery pressure
  - Stage4 opening-authority hardening that treats soft carryover too close to hard canon
  - Stage4 chain-link persistence that can make mild `physical_state` and routine `pending_actions` sticky
  - Stage3 passive carryover seam only if the first-wave Stage2/Stage4 patch leaves residual genre-blind inherited-state pressure
- next action:
  - keep this lane below the current Stage4 consumer/repair pair
  - Stage2 producer tranche is already landed; do not reopen it unless later runtime evidence shows residual producer-side false hardening
  - 2026-04-07 reinspection found no hidden Stage4 landing in the current workspace; treat Stage4 as the real next implementation owner set
  - next bounded step is Stage4 intake/post-pass normalization, not Stage3
  - continue to realize this lane as a bounded dual-owner Stage2 + Stage4 patch rather than a broad cross-stage rewrite
  - preserve `natural healing`
  - preserve true injury continuity while softening false hard-fail pressure for non-wuxia soft-fatigue cases
  - treat Stage3 as optional follow-on only if Stage2/Stage4 normalization is insufficient
- temp cleanup action:
  - keep mirror while this remains a queued bounded P1 lane; remove only on explicit closure, replacement, or strategic deactivation

### 0_0-stage2-contract-normalization-remediation

- global Stage2 production-consumption survey completed (2026-04-02)
- execution SSOT: `partially_realized`
- primary seams:
  - mission truth trapped in `tactical_doc` prose
  - Stage2-owned packet alias ambiguity at emission time
  - low-signal or dropped fields (`beat_sequence`, `hybrid_composition`, `semantic_carryover`)
  - residual artifact-truth false closure and observability debt recorded in the Golden bounded survey
  - broader Stage2 normalization remains open even though the bounded persistence-authority child tranche has landed
- next action:
  - do not reopen the landed persistence-authority child tranche unless a fresh live run or new evidence reopens the seam
  - keep this Stage2 item below the current Stage4 consumer/repair pair and below the new non-wuxia P1 lane
  - keep broader mission-authority, alias, dead-field, Golden artifact-truth, and observability follow-up work deferred inside this SSOT
  - when Stage2 is reactivated, start from a fresh live-run impact check rather than widening from static debt alone
- temp cleanup action:
  - keep mirror while this broader Stage2 SSOT remains partial; remove only on explicit closure or replacement

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
- queue inventory updated again to include the new bounded non-wuxia state-lock overreach execution lane
- new Flashback continuity child lane added directly under the aggregate Stage4 lane
- NpcDrift child lane kept directly below it as the next bounded seam
- existing Stage4 lanes kept as substrate rather than removed
- parent readiness lane remains blocked behind the active Stage4 pair, the new non-wuxia lane, and the broader residual Stage2 lane

### Pass 2. Evidence and Consistency

- canonical and temp paths for the new aggregate lane verified against filesystem
- canonical and temp paths for the new single-episode demo lane verified against filesystem
- canonical and temp paths for the new non-wuxia execution lane verified against filesystem
- ordering is consistent with the latest Stage4 consumer-finalization survey, the latest ep2 bounded canary failure, and the new 2026-04-06 bounded survey plus execution SSOT for non-wuxia state-lock overreach
- the 2026-04-07 workspace reinspection still finds generic Stage4 opening/carryover hardening in code and tests, so the non-wuxia lane remains partial and does not move in queue order
- parked/blocked legacy items remain unchanged

### Pass 3. Execution and Readability

- per-item status ledger updated with concrete next actions
- dependency chain is explicit: Stage4 consumer -> Stage4 repair -> bounded non-wuxia state-lock overreach -> broader Stage2 residual lane -> parent readiness -> parked cross-stage/Stage3/Stage0 waves -> historical substrate lanes
- new bounded non-wuxia P1 lane inserted without disturbing the current Stage4 front pair
- broader residual Stage2 lane kept below the new non-wuxia lane
- new parked Stage3 future wave inserted ahead of the Stage2 future wave without disturbing active Stage4 order
- no overreach: demo utility not promoted to closure proof, Stage4 resume not declared

Confidence: `96%`
