# T9: Artifact Truth Diff Ledger — Raw Evidence

Date: 2026-03-24
Terminal: T9
Parent Report: `docs/2026-03-24/opus-live-run-residual/t9-artifact-truth-diff-ledger.md`

---

## EP2 Evidence Chain

### Blueprint source (dialogue_focused, attempt_02)

File: `projects/0324_00_/logs/artifacts/stage3/ep_0002/attempt_02/final_blueprint__dialogue_focused.json`

Scene 4 "독이 든 성배 거부":
> 시우는 조부가 자신의 이름으로 남겨 둔 HMC투자증권 신탁 계좌 20억 원의 해지를 요구

Scene description consistently uses "조부" (grandfather) as trust originator.

### Rejected manuscript (A_balanced, attempt_01)

File: `projects/0324_00_/logs/artifacts/stage4/ep_0002/attempt_01/rejected_best__A_balanced.txt`

Key passage:
> "조부 명의로 묶여 있는 HMC투자증권의 신탁 계좌"
> "서른 살 전까지는 한정호 회장의 동의 없이 해지 불가"

Additional: Notebook stored in "소형 금고" (safe behind bookshelf, 2nd shelf). Closing line: "제 몫의 **설계**를 시작할 뿐입니다."

### Final manuscript (A, attempt_04)

File: `projects/0324_00_/logs/artifacts/stage4/ep_0002/attempt_04/final_manuscript__A.txt`

Key passage:
> "어머니께서 제 앞으로 남겨주신"

Opens with 김 변호사 phone call. No age restriction. Closing line: "제 몫의 **전쟁**을 시작할 뿐입니다."

### Production JSONL confirmation

EP2 R1 (line 3): `gate_basis: "post_select_conflict"`, rejection warnings include starting location contract violation and V66.1 item re-acquisition.

EP2 R4 (line 10): Director open_review notes: "Blueprint의 '조부 명의' 오류를 '어머니 명의'로 교정."

---

## EP3 Evidence Chain

### Blueprint source (emotion_focused, attempt_01)

File: `projects/0324_00_/logs/artifacts/stage3/ep_0003/attempt_01/final_blueprint__emotion_focused.json`

Scene 2 "온실을 나서는 짐싸기":
> "서랍 깊숙이 넣어둔" 가죽 노트 (notebook stored deep in drawer)

quality_risk: true (MAJOR continuity warning: location discontinuity)

### Rejected manuscript (C_tension, attempt_01)

File: `projects/0324_00_/logs/artifacts/stage4/ep_0003/attempt_01/rejected_best__C_tension.txt`

Key passage:
> 가죽 노트를 "서랍" 깊숙한 곳에서 꺼냄 (takes notebook from desk drawer)
> VVIP arrival: 오후 3시 35분 (same day)
> Trust provenance: "어머니께서 제 앞으로 남겨주신" (correct, consistent with EP2 final)

### Patched manuscript (A, attempt_02)

File: `projects/0324_00_/logs/artifacts/stage4/ep_0003/attempt_02/patched_after_fix__A.txt`

Key changes:
> 가죽 노트를 "소형 금고" (safe behind bookshelf, 2nd shelf)에서 꺼냄
> Day transition: "그리고 다음 날 오후" before VVIP visit
> VVIP arrival: 오후 3시 30분
> Ends with `[원고_끝]` marker

### Production JSONL confirmation (CRITICAL EVIDENCE)

EP3 R2 (line 13): Director open_review:
> "가죽 노트 금고 보관 유지; **Blueprint '서랍 보관' 오류를 '금고 보관'으로 자체 교정**; 타임라인 충돌 해소 (증권사 방문을 '다음 날 오후'로 설정)"

This single sentence from the production log proves:
1. The blueprint said "서랍 보관" — this is a blueprint error, not a writer invention
2. The writer "자체 교정" (self-corrected) the blueprint error
3. The timeline fix was also a writer correction

---

## EP5 Evidence Chain

### Blueprint source (emotion_focused, attempt_01)

File: `projects/0324_00_/logs/artifacts/stage3/ep_0005/attempt_01/final_blueprint__emotion_focused.json`

Scene 2: 19.3억 → 970원/$ → ~$1.98M. No "3배 레버리지" in EP5 blueprint.
Scene 5: "~$1.98 million enters WTI long position" at $60.20. No contract count specified.

### Selected-before-fix manuscript (B, attempt_01)

File: `projects/0324_00_/logs/artifacts/stage4/ep_0005/attempt_01/selected_before_fix__B.txt`

Key financial passages:
> 예수금: 1,900,000,000원 (19억 원)
> 환율 970원/$ → $1,958,762.88
> WTI 증거금 ~4,000$/계약, max 480계약
> 한태준: "부사장님"

### Patched manuscript (A_inplace_patch, attempt_03)

File: `projects/0324_00_/logs/artifacts/stage4/ep_0005/attempt_03/patched_after_fix__A_inplace_patch.txt`

Key changes from before-fix:
> 한태준: "이사님" (title downgraded)
> 한태준 characterization: "후계 구도에서 밀려나 변두리를 맴도는 큰형"
> Two-step transfer process added: 현금화 → 증권 계좌 → 파생상품 계좌

### Production JSONL confirmation

EP5 R1 (line 15): PASS_WITH_FIX reason: "3배 레버리지를 의도한다는 독백과 실제 480계약(약 15배 풀레버리지) 진입 사이의 산술적 불일치"

EP5 R2 (line 17): PASS_WITH_FIX reason: "잔고 19억 원에 대한 설명 문구에서 산술적 오류 발생"

---

## EP6 Evidence Chain

### Blueprint source (dialogue_focused, attempt_03)

File: `projects/0324_00_/logs/artifacts/stage3/ep_0006/attempt_03/final_blueprint__dialogue_focused.json`

Scene 1: "2006년 2월 하순", WTI June futures at $60.20, "3배 레버리지 진입" planned for "이번 금요일"
Scene 2: Park Seongho at Hanmi Securities, Siwoo needs "15억 원 3배 레버리지 WTI 주문"
Park's context: "20억 원 B등급 회사채 펀드 잔여 물량" (Park's KPI burden — NOT Si-woo's money)

### Rejected manuscript (A_tension, attempt_01)

File: `projects/0324_00_/logs/artifacts/stage4/ep_0006/attempt_01/rejected_best__A_tension.txt`

Key inventions (not in blueprint):
> "[2006년 4월 18일 밤 11시]" — changed February to April
> "확보해 둔 20억 원의 법인 자금" — invented 20億 corporate fund
> "20억 원이 찍힌 법인 통장" — reiterated
> "본가를 나설 때 챙겨 왔던 명품 의류들" — coat from family home
> 사무실 referred to as "오피스텔"

### Final manuscript (A, attempt_03)

File: `projects/0324_00_/logs/artifacts/stage4/ep_0006/attempt_03/final_manuscript__A.txt`

Key corrections:
> "2006년 2월 하순의 심야" — February restored
> No 20億 법인 references — completely removed
> "내 수중에 현금 15억이 있다고? 웃기는 소리" — explicitly denies cash
> "전 재산 19억 원은 단 1원의 여유도 없이 WTI 롱 포지션 증거금으로 묶여 있다"
> Coat: "개인 신용카드의 남은 한도를 긁어 구입" — newly purchased

### Production JSONL confirmation

EP6 R1 (line 20): Director REJECT (score 78). Reasons: timeline, location, item acquisition.
EP6 R2 (line 22): Continuity firewall (score 44). CRITICAL: 자본금 정합성 모순.
EP6 R3 (line 24): PASS (score 98). Resolution: "자본금 모순을 한시우의 내면 묘사로 해결."

---

## EP7 Evidence Chain

### Blueprint source (emotion_focused, attempt_01)

File: `projects/0324_00_/logs/artifacts/stage3/ep_0007/attempt_01/final_blueprint__emotion_focused.json`

Scene 5: "2024 파산 기억의 환상통이 손목을 스침" — references 2024 bankruptcy correctly, no "18년 전" phrasing.

### Selected-before-fix manuscript (B, attempt_01)

File: `projects/0324_00_/logs/artifacts/stage4/ep_0007/attempt_01/selected_before_fix__B.txt`

Key line:
> "18년 전 시우 자신을 짓눌렀던 파산의 환상통이 미세하게 손목을 훑고 지나갔다"

### Patched manuscript (A_InPlace, attempt_01)

File: `projects/0324_00_/logs/artifacts/stage4/ep_0007/attempt_01/patched_after_fix__A_InPlace.txt`

Changed line:
> "**전생에** 시우 자신을 짓눌렀던 파산의 환상통이 미세하게 손목을 훑고 지나갔다"

Single-line change. All other content character-identical.

### Production JSONL confirmation

EP7 R1 (line 26): PASS_WITH_FIX reason: "Blueprint의 오류이긴 하나, 회귀 전 미래의 파산 기억을 '18년 전'이라고 표현한 타임라인 모순"

Note: Director says "Blueprint의 오류이긴 하나" but the blueprint artifact does NOT contain "18년 전." The Director's attribution to the blueprint appears inaccurate.

---

## EP8 Residual Evidence

### Final manuscript (A, attempt_01)

File: `projects/0324_00_/logs/artifacts/stage4/ep_0008/attempt_01/final_manuscript__A.txt`

Line 3 (opening bridge from EP7):
> "**전생에** 시우 자신을 짓눌렀던 파산의 끔찍한 감각" — correct, matches EP7 patch

Line 107 (scene 5 internal monologue):
> "**18년 전** 파산의 트라우마" — incorrect, same error as EP7 pre-patch

These two lines within the same manuscript use different temporal references for the same event, creating an internal contradiction that was not caught by Round 1 validation.

---

## Cross-Episode Financial State Progression

| Episode | Established Balance | Key Transaction | Ending State |
|---|---|---|---|
| EP1 | Trust exists (20億, 어머니 명의) | None | Trust intact |
| EP2 | Trust released by Chairman | 해지 승인 획득 | Trust pending dissolution |
| EP3 | 20億 - 3.5% fee = **19.3億** | Trust liquidated, cash received | 19.3億 현금 |
| EP4 | 19.3億 - 보증금 3천만 = **19億** | Office deposit, 법인 설립 | 19億 + SW Investment |
| EP5 | 19億 → $1.98M (970원/$) | All-in WTI long @ $60.20 | WTI position, 0 cash |
| EP6 | WTI position + 0 cash | 15億 3x leverage via Hanmi (bluff) | Same + Hanmi arrangement |
| EP7 | Same | Trade confirmation printed | Same |
| EP8 | Same | WTI drops to $59.50 | Unrealized loss -5,250만 |

**Note**: EP5→EP6 transition is where the capital state becomes most vulnerable to writer invention, because "all funds deployed" is a negative state (zero cash) that must be explicitly constrained.
