# 10-Pair Meta Cleanup — Terminal 02 / Pair 02

- Date: 2026-04-07
- Status: final
- Document Type: read-only bounded survey (single pair)
- Canonical Path: `docs/2026-04-07/10pair_meta_cleanup_terminal02_pair02.md`
- Parent Order: `docs/2026-04-07/10pair_tr_bi_legacy_meta_cleanup_10terminal_opus_order.md`
- Baseline Commit: `5c71b81a36ab2cbae824c630bb63219354b913a8`

## 1. Terminal Scope

- read-only legacy meta wording survey on the live numbered pair `02` only
- no repair, no code edits, no `docs/temp/` mutation, no live pair mutation
- output must classify `allowed_structural_meta` vs `diegetic_meta_ref` vs `label_meta_ref` vs `blocked_by_pair_truth`
- final merge into `10pair_tr_bi_legacy_meta_cleanup_bounded_survey.md` is reserved for Codex

## 2. Assigned Pair And Family

- pair: `02 — chaebol_allowance_zero`
- TR: `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json`
- BI: `bible/02_bi_chaebol_allowance_zero.json`
- family: `blockguide` (modern-fantasy business-power, sub-profile reads as cashflow × office-power composite per BI `_genre`)
- prior pair status (per `docs/2026-04-06/10pair_tr_bi_consistency_bounded_survey.md`): `clean` / `P3`
- prior survey final reading: "strong blockguide alignment, genre key naming noise only"

## 3. Artifact Truth

| Check | TR | BI |
| --- | --- | --- |
| file exists | yes | yes |
| size on disk | `342,194` bytes | `493,550` bytes |
| UTF-8 decode | succeeds (no BOM) | succeeds **only with `utf-8-sig`** — file carries a leading UTF-8 BOM |
| JSON parse | succeeds, dict, `_total_blocks = 70`, `len(blocks) = 70` | succeeds, dict, `MasterBible` root with `plot_roadmap` mirroring TR 70 blocks |
| pair-truth integrity | `_work_id = "chaebol_allowance_zero"` matches BI `_work_id` | matches TR; same protagonist, arc, expansion order |

Note on the BOM:

- the BI is still strict UTF-8 in payload terms, so this is not `P0`
- it is a cosmetic/encoding hygiene item that the eventual cleanup patch should normalize, but it does not block the wording survey

## 4. Raw Count Snapshot

Read-only token-prevalence scan (regex covers `Block / 블록 / B\d+ / ARC[-_ ]?\d+ / 아크 / Arc / Phase / 페이즈 / Stage / 스테이지` forms, leaf-field aware):

| Source | raw meta-token hits | `allowed_structural_meta` | `diegetic_meta_ref + label_meta_ref` |
| --- | ---: | ---: | ---: |
| TR | `354` | `70` | `284` |
| BI | `431` | `91` | `340` |

The order's prior triage table reported `TR 394 / BI 485`. The delta is regex-shape variance only and stays in the same order of magnitude. Per the order's interpretation rule, raw counts are evidence that the surface is wide enough to justify a bounded review, not failure counts.

Top disallowed leaf-field buckets:

- TR: `foreshadow:85`, `section_rotation:70`, `content.solution:32`, `content.context:27`, `stakes:19`, `callback.note:15`, `content.reward:10`
- BI: `foreshadow:85`, `section_rotation:70`, `content.solution:32`, `content.context:27`, `stakes:19`, `callback.note:15`, `operational_power_gain:12`, `content.reward:10`, `seed:8`, `payoff:8`, `expansion_order_locked:7`, `expansion_order:7`, `event:6`, `phase:3`

## 5. Findings

### 5.1 `allowed_structural_meta`

These hits are pure structural metadata and must NOT be cleaned:

- `TR: blocks[*].block_id` — 70 entries of literal `"Block N"` IDs (`block_id` is on the allowed list)
- `BI: MasterBible.WorldState.front_sector_by_arc[*].arc_id` — `"ARC-01" .. "ARC-07"` (pure `arc_id`)
- `BI: MasterBible.AssetLibrary.ArcSheets[*].arc_id` — same canonical `arc_id` set
- `BI: MasterBible.AssetLibrary.OperationalPowerByArc[*].arc_id` — same
- `BI: MasterBible.AssetLibrary.CapitalCurve[*].block_no` / `block_id` — pure structural numbering

There is no `evolution`-keyed string in this pair, so the `evolution` allowance from `SSOT_bi-evolution-metadata-standard.md` does not need to be invoked.

### 5.2 `diegetic_meta_ref`

These are number-meta tokens that have leaked into prose-facing fields and must be rewritten as natural language. The pattern is **systemic, not isolated** — TR `blocks[*]` and BI `MasterBible.plot_roadmap[*]` are mirror objects that share the same prose, so almost every TR leak is duplicated in BI.

Coverage by field type:

- `content.context` — 27 paragraphs reference `Block N`, e.g. `Block 6`, `Block 4`, `Block 7`, `Block 8`, `Block 17`, `Block 20` are quoted inside in-scene context prose
- `content.solution` — 32 paragraphs reference `Block N` inside the in-scene solution narration (e.g. `Block 12`, `Block 63`, `Block 5`, `Block 8`, `Block 14`)
- `content.reward` — 10 paragraphs use `Block N` references such as "Block 17 공동 인수의 씨앗"
- `stakes` — 19 entries quote `ARC-02`, `ARC-03` inside the in-scene stakes line ("ARC-02 전체가 무너진다")
- `foreshadow` — 85 entries are written as full sentences containing `Block N` (e.g. "노현주가 봉인한 유언장 뒷면 조항은 Block 63에서 다시 열린다.")
- `callback.note` — 15 entries open with `"Block N의 ..."` instead of using `callback_sources` for the number and natural language for the meaning
- `BI: MasterBible.AssetLibrary.CapitalCurve[*].event` — 6 entries written as `"ARC-0X exit — ..."` prose
- `BI: MasterBible.AssetLibrary.ArcSheets[*].operational_power_gain[*]` — 12 entries appended with `"(ARC-0X 입장권)"` parenthetical inside human-readable gain descriptions
- `BI: MasterBible.WorldState.expansion_order_locked[*]` and `BI: MasterBible.AssetLibrary.BusinessAxis.expansion_order[*]` — 14 entries written as `"공장 (ARC-03)"` style prose tags

### 5.3 `label_meta_ref`

Number-meta leakage inside fields that are *labels* meant to be read by humans but live alongside structural keys:

- `genre_ext.section_rotation` — 70 entries open with `"ARC-0X - <human label>"` pattern (this is exactly the canonical "Bad" example from `meta-language-leak-context-handoff.md` §5.2). Mirrored in TR `blocks[*]` and BI `MasterBible.plot_roadmap[*]`.
- `BI: MasterBible.WorldState.opponent_transition_plan[*].phase` — 3 entries written as `"Phase 1: 초기 감시·차단"` etc. The structural slot already exists; the value should be natural language only.

### 5.4 `blocked_by_pair_truth`

None.

Pair `02` is on the prior bounded survey's `clean` list with no `P0` / `P1` / `P2` truth blockers; only `P3` naming noise was noted. This wording cleanup is **separable** from any pair-truth repair, because:

- TR and BI agree on `_work_id`, protagonist, arc count (`7`), block count (`70`), expansion order, and CFO/family conflict architecture
- the leakage is consistently *wording* — same English-form meta tokens dropped into mirrored prose fields, not contradictory facts

## 6. Concrete Anchors (5 max, key-path first)

1. `BI: MasterBible.plot_roadmap[0].foreshadow[0]` → `"노현주가 봉인한 유언장 뒷면 조항은 Block 63에서 다시 열린다."` — canonical `diegetic_meta_ref` in `foreshadow`. Mirrored at `TR: blocks[0].foreshadow[0]`. Number must move into `foreshadow_targets`, prose must restate the meaning without `Block 63`.
2. `BI: MasterBible.plot_roadmap[0].genre_ext.section_rotation` → `"ARC-01 - 카드 차단 직후 운영권 확보"` — canonical `label_meta_ref`. Mirrored at `TR: blocks[0].genre_ext.section_rotation` and 69 sibling blocks. The `ARC-0X - ` prefix should be dropped; arc grouping is already carried by `arc_id`.
3. `BI: MasterBible.plot_roadmap[1].callback[0].note` → `"Block 1의 '외부인 책임' 해석이 이번 블록의 응급 배식 개입 근거로 재사용된다."` — `diegetic_meta_ref` in `callback.note`. The `Block 1` token belongs in `callback_sources`; the note must read as standalone prose.
4. `BI: MasterBible.AssetLibrary.CapitalCurve[2].event` → `"ARC-01 exit — 호텔 백오브하우스 진입 명분(다음 운영 전장 입장권) 확보. 형 서도윤 시선 전환."` — `diegetic_meta_ref` inside a human-readable `event` line. The arc identity should come from the surrounding `arc_id`/`block_no`, not from a `"ARC-01 exit — "` prefix.
5. `BI: MasterBible.WorldState.opponent_transition_plan[0].phase` → `"Phase 1: 초기 감시·차단"` — `label_meta_ref` in a label slot whose adjacent structural index already encodes the phase order. The `"Phase 1: "` prefix is the disallowed bit; the natural-language description survives.

## 7. Final Severity

- `P2`

Reason: per the order's severity table, `P2 = repeated disallowed meta leakage exists and bounded cleanup should be scheduled soon`. The disallowed leakage in this pair is not sparse — it covers `foreshadow / callback.note / content.context / content.solution / content.reward / stakes / section_rotation / phase / expansion_order / CapitalCurve.event / operational_power_gain` across all 70 mirrored blocks plus several BI-only structures. It is well above the `P3 = sparse or cosmetic` floor, but it is not `P1` because pair truth is intact and the leakage is wording-only.

## 8. Final Execution Route

- `cleanup_now`

The smallest cleanup unit is **`TR + BI`**, not `BI only`, because:

- the leakage is concentrated in fields that the TR and BI mirror byte-for-byte (`blocks[*]` ⇄ `MasterBible.plot_roadmap[*]`): `foreshadow`, `callback.note`, `genre_ext.section_rotation`, `content.context/solution/reward`, `stakes`
- BI-only structures (`expansion_order_locked`, `expansion_order`, `CapitalCurve.event`, `OperationalPowerByArc.operational_power_gain`, `opponent_transition_plan.phase`) carry additional leakage that cleanup must also address, but they cannot be split off without resyncing with TR's `genre_ext` and `plot_roadmap` shapes
- `truth_repair_first` is not required (pair truth is `clean`)
- `tr_completion_first` is not required (TR has all 70 blocks complete, `_draft_status = "ARC-01~07 complete (blocks 1-70). TR draft full."`)
- `no_action` would leave the canonical "Bad" pattern from `meta-language-leak-context-handoff.md` §5.2 alive in 70 mirrored places

## 9. Minimal Next-Step Suggestion

Codex should schedule a bounded `TR + BI` wording cleanup pass on pair `02` that (a) moves `Block N` / `ARC-0X` tokens from prose fields into `foreshadow_targets` / `callback_sources`, (b) strips `"ARC-0X - "` prefixes from `genre_ext.section_rotation` and the `"Phase N: "` prefixes from `opponent_transition_plan[*].phase`, (c) rewrites `CapitalCurve[*].event`, `expansion_order(_locked)[*]`, and `operational_power_gain[*]` parenthetical arc tags as natural language, and (d) opportunistically strips the BI's leading UTF-8 BOM during the same pass.

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-07 output
