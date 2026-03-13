# TF-S4DD Track 5: Test Coverage & Config Alignment Findings

**Date**: 2026-03-13
**Scope**: Stage 4 code — orchestrator, interview_round, context_builder, post_processor
**Status**: Read-only audit (no code changes)

---

## 5.1 Coverage Gaps — Public & Key Method Inventory

### Stage4Orchestrator (`modules/core/stage4_orchestrator.py`)

| Method | Tested? | Test Location |
|--------|---------|---------------|
| `stage_4_v2_chief_writer()` | YES | `tests/e2e/test_l3_stage4_smoke.py`, `tests/test_chief_writer.py` |
| `ctx` (property get/set) | YES | `tests/test_stage4_context.py` |
| `post_processor` (property) | YES | `tests/test_stage4_post_processor.py` |
| `context_builder` (property) | YES | `tests/test_stage4_context_builder.py` |
| `interview_round` (property) | YES | `tests/test_stage4_interview_round.py` |
| `_preflight_validate_blueprint()` | YES | `tests/test_blueprint_preflight.py` (14 tests) |
| `_extract_chain_link()` | YES | `tests/test_stage4_context.py` |
| `_run_interview_loop()` | PARTIAL | e2e smoke test only (mocks `_handle_round_outcome`) |
| `_handle_round_outcome()` | PARTIAL | `tests/test_stage4_orchestrator.py` (inject/feedback tests) |
| `_prepare_stage4_session()` | PARTIAL | e2e smoke test only (fully mocked) |
| `_set_agent_telemetry_context()` | NO | **GAP** |
| `_build_stage4_to_3_reverse_feedback()` | NO | **GAP** — tested implicitly via `_handle_round_outcome` test but no direct unit test |
| `_merge_blueprint_feedback()` | NO | **GAP** — static method, no direct test |
| `_register_bible_world_laws()` | NO | **GAP** |
| `_log_escalation_event()` | YES | `tests/test_stage4_orchestrator.py` (via log dir test) |
| `_regenerate_blueprint()` | YES | `tests/test_stage4_orchestrator.py` |
| `_detect_npc_overexposure()` (module-level) | YES | 10+ tests in `tests/test_stage4_orchestrator.py` |
| `_detect_cross_episode_repetition()` (module-level) | YES | 3 tests in `tests/test_stage4_orchestrator.py` |

### Stage4InterviewRound (`modules/core/stage4_interview_round.py`)

| Method | Tested? | Test Location |
|--------|---------|---------------|
| `run()` | YES | `tests/test_stage4_interview_round.py` (PASS/REJECT/EMPTY/patch paths) |
| `_generate_candidates()` | YES | 5 tests in `test_stage4_interview_round.py` |
| `_run_post_select_checks()` | YES | 3 tests (continuity/history/no-conflict) |
| `_execute_pass_with_fix_loop()` | YES | `tests/test_pass_with_fix.py` (7+ tests) |
| `_process_verdict()` | YES | 1 test (reaudit score) |
| `_handle_reject()` | YES | 4 tests (firewall continuity/numeric, force patch) |
| `_record_s4_attempt()` | YES | 6+ tests |
| `_append_episode_log()` | YES | 7+ tests |
| `_build_retry_advisory_digest()` | INDIRECT | Covered via run() REJECT path test |
| `_merge_retry_advisory_feedback()` | YES | 1 direct test |
| `_build_cv_context()` | YES | `test_stage4_cv_context.py` (15+ tests) |
| `_resolve_npc_profiles()` | INDIRECT | Tested via `_build_cv_context` path only |
| `_run_advisory_chain()` | NO (always mocked) | **GAP** — always `MagicMock(return_value=[...])` in tests |
| `_advisory_truth_gate()` | NO | **GAP** — tested separately in `tests/test_truth_gate.py` for the TruthGate class, but not the interview_round wrapper |
| `_advisory_npc_drift()` | NO | **GAP** — same pattern |
| `_advisory_numeric_drift()` | NO | **GAP** |
| `_advisory_flashback()` | NO | **GAP** |
| `_advisory_info_paradox()` | NO | **GAP** |
| `_advisory_rel_drift()` | NO | **GAP** |
| `_advisory_long_term_rep()` | NO | **GAP** |
| `_advisory_numeric_consistency()` | NO | **GAP** |
| `_build_db_pacing_advisory()` | YES | `tests/test_db_utilization.py` |
| `_build_db_satisfaction_advisory()` | YES | `tests/test_db_utilization.py` |
| `_build_db_reveals_advisory()` | YES | `tests/test_db_utilization.py` |
| `_build_db_reflexion_advisory()` | YES | `tests/test_db_utilization.py` |
| `_setup_writing_directive()` | NO | **GAP** |
| `_build_common_writer_kwargs()` | INDIRECT | Verified via `test_stage234_fixes.py` source-level check only |
| `_run_pre_director_validation()` | NO | **GAP** |
| `_classify_reject_bucket()` | NO | **GAP** — static method |
| `_suppress_conflicting_advisories()` | YES | 1 test |
| `_build_candidate_diversity_advisory()` | YES | 1 test |
| `_summarize_candidate_diversity()` | YES | 1 test |
| `_detect_shared_failure_warnings()` | YES | 1 test |
| `_build_director_relationship_context()` | INDIRECT | Tested via sc5 director tests |
| `_is_continuity_replay_reject()` | INDIRECT | Tested via firewall tests |
| `_compose_director_work_focus_text()` | INDIRECT | Tested via sc5 tests |
| `_build_round_attempt_key()` | YES | 1 test |
| `_log_round_outcome()` | YES | 1 test |

### Stage4ContextBuilder (`modules/core/stage4_context_builder.py`)

| Method | Tested? | Test Location |
|--------|---------|---------------|
| `load_chain_link_section()` | YES | 4 tests |
| `build_extended_lookback_digest()` | YES | 3 tests |
| `prepare_episode_context()` | YES | 12+ tests (hybrid tiers, early episodes) |
| `compute_scene_similarity_advisory()` | YES | `tests/test_nc2_gaps.py` |
| `build_mandatory_context()` | YES | 12+ tests (writer guidance, SPG, advisor, budget, relation slice) |
| `build_round_context()` | YES | 1 test |
| `_resolve_protagonist_name()` | INDIRECT | Covered via other tests |
| `_extract_npc_tokens()` | NO | **GAP** — static method |
| `_collect_npc_roster()` | YES | 1 test (scene_breakdown dict) |
| `_collect_arc_state_entities()` | INDIRECT | Via `_extract_blueprint_entities` test |
| `_suggest_ambient_npcs()` | YES | 4 tests |
| `_extract_blueprint_entities()` | YES | 1 test |
| `_build_npc_boundary_block()` | YES | 1 test |
| `_build_continuity_packet()` | NO | **GAP** |
| `_compose_work_focus_text()` | INDIRECT | Via build_mandatory_context |
| `_resolve_work_retrieval_focus()` | INDIRECT | Via build_mandatory_context |
| `_build_work_identity_slot_summary()` | INDIRECT | Via build_mandatory_context |
| `_execute_retrieval_plan()` | YES | 1 test (slot_max_chars) |
| `_apply_context_budget()` | YES | 2 tests |
| `_compose_mandatory_context_with_headroom()` | YES | 1 test (via build_mandatory_context rebalance) |
| `_build_condensed_world_state_summary()` | NO | **GAP** |
| `_build_condensed_fact_ledger_summary()` | NO | **GAP** |
| `_fetch_manuscript_excerpt()` | NO | **GAP** |
| `_parse_ep_range_from_query()` | NO | **GAP** |
| `_build_future_arc_context()` | NO | **GAP** (mocked in headroom test) |
| `_prioritize_summaries_by_work_focus()` | NO | **GAP** |

### Stage4PostProcessor (`modules/core/stage4_post_processor.py`)

| Method | Tested? | Test Location |
|--------|---------|---------------|
| `process_pass_result()` | YES | 18+ tests in `test_stage4_post_processor.py` |
| `run_post_episode_tasks()` | YES | 3 tests (vector sync) |
| `_report_soft_failure()` | YES | 1 test (soft failure logging) |
| `_extract_state_change_info()` | INDIRECT | Via process_pass_result |
| `_parse_hud_capital_to_eok()` | INDIRECT | Via reconcile tests |
| `_extract_capital_from_manuscript()` | YES | 8 tests |
| `_reconcile_capital()` | YES | 4 tests |
| `_submit_manager_async()` | INDIRECT | Via process_pass_result (manager_sync_retry test) |
| `_memorize_and_validate()` | NO | **GAP** |
| `_collect_manager_and_build_delta()` | NO | **GAP** |
| `_save_world_state_atomic()` | YES | 2 tests (transaction wrap/rollback) |
| `_run_post_pass_advisories()` | NO | **GAP** |

---

## 5.1 Summary

**Total distinct methods across 4 files**: ~105
**Directly tested**: ~58 (55%)
**Indirectly tested** (via caller): ~18 (17%)
**No test coverage**: ~29 (28%)

### Critical coverage gaps (high-impact methods with no test):

1. **`_run_advisory_chain()`** — Always mocked in interview_round tests; the actual dispatch logic is untested.
2. **All 8 `_advisory_*()` wrappers** in interview_round — Each wraps an external advisor but the wiring (argument construction, error handling, result formatting) is never tested.
3. **`_run_pre_director_validation()`** — Pre-director validation pipeline invocation in interview_round (complex orchestration logic).
4. **`_setup_writing_directive()`** — WritingDirective setup before candidate generation.
5. **`_build_condensed_world_state_summary()`** and **`_build_condensed_fact_ledger_summary()`** — Core context assembly with no tests.
6. **`_memorize_and_validate()`** and **`_collect_manager_and_build_delta()`** in post_processor — Post-PASS state persistence logic.
7. **`_run_post_pass_advisories()`** — Post-pass advisory execution.

---

## 5.2 Hardcoded Thresholds in Tests

| Test File | Line | Hardcoded Value | Likely Config Key | Risk |
|-----------|------|-----------------|-------------------|------|
| `test_stage4_orchestrator.py:115` | `PatchModeThresholds.INPLACE == 60` | 60 | `patch_mode.inplace_below` | LOW — uses constants.py constant, which reads yaml |
| `test_stage4_interview_round.py:214` | `threshold=0.6` | 0.6 | (internal param, no yaml key) | NONE — test param |
| `test_stage4_interview_round.py:384,413` | `"score": 90` | 90 | `scoring.quality_gate_score` | MEDIUM — if yaml changes from 90, test semantics shift |
| `test_stage4_interview_round.py:340,978,1012,1210` | `"score": 70` | 70 | `scoring.genre_thresholds.wuxia` | LOW — used as arbitrary previous score, not threshold assertion |
| `test_stage4_interview_round.py:2337` | `quality_gate_score=90` | 90 | `scoring.quality_gate_score` | MEDIUM — directly hardcodes QG score |
| `test_stage4_interview_round.py:2483` | comment mentioning `1500` | 1500 | `smart_retrieval.slot_max_chars_default` | MEDIUM — yaml now 3000, comment references old value |
| `test_stage4_context_builder.py:788` | `threshold_side_effect` returns `16` for `vector_max_results_s4` | 16 | `context.vector_max_results_s4` | LOW — test overrides via mock |

### Assessment
Most tests do not directly read from `validation.yaml`; they either use `constants.py` re-exports or mock `_threshold()`. Two instances of `90` (quality_gate_score) are hardcoded as test expectations rather than reading from config. If `scoring.quality_gate_score` changes, these tests would need manual update.

---

## 5.3 Config Alignment — `_threshold()` Default vs YAML

### Mismatches Found (default != yaml value)

| File | Key | Default in Code | YAML Value | Severity |
|------|-----|----------------|------------|----------|
| `stage4_orchestrator.py:933` | `retry.director_max_attempts` | **5** | **10** | **HIGH** — Code default is half the yaml value. If yaml fails to load, retry budget drops to 5. |
| `stage4_orchestrator.py:794` | `context.mandatory_context_max` | **80000** | **400000** | **HIGH** — 5x difference. Fallback would severely truncate context. |
| `stage4_context_builder.py:1448` | `context.mandatory_context_max` | **80000** | **400000** | **HIGH** — Same as above, different call site. |
| `stage4_context_builder.py:1562` | `context.lookback_excerpt_chars` | **500** | **5000** | **HIGH** — 10x difference. Lookback excerpts would be severely truncated on fallback. |
| `stage4_context_builder.py:1590` | `context.lookback_total_chars` | **4000** | **40000** | **HIGH** — 10x difference. Same pattern. |
| `stage4_context_builder.py:1213` | `context.vector_max_results_s4` | **20** | **50** | **MEDIUM** — Fallback yields fewer vector results. |
| `stage4_context_builder.py:1345` | `smart_retrieval.stage4_total_budget` | **50000** | **300000** | **HIGH** — 6x difference. |
| `stage4_interview_round.py:2310` | `context.vector_max_results_s4` | **20** | **50** | **MEDIUM** — Same key, different call site. |
| `stage4_interview_round.py:2311` | `smart_retrieval.slot_max_chars_default` | **1500** | **3000** | **MEDIUM** — 2x difference. |
| `stage4_interview_round.py:2371` | `smart_retrieval.director_total_budget` | **20000** | **300000** | **HIGH** — 15x difference. |
| `stage4_context_builder.py:1267` | `smart_retrieval.dense_k` | **10** | **20** | **MEDIUM** — Halved recall on fallback. |

### Matches (default == yaml)

| Key | Code Default | YAML | Status |
|-----|-------------|------|--------|
| `npc_exposure.max_mentions_per_episode` | 15 | 15 | OK |
| `cross_episode_repetition.overlap_warning` | 3 | 3 | OK |
| `cross_episode_repetition.overlap_regression` | 6 | 6 | OK |
| `blueprint_preflight.enabled` | True | true | OK |
| `blueprint_preflight.min_episode` | 2 | 2 | OK |
| `patch_mode.inplace_min_samples` | 5 | 5 | OK |
| `pattern_tracker.enable` | True | true | OK |
| `pattern_tracker.lookback_episodes` | 5 | 5 | OK |
| `patch_mode.inplace_below` | 60 | 60 | OK |
| `patch_mode.min_patched_length` | 2000 | 2000 | OK |
| `patch_mode.inplace_min_preserve_ratio` | 0.70 | 0.70 | OK |
| `patch_mode.inplace_max_change_ratio` | 0.30 | 0.30 | OK |
| `scoring.quality_gate_score` | 90 | 90 | OK |
| `feature_flags.enable_patch_mode` | True | true | OK |
| `smart_retrieval.max_npcs_per_slot` | 5 | 5 | OK |
| `smart_retrieval.rrf_k` | 60 | 60 | OK |
| `context.timeline_budget` | 3000 | 3000 | OK |
| `context.canonical_facts_budget` | 13000 | 13000 | OK |
| `npc_exposure.min_name_length` | 2 | 2 | OK |
| `cross_episode_repetition.enabled` | True | true | OK |
| `cross_episode_repetition.lookback_episodes` | 5 | 5 | OK |
| `cross_episode_repetition.min_sentence_length` | 15 | 15 | OK |

### Root Cause
The defaults were likely set at original implementation time and never updated when yaml values were subsequently increased (particularly the `[1M-CTX-P0]` context expansion and `[감리3차]` budget normalization). The code defaults represent pre-expansion conservative values.

### Risk
If `validation.yaml` fails to load (file missing, parse error), the system silently falls back to defaults that are **5-15x lower** than intended for context budgets. This would produce truncated prompts with dramatically reduced context, degrading output quality without any visible error.

---

## 5.4 Feature Flags

### Defined in `validation.yaml` under `feature_flags:`

| Flag | YAML Value | Consumed? | Consumer |
|------|-----------|-----------|----------|
| `enable_patch_mode` | true | YES | `stage4_interview_round.py:3371` |
| `enable_state_text_verifier` | true | YES | `stage4_post_processor.py:968` |

### Defined in `validation.yaml` under `smart_retrieval:`

| Flag | YAML Value | Consumed? | Notes |
|------|-----------|-----------|-------|
| `enabled` | true | YES | Multiple call sites in context_builder and interview_round |
| `stage2_enabled` | true | YES | `stage2_context.py` (out of scope) |
| `stage3_enabled` | true | YES | `stage3_orchestrator.py` (out of scope) |
| `stage4_enabled` | true | YES | context_builder:2324, interview_round:2269 |
| `director_enabled` | true | YES | interview_round:2270 |

### Default Mismatch for Boolean Flags

| Flag | Code Default | YAML | Risk |
|------|-------------|------|------|
| `smart_retrieval.enabled` | **False** | **true** | HIGH — Fallback disables smart retrieval entirely |
| `smart_retrieval.stage4_enabled` | **False** | **true** | HIGH — Same pattern |
| `smart_retrieval.director_enabled` | **False** | **true** | HIGH — Same pattern |
| `feature_flags.enable_state_text_verifier` | **False** | **true** | MEDIUM — Fallback disables state text verification |

These False defaults are intentionally conservative (features disabled if config missing), but the gap means a yaml load failure silently disables 4 features.

### Orchestrator Flags (consumed in `validation_orchestrator.py`, not stage4 directly)

All 5 orchestrator flags (`use_pre_llm`, `use_self_consistency`, `use_retrospective`, `use_reflexion`, `use_adaptive_threshold`) and 3 params (`consistency_votes`, `catharsis_max_gap`, `max_parallel_workers`) are consumed. No unused flags found.

### Unused Flags
**None found.** All flags defined in yaml are consumed in code.

---

## 5.5 Test Realism Assessment

### Mock Depth

**Finding: Deeply mocked, hiding real behavior in several areas.**

1. **`_make_ctx()` pattern** — All test files create a `MagicMock()` context with 15-20 pre-configured mock attributes. This is a necessary pragmatic choice given the deep dependency graph, but it means:
   - Tests never exercise real `Stage4Context.from_app()` wiring (only `test_stage4_context.py` tests this).
   - Mock return values may not match real runtime shapes.

2. **`_run_advisory_chain` always mocked** — In `test_stage4_interview_round.py:296`, the entire advisory chain is replaced with `MagicMock(return_value=[...])`. No test exercises the actual dispatch to 8 individual `_advisory_*` methods or their error handling.

3. **Director mock** — `ctx.agents["director"].select_and_judge_ensemble` always returns a well-formed dict. Real director can return malformed/partial results.

4. **`_prepare_stage4_session` fully mocked in e2e** — The session preparation (blueprint loading, arc resolution, output dir creation) is replaced with a lambda returning a static dict.

### Positive patterns
- Tests verify Korean text handling (e.g., `"통과 원고"`, `"테스트 원고"`, `"이전 원고"`).
- Tests check boundary conditions (empty candidates, DB exceptions, None values).
- `_AppTrapContextBuilder` / `_AppTrapInterviewRound` patterns verify DI correctness by raising on `self.app` access.
- Budget/truncation tests use realistic character counts.

### Korean Text Pattern Coverage

| Pattern | Covered? |
|---------|----------|
| NPC names in Korean | YES — `"노사부"`, `"흑풍"`, `"연홍"` in context_builder tests |
| Korean manuscript content | YES — `"테스트 원고"`, `"통과 원고"`, `"이전 화 내용"` |
| Korean director feedback | YES — `"좋음"`, `"부족"`, `"피드백"` |
| Korean advisory text | PARTIAL — `"마지막 장면 모순"` in one test, but advisory wrapper methods untested |
| Wuxia-specific terms | YES — `"천하제일"`, `"청풍산장"`, `"청룡검"` |
| Investment-specific terms | YES — capital extraction tests with Korean number patterns |

### Advisory Chain Test Coverage

| Advisor | Unit Test (standalone) | Integration Test (via interview_round) |
|---------|----------------------|---------------------------------------|
| TruthGate | YES (`test_truth_gate.py`) | NO — `_advisory_truth_gate()` wrapper untested |
| NPC Drift | YES (`test_npc_drift_advisor.py`) | NO — `_advisory_npc_drift()` wrapper untested |
| Numeric Drift | YES (`test_numeric_drift_advisor.py`) | NO — `_advisory_numeric_drift()` wrapper untested |
| Flashback | YES (`test_flashback_verifier.py`) | NO — `_advisory_flashback()` wrapper untested |
| Info Paradox | YES (`test_info_paradox_checker.py`) | NO — `_advisory_info_paradox()` wrapper untested |
| Relationship Drift | INDIRECT | NO |
| Long-term Repetition | YES (`test_long_term_repetition.py`) | NO |
| Numeric Consistency | YES (`test_numeric_consistency_checker.py`) | NO |

**Key Gap**: Each advisor class has its own test suite, but the **wiring layer** in `Stage4InterviewRound._advisory_*()` methods is never tested. This layer handles:
- Argument construction from round context
- Error swallowing (try/except returning `[]`)
- Timeout handling
- Result formatting into advisory text

---

## Summary of Findings by Priority

### P0 (High Risk)
1. **11 `_threshold()` defaults are stale** — Context budgets default to 5-15x below yaml values. A yaml load failure would silently degrade quality. Most critical: `retry.director_max_attempts` (5 vs 10), `context.mandatory_context_max` (80K vs 400K), `smart_retrieval.director_total_budget` (20K vs 300K).
2. **3 boolean feature flags default to False** — `smart_retrieval.enabled/stage4_enabled/director_enabled` all default False; yaml load failure disables smart retrieval silently.

### P1 (Coverage Gap)
3. **Advisory chain wiring untested** — `_run_advisory_chain()` + 8 `_advisory_*()` wrappers have zero direct tests. Error handling, argument construction, and timeout behavior is unverified.
4. **`_run_pre_director_validation()`** — Pre-director validation pipeline not tested.
5. **`_setup_writing_directive()`** — WritingDirective setup not tested.
6. **Post-processor persistence methods** — `_memorize_and_validate()`, `_collect_manager_and_build_delta()`, `_run_post_pass_advisories()` untested.

### P2 (Minor)
7. **2 hardcoded `90` values** in tests match `scoring.quality_gate_score` but would need manual update if yaml changes.
8. **Context builder helper methods** — `_build_condensed_world_state_summary()`, `_build_condensed_fact_ledger_summary()`, `_fetch_manuscript_excerpt()`, `_build_future_arc_context()` lack direct tests.
9. **Comment in `test_stage4_interview_round.py:2483`** references old value `1500` for `slot_max_chars_default` (now 3000 in yaml).
