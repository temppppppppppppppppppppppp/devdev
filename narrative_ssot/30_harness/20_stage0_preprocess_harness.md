# Stage0 Preprocess Harness

Status: scaffold draft
Date: 2026-03-31

## Goal

`reference_selection`을 기반으로 `source_manifest -> profile_lock -> material_bundle_summary -> phase0_ready_snapshot`를 만든다.

## Input Priority

1. `reference_selection.json`
   - optional `profile_override` may lock the intended primary/secondary profile before Stage0 draft generation
2. saved slim card labels
3. project brief / user notes
4. legacy project artifacts if explicitly needed

## Suggested Command

```text
python -X utf8 scripts/build_stage0_from_reference_selection.py --work-id <work_id>
```

## Output

- `20_preprocess/source_manifest.json`
- `20_preprocess/profile_lock.json`
- `20_preprocess/material_bundle_summary.json`
  - must reserve `opening_bundle_contract`
  - the default reader-earning window is `TR 2~6`
  - the contract must name the opening macro battlefield, signboard block, reevaluation block, and next-ticket block
- `20_preprocess/phase0_ready_snapshot.json`

## Stop Rule

- `phase0_ready_snapshot.manual_audit_pass != true`면 planning 진입 금지
- scaffold placeholders must be replaced before Stage0 lock
