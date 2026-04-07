# Canon

This directory stores work-level canonical pitch docs and transition anchor notes.

Rules:

- read `material_ssot/20_pitch/material-benchmark-readiness-harness-v1.md` before locking a new canon file
- point to the current best pitch source for each work
- prefer a `material_ssot/20_pitch` path when a migrated payload exists
- if no standalone pitch file exists, record the current source of truth explicitly
- keep work-level canonical references inside the stage SSOT root
- when a work is strong enough, replace the bootstrap note with a full canonical pitch doc
- do not lock canon while any upstream `first_block_cider_ledger` row in `2~6` remains `has_cider: false`
- use `canonical_pitch_template_v1.md` for future canon files
- run `python -X utf8 scripts/material_promotion_gate.py --stage canon --path <canon-md>` before canon lock

Current state:

- `office_checkup_next_day.md` is the first active canonical pitch exemplar
- `pantech_cyworld_reborn.md` is the second active canonical pitch exemplar
- `wuxia_heavenly_physician.md` still operates as a transition anchor note
