Date: 2026-03-23
Status: final
Document Type: T2 evidence manifest
Canonical Path: `docs/2026-03-23/opus/rol-global-survey-t2-persistence-operator-evidence.md`

---

# T2 Persistence / Operator — Evidence Manifest

## 1. DB Schema Evidence

### Tables Inventoried (30+)

| Table | Primary Key | Decision-Bearing | Max-Retention Compliant |
|-------|-------------|-------------------|------------------------|
| `stage_attempts` | id (autoincrement) | verdict, reject_reason, selection_reason, verdict_reason, open_review, fix_scope_reasoning, runtime_advisory, retry_directives | YES — no [:N] in DB write |
| `director_selections` | id (autoincrement) | verdict, selection_reason, verdict_reason, director_thinking, firewall_reason | YES — no [:N] in DB write |
| `llm_calls` | id (autoincrement) | thinking_snippet [TF-58], prompt_snippet (failure only), response_snippet (failure only) | YES |
| `attempt_raw_rationale` | id (autoincrement) | payload (raw text) | YES — full retention |
| `ui_events` | id (autoincrement) | message, meta_json | YES |
| `manuscripts` | ep_num | content (full) | YES |
| `episode_bibles` | ep_num | 12 JSON fields | YES |
| `state_logs` | ep_num | data (JSON), summary | YES |
| `episode_quality_labels` | ep_num | verdict, selection_reason, open_review | YES |
| `episode_quality_signals` | ep_num | signal_summary (JSON) | YES |
| `cost_log` | id (autoincrement) | model_breakdown (JSON) | YES |

### Schema Governance
- WAL mode: `PRAGMA journal_mode=WAL` (L34)
- `PRAGMA synchronous=NORMAL` (L35)
- Transaction: `commit_episode_factory()` uses `RLock` + nested check
- Rollback: `reset_after()` deletes from 20+ tables by ep_num

---

## 2. Truncation Evidence

### P1 Violations — Still Live

| ID | File:Line | Variable | Limit | Sink | Policy Violated |
|----|-----------|----------|-------|------|-----------------|
| T-01 | `stage2_finalizer.py:1878` | `reason` | [:500] | session_logger decisions.jsonl | JSONL max-retention |
| T-02 | `stage2_finalizer.py:3018` | `reject_reason` | [:100] | pass_rate_monitor.json | metrics max-retention |
| T-03 | `stage2_finalizer.py:2943` | `reason` → description | [:200] | console prep dict | console max-display |
| T-04 | `stage2_finalizer.py:1189` | `description` | [:200] | internal dict | console max-display |
| T-05 | `stage4_director_runtime.py:685` | `decision.reason` | [:80] | ui.log (console) | console max-display |
| T-06 | `stage4_director_runtime.py:699` | `decision.reason` | [:120] | _log_attempt_event (audit) | console max-display |
| T-07 | `stage4_director_runtime.py:729` | `selection_reason` | [:120] | ui.log (console) | console max-display |
| T-08 | `stage4_director_runtime.py:736` | `selection_reason` | [:120] | meta dict (audit) | console max-display |
| T-09 | `stage4_director_runtime.py:753` | `decision.reason` | [:120] | ui.log (console) | console max-display |
| T-10 | `pass_rate_monitor.py:315` | `reject_reason` (key) | [:50] | statistics key | analytics only |
| T-11 | `pass_rate_monitor.py:842` | `reject_reason` (export) | [:160] | hard_arc_analysis export | analytics only |

### Resolved Truncation — No Longer Live

| ID | Prior Claim | Current State |
|----|-------------|---------------|
| R-01 | "Stage 2 `reject_reason[:500]` before DB persistence" | DB path does NOT truncate. Only JSONL path truncates. |
| R-02 | "Stage 3 omits selection_reason, verdict_reason, open_review, fix_scope_reasoning" | Stage 3 now passes all 4 fields. Only runtime_advisory and retry_directives remain empty. |
| R-03 | "Stage 4 DB/console max-retention waves active" | Both execution SSOTs are closed. |

---

## 3. Stage Parity Evidence

### stage_attempts Field Parity

| Field | Stage 2 | Stage 3 | Stage 4 | Parity Status |
|-------|---------|---------|---------|---------------|
| verdict | ✓ | ✓ | ✓ | PARITY |
| score | ✓ | ✓ | ✓ | PARITY |
| attempt_num | ✓ | ✓ | ✓ | PARITY |
| reject_reason | ✓ (REJECT) | ✓ (REJECT) | ✓ | PARITY |
| selection_reason | ✓ | ✓ | ✓ | PARITY |
| verdict_reason | ✓ | ✓ | ✓ | PARITY |
| open_review | ✓ | ✓ | ✓ | PARITY |
| fix_scope_reasoning | ✓ | ✓ | ✓ | PARITY |
| advisory_flags | ✓ | ✓ | ✓ | PARITY |
| attempt_key | ✓ | ✓ | ✓ | PARITY |
| candidate_key | ✓ | ✓ | ✓ | PARITY |
| content_hash | ✓ | ✓ | ✓ | PARITY |
| artifact_path | ✓ | ✓ | ✓ | PARITY |
| runtime_advisory | ✗ `""` | ✗ `""` | ✓ | **GAP** |
| retry_directives | ✗ `""` | ✗ `""` | ✓ | **GAP** |
| initial_verdict | ✗ | ✗ | ✓ | **GAP** (Stage 4 specific) |
| score_breakdown | ✗ | ✗ | ✓ | **GAP** (Stage 4 specific) |
| is_patch | ✗ | ✗ | ✓ | **GAP** (Stage 4 specific) |
| is_patch_fallback | ✗ | ✗ | ✓ | **GAP** (Stage 4 specific) |
| patch_strategy | ✗ | ✗ | ✓ | **GAP** (Stage 4 specific) |
| generation_method | ✓ | ✗ | ✗ | **GAP** (Stage 2 specific) |

### director_selections Field Parity

| Field | Stage 2 | Stage 3 | Stage 4 |
|-------|---------|---------|---------|
| verdict | ✓ | ✓ | ✓ |
| score | ✓ | ✓ | ✓ |
| selection_reason | ✓ | ✓ | ✓ |
| selected_strategy | ✓ | ✓ | ✓ |
| fix_scope | ✓ | ✓ | ✓ |
| attempt_key | ✓ | ✓ | ✓ |
| selected_label | ✓ `""` | ✓ | ✓ |
| candidate_count | ✗ | ✗ | ✓ |
| advisory_warnings | ✗ | ✗ | ✓ |
| verdict_reason | ✗ | ✗ | ✓ |
| pre_firewall_score | ✗ | ✗ | ✓ |
| firewall_triggered | ✗ | ✗ | ✓ |
| firewall_reason | ✗ | ✗ | ✓ |
| candidate_key | ✗ | ✗ | ✓ |
| content_hash | ✗ | ✗ | ✓ |
| artifact_path | ✗ | ✗ | ✓ |
| director_thinking | ✗ | ✗ | ✓ |

---

## 4. Sink Retention Evidence

| Sink | Type | Retention | Auto-Cleanup |
|------|------|-----------|-------------|
| DB (project_data.db) | SQLite | Indefinite | Manual only (`reset_after()`) |
| episode_production.jsonl | JSONL | Append-only | None |
| runtime_audit.jsonl | JSONL | Append-only | None |
| decisions.jsonl | JSONL | 100MB rotation | 10 rotations max |
| llm_io.jsonl | JSONL | 100MB rotation | 10 rotations max |
| state_changes.jsonl | JSONL | 100MB rotation | 10 rotations max |
| ui_events.jsonl | JSONL | 100MB rotation | 10 rotations max |
| pass_rate_monitor.json | JSON | Latest 1000 records | Auto at 100-record boundary |
| metrics_{id}.json | JSON | 1 per session | Manual |
| session_{ts}.log | Text | 1 per session | Manual |
| runtime_audit_summary.json | JSON | Overwrites on each call | Per-call |
| audit_service memory buffer | In-memory | 1000 events, keeps 500 on overflow | Auto |

---

## 5. Silent Data Loss Paths

| ID | Location | Mechanism | Severity |
|----|----------|-----------|----------|
| SDL-1 | `db_manager.py:2876` | `save_llm_call()` failure → `logging.debug` only | P2 |
| SDL-2 | `db_manager.py:2980` | `save_stage_attempt()` failure → `logging.debug` only | P2 |
| SDL-3 | `db_manager.py:452` | `begin_shutdown()` sets `_accept_runtime_telemetry_writes = False` | By design |
| SDL-4 | `db_manager.py:1810-1818` | FTS/vec deletion failure → `pass` | P2 (rollback path only) |
| SDL-5 | `db_manager.py:558-559` | Blueprint JSON parse failure → returns None + `logging.warning` | P2 |
| SDL-6 | `audit_service.py:70-71` | Memory buffer cap 1000 → keeps 500 | P2 (JSONL unaffected) |

---

## 6. Desktop Operator Visibility Matrix

| Surface | Verdict | Score | Rationale | Feedback | Patch Mode | Decision History |
|---------|---------|-------|-----------|----------|------------|-----------------|
| Console | ✓ live | ✓ | ⚠️ [:80-120] | ⚠️ action items only | ✗ | ✗ current round |
| episode_production.jsonl | ✓ | ✓ | ✓ full | ✓ full | ✓ | ✓ |
| Desktop /quality/summary | ✓ latest | ✓ | ✗ | ✗ | ✗ | ⚠️ 8 ep window |
| Desktop /quality/dashboard | ✓ latest | ✓ | ⚠️ partial | ✗ | ✗ | ⚠️ analytics only |
| runtime_audit.jsonl | ⚠️ events | ✗ | ✗ | ✗ | ✗ | ✓ event stream |
| DB stage_attempts | ✓ | ✓ | ✓ full | ✓ full | ✓ Stage 4 | ✓ |
| DB director_selections | ✓ | ✓ | ✓ full Stage 4 | ✓ thinking Stage 4 | ✗ | ✓ |

---

## 7. Cross-Lane Observations (Not T2 Primary)

### CONDITIONAL_PASS Downstream Handling
- `director_ensemble.py:1187-1204` resolves CONDITIONAL_PASS to PASS or REJECT in normal path
- Exception path at L1178-1183 can return `state.original_verdict` = CONDITIONAL_PASS without resolution
- `stage4_interview_round.py:3788` only checks `("PASS", "PASS_WITH_FIX")` — CONDITIONAL_PASS would fall through
- This is a T1 (Runtime/Domain) finding, noted here because it affects which verdict reaches the persistence layer

### Stage 3 Session Logger Truncation
- `stage3_orchestrator.py:1824` — `str(log_err)[:100]` in debug log (cosmetic, P2)
- `stage3_orchestrator.py:2592` — `str(_log_err)[:100]` in debug log (cosmetic, P2)
- These are error-message truncation, not decision-text truncation

---

## 8. Source File Line Counts (Survey Scope)

| File | Lines | Role |
|------|-------|------|
| `modules/core/db_manager.py` | 3,432 | DB schema + all persistence |
| `modules/core/session_logger.py` | 355 | JSONL session logging |
| `modules/core/logger.py` | 353 | Standard logging + LoggerAdapter |
| `modules/core/pass_rate_monitor.py` | 881 | Pass-rate analytics |
| `modules/core/metrics_collector.py` | 537 | Performance/cost metrics |
| `modules/core/services/audit_service.py` | 317 | Runtime audit events |
| `modules/core/studio_visualizer.py` | 147 | Console/UI rendering |
| `modules/core/stage2_finalizer.py` | ~3,100 | Stage 2 persistence writes |
| `modules/core/stage3_orchestrator.py` | ~2,700 | Stage 3 persistence writes |
| `modules/core/stage4_interview_round.py` | ~5,900 | Stage 4 persistence writes |
| `modules/core/stage4_post_processor.py` | ~850 | Settlement persistence |
| `modules/core/stage4_post_pass_runtime.py` | ~1,400 | Post-pass persistence |
| `modules/core/stage4_director_runtime.py` | ~900 | Console output paths |
| `modules/api/bridge_server.py` | ~900 | Desktop API endpoints |
