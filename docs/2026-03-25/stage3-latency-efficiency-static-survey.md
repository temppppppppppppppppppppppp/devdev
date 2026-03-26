# Stage 3 Latency / Efficiency Static Survey

Date: 2026-03-25
Status: survey-only (no execution SSOT)
Scope: Stage 3 blueprint runtime and cost
Evidence basis: live code + canary_0325_overval_s3 llm_io.jsonl (4 episodes, all first-pass PASS)

## 1. Dominant Cost Center Breakdown

### Canary Evidence (canary_0325_overval_s3, 4 eps, all PASS on retry 0)

| Cost Center | Calls/ep | Avg ms/call | Wall ms/ep (est.) | Notes |
|---|---|---|---|---|
| BlueprintEnsemble generation (3 parallel) | 3 | 61,000 | ~75,000 (slowest) | Parallel via ThreadPool(3) |
| BlueprintEnsemble (4th call, purpose TBD) | 1 | 46,000 | ~46,000 | Possibly context cache related or backup |
| Director (compare/continuity/validation) | 3 | 22,300 | ~67,000 (serial) | Includes compare + continuity + 1 more |
| StateExtractor (once per session) | 0.25 | 28,800 | ~7,200 | One-time init cost |
| **Total per episode** | **7** | | **~185,000** | |

Grand total across 4 episodes: **1,273s** serial LLM time.
Estimated wall time per episode (happy path): **~185s (~3 min)**.
Per-episode LLM call count: **7** (4 BlueprintEnsemble + 3 Director).

### Key Observation: Retries Are the Main Latency Amplifier

This canary was clean: all 4 episodes passed on the first attempt. The real-world multiplier is the retry loop. `max_retries=9` means up to **10 full cycles** per episode, each incurring:

- 3 parallel BlueprintEnsemble generation calls (~75s wall)
- 1 Director compare_and_select (~31s)
- 1 Director continuity check (~18s)
- retry feedback assembly overhead

One REJECT doubles the per-episode cost. Two REJECTs triple it. A 3-retry episode costs ~555s (~9 min) of LLM wall time.

## 2. Cost Category Classification

### A. Likely Fixed Overhead (per session, not per episode)
- StateExtractor init: ~29s (one-time per Stage 3 session)
- StateTracker/WorldState/FactLedger lazy init: <1s each (Python only, no LLM)
- Semantic bundle assembly: Python only, <1s

### B. Likely Per-Episode LLM Cost (irreducible on happy path)
- 3 parallel BlueprintEnsemble generation calls: **~61s each, ~75s wall** (slowest determines wall time)
- 1 additional BlueprintEnsemble LLM call: **~46s** (exact purpose needs instrumented logging to confirm — may be backup model, context validation, or cache-path overhead)
- 3 Director calls (compare + continuity + validation): **~22s avg each, ~67s total serial**
- Total per-episode LLM wall on happy path: **~185s**

### C. Likely Candidate-Count / Strategy Fan-Out Cost
- Fixed at 3 strategies: action_focused, emotion_focused, dialogue_focused
- `max_workers=3`, all 3 strategies always run in parallel
- The 3 parallel calls share a Gemini context cache (created once per episode, ~46s)
- On retry with `fix_scope == "partial"`: falls to 1 strategy (single_strategy optimization already exists)
- On retry with high-enough score: uses in-place patch (1 LLM call instead of 3)
- **No dynamic fan-out; the 3-strategy count is hardcoded**

### D. Likely Context/Prompt Assembly Cost
- Semantic bundle: Python-only, includes world_state, fact_ledger, style_guide, treatment_block, timeline advisories, relationship slices. All local DB/memory reads. **<1s per episode**.
- Gemini context cache creation: **~46s per episode** (creates a cached content block from the shared context). This is an API call, not Python overhead.
- Previous manuscripts loading: DB read of up to 36 recent manuscripts, truncated. **Negligible Python time**, but **inflates prompt tokens** for all 3 parallel generation calls.

### E. Likely Validation/Retry Overhead
- Python prevalidation (`_python_pre_validate`): runs per candidate (3x per attempt), purely local Python regex/heuristic checks. **<100ms total**.
- Director calls dominate validation overhead: 3 Director LLM calls per attempt.
- **Retry multiplier: each REJECT adds ~140s of LLM wall time.**

## 3. Investigation Answers

### Q1: What are the dominant Stage 3 runtime cost centers?

1. **Blueprint generation (3 parallel + 1 additional LLM calls)**: ~65% of per-episode wall time (4 BlueprintEnsemble calls total)
2. **Director validation (3 LLM calls)**: ~34%
3. Python overhead: ~1%

### Q2: Is the main cost from prompt/context size, strategy fan-out, LLM retries, validator passes, or orchestration overhead?

**Mixed**. On the happy path (first-pass PASS), cost is split roughly 40/25/34 between generation/cache/Director. But on the unhappy path, **retries dominate** — each retry adds ~140s wall time, and the budget allows up to 10 attempts. The retry budget is the main latency risk.

Context cache creation (~46s/ep) is a material cost that is potentially reducible because:
- The shared context (constraints, prev info, HUD) is largely stable within an arc
- Gemini context cache TTL is already 600s
- Consecutive episodes within the same arc could potentially reuse the cache

### Q3: Which bounded optimization has the best ROI with the lowest blast radius?

**Ranked by ROI / blast radius:**

| Rank | Candidate | Est. savings | Blast radius | Confidence |
|---|---|---|---|---|
| 1 | Cross-episode context cache reuse within arc | 46s/ep (25%) for eps 2+ in same arc | Low — cache key logic only | 80% |
| 2 | Reduce retry budget from 10 to 5 for high-score first attempts | Caps worst-case at 5x instead of 10x | Low — only affects retry ceiling | 75% |
| 3 | Skip Director continuity check for ep_num == 1 | 18s/ep for first episode | Very low | 90% |
| 4 | Reduce 3 strategies to 2 on retry (drop weakest) | ~20s/retry (one fewer parallel call) | Medium — changes candidate diversity | 60% |
| 5 | Director call consolidation (compare+continuity in one call) | ~18s/ep | High — Director prompt redesign | 40% |

### Q4: What should remain untouched because it risks quality regression?

- **3-strategy ensemble on first attempt**: All 3 strategies provide meaningful candidate diversity. Reducing to 2 on the first attempt would reduce blueprint quality.
- **Director compare_and_select**: This is the core quality gate. Cannot be shortened or removed.
- **Director continuity check (ep > 1)**: Prevents continuity breaks. Must not be removed for episodes after the first.
- **`max_retries=9` for genuinely failing blueprints**: Lowering the retry budget risks terminal failures on hard episodes. Any change should be conditional (e.g., only reduce if first attempt scores high).
- **Python prevalidation**: Already free (local heuristics). Must not be weakened.
- **Prompt self-audit checklist**: Just landed in this session. Must not be removed.

### Q5: Is there a clear next wave, or should fresh run evidence land first?

**Fresh run evidence should land first.** The canary_0325_overval_s3 data is limited:
- Only 4 episodes, all first-pass PASS (no retry data)
- No token count data in llm_io.jsonl (token fields are 0)
- No per-episode cost data (cost fields are None)
- Cannot distinguish context cache creation from generation in timing alone

A post-patch canary (after the 3 quality waves landed today) with full token/cost logging would provide the missing data to confidently choose between candidates #1 and #2.

## 4. Candidate Optimization Lanes

### Safe After Stabilization

**Lane A: Cross-episode context cache reuse within arc**
- The ensemble's `_get_or_create_context_cache` creates a new cache per episode even when consecutive episodes share the same arc data and constraints
- A cache key that includes `arc_idx` instead of `ep_num` (or both with a stable hash of the shared_context content) could allow episodes within the same arc to skip the ~46s cache creation call
- This requires careful validation that the constraint block and prev_info are actually identical enough across episodes
- **Blast radius**: low (cache key logic only, no prompt or quality change)

**Lane B: Skip continuity check for ep_num == 1**
- `check_blueprint_continuity_with_cache` always runs, but for ep_num=1 there is no predecessor to check against
- The code already guards `if not (director and db and ep_num > 1): return None`, so this is already handled — but the guard is inside `_maybe_reject_phase3_continuity`, so the Director call is not made for ep_num=1
- **Confirmed: already optimized. No savings available here.**

**Lane C: Conditional retry budget reduction**
- If the first attempt scores above a threshold (e.g., 85+), reduce remaining retry budget from 9 to 3-4
- This is a safety net reduction, not a quality reduction — high-scoring blueprints rarely need 9 more retries
- **Blast radius**: low, but needs real retry-pattern data to set the threshold correctly

### Risky Before More Evidence

**Lane D: Strategy reduction on retry**
- After a REJECT, the current code already supports `single_strategy` mode when `fix_scope == "partial"`
- Extending this to always reduce to 2 strategies on retry would save ~20s/retry but reduce candidate diversity when it matters most
- **Needs retry distribution data**: what fraction of retries benefit from all 3 strategies vs. a targeted single-strategy fix?

**Lane E: Director call consolidation**
- Merging compare_and_select + continuity_check into one Director prompt would save ~18s/ep
- **High blast radius**: requires Director prompt redesign, changes the quality gate contract, and risks regression in both selection quality and continuity detection
- Should not be attempted without extensive A/B canary comparison

**Lane F: Context cache TTL extension for stable arcs**
- Currently 600s (10 min). If an arc spans 4 episodes and each takes ~3 min, the cache expires before ep 3
- Extending TTL to 1200-1800s for same-arc episodes could preserve the cache across episodes
- **Needs measurement**: does the Gemini cache actually persist and reduce billing, or is the creation call still required?

## 5. Findings Summary

1. **Stage 3 per-episode happy-path cost is ~185s wall time across 7 LLM calls**
2. **Retries are the dominant latency amplifier** — each REJECT adds ~140s
3. **Context cache creation takes ~46s/ep** and is potentially shareable across same-arc episodes
4. **3 Director calls per episode** is architectural (compare + continuity + additional validation)
5. **Python overhead is negligible** (<1%)
6. **Token/cost data is missing** from the available canary logs — need instrumented canary

## 6. Recommendation

**Do not open an execution SSOT now.** Confidence on the best bounded next move is ~80%, below the 95% threshold.

**Recommended next step**: run one instrumented Stage 3-only canary (4-9 episodes) with full token/cost logging enabled, then re-evaluate Lane A (cross-episode cache reuse) and Lane C (conditional retry budget) with concrete data.

---

Dominant Stage 3 latency source: LLM generation calls (3 parallel ensemble + 3 Director per episode), amplified by retry budget
Best bounded next wave: cross-episode context cache reuse (Lane A), pending fresh instrumented canary data
Should Codex open an execution SSOT now: no
