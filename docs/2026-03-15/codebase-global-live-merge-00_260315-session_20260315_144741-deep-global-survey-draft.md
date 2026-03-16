<!-- [참고자료] -->
# Codebase Global Live Merge 00_260315 Session 20260315_144741 Deep Global Survey Draft

Date: 2026-03-15
Status: draft-live-run-pending
Mode: `ROL live-merge + deep global survey`
Canonical Path: `docs/2026-03-15/codebase-global-live-merge-00_260315-session_20260315_144741-deep-global-survey-draft.md`
Baseline Commit: `d2982aa2`
Baseline Dirty Summary: `modified=6, deleted=51, untracked=11, other=0`
Project: `projects/00_260315`
Session ID: `20260315_144741`
Source Draft Evidence:
- `docs/2026-03-15/codebase-global-live-merge-00_260315-session_20260315_144741-preflight-watchlist.md`
- `docs/2026-03-15/codebase-global-live-merge-00_260315-session_20260315_144741-live-run-evidence-manifest.md`
- `docs/2026-03-15/codebase-global-live-merge-00_260315-session_20260315_144741-live-run-evidence.txt`
Companion Drafts:
- `docs/2026-03-15/codebase-global-live-merge-00_260315-session_20260315_144741-cross-cut-integrity-matrix-draft.md`
- `docs/2026-03-15/codebase-global-live-merge-00_260315-session_20260315_144741-uncertainty-contradiction-ledger-draft.md`
Raw Inventories:
- `docs/2026-03-15/codebase-global-live-merge-00_260315-session_20260315_144741-source-inventory.txt`
- `docs/2026-03-15/codebase-global-live-merge-00_260315-session_20260315_144741-hotspot-ranking.txt`
- `docs/2026-03-15/codebase-global-live-merge-00_260315-session_20260315_144741-surface-anchor-inventory.txt`

## 1. Mode Lock
- This document is a deep global survey draft, not a final SSOT.
- The fresh live run is still active, so final conclusions, closure claims, execution SSOT mirrors, and roadmap closure remain blocked.
- Mid-run evidence is authoritative for freshness only. Final defect classification waits for terminal state and post-run merge audit.

## 2. Scope
Included:
- `main_a.py`
- `modules/`
- `scripts/`
- `tests/`
- `UI/`
- `geuldobi-desktop/`
- root-level system bootstrap/config surfaces
- active live-run artifacts under `projects/00_260315/`

Excluded by default:
- `.git/`
- cache and build outputs
- `node_modules/`
- `dist/`
- `build/`
- `__pycache__/`
- historical logs outside the active run unless required for contradiction checks
- narrative pipeline content generation assets as primary survey targets

Operational note:
- `UI/` is included for operator-surface coverage, but current active app-shell logic is weighted toward `geuldobi-desktop/` and backend bridge code.
- `geuldobi-desktop/` counts in this draft are active-source counts with `node_modules/dist/build` excluded.

## 3. Macro Topology Snapshot
- top-level active system sweep roots:
  - `main_a.py`
  - `modules/`
  - `scripts/`
  - `tests/`
  - `UI/`
  - `geuldobi-desktop/`
  - `config/`
- active-source counts with build/cache excluded:
  - `modules`: `265 files / 7,241,852 bytes`
  - `scripts`: `36 files / 643,193 bytes`
  - `tests`: `354 files / 4,217,904 bytes`
  - `UI`: `637 files / 351,444,333 bytes`
  - `geuldobi-desktop`: `49 files / 1,272,083 bytes`
  - `config`: `55 files / 21,152,181 bytes`
- `modules/core`: `175 files`
- `modules/domain`: `46 files`
- top heavy hotspots by line count still cluster in:
  - `modules/core/stage4_interview_round.py`
  - `main_a.py`
  - `modules/core/db_manager.py`
  - `modules/core/stage4_context_builder.py`
  - `modules/domain/agents/base_agent.py`
  - `modules/domain/agents/four_phase_arc_generator.py`
  - `modules/core/stage3_orchestrator.py`
  - `modules/api/bridge_server.py`

Primary control spine:
1. `main_a.py`
2. stage orchestrators under `modules/core/`
3. persistence and audit services under `modules/core/`
4. desktop/backend bridge under `geuldobi-desktop/src/` and `modules/api/`
5. operational harnesses under `scripts/`
6. regression surface under `tests/`

Included-path note:
- this draft covers macro + micro + cross-cut + operational views across the active system roots
- it is not a historical-doc sweep and does not treat archival logs or narrative assets as primary truth

## 4. Tranche Coverage

### Tranche A. Macro Topology
Coverage:
- repo topology and active runtime roots inventoried
- entry/control spine identified
- included/excluded scope locked

Provisional hotspot:
- runtime authority is split across CLI core, backend bridge, desktop shell, and heavy script/test harnesses; this is manageable but increases contradiction risk during live runs

### Tranche B. Runtime Core
Key anchors:
- `main_a.py` (`4091` lines)
- `modules/core/stage2_orchestrator.py` (`944` lines)
- `modules/core/stage3_orchestrator.py` (`1888` lines)
- `modules/core/stage4_orchestrator.py` (`1510` lines)
- `modules/api/process_runner.py` (`669` lines)
- `modules/api/bridge_server.py` (`1764` lines)

Observed traits:
- `main_a.py` still owns prompt flow, one-stop pipeline control, pass-rate flush hook, and audit summary trigger points
- prompt surfaces remain mixed between `_get_int_input(...)` and raw `input(...)`
- `modules/api/process_runner.py` keeps both Mode A pre-fed stdin and Mode B interactive prompt handling in one runner
- `bridge_server.py` and `process_runner.py` jointly own live desktop/app orchestration, so CLI and desktop runtime truth are not isolated
- `main_a.py` normalizes stdout/stderr/stdin early, but current live evidence still shows content-level message corruption downstream

Provisional hotspot:
- runtime core remains highly centralized in `main_a.py`, so operator-surface regressions and sink-alignment defects can still couple to one another

### Tranche C. Domain and Agent Layer
Key anchors:
- `modules/domain/agents/base_agent.py` (`1885` lines)
- dense agent layer with Director, ChiefWriter, Analyst, Manager, ensemble generators, validators, and continuity surfaces
- hotspot outliers also include:
  - `modules/domain/agents/state_tracker_npc.py` (`2205` lines)
  - `modules/domain/agents/chief_writer.py` (`1892` lines)
  - `modules/domain/agents/analyst.py` (`1848` lines)
  - `modules/domain/agents/director_ensemble.py` (`1440` lines)

Observed traits:
- generation, review, and validation are highly distributed across many agents
- retry, advisory, and self-critique behavior is embedded deeply in agent layer rather than isolated in one control module
- current live run shows active ChiefWriter self-critique and repeated remote calls through session log tail

Provisional hotspot:
- content corruption may originate before durable sink serialization if already-corrupted strings are produced or transformed in the agent/review layer

### Tranche D. Persistence and Observability
Key anchors:
- `modules/core/db_manager.py` (`3362` lines)
- `modules/core/services/audit_service.py` (`231` lines)
- `main_a.py` flush/save hooks
- persistence entry anchors observed directly:
  - `save_anchor`
  - `load_anchor`
  - `save_director_selection`
  - `save_llm_call`
  - `save_stage_attempt`
  - `save_ui_event`
  - `flush_audit_buffer`
  - `write_audit_summary`

Observed traits:
- DB manager remains a large mixed-responsibility persistence hub
- compatibility migration, anchor storage, attempt persistence, UI event persistence, and close/rollback logic all live in the same substrate
- audit service writes `runtime_audit.jsonl` and `runtime_audit_summary.json`, and builds proof digests from DB + JSONL sinks
- current live evidence shows:
  - `runtime_audit_summary.json`, `pass_rate_monitor.json`, and `runtime_audit.jsonl` paused at `2026-03-15 14:56:45`
  - `ui_events.jsonl`, `llm_io.jsonl`, `quality_metrics.jsonl`, and DB WAL continued moving through `15:05:35`

Provisional hotspot:
- observability surfaces still look time-skewed mid-run; post-run merge must decide whether this is expected heartbeat behavior or renewed stale-summary drift

### Tranche E. Operator Surface and App Shell
Key anchors:
- `modules/core/services/ui_service.py` (`194` lines)
- `modules/core/studio_visualizer.py` (`163` lines)
- `geuldobi-desktop/src/main.js` (`814` lines)
- `geuldobi-desktop/src/desktop_control_plane_contract.js` (`91` lines)
- direct prompt anchors still exist in:
  - `main_a.py`
  - `modules/core/services/project_service.py`
  - `modules/core/stage4_post_processor.py`
  - `scripts/run_auto_frontier_lag_harness.py`

Observed traits:
- CLI prompt rendering and raw `input(...)` handling remain partly duplicated across core UI service and direct runtime calls
- prompt dedup fix remains in place, but visible message payloads in `ui_events.jsonl` still look corrupted
- Electron shell spawns backend, mediates IPC, and bridges `/run`, `/stop`, `/status`, `/quality/*`, and prompt resolution routes
- `UI/` directory is mostly asset/reference payloads, not the active control plane

Provisional hotspot:
- operator-visible integrity is currently threatened more by text payload corruption than by prompt duplication

### Tranche F. Quality and Regression Surface
Inventory:
- `tests/test_*.py` total: `282`
- tagged counts:
  - `ui`: `14`
  - `db`: `13`
  - `stage2`: `10`
  - `stage4`: `10`
  - `desktop`: `7`
  - `frontier`: `4`
  - `process`: `3`
  - `runtime`: `3`
  - `canary`: `3`
  - `audit`: `2`
  - `encoding`: `1`
- deeper operational outliers by line count include:
  - `tests/test_stage4_interview_round.py`
  - `tests/test_pass_with_fix.py`
  - `tests/test_stage3_orchestrator.py`
  - `tests/test_stage4_orchestrator.py`
  - `tests/test_failure_analyzer.py`

Observed traits:
- regression surface is broad but uneven; operator-path and sink-alignment issues are spread across many targeted tests rather than one integrated system suite
- low-memory pytest governance is now codified, but temporary artifacts and long-running live tests still require manual discipline

Provisional hotspot:
- integrated live operator regressions can still slip through despite targeted unit tests because the runtime is multi-surface and cross-process

### Tranche G. Scripts and Utility Surface
Inventory:
- `scripts/*.py` categories:
  - `run_*`: `8`
  - `build_*`: `8`
  - `validate_*`: `2`
  - `repair_*`: `1`
  - `*audit*`: `2`
  - `*check*`: `1`
  - `other`: `12`

Observed traits:
- scripts layer mixes runtime-affecting harnesses, validation/governance tools, content builders, and repair utilities
- runtime-affecting harnesses include:
  - `run_auto_frontier_lag_harness.py`
  - `run_stage2_smoke.py`
  - `run_stage3_smoke.py`
  - `run_stage4_smoke.py`
  - `run_stage4_canary.py`
  - `run_stage34_canary.py`
  - `run_pytest_lowmem.py`
- governance scripts now include:
  - `ops_validator.py`
  - `check_utf8_hygiene.py`
  - `validate_deep_global_survey_bundle.py`
  - `sync_temp_queue_state.py`
- large script hotspots also include:
  - `scripts/investment_corpus_support.py`
  - `scripts/tr_batch_harness.py`
  - `scripts/build_fallen_prince_buys_joseon_assets.py`
  - `scripts/build_chaebol_allowance_zero_assets.py`

Provisional hotspot:
- script layer is a real operational substrate, not a side shelf; governance and runtime harness responsibilities are still co-located

### Tranche H. Cross-Cutting Contracts and Config
Key anchors:
- `AGENTS.md`
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/live-run-merge-survey-harness.md`
- `docs/2026-03-13/encoding-boundary-contract.json`
- `docs/implementation/event-schema-v1.json`
- `.editorconfig`
- `.pre-commit-config.yaml`

Observed traits:
- governance layer is now much more formalized, with explicit live-merge mode and queue rules
- encoding boundary and UTF-8 hygiene are documented and gated
- live run evidence still suggests the code/data path can emit corrupted Korean payloads despite those guardrails

Provisional hotspot:
- current contract strength is higher than the observed runtime text integrity, which means enforcement is still incomplete somewhere between source strings, transform layers, and durable sinks

## 5. Cross-Cutting Provisional Findings
1. Content-level mojibake remains the largest open cross-cut issue.
   - Current session sinks are UTF-8 decodable, but many Korean message payloads are visibly corrupted.
2. Mid-run observability surfaces are not aligned on freshness.
   - Summary files paused while append-only JSONL and DB WAL continued moving.
3. Session identity appears split.
   - Plain session log filename uses `20260315_144654`, while JSONL sink events use `session_id = 20260315_144741`.
4. The current menu `7` regression does not appear to have resurfaced in the active run so far.
   - No fresh evidence of the initial tranche prompt reappearing has been captured in this cycle.
5. Active operator/runtime authority is still highly centralized.
   - `main_a.py`, `db_manager.py`, `bridge_server.py`, and the Stage 3/4 orchestration stack remain blast-radius hotspots.
6. `UI/` is high-volume but low-authority for current logic.
   - The directory is large in bytes, but active operator behavior is governed more by CLI core and Electron/bridge code.

## 6. Provisional Action-Bearing Areas
- Area A: text integrity / mojibake boundary tracing across runtime, UI sinks, and session log content
- Area B: audit/pass-rate/session summary freshness and terminal-state alignment
- Area C: session identity/log naming alignment across plain logs, JSONL sinks, and DB-backed attempts
- Area D: process/desktop bridge observability, especially where stdout/stderr and prompt routing define operator truth
- Area E: hotspot concentration and responsibility spread around `main_a.py`, `db_manager.py`, `bridge_server.py`, and Stage 4 runtime surfaces

These are provisional action areas only. Final execution SSOT mapping waits for post-run merge.

## 7. Notable Non-Findings So Far
- no fresh evidence yet that menu `7` initial prompt regression returned
- no fresh evidence yet of prompt double-render resurfacing
- no fresh evidence yet of DB proof-digest contract failure under the new committed-only read path

## 8. Draft Confidence
- provisional confidence: `83%`

Confidence is capped below final-save threshold because:
- the run is still active
- summary-vs-WAL freshness is unresolved
- session identity split is unresolved
- mojibake source boundary is unresolved

## 9. Post-Run Merge Requirements
- capture terminal state of the live run
- compare final `runtime_audit_summary.json`, `pass_rate_monitor.json`, DB counts, and artifact counts
- decide whether paused summary files were expected heartbeat behavior or stale-write drift
- localize content-level mojibake to source text, transform layer, sink serialization, or shell rendering
- convert confirmed action areas into canonical execution docs only after the merged audit passes the 3-pass gate
