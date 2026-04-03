# 20_pitch

Role:

- become the canonical stage hub for pitch and intake
- separate canonical pitch state from intake and archive state
- stabilize work-level pitch anchors and imported legacy payloads

Transition note:

- `material_ssot/20_pitch/intake/legacy_import` now stores migrated payloads from the old `전처리_ssot/기획안` bundle
- `material_ssot/20_pitch/quarantine` stores pitch-adjacent docs that are not current pitch truth
- `전처리_ssot/docs/10_pitches` remains a legacy transition source
- `전처리_ssot/기획안` is now a frozen pointer path and should not receive new payloads

Bootstrap rule:

- use `canon/` to register work-level pitch anchors
- use `intake/legacy_import/` for migrated legacy pitch payloads
- use explicit deferred notes when a standalone pitch file does not yet exist
- use `quarantine/` only for non-canonical pitch-adjacent docs
- point new references to `material_ssot/20_pitch` paths, not the old bundle
