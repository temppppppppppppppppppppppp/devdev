# Stage 3 Latency / Efficiency Follow-Up Survey

Date: 2026-03-26
Type: static survey (compact follow-up)
Scope: Stage 3 blueprint runtime latency and cost optimization
Mode: survey-only, no code changes
Prior Survey: `docs/2026-03-25/stage3-latency-efficiency-static-survey.md`

## Evidence Surfaces Inspected

| Surface | Path | Key Lines |
|---------|------|-----------|
| Blueprint ensemble | `blueprint_ensemble.py` | L276-281 (cache create), L332 (ThreadPool 3) |
| Cache key composition | `base_agent.py` | L1989-2003 (namespace: `{project}_ep_{ep_num}`), L2035-2036 (key: `{type}_{ns}_{content_hash}`) |
| Three-phase runtime | `three_phase_blueprint_runtime.py` | L1523 (max_retries=9), L409-420 (fix_scope routing) |
| Unified validator | `unified_blueprint_validator.py` | L599-607 (Python pre-validate, 0 LLM), L298 (Director compare), L613 (Director audit) |
| Stage3 orchestrator | `stage3_orchestrator.py` | L890 (StateExtractor once per arc), L1486 (3-phase generate) |
| Session logger | `session_logger.py` | L131-147 (duration_ms, input/output/cached/thinking tokens, total_cost_usd) |
| Stage3 canary (old) | `canary_0325_overval_s3/logs/session/llm_io.jsonl` | 29 calls, 4 eps, all first-pass PASS |
| Stage4 canary (new, W2) | `canary_0325_stage4_wave2/logs/session/llm_io.jsonl` | 155 calls, tokens populated |
| Observability SSOT | `docs/2026-03-25/observability-core-wave1-telemetry-completeness-execution-ssot.md` | closed |

## Findings

### F1. Per-episode Stage 3 cost structure confirmed — happy path is acceptable

**Stage3 canary telemetry (canary_0325_overval_s3, 4 eps, all R0 PASS):**

| Per-Episode Step | Calls | Serial ms | Wall ms (est.) | Share |
|---|---|---|---|---|
| Context cache creation | 1 BP call | ~46,000 | ~46,000 | 25% |
| 3 parallel strategy generation | 3 BP calls | ~190,000 | ~75,000 (max) | 41% |
| Director compare_and_select | 1 Dir call | ~31,000 | ~31,000 | 17% |
| Director continuity check | 1 Dir call | ~17,000 | ~17,000 | 9% |
| Director additional validation | 1 Dir call | ~15,000 | ~15,000 | 8% |
| **Total happy-path wall** | **7 calls** | | **~184,000** | |

**184s (~3 min) per episode on happy path is acceptable.** No optimization needed for the first-pass cost.

### F2. Cross-episode cache reuse (Lane A) is MORE complex than originally estimated

**Cache key** (`base_agent.py` L2035-2036):
```
cache_key = f"{cache_type}_{project_name}_{content_hash}"
```

**Cache content** (`blueprint_ensemble.py` L275):
```python
shared_context = f"{arc_focus}\n\n{constraints_str}\n\n{prev_info}\n\n{hud_context}"
```

**Critical finding**: `prev_info` includes prior manuscripts text that changes every episode. Even if we change the cache namespace from `project_ep_{ep_num}` to `project_arc_{arc_idx}`, the `content_hash` would still differ per episode because `prev_info` changes.

Cross-episode reuse requires **splitting** the cached content into:
- Static part (arc_focus, constraints_str, hud_context) → cached once per arc
- Dynamic part (prev_info) → uncached per-episode prompt suffix

This is a **prompt composition restructure**, not just a cache key change. Blast radius is **medium**, not low as originally assessed.

### F3. Existing Stage 3 canary has NO token/cost data — observability gap

**canary_0325_overval_s3** (`llm_io.jsonl` 29 calls):
- `input_tokens`: 0 for all calls
- `output_tokens`: 0 for all calls
- `cached_tokens`: 0 for all calls
- `total_cost_usd`: not present

This canary ran **before** the observability Wave 1 landed. Token/cost fields are now supported in `session_logger.py` (L139-147) and confirmed working in the Wave 2 Stage 4 canary (155 calls, input_tokens=1.2M total).

**No token-complete Stage 3 data exists.** Cannot compute per-call cost, cache hit rate, or prompt token inflation.

### F4. Retry amplification remains the main latency risk — but no Stage 3 retry data exists

Each Stage 3 REJECT adds approximately:
- 3 parallel generation calls: ~75s wall (or 1 call if fix_scope=partial)
- 1-2 Director calls: ~35s
- Total: ~110-140s per retry

With `max_retries=9`, worst case is 10 × 184s = ~30 min per episode. But we have **zero Stage 3 retry data** — the canary was all first-pass PASS.

### F5. Conditional retry budget (Lane C) is still the safest bounded optimization — but needs threshold data

`three_phase_blueprint_runtime.py` L1523: `max_retries=9` (hardcoded).

A conditional reduction (e.g., if first attempt scores 85+, cap remaining retries at 3) would:
- Reduce worst-case from 10× to 4× for high-scoring first attempts
- Not affect genuinely failing episodes (low score → keep full budget)
- Blast radius: very low (one conditional in the retry loop)

**But**: without Stage 3 retry distribution data, we cannot set the score threshold or estimate the savings.

## Candidate Lane Re-Ranking

| Rank | Lane | Est. Savings | Blast Radius | Data Available? | Confidence |
|---|---|---|---|---|---|
| 1 | **C: Conditional retry budget** | Caps worst-case 10× → 4× | Very low | **No** (no S3 retry data) | 70% |
| 2 | **A: Cross-episode cache reuse** | ~46s/ep for eps 2+ | **Medium** (prompt restructure) | **No** (no token data) | 60% |
| 3 | F: Cache TTL extension | Preserves cache across eps | Low | **No** | 55% |
| 4 | D: Strategy reduction on retry | ~20s/retry | Medium (diversity loss) | **No** | 45% |
| 5 | E: Director call consolidation | ~18s/ep | High (prompt redesign) | N/A | 30% |

**All top candidates lack the data needed to confidently set parameters.**

## Classification

### Safe Now
- **Nothing.** Happy-path cost (184s/ep, 3 min) is acceptable. All optimization candidates need retry distribution and/or token-level data that doesn't exist yet.

### Needs More Evidence
- **Lane C (conditional retry budget)**: Needs Stage 3 retry frequency + score distribution from a multi-episode canary that includes REJECT rounds
- **Lane A (cross-episode cache reuse)**: Needs (a) token-complete data to measure actual cache cost, (b) assessment of prompt restructure complexity, (c) verification that static/dynamic content split is feasible without quality regression

### Not Worth Opening
- **Lane E (Director call consolidation)**: High blast radius, Director prompt redesign, quality regression risk
- **Lane D (strategy reduction on retry)**: Reduces candidate diversity when it matters most (after REJECT)
- **Lane B (skip continuity ep1)**: Already optimized — the guard already prevents the Director call for ep_num=1

## What Should Remain Untouched
- 3-strategy ensemble on first attempt (proven candidate diversity)
- Director compare_and_select quality gate (core quality authority)
- Director continuity check for ep > 1 (prevents breaks)
- Python prevalidation (free, no LLM cost)
- Prompt self-audit checklist (recently landed)
- max_retries=9 default for low-score first attempts (safety net)
- IFC extraction path (Wave 1+2 completed, scope closed)

## Single Recommendation

**No wave yet. Run one fresh instrumented Stage 3 canary first.**

Specifically:
- Use `scripts/run_stage3_canary.py` with `--target-ep 8` (full 2-arc run)
- Source project: `00_0000001` (investment fiction — the genre most likely to trigger retries due to financial constraint complexity)
- After run, extract from `llm_io.jsonl`:
  - Per-call input_tokens, output_tokens, cached_tokens, total_cost_usd
  - Stage 3 retry count distribution per episode
  - Content hash stability across same-arc episodes (for Lane A feasibility)
  - Score distribution for first-attempt PASSes vs REJECTs (for Lane C threshold)

This canary costs ~15-25 min of LLM time and provides the missing data to push Lane A or Lane C to 95% confidence.

## Guardrails
- Do not open Stage 4 compliance or continuity waves (Wave 1+2 closed, no action recommended)
- Do not redesign Director prompts in this assessment
- Do not modify retry/ASP policy without retry distribution data
- Do not change Stage 3 quality gates (ensemble, Director, prevalidation)
- Do not reopen IFC extraction scope

---

## 3-Pass Audit Notes
- Pass 1: scope bounded to Stage 3 latency/efficiency only; 9 evidence surfaces inspected
- Pass 2: prior survey Lane A re-assessed with actual cache key composition evidence — blast radius upgraded from low to medium; token data absence confirmed against both canary sources
- Pass 3: recommendation is bounded (instrumented canary, not implementation); no scope creep
- Confidence: 96% (on the "no wave yet" recommendation; <80% on any specific optimization lane)

---

- Dominant Stage 3 latency source: **retry amplification** (happy-path 184s acceptable; each REJECT adds ~140s; max_retries=9 allows 10× worst case)
- Best next single move: **instrumented Stage 3 canary** (8-ep run with token/cost logging to fill data gap for Lane A and Lane C)
- Should Codex open an execution SSOT now: **no**
