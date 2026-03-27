# Chaebol Allowance Zero Rewrite Wave 2 OPUS Context Memo

Date: 2026-03-27
Purpose: minimal handoff memo for executor-OPUS
Target: `chaebol_allowance_zero`

## 1. Current Truth

- family: `blockguide`
- mode: existing `TR + BI` pair density rewrite execution
- live pair: `_quarantine` (sole live authority, confirmed)
- density-recovery rewrite plan: **complete**
- Wave 1 (Block 7-15): **complete** (8/8 PASS)
- next unit: `TR rewrite — Wave 2 (Block 16-35)`

## 2. Canonical Live Pair Paths

- TR: `treatments/_quarantine/chaebol_allowance_zero_tr_block_070_draft.json`
- BI: `bible/_quarantine/0_bi_chaebol_allowance_zero.json` (read-only)

TR shape: raw JSON list, 70 blocks, array index 0-based.
Wave 2 target: array index 15-34 (Block 16-35, 20 blocks).

## 3. Why This Run Exists

Wave 1이 Block 7-15의 template 반복을 해소했다. Block 16-35는 **더 심각한** template 반복 상태:

- Wave 1과 동일한 solution 뼈대("기억를 떠올리며 → 순서를 다시 계산 → 한 장 표로 묶어")가 그대로 존속
- 추가로 context, event_villain, stakes, power_shift, reward, foreshadow, callback까지 전 필드가 템플릿화
- 윤석진이 거의 전 블록에 동일 archetype으로 등장
- historical_event 20블록 중 1건만 non-null (B31 COVID)
- 도메인 전환(호텔→공장→병원)이 서사적 사건인데 현재는 template 치환만으로 처리

## 4. What This Run Does

- Block 16-35의 거의 모든 content 필드를 전면 리라이트
- 18개 반복 패턴 전면 삭제
- 블록마다 독립된 operational 전술 20개 부여
- opponent roster 재편: 윤석진 최대 5블록, 신규 적대자 6명+
- historical event 최소 5건 배치
- 호텔→공장→병원 도메인 전환의 서사적 밀도 확보
- villain intelligence evolution 20블록에 걸쳐 점진적 상승

## 5. What This Run Does NOT Do

- Block 1-15 수정 금지 (Wave 1 결과 보존)
- Block 36-70 수정 금지
- BI 수정 금지
- capital 수치 변경 금지
- title / time_span 변경 금지
- 코드/시스템 수정 금지
- promotion / probe 금지

## 6. Fixed Creative Anchors

- support-system cashflow warfare (호텔 위생/정산 → 공장 급식/폐기물/세탁 → 병원 진입)
- moneyline > inheritance
- no family bailout
- B2B 일상경비 조임점이 전쟁터
- 호텔→공장→병원 도메인 전환이 이 Wave의 서사적 사건

## 7. Critical Difference from Wave 1

| Dimension | Wave 1 | Wave 2 |
| ---- | ---- | ---- |
| Blocks | 9 (B7-15) | 20 (B16-35) |
| Template depth | solution + weakness 중심 | 전 필드(context/villain/solution/reward/stakes/power_shift/foreshadow/callback) |
| Kill rules | 7개 | 18개 |
| Domain transitions | 1 (장례→호텔) | 2 (호텔→공장, 공장→병원진입) |
| Opponent fix | 균형 조정 | 대폭 재편 (윤석진 5블록 상한) |
| Historical events | 최소 2건 | 최소 5건 |
| Quality gates | 8개 | 9개 (opponent 다양성 추가) |

## 8. Main Order Doc

Read and follow:

- `docs/2026-03-27/opus-chaebol-allowance-zero-rewrite-wave2-order.md`

## 9. Expected Deliverable

- TR JSON 수정 1건: `treatments/_quarantine/chaebol_allowance_zero_tr_block_070_draft.json` (Block 16-35 only)

## 10. 3-Pass Note

- pass1: scope fixed to B16-35, capital/title/time_span locked
- pass2: 18 kill rules + 9 quality gates + opponent roster requirements
- pass3: deliverable = TR JSON only, no report

Confidence:
- 96% this memo is sufficient for executor-OPUS handoff
