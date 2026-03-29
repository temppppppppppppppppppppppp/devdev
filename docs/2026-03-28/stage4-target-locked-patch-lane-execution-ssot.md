# Stage4 Target-Locked Patch Lane Execution SSOT

Date: 2026-03-28
Status: execution-ready
Canonical Path: `docs/2026-03-28/stage4-target-locked-patch-lane-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage4-target-locked-patch-lane-execution-ssot.md`
Commit State:
- Baseline Commit: `33acf349ce3e1559c06338ef88f7da7c8d50db0f`
- Baseline Dirty Summary: `dirty: stage4 code/tests, BI metadata docs/json, TR json, canary project logs, stage4 survey docs`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none at SSOT creation time`
Source Survey Docs:
- `docs/2026-03-28/stage4-target-locked-patch-lane-full-survey-audit-order.md`
- `docs/2026-03-28/stage4-target-locked-patch-lane-full-survey.md`
Evidence Artifacts:
- `projects/canary_0328_golden_s4_shadow/logs/episode_production.jsonl`
- `projects/canary_0328_golden_s4_shadow/logs/session/llm_io.jsonl`
- `projects/canary_0328_golden_new2_s4/logs/runtime_audit.jsonl`
- `projects/canary_0328_golden_new2_s4/logs/canary_summary.json`
Side-Effect Coverage: covered

## 1. Intent

Realize the smallest safe Stage 4 patch-lane correction proven by the audited survey.

Why now:

- the survey is final and 3-pass audited
- the strongest proven defect is narrow and local
- the current bug is not "too few retries"
- the current bug is "fake patch lane can run without a ready fix_pack contract"

This execution document is intentionally narrower than the survey. It does not attempt Stage 4 redesign.

## 2. Baseline Facts

- `modules/core/stage4_retry_runtime.py:881-889` requires `fix_pack_contract.ready` for Lane 1 `inplace`
- the same router allows Lane 2 `patch_revision` without `fix_pack_contract.ready`
- `modules/domain/agents/chief_writer.py:1907-1955` implements `patch_with_feedback()` as bounded regeneration via `generate_ensemble(...)`
- live canaries repeatedly showed:
  - `fix_pack_reason = "missing_fix_pack"`
  - `error_category = "QUALITY_ISSUE"`
  - `score = 50`
  - `patch_revision` / `patch_with_feedback` loop
- the live canaries are provider-contaminated, so they are not clean policy baselines
- despite that contamination, the routing and contract bug is independently evidenced in final Stage 4 sinks
- `tests/test_stage4_interview_round.py:3204` currently proves that missing fix_pack can still route to patch

## 3. Scope

Included:

- `modules/core/stage4_retry_runtime.py`
- `modules/domain/agents/chief_writer.py`
- `tests/test_stage4_interview_round.py`
- `tests/test_stage4_orchestrator.py` if a direct retry-routing assertion needs adjustment
- bounded docs/temp mirror and queue-validation artifacts related to this SSOT

Excluded:

- `modules/core/stage4_outcome_runtime.py` escalation policy changes
- `modules/core/stage4_policy_digest.py` or `config/settings/stage4_policy_digest.json` threshold tuning
- round ceiling changes (`10` remains unchanged)
- blueprint/V75-D/V75-B redesign
- provider fallback redesign
- broad rename or sink-schema migration for historical Stage 4 artifacts

## 4. Pass 1. Inventory Summary

- one proven router gap:
  - Lane 2 `patch_revision` can activate without `fix_pack_contract.ready`
- one proven semantic mismatch:
  - `patch_with_feedback()` is not true patching
- one existing regression anchor:
  - `test_retry_inplace_requires_fix_pack_and_routes_to_patch`
- one live failure fingerprint repeated across canaries:
  - `quality_issue|fix_pack:missing_fix_pack`

Main hotspot lane:

- Stage 4 retry routing between `inplace`, `patch_revision`, and `rewrite_regenerate`

## 5. Pass 2. Semantic Classification

- Class A: proven contract bug
  - empty or non-ready fix_pack still qualifies for patch-labeled retry

- Class B: bounded implementation correction
  - fail-close Lane 2 when the fix_pack contract is not ready
  - narrow `patch_with_feedback()` usage semantics so it is not treated as a normal patch path without targets

- Class C: deferred follow-up
  - IFC-to-logic-like escalation bridge
  - broader Stage 4 repair-policy redesign
  - retry ceiling review

## 6. Side-Effect Map

- file writes / artifacts:
  - code changes in `stage4_retry_runtime.py` and possibly `chief_writer.py`
  - test updates in `tests/test_stage4_interview_round.py` and possibly `tests/test_stage4_orchestrator.py`
  - canonical execution SSOT and temp mirror

- DB / schema / transaction boundaries:
  - not applicable
  - no schema or transaction changes are in scope

- JSONL / log / audit sinks:
  - existing Stage 4 sink values may show different retry-lane labels or fallback behavior after implementation
  - no new durable sink schema is planned in this wave

- console / UI / operator output:
  - retry-lane logs may change if fake patch entry is blocked
  - any logging change must stay bounded and explain the fail-closed decision

- rollback / recovery / retry:
  - retry behavior will change only at Lane 2 eligibility
  - no new rollback substrate is planned

- cache / global state:
  - not applicable
  - no cache or global-state contract change is intended

- bootstrap fallback / config-env mutation:
  - not applicable
  - no config or env mutation is in scope

## 7. Realization Architecture

- substrate requirement:
  - keep existing Stage 4 retry topology
  - do not invent a new repair lane in this wave

- contract requirement:
  - `patch_revision` must no longer be eligible when `fix_pack_contract.ready != True`
  - if the contract is not ready, the router must fall through to a non-patch path

- semantics requirement:
  - `patch_with_feedback()` may remain implemented as bounded regeneration
  - but it must not be used under a patch contract when no concrete patch contract exists

- compatibility requirement:
  - keep the `10` round ceiling unchanged
  - avoid sink-schema churn
  - keep blast radius inside Stage 4 retry routing and its direct tests

## 8. Execution Tranches

1. Tranche 1: fail-closed Lane 2 eligibility
   - add `fix_pack_contract.ready` gating to the `use_patch` decision
   - preserve Lane 1 and Lane 3 behavior

2. Tranche 2: bounded contract narrowing
   - adjust `patch_with_feedback()` call assumptions or comments/logs so the code no longer implies normal patch semantics when the contract is absent
   - keep this bounded; no broad rename migration in this wave

3. Tranche 3: regression coverage and bounded verification
   - update or replace the current missing-fix-pack routing test
   - add direct assertions that non-ready fix_pack no longer routes into normal `patch_revision`

## 9. Acceptance Criteria

- missing or non-ready fix_pack no longer qualifies for Lane 2 `patch_revision`
- the fake patch lane shown in the audited survey is closed
- existing valid `inplace` flow still requires ready contract and remains intact
- existing rewrite fallback still works
- no round-ceiling change is introduced
- no escalation-threshold change is introduced
- test coverage explicitly locks the corrected Lane 2 behavior

## 10. Verification Plan

- targeted pytest:
  - `tests/test_stage4_interview_round.py`
  - `tests/test_stage4_orchestrator.py` if touched
- targeted contract checks:
  - missing fix_pack -> no normal patch lane
  - ready fix_pack -> patch or inplace still eligible according to current policy
- `python scripts/check_utf8_hygiene.py` on touched code/tests/docs
- `python scripts/ops_validator.py --strict` after temp mirror refresh

Canary validation is explicitly deferred to a later turn.

## 11. Guardrails

- do not lower the Stage 4 round ceiling
- do not tune V75-D or V75-B thresholds in this wave
- do not add IFC reclassification logic in this wave
- do not broaden the change into blueprint-escalation redesign
- do not change provider selection or provider fallback behavior
- do not rename durable sink keys unless required by a direct correctness issue

## 12. Temp Queue Notes

- temp status: pending
- cleanup condition:
  - remove `docs/temp/stage4-target-locked-patch-lane-execution-ssot.md` after realization and closure
- roadmap dependency:
  - current temp roadmap remains `docs/temp/execution-roadmap.md`
  - this item is not auto-promoted by this document alone

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule:
  - re-run this document's 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. 3-Pass Audit Record

### Pass 1. Structure and Scope

- execution doc type matches the requested next step after the audited survey
- included and excluded surfaces are explicit
- the first move is intentionally narrower than the survey's full discussion
- PASS

### Pass 2. Evidence and Consistency

- commit state was captured from live workspace
- source survey and log evidence paths were checked
- the document keeps the provider-contamination caveat and avoids zero-contamination overclaim
- the plan stays anchored to the proven contract gap rather than to speculative blueprint conclusions
- PASS

### Pass 3. Execution and Readability

- tranches are actionable
- acceptance criteria are bounded
- guardrails prevent scope creep into escalation and round-ceiling work
- the next implementer can patch directly from this document after re-audit
- PASS

Estimated confidence: `96%`

