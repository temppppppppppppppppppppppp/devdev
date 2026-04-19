# Stage2 Contract Normalization Reactivation Refresh

Date: 2026-04-19
Status: final
Canonical Path: `docs/2026-04-19/stage2-contract-normalization-reactivation-refresh.md`
Baseline Commit: `029df1a74af89a7b5387c449f4723a5df0d000d4`
Baseline Dirty Summary: `dirty worktree with active runtime/canary/docs/test deltas already present; this refresh is a queue-governing current-state re-audit only and does not claim a clean tree`
Source Docs:
- `docs/2026-04-19/stage2-pacing-closure-review.md`
- `docs/2026-04-19/active-temp-execution-roadmap.md`
- `docs/2026-04-11/stage23-current-main-static-parallel-survey.md`
- `docs/2026-04-10/00_000-stage2-fresh-run-post-run-merge-audit.md`
- `docs/2026-04-05/00_0405-stage2-artifact-truth-observability-bounded-survey.md`
- `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
Evidence Surfaces:
- `docs/2026-04-19/stage2-pacing-arc5-rerun-proof.md`
- `docs/temp/queue-state.json`
- `docs/temp/execution-roadmap.md`
Side-Effect Coverage: documentation and queue semantics only

## 1. Question

After the Stage2 pacing lane closed, what is the current front-active reading of `0_0-stage2-contract-normalization-remediation`, and what bounded tranche should it own next?

## 2. Current Reading

The current front-active Stage2 item is no longer the old proof-sink residue around:

- `runtime_advisory`
- `retry_directives`
- `ep_num`
- carryover-authority start-state truth

Those slices are now historical landed backing.

The live Stage2 residue has narrowed to a different family:

- Stage2 artifact packet-to-txt round-trip drift
- opening carryover instruction realization at the state-shell layer
- carried equipment and other start-state facts missing from human-facing state headers
- keep-or-drop / alias clarity where Stage2 emission shells still blur canonical state

In short, the lane is now better read as `state-shell cleanliness plus artifact round-trip normalization`, not as `proof-sink bookkeeping`.

## 3. Why This Lane Reactivates

Three evidence streams now line up:

1. The pacing lane is closed and explicitly hands remaining non-pacing Stage2 residue to this sibling lane.
2. The current roadmap and queue-state now place this item first.
3. The older Stage2 SSOT still talks like the lane is operator-parked behind Stage3 and Stage4, which is stale against the current queue controller.

That means the next honest move is not immediate code patching from the old wording. The next honest move is to refresh the governing Stage2 SSOT so it matches the current queue and residue shape.

## 4. Bounded Next Tranche

The next bounded tranche should stay narrow:

1. refresh the governing execution SSOT against the 2026-04-19 queue state
2. narrow the active owner family to Stage2 artifact emission / state-shell cleanliness
3. treat the first implementation slice as:
   - carryover opening instruction realization
   - state-header completeness for carried facts
   - packet-to-txt round-trip normalization for location/item/state truth
4. defer broader mission-authority rewrite unless the bounded shell cleanup proves insufficient

## 5. Not The Next Tranche

The following are specifically **not** the immediate next patch:

- reopening the old proof-sink bookkeeping tranche
- broad Stage2 mission-authority extraction
- Stage3 contract or opening-transition work
- Stage4 consumer or repair debt
- fresh canary expansion before the governing Stage2 lane is refreshed

## 6. Execution Consequence

This refresh does not change queue ordering.

It does change the meaning of the front Stage2 lane:

- old meaning: broader proof-pending, operator-parked Stage2 normalization
- current meaning: front-active bounded Stage2 shell/round-trip cleanup

The canonical Stage2 SSOT should now say that explicitly.

## Pass 1

- the document is a bounded refresh note, not a new execution SSOT
- the scope is limited to current queue meaning and next-tranche interpretation

## Pass 2

- the claims are grounded in the pacing closure review, the current roadmap, the queue-state, and the older Stage2 survey family
- no new bug claim is introduced without existing evidence

## Pass 3

- the operating consequence is explicit: refresh the canonical Stage2 SSOT first, then start bounded implementation from the refreshed reading
- the lane meaning is narrowed enough to avoid reopening stale proof-sink work by accident

Confidence: `96%`
