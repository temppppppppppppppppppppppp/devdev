# Stage0 Preprocess Harness

Status: scaffold draft
Date: 2026-03-31

## Goal

`reference_selection`을 기반으로 `source_manifest -> profile_lock -> material_bundle_summary -> phase0_ready_snapshot`를 만든다.

## Input Priority

1. `reference_selection.json`
2. saved slim card labels
3. project brief / user notes
4. legacy project artifacts if explicitly needed

## Output

- `20_preprocess/source_manifest.json`
- `20_preprocess/profile_lock.json`
- `20_preprocess/material_bundle_summary.json`
- `20_preprocess/phase0_ready_snapshot.json`

## Stop Rule

- `phase0_ready_snapshot.manual_audit_pass != true`면 planning 진입 금지

