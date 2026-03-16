# Project 0_260316 PASS_WITH_FIX + Firewall Survey

Date: 2026-03-16
Status: canonical survey
Scope: `0_260316` Stage 4 `PASS_WITH_FIX` underuse, Contradiction Firewall routing, and fixable-vs-structural reject separation
Confidence After 3-Pass Audit: `96%`

## Executive Verdict

- **Fact:** Stage 4 already has a mature `PASS_WITH_FIX` patch/re-audit loop, but `Contradiction Firewall` still force-converts some locally fixable contradictions into `REJECT` and floors the score to `44`.
- **Fact:** `0_260316` contains three strong local-fix candidates that were not handled as such: `ep4 round 0` first-brother name drift, `ep4 round 1` forbidden expression residue, and `ep5 round 0` opening location drift.
- **Fact:** `ep5 round 2` is not a clean local-fix candidate. It already escalated to `fix_scope=partial`, carried `continuity replay` guidance, and behaved like a frontier/state conflict rather than a one-line typo.
- **Decision:** `PASS_WITH_FIX` should be used more aggressively, but only through a narrow `fixable_firewall` lane. A blanket relaxation of Firewall semantics would be incorrect.
- **Decision:** the required changes are `fixable-firewall classification`, `detailed contradiction payload persistence`, `exact post-patch verification for lexical fixes`, and `Stage 2/3 parity review`.

## Evidence Base

### Raw Run Evidence

- `projects/0_260316/logs/episode_production.jsonl`
- `projects/0_260316/logs/session/ui_events.jsonl`
- `projects/0_260316/logs/session/decisions.jsonl`
- `projects/0_260316/logs/artifacts/stage4/ep_0004/...`
- `projects/0_260316/logs/artifacts/stage4/ep_0005/...`
- `projects/0_260316/drafts/ep_0004.txt`
- `projects/0_260316/drafts/ep_0005.txt`
- `projects/0_260316/plans/blueprints/blueprint_0005.txt`

### Code Revalidation

- `modules/domain/agents/director_ensemble.py:642-669`
- `modules/domain/agents/director_ensemble.py:1120-1144`
- `modules/domain/agents/director_ensemble.py:1374-1382`
- `modules/core/stage4_interview_round.py:427-467`
- `modules/core/stage4_interview_round.py:2989-3234`
- `modules/core/stage4_interview_round.py:3473-3491`
- `modules/core/stage4_interview_round.py:3715-3845`
- `modules/domain/agents/director_auditor.py:918-943`
- `modules/core/stage2_finalizer.py:657-842`
- `modules/domain/agents/three_phase_blueprint_generator.py:461-588`

### Test Coverage Revalidation

- `tests/test_stage4_interview_round.py:1643-1684`
- `tests/test_stage4_interview_round.py:1686-1729`
- `tests/test_v75c_contradiction_firewall.py:54-117`
- `tests/test_v75c_contradiction_firewall.py:306-368`

## Case Review

| Case | What the evidence shows | Classification | `PASS_WITH_FIX` suitability |
| --- | --- | --- | --- |
| `ep4 round 0` | Selected manuscript used `한태준`, but project truth already had first brother as `한진호` from `ep1`; UI log explicitly recorded `Post-select history conflict` on that name change. | Local named-entity continuity drift | **Strong** |
| `ep4 round 1` | Director already returned `PASS_WITH_FIX 90`, but the explicit instruction to replace forbidden phrase `그림자처럼` was not applied; patch trace shows near-zero change and wrong target focus. | Local forbidden-expression residue + patch targeting miss | **Strong** |
| `ep5 round 0` | Selected manuscript opened with `신축 오피스`, while actual prior frontier and final ep4 office were `허름한 상가 건물 2층`; the same candidate otherwise already used `한미증권`. | Local opening/location alias drift | **Strong** |
| `ep5 round 1` | Open review itself says the `신축 오피스` signal was false-positive at this point, but the manuscript still injected `한미은행` and `박성호 차장`; score had already collapsed to `44` and `fix_scope` was `partial`. | Mixed proper-noun/title drift after a failed fix cycle | **Conditional, not clean** |
| `ep5 round 2` | Initial verdict `PASS_WITH_FIX 97`, final Firewall `REJECT`, `fix_scope=partial`, retry directives include `[A-4 continuity replay]`, and action items offer either title unification or explicit “different person” narration. | Frontier/state conflict with local symptoms | **No** |

## Resolved Fact Corrections

Two prior interpretations were wrong or overstated and are corrected here.

1. `ep4 round 0` name direction
- Some prior notes framed the issue as `한진호 -> 한태준` typo in the final text.
- Raw evidence shows the reverse project truth: `ep1` already established the first brother as `한진호`, while `ep4 round 0` selected candidate drifted to `한태준`.
- Evidence:
  - `projects/0_260316/drafts/ep_0001.txt:54`
  - `projects/0_260316/logs/artifacts/stage4/ep_0004/attempt_01/selected_candidate__B.txt:5`
  - `projects/0_260316/logs/session/ui_events.jsonl:688`

2. `ep5 round 0` blueprint contamination claim
- Some prior notes overstated this as `blueprint_0005` contamination.
- The actual `blueprint_0005` text is clean on the core office/location handoff and on `한미증권`.
- The visible `신축 오피스` drift appears in the selected manuscript, not in `blueprint_0005`.
- Evidence:
  - `projects/0_260316/plans/blueprints/blueprint_0005.txt:7-13`
  - `projects/0_260316/logs/artifacts/stage4/ep_0005/attempt_01/selected_candidate__C.txt:1`
  - `projects/0_260316/drafts/ep_0004.txt:39`

## Why Current Routing Wastes Rounds

### 1. Director prompt already encourages `PASS_WITH_FIX`

`modules/domain/agents/director_ensemble.py:642-669` explicitly tells the Director to prefer `PASS_WITH_FIX` for minor contradictions and local edits.

- `642`: large numeric mismatch should prefer `PASS_WITH_FIX` or `REJECT`
- `663`: `80~89` band maps to `PASS_WITH_FIX`
- `669`: “minor contradictions only” should become `PASS_WITH_FIX + fix_scope="inplace"`

The intended philosophy is already present.

### 2. Firewall later collapses that nuance into binary `REJECT`

`modules/domain/agents/director_ensemble.py:1120-1144` does this:

- any `CRITICAL >= 1` or `MAJOR >= 2` contradiction triggers Firewall
- verdict becomes `REJECT`
- score is clamped to `44`
- the detailed contradiction payload is only logged, not preserved in a structured way

That means:

- local named-entity drift
- forbidden-expression residue
- title/honorific mismatch
- location alias mismatch

can all collapse into the same terminal `REJECT` bucket as true structural failure.

### 3. The retry path only has one special escape hatch: continuity replay

`modules/core/stage4_interview_round.py:427-467` and `3473-3491` only recognize `continuity replay` style Firewall rejects and upgrade them to `partial`/`post_select_conflict`.

There is no symmetric classifier for:

- local proper noun fixes
- title/honorific fixes
- explicit forbidden-expression removals
- local location alias substitutions

### 4. Detailed contradiction payload is discarded too early

`modules/domain/agents/director_ensemble.py:1374-1382` only forwards `contradiction_types`, not full `found_contradictions`.

That makes later routing coarse:

- the retry path keeps a list of types
- but it loses structured `severity`, `current_violation`, and any per-issue detail needed to separate “replace one token” from “rewrite the scene logic”

### 5. Existing patch machinery is strong enough; the classifier is the weak link

`modules/core/stage4_interview_round.py:2989-3234` already supports:

- up to 3 local patch attempts
- re-audit after each patch
- patch diff logging
- patch history injection into re-audit context

So the main gap is not absence of patch machinery. The main gap is wrong routing into that machinery.

## Concrete Case Analysis

### Finding F1. `ep4 round 0` should have been classified as local fix, not hard reject

Evidence:

- `projects/0_260316/logs/artifacts/stage4/ep_0004/attempt_01/selected_candidate__B.txt:5`
- `projects/0_260316/logs/session/ui_events.jsonl:688`
- `projects/0_260316/logs/session/decisions.jsonl:15`

What happened:

- Director selected candidate `B` with `score=99`.
- The selected manuscript says `한태준`.
- The project truth from `ep1` says the first brother is `한진호`.
- The run logged this as a `Post-select history conflict`.

Why this matters:

- This is a real continuity violation.
- But it is still a lexical identity substitution, not a scene-logic rewrite.
- The current system had no structured “fixable firewall” lane, so the round ended as `REJECT`.

### Finding F2. `ep4 round 1` proves the patch loop exists but can miss obvious one-line fixes

Evidence:

- `projects/0_260316/logs/session/decisions.jsonl:16`
- `projects/0_260316/logs/artifacts/stage4/ep_0004/attempt_02/selected_before_fix__A_inplace_patch.txt:1`
- `projects/0_260316/logs/episode_production.jsonl:5`

What happened:

- Director explicitly returned `PASS_WITH_FIX` with `score=90`.
- Action item: replace forbidden phrase `그림자처럼`.
- The selected manuscript still contained that phrase in the opening line.
- Patch trace recorded `patch_strategy=inplace_patch_structural`, `patch_targets=["scene_3"]`, and `unchanged_ratio=0.9971`.

Interpretation:

- The problem was not verdict philosophy.
- The problem was that the fix loop targeted the wrong area and did not verify the exact requested substitution.

This is the cleanest proof that exact local-fix verification is missing.

### Finding F3. `ep5 round 0` was also a strong local-fix candidate

Evidence:

- `projects/0_260316/logs/artifacts/stage4/ep_0005/attempt_01/selected_candidate__C.txt:1`
- `projects/0_260316/drafts/ep_0004.txt:39`
- `projects/0_260316/logs/session/decisions.jsonl:18`

What happened:

- Director selected candidate `C` with `score=90`.
- The candidate opens with `[밤, 테헤란로 신축 오피스]`.
- The actual frontier from final `ep4` is `테헤란로의 한 허름한 상가 건물 2층`.
- The same selected candidate already used `한미증권` correctly later in the episode.

Interpretation:

- This is not proof of a healthy state pipeline.
- But it is a strong sign that the chosen candidate was close enough that a local opening correction should have been considered before forcing a new outer round.

### Finding F4. `ep5 round 1` is a mixed case, not a clean promote-to-`PASS_WITH_FIX`

Evidence:

- `projects/0_260316/logs/session/decisions.jsonl:19`
- `projects/0_260316/logs/artifacts/stage4/ep_0005/attempt_02/rejected_best__A_inplace_patch.txt:48`
- `projects/0_260316/logs/artifacts/stage4/ep_0005/attempt_02/rejected_best__A_inplace_patch.txt:61`
- `projects/0_260316/logs/artifacts/stage4/ep_0005/attempt_02/rejected_best__A_inplace_patch.txt:77`

What happened:

- The failed patch candidate introduced `한미은행`.
- It also kept `박성호 차장`.
- Open review itself says the earlier `신축 오피스` signal is false-positive by this point.
- But the round had already collapsed to `score=44` and `fix_scope=partial`.

Interpretation:

- There is still local lexical damage here.
- But by this point the run had already lost confidence about the frontier and identity model.
- This is not the right exemplar for broad `PASS_WITH_FIX` promotion.

### Finding F5. `ep5 round 2` is the boundary case that should stay out of aggressive `PASS_WITH_FIX`

Evidence:

- `projects/0_260316/logs/session/decisions.jsonl:20`
- `projects/0_260316/logs/episode_production.jsonl:10`
- `modules/core/stage4_interview_round.py:3473-3491`

What happened:

- Initial verdict was `PASS_WITH_FIX 97`, but final verdict became Firewall `REJECT`.
- `fix_scope` was already `partial`.
- Retry directives explicitly carried `[A-4 continuity replay]`.
- Action items allowed either title unification or “different person” narration.

Interpretation:

- This is already beyond exact token replacement.
- The system was no longer asking for a one-line edit; it was asking for relationship/frontier adjudication.
- This should remain outside aggressive `PASS_WITH_FIX`.

## Waste Model

### Proven avoidable waste floor

The cleanest proven waste is `ep4 round 2`.

- `ep4 round 1` had an explicit one-line action item.
- The patch missed it.
- `ep4 round 2` then spent `195343 ms` and `$0.147019` to finish the same episode.

That is hard evidence of avoidable cost/time caused by local-fix execution failure.

### Plausible upper-bound recoverable waste

If strong local-fix candidates had been routed through a clean `fixable_firewall` lane with exact verification:

- `ep4` likely could have avoided outer rounds `1` and `2`
- `ep5` likely could have avoided outer rounds `1`, `2`, and `3`

Upper-bound recoverable spend:

- `ep4 rounds 1+2`: `$0.321129`, `469609 ms`
- `ep5 rounds 1+2+3`: `$0.877859`, `950342 ms`
- total: `$1.198988`, `1419951 ms` (`23.7 min`)

This upper bound is plausible, not guaranteed. It depends on routing the local cases correctly and verifying exact patch application.

## Recommended Design

### Decision

Adopt a narrow `fixable_firewall` lane instead of a blanket “more PASS_WITH_FIX everywhere” policy.

### Guard Conditions

Promote Firewall output to local-fix handling only when all of the following hold:

1. pre-Firewall verdict is `PASS` or `PASS_WITH_FIX`
2. `pre_firewall_score >= 90`
3. `score_breakdown.continuity_contradiction >= 30`
4. contradiction count is `<= 3`
5. every contradiction falls inside a lexical/local family:
   - proper noun / entity name
   - organization name
   - title or honorific
   - forbidden expression
   - local location alias
6. no continuity replay markers from `modules/core/stage4_interview_round.py:427-467`
7. no hard structural families:
   - deceased actor
   - numeric impossibility
   - timeline reversal
   - event ordering collapse
   - scene overlap replay

These conditions cleanly separate the strong `0_260316` local-fix cases from the mixed/structural ones.

### Required Code Shape

1. `modules/domain/agents/director_ensemble.py`
- add structured fixability classification before the blanket `REJECT + score=44`
- when fixable, emit `verdict=PASS_WITH_FIX`, `fix_scope=inplace`, and a dedicated flag such as `firewall_mode=fixable`
- persist full `found_contradictions`, not only `contradiction_types`

2. `modules/core/stage4_interview_round.py`
- generalize the current continuity-only replay exception into a broader routing classifier
- continuity replay should still escalate to `partial/full`
- lexical local fixes should remain in `inplace` with explicit verification

3. `modules/core/stage4_interview_round.py` local patch loop
- add exact post-patch verification for explicit lexical directives
- examples:
  - forbidden expression must disappear
  - corrected proper noun must appear
  - banned alias must not appear
- this is a deterministic compliance check for explicit action items, not a world-fact rewrite engine

4. `modules/domain/agents/director_auditor.py`
- mirror the same fixable-firewall semantics in Stage 2/3 audit
- otherwise Stage 4 and Stage 2/3 will diverge in verdict meaning

5. Tests
- add `0_260316` regression fixtures for:
  - `ep4 round 0` name drift
  - `ep4 round 1` forbidden expression residue
  - `ep5 round 0` opening location drift
  - `ep5 round 2` non-fixable continuity replay boundary

## Non-Recommendations

- Do not route `numeric contradiction`, `deceased NPC`, `timeline reversal`, or `scene overlap replay` into aggressive `PASS_WITH_FIX`.
- Do not treat every Firewall hit as patchable just because the selected manuscript scored high before Firewall.
- Do not rely only on `contradiction_types`; that loses too much information.
- Do not use `0_260316` recovery success as evidence that the classifier problem is solved.

## 3-Pass Audit

### Pass 1: Fact Check

- Verified raw round records for `ep4` and `ep5` from `episode_production.jsonl`.
- Verified `ep4 round 0` history-conflict direction from `ui_events.jsonl:688` and artifact text.
- Verified `ep5 round 0` selected manuscript opener against final `ep4` frontier and `blueprint_0005`.
- Verified code locations for Director prompt intent, Firewall override, contradiction payload loss, continuity replay exception, and patch routing.

Pass 1 result: factual base is stable. Two prior interpretation errors were corrected before save.

### Pass 2: Consistency Check

- The “use `PASS_WITH_FIX` more aggressively” thesis is supported, but only for the strong local-fix subset.
- The thesis does not hold for `ep5 round 2`, which is the key boundary case.
- The code evidence is consistent with the run evidence: routing, not absence of patch machinery, is the main defect.

Pass 2 result: no unresolved contradiction remains inside this survey.

### Pass 3: Actionability Check

- The document identifies exact code touchpoints.
- The document separates strong candidates, conditional cases, and non-candidates.
- The document distinguishes `fact`, `plausible upper bound`, and `decision`.

Pass 3 result: this survey is implementation-ready and safe to merge into the canonical execution SSOT.
