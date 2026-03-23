Date: 2026-03-23
Document Type: evidence manifest
Terminal: T9
Parent Report: `docs/2026-03-23/opus/pre-rerun-root-cause-t9-context-retrieval.md`

---

# T9 Evidence Manifest — Context and Retrieval Support Factors

## 1. Source Files Surveyed

| File | LOC (approx) | Survey Method |
|------|-------------|---------------|
| `modules/core/context_advisor.py` | ~1,160 | Full read via Explore agent |
| `modules/core/stage4_context_builder.py` | ~2,400 | Full read via Explore agent |
| `modules/core/stage4_context_packets.py` | ~803 | Full read via Explore agent |
| `modules/core/vec_memory.py` | ~1,100 | Full read via Explore agent |
| `modules/domain/agents/chief_writer_context.py` | ~512 | Full read via Explore agent |
| `modules/domain/agents/chief_writer_context_packets.py` | ~989 | Full read via Explore agent |
| `modules/domain/agents/continuity_arc.py` | ~1,096 | Full read via Explore agent |
| `modules/validation/continuity_validator.py` | ~1,265 | Full read via Explore agent |

## 2. Configuration Verified

| Parameter | File | Value | Verified |
|-----------|------|-------|----------|
| smart_retrieval.enabled | `config/settings/validation.yaml:179` | `true` | grep confirmed |
| stage4_total_budget | `config/settings/validation.yaml:186` | 300,000 chars | grep confirmed |
| mandatory_context_max | `config/settings/validation.yaml:77` | 400,000 chars | grep confirmed |
| vector_max_results_s4 | `config/settings/validation.yaml:88` | 50 | grep confirmed |

## 3. Live Code Anchors Verified

| Claim | File:Line | Verified Pattern |
|-------|-----------|-----------------|
| Stage 4 slot cap = 8 | `context_advisor.py:365-370` | `_STAGE_QUERY_CAPS = {"stage2": 5, "stage3": 6, "stage4": 8, "director": 5}` |
| NPC section cap = 10 | `stage4_context_packets.py:39` | `npc_names[:10]` |
| NPC blueprint cap = 10 | `stage4_context_packets.py:91` | `npc_names[:10]` |
| prev_ending = tail 2500 | `chief_writer_context_packets.py:59` | `prev_manuscript[-2500:]` |
| Emergency protected ratio = 0.68 | `stage4_context_builder.py:1214` | `ratio=0.68` |
| Protected ratio = 0.88 | `stage4_context_builder.py:1206` | `ratio=0.88` |
| Regular ratio = 0.7 | `stage4_context_builder.py:1204` | `ratio=0.7` |
| growth_keywords restored | `continuity_validator.py:1009-1016` | `("성장", "변화", "깨달", "반성", "후회", "각성", "결심", "다짐")` |
| LIKE fallback exists | `vec_memory.py:503,575,704,924,1040` | `_keyword_fallback_search()` 5 call sites |
| WorldState not imported by continuity_validator | `continuity_validator.py` | 0 references to world_state or WorldState |
| FactLedger not imported by continuity_arc | `continuity_arc.py` | 0 references to fact_ledger or FactLedger |

## 4. Console Evidence Anchors

| Episode | Line Range | Key Observation |
|---------|-----------|-----------------|
| Ep1 | 481-569 | Round 1 PASS (score 98), `[SC-5] Director 벡터 메모리 수집` (not shown = pre-ep1, no prior data) |
| Ep2 | 571-658 | Round 1 PASS (score 98), `[SC-5] 1건 수집 완료`, NpcDrift advisory for 박 여사 |
| Ep3 R1 | 661-746 | REJECT (score 80), `[SC-5] 1건 수집 완료`, scene 0/5, pressure not detected, NPC drift 한정호 |
| Ep3 R2 | 747-753 | Total generation failure: `🚨 [V66.3] 모든 후보 생성 실패` (patch mode) |
| Ep3 R3 | 754-831 | REJECT (score 76), `[SC-5] 1건 수집 완료`, same scene/pressure/NPC pattern |
| Ep3 R4 | 832-913 | Director PASS (score 98) then post-select REJECT: timeline conflict 1/17 vs 1/18 |
| Ep3 R5 | 914-989 | PASS (score 98), timeline fixed, post-select PASS |

## 5. Artifact Inventory

| Path | Contents |
|------|----------|
| `projects/0_0323/logs/artifacts/stage4/ep_0001/` | 1 attempt directory |
| `projects/0_0323/logs/artifacts/stage4/ep_0002/` | 1 attempt directory |
| `projects/0_0323/logs/artifacts/stage4/ep_0003/` | 4 attempt directories (attempt_01, attempt_03, attempt_04, attempt_05) |
| `projects/0_0323/drafts/` | ep_0001.txt, ep_0002.txt, ep_0003.txt |

Note: attempt_02 directory absent, consistent with Round 2 total generation failure.

## 6. Cross-Reference Sources

| Document | Relevance to T9 |
|----------|-----------------|
| `q6-selective-retrieval-deep-dive.md` | RT-1 (LIKE fallback), RT-2 (slot cap), confirmed in live code |
| `q7-context-reception-deep-dive.md` | RX-1 (Tier2 drop), RX-2 (work focus trim), confirmed structurally |
| `generation-coherence-deep-dive-report.md` | CO-1/CO-2 (non-atomic save), CO-3 (no reverse write), RT-1 (embed fallback) |
| `director-pipeline-7axis-deep-dive.md` | Director context reception map (Section 5) — no T9 contradictions |
| `q1-q8-current-state-merge-audit.md` | Q6 ranked 3rd for pre-rerun fix (retrieval observability) |
| `fresh-run-3pass-audit-report.md` | P2-1 NPC encyclopedia DEGRADED — environment difference, not T9 scope |

## 7. DB Tables Referenced (Not Directly Queried)

| Table | Relevance |
|-------|-----------|
| `vec_episodes` | sqlite-vec KNN store, hybrid retrieval source |
| `episode_meta` | FTS5 backing, metadata for sparse search |
| `episode_fts` | FTS5 virtual table for sparse retrieval |
| `sync_status` | Episode vector sync tracking |
| `vec_metadata` | Embedding model version tracking |
