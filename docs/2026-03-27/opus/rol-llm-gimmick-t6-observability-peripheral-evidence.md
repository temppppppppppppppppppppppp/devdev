Date: 2026-03-27
Type: evidence manifest (T6 lane)
Parent Report: `docs/2026-03-27/opus/rol-llm-gimmick-t6-observability-peripheral.md`

## Observability Module Inventory

| Module | Lines | Gimmick Count | Elegant | Inelegant | Mixed |
|---|---|---|---|---|---|
| `modules/core/db_manager.py` | 3,446 | 2 | 2 | 0 | 0 |
| `modules/core/pass_rate_monitor.py` | ~300 | 1 | 1 | 0 | 0 |
| `modules/core/logger.py` | 353 | 3 | 2 | 1 | 0 |
| `modules/core/metrics_collector.py` | 581 | 5 | 3 | 1 | 1 |
| `modules/core/session_logger.py` | 392 | 2 | 2 | 0 | 0 |

## Gimmick Anchor List

| Gimmick | File:Line | Verdict |
|---|---|---|
| DB Method-Group ToC | `db_manager.py:61-78` | elegant |
| Cumulative bible cache | `db_manager.py:89-90` | elegant |
| Non-authoritative declaration | `pass_rate_monitor.py:16-22` | elegant |
| Emoji-to-log-level | `logger.py:166-173` | inelegant |
| Root logger cleanup | `logger.py:92-97` | elegant |
| Log file retarget | `logger.py:216-243` | elegant |
| Provider identity inference | `metrics_collector.py:97-110` | inelegant |
| Inline MODEL_COSTS | `metrics_collector.py:80-94` | mixed |
| Vertex billing normalization | `metrics_collector.py:113-119` | elegant |
| Scope accumulator | `metrics_collector.py:195-201` | elegant |
| Stale metric cleanup | `metrics_collector.py:222-227` | elegant |
| JSONL opt-in + rotation | `session_logger.py:40,287-358` | elegant |
| Soft failure tracking | `session_logger.py:361-392` | elegant |

## Peripheral Directory Inventory

| Directory | File Count | Total Size | Has README | Code Files | Stale Artifacts |
|---|---|---|---|---|---|
| `scripts/` | 50+ | ~530KB code | yes | 49 .py + 1 .ps1 | 0 |
| `tests/` | 378 | ~108K LOC | yes | 378 .py | ~8 stale JSON/log |
| `UI/` | ~20 | ~337MB | yes | 0 | 0 |
| `geuldobi-desktop/` | ~30 src | ~210KB code | yes (DESKTOP-GUIDE) | 10 .js + .html | 0 |
| `docs/implementation/` | 47 | ~120KB | N/A (self-governing) | 0 (stale .py deleted) | 0 |

## Prior T6 Hotspot Resolution Status

| Prior ID | Description | Status |
|---|---|---|
| H1 | `docs/implementation/prompt_broker.py` | **RESOLVED** (deleted) |
| H2 | `docs/implementation/input_route.py` | **RESOLVED** (deleted) |
| H3 | `scripts/` no README | **RESOLVED** (README added) |
| H4 | `tests/` no README | **RESOLVED** (README added) |
| H5 | `UI/` name confusion | **RESOLVED** (README added) |
| H6 | `scripts/tf_c1_patch.py` | **RESOLVED** (deleted) |
| H7 | temp Electron files | **RESOLVED** (deleted) |
| H8 | stale test artifacts | **UNRESOLVED** (still present) |
| H9 | `risk-approval-checklist.md` metadata | **UNRESOLVED** |
| H10 | `release-gate-v1.md` metadata | **UNRESOLVED** |

## Dirty/Untracked Files in T6 Scope

| File | Status | Assessment |
|---|---|---|
| `modules/core/metrics_collector.py` | dirty (tracked) | Multi-provider cost/provider additions. Survey-only; not modified by this lane. |
| `tests/test_blocking_validator_submodules.py` | dirty (tracked) | Test updates. Not a T6 concern. |
| `tests/test_llm_router.py` | dirty (tracked) | Router test updates. Not a T6 concern. |
| `tests/test_stage3_orchestrator.py` | dirty (tracked) | Stage 3 test updates. Not a T6 concern. |
| `tests/test_stage4_context_builder.py` | dirty (tracked) | Context builder test updates. Not a T6 concern. |
| `scripts/probe_claude_vertex_matrix.py` | untracked | Exploratory probe script. No authority issue. |
| `tests/test_probe_claude_vertex_matrix.py` | untracked | Test for probe script. No authority issue. |
