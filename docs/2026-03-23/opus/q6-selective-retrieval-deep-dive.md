Date: 2026-03-23
Status: final (3-pass audited)
Document Type: Q6 selective retrieval deep-dive survey report
Canonical Path: `docs/2026-03-23/opus/q6-selective-retrieval-deep-dive.md`
Source Order: `docs/2026-03-23/q1-q8-current-state-parallel-deep-survey-order.md` (T6)
Evidence Manifest: `docs/2026-03-23/opus/q6-selective-retrieval-evidence-manifest.md`

---

## 1. Executive Summary

Q6 asks: **"잘 찾냐"** — Does the system correctly find, route, and retrieve relevant information when the LLM needs it?

The selective retrieval subsystem has a well-designed **multi-source, multi-tier architecture** spanning 4 retrieval stores (VEC_MEMORY, DB_NPC_HISTORY, DB_NPC_RELATIONSHIP, STATIC/manuscript_db), an LLM-enrichable advisor planner, and a budget-aware context assembler. The fresh run confirmed 213 LLM calls at 100% success with no retrieval crashes.

However, the subsystem suffers from **silent degradation**: retrieval failures, fallback transitions, and budget exhaustion all occur without logging or metrics. The LLM receives incomplete context but neither the operator nor the system can detect the gap. This is the dominant Q6 quality risk.

**Top 3 findings:**
1. **Multi-query silent fallback** (P0): When vector embedding fails mid-batch, the system silently switches to keyword-only search for the first query and returns, ignoring remaining queries. No warning emitted.
2. **NPC entity matching fragility** (P0): Space-removal + comma-boundary LIKE search in `vec_memory.py` doesn't match real multi-token entity names stored as-is. False negatives in NPC context retrieval.
3. **Advisor failure opacity** (P1): When `context_advisor.plan_stage4_retrieval()` returns None or empty, `stage4_context_builder.py` silently falls back to legacy vector search without logging the transition.

**Fresh-run-before-fix allowed: no** — Silent retrieval failures mean a fresh run cannot distinguish "correct retrieval" from "silently degraded retrieval." Fixes for observability (at minimum) should precede the next live run.

---

## 2. Current Ownership / Flow Map

### 2.1 Module Responsibilities

| Module | Role | Lines | Owner Pattern |
|--------|------|-------|---------------|
| `vec_memory.py` | Vector/FTS/keyword retrieval engine | ~1,370 | Standalone class, shared DB conn |
| `context_advisor.py` | Retrieval planning (heuristic + LLM) | ~1,160 | Planner, no execution authority |
| `stage4_context_builder.py` | Context assembly + plan execution | ~2,730 | Executor, owns budget/trimming |
| `stage4_context_packets.py` | Tier-0 packet assembly (CP, world state, fact ledger) | ~800 | Packet builder, no retrieval authority |

### 2.2 Retrieval Flow (Stage 4 Hot Path)

```
stage4_orchestrator.py
  → stage4_context_builder.build_mandatory_context()
    ├─ Tier 0: context_packets.build_continuity_packet()
    │   └─ DB: get_npc_history(), get_relationship_history(), get_canonical_facts()
    ├─ Tier 0: context_packets.build_condensed_world_state_summary()
    │   └─ world_state._state (CP-aware dedup)
    ├─ Tier 0: context_packets.build_condensed_fact_ledger_summary()
    │   └─ fact_ledger._ledger (CP-aware dedup)
    ├─ Tier 1: _collect_stage4_retrieval_context()
    │   ├─ context_advisor.plan_stage4_retrieval() [smart path]
    │   │   └─ _execute_retrieval_plan() → routes to 4 source types
    │   └─ vec_memory.retrieve_multi_query_context() [legacy fallback]
    └─ Tier 2: context_packets.build_tier12_auxiliary_sections()
        └─ state_tracker summaries, hierarchical context, genre-ext, etc.
```

### 2.3 VecMemory Call Sites (6 stages)

| Caller | Method | Source Routing |
|--------|--------|----------------|
| `stage2_preflight.py` L291-334 | retrieve_npc_context / hybrid / high_res / multi_query | threshold-based mode selection |
| `stage3_orchestrator.py` L1073-1086 | retrieve_npc_context / multi_query | slot_source routing |
| `stage4_context_builder.py` L1023-1060 | retrieve_npc_context / hybrid / multi_query | advisor plan execution |
| `stage4_context_builder.py` L1790 | retrieve_multi_query_context | legacy fallback |
| `stage4_director_runtime.py` L1043-1076 | retrieve_npc_context / multi_query | advisor slot routing |
| `stage4_interview_round.py` L4729-4734 | retrieve_high_res_context | flashback advisory |

---

## 3. Top Hotspots

### P0 Findings (3)

#### P0-1. Multi-Query Silent Fallback — Early Exit on Partial Failure
- **File:Line**: `modules/core/vec_memory.py:550-581`
- **fix type**: `observability-only`
- **Issue**: When vector embedding fails for some queries in `retrieve_multi_query_context()`, exceptions are caught at debug level. If ALL queries fail, fallback to `_keyword_fallback_search()` fires for the FIRST query only and returns immediately — remaining queries ignored.
- **Impact**: Caller receives keyword-only results for 1 query out of N. No warning emitted. LLM gets incomplete context but system reports success.
- **Evidence**: L562-564 catches SQL exception at `logging.debug()`. L566-581 early-exits on first fallback hit.

#### P0-2. NPC Entity Matching — Space/Boundary Logic Broken
- **File:Line**: `modules/core/vec_memory.py:762-768`
- **fix type**: `contract-cleanup`
- **Issue**: `_collect_npc_entity_candidates()` removes ALL spaces from entity_names column (`REPLACE(entity_names, ' ', '')`) and wraps in comma boundaries (`%,name,%`). But `memorize_v20_episode()` stores entity_names as-is (with spaces, commas, mixed formats). This creates systematic false negatives.
- **Impact**: NPC context retrieval misses valid episodes when NPC names contain spaces or are stored within longer comma-separated lists.
- **Example**: Stored "Kim Soo-ho, Jade Sword Master" → search for `%,KimSoo-ho,%` → no match.

#### P0-3. Hybrid RRF Fusion — Asymmetric Scoring
- **File:Line**: `modules/core/vec_memory.py:670-679, 1122, 1142-1145`
- **fix type**: `contract-cleanup`
- **Issue**: RRF formula gives episodes with BOTH dense and sparse rankings up to 2x the score of episodes appearing in only one index. Additionally, `fts_rank` in `_fts_search()` is actually `enumerate()` position (L1122), not the BM25 score — so dense rank and sparse "rank" are not comparable quantities.
- **Impact**: Hybrid retrieval systematically favors episodes that happen to appear in both indices, regardless of actual relevance. Dense-only perfect matches can be outranked by mediocre dual-ranked episodes.

### P1 Findings (6)

#### P1-1. Advisor Failure → Silent Legacy Fallback
- **File:Line**: `modules/core/stage4_context_builder.py:1708-1748`
- **fix type**: `observability-only`
- **Issue**: When `context_advisor.plan_stage4_retrieval()` returns None/empty, code silently falls through to legacy vector search. No logging of the transition. Coverage warnings cannot distinguish smart-planned vs. fallback retrieval.

#### P1-2. Work Focus Source Inference — Substring False Positives
- **File:Line**: `modules/core/context_advisor.py:761-769`
- **fix type**: `contract-cleanup`
- **Issue**: `_infer_work_focus_source()` uses substring `in` check for Korean tokens. "관계" matches both "관계선" and "조직관계", routing non-relationship items to DB_NPC_RELATIONSHIP. Should use word-boundary matching.

#### P1-3. Slot Truncation Before Priority Sort
- **File:Line**: `modules/core/context_advisor.py:592`
- **fix type**: `contract-cleanup`
- **Issue**: `slots = slots[:cap]` truncates AFTER building slots but BEFORE sorting by priority. If work_focus slots are added first, they occupy early positions and high-priority arc slots may be dropped.

#### P1-4. Embedding Cache Not Invalidated on Model Change
- **File:Line**: `modules/core/vec_memory.py:251-280`
- **fix type**: `contract-cleanup`
- **Issue**: When embed_model changes (detected at L265), a warning is logged but the in-memory LRU cache (512 entries) is NOT cleared. New queries embed with new model, cached queries use old vectors. KNN search across mixed vector spaces gives meaningless distances.

#### P1-5. Continuity Packet Budget Exhaustion — Silent
- **File:Line**: `modules/core/stage4_context_packets.py:78-81, 218-221, 238-240, 249-252`
- **fix type**: `observability-only`
- **Issue**: Budget loops in `build_continuity_packet()` silently `break` or `continue` when budget exhausted. No logging. Caller unaware that only 4 of 15 NPCs were included, or that relationship section was dropped.

#### P1-6. Tier-0 Ordering Inversion via `insert(0, ...)`
- **File:Line**: `modules/core/stage4_context_builder.py:1617-1686`
- **fix type**: `contract-cleanup`
- **Issue**: Tier-0 sections are all added via `insert(0, ...)`, reversing the intended order. Continuity Packet (most important) ends up LAST in the tier-0 block, positioned furthest from the LLM's strongest attention region.

---

## 4. Quick Wins

| # | Fix | Scope | fix type | ROI | File:Line |
|---|-----|-------|----------|-----|-----------|
| QW-1 | Log WARNING when multi-query fallback triggers | 3 lines | observability-only | HIGH | `vec_memory.py:566` |
| QW-2 | Log WARNING when advisor plan returns None → legacy fallback | 2 lines | observability-only | HIGH | `stage4_context_builder.py:1733` |
| QW-3 | Clear `_embed_cache` on model mismatch detection | 1 line | contract-cleanup | HIGH | `vec_memory.py:267` |
| QW-4 | Sort slots by priority BEFORE cap truncation | 1 line (move) | contract-cleanup | MEDIUM | `context_advisor.py:592` |
| QW-5 | Log budget exhaustion in continuity packet assembly | 4 lines | observability-only | MEDIUM | `stage4_context_packets.py:79` |
| QW-6 | Use word-boundary regex for work focus source inference | 2 lines | contract-cleanup | MEDIUM | `context_advisor.py:765-768` |
| QW-7 | Unify fallback metadata strings across retrieval paths | 3 lines | contract-cleanup | LOW | `vec_memory.py:1019, 722, 875` |

---

## 5. Boundary Refactor Candidates

### BR-1. VecMemory Retrieval → Source-Attributed Results
- **Current**: All 4 public retrieve methods return `str` — raw text with no source metadata.
- **Proposed**: Return `RetrievalResult(text, source, method, fallback_used, query_count, hit_count)` dataclass.
- **Benefit**: Enables per-source quality metrics, coverage warnings, and observability without changing caller behavior (callers that only need `str` use `.text`).
- **Scope**: `vec_memory.py` 4 public methods + all callers (6 files, ~15 call sites).
- **fix type**: `boundary-refactor`

### BR-2. Context Advisor → Coverage Metrics Payload
- **Current**: `RetrievalPlan` contains slots list but no execution-result metadata.
- **Proposed**: Add `CoverageReport` to plan execution output: `{ slots_planned, slots_executed, slots_empty, slots_fallback, source_distribution }`.
- **Benefit**: Enables post-hoc retrieval quality analysis. Coverage warnings become data-driven instead of string-matching.
- **Scope**: `context_advisor.py` + `stage4_context_builder.py:_execute_retrieval_plan()`.
- **fix type**: `boundary-refactor`

### BR-3. NPC Entity Storage → Structured Format
- **Current**: `entity_names` stored as comma-separated string in `episode_meta`. LIKE search with space-removal doesn't match correctly.
- **Proposed**: Store entity_names as JSON array. Use JSON_EACH for matching. Eliminates boundary/space issues.
- **Scope**: `vec_memory.py:memorize_v20_episode()` (write) + `_collect_npc_entity_candidates()` (read) + migration.
- **fix type**: `boundary-refactor`

---

## 6. Fresh-Run Relevance

### Fresh-run-before-fix allowed: no

**Rationale**: The dominant Q6 risk is **silent degradation**. A fresh run cannot reveal whether retrieval is working correctly because:
1. Multi-query fallback produces results (just wrong/incomplete ones) — no error signal
2. NPC entity mismatches silently return empty — no crash
3. Advisor fallback silently works — just less optimal
4. Budget exhaustion silently truncates — context looks normal but is incomplete

A fresh run would appear successful even if retrieval quality is severely degraded.

### Top 3 highest-ROI code fixes before next fresh run

1. **QW-1 + QW-2: Retrieval fallback logging** (5 lines total)
   - Makes retrieval mode transitions visible in console/logs
   - Enables post-run diagnosis of "did smart retrieval actually fire?"
   - Reason: `observability gap` — without this, fresh run results are uninterpretable for Q6

2. **QW-3: Embedding cache invalidation on model change** (1 line)
   - Prevents vector space corruption if model version changes between runs
   - Reason: `retrieval accuracy` — mixed vector spaces produce meaningless KNN results

3. **QW-4: Slot priority-sort before cap** (1 line move)
   - Ensures high-priority retrieval slots survive when budget is tight
   - Reason: `retrieval coverage` — P1 arc/continuity slots dropped in favor of lower-priority work_focus

---

## 7. Confidence And Limits

**Estimated confidence: 95%**

**Basis:**
- All 4 primary scope files read in full (1,370 + 1,160 + 2,730 + 800 lines)
- All 6 caller sites verified via grep (stage2_preflight, stage3_orchestrator, stage4_context_builder, stage4_director_runtime, stage4_interview_round, stage0/reverse_expander)
- All 4 VecMemory public retrieval methods analyzed including internal engines
- Context advisor routing logic + slot building for all 4 stages verified
- Budget trimming 4-phase logic in stage4_context_builder traced end-to-end
- Continuity packet assembly budget loops and fallback chains verified
- Cross-referenced with fresh-run report (P2-1 NPC encyclopedia DEGRADED aligns with P0-2 entity matching issue)

**The 5% gap is from:**
- No live retrieval trace data available (fresh run logs don't capture retrieval method selection) — 2%
- `smart_retrieval` config values not verified against production defaults — 1%
- `config/smart_retrieval/genre_hints.yaml` content not inspected — 1%
- Hybrid RRF score distribution not tested with real episode vectors — 1%

---

## 8. Cross-Axis References

| Finding | Related Axis | Note |
|---------|-------------|------|
| P0-1 silent fallback | Q8 (logging) | Decision-bearing retrieval mode change not logged |
| P0-2 NPC matching | Q5 (consistency) | NPC history gaps affect long-term coherence |
| P1-1 advisor opacity | Q7 (context reception) | LLM may receive legacy context when smart context was expected |
| P1-5 budget exhaustion | Q7 (context reception) | Tier-0 truncation affects prompt completeness |
| P1-6 ordering inversion | Q7 (context reception) | CP attention priority degraded by position |

---

## 9. Appendix: Full Finding Inventory

### A. vec_memory.py (8 findings)

| ID | Severity | Category | Summary | Line |
|----|----------|----------|---------|------|
| P0-1 | CRITICAL | failure-mode | Multi-query silent fallback early exit | 550-581 |
| P0-2 | HIGH | store-accuracy | NPC entity matching space/boundary broken | 762-768 |
| P0-3 | HIGH | ranking | Hybrid RRF asymmetric fusion + rank type mismatch | 670-679, 1122 |
| P1-4 | HIGH | cache | Embedding cache not invalidated on model change | 251-280 |
| P1-A | MEDIUM | routing | retrieve_high_res_context delegation inconsistency | 487-496 |
| P1-B | MEDIUM | ranking | Arc bonus missing in multi-query path | 519-526 |
| P1-C | MEDIUM | fallback | Keyword fallback 2-char min + recency-only ordering | 1037-1084 |
| P1-D | MEDIUM | metadata | Inconsistent fallback strings across retrieval paths | 1019, 722, 875 |

### B. context_advisor.py (6 findings)

| ID | Severity | Category | Summary | Line |
|----|----------|----------|---------|------|
| P1-2 | MEDIUM | routing | Work focus substring false positives | 761-769 |
| P1-3 | MEDIUM | coverage | Slot truncation before priority sort | 592 |
| P1-E | MEDIUM | routing | LLM enrichment hardcoded to VEC_MEMORY source | 618 |
| P1-F | MEDIUM | coverage | Scene query empty without warning | 1026-1044 |
| P1-G | MEDIUM | routing | Relationship query format tightly coupled to parser | 1007-1009 |
| P2-A | LOW | performance | NPC roster dedup via set() only at final collection | 855 |

### C. stage4_context_builder.py (6 findings)

| ID | Severity | Category | Summary | Line |
|----|----------|----------|---------|------|
| P1-1 | HIGH | observability | Advisor failure → silent legacy fallback | 1708-1748 |
| P1-6 | MEDIUM | ordering | Tier-0 insert(0) inversion | 1617-1686 |
| P1-H | MEDIUM | coverage | Fallback NPC field list only 3/8 state_change keys | 1750-1787 |
| P1-I | MEDIUM | budget | Headroom calculation inflates (20% of limit) | 1248-1249 |
| P1-J | MEDIUM | observability | World state/fact ledger nested null chains | 1605-1620 |
| P1-K | LOW | coverage | Genre queries hardcoded to 3 genres only | 1782-1785 |

### D. stage4_context_packets.py (5 findings)

| ID | Severity | Category | Summary | Line |
|----|----------|----------|---------|------|
| P1-5 | MEDIUM | observability | Budget exhaustion silent in CP assembly | 78-81 |
| P1-L | MEDIUM | coverage | Relationship edges filtered to blueprint NPCs only | 108-110 |
| P1-M | MEDIUM | coverage | Numeric facts filtered by full_text presence | 159-160 |
| P1-N | MEDIUM | observability | World state condensed fallback loses CP dedup | 434-449 |
| P2-B | LOW | consistency | break vs continue inconsistency in budget loops | 79, 219, 238, 250 |

---

## 10. 3-Pass Audit Record

### Pass 1. Coverage and Completeness
- All 4 primary scope files read in full
- All 6 caller sites verified
- 25 total findings classified across 4 severity levels
- Cross-referenced with fresh-run report for live evidence alignment
- PASS

### Pass 2. Claim Verification
- P0-1 (silent fallback): confirmed via code trace — debug-level logging at L562-564, early exit at L566-581
- P0-2 (NPC matching): confirmed — memorize_v20_episode stores as-is (L438), search removes spaces (L763)
- P0-3 (RRF asymmetry): confirmed — enumerate index used as "rank" at L1122, not BM25 score
- P1-1 (advisor opacity): confirmed — no logging between L1733 and fallback at L1790
- All file:line anchors verified against live workspace
- PASS

### Pass 3. Confidence and Limits
- Confidence 95% — all major retrieval paths covered, all caller sites traced
- Fresh-run-before-fix: NO — justified by silent degradation pattern
- Top 3 ROI fixes: observability logging (QW-1/QW-2), cache invalidation (QW-3), priority sort (QW-4)
- No execution SSOT created (survey-only constraint respected)
- No code changes made (survey-only constraint respected)
- PASS
