<!-- [참고자료] -->
# Codebase Global Live Merge 00_260315 Session 20260315_144741 Preflight Watchlist

Date: 2026-03-15
Status: draft-live-run-pending
Project: `projects/00_260315`
Session ID: `20260315_144741`
Process:
- `python main_a.py`
- PID `9292`
- created `2026-03-15 14:46:53`

## Intent
- Track current fresh live run without freezing final conclusions before the run reaches a terminal state.
- Keep this cycle separate from the earlier bounded partial run on the same project.

## Priority Watch Items
- `menu 7` nonstop contract:
  - confirm the current run entered FrontierLag without the initial tranche prompt resurfacing
- source-text mojibake persistence:
  - `ui_events.jsonl`, `decisions.jsonl`, and the plain session log decode as UTF-8, but visible Korean message payloads still contain corrupted-looking text
  - treat this as content-level corruption until post-run merge proves otherwise
- mid-run summary staleness:
  - `runtime_audit_summary.json`, `pass_rate_monitor.json`, and `runtime_audit.jsonl` stopped at `2026-03-15 14:56:45`
  - `ui_events.jsonl`, `llm_io.jsonl`, `quality_metrics.jsonl`, and `project_data.db-wal` continued moving after `15:03`
- session identity split:
  - plain session log file is `session_20260315_144654.log`
  - live JSONL sinks are recording `session_id = 20260315_144741`
  - determine post-run whether this is expected boot/session split or a sink-alignment defect
- stage progress correlation:
  - DB counts already show `stage_attempts = 5` and `director_selections = 5`
  - `pass_rate_monitor.json` still shows only `4` finalized records mid-run
  - do not classify this as mismatch until the run terminates

## Read-Only Capture Targets
- `projects/00_260315/logs/session_20260315_144654.log`
- `projects/00_260315/logs/session/ui_events.jsonl`
- `projects/00_260315/logs/session/decisions.jsonl`
- `projects/00_260315/logs/session/llm_io.jsonl`
- `projects/00_260315/logs/runtime_audit_summary.json`
- `projects/00_260315/logs/pass_rate_monitor.json`
- `projects/00_260315/logs/runtime_audit.jsonl`
- `projects/00_260315/logs/quality_metrics.jsonl`
- `projects/00_260315/project_data.db`
- `projects/00_260315/project_data.db-wal`

## Guardrail
- This is a live-run draft watchlist only.
- No final SSOT, closure, or resolved/regressed claim is allowed until the run reaches a documented terminal state and the post-run merge audit passes 3-pass review.
