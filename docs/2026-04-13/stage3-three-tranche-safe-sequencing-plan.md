# Stage3 Three-Tranche Safe Sequencing Plan

- Date: 2026-04-13
- Status: active-plan-support (baseline snapshot and tranche 1 are committed, tranche 2 is now landed on the live workspace, and tranche 3 is the immediate-next action)
- Scope: Stage3 cost-first refactor sequencing on current `main`, with mandatory static validation and snapshot commits between tranches
- Mode: execution-support planning note; no live rerun and no code realization in this note itself
- Canonical Path: `docs/2026-04-13/stage3-three-tranche-safe-sequencing-plan.md`
- Baseline Commit: `347acac374f7246cca433d4be9c7466e802c9883`
- Baseline Dirty Summary: `dirty: active Stage3 code/docs/tests plus live-run artifacts, logs, and polaris planning docs already present in worktree`
- Resume Commit: `765132d8d5d45c3dadffb260ac37c2ef0b94fe94`
- Resume Drift Summary: `the baseline snapshot commit now isolates the earlier Stage3/doc state, tranche 1 Stage3RepairRouter extraction is committed, and tranche 2 strict local-fix contract gating is now landed on the live workspace with static validation rerun, so this note now advances the immediate-next action to tranche 3`
- Confidence: `97%`

## Purpose

This note fixes the operator-safe order for the next Stage3 refactor wave.

The goal is not to move fastest.

The goal is to move safely, with:

- one tranche at a time
- static validation only inside each tranche
- mandatory snapshot commit before the next tranche starts
- no paid live rerun until the three static tranches are landed

This note intentionally overrides the cheaper earlier suggestion of `rerun after the next parent tranche`.

For the current operator preference, the safer route is:

1. Tranche 1
2. static validation
3. snapshot commit
4. Tranche 2
5. static validation
6. snapshot commit
7. Tranche 3
8. static validation
9. snapshot commit
10. one fresh proof rerun

## Why This Is The Safer Route

The current Stage3 parent lane already landed the first cost-first tranche:

- contract-driven repair eligibility
- success-state projection normalization

But the operator preference is now stronger:

- avoid patchy growth
- prefer orderly architecture work
- accept slower speed in exchange for bounded risk

Under that preference, the safest next move is not immediate proof.

The safest next move is to freeze the next three refactor tranches and force commit boundaries between them.

## Non-Negotiable Operating Rules

1. Only one tranche may be active at a time.
2. A tranche is not allowed to overlap with the next tranche.
3. Each tranche must end with static validation only:
   - targeted `pytest`
   - `py_compile`
   - `python scripts/check_utf8_hygiene.py ...`
   - `python scripts/ops_validator.py --strict`
4. No live rerun is allowed inside tranche 1, 2, or 3.
5. A snapshot commit on `main` is required after each tranche before the next tranche begins.
6. Snapshot commits must stay tranche-scoped:
   - code
   - tests
   - canonical docs
   - temp execution mirrors if touched
7. Live-run artifacts, DB files, logs, and unrelated planning drafts must not be bundled into the tranche commit unless explicitly chosen as a separate evidence commit.
8. If static validation confidence drops below the intended design confidence, stop before the next tranche.

## Tranche Sequence

### Tranche 1. Stage3RepairRouter Extraction

Goal:

- separate Stage3 repair-routing decisions into one authoritative routing surface

Bounded scope:

- extract the decision logic that currently determines:
  - local patch reopen
  - single-strategy regenerate
  - full regenerate
  - terminal warning acceptance / failure handoff boundaries
- keep behavior meaning as close as possible to the current landed code
- this tranche is about authority consolidation, not policy tightening

Allowed changes:

- refactor runtime decision code into one router object or one bounded routing module
- centralize routing inputs and outputs
- normalize operator-visible route metadata

Not allowed in tranche 1:

- stricter eligibility rules beyond current landed semantics
- new target-kind allowlists
- patch IR activation
- live rerun

Required validation:

- `tests/test_blueprint_patch_mode.py`
- any new targeted router extraction tests if introduced
- `py_compile`
- UTF-8 hygiene
- `ops_validator --strict`

Required closure:

- snapshot commit on `main`

Current state:

- tranche 2 is now landed on the live workspace
- Stage3 local patch entry now fails closed without a ready local-fix contract
- missing authoritative scope, patch target records, `must_fix`, or `success_condition` now route back to regenerate instead of silently reopening faux-inplace
- tranche 3 is now the immediate-next move after this tranche-scoped snapshot commit lands

Current state:

- tranche 1 is now landed on the live workspace as an authority-consolidation refactor
- repair reopen / `PASS_WITH_FIX` routing now flows through one `Stage3RepairRouter` surface
- tranche 2 is now the immediate-next move after this tranche-scoped snapshot commit lands

### Tranche 2. Strict Local-Fix Contract Gate

Goal:

- make local patch entry fail-closed unless a truly ready local-fix contract exists

Bounded scope:

- require explicit contract readiness for local patch:
  - authoritative local scope
  - supported target kind
  - explicit patch targets / target records
  - `must_fix`
  - `success_condition`
- convert missing or non-local contracts into regenerate routing

Allowed changes:

- stricter contract readiness checks
- contract payload normalization
- stronger tests around negative and positive local-fix entry

Not allowed in tranche 2:

- patch IR execution
- whole-generator redesign
- live rerun

Required validation:

- `tests/test_blueprint_patch_mode.py`
- `tests/test_unified_blueprint_validator_lane_c.py` if contract payloads change
- Stage3 orchestrator tests if projection payloads change
- `py_compile`
- UTF-8 hygiene
- `ops_validator --strict`

Required closure:

- snapshot commit on `main`

### Tranche 3. Faux-Inplace Reduction / Patch-IR Preparation

Goal:

- reduce or replace the remaining faux-inplace whole-blueprint rewrite lane in a controlled way

Landed result on the live workspace:

- the first bounded Stage3 patch-IR lane now exists for leaf/path-scoped targets only
- current supported target kinds are `dialogue`, `entity_ref`, `field_value`, `local_phrase`, and `local_sentence`
- unresolved or unresolvable target snapshots fail closed before the local patch call
- broader `scene_block`-style repair still stays on the legacy whole-blueprint lane for now

Bounded scope:

- either:
  - shrink faux-inplace eligibility to a smaller family set
  - or introduce the first bounded Stage3 patch-IR / path-scoped lane

Allowed changes:

- generator-side lane split
- new patch-plan structures
- path-targeted or field-targeted local repair scaffolding

Not allowed in tranche 3:

- broad DecisionKernel migration
- unrelated queue compaction work
- live rerun before static closure

Required validation:

- `tests/test_blueprint_patch_mode.py`
- any generator-side targeted tests
- Stage3 orchestrator tests if success projection changes again
- `py_compile`
- UTF-8 hygiene
- `ops_validator --strict`

Required closure:

- snapshot commit on `main`

### Proof Step. Fresh Rerun After Tranche 3

Goal:

- only after tranche 1, 2, and 3 are individually landed and committed, run one fresh proof rerun

Primary proof targets:

- `ep7/ep8`
- no binding-driven faux-inplace churn
- no non-local contract slipping into local patch
- no success-state sink mismatch

## Commit Discipline

Every tranche must produce a narrow snapshot commit.

Recommended shape:

- commit 1: `refactor: extract stage3 repair router`
- commit 2: `fix: enforce stage3 local repair contract gate`
- commit 3: `refactor: introduce stage3 blueprint patch ir`

Commit content should be path-scoped.

Do not use a broad `workspace snapshot` commit for these tranches.

If unrelated dirt is present in the worktree, commit only the tranche-owned files.

## Stop Conditions

Stop before the next tranche if any of the following happens:

- routing meaning changes more than intended in tranche 1
- contract semantics become ambiguous in tranche 2
- tranche 3 expands beyond bounded patch-lane preparation into general redesign
- static validation fails and the fix would require widening the tranche
- the worktree becomes too mixed to guarantee tranche-scoped commits

## Immediate Next Action

Tranche 3 is now landed on the live workspace and closed by static validation.

The next action is now:

- create the narrow tranche-3 snapshot commit on `main`
- then run one fresh proof rerun

That proof rerun should target `ep7/ep8` and verify the new bounded patch-IR lane without widening the tranche again.
