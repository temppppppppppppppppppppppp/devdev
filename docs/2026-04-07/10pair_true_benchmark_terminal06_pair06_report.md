# 10pair True Benchmark Terminal 06 Pair 06 Report

Date: 2026-04-07
Status: active
Audit Type: read-only true benchmark audit
Spec: `material_ssot/00_governance/production-pair-benchmark-spec-v1.md`
Doctrine: `material_ssot/20_pitch/cider-doctrine-v1.md`
Parent Order: `docs/2026-04-07/10pair_true_benchmark_10terminal_opus_order.md`
Prompt: `docs/2026-04-07/10pair_true_benchmark_terminal06_pair06_prompt.md`

## Pair Identity

- pair id: `06`
- slug: `gatekeeper_heir`
- family: `blockguide`
- BI: `bible/06_bi_gatekeeper_heir.json`
- TR: `treatments/06_gatekeeper_heir_tr_block_070_draft.json` (70 blocks)
- WG: `work_guards/06_gatekeeper_heir.yaml`
- one_line_truth (WG): "돈 대신 권한을 요구하는 후계자가 죽은 자산과 묻힌 사람을 살려 병목을 관문으로 바꾸고, 그룹 전체가 자신의 관문을 거치지 않으면 움직이지 못하는 운영제국을 만든다"
- canonical exemplar reference: spec §9 currently lists this pair as the **proof-scene precision benchmark**; this audit re-tests that label against the strict full-block cider rule.

## Evidence Anchor Table

| Anchor | Source | Value (semantic extract) |
| --- | --- | --- |
| `one_line_truth` | WG `work_identity.one_line_truth` | 돈 대신 권한 / 죽은 자산·묻힌 사람 재배치 / 병목→관문 전환 |
| `mandatory_scene_engines` | WG | (1) 딜 테이블에서 돈이 아니라 권한 요구 (2) 죽은 장비·묻힌 인재 재배치로 고객 재심/인증 통과 (3) 성과 직후 보상 부착 + 다음 섹터 입장권 |
| `evaluation_thresholds` | WG | 1화 즉시 고평가, 3화 내 재심 통과·간판 폭발, Block 1 완료 시 지휘권·인사권·직보권, 큰 피해 뒤 즉시 다음 카드 |
| `tracking_slots` | WG | 관문 전환 진척, 권한 회수, 저평가→고평가 전환, 그룹 통행 경로 연결도 |
| `custom_rules` | WG | 위기는 우선순위 선택권 증명, 반격 예약 없는 손해 금지, 보상은 현금흐름·사람·규칙 중 체감형, 다음 섹터는 이전 보상으로만 열림 |
| `forbidden_flattenings` | WG | 회개물·자기연민·고유성 없는 승리·활약 후 보상 누락·위기 무대응 등 |
| `cider_point` (BI `CommercialCode`) | BI | 저평가된 자산과 묻힌 인재를 읽어 재배치로 전환하는 능력자 |
| `success_device` (BI `CommercialCode`) | BI | 돈이 아니라 권한·자리·이름. 총애를 권한으로, 권한을 시스템으로, 시스템을 표준으로. 같은 시대 보상을 동시대에 받는다 |
| early promise (BI `MetaInfo.logline`) | BI | 회사가 아니라 관문을 먹는 후계자, 죽은 자산과 묻힌 인재로 그룹 운영체계 재설계 |
| BI/TR conversion alignment | BI vs TR Block 1~3 | TR Block 1~3에서 cider_point/success_device가 그대로 작동: 도윤이 회장 비서실의 보호용 손자 분류를 깨고 회장 독대 10분→비공개 위기 선독→돈 대신 권한 요구로 직결 |

## P0 Hard Gates

| Gate | Anchor (TR blocks 2~6 only for gates 1~4) | Verdict |
| --- | --- | --- |
| 1. first-block visible cider | TR Block 2 (회장실 10분 + Lv1 독대권 확보) → TR Block 3 (그룹 급소 선독, 회장의 평가 전환) → **TR Block 4 (세원정밀 6개월 지휘권 + 인사 이동권 3명 + 회장 직보권 = Lv2)**. 첫 visible token이 정확히 strict window(2~6) 안에서 발화. | **PASS** |
| 2. protagonist-only proof | TR Block 3 — 검사 7공정 미세균열 + X-ray 장비 + 결함 라이브러리 + 세원전자 비공개 재심 회의 일정을 한 번에 연결. 회귀 기억과 배치 조감이 결합한 도윤 고유 능력으로만 가능. WG `protagonist_weapon` 1·2번 항목과 1:1 매칭. | **PASS** |
| 3. evaluation revision | TR Block 3 — 강석명: "귀여운 손자" → "그룹 급소를 먼저 본 인물"로 즉각 전환, 남기현: "일정표 바깥으로 새어 나가려는 위험한 변수"로 재분류. TR Block 4 — 강석명: "시험 가능한 권한만 골라 쥐는 경영자". WG `observer_tiers` 1~2단계가 동일 윈도에서 발화. | **PASS** |
| 4. visible reward token | TR Block 4 — 세원정밀 6개월 지휘권(운영권 토큰) + 인사 이동권 3명(인사권 토큰) + 회장 직보권(직보 토큰) 세 가지 동시 부착. WG `mandatory_scene_engines` 1번(권한 요구 장면)과 BI `success_device`(돈이 아니라 권한)가 동일 블록에서 토큰화. | **PASS** |
| 5. block1 → block2 gate linkage | TR Block 4의 지휘권 토큰이 TR Block 5(세원정밀 창고 단독 정찰)→TR Block 7(48시간 내부자원 미세균열 보고서)→TR Block 8(고객 인증 재심 통과)→TR Block 9(장비 분야 공식 담당, 6개월→상시) 라인을 직접 연다. TR Block 7+는 retroactive backfill이 아니라 Block 4 토큰의 정상 행사 라인이다. | **PASS** |
| 6. BI/TR early conversion alignment | TR Block 1에서 BI `success_device`(돈이 아니라 권한·자리·이름)가 즉시 발화: 도윤이 합격 통지서 자리에서 축하·유학·돈을 거절하고 회장 독대 10분만 요구한다. TR Block 2에서 같은 success_device가 한 단계 더 구체화되어 회장실 10분 토큰으로 환산되고, 비서실 일정표라는 보호 분류가 깨진다. TR Block 3에서 BI `cider_point`(저평가 자산·묻힌 인재 재배치) 라인이 발화: 검사 7공정 미세균열·X-ray·결함 라이브러리 선독으로 강석명의 평가가 "귀여운 손자→그룹 급소를 먼저 본 인물"로 공식 갱신된다. BI logline의 "회사가 아니라 관문을 먹는다"가 TR Block 1~3 안에서 summary echo가 아니라 능동 amplification으로 작동. | **PASS** |

P0 결과: **6/6 PASS** — Block 1 conversion 자체는 spec §9의 "proof-scene precision benchmark" 수식을 그대로 정당화한다. P0 라인만 보면 GREENPLUS 후보이지만, 아래 full-block cider scan이 ceiling을 제한한다.

보강 메모 (gate 6 관련): TR Block 4의 지휘권+인사권+직보권 트리플 토큰은 gate 6의 anchor로는 사용하지 않았다. gate 6은 BI early promise / cider_point / success_device가 TR 1~3 안에서 살아 있는지만 검증한다. Block 4는 gate 1·4의 정식 anchor이며, gate 6에서는 BI 약속이 1~3에서 발화한 뒤 정상 행사된 후속 토큰으로만 참고된다 (retroactive backfill 아님).

## Full-Block Cider Scan

총 TR block 수: **70**
no-cider block 수: **27**
no-cider block 번호: **5, 6, 10, 11, 12, 14, 15, 21, 22, 23, 24, 25, 30, 31, 34, 35, 40, 41, 44, 45, 50, 53, 55, 61, 62, 64, 65**
longest no-cider drought 길이: **5 blocks** (TR Block 21~25, 시스템 단계 발견·시범 무력화·quiet 구간)

Window summary (block_no / has_cider 표기):

- **1~10**: 1✓ 2✓ 3✓ 4✓ **5✗** **6✗** 7✓ 8✓ 9✓ **10✗**
  - Block 1~4 = 첫 관문 토큰 라인(독대권→Lv2 지휘권). Block 5는 세원정밀 단독 정찰(setup-only, "변동 없음"). Block 6은 첫 좌절(현장 협조 부재, pain). Block 7~9에서 즉시 회수. Block 10은 다음 병목 발견(setup-only).
- **11~20**: **11✗** **12✗** 13✓ **14✗** **15✗** 16✓ 17✓ 18✓ 19✓ 20✓
  - Block 11~12 = 소재 위기 정찰. Block 13 산학 합의가 첫 외부 파트너 토큰. Block 14 시험배치 -3천만 원 패배, Block 15 quiet 원인 분석. Block 16~20에서 두 번째 시험 성공→미즈카미 균열→Lv3 조달 공동결재권으로 회수.
- **21~30**: **21✗** **22✗** **23✗** **24✗** **25✗** 26✓ 27✓ 28✓ 29✓ **30✗**
  - **이 윈도에 audit 전체에서 가장 긴 5블록 no-cider drought 발생**. 시스템 단계 발견(21 사람 의존 구조)→MES 발굴(22)→삼각구조 결성(23)→시범 무력화(24)→감정 quiet(25). Block 26 윤태석 동의가 첫 reevaluation receipt로 회복. Block 30은 다음 단계 진입점(setup).
- **31~40**: **31✗** 32✓ 33✓ **34✗** **35✗** 36✓ 37✓ 38✓ 39✓ **40✗**
  - 공장 밖 단계: 31 이정수 발굴(setup), 32~33에서 세원로지스 합류·보험 endorsement, 34 선적 실패, 35 quiet 항만 정찰. 36~39에서 HS 코드 정정·직항 확보·서비스 크레딧 전환. 40은 다음 단계 진입점.
- **41~50**: **41✗** 42✓ 43✓ **44✗** **45✗** 46✓ 47✓ 48✓ 49✓ **50✗**
  - 증설 단계: 41 우회 경로 발견, 42~43 세원유틸리티/백창수 합류, 44 인허가 반려, 45 quiet 프레임 전환. 46~49에서 야간전력 패키지→투심위 조건부 의결→Lv6 증설 승인권. 50 다음 단계 진입점.
- **51~60**: 51✓ 52✓ **53✗** 54✓ **55✗** 56✓ 57✓ 58✓ 59✓ 60✓
  - 자본 규율 단계: 51~52 리스 구조 설계, 53 첫 부도 패배, 54 MES 모니터링 반격, 55 quiet 서비스 조건표 초안. 56~60 인증 작업반→JV→PEF 등장→Lv7 금융/표준 권한.
- **61~70**: **61✗** **62✗** 63✓ **64✗** **65✗** 66✓ 67✓ 68✓ 69✓ 70✓
  - 관문 제국 단계: 61 회장 건강·정우석 공식 제안(감정 마비), 62 방어 분석(자본 변동 없음, 토큰 없음), 63 이사회 즉결 저지. 64 holdco 승인 실패(감정의 벽), 65 quiet 조건표 재설계. 66 공신 3인 자발 서명→67 holdco 상정→68 이사회 통과→69 후계자 실권 확정→70 관문 제국 캡스톤.

분류 기준: spec §2.3 "has_cider=true는 같은 블록 내에서 reader-countable payback(visible reward token / weighted reevaluation receipt / protection receipt / authority·access shift / 같은 블록의 통증을 실질 상쇄하는 recovery asset / 다음 카드·다음 게이트 영수증)이 최소 1개". 위 27개 block은 명시적으로 "보상은 없다 / 자본 변동 없음 / 정찰 완료 / 발견 / quiet" 표현을 본문에 직접 적고 있고, 다음 블록 이전에는 reader-countable payback이 닿지 않는 setup-only / pain-only / explanation-only 구조다.

## Active Cap Rules

- **`any no-cider block in the full-block cider scan: YELLOW ceiling`** — 트리거됨 (27개 no-cider block).
- **`rewardless pain blocks 2 in a row: GREEN ceiling`** — 트리거됨 다수: (5,6) (11,12) (14,15) (21,22), (22,23), (23,24), (24,25), (30,31), (34,35), (40,41), (44,45), (61,62), (64,65). YELLOW ceiling이 우선 적용되어 grade 결정에는 종속.
- **`no-cider drought 6+ blocks: YELLOW ceiling`** — 트리거되지 않음 (max drought = 5).
- **`major defeat without next card in the same or next block: YELLOW ceiling`** — **트리거됨 (재판정)**. spec §6의 문언("same or next block")을 strict reading하면 quiet 1블록을 끼우는 패턴은 미트리거가 아니라 재판정 대상이다. 패배 직후 블록(quiet)에 reader-countable next card가 닿지 않으면 다음 카드가 두 블록 뒤에 도달하므로 same/next 윈도를 벗어난다. 다음 5건이 strict reading 하에서 트리거된다:
  - **Block 14 (시험 배치 -3천만 원 패배) → Block 15 (quiet, 패배 원인 특정만, no card) → Block 16 (두 번째 시험 성공)**: next card가 +2 블록에서 도달.
  - **Block 24 (현장 반발 시범 무력화) → Block 25 (quiet, 프레임 전환, no card) → Block 26 (윤태석 동의)**: next card +2.
  - **Block 34 (선적 실패, 납기 지연 4일) → Block 35 (quiet, 항만의 밤, no card) → Block 36 (HS 코드 정정 3일 회수)**: next card +2.
  - **Block 44 (인허가 반려) → Block 45 (quiet, 프레임 전환, no card) → Block 46 (야간전력 패키지)**: next card +2.
  - **Block 64 (holdco 승인 실패, 의리의 벽) → Block 65 (quiet, 조건표 재설계, no card) → Block 66 (공신 3인 자발 서명)**: next card +2.
  - 비교 (트리거 안 됨): Block 6 → 7 win (next), Block 53 → 54 win (next).
  - 효과: 본 cap은 YELLOW ceiling이며, `any no-cider block` 캡이 이미 동일 ceiling을 강제하고 있어 grade를 낮추지는 못하지만 ceiling 강도와 수리 우선순위에 가중을 더한다.
- 그 외 cap rules (asset-only / stupid opposition / generic domain / passive protagonist) — 트리거되지 않음.

## P1 Score Table

| Axis | 점수 | Anchor 근거 |
| --- | --- | --- |
| protagonist innocence | **2** | TR Block 1의 몰락은 비서실/공신 세대의 보호용 후계 분류와 구세대 정답에서 비롯; 도윤 자신의 게으름·자초가 아님. WG `forbidden_flattenings`의 "회개물 스타트" 금지와 일치. |
| protagonist-only proof clarity | **2** | TR Block 3 검사 7공정 미세균열 + X-ray + 결함 라이브러리 결합. 회귀 정보 + 배치 조감으로만 가능. |
| evaluation revision visibility | **2** | TR Block 3·4·8·9에서 강석명 / 한재용 / 야마모토 / 임원회의 등 다층 observer가 공식 reevaluation. WG `observer_tiers` 1~5단 모두 활성. |
| visible reward token strength | **2** | 지휘권·인사권·직보권(B4) → 조달 공동결재권(B20) → 데이터/시스템 권한(B29) → 증설 승인권(B49) → 금융/표준 권한(B60) → 후계자 실권(B69)의 7단 토큰 사다리. |
| block1 → block2 linkage | **2** | Block 4 토큰이 Block 5~9 라인을 직접 열고, 각 아크 마무리 토큰이 다음 아크의 진입점으로 환산되는 패턴이 6아크 반복. |
| rational opposition | **2** | 이관식(20년 거래 관성) / 최병수(현장 30년 정답) / 정우석(스택 가치 정확히 읽는 PEF) — 모두 incentive·시대 정답 기반, cartoon 아님. WG `role_fit_constraints`의 공신 캐리커처 금지와 정합. |
| domain truth density | **2** | HS 코드 9031/8486 정정, 보험 약관 면책 endorsement, 야간전력 45% 절감, MES 자동보정, 데이터센터→후공정 냉각 변환, holdco 분리 비용 구조 등 lane swap이 어려운 구체 지식. |
| repeatable loop clarity | **2** | "묻힌 계열사 → 묻힌 사람 → 자리값 읽기 → 같은 블록 보상" 루프가 세원정밀 / 세원소재 / 세원IT / 세원로지스 / 세원유틸리티 / 세원캐피탈 6번 반복. |
| BI amplification power | **2** | BI `cider_point`·`success_device`·`logline`이 TR 매 아크의 capital_target에 1:1 환산. summary echo 아님. |
| blockwise cider continuity | **0** | 27개 no-cider block, 최장 drought 5블록. spec §5 표의 `0` 정의("one or more no-cider blocks")에 명시적으로 해당. |

총점: **18 / 20**

## Provisional Grade

**YELLOW**

- 산술 총점은 18 (GREENPLUS 구간 17~20)이지만, spec §6 cap rule "any no-cider block in the full-block cider scan → YELLOW ceiling"이 강제로 적용된다.
- spec §2.3 마지막 문장은 이 규칙이 의도된 강한 house rule임을 명시한다: "a production pair does not earn GREEN or GREENPLUS by asking the reader to coast through rewardless blocks".
- spec §10의 audit discipline에 따라 P0 6/6 PASS가 GREEN 이상을 보장하지 않으며, full-block cider scan의 27 no-cider block이 ceiling을 그대로 적용한다.
- 추가로 위 §Active Cap Rules에서 재판정한 `major defeat without next card in the same or next block` 캡이 5건(Block 14·24·34·44·64) 트리거되어 동일 ceiling을 다중 강화한다.
- **ceiling 유지 원칙**: spec §6·§8.3은 no-cider block 카운트가 0이 되기 전까지 YELLOW ceiling을 유지한다. 부분 수리(예: drought 분쇄, 일부 블록 토큰 부착)로 카운트가 27 → 10 또는 27 → 3으로 줄어도 ceiling은 그대로다. **GREEN 이상으로의 재진입은 no-cider block 수 = 0 (그리고 모든 cap rule 미트리거) 조건을 동시에 충족할 때만 가능하다.**
- 이 결과는 spec §9가 이 pair를 "proof-scene precision benchmark exemplar"로 인용한 것과 충돌한다. 충돌의 의미: P0 first-block conversion 영역(TR 1~6 + 7~9 회수 라인)에서는 여전히 exemplar이지만, 시스템 단계(21~25)와 매 아크 전환부(30, 31, 40, 41, 50)의 setup-only / quiet 누적, 그리고 매 패배 직후 quiet 1블록 패턴(14·24·34·44·64)이 strict full-block 룰의 비용을 그대로 받는다. WG와 BI는 다 살아 있고, 블록당 토큰 강도도 높다 — 단, doctrine이 요구하는 것은 "강한 토큰 몇 개"가 아니라 "모든 블록의 same-block payback"이다.

## Top 3 Repair Units or Alias Note

YELLOW이므로 spec §10·§11에 따라 bounded top-3 repair units (full-wave surgery 금지). 단, 아래 수리는 ceiling을 푸는 것이 아니라 ceiling 강도와 수리 우선순위를 줄이는 것이며, **no-cider block 수가 0이 되기 전까지 YELLOW ceiling은 유지된다**:

1. **패배 직후 quiet 1블록 패턴 분쇄 (TR Block 14·15 / 24·25 / 34·35 / 44·45 / 64·65)**
   - 문제: 위 §Active Cap Rules에서 재판정한 5건의 `major defeat without next card in same or next block` 캡 트리거. quiet 1블록이 패배와 회복 사이에 끼어 next card가 +2 블록 위치로 밀린다. 이 패턴은 동시에 6개 quiet 블록 중 5개를 차지하므로 가장 큰 ceiling 가중치를 갖는다.
   - 수리: 패배 블록(14·24·34·44·64) 본문 내 또는 직후 quiet(15·25·35·45·65)에 same-block reader-countable card 1개 부착. 예) Block 15에 "윤태석이 김순호 90초의 메모를 같은 블록에서 도윤에게 직접 건네는 protection receipt", Block 25에 "공재홍이 다음 시범 범위에 대한 1줄 묵인을 같은 블록에서 흘리는 enemy stance shift", Block 65에 "박진섭이 같은 블록 안에서 사전 서명 1장을 미리 남기는 next-card receipt". 프레임 전환은 그대로 두고 receipt만 부착.

2. **시스템 단계 5블록 drought 분쇄 (TR Block 21~25)**
   - 문제: audit 전체 최장 drought이며, spec §6의 6+ 캡까지 1블록 차이로 근접. 21(사람 의존 발견)→22(MES 발굴)→23(삼각구조 결성)→24(시범 무력화)→25(감정 quiet)가 setup·discovery·pain·quiet만으로 5블록 연속.
   - 수리: Block 23 시범 범위 확정 시점에 same-block 토큰 1개 추가 — 예) 강석명·남기현 라인의 "데이터/시스템 한정 사전 열람권 1단계" 또는 윤태석 부재 시 수율 낙폭 측정 데이터를 회장 직보 라인에 같은 블록에서 등록(공식 evaluation revision 영수증). drought를 21~22와 24~25 두 개 짧은 구간으로 잘라 6+ 캡 영구 제거.

3. **아크 전환 setup blocks 묶음 (TR Block 10·11·12, 30·31, 40·41, 50)**
   - 문제: 매 아크 끝/시작에 "다음 병목 발견 + 묻힌 계열사 정찰" 2~3블록이 자본 변동 없음으로 반복. 특히 10~12는 3블록 연속 no-cider.
   - 수리: 전환 블록당 same-block 토큰 1개 — 예) Block 11에서 황정민의 "특허 시험 배치 사전 동의서" 또는 오서윤의 "조달 데이터 비공식 열람 권한" 같은 작은 access shift 1개. 전환 블록이 "다음 관문 발견 + 지금 한 가지 카드 확보" 구조로 바뀌면 setup-only 분류에서 빠진다.

(spec §11: 수리 후 반드시 re-grade. 부분 수리는 no-cider 카운트와 cap 트리거 수를 줄여 ceiling 강도와 수리 우선순위를 낮추지만, **카운트가 0에 도달하고 모든 cap rule이 미트리거가 되기 전까지 YELLOW ceiling은 그대로 유지된다.**)

## Concise Rationale

- gatekeeper_heir는 P0 6게이트와 P1 대부분 축에서 spec §9가 인용한 exemplar 위상을 그대로 정당화한다. Block 4의 권한 토큰 트리플은 blockguide family에서 가장 깨끗한 first-block conversion 사례 중 하나이고, BI `cider_point`·`success_device`·logline이 TR Block 1~9에 그대로 환산된다.
- 그러나 strict full-block cider scan은 27개 no-cider block(전체의 38.6%)을 적출한다. 매 아크 끝/시작의 정찰·발견 setup 블록과 quiet 프레임 전환 블록이 same-block reader payback 없이 닫힌다는 점, 그리고 매 패배(14·24·34·44·64) 직후 quiet 1블록이 끼면서 next card가 +2 블록으로 밀린다는 점(`major defeat without next card in same/next block` 캡 5건 트리거)이 ceiling을 다중으로 강제한다.
- 따라서 grade는 P1 18점이라는 산술 총점과 무관하게 spec §6·§8.3의 cap rule에 의해 **YELLOW**로 결정된다. 이는 hidden proof / 다음 카드 / 후속 회수에 의존해 미달 영수증을 backfill 하는 reading을 doctrine이 명시적으로 거부한 결과이며, watchpoint("hidden proof or delayed reveal cannot hide a missing same-block receipt; require the proof scene to convert into visible entry-ticket or reevaluation on time")를 그대로 적용한 결과이기도 하다.
- 이 audit는 work_guard와 BI를 P0 게이트 anchor로 사용했지만, 어느 게이트나 cap rule에서도 work_guard·BI가 빠진 TR 영수증을 대체하도록 허용하지 않았다.
- 운영 권고: spec §9의 "proof-scene precision benchmark" 라벨은 first-block에 한정해서만 유지하고, full-block 라벨로 확대되지 않도록 alias 문서에 분리 표기 필요. 위 Top 3 수리 단위는 ceiling 강도와 cap 트리거 수를 줄이는 bounded 작업이며, **no-cider block 카운트가 0에 도달하기 전까지 YELLOW ceiling은 그대로 유지된다**. GREEN 이상으로의 재진입은 부분 수리만으로 보장되지 않는다.

read-only true benchmark audit complete; no pair files mutated
