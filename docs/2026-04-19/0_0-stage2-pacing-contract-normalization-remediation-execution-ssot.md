# 0_0 Stage2 Pacing Contract Normalization Remediation Execution SSOT

Date: 2026-04-19
Status: closed (closure-review passed on 2026-04-19; the bounded five-family contraction set satisfies the lane exit criteria, and remaining carryover or state-header repair noise is now explicitly classified as adjacent non-pacing state-shell cleanliness under sibling Stage2 contract normalization work)
Canonical Path: `docs/2026-04-19/0_0-stage2-pacing-contract-normalization-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage2-pacing-contract-normalization-remediation-execution-ssot.md` (removed during the 2026-04-19 closure cleanup)
Commit State:
- Baseline Commit: `029df1a74af89a7b5387c449f4723a5df0d000d4`
- Baseline Dirty Summary: `dirty worktree with active canary, runtime, docs, and test deltas already present; this SSOT is queue/document refresh only and does not claim a clean tree`
Source Survey Docs:
- `docs/2026-04-19/stage2-pacing-arc5-rerun-proof.md`
- `docs/2026-04-19/stage2-pacing-arc4-rerun-proof.md`
- `docs/2026-04-19/stage2-pacing-arc3-rerun-proof.md`
- `docs/2026-04-19/stage2-pacing-arc2-rerun-proof.md`
- `docs/2026-04-19/stage2-pacing-opener-rerun-proof.md`
- `docs/2026-04-19/stage2-pacing-block12-deep-trace.md`
- `docs/2026-04-19/stage2-pacing-trace-bounded-survey.md`
- `docs/2026-04-18/golden-canary-deepclone-probe-a-loop-doctrine-upgrade-plan.md`
- `docs/2026-04-18/golden-canary-deepclone-probe-a-static-cause-hypothesis.md`
Source Anchors:
- [Stage2 orchestrator BI handoff](/c:/Users/PC/Desktop/글도비/modules/core/stage2_orchestrator.py:302)
- [Stage2 batch enrich entry](/c:/Users/PC/Desktop/글도비/modules/core/stage2_orchestrator.py:478)
- [Stage2 preflight enrichment into FourPhase](/c:/Users/PC/Desktop/글도비/modules/core/stage2_preflight.py:2056)
- [FourPhase ep_count heuristic](/c:/Users/PC/Desktop/글도비/modules/domain/agents/four_phase_arc_generator.py:454)
- [Arc ensemble ep_count suggestion intake](/c:/Users/PC/Desktop/글도비/modules/domain/agents/arc_ensemble.py:1015)
- [Arc ensemble pacing ownership rules](/c:/Users/PC/Desktop/글도비/modules/domain/agents/arc_ensemble.py:1381)
- [Arc ensemble pace-mode clamp](/c:/Users/PC/Desktop/글도비/modules/domain/agents/arc_ensemble.py:1412)
- [Stage0 to Stage2 plot_roadmap projection](/c:/Users/PC/Desktop/글도비/modules/core/stage0_handoff.py:254)
- [Legacy analyst pacing prompt mismatch](/c:/Users/PC/Desktop/글도비/modules/domain/agents/analyst_prompts.py:305)
- [Runtime ep_count schema bound](/c:/Users/PC/Desktop/글도비/modules/core/response_schemas.py:372)

## Executive Summary

Stage2 pacing is not currently driven by raw donor text. It is driven by the translated Stage0 or BI-side `plot_roadmap` block, the Stage2-enriched `curr_block`, and then a mixed Python plus LLM pacing contract. That means donor doctrine can still distort pacing, but only after it has been translated into material-side block payload.

The main risk is not "donor direct control." The main risk is `translated block density inflation -> heuristic overestimation -> permissive pacing language mismatch -> episode over-allocation`.

The current bounded proofs now show repeated positive contraction signals on live Stage2:

- `arc_001`: `6 -> 4`
- `arc_002`: `6 -> 5`
- `arc_003`: `5 -> 4`
- `arc_004`: `5 -> 4`
- `arc_005`: `4 -> 3`

That is enough to close the lane as a realized pacing-normalization item. The remaining noise seen in the latest families no longer changes the pacing claim itself and now belongs to sibling non-pacing cleanup lanes.

## Current Contract

The current active Stage2 path is:

1. Stage2 reads `MasterBible.plot_roadmap` as the structured upstream source.
2. Stage2 enriches the selected roadmap block into `enriched_block`.
3. Stage2 preflight passes `enriched_block` into `four_phase.generate(...)`.
4. FourPhase computes an `ep_count` suggestion from text length, sentence count, and `tension_level`.
5. ArcEnsemble receives the suggestion, shows Python-collected pacing signals to the LLM, and lets the LLM choose the final `ep_count`.
6. The final result is clamped back into schema and pace-mode bounds.

This means the system currently has two pacing shapers:

- upstream translated block density
- runtime pacing heuristics and clamps

## Why This Is Now Front Priority

Recent queue work closed multiple downstream false-positive and retry families, but the remaining medium-horizon risk is now upstream pacing honesty.

If Stage2 still over-allocates episodes for a block that should stay compact, then:

- Stage2 can emit a diluted tactical surface even when downstream contracts are cleaner
- Stage3 can inherit stretched opening, replay, and seam pressure that is not actually required by the story unit
- donor doctrine evaluation becomes noisy because "loop gain" and "episode inflation" are mixed together

The current question is therefore no longer secondary. It directly affects whether the current Probe A uplift is being measured honestly.

## Concrete Problem Statement

The active workspace now needs one bounded Stage2 pacing normalization lane that answers four questions:

1. Which upstream fields in `plot_roadmap` or `curr_block` are actually pushing `ep_count` up?
2. Where do current runtime heuristics still allow a `3-episode` story unit to spread toward `5-6` episodes?
3. Which prompt or contract surfaces still describe stale pacing bands that do not match the current runtime clamp?
4. How should donor-translated pacing signals be represented so they guide density without directly inflating episode count?

## Immediate Hypotheses

The most likely near-term causes are:

- `curr_block` payloads are too broad or too narratively saturated after translation, so the Python heuristic reads them as high-density even when they should stay compact.
- legacy pacing instructions still describe wider or slower pacing families than the current bounded runtime contract.
- Stage2 still lacks a sharper distinction between:
  - `event density`
  - `loop density`
  - `exposition density`

That distinction matters because donor-inspired doctrine often increases named hooks and payoff surfaces without requiring more episodes.

## Bounded Remediation Scope

This execution lane is intentionally narrow.

In scope:

- trace the real `ep_count` input chain for active Probe A blocks
- compare upstream block `ep_count`, FourPhase suggestion, and final ArcEnsemble result
- normalize mismatched pacing language across producer-facing surfaces
- add bounded proof around known "should be compact" blocks

Out of scope:

- broad donor redesign
- reopening unrelated Stage3 or Stage4 proof lanes
- changing the donor packet itself before the pacing chain is traced

## Proposed Tranches

### Tranche 1. Trace Current Pacing Inputs

- capture the exact upstream `plot_roadmap` / `curr_block` surfaces that shape `ep_count`
- identify one or two Probe A blocks where operator expectation says "roughly 3 episodes" but runtime pressure tends to stretch

### Tranche 2. Contract Normalization

- align producer prompt language, runtime heuristics, and schema bounds so they describe the same pacing families
- remove stale wider-band wording where it conflicts with the active runtime clamp

### Tranche 3. Inflation Guards

- add bounded guards or scoring around "loop density is high, but episode expansion is not justified"
- make sure donor-translated receipts or hooks do not automatically count as more episodes

### Tranche 4. Proof

- run a bounded Stage2 or Stage23 canary on the traced compact block family
- confirm whether over-allocation drops without reopening downstream closure-clean seams

## Exit Criteria

This lane was ready to demote from front-active only when all of the following became true:

- one concrete compact-block family has an evidence-backed pacing trace
- producer/runtime/schema pacing language is aligned
- at least five bounded reruns show contraction on traced compact or near-compact families, with any residual repair noise explicitly separated from the pacing claim
- the result is documented clearly enough that donor-doctrine evaluation can be read separately from pacing inflation

All four conditions are now satisfied by the bounded survey, the block `1~2` trace, the contract-normalization patch set, and the `arc_001~005` rerun proof chain.

## Non-Goals

- proving that donor doctrine is good or bad in general
- solving all Stage2 density questions in one pass
- widening back into the older broad queue without a fresh reason

## Queue Placement

This lane is no longer the front-active Stage2 item. It now remains as closed canonical evidence for the pacing-normalization result.

The next front-active sibling after closure is `0_0-stage2-contract-normalization-remediation`, because the remaining repair noise exposed during `arc_005` belongs to state-shell cleanliness rather than pacing allocation.

During active realization this lane outranked:

- older proof-anchor lanes that are now historical backing only
- parked architecture debt
- broader downstream proof-pending work that can wait until pacing honesty is clearer

## Pass 1

- the document names the real active pacing owners: `plot_roadmap`, `curr_block`, FourPhase heuristic, ArcEnsemble clamp
- the document distinguishes donor indirect influence from direct Stage2 authority

## Pass 2

- the document keeps this lane bounded to pacing normalization instead of widening into donor or downstream redesign
- the promotion rationale is tied to current queue reality, not historical April queue text

## Pass 3

- the next action is concrete: trace -> normalize -> guard -> prove
- the exit criteria are narrow enough to justify a clean closure decision

## Closure Note

Closure review on 2026-04-19 concluded that the pacing lane is realized and no longer belongs in the active temp queue.

Verified behavior:

- `arc_001`: `6 -> 4`
- `arc_002`: `6 -> 5`
- `arc_003`: `5 -> 4`
- `arc_004`: `5 -> 4`
- `arc_005`: `4 -> 3`

Verification surfaces:

- survey and trace docs: `stage2-pacing-trace-bounded-survey`, `stage2-pacing-block12-deep-trace`
- contract alignment tests and bounded rerun proofs for `arc_001~005`
- hygiene and queue validation after the canonical docs were refreshed

Residual risk:

- donor-translated block density can still inflate upstream payloads in new families, but the current runtime pacing contract now behaves honestly across the available bounded family set
- adjacent carryover or state-header repair noise remains real, but it is not evidence that the pacing lane itself is still open

Follow-up handoff:

- keep `0_0-stage2-contract-normalization-remediation` as the live sibling lane for remaining non-pacing Stage2 cleanliness work
- preserve this SSOT and its proof notes as historical backing, not front-active workload

Confidence: 96/100
