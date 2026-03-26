# Stage3 ThreePhase PWF Early-Exit Wave 1 Execution SSOT

Date: 2026-03-26
Status: closed (closure-audited)
Canonical Path: `docs/2026-03-26/stage3-threephase-pwf-early-exit-wave1-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage3-threephase-pwf-early-exit-wave1-execution-ssot.md`
Commit State:
- Baseline Commit: `e3f2771699cb5d596aefaf994a8a177bbbad0a3e`
- Baseline Dirty Summary: `dirty: docs/2026-03-24/console.txt, docs/implementation/system-order-init-harness.md, docs/temp/queue-state.json, observability/stage4-related production+test files modified; docs/2026-03-25 and docs/2026-03-26 contain multiple untracked docs/projects; no active temp execution queue at open time`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-26/stage3-latency-telemetry-canary-report.md`
- `compact survey synthesis from 2026-03-26 session: ThreePhase internal retry amplification / PWF loop analysis`
Evidence Artifacts:
- `projects/canary_0326_stage3_telemetry/logs/stage3_canary_summary.json`
- `projects/canary_0326_stage3_telemetry/logs/session/llm_io.jsonl`
- `modules/domain/agents/three_phase_blueprint_runtime.py`
- `tests/test_pass_with_fix.py`
Side-Effect Coverage: covered

## 1. Intent

- Realize one bounded Stage 3 optimization wave that cuts waste inside the ThreePhase PASS_WITH_FIX loop without changing the broader Stage 3 architecture.
- Target the specific internal amplification seam confirmed by the instrumented canary and follow-up compact survey:
  - outwardly `1 attempt PASS`
  - inwardly repeated `PASS_WITH_FIX -> inplace patch -> re-audit -> PASS_WITH_FIX`
  - up to 3 fix rounds per retry before escalating
- Apply a fail-fast rule only when re-audit scores stall or regress, so the runtime stops spending LLM calls on non-improving inplace patches.

## 2. Baseline Facts

- `stage3-latency-telemetry-canary-report.md` established that Stage 3 telemetry is now sufficient and that the dominant latency/cost source is `ThreePhase-internal-retry-amplification`, not the outer retry budget.
- The compact survey narrowed the multiplier to a 3-layer cascade:
  - outer retry loop
  - per-retry ensemble/validate cycle
  - `PASS_WITH_FIX` fix loop
- The highest multiplicative waste sits in `_run_pass_with_fix_loop()`:
  - `max_fix = 3`
  - each fix round can spend:
    - 1 LLM call for `_inplace_patch_blueprint()`
    - 1 LLM call for `validator.validate(...)`
  - worst-case `6` LLM calls per PWF entry before escalation
- The compact survey's central finding was not “PWF exists,” but:
  - `score-stalled PWF continues spending all remaining fix rounds`
  - that makes PWF the cheapest bounded place to add a fail-fast cut

## 3. Scope

Included:
- `modules/domain/agents/three_phase_blueprint_runtime.py`
- targeted Stage 3 PASS_WITH_FIX tests
  - default target: `tests/test_pass_with_fix.py`
  - optional tiny dedicated test file only if keeping `tests/test_pass_with_fix.py` bounded becomes impractical

Excluded:
- outer `max_retries` policy
- ensemble strategy count / ensemble generation flow
- Director compare / audit prompt or rubric changes
- validator schema or verdict contract changes
- cache/context reuse waves
- Stage 4 code/prompts/runtime
- DB schema
- JSONL path/naming
- observability sink redesign
- broad PWF redesign beyond this early-exit guard

## 4. Pass 1. Inventory Summary

- Main owner surface:
  - `ThreePhaseBlueprintRuntime._run_pass_with_fix_loop()` (`three_phase_blueprint_runtime.py` L908+)
- Iteration worker:
  - `_run_pass_with_fix_iteration()` (`three_phase_blueprint_runtime.py` L981+)
- Existing relevant behavior:
  - `max_fix = 3` (`L932`)
  - loop body `for fix_index in range(max_fix)` (`L936`)
  - re-audit logging uses `re_validation.get("score", 0)` (`L1092-L1095`)
  - low-score PASS already has a quality-gate stop for re-audit PASS (`L1103-L1125`)
  - repeated unresolved PWF currently runs to exhaustion and then escalates (`L1156-L1198`)
- Existing test surface:
  - `tests/test_pass_with_fix.py` already contains Stage 3 PASS_WITH_FIX and repeated re-audit semantics
  - this is the preferred verification substrate because it already encodes the family contract

## 5. Pass 2. Semantic Classification

- Class A. `bounded fail-fast guard`
  - stop further PWF fix rounds when the latest re-audit score is not better than the prior score
- Class B. `contract preservation`
  - preserve existing behavior for:
    - outright PASS
    - PASS below quality gate
    - patch failure
    - `fix_scope in ("partial", "full")`
    - final escalation to outer retry
- Class C. `narrow observability continuity`
  - keep existing operator logging shape, with at most one new explicit early-exit warning line
- Class D. `explicit defers`
  - do not redesign PWF scoring, fix_scope routing, or outer retry policy in this wave

## 6. Side-Effect Map

- file writes / artifacts:
  - none expected beyond normal code/test file edits
- DB / schema / transaction boundaries:
  - none
- JSONL / log / audit sinks:
  - no sink topology change
  - possible additional operator log message for early-exit reason
- console / UI / operator output:
  - Stage 3 runtime may emit one extra warning/info line when score-stall early-exit fires
- rollback / recovery / retry:
  - yes, but bounded to the Stage 3 PWF loop only
  - outer retry remains authoritative after the early break
- cache / global state:
  - none
- bootstrap fallback / config-env mutation:
  - none

## 7. Realization Architecture

The intended change is a **local fail-fast rule**, not a redesign.

Recommended shape:

1. In `_run_pass_with_fix_loop()`, track `prior_score`, initialized from the incoming Stage 3 validation score.
2. After each successful re-audit that still returns `PASS_WITH_FIX`:
   - parse the new score
   - if the new score is `<= prior_score`, stop spending more fix rounds
   - break out and escalate to the existing outer retry path
3. If the new score improves:
   - update `prior_score`
   - allow one more fix round under existing semantics
4. If the score is absent or unparsable:
   - preserve legacy behavior
   - do not trigger the early-exit guard from missing telemetry alone

This keeps the wave bounded and avoids accidental behavior changes when score data is malformed or absent.

## 8. Execution Tranches

1. Tranche A — runtime guard insertion
   - add `prior_score` tracking in `_run_pass_with_fix_loop()`
   - add score-stall early-exit after re-audit returns `PASS_WITH_FIX`
   - preserve the existing `PASS_WITH_WARNING` success path

2. Tranche B — operator-visible reason logging
   - emit one bounded runtime/operator log line when early-exit fires
   - include prior score and current score if available
   - do not add new sink families

3. Tranche C — regression tests
   - add/update tests proving:
     - score-improving PWF may continue
     - score-stalled PWF breaks early instead of exhausting all 3 fix rounds
     - score-regressing PWF breaks early
     - missing/unparsable score preserves legacy behavior
     - partial/full fix_scope break semantics remain unchanged

## 9. Acceptance Criteria

- `_run_pass_with_fix_loop()` no longer spends all remaining fix rounds when re-audit returns `PASS_WITH_FIX` with a non-improving score
- improved-score PWF still allows continued fix attempts under the existing bounded loop
- `PASS_WITH_WARNING` remains a success path
- `fix_scope in ("partial", "full")` behavior remains unchanged
- outer retry escalation remains unchanged after early-exit
- no Stage 4 surface is opened
- no retry-budget or ensemble-count change is introduced

## 10. Verification Plan

- `python -m py_compile modules/domain/agents/three_phase_blueprint_runtime.py`
- targeted pytest, memory-conservative:
  - `set PYTHONIOENCODING=utf-8 && pytest tests/test_pass_with_fix.py -q -k "Stage3PassWithFix or PF-3 or PASS_WITH_FIX"`
- run any tiny additional dedicated test file only if introduced
- `python scripts/check_utf8_hygiene.py modules/domain/agents/three_phase_blueprint_runtime.py tests/test_pass_with_fix.py docs/2026-03-26/stage3-threephase-pwf-early-exit-wave1-execution-ssot.md docs/temp/stage3-threephase-pwf-early-exit-wave1-execution-ssot.md`
- post-implementation bounded validation:
  - rerun one Stage 3-only telemetry canary and compare:
    - LLM call count
    - duration
    - total_cost_usd
    - PASS rate stability

## 11. Guardrails

- do not change `max_fix = 3` in this wave
- do not change `max_retries = 9` outer policy in this wave
- do not change ensemble fan-out or strategy selection
- do not change Director compare/audit semantics
- do not infer “score stall” from missing score values
- do not widen this wave into full PWF redesign

## 12. Temp Queue Notes

- temp status: pending
- cleanup condition:
  - implementation complete
  - verification complete
  - closure audit complete
  - then remove `docs/temp/stage3-threephase-pwf-early-exit-wave1-execution-ssot.md`
- roadmap dependency:
  - none at open time; this is a single active execution item

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py`
- queue-state sync: `python scripts/sync_temp_queue_state.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

---

## 3-Pass Audit Notes

- Pass 1: scope bounded to Stage 3 ThreePhase PASS_WITH_FIX loop only; outer retry, cache, Director, and Stage 4 were explicitly excluded
- Pass 2: claims anchored to live code in `three_phase_blueprint_runtime.py` and to the telemetry canary evidence; execution target narrowed to score-stall early-exit rather than broad PWF redesign
- Pass 3: implementation path is actionable and low-blast-radius; verification includes both targeted pytest and a post-implementation bounded telemetry canary
- Confidence: 97%
