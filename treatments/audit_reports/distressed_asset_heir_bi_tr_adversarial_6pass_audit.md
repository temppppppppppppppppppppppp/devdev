# distressed_asset_heir BI/TR - Adversarial 6-Pass Audit

artifact scope:

- TR: `treatments/distressed_asset_heir_tr_block_070_draft.json`
- BI: `bible/0_bi_distressed_asset_heir.json`

request boundary:

- no new manuscript generation
- no new episode production packet generation
- audit target is BI/TR only

overall verdict: FAIL for manuscript-handoff readiness; PASS for mechanical BI/TR pair validity

## Evidence Snapshot

- TR block count: 70
- TR sequence problems: 0
- missing primary/secondary incident density fields: 0
- no-cider blocks: 0
- pain-only exits: 0
- unresolved `foreshadow_targets`: 0
- invalid `callback_sources`: 0
- BI `MasterBible.plot_roadmap` length: 70
- BI/TR title mismatch count: 0
- BI/TR consumability checker: pair PASS, canonical PASS, normalized PASS
- producer-language leakage:
  - `해당 사건` / `해당 아크` in TR strings: 225
  - affected TR blocks: 64
  - mirrored `해당 사건` / `해당 아크` in BI strings: 225

## Pass 1 - Structural Contract

Attack:

- Does the TR actually contain a complete 70-block sequence?
- Is BI pointing at the expected work and source files?
- Is the BI plot roadmap present at the same scale as the TR?

Findings:

- TR has 70 blocks and sequential block numbering has no gaps.
- TR `_production_status.last_sequential_block_pass` is 70.
- BI `_work_id` is `distressed_asset_heir`.
- BI `_source_tr` points to `treatments/distressed_asset_heir_tr_block_070_draft.json`.
- BI `MasterBible.plot_roadmap` has 70 entries.

Verdict: PASS.

## Pass 2 - Webnovel Pacing And Incident Density

Attack:

- Does any block fail the user's pacing contract that one block should hold at least two incident beats?
- Are there blocks that exit on pain only without a receipt?

Findings:

- Every TR block has `primary_incident` and `secondary_incident` in `genre_ext.episode_bundle_density`.
- Every TR block has `genre_ext.block_cider.has_cider = true`.
- No TR block is marked as `pain_only_exit`.
- The reward types rotate across access, deal approval, cashflow, option defense, workout, officialization, exclusive review, standstill, pricing cap, option control, pilot contract, financing, and governance defense.

Verdict: PASS.

## Pass 3 - Protagonist Self-Interest

Attack:

- Does Han Doyun become kind, morally heroic, or passive?
- Does the reward engine drift into family praise or social approval?

Findings:

- Core decisions remain transactional: access before capital, rights before stores, account control before persuasion, option rights before ownership, proof before price.
- Family recognition is narrow: review windows, small limits, meeting-table adoption, audit boundaries, and mandate language.
- The protagonist repeatedly accepts bounded loss when it protects larger control, which supports the requested efficiency/profit/optionality logic.

Verdict: PASS.

## Pass 4 - Continuity, Foreshadow, Callback Graph

Attack:

- Are there dangling foreshadow targets or impossible callback references?
- Does the TR lose causal continuity between assets?

Findings:

- No `foreshadow_targets` point backward, outside the 1-70 range, or beyond the completed TR.
- No `callback_sources` point forward or outside the 1-70 range.
- The macro-battlefield progression is coherent: franchise rights -> cold-chain NPL -> institutional meal supply -> commercial district REIT -> PEF carve-out -> confirmatory diligence -> family/audit defense.

Verdict: PASS mechanically.

Adversarial note:

- The graph is mechanically valid, but many callback/foreshadow strings use producer-side placeholders such as `해당 사건` and `해당 아크`.
- This does not break the numeric graph, but it is a production-handoff hygiene problem.

## Pass 5 - BI/TR Synchronization

Attack:

- Did the BI drift away from the accepted TR?
- Is the BI plot roadmap internally aligned with the TR?

Findings:

- `check_bi_tr_consumability.py` reports: pair PASS, canonical PASS, normalized PASS, blocks=70.
- BI `plot_roadmap` length equals TR block count.
- BI plot roadmap titles match the TR block titles.
- The same leakage strings are mirrored into BI because BI was generated from the TR source.

Verdict: PASS for synchronization, FAIL for inherited source hygiene.

## Pass 6 - Manuscript-Handoff Hygiene

Attack:

- If the BI/TR pair is fed into a downstream manuscript or episode harness, can producer-language leak into generated prose?

Findings:

- TR contains 225 occurrences of `해당 사건` / `해당 아크` across 64 blocks.
- BI contains the same 225 occurrences mirrored under `MasterBible.plot_roadmap`.
- Examples:
  - `해당 사건에서 분리 매입 대상으로 올린 임대차 우선협상권이 실제 방어전에서 작동한다.`
  - `고장 난 냉장창고와 리스료 연체는 해당 아크에서 route control과 설비 회수 순서 싸움으로 확대된다.`
  - `도윤은 해당 사건에서 route control option을 행사할 수 있는 가격 방어선을 얻는다.`
- These are not character-facing facts. They are producer shorthand.
- If consumed directly, they can cause the manuscript runner to emit vague or artificial phrasing.

Verdict: FAIL.

## Final Director Decision

The BI/TR pair remains mechanically valid and structurally complete, but it should not be declared manuscript-handoff clean after this 6-pass adversarial audit.

Required next BI/TR-only remediation:

1. Replace `해당 사건` / `해당 아크` in TR source fields with concrete antecedents:
   - exact prior asset, contract, option, memo, route, audit object, or battlefield name;
   - avoid vague replacements like `이 사건` or `이번 건`.
2. Regenerate BI from the cleaned TR so `MasterBible.plot_roadmap` inherits the repaired text.
3. Rerun:
   - BI/TR consumability check;
   - BI 5-pass audit;
   - this 6-pass adversarial audit.

Completion status after this audit: blocked on producer-language cleanup.
