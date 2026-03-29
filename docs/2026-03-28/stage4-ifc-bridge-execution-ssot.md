# Stage4 IFC Bridge Execution SSOT

Date: 2026-03-28
Status: execution-ready
Canonical Path: `docs/2026-03-28/stage4-ifc-bridge-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage4-ifc-bridge-execution-ssot.md`
Commit State:
- Baseline Commit: `33acf349ce3e1559c06338ef88f7da7c8d50db0f`
- Baseline Dirty Summary: `dirty: stage4 code/tests, BI metadata docs/json, temp queue state, canary project logs, stage4 survey docs`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none at SSOT creation time`
Source Survey Docs:
- `docs/2026-03-28/stage4-ifc-bridge-full-survey.md`
- `docs/2026-03-28/stage4-target-locked-patch-lane-full-survey.md`
Evidence Artifacts:
- `projects/canary_0328_golden_s4_shadow/logs/episode_production.jsonl`
- `projects/canary_0328_golden_new2_s4/logs/runtime_audit.jsonl`
- `tests/test_stage4_orchestrator.py`
Side-Effect Coverage: covered

## 1. Intent

Realize the smallest safe IFC bridge in Stage 4.

Why now:

- the fake patch lane is already fail-closed
- the next proven gap is narrower than a full escalation redesign
- the system can now consider whether repeated IFC-shaped `QUALITY_ISSUE` retries should count toward existing logic-like escalation

This execution document does not redesign Stage 4 generally.

## 2. Baseline Facts

- `modules/core/stage4_outcome_runtime.py:589-614` counts only:
  - explicit `LOGIC_ERROR`
  - optional `post_select_conflict`
- plain `QUALITY_ISSUE` currently resets `logic_error_streak`
- live canaries showed repeated:
  - `reject_bucket = quality_issue`
  - `error_category = QUALITY_ISSUE`
  - `fix_pack_reason = missing_fix_pack`
  - `score = 50`
  - `plateau_detected = true`
  - IFC wording inside `fix_scope_reasoning`
- the evidence supports a narrow bridge into `logic_error_streak`
- the evidence does not support global `QUALITY_ISSUE` reclassification or direct forced blueprint escalation

## 3. Scope

Included:

- `modules/core/stage4_outcome_runtime.py`
- `tests/test_stage4_orchestrator.py`
- canonical execution SSOT and temp mirror

Excluded:

- `modules/core/stage4_retry_runtime.py`
- `modules/domain/agents/chief_writer.py`
- `config/settings/stage4_policy_digest.json`
- round ceiling changes
- V75-D / V75-B threshold tuning
- sink-schema changes
- provider fallback changes

## 4. Pass 1. Inventory Summary

- one hotspot function:
  - `_should_count_reject_as_logic_like(...)`
- one downstream decision point:
  - `apply_retry_repair_escalation(...)`
- one existing bridge family:
  - `post_select_conflict`
- one new candidate bridge family:
  - repeated IFC-shaped `QUALITY_ISSUE`

Main hotspot lane:

- reject outcome classification before escalation thresholds fire

## 5. Pass 2. Semantic Classification

- Class A: existing stable behavior
  - `LOGIC_ERROR` counts
  - `post_select_conflict` optional bridge counts

- Class B: bounded next correction
  - narrow IFC-shaped `QUALITY_ISSUE` may count toward `logic_error_streak`
  - this affects only streak counting, not durable sink category labels

- Class C: deferred follow-up
  - direct blueprint escalation rules
  - threshold tuning
  - round ceiling review

## 6. Side-Effect Map

- file writes / artifacts:
  - `stage4_outcome_runtime.py`
  - `tests/test_stage4_orchestrator.py`
  - canonical execution SSOT and temp mirror

- DB / schema / transaction boundaries:
  - not applicable

- JSONL / log / audit sinks:
  - no sink schema changes intended
  - sink payloads may still show `QUALITY_ISSUE` while the bounded bridge influences streak counting internally

- console / UI / operator output:
  - no new operator-facing log family required in this wave unless needed for bounded debug clarity

- rollback / recovery / retry:
  - retry escalation eligibility may advance sooner for bounded IFC-shaped failures
  - no rollback substrate changes are planned

- cache / global state:
  - not applicable

- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

- keep Stage 4 retry topology unchanged
- do not mutate `error_category` globally
- do not add a new repair lane
- implement a narrow predicate inside reject analysis
- the bridge must be evidence-shaped and fail-closed

Recommended contract:

- `QUALITY_ISSUE` counts as logic-like only when all of the following are true:
  1. `reject_bucket == "quality_issue"`
  2. IFC signal exists
     - current minimal source: `"[IFC]"` inside `fix_scope_reasoning`
  3. persistence signal exists
     - current minimal source: `plateau_detected == true`

Why this shape:

- all required signals already exist in `previous_attempt`
- no extra sink or function-signature churn is required
- plain quality/style failures remain outside logic-like escalation

## 8. Execution Tranches

1. Tranche 1: bounded predicate extraction
   - add a helper for IFC-shaped `QUALITY_ISSUE` detection inside `stage4_outcome_runtime.py`
   - keep it local to the module

2. Tranche 2: narrow bridge wiring
   - extend `_should_count_reject_as_logic_like(...)`
   - do not alter post-select behavior
   - do not alter threshold selection

3. Tranche 3: regression coverage
   - positive test: IFC-shaped `QUALITY_ISSUE` increments `logic_error_streak`
   - negative test: plain `QUALITY_ISSUE` still resets to `0`
   - existing post-select tests continue to pass unchanged

## 9. Acceptance Criteria

- plain `QUALITY_ISSUE` without bounded IFC signals still does not count as logic-like
- repeated IFC-shaped `QUALITY_ISSUE` can count as logic-like
- `error_category` is not globally rewritten
- existing `post_select_conflict` bridge behavior remains intact
- no threshold change is introduced
- no round ceiling change is introduced

## 10. Verification Plan

- targeted pytest:
  - `tests/test_stage4_orchestrator.py -q -k "logic_like or quality_risk or blueprint_regeneration"`
- targeted new assertions:
  - IFC-shaped `QUALITY_ISSUE` positive bridge
  - plain `QUALITY_ISSUE` negative control
- `python scripts/check_utf8_hygiene.py` on touched code/tests/docs
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

Canary validation remains deferred until after this wave lands.

## 11. Guardrails

- do not globally remap `QUALITY_ISSUE` to `LOGIC_ERROR`
- do not lower the `10` round ceiling
- do not tune V75-D or V75-B thresholds
- do not force blueprint regeneration directly from IFC detection
- do not add new durable sink keys unless a direct correctness issue requires them

## 12. Temp Queue Notes

- temp status: pending
- cleanup condition:
  - remove `docs/temp/stage4-ifc-bridge-execution-ssot.md` after realization and closure
- roadmap dependency:
  - current temp roadmap remains `docs/temp/execution-roadmap.md`

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule:
  - re-run this document's 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. 3-Pass Audit Record

### Pass 1. Structure and Scope

- execution doc type matches the current next step
- included and excluded surfaces are explicit
- the document is narrow enough to avoid escalation redesign creep
- PASS

### Pass 2. Evidence and Consistency

- claims are anchored to inspected code and canary sink evidence
- the document preserves the prior-wave contract fix and does not reopen it
- no unsupported global `QUALITY_ISSUE` claim is made
- PASS

### Pass 3. Execution and Readability

- tranches are implementable
- acceptance criteria are testable
- guardrails keep the wave bounded
- PASS

Estimated confidence: `95%`
