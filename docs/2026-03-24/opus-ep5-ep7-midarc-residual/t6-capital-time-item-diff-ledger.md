# T6: Capital-Time-Item Diff Ledger

Date: 2026-03-24
Terminal: T6
Lane: Capital-Time-Item Diff Ledger
Status: final (3-pass audited)
Master Order: `docs/2026-03-24/ep5-ep7-midarc-residual-6terminal-master-order.md`
Report Path: `docs/2026-03-24/opus-ep5-ep7-midarc-residual/t6-capital-time-item-diff-ledger.md`
Evidence Path: `docs/2026-03-24/opus-ep5-ep7-midarc-residual/t6-capital-time-item-diff-ledger-evidence.md`

## 1. Scope

Cross-episode ledger tracking capital, timeline, and item/location state from EP4 accepted truth through EP7 final truth, with the goal of identifying where the first undeniable contradiction emerges and at which stage (Stage 3 blueprint vs Stage 4 manuscript expansion).

## 2. Evidence Sources

| Source | Path | Role |
|---|---|---|
| EP4 Blueprint | `logs/artifacts/stage3/ep_0004/attempt_01/final_blueprint__emotion_focused.json` | Baseline blueprint authority |
| EP4 Final Manuscript | `logs/artifacts/stage4/ep_0004/attempt_01/final_manuscript__A.txt` | Baseline accepted truth |
| EP5 Blueprint | `logs/artifacts/stage3/ep_0005/attempt_01/final_blueprint__emotion_focused.json` | EP5 blueprint authority |
| EP5 Final Manuscript | `logs/artifacts/stage4/ep_0005/attempt_03/selected_candidate__A_inplace_patch.txt` | EP5 accepted truth |
| EP6 Blueprint | `logs/artifacts/stage3/ep_0006/attempt_03/final_blueprint__dialogue_focused.json` | EP6 blueprint authority |
| EP6 Rejected Attempt 1 | `logs/artifacts/stage4/ep_0006/attempt_01/rejected_best__A.txt` | EP6 rejected evidence (timeline drift) |
| EP6 Final Manuscript | `logs/artifacts/stage4/ep_0006/attempt_03/final_manuscript__A.txt` | EP6 accepted truth |
| EP7 Blueprint | `logs/artifacts/stage3/ep_0007/attempt_01/final_blueprint__emotion_focused.json` | EP7 blueprint authority |
| EP7 Selected Before Fix | `logs/artifacts/stage4/ep_0007/attempt_01/selected_before_fix__B.txt` | EP7 pre-fix candidate |
| EP7 Patched After Fix | `logs/artifacts/stage4/ep_0007/attempt_01/patched_after_fix__A_InPlace.txt` | EP7 accepted truth |

All paths relative to `projects/0324_00_/`.

## 3. Capital Diff Ledger

### 3.1 EP4 → EP5 Transition (Baseline → First Investment)

| Field | EP4 Blueprint Ending | EP4 Manuscript Ending | EP5 Blueprint Start | EP5 Manuscript Start | Verdict |
|---|---|---|---|---|---|
| Total Capital | 19억 원 (개인 계좌) | 19억 원 (보증금 3천만 제외) | **19억 3천만 원** (1,930,000,000) | **19억 원** (1,900,000,000) | **Stage 3 drift — confirmed** |
| Dollar Equivalent | n/a | n/a | **약 198만 달러** (blueprint) | **$1,958,762.88 (약 195만 달러)** (manuscript) | Stage 3 inflated by ~3만 달러 |
| 보증금 3천만 원 Deduction | Applied | Applied | **NOT applied** | Applied | Blueprint ignores EP4 event |

**Finding C-1: EP5 Blueprint Capital Stale**

- EP4 ends with 19억 원 (보증금 3천만 차감됨)
- EP5 blueprint `integrated_scenario`는 "1,930,000,000원"으로 시작 — 보증금 차감이 반영되지 않음
- EP5 manuscript는 이를 자체 교정하여 "1,900,000,000원"으로 정확히 표시
- 차이: 3천만 원 (보증금)
- 분류: `confirmed primary cause` — Stage 3 blueprint가 prior-episode 자본변동을 carry forward 하지 않음
- 환산 달러 차이: blueprint ~$1,989,690 vs manuscript $1,958,762 (약 $30,928 gap)

**보충: 법인 자본금 5천만 원 미해결 상태**

EP4에서 SW인베스트먼트 법인 자본금 5천만 원 납입이 합의되었으나, EP4 manuscript 기준 실제 이체는 "조만간" 수행 예정으로 남음. EP5 manuscript는 개인 계좌 19억 원 전액을 달러 환전하며, 법인 자본금 5천만 원이 선이체되었는지 언급하지 않음. 이것은 서사적으로 "법인 설립 수일 소요" + "당일 밤 WTI 진입"의 시간차로 해석 가능하나, 엄밀히는 capital chain에 5천만 원 ambiguity가 존재함. 분류: `not proven` — rescue round의 직접 원인으로 보기 어려움.

### 3.2 EP5 → EP6 Transition (Investment → Broker Acquisition)

| Field | EP5 Ending Truth | EP6 Blueprint State | EP6 Manuscript State | Verdict |
|---|---|---|---|---|
| WTI Position | 480계약 롱, 진입가 $60.20, 증거금 ~195만 달러 전액 투입 | 명시 안 됨 | 정확히 carry forward됨 (씬 1) | Manuscript corrects |
| Available Cash | 0원 (전액 증거금 투입) | **"19억 3천만 원이 예치된 계좌 내역"** (equipment) | **"전 재산 19억 원은 단 1원의 여유도 없이 WTI 롱 포지션 증거금으로 묶여 있다"** (씬 4 내면독백) | **Stage 3 critical drift** |
| 추가 투자금 15억 Source | n/a | "15억 원어치의 자금을 WTI 6월물 3배 레버리지 롱 포지션에" (scenario) | 기존 포지션을 담보로 한 추가 레버리지로 해석 | Blueprint gap |

**Finding C-2: EP6 Blueprint Capital Phantom — CRITICAL**

- EP5 종료 시 전액 WTI 투입 → 현금 0원
- EP6 blueprint `protagonist_state.equipment`에 **"19억 3천만 원이 예치된 계좌 내역"** 기재 — 이것은 EP4 시작 시점의 원래 시드머니로, EP4(보증금 -3천만), EP5(WTI 전액투자) 어떤 변동도 반영하지 않은 완전 stale 상태
- EP6 manuscript는 이를 인지하고 자체 교정: 씬 1에서 기존 480계약 포지션을 명시적으로 carry forward하고, 씬 4 내면독백에서 "현금은 없다"고 명시
- 분류: `confirmed primary cause` — Stage 3 blueprint가 자본 상태를 episode 경계에서 완전히 재설정(reset)함
- 이 갭은 Stage 4가 "15억 원" 추가 투자의 출처를 설명해야 하는 부담을 만들며, rescue round의 직접 원인이 됨

### 3.3 EP6 → EP7 Transition (Cliffhanger → Execution)

| Field | EP6 Ending Truth | EP7 Blueprint State | EP7 Manuscript State | Verdict |
|---|---|---|---|---|
| WTI 기존 포지션 | 480계약 @$60.20 (개인 HTS) | 명시적 언급 없음 | 씬 3: "현재 제 개인 HTS 계좌에 19억 원 규모의 WTI 파생 포지션" — carry forward | Manuscript fills gap |
| Available Cash | 0원 | **"19억 3천만 원이 예치된 계좌 내역"** (equipment) | 기존 포지션 이관 + 담보 레버리지 구조 | **Stage 3 critical drift — 3연속** |
| 신규 투자 | 한시우가 "내가 살 건..." 선언 직전 | 15억 원 3배 레버리지 (45억 명목) | 15억 원 3배 레버리지 — 기존 포지션 담보 기반 | Blueprint-manuscript 일치 |
| 자금 구조 | 미결 | 설명 안 됨 | 씬 3: "그 계좌의 자산과 포지션 전액을 한미증권 VVIP 계좌로 이관하겠습니다. 그리고 그 자금을 담보로 삼아..." | **Manuscript invents resolution** |

**Finding C-3: EP7 Blueprint Capital — 3rd Consecutive Stale Equipment**

- EP7 blueprint `protagonist_state.equipment`에 또다시 **"19억 3천만 원이 예치된 계좌 내역"** 기재
- EP4(보증금 -3천만), EP5(WTI 전액투자), EP6(추가 레버리지 논의) 어떤 이벤트도 반영되지 않음
- Stage 3는 `protagonist_state.equipment`를 episode-independent static field로 취급하고 있음
- 분류: `confirmed primary cause` — 동일 root cause의 3번째 반복

### 3.4 Capital State Summary Table

| Episode | Blueprint Capital | Manuscript Capital | True Available Cash | Delta | Stage 3 Correct? |
|---|---|---|---|---|---|
| EP4 END | 19억 원 | 19억 원 | 19억 원 | 0 | Yes |
| EP5 START | **19.3억 원** | 19억 원 | 19억 원 | **-3천만** | **No** |
| EP5 END | ~198만$ invested | ~195만$ invested | **0원** | n/a | Partial |
| EP6 START | **19.3억 예치** | 0원 (전액 투입) | **0원** | **-19.3억** | **No — phantom** |
| EP6 END | 미결 (cliffhanger) | 0원 + 포지션 | **0원** | n/a | n/a |
| EP7 START | **19.3억 예치** | 0원 + 19억 포지션 | **0원** | **-19.3억** | **No — phantom** |
| EP7 END | 매수 체결 | 19억 포지션 이관 + 15억 3x 추가 | 포지션 기반 담보 | n/a | n/a |

## 4. Timeline Diff Ledger

### 4.1 Accepted Truth Timeline Chain

| Episode | Blueprint Timeline | Manuscript Timeline | Verdict |
|---|---|---|---|
| EP4 | "2006년 1월, 노을이 지는 저녁 무렵" | 동일 (명시적 날짜 없음) | Clean |
| EP5 | "2006년 1월 늦은 밤" | 동일 (저녁→늦은밤) | Clean |
| EP6 | "2006년 2월 하순의 오후" | "2006년 2월 하순의 심야" (씬 1) → "다음 날 오후" (씬 2 이후) | **Loose — 시작 시점 불일치** |
| EP7 | "2006년 2월 하순의 늦은 오후" | "오후 늦은 시간" (씬 1~5 연속) | Clean — EP6 직접 이어짐 |

**Finding T-1: EP6 Time Flow Internal Tension**

- EP6 blueprint `ending_state.timeline`: "2006년 2월 하순의 오후"
- EP6 manuscript 씬 1: "2006년 2월 하순의 심야" — 밤을 새우며 모니터 분석
- EP6 manuscript 씬 2: "다음 날 오후" — 한미증권 방문
- Blueprint의 `time_flow`는 "늦은 밤 → 다음 날 오후"로 정확하나, `ending_state`의 timeline 표현은 시작 시점과 혼동 가능
- 분류: `artifact-truth mismatch` — 기능적 모순은 아니나 메타데이터 정확도 미흡

### 4.2 Rejected Manuscript Timeline Drift — CRITICAL

| Field | Blueprint Authority | Rejected EP6 Attempt 1 | Accepted EP6 Attempt 3 |
|---|---|---|---|
| Scene 1 Time | 2006년 2월 하순 심야 | **"2006년 4월 18일 밤 11시"** | 2006년 2월 하순 심야 |
| Scene 2 Time | 다음 날 오전 | **"다음 날 오전 6시"** | 다음 날 오후 |
| Scene 3 Time | 오후 | **"같은 날 오후 2시"** | 오후 |

**Finding T-2: Rejected EP6 Timeline 2-Month Forward Drift**

- Rejected EP6 attempt_01은 "2006년 4월 18일"로 시작 — blueprint의 "2006년 2월 하순"에서 약 2개월 앞으로 점프
- 이 시점은 작중 이란 핵 위기 이후 WTI 상승기와 겹치므로, LLM이 거시경제 사건 순서를 자체 추론하여 timeline을 재배치한 것으로 보임
- Attempt 3에서 교정됨 → rescue round의 원인 중 하나
- 분류: `confirmed secondary amplifier` — Stage 4 LLM의 자체 timeline 추론이 blueprint authority를 override하는 패턴

## 5. Item / Location Diff Ledger

### 5.1 Key Items Cross-Episode Tracking

| Item | EP4 Origin | EP5 | EP6 | EP7 | Carry Status |
|---|---|---|---|---|---|
| SW인베스트먼트 사무실 열쇠 | EP4 씬 3에서 획득 | Blueprint equipment에 포함 | 직접 언급 없음 | 직접 언급 없음 | Decays after EP5 |
| 임대차 계약서 | EP4 씬 3에서 획득 | EP5 씬 1에서 존재 확인 | 언급 없음 | 언급 없음 | Decays after EP5 |
| 가죽 노트 (18년 레시피) | EP4 씬 1에서 등장 | EP5 씬 1에서 존재 확인 | 언급 없음 | 언급 없음 | Decays after EP5 |
| 캐시미어 코트 | EP4 전편 등장 | EP5 씬 1에서 등장 | **EP6 blueprint equipment에 "로로피아나 캐시미어 코트"** 신규 등장 | EP7 blueprint equipment에 포함 | **EP6에서 구매 이벤트 발생** |
| 파텍필립 노틸러스 | 미등장 | 미등장 | EP6 씬 3에서 첫 등장 | EP7 씬 2에서 등장 | EP6에서 신규 도입 |
| WTI 매수 체결 확인서 | n/a | n/a | n/a | EP7 씬 5에서 획득 | EP7 신규 |

**Finding I-1: Item State Mostly Clean**

- 아이템 추적은 대체로 정합적
- EP6에서 로로피아나 코트와 파텍필립 시계가 신규 구매/착용으로 등장하며, 이는 서사적으로 "박성호를 낚기 위한 미끼"로 설명됨
- EP6 rejected attempt_01은 "본가를 나설 때 챙겨왔던 명품 의류들 사이에서" 코트를 꺼내는 것으로 처리, accepted attempt_03은 "여의도 중심가 명품 부티크에서 구입"으로 처리 — 두 버전 모두 서사적으로 유효하나 acquisition 경로가 다름
- 분류: `cleared / not primary`

### 5.2 Location Chain

| Episode | Blueprint Start Location | Blueprint End Location | Manuscript Match |
|---|---|---|---|
| EP4 | 여의도 HMC투자증권 빌딩 앞 | 여의도 이면도로 낡은 빌딩 4층 SW인베스트먼트 사무실 | Yes |
| EP5 | 여의도 이면도로 낡은 빌딩 4층 SW인베스트먼트 사무실 | 여의도 SW인베스트먼트 사무실 데스크 앞 | Yes |
| EP6 | 여의도 이면도로 낡은 빌딩 4층 SW인베스트먼트 사무실 | 여의도 한미증권 본사 VVIP 프라이빗 룸 | Yes |
| EP7 | 여의도 한미증권 본사 VVIP 프라이빗 룸 | 여의도 한미증권 본사 VVIP 프라이빗 룸 문 앞 | Yes |

**Finding I-2: Location Chain Clean**

- EP4→EP5→EP6→EP7 location chain은 완벽하게 연속적
- EP6→EP7은 동일 장소(한미증권 VVIP 프라이빗 룸)에서 cliffhanger→continuation으로 이어짐
- 분류: `cleared / not primary`

## 6. Contradiction First-Emergence Map

| Contradiction | First Undeniable At | Stage | Severity |
|---|---|---|---|
| **C-1: 3천만 보증금 미반영** | EP5 Blueprint | **Stage 3** | Medium — manuscript 자체교정 가능 |
| **C-2: 19.3억 phantom capital** | EP6 Blueprint equipment | **Stage 3** | **Critical — 전액 투입 후 0원인데 19.3억 기재** |
| **C-3: 3연속 stale equipment** | EP7 Blueprint equipment | **Stage 3** | Critical — systemic pattern |
| **C-4: 15억 출처 불명** | EP6-EP7 Blueprint scenario | **Stage 3** | High — manuscript가 담보 구조로 해결하나 blueprint에 근거 없음 |
| **T-2: 2개월 timeline forward drift** | EP6 Rejected Attempt 1 | **Stage 4** | High — rescue round 원인 |

**최초 부정할 수 없는 모순 지점: EP6 Blueprint의 `protagonist_state.equipment` — "19억 3천만 원이 예치된 계좌 내역"**

이 시점에서 EP5에서 전액 WTI에 투입된 자본이 마치 건재한 것처럼 blueprint에 기재되어 있다. 이것은 단순한 수치 오류가 아니라, Stage 3 blueprint 생성기가 **prior-episode ending state를 다음 episode의 protagonist_state에 carry forward하지 않는 구조적 결함**을 드러낸다.

## 7. Root Cause Analysis

### 7.1 Primary Root Cause: Stage 3 `protagonist_state.equipment` Static Reset

Stage 3 blueprint ensemble이 `protagonist_state.equipment` 필드를 생성할 때:
- prior episode의 `ending_state`를 참조하지 않거나
- 초기 시드머니(19.3억)를 static default로 사용하거나
- 자본 변동 이벤트(지출, 투자, 환전)를 추적하는 메커니즘이 없음

이로 인해 EP5→EP6→EP7에서 동일한 "19억 3천만 원" phantom capital이 3연속 반복됨.

### 7.2 Secondary Amplifier: Stage 4 LLM Timeline Self-Inference

EP6 rejected attempt_01에서 확인된 바와 같이, Stage 4의 LLM은 작품의 거시경제 배경(이란 핵 위기, WTI 상승)을 자체 추론하여 blueprint의 timeline authority("2006년 2월 하순")를 override하고 "2006년 4월 18일"로 재배치함. 이는 rescue round를 유발하는 secondary factor.

### 7.3 Stage 4 Self-Correction Capability

Stage 4 manuscript는 blueprint의 capital drift를 상당 부분 자체 교정함:
- EP5: 19.3억 → 19억으로 보증금 차감 반영
- EP6 씬 1: 기존 포지션 carry forward
- EP6 씬 4: "현금 0원" 명시적 내면독백
- EP7 씬 3: 포지션 이관 + 담보 레버리지 구조로 15억 출처 해결

그러나 이 교정은 Stage 4 LLM의 implicit reasoning에 의존하며, blueprint authority와 충돌할 때 validator(continuity_firewall, post_select_conflict)가 개입하여 rescue round를 유발함.

## 8. Lane Conclusions

### 8.1 Claim Classification

| Claim | Classification |
|---|---|
| Stage 3 blueprint가 capital state를 episode 경계에서 carry forward 하지 않음 | `confirmed primary cause` |
| protagonist_state.equipment가 static default (19.3억)로 고정됨 | `confirmed primary cause` |
| Stage 4 LLM이 blueprint capital drift를 implicit self-correction함 | `confirmed secondary amplifier` — 교정 자체는 올바르나, blueprint authority와의 충돌이 rescue round 유발 |
| Stage 4 rejected attempt에서 timeline forward drift 발생 | `confirmed secondary amplifier` |
| Item/location chain에 primary-level 모순 존재 | `cleared / not primary` |

### 8.2 Mandatory Final Lines

- **Dominant seam in this lane: Stage 3**
- **Can this lane explain a real rescue round by itself: yes** — EP6 attempt_01/02의 reject 원인은 Stage 3 blueprint의 phantom capital이 Stage 4에서 충돌을 일으키고, validator가 이를 감지하여 reject하는 패턴. EP6 rejected attempt_01의 "20억 원 법인 자금" 등 Stage 4가 phantom capital을 자체 해석하면서 발생하는 hallucination이 reject의 직접 원인.
- **Would this lane justify a bounded next execution wave: yes** — Stage 3 blueprint ensemble의 `protagonist_state` carry-forward 로직 수정. 구체적으로: prior episode `ending_state`의 capital/equipment 변동을 다음 episode blueprint 생성 시 입력으로 주입하는 contract 보강.
