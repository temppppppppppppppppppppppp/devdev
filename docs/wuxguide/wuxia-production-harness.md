# Wuxia Production Harness

Date: 2026-03-20
Status: active
Family: `wuxguide`
Output: `treatments/{work_id}_tr_block_070_draft.json`

## 1. When To Use

Use this harness when:

- family is `wuxguide`
- `phase0_design` already exists
- `tr_block_070_draft` does not exist yet, or needs the next batch

## 2. Core Production Principle

The TR block engine remains sequential, but the semantic contract is martial-family specific.

Each block should primarily advance one or more of:

- realm progression
- internal-energy movement
- martial-art gain or refinement
- sect / clan / alliance consequence
- jianghu reputation shift
- revenge or grievance escalation / payoff

## 3. Routed Commands

Prompt:

```bash
python -X utf8 scripts/narrative_tr_batch.py --genre wuxia prompt --draft treatments/<work_id>_tr_block_070_draft.json --roadmap bible/0_bi_<work_id>.json --start <start_block> --batch-size 3 --output treatments/<work_id>_batch_prompt.md
```

Check:

```bash
python -X utf8 scripts/narrative_tr_batch.py --genre wuxia check --candidate treatments/<candidate>.json --draft treatments/<work_id>_tr_block_070_draft.json --start <start_block> --batch-size 3 --report treatments/<work_id>_batch_check.md
```

Merge:

```bash
python -X utf8 scripts/narrative_tr_batch.py --genre wuxia merge --draft treatments/<work_id>_tr_block_070_draft.json --candidate treatments/<candidate>.json --start <start_block> --batch-size 3 --report treatments/<work_id>_batch_merge.md
```

## 4. Wuxia Block Contract

Recommended `genre_ext` keys:

- `realm_before`
- `realm_after`
- `internal_energy_before`
- `internal_energy_after`
- `martial_art_gain`
- `artifact_or_manual_gain`
- `faction_position`
- `jianghu_reputation`
- `enemy_pressure`
- `opponent.name`
- `opponent.sect_or_faction`
- `opponent.weakness_exploited`

## 5. Continuity Priorities

Production review should prioritize:

- realm continuity
- internal-energy continuity
- injury and recovery continuity
- martial-art acquisition causality
- sect / clan consequence tracking
- grievance escalation or payoff
- foreshadow / callback integrity

## 6. Production Guardrails

- Do not require `capital_before/after` for wuxia validity.
- Do not require `deal_type`, `business_sector`, `company_state`, or `business_lines`.
- Do not translate every gain into wealth metaphors.
- If a hybrid work needs both martial and business axes, martial continuity still leads inside `wuxguide`.
