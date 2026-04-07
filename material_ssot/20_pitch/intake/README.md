# Intake

Incoming, draft, and imported legacy pitch materials are staged here.

Current structure:

- `legacy_import/20260320`: migrated legacy pitch payload batch
- `legacy_import/20260330`: migrated legacy pitch payload batch
- `legacy_import/supporting/20260320`: supporting onboarding prompts that still belong to pitch intake context

Current intake rule:

- read `material_ssot/20_pitch/material-benchmark-readiness-harness-v1.md` before calling any intake file `selection-ready`
- use `fresh_candidate_template_v1.md` for future fresh candidate files
- no intake file may self-upgrade around unresolved `first_block_cider_ledger` holes
- run `python -X utf8 scripts/material_readiness_validator.py --path <intake-md-or-dir>` before promotion

Quarantine-only documents do not belong here and should stay under `../quarantine/`.
