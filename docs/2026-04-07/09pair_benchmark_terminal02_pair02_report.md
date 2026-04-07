# Pair 02 Benchmark Report

Date: 2026-04-07
Terminal: 02
Document Type: read-only benchmark audit report
Benchmark Spec: `material_ssot/00_governance/production-pair-benchmark-spec-v1.md`

---

## 1. Pair Identity

| Field | Value |
| --- | --- |
| pair id | `02` |
| work_id | `chaebol_allowance_zero` |
| family | `blockguide` |
| TR | `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json` |
| BI | `bible/02_bi_chaebol_allowance_zero.json` |
| TR schema | `tr.v1`, 70 blocks, ARC-01~07 complete |
| BI schema | `2.0` |
| protagonist | 윤재이 (윤성그룹 오너 3세 / 제로라인파트너스 대표) |
| genre | 현대 한국 재벌 support-system cashflow × office power 복합 장악물 |

---

## 2. P0 Hard Gates

| # | Gate | Pass/Fail | Evidence |
| --- | --- | --- | --- |
| 1 | first-block visible cider | **PASS** | Block 2: 긴급 배식 수수료 2억 + 한유림의 첫 인정. Block 3: 셔틀·주차 관제권 48시간 위임. Block 4: 꽃집 직접 라인 4개 + 단가 이상 데이터. Block 5: 셔틀 노선 3개 공동 운영권 + 배정호 파트너. 보상이 눈에 보이는 운영권·현금·파트너 형태로 block 1 내에 반복 착지한다. |
| 2 | protagonist-only proof | **PASS** | Block 2 `solution`: 전생 현장 동선 기억 + 조문객 동선표 + 냉장창고 재고 교차 → 90분 응급 배식 설계. 이 조합은 윤재이의 회귀자 생활권 지식 없이 불가능하다. `저건 쟤라서 가능했다` 성립. |
| 3 | evaluation revision | **PASS** | Block 2: 한유림이 재이의 방식을 '즉흥이 아니라 숫자에 근거한 운영 설계'로 **첫 인정** (`relationship_delta`). Block 3: 서도윤이 '작은 운영권 방치가 체면·통제력을 갉아먹는다'고 인식 전환. 유의미한 무게를 가진 인물(비서실 실무자 + 장남)의 재평가가 block 1 내에서 명시적으로 발생. |
| 4 | visible reward token | **PASS** | Block 1: 장례식장 뒷문 출입표·의전팀 연락망·민원 책임선 (entry ticket). Block 2: 급식 라인 반복매출 후보 (seat). Block 3: 셔틀·주차 48시간 관제권 (approval right). Block 5: 셔틀 노선 3개 공동 운영권 + 설비 자산 접근권 (ownership). 모두 blockguide preferred token에 해당. |
| 5 | block 1 → block 2 gate linkage | **PASS** | Block 9~10에서 세탁·청소·셔틀 월 반복매출 1.5억/월 확정 → 형 서도윤 시선 전환 → 호텔 BOH 입장권이 공식 개방. block 1에서 번 운영권이 block 2(ARC-02 호텔)의 문을 직접 연다. |
| 6 | BI/TR early conversion alignment | **PASS** | BI `cider_point`(장례식장 뒷문부터 한 칸씩 옮겨와 가문이 조건표 앞에 서는 역전감)과 `success_device`(반복 현금흐름·정산 레인·구매 코드·결재선 접근권)가 TR blocks 1~10에서 그대로 실행된다. BI의 약속이 TR 초반에서 살아 있다. |

P0 결과: **6/6 PASS — 하드게이트 전통과**

---

## 3. Active Cap Rules

| Cap Rule | Active? | Note |
| --- | --- | --- |
| no visible cider inside block 1 | no | block 2부터 운영권·현금·파트너 보상 연속 |
| rewardless pain blocks 2 in a row | no | block 6(증거 예치, quiet_setup)은 보상 공백이나 block 5·7이 모두 보상 블록이므로 연속 2블록 공백 없음 |
| no-cider drought 6+ blocks | no | 70블록 전체에 걸쳐 defeat block(4, 25, 35, 45, 55, 65)이 산재하나, 각 defeat block 직후 1~2블록 안에 보상 회복 발생 |
| major defeat without next card in same or next block | no | defeat block 4(꽃값) → block 5(셔틀 노선). defeat block 25 → block 26(폐기물 코드). 모두 즉시 다음 카드 제시 |
| BI acts as summary echo only | no | BI가 opponent_transition_plan(3단계 적대 전환), front_sector_by_arc(7아크 전선 배치), hud_interpretation(Resource-Power HUD 해석 규칙) 등 TR에 없는 구조적 증폭 제공 |
| early reward is asset-only, lacks status/authority shift | no | block 2에서 한유림 평가 전환, block 3에서 서도윤 인식 변화, block 9에서 노현주 집행 보고를 통한 가문 공식 기록 — 자산 + 지위/권한 이동이 함께 발생 |
| wins rely on stupid opposition | no | 노현주(법률 중심 사고), 서도윤(장남 통제 오만), 윤석진(CFO 관성), 백도현(사모펀드 선매입) — 모두 자기 인센티브에 따른 합리적 방해. 시대·구조 유효 |
| domain texture is generic enough to swap with another lane | no | 장례 뒷문 → 밥차 → 꽃값 → 셔틀 → 영수증 → 세탁실 → 청소 → 린넨 → 폐기물 → 정산코드의 현장 질감은 다른 장르 레인과 교환 불가 |
| protagonist stays mostly passive across key arc while reward remains weak | no | 모든 아크에서 주인공이 직접 설계·제안·압박을 실행 |

Active cap rules: **none**

---

## 4. P1 Score Table

| Axis | Score | Anchor |
| --- | --- | --- |
| protagonist innocence | **2** | 유언장 7항 집행(wrong structure), 망나니 평판은 전생 자해이나 현재 주인공의 과실 아님. 개시 불이익이 가문 구조에서 온다 |
| protagonist-only proof clarity | **2** | block 2 응급 배식 설계: 전생 동선 기억 × 실시간 데이터 교차 → 90분 안에 민원을 꺾는 행위는 윤재이 고유 |
| evaluation revision visibility | **2** | block 2 한유림 첫 인정, block 3 서도윤 인식 전환, block 9 노현주 집행 보고 — 세 명 모두 유의미한 무게를 가진 인물 |
| visible reward token strength | **2** | 출입표 → 급식 수수료 2억 → 관제권 → 노선 공동 운영권 → 월 반복매출 1.5억/월. 감정이 아니라 숫자·계약·권한 형태의 체감형 토큰 |
| block 1 → block 2 linkage | **2** | ARC-01 exit(block 10) 월 반복매출 → 형 시선 전환 → 호텔 BOH 입장권 공식 개방. 깔끔한 next-gate opening |
| rational opposition | **2** | 노현주(유언 집행 의무), 서도윤(장남 통제권 보호), 윤석진(비용 통제 CFO), 백도현(부실 자산 롤업) — 전원 인센티브 기반, 시대 유효 |
| domain truth density | **2** | 장례 뒷문 비용 라인, 밥차 냉각 고장, 꽃값 외상 구조, 셔틀 노선권, 조의금 영수증 누수, 세탁실 출입카드, 청소 야간 할증 중복 — 현장 밀도 극상 |
| repeatable loop clarity | **2** | 운영 현장 병목 탐지 → 전생 지식 기반 재설계 → 영수증/로그 분리 → 반복 현금흐름 확보 → 다음 전장 입장권. 이 루프가 7아크 70블록에 걸쳐 반복 |
| BI amplification power | **2** | BI가 opponent_transition_plan(3단계), front_sector_by_arc(7아크), hud_interpretation, portfolio_history, expansion_order_locked 등으로 TR을 구조적으로 증폭 |
| cider drought control | **1** | block 6(quiet_setup: 증거 예치만, 직접 현금 증가 없음) + block 7(quiet_infiltration: 로그권만) 구간에서 보상 체감이 약해진다. 또한 defeat block(4, 25, 35, 45, 55, 65)이 정확히 아크당 1회 배치되어 패턴이 기계적으로 느껴질 수 있다 |

**P1 Total: 19 / 20**

---

## 5. Provisional Grade

**GREENPLUS**

근거:
- P0 하드게이트 6/6 전통과
- cap rule 활성 없음
- P1 총점 19/20 (GREENPLUS 구간 17~20)
- block 1(episodes 2~6)이 `proof → reevaluation → reward → next gate` 의 모범 사례
- 후반 보상 케이던스가 아크 exit reward(block 10, 20, 30, 40, 50, 60, 68~70)로 의도적으로 유지

---

## 6. Top 3 Repair Units or Alias Note

GREENPLUS이므로 repair unit 대신 alias note와 residual risk를 기록한다.

### Alias Note

- pair 02는 **support-system cashflow 장악물 벤치마크 레퍼런스**로 등록 가능
- block 1 conversion chain(장례 뒷문 → 밥차 → 관제권 → 꽃값 → 셔틀 → 월 반복매출)은 blockguide 가문의 first-block cider 교과서 사례
- `영수증 분리 발행 → 출입카드 로그 → 정산 코드`로 이어지는 데이터 자산 축적 패턴은 다른 pair에도 참조 가능

### Residual Risk

1. **quiet block 연속 구간(block 6~7)의 보상 체감 약화** — 증거 예치·로그 확보는 전략적으로 타당하나 독자 체감 cider가 2블록 연속 약하다. 조용한 블록에도 작은 체감 보상 한 줄을 추가하면 케이던스가 더 단단해진다.
2. **defeat block 배치의 기계적 균일성** — 아크당 정확히 1회(block 4, 25, 35, 45, 55, 65) defeat block이 반복되어 구조적 예측 가능성이 생긴다. 패배 타이밍에 약간의 비대칭을 주면 긴장감이 올라간다.
3. **block 6 증거 예치의 장기 페이오프 체감** — 조의금 영수증 누수 지도가 block 63(유언장 뒷면)에서 회수되지만, 57블록 간격은 독자 기억 한계를 넘을 수 있다. 중간 리마인더 콜백이 있으면 페이오프 만족도가 상승한다.

---

## 7. Concise Rationale

pair 02는 현재 벤치마크 기준으로 가장 완성도 높은 pair 중 하나다. block 1에서 가족카드 차단(wrong structure)이라는 구조적 불이익에서 출발해, 전생 지식 기반 현장 재설계로 90분 안에 첫 승리를 만들고, 한유림·서도윤·노현주 세 명의 평가 전환을 block 1 안에서 모두 끌어낸다. 보상은 감정이 아니라 출입표·수수료·관제권·노선권·월 반복매출이라는 숫자와 계약 형태로 착지하며, 각 보상이 다음 전장(호텔 → 공장 → 병원 → 정산 → 전국망 → 가문 역의존)의 입장권을 직접 연다.

watchpoint 검증:
- **early gains가 visible cider인가, survival/probation relief에 불과한가**: block 2의 2억 수수료 + 한유림 인정, block 3의 관제권 확보는 단순 생존이 아니라 다음 운영 전장으로의 확장 발판이다. 생존 안도가 아니라 '한 칸 올라섰다'는 체감이 분명하다.
- **block 1 reward가 block 2를 실제로 여는가, 단지 즉각적 고통을 멈추는 것에 그치는가**: block 9~10에서 세탁·청소·셔틀 월 반복매출이 확정되고, 이것이 형의 시선 전환을 거쳐 호텔 BOH 진입 입장권으로 직접 전환된다. 고통 중지가 아니라 게이트 개방이다.

BI는 opponent_transition_plan, front_sector_by_arc, hud_interpretation, expansion_order_locked 등으로 TR을 단순 요약하는 것이 아니라 구조적으로 증폭한다. pair 수준의 엔진이 살아 있다.

cider drought control에서 1점을 감점한 것은 block 6~7의 quiet 연속 구간과 defeat block 배치의 기계적 균일성 때문이나, 이는 GREENPLUS를 위협하는 수준이 아니다. residual risk 3건은 모두 미세 조정 영역이며, 수리가 아니라 polish에 해당한다.

---

read-only benchmark audit complete; no pair files mutated
