# BI Evolution Metadata Standard

Date: 2026-03-28
Status: active
Scope: narrative-pipeline BI only

## 1. Purpose

- Standardize the compact growth-trace metadata used in ready BI files.
- Remove family-local key drift such as `engine_evolution`, `evolution_arc`, and `evolution_stages`.
- Keep the field narrow: this is metadata for a concrete growth-bearing entity, not a free-floating summary paragraph.

## 2. Canonical Key

- Canonical field name: `evolution`
- Allowed value types:
  - `string`
  - `string[]`
- Core meaning:
  - a compact progression trace for one concrete entity such as a martial art, special ability, engine, doctrine, or other growth-bearing capability

## 3. When To Use It

- Use `evolution` when the BI needs a compact "how this thing grows across blocks/phases" trace.
- Do not force it into every BI object.
- It is recommended when one of the following exists:
  - named martial art / technique growth
  - named special ability growth
  - protagonist engine or doctrine growth
  - a concrete capability whose progression matters to later production or audit

## 4. Placement Rules

- Attach `evolution` to the concrete entity object that grows.
- Good:
  - `MartialHUD.Protagonist.actual_truth.martial_status.martial_arts[*].evolution`
  - `protagonist_config.special_ability.evolution`
  - `ProjectData.CoreIdentity.<engine_like_object>.evolution`
- Bad:
  - a detached top-level `evolution` with no entity owner
  - copying the same `evolution` text into multiple unrelated objects

## 5. Content Rules

- `string` form:
  - use one compact arrow-trace string
  - example: `B22~23 1~3침 → B61 6침 완성 → B69 7침 완성`
- `string[]` form:
  - use when the engine progression is better expressed as phase-by-phase short lines
  - each item should stay compact
- Block references are allowed inside `evolution` because this field is metadata.
- Do not spill the same block-trace into `origin`, `description`, `summary`, or other narrative prose fields.
- Keep it compact. No paragraphs.

## 6. Legacy Alias Policy

- Deprecated aliases:
  - `engine_evolution`
  - `evolution_arc`
  - `evolution_stages`
- Read compatibility:
  - existing BI may still contain these legacy keys
- Write policy:
  - all new or newly touched BI should write `evolution`
- Migration policy:
  - normalize legacy aliases to `evolution` when the containing object is touched
  - do not write both canonical and legacy keys into the same newly touched object unless a temporary compatibility reason is explicitly documented

## 7. Family Notes

### 7.1 Wuxguide

- `martial_arts[*].evolution` is the canonical form for named martial-technique growth traces.
- A verified `phase0_design` growth trace may be carried into BI as `evolution` if it matches source TR intent and remains compact.

### 7.2 Blockguide

- `special_ability` or other protagonist engine-like objects should prefer `evolution`.
- Old blockguide BI that used `engine_evolution` or `evolution_arc` should treat those as legacy spellings, not the forward standard.

## 8. Audit Classification

- Default classification: P1 recommended metadata
- It becomes effectively required when a family-specific BI contract explicitly asks for a growth-trace field for that entity family.

## 9. Non-Goals

- This standard does not make `evolution` mandatory in ready TR.
- This standard does not require retrofitting every historical BI immediately.
- This standard does not replace `realm_history`, `portfolio_history`, or other event-history structures.
