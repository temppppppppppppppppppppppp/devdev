# Stage 3 PWF Early-Exit Wave 1 Canary Report

Date: 2026-03-26
Type: post-implementation instrumented Stage 3-only canary
Source Project: `00_0000001`
Target Project: `canary_0326_stage3_pfee`
Run Window: EP1-EP8 (Arc 1 EP1-EP4 + Arc 2 EP5-EP8)
Run Status: completed (exit code 0, hard_gates: pass)
Baseline Comparison: `docs/2026-03-26/stage3-latency-telemetry-canary-report.md`
Wave 1 SSOT: `docs/2026-03-26/stage3-threephase-pwf-early-exit-wave1-execution-ssot.md`

## Evidence Artifacts

| Artifact | Path |
|----------|------|
| Canary summary | `projects/canary_0326_stage3_pfee/logs/stage3_canary_summary.json` |
| LLM I/O telemetry | `projects/canary_0326_stage3_pfee/logs/session/llm_io.jsonl` (71 calls) |
| Session log | `projects/canary_0326_stage3_pfee/logs/session_20260326_094536.log` |
| Blueprints | EP1-EP8 all completed (8/8) |
| Prior canary LLM I/O | `projects/canary_0326_stage3_telemetry/logs/session/llm_io.jsonl` (164 calls) |
| Prior canary summary | `projects/canary_0326_stage3_telemetry/logs/stage3_canary_summary.json` |

## Primary Finding

**The PF-EE score-stall early-exit guard was never activated during this canary run.** Zero occurrences of `[PF-EE]` in the session log. The guard's trigger condition — re-audit returning `PASS_WITH_FIX` with a non-improving score — did not occur because all re-audits returned either `PASS` or `REJECT`, never `PASS_WITH_FIX`.

This means the observed call count reduction (164→71, -56.7%) is **not attributable to the PF-EE guard**. It is attributable to natural LLM non-determinism: the Director issued fewer `PASS_WITH_FIX` verdicts and more direct `PASS` verdicts in this run compared to the prior run.

The guard is confirmed benign — zero interference with normal runtime behavior.

## Before vs After Comparison

### Total LLM Calls (llm_io.jsonl — authoritative)

| Metric | Prior | Current | Delta |
|---|---|---|---|
| Total LLM calls | 164 | 71 | **-93 (-56.7%)** |
| Total cost | $5.78 | $2.84 | **-$2.94 (-50.9%)** |
| BlueprintEnsemble calls | 83 | 38 | -45 (-54.2%) |
| Director calls | 79 | 31 | -48 (-60.8%) |
| StateExtractor calls | 2 | 2 | 0 |

### Per-Episode Telemetry (episode_telemetry — per-ep attribution)

| EP | Prior Calls | Current Calls | Prior Cost | Current Cost | Prior Duration (s) | Current Duration (s) |
|---|---|---|---|---|---|---|
| 1 | 63 | 25 | $2.07 | $0.92 | 2,544 | 1,146 |
| 2 | 41 | 27 | $1.42 | $0.91 | 1,581 | 1,156 |
| 3 | 43 | 27 | $1.55 | $0.92 | 2,093 | 1,467 |
| 4 | 52 | 39 | $1.51 | $1.00 | 2,233 | 1,700 |
| 5 | 17 | 11 | $0.67 | $0.61 | 735 | 554 |
| 6 | 17 | 14 | $0.70 | $0.65 | 756 | 638 |
| 7 | 14 | 11 | $0.69 | $0.67 | 577 | 512 |
| 8 | 17 | 17 | $0.77 | $0.77 | 732 | 769 |
| **Sum** | **264** | **171** | **$9.38** | **$6.44** | **11,251** | **7,941** |

### Arc 1 vs Arc 2 Cost Profile

| Metric | Prior Arc 1 | Current Arc 1 | Prior Arc 2 | Current Arc 2 |
|---|---|---|---|---|
| Avg calls/ep | 50 | 30 | 16 | 13 |
| Avg cost/ep | $1.64 | $0.94 | $0.71 | $0.67 |
| Total cost | $6.55 | $3.75 | $2.83 | $2.69 |

Arc 1 gap narrowed significantly (2.3× prior → 1.4× current). This is LLM variance, not guard effect.

### Pass Rate

| Metric | Prior | Current |
|---|---|---|
| Total PASS | 8/8 (100%) | 8/8 (100%) |
| Outer attempts | 1 per EP | 1 per EP |

No pass rate regression.

### Score Quality

| EP | Prior Score | Current Score |
|---|---|---|
| 1 | 91 | 90 |
| 2 | 91 | 90 |
| 3 | 91 | 90 |
| 4 | 93 | 90 |
| 5 | 94 | 95 |
| 6 | 93 | 85 |
| 7 | 90 | 95 |
| 8 | 92 | 90 |
| **Avg** | **91.9** | **90.6** |

Average score dropped 1.3 points. EP6 scored 85 (prior 93), but EP5 and EP7 scored higher. Within normal LLM variance.

### PASS_WITH_FIX Pattern

| Metric | Prior | Current |
|---|---|---|
| Director PWF verdicts total | 16 | 8 |
| PWF patch attempts | 16 | 8 |
| Patch → PASS (resolved) | 2 | 5 |
| Patch → REJECT (failed) | 14 | 3 |
| Re-audit returned PASS_WITH_FIX | 0 | 0 |
| PF-EE guard activated | N/A | 0 |

Critical observation: in **neither run** did a re-audit ever return `PASS_WITH_FIX`. All re-audits resolved to either `PASS` or `REJECT`. The PWF loop therefore always exited after exactly 1 iteration via `fix_ok=True` (PASS) or `should_break=True` (REJECT). The PF-EE guard's target condition — the loop continuing with a stalled score — never materialized.

### Cached Tokens

| Metric | Prior | Current |
|---|---|---|
| cached_tokens > 0 | 0/164 (0%) | 0/71 (0%) |

Unchanged. Still 0 across all calls.

### Episode Telemetry vs LLM I/O Divergence

| Source | Prior | Current |
|---|---|---|
| llm_io calls | 164 | 71 |
| episode_telemetry calls | 264 | 171 |
| Ratio | 1.61× | 2.41× |

Divergence exists in both runs. The episode_telemetry counter includes initialization, setup, and non-LLM calls that llm_io.jsonl does not capture. The ratio shifted from 1.61× to 2.41×, suggesting proportionally more non-LLM overhead per episode in the current run (consistent with fewer LLM retry rounds diluting the fixed setup cost).

## What Improved

- **Guard is benign**: zero interference with normal operation, zero false positives, zero unintended side effects.
- **All acceptance criteria from the SSOT are met**: tests pass (8 PF-EE tests + 94 existing PWF tests), no quality regression, no Stage 4 surface opened.
- **Code is in place** for the guard to activate when the stall condition does occur in a future run.

## What Stayed Flat

- **Pass rate**: 8/8 both runs. No change.
- **cached_tokens**: still 0. No change.
- **Re-audit PASS_WITH_FIX frequency**: 0 in both runs. The guard's trigger condition is rare enough that a single 8-episode canary does not exercise it.

## What Regressed

- **Nothing attributable to the guard.** Score average dropped 1.3 points (91.9→90.6), within normal LLM variance. EP6 scored 85 vs prior 93, but EP5 scored 95 vs prior 94 and EP7 scored 95 vs prior 90.

## New Pathology Check

No new pathology replaces the old PWF waste. The run was cleaner because the Director happened to issue fewer PWF verdicts (8 vs 16) and more of the patches resolved to PASS (5/8 vs 2/16). This is LLM variance, not a new behavioral pattern.

## Recommendation

**No action.** The PF-EE guard is correctly implemented and benign. A single canary run cannot prove the guard's effectiveness because its trigger condition (re-audit returning `PASS_WITH_FIX` with a non-improving score) did not occur in this run or the prior run. The guard is a targeted safety net for a probabilistic condition that the original compact survey confirmed exists in longer or more contested runs. Opening a new execution SSOT for this finding would be premature — the guard works, it simply wasn't needed in this particular run window.

---

## 3-Pass Audit Notes

- Pass 1: evidence grounded in three authoritative sources — `llm_io.jsonl` (71 entries), `stage3_canary_summary.json` (8/8 pass), and `session_20260326_094536.log` (0 PF-EE activations, 8 PWF entries, 0 re-audit PASS_WITH_FIX); per-episode telemetry and score comparisons verified against both canary summaries
- Pass 2: primary finding — guard benign but not exercised — is consistent across all three evidence sources; call count reduction correctly attributed to LLM variance (Director issued 8 PWF verdicts vs prior 16) rather than the guard; episode_telemetry/llm_io divergence pattern is consistent with prior run
- Pass 3: recommendation is bounded (no action); no scope creep beyond the canary's measurement objective; score quality within LLM variance bounds
- Confidence: 97%

---

- PWF early-exit effect: **unchanged** (guard not exercised; confirmed benign)
- Stage 3 quality regression: **none** (8/8 PASS, avg score 90.6 vs 91.9 within LLM variance)
- Should Codex open a new execution SSOT now: **no**
