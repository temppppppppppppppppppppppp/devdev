# P0 Stage 4 Hardening OPUS Brief

## Scope
- P0 only
- no real rerun
- goal: reduce late discard cost and make firewall rejection explicitly patchable

## Touched Paths
- [director_ensemble.py](C:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py)
- [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py)

## Change Summary
- Firewall REJECT now keeps `score=44` cap but defaults to `fix_scope="inplace"` and `fix_scope_reasoning=firewall_reason` when a selected manuscript exists and the Director did not request a stronger scope.
- Post-select conflict downgrade now preserves `selected_strategy_key`, `selection_reason`, `verdict_reason`, and `reject_bucket="post_select_conflict"` in `previous_attempt`.
- Post-select conflict retries now prefer `patch_with_feedback(single_strategy=selected_strategy_key)` before `inplace_patch` or full regenerate.
- `selection_reason` and `verdict_reason` remain split in Stage 4 logging and persistence.

## Review Questions
1. Does routing post-select conflict to `partial` patch risk letting hard contradictions slip through too easily?
2. Is defaulting firewall REJECT to `fix_scope="inplace"` too permissive when the chosen manuscript has broader structural damage?
3. Does fixing retries to `selected_strategy_key` create stale strategy lock-in in cases where the selected branch was itself the wrong branch?

## Regression Result
- Command:
```text
pytest tests/test_stage4_interview_round.py tests/test_v75c_contradiction_firewall.py tests/integration/test_patch_wiring.py -q
```
- Result: `70 passed`

## Related Analysis
- [ops-runtime-cost-reconciliation-codex.md](C:/Users/User/Desktop/글도비/docs/2026-03-11/ops-runtime-cost-reconciliation-codex.md)
