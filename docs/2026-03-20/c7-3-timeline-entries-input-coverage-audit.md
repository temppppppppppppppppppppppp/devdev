# C7-3 Timeline Entries Input Coverage Audit (3-Pass Audit)

Date: 2026-03-20
Mode: system-track live-survey follow-up
Confidence: 0.95

## Scope

- Source follow-up:
  - `docs/2026-03-20/c7-tracking-table-live-split-and-karma-status-fix-3pass-audit.md`
- Live evidence:
  - `projects/0_260318/project_data.db`
- Code review targets:
  - `modules/core/world_state.py`
  - `modules/core/stage4_post_processor.py`
  - `tests/test_timeline_entries.py`
  - `tests/test_cumulative_elapsed.py`
  - `tests/test_stage4_post_processor.py`

## Summary

`timeline_entries` is still empty in the live project, but the current evidence does not justify a bounded backend sink patch.

The active sink is real and already wired:

- `WorldState.update_from_state_changes()` writes DB `timeline_entries`
- but only from `state_changes["time_markers"]`

The live run did not provide `time_markers`.

## Live Evidence

From `projects/0_260318/project_data.db`:

- `timeline_entries = 0`
- `episode_bibles.time_passed` was empty in the inspected rows
- `state_logs.data.actual_truth` did not carry `time_markers`

From the live code:

- `modules/core/stage4_post_processor.py`
  - persists `bible_delta["time_passed"]`
- `modules/core/world_state.py`
  - persists timeline rows only from `time_markers`

## Why This Is Not Yet a Bounded Bugfix

Two different semantics are in play:

- `time_markers`
  - structured timeline event input
  - already tested and already sinks into DB
- `time_passed`
  - looser narrative summary string
  - currently stored in episode bible metadata, not promoted into `timeline_entries`

Blindly converting `time_passed` into timeline rows would be a behavior decision, not a pure sink fix.

## Existing Coverage

- `tests/test_timeline_entries.py`
  - proves `time_markers -> timeline_entries`
- `tests/test_cumulative_elapsed.py`
  - proves elapsed-time accumulation from `time_markers`
- `tests/test_stage4_post_processor.py`
  - proves `bible_delta["time_passed"]` persistence

## Decision

- `C7-3 timeline_entries`
  - remains open as input/extraction coverage
  - not promoted into an immediate backend patch

## Future Trigger

Reopen this item only if one of these becomes true:

- live runs start producing non-empty `time_passed` with operator expectation that it must feed `timeline_entries`
- upstream extraction is changed so `time_passed` is the canonical time signal
- product policy explicitly decides that `time_passed` should auto-materialize into timeline rows

## Conclusion

`C7-3` is not blocked by a missing DB write primitive. It is blocked by absent structured time input and an unresolved semantic choice between `time_markers` and `time_passed`.
