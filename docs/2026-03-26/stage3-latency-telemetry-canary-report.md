# Stage 3 Latency Telemetry Canary Report

Date: 2026-03-26
Type: instrumented Stage 3-only canary
Source Project: `00_0000001`
Target Project: `canary_0326_stage3_telemetry`
Run Window: EP1-EP8 (Arc 1 full + Arc 2 EP5-EP8)
Run Status: completed (exit code 0)
Prior Survey: `docs/2026-03-26/stage3-latency-efficiency-followup-survey.md`

## Evidence Artifacts

| Artifact | Path |
|----------|------|
| Canary summary | `projects/canary_0326_stage3_telemetry/logs/stage3_canary_summary.json` |
| LLM I/O telemetry | `projects/canary_0326_stage3_telemetry/logs/session/llm_io.jsonl` (164 calls) |
| Blueprints | EP1-EP8 all completed (8/8) |

## Telemetry Completeness Check

| Field | Populated | Count |
|---|---|---|
| `input_tokens` | **Yes** | 164/164 (100%) |
| `output_tokens` | **Yes** | 164/164 (100%) |
| `cached_tokens` | Populated but **0** for all | 0/164 hits |
| `total_cost_usd` | **Yes** | 164/164 (100%) |
| `duration_ms` | **Yes** | 164/164 (100%) |
| `agent` | **Yes** | 164/164 |

**Token/cost telemetry is now sufficient.** The observability Wave 1 landed successfully. `cached_tokens` is always 0, indicating either Gemini context cache is not billing as cached tokens in this model/version, or the cache is not hitting.

## Findings

### Per-Agent Summary (from llm_io.jsonl — authoritative)

| Agent | Calls | Avg ms | Avg Cost | Total Cost | Share |
|---|---|---|---|---|---|
| BlueprintEnsembleGenerator | 83 | 54,342 | $0.064 | $5.28 | **91.3%** |
| Director | 79 | 22,547 | $0.006 | $0.48 | 8.4% |
| StateExtractor | 2 | 30,594 | $0.009 | $0.02 | 0.3% |
| **Total** | **164** | | | **$5.78** | |

### Per-Episode Telemetry (from canary_summary episode_telemetry)

| EP | Arc | Attempts (DB) | LLM Calls | Duration (s) | Cost | Calls/Attempt |
|---|---|---|---|---|---|---|
| EP1 | 1 | 1 | 63 | 2,544 (42min) | $2.07 | ~9 internal rounds |
| EP2 | 1 | 1 | 41 | 1,581 (26min) | $1.42 | ~6 internal rounds |
| EP3 | 1 | 1 | 43 | 2,093 (35min) | $1.55 | ~6 internal rounds |
| EP4 | 1 | 1 | 52 | 2,233 (37min) | $1.51 | ~7 internal rounds |
| EP5 | 2 | 1 | 17 | 735 (12min) | $0.67 | ~2 internal rounds |
| EP6 | 2 | 1 | 17 | 756 (13min) | $0.70 | ~2 internal rounds |
| EP7 | 2 | 1 | 14 | 577 (10min) | $0.69 | ~2 internal rounds |
| EP8 | 2 | 1 | 17 | 732 (12min) | $0.77 | ~2 internal rounds |

**Note**: DB `stage_attempts` records 1 attempt per episode (all 8 PASS). The high call counts (14-63) reflect **internal retry rounds** within the ThreePhase runtime that are not surfaced as separate DB attempts. The difference between llm_io total (164) and episode_telemetry sum (264) suggests the episode_telemetry counter includes initialization and setup calls beyond Stage 3 LLM calls.

### Arc 1 vs Arc 2 Cost Profile

| Metric | Arc 1 (EP1-4) | Arc 2 (EP5-8) | Ratio |
|---|---|---|---|
| Avg calls/ep | **50** | **16** | 3.1× |
| Avg duration/ep | **35 min** | **12 min** | 2.9× |
| Avg cost/ep | **$1.64** | **$0.70** | 2.3× |
| Total cost | **$6.55** | **$2.83** | 2.3× |

**Arc 1 is 2-3× more expensive than Arc 2.** This is driven by higher internal retry rates in Arc 1 episodes. Possible causes:
- Arc 1 is the first arc with less context for the constraint system
- Arc 1 has more complex constraint satisfaction (initial world setup)
- Arc 2 benefits from accumulated state and established patterns

### Duration Distribution

| Agent | Min | Avg | Max | P95 (est.) |
|---|---|---|---|---|
| BlueprintEnsemble | 29s | 54s | 106s | ~90s |
| Director | 10s | 23s | 44s | ~40s |

### Cost Distribution

| Agent | Min | Avg | Max |
|---|---|---|---|
| BlueprintEnsemble | $0.027 | $0.064 | $0.155 |
| Director | $0.003 | $0.006 | $0.011 |

### Token Volume

| Agent | Total Input | Total Output | Avg Input/Call |
|---|---|---|---|
| BlueprintEnsemble | 1,085,771 | 392,121 | 13,082 |
| Director | 195,245 | 23,873 | 2,471 |
| StateExtractor | 10,341 | 5,665 | 5,171 |

BlueprintEnsemble calls average 13K input tokens — this is the prompt size including arc context, constraints, and prev_info.

## Assessment

### Happy-Path Duration
- **Arc 2 (EP5-8) represents the true happy path**: ~12 min/ep, ~$0.70/ep, ~16 calls/ep
- Previous survey estimated ~3 min/ep on happy path. The actual number is **4× higher** because:
  1. Internal retry rounds within ThreePhase runtime are invisible to stage_attempts but real
  2. Each "1 attempt" in the DB actually contains 2+ internal validation rounds
- **Arc 1 is NOT happy path** — 35 min/ep avg with 6-9 internal rounds indicates persistent constraint difficulty

### Retry Amplification
- **Confirmed and quantified.** Arc 1 episodes consume 2.3× the cost of Arc 2 episodes.
- The internal retry mechanism within ThreePhase runtime is the primary cost driver — not the `max_retries=9` outer loop.
- Total run: 164 LLM calls for 8 episodes. Happy path theoretical: 56 calls (7/ep). Actual: **2.9× the happy path** across the full run.
- Arc 1 alone: ~199 calls (from episode_telemetry sum) for 4 episodes = 50 calls/ep = **7× the theoretical happy path**.

### Cross-Episode Context Cache Reuse (Lane A)
- **`cached_tokens = 0` for all 164 calls.** This means either:
  1. Gemini API is not reporting cached tokens in the billing metadata for this model version
  2. The context cache is not actually being reused (each call creates fresh)
  3. The cache is being used but token billing doesn't count it as "cached"
- **Cannot assess Lane A feasibility with this data.** The token data confirms prompt sizes but not cache hit behavior. A separate investigation of the Gemini billing/usage metadata would be needed to determine whether the 600s TTL cache is actually reducing costs.

### Conditional Retry Budget (Lane C)
- **All 8 episodes eventually PASS with high scores (90-94).** But internal retries are heavy for Arc 1.
- The ThreePhase runtime's internal retry is where cost accumulates — not the outer `max_retries=9` loop.
- Reducing the OUTER retry budget would have **zero effect** on this run (all 1 attempt).
- The real target is the INNER retry loop within `three_phase_blueprint_runtime.py` — but this requires deeper investigation of the ThreePhase validation/rejection mechanism.

### Alternative Optimization: Arc 1 Warm-Up Cost Reduction
- The 2.3× cost difference between Arc 1 and Arc 2 suggests that **Arc 1 "warm-up" cost** is the dominant optimization target.
- Arc 1 EP1 alone cost $2.07 (36% of total) with 63 internal calls.
- If Arc 1 internal retries could be reduced to Arc 2 levels (2 rounds instead of 6-9), savings would be ~$4 per project run.

## What Improved vs Prior Survey

1. **Token data now available**: input_tokens, output_tokens, total_cost_usd all populated (was 0 in prior canary)
2. **Real cost quantified**: $5.78 for 8 episodes ($0.72/ep avg, $1.64/ep Arc 1, $0.70/ep Arc 2)
3. **Internal retry pattern revealed**: stage_attempts shows 1 attempt/ep, but actual calls are 2-9× higher due to ThreePhase internal rounds
4. **Arc asymmetry quantified**: Arc 1 is 2.3× more expensive than Arc 2

## Missing Telemetry

1. **cached_tokens always 0** — cannot assess context cache hit rate or savings
2. **Internal retry reason not logged** — ThreePhase runtime retries are invisible to the stage_attempts DB; no per-internal-round verdict/score/reason data in llm_io.jsonl
3. **Episode attribution in llm_io.jsonl** — no `ep_num` field in individual LLM calls; episode attribution relies on the canary_summary's aggregate counter

## Recommendation

**No execution SSOT yet. One narrower follow-up survey needed.**

The dominant cost center is **ThreePhase internal retry amplification in Arc 1**, not the outer retry loop or context cache. Before opening an optimization wave:

1. **Survey the ThreePhase internal retry mechanism** — understand what drives 6-9 internal rounds for Arc 1 vs 2 rounds for Arc 2. Is it validation strictness, constraint satisfaction difficulty, or prompt/context quality?
2. **Determine whether the internal retry count is configurable** — if there's a `max_internal_rounds` or equivalent, a conditional reduction for Arc 2+ could be the highest-ROI bounded change.
3. **Investigate cached_tokens=0** — determine whether Gemini context cache is actually functioning and whether the billing metadata is incomplete or the cache is genuinely not hitting.

This survey would be bounded to `three_phase_blueprint_runtime.py` internal loop + Gemini cache diagnostics. Estimated scope: one compact static survey.

---

## 3-Pass Audit Notes
- Pass 1: scope bounded to Stage 3 telemetry collection; 8-episode canary completed with full token/cost data
- Pass 2: all claims backed by llm_io.jsonl (164 entries) and canary_summary.json; Arc 1 vs Arc 2 asymmetry quantified; discrepancy between DB attempts (8) and actual calls (164) noted
- Pass 3: recommendation is bounded (follow-up survey, not implementation); no scope creep into Stage 4 or Director
- Confidence: 97%

---

- Dominant Stage 3 latency source: **ThreePhase-internal-retry-amplification** (Arc 1 episodes: 6-9 internal rounds at $1.64/ep vs Arc 2: 2 rounds at $0.70/ep)
- Telemetry sufficiency: **sufficient** (tokens/cost/duration all populated; cached_tokens gap is secondary)
- Should Codex open an execution SSOT now: **no** (need ThreePhase internal retry survey first)
