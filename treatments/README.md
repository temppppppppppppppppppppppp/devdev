# treatments Root Shelf

Date: 2026-04-20
Status: active operator note
Scope: root `TR` shelf after donor-ready waiting-room wave

This root is no longer the mixed `TR` inventory shelf.

- root `treatments/` now keeps only the current donor-ready keep file
- non-keep `TR` files and sidecars move into `_waiting_room/`
- current keep rule for this wave is recorded in `config/material_waiting_room_manifest.json`

Current root keep file:

- `golden_canary_deepclone_probe_a_fullblock_v1_tr_block_070_draft.json`

Waiting room:

- `treatments/_waiting_room/2026-04-20_donor_ready_root_wave/`

Historical note:

- `docs/2026-04-20/bi-tr-root-lane-audit.md` records the pre-move mixed root state

Operator rule:

- treat the root file as the active donor-ready shelf
- treat `_waiting_room/` as a restore-only holding lane, not a deleted/archive lane
- this wave does not move `treatments/phase0/` or `work_guards/`
