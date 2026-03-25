# T6: Capital-Time-Item Diff Ledger — Evidence Appendix

Date: 2026-03-24
Terminal: T6
Parent Report: `docs/2026-03-24/opus-ep5-ep7-midarc-residual/t6-capital-time-item-diff-ledger.md`

## E-1: EP4 → EP5 Capital Transition Evidence

### EP4 Blueprint Ending State (file: stage3/ep_0004/attempt_01/final_blueprint__emotion_focused.json)

```json
"protagonist_state": {
    "equipment": [
      "19억 원이 남은 개인 계좌",
      "SW인베스트먼트 사무실 열쇠",
      "임대차 계약서"
    ]
}
```

Capital: 19억 원 (보증금 3천만 원 이미 차감됨)

### EP4 Manuscript Final Lines (file: stage4/ep_0004/attempt_01/final_manuscript__A.txt, L57-61)

```
19억 3천만 원이었던 잔고가 보증금 지출로 인해 19억 원으로 떨어졌지만
...
법인 설립을 위한 초기 자본금 5천만 원의 납입 증명까지 일사천리로 협의를 마쳤다.
이제 19억 원 남짓 남은 개인 계좌의 자금은 조만간 설립될 SW인베스트먼트의 법인 계좌로 이동하여
```

Confirmed: EP4 ends with 19억 원 (보증금 차감), 법인 자본금 5천만은 아직 미이체 상태.

### EP5 Blueprint Start State (file: stage3/ep_0005/attempt_01/final_blueprint__emotion_focused.json)

```json
"integrated_scenario": "... 계좌 잔고에 찍힌 1,930,000,000원을 확인한 한시우는, 해외 선물 거래를 위해 이를 즉시 달러로 환전한다. 환율 970원이 적용되어 약 198만 달러가 파생상품 계좌에 예치된다."
```

**1,930,000,000 = 19.3억 원 — EP4 보증금 3천만 원 차감이 반영되지 않음**

Arithmetic: 1,930,000,000 / 970 = 1,989,690.72 ≈ 약 199만 달러 (blueprint는 "약 198만"으로 반올림)

### EP5 Manuscript Correction (file: stage4/ep_0005/attempt_03/selected_candidate__A_inplace_patch.txt, L29-39)

```
[예수금: 1,900,000,000원]
사무실 보증금 3천만 원을 제외하고 남은 19억 원.
...
환전 메뉴에 전액인 19억 원을 입력하고 실행 버튼을 눌렀다.
[환전이 완료되었습니다.]
[파생상품 계좌 잔고: $1,958,762.88]
```

**1,900,000,000 / 970 = 1,958,762.88 — 정확**

Stage 4 manuscript가 blueprint의 19.3억을 19억으로 자체 교정함.

## E-2: EP6 Blueprint Phantom Capital Evidence

### EP6 Blueprint Equipment (file: stage3/ep_0006/attempt_03/final_blueprint__dialogue_focused.json)

```json
"protagonist_state": {
    "equipment": [
      "19억 3천만 원이 예치된 계좌 내역",
      "로로피아나 캐시미어 코트"
    ]
}
```

**이 시점에서 실제 상태: WTI 480계약 진입 완료, 현금 0원**

### EP6 Manuscript Self-Correction (file: stage4/ep_0006/attempt_03/final_manuscript__A.txt)

씬 1, L5-6:
```
480계약의 롱(매수) 포지션 정보가 선명하게 찍혀 있었다. 진입가 60.20달러. 투입된 증거금은 약 195만 달러, 한화로 19억 원에 달하는 그의 전 재산이었다.
```

씬 4, L70:
```
'내 수중에 현금 15억이 있다고? 웃기는 소리. 지금 내 전 재산 19억 원은 단 1원의 여유도 없이 WTI 롱 포지션 증거금으로 묶여 있다. 당장 굴릴 수 있는 현금 따위는 존재하지 않지.'
```

Stage 4 manuscript는 blueprint의 phantom 19.3억을 무시하고 실제 상태(현금 0원, 포지션만 존재)를 정확히 반영함.

## E-3: EP6 Rejected Attempt Timeline Drift Evidence

### EP6 Rejected Attempt 1 (file: stage4/ep_0006/attempt_01/rejected_best__A.txt, L3)

```
[2006년 4월 18일 밤 11시, 여의도 이면도로 낡은 빌딩 4층 SW인베스트먼트 사무실]
```

### EP6 Blueprint Authority

```json
"ending_state": {
    "timeline": {
      "expression": "2006년 2월 하순의 오후",
      "표현": "2006년 2월 하순의 오후"
    }
}
```

**Rejected attempt: 4월 18일 vs Blueprint authority: 2월 하순 — 약 2개월 forward drift**

### EP6 Rejected Attempt 1 — Phantom Capital (file: stage4/ep_0006/attempt_01/rejected_best__A.txt, L17)

```
확보해 둔 20억 원의 법인 자금을 3배 레버리지 롱 포지션에 밀어 넣는 극단적인 베팅.
```

**"20억 원의 법인 자금" — 어떤 truth chain에도 존재하지 않는 phantom amount**

### EP6 Rejected Attempt 1 — Additional Phantom (file: stage4/ep_0006/attempt_01/rejected_best__A.txt, L25)

```
SW인베스트먼트 법인 인감, 해외 선물 법인 계좌용 보안 매체(OTP), 그리고 20억 원이 찍힌 법인 통장.
```

**법인 통장 20억 원 — EP4에서 법인 자본금은 5천만 원이었으며, 개인 자금 19억 원의 법인 이전은 아직 미완료 상태**

## E-4: EP7 Blueprint Stale Equipment Evidence

### EP7 Blueprint Equipment (file: stage3/ep_0007/attempt_01/final_blueprint__emotion_focused.json)

```json
"protagonist_state": {
    "equipment": [
      "19억 3천만 원이 예치된 계좌 내역",
      "로로피아나 캐시미어 코트",
      "WTI 선물 매수 체결 확인서"
    ]
}
```

**3번째 연속 "19억 3천만 원이 예치된 계좌 내역" — EP4/EP5/EP6 변동 일체 미반영**

참고: "WTI 선물 매수 체결 확인서"는 EP7 씬 5에서 획득되는 아이템으로, ending equipment에 포함은 정확함. 그러나 "19.3억 계좌 내역"과 동시에 기재됨으로써 자본 상태에 대한 혼란을 가중시킴.

### EP7 Manuscript Resolution (file: stage4/ep_0007/attempt_01/patched_after_fix__A_InPlace.txt, L61-65)

```
"현재 제 개인 HTS 계좌에 19억 원 규모의 WTI 파생 포지션이 진입되어 있습니다. 오늘 당장 그 계좌의 자산과 포지션 전액을 한미증권의 이 VVIP 계좌로 이관하겠습니다."

"그리고 그 자금을 담보로 삼아, 즉시 15억 원 규모의 3배 레버리지 롱 포지션을 추가로 실행하세요."
```

Stage 4 manuscript는 blueprint의 phantom capital을 무시하고, 기존 포지션 이관 + 담보 레버리지라는 경제적으로 유효한 구조를 자체 생성하여 자본 흐름을 해결함.

## E-5: Capital State Trajectory Visualization

```
EP3 END    ────────────────────────────> 19.3억 원 (현금)
                                            │
EP4 START  ─────────────────────────────────┘
EP4 EVENT  보증금 -3천만 원 ──────────> 19.0억 원 (현금)
EP4 EVENT  법인 자본금 -5천만 (pending) ──> 19.0억 (현금, 이체 미완)
EP4 END    ────────────────────────────> 19.0억 원 (현금)
                                            │
EP5 BLUEPRINT ─── "1,930,000,000원" ──> ❌ STALE (보증금 미반영)
EP5 MANUSCRIPT ── "1,900,000,000원" ──> ✅ CORRECTED
EP5 EVENT  전액 환전 $1,958,762 ──────> 0원 (현금) + ~195만$ WTI 480계약
EP5 END    ────────────────────────────> 0원 (현금) + WTI 포지션
                                            │
EP6 BLUEPRINT ─── "19.3억 예치" ──────> ❌ PHANTOM (전액 투자 후 0원인데)
EP6 MANUSCRIPT ── "전 재산...증거금" ──> ✅ CORRECTED
EP6 END    ────────────────────────────> 0원 + WTI 포지션 + cliffhanger
                                            │
EP7 BLUEPRINT ─── "19.3억 예치" ──────> ❌ PHANTOM (3연속)
EP7 MANUSCRIPT ── 포지션 이관+담보 ───> ✅ RESOLVED
EP7 END    ────────────────────────────> WTI 이관 + 15억 3x 추가 레버리지
```

## E-6: Cross-Reference with Rescue Round Pattern

| Episode | Stage 4 Attempts | Rescue Likely From Capital Drift? |
|---|---|---|
| EP5 | 3 attempts (att1 rejected, att2 rejected, att3 accepted) | **Possible** — blueprint의 19.3억 vs 실제 19억 차이가 validator 감지 |
| EP6 | 3 attempts (att1 rejected, att2 rejected, att3 accepted) | **Highly likely** — phantom 19.3억이 rejected attempt에서 "20억 법인 자금" hallucination으로 변형, timeline도 2개월 drift |
| EP7 | 1 attempt (selected_before_fix → patched_after_fix) | **Likely** — PASS_WITH_FIX 패턴, 자본 구조 해석 보완 필요 |
