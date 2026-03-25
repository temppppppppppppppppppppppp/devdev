# T4 Evidence: Stage4 Manuscript Expansion — EP5-EP7

## 1. Artifact File Inventory

### EP5 Stage 4 Artifacts
```
stage4/ep_0005/attempt_01/rejected_best__B_balanced.txt       — 5 scenes, 161 lines, markdown
stage4/ep_0005/attempt_01/selected_before_fix__B.txt          — identical narrative to rejected_best
stage4/ep_0005/attempt_02/rejected_best__A_inplace_patch.txt  — JSON-escaped, same 5-scene narrative
stage4/ep_0005/attempt_02/selected_before_fix__A_inplace_patch.txt — JSON-escaped, same narrative
stage4/ep_0005/attempt_03/patched_after_fix__A_inplace_patch.txt   — 5 scenes, markdown, PASS version
stage4/ep_0005/attempt_03/selected_candidate__A_inplace_patch.txt  — identical to patched_after_fix
```

### EP6 Stage 4 Artifacts
```
stage4/ep_0006/attempt_01/rejected_best__A.txt           — 5 scenes, truncated at "내가 살 건..."
stage4/ep_0006/attempt_01/rejected_best__A_tension.txt   — identical content, tension strategy label
stage4/ep_0006/attempt_02/rejected_best__A.txt           — same content, rejected again
stage4/ep_0006/attempt_02/rejected_best__A_tension.txt   — same content
stage4/ep_0006/attempt_03/selected_candidate__A.txt      — PASS version, location corrected to 시중은행
stage4/ep_0006/attempt_03/final_manuscript__A.txt         — identical to selected_candidate
```

### EP7 Stage 4 Artifacts
```
stage4/ep_0007/attempt_01/selected_before_fix__B.txt       — 5 scenes, 한미증권→시중은행 partial fix
stage4/ep_0007/attempt_01/patched_after_fix__A_InPlace.txt — PASS version, all corrections applied
```

### EP5-EP7 Stage 3 Blueprints
```
stage3/ep_0005/attempt_01/final_blueprint__emotion_focused.json  — 1 attempt, clean
stage3/ep_0006/attempt_03/final_blueprint__dialogue_focused.json — 3 attempts, clean
stage3/ep_0007/attempt_01/final_blueprint__emotion_focused.json  — 1 attempt, clean
```

## 2. Blueprint vs Manuscript Capital Ledger

| Field | EP5 Blueprint | EP5 Manuscript (all attempts) | Mismatch? |
|-------|--------------|------------------------------|-----------|
| 초기자금 | 1,930,000,000원 | 1,900,000,000원 | **YES** — 3천만 차이 |
| 환전 후 | ~198만 달러 | $1,958,762.88 (~195만 달러) | **YES** — ~3만 달러 차이 |
| WTI 계약수 | 480계약 | 480계약 | match |
| 진입가 | $60.20 | $60.20 | match |
| 환율 | 970원 | 970원 | match |

Note: Blueprint's `integrated_scenario` says "보증금 3천만 원을 제외하고" but also says "1,930,000,000원" (implying 법인 설립 5천만 + 보증금 3천만 = 8천만 제외). Manuscripts simplify to "보증금 3천만 원을 제외하고 남은 19억 원", dropping the 법인 설립 자본금 deduction.

## 3. Console Evidence — EP5 Rejection Chain

### R1: PASS_WITH_FIX → REJECT downgrade
```
console.txt L1221: Director 판정: PASS_WITH_FIX (점수: 92, 선택: 후보 A)
console.txt L1234: [A-3] Post-select continuity conflict: 제3화에서 시중은행 소속이었던 박성호 PB가 제5화에서는 한미증권 소속으로 등장
console.txt L1236: [A-3] Post-select history conflict: 이전 회차에서 시중은행 본점 소속이었던 박성호 PB
console.txt L1238: [TF-3] Provisional PASS → REJECT downgrade: 2 post-select conflicts (continuity, history)
```

### R2: REJECT
```
console.txt L1324: Director 판정: REJECT (점수: 78, 선택: 후보 A)
console.txt L1325: 사유: EP 3에서 이미 기선 제압당한 박성호 PB의 태도가 '호구로 얕봄'으로 리셋됨
console.txt L1329: 선택 사유: Blueprint의 '한미증권' 오류를 이전 화의 설정에 맞춰 '시중은행 본점'으로 자체 교정한 점은 훌륭합니다. 그러나 박성호 PB의 태도와 제안 내용에서 직전 화(EP 3)와의 심각한 설정 충돌
```

### R3: PASS
```
console.txt L1427: Director 판정: PASS (점수: 95, 선택: 후보 A)
console.txt L1391: [ASP] 레드팀 교정 발동 (재시도 3회차)
```

## 4. Console Evidence — EP6 Rejection Chain

### R1: REJECT
```
console.txt L1508: Director 판정: REJECT (점수: 75, 선택: 후보 C)
console.txt L1509: 사유: 직전 화와의 장소 연속성 단절 (시중은행 -> 한미증권)
console.txt L1536: [MINOR] 수학: 15억 원 사용 후 잔액을 5억 원으로 표기함 (정상 산술: 4.7억)
```

### R2: PASS
```
console.txt L1576: Director 판정: PASS (점수: 90, 선택: 후보 A)
console.txt L1583-1584: Blueprint에 잘못 기재된 장소(한미증권)를 무시하고 연속성을 지킨 점이 매우 훌륭합니다.
```

## 5. Console Evidence — EP7 Rejection Chain

### R1: REJECT
```
console.txt L1661: Director 판정: REJECT (점수: 86, 선택: 후보 C)
console.txt L1662: 사유: 직전 화와의 장소 연속성 오류
console.txt L1666-1668: 세 후보 모두 Blueprint의 오류를 그대로 수용하여 직전 화의 장소(시중은행 본점)를 '여의도 한미증권'으로 잘못 기재하는 모순을 범했으나
```

### R2: REJECT
```
console.txt L1721: Director 판정: REJECT (점수: 75, 선택: 후보 A)
console.txt L1722: 사유: 작품 전체 시점(3인칭) 위반
console.txt L1726-1727: Blueprint의 씬 구성과 장소 오류(한미증권 -> 시중은행 본점)를 자체적으로 잘 교정하여 서사를 전개했습니다. 그러나 치명적인 시점 위반
console.txt L1732: 원고 전체의 1인칭 서술('나는', '내')을 3인칭('한시우는', '그는')으로 전면 수정할 것
```

### R3: PASS
```
console.txt L1812: Director 판정: PASS (점수: 96, 선택: 후보 A)
console.txt L1774: [ASP] 레드팀 교정 발동 (재시도 3회차)
console.txt L1813: 이전 피드백(3인칭 시점 전환, 장소 오류 수정, 통장 획득 중복 묘사 삭제)을 완벽하게 반영
```

## 6. Blueprint 한미증권 오류 — Direct Evidence

### EP6 Blueprint (stage3/ep_0006/attempt_03/final_blueprint__dialogue_focused.json)
```json
"scene_3": {
    "title": "호구의 등장",
    "location": "한미증권 본사 VIP 라운지",
    "content": "여의도 한미증권 본사 2층 VVIP 라운지. 박성호 팀장은..."
}
```

### EP7 Blueprint (stage3/ep_0007/attempt_01/final_blueprint__emotion_focused.json)
```json
"start_location": "여의도 한미증권 본사 VVIP 프라이빗 룸",
"integrated_scenario": "여의도 한미증권 본사 VVIP 프라이빗 룸. \"박 팀장님. 그 쓰레기 같은 채권 펀드 브리핑은..."
```

### Director's Verdict on Blueprint Error (EP6 R2 PASS justification)
```
console.txt L1583-1584: Blueprint에 잘못 기재된 장소(한미증권)를 무시하고 연속성을 지킨 점이 매우 훌륭합니다.
```

This confirms the Director itself recognizes the blueprint contains an error that Stage 4 must override.

## 7. EP5 Attempt Content Comparison

All 6 EP5 manuscript files contain the **same** 5-scene narrative with only formatting differences:
- attempt_01 files: markdown with ### headers
- attempt_02 files: JSON-escaped single string (씬 headings without ###)
- attempt_03 files: markdown with ### headers

Content differences between attempts are minimal — primarily the 한태준 호칭 ("부사장님" → "이사님") and minor prose variations. The underlying narrative, capital figures, scene flow, and character actions are identical across all attempts. This confirms Stage 4 is not inventing new narrative material on retry — it's producing the same blueprint-faithful expansion with minor cosmetic variation.

## 8. EP7 POV Violation — Direct Evidence

The `selected_before_fix__B.txt` file (EP7 attempt 1) uses 3인칭 throughout:
```
한시우는 찻잔에서 손을 떼고 등받이에 몸을 깊숙이 기댔다.
```

However, console.txt L1744 reports:
```
[MAJOR] 상태: 후보 A는 전체가 1인칭 주인공 시점('나는', '내')으로 서술됨
```

This means the R2 candidate A (which is not preserved in artifacts — only the final patched version is saved) was written in 1인칭. The saved `patched_after_fix__A_InPlace.txt` is the R3 corrected version in 3인칭. The 1인칭 error was a pure Stage 4 LLM output aberration.
