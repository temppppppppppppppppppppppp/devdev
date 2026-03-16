<!-- [참고자료] -->
# TF-020 Test Coverage Mapping Report

Date: 2026-03-15
Status: final
Canonical Path: `docs/2026-03-15/tf-020-test-coverage-mapping-report.md`
Commit State:
- Baseline Commit: `bbb00a77c7356a32fe6358642cff0d3d445b7e8e`
- Baseline Dirty Summary: `dirty: active roadmap/temp docs, post-remediation bundle docs, runtime/operator and Stage 4 follow-up edits, projects/000 artifacts, and unrelated historical doc churn`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `TF-012 is implemented, TF-013, TF-017, and TF-018 are already closed, and TF-020 is being finalized as a bounded coverage-mapping report for the remaining residual lane`
Parent Lane: `docs/2026-03-15/post-remediation-unqueued-survey-followups-execution-ssot.md`
TF Composition Source: `docs/2026-03-15/codebase-global-post-remediation-tf-composition.md`
Source Evidence:
- `docs/2026-03-15/post-remediation-unqueued-survey-followups-execution-ssot.md`
- `docs/2026-03-15/codebase-global-post-remediation-tf-composition.md`
- `pyproject.toml`
- `.github/workflows/test.yml`
- `docs/2026-03-15/tf-020-test-coverage-report.txt`
- `docs/2026-03-15/tf-020-test-coverage-report.json`
- `logs/pytest_lowmem/tf020_20260315_235935/`

## 1. Intent
- Produce a saved module-level coverage baseline for `TF-020`.
- Replace the stale survey headline (`315` tests vs `244` modules) with current workspace counts and a real coverage artifact.
- Keep the output bounded to one report artifact rather than widening into immediate test-fix implementation.

## 2. Capture Method
- Current workspace counts are:
  - `245` Python module files under `modules/`
  - `309` `test_*.py` files under `tests/`
- Of those module files, `241` currently contain executable statements according to Coverage.py.
- The workspace already supports `pytest --cov=modules` in `.github/workflows/test.yml`, but no dated saved coverage map existed in the March 15 post-remediation bundle.
- Local baseline command:
  - `python scripts/run_pytest_lowmem.py tests --chunk-size 12 --keep-going --log-dir logs/pytest_lowmem/tf020_20260315_235935 --pytest-arg=--cov=modules --pytest-arg=--cov-append --pytest-arg=--cov-report=term-missing:skip-covered`
- Coverage artifacts were then materialized as:
  - `docs/2026-03-15/tf-020-test-coverage-report.txt`
  - `docs/2026-03-15/tf-020-test-coverage-report.json`

## 3. Baseline Totals
- Low-memory run shape:
  - `26` shards total
  - `14` passed
  - `12` failed
- Cumulative module coverage captured before shard failures stopped individual shards:
  - `60.63%` total line coverage
  - `36,839` covered lines
  - `23,924` missing lines
  - `60,763` executable statements
- This is therefore a useful repo-wide baseline, but not a clean all-green suite proof.

## 4. High-Signal Module Coverage
- DI and runtime contract surfaces:
  - `modules/core/stage2_context.py` -> `92.38%` (`97/105`)
  - `modules/core/stage3_context.py` -> `100.00%` (`30/30`)
  - `modules/core/stage4_context.py` -> `96.30%` (`104/108`)
- Stage 2/4 runtime-heavy modules:
  - `modules/core/stage2_preflight.py` -> `69.30%` (`666/961`)
  - `modules/core/stage2_finalizer.py` -> `31.83%` (`311/977`)
  - `modules/core/stage2_validation_pipeline.py` -> `72.12%` (`370/513`)
  - `modules/core/stage4_context_builder.py` -> `73.58%` (`1298/1764`)
  - `modules/core/stage4_interview_round.py` -> `72.84%` (`1859/2552`)
- Shared infrastructure:
  - `modules/core/db_manager.py` -> `65.07%` (`1125/1729`)
  - `modules/api/bridge_server.py` -> `77.30%` (`589/762`)
  - `modules/core/services/ui_service.py` -> `85.06%` (`131/154`)
  - `modules/core/services/project_service.py` -> `84.73%` (`355/419`)
  - `modules/validation/validation_orchestrator.py` -> `73.96%` (`571/772`)

## 5. Zero-Coverage Modules
- `modules/core/pacing_analyzer.py` -> `0.00%`
- `modules/domain/agents/continuity_inspector.py` -> `0.00%`
- `modules/core/agent_intelligence.py` -> `0.00%`
- `modules/domain/agents/state_locked_arc_generator.py` -> `0.00%`
- `modules/core/data_collector.py` -> `0.00%`
- `modules/core/quality_amplifier.py` -> `0.00%`
- `modules/core/failure_learning.py` -> `0.00%`
- `modules/core/multi_agent_deliberation.py` -> `0.00%`
- `modules/core/adversarial_self_play.py` -> `0.00%`
- `modules/core/dynamic_prompt_weighting.py` -> `0.00%`
- `modules/core/error_helper.py` -> `0.00%`
- `modules/core/expert_mixture.py` -> `0.00%`
- `modules/core/material_db.py` -> `0.00%`
- `modules/core/jianghu_logic.py` -> `0.00%`
- `modules/core/karma_service.py` -> `0.00%`
- `modules/core/technique_weaver.py` -> `0.00%`

## 6. Representative Low-Coverage Modules
- `modules/core/arc_summary_utils.py` -> `6.67%`
- `modules/domain/agents/preflight_checker.py` -> `8.84%`
- `modules/domain/agents/critic.py` -> `9.28%`
- `modules/domain/agents/arc_corrector.py` -> `9.82%`
- `modules/core/reference_anchor.py` -> `11.02%`
- `modules/validation/retrospective_validator.py` -> `11.24%`
- `modules/domain/agents/block_enricher.py` -> `12.00%`
- `modules/core/diversity_sampler.py` -> `12.56%`
- `modules/api/prompt_classifier.py` -> `14.04%`
- `modules/core/stage0/spinner.py` -> `15.82%`
- `modules/core/lore_manager.py` -> `16.74%`
- `modules/domain/agents/blueprint_constraint_compiler.py` -> `18.01%`
- `modules/core/tree_of_thoughts.py` -> `18.36%`
- `modules/domain/agents/writer.py` -> `22.34%`
- `modules/core/power_scaling.py` -> `24.06%`
- `modules/core/emotion_tracker.py` -> `24.75%`

## 7. Blockers Observed During Coverage Collection
- The low-memory full-suite run did not finish green.
- Failed shard families were concentrated in two patterns:
  - `6` shards hit `UnicodeEncodeError` from CP949 console writes on emoji-bearing `print(...)` paths in Stage 2 runtime/finalizer flows.
  - `3` shards hit `_FakeDirector` test doubles missing `_operator_log` after current director-ensemble contract changes.
  - `3` additional shards showed mixed failure output that included both contract and encoding families.
- Those failures do not invalidate the captured baseline, but they do limit how confidently this report can be used as a release gate or final CI-quality coverage statement.

## 8. Operating Consequence
- TF-020 is satisfied by this saved coverage mapping report plus the raw module-level coverage artifacts.
- No successor execution SSOT is required for TF-020 itself.
- The residual lane stays active only for the later bounded hardening tranche: `TF-014`, `TF-015`, `TF-016`, and `TF-019`.
- If coverage is later needed as a hard gate, rerun the full suite after fixing the two blocker families above so the baseline becomes a clean green coverage proof rather than a partial best-effort map.
