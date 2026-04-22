# Golden Canary Stage4 ep10 Pre-Run Static Watchlist

## Authority

- `live evidence > this watchlist > stale survey text > assumption`
- this watchlist is for the next `골든 카나리아 / Stage4 / target_ep=10` rerun after the April 22 patch

## What Changed Since The Last Run

- Stage3 now has a direct-opening guardrail for carryover-active-character re-entry.
- Stage3 replay detection now escalates a single opening-scene replay family when the opening is `direct_continuation`.
- the prompt now surfaces `opening.active_characters` and states that direct carryover must not restage re-entry.

## Primary Watchpoints

1. `direct_continuation` opening actor continuity
   - if `ep10` keeps `direct_continuation`, `박성호` must already be in the VIP room at scene 1 start
   - scene 1 must not restage `박성호` entering from outside

2. opening replay family
   - scene 1 must not replay the just-consumed VIP-room opening family from `ep9`
   - opening must advance from the prior phone-call frontier instead of re-starting the room geometry

3. hidden-number call semantics
   - survey whether the blueprint still collapses the mysterious call too early into the realtor lane
   - watch for premature resolution of the call source before the story earns it

4. gold-task ordering
   - `ep9` already issued the gold-data instruction before the call
   - `ep10` should not replay that order as if it is freshly given after the opening call

5. oil framing carryover
   - `ep9` frontier is same-night live surge pressure
   - watch for blueprint/manuscript drift that reframes it as a settled sideways market without an explicit time cut

## Secondary Watchpoints

1. `npc_drift`
   - keep it secondary unless it becomes the first stable blocker in live evidence

2. `numeric_drift`
   - still monitor it, but do not treat it as the owner unless it becomes a blocking layer rather than advisory noise

3. downstream fix-pack semantics
   - if Stage4 still rejects on `strong_advisory_escalation_non_local_fix`, inspect whether the new manuscript actually needs non-local repair or whether the advisory path is over-escalating again

## Suggested Read Order

1. `docs/2026-04-22/golden-canary-stage4-ep10-post-run-merge-audit.md`
2. `modules/domain/agents/unified_blueprint_validator.py`
3. `modules/domain/agents/blueprint_ensemble.py`
4. `projects/골든 카나리아/drafts/ep_0009.txt`
5. `projects/골든 카나리아/logs/artifacts/stage3/ep_0010/attempt_01/final_blueprint__emotion_focused.json`
6. `projects/골든 카나리아/logs/artifacts/stage4/ep_0010/attempt_04/rejected_best__B_tension.txt`
7. `projects/골든 카나리아/logs/artifacts/stage4/ep_0010/attempt_05/rejected_best__B_asp_correction.txt`

## Expected Output From External Review

- a bounded `delta watchlist`
- agreement or disagreement on the new primary owner call
- any additional static watchpoints that should be merged before rerun
- no code changes required for the review pass
