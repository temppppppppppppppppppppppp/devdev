# Golden Canary Stage4 ep14 Strong Advisory Localfix Backfill Execution SSOT

Date: 2026-04-22
Status: active
Canonical Path: `docs/2026-04-22/golden-canary-stage4-ep14-strong-advisory-localfix-backfill-execution-ssot.md`
Temp Mirror Path: `docs/temp/golden-canary-stage4-ep14-strong-advisory-localfix-backfill-execution-ssot.md`
Commit State:
- Baseline Commit: `4a8f03a9370ba06eacdb3075389147c74056bc8c`
- Baseline Dirty Summary: `dirty: tracked runtime artifacts in benchmarks and projects/골든 카나리아 logs/db; untracked drafts and stage4 artifacts for ep_0011-ep_0014`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-04-22/golden-canary-stage4-current-context-and-rerun-readiness.md`
- `docs/2026-04-22/golden-canary-stage4-ep14-strong-advisory-localfix-backfill-3pass-audit.md`
Evidence Artifacts:
- `projects/골든 카나리아/logs/stage4_direct_supervised_guarded_result.json`
- `projects/골든 카나리아/logs/episode_production.jsonl`
- `projects/골든 카나리아/logs/session/decisions.jsonl`
- `projects/골든 카나리아/logs/session_20260422_191329.log`
- `projects/골든 카나리아/logs/artifacts/stage4/ep_0014/`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_reject_runtime.py`
Side-Effect Coverage: covered

## 1. Intent

- Unblock the `ep14` rerun loop by repairing the strong-advisory backfill seam in one bounded place.
- Cover both observed invalid-contract shapes:
  - inherited runtime `scene_model` sentinel that should be replaceable by a bounded local contract
  - already-local fix-pack that still fails because guard and success fields remain blank

## 2. Baseline Facts

- The rerun persisted `ep11`, `ep12`, and `ep13`; no final `ep14` draft exists.
- `ep14` failed five times with `gate_basis=strong_advisory_escalation_non_local_fix`.
- The failure loop contains two contract shapes:
  - attempts with inherited `scene_model` sentinel
  - an attempt with `local_phrase` target but missing `do_not_regress` and `success_condition`
- The bug owner remains `_backfill_strong_advisory_fix_pack()` in `modules/core/stage4_interview_round.py`.

## 3. Scope

Included:

- `modules/core/stage4_interview_round.py`
- `tests/test_stage4_advisory_escalation_seam.py`
- `tests/test_stage4_interview_round.py`
- queue docs for this new front-active execution lane

Excluded:

- `modules/core/stage4_reject_runtime.py`
- wider Stage4 architecture refactors
- rerun execution itself
- runtime artifacts under `projects/골든 카나리아/`

## 4. Pass 1. Inventory Summary

- One production seam owns the bug: `_backfill_strong_advisory_fix_pack()`
- One reject-runtime surface creates the inherited sentinel: `_build_explicit_non_local_fix_pack()`
- Existing tests already cover both guardrails:
  - strong-advisory escalation and local backfill paths in `tests/test_stage4_advisory_escalation_seam.py`
  - generic `scene_model` downgrade and reject logging contracts in `tests/test_stage4_interview_round.py`

## 5. Pass 2. Semantic Classification

- Class A: inherited runtime `scene_model` sentinel that is only a retry-routing placeholder and may be replaceable
- Class B: advisory-specific local builders for `npc_drift` and `flashback` that can already synthesize local contracts
- Class C: local target kinds whose contract is still incomplete because generic backfill stopped early
- Class D: explicit or genuinely non-local `scene_model` contracts that must keep rejecting

## 6. Side-Effect Map

- file writes / artifacts: code files and queue docs only
- DB / schema / transaction boundaries: not applicable
- JSONL / log / audit sinks: no runtime sink mutation planned
- console / UI / operator output: pytest and validator output only
- rollback / recovery / retry: no change to retry contract beyond fix-pack completeness
- cache / global state: limited to Stage4 in-memory advisory metadata already present
- bootstrap fallback / config-env mutation: not applicable

## 7. Realization Architecture

- Keep reject-runtime sentinel generation intact.
- Narrow the change to the strong-advisory backfill seam:
  - identify the inherited runtime sentinel by `target_kind="scene_model"` plus sentinel markers
  - if a local advisory builder can synthesize a bounded contract, clear the inherited sentinel and reuse the existing zero-to-local synth branch
  - if the target is already local but `do_not_regress` or `success_condition` is blank, complete those fields with bounded generic backfill
  - otherwise preserve the current `scene_model` reject path
- Validate with seam tests plus the generic `scene_model` downgrade guard.

## 8. Execution Tranches

1. Create and audit the governing audit doc and execution SSOT.
2. Patch `_backfill_strong_advisory_fix_pack()` with sentinel override and local-contract completion.
3. Add regression tests for sentinel override, generic local completion, and explicit non-local preservation.
4. Run targeted pytest plus temp-queue validation.

## 9. Acceptance Criteria

- Inherited runtime `scene_model` sentinel no longer blocks a bounded `npc_drift` or `flashback` local fix-pack when one is synthesizable.
- Already-local fix-packs do not fail solely because `do_not_regress` or `success_condition` stayed blank.
- Explicit or truly scene-level `scene_model` contracts still route to `REJECT`.
- Targeted tests pass.
- No runtime artifacts or project DB state are mutated by this patch batch.

## 10. Verification Plan

- `pytest tests/test_stage4_advisory_escalation_seam.py tests/test_stage4_interview_round.py -q`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails

- Do not weaken `_evaluate_fix_pack_contract()`.
- Do not alter reject-runtime sentinel synthesis semantics for genuinely non-local retries.
- Do not refactor unrelated Stage4 owner-surface areas in this batch.
- Do not claim rerun success without a fresh guarded run.

## 12. Temp Queue Notes

- temp status: `in_progress`
- cleanup condition: keep this mirror until the bounded patch is validated and the follow-up rerun decision is resolved
- roadmap dependency: first item in the refreshed active temp roadmap

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-audit confirmed in the same batch with confidence above 95%
