Date: 2026-03-23
Status: final
Document Type: Q6 selective retrieval evidence manifest
Canonical Path: `docs/2026-03-23/opus/q6-selective-retrieval-evidence-manifest.md`
Parent Report: `docs/2026-03-23/opus/q6-selective-retrieval-deep-dive.md`

---

## 1. Source Files Analyzed

| File | Path | Lines | Read Method |
|------|------|-------|-------------|
| vec_memory.py | `modules/core/vec_memory.py` | ~1,370 | Full read (chunked) |
| context_advisor.py | `modules/core/context_advisor.py` | ~1,160 | Full read (chunked) |
| stage4_context_builder.py | `modules/core/stage4_context_builder.py` | ~2,730 | Full read (chunked) |
| stage4_context_packets.py | `modules/core/stage4_context_packets.py` | ~800 | Full read (chunked) |

---

## 2. Caller Site Inventory (grep-verified)

### vec_memory.py callers

| Caller File | Line(s) | Method Called | Context |
|-------------|---------|--------------|---------|
| main_a.py | 158, 1353-1358 | VecMemory() init | Shared conn mode |
| main_a.py | 1140-1143, 2708-2716 | close() | Shutdown |
| db_manager.py | 260-370 | _migrate_vec_memory_db() | 1x migration |
| stage2_preflight.py | 291 | retrieve_npc_context() | NPC history |
| stage2_preflight.py | 305-306 | retrieve_hybrid_context() | hybrid mode |
| stage2_preflight.py | 323 | retrieve_high_res_context() | dense mode |
| stage2_preflight.py | 334 | retrieve_multi_query_context() | multi-query |
| stage2_preflight.py | 1133 | retrieve_high_res_context() | episodic ctx |
| stage3_orchestrator.py | 1073-1074 | retrieve_npc_context() | DB_NPC_HISTORY |
| stage3_orchestrator.py | 1086 | retrieve_multi_query_context() | fallback |
| stage4_context_builder.py | 1023 | retrieve_npc_context() | plan execution |
| stage4_context_builder.py | 1037-1038 | retrieve_hybrid_context() | hybrid mode |
| stage4_context_builder.py | 1060 | retrieve_multi_query_context() | multi-query |
| stage4_context_builder.py | 1790 | retrieve_multi_query_context() | legacy fallback |
| stage4_director_runtime.py | 1043-1051 | retrieve_npc_context() | director NPC |
| stage4_director_runtime.py | 1076 | retrieve_multi_query_context() | director ctx |
| stage4_interview_round.py | 4729-4734 | retrieve_high_res_context() | flashback |
| stage0/reverse_expander.py | 537 | is_operational() | expansion ctx |

### context_advisor.py callers

| Caller File | Line | Method Called |
|-------------|------|--------------|
| stage2_preflight.py | 1101 | plan_stage2_retrieval() |
| stage3_orchestrator.py | 1055 | plan_stage3_retrieval() |
| stage4_context_builder.py | 1723 | plan_stage4_retrieval() |
| stage4_director_runtime.py | 919 | plan_director_retrieval() |

### stage4_context_packets.py callers

| Caller File | Line | Method Called |
|-------------|------|--------------|
| stage4_context_builder.py | 175 | __init__ |
| stage4_context_builder.py | 1608 | build_condensed_world_state_summary() |
| stage4_context_builder.py | 1636 | build_condensed_fact_ledger_summary() |
| stage4_context_builder.py | 1667 | build_continuity_packet() |
| stage4_context_builder.py | 2516 | build_tier12_auxiliary_sections() |

---

## 3. VecMemory Internal Architecture

### Public Retrieval Methods (4)

```
retrieve_high_res_context(query, current_ep, n_results=3) → str
  └─ delegates to _knn_search() or retrieve_hybrid_context() based on threshold

retrieve_multi_query_context(queries[], current_ep, n_per_query=3, max_results=5, arc_no) → str
  └─ per-query: _knn_search() → merge → fallback: _keyword_fallback_search()

retrieve_hybrid_context(query, current_ep, dense_k=10, sparse_k=10, max_results=5, rrf_k=60) → str
  └─ _knn_search_raw() + _fts_search() → RRF fusion → render

retrieve_npc_context(npc_names[], current_ep, max_results=5) → str
  └─ _collect_npc_entity_candidates() + _build_npc_vector_queries() + _select_npc_candidates()
```

### Internal Search Engines (5)

```
_knn_search(emb, current_ep, n_results) → rendered str (metadata-rich)
_knn_search_raw(emb, current_ep, n_results, arc_no) → dict (for RRF)
_fts_search(query, current_ep, n_results) → list of dicts (BM25-ranked)
_keyword_fallback_search(query, current_ep, n_results) → str (LIKE-based)
_rrf_score(dense_rank, sparse_rank, k=60) → float (reciprocal rank fusion)
```

### Database Schema

```
vec_episodes (virtual, sqlite-vec):  rowid=ep_num, embedding=float[3072]
episode_meta (regular):              ep_num PK, summary, causal_data, arc_no, event_types, entity_names
episode_fts (virtual, FTS5):         rowid=ep_num, summary, event_types, entity_names
sync_status (regular):               ep_num PK, synced, vector_synced
anchors (regular):                   key PK, data, updated_at
vec_metadata (regular):              key PK, value (embed_model, embed_dim)
```

---

## 4. Context Advisor Architecture

### Retrieval Source Types

```
RetrievalSources.VEC_MEMORY          → vector/hybrid/multi-query search
RetrievalSources.DB_NPC_HISTORY      → NPC history table (direct DB)
RetrievalSources.DB_NPC_RELATIONSHIP → relationship pairs table (direct DB)
RetrievalSources.STATIC              → query text returned as-is
RetrievalSources.MANUSCRIPT_DB       → manuscript excerpts by ep range
```

### Stage-Specific Slot Strategies

| Stage | Slot Types | Max Slots (cap) |
|-------|-----------|-----------------|
| Stage 2 | block_theme, npc_recent, plot_suspension, arc_tactical + work_focus | ~6 |
| Stage 3 | similar_blueprint, npc_history, continuity_hook, unresolved_plot, genre_context + work_focus | ~7 |
| Stage 4 | prev_ending, npc_history, arc_tactical, scene_context, plot_suspension, relationship_history, arc_semantic_carryover, genre_context, manuscript_excerpt + work_focus | ~8 |
| Director | npc_consistency, event_claim, relationship_consistency, location_item_consistency, blueprint_alignment | ~6 |

### Budget Allocation

```
Priority 1 → weight 3
Priority 2 → weight 2
Priority 3 → weight 1
Each slot.max_chars = floor(total_budget * slot_weight / sum_all_weights)
```

---

## 5. Context Packets Architecture

### Continuity Packet (Tier 0) Assembly Order

```
build_continuity_packet(entities)
  1. Header: "=== [Continuity Packet] ..."
  2. NPC sections (_build_continuity_npc_sections): top 10 NPCs
     └─ Per NPC: world_state entry + fact_ledger entry + DB history (3 rows)
  3. Relationship section (_build_continuity_relationship_section)
     └─ get_relationship_history() + get_npc_relationship_edges()
  4. Plot/item sections from entities dict
  5. Fact sections (_build_continuity_fact_sections)
     └─ numbers (if in full_text) + canonical_facts (from DB)
  Budget: 7000 chars hard limit, per-section break/continue on exhaustion
```

### Tier 1+2 Auxiliary Sections

```
build_tier12_auxiliary_sections(...)
  Tier 1:
    - work_identity_slot_summary
    - arc_rationale_digest
    - series_summary / volume_summary
  Tier 2:
    - stage2_failure_context
    - ambient NPC text
    - V68 hierarchical summaries
    - V74 treatment genre_ext constraints
    - state_tracker summaries (16 types, genre-specific variants)
    - foreshadowing block
    - arc history lookback (3 prior arcs)
```

---

## 6. Retrieval Mode Configuration

| Config Key | Default | Purpose |
|-----------|---------|---------|
| `smart_retrieval.enabled` | False | Master toggle for advisor |
| `smart_retrieval.stage2_enabled` | True | Stage 2 advisor toggle |
| `smart_retrieval.stage3_enabled` | True | Stage 3 advisor toggle |
| `smart_retrieval.stage4_enabled` | True | Stage 4 advisor toggle |
| `smart_retrieval.director_enabled` | True | Director advisor toggle |
| `smart_retrieval.retrieval_mode` | "dense" | Default retrieval method |
| `smart_retrieval.stage4_total_budget` | 300000 | Stage 4 total budget chars |
| `smart_retrieval.max_queries_per_plan` | 8 | Max slots per plan |

---

## 7. Finding-to-Line Anchor Index

| Finding ID | File | Line(s) |
|-----------|------|---------|
| P0-1 | vec_memory.py | 550-581 |
| P0-2 | vec_memory.py | 762-768 |
| P0-3 | vec_memory.py | 670-679, 1122, 1142-1145 |
| P1-1 | stage4_context_builder.py | 1708-1748 |
| P1-2 | context_advisor.py | 761-769 |
| P1-3 | context_advisor.py | 592 |
| P1-4 | vec_memory.py | 251-280 |
| P1-5 | stage4_context_packets.py | 78-81, 218-221, 238-240, 249-252 |
| P1-6 | stage4_context_builder.py | 1617-1686 |
| P1-A | vec_memory.py | 487-496 |
| P1-B | vec_memory.py | 519-526 |
| P1-C | vec_memory.py | 1037-1084 |
| P1-D | vec_memory.py | 1019, 722, 875 |
| P1-E | context_advisor.py | 618 |
| P1-F | context_advisor.py | 1026-1044 |
| P1-G | context_advisor.py | 1007-1009 |
| P1-H | stage4_context_builder.py | 1750-1787 |
| P1-I | stage4_context_builder.py | 1248-1249 |
| P1-J | stage4_context_builder.py | 1605-1620 |
| P1-K | stage4_context_builder.py | 1782-1785 |
| P1-L | stage4_context_packets.py | 108-110 |
| P1-M | stage4_context_packets.py | 159-160 |
| P1-N | stage4_context_packets.py | 434-449 |
| P2-A | context_advisor.py | 855 |
| P2-B | stage4_context_packets.py | 79, 219, 238, 250 |

---

## 8. Test File References

| Test File | Coverage |
|-----------|---------|
| tests/test_vec_memory.py | Core VecMemory unit tests |
| tests/test_npc_aware_retrieval.py | NPC-specific retrieval |
| tests/test_db_merge.py | Shared mode integration |
| tests/test_context_advisor.py | Advisor planning tests |
| tests/test_stage4_context_builder.py | Context builder integration |
| tests/test_stage4_interview_round.py | Stage 4 interview round |
| tests/test_sc6_observability.py | SC6 coverage tests |

---

## 9. Missing Test Coverage (Identified Gaps)

| Gap | Scope | Impact |
|-----|-------|--------|
| RRF fusion correctness with real data | vec_memory.py hybrid path | P0-3 untested |
| Multi-query partial failure (1 success, N-1 fail) | vec_memory.py multi-query | P0-1 untested |
| NPC entity matching with multi-token names | vec_memory.py NPC search | P0-2 untested |
| Embedding cache invalidation on model change | vec_memory.py cache | P1-4 untested |
| Advisor None → legacy fallback path | stage4_context_builder.py | P1-1 untested |
| Budget exhaustion boundary in CP | stage4_context_packets.py | P1-5 untested |
| Tier-0 section ordering verification | stage4_context_builder.py | P1-6 untested |
