# Post-Remediation TF Composition

| Field | Value |
|-------|-------|
| **Baseline** | `bbb00a77` |
| **Date** | 2026-03-15 |
| **Source survey** | codebase-global-post-remediation-deep-global-survey.md |
| **Total TF items** | 14 |

---

## Severity / Priority Definitions

| Severity | Definition |
|----------|-----------|
| **CRITICAL** | Data loss, silent corruption, runtime crash risk |
| **IMPORTANT** | Operator confusion, contract violation, regression gap |
| **INSIGHT** | Code hygiene, modernization, structural improvement |

| Priority | Definition |
|----------|-----------|
| **P0** | Must resolve before next production run |
| **P1** | Resolve in next remediation cycle |
| **P2** | Resolve when touching related code |
| **P3** | Backlog |

---

## Lane 1: Persistence/Observability — STATUS: COMPLETE

All Lane 1 TFs from the original plan have been implemented in `bbb00a77`:

| Original TF | Item | Status | Evidence |
|-------------|------|--------|----------|
| TF-001 | Late-write defense (begin_shutdown) | ✅ Done | db_manager.py L1118, session_logger.py L69 |
| TF-002 | Audit summary timing (quiescent-point) | ✅ Done | audit_service.py L269 pre-hook |
| TF-003 | Artifact hash integrity | ✅ Done | artifact_logging.py L53 persisted_bytes |
| TF-004 | Session identity reconciliation | ✅ Done | audit_service.py L173 dual lineage |
| TF-005 | Shutdown sequence ordering | ✅ Done | main_a.py L3003-3018 |
| TF-006 | Rationale mismatch sync | ✅ Done | stage4_interview_round.py L2138, L2297 |

**No remaining Lane 1 items.**

---

## Active TF Items (14 total)

### CRITICAL / P0 — None

No CRITICAL/P0 items remain. Lane 1 implementation resolved all data-integrity risks.

---

### IMPORTANT / P1 (3 items)

#### TF-007: C-05 Desktop Runtime Validation

| Field | Value |
|-------|-------|
| **Severity** | IMPORTANT |
| **Priority** | P1 |
| **Lane** | 3 (Desktop/Control-Plane) |
| **Description** | Backend-front readiness separation has contract but no runtime proof |
| **Action** | Execute desktop session with health check logging to validate command-path vs websocket-path decoupling |
| **Evidence sources** | C-05 contradiction (PARTIALLY RESOLVED), backend-front-control-plane-connectivity-hardening-remediation-execution-ssot.md |
| **Acceptance** | Health check logs show independent command and websocket liveness |

#### TF-008: U-01 Desktop Test Coverage

| Field | Value |
|-------|-------|
| **Severity** | IMPORTANT |
| **Priority** | P1 |
| **Lane** | 3 (Desktop/Control-Plane) |
| **Description** | 0 test files in geuldobi-desktop/src/ — IPC, reconnect, splash untested |
| **Action** | Create minimal test suite for: preload.js IPC bridge, splash polling, main.js lifecycle |
| **Evidence sources** | U-01 uncertainty (OPEN) |
| **Acceptance** | At least 5 tests covering IPC, splash timeout, and error paths |

#### TF-009: Desktop Reconnect Strategy

| Field | Value |
|-------|-------|
| **Severity** | IMPORTANT |
| **Priority** | P1 |
| **Lane** | 3 (Desktop/Control-Plane) |
| **Description** | Splash polling uses fixed 1s interval with 30s timeout, no exponential backoff |
| **Action** | Implement exponential backoff in splash.js polling loop |
| **Evidence sources** | U-03 uncertainty (BOUNDED) |
| **Acceptance** | Backoff strategy documented; polling uses increasing intervals |

---

### IMPORTANT / P2 (3 items)

#### TF-010: Menu7 Arc Input Contract

| Field | Value |
|-------|-------|
| **Severity** | IMPORTANT |
| **Priority** | P2 |
| **Lane** | 4 (Operator Surface) |
| **Description** | Menu 7 desired-arc input contract needs remediation per investigation |
| **Action** | Implement input validation per menu7-desired-arc-input-contract-remediation-execution-ssot.md |
| **Evidence sources** | docs/2026-03-15/menu7-desired-arc-input-contract-remediation-execution-ssot.md |
| **Acceptance** | Menu 7 input validated against contract schema |

#### TF-011: Prompt Authority Consolidation Documentation

| Field | Value |
|-------|-------|
| **Severity** | IMPORTANT |
| **Priority** | P2 |
| **Lane** | 4 (Operator Surface) |
| **Description** | UIService is extracted but prompt authority chain documentation is informal |
| **Action** | Document prompt authority chain: UIService → renderer → PromptBroker → asyncio.Event |
| **Evidence sources** | C-02 resolution evidence |
| **Acceptance** | Architecture doc with prompt lifecycle diagram |

#### TF-012: Stage4 Context DB Retrieval Reject Persistence

| Field | Value |
|-------|-------|
| **Severity** | IMPORTANT |
| **Priority** | P2 |
| **Lane** | 1 (Persistence) |
| **Description** | Stage 4 context/DB retrieval reject persistence needs investigation |
| **Action** | Implement per stage4-cw-context-db-retrieval-reject-persistence-investigation.md |
| **Evidence sources** | docs/2026-03-15/stage4-cw-context-db-retrieval-reject-persistence-investigation.md |
| **Acceptance** | Reject persistence verified in bounded test |

---

### INSIGHT / P2 (2 items)

#### TF-013: DB Connection Pooling

| Field | Value |
|-------|-------|
| **Severity** | INSIGHT |
| **Priority** | P2 |
| **Lane** | 1 (Persistence) |
| **Description** | Single shared DB connection with check_same_thread=False; RLock serializes all access |
| **Action** | Evaluate connection pool (e.g., 2-3 connections) for read-heavy advisory queries vs write path |
| **Evidence sources** | Tranche D operational survey |
| **Acceptance** | Decision document: pool or retain current model |

#### TF-014: Console Print Audit

| Field | Value |
|-------|-------|
| **Severity** | INSIGHT |
| **Priority** | P2 |
| **Lane** | 5 (Code Health) |
| **Description** | 130 print() calls across 30 files. Most are spinners but some are diagnostic |
| **Action** | Migrate diagnostic print() to logging.debug(); preserve spinner print() |
| **Evidence sources** | Tranche E side-effects survey |
| **Acceptance** | Diagnostic print() reduced to 0; spinner print() annotated |

---

### INSIGHT / P3 (6 items)

#### TF-015: Ruff Auto-Fix (52 violations)

| Field | Value |
|-------|-------|
| **Severity** | INSIGHT |
| **Priority** | P3 |
| **Lane** | 5 (Code Health) |
| **Description** | 52 auto-fixable Ruff violations: I001(20), UP045(9), UP006(8), UP017(5), F401(4), UP037(2), UP041(1), UP035(partial) |
| **Action** | `ruff check --fix modules/ scripts/ main_a.py` |
| **Evidence sources** | Ruff statistics output |
| **Acceptance** | Auto-fixable count drops to 0 |

#### TF-016: Ruff Manual-Fix (14 violations)

| Field | Value |
|-------|-------|
| **Severity** | INSIGHT |
| **Priority** | P3 |
| **Lane** | 5 (Code Health) |
| **Description** | 14 manual violations: E402(9) import order + UP035(5) deprecated imports |
| **Action** | E402: restructure imports or add noqa. UP035: update import sources |
| **Evidence sources** | Ruff statistics output |
| **Acceptance** | Manual violations resolved or explicitly suppressed |

#### TF-017: JSONL Sink Consolidation

| Field | Value |
|-------|-------|
| **Severity** | INSIGHT |
| **Priority** | P3 |
| **Lane** | 5 (Code Health) |
| **Description** | 11 distinct JSONL sinks with 3 different lock mechanisms (global, per-instance, inline) |
| **Action** | Evaluate consolidating lock strategy; document sink inventory |
| **Evidence sources** | Tranche D JSONL analysis |
| **Acceptance** | Decision document on lock unification |

#### TF-018: DI Context Slot Audit

| Field | Value |
|-------|-------|
| **Severity** | INSIGHT |
| **Priority** | P3 |
| **Lane** | 5 (Code Health) |
| **Description** | Stage2Context has 47 slots (21 callbacks alone) — growth risk |
| **Action** | Evaluate callback grouping or delegation pattern for Stage2Context |
| **Evidence sources** | Tranche C cross-cut analysis |
| **Acceptance** | Decision: group callbacks or maintain current flat structure |

#### TF-019: Guard Chain Config Validation

| Field | Value |
|-------|-------|
| **Severity** | INSIGHT |
| **Priority** | P3 |
| **Lane** | 5 (Code Health) |
| **Description** | 10 genre guard YAML configs + WorkGuard overlay — no schema validation at load |
| **Action** | Add YAML schema validation for guard config loading |
| **Evidence sources** | Tranche C guard chain analysis |
| **Acceptance** | Invalid guard YAML raises clear error at startup |

#### TF-020: Test Coverage Mapping

| Field | Value |
|-------|-------|
| **Severity** | INSIGHT |
| **Priority** | P3 |
| **Lane** | 5 (Code Health) |
| **Description** | 315 test files vs 244 module files — no explicit coverage map |
| **Action** | Generate pytest coverage report; identify uncovered modules |
| **Evidence sources** | Tranche F coverage analysis |
| **Acceptance** | Coverage report with module-level coverage percentages |

---

## TF Summary

| Priority | CRITICAL | IMPORTANT | INSIGHT | Total |
|----------|----------|-----------|---------|-------|
| P0 | 0 | 0 | 0 | **0** |
| P1 | 0 | 3 | 0 | **3** |
| P2 | 0 | 3 | 2 | **5** |
| P3 | 0 | 0 | 6 | **6** |
| **Total** | **0** | **6** | **8** | **14** |

### By Lane

| Lane | Count | Items |
|------|-------|-------|
| 1 Persistence | 2 | TF-012, TF-013 |
| 3 Desktop | 3 | TF-007, TF-008, TF-009 |
| 4 Operator Surface | 2 | TF-010, TF-011 |
| 5 Code Health | 7 | TF-014~TF-020 |
| **Total** | **14** | |

**Lane 1 (Persistence/Observability)**: Original 6 items ALL COMPLETE. 2 follow-up items remain (P2).
**Lane 2 (Encoding/Hygiene)**: FULLY RESOLVED in d2982aa2 + bbb00a77. No remaining items.
