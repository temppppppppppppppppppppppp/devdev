Date: 2026-03-24
Status: final
Document Type: evidence ledger (T6 lane — Stage 3 Prompt Injection)
Parent Report: `docs/2026-03-24/opus-residual/t6-stage3-prompt-injection.md`

---

# T6. Stage 3 Prompt Injection — Evidence Ledger

## A. Prompt Injection Surface Inventory

### A1. Treatment Block Injection

**Function**: `_inject_stage3_treatment_block_context()`
**File**: `modules/core/stage3_orchestrator.py:1115-1171`

Wave 1 changes (confirmed by `[W1]` comments in code):
- L1127-1132: Only `title`, `emotional_beat`, `foreshadow` fields allowed
- L1137-1140: Only `content.context` allowed; `event_villain`/`solution` removed
- L1151-1157: Structural header guard with explicit warning

Residual: `genre_ext` at L1141-1149 passes through unfiltered.

### A2. Advisory Builder Functions

| Function | File:Line | Input Source | Temporal Scope |
|---|---|---|---|
| `_build_world_state_advisory` | `s3o:221-235` | `world_state.get_summary()` | Past-verified |
| `_build_fact_ledger_advisory` | `s3o:204-218` | `db.load_anchor("fact_ledger")` | Past-verified |
| `_build_stale_seed_advisory` | `s3o:172-201` | `db.get_active_seeds()` | 20+ episode old |
| `_build_style_guide_advisory` | `s3o:238-249` | `project` style data | Non-temporal |
| `_build_stage3_work_focus_advisory` | `s3o:323-412` | `arc_data`, `entity_registry`, `SemanticQueryBroker` | Mixed (arc query → past-verified results) |
| `_inject_stage3_timeline_advisory` | `s3o:1173-1215` | Previous arc markers | Arc-to-arc only |

### A3. Continuity Pins

**Function**: `apply_continuity_pins()`
**Call site**: `stage3_orchestrator.py:1958-1975`

Inputs:
- `previous_published_text`: previous manuscript (past-verified)
- `arc_tactical_text`: extracted via `extract_episode_tactical(arc_data, working_ep, episode_details=...)` — filtered by current episode

### A4. Constraint Prompt Injection

**Function**: `compile_to_prompt()`
**File**: `blueprint_constraint_compiler.py:119-212`

Sections injected:
- `### ARC semantic carryover` (L132-136) — arc-global, no episode filter
- `### MUST_FOCUS` (L145-154) — current episode only (CLEAN)
- `### STOP_LINE` (L157-175) — all future episodes (CLEAN, Wave 1 expanded)
- `### CONTINUITY` (L178-188) — previous episode (CLEAN)
- `### INHERITED_STATE` (L191-212) — from prev blueprint + arc_start (CLEAN)
- `### state_changes` — filtered by `_within_ep()` (CLEAN, Wave 1)

### A5. Semantic Context Assembly

**Function**: `_finalize_stage3_blueprint_semantic_bundle()`
**File**: `stage3_orchestrator.py:1217-1322`

Assembly order (prepended):
1. WorkFocus advisory
2. StaleSeeds advisory
3. FactLedger advisory
4. StyleGuide advisory
5. WorldState advisory
6. Treatment block (via `_inject_stage3_treatment_block_context`)
7. Timeline advisory (via `_inject_stage3_timeline_advisory`)

Budget enforcement: `build_context_budget_ledger()` at L1288-1294

---

## B. `genre_ext` Content Evidence

**Source**: `treatments/01_tr_투자물_골든_카나리아 테스트.json` Block 0

```json
{
  "capital_before": "0 (정리 전)",
  "capital_after": "20억 (정리 후)",
  "capital_delta": "+20억 (자산 정리)",
  "profit_loss": "해당 없음",
  "method": "자산 정리 및 법인 설립",
  "investment_type": "준비 단계",
  "deal_type": "해당 없음",
  "leverage_used": [
    "회귀 지식 (향후 18년 경제사)",
    "가족의 무관심 (레이더 밖에서 활동 가능)"
  ],
  "opponent": {
    "name": "없음 (가족은 방관)",
    "type": "해당 없음",
    "weakness_exploited": "해당 없음"
  },
  "historical_event": null,
  "time_pressure": "법인 설립에 ..."
}
```

This is arc-level (Block 0 covers eps 1-4). `capital_after: 20억` and `method: 자산 정리 및 법인 설립` describe the block outcome, not any specific episode.

**LLM I/O trace**: `projects/00_001/logs/session/llm_io.jsonl` Line 9 (first BlueprintEnsembleGenerator call)

```
genre_ext:
    capital_before: 0 (정리 전)
    capital_after: 20억 (정리 후)
    capital_delta: +20억 (자산 정리)
    profit_loss: 해당 없음
    method: 자산 정리 및 법인 설립
    investment_type: 준비 단계
    deal_type: 해당 없음
    ...
```

This content entered the LLM prompt for what appears to be the ep1 blueprint generation call.

---

## C. `semantic_carryover` Content Evidence

**Source**: `projects/00_001/logs/artifacts/stage2/arc_001/attempt_01/final_arc__balanced.json`

```json
{
  "continuity_checkpoints": [
    "20억 자본금 확보 완료",
    "가족의 감시망에서 완전히 벗어남",
    "여의도 임시 사무실 계약 및 법인 설립 완료"
  ],
  "foreshadow_anchors": [
    "저녁 뉴스에서 '유가 상승세, 이란 핵 문제 재점화' 보도",
    "아버지가 '그룹 일은 형들이 알아서 할 거다'라고 발언",
    "한시우의 '그룹 돈은 한 푼도 안 받겠다'는 선언"
  ],
  "growth_justification": "미래 18년 치의 거시경제 지식 각성 및 초기 투자 자본 20억 원 확보"
}
```

Enters via `compile_to_prompt()` at `blueprint_constraint_compiler.py:132-136` as:

```
### ARC semantic carryover
  relationship 한정호 (아버지): 독자적인 투자사 설립 및 자립 선언
  ...
  growth_justification: 미래 18년 치의 거시경제 지식 각성 및 초기 투자 자본 20억 원 확보
```

**LLM I/O confirmation**: `projects/00_001/logs/session/llm_io.jsonl` L9 contains `[Arc Semantic Carryover]` with these entries.

---

## D. Fresh Live Run Blueprint Comparison

### D1. 00_001 ep1 Blueprint (attempt 09) — OVERCONSUMPTION

**Source**: `projects/00_001/logs/artifacts/stage3/ep_0001/attempt_09/final_blueprint__emotion_focused.json`

```
ending_state.protagonist_status: "자본금 20억 확보 및 법인 설립을 완료하고 첫 투자를 목전에 둔 상태"
scene_3: "20억 원의 시드 머니를 만들기로 결정" (ep3 scope)
scene_4: "SW인베스트먼트 법인 인감도장과 20억 예치 법인 계좌 OTP를 무사히 발급" (ep4 scope)
scene_5: "이란 핵 문제 재점화 뉴스 확인" (ep4 scope)
```

EP1 blueprint absorbed ep3 (20억 현금화) and ep4 (법인 설립, OTP, WTI 준비) scope into scenes 3-5.

### D2. 00_0324 ep1 Blueprint (attempt 01) — CLEAN

**Source**: `projects/00_0324/logs/artifacts/stage3/ep_0001/attempt_01/final_blueprint__emotion_focused.json`

```
ending_state.protagonist_status: "감정을 완벽히 통제하고 가족 대면을 준비하는 상태"
scene_1: "죽음의 끝에서 들이켠 숨" — awakening
scene_2: "서늘한 각성" — determination
scene_3: "부의 지도를 그리다" — writing economic data in notebook
scene_4: "전장의 문턱" — butler's knock for dinner
```

EP1 blueprint stayed within ep1 scope. No 20억 확보, no 법인 설립, no OTP.

### D3. 00_0324 ep3 Blueprint — CLEAN

```
ending_state.protagonist_status: "독립 선언을 성공적으로 마쳤으나 회귀의 물리적 반동으로 인해..."
scene_3: "20억의 선언" — declares 20억 investment firm plan (ep3 content, correctly placed)
```

### D4. 00_0324 ep4 Blueprint — CLEAN

```
ending_state.protagonist_status: "자산 현금화 완료, 다음 투자를 위해 이동할 준비"
scene_4: "20억 4,500만 원" — cash secured (ep4 content, correctly placed)
```

---

## E. `episode_details` Context

**Source**: `projects/00_001/logs/artifacts/stage2/arc_001/attempt_01/final_arc__balanced.json`

| Episode | Detail Items | Content |
|---|---|---|
| EP 1 | 2 | "2024년 고독사 후 2006년 본가 침실에서 깨어남"; "18년 치 거시경제 데이터 복기 및 두통 극복" |
| EP 2 | 2 | "아버지 한정호의 서재로 호출됨"; "형들의 무관심 속에서 그룹 지원 거절 및 투자사 설립 선언" |
| EP 3 | 2 | "은행 PB 박성호를 만나 신탁 펀드 및 스폰서십 해지 강행"; "자산 20억 원 현금화 완료" |
| EP 4 | 2 | "여의도 낡은 오피스텔 계약 및 SW인베스트먼트 설립 완료"; "이란 핵 문제 보도 WTI 투자 준비" |

EP1 has only 2 sparse detail items — this becomes the MUST_FOCUS content. When combined with `genre_ext` (capital_after: 20억) and `semantic_carryover` (법인 설립 완료), the LLM has much louder "arc outcome" signals than "current episode" signals.

---

## F. Wave 1 SSOT Residual Risk Reference

**Source**: `docs/2026-03-24/stage2-stage3-episode-boundary-wave1-execution-ssot.md` Section 16 (Closure Note)

> Residual Risk:
> - `semantic_carryover` foreshadow anchors can still describe arc-end state abstractly; this remained outside Wave 1 by design
> - `genre_ext` still enters the treatment overview; acceptable for Wave 1, but still worth watching

Both residuals identified in this survey were already flagged in the Wave 1 closure note.
