# Stage2 Pacing Trace Bounded Survey

Date: 2026-04-19
Status: final (bounded static survey complete; confidence `97/100`)
Canonical Path: `docs/2026-04-19/stage2-pacing-trace-bounded-survey.md`
Commit State:
- Baseline Commit: `029df1a7`
- Baseline Dirty Summary: `dirty worktree with active canary, runtime, docs, and test deltas already present; this survey is read-only synthesis and does not claim a clean tree`
Source Survey Docs:
- `docs/2026-04-19/0_0-stage2-pacing-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-18/golden-canary-deepclone-probe-a-loop-doctrine-upgrade-plan.md`
- `docs/2026-04-18/golden-canary-deepclone-probe-a-static-cause-hypothesis.md`
Source Anchors:
- [Stage0 handoff contract](/c:/Users/PC/Desktop/글도비/modules/core/stage0_handoff.py:83)
- [Stage0 normalize_treatment_blocks](/c:/Users/PC/Desktop/글도비/modules/core/stage0_handoff.py:194)
- [Stage0 readiness validation](/c:/Users/PC/Desktop/글도비/modules/core/stage0_handoff.py:586)
- [Stage2 orchestrator plot_roadmap ingest](/c:/Users/PC/Desktop/글도비/modules/core/stage2_orchestrator.py:275)
- [Stage2 preflight active generate path](/c:/Users/PC/Desktop/글도비/modules/core/stage2_preflight.py:1981)
- [FourPhase ep_count heuristic](/c:/Users/PC/Desktop/글도비/modules/domain/agents/four_phase_arc_generator.py:450)
- [FourPhase pacing signal payload](/c:/Users/PC/Desktop/글도비/modules/domain/agents/four_phase_arc_generator.py:520)
- [ArcEnsemble suggestion intake](/c:/Users/PC/Desktop/글도비/modules/domain/agents/arc_ensemble.py:1004)
- [ArcEnsemble pace bands](/c:/Users/PC/Desktop/글도비/modules/domain/agents/arc_ensemble.py:1343)
- [ArcEnsemble final pacing ownership](/c:/Users/PC/Desktop/글도비/modules/domain/agents/arc_ensemble.py:1361)
- [ARC_DESIGN_SCHEMA ep_count bound](/c:/Users/PC/Desktop/글도비/modules/core/response_schemas.py:355)
- [Shared Stage2 constants drift](/c:/Users/PC/Desktop/글도비/modules/core/constants.py:239)
- [Active ensemble prompt wording](/c:/Users/PC/Desktop/글도비/config/prompts/ensemble.yaml:40)
- [Fallback analyst prompt wording](/c:/Users/PC/Desktop/글도비/config/prompts/analyst.yaml:292)
- [Legacy analyst prompt mirror](/c:/Users/PC/Desktop/글도비/modules/domain/agents/analyst_prompts.py:305)
- [Probe A BI episodes_per_arc baseline](/c:/Users/PC/Desktop/글도비/bible/0_bi_golden_canary_deepclone_probe_a_fullblock_v1.json:14)
- [Probe A Phase0 ARC-01 block span](/c:/Users/PC/Desktop/글도비/treatments/phase0/golden_canary_deepclone_probe_a_fullblock_v1_phase0_design.json:104)
- [Probe A Phase0 ARC-02 block span](/c:/Users/PC/Desktop/글도비/treatments/phase0/golden_canary_deepclone_probe_a_fullblock_v1_phase0_design.json:134)
- [Probe A Stage2 arc_001 plan](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage23probe_r1_arc23only_r1/plans/arcs/arc_001.txt:7)
- [Probe A Stage2 arc_002 plan](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage23probe_r1_arc23only_r1/plans/arcs/arc_002.txt:7)
- [Probe A Stage2 arc_003 plan](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage23probe_r1_arc23only_r1/plans/arcs/arc_003.txt:7)
- [Probe A Stage3 ep12 continuation](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep12authority_r1/logs/stage3_canary_summary.json:6)
- [Probe A Stage3 ep17 continuation](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep17oneshot_r1/logs/stage3_canary_summary.json:6)

## Executive Summary

The current Stage2 pacing problem is not `donor raw structure directly controls ep_count`.

The live authority chain is:

`translated plot_roadmap block -> enriched curr_block -> FourPhase heuristic suggestion -> ArcEnsemble LLM choice -> pace-mode/schema clamp`

That means current over-allocation risk is better described as:

`material-side block density inflation + heuristic overshoot + stale pacing language mismatch`

Probe A evidence now points to a specific failure shape: the material baseline still looks compact on paper, but the translated block payloads behave like `1 block ~= 1 episode` much more often than a webnovel-style compact opener should.

## Pass 1: Active Authority Trace

- Stage0 hands Stage2 the structured `plot_roadmap`, but it does not create or normalize a live final `ep_count` authority on the normal path. `normalize_treatment_blocks()` preserves incoming fields and readiness validation only checks shape and consumer payload presence, not pacing truth.
- Stage2 then reads `MasterBible.plot_roadmap`, selects the current block, enriches it, and passes `curr_block=enriched_block` into the active FourPhase generate path.
- On the live path, FourPhase recomputes `ep_count_suggestion` from content length, sentence count, and `tension_level`. The key thresholds are already aggressive: `>1500 chars -> 6`, `>=15 sentences -> 5`, then `tension_level >= 8` can add `+1` before clamping.
- ArcEnsemble explicitly tells the model that Python only collected pacing signals and the LLM owns the final `ep_count`. The returned `ep_count` then becomes the working value unless invalid, in which case the suggestion is used.
- Final Stage2 output is clamped twice: by pace family and by schema. Active runtime contract is `compressed=2~3`, `standard=4~5`, `expanded=6`, with schema also allowing `2~6`.

Conclusion from pass 1:

- donor text is not the direct live owner
- translated block density is
- Stage0-side pacing values can drift because the live Stage2 path recomputes suggestion rather than trusting upstream `ep_count`

## Pass 2: Real Probe A Inflation Evidence

Material-side baseline still advertises a compact frame:

- BI says `episodes_per_arc = 5`
- Phase0 sets ARC-01 to Blocks `1~10`
- Phase0 sets ARC-02 to Blocks `11~20`

Observed live Stage2 pacing is much looser:

| Slice | Material baseline | Observed Stage2 result | Signal |
| --- | --- | --- | --- |
| ARC-01 opener | Blocks `1~10` under a `5 eps / arc` baseline | Blocks `1~6 -> 6 episodes` in `arc_001` | opener already expands to max band |
| ARC-01 -> ARC-02 seam | ARC-02 should only begin at Block `11` | Blocks `7~12 -> 6 episodes` in `arc_002` | seam is already treated as full six-episode spread |
| ARC-02 crash cluster | ARC-02 still only spans Blocks `11~20` | Blocks `13~17 -> 5 episodes` in `arc_003` | crash cluster stays near `1 block ~= 1 ep` |

The continuation evidence does not show meaningful downstream recompression:

- Probe A Stage3 already reaches `12` blueprints by `ep12`
- Probe A continuation preserves the same spread through `ep17`

Conclusion from pass 2:

- the pacing pressure is already present before Stage3
- early Probe A block translation is dense enough that the live Stage2 stack keeps reading each block as an episode-scale unit
- the system is not correcting back toward the compact material baseline once that pressure is present

## Pass 3: Contract and Prompt Drift

The schema is mostly aligned with the live contract, but the surrounding language is stale in several places:

- Active ensemble prompt still says `ep_count x 500` and treats `<1500` as a critical reject, while runtime filtering/scoring uses `450 chars / episode`.
- Shared constants still advertise a Stage2 minimum of `3`, even though the active owner and schema both allow `2`.
- FourPhase maintainer-facing wording still says `3~6`, even though the code can legitimately emit `2`.
- Fallback Analyst surfaces still describe slower bands such as `Blitz(3)` or `3~6`, so anyone reading those surfaces gets a slower mental model than the live runtime actually uses.
- Secondary validator wording still tells operators to think in `500 chars / episode`, which reinforces the same stale floor.

Conclusion from pass 3:

- the active pacing contract is already wider and faster than several prompts, constants, and validator messages admit
- stale wording does not fully explain inflation, but it absolutely makes operator diagnosis and fallback behavior noisier
- current system language still overstates how much room Stage2 should take before it is considered too slow

## Classification

Primary cause:

- translated block payloads are too episode-shaped, so FourPhase sees high density before ArcEnsemble even decides pace

Secondary cause:

- FourPhase threshold jumps and pace-mode bands make it easy for already-dense blocks to land at `5~6`

Tertiary cause:

- stale pacing wording across prompts, constants, and validators obscures the real contract and makes slower allocation look more normal than it should

Rejected cause:

- donor raw structure is not directly setting live `ep_count`

## Bounded Execution Consequence

The front pacing lane should stay active, but the next tranche should stay narrow:

1. Trace `Block 1` and `Block 2` end-to-end from raw BI payload into `enriched_block` length, sentence count, and `tension_level`.
2. Normalize active wording so prompts, constants, and validator messages stop contradicting the `2~6 / 450 chars` live contract.
3. Add a compactness distinction between `loop density` and `event density`, so a hook-rich block can still stay in `2~3` episodes when it does not actually contain `5~6` episode-scale turns.
4. Re-run the bounded opener family after normalization and confirm that at least one previously-inflated slice no longer expands unjustifiably.

## Final Judgment

`Stage2 pacing honesty` belongs at the front of the active queue.

The reason is not that the donor is directly overruling the system. The reason is that the translated material contract is currently dense enough, and the runtime contract currently permissive enough, that a compact webnovel unit can still spread into a slower arc than intended. That is now the cleanest upstream risk left.
