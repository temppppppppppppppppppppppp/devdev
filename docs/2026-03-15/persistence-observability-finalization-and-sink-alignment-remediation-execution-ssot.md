# persistence-observability-finalization-and-sink-alignment-remediation Execution SSOT

Date: 2026-03-15
Status: execution-ready
Canonical Path: `docs/2026-03-15/persistence-observability-finalization-and-sink-alignment-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/persistence-observability-finalization-and-sink-alignment-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `d2982aa2790f5ab81529f1e8d87cf6f6006f13c9`
- Baseline Dirty Summary: `dirty: unrelated investment/style/pdf/log artifacts already present`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs: `docs/2026-03-15/codebase-global-log-evidence-merged-3pass-audit.md`; `docs/2026-03-15/codebase-global-log-evidence-merged-deep-global-survey.md`
Evidence Artifacts: `docs/2026-03-15/codebase-global-log-evidence-merged-runtime-log-db-evidence.txt`; `docs/2026-03-15/codebase-global-log-evidence-merged-stage4-rationale-mismatch-table.json`; `docs/2026-03-15/codebase-global-log-evidence-merged-side-effects.txt`
Side-Effect Coverage: covered

## 1. Intent
- Move persistence and observability finalization to a true quiescent boundary.
- Eliminate writes that outlive DB/resource shutdown.
- Align summary, JSONL, DB, and Stage 4 rationale sinks under one explicit ownership and lineage contract.

## 2. Baseline Facts
- The secured run proves a late-write defect:
  - DB connection closes at log line `11934`
  - two `operator event sink failed` records occur at `11935` and `11937`
  - `save_llm_call failed (non-blocking)` occurs at `11945`
- `runtime_audit_summary.json` writes at `17:24:09`, but `pass_rate_monitor.json` updates at `17:24:25.933860` and `llm_io.jsonl` continues to `17:24:58`.
- `ui_events.jsonl=1448` while DB `ui_events=1446`, which is consistent with the two late post-close failures.
- Stage 4 rationale mismatches are real and localized to two attempt keys, not just a vague historical suspicion.
- Plain log token `20260315_144654` and structured sink session id `20260315_144741` are not normalized today.

## 3. Scope
Included:
- `main_a.py`
- `modules/core/db_manager.py`
- `modules/core/services/audit_service.py`
- `modules/core/session_logger.py`
- stage2/3/4 completion writers and relevant context callbacks
- `modules/core/failure_analyzer.py`
- targeted tests for audit summary, sink alignment, DB ownership, and shutdown behavior

Excluded:
- desktop reconnect and websocket transport semantics
- broad schema redesign outside the current sink-alignment defects
- source-text cleanup except when touched by this lane incidentally
- historical logs outside the selected secured run

## 4. Pass 1. Inventory Summary
- Finalization and write authority are still split across:
  - stage completion callbacks
  - `AuditService`
  - `SessionLogger`
  - `DBManager`
  - shutdown logic in `main_a.py`
- The secured run now proves that this is not only a structural cleanliness issue; it is a runtime durability defect.

## 5. Pass 2. Semantic Classification
- Class A: finalization ordering and quiescent-point defects
- Class B: post-close late writes and shutdown lifecycle leaks
- Class C: sink lineage and identity drift across plain log, JSONL, DB, and summary artifacts
- Class D: Stage 4 rationale-field normalization mismatches

## 6. Side-Effect Map
- file writes / artifacts:
  - runtime summary JSON, runtime audit JSONL, session JSONL, episode production JSONL, artifacts, project DB
- DB / schema / transaction boundaries:
  - primary focus
- JSONL / log / audit sinks:
  - primary focus
- console / UI / operator output:
  - indirect but important because shutdown telemetry and UI-event durability are part of the defect
- rollback / recovery / retry:
  - direct focus because shutdown timing and non-blocking failures are central
- cache / global state:
  - audit buffer, pending callbacks, app shutdown state
- bootstrap fallback / config-env mutation:
  - not primary

## 7. Realization Architecture
- Define one explicit shutdown/finalization contract:
  - stop accepting new writes
  - let in-flight callbacks quiesce or redirect safely
  - then finalize summary and close persistence resources
- Make sink lineage explicit:
  - plain log token
  - structured session id
  - DB rows
  - summary scope timestamp
- Close the Stage 4 rationale mismatch path with authoritative normalization and regression tests.

## 8. Execution Tranches
1. Rework shutdown and callback finalization so `save_ui_event` and `save_llm_call` cannot land after DB close.
2. Move summary/proof-digest generation behind a true quiescent point and lock its timestamp semantics.
3. Normalize run/session identity across plain log, JSONL, DB, and summary surfaces.
4. Close the Stage 4 `selection_reason` / `verdict_reason` mismatch path and cover it with a durable mismatch test.

## 9. Acceptance Criteria
- No post-close `save_ui_event` or `save_llm_call` failures on a bounded live run.
- Final summary timestamp is consistent with the durable state it claims to summarize.
- UI-event and related sink counts align or any deliberate exclusion is contract-explicit.
- Plain-log token and structured session identity are either unified or explicitly mappable by contract.
- Stage 4 rationale mismatch table closes to zero unexpected mismatches for the covered regression slice.

## 10. Verification Plan
- targeted pytest for DB manager, audit service, failure analyzer, summary generation, and shutdown/finalization behavior
- `python -m py_compile` for touched Python files
- bounded live rerun or read-only smoke to confirm sink counts and summary timing on real artifacts

## 11. Guardrails
- Do not paper over late writes by silently swallowing them without fixing lifecycle ownership.
- Do not claim whole-run correctness from summary files that still finalize too early.
- Do not widen this lane into desktop transport repair.

## 12. Temp Queue Notes
- temp status: pending
- cleanup condition: remove temp mirror only after realization is validated and closed
- roadmap dependency: second item in `docs/2026-03-15/codebase-global-log-evidence-merged-execution-roadmap.md`

## 13. Validation And Closure Hooks
- validator command: `python scripts/ops_validator.py --strict`
- bundle validator: `python scripts/validate_deep_global_survey_bundle.py --survey-doc docs/2026-03-15/codebase-global-log-evidence-merged-deep-global-survey.md --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document
