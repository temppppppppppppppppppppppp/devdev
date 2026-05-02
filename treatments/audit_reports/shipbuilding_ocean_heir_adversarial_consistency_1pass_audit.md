# shipbuilding_ocean_heir Adversarial Consistency 1-Pass Audit

Date: 2026-05-02
Status: PASS
Work ID: `shipbuilding_ocean_heir`
Scope: one adversarial consistency audit after GREENPLUS / immediate-deployment / range-complete admission

## 1. Attack Posture

This audit did not assume the existing PASS labels were true. It attacked five possible failure modes:

- registry / overlay says immediate deployment, but the row still carries candidate-only or pending language
- TR and BI roadmap diverged after prior quality-up surfaces
- downstream episode pacing hints are incomplete, uniform, or open B071+
- donor-review / contamination guardrails are missing from visible material-side authority
- reward engine is generic succession praise rather than shipbuilding / ship-finance rights, control, cash, status, or approval receipts

No code, runtime, S2, or core plot rewrite was in scope.

## 2. Files Audited

- `treatments/shipbuilding_ocean_heir_tr_block_070_draft.json`
- `bible/0_bi_shipbuilding_ocean_heir.json`
- `bible/_waiting_room/2026-05-01_shipbuilding_ocean_heir/0_bi_shipbuilding_ocean_heir.json`
- `treatments/preprocess/shipbuilding_ocean_heir/source_manifest.json`
- `treatments/phase0/shipbuilding_ocean_heir_phase0_design.json`
- `material_ssot/00_governance/production-pair-operational-registry-v1.json`
- `material_ssot/00_governance/production-pair-operational-registry-v1.md`
- `docs/2026-04-29/material-side-immediate-deployment-overlay.md`
- prior shipbuilding source / BI / range / GREENPLUS / reaudit reports

## 3. Mechanical Evidence

| check | result |
| --- | --- |
| JSON parse for TR / BI / waiting BI / source / Phase0 / registry | PASS |
| TR block count | `70` |
| BI roadmap count | `70` |
| block_no range | `1-70` |
| TR/BI order sync | `true` |
| TR/BI genre_ext mismatch | `0` |
| root BI / waiting-room BI byte equality | `true` |
| registry alias | `GREENPLUS` |
| registry schema status | `pass` |
| registry deployment status | `immediate_deployable_material` |
| registry range status | `range_complete` |
| registry overlay status | `current_immediate_deployment_shelf_range_complete` |

Coverage:

| surface | TR | BI |
| --- | ---: | ---: |
| `capital_delta` | `70/70` | `70/70` |
| `success_pattern` | `70/70` | `70/70` |
| `reader_payoff_ladder` | `70/70` | `70/70` |
| `webnovel_pacing_contract` | `70/70` | `70/70` |
| `downstream_episode_pacing_hint` | `70/70` | `70/70` |

Normalization:

- `pair_consumability=pass`
- `strict_tier_a_status=pass`
- `tier_b_status=normalized`
- `schema_status=pass`
- `evidence_mode=serialized_canonical`
- `open_migration_debt=false`
- `alias_refresh_eligible=true`
- `active_baseline_eligible=true`
- `required_fix_targets=[]`

## 4. Attack Results

### Attack 1: Candidate / Pending Language Leak

Question: does the active shipbuilding row still read as a candidate or delayed row?

Result: PASS.

- registry JSON row has `benchmark_alias=GREENPLUS`
- `material_deployment_status=immediate_deployable_material`
- `range_attachment_status=range_complete`
- `immediate_overlay_status=current_immediate_deployment_shelf_range_complete`
- deployment artifact points to `shipbuilding_ocean_heir_immediate_deployment_reaudit_patch_loop_3pass_audit.md`
- overlay shipbuilding section uses promotion / immediate-deployment identity language

Non-target note: registry / overlay now include additional later admissions such as `power_grid_heir`. This audit did not revert or judge those rows; it only checked that the shipbuilding row remains coherent inside the latest surface.

### Attack 2: TR / BI Surface Drift

Question: did prior repairs create TR/BI divergence?

Result: PASS.

- block count and block order sync remain exact
- `genre_ext` mirror mismatch is `0`
- root BI and waiting-room BI remain byte-identical
- no missing block numbers and no B071+ expansion

### Attack 3: Range Hint Abuse

Question: are downstream pacing hints mechanically stamped, incomplete, or over-expanded?

Result: PASS.

- required hint fields are present across all 70 TR blocks
- TR/BI mirror coverage is `70/70`
- range distribution remains non-uniform: `2-3 x48 / 3 x1 / 3-4 x21`
- final block closes on final authority receipt and does not open B071+

### Attack 4: Donor / Contamination Authority

Question: are donor adoption and contamination guardrails visible only in audit wording, not material authority?

Result: PASS.

- `source_manifest.donor_review.decision=adopted`
- `source_manifest.donor_review.contamination_guard` count is `5`
- `phase0_design.donor_review.decision=adopted`
- `phase0_design.contamination_guard` count is `5`
- `phase0_design.do_not_fake` count is `3`
- BI `GenreRules.contamination_guard` count is `5`
- BI `BIAmplificationPower` exists

Clarification: Phase0 guardrails live under the nested `phase0_design` object, not as top-level JSON keys. The nested location is valid for this Phase0 schema and is not a defect.

### Attack 5: Reward Engine Flattening

Question: does the work secretly close on praise, family recognition, or generic succession drama?

Result: PASS.

- donor proper-noun contamination scan found no donor work-id / domain-token hits in the TR/BI material payload
- BI amplification thesis explicitly blocks generic heir praise from replacing operating assets
- active reward identity remains shipbuilding / ship-finance business power: contract review rights, production raw-data access, guarantee review seats, waiver terms, supplier slots, account control, market frame, insurance/rate repricing, paid verification, deposits, vetoes, and final approval authority

Non-blocking note: `genre_ext.block_cider` does not serialize a field named `same_block_receipt`; the receipt is carried by the block `content.reward` plus the canonical cider fields accepted by the consumability and normalization validators. Because both validators pass and no block reward is missing, this is not a defect.

## 5. Validation Commands

```powershell
python -X utf8 scripts/check_bi_tr_consumability.py --bible bible/0_bi_shipbuilding_ocean_heir.json --treatment treatments/shipbuilding_ocean_heir_tr_block_070_draft.json --json
python -X utf8 scripts/production_pair_normalization_runner.py --bible bible/0_bi_shipbuilding_ocean_heir.json --treatment treatments/shipbuilding_ocean_heir_tr_block_070_draft.json --state regenerated_pair --json
python -X utf8 scripts/check_utf8_hygiene.py treatments/shipbuilding_ocean_heir_tr_block_070_draft.json bible/0_bi_shipbuilding_ocean_heir.json bible/_waiting_room/2026-05-01_shipbuilding_ocean_heir/0_bi_shipbuilding_ocean_heir.json treatments/preprocess/shipbuilding_ocean_heir/source_manifest.json treatments/phase0/shipbuilding_ocean_heir_phase0_design.json material_ssot/00_governance/production-pair-operational-registry-v1.json material_ssot/00_governance/production-pair-operational-registry-v1.md docs/2026-04-29/material-side-immediate-deployment-overlay.md
```

Observed result: PASS.

## 6. Final Ruling

PASS.

No payload patch is required from this adversarial pass. `shipbuilding_ocean_heir` remains:

- `GREENPLUS`
- schema `pass`
- `immediate_deployable_material`
- `range_complete`
- current immediate-deployment shelf material
