# TF-S4DD Track 3: Advisory Chain Completeness Findings

**Date**: 2026-03-13
**Scope**: Stage 4 Advisory Chain — completeness, severity, timeout, dedup, four-principles compliance, Director injection
**Status**: Read-only audit — no code changes

---

## 3.1 Advisory Call Completeness

### ThreadPoolExecutor Submission (L3807-3815)

`_run_advisory_chain()` submits **8 advisories** in the `ThreadPoolExecutor(max_workers=8)`:

| # | Future key | Method | Module |
|---|-----------|--------|--------|
| 1 | TruthGate | `_advisory_truth_gate` | `modules/core/truth_gate.py` |
| 2 | NpcDrift | `_advisory_npc_drift` | `modules/core/npc_drift_advisor.py` |
| 3 | NumericDrift | `_advisory_numeric_drift` | `modules/core/numeric_drift_advisor.py` |
| 4 | Flashback | `_advisory_flashback` | `modules/core/flashback_verifier.py` |
| 5 | InfoParadox | `_advisory_info_paradox` | `modules/core/info_paradox_checker.py` |
| 6 | RelDrift | `_advisory_rel_drift` | `modules/core/relationship_drift_advisor.py` |
| 7 | LongTermRep | `_advisory_long_term_rep` | `modules/core/long_term_repetition_advisor.py` |
| 8 | NumericConsistency | `_advisory_numeric_consistency` | `modules/core/numeric_consistency_checker.py` |

### SceneSimilarity (9th advisory) — INLINE, NOT in ThreadPool

SceneSimilarity is **not** submitted via the ThreadPoolExecutor. Instead it runs **inline** after the advisory chain completes, at L1674-1692 inside the main `run()` flow:

```python
_sim_adv = Stage4ContextBuilder.compute_scene_similarity_advisory(
    _cand_ms, _recent_scene_kws,
)
if _sim_adv:
    _director_mc_parts.append(_sim_adv)
```

This is a **Python-only** Jaccard keyword similarity check (LLM 0 calls), located in `modules/core/stage4_context_builder.py` L1979-2018. It runs synchronously because it is lightweight (no LLM call).

### Timeline (10th advisory) — INLINE, NOT in ThreadPool

Timeline is also **inline**, implemented as two separate injections:

1. **`[Timeline]` cumulative_elapsed** (L1629-1641): Reads `world_state._state["cumulative_elapsed"]` and formats via `NarrativeContextFormatter.format_cumulative_time()`. Python-only, LLM 0 calls.

2. **`[Arc 시간 연속성 참고]` NS-4-S4** (L1643-1672): Extracts time markers from previous/current Arc via `_ns4_extract_time_markers()` (regex, LLM 0 calls). Appended to `_director_mc_parts`.

### Verdict: SPEC MATCH

All 10 advisories from CLAUDE.md are present:
- **8 in ThreadPool**: TruthGate, NpcDrift, NumericDrift, Flashback, InfoParadox, RelDrift, LongTermRep, NumericConsistency
- **2 inline** (Python-only, no LLM): SceneSimilarity, Timeline

The print/log message says "8개 병렬 실행" which is accurate — only 8 use the thread pool. The remaining 2 are lightweight Python computations that don't need parallelization.

---

## 3.2 Severity Tagging

### `_classify_advisory_tier()` (L1005-1021)

| Advisory | Tier | Kind | CLAUDE.md Spec | Match? |
|----------|------|------|----------------|--------|
| TruthGate | 3 | "TruthGate" | CRITICAL | YES |
| NpcDrift | 2 | "NpcDrift" | MAJOR | YES |
| RelDrift | 2 | "RelDrift" | MAJOR | YES |
| Flashback | 2 | "Flashback" | MAJOR | YES |
| InfoParadox | 2 | "InfoParadox" | MAJOR | YES |
| NumericDrift | 1 | "NumericDrift" | INFO | YES |
| LongTermRep | 1 | "LongTermRepetition" | INFO | YES |
| (default) | 1 | "Advisory" | INFO | YES |

### Formatting Pass (L1584-1616)

The severity labels applied when formatting for Director MC also match:

- `[TruthGate` → `[CRITICAL · TruthGate]`
- `[LM-B]` / `NpcDrift` → `[MAJOR · NpcDrift]`
- `[LM-D]` / `RelDrift` → `[MAJOR · RelDrift]`
- `[LM-E]` / `Flashback` → `[MAJOR · Flashback]`
- `[LM-F]` / `InfoParadox` → `[MAJOR · InfoParadox]`
- Everything else → `[INFO]`

### Discrepancy: NumericDrift severity label in output

Within `_advisory_numeric_drift()` (L3942), the per-item label is `[MAJOR]`:
```python
_nd_lines.append(f"- [MAJOR] '{_nd.get('key', '')}': ...")
```

But the CLAUDE.md spec classifies NumericDrift as INFO, and `_classify_advisory_tier` returns tier=1 (INFO). The `[MAJOR]` label here is the **per-item severity from the advisor module**, not the overall advisory tier. The formatting pass (L1616) would apply `[INFO]` to it since it doesn't match any MAJOR tags. This is **cosmetically inconsistent** but functionally correct — the suppression logic uses tier=1, which is correct.

**Verdict**: Severity tiers match spec. Minor cosmetic: NumericDrift items internally tagged `[MAJOR]` but the advisory as a whole is correctly classified as INFO tier.

---

## 3.3 Timeout Handling

### Per-advisory timeout: 60s — CONFIRMED

```python
result = future.result(timeout=60)  # L3821
```

### Global timeout: 300s — CONFIRMED

```python
for future in as_completed(futures, timeout=300):  # L3818
```

### Fail-open on failure — CONFIRMED

```python
except Exception as e:
    logging.debug("[Advisory] %s 실패 (비치명): %s", _name, e)  # L3826
```

On exception (timeout or any other error), the advisory is silently skipped with a debug log. No exception propagates. The manuscript pipeline continues.

Each individual `_advisory_*` method also has its own try/except with `logging.warning()` and `return []`, providing double-layer fail-open protection.

### Conditional guards (additional fail-safe):

- `NumericDrift`: Only runs on episodes divisible by 5 (`next_ep % 5 != 0` → early return)
- `RelDrift`: Skips if `next_ep < 5`
- `LongTermRep`: Skips if `next_ep < 20`
- `InfoParadox`: Skips if POV is not 1인칭

**Verdict**: Timeout handling fully matches spec. Fail-open confirmed at two levels.

---

## 3.4 Advisory Dedup/Suppression

### `_suppress_conflicting_advisories()` (L1066-1109)

**Algorithm**:
1. Each advisory part is classified by `_classify_advisory_tier()` → `(tier, kind)`
2. Subject extraction via `_extract_advisory_subjects()` → `(explicit_names, broad_tokens)`
   - Explicit: regex captures NPC names in `'...'` patterns
   - Broad: all Korean/ASCII tokens > 1 char, minus stopwords
3. Iterate from highest tier down. For each high-tier advisory, check lower-tier advisories for subject overlap:
   - `high.explicit ∩ low.explicit`
   - `high.explicit ∩ low.broad`
   - `low.explicit ∩ high.broad`
4. If overlap found, suppress the lower-tier advisory

**Effect**: If TruthGate (tier=3) and NpcDrift (tier=2) both flag NPC "김수현", the NpcDrift entry is suppressed. This prevents Director from seeing duplicate warnings about the same NPC at different severity levels.

**Invocation**: Called at L1565:
```python
_advisory_parts = self._suppress_conflicting_advisories(_advisory_parts or [])
```

**Verdict**: Sound dedup logic. Higher-tier advisory wins when subjects overlap. No risk of losing critical information — the more severe warning is always preserved.

---

## 3.5 Four Principles Compliance

### Principle 1: Python collects, LLM judges

**COMPLIANT**. All advisory methods follow this pattern:
- Python gathers data (NPC registry, fact ledger, DB queries, world state)
- LLM-backed advisories (NpcDrift, Flashback, InfoParadox, RelDrift, LongTermRep, NumericDrift) call `llm_ask` to **analyze**, but their output is **advisory text only**
- NumericConsistency and SceneSimilarity are pure Python (LLM 0 calls)
- Timeline is pure Python (regex extraction)
- No advisory modifies any data structure

### Principle 2: Only LLM modifies factsheets

**COMPLIANT**. No advisory writes to NPC registry, world state, fact ledger, or DB. They only read.

One subtle point: `_advisory_truth_gate` writes `truth_gate_warnings` into `validation_results[i]` (L3859):
```python
validation_results[_ci].setdefault("truth_gate_warnings", _tg_result["structured_warnings"])
```
This is metadata annotation on the validation result dict, not factsheet modification. Acceptable.

### Principle 3: Director sovereignty

**COMPLIANT**. Every advisory header explicitly states "참고용 advisory — 최종 판단은 Director":
- NpcDrift: "참고용 advisory — 최종 판단은 Director"
- Flashback: "참고용 advisory — 최종 판단은 Director"
- InfoParadox: "참고용 advisory — 최종 판단은 Director"
- RelDrift: "참고용 advisory — 최종 판단은 Director"
- LongTermRep: "참고용 advisory — 최종 판단은 Director"
- NumericConsistency: "각 항목에 대해 numeric_consistency_review에서 AGREE/DISMISS 판정 필수"

TruthGate header says "CRITICAL 경고 시 반드시 REJECT" — this is the strongest directive, but it's still presented as advisory text in the Director's mandatory context, not as a programmatic REJECT. The Director LLM makes the final call.

No advisory forces a REJECT or modifies the Director's verdict programmatically.

### Principle 4: Deceased NPCs — appearance = REJECT

**COMPLIANT**. `TruthGate._check_deceased_resurrection()` (L79-167):
- Collects deceased NPCs from `npc_registry` (status="dead") + `world_state.get_deceased_npcs()`
- Checks manuscript for name + action verbs (said/did patterns)
- Allows recall patterns: "회상", "과거", "기억", "떠올", "추억", "생전", "살아있을 때", "그때"
- Flags as **CRITICAL** severity with check type "deceased_resurrection"
- Also detects resurrection attempts in state_updates (status changing from "dead" to something else)

**Verdict**: All four principles fully respected.

---

## 3.6 Director MC Injection Flow

### Data flow trace:

1. **Advisory chain execution** (L1564):
   ```python
   _advisory_parts = self._run_advisory_chain(candidates, validation_results, next_ep, genre_name)
   ```

2. **Dedup/suppression** (L1565):
   ```python
   _advisory_parts = self._suppress_conflicting_advisories(_advisory_parts or [])
   ```

3. **Summary tracking** (L1566-1583): Builds `_advisory_summary` dict for logging.

4. **Severity formatting** (L1584-1617): Each part gets `[CRITICAL · ...]`, `[MAJOR · ...]`, or `[INFO]` prefix.

5. **Prepend to `_director_mc_parts`** (L1619):
   ```python
   _director_mc_parts = _advisory_parts + _director_mc_parts
   ```
   Advisory parts are placed **first** (before WritingDirective, S3-META, POV, shared failure warnings).

6. **Inline advisories appended** (L1629-1696):
   - `[Timeline]` cumulative_elapsed
   - `[Arc 시간 연속성 참고]` NS-4-S4 time markers
   - `[SceneSimilarity]` scene duplication
   - Candidate diversity advisory
   - Preflight advisory
   - Python validation warnings
   - V69.1 manuscript conflict warnings
   - DB advisories (reference-only block)
   - Work guard review advisory

7. **Final join** (L1763):
   ```python
   _director_mandatory_context = "\n\n".join(str(x) for x in _director_mc_parts if x is not None)
   ```

8. **Passed to Director** (L1765):
   ```python
   director_result = self.ctx.agents["director"].select_and_judge_ensemble(
       ep_num=next_ep,
       ...
       mandatory_context=_director_mandatory_context,
       ...
   )
   ```

### Ordering in Director MC:

1. Advisory chain results (CRITICAL first, then MAJOR, then INFO)
2. WritingDirective
3. S3-META quality_risk warning
4. Shared failure warnings
5. POV/외부시점 policy
6. Timeline / SceneSimilarity / diversity / preflight / validation warnings
7. DB advisories (reference-only)
8. Work guard review

**Verdict**: Clean injection path. Advisory results are prominently placed at the top of Director's mandatory context, ensuring they are seen first. No advisory bypasses Director.

---

## Summary

| Check | Result | Notes |
|-------|--------|-------|
| 3.1 Advisory completeness | PASS | All 10 advisories present (8 threaded + 2 inline) |
| 3.2 Severity tagging | PASS | Matches CLAUDE.md spec; minor cosmetic: NumericDrift items say [MAJOR] internally |
| 3.3 Timeout handling | PASS | 60s per-advisory, 300s global, double-layer fail-open |
| 3.4 Dedup/suppression | PASS | Higher-tier suppresses lower-tier on subject overlap |
| 3.5 Four principles | PASS | All 4 principles fully respected |
| 3.6 Director MC injection | PASS | Advisory → dedup → format → prepend to MC → join → Director |

**No code changes required. Advisory chain is complete and correctly implemented.**
