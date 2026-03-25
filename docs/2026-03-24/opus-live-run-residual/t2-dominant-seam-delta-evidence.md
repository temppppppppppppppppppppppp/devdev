# T2 Dominant Seam Delta — Evidence Ledger

Date: 2026-03-24
Status: evidence ledger (supports dissent note)
Parent: `docs/2026-03-24/opus-live-run-residual/t2-dominant-seam-delta.md`

---

## Evidence Index

| ID | Type | File | Lines | Claim |
|----|------|------|-------|-------|
| E-01 | Blueprint | `stage3/ep_0002/.../final_blueprint__dialogue_focused.json` | L60 | "조부 명의" provenance error |
| E-02 | Blueprint | `stage3/ep_0005/.../final_blueprint__emotion_focused.json` | L27 | "1,930,000,000원" 시작 자본 (EP4 5천만원 미차감) |
| E-03 | Blueprint | `stage3/ep_0005/.../final_blueprint__emotion_focused.json` | L74 | "19억 3천만 원을 달러로 환전" (미차감 자본 재확인) |
| E-04 | Blueprint | `stage3/ep_0005/.../final_blueprint__emotion_focused.json` | L27 | "약 198만 달러의 자본이 WTI 롱 포지션에 쏟아져 들어간다" (전액 투입) |
| E-05 | Blueprint | `stage3/ep_0005/.../final_blueprint__emotion_focused.json` | L33 | equipment: "약 198만 달러가 예치된 파생상품 계좌" |
| E-06 | Blueprint | `stage3/ep_0006/.../final_blueprint__dialogue_focused.json` | L32 | equipment: "19억 3천만 원이 예치된 계좌 내역" |
| E-07 | Blueprint | `stage3/ep_0006/.../final_blueprint__dialogue_focused.json` | L51 | "19억 3천만 원의 시드머니를 온전히 쏟아부을 3배 레버리지" |
| E-08 | Blueprint | `stage3/ep_0006/.../final_blueprint__dialogue_focused.json` | L52 | "시드머니 19억 3천만 원을 극대화할 3배 레버리지 진입 시점" |
| E-09 | Arithmetic | (계산) | — | 1,930,000,000 ÷ 970 = 1,989,690.72 ≈ 199만$, not 198만$ |
| E-10 | Report Error | `ep1-ep8-live-run-residual-opus-survey-report.md` | L33 | EP3 Final Score 97 (should be 90) |

---

## E-01: EP2 Blueprint Provenance Error

**File**: `projects/0324_00_/logs/artifacts/stage3/ep_0002/attempt_02/final_blueprint__dialogue_focused.json`
**Line**: 60

```json
"초기 자본금 20억 원 마련을 위해 조부 명의의 HMC투자증권 신탁 계좌 해지 목표 설정"
```

EP1 확정 canon은 "어머니가 남겨준 신탁". Blueprint가 "조부 명의"로 명시하여 writer가 이를 따름.

**Attribution**: Stage 3 blueprint error. Writer는 blueprint를 충실히 따랐다.

---

## E-02, E-03: EP5 Blueprint 시작 자본 미차감

**File**: `projects/0324_00_/logs/artifacts/stage3/ep_0005/attempt_01/final_blueprint__emotion_focused.json`

**L27** (integrated_scenario):
```
계좌 잔고에 찍힌 1,930,000,000원을 확인한 한시우는
```

**L74** (scene_2.key_events):
```json
"19억 3천만 원을 해외 선물용 달러(약 198만 달러)로 환전"
```

**L77** (scene_2.summary):
```json
"HTS를 설치하고 19억 3천만 원을 달러로 환전하여 파생상품 계좌에 예치한다."
```

EP4에서 법인 설립 자본금 5천만 원을 지출. EP5 시작 시 실제 가용 자본은 19.3억 - 0.5억 = **18.8억**이어야 함.

Blueprint는 19.3억을 그대로 사용. Writer는 이 금액을 따랐고, post-select가 "5천만원 미반영"으로 reject.

**Attribution**: Stage 3가 EP4 지출을 cross-reference하지 않고 arc-level 자본(19.3억)을 그대로 사용.

---

## E-04, E-05: EP5 Blueprint "전액 투입" 명시

**File**: `projects/0324_00_/logs/artifacts/stage3/ep_0005/attempt_01/final_blueprint__emotion_focused.json`

**L27** (integrated_scenario, 후반부):
```
약 198만 달러의 자본이 WTI 롱 포지션에 쏟아져 들어간다
```

**L33** (protagonist_state.equipment):
```json
"약 198만 달러가 예치된 파생상품 계좌"
```

Blueprint는 198만 달러 **전액**이 WTI에 투입되었음을 명시. Equipment에도 "예치된 파생상품 계좌"로 기재.

→ EP5 종료 시 자본 상태: **현금 0, WTI 롱 포지션 ~198만$**

---

## E-06, E-07, E-08: EP6 Blueprint "19.3억 잔존" 명시

**File**: `projects/0324_00_/logs/artifacts/stage3/ep_0006/attempt_03/final_blueprint__dialogue_focused.json`

**L32** (protagonist_state.equipment):
```json
"19억 3천만 원이 예치된 계좌 내역"
```

**L51** (scene_1.content):
```
19억 3천만 원의 시드머니를 온전히 쏟아부을 3배 레버리지.
이 거대한 판을 흔적 없이, 그리고 가장 공격적으로 대행해 줄 사냥개가 필요했다.
```

**L52** (scene_1.description):
```
시드머니 19억 3천만 원을 극대화할 3배 레버리지 진입 시점을 '이번 주 금요일 장 마감 직전'으로 확정한다.
```

→ EP6 시작 시 자본 상태 (blueprint 기준): **현금 19.3억, WTI 미진입**

---

## EP5→EP6 Cross-Blueprint Capital Contradiction (E-04/05 vs E-06/07/08)

| | EP5 Blueprint | EP6 Blueprint |
|---|---|---|
| 자본 위치 | WTI 롱 포지션에 전액 투입 완료 | 계좌에 19.3억 예치 중 |
| 투자 상태 | 매수 체결 완료 | 아직 미진입, 3배 레버리지 진입 예정 |
| 증권사 | HMC투자증권 HTS 직접 거래 | 한미증권 박성호 PB 경유 |

**상호 배타적 상태**: EP5에서 전액 투입이 완료되었다면, EP6에서 19.3억이 계좌에 있을 수 없다.

가능한 해석:
1. EP5의 "전액 투입"이 오류 → 실제로는 계좌 이체만 하고 매수는 미완료
2. EP6의 "19.3억 예치"가 오류 → 실제로는 WTI 포지션 상태
3. EP5 투입 후 EP6 시작 전에 청산 → 양쪽 blueprint 모두 이 과정을 기술하지 않음

어떤 해석이든 **Stage 3 cross-episode reconciliation 실패**가 원인이다.

---

## E-09: EP5 Blueprint 환전 Arithmetic Error

Blueprint L74: "19억 3천만 원 → 약 198만 달러 (환율 970원)"

검증:
```
1,930,000,000 ÷ 970 = 1,989,690.72
→ 약 198.97만 달러 ≈ 199만 달러
```

Blueprint는 "약 198만 달러"로 기재. 1만 달러 (≈970만 원) 차이.

Writer manuscript에서는 "$1,958,762.88" (19억 기준, 보증금 3천만 차감 후)로 작성.
→ Writer는 19억 기준으로 재계산했으나, blueprint의 19.3억 기준 환전 결과와도 불일치.

**Attribution**: Blueprint arithmetic error. Writer는 별도 재계산을 시도했으나 기준 금액 자체가 blueprint에서 잘못 전달됨.

---

## E-10: Terminal 1 Report EP3 Score Error

**File**: `docs/2026-03-24/ep1-ep8-live-run-residual-opus-survey-report.md`
**Line**: 33

Terminal 1 table:
```
| 3 | 2 | PASS | 97 | Leather notebook storage + timeline regression |
```

Console evidence (episode_production.jsonl + console.txt):
- EP3 Round 1: Director Score **97** → **REJECT** (post_select_conflict)
- EP3 Round 2: Director Score **90** → **PASS** (director_primary_pass)

97은 rejected round의 score. Final (accepted) score는 **90**.

---

## Summary

| EP | Terminal 1 Attribution | Terminal 2 Attribution | Key Evidence |
|----|----------------------|----------------------|--------------|
| EP2 | Stage 3 PRIMARY | Stage 3 PRIMARY | E-01 |
| EP3 | Writer PRIMARY | Mixed (writer + blueprint) | — |
| EP5 | Writer PRIMARY | **Stage 3 PRIMARY** | E-02, E-03, E-04, E-05, E-09 |
| EP6 | Writer PRIMARY | **Stage 3 PRIMARY** (capital) + Writer (timeline) | E-06, E-07, E-08 vs E-04, E-05 |
| EP7 | Writer PRIMARY (minor) | Blueprint (minor) | — |
