# C7 Tracking Tables Live Split and Karma Status Fix (3-Pass Audit)

Date: 2026-03-20
Mode: system-track live survey follow-up
Confidence: 0.96

## Scope

- Source OPUS item:
  - `docs/2026-03-18/OPUS/ssot_execution/s8-0_260318-project-deepdive-execution.md`
- Live evidence targets:
  - `projects/0_260318/project_data.db`
  - `modules/core/stage4_post_processor.py`
  - `modules/core/db_manager.py`
  - `modules/core/fact_ledger.py`
  - `modules/core/world_state.py`
  - `tests/test_stage4_post_processor.py`

## Summary

`C7` was not a single missing-tracking-table bug.

- `C7-1 karma_status`
  - real live sink gap
  - `state_logs.karma_matrix` was populated in the real run, but the current Stage 4 PASS path did not dual-write into `karma_status`
  - fixed in this pass
- `C7-2 canonical_facts`
  - this pass originally classified it as schema/input-population gap
  - later fresh live evidence showed direct finance scalars already existed in `actual_truth`
  - that narrower direct-finance coverage gap is superseded by:
    - `docs/2026-03-20/c7-2-direct-financial-canonical-facts-coverage-fix-3pass-audit.md`
- `C7-3 timeline_entries`
  - not a direct missing-table bug
  - live run stayed empty because `time_markers` were absent
  - reclassified as upstream extraction/input gap

## Live Evidence

Fresh query against `projects/0_260318/project_data.db`:

- `karma_status = 0`
- `canonical_facts = 0`
- `timeline_entries = 0`
- `character_voice = 0`
- `npc_relationship_edges = 0`
- `state_logs = 2`
- `stage_attempts = 17`
- `director_selections = 17`
- `episode_meta = 2`

Anchor truth from the same DB:

- `fact_ledger.last_updated_ep = 2`
- `fact_ledger.numbers_len = 0`
- `fact_ledger.characters_len = 4`
- `world_state.last_updated_ep = 2`
- `world_state.timeline_len = 0`

State log truth from the same DB:

- `ep1 karma_len = 3`
- `ep2 karma_len = 1`
- `ep2 relationship_len = 3`
- `actual_truth` carried finance-like scalar keys such as `capital`, `wealth`, `total_assets`, `stocks`, `market_insight`
- `actual_truth` did not carry `time_markers`

Interpretation:

- `karma_status = 0` despite non-empty `karma_matrix` means a real sink gap existed on the live Stage 4 PASS path
- `canonical_facts = 0` does not prove a missing DB sink by itself
  - `FactLedger._extract_numerical_facts()` currently syncs only:
    - `status_shadow`
    - `financial_events`
    - `power_level`
    - `numerical_facts`
  - the observed run had finance-like scalar fields in `actual_truth`, but not those supported extractor buckets
- `timeline_entries = 0` is explained by absent `time_markers`
  - `WorldState.update_from_state_changes()` only syncs timeline rows from `time_markers`

## Code Findings

### C7-1 karma_status

- `modules/core/stage4_post_processor.py`
  - already computed `karma_matrix`
  - already persisted it into `episode_bibles` and `state_logs`
  - did not call `db.update_karma(...)` on the live PASS path
- `modules/core/db_manager.py`
  - `update_karma(...)` already existed and was valid
- `modules/core/db_manager.py`
  - legacy `commit_episode_factory(...)` still called `update_karma(...)`

Judgment:

- this was a path migration omission, not a missing DB primitive

### C7-2 canonical_facts

- `modules/core/fact_ledger.py`
  - `update_number(...)` already dual-writes into `canonical_facts`
  - `_extract_numerical_facts(...)` is the active extractor
  - extractor coverage is intentionally narrow

Judgment:

- current emptiness in `0_260318` is a live schema/input mismatch, not a direct sink absence

### C7-3 timeline_entries

- `modules/core/world_state.py`
  - `upsert_timeline_entry(...)` is already wired
  - it only runs from `time_markers`

Judgment:

- current emptiness in `0_260318` is explained by missing `time_markers`

## Patch

Bounded fix applied:

- `modules/core/stage4_post_processor.py`
  - added `_normalize_karma_entry(...)`
  - added `_persist_karma_status(...)`
  - Stage 4 PASS flow now dual-writes `karma_matrix` into `karma_status`
  - failure stays soft:
    - does not fail the whole PASS path
    - emits soft-failure telemetry and UI warning
  - in-memory `current_project.karma_status` cache is also updated

## Regression Coverage

- `tests/test_stage4_post_processor.py`
  - `test_karma_matrix_flows_into_karma_status_table`
  - `test_karma_status_save_failure_is_logged_as_soft_failure`

## Validation

- `python -m pytest tests/test_stage4_post_processor.py -k "karma_matrix_flows_into_karma_status_table or karma_status_save_failure_is_logged_as_soft_failure" -q`
  - `2 passed, 50 deselected`
- `python -m pytest tests/test_stage4_post_processor.py -k "quality_signal_save_failure_is_logged_as_soft_failure or relationship_changes_flow_into_state_log_and_state_sinks or active_pressure_vectors_flow_into_state_log_bible_and_world_state" -q`
  - `3 passed, 49 deselected`
- `python -m pytest tests/test_stage4_post_processor.py -q`
  - `52 passed`

## Decision

- `C7-1 karma_status`
  - fixed and closed
- `C7-2 canonical_facts`
  - reclassified
  - not a bounded BE sink bug from this evidence alone
- `C7-3 timeline_entries`
  - reclassified
  - not a bounded BE sink bug from this evidence alone

## Conclusion

`C7` should no longer be treated as a single "empty tracking tables" item.

The first bounded live backend defect in that cluster was `karma_status`, and it is now closed. `canonical_facts` was later reopened on fresher live evidence and closed separately for direct finance scalar coverage. `timeline_entries` still remains better understood as upstream extraction/schema coverage, not direct DB sink absence.
