Date: 2026-03-23
Status: final
Document Type: T3 evidence manifest
Canonical Path: `docs/2026-03-23/opus/rol-global-survey-t3-contracts-regression-evidence.md`

---

# T3 Contracts / Regression — Evidence Manifest

## 1. Test Harness Metrics (live collection)

| Metric | Value | Method |
|---|---|---|
| Test files (*.py in tests/) | 383 | `find tests -name "*.py" -type f \| wc -l` |
| Files with `def test_*` | 373 | `grep -rl "def test_" tests/ \| wc -l` |
| Total `def test_*` definitions | 5,175 | `grep -rh "def test_" tests/ \| wc -l` |
| Pytest collected items | 5,423 | `python -m pytest tests/ --co -q` |
| Collection errors | 1 | `test_wuxia_narrative_router_and_bi.py` |
| xfail markers | 0 | `grep -rl "xfail" tests/ \| wc -l` |
| Files using `pytest.skip` | 10 | `grep -rl "pytest.skip" tests/ \| wc -l` |

## 2. Test File Distribution — Top 30 by Function Count

| File | Functions |
|---|---|
| test_stage4_interview_round.py | 219 |
| test_stage4_orchestrator.py | 142 |
| test_director_modules.py | 119 |
| test_stage4_context_builder.py | 97 |
| test_stage2_preflight.py | 87 |
| test_pass_with_fix.py | 86 |
| test_stage2_pipeline.py | 85 |
| test_chief_writer.py | 85 |
| test_stage3_orchestrator.py | 81 |
| test_base_agent.py | 81 |
| test_continuity_modules.py | 78 |
| test_stage4_post_processor.py | 71 |
| test_vec_memory.py | 67 |
| test_feedback_system.py | 63 |
| test_pydantic_models.py | 57 |
| test_relationship_tracker.py | 47 |
| test_stage01_helpers.py | 46 |
| test_prompt_builder.py | 46 |
| test_genre_schema_builder.py | 46 |
| test_api_contract.py | 43 |
| test_state_service.py | 41 |
| test_db_manager.py | 41 |
| test_chief_writer_context.py | 41 |
| test_state_tracker.py | 40 |
| test_stage2_preflight_helpers.py | 40 |
| test_numeric_consistency_checker.py | 40 |
| test_chief_writer_quality.py | 39 |
| test_stage4_context.py | 35 |
| test_genre_guard.py | 34 |
| test_pipeline_smoke.py (integration) | 34 |

## 3. Specialized Test Tiers

| Tier | Files | Total Lines |
|---|---|---|
| E2E (`tests/e2e/`) | 8 (+1 conftest, +1 __init__) | 2,074 |
| Integration (`tests/integration/`) | 2 (+1 __init__) | 1,505 |
| Chaos (`tests/chaos/`) | 7 (+1 __init__) | 1,108 |

## 4. Contract / Canary Test Files

| File | Functions | Purpose |
|---|---|---|
| test_runtime_authority_contract.py | 15 | Stage ownership invariants |
| test_encoding_boundary_contract.py | 4 | UTF-8 boundary checks |
| test_check_utf8_hygiene.py | 10 | Pre-commit hook unit tests |
| test_desktop_packaging_contract.py | 11 | Desktop build contract |
| test_smoke_fixture_contract.py | 7 | Fixture naming contract |
| test_regression_validation_tier_contract.py | 3 | Tier file existence |
| test_main_a_packaged_bootstrap_contract.py | 2 | Packaged bootstrap paths |
| test_main_a_stage_entry_contracts.py | 7 | Stage entry routing |
| test_runtime_ownership_contract.py | (in CONTRACT_SAFE tier) | Ownership invariants |
| test_runtime_paths.py | (in CONTRACT_SAFE tier) | Path resolution |
| test_runtime_print_allowlist.py | (in CONTRACT_SAFE tier) | Print containment |
| test_surface_containment_contract.py | (in CONTRACT_SAFE tier) | Surface leak prevention |

## 5. Script Inventory Summary

| Category | Count | LOC | DB Mutation |
|---|---|---|---|
| A. Runtime-affecting | 9 | ~3,100 | Yes (fixture-bounded) |
| B. Governance/ops | 9 | ~1,800 | No |
| C. Document builders | 15 | ~5,500 | No (file output only) |
| D. Corpus builders | 3 | ~200 | No |
| E. Migration/repair | 2 | ~810 | Yes (one-time, completed) |
| F. Support libraries | 4 | ~2,400 | N/A (import-only) |
| G. Shell | 1 | N/A | N/A |
| **Total** | **47** | **~17,000** | |

## 6. Config File Inventory

| Group | Count | Format | Schema Validation |
|---|---|---|---|
| System YAML (system.yaml, models.yaml) | 2 | YAML | None |
| Validation YAML | 1 | YAML | None (type coercion only) |
| Genre guard YAML | 10 | YAML | None |
| Prompt template YAML | 9 | YAML | None (custom parser) |
| Prompt library JSON | 12 | JSON | None |
| Style reference JSON | 2 | JSON | None |
| Term mapping JSON | 2 | JSON | None |
| Settings JSON (legacy) | 1 | JSON | None |
| Other (tone presets, suffixes, genre hints) | 5 | Mixed | None |
| **Total** | **44** | | **0 with schema** |

## 7. Key Verified Source Anchors

| Finding | Anchor | Verified |
|---|---|---|
| tf_c1_patch.py missing __main__ guard | `scripts/tf_c1_patch.py:1-99` | grep confirmed no `__main__` |
| Deprecated configs unreferenced | `config/prompts/deprecated/*.json` | grep across modules/ returned empty |
| ConfigManager provenance tested | `tests/test_config_manager.py` | 29 test functions verified |
| Regression tier contract valid | `scripts/regression_validation_tiers.py:1-85` | read in full |
| Smoke fixture contract valid | `scripts/smoke_fixture_contract.py:1-8` | read in full |
| Pre-commit hook is check_utf8_hygiene only | `.pre-commit-config.yaml` | confirmed single entry |
| xfail = 0 | `grep -rl "xfail" tests/` | confirmed empty result |
| settings.json compat path active | `modules/core/config_manager.py:134+` | `load_settings_json()` method exists |
| tf_c1_patch.py hardcoded wrong user path | `scripts/tf_c1_patch.py:4` | `C:\Users\wjjo\Desktop\` (not current user) |

## 8. Production Module Directory Coverage

| Directory | Modules | Has test_* files |
|---|---|---|
| modules/core/ | 142 | Yes (name-matched) |
| modules/domain/agents/ | 49 | Yes (name-matched) |
| modules/validation/ | 16 | Yes (name-matched) |
| modules/api/ | 7 | Yes (name-matched) |
| modules/core/genre_guards/ | 13 | Yes (name-matched) |
| modules/core/stage0/ | 5 | Yes (name-matched) |

Note: "name-matched" means `tests/test_{module_name}*.py` exists. Depth of coverage varies.
