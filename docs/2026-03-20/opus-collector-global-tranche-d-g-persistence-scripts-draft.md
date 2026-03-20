# Tranche D + G: Persistence, Observability, Scripts & Utility Surface — Global Survey Draft

**Status**: DRAFT / NOT AUTHORITY / COLLECTOR ONLY / NO EXECUTION AUTHORITY
**Date**: 2026-03-20
**Terminal**: 3
**Mode**: survey-only, no patches, no execution SSOT, no roadmap, no closure
**Baseline**: git dirty on main (see git status snapshot at conversation start)

---

## 1. Scope

### Included
- **Tranche D**: DB manager, session logger, audit service, JSONL sinks, proof artifacts, logging setup, quality dashboard, pass rate monitor, soft failure system, failure analyzer, metrics collector, control plane provenance, artifact logging
- **Tranche G**: `scripts/` (37 files), `tools2/` (20 files), `tools/` (12 files), `main_tools/` (1 file), root-level utility scripts (8 files)

### Excluded
- `.git/`, `.venv/`, `__pycache__/`, build outputs
- `docs/` (reference only, not sweep target)
- Narrative pipeline content (treatments, bibles, etc.)

### Evidence Sources
- Live workspace code reads (primary authority)
- TF-tagged test fixtures and regression tests (secondary evidence)
- Agent survey reports (6 parallel agents, synthesized below)

---

## 2. Persistence Sink Inventory

### 2.1 Authoritative Sinks (Durable, Truth-Source)

Defined in `modules/api/control_plane_contract.py:49-53` and `modules/core/services/audit_service.py:33-39`.

| Sink ID | Path Pattern | Format | Writer Module | Write Mode |
|---------|-------------|--------|---------------|------------|
| project_data_db | `{project}/project_data.db` | SQLite | `db_manager.py` | transactional R/W |
| control_plane_provenance | `logs/control-plane-provenance.jsonl` | JSONL append | `bridge_server.py:202-231` | append via `append_jsonl_record` |
| episode_production_log | `{project}/logs/episode_production.jsonl` | JSONL append | `stage4_interview_round.py:6037`, `stage4_orchestrator.py:1458` | append via `append_jsonl_record` |
| stage_attempts (DB) | `project_data.db` table | SQLite | `db_manager.py:3499` | non-blocking telemetry |
| pass_rate_monitor | `logs/pass_rate_monitor.json` | JSON overwrite | `pass_rate_monitor.py:152-163` | overwrite (last 1000 records) |
| session_decisions (JSONL) | `logs/session/decisions.jsonl` | JSONL append | `session_logger.py` | append with rotation |
| director_selections (DB) | `project_data.db` table | SQLite | `db_manager.py:2775` | non-blocking telemetry |

### 2.2 Companion Snapshots (Read-Only Aggregations, Not Durable Authority)

Per `control_plane_contract.py:54-61`:

| Surface | Description |
|---------|-------------|
| `/status` | Live runner state, non-authoritative |
| `/quality/dashboard` | Read-only project metrics aggregation |
| `/quality/summary` | Read-only subset |
| `runtime_health` | `soft_failures.jsonl` digest |
| `proof_status` | Derived from sink_alignment + runtime_audit |
| `runtime_audit_summary` | Point-in-time snapshot |

### 2.3 Full JSONL Sink Map

| File | Writer | Data | Lock | Error Handling | Rotation |
|------|--------|------|------|----------------|----------|
| `logs/session/llm_io.jsonl` | SessionLogger | Agent, model, prompt/response, tokens | `_write_lock` | soft_failure | 100MB / 10 files |
| `logs/session/decisions.jsonl` | SessionLogger | Stage, ep_num, decision, score | `_write_lock` | soft_failure | 100MB / 10 files |
| `logs/session/state_changes.jsonl` | SessionLogger | ep_num, entity, before/after | `_write_lock` | soft_failure | 100MB / 10 files |
| `logs/session/ui_events.jsonl` | SessionLogger | Session events, selections | `_write_lock` | soft_failure | 100MB / 10 files |
| `logs/episode_production.jsonl` | stage4_interview_round | Candidates, verdicts, patch trace | `_JSONL_APPEND_LOCK` | WARNING log, non-blocking | None |
| `logs/quality_metrics.jsonl` | QualityDashboard | Validation, HUD, coverage, retrieval | direct open | soft_failure | None |
| `logs/runtime_audit.jsonl` | AuditService | Buffered events (max 1000 → trim 500) | `append_jsonl_record` | WARNING, non-blocking | None |
| `logs/soft_failures.jsonl` | soft_failure.py | Component failures, degraded state | `_JSONL_APPEND_LOCK` | stderr fallback | None |
| `logs/control-plane-provenance.jsonl` | bridge_server | /run invocations, approval_id, risk_key | `_JSONL_APPEND_LOCK` | not observed | None |
| `logs/risk-approval-log.jsonl` | RiskApprovalGate | Approval tickets, status | `_JSONL_APPEND_LOCK` | non-blocking | None |

### 2.4 JSON (Non-JSONL) Sinks

| File | Writer | Format | Write Mode |
|------|--------|--------|------------|
| `logs/pass_rate_monitor.json` | PassRateMonitor | JSON object | Overwrite (every 100 records) |
| `logs/runtime_audit_summary.json` | AuditService | JSON object | Overwrite (on summary write) |

### 2.5 Database Schema Summary (30+ Tables)

**Core Content Tables:**

| Table | Key | Purpose | Migration Status |
|-------|-----|---------|-----------------|
| `anchors` | key (bible, arcs, genre_info, sys_caches, world_state, fact_ledger, chain_link_*, volume_summary_*, series_summary) | JSON-serialized anchor data | Stable |
| `blueprints` | ep_num | Episode design JSON | Stable |
| `manuscripts` | ep_num | Title + content + hud_snapshot | hud_snapshot column migrated |
| `state_logs` | ep_num | State data + summary | summary column migrated |
| `episode_bibles` | ep_num | new_items, new_npcs, relationships, state_changes, reveals + 3 migrated | causal_links, karma_matrix, knowledge_map migrated |
| `causal_graph` | ep_num | Causal link data | Stable |
| `npc_history` | append-only | NPC change tracking | Stable |

**Tracking & Analytics Tables:**

| Table | Purpose | Write Type | Error Level |
|-------|---------|------------|-------------|
| `stage_attempts` | Per-stage attempt telemetry | Telemetry guard | DEBUG only |
| `llm_calls` | Per-LLM-call metrics + 8 migrated columns | Telemetry guard | DEBUG only |
| `ui_events` | User interface events | Telemetry guard | DEBUG only |
| `director_selections` | Director decisions + 10 migrated columns | Telemetry guard | DEBUG only |
| `cost_log` | Scope-level cost records | Telemetry guard | DEBUG only |
| `episode_quality_labels` | Manual quality labels | Normal | Standard |
| `episode_quality_signals` | Python-only quality signals | Normal | Standard |
| `episode_satisfaction_tags` | Satisfaction metrics | Normal | Standard |
| `character_voice_profiles` | Character voice tracking | Normal | Standard |
| `foreshadow` | Foreshadow tracking | Normal | Standard |
| `timeline_entries` | Story timeline | Normal | Standard |
| `npc_relationship_edges` | NPC relationship graph | Normal | Standard |
| `karma_status` | NPC misunderstanding/obsession | Normal | Standard |
| `martial_tracker` | 15 genre-specific metrics | Normal | Standard |
| `seeds` | Foreshadow management | Normal | Standard |
| `encyclopedia` | Lore knowledge base | Normal | Standard |

**Transaction Boundary Summary:**

| Method | Lock | Transaction | Error Level | Blocking |
|--------|------|-------------|-------------|----------|
| `commit_episode_factory()` | `_lock.acquire()` | Explicit `begin()/commit()/rollback()` | CRITICAL on OperationalError | Yes (most critical write) |
| `save_manuscript()` | `_lock` | Nested-aware | Standard | Yes |
| `save_anchor()` | `_lock` | Nested-aware | WARNING, returns bool | Yes |
| `save_blueprint()` | `_lock` | Nested-aware | Standard | Yes |
| `save_llm_call()` | `_lock` | Auto-commit | **DEBUG only** | **No** |
| `save_stage_attempt()` | `_lock` | Auto-commit | **DEBUG only** | **No** |
| `save_ui_event()` | `_lock` | Auto-commit | **DEBUG only** | **No** |
| `save_cost_record()` | `_lock` | Auto-commit | **DEBUG only** | **No** |

### 2.6 Non-DB Persistence: ConstraintDB & MaterialDB

| Class | File | Persistence | Notes |
|-------|------|-------------|-------|
| `ConstraintDB` | `modules/core/constraint_db.py` | Reads from `project_data.db` arcs, builds in-memory ArcState | No direct DB writes; state derived from arcs |
| `MaterialDB` | `modules/core/material_db.py` | Static in-memory data + optional `laws/{genre}.json` loading | No DB writes; read-only material pools |

---

## 3. Observability Flow Map

### 3.1 Logging Stack

```
┌─────────────────────────────────────────────────┐
│  StudioLogger (modules/core/logger.py)          │
│  Root: "글도비" → FileHandler → session_{ts}.log │
│  Boot: faulthandler → crash_dump.log            │
│  Sub-loggers: per-module via getLogger(__name__)  │
└─────────────┬───────────────────────────────────┘
              │
              ├── QualityDashboard → quality_metrics.jsonl
              ├── PassRateMonitor → pass_rate_monitor.json
              ├── SessionLogger → session/{llm_io,decisions,state_changes,ui_events}.jsonl
              ├── AuditService → runtime_audit.jsonl + runtime_audit_summary.json
              ├── SoftFailure → soft_failures.jsonl
              ├── MetricsCollector → in-memory (optional logs/metrics/)
              ├── ArtifactLogger → logs/artifacts/stage{N}/...
              ├── FailureAnalyzer → (read-only, analysis from DB)
              └── BridgeServer → control-plane-provenance.jsonl + WS /events
```

### 3.2 Session Lineage

Defined in `modules/core/logging_keys.py`:
- `resolve_logging_session_id()`: Resolves stable session ID from runtime objects
- `build_attempt_key()`: Deterministic cross-sink key `s{stage}:ep{N}:arc{M}:a{attempt}[:session_id]`
- Lineage reconciliation: Plain log token (`session_*.log` mtime) ↔ structured DB session_id (`stage_attempts`, `ui_events`, `llm_calls`)

### 3.3 JSONL I/O Infrastructure

Single shared writer in `modules/core/jsonl_io.py`:
- `append_jsonl_record()`: Process-wide `threading.Lock`, UTF-8 append, `json.dumps(ensure_ascii=False, default=str)`
- 21 lines total — minimal, well-contained
- Used by: episode_production, runtime_audit, control_plane_provenance, risk_approval, soft_failures

### 3.4 Proof Digest System

Built by `AuditService._build_proof_digest()` (audit_service.py:202-262):

| Check | Source | Status Values |
|-------|--------|---------------|
| `db_available` | project_data.db exists | bool |
| `session_decisions_exists` | logs/session/decisions.jsonl | bool |
| `ui_events_jsonl_exists` | logs/session/ui_events.jsonl | bool |
| `pass_rate_monitor_exists` | logs/pass_rate_monitor.json | bool |
| `episode_production_exists` | logs/episode_production.jsonl | bool |
| `runtime_audit_jsonl_exists` | logs/runtime_audit.jsonl | bool |
| `ui_events_db_available` | COUNT from DB | bool |
| `ui_event_coverage_status` | Cross-check JSONL vs DB | ok / partial / missing |
| `session_lineage` | Plain log ↔ structured DB | unified / split_mapped / partial / missing |
| `stage_3_4_sink_alignment` | FailureAnalyzer.sink_alignment_summary() | issue counts |

### 3.5 Sink Alignment Verification

`FailureAnalyzer.sink_alignment_summary()` checks 17 issue types:
- `final_sink_missing`, `lifecycle_sink_missing`
- `content_hash_mismatches`, `artifact_path_mismatches`, `artifact_missing_files`
- `verdict_reason_mismatches`, `fix_scope_mismatches`
- `session_decision_rows_without_attempt_key`
- (and more per stage 3/4 scope)

### 3.6 Operator-Visible Output Surfaces

| Surface | Module | Mechanism |
|---------|--------|-----------|
| Console (Rich) | `studio_visualizer.py` | `console.print()` + `log()` |
| Operator Event Sink | `studio_visualizer.py` | Callback with seq/level/component/stage/ep_num/message |
| WebSocket `/events` | `bridge_server.py` | Real-time event stream (event-schema-v1) |
| REST `/status` | `bridge_server.py` | JSON runner state |
| REST `/health` | `bridge_server.py` | Aggregated dashboard + pass rate + proof digest |

### 3.7 Degraded-Mode Behaviors

| Component | Trigger | Behavior | Visibility |
|-----------|---------|----------|------------|
| QualityDashboard | File I/O error | In-memory only, soft_failure event | WARNING log |
| PassRateMonitor | JSON load/save failure | WARNING log, continues with empty/stale records | WARNING log |
| SessionLogger | JSONL write failure | soft_failure event, `_soft_failure_count++` | Via `get_health_snapshot()` |
| AuditService | JSONL/DB failure | Non-blocking, event buffered | UI callback |
| Telemetry (DB) | Any exception | **DEBUG only** log, returns False/None | **Not visible in normal logs** |
| ArtifactLogger | Snapshot write failure | soft_failure event, execution continues | WARNING log |
| SoftFailure | Own JSONL write failure | stderr fallback | stderr only |

---

## 4. Script Classification

### 4.1 Classification Table — scripts/ (37 files)

| Script | Category | Runtime-Affecting | DB Mutation | File Writes | Risk |
|--------|----------|------------------|-------------|-------------|------|
| `run_stage2_smoke.py` | test-helper | Yes (Stage2Orchestrator) | Yes | Plan artifacts | Medium |
| `run_stage3_smoke.py` | test-helper | Yes (Stage3Orchestrator) | Yes | Blueprint outputs | Medium |
| `run_stage4_smoke.py` | test-helper | Yes (Stage4Orchestrator) | Yes | Manuscripts, logs | Medium |
| `run_stage34_canary.py` | test-helper | Yes (Stage3+4) | Yes (COPY+RESET+WRITE) | Full project state | **CRITICAL** |
| `run_stage4_canary.py` | test-helper | Yes (Stage4) | Yes (copy, reset, write proof) | CSV summary, proof | **CRITICAL** |
| `run_auto_frontier_lag_harness.py` | test-helper | Yes (CLI) | Yes (project creation) | Watchdog logs | Medium |
| `audit_bi_5pass.py` | verification | No | No | Markdown report | Low |
| `ops_validator.py` | verification | No | No | None (read-only) | Low |
| `validate_deep_global_survey_bundle.py` | verification | No | No | None (read-only) | Low |
| `validate_manual_sweep.py` | verification | No | No | Unknown | Low |
| `regression_validation_tiers.py` | verification | No | No | None (constants only) | Low |
| `tr_batch_harness.py` | test-helper | No | No | None (library) | Low |
| `process_and_audit_tr_bi_loop.py` | verification | No | No | TR & BI JSON, reports | Medium |
| `backfill_quality_sidecars.py` | migration | No | **Direct SQLite** | None | **CRITICAL** |
| `repair_tr_korean_utf8.py` | repair | No | No | **Rewrites TR JSON** | **CRITICAL** |
| `build_bi_from_phase0_and_tr.py` | build | No | No | BI JSON | Medium |
| `build_fallen_prince_buys_joseon_assets.py` | build | No | No | Static BI JSON | Low |
| `build_chaebol_allowance_zero_assets.py` | build | No | No | Static BI JSON | Low |
| `generate_tr_bibles.py` | build | No | No | TR & BI JSON | Medium |
| `build_execution_roadmap.py` | ops-tooling | No | No | `docs/temp/execution-roadmap.md` | Medium |
| `sync_temp_queue_state.py` | ops-tooling | No | No | **Overwrites queue-state.json** | **CRITICAL** |
| `populate_process_health_scorecard.py` | ops-tooling | No | No | Scorecard JSON/CSV | Low |
| `generate_evidence_manifest.py` | ops-tooling | No | No | Manifest JSON | Low |
| `run_pytest_lowmem.py` | test-helper | No | No | `logs/pytest_lowmem/` | Low |
| `check_utf8_hygiene.py` | data-processing | No | No | Hygiene report | Low |
| `mojibake_global_survey.py` | data-processing | No | No | Survey CSV/JSON | Low |
| `build_investment_epub_corpus.py` | data-processing | No | No | `data/investment_corpus/` | Low |
| `investment_corpus_support.py` | data-processing | No | No | Library module | Low |
| `build_investment_gemini_jsonl.py` | data-processing | No | No | JSONL files | Low |
| `build_investment_pseudonymized_corpus.py` | data-processing | No | No | Anonymized corpus | Low |
| `extract_manuscript_samples.py` | data-processing | No | No | Sample txt files | Low |
| `build_title_style_control_dataset.py` | data-processing | No | No | Dataset JSON | Low |
| `generate_stagewise_manuscript_truth_report.py` | verification | No | No | Report markdown | Low |
| `render_later_hardening_autopilot.py` | ops-tooling | No | No | Schedule markdown | Low |
| `tf_c1_patch.py` | repair | No | No | Patched files | Medium |
| `run_stale_reference_sweep.py` | ops-tooling | No | No | Unknown | Low |
| `ops_support.py` | ops-tooling | No | No | Library module | Low |

### 4.2 Classification Table — tools2/ (20 files)

| Script | Category | Runtime-Affecting | Side Effects |
|--------|----------|------------------|-------------|
| `cost_calculation.py` | cost-analysis | No | Print only |
| `full_project_cost.py` | cost-analysis | No | Print only |
| `studio_dashboard.py` | ops-tooling | No | DB read-only (Streamlit) |
| `arc_dashboard.py` | ops-tooling | No | DB read-only (Streamlit) |
| `performance_dashboard.py` | ops-tooling | No | JSON read-only (Streamlit) |
| `style_transfer.py` | data-processing | No | File write + LLM calls |
| `expand_ep15.py` | data-processing | No | File write + LLM calls |
| `automate_snack.py` | data-processing | No | File write |
| `reverse_bible.py` | data-processing | No | File write + LLM calls |
| `sanitize_reference.py` | data-processing | No | File write |
| `apply_v3.py` | data-processing | No | File write |
| `apply_v3_pt2.py` | data-processing | No | File write |
| `test_continuity_validator.py` | test-prototype | No | Console only |
| `test_phase3_systems.py` | test-prototype | No | Console only |
| `test_priority1_security_fixes.py` | test-prototype | No | Console only |
| `test_v0128_validation.py` | test-prototype | No | Console only |
| `test_v43_updates.py` | test-prototype | No | Console only |
| `validation_test_harness.py` | test-prototype | No | Console only |
| `temp.py` | utility | No | File write |
| `rlhf_interface.py` | ops-tooling | No | Unknown (Streamlit?) |

### 4.3 Classification Table — tools/ (12 files, legacy)

| Script | Category | DB Mutation |
|--------|----------|-------------|
| `bible_builder.py` | build | No (outputs JSON) |
| `treatment_builder.py` | build | No (outputs JSON) |
| `treatment_extractor.py` | data-processing | No |
| `make_BP.py` | build | **Yes (INSERT blueprints)** |
| `normalize_arcs_db.py` | migration | **Yes (ALTER + UPDATE)** |
| `db_porter.py` | migration | **Yes (cross-DB copy)** |
| `blueprint_name_fixer.py` | repair | **Yes (UPDATE)** |
| `fix_future_items.py` | repair | No (JSON rewrite) |
| `genre_library_builder.py` | build | No (outputs JSON) |
| `story_expander.py` | data-processing | No |
| `0_json만들기.py` | data-processing | No |
| `concat_txt.py` | data-processing | No |

### 4.4 Root-Level Utilities (8 files)

| Script | Category | Runtime-Affecting | Critical Notes |
|--------|----------|------------------|---------------|
| `main_a.py` | runtime entry | Yes | Primary entry point |
| `RESET.py` | repair | No | DB writes, file deletes |
| `smoke_sc.py` | test-helper | No | Real Gemini API calls (~$0.5-2) |
| `generate_empire_reborn_tr70.py` | data-processing | No | Static treatment output |
| `md2pdf.py` | ops-tooling | No | **Hardcoded: `C:\Windows\Fonts\malgun*.ttf`** |
| `fix_costs.py` | cost-analysis | No | **BROKEN: hardcoded `C:\Users\wjjo\` path** |
| `fix_costs2.py` | cost-analysis | No | **BROKEN: hardcoded `C:\Users\wjjo\` path** |
| `tmp_utf8_check.py` | repair | No | Print only |

### 4.5 main_tools/ (1 file)

| Script | Category | DB Mutation | Risk |
|--------|----------|-------------|------|
| `blueprint_editor.py` | ops-tooling | **Yes (direct SQLite UPDATE)** | **CRITICAL** |

---

## 5. Runtime-Affecting Utilities

### 5.1 Runtime-Imported Scripts (via Stage Orchestrators)

All 6 smoke/canary runners in `scripts/` directly import from `modules/core/`:

```
scripts/run_stage{2,3,4}_smoke.py → modules/core/stage{2,3,4}_orchestrator.py
scripts/run_stage34_canary.py → Stage3Orchestrator + Stage4Orchestrator
scripts/run_stage4_canary.py → SovereignApp + PassRateMonitor
```

These create real project state (DB writes, log files, artifact directories).

### 5.2 Scripts That Directly Mutate Production DB

| Script | Mutation Type | Backup Required |
|--------|-------------- |-----------------|
| `backfill_quality_sidecars.py` | Direct SQLite UPDATE/INSERT | Yes |
| `tools/make_BP.py` | INSERT blueprints | Yes |
| `tools/normalize_arcs_db.py` | ALTER schema + UPDATE data | Yes |
| `tools/db_porter.py` | Cross-DB copy | Yes |
| `tools/blueprint_name_fixer.py` | UPDATE blueprint records | Yes |
| `main_tools/blueprint_editor.py` | Direct SQLite UPDATE | Yes |

### 5.3 Scripts Not Imported by Runtime

All `tools2/` files: zero imports from `main_a.py` or `modules/`. Confirmed safe for runtime isolation.

All `tools/` files: legacy standalone CLI tools, not imported.

---

## 6. Side-Effect Sweep

### 6.1 File Writes and Artifact Generation

| Writer | Output Pattern | Directory Auto-Create | Overwrite Behavior |
|--------|---------------|----------------------|-------------------|
| DBManager | `project_data.db` | `mkdir(parents=True, exist_ok=True)` | Transaction-controlled |
| SessionLogger | `logs/session/*.jsonl` | Yes (on init) | Append + rotation |
| QualityDashboard | `logs/quality_metrics.jsonl` | No (assumes logs/ exists) | Append |
| ArtifactLogger | `logs/artifacts/stage{N}/**` | Yes (makedirs) | New file per attempt |
| PassRateMonitor | `logs/pass_rate_monitor.json` | No (assumes logs/ exists) | Overwrite |
| AuditService | `logs/runtime_audit{.jsonl,.json}` | Via append_jsonl_record | Append / Overwrite |
| SoftFailure | `logs/soft_failures.jsonl` | Yes (directory auto-create) | Append |
| BridgeServer | `logs/control-plane-provenance.jsonl` | Via append_jsonl_record | Append |
| StudioLogger | `logs/session_{ts}.log` | Yes (on init) | FileHandler append |

### 6.2 DB Writes, Schema Touchpoints, Transaction Boundaries

**Critical transaction**: `commit_episode_factory()` (db_manager.py:2147-2334)
- Lock: `_lock.acquire()`/`.release()` with try-finally
- Explicit `begin()` → multi-table INSERT → `commit()` or `rollback()`
- Error tiers: IntegrityError (HIGH), OperationalError (CRITICAL), DBError (re-raise if nested), Exception (HIGH)
- Rollback safety: `try: self.rollback() except: pass`

**Schema migration**: Auto-migration in `_boot_db()` via ALTER TABLE wrapped in try-except-commit/rollback per column.

**WAL mode**: Enabled in `_boot_db()` for concurrent read/write.

**Integrity checks**: `PRAGMA integrity_check` on connection init.

**Corruption recovery**: `_quarantine_corrupt_db()` creates `.corrupt_*` backup (db_manager.py:180).

### 6.3 Console, UI, and Operator-Visible Output

- `StudioVisualizer.log()` → Rich console + `logging.getLogger("UI").info()`
- `StudioVisualizer.set_operator_event_sink()` → Structured callback with 15+ fields (seq, level, component, stage, ep_num, etc.)
- Bridge WebSocket `/events` → Real-time stream to desktop client

### 6.4 Rollback, Recovery, Retry, Compensation

- `commit_episode_factory()`: Full transaction rollback on any error
- `ProjectService`: `rollback()`, `rewind()` — destructive ops with `DestructiveOpResult.db_committed` tracking
- DB corruption: `_quarantine_corrupt_db()` → `.corrupt_*` backup then fresh init
- No automatic retry on DB write failures (telemetry writes just fail silently)

### 6.5 Cache, Global State, In-Memory Mutation

- `MetricsCollector`: In-memory cache with 600s stale cleanup, RLock
- `QualityDashboard`: 5 in-memory collections (max 500 items each)
- `PassRateMonitor`: In-memory records (max 1000) + file-backed JSON
- `SessionLogger`: `_soft_failure_count` counter
- `AuditService`: In-memory buffer (max 1000 events, trim to 500)
- `ConstraintDB`: In-memory ArcState derived from DB arcs

### 6.6 Config Mutation, Env Loading, Bootstrap Fallback

- `StudioLogger.retarget()`: Moves from bootstrap location to project logs, seeds early logs
- `GEULDOBI_RUN_ID` env var: Used as session_id by MetricsCollector, PassRateMonitor
- DB boot: `_boot_db()` creates 30+ tables if not exist, runs column migrations
- ConstraintDB: `_degraded` flag if project context unavailable

---

## 7. Facts

**FACT-D1**: `jsonl_io.py` is 21 lines, uses a single process-wide `threading.Lock`, UTF-8 append. All JSONL sinks except SessionLogger's own files go through this.

**FACT-D2**: SessionLogger has independent `_write_lock` and its own file rotation (100MB / 10 files). It does NOT use `append_jsonl_record`.

**FACT-D3**: Telemetry DB writes (`save_llm_call`, `save_stage_attempt`, `save_ui_event`, `save_cost_record`) catch ALL exceptions and log at **DEBUG level only**. They also check `accepts_runtime_telemetry_writes` guard and return early if False.

**FACT-D4**: `commit_episode_factory()` is the only write path with explicit `begin()`/`commit()`/`rollback()` transaction control. All other writes use nested-awareness or auto-commit.

**FACT-D5**: Proof digest (audit_service.py:202-262) checks 10+ artifact existence conditions and cross-validates DB ↔ JSONL ↔ file artifacts.

**FACT-D6**: `FailureAnalyzer.sink_alignment_summary()` is scoped to Stage 3 & 4 only (audit_service.py:241).

**FACT-D7**: `quality_metrics.jsonl` and `pass_rate_monitor.json` have **no rotation** mechanism. Both can grow unbounded over long production runs.

**FACT-D8**: `logging_keys.py` provides deterministic cross-sink keys via `build_attempt_key()` and `resolve_logging_session_id()`.

**FACT-G1**: No file in `tools2/` is imported by `modules/`, `main_a.py`, or any runtime code. Only `tests/test_tools2_cost_tables.py` references `tools2/` via `runpy.run_path()`.

**FACT-G2**: 4 scripts have **hardcoded user-specific paths** (`C:\Users\wjjo\`): `fix_costs.py`, `fix_costs2.py`, `render_later_hardening_autopilot.py`, `tf_c1_patch.py`. These will fail on any other user account.

**FACT-G3**: `md2pdf.py` has a **Windows-only** hardcoded font path: `C:\Windows\Fonts\malgun.ttf`.

**FACT-G4**: 6 scripts perform direct SQLite mutation without the DBManager API: `backfill_quality_sidecars.py`, `make_BP.py`, `normalize_arcs_db.py`, `db_porter.py`, `blueprint_name_fixer.py`, `blueprint_editor.py`.

**FACT-G5**: `sync_temp_queue_state.py` overwrites `docs/temp/queue-state.json` — an execution state artifact.

**FACT-G6**: Canary runners (`run_stage34_canary.py`, `run_stage4_canary.py`) create/reset projects and perform full pipeline writes. These are the highest-risk standalone scripts.

---

## 8. Inferences

**INF-D1**: The DEBUG-only logging for telemetry writes (FACT-D3) means that DB write failures for `llm_calls`, `stage_attempts`, `ui_events`, `cost_log` are **invisible in normal production logs**. Operators would need DEBUG-level logging enabled to detect data loss. This is likely intentional (non-blocking telemetry), but creates a silent data loss surface for analytics/audit.

**INF-D2**: The absence of rotation on `quality_metrics.jsonl` and `pass_rate_monitor.json` (FACT-D7) implies a long-running project (250+ episodes) could accumulate substantial file sizes. `quality_metrics.jsonl` is append-only; `pass_rate_monitor.json` is overwrite-with-1000-records so it's bounded.
- **Correction**: Only `quality_metrics.jsonl` has an unbounded growth concern. `pass_rate_monitor.json` is self-bounded at 1000 records.

**INF-D3**: `FailureAnalyzer.sink_alignment_summary()` being scoped to Stage 3 & 4 only (FACT-D6) means Stage 2 sink alignment is not verified by the proof digest. Stage 2 has its own substantial write paths (arc ensembles, blueprint planning) that aren't covered.

**INF-D4**: The `_JSONL_APPEND_LOCK` in `jsonl_io.py` is process-wide but **not cross-process safe**. If multiple processes write to the same JSONL file concurrently (e.g., bridge_server + main_a subprocess), interleaving is possible. The bridge_server runs in a separate process from the main pipeline, but writes to different files (`control-plane-provenance.jsonl` vs. `episode_production.jsonl`), so this may be a theoretical concern only.

**INF-G1**: The 6 scripts that bypass DBManager for direct SQLite mutations (FACT-G4) bypass all safety features: WAL mode awareness, lock acquisition, nested transaction tracking, column validation, and the telemetry write guard. They could cause schema drift if they add/alter columns not known to DBManager.

**INF-G2**: The `tools2/` test prototypes (`test_continuity_validator.py`, `test_phase3_systems.py`, etc.) appear to be older standalone test suites predating the main `tests/` directory. They import from `modules/` but are not part of the CI/regression harness.

---

## 9. Uncertainty / Contradictions

**UNC-D1**: **Rotation gap for quality_metrics.jsonl**: SessionLogger has 100MB/10-file rotation. QualityDashboard writes to `quality_metrics.jsonl` with **no rotation observed in code**. It loads all records on init and trims to 500 in memory, but the file on disk grows unbounded. Uncertain whether this has been a problem in practice.
- **Stale risk**: Low (file unlikely to exceed tens of MB for typical projects).

**UNC-D2**: **Cross-process JSONL safety**: `jsonl_io.py` uses `threading.Lock` (process-local). The bridge_server runs as a separate process (FastAPI/Uvicorn). The main pipeline runs as a subprocess from ProcessRunner. If both append to the same JSONL file, lines could interleave. Current sink separation (different files per process) may prevent this in practice, but the contract is not explicit.

**UNC-D3**: **`risk-approval-log.jsonl` authority status**: This sink is written by RiskApprovalGate in bridge_server.py and tested in `test_control_plane_approval_provenance_ssot.py`. However, it is NOT listed in `CONTROL_PLANE_AUTHORITY_CONTRACT["authoritative_sinks"]` in `control_plane_contract.py`. It's unclear whether this is an intentional companion snapshot or an omission from the authority contract.

**UNC-D4**: **SessionLogger disabled-by-default**: SessionLogger starts with `enabled=False` and must be activated per-project via `set_log_dir()`. If a code path writes before activation, the write is silently dropped. Uncertain whether any early-boot write paths exist before project selection activates the logger.

**UNC-G1**: **`validate_manual_sweep.py` purpose unknown**: Not enough content was surveyed to determine its full behavior. Filename suggests manual QA validation but details are uncertain.

**UNC-G2**: **`rlhf_interface.py` status unknown**: Likely a Streamlit prototype for RLHF feedback, but details not fully surveyed.

**UNC-G3**: **scripts/ `ops_support.py` role**: Listed as a library module but its exact exports and consumers were not fully traced.

---

## 10. Candidate Watchlist

### High Priority

| ID | Item | Reason | Severity Estimate |
|----|------|--------|------------------|
| W-D1 | Telemetry writes log at DEBUG only | FACT-D3: Silent data loss for `llm_calls`, `stage_attempts`, `ui_events`, `cost_log` invisible in production logs | Medium (intentional design, but analytics gap) |
| W-D2 | Stage 2 sink alignment not in proof digest | FACT-D6 / INF-D3: Stage 2 write paths uncovered by proof verification | Medium |
| W-D3 | `risk-approval-log.jsonl` not in authority contract | UNC-D3: Possible authority gap | Low-Medium |
| W-G1 | 4 scripts with hardcoded `C:\Users\wjjo\` paths | FACT-G2: `fix_costs.py`, `fix_costs2.py`, `render_later_hardening_autopilot.py`, `tf_c1_patch.py` | Low (one-off scripts, not runtime) |
| W-G2 | 6 scripts bypass DBManager for direct SQLite | FACT-G4 / INF-G1: No transaction safety, no column validation | Medium (mutation risk if used on production DB) |

### Medium Priority

| ID | Item | Reason |
|----|------|--------|
| W-D4 | `quality_metrics.jsonl` no rotation | UNC-D1: Unbounded file growth on long projects |
| W-D5 | Cross-process JSONL interleave theoretical risk | UNC-D2 / INF-D4 |
| W-G3 | `md2pdf.py` Windows-only font path | FACT-G3 |
| W-G4 | Canary runners create/reset projects | FACT-G6: Data loss if target project exists |

### Low Priority / Stale-Possible

| ID | Item | Reason |
|----|------|--------|
| W-G5 | `tools2/` test prototypes not in CI | INF-G2: May have drifted from current module APIs |
| W-G6 | `validate_manual_sweep.py` purpose unknown | UNC-G1 |

---

## 11. TF Evidence Notes

### TF-Tagged Patterns Found in Tests

| Tag | Location | What It Tests | Live Code Status |
|-----|----------|---------------|-----------------|
| TF-C07 | `test_fact_ledger.py:73-114` | Numerical facts auto-extraction from `status_shadow`, `financial_events` | Live: `fact_ledger.py` still has this logic |
| P0-2 | `test_fact_ledger.py:197-214` | `established_value` permanence across FIFO trim | Live: fact_ledger preserves this contract |
| TF-30-7 | `session_logger.py` (comment) | Multithreaded JSONL interleave prevention via Lock | Live: `_write_lock` present |
| TF-28 | `session_logger.py` (comment) | LLM thinking content non-empty tracking | Live: thinking content field exists |
| TF-26 | `studio_visualizer.py` (comment) | Dual console + file logger output | Live: both paths active |

### TF-Relevant Test Contract Summary

| Test File | Sink Contract Tested | Mock Strategy | Actual File Writes Verified |
|-----------|---------------------|---------------|---------------------------|
| `test_audit_service.py` | runtime_audit.jsonl, runtime_audit_summary.json, proof_digest | MagicMock + explicit fixture files | Yes (`.exists()`, `.read_text()`) |
| `test_fact_ledger.py` | DB anchor load/save via StubDB | `_StubDB`, `_BrokenSaveDB`, `_BrokenLoadDB` | No (all in-memory) |
| `test_quality_regression.py` | quality_metrics.jsonl, soft_failures.jsonl | `patch("...open", side_effect=OSError)` | Yes (soft_failures.jsonl verified) |
| `test_pass_rate_monitor_rol.py` | pass_rate_monitor.json | Real PassRateMonitor + tmp_path | Yes (file persistence) |
| `test_db_manager.py` | 30+ DB tables, transaction rollback | Real DBManager + tmp_path DB | Yes (real SQLite) |
| `test_artifact_logging.py` | logs/artifacts/ snapshots, content hash | SimpleNamespace project mock | Yes (file + hash verified) |
| `test_session_logger.py` | session/*.jsonl, rotation, truncation | Real SessionLogger + tmp_path | Yes (JSONL creation verified) |
| `test_control_plane_approval_provenance_ssot.py` | control-plane-provenance.jsonl, risk-approval-log.jsonl | App test client | Yes (JSONL verified) |
| `test_runtime_authority_contract.py` | RUNTIME_AUTHORITY_CONTRACT, CONTROL_PLANE_AUTHORITY_CONTRACT | Direct import assertions | N/A (contract validation) |

### TF Contradiction Check

No contradictions found between TF-tagged test expectations and live code. All tested contracts appear to match current implementation:
- `established_value` permanence (P0-2): Live
- Numerical extraction from `status_shadow`/`financial_events` (TF-C07): Live
- Thread-safe JSONL writes (TF-30-7): Live
- Authoritative sink list in tests matches `CONTROL_PLANE_AUTHORITY_CONTRACT`: **Partial match** — `risk-approval-log.jsonl` tested but not in contract (see UNC-D3)

---

*End of draft. This document is collector output only. It does not authorize execution, patches, policy verdicts, or severity declarations.*
