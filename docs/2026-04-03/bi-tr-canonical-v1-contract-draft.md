# BI/TR Canonical v1 Contract Draft

Date: 2026-04-03
Status: working canon for `IDE-2` (`draft`, not repo-wide SSOT yet)
Owner Lane: `IDE-2`
Branch Context: `ops/stage0-bi-tr`
Purpose: freeze the next BI/TR contract before changing builders, validators, or Stage0 handoff logic

## 0. Authority Scope

This document is currently:

- the working canon for `IDE-2` BI/TR normalization work on `ops/stage0-bi-tr`
- the contract we should use for mapping, normalization, validator split, and builder updates in this lane

This document is not yet:

- the repository-wide execution SSOT
- an active queue decision
- a merged cross-IDE contract until `IDE-1` review and merge happen

## 1. Answer First

`Golden Canary` is the stronger runtime reference specimen, but it should not be promoted as-is.

The next target should be `hybrid canonical v1`:

- keep the effective BI root discipline that runtime actually needs
- keep the builder reproducibility goals from current BI/TR harnesses
- stop treating silent rewrite paths as normal behavior

## 2. Canonical Ownership

Canonical `v1` separates owner roles this way:

1. `phase0_design`
   - upstream planning material
   - not a direct runtime consume contract

2. `TR`
   - canonical owner of block sequence and block-level narrative payload
   - source for Stage0 -> Stage2 roadmap projection

3. `BI`
   - canonical owner of runtime identity, world/state summary, HUD surfaces, and embedded roadmap projection

4. `DB bible anchor`
   - operational cache / resume artifact
   - not the authoring source of truth

Implication:

- healthy canonical BI/TR inputs should validate and forward
- `ensure_plot_roadmap()` and `force_sync_v25_dna()` should exist only as compatibility bridges for legacy inputs

## 3. BI Canonical v1

### 3.1 File Root

Canonical BI files should use one wrapped root:

```json
{
  "_schema_version": "3.0",
  "_schema_description": "work BI",
  "_last_updated": "YYYY-MM-DD",
  "_genre": "family code",
  "MasterBible": {}
}
```

Rules:

- `MasterBible` wrapper is required for canonical pass
- root-level sidecar fields that duplicate runtime fields are legacy only
- root-level `plot_roadmap` outside `MasterBible` is legacy only
- root-level `protagonist_config` outside `MasterBible` is legacy only

### 3.2 Effective BI Root

The effective BI root is always:

- `bible["MasterBible"]`

Canonical effective BI root must include:

- `ProjectData`
- `protagonist_config`
- `plot_roadmap`

Strongly expected for canonical pass:

- `WorldState`
- `Seeds`
- at least one family HUD surface such as `FinanceHUD` or `MartialHUD`

### 3.3 ProjectData Minimum

Canonical minimum:

- `ProjectData.MetaInfo.title`
- `ProjectData.CoreIdentity.protagonist`

Recommended stable fields:

- `ProjectData.MetaInfo.logline`
- `ProjectData.CoreIdentity.protagonist_faction`
- `ProjectData.CommercialCode`

### 3.4 protagonist_config Contract

`protagonist_config` is a runtime identity contract first.

Required fields for canonical pass:

- `world_origin`
- `incarnation_type`
- `pov`
- `external_pov_insert_policy`

Allowed optional fields:

- `regression_point`
- `start_point`
- `execution_doctrine`
- `governance_doctrine`
- `secrecy_rule`
- family-specific extras

Rule:

- family-specific richness may extend `protagonist_config`
- family-specific fields may not replace the four runtime identity keys above

### 3.5 plot_roadmap Contract

`plot_roadmap` must live inside the effective BI root and must already be Stage2-ready.

Each canonical entry must include:

- `block_no`
- `title`
- at least one Stage2-consumable payload source from:
  - `content`
  - `tactical_doc`
  - `key_events`

Recommended stable fields:

- `block_id`
- `summary`
- `stakes`
- `power_shift`
- `relationship_delta`
- `foreshadow`
- `callback`
- `emotional_beat`
- `tension_level`
- `location`
- `time_span`
- namespaced family extension fields such as `genre_ext`, `regression_ext`, `martial_ext`

Rule:

- `title/summary only` roadmap entries do not qualify for canonical pass

## 4. TR Canonical v1

### 4.1 File Root

Canonical TR files should converge to one dict wrapper:

```json
{
  "_schema": "tr.v1",
  "_work_id": "work-key",
  "_family": "family code",
  "_created": "YYYY-MM-DD",
  "_phase0_ref": "phase0 file or id",
  "_total_blocks": 70,
  "blocks": []
}
```

Rules:

- canonical TR output uses dict wrapper plus `blocks`
- raw list TR remains accepted only as legacy compatibility input
- `dict.treatments` remains accepted only as legacy compatibility input

### 4.2 Block Contract

Each canonical block must include:

- `block_no`
- `title`
- one Stage2-consumable payload source from:
  - `content`
  - `tactical_doc`
  - `key_events`

Recommended stable fields:

- `block_id`
- `summary`
- `stakes`
- `power_shift`
- `relationship_delta`
- `foreshadow`
- `callback`
- `emotional_beat`
- `tension_level`
- `pov_character`
- `location`
- `time_span`

Allowed family extensions:

- `genre_ext`
- `regression_ext`
- `martial_ext`
- future family namespaced `*_ext`

Rule:

- family extensions may enrich a block
- family extensions may not be the only meaningful payload in place of block narrative content

## 5. BI/TR Pair Invariants

Canonical `v1` should enforce these pair rules:

1. `BI.MasterBible.plot_roadmap` and `TR.blocks` describe the same ordered block sequence
2. `plot_roadmap` entry count equals `TR.blocks` count
3. `block_no` ordering is monotonic and aligned across BI/TR
4. BI may project TR block payload, but it may not silently replace healthy canonical TR truth
5. DB anchor writes may cache normalized BI/TR truth, but should not become a stronger owner than the source files

Recommended normalization target:

- BI `plot_roadmap` is a Stage2-ready projection of canonical TR blocks
- projection may preserve the full TR block payload when already compatible

## 6. Canonical Pass vs Legacy Compatibility Pass

Validator behavior should split into two explicit lanes.

### Canonical Pass

Canonical pass requires:

- BI has `MasterBible`
- effective BI root has `protagonist_config`
- effective BI root has `plot_roadmap`
- `protagonist_config` includes the four runtime identity keys
- roadmap entries have `block_no`
- roadmap entries have Stage2-consumable payload
- TR uses dict wrapper plus `blocks`

### Legacy Compatibility Pass

Legacy compatibility pass may still accept:

- BI without `MasterBible`
- BI with root-level sidecar `plot_roadmap`
- TR as raw list
- TR as `dict.blocks`
- TR as `dict.treatments`

But compatibility pass must:

- emit warnings
- identify which canonical requirements were missing
- feed normalizers instead of pretending the input was already canonical

## 7. Compatibility Bridge Rules

The following code paths should be treated as compatibility bridges, not canonical authoring behavior:

- `modules/core/stage0_handoff.py::ensure_plot_roadmap`
- `modules/core/project_manager.py::force_sync_v25_dna`
- validator fallbacks that silently accept non-canonical wrappers

Target behavior:

- canonical healthy input -> validate and forward
- legacy input -> normalize, warn, and only then forward

## 8. Known Gaps Against This Contract

Current known gaps in this branch baseline:

1. current modern BI builder omits `pov` and `external_pov_insert_policy`
2. current wuxia BI builder does not expose canonical runtime `protagonist_config`
3. current builders still accept raw list TR as normal output/input
4. current BI template is too thin and still places `plot_roadmap` at root level
5. current validator is broad compatibility logic, not a canonical gate

## 9. Immediate Implementation Order

Do these next:

1. write the BI/TR field mapping table into canonical `v1`
2. define `legacy -> canonical` normalization rules
3. update the BI template to canonical root shape
4. add a read-side normalizer that outputs canonical BI/TR views
5. tighten validators to distinguish canonical pass from compatibility pass
6. update builders to emit canonical `v1`
7. add fixture tests for:
   - one Golden Canary pair
   - one modern builder pair
   - one wuxia builder pair

## 10. Non-Goals

This draft does not yet:

- rewrite Stage0 handoff logic
- promote the parked BI/TR SSOT into active queue
- collapse BI and TR into one file
- remove legacy compatibility inputs immediately
