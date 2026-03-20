# Preprocess Production Base Template

Copy this folder to `treatments/preprocess/{work_id}/` before Stage 0 work.

Rules:
- Keep the four contract files at the top level.
- Do real work inside the numbered folders.
- Promote only final approved assets to `treatments/` and `bible/`.
- Do not skip `manual_audit_pass`.
- Use `docs/sequential_run_status.json` as the primary production resume pointer.
- `docs/sequential_run_status.md` may exist as a human-readable mirror, but it is not the canonical resume source.
- Prefilled block folders or copied final drafts count as `seed_baseline_sync`, not real sequential progress.

Minimal flow:
1. Fill `00_brief/` and `01_source_pack/`.
2. Complete the four Stage 0 contract files.
3. Set `phase0_ready_snapshot.manual_audit_pass` to `true` only after manual review.
4. Build `phase0_design`.
5. Produce TR one block at a time.
6. Build BI after TR gate pass.

Resume rule:
- `run_class = sequential_production` and `last_sequential_block_pass = N` -> continue at `Block {N+1}`.
- `run_class = seed_baseline_sync` or missing status -> restart at `Block 001`.
