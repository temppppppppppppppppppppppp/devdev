# Runtime Audit Rationale Sink Alignment Remediation Execution SSOT

Date: 2026-03-14
Status: closed
Canonical Path: `docs/2026-03-14/runtime-audit-rationale-sink-alignment-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/runtime-audit-rationale-sink-alignment-remediation-execution-ssot.md` (removed on `2026-03-15`)
Commit State:
- Baseline Commit: `2a4d45a4896282d9cf96e67e8daff9dd0287ef4f`
- Baseline Dirty Summary: `dirty: 7 tracked, 3 untracked; hotspots: docs/implementation/*, 260314-print.txt`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `dirty realization landed in main_a.py, modules/core/{services/audit_service.py,db_manager.py,stage3_orchestrator.py,stage4_interview_round.py}, tests/{test_audit_service.py,test_db_manager.py,test_stage3_orchestrator.py,test_stage4_interview_round.py}`
Source Survey Docs:
- `docs/2026-03-14/codebase-global-rol-db-log-frontier-lag-3pass-audit.md`
- `docs/2026-03-14/codebase-global-rol-db-log-frontier-lag-reaudit.md`
Evidence Artifacts:
- `docs/2026-03-14/db-log-frontier-lag-reaudit-sink-alignment.json`
Side-Effect Coverage: covered
Primary References:
- `projects/00_20260314/logs/runtime_audit_summary.json`
- `projects/00_20260314/logs/pass_rate_monitor.json`
- `projects/00_20260314/logs/session/decisions.jsonl`
- `projects/00_20260314/logs/episode_production.jsonl`
- `projects/00_20260314/project_data.db`
- `modules/core/services/audit_service.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/db_manager.py`

## 1. Intent
- Restore one trustworthy sink-alignment story across DB, JSONL, and saved runtime summaries.
- Eliminate Stage 4 rationale drift and `ui_events` stage-label persistence failures under the same persistence contract.

## 2. Baseline Facts
- `runtime_audit_summary.json` was written at `2026-03-14 22:10:51`, while `pass_rate_monitor.json` was last updated at `2026-03-14T22:11:26.247293`.
- `AuditService` already calls `FailureAnalyzer.sink_alignment_summary(..., include_session_decisions=True)` when it builds the proof digest.
- The saved summary reports stale `pass_rate_monitor: 0` coverage for Stage 3 and Stage 4 because the summary predates the final monitor save.
- The live analyzer narrows the remaining Stage 4 issue to two `selection_reason` mismatches.
- `director_selections.selection_reason` is truncated to `200` chars in `modules/core/db_manager.py:2714`, while `stage_attempts.selection_reason` keeps `500` chars in `modules/core/db_manager.py:3190`.
- Patch flows prefix `director_selections.selection_reason` with `[patch|score=...]` in `modules/core/stage4_interview_round.py:2012-2017`.
- `ui_events` DB persistence currently tries `int(stage)` and therefore rejects string labels such as `stage0`, `stage3`, `stage4`, and `shutdown`.

## 3. Scope
Included:
- `modules/core/services/audit_service.py`
- `modules/core/db_manager.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage2_orchestrator.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_orchestrator.py`
- `main_a.py` shutdown monitor-save path
- sink-alignment, audit-service, and encoding-adjacent persistence tests

Excluded:
- broader encoding policy outside the sink contract
- menu `7` interactive contract changes
- DB compatibility-migration logging policy except where it blocks summary truth

## 4. Pass 1. Inventory Summary
- saved summary stages currently contradicted by live post-flush truth: `2`
- confirmed Stage 4 rationale mismatches after live recheck: `2`
- `ui_events` DB mirror failures in the observed session: `183`
- owning code sites for this track: `7`

## 5. Pass 2. Semantic Classification
- Class A:
  - summary write order, rationale persistence, and `ui_events` stage coercion in live code
- Class B:
  - saved summary versus post-flush analyzer output
  - attempt-key rationale samples across DB and JSONL sinks
- Class C:
  - predecessor docs that assumed the operator-event substrate had already converged

## 6. Side-Effect Map
- file writes / artifacts:
  - `runtime_audit_summary.json`
  - `pass_rate_monitor.json`
  - `session/decisions.jsonl`
  - `episode_production.jsonl`
- DB / schema / transaction boundaries:
  - `stage_attempts`
  - `director_selections`
  - `ui_events`
- JSONL / log / audit sinks:
  - summary digest and session decision sinks
- console / UI / operator output:
  - warning/debug noise will change because `ui_events` DB mirror failures should disappear
- rollback / recovery / retry:
  - patch provenance and retry advisory metadata must remain available after rationale normalization
- cache / global state:
  - in-memory pass-rate monitor state
- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture
- `selection_reason` is the canonical human-readable director rationale field. It must match across `stage_attempts`, `director_selections`, `session_decisions`, and `episode_production`.
- Patch provenance must move out of `selection_reason`. Persist it instead under `director_selections.advisory_warnings.patch_context` while keeping `selection_reason` and `verdict_reason` human-readable and unprefixed.
- Align rationale truncation to one cap. Use the `500`-char ceiling already used by `stage_attempts`; do not keep a shorter `director_selections` cap.
- Stage-complete summary writes must happen only after the pass-rate monitor has been flushed or saved for the same logical checkpoint. The saved `runtime_audit_summary.json` must not predate the final monitor state it claims to summarize.
- Keep `include_session_decisions=True` as the proof-digest join policy.
- `ui_events.stage` remains a nullable integer field. Normalize known string labels before DB insert:
  - `stage0 -> 0`
  - `stage2 -> 2`
  - `stage3 -> 3`
  - `stage4 -> 4`
  - `shutdown -> NULL`
- Preserve the original non-numeric label under `meta.stage_label` when normalization changes the DB field.

## 8. Execution Tranches
1. Fix summary-write ordering so saved proof digests are produced after the relevant monitor state is durable.
2. Normalize rationale persistence: unprefixed `selection_reason`, 500-char cap alignment, and patch provenance migration to advisory metadata.
3. Normalize `ui_events` stage labels and remove current DB mirror failures.

## 9. Acceptance Criteria
- A fresh saved `runtime_audit_summary.json` matches the live analyzer for the same sink state and no longer reports stale `pass_rate_monitor: 0` coverage.
- Stage 4 rationale alignment no longer produces mismatches caused by patch prefixing or 200-char truncation.
- `ui_events` DB mirroring no longer emits `invalid literal for int()` stage-label failures for `stage0`, `stage3`, `stage4`, or `shutdown`.
- Patch provenance remains queryable through advisory metadata even after it is removed from `selection_reason`.

## 10. Verification Plan
- Run `tests/test_failure_analyzer.py`.
- Run `tests/test_audit_service.py`.
- Run `tests/test_safe_ops_db_consistency.py`.
- Add targeted coverage for:
  - summary-write ordering versus monitor flush
  - rationale equality across DB and JSONL sinks
  - `ui_events` stage-label normalization
- Recompute sink alignment on a bounded fixture project and confirm the saved summary matches the live analyzer result.

## 11. Guardrails
- Do not remove patch provenance entirely; move it out of the primary rationale field instead.
- Do not weaken the proof digest by dropping session decisions from the join.
- Do not change the authoritative sink set without updating the audit contract docs and tests.

## 12. Temp Queue Notes
- temp status: closed
- cleanup condition: satisfied on `2026-03-15`; temp mirror removed after canonical closure and roadmap sync
- roadmap dependency: `docs/2026-03-14/codebase-global-rol-db-log-frontier-lag-execution-roadmap.md`

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run this document through the 3-pass audit and reconfirm 95% confidence against the live workspace before patching code

## 14. Closure Note
Closure Date: `2026-03-15`
Closure Status: `closed`
Realization Summary:
- `AuditService` now runs a pre-summary hook so saved proof digests are built after pass-rate monitor state is flushed.
- `main_a.py` now provides a non-operator-noise pass-rate save hook for stage summary writes.
- `director_selections.selection_reason` and Stage 3 director-selection payloads now keep the same `500`-char cap as `stage_attempts`.
- Stage 4 patch retries now keep `selection_reason` human-readable and move patch provenance to `advisory_warnings.patch_context`.
- `ui_events` now normalizes string stage labels into DB-safe integers and preserves the original label under `meta.stage_label`.
Verification Evidence:
- `python -m pytest tests/test_audit_service.py tests/test_db_manager.py tests/test_stage3_orchestrator.py tests/test_stage4_interview_round.py -q` -> `181 passed`
- `python -m pytest tests/test_bridge_quality_summary.py tests/test_failure_analyzer.py tests/test_safe_ops_db_consistency.py -q` -> `24 passed`
- `python scripts/ops_validator.py --strict` -> `PASS`
Residual Risk:
- bounded fixture and unit coverage are strong, but the historical `projects/00_20260314/` runtime bundle was not replayed in this implementation turn
- the next queue item remains `docs/2026-03-14/db-bootstrap-migration-noise-remediation-execution-ssot.md`
