# BI/TR Canonical v1 Mapping Table Draft

Date: 2026-04-03
Status: working map for `IDE-2`
Owner Lane: `IDE-2`
Branch Context: `ops/stage0-bi-tr`
Purpose: map representative legacy/current BI/TR shapes into canonical `v1`

## 1. Scope

Reference candidates:

- Golden Canary
  - `bible/01_bi_투자물_골든_카나리아 테스트.json`
  - `treatments/01_tr_투자물_골든_카나리아 테스트.json`
- Current modern builder family
  - `bible/0_bi_gatekeeper_heir.json`
  - `treatments/gatekeeper_heir_tr_block_070_draft.json`
- Current wuxia builder family
  - `bible/0_bi_wuxia_heavenly_physician.json`
  - `treatments/wuxia_heavenly_physician_tr_block_070_draft.json`

Mapping verbs used below:

- `pass-through`: already matches canonical shape closely
- `wrap`: add canonical outer container
- `lift`: move a field to the canonical location
- `derive`: compute from an existing explicit source field
- `inject`: require an explicit canonical field because safe inference is not guaranteed
- `project`: rebuild BI roadmap from canonical TR blocks
- `preserve`: keep as family extension data

## 2. BI File Root Mapping

| Canonical target | Golden Canary | Modern builder family | Wuxia builder family | Normalization rule |
| --- | --- | --- | --- | --- |
| `root._schema_version` | pass-through | pass-through | pass-through | keep existing until repo-wide version bump; final canonical writer may bump to `3.0` |
| `root._schema_description` | pass-through | pass-through | pass-through | preserve |
| `root._last_updated` | pass-through | pass-through | pass-through | preserve/update on write |
| `root._genre` | pass-through | pass-through | pass-through | preserve |
| `root.MasterBible` | pass-through | pass-through | pass-through | canonical owner stays here |
| root-level sidecar `plot_roadmap` | absent | present at BI root | absent | modern family must move this into `MasterBible.plot_roadmap` and stop emitting root-level sidecar roadmap |

## 3. BI Effective Root Mapping

| Canonical target | Golden Canary | Modern builder family | Wuxia builder family | Normalization rule |
| --- | --- | --- | --- | --- |
| `MasterBible.ProjectData` | pass-through | pass-through | pass-through | preserve |
| `MasterBible.protagonist_config` | already at canonical location | currently nested at `MasterBible.ProjectData.protagonist_config` | already at canonical location but runtime subset missing | modern family lifts field out of `ProjectData`; wuxia family enriches current object instead of relocating it |
| `MasterBible.plot_roadmap` | already present | currently emitted at BI root | already present | canonical writer should prefer TR-driven projection and only preserve existing BI roadmap when already canonical-ready |
| `MasterBible.WorldState` | pass-through | pass-through | pass-through | preserve |
| family HUD surface | `FinanceHUD` and `MartialHUD` | `FinanceHUD` | `MartialHUD` | preserve at least one family HUD surface |
| `MasterBible.Seeds` | pass-through | pass-through | pass-through | preserve |

## 4. Runtime Identity Mapping

Canonical required runtime identity keys:

- `world_origin`
- `incarnation_type`
- `pov`
- `external_pov_insert_policy`

| Canonical field | Golden Canary source | Modern builder family source | Wuxia builder family source | Canonical action |
| --- | --- | --- | --- | --- |
| `world_origin` | `MasterBible.protagonist_config.world_origin` | missing at canonical location; derive from explicit family/runtime authoring input, not from BI absence | missing | if absent, normalizer should require explicit authoring/default lane config rather than silently omit |
| `incarnation_type` | `MasterBible.protagonist_config.incarnation_type` | derive from `MasterBible.ProjectData.protagonist_config.regression.regression_type` when explicit | missing | canonical writer should map known regression metadata to runtime identity value; otherwise require explicit input |
| `pov` | `MasterBible.protagonist_config.pov` | missing | missing | inject explicit canonical field; do not leave absent |
| `external_pov_insert_policy` | `MasterBible.protagonist_config.external_pov_insert_policy` | missing | missing | inject explicit canonical field; do not leave absent |

Additional runtime-adjacent fields:

| Canonical field | Golden Canary source | Modern builder family source | Wuxia builder family source | Canonical action |
| --- | --- | --- | --- | --- |
| `regression_point` | `MasterBible.protagonist_config.regression_point` | derive from `MasterBible.ProjectData.protagonist_config.regression` | missing | preserve if explicit; optional for canonical pass |
| `start_point` | absent | derive from modern builder `start_point` style fields if present | absent | optional family/runtime extra |
| `execution_doctrine` | direct field in `protagonist_config` | available in `WorldState.execution_doctrine` and setting-derived surfaces | available in setting-derived surfaces, not `protagonist_config` | preserve as optional if author wants runtime identity doctrine close to protagonist config |
| family profile extras | not needed beyond Golden runtime subset | `special_ability` and related profile fields under current `ProjectData.protagonist_config` | current wuxia `name`, `age_at_start`, goals, strengths | preserve as family-specific extras after runtime keys are satisfied |

## 5. BI plot_roadmap Mapping

| Canonical target | Golden Canary | Modern builder family | Wuxia builder family | Canonical action |
| --- | --- | --- | --- | --- |
| roadmap location | `MasterBible.plot_roadmap` | `root.plot_roadmap` | `MasterBible.plot_roadmap` | canonical location is always `MasterBible.plot_roadmap` |
| entry count | `60` | `70` | `70` | preserve work count |
| `block_no` | missing in embedded BI roadmap | present in current TR, but root BI sidecar location is wrong | BI uses `block` not reliable `block_no` | canonical BI roadmap should project from canonical TR block numbers |
| Stage2 payload | strong, but `block_no` missing | strong in TR, BI effective root missing roadmap | weak in embedded BI roadmap because many entries are `title/summary` shells | prefer TR-driven projection for modern and wuxia; Golden only needs `block_no` normalization |
| family extensions | `genre_ext`, `regression_ext` | `genre_ext`, `regression_ext` | `martial_ext` | preserve namespaced extension payload |

Normalization rule:

- `MasterBible.plot_roadmap` should be written from canonical TR blocks, not trusted as an independent competing truth

## 6. TR Wrapper Mapping

| Canonical target | Golden Canary | Modern builder family | Wuxia builder family | Canonical action |
| --- | --- | --- | --- | --- |
| root wrapper | raw list | raw list | dict with `blocks` | canonical writer wraps all TR outputs into dict + `blocks` |
| `_schema` | absent | absent | present | canonical writer emits one stable `tr.v1`-style schema marker |
| `_work_id` | absent | absent | present | add for Golden and modern families |
| `_family` | absent | absent | present | add for Golden and modern families |
| `_created` | absent | absent | present | add on canonical write |
| `_phase0_ref` | absent | absent | present | add where available |
| `_total_blocks` | absent | absent | present | derive from block count for all families |

## 7. TR Block Mapping

| Canonical field | Golden Canary source | Modern builder family source | Wuxia builder family source | Canonical action |
| --- | --- | --- | --- | --- |
| `block_no` | derive from `block_id` or list index | already present on TR block | derive from `block_id`, legacy `block`, or list index | always emit explicit `block_no` |
| `title` | pass-through | pass-through | pass-through | preserve |
| `content` | pass-through | pass-through | pass-through | preserve |
| `tactical_doc` | absent in sample | absent in sample | absent in sample | optional payload lane |
| `key_events` | absent in sample | absent in sample | absent in sample | optional payload lane |
| `stakes` | pass-through | pass-through | pass-through | preserve |
| `power_shift` | pass-through | pass-through | pass-through | preserve |
| `relationship_delta` | pass-through | pass-through | pass-through | preserve |
| `foreshadow` | pass-through | pass-through | pass-through | preserve |
| `callback` | pass-through | pass-through | pass-through | preserve |
| `emotional_beat` | pass-through | pass-through | pass-through | preserve |
| `tension_level` | pass-through | pass-through | pass-through | preserve |
| `pov_character` | pass-through | pass-through | sometimes absent | preserve when present, do not require canonically |
| `location` | pass-through | pass-through | pass-through | preserve |
| `time_span` | pass-through | pass-through | pass-through | preserve |
| family extension payload | `genre_ext`, `regression_ext` | `genre_ext`, `regression_ext` | `martial_ext` | preserve as namespaced extension object |

## 8. No-Guess Fields

These should not be guessed silently during normalization:

- `pov`
- `external_pov_insert_policy`
- `world_origin` when family/runtime metadata does not explicitly declare it
- `incarnation_type` when regression/incarnation metadata is ambiguous

Rule:

- if these are missing, emit a compatibility warning and require explicit builder/default policy injection

## 9. Immediate Implementation Follow-Up

Use this mapping order:

1. build read-side normalizers:
   - `legacy BI -> canonical BI view`
   - `legacy TR -> canonical TR view`
2. update the BI template to canonical root shape
3. update modern BI builder to:
   - lift `ProjectData.protagonist_config`
   - stop emitting root-level roadmap sidecar
   - inject runtime identity keys explicitly
4. update wuxia BI builder to:
   - keep family profile extras
   - inject runtime identity keys explicitly
   - write BI roadmap from canonical TR block projection
5. update both TR builders to emit dict wrapper plus `blocks`
6. split validators into:
   - canonical pass
   - legacy compatibility pass
