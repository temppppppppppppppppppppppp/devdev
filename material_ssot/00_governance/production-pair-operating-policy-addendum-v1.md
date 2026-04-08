# Production Pair Operating Policy Addendum v1

Date: 2026-04-08
Status: active

## 1. Role

This addendum closes the operational policy gaps left intentionally broad in:

- `production-pair-schema-standard-v1.md`
- `production-pair-benchmark-spec-v1.md`
- `production_pair_grade_aliases/README.md`
- `docs/narrative-router/material-revival-ladder-harness.md`

Use this document when a live pair needs an operational ruling that is more specific than the base schema document.

## 2. Scope

This addendum governs:

- historical live pairs already active in root live inventory on `2026-04-08`
- new live pairs
- newly touched live pairs
- regenerated live pairs
- promotion-target pairs
- reference-only benchmark pairs

## 3. Operational State Definitions

### 3.1 Untouched Historical Live Pair

An `untouched historical live pair` is a root live `BI/TR` pair that:

- was already active in the root live inventory on `2026-04-08`
- has not had its live pair payload rewritten since this addendum was adopted

The following do not count as touching the pair:

- editing docs, reports, or audit notes
- editing alias snapshot files
- moving notes around `_quarantine`
- metadata or governance changes outside the live `BI/TR` JSON pair files

### 3.2 Material Touch

A `material touch` means any write to the live `BI` or `TR` pair payload itself, including:

- metadata normalization inside the pair file
- `TR.blocks[*]` edits
- `genre_ext` or `martial_ext` edits
- `BI` family-slot promotion or wrapper cleanup
- builder re-emission that rewrites the live pair JSON

Once a pair is materially touched, it no longer qualifies as an `untouched historical live pair`.

### 3.3 Regenerated Pair

A `regenerated pair` is a pair whose live `TR` or `BI` was re-emitted from `phase0`, preprocess authority bundles, or a repair/build script in a way that rewrites substantive payload rather than applying only tiny local edits.

### 3.4 Promotion-Target Pair

A `promotion-target pair` is any pair entering one of these lanes:

- `promotion patch`
- `revival-stage probe`
- `active promotion`
- `Stage 4 canary`
- active family baseline candidacy
- alias refresh or new grade-alias assignment

### 3.5 Reference Pair

A `reference pair` is a non-live pair kept for benchmark reading, example reading, or family comparison.

Reference pairs:

- do not count as active live baseline inventory
- may keep a historical benchmark alias or reference note
- may remain useful for comparison even when not promotion-eligible

### 3.6 Newly Touched Reference Pair

A `newly touched reference pair` is a reference-only pair whose live `BI/TR` payload was materially rewritten after its last benchmark or reference snapshot.

Operational reading:

- keep it non-live
- keep it out of active baseline lanes
- treat any existing benchmark alias as a historical snapshot until freshness is refreshed

## 4. Migration Debt Rule

### 4.1 What Counts As Migration Debt

Open `Tier B migration debt` currently means one narrow case only:

- the pair is otherwise operationally live
- the only missing promoted family-core serialization is canonical `block_cider.*`

If a pair also has other live canonical drift such as broken provenance packaging, wrapper drift, or canonical field-name drift, record those separately. That pair is not a `block_cider-only` debt case.

### 4.2 Grandfathered Window

`block_cider` migration debt is grandfathered only for `untouched historical live pairs` that were already active on `2026-04-08`.

Grandfathering ends immediately when any of the following happens:

- the pair is materially touched
- the pair is regenerated
- the pair becomes a promotion target
- the pair is submitted for alias refresh
- the pair is proposed as an active family baseline candidate

After that point, canonical `block_cider` is treated as fully required again.

## 5. Benchmark, Grade, And Alias Interlock

Benchmark grade and schema status are separate axes.

Required reporting split:

- `benchmark grade`
- `schema status`
- `evidence mode`
- `open migration debt: yes/no`

Operational rule:

- an untouched historical live pair may temporarily keep its existing alias snapshot while carrying open `block_cider` migration debt
- no pair may newly earn or refresh a positive live alias while open migration debt remains
- no pair with open migration debt may be used as an active family baseline candidate or promotion-target exemplar

Practical reading:

- `historical alias may persist`
- `new operational endorsement may not`

### 5.1 Benchmark Freshness

Schema status and benchmark freshness are separate.

Use these freshness readings:

- `current`
  - the benchmark was run after the latest material touch or regeneration, or
  - a bounded benchmark-preservation audit explicitly recorded that benchmark anchors and cap rules remained intact after the latest schema-only rewrite
- `pending_refresh`
  - the pair was materially touched or regenerated after the latest benchmark artifact, and no post-touch freshness audit exists yet
- `unbenchmarked`
  - no benchmark-grade artifact exists yet

Operational rule:

- `pending_refresh` does not erase a historical benchmark result
- `pending_refresh` does block active baseline claims, fresh alias refresh, and promotion-target exemplar use
- reference pairs may keep historical comparison value while still being `pending_refresh`

## 6. Benchmark Evidence Mode

### 6.1 Legacy Read Mode

`legacy_read` is allowed only when all of the following are true:

- the pair is an `untouched historical live pair`
- the pair is being benchmarked for observation or debt tracking, not for alias refresh or promotion-target use
- the only open family-core serialization gap is canonical `block_cider.*`

In `legacy_read` mode, the auditor may derive `has_cider: true/false` from:

- `TR` prose
- existing runtime fields
- explicit same-block receipts named in the report

The report must still name exact block numbers and the concrete same-block receipt logic.

### 6.2 Serialized Canonical Mode

`serialized_canonical` mode is required for:

- new live pairs
- newly touched pairs
- regenerated pairs
- promotion-target pairs

In this mode:

- `genre_ext.block_cider.*` is the primary benchmark evidence surface
- prose citations remain supporting evidence, not a substitute for missing canonical serialization

If canonical `block_cider` exists but conflicts with the actual block reading, the pair is non-compliant and must be repaired before alias refresh, promotion, or baseline use.

## 7. Provenance And Metadata Requiredness

### 7.1 Canonical Metadata Policy

Use this split:

- `_work_id`
  - warning-only if absent on an untouched historical live pair
  - required for new, newly touched, regenerated, or promotion-target pairs
- `_authority_chain`
  - canonical write name for all forward work
  - historical `_authority_sources` counts as `alias-pass` only for untouched historical live pairs
- `_phase0_ref`
  - warning-only on untouched historical live pairs
  - required when a touched or promotion-target `TR` depends on family-specific `phase0` authority
- `BI._source_phase0`
  - warning-only on untouched historical live pairs
  - required for regenerated or promotion-target `BI` outputs
- `BI._source_tr`
  - warning-only on untouched historical live pairs
  - required for regenerated or promotion-target `BI` outputs

### 7.2 Phase0 Authority Fallback Rule

If a live pair has no root `treatments/phase0/{work_id}_phase0_design.json` file, use this rule:

- untouched historical live pair:
  - provenance may pass as `alias-pass` if a stable preprocess authority bundle exists and the audit or metadata names that authority source exactly
- new, newly touched, regenerated, or promotion-target pair:
  - restore or emit the canonical root `phase0` file before alias refresh, promotion, or active baseline use

## 8. Alias Matrix

Use this matrix consistently across audits, builders, and repair tools:

- `_authority_sources` -> canonical `_authority_chain`
- `martial_ext` -> canonical forward `genre_ext`
- `faction_status` -> canonical forward `faction_position`
- root `capital_curve` -> canonical `MasterBible.AssetLibrary.CapitalCurve`

Notes:

- `martial_ext` and `faction_status` are read-compat migration aliases, not preferred write names
- root `capital_curve` is historical leakage, not a stable forward alias to preserve indefinitely

## 9. Output Contract

Every live-pair audit, repair note, or promotion note should state:

1. pair identity
2. operational state
3. schema status
4. benchmark freshness
5. evidence mode
6. open migration debt: `yes/no`
7. benchmark grade if a benchmark was run

This keeps benchmark quality, schema cleanliness, and promotion readiness from being collapsed into one vague label.
