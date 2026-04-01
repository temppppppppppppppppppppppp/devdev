# 0_0 Stage4 Post-Select Continuity Seam Bounded Survey

Date: 2026-04-02
Status: final
Confidence: 96%
Scope: static bounded survey of the residual `Stage4 ep4 post_select_conflict / continuity` seam after the landed fix-pack finalization tranche
Canonical Path: `docs/2026-04-02/0_0-stage4-post-select-continuity-seam-bounded-survey.md`
Evidence Artifact: `docs/2026-04-02/0_0-stage4-post-select-continuity-seam-evidence.json`
Related Docs:
- `docs/2026-04-02/0_0-stage4-canonical-entity-postselect-runtime-closure-audit.md`
- `docs/2026-04-02/0_0-stage4-fixpack-finalization-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage4-fixpack-finalization-post-implementation-audit.md`

## 1. Answer First

The residual `ep4` seam is narrower than "Stage4 missing_fix_pack" and narrower than "Stage2/3 hierarchy regression."

It is a mixed Stage4 final-round continuity seam:

1. there are still real artifact-level contradictions in the observed `ep4` candidate path
2. the Stage4 post-select downgrade contract flattens those contradictions into coarse `continuity/history` buckets
3. that flattening hides whether the conflict is a bounded `proper_noun/timeline` repair or a broader rewrite-class collapse

So the next non-runtime question is not "reopen Stage2/3" and not "broad Stage4 redesign." It is:

- whether Stage4 should preserve contradiction subtype precision across the `continuity_firewall -> post_select_conflict -> reject guidance/snapshot` handoff

The just-landed fix-pack preservation tranche already narrowed the old `missing_fix_pack` problem. The remaining survey result is that Stage4 still compresses too much final-round continuity detail into a rewrite-first conflict contract.

## 2. Hard Conclusions

### 2.1 `ep4` was not blocked by a pure false positive; the artifact path still contained real contradictions

`attempt_01` artifact truth shows a genuine proper-noun/entity drift:

- the selected manuscript uses `신성증권`, `최동욱`, and `3일 뒤`
- this directly conflicts with the accepted carryover line that later settles on `한미증권 박 지점장`

`attempt_02` artifact truth shows the institution/person anchor improved, but the manuscript still carries:

- `영업일 기준 3일 뒤`
- explicit `HUD 시스템`
- lingering intrusion/system contamination in the selected text

So the final-round downgrade was not operating on a clean manuscript. There was still real continuity pressure in the artifact itself.

### 2.2 The post-select contract builder is structurally coarse

`_build_post_select_conflict_contract()` currently preserves only:

- `conflict_type = continuity/history/check_error`
- `conflict_detail`
- `expected_truth`

It does not preserve:

- contradiction subtype such as `proper_noun` or `timeline`
- field-level anchor
- manuscript span or repair target
- whether the originating contradiction was previously judged locally fixable

That means a bounded proper-noun or timeline contradiction is serialized into the same contract family as broader history-collapse conflicts.

### 2.3 Earlier Stage4 contradiction logic already knows more than the post-select contract preserves

The contradiction-firewall path and its tests already model:

- `timeline`
- `고유명사`
- fixable local contradiction -> `PASS_WITH_FIX`
- non-fixable contradiction -> hard `REJECT`

So the information loss does not begin at the earliest contradiction classifier. It happens later, when post-select validation repackages the problem into the coarse `post_select_conflict` contract.

### 2.4 The recently landed fix-pack preservation tranche addresses one symptom, not the entire seam

The new fix-pack finalization tranche now preserves bounded local hints for `post_select_conflict` in reject guidance/snapshots.

That helps with:

- downstream observability
- avoiding unconditional `missing_fix_pack` flattening

But it does not by itself solve:

- contradiction subtype loss
- severity blending between fixable local continuity and broad rewrite-class history collapse

So the residual seam is now best described as `post-select contradiction contract precision`, not generic `missing_fix_pack`.

## 3. Medium-Confidence Conclusions

### 3.1 The next bounded Stage4 follow-up, if opened later, should likely target contract normalization rather than another fix-pack-only lane

The current evidence suggests that the next precision gain would come from preserving more structure across the post-select downgrade boundary:

- contradiction subtype
- source anchor
- repair granularity

Confidence: 86%

### 3.2 `ep4` may contain two separable continuity families that are currently over-packed into one contract

The observed path mixes:

- bounded proper-noun/timeline continuity
- broader system/HUD contamination and stale hook carryover

If both remain flattened into one `post_select_conflict` envelope, later runtime handling cannot cleanly decide between bounded repair guidance and truly broad rewrite pressure.

Confidence: 82%

## 4. Open Questions

1. Should `_build_post_select_conflict_contract()` preserve contradiction subtype arrays such as `proper_noun`, `timeline`, and `system_contamination`?
2. Should post-select downgrade payloads preserve source anchors or span-level repair hints when the originating conflict was locally fixable?
3. Should `HUD/system contamination` remain a continuity/history member of the same contract, or be split into a different Stage4 final-round family?

## 5. Artifact / Metadata / Narrative Truth

### 5.1 Artifact Truth

- `ep4 attempt_01` selected manuscript contains `신성증권`, `최동욱`, and `3일 뒤`
- `ep4 attempt_02` selected manuscript contains `한미증권 박 지점장`, but still also contains `영업일 기준 3일 뒤` and explicit `HUD 시스템`
- the patched blueprint under `attempt_01` still contains `HUD`/intrusion contamination, so the Stage4 candidate path was not entering post-select from a pristine upstream state

### 5.2 Metadata Truth

- prior runtime audit logged `ep4` as `post_select_conflict|contradiction:고유명사|continuity_firewall|fix_pack:missing_fix_pack`
- then again as `post_select_conflict|contradiction:타임라인|fix_pack:missing_fix_pack`
- the current code path promotes `gate_basis` into `reject_bucket=post_select_conflict` and forces `fix_scope=full`
- the post-select contract builder itself does not preserve subtype precision

### 5.3 Narrative Truth

- `attempt_01` is a real canonical-name regression
- `attempt_02` is not a simple name regression anymore, but it still contains timeline and world-model contamination
- that means the seam is not a fake conflict detector; it is a real conflict path whose final-round contract is too blunt

## 6. Operating Consequence

- keep `Stage4` paused
- do not reopen `Stage2/3` on the basis of this seam
- do not run canary yet in this turn
- if a new bounded non-runtime lane is needed before any future runtime proof, the right target is:
  - `Stage4 post-select contradiction subtype / continuity contract normalization`

## 7. 3-Pass Audit Record

### Pass 1. Structure and Scope

- kept this as a bounded survey, not an execution SSOT
- bounded to the residual `ep4` Stage4 seam
- explicitly excluded fresh runtime claims

### Pass 2. Evidence and Consistency

- matched artifact truth against actual `ep4` Stage4 selected manuscripts
- matched metadata truth against the prior runtime closure evidence and runtime audit fingerprints
- matched code truth against the live post-select contract builder and reject/runtime routing

### Pass 3. Execution and Readability

- reduced the next action to one static residual seam
- avoided reopening Stage2/3 or broad Stage4 redesign
- made the operator consequence explicit: pause stays, canary deferred, contract precision is the next bounded non-runtime target
