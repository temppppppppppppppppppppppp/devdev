# phase0 Root Shelf

Date: 2026-04-20
Status: active operator note
Scope: root `treatments/phase0` shelf after donor-ready waiting-room wave

This folder now keeps only the current donor-ready keep file on the visible root shelf.

- root `treatments/phase0/` keeps only `golden_canary_deepclone_probe_a_fullblock_v1_phase0_design.json`
- non-keep `Phase0` files move into `_waiting_room/`
- resolver-based tools may still reopen hidden files by direct `work_id`

Current root keep file:

- `golden_canary_deepclone_probe_a_fullblock_v1_phase0_design.json`

Waiting room:

- `treatments/phase0/_waiting_room/2026-04-20_donor_ready_root_wave/`

Operator rule:

- this wave hides root clutter without deleting old Phase0 authority files
- `config/material_waiting_room_manifest.json` is the moved-file ledger
