# Pair 05 Benchmark Audit Report

Date: 2026-04-07
Terminal: 05
Document Type: read-only benchmark audit report
Canonical Path: `docs/2026-04-07/09pair_benchmark_terminal05_pair05_report.md`
Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
Governing Spec: `material_ssot/00_governance/production-pair-benchmark-spec-v1.md`

## Pair Identity

- pair id: `05`
- work id: `failed_future_ceo_intern`
- title: 망한 미래의 CEO가 인턴으로 빙의했다
- family: `blockguide`
- TR: `treatments/05_failed_future_ceo_intern_tr_block_070_draft.json` (70 blocks)
- BI: `bible/05_bi_failed_future_ceo_intern.json`
- genre: 현대 한국 기업 빙의 조직장악물

## P0 Hard Gates

| # | Gate | Result | Anchor |
| --- | --- | --- | --- |
| 1 | first-block visible cider | **PASS** | Block 3 `reward`: CC 라인 진입 + 발표권 (Lv1→Lv2, "첫 사이다" 명시). Block 7 `reward`: 해고 철회 + 김미선 공식 지지자 전환. Block 9 `reward`: 정태준 실명 호명 + 재정리 지시 (Lv2→Lv3). Block 10: 보상 4종 동시 발동 |
| 2 | protagonist-only proof | **PASS** | Block 3: 연락처 트랩→차장 검증 콜백 유도 — 13년 CEO 기억 기반 결재선 우회 설계는 수혁만 가능. Block 9: 정태준 주재 회의에서 침묵→단문 1개로 실명 호명 유도 — 이사회 보고용 가중치 구조를 아는 인턴은 없다 |
| 3 | evaluation revision | **PASS** | Block 3: 최준호 차장이 CC 진입시키고 "직접 5분 발표하라" 지시. Block 7: 김미선이 인사 조작 감지 후 공식 지지자 전환. Block 9: 정태준 부사장이 "이수혁 인턴, 이 안건 네가 다시 정리해서 올려"로 첫 실명 호명. 3인의 weighted evaluator가 block 1 안에서 명시적으로 재평가 |
| 4 | visible reward token | **PASS** | Block 2: 분기 KPI 회의 참관권 (entry ticket). Block 3: CC 라인 정식 진입 + 발표권 (CC/report-line entry). Block 9: 정태준 실명 호명 (name call) + 임시 상신권. Block 10: 정규직 전환 트랙 확정 + 전략기획실 직속 OJT + KPI 안건 작성자 권한 (seat + approval + project assignment). 개인 3,000만 원 코스피 매수 |
| 5 | block 1 → block 2 gate linkage | **PASS** | Block 10 `exit_function`: 보상 4종(정규직 전환·전략기획실 접근·정태준 실명·KPI 발언권)이 ARC-02 "사원에서 핵심 인재로" 진입을 직접 개방. ARC-02 `entry_function`이 ARC-01 보상을 전제 |
| 6 | BI/TR early conversion alignment | **PASS** | BI `cider_point`: "저평가된 자산과 병목을 먼저 읽고 지배력으로 전환하는 역전감." BI `success_device`: "답을 통과시키는 권한 구조까지 손에 넣어야 판이 바뀐다." TR blocks 1-3에서 KPI 우회 상신→CC 진입→연락처 트랩이 정확히 이 계약을 이행. BI `desire`: "오프닝 단계 안에 권한 입장권 보상 4종으로 회수" — block 10에서 정확히 회수 |

Opening Innocence Rule: **통과**. 오프닝 추락 원인은 전생 정태준의 데이터 조작 + 외부 세력 매각 포석이며 현재 주인공의 과실이 아님. 빙의 출발점은 "wrong seat + inherited bad frame"에 해당.

## Active Cap Rules

**none**

검증 근거:

| Cap Rule | Status | Anchor |
| --- | --- | --- |
| no visible cider inside block 1 | 미해당 | blocks 2-3, 7, 9, 10에 복수의 concrete cider |
| rewardless pain blocks 2 in a row | 미해당 | blocks 4-6이 가장 긴 저보상 구간이나 block 4는 전략적 예금(타임스탬프), block 5-6은 관찰·관계 포석이지 pain이 아님. block 7에서 해고 위기→동맹으로 강력 회수 |
| no-cider drought 6+ blocks | 미해당 | 매 arc마다 quiet 1 + defeat 1-2 + reward 복수. 최장 저보상 구간 3블록(4-6) |
| major defeat without next card | 미해당 | block 4 defeat→block 7 동맹(3블록 gap이나 5-6은 관찰 포석). block 20 피로스→block 21 차장 발령. block 44 양산 실패→same block 장현우 특허 적용. block 63 임원 12명 사직→same block 대체 12명 즉시 승진. **watchpoint 충족: 매 major defeat가 same/next block에서 next card 반환** |
| BI acts as summary echo only | 미해당 | BI `opponent_transition_plan` 5단계, `ArcSheets` 7개(entry/exit function·emotion curve·defeat blocks 별도 구조화), `portfolio_history` 0원→5,200억 추적, `DealTypeRotation` 70블록 전량 등재. TR 요약 이상의 구조적 증폭 |
| early reward asset-only, no status/authority shift | 미해당 | block 2 참관권(authority), block 3 CC+발표권(authority shift), block 9 실명 호명(status shift), block 10 정규직+직속 OJT(status+authority) |
| wins rely on stupid opposition | 미해당 | 오승재: 한예린 승계 차단이라는 합리적 동기. 정태준: 외부 매각 장기 포석. 사라 밀러: LP 구조 기반 행동주의 펀드. 모두 incentive-driven, era-valid |
| domain texture generic/swappable | 미해당 | 결재선 우회, KPI 산정식, 인사 시스템 로그, 이사회 표결, 스톡옵션, 위임장 대결, 포이즌 필, 크로스보더 스왑 — 한국 대기업 경영 도메인 자체가 엔진 |
| protagonist passive across key arc + weak reward | 미해당 | 매 블록 수혁이 우회 설계·트랩·프레임 전환·증거 설계를 주도. quiet blocks(6, 17, 24, 36, 46, 53, 69)에서도 관찰·기록·자기 판단 외부화로 능동적 |

## P1 Score Table

| Axis | Score | Anchor |
| --- | --- | --- |
| protagonist innocence | **2** | 전생 파산 원인은 정태준 데이터 조작(재작성 폭 31%) + 외부 매각 포석. 현재 주인공 과실 0. "wrong seat + inherited bad frame" |
| protagonist-only proof clarity | **2** | 13년 CEO 기억 + 결재선 우회 설계 조합이 모든 proof scene의 기저. block 3 연락처 트랩, block 9 침묵+단문은 "저건 쟤라서 가능했다"의 교과서적 실행 |
| evaluation revision visibility | **2** | 최준호(block 3 CC), 김미선(block 7 공식 지지), 정태준(block 9 실명 호명), 노정숙(block 16 첫 인지) — 4인의 weighted evaluator가 명시적 재평가. 블록 내 관계 delta로 추적 가능 |
| visible reward token strength | **2** | 참관권→CC→발표권→실명 호명→임시 상신권→정규직→직속 OJT→KPI 작성자 권한. blockguide 토큰 7종+ 이 block 1 안에서 단계적 적층. 현금(3,000만)은 부차 |
| block1 → block2 linkage | **2** | ARC-01 exit function "권한 이동 4종"이 ARC-02 entry function "전략기획실 말단 사원 배치"를 직접 개방. 보상이 다음 게이트를 여는 구조가 명시적 |
| rational opposition | **2** | 5단계 적대자 전환(오승재 내부정치 → 빅터 웨이 기술탈취 → 사라 밀러 행동주의 → 정태준 배신 → 삼면 연합). 각 적대자의 동기가 경제적·정치적으로 구체적이며 era-valid |
| domain truth density | **2** | 한국 대기업 결재선·KPI·인사 시스템·이사회 표결·포이즌 필·위임장 대결·스톡옵션·크로스보더 스왑·BIS 수출 규제·국민연금 지분이 엔진 자체. 다른 장르와 swap 불가 |
| repeatable loop clarity | **2** | "미래 지식 → 결재선 병목 식별 → 우회 설계 → 권한 상승 → 다음 게이트" 루프가 70블록에 걸쳐 명시적 반복·확장. BI `success_device`에 루프 공식이 문장으로 명시 |
| BI amplification power | **1** | BI `opponent_transition_plan`·`ArcSheets`·`portfolio_history`·`DealTypeRotation`은 TR을 구조적으로 증폭. 그러나 `KeyNPCs` desc 필드가 TR 블록 내용을 장문 반복하고, `MartialHUD`는 alias placeholder. 증폭은 있으나 echo 비율이 일부 과다 |
| cider drought control | **2** | 매 10블록 arc마다 quiet 1 + defeat 1-2 + reward 복수. defeat blocks(4, 7, 14, 20, 26, 29, 33, 38, 44, 47, 55, 63, 66)이 same/next block에서 next card를 반환. 최장 저보상 구간 3블록(4-6) |

**Total: 19 / 20**

## Provisional Grade

**GREENPLUS**

근거:
- P0 hard gates 6/6 전량 통과
- YELLOW ceiling rule 미해당
- P1 total 19 (GREENPLUS 범위 17-20)
- block 1이 proof → reevaluation → reward → next gate 모범 사례
- later reward cadence가 arc 단위로 의도적 유지
- watchpoint 항목 (punishment spiral / passive suffering / delay-only reward) 전량 미해당

## Top 3 Repair Units or Alias Note

Grade가 GREENPLUS이므로 repair units 대신 alias note 및 residual risk를 기록한다.

### Alias Note

- pair `05`는 현재 benchmark spec 기준 `GREENPLUS` provisional grade에 해당
- 기존 benchmark exemplar 중 `office_checkup_next_day`(first-block conversion benchmark)와 동급 또는 상위의 first-block conversion chain을 보유
- `pantech_cyworld_reborn`(authority-ticket benchmark)과 동급의 block 1 authority token 적층 구조
- `투자물_골든_카나리아 테스트_canonical_v1`(GREEN reference)보다 상위: 이 pair는 early reward가 자산 + 권한 + 지위 3축 동시 이동이며, GREEN reference의 "자산 우선" 패턴을 초과

### Residual Risk (3항목)

1. **BI echo 비율**: `KeyNPCs` description이 TR 블록 content를 장문 반복하고 `MartialHUD`가 alias placeholder 상태. BI가 TR echo를 줄이고 독자 구조(foreshadow seed graph, opponent weakness evolution 등)를 강화하면 P1 BI amplification 2점 가능
2. **blocks 4-6 저보상 구간**: block 1 내 유일한 3블록 연속 저보상 구간. 현재 narrative 기능(전략적 예금→관찰→파벌 지도)으로 정당화되나, block 5-6의 reader-facing cider를 한 단계 올리면 first-block conversion이 더 견고
3. **빙의 지식 의존 단조성 가능성**: protagonist-only proof의 기저가 "전생 기억으로 먼저 안다"에 집중. TR이 간접 제안→데이터 설득→직접 의사결정→조직 설계로 방법론을 확장하여 관리하고 있으나, 70블록 장편에서 빙의 지식 정확도 하락(나비효과) 구간이 주로 quiet/내면 블록에 배치되어 본격 갈등으로의 전환 밀도를 높이면 더 강해짐

## Concise Rationale

Pair `05`는 block 1 안에서 "인턴 0권한 → 결재선 우회 → CC 진입 → 실명 호명 → 보상 4종 동시 발동"이라는 blockguide 교과서적 first-block conversion을 달성한다. 주인공의 proof는 13년 CEO 기억 + 결재선 우회 설계라는 protagonist-only 조합에 의존하며, 최준호·김미선·정태준·노정숙 4인의 weighted evaluator가 block 1-16에 걸쳐 명시적으로 재평가한다. 적대자 전환이 5단계(오승재→빅터 웨이→사라 밀러→정태준→삼면 연합)로 구조화되어 있고, 각 적대자가 경제적·정치적으로 합리적인 동기를 가진다. 한국 대기업 경영 도메인(결재선·KPI·인사·이사회·위임장·공개매수)이 엔진 자체이며 다른 장르와 swap 불가능하다. BI는 opponent transition plan·arc sheets·portfolio history로 TR을 구조적으로 증폭하나, NPC description echo와 MartialHUD placeholder가 잔존 약점이다. 70블록에 걸친 reward cadence는 매 arc마다 defeat → same/next block recovery를 유지하여 watchpoint(punishment spiral, passive suffering, delay-only reward)에 해당하는 구간이 없다.

read-only benchmark audit complete; no pair files mutated
