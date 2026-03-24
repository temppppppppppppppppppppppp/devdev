Date: 2026-03-24
Document Type: T5 evidence manifest
Parent Report: `docs/2026-03-24/opus/rol-llm-friendly-t5-persistence-observability.md`

## File Inventory

### Primary Scope Files (fully read)

| File | Lines | Role |
|---|---|---|
| `modules/core/db_manager.py` | 3,432 | DB persistence owner, 136+ methods |
| `modules/core/pass_rate_monitor.py` | 881 | Attempt tracking, JSON cache sink |
| `modules/core/logger.py` | 353 | File-only session logging |
| `modules/core/metrics_collector.py` | 537 | API cost/performance metrics |
| `modules/core/session_logger.py` | 355 | 4-category JSONL telemetry |
| `modules/core/services/audit_service.py` | 317 | Runtime audit buffer + proof digest |
| `modules/core/jsonl_io.py` | 21 | Synchronized JSONL append utility |
| `modules/core/logging_keys.py` | 54 | Deterministic cross-sink key builders |
| `modules/core/artifact_logging.py` | 147 | Artifact snapshot + content hash |
| `modules/core/stage4_episode_logging.py` | 176 | Stage 4 PASS episode log payload builder |
| `modules/core/quality_signal_metrics.py` | 244 | Python-only quality signal computation |
| `modules/core/soft_failure.py` | partial | Non-blocking failure reporting |

### Cross-Referenced Files (sink write paths)

| File | Lines Read | Context |
|---|---|---|
| `modules/core/stage3_orchestrator.py` | L2475-2730 | Stage 3 REJECT sink writes (per-sink try/except verified) |
| `modules/core/stage4_outcome_runtime.py` | L400-490 | `episode_production.jsonl` writer #2 |
| `modules/core/stage4_interview_round.py` | L5527 ref | `episode_production.jsonl` writer #1 |
| `modules/core/stage4_orchestrator.py` | L1970-2003 ref | `episode_production.jsonl` writer #3 (escalation) |
| `modules/core/quality_dashboard.py` | L1-80 | `quality_metrics.jsonl` consumer |
| `modules/core/quality_sidecar_bootstrap.py` | ref only | `quality_metrics.jsonl` writer |
| `modules/core/failure_analyzer.py` | ref only | `episode_production.jsonl` reader + sink alignment checker |
| `modules/core/stage2_finalizer.py` | L1-80 | Stage 2 sink write helpers |
| `modules/core/services/ui_service.py` | L1-100 | Console output helper service |
| `modules/core/stage4_context.py` | L240-244 ref | `write_audit_summary` callback |
| `modules/core/stagewise_manuscript_truth_report.py` | L1-80 | Manuscript truth report builder |

## Key Line Anchors

### db_manager.py Sink Methods
- `__init__` + lifecycle: L81-100
- Method-Group ToC: L61-78
- `begin_shutdown()`: L452-455
- `accepts_runtime_telemetry_writes`: L457-459
- `save_manuscript()`: L501
- `save_episode_bible()`: L601
- `save_blueprint()`: L1294
- `save_state_log()`: L1315
- `commit_episode_factory()`: L1604
- `save_director_selection()`: L2152
- `save_episode_quality_label()`: L2252
- `save_episode_quality_signal()`: L2289
- `save_episode_quality_observation()`: L2334
- `save_llm_call()`: L2804
- `save_stage_attempt()`: L2878
- `save_attempt_raw_rationale()`: L2983
- `save_ui_event()`: L3034
- `save_cost_record()`: L3178
- `save_satisfaction_tag()`: L3298
- `save_pacing_record()`: L3369

### Session JSONL Categories
- `session_logger.py` L39: `_CATEGORIES = ("llm_io", "decisions", "state_changes", "ui_events")`
- `session_logger.py` L49: `enabled=False` default
- `session_logger.py` L55: `_write_lock = threading.Lock()`

### episode_production.jsonl Writers
- `stage4_interview_round.py` L5527: PASS production events
- `stage4_outcome_runtime.py` L425: CoVe runtime advisory events
- `stage4_outcome_runtime.py` L883: REJECT production events
- `stage4_orchestrator.py` L2003: Escalation events

### Stage 3 Per-Sink Try/Except Pattern
- Prep block: L2515-2569 (single try/except, justified — no data to write on prep failure)
- Session logger sink: L2573-2592 (individual try/except)
- Pass-rate monitor sink: L2601-2626 (individual try/except)
- DB save_stage_attempt: L2632-2662 (individual try/except)
- DB save_director_selection: L2663-2667 (individual try/except)
- Summary log: L2669-2687 (individual try/except)

### Shutdown Gates
- `db_manager.py` L452-459: `begin_shutdown()` + `accepts_runtime_telemetry_writes`
- `session_logger.py` L70-71: `begin_shutdown()` → `_enabled = False`
- `metrics_collector.py` L492-508: `snapshot_and_reset_scope()` for final metric capture

## Grep Evidence

### episode_production.jsonl write locations
```
modules/core/stage4_interview_round.py:5527
modules/core/stage4_outcome_runtime.py:425
modules/core/stage4_outcome_runtime.py:883
modules/core/stage4_orchestrator.py:2003
```

### DB telemetry sink methods using shared cursor under lock
```
db_manager.py:2841  save_llm_call → self.cursor.execute(...)
db_manager.py:2927  save_stage_attempt → self.cursor.execute(...)
db_manager.py:3069  save_ui_event → self.cursor.execute(...)
db_manager.py:3200  save_cost_record → self.cursor.execute(...)
```

### accepts_runtime_telemetry_writes guard pattern
```
db_manager.py:2830  save_llm_call — outer check
db_manager.py:2839  save_llm_call — inner check (under lock)
db_manager.py:2914  save_stage_attempt — outer check
db_manager.py:2924  save_stage_attempt — inner check (under lock)
db_manager.py:3059  save_ui_event — outer check
db_manager.py:3066  save_ui_event — inner check (under lock)
```
