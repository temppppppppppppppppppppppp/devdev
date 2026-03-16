<!-- [참고자료] -->
# Codebase Global Live-Merge 00_260315 Preflight Watchlist

Date: 2026-03-15
Status: evidence-frozen
Mode: `ROL 전역 전체 전수조사` + `ROL live-merge`
Run State: `stopped / bounded-partial`
Live Run PID: `13684 (terminated)`
Baseline Commit: `083c86d9`
Baseline Dirty Summary: `modified=30, deleted=54, untracked=7`
Canonical Scope: codebase-global system-track survey only
Execution Output Rule: live run reached a terminal state, so final survey synthesis may proceed; execution SSOTs and roadmap refresh remain deferred because this turn is investigation-only

## Scope
- Included primary sweep: `main_a.py`, `modules/`, `scripts/`, `tests/`, `UI/`, `geuldobi-desktop/`, active runtime contracts/config
- Included live evidence: `projects/00_260315/logs/`, `projects/00_260315/project_data.db`
- Excluded by default: generated bulk trees such as `dist/`, `python-embed/`, historical docs, stale `logs/pytest_lowmem/`

## Current Runtime Snapshot
- Menu `7` interactive path is active and recorded one initial tranche prompt plus auto-selection confirmation.
- Active session log: `projects/00_260315/logs/session_20260315_132843.log`
- Active append-only sinks: `ui_events.jsonl`, `llm_io.jsonl`
- Active SQLite persistence: `project_data.db` with `project_data.db-wal`
- `runtime_audit_summary.json`, `pass_rate_monitor.json`, and `runtime_audit.jsonl` have not advanced since `2026-03-15T13:37:10`, while `quality_metrics.jsonl`, JSONL session sinks, and WAL continue moving.

## Tranche Watchlist

### Tranche A. Macro Topology
- Watch whether current live evidence implicates only runtime core or spills into desktop/operator/contract surfaces.
- Preserve current queue state as empty `docs/temp/` plus one active live-merge bundle under `docs/2026-03-15/`.

### Tranche B. Runtime Core
- Confirm that menu `7` contract holds on the normal path:
  - initial prompt occurs once
  - default remains `3`
  - no duplicate prompt render
  - no re-entry prompt between arcs unless failure policy triggers
- Confirm that the earlier shutdown race does not recur if the run is allowed to finish normally.
- Check whether `Faulthandler` and bootstrap notices remain on the intended channel without poisoning operator sinks.

### Tranche C. Domain and Agent Layer
- Confirm Stage 3/4 retries, candidate selection, and advisory chain behavior remain stable for a 3-arc bounded run.
- Recheck `selection_reason` fidelity across `director_selections`, `stage_attempts`, and JSONL after the run reaches terminal state.

### Tranche D. Persistence and Observability
- Reconcile why `runtime_audit_summary.json`, `pass_rate_monitor.json`, and `runtime_audit.jsonl` are stale relative to `quality_metrics.jsonl`, `ui_events.jsonl`, `llm_io.jsonl`, and `project_data.db-wal`.
- Confirm whether summary/audit sinks intentionally flush only at terminal state or whether stale-write drift persists.
- Validate that `ui_events` mirror remains aligned between JSONL and DB row counts after the run completes.
- Recheck proof-digest contract after terminal state because current summary file does not yet expose a usable `truth_scope` field in the live artifact.

### Tranche E. Operator Surface and App Shell
- `session_20260315_132843.log` shows mojibake-like operator-facing lines in the plain session log while `ui_events.jsonl`, `decisions.jsonl`, and DB rows remain UTF-8 clean. This currently looks like sink-specific rendering or logger-path corruption, not whole-system text corruption.
- Static trace already shows `modules/core/logger.py` writes the plain session log through `logging.FileHandler(..., encoding="utf-8")`, so the current suspicion is upstream message corruption, mixed logger path, or render-path drift rather than a missing file-handler encoding declaration.
- Confirm whether the plain `.log` sink is authoritative, derivative, or lossy for Korean/emoji operator text.
- Confirm that prompt dedup remains fixed in live CLI usage, not only in tests.

### Tranche F. Quality and Regression Surface
- Fresh live run evidence may contradict current regression assumptions; do not close any finding until the run ends.
- Newly added `scripts/check_utf8_hygiene.py` is itself on the watchlist:
  - false-positives on legitimate Korean question prompts
  - `UnicodeEncodeError` when printing findings to cp949 PowerShell if snippets contain emoji

### Tranche G. Scripts and Utility Surface
- `scripts/check_utf8_hygiene.py` needs post-run hardening review before it can be trusted as an operator-facing gate on Windows shells.
- Keep utility-surface changes documentation-only during the active run.

### Tranche H. Cross-Cutting Contracts and Config
- Reconcile contract authority between:
  - UTF-8 guardrails in `AGENTS.md`
  - `encoding-boundary-contract.json`
  - process-runner stderr policy
  - actual live session-log behavior
- Confirm that current `.editorconfig` + pre-commit gate do not block valid Korean `?` prompts.

## Immediate Hypotheses
- `H1`: plain session `.log` sink has a narrower or lossy text path than JSONL/DB sinks.
- `H2`: audit/summary sinks are terminal-flush based, not continuously updated, but this must be proven from completed run evidence.
- `H3`: the new UTF-8 hygiene gate is too aggressive for legitimate Korean prompt text and is not yet shell-safe on cp949 hosts.

## Not Final
- This document is not a final survey, final audit, closure note, or execution SSOT.
- All claims here are provisional until the live run reaches `completed`, `failed`, `stopped`, or `aborted by operator`.
