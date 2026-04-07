# 10-Pair Meta Cleanup Terminal 03 — Pair 03

- Date: 2026-04-07
- Status: final
- Document Type: bounded read-only survey (one terminal, one pair)
- Canonical Path: `docs/2026-04-07/10pair_meta_cleanup_terminal03_pair03.md`
- Owning Order: `docs/2026-04-07/10pair_tr_bi_legacy_meta_cleanup_10terminal_opus_order.md`
- Terminal: `03`
- Assigned Pair: `03`
- Family: `blockguide`
- Baseline Commit: `5c71b81a36ab2cbae824c630bb63219354b913a8`

## 1. Terminal Scope

- read-only survey of pair `03` only
- classify legacy `Block / ARC / Phase / Stage` meta wording in the live numbered `TR + BI` pair
- separate `allowed_structural_meta` from `diegetic_meta_ref` and `label_meta_ref`
- do not mutate `treatments/`, `bible/`, `docs/temp/`, code, or any other unrelated dirty file
- do not write the merged cleanup order or any patch plan
- do not touch other terminals' output files

## 2. Assigned Pair

- Work identity: `03_chaebol_ent_empire` (세령컬처웍스 / 엔터테인먼트 제국)
- Family overlay: `blockguide`
- Profile reading: `entertainment_media_profile` (엔터/방송/IP/팬덤) under blockguide general mode
- TR: `treatments/03_chaebol_ent_empire_tr_block_070_draft.json`
- BI: `bible/03_bi_chaebol_ent_empire.json`
- Prior pair-consistency verdict: `clean` / `P3` — see `docs/2026-04-06/10pair_tr_bi_consistency_bounded_survey.md` §3 and §4.1

## 3. Artifact Truth

| Check | TR | BI |
| --- | --- | --- |
| file exists | yes (357,719 bytes) | yes (442,281 bytes) |
| UTF-8 decode | pass | pass |
| JSON parse | pass | pass |
| top type | `dict` | `dict` |
| top keys | `_schema`, `_total_blocks`, `blocks` | `_schema_version`, `_schema_description`, `_last_updated`, `_genre`, `_repair_note`, `MasterBible` |
| block count | `70` (`blocks[]` length = 70, `block_id` = `Block 1`..`Block 70`) | `70` (`MasterBible.plot_roadmap[]` length = 70) |

Both artifacts parse cleanly. No `P0` condition.

## 4. Raw Meta-Token Snapshot

Regex set applied: `Block \d+`, `ARC[-_ ]?\d+`, `Arc \d+`, `Phase \d+`, `Stage \d+`, `B\d+`, `블록 \d+`, `아크 \d+`, `페이즈 \d+`.

| Artifact | Total raw meta-token hits | Dominant form |
| --- | ---: | --- |
| TR | `156` | `Block N` × 155, `Phase N` × 1 |
| BI | `215` | `Block N` × 185, `ARC-NN` × 14, `Phase N` × 8, `BN` × 7, `블록 N` × 1 |

Interpretation note per order §2: the raw counts are triage evidence only, not failure counts. The field-level classification in §5 is the actual reading.

## 5. Field-Level Findings

### 5.1 `allowed_structural_meta`

These key-paths carry meta tokens but are explicitly allowed by the order §6.1 and by `docs/narrative-router/SSOT_bi-evolution-metadata-standard.md` §5.

- `TR: blocks[*].block_id` — 70 entries, each a `Block N` ID string. Key is in the allowed structural set, so the `Block N` form is legal even though it is the English-form meta token.
- `BI: MasterBible.plot_roadmap[*].block_id` — same 70 entries, mirror of TR.
- `BI: MasterBible.ProjectData.CoreIdentity.evolution[0..6]` — 7 compact arrow-trace lines like `Phase 1 (B1-10): 사람 발굴 ...`. `evolution` is explicitly allowed to carry block/phase trace per SSOT_bi-evolution-metadata-standard.md §5. No violation.
- `BI: MasterBible.opponent_transition_plan[*].arc` — 7 entries holding pure ID strings like `ARC-01`, `ARC-02`. Functionally an `arc_id`. The canonical allowed keys are `arc_id`/`arc_no`, so this is **non-canonical key naming** rather than a value leak. Classify as `allowed_structural_meta_under_non_canonical_key_name` — still structural, but the key should be renamed to `arc_id` during cleanup so the allow-list matches literally.

### 5.2 `label_meta_ref`

These are label-shaped fields whose values carry disallowed `Block / ARC / Phase / Stage` wording. Labels may exist, but values must be natural language.

- `BI: MasterBible.opponent_transition_plan[*].section_rotation` — 7 entries, all in the canonical bad form `ARC-01 — 쓰레기통에서 사람 찾기`, `ARC-02 — 배우·연습생으로 첫 증명`, etc. This is the exact bad example in `meta-language-leak-context-handoff.md` §5.2. Textbook `label_meta_ref`.
- `BI: MasterBible.opponent_transition_plan[*].methods[*]` — 9 string entries of the form `"감사실 칼날(Block 16)"`, `"아버지의 진짜 조건(Block 18)"`, `"방송 채널 차단(Block 23)"`. These are human-readable method labels with inline block-number parentheticals. Per the inference rule in §6.2 of the owning order, short human-readable label items fall under `label_meta_ref`. The block tethers should move out of the label text into a structural `trigger_blocks` sibling (or an `entry_block` style field that already exists on the same object).

### 5.3 `diegetic_meta_ref`

These are natural-language or prose-shaped fields whose bodies still carry `Block N` / `ARC-NN` / `Phase N` wording. These are the primary cleanup mass for pair `03`.

TR side (prose leakage):

- `TR: blocks[*].callback[*]` — **63 hits across blocks `6..70`**. The dominant leakage vector. Example: `"Block 4-5의 패배와 추적을 겪은 뒤 사람을 재결집시키는 밤이다."`. Callback prose repeatedly names `Block N` instead of using `callback_sources` + natural-language summary.
- `TR: blocks[*].foreshadow[*]` — 2 hits. Example at block `6`: `"이 밤에 잡힌 쇼케이스 기획안이 Block 7의 구체적 실행으로 이어진다."`. Use `foreshadow_targets: [7]` + natural prose.
- `TR: blocks[*].content.context` — 5 hits. Example at block `5`: prose that cites `Block 1-3에서 ...`. `content.*` is explicitly disallowed per order §6.2.
- `TR: blocks[*].content.reward` — 3 hits. Prose citing `Block 1-N`.
- `TR: blocks[*].stakes` — 3 hits. `stakes` is explicitly disallowed per order §6.2.
- `TR: blocks[*].{event_villain, solution, method, leverage_used}` — 4 additional single-hit prose fields each carry one `Block N` token (mostly inside `content.*` sub-objects of a few blocks). Same diegetic leak class.

BI side (prose leakage):

- `BI: MasterBible.plot_roadmap[*].callback[*]` — **63 hits**, mirror of TR. Example block 2 callback[0]: `"Block 1에서 강이현을 보자마자 멈춘 태하의 시선이 이번에는 윤서아에게 반복된다."`. Same cleanup unit as TR callback.
- `BI: MasterBible.plot_roadmap[*].foreshadow[*]` — 2 hits. Same pattern as TR.
- `BI: MasterBible.plot_roadmap[*].content.context` — 5 hits.
- `BI: MasterBible.plot_roadmap[*].content.reward` — 3 hits.
- `BI: MasterBible.plot_roadmap[*].stakes` — 3 hits.
- `BI: MasterBible.AssetLibrary.KeyNPCs[*].desc` — 7 hits. Example NPC `[2].desc`: `"...Block 68에서 공급망·지분 공작이 폭로되며 명분을 잃고 무너진다."`. NPC description prose.
- `BI: MasterBible.HistoricalEvents.events[*].summary` — 6 hits. Prose event summaries citing `Block 1-3` style ranges.
- `BI: MasterBible.HistoricalEvents.events[*].impact` — 1 hit. Example: `"Block 1-15에서 쌓은 모멘텀이 통째로 날아간다."`.
- `BI: MasterBible.ProjectData.CommercialCode.defeat_mechanic` — 1 hit. Example: `"Block 55 pyrrhic victory, Block 63 경영권 탈취가 이 패턴."`.
- `BI: MasterBible.foreshadow_map[*].payoff` — 1 hit. Example: `"...Block 55의 pyrrhic victory를 만들고, Block 60에서 구조적 탈피로 해소."`.
- `BI: MasterBible.Seeds[*].description` — 1 hit. Example: `"자본 흐름의 이상 징후(Block 39, 48)가 장부 카드로 축적되어 최종 폭로 증거가 된다."`.
- `BI: MasterBible.WorldState.CurrentEra` — 1 hit. `"2009년 시작, Block 70 기준 추정 2020년대 초반"`. `Block 70 기준` is a meta tether inside a world-state prose field.

### 5.4 `blocked_by_pair_truth`

Not applicable. Pair `03` was rated `clean` / `P3` in `docs/2026-04-06/10pair_tr_bi_consistency_bounded_survey.md` §4.1. Pair identity, protagonist engine, TR/BI alignment, and TR production completeness are all intact. Nothing found in this terminal's read changes that reading. Wording cleanup can proceed without prior truth repair.

## 6. Concrete Anchors (up to 5)

1. `TR: blocks[5].callback[0]` — `"Block 4-5의 패배와 추적을 겪은 뒤 사람을 재결집시키는 밤이다."` — representative of the dominant `callback` leakage on both sides; 63×2 cleanup mass.
2. `BI: MasterBible.plot_roadmap[5].foreshadow[1]` — `"이 밤에 잡힌 쇼케이스 기획안이 Block 7의 구체적 실행으로 이어진다."` — classic foreshadow-with-number leak; should move to `foreshadow_targets: [7]` plus natural prose.
3. `BI: MasterBible.opponent_transition_plan[0].section_rotation` — `"ARC-01 — 쓰레기통에서 사람 찾기"` — textbook `label_meta_ref` (identical shape to `meta-language-leak-context-handoff.md` §5.2 bad example).
4. `BI: MasterBible.opponent_transition_plan[1].methods[0]` — `"감사실 칼날(Block 16)"` — `label_meta_ref` with inline `(Block N)` tether.
5. `BI: MasterBible.ProjectData.CoreIdentity.evolution[0]` — `"Phase 1 (B1-10): 사람 발굴 — 재능의 터질 타이밍을 읽는다"` — confirms the `evolution` path is `allowed_structural_meta`; do **not** false-positive this during cleanup.

## 7. Severity

`P2`.

Reason:

- no decode / parse / file-missing failure (not `P0`)
- pair truth is stable and the prior consistency survey explicitly rated pair `03` as `clean` (not `P1`)
- the leakage is not sparse or cosmetic — `callback` alone is 63 hits on each side, and leakage is also present in `section_rotation`, `methods`, `content.context`, `content.reward`, `stakes`, `foreshadow`, NPC `desc`, event `summary/impact`, `defeat_mechanic`, `foreshadow_map.payoff`, `Seeds.description`, and `WorldState.CurrentEra` (not `P3`)
- the shape is exactly the downstream-risk pattern `meta-language-leak-context-handoff.md` §7 is trying to block: narrative-facing prose citing `Block N`

## 8. Execution Route

`cleanup_now`.

Smallest cleanup unit: `TR + BI`.

Rationale:

- `callback[]` leakage is symmetric on both sides (63 TR + 63 BI) and repairs cleanly only if both sides are rewritten together into natural-language bodies plus a structural sibling (`callback_sources: [n, ...]`).
- `foreshadow[]`, `content.context`, `content.reward`, `stakes` are also mirrored on both sides in the plot-roadmap / blocks array.
- BI-only tails still exist (`section_rotation`, `methods`, `desc`, `summary`, `impact`, `defeat_mechanic`, `payoff`, `Seeds.description`, `CurrentEra`, `opponent_transition_plan.arc` key rename), so a `BI only` scope would leave TR-side callback prose dirty.
- A `TR only` scope would leave the BI mirror plus the BI-only tails dirty.
- Therefore the minimal safe cleanup scope is the paired rewrite.

## 9. One-Line Minimal Next Step

Rewrite `callback[]` on both TR `blocks[*]` and BI `plot_roadmap[*]` as natural-language prose with a new sibling `callback_sources: [n, ...]`, then sweep `foreshadow[]`, `content.context/reward`, `stakes`, `section_rotation`, `methods[]`, NPC `desc`, `HistoricalEvents.events[].summary/impact`, `CommercialCode.defeat_mechanic`, `foreshadow_map[].payoff`, `Seeds[].description`, and `WorldState.CurrentEra` in the same patch wave; leave `block_id` and `evolution` alone.

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-07 output
