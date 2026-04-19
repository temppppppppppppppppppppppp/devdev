# Stage2 Pacing Arc 2 Rerun Proof

Date: 2026-04-19
Status: final (second bounded family rerun complete; confidence `96/100`)
Canonical Path: `docs/2026-04-19/stage2-pacing-arc2-rerun-proof.md`
Commit State:
- Baseline Commit: `029df1a7`
- Baseline Dirty Summary: `dirty worktree with active canary, runtime, docs, and test deltas already present; this proof note records the second bounded pacing-normalization rerun`
Source Survey Docs:
- `docs/2026-04-19/stage2-pacing-trace-bounded-survey.md`
- `docs/2026-04-19/stage2-pacing-block12-deep-trace.md`
- `docs/2026-04-19/stage2-pacing-opener-rerun-proof.md`
- `docs/2026-04-19/0_0-stage2-pacing-contract-normalization-remediation-execution-ssot.md`
Source Anchors:
- [Pre-patch arc 2 artifact](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage23probe_r1_arc23only_r1/logs/artifacts/stage2/arc_002/attempt_01/final_arc__creative.json:1)
- [Pre-patch arc 2 plan](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage23probe_r1_arc23only_r1/plans/arcs/arc_002.txt:1)
- [Post-patch arc 2 artifact](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage2_arc2_pacing_r1/logs/artifacts/stage2/arc_002/attempt_01/final_arc__balanced.json:1)
- [Post-patch arc 2 plan](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage2_arc2_pacing_r1/plans/arcs/arc_002.txt:1)
- [Post-patch arc 2 canary summary](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage2_arc2_pacing_r1/logs/stage2_canary_summary.json:1)

## Result

The second bounded Stage2 pacing-normalization tranche also produced a real contraction, though milder than the opener family.

- before: `arc_002 ep_count = 6`, `episode range = 7~12`
- after: `arc_002 ep_count = 5`, `episode range = 7~11`

The post-patch arc 2 rerun stayed healthy on the bounded proof run:

- one-arc baseline canary project prepared from `golden_canary_deepclone_probe_a_stage23probe_r1`
- Stage2 rerun target: `2 arcs total`, with `arc_002` regenerated from the preserved `arc_001` baseline
- final verdict: `PASS`
- attempt count: `1`
- final arc count: `2`
- hard gates: `pass`
- `arc_001 end -> arc_002 start` carryover remained aligned

## Interpretation

This is enough to treat the current pacing guard as a partial generalization, not merely an opener-only special case.

The contraction is smaller than the first proof (`6 -> 4` on `arc_001`), which means the heuristic is not simply force-compressing every front family into the same size. Instead, it appears to be separating `loop-heavy prose density` from true `episode-scale expansion` while still leaving room for a heavier tactical block to stay broader than the opener.

That is a healthy signal for this lane:

- `arc_001`: over-allocation dropped sharply
- `arc_002`: over-allocation still dropped, but only by one episode

This pattern is consistent with a bounded normalization pass rather than an indiscriminate compression bug.

## Remaining Scope

What this proof does **not** claim:

- that the Stage2 pacing lane is closed
- that all later blocks will contract
- that raw BI block density is no longer the primary upstream inflation source

What it does justify:

1. bank the opener proof and the arc 2 proof together as the first two positive family checks
2. keep the Stage2 pacing lane `in_progress` until at least one later family is checked
3. treat current pacing normalization as a real behavioral change on live Stage2, not just contract wording cleanup

## Pass 1

- the document records a fresh rerun, not a static comparison only
- the comparison uses pre-patch and post-patch artifacts plus plan files

## Pass 2

- the interpretation stays narrow: partial generalization, not full closure
- the proof distinguishes opener contraction from second-family contraction instead of flattening them into one claim

## Pass 3

- the remaining scope is explicit
- the next natural tranche is a later block family rather than a broad wave

Confidence: 96/100
