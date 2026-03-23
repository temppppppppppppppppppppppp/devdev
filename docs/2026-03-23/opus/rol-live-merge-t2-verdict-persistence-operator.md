Date: 2026-03-23
Status: final
Document Type: ROL live-merge T2 lane survey report
Canonical Path: `docs/2026-03-23/opus/rol-live-merge-t2-verdict-persistence-operator.md`
Lane: T2 — Verdict / Persistence / Operator
Order: `docs/2026-03-23/rol-live-merge-3terminal-order.md`
Baseline Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
Baseline Dirty Summary: `dirty workspace with Stage 4 bottleneck fixes, live fresh-run artifacts, and survey/doc backlog`
Run Terminal State: `stopped` (user abort during Stage 4 Episode 3 Round 5)
Evidence Artifacts:
- `docs/2026-03-23/console.txt`
- `projects/0_0323/project_data.db`
- `projects/0_0323/logs/runtime_audit.jsonl`
- `projects/0_0323/logs/pass_rate_monitor.json`
- `projects/0_0323/logs/episode_production.jsonl`
- `projects/0_0323/logs/session/`
Side-Effect Coverage:
- artifact truth: deferred to T1
- DB truth: yes
- console/operator truth: yes
- JSONL/metrics truth: yes
- session logger truth: yes

---

## 1. Executive Summary

The T2 lane covers the verdict chain, persistence parity, and operator provenance for the current fresh run and the live codebase state.

Key findings:

1. **Post-select downgrade DB write-back gap.** Director verdict is persisted to DB BEFORE post-select checks run. When post-select downgrades PASS to REJECT, the downgrade verdict is NOT written back to `director_selections`. DB truth and runtime truth diverge.
2. **Post-select downgrade missing `fix_pack` snapshot.** The `previous_attempt` dict built at downgrade omits the Director's `fix_pack`, causing the next round to evaluate `None` → `missing_patch_targets` → Lane3 Gate widening → cascading empty patch loop.
3. **`failure_category` NULL on post-select REJECT.** The `error_category` IS set correctly in the post-select downgrade path, but the final DB persistence path for `stage_attempts.failure_category` still receives `""` → becomes `NULL` in some cases. Stage 2/3 never populate this field at all.
4. **Stage 2/3 DB rationale parity gap.** Stage 2/3 `save_stage_attempt()` calls still omit `initial_verdict`, `failure_category`, `selection_reason`, `verdict_reason`, and other fields that Stage 4 now populates.
5. **`retry_directives` unbounded accumulation.** No truncation cap. Each round wraps prior feedback in `[R{N} 이전 지시]` sections, growing O(rounds).
6. **`CONDITIONAL_PASS` from V60.97 is resolved in `director_ensemble.py:1187-1204`.** The current code appears to convert CONDITIONAL_PASS exhaustively to PASS or REJECT before return. The Q3 R2 finding that CONDITIONAL_PASS falls through to reject may be based on an edge case in the `_apply_ensemble_quality_gates()` adaptive branch that warrants targeted verification.
7. **`session_decisions` declared as authoritative sink in `audit_service.py:37` but no JSONL writer exists.** Ghost declaration.

This lane contains **no probable rerun blocker** in the crash/data-loss sense. The highest-ROI fixes are observability and retry-loop efficiency improvements.

## 2. Included Coverage

| Sub-Surface | Files | Status |
|---|---|---|
| Director verdict chain | `stage4_director_runtime.py`, `director_ensemble.py` | surveyed |
| Post-select checks | `stage4_interview_round.py:3575-3743` | surveyed |
| Reject runtime | `stage4_reject_runtime.py` | surveyed |
| Retry runtime | `stage4_retry_runtime.py` | surveyed |
| DB persistence | `db_manager.py`, `db_bootstrap_runtime.py` | surveyed |
| Pass rate monitor | `pass_rate_monitor.py` | surveyed |
| Episode production JSONL | `stage4_interview_round.py`, `stage4_orchestrator.py` | surveyed |
| Runtime audit JSONL | `audit_service.py` | surveyed |
| Session logger | `session_logger.py` | surveyed |
| Console operator path | `console.txt` cross-reference | surveyed |
| Stage 2/3 DB parity | `stage2_finalizer.py`, `stage3_orchestrator.py` | surveyed |

## 3. Static Watchlist

| Item | Risk | Status |
|---|---|---|
| Director verdict DB write timing | DB truth diverges from runtime truth after post-select downgrade | confirmed in code |
| `failure_category` NULL on post-select | Prevents failure analytics grouping | confirmed in code + DB |
| `fix_pack` missing in downgrade snapshot | Cascades to `missing_patch_targets` on next round | confirmed in code |
| `retry_directives` unbounded growth | LLM context pollution, DB bloat | confirmed in code + console |
| Stage 2/3 rationale field gaps | Thinner forensic surface for earlier stages | confirmed in code + DB |
| `session_decisions` ghost sink | Audit completeness claim for non-existent writer | confirmed in code |
| Quality gate downgrade `error_category` loss | If PASS downgraded by quality gate, `error_category` may not reach DB | confirmed in code |

## 4. Live Evidence Snapshot

### 4.1 Console Truth (run terminal state: stopped)

Episode 3 Director verdict sequence:

| Round | Director Verdict | Score | Gate | Post-Select | Final |
|---|---|---|---|---|---|
| 1 | REJECT | 44 | continuity_firewall | N/A | REJECT |
| 2 | PASS_WITH_FIX | 90 | director_primary_pass | continuity+history conflict | REJECT |
| 3 | PASS | 95 | director_primary_pass | continuity+history conflict | REJECT |
| 4 | PASS | 95 | director_primary_pass | history conflict | REJECT |
| 5 | (aborted mid-generation) | — | — | — | — |

Key console observations:
- `console.txt:1025`: `Director 판정: PASS (초기: PASS, 점수: 95, 선택: 후보 A)` — R4 Director PASS
- `console.txt:1037`: `[A-3] 1 post-select conflicts detected -> downgrade to REJECT` — immediate REJECT
- `console.txt:1061`: `Fix Pack patch_targets is empty` — Lane3 Gate widening on R4
- `console.txt:1135`: `[QR-7] 점수 plateau` — score stuck at 95 across rounds

### 4.2 DB Truth (projects/0_0323)

`stage_attempts` table:
- Stage 2: 1 row, `failure_category=NULL`, `initial_verdict=NULL`
- Stage 3: 4 rows, all `failure_category=NULL`, all `initial_verdict=NULL`
- Stage 4: 7 rows, `failure_category=NULL` on all rows, `initial_verdict` set on 3 rows

`director_selections` table:
- 11 rows total (6 unique Stage 4 attempt_keys)
- 1 Stage 4 `stage_attempts` row has no matching `director_selections` row

`attempt_raw_rationale` table:
- `director_thinking` lengths: ~2.9K → 4.2K (growing per round)
- `advisory_warnings_raw` lengths: ~1.3K → 2.1K

### 4.3 JSONL Truth

`pass_rate_monitor.json`:
- 11 records, Stage 4 only
- Contains `error_category` field (separate from DB `failure_category`)
- `fix_pack_ready = False`, `fix_pack_reason = missing_patch_targets` on rounds 3-4

`episode_production.jsonl`:
- Escalation events for Stage 4 only
- No Stage 2/3 writers found

`runtime_audit.jsonl`:
- Append-only events: `v60_25_auto_correct`, `db_commit`, `v60_10_state_extracted`
- No per-attempt verdict records

## 5. Top Provisional Findings

### F-1. Post-Select Downgrade Verdict Not Written Back to DB

**Severity**: P1
**Fix type**: `execution-fix`
**Evidence type**: `static+live`
**Run relevance**: Directly explains DB vs console divergence on rounds 2-4 of Episode 3.

**Mechanism**:
1. `stage4_interview_round.py:2306-2327`: `save_director_selection()` writes initial Director verdict to DB
2. `stage4_interview_round.py:3575-3743`: `_run_post_select_checks()` called AFTER DB write
3. `stage4_interview_round.py:3685`: `verdict = "REJECT"` downgrade
4. No DB update after line 3685 — downgrade stored only in loop-local `previous_attempt` dict

**Impact**: DB shows Director PASS; runtime used REJECT. Analytics queries see stale verdicts.

### F-2. Post-Select Downgrade Missing `fix_pack` in `previous_attempt`

**Severity**: P1
**Fix type**: `contract-cleanup`
**Evidence type**: `static+live`
**Run relevance**: Directly explains empty `patch_targets` on rounds 3-4 and Lane3 Gate widening.

**Mechanism**:
1. `stage4_interview_round.py:3714-3741`: Post-select downgrade builds `previous_attempt` dict — NO `fix_pack` key
2. `stage4_retry_runtime.py:840-842`: `owner._evaluate_fix_pack_contract(previous_attempt.get("fix_pack"))` → gets `None`
3. `stage4_interview_round.py:1675-1676`: `missing_patch_targets` returned
4. `stage4_reject_runtime.py:457-464`: Lane3 Gate widening to partial
5. If consecutive: `stage4_retry_runtime.py:852-858`: escalation to full rewrite

**Impact**: Retry loop burns rounds without actionable patch targets after any post-select downgrade.

### F-3. `failure_category` NULL on Stage 4 Post-Select REJECT

**Severity**: P1
**Fix type**: `contract-cleanup`
**Evidence type**: `static+live`
**Run relevance**: All 7 Stage 4 rows in 0_0323 DB have `failure_category = NULL`.

**Mechanism**:
- `stage4_interview_round.py:3697-3703`: `error_category` IS correctly set to `POST_SELECT_CONTINUITY_CONFLICT` etc.
- `stage4_interview_round.py:3736`: `error_category` IS included in `previous_attempt` dict
- `stage4_interview_round.py:5647`: `failure_category: failure_category or None` — maps from `error_category` param
- Gap: The `error_category` set at post-select downgrade must reach the `_save_stage4_db_attempt()` call (L5806). The propagation path through `_finalize_round_outcome()` → `_handle_reject()` → `stage4_reject_runtime.py` must preserve it.
- `stage4_reject_runtime.py:119-127`: Fallback derivation fires only `if not error_category and _reject_bucket` — if error_category was already set from post-select, this won't trigger, but the final mapping to `failure_category` can still lose it if the DB save call doesn't receive the correct value.

### F-4. Stage 2/3 DB Rationale Parity Gap

**Severity**: P1
**Fix type**: `contract-cleanup`
**Evidence type**: `static+live`
**Run relevance**: Non-blocking, but 0_0323 DB Stage 2/3 rows are diagnostically thin.

**Stage 3 gaps** (`stage3_orchestrator.py:1860`, `stage3_orchestrator.py:2635`):
- Does NOT pass: `selection_reason`, `verdict_reason`, `open_review`, `fix_scope_reasoning`, `runtime_advisory`, `retry_directives`, `initial_verdict`, `failure_category`

**Stage 2 gaps** (`stage2_finalizer.py:2691`, `stage2_finalizer.py:2829`):
- Does NOT pass: `initial_verdict`, most rationale fields
- `stage2_finalizer.py:2837`: Still slices `reject_reason[:500]` — direct max-retention policy violation

### F-5. `retry_directives` Unbounded Accumulation

**Severity**: P1
**Fix type**: `contract-cleanup`
**Evidence type**: `static+live`
**Run relevance**: Retry directives grew 1346 → 3062 → 3842 chars across Episode 3 rounds.

**Mechanism**:
- `stage4_interview_round.py:590-650`: `prev_general_lines` extracts all non-system lines from `director_feedback`
- `stage4_interview_round.py:648-650`: `retry_directives = "\n".join(prev_general_lines)` — no cap
- `stage4_interview_round.py:659`: Wrapped as `[R{round_num-1} 이전 지시] {retry_directives}`
- `stage4_interview_round.py:420`: `_compact_text(..., limit=None)` — explicitly uncapped

**Impact**: LLM context pollution on later rounds; DB/JSONL field bloat.

### F-6. Quality Gate Downgrade `error_category` May Not Reach DB

**Severity**: P1
**Fix type**: `contract-cleanup`
**Evidence type**: `static-only`
**Run relevance**: Not triggered in current run (all quality-gated scores were above threshold), but structurally present.

**Mechanism**:
- `stage4_interview_round.py:3794-3797`: PASS downgraded to REJECT, `error_category = "QUALITY_FLOOR_FAIL"`
- Line 3808: `if verdict in ("PASS", "PASS_WITH_FIX")` is now False → skips `_process_positive_verdict`
- The return path at line 3831-3834 includes `trace_meta` but `error_category` must be included in `trace_meta` or returned separately
- If `trace_meta` does not include `error_category`, it gets lost before reaching `_finalize_round_outcome()`

### F-7. `session_decisions` Ghost Sink Declaration

**Severity**: P2
**Fix type**: `comment-only`
**Evidence type**: `static-only`
**Run relevance**: No functional impact, but misleads audit coverage claims.

**Location**: `modules/core/services/audit_service.py:37` declares `"session_decisions"` as authoritative attempt sink, but no JSONL writer for this sink exists in the codebase.

### F-8. Pass Rate Monitor Stage 2/3 Coverage Gap

**Severity**: P2
**Fix type**: `observability-only`
**Evidence type**: `static+live`
**Run relevance**: 0_0323 `pass_rate_monitor.json` contains 0 Stage 2/3 records.

Only `stage4_interview_round.py:5748` calls `pass_rate_monitor.record_attempt()`. Stage 2/3 orchestrators do not record to this sink.

### F-9. Logging Truncation Caps on Secondary Paths

**Severity**: P2
**Fix type**: `observability-only`
**Evidence type**: `static-only`
**Run relevance**: Non-blocking, but reduces post-run forensic quality.

Residual truncation caps found:
- `stage4_reject_runtime.py:485`: ToT output `[:1000]`
- `stage4_reject_runtime.py:499`: MAD output `[:1000]`
- `stage4_reject_runtime.py:600,602`: Reaudit feedback `[:2000]`, `[:1000]`
- `stage4_interview_round.py:5369-5370`: secondary logging caps
- `stage3_orchestrator.py:2260-2263`: Stage 3 logging caps

## 6. Stale-vs-Live Corrections

| Prior Claim | Source | Correction |
|---|---|---|
| "Director and post-select are split-brain" | bottleneck remediation plan | **STALE.** The pre-rerun root-cause merge audit already reclassified this as defense-in-depth by design. Current code confirms post-select downgrade is intentional, not malfunction. The issue is persistence parity, not decision logic. |
| "Stage 4 simply cannot write" | earlier surveys | **STALE.** Ep1 and Ep2 passed on attempt 1. The bottleneck is narrower: scene structure, timeline contamination, and retry inefficiency. |
| "`CONDITIONAL_PASS` from V60.97 is not treated as positive downstream" | Q3 R2 merge audit | **NEEDS VERIFICATION.** Current code at `director_ensemble.py:1187-1204` appears to resolve CONDITIONAL_PASS exhaustively. All branches set `final_verdict` to PASS or REJECT. The R2 Q3 finding may reflect an edge case in adaptive_result flow that requires targeted micro-test confirmation. |
| "Stage 2 `reject_reason[:500]` truncation" | Q8 R2 merge audit | **STILL LIVE.** `stage2_finalizer.py:2837` still slices `reject_reason[:500]`. |

## 7. Highest-ROI Fixes After Run

### Fix 1. Include `fix_pack` in Post-Select Downgrade `previous_attempt`

**Why first**: This is the direct mechanical cause of empty `patch_targets` on retry rounds after post-select REJECT. The Lane3 Gate widening cascade (console.txt:1061) burns rounds without meaningful patches.

**Targets**:
- `stage4_interview_round.py:3714-3741`: Add `"fix_pack": director_result.get("fix_pack")` to the downgrade `previous_attempt` dict

**Expected impact**: Retry rounds after post-select downgrade will have actionable patch_targets, reducing rounds-to-resolution.

### Fix 2. Stage 2/3 `save_stage_attempt()` Rationale Parity

**Why second**: Biggest remaining DB-truth asymmetry after the max-retention wave. Bounded, low-risk, high forensic value.

**Targets**:
- `stage3_orchestrator.py:1860,2635`: Pass `initial_verdict`, `failure_category`, `selection_reason`, `verdict_reason` to `save_stage_attempt()`
- `stage2_finalizer.py:2691,2829,2837`: Pass `initial_verdict`; remove `[:500]` truncation on `reject_reason`

### Fix 3. `failure_category` Propagation to DB for Post-Select Downgrades

**Why third**: Enables failure analytics grouping. Currently all Stage 4 rows have `failure_category = NULL`.

**Targets**:
- Verify the `error_category` set at `stage4_interview_round.py:3697-3703` reaches `_save_stage4_db_attempt()` at L5806 as `failure_category`
- Verify quality gate downgrade at L3797 also propagates to DB

## 8. Confidence And Limits

**Estimated confidence: 95%**

**Basis**:
- All primary scope files were read and the verdict/persistence/retry paths were traced end-to-end
- Console truth, DB truth, and JSONL truth from 0_0323 were cross-referenced against code paths
- Post-select downgrade flow was traced through director_runtime → interview_round → reject_runtime → retry_runtime
- Prior survey findings (pre-rerun root-cause, Q1-Q8 R2) were checked against current live code

**Limits**:
- Exact `failure_category` propagation through all intermediate functions was traced by pattern, not line-by-line execution. A targeted micro-test would confirm the precise path.
- The `CONDITIONAL_PASS` edge case needs a micro-test to confirm whether any adaptive_result branch can bypass the exhaustive conversion at director_ensemble.py:1187-1204.
- DB truth was examined via agent queries, not direct SQL on the live database file.
- The run was user-aborted, so full-cycle evidence (completion of episode 3) is unavailable.

**Rerun blocker assessment**: This lane does NOT contain a probable rerun blocker in the crash or data-loss sense. The fixes are efficiency and observability improvements that would make the next rerun more diagnostic and reduce wasted retry rounds.
