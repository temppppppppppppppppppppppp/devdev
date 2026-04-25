# Stage Run Result Authority Execution SSOT

Date: 2026-04-25
Status: closed
Canonical Path: `docs/2026-04-25/stage-run-result-authority-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage-run-result-authority-execution-ssot.md`

Commit State:

- Baseline Commit: `ccc3ac914fe32a2179b96636ea0c6d352e2e2713`
- Baseline Dirty Summary: `dirty: prior Director-authority correction changes plus untracked 2026-04-25 survey/execution docs`
- Resume Commit: `ccc3ac914fe32a2179b96636ea0c6d352e2e2713`
- Resume Drift Summary: `no active temp execution queue; current dirty work is bounded to the previous authority-boundary wave`

Source Survey Docs:

- `docs/2026-04-25/codebase-parallel-maintenance-deep-dive-wave2-synthesis.md`

Evidence Artifacts:

- live code inspection of `main_a.py`
- live code inspection of `modules/core/stage4_orchestrator.py`
- live code inspection of `scripts/run_stage4_direct_supervised.py`
- live code inspection of `scripts/run_stage4_direct_supervised_guarded.py`
- focused tests under `tests/test_one_stop_pipeline.py`, `tests/test_run_stage4_direct_supervised.py`, and `tests/test_run_stage4_direct_supervised_guarded.py`

Side-Effect Coverage: covered

## 1. Intent

Prevent operator and benchmark surfaces from reporting Stage4 completion when the runtime did not actually advance manuscript output to the requested target episode.

This is not a Director-quality verdict issue. It is a runtime truth issue: completion status must be tied to observed artifact/DB progress, not to swallowed exceptions or stale audit tags.

## 2. Baseline Facts

- `main_a.py::_run_one_stop_arc_step()` catches Stage4 exceptions, logs best-effort acceptance, and still returns `status="completed"`.
- The same OneStop path can return completed with `manuscripts_delta=0` even when latest manuscript episode is still below `arc_ep_end`.
- `scripts/run_stage4_direct_supervised.py` treats `runtime_audit_tag == "stage4_complete"` as success even when `after_latest_ep < target_ep`.
- `scripts/run_stage4_direct_supervised_guarded.py` has the same stale-tag fallback when child summary is missing.
- `modules/core/stage4_orchestrator.py` can emit `stage4_complete` after the loop returns, so stale or mismatched audit tags are not sufficient as standalone success proof.

## 3. Scope

Included:

- `main_a.py` OneStop arc-step Stage4 result status
- `scripts/run_stage4_direct_supervised.py` success calculation
- `scripts/run_stage4_direct_supervised_guarded.py` fallback success calculation
- focused regression tests for these surfaces

Excluded:

- broad `StageRunResult` dataclass introduction
- Stage4 internal loop return-type refactor
- live canary execution
- benchmark archive schema changes

## 4. Pass 1. Inventory Summary

Runtime completion seams:

- OneStop Stage4 exception path can still mark the arc complete.
- OneStop Stage4 no-progress path can still mark the arc complete.
- Direct supervised runner can report success from stale `runtime_audit_tag`.
- Guarded runner can fall back to the same stale-tag success calculation when child summary is unavailable.

Existing safety anchors:

- `tests/test_one_stop_pipeline.py` already constructs isolated `SovereignApp` arc-step fixtures.
- `tests/test_run_stage4_direct_supervised.py` covers summary/archive behavior.
- `tests/test_run_stage4_direct_supervised_guarded.py` covers guarded archive status and monitor behavior.

## 5. Pass 2. Semantic Classification

Class A: Artifact truth

- Success requires `after_latest_ep >= target_ep` or `after_latest_ep >= arc_ep_end` for the relevant path.
- `runtime_audit_tag` is supporting evidence, not standalone completion proof.

Class B: Operator status truth

- OneStop should return `stage4_error` after Stage4 exception.
- OneStop should return `stage4_incomplete` when Stage4 exits without reaching the arc target.
- Pre-existing completion before the call remains allowed: if `manuscripts_before >= arc_ep_end`, a zero delta can still be complete.

Class C: Benchmark truth

- Direct supervised summaries should preserve `runtime_audit_tag` for evidence, but `success` should be target-progress based.
- Archive status should be `partial` when the target episode was not reached on clean exit.

## 6. Side-Effect Map

- file writes / artifacts: direct runner summary JSON stays at existing path.
- DB / schema / transaction boundaries: no schema change.
- JSONL / log / audit sinks: no new audit sink; status strings become more truthful.
- console / UI / operator output: OneStop logs incomplete/error instead of false completion.
- rollback / recovery / retry: no rollback; incomplete status prevents downstream arc-count advancement.
- cache / global state: not applicable.
- bootstrap fallback / config-env mutation: not applicable.

## 7. Realization Architecture

1. In OneStop arc step, compute `manuscripts_after` after Stage4 and require it to reach `arc_ep_end`.
2. On Stage4 exception, return `stage4_error` with zero completed arc delta.
3. On no progress to target, return `stage4_incomplete` with zero completed arc delta.
4. In direct supervised runner, calculate success only from `after_latest_ep >= target_ep`.
5. In guarded runner fallback, calculate success only from `after_latest_ep >= target_ep`.

## 8. Execution Tranches

1. `one-stop-stage4-completion-truth`
2. `direct-supervised-stale-tag-false-pass`
3. `focused-regression-validation`

## 9. Acceptance Criteria

- OneStop does not report `completed` after a Stage4 exception.
- OneStop does not increment completed arc count when Stage4 does not reach `arc_ep_end`.
- OneStop may still report `completed` with zero delta if the target manuscript already existed before the call.
- Direct supervised runner reports `success=False` when `after_latest_ep < target_ep`, even if `runtime_audit_tag == "stage4_complete"`.
- Guarded runner fallback reports `success=False` under the same stale-tag condition.

## 10. Verification Plan

- `python -m pytest tests/test_one_stop_pipeline.py tests/test_run_stage4_direct_supervised.py tests/test_run_stage4_direct_supervised_guarded.py -q`
- `python scripts/check_utf8_hygiene.py main_a.py scripts/run_stage4_direct_supervised.py scripts/run_stage4_direct_supervised_guarded.py tests/test_one_stop_pipeline.py tests/test_run_stage4_direct_supervised.py tests/test_run_stage4_direct_supervised_guarded.py docs/2026-04-25/stage-run-result-authority-execution-ssot.md`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails

- Do not change Director PASS/REJECT authority.
- Do not change Stage4 internal quality judgment.
- Do not use `runtime_audit_tag` as standalone success proof.
- Do not penalize already-complete arcs where `manuscripts_before >= arc_ep_end`.
- Keep this as a compact truth-surface patch; defer full `StageRunResult` contracts.

## 12. Temp Queue Notes

- temp status: completed
- cleanup condition: `docs/temp/stage-run-result-authority-execution-ssot.md` removed after realization and validation completed
- roadmap dependency: none

## 13. Document 3-Pass Audit

Pass 1 - Structure and scope:

- Document type is execution SSOT.
- Canonical and temp mirror paths are explicit.
- Scope is bounded to OneStop and direct-supervised success truth.
- Acceptance criteria and verification plan are present.

Pass 2 - Evidence and consistency:

- Claims match inspected live code and focused tests.
- Baseline dirty state is explicit.
- This does not conflict with Director sovereignty because it only governs runtime/artifact completion truth.

Pass 3 - Execution and readability:

- Execution tranches are small.
- Side effects and non-goals are explicit.
- Temp cleanup rule is explicit.

Estimated confidence:

- Execution SSOT confidence: `95%`

## 14. Closure Note

Closure status: `closed`

Realized changes:

- OneStop arc-step Stage4 status now returns `stage4_error` after a Stage4 exception instead of false `completed`.
- OneStop arc-step Stage4 status now returns `stage4_incomplete` when the latest manuscript episode remains below `arc_ep_end`.
- OneStop still allows `completed` with zero delta when the target manuscript was already present before the call.
- Direct supervised Stage4 runner now computes `success` only from `after_latest_ep >= target_ep`.
- Guarded direct supervised fallback now uses the same target-progress success rule when child summary is missing.

Verification evidence:

- `python -m py_compile main_a.py scripts/run_stage4_direct_supervised.py scripts/run_stage4_direct_supervised_guarded.py tests/test_one_stop_pipeline.py tests/test_run_stage4_direct_supervised.py tests/test_run_stage4_direct_supervised_guarded.py` passed.
- `python -m pytest tests/test_one_stop_pipeline.py tests/test_run_stage4_direct_supervised.py tests/test_run_stage4_direct_supervised_guarded.py -q` passed: `16 passed`.
- `python scripts/check_utf8_hygiene.py ...` passed for touched code, tests, and execution SSOT docs.
- `git diff --check` reported no whitespace errors; it only warned that `tests/chaos/test_feedback_loop.py` line endings will normalize from CRLF to LF when Git touches it.
- `python scripts/ops_validator.py --strict` passed before temp cleanup with one active mirror matching canonical.

Complexity evidence:

- `main_a.py::_run_one_stop_arc_step`: `110 LOC`
- `scripts/run_stage4_direct_supervised.py::run_direct_stage4`: `56 LOC`
- `scripts/run_stage4_direct_supervised_guarded.py::run_guarded_stage4`: `157 LOC`
- `run_guarded_stage4` is a pre-existing 120+ LOC process-supervision bounded shell; this wave changed only its fallback success predicate and did not push it into the 180+ high-risk band.

Residual risks:

- Full `StageRunResult` contract normalization remains deferred.
- No live Stage4 run was executed in this closure.
- Broader CI tier expansion remains a separate follow-up item.
