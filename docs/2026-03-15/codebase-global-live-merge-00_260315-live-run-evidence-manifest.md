<!-- [참고자료] -->
# Codebase Global Live-Merge 00_260315 Live Run Evidence Manifest

Date: 2026-03-15
Status: evidence-frozen
Topic Slug: `codebase-global-live-merge-00_260315`
Baseline Commit: `083c86d9`
Baseline Dirty Summary: `modified=30, deleted=54, untracked=7`
Run State: `stopped / bounded-partial`
Authority Rule: completed live-run evidence > static inference > stale survey text

## Included Evidence

### Process State
- Terminal process classification:
  - former active process: `python.exe main_a.py`
  - PID: `13684`
  - current state: no live `main_a.py` process remains
  - shutdown class: `stopped / bounded partial` because the session log ends mid-Stage-2 without a graceful shutdown marker, traceback, or current-run crash dump

### Primary Runtime Evidence
- `projects/00_260315/logs/session_20260315_132843.log`
- `projects/00_260315/logs/session/ui_events.jsonl`
- `projects/00_260315/logs/session/decisions.jsonl`
- `projects/00_260315/logs/session/llm_io.jsonl`
- `projects/00_260315/project_data.db`
- `projects/00_260315/project_data.db-wal`

### Secondary Runtime Evidence
- `projects/00_260315/logs/runtime_audit_summary.json`
- `projects/00_260315/logs/pass_rate_monitor.json`
- `projects/00_260315/logs/runtime_audit.jsonl`
- `projects/00_260315/logs/quality_metrics.jsonl`

### Static Survey Anchors
- `main_a.py`
- `modules/core/logger.py`
- `modules/core/db_manager.py`
- `modules/core/services/audit_service.py`
- `modules/core/studio_visualizer.py`
- `modules/core/services/ui_service.py`
- `modules/api/process_runner.py`
- `scripts/check_utf8_hygiene.py`

## Current Evidence Shape

### Sink Freshness
- `ui_events.jsonl`: `346` lines and still advancing during the run
- `llm_io.jsonl`: `41` lines and still advancing during the run
- `decisions.jsonl`: `6` lines, last update `2026-03-15T13:42:04`
- `project_data.db`: active with WAL sidecar
- `project_data.db-wal`: larger and newer than the base DB file, so base-file `mtime` alone is not authoritative mid-run
- `runtime_audit_summary.json`, `pass_rate_monitor.json`, `runtime_audit.jsonl`: frozen at `2026-03-15T13:37:10` during current observation window
- `quality_metrics.jsonl`: still advancing after the summary/audit trio stopped

### Observed Alignment
- `ui_events.jsonl` line count: `346`
- `ui_events` DB row count: `346`
- `llm_io.jsonl` line count: `41`
- `llm_calls` DB row count: `41`
- `director_selections` DB row count: `5`
- `stage_attempts` DB row count: `5`

### Static Logger Trace
- `main_a.py` initializes the studio logger before runtime work and binds `SessionLogger` separately.
- `modules/core/logger.py` writes `session_<session_name>.log` through `logging.FileHandler(..., encoding="utf-8")` on both the studio logger and root logger attachment path.
- Current plain `.log` mojibake therefore does not yet support the narrow claim “missing UTF-8 file handler”; the defect is likely higher in the message path or caused by mixed sink composition.

### Session Log Landmarks
- Initial frontier tranche prompt recorded once
- Initial batch size confirmed as `3`
- Frontier arc progression entered `Arc 1/60 frontier 전진 (1/3)`
- Stage 4 episode 1 reached `director_verdict=PASS score=92 selected=A`
- `ui_events.jsonl` currently shows the frontier-tranche interaction as one `prompt` row plus one hidden `prompt_response` row plus one hidden `selection` row, which is consistent with the dedup contract rather than a duplicated visible prompt.

## Known Caveats
- Plain session `.log` lines currently show mojibake-like operator text in some surfaces.
- JSONL sinks and DB excerpts observed so far remain UTF-8 legible.
- `scripts/check_utf8_hygiene.py` currently over-flags legitimate Korean prompt lines and crashes when emitting certain findings to cp949 PowerShell.

## Excluded For Now
- `docs/temp/` mirrors: none active
- historical dated docs: reference only
- stale `logs/pytest_lowmem/`: unrelated to the active live run

## Next Merge Inputs
- terminal run state
- final `runtime_audit_summary.json`
- final `pass_rate_monitor.json`
- final session log tail
- final `project_data.db` + `-wal` reconciliation
- static contradiction review across prompt, audit, process-runner, and UTF-8 guardrail surfaces
