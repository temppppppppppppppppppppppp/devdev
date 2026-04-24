# Canary Root Isolation Adversarial 3-Pass Audit

Date: 2026-04-24
Status: completed (documentation-only adversarial audit; execution parked, no code change authorized)
Source Plan: `docs/2026-04-24/canary-root-isolation-plan.md`
Related Hygiene Survey: `docs/2026-04-24/repo-trashbox-candidate-survey.md`

## 1. Audit Target

Target proposal:

- stop writing new canary runs under `projects/_canary/`
- introduce a repo-local `canary/` root for future canary runs
- keep existing `projects/_canary/` data unmoved in the first pass
- preserve legacy read fallback for old canary evidence
- scope `GEULDOBI_PROJECTS_ROOT=<repo>\canary` only during canary execution

Non-goal:

- no migration of existing canary data
- no cleanup of `projects/_canary/`
- no implementation in this turn

## 2. Pass 1: Path Resolution Attack

Adversarial question:

Could the new `canary/` root silently break existing operator commands that pass `_canary/<name>` or `projects/_canary/<name>`?

Findings:

- Current code concentrates canary path routing in `scripts/canary_path_utils.py`.
- Existing tests assert that new canary targets land under `projects/_canary`; those tests must change before implementation is trusted.
- Historical docs contain many `projects/_canary` references. Rewriting those docs would destroy evidence semantics and is out of scope.
- Explicit absolute paths must remain absolute.
- Explicit `projects/<name>` must continue to mean real projects root, not canary root.

Required mitigation:

- add new helper semantics instead of ad hoc path edits in every canary script
- keep `projects/_canary/<name>` as read fallback only
- update focused path tests first
- do not rewrite historical proof docs

Pass 1 verdict:

The proposal is safe only if implemented at the path-helper layer with legacy fallback. Direct bulk replacement of `_canary` strings is unsafe.

## 3. Pass 2: Runtime Boot Attack

Adversarial question:

Could path resolution point to `canary/<name>` while `SovereignApp` still boots against the normal `projects/` root and either fail or create duplicate data?

Findings:

- Runtime project resolution already supports `GEULDOBI_PROJECTS_ROOT`.
- Canary scripts boot `SovereignApp` through runtime project names derived by `project_name_from_path()`.
- If `project_name_from_path()` returns a normal-looking project name but `GEULDOBI_PROJECTS_ROOT` is not set to `canary/`, runtime boot will look in `projects/<name>`.
- Stage 2 runs through a subprocess, so the canary projects root must be passed into the subprocess environment as well.
- Environment leakage would be dangerous: normal operator runs must not inherit `GEULDOBI_PROJECTS_ROOT=<repo>\canary`.

Required mitigation:

- wrap canary run/analyze execution in a scoped environment manager
- restore the previous `GEULDOBI_PROJECTS_ROOT` after every run, including error paths
- pass the scoped environment into Stage 2 subprocess calls
- add tests that assert the environment is restored

Pass 2 verdict:

The proposal is safe only with scoped runtime environment handling. Path helper changes alone are incomplete.

## 4. Pass 3: Repository Hygiene Attack

Adversarial question:

Could the new `canary/` root become a second noisy tracked artifact tree and fail the original goal?

Findings:

- Canary projects contain copied DBs, logs, drafts, blueprints, and artifacts.
- If `canary/` is not ignored, the repository will simply move clutter from `projects/_canary` to `canary/`.
- Keeping a tracked `canary/README.md` is optional, but the simplest safe policy is to ignore all generated canary output.
- Existing `projects/_canary/` remains large and noisy until separately cleaned up. The first pass prevents new clutter but does not erase old clutter.

Required mitigation:

- add `canary/` to `.gitignore` after implementation tests pass
- leave old `projects/_canary/` untouched until a separate cleanup decision
- keep the execution item parked so it is not accidentally treated as current patch authority

Pass 3 verdict:

The proposal meets the hygiene goal for future output only. Existing canary residue remains a separate cleanup item.

## 5. Consolidated Decision

Decision: park as a future execution wave.

Implementation is feasible and bounded, but it crosses runtime path resolution, boot environment scoping, subprocess behavior, and Git hygiene. It should not be patched casually while other queue items and live project state are dirty.

Confidence: 96/100

## 6. Required Execution Conditions

Before implementation:

- re-check `scripts/canary_path_utils.py`
- re-check all `scripts/run_stage*_canary.py` entrypoints
- confirm current `GEULDOBI_PROJECTS_ROOT` behavior still works
- update focused tests before running broad tests

During implementation:

- no existing canary data move
- no historical doc rewrite
- no real project path behavior change
- no default runtime workspace behavior change outside canary scripts

After implementation:

- prove new targets write under `canary/`
- prove legacy read fallback still reads `projects/_canary/`
- prove `GEULDOBI_PROJECTS_ROOT` restoration
- prove generated `canary/` output is ignored by Git

