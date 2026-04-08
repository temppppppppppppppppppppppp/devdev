# Production Pair Schema Standard v1

Date: 2026-04-08
Status: active
Scope: canonical schema contract for live `TR + BI` pairs under material-side governance

## 1. Role

- define one shared schema ruler before pair audit, repair, benchmark, promotion, or re-grade
- separate `pair is ingestible` from `pair is narratively strong`
- absorb recent `Stage 0` enrichment growth without forcing every new field into pair-core requiredness
- classify pair fields into:
  - `admission core`
  - `family-standard enrichment`
  - `work-local enrichment`

This document is schema-first. It does not replace the benchmark judgment in `production-pair-benchmark-spec-v1.md`.

## 2. Why This Exists

Current runtime admission is intentionally thin:

- router-family contracts require only a small `phase0_design` core
- canonical `TR` validation requires the `dict.blocks` wrapper plus Stage2-ready block payload
- canonical `BI` validation requires `MasterBible`, runtime protagonist keys, and `plot_roadmap`

That thin contract is good for fail-closed admission, but it is too weak to standardize newer `Stage 0` enrichments.

Result:

- some live pairs serialize richer `Stage 0` fields
- some equally valid live pairs do not
- pair repair can drift into per-work taste unless schema classification is fixed first

## 3. Core Model

### 3.1 Pair Unit

A production pair is one bounded unit:

- one canonical `TR`
- one canonical `BI`
- one source `phase0_design`

Pair-level decisions must preserve this authority split:

- `TR` owns blockwise progression truth
- `BI.MasterBible.plot_roadmap` is the canonical runtime projection of `TR`
- `BI` owns amplified runtime-facing surfaces
- `phase0_design` owns pre-TR design enrichment until a field is explicitly promoted into pair schema

### 3.2 Contract Tiers

Use these tiers everywhere.

- `Tier A: admission core`
  - required for a live canonical pair
  - missing fields are contract blockers
- `Tier B: family-standard enrichment`
  - not required for bare admission
  - once present for a work, should serialize into stable family slots instead of ad-hoc per-pair drift
- `Tier C: work-local enrichment`
  - allowed and useful
  - not implied mandatory for other works
  - must not be benchmarked as a missing family-core feature

### 3.3 Write Policy vs Read Compatibility

Canonical write shape and read-compat aliases are different things.

- new or newly touched pairs should write the canonical field names in this document
- existing live pairs may keep legacy aliases until the pair is touched
- `block_cider` is a special migration case:
  - new, newly touched, regenerated, or promotion-target live pairs must serialize canonical `block_cider`
  - historical untouched live pairs whose only missing family-core surface is canonical `block_cider` should be tracked as `Tier B migration debt` during the bounded migration window
- readers, auditors, and repair tools should stay alias-tolerant during the bounded migration window

### 3.4 Operating Addendum

Use `production-pair-operating-policy-addendum-v1.md` when you need an explicit operational ruling for:

- `untouched historical live pair` vs `newly touched` vs `regenerated` vs `promotion-target`
- when `Tier B migration debt` begins or ends
- when benchmark may use `legacy_read` evidence mode
- when a positive alias may be refreshed
- when preprocess authority may temporarily stand in for a missing canonical root `phase0` file

## 4. Canonical `TR` Standard

### 4.1 Wrapper and Pair Metadata

Required `Tier A` wrapper:

- top-level `dict`
- `_schema`
- `_total_blocks`
- `blocks`

Canonical top-level metadata names:

- `_work_id`
- `_authority_chain`
- `_family`
- `_phase0_ref`
- `_draft_status`

Alias policy:

- canonical write name: `_authority_chain`
- read-compat alias: `_authority_sources`

Notes:

- `_work_id` is warning-only for untouched historical live pairs, but required for forward work states defined in the operating addendum
- `_family` is required whenever the pair is not plain default `blockguide`
- `_phase0_ref` is warning-only for untouched historical live pairs, but required for forward work states defined in the operating addendum when the pair depends on family-specific `phase0` authority

### 4.2 Block Core Shape

Each canonical block should carry the following core surfaces.

Required `Tier A` block fields:

- `block_id`
- `block_no`
- `title`
- `content.context`
- `content.event_villain`
- `content.solution`
- `content.reward`

Required `Tier A` continuity/runtime surfaces:

- `stakes`
- `emotional_beat`
- `tension_level`
- `location`
- `time_span`
- `relationship_delta`
- `power_shift`

Recommended shared block fields:

- `pov_character`
- `foreshadow`
- `callback`
- `foreshadow_targets`
- `callback_sources`
- `regression_ext`

### 4.3 Consumer-Backed Payload Rule

Canonical `TR` is not a title-only scaffold.

- every block must contain real Stage2-consumable payload
- `title` or summary-only blocks are compatibility-valid only in a weak sense and should not be treated as ready canonical pair blocks
- numeric block refs belong in `foreshadow_targets` / `callback_sources`, not in natural-language prose fields

### 4.4 Canonical Family Extension Container

Canonical forward write name for block-level extension data:

- `genre_ext`

Read-compat aliases:

- `martial_ext` for existing wuxguide pairs

Rules:

- `blockguide` writes `genre_ext`
- `wuxguide` may still be read from `martial_ext`, but newly touched pair surfaces should converge toward `genre_ext`
- if a repair touches a legacy `martial_ext` pair, preserve truth first; full alias migration is optional unless the same change is already reshaping the block container

### 4.5 `blockguide` Family Core

Required `Tier A` `genre_ext` surfaces for production-ready `blockguide` pairs:

- `block_cider.has_cider`
- `block_cider.receipt_type`
- `block_cider.receipt_line`
- `block_cider.pain_only_exit`
- `capital_before`
- `capital_after`
- `capital_delta`

Transitional enforcement policy for historical live pairs:

- missing canonical `block_cider.*` alone is recorded as `Tier B migration debt`, not as an automatic de-live signal, if the pair is otherwise an untouched historical live pair
- once the pair is regenerated, materially touched, or promoted, `block_cider.*` returns to strict `Tier A` enforcement
- `capital_before`, `capital_after`, and `capital_delta` remain family-core runtime truth, not optional decoration

Required `Tier B` stable family surfaces:

- `method`
- `success_pattern`
- `deal_type`
- `opponent.name`

Recommended `Tier B` family surfaces:

- `knowledge_used`
- `risk_level`
- `business_sector`
- `leverage_used`
- `historical_event`

### 4.6 `wuxguide` Family Core

Required `Tier A` `genre_ext` surfaces for production-ready `wuxguide` pairs:

- `block_cider.has_cider`
- `block_cider.receipt_type`
- `block_cider.receipt_line`
- `block_cider.pain_only_exit`
- `realm_before`
- `realm_after`
- `internal_energy_before`
- `internal_energy_after`
- `faction_position`
- `jianghu_reputation`
- `enemy_pressure`

Transitional enforcement policy for historical live pairs:

- missing canonical `block_cider.*` alone is recorded as `Tier B migration debt`, not as an automatic de-live signal, if the pair is otherwise an untouched historical live pair
- once the pair is regenerated, materially touched, or promoted, `block_cider.*` returns to strict `Tier A` enforcement
- canonical forward write still converges toward `genre_ext`; read-compat `martial_ext` is tolerated only during the bounded migration window

Required `Tier B` stable family surfaces:

- `opponent.name`

Recommended `Tier B` family surfaces:

- `martial_art_gain`
- `artifact_or_manual_gain`
- `success_pattern`
- `opponent.weakness_exploited`

## 5. Canonical `BI` Standard

### 5.1 Wrapper and Top Metadata

Required `Tier A` wrapper:

- `_schema_version`
- `_schema_description`
- `_last_updated`
- `_genre`
- `MasterBible`

Canonical top-level metadata names:

- `_work_id`
- `_authority_chain`
- `_family`
- `_source_phase0`
- `_source_tr`

Alias policy:

- canonical write name: `_authority_chain`
- read-compat alias: `_authority_sources`

Notes:

- `_work_id` is warning-only for untouched historical live pairs, but required for forward work states defined in the operating addendum
- `_source_phase0` and `_source_tr` follow the provenance rule in the operating addendum

### 5.2 Shared `MasterBible` Core

Required `Tier A` shared surfaces:

- `ProjectData`
- `protagonist_config`
- `plot_roadmap`

Required `protagonist_config` runtime keys:

- `world_origin`
- `incarnation_type`
- `pov`
- `external_pov_insert_policy`

Canonical sidecar cleanup:

- canonical write path for roadmap: `MasterBible.plot_roadmap`
- legacy-only alias: root-level `plot_roadmap`
- canonical write path for runtime protagonist config: `MasterBible.protagonist_config`
- legacy-only alias: `ProjectData.protagonist_config`

### 5.3 `plot_roadmap` Sync Rule

`BI.MasterBible.plot_roadmap` is not a free summary layer.

- it must remain a normalized projection of canonical `TR.blocks`
- pair benchmark and repair should treat `TR` as the truth owner for block sequence
- `BI` may amplify meaning elsewhere, but must not drift from `TR` in roadmap truth

### 5.4 Family Core Sections

Required `Tier A` family master sections:

- `blockguide`
  - `FinanceHUD`
  - `WorldState`
  - `AssetLibrary`
  - `Seeds`
- `wuxguide`
  - `MartialHUD`
  - `WorldState`
  - `AssetLibrary`
  - `FactionMap`
  - `Treasures`
  - `Seeds`

## 6. Promotion Rule For New `Stage 0` Features

Do not auto-promote every new `Stage 0` field into pair-core requiredness.

Promote a `Stage 0` feature into `Tier B family-standard enrichment` only if all of the following are true:

1. the feature materially helps repair, audit, runtime guidance, or benchmark judgment
2. the feature can be serialized into one stable pair slot without work-specific prose drift
3. the feature is already used by multiple live works or is clearly family-level rather than one-work flavor
4. at least one builder, auditor, or runtime consumer can name the destination slot without guesswork

If those conditions are not met yet, keep the feature `Tier C work-local enrichment`.

## 7. Current v1 Promotion Decisions

These decisions standardize the current drift without forcing full pair rewrites in the same turn.

### 7.1 Promote Now: `blockguide`

Promote to `Tier B family-standard enrichment` when present:

- `regulatory_context`
  - canonical BI slot: `MasterBible.WorldState.regulatory_context`
- `expansion_order_locked`
  - canonical BI slot: `MasterBible.WorldState.expansion_order_locked`
- `hud_interpretation`
  - canonical BI slot: `MasterBible.WorldState.hud_interpretation`
- `capital_curve`
  - canonical BI slot: `MasterBible.AssetLibrary.CapitalCurve`
  - legacy-only alias: root-level `capital_curve`
- `do_not_fake`
  - canonical BI slot: `MasterBible.GenreRules.do_not_fake`
- `contamination_guard`
  - canonical BI slot: `MasterBible.GenreRules.contamination_guard`

Keep as provenance-only metadata, not pair semantic core:

- `canonical_pitch_authority`

### 7.2 Promote Now: `wuxguide`

Promote to `Tier B family-standard enrichment` when present:

- `internal_energy_curve`
  - canonical BI slot: `MasterBible.WorldState.internal_energy_curve`
- `taboo_rules`
  - canonical BI slot: `MasterBible.GenreRules.taboo_rules`
- `do_not_fake`
  - canonical BI slot: `MasterBible.GenreRules.do_not_fake`

Already treated as family core, not optional decoration:

- `FactionMap`
- `Treasures`

Keep in `Tier C work-local enrichment` until a stable multi-work slot exists:

- full `realm_path` traces
- full `martial_art_path` traces
- `growth_axes`
- `defeat_curve`
- `enrichment_deferred_to_tr`

## 8. Workflow Order

Use this order for any live pair:

1. normalize the pair against this schema standard
2. patch only the smallest contract blockers
3. run pair consumability
4. run benchmark judgment
5. only then expand into narrative repair, BI amplification, or promotion work

Benchmark rule:

- pair benchmark must not score a pair down for missing `Tier C work-local enrichment`
- pair benchmark must obey the operating addendum for `migration debt`, `evidence mode`, and alias-refresh eligibility
- pair repair must not invent new family requiredness outside this document without updating this document first

## 9. Non-Goals

- this standard does not require retrofitting every historical pair immediately
- this standard does not make every `Stage 0` enrichment mandatory
- this standard does not decide pair narrative grade
- this standard does not replace family harness docs
