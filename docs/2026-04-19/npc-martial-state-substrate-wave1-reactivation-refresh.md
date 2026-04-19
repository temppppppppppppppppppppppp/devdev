# NPC Martial State Substrate Wave1 Reactivation Refresh

Date: 2026-04-19
Status: final
Canonical Path: `docs/2026-04-19/npc-martial-state-substrate-wave1-reactivation-refresh.md`
Baseline Commit: `029df1a74af89a7b5387c449f4723a5df0d000d4`
Baseline Dirty Summary: `dirty worktree with active runtime/canary/docs/test deltas already present; this refresh is a queue-governing current-state re-audit only and does not claim a clean tree`
Source Docs:
- `docs/2026-04-19/active-temp-execution-roadmap.md`
- `docs/2026-03-27/npc-martial-state-substrate-wave1-execution-ssot.md`
- `docs/2026-04-19/frontier-lag-soak-canary-wave1-reactivation-refresh.md`
- `docs/2026-03-27/frontier-lag-soak-canary-wave1-execution-ssot.md`
Evidence Surfaces:
- `docs/2026-03-27/npc-martial-state-substrate-wave1-execution-ssot.md`
- `docs/2026-03-27/npc-technique-realm-execution-readiness-deep-dive-audit.md`
- `docs/2026-04-19/active-temp-execution-roadmap.md`
Side-Effect Coverage: documentation and queue semantics only

## 1. Question

After the queue has been compacted into parked mode and the frontier soak lane has been reclassified as parked low-priority validation debt, should `npc-martial-state-substrate-wave1` still remain `blocked holding`, or has it become stale blocked debt that should be removed from the visible queue?

## 2. Current Reading

The old SSOT stayed `blocked` because:

- the storage-only substrate wave had already partially landed
- the later hotfix seam was narrowed to the Stage 4 / STV pre-persistence normalization boundary
- queue authority had already determined that no fresh bounded diff or live wuxia canary seam remained on that boundary

The current board state changes the lane's rank, but not its blocker truth:

- this lane is not a current runtime blocker
- the partially landed storage substrate is still real
- the remaining follow-up is still real in principle:
  - Stage 4 / STV pre-persistence martial-shape normalization
  - fresh wuxia seam evidence before a resumed NPC-martial wave
- but the queue still lacks the reopen condition that this SSOT itself declared:
  - a fresh bounded diff on the declared seam, or
  - fresh survey evidence justifying reopen

That means this lane is not stale.

It is still preserved blocked follow-up debt.
It should remain `blocked holding`, not promoted and not closed.

## 3. Family Boundary

This lane now reads as:

- a blocked historical substrate follow-up
- a future Stage 4 / STV seam hotfix candidate
- a preserved martial-state context lane that remains separate from the parked frontier soak validation lane

This lane does **not** now read as:

- a front-active implementation lane
- a parked future wave that can resume without new evidence
- a hidden continuation of the frontier soak lane
- a closure-ready historical backing lane

## 4. Why The Existing `Blocked` Wording Still Needs Refresh

The current `blocked` status is still directionally right, but it lacks today's queue context.

The honest current reading is:

- the storage substrate is already partially landed
- the remaining hotfix seam is still concrete
- but there is still no fresh Stage 4 / STV seam diff or new wuxia evidence to justify reopening
- so this lane should remain visible as blocked follow-up context only

That means the lane should stay on the board with blocked semantics, not be upgraded to parked progress and not be silently archived.

## 5. Operating Consequence

The next honest move is:

1. keep `npc-martial-state-substrate-wave1` on the active roadmap
2. keep its temp mirror in place
3. preserve it explicitly as `blocked holding`
4. require fresh bounded Stage 4 / STV seam evidence before any implementation reactivation

## 6. Not The Next Tranche

The following are specifically **not** the automatic next action for this lane:

- pretending this is the current system front item
- downgrading it to a normal parked future wave without new evidence
- closing it just because the queue is now parked overall
- resuming martial-state code work without a fresh bounded seam diff or fresh survey evidence

## Pass 1

- this document is a current-state refresh note, not a new execution SSOT
- the scope is limited to queue meaning, lane ownership, and blocked-candidate honesty

## Pass 2

- the claims are grounded in the existing npc-martial SSOT, the adjacent frontier soak refresh, and the current roadmap
- the reopen condition remains explicit enough to avoid false promotion or false closure

## Pass 3

- the operating consequence is actionable: keep this lane blocked and visible
- the document avoids pretending that preserved blocked debt is either stale or queue-ready

Confidence: 97/100
