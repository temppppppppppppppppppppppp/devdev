# Active Temp Execution Roadmap

Date: 2026-04-01
Status: active (3-pass audited, Stage4 consumer-contract aggregate active; NpcDrift relation-tag child lane code-landed, runtime proof pending)
Canonical Path: `docs/2026-04-01/active-temp-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Baseline Commit: `fd1707372bd7eb8ad23a5d4506ef556e3f72cc51`
Baseline Dirty Summary: `dirty: 0_0 runtime logs/db/artifacts active; legacy temp queue mirrors present; 2026-03-31 0_0 survey docs untracked`
Resume Commit: `09a7b478c2a2c16d708cc041aaa6e194278e7f9b`
Resume Drift Summary: `new dominant blocker isolated to Stage4 split canonical truth; canonical-entity/post-select lane inserted ahead of parent readiness closure`
Supersedes:
- `docs/2026-03-31/active-temp-execution-roadmap.md`

Queue Snapshot:
- `docs/temp/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
- `docs/temp/0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation-execution-ssot.md`
- `docs/temp/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md`
- `docs/temp/0_0-stage4-post-select-continuity-contract-normalization-remediation-execution-ssot.md`
- `docs/temp/0_0-stage4-fixpack-finalization-remediation-execution-ssot.md`
- `docs/temp/0_0-stage4-canonical-entity-postselect-remediation-execution-ssot.md`
- `docs/temp/0_0-stage4-ep2-advisory-escalation-loop-remediation-execution-ssot.md`
- `docs/temp/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md`
- `docs/temp/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
- `docs/temp/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
- `docs/temp/frontier-lag-soak-canary-wave1-execution-ssot.md`
- `docs/temp/npc-martial-state-substrate-wave1-execution-ssot.md`

## 1. Purpose

This roadmap is the active controller for the current `docs/temp/` execution queue.

This refresh inserts the new aggregate Stage4 consumer-contract lane ahead of the prior Stage4/runtime items:

1. `0_0-stage4-consumer-contract-normalization-remediation` (new highest priority aggregate Stage4 wave)
2. `0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation` (new direct child lane; latest ep2 bounded canary isolated this as the live dominant blocker)
3. `0_0-stage4-post-select-continuity-contract-normalization-remediation` (partial substrate; solved subtype persistence but not the broader consumer contract family)
4. `0_0-stage4-fixpack-finalization-remediation` (partial substrate; solved missing-fix-pack flattening but not the broader consumer contract family)
5. `0_0-stage4-canonical-entity-postselect-remediation` (partial substrate; moved the blocker forward but did not close Stage4)
6. `0_0-stage2-stage3-stage4-readiness-remediation` (blocked; Stage4 still not closure-ready)
7. `0_0-stage4-ep2-advisory-escalation-loop-remediation` (partial substrate; Flashback FP suppressed, but ep2 remained blocked by NpcDrift relation-tag drift)
8. `0_0-stage234-cross-stage-contract-normalization-remediation` (parked future wave; long-term shared contract substrate)
9. `0_0-stage3-contract-tightening-remediation` (new parked future wave; static survey-backed, explicit canary proof pending)
10. `0_0-stage2-contract-normalization-remediation` (parked future wave; survey-backed, below active Stage4 seams and below the nearer Stage3 future wave)

The new lane outranks all other items because:

- the latest global Stage4 consumer-finalization survey showed the dominant residual blocker is broader than any one existing Stage4 seam
- the latest bounded ep2 canary failure then isolated one concrete Stage4 child seam inside that broader family: `NpcDrift relation_to_protag` compressed-tag drift plus missing local-fix synthesis
- the remaining debt clusters into one aggregate family: intake prose flattening, finalization contract loss, and post-pass split truth
- the parent upstream lane is now blocked by Stage4 finalization, not by Stage2/3 hierarchy
- the existing Stage4 lanes produced useful substrate, but none alone closes the aggregate consumer-side contract family
- the new cross-stage matrix survey proved a real long-term substrate wave is needed, but it remains parked behind the active Stage4 queue
- the remaining legacy temp items were already `parked` or `blocked`
- the new Stage3 and Stage2 future waves are intentionally parked and do not reorder the active Stage4 stack

## 2. Queue Inventory

| Item | Canonical Path | Temp Path | Status | Notes |
| --- | --- | --- | --- | --- |
| `0_0-stage4-consumer-contract-normalization-remediation` | `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md` | partial | aggregate Stage4 contract wave active; child NpcDrift lane code-landed, runtime proof pending |
| `0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation` | `docs/2026-04-02/0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation-execution-ssot.md` | partial | code landed; static validation closed; ep2 runtime proof still pending |
| `0_0-stage234-cross-stage-contract-normalization-remediation` | `docs/2026-04-02/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md` | `docs/temp/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md` | parked | long-term shared vocabulary and source-of-truth substrate; survey-backed; held below active Stage4 work |
| `0_0-stage4-post-select-continuity-contract-normalization-remediation` | `docs/2026-04-02/0_0-stage4-post-select-continuity-contract-normalization-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-post-select-continuity-contract-normalization-remediation-execution-ssot.md` | partial | code landed; static validation closed; runtime proof deferred |
| `0_0-stage4-fixpack-finalization-remediation` | `docs/2026-04-02/0_0-stage4-fixpack-finalization-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-fixpack-finalization-remediation-execution-ssot.md` | partial | code landed; static validation closed; runtime proof deferred |
| `0_0-stage4-canonical-entity-postselect-remediation` | `docs/2026-04-01/0_0-stage4-canonical-entity-postselect-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-canonical-entity-postselect-remediation-execution-ssot.md` | partial | runtime partial proof captured; moved the blocker forward into Stage4 finalization |
| `0_0-stage2-stage3-stage4-readiness-remediation` | `docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md` | `docs/temp/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md` | blocked | Stage3 no longer dominant blocker; parent lane still blocked by unresolved Stage4 finalization seams |
| `0_0-stage4-ep2-advisory-escalation-loop-remediation` | `docs/2026-04-01/0_0-stage4-ep2-advisory-escalation-loop-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-ep2-advisory-escalation-loop-remediation-execution-ssot.md` | partial | T1-T3 show positive runtime signal at ep2, but combined Stage4 closure still pending |
| `0_0-stage3-contract-tightening-remediation` | `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md` | `docs/temp/0_0-stage3-contract-tightening-remediation-execution-ssot.md` | parked | narrowed future wave; binding and semantic-handoff enforcement only; tier-2.5 canary prepared but not executed |
| `0_0-stage2-contract-normalization-remediation` | `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md` | `docs/temp/0_0-stage2-contract-normalization-remediation-execution-ssot.md` | parked | narrowed future upstream wave; Stage2 packet extraction and keep-drop normalization only |
| `frontier-lag-soak-canary-wave1` | `docs/2026-03-27/frontier-lag-soak-canary-wave1-execution-ssot.md` | `docs/temp/frontier-lag-soak-canary-wave1-execution-ssot.md` | parked | non-critical soak lane |
| `npc-martial-state-substrate-wave1` | `docs/2026-03-27/npc-martial-state-substrate-wave1-execution-ssot.md` | `docs/temp/npc-martial-state-substrate-wave1-execution-ssot.md` | blocked | awaits fresh evidence and explicit reactivation |

## 3. Dependency Notes

- `0_0-stage4-consumer-contract-normalization-remediation` is now the aggregate Stage4 contract wave and the highest-level dependency for any parent-lane advancement.
- `0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation` is now the immediate live child seam under the aggregate Stage4 wave because the latest bounded canary showed it is the direct ep2 blocker after Flashback false positives were suppressed.
- `0_0-stage234-cross-stage-contract-normalization-remediation` is a parked long-term substrate wave; it should not outrank active Stage4 work, but it now outranks ad hoc simplification discussion because the matrix survey proved the debt structure explicitly.
- `0_0-stage4-post-select-continuity-contract-normalization-remediation` is now the direct active seam for advancing Stage4 beyond the residual ep4 final-round downgrade boundary.
- `0_0-stage4-fixpack-finalization-remediation` remains substrate for this new lane.
- `0_0-stage4-canonical-entity-postselect-remediation` produced positive runtime signal but did not close; it now serves as substrate for the new finalization lane.
- `0_0-stage2-stage3-stage4-readiness-remediation` is no longer waiting on upstream Stage3 normalization evidence; it is blocked by unresolved Stage4 finalization seams.
- `0_0-stage4-ep2-advisory-escalation-loop-remediation` remains useful substrate and now has positive ep2 runtime signal, but it still cannot be closed independently of the broader Stage4 finalization outcome.
- `0_0-stage3-contract-tightening-remediation` is intentionally parked; the immediate next artifact is a tier-2.5 canary proof, not execution realization.
- `0_0-stage2-contract-normalization-remediation` is intentionally parked; the immediate upstream action is Stage3 static survey, not Stage2 realization.
- `0_0-stage3-semantic-fidelity-remediation` is closed via `docs/2026-04-01/0_0-stage3-semantic-fidelity-runtime-closure-audit.md`.
- `frontier-lag-soak-canary-wave1` stays parked; it is not a prerequisite for the active 0_0 lanes.
- `npc-martial-state-substrate-wave1` stays blocked and does not constrain any active lane.

## 4. Execution Order

1. `0_0-stage4-consumer-contract-normalization-remediation`
2. `0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation`
3. `0_0-stage4-post-select-continuity-contract-normalization-remediation`
4. `0_0-stage4-fixpack-finalization-remediation`
5. `0_0-stage4-canonical-entity-postselect-remediation`
6. `0_0-stage2-stage3-stage4-readiness-remediation`
7. `0_0-stage4-ep2-advisory-escalation-loop-remediation`
8. `0_0-stage234-cross-stage-contract-normalization-remediation`
9. `0_0-stage3-contract-tightening-remediation`
10. `0_0-stage2-contract-normalization-remediation`
11. `frontier-lag-soak-canary-wave1`
12. `npc-martial-state-substrate-wave1`

Order rationale:

- priority 1 is the new aggregate Stage4 consumer-contract wave because the latest survey proved the residual blocker is broader than any one existing Stage4 patch lane
- priority 2 is the new NpcDrift relation-tag child lane because the latest bounded canary isolated it as the immediate live blocker
- priority 3 is the post-select continuity-contract substrate lane
- priority 4 is the fix-pack/finalization substrate lane
- priority 5 is the canonical-entity/postselect substrate lane
- priority 6 is the parent upstream lane, still blocked specifically by unresolved Stage4 seams
- priority 7 is the already-landed ep2 advisory substrate lane
- priority 8 is the new parked cross-stage contract substrate wave, justified by the completed matrix survey but still below active Stage4 work
- priority 9 is the parked Stage3 future wave, closer to current evidence than the Stage2 future wave but still not active
- priority 10 is the parked Stage2 future wave
- priority 11 remains a parked soak lane
- priority 12 remains blocked and cannot outrank an executable lane

## 5. Per-Item Status Ledger

### 0_0-stage4-consumer-contract-normalization-remediation

- global Stage4 consumer-finalization survey completed (2026-04-02)
- execution SSOT: `pending`
- primary seams:
  - intake prose flattening of canonical truth
  - fix-pack provenance and routing ambiguity
  - post-select bounded-repair flattening
  - post-pass split truth across `final_state_updates`, `actual_truth`, and `world_state`
- next action:
  - keep Stage4 paused
  - treat the new NpcDrift relation-tag lane as the immediate active child seam
  - treat existing Stage4 partial lanes as substrate
  - do not start realization from this document until explicit operator direction
- temp cleanup action:
  - keep mirror while this remains the aggregate Stage4 contract lane; remove only on explicit closure or replacement

### 0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation

- bounded survey completed (2026-04-02)
- execution SSOT: `pending`
- primary seams:
  - compressed `relation_to_protag` canonical tags have no semantic-expansion bridge
  - `NpcDrift` relation-tag drift is escalated too coarsely for this subtype
  - advisory-only relation-tag drift cannot synthesize bounded local fix contracts from zero
- next action:
  - keep Stage4 paused
  - treat this as the direct child seam under the aggregate Stage4 wave
  - do not widen into broad NpcDrift rewrite before bounded realization is attempted
- temp cleanup action:
  - keep mirror while this remains the live child seam; remove only on explicit closure or replacement

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
  - runtime signal is now positive on Flashback suppression, but the latest ep2 bounded canary isolated `NpcDrift relation_to_protag` as the remaining blocker
  - still defer final closure until the NpcDrift child seam and the broader Stage4 finalization seam are closed
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
- new NpcDrift child lane added directly under the aggregate Stage4 lane
- existing Stage4 lanes kept as substrate rather than removed
- parent readiness lane remains blocked behind Stage4

### Pass 2. Evidence and Consistency

- canonical and temp paths for the new aggregate lane verified against filesystem
- ordering is consistent with the latest Stage4 consumer-finalization survey and the latest ep2 bounded canary failure
- parked/blocked legacy items remain unchanged

### Pass 3. Execution and Readability

- per-item status ledger updated with concrete next actions
- dependency chain is explicit: aggregate Stage4 contract wave -> NpcDrift child lane -> substrate lanes -> parent readiness -> later runtime proof -> Stage4 resume decision
- new parked Stage2 future wave inserted without disturbing active Stage4 order
- new parked Stage3 future wave inserted ahead of the Stage2 future wave without disturbing active Stage4 order
- no overreach: canary not promoted, Stage4 resume not declared

Confidence: `96%`
