# 0_1 Stage4 CW First-Pass Miss Parallel Bounded Survey

Date: 2026-03-31
Status: final (3-pass audited)
Document Type: bounded parallel synthesis survey
Canonical Path: `docs/2026-03-31/0_1-stage4-cw-first-pass-miss-parallel-bounded-survey.md`
Temp Mirror Path: `(none - survey only)`
Baseline Commit: `229b85c655c32366818c2278462b51f3ad490913`
Baseline Dirty Summary: `dirty: active stage4 runtime/tests/log-db drift, temp queue active, multiple 2026-03-30 docs still untracked`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Parent Order: `docs/2026-03-30/0_1-stage4-cw-first-pass-miss-parallel-master-order.md`
Lane Drafts:
- `docs/2026-03-30/0_1-stage4-cw-first-pass-miss-lane1-prompt-topology-draft.md`
- `docs/2026-03-30/0_1-stage4-cw-first-pass-miss-lane2-carryover-cognition-draft.md`
- `docs/2026-03-30/0_1-stage4-cw-first-pass-miss-lane3-model-tier-budget-draft.md`
- `docs/2026-03-30/0_1-stage4-cw-first-pass-miss-lane4-runtime-vs-gate-draft.md`
Evidence Artifact:
- `docs/2026-03-31/0_1-stage4-cw-first-pass-miss-parallel-evidence.json`

## Answer First

`Chief Writer` is not primarily failing on first pass.

The audited synthesis points the other way:

1. `Director` passed every first-pass manuscript across EP1-EP10.
2. The dominant first-pass failure pattern is `Director PASS -> downstream Python gate REJECT`.
3. Model tier, provider fallback, context budget, and candidate diversity do not explain the misses.
4. Prompt hierarchy and previous-manuscript salience are real but secondary contributors.
5. The current system over-attributes downstream gate failures to `CW first-pass weakness`.

The smallest correct diagnosis is:

- `primary`: downstream gate override / advisory-deadlock illusion
- `secondary`: first-pass authority salience and carryover reinforcement weakness
- `non-primary`: model tier / provider / context budget

## Hard Conclusions

### 1. First-pass `CW quality failure` is not supported by live evidence

Lane 4 reconstructed EP1-EP10 first-pass attempts and found:

- all 10 first-pass manuscripts received `Director PASS`
- first-pass score range: `90-100`
- median first-pass score: `96`
- three episodes passed later with a lower score than the first pass:
  - EP3: `100 -> 96`
  - EP9: `98 -> 95`
  - EP10: `96 -> 95`

This closes the main question: the system is not observing an initial-writing quality floor from `CW`. It is observing a post-Director override problem.

### 2. The dominant first-pass blocker is downstream gate override

The main failing families are:

- `strong_advisory_escalation_non_local_fix`
- `pass_with_fix_contract_missing_patch_targets`
- `post_select_conflict`

These are Python/runtime gate families that fire after `Director PASS`.

The most recurrent false-miss pattern is:

- `PASS`
- strong advisory escalation converts it to `PASS_WITH_FIX`
- local `fix_pack` is absent or not patch-ready
- runtime converts it to `REJECT`

This is not a manuscript-quality rejection. It is a gate/contract rejection.

### 3. Model tier is not the primary issue

Lane 3 closed the model hypothesis with direct evidence:

- requested `chief_writer` model: `gemini-3.1-pro-preview`
- no fallback events in recent `0_1` runs
- CW `llm_io` entries stay on primary model
- prompt sizes stay well below the configured guardrails
- candidate diversity remains a 3-strategy ensemble with bias adjustment

So the first-pass miss is not primarily caused by:

- low model tier
- provider degradation
- context overflow
- shallow ensemble search

### 4. Prompt hierarchy and V67 salience are secondary, not primary

Lane 1 and Lane 2 agree on a mixed result:

- strong authority anchors exist early:
  - `immutable_fact_section`
  - `chain_link_section`
  - `prev_digest`
  - `opening_anchor_section`
- but the explicit hierarchy declaration arrives late
- `prev_manuscripts_section` is placed at the tail and is not named in the explicit authority ladder
- retry prompts gain clearer task framing than first-pass prompts

This makes first-pass prompts somewhat weaker than they should be, but the survey does not support treating this as the main reason manuscripts fail.

## Medium-Confidence Conclusions

### 1. The system's operator-facing diagnosis is currently wrong or at least misleading

Because live sinks emphasize `final_verdict` and `gate_basis`, operators can easily read:

- `EP9 failed`
- `EP10 first pass failed`

and conclude:

- `CW wrote poorly on first pass`

But the evidence says:

- `Director PASS + runtime override`

That distinction is not prominent enough in current persisted evidence.

### 2. Retry success comes from narrower task shape and gate avoidance, not from CW "learning to write"

Retries improve the situation when they:

- avoid a false advisory
- switch candidate selection
- reuse a near-pass baseline
- or stop triggering the downstream override

This does not look like a primary `CW prose improvement` story.

### 3. `carryover_ceiling` is too investment-shaped

Lane 2 found that the `carryover_ceiling` heuristics rely heavily on investment-fiction keywords.
That makes the section sparse or empty for other genres, weakening one of the few structured prior-state reinforcements available to first-pass generation.

## Open Questions

1. How many strong advisory classes are still precision-poor after the recent `NpcDrift` remediation wave?
2. Is `flashback` in EP10 a false positive, a low-precision advisory, or a correct gate on a genuinely unsafe manuscript?
3. Would stronger first-pass authority framing measurably reduce later `post_select_conflict`, or is that mostly a separate continuity-selection issue?
4. Should strong advisory escalations remain fail-closed at the same layer, or should they move into a different runtime lane that preserves `Director PASS` quality attribution?

## First-Pass vs Retry Delta Matrix

| Dimension | First Pass | Retry | Effect |
| --- | --- | --- | --- |
| `Director feedback` | absent | present | retry gets explicit correction target |
| `selection_reason` | absent | present | retry gets strategy rationale |
| `open_review` | absent | present on rewrite path | retry gets extra diagnostic prose |
| `score_breakdown` | absent | present | retry gets more structured failure cues |
| `validation_warnings` | absent | present | retry gets extra machine-side constraints |
| `reuse_contract` baseline | absent | conditional | retry may preserve near-pass text |
| `retry history` | absent | present | retry avoids repeating prior failures |
| `prev_manuscripts_section` | present | present | shared, but not enough to equalize task shape |
| `authority ladder` | present but late | same base topology | still suboptimal |

Interpretation:

- retry is structurally more informed
- but this does not prove first-pass `CW` weakness
- it mainly shows why retry is easier to steer

## Advisory vs CW Fault Separation

| Layer | Current Evidence | Interpretation |
| --- | --- | --- |
| `artifact truth` | first-pass manuscripts exist and score high | not a blank-output or low-model floor problem |
| `metadata truth` | `Director PASS` often becomes runtime `REJECT` | sink semantics currently blur quality layer vs gate layer |
| `narrative truth` | some retries solve genuine continuity conflicts | a subset of later failures are real, but not first-pass CW failures |

## Patch Priority Ranking

1. Normalize the strong-advisory escalation contract so `Director PASS` without a patch-ready local fix contract no longer collapses into a synthetic `REJECT`.
2. Harden first-pass authority framing:
   - explicitly rank `V67 prior manuscript full-text`
   - reinforce that later `V67` corpus is binding archive truth
3. Generalize `carryover_ceiling` so it is not investment-biased.
4. Improve sink visibility for `Director PASS -> runtime override` cases where that split is still diagnostically important after the contract fix lands.

## Recommended Next Step

The correct execution wave is not `model upgrade`.

It is a bounded Stage 4 remediation wave:

1. `advisory escalation contract normalization`
2. `first-pass authority salience hardening`
3. `carryover ceiling generalization`

This is still deliberately smaller than a full advisory-policy redesign.
It fixes the proven deadlock first, then tightens the secondary prompt contributors that the survey identified.

## 3-Pass Audit Record

Pass 1, structure and scope:

- document type is a bounded synthesis survey, not an execution SSOT
- scope remains the `CW first-pass miss` question
- primary vs secondary causes are separated explicitly

Pass 2, evidence and consistency:

- all hard claims map back to the four lane drafts
- no claim here contradicts the live lane verdicts
- model, prompt, carryover, and runtime layers are separated rather than collapsed

Pass 3, execution and readability:

- the document is answer-first
- recommended next move is bounded and execution-ready
- the survey does not overclaim a full advisory-policy redesign

Confidence: 97%
