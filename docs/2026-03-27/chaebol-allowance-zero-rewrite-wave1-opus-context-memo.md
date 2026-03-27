# Chaebol Allowance Zero Rewrite Wave 1 OPUS Context Memo

Date: 2026-03-27
Purpose: minimal handoff memo for OPUS
Target: `chaebol_allowance_zero`

## 1. Current Truth

- family: `blockguide`
- mode: existing `TR + BI` pair density rewrite execution
- live pair: `_quarantine` (sole live authority, confirmed)
- density-recovery rewrite plan: **complete** (verdict: mixed)
- path truth: **resolved**
- next unit: `TR rewrite — Wave 1 (Block 7-15)`

## 2. Canonical Live Pair Paths

- TR: `treatments/_quarantine/chaebol_allowance_zero_tr_block_070_draft.json`
- BI: `bible/_quarantine/0_bi_chaebol_allowance_zero.json` (read-only)

TR shape: raw JSON list, 70 blocks, array index 0-based.
Wave 1 target: array index 6-14 (Block 7-15).

## 3. Why This Run Exists

The density-recovery rewrite plan identified:

- Block 1-6: high-density benchmark band (보존)
- Block 7-70: template-heavy low-density band (rewrite 대상)
- Block 7-15: template 반복 진입점 → **첫 rewrite wave**

Specific template problems in Block 7-15:
- solution이 9블록 전부 동일 뼈대: "기억를 떠올리며 → 순서를 다시 계산 → 실물 자료를 한 장 표로 묶어"
- weakness_exploited가 9블록 전부 동일 뼈대: "[직책]로서 [제목]를 잡무나 비용으로 보고"
- historical_event가 9블록 전부 null
- "재이의 정보 출처를 의심한다" 반복

## 4. What This Run Does

- Block 7-15의 content(context/event_villain/solution/reward), stakes, power_shift, weakness_exploited를 전면 리라이트
- 블록마다 독립된 operational 전술 부여
- villain intelligence evolution 삽입
- historical event 최소 2건 배치
- 7개 반복 패턴 전면 삭제

## 5. What This Run Does NOT Do

- Block 1-6 수정 금지
- Block 16-70 수정 금지
- BI 수정 금지
- capital 수치 변경 금지
- title / time_span / foreshadow / callback 변경 금지
- 코드/시스템 수정 금지
- promotion / probe 금지

## 6. Fixed Creative Anchors

- support-system cashflow warfare (장례 세탁/청소 → 호텔 린넨/주차/미니바)
- moneyline > inheritance
- no family bailout
- B2B 일상경비 조임점이 전쟁터
- 장례→호텔 도메인 전환이 이 Wave의 서사적 사건

## 7. Main Order Doc

Read and follow:

- `docs/2026-03-27/opus-chaebol-allowance-zero-rewrite-wave1-order.md`

## 8. Expected Deliverable

- TR JSON 수정 1건: `treatments/_quarantine/chaebol_allowance_zero_tr_block_070_draft.json` (Block 7-15 only)

## 9. Suggested One-Line OPUS Prompt

```text
`docs/2026-03-27/opus-chaebol-allowance-zero-rewrite-wave1-order.md`와 `docs/2026-03-27/chaebol-allowance-zero-rewrite-wave1-opus-context-memo.md`, `docs/2026-03-27/chaebol-allowance-zero-rewrite-wave1-order-opus-brief.md`를 UTF-8로 읽고, `chaebol_allowance_zero` TR의 Block 7-15를 density rewrite하라. Wave 1 only.
```

## 10. 3-Pass Note

- pass1: target / live pair / scope / non-goals fixed
- pass2: template problems compressed to what OPUS must know to rewrite
- pass3: deliverable path and quality gate fixed to prevent scope drift

Confidence:
- 97% this memo is sufficient for low-overhead OPUS handoff
