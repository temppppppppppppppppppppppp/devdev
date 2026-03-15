# Codebase Global Live Merge 00_260315 Session 20260315_144741 Live Run Evidence Manifest

Date: 2026-03-15
Status: draft-live-run-pending
Project: `projects/00_260315`
Session ID: `20260315_144741`

## Process Anchor
- Active process: `python main_a.py`
- PID: `9292`
- Created: `2026-03-15 14:46:53`

## Files and Freshness
- `projects/00_260315/logs/session_20260315_144654.log`
  - last observed tail includes active Stage 4 ChiefWriter HTTP traffic through `2026-03-15 15:05:35`
- `projects/00_260315/logs/session/ui_events.jsonl`
  - last write `2026-03-15 15:03:27`
  - last observed `seq = 372`
- `projects/00_260315/logs/session/decisions.jsonl`
  - last write `2026-03-15 15:01:55`
  - currently contains finalized Stage 2 and Stage 3 records plus Stage 4 episode 1 director selection
- `projects/00_260315/logs/session/llm_io.jsonl`
  - last write `2026-03-15 15:05:35`
- `projects/00_260315/logs/runtime_audit_summary.json`
  - last write `2026-03-15 14:56:45`
  - tag `stage3_complete`
- `projects/00_260315/logs/pass_rate_monitor.json`
  - last write `2026-03-15 14:56:45`
  - `total_records = 4`
- `projects/00_260315/logs/runtime_audit.jsonl`
  - last write `2026-03-15 14:56:45`
- `projects/00_260315/logs/quality_metrics.jsonl`
  - last write `2026-03-15 15:03:10`
- `projects/00_260315/project_data.db`
  - last write `2026-03-15 15:01:57`
- `projects/00_260315/project_data.db-wal`
  - last write `2026-03-15 15:05:35`

## Current Read-Only Snapshots
- DB counts:
  - `stage_attempts = 5`
  - `llm_calls = 46`
  - `ui_events = 372`
  - `director_selections = 5`
- artifact counts:
  - `stage3 = 9`
  - `stage4 = 4`
- latest concrete Stage 4 artifact on disk:
  - `logs/artifacts/stage4/ep_0001/attempt_01/final_manuscript__C.txt`
  - `logs/artifacts/stage4/ep_0001/attempt_01/selected_candidate__C.txt`

## Provisional Evidence Rules
- Mid-run summary files are provisional because the run is still active.
- DB/WAL and append-only JSONL sinks currently outrank paused summary files for freshness only, not for final defect classification.
- Final interpretation waits for terminal state.
