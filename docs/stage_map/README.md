# Stage Map

Purpose:
- Keep one stable documentation surface for Stage 0-4 operations.
- Record current workspace behavior, not just the last clean commit.
- Reduce re-discovery time during audits, bug fixes, and handoffs.

How to use:
1. Start here.
2. Read `UPDATE_ORDER.md` to understand source priority, metadata rules, and refresh procedure.
3. Open the relevant stage file (`stage0.md` ... `stage4.md`).
4. Cross-check handoff contracts in `interfaces.md`.
5. Use `runbook.md` for destructive safe-op semantics.
6. Confirm freshness in `doc_status.md`.

Source Priority:
1. Current workspace code and tracked behavior in this working tree.
2. Consolidated audit evidence from `docs/2026-03-13/*`.
3. Existing `docs/stage_map/*` content.

Files:
- `UPDATE_ORDER.md`: Canonical refresh order for this folder.
- `stage0.md`: Stage 0 structure, cache, provenance, and runtime notes.
- `stage1.md`: Stage 1 volume-planning structure and runtime notes.
- `stage2.md`: Stage 2 arc-production structure and runtime notes.
- `stage3.md`: Stage 3 blueprint-production structure and runtime notes.
- `stage4.md`: Stage 4 manuscript-production structure and runtime notes.
- `interfaces.md`: Stage-to-stage contracts and invariants.
- `gotchas.md`: Current pitfalls that are easy to misread from docs or logs.
- `agent_graph.md`: Text call graph for Stage 2/3/4 runtime surfaces.
- `runbook.md`: Retry, rollback, wipe, and rewind semantics.
- `metrics_baseline.md`: Full-suite baseline plus live threshold ledger.
- `doc_status.md`: Freshness and code-sync status.
- `SYNC_CHECK.md`: Active sync-check playbook.
- `FILL_ORDER.md`: Deprecated historical fill order.
- `ENHANCE_ORDER.md`: Deprecated historical enhance order.

Metadata Rules:
- Active docs use the same footer schema:
  - `Date`
  - `Commit`
  - `Workspace State`
  - `Code Sync (Yes/No)`
  - `Verified By`
- `Commit` records the HEAD commit used as the verification basis.
- `Workspace State` records whether verification happened against a clean or dirty tree.
- Set `Code Sync` to `No` only when the document is known to be out of sync with the current workspace.

Update Rules:
- If code behavior changes, update the matching stage_map document in the same session when possible.
- Prefer recording unresolved issues under `Open Risks` or `Known drift` rather than leaving stale facts in the main flow.
- Do not promote partial pytest runs to the global baseline. Only the last verified full-suite result belongs in `metrics_baseline.md`.

## Last Verified
- Date: 2026-03-13
- Commit: `e18f9910`
- Workspace State: dirty
- Code Sync (Yes/No): Yes
- Verified By: Codex
