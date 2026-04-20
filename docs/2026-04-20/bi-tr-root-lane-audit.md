# BI/TR Root Lane Audit

Date: 2026-04-20
Status: frozen pre-move audit
Scope: root `treatments/` + `bible/` lane labeling before the donor-ready waiting-room move

## 1. Purpose

- root `treatments/` and `bible/` are mixed live inventories, not one clean pair shelf
- this audit records the mixed root state before the donor-ready waiting-room move
- this follows the current material-side rule: connect legacy and mixed root paths by manifest and labeling first

Historical note:

- after this audit, the donor-ready waiting-room wave moved non-keep root files into `_waiting_room/`
- use this document as the pre-move baseline, not as the current root shelf listing

## 2. Evidence Base

- root file listing of `treatments/` and `bible/` on 2026-04-20
- `material_ssot/00_governance/production-pair-operational-registry-v1.md`
- latest reachable work-specific authority notes:
  - `docs/2026-04-12/empire_youngest_allsector_promotion_note.md`
  - `docs/2026-04-09/smart_new_hire_live_status.md`
  - `docs/2026-04-09/hoegui_surgeon_live_status.md`
  - `docs/2026-04-08/jaebeol3se_loss_line_live_status.md`
  - `docs/2026-04-09/africa_farm_king_live_status.md`
  - `docs/2026-04-09/gulf_tycoon_heir_live_status.md`
  - `docs/2026-04-08/quiet_chaebol_heir_live_status.md`
  - `docs/2026-04-20/golden_canary_deepclone_probe_a_fullblock_v1_live_status.md`
- root `Phase0` / preprocess donor signal spot-checks for:
  - `chaebol_allowance_zero`
  - `pantech_cyworld_reborn`
  - `golden_canary_deepclone_probe_a`
  - `golden_canary_deepclone_probe_a_fullblock_v1`

## 3. Root Lane Map

| Lane | work_id | TR root status | BI root status | Current operator reading |
| --- | --- | --- | --- | --- |
| pair-tracked live pair | `투자물_골든_카나리아 테스트_canonical_v1` | live | live | registry-tracked numbered live pair |
| pair-tracked live pair | `chaebol_allowance_zero` | live | live | registry-tracked numbered live pair |
| pair-tracked live pair | `chaebol_ent_empire` | live | live | registry-tracked numbered live pair |
| pair-tracked live pair | `defense_defect_engineer` | live | live | registry-tracked numbered live pair |
| pair-tracked live pair | `office_checkup_next_day` | live | live | registry-tracked numbered live pair |
| pair-tracked live pair | `pantech_cyworld_reborn` | live | live | registry-tracked numbered live pair |
| pair-tracked live pair | `wuxia_heavenly_physician` | live | live | registry-tracked numbered live pair |
| pair-tracked live pair | `jangyeongshil_industrial_revolution` | live | live | registry-tracked unslotted live pair |
| pair-tracked live pair | `manual_meridian_archivist` | live | live | registry-tracked unslotted live pair |
| live pair, outside pair registry | `smart_new_hire` | live | live | pair complete, BI audit PASS, mirrored `001` + `070` TR roots by design |
| live pair, outside pair registry | `empire_youngest_allsector` | live | live | promotion note says live authority pair ready |
| active TR, pair incomplete | `africa_farm_king` | live | absent | TR `1~10`, no live BI |
| active TR, pair incomplete | `gulf_tycoon_heir` | live | absent | TR `1~5`, no live BI |
| active TR, pair incomplete | `jaebeol3se_loss_line` | live | absent | TR `1~30`, no live BI |
| active TR, pair incomplete | `quiet_chaebol_heir` | live | absent | TR `1~51`, no live BI |
| active TR, pair incomplete | `hoegui_surgeon` | live | live | BI exists but latest BI audit is FAIL, not pair-tracked yet |
| probe / reference lane | `golden_canary_deepclone_probe_a` | live | live | donor-aware probe pair, not current registry-tracked live shelf |
| pair-tracked live pair | `golden_canary_deepclone_probe_a_fullblock_v1` | live | live | registry-tracked unslotted donorized gold sample; deployable GREENPLUS under 2026-04-20 benchmark + manual closeout |

## 4. Treatments Root Findings

- the root `TR` folder is dirty mainly because `current live pair`, `active TR only`, `probe/reference`, `legacy chunk`, and `sidecar note` files all coexist in one flat surface
- filename boundary is not current status truth
- current examples:
  - `hoegui_surgeon_tr_block_020_draft.json` serializes a full `70`-block TR, not a live `20`-block boundary
  - `jaebeol3se_loss_line_tr_block_005_draft.json` is the current live TR authority for `Block 1~30`
  - `quiet_chaebol_heir_tr_block_001_draft.json` is the current live TR authority for `Block 1~51`
  - `smart_new_hire_tr_block_001_draft.json` and `smart_new_hire_tr_block_070_draft.json` are an intentional synced mirror pair, not a duplicate mistake
- files that should not be misread as current root live pair authority:
  - `quiet_chaebol_heir_arc05_npc_lock.md`
  - `quiet_chaebol_heir_tr_block_001_draft.json.pre_scrub_backup`
  - `jangyeongshil_industrial_revolution_tr_block_010_draft.json`
  - `jangyeongshil_industrial_revolution_tr_block_011_015_draft.json`
  - `jangyeongshil_industrial_revolution_tr_block_016_020_draft.json`
  - `jangyeongshil_industrial_revolution_tr_block_021_025_draft.json`
- for `jangyeongshil_industrial_revolution`, the current root live authority is `jangyeongshil_industrial_revolution_tr_block_025_draft.json`; the smaller chunk files are historical chunk artifacts that still share the root surface

## 5. Bible Root Findings

- the root `BI` folder is cleaner than `treatments/`, but it still mixes:
  - pair-tracked live BI
  - live BI outside the current pair registry
  - BI on an audit-fail rehab lane
  - probe/reference BI
- the two main non-registry but live BI rows currently visible at root are:
  - `0_bi_empire_youngest_allsector.json`
  - `0_bi_smart_new_hire.json`
- the one root BI that must not be called a complete pair yet is:
  - `0_bi_hoegui_surgeon.json`
  - reason: latest live status says BI build succeeded but the current BI audit remains FAIL

## 6. Donor Reflection Watchlist

- `chaebol_allowance_zero`
  - root `Phase0` exposes `contamination_guard` + `do_not_fake`
  - root `BI` also exposes `MasterBible.GenreRules.contamination_guard` + `do_not_fake`
  - current reading: donor-translated rule surfaces are reflected into the live pair
- `pantech_cyworld_reborn`
  - root `Phase0` exposes `contamination_guard` + `do_not_fake`
  - root `BI` also exposes `MasterBible.GenreRules.contamination_guard` + `do_not_fake`
  - current reading: donor-translated rule surfaces are reflected into the live pair
- `golden_canary_deepclone_probe_a`
  - preprocess authority surfaces carry explicit donor wording
  - current root `Phase0` does not expose `contamination_guard` or `do_not_fake`
  - current root `BI` has `GenreRules`, but the donor-translation guard surfaces are not yet visible there
  - current reading: donor-aware preprocess exists, but donor reflection is not yet visibly closed at root pair level
- `golden_canary_deepclone_probe_a_fullblock_v1`
  - preprocess `source_manifest.json` says bounded donor translation is complete and frozen
  - current root `Phase0` exposes `contamination_guard` + `do_not_fake`
  - current root `BI` also exposes `MasterBible.GenreRules.contamination_guard` + `do_not_fake`
  - current reading: donor reflection is visibly closed at root pair level and the pair is registry-tracked live authority

## 7. Metadata Drift Watchlist

- `empire_youngest_allsector_tr_block_070_draft.json`
  - current live TR file still serializes only `_schema`, `_total_blocks`, and `blocks`
  - `TR`-side `_work_id`, `_authority_chain`, and `_phase0_ref` are missing even though the promotion note already treats the pair as promoted live authority
  - `BI` already carries the expected source metadata
  - current reading: promotion is operationally declared, but `TR` metadata normalization is still open

## 8. Operator Rule

- do not sort the root folders by filename alone
- treat `production-pair-operational-registry-v1` as the first shelf for current pair-tracked live pairs
- when a root work is outside the registry, read the latest work-specific `live_status` or `promotion_note` before touching the pair
- do not call the base `golden_canary_deepclone_probe_a` probe variant a donor-reflected pair authority from current root surfaces alone
- read `golden_canary_deepclone_probe_a_fullblock_v1` through its work-specific live status plus registry row; it is now an unslotted deployable GREENPLUS row, not an automatic canonical-pair replacement by naming alone
- this document preserves the pre-move mixed root reading that was used before the donor-ready waiting-room wave
