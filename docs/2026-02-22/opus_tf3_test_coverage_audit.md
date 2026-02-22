# Opus TF3 Test Coverage Gap Analysis

> Date: 2026-02-22
> Auditor: Claude Opus 4.6
> Baseline: 2,266 passed + 68 xfailed (2,189 test functions across 120 test files)
> Production code: ~100,000 lines across 200 modules

---

## Executive Summary

The test suite covers **30% of production modules** by dedicated test file count (60/200).
The remaining 140 modules (68,102 production lines) have no dedicated test file.
While some are partially covered via sweep tests or integration tests, the **structural coverage gap is severe** in the following areas:

1. **Domain agents**: 29/47 agent modules untested (62%)
2. **Core infrastructure**: 86/113 core modules untested (76%)
3. **Validation pipeline**: 10/16 validators untested (63%)
4. **Strategies**: 8/8 strategy modules untested (100%)
5. **Stage 0**: 5/5 stage0 submodules untested (100%)

Test/Production ratio: **0.34** (34 test lines per 100 production lines). Industry standard for critical systems is 0.8-1.2.

---

## 1. Untested Critical Modules

### 1.1 Tier 1 -- Pipeline Core (Must-Test, Breaking Risk HIGH)

These are modules on the critical execution path. Bugs here crash the entire pipeline.

| Module | Lines | Risk | Notes |
|--------|-------|------|-------|
| `modules/core/adaptive_retry.py` | 860 | **CRITICAL** | Retry logic for all LLM calls. Failure = pipeline halt. No test at all. |
| `modules/core/project_manager.py` | 940 | **CRITICAL** | Project lifecycle, rollback, state management. Partially tested via `test_project_service` but no direct test. |
| `modules/core/stage2_orchestrator.py` | 826 | **CRITICAL** | Arc orchestration. Has `test_stage2_pipeline.py` (76 tests) but those test sub-components, not the orchestrator itself. |
| `modules/core/stage2_optimizer.py` | 898 | **HIGH** | Arc optimization. A-2 fixed TODOs but no regression test. |
| `modules/core/stage3_context.py` | 659 | **HIGH** | Stage3 DI context. No test despite Stage2/4 contexts having dedicated tests. |
| `modules/core/stage4_types.py` | varies | **MEDIUM** | Type definitions. Low risk but gap in typing contracts. |
| `modules/core/world_state.py` | 474 | **HIGH** | World state tracking. Only touched by `test_sweep22` (1 test). |
| `modules/core/state_delta_tracker.py` | 419 | **HIGH** | State delta tracking. No test. |
| `modules/validation/validation_orchestrator.py` | 1,522 | **CRITICAL** | Orchestrates all 3 tiers of validation. Only init test in `test_validation.py`, rest xfailed. |
| `modules/validation/scoring_validator.py` | 1,117 | **CRITICAL** | LLM-based scoring. Only mock tests exist, no actual scoring logic tested. |
| `modules/validation/continuity_validator.py` | 985 | **HIGH** | Cross-episode continuity. No test at all. |

### 1.2 Tier 2 -- Agent Layer (High-Value, Testing Gap)

| Module | Lines | Risk | Notes |
|--------|-------|------|-------|
| `modules/domain/agents/analyst.py` | 1,474 | **CRITICAL** | Genre analysis, NPC extraction. Zero tests. |
| `modules/domain/agents/continuity_manuscript.py` | 1,220 | **HIGH** | Manuscript continuity checking. Zero tests. |
| `modules/domain/agents/director_auditor.py` | 1,065 | **HIGH** | Quality audit. Only 2 sweep tests (sweep27). |
| `modules/domain/agents/continuity_arc.py` | 1,010 | **HIGH** | Arc continuity. Zero tests. |
| `modules/domain/agents/state_tracker_npc.py` | 2,006 | **CRITICAL** | NPC state tracking. Only 2 tests in `test_state_tracker_npc_sweep20.py`. |
| `modules/domain/agents/state_tracker_plots.py` | 944 | **HIGH** | Plot state tracking. Zero tests. |
| `modules/domain/agents/state_tracker_financial.py` | varies | **MEDIUM** | Financial state. Zero tests. |
| `modules/domain/agents/four_phase_arc_generator.py` | 825 | **HIGH** | 4-phase arc generation. Zero tests. |
| `modules/domain/agents/state_extractor.py` | 854 | **HIGH** | State extraction. Only tested via sweep32. |
| `modules/domain/agents/director_grading.py` | 680 | **HIGH** | Director scoring. Zero dedicated tests. |
| `modules/domain/agents/blueprint_ensemble.py` | 681 | **HIGH** | Blueprint ensemble strategy. Zero tests. |
| `modules/domain/agents/arc_ensemble.py` | 709 | **HIGH** | Arc ensemble strategy. Zero tests. |
| `modules/domain/agents/critic.py` | 714 | **HIGH** | Critic agent. Zero tests. |
| `modules/domain/agents/block_enricher.py` | 871 | **MEDIUM** | Block enrichment. Zero tests. |
| `modules/domain/agents/unified_arc_validator.py` | 635 | **HIGH** | Arc validation, MAJOR/CRITICAL classification. Zero tests. |
| `modules/domain/agents/unified_blueprint_validator.py` | 428 | **HIGH** | Blueprint validation. Zero tests. |
| `modules/domain/agents/weaver.py` | 373 | **MEDIUM** | Story weaving. Zero tests. |
| `modules/domain/agents/writer.py` | 373 | **LOW** | Writer agent. Partially tested via chief_writer tests. |

### 1.3 Tier 3 -- Supporting Infrastructure

| Module | Lines | Risk | Notes |
|--------|-------|------|-------|
| `modules/core/quality_dashboard.py` | 1,100 | **MEDIUM** | Dashboard/reporting. Zero tests. |
| `modules/core/pattern_tracker.py` | 936 | **MEDIUM** | Pattern tracking. Only 1 sweep test. |
| `modules/core/pass_rate_monitor.py` | 550 | **MEDIUM** | Pass rate monitoring. Zero tests. |
| `modules/core/tree_of_thoughts.py` | 730 | **MEDIUM** | ToT reasoning. Zero tests. |
| `modules/core/manuscript_enhancer.py` | 788 | **MEDIUM** | Post-enhancement. Zero tests. |
| `modules/core/genre_hud_manager.py` | 751 | **MEDIUM** | HUD management. Zero tests. |
| `modules/core/semantic_item_registry.py` | 781 | **MEDIUM** | Item registry. Zero tests. |
| `modules/core/response_schemas.py` | 593 | **LOW** | Schema definitions. Zero tests. |
| `modules/core/stage0/reverse_expander.py` | 1,150 | **MEDIUM** | Reverse expansion. Zero tests. |
| `modules/core/stage0/style_extractor.py` | 772 | **MEDIUM** | Style extraction. Zero tests. |
| `modules/core/stage0/preset_registry.py` | 714 | **MEDIUM** | Genre presets. Zero tests. |
| `modules/core/stage0/story_expander.py` | 556 | **MEDIUM** | Story expansion. Only 1 sweep28 test. |
| `modules/core/stage0/spinner.py` | 666 | **LOW** | UI spinner. Zero tests. |

### 1.4 Strategy Layer -- 100% Untested

All 8 strategy modules have zero tests:

| Module | Lines |
|--------|-------|
| `modules/domain/strategies/wuxia_strategy.py` | 42 |
| `modules/domain/strategies/hunter_strategy.py` | 41 |
| `modules/domain/strategies/investment_strategy.py` | 42 |
| `modules/domain/strategies/composer_strategy.py` | 43 |
| `modules/domain/strategies/cooking_strategy.py` | 43 |
| `modules/domain/strategies/medical_strategy.py` | 43 |
| `modules/domain/strategies/sports_strategy.py` | 43 |
| `modules/domain/strategies/base_strategy.py` | 18 |

These are small but critical for genre-specific behavior. A single parametrized test covering all strategies would close this gap.

---

## 2. Mocking Overreliance vs Integration Test Deficit

### 2.1 Mock-Heavy Tests (Real Integration Never Verified)

Total mock references across test suite: **2,585 lines** referencing Mock/MagicMock/patch.
Total assert statements: **3,841**.

**Key concern**: Many test files construct elaborate mocks that may not reflect actual API contracts.

| Pattern | Count | Risk |
|---------|-------|------|
| `MagicMock()` as agent constructor arg | ~200+ | Agent signatures changed (DI refactor); mocks don't catch drift |
| `mock_response.text = json.dumps(...)` | ~50+ | Real LLM responses have different structure/edge cases |
| `hasattr(x, 'method')` conditional in tests | 22 | Tests skip assertions if API changed -- silently passing |
| `if hasattr(validator, "validate"):` | 3 | Validator tests don't actually call validate() |

### 2.2 Integration Gaps

| Gap | Details |
|-----|---------|
| Stage 2 -> 3 handoff | No test verifies arc data flows correctly into blueprint generation |
| Stage 3 -> 4 handoff | No test verifies blueprint data flows correctly into manuscript generation |
| NPC state across episodes | `test_npc_continuity_e2e.py` exists but is the only cross-episode NPC test |
| Validation orchestrator with real validators | All 3-tier validation tests use mocks; no integration test runs blocking -> scoring -> advisory chain |
| DB + Agent interaction | DBManager tested in isolation; agent tests mock DB entirely |
| Guard chain (Genre -> Work -> Style) | Individual guards tested, but chain composition untested |

### 2.3 Specific Mock Fragility Examples

1. **`test_agents.py`**: Entire file (23 tests) marked `xfail(run=False)` because `BaseAgent.__init__` signature changed from `(config)` to `(context, client)`. These tests never run.

2. **`test_validation.py`**: 13 of 25 tests are xfailed with reason "V44 API 변경 후 미갱신". The validation API was changed but tests were never updated -- they were just xfailed.

3. **`test_edge_cases.py`**: 8 xfails, mostly "Windows SQLite file lock". The DB handle cleanup issue is a fixture problem, not a production problem, but it prevents these tests from running.

---

## 3. Edge Case Coverage Analysis

### 3.1 Existing Edge Case Coverage

`test_edge_cases.py` covers:
- Empty string manuscript (xfail)
- Very long manuscript 999,999 chars (xfail)
- Unicode special characters (passes)
- Null/None values (passes)
- Negative numbers (passes)
- Deep nesting 10 levels (passes)
- Large arrays 10,000 elements (passes)
- Concurrent read/write (no assertion)

### 3.2 Missing Edge Cases

| Category | Missing Test | Risk |
|----------|-------------|------|
| **Empty/None input to agents** | No agent tested with None/empty manuscript, blueprint, or arc | HIGH -- LLM calls with empty prompts waste API quota |
| **Malformed LLM responses** | Only 1 test (sweep4) checks malformed JSON from LLM | CRITICAL -- real LLMs return malformed JSON frequently |
| **API timeout/retry exhaustion** | `test_edge_cases.py` has xfailed timeout test, retry exhaustion untested | HIGH -- retry exhaustion should gracefully fail |
| **Concurrent episode writes** | `test_concurrent_read_write` has no assertions | MEDIUM |
| **HUD with extreme values** | No test for internal_energy=999999 or negative martial_root | LOW |
| **Empty NPC list** | No agent tested with zero NPCs in encyclopedia | MEDIUM |
| **Unicode in NPC names** | Tested for DB storage, not for guard validation | MEDIUM |
| **Circular relationship references** | NPC A -> B -> A relationship cycle | LOW |
| **Duplicate episode numbers** | No test for re-generating an existing episode | MEDIUM |
| **Missing YAML prompt files** | `test_prompt_loader.py` exists but missing file fallback untested | HIGH |
| **Genre guard with mixed-genre text** | Guards tested individually, not with text containing terms from multiple genres | MEDIUM |

---

## 4. Regression Test Gap for Audit Fixes

### 4.1 Sweep Tests as Regression Coverage

193 sweep-related test functions exist across 22 sweep files. These provide regression coverage for specific bugs found during debug sweeps 1-12.

**However**, sweep tests have structural issues:
- They are numbered by sweep batch, not by module -- making it hard to find which module is covered.
- Some sweep tests only verify patterns in source code (grep-style) rather than runtime behavior.
- `test_sweep38.py`: 6 tests all read source files and check patterns -- no runtime testing.

### 4.2 Audit Fixes Without Regression Tests

Based on the Opus TF audit (Phases R1-R5, Sweep 1-12), the following fixes lack regression tests:

| Fix | Module | Test Status |
|-----|--------|-------------|
| R1-R3 monster function splits | `stage4_orchestrator`, `chief_writer` | Covered by submodule tests |
| R5 2nd-round splits | `stage2_validation_pipeline`, `stage2_finalizer`, `stage2_preflight` | Covered |
| DB-SSOT VecMemory merge | `vec_memory.py` | `test_vec_memory.py` covers (36 tests) |
| Patch Mode Stage 2/3 | `stage2_orchestrator`, `stage3_orchestrator` | `test_arc_patch_mode.py`, `test_blueprint_patch_mode.py` cover |
| Passrate strategy retry | `adaptive_retry.py`, `pass_rate_monitor.py` | **NO dedicated test** |
| Ensemble Feedback | `stage2_orchestrator` | Only via sweep tests |
| Protocol standardization (B-3) | `protocols/*.py` | `test_protocol_conformance.py`, `test_protocols.py` cover |
| NPC over-appearance warning (3-5C) | `state_tracker_npc.py` | Only 2 tests in `test_state_tracker_npc_sweep20.py` |
| Cross-episode repetition (3-B) | `repetition_guard.py` | `test_cross_episode_repetition.py` covers (13 tests) |
| Quality regression detection (3-QR) | `quality_dashboard.py` | **NO dedicated test** |
| Satisfaction framework (D.Steps1-5) | Multiple modules | Covered: 75 tests across 4 satisfaction test files |
| Director selection tracker (D-4) | `db_manager.py` | `test_selection_tracker.py` covers (11 tests) |
| NPC rollback (D-2) | `project_manager.py` | `test_rollback_npc.py` covers (13 tests) |
| StyleGuard auto-generation (D-3) | `style_guard.py` | `test_style_guard.py` covers (12 tests) |

### 4.3 Critical Untested Audit Fixes

1. **`adaptive_retry.py` (860 lines)** -- Passrate strategy retry logic was a major feature. No test verifies retry escalation, backoff timing, or model fallback behavior.

2. **`pass_rate_monitor.py` (550 lines)** -- Pass rate monitoring for quality control. No test verifies threshold alerts or historical tracking.

3. **`quality_dashboard.py` (1,100 lines)** -- Quality regression detection (3-QR). No test verifies regression alerts.

---

## 5. xfail Analysis (68 Tests)

### 5.1 Breakdown by Reason

| Reason | Count | Category |
|--------|-------|----------|
| "V44 API 변경 후 미갱신" | 13 | **Permanent** -- API changed, tests never updated |
| "DBManager API drift + Windows SQLite file lock" (run=False) | 7 | **Permanent** -- Tests don't even execute |
| "Windows SQLite file lock" | 5+5 | **Environmental** -- Fixture cleanup issue |
| "Windows SQLite file lock - DB handle not closed" | 5 | **Environmental** -- Fixture cleanup issue |
| "BaseAgent.__init__ signature changed" | 3 | **Permanent** -- DI refactor broke constructor |
| "Agent constructor/API signatures changed" (run=False) | 1 (module-level, covers 23 tests) | **Permanent** -- Entire file disabled |
| "BlockingValidator behavior changed" | 1 | **Permanent** -- Validator API changed |
| "load_anchor returns {} instead of None" | 1 | **Permanent** -- Return type changed |

### 5.2 Classification

| Type | Count | Action |
|------|-------|--------|
| **Permanent xfail (API changed, never updated)** | 45 | Rewrite tests to match current API |
| **Environmental (Windows SQLite file lock)** | 15 | Fix fixture cleanup to close DB handles properly |
| **Module-level xfail (entire file disabled)** | 23 | Rewrite `test_agents.py` with current DI constructor |
| **Behavioral (run=False)** | 7 | Tests not executed at all -- dead code |

### 5.3 Quick Wins for xfail Resolution

1. **Windows SQLite file lock (15 tests)**: Add `db.close()` in `try/finally` in conftest fixtures. This is a fixture bug, not a production bug.

2. **test_agents.py (23 tests)**: Rewrite with `BaseAgent(context, client)` constructor instead of `BaseAgent(config)`. The tests themselves are valuable but use the wrong constructor.

3. **test_validation.py (13 tests)**: Update `BlockingValidator` call signature. The validator no longer takes `(ep_num, text, context)` -- update to current API.

4. **load_anchor returns {} instead of None (1 test)**: Change assertion from `assert result is None` to `assert result == {}` or verify actual return contract.

---

## 6. Test Quality Analysis

### 6.1 Weak/Empty Tests

**121 test functions** have no assertions or only contain `pass`. These are "phantom tests" that inflate the pass count without verifying anything.

Top offenders:
| File | Empty/Weak Tests | Total Tests | Phantom Rate |
|------|-----------------|-------------|--------------|
| `test_stage01_helpers.py` | 19 | 29 | 66% |
| `test_project_service.py` | 8 | 17 | 47% |
| `test_stage3_orchestrator.py` | 7 | 38 | 18% |
| `test_stage4_post_processor.py` | 6 | 20 | 30% |
| `test_edge_cases.py` | 6 | 30 | 20% |
| `test_martial_manager.py` | 6 | 23 | 26% |
| `test_validation.py` | 9 | 25 | 36% |
| `test_agents.py` | 10 | 23 | 43% |
| `test_stage2_context.py` | 2 | 16 | 13% |
| `test_stage4_context.py` | 3 | 30 | 10% |

**Impact**: 121 of 2,189 test functions (5.5%) are phantom tests. The real pass count is closer to **~2,068** rather than 2,266.

### 6.2 hasattr Conditional Tests

22 test locations use `if hasattr(obj, 'method'):` to conditionally execute assertions. This means:
- If the API method is removed, the test silently passes.
- No assertion failure ever triggers.
- These are worse than empty tests because they create false confidence.

### 6.3 Test Isolation Issues

| Issue | Details |
|-------|---------|
| `sys.path.insert` in test files | Multiple test files manually insert project root. This is a conftest responsibility, not per-file. |
| Shared fixture state | Some tests modify fixtures (e.g., `validation_context["encyclopedia"] = None`) without deepcopy, potentially affecting other tests. |
| No test ordering guarantee | Concurrent DB tests may interfere without proper isolation. |

### 6.4 Flaky Test Risk

| Risk Factor | Count | Notes |
|-------------|-------|-------|
| Threading in tests | 3 tests | `test_concurrent_read_write`, `test_concurrent_access_safety` -- no assertions on thread results |
| Temporary directory race | 0 known | `temp_dir` fixture uses `tempfile.TemporaryDirectory` correctly |
| Time-dependent tests | 0 known | No `time.sleep` or date-dependent assertions found |
| File system dependent | 15 xfails | Windows SQLite file lock issue |

---

## 7. Recommended Test Additions (Priority Order)

### P0 -- Immediately Required (Pipeline Safety)

| # | Test Target | Estimated Tests | Rationale |
|---|------------|-----------------|-----------|
| 1 | `adaptive_retry.py` | 15-20 | Retry exhaustion, backoff timing, model fallback, quota handling. Zero coverage for 860 lines of critical retry logic. |
| 2 | `validation_orchestrator.py` | 10-15 | 3-tier cascade (blocking -> scoring -> advisory), short-circuit on REJECT, genre-specific routing. 1,522 lines, only init tested. |
| 3 | `scoring_validator.py` | 10-15 | Score calculation, threshold boundary, weighted scoring, malformed LLM response handling. 1,117 lines. |
| 4 | `continuity_validator.py` | 10-12 | Cross-episode state consistency, NPC death tracking, location destruction. 985 lines, zero tests. |
| 5 | `analyst.py` | 10-15 | Genre analysis, NPC extraction, arc recommendation. 1,474 lines, zero tests. Largest untested agent. |

### P1 -- High Priority (Quality Assurance)

| # | Test Target | Estimated Tests | Rationale |
|---|------------|-----------------|-----------|
| 6 | `state_tracker_npc.py` | 15-20 | 2,006 lines, only 2 tests. NPC state is core to continuity. |
| 7 | `continuity_manuscript.py` | 10-12 | 1,220 lines, zero tests. Manuscript continuity checking. |
| 8 | `director_auditor.py` | 8-10 | 1,065 lines, only 2 sweep tests. Quality audit logic. |
| 9 | `project_manager.py` | 10-12 | 940 lines. Project lifecycle, rollback. Partially covered via services. |
| 10 | `pass_rate_monitor.py` | 8-10 | 550 lines. Quality threshold monitoring. |
| 11 | `quality_dashboard.py` | 8-10 | 1,100 lines. Quality regression detection (3-QR feature). |
| 12 | `stage3_context.py` | 5-8 | DI context parity with Stage2/4 contexts (both have tests). |

### P2 -- Medium Priority (Completeness)

| # | Test Target | Estimated Tests | Rationale |
|---|------------|-----------------|-----------|
| 13 | `four_phase_arc_generator.py` | 8-10 | 825 lines, core arc generation. |
| 14 | `arc_ensemble.py` + `blueprint_ensemble.py` | 10-12 | Ensemble selection strategy. |
| 15 | `unified_arc_validator.py` | 8-10 | MAJOR/CRITICAL classification changed in V62. |
| 16 | `critic.py` | 5-8 | 714 lines, critic feedback. |
| 17 | `stage0/reverse_expander.py` | 8-10 | 1,150 lines, reverse expansion logic. |
| 18 | `stage0/style_extractor.py` | 5-8 | 772 lines, style cloning. |
| 19 | `genre_hud_manager.py` | 8-10 | 751 lines, all 9 genre HUD managers. |
| 20 | All 8 strategies (parametrized) | 5-8 | Small but critical. One parametrized test. |

### P3 -- xfail Resolution

| # | Action | Estimated Effort |
|---|--------|-----------------|
| 21 | Fix Windows SQLite file lock (fixture cleanup) | 1 hour -- add `db.close()` to fixtures |
| 22 | Rewrite `test_agents.py` with current DI constructor | 2-3 hours |
| 23 | Update `test_validation.py` to current BlockingValidator API | 2 hours |
| 24 | Remove `run=False` xfails (test_db_manager 7 tests) | 1-2 hours |
| 25 | Add assertions to 121 phantom tests | 4-6 hours |

---

## 8. Coverage Heat Map

```
                        Coverage Level
Module Area             [===  LOW  ===] [== MED ==] [= HIGH =]
------------------------------------------------------------
modules/core/services/  ########################################  ~80%
modules/core/stage4_*   ############################              ~60%
modules/core/stage2_*   ########################                  ~50%
modules/validation/     ############                              ~25%
modules/core/ (other)   ########                                  ~15%
modules/domain/agents/  ######                                    ~12%
modules/core/stage0/    ##                                        ~5%
modules/core/genre_guards/ #####                                  ~10%
modules/domain/strategies/ (none)                                 ~0%
modules/protocols/      ################                          ~40%
```

---

## 9. Structural Recommendations

### 9.1 Test Organization

**Current**: Flat structure with 100+ test files in `tests/`. Sweep tests numbered by batch, not by module.

**Recommended**: Group tests by module path:
```
tests/
  core/
    test_adaptive_retry.py
    test_project_manager.py
    ...
  domain/
    agents/
      test_analyst.py
      test_continuity_manuscript.py
      ...
    strategies/
      test_strategies.py  (parametrized)
  validation/
    test_scoring_validator.py
    test_continuity_validator.py
    ...
  e2e/
    (existing)
```

### 9.2 Fixture Improvements

1. **DB fixture cleanup**: All DB-using fixtures should use `try/finally` to ensure `db.close()` is called.
2. **Agent factory fixture**: Create a universal agent fixture using the current DI constructor `(context, client)`.
3. **LLM response factory**: Create a fixture that generates realistic malformed/valid LLM responses.

### 9.3 Mock Strategy

1. **Replace hasattr conditionals** with direct assertions. If an API method doesn't exist, the test should fail, not skip.
2. **Create protocol-based mocks** using `modules/protocols/` as the contract source.
3. **Add contract tests** that verify mock objects match production interfaces.

---

## 10. Summary Statistics

| Metric | Value |
|--------|-------|
| Total production modules | 200 |
| Modules with dedicated tests | 60 (30%) |
| Modules without any test | 140 (70%) |
| Total production lines | ~100,000 |
| Untested production lines | ~68,102 (68%) |
| Total test functions | 2,189 |
| Phantom tests (no assertions) | 121 (5.5%) |
| Effective test functions | ~2,068 |
| xfail tests | 68 (35 per-method + 23 module-level + 10 environmental) |
| xfail tests that never execute (run=False) | 30 |
| xfail tests fixable with fixture cleanup | 15 |
| Test/Production ratio | 0.34 |
| Mock references | 2,585 lines |
| hasattr conditionals in tests | 22 |
| Sweep regression tests | 193 |

---

## End of Audit

This document is research-only. No code changes were made.
