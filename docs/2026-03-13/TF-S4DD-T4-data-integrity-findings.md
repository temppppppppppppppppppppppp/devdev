# TF-S4DD-T4: Stage 4 Data Integrity & State Management Audit

**Date**: 2026-03-13
**Scope**: Read-only audit of Stage 4 data synchronization, transaction safety, append-only invariants, and attempt logging completeness.

---

## 4.1 HUD Capital Sync

### Extraction Mechanism
`Stage4PostProcessor._extract_capital_from_manuscript()` (L195-234) uses **regex-based extraction** with three pattern families:

1. **`_CAPITAL_PATTERNS`** (L148-153): Two compiled regexes matching "잔고 131억" and "80억의 자본" forms.
2. **`_COMPOUND_CAPITAL_RE`** (L155-158): Compound pattern for "38억 3,154만 200원" forms.
3. **Dialogue exclusion** (L160, L198): `_DIALOGUE_RE` strips quoted dialogue before extraction to prevent counting other characters' assets.

All matches are collected as `(position, value_eok)` tuples. When duplicates exist at the same position, the higher-precision compound value wins. The **last-mentioned** capital value in the manuscript is returned (L234: `pos_best[max(pos_best)]`).

### Comparison Against Expected Values
`_reconcile_capital()` (L236-285):
- Fetches current HUD capital via `hud.pro_data.get("capital")`.
- Parses HUD value through `_parse_hud_capital_to_eok()` which handles "억/만/원" compound strings and raw integer (won) fallback.
- Compares extracted vs HUD with a **5억 tolerance** (L271: `diff <= 5`).
- **Director sovereignty respected**: If `final_state_updates` already contains capital-related keys, reconciliation is skipped entirely (L244-249).

### Advisory Warning Flow
When discrepancy exceeds 5억:
- `logging.warning()` with details (L274).
- UI advisory message (L282-285).
- **No automatic HUD modification** -- the comment says "Director state_updates 반영 대기".

### NumericConsistencyChecker Cross-Validation
`NumericConsistencyChecker._check_against_ledger()` (L410-454) performs a separate cross-check:
- Extracts money/percent/leverage numbers from manuscript (excluding dialogue).
- Compares against `FactLedger.get_numbers()` with **5% tolerance** (L419).
- Uses synonym mapping (L201-210) for label matching (e.g., "잔고" matches "자본금", "현금", etc.).
- Results are MAJOR severity advisory warnings only.

### Findings
- **SOUND**: Dual-layer validation (HUD reconciliation + FactLedger cross-check) with appropriate tolerances.
- **MINOR CONCERN**: `_extract_capital_from_manuscript` takes the last-mentioned value. If the manuscript ends with a different character's assets mentioned in narration (outside quotes), it could be misattributed. The dialogue exclusion mitigates but does not fully prevent this (narration mentions of third-party assets are not excluded).
- **VERDICT**: Low risk. The 5억 tolerance and Director bypass provide adequate safety margins.

---

## 4.2 World State Atomic Save

### DB Save (Primary Data)
`process_pass_result()` (L311-337) performs **explicit atomic transaction**:
```
_db._lock:                       # threading Lock
  if _db.conn.in_transaction:    # cleanup any dangling tx
      _db.conn.commit()
  _db.conn.execute("BEGIN")
  try:
      _db.save_manuscript(...)
      _db.update_martial_tracker(...)
      _db.conn.commit()
  except:
      _db.conn.rollback()
      raise
```

**Verdict**: Atomic with lock. DB save failure returns `False`, halting the episode.

### HUD Update
HUD update (L381-396) runs **only after DB commit succeeds**. Uses `director.on_approve_workflow()` for approval, then `hud.bulk_update()`. Non-blocking on failure (warning only).

### WorldState + FactLedger Save
`_save_world_state_atomic()` (L1141-1233):
- Takes **deep copy snapshots** of `world_state._state` and `fact_ledger._ledger` before modification.
- Uses `_db.transaction()` context manager if available.
- On any exception, **restores in-memory state from snapshots** (L1222-1225).
- Reports soft failure but does not block.

### Async Submission
`_submit_manager_async()` (L621-682) submits Manager LLM work to a `ThreadPoolExecutor(max_workers=1)`. The future is collected synchronously in `_collect_manager_and_build_delta()` with a **120s timeout** (L793). If timeout/failure occurs, a synchronous retry is attempted. This is blocking relative to the episode loop.

### Completion Before Next Episode
The orchestrator loop (stage4_orchestrator.py L874-890) calls `process_pass_result()` **synchronously**. The function does not return until all saves (DB, HUD, WorldState, FactLedger, VecMemory, file) complete. The next episode iteration cannot begin until `process_pass_result()` returns `True`.

### Race Condition Analysis
- **DB lock**: `_db._lock` protects concurrent DB access.
- **Manager async**: Single-threaded executor, future collected before world state save. No parallel mutation.
- **VecMemory**: Saved in `_memorize_and_validate()` before world state update.

### Findings
- **SOUND**: Proper atomic save with snapshot-based rollback for in-memory state.
- **MINOR CONCERN**: Quality labels (`save_episode_quality_label`, L343-355) and quality signals (L357-378) are saved **outside** the main transaction. A crash between the main commit and these sidecar saves would leave quality metadata missing but core data intact. This is acceptable (labeled "비차단").
- **MINOR CONCERN**: `_submit_manager_async` uses `shutdown(wait=False)`. If the main process dies before the future is collected, the thread may leak. However, since the future is collected with `result(timeout=120)` shortly after, practical risk is negligible.
- **VERDICT**: Low risk. Sequential episode processing with atomic DB + snapshot rollback provides strong guarantees.

---

## 4.3 Canary DB Transactions

### Transaction Pattern
`_delete_stage4_db_outputs()` (L259-299):

```python
started_tx = not db.conn.in_transaction
if started_tx:
    cur.execute("BEGIN")
try:
    # ... 20 DELETE statements ...
    db.conn.commit()
except Exception:
    db.conn.rollback()
    raise
```

**Verdict**: Proper BEGIN/COMMIT/ROLLBACK with conditional BEGIN (avoids nested transaction error).

### DELETE Statement Count and Table Coverage
**20 DELETE statements** covering:

| # | Table | Column Filter |
|---|-------|---------------|
| 1-4 | state_logs, causal_graph, manuscripts, martial_tracker | ep_num >= from_ep |
| 5 | episode_bibles | ep_num >= from_ep |
| 6 | sync_status | ep_num >= from_ep |
| 7 | karma_status | last_updated_ep >= from_ep |
| 8 | npc_history | episode_no >= from_ep |
| 9 | episode_sentence_hashes | episode_number >= from_ep |
| 10 | episode_satisfaction_tags | ep_num >= from_ep |
| 11 | director_selections | ep_num >= from_ep AND stage=4 |
| 12 | episode_pacing | ep_num >= from_ep |
| 13 | episode_quality_labels | ep_num >= from_ep |
| 14 | episode_quality_signals | ep_num >= from_ep |
| 15 | episode_quality_observations | ep_num >= from_ep |
| 16 | stage_attempts | stage=4 AND ep_num >= from_ep |
| 17 | episode_fts | rowid >= from_ep (try/except) |
| 18 | episode_meta | ep_num >= from_ep |
| 19 | foreshadow | planted_ep >= from_ep |
| 20 | npc_relationship_edges | updated_ep >= from_ep |

Plus:
- DELETE from `npc_relationship_history` (change_ep >= from_ep)
- DELETE from `seeds` (planted_ep >= from_ep)
- **UPDATE** `seeds` (reset recovered_ep, set status='active' for recovered_ep >= from_ep)

### Post-Transaction
`db.conn.execute("VACUUM")` runs outside the transaction (try/except, non-blocking).

### Findings
- **SOUND**: All DELETEs within a single transaction with proper rollback.
- **NOTE**: `episode_fts` DELETE is wrapped in its own try/except (L282-285), meaning FTS cleanup failure does not abort the entire transaction. This is intentional (FTS table may not exist).
- **NOTE**: The `seeds` UPDATE (L291) resets recovered seeds to 'active' status -- this is a state restoration operation appropriate for canary reset.
- **VERDICT**: Safe. Comprehensive table coverage with single-transaction atomicity.

---

## 4.4 NPC History Append-Only

### Stage 4 File Scan Results

Files checked: `stage4_orchestrator.py`, `stage4_post_processor.py`, `stage4_interview_round.py`, `stage4_context_builder.py`, `stage4_context.py`, `stage4_canary_tools.py`

| File | Operation | Line | Context |
|------|-----------|------|---------|
| stage4_context_builder.py | `db.get_npc_history()` (READ) | L579 | Fetches last 3 history rows for context |
| stage4_interview_round.py | `state_tracker.get_npc_change_history()` (READ) | L3669 | Gets NPC history for cv_context injection |
| stage4_canary_tools.py | `DELETE FROM npc_history WHERE episode_no >= ?` | L270 | Canary cleanup only |

### Verification
- **No UPDATE on npc_history** in any Stage 4 file.
- **No DELETE on npc_history** except in canary cleanup (`stage4_canary_tools.py`).
- **No INSERT on npc_history** in Stage 4 files. All inserts go through `db_manager.py` L2611: `INSERT INTO npc_history (...) VALUES (...)` which is called by the state tracker, not directly by Stage 4 code.
- The canary cleanup DELETE is legitimate (test infrastructure reset).

### Findings
- **SOUND**: Append-only invariant is preserved. Stage 4 only READs npc_history. The sole DELETE is in canary test tooling, not production flow.
- **VERDICT**: No violation.

---

## 4.5 FactLedger Read-Only in Advisory Modules

### Advisory Modules Checked

| Module | FactLedger Access | Writes? |
|--------|-------------------|---------|
| `truth_gate.py` | `self._fact_ledger` stored but **never called** (no `.get_numbers()`, `.update()`, etc.) | NO |
| `numeric_consistency_checker.py` | `self._fact_ledger.get_numbers()` (READ) | NO |
| `numeric_drift_advisor.py` | Receives `numbers` dict param (pre-extracted), no FactLedger reference | NO |
| `npc_drift_advisor.py` | No FactLedger reference | N/A |
| `relationship_drift_advisor.py` | No FactLedger reference | N/A |
| `flashback_verifier.py` | No FactLedger reference | N/A |
| `info_paradox_checker.py` | No FactLedger reference | N/A |
| `long_term_repetition_advisor.py` | No FactLedger reference | N/A |

### FactLedger Writes
The **only** FactLedger write operations are in `stage4_post_processor.py:_save_world_state_atomic()`:
- L1196: `self.ctx.fact_ledger.update_from_state_changes()`
- L1199: `self.ctx.fact_ledger.update_from_bible_delta()`
- L1202: `self.ctx.fact_ledger.save()`

These are in the post-pass data settlement phase, not in advisory modules.

### Findings
- **SOUND**: All advisory modules are strictly read-only with respect to FactLedger.
- **NOTE**: `TruthGate` stores a `_fact_ledger` reference but never calls any method on it in the current codebase. This is either dead code or reserved for future use.
- **VERDICT**: No violation. Clean read-only advisory pattern.

---

## 4.6 Attempt Logging Completeness

### `_record_s4_attempt` Location
Defined in `stage4_interview_round.py` L4499-4642.

### Exit Path Coverage

| Exit Path | Called? | Location | Verdict Param |
|-----------|--------|----------|---------------|
| **PASS** | YES | L3004 | `verdict=verdict` (PASS or PASS_WITH_FIX) |
| **PASS_WITH_FIX** | YES | L3004 | Same call as PASS (L2970: `if verdict in ("PASS", "PASS_WITH_FIX")`) |
| **REJECT** | YES | L3235 | `verdict="REJECT"` |
| **EMPTY** (empty candidates) | YES | L1438 | `verdict="ERROR"`, `reject_reason="empty_candidates"` |

### Details
1. **PASS/PASS_WITH_FIX** (L3004-3029): Full metadata including `success=True`, score, patch strategy, candidate_key, artifact_payload, selection_reason, verdict_reason, open_review, fix_scope_reasoning, runtime_advisory, score_breakdown.

2. **REJECT** (L3235-3261): Full metadata including `success=False`, reject_reason, fix_scope, candidate_key, artifact of rejected best, all rationale fields.

3. **EMPTY** (L1438-1450): Minimal metadata: `success=False`, `score=0`, `verdict="ERROR"`, `reject_reason="empty_candidates"`. Missing: selection_reason, verdict_reason, open_review, fix_scope_reasoning, runtime_advisory, retry_directives, score_breakdown.

### PassRateMonitor Integration
`_record_s4_attempt` internally calls `self.ctx.pass_rate_monitor.record_attempt()` (L4571) and `_db.save_stage_attempt()` (L4610) -- both wrapped in try/except for non-blocking behavior.

### Findings
- **SOUND**: All 4 exit paths (PASS, PASS_WITH_FIX, REJECT, EMPTY) call `_record_s4_attempt`.
- **MINOR CONCERN**: The EMPTY path records `verdict="ERROR"` rather than `verdict="EMPTY"`. This may cause slight confusion in analytics since the `_InterviewRoundResult` returns `verdict="EMPTY"` but the DB records `verdict="ERROR"`. Downstream consumers querying `stage_attempts` table for EMPTY verdicts would need to filter by `reject_reason="empty_candidates"` instead.
- **MINOR CONCERN**: The EMPTY path does not pass `selection_reason`, `verdict_reason`, `open_review`, `fix_scope_reasoning`, `runtime_advisory`, `retry_directives`, or `score_breakdown`. These default to empty strings/None in the function signature, which is acceptable but means EMPTY attempts have sparser audit trails.
- **VERDICT**: Complete coverage. All paths logged.

---

## Summary

| Task | Status | Risk |
|------|--------|------|
| 4.1 HUD Capital Sync | SOUND | LOW -- dual-layer regex extraction + 5억 tolerance + Director bypass |
| 4.2 World State Atomic Save | SOUND | LOW -- atomic DB tx + snapshot rollback + sequential episode processing |
| 4.3 Canary DB Transactions | SOUND | NONE -- single-tx with BEGIN/COMMIT/ROLLBACK, 22 operations across 20+ tables |
| 4.4 NPC History Append-Only | SOUND | NONE -- only READs in production code, DELETE only in canary cleanup |
| 4.5 FactLedger Read-Only | SOUND | NONE -- all advisories strictly read-only |
| 4.6 Attempt Logging Completeness | SOUND | LOW -- all 4 exits logged, minor verdict label inconsistency for EMPTY |

### Minor Action Items (Non-Blocking)
1. EMPTY verdict records as "ERROR" in DB but "EMPTY" in return value -- consider aligning.
2. `TruthGate._fact_ledger` stored but never used -- candidate for cleanup or documentation.
3. Quality label/signal saves outside main transaction -- acceptable but worth noting in ops runbook.
