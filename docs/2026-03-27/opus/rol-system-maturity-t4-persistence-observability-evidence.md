Date: 2026-03-27
Type: evidence manifest
Lane: T4 — Persistence / Observability / Side-Effect Integrity
Parent Report: `docs/2026-03-27/opus/rol-system-maturity-t4-persistence-observability.md`

## File Inventory

| File | Lines | Inspected Sections |
|---|---|---|
| `modules/core/db_manager.py` | 3,446 | L1-200 (init/lifecycle/helpers), L200-400 (integrity/migration), L2800-2900 (telemetry sinks) |
| `modules/api/bridge_server.py` | 2,372 | L1-100 (imports/constants/authority helpers) |
| `modules/core/quality_dashboard.py` | 1,271 | L1-200 (init/record/process) |
| `modules/core/session_logger.py` | 391 | L1-200 (docstring/init/API/log methods) |
| `modules/core/logger.py` | 352 | L1-200 (init/handlers/methods) |
| `modules/core/metrics_collector.py` | 588 | L1-300 (dataclasses/costs/identity/init/start_call/end_call) |
| `modules/core/pass_rate_monitor.py` | 889 | L1-200 (dataclasses/init/load/save/record) |
| `modules/core/soft_failure.py` | 175 | Full file |
| `modules/core/artifact_logging.py` | 146 | Full file |
| `modules/core/jsonl_io.py` | 20 | Full file |
| `modules/core/stage4_episode_logging.py` | 175 | Full file |

## Authority Classification Anchors

| File | Line Range | Classification | Quote Excerpt |
|---|---|---|---|
| `db_manager.py` | L2804-2816 | Non-authoritative telemetry | "NOT authoritative truth for verdict adjudication" |
| `session_logger.py` | L12-18 | Optional best-effort telemetry | "If JSONL files are lost, no durable pipeline truth is lost" |
| `pass_rate_monitor.py` | L16-22 | Non-authoritative convenience cache | "rebuilt from in-memory records on each save cycle" |

## Thread Safety Anchors

| File | Mechanism | Line |
|---|---|---|
| `db_manager.py` | `threading.RLock` (`self._lock`) | L87 |
| `session_logger.py` | `threading.Lock` (`self._write_lock`) | L64 |
| `jsonl_io.py` | `threading.Lock` (`_JSONL_APPEND_LOCK`) | L10 |
| `metrics_collector.py` | `threading.RLock` (`self._lock`) | L213 |
| `pass_rate_monitor.py` | `threading.Lock` (`self._lock`) | L134 |
| `soft_failure.py` | `threading.Lock` (`_WARN_LOCK`) | L14 |
| `quality_dashboard.py` | **None** | (missing) |

## Integrity Recovery Anchors

| Mechanism | File:Line | Description |
|---|---|---|
| PRAGMA integrity_check | `db_manager.py:231` | Runs on every connection |
| Corrupt DB quarantine | `db_manager.py:202-219` | Renames to `.corrupt_*` |
| Auto-recovery | `db_manager.py:236-247` | Creates fresh DB after quarantine |
| Schema migration | `db_manager.py:148-185` | `_ensure_columns_exist` via ALTER TABLE |

## Artifact Linkage Anchors

| Component | File:Line | Role |
|---|---|---|
| `build_candidate_key` | `artifact_logging.py:15-20` | Deterministic key from label+strategy |
| `snapshot_logged_artifact` | `artifact_logging.py:40-89` | Write + SHA-256 hash + path |
| `normalize_artifact_meta` | `artifact_logging.py:23-37` | Normalize triple |
| DB storage | `db_manager.py` save_director_selection | Stores triple in DB row |

## Runtime Evidence Cross-Reference

| Source | Date | Key Metric | Supports |
|---|---|---|---|
| `fresh-run-3pass-audit-report.md` | 2026-03-23 | 213 LLM calls, 100% success, 0 P0 | late-stabilization |
| `chaebol-ent-empire-revival-canary-report.md` | 2026-03-27 | Pair consumability pass, DB integrity pass | late-stabilization |
| `chaebol-ent-empire-revival-stage-probe-report.md` | 2026-03-27 | Runtime admission pass, Stage 0/2/3 probe pass | late-stabilization |
| `current-state-situation-survey-report.md` | 2026-03-23 | Risk #5: DB truncation confirmed | optimization gap (may be resolved) |
| `docs/temp/queue-state.json` | 2026-03-27 | `active_item_count: 0` | queue clean |
