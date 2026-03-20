# C10 Target Episode Decision Logging (3-Pass Audit)

Date: 2026-03-20
Confidence: 0.97
Scope: bounded backend observability patch

## Problem

`Stage4Orchestrator` stopped when `next_ep > target_ep`, but this boundary was only visible in UI text.

Before this patch:

- [stage4_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py) stopped the loop
- no explicit control-row was written to `decisions.jsonl`
- no dedicated audit event named `target_ep_reached` was emitted

## Change

Updated [stage4_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py).

- added `_log_target_ep_reached(target_ep, next_ep)`
- when the stop boundary is hit:
  - `session_logger.log_decision(...)` writes a control-row with:
    - `stage="stage4_control"`
    - `decision_type="target_ep_reached"`
    - `result="STOP"`
    - `ep_num=<target_ep>`
    - `next_ep=<next_ep>`
  - `audit_event("target_ep_reached", ...)` is emitted when audit hook exists

Using `stage4_control` avoids polluting ordinary Stage 4 attempt-level proof-digest joins.

## Validation

Sequential shards:

- `python -m pytest tests/test_stage4_orchestrator.py -k "Stage4AuditSummary or log_target_ep_reached" -q` -> `9 passed`
- `python -m pytest tests/e2e/test_l3_stage4_smoke.py -k "loop_termination" -q` -> `1 skipped`

Regression added:

- [test_stage4_orchestrator.py](C:/Users/User/Desktop/글도비/tests/test_stage4_orchestrator.py)
  - direct helper contract for control decision row + audit event

## Conclusion

`C10` is now closed as a bounded backend observability fix.

Most actionable remaining OPUS-derived backend candidates are now:

- `C4`
- `C8`
- plus policy-shaped `C3`, `C9`
