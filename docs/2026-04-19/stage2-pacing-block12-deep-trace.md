# Stage2 Pacing Block 1-2 Deep Trace

Date: 2026-04-19
Status: final (bounded trace complete; confidence `98/100`)
Canonical Path: `docs/2026-04-19/stage2-pacing-block12-deep-trace.md`
Commit State:
- Baseline Commit: `029df1a7`
- Baseline Dirty Summary: `dirty worktree with active canary, runtime, docs, and test deltas already present; this trace is bounded evidence plus contract wording normalization`
Source Survey Docs:
- `docs/2026-04-19/stage2-pacing-trace-bounded-survey.md`
- `docs/2026-04-19/0_0-stage2-pacing-contract-normalization-remediation-execution-ssot.md`
Source Anchors:
- [Probe A BI Block 1](/c:/Users/PC/Desktop/글도비/bible/0_bi_golden_canary_deepclone_probe_a_fullblock_v1.json:1481)
- [Probe A BI Block 2](/c:/Users/PC/Desktop/글도비/bible/0_bi_golden_canary_deepclone_probe_a_fullblock_v1.json:1594)
- [Analyst enrich_raw_block_async merge behavior](/c:/Users/PC/Desktop/글도비/modules/domain/agents/analyst.py:1421)
- [FourPhase ep_count heuristic](/c:/Users/PC/Desktop/글도비/modules/domain/agents/four_phase_arc_generator.py:454)
- [Probe A Stage2 arc_001 plan](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage23probe_r1_arc23only_r1/plans/arcs/arc_001.txt:7)

## Question

Which fields are actually inflating opener pacing for `Block 1` and `Block 2`?

## Raw Block Findings

`Block 1` already crosses the max-band threshold before any Stage2 enrichment salvage.

- raw heuristic payload fields used by FourPhase: `context`, `event_villain`, `solution`, `reward`, `content`
- measured concatenated length: `1537 chars`
- measured split sentence count: `65`
- `tension_level = 6`
- FourPhase result on raw payload alone: `6 episodes`
- governing branch: `content_len > 1500 -> max_ep_count`

`Block 2` also lands at the max band before any later recompression logic.

- measured concatenated length: `986 chars`
- measured split sentence count: `44`
- `tension_level = 8`
- pre-tension heuristic result: `5 episodes`
- tension adjustment: `+1`
- final raw heuristic result: `6 episodes`

## Enrichment Findings

For the sampled enrich logs, the analyst enrichment layer did not introduce the newer pacing-heavy fields that would explain the opener inflation by itself.

- sampled enrich outputs for Blocks `1` and `2` added `joint_docs` and `status_shadow`
- sampled outputs did **not** add `block_theme`, `constraint_summary`, `episode_details`, `plot_suspension`, `work_focus`, or `must_focus`
- recomputing the FourPhase heuristic on the sampled enriched outputs produced the same opener result as the raw inputs

This means the current opener inflation is not primarily caused by enrichment adding a second dense payload layer. The raw BI block bodies are already episode-shaped enough to trigger the high band directly.

## Judgment

For the opener family, the first-order inflation source is:

`raw BI block density -> FourPhase heuristic max-band decision`

not:

`Stage2 enrichment adds too many new pacing fields`

That matters because the first repair tranche should not start with a large enrich refactor. The honest first moves are:

1. normalize surrounding pacing language to the live contract
2. separate `loop density` from `event density` in the heuristic or in the pre-heuristic payload
3. only then decide whether a deeper material-side rewrite is necessary
