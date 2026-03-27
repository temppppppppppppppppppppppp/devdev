# Stage4 God1 Handoff Replacement Wave1 Execution SSOT

Date: 2026-03-27
Status: closed
Canonical Path: `docs/2026-03-27/stage4-god1-handoff-replacement-wave1-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage4-god1-handoff-replacement-wave1-execution-ssot.md`
Commit State:
- Baseline Commit: `eb7a41d86a52b075861bcbd59a402622ab08d6cc`
- Baseline Dirty Summary: `dirty: tracked narrative/router/provider/stage4/test/doc surfaces, logs/artifacts; untracked dated docs, provider adapters/tests, canary projects, narrative artifacts`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `new single-item defer queue opened after higher-priority fact-contract, provider/request-shape, and maturity waves were closed`
Source Survey Docs:
- `docs/2026-03-27/llm-friendliness-gimmick-elegance-defer-priority-freeze.md`
- `docs/2026-03-27/llm-friendliness-gimmick-elegance-opus-deep-dive-audit.md`
- `docs/2026-03-27/opus/rol-llm-gimmick-t3-stage4-authority-verdict.md`
Evidence Artifacts:
- live recheck of `modules/core/stage4_interview_round.py`
- live recheck of `modules/core/stage4_director_runtime.py`
- live recheck of `tests/test_stage4_interview_round.py`
- live recheck of `tests/test_stage4_director_runtime_observability.py`
Side-Effect Coverage: covered

## 1. Intent

- realize the next remaining frozen defer item by replacing the Stage 4 `_god1_*` hidden handoff with an explicit round-local contract
- keep the wave narrowly bounded to the current pre-director validation bridge and its write-back path
- preserve Stage 4 operator-visible behavior while removing the sole documented hidden mutable side-channel in this slice

Why now:
- the higher-priority defer items above this lane are already closed in bounded waves:
  - `state_changes schema formalization`
  - `provider identity / usage normalization`
  - `writer/context request-shape cleanup`
  - protagonist-side wuxia technique / realm contract alignment
- the temp execution queue is currently empty, so one bounded single-item defer wave can be opened cleanly without aggregate-roadmap overhead

## 2. Baseline Facts

- the remaining `_god1_*` contract is concentrated in one producer and one main consumer:
  - producer: `Stage4InterviewRound._run_validation_phase()`
  - consumer: `Stage4DirectorRuntime.run_pre_director_validation()`
- current producer field inventory is 7 round-local owner mutations:
  - `_god1_stage4_spinner`
  - `_god1_round_num`
  - `_god1_arc_pos`
  - `_god1_total_ep_in_arc`
  - `_god1_arc_data`
  - `_god1_prev_manuscript`
  - `_god1_director_memory_context`
- the current consumer reads 6 of those fields through `getattr(owner, "_god1_*", None)` and writes back `owner._god1_director_memory_context`
- one same-file residual read remains in `Stage4InterviewRound._run_advisory_chain()` via `getattr(self, "_god1_round_num", None)`
- test coverage currently seeds `_god1_*` attrs directly in `tests/test_stage4_interview_round.py`, which means the hidden handoff is part of the current test contract and must be updated in the same wave
- current evidence still supports the earlier audit judgment:
  - the lane is narrow
  - the mechanism is inelegant
  - the blast radius is moderate rather than broad

## 3. Scope

Included:
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_director_runtime.py`
- `tests/test_stage4_interview_round.py`
- `tests/test_stage4_director_runtime_observability.py`

Excluded:
- `_EnsembleSelectionState` mutation-chain cleanup
- `_finalize_round_outcome` signature work
- PASS_WITH_FIX policy or retry-lane redesign
- director verdict semantics
- broader Stage 4 owner split or module split
- `_god1_*`-unrelated advisory-chain cleanup

## 4. Pass 1. Inventory Summary

- production-owner surfaces touched: 2 files
- direct `_god1_*` read/write touchpoints found at baseline: 16
  - 9 in `stage4_interview_round.py` (7 producer writes + 1 return read + 1 residual advisory-chain read)
  - 7 in `stage4_director_runtime.py` (6 consumer reads + 1 write-back)
- direct test surfaces coupled to `_god1_*` at baseline: 2 test regions (12 seeds) in `tests/test_stage4_interview_round.py`
- current queue mode after opening this document: single-item defer wave

## 5. Pass 2. Semantic Classification

- Class A. Explicit round-local input contract
  - replace owner-instance mutation with one named payload or equivalent explicit parameter seam for the pre-director validation path
- Class B. Explicit result return
  - stop using owner write-back for `director_memory_context`; return it explicitly from the runtime path
- Class C. Behavior-parity test migration
  - update touched tests so they stop seeding `_god1_*` attrs and instead assert the explicit contract

## 6. Side-Effect Map

- file writes / artifacts:
  - bounded edits to the two Stage 4 runtime files
  - bounded test updates
  - canonical execution doc and temp mirror refresh
- DB / schema / transaction boundaries:
  - not applicable; no schema, persistence owner, or transaction-path redesign
- JSONL / log / audit sinks:
  - existing Stage 4 logs and audit sinks should remain behaviorally equivalent
- console / UI / operator output:
  - spinner detail and Stage 4 progress logs must remain intact
- rollback / recovery / retry:
  - retry policy is out of scope; only the round-local validation handoff is touched
- cache / global state:
  - this wave should reduce hidden owner state by removing `_god1_*` mutation in the touched path
- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

- preferred replacement shape:
  - introduce one explicit round-local validation payload for:
    - spinner
    - round_num
    - arc_pos
    - total_ep_in_arc
    - arc_data
    - prev_manuscript
  - pass that payload explicitly into `Stage4DirectorRuntime.run_pre_director_validation()`
  - return `director_memory_context` explicitly rather than writing it back through `owner._god1_director_memory_context`
- cleanup rule:
  - the touched pre-director validation path should not depend on any `_god1_*` owner attrs after this wave
  - if `Stage4InterviewRound` still needs `round_num` for same-file observability helpers, pass it explicitly or localize it without recreating a hidden `_god1_*` bridge
- queue rule:
  - this is a single active bounded wave, so no temp roadmap is required

## 8. Execution Tranches

1. Tranche A. Explicit pre-director validation payload
   - replace producer-side `_god1_*` owner mutation with an explicit input payload or equivalent explicit argument seam

2. Tranche B. Explicit return path and residual `_god1_*` removal
   - replace `owner._god1_director_memory_context` write-back with an explicit return value
   - remove the remaining same-file `_god1_*` dependency in the touched Stage 4 slice

3. Tranche C. Bounded regression coverage
   - update existing Stage 4 tests to use the new explicit contract
   - add a tiny new test only if the existing files cannot host the coverage cleanly

## 9. Acceptance Criteria

- no `_god1_*` reads or writes remain in the touched pre-director validation bridge between `Stage4InterviewRound` and `Stage4DirectorRuntime`
- `director_memory_context` is no longer returned through owner mutation
- current Stage 4 spinner/progress behavior stays intact
- touched tests no longer seed `_god1_*` attrs directly
- the wave does not widen into retry, verdict, or broader Stage 4 refactor work

## 10. Verification Plan

- `python -m py_compile modules/core/stage4_interview_round.py modules/core/stage4_director_runtime.py`
- `pytest tests/test_stage4_interview_round.py -q`
- `pytest tests/test_stage4_director_runtime_observability.py -q`
- `python scripts/check_utf8_hygiene.py modules/core/stage4_interview_round.py modules/core/stage4_director_runtime.py tests/test_stage4_interview_round.py tests/test_stage4_director_runtime_observability.py docs/2026-03-27/stage4-god1-handoff-replacement-wave1-execution-ssot.md docs/temp/stage4-god1-handoff-replacement-wave1-execution-ssot.md`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails

- do not widen this into a general Stage 4 runtime redesign
- do not change verdict semantics, retry semantics, or Director scoring rules
- do not introduce a second hidden compat shell around the explicit payload
- if `_god1_*` removal requires touching unrelated Stage 4 families, stop and re-scope instead of silently widening the wave

## 12. Temp Queue Notes

- temp status: removed
- cleanup condition: satisfied and executed; temp mirror and queue-state were removed during closure audit
- roadmap dependency: none; this remained a single-item bounded wave

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. 3-Pass Audit Record

Pass 1. Structure and Scope
- kept the wave bounded to the `_god1_*` producer/consumer bridge plus direct test fallout
- kept broader Stage 4 refactor candidates out of scope
- PASS

Pass 2. Evidence and Consistency
- verified that the higher-priority deferred items are already closed, making this the next remaining frozen defer
- verified that `_god1_*` still exists live in the producer, consumer, and one same-file residual read
- verified that current tests still seed the hidden contract directly
- PASS

Pass 3. Execution Readiness
- acceptance criteria are concrete
- touched surface is narrow enough for a single bounded wave
- single-item queue semantics are sufficient; no aggregate roadmap is needed
- PASS

Estimated confidence: 96%

## 15. Realization Record

Realized: 2026-03-27
Final status: `stage4-god1-handoff-replacement-wave1 complete`

### Changes Applied

Tranche A — Explicit pre-director validation payload:
- `stage4_director_runtime.py`: added 6 explicit keyword parameters (`stage4_spinner`, `round_num`, `arc_pos`, `total_ep_in_arc`, `arc_data`, `prev_manuscript`) to `run_pre_director_validation()`; removed 6 `getattr(owner, "_god1_*", ...)` consumer reads and the `_god1_*` comment block
- `stage4_interview_round.py`: removed 7 `self._god1_*` producer writes and the `_god1_*` comment/TODO block from `_run_validation_phase()`; passes all 6 fields as explicit keyword arguments to the runtime call

Tranche B — Explicit return path and residual removal:
- `stage4_director_runtime.py`: changed `run_pre_director_validation()` return type from `list[dict]` to `tuple[list[dict], str]`; returns `(validation_results, director_memory_context)` explicitly; removed `owner._god1_director_memory_context` write-back
- `stage4_interview_round.py`: receives `(validation_results, director_memory_context)` via tuple unpacking; removed `getattr(self, "_god1_director_memory_context", "")` return-path read
- `stage4_interview_round.py`: added `round_num: int | None = None` keyword parameter to `_run_advisory_chain()`; removed `getattr(self, "_god1_round_num", None)` residual read
- `stage4_director_runtime.py`: passes `round_num=round_num` to `owner._run_advisory_chain()` call

Tranche C — Bounded regression coverage:
- `tests/test_stage4_interview_round.py`: migrated 2 test regions (12 `_god1_*` seed lines removed); both tests now pass explicit keyword arguments and unpack the `tuple[list[dict], str]` return

### Residual `_god1_*` Status

- `_god1_*` reads or writes remaining in touched files: **0**
- `_god1_*` reads or writes remaining in any `.py` file in the workspace: **0** (confirmed via workspace-wide grep)

### Verification Results

- `py_compile`: OK (both production files)
- `pytest tests/test_stage4_interview_round.py -q`: 219 passed
- `pytest tests/test_stage4_director_runtime_observability.py -q`: 2 passed
- `check_utf8_hygiene.py`: clean (no output)
- `ops_validator.py --strict`: PASS (errors=0, warnings=0)

## 16. Closure Note

Closure Date: 2026-03-27
Closure Status: closed (closure-audited)

- canonical execution SSOT retained at `docs/2026-03-27/stage4-god1-handoff-replacement-wave1-execution-ssot.md`
- temp execution mirror removed from `docs/temp/`
- `docs/temp/queue-state.json` removed after queue exhaustion
- no active execution SSOT remains in `docs/temp/` after this closure
