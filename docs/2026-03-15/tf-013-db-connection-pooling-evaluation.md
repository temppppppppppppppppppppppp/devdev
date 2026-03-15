# TF-013 DB Connection Pooling Evaluation

Date: 2026-03-15
Status: final
Canonical Path: `docs/2026-03-15/tf-013-db-connection-pooling-evaluation.md`
Commit State:
- Baseline Commit: `bbb00a77c7356a32fe6358642cff0d3d445b7e8e`
- Baseline Dirty Summary: `dirty: active roadmap/temp docs, post-remediation bundle docs, runtime/operator and Stage 4 follow-up edits, projects/000 artifacts, and unrelated historical doc churn`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `TF-012 is already landed inside the residual lane; this evaluation checks whether TF-013 should remain a decision doc or escalate into a successor execution SSOT`
Parent Lane: `docs/2026-03-15/post-remediation-unqueued-survey-followups-execution-ssot.md`
TF Composition Source: `docs/2026-03-15/codebase-global-post-remediation-tf-composition.md`
Source Evidence:
- `docs/2026-03-15/codebase-global-post-remediation-deep-global-survey.md`
- `docs/2026-03-15/codebase-global-post-remediation-evidence.txt`
- `docs/2026-03-15/codebase-global-live-merge-00_260315-post-run-merge-audit.md`
- `modules/core/db_manager.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/services/audit_service.py`
- `modules/core/stage4_context_builder.py`
- `tests/test_integrity.py`

## 1. Intent
- Evaluate whether the current SQLite access model should be replaced with a small connection pool for `TF-013`.
- Keep the outcome bounded to one decision: either retain the current model or spawn a successor execution SSOT for pooling implementation.
- Avoid opportunistic persistence rewrites while the residual lane is still active.

## 2. Current Model
- `DBManager` owns one shared SQLite connection created with `check_same_thread=False` and protects operations with `threading.RLock()`.
- The shared connection is configured with `PRAGMA journal_mode=WAL`, `synchronous=NORMAL`, and a `30.0` second timeout.
- Transaction boundaries rely on `conn.in_transaction` checks plus explicit commit/rollback handling rather than a pool-level transaction coordinator.
- A separate read-only seam already exists for proof/audit workloads: `AuditService._resolve_proof_digest_db()` opens a dedicated `mode=ro` connection.

## 3. Evidence Review

### 3.1 Runtime Contention Evidence
- The current post-run merge audit explicitly states there was no current-run traceback, `closed database`, duplicate-column burst, or crash dump for that session.
- A direct search for `database is locked` across `projects/00_260315/logs` and `docs/2026-03-15` returned `0` matches.
- The stronger March 15 persistence defect that did exist was `closed database` after shutdown timing, and that defect was already handled under the persistence/observability lane rather than by introducing a pool.

### 3.2 Read-Heavy Advisory Path Reality
- The headline reason for pooling in TF-013 was "read-heavy advisory queries vs write path".
- The actual Stage 4 DB advisory calls:
  - `_build_db_pacing_advisory()`
  - `_build_db_satisfaction_advisory()`
  - `_build_db_reveals_advisory()`
  - `_build_db_reflexion_advisory()`
  are assembled in one serial `for` loop after the main Director feedback block.
- The 8-way advisory `ThreadPoolExecutor` does not run these DB advisory queries; it runs other advisory analyzers.
- Result: the current code does not demonstrate the specific parallel DB-read pressure that the original pooling hypothesis was meant to relieve.

### 3.3 Existing Escape Hatch For Parallel Reads
- The workspace already has one scoped answer for concurrent proof reads: `AuditService` opens a separate `mode=ro` SQLite connection on demand.
- That is materially safer than retrofitting a general-purpose pool into the live runtime path because it preserves the main write connection and avoids a new transaction-sharing contract.

### 3.4 Pooling Migration Risk
- A workspace-wide sweep found `43` direct `.conn.execute/.conn.cursor/.conn.in_transaction` call sites outside `db_manager.py`, spread across `8` files.
- Those bypasses mean the codebase is not yet cleanly abstracted around a single repository or connection-acquisition contract.
- A pool would therefore require more than swapping the constructor:
  - transaction semantics would need to be redefined
  - direct `.conn.*` users would need refactoring first
  - test expectations around `RLock`, nested transactions, and close behavior would need re-audit

## 4. Verification
- `python -m pytest tests/test_integrity.py -k concurrent_episode_number_generation` -> `1 passed, 21 deselected`
- `rg -n "database is locked" projects/00_260315/logs docs/2026-03-15 -g "*.log" -g "*.txt" -g "*.md"` -> `0 matches`
- Static line inspection confirmed:
  - single shared connection + `RLock` + WAL in `modules/core/db_manager.py`
  - read-only proof seam in `modules/core/services/audit_service.py`
  - serial DB advisory assembly outside the 8-way advisory executor in `modules/core/stage4_interview_round.py`
  - direct `.conn.*` bypass count across non-DBManager modules

## 5. Decision
- Retain the current single-connection model for now.
- Do not create a successor execution SSOT for general-purpose DB pooling from TF-013.
- Treat TF-013 as complete through a bounded decision document rather than code changes.

## 6. Rationale
- No authoritative live evidence currently shows lock contention that pooling would solve.
- The most plausible "read-heavy advisory" pressure is not actually running inside the current advisory thread pool.
- The codebase already has a narrower and safer pattern for isolated reads via the read-only audit/proof connection.
- The current abstraction surface is too leaky for a low-risk pooling rollout because direct `.conn.*` access still exists in multiple non-DBManager modules.

## 7. Reopen Triggers
- Reopen TF-013 only if one of the following becomes true:
  - fresh live evidence shows `database is locked` or equivalent contention under normal runtime load
  - DB-heavy advisory queries are moved into real parallel execution against the same live database path
  - direct `.conn.*` bypasses are first collapsed behind an explicit repository or connection-acquisition contract
  - a new lane explicitly asks for a persistence architecture refactor rather than a bounded evaluation

## 8. Operating Consequence
- The residual lane stays active, but TF-013 is satisfied by this decision doc.
- The next residual evaluation item should proceed without assuming a future pool implementation.
