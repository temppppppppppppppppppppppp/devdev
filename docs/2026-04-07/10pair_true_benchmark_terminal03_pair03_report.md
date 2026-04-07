# 10pair True Benchmark — Terminal 03 / Pair 03 Report

Date: 2026-04-07
Status: active
Audit Mode: read-only true benchmark
Spec: `material_ssot/00_governance/production-pair-benchmark-spec-v1.md`
Manifest: `docs/2026-04-07/01_10_canonical_pair_manifest.md`

## 1. Pair Identity

- pair id: `03`
- slug: `chaebol_ent_empire`
- family: `blockguide`
- one_line_truth: 쓰레기로 떠넘겨진 소형 엔터 자회사의 낙하산 대표가, 스타의 터질 타이밍과 맞는 자리를 읽는 감각으로 배치·패키지·접점을 묶어 업계가 따라 할 수밖에 없는 구조를 만든다
- BI: `bible/03_bi_chaebol_ent_empire.json`
- TR: `treatments/03_chaebol_ent_empire_tr_block_070_draft.json` (총 70 블록, schema `tr.v1`)
- WG: `work_guards/03_chaebol_ent_empire.yaml`

## 2. Evidence Anchor Table

| Anchor | Source | Location | Content (요약) |
| --- | --- | --- | --- |
| early promise | BI MetaInfo.logline | BI L13 | "몰락 재벌 3세가 쓰레기처럼 떠넘겨진 소형 엔터 자회사를 배우·아이돌·셰프·팬덤·커머스를 묶는 스타 IP 복합기업으로 키워 업계 표준" |
| cider_point | BI CommercialCode | BI L37 | "누구도 가치를 못 보던 사람을 맞는 자리에 놓는 순간 폭발하는 반전. 업계가 비웃던 변칙이 시장에서 먼저 통하는 쾌감" |
| success_device | BI CommercialCode | BI L38 | "개별 자산을 묶어 시장 자체를 만드는 패키지 전략. 방송이 아니라 팬 접점을 먼저 장악하는 비대칭 확장" |
| CommercialCode set | BI L36–41 | BI | cider_point / success_device / attitude / defeat_mechanic 4종 모두 존재 |
| one_line_truth | WG `work_identity.one_line_truth` | WG L5 | 위 동일 문장 |
| mandatory_scene_engines | WG L58–62 | WG | 비대칭 무대 공개증명 → 태도변화 회수 / 스타 감지 즉각 통하는 proof / 패키지 확장 / 위기 선독→다음 입장권 |
| evaluation_thresholds | WG L82–86 | WG | Block 1 강이현 즉석 proof, 첫 배치 직후 평가 수정, 후속 부킹·계약·자본 입장권, 큰 피해 뒤 즉시 카드 회수 |
| custom_rules | WG L102–109 | WG | 비회귀, 발굴이 아니라 배치, 블록 보상은 인재·계약·자본·접근권·서열 변화로 체감, 반격 예약 없는 손해 금지, 위기는 선독→대비→최소 피해→즉시 보상 순서로만 |
| tracking_slots | WG L43–47 | WG | 낙하산→사람 볼 줄 아는 놈→업계 표준 설계자, 인재 포트폴리오 확장, 비대칭 증명 누적, 자회사 자율권 |
| first_block_reward | WG L48–52 | WG | 평가 수정 + 7억 부킹 = 입장권 + 120억 = 결정권 + 한도윤 감시 벽 첫 후퇴 |

## 3. P0 Hard Gates

증거 창은 전부 `TR blocks 2~6` 안 (gate 5는 다운스트림 7+ 인용 허용, gate 6은 TR 1~3 허용).

| Gate | Result | Anchor | Note |
| --- | --- | --- | --- |
| 1. first-block visible cider | PASS | TR B2 reward (윤서아 정식 오디션 콜백 + 강이현 후속 부킹 확정, 자본 125억), TR B3 reward (+15억 현금 회수) | 블록 2~6 안에서 reader-countable 토큰 다수, B1 의존 없음 |
| 2. protagonist-only proof | PASS | TR B2 solution (윤서아를 '차갑고 위험한 조연'으로 재포지셔닝, PD 콜백), TR B3 solution (직접 지방 행사 동선·미수금·후속 일정 묶어 협상) | 스타 감지 + 배치 감각이 태하 고유. 단, B2~B3는 감각 기반이라 계량적 proof scene은 B1 즉석 무대만큼 쨍하지는 않음 (점수 영향 없음) |
| 3. evaluation revision | PASS | TR B2 relationship_delta 서민재 ("사람 보는 눈만큼은 이상하게 맞는다고 처음 의심"), TR B3 relationship_delta 오지혁 ("직접 뛰고 사람 성과까지 챙기는 인간이라 인정"), TR B3 reward 외부 거래처 담당자 ("이 회사 생각보다 될 수도 있겠다") | weight observer 3축 (실무 총괄 / 현장 매니저 / 외부 거래처) 모두 블록 2~3에서 작동 |
| 4. visible reward token | PASS | TR B2 (정식 오디션 콜백 + 부킹 계약 확정), TR B3 (+15억 운용 자본 + 외부 인정), WG L48–52 first_block_reward 조건과 일치 | 콜백·부킹·캐시·인정 4종 토큰이 2~3에서 동시 회수 |
| 5. block1→block2 gate linkage | PASS | TR B5 reward (스폰서 복귀 + 13억 부분 반격) → TR B6 reward (예약·셋리스트·대본·관계자 명단 실물) → TR B7 reward (쇼케이스 14억 후속) → TR B8 reward (드라마 캐스팅 +15억) | 같은 보상 사슬로 다음 게이트가 실제로 열린다. TR B7은 다운스트림 확인용 |
| 6. BI/TR early conversion alignment | PASS (narrow evidence) | BI L37 cider_point ↔ TR B1 강이현 즉석 무대 / TR B2 윤서아 '차갑고 위험한 조연' 재포지셔닝, BI L38 success_device(패키지 전략) ↔ TR B3 solution (강이현 부킹 정산 + 윤서아 콜백 사실 + 미수금·후속 행사·세령그룹 호텔 라인을 한 번에 묶어 협상) | spec v1상 P0 gate 상태값은 PASS/FAIL only. spec §2.1 strict window 기준 gate 6은 TR 1~3 안에서만 판정. early promise / cider_point / attitude는 B1~B3 안에서 명백히 살아 있고, success_device(패키지 전략)도 B3 협상 장면에서 사람 카드 + 행사 라인 + 호텔 계열을 한 번에 묶는 씨앗 형태로 visibly alive — strict window 안에서 alive 판정이 가능하므로 PASS. 다만 본격 패키지 단계는 아직 도달하지 않은 narrow한 증거라 P1 BI amplification power axis에 1점으로만 반영(§6 참조) |

종합: P0 6게이트 전부 PASS (gate 6은 narrow evidence). spec v1상 P0 상태값은 PASS/FAIL only이므로 ceiling 발동 없음. gate 6 narrow evidence는 §6 P1 BI amplification power axis에서 1점으로만 반영된다. §4 full-block cider scan 결과는 별도 ceiling을 발동한다.

## 4. Full-Block Cider Scan

- total TR block count: 70
- no-cider block count: 8
- exact no-cider block numbers: `4, 16, 23, 28, 34, 47, 55, 63`
- longest no-cider drought (consecutive rewardless blocks): 1 (모든 no-cider 블록이 단발로 분포, 2연속 없음)

판정 기준: 같은 블록 안에서 reader-countable 토큰(자본·계약·콜백·접근권·평가 수정·다음 카드 실물·즉시 보호 회수) 1개 이상 회수 여부. 자본 +수치만으로는 부족하면 token quality도 같이 본다.

### 4.1 Window Summary

- **B1~B10 (1섹터 — 쓰레기통 접수, 첫 패키지)**
  - cider hit: B1, B2, B3, B5, B6, B7, B8, B9, B10 (9/10)
  - no-cider: **B4** ("조준된 패배" — -15억 손실, reward는 "처음 의심" 인사이트 한 줄. 같은 블록 안에서 다음 카드/입장권 회수 없음 → pain-only)
  - 윈도우 평가: 첫 블록 conversion은 명백히 살아 있고 B10에서 청산 보류 + 패키지 인식까지 도달. 다만 B4가 WG `crisis_doctrine` ("즉시 보상")과 `custom_rules` "반격 예약 없는 손해 금지"를 직접 위반.
- **B11~B20 (2섹터 — 시스템·배신 1차)**
  - cider hit: B11, B12, B13, B14, B15, B17, B18, B19, B20 (9/10)
  - no-cider: **B16** ("배신" — -58억 급락, reward 본문은 "한도윤이 단순 감시자가 아니라 회사를 흔들 수 있는 정치 라인이라는 사실이 드러난다"는 정보형 회수만. 같은 블록 토큰 없음)
  - 윈도우 평가: B17~B20 강한 회복으로 380억까지 청산 위협 정리, 그러나 B16의 단발 무수확 손해는 같은 cap rule을 한 번 더 친다.
- **B21~B30 (3섹터 — 외부 자본·체질)**
  - cider hit: B21, B22, B24, B25, B26, B27, B29, B30 (8/10)
  - no-cider: **B23** (-56억, "외부 자본가가 더 큰 결과를 요구한다는 사실" 학습형 회수만), **B28** ("introspection", +3억 미미 + 내부 태도 변화만 — 독자가 셀 수 있는 토큰 없음)
  - 윈도우 평가: 전반적으로는 470억 도달까지 cadence 유지. B28은 토큰 약함 케이스에 가깝지만 spec의 reader-countable 정의에 미달.
- **B31~B40 (4섹터 — 패키지·F&B·체질 변화)**
  - cider hit: B31, B32, B33, B35, B36, B37, B38, B39, B40 (9/10)
  - no-cider: **B34** (-61억 setback, reward는 "체질 변화 필요 자각"만, 같은 블록 회수 카드 없음)
  - 윈도우 평가: B40에서 760억 돌파, 4단계 체질 변화 완수. 단발 손해 1개.
- **B41~B50 (5섹터 — 라이프스타일 IP 재정의)**
  - cider hit: B41, B42, B43, B44, B45, B46, B48, B49, B50 (9/10)
  - no-cider: **B47** (-136억 crisis, reward 본문이 "타격이 된다 + 내부 화살까지 맞는 자리라는 걸 처음 직접적으로 본다"는 인식 회수만)
  - 윈도우 평가: B49~B50 강력 회복(+163억, +176억)으로 1280억 도달, 라이프스타일 IP 기업 재정의 도달. 다만 B47 단발 무수확 손해.
- **B51~B60 (6섹터 — 글로벌 ORBIT)**
  - cider hit: B51, B52, B53, B54, B56, B57, B58, B59, B60 (9/10)
  - no-cider: **B55** (-264억 pyrrhic_victory — 본문 "큰 승리도 결국 패배가 될 수 있다는 것 체감"만, 같은 블록 회수 카드 없음. defeat_mechanic 직접 작동 블록이지만 same-block 토큰은 없음)
  - 윈도우 평가: B60에서 3600억 도달, 추천제 플레이어 단계. 단발 손해 1개.
- **B61~B70 (7섹터 — 권력전·표준화)**
  - cider hit: B61, B62, B64, B65, B66, B67, B68, B69, B70 (9/10)
  - no-cider: **B63** (-666억 collapse, reward "권력 자체가 흔들린다 자각" 학습형. 같은 블록 회수 카드 없음)
  - 윈도우 평가: B68~B70에서 6800억까지 가치 회복 + 산업 표준 확정으로 마무리. 단발 손해 1개.

### 4.2 Same-block Receipt 판정 디테일 (no-cider 8블록)

| Block | capital_delta | emotional_beat | reward 본문 핵심 | 판정 사유 |
| --- | --- | --- | --- | --- |
| 4 | -15억 | defeat | "이번 붕괴가 우연이 아니라 누군가 설계한 흐름이라는 첫 의심" | 정보형 인사이트 only, 같은 블록 토큰·카드 없음. WG custom_rule "반격 예약 없는 손해 금지" 위반 |
| 16 | -58억 | betrayal | "한도윤이 회사를 흔들 정치 라인이라는 정체가 드러난다" | 정보형 회수, 같은 블록 토큰 없음 |
| 23 | -56억 | frustration | "외부 자본가가 더 큰 결과를 요구한다는 걸 느낀다" | 학습형 회수, 같은 블록 토큰 없음 |
| 28 | +3억 | introspection | "경영 태도 한 단계 바뀐다" | 내부 태도만, +3억은 reader-felt 토큰으로 미달 |
| 34 | -61억 | setback | "체질 변화 필요를 더 분명히 자각" | 학습형 회수 |
| 47 | -136억 | crisis | "타격이 된다는 사실 + 내부 화살도 맞는 자리라는 걸 처음 직접적으로 본다" | 인식 회수, 같은 블록 카드 없음 |
| 55 | -264억 | pyrrhic_victory | "큰 승리도 결국 패배가 된다는 것 체감" | 학습형 회수 — defeat_mechanic 자체가 블록으로 작동하지만 same-block 토큰은 없음 |
| 63 | -666억 | collapse | "권력 자체가 흔들린다 자각" | 학습형 회수 |

전체 패턴: 무수확 블록은 모두 단발이고, 직후 블록(B5/B17/B24/B29/B35/B48/B56/B64)에서 강한 회복이 나온다. 그러나 spec §2.3의 강성 룰은 "다음 블록 회복"이 아니라 "같은 블록 안 reader-countable 회수"를 요구하므로, 8블록은 모두 no-cider로 확정된다.

## 5. Active Cap Rules

| Cap Rule | Active? | 근거 |
| --- | --- | --- |
| 블록 1 안 visible cider 부재 | not active | TR B2~B6 토큰 다수 |
| 첫 토큰이 TR B7+에 첫 등장 | not active | B2~B3에 콜백·부킹·캐시 토큰 도착 |
| **any no-cider block in full-block scan: YELLOW ceiling** | **ACTIVE** | no-cider 블록 8개 (4, 16, 23, 28, 34, 47, 55, 63) |
| rewardless pain blocks 2 in a row: GREEN ceiling | not active | 2연속 무수확 없음 (longest drought = 1) |
| no-cider drought 6+ blocks: YELLOW ceiling | not active | longest drought = 1 |
| major defeat without next card in same/next block: YELLOW ceiling | not active | 모든 무수확 손해 직후 블록(B5/B17/B24/B35/B48/B56/B64)에서 카드 회수 |
| BI summary echo only: GREEN ceiling | not active | BI cider_point/success_device가 TR을 sharpen |
| early reward asset-only without status/authority: GREEN ceiling | not active | B1에서 자본 + 결정권 + 부킹 입장권 + 한도윤 감시 벽 첫 후퇴까지 동시 |
| 멍청한 적대자에 의존한 승리: GREEN ceiling | not active | 한도윤·권도현·대형 기획사 모두 incentive-driven |
| 도메인 텍스처 generic: GREEN ceiling | not active | 배치·부킹·캐스팅·패키지·접점·라이선싱·기업가치·표준 어휘가 본문에 살아 있음 |
| 주인공 수동성 + 약한 보상 누적: YELLOW ceiling | not active | 모든 핵심 구간에서 태하가 직접 판을 짠다 |

활성 cap: **YELLOW ceiling (no-cider 8블록 cap rule 1건)**.

## 6. P1 Score Table

| Axis | Score | 근거 |
| --- | --- | --- |
| protagonist innocence | 2 | 호텔 사고는 배경, 떠넘겨진 자회사·정치적 시험대 — 전형적 정치적 희생 / 잘못된 자리. WG `forbidden_flattenings` "비굴한 해명" 회피 확인 |
| protagonist-only proof clarity | 2 | B1 강이현 즉석 무대, B2 윤서아 '차갑고 위험한 조연' 재포지셔닝, B3 직접 현장 협상 — 모두 스타 감지 + 배치 고유성 |
| evaluation revision visibility | 2 | B2 서민재 / B3 오지혁 / B3 외부 거래처 / B5 한도윤 첫 불편 — 4축 weight observer 모두 작동 |
| visible reward token strength | 2 | B1 자본 120억 + 결정권 + 부킹 7억, B2 콜백 + 부킹 확정, B3 +15억 + 외부 인정, B7 쇼케이스 14억, B10 청산 보류 |
| block1→block2 linkage | 2 | B5 부분 반격 → B6 실물 기획 → B7 쇼케이스 → B8 드라마 캐스팅 → B10 청산 보류, 사슬 깨끗 |
| rational opposition | 2 | 한도윤은 시장 정답 + 정치 라인, 권도현은 산업 시각 차이, 대형 기획사는 시장 합리성. WG role_fit_constraints "적대자 존엄 유지" 준수 |
| domain truth density | 2 | 케이블 드라마 악역 조연 수요(2009), VIP 행사 부킹, 케이터링·호텔 라인 묶기, 팬덤 플랫폼·F&B IP — 엔터/엔터테인먼트 라인 텍스처 살아 있음 |
| repeatable loop clarity | 2 | "선독 → 비대칭 배치 → 공개 증명 → 입장권 회수" 루프가 B1→B7→B10에서 이미 가시화, B30 이후 시스템 단위로 반복 |
| BI amplification power | 1 | BI cider_point는 TR 1~3에서 즉시 작동, defeat_mechanic은 후반 패배 블록 설계의 뼈대로 살아 있음. success_device(패키지 전략)도 gate 6 strict window(TR 1~3) 안에서는 B3 협상 장면의 씨앗 형태로만 visibly alive — gate 6 자체는 PASS이지만 amplification은 부분만 인정 |
| blockwise cider continuity | **0** | no-cider 8블록 (4, 16, 23, 28, 34, 47, 55, 63) — 단발이지만 spec 강성 룰상 0점 |

**Total: 17 / 20**

점수만 보면 여전히 GREENPLUS 밴드 하한(17~20)이지만, §6 active cap rule이 GREEN/GREENPLUS 진입을 차단한다.

## 7. Provisional Grade

**YELLOW**

판정 경로:
- P0 6게이트 전부 PASS (gate 6은 narrow evidence — spec v1상 P0 상태값은 PASS/FAIL only이라 PASS로 정규화, 약함은 P1 BI amplification axis 1점으로만 반영)
- P1 총점 17/20 → 자체적으로는 GREENPLUS 밴드 하한
- 그러나 §6 active cap "any no-cider block → YELLOW ceiling"이 활성 (no-cider 8블록 전부 해당)
- spec §2.3 / §3 / §6 / §8.3에 따라 cap이 점수보다 우선 → grade는 YELLOW로 고정

해석: 엔진은 강하게 살아 있다. defeat_mechanic이 정의된 작품답게 큰 패배 블록(B16/B47/B55/B63)이 계획적으로 들어와 있고 직후 블록에서 회복이 일어나지만, spec §2.3은 "같은 블록 안 회수"를 요구하므로 단발 무수확 8블록이 모두 ceiling을 깬다. spec §2.3 강성 룰상 **no-cider 블록이 하나라도 남아 있는 한 ceiling은 그대로 유지**되며, 일부만 보강해서는 ceiling이 풀리지 않는다. 한 단계 위 grade로 가려면 8블록 전수 surgical 보강이 필요하다.

## 8. Top 3 Repair Units

중요 전제: spec §2.3에 따라 **no-cider 블록이 8개 전부 남아 있는 한 YELLOW ceiling은 유지된다**. 아래 3건은 ceiling을 즉시 해제하는 패치가 아니라, 가장 영향이 큰 자리부터 정리하기 위한 우선순위 큐다. 잔여 5블록(B23, B28, B34, B55, B63)도 같은 spec rule상 모두 처리되어야 ceiling이 비로소 풀린다. 모두 read-only 진단 — 실제 mutation은 본 audit 범위 밖.

1. **TR Block 4 (조준된 패배) — 같은 블록 안 next-card 1조각 추가**
   - 현재: -15억 손실 + "첫 의심" 인사이트만
   - 제안: 같은 블록 안에서 (a) 오지혁이 단기 행사 라인 1건을 그 밤 안에 묶어 들어오거나, (b) 강이현 후속 부킹 한 건이 행사 직후 살아남거나, (c) 윤서아가 무대 직전 짧은 리딩으로 PD 한 명을 따로 잡는 micro-token 중 1개를 회수. WG `crisis_doctrine` "즉시 보상" + custom_rules "반격 예약 없는 손해 금지"를 직접 만족시키는 가장 비싼 수정.
   - 영향: 첫 블록 윈도우 안 cider 깨짐을 막아 P0 게이트 인접 자리의 위험을 줄인다. ceiling 자체는 잔여 7블록이 남아 있는 한 유지된다.

2. **TR Block 16 (배신) — same-block 토큰 1조각 추가**
   - 현재: -58억 + 한도윤 정체 폭로(정보형)
   - 제안: 같은 블록 안에서 (a) 한도윤 손에서 빠져나간 계약권/예산권 1조각이 회수되거나, (b) 외부 동맹(서민재 또는 오지혁) 1명이 명시적으로 태하 편 선언을 같은 블록 안에서 등록. 정보형 폭로 + 미세 권력 토큰 1조각 조합이면 충분.
   - 영향: 2섹터 단발 무수확 1건 정리. ceiling은 잔여 6블록이 남아 있는 한 유지된다.

3. **TR Block 47 (1차 라이프스타일 IP 위기) — same-block 회수 카드 1조각 추가**
   - 현재: -136억 + "타격 자리라는 인식"
   - 제안: 같은 블록 안에서 (a) F&B 또는 윤서아 라인 IP 1조각의 단기 보호 협약, (b) 박재인 팬덤 플랫폼이 같은 블록에서 작은 supportive metric 1개 회수, (c) 회사 내부 인사 1명의 명시적 잔류 선언 중 1개. WG `crisis_doctrine` "최소 피해 통제 + 즉시 다음 입장권" 그대로.
   - 영향: 5섹터 단발 무수확 1건 정리. ceiling은 잔여 5블록이 남아 있는 한 유지된다.

비고: 나머지 5개 no-cider 블록(B23, B28, B34, B55, B63) 역시 ceiling 해제를 위해 동일한 same-block 토큰 패치가 필요하다. 이 중 B55/B63은 defeat_mechanic이 의도적으로 작동하는 자리라 손대기 전에 BI defeat_mechanic 정의와 cross-check가 선행되어야 한다. B23/B28/B34는 위 3건과 같은 패턴으로 정리 가능하지만 영향도가 상대적으로 낮아 후순위로 둔다. 8블록 전수 정리가 끝나야 ceiling이 풀리고 재감리에서 GREEN/GREENPLUS 재배치 후보가 된다.

## 9. Concise Rationale

- pair 03은 P0 6게이트 전부 PASS (gate 6은 narrow evidence — spec v1상 PASS/FAIL only라 PASS로 정규화), P1 총점 17/20.
- BI CommercialCode의 cider_point / attitude는 TR 1~3 안에서 즉시 작동하고, success_device(패키지 전략)도 B3 협상 장면의 씨앗 형태로 visibly alive, defeat_mechanic은 후반 패배 블록 설계의 뼈대로 살아 있다. gate 6의 narrow evidence 약함은 P1 BI amplification axis 1점으로만 반영.
- 첫 블록 cider, protagonist-only proof, evaluation revision, reward token, gate linkage anchor는 모두 TR blocks 2~6 안에서, BI/TR early alignment anchor는 TR blocks 1~3 안에서 확보 가능. B1 의존 없음, B7+ rescue 없음.
- full-block cider scan에서 single-block no-cider 블록 8개(4, 16, 23, 28, 34, 47, 55, 63)가 발견된다. 모두 단발이라 drought는 1에 그치지만, spec §2.3 강성 룰 ("any no-cider block → YELLOW ceiling")이 ceiling으로 직접 작용한다.
- defeat_mechanic이 정의된 작품 특성상 큰 패배 블록 4종(B16/B47/B55/B63)은 의도된 설계이지만, spec은 다음 블록 회복이 아니라 same-block 토큰을 요구한다. 따라서 grade는 점수가 아니라 cap rule로 결정된다.
- WG `custom_rules` "반격 예약 없는 손해 금지" + `crisis_doctrine` "즉시 보상"이 명시되어 있는데, B4를 비롯한 8 블록은 이 자체 contract를 어기는 자리라 surgical 수정의 명분도 분명하다.
- 최종 판정: **YELLOW**. spec §2.3 강성 룰상 no-cider 블록이 1개라도 남아 있는 한 ceiling은 유지되며, 8블록 전수 same-block 토큰 보강이 끝나야 ceiling이 풀린다. B4/B16/B47만 손대는 부분 보강은 ceiling 해제 효과가 없고, 잔여 5블록(특히 B55/B63은 BI defeat_mechanic 재확인 선행)까지 모두 정리되어야 재감리에서 GREEN/GREENPLUS 재배치 후보가 된다.

read-only true benchmark audit complete; no pair files mutated
