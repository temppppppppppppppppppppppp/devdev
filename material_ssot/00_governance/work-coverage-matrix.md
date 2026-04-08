# Work Coverage Matrix

Date: 2026-04-08
Status: active bounded matrix
Scope: representative bounded work coverage inside `material_ssot`

## 1. Coverage Table

| work_id | family | research manifest | pitch anchor | Stage0 manifest | Phase0 manifest | TR manifest | BI manifest | key gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `office_checkup_next_day` | `blockguide` | yes | yes | yes | yes | yes | yes | raw research path not yet pinned |
| `wuxia_heavenly_physician` | `wuxguide` | yes | yes | yes | yes | yes | yes | raw research path not yet pinned |

This matrix stays intentionally bounded to representative end-to-end research-to-live chains.

Global live-pair readiness and benchmark freshness are tracked separately in `production-pair-operational-registry-v1.md`.

## 2. Stage Notes

### office_checkup_next_day

- pitch resolves to `material_ssot/20_pitch/intake/legacy_import/20260330/컨셉기획_검진다음날부터.md`
- Phase0, TR, and BI all exist as live artifacts
- current live pair is schema-clean under `production_pair_normalization_runner.py`

### wuxia_heavenly_physician

- pitch resolves to `material_ssot/20_pitch/intake/legacy_import/20260320/컨셉기획_041_무협_천의무쌍.md`
- root `treatments/phase0/wuxia_heavenly_physician_phase0_design.json` now exists as the canonical Phase0 file
- TR and BI exist as live artifacts and the current live pair is schema-clean

## 2A. Companion Visibility Note

- `office_checkup_next_day`: work-guard library publish visible at `work_guards/07_office_checkup_next_day.yaml`
- `wuxia_heavenly_physician`: work-guard library publish visible at `work_guards/09_wuxia_heavenly_physician.yaml`
- these entries are advisory material-side companion signals, not stage hard gates

## 3. Validation Note

- bounded work-chain validation now runs through `python -X utf8 scripts/validate_material_ssot.py`
- repo-level pre-new-pitch readiness now runs through `python -X utf8 scripts/pre_new_pitch_readiness_gate.py`

## 4. Rule

Do not expand the representative work set by default until one of these happens:

- governance rules need stress testing on another family
- a new work has stable research-to-live manifests and should replace a current exemplar
- the bounded pair registry and fresh-pitch preflight both remain stable after the next expansion
