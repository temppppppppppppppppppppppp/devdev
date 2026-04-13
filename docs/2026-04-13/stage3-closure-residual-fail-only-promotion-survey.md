# Stage3 Closure Residual Fail-Only Promotion Survey

- Date: 2026-04-13
- Scope: current `main@2701e9e6` re-audit of the residual families reported by `stage3-live-run-closure-and-residual-families-parallel-full-survey.md`
- Mode: survey-only, bounded execution-promotion survey for the active Stage3 queue lanes
- Baseline Commit: `2701e9e6a7d741d455afc930afd94e178ed555d4`
- Baseline Dirty Summary: `clean`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
- Confidence: 96%

## Scope

This survey answers one narrow execution question:

- which residual findings from the Stage3 closure survey still require a bounded code tranche on current `main`, and which execution lane should own them

This document does not open a new queue lane.

This document does not patch code by itself.

## Why Additional Survey Was Required

The closure survey already proved the live rerun state:

- `ep2` closed as `PASS_WITH_WARNING 85`
- `ep3` closed as `PASS 92`
- the run returned to menu

But that document was still a closure survey, not an execution-shaping decision. It listed four possible reopen families:

- `temporal_deictic`
- advisory-only `scenario_density`
- concept/entity warning normalization
- Stage3 completion-stat observability drift

Execution promotion on current `main` needed one more bounded pass because:

1. not every residual family has the same current-head execution value
2. the active queue already has a Stage3 parent lane, a Stage3 partial-fix child lane, and a sibling opening-transition lane
3. the right action here is not "open another lane", but "promote only the residual slice that still has direct code evidence and bounded ownership"

## Evidence Anchors

- Prior closure survey:
  - [stage3-live-run-closure-and-residual-families-parallel-full-survey.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-13/stage3-live-run-closure-and-residual-families-parallel-full-survey.md)
- Prior handoff / precursor surveys:
  - [stage3-live-run-handoff-context-note.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-13/stage3-live-run-handoff-context-note.md)
  - [stage3-live-run-retry-plateau-parallel-full-survey.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-13/stage3-live-run-retry-plateau-parallel-full-survey.md)
  - [stage3-live-run-quality-gate-patch-reopen-parallel-full-survey.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-13/stage3-live-run-quality-gate-patch-reopen-parallel-full-survey.md)
- Governing execution docs:
  - [0_0-stage3-contract-tightening-remediation-execution-ssot.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md)
  - [0_0-stage3-partial-fix-hardening-remediation-execution-ssot.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-07/0_0-stage3-partial-fix-hardening-remediation-execution-ssot.md)
  - [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md)
- Current code owners:
  - [three_phase_blueprint_runtime.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py:1492)
  - [three_phase_blueprint_runtime.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py:1734)
  - [unified_blueprint_validator.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py:326)
  - [unified_blueprint_validator.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py:2340)
  - [stage3_orchestrator.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage3_orchestrator.py:957)

## Findings

### 1. `scenario_density` still has direct current-head evidence as a low-yield local-patch cost

This family remains execution-worthy on current `main` because the cost is still visible in live code, not only in historical logs.

Current-head evidence:

- `scenario_density` issues are still emitted as advisory-only in [unified_blueprint_validator.py:2408](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py:2408)
- the same issue still carries a concrete `fix_pack` with `patch_target_records -> integrated_scenario -> local_sentence` in [unified_blueprint_validator.py:2425](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py:2425)
- validator still merges advisory issue fix packs through [unified_blueprint_validator.py:326](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py:326)
- runtime still normalizes and consumes `advisory_fix_pack` inside the Stage3 patch loop in [three_phase_blueprint_runtime.py:1734](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py:1734)

Conclusion:

- this is not stale survey text
- the cheapest bounded improvement is to stop low-yield local repair churn when only advisory `scenario_density` residuals remain

### 2. The Stage3 completion-stat mismatch still has direct current-head evidence

The closure survey's observability finding is still live in code.

Current-head evidence:

- [stage3_orchestrator.py:957](/c:/Users/wjjo/Desktop/글도비/modules/core/stage3_orchestrator.py:957) prints `success_count` and `fail_count` from the current run
- [stage3_orchestrator.py:960](/c:/Users/wjjo/Desktop/글도비/modules/core/stage3_orchestrator.py:960) separately prints `ctx.agents["three_phase_bp"].get_stats()["pass_rate"]`

Conclusion:

- the operator-facing mismatch is still real on current `main`
- this is a bounded same-lane observability fix, not a new queue topic

### 3. `temporal_deictic` remains important, but it is not the best current bounded tranche

Current-head evidence confirms the detector still exists in [unified_blueprint_validator.py:1810](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py:1810).

But compared with `scenario_density`, this family does not yet present the same level of "cheap current-head control-plane waste" evidence for an immediate bounded patch in this turn.

Conclusion:

- keep it on the residual watchlist
- do not promote it ahead of the narrower advisory-loop cost fix

### 4. Concept/entity warning normalization also stays deferred for this turn

The closure survey showed that the visible shape in the latest tail was concept aliasing around `이란 핵 문제`, not a fresh hard `organization mismatch` spike.

Conclusion:

- keep entity/concept normalization inside the broader Stage3 parent watchlist
- do not widen this turn into a new concept-normalization patch family

## Execution Promotion

No new queue owner is needed.

Promote this residual slice into the existing Stage3 execution docs as:

1. `0_0-stage3-partial-fix-hardening-remediation`
   - owner of the bounded fail-only change
   - target: suppress low-yield local patch churn when only advisory `scenario_density` residuals remain

2. `0_0-stage3-contract-tightening-remediation`
   - parent owner of the same-session operator-visibility follow-up
   - target: make Stage3 completion stats read as one coherent operator surface rather than mixed run-local/cumulative authority

3. `active-temp-execution-roadmap`
   - keep queue rank unchanged
   - record the new residual slice as a same-lane landed-or-in-progress bounded follow-up, not as a new lane

## Proposed Tranche Shape

Bounded implementation in this turn should stay limited to:

1. runtime gating for advisory-only `scenario_density` residuals
2. Stage3 completion-stat surface normalization

Explicitly deferred:

- `temporal_deictic` semantic tightening
- concept/entity warning normalization
- broader memory / context routing work
- new queue creation or queue reranking

## Final Judgment

Additional survey was justified, but only as a narrow promotion pass.

The correct formal move is:

- do not open a new Stage3 lane
- re-audit and update the existing Stage3 parent/child execution docs
- realize one bounded residual tranche on current `main`

## 3-Pass Audit Record

### Pass 1. Structure / Scope

- document type is survey-only promotion guidance, not a new execution SSOT
- scope is limited to current-head residual execution selection
- included and excluded surfaces are explicit

### Pass 2. Evidence / Consistency

- all promoted findings were rechecked against live code on `2701e9e6`
- no queue-rank claim exceeds the active roadmap
- the survey keeps `temporal_deictic` and entity normalization deferred because the current evidence is weaker for immediate bounded action

### Pass 3. Execution / Readability

- the owning lanes are explicit
- the bounded tranche is explicit
- no new queue owner or broad redesign is introduced
