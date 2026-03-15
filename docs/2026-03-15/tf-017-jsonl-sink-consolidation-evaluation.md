# TF-017 JSONL Sink Consolidation Evaluation

Date: 2026-03-15
Status: final
Canonical Path: `docs/2026-03-15/tf-017-jsonl-sink-consolidation-evaluation.md`
Commit State:
- Baseline Commit: `bbb00a77c7356a32fe6358642cff0d3d445b7e8e`
- Baseline Dirty Summary: `dirty: active roadmap/temp docs, post-remediation bundle docs, runtime/operator and Stage 4 follow-up edits, projects/000 artifacts, and unrelated historical doc churn`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `TF-012 is implemented and TF-013 is already closed as a decision doc; this evaluation checks whether TF-017 needs a lock-unification successor lane or should remain documentation-only`
Parent Lane: `docs/2026-03-15/post-remediation-unqueued-survey-followups-execution-ssot.md`
TF Composition Source: `docs/2026-03-15/codebase-global-post-remediation-tf-composition.md`
Source Evidence:
- `docs/2026-03-15/codebase-global-post-remediation-deep-global-survey.md`
- `docs/2026-03-15/codebase-global-post-remediation-cross-cut-integrity-matrix.md`
- `docs/2026-03-15/codebase-global-post-remediation-evidence.txt`
- `docs/2026-03-15/codebase-global-live-merge-00_260315-post-run-merge-audit.md`
- `modules/core/jsonl_io.py`
- `modules/core/session_logger.py`
- `modules/core/services/audit_service.py`
- `modules/core/soft_failure.py`
- `modules/core/quality_dashboard.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_orchestrator.py`
- `tests/test_session_logger.py`
- `tests/test_audit_service.py`
- `tests/test_validation_orchestrator_soft_failure.py`
- `tests/test_failure_analyzer.py`
- `tests/test_stage4_orchestrator.py`

## 1. Intent
- Evaluate whether the workspace should consolidate JSONL sink lock strategy under one shared append policy for `TF-017`.
- Produce an authoritative, bounded decision instead of widening into opportunistic logging refactors.
- Preserve the already-closed persistence lane as the authority for shutdown ordering and sink-alignment fixes.

## 2. Current Sink And Lock Shapes
- `session/*.jsonl` (`llm_io`, `decisions`, `state_changes`, `ui_events`)
  - writer: `SessionLogger`
  - lock shape: per-instance `_write_lock`
  - notable behavior: rotation and shutdown disable semantics are coupled to the logger instance
- `runtime_audit.jsonl`
  - writer: `AuditService.flush_audit_buffer()`
  - lock shape: inline append, no shared file-lock helper
  - notable behavior: buffered flush ordered relative to summary/proof generation
- `episode_production.jsonl`
  - writer: Stage 4 paths via `append_jsonl_record()`
  - lock shape: process-wide `_JSONL_APPEND_LOCK` in `jsonl_io.py`
  - notable behavior: append-only helper used from multiple Stage 4 call sites
- `quality_metrics.jsonl`
  - writer: `QualityDashboard._save_record()`
  - lock shape: inline append, no dedicated file-lock around writes
  - notable behavior: singleton init lock exists, but it does not govern file appends
- `soft_failures.jsonl`
  - writer: `report_soft_failure()`
  - lock shape: inline append; `_WARN_LOCK` throttles warning emission, not file writes
  - notable behavior: this path must stay callable from degraded/failure contexts

## 3. Evidence Review

### 3.1 No Fresh Defect Tied To Lock Diversity
- The post-run merge audit records retained JSONL/DB sink alignment improvements on the completed slice.
- The same audit records prompt dedup as retained in `ui_events.jsonl`, not regressed.
- The live-run evidence manifest says observed JSONL sinks and DB excerpts remained UTF-8 legible.
- The stronger March 15 sink defects were stale summaries, late writes after close, and sink lineage drift, and those were already handled under the persistence/observability lane rather than by lock unification.

### 3.2 Writer Semantics Are Intentionally Different
- `SessionLogger` is not a plain append helper:
  - it rotates files
  - it owns enable/disable state
  - it protects category-specific writes with a per-instance lock
- `AuditService` is also not a plain append helper:
  - it writes from an in-memory buffer
  - it is ordered against pre-summary hooks and proof-digest generation
- `SoftFailure` is a degraded-path reporter:
  - it throttles warnings separately
  - it should remain callable even when higher-level services are unstable
- `episode_production.jsonl` is the closest fit for a shared append helper, and it already uses `jsonl_io.append_jsonl_record()`

### 3.3 Inventory Authority Is Not Yet Clean Enough
- The March 15 survey bundle describes `11` JSONL sinks, but the current code-visible writer map is less uniform than that summary suggests.
- `quality_metrics.jsonl` is written by `QualityDashboard`, not by `DataCollector`.
- The survey docs list `failure_analysis.jsonl` and `quality_dashboard.jsonl`, but current code search did not find active writer paths for those filenames.
- That means the first missing artifact is not a shared lock implementation. It is a tighter authoritative sink-ownership map.

### 3.4 Unification Risk
- Forcing one shared append helper across all JSONL sinks would couple:
  - rotated session telemetry
  - buffered audit flushes
  - degraded soft-failure reporting
  - Stage 4 append-only event logs
  - quality sidecar metrics
- That coupling would widen scope from "evaluate consolidation" into "normalize writer lifecycle, shutdown ordering, rotation policy, and degraded-path behavior".
- Current evidence does not justify that widening.

## 4. Verification
- `python -m pytest tests/test_session_logger.py -k "ui_event_creates_ui_events_jsonl"` -> `1 passed, 20 deselected`
- `python -m pytest tests/test_audit_service.py -k "runtime_audit"` -> `1 passed, 11 deselected`
- `python -m pytest tests/test_validation_orchestrator_soft_failure.py` -> `4 passed`
- `python -m pytest tests/test_failure_analyzer.py -k "sink_alignment_uses_selection_candidate_key_from_episode_production_when_available or failure_analyzer_summary_reports_soft_failures"` -> `2 passed, 11 deselected`
- `python -m pytest tests/test_stage4_orchestrator.py -k "runtime_audit_summary"` -> `5 passed, 51 deselected`
- Static line inspection confirmed:
  - `SessionLogger` per-instance write lock and rotation path
  - `AuditService` inline buffered append for `runtime_audit.jsonl`
  - `SoftFailure` inline append with warning throttling lock only
  - `QualityDashboard` inline append to `quality_metrics.jsonl`
  - Stage 4 append-helper usage for `episode_production.jsonl`

## 5. Decision
- Do not introduce global JSONL lock unification from TF-017.
- Retain the current split lock strategy for now.
- Treat TF-017 as complete through a bounded decision document, not code changes.

## 6. Rationale
- There is no fresh runtime evidence that lock diversity itself is causing JSONL corruption or sink misalignment.
- Different sinks have meaningfully different lifecycle and ownership requirements.
- A shared lock helper already exists where it fits naturally: append-only Stage 4 event rows.
- Before any future unification, the workspace needs a corrected authoritative sink inventory and owner map.

## 7. Reopen Triggers
- Reopen TF-017 only if one of the following becomes true:
  - fresh live evidence shows JSONL interleave/corruption that maps to lock strategy rather than shutdown timing or content encoding
  - multiple currently-inline writers begin writing concurrently enough to create measured contention
  - the sink inventory is first normalized so every active JSONL writer and lock owner is explicit
  - a future lane explicitly asks for a logging architecture refactor rather than a bounded evaluation

## 8. Operating Consequence
- The residual lane stays active, but TF-017 is satisfied by this decision doc.
- The next evaluation item should not assume upcoming JSONL lock unification.
