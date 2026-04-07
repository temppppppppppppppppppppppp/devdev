# 10-Pair TR/BI Legacy Meta Cleanup — Terminal 07 / Pair 07

- Date: 2026-04-07
- Status: read-only bounded survey output
- Document Type: terminal lane output
- Canonical Path: `docs/2026-04-07/10pair_meta_cleanup_terminal07_pair07.md`
- Owner: Opus Terminal 07
- Order: `docs/2026-04-07/10pair_tr_bi_legacy_meta_cleanup_10terminal_opus_order.md`
- Family Overlay: `blockguide`
- Mode: `read-only / no repair / no pair mutation / no docs/temp mutation`
- Baseline Commit: `5c71b81a36ab2cbae824c630bb63219354b913a8`

## 1. Terminal Scope

Bounded read-only survey of legacy `Block / ARC / Phase / Stage` meta wording in pair `07` only.
This is not pair-truth repair, not TR completion, not BI rewrite, not promotion, and not Stage 2/3/4 probing.
Per the order, pair `07` is a `mixed` pair from the prior `10pair_tr_bi_consistency_bounded_survey`, so meta-wording findings must be kept strictly separate from prior pair-truth drift.

## 2. Assigned Pair

| Slot | Path |
| --- | --- |
| Pair | `07` |
| Family overlay | `blockguide` |
| TR | `treatments/07_office_checkup_next_day_tr_block_070_draft.json` |
| BI | `bible/07_bi_office_checkup_next_day.json` |

## 3. Artifact Truth

| Check | TR | BI |
| --- | --- | --- |
| File exists | yes | yes |
| UTF-8 decode | pass | pass |
| JSON parse | pass | pass |
| Top shape | `dict { _schema: "tr.v1", _total_blocks: 70, blocks: [70] }` | `dict { _schema_version, _schema_description, _last_updated, _genre, MasterBible{ ProjectData, protagonist_config, FinanceHUD, MartialHUD, WorldState, AssetLibrary, Seeds, HistoricalEvents, GenreRules, plot_roadmap[70] } }` |
| Block count | `70` | `plot_roadmap` length `70` (mirrors TR 1:1) |

No `_sync_manifest` exists in this BI, so the prior pair `10`-style sync-count concern does not apply here.

## 4. Raw-Count Snapshot

A pure regex prevalence sweep over the assigned pair (recursive walk over all string leaves), using the meta lexicon from `meta-language-leak-context-handoff.md` §4 (`Block N`, `BLOCK N`, `block N`, `블록 N`, `ARC-N`, `Arc N`, `아크 N`, `Phase N`, `phase N`, `페이즈 N`, `Stage N`, `스테이지 N`, `B12` short form):

| Asset | Raw meta-token hits | Allowed structural metadata hits | Disallowed human-readable hits |
| --- | ---: | ---: | ---: |
| TR | `371` | `70` | `301` |
| BI | `415` | `91` | `324` |

Allowed structural hits in TR are dominated by `block_id = "Block N"` (`70`) which is on the §6.1 allow list.
Allowed structural hits in BI are dominated by `plot_roadmap[*].block_id` plus other structural numbering keys such as `block_no` and `foreshadow_targets`.

Raw-count interpretation rule from order §2:
- these are triage evidence only, not violation counts
- field-level classification below is the actual finding

Disallowed top forbidden leaf fields in TR (`leaf field : disallowed hit count`):

- `callback : 129`
- `foreshadow : 68`
- `section_rotation : 41`
- `reward (content.reward) : 12`
- `leverage_used (genre_ext.leverage_used) : 10`
- `context (content.context) : 9`
- `knowledge_used (genre_ext.knowledge_used) : 8`
- `solution (content.solution) : 4`
- `after / before (relationship_delta) : 5`
- `event_villain (content.event_villain) : 2`
- `success_pattern (genre_ext.success_pattern) : 2`
- `capital_after / capital_before (genre_ext) : 3`
- `method (genre_ext.method) : 1`
- additional minor leakage in `protagonist (power_shift)`, `antagonist`, `historical_event`, `risk_level`, `profit_loss`

Disallowed top forbidden leaf fields in BI:
- the same `callback / foreshadow / section_rotation / reward / context / leverage_used / knowledge_used / solution / event_villain / success_pattern / method / capital_*` distribution mirrored 1:1 inside `MasterBible.plot_roadmap[*]`
- plus BI-only leakage in `AssetLibrary.KeyNPCs[*].desc`, `AssetLibrary.KeyNPCs[*].key_turning_points[*].event`, `WorldState.opponent_transition_plan[*].phase`, `AssetLibrary.Partners[*].cadence`, `WorldState.starter_company.state` (start-state context only — borderline), `HistoricalEvents[*].summary`, `_schema_description`

## 5. Findings

### 5.1 `allowed_structural_meta` (correct, do not touch)

- TR: `blocks[*].block_id = "Block N"` — on §6.1 allow list (`block_id`), text form is just the canonical id, not a prose carrier
- TR: `blocks[*].block_no` — purely numeric structural id
- TR: `blocks[*].foreshadow_targets` / `callback_sources` — number arrays, on §6.1 allow list
- BI: `MasterBible.plot_roadmap[*].block_id` / `block_no` — structural mirror of TR
- BI: any `evolution` field — explicitly allowed by `SSOT_bi-evolution-metadata-standard.md` (none observed in this BI but documented for completeness)

These are not violations and must not be normalized.

### 5.2 `diegetic_meta_ref` (forbidden — meta wording inside human-readable fields)

The most concerning class. Meta tokens are embedded inside fields whose values are read as prose by downstream stages and ultimately by readers.

Pervasive in both assets:

- TR `blocks[*].callback[*]` (`129` hits): every callback string starts with `Block N에서 ...`. Example: `blocks[1].callback[0] = "Block 1에서 장현태가 '현장을 알아?'로 자른 이유의 진짜 동기가 드러난다 — ..."`. Per `meta-language-leak-context-handoff.md` §3.2 `callback` is explicitly a forbidden field for `Block / ARC / Phase / Stage` wording, and `foreshadow_targets` / `callback_sources` exist precisely so the prose field stays clean.
- TR `blocks[*].foreshadow[*]` (`68` hits): same pattern, e.g. `blocks[0].foreshadow[0] = "시혁의 SCM 보고서에 ... Block 5-7에서 ... 쓰인다."`
- TR `blocks[*].content.reward / content.context / content.solution / content.event_villain` (~`27` hits combined): block-narrative prose carrying explicit `Block N` references, e.g. `blocks[4].content.reward = "... 이 정보 비대칭이 Block 6-7의 행동을 가능하게 한다."`
- TR `blocks[*].genre_ext.success_pattern` and `blocks[*].genre_ext.method`: explicitly named in §3.2 as forbidden, e.g. `blocks[6].genre_ext.success_pattern = "Block 1 spike — 간판 장면. ..."`
- TR `blocks[*].genre_ext.leverage_used / knowledge_used / capital_after / capital_before / profit_loss`: short narrative summaries inside `genre_ext.*` that openly anchor to `Block N`. These are not on the §3.2 explicit list but per the §3.2 inference rule are clearly meant to be read as prose / labels, so they count.
- TR `blocks[*].relationship_delta.before / after` (~`5` hits): short prose deltas with `ARC-03`, `Block N` references.
- BI `MasterBible.plot_roadmap[*].*` (~`290` of the BI hits): the BI's `plot_roadmap` is a 1:1 mirror of the TR blocks, so every TR `diegetic_meta_ref` hit is duplicated here. Cleaning the TR carrier carries through if the BI mirror is regenerated from the cleaned TR; cleaning the BI directly without TR repair would produce drift.
- BI `MasterBible.AssetLibrary.KeyNPCs[1].desc = "적대자(팀장). Block 1부터 본격적으로 영향력을 행사한다."` — NPC description (read by downstream as prose).
- BI `MasterBible.AssetLibrary.Partners[0].cadence = "Phase 1: 공 가로채기"` — partner-cadence prose carrying `Phase 1` token.
- BI `MasterBible.HistoricalEvents[*].summary` — multiple summaries open with `이 블록은 ...` and reference `Block N` directly. Example: `HistoricalEvents[9].summary = "이 블록은 defeat다. ... Block 1의 B0보다는 올랐지만, ..."`.
- BI `_schema_description = "검진 다음 날, 터질 게 보인다 Bible - phase0/TR draft 동기화 산출물"`: short header but contains `phase0` token.

### 5.3 `label_meta_ref` (forbidden — meta wording inside label/short-title fields)

Per `meta-language-leak-context-handoff.md` §6, label fields are allowed to exist but their values must be natural language.

- TR `blocks[*].genre_ext.section_rotation` (`41` hits — every block): every value is of the form `"ARC-01 검진 다음 날"`, `"ARC-02 ..."`, `"ARC-03 숨겨진 숫자"`, etc. The natural-language portion is fine (`"검진 다음 날"`, `"숨겨진 숫자"`), but the leading `ARC-NN` prefix is exactly the leakage class the policy targets in §5.1 / §6 (`section_rotation = "원자재로 ..."` is `Good`; `section_rotation = "ARC-01 - 원자재로 ..."` is `Bad`).
- BI `MasterBible.plot_roadmap[*].genre_ext.section_rotation`: same `41`-block leakage mirrored through the BI plot_roadmap.
- BI `MasterBible.AssetLibrary.KeyNPCs[0].key_turning_points[*].event` — an NPC turning-point label such as `"ARC-01 대표 스파이크 - 물류 통합안 저지"`. This is a short event label, so it sits between `label_meta_ref` and `diegetic_meta_ref` — classified `label_meta_ref` because the field is acting as a per-event title.
- BI `MasterBible.WorldState.opponent_transition_plan[*].phase` — explicitly the `phase` key, which `meta-language-leak-context-handoff.md` §3.2 names as a forbidden human-readable field. Current value examples: `"Phase 1: 공 가로채기"`, `"Phase 2: ..."`.

### 5.4 `blocked_by_pair_truth` — checked, currently not blocking

The order requires terminal `07` to keep prior truth drift strictly separate from meta wording. Re-checking the prior `10pair_tr_bi_consistency_bounded_survey` §4.2 against the current baseline:

Prior claim (2026-04-06):
- `BI: protagonist_config.incarnation_type = "회귀자"` while `TR: regression_ext.is_regressor = false`
- `BI: financial_status.company_state` stuck at `Block 1`-style start state while `TR Block 70` end-state lives in `mobilizable_capital`

Observed in current baseline (`5c71b81a`):
- TR `blocks[0].regression_ext.is_regressor = false` and TR `blocks[69].regression_ext.is_regressor = false` (consistent with prior reading)
- BI `MasterBible.protagonist_config.incarnation_type = "각성"` (no longer `"회귀자"`)
- BI `MasterBible.FinanceHUD.Protagonist.actual_truth.financial_status.company_state = "경영기획팀장 + 그룹 구조조정 TF 실무총괄, 전략실/대표 보고 라인 확보, 라인 선택권 확보"` — this is the Block 70 end-state, not the Block 1 start state
- BI `MasterBible.protagonist_config.start_point.context = "한일유통 경영기획팀를 사수 퇴사 후 혼자 남은 팀 막내, 잡무 담당, 인사평가 B0 상태에서 되살려야 하는 출발점"` — correctly the start point, in its own field

Reading:
- the two `P2` truth blockers from the prior survey are no longer present in the current baseline; they appear to have been silently corrected sometime between `2026-04-06` and `2026-04-07`
- `각성` is consistent with `is_regressor = false` (각성 is awakening, not regression)
- start-state and end-state are now stored in the correct fields (`start_point.context` carries the start state, `financial_status.company_state` carries the end state)

Therefore: this terminal does not classify any current finding as `blocked_by_pair_truth`. The meta-wording cleanup is cleanly separable from the prior pair-truth drift, satisfying the order §10 separability gate for pair `07`.

This terminal does not assert that the prior truth drift was correctly repaired upstream — only that it is no longer observable in the current baseline. Codex should still spot-check the repair history before merging this lane.

## 6. Concrete Anchors (max 5)

1. `TR: blocks[0].genre_ext.section_rotation`
   - value: `"ARC-01 검진 다음 날"`
   - classification: `label_meta_ref` — natural-language tail is clean, but the `ARC-01` prefix is the exact `Bad` form in `meta-language-leak-context-handoff.md` §5.2; this single leakage repeats across all `41` rotation blocks.

2. `TR: blocks[1].callback[0]`
   - value: `"Block 1에서 장현태가 '현장을 알아?'로 자른 이유의 진짜 동기가 드러난다 — 보고서 내용이 아니라 MD사업부 비용 비교를 막기 위해서였다."`
   - classification: `diegetic_meta_ref` — `callback` is on the §3.2 explicit forbidden list; structural anchor belongs in `callback_sources` while the prose carries only natural language.

3. `TR: blocks[6].genre_ext.success_pattern`
   - value: `"Block 1 spike — 간판 장면. 직접 싸우지 않고, 상위 결재선의 입을 빌려 판을 뒤집는다."`
   - classification: `diegetic_meta_ref` — `genre_ext.success_pattern` is explicitly named in §3.2 as a forbidden field.

4. `BI: MasterBible.AssetLibrary.KeyNPCs[1].desc`
   - value: `"적대자(팀장). Block 1부터 본격적으로 영향력을 행사한다."`
   - classification: `diegetic_meta_ref` — NPC description is a clearly human-readable prose field per the §3.2 inference rule. This is BI-only leakage that does not get cleaned even if the TR plot_roadmap mirror is regenerated.

5. `BI: MasterBible.WorldState.opponent_transition_plan[0].phase`
   - value: `"Phase 1: 공 가로채기"`
   - classification: `label_meta_ref` — `phase` is explicitly named in §3.2 as a forbidden human-readable field; the value is a short label that should hold a natural-language stage name only, with structural numbering moved to `phase_no` or sibling structural metadata.

## 7. Severity

`P2`

Reason:
- repeated disallowed meta leakage in many fields (`callback`, `foreshadow`, `section_rotation`, `content.*`, `genre_ext.success_pattern`, `genre_ext.method`, `relationship_delta.*`, `WorldState.opponent_transition_plan[*].phase`, `AssetLibrary.KeyNPCs[*].desc`, `AssetLibrary.Partners[*].cadence`, `HistoricalEvents[*].summary`)
- the leakage is widespread but not random — it follows a small set of stable templates, so a bounded normalization pass should be tractable
- no `P0` evidence: the files exist, decode, and parse
- no current `P1` evidence: prior pair-truth blockers are not observable in the current baseline (see §5.4)
- not `P3`: this is well beyond sparse cosmetic leakage

## 8. Execution Route

`cleanup_now`

Smallest cleanup unit: `TR + BI`

Reason:
- pair-truth side appears clean in the current baseline, so wording cleanup is separable per order §10
- BI `plot_roadmap` is a 1:1 mirror of TR `blocks`, so cleaning only one side will desync the pair; either repair TR first and regenerate the BI mirror, or repair both sides in one bounded pass
- BI also carries non-mirror leakage (`AssetLibrary.KeyNPCs[*].desc`, `WorldState.opponent_transition_plan[*].phase`, `AssetLibrary.Partners[*].cadence`, `HistoricalEvents[*].summary`, `_schema_description`) that must be touched independently of any TR-side fix
- this terminal only proposes a route; it does not execute the cleanup, does not pick a normalization template, and does not write a patch order

## 9. One-Line Minimal Next-Step Suggestion

After Codex merges the `10` lane outputs, schedule a single bounded `pair 07 wording-only normalization` patch that drops the leading `ARC-NN` prefix on `genre_ext.section_rotation`, rewrites `callback / foreshadow / content.* / genre_ext.success_pattern / genre_ext.method` prose to natural language while moving any structural anchors into `callback_sources` / `foreshadow_targets`, and separately scrubs the BI-only `KeyNPCs[*].desc / opponent_transition_plan[*].phase / Partners[*].cadence / HistoricalEvents[*].summary / _schema_description` leakage — all without touching `block_id`, `block_no`, structural numeric arrays, or any `evolution` field.

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-07 output
