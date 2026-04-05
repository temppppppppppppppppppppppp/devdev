# Work Coverage Matrix

Date: 2026-04-05
Status: active bounded matrix
Scope: current representative bounded work coverage inside `material_ssot`

## 1. Coverage Table

| work_id | family | research manifest | pitch anchor | Stage0 manifest | Phase0 manifest | TR manifest | BI manifest | key gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `gatekeeper_heir` | `blockguide` | yes | yes | yes | yes | yes | yes | later enrichment only |
| `office_checkup_next_day` | `blockguide` | yes | yes | yes | yes | yes | yes | raw research path not yet pinned |
| `wuxia_heavenly_physician` | `wuxguide` | yes | yes | yes | yes | yes | yes | root phase0 live file not yet materialized |

## 2. Stage Notes

### gatekeeper_heir

- canonical pitch now exists at `material_ssot/20_pitch/canon/gatekeeper_heir.md`
- Phase0, TR, and BI all exist as live artifacts

### office_checkup_next_day

- pitch resolves to `material_ssot/20_pitch/intake/legacy_import/20260330/컨셉기획_검진다음날부터.md`
- Phase0, TR, and BI all exist as live artifacts

### wuxia_heavenly_physician

- pitch resolves to `material_ssot/20_pitch/intake/legacy_import/20260320/컨셉기획_041_무협_천의무쌍.md`
- phase0 currently resolves through `treatments/preprocess/wuxia_heavenly_physician/phase0_ready_snapshot.json`
- TR and BI exist as live artifacts and both are currently canonical

## 3. Validation Note

- bounded work-chain validation now runs through `python -X utf8 scripts/validate_material_ssot.py`

## 4. Rule

Do not expand the work set by default until one of these happens:

- governance rules need stress testing on another family
- a new live work already has stable preprocess, TR, and BI paths
- the current three bootstrap works stop being representative
