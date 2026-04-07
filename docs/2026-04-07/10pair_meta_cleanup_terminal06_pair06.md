# 10-Pair TR/BI Legacy Meta Cleanup — Terminal 06 / Pair 06

Date: 2026-04-07
Status: final
Document Type: bounded read-only survey output
Canonical Path: `docs/2026-04-07/10pair_meta_cleanup_terminal06_pair06.md`
Parent Order: `docs/2026-04-07/10pair_tr_bi_legacy_meta_cleanup_10terminal_opus_order.md`
Baseline Commit: `5c71b81a36ab2cbae824c630bb63219354b913a8`

## 1. Terminal Scope

- read-only bounded survey of a single numbered pair
- classify meta wording into `allowed_structural_meta`, `diegetic_meta_ref`, `label_meta_ref`, or `blocked_by_pair_truth`
- no repair
- no pair mutation
- no docs/temp mutation
- no patch execution order
- no pair regrading beyond the prior consistency survey

## 2. Assigned Pair and Family

- Pair: `06`
- Family: `blockguide` (business-power / 세원 heir storyline)
- TR: `treatments/06_gatekeeper_heir_tr_block_070_draft.json`
- BI: `bible/06_bi_gatekeeper_heir.json`

## 3. Artifact Truth

| Artifact | Exists | UTF-8 decode | JSON parse |
| --- | --- | --- | --- |
| TR | yes | yes | yes (root object with `blocks[70]`) |
| BI | yes | yes | yes (root object, `MasterBible.*` tree present) |

- no file-level P0 conditions detected
- prior `10pair_tr_bi_consistency_bounded_survey.md` verdict for pair 06 = `clean`, highest severity `P3`, cosmetic/wording drift only
- therefore this survey is not gated by `blocked_by_pair_truth`; wording is cleanly separable from any structural drift

## 4. Raw-Count Snapshot

Meta-lexicon scanned: `Block N`, `B\d+`, `블록 N`, `ARC-?N`, `Arc N`, `아크 N`, `Phase N`, `페이즈 N`, `Stage N`, `스테이지 N`.

| File | Raw meta-token hits | `allowed_structural_meta` | `label_meta_ref` | `diegetic_meta_ref` |
| --- | ---: | ---: | ---: | ---: |
| TR | `977` | `70` | `75` | `832` |
| BI | `1033` | `91` | `80` | `862` |

Classification rules applied per `meta-language-leak-context-handoff.md` §3 and `SSOT_bi-evolution-metadata-standard.md`:

- `allowed_structural_meta`: `block_id`, `arc_id`, `arc_no`, `phase_no`, `stage_no`, `foreshadow_targets`, `callback_sources`, `evolution`
- `label_meta_ref`: value sits in a label field (`section_rotation`, `arc_section`, `phase`, `phase_label`) but carries `ARC-N / Phase N / Block N` tokens instead of clean natural-language labels
- `diegetic_meta_ref`: value sits in a prose / scene-facing field (`content.*`, `stakes`, `power_shift.*`, `relationship_delta.before/after`, `genre_ext.method`, `genre_ext.success_pattern`, `foreshadow`, `callback`, and other clearly human-readable prose like `reward`, `solution`, `leverage_used`, `context`, `desc`, `total_assets` descriptions)

Raw counts are used as triage evidence only, not as failure counts.

## 5. Findings

### 5.1 `allowed_structural_meta` — contrast only, not a violation

- TR `blocks[*].block_id` (`70` hits): values like `"Block 1"` … `"Block 70"` — the policy explicitly permits block numbering inside `block_id`, so these are not leakage.
- BI `MasterBible.WorldState.front_sector_by_arc[*].arc_id` (`21` hits total under `arc_id` leaf): values like `"ARC-01"` … `"ARC-06"` — allowed per §6.1 of the order and per `SSOT_bi-evolution-metadata-standard.md`.
- BI `MasterBible.Protagonist.*.evolution` / engine-like `evolution` entries: values carrying block-trace strings are allowed because `evolution` is a structural metadata key by policy.

Interpretation: the majority of the `allowed_structural_meta` hits in this pair are exactly where policy wants them, so the `70`+`91` allowed-class hits should be subtracted from any raw failure framing.

### 5.2 `label_meta_ref` — systematic, repair-worthy

- **TR `blocks[*].genre_ext.section_rotation`** (`70` hits, 100% of blocks): every block prefixes the rotation label with `ARC-0N - ...`, e.g. `"ARC-01 - 회귀 직후 독대권 확보"`, `"ARC-01 - 독대권을 실전 테이블로 전환"`. Per §6 of the handoff doc, `section_rotation` must exist but the value must be natural-language only; the `ARC-0N - ` prefix is a pure leakage artifact. Systematic, identical pattern across all 70 rotations.
- **BI `MasterBible.plot_roadmap[*].genre_ext.section_rotation`** (`70` hits): mirrors the TR side 1:1 — the BI copied the TR rotations verbatim, so the same prefix leak propagates into BI. Single systematic fix on TR will cascade here on resync.
- **BI `MasterBible.WorldState.opponent_transition_plan[*].phase`** (`5` hits): values `"Phase 1: 비용센터 사고"`, `"Phase 2: 공급망 인질극"`, `"Phase 3: 시스템 거부"`, `"Phase 4: 공장 밖의 장벽"`, `"Phase 5: 쪼개기 제국"`. The `phase` leaf is on the forbidden label list in §3.2 of the handoff doc; the natural-language label is already present but the `Phase N:` prefix is a direct leakage marker.

No `label_meta_ref` hits were found on `arc_section` or `phase_label` in this pair.

### 5.3 `diegetic_meta_ref` — systematic, widest surface

Distribution of leakage leaf-fields (human-readable prose), both files combined:

| Leaf field | TR hits | BI hits | Field kind |
| --- | ---: | ---: | --- |
| `foreshadow` | `179` | `179` | narrative prose array in `blocks[*].foreshadow[*]` (and mirrored in BI `plot_roadmap[*].foreshadow[*]`) |
| `callback` | `221` | `221` | narrative prose array |
| `reward` | `44` | `44` | block/arc reward prose |
| `success_pattern` | `33` | `33` | `genre_ext.success_pattern` — explicitly on the forbidden list |
| `before` / `after` | `29` / `4` | `29` / `4` | `relationship_delta.before/after` — explicitly on the forbidden list |
| `leverage_used` | `23` | `23` | `genre_ext.leverage_used[*]` prose |
| `solution` | `22` | `22` | prose solution-line |
| `event_villain` | `14` | `14` | prose villain-line |
| `context` | `9` | `9` | `start_point.context` and similar scene-facing prose |
| `protagonist` | `8` | `8` | protagonist-facing prose |
| `stakes` | `7` | `7` | explicitly on the forbidden list |
| `capital_delta` | `7` | `7` | prose delta line |
| `desc` | `0` | `9` | BI-only: `MasterBible.AssetLibrary.KeyNPCs[*].desc` (`"…Block N부터 본격적으로 영향력을 행사한다."`) |
| `total_assets` (prose) | `0` | several | BI-only: `MasterBible.FinanceHUD.Protagonist.actual_truth.portfolio_history[*].total_assets` prose summary carrying `ARC-04/05/06 진입점` |

Observations:

- TR ↔ BI foreshadow/callback counts are identical at the leaf level (`179 / 221`), meaning the BI mirrored the TR prose wholesale. A single-pass TR rewrite on these fields will propagate to BI on resync.
- The leakage pattern inside prose is consistent: `Block N에서 확보한 …`, `… Block 3에서 회장실 안으로 들어간다`, `Block 4에서 확보한 세원정밀 지휘권`, `Block 007에서 48시간 구출전의 돌파구`, `ARC-04 진입점 확보`. These are exactly the `downstream meta erosion` failure mode that §7 of the handoff doc is written to prevent — i.e. characters/narrator-facing text would carry `Block N`/`ARC-N` tokens into Stage 2/3/4.
- The BI-only `KeyNPCs[*].desc` pattern (`"…Block N부터 본격적으로 영향력을 행사한다."`) is a BI-side templated generator leak — this is a separate, narrower cleanup surface from the TR foreshadow/callback prose.
- The BI-only `portfolio_history[*].total_assets` prose carries `ARC-NN 진입점` suffixes, which is diegetic leakage inside a HUD snapshot prose field, not structural metadata.

### 5.4 `blocked_by_pair_truth` — none

- the `10pair_tr_bi_consistency_bounded_survey.md` merged verdict for pair 06 is `clean / P3`, with only `start_point.context = "세원정밀를 ..."` typo and end-state snapshot convention as prior notes
- this terminal did not find new truth contradictions during the wording survey
- wording cleanup on pair 06 is cleanly separable from any pair-truth repair
- this terminal therefore does not tag any finding as `blocked_by_pair_truth`

## 6. Concrete Anchors (5 total, per output contract §9)

1. `TR: blocks[*].genre_ext.section_rotation` — label leak: every one of 70 rotations carries an `"ARC-0N - "` prefix before the natural-language label. Systematic `label_meta_ref`; single regex-style prefix strip fixes all 70 entries and the identical BI mirror.
2. `BI: MasterBible.WorldState.opponent_transition_plan[*].phase` — label leak: 5 entries carry a `"Phase N: "` prefix before the natural-language phase name. Systematic `label_meta_ref`, `phase` leaf is explicitly on the forbidden list.
3. `TR: blocks[*].foreshadow[*]` + `TR: blocks[*].callback[*]` — diegetic leak: `~400` prose entries reference `Block N` / `Block 007` directly inside the narrative text (e.g. `"Block 1에서 확보한 독대 요구가 실제 회장실 10분으로 전환된다."`). Core `diegetic_meta_ref` surface; wording must be rewritten into natural language with structural info moved into `foreshadow_targets` / `callback_sources`.
4. `BI: MasterBible.AssetLibrary.KeyNPCs[*].desc` — diegetic leak: templated NPC descriptions read `"…Block N부터 본격적으로 영향력을 행사한다."` inside a character-facing `desc` prose field. Narrow BI-side template fix; does not need TR changes.
5. `BI: MasterBible.FinanceHUD.Protagonist.actual_truth.portfolio_history[*].total_assets` — diegetic leak: HUD prose snapshots carry `"… ARC-04 진입점 확보"`, `"… ARC-05 진입점"`, `"… ARC-06 진입점"` suffixes inside a prose field that downstream consumers may surface verbatim. Contrast with the adjacent `front_sector_by_arc[*].arc_id` values which are correctly placed in an `allowed_structural_meta` field.

## 7. Final Severity

- not `P0` — files exist, decode, and parse
- not `P1` — pair truth is stable per prior 10pair survey; wording leakage is structurally isolable from any truth repair
- final severity: **`P2`** — repeated disallowed meta leakage exists across label (systematic 70-row `section_rotation` prefix, systematic 5-row `opponent_transition_plan[*].phase` prefix) and diegetic (`~400` foreshadow/callback prose entries, plus `KeyNPCs[*].desc` and `portfolio_history[*].total_assets` prose leaks) surfaces; bounded cleanup should be scheduled soon

## 8. Final Execution Route

- **`cleanup_now`**

Justification:

- prior merged survey already rates pair 06 as `clean`, so this is a wording-only follow-up, not a truth-repair follow-up
- the TR and BI label prefixes are systematic and mechanical (`ARC-0N - `, `Phase N: `) and can be stripped in one bounded pass without touching structural meaning
- the diegetic prose leaks in foreshadow/callback/desc/total_assets are wide but are all clearly on the forbidden-field list in §3.2 of the handoff doc, so the cleanup scope is well-bounded
- no pair-truth blocker competes for the same edit slots

## 9. Minimal Next-Step Suggestion

One-line: strip `ARC-0N - ` from `blocks[*].genre_ext.section_rotation` (TR+BI mirror) and `Phase N: ` from `MasterBible.WorldState.opponent_transition_plan[*].phase`, then do one bounded natural-language rewrite pass over `blocks[*].foreshadow[*]` / `callback[*]` (and the BI-side `KeyNPCs[*].desc` and `portfolio_history[*].total_assets` prose) while migrating the structural block/arc numbers into `foreshadow_targets` / `callback_sources` / `arc_no`.

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-07 output
