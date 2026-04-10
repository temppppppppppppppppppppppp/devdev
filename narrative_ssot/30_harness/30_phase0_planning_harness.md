# Phase0 Planning Harness

Status: scaffold draft
Date: 2026-03-31

## Goal

전처리 산출물을 바탕으로 `phase0_design.json`을 만든다.

## Required Inputs

- `source_manifest.json`
  - `work_identity.title` is the first title authority; if it is unresolved, Phase0 may retain an existing manual title but should not invent a new one
  - `work_identity.commercial_label / slug_aliases` should be mirrored into planning so later BI/TR builders keep naming surfaces aligned
- `profile_lock.json`
- `material_bundle_summary.json`
- `phase0_ready_snapshot.json`

## Suggested Command

```text
python -X utf8 scripts/build_phase0_seed_from_stage0.py --work-id <work_id>
```

## Opening Bundle Contract

- `material_bundle_summary.opening_bundle_contract` is mandatory planning authority
- `phase0_design.opening_bundle_contract` must mirror the preprocess contract before TR production begins
- the contract must keep the first reader-earning bundle inside `TR 2~6`
- the contract must name:
  - `macro_battlefield`
  - `macro_battlefield_map`
  - `bundle_goal`
  - `first_signboard_block`
  - `representative_reevaluation_block`
  - `next_battlefield_ticket_block`
  - `timing_reconciliation_note`

## Required Output

- `30_planning/phase0_design.json`

## Minimum Design Axes

- title
- work_identity_surface
- protagonist
- core_fantasy
- opening_arc
- opening_bundle_contract
- representative_spike
- growth_axis
- opponent_transition_plan
- payoff_axis
