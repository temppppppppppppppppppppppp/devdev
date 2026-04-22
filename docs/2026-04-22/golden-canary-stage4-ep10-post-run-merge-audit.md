# Golden Canary Stage4 ep10 Post-Run Merge Audit

## Scope

- project: `골든 카나리아`
- lane: `Stage4 direct supervised guarded`
- run date: `2026-04-22`
- frontier truth at stop time: `ep9 PASS persisted`, `ep10 unresolved`
- authority rule: `live evidence > this audit > stale pre-run static watchlist`

## Live Evidence

1. persisted frontier stayed at `ep9`
   - `project_data.db` manuscripts max ep = `9`
   - no persisted `ep10` manuscript row exists
   - `runtime_audit.jsonl` shows `STAGE4_POST_PASS_CONTRACT` for `ep8`, `ep9`, and none for `ep10`

2. Stage4 rejected `ep10`, but the contradiction was already present in accepted Stage3 blueprint
   - `ep9` ends inside `여의도 한미증권 VIP룸` with `박성호` still present when the secure-phone call begins
   - accepted `ep10` Stage3 blueprint declares `opening_transition.type = direct_continuation`
   - the same accepted `ep10` blueprint then writes scene 1 as `박성호와 함께 ... VIP룸으로 들어온다`
   - this is an impossible re-entry/reset against the previous ending

3. downstream gate noise existed, but it was not the earliest owner
   - `stage_attempts` rows `45-46` for `ep10 attempt 4/5` are `REJECT` with `primary_failure_layer=downstream_gate`
   - those rows also carry stale or mixed reject metadata after later manuscript variants partially corrected the room geometry
   - the first stable defect is still `Stage3 accepted a contradictory opening`

## Root Cause Call

### Primary

- `UnifiedBlueprintValidator` did not explicitly reject a `direct_continuation` opening that re-entered a carryover-active character already on stage at the previous ending.
- `episode_progression` replay detection only escalated when `matched_families >= 2`, so a single opening-scene replay/reset could slip through.

### Secondary

- Stage4 downstream gate still surfaced `strong_advisory_escalation_non_local_fix`, but current code already contains strong-advisory fix-pack backfill logic.
- For this April 22 live blocker, downstream gate is acting as the firewall, not the first owner.

## Patch Applied

### Stage3 Validator

- file: `modules/domain/agents/unified_blueprint_validator.py`
- added direct-opening carryover re-entry detection:
  - if `opening_transition.type == direct_continuation`
  - and `opening_truth.active_characters` contains a character that scene 1 newly makes `enter`
  - emit `CRITICAL / opening_transition`
- strengthened replay detection:
  - a single matched replay family now escalates when it is `scene_1` under `direct_continuation`

### Stage3 Prompt Surface

- file: `modules/domain/agents/blueprint_ensemble.py`
- `EpisodeStatePacket` formatting now explicitly surfaces:
  - `opening.active_characters`
  - direct instruction that `direct_continuation` must treat them as already on-stage and must not re-stage re-entry

## Validation

1. targeted pytest
   - `python -m pytest tests/test_unified_blueprint_validator_lane_c.py tests/test_blueprint_ensemble_generate_ensemble.py -q`
   - result: `108 passed`

2. adjacent carryover shard
   - `python -m pytest tests/test_stage3_npc_capital_carryforward_guardrail.py -q`
   - result: `49 passed`

3. utf8 hygiene
   - `python scripts/check_utf8_hygiene.py modules/domain/agents/unified_blueprint_validator.py modules/domain/agents/blueprint_ensemble.py tests/test_unified_blueprint_validator_lane_c.py tests/test_blueprint_ensemble_generate_ensemble.py`

4. real-case replay
   - replayed the accepted `ep10` Stage3 blueprint through `_python_pre_validate` with the actual `ep9` ending location plus active characters
   - result now emits:
     - `CRITICAL / opening_transition`
     - `direct_continuation opening에서 carryover active character를 다시 입장시키고 있음: 박성호`

## Current Rerun Posture

- patch status: `ready`
- local validation: `clean`
- next operator step before rerun: external second-look on refreshed watchlist
- rerun target remains:
  - `Stage4 direct supervised guarded`
  - project `골든 카나리아`
  - `target_ep=10`
  - external cap `retry <= 5`

## Remaining Watchpoints

1. `ep10` opening must keep `박성호` already inside the room if `direct_continuation` is retained.
2. if the opening truly needs a new arrival beat, Stage3 must switch to `explicit_transition` or `jump_opening`.
3. even after the room-geometry fix, survey should still inspect:
   - hidden-number call semantics drift
   - gold-task ordering drift
   - oil framing drift (`same-night surge` vs `며칠째 횡보`)
4. downstream advisory noise (`npc_drift`, `numeric_drift`) stays secondary unless it becomes the first stable owner in the next live run.
