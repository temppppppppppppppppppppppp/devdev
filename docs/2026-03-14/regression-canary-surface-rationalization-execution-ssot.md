# Regression and Canary Surface Rationalization Execution SSOT

Date: 2026-03-14
Status: ready for implementation
Canonical Path: `docs/2026-03-14/regression-canary-surface-rationalization-execution-ssot.md`
Temp Mirror Path: `docs/temp/regression-canary-surface-rationalization-execution-ssot.md`
Source Survey Docs:
- `docs/2026-03-14/codebase-global-rol-deep-global-survey.md`
- `docs/2026-03-14/codebase-global-rol-system-full-survey-3pass-audit.md`
Evidence Artifacts:
- `docs/2026-03-14/codebase-global-rol-deep-survey-inventory.json`
- `docs/2026-03-14/codebase-global-rol-deep-survey-regression-surface.txt`
- `docs/2026-03-14/codebase-global-rol-deep-survey-side-effects.json`
- `docs/2026-03-14/codebase-global-rol-system-survey-inventory.json`
- `docs/2026-03-14/codebase-global-rol-system-survey-regression-surface.txt`
- `docs/2026-03-14/codebase-global-rol-system-survey-side-effects.json`
Side-Effect Coverage: covered
Confidence Target: 95%
Live Workspace Revalidation: 2026-03-14 PASS
Revalidated Confidence: 96%

## 1. Intent
- Rationalize the regression surface into clearer tiers: read-only contract checks, mutation-heavy smoke tests, and canary proof runs.
- Make it easier to choose the right validation path before and after risky system changes.
- Reduce confusion between fixture-heavy mutation scripts and low-risk contract validation.

## 2. Baseline Facts
- The active surveyed regression surface now contains `305` current test files under `tests/`: `301` Python plus `4` JavaScript files.
- The repository also contains dedicated smoke/canary helpers:
  - `scripts/run_stage2_smoke.py`
  - `scripts/run_stage3_smoke.py`
  - `scripts/run_stage4_smoke.py`
  - `scripts/run_stage4_canary.py`
  - `scripts/run_stage34_canary.py`
  - `scripts/e2e_menu_smoke.ps1`
- Canary helpers boot live app flows, patch `input`, open project DBs, and write JSON summaries into project logs.
- Desktop contract tests and backend bridge tests are already a distinct read-only sub-surface and should remain independently runnable.

## 3. Pass 1. Inventory Summary
- regression partitions present:
  - root `tests/` contract and unit suite
  - `tests/e2e/`
  - `tests/integration/`
  - `tests/chaos/`
  - stage fixture projects under `tests/stage4_v2_test/` and `tests/stage3_isolated_test/`
- current test bucket signals:
  - `stage_pipeline 34`
  - `persistence_observability 18`
  - `desktop_ui 13`
  - `backend_control_plane 7`
- mutation-heavy helpers:
  - canary scripts
  - smoke scripts
  - fixture-project writers

## 4. Pass 2. Semantic Classification

### Class A. Read-Only Contract Checks
- desktop shadow and bridge contract tests
- API and transport contract tests
- ownership and runtime-path contract tests

### Class B. Focused Product Tests
- Stage 0 to Stage 4 unit and integration tests against mocked or isolated surfaces

### Class C. Mutation-Heavy Proving Runs
- canary and smoke helpers that clone projects, write JSON summaries, or drive live generation flows

## 5. Side-Effect Map
- file writes:
  - canary summaries and companion audits
  - fixture-project logs and stage outputs
- DB:
  - canary and fixture projects interact with project-local SQLite files
- console and prompt behavior:
  - smoke helpers still rely on direct `print` and patched `input`
- runtime mutation:
  - canary scripts boot real app surfaces and persist post-run state

## 6. Realization Architecture
- Define an explicit regression taxonomy:
  - contract-safe
  - focused mutation
  - full canary proof
- Make the chosen tier discoverable from script and test names, not only tribal knowledge.
- Ensure each major execution doc can point to the minimum validation tier it requires before and after landing changes.

## 7. Execution Tranches
1. Classify and document current regression assets into stable tiers.
2. Separate read-only contract subsets from mutation-heavy canary scripts in documentation and invocation helpers.
3. Align execution docs with recommended validation tiers so post-change verification is consistent.
4. Refresh helper names or wrappers only where ambiguity materially hurts operator choice.

## 8. Acceptance Criteria
- Contract-safe subsets can be identified and run without touching live project state.
- Mutation-heavy smoke/canary helpers are clearly labeled as such.
- Execution docs can point to bounded validation subsets instead of an undifferentiated test mass.
- Desktop/backend contract checks stay visible as a separate verification lane.

## 9. Verification Plan
- review `tests/` partition map and smoke/canary wrappers
- keep existing desktop/API contract subset runnable
- validate that documentation and helper names communicate mutation boundaries clearly

## 9A. Current-State Revalidation
- Revalidated against live workspace changes in `modules/core/stage4_canary_tools.py`, `scripts/run_stage4_canary.py`, `tests/test_run_stage4_canary.py`, and the surrounding desktop/runtime contract tests.
- The canary surface has become more explicit, not less: `run_stage4_canary.py` now writes both `canary_summary.json` and `canary_companion_audit.json`, and it exposes a `branch_inventory(...)` output path for proof coverage inventory.
- `stage4_canary_tools.py` now tracks companion audit status, branch coverage, and retry-path proof gaps. This is useful groundwork for tiering, but it also confirms that canary helpers remain mutation-heavy runtime probes rather than safe read-only checks.
- Current tests now assert artifact writes for companion audits and branch inventory output. That improves proof hygiene but does not yet create the contract-safe versus mutation-heavy taxonomy this document calls for.
- Revalidation outcome: document direction unchanged; this item remains the final queue step because it should codify validation tiers after upstream runtime, operator-surface, and desktop contracts settle.

## 10. Guardrails
- Do not collapse all validation into one oversized suite recommendation.
- Do not relabel mutation-heavy canaries as safe read-only checks.
- Do not couple regression-surface cleanup to product behavior changes in the same pass.

## 11. Temp Queue Notes
- temp status: pending
- cleanup condition: remove mirror after implementation and closure
- roadmap dependency: execute after upstream runtime, Stage 0, and desktop contracts settle enough to define stable validation tiers

## 12. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document
