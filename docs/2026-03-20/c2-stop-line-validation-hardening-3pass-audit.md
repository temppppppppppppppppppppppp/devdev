# C2 Stop-Line Validation Hardening (3-Pass Audit)

Date: 2026-03-20
Mode: system-track bounded backend hardening
Confidence: 0.95

## Scope

- Source OPUS item:
  - `docs/2026-03-18/OPUS/ssot_execution/s8-0_260318-project-deepdive-execution.md`
- Live targets:
  - `modules/domain/agents/blueprint_constraint_compiler.py`
  - `modules/domain/agents/unified_blueprint_validator.py`
  - `tests/test_tf10_episode_details.py`
  - `tests/test_legacy_reentry_reaudit.py`

## Re-check Summary

The original OPUS wording for `C2` was overstated.

- `stop_line` extraction already existed in:
  - `modules/domain/agents/blueprint_constraint_compiler.py`
- Python-side stop-line validation already existed in:
  - `modules/domain/agents/unified_blueprint_validator.py`

The real issue was not "validation absent".
The real issue was that the live validator only checked whether `stop_content[:30]` appeared as a direct substring inside `integrated_scenario`.

That was too weak for next-episode leakage cases where:

- wording was slightly reordered
- the same event was paraphrased
- the current blueprint repeated most of the next-episode clause without copying the exact leading 30 characters

## Patch

Bounded hardening applied in `modules/domain/agents/unified_blueprint_validator.py`:

- added `_extract_stop_line_clauses(...)`
- added `_extract_significant_stop_tokens(...)`
- added `_detect_stop_line_violation(...)`

New behavior:

- still rejects clear exact clause leakage
- also rejects high-coverage stop-line token overlap
  - at least 3 significant overlapping tokens
  - overlap ratio at least 0.75
- avoids over-triggering on light shared setup words by filtering common tokens such as:
  - `다음`, `장면`, `주인공`, `계획`, `상황`

This remains a bounded Python-side hardening patch. It does not change Director sovereignty.

## Regression Coverage

- `tests/test_legacy_reentry_reaudit.py`
  - `test_unified_blueprint_validator_rejects_stop_line_clause_leak`
  - `test_unified_blueprint_validator_allows_light_stop_line_overlap_without_leak`
- `tests/test_tf10_episode_details.py`
  - existing stop-line extraction tests kept passing

## Validation

- `python -m pytest tests/test_legacy_reentry_reaudit.py -k "stop_line or unified_blueprint_validator" -q`
  - `3 passed, 8 deselected`
- `python -m pytest tests/test_director_modules.py -k "compare_and_select_pass_with_warning_sets_quality_risk or compare_and_select_multi_candidate_pass_with_fix_preserves_advisory or compare_and_select_single_candidate_reject_short" -q`
  - `3 passed, 96 deselected`
- `python -m pytest tests/test_tf10_episode_details.py -k "extract_stop_line" -q`
  - `2 passed, 17 deselected`

## Decision

- OPUS wording "stop-line validation missing" is stale
- the remaining live weakness was real
- that bounded weakness is now hardened and can be treated as closed

## Conclusion

`C2` is no longer an open bounded backend item.

The codebase already had stop-line extraction and a basic validator. This pass upgraded the validator from fragile prefix-substring matching to a more usable clause/token leakage detector without changing the broader Stage 3 governance model.
