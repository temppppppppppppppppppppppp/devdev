# C9 NPC Drift Advisory Governance Audit

Date: 2026-03-20
Mode: system-track policy audit
Confidence: 0.95

## Scope

- Source OPUS item:
  - `docs/2026-03-18/OPUS/ssot_execution/s8-0_260318-project-deepdive-execution.md`
- Live targets:
  - `modules/core/npc_drift_advisor.py`
  - `modules/core/stage3_orchestrator.py`
  - `tests/test_npc_drift_advisor.py`
  - `tests/e2e/test_lm_advisory_smoke.py`

## Summary

`C9` is not a missing check.

The live code explicitly implements NPC drift detection as advisory-only.

## Live Findings

- `modules/core/npc_drift_advisor.py`
  - module docstring explicitly says:
    - advisory-only
    - Director keeps final judgment authority
- `NpcDriftAdvisor.check(...)`
  - returns drift findings
  - does not mutate facts
  - does not hard-reject on its own
- `modules/core/stage3_orchestrator.py`
  - semantic/advisory material is injected into context as warning/reference input
  - not as an unconditional blocking gate
- tests already exist around the advisory path:
  - `tests/test_npc_drift_advisor.py`
  - `tests/e2e/test_lm_advisory_smoke.py`

## Judgment

This is a governance choice, not a compact backend defect.

Current model:

- drift advisors detect suspicious narrative/state shifts
- Director receives that signal
- Director decides whether it is acceptable, explainable, or reject-worthy

Alternative model:

- promote NPC drift to an automatic blocking rule

That alternative would change the current authority split and should be treated as a separate policy rewrite.

## Recommendation

Keep `npc_drift` advisory-only unless there is a deliberate decision to move narrative drift signals from Director judgment input into a hard gate class.

## Conclusion

`C9` should remain classified as a policy boundary, not as the next bounded backend bugfix.
