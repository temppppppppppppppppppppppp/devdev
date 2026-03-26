# Stage 4 ChiefWriter State-Injection Path Audit

Date: 2026-03-25
Type: static survey (compact, single-path)
Scope: Stage 4 ChiefWriter context injection — resource balance, completed events, time/place continuity, operating principles
Mode: survey-only, no code changes
Confidence: 98%

## Evidence Surfaces Inspected

| Surface | Path |
|---------|------|
| IFC builder | `modules/core/stage4_immutable_fact_contract.py` L108-218, L481-549 |
| CW context assembler | `modules/domain/agents/chief_writer_context.py` L114-272, L525-549 |
| CW prompt template | `modules/domain/agents/chief_writer_prompts.py` L50-200 |
| CW context packets | `modules/domain/agents/chief_writer_context_packets.py` |
| Stage4 context builder | `modules/core/stage4_context_builder.py` L1369-1404, L2129-2158 |
| Fact ledger summary | `modules/core/fact_ledger.py` L605-753 |
| World state summary | `modules/core/world_state.py` L840-880, L1056-1082 |
| Live DB state | `projects/00_0000001/project_data.db` anchors table |
| Console evidence | `docs/2026-03-25/console.txt` L1654-2544 |
| Production log | `projects/00_0000001/logs/episode_production.jsonl` L19-32 |
| EP4 artifacts | `projects/00_0000001/logs/artifacts/stage4/ep_0004/attempt_01-06/` |
| EP5 artifacts | `projects/00_0000001/logs/artifacts/stage4/ep_0005/attempt_01/` |

## Architecture Summary

ChiefWriter receives state through a multi-layer injection chain:

```
Stage4Orchestrator
  → Stage4ContextBuilder._build_episode_state()
    → _RoundContext (chain_link_section, world_state_summary)
      → Stage4InterviewRound
        → ChiefWriter.generate_ensemble()
          → ChiefWriterContextBuilder.build_common_context()
            → _build_immutable_fact_section()
              → stage4_immutable_fact_contract.build_packet()
                → _extract_committed_state_facts()
                → _extract_completed_event_facts()
              → render_packet_for_cw()
            → build_chief_writer_main_prompt()
```

The IFC (Immutable Fact Contract) is the designated high-authority injection layer for prior-episode state, with ⛔ markers that signal "instant REJECT if violated."

## Findings

### F1. CRITICAL — Fact Ledger Data Never Reaches IFC Builder

**File:** `chief_writer_context.py` L542
```python
packet = build_packet(
    ...
    world_state_summary=world_state_summary,
    fact_ledger_summary=world_state_summary,  # ← WRONG: passes world_state AGAIN
    ...
)
```

The `fact_ledger_summary` parameter of `build_packet()` receives **world_state_summary** instead of `fact_ledger.to_summary()`. The comment reads "world_state carries fact-ledger-grade state facts" — but this is false for this project.

**Actual fact_ledger DB state** (pre-EP4):
```json
"numbers": {
  "capital": {
    "value": 2000000000.0,
    "unit": "won",
    "established_value": 2000000000.0,
    "last_ep": 3
  }
}
```

This tracks the exact resource balance (20억 원) that EP4 consistently violated. But this data **never reaches the IFC builder**.

### F2. CRITICAL — World State Protagonist Fields Are Empty

**Actual world_state DB state:**
```json
"protagonist": {
  "name": "",
  "location": "",
  "assets": "",
  "injuries": "정상",
  "skills": []
}
```

All protagonist fields (name, location, assets) are empty strings. The world_state summary renders nothing for protagonist section. Even if the fact_ledger_summary substitution at L542 were correct (using world_state instead of fact_ledger), the world state has **no financial data** to extract.

### F3. SECONDARY — IFC Extraction Uses Korean Keywords Against English Data

**File:** `stage4_immutable_fact_contract.py` L161-185

```python
# Extraction from fact_ledger_summary:
if line.startswith("-") and any(
    kw in line for kw in ("억", "만원", "원", "달러", "$", "계좌", "자본", "잔고", "자산")
):
```

The fact_ledger renders numbers as:
```
  - capital: 2000000000.0 won (ep3 기준)
```

The Korean keywords ("억", "원", "자본") do not match English text ("capital", "won", "2000000000.0"). Even if F1 were fixed and fact_ledger data reached this function, the extraction would still return zero matches for this project.

### F4. SECONDARY — Completed Event Extraction Vocabulary Skews Wuxia

**File:** `stage4_immutable_fact_contract.py` L188-218

Extraction keywords: `완료, 달성, 처단, 사망, 획득, 습득, 돌파, 성공, 해결, 종결`

These keywords are tuned for wuxia/action genres (처단=execution, 돌파=breakthrough, 습득=martial art acquisition). Investment-fiction completed events ("계좌 개설", "법인 설립", "HTS 구축") use different vocabulary and would require: `개설, 설립, 구축, 이체, 체결, 계약`.

**chain_link_3 evidence:** Pending actions contain "60억 원 규모(3배 레버리지)의 WTI 원유 선물 매수 포지션 진입" — no completion keywords → not extracted as completed_event_fact.

### F5. CONFIRMED WORKING — Time/Place Injection Via Opening Anchor + Chain Link

**Opening anchor** (from blueprint): Correctly injects `start_location` and `start_time_flow` with "⛔ 위 장소/시간을 변경하면 즉시 불합격" enforcement.

**chain_link_3** correctly stores:
```
- 현재 위치: 증권사 인근 고급 라운지 카페의 조용한 구석 테이블
- 작중 시간: 2006년 2월 평일 오후
```

Both injected into CW prompt. Despite this, ChiefWriter wrote "증권사 VIP 라운지" for 5/6 rounds, suggesting LLM compliance failure even with ⛔-marked constraints. This is a separate problem from the state injection gap.

### F6. CONFIRMED WORKING — Retry Does Not Degrade State Contract

IFC packet is re-derived per attempt from the same source inputs (blueprint, world_state, chain_link, prev_digest). Source data is loaded once per episode from DB anchors and does not change between retry rounds. The packet is not persisted or cached.

**However:** Since committed_state_facts and completed_event_facts are empty from round 1, there is nothing to preserve or degrade. The "⛔ Committed State" section never appears in any round.

### F7. Post-Select Correctly Catches Prompt-Injection Miss

Post-select continuity/history checks use separate LLM calls that read prior manuscripts directly. They are NOT constrained by the same IFC extraction filter. This is why post-select correctly identifies:
- "자금 상태 충돌" (resource balance contradiction)
- "타임라인 오류" (time continuity violation)
- "계좌 개설 완료 상태 무시" (completed event regression)

Post-select is **masking F1-F4**, not a standalone detection success. It catches what the prompt should have prevented.

## State Injection Classification

### Clearly Injected (Working)
| Fact Type | Source | Authority | Prompt Section |
|-----------|--------|-----------|----------------|
| Start location | Blueprint → IFC opening_anchor | ⛔ HIGH | `#### 1. 시작 계약` |
| Start time_flow | Blueprint → IFC opening_anchor | ⛔ HIGH | `#### 1. 시작 계약` |
| Prior episode ending bridge | prev_manuscript[-500:] | MEDIUM | IFC opening anchor |
| Scene obligations | Blueprint scene_breakdown | ⛔ HIGH | `#### 4. 씬별 의무` |
| Chain link place | chain_link DB anchor | MEDIUM | `[V68] 직전 화 연결고리` |
| Chain link time | chain_link DB anchor | MEDIUM | `[V68] 직전 화 연결고리` |
| Chain link pending actions | chain_link DB anchor | MEDIUM | `[V68] 직전 화 연결고리` |
| Prior manuscripts (30ep) | DB manuscripts table | HIGH | `[V67]` section |
| Dead NPCs list | state_tracker | ⛔ HIGH | past_guard_section |

### Missing From Prompt
| Fact Type | Root Cause | Impact |
|-----------|-----------|--------|
| **Resource balance** (e.g., 20억 원 전액 선물계좌 이체) | F1+F2+F3: fact_ledger never reaches IFC; world_state protagonist.assets empty; keyword language gap | EP4 R1-R5 all violated resource state; 6-round retry loop |
| **Completed events** (e.g., 계좌 개설 완료, HTS 구축 완료) | F4: extraction keywords tuned for wuxia, not investment fiction | EP5 R1 regressed "계좌 개설 완료" to "서류 미완" |

### Present But Too Low Authority
| Fact Type | Current Authority | Gap |
|-----------|------------------|-----|
| Operating principles (e.g., 3배 레버리지 원칙) | Embedded in chain_link prose (MEDIUM) | No ⛔ enforcement; not extracted as committed_state_fact |
| Chain link location/time | `반드시 이어받을 것` (MEDIUM) | Duplicated by opening_anchor (⛔), but chain_link alone lacks ⛔ marker |

## Causal Chain (EP4 Failure)

```
1. Stage4Orchestrator loads world_state and chain_link from DB ✓
2. _build_immutable_fact_section() substitutes fact_ledger with world_state (L542) ✗
3. world_state protagonist.assets = "" → no financial data available ✗
4. _extract_committed_state_facts() finds zero matches → empty list ✗
5. render_packet_for_cw() skips "#### 2. Committed State" section entirely ✗
6. ChiefWriter prompt has NO ⛔-enforced resource balance constraint ✗
7. ChiefWriter generates prose with "20억 원 실탄" cash usage ✗
8. Director scores 90-96 (high quality prose, doesn't catch financial contradiction)
9. Post-select catches "자금 상태 충돌" → REJECT downgrade ✓
10. Feedback accumulated but ChiefWriter still has no committed_state_facts → loop
```

## Single Recommendation

**Open one execution SSOT** to fix the fact_ledger → IFC committed_state_facts injection path.

Scope:
1. Pass actual `fact_ledger.to_summary()` to IFC builder instead of world_state substitute (L542 fix)
2. Add English financial keywords to extraction filter (L172-174): `"capital"`, `"won"`, `"balance"`, `"account"`, `"fund"`
3. Add investment-fiction completion keywords to event extraction (L201-214): `"개설"`, `"설립"`, `"구축"`, `"이체"`, `"체결"`, `"계약"`
4. One canary test: verify committed_state_facts is non-empty for this project after fix

Out of scope (separate investigation):
- ChiefWriter LLM compliance failure for ⛔-marked opening anchor (F5 observation)
- World state protagonist field population emptiness
- Post-select → retry feedback effectiveness

---

- **Dominant Stage 4 state-injection failure: fact-ledger-severed** (fact_ledger data substituted by empty world_state at L542; extraction keywords language-gapped)
- **Best next single move: one execution SSOT** (3-item fix: L542 wiring + keyword bilingual + genre vocabulary)
- **Should Codex open an execution SSOT now: yes**
