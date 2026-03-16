# Project 0_260316 Threat Carry-Over Delta Audit

Date: 2026-03-16
Status: completed canonical
Canonical Path: `docs/2026-03-16/project-0-260316-threat-carryover-delta-audit.md`
Scope: `project-0-260316` Stage 4 threat carry-over substrate closure audit after the bounded `active_pressure_vectors` implementation
Commit State:
- Baseline Commit: `3167fb2039ae54266d40f5d00d21b63f722a90de`
- Baseline Dirty Summary: `dirty: 1 tracked; hotspot: projects/test_project/logs/episode_production.jsonl`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Canonical Docs:
- `docs/2026-03-16/project-0-260316-execution-ssot.md`
- `docs/2026-03-16/project-0-260316-stage4-continuity-and-codebase-survey.md`

## Intent

- confirm whether `relationship/threat delta durable persistence` was fully closed in live code
- separate `relationship persistence` from `threat carry-over` so queue closure does not outrun evidence
- verify whether the remaining bounded tranche is now actually closed in live code

## Pass 1: Inventory

Runtime surfaces inspected:
- `modules/core/stage4_post_processor.py`
- `modules/core/world_state.py`
- `modules/core/fact_ledger.py`
- `modules/core/stage4_context_builder.py`
- `modules/validation/continuity_validator.py`
- `tests/test_stage4_post_processor.py`
- `tests/test_validation.py`

Findings:
- `stage4_post_processor` now derives `active_pressure_vectors` from `ending_hook` / `cliffhanger` / `expected_ending`, normalizes cue terms, and persists them through `actual_truth`, `state_log_data`, and `bible_delta`
- `world_state` now has a persisted `active_pressure_vectors` surface, replaces it per-episode, replays it on rollback, and exposes it in the canonical summary as `[지속 압박/위협]`
- `stage4_context_builder` now keeps `[지속 압박/위협]` in the condensed world-state summary path used alongside Continuity Packet injection
- `stage4_interview_round` now merges persisted `active_pressure_vectors` into `prev_hud` resolution even when `manuscript.hud_snapshot` is the winning source
- `continuity_validator` now emits `threat_carryover_drift` warnings when the opening drops all persisted pressure cues
- targeted Stage 4 persistence/runtime tests now cover producer, sink, summary, prev_hud consumer, and validator warning behavior

Pass 1 result:
- `relationship persistence` is a real implemented path
- `threat carry-over` is now a real implemented path via `active_pressure_vectors`

## Pass 2: Semantic Classification

Fact:
- the prior queue re-open correctly separated `relationship_changes` from `threat carry-over`, and the missing substrate is now implemented as `active_pressure_vectors`

Fact:
- this tranche was not a validator-threshold tweak; it required a new persisted continuity surface

Inference:
- `active_pressure_vectors` was the correct bounded canonical surface because it fit the existing Stage 4 continuity contract without forcing a new DB schema

Decision:
- close the project-specific queue item
- keep `relationship persistence` closed
- mark `threat carry-over` closed for `project-0-260316`

## Pass 3: Execution Shape

Closure shape:
1. canonical threat surface: `active_pressure_vectors`
2. persistence: `actual_truth` → `state_log_data` → `bible_delta/state_changes`
3. canonical sink: `world_state.update_from_state_changes()`
4. Stage 4 consumers: condensed `stage4_context_builder` summary + `stage4_interview_round` prev_hud merge
5. validator/test coverage: `threat_carryover_drift` warning plus targeted regression suites

Non-goals for this tranche:
- do not reopen the landed `relationship_changes` wire fix
- do not reopen `inventory_count_drift` or `fixable_firewall`
- do not claim `threat` closure from prose-only evidence

## 3-Pass Audit

- Pass 1 Structure and Scope: completed
- Pass 2 Evidence and Consistency: completed
- Pass 3 Execution and Readability: completed
- Estimated Confidence: `96%`

## Conclusion

- `relationship persistence`: closed after the state-log gate fix
- `threat carry-over`: closed via `active_pressure_vectors` persistence, Stage 4 re-injection, and warning-only continuity validation
