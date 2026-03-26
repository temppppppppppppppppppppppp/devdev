# T1. Runtime / Timing / Cost Surfaces — Survey Report

Date: 2026-03-25
Status: survey-only (lane output)
Lane: T1 (Runtime / Timing / Cost)
Master Order: `docs/2026-03-25/global-observability-statistics-core-4terminal-master-order.md`
Baseline Commit: `e3f2771699cb5d596aefaf994a8a177bbbad0a3e`
Evidence basis: live code static analysis of production modules

---

## 1. Findings

### 1.1 Per-LLM-Call Timing — Already Exists, Well-Instrumented

| Surface | Location | What It Captures | Sink |
|---|---|---|---|
| `BaseAgent.ask()` wall time | `base_agent.py` L633-L828 | `time.time()` before/after each API call, continuation calls, backup model calls | `duration_ms` → DB `llm_calls`, SessionLogger `llm_io.jsonl`, MetricsCollector in-memory |
| `MetricsCollector.AgentMetric.duration_ms` | `metrics_collector.py` L43-L47 | `(end_time - start_time) * 1000` for each start_call/end_call pair | In-memory aggregation (P50/P90/P99) + `logs/metrics/metrics_<session>.json` |
| DB `llm_calls.duration_ms` | `db_bootstrap_runtime.py` L431, `db_manager.py` L2858 | Per-LLM-call `duration_ms INTEGER` column | `project_data.db` (authoritative telemetry sink) |

**Assessment**: Per-LLM-call wall time is comprehensively captured. Every `BaseAgent.ask()` call records `duration_ms` in DB, JSONL (when enabled), and MetricsCollector. No gap here.

### 1.2 Per-Attempt/Round Timing — Partially Exists

| Surface | Location | What It Captures | Sink |
|---|---|---|---|
| Stage 4 round duration | `stage4_interview_round.py` L5460-L5463 | `time.monotonic() - self._round_start_ts` per interview round | `episode_production.jsonl` (`duration_ms` field) |
| Stage 4 `stage_attempts.duration_ms` | `db_bootstrap_runtime.py` L486, `db_manager.py` L2904 | Per-attempt `duration_ms INTEGER` column | `project_data.db` |
| Stage 3 per-episode pipeline duration | `stage3_orchestrator.py` L1562 | `_time.perf_counter() - started_at` per blueprint generation | `pipeline_result["_stage3_duration_ms"]` → passed to `save_stage_attempt(duration_ms=...)` |

**Assessment**: Per-attempt timing exists for both Stage 3 and Stage 4. Stage 4 uses `time.monotonic()` per round. Stage 3 uses `time.perf_counter()` per episode. Both persist to DB `stage_attempts.duration_ms`. **No gap** for attempt-level wall time.

### 1.3 Per-Stage Session Timing — MISSING

| Surface | Exists? | Notes |
|---|---|---|
| Stage 2 total session wall time | **No** | `stage2_finalizer.py` does not capture total Stage 2 session duration. Only individual cost scope snapshots. |
| Stage 3 total session wall time | **No** | `stage3_orchestrator.py` captures per-episode duration but not total Stage 3 session elapsed. |
| Stage 4 total session wall time | **No** | `stage4_orchestrator.py` does not capture total Stage 4 session duration. |
| Cross-stage total pipeline wall time | **No** | `main_a.py` does not aggregate or persist total pipeline wall time. |

**Assessment**: **Gap.** No sink captures total stage-level or pipeline-level wall time. An operator can infer it from summing `llm_calls.duration_ms` or `stage_attempts.duration_ms`, but no pre-computed field exists.

### 1.4 Token Counts — Exist in Schema, Partially Populated

| Surface | Location | What It Captures | Population Status |
|---|---|---|---|
| DB `llm_calls` token columns | `db_bootstrap_runtime.py` L437-L441, L454-L458 | `input_tokens`, `output_tokens`, `cached_tokens`, `thinking_tokens` | Populated via `MetricsCollector` when `METRICS_ENABLED=True`. **But**: `BaseAgent._build_metric_usage_payload` uses heuristic estimation (`estimate_tokens`), not API-returned usage metadata. |
| MetricsCollector session totals | `metrics_collector.py` L353-L396 | Per-model `input_tokens`, `output_tokens`, `cached_tokens`, `thinking_tokens` | Same heuristic estimation |
| SessionLogger `llm_io.jsonl` | `session_logger.py` L103-L135 | `duration_ms` only; **no token fields** | Token data is not passed through SessionLogger |
| Stage 4 `episode_production.jsonl` | `stage4_interview_round.py` L5521-L5529 | `round_total_calls`, `round_total_tokens`, `round_total_cost_usd`, `round_model_breakdown` | From `MetricsCollector.peek_scope()` — same heuristic token data |

**Assessment**: Token count infrastructure exists but is **heuristic-estimated, not API-returned**. The Gemini API returns `usage_metadata` with actual `prompt_token_count`, `candidates_token_count`, `cached_content_token_count`, but `BaseAgent.ask()` does not extract or propagate these to MetricsCollector. The canary logs confirm this: token fields are 0 in `llm_io.jsonl`, and heuristic estimates in the DB may diverge from actual billing.

### 1.5 Cost Calculation — Exists, Dependent on Heuristic Tokens

| Surface | Location | What It Captures | Accuracy |
|---|---|---|---|
| `MetricsCollector.calculate_cost()` | `metrics_collector.py` L292-L311 | Per-call cost from `MODEL_COSTS` dictionary (Gemini pricing) | Correct pricing rates, but input is heuristic token estimates, not API actuals. |
| DB `llm_calls.total_cost_usd` | `db_manager.py` L2860, L2882 | Per-call cost written to DB | Same heuristic basis |
| DB `cost_log` table | `db_bootstrap_runtime.py` L570-L581 | Scoped cost records (arc/episode/session) with `total_calls`, `total_tokens`, `total_cost_usd`, `model_breakdown` | Accumulated from scope snapshots via MetricsCollector |
| `save_cost_record()` call sites | Stage 2: `stage2_finalizer.py` L1322, L2902. Stage 3: `stage3_orchestrator.py` L2737. Stage 4: `stage4_post_processor.py` L841, `stage4_reject_runtime.py` L616 | Per-episode or per-arc cost records | Actual field values depend on upstream MetricsCollector heuristic data |

**Assessment**: Cost infrastructure is structurally complete — model pricing, per-call cost, scoped cost records, all connected. But the **input token counts are heuristic estimates** (Korean 1.5 chars/token, English 4 chars/token), not actual API-returned values. Cost accuracy is bounded by this estimation gap.

### 1.6 Runtime Attribution (Fixed Overhead vs LLM vs Retry) — MISSING

| Capability | Exists? | Notes |
|---|---|---|
| Attribute wall time to LLM calls vs Python overhead | **Partially** | `BaseAgent.ask()` captures LLM call duration. Python overhead is `total_round_duration - sum(llm_call_durations)`. Requires manual SQL join. No pre-computed attribution. |
| Attribute wall time to first attempt vs retries | **Partially** | `stage_attempts.attempt_num` + `duration_ms` allows per-attempt timing. But no aggregate "retry overhead fraction" is pre-computed. |
| Attribute cost to fixed overhead vs retries | **No** | `cost_log` captures scoped totals but does not split first-pass vs retry cost. |
| Separate context cache creation time from generation time | **No** | Context cache creation (~46s in Stage 3) is lumped into the first LLM call duration. No distinct timing for cache creation vs generation. |

**Assessment**: **Gap.** The raw data for attribution exists (per-call + per-attempt timing in DB), but no pre-computed runtime attribution is produced. An operator cannot quickly see "X% of wall time was retries" or "Y% was fixed overhead" without manual query construction.

### 1.7 Canary Summary Payloads — Runtime Data Coverage

| Field | Stage 3 Canary Summary | Stage 4 Canary Summary |
|---|---|---|
| Per-episode wall time | Not in summary payload | Not in summary payload |
| Per-episode token count | Not in summary payload | Not in summary payload |
| Per-episode cost | Not in summary payload | Not in summary payload |
| `runtime_audit_summary` | Not consulted | Included (from `logs/runtime_audit_summary.json`) |
| Attempt count | Not in summary | `stage4_attempts` count |
| Round-level metrics | Not in summary | Via `episode_production.jsonl` (round-level timing/cost) |

**Assessment**: **Gap in Stage 3 canary summary.** The Stage 3 canary summary (`build_stage3_canary_summary()`) does not include per-episode timing, token, or cost data. The raw data exists in DB `llm_calls` and `stage_attempts`, but the canary summary builder does not extract or report it. Stage 4 canary summary is slightly better — it includes `runtime_audit_summary` — but still lacks per-episode timing/cost breakdown.

### 1.8 Console Runtime Reporting — Minimal

The operator console shows per-round UI logs (e.g., "Round 1 PASS") but does not display:
- Per-episode wall time
- Per-stage total elapsed time
- Running cost accumulation
- Retry overhead fraction

The `MetricsCollector.get_summary_report()` method exists (L398-L444) and produces a formatted text report with per-agent timing stats, token totals, and cost. But it is only called at session finalization and is not displayed mid-session.

## 2. Summary of Existing vs Missing

### Already Exists (Strong)
1. **Per-LLM-call wall time** — `BaseAgent.ask()` → DB `llm_calls.duration_ms`, JSONL, MetricsCollector
2. **Per-attempt wall time** — Stage 3 perf_counter, Stage 4 monotonic → DB `stage_attempts.duration_ms`
3. **Per-call cost calculation** — `MetricsCollector.calculate_cost()` with correct Gemini pricing
4. **Scoped cost accumulation** — `cost_log` table with arc/episode/session scope and model breakdown
5. **MetricsCollector session report** — Full per-agent timing stats (P50/P90/P99), per-model token/cost breakdown
6. **Stage 4 per-round metrics** — `episode_production.jsonl` includes `round_total_calls`, `round_total_tokens`, `round_total_cost_usd`

### Missing or Weak
1. **API-returned token counts** — Gemini `usage_metadata` not propagated; heuristic estimation only
2. **Per-stage total wall time** — No sink captures Stage 2/3/4 total session elapsed
3. **Runtime attribution** — No pre-computed split of LLM time vs Python overhead vs retry overhead
4. **Context cache creation timing** — Lumped into first LLM call duration, not separately measured
5. **Canary summary runtime data** — Stage 3 summary lacks per-episode timing/token/cost; Stage 4 summary lacks per-episode timing breakdown
6. **Mid-session cost display** — MetricsCollector report exists but only at finalization, not streaming

## 3. Investigation Answers

### Q1: Where do stage, episode, and attempt-level timing facts already exist?

- **Attempt-level**: DB `stage_attempts.duration_ms` (both Stage 3 and 4), `episode_production.jsonl` (Stage 4 per-round)
- **LLM-call-level**: DB `llm_calls.duration_ms`, MetricsCollector in-memory (P50/P90/P99 per agent)
- **Episode-level**: Stage 3 `_stage3_duration_ms` in `pipeline_result` (transient, written to DB via `save_stage_attempt`). Stage 4 per-round `duration_ms` in `episode_production.jsonl`.
- **Stage-level**: **Does not exist.** No sink captures total Stage 2, 3, or 4 session elapsed.
- **Pipeline-level**: **Does not exist.**

### Q2: Is the current system able to attribute runtime to fixed overhead vs LLM calls vs retries?

**No, not without manual SQL joins.** The raw data for attribution exists:
- `llm_calls.duration_ms` for LLM call time
- `stage_attempts.attempt_num` + `duration_ms` for first-pass vs retry
- `MetricsCollector` scope snapshots for cost per scope

But there is no pre-computed runtime attribution layer. An operator would need to:
1. Sum `llm_calls.duration_ms` grouped by `ep_num` to get LLM time per episode
2. Compare against `stage_attempts.duration_ms` to derive Python overhead
3. Partition `stage_attempts` by `attempt_num == 1` vs `> 1` to separate first-pass from retry

This is feasible but not automated.

### Q3: Are token/cost fields already captured anywhere, or only inferable?

**Token fields exist in the DB schema** (`llm_calls.input_tokens`, `output_tokens`, `cached_tokens`, `thinking_tokens`, `total_cost_usd`), **but they are populated with heuristic estimates, not API-returned values.**

The `BaseAgent._build_metric_usage_payload()` uses `MetricsCollector.estimate_tokens()` (Korean 1.5 chars/token, English 4 chars/token) rather than extracting the Gemini API `usage_metadata.prompt_token_count` / `candidates_token_count` / `cached_content_token_count`.

The `cost_log` table aggregates these heuristic token counts into scoped cost records. Cost calculation uses correct per-model pricing rates, so the cost is only as accurate as the token estimation.

**Key evidence**: The Stage 3 canary (`canary_0325_overval_s3`) showed token fields as 0 in `llm_io.jsonl`, confirming that SessionLogger does not receive token data at all, and the DB token values come from the heuristic estimator only.

### Q4: What is the best bounded next move for runtime/cost observability?

**Ranked by ROI / blast radius:**

| Rank | Candidate | Estimated Impact | Blast Radius | Confidence |
|---|---|---|---|---|
| 1 | **Propagate Gemini `usage_metadata` to MetricsCollector** | Replaces heuristic token estimates with API actuals; fixes all downstream cost accuracy (DB, cost_log, canary summaries) | Low — `BaseAgent.ask()` already has the API response; needs extraction of `usage_metadata` fields and passing to `end_call()` | 90% |
| 2 | **Add per-stage session wall time** | One `time.perf_counter()` at stage start/end, written to `cost_log` or new column | Very low — 3 touch points (Stage 2/3/4 entry+exit), pure timing instrumentation | 95% |
| 3 | **Enrich canary summaries with runtime/cost data** | Include per-episode `duration_ms`, `total_tokens`, `total_cost_usd` from DB joins | Low — read-only query additions to `build_stage3_canary_summary()` / `build_stage4_canary_summary()` | 85% |
| 4 | **Pre-computed runtime attribution query** | A `FailureAnalyzer` method that returns `{llm_time_pct, python_overhead_pct, retry_overhead_pct}` per stage/episode | Low — read-only DB query, no pipeline change | 80% |
| 5 | **Mid-session streaming cost display** | Periodic `MetricsCollector.peek_scope()` display in console during execution | Medium — requires UI integration and frequency tuning | 60% |

**Recommendation**: Candidates #1 and #2 are the highest-ROI, lowest-blast next moves. #1 fixes the foundational accuracy problem that all downstream cost/token reporting depends on. #2 fills the most visible timing gap at minimal risk.

## 4. Limits and Confidence

- **Confidence in findings**: ~95%. All claims are based on direct code inspection of the listed evidence surfaces. DB schema, MetricsCollector, BaseAgent, and Stage 3/4 orchestrators were fully examined.
- **Limit**: No live run data was inspected for this lane (static analysis only). The canary_0325_overval_s3 data referenced in the Stage 3 latency survey corroborates the token=0 finding.
- **Limit**: `scripts/run_auto_frontier_lag_harness.py` runs the pipeline as a subprocess; its internal timing instrumentation was not deeply traced.

---

Dominant observability gap in this lane: runtime-cost
Best bounded instrumentation candidate in this lane: Propagate Gemini usage_metadata to MetricsCollector (actual token counts replace heuristic estimates)
Should this lane alone trigger a new SSOT: no
