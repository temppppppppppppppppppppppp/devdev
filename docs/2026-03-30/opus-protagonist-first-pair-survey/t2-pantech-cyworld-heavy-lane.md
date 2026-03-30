# T2. Pantech Cyworld Heavy Lane — Protagonist-First TR-BI Pair Survey

Date: 2026-03-30
Lane: T2
Reviewer: Terminal 2 (Opus)
Status: final (3-pass audited)

## 1. Pair Identity

- work_id: `pantech_cyworld_reborn`
- family: `blockguide`
- TR path: `treatments/pantech_cyworld_reborn_tr_block_070_draft.json`
- BI path: `bible/0_bi_pantech_cyworld_reborn.json`

## 2. Survey Windows

### TR Windows

| Window | Blocks | Rationale |
|--------|--------|-----------|
| Opening | 1-10 | Establishment of protagonist engine, first setback cycle |
| Middle stress | 30-32 | Peak승계전 + political exposure — high pressure zone |
| Endgame | 63-70 | Policy adoption → Japan export → succession resolution → coronation |

### BI Sections Inspected

- `ProjectData.CoreIdentity` (protagonist desire/edge/crisis/growth_arc)
- `FinanceHUD.Protagonist.actual_truth` (financial status, inventory, causal_injuries)
- `FinanceHUD.Protagonist.public_reputation`
- `GenreRules` + `genre_contract`
- `ArcStructure` (7-arc overview)
- `OpponentTransitionPlan` (6-phase enemy map)
- `BackHalfTechIdentityAnchors` (Block 40-70 drift guards)
- `PayoffTrack` (capital/power/relationship/foreshadow payoff)
- `plot_roadmap` Block 1 alignment check
- `portfolio_history` (15 checkpoints, Block 1-70)
- `KeyNPCs` (15 NPCs with arc summaries)

## 3. Rubric Findings

### R1. Protagonist Reward Visibility — GREEN

Every surveyed block gives visible recognition after protagonist success:

- **Block 1**: 회장이 판을 열어 줌 + 차우진이 "숫자만큼은 틀리지 않았다"고 인정 + 정민석이 비공식 협력 시작
- **Block 2**: 오세라가 터치 UI 프로토타입과 인력 지도를 공유 (신뢰의 표현)
- **Block 5**: 공개 시연 실패 — 그러나 병목 데이터 확보 + 오세라/한유리가 밤샘으로 버팀 + 박기태 합류. 실패가 순수 처벌이 아니라 "실패를 자산으로 전환"하는 구조. **주인공이 능동적으로 실패를 뒤집음**.
- **Block 30**: 장외 매집 성공 + 초도 출고 공개 + 시장이 "미래"로 인정. "지분과 출고를 동시에 장악"이라는 서사적 쾌감.
- **Block 65**: 비용을 치르지만 의결권 방어 성공 + 형제파가 "낡은 언어"로 밀림
- **Block 70**: coronation 감정 비트, intensity 10. 팬택과 싸이월드를 "한 시대의 생활계정"으로 재정의.

**위반 없음.** 성취 후 반응 파이프라인이 70블록 전체에서 일관되게 작동.

### R2. Reward Dwell Time — GREEN

보상 체류가 일관되게 유지됨:

- Block 1(350억 확보) → Block 2-3에서 팬택 채권 선점, 싸이월드 인수 논리 활용으로 보상 활용
- Block 6(베타폰 성공) → Block 7-9에서 베타폰 기반 체험존 진출, 앱마켓 확대로 향유
- Block 30(장외 매집 역전) → Block 31에서 수출 로그 분석으로 2세대 설계, Block 33에서 시제품 공개까지 보상 활용
- Block 63(정책협의체 채택) → Block 64(일본 수출 협상 양해각서) → Block 68(기업가치 재평가)로 점진적 보상 확장

**즉시 박탈 패턴 0건.** 자본 감소가 발생하는 블록(2, 5, 15, 20, 32, 65, 70)에서도 감소 원인이 "주인공이 의도적으로 투자한 비용"이지 외부가 강제로 빼앗은 것이 아님. `portfolio_history`에서 25/70 블록 setback(36%)이지만, 모든 setback이 "쓰라린 승리" 또는 "전략적 비용"으로 프레이밍됨.

### R3. Pain Aesthetic — GREEN

주인공이 고통받는 장면의 미학이 일관되게 aspirational:

- **Block 5** (코엑스 시연 실패): emotional_beat = `humiliation`, intensity 4. 그러나 주인공은 "실패를 정면으로 인정"하고 "병목을 산다"는 냉혹한 실행력으로 반전. 독자 감정이 "답답함"이 아니라 "이 사람 대단하다"로 전환.
- **Block 2** (60억 손실): `pyrrhic_victory`. 돈은 잃었지만 이사회 진입권과 기술 인력 확보. "지금 돈을 아끼면 나중에 살릴 기술이 없어진다"는 주인공 독백이 aspirational.
- **Block 65** (170억 방어 비용): 형제파 이사회 공세를 방어하느라 비용 소모. 그러나 "숫자와 문장 모두에서 더 설득력 있다"는 시장 평가가 따라옴.

**순수 굴욕, 무력감, 침울함만 남는 블록 0건.** 고통 후 반드시 주인공이 더 강해지는 방향으로 벡터 전환.

### R4. Vector Direction — GREEN

표면적으로 처벌/손실로 보이는 전개의 실제 벡터가 일관되게 보호적/전략적:

- 모든 자본 감소 블록에서 `success_pattern` 필드가 "쓰라린 실패/승리" + "다음 단계 선점"으로 명시
- `death_flag.avoided` 필드가 매 블록에서 주인공이 피한 비극적 미래를 보여줌 → 독자에게 "전생에서는 이걸 못 했는데 이번에는 해냈다"는 보상 감각
- `execution_doctrine` 필드가 매 블록마다 주인공의 판단 원칙을 one-liner로 제시 → 주인공이 멋있게 읽히는 장치

**좌절 벡터가 부정적으로만 남는 블록 0건.**

### R5. Exclusive Protagonist Engine — GREEN

윤도현만의 교체 불가능한 엔진이 명확:

1. **회귀 지식**: 2006-2024년 한국 IT 전체 흥망사를 알고 있음. `regression_ext`가 70블록 전체에서 "미래 지식 → 타이밍 투자"로 작동.
2. **이중 구조**: 최대 강점(미래 지식) = 최대 약점(정체 노출). BI `protagonist_config.regression_mechanic.suspicion_pressure`에서 17명 NPC의 의심 이벤트 누적으로 긴장 유지.
3. **투자+통제 실행력**: 단순히 돈을 버는 게 아니라 "몰락 직전의 기업을 한 몸처럼 묶는" 설계 역량. 다른 캐릭터로 교체 시 스토리 엔진 완전 붕괴.

BI `CoreIdentity.edge`: "2006~2024년 한국 IT 흥망의 전체 타임라인 지식 + 냉혹한 손익 판단 + 실패를 자산으로 전환하는 실행력"

### R6. Genre Contract Stability — GREEN

blockguide의 현대판타지 business-power 계약이 일관되게 유지:

- `genre_contract.primary_resource`: "자본(현금, CB, ABS, 지분) + 기술 통제권(특허, 인증, 표준) + 사용자 습관(첫 화면, 구독, 데이터)"
- `genre_contract.defeat_mechanic`: "25/70 블록에서 자본 감소. 단기 손실이 장기 통제권의 대가."
- `genre_contract.tech_identity_anchor`: "모든 확장은 '팬택의 제조 역량 + 싸이월드의 관계 그래프'에서 출발한다는 원점을 유지"

후반부(Block 40+) 스마트시티/돌봄/정책 확장에서도 `BackHalfTechIdentityAnchors`가 BI 레벨에서 기술 정체성 드리프트를 방어:
- Block 40-50: "병원 연동도 '모바일 건강 데이터를 가족 계정에 묶는 기술'이지, 병원 SI 수주가 아니다."
- Block 51-60: "도시 운영판의 OS는 팬택 단말의 IoT 센서 네트워크 + 싸이월드 생활계정이다."
- Block 61-70: "승계 전쟁의 최종 무기는 '이 생태계가 실제로 작동한다'는 실적이다."

**노맨스 계약 위반 0건. 기술/사업 쾌감이 정치/공공 언어로 대체되는 드리프트를 BI 앵커가 능동적으로 방어.**

### R7. BI Amplification — GREEN

BI가 단순 TR 미러가 아니라 독자적 보강을 제공:

1. **PayoffTrack**: TR에 없는 메타 수준의 보상 누적 구조 (자본 0→7,790억, power milestone 9개, relationship delta 210건, foreshadow 137건 planted / 82건 resolved).
2. **OpponentTransitionPlan**: 6단계 적대 세력 진화 맵이 TR 블록을 관통하는 거시 구조로 보강.
3. **BackHalfTechIdentityAnchors**: TR에 없는 BI 전용 drift guard. 후반부 장르 정체성 방어를 BI 레벨에서 추가.
4. **KeyNPCs**: 15명 NPC의 arc_summary, suspicion_count, key_blocks가 TR 블록 단위 기술을 넘어 캐릭터 여정의 전체 지도를 제공.
5. **portfolio_history**: 15개 체크포인트로 자본 성장 궤적과 narrative_state를 한눈에 보여줌.
6. **protagonist_config.regression_mechanic**: 의심 압력 누적 구조 (17명 NPC, 상위 3명 10회+)가 TR의 블록별 `regression_hint`를 거시적으로 보강.

**BI가 TR의 블록 요약만 반복하는 thin-echo 패턴 0건. 구조적 보강이 명확.**

## 4. Focus Question Responses

### "does this pair make the protagonist feel admired for judgment and leverage, not just nostalgia or corporate scale?"

**Yes.** 팬택/싸이월드라는 실존 브랜드의 향수(nostalgia)는 서사의 배경이지 주인공 쾌감의 원천이 아님. 독자가 감탄하는 것은:
- Block 1: 아이폰 쇼크 전에 선제 포지셔닝하는 판단
- Block 5: 공개 망신을 자산으로 바꾸는 실행력
- Block 30: 지분과 출고를 같은 날 움직여 판을 뒤집는 레버리지
- Block 68: 시장의 가치평가 문법 자체를 다시 쓰는 설계력

주인공이 단순히 "큰 회사를 가진 재벌"이 아니라 "타이밍을 읽고, 실패를 사고, 병목을 지배하는 투자자"로 읽힘.

### "when setbacks hit, do they still carry positive vector / reversal potential?"

**Yes, 일관적으로.** 70블록 전체에서 setback 25건(36%), 모든 건에서:
- `death_flag.avoided`로 "이 비용을 치르지 않았으면 벌어졌을 비극"이 명시
- `success_pattern`으로 "쓰라린 승리/실패"의 aspirational 프레이밍
- 주인공이 비용을 자발적으로 지불하는 구조 (외부 강제 박탈 아님)

### "does the BI keep the protagonist-first engine legible, or drown it in world/business data?"

**Legible.** BI가 9,200줄 규모로 거대하지만, protagonist-first 엔진이 묻히지 않는 이유:
- `CoreIdentity`가 욕망/결핍/우위/성장호를 명확히 정의
- `CommercialCode`가 대리만족 메커니즘을 직접 명시 ("타이밍 지식 기반 선제 투자 쾌감", "재벌 내부 정치를 실적으로 짓밟는 쾌감")
- `BackHalfTechIdentityAnchors`가 세계관/사업 데이터로 주인공 엔진이 묻히는 것을 능동 방어
- `PayoffTrack`이 보상 누적 구조를 전용 섹션으로 분리

## 5. Strongest Evidence

### Strongest Confirming Evidence

**Block 5 "코엑스에서 깨진 유리창"** — 이 블록이 protagonist-first의 가장 강력한 증거인 이유:

공개 시연이 망하는 장면(emotional_beat: humiliation)이지만, 주인공이 (1) 실패를 즉시 인정하고, (2) 병목 자체를 사들이고, (3) 핵심 동맹이 도망치지 않고 함께 남으며, (4) 312종 충돌 로그라는 "다음 승부의 자산"을 확보한다. 독자 감정은 "답답함"이 아니라 "이 사람은 진짜 다르다"로 전환된다.

이 블록은 `둥기둥기 first` 원칙의 "위협이 존재하되 PASS인 패턴" — "겉: 망신 / 실제: 전화위복"의 교과서적 실행.

BI의 `PayoffTrack.capital_payoff.mechanism`이 이를 "28가지 고유 deal_type으로 달성"이라고 거시적으로 확인.

### Strongest Violating Evidence

**위반 증거 없음.**

가장 가까운 후보: Block 65에서 170억 방어 비용 소모. 그러나 이것도 (1) 주인공이 자발적으로 지불, (2) 형제파가 "낡은 언어에 매달린다는 점만 더 선명해진다"는 가시적 인정, (3) "숫자와 문장 모두에서 더 설득력 있다"는 시장 반응이 즉시 따라오므로 위반이 아님.

## 6. 3-Pass Self Audit

### Pass 1. Scope Audit
- survey only — 코드 변경, 산출물 재생성, docs/temp 편집, 큐/로드맵 편집 없음
- live JSON body를 primary evidence로 사용
- 주인공 둥기둥기 first 정렬만 판정

### Pass 2. Operational Audit
- T2 lane only — pantech_cyworld_reborn 단일 작품만 판정
- 다른 lane의 report를 덮어쓰지 않음
- bounded windows 먼저 → 확장 불필요 (위반 발견 없음)

### Pass 3. Integrity Audit
- `docs/2026-03-30/opus-protagonist-first-pair-survey/` 아래 저장
- UTF-8 only
- queue/temp mutation 없음
- patch/artifact rewrite 지시 없음
- 확신도: 97%

## 7. Verdict

```
lane: T2
work_id: pantech_cyworld_reborn
family: blockguide
TR verdict: green
BI verdict: green
pair verdict: green
strongest confirming evidence: Block 5 "코엑스에서 깨진 유리창" — 공개 시연 실패(humiliation beat)를 주인공이 병목 인수로 전환, 핵심 동맹이 함께 남고 312종 충돌 로그 확보. 겉: 망신 → 실제: 전화위복. 둥기둥기 first의 교과서적 실행.
strongest violating evidence: 없음. 가장 가까운 후보는 Block 65의 170억 방어비용이나, 주인공 자발적 지불 + 형제파 약화 확인 + 시장 인정이 즉시 따라오므로 위반 아님.
reference pair candidate: yes
```
