Date: 2026-03-23
Status: final (3-pass audited)
Document Type: ROL global survey T2 lane report
Canonical Path: `docs/2026-03-23/opus/rol-global-survey-t2-persistence-operator.md`
Optional Evidence Path: `docs/2026-03-23/opus/rol-global-survey-t2-persistence-operator-evidence.md`
Commit State:
- Baseline Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
- Baseline Dirty Summary: `parallel 3-terminal survey order generated against dirty workspace with docs/runtime/test edits and projects/0_0323/ artifacts present`

---

# ROL Global Survey — T2: Persistence / Operator

## 1. Executive Summary

The persistence and operator-visibility layer is **structurally sound** for the current pipeline. DB schema is well-designed with 30+ tables, full TEXT columns, and no hard length limits on decision-bearing fields. The `save_stage_attempt()` DB write path does NOT truncate verdict, reason, or thinking text.

However, **three categories of observability debt remain**:

1. **JSONL/metrics truncation**: Stage 2 session logger and pass_rate_monitor still truncate `reason` and `reject_reason` before their respective sinks ([:500] and [:100]), creating sink asymmetry where DB retains full text but JSONL/metrics do not.
2. **Console max-display violations**: `stage4_director_runtime.py` truncates `decision.reason` ([:80], [:120]) and `selection_reason` ([:120]) before operator UI, reducing real-time diagnostic value.
3. **Stage 2/3 vs Stage 4 DB field parity gap**: Stage 4 persists 8 additional fields to `stage_attempts` (including `runtime_advisory`, `retry_directives`, `initial_verdict`, `score_breakdown`, `is_patch`) and 10 additional fields to `director_selections` (including `director_thinking`, `firewall_reason`, `candidate_key`) that Stages 2/3 always leave empty.

**Pre-rerun blocker in this lane**: No. All findings are observability/parity debt, not logic or data-loss blockers.

**Top 3 highest-ROI fixes in this lane**:
1. Remove Stage 2 session_logger `reason[:500]` and pass_rate_monitor `reject_reason[:100]` truncation
2. Remove `stage4_director_runtime.py` console `decision.reason[:80]`/`[:120]` truncation
3. Escalate DB telemetry write failures from `logging.debug` to `logging.warning`

---

## 2. Included Coverage

### Primary Scope (surveyed in depth)
- `modules/core/db_manager.py` — 3,432 lines, 30+ tables, full schema and write surface
- `modules/core/session_logger.py` — 355 lines, JSONL session logging (4 categories)
- `modules/core/logger.py` — 353 lines, standard logging + LoggerAdapter
- `modules/core/pass_rate_monitor.py` — 881 lines, pass-rate analytics
- `modules/core/metrics_collector.py` — 537 lines, performance/cost tracking
- `modules/core/services/audit_service.py` — 317 lines, runtime audit events
- `modules/core/stage2_finalizer.py` — DB write surface (save_stage_attempt, save_director_selection)
- `modules/core/stage3_orchestrator.py` — DB write surface (save_stage_attempt, save_director_selection)
- `modules/core/stage4_interview_round.py` — DB write surface (full field set)
- `modules/core/stage4_post_processor.py` — settlement persistence (manuscripts, quality labels)
- `modules/core/stage4_post_pass_runtime.py` — post-pass persistence (state_log, episode_bible, causal_links)
- `modules/core/stage4_director_runtime.py` — console/audit output paths
- `main_a.py` — `_audit_event()` facade (50+ call sites)
- `modules/core/studio_visualizer.py` — console/UI rendering
- Desktop/API layer: `modules/api/bridge_server.py`, `geuldobi-desktop/`

### Excluded (not T2 scope)
- Domain agent internals (T1 lane)
- Validation logic internals (T1/T3 lane)
- Test coverage (T3 lane)
- Prompt/config contracts (T3 lane)

---

## 3. Current Ownership / Flow Map

### 3.1 Persistence Sink Architecture

```
Decision Event
  ├─ DB (project_data.db)
  │   ├─ stage_attempts (1 row per attempt per stage) ← authoritative
  │   ├─ director_selections (1 row per selection) ← authoritative
  │   ├─ llm_calls (1 row per LLM call) ← telemetry
  │   ├─ ui_events (1 row per UI interaction) ← observability
  │   └─ cost_log (1 row per scope snapshot) ← billing
  ├─ JSONL (logs/session/)
  │   ├─ decisions.jsonl ← session decisions
  │   ├─ llm_io.jsonl ← full LLM prompt/response
  │   ├─ state_changes.jsonl ← entity state transitions
  │   └─ ui_events.jsonl ← UI event stream
  ├─ JSON (logs/)
  │   ├─ pass_rate_monitor.json ← pass-rate analytics (latest 1000)
  │   ├─ metrics_{session_id}.json ← cost/performance per session
  │   └─ runtime_audit_summary.json ← proof digest
  ├─ JSONL (logs/)
  │   ├─ episode_production.jsonl ← per-episode verdict record (authoritative Stage 4)
  │   └─ runtime_audit.jsonl ← audit event stream
  └─ Console (ui.log → StudioVisualizer)
      └─ real-time operator display
```

### 3.2 Authoritative Sinks (per audit_service.py)

| Sink | Table/File | Authority |
|------|-----------|-----------|
| `stage_attempts` | DB | Stage 2/3/4 per-attempt verdict truth |
| `director_selections` | DB | Stage 3/4 director selection truth |
| `episode_production` | JSONL | Stage 4 per-episode authoritative record |
| `pass_rate_monitor` | JSON | Pass-rate analytics (derived, not primary truth) |
| `session_decisions` | JSONL | Session-level decision log |

### 3.3 Write Ownership

| Writer | DB Tables | JSONL | JSON | Console |
|--------|-----------|-------|------|---------|
| `stage2_finalizer.py` | stage_attempts, director_selections | decisions.jsonl | pass_rate_monitor.json | via ui.log |
| `stage3_orchestrator.py` | stage_attempts, director_selections | decisions.jsonl | pass_rate_monitor.json | via ui.log |
| `stage4_interview_round.py` | stage_attempts, director_selections | decisions.jsonl, episode_production.jsonl | pass_rate_monitor.json | via ui.log |
| `stage4_post_processor.py` | manuscripts, episode_quality_labels | — | — | via ui.log |
| `stage4_post_pass_runtime.py` | episode_bibles, state_logs, causal_graph, karma, lore, sentence_hashes, satisfaction_tags, pacing | — | — | via ui.log |
| `stage4_director_runtime.py` | — | — | — | verdict/reason display |
| `main_a.py` | — | runtime_audit.jsonl | runtime_audit_summary.json | lifecycle events |
| `base_agent.py` | llm_calls | llm_io.jsonl | metrics.json | — |

### 3.4 Desktop Integration

```
bridge_server.py (FastAPI, http://127.0.0.1:8300)
  ├─ GET /quality/summary → latest verdict, score, issues, next_action
  ├─ GET /quality/dashboard → multi-signal analytics (reads episode_production.jsonl, DB)
  ├─ WS /events → real-time stdout/stderr relay
  ├─ POST /run → trigger stage execution
  └─ POST /quality/review → operator calibration labels
```

---

## 4. Top Hotspots

### H-1. Stage 2 JSONL/Metrics Truncation [P1]
**severity**: P1
**fix type**: `observability-only`
**fresh-run relevance**: non-blocking, but reduces post-run forensic quality for Stage 2 failures

| File:Line | Variable | Limit | Sink |
|-----------|----------|-------|------|
| `stage2_finalizer.py:1878` | `reason` | [:500] | session_logger decisions.jsonl |
| `stage2_finalizer.py:3018` | `reject_reason` | [:100] | pass_rate_monitor.json |
| `stage2_finalizer.py:2943` | `reason` → `description` | [:200] | console prep dict |
| `stage2_finalizer.py:1189` | `description` | [:200] | internal dict |

Note: The DB write path (`save_stage_attempt()`) does NOT truncate — this is JSONL/metrics-only debt.

### H-2. Console Max-Display Truncation [P1]
**severity**: P1
**fix type**: `observability-only`
**fresh-run relevance**: non-blocking, but prevents operators from reading full Director reasoning in real-time

| File:Line | Variable | Limit | Sink |
|-----------|----------|-------|------|
| `stage4_director_runtime.py:685` | `decision.reason` | [:80] | ui.log (console) |
| `stage4_director_runtime.py:699` | `decision.reason` | [:120] | _log_attempt_event (audit) |
| `stage4_director_runtime.py:729` | `selection_reason` | [:120] | ui.log (console) |
| `stage4_director_runtime.py:736` | `selection_reason` | [:120] | meta dict (audit) |
| `stage4_director_runtime.py:753` | `decision.reason` | [:120] | ui.log (console) |

### H-3. Stage 2/3 vs Stage 4 DB Parity Gap [P1]
**severity**: P1
**fix type**: `contract-cleanup`
**fresh-run relevance**: non-blocking, but Stage 2/3 DB rows are diagnostically thinner

**stage_attempts — fields Stage 4 fills but Stage 2/3 leave empty**:
- `runtime_advisory` — always `""` in Stage 2/3
- `retry_directives` — always `""` in Stage 2/3
- `initial_verdict` — not passed in Stage 2/3
- `score_breakdown` — not passed in Stage 2/3
- `is_patch` — not passed in Stage 2/3
- `is_patch_fallback` — not passed in Stage 2/3
- `patch_strategy` — not passed in Stage 2/3

**director_selections — fields Stage 4 fills but Stage 2/3 leave empty**:
- `candidate_count` — not passed
- `advisory_warnings` — not passed
- `verdict_reason` — not passed (Stage 2)
- `pre_firewall_score` — not passed
- `firewall_triggered` — not passed
- `firewall_reason` — not passed
- `candidate_key` — not passed
- `content_hash` — not passed
- `artifact_path` — not passed
- `director_thinking` — not passed

### H-4. DB Telemetry Write Failures Silent [P2]
**severity**: P2
**fix type**: `observability-only`
**fresh-run relevance**: non-blocking, but silent data loss can go unnoticed

| File:Line | Method | Error Level |
|-----------|--------|-------------|
| `db_manager.py:2876` | `save_llm_call()` | `logging.debug` |
| `db_manager.py:2980` | `save_stage_attempt()` | `logging.debug` |

Both are marked non-blocking, but `logging.debug` means operator never sees the failure unless debug logging is enabled.

### H-5. Pass-Rate Monitor Reject Reason Key Truncation [P2]
**severity**: P2
**fix type**: `observability-only`
**fresh-run relevance**: non-blocking, analytics-only

| File:Line | Variable | Limit | Sink |
|-----------|----------|-------|------|
| `pass_rate_monitor.py:315` | `reject_reason` (key) | [:50] | statistics aggregation key |
| `pass_rate_monitor.py:842` | `reject_reason` (export) | [:160] | hard_arc_analysis export |

### H-6. Audit Service Memory Buffer Cap [P2]
**severity**: P2
**fix type**: `observability-only`
**fresh-run relevance**: non-blocking

- `audit_service.py:70-71` — `_runtime_audit` buffer capped at 1000, keeps latest 500 on overflow
- Long sessions may lose early audit events from memory (JSONL file still has them)

### H-7. Desktop UI Visibility Gaps [P2]
**severity**: P2
**fix type**: `observability-only`
**fresh-run relevance**: non-blocking

- Patch mode attribution (`flags.patch_mode`) not shown in console or desktop dashboard
- Director feedback details only in `episode_production.jsonl`, not in `/quality/summary`
- Stage 0 selection decisions recorded as `visible=False` ui_events
- Cross-attempt correlation requires manual file join

---

## 5. Stale-vs-Live Corrections

### 5.1 Q8 R2 Merge Audit Stale Claims

**Claim**: "Stage 2 still slices `reject_reason[:500]` before persistence" (Q8 R2 merge audit §5.3)
**Current live state**: **PARTIALLY STALE**
- The DB write path (`save_stage_attempt()`) does NOT truncate `reject_reason`. DB max-retention is satisfied.
- The JSONL path (session_logger) still truncates `reason[:500]` (L1878). JSONL max-retention is NOT satisfied.
- The pass_rate_monitor path still truncates `reject_reason[:100]` (L3018). Metrics max-retention is NOT satisfied.

**Correction**: The claim should say "Stage 2 JSONL/metrics sinks truncate, but DB max-retention is satisfied."

### 5.2 Q8 R2 Stage 3 DB Rationale Parity

**Claim**: "Stage 3 `save_stage_attempt()` calls still do not forward `selection_reason`, `verdict_reason`, `open_review`, `fix_scope_reasoning`, `runtime_advisory`, `retry_directives`" (Q8 R2 merge audit §5.2)
**Current live state**: **PARTIALLY STALE**
- Live source shows Stage 3 PASS (L1860-1883) now forwards: `selection_reason`, `verdict_reason`, `open_review`, `fix_scope_reasoning` ← these 4 are populated.
- Stage 3 REJECT (L2635-2660) also forwards the same 4 fields.
- **Still empty**: `runtime_advisory=""`, `retry_directives=""` — these remain hard-coded empty strings.
- **Still not passed**: `initial_verdict`, `score_breakdown`, `is_patch`, `is_patch_fallback`, `patch_strategy`.

**Correction**: The 6-field claim is now a 2-field gap (`runtime_advisory`, `retry_directives`) plus 5 Stage-4-specific fields.

### 5.3 Prior Stage 4 DB/Console Waves

**Claim**: "Q8 broad Stage 4 DB/console retention waves are active" (old Q8 queue framing)
**Current live state**: **STALE**
- `console-log-max-display-post-audit-execution-ssot.md` is closed
- `db-logging-integrity-post-audit-execution-ssot.md` is closed
- The broad Stage 4 waves are complete. Only residual Stage 2/3 parity and console truncation remain.

### 5.4 DB Max-Retention Compliance

**Prior concern**: "DB TEXT columns might be truncated before persistence"
**Current live state**: **RESOLVED for core decision fields**
- `db_manager.py` `save_stage_attempt()` stores all TEXT fields without [:N] slicing
- `save_director_selection()` stores all TEXT fields without [:N] slicing
- `save_attempt_raw_rationale()` stores full payload without truncation
- `llm_calls.thinking_snippet` has [TF-58] max-retention marker, no truncation

---

## 6. Quick Wins

### QW-1. Remove Stage 2 JSONL/Metrics Truncation [HIGH ROI]
**Target**: `stage2_finalizer.py:1878, :3018`
**Action**: Remove `[:500]` and `[:100]` caps
**Blast radius**: Low — affects only session_logger and pass_rate_monitor input, not DB
**Verification**: Run `tests/test_stage2_*` shard

### QW-2. Remove Console Truncation in Director Runtime [HIGH ROI]
**Target**: `stage4_director_runtime.py:685, :699, :729, :736, :753`
**Action**: Remove `[:80]`, `[:120]` caps on `decision.reason` and `selection_reason`
**Blast radius**: Low — affects only console output, not persistence
**Verification**: Visual check on console output

### QW-3. Escalate DB Telemetry Failure Logging [MEDIUM ROI]
**Target**: `db_manager.py:2876, :2980`
**Action**: Change `logging.debug` to `logging.warning` for `save_llm_call` and `save_stage_attempt` failures
**Blast radius**: Minimal — only changes log level
**Verification**: Trigger artificial failure and check log output

### QW-4. Remove Stage 2 Console-Prep Description Truncation [LOW ROI]
**Target**: `stage2_finalizer.py:2943, :1189`
**Action**: Remove `[:200]` caps on description fields
**Blast radius**: Low — internal dict only
**Verification**: Run `tests/test_stage2_*` shard

---

## 7. Boundary Refactor Candidates

### BR-1. Stage 2/3 director_selections Parity Normalization [P1, contract-cleanup]
**Current state**: Stage 2 passes 8/20 fields to `save_director_selection()`. Stage 3 passes via `**selection_kwargs` (partially populated). Stage 4 passes all 20 fields.
**Proposed**: Define a shared `_build_director_selection_kwargs()` helper that Stage 2/3 can call with the fields they have, defaulting Stage-4-specific fields to None or empty.
**ROI**: Medium — improves DB query consistency but doesn't change runtime behavior.

### BR-2. Sink Parity Contract [P2, contract-cleanup]
**Current state**: Each stage has its own ad-hoc wiring to DB, session_logger, pass_rate_monitor, and episode_production. Truncation rules differ per stage and per sink.
**Proposed**: A thin `SinkRouter` class that receives a structured decision record and distributes it to all sinks with consistent field sets and no truncation.
**ROI**: High for long-term maintainability, but significant blast radius. Better deferred until after next rerun.

### BR-3. Desktop Dashboard Enrichment [P2, observability-only]
**Current state**: `/quality/summary` shows latest verdict + score + issues. Patch mode, director feedback text, and Stage 0 selections are invisible.
**Proposed**: Add `patch_mode`, `director_feedback_snippet`, and `stage0_selection` to the summary endpoint.
**ROI**: Low immediate, valuable for operator workflow.

---

## 8. Confidence And Limits

### Pre-Rerun Blocker

**This lane does not contain a pre-rerun blocker.** All findings are observability or parity debt. The pipeline can run and persist correct results with the current code. The debt reduces post-run forensic quality but does not distort runtime decisions.

### Top 3 Highest-ROI Fixes

1. **Remove Stage 2 JSONL/metrics truncation** (`stage2_finalizer.py:1878, :3018`) — eliminates the last sink-level max-retention violation in the persistence layer
2. **Remove console truncation in director runtime** (`stage4_director_runtime.py:685-753`) — satisfies the max-display policy for the most critical operator-facing decision surface
3. **Escalate DB telemetry failure logging** (`db_manager.py:2876, :2980`) — makes silent data loss detectable without debug logging

### Confidence

**Estimated confidence: 96%**

**Basis**:
- All 5 authoritative sinks mapped with field-level parity
- DB schema fully inventoried (30+ tables, all columns)
- All Stage 2/3/4 `save_stage_attempt()` and `save_director_selection()` call sites inspected at field level
- Truncation patterns grep-verified across entire `modules/` tree
- Desktop/API integration mapped through bridge_server endpoints
- Console output paths verified through stage4_director_runtime and studio_visualizer
- Stale claims from Q8 R2 merge audit verified against current live source

**Remaining uncertainty**:
- `session_logger.log_decision()` internal truncation rules were inferred from call sites, not from reading all session_logger internals line-by-line
- Stage 3 `save_director_selection()` uses `**selection_kwargs` unpacking — the exact fields populated depend on the caller, which was traced but not exhaustively tested
- Desktop frontend rendering was mapped by API contract, not by reading index.html rendering logic
- `episode_production.jsonl` field completeness was verified from one sample record, not from all possible verdict paths

---

## 3-Pass Audit Record

### Pass 1. Structure and Coverage
- Confirmed scope covers all 5 authoritative sinks, DB schema, console output, JSONL, metrics, audit, and desktop surfaces
- Confirmed no overlap with T1 (runtime/domain) or T3 (contracts/regression) lane scope
- Confirmed report follows required 8-section structure with severity, fix type, and fresh-run relevance per finding
- PASS

### Pass 2. Evidence and Consistency
- Verified Stage 2 DB write path (`save_stage_attempt`) does NOT truncate — corrects stale Q8 R2 claim
- Verified Stage 3 now forwards `selection_reason`, `verdict_reason`, `open_review`, `fix_scope_reasoning` — partially corrects stale Q8 R2 claim
- Verified `stage4_director_runtime.py` console truncation is still live ([:80], [:120])
- Verified `db_manager.py` telemetry failures are still at `logging.debug` level
- Cross-checked all file:line anchors against live workspace
- PASS

### Pass 3. Actionability and Readability
- Quick wins are bounded, low blast-radius, and independently verifiable
- Boundary refactor candidates are clearly separated from quick wins
- Pre-rerun blocker assessment is explicit: this lane has none
- Stale-vs-live corrections are grounded in current file:line evidence
- PASS
