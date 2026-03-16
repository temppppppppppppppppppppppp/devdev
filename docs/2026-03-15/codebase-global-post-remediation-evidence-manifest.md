<!-- [참고자료] -->
# Post-Remediation Evidence Manifest

| Field | Value |
|-------|-------|
| **Baseline** | `bbb00a77` |
| **Survey** | codebase-global-post-remediation-deep-global-survey.md |
| **Date** | 2026-03-15 |

---

## Evidence Sources by Tranche

### A. Macro Topology

| Evidence | Method | Result |
|----------|--------|--------|
| modules/ file count | `find modules/ -name "*.py" \| wc -l` | 244 |
| tests/ file count | `find tests/ -name "*.py" \| wc -l` | 315 |
| scripts/ file count | `find scripts/ -name "*.py" \| wc -l` | 34 |
| modules/ LOC | `wc -l modules/**/*.py` | 138,260 |
| tests/ LOC | `wc -l tests/**/*.py` | 77,833 |
| config file count | Directory listing | 47 (+ 21 laws/seeds) |
| services/ new surface | Directory listing | 5 .py files, 1,522 LOC |

### B. Runtime Core (Lane 1)

| File | Evidence | Method |
|------|----------|--------|
| db_manager.py | begin_shutdown() L1118, _accept_runtime_telemetry_writes L66 | Source read |
| db_manager.py | Telemetry gating on 4 methods | Source read + grep |
| db_manager.py | update_director_selection_rationale() L2821 | Source read |
| artifact_logging.py | persisted_bytes key L53, L100, L107 | Source read |
| artifact_logging.py | write_bytes() L114 | Source read |
| session_logger.py | begin_shutdown() L69-71 | Source read |
| session_logger.py | _enabled guard on 4 log methods | Source read |
| stage4_interview_round.py | Rationale sync L2138, L2297 | Source read |
| audit_service.py | _build_session_lineage() L173-186 | Source read |
| audit_service.py | proof_digest_truth_scope L256 | Source read |
| main_a.py | Shutdown sequence L3003-3018 | Source read |

### C. Cross-Cut

| Evidence | Method | Result |
|----------|--------|--------|
| Stage2Context slots | Source read stage2_context.py | 47 __slots__ |
| Stage3Context slots | Source read stage3_context.py | 19 __slots__ |
| Stage4Context slots | Source read stage4_context.py | 26 __slots__ |
| Callback wiring patterns | Source read + grep | 3 distinct patterns |
| Guard chain order | Source read work_guard.py L7 | GenreGuard → WorkGuard → StyleGuard |
| Guard class count | Glob genre_guards/*.py | 13 classes |
| Service boundaries | Source read services/*.py | 4 services, 57+ methods |

### D. Operational

| Evidence | Method | Result |
|----------|--------|--------|
| DB transaction safety | Grep BEGIN/COMMIT/ROLLBACK | RLock + WAL + nested detection |
| JSONL sink inventory | Grep .jsonl patterns | 11 distinct sinks |
| Shutdown sequence | Source read main_a.py | 6-phase + 2 quiescence points |
| Connection model | Source read db_manager.py L204 | Single shared, check_same_thread=False |

### E. Side-Effects

| Evidence | Method | Result |
|----------|--------|--------|
| File writes | Grep open(.*w) + write_text | 18 write patterns |
| DB write ops | Grep INSERT/UPDATE | 29+ operations |
| Console output | Grep print( in modules/ | 130 calls, 30 files |
| Audit trail | Source read audit_service.py | Buffer (1K cap) + JSONL append |

### F. Coverage

| Evidence | Method | Result |
|----------|--------|--------|
| test_audit_service.py | wc -l | 451 lines |
| test_session_logger.py | wc -l | 390 lines |
| test_artifact_logging.py | wc -l | 88 lines |
| Lane 1 mapping | Glob test_*.py | All 4 core modules have dedicated tests |
| Suite status | pytest (historical) | 2,114 passed + 68 xfailed |

### G. Dependencies

| Evidence | Method | Result |
|----------|--------|--------|
| External APIs | Grep requests/genai | 2 (Slack webhook, Gemini SDK) |
| Circular guards | Grep TYPE_CHECKING | 6 files with forward reference guards |
| Requirements | Read requirements.txt | google-genai, sqlite-vec, fastapi, pytest |

### H. Risk

| Evidence | Method | Result |
|----------|--------|--------|
| C-01 encoding | Source read + commit diff | RESOLVED: UTF-8 pipeline + 3 test suites |
| C-02 prompt authority | Grep input( in main_a.py | RESOLVED: 0 bare input(), UIService only |
| C-05 backend-front | Read contract docs | PARTIALLY: contract defined, no runtime proof |
| C-06 prompt lifecycle | Source read prompt_broker.py | RESOLVED: state machine + policy |
| Log C-02 timing | Source read audit_service.py | RESOLVED: committed_persistence_only |
| Log C-05 session ID | Source read session_logger.py + audit_service.py | RESOLVED: dual lineage |
| Log C-07/08 hash+teardown | Source read artifact_logging.py + main_a.py | RESOLVED: SHA256 + multi-phase |

---

## Execution Evidence

### Bounded Persistence Validation

- **Location**: `projects/bounded_persistence_20260315_190309/`
- **Result**: Full execution trace confirms:
  - Telemetry gating works (no writes after freeze)
  - Artifact hash matches persisted bytes
  - Session logger properly disabled
  - Audit summary captures committed state only
  - Shutdown sequence completes without data loss

### Project 000 Test Run

- **Location**: `projects/000/`
- **Content**: 6 episodes, Stage 4 complete
- **Evidence**: episode_production.jsonl with 5 episodes recorded
- **Verdicts**: PASS (ep1-3), PASS_WITH_FIX→REJECT (ep4, 2 attempts)

---

## Ruff Evidence

| Source | Method | Result |
|--------|--------|--------|
| Current violations | `ruff check --statistics` | 66 total, 52 auto-fixable |
| Previous count | Plan document | 186 (64% reduction achieved) |
| Rule breakdown | Statistics output | I001(20), E402(9), UP045(9), UP006(8), UP035(8), UP017(5), F401(4), UP037(2), UP041(1) |
