# Smoke Fixture Alignment Execution SSOT

Date: 2026-03-20
Status: active
Canonical Path: `docs/2026-03-20/smoke-fixture-alignment-execution-ssot.md`
Temp Mirror Path: `docs/temp/smoke-fixture-alignment-execution-ssot.md`
Commit State:
- Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
- Baseline Dirty Summary: `dirty: 128 tracked/other, 19 untracked; hotspots: docs/2026-03-20/, geuldobi-desktop/, projects/ disposable fixture clones`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-20/rol-global-live-run-preflight-watchlist.md`
- `docs/2026-03-20/rol-live-run-fixture-target-selection-audit.md`
- `docs/2026-03-20/rol-global-live-run-evidence-manifest.md`
- `docs/2026-03-20/rol-global-post-run-merge-audit.md`
- `docs/2026-03-20/smoke-fixture-alignment-3pass-audit.md`
Evidence Artifacts:
- `scripts/run_stage2_smoke.py`
- `scripts/run_stage3_smoke.py`
- `scripts/run_stage4_smoke.py`
- `scripts/prepare_smoke_fixture.py`
- `modules/core/smoke_fixture_tools.py`
- `geuldobi-desktop/scripts/build_workspace_seed.py`
- `dist/workspace-seed/projects/investment_canary_demo/`
- `projects/smoke_fixture_demo/`
- `projects/코덱스_테스트/`
- `projects/코덱스_테스트__seed_live_run_capture_20260320_092956/`
Side-Effect Coverage: covered

## 1. Intent

Align the bounded smoke stack around one official disposable fixture contract.

This execution item exists because the current smoke target name, packaged seed lineage, and actual lane richness requirements are misaligned:
- desktop spike works on the current seed lineage
- Stage 4 smoke works on the current seed lineage
- Stage 3 smoke requires a richer disposable fixture than the current seed lineage provides
- Stage 2 smoke currently completes in degraded form on the seed lineage

The goal is not to patch one script ad hoc. The goal is to define and realize one bounded smoke fixture contract that Stage 2/3/4 and desktop spike can rely on without mutating historical audit projects.

## 2. Baseline Facts

- `scripts/run_stage2_smoke.py`, `scripts/run_stage3_smoke.py`, and `scripts/run_stage4_smoke.py` currently assume `projects/코덱스_테스트`.
- `geuldobi-desktop/scripts/build_workspace_seed.py` and `dist/workspace-seed/` define the current packaged sample lineage.
- `dist/workspace-seed/projects/investment_canary_demo/` is sufficient for desktop spike and Stage 4 smoke.
- `investment_canary_demo` lineage is not sufficient for Stage 3 smoke because the live run exposed `arcs=2`, while Stage 3 smoke requires `arcs >= 3`.
- Stage 2 smoke on the seed lineage completed with degraded proof quality and produced `arc_3_failure_report.txt`.
- A disposable clone of `projects/0_260318` unblocked Stage 3 smoke, but historical audit projects should not become the official smoke fixture source.
- current realization now establishes `projects/smoke_fixture_demo/` as the canonical smoke fixture source lineage
- `geuldobi-desktop/scripts/build_workspace_seed.py` now sources from `projects/smoke_fixture_demo` while still packaging to `investment_canary_demo`
- `scripts/prepare_smoke_fixture.py` now exists as the bounded restore helper from canonical source to the hardcoded smoke target

## 3. Scope

Included:
- `scripts/run_stage2_smoke.py`
- `scripts/run_stage3_smoke.py`
- `scripts/run_stage4_smoke.py`
- `geuldobi-desktop/scripts/build_workspace_seed.py`
- `dist/workspace-seed/`
- bounded fixture selection/restore notes and related tests or docs

Excluded:
- general Stage 2/3/4 logic redesign
- broader desktop bridge/runtime work
- historical audit projects as permanent smoke targets
- unrelated survey bundle or roadmap updates

## 4. Pass 1. Inventory Summary

- smoke target hotspot: `projects/코덱스_테스트`
- smoke lane hotspot: Stage 3 requires richer fixture than packaged seed currently provides
- seed lineage hotspot: `investment_canary_demo`
- disposable clone hotspot: `projects/코덱스_테스트__seed_live_run_capture_20260320_092956/`
- builder hotspot: `geuldobi-desktop/scripts/build_workspace_seed.py`

## 5. Pass 2. Semantic Classification

- Class A. Target-name contract surfaces
  - smoke scripts
  - restore assumptions
- Class B. Fixture richness surfaces
  - arcs / blueprints / manuscript reset expectations
  - Stage 2/3/4 lane prerequisites
- Class C. Packaged seed lineage surfaces
  - desktop workspace seed builder
  - `dist/workspace-seed/`
- Class D. Safety and provenance surfaces
  - disposable clone handling
  - historical audit project non-mutation guardrails

## 6. Side-Effect Map

- file writes / artifacts:
  - fixture clone/reset under `projects/코덱스_테스트`
  - smoke outputs under `plans/` and `logs/`
- DB / schema / transaction boundaries:
  - disposable `project_data.db` replacement or regeneration
  - no production schema change should be required
- JSONL / log / audit sinks:
  - smoke scripts may emit failure reports and run logs
- console / UI / operator output:
  - desktop spike and smoke terminal summaries are affected
- rollback / recovery / retry:
  - fixture replacement must remain reversible via backup/clone strategy
- cache / global state:
  - not applicable beyond smoke-target filesystem state
- bootstrap fallback / config-env mutation:
  - seed builder output is part of the bounded fixture contract

## 7. Realization Architecture

- keep the official smoke target name bounded and disposable
- align one official fixture richness contract before considering target-name parameterization
- prefer packaged or builder-produced disposable fixture lineage over direct historical project usage
- keep historical audit projects as evidence sources only, not as runtime smoke targets

Recommended final shape:
- one official disposable smoke fixture lineage
- restore/build path that guarantees Stage 2/3/4 smoke prerequisites
- smoke scripts continue to operate against one consistent target contract
- direct historical project mutation remains forbidden

## 8. Execution Tranches

1. Contract tranche
   - define the minimum official smoke fixture richness contract
   - lock Stage 2/3/4 prerequisite counts and reset expectations
   - status: completed
2. Seed lineage tranche
   - align `investment_canary_demo` lineage or create a dedicated richer smoke fixture lineage
   - keep desktop seed compatibility explicit
   - status: completed
   - canonical source is now `projects/smoke_fixture_demo`
3. Script alignment tranche
   - only after the fixture contract is stable, adjust smoke restore/selection flow as needed
   - avoid premature hotfixing of hardcoded target naming
   - status: in_progress
   - bounded restore helper exists, but the smoke runners themselves are still unchanged
4. Verification tranche
   - rerun desktop spike
   - rerun Stage 2/3/4 smoke against the aligned disposable fixture
   - confirm no historical audit project is used as the live smoke target

## 9. Acceptance Criteria

- one official disposable smoke fixture contract is explicitly defined
- Stage 2/3/4 smoke all run against the same fixture contract or officially documented equivalent lineage
- Stage 3 no longer depends on a historical project clone to meet `arcs >= 3`
- Stage 2 no longer completes only in degraded form because of fixture poverty
- desktop spike remains compatible with the aligned fixture lineage

## 10. Verification Plan

- bounded reruns:
  - `npm run start:desktop-spike` from `geuldobi-desktop`
  - `python scripts/run_stage2_smoke.py`
  - `python scripts/run_stage3_smoke.py`
  - `python scripts/run_stage4_smoke.py`
- fixture truth checks:
  - verify `project_data.db`
  - verify arc / blueprint / manuscript prerequisite counts
- hygiene and queue validation:
  - `python scripts/check_utf8_hygiene.py docs/2026-03-20/smoke-fixture-alignment-execution-ssot.md docs/temp/smoke-fixture-alignment-execution-ssot.md`
  - `git diff --check -- docs/2026-03-20/smoke-fixture-alignment-execution-ssot.md docs/temp/smoke-fixture-alignment-execution-ssot.md`
  - `python scripts/ops_validator.py`

## 11. Guardrails

- do not treat historical audit projects as the permanent smoke fixture source
- do not patch smoke target names first and hope fixture richness problems disappear
- do not claim alignment if desktop spike and Stage 2/3/4 smokes still require different hidden fixture assumptions
- do not widen this item into a general Stage 2/3/4 runtime redesign

## 12. Temp Queue Notes

- temp status: in_progress
- cleanup condition:
  - remove temp mirror after fixture alignment is implemented and verified
- roadmap dependency:
  - none currently; single execution SSOT item

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule:
  - re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document
