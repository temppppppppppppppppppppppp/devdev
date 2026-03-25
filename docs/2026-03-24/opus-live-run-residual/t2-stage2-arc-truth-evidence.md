# T2 Stage2 Arc Truth — Evidence Ledger

Date: 2026-03-24
Parent: `docs/2026-03-24/opus-live-run-residual/t2-stage2-arc-truth.md`

---

## Evidence Index

| ID | Source | File | Line | Claim |
|----|--------|------|------|-------|
| AE-01 | Arc 1 | `stage2/arc_001/.../final_arc__conservative.json` | L94 | 3-출처 합산: "조부의 유산, 승마 스폰서십, 모친 명의 신탁 자산" |
| AE-02 | Arc 1 | same | L234-236 | `item_consumption`: ["조부의 현금성 유산", "승마 스폰서십", "모친 명의 신탁 자산"] |
| AE-03 | Arc 1 | same | L240 | `tactical_doc` EP3: "할아버지가 쥐여준 용돈 계좌 + 승마 스폰서십 + 어머니가 몰래 신탁해 둔 자산" |
| AE-04 | Arc 1 | same | L117 | `episode_details` EP3: "조부 유산 및 신탁 자산 해지" (축약, 신탁 소유자 미명시) |
| AE-05 | Arc 1 | same | L142 | `joint_docs.physical_inventory`: "20억 원이 찍힌 법인 통장" |
| AE-06 | Arc 1 | same | L240 | `tactical_doc` EP3 ending: "통장에는 정확히 20억 원이라는 숫자" |
| AE-07 | Arc 1 | same | L240 | `tactical_doc` EP4: "자본금 20억 원을 법인 계좌로 이체" |
| AE-08 | Arc 1 | same | L240 | `tactical_doc` EP5: "법인 계좌에 예치된 20억 원...계획을 세운다" + "마우스 위에 손을 얹은" |
| AE-09 | Arc 1 | same | L240 | `tactical_doc` EP5 소지품: "20억 원이 찍힌 법인 통장" (자금 계좌 유지) |
| AE-10 | Arc 1 | same | L96 | `beat_sequence` EP5: "WTI 원유 롱 포지션 진입 **준비 완료**" |
| AE-11 | Arc 1 | same | L238 | `key_stat_change`: "가용 자본: 0원 -> 20억 원" |
| AE-12 | Arc 2 | `stage2/arc_002/.../final_arc__balanced.json` | L241 | `arc_start_state.capital`: "20억원" |
| AE-13 | Arc 2 | same | L245 | `arc_start_state.portfolio_position`: "현금 100%" |
| AE-14 | Arc 2 | same | L246 | `arc_start_state.total_assets`: "20억원" |
| AE-15 | Arc 2 | same | L93 | `beat_sequence` EP7: "15억 원어치 3배 레버리지 매수 주문 강행" |
| AE-16 | Arc 2 | same | L113 | `episode_details` EP7: "15억 원어치 WTI 6월물 3배 레버리지 롱 포지션 진입 강행" |
| AE-17 | Arc 2 | same | L275 | `investment_calc.transactions[0].ep_no`: 7 |
| AE-18 | Arc 2 | same | L278 | `investment_calc.transactions[0].principal`: 1500000000 (15억) |
| AE-19 | Arc 2 | same | L277 | `investment_calc.transactions[0].leverage`: 3 |
| AE-20 | Arc 2 | same | L312 | `key_stat_change`: "가용 현금 20억 원 중 15억 원 증거금 구속, 예비금 5억 원" |
| AE-21 | Arc 2 | same | L227 | `arc_end_state.capital`: "5억원" |
| AE-22 | Arc 2 | same | L268 | `investment_calc.final_cash`: 500000000 (5억) |
| AE-23 | Arc 2 | same | L269 | `investment_calc.final_total_assets`: 2375000000 (23.75억) |
| AE-24 | Arc 2 | same | L314 | `tactical_doc` EP6 소지품: "20억 원이 찍힌 법인 통장" |
| AE-25 | Arc 2 | same | L314 | `tactical_doc` EP7: "3배 레버리지. WTI 6월물. 15억 넣어." |
| AE-26 | Arc 2 | same | L98 | `constraint_summary`: Arc 1 획득 아이템 재획득 금지 3건 |
| AE-27 | Stage 3 | `stage3/ep_0002/.../final_blueprint__dialogue_focused.json` | L60 | "조부 명의의 HMC투자증권 신탁 계좌 해지 목표 설정" |
| AE-28 | Stage 3 | `stage3/ep_0005/.../final_blueprint__emotion_focused.json` | L26 | `expected_ending`: "WTI 롱 포지션 매수 체결 완료" |
| AE-29 | Stage 3 | same | L27 | "약 198만 달러의 자본이 WTI 롱 포지션에 쏟아져 들어간다" |
| AE-30 | Stage 3 | same | L33 | equipment: "약 198만 달러가 예치된 파생상품 계좌" |
| AE-31 | Stage 3 | same | L74 | "19억 3천만 원을 해외 선물용 달러(약 198만 달러)로 환전" |
| AE-32 | Stage 3 | `stage3/ep_0006/.../final_blueprint__dialogue_focused.json` | L32 | equipment: "19억 3천만 원이 예치된 계좌 내역" |
| AE-33 | Stage 3 | same | L51 | "19억 3천만 원의 시드머니를 온전히 쏟아부을 3배 레버리지" |

---

## Cross-Reference Matrix

### A. Provenance Truth Chain

```
Arc 1 L94/L234-236/L240 (3-출처):
  조부 현금유산 + 승마 스폰서십 + 모친 명의 신탁
                    ↓
Arc 1 L117 (축약, 모호):
  "조부 유산 및 신탁 자산"
                    ↓
Stage 3 EP2 L60 (변환):
  "조부 명의의 HMC투자증권 신탁 계좌"
                    ↓
EP2 manuscripts rounds 1-3: REJECT (history conflict)
EP2 round 4: "어머니" 기준 정규화 → PASS
```

**변환 지점**: Arc 1 L117 → Stage 3 L60. "모친 명의 신탁"이 "조부 명의 신탁"으로 교체됨.

### B. Capital Flow Truth Chain

```
Arc 1 L142/L240 (canonical):
  20억 → 법인 통장 → 20억 유지
                    ↓
Arc 2 L241/L245 (cross-arc handoff):
  20억, 현금 100%
                    ↓
Stage 3 EP3 (수수료 도입):        Stage 3 EP5 (전액 투입):
  20억 - 3.5% = 19.3억              19.3억 → 198만$ WTI 전액
                    ↓                              ↓
Stage 3 EP6 L32/L51 (19.3억 계좌 잔존):  ← 모순 (전액 투입 후 잔존 불가)
  19.3억, 15억 투입 계획
                    ↓
Arc 2 L278/L312/L314 (arc truth):
  20억 중 15억 투입, 5억 예비금
```

**핵심 분기점**: Stage 3 EP3에서 "19.3억"이 생성된 순간부터 arc truth (20억)와 영구 괴리. Stage 3 EP5에서 "전액 투입"이 추가되면서 arc truth (15억 부분투입)와도 괴리.

### C. WTI Entry Timing Truth Chain

```
Arc 1 L96/L240 (EP5 = 준비만):
  "진입 준비 완료" + "계획을 세운다" + "마우스 위에 손" + 소지품 "20억 통장"
                    ↓
Arc 2 L93/L275 (EP7 = 실행):
  "15억 매수 주문 강행" + investment_calc.ep_no = 7
                    ↓
Stage 3 EP5 L26/L27 (EP5 = 실행):
  "매수 체결 완료" + "자본이 WTI에 쏟아져 들어간다"
```

**변환 지점**: Arc 1의 "준비 완료" ending을 Stage 3가 "매수 체결 완료"로 재해석. Arc 2 EP7에 예정된 매수 체결이 2화 앞당겨 EP5에서 발생.

---

## Arithmetic Verification

### Arc 2 Investment Calc (AE-17~AE-23)

```
Initial capital:        20억 (AE-12/AE-14)
WTI principal:          15억 (AE-18)
Leverage:               3x (AE-19)
Notional exposure:      45억
Entry price:            $60 (L274)
Exit price:             $65 (L276)
Price change:           +8.33%
Leveraged return:       +25%
Profit:                 15억 × 25% = 3.75억 (L279: stated_profit = 375,000,000) ✓
Final WTI value:        15억 + 3.75억 = 18.75억
Final cash:             5억 (AE-22: 500,000,000) ✓
Final total:            5억 + 18.75억 = 23.75억 (AE-23: 2,375,000,000) ✓
```

Arc 2 내부 arithmetic 정합 확인 완료. 오류 없음.

### Stage 3 EP5 Blueprint Conversion (AE-31)

```
Blueprint figure:       19.3억 ÷ 970원/$ = 1,989,690.72 ≈ 199만$
Blueprint claims:       "약 198만 달러"
Discrepancy:            ~1만$ (≈970만 원)
```

Blueprint의 환전 계산에 ~1만$ 오차 존재. Minor.
