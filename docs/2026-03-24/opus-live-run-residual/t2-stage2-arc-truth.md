# T2 Lane Report — Stage2 Arc Truth

Date: 2026-03-24
Status: final (3-pass audited, confidence 95%)
Lane: `Stage2 Arc Truth`
Document Type: lane survey report (NOT merged conclusion, NOT execution SSOT)
Governing Order: `docs/2026-03-24/ep1-ep8-live-run-residual-10terminal-master-order.md`
Evidence Ledger: `docs/2026-03-24/opus-live-run-residual/t2-stage2-arc-truth-evidence.md`
Primary Evidence:
- `projects/0324_00_/logs/artifacts/stage2/arc_001/attempt_01/final_arc__conservative.json`
- `projects/0324_00_/logs/artifacts/stage2/arc_002/attempt_01/final_arc__balanced.json`
Cross-reference:
- `projects/0324_00_/logs/artifacts/stage3/ep_0002/attempt_02/final_blueprint__dialogue_focused.json`
- `projects/0324_00_/logs/artifacts/stage3/ep_0005/attempt_01/final_blueprint__emotion_focused.json`
- `projects/0324_00_/logs/artifacts/stage3/ep_0006/attempt_03/final_blueprint__dialogue_focused.json`

---

## 1. Executive Summary

Arc 1/Arc 2 실물 기준으로 account/provenance/capital state truth를 전수 검사한 결과, **Stage 2 arc artifact는 내부적으로 대체로 일관되나, Stage 3 blueprint가 arc truth를 잘못 소비한 지점이 4개 확인**되었다.

핵심 발견:

1. **Provenance**: Arc 1은 20억을 **3개 출처** (조부 현금유산 + 승마 스폰서십 + 모친 신탁)의 합산으로 명시. Stage 3 EP2 blueprint는 이를 **단일 출처** ("조부 명의 HMC투자증권 신탁")로 축소하여 provenance error 발생.

2. **Capital amount**: Arc 1/Arc 2 모두 **"20억"**을 canonical figure로 유지. Stage 3가 EP3에서 3.5% 신탁 해지 수수료를 도입하여 "19.3억"으로 변환했으나, 이 차감은 **arc에 없는 Stage 3 발명**. Arc 2는 시작 자본을 "20억원, 현금 100%"로 명시.

3. **WTI 진입 시점**: Arc 1 EP5는 WTI 진입 **"준비 완료"** (마우스 위에 손, 미클릭). Arc 2는 EP7에서 **15억 3배 레버리지** 체결. Stage 3 EP5 blueprint는 **"전액 투입 매수 체결 완료"**로 변환 — arc 경계를 넘어 Arc 2 이벤트를 Arc 1에서 조기 실행.

4. **투입 금액**: Arc 2는 **15억** (잔여 5억 예비금). Stage 3 EP5 blueprint는 **전액** (~198만$). 금액과 전략이 모두 다름.

---

## 2. Included Coverage / Exclusions

### Included

- Arc 1 전체: `beat_sequence`, `episode_details`, `tactical_doc` (EP1-5), `joint_docs`, `state_constraints`, `state_changes`, `status_shadow`
- Arc 2 전체: `beat_sequence`, `episode_details`, `tactical_doc` (EP6-10), `joint_docs`, `state_constraints`, `state_changes`, `status_shadow`, `investment_calc`
- Arc 1 → Arc 2 경계의 capital/inventory/location 연속성
- Stage 3 EP2/EP5/EP6 blueprint와의 cross-reference (provenance, capital, WTI entry)

### Excluded

- Stage 3 orchestrator code path (T4/T5 lane 범위)
- Stage 4 writer/validator behavior (T6/T7/T8 lane 범위)
- Stage 2 validation guardrails (T3 lane 범위)
- Execution SSOT, temp queue, merge audit 생성

---

## 3. Key Evidence

### 3-A. Provenance: Arc 1은 3-출처 합산

Arc 1에서 20억의 출처는 **세 가지 자산의 합산**이다:

| Source | Arc 1 Field | Line | Text |
|--------|-------------|------|------|
| `beat_sequence` | EP3 | L94 | "**조부의 유산**, 승마 스폰서십, **모친 명의 신탁 자산** 등 흩어진 개인 자산을 긁어모아 20억 원" |
| `status_shadow.item_consumption` | — | L234-236 | ["**조부의 현금성 유산**", "승마 스폰서십 누적 수익", "**모친 명의 신탁 자산**"] |
| `tactical_doc` EP3 | — | L240 | "**할아버지가** 어릴 적부터 쥐여준 용돈을 모은 계좌, 승마 국가대표 시절 스폰서십으로 받은 누적 수익, 그리고 **어머니가 몰래 신탁해 둔 자산**의 일부까지 전부 해지" |

**Arc truth**: 조부 자산 ≠ 모친 신탁. 별개 항목. 모친이 신탁을 설정한 당사자.

**Stage 3 EP2 blueprint deviation**:
- File: `stage3/ep_0002/.../final_blueprint__dialogue_focused.json` **L60**
- Text: "초기 자본금 20억 원 마련을 위해 **조부 명의의** HMC투자증권 **신탁** 계좌 해지 목표 설정"
- Stage 3가 "모친 명의 신탁"을 "조부 명의 신탁"으로 축소/변환. 3-출처 구조도 단일-출처로 축소.

### 3-B. Capital Amount: Arc canonical figure = 20억

| Artifact | Field | Line | Figure |
|----------|-------|------|--------|
| Arc 1 `joint_docs` | `physical_inventory` | L142 | "**20억 원이 찍힌** 법인 통장" |
| Arc 1 `tactical_doc` EP3 | 종료 | L240 | "통장에는 정확히 **20억 원**이라는 숫자가 찍힌다" |
| Arc 1 `tactical_doc` EP4 | 본문 | L240 | "자본금 **20억 원**을 법인 계좌로 이체" |
| Arc 1 `tactical_doc` EP5 | 소지품 | L240 | "**20억 원이 찍힌** 법인 통장" |
| Arc 1 `status_shadow` | `key_stat_change` | L238 | "가용 자본: 0원 -> **20억 원**" |
| Arc 2 `state_constraints` | `arc_start_state.capital` | L241 | "**20억원**" |
| Arc 2 `state_constraints` | `arc_start_state.total_assets` | L246 | "**20억원**" |
| Arc 2 `state_constraints` | `arc_start_state.portfolio_position` | L245 | "**현금 100%**" |
| Arc 2 `tactical_doc` EP6 | 소지품 | L314 | "**20억 원이 찍힌** 법인 통장" |
| Arc 2 `status_shadow` | `key_stat_change` | L312 | "가용 현금 **20억 원** 중 15억 원 증거금 구속" |

Arc 1/Arc 2 어디에도 3.5% 수수료, 19.3억, 18.8억 같은 차감 후 금액이 없다.

**Stage 3 deviation**: EP3 blueprint가 "3.5% 중도해지 수수료 → 19.3억"을 도입. 이는 서사적 리얼리즘 강화이나, **arc와 미합의된 Stage 3 발명**. 이후 EP5/EP6 blueprint가 모두 "19.3억"을 base figure로 사용하면서 arc의 "20억"과 영구 괴리 발생.

### 3-C. WTI 진입 시점: Arc 1 EP5는 준비만, Arc 2 EP7이 실행

**Arc 1 EP5 ending**:
- File: `arc_001/.../final_arc__conservative.json` **L240** (tactical_doc EP5)
- Text: "법인 계좌에 예치된 20억 원. 그는 3배 레버리지를 적용해 총 60억 원 규모의 포지션을 운용할 **계획을 세운다**. ... 마우스 위에 손을 얹은 한시우의 눈빛이 매섭게 빛난다."
- EP5 종료 소지품: "**20억 원이 찍힌 법인 통장**" → 자금이 계좌에 그대로 있음
- `beat_sequence` L96: "WTI 원유 롱 포지션 **진입 준비 완료**" (준비, not 실행)

**Arc 2 EP7 execution**:
- File: `arc_002/.../final_arc__balanced.json` **L93**
- `beat_sequence`: "한미증권 VIP룸에서 박성호 PB의 만류를 뚫고 **15억 원어치 3배 레버리지 매수 주문 강행**"
- `investment_calc` L275: `ep_no: 7` — 체결 에피소드 = EP7
- `tactical_doc` EP7 L314: "**3배 레버리지. WTI 6월물. 15억 넣어.** 단호하고 건조한 명령."

**Stage 3 EP5 blueprint deviation**:
- File: `stage3/ep_0005/.../final_blueprint__emotion_focused.json`
- L26: `expected_ending` = "WTI 롱 포지션 **매수 체결 완료** 및 내면의 두려움 극복"
- L27: "약 198만 달러의 자본이 WTI 롱 포지션에 **쏟아져 들어간다**"

Stage 3가 Arc 1의 "준비 완료" 엔딩을 "매수 체결 완료"로 변환. Arc 2 EP7의 이벤트(15억 매수 체결)를 Arc 1 EP5에서 조기 실행하되 금액(전액)과 채널(자체 HTS vs 한미증권 PB)까지 변경.

### 3-D. 투입 금액: Arc 2 = 15억 (예비금 5억), Stage 3 EP5 = 전액

| Source | Amount | Reserve | Channel |
|--------|--------|---------|---------|
| Arc 2 `investment_calc` L278 | `principal: 1500000000` (15억) | 5억 | 한미증권 박성호 PB |
| Arc 2 `status_shadow` L312 | "15억 원 증거금 구속, **예비금 5억 원**" | 5억 | — |
| Arc 2 `arc_end_state` L227 | `capital: "5억원"` | 5억 | — |
| Stage 3 EP5 blueprint L27 | "약 198만 달러의 자본이 ... **쏟아져 들어간다**" (전액) | 0 | 자체 HTS |
| Stage 3 EP5 blueprint L33 | equipment: "약 198만 달러가 예치된 파생상품 계좌" | 0 | — |

Arc 2는 20억 중 15억만 투입하고 5억을 예비금으로 유지하는 명확한 자금 설계를 가지고 있다. Stage 3 EP5 blueprint는 이를 "전액 투입"으로 변환하여 예비금 개념 자체를 소멸시켰다.

### 3-E. Arc 1 내부 약한 모호성 1건

`episode_details` EP3 L117: "**조부 유산** 및 **신탁 자산** 해지하여 20억 원 시드머니 확보"

이 표현은 "조부 유산 + 신탁 자산"으로 읽히며, 신탁의 소유자를 명시하지 않는다. `tactical_doc`과 `status_shadow`는 명확히 "모친 명의 신탁"이라고 하지만, `episode_details`의 축약 표현이 Stage 3에 모호한 입력을 제공했을 가능성이 있다.

그러나 `tactical_doc`이 `episode_details`보다 상세하고 권위 있는 필드이므로, "모친 명의"가 arc truth이다.

---

## 4. Findings Ranked

### F-1. CRITICAL: Stage 3가 Arc 2 EP7 이벤트를 Arc 1 EP5에서 조기 실행

- Arc 1 EP5 = "준비 완료" (마우스 위 손, 미클릭, 계좌 20억 유지)
- Arc 2 EP7 = "15억 3배 레버리지 매수 체결" (한미증권 박성호 경유)
- Stage 3 EP5 blueprint = "전액 투입 매수 체결 완료" (자체 HTS, 19.3억 전액)
- **결과**: EP5에서 이미 전액 투입되었으므로, EP6/EP7에서 한미증권 15억 투입 서사가 arc truth와도 blueprint truth와도 모순

### F-2. CRITICAL: 자금 규모 불일치 (20억 vs 19.3억 vs 15억)

| Stage | Canonical Capital | WTI 투입 | 예비금 |
|-------|-------------------|---------|--------|
| Arc 1/2 | **20억** | **15억** (EP7) | **5억** |
| Stage 3 EP3 | **19.3억** (수수료 차감) | — | — |
| Stage 3 EP5 | **19.3억** | **전액** (~198만$) | **0** |
| Stage 3 EP6 | **19.3억** (계좌 잔존) | **15억** (계획) | — |

Stage 3가 arc의 20억을 19.3억으로, arc의 15억 부분투입을 전액투입으로 각각 변환. 두 변환 모두 arc truth에 없는 Stage 3 발명.

### F-3. HIGH: Provenance 축소 (3-출처 → 단일 출처)

- Arc truth: 20억 = 조부 현금유산 + 승마 스폰서십 + 모친 명의 신탁
- Stage 3 EP2 blueprint: 20억 = 조부 명의 HMC투자증권 신탁 (단일)
- 모친 소유 신탁을 조부 소유로 귀속 변환
- EP2 rejected manuscripts 3건의 직접 원인

### F-4. MODERATE: Arc 1 `episode_details` L117의 약한 모호성

- "조부 유산 및 신탁 자산"이라는 축약 표현이 신탁 소유자를 명시하지 않음
- Stage 3가 이 축약 표현만 읽고 `tactical_doc`의 상세 내용을 무시했을 가능성
- 그러나 이는 **arc 결함**이라기보다 **입력 필드 우선순위 문제**

---

## 5. Cleared Non-Culprits

### 5-1. Arc 1↔Arc 2 internal consistency — CLEARED

Arc 2 `arc_start_state` (L240-247)는 Arc 1 `joint_docs` (L140-143)와 정확히 일치:
- 위치: "서울 여의도, SW인베스트먼트 소형 오피스"
- 자본: "20억원"
- 포지션: "현금 100%"
- 장비: Arc 1 종료 장비 (인감, OTP, 통장) 이월
- Arc 2 `constraint_summary` L98: Arc 1 획득 아이템 재획득 금지 규칙 명시

Cross-arc 연속성은 Stage 2 수준에서 정상 작동.

### 5-2. Arc 2 `investment_calc` internal arithmetic — CLEARED

- 15억 × 3배 = 45억 규모 포지션
- Entry $60 → Exit $65 = 8.33% 상승
- 8.33% × 3배 레버리지 = 25% 수익
- 15억 × 25% = 3.75억 수익
- 최종: 현금 5억 + WTI 18.75억 = 23.75억

`investment_calc` L268-279와 `arc_end_state` L227-238이 정확히 일치.

### 5-3. Stage 2 episode-count / density — CLEARED

Arc 1 = 5화, Arc 2 = 5화. 할당 정상. 밀도 불균형 증거 없음.

---

## 6. Residual Culprit Candidate

**Stage 2는 직접적 culprit가 아니다.** Arc artifact 자체는 내부적으로 일관된다.

그러나 Stage 2는 **간접적 amplifier**로 작용한다:
- `episode_details` L117의 축약 표현이 provenance 모호성을 제공
- Arc 1 EP5 tactical_doc의 "계획을 세운다"가 Stage 3에 의해 "체결 완료"로 재해석될 여지를 남김
- Arc 1/Arc 2 사이에 **fee adjustment** (3.5% 등)에 대한 사전 합의가 없어, Stage 3가 독자적으로 수수료를 도입할 여유가 발생

**진짜 culprit**: Stage 3 blueprint generation이 arc truth를 소비할 때:
1. `episode_details` 축약 표현을 `tactical_doc` 상세 내용보다 우선 소비한 것으로 추정
2. Arc 1 EP5의 "준비 완료" ending을 "매수 체결 완료"로 scope 확장
3. Arc 2의 15억 부분투입/5억 예비금 설계를 무시하고 전액투입으로 변환
4. 3.5% 수수료를 독자 도입하여 arc의 20억 canonical figure와 영구 괴리 생성

이 4가지는 모두 **Stage 3의 arc-truth 소비 방식** 문제이며, Stage 2 arc artifact 자체의 결함은 아니다.

---

## 7. Next-Scope Recommendation

### 이 lane 단독으로 권장하는 것

1. **T4 (Stage3 Blueprint Authority) lane과 교차 확인**: Stage 3 orchestrator가 arc artifact의 어떤 필드를 실제로 읽는지 (`episode_details` vs `tactical_doc` vs `state_constraints`) code-level 확인. 이것이 F-1~F-3의 root cause를 90%→100% 증명할 수 있다.

2. **Arc 1 `episode_details` EP3 L117의 모호성 평가**: 이 축약 표현이 Stage 3에 잘못된 provenance를 주입한 경로였는지 확인. 만약 Stage 3가 `episode_details`만 읽고 `tactical_doc`을 읽지 않는다면, 이것이 provenance error의 직접 원인.

### 이 lane 단독으로 권장하지 않는 것

- Arc artifact 수정 (arc 자체는 내부 일관)
- Execution SSOT 작성 (이 lane만으로는 scope 불충분)
- Stage 2 validation guardrails 추가 (T3 lane 범위)

---

## 8. Confidence And Limits

### Confidence: 95%

모든 finding이 artifact body의 직접 인용과 line number에 기반한다. Arc 1/Arc 2 전문을 읽고 cross-reference하여 추정이 아닌 사실 기반 판정.

### 확신 근거:

- Arc 1/Arc 2 전문 직접 읽기 완료 (각 240/314행)
- Stage 3 EP2/EP5/EP6 blueprint와의 교차 대조 완료
- Capital figure 20억이 Arc 1/Arc 2에서 10회 이상 일관 반복 확인
- Provenance 3-출처 구조가 3개 독립 필드 (`beat_sequence`, `tactical_doc`, `status_shadow`)에서 동일 확인
- Arc 2 `investment_calc` arithmetic 정합 확인

### 제한:

- Stage 3 orchestrator가 실제로 arc artifact의 **어떤 필드**를 입력으로 사용하는지 code-level 미확인 (이 lane scope 외)
- EP4 blueprint/manuscript 미검사 (EP4는 troubled episode가 아니므로 10-terminal order scope 외)
- Arc 1의 `episode_details` L117 축약 표현이 Stage 3에 **실제로** 잘못된 provenance를 주입한 경로인지는 code path 확인 필요 (T4 lane 교차 확인 필요)

---

## 3-Pass Audit Record

- **Pass 1 (Structure)**: lane survey report 형식, 8개 필수 섹션 존재, execution SSOT/temp queue/merge audit 미생성 확인
- **Pass 2 (Evidence)**: 모든 인용에 file/line anchor 부착, arc_001 L94/L142/L234-236/L240 and arc_002 L241/L245/L246/L278/L312/L314 직접 대조 완료, Stage 3 cross-reference L60/L26/L27/L32/L51 확인 완료
- **Pass 3 (Readability)**: findings-first 구조, mandatory final lines 존재, next-scope가 이 lane의 범위 내로 한정됨

---

## Mandatory Final Lines

- **Can this lane explain a real residual failure by itself**: no — Stage 2 arc artifact 자체는 내부 일관. 실패의 직접 원인은 Stage 3의 arc-truth 소비 방식.
- **Does this lane explain repeated rescue rounds after the closed waves**: no — arc가 아닌 Stage 3 blueprint가 rescue round를 유발. 단, arc의 `episode_details` 모호성이 간접 기여 가능.
- **Would this lane justify a bounded next execution wave**: no — arc artifact 수정 불필요. Stage 3의 arc-truth 소비 로직 (T4 lane)이 execution 대상.
