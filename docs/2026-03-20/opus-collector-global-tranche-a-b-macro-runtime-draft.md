# DRAFT / NOT AUTHORITY / COLLECTOR ONLY / NO EXECUTION AUTHORITY

---
Document Type: Collector Survey Draft (Tranche A + B)
Terminal: 1
Date: 2026-03-20
Status: DRAFT — evidence collection only
Baseline Commit: `d0fa70f1` (docs: CODEX-ENTRY-POINT — OPUS 15건 근본 재감리 결과 반영)
Baseline Dirty: Yes — 100+ modified/untracked files (see git status snapshot)
Mode: survey-only, no execution, no patches, no closure
Authority: NONE — this document is raw evidence and inference, not an execution SSOT
---

## 1. Scope

**Coverage**: Tranche A (Macro Topology) + Tranche B (Runtime Core)
**Mode**: ROL 전역 전체 전수조사 — survey-only, side-effects included
**Role**: 기초 자료 수집 (evidence organizer, draft survey collector)

### Included Paths
- `main_a.py` — primary entrypoint (4,891 lines)
- `modules/core/` — runtime orchestration, stage pipeline, persistence, logging
- `modules/api/` — bridge server, process runner, IPC layer
- `modules/domain/agents/` — agent base class (bootstrap-relevant portions only)
- `modules/core/runtime_paths.py` — authority contract
- `config/` — runtime-affecting config (models.yaml, system.yaml, validation.yaml)
- `geuldobi-desktop/src/main.js` — desktop entry (authority chain head)

### Excluded Paths
- `modules/domain/agents/*` (agent logic beyond base_agent.py — Tranche C scope)
- `modules/validation/*` (validation pipeline — Tranche C scope)
- `UI/` (operator surface — Tranche E scope)
- `tests/` (regression surface — Tranche F scope, but TF evidence referenced)
- `scripts/` (utility surface — Tranche G scope)
- `docs/` (reference only, not primary sweep target)
- `.git/`, `__pycache__/`, `.venv/`, build outputs

---

## 2. Included Paths (Detailed)

| Path | Lines | Role |
|------|-------|------|
| `main_a.py` | 4,891 | God-object facade + bootstrap + menu loop |
| `modules/core/stage2_orchestrator.py` | 1,072 | Stage 2 arc design orchestration |
| `modules/core/stage3_orchestrator.py` | 2,257 | Stage 3 blueprint batch generation |
| `modules/core/stage4_orchestrator.py` | 1,757 | Stage 4 chief writer production |
| `modules/core/stage2_preflight.py` | 1,801 | Stage 2 preflight state analysis |
| `modules/core/stage2_finalizer.py` | 2,165 | Stage 2 arc output formatting/auditing |
| `modules/core/stage4_interview_round.py` | 6,203 | Stage 4 interview loop + advisory parallelism |
| `modules/core/stage4_context_builder.py` | 2,975 | Stage 4 context assembly |
| `modules/core/stage4_post_processor.py` | 1,874 | Stage 4 post-processing |
| `modules/core/stage2_context.py` | 371 | Stage 2 DI context (44 __slots__) |
| `modules/core/stage3_context.py` | 128 | Stage 3 DI context (19 __slots__) |
| `modules/core/stage4_context.py` | 271 | Stage 4 DI context (conditional_modules dict) |
| `modules/core/stage4_types.py` | 91 | Shared types (_RoundContext, _InterviewRoundResult) |
| `modules/core/stage0/__init__.py` | 1,016 | Stage 0 initialization manager |
| `modules/core/db_manager.py` | 3,986 | Database operations (SQLite, RLock) |
| `modules/core/prompt_builder.py` | 968 | Prompt template assembly |
| `modules/core/prompt_loader.py` | 276 | YAML prompt loading (singleton, thread-safe) |
| `modules/core/logger.py` | 352 | Logging utilities (singleton) |
| `modules/core/session_logger.py` | 354 | JSONL session logging |
| `modules/core/runtime_paths.py` | 102 | Authority contract + path resolution |
| `modules/core/world_state.py` | 1,338 | World state persistence |
| `modules/core/fact_ledger.py` | 852 | Cumulative fact tracking |
| `modules/api/bridge_server.py` | 2,320 | FastAPI bridge (desktop ↔ engine) |
| `modules/api/process_runner.py` | 808 | main_a.py subprocess wrapper |
| `modules/domain/agents/base_agent.py` | 2,213 | Agent base (context caching, session logger) |
| **Total** | **~36,000+** | |

---

## 3. Excluded Paths

| Path | Reason |
|------|--------|
| `modules/domain/agents/*` (except base_agent.py) | Tranche C (domain/agent layer) |
| `modules/validation/*` | Tranche C |
| `UI/` | Tranche E (operator surface) |
| `geuldobi-desktop/` (except main.js authority chain note) | Tranche E |
| `tests/` | Tranche F (referenced as TF evidence only) |
| `scripts/` | Tranche G |
| `config/` (deep internals) | Tranche H (cross-cutting contracts) |
| `lite_mode/`, `test_mode/` | Class B compatibility, not authoritative runtime |
| `tools/`, `tools2/`, `spikes/` | Non-runtime utilities |

---

## 4. Entrypoints

### 4.1 Supported Authority Chain (Class A)

**FACT** (verified from `modules/core/runtime_paths.py:L24-51` — live code):

```
geuldobi-desktop/src/main.js     (Electron app entry)
  → modules/api/bridge_server.py  (FastAPI, POST /run, WS /events)
  → modules/api/process_runner.py (subprocess wrapper for main_a.py)
  → main_a.py                     (SovereignApp.boot())
  → modules/core/stage{0,2,3,4}_orchestrator
```

- `RUNTIME_AUTHORITY_CONTRACT` dict at `runtime_paths.py:L24-51` codifies this chain
- `build_runtime_authority_summary()` at `runtime_paths.py:L54-64` exposes the contract as a queryable dict

### 4.2 Compatibility Entries (Class B)

**FACT** (from `runtime_paths.py:L32-37`):

| Entry | Label | Status |
|-------|-------|--------|
| `main.js` (root) | `debug_shadow_entry` | re-exports desktop src/main.js |
| `geuldobi-desktop/main.js` | `legacy_shim` | re-exports src/main.js |
| `lite_mode/` | `maintenance_only` | not part of supported runtime |
| `test_mode/` | `maintenance_only` | not part of supported runtime |

### 4.3 Direct Python Entrypoints

**FACT** (93 files with `if __name__ == "__main__"` found):

| File | Category | Notes |
|------|----------|-------|
| `main_a.py` | PRIMARY | `SovereignApp().boot()` |
| `RESET.py` | Utility | Project reset |
| `smoke_sc.py` | Smoke test | Direct smoke runner |
| `scripts/run_stage2_smoke.py` | Smoke | Stage 2 smoke test |
| `scripts/run_stage3_smoke.py` | Smoke | Stage 3 smoke test |
| `scripts/run_stage4_smoke.py` | Smoke | Stage 4 smoke test |
| `scripts/run_stage34_canary.py` | Canary | Stage 3+4 canary |
| `scripts/run_stage4_canary.py` | Canary | Stage 4 canary |
| `scripts/run_pytest_lowmem.py` | Test runner | Low-memory pytest |
| `scripts/ops_validator.py` | Ops | Queue validation |
| `lite_mode/main_lite.py` | Lite | Class B |
| `test_mode/run_stage.py` | Test mode | Class B |
| (81 others) | Scripts/tools/tests | Non-runtime |

---

## 5. Runtime Spine

### 5.1 Module-Level Bootstrap (main_a.py:L1-345)

**FACT** — These execute at **import time**, not in `__main__`:

| Lines | Function | Side-Effect | Guard |
|-------|----------|-------------|-------|
| L8-9 | Global flags | `_STDIO_BOOTSTRAPPED`, `_ASYNCIO_POLICY_BOOTSTRAPPED` | Module-level |
| L12-17, L44 | `_bootstrap_engine_sys_path()` | `sys.path.insert(0, script_dir)` | Called at L44 |
| L47-66, L91 | `_bootstrap_windows_stdio_utf8()` | Wraps stdout/stderr UTF-8 | Skips if `pytest` in sys.modules |
| L70-88, L92 | `_bootstrap_windows_asyncio_policy()` | Sets SelectorEventLoopPolicy | Skips if `pytest` in sys.modules |
| L94-100 | Faulthandler init | Opens `crash_dump.log`, `atexit.register` | try/except OSError |
| L128 | `load_dotenv(override=True)` | Loads `.env` into `os.environ` | Always runs |
| L131-159 | Eager imports | Core modules loaded | N/A |
| L161-175 | Lazy flags | `V50_MODULES_AVAILABLE`, `STAGE0_AVAILABLE` | Set to False |
| L188-314 | Lazy loaders defined | Functions defined, not called | Deferred |
| L317-320 | Spinner module flags | `_spinners_mod.V50/STAGE0` set | Module-level |
| L322-343 | Post-lazy imports | `asyncio`, `google.genai.types`, constants | Always runs |

**INFERENCE**: The pytest guard (L53, L76) prevents stdio wrapping and asyncio policy changes in test environments. This is a deliberate isolation seam. However, `sys.path.insert` (L44), `load_dotenv` (L128), and faulthandler (L94-100) run unconditionally.

### 5.2 SovereignApp.__init__ (main_a.py:L346-485)

**FACT** — Constructor sequence (all eager, ~140 lines):

| Order | Lines | What | Side-Effects |
|-------|-------|------|--------------|
| 1 | L350 | `load_dotenv(override=True)` | Env reload |
| 2 | L351 | `StudioVisualizer()` | Console UI init |
| 3 | L352-354 | `init_logger()` | FileHandler → `logs/session_*.log` |
| 4 | L355 | `StudioSystem(api_client=genai.Client(...))` | Gemini API client init |
| 5 | L356-367 | Core state init | Caches, flags, genre, history |
| 6 | L368-373 | Sub-orchestrator construction | Stage01Helpers, Stage2/3/4 Orchestrator (app=self) |
| 7 | L374-377 | Lazy module placeholders | `world_state=None`, `fact_ledger=None` |
| 8 | L379-391 | Session logger + agent logger | JSONL sink, BaseAgent class-level logger |
| 9 | L396-405 | AuditService + atexit | Buffer, callbacks, `atexit.register` |
| 10 | L407-438 | Service layer | UIService, StateService, ProjectService |
| 11 | L440-485 | V50 module nulls | 26 attributes → `None` (lazy) |

### 5.3 Boot Flow (main_a.py, ~L1329-2582)

**FACT** — `SovereignApp.boot()` sequence:

```
boot()
├── _select_genre()              # User selects genre (1-4+)
├── _select_project()            # User selects/creates project
├── _bind_selected_project(name)
│   ├── _reload_project_environment(name)
│   ├── sys.boot_v20_project(name, genre)
│   └── _retarget_project_runtime_sinks()
├── _restore_boot_runtime_state()
│   ├── PromptLoader().invalidate_cache()
│   └── _restore_preset_registry()
├── _ensure_project_genre_alignment()
│   └── Check stored vs selected genre; reject on mismatch
├── _initialize_project_genre_runtime()
│   ├── create_hud_manager() → self.sys.hud
│   ├── create_genre_guard() → self.sys.guard
│   └── work_guard.yaml → wrap genre guard (if exists)
└── _initialize_project_runtime_support(name)
    ├── _check_vector_db_lock()    # CRITICAL gate
    ├── VecMemory init (sqlite-vec)
    ├── _attach_agents()
    │   ├── _load_bootstrap_components()
    │   │   ├── _lazy_load_agents()       # 17 agent classes
    │   │   ├── _lazy_load_v50_modules()  # 25+ modules
    │   │   └── _lazy_load_stage0()
    │   ├── _get_agent_model_map()        # models.yaml
    │   ├── _init_core_agents()           # 17 agent instances
    │   ├── _apply_genre_bindings()       # genre → Director/Writer
    │   ├── _bootstrap_continuity_inspector()
    │   ├── _init_v50_modules()           # 25+ V50 instances
    │   └── _finalize_bootstrap_status()
    └── _run_main_process()               # infinite menu loop
```

### 5.4 Main Menu Loop (main_a.py:L2464-2582)

**FACT** — Infinite loop with 11 dispatch options:

| Key | Target | Description |
|-----|--------|-------------|
| 0 | `_phase_0_recovery()` | Phase 0 (Bible recovery) |
| 1 | `_stage_1_volumes()` | Stage 1 (Volume strategy) |
| 2 | `_stage_2_arcs()` | Stage 2 (Arc design) |
| 3 | `_stage_3_batch_blueprinting()` | Stage 3 (Blueprint design) |
| 4 | `_stage_4_v2_chief_writer()` | Stage 4 (Chief Writer production) |
| 5 | `_shutdown_app()` | Exit |
| 6 | One-Stop Arc pipeline | Compound |
| 7 | One-Stop Frontier Lag | Compound |
| 44 | Episode rollback | Destructive |
| 77 | Wipe production data | Destructive |
| 88 | Reset Stage 2 | Destructive |
| 99 | Selective rewind | Destructive |

**Error handling**: `KeyboardInterrupt` → `_shutdown_app()` + `sys.exit(0)`. General `Exception` → traceback to `logs/error.log` + `_shutdown_app()` + `sys.exit(1)`.

### 5.5 Stage Pipeline Spine

#### Stage 0: `modules/core/stage0/__init__.py` (1,016 lines)
- **Class**: `StageZeroManager`
- **Init**: receives `project_path`, `llm_client`, `ui`
- **Entry**: `run_new_project_flow()`, `run_reverse_engineering_flow()`, `import_bible()`
- **Side-effects**: Writes `work_guard.yaml`, `preset_registry.json`, state to output_dir

#### Stage 2: `modules/core/stage2_orchestrator.py` (1,072 lines)
- **Class**: `Stage2Orchestrator` (L24)
- **Init**: receives `app` (SovereignApp), optional `context` (Stage2Context)
- **Entry**: `async stage_2_arcs_async_logic(target_arc_count=None)`
- **DI**: Stage2Context auto-built from app via `from_app()` if not injected
- **Sub-modules**: `Stage2ValidationPipeline`, `Stage2PreflightAnalysis`, `Stage2Finalizer` (all lazy)
- **Fallback**: Arc number resolution: callback → direct lookup → division-based default

#### Stage 3: `modules/core/stage3_orchestrator.py` (2,257 lines)
- **Class**: `Stage3Orchestrator` (L478)
- **Init**: receives `app`, optional `context` (Stage3Context)
- **Entry**: `stage_3_batch_blueprinting(target_ep=None) → dict`
- **Lazy init**: StateTracker, WorldStateManager, FactLedger initialized on first stage 3 entry
- **Write-back**: `ctx.state_tracker = self.app.state_tracker` after lazy init (L580-582)

#### Stage 4: `modules/core/stage4_orchestrator.py` (1,757 lines)
- **Class**: `Stage4Orchestrator` (L209)
- **Init**: receives `app`, optional `context` (Stage4Context)
- **Entry**: `stage_4_v2_chief_writer(limit_mode=False, target_ep=None, skip_pause=False) → None`
- **Sub-modules**: `Stage4PostProcessor`, `Stage4ContextBuilder`, `Stage4InterviewRound` (all lazy)
- **Interview loop**: Up to 5 rounds; advisory chain parallelism (8 advisories, ThreadPoolExecutor(max_workers=8))
- **Error handling**: KeyboardInterrupt/Exception → flush audit buffer + safe_commit + return

### 5.6 DI Context Pattern (Phase 4C Standard)

**FACT** — All 3 stages follow identical pattern:

```python
class StageNOrchestrator:
    def __init__(self, app, context=None):
        self.app = app
        self._ctx = context  # optional injection

    @property
    def ctx(self):
        if self._ctx is None:
            self._ctx = StageNContext.from_app(self.app)
        return self._ctx
```

**Stage2Context**: 44 __slots__ (5 required + 18 extended + 20 callbacks + sync_cache_key_to_app)
**Stage3Context**: 19 __slots__ (2 required + 7 properties + 10 callbacks)
**Stage4Context**: ~22 __slots__ + `conditional_modules` dict (8 optional modules) + `get_module(name)` helper

**INFERENCE**: The one-way snapshot pattern means orchestrators read from `from_app()` at stage entry. Mutations during stage execution don't auto-sync back unless explicitly written. This is documented as a known lesson (memory: "DI ctx 스냅샷은 단방향 — Stage 종료 후 app에 write-back 필수").

### 5.7 Shutdown Flow

**FACT** (main_a.py, ~L3053-3071):

```
_shutdown_app()
├── _persist_shutdown_metrics()
├── _persist_shutdown_cost_scope()
├── _persist_shutdown_advisory_state()
├── _persist_shutdown_trackers()
├── _persist_shutdown_project_state()
├── session_logger.begin_shutdown()
├── db.begin_shutdown()
├── _write_audit_summary("shutdown_final")
└── _close_shutdown_resources()
```

**Registered atexit handlers** (2):
1. `_fault_log.close` (L97) — crash dump file handle
2. `_flush_audit_buffer` (L405) — audit buffer flush

---

## 6. Side-Effect Sweep

### 6.1 File Writes

| Source | Target | Trigger | Blocking? |
|--------|--------|---------|-----------|
| `main_a.py:L35` | `logs/error.log` | Boot failure traceback | Non-blocking (try/except) |
| `main_a.py:L95` | `crash_dump.log` | Faulthandler init | Non-blocking (try/except OSError) |
| `logger.py:L81` | `logs/session_YYYYMMDD_HHMMSS.log` | `init_logger()` | Blocking (logger setup) |
| `session_logger.py` | `logs/session/*.jsonl` | Session event recording | Non-blocking |
| `bridge_server.py:L212` | `logs/control-plane-provenance.jsonl` | API call logging | Non-blocking |
| `stage0/__init__.py` | `work_guard.yaml`, `preset_registry.json`, state files | Stage 0 completion | Non-blocking |
| `db_manager.py` | `project_data.db` (SQLite) | All DB writes | Blocking (RLock) |
| `world_state.py:L141-149` | DB anchor `world_state` | State save | Non-blocking (catches exception) |
| `fact_ledger.py` | DB anchor `fact_ledger` | Fact save | Non-blocking (degraded mode on failure) |

### 6.2 DB Writes

| Component | DB Target | Operation |
|-----------|-----------|-----------|
| DBManager | `project_data.db` | `_boot_db()` → CREATE TABLE (multiple tables) |
| Stage 2 | arcs, state_snapshots | INSERT/UPDATE after arc generation |
| Stage 3 | blueprints, state_snapshots | INSERT/UPDATE after blueprint generation |
| Stage 4 | manuscripts, titles, state_updates | INSERT/UPDATE after manuscript production |
| WorldState | `world_state` anchor | JSON blob save |
| FactLedger | `fact_ledger` anchor | JSON blob save |
| VecMemory | `project_data.db` (sqlite-vec tables) | Embedding storage |

### 6.3 Console/UI Output

| Source | Surface | Notes |
|--------|---------|-------|
| `StudioVisualizer` | stdout/stderr | Rich console output via spinners |
| `print()` | stdout | Bootstrap notices (L98-100) |
| Menu loop | stdout | Genre/project selection, stage menu |

### 6.4 Cache/Global State

| Singleton/Cache | Location | Thread-Safety |
|-----------------|----------|---------------|
| `PromptLoader._instance` + `_cache` | `prompt_loader.py:L21-25` | threading.Lock (double-checked) |
| `StudioLogger._instance` | `logger.py:L42-43` | threading.Lock |
| `BaseAgent._context_caches` | `base_agent.py:L1896-1897` | threading.Lock |
| `MetricsCollector` | `metrics_collector.py` | Singleton pattern |
| `SovereignApp._cumulative_state_cache` | `main_a.py:L365` | Instance-level (no lock) |
| `Stage3Orchestrator._cached_entity_registry` | `stage3_orchestrator.py:L494-495` | Instance-level (no lock) |

### 6.5 Rollback/Recovery/Retry

| Path | Mechanism | Notes |
|------|-----------|-------|
| Menu key 44 | Episode rollback | Sets `state_tracker = None` after rollback |
| Menu key 77 | Wipe production data | Full data wipe |
| Menu key 88 | Reset Stage 2 | Stage 2 data reset |
| Menu key 99 | Selective rewind | Targeted rewind |
| Stage 4 KeyboardInterrupt | Flush + commit + return | Graceful cleanup |
| Stage 4 Exception | Log + flush + commit + return | Graceful cleanup |
| WorldState save failure | Non-blocking continue | Catches exception |
| FactLedger init failure | `_degraded` flag | Continues with degraded mode |

### 6.6 Config/Env Mutation

| Source | Target | Timing |
|--------|--------|--------|
| `load_dotenv(override=True)` | `os.environ` | Module-level (L128) + `__init__` (L350) |
| `_bootstrap_engine_sys_path()` | `sys.path` | Module-level (L44) |
| `_bootstrap_windows_stdio_utf8()` | `sys.stdout`, `sys.stderr` | Module-level (L91) |
| `_bootstrap_windows_asyncio_policy()` | asyncio event loop policy | Module-level (L92) |

### 6.7 Bootstrap Fallback Behavior

| Fallback | Condition | Behavior |
|----------|-----------|----------|
| Faulthandler | OSError on `crash_dump.log` | Print warning to stderr, continue |
| Windows stdio | pytest loaded | Skip entirely |
| Windows asyncio policy | pytest loaded | Skip entirely |
| `_lazy_load_v50_modules()` | ImportError | Returns None, `V50_MODULES_AVAILABLE=False` |
| VecMemory | sqlite_vec tables missing | Lazy-creates tables |
| WorldState save | Exception | Non-blocking, logs warning |
| FactLedger init | Exception | `_degraded=True`, continues |

---

## 7. Facts

### F-1. Runtime Authority Chain
`runtime_paths.py:L24-51` defines the supported chain as `desktop/main.js → bridge_server → process_runner → main_a.py → stage pipeline`. This is a live code contract, not just documentation.

### F-2. Module-Level Bootstrap Executes at Import
Lines 44, 91, 92, 94-100, 128 in `main_a.py` execute side-effects at module import time. The `pytest` guard (L53, L76) prevents stdio/asyncio changes in test environments but does NOT prevent `sys.path.insert`, `load_dotenv`, or faulthandler.

### F-3. SovereignApp is a God Object
4,891 lines. Constructor initializes 3 orchestrators, 3 services, 1 audit service, 1 session logger, 26 V50 module placeholders. Facade pattern delegates to sub-modules but retains menu loop and stage wrappers.

### F-4. Stage Pipeline is Synchronous CLI Menu
`_run_main_process()` is an infinite loop dispatching to stage methods. No async event loop, no subprocess parallelism at the top level. ProcessRunner wraps main_a.py as a subprocess only when the desktop bridge drives it.

### F-5. DI Context Snapshot is One-Way
Stage2/3/4Context.from_app() takes a snapshot. Changes during stage execution require explicit write-back. This is a known contract (confirmed by memory and live code).

### F-6. Three Singletons Shared Across Process
PromptLoader, StudioLogger, BaseAgent._context_caches are class-level singletons with threading.Lock protection.

### F-7. Lazy Loading Strategy
Agents (17 classes), V50 modules (25+), Stage 0 are lazy-loaded only during `_attach_agents()`, not at module import. This is a deliberate memory/startup optimization.

### F-8. ProcessRunner Drives main_a.py as Subprocess
`modules/api/process_runner.py` wraps `main_a.py` as a hidden subprocess with stdin sequencing (Mode A: genre → project → menu key → sub_key → exit). ANSI stripping, UTF-8 decode with `errors="replace"`.

### F-9. Bridge Server is FastAPI
`modules/api/bridge_server.py` (2,320 lines) serves POST /run, POST /stop, GET /status, WS /events, POST /run/{run_id}/input. Provenance logging to `logs/control-plane-provenance.jsonl`.

### F-10. DBManager Uses RLock
`db_manager.py:L65` — `self._lock = threading.RLock()` for thread-safety. 3,986 lines total. `_boot_db()` runs CREATE TABLE at init.

### F-11. Two Log Sinks Before Project Init
- `logs/error.log` (workspace-level, boot failure fallback)
- `crash_dump.log` (faulthandler, process-level)

After project init, project-local sinks take over: `logs/session_*.log`, `logs/session/*.jsonl`.

### F-12. atexit Handlers Registered at Constructor Time
- `_fault_log.close` (L97) — crash dump file
- `_flush_audit_buffer` (L405) — audit buffer

### F-13. Stage 4 Advisory Chain is Parallelized
`stage4_interview_round.py:L2330-2367` — ThreadPoolExecutor(max_workers=8), 8 advisory checks (7 LLM + 1 Python-only), per-advisory timeout 60s, overall timeout 300s.

### F-14. Env Var Authority
- `GEULDOBI_ENGINE_ROOT` — frozen mode override (runtime_paths.py:L68)
- `GEULDOBI_WORKSPACE` — workspace root (runtime_paths.py:L75)
- `GEULDOBI_PROJECTS_ROOT` — projects directory (runtime_paths.py:L82)
- `GOOGLE_API_KEY` — Gemini API key (main_a.py:L355)
- `GEULDOBI_DESKTOP_MODE` — desktop mode flag (bridge_server.py:L228)
- `PROMPT_DIR` — prompt directory override (prompt_loader.py:L43-44)

### F-15. Stage Orchestrator Line Counts (Verified)
| File | Lines |
|------|-------|
| stage2_orchestrator.py | 1,072 |
| stage3_orchestrator.py | 2,257 |
| stage4_orchestrator.py | 1,757 |
| stage2_preflight.py | 1,801 |
| stage2_finalizer.py | 2,165 |
| stage4_interview_round.py | 6,203 |
| stage4_context_builder.py | 2,975 |
| stage4_post_processor.py | 1,874 |
| **Total stage pipeline** | **20,104** |

---

## 8. Inferences

### I-1. Module-Level Side-Effects May Affect Test Isolation
`sys.path.insert` and `load_dotenv(override=True)` run unconditionally at import. While `pytest` guards prevent stdio/asyncio changes, dotenv override could mutate test environment variables if `.env` file has unexpected contents. Test fixtures should account for this.

### I-2. God Object Size is Stable but Large
4,891 lines in main_a.py is large but has been stable through V64-V68 refactors. The facade pattern (delegating to orchestrators and services) reduces cognitive load but the constructor's 140-line init sequence is still a single-point-of-failure for bootstrap.

### I-3. DI Context Write-Back is a Known but Manual Contract
The one-way snapshot pattern works but requires developers to remember explicit write-back calls. This was a source of a prior CRITICAL bug (Stage2→app StateTracker sync — memory: "Debug Sweep 2차 Phase 1"). The pattern is now documented but enforcement is convention-only.

### I-4. ProcessRunner stdin Sequencing is Fragile
Mode A stdin sequence (`genre_index → Enter → project_index → genre_confirm → menu_key → sub_key → confirmations → exit(5)`) is tightly coupled to main_a.py's menu structure. Any change to menu order or prompts could break the bridge.

### I-5. Lazy Loading Defers Most Memory to _attach_agents
The 17 agent classes + 25+ V50 modules are only loaded after project selection. This means ~70% of runtime code is deferred until the user commits to a project. Failure in lazy loading cascades to bootstrap failure.

### I-6. FactLedger Degraded Mode is Silent
`_degraded=True` on init failure means FactLedger continues silently without fact tracking. This could lead to undetected data loss in long-running sessions if the DB anchor is corrupted.

### I-7. Advisory Chain Timeout May Mask Failures
60s per-advisory timeout with 300s overall could mask slow LLM responses as timeouts rather than failures. The distinction between "advisory timed out" and "advisory failed" may not be clear in downstream telemetry.

---

## 9. Uncertainty / Contradictions

### U-1. load_dotenv Called Twice — Intent Unclear
`load_dotenv(override=True)` is called at module level (L128) AND in `__init__` (L350). The module-level call loads workspace `.env`. The `__init__` call reloads it. If a project-specific `.env` is intended for the second call, this is not visible from the current code path — the project isn't selected yet at `__init__` time.

**Stale suspicion**: The second call may be a historical artifact from before the DI refactor.

### U-2. _cumulative_state_cache Thread Safety
`main_a.py:L365-366` — `_cumulative_state_cache` and `_cumulative_state_cache_key` are instance-level without explicit locking. The main menu loop is single-threaded, so this is likely safe in practice. However, if Stage 4's ThreadPoolExecutor advisories access this cache indirectly, there could be a data race.

**Uncertainty level**: Low risk in current architecture (main loop is serial), but worth noting.

### U-3. VecMemory Shared Mode Seam
`vec_memory.py:L78-79` supports a shared mode with external conn/lock. The interaction between shared mode and DBManager's RLock is not immediately clear. If both VecMemory and DBManager hold separate locks on the same SQLite file, deadlock is theoretically possible.

**Uncertainty level**: Needs deeper investigation (Tranche D scope).

### U-4. Bridge Server Global Sequence Counter
`bridge_server.py:L103` — `_seq_iter = itertools.count(1)` is a module-level counter. If the bridge server is restarted without clearing client state, sequence numbers could collide with client expectations. This is a minor concern for long-running desktop sessions.

### U-5. Stage 1 is Missing from Orchestrator Pattern
Stage 0 has `StageZeroManager`. Stage 2/3/4 have dedicated orchestrators. Stage 1 (`_stage_1_volumes()`) delegates to `_stage01_helpers`. There's no `Stage1Orchestrator` class. This asymmetry may be intentional (Stage 1 is simpler) or may represent a gap in the DI refactor.

**Inference**: Likely intentional — Stage 1 volume strategy is handled by `Stage01Helpers` which combines stage 0 and 1 support.

### U-6. TF Test Assumptions vs Live Code — Potential Staleness

Memory records TF audit completion with "2,114 passed + 68 xfailed". Live workspace has 100+ modified files. Some TF tests may assume contracts that have since changed. Specific areas of concern:

- `test_main_a_stage_entry_contracts.py` — assumes specific context-building wrappers in main_a.py. If wrapper signatures changed in dirty files, tests may be out of sync.
- `test_stage4_orchestrator.py` — assumes patch mode threshold logic. Threshold values may have shifted.
- `test_safe_op_recovery_state_matrix.py` — references `docs/2026-03-13/safe-op-recovery-state-matrix.json`. If this file moved or was modified, test may be stale.

**Stale suspicion**: Cannot confirm without running tests. Marked as watchlist.

---

## 10. Candidate Watchlist

| ID | Area | Concern | Priority |
|----|------|---------|----------|
| W-1 | `main_a.py:L128+L350` | Double `load_dotenv` — verify intent | Low |
| W-2 | `main_a.py:L365-366` | `_cumulative_state_cache` lock safety under ThreadPoolExecutor | Low |
| W-3 | `vec_memory.py` shared mode | Lock interaction with DBManager.RLock | Medium (Tranche D) |
| W-4 | `bridge_server.py:L103` | Global seq counter restart behavior | Low |
| W-5 | Stage 1 DI pattern gap | No Stage1Orchestrator / Stage1Context | Low |
| W-6 | TF test staleness | 100+ dirty files may invalidate TF assumptions | Medium |
| W-7 | `process_runner.py` stdin coupling | Menu structure changes break bridge | Medium |
| W-8 | `fact_ledger.py` degraded mode | Silent data loss on init failure | Medium |
| W-9 | Advisory timeout vs failure distinction | Telemetry clarity for timed-out advisories | Low |
| W-10 | Module-level `sys.path.insert` | Potential import ordering surprises in PyInstaller | Low |

---

## 11. TF Evidence Notes

### 11.1 Runtime Core Tests (TF-linked)

| Test File | TF/Sweep | Live Contract | Status |
|-----------|----------|---------------|--------|
| `test_main_a_boot_binding.py` | Boot binding | Project selection + env reload + VecDB lock | **FACT**: exists, mocks SovereignApp |
| `test_main_a_stage_entry_contracts.py` | Stage entry | Context building wrappers for Stage2/3/4 | **STALE SUSPICION**: dirty files may have changed wrappers |
| `test_main_a_packaged_bootstrap_contract.py` | Packaged app | Bootstrap in frozen mode | **FACT**: exists |
| `test_bootstrap_status.py` | Bootstrap | Agent loading, spinner flags, genre bindings | **FACT**: exists |
| `test_stage2_orchestrator.py` | S2 | Arc resolution chain + constraint normalization | **FACT**: exists |
| `test_stage3_orchestrator.py` | S3 | Quality dashboard recording + lazy init | **FACT**: exists |
| `test_stage4_orchestrator.py` | S4 | Patch mode + interview round + advisory chain | **FACT**: exists |
| `test_opus_tf5_e6_regressions.py` | TF-5 | Stage2 finalizer + arc critic + unified validator | **FACT**: 123 lines |
| `test_tf10_episode_details.py` | TF-10 | ArcData model + episode_details | **FACT**: 80 lines |
| `test_safe_op_recovery_state_matrix.py` | Recovery | Destructive ops state machine | **STALE SUSPICION**: references dated doc |

### 11.2 Chaos Tests (Runtime Failure Modes)

| Test | Contract | Mock Strategy | TF Link |
|------|----------|---------------|---------|
| `chaos/test_validation_degrade.py` | prev_hud=None → fail-closed (BLOCKING) | ContinuityValidator mock | TF-15 policy |
| `chaos/test_dead_npc_hard_block.py` | Deceased NPC → REJECT | State change mock | 대원칙 4 |
| `chaos/test_feedback_loop.py` | Director REJECT → rewrite loop | Multi-call side_effect | S2/S4 retry |
| `chaos/test_partial_commit.py` | Incomplete DB transaction | DBManager mock | DB safety |
| `chaos/test_rollback_boundary.py` | Episode→arc mapping during rollback | Mapping validation | Menu key 44 |
| `chaos/test_stage3_metrics.py` | QualityDashboard recording | Mock calls | P6-02 |
| `chaos/test_blueprint_none.py` | None blueprint handling | None-assertion | Null safety |

### 11.3 E2E Smoke Tests

| Test | What It Proves | Real Components |
|------|----------------|-----------------|
| `e2e/test_l3_stage4_smoke.py` | Full Stage 4 DB lifecycle | Real DBManager on tmp_path, real project_data.db copy |
| `e2e/test_smoke_pipeline.py` | Multi-stage pipeline | TBD |

### 11.4 TF Assumptions vs Live Code

**Key observation**: Memory records "2,114 passed + 68 xfailed" at Opus TF audit checkpoint. Current workspace has 100+ modified files. The following TF contracts should be re-validated:

1. **Stage2Context 44 __slots__** — if any new slots were added in dirty files, tests using `from_app()` may be incomplete
2. **Stage4Context conditional_modules** — 8 modules listed; if new modules were added, `get_module()` tests may be incomplete
3. **Patch mode thresholds (50/80)** — if thresholds changed, `test_arc_patch_mode.py` / `test_blueprint_patch_mode.py` may fail
4. **Advisory chain worker count (8)** — if advisory count changed, `test_stage4_interview_round.py` may be out of sync

**Recommendation**: These are watchlist items, not conclusions. Test execution would resolve them definitively.

---

## Appendix A. Key File Reference (Quick Lookup)

```
RUNTIME AUTHORITY
  modules/core/runtime_paths.py:L24-51    RUNTIME_AUTHORITY_CONTRACT

BOOTSTRAP
  main_a.py:L1-100                        Module-level side-effects
  main_a.py:L346-485                      SovereignApp.__init__
  main_a.py:L1329-1350                    boot()
  main_a.py:L2286-2339                    _attach_agents()
  main_a.py:L2464-2582                    _run_main_process()
  main_a.py:L3053-3071                    _shutdown_app()
  main_a.py:L4881-4891                    if __name__ == "__main__"

STAGE PIPELINE
  modules/core/stage0/__init__.py          StageZeroManager
  modules/core/stage2_orchestrator.py:L24  Stage2Orchestrator
  modules/core/stage3_orchestrator.py:L478 Stage3Orchestrator
  modules/core/stage4_orchestrator.py:L209 Stage4Orchestrator

DI CONTEXTS
  modules/core/stage2_context.py           44 __slots__
  modules/core/stage3_context.py           19 __slots__
  modules/core/stage4_context.py           conditional_modules dict

PERSISTENCE
  modules/core/db_manager.py               RLock + SQLite
  modules/core/world_state.py              DB anchor world_state
  modules/core/fact_ledger.py              DB anchor fact_ledger

IPC / BRIDGE
  modules/api/bridge_server.py             FastAPI bridge
  modules/api/process_runner.py            Subprocess wrapper

SINGLETONS
  modules/core/prompt_loader.py:L21-25     PromptLoader (Lock)
  modules/core/logger.py:L42-43            StudioLogger (Lock)
  modules/domain/agents/base_agent.py:L1896-1897  _context_caches (Lock)
```
