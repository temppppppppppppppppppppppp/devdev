# chaebol_allowance_zero 4축 종합 감사 보고서

**작성일:** 2026-03-24
**대상 산출물:**
- `treatments/chaebol_allowance_zero_phase0_design.json`
- `treatments/chaebol_allowance_zero_tr_block_070_draft.json` (70블록, ~551KB)
- `bible/chaebol_allowance_zero_bi.json` (70블록, ~598KB)
- `treatments/preprocess/chaebol_allowance_zero/` (전처리 산출물 일체)

---

## 1. 시스템 적합성 평가 (글도비 규격 vs 실물)

### 1.1 라우팅 판정

| 항목 | 기준 | 판정 |
|------|------|------|
| 패밀리 | cashflow/B2B 장악 → `blockguide` | PASS |
| 장르 프로파일 | `business_growth_profile` + `office_power_profile` | PASS (bi-production-harness 6.5절에 명시 앵커) |
| 현재 스테이지 | `phase0_design` 존재 + `tr_block_070_draft` 존재 + `0_bi` 존재 → BI 완료 대기 | PASS |

### 1.2 전처리(Stage 0) 산출물 4종

| 산출물 | 존재 | 판정 |
|--------|------|------|
| `source_manifest.json` | O | PASS |
| `profile_lock.json` | O | PASS |
| `material_bundle_summary.json` | O | PASS |
| `phase0_ready_snapshot.json` | O (`manual_audit_pass: true`) | PASS |

### 1.3 Phase 0 최소 필수 시트

| 시트 | 존재 | 수량 | 판정 |
|------|------|------|------|
| `arcs` | O | 7개 아크 | PASS |
| `npc_timeline` | O | 10명 | PASS |
| `foreshadow_map` | O | 6개 복선 | PASS |
| `opponent_transition_plan` | O | 3단계 (초기/중기/최종) | PASS |
| `defeat_blocks` / `quiet_blocks` | O | 아크별 명시 | PASS |

### 1.4 TR 블록 규격

| 항목 | 기준 | 실물 | 판정 |
|------|------|------|------|
| 블록 수 | 70 | 70 | PASS |
| 블록 스키마 | content/stakes/power_shift/genre_ext/regression_ext 등 | 전 블록 충족 | PASS |
| candidate → fixed → draft 상태 머신 | 전처리 `03_tr_blocks/` 내 블록별 candidate + fixed 존재 | Block 001~070 모두 존재 | PASS |
| UTF-8 인코딩 | UTF-8 only | PASS (5-Pass 감리 PASS 1 확인 완료) |

### 1.5 BI 5-Pass 감리 결과 (기존 `bible/audit_reports/chaebol_allowance_zero_bi_5pass.md`)

| Pass | 항목 | 결과 |
|------|------|------|
| PASS 1 | 인코딩/파싱 | OK |
| PASS 2 | 최소 스키마 (`plot_roadmap` 70개) | OK |
| PASS 3 | 내부 정합성 (주인공/제목/자본 동기화) | OK |
| PASS 4 | TR↔BI 동기화 (타이틀 시퀀스/해시 일치) | OK |
| PASS 5 | 품질 감리 (이물질/NPC명 일관성) | OK |

### 1.6 시스템 적합성 종합

**등급: PASS (구조적 적합)**

전처리 4종, Phase 0 4대 시트, TR 70블록, BI 70블록, 5-Pass 감리 전량 통과.
글도비 시스템이 요구하는 **형식적·구조적 규격은 완전 충족**.

단, 아래 2~4축에서 드러나는 **내용적 품질 문제**는 시스템 규격 밖의 영역이므로 별도 판정한다.

---

## 2. 서사 정합성 평가 (앞뒤가 맞는가)

### 2.1 잘 작동하는 부분

- **자본 연속성**: 전 블록 `capital_before == 직전 블록 capital_after` 일관 유지
- **복선-회수 원환**: Block 1 유언장 등본 → Block 63 유언장 7항 뒷면 회수, Block 3 VIP 번호표 → Block 12 유령업체 장부 대조, Block 5 셔틀 회차표 → Block 46 정산 원본 등 핵심 복선 6개 전량 회수
- **아크 전환**: 사업 영역(장례→호텔→공장→병원→정산→전국→가문)이 논리적으로 확장
- **relationship_delta 캐리오버**: Block N의 `after`가 Block N+1의 `before`와 일치 (Batch 001 3-Pass에서 확인)

### 2.2 발견된 정합성 문제

| # | 심각도 | 내용 |
|---|--------|------|
| C-01 | **Critical** | **회귀 시점(2006) vs 스토리 시작(2018.4)**: 12년 공백 미설명. protagonist_config에 2006년 회귀라고 명시되어 있으나 Block 1은 2018년 4월. 이 12년간 주인공이 무엇을 했는지 일체 서술 없음 |
| C-02 | **Major** | **Block 13 적대자 불일치**: 미니바 냉장고 블록의 opponent가 "김태석(주차장 야간반장)". 직무 영역이 맞지 않음 |
| C-03 | **Major** | **Block 30→31 시간 공백 9개월** (2019.4→2020.1): 자본 변동 없이(74→74억) 9개월이 넘어감. 이 기간의 사업 활동 미기술 |
| C-04 | **Major** | **HistoricalEvents 15개만 기록**: Block 1~15에 대응하는 사건만 있고 Block 16~70은 누락 |
| C-05 | **Moderate** | **regression_hint 70회 반복 의심**: 매 블록마다 "재이의 정보 출처를 의심한다"인데 한 번도 실질적 후속 조치 없음. 70번 의심만 하고 아무도 행동하지 않는 것은 비현실적 |
| C-06 | **Moderate** | **FinanceHUD 미갱신**: `total_assets`, `liquid_cash` 등 "초기 설정 필요" 상태. 70블록 경과 후에도 업데이트 없음 |
| C-07 | **Moderate** | **Seeds echo_count/harvested_ep 전량 0/null**: 실제 회수된 복선도 상태값 미갱신 |
| C-08 | **Minor** | **KarmaMatrix 비어 있음**: 70블록 관계 변화 요약 누락 |

### 2.3 서사 정합성 종합

**등급: CONDITIONAL PASS (조건부 통과)**

핵심 플롯 라인(자본 성장, 아크 전환, 복선-회수)은 정합하나, C-01(회귀 시점 공백)과 C-02(적대자 불일치)는 원고 생산 전 반드시 해소 필요. C-05(반복 의심)는 서사적 긴장감을 훼손하므로 중기적 보완 권장.

---

## 3. TR-BI 정합성 평가

### 3.1 기계적 정합성 (5-Pass 감리 기통과)

| 항목 | 판정 | 근거 |
|------|------|------|
| 타이틀 시퀀스 | MATCH | 70블록 제목 전량 일치 |
| 자본 최종값 | MATCH | TR 최종 1,318억 = BI `capital_after` |
| 주인공명 | MATCH | 윤재이 3개 위치 일치 |
| plot_roadmap 해시 | MATCH | TR과 BI의 roadmap 해시 동일 |

### 3.2 의미적 정합성

| 항목 | 판정 | 상세 |
|------|------|------|
| phase0 아크 자본 목표 vs TR 실현값 | **NEAR MISS** | phase0은 ARC-01 목표 12억, TR 실현값 10억. phase0은 ARC-02 목표 38억, TR 실현값 36억. 전체적으로 phase0 대비 TR이 약 5~10% 낮음. 심각하지는 않으나 불일치 존재 |
| phase0 NPC 타임라인 vs TR 등장 블록 | **MATCH** | phase0에 명시된 `first_block`과 TR 실제 등장 일치 |
| phase0 복선 `payoff_block` vs TR 실제 회수 | **MATCH** | 6개 복선 전량 명시된 블록에서 회수 |
| BI `WorldState.CurrentEra` vs TR 최종 시점 | **MATCH** | 둘 다 2022년 10월 |
| BI `FinanceHUD` vs TR 최종 자본 | **MISMATCH** | BI FinanceHUD가 "초기 설정 필요" 상태. TR의 1,318억과 동기화 안 됨 |

### 3.3 TR-BI 정합성 종합

**등급: PASS (기계적) / CONDITIONAL (의미적)**

5-Pass 감리 기준 완전 통과. 다만 FinanceHUD 미갱신과 phase0 대비 자본 목표 소폭 불일치가 남아 있음.

---

## 4. 전체적 평가: 루즈함 + 거물/아이템 밀도

### 4.1 가장 심각한 문제: Block 7~70 템플릿 반복

이 작품의 **핵심 품질 이슈**는 Block 1~6과 Block 7~70의 극단적 품질 격차다.

**Block 1~6 (수작업 고밀도)**:
- 블록당 평균 850자 이상 (context/event_villain/solution/reward 합산)
- 적대자 3명 고유 진행 (노현주→최병태→서도윤)
- 솔루션이 블록마다 전술적으로 차별화
- 복선/콜백이 정밀 교차 참조

**Block 7~70 (템플릿 자동 생성)**:
- event_villain 문장 구조 64개 블록 동일: `"[인물]은 [직위] 위치에서 이번 '[블록명]'를 가볍게 본다…"`
- solution 문장 64개 블록 동일: `"그는 먼저 [전생 기억]을 떠올리며 병목이 터질 순서를 다시 계산한다…"`
- relationship_delta `"같이 붙어도 돈이 되는 운영 파트너"` 동일 문장 30회 반복
- stakes/power_shift도 변수만 바꾼 Mad Libs 수준

### 4.2 루즈한 구간

| 구간 | tension_level | 사유 |
|------|---------------|------|
| Block 14~15 | 4~5 | 주차장 야간반 + 불 꺼진 연회장. 긴장감 최저 |
| Block 18 | 4 | "카드키보다 영수증". 사건 규모 소 |
| Block 24 | 5 | "기숙사 복도등". emotional beat "stability" |
| Block 28 | 4 | "하루 세 번 발주". emotional beat "control" |
| Block 30→31 사이 | - | 9개월 시간 점프. 서사 없음 |

### 4.3 거물/아이템 밀도 부족

**역사적 이벤트:**
- 70블록 중 **단 2건**만 역사적 이벤트 활용 (Block 2: 2018 외식업 인력난, Block 31: 코로나19)
- 2018~2022년은 미중 무역전쟁, 반도체 수급, 부동산 규제, 금리 변동, 가상화폐 등 재벌/투자물에서 활용 가능한 실제 이벤트가 풍부한 시기
- **68/70 블록의 historical_event가 null** → 심각한 밀도 부족

**적대자(거물) 밀도:**
- Block 1~6: 매 블록 고유 적대자 (밀도 최고)
- Block 7 이후: 2~3명이 아크 내 순환. 외부 거물(은행장, 정치인, 경쟁 재벌, 외국 자본 등)이 거의 등장하지 않음
- **서도윤/노현주/윤석진 3인 외 외부 거물 전무** → 후반부로 갈수록 자본은 1,000억대인데 상대하는 적대자가 "지역 사장", "회계지원센터장" 수준

**아이템:**
- KeyItems 2개뿐 (경영 대시보드, 핵심 네트워크 맵). 둘 다 추상적
- 투자물의 킬 아이템(내부 문서, 비밀 계약서, 증거자료, 특허, 인허가 등)이 구체적으로 등장하지 않음
- special_ability가 전 블록 `has_ability: false`

**패배 블록의 기계적 배치:**
- 정확히 각 아크의 5번째 블록에서 패배 발생 (Block 5, 15, 25, 35, 45, 55, 65)
- 손실 규모도 자본 규모에 비례한 등비급수: -1, -1, -1, -4, -2, -3, -6, -10, -16억
- 현실적 서사 리듬이 아닌 기계적 분할

**자본 성장의 등비급수 문제:**
- ARC별 약 2배 성장(10→36→74→152→318→668→1,318억)
- 깔끔한 등비급수 → 서사적 우연치고 너무 기계적

### 4.4 문법/표기 오류 (반복 전파)

- "반장**로서**" → "반장**으로서**" (자동 생성 템플릿 오류가 64블록에 전파)
- "양수**을**" → "양수**를**"
- 기타 조사 오류 다수

---

## 종합 판정

| 축 | 등급 | 요약 |
|----|------|------|
| **1. 시스템 적합성** | **PASS** | 전처리 4종, Phase 0 4대 시트, TR 70블록, BI 70블록, 5-Pass 전량 통과. 형식적 규격 완전 충족 |
| **2. 서사 정합성** | **CONDITIONAL PASS** | 자본/복선/아크 전환은 정합. 회귀 시점 12년 공백(C-01), Block 13 적대자 불일치(C-02), 9개월 시간 점프(C-03)는 해소 필요 |
| **3. TR-BI 정합성** | **PASS / CONDITIONAL** | 기계적 5-Pass 통과. FinanceHUD 미갱신, phase0 대비 자본 목표 소폭 불일치 잔존 |
| **4. 밀도/루즈함** | **FAIL** | Block 7~70 (전체의 91%)이 템플릿 자동 생성 수준. 거물 밀도 심각 부족. 역사적 이벤트 68/70 null. 패배/성장 곡선 기계적. 실질적 원고 생산에 바로 사용하기 어려운 상태 |

---

## 권고 사항

### 즉시 조치 (원고 생산 전 필수)

1. **C-01 회귀 시점 정합**: 2006년 회귀 → 2018년 스토리 시작 사이 12년 공백에 대한 설정 보완 (protagonist_config 수정 또는 프롤로그 설계)
2. **C-02 Block 13 적대자 교체**: 주차장 야간반장 → 미니바/하우스키핑 관련 적대자로 수정
3. **FinanceHUD 동기화**: TR 최종 자본 1,318억으로 BI FinanceHUD 갱신

### 중기 조치 (품질 도약을 위해 강력 권장)

4. **Block 7~70 재작성**: Block 1~6 수준의 구체성으로 최소 핵심 필드(event_villain/solution/stakes) 개별 재작성. 현재 상태는 "플롯 스켈레톤"이지 "트리트먼트"가 아님
5. **외부 거물 투입**: 후반부(ARC-05~07, 자본 150억+)에 은행장/경쟁 재벌/외국 자본/정치인 등 외부 거물 최소 3~5명 추가
6. **역사적 이벤트 활용**: 2018~2022년 실제 경제 이벤트(미중 무역전쟁, 반도체 수급, 코로나 2~3차 파도, 금리 변동, NFT/가상화폐 등)를 최소 ARC당 1~2건 배치
7. **패배 블록 리듬 재설계**: 기계적 "아크 5번째 블록 = 패배"를 예측 불가능한 리듬으로 변경
8. **regression_hint 차별화**: 70번 반복 의심이 아닌, 실질적 위기 에스컬레이션 설계

### 하위 조치

9. Seeds echo_count / harvested_ep 갱신
10. KarmaMatrix 채움
11. HistoricalEvents Block 16~70 보완
12. 문법 오류("반장로서" 등) 템플릿 수준 일괄 수정
