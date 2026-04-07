# Material Benchmark PASS / HOLD / REJECT Cheat Sheet

Date: 2026-04-07
Status: active
Scope: operator quick-check card for external-model material readiness audits

## 1. One-Line Use

Use this immediately before:

- launching a material benchmark prompt
- accepting an external-model material report
- deciding whether to run `material_promotion_gate.py`

## 2. First Split

Ask these in order.

1. Is this a live promotion target?
2. Does the doc contain exact ledger rows `2, 3, 4, 5, 6`?
3. Is the target inside the current active promotion lane?

If the answer to `1` or `3` is clearly `no`, default to `REJECT`.

If the answer to `2` is `no`, default to `REJECT`.

## 3. PASS

Call the material benchmark `PASS` only if all of the following are true.

- exact ledger rows `2, 3, 4, 5, 6` exist
- every row has `has_cider: true`
- no row is blank
- `block 1` is not used as opening rescue
- `block 7+` is not used as opening rescue
- `bridge_or_payback_note` is not carrying a false row
- `block 6` is not `pain_only_exit: true`
- first-block proof, reevaluation, visible token, and next gate are all visible
- the target is inside the active promotion lane
- the report clearly says promotion gate is still separate

Quick read:

- `PASS = structurally promotable`

What `PASS` does not mean:

- it does not itself grant canon
- it does not itself grant `Phase0`
- it does not replace `material_promotion_gate.py`

Reference exemplar:

- [material_benchmark_office_checkup_next_day_report.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-07/material_benchmark_office_checkup_next_day_report.md)

## 4. HOLD

Call the material benchmark `HOLD` if the idea is still in the live lane but promotion must pause.

Common `HOLD` triggers:

- one or more ledger rows are false
- one or more ledger rows are blank
- `block 1` or `block 7+` is rescuing the opening
- `bridge_or_payback_note` is doing the real work instead of same-block receipt
- `block 6` closes in pain-only mode
- the ledger is strong, but the source doc is still intentionally self-locked as pre-promotion candidate
- the operator wants one more tightening pass before canon or `Phase0`

Quick read:

- `HOLD = live candidate, not promotable today`

Reference exemplar:

- [material_benchmark_line_stop_deputy_hold_example.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-07/material_benchmark_line_stop_deputy_hold_example.md)

## 5. REJECT

Call the material benchmark `REJECT` if the target should not enter the active promotion lane at all.

Common `REJECT` triggers:

- target is `legacy_import`, archive, quarantine, or reference-only
- target lacks exact machine-readable ledger rows `2~6`
- target lacks readiness claim/declaration
- protagonist engine breaks current house law
- opening is pain-only by design
- no credible visible first-block token exists
- under the current operator policy, the target is outside the active lane before any ledger discussion even starts

Quick read:

- `REJECT = do not promote this target in the current lane`

Reference exemplar:

- [material_benchmark_legacy_import_042_reject_example.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-07/material_benchmark_legacy_import_042_reject_example.md)

## 6. Fast Operator Matrix

| Question | PASS | HOLD | REJECT |
| --- | --- | --- | --- |
| exact ledger rows `2~6` exist | yes | maybe, but flawed | no |
| all rows `has_cider: true` | yes | no / not yet accepted | irrelevant if lane-ineligible |
| active promotion lane | yes | yes | no |
| promotion can proceed today | yes, after separate gate | no | no |
| separate promotion gate still required | yes | later | not applicable |

## 7. Acceptance Rule For External-Model Reports

Reject the report immediately if it does any of the following.

- uses pair grade language instead of `PASS / HOLD / REJECT`
- treats the benchmark report as promotion-gate output
- ignores missing ledger rows
- lets `block 1` or `block 7+` rescue the opening
- hides a false row behind `bridge_or_payback_note`

## 8. Final Operator Step

If the material report is `PASS` and the operator actually wants promotion:

```text
python -X utf8 scripts/material_promotion_gate.py --stage canon --path <candidate-md>
python -X utf8 scripts/material_promotion_gate.py --stage phase0 --path <pitch-md> --work-id <work_id>
```

If the report is `HOLD` or `REJECT`, do not run the promotion gate yet.

## 9. One-Line Rule

`PASS means promotable, HOLD means not yet, REJECT means not in this lane.`
