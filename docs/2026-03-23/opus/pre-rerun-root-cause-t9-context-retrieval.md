Date: 2026-03-23
Status: final
Document Type: pre-rerun root-cause deep survey report
Terminal: T9
Focus: Context and retrieval support factors
Canonical Path: `docs/2026-03-23/opus/pre-rerun-root-cause-t9-context-retrieval.md`
Evidence Path: `docs/2026-03-23/opus/pre-rerun-root-cause-t9-context-retrieval-evidence.md`
Source Order: `docs/2026-03-23/opus-pre-rerun-root-cause-deep-survey-order.md`

Commit State:
- Baseline Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
- Baseline Dirty Summary: `dirty workspace allowed; touched surfaces include modules/core/stage3_orchestrator.py, modules/domain/agents/director_ensemble.py, tests/test_stage3_orchestrator.py, tests/test_director_modules.py, docs/temp/queue-state.json`

---

# T9: Context and Retrieval Support Factors — Pre-Rerun Root-Cause Deep Survey

## 1. Executive Summary

The context and retrieval subsystem is **structurally sound** for the current run's scope (3 episodes, 1 arc) but contains **5 root-cause-relevant findings** and **3 symptom-level observations** that affect the Arc 1 Episode 3 divergence.

**Primary blocker**: Not the context/retrieval layer itself. The Ep3 repeated REJECT cycle (5 rounds, 30+ minutes) was driven by (a) scene structure mismatch between blueprint and manuscript format and (b) a timeline date error (1/17 vs 1/18). Neither failure originated from missing or degraded retrieval context.

**However**, the context/retrieval layer contributed to the Ep3 difficulty in two ways:

1. **Thin vector memory at early episodes**: `[SC-5] 1건 수집 완료` — with only 1-2 prior episodes, the hybrid retrieval system returns minimal context, leaving the ChiefWriter with less grounding than later episodes would enjoy.
2. **Continuity pressure signal not reaching writer**: All Ep3 candidates across all rounds showed `직전 화의 지속 압박/위협이 opening 초반에서 감지되지 않음`, indicating the pressure vectors from Ep2's ending were either not injected prominently enough or were ignored by the LLM.

**Fresh-run-before-fix allowed: yes** — No context/retrieval issue blocks the next rerun. All findings are either observability improvements or structural improvements whose absence causes graceful degradation, not crashes.

---

## 2. Current Ownership / Flow Map

### 2.1 Context Assembly Pipeline

```
ContextAdvisor.plan_stage4_retrieval()     → RetrievalPlan (max 8 slots)
  ↓
Stage4ContextBuilder._execute_retrieval_plan()
  ├─ STATIC slots → direct text injection
  ├─ DB_NPC_HISTORY → VecMemory.retrieve_npc_context()
  ├─ DB_NPC_RELATIONSHIP → db.get_relationship_history()
  ├─ manuscript_db → _fetch_manuscript_excerpt()
  └─ VEC_MEMORY → VecMemory.retrieve_hybrid_context()
  ↓
Stage4ContextBuilder._compose_tiered_mandatory_context_with_headroom()
  ├─ Tier 0: mandatory context + world state + fact ledger + continuity packet
  ├─ Tier 1: retrieval results + work focus + relation slice (protected ratio 0.88)
  └─ Tier 2: digest + pacing + advisory (regular ratio 0.7)
  ↓
ChiefWriterContextBuilder.build_common_context()
  ├─ prev_ending: prev_manuscript[-2500:]
  ├─ prev_digest: Python-only episode digest
  ├─ future_guard_section: inventory/martial/dead NPC constraints
  ├─ past_guard_section: resurrection/recovery blocks
  ├─ HUD sections: trend + anomaly + high-density
  └─ DNA instruction: ep1 special vs continuation mode
  ↓
Final prompt assembly → ChiefWriter LLM call
```

### 2.2 Continuity Validation Pipeline

```
ContinuityValidator.validate()
  ├─ Python-only checks (item, weapon, injury, location, time)
  ├─ Personality proximity (growth_keywords downgrade)
  └─ Input: current manuscript + prev_hud (no WorldState/FactLedger cross-check)

ContinuityArcValidator.inspect_arc()
  ├─ Python advisory phase (inventory, injury, item timeline)
  ├─ joint_docs auto-correction (LLM)
  ├─ LLM validation (5-step chain-of-thought)
  └─ Input: current_arc + prev_arcs (no WorldState/FactLedger cross-check)
```

### 2.3 File Ownership

| File | Owner | Role |
|------|-------|------|
| `context_advisor.py` | ContextAdvisor | Retrieval plan builder (heuristic + optional LLM) |
| `stage4_context_builder.py` | Stage4ContextBuilder | Tier assembly, budget management, retrieval execution |
| `stage4_context_packets.py` | Stage4ContextPackets | Continuity packet, world state/fact ledger condensation |
| `vec_memory.py` | VecMemory | Hybrid vector/FTS5 retrieval, embedding cache |
| `chief_writer_context.py` | ChiefWriterContextBuilder | Writer-side context assembly facade |
| `chief_writer_context_packets.py` | ChiefWriterContextPackets | prev_ending, guards, HUD, DNA packets |
| `continuity_arc.py` | ContinuityArcValidator | Arc-level LLM continuity check |
| `continuity_validator.py` | ContinuityValidator | Episode-level Python-only continuity check |

---

## 3. Focus-Scope Findings

### P0 — None

No P0 (crash/data-loss) findings in the context/retrieval layer for this run.

### P1 — 3 Findings

#### P1-1. Thin Vector Memory at Early Episodes

- **File**: `vec_memory.py`, `stage4_context_builder.py`
- **Evidence type**: console
- **Console anchor**: Lines 499, 679-680, 849-850, 928-929 — `[SC-5] 1건 수집 완료` across all Ep3 rounds
- **Description**: With only 1-2 prior episodes in the vector store, hybrid retrieval yields 1 result per query. The system operates as designed (no crash, no error), but the ChiefWriter receives thin grounding context for early-arc episodes. This is an inherent cold-start limitation, not a bug.
- **Root-cause relevance**: **Symptom, not root cause.** The Ep3 rejections were about scene structure and timeline errors, not context gaps. However, thin retrieval exacerbates the difficulty of generating contextually grounded manuscripts in early episodes.
- **Fix type**: `comment-only`
- **Blocks rerun**: No

#### P1-2. Continuity Pressure Vectors Not Reaching Writer Output

- **File**: `chief_writer_context_packets.py:59`, `stage4_context_builder.py` (tier0 injection)
- **Evidence type**: console
- **Console anchor**: Lines 690, 777, 858, 937 — `[V66.1] 연속성 경고: 직전 화의 지속 압박/위협이 opening 초반에서 감지되지 않음`
- **Description**: The pressure vectors from Ep2's ending are stored in the Episode Bible and injected into context. Yet all Ep3 candidates across 5 rounds fail to reference them in their opening. The `prev_ending` is injected as the tail 2500 chars of the previous manuscript, but pressure vectors stored in the Episode Bible metadata (`지속 압박/위협`) may not appear in this tail slice. They are separately available via the world state and continuity packet, but the LLM consistently ignores them.
- **Root-cause relevance**: **Contributing factor, not root cause.** The REJECT was for scene structure, not pressure continuity. But pressure vector non-reception adds friction to generation quality.
- **Fix type**: `observability-only` (log which pressure vectors were injected and whether they appeared in the manuscript opening)
- **Blocks rerun**: No

#### P1-3. WorldState / FactLedger Not Cross-Checked by Continuity Validators

- **File**: `continuity_validator.py`, `continuity_arc.py`
- **Evidence type**: source
- **Source anchor**: Both files contain zero references to `world_state.py` or `fact_ledger.py`
- **Description**: Neither the episode-level `ContinuityValidator` nor the arc-level `ContinuityArcValidator` consults WorldState or FactLedger. The episode validator checks `prev_hud` only. The arc validator checks `joint_docs` and `status_shadow` only. If WorldState records a state (e.g., NPC death, location change) that diverges from the HUD or joint_docs, the validators will not catch the inconsistency.
- **Root-cause relevance**: **Structural gap, not exercised in this run.** The 3-episode run did not trigger WorldState/FactLedger divergence. But for longer runs (50+ episodes), this gap becomes a latent data integrity risk.
- **Fix type**: `boundary-refactor` (long-term)
- **Blocks rerun**: No

### P2 — 5 Findings

#### P2-1. NPC Section Cap at 10 Names

- **File**: `stage4_context_packets.py:39,91,204`
- **Evidence type**: source
- **Description**: Hardcoded `npc_names[:10]` caps the continuity packet to 10 NPCs. For the current run (5-8 NPCs per episode), this is adequate. For complex arcs with 15+ NPCs, the 11th-onward NPCs lose continuity context.
- **Root-cause relevance**: Not exercised. No impact on Ep3.
- **Fix type**: `contract-cleanup` (configurable cap)
- **Blocks rerun**: No

#### P2-2. Stage 4 Slot Cap at 8

- **File**: `context_advisor.py:365-370`
- **Evidence type**: source
- **Description**: `_STAGE_QUERY_CAPS["stage4"] = 8`. With work focus (3+2+2=7 slots) + NPC + plots + relationships, complex episodes may saturate the cap. Excess slots are silently dropped with no coverage warning.
- **Root-cause relevance**: Not exercised. Early episodes have fewer retrieval demands.
- **Fix type**: `contract-cleanup` (raise to 10-12 or make configurable)
- **Blocks rerun**: No

#### P2-3. Coverage Warning for Slot Overflow Not Emitted by ContextAdvisor

- **File**: `context_advisor.py:1157-1158`
- **Evidence type**: source
- **Description**: When `len(slots) > stage_cap`, the advisor silently truncates to `slots[:stage_cap]` after priority sorting. No coverage_warning is emitted to the downstream ledger. The Stage4ContextBuilder's coverage warning system only tracks post-retrieval gaps (missing sections), not pre-retrieval slot drops.
- **Root-cause relevance**: Not exercised in this run. Becomes a diagnostic blind spot for complex episodes.
- **Fix type**: `observability-only`
- **Blocks rerun**: No

#### P2-4. Embedding Cache LRU 512 — No Model-Change Invalidation Signal to Callers

- **File**: `vec_memory.py`
- **Evidence type**: source
- **Description**: The `_check_embedding_version()` method clears the embedding cache on model mismatch and logs a WARNING. However, the caller (Stage4ContextBuilder) receives no signal that a cache reset occurred. If a model change happens mid-run, the first few queries after reset may return stale LIKE-fallback results until the cache warms up.
- **Root-cause relevance**: Not exercised. No model change during this run.
- **Fix type**: `observability-only`
- **Blocks rerun**: No

#### P2-5. Round 2 Total Generation Failure (Context Contribution)

- **File**: `chief_writer_context.py`, `stage4_context_builder.py`
- **Evidence type**: console
- **Console anchor**: Line 752 — `🚨 [V66.3] 모든 후보 생성 실패 — 다음 면담으로 진행`
- **Description**: Ep3 Round 2 entered patch mode (`score=80, 원본 보존 수정`) and all 3 candidates failed generation entirely. The patch mode constrains the writer to preserve the original manuscript while fixing specific issues. If the original + feedback + patch constraints are too complex for the context window, generation can fail. The context layer is not the primary cause (that's the patch mode logic), but context size contributes to feasibility of in-context patching.
- **Root-cause relevance**: **Downstream symptom.** Root cause is in Stage 4 retry/patch logic (T5 scope), not context assembly.
- **Fix type**: `ignore` (for T9 scope)
- **Blocks rerun**: No

---

## 4. Root-Cause Relevance

### What caused the Ep3 REJECT cycle?

| Factor | Root cause or symptom? | Evidence |
|--------|----------------------|----------|
| Blueprint scene structure not matching manuscript format | **Root cause** (T5/T10 scope) | Director REJECT reason: "5개의 씬 구분이 원고에 전혀 반영되지 않음" across Rounds 1,3 |
| Timeline date error (1/17 vs 1/18) | **Root cause** (context handoff) | Post-select check in Round 4: "제3화의 시작 시점이 제2화에서 설정된 시간 흐름과 명백하게 충돌" |
| Thin vector memory (1 result) | **Symptom** (expected cold-start) | `[SC-5] 1건 수집 완료` consistent across all rounds |
| Pressure vector not in opening | **Symptom** (LLM behavioral) | `[V66.1] 직전 화의 지속 압박/위협이 opening 초반에서 감지되지 않음` all rounds |
| NPC role drift (한정호) | **Symptom** (LLM behavioral) | NpcDrift advisory in all rounds, not changed by context fixes |
| Round 2 total generation failure | **Symptom** (patch mode) | `[V66.3] 모든 후보 생성 실패` |

**Conclusion**: The context/retrieval layer is **not the root cause** of the Ep3 divergence. The root causes are (1) scene structure format mismatch (blueprint expects explicit scene markers that the writer LLM doesn't produce) and (2) temporal continuity handoff weakness. Both are generation/feedback issues, not retrieval issues.

The context layer amplifies difficulty through thin early-episode retrieval and imperfect pressure vector surfacing, but these are not blocking failures.

---

## 5. Quick Wins

| # | Target | Fix Type | Description | ROI |
|---|--------|----------|-------------|-----|
| QW-1 | `context_advisor.py:1157` | observability-only | Emit coverage_warning when slot count exceeds stage cap before truncation | HIGH — diagnostic visibility for complex episodes |
| QW-2 | `stage4_context_builder.py` (retrieval execution) | observability-only | Log empty-result slots in `_execute_retrieval_plan()` instead of silently continuing | MEDIUM — early retrieval degradation detection |
| QW-3 | `vec_memory.py:500-508` | observability-only | Emit explicit coverage_warning when LIKE fallback is used instead of vector search | MEDIUM — makes semantic degradation visible |

---

## 6. False Leads / Non-Causes

### 6.1 "Retrieval returned only 1 result" — Not a bug

The `[SC-5] 1건 수집 완료` pattern is expected for Episode 3 (only 2 prior episodes in the vector store). The system correctly returns whatever is available. This is cold-start behavior, not degradation.

### 6.2 "NPC cap at 10 caused Ep3 failure" — Not exercised

The Ep3 run had ~5 NPCs (한시우, 한정호, 박 여사, 김 실장, 한태민). The cap of 10 was never hit.

### 6.3 "WorldState/FactLedger gap caused timeline error" — Not the mechanism

The timeline date error (1/17 vs 1/18) was a generation error by the ChiefWriter, caught by the post-select continuity check. The check that caught it uses `prev_manuscripts` comparison (LLM-based), not WorldState. The WorldState gap is real but was not the mechanism that caused or missed this particular error.

### 6.4 "Emergency trim ratio 0.68 caused context loss" — Not exercised

The 3-episode run with 300K budget and minimal retrieval results would not have triggered the emergency trim path. Budget pressure is a long-run concern.

### 6.5 "growth_keywords mojibake" — Already fixed

Live code at `continuity_validator.py:1009-1016` shows properly restored Korean keywords. This claim from Q5 is stale.

---

## 7. Fresh-Run Relevance

**Fresh-run-before-fix allowed: yes**

Rationale:
- No context/retrieval finding blocks the next rerun
- All context/retrieval issues cause graceful degradation, not crashes
- The cold-start thin retrieval is inherent and will repeat regardless of fixes
- Observability improvements are valuable but not rerun-blocking
- The root causes (scene structure, timeline handoff) are in the generation/feedback layer, not context/retrieval

**Top 3 highest-ROI fixes before the next rerun** (from T9 scope):

1. **QW-1**: Emit slot-overflow coverage_warning in ContextAdvisor — enables post-run diagnosis of complex-episode retrieval gaps
2. **QW-2**: Log empty-result retrieval slots — enables cold-start impact measurement
3. **QW-3**: LIKE-fallback coverage_warning — makes semantic degradation visible in audit logs

These are all observability-only and would improve post-run diagnosis without requiring code logic changes.

---

## 8. Confidence And Limits

**Estimated confidence: 96%**

**Basis**:
- All 8 primary scope files fully surveyed via deep exploration agents
- Key constants and thresholds verified against live code (smart_retrieval enabled, slot cap 8, NPC cap 10, prev_ending 2500, budget 300K/400K, emergency ratio 0.68, growth_keywords restored)
- Console evidence for Arc 1 Episodes 1-3 fully traced (lines 1-997)
- Runtime artifact directories confirmed (ep_0001, ep_0002, ep_0003 with 4 attempt directories for ep_0003)
- Cross-referenced against Q1-Q8 merge audit, Director 7-axis deep dive, Generation/Coherence deep dive, and Fresh Run 3pass audit

**Residual limits**:
- Runtime audit JSONL not directly inspected (console evidence was sufficient for the 3-episode scope)
- DB rows for retrieval slot execution not queried (would require sqlite3 on project_data.db)
- Actual token counts of context payloads not measured (would require live instrumentation)
- Long-run scenarios (50+ episodes) could not be validated from this 3-episode evidence base

---

## 3-Pass Audit Record

### Pass 1. Structure and Scope
- Confirmed 8 primary scope files read
- Mapped ownership, flow, and handoff boundaries
- Identified 3 P1 and 5 P2 candidates

### Pass 2. Evidence Reconciliation
- Verified all findings against live code (6 grep confirmations)
- Verified console evidence lines for Ep3 REJECT cycle
- Reconciled against prior Q6 and Q7 reports — no contradictions, 1 stale claim confirmed (growth_keywords)

### Pass 3. Root-Cause Classification
- Separated root causes (scene structure, timeline) from symptoms (thin retrieval, pressure non-reception)
- Classified 5 false leads with evidence
- Confirmed fresh-run-before-fix: yes with rationale
