# Stage234 Arc2/3 Stage2 Packet Fidelity Focused 3-Pass Audit

Date: 2026-04-16
Status: final (3-pass audited; focused Arc2/3 packet fidelity audit after bounded live-merge closure)
Canonical Path: `docs/2026-04-16/stage234-arc23-stage2-packet-fidelity-focused-3pass-audit.md`
Commit State:
- Baseline Commit: `cf744f871d3fd0d98d51e0fda7c83de8024f143b`
- Baseline Dirty Summary: active user/live-run drift present (`0_temp.txt`, `config/style_references/investment/style_guide.json`, deletions under legacy projects `000_0412-1` and `000_260412_a`)
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: unchanged during this focused audit; no normalization or revert performed
Source Survey Docs:
- `docs/2026-04-16/stage234-s2-s3-s4-bounded-live-merge-post-run-merge-audit.md`
- `docs/implementation/live-run-merge-survey-harness.md`
- `docs/2026-04-16/stage234-s2-s3-s4-authority-alignment-post-merge-current-head-adversarial-3pass-audit.md`
Evidence Artifacts:
- `projects/00_260416/project_data.db`
- `projects/00_260416/logs/session_20260416_111959.log`
- `projects/00_260416/logs/artifacts/stage2/arc_002/attempt_01/final_arc__balanced.json`
- `projects/00_260416/logs/artifacts/stage2/arc_003/attempt_01/final_arc__balanced.json`
- `modules/core/stage2_finalizer.py`
- `modules/core/stage2_optimizer.py`
- `modules/core/cross_stage_authority_packet.py`
- `modules/core/episode_state_arbiter.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_post_pass_runtime.py`
- `tests/test_stage4_post_processor.py`
Side-Effect Coverage: covered for selected Stage2 artifacts, DB persistence, packet emission path, Stage3 opening/location consumers, Stage4 numeric/location consumers; no code mutation performed
Confidence: `95%`

## 1. Intent

This is a focused follow-up audit for the specific dormant risk left open by the bounded live-merge closure:

- Arc2/3 Stage2 packet fidelity

It answers four narrow questions:

1. are Arc2/3 issues merely candidate noise or selected/persisted outputs?
2. which fields are stale or missing?
3. how do later consumers react to those missing fields?
4. if code work is later warranted, which lane is the likely owner?

This audit is intentionally not a code-change wave.

## 2. Final Verdict

### Finding 1. Arc2/3 packet fidelity loss is real and already persisted inside selected PASS outputs

Severity: medium

Arc2 and Arc3 are not noisy rejected candidates.

They are selected Stage2 outputs that persisted as `PASS` artifacts and Stage2 DB rows.

At the same time, the live Stage2 selection lane was not perfectly clean:

- Arc2 was chosen as `PASS_WITH_FIX` during the live director lane before later persistence
- Arc3 was also chosen as `PASS_WITH_FIX`, and Arc3 explicitly carried a metadata-mismatch contradiction in the live director lane

So the right read is not `clean PASS`.

It is:

- `selected and persisted`
- while the runtime had already surfaced bounded problems before final save

Arc2 evidence:

- DB `stage_attempts` records `ARC 2 VERDICT PASS SCORE 100`
- the selected artifact is `final_arc__balanced.json`

Arc3 evidence:

- DB `stage_attempts` records `ARC 3 VERDICT PASS SCORE 100`
- the selected artifact is `final_arc__balanced.json`

Operational meaning:

- this is not disposable candidate drift
- this is persisted fidelity loss inside chosen Stage2 outputs

### Finding 2. The strongest stale surface is location, not a full internal packet contradiction

Severity: medium

For both Arc2 and Arc3, the three structured surfaces remain internally aligned with each other:

- `joint_docs.final_location`
- `state_constraints.arc_end_state.location`
- `cross_stage_authority_packet.opening_carryover.location`

However, they are aligned around the wrong value: `알 수 없음`.

Arc2:

- tactical text advances through Hanmi Securities and closes with `SW인베스트먼트 대표실`
- `joint_docs.final_location` remains `알 수 없음`
- `arc_end_state.location` remains `알 수 없음`
- packet `opening_carryover.location` inherits `알 수 없음`

Arc3:

- tactical text closes at `서울 강남, SW인베스트먼트 소규모 원룸 오피스 창가`
- `joint_docs.final_location` remains `알 수 없음`
- `arc_end_state.location` remains `알 수 없음`
- packet `opening_carryover.location` inherits `알 수 없음`

So the precise condition is:

- not `structured surfaces disagree with each other`
- but `structured surfaces agree on stale location while diverging from tactical closure truth`

### Finding 3. Numeric carryover loss is also real, and it is upstream of packet emission

Severity: medium

Arc2 tactical text explicitly reaches:

- `23억 원(미실현 수익 포함)`

Arc3 tactical text explicitly reaches:

- `총자산 30억`

But both selected artifacts persist:

- `cross_stage_authority_packet.numeric_carryover = {}`

This does not appear to be a packet-builder bug in isolation.

The stronger read is:

- `state_constraints.arc_end_state` itself does not carry `capital`, `total_assets`, or `portfolio_position`
- `state_constraints.investment_calc` does not supply `final_cash` / `final_total_assets`
- the packet builder only reads those structured numeric fields
- therefore the packet emits no numeric carryover

Operational meaning:

- numeric authority was never promoted into the structured end-state surfaces that the packet trusts
- the packet is faithfully emitting an already-thinned structured state

### Finding 4. Downstream impact is real but mostly soft degradation until later arcs are actually realized

Severity: medium

The current downstream path is not a guaranteed hard break.

What happens instead:

- Stage3/arbiter opening location loses a strong packet anchor and falls back to weaker surfaces
- Stage3/Stage4 prompt builders lose structured numeric authority rows when packet numeric carryover is empty
- Stage4 post-pass can still bootstrap numbers from fact ledger first when those exist

This means Arc2/3 packet loss is currently best classified as:

- persisted authority-surface degradation
- not yet a demonstrated later-arc manuscript collapse

## 3. Pass 1. Artifact Truth Audit

### 3.1 Arc2

Arc2 selected artifact facts:

- `comparison_notes` says a stronger candidate existed with better joint-doc fidelity, but the selected artifact is still the saved `balanced` output
- `joint_docs.final_location` is `알 수 없음`
- `state_constraints.arc_end_state.location` is `알 수 없음`
- `cross_stage_authority_packet.opening_carryover.location` is `알 수 없음`
- tactical text later closes at `SW인베스트먼트 대표실`

This is sufficient to prove persisted stale-location transport.

### 3.2 Arc3

Arc3 selected artifact facts:

- Stage2 director logging explicitly flagged metadata mismatch against tactical closure
- the selected artifact still persisted with `joint_docs.final_location = 알 수 없음`
- `state_constraints.arc_end_state.location = 알 수 없음`
- packet opening location stays `알 수 없음`
- tactical text closes at `서울 강남, SW인베스트먼트 소규모 원룸 오피스 창가`

This is stronger than a cosmetic omission because the runtime itself already noticed the tactical/metadata split during Stage2.

Pass 1 conclusion:

- Arc2/3 location loss is real
- Arc2/3 numeric loss is real
- both are persisted in selected PASS outputs

## 4. Pass 2. Structured-Field Root-Cause Audit

The strongest root-cause candidate sits in Stage2 emission/finalization, not in later consumers.

### 4.1 Location path

`stage2_optimizer._sync_final_location()` only synchronizes:

- `joint_docs.final_location -> arc_end_state.location`

It does not recover a missing final location from the last tactical episode when `joint_docs.final_location` is already blank or unknown.

`stage2_finalizer._sync_stage2_end_location_contract()` then narrows even further:

- it canonicalizes `arc_end_state.location` and `joint_docs.final_location`
- it picks `canonical_location = end_location or final_location`
- if `arc_end_state.location` is stale but non-empty, it can win over a richer `joint_docs.final_location`
- if both are effectively unknown, nothing is repaired

So the finalizer only harmonizes existing structured location.

It does not promote tactical end-state truth into structured metadata.

For the concrete Arc2/3 samples audited here, the stronger confirmed fact is:

- both structured location surfaces are already `알 수 없음` by the time finalizer harmonization runs

So the sampled failure is not a proven overwrite of a richer joint-doc label.

It is a proven failure to promote tactical closure truth into structured metadata before packet build.

This makes the location issue most plausibly a `Stage2 sync-normalization` problem:

- structured location is being normalized and re-harmonized
- but the repair path is not tactical-aware enough to recover the real last-episode closure when the structured surfaces are already thinned

### 4.2 Inventory path

`_sync_stage2_end_state_inventory_contract()` aligns:

- `arc_end_state.equipment`
- `joint_docs.physical_inventory`

using declared metadata and carryover math.

It does not parse the final tactical episode to recover missing final carried items.

So Arc3 can keep empty structured inventory even when the tactical text names explicit documents/contracts at the end.

### 4.3 Numeric path

`build_cross_stage_authority_packet()` only reads numeric carryover from:

- `state_constraints.arc_end_state.capital`
- `state_constraints.arc_end_state.total_assets`
- `state_constraints.arc_end_state.portfolio_position`
- `state_constraints.investment_calc.final_cash`
- `state_constraints.investment_calc.final_total_assets`

If those fields are absent, the packet correctly emits `{}`.

There is no tactical-text numeric fallback in the packet builder.

`stage2_finalizer` also rebuilds the packet from `refined_arc` at persist time.

That means numeric truth not promoted into:

- `state_constraints.arc_end_state`
- or `state_constraints.investment_calc`

is dropped at the point of Stage2 emission, even if some other earlier surface knew it.

Stage2 already contains tactical numeric parsing for advisory purposes elsewhere, for example:

- `_check_cross_arc_asset_continuity()` can extract prior-arc asset numbers from tactical text when structured fields are absent

That contrast matters:

- tactical extraction exists in Stage2 as advisory logic
- but the structured end-state repair path does not currently reuse it for authoritative packet emission

Pass 2 conclusion:

- likely owner lane is `Stage2 sync-normalization + Stage2 emission/finalization`
- likely failure mode is `structured end-state promotion gap`, not a downstream consumer regression

## 5. Pass 3. Downstream Consumer Impact Audit

### 5.1 Stage3 opening/location consumers

`episode_state_arbiter` resolves packet opening location first, then falls back to weaker surfaces such as arc start location or joint docs.

This means stale packet location weakens the opening authority anchor.

It does not automatically crash the lane.

### 5.2 Stage3/Stage4 numeric consumers

`blueprint_constraint_compiler` and Stage4 context builders only surface numeric carryover when the packet or fact-ledger side actually provides those values.

If packet numeric carryover is empty:

- the structured numeric authority section simply becomes thinner
- later stages rely more heavily on fact ledger or other context

### 5.3 Why this is not yet a proven later-arc break

The current run did not realize Arc2/3 blueprints/manuscripts.

So what is proven now is:

- the authority packet is weakened before those arcs are consumed

What is not yet proven is:

- a concrete Stage3/Stage4 Arc2/3 manuscript contradiction caused by this weakness

Pass 3 conclusion:

- this is a meaningful upstream defect candidate
- it remains a focused follow-up issue until Arc2/3 are actually realized or until code remediation is chosen

## 6. Scope Decision

The correct current scope call is:

- yes to focused fidelity audit closure
- no to immediate code mutation in this turn
- no to immediate global survey escalation

The likely next engineering lane, if later authorized, is:

- Stage2 end-state promotion and finalization

not:

- a broad Stage3/Stage4 rewrite

## 7. Recommendation

No code change was performed in this audit.

If a later patch is authorized, the most likely fix candidates are:

1. promote final tactical episode closure into `joint_docs.final_location` / `arc_end_state.location` when both structured surfaces are unknown
2. promote final tactical numeric truth or equivalent authoritative numeric summary into `arc_end_state` / `investment_calc` before packet build
3. optionally harden Stage2 validation so selected PASS outputs cannot retain tactical-vs-metadata stale closure on investment-critical location/numeric fields

Until such a patch is explicitly authorized, the correct reading is:

- `Arc2/3 packet fidelity issue confirmed`
- `upstream structured-state promotion gap is the leading hypothesis`
- `not an immediate code-change order by itself`
