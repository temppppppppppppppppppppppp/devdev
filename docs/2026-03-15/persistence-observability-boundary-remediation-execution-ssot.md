# persistence-observability-boundary-remediation Execution SSOT

Date: 2026-03-15
Status: superseded-by-persistence-observability-finalization-and-sink-alignment
Successor: `docs/2026-03-15/persistence-observability-finalization-and-sink-alignment-remediation-execution-ssot.md`
Canonical Path: `docs/2026-03-15/persistence-observability-boundary-remediation-execution-ssot.md`
Temp Mirror Path: `none`
Queue Disposition: `historical cleanroom predecessor only; excluded from active queue`
Authority Class: `historical predecessor; do not use as live execution authority`
Commit State:
- Baseline Commit: `d2982aa2790f5ab81529f1e8d87cf6f6006f13c9`
- Baseline Dirty Summary: `dirty: unrelated investment/style/docs/log artifacts already present`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs: `docs/2026-03-15/codebase-global-cleanroom-source-only-3pass-audit.md`; `docs/2026-03-15/codebase-global-cleanroom-source-only-deep-global-survey.md`
Evidence Artifacts: `docs/2026-03-15/codebase-global-cleanroom-source-only-source-inventory.txt`; `docs/2026-03-15/codebase-global-cleanroom-source-only-surface-anchor-inventory.txt`; `docs/2026-03-15/codebase-global-cleanroom-source-only-side-effects.txt`
Side-Effect Coverage: covered

## Historical Supersession Notice

- This cleanroom execution SSOT is retained as a historical predecessor only.
- Live execution authority moved to `docs/2026-03-15/persistence-observability-finalization-and-sink-alignment-remediation-execution-ssot.md`, which was later realized and closed under the post-remediation roadmap.
- Any `execution-ready`, temp-path, or roadmap semantics below are historical snapshot content, not current queue state.

## 1. Intent
- Tighten the boundary between persistence, audit, session logging, and runtime-stage callers.
- Reduce change-risk caused by `DBManager` size and by the spread of write authority across app, services, and stage modules.

## 2. Baseline Facts
- Source sweep found 146 `load_anchor(...)`, 78 `save_anchor(...)`, 100 `.commit(...)`, 32 `.rollback(...)`, 87 `save_director_selection`, 76 `save_stage_attempt`, 19 `save_ui_event`, 28 `save_llm_call`, 90 `write_audit_summary`, and 77 `flush_audit_buffer` hits.
- `modules/core/db_manager.py` is one of the three largest active action-bearing runtime files.
- `AuditService` and `SessionLogger` are separate sink authorities, while stage modules and `main_a.py` still hold direct write seams.

## 3. Scope
Included:
- `modules/core/db_manager.py`
- `modules/core/services/audit_service.py`
- `modules/core/session_logger.py`
- `main_a.py`
- stage2/3/4 writers and agent DB-write call sites
- direct tests for DB, audit, bridge-quality summary, and safe-ops consistency

Excluded:
- desktop prompt transport except where sink contracts overlap
- historical logs and DB artifacts
- broad schema redesign beyond what the current write boundary requires

## 4. Pass 1. Inventory Summary
- Persistence authority is both centralized and leaked:
  - centralized in `DBManager`
  - leaked through many direct callers and direct commit/rollback touches
- Observability authority is split across audit summary, runtime audit JSONL, session JSONL, and console/UI event sinks.

## 5. Pass 2. Semantic Classification
- Class A: anchor/state persistence and transaction exposure
- Class B: attempt/selection/UI-event write surfaces
- Class C: audit/session proof surfaces and sink summaries

## 6. Side-Effect Map
- file writes / artifacts:
  - runtime_audit.jsonl, runtime_audit_summary.json, session JSONL, project DB, quality artifacts
- DB / schema / transaction boundaries:
  - primary focus; direct commit/rollback and caller responsibility must shrink
- JSONL / log / audit sinks:
  - primary focus; sink responsibilities must become easier to reason about
- console / UI / operator output:
  - indirect through audit and UI-event logging contracts
- rollback / recovery / retry:
  - direct focus because transaction ownership is part of the problem
- cache / global state:
  - runtime audit buffer and app-level service callbacks are relevant
- bootstrap fallback / config-env mutation:
  - not primary in this lane

## 7. Realization Architecture
- Separate responsibilities more clearly:
  - persistence service boundary
  - audit summary/proof boundary
  - session JSONL boundary
- Reduce direct caller knowledge of transaction handling.
- Keep read-only summary/proof paths explicit and testable.

## 8. Execution Tranches
1. Map direct write owners and isolate the highest-risk direct commit/rollback seams.
2. Reduce write-authority spread for attempts, selections, UI events, and audit summary generation.
3. Strengthen regression coverage around sink alignment and transaction ownership.

## 9. Acceptance Criteria
- Write ownership is more concentrated and more explicit.
- Transaction boundaries are not silently controlled from many unrelated caller sites.
- Audit and session sinks remain coherent under the new boundary.

## 10. Verification Plan
- targeted pytest for DB manager, audit service, bridge quality summary, safe-ops DB consistency, and affected stage modules
- `python -m py_compile` for touched Python files
- any necessary read-only smoke helpers after implementation

## 11. Guardrails
- Do not collapse all sink logic back into `main_a.py`.
- Do not change sink semantics without matching regression tests.

## 12. Temp Queue Notes
- temp status: pending
- cleanup condition: remove temp mirror only after realization is validated and closed
- roadmap dependency: third item in `docs/2026-03-15/codebase-global-cleanroom-source-only-execution-roadmap.md`

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document
