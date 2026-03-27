Date: 2026-03-27
Type: T1 lane evidence manifest
Parent Report: `docs/2026-03-27/opus/rol-llm-gimmick-t1-navigation-entry.md`

## File Inventory

| File | Lines | Surveyed |
|------|-------|----------|
| `main_a.py` | 4,808 | Entry routing, stage dispatch, shutdown, gimmick sites |
| `modules/core/stage01_helpers.py` | 1,029 | Full class structure, entry methods, delegation |
| `modules/core/stage2_orchestrator.py` | 1,731 | DI context, lazy sub-modules, payload schemas |
| `modules/core/stage3_orchestrator.py` | 2,851 | DI context, implicit state transfer, entity cache |
| `modules/core/stage4_orchestrator.py` | 2,414 | DI context, lazy sub-modules, cache invalidation |
| `modules/api/bridge_server.py` | 2,372 | Routes, lifespan, WS, singleton management |
| `modules/api/process_runner.py` | 823 | Credential injection, Mode A/B, subprocess lifecycle |
| `modules/api/control_plane_contract.py` | 92 | Authority path, key sets |
| `modules/api/run_validator.py` | 95 | Validation gate, whitelist |
| `modules/api/risk_approval.py` | 214 | Dual-control enforcement |
| `modules/api/prompt_broker.py` | 205 | Prompt lifecycle, sync/async bridge |
| `modules/api/prompt_classifier.py` | 172 | Regex patterns, prompt detection |
| `modules/api/__init__.py` | 13 | Re-exports |
| `docs/2026-03-23/llm-codebase-orientation-pack.md` | 306 | Drift-checked |

## Key Anchor Lines

### main_a.py
- L346: `class SovereignApp`
- L1387: `boot()`
- L1424: Legacy model map fallback
- L2159: `_run_main_process()` menu loop
- L2231: `_dispatch_main_process_choice()`
- L2257: Silent fallthrough `return True`
- L2280: `[SilentPass:Shutdown]` exception handler
- L2771: `_shutdown_app()` 4-phase sequence
- L2796: Stage 0 thin delegate `[Phase 4C-1b-a]`
- L2808: Stage 1 thin delegate `[Phase 4C-1b-b]`
- L2907: Stage 2 entry (not thin)
- L2930-2935: StateTracker sync-back from Stage 2
- L2939-2961: Stage 2 `[V64.P3][COMPAT]` stubs (5 methods)
- L3164: Stage 3 thin delegate `[Phase 4C-1a]`
- L3794: Stage 4 lazy-init gateway `[V64.P3]` (NOT thin)
- L3811-3831: StateTracker lazy-init (non-blocking)
- L3833-3846: WorldState lazy-init (non-blocking)
- L3852-3868: FactLedger lazy-init (non-blocking)
- L4798: `if __name__ == "__main__"`

### stage01_helpers.py
- L35: `class Stage01Helpers`
- L130: `phase_0_recovery()`
- L505: `stage_0_extended()`
- L786: `stage_1_volumes()`

### stage2_orchestrator.py
- L78: `class Stage2Orchestrator`
- L105: `ctx` property (lazy DI)
- L118: `validation_pipeline` lazy property
- L127: `preflight` lazy property
- L136: `finalizer` lazy property
- L889: `stage_2_arcs_async_logic()`
- L1708-1729: Thin wrapper methods

### stage3_orchestrator.py
- L480: `class Stage3Orchestrator`
- L500: `ctx` property (lazy DI)
- L549: `stage_3_batch_blueprinting()`
- L701: `_init_state_tracker_if_needed()` (assigns to app)
- L726: `_init_world_state_if_needed()` (assigns to app)
- L743: `_init_fact_ledger_if_needed()` (assigns to app)

### stage4_orchestrator.py
- L461: `class Stage4Orchestrator`
- L479: `outcome_runtime` (eager init)
- L482: `ctx` property (lazy DI)
- L493-496: Cache invalidation on ctx assignment
- L499: `post_processor` lazy property
- L506: `context_builder` lazy property
- L543: `interview_round` lazy property
- L2365: `stage_4_v2_chief_writer()`

### process_runner.py
- L232: `class ProcessRunner`
- L278: `start()`
- L310: Mode A/B auto-selection
- L380: `stop()`
- L567: `_read_loop_mode_b()` (prompt detection)
- L687: `_build_stdin_sequence()`
- L780: `_build_env()` (credential injection)
- L794-821: API key / Vertex / Anthropic env vars

### bridge_server.py
- L2025: `lifespan()` context manager
- L2049: FastAPI app creation
- L2057: `POST /run`
- L2170: `POST /run/{run_id}/input`
- L2200: `POST /stop`
- L2218: `GET /status`
- L2355: `WebSocket /events`

## Orientation Pack Drift Summary

### Files in §2 Reading Order: All 31 Exist

### Files Missing from §2 But Exist in Live Workspace

| File | Why It Matters |
|------|---------------|
| `modules/core/stage4_reject_runtime.py` | Retry/reject loop authority (imported by stage4_interview_round.py) |
| `modules/core/stage4_retry_runtime.py` | Retry/reject loop authority (imported by stage4_interview_round.py) |
| `modules/core/stage4_outcome_runtime.py` | Outcome processing (imported by stage4_orchestrator.py, eagerly instantiated) |
| `modules/core/stage4_context_packets.py` | Context pipeline (mentioned in pack §9 but not in §2) |
| `modules/core/llm_router.py` | Provider routing layer |
| `modules/core/llm_provider.py` | Provider-neutral request/response |
| `modules/core/models_config.py` | Model metadata SSOT |
| `modules/core/providers/*.py` | 6 provider adapters |

### §4.5 `_god1_*` Channel: Verified

Producer: `stage4_interview_round.py:2270-2280` (7 attributes set)
Consumer: `stage4_director_runtime.py:102-110` (7 attributes read via getattr)
Reverse: `stage4_director_runtime.py:167` (writes `_god1_director_memory_context` back)

## Gimmick Registry

| ID | Name | Location | Verdict |
|----|------|----------|---------|
| G-1 | Dispatch silent fallthrough | `main_a.py:2257` | Inelegant |
| G-2 | Stage 4 lazy-init non-blocking | `main_a.py:3794-3879` | Mixed |
| G-3 | Stage 3 implicit state transfer | `stage3_orchestrator.py:701-761` | Inelegant |
| G-4 | Stage 2 StateTracker sync-back | `main_a.py:2930-2935` | Mixed |
| G-5 | Credential injection no audit | `process_runner.py:780-823` | Mixed |
| G-6 | Legacy model map fallback | `main_a.py:1424` | Inelegant |
| G-7 | Multi-key arc fallback | `main_a.py:2838-2870` | Mixed |
| G-8 | Mode A/B auto-selection | `process_runner.py:310` | Elegant |
| G-9 | Shutdown silent-pass | `main_a.py:2280` | Elegant |
| G-10 | DI context cache invalidation | `stage4_orchestrator.py:493-496` | Elegant |
| G-11 | `_god1_*` authority channel | `stage4_interview_round.py:2270` | Inelegant |
| G-12 | Eager outcome_runtime | `stage4_orchestrator.py:479` | Mixed |
