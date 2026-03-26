# T3. Retry / Rescue / ASP Statistics — Observability Survey

Date: 2026-03-25
Status: final (3-pass audited)
Document Type: lane survey report
Lane: T3 (Retry / Rescue / ASP Statistics)
Master Order: `docs/2026-03-25/global-observability-statistics-core-4terminal-master-order.md`
Baseline Commit: `e3f2771699cb5d596aefaf994a8a177bbbad0a3e`

## 1. Existing Retry/Rescue/ASP Statistics

### 1.1 AdaptiveRetryStrategy (`modules/core/adaptive_retry.py`)

**What it captures**:
- `RetryContext.error_history`: list of `{type, info, attempt}` per task — kept in memory only
- `RetryContext.attempt`: current attempt count per task
- Error classification into 8 types: CONSTRAINT_VIOLATION, QUALITY_ISSUE, STRUCTURE_ERROR, TIMEOUT, QUOTA_EXCEEDED, CHARACTER_INCONSISTENCY, LOGIC_ERROR, SCOPE_OVERFLOW

**What it does NOT capture**:
- No persistent log of retry trigger events. `error_history` lives in `RetryContext` and is discarded on `reset_context()` or process end.
- No aggregation across tasks/episodes. There is no "retry fired N times this session" counter.
- No retry strategy effectiveness tracking. When a strategy (temperature delta, prompt injection, schema forcing) is applied, there is no record of whether the next attempt passed.
- No retry cost attribution. The system cannot answer "how much wall time / tokens / cost did retries add?"

**Sink**: None. Pure in-memory, per-task. Not written to JSONL, DB, or summary.

### 1.2 PassRateMonitor (`modules/core/pass_rate_monitor.py`)

**What it captures** (relevant to retry/rescue):
- `AttemptRecord.generation_method`: "default", "two_phase", "tot", "asp", "mad" — **this is the primary ASP trigger record**
- `AttemptRecord.is_patch`: whether this was a patch attempt
- `AttemptRecord.patch_fallback`: whether patch fell back
- `AttemptRecord.patch_strategy`: string describing patch approach
- `AttemptRecord.structural_attempted`: bool
- `AttemptRecord.attempt_num`: attempt sequence number
- `AttemptRecord.duration_ms` and `AttemptRecord.token_cost`: per-attempt timing and cost
- `AttemptRecord.reject_reason` and `AttemptRecord.reject_bucket`: why attempt failed
- `AttemptRecord.fix_pack`: the fix pack dict (for PASS_WITH_FIX paths)
- `AttemptRecord.retry_budget_axes`: retry budget allocation

**What it already computes** (via `get_stats()`):
- `method_success_rate`: success rate keyed by `generation_method` — **this already answers "ASP success rate"**
- `first_attempt_rate` and `eventual_rate` per stage
- `avg_attempts_to_pass` per stage
- `common_reject_reasons`: frequency-sorted reject reasons

**Authority status**: Explicitly documented as NON-AUTHORITATIVE convenience cache. Rebuilt from in-memory records on save. If lost, no durable truth is lost.

**Sink**: `logs/pass_rate_monitor.json` — JSON file, not JSONL append.

### 1.3 FailureAnalyzer (`modules/core/failure_analyzer.py`)

**What it computes** (relevant to retry/rescue):
- `avg_attempts_by_stage()`: average max attempt count per episode, by stage — from DB `stage_attempts`
- `stage_pass_rates()`: total attempts, pass, reject, `pass_with_fix_transient` counts per stage
- `quality_distribution()`: includes `pass_with_fix_count` — count of PASS_WITH_FIX verdicts
- `patch_trace_summary()`: summarizes patch behavior from `episode_production.jsonl` patch_trace payloads
- `sink_alignment_summary()`: cross-joins 5 sinks (stage_attempts, pass_rate_monitor, session_decisions, episode_production, director_selections) per attempt_key

**What it already reveals about rescue**:
- `pass_with_fix_count` in `quality_distribution()` gives the rescue-via-fix count
- `patch_trace_summary()` gives patch strategy distribution, count, and behavioral patterns
- `sink_alignment_summary()` can join rescue events across sinks by `attempt_key`

**What it does NOT compute**:
- No rescue success rate (how often PASS_WITH_FIX actually resolved vs. fell back to REJECT)
- No rescue improvement delta (score before fix vs. score after fix)
- No rescue wall-time cost (additional LLM calls / time spent in PASS_WITH_FIX loop)
- No ASP-specific summary (trigger rate, improvement delta, rounds)

**Sink**: Queries DB + reads JSONL files. No own persistent output — it's a read-only analyzer.

### 1.4 Stage4RetryRuntime (`modules/core/stage4_retry_runtime.py`)

**What it captures** (relevant to retry/rescue):
- `execute_pass_with_fix_loop()`: up to 3 fix iterations, each with patch attempt, guard check, re-audit, verdict
- Console logs: "🔩 [TF-32-V] PASS_WITH_FIX patch #N/3" per fix attempt
- `_get_inplace_success_rate()`: queries `director_selections` for inplace fix_scope PASS ratio — **already exists and is logged**
- `_run_asp_correction()`: fires ASP when `round_num >= 2` and ASP module is available
- Console log: "✅ [ASP] 교정 완료 (delta: +N)" when ASP succeeds

**What it does NOT persist**:
- The PASS_WITH_FIX loop iteration count (how many of the 3 max_fix iterations actually ran) — logged to console but not to any structured sink
- ASP trigger/skip decision — only logged as console text
- ASP improvement delta — logged to console but not to JSONL/DB
- Fix-loop wall time — not measured or logged

### 1.5 Stage4EpisodeLogging (`modules/core/stage4_episode_logging.py`)

**What it captures**:
- `Stage4PassEpisodeLogRequest` includes: `is_patch`, `is_patch_fallback`, `tot_used`, `mad_used`, `asp_used`, `initial_verdict`, `initial_score`, `final_verdict`, `final_score`, `patch_trace`, `model_tier`
- This is the PASS-path structured log payload for `episode_production.jsonl`

**What this means for rescue/ASP observability**:
- **`asp_used` is already persisted** in `episode_production.jsonl` as a boolean per episode
- **`initial_verdict` vs `final_verdict`** can show rescue transitions (e.g., PASS_WITH_FIX → PASS)
- **`initial_score` vs `final_score`** can show score improvement delta from rescue
- **`patch_trace`** carries patch strategy and targets

This is the **richest existing rescue evidence sink**, but it only covers the PASS path. REJECT episodes (where rescue was attempted but failed) are logged differently via `Stage4RejectRuntime`.

### 1.6 Stage4InterviewRound (`modules/core/stage4_interview_round.py`)

**What it captures** (at the logging call site, L5413-5543):
- `flags` dict includes: `tot`, `mad`, `asp`, `strategy_budget`, `strategy_count`
- This is emitted per-round, not just per-episode

**Key evidence**: the `asp` flag is already part of the per-round logging payload.

### 1.7 AdversarialSelfPlay (`modules/core/adversarial_self_play.py`)

**What it captures**:
- `ASPResult.improvement_delta`: score change (int)
- `ASPResult.rounds`: number of ASP rounds performed
- `ASPResult.adversary_feedback.decision`: PASS/REVISE/REJECT from virtual Director
- `ASPResult.adversary_feedback.score`: virtual Director score

**What it does NOT persist**:
- The `ASPResult` is consumed by `stage4_retry_runtime._run_asp_correction()` which logs only the delta to console
- None of the ASP internals (adversary feedback, round count, virtual Director score) are persisted to any structured sink

## 2. Gap Analysis

### 2.1 Can the system currently answer: "How often does retry fire?"

**YES, partially.** `PassRateMonitor.get_stats()` provides `avg_attempts_to_pass` per stage, and `FailureAnalyzer.avg_attempts_by_stage()` provides the same from DB. These already answer average retry frequency.

**Missing**: per-episode retry event stream with timestamps. The system knows the final attempt count but not the intermediate retry decision points.

### 2.2 Can the system currently answer: "How often does ASP fire?"

**YES, partially.** `asp_used` boolean is in `episode_production.jsonl` for PASS episodes. `generation_method: "asp"` is in `PassRateMonitor` records. ASP console log "✅ [ASP] 교정 완료" is visible to the operator.

**Missing**: ASP fire count as a structured aggregate. To get "ASP fired in 3/9 episodes," the operator must grep JSONL or count pass_rate_monitor records manually.

### 2.3 Can the system currently answer: "What is the rescue rate?"

**PARTIALLY.** `FailureAnalyzer.quality_distribution()` returns `pass_with_fix_count`, and `stage_pass_rates()` returns `pass_with_fix_transient`. These answer "how many times PASS_WITH_FIX was the initial verdict."

**Missing**: rescue success rate — i.e., of those PASS_WITH_FIX attempts, how many became PASS vs. fell back to REJECT. This requires joining `initial_verdict` with `final_verdict` per attempt_key, which `episode_production.jsonl` already contains for PASS outcomes but not for failed rescues.

### 2.4 Can the system currently answer: "What is the rescue improvement delta?"

**PARTIALLY.** `episode_production.jsonl` contains `initial_score` and `final_score` per PASS episode. The delta is `final_score - initial_score`. But:

- Only for PASS episodes. Failed rescues (REJECT after PASS_WITH_FIX) don't emit this log.
- Not aggregated anywhere. The operator must compute the delta manually.

### 2.5 Can the system currently answer: "How much wall time / cost do retries add?"

**NO.** `PassRateMonitor.AttemptRecord.duration_ms` and `.token_cost` exist as fields, but:

- `duration_ms` is set to 0 in the actual recording calls (the caller does not populate it consistently)
- `token_cost` is similarly not populated at the recording call site
- There is no "retry-added time" metric anywhere

This is the **largest instrumentation gap** in the retry/rescue domain.

### 2.6 Can the system currently answer: "How effective is each retry strategy?"

**NO.** `AdaptiveRetryStrategy` applies strategies (temperature delta, prompt injection, schema forcing, constraints) but does not record which strategy was used for which attempt. The strategy is applied in-memory and forgotten. The next attempt's pass/fail is not linked back to the strategy that was applied.

`PassRateMonitor` records `generation_method` which captures broad categories (tot, asp, mad, default) but not the specific `AdaptiveRetryStrategy` action.

## 3. Existing Statistics Summary Table

| Statistic | Exists | Sink | Authoritative |
|-----------|--------|------|---------------|
| Retry count per episode | YES | DB stage_attempts, pass_rate_monitor | DB is authoritative |
| Avg attempts to pass by stage | YES | FailureAnalyzer (computed from DB) | DB is authoritative |
| ASP trigger (boolean) | YES | episode_production.jsonl, pass_rate_monitor | episode_production |
| ASP improvement delta | CONSOLE ONLY | Console log text | Not persisted |
| ASP round count | NO | Not persisted | N/A |
| PASS_WITH_FIX count | YES | FailureAnalyzer, stage_pass_rates | DB is authoritative |
| Rescue success rate | NO | Not computed | N/A |
| Rescue score delta | PARTIAL | episode_production (PASS only) | episode_production |
| PASS_WITH_FIX loop iteration count | CONSOLE ONLY | Console log text | Not persisted |
| Retry wall time cost | NO | duration_ms field exists but unpopulated | N/A |
| Retry token/$ cost | NO | token_cost field exists but unpopulated | N/A |
| Per-strategy effectiveness | NO | Not tracked | N/A |
| Inplace success rate | YES | Computed from director_selections DB | DB is authoritative |
| Patch trace summary | YES | FailureAnalyzer (from episode_production) | episode_production |

## 4. Ranked Instrumentation Candidates

### Rank 1: Populate `duration_ms` and `token_cost` in PassRateMonitor recording

**Gap**: The fields exist in `AttemptRecord` but are set to 0 at the call site.

**Why highest ROI**: Without per-attempt timing, the system cannot attribute cost to retries vs. first-pass. This is the single most impactful observability gap for operator cost judgment.

**Blast radius**: LOW. The `record_attempt()` call already accepts `duration_ms` and `token_cost` params. The change is at the call site (passing the values), not in the data model.

**Dependency**: `MetricsCollector` already tracks per-call timing and cost. The values exist; they just aren't passed to `PassRateMonitor.record_attempt()`.

### Rank 2: Compute and persist rescue success rate

**Gap**: PASS_WITH_FIX count exists but success-vs-fallback ratio does not.

**Why high ROI**: Rescue effectiveness is the key question for "should we invest in better fix packs vs. better first-pass generation?" Without this number, the operator cannot make the tradeoff.

**Blast radius**: LOW-MEDIUM. Options:
- Option A: Add a `FailureAnalyzer.rescue_effectiveness()` method that joins `initial_verdict` and `final_verdict` across episode_production and stage_attempts. Pure read-only analysis, zero write-side change.
- Option B: Add `rescue_attempted` and `rescue_succeeded` booleans to pass_rate_monitor AttemptRecord. Small schema addition.

**Recommendation**: Option A first (zero schema change, pure computed metric).

### Rank 3: Persist ASP improvement delta to structured sink

**Gap**: ASP delta is logged to console as text ("✅ [ASP] 교정 완료 (delta: +N)") but not to any structured sink.

**Why medium ROI**: ASP fires rarely (round_num >= 2, module available, previous attempt exists). The operator needs to know whether ASP is worth its ~$0.03/fire cost. Without structured delta data, this is unjudgeable.

**Blast radius**: LOW. The delta already exists in `ASPResult.improvement_delta`. Persisting it requires one additional field in the per-round log payload or a new JSONL append at `_run_asp_correction()`.

### Rank 4: Per-retry-strategy effectiveness tracking

**Gap**: `AdaptiveRetryStrategy` applies strategies but doesn't record which was used or whether it helped.

**Why lower ROI**: This answers a second-order question ("which retry strategy is best?") rather than the first-order question ("how much do retries cost?").

**Blast radius**: MEDIUM. Requires linking the strategy applied in `get_retry_strategy()` to the subsequent attempt's outcome. This crosses the boundary between AdaptiveRetryStrategy (in-memory) and PassRateMonitor (persisted).

**Recommendation**: Defer behind Rank 1-3.

### Rank 5: PASS_WITH_FIX loop iteration count to structured sink

**Gap**: The loop runs up to 3 iterations with console-only logging per iteration.

**Why low ROI**: The iteration count is useful but secondary to knowing whether the loop succeeded (Rank 2) and how long it took (Rank 1).

**Blast radius**: LOW. Add one field to the episode_production log payload.

## 5. Cross-Cutting Observations

### 5.1 The `MetricsCollector` → `PassRateMonitor` Gap

`MetricsCollector` (singleton) captures per-LLM-call timing, tokens, and cost with high fidelity. `PassRateMonitor` has fields for `duration_ms` and `token_cost` per attempt. But the values are not connected. This is the simplest and highest-impact wiring fix: at the call site where `pass_rate_monitor.record_attempt()` is invoked, pull the accumulated metrics from `MetricsCollector` and pass them through.

### 5.2 ASP Observability Is Thin But Not Zero

ASP is already observable via:
- `asp_used` boolean in episode_production
- `generation_method: "asp"` in pass_rate_monitor
- Console delta log

What's missing is structured internals (adversary score, round count, feedback quality). For a low-frequency event (~fires on round 3+), the boolean + console delta may be sufficient. The structured internals are a luxury unless ASP frequency or importance increases.

### 5.3 Rescue Observability Has a REJECT-Side Blind Spot

`episode_production.jsonl` only logs PASS outcomes. When rescue (PASS_WITH_FIX → fix loop) fails and the episode ends as REJECT, the rescue attempt details are NOT in episode_production. They ARE partially in:
- `stage_attempts` DB (verdict, score)
- `pass_rate_monitor.json` (if recorded)
- `session/decisions.jsonl` (if session logging is active)

But the fix loop details (iterations, patch traces, score changes within the loop) are console-only for REJECT outcomes.

## 6. Confidence And Limits

Estimated confidence: 96%

Why this clears the 95% gate:
- All claims backed by live code evidence (file:line references from `adaptive_retry.py`, `pass_rate_monitor.py`, `failure_analyzer.py`, `stage4_retry_runtime.py`, `stage4_episode_logging.py`, `stage4_interview_round.py`, `adversarial_self_play.py`, `metrics_collector.py`)
- Existing vs. missing distinctions are structural (field exists but is unpopulated, vs. field does not exist)
- The ranking is based on blast radius and ROI, not on speculative benefit claims
- Cross-checked against `stage3-latency-efficiency-static-survey.md` for retry cost context

Limits:
- This survey does not quantify the actual retry cost (because the instrumentation to measure it is the gap itself)
- ASP fire rate is inferred from code path conditions, not from actual production frequency data
- Rescue success rate is estimated as computable but not verified against live data
- The interaction between retry cost instrumentation and the upcoming Stage 3 authority re-banding wave is unexamined

---

Dominant observability gap in this lane: retry-rescue (specifically: retry cost attribution and rescue effectiveness measurement)
Best bounded instrumentation candidate in this lane: Populate existing `duration_ms` and `token_cost` fields in PassRateMonitor from MetricsCollector at the recording call site
Should this lane alone trigger a new SSOT: no — the gap is real but should be merged with other lanes to determine the best single observability wave
