# Tranche F+H: Quality/Regression Surface + Cross-Cutting Contracts/Config

**Status**: DRAFT / NOT AUTHORITY / COLLECTOR ONLY / NO EXECUTION AUTHORITY

**Terminal**: 5
**Date**: 2026-03-20
**Baseline Commit**: `d0fa70f1` (docs: CODEX-ENTRY-POINT — OPUS 15건 근본 재감리 결과 반영)
**Baseline Dirty Summary**: 90+ modified files (modules, tests, docs, desktop), 20+ untracked files
**Mode**: survey-only, side-effects included
**Scope**: Tranche F (tests, smoke, canary, regression) + Tranche H (config, contracts, prompts, bootstrap)

---

## 1. Scope

### Included
- `tests/` — 328 Python files, 87,706 lines total (root: 297, e2e: 10, chaos: 7, integration: 3, property: 4, stage3_isolated: 3, stage4_v2: 2)
- `config/` — system.yaml, models.yaml, validation.yaml, 9 prompt YAMLs, 10 genre YAMLs, item_suffixes.yaml, genre_hints.yaml, tone_presets.json
- `docs/implementation/` — 6 JSON contracts, 20+ governance/harness MDs
- `modules/core/config_manager.py`, `constants.py`, `models_config.py`, `response_schemas.py`, `constraint_db.py`
- `modules/validation/` — validation_orchestrator.py, advisory_validator.py, + 5 tier validators
- `modules/core/` quality systems — pass_rate_monitor.py, quality_dashboard.py, constitutional_checker.py, self_reflection.py, chain_of_verification.py, cross_agent_verifier.py, adversarial_self_play.py
- `geuldobi-desktop/package.json`, `src/main.js`, `src/preload.js`
- `pyproject.toml`, `.editorconfig`, `.gitattributes`

### Excluded
- `.git/`, `__pycache__/`, `.venv/`, build outputs
- `docs/` historical surveys (reference only)
- Narrative pipeline content (treatments, bibles, blockguides)

---

## 2. Test Harness Inventory

### 2.1 Directory Structure

| Directory | Files | Lines | Purpose |
|-----------|-------|-------|---------|
| `tests/` (root) | 297 | ~80,000 | Unit + contract + sweep + advisory tests |
| `tests/e2e/` | 10 | ~2,200 | End-to-end smoke tests (mocked LLM, real DB copies) |
| `tests/chaos/` | 7 | ~1,100 | Robustness/boundary tests (feedback loops, dead NPCs, partial commits) |
| `tests/integration/` | 3 | ~1,500 | DI chain signal flow, pipeline wiring |
| `tests/property/` | 4 | ~1,100 | Hypothesis-based generative tests (rollback, DB, validation, budget) |
| `tests/stage3_isolated_test/` | 3 | ~900 | Stage 3 production isolation (REAL API calls) |
| `tests/stage4_v2_test/` | 2 | ~550 | Stage 4 batch tests (REAL API calls) |

### 2.2 Top Test Files by Size

| File | Lines | Functions | Domain |
|------|-------|-----------|--------|
| test_stage4_interview_round.py | 3,771 | 102 | Stage 4 interview + advisory chain |
| test_pass_with_fix.py | 2,537 | 86 | PASS_WITH_FIX loop + retry |
| test_director_modules.py | 1,699 | 99 | Director facade + 5 sub-modules |
| test_stage4_context_builder.py | 1,663 | 63 | Stage4Context DI construction |
| test_stage3_orchestrator.py | 1,506 | 76 | Stage 3 orchestration |
| test_chief_writer.py | 1,460 | 85 | ChiefWriter ensemble generation |
| test_stage4_post_processor.py | 1,350 | 52 | Post-processing + emotion tracking |
| test_stage4_orchestrator.py | 1,336 | 61 | Stage 4 round execution |
| test_stage2_preflight_helpers.py | 1,194 | ~40 | Stage 2 preflight validation |
| test_continuity_modules.py | 1,165 | 70 | Continuity arc/blueprint/manuscript |

### 2.3 Conftest Fixtures

**tests/conftest.py** (254 lines, 11 fixtures):
- `temp_dir` — custom temp directory with Windows-aware retry cleanup (shutil.rmtree retry loop + gc.collect)
- `sample_bible`, `sample_blueprint`, `sample_manuscript` — data fixtures
- `sample_hud_wuxia`, `sample_hud_hunter`, `sample_hud_investment` — genre HUDs
- `mock_api_client` — MagicMock Gemini API client
- `mock_db_manager` — real SQLite DB in temp directory
- `mock_project_context` — directory structure + bible
- `validation_context` — validation context with encyclopedia/HUD

**tests/e2e/conftest.py** (174 lines, 5 fixtures + 4 constants):
- `e2e_db` — real SQLite DB via DBManager(tmp_path)
- `e2e_bible`, `e2e_arc`, `e2e_blueprint` — data fixtures
- `e2e_stage4_ctx` — Stage4Context manual assembly with real DB binding
- Constants: `MOCK_MANUSCRIPT` (~5100 chars), `MOCK_ENSEMBLE` (3 strategies), `MOCK_DIRECTOR_PASS` (score=85), `MOCK_DIRECTOR_REJECT` (score=45)

### 2.4 Test Configuration

**pyproject.toml:**
```
testpaths = ["tests"]
addopts = "-p no:xdist --tb=short -o console_output_style=count"
```
- xdist explicitly disabled (memory conservation, per AGENTS.md pytest memory rule)
- No registered custom markers in pyproject.toml

**tools2/pytest.ini** — registers: `slow`, `integration`, `edge_case` markers

---

## 3. Smoke / Canary / Regression Map

### 3.1 Smoke Tests

| File | Type | Real API? | Real DB? | Key Checks |
|------|------|-----------|----------|------------|
| tests/e2e/test_l3_stage4_smoke.py | E2E smoke | No (mocked) | Yes (copy of real) | 3-episode Stage4 with blueprint input |
| tests/e2e/test_l3_stage3_smoke.py | E2E smoke | No (mocked) | Yes (copy of real) | Stage 3 pipeline smoke |
| tests/e2e/test_l3_stage2_realproject.py | E2E smoke | No (mocked) | Yes (copy of real) | Stage 2 real project |
| tests/e2e/test_l3_golden_route.py | E2E smoke | No (mocked) | No (file scan) | Golden path with real treatments |
| tests/e2e/test_smoke_pipeline.py | Pipeline smoke | No (mocked) | No | Lightweight pipeline validation |
| tests/e2e/test_lm_advisory_smoke.py | Advisory smoke | No (mocked) | No | Advisory system smoke |
| tests/integration/test_pipeline_smoke.py | Integration | No (mocked) | Yes (temp) | Pipeline wiring validation |

**Conditional skip**: E2E smoke tests skip if `projects/코덱스_테스트/project_data.db` not found. This creates a hidden dependency on a real project database.

### 3.2 Canary Tests

| File | Lines | Purpose |
|------|-------|---------|
| test_stage4_canary_tools.py | 571 | Stage 4 quick validation tools |
| test_run_stage4_canary.py | 117 | Canary test runner wrapper |
| test_run_stage34_canary.py | 148 | Multi-stage canary |
| test_auto_frontier_lag_harness.py | 255 | Frontier lag detection |

### 3.3 Regression / Sweep Tests

**26 sweep test files** (test_sweep3.py through test_sweep39.py):
- Track bug-fix iterations chronologically
- Notable: test_sweep28.py (592 lines — major iteration), test_sweep31.py (int coercion safety)
- Each sweep file verifies specific past regressions remain fixed

**Dedicated regression tests:**

| File | Lines | Regression Target |
|------|-------|-------------------|
| test_quality_regression.py | ~300 | Score regression detection thresholds |
| test_legacy_reentry_reaudit.py | 317 | Historical regression audit |
| test_opus_tf5_e6_regressions.py | ~200 | Opus TF-specific regressions |
| test_satisfaction_step3_tagging.py | ~200 | Satisfaction tagging regression |

### 3.4 Test Tier Contract

Per `docs/implementation/regression-validation-tier-contract-v1.json`:

| Tier | Count | Description |
|------|-------|-------------|
| contract_safe | 10 tests | Read-only contract checks, no project state mutation |
| focused_mutation | 2 tests + 3 scripts | Targeted smoke, fixture/project mutation |
| full_canary_proof | 0 tests + 2 scripts | Live proof helpers with project logging |

### 3.5 Property-Based Tests (Hypothesis)

| File | Lines | Invariant Tested |
|------|-------|------------------|
| test_rollback_props.py | 328 | State rollback invariants |
| test_db_rollback_props.py | 295 | DB rollback properties |
| test_validation_props.py | 246 | Validation invariants |
| test_budget_props.py | 222 | ContextAdvisor slot budget (min_chars ≥ 1500) |

---

## 4. Prompt / Contract / Config Surface

### 4.1 System Configuration Files

| File | Purpose | SSOT? | Missing Behavior |
|------|---------|-------|------------------|
| config/system.yaml | API params, thinking budget, timeouts, cache | Yes (API layer) | WARNING log, hard-coded fallback |
| config/models.yaml | Model assignments (20+ agents) | Yes (model routing) | WARNING log, 23 hard-coded defaults |
| config/settings/validation.yaml | All validation thresholds, context limits, features | Yes (validation) | Empty dict {}, Python constant fallback |
| config/settings.json | Legacy (only costs.max_retries, temperature, validation.use_v0128) | No (superseded) | Empty dict {} |
| pyproject.toml | Ruff config, pytest config, project metadata | Yes (tooling) | N/A |
| .editorconfig | UTF-8 pin, indent rules | Yes (encoding guard) | N/A |
| .gitattributes | EOL normalization, binary marking | Yes (diff guard) | N/A |

### 4.2 Prompt Template Files

| File | Version | Agents Using | Key Templates |
|------|---------|-------------|---------------|
| config/prompts/ensemble.yaml | V70 opt3 | ArcEnsemble, BlueprintEnsemble | ENSEMBLE_ARC_PROMPT, BLUEPRINT_GENERATION_PROMPT |
| config/prompts/chief_writer.yaml | V70 opt3 | ChiefWriter | PROMPT_TEMPLATE_OUTPUT, COMMON_RULES_SECTION, WRITING_GUIDELINES, PATCH_MODE_PROMPT |
| config/prompts/director.yaml | V70 opt3 | Director, DirectorEnsemble | ENSEMBLE_STABLE_CONTEXT (180K cached), ENSEMBLE_VARIABLE_PROMPT |
| config/prompts/analyst.yaml | V70 opt1 | Analyst | POST_STITCH_REPAIR_PROMPT, ENRICH_BLOCK_PROMPT_V30 |
| config/prompts/arc_generator.yaml | V70 opt3 | FourPhaseArcGenerator | ARC_PATCH_MODE_PROMPT |
| config/prompts/blueprint_generator.yaml | V70 opt3 | ThreePhaseBlueprintGenerator | BLUEPRINT_PATCH_MODE_PROMPT, BLUEPRINT_PREFLIGHT_VALIDATE_PROMPT |
| config/prompts/writing_directive.yaml | — | ChiefWriter | WRITING_DIRECTIVE_SYSTEM |
| config/prompts/emotion_tracker.yaml | — | EmotionTracker | Negative/positive streak recommendations |
| config/prompts/investment_math_verifier.yaml | — | InvestmentMathVerifier | VERIFY_PROMPT |

### 4.3 Genre Guard Configuration (10 genres)

All under `config/genres/*.yaml`, same structure: `genre_name`, `forbidden_terms`, `allowed_terms`, `mandatory_concepts`, optional hierarchies.

| Genre | Forbidden | Allowed | Mandatory | Special |
|-------|-----------|---------|-----------|---------|
| wuxia | 100+ | — | — | Most restrictive (blocks modern/game terms) |
| investment | 47 | 25 | 4 | Wealth hierarchy, realistic return rates, status-action limits |
| hunter | 45 | 13 | 4 | Rank hierarchy, rank technique limits |
| fantasy | 43 | 32 | 2 | Blocks wuxia-specific terms |
| cooking, medical, sports, actor, alt_history, composer | Variable | Variable | Variable | Genre-specific terms |

### 4.4 IPC / API Contracts

| Contract | Path | Version | Key Content |
|----------|------|---------|-------------|
| Desktop IPC | docs/implementation/desktop-ipc-surface-contract-v1.json | v1 | 26 live preload methods, 0 dead candidates |
| Prompt Map | docs/implementation/prompt-map-v1.json | v1 | Stage 0 menu schema (7 keys), stage input steps |
| Event Schema | docs/implementation/event-schema-v1.json | v1 | WebSocket events: run_started, stdout, prompt_*, run_completed/failed/stopped |
| Surface Containment | docs/implementation/surface-containment-contract-v1.json | v1 | live/manual-only/shadow/residue classification |
| Regression Tier | docs/implementation/regression-validation-tier-contract-v1.json | v1 | contract_safe/focused_mutation/full_canary_proof |
| Desktop Runtime | docs/implementation/desktop-runtime-contract-v1.json | v1 | Desktop file structure and init |

### 4.5 Response Schema Constants

From `modules/core/response_schemas.py`:

| Schema | Verdict Values | Key Fields |
|--------|---------------|------------|
| DIRECTOR_AUDIT_SCHEMA | PASS, PASS_WITH_FIX, PASS_WITH_WARNING, REJECT | decision, score(0-100), fix_scope(inplace/partial/full), error_category, consistency_checklist(14 items) |
| STRATEGIC_AUDIT_SCHEMA | PASS, PASS_WITH_FIX, PASS_WITH_WARNING, REJECT | Same verdict enum |
| BLOCKING_RESULT_SCHEMA | passed: bool | tier="BLOCKING", failures[], message |
| SCORING_RESULT_SCHEMA | passed: bool | total_score(0-100), breakdown(6 dimensions), threshold |
| ADVISORY_RESULT_SCHEMA | passed: True (always) | tier="ADVISORY", suggestions[] |

### 4.6 Validation Pipeline Architecture

**6-Tier Pipeline** (validation_orchestrator.py `validate_v59()`):

| Tier | Name | Type | Blocking? | Verdict |
|------|------|------|-----------|---------|
| 0.25 | PRE-LLM | Python | No | warnings → -1 score |
| 0.5 | CONTINUITY | Python | No (advisory) | violations → -5/violation (cap -15) |
| 1 | BLOCKING | Python | No (advisory) | failures → -5/failure (cap -20) |
| 1.5 | CONSISTENCY | Python+LLM | YES (if unjustifiable) | unjustifiable → immediate advisory/CRITICAL |
| 2 | SCORING | LLM | Via threshold | 0-100 score (6 dimensions) |
| 3 | ADVISORY | LLM | No | Always passes, suggestions only |

**Post-Tier Adjustments:**
- CatharsisTimer: -2 to -5
- ActionSceneEvaluator: ±2 to ±3
- RetrospectiveValidator: -5 to -15

**Final Decision:**
```
total >= max(85, adaptive_threshold) → PASS
adaptive_threshold <= total < 85     → CONDITIONAL_PASS
total < adaptive_threshold           → REJECT
```

**Adaptive Threshold** (clamped [60, 90]):
- Base: genre profile (68-73)
- Episode type: ±3 to ±7
- Streak: ±2 to ±5
- Pattern: ±2 to ±4
- Arc position: -1 to +3

### 4.7 Bootstrap / Config Loading Order

**SovereignApp (main_a.py):**
1. `load_dotenv(override=True)` → loads `.env` (GOOGLE_API_KEY required)
2. `StudioVisualizer()` → UI
3. `init_logger()` → creates `logs/`
4. `genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))` → blocks if missing
5. 140+ attributes initialized to None (lazy)
6. DI orchestrators created: Stage2/3/4Orchestrator(app=self)
7. Agents loaded lazily: `_lazy_load_agents()`, `_lazy_load_v50_modules()`, `_lazy_load_stage0()`

**ConfigManager:**
1. Root = `Path.cwd()` (repo root assumption)
2. Auto-creates `projects/`, `logs/`
3. `_load_agents_from_yaml()` → `config/models.yaml` (fallback: 23 hard-coded defaults)
4. `load_settings()` (on-demand) → `config/settings/validation.yaml` (fallback: empty dict)
5. `load_settings_json()` (on-demand) → `config/settings.json` (fallback: empty dict)

**Fallback Hierarchy:**
```
YAML config file → settings.json (compat) → Python constants → caller default → hard-coded
```

**Desktop (Electron):**
1. `main.js` requires `console_relay`, `desktop_control_plane_contract` (hard fail if missing)
2. Constants: `STATUS_BASE_URL = "http://127.0.0.1:8300"`, `EVENTS_WS_URL = "ws://127.0.0.1:8300/events"`
3. `preload.js` exposes 26 IPC methods via `contextBridge.exposeInMainWorld`

### 4.8 Key Threshold Constants

| Parameter | Value | Source | Fallback |
|-----------|-------|--------|----------|
| quality_gate_score | 90 | validation.yaml | constants.py |
| default_pass_threshold | 60 | validation.yaml | constants.py |
| manuscript.min_length | 4,000 | validation.yaml | constants.py |
| manuscript.target_length | 5,000 | validation.yaml | constants.py |
| max_context_chars | 1,000,000 | validation.yaml | constants.py |
| mandatory_context_max | 400,000 | validation.yaml | constants.py |
| director_max_attempts | 10 | validation.yaml | constants.py |
| patch_mode.rewrite_below | 50 | validation.yaml | — |
| patch_mode.inplace_below | 60 | validation.yaml | — |
| cascade_cap_passes | 10 | validation.yaml | — |
| thinking_budget.maximum | 24,576 | system.yaml | — |
| api.timeout | 300s | system.yaml | — |
| ensemble_timeout.arc | 300s | system.yaml | — |

---

## 5. Cross-Cut Drift Notes

### 5.1 Test ↔ Runtime Verdict Contract — SYNC

**FACT**: All 4 verdict values (PASS, PASS_WITH_FIX, PASS_WITH_WARNING, REJECT) tested in `test_pass_with_fix.py` and `test_llm_schema.py` match the enum in `response_schemas.py` L133.

**FACT**: PASS_WITH_FIX loop (max 3 iterations) tested in `test_pass_with_fix.py` matches `stage4_interview_round.py` L3658 `_execute_pass_with_fix_loop()`.

**FACT**: Blocking validator advisory (non-blocking with score penalty) tested in `test_validation_orchestrator.py` matches live code at `validation_orchestrator.py` L916-917.

### 5.2 Test ↔ Schema Contract — SYNC

**FACT**: `test_llm_schema.py` tests `DIRECTOR_AUDIT_SCHEMA` enum values match `response_schemas.py` L133.

**FACT**: `test_canonical_constraints.py` tests `FactLedger.get_canonical_summary()` and `WorldStateManager.get_canonical_constraints()` match live interfaces.

### 5.3 Test ↔ Stage Orchestration — SYNC

**FACT**: Stage2Orchestrator `_resolve_arc_number_for_episode()` tested with fallback logic matches live code.

**FACT**: Stage3 lazy-init pattern (3→19 slots expansion) reflected in tests.

**FACT**: Stage4Context DI properties tested in `test_stage4_context.py` match `stage4_context.py`.

### 5.4 Test ↔ Sweep Bug Fixes — SYNC

**FACT**: test_sweep28 (ChainOfVerification context preservation), test_sweep29 (Stage4ContextBuilder + degraded mode), test_sweep31 (int coercion safety) all verified against live code — safety patterns remain in place.

### 5.5 Test ↔ Desktop Contracts — SYNC

**FACT**: `test_desktop_direct_surface_contract.py` verifies INDEX_HTML contains React vendor files, MAIN_JS defines STATUS_BASE_URL and EVENTS_WS_URL. Matches live `geuldobi-desktop/src/main.js`.

**FACT**: `test_desktop_contract_refresh.py` defines OFFICIAL_DESKTOP_GATE_CHECKS that match live desktop structure.

### 5.6 Config ↔ Constants Fallback Chain — NO OBSERVED DRIFT

**FACT**: `_LazyThreshold` descriptors in `constants.py` correctly defer to `validation.yaml` via `_threshold()`, with Python defaults as fallback.

**FACT**: `ConfigManager.get_guard_threshold_contract()` returns provenance dict with `used_fallback` flag — no silent fallback drift.

### 5.7 Prompt Version Alignment

**FACT**: All prompt YAMLs show V70 version markers (opt1-opt3). No version mismatch across prompts detected.

**INFERENCE**: Prompt versions were likely synchronized in a single upgrade pass. Cross-prompt consistency appears maintained.

---

## 6. Side-Effect Sweep

### 6.1 Test Suite Side Effects

| Category | Count | Mechanism | Risk | Auto-Cleanup |
|----------|-------|-----------|------|--------------|
| Temp directory fixtures | 50+ | `tmp_path` / custom `temp_dir` | Low | Yes (pytest) |
| SQLite DB creation | 92 files | DBManager in temp | Low | Yes (fixture teardown) |
| File writes (write_text) | 180+ | In tmp_path | Low | Yes (pytest) |
| Persistent artifact logs | 2 | `logs/`, `projects/test_project/logs/` | **HIGH** | No |
| Real API calls | 2 files | Google Gemini direct | **CRITICAL** | No |
| Node.js subprocess | 6 files | `subprocess.run(["node", ...])` | Medium | No |
| Environment variable patches | 15+ | monkeypatch | Low | Yes (pytest) |
| CWD changes | 5+ | monkeypatch.chdir | Low | Yes (pytest) |

### 6.2 Persistent Artifacts (Not Auto-Cleaned)

**FACT**: `projects/test_project/logs/episode_production.jsonl` — 303 lines, ~485 KB, last modified 2026-03-19. This is a real accumulated production log that persists across test runs.

**FACT**: `tests/stage3_isolated_test/test_stage3_production.py` and `tests/stage4_v2_test/test_episode_1.py` make real Google Gemini API calls (not mocked). These require `GOOGLE_API_KEY` and incur real costs.

**FACT**: 6 test files spawn `node` processes via `subprocess.run()` for JavaScript contract verification.

### 6.3 Hidden Dependencies

**FACT**: E2E smoke tests (test_l3_stage4_smoke, test_l3_stage2_realproject, test_l3_stage3_smoke) depend on `projects/코덱스_테스트/project_data.db` existing. They skip if absent.

**FACT**: `test_l3_golden_route.py` depends on real treatment files under `treatments/`.

**FACT**: Windows-specific file locking prompted custom `temp_dir` fixture with retry loop (conftest.py L21-38).

---

## 7. Facts

### Test Infrastructure
1. **328 test files**, ~87,706 lines across 7 directories
2. **11 root conftest fixtures** + **5 e2e conftest fixtures** + **4 mock constants**
3. **No @pytest.mark.xfail decorators found** in any test file. The 68 xfailed count (from memory) may refer to tests conditionally skipped by feature flags, not explicit xfail markers.
4. **19 pytest.skip() calls** across 6 files — conditional on environment (sqlite-vec, real DB, keyword constants, treatment files)
5. **1 @pytest.mark.skipif** — `test_db_merge.py` for sqlite-vec availability
6. **26 sweep test files** (test_sweep3 through test_sweep39) track historical bug-fix regressions
7. **Feature flags controlling test execution**: `V50_MODULES_AVAILABLE` (70+ tests), `STAGE0_AVAILABLE` (45+ tests), `_VEC_AVAILABLE` (5 tests), `RETROSPECTIVE_AVAILABLE` (1 test)

### Quality System
8. **4 verdict values**: PASS, PASS_WITH_FIX, PASS_WITH_WARNING, REJECT (response_schemas.py L133)
9. **6-tier validation pipeline**: PRE-LLM → CONTINUITY → BLOCKING → CONSISTENCY → SCORING → ADVISORY
10. **Adaptive threshold**: base(68-73) ± adjustments, clamped [60, 90], self-consistency activates in [50,60] range
11. **PASS_WITH_FIX loop**: max 3 iterations, calls chief_writer.inplace_patch() + director re-audit
12. **Advisory always passes**: tier="ADVISORY", passed=True — suggestions only, never blocking
13. **Blocking is advisory**: BLOCKING tier failures feed score penalty (-5/failure, cap -20), not immediate REJECT
14. **Constitutional checker**: Stage 2 articles A1-A6, Stage 3 articles B1-B5, Stage 4 articles M1-M8

### Configuration
15. **validation.yaml**: SSOT for all thresholds (manuscript limits, scoring, context, retry, patch mode, quality regression, adaptive threshold, feature flags)
16. **models.yaml**: SSOT for model assignments (20+ agents, all Gemini 2.5 pro/flash)
17. **system.yaml**: SSOT for API params (thinking budget, timeouts, cache, ensemble timeouts)
18. **9 prompt YAMLs**: All at V70 version, synchronized
19. **10 genre YAMLs**: Consistent structure (forbidden_terms, allowed_terms, mandatory_concepts)
20. **Fallback chain**: YAML → settings.json → Python constants → caller default → hard-coded

### Contracts
21. **Desktop IPC contract**: 26 live preload methods, 0 dead candidates
22. **Event schema**: 8 event types (run lifecycle + prompt flow)
23. **Surface containment**: 4 categories (live, manual-only, shadow, residue)
24. **Regression tier**: 3 tiers (contract_safe=10, focused_mutation=2+3, full_canary_proof=0+2)

### Bootstrap
25. **SovereignApp** requires `GOOGLE_API_KEY` (blocks if missing)
26. **ConfigManager** assumes `Path.cwd()` is repo root
27. **Desktop main.js** hard-fails if `console_relay` or `desktop_control_plane_contract` missing
28. **All config loading is graceful** except GOOGLE_API_KEY and desktop module requires

---

## 8. Inferences

### Test Coverage Quality
1. **INFERENCE**: The test suite is heavily weighted toward Stage 4 (8+ files, 8,400+ lines) and Stage 2 (8 files, 4,000+ lines). Stage 3 has comparatively lighter coverage (3 files, 1,700+ lines). **Confidence**: HIGH — line counts are direct evidence.

2. **INFERENCE**: The sweep test pattern (26 files) indicates a discipline of regression-pinning — each bug fix gets a permanent test. This reduces regression risk but creates test maintenance burden over time. **Confidence**: MEDIUM — interpretation of pattern.

3. **INFERENCE**: The absence of explicit xfail markers suggests the project prefers skip-on-missing-env over expected-failure semantics. Feature flags gate entire test paths rather than marking individual tests as known-failing. **Confidence**: HIGH — based on grep results.

### Config Coherence
4. **INFERENCE**: The YAML → Python fallback chain is well-designed with provenance tracking (ConfigManager returns `used_fallback` flag). Config drift risk is low because constants.py uses `_LazyThreshold` descriptors that defer to YAML. **Confidence**: HIGH — code structure supports this.

5. **INFERENCE**: The prompt version synchronization at V70 suggests a coordinated upgrade. If one prompt template is updated without the others, cross-template assumptions could drift. **Confidence**: MEDIUM — no automated version-lock mechanism observed.

### Contract Stability
6. **INFERENCE**: Desktop IPC contract (26 methods, 0 dead) is actively maintained. Test coverage for desktop contracts (7 test files) provides reasonable regression protection. **Confidence**: HIGH — direct evidence.

7. **INFERENCE**: The regression tier contract (10 contract_safe, 2+3 focused_mutation, 0+2 full_canary_proof) is conservative — most tests are classified as safe, and live proof tests don't exist yet. **Confidence**: HIGH — contract file is explicit.

### Side-Effect Risk
8. **INFERENCE**: The 2 test files making real API calls (stage3_isolated, stage4_v2) are likely manual integration tests, not CI tests. They would fail or incur costs in automated runs. **Confidence**: HIGH — they require API keys and real project data.

9. **INFERENCE**: The persistent `episode_production.jsonl` (485KB, 303 entries) could accumulate indefinitely and mask test pollution or create false test dependencies. **Confidence**: MEDIUM — size is manageable but growth is unbounded.

---

## 9. Uncertainty / Contradictions

### U-1: xfailed Count Source — UNCERTAIN

**Memory claim**: "2,114 passed + 68 xfailed" (from Opus TF audit baseline).
**Live evidence**: No @pytest.mark.xfail decorators found in any test file. 19 pytest.skip() calls found.

**Possible explanations**:
- The 68 xfailed may come from tests that were *expected to fail* via a mechanism not captured by decorator grep (e.g., dynamic xfail in conftest, or plugin behavior)
- The count may be stale (from a previous codebase state with different test configuration)
- Pytest's xfail count may include tests skipped by feature flag mechanisms that map to xfail internally

**Status**: UNCERTAIN — needs fresh `pytest --co` or full test run to resolve.

### U-2: Feature Flag Test Path Coverage — UNCERTAIN

**Observation**: `V50_MODULES_AVAILABLE` gates 70+ tests, `STAGE0_AVAILABLE` gates 45+ tests.
**Question**: Are both True/False paths tested? If V50 is always True in test env, the False path may be untested.

**Status**: UNCERTAIN — would need test run analysis to determine actual feature flag states during CI.

### U-3: Real API Test Isolation — UNCERTAIN

**Observation**: `stage3_isolated_test/test_stage3_production.py` and `stage4_v2_test/test_episode_1.py` make real Gemini API calls.
**Question**: Are these excluded from standard test runs? No `@pytest.mark.integration` or `@pytest.mark.slow` markers observed on them.

**Status**: UNCERTAIN — their pytest discovery path (`tests/` is configured as testpath) means they could run in standard `pytest` invocation if API key and DB are available.

### U-4: Prompt YAML Cross-Version Lock — UNCERTAIN

**Observation**: All 9 prompt YAMLs show V70 markers, but no automated mechanism enforces version lock.
**Question**: Can one prompt be updated to V71 while others remain at V70, creating cross-template inconsistency?

**Status**: UNCERTAIN — no enforcement mechanism observed. Currently consistent but vulnerable to manual drift.

### U-5: Desktop Contract Completeness — UNCERTAIN

**Observation**: IPC contract lists 26 methods, 0 dead. Tests verify key constants and React vendor presence.
**Question**: Do tests cover all 26 IPC methods, or only a subset?

**Status**: UNCERTAIN — desktop test files (7 total, ~1,300 lines) may not exhaustively cover all 26 channels.

### U-6: Regression Tier Contract Drift — WATCHLIST

**Observation**: `regression-validation-tier-contract-v1.json` lists 10 contract_safe tests by name.
**Question**: As new tests are added, do they get classified into tiers? Or does the contract become stale?

**Status**: WATCHLIST — the contract is manually maintained; new tests not in the list are unclassified.

---

## 10. Candidate Watchlist

### W-1: Persistent Test Artifact Accumulation
**Surface**: `projects/test_project/logs/episode_production.jsonl` (485KB, growing)
**Risk**: Unbounded growth, potential false test state fingerprinting
**Recommendation for future survey**: Check if this file is git-tracked and whether cleanup policy exists

### W-2: Real API Call Tests Without Markers
**Surface**: `stage3_isolated_test/test_stage3_production.py`, `stage4_v2_test/test_episode_1.py`
**Risk**: Accidental execution in CI, real costs, non-deterministic results
**Recommendation for future survey**: Verify these are excluded from standard pytest runs

### W-3: Prompt Version Lock Mechanism
**Surface**: 9 prompt YAMLs at V70
**Risk**: Manual update to one prompt without others could create cross-template drift
**Recommendation for future survey**: Check if PromptLoader validates version consistency

### W-4: Desktop IPC Method Test Coverage
**Surface**: 26 live IPC methods vs 7 test files
**Risk**: Untested IPC channels may silently regress
**Recommendation for future survey**: Map each IPC method to its test coverage

### W-5: Feature Flag Path Coverage
**Surface**: V50_MODULES_AVAILABLE (70+ tests), STAGE0_AVAILABLE (45+ tests)
**Risk**: If flags are always True in tests, False path is untested
**Recommendation for future survey**: Verify both flag states are tested

### W-6: Regression Tier Contract Maintenance
**Surface**: `regression-validation-tier-contract-v1.json` (10 + 2+3 + 0+2 classified)
**Risk**: New tests created since contract was written may be unclassified
**Recommendation for future survey**: Compare contract test list against current test file inventory

### W-7: Custom temp_dir Fixture (Windows File Locking)
**Surface**: `tests/conftest.py` L21-38 — retry loop with gc.collect + sleep
**Risk**: Indicates persistent Windows file-locking issues; may leave orphaned temp dirs
**Recommendation for future survey**: Check if `tmp_path` (standard pytest) could replace custom fixture

### W-8: Config Schema Validation
**Surface**: validation.yaml (8,800+ bytes, 50+ top-level keys)
**Risk**: No JSON Schema or Pydantic validation for YAML config files — typos or missing keys silently fall to defaults
**Recommendation for future survey**: Check if config loading has validation or just silent fallback

---

## 11. TF Evidence Notes

### TF Cross-References Used as Evidence

| TF ID | Area | Test Evidence | Live Code Match | Status |
|-------|------|--------------|-----------------|--------|
| TF-26 | Ensemble timeouts | system.yaml `ensemble_timeouts` section | base_agent.py, system.yaml | SYNC — live config matches TF intent |
| TF-28b | Unified quality gate | validation.yaml `quality_gate_score: 90` | stage4_interview_round.py L4037 | SYNC — threshold matches |
| TF-32 | PASS_WITH_FIX | test_pass_with_fix.py (86 functions) | stage4_interview_round.py L3658 | SYNC — loop mechanics match |
| TF-36 | Blocking advisory | test_validation_orchestrator.py comments | validation_orchestrator.py L916-917 | SYNC — non-blocking confirmed |
| TF-49b | Blueprint preflight | blueprint_generator.yaml PREFLIGHT_VALIDATE_PROMPT | validation.yaml `blueprint_preflight: enabled` | SYNC — config + prompt aligned |
| TF-54 | Metaphor/intensity/NPC voice | chief_writer.yaml COMMON_RULES L8-L10 | ChiefWriter prompt injection | SYNC — rules present in prompt |
| TF-IPG | Inplace preserve ratio | validation.yaml `inplace_min_preserve_ratio: 0.70` | patch mode logic | SYNC — threshold present |
| I-10 | Graduated penalty | director.yaml contradiction check section | Director ensemble scoring | SYNC — CRITICAL→max 15/40, MAJOR→-10, MINOR→-3 |
| I-17 | Shared types | stage4_types.py (_RoundContext, _InterviewRoundResult) | Tests import from stage4_types | SYNC — type extraction confirmed |
| S-13 | Conditional modules | Stage4Context `conditional_modules: dict` | test_stage4_context.py | SYNC — pattern confirmed |

### TF Evidence Not Directly Verifiable in This Survey

| TF ID | Reason |
|-------|--------|
| TF-1 through TF-4 | Long-serialization systems (WorldState, ChainLinks, VolumeSummary, FactLedger) — require runtime or DB inspection, not static test survey |
| I-18 | Quota lock — requires API quota exhaustion scenario, not testable from static analysis |
| I-20 | Eviction TOCTOU — race condition, requires concurrent execution |
| C-03 | Degraded blocking — requires runtime degradation scenario |

### TF Stale Suspicions

**None identified.** All TF-tagged test assertions that could be verified against live code were found to be SYNC. No test was found to assume semantics that differ from the current implementation.

**Caveat**: This is a static analysis. Dynamic runtime behavior (threading, API quota, TOCTOU) cannot be fully verified from test file reading alone.

---

## Appendix A: Test File Classification by Domain

### Stage Pipeline Tests (24 files)
- Stage 0: test_stage0_fixes.py, test_stage0_work_guard_style_cache.py, test_stage01_helpers.py
- Stage 2: test_stage2_pipeline.py, test_stage2_orchestrator.py, test_stage2_context.py, test_stage2_preflight.py, test_stage2_preflight_helpers.py, test_stage2_finalizer.py, test_stage2_validation_pipeline.py, test_stage2_optimizer.py
- Stage 3: test_stage3_orchestrator.py, stage3_isolated_test/ (3 files)
- Stage 4: test_stage4_interview_round.py, test_stage4_context_builder.py, test_stage4_orchestrator.py, test_stage4_post_processor.py, test_stage4_context.py, test_stage4_canary_tools.py, test_stage4_cv_context.py, stage4_v2_test/ (2 files)

### Validation/Advisory Tests (12+ files)
- test_validation.py, test_validation_orchestrator.py, test_validation_orchestrator_soft_failure.py
- test_truth_gate.py, test_npc_drift_advisor.py, test_numeric_consistency_checker.py
- test_flashback_verifier.py, test_info_paradox_checker.py, test_relationship_drift_advisor.py
- test_numeric_drift_advisor.py, test_pass_with_fix.py

### Agent Tests (10+ files)
- test_chief_writer.py, test_chief_writer_context.py, test_chief_writer_quality.py
- test_director_modules.py, test_base_agent.py
- test_four_phase_arc_generator.py, test_unified_arc_validator.py, test_unified_blueprint_validator.py
- test_continuity_modules.py

### Desktop Tests (7 files)
- test_desktop_direct_surface_contract.py, test_desktop_contract_refresh.py
- test_desktop_transport_contract.py, test_desktop_shadow_hygiene.py
- test_desktop_packaging_contract.py, test_desktop_backend_restart_guard.py
- test_desktop_settings_recovery.py

### Database/Persistence Tests (8 files)
- test_db_manager.py, test_db_utilization.py, test_db_efficiency_transactions.py
- test_db_integrity_recovery.py, test_db_merge.py, test_db_cursor_live_inventory.py
- test_vec_memory.py, property/test_db_rollback_props.py

### Config/Schema Tests (5 files)
- test_llm_schema.py, test_canonical_constraints.py, test_genre_schema_builder.py
- test_context_window_utilization.py, test_genre_guard.py

---

## Appendix B: Config File Cross-Reference Matrix

| Config File | Loaded By | Tested By | Fallback |
|-------------|-----------|-----------|----------|
| config/models.yaml | config_manager.py, models_config.py | test_llm_schema.py | 23 hard-coded defaults |
| config/settings/validation.yaml | config_manager.py, constants.py | test_validation.py, test_canonical_constraints.py | Empty dict + Python constants |
| config/system.yaml | base_agent.py | test_base_agent.py | Hard-coded API defaults |
| config/prompts/ensemble.yaml | prompt_loader.py | test_four_phase_arc_generator.py, test_stage2_pipeline.py | N/A (required) |
| config/prompts/chief_writer.yaml | prompt_loader.py | test_chief_writer.py | N/A (required) |
| config/prompts/director.yaml | prompt_loader.py | test_director_modules.py | N/A (required) |
| config/genres/*.yaml | base_guard.py | test_genre_guard.py, test_genre_guards_extended.py | N/A (required) |
| desktop-ipc-surface-contract-v1.json | docs reference | test_desktop_direct_surface_contract.py | N/A (governance) |
| regression-validation-tier-contract-v1.json | docs reference | N/A (governance) | N/A |

---

*End of Tranche F+H survey. This document is DRAFT / COLLECTOR ONLY / NO EXECUTION AUTHORITY.*
