# Stage2 Pacing Arc 4 Rerun Proof

Date: 2026-04-19
Status: final (fourth bounded family rerun complete; confidence `97/100`)
Canonical Path: `docs/2026-04-19/stage2-pacing-arc4-rerun-proof.md`
Commit State:
- Baseline Commit: `029df1a7`
- Baseline Dirty Summary: `dirty worktree with active canary, runtime, docs, and test deltas already present; this proof note records the fourth bounded pacing-normalization rerun`
Source Survey Docs:
- `docs/2026-04-19/stage2-pacing-trace-bounded-survey.md`
- `docs/2026-04-19/stage2-pacing-block12-deep-trace.md`
- `docs/2026-04-19/stage2-pacing-opener-rerun-proof.md`
- `docs/2026-04-19/stage2-pacing-arc2-rerun-proof.md`
- `docs/2026-04-19/stage2-pacing-arc3-rerun-proof.md`
- `docs/2026-04-19/0_0-stage2-pacing-contract-normalization-remediation-execution-ssot.md`
Source Anchors:
- [Pre-patch arc 4 artifact](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage24_arc4_r1/logs/artifacts/stage2/arc_004/attempt_01/final_arc__creative.json:1)
- [Pre-patch arc 4 plan](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage24_arc4_r1/plans/arcs/arc_004.txt:1)
- [Post-patch arc 4 artifact](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage2_arc4_pacing_r1/logs/artifacts/stage2/arc_004/attempt_01/final_arc__conservative.json:1)
- [Post-patch arc 4 plan](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage2_arc4_pacing_r1/plans/arcs/arc_004.txt:1)
- [Post-patch arc 4 canary summary](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage2_arc4_pacing_r1/logs/stage2_canary_summary.json:1)

## Result

The fourth bounded Stage2 pacing-normalization tranche produced another real contraction on a later family.

- before: `arc_004 ep_count = 5`, `episode range = 18~22`
- after: `arc_004 ep_count = 4`, `episode range = 18~21`

The post-patch arc 4 rerun stayed healthy on the bounded proof run:

- three-arc baseline canary project prepared from `golden_canary_deepclone_probe_a_stage23probe_r1`
- Stage2 rerun target: `4 arcs total`, with `arc_004` regenerated from the preserved `arc_001~003` baseline
- final verdict: `PASS`
- attempt count: `1`
- score: `100`
- final arc count: `4`
- hard gates: `pass`
- `arc_003 end -> arc_004 start` carryover remained aligned

## Interpretation

This strengthens the current reading from "partial generalization" toward "stabilizing bounded generalization."

The later-family shape did not bounce back to the old 5-episode allocation. Instead, it contracted to 4 while preserving one-shot health and clean carryover. That means the pacing guard is still producing reductions after the opener-front lane and after the first later-family check.

The current bounded pattern is now:

- `arc_001`: `6 -> 4`
- `arc_002`: `6 -> 5`
- `arc_003`: `5 -> 4`
- `arc_004`: `5 -> 4`

This no longer looks like a single-family correction. It looks like a consistent normalization tendency across four bounded families, with heavier blocks still allowed to remain broader than the opener when needed.

## Remaining Scope

What this proof does **not** claim:

- that the Stage2 pacing lane is fully closed
- that every remaining family will keep contracting
- that BI-side raw block density is no longer the dominant inflation source

What it does justify:

1. treat the current pacing lane as `stabilizing` rather than merely exploratory
2. stop repeating the same front or early-middle family proofs unless a regression appears
3. choose any next tranche from a genuinely different later-family shape or convert effort into closure criteria review

## Pass 1

- the document records a fresh rerun with preserved prior-arc baseline
- the proof anchors to real pre/post artifacts and the new canary summary

## Pass 2

- the interpretation is stronger than arc 3 but still bounded
- the document does not overclaim full closure

## Pass 3

- the four-family pattern is explicit
- the next move is narrowed to either different-family validation or lane stabilization review

Confidence: 97/100
