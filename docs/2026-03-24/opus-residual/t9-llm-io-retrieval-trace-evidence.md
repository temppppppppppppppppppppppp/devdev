Date: 2026-03-24
Status: final
Document Type: raw evidence ledger (T9 lane)
Canonical Path: `docs/2026-03-24/opus-residual/t9-llm-io-retrieval-trace-evidence.md`

---

# T9 Evidence Ledger — LLM I/O / Retrieval Trace

## A. LLM I/O Statistics

### Old Run (00_001)
- File: `projects/00_001/logs/session/llm_io.jsonl`
- Size: 12,805,901 bytes, 368 entries
- Agent distribution:
  - Director: 185
  - ChiefWriter: 74
  - BlueprintEnsembleGenerator: 62
  - Manager: 15
  - ArcEnsembleGenerator: 12
  - StateExtractor: 10
  - PreflightChecker: 4
  - Analyst: 3
  - Weaver: 3

### Fresh Run (00_0324)
- File: `projects/00_0324/logs/session/llm_io.jsonl`
- Size: 4,321,430 bytes, 114 entries
- Agent distribution:
  - Director: 43
  - ChiefWriter: 30
  - BlueprintEnsembleGenerator: 18
  - ArcEnsembleGenerator: 6
  - Manager: 6
  - StateExtractor: 5
  - Analyst: 2
  - Weaver: 2
  - PreflightChecker: 2

## B. Contamination Marker Analysis

### Old Run EP1 Blueprint Prompts (L9-L11, ~8663c each)

Markers found in prompt:
- `법인 설립`: 3 occurrences
- `법인 인감도장`: 1 occurrence (EP4 item — contamination)
- `OTP`: 1 occurrence (EP4 item — contamination)
- `상태 변경`: 1 occurrence (section header)
- `Stop Line`: 1 occurrence (EP2-only)
- `Treatment`: 1 occurrence

Context around contamination:
```
[상태 변경 요약]
  🤝 관계변화: 한정호 기대 제로→의외라는 시선
  🤝 관계변화: 한정호 (아버지) 귀여운 막내, 기대 제로→의외라는 시선, 약간의 관심
  🤝 관계변화: 한태준 (큰형) 무관심→무관심 유지
  📦 아이템: SW인베스트먼트 법인 인감도장 (획득)    ← EP4/5 item
  📦 아이템: 20억 예치 법인 계좌 OTP (획득)        ← EP4 item
```

### Fresh Run EP1 Blueprint Prompts (L9-L11, ~7452c each)

Markers found in prompt:
- `20억`: 2 occurrences (in `genre_ext.capital_after` — arc-level metadata)
- `법인 설립`: 2 occurrences (in `genre_ext.method` — arc-level metadata)
- `WTI`: 3 occurrences (legitimate arc-level investment target)
- `상태 변경`: 1 occurrence (section header)
- `Stop Line`: 1 occurrence (EP2-only)
- `법인 인감도장`: 0 occurrences (CLEAN)
- `OTP`: 0 occurrences (CLEAN)
- `Treatment`: 0 occurrences (CLEAN)

Context around `state_changes`:
```
[상태 변경 요약]
  🤝 관계변화: 한정호 (아버지) 귀여운 막내, 기대 제로→의외라는 시선, 약간의 관심
  🤝 관계변화: 한태준 (큰형) 무관심→무관심 유지
  🤝 관계변화: 한태민 (둘째형) 무관심→무관심 유지
  (NO item acquisitions — filter is working)
```

Context around `[Arc 개요]`:
```
[Arc 개요 — 아크 1~5화 방향성 참조]
⚠️ 현재 화는 1화입니다. 아래는 아크 전체의 제목·감정선·복선만 제공합니다.
구체적 사건(빌런 등장, 해결책, 보상, 전력 변화)은 제거되었습니다.
현재 화의 구체적 내용은 arc_focus와 MUST_FOCUS를 기준으로 작성하세요.
  title: 회귀, 그리고 선언
  emotional_beat: {{'type': 'rebirth', 'intensity': 9}}
  foreshadow: [...]
  content.context: (narrative summary without event details)
```

## C. Stop Line Evidence

### Old Run EP1 Stop Line
```
[Stop Line]
  다음 화 내용 금지: 아버지 한정호의 서재로 호출됨; 형들의 무관심 속에서 그룹 지원을 거절하고
  독자적인 투자사 설립 선언
```
Coverage: EP2 only. EP3/EP4/EP5 unguarded.

### Fresh Run EP1 Stop Line
```
[Stop Line]
  다음 화 내용 금지: 서울 성북동 본가 저택 다이닝룸 — 가족 저녁 식사에서 형들의 암투 관찰;
  과거와 달리 묵묵히 식사만 하며 자신의 변화를 내비침
```
Coverage: EP2 only. EP3/EP4/EP5 still unguarded. Same pattern as old run.

### Fresh Run EP3 (L20) Stop Line
```
[Stop Line]
  다음 화 내용 금지: 서울 강남 PB센터 VIP룸 — 전담 PB 박성호와 대면; 모든 개인 자산 및 신탁을
  강제 해지하여 20억 원의 시드머니 현금 확보
```
Coverage: EP4 only. EP5 unguarded.

### Code Path Analysis

Constraint compiler `_extract_stop_line()` at `blueprint_constraint_compiler.py:312-373`:
- Lines 318-333: Extract next-ep content from `episode_details`
- Lines 353-366: **[W1]** Collect ALL future episodes into `future_eps` list
- Line 372: Return `{"content": next_ep_content, "future_eps": [...], ...}`

Constraint compiler `compile_to_prompt()` at `blueprint_constraint_compiler.py:119-174`:
- Line 157: Header `### 🚨 STOP_LINE (현재 화 이후 모든 사건 — 절대 침범 금지)`
- Lines 162-167: Render next-ep content
- Lines 168-169: Render ALL `future_eps`
- Lines 170-174: Blanket prohibition
- **STATUS: DEAD CODE** — 0 production callers (per T10-TF-004 and grep verification)

Blueprint ensemble `_format_constraints()` at `blueprint_ensemble.py:842-867`:
- Lines 864-867: Render ONLY `stop_line["content"]` (next-ep)
- `stop_line["future_eps"]` is NEVER accessed
- **STATUS: LIVE CODE** — called at `blueprint_ensemble.py:264`

## D. Blueprint Output Comparison

### Old Run EP1 Blueprint (00_001, attempt_09, emotion_focused)
- `ending_hook`: "한시우의 손에 들린 OTP가 차갑게 빛났다." — EP4 item consumed
- `ending_state.protagonist_status`: "자본금 20억 확보 및 법인 설립을 완료하고 첫 투자를 목전에 둔 상태" — EP4 state
- `equipment`: ["SW인베스트먼트 법인 인감도장", "20억 예치 법인 계좌 OTP"] — EP4 items
- `integrated_scenario` length: 1,063 chars — contained full arc progression through EP4

### Fresh Run EP1 Blueprint (00_0324, attempt_01, emotion_focused)
- `ending_hook`: "\"도련님, 회장님께서 찾으십니다.\" 문 너머의 목소리에 한시우의 입꼬리가 비틀렸다." — proper EP1 ending
- `ending_state.protagonist_status`: "감정을 완벽히 통제하고 가족 대면을 준비하는 상태" — proper EP1 state
- `equipment`: ["구형 애니콜 휴대폰", "암호화된 가죽 수첩"] — proper EP1 items
- `integrated_scenario` length: 1,905 chars — stays within EP1 scope

## E. Prompt Size Growth Data

| Episode | Old Run (00_001) avg chars | Fresh Run (00_0324) avg chars |
|---------|---------------------------:|------------------------------:|
| EP1     |                      8,663 |                         7,452 |
| EP2     |                      6,895 |                        10,379 |
| EP3     |                      8,665 |                        10,787 |
| EP4     |                      8,911 |                        11,499 |
| EP5     |                      9,814 |                        12,351 |
| EP6     |                          — |                        38,410 |
| EP8     |                     11,716 |                            — |
| EP11    |                     22,192 |                            — |
| EP15    |                     29,889 |                            — |
| EP17    |                     31,124 |                            — |
| EP19    |                     42,681 |                            — |

Notes:
- Fresh run EP1 is ~14% smaller than old run EP1 (quarantined content removed)
- EP6 in fresh run is Arc 2 start — jumps to 38K due to accumulated Arc 1 context
- Old run shows ~5x growth from EP1 to EP19

## F. Production Outcome Data

### Old Run (00_001) Episode Production
- EP1: PASS R0, s96
- EP2: PASS R0, s96
- EP3: PASS R0 (s95) → REJECT (s44, "20억 이체 already done in EP1") → PASS R2 (s95)
- EP4: REJECT (s30, "타임라인 역행") → PASS R2 (s96)
- EP5: REJECT (s80) → PASS R1 (s90)
- EP6: PASS R0, s96
- EP7: PASS_WITH_FIX (s93) → PASS R0 (s95)
- Total: 17 attempts for 7 episodes, 7 rejections

### Fresh Run (00_0324) Episode Production
- EP1: PASS R0, s95 (emotion_focused)
- EP2: PASS_WITH_FIX (s92) → patched → PASS (s90)
- EP3: PASS R0, s95
- Total: 3 attempts for 3 episodes, 0 rejections

## G. Context Budget / Retrieval Observations

No context budget or prompt truncation mechanism was found in the Stage 3 blueprint generation path. Specifically:
- `blueprint_ensemble.py` has no `context_budget` or `token_budget` references
- `_format_constraints()` uses `_fit_compact_context()` for individual fields (150-800 char limits per field) but has no global prompt size limit
- Prompt size grows unboundedly as episodes accumulate continuity/state data
- Stage 4 has `context_budget` references but Stage 3 does not

No retrieval contamination was observed:
- Vector memory (`VecMemory`) is used in Stage 4 for Director reference, not in Stage 3 blueprint generation
- Stage 3 uses `semantic_ctx` (fixed semantic context from constraint compiler), not dynamic retrieval
