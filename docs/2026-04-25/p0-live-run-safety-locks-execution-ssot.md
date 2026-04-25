# P0 Live Run Safety Locks Execution SSOT

Date: 2026-04-25
Status: closed
Canonical Path: `docs/2026-04-25/p0-live-run-safety-locks-execution-ssot.md`
Temp Mirror Path: `docs/temp/p0-live-run-safety-locks-execution-ssot.md`
Commit State:
- Baseline Commit: `f1bb2b11141fbaaa1e62cdb35f48a70041b1e3e1`
- Baseline Dirty Summary: `clean`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- inline P0/P1 parallel survey on 2026-04-25
Evidence Artifacts:
- live code evidence from `modules/core/stage4_orchestrator.py`
- live code evidence from `scripts/canary_path_utils.py`
- live code evidence from `modules/core/stage4_canary_tools.py`
- live code evidence from `scripts/archive_benchmark_record.py`
Side-Effect Coverage: covered

## 1. Intent

Before any fresh live run, close the three P0 safety holes that can either bypass Director authority or destroy live/evidence artifacts.

This document authorizes a bounded implementation wave only for:
- blocking Stage 4 rejected `last_best` manuscript adoption
- preventing canary preparation from deleting arbitrary absolute or live project paths
- making benchmark archive overwrite evidence-preserving and atomic

## 2. Baseline Facts

- Stage 4 accepted verdicts are `PASS` and `PASS_WITH_FIX`, but exhaustion handling can still adopt `previous_attempt.best_manuscript` when the operator selects option `1`.
- Canary path resolution currently returns absolute `project_name` inputs unchanged, while canary prep deletes an existing target with `shutil.rmtree()` when `force=True`.
- Benchmark archive overwrite currently deletes the existing record directory before the new bundle has been successfully staged.
- The current branch baseline is clean and already includes runtime freshness metadata from `f1bb2b11`.

## 3. Scope

Included:
- `config/settings/stage4_policy_digest.json`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_canary_tools.py`
- `scripts/canary_path_utils.py`
- `scripts/archive_benchmark_record.py`
- directly related tests

Excluded:
- ProcessRunner stderr draining and stop-state semantics
- broader Director post-gate policy rearchitecture
- legacy destructive root scripts not used by fresh live run
- full fresh live run execution

## 4. Pass 1. Inventory Summary

- Stage 4 adoption path: `_allow_stage4_best_manuscript_adoption()` and `_finalize_round_outcome_loop()`.
- Canary deletion path: `resolve_workspace_project_dir()` permits absolute paths; `prepare_stage34_canary_project()` deletes existing target when `force=True`.
- Archive overwrite path: `archive_benchmark_record()` removes `record_root` before the new archive is fully built.

## 5. Pass 2. Semantic Classification

- Class A, authority lock: Stage 4 must not convert a non-accepted Director outcome into a persisted episode artifact through operator fallback.
- Class B, destructive path containment: canary helpers may delete only within the canary root and never a live project or arbitrary absolute path.
- Class C, evidence preservation: benchmark overwrite must stage a complete replacement first, then atomically replace or preserve the old record on failure.

## 6. Side-Effect Map

- file writes / artifacts: canary target copies; benchmark archive bundles; Stage 4 policy JSON.
- DB / schema / transaction boundaries: canary reset may mutate copied project DB only after containment; archive copies DB files but does not mutate source DB.
- JSONL / log / audit sinks: benchmark archive copies logs; Stage 4 policy changes affect retry/exhaustion behavior and shadow logging.
- console / UI / operator output: Stage 4 exhaustion must report human review instead of offering rejected-manuscript proceed.
- rollback / recovery / retry: archive overwrite must preserve previous record if staging fails.
- cache / global state: not materially changed.
- bootstrap fallback / config-env mutation: Stage 4 policy default changes from allowing best adoption to disallowing it.

## 7. Realization Architecture

- Stage 4: make best-manuscript adoption fail closed. The old operator option is removed from the runtime path; rejection exhaustion returns human review.
- Canary: reject absolute project names at resolver boundary and add a target containment guard before any `rmtree`.
- Archive: build overwrite bundles in a sibling temporary staging directory, then replace the old record only after successful staging.

## 8. Execution Tranches

1. Disable Stage 4 rejected `last_best` adoption and update tests.
2. Add canary target containment and absolute-path rejection tests.
3. Make benchmark overwrite atomic and add failure-preserves-existing-record coverage.

## 9. Acceptance Criteria

- Stage 4 exhaustion with `best_manuscript` no longer returns a final manuscript without a Director accepted verdict.
- Canary prepare/full cannot delete a live project or arbitrary absolute path, even with `--force`.
- Benchmark archive overwrite preserves the previous record if new archive creation fails before replacement.
- No touched production function newly enters the 120+/180+ complexity guard band.

## 10. Verification Plan

- `python -m pytest tests/test_stage4_orchestrator.py -q -k "finalize_round_outcome_loop"`
- `python -m pytest tests/test_canary_path_utils.py tests/test_canary_prep_isolation.py tests/test_run_stage34_canary.py -q`
- `python -m pytest tests/test_archive_benchmark_record.py -q`
- `python -m ruff check <touched files>`
- `python scripts/check_utf8_hygiene.py <touched files>`
- `git diff --check`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails

- Do not add a new path where Python decides narrative pass/reject.
- Do not run a fresh live run inside this execution wave.
- Do not use destructive shell commands for path cleanup.
- Do not widen archive overwrite to unrelated benchmark schema changes.

## 12. Temp Queue Notes

- temp status: pending
- cleanup condition: remove the temp mirror after realization is committed, validated, and the canonical SSOT is marked closed
- roadmap dependency: none; this is the only active execution item

## 13. Document 3-Pass Audit

- Pass 1, structure and scope: PASS. The document is an execution SSOT, scope is explicit, included/excluded surfaces are bounded, and acceptance criteria are present.
- Pass 2, evidence and consistency: PASS. Claims are tied to inspected live code paths and the baseline commit is recorded.
- Pass 3, execution and readability: PASS. Tranches are actionable, side effects are mapped, and verification commands are concrete.
- Confidence: 96%. The three P0 targets are independently confirmed by live code evidence; P1/P2 items are intentionally excluded to avoid scope creep.

## 14. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- execution-start rule: this document was audited against `f1bb2b11141fbaaa1e62cdb35f48a70041b1e3e1` and is current for this branch.

## 15. Closure Evidence

Closure Status: closed
Implementation Branch: `codex/p0-live-run-safety`
Implementation Commit: pending local commit / PR branch publication

Verified behavior:
- Stage 4 rejected `last_best` adoption now fails closed into human review; no Director-unapproved manuscript is converted into a final manuscript.
- Canary project resolution rejects absolute project path inputs, and canary prep validates the target boundary before any `rmtree` path.
- Benchmark archive overwrite builds a staged replacement and preserves the existing record plus index row when staging fails.

Validation commands:
- `python -m pytest tests/test_archive_benchmark_record.py -q` -> PASS, 3 passed.
- `python -m pytest tests/test_canary_path_utils.py tests/test_canary_prep_isolation.py tests/test_stage2_canary_tools.py tests/test_stage4_canary_tools.py tests/test_run_stage3_canary.py -q` -> PASS, 42 passed.
- `python -m pytest tests/test_stage4_orchestrator.py -q -k "finalize_round_outcome_loop"` -> PASS, 4 passed, 160 deselected.
- `python -m pytest tests/test_run_stage2_canary.py tests/test_run_stage4_canary.py tests/test_run_stage34_canary.py tests/test_run_stage34_ep_demo_canary.py -q` -> PASS, 23 passed.
- `python -m ruff check modules/core/stage4_policy_digest.py modules/core/stage4_orchestrator.py modules/core/stage4_canary_tools.py scripts/canary_path_utils.py scripts/archive_benchmark_record.py tests/test_stage4_orchestrator.py tests/test_canary_path_utils.py tests/test_canary_prep_isolation.py tests/test_stage2_canary_tools.py tests/test_stage4_canary_tools.py tests/test_run_stage3_canary.py tests/test_archive_benchmark_record.py` -> PASS.
- `python scripts/check_utf8_hygiene.py modules/core/stage4_policy_digest.py modules/core/stage4_orchestrator.py modules/core/stage4_canary_tools.py scripts/canary_path_utils.py scripts/archive_benchmark_record.py tests/test_stage4_orchestrator.py tests/test_canary_path_utils.py tests/test_canary_prep_isolation.py tests/test_stage2_canary_tools.py tests/test_stage4_canary_tools.py tests/test_run_stage3_canary.py tests/test_archive_benchmark_record.py docs/2026-04-25/p0-live-run-safety-locks-execution-ssot.md docs/temp/p0-live-run-safety-locks-execution-ssot.md` -> PASS.
- `git diff --check` -> PASS.
- `python scripts/ops_validator.py --strict` -> PASS before temp cleanup; canonical and temp mirror matched.
- `python scripts/ops_validator.py --strict` -> PASS after temp cleanup; no active execution SSOT mirrors remain.

Complexity recount:
- `scripts/archive_benchmark_record.py::archive_benchmark_record` = 103 LOC.
- `modules/core/stage4_orchestrator.py::_finalize_round_outcome_loop` = 79 LOC.
- `scripts/canary_path_utils.py::resolve_workspace_project_dir` = 41 LOC.
- `modules/core/stage4_canary_tools.py::_validate_canary_target_boundary` = 23 LOC.
- No touched production function newly entered the 120+/180+ guard band.

Residual risks and deferred scope:
- No fresh live run was executed in this closure wave; the next live run should consume these locks.
- ProcessRunner stderr drain/stop semantics, legacy destructive root scripts, and broader Director post-gate policy cleanup remain outside this P0 closure.
- The Stage 4 policy key remains present for compatibility, but runtime adoption is hard-disabled to preserve Director authority.
