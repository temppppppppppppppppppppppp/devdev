# Wuxia BI Production Harness

Date: 2026-03-20
Status: active
Family: `wuxguide`
Output: `bible/0_bi_{work_id}.json`

## 1. When To Use

Use this harness when:

- family is `wuxguide`
- `tr_block_070_draft` already exists
- `0_bi_{work_id}.json` does not exist yet, or needs audit / repair

## 2. Canonical BI Root

The canonical root is `MartialHUD`.

Minimum expectation:

- `MartialHUD.Protagonist.actual_truth` must exist
- `_genre` must resolve to `wuxia` or the intended martial-family code
- `plot_roadmap` must be copied from TR, not rewritten from memory
- current martial state must sync with the final TR block

## 3. Routed Commands

Build:

```bash
python -X utf8 scripts/build_narrative_bi.py --genre wuxia --phase0 treatments/<work_id>_phase0_design.json --draft treatments/<work_id>_tr_block_070_draft.json --output bible/0_bi_<work_id>.json
```

Audit:

```bash
python -X utf8 scripts/audit_narrative_bi.py --genre wuxia --phase0 treatments/<work_id>_phase0_design.json --draft treatments/<work_id>_tr_block_070_draft.json --bi bible/0_bi_<work_id>.json --report bible/audit_reports/<work_id>_wuxia_bi_5pass.md
```

## 4. Minimum BI Sections

- `MasterBible.ProjectData`
- `plot_roadmap`
- `MartialHUD`
- `WorldState`
- `AssetLibrary.KeyNPCs`
- `FactionMap`
- `Treasures`
- `Seeds`

## 5. Minimum MartialHUD Truth

Recommended minimum fields:

- `name`
- `alias`
- `age`
- `current_realm`
- `internal_energy`
- `current_martial_arts`
- `faction`
- `injuries`
- `resources`
- `current_objective`
- `mid_term_goal`
- `final_goal`

Recommended public-reputation fields:

- `jianghu_title`
- `feared_by`
- `trusted_by`
- `rumor_state`

## 6. BI Guardrails

- `FinanceHUD` is not canonical for this family.
- compatibility aliases are allowed only when runtime bridging explicitly requires them.
- `plot_roadmap` title sequence must match TR exactly.
- realm, internal-energy, reputation, and enemy-pressure end state must not contradict the final TR block.
- sect / clan / jianghu status cannot be left as generic placeholders.
