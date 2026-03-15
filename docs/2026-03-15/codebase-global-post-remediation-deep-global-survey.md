# Post-Remediation Deep Global Survey

| Field | Value |
|-------|-------|
| **Baseline** | `bbb00a77` (2026-03-15) |
| **Predecessor** | cleanroom-source-only (96/100), log-evidence-merged (98/100) |
| **Scope** | main_a.py, modules/ (244), tests/ (315), scripts/ (34), config/ (47), geuldobi-desktop/src/, UI/ |
| **Exclusions** | .git, __pycache__, node_modules, venv, logs/pytest_lowmem, python-embed/ |
| **Method** | Hybrid — predecessor authority + full re-scan across 8 tranches |
| **Confidence** | **96/100** |

---

## Tranche A — Macro Topology

### Codebase Metrics

| Area | Files (.py) | LOC | Notes |
|------|-------------|-----|-------|
| modules/core/ | 159 | 80,860 | Genre guards 7.5K, services 1.5K, stage0 5.3K |
| modules/domain/ | 48 | 38,880 | Agents: Director 7, ChiefWriter 4, State 4, Continuity 4 |
| modules/validation/ | 17 | 8,486 | Advisory systems, quality gates |
| modules/api/ | 8 | 3,233 | REST endpoints, bridge server, prompt broker |
| modules/models/ | 5 | 478 | Data models |
| modules/protocols/ | 5 | 688 | Protocol definitions |
| **modules/ total** | **244** | **138,260** | |
| tests/ | 315 | 77,833 | Test:module ratio 1.29:1 |
| scripts/ | 34 | 13,762 | Pipelines, smoke, validation, ops |
| root .py | 8 | 6,088 | main_a.py (4,699) + 7 utilities |

### New Surface: modules/core/services/ (Phase 4B)

| File | LOC | Interface |
|------|-----|-----------|
| audit_service.py | 303 | Buffered audit + proof digest + session lineage |
| state_service.py | 373 | 15 public methods: validation, NPC profiles, pattern |
| project_service.py | 619 | 24+ methods: rollback, rewind, restore ops |
| ui_service.py | 222 | 11 methods: bible/treatment selection, input |
| __init__.py | 5 | Re-exports |

### Config Inventory (47 files)

| Category | Count | Location |
|----------|-------|----------|
| Genre configs | 10 | config/genres/*.yaml |
| Prompt configs | 17 | config/prompts/*.yaml + .json |
| System configs | 3 | config/models.yaml, system.yaml, settings.json |
| Validation | 1 | config/settings/validation.yaml (14KB, 35+ items) |
| Settings | 2 | config/settings/item_suffixes.yaml |
| Terms | 2 | config/terms/*.json |
| Style | 3 | config/smart_retrieval/, style_references/, tone_presets |
| Laws/Seeds | 21 | modules/core/laws/*.json |
| **Total** | **47+21** | |

### Desktop (geuldobi-desktop/src/)

| File | Purpose |
|------|---------|
| main.js | Electron entry, IPC, splash lifecycle |
| preload.js | IPC bridge (runKey, stopRun, getBackendUrl) |
| index.html | Main UI shell |
| console_relay.js | Console bridge |
| desktop_control_plane_contract.js | Contract schema |
| splash/ (3 files) | Splash polling, CSS, HTML |

---

## Tranche B — Runtime Core (Lane 1 Verification)

### Implementation Status: FULLY COMPLETE

| File | Lines | Lane 1 Feature | Status |
|------|-------|----------------|--------|
| db_manager.py | 3,743 | begin_shutdown(), telemetry gating (4 methods), rationale update | ✓ Complete |
| artifact_logging.py | 147 | persisted_bytes hash, SHA256 on UTF-8 disk bytes | ✓ Complete |
| session_logger.py | 355 | begin_shutdown(), _enabled guard on all 4 log methods | ✓ Complete |
| stage4_interview_round.py | 5,037 | 2 rationale sync points (L2138, L2297), non-blocking | ✓ Complete |
| audit_service.py | 303 | Session lineage reconciliation, quiescent-point proof digest | ✓ Complete |
| main_a.py | 4,699 | 6-phase shutdown: metrics→cost→advisory→trackers→state→freeze→audit→close | ✓ Complete |

### Telemetry Gating Detail (db_manager.py)

- `_accept_runtime_telemetry_writes` flag (L66), initially True
- `begin_shutdown()` (L1118-1121) sets flag False
- Dual-check pattern (before lock + after lock) on:
  - `save_director_selection()` (L2768+)
  - `insert_llm_call()` (L3161+)
  - `save_stage_attempt()` (L3284+)
  - `save_ui_event()` (L3367+)

### Shutdown Sequence (main_a.py)

```
_shutdown_app()
├── _persist_shutdown_metrics()         # ThreadPoolExecutor, 5s timeout
├── _persist_shutdown_cost_scope()      # Session cost JSON
├── _persist_shutdown_advisory_state()  # pass_rate_monitor.json
├── _persist_shutdown_trackers()        # learner/voice/foreshadow/emotion
├── _persist_shutdown_project_state()   # bible/genre_info
├── session_logger.begin_shutdown()     # Freeze JSONL
├── db.begin_shutdown()                 # Freeze DB telemetry
├── _write_audit_summary("shutdown_final")  # Proof digest
└── _close_shutdown_resources()         # DB close, VecMemory disconnect
```

---

## Tranche C — Cross-Cut Architecture

### DI Context Chains

| Context | __slots__ | Breakdown |
|---------|-----------|-----------|
| Stage2Context | 47 | 5 required + 1 world_state + 18 extended + 21 callbacks + 1 sync + 1 session_logger |
| Stage3Context | 19 | 2 required + 11 properties + 10 callbacks + 1 session_logger |
| Stage4Context | 26 | 5 required + 14 extended + 1 conditional_modules dict + 7 callbacks + 2 meta |

### Callback Wiring Patterns

| Context | Pattern | Safety |
|---------|---------|--------|
| Stage2 | Weakref-based sync via `_make_sync_callback()` | GC-safe |
| Stage3 | Direct getattr assignment | Simple |
| Stage4 | Property-backed via `_stage4_context_budget_meta` dict | Lazy resolution |

### Guard Chain

```
GenreGuard (10 genre classes) → WorkGuard (YAML overlay) → StyleGuard (style validation)
```

13 total guard classes: 1 base + 10 genre + WorkGuard + StyleGuard

### Service Boundaries

| Service | LOC | Methods | Pattern |
|---------|-----|---------|---------|
| AuditService | 303 | 7+ | Buffered audit + proof digest |
| StateService | 373 | 15 | Validation + pattern helper |
| ProjectService | 619 | 24+ | Destructive ops + restore |
| UIService | 222 | 11 | UI abstraction + logging |

---

## Tranche D — Operational Infrastructure

### DB Transaction Safety

| Mechanism | Detail |
|-----------|--------|
| Lock | `threading.RLock()` wraps all 40+ methods |
| WAL mode | `PRAGMA journal_mode=WAL`, `synchronous=NORMAL` |
| Timeout | 30s per connection |
| Nested tx | `conn.in_transaction` checks prevent double-BEGIN |
| Rollback | On error or close during active transaction |
| Connection | Single shared, `check_same_thread=False` |

### JSONL Sinks (11 distinct files)

| Sink | Writer | Purpose |
|------|--------|---------|
| session_*.jsonl (4 categories) | session_logger.py | llm_io, decisions, state_changes, ui_events |
| runtime_audit.jsonl | audit_service.py | Audit events |
| episode_production.jsonl | stage4_*.py | Episode results |
| quality_metrics.jsonl | data_collector.py | Quality signals |
| failure_analysis.jsonl | failure_analyzer.py | Failure classification |
| quality_dashboard.jsonl | quality_dashboard.py | Dashboard metrics |
| soft_failures.jsonl | soft_failure.py | Recoverable failures |
| canary_*.jsonl | canary tools | Canary results/metrics |

### Thread Safety

- `jsonl_io.py`: Global `_JSONL_APPEND_LOCK` for atomic appends
- `session_logger.py`: `_write_lock` for per-instance multithread protection
- `db_manager.py`: `_lock` RLock for all DB operations

---

## Tranche E — Side-Effects

### File Write Points

| Category | Count | Key Locations |
|----------|-------|---------------|
| `open(..., 'w')` | 10 files | Orchestrators, metrics, failure, preflight |
| `.write_text()` | 8 files | Style, analysis, post-process, project, logs |
| JSONL append | 11 sinks | See Tranche D table |
| DB writes | 29+ ops | 17 INSERT/UPSERT + 12 UPDATE (db_manager.py) |

### Console Output

- 130 `print()` calls across 30 files
- Primary: spinners/progress (stage0/spinner.py: 48 calls)
- Secondary: debug/status (orchestrators, director)
- No production logging via print()

### Audit Trail

- In-memory buffer capped at 1,000 items (rolls to 500)
- JSONL sink: runtime_audit.jsonl, append-only, UTF-8
- 5 authoritative attempt sinks: stage_attempts, pass_rate_monitor, session_decisions, episode_production, director_selections

---

## Tranche F — Test Coverage

### Mapping

| Area | Module Files | Test Files | Ratio |
|------|-------------|------------|-------|
| modules/ | 244 | 315 | 1.29:1 |
| Lane 1 additions | 4 | 4 | 1:1 |

### Lane 1 Test Coverage

| Test File | Lines | Tests | Coverage |
|-----------|-------|-------|----------|
| test_audit_service.py | 451 | 8+ | proof_digest, quiescent-point, facade stub |
| test_session_logger.py | 390 | 14 | enabled/disabled, rotation, health, thinking |
| test_artifact_logging.py | 88 | 8 | hash computation, write failure softness |
| test_db_manager.py | existing | +new | Telemetry gating assertions added |

### Test Suite Status

- **2,114 passed + 68 xfailed** (Opus TF audit baseline)
- Property-based testing via hypothesis
- Chaos testing in tests/chaos/
- E2E integration in tests/e2e/

---

## Tranche G — Dependencies

### External APIs

| API | Module | Pattern |
|-----|--------|---------|
| Gemini | google.genai (SDK) | models_config.py routing |
| Slack | requests.post (webhook) | slack_bot.py, 10s timeout |

### Circular Dependency Guards

- 6 files use `if TYPE_CHECKING:` blocks
- No bare circular imports found
- Sub-modules use lazy loading patterns

### Key Dependencies (requirements.txt)

- google-genai ≥1.60.0 (LLM provider)
- sqlite-vec ≥0.1.6 (vector DB)
- fastapi ≥0.111.0 + uvicorn (API server)
- pytest ≥8.0 + hypothesis ≥6.0 (testing)

---

## Tranche H — Risk (Contradictions + Uncertainties)

### Contradictions (7 items)

| ID | Item | Status | Evidence |
|----|------|--------|----------|
| C-01 | Mojibake vs hygiene FP | ✅ RESOLVED | d2982aa2+bbb00a77 UTF-8 pipeline, 3 test suites |
| C-02 | Prompt authority split | ✅ RESOLVED | UIService extraction, 0 bare input() in main_a.py |
| C-05 | Backend-front readiness | ◐ PARTIALLY | Contract defined, runtime proof deferred |
| C-06 | Prompt lifecycle concurrency | ✅ RESOLVED | PromptBroker state machine, explicit policy |
| Log C-02 | Proof-digest timing | ✅ RESOLVED | Quiescent-point hook, committed_persistence_only |
| Log C-05 | Session identity | ✅ RESOLVED | Dual lineage tracking (plain + structured) |
| Log C-07/08 | Artifact hash + teardown | ✅ RESOLVED | SHA256 on persisted bytes, multi-phase shutdown |

### Uncertainties (9 items)

| ID | Item | Status | Detail |
|----|------|--------|--------|
| U-01 | Desktop test depth | OPEN | 0 test files in geuldobi-desktop/ |
| U-02 | Lane 1 test depth | ✅ RESOLVED | 929 lines across 3 dedicated test files |
| U-03 | Desktop reconnect | BOUNDED | 1s polling, 30s timeout, no backoff |
| U-04 | Splash timeout | ✅ RESOLVED | 8s hardcoded + 5s per-fetch abort |
| U-05 | UI service completeness | ✅ RESOLVED | 223 LOC, no TODO markers |
| U-06 | Command/WS separation | ✅ RESOLVED | HTTP POST commands, WS events |
| Log U-01 | Desktop log consumption | BOUNDED | Desktop uses /events WS, not log files |
| Log U-02 | Late-write chain | ✅ RESOLVED | begin_shutdown() before all DB writes |
| Log U-05 | Hash capture timing | ✅ RESOLVED | Hash on serialized payload pre-write |

---

## Ruff Violations

| Rule | Count | Auto-fix | Description |
|------|-------|----------|-------------|
| I001 | 20 | ✓ | Unsorted imports |
| E402 | 9 | ✗ | Module import not at top |
| UP045 | 9 | ✓ | Non-PEP604 Optional annotation |
| UP006 | 8 | ✓ | Non-PEP585 annotation |
| UP035 | 8 | - | Deprecated import |
| UP017 | 5 | ✓ | datetime.timezone.utc |
| F401 | 4 | ✓ | Unused import |
| UP037 | 2 | ✓ | Quoted annotation |
| UP041 | 1 | ✓ | Timeout error alias |
| **Total** | **66** | **52 fixable** | Down from 186 (64% reduction) |

---

## Confidence Score

| Dimension | Max | Score | Justification |
|-----------|-----|-------|---------------|
| Scope/path completeness | 20 | 20 | 8 tranches scanned, all paths verified |
| View completeness (8 tranches) | 15 | 15 | A-H all covered with evidence |
| Side-effects/durability | 15 | 14 | 11 JSONL sinks mapped, 29+ DB ops, -1 for desktop gap |
| Evidence triangulation | 15 | 14 | Code + tests + execution evidence for Lane 1; desktop limited |
| Contradiction closure | 10 | 9 | 6/7 resolved, C-05 partially (no desktop runtime proof) |
| Uncertainty ledger | 10 | 9 | 6/9 resolved, 2 bounded, 1 open (desktop tests) |
| SSOT/roadmap alignment | 10 | 10 | All existing SSOTs cross-referenced |
| Verification artifacts | 5 | 5 | projects/000/ + bounded_persistence execution evidence |
| **Total** | **100** | **96** | |
