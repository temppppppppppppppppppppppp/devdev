<!-- [참고자료] -->
# Codebase Global Live Merge 00_260315 Session 20260315_144741 Cross-Cut Integrity Matrix Draft

Date: 2026-03-15
Status: draft-live-run-pending
Project: `projects/00_260315`
Session ID: `20260315_144741`
Baseline Commit: `d2982aa2`

| Surface | Primary Anchors | Side Effects | Current Live Evidence | Provisional Risk |
| --- | --- | --- | --- | --- |
| Runtime entry and pipeline | `main_a.py`, `stage2_orchestrator.py`, `stage3_orchestrator.py`, `stage4_orchestrator.py` | prompts, stage transitions, DB writes, audit hooks | active run in Stage 4; no fresh menu `7` regression seen yet | medium |
| Prompt and operator I/O | `main_a.py`, `ui_service.py`, `studio_visualizer.py` | console output, input waits, UI events | prompt dedup retained, but message payload corruption remains visible in `ui_events.jsonl` | high |
| Persistence substrate | `db_manager.py` | anchors, stage attempts, selections, UI events, commits/rollbacks | DB counts continue moving via WAL; stage attempts and selections already outpace paused summary files | high |
| Audit and heartbeat summary | `audit_service.py`, `main_a.py` pre-summary save hook | `runtime_audit.jsonl`, `runtime_audit_summary.json`, proof digest | summaries paused at Stage 3 timestamp while run continues | high |
| Session telemetry | `session/ui_events.jsonl`, `session/decisions.jsonl`, `llm_io.jsonl` | append-only JSONL sinks | UTF-8 decodable, but many Korean payloads are already corrupted in content | high |
| Desktop bridge | `geuldobi-desktop/src/main.js`, `desktop_control_plane_contract.js`, `bridge_server.py`, `process_runner.py` | subprocess control, IPC, route mediation, stdout/stderr tails | route and IPC surface is broad; current run is CLI, but bridge remains parallel operational substrate | medium |
| Governance and guards | `AGENTS.md`, `.editorconfig`, `.pre-commit-config.yaml`, `check_utf8_hygiene.py` | policy enforcement, pre-commit gates, survey governance | guardrail strength increased, but runtime text corruption still exists beyond file-encoding checks | medium-high |
| Regression harnesses | `run_auto_frontier_lag_harness.py`, `run_pytest_lowmem.py`, smoke/canary scripts, test suite | validation, bounded reruns, low-memory execution | targeted unit coverage is broad; integrated live behavior still needs post-run confirmation | medium |

## Matrix Notes
- `UI/` binary asset packs are not treated as a primary logic substrate in this cycle.
- The highest provisional risk is not raw file encoding; it is corrupted operator-visible payload content inside already-decoded sinks.
- Summary freshness remains unresolved until the run terminates.
