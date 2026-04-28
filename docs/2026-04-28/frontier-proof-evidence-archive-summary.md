# Frontier Proof Evidence Archive Summary

- archive_id: 20260428-154615
- compact_archive_zip: `C:\Users\PC\Desktop\글도비_evidence_archive_20260428-154615.zip`
- compact_archive_size: 83.2 MB
- archive_root: `C:\Users\PC\Desktop\글도비_evidence_archive_20260428-154615`
- root_main_at_archive_time: 3f4dd3f1c61cc87a9bfbb00d1522d17d55ab2e0c
- benchmark_manifest: `benchmarks/frontier_proof_evidence_archive_20260428.csv`
- captured_worktrees: 40
- dirty_worktrees_captured: 19
- project_roots_indexed: 60

## Purpose

This archive preserves the local evidence map for the 2026-04-28 frontier proof wave without committing the large raw project directories to git.
The committed benchmark manifest keeps the worktree name, branch or detached head, commit SHA, dirty count, and total indexed project bytes for each evidence source.

## Main Inclusion

The code and PR results are already on `main` through PRs #84 through #111.
This follow-up only promotes benchmark-facing metadata and the final direct supervised Stage3/Stage4 benchmark rows that were still local in the post-#109 proof worktree.

## Desktop Cleanup Guidance

The `C:\Users\PC\Desktop\글도비_*` proof folders are git worktrees created for parallel verification.
After this archive and the committed manifest are verified, those worktrees can be removed if we only need the compact benchmark evidence and main history.
Do not delete them yet if we need full raw project databases, draft text payloads, or uncommitted runtime directories beyond the compact archive.

The compact zip contains small evidence files, status snapshots, diffs, docs, logs, benchmark metadata, and project summaries.
It does not contain complete copies of the large project roots; those original paths are indexed in the manifest.
