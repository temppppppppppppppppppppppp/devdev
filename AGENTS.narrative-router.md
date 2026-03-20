# Narrative Router Sidecar

Purpose:
- keep root `AGENTS.md` lighter and reduce merge-conflict surface
- store narrative-router-specific read order and operator notes outside the main workspace SSOT

This file is subordinate to root `AGENTS.md`.

## Narrative Router Read Order

1. `docs/narrative-router/SSOT_narrative-router-integrated-order.md`
2. resolve family
3. open the resolved family integrated order
4. open the resolved family planning / production / BI harnesses

## Family Summary

`blockguide`
- `docs/blockguide/SSOT_blockguide-integrated-order.md`
- `docs/blockguide/treatment-planning-harness.md`
- `docs/blockguide/treatment-production-harness-v2.md`
- `docs/blockguide/bi-production-harness-v1.md`
- if `alt_history`, also `docs/blockguide/alt_history_db_harness.md`

`wuxguide`
- `docs/wuxguide/SSOT_wuxguide-integrated-order.md`
- `docs/wuxguide/wuxia-planning-harness.md`
- `docs/wuxguide/wuxia-production-harness.md`
- `docs/wuxguide/wuxia-bi-production-harness.md`

## Family Resolution Heuristic

- modern-fantasy business-power works -> `blockguide`
- wuxia / xianxia / jianghu / sect / realm-first works -> `wuxguide`
- explicit user family hint overrides heuristics

## Operator Note

Use the router CLI before entering family-specific generation:

```bash
python -X utf8 scripts/narrative_router.py --genre <genre> --work-id <work_id> --json
```

For routed entry examples, see `README.narrative-router.md`.
