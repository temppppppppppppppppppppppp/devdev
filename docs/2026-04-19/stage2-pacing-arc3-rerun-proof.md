# Stage2 Pacing Arc 3 Rerun Proof

Date: 2026-04-19
Status: final (third bounded family rerun complete; confidence `97/100`)
Canonical Path: `docs/2026-04-19/stage2-pacing-arc3-rerun-proof.md`
Commit State:
- Baseline Commit: `029df1a7`
- Baseline Dirty Summary: `dirty worktree with active canary, runtime, docs, and test deltas already present; this proof note records the third bounded pacing-normalization rerun`
Source Survey Docs:
- `docs/2026-04-19/stage2-pacing-trace-bounded-survey.md`
- `docs/2026-04-19/stage2-pacing-block12-deep-trace.md`
- `docs/2026-04-19/stage2-pacing-opener-rerun-proof.md`
- `docs/2026-04-19/stage2-pacing-arc2-rerun-proof.md`
- `docs/2026-04-19/0_0-stage2-pacing-contract-normalization-remediation-execution-ssot.md`
Source Anchors:
- [Pre-patch arc 3 artifact](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage23probe_r1_arc23only_r1/logs/artifacts/stage2/arc_003/attempt_01/final_arc__creative.json:1)
- [Pre-patch arc 3 plan](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage23probe_r1_arc23only_r1/plans/arcs/arc_003.txt:1)
- [Post-patch arc 3 artifact](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage2_arc3_pacing_r1/logs/artifacts/stage2/arc_003/attempt_01/final_arc__conservative.json:1)
- [Post-patch arc 3 plan](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage2_arc3_pacing_r1/plans/arcs/arc_003.txt:1)
- [Post-patch arc 3 canary summary](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage2_arc3_pacing_r1/logs/stage2_canary_summary.json:1)

## Result

The third bounded Stage2 pacing-normalization tranche produced another real contraction, this time beyond the opener-front family.

- before: `arc_003 ep_count = 5`, `episode range = 13~17`
- after: `arc_003 ep_count = 4`, `episode range = 13~16`

The post-patch arc 3 rerun stayed healthy on the bounded proof run:

- two-arc baseline canary project prepared from `golden_canary_deepclone_probe_a_stage23probe_r1`
- Stage2 rerun target: `3 arcs total`, with `arc_003` regenerated from the preserved `arc_001~002` baseline
- final verdict: `PASS`
- attempt count: `1`
- score: `95`
- final arc count: `3`
- hard gates: `pass`
- `arc_002 end -> arc_003 start` carryover remained aligned

## Interpretation

This is the first clear sign that the current pacing guard is not only correcting the opener family.

`arc_002` already suggested partial generalization through a mild contraction (`6 -> 5`). `arc_003` strengthens that read by showing a later family contraction (`5 -> 4`) while preserving one-shot health and carryover alignment. That makes the current signal stronger than "front block cleanup only."

The current pattern now looks like this:

- `arc_001`: `6 -> 4`
- `arc_002`: `6 -> 5`
- `arc_003`: `5 -> 4`

This pattern is consistent with a bounded normalization pass that reduces over-allocation where density had been overstated, without flattening every arc to the same episode count.

## Remaining Scope

What this proof does **not** claim:

- that the Stage2 pacing lane is fully closed
- that every later family will contract again
- that raw BI block density is no longer the dominant upstream cause

What it does justify:

1. treat the current pacing lane as behaviorally proved across three bounded families
2. move the lane closer to `stabilizing` while keeping it `in_progress`
3. use any next tranche to test a genuinely different later-family shape instead of repeating more front-family proofs

## Pass 1

- the document records a fresh rerun rather than only a plan diff
- the proof uses real post-patch canary artifacts and summary state

## Pass 2

- the interpretation is stronger than arc 2 but still bounded
- the document distinguishes `partial generalization` from `full closure`

## Pass 3

- the family pattern is explicit and easy to compare
- the next move is narrowed to a different later-family shape

Confidence: 97/100
