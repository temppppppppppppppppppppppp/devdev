# continuity-history-and-escalation-guardrails Execution SSOT

Date: 2026-03-16
Status: closed
Canonical Path: `docs/2026-03-16/continuity-history-and-escalation-guardrails-execution-ssot.md`
Temp Mirror Path: `docs/temp/continuity-history-and-escalation-guardrails-execution-ssot.md`
Commit State:
- Baseline Commit: `d6c81c1976d9812d447c2a78e2aeb36f7aed666a`
- Baseline Dirty Summary: `dirty: wide workspace code/docs changes already present; OPUS memo re-audit and survivor queue promotion in progress`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `dirty: lane realized in continuity/stage3/stage4 modules plus targeted regression coverage; survivor queue exhausted after closure`
Source Survey Docs:
- `docs/2026-03-16/opus-survivor-intake-authority-reclassification.md`
- `docs/2026-03-15/opus/all-stage-deepdive-fix-candidates-ssot.md`
- `docs/2026-03-15/opus/all-subsystem-tf-consolidated-ssot.md`
- `docs/2026-03-15/opus/escalation-residual-tf-consolidated-ssot.md`
Evidence Artifacts:
- `docs/2026-03-16/opus-survivor-intake-evidence.txt`
Side-Effect Coverage: covered

## 1. Intent
- Close the still-live continuity, history-window, and Stage 4 escalation guardrail gaps surfaced by the OPUS survivor intake.
- Realize only the survivor items still supported by live code: `TF-CM-03`, `S3-1`, `S3-2`, `S4-4`, `S4-5`, `TF-E3`.

## 2. Baseline Facts
- `continuity_manuscript.py` still tracks `사망` and `굴복` keywords but omits them from `STATE_ORDER`.
- Stage 3 still hard-truncates prior manuscript context by char count and hard-caps prior blueprints to `30`.
- Stage 4 continuity/history checks still run only on round `0`.
- Stage 4 patch loop still breaks immediately when feedback is empty.
- escalation event logging still emits only `{ts, ep, event, streak, success}`.

## 3. Scope
Included:
- `modules/domain/agents/continuity_manuscript.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_orchestrator.py`
- targeted tests for continuity state transitions, history-window behavior, patch-loop behavior, and escalation logs

Excluded:
- Stage 4 context-builder raw DB access
- WorldState / FactLedger save failure behavior
- Director grading and feedback quantification

## 4. Pass 1. Inventory Summary
- Survivor count in this lane: `6`
- Main hotspots:
  - continuity state-order omission
  - Stage 3 history-window truncation
  - Stage 4 round-gated continuity checks
  - patch loop early abort
  - escalation telemetry under-reporting

## 5. Pass 2. Semantic Classification
- Class A: continuity state model gaps (`TF-CM-03`)
- Class B: stage-history truncation and bounded context drift (`S3-1`, `S3-2`)
- Class C: Stage 4 guardrail dropouts (`S4-4`, `S4-5`)
- Class D: escalation observability incompleteness (`TF-E3`)

## 6. Side-Effect Map
- file writes / artifacts:
  - escalation JSONL payload and possibly saved stage-history artifacts may change
- DB / schema / transaction boundaries:
  - not primary, but escalation payload may touch structured sinks
- JSONL / log / audit sinks:
  - direct scope via escalation logging
- console / UI / operator output:
  - patch-loop and continuity behavior can change operator-visible retries
- rollback / recovery / retry:
  - direct scope
- cache / global state:
  - continuity state ordering is direct scope
- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture
- Make continuity state transitions explicit for death/surrender terminal states.
- Replace naive history truncation with a bounded but semantically safer policy.
- Extend Stage 4 continuity coverage beyond the initial round without exploding cost.
- Make empty-feedback patch handling explicit rather than silent abort.
- Enrich escalation telemetry enough for later runtime diagnosis.

## 8. Execution Tranches
1. Fix continuity state-order omission and Stage 4 empty-feedback behavior.
2. Rework Stage 3 history-window / blueprint carryover policy into a bounded, testable contract.
3. Expand Stage 4 continuity coverage and escalation log payload with focused regression tests.

## 9. Acceptance Criteria
- continuity state-order logic no longer omits death/surrender terminal semantics
- Stage 3 history carryover is bounded but no longer only a blunt hard-cut
- Stage 4 continuity checks are not limited to round `0` only
- empty-feedback patch paths do not silently break the fix loop
- escalation logs capture enough structured context for later diagnosis

## 10. Verification Plan
- targeted pytest for continuity manuscript checks
- targeted pytest for Stage 3 history-window behavior
- targeted pytest for Stage 4 interview-round patch behavior
- targeted pytest for Stage 4 escalation log payload
- `python -m py_compile` for touched Python files

## 11. Guardrails
- Do not turn this lane into a repo-wide context-compression redesign.
- Do not widen escalation telemetry into unrelated sink redesign.
- Do not reopen OPUS-only memo items that were excluded by the survivor intake.

## 12. Temp Queue Notes
- temp status: cleaned after closure
- cleanup condition: remove the mirror after realization and closure
- roadmap dependency: `docs/2026-03-16/opus-survivor-followup-execution-roadmap.md`

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. Closure Summary
- realization status:
  - `TF-CM-03` landed: `ContinuityManuscriptValidator` now treats `굴복` and `사망` as explicit terminal states inside `STATE_ORDER`
  - `S3-1` and `S3-2` landed: Stage 3 now uses a bounded anchor+recent history policy for blueprint and manuscript carryover instead of a blunt last-30 trim
  - `S4-4` landed: post-select continuity/history checks now run on retry rounds too
  - `S4-5` landed: PASS_WITH_FIX now emits an explicit operator-visible abort when fix feedback is empty instead of silently breaking
  - `TF-E3` landed: escalation JSONL payloads can now record `round_num`, `attempt_key`, `fix_scope`, `reason`, and `contradiction_type`
- verification:
  - `python -m py_compile modules/domain/agents/continuity_manuscript.py modules/core/stage3_orchestrator.py modules/core/stage4_interview_round.py modules/core/stage4_orchestrator.py tests/test_continuity_modules.py tests/test_stage3_orchestrator.py tests/test_stage4_interview_round.py tests/test_stage4_orchestrator.py`
  - `python -m pytest tests/test_stage3_orchestrator.py`
  - `python -m pytest tests/test_continuity_modules.py`
  - `python -m pytest tests/test_stage4_interview_round.py`
  - `python -m pytest tests/test_stage4_orchestrator.py tests/test_v75b_escalation.py`
  - `python scripts/check_utf8_hygiene.py modules/domain/agents/continuity_manuscript.py modules/core/stage3_orchestrator.py modules/core/stage4_interview_round.py modules/core/stage4_orchestrator.py tests/test_continuity_modules.py tests/test_stage3_orchestrator.py tests/test_stage4_interview_round.py tests/test_stage4_orchestrator.py`
- residual risk:
  - no open blocker remains inside this bounded lane
  - the Stage 3 anchor window intentionally remains a bounded compression policy, not a whole-pipeline long-range memory redesign
- next queue item:
  - none; the survivor follow-up queue is exhausted
