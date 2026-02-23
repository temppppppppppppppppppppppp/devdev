# Stage Map

Purpose:
- Keep one stable documentation surface for Stage 0-4 operations.
- Record actual code-linked behavior after each implementation batch.
- Reduce re-discovery time during audits, bug fixes, and handoffs.

How to use:
1. Start from this file.
2. Open the target stage file (`stage0.md` ... `stage4.md`).
3. Cross-check contracts in `interfaces.md`.
4. Follow incident procedures in `runbook.md`.
5. Update status in `doc_status.md` after each code change batch.

Files:
- `stage0.md`: Stage 0 structure and runtime notes.
- `stage1.md`: Stage 1 structure and runtime notes.
- `stage2.md`: Stage 2 structure and runtime notes.
- `stage3.md`: Stage 3 structure and runtime notes.
- `stage4.md`: Stage 4 structure and runtime notes.
- `interfaces.md`: Stage-to-stage contracts and invariants.
- `runbook.md`: Retry, rollback, and incident handling.
- `metrics_baseline.md`: Baselines and thresholds for key metrics.
- `doc_status.md`: Documentation freshness and code-sync status.

Update rules:
- If code behavior changes, update the matching stage file in the same PR/session.
- Fill `Last Verified` with date + commit hash + verifier.
- Set `Code Sync` to `No` if any known mismatch exists.

