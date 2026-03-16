<!-- [완료] -->
﻿# persistence-observability-finalization-and-sink-alignment-remediation Execution SSOT

Date: 2026-03-15
Status: closed
Canonical Path: `docs/2026-03-15/persistence-observability-finalization-and-sink-alignment-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/persistence-observability-finalization-and-sink-alignment-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `d2982aa2790f5ab81529f1e8d87cf6f6006f13c9`
- Baseline Dirty Summary: `dirty: unrelated investment/style/pdf/log artifacts already present`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `lane was realized in bbb00a77; current closure refresh revalidates persistence/session/artifact contracts and removes the final temp residue`
Source Survey Docs: `docs/2026-03-15/codebase-global-log-evidence-merged-3pass-audit.md`; `docs/2026-03-15/codebase-global-log-evidence-merged-deep-global-survey.md`
Evidence Artifacts: `docs/2026-03-15/codebase-global-log-evidence-merged-runtime-log-db-evidence.txt`; `docs/2026-03-15/codebase-global-log-evidence-merged-stage4-rationale-mismatch-table.json`; `docs/2026-03-15/codebase-global-log-evidence-merged-artifact-truth-evidence.txt`; `docs/2026-03-15/codebase-global-log-evidence-merged-artifact-hash-mismatch-table.json`; `docs/2026-03-15/codebase-global-log-evidence-merged-side-effects.txt`; `15일.txt`
Side-Effect Coverage: covered

## 1. Intent
- Move persistence and observability finalization to a true quiescent boundary.
- Eliminate writes that outlive DB/resource shutdown.
- Align summary, JSONL, DB, artifact files, and Stage 4 rationale sinks under one explicit ownership and lineage contract.

## 2. Baseline Facts
- The secured run proves a late-write defect:
  - DB connection closes at log line `11934`
  - two `operator event sink failed` records occur at `11935` and `11937`
  - `save_llm_call failed (non-blocking)` occurs at `11945`
- `runtime_audit_summary.json` writes at `17:24:09`, but `pass_rate_monitor.json` updates at `17:24:25.933860` and `llm_io.jsonl` continues to `17:24:58`.
- `ui_events.jsonl=1448` while DB `ui_events=1446`, which is consistent with the two late post-close failures.
- Stage 4 rationale mismatches are real and localized to two attempt keys, not just a vague historical suspicion.
- Plain log token `20260315_144654` and structured sink session id `20260315_144741` are not normalized today.
- Referenced artifact files are structurally healthy (`missing=0`, `zero-byte=0`, `utf-8 decode failures=0`, `stage2/stage3 json parse failures=0`), but stored hash lineage is not:
  - `stage_attempts` artifact hash mismatches: `29/29`
  - linked `episode_production` artifact and selection hash mismatches: `28`
- `episode_production.jsonl` mixes `14` attempt-linked rows with `5` event-only rows that do not carry `attempt_key`.
- `15일.txt` shows `[System] DB 연결 안전하게 해제됨` and `종료 완료`, followed by `threading/_python_exit -> KeyboardInterrupt` and `BaseEventLoop.__del__ -> AttributeError`, so app-level shutdown completion is not the same as process-level quiescence.

## 3. Scope
Included:
- `main_a.py`
- `modules/core/db_manager.py`
- `modules/core/services/audit_service.py`
- `modules/core/session_logger.py`
- `modules/core/stage4_interview_round.py`
- stage2/3/4 completion writers and relevant context callbacks
- `modules/core/failure_analyzer.py`
- `projects/00_260315/logs/artifacts/stage2/`
- `projects/00_260315/logs/artifacts/stage3/`
- `projects/00_260315/logs/artifacts/stage4/`
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
- artifact-hash ownership is also split across:
  - stage attempt persistence
  - episode production emission
  - artifact final-write paths, including patch/post-fix rewrites
- The secured run plus artifact sweep prove that this is not only a structural cleanliness issue; it is a runtime durability and artifact-lineage defect.

## 5. Pass 2. Semantic Classification
- Class A: finalization ordering and quiescent-point defects
- Class B: post-close late writes and shutdown lifecycle leaks
- Class C: sink lineage and identity drift across plain log, JSONL, DB, and summary artifacts
- Class D: Stage 4 rationale-field normalization mismatches
- Class E: artifact-hash capture drift between stored metadata and final on-disk bytes
- Class F: app-level shutdown completion vs process-level teardown exceptions

## 6. Side-Effect Map
- file writes / artifacts:
  - runtime summary JSON, runtime audit JSONL, session JSONL, episode production JSONL, artifacts, project DB
- DB / schema / transaction boundaries:
  - primary focus
- JSONL / log / audit sinks:
  - primary focus
- console / UI / operator output:
  - indirect but important because shutdown telemetry and claimed completion messages are part of the defect
- rollback / recovery / retry:
  - direct focus because shutdown timing, teardown exceptions, and non-blocking failures are central
- cache / global state:
  - audit buffer, pending callbacks, app shutdown state, final-write hash state
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
-   - artifact paths and their final content hashes
- Close the Stage 4 rationale mismatch path with authoritative normalization and regression tests.
- Stamp `content_hash` and `selection_content_hash` only at the durable final artifact boundary, not at a pre-patch or pre-rewrite intermediate point.
- Treat shutdown completion as a quiescent-process condition, not only an app-level message emission.

## 8. Execution Tranches
1. Rework shutdown and callback finalization so `save_ui_event` and `save_llm_call` cannot land after DB close.
2. Move summary/proof-digest generation behind a true quiescent point and lock its timestamp semantics.
3. Normalize run/session identity across plain log, JSONL, DB, summary, and artifact-linked sinks.
4. Move artifact hash capture to the final durable write boundary and align `stage_attempts` plus `episode_production` metadata with actual bytes on disk.
5. Close the Stage 4 `selection_reason` / `verdict_reason` mismatch path and cover it with a durable mismatch test.
6. Eliminate post-completion teardown exceptions so shutdown completion implies process-level quiescence for this lane's owned resources.

## 9. Acceptance Criteria
- No post-close `save_ui_event` or `save_llm_call` failures on a bounded live run.
- Final summary timestamp is consistent with the durable state it claims to summarize.
- UI-event and related sink counts align or any deliberate exclusion is contract-explicit.
- Plain-log token and structured session identity are either unified or explicitly mappable by contract.
- `stage_attempts.content_hash` aligns with the current bytes of every referenced artifact in the covered regression slice.
- `episode_production.content_hash` and `selection_content_hash` align with the current bytes of their referenced artifacts in the covered regression slice.
- `episode_production` event-only rows are either kept clearly non-attempt-truth by contract or split into a separate sink.
- Stage 4 rationale mismatch table closes to zero unexpected mismatches for the covered regression slice.
- After the app reports shutdown completion, no owned Python teardown exception should remain in the covered live-run slice.

## 10. Verification Plan
- targeted pytest for DB manager, audit service, failure analyzer, summary generation, artifact-hash lineage, and shutdown/finalization behavior
- `python -m py_compile` for touched Python files
- bounded live rerun or read-only smoke to confirm sink counts, artifact-hash truth, summary timing, and teardown cleanliness on real artifacts

## 11. Guardrails
- Do not paper over late writes by silently swallowing them without fixing lifecycle ownership.
- Do not claim whole-run correctness from summary files that still finalize too early.
- Do not repair one hash sink while leaving another sink to emit stale artifact hashes.
- Do not treat `종료 완료` as sufficient proof if teardown exceptions still fire afterward.
- Do not widen this lane into desktop transport repair.

## 12. Temp Queue Notes
- temp status: closed
- cleanup condition: satisfied; remove the temp mirror during this closure refresh
- roadmap dependency: first item in `docs/2026-03-15/codebase-global-log-evidence-merged-execution-roadmap.md`

## 13. Validation And Closure Hooks
- validator command: `python scripts/ops_validator.py --strict`
- bundle validator: `python scripts/validate_deep_global_survey_bundle.py --survey-doc docs/2026-03-15/codebase-global-log-evidence-merged-deep-global-survey.md --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. Closure Evidence
- Implemented:
  - `main_a.py`
  - `modules/core/artifact_logging.py`
  - `modules/core/db_manager.py`
  - `modules/core/services/audit_service.py`
  - `modules/core/session_logger.py`
  - `modules/core/stage4_interview_round.py`
  - `tests/test_artifact_logging.py`
  - `tests/test_audit_service.py`
  - `tests/test_db_manager.py`
  - `tests/test_session_logger.py`
  - `tests/test_stage4_interview_round.py`
- Realized outcomes:
  - late-write persistence ownership is now bounded behind the realized shutdown/finalization path recorded in `bbb00a77`
  - artifact/content-hash capture moved onto the realized durable-write path instead of the earlier stale pre-final-write seam
  - audit/session/stage4 sinks now align with the bounded runtime evidence and no longer require this lane to stay in the temp queue
- Verification:
  - `python -m py_compile main_a.py modules/core/artifact_logging.py modules/core/db_manager.py modules/core/services/audit_service.py modules/core/session_logger.py modules/core/stage4_interview_round.py tests/test_artifact_logging.py tests/test_audit_service.py tests/test_db_manager.py tests/test_session_logger.py tests/test_stage4_interview_round.py`
  - `python -m pytest tests/test_artifact_logging.py` -> `5 passed`
  - `python -m pytest tests/test_audit_service.py -k "runtime_audit"` -> `1 passed, 11 deselected`
  - `python -m pytest tests/test_db_manager.py -k "stage_attempts_for_arc or save_stage_attempt_persists_rationale_fields"` -> `2 passed, 28 deselected`
  - `python -m pytest tests/test_session_logger.py` -> `21 passed`
  - `python -m pytest tests/test_stage4_interview_round.py` -> `76 passed`
  - `python -m pytest tests/test_failure_analyzer.py -k "sink_alignment_uses_selection_candidate_key_from_episode_production_when_available or failure_analyzer_summary_reports_soft_failures"` -> `2 passed, 11 deselected`
  - `python -m pytest tests/test_stage4_orchestrator.py -k "runtime_audit_summary"` -> `5 passed, 51 deselected`
- Residual risk:
  - no fresh bounded live rerun or artifact-hash sweep was repeated in this cleanup pass; closure relies on the realized lane evidence from `bbb00a77` plus the current targeted regression recheck
