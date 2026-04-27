# Issue #59 Terminal 03 - Rationale Metadata Sink Alignment

Status: final after 3-pass adversarial audit  
Scope: selection/verdict/runtime/retry rationale fields and metadata propagation

## Finding Summary

Current Stage4 rationale metadata warnings are real, but not all represent the same defect class.

For session `20260427_070604`, direct analyzer counts are:

- `selection_reason_mismatches`: 4
- `verdict_reason_mismatches`: 4
- `runtime_advisory_mismatches`: 10
- `retry_directives_mismatches`: 4
- `rationale_metadata_missing`: 6
- `gate_repair_metadata_missing`: 4

The most important adversarial observation: some selection/verdict mismatches compare an original Director-selection reason with a later post-fix/finalized reason. That may be legitimate phase drift, but it is currently surfaced as a generic mismatch.

## Evidence

- `FailureAnalyzer._collect_sink_alignment_rationale_results` compares `selection_reason`, `verdict_reason`, `comparison_notes`, `selected_candidate_advisory`, `fix_scope`, `runtime_advisory`, and `retry_directives` across sinks.
- For Stage4, `director_selections` missing `runtime_advisory` and `retry_directives` is not automatically treated as a gap when companion sinks carry the runtime advisory. Existing tests cover that.
- Current examples show `retry_directives` missing in `stage_attempts` for attempts such as:
  - `s4:ep4:arc1:a1:20260427_070604`
  - `s4:ep5:arc2:a1:20260427_070604`
  - `s4:ep6:arc2:a1:20260427_070604`
- Current examples show `fix_pack_target_kind` missing in `session_decisions` for attempts such as:
  - `s4:ep4:arc1:a1:20260427_070604`
  - `s4:ep6:arc2:a1:20260427_070604`

## Risk / Gap

The analyzer currently has the evidence to tell us that fields differ, but not always why they differ. For Stage4, source phase matters:

- Director-original rationale
- post-select conflict rationale
- repair/fix-pack rationale
- settled/final attempt rationale
- retry-directive rationale

Without phase tagging, a legitimate post-fix reason update can look like an integrity mismatch.

## Suggested Contract Or Test

Add phase-aware rationale fields or normalization:

- `director_selection_reason`
- `settled_selection_reason`
- `director_verdict_reason`
- `settled_verdict_reason`
- `runtime_advisory_digest`
- `retry_directive_digest`
- `repair_scope_authority_note`

Test expectation: if `director_selections` keeps the original Director reason and `stage_attempts` keeps a post-fix settled reason, the summary should classify it as `phase_drift_warn`, not generic `selection_reason_mismatch`.

## Implementation Owner Surface

- `modules/core/failure_analyzer.py`
- `modules/core/stage4_canary_tools.py`
- `modules/core/db_manager.py`
- Stage4 persistence call sites that write `stage_attempts`, `session_decisions`, and `episode_production`

## Open Questions

- Is `stage_attempts.selection_reason` intended to be original Director selection reason or final settled selection reason?
- Should retry directives be stored in `stage_attempts` for every rejected Stage4 attempt, or only when retry is actually invoked?

## 3-Pass Save Audit

- Pass 1: Source comparison logic and current count evidence were checked.
- Pass 2: Possible false positives from phase drift were separated from missing metadata.
- Pass 3: Suggested contract preserves LLM/Director judgment ownership.

