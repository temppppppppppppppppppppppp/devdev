# S3D-T5: Stage 3 Test Coverage, Mock Accuracy, Error Path Audit (1-pass)

**Date**: 2026-03-13
**Scope**: `tests/test_stage3_orchestrator.py`, `tests/e2e/test_l3_stage3_smoke.py`
**Source under test**: `modules/core/stage3_orchestrator.py`, `modules/domain/agents/three_phase_blueprint_generator.py`

---

## Coverage Map

### `tests/test_stage3_orchestrator.py` (1129 lines, 43 test functions)

| Class | Test Function | Covers |
|-------|--------------|--------|
| `TestConstructor` | `test_app_reference_stored` | `__init__` app binding |
| | `test_entity_cache_initialized` | `__init__` cache sentinel |
| `TestInitStateTrackerIfNeeded` | `test_skip_if_already_initialized` | `_init_state_tracker_if_needed` skip |
| | `test_creates_when_none_stub` | stub call (weak) |
| | `test_creates_when_none` | actual creation with patch |
| `TestInitWorldStateIfNeeded` | `test_skip_if_already_initialized` | skip path |
| | `test_creates_when_none` | creation path |
| | `test_failure_is_non_blocking` | exception path |
| `TestInitFactLedgerIfNeeded` | `test_skip_if_already_initialized` | skip path |
| | `test_creates_when_none` | creation path |
| | `test_failure_is_non_blocking` | exception path |
| `TestGetEntityRegistry` | `test_first_call_extracts` | initial extraction |
| | `test_cached_on_same_arc` | cache reuse |
| | `test_refreshes_on_new_arc` | cache invalidation |
| | `test_failure_non_blocking` | LLM error path |
| `TestStageAttemptObservability` (4 tests) | `test_handle_success_persists_semantic_context_metadata` | observability flags in success |
| | `test_handle_failure_persists_failure_category_and_observability` | failure category classification |
| | `test_handle_success_persists_stage3_director_selection` | director_selection DB save (PASS) |
| | `test_handle_failure_persists_stage3_director_selection` | director_selection DB save (REJECT) |
| `TestLoadPrevBlueprint` | 3 tests | ep1 None, ep2 returns, crash returns None |
| `TestGetProtagonistNameSafe` | 2 tests | normal return, crash default |
| `TestNs4TimelineHelpers` | 2 tests | timeline extraction, raw equality |
| `TestGenerateBlueprint` | 7 tests | world_state, fact_ledger, style_guide, work_focus, advisor, ctx DI, relation_slice in semantic_context |
| `TestProcessSingleEpisode` | 13 tests | skip existing, continuity block, no arc break, PASS_WITH_FIX routing, pass_rate_monitor success/failure, metrics_session_id, artifact linkage, episode summary logging (PASS+REJECT) |
| `TestHandleSuccess` | 3 tests | save+increment, integrity fail skip, unresolved continuity pins |
| `TestHandleFailure` | 2 tests | increment, 3-consecutive-fails break |
| `TestStage3BatchBlueprintingEntryPoint` | 4 tests | no arcs early return, full single episode, break path, hybrid project head |
| `TestStage3ContextDI` | 10 tests | ctx null/auto-build/inject/setter/protagonist/from_app/slots_count/sync/compat/none_callbacks |

### `tests/e2e/test_l3_stage3_smoke.py` (234 lines, 5 test functions)

| Class | Test Function | Covers |
|-------|--------------|--------|
| `TestL3Stage3Setup` | `test_arcs_loaded` | fixture sanity |
| | `test_arc_structure` | ep_start/ep_end type check |
| | `test_bible_has_plot_roadmap` | bible structure |
| `TestL3Stage3Pipeline` | `test_stage3_runs_3_episodes` | 3-episode full pipeline |
| | `test_blueprint_content_valid` | DB persistence + field presence |

---

## Checklist Findings

### 1. Coverage Gaps

**Status: FINDING**

| Gap | Severity | Evidence | Impact |
|-----|----------|----------|--------|
| **SC (Smart Context) failure path** untested | P3 | `stage3_orchestrator.py:1041` `except Exception as _s3_sc_err` -- no test exercises this path | Low -- non-blocking, but silent failure could mask retrieval issues |
| **Treatment Block injection** untested | P2 | `stage3_orchestrator.py:1044-1101` -- `[TF9]` block injection from `plot_roadmap` not covered by any test | Medium -- production semantic_context will include this block but no test verifies its format/content |
| **Time markers (`[NS-4]`)** partially tested | P3 | `test_stage3_orchestrator.py:398-421` covers `_extract_timeline_start_end` and `_timeline_start_end_raw_equal` helper methods, but the injection path in `_generate_blueprint` (`stage3_orchestrator.py:1103-1146`) is untested | Low -- helpers are tested but integration into semantic_context is not |
| **InPlace Patch** not applicable | OK | Stage 3 does not use InPlace/PASS_WITH_FIX 3-tier routing (that is Stage 4 only). Stage 3 only routes PASS_WITH_FIX to _handle_failure. | N/A |
| **PASS_WITH_FIX routing** tested | OK | `test_stage3_orchestrator.py:714-732` `test_pass_with_fix_uses_failure_path` verifies PASS_WITH_FIX goes to `_handle_failure` and not `_handle_success` | Correct -- Stage 3 treats PASS_WITH_FIX as failure per `stage3_orchestrator.py:791-794` which only accepts `PASS` and `PASS_WITH_WARNING` |
| **ASP (Adaptive Sampling Protocol)** untested | P3 | `stage3_orchestrator.py:1260` passes `adversarial_self_play=ctx.adversarial_self_play` to generate() but no test verifies this wiring | Low -- ASP is informational in Stage 3 |
| **gen_err crash path** untested | P2 | `stage3_orchestrator.py:1270-1278` -- `except Exception as gen_err` produces `{"final_verdict": "ERROR", "error": ...}` but no test exercises this path (the LLM generate() crash) | Medium -- this is the primary crash safety net for the entire _generate_blueprint method |
| **invalid pipeline_result guard** untested | P3 | `stage3_orchestrator.py:1280-1281` -- `if not isinstance(pipeline_result, dict)` fallback untested | Low -- edge case but could mask data corruption |

### 2. Mock Contracts

**Status: FINDING (minor)**

| Item | Status | Evidence | Description |
|------|--------|----------|-------------|
| `generate()` return format | OK | Mock returns `(dict, dict)` tuple matching `ThreePhaseBlueprintGenerator.generate()` signature `-> tuple[dict | None, dict]` at `three_phase_blueprint_generator.py:77`. Unit test mock at `test_stage3_orchestrator.py:43-46` returns `({"integrated_scenario": "test", ...}, {"final_verdict": "PASS", ...})` |
| `generate()` kwargs | OK | `stage3_orchestrator.py:1245-1261` calls `.generate(ep_num=..., arc_data=..., ...)` matching the real signature at `three_phase_blueprint_generator.py:58-76` |
| DB method signatures | OK | `save_stage_attempt`, `save_director_selection`, `save_cost_record`, `get_latest_blueprint_number`, `get_blueprint`, `get_recent_manuscripts`, `load_anchor` -- all called via kwargs, MagicMock auto-accepts |
| `_get_arc_context_for_episode` return type | OK | Returns `(int, dict)` tuple at `test_stage3_orchestrator.py:68`, matches orchestrator usage at `stage3_orchestrator.py:731` |
| **`state_extractor` mock contract** | FINDING P3 | `test_stage3_orchestrator.py:177` mocks `extract_cumulative_state` return as `{"entity_registry": {"characters": ["A"]}}`. Real StateExtractor returns dict with more fields. The mock is sufficient for the code path tested, but `characters` value is `["A"]` (list of str) while production returns list of dict (`[{"name": "A", ...}]`). The orchestrator handles both via `_fix_entity_registry_protagonist`, but the mock doesn't exercise the dict-within-list path. | Minor -- `_fix_entity_registry_protagonist` is delegated to app facade |

### 3. Error Paths

**Status: FINDING**

| Path | Status | Evidence | Description |
|------|--------|----------|-------------|
| **gen_err crash** | FINDING P2 | `stage3_orchestrator.py:1270-1278` -- When `three_phase_bp.generate()` raises an exception, the orchestrator catches it, logs, and returns `(None, {"final_verdict": "ERROR", ...})`. This flows to `_handle_failure`. No test exercises this path. | Missing test for the primary crash safety net |
| **Director error** | N/A | Stage 3 does not call Director directly -- Director is called inside `ThreePhaseBlueprintGenerator.generate()`. The orchestrator only receives the result tuple. | Not applicable at orchestrator level |
| **DB commit failure** | FINDING P3 | `_safe_commit` is mocked at `test_stage3_orchestrator.py:73` but never tested with `side_effect=Exception`. The `_handle_success` calls `ctx.safe_commit()` at `stage3_orchestrator.py` (after save_episode_blueprint) but a commit failure path is uncovered. | Low -- `_safe_commit` is a facade method with its own error handling |
| **save_cost_record failure** | OK | `stage3_orchestrator.py:1975` wraps in try/except. Not tested but non-blocking by design |
| **pass_rate_monitor.record_attempt failure** | OK | `stage3_orchestrator.py:1372,1884` wrapped in try/except. Non-blocking |

### 4. E2E integrated_scenario Length

**Status: FINDING**

| Item | Severity | Evidence | Description |
|------|----------|----------|-------------|
| **E2E mock blueprint** | P2 | `test_l3_stage3_smoke.py:76`: `integrated_scenario=f"Episode {ep_num}: {context[:120]}"`. The `context` variable comes from `content.get("context", "market pressure rises")` (line 69). For Arc data with no content, the fallback is "market pressure rises" (22 chars). So `integrated_scenario` = "Episode 1: market pressure rises" = ~31 chars. Even with real content, max is "Episode N: " + 120 chars = ~131 chars. | The production validator at `unified_blueprint_validator.py:31` enforces `BLUEPRINT_MIN_CHARS = 800`. The E2E test's mock blueprints are ~8-16x shorter than the minimum threshold. This means the E2E test would fail production validation but bypasses it because validation runs inside `ThreePhaseBlueprintGenerator.generate()` which is fully mocked. **This is a test realism gap** -- the E2E test proves the orchestrator pipeline works but does not validate that mock data is representative of production. |

### 5. Test Data

**Status: FINDING (minor)**

| Item | Severity | Evidence | Description |
|------|----------|----------|-------------|
| **tactical_doc "x"*600** | P3 | `test_stage3_orchestrator.py:28`: `"tactical_doc": "x" * 600`. The `_extract_arc_time_markers` method at `stage3_orchestrator.py:879-897` applies regex patterns like `\d{4}년\s*\d{1,2}월` to tactical_doc. "x"*600 will never match any pattern, so the time marker injection path is never exercised through this fixture data. | Minor -- this is expected for a unit test fixture (intentionally degenerate data). The time marker helper methods are tested independently in `TestNs4TimelineHelpers`. However, no integration test exercises the time marker injection flow with realistic tactical_doc content. |
| **state_extractor reference accuracy** | P3 | `test_stage3_orchestrator.py:38-42`: `app.agents` includes `"state_extractor"` key. The orchestrator at `stage3_orchestrator.py:818` accesses `ctx.agents["state_extractor"].extract_cumulative_state(...)`. This matches. However, the agent is accessed via `ctx.agents` (DI context) not `app.agents` directly. The `Stage3Context.from_app()` maps `app.agents` to `ctx.agents` (verified at `test_stage3_orchestrator.py:1026`), so the contract is correct. | OK |

---

## Summary

| Checklist Item | Status | Findings |
|----------------|--------|----------|
| 1. Coverage gaps | FINDING | 2x P2 (Treatment Block injection, gen_err crash path), 3x P3 (SC failure, NS-4 integration, ASP wiring) |
| 2. Mock contracts | FINDING (minor) | 1x P3 (state_extractor entity_registry list-of-str vs list-of-dict) |
| 3. Error paths | FINDING | 1x P2 (gen_err crash not tested), 1x P3 (DB commit failure) |
| 4. E2E integrated_scenario length | FINDING | 1x P2 (~131 chars vs BLUEPRINT_MIN_CHARS=800, test realism gap) |
| 5. Test data | FINDING (minor) | 1x P3 (tactical_doc "x"*600 never matches time marker regex) |

### Severity Breakdown

- **P0**: 0
- **P1**: 0
- **P2**: 3 (Treatment Block injection coverage, gen_err crash path, E2E scenario length realism)
- **P3**: 5 (SC failure path, NS-4 integration, ASP wiring, state_extractor mock shape, tactical_doc parseability)

### Overall Assessment

Stage 3 test coverage is **solid for the happy path and DI contracts** (43 unit tests + 5 E2E tests). The DI context mapping is thoroughly verified (10 tests in `TestStage3ContextDI`). Observability and metrics recording are well-covered.

The main gaps are in **error/crash paths** (gen_err exception during LLM generate, DB commit failure) and **semantic_context integration** (Treatment Block injection from plot_roadmap is untested). The E2E test uses mock blueprints far below the production minimum character threshold, which limits its value as a realism check.

No P0 or P1 findings. All P2 findings are test coverage gaps, not production bugs.
