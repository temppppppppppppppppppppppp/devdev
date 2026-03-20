# C3 Director Python Critical Hard-Gate Policy Audit

Date: 2026-03-20
Mode: system-track policy audit
Confidence: 0.95

## Scope

- Source OPUS item:
  - `docs/2026-03-18/OPUS/ssot_execution/s8-0_260318-project-deepdive-execution.md`
- Live targets:
  - `modules/domain/agents/director_ensemble.py`
  - `modules/domain/agents/director_prompts.py`
  - `modules/core/stage4_interview_round.py`
  - `tests/test_director_modules.py`
  - `tests/test_stage4_interview_round.py`

## Question

Does the current system still have a bounded backend bug where Python-side CRITICAL warnings fail to override an unsafe Director PASS?

## Live Findings

### What already hard-gates today

- `modules/domain/agents/director_ensemble.py`
  - contradiction firewall already force-rejects:
    - at least 1 `CRITICAL` contradiction
    - or at least 2 `MAJOR` contradictions
- `tests/test_stage4_interview_round.py`
  - extensive regression coverage already locks contradiction-firewall behavior

This means the OPUS wording "Director 99 override" is overstated if interpreted as "no hard gate exists".

### What still remains soft

- `modules/domain/agents/director_prompts.py`
  - Python findings remain part of the scoring/advisory channel
- `modules/domain/agents/director_ensemble.py`
  - `python_warnings` still shape score and advisory context
  - there is no generic rule of the form:
    - `N Python CRITICAL warnings => force REJECT`
- `modules/core/stage4_interview_round.py`
  - final orchestration consumes Director verdict/gate semantics
  - it does not add a separate generic Python critical hard gate on top

## Judgment

This is no longer a bounded missing-check bug.

It is now a governance decision:

- current model:
  - contradiction-like critical evidence already has a hard gate
  - generic Python critical signals remain Director-facing judgment input
- alternative model:
  - promote generic Python CRITICAL warnings into a global hard gate

That alternative would materially change the current Director sovereignty model.

## Why this is policy-shaped

If a new generic hard gate is added here, the system changes from:

- `Director judges with strong Python evidence`

to:

- `Python can unilaterally override Director for broader classes of warnings`

That is not a narrow bugfix. It is a change in authority allocation.

## Recommendation

Keep current behavior unless there is a separate policy decision to expand hard-gate scope beyond contradiction-class failures.

If revisited later, the next step should be a dedicated policy design pass, not a compact bugfix patch.

## Conclusion

`C3` remains live only as a policy/governance boundary.

It should not be treated as the next bounded backend fix from the OPUS BE P0-P3 set.
