Date: 2026-03-23
Status: final
Document Type: Q6 selective retrieval R2 evidence manifest
Parent Report: `docs/2026-03-23/opus/r2-q6-selective-retrieval.md`

---

## 1. Code Fix Verification Evidence

### Fix 1: Multi-query fallback WARNING (P0-1)
- **Git diff**: `git diff 79f570f2^..79f570f2 -- modules/core/vec_memory.py`
- **Change**: Added `logging.warning("[VecMem] 멀티쿼리 전체 임베딩 실패 → 키워드 폴백 (queries=%d, ep<%d)")` at L570
- **Live source anchor**: `modules/core/vec_memory.py:570`
- **Fresh run anchor**: `projects/0_0323/logs/session_20260323_134127.log` — 11 instances of `[VecMem] 멀티쿼리 전체 임베딩 실패`
  - First: `[2026-03-23 13:47:49] queries=1, ep<1`
  - Last: `[2026-03-23 14:02:14] queries=1, ep<4`

### Fix 2: Advisor fallback WARNING (P1-1)
- **Git diff**: `git diff 79f570f2^..79f570f2 -- modules/core/stage4_context_builder.py`
- **Change**: Added `logging.warning("[Q6-T3] advisor plan 미사용 → 레거시 벡터 검색 폴백 (ep=%d)")` at L1752
- **Live source anchor**: `modules/core/stage4_context_builder.py:1752`
- **Fresh run anchor**: grep `Q6-T3` in session log returns 0 results (advisor path worked)

### Fix 3: Priority sort before cap (P1-3)
- **Git diff**: `git diff 79f570f2^..79f570f2 -- modules/core/context_advisor.py`
- **Change**: Added `slots.sort(key=lambda s: s.priority)` at L593
- **Live source anchor**: `modules/core/context_advisor.py:593`

### Fix 4: Embedding cache invalidation (P1-4)
- **Git diff**: `git diff 79f570f2^..79f570f2 -- modules/core/vec_memory.py`
- **Change**: Added `self._embed_cache.clear()` at L269 inside model mismatch branch
- **Live source anchor**: `modules/core/vec_memory.py:268-269`

---

## 2. Persisting Finding Evidence

### P0-2: NPC entity matching
- **Live source anchor**: `modules/core/vec_memory.py:765-771`
- **Code**: `REPLACE(IFNULL(entity_names, ''), ' ', '')` + `%,name.replace(' ', ''),%`
- **DB evidence**: `projects/0_0323/project_data.db` — `episode_meta` table
  - ep=1: entity_names='' (empty)
  - ep=2: entity_names='한정호' (3 bytes UTF-8, hex=ED959C ECA095 ED98B8)
  - ep=3: entity_names='' (empty)

### P0-3: RRF asymmetric scoring
- **Live source anchor (fts_rank)**: `modules/core/vec_memory.py:1125` — `for rank, (ep_num, ...) in enumerate(rows)`
- **Live source anchor (RRF formula)**: `modules/core/vec_memory.py:1138-1149`

### P1-2: Work focus substring
- **Live source anchor**: `modules/core/context_advisor.py:767-770`
- **Token overlap**: "동료" in BOTH `_WORK_FOCUS_RELATION_TOKENS` (L388) and `_WORK_FOCUS_NPC_TOKENS` (L433)

### P1-5: Budget exhaustion silent
- **Live source anchors**: `modules/core/stage4_context_packets.py:78-79, 218-219, 249-250`

### P1-6: Tier-0 insert(0)
- **Live source anchor**: `modules/core/stage4_context_builder.py:1617, 1628, 1645, 1660, 1669, 1686`
- **Actual order (last-inserted-first)**: npc_boundary → CP → canonical → fact_ledger → timeline → world_state

---

## 3. Fresh Run Evidence Summary

### Session Log
- **Path**: `projects/0_0323/logs/session_20260323_134127.log`
- **Size**: 822,310 bytes
- **Key patterns**:
  - `[VecMem] 멀티쿼리 전체 임베딩 실패`: 11 instances
  - `[Q6-T3]`: 0 instances (advisor path succeeded)
  - `advisor_path_used`: present in all STAGE3_EPISODE_SUMMARY entries (ep1-4)
  - `semantic_ctx=2605자`: constant across ep1-4
  - `path=hybrid`: 12+ Director retrieval calls, 0 hits for ep<1, 1-2 hits for ep<2+
  - `[SC-5] 1건 수집 완료`: Director vector memory collection

### DB (project_data.db)
- **Path**: `projects/0_0323/project_data.db`
- **Size**: 14,561,280 bytes
- **Tables inspected**: episode_meta, vec_metadata
- **episode_meta**: 3 rows (ep 1-3), entity_names sparse (1/3 populated)
- **vec_metadata**: embed_model=gemini-embedding-001, embed_dim=3072

### Runtime Audit
- **Path**: `projects/0_0323/logs/runtime_audit.jsonl`
- **Observation**: No retrieval-specific event types. Retrieval mode selection and fallback transitions are not captured in runtime audit — console log is the only diagnostic source for Q6.

---

## 4. Cross-Reference Map

### T9 → R2 Q6

| T9 ID | T9 Description | R2 Q6 Mapping |
|-------|---------------|---------------|
| T9-P1-1 | Thin vector memory | Cold-start confirmed, now visible via P0-1 fix |
| T9-P2-1 | NPC cap at 10 | Unchanged, not exercised |
| T9-P2-2 | Slot cap at 8 | Mitigated by P1-3 priority sort |
| T9-P2-3 | Slot overflow no warning | Still absent |
| T9-P2-4 | Cache no invalidation | Resolved by P1-4 fix |

### Generation Coherence → R2 Q6

| GC ID | GC Description | R2 Q6 Mapping |
|-------|---------------|---------------|
| RT-1 | Embedding fail → LIKE fallback | P0-1 fix (WARNING) |
| RT-2 | S4 slot cap + silent truncation | P1-3 fix (priority sort) + cap unchanged |
| RT-3 | FTS5 unicode61 Korean loss | Persists, not in fix scope |
| RT-4 | LLM enrichment threshold | Persists, not in fix scope |
| RT-5 | Cache LRU 512 | P1-4 fix (clear on model change) |

---

## 5. R1 Full Finding Status Map

| R1 ID | R1 Severity | R2 Status |
|-------|-------------|-----------|
| P0-1 | CRITICAL | **resolved** |
| P0-2 | HIGH | persists |
| P0-3 | HIGH | persists |
| P1-1 | HIGH | **resolved** |
| P1-2 | MEDIUM | persists |
| P1-3 | MEDIUM | **resolved** |
| P1-4 | HIGH | **resolved** |
| P1-5 | MEDIUM | persists |
| P1-6 | MEDIUM | persists (severity reduced — CP actually well-positioned) |
| P1-A | MEDIUM | persists (not in fix scope) |
| P1-B | MEDIUM | persists (not in fix scope) |
| P1-C | MEDIUM | persists (not in fix scope) |
| P1-D | MEDIUM | persists (not in fix scope) |
| P1-E | MEDIUM | persists (not in fix scope) |
| P1-F | MEDIUM | persists (not in fix scope) |
| P1-G | MEDIUM | persists (not in fix scope) |
| P1-H | MEDIUM | persists (not in fix scope) |
| P1-I | MEDIUM | persists (not in fix scope) |
| P1-J | MEDIUM | persists (not in fix scope) |
| P1-K | LOW | persists (not in fix scope) |
| P1-L | MEDIUM | persists (not in fix scope) |
| P1-M | MEDIUM | persists (not in fix scope) |
| P1-N | MEDIUM | persists (not in fix scope) |
| P2-A | LOW | persists (not in fix scope) |
| P2-B | LOW | persists (not in fix scope) |
