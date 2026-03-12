# chaebol_allowance_zero preprocess base

This folder is the active Stage 0 production base for `chaebol_allowance_zero`.

Rules:
- Keep the four contract files at the top level.
- Use `00_brief/` and `01_source_pack/` for human-readable locks and audit notes.
- Treat failed numbered assets as reference-only.
- Promote only final approved assets to `treatments/` and `bible/`.
- Do not reopen Planning unless `manual_audit_pass` stays defensible.

Minimal flow:
1. Reconfirm `source_manifest.json`, `profile_lock.json`, `material_bundle_summary.json`, and `phase0_ready_snapshot.json`.
2. Update `00_brief/` if title, protagonist, or scope drifts.
3. Build or normalize `treatments/chaebol_allowance_zero_phase0_design.json`.
4. Produce TR one block at a time from `03_tr_blocks/`.
5. Merge verified blocks into `04_tr_final/`.
6. Build BI only after TR gate pass.
