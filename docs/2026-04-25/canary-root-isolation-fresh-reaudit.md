# Canary Root Isolation Fresh Re-Audit

Date: 2026-04-25
Status: final
Canonical Path: `docs/2026-04-25/canary-root-isolation-fresh-reaudit.md`
Commit State:
- Baseline Commit: `324c0d270b61496058dbdacdec24fa7d89849446`
- Baseline Dirty Summary: `clean main after PR #14 merge; fresh branch feat/canary-root-isolation opened for canary-root-isolation activation`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Docs:
- `docs/2026-04-24/canary-root-isolation-execution-ssot.md`
- `docs/2026-04-24/canary-root-isolation-plan.md`
- `docs/2026-04-24/canary-root-isolation-adversarial-3pass-audit.md`
- `docs/2026-04-24/active-temp-execution-roadmap.md`
Evidence Surfaces:
- `scripts/canary_path_utils.py`
- `scripts/run_stage2_canary.py`
- `scripts/run_stage3_canary.py`
- `scripts/run_stage34_canary.py`
- `scripts/run_stage34_ep_demo_canary.py`
- `scripts/run_stage4_canary.py`
- `scripts/canary_stage2_headless.py`
- `modules/core/runtime_paths.py`
- `tests/test_canary_path_utils.py`
- `tests/test_run_stage2_canary.py`
- `tests/test_run_stage3_canary.py`
- `tests/test_run_stage34_canary.py`
- `tests/test_run_stage34_ep_demo_canary.py`
- `tests/test_run_stage4_canary.py`
- `.gitignore`
Side-Effect Coverage: path resolution, file artifact root, subprocess environment, runtime boot environment, legacy read fallback, and Git ignore policy

## 1. Question

Can `canary-root-isolation` move from parked future-wave status into the next bounded implementation unit after Stage0 runtime handoff closure on `2026-04-25`?

## 2. Answer

Yes. Open `canary-root-isolation` as the front-active queue item, with a narrow implementation boundary:

- route new canary targets to repo-local `canary/<target>`
- keep legacy reads for `projects/_canary/<target>`
- scope `GEULDOBI_PROJECTS_ROOT=<repo>/canary` only during canary runtime execution
- pass that scoped environment into the Stage 2 headless subprocess
- add `canary/` to Git ignore policy

Do not move, delete, rewrite, or archive existing `projects/_canary/` data in this unit.

## 3. Current-State Findings

- `scripts/canary_path_utils.py` still uses `CANARY_ROOT_NAME = "_canary"` and resolves canary targets under `projects/_canary`.
- `modules/core/runtime_paths.py` already supports `GEULDOBI_PROJECTS_ROOT`, so the runtime can boot against a scoped alternate projects root without a broader runtime redesign.
- Stage 2 canary execution uses `scripts/canary_stage2_headless.py` via `subprocess.run()`, so subprocess env propagation is part of the required patch.
- The focused tests still assert legacy `projects/_canary` write behavior and must be updated to prove the new default root plus legacy fallback.
- `.gitignore` currently ignores `projects/canary_*/` but does not ignore a repo-local generated `canary/` tree.

## 4. Bounded Implementation Shape

Allowed next patch:

- update `scripts/canary_path_utils.py` as the single routing owner for canary root semantics
- add scoped canary runtime environment helpers in the same helper module
- update canary runner scripts to boot/analyze under the scoped canary projects root
- pass the scoped env to the Stage 2 subprocess
- update focused tests for new root, legacy fallback, env restore, and subprocess env propagation
- add `canary/` to `.gitignore`

Not allowed in this unit:

- no migration of `projects/_canary/`
- no deletion of old canary output
- no historical evidence rewrite
- no normal project root behavior change
- no trashbox cleanup
- no broad runtime or desktop path redesign

## 5. Activation Decision

Decision: activate the parked lane as front-active `canary-root-isolation`.

Required queue updates:

- change canonical and temp canary SSOT status from parked/execution-ready to `in_progress`
- change execution metadata status to `in_progress`
- change execution metadata queue role to `front_active`
- normalize canary roadmap rank to `1`
- keep repo-trashbox-cleanup parked behind canary-root-isolation
- add this fresh re-audit as the current activation anchor

## 6. Validation Plan

Focused validation for the implementation unit:

- `python -m py_compile scripts/canary_path_utils.py scripts/run_stage2_canary.py scripts/run_stage3_canary.py scripts/run_stage34_canary.py scripts/run_stage34_ep_demo_canary.py scripts/run_stage4_canary.py scripts/canary_stage2_headless.py`
- `py -3.12 -m pytest tests/test_canary_path_utils.py tests/test_run_stage2_canary.py tests/test_run_stage3_canary.py tests/test_run_stage34_canary.py tests/test_run_stage34_ep_demo_canary.py tests/test_run_stage4_canary.py -q`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`
- `python scripts/check_utf8_hygiene.py <touched files>`
- `git diff --check`

Optional read-only legacy smoke remains optional and must not move or create legacy data.

## 7. 3-Pass Audit

Pass 1. Structure/scope:

- The queue now has two parked items, and canary-root-isolation is rank 1.
- The implementation unit is bounded to helper routing, scoped env, subprocess env, focused tests, and ignore policy.
- Trashbox cleanup remains parked and dependent on canary policy settlement.

Pass 2. Evidence/current-state:

- Live code confirms the legacy `projects/_canary` default.
- Live runtime path code confirms `GEULDOBI_PROJECTS_ROOT` already exists as the correct runtime binding mechanism.
- Live tests confirm expected assertions must change from legacy write behavior to new `canary/` default plus legacy fallback.

Pass 3. Execution/readability:

- The next reader can implement from this re-audit without re-reading stale queue status.
- Guardrails explicitly prohibit migration, deletion, historical rewrite, normal project behavior changes, and trashbox cleanup.
- Validation targets are focused and fit the Pytest memory rule.

Confidence: 96/100
