# C1 Arc Title Propagation (3-Pass Audit)

Date: 2026-03-20
Confidence: 0.97
Scope: bounded backend patch

## Problem

`C1` from OPUS screening remained live:

- `modules/domain/agents/blueprint_constraint_compiler.py`
  - `_extract_episode_focus()` did not carry an explicit per-episode title field
- `modules/domain/agents/blueprint_ensemble.py`
  - generation constraints therefore only exposed tactical content, not an explicit title line

This left Stage 3 Blueprint generation without a stable title hint even when a title-like tactical header existed.

## Change

### 1. Constraint compiler

Updated [blueprint_constraint_compiler.py](C:/Users/User/Desktop/글도비/modules/domain/agents/blueprint_constraint_compiler.py).

- added `_extract_episode_title(...)`
- title resolution order:
  1. `episode_details[*]` title-like keys
  2. `tactical_doc` episode header
  3. top-level `arc_data["title"]`
- `_extract_episode_focus()` now returns `must_focus["arc_title"]`
- `compile_to_prompt()` now prints the title line when present

### 2. Blueprint prompt consumption

Updated [blueprint_ensemble.py](C:/Users/User/Desktop/글도비/modules/domain/agents/blueprint_ensemble.py).

- `_format_constraints(...)` now renders `[이번 화 제목]` when `must_focus.arc_title` exists

## Validation

Sequential shards only:

- `python -m pytest tests/test_tf10_episode_details.py -q` -> `19 passed`
- `python -m pytest tests/test_tier4_ensemble_caching.py -q` -> `12 passed`

Added regressions:

- tactical header title extraction
- fallback to top-level Arc title when header is generic
- constraint formatting includes explicit episode title

## Conclusion

`C1` is now closed as a bounded backend fix.

Remaining OPUS-derived backend live candidates should now be re-read as:

- `C4`
- `C8`
- `C10`
- plus policy-shaped `C3`, `C9`
