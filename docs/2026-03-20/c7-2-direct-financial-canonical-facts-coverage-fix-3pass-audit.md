# C7-2 Direct Financial Canonical Facts Coverage Fix (3-Pass Audit)

Date: 2026-03-20
Mode: system-track live-survey follow-up
Confidence: 0.96

## Scope

- Source follow-up:
  - `docs/2026-03-20/c7-tracking-table-live-split-and-karma-status-fix-3pass-audit.md`
- Live evidence:
  - `projects/0_260318/project_data.db`
- Patch targets:
  - `modules/core/fact_ledger.py`
  - `tests/test_fact_ledger.py`
  - `tests/test_canonical_constraints.py`

## Summary

`C7-2` was initially reclassified as schema/input-population only, but fresher live evidence narrowed it into a bounded extractor coverage defect.

Live `state_logs.data.actual_truth` already carried direct finance scalars such as:

- `capital`
- `total_assets`
- `wealth`

However, `FactLedger._extract_numerical_facts()` only consumed:

- `status_shadow`
- `financial_events`
- `power_level`
- `numerical_facts`

That left `canonical_facts` empty even though real finance scalars were already present in the Stage 4 state payload.

## Live Evidence

Fresh inspection of `projects/0_260318/project_data.db` showed:

- `state_logs.data.actual_truth.capital = 2000000000`
- `state_logs.data.actual_truth.total_assets = 2000000000`
- `state_logs.data.actual_truth.wealth = "20억"`
- `state_logs.data.actual_truth` did not use `financial_events` or `numerical_facts`

Interpretation:

- this was not a missing DB primitive
- this was not a broad schema rewrite requirement
- this was a narrow extractor coverage gap on already-present live fields

## Patch

Bounded fix applied in `modules/core/fact_ledger.py`:

- added direct-finance allowlist:
  - `capital`
  - `total_assets`
  - `wealth`
- added a small Korean-unit parser for direct scalar values
- direct finance scalars now flow into:
  - in-memory `FactLedger.numbers`
  - DB `canonical_facts` via existing `update_number()` dual-write

Non-goals:

- no change to `timeline_entries`
- no broad schema redesign
- no free-form extraction from arbitrary string fields such as `market_insight`

## Regression Coverage

- `tests/test_fact_ledger.py`
  - direct finance scalar extraction into `numbers`
- `tests/test_canonical_constraints.py`
  - direct finance scalar sync into real DB `canonical_facts`

## Validation

- `python -m pytest tests/test_fact_ledger.py -q`
- `python -m pytest tests/test_canonical_constraints.py -q`

## Decision

- `C7-2 canonical_facts`
  - reopened on fresher live evidence
  - bounded direct-finance coverage fix applied
  - closed

- `C7-3 timeline_entries`
  - still open as input/extraction coverage
  - not closed by this patch

## Conclusion

`canonical_facts` emptiness in the live project was not purely upstream noise. A narrower backend coverage defect existed for direct finance scalars already present in `actual_truth`, and that defect is now closed.
