# 0_0 Stage4 Interview-Round Owner-Surface Reduction Remediation Execution SSOT

Date: 2026-04-07
Status: pending (promoted from parked on 2026-04-07 roadmap reorder; structure-first lane kept below functional pending work)
Canonical Path: `docs/2026-04-07/0_0-stage4-interview-round-owner-surface-reduction-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage4-interview-round-owner-surface-reduction-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
- Baseline Dirty Summary: `dirty: tracked narrative TR/BI artifacts modified; 2026-04-07 in-flight meta cleanup docs untracked`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-04-07/0_0-stage4-interview-round-owner-surface-reduction-bounded-survey.md`
Evidence Artifacts:
- `none; direct code/AST evidence is embedded in the source survey`
Side-Effect Coverage: covered

## 1. Intent

Promote a structure-only pending lane that reduces `Stage4InterviewRound` owner pressure through module-boundary extraction after the current functional queue clears enough to justify it.

This lane is not a hidden runtime blocker.
It exists so the workspace can keep a real owner-surface debt item explicit in the formal queue instead of rediscovering it later during unrelated Stage4 changes.

## 2. Baseline Facts

- `Stage4InterviewRound` currently owns `158` direct methods.
- It still contains `3` `180+ LOC` methods and `6` `120+ LOC` methods.
- Existing extracted siblings already exist:
  - `Stage4DirectorRuntime`
  - `Stage4RejectRuntime`
  - `Stage4RetryRuntime`
- The remaining heavy families still concentrated in the owner are:
  - post-select downgrade / continuity / reuse handling
  - director gate normalization / pass-with-fix shaping
  - episode-log / attempt / sink payload assembly
- This is therefore best treated as a `module boundary / owner-surface reduction` lane, not as incremental helper growth inside the same file.

## 3. Scope

Included:

- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_director_runtime.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_retry_runtime.py`
- any new Stage4 boundary module created specifically to reduce `Stage4InterviewRound` owner pressure
- targeted Stage4 contract/regression tests for the extracted families

Excluded:

- current front functional Stage4 consumer fixes
- repair-contract behavior changes
- non-wuxia Stage4 continuity normalization
- Stage2 / Stage3 upstream refactors
- DB schema redesign
- broad prompt redesign

## 4. Pass 1. Inventory Summary

Primary owner inventory:

1. owner shell
   - `stage4_interview_round.py`
2. existing extracted runtime siblings
   - `stage4_director_runtime.py`
   - `stage4_reject_runtime.py`
   - `stage4_retry_runtime.py`
3. high-risk regression surfaces
   - `tests/test_stage4_interview_round.py`
   - `tests/test_stage4_lane2_binding_contract.py`
   - `tests/test_stage4_advisory_escalation_seam.py`

Primary debt inventory:

1. post-select handling is still a large direct owner responsibility
2. gate semantics normalization still mixes contract logic, fallback rules, and mutation wiring in one owner method
3. episode-log / sink payload assembly still sits as a long owner-local serialization family
4. the existing runtime helper extraction pattern is underused relative to current owner pressure

## 5. Pass 2. Semantic Classification

### Class A. Primary future extraction families

- `_run_post_select_checks`
- `_normalize_director_gate_semantics`
- `_append_episode_log`

### Class B. Secondary extraction / cleanup support

- `_backfill_strong_advisory_fix_pack`
- `_build_retry_feedback_provenance`
- adjacent payload builders and trace helpers that naturally move with the extracted family

### Class C. Explicitly deferred outside this lane

- live behavior changes
- sink contract reinterpretation
- Stage4 queue reprioritization above active functional items
- same-file helper multiplication as a substitute for boundary extraction

## 6. Realization Architecture

This lane should be realized as owner-surface reduction, not cosmetic cleanup.

Preferred direction:

- keep `Stage4InterviewRound` as the coordinator shell
- move one family at a time behind explicit boundary owners
- freeze behavior with targeted tests before each extraction tranche
- recount direct-method and long-function pressure after the extraction wave

Implementation rule:

- prefer new module boundaries over adding more same-file helpers to an owner already above the pressure line

## 7. Execution Tranches

1. contract freeze and owner map
   - identify the exact behavior contract and sink ownership for the target family
   - freeze it with targeted tests before movement

2. post-select boundary extraction
   - move the final-round downgrade / reuse decision family out of the owner shell

3. gate-semantics boundary extraction
   - move pass-with-fix / authoritative-scope normalization into a dedicated boundary owner

4. attempt-log boundary extraction
   - move episode-log / attempt payload assembly out of the owner shell

5. recount and closure
   - rerun targeted regressions
   - recount direct-method pressure and `120+ / 180+` hotspot deltas

## 8. Acceptance Criteria

- no new `180+ LOC` function is introduced
- at least one current `180+ LOC` hotspot is reduced below `180 LOC` or moved out of `Stage4InterviewRound`
- `Stage4InterviewRound` direct-method pressure is reduced from the current `158` baseline
- extracted families have explicit owner boundaries rather than same-file helper sprawl
- targeted Stage4 regressions pass without semantic drift
- post-change complexity recount is recorded

## 9. Verification Plan

- targeted Stage4 regression shards for the extracted family
- `pytest` on touched Stage4 contract files only, sequentially
- `python -m py_compile` on touched production modules
- `ruff check` on touched production/test files
- UTF-8 hygiene on touched docs/code
- post-change AST recount for:
  - direct method count
  - `120+ LOC` functions
  - `180+ LOC` functions

## 10. Guardrails

- do not activate this lane ahead of the active functional Stage4 pair
- do not activate this lane ahead of the currently pending functional Stage3/Stage0 waves without explicit reprioritization
- do not use same-file helper growth as the main realization strategy
- do not silently change verdict, retry, or sink semantics under the name of refactor
- keep behavior-preservation tests ahead of extraction work

## 11. Temp Queue Notes

- temp status: `pending`
- cleanup condition:
  - keep the mirror while this remains a recognized pending structure lane
  - remove only on explicit closure, deactivation, or replacement
- roadmap dependency:
  - below the active Stage4 consumer / repair / non-wuxia lanes
  - below the broader pending functional waves
  - above soak-only reference lanes

## 12. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule:
  - re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before any code refactor begins from this document

## 13. 3-Pass Audit Record

Pass 1, structure and scope:

- execution SSOT type is correct for a pending structure-only queue lane
- scope is bounded to one owner family and its immediate extracted siblings

Pass 2, evidence and consistency:

- queue absence was rechecked against the current roadmap before promotion
- source survey, hotspot counts, and boundary rationale are aligned

Pass 3, execution and readability:

- tranches are boundary-first and actionable
- guardrails keep the lane from jumping ahead of current functional work
- acceptance criteria stay measurable without overpromising a full Stage4 redesign

Confidence: `96%`
