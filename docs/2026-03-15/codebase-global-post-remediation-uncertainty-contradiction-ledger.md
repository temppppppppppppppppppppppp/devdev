# Post-Remediation Uncertainty & Contradiction Ledger

| Field | Value |
|-------|-------|
| **Baseline** | `bbb00a77` |
| **Date** | 2026-03-15 |
| **Predecessor ledgers** | cleanroom-source-only, log-evidence-merged |

---

## Contradiction Registry (7 items)

### C-01: Mojibake vs Hygiene False Positive — RESOLVED

| Field | Value |
|-------|-------|
| **Origin** | cleanroom-source-only survey |
| **Claim** | Mojibake scan may produce false positives against legitimate Korean encoding |
| **Resolution** | d2982aa2 + bbb00a77 established distinct mojibake vs hygiene pipelines |
| **Evidence** | scripts/check_utf8_hygiene.py (211 LOC), tests/test_encoding_boundary_contract.py (14 assertions), tests/test_mojibake_global_survey.py (17 assertions), tests/test_check_utf8_hygiene.py (83 assertions). artifact_logging.py L114: `write_bytes(text.encode("utf-8"))` guarantees UTF-8 on-disk integrity |
| **Closure date** | 2026-03-15 (bbb00a77) |

### C-02: Prompt Authority Split — RESOLVED

| Field | Value |
|-------|-------|
| **Origin** | cleanroom-source-only survey |
| **Claim** | main_a.py input() calls bypass UIService, creating dual prompt authority |
| **Resolution** | UIService extraction complete (Phase 4B-2). 0 bare input() calls in main_a.py |
| **Evidence** | main_a.py L113: UIService imported, L372: initialized. All user input routes through UIService → renderer/desktop bridge. Grep confirms 0 matches for standalone `input(` |
| **Closure date** | 2026-03-15 |

### C-05: Backend-Front Readiness Conflation — PARTIALLY RESOLVED

| Field | Value |
|-------|-------|
| **Origin** | cleanroom-source-only survey |
| **Claim** | Backend readiness and desktop readiness are conflated in health checks |
| **Resolution** | Contract documents define separation; no runtime proof yet |
| **Evidence** | docs/2026-03-15/backend-front-control-plane-connectivity-hardening-remediation-execution-ssot.md defines command-path vs websocket-path decoupling. process_runner.py reconnect timeout stabilized. Desktop code still gates on `_backendConnected` |
| **Remaining** | Runtime desktop session required to validate end-to-end separation |
| **Status** | PARTIALLY RESOLVED — blocked on desktop runtime validation |

### C-06: Prompt Lifecycle Concurrency — RESOLVED

| Field | Value |
|-------|-------|
| **Origin** | cleanroom-source-only survey |
| **Claim** | Multiple concurrent prompts may silently drop in renderer |
| **Resolution** | PromptBroker state machine with per-prompt PromptState (prompt_id, resolved flag, asyncio.Event). Explicit timeout + default semantics replace silent drops |
| **Evidence** | modules/api/prompt_broker.py L27-70: PromptState + PromptBroker implementation. Thread-safe via _lock. Event-schema-v1.json documents policy |
| **Closure date** | 2026-03-15 |

### Log C-02: Proof-Digest Timing — RESOLVED

| Field | Value |
|-------|-------|
| **Origin** | log-evidence-merged survey |
| **Claim** | Proof digest may capture uncommitted or stale data |
| **Resolution** | `proof_digest_truth_scope: "committed_persistence_only"`. Read-only DB mode (`mode=ro`). Pre-summary hook flushes advisory state before digest |
| **Evidence** | audit_service.py L256: truth_scope declaration. L133: read-only mode. L269: pre-hook. test_audit_service.py L399-410: committed snapshot assertion. L252: ExplodingDBManager prevents re-entry |
| **Closure date** | 2026-03-15 (bbb00a77) |

### Log C-05: Session Identity — RESOLVED

| Field | Value |
|-------|-------|
| **Origin** | log-evidence-merged survey |
| **Claim** | Session IDs from different sinks may diverge undetected |
| **Resolution** | Dual lineage tracking: plain_log_token + structured_session_id with explicit reconciliation status |
| **Evidence** | audit_service.py L173-186: `_build_session_lineage()`. Status enum: unified/split_mapped/partial/missing. test_audit_service.py L272-274: split_mapped assertion |
| **Closure date** | 2026-03-15 (bbb00a77) |

### Log C-07/C-08: Artifact Hash + Teardown — RESOLVED

| Field | Value |
|-------|-------|
| **Origin** | log-evidence-merged survey |
| **Claim** | Artifact hash may not match persisted content; teardown may lose audit data |
| **Resolution** | (C-07) SHA256 computed on `persisted_bytes` which are the exact UTF-8 bytes written to disk. (C-08) Multi-phase shutdown: atexit audit flush → pre-summary hook → proof digest → resource cleanup |
| **Evidence** | (C-07) artifact_logging.py L53: SHA256 on persisted_bytes, L114: write_bytes(). test_artifact_logging.py L39-56: round-trip hash assertion. (C-08) main_a.py L369: atexit registration, L3003-3018: ordered shutdown. test_audit_service.py L99-119: pre-hook sentinel test |
| **Closure date** | 2026-03-15 (bbb00a77) |

---

## Contradiction Summary

| Status | Count | Items |
|--------|-------|-------|
| RESOLVED | 6 | C-01, C-02, C-06, Log C-02, Log C-05, Log C-07/08 |
| PARTIALLY RESOLVED | 1 | C-05 (desktop runtime proof pending) |
| OPEN | 0 | — |

---

## Uncertainty Registry (9 items)

### U-01: Desktop Integration Test Depth — OPEN

| Field | Value |
|-------|-------|
| **Status** | OPEN |
| **Detail** | 0 test files in geuldobi-desktop/src/. IPC handlers, reconnect logic, splash polling all untested |
| **Impact** | Low (backend is primary; desktop is rendering layer) |
| **Mitigation** | Manual desktop session testing; contract documents define expected behavior |

### U-02: Lane 1 Test Depth — RESOLVED

| Field | Value |
|-------|-------|
| **Status** | RESOLVED |
| **Detail** | test_audit_service.py (451 LOC), test_session_logger.py (390 LOC), test_artifact_logging.py (88 LOC). All Lane 1 code paths covered |
| **Evidence** | 929 total test lines across 3 dedicated suites. Proof-digest, quiescent-point, hash round-trip, shutdown, rotation all tested |

### U-03: Desktop Reconnect Behavior — BOUNDED

| Field | Value |
|-------|-------|
| **Status** | BOUNDED |
| **Detail** | Splash polls /status at 1s intervals, fails after MAX_POLL_FAILS=30 (30s). No exponential backoff |
| **Scope** | Known limitation — acceptable for local desktop app. Reconnect is renderer-side (browser fetch retry) |
| **Impact** | Low (local-only deployment) |

### U-04: Desktop Splash Timeout — RESOLVED

| Field | Value |
|-------|-------|
| **Status** | RESOLVED |
| **Detail** | SPLASH_FALLBACK_MS = 8000 (main.js L66). AbortSignal.timeout(5000) per-fetch (splash.js L17) |
| **Evidence** | Hardcoded values with explicit comments. fallbackTimer at L374-377 |

### U-05: UI Service Completeness — RESOLVED

| Field | Value |
|-------|-------|
| **Status** | RESOLVED |
| **Detail** | ui_service.py: 222 LOC, 11 methods, 0 TODO/FIXME markers. Input validation present |
| **Evidence** | Source read confirms complete implementation |

### U-06: Command vs WebSocket Separation — RESOLVED

| Field | Value |
|-------|-------|
| **Status** | RESOLVED |
| **Detail** | HTTP POST for commands (/run, /stop, /run/{id}/input), WebSocket for events (/events). No cross-routing |
| **Evidence** | bridge_server.py route definitions. preload.js exposes both paths separately |

### Log U-01: Desktop Plain-Log Consumption — BOUNDED

| Field | Value |
|-------|-------|
| **Status** | BOUNDED |
| **Detail** | Desktop does NOT read session_*.log files. Uses WebSocket /events for real-time streaming |
| **Scope** | Known design — plain logs are for post-mortem analysis only |
| **Impact** | None (intended architecture) |

### Log U-02: Late-Write Chain Completeness — RESOLVED

| Field | Value |
|-------|-------|
| **Status** | RESOLVED |
| **Detail** | main_a.py shutdown: session_logger.begin_shutdown() (L3009) called before db.begin_shutdown() (L3013). All persistence methods complete before freeze. Audit summary written after both freezes (L3015) |
| **Evidence** | Source read of shutdown sequence. Bounded persistence test project validates |

### Log U-05: Hash Capture Point Timing — RESOLVED

| Field | Value |
|-------|-------|
| **Status** | RESOLVED |
| **Detail** | artifact_logging.py L52-53: hash computed on serialized payload BEFORE disk write (L66). Hash describes content, not file existence. Empty hash returned if no bytes |
| **Evidence** | test_artifact_logging.py L39-56: round-trip assertion confirms hash matches persisted bytes |

---

## Uncertainty Summary

| Status | Count | Items |
|--------|-------|-------|
| RESOLVED | 6 | U-02, U-04, U-05, U-06, Log U-02, Log U-05 |
| BOUNDED | 2 | U-03 (reconnect), Log U-01 (plain-log) |
| OPEN | 1 | U-01 (desktop test depth) |

---

## Residual Risk Assessment

| Item | Risk Level | Mitigation |
|------|-----------|------------|
| C-05 (desktop runtime) | LOW | Contract defined; blocked only on runtime session |
| U-01 (desktop tests) | LOW | Backend is primary; desktop is rendering layer |
| U-03 (reconnect) | LOW | Local-only deployment; 30s timeout adequate |
| Log U-01 (plain-log) | NONE | Intended architecture (WS for real-time, logs for post-mortem) |
