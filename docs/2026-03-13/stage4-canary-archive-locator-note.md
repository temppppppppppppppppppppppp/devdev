# Stage 4 Canary Archive Locator Note

Created: 2026-03-13
Status: `runtime-open`

## Summary

- Historical docs cite `projects/00_test_07`.
- In the current workspace, neither `projects/00_test_07` nor `projects/기록용/00_test_07` exists.
- No `canary_summary.json` is currently present under `projects/`.
- Those historical canary links are stale in this workspace.

## Decision For This Turn

- No fresh canary rerun was executed.
- No new runtime proof artifact was generated.
- Future canary artifacts now have an archive-safe `project_locator`.

## Rules Going Forward

- Use `canary_summary.json.project_locator` as the canonical locator.
- Record these three items together in docs:
- `project_locator`
- `logs/canary_summary.json`
- `project_data.db`
- Nested project names are allowed.
- Example: `archive/demo_canary`

## Current Judgment

- Historical proof based on `projects/00_test_07` is not reopenable in this workspace.
- Runtime proof remains open until a fresh rerun is intentionally produced.
- This note is the archive-stable pointer for old path references.
