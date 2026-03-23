Date: 2026-03-23
Status: final
Document Type: Q6 selective retrieval R2 delta survey report
Terminal: T6
Canonical Path: `docs/2026-03-23/opus/r2-q6-selective-retrieval.md`
Evidence Path: `docs/2026-03-23/opus/r2-q6-selective-retrieval-evidence.md`
Source Order: `docs/2026-03-23/q1-q8-r2-parallel-deep-survey-order.md`
R1 Baseline: `docs/2026-03-23/opus/q6-selective-retrieval-deep-dive.md`

Commit State:
- Baseline Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
- Baseline Dirty Summary: `dirty workspace allowed; touched surfaces include modules/core/stage3_orchestrator.py, modules/domain/agents/director_ensemble.py, tests/test_stage3_orchestrator.py, tests/test_director_modules.py, docs/temp/queue-state.json`

---

# T6: Q6 Selective Retrieval R2 Delta Survey

## 1. Executive Summary

Q6 asks: **"잘 찾냐"** — Does the system correctly find, route, and retrieve relevant information when the LLM needs it?

R2 status: **4 of 9 R1 P0/P1 findings resolved by commit `79f570f2`.** The commit targeted observability and one contract-cleanup fix. The resolved findings are:
- P0-1 multi-query fallback WARNING (verified exercised 11x in fresh run)
- P1-1 advisor fallback WARNING (verified in code, not exercised — advisor worked)
- P1-3 priority sort before cap (verified in code)
- P1-4 embedding cache invalidation (verified in code)

**5 R1 P0/P1 findings persist** unchanged: P0-2 NPC entity matching, P0-3 RRF asymmetry, P1-2 work focus substring, P1-5 budget exhaustion silent, P1-6 tier-0 insert(0) ordering.

**2 new findings** emerged from fresh-run evidence:
- N-1: Multi-query fallback WARNING message is misleading ("전체 임베딩 실패" vs actual cold-start / no-results)
- N-2: entity_names sparse population in DB (1/3 episodes populated)

**Fresh-run-before-fix allowed: conditional yes** — The critical observability gaps (P0-1, P1-1) are now resolved. The remaining persisting issues (P0-2, P0-3) cause accuracy degradation, not crashes. A fresh run with the current fixes would produce interpretable diagnostic output for Q6, unlike before the fixes.

---

## 2. R1 to R2 Delta Summary

### Resolved (4 items)

| R1 ID | R1 Severity | Summary | Fix Mechanism | Verified |
|-------|-------------|---------|---------------|----------|
| P0-1 | CRITICAL | Multi-query silent fallback — early exit on partial failure | `logging.warning()` added at `vec_memory.py:570` | source + fresh run (11x WARNING in session log) |
| P1-1 | HIGH | Advisor failure → silent legacy fallback | `logging.warning("[Q6-T3]...")` added at `stage4_context_builder.py:1752` | source (not exercised — advisor path worked in fresh run) |
| P1-3 | MEDIUM | Slot truncation before priority sort | `slots.sort(key=lambda s: s.priority)` added at `context_advisor.py:593` | source |
| P1-4 | HIGH | Embedding cache not invalidated on model change | `self._embed_cache.clear()` added at `vec_memory.py:269` | source (not exercised — no model change in fresh run) |

### Persists (5 items)

| R1 ID | R1 Severity | Summary | Why Persists | fix type |
|-------|-------------|---------|-------------|----------|
| P0-2 | HIGH | NPC entity matching — space/boundary LIKE broken | Not in commit scope. `REPLACE(entity_names, ' ', '')` + comma-boundary unchanged at `vec_memory.py:765-771` | contract-cleanup |
| P0-3 | HIGH | Hybrid RRF asymmetric scoring — enumerate rank, not BM25 | Not in commit scope. `fts_rank` is still `enumerate()` position at `vec_memory.py:1125`. RRF formula unchanged at L1138-1149 | contract-cleanup |
| P1-2 | MEDIUM | Work focus source inference — substring false positives | Not in commit scope. `token in haystack` check at `context_advisor.py:767-770` | contract-cleanup |
| P1-5 | MEDIUM | Budget exhaustion silent in CP assembly | Not in commit scope. Silent `break`/`continue` at `stage4_context_packets.py:78-79, 218-219, 249-250` | observability-only |
| P1-6 | MEDIUM | Tier-0 insert(0) ordering inversion | Not in commit scope. All `insert(0, ...)` at `stage4_context_builder.py:1617-1686` | contract-cleanup |

### New (2 items)

| ID | Severity | Summary | Evidence | fix type |
|----|----------|---------|----------|----------|
| N-1 | P2 | Multi-query fallback WARNING message misleading | Fresh run shows 11x "전체 임베딩 실패" warnings for ep<1 through ep<4 where actual cause is empty vector store (cold start), not embedding failure | observability-only |
| N-2 | P2 | entity_names sparse DB population | Fresh run DB: ep=1 empty, ep=2 "한정호" only (3 chars), ep=3 empty. Limits NPC entity retrieval even if P0-2 were fixed | contract-cleanup |

---

## 3. Current Ownership / Flow Map

Unchanged from R1. Key modules:

| Module | Role | Lines |
|--------|------|-------|
| `vec_memory.py` | Vector/FTS/keyword retrieval engine | ~1,370 |
| `context_advisor.py` | Retrieval planning (heuristic + LLM) | ~1,160 |
| `stage4_context_builder.py` | Context assembly + plan execution | ~2,730 |
| `stage4_context_packets.py` | Tier-0 packet assembly | ~800 |

Stage 4 retrieval flow:
```
advisor.plan_stage4_retrieval() → RetrievalPlan (max 8 slots, now priority-sorted)
  → _execute_retrieval_plan() → routes to 4 source types
  → [fallback] retrieve_multi_query_context() (now with WARNING)
```

---

## 4. Focus-Scope Findings

### 4.1 Code-Fix Verification — All 4 fixes verified

**Fix 1: Multi-query fallback WARNING (P0-1)**
- **Before**: `logging.debug()` only, no operator-visible signal
- **After**: `logging.warning("[VecMem] 멀티쿼리 전체 임베딩 실패 → 키워드 폴백 (queries=%d, ep<%d)")` at `vec_memory.py:570`
- **Fresh run verification**: 11 WARNING instances across ep<1 through ep<4 in `projects/0_0323/logs/session_20260323_134127.log`
- **Verdict**: **resolved** — fallback transition now visible to operator
- **Residual**: WARNING message text says "임베딩 실패" but the root cause in early episodes is empty vector store (cold start), not embedding failure. This is a labeling inaccuracy (N-1), not a blocking issue.

**Fix 2: Advisor fallback WARNING (P1-1)**
- **Before**: Silent fallback to legacy vector search when advisor returns None/empty
- **After**: `logging.warning("[Q6-T3] advisor plan 미사용 → 레거시 벡터 검색 폴백 (ep=%d)")` at `stage4_context_builder.py:1752`
- **Fresh run verification**: No `Q6-T3` markers in session log — advisor path was successfully used (confirmed by `observability=advisor_path_used` in STAGE3_EPISODE_SUMMARY)
- **Verdict**: **resolved** — fallback path now observable when it occurs

**Fix 3: Priority sort before cap (P1-3)**
- **Before**: `slots = slots[:cap]` without sorting
- **After**: `slots.sort(key=lambda s: s.priority)` before `slots[:cap]` at `context_advisor.py:593-594`
- **Verdict**: **resolved** — high-priority slots now survive cap truncation

**Fix 4: Embedding cache invalidation (P1-4)**
- **Before**: Warning logged but cache not cleared
- **After**: `self._embed_cache.clear()` on model mismatch at `vec_memory.py:269`
- **Fresh run verification**: `vec_metadata` shows `embed_model=gemini-embedding-001` — no model change during run, so code path not exercised. Code inspection confirms correctness.
- **Verdict**: **resolved** — cache corruption on model change now prevented

### 4.2 Persisting Findings Detail

**P0-2: NPC entity matching (persists)**
- `vec_memory.py:765-771`: `REPLACE(IFNULL(entity_names, ''), ' ', '')` + `%,name,%` LIKE pattern unchanged
- Fresh run DB shows sparse entity_names population (N-2), partially masking this issue
- For names without spaces (한정호, 한시우), the space-removal doesn't cause false negatives
- For multi-token names with spaces, false negatives still occur
- **Not exercised** in fresh run because Korean NPC names don't contain spaces
- **Root-causal**: Yes — limits NPC context retrieval accuracy for non-Korean or multi-token names
- **Blocks rerun**: No — graceful degradation, not crash

**P0-3: RRF asymmetric scoring (persists)**
- `vec_memory.py:1125`: `fts_rank` is `enumerate()` position (0-indexed sequential), not BM25 relevance score
- `vec_memory.py:1138-1149`: RRF formula sums `1/(k+rank)` for each index independently — dual-ranked episodes get up to 2x score
- **Partially exercised** in fresh run: hybrid path used by Director at Stage 4 (`path=hybrid` entries in session log). With few episodes, impact is minimal, but formula is structurally flawed for larger episode sets.
- **Root-causal**: Yes — systematically biases hybrid retrieval toward dual-indexed episodes
- **Blocks rerun**: No — produces suboptimal ranking, not incorrect results

**P1-2: Work focus substring false positives (persists)**
- `context_advisor.py:767-770`: `any(token in haystack for token in cls._WORK_FOCUS_RELATION_TOKENS)`
- Token sets include Korean substring pairs: "관계" matches "관계선", "조직관계"
- Token "동료" appears in BOTH `_WORK_FOCUS_RELATION_TOKENS` (L388) and `_WORK_FOCUS_NPC_TOKENS` (L433) — RELATION wins because it's checked first
- **Not exercised** in fresh run (no work_focus with ambiguous tokens observed)
- **Blocks rerun**: No

**P1-5: Budget exhaustion silent in CP (persists)**
- `stage4_context_packets.py:78-79`: `if used + len(section) > budget: break` — no logging
- Similar silent truncation at L218-219, L249-250
- **Partially exercised** in fresh run: CP was assembled for ep1-4, budget of 7000 chars was likely not exhausted for 5-8 NPCs
- **Blocks rerun**: No

**P1-6: Tier-0 insert(0) inversion (persists)**
- `stage4_context_builder.py:1617-1686`: All tier0 sections use `insert(0, ...)`
- Final order (last-inserted-first): NPC boundary → CP → Canonical → FactLedger → Timeline → WorldState
- CP ends up at position 1 (near beginning, good attention position), but the code pattern is counterintuitive and fragile
- **Exercised** in fresh run: tier0 was assembled for all episodes
- **Blocks rerun**: No — CP is actually well-positioned despite confusing code pattern

---

## 5. Code-Fix Verification

Summarized in section 4.1 above. All 4 fixes from commit `79f570f2` verified via:
- **Git diff**: exact code changes confirmed
- **Live source**: changes present in current workspace
- **Fresh run**: P0-1 fix exercised 11x, P1-1 fix not triggered (positive — advisor worked)

---

## 6. Pre-Rerun T-Report Cross-Reference

### T9 (Context and Retrieval Support Factors)

| T9 Finding | Q6 Alignment | R2 Status |
|------------|-------------|-----------|
| P1-1: Thin vector memory at early episodes | Aligns with fresh run multi-query fallback WARNING pattern (11x for ep<1 through ep<4). Cold-start is inherent, now visible. | Absorbed — P0-1 fix makes cold-start visible |
| P2-1: NPC section cap at 10 names | Unchanged. Not exercised in fresh run (5-8 NPCs per episode). | Persists as-is |
| P2-2: Stage 4 slot cap at 8 | Slot priority sort fix (P1-3) ensures highest-priority slots survive cap. Cap value unchanged. | Partially mitigated by P1-3 fix |
| P2-3: Coverage warning for slot overflow not emitted | Still not emitted. `context_advisor.py` does not log when `len(slots) > stage_cap` before truncation. | Persists |
| P2-4: Embedding cache LRU 512 — no model-change invalidation | **Resolved** by P1-4 fix: `_embed_cache.clear()` on model mismatch. | Resolved |

### Generation Coherence Deep-Dive

| Finding | Q6 Relevance | R2 Status |
|---------|-------------|-----------|
| RT-1: VecMemory embedding failure → LIKE fallback (P0) | Same as R1 P0-1. Now with WARNING. | Resolved (observability) |
| RT-2: ContextAdvisor S4 slot cap 8 + silent truncation (P0) | Priority sort applied (P1-3 fix). Cap value unchanged. Coverage warning still absent. | Partially mitigated |
| RT-3: FTS5 unicode61 → Korean variant loss (P1) | Unchanged. Not in fix scope. | Persists |
| RT-4: LLM enrichment npc<5 not triggered (P1) | Unchanged. Not in fix scope. | Persists |
| RT-5: Embedding cache LRU 512 (P1) | Cache clear on model mismatch now applied (P1-4). LRU size unchanged. | Partially resolved |

---

## 7. Fresh-Run Evidence

### 7.1 Session Log Analysis (`projects/0_0323/logs/session_20260323_134127.log`)

| Metric | Value |
|--------|-------|
| Multi-query fallback WARNINGs | 11 |
| Advisor fallback WARNINGs (Q6-T3) | 0 (advisor path succeeded) |
| Hybrid search calls (Director) | 12+ (ep<1 through ep<2, various queries) |
| Hybrid hits for ep<1 | 0 (cold start — no prior episodes) |
| Hybrid hits for ep<2+ | 1-2 per query |
| semantic_ctx chars (Stage 3) | 2,605 (constant across all episodes) |
| STAGE3_EPISODE_SUMMARY observability | `advisor_path_used,budget_ledger,planned_slots_count,provenance_ledger,semantic_ctx_chars,semantic_ctx_source_counts,semantic_ctx_sources` |

### 7.2 DB Evidence (`projects/0_0323/project_data.db`)

| Table | Key Observation |
|-------|----------------|
| episode_meta | 3 rows: ep=1 (entity_names empty), ep=2 (entity_names="한정호", 3 chars), ep=3 (entity_names empty) |
| vec_metadata | embed_model=gemini-embedding-001, embed_dim=3072 |
| episode_fts | Exists, populated (FTS5 index) |

### 7.3 Key Diagnostic Insights

1. **P0-1 fix exercised**: The WARNING message now makes multi-query fallback visible. All 11 instances show `queries=1` pattern — single-query calls hitting the fallback path. The message successfully distinguishes from normal retrieval.

2. **WARNING message accuracy (N-1)**: The warning text "전체 임베딩 실패" is misleading for early episodes. Embedding likely succeeds, but `vec_episodes` has no qualifying rows (ep_num < current_ep). The code at L548-549 (`emb = self._embed_text(query_text); if emb is None: continue`) skips on embedding failure, but if embedding succeeds and KNN returns 0 rows (all `rowid >= current_ep`), `seen` is still empty and the "임베딩 실패" warning fires. The actual cause is "no vector results" — this is a labeling gap, not a functional gap.

3. **entity_names sparse (N-2)**: Only 1/3 episodes have entity_names populated. This limits the effectiveness of `_collect_npc_entity_candidates()` even with correct matching logic. The memorize path (`memorize_v20_episode`) stores entity_names from state_changes/NPC extraction — sparsity suggests state_changes may not consistently populate entity names.

4. **Advisor path success**: No `Q6-T3` fallback warnings in session log. `advisor_path_used` appears in all STAGE3_EPISODE_SUMMARY entries. The smart retrieval path is working as intended for Stage 3.

---

## 8. Root-Cause vs Symptom Classification

| Finding | Classification | Rationale |
|---------|---------------|-----------|
| P0-1 (multi-query silent fallback) | **Resolved symptom** | Observability fix makes degradation visible but doesn't prevent the fallback itself |
| P0-2 (NPC entity matching) | **Root cause** | Systematic false negatives in NPC context retrieval for names with spaces |
| P0-3 (RRF asymmetry) | **Root cause** | Structural scoring bias in hybrid retrieval ranking |
| P1-1 (advisor fallback) | **Resolved symptom** | Observability fix for mode transition |
| P1-2 (work focus substring) | **Root cause** | Mis-routing of retrieval queries to wrong data source |
| P1-3 (slot priority sort) | **Resolved root cause** | High-priority slots now correctly survive cap truncation |
| P1-4 (cache invalidation) | **Resolved root cause** | Vector space corruption on model change now prevented |
| P1-5 (budget exhaustion silent) | **Symptom** | Budget exhaustion is inherent; silence is the observability gap |
| P1-6 (insert(0) ordering) | **Symptom** | Code pattern is confusing but CP is actually well-positioned |
| N-1 (WARNING message misleading) | **Symptom** | Labeling inaccuracy in newly added warning |
| N-2 (entity_names sparse) | **Root cause** | Limits NPC entity retrieval effectiveness at the data layer |

---

## 9. Quick Wins

| # | Fix | Scope | fix type | ROI | File:Line |
|---|-----|-------|----------|-----|-----------|
| QW-1 | Fix WARNING message: "전체 임베딩 실패" → "벡터 검색 결과 없음 (임베딩 성공 시 cold-start 가능)" | 1 line | observability-only | HIGH | `vec_memory.py:570` |
| QW-2 | Log WARNING on CP budget exhaustion | 4 lines | observability-only | MEDIUM | `stage4_context_packets.py:79, 219, 250` |
| QW-3 | Log coverage_warning when slot count exceeds stage cap | 2 lines | observability-only | MEDIUM | `context_advisor.py:594` (after cap truncation) |
| QW-4 | Use word-boundary regex for work focus source inference | 2 lines | contract-cleanup | MEDIUM | `context_advisor.py:767-770` |

---

## 10. False Leads / Non-Causes

### 10.1 "Advisor path always falls back to legacy" — False

Fresh run evidence shows `Q6-T3` fallback WARNING was never triggered. `observability=advisor_path_used` in all STAGE3_EPISODE_SUMMARY entries. The smart retrieval advisor is successfully planning and executing retrieval for Stage 3.

### 10.2 "Embedding model changed during run" — Not exercised

`vec_metadata` shows consistent `embed_model=gemini-embedding-001`. P1-4 fix is verified in code but was not exercised in this fresh run.

### 10.3 "P1-6 insert(0) puts CP at end of tier0" — Severity overstated in R1

R1 stated "Continuity Packet ends up LAST." In reality, CP is inserted 5th via `insert(0)` and npc_boundary is inserted 6th (last). Final order: `[npc_boundary, CP, canonical, fact_ledger, timeline, world_state]` — CP is at position 1, near the beginning. The code pattern is confusing but the actual position is favorable for attention.

### 10.4 "semantic_ctx constant at 2605 chars indicates broken scaling" — Inconclusive

The 2605-char constant across episodes could indicate a static budget allocation that doesn't scale with available data, or it could be a fixed-size context output (e.g., from a static slot that doesn't grow with episode count). Not enough evidence to classify as a bug without deeper tracing.

---

## 11. Fresh-Run Readiness

**Fresh-run-before-fix allowed: conditional yes**

Changed from R1's **no** to **conditional yes**. Rationale:

1. **Observability gap resolved**: The two most critical observability fixes (P0-1 multi-query fallback WARNING, P1-1 advisor fallback WARNING) are now in place. A fresh run will produce interpretable diagnostic output for Q6.

2. **Remaining P0 items cause degradation, not blindness**: P0-2 (NPC matching) and P0-3 (RRF asymmetry) cause suboptimal retrieval accuracy but don't prevent diagnosis. With the new WARNINGs, operators can now distinguish "retrieval worked correctly" from "retrieval fell back to keyword."

3. **Priority sort fix prevents silent slot dropping**: P1-3 fix ensures high-priority retrieval slots survive cap truncation. This improves retrieval coverage for complex episodes.

4. **Condition**: The fresh run must be accompanied by post-run Q6 observability review, checking:
   - Count of multi-query fallback WARNINGs (should decrease as episodes grow)
   - Presence/absence of `Q6-T3` advisor fallback WARNINGs
   - `advisor_path_used` in STAGE_EPISODE_SUMMARY observability fields
   - entity_names population in episode_meta

**Top 3 highest-ROI remaining fixes:**

1. **QW-1: Fix WARNING message text** (1 line) — Prevents misdiagnosis of cold-start as embedding failure in post-run review
2. **P0-3: RRF scoring normalization** (5-10 lines) — Replace enumerate rank with BM25 score for sparse, normalize dense/sparse scales
3. **P0-2: NPC entity matching** (boundary-refactor, 20-30 lines) — Structured JSON entity storage or exact-match query replacing LIKE + space-removal

---

## 12. Confidence And Limits

**Estimated confidence: 96%**

**Basis:**
- All 4 code fixes verified via git diff + live source inspection
- 3 of 4 primary scope files read (vec_memory.py, context_advisor.py, stage4_context_builder.py) at fix-relevant sections
- stage4_context_packets.py read at P1-5 relevant sections
- Fresh run session log analyzed: 11 multi-query WARNINGs, 0 advisor fallback WARNINGs, hybrid search traces, STAGE3_EPISODE_SUMMARY observability fields
- Fresh run DB queried: episode_meta entity_names (3 rows), vec_metadata (model/dim)
- Git diff for commit `79f570f2` confirms exact scope of changes to Q6 files
- T9 and Generation Coherence cross-referenced: all Q6-relevant findings mapped

**Residual limits (4%):**
- `stage4_context_packets.py` not fully re-read (only P1-5 relevant sections) — 1%
- entity_names population mechanism (`memorize_v20_episode`) not traced to identify why 2/3 episodes have empty names — 1%
- Hybrid RRF scoring not tested with real multi-episode data (only 3 episodes in fresh run DB) — 1%
- smart_retrieval config values not verified against production defaults — 1%

---

## 3-Pass Audit Record

### Pass 1. Structure and Scope
- R1 report fully read with 9 P0/P1 findings and 25 total findings
- R2 order structure followed: 12 mandatory sections included
- All R1 P0/P1 findings classified as resolved/persists/new
- Code fix scope from commit `79f570f2` bounded to 4 changes in 3 files

### Pass 2. Evidence Reconciliation
- All 4 code fixes verified via git diff and live source
- P0-1 fix verified exercised in fresh run (11 WARNING instances)
- P1-1 fix verified NOT exercised (advisor path worked — positive outcome)
- Fresh run DB evidence confirms entity_names sparsity (N-2 finding)
- T9 findings absorbed: 5 items mapped to R2 status
- Generation Coherence findings absorbed: 5 items mapped to R2 status

### Pass 3. Readiness and Confidence
- Fresh-run readiness changed from R1 "no" to R2 "conditional yes" with justification
- 3 highest-ROI remaining fixes ranked
- Root-cause vs symptom classification complete for all 11 findings
- Confidence 96% — all evidence sources consulted, residual gaps bounded and explicit
