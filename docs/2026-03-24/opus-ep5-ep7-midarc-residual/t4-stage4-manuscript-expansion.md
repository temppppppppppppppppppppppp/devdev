# T4: Stage4 Manuscript Expansion — EP5-EP7 Mid-Arc Residual Survey

Date: 2026-03-24
Status: final (3-pass audited)
Lane: T4 — Stage4 Manuscript Expansion
Master Order: `docs/2026-03-24/ep5-ep7-midarc-residual-6terminal-master-order.md`
Evidence Path: `docs/2026-03-24/opus-ep5-ep7-midarc-residual/t4-stage4-manuscript-expansion-evidence.md`

## 1. Artifact Inventory

| Episode | Attempts | Files per Attempt | Final Verdict | Rounds to PASS |
|---------|----------|-------------------|---------------|----------------|
| EP5 | 3 | 2 each (6 total) | PASS (score 95) | 3 |
| EP6 | 3 | 2 each (6 total) | PASS (score 90) | 2 |
| EP7 | 1 | 2 (selected_before_fix + patched_after_fix) | PASS (score 96) | 3 |

All artifact files confirmed present under `projects/0324_00_/logs/artifacts/stage4/ep_000{5,6,7}/`.

## 2. EP5 — What Stage 4 Adds Beyond the Blueprint

### Blueprint Authority (Stage 3)

- 5 scenes: 먼지와 캐시미어 → 2006년의 인터페이스 → 오만한 방관자 → 트리거: 이란 핵 위기 → 첫 번째 사냥
- Capital: 1,930,000,000원 → 환전 970원 → ~198만 달러 → WTI 480계약 $60.20
- Location: 여의도 SW인베스트먼트 사무실 + 강남 요정 (씬3)
- NPC: 한태준 (큰형), 비서실장
- **Blueprint does NOT mention 한미증권 or 박성호 for EP5** — the rescue-round rejection came from post-select continuity checks referencing EP3's established 박성호 affiliation

### Stage 4 Expansion Characterization

| Dimension | Blueprint Content | Stage 4 Manuscript Content | Classification |
|-----------|------------------|--------------------------|----------------|
| Scene structure | 5 scenes, titles, flow | Faithful reproduction of all 5 scenes | `faithful expansion` |
| Capital amount | 1,930,000,000원, ~198만 달러 | **1,900,000,000원, $1,958,762.88 (~195만 달러)** | `artifact-truth mismatch` |
| 한태준 호칭 | not specified | Attempt 1: "부사장님" / Attempt 3: "이사님" | `Stage 4 invention` |
| WTI entry price | $60.20 | $60.20 — consistent | `faithful expansion` |
| 환전 환율 | 970원 | 970원 — consistent | `faithful expansion` |
| 트라우마 묘사 | "파산의 공포가 환상통처럼" | Expanded to 2024년 원룸/차압 딱지/수백억 부채 detail | `faithful expansion` |
| 한태준 반응 | "자멸할 것이라 확신, 감시 철수" | Faithful reproduction with dialogue | `faithful expansion` |

### EP5 Rejection Analysis

| Round | Verdict | Score | Primary Rejection Reason | Source |
|-------|---------|-------|--------------------------|--------|
| R1 | PASS_WITH_FIX → REJECT (downgrade) | 92 | post-select continuity: 박성호 NPC 소속 (한미증권 vs 시중은행 from EP3) | **Stage 3 blueprint NPC truth error** |
| R2 | REJECT | 78 | "EP3에서 이미 기선 제압당한 박성호 태도가 '호구로 얕봄'으로 리셋됨" | **Stage 3 blueprint relationship-state error** |
| R3 | PASS | 95 | ASP red-team correction + PB attitude/product corrections | — |

**EP5 conclusion**: Stage 4 faithfully expanded the blueprint. The rescue rounds were caused by **blueprint errors** (NPC 소속, NPC 관계 상태) not by Stage 4 invention. The capital drift (19억 vs 19.3억) is also a blueprint/expansion inconsistency but was not the rejection trigger.

## 3. EP6 — What Stage 4 Adds Beyond the Blueprint

### Blueprint Authority (Stage 3)

- 5 scenes: 모니터 앞의 설계자 → 사냥개의 조건 → 호구의 등장 → 탐욕의 브리핑 → 판을 엎는 한마디
- Capital: 19억 3천만 원
- Location: starts 여의도 SW인베스트먼트, moves to **한미증권 본사** (blueprint error)
- NPC: 박성호 (한미증권 VVIP 전담 PB — wrong affiliation)
- Ending: cliffhanger at "내가 살 건..."

### Stage 4 Expansion Characterization

| Dimension | Blueprint Content | Stage 4 Manuscript Content | Classification |
|-----------|------------------|--------------------------|----------------|
| Scene structure | 5 scenes, cliffhanger ending | Faithful reproduction | `faithful expansion` |
| 장소 | "한미증권 본사 2층 VVIP 라운지" | Attempt 1/2: 한미증권 (faithfully wrong). Attempt 3: 시중은행 본점 (corrected) | `faithful expansion of already-wrong blueprint` → `Stage 4 self-correction on R2` |
| 박성호 직함 | "한미증권 VVIP 전담 PB" | Attempt 1/2: 한미증권. Attempt 3: 시중은행 PB | `faithful expansion of already-wrong blueprint` |
| 재무 디테일 | "태형건설 PF ABCP, 할인율 8%" mentioned in scenario | Fully expanded: 연체율 14%, 브릿지론 2차 거절, 메자닌 위험 | `faithful expansion` |
| 산술 | Blueprint doesn't specify post-trade balance | Attempt 1: 잔고 5억 (error). Attempt 3: 잔고 4억 7천만 (correct) | `Stage 4 invention` (R1 error) / `corrected on R2` |
| 패텍필립/로로피아나 | Blueprint mentions as disguise items | Faithful detail expansion | `faithful expansion` |

### EP6 Rejection Analysis

| Round | Verdict | Score | Primary Rejection Reason | Source |
|-------|---------|-------|--------------------------|--------|
| R1 | REJECT | 75 | "직전 화와의 장소 연속성 단절 (시중은행 -> 한미증권)" + 산술 오류 | **Stage 3 blueprint 장소 오류** + minor Stage 4 arithmetic |
| R2 | PASS | 90 | "Blueprint에 잘못 기재된 장소(한미증권)를 무시하고 연속성을 지킨 점이 매우 훌륭" | — |

**EP6 conclusion**: The single rescue round was caused primarily by the **Stage 3 blueprint's wrong location** (한미증권). Stage 4 faithfully reproduced the wrong blueprint in R1, then self-corrected by overriding the blueprint in R2. A minor Stage 4 arithmetic error (5억 vs 4.7억) was a secondary factor.

## 4. EP7 — What Stage 4 Adds Beyond the Blueprint

### Blueprint Authority (Stage 3)

- 5 scenes: 허울뿐인 브리핑의 종말 → 사냥개의 착각과 균열 → 진짜 목적, WTI 레버리지 → 탐욕의 계산기 → 첫 번째 방아쇠와 환상통
- Capital: 15억 원 3배 레버리지 (45억 규모), 기존 19억 원 포지션 이관
- Location: **한미증권 본사 VVIP 프라이빗 룸** (blueprint error — same as EP6)
- Ending: 매수 체결 확인서 + 전생 환상통

### Stage 4 Expansion Characterization

| Dimension | Blueprint Content | Stage 4 Manuscript Content | Classification |
|-----------|------------------|--------------------------|----------------|
| Scene structure | 5 scenes, emotional reveal ending | Faithful reproduction | `faithful expansion` |
| 장소 | "한미증권 VIP룸" | R1: 한미증권 (faithfully wrong). R2: 시중은행 (corrected). R3: 시중은행 (maintained) | `faithful expansion of already-wrong blueprint` → `corrected` |
| 시점 (POV) | Blueprint doesn't specify (implicit 3인칭 from work convention) | R2: **1인칭 서술 ('나는', '내')** — pure Stage 4 error | `Stage 4 invention` |
| 레버리지 계산 | 15억 × 3배 = 45억 거래 규모 | Faithful: "실질적인 단일 거래 규모만 45억 원" | `faithful expansion` |
| 박성호 심리 묘사 | "탐욕에 굴복" summary | Expanded to full internal monologue with KPI/보너스 calculation | `faithful expansion` |
| 환상통 | "전생의 파산 환상통이 손목을 훑고 지나갔다" | Expanded: 2024년 원룸, 수백억 부채, 피를 토하며 죽어가던 기억 | `faithful expansion` |

### EP7 Rejection Analysis

| Round | Verdict | Score | Primary Rejection Reason | Source |
|-------|---------|-------|--------------------------|--------|
| R1 | REJECT | 86 | "직전 화와의 장소 연속성 오류" — 한미증권 vs 시중은행 | **Stage 3 blueprint 장소 오류** |
| R2 | REJECT | 75 | "작품 전체 시점(3인칭) 위반" — 1인칭으로 작성 | **Stage 4 manuscript invention** |
| R3 | PASS | 96 | ASP red-team correction, all issues resolved | — |

**EP7 conclusion**: R1 was caused by the **same Stage 3 blueprint location error** as EP5/EP6. R2 was a **pure Stage 4 manuscript error** — the LLM produced 1인칭 narration instead of the work's established 3인칭. This is the only rescue round across EP5-EP7 that is a genuine Stage 4 invention with no blueprint contribution.

## 5. Cross-Episode Pattern: The "한미증권" Blueprint Poisoning

The single most impactful defect across all three episodes is:

> **Stage 3 blueprints for EP6 and EP7 contain "한미증권" as 박성호's workplace, but the live run's EP3 (and EP5's corrected final) established him at "시중은행".**

This is a **blueprint fact-lock failure**. The Stage 3 blueprint generator did not honor the NPC registry's established affiliation. This single defect caused:
- EP5 R1: post-select continuity downgrade (from PASS_WITH_FIX to REJECT)
- EP6 R1: director_primary_reject
- EP7 R1: director_primary_reject

Additionally, EP5 R2 was caused by a related blueprint error: the blueprint instructed 박성호 to treat 한시우 as a "호구" (mark), but EP3 had already established that 박성호 was intimidated by 한시우.

## 6. Stage 4 Pure Invention Errors (Not Blueprint-Driven)

| Episode | Round | Error Type | Description | Severity |
|---------|-------|------------|-------------|----------|
| EP5 | — | Capital drift | 19억 vs 19.3억 (blueprint says 19.3, manuscripts say 19) | minor, not rejection trigger |
| EP5 | — | NPC title inconsistency | 한태준: "부사장님" (R1) vs "이사님" (R3) | minor, not rejection trigger |
| EP6 | R1 | Arithmetic | 잔고 5억 (should be 4.7억 after 15억 from 19.7억) | minor secondary, corrected R2 |
| EP7 | R2 | POV violation | 1인칭 서술 instead of 3인칭 | **confirmed primary cause of R2** |

## 7. Claim Classification Summary

| Claim | Classification |
|-------|---------------|
| Blueprint 장소 오류 (한미증권 vs 시중은행) causes EP5/6/7 rescue rounds | `confirmed primary cause` |
| Blueprint NPC 관계 상태 오류 (박성호 태도 리셋) causes EP5 R2 | `confirmed primary cause` |
| Stage 4 POV violation causes EP7 R2 | `confirmed primary cause` (Stage 4 only) |
| Stage 4 capital drift (19억 vs 19.3억) | `artifact-truth mismatch` |
| Stage 4 arithmetic error (EP6 R1 잔고) | `confirmed secondary amplifier` |
| Stage 4 han_taejun title inconsistency | `artifact-truth mismatch` |
| Stage 4 invents narrative content beyond blueprint | `cleared / not primary` — expansions are faithful and expected |

## 8. Lane Answers

### Can this lane explain a real EP5-EP7 rescue round by itself: **yes** (EP7 R2 only)
- EP7 R2's POV violation (1인칭 vs 3인칭) is a pure Stage 4 manuscript error, not blueprint-driven.
- EP5 and EP6 rescue rounds are entirely explained by Stage 3 blueprint errors, not Stage 4 invention.

### Does this lane justify a bounded next execution wave: **yes, but narrow**
- The POV violation (EP7 R2) is a Stage 4-specific error but appears to be a one-off LLM output aberration, not a systemic contract failure. A patch-mode or ASP correction resolved it on the next attempt.
- The arithmetic error (EP6 잔고) suggests Stage 4 could benefit from a capital-state assertion check, but this is a validator-side improvement, not a Stage 4 code change.

### Dominant seam in this lane: **Stage 3 primary, Stage 4 secondary**
- 5 of 6 rescue rounds across EP5-EP7 trace to Stage 3 blueprint errors (wrong NPC affiliation, wrong location, wrong relationship state).
- 1 of 6 rescue rounds (EP7 R2) is a pure Stage 4 manuscript error (POV violation).
- Stage 4 is predominantly the **faithful amplifier** of blueprint errors, not the originator.

## 9. Mandatory Final Lines

- Dominant seam in this lane: **stage3**
- Can this lane explain a real rescue round by itself: **yes** (EP7 R2 only — POV violation)
- Would this lane justify a bounded next execution wave: **yes** (narrow: capital-assertion check + POV guardrail; but the primary fix target is Stage 3 blueprint fact-lock)
