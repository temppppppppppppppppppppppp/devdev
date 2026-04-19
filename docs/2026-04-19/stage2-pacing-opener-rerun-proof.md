# Stage2 Pacing Opener Rerun Proof

Date: 2026-04-19
Status: final (bounded rerun complete; confidence `97/100`)
Canonical Path: `docs/2026-04-19/stage2-pacing-opener-rerun-proof.md`
Commit State:
- Baseline Commit: `029df1a7`
- Baseline Dirty Summary: `dirty worktree with active canary, runtime, docs, and test deltas already present; this proof note records the first bounded pacing-normalization rerun`
Source Survey Docs:
- `docs/2026-04-19/stage2-pacing-trace-bounded-survey.md`
- `docs/2026-04-19/stage2-pacing-block12-deep-trace.md`
- `docs/2026-04-19/0_0-stage2-pacing-contract-normalization-remediation-execution-ssot.md`
Source Anchors:
- [Pre-patch opener artifact](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage23probe_r1_arc23only_r1/logs/artifacts/stage2/arc_001/attempt_01/final_arc__creative.json:1)
- [Post-patch opener artifact](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage2_opener_pacing_r1/logs/artifacts/stage2/arc_001/attempt_01/final_arc__balanced.json:1)
- [Post-patch opener plan](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage2_opener_pacing_r1/plans/arcs/arc_001.txt:1)
- [Post-patch opener canary summary](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage2_opener_pacing_r1/logs/stage2_canary_summary.json:1)

## Result

The first bounded Stage2 pacing-normalization tranche produced a real opener contraction.

- before: `arc_001 ep_count = 6`, `pace_mode = expanded`
- after: `arc_001 ep_count = 4`, `pace_mode = standard`

The post-patch opener stayed healthy on the bounded proof run:

- fresh zero-arc canary project prepared from `golden_canary_deepclone_probe_a_stage23probe_r1`
- Stage2 rerun target: `1 arc`
- final verdict: `PASS`
- attempt count: `1`
- final arc count: `1`

## Interpretation

This is enough to say the current heuristic split is not merely cosmetic wording cleanup.

The bounded rerun shows that separating `loop-heavy prose density` from `episode-scale expansion signals` can materially reduce opener over-allocation on the live Stage2 path. The result is not yet a full pacing closure, but the first front-family proof is positive.

## Remaining Scope

What this proof does **not** claim:

- that every opener or every genre family will contract the same way
- that the Stage2 pacing lane is closed
- that later arcs no longer need `loop density` vs `event density` normalization

What it does justify:

1. keep the Stage2 pacing lane as the front active upstream item
2. run at least one more bounded family after the opener
3. treat the current tranche as a real behavioral improvement, not just documentation cleanup
