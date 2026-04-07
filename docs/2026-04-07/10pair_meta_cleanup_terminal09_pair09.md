# 10-Pair Meta Cleanup Terminal 09 Pair 09 Survey

Date: 2026-04-07
Status: final
Document Type: read-only bounded meta-wording survey (single terminal)
Canonical Path: `docs/2026-04-07/10pair_meta_cleanup_terminal09_pair09.md`
Baseline Commit: `5c71b81a36ab2cbae824c630bb63219354b913a8`
Parent Order: `docs/2026-04-07/10pair_tr_bi_legacy_meta_cleanup_10terminal_opus_order.md`

## 1. Terminal Scope

- single pair
- read-only
- bounded meta-wording survey only
- classify `allowed_structural_meta` vs `diegetic_meta_ref` vs `label_meta_ref`
- no repair
- no pair mutation
- no `docs/temp/` mutation
- no patch order drafting

## 2. Assigned Pair

- Pair: `09`
- Family: `wuxguide` (wuxia / heavenly physician)
- TR: `treatments/09_wuxia_heavenly_physician_tr_block_070_draft.json`
- BI: `bible/09_bi_wuxia_heavenly_physician.json`
- Prior consistency verdict (`docs/2026-04-06/10pair_tr_bi_consistency_bounded_survey.md`): `clean` / `P3` / `seeds granularity only`
- No prior `blocked_by_pair_truth` condition — pair is not on the `07` / `10` mixed list

## 3. Artifact Truth

| Check | TR | BI |
| --- | --- | --- |
| file exists | yes | yes |
| UTF-8 decode | yes (`utf-8`) | yes (`utf-8-sig`, BOM present) |
| JSON parse | yes (`dict`, `_total_blocks=70`, `blocks` len=70) | yes (`dict`, `MasterBible.plot_roadmap` len=70) |
| block coverage | 1-70 contiguous | 1-70 contiguous |

Both artifacts parse cleanly. No `P0` file-level defect. TR is a `dict` wrapper around `blocks` (not a bare list), distinct from pair `10`'s shape. BI `_source_tr` correctly points to the live TR path.

## 4. Raw Count Snapshot

Single regex pass for the minimum meta lexicon (`Block N / BLOCK N / 블록 N / ARC-N / Arc N / 아크 N / Phase N / 페이즈 N / Stage N / 스테이지 N / Bnn`) with no field classification:

| Artifact | TR raw meta-token hits | BI raw meta-token hits |
| --- | ---: | ---: |
| pair `09` | `93` | `348` |

These are triage numbers, not failure counts. TR total is small because `block_id = "Block N"` only fires once per block (70) plus ~23 `Bnn` shorthand hits in `martial_ext`. BI total is inflated by `WorldState.internal_energy_curve[*].block` (pure block-ID structural fields), `evolution` strings (allowed metadata), `KeyNPCs[*].turning_points` (short prose list), `GenreRules.realm_progression[*]` (arc + defeat_block fields), and the plot_roadmap mirror of TR `martial_ext`.

Field-classified counts below tell the real story.

## 5. Findings (classified)

### 5.1 `allowed_structural_meta` (not a violation)

Confirmed structural metadata carriers — these are allowed per §6.1 of the parent order and per `SSOT_bi-evolution-metadata-standard.md`:

- `TR: blocks[*].block_id` — `"Block 1"`..`"Block 70"`, plus integer `block_no`. Allowed.
- `BI: arcs[*].arc_id` — `"ARC-01"`..`"ARC-07"` across 7 arcs. Allowed.
- `BI: opponent_transition_plan[*].arc_range` — `"ARC-01~02"` etc. Pure structural range, not prose. Treated as allowed.
- `BI: MartialHUD.Protagonist.actual_truth.martial_status.martial_arts[*].evolution` — 6 entries with arrow-trace strings such as `"B22~23 1~3침 → B61 6침 완성 → B63 7침 실패 → B65 정(情)의 침 깨달음 → B69 7침 완성"`. Explicitly allowed by `SSOT_bi-evolution-metadata-standard.md` §5: "Block references are allowed inside `evolution` because this field is metadata." The wuxguide family note §7.1 also canonizes `martial_arts[*].evolution`. All 6 are compact arrow-traces, not paragraphs — they comply with the standard's content rules.
- `BI: WorldState.internal_energy_curve[*].block` — 18 entries of pure `"B01"`-form block IDs stored as a dedicated `block` sub-field. Structural. Allowed.
- `BI: GenreRules.realm_progression[*].arc` — `"ARC-01"` pure arc-ID sub-field (7 entries). Structural. Allowed.
- `BI: FactionMap.protagonist_faction.position_progression[*].arc` — `"ARC-01~02"` pure sub-field (5 entries). Structural. Allowed.
- `BI: AssetLibrary.KeyNPCs[*].enter` — 10 entries of pure `"B01"`-form block IDs as a dedicated anchor sub-field. Structural. Allowed.

### 5.2 `diegetic_meta_ref` (disallowed — prose leakage)

Disallowed meta wording has leaked into fields that are clearly meant to be read as prose / short labels. Applying the inference rule of `meta-language-leak-context-handoff.md` ("if a field is clearly meant to be read as prose, a label, a short description... treat it as human-readable even if the policy note does not name that exact key"), the following wuxia `martial_ext` + BI asset fields are `diegetic_meta_ref`:

TR side (22 hits, all inside `blocks[*].martial_ext`):

- `blocks[*].martial_ext.injury_status.current` — 6 hits such as `"정상. B01 탈진에서 완전 회복."`, `"B07 경미한 타박상 회복 완료. 정상."`, `"왼팔 마비독 완전 회복. 경맥 피로 지속 (B16 이후 누적). 물리적 부상 없음."`
- `blocks[*].martial_ext.injury_status.change` — 3 hits such as `"변동 없음. 의식적 발현 시 체력 소모 있으나 B01 수준의 탈진은 아님"`, `"기력 저하(B13) → 회복 + 경미한 찰과상"`, `"과로(B16) 지속 → 피로 누적 심화"`
- `blocks[*].martial_ext.injury.detail` — 1 hit `"... B28 흉터 부위. 토혈. 전투 불능"`
- `blocks[*].martial_ext.leverage_used[i]` — 12 short-label list items such as `"독역 관찰 데이터 (B04~B11 축적)"`, `"B15 홍연 체질 분석"`, `"B34 해독제 분석 경험"`, `"살침(B41 이론)"`, `"B44 제조시설 증거"`

BI side — mirror + extra fields (~54 hits, no label field):

- `BI: MasterBible.plot_roadmap[*].martial_ext.*` — 22 identical hits mirroring TR exactly (22-to-22 byte-for-byte parity on `injury_status.current/change`, `injury.detail`, `leverage_used[]`)
- `BI: MasterBible.MartialHUD.Protagonist.actual_truth.equipment.artifacts[*].origin` — 2 hits `"B22 태산 석굴 발견"`, `"B60 홍연 혈액 기반 완성"`. `origin` is explicitly named as a forbidden spill target in `SSOT_bi-evolution-metadata-standard.md` §5: "Do not spill the same block-trace into `origin`, `description`, `summary`, or other narrative prose fields."
- `BI: MasterBible.Treasures[*].{discovery, activation, full_power, impact}` — 12 event-label hits such as `"B01 (선천 보유, 의무일체 발현)"`, `"B22 (태산 석굴)"`, `"B23~ (1~3침 수련 시작)"`, `"중반부 핵심 치료 자원. B20 약고 습격 후 대체 경로 필요"`
- `BI: MasterBible.AssetLibrary.KeyNPCs[*].turning_points[i]` — high-volume short prose list with B-ref headers (e.g. `"B01 소백 무시"`, `"B10 장로회 축출 시도 지지"`, `"B25 소백 의술 기록 수집 발각"`, `"B45 독문 전쟁 중 전사"`). Contributes most of BI's raw-count inflation.
- `BI: MasterBible.AssetLibrary.KeyNPCs[*].exit` — multiple hits like `"B45(전사), B60(유서 발견)"` — mixes a pure block-ID with parenthetical event prose.
- `BI: MasterBible.GenreRules.realm_progression[*].defeat_block` — 5 hits such as `"B13: 아버지 치료 실패, 정확도50%로 하락"`, `"B28: 과로 경맥 손상, 내공 15갑자로 하락"`, `"B38: 스승 엽천수 사망, 정확도 0%로 급락"` — colon-prefixed prose on a structural-sounding key name.
- `BI: MasterBible.FactionMap.protagonist_faction.position_progression[*].key_event` — 5 hits such as `"B10 축출 위기"`, `"B24 의선 대회 우승"`, `"B50 아버지 화해"`, `"B56 가문 추대"`, `"B70 천의 완성"`.
- `BI: MasterBible.ProjectData.CommercialCode.killing_points[2..4]` — 3 marketing-prose hits such as `"아버지와의 화해 (B50) — 시리즈 최대 감동"`, `"스승 유언이 열어주는 살침 각성 (B38→B43)"`, `"최종전: 적을 치료하며 이기다 (B69)"`.

### 5.3 `label_meta_ref` (disallowed — label-field leakage)

None found in the sense of §6.2 label keys (`section_rotation`, `arc_section`, `phase`, `phase_label`). Those keys do not exist anywhere in pair `09` TR or BI. This is a clean structural result: the leakage is purely in `martial_ext` / asset-prose surfaces, not in label-field keys.

### 5.4 `blocked_by_pair_truth`

Not applicable. Prior `10pair_tr_bi_consistency_bounded_survey.md` rated pair `09` as `clean` / `P3` and explicitly excluded it from the `07` (`mixed — BI metadata drift`) and `10` (`mixed — TR incomplete`) repair queue. There is no upstream pair-truth failure fused with the wording issue, and TR has all 70 blocks present.

### 5.5 Pattern Summary

- The wuxia family encodes continuity density through compact `Bnn` cross-references inside short-label and injury-tracking fields. This is exactly the erosion pattern `meta-language-leak-context-handoff.md` §1 warns about: compact meta shorthand that rides downstream into diegetic prose.
- TR and BI plot_roadmap are byte-parity on `martial_ext`, so any cleanup must touch both in one pass or be re-generated via a shared transform to avoid re-drift.
- BI carries an additional leakage surface that TR does not — `KeyNPCs.turning_points`, `Treasures.{discovery,activation,full_power,impact}`, `GenreRules.defeat_block`, `FactionMap.key_event`, `CommercialCode.killing_points`, `equipment.artifacts.origin` — so the smallest repair unit is `TR + BI`, not `TR only`.
- `evolution` is the only surface where block-trace wording is canonical — the 6 `martial_arts[*].evolution` entries must be preserved as-is.

## 6. Concrete Anchors (5 max)

1. `TR: blocks[2].martial_ext.injury_status.current` — `"정상. B01 탈진에서 완전 회복."` — representative of 6 `injury_status.current` hits; compact `Bnn` shorthand embedded in injury-state prose; should move to a structural prior-injury ID sub-field and leave natural language only (`diegetic_meta_ref`).
2. `TR: blocks[29].martial_ext.leverage_used[2]` — `"B15 홍연 체질 분석"` — representative of 12 `leverage_used[]` short-label list hits; each entry is a B-ref header glued to a prose label. BI `plot_roadmap[*].martial_ext.leverage_used[]` mirrors this one-for-one (`diegetic_meta_ref`).
3. `BI: MartialHUD.Protagonist.actual_truth.martial_status.martial_arts[1].evolution` — `"B22~23 1~3침 → B61 6침 완성 → B63 7침 실패 → B65 정(情)의 침 깨달음 → B69 7침 완성"` — explicit `evolution` metadata carrier; compact arrow-trace with block refs; `allowed_structural_meta` per `SSOT_bi-evolution-metadata-standard.md` §5/§7.1 and must be preserved unchanged.
4. `BI: AssetLibrary.KeyNPCs[0].turning_points[4]` — `"B60 유서 '네가 진가의 진짜 자랑이다'"` — representative of the highest-volume BI leakage surface: short prose turning-point entries with `Bnn` headers. Structure should split into a separate anchor block field plus natural-language event text (`diegetic_meta_ref`).
5. `BI: GenreRules.realm_progression[1].defeat_block` — `"B13: 아버지 치료 실패, 정확도50%로 하락"` — representative of a "structural-sounding key, prose-filled value" pattern. The key name `defeat_block` implies a pure block-ID, but the value is colon-prefixed prose. Should become `defeat_block: 13` (int or `"Block 13"` form) plus `defeat_reason: "아버지 치료 실패, 정확도50%로 하락"` (`diegetic_meta_ref`).

## 7. Severity

`P2`

Reasoning:

- `P0` is excluded — files parse, 70 blocks are present, no decode failure.
- `P1` is excluded — no pair-truth instability; prior consistency survey already cleared pair `09` as `clean`; no other blocker sits under the wording issue.
- `P3` would understate reality — the leakage is not sparse or cosmetic; it is systematic across `martial_ext` (both sides), `KeyNPCs.turning_points` (high volume), `Treasures.{discovery,activation}`, `GenreRules.defeat_block`, `FactionMap.key_event`, and `CommercialCode.killing_points`. That is 5+ distinct wuxguide asset families affected, not one stray field.
- `P2` fits exactly: repeated disallowed meta leakage exists and a bounded cleanup should be scheduled.

## 8. Execution Route

`cleanup_now`

- no upstream truth blocker
- no TR completion gap (all 70 blocks present, `_total_blocks` matches)
- prior consistency survey already qualifies pair `09` for non-blocking cleanup
- the cleanup is mechanical: split block-ref shorthand into sibling structural fields and leave natural language in the human-readable field, with `evolution` preserved

Smallest cleanup unit: `TR + BI`

- TR must be cleaned because all 22 `martial_ext` leakages originate there.
- BI must be cleaned in the same wave because `plot_roadmap[*].martial_ext` is byte-parity with TR (reverting only TR would re-drift against BI) AND BI carries leakage in asset surfaces that do not exist in TR (`KeyNPCs.turning_points`, `Treasures`, `GenreRules.defeat_block`, `FactionMap.key_event`, `CommercialCode.killing_points`, `equipment.artifacts.origin`).
- `evolution` surface must be preserved untouched.

## 9. One-Line Minimal Next Step

Schedule a bounded `TR + BI` meta-wording cleanup patch for pair `09` that moves `Bnn` / `ARC-N` shorthand out of `martial_ext`, `KeyNPCs.turning_points`, `Treasures.{discovery,activation,full_power,impact}`, `GenreRules.defeat_block`, `FactionMap.key_event`, `CommercialCode.killing_points`, and `artifacts.origin` into sibling structural fields, while explicitly preserving `MartialHUD.Protagonist.actual_truth.martial_status.martial_arts[*].evolution` as-is.

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-07 output
