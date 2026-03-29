# Stage4 Feedback Windowing Execution SSOT

Date: 2026-03-29
Status: execution-ready
Canonical Path: `docs/2026-03-28/stage4-feedback-windowing-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage4-feedback-windowing-execution-ssot.md`
Commit State:
- Baseline Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`
- Baseline Dirty Summary: `dirty: 8 tracked, 26 untracked; hotspots: narrative docs, canary projects, temp queue`
- Resume Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`
- Resume Drift Summary: `same commit; execution-start re-audit completed on 2026-03-29 with only unrelated narrative docs, canary projects, and temp queue drift present`
Source Survey Docs:
- `docs/2026-03-28/stage4-feedback-windowing-full-survey-audit-order.md`
- `docs/2026-03-28/stage4-feedback-windowing-full-survey.md`
- `docs/2026-03-28/stage4-decision-contract-matrix-full-survey.md`
Evidence Artifacts:
- `projects/canary_0328_stage4_ifc_bridge_check/logs/episode_production.jsonl`
- `projects/canary_0328_fixpack_contract_check_v2/logs/episode_production.jsonl`
- `projects/canary_0328_gemini_direct_fixscope_check/logs/episode_production.jsonl`
- `projects/canary_0328_sink_verify_micro/logs/episode_production.jsonl`
Side-Effect Coverage: covered

## 1. Intent

Realize the smallest safe next correction after the closed `fix_scope` seam wave.

The next confirmed structural amplifier is:

> runtime-derived historical advisories accumulate into `retry_directives`, then re-enter the Chief Writer prompt as stale negative context across rounds.

This wave is not a broad Stage 4 redesign.
This wave is about bounded windowing of derived retry feedback while preserving:

- Director sovereignty
- authoritative Director rationale
- current round signal
- non-advisory structural directives such as IFC / conflict-first / Lane3 Gate

## 2. Baseline Facts

- failing canaries show `retry_directives` linear growth of roughly `350-500 chars / failed round`
- in `canary_0328_stage4_ifc_bridge_check`, total feedback payload grows `3.61x` by round 5
- the primary vector is:
  - current-round `runtime_advisory`
  - carried into next-round `prev_general_lines`
  - rewritten as `retry_directives`
- `TF-29` currently stacks on every round where `bucket_streak >= 3`
- plateau advisory already has a one-time guard
- the Director main prompt does not receive historical `retry_directives`
- the Chief Writer prompt does receive the merged `director_feedback`

## 3. Scope

Included:

- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_outcome_runtime.py`
- `tests/test_stage4_interview_round.py`
- `tests/test_stage4_orchestrator.py`
- canonical execution SSOT and temp mirror maintenance

Excluded:

- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_director_runtime.py`
- `modules/domain/agents/chief_writer.py`
- Director prompt contract changes
- provider / fallback / model-default changes
- broad feedback assembly redesign
- operator sink-only compaction
- canary runner changes

## 4. Pass 1. Inventory Summary

- one confirmed growth vector:
  - historical derived advisory text inside `retry_directives`
- one confirmed repeated-stacking vector:
  - `TF-29`
- one already-bounded signal:
  - plateau advisory has a one-time guard
- one protected surface:
  - authoritative Director rationale should remain verbatim

Main hotspot lane:

- `_build_retry_feedback_provenance` in `stage4_interview_round.py`
- `_apply_reject_bucket_advisory` / surrounding TF-29 emit path in `stage4_outcome_runtime.py`

## 5. Pass 2. Semantic Classification

- Class A: preserve as-is
  - authoritative Director `action_items`, `feedback.issues`, `open_review`, `fix_scope_reasoning`
  - non-advisory structural directives
  - plateau one-time behavior

- Class B: bounded reduction target
  - historical advisory entries that refer to prior-round candidates no longer in scope
  - repeated `TF-29` copies after the first emission

- Class C: deferred follow-up
  - category-level advisory deduplication
  - broader authoritative-vs-derived feedback split tightening
  - sink-only compaction

## 6. Side-Effect Map

- file writes / artifacts:
  - `modules/core/stage4_interview_round.py`
  - `modules/core/stage4_outcome_runtime.py`
  - targeted tests
  - canonical execution SSOT and temp mirror

- DB / schema / transaction boundaries:
  - no DB schema change intended

- JSONL / log / audit sinks:
  - `retry_directives` length/content in JSONL sinks will shrink
  - `TF-29` repetition count in operator evidence will reduce

- console / UI / operator output:
  - repeated `TF-29` console notices should stop after first emission
  - current round advisory visibility remains

- rollback / recovery / retry:
  - retry lane choice must remain unchanged
  - no ceiling, escalation threshold, or lane contract change in this wave

- cache / global state:
  - one new episode-local emitted flag is allowed if needed for TF-29 one-time behavior

- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

### 7.1 Retry-Directives Windowing Contract

The intended behavior is:

- keep authoritative Director text verbatim
- keep current-round derived advisory text verbatim
- keep non-advisory structural directives across rounds
- drop stale advisory entries older than the latest failed round when building `retry_directives`

Implementation shape:

- tag or otherwise identify advisory-derived lines at the moment they enter the carry-forward path
- on the next round, keep only the latest round's advisory-derived entries
- preserve non-advisory lines regardless of age

This wave must not rely on Python deciding which quality finding matters.
It may only distinguish:

- derived advisory formatting artifacts
- non-advisory directive lines already treated as structural instructions

### 7.2 TF-29 One-Time Guard Contract

The intended behavior is:

- first `TF-29` emission remains unchanged
- later rounds do not prepend the same `TF-29` notice again in the same episode

The guard should mirror plateau-advisory semantics:

- episode-local
- explicit
- observable in tests

### 7.3 No-Broaden Rule

This wave must not:

- compact authoritative Director rationale
- change Director prompts
- redesign `feedback_provenance`
- change retry lane selection
- change escalation thresholds

## 8. Execution Tranches

1. Tranche 1: latest-round-only derived advisory windowing
   - implement bounded filtering in `_build_retry_feedback_provenance`
   - preserve non-advisory directive lines
   - preserve current-round advisory text

2. Tranche 2: TF-29 one-time guard
   - add an episode-local emitted flag alongside existing plateau semantics
   - stop repeated TF-29 prepend after first emission

3. Tranche 3: regression coverage
   - prove stale advisory entries no longer accumulate past one prior failed round
   - prove non-advisory directives still persist
   - prove TF-29 emits once, not N times

## 9. Acceptance Criteria

- `retry_directives` no longer grows by carrying advisory-derived entries from multiple older rounds
- latest-round advisory context still reaches the Chief Writer prompt
- non-advisory directive lines still persist across rounds
- `TF-29` emits once per episode
- plateau advisory behavior remains unchanged
- no change to retry lane choice, escalation threshold, or Director authority

## 10. Verification Plan

- targeted pytest for:
  - retry feedback provenance windowing
  - preservation of non-advisory lines
  - TF-29 one-time guard behavior
- `python scripts/check_utf8_hygiene.py` on touched code/tests/docs
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

Fresh Gemini direct-only canary should happen only after this wave lands.

## 11. Guardrails

- do not let Python summarize or rewrite authoritative Director rationale
- do not suppress current-round advisory signal
- do not bundle category-dedup, sink-only compaction, or broader feedback split into this wave
- do not touch provider/default-model policy
- do not start from this document without a fresh 3-pass re-audit against the live workspace

## 12. Temp Queue Notes

- temp status: pending
- cleanup condition:
  - remove `docs/temp/stage4-feedback-windowing-execution-ssot.md` after realization and closure
- roadmap dependency:
  - refresh `docs/temp/execution-roadmap.md` before realization because the active temp queue predates this item

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- queue sync command: `python scripts/sync_temp_queue_state.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- execution-start rule:
  - re-run this document's 3-pass audit and confirm at least `95%` confidence against the current workspace state before patching from it

## 14. 3-Pass Audit Record

### Pass 1. Structure and Scope

- implementation stayed bounded to the two confirmed vectors
- non-windowing redesigns stayed excluded
- PASS

### Pass 2. Evidence and Consistency

- implementation target matches the survey's two highest-confidence remediations
- operator-sink side effects are called out explicitly
- roadmap dependency is disclosed rather than silently ignored
- PASS

### Pass 3. Actionability and Overclaim Control

- execution tranches are patchable without reopening the full survey
- guardrails preserve Director sovereignty and current-round signal
- no hidden expansion into escalation or provider redesign
- PASS

Estimated confidence: `96%`
