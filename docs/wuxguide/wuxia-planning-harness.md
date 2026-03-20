# Wuxia Planning Harness

Date: 2026-03-20
Status: active
Family: `wuxguide`

## 1. When To Use

Use this harness when:

- family is `wuxguide`
- `phase0_design` does not exist yet
- Stage 0 preprocess artifacts exist and `phase0_ready_snapshot.manual_audit_pass == true`

If preprocess artifacts are missing or not audited, return to Stage 0 preprocess first.

## 2. Required Inputs

- canonical pitch / onboarding / user notes
- `treatments/preprocess/{work_id}/source_manifest.json`
- `treatments/preprocess/{work_id}/profile_lock.json`
- `treatments/preprocess/{work_id}/material_bundle_summary.json`
- `treatments/preprocess/{work_id}/phase0_ready_snapshot.json`

## 3. Operator Start

Check readiness first:

```bash
python -X utf8 scripts/narrative_router.py --genre wuxia --work-id <work_id> --json
```

Only continue when:

- `stage == planning`
- `artifact_state.preprocess_ready == true`
- `artifact_state.manual_audit_pass == true`

## 4. Phase 0 Focus

`wuxguide` planning must lock the martial-family progression frame before TR starts.

Minimum Phase 0 concerns:

- protagonist opening lack and pressure
- realm path / breakthrough ladder
- internal-energy curve
- martial-art acquisition path
- sect / clan / alliance map
- enemy ladder and grievance chain
- jianghu reputation path
- treasure / manual / elixir path
- taboo rules and irreversible costs
- npc timeline and foreshadow map

## 5. Recommended Phase 0 Shape

- `project`
  - title, genre code, logline, core premise
- `protagonist`
  - name, age_at_start, opening_status, initial_goal, mid_goal, final_goal, true_strength, true_weakness
- `setting`
  - era, region, jianghu_order, starting_faction, martial_doctrine
- `phase0_design`
  - arcs
  - realm_path
  - internal_energy_curve
  - martial_art_path
  - faction_map
  - npc_timeline
  - foreshadow_map
  - opponent_transition_plan
  - treasure_path
  - taboo_rules
  - do_not_fake

Output target:

```text
treatments/{work_id}_phase0_design.json
```

## 6. Continue / Next Step

After Phase 0 is saved, rerun the router:

```bash
python -X utf8 scripts/narrative_router.py --genre wuxia --work-id <work_id>
```

Expected next stage: `production`.

## 7. Planning Guardrails

- Do not force business-power vocabulary into wuxia planning.
- Do not use `starter_company` as the primary world anchor.
- If the dominant engine is unclear, stop at router classification rather than drafting a hybrid Phase 0 blindly.
