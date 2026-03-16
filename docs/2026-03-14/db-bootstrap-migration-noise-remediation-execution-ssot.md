<!-- [완료] -->
# DB Bootstrap Migration Noise Remediation Execution SSOT

Date: 2026-03-14
Status: closed
Canonical Path: `docs/2026-03-14/db-bootstrap-migration-noise-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/db-bootstrap-migration-noise-remediation-execution-ssot.md` (removed on `2026-03-15`)
Commit State:
- Baseline Commit: `2a4d45a4896282d9cf96e67e8daff9dd0287ef4f`
- Baseline Dirty Summary: `dirty: 7 tracked, 3 untracked; hotspots: docs/implementation/*, 260314-print.txt`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `dirty realization landed in modules/core/{db_manager.py,services/audit_service.py}, main_a.py, tests/{test_audit_service.py,test_logging_phase2.py}`
Source Survey Docs:
- `docs/2026-03-14/codebase-global-rol-db-log-frontier-lag-3pass-audit.md`
- `docs/2026-03-14/codebase-global-rol-db-log-frontier-lag-reaudit.md`
Evidence Artifacts:
- `docs/2026-03-14/db-log-frontier-lag-reaudit-migration-noise.txt`
- `docs/2026-03-14/db-log-frontier-lag-reaudit-sink-alignment.json`
Side-Effect Coverage: covered
Primary References:
- `projects/00_20260314/logs/session_20260314_213845.log`
- `modules/core/db_manager.py`
- `modules/core/project_manager.py`
- `modules/core/services/audit_service.py`
- `modules/core/stage2_orchestrator.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_orchestrator.py`

## 1. Intent
- Stop repeated duplicate-column migration noise from polluting one session multiple times.
- Separate read-only audit-summary DB access from write-path schema boot behavior.

## 2. Baseline Facts
- The observed session contains `80` duplicate-column lines: `32` for `llm_calls` and `48` for `stage_attempts`.
- The same noise appears four times in one run:
  - project boot
  - `write_audit_summary("stage2_complete")`
  - `write_audit_summary("stage3_complete")`
  - `write_audit_summary("stage4_complete")`
- `DBManager` still uses exception-driven `ALTER TABLE ... ADD COLUMN` loops for compatibility migration in `modules/core/db_manager.py:536-552` and `modules/core/db_manager.py:593-612`.
- `AuditService._build_proof_digest(...)` instantiates a fresh `DBManager(db_path)` for summary generation.

## 3. Scope
Included:
- `modules/core/db_manager.py`
- `modules/core/services/audit_service.py`
- `modules/core/project_manager.py`
- DB bootstrap and proof-digest validation tests

Excluded:
- rationale normalization itself
- interactive menu contract changes
- unrelated SQLite table design changes

## 4. Pass 1. Inventory Summary
- duplicate-column clusters in one session: `4`
- affected compatibility loops: `2`
- re-entry paths to control: `4`
- impacted tables: `2` primary families plus silent legacy table checks

## 5. Pass 2. Semantic Classification
- Class A:
  - DB boot and compatibility loops in `DBManager`
  - proof-digest DB construction in `AuditService`
- Class B:
  - exact log cluster evidence from one captured session
- Class C:
  - reopened queue dependency from the runtime-audit track because stale-summary generation currently re-enters schema boot

## 6. Side-Effect Map
- file writes / artifacts:
  - session log noise is the primary operator-visible artifact
- DB / schema / transaction boundaries:
  - `llm_calls`
  - `stage_attempts`
  - compatibility migration helpers
- JSONL / log / audit sinks:
  - audit-summary log lines and runtime logs
- console / UI / operator output:
  - yes; duplicate-column debug lines currently leak into operator-visible logs
- rollback / recovery / retry:
  - schema compatibility behavior must remain safe for old DBs
- cache / global state:
  - optional schema-column cache may be introduced per connection
- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture
- Replace exception-driven compatibility loops with explicit column-existence prechecks using `PRAGMA table_info(...)`.
- Apply missing-column `ALTER TABLE` statements only for columns that are truly absent.
- Collapse migration logging to one bounded summary line per table family when a migration actually runs; emit nothing when the schema is already compatible.
- `AuditService` must stop opening a boot-migrating `DBManager` just to compute a proof digest. Use either:
  - the live project DB handle when available, or
  - a read-only SQLite connection path that does not execute compatibility boot loops.
- Preserve backward compatibility: if a genuinely old DB is missing columns, the migration still runs and commits those additions safely.

## 8. Execution Tranches
1. Introduce reusable column-introspection helpers and remove exception-driven compatibility loops.
2. Change proof-digest DB access so audit-summary generation no longer re-triggers full DB boot behavior.
3. Refresh tests and log assertions so repeated duplicate-column bursts cannot regress silently.

## 9. Acceptance Criteria
- The same session no longer emits repeated duplicate-column bursts at Stage 2/3/4 summary checkpoints.
- Project boot emits no per-column duplicate noise when the schema is already current.
- Audit-summary generation does not instantiate a path that reruns schema compatibility work on every summary.
- Older DBs with missing columns still receive the required compatibility additions safely.

## 10. Verification Plan
- Run targeted DB bootstrap tests around `DBManager`.
- Add or refresh tests that exercise `AuditService._build_proof_digest(...)` without duplicate migration logs.
- Reproduce a bounded proof-digest write path and confirm that no duplicate-column cluster reappears in the log.
- Re-check schema contents before and after the remediation on a fixture DB that is already current.

## 11. Guardrails
- Do not remove compatibility migrations entirely.
- Do not drop or rewrite existing columns as part of this item.
- Do not couple this item to unrelated persistence refactors outside the two affected table families and proof-digest entry path.

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
- `DBManager` now prechecks schema columns with `PRAGMA table_info(...)` before applying compatibility migrations for `llm_calls` and `stage_attempts`.
- Current schemas emit no duplicate-column debug noise; legacy schemas emit one bounded compatibility summary per affected table family when new columns are actually added.
- `AuditService` proof-digest generation no longer instantiates a fresh `DBManager(db_path)`; it uses the live project DB handle when available and otherwise opens a direct read-only SQLite analysis connection.
Verification Evidence:
- `python -m pytest tests/test_audit_service.py tests/test_logging_phase2.py -q` -> `26 passed`
- `python -m pytest tests/test_bridge_quality_summary.py tests/test_failure_analyzer.py tests/test_safe_ops_db_consistency.py -q` -> `24 passed`
- `python -m pytest tests/test_db_manager.py -q` -> `26 passed`
- `python scripts/ops_validator.py --strict` -> `PASS`
Residual Risk:
- other legacy compatibility migrations in `DBManager` still use older patterns outside this queue item; this closure only covers the `llm_calls` and `stage_attempts` families plus proof-digest re-entry
- the next queue item is `docs/2026-03-14/frontier-lag-nonstop-contract-remediation-execution-ssot.md`
