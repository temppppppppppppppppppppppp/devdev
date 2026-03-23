Date: 2026-03-23
Status: final
Document Type: T3 evidence manifest
Lane: Contracts / Context / Regression
Canonical Path: `docs/2026-03-23/opus/rol-live-merge-t3-contracts-context-regression-evidence.md`
Baseline Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
Baseline Dirty Summary: `dirty workspace with Stage 4 bottleneck fixes, live fresh-run artifacts, and survey/doc backlog`

---

## Source Files Inspected

### Pre-Director Contract Surface
- `modules/core/pre_director_checklist.py` (679 lines)
- `modules/core/pre_director_manuscript_checker.py` (~460 lines)

### Chief Writer Context / Prompts
- `modules/domain/agents/chief_writer_context.py` (542 lines)
- `modules/domain/agents/chief_writer_prompts.py` (281 lines)
- `modules/domain/agents/chief_writer_context_packets.py` (~945 lines)

### Validation Contracts
- `modules/validation/blocking_validator_scene_checks.py` (493 lines)
- `modules/validation/scoring_validator.py` (1,287 lines)
- `modules/validation/validation_orchestrator.py` (1,675 lines)
- `modules/validation/blocking_validator.py` (208 lines)

### Tests
- `tests/test_blocking_validator_submodules.py` (323 lines, 23 tests)
- `tests/test_pre_director_submodules.py` (286 lines, 28 tests)
- `tests/test_chief_writer_context.py` (472 lines, 41 tests)
- `tests/test_blueprint_ensemble_generate_ensemble.py` (220 lines, 9 tests)
- `tests/test_blueprint_patch_mode.py` (939 lines, 32 tests)
- `tests/test_stage3_orchestrator.py` (1,687 lines, 81 tests)
- `tests/test_stage4_interview_round.py` (7,989 lines, 219 tests)
- `tests/test_director_modules.py` (2,287 lines, 119 tests)

### Config / Constants
- `config/models.yaml` (66 lines)
- `modules/core/constants.py` (~894 lines)
- `modules/core/models_config.py` (98 lines)
- `modules/core/config_manager.py` (269 lines)

## Live Run Evidence

### Console Evidence
- `docs/2026-03-23/console.txt` (1,233 lines)
- Run terminal state: stopped (Arc 2 Stage 2 batch enrichment, L1162)
- Ep1: Round 1 PASS (score=96)
- Ep2: Round 1 PASS (score=95)
- Ep3: Round 1 REJECT (score=44, continuity_firewall), Round 2 PASS_WITH_FIX (score=90) -> post-select REJECT, Round 3 PASS (score=95) -> post-select REJECT, Round 4 PASS (score=95) -> post-select REJECT, Round 5 PASS (implied from Ep3 completion at L1105)
- Scene completeness `0/5` appeared on ALL candidates in ALL rounds for ALL episodes

### Prior Survey Docs
- `docs/2026-03-23/rol-freshrun-evidence-bottleneck-remediation-plan.md`
- `docs/2026-03-23/pre-rerun-root-cause-merge-audit.md`
- `docs/2026-03-23/q1-q8-r2-merge-audit.md`

## Key Evidence Anchors

### Scene-Completeness False Positive Chain
1. `blocking_validator_scene_checks.py:135` -- `_check_scene_completeness` entry
2. `blocking_validator_scene_checks.py:158-159` -- primary header regex (fails: no headers in prose)
3. `blocking_validator_scene_checks.py:167-172` -- fallback keyword path (fails: keywords don't match)
4. `blocking_validator_scene_checks.py:179-183` -- 50% threshold triggers HIGH
5. `stage4_interview_round.py:3501` -- tagged as `[Python검증-HIGH]`

### Context Priority Inversion Chain
1. `chief_writer_prompts.py:103` -- chain_link_section (early, carries prev location/time)
2. `chief_writer_prompts.py:137` -- prev_digest (carries last location)
3. `chief_writer_prompts.py:139` -- continuity instruction ("자연스럽게 이어져야 한다")
4. `chief_writer_prompts.py:146` -- prev_ending (raw 2500 chars)
5. `chief_writer_prompts.py:148` -- opening_anchor (arrives LAST, structurally outvoted)

### CONDITIONAL_PASS Gap
1. `modules/domain/agents/director_ensemble.py:1187-1194` -- can leave `CONDITIONAL_PASS`
2. `modules/core/stage4_interview_round.py:3787` -- only checks PASS/PASS_WITH_FIX as positive
3. `tests/test_stage4_interview_round.py` -- NO explicit CONDITIONAL_PASS routing test

### Truncation Sites ([:N] slicing in T3 scope)
- `chief_writer_context_packets.py:59` -- `prev_manuscript[-2500:]`
- `chief_writer_context_packets.py:279` -- `cliffhanger[:50]`
- `chief_writer_context.py:295` -- `_s1_summary[:200]`
- `chief_writer_context.py:410` -- `ending_avoid_phrases[:5]`
