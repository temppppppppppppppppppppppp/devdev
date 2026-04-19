# Parked Board Compaction Closure Review

Date: 2026-04-19
Status: final
Canonical Path: `docs/2026-04-19/parked-board-compaction-closure-review.md`
Baseline Commit: `029df1a74af89a7b5387c449f4723a5df0d000d4`
Baseline Dirty Summary: `dirty worktree with active runtime/canary/docs/test deltas already present; this review is queue-governing compaction only and does not claim a clean tree`
Source Docs:
- `docs/2026-04-19/active-temp-execution-roadmap.md`
- `docs/temp/queue-state.json`
- `docs/implementation/temp-execution-queue-roadmap-harness.md`
- `docs/implementation/execution-closure-harness.md`
Evidence Surfaces:
- `docs/2026-04-19/active-temp-execution-roadmap.md`
- `docs/temp/queue-state.json`
- `docs/temp/`
Side-Effect Coverage: documentation, temp-queue mirrors, queue-state, and ClickUp mirror only

## 1. Question

Now that every visible parked and blocked candidate has been re-audited for honest queue meaning, should the temp queue keep carrying `historical_backing` mirrors, or is it time to compact the board down to only true parked and blocked items?

## 2. Current Reading

The answer is now clear.

The board has already separated into three classes:

- `parked future wave`
- `blocked holding`
- `historical backing only`

Only the first two classes still belong on the live temp queue surface.

The third class no longer needs `docs/temp/` mirrors because:

- the canonical dated execution SSOTs already preserve the evidence and rationale
- the board no longer treats those items as live workload
- keeping them in `docs/temp/` inflates `active_item_count` and makes the parked board look busier than it really is

That means the next honest move is queue compaction, not more per-item refresh work.

## 3. Compaction Decision

Compaction verdict: `go`

Compaction rule:

- keep temp mirrors only for:
  - `parked future wave`
  - `blocked holding`
- remove temp mirrors for:
  - `historical backing only`

Canonical dated docs remain authoritative and are not deleted.

## 4. Items To Compact Out Of `docs/temp/`

These items should leave the temp queue surface in this wave:

- `0_0-stage234-arc23-post-patch-rerun-proof`
- `0_0-stage234-global-authority-alignment-bounded-remediation`
- `0_0-stage234-cross-stage-contract-normalization-remediation`
- `0_0-stage234-nonwuxia-state-lock-overreach-remediation`
- `0_0-stage4-partial-fix-hardening-remediation`
- `0_0-stage3-partial-fix-hardening-remediation`
- `0_0-stage2-partial-fix-hardening-remediation`
- `0_0-stage34-ep2-single-episode-demo-canary`
- `0_0-stage4-ep2-advisory-escalation-loop-remediation`
- `0_0-stage4-canonical-entity-postselect-remediation`
- `0_0-stage4-flashback-continuity-localfix-remediation`
- `0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation`

## 5. Items That Must Stay On The Live Board

These still deserve temp mirrors because they remain the true visible queue:

- `0_0-stage4-interview-round-owner-surface-reduction-remediation`
- `stage0-treatment-enrich-retirement-remediation`
- `stage0-bi-tr-production-harness-normalization-remediation`
- `0_0-stage2-stage3-stage4-readiness-remediation`
- `frontier-lag-soak-canary-wave1`
- `npc-martial-state-substrate-wave1`

## 6. Operating Consequence

After compaction:

1. the canonical roadmap remains authoritative
2. the temp roadmap remains present because the queue is not empty
3. `docs/temp/queue-state.json` should shrink to only the six true live queue items
4. ClickUp should mirror the compacted queue surface rather than the old inflated queue count

## 7. Residual Risk

- some canonical historical-backing execution SSOTs still keep old `in_progress` wording internally
- that is tolerated in this wave because the queue controller already demotes them out of the live surface
- a later archival wording sweep may normalize those canonical docs, but it is not required for honest temp-queue compaction

## Pass 1

- this document is a queue-compaction closure review, not a new execution SSOT
- the scope is limited to temp-queue membership and mirror cleanup

## Pass 2

- the compaction set is grounded in the current roadmap and queue-state semantics
- the keep/remove split is explicit enough to avoid accidental deletion of still-live parked or blocked items

## Pass 3

- the operating consequence is actionable: remove historical-backing temp mirrors and keep only the six real queue items
- the document avoids conflating canonical evidence preservation with temp-queue membership

Confidence: 97/100
