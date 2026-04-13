# hoegui_surgeon BI refresh audit memo

Date: 2026-04-12
Work ID: `hoegui_surgeon`
Envelope: `bi_refresh`
Result: `build_complete / audit_fail / rehab_wave_6_complete`

## 1. Entry Set

- `treatments/phase0/hoegui_surgeon_phase0_design.json`
- `treatments/hoegui_surgeon_tr_block_020_draft.json`
- `docs/2026-04-12/hoegui_surgeon_block_61_70_self_audit.md`

## 2. Outputs

- live BI created:
  - `bible/0_bi_hoegui_surgeon.json`
- audit report:
  - `bible/audit_reports/hoegui_surgeon_bi_5pass.md`

## 3. Builder / Audit Compatibility

- `scripts/build_bi_from_phase0_and_tr.py`
  - closed a legacy profile mismatch by deriving BI checkpoints from:
    - `genre_ext.capital_after`
    - fallback `genre_ext.authority_after`
    - fallback `content.reward`
    - fallback `title`
- `scripts/audit_bi_5pass.py`
  - closed a legacy profile mismatch by:
    - treating `setting.starter_company` as optional
    - comparing BI portfolio sync against the same derived checkpoint logic as the builder

These script mismatches are now closed. The remaining FAIL is no longer a runner issue.

## 4. Current Audit Truth

- BI build: `OK`
- BI 5-pass: `FAIL`
- dominant fail cluster:
  - `production_density_gate = FAIL`
  - `diegetic_meta_ref_count = 741`
  - `label_meta_ref_count = 0`
  - `npc_continuity_mismatch_count = 129`
  - `bi_diegetic_meta_leak_count = 753`
  - hard-gate failures:
    - `diegetic_meta_ref_zero`
    - `diegetic_block_ref_zero`

## 5. Rehab Wave 1 (completed)

- unit:
  - `genre_ext.section_rotation` label cleanup on the 21 ARC-tagged blocks
- result:
  - `source_tr_label_meta_gate = OK`
  - `bi_label_meta_leak_count = 0`
  - `label_meta_ref_count = 0`

## 6. Rehab Wave 2 (completed)

- unit:
  - `genre_ext.block_cider` backfill across Blocks 1-70
- result:
  - `block_cider_declared = OK`
  - `no_cider_blocks_zero = OK`
  - `cider_receipt_line_present = OK`
  - hard-gate failures reduced to:
    - `diegetic_meta_ref_zero`
    - `diegetic_block_ref_zero`

## 7. Rehab Wave 3 (completed)

- unit:
  - bounded diegetic meta leak sweep on Blocks `21-30`
  - touched fields only:
    - `content.context`
    - `content.reward`
    - `content.solution`
- result:
  - targeted slice hit count reduced from:
    - `context: 8`
    - `reward: 13`
    - `solution: 13`
  - targeted slice residuals after patch:
    - `context: 0`
    - `reward: 0`
    - `solution: 0`
  - global audit deltas:
    - `diegetic_meta_ref_count = 840 -> 825`
    - `bi_diegetic_meta_leak_count = 856 -> 841`
  - unchanged carry:
    - `npc_continuity_mismatch_count = 129`
    - `production_density_gate = FAIL`

## 8. Rehab Wave 4 (completed)

- unit:
  - bounded diegetic meta leak sweep on Blocks `31-40`
  - touched fields only:
    - `content.context`
    - `content.reward`
    - `content.solution`
- result:
  - targeted slice hit count reduced from:
    - `context: 18`
    - `reward: 53`
    - `solution: 34`
  - targeted slice residuals after patch:
    - `context: 0`
    - `reward: 0`
    - `solution: 0`
  - global audit deltas:
    - `diegetic_meta_ref_count = 825 -> 798`
    - `bi_diegetic_meta_leak_count = 841 -> 813`
  - unchanged carry:
    - `npc_continuity_mismatch_count = 129`
    - `production_density_gate = FAIL`

## 9. Rehab Wave 5 (completed)

- unit:
  - bounded diegetic meta leak sweep on Blocks `41-50`
  - touched fields only:
    - `content.context`
    - `content.reward`
    - `content.solution`
- result:
  - targeted slice hit count reduced from:
    - `context: 29`
    - `reward: 56`
    - `solution: 31`
  - targeted slice residuals after patch:
    - `context: 0`
    - `reward: 0`
    - `solution: 0`
  - global audit deltas:
    - `diegetic_meta_ref_count = 798 -> 771`
    - `bi_diegetic_meta_leak_count = 813 -> 785`
  - unchanged carry:
    - `npc_continuity_mismatch_count = 129`
    - `production_density_gate = FAIL`

## 10. Rehab Wave 6 (completed)

- unit:
  - bounded diegetic meta leak sweep on Blocks `51-60`
  - touched fields only:
    - `content.context`
    - `content.reward`
    - `content.solution`
- result:
  - targeted slice hit count reduced from:
    - `context: 44`
    - `reward: 56`
    - `solution: 105`
  - targeted slice residuals after patch:
    - `context: 0`
    - `reward: 0`
    - `solution: 0`
  - global audit deltas:
    - `diegetic_meta_ref_count = 771 -> 741`
    - `bi_diegetic_meta_leak_count = 785 -> 753`
  - unchanged carry:
    - `npc_continuity_mismatch_count = 129`
    - `production_density_gate = FAIL`

## 11. Next Legal Step

- pair completion is still blocked
- next main envelope: `schema_backfill`
- next bounded rehab unit:
  - diegetic meta leak sweep
  - continue the same family on Blocks `61-70`
  - first target fields should remain:
    - `content.reward`
    - `content.context`
    - `content.solution`
  - current residual count in that slice:
    - `context: 19`
    - `reward: 36`
    - `solution: 54`
- follow-up rehab families:
  - NPC continuity normalization

## 12. Operator Note

- `tr_continue` is closed
- this is not a continuation problem
- this is a `legacy TR schema/content rehab -> BI re-audit` problem
