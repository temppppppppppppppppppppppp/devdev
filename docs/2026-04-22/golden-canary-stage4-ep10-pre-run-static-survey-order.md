# Golden Canary Stage4 ep10 Pre-Run Static Survey Order

## Purpose

External second-look on the refreshed `ep10` blocker family before the next guarded rerun.

## Operator Constraints

- read-only survey only
- no code edits
- no DB writes
- no rerun launch
- treat `live evidence > this static survey`

## Primary Context

- audit: `docs/2026-04-22/golden-canary-stage4-ep10-post-run-merge-audit.md`
- watchlist: `docs/2026-04-22/golden-canary-stage4-ep10-pre-run-static-watchlist.md`

## Review Goal

Verify or challenge this owner call:

- primary owner: `Stage3 direct-continuation opening carryover failure`
- supporting owner: `single opening replay family slipped through replay guardrail`
- secondary only: `Stage4 downstream advisory / fix-pack semantics`

## Required Reads

1. `docs/2026-04-22/golden-canary-stage4-ep10-post-run-merge-audit.md`
2. `docs/2026-04-22/golden-canary-stage4-ep10-pre-run-static-watchlist.md`
3. `projects/골든 카나리아/drafts/ep_0009.txt`
4. `projects/골든 카나리아/logs/artifacts/stage3/ep_0010/attempt_01/final_blueprint__emotion_focused.json`
5. `projects/골든 카나리아/logs/artifacts/stage4/ep_0010/attempt_04/rejected_best__B_tension.txt`
6. `projects/골든 카나리아/logs/artifacts/stage4/ep_0010/attempt_05/rejected_best__B_asp_correction.txt`
7. `modules/domain/agents/unified_blueprint_validator.py`
8. `modules/domain/agents/blueprint_ensemble.py`

## Questions To Answer

1. Is the new primary owner call correct?
2. Is there any higher-authority static risk still likely to block the next rerun?
3. Are hidden-number call semantics, gold-task ordering, or oil framing likely to remain first-order blockers after the patch?
4. Is there any reason to widen the next fix wave beyond the current Stage3 guardrail patch?

## Required Output

Produce one bounded note with:

- `agreement / disagreement`
- `top 3 watchpoints`
- `one-line rerun risk call`

## Copy-Paste Order

```text
Read-only static survey for Golden Canary Stage4 rerun prep.

Read these first:
- docs/2026-04-22/golden-canary-stage4-ep10-post-run-merge-audit.md
- docs/2026-04-22/golden-canary-stage4-ep10-pre-run-static-watchlist.md
- projects/골든 카나리아/drafts/ep_0009.txt
- projects/골든 카나리아/logs/artifacts/stage3/ep_0010/attempt_01/final_blueprint__emotion_focused.json
- projects/골든 카나리아/logs/artifacts/stage4/ep_0010/attempt_04/rejected_best__B_tension.txt
- projects/골든 카나리아/logs/artifacts/stage4/ep_0010/attempt_05/rejected_best__B_asp_correction.txt
- modules/domain/agents/unified_blueprint_validator.py
- modules/domain/agents/blueprint_ensemble.py

Constraints:
- no code changes
- no DB writes
- no rerun launch
- live evidence wins over static survey

Return one bounded note with:
- agreement/disagreement on the new primary owner call
- top 3 watchpoints before rerun
- one-line rerun risk call
```
