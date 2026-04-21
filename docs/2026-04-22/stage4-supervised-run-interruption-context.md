# Stage4 Supervised Run Interruption Context

Date: 2026-04-22
Project: `projects/골든 카나리아`
Status: interrupted-by-user
Confidence: 0.97

## Summary

- Real-project `Stage 4 supervised` was resumed toward `target_ep=5`.
- The run was explicitly interrupted by the user and the background Python process was terminated.
- Persisted frontier at interruption time:
  - `Stage 3`: blueprints through `ep16`
  - `Stage 4`: manuscripts through `ep3`
  - `Stage 4 ep4`: rejected 3 times
  - `Stage 4 ep5`: not started

## Persisted State At Stop Time

- DB snapshot from `projects/골든 카나리아/project_data.db`
  - `blueprint_count=16`
  - `max_blueprint_ep=16`
  - `manuscript_count=3`
  - `max_manuscript_ep=3`
  - `stage3_ep4_attempt_rows=1`
  - `stage4_ep4_attempt_rows=3`
  - `stage4_ep5_attempt_rows=0`
- Draft/manuscript artifacts currently present
  - `drafts/ep_0001.txt`
  - `drafts/ep_0002.txt`
  - `drafts/ep_0003.txt`
  - corresponding `*.settlement.json` files
- Relevant live logs
  - `logs/session_20260422_065708.log`
  - `logs/session_20260422_080513.log`
  - `logs/episode_production.jsonl`
  - `logs/quality_metrics.jsonl`
  - `logs/runtime_audit.jsonl`

## What Happened

### First Stage4 wave

- The first real-project Stage4 supervised run produced manuscripts for `ep1`, `ep2`, and `ep3`.
- `ep4` did not pass. Two persisted Stage4 reject rows were left in DB before the resumed attempt:
  - row `27`: `REJECT`, score `94`, `primary_failure_layer=downstream_gate`
  - row `28`: `REJECT`, score `90`, `primary_failure_layer=downstream_gate`

### Investigation result before resume

- The most concrete code-side issue found was in `modules/core/numeric_consistency_checker.py`.
- FactLedger carryover numbers in this project are stored as raw KRW with `unit="won"`.
- `_to_eok()` already handled:
  - Hangul `원`
  - unitless raw KRW
- but did not handle literal `"won"` / `"krw"`.
- Because of that, `2_000_000_000 won` could be rendered as `2000000000.0억` instead of `20.0억`, creating a likely false-positive `numeric_carryover_authority mismatch`.

## Patch Applied Before Resume

- Production patch:
  - `modules/core/numeric_consistency_checker.py`
  - added `won/krw` -> KRW-to-억 conversion in `_to_eok()`
- Focused regression test:
  - `tests/test_numeric_consistency_checker.py`
  - added a case asserting that `20억` vs `2_000_000_000 won` does not raise a false-positive FactLedger mismatch
- Focused verification completed:
  - `pytest tests/test_numeric_consistency_checker.py -q -k "carryover_authority_warning_formats_unitless_raw_krw_as_eok or carryover_authority_won_unit_does_not_false_positive_on_same_eok_value"`
  - result: `2 passed`

## Resume Attempt Outcome

- After the numeric patch, Stage4 was resumed again toward `target_ep=5`.
- The resumed process did not reach manuscript persistence for `ep4` or `ep5` before interruption.
- A third Stage4 reject row was persisted for `ep4`:
  - row `29`: `REJECT`, score `40`, `primary_failure_layer=director_quality`
  - `gate_basis=continuity_firewall`
  - `repair_contract.subtype=타임라인`
  - `repair_contract.target_kind=scene_model`
  - `fix_pack` empty / non-local rewrite required

## Highest-Signal Remaining Problem

- The dominant unresolved blocker is no longer a tiny local phrase fix.
- The latest persisted reject is a timeline replay / completed-event repetition problem:
  - `ep3` already executed the Park Seong-ho meeting and the cash-liquidation / account-setup directive
  - `ep4 scene 2` attempted to stage that directive again as if it were happening for the first time
- The persisted reject rationale explicitly says `scene 2` should be rewritten away from “meet Park again and reissue the same order” toward a follow-up/reporting execution beat.

In short:

- `ep4` is blocked primarily by frontier/timeline replay
- not by a bounded local wording patch

## Important Caveat

- The persisted `row 29` reject text still contains `numeric_carryover_authority` warnings rendered as if the ledger were `2000000000.0억`.
- That means the end-to-end live Stage4 lane has **not yet** been freshly validated as clean after the local `won/krw` numeric patch.
- So the numeric patch is a justified root-cause fix at code level, but its live-run effect is still unconfirmed at interruption time.

## Process State

- The background resume runner was terminated on user interruption.
- No Stage4 resume Python process should remain active after this context snapshot.

## Resume Recommendation

When resuming later, the next step should be:

1. Re-enter from `ep4`, not `ep5`.
2. Treat `ep4` as a `frontier/timeline correction` problem first.
3. Validate whether the `won/krw` numeric fix actually removes the carryover false positive in live Stage4.
4. Only continue to `ep5` after `ep4` passes cleanly.

## Queue Note

- `docs/temp/` still contains active system execution queue artifacts and roadmap files.
- This run/context snapshot was performed under explicit user redirection, so the queue remains pending rather than closed.
