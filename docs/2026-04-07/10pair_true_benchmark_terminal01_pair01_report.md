# 10pair True Benchmark Terminal 01 Pair 01 Report

Date: 2026-04-07
Status: active
Mode: read-only true benchmark audit
Audited Pair: `01` (canonical_v1)
Family: `blockguide`

## Pair Identity

- pair id: `01`
- slug / title: `투자물_골든_카나리아 테스트`
- BI: `bible/01_bi_투자물_골든_카나리아 테스트_canonical_v1.json`
- TR: `treatments/01_tr_투자물_골든_카나리아 테스트_canonical_v1.json`
- WG: `work_guards/01_투자물_골든_카나리아 테스트_canonical_v1.yaml`
- canonical_v1 suffix preserved on all three axes; no slug-normalize applied
- TR `_total_blocks`: 60 (manifest carries `01~10` of canonical pair set; this audit windows up to `51~60` only)

## Evidence Anchor Table

| Anchor | Source | Locator |
| ---- | ---- | ---- |
| `one_line_truth` | WG | `work_identity.one_line_truth` (line 5) — "고독사한 재벌가 막내가 18년치 경제 캘린더와 exit 설계 감각으로 …" |
| early promise | WG `evaluation_thresholds[0]` | line 79 — "Block 2~4 내 원유 proof scene과 PB tone shift 1회 이상" |
| `success_device` (semantic) | WG `protagonist_weapon` + `mandatory_scene_engines` | lines 6–9, 54–58 — `cycle reading` + `이벤트 선점 → proof 회수` |
| `cider_point` (semantic) | WG `protagonist_evaluation.admiration_axes` + `evaluation_thresholds` | lines 60–65, 78–82 — observer tier `tone shift` + `자산→딜 접근권/운용권` 환전 |
| `CommercialCode` (semantic) | WG `business_axes` + `control_axes` | lines 10–21 — `매크로 선점 / CDS / OTC / TWAP / 패밀리오피스 운용권` |
| `mandatory_scene_engines` | WG | lines 54–58 — 4 engines: 이벤트 선점-proof, 익절 타이밍 강제 tone shift, 다음 cycle 입장권 확보, 자산→방화벽/패밀리오피스 환전 |
| `evaluation_thresholds` | WG | lines 78–82 — early oil proof, ARC1 외부 재평가, 자산→딜접근권/운용권, 가문 실사 자료 회수 |
| `custom_rules` | WG `custom_rules` | lines 106–112 — 출구 우선, 위기=유동성 증명, 반격 예약 없는 손해 금지, 회귀=정보 비대칭, 자산은 반드시 환전, 가족 도움≠운용권 |
| `tracking_slots` | WG | lines 49–53 — 선매·선매도 정확도 재평가, 다음 cycle 입장권, 방화벽 강화, 가문이 규칙 안으로 들어옴 |
| TR Block 2 oil proof anchor | TR | line 112 (Block 2 `검은 황금`) — WTI 6월물 3배 레버리지 진입, 이란 핵 농축 재개 후 PB 선전화 |
| TR Block 3 PB tone shift anchor | TR | line 220 (Block 3 `중동의 불씨`) — 에콰도르 옥시덴탈 강제 해지 직후 부분 익절, "어떻게 아셨습니까" + 증권가 첫 소문 |
| TR Block 4 gold pivot | TR | line 332 (Block 4 `금의 귀환`) — 금 620→680 익절, 박성호 절대 신뢰 |
| TR Block 5 first graduation | TR | line 442 (Block 5 `첫 번째 졸업`) — 50억 결산, 가족 회식에서는 invisibility 선택 |
| TR Block 6 KOSPI rally | TR | line 564 (Block 6 `코스피의 봄`) — 30→70억, PB 맹목 추종 |

## P0 Hard Gates

re-scored against `production-pair-benchmark-spec-v1` §4.1 — 6 hard gates, scope `TR blocks 2~6` only. `TR block 1` may be opening setup, `TR block 7+` may only confirm downstream linkage for gate 5.

| Gate | Spec definition | Verdict | TR anchor (블록 번호 + line) |
| ---- | ---- | ---- | ---- |
| P0-1 first-block visible cider | `TR blocks 2~6`에 reader가 셀 수 있는 visible reward 1개 이상 | PASS | TR B2 (line 118) "취미 투자 깔보던 톤이 사라졌다 + 15→18억 미실현"; TR B3 (line 226) 에콰도르 적중 후 부분 익절 5억 확정 + 증권가 첫 소문 |
| P0-2 protagonist-only proof | `TR blocks 2~6`이 "저건 쟤라서 가능했다"를 부정 불가능하게 만든다 | PASS | TR B2 (line 116–117) 이란 핵 재개 시점·가격 정확 선점; TR B3 (line 224–225) "에콰도르가 터진다" 사전 명시 후 5월 16일 옥시덴탈 강제 해지 적중; TR B4 (line 336–337) 두 달 횡보 인내 후 연준 금리 멈춤 적중 — cycle reading은 한시우 고유 무기 |
| P0-3 evaluation revision | `TR blocks 2~6` 안에서 weight 있는 인물이 주인공을 재평가 | PASS | TR B2 (line 129–130) 박성호 "당혹 → 큰 손 가능성 재평가"; TR B3 (line 226, 234–243) 박성호 "경외", 증권사 리스크관리팀 압박 → 입다묾, 증권가 "재벌가 막내가 원유로 찍었다" 첫 소문; TR B4 (line 347–350) 박성호 "절대 신뢰" |
| P0-4 visible reward token | `TR blocks 2~6`에 blockguide 토큰 1개 이상 (name call / seat / CC / report line / TF / approval / ownership / entry ticket) | PASS (thin) | TR B3 (line 226) 증권가 소문 = reputation token; TR B6 (line 587) "골드만삭스 아시아 데스크 연락처 확보" = entry-ticket token. 두 토큰 모두 명시되어 게이트는 통과하나 어느 쪽도 단일로 강하지 않고 자산 숫자(20→70억) 옆에 한 줄로만 박혀 있어 cap rule "early reward is asset-only" 경계에 근접 |
| P0-5 block1 → block2 gate linkage | `TR block 6` 이하에서 얻은 토큰이 다음 게이트를 연다 — `TR block 7+`는 confirmation으로만 인용 | PASS | TR B6 (line 587, 661–664) 골드만 라인 확보 토큰이 → TR B7 `미국의 그림자` (line 676, 681) "CDS 거래 루트 확보"를 직접 연다. B7은 backfill이 아니라 B6 토큰의 downstream confirmation으로만 인용됨 |
| P0-6 BI/TR early conversion alignment | BI `grand_objective` / `cider_point` / `success_device`가 TR `block 1~3`에서 가시적으로 살아있음 | PASS | BI line 10 `grand_objective` "2006~2024 경제 이벤트로 20억을 135조로 키우고, 형들의 몰락과 시장 광기를 통제권과 자산 방화벽으로" → TR B1 (line 11) 회귀 직후 "사업 하겠습니다 / 그룹 돈 한 푼 안 받겠습니다" 선언으로 방화벽 첫 줄을 그음. BI line 25 `cider_point` "모두가 늦었다고 할 때 먼저 사고 먼저 파는 정확한 출구 설계" → TR B2 (line 116–118) 이란 핵 재개 선점 + B3 (line 224–226) "에콰도르가 터진다" 사전 발화 후 부분 익절로 곧장 환전. BI line 26 `success_device` "이득 구조 읽기, 캘린더 선점, 디스트레스 유동성 우위, recognition 서사" → TR B2~B3에서 캘린더 선점 + 박성호 PB recognition 서사가 동시 가동. 세 BI 항목이 모두 TR block 1~3에 1:1로 살아 있음 |

P0 verdict: **6 / 6 PASS**, 다만 P0-4가 thin pass (단일 토큰 강도가 약하고 자산 증가에 묶여 있음). Opening Innocence Rule (§4.3) 별도 점검: TR B1 회귀 전 몰락의 주인은 형들의 후계 싸움 → 그룹 분열 → 막내 찬밥 = `inherited bad frame / wrong seat`이며 laziness 또는 self-inflicted collapse가 아님. **innocence rule PASS**.

## Full-Block Cider Scan

scope: TR blocks 1~60 (full)

method: per block, mark `cider` if reward/power_shift contains either (a) observer tier가 가시적으로 평가를 갱신하거나 (b) 자산 증가가 다음 접근권/운용권/방화벽 토큰으로 환전된 경우. 단순 자산 숫자 증가만으로는 cider로 세지 않음.

window summary (cider count / blocks scanned):

- `1~10`: 7/10 cider — strong opening; no-cider at B1, B5, B8 (B1 declaration only / B5 family-mocking calm-before-storm / B8 CDS 진입 후 대기)
- `11~20`: 9/10 cider — Lehman arc spike (B11~15 연속), no-cider at B19 (BTC OTC 매집, OTC 딜러는 단순 "미친놈" 갱신 없음)
- `21~30`: 8/10 cider — 카카오/YG/알리바바/넷마블 환전 dense; no-cider at B25 (Mt Gox 추가 매집), B27 (ETH OTC 확보)
- `31~40`: 6/10 cider — `긴 drought` 구간; no-cider at B31 (크립토 윈터 관망), B32 (테슬라 매수 prep), B33 (포지션 구축 완료), B34 (헷지 prep "곧 온다")
- `41~50`: 9/10 cider — 코로나 V/마이클 합류/도지 사이클/UST 숏 prep; no-cider at B44 (피의 여름 reposition, 단순 손익 표만 남음)
- `51~60`: 10/10 cider — 엔비디아·BTC ETF·운용 헌장·가문 실사 회수까지 환전 dense, drought 없음

aggregate ledger:

- TR total blocks: 60
- no-cider blocks: 11
- exact no-cider block numbers: `1, 5, 8, 19, 25, 27, 31, 32, 33, 34, 44`
- longest no-cider drought: 4 (consecutive `B31 → B32 → B33 → B34`, 크립토 윈터~테슬라 prep~포지션 구축~헷지 진입)
- second-longest drought: 1 (모든 다른 no-cider는 인접 블록에서 끊김)

spot-check confirmation (re-opened flagged blocks + immediate neighbors):

- B5 (line 442–561) 재확인: reward "감흥 없다 / 이건 시작도 아니야" + 가족 모임은 일방 경멸 only. observer 갱신 없음. 양옆 B4·B6는 강한 cider — drought 1.
- B8 (line 788–900) 재확인: reward "포지션 진입 완료. 이제 기다린다." 마이클 첸 관계는 관찰자 갱신보다 prep 톤. NO CIDER 확정.
- B19 (line 2097–2204) 재확인: OTC 딜러는 "미친 부자" → "진짜 미친놈" 정도, 평가 갱신이 아니라 동일 라벨의 강도 변화. NO CIDER 확정.
- B31~B34 (line 3504~3947) 재확인: 모두 prep / 매집 / 헷지 buy 톤. observer tier가 침묵하거나 한 줄도 등장하지 않음. 4-block drought 확정 — `cider doctrine`상 가장 무거운 신호.

## Active Cap Rules

cap rules re-checked against `production-pair-benchmark-spec-v1` §6.

| spec §6 cap rule | status | 근거 |
| ---- | ---- | ---- |
| no visible cider inside block 1 → `YELLOW ceiling` | NOT triggered | TR B2 cider visible (PB tone shift + 18억 미실현) |
| first concrete token at TR block 7+ → `YELLOW ceiling` | NOT triggered | TR B3 reputation token + TR B6 골드만 라인 entry-ticket 모두 게이트 범위 내 |
| **any no-cider block in full-block scan → `YELLOW ceiling`** | **TRIGGERED** | 11 no-cider blocks (`1, 5, 8, 19, 25, 27, 31, 32, 33, 34, 44`) |
| rewardless pain blocks 2 in a row → `GREEN ceiling` | NOT triggered | 연속된 두 블록이 동시에 pain-only는 아님 (drought 4블록은 prep tone이지 pain tone 아님) |
| no-cider drought 6+ blocks → `YELLOW ceiling` | NOT triggered (이미 위 cap이 발동됨) | 최장 drought = 4 (B31~B34) — 6에 미달이지만 위 cap이 더 넓게 잡음 |
| major defeat without next card → `YELLOW ceiling` | NOT triggered | 손실/방어 블록(B43, B47, B53)도 다음 cycle 카드 동반 |
| BI as summary echo only → `GREEN ceiling` | borderline | P1#9 = 1; cap을 발동시킬 정도로 echo-only는 아니지만 amplification은 약함 |
| **early reward asset-only, no status/authority shift → `GREEN ceiling`** | borderline / partial | TR B2~B6에 status token (PB 톤 갱신, 증권가 소문, 골드만 라인)이 존재하지만 자산 숫자(20→70억) 옆에 한 줄로만 박혀 있어 cap rule 경계. P0-4가 thin pass인 이유와 동일. 위 YELLOW cap이 더 강하게 작동하므로 GREEN cap은 부속 신호로만 기록 |
| wins rely on stupid opposition → `GREEN ceiling` | NOT triggered | P1#6 = 2 |
| domain texture generic, swappable lane → `GREEN ceiling` | NOT triggered | P1#7 = 2, 구체 사건명·법인·종목·계약명 dense |
| protagonist passive across key arc with weak reward → `YELLOW ceiling` | NOT triggered | 모든 cycle 블록에서 한시우가 능동적 진입자 |

요지: spec §6의 `any no-cider block` cap이 단일 결정타로 ceiling을 YELLOW에 잠금. 추가로 `early reward asset-only` cap이 borderline 신호로 함께 누적되지만, YELLOW가 이미 더 강한 잠금이라 GREEN cap은 sub-signal로만 기록. RED trigger (§7) 해당 없음.

## Provisional Grade

re-derived from spec §8 grade decision table only.

- raw P1 total: **16 / 20** (spec §8.2 GREEN band `13~16`의 상단)
- P0 result: 6/6 PASS, opening innocence rule PASS
- active cap: spec §6 `any no-cider block → YELLOW ceiling` (TRIGGERED)
- spec §8.3 첫 줄: "any YELLOW ceiling rule triggered, **or** any no-cider block exists, **or** total score `9~12`" → 셋 중 하나만 충족해도 YELLOW. 본 페어는 첫 두 조건을 동시에 충족
- spec §8.1 GREENPLUS 조건 "full-block cider scan shows zero no-cider blocks" 미충족
- spec §8.2 GREEN 조건 "full-block cider scan shows zero no-cider blocks" 미충족
- 따라서 raw 16점이 GREEN 점수대 상단이라도 ceiling이 강제 적용되어 grade는 한 단계 잠김

**Provisional grade: `YELLOW`** (raw score 16/20 GREEN band 상단이지만 §8.3 ceiling lock으로 YELLOW 고정)

## P1 Score Table

re-scored against `production-pair-benchmark-spec-v1` §5 — 10 axes × `0 / 1 / 2`, total `/20`.

| # | Axis (spec §5) | Score | 근거 (TR/BI/WG anchor) |
| - | ---- | ----- | ---- |
| 1 | protagonist innocence | 2 | TR B1 (line 9–10) 회귀 전 몰락은 형들의 후계 싸움 → 그룹 분열로 막내가 찬밥 신세 = `wrong seat / inherited bad frame`. 한시우 본인의 게으름이나 무책임이 1차 원인이 아님. spec §4.3 acceptable list와 직접 일치 |
| 2 | protagonist-only proof clarity | 2 | TR B2~B4가 일반 운빨이 아니라 cycle reading 고유 무기로 작동: B2 이란 핵 농축 재개 시점 정확, B3 "에콰도르가 터진다" 사전 발화 후 5/16 옥시덴탈 적중, B4 두 달 횡보 인내 후 연준 금리 멈춤 적중. WG line 6–9 `protagonist_weapon` 그대로 가시화 |
| 3 | evaluation revision visibility | 2 | TR B2 (line 129–130) 박성호 1차 재평가, TR B3 (line 226, 234–243) 박성호 "경외" + 리스크관리팀 침묵 + 증권가 첫 소문, TR B4 (line 347–350) 박성호 "절대 신뢰" — 3블록 연속 weighted observer 갱신 |
| 4 | visible reward token strength | 1 | 토큰은 존재 (B3 증권가 소문 = reputation, B6 line 587 골드만 라인 = entry ticket) 하지만 둘 다 한 줄짜리 thin token이고 reward 본문은 자산 숫자(20→70억) 위주. spec §6 cap rule "early reward is asset-only and lacks status or authority shift"의 경계 — 토큰이 아예 없진 않으므로 `1` |
| 5 | block1 → block2 linkage | 2 | TR B6 (line 587, 661–664) 골드만 라인 확보 토큰이 TR B7 (line 676, 681) "CDS 거래 루트 확보"로 깨끗이 다음 게이트를 연다. B7은 retroactive backfill이 아니라 B6 토큰의 downstream confirmation |
| 6 | rational opposition | 2 | TR B2 (line 116) 박성호의 거부는 수수료 + 변동성 회피 incentive, TR B3 (line 224) 리스크관리팀 압박은 회사 손실 보호 incentive, TR B5 (line 446) 형들의 비웃음은 후계 경쟁 동기 — cartoon resistance 아님, era-valid |
| 7 | domain truth density | 2 | WTI 6월물 / 3배 레버리지 / WG line 22–35 mandatory_lexicon (포지션·익절·CDS·OTC·TWAP·패밀리오피스) 모두 TR B2~B6에서 실제 사용. 이란 핵·에콰도르 옥시덴탈·BNP 파리바·뉴센추리 등 구체 사건명으로 lane을 잠금 — generic으로 swap 불가 |
| 8 | repeatable loop clarity | 2 | 단일 loop가 가시적이고 재사용됨: `이벤트 선점 → 가격 반영 → 익절 → 다음 cycle 입장권 확보`. TR B2~B3 (원유), B4 (금), B6 (조선/철강), B7~B14 (서브프라임/리먼)까지 동일 loop가 다른 cycle에 그대로 재적용됨 |
| 9 | BI amplification power | 1 | WG `evaluation_thresholds`/`mandatory_scene_engines`/`custom_rules`가 TR을 직접 룰화하지만, 실제 TR B1~B6 본문은 BI를 echo하는 톤이 우세하고 BI 고유의 metaphor/명명/구조 압축이 TR을 sharpen하는 비율은 제한적. material amplification보다는 룰 강화 위주 — `1` |
| 10 | blockwise cider continuity | 0 | 60블록 중 11블록 no-cider (`1, 5, 8, 19, 25, 27, 31, 32, 33, 34, 44`), B31~B34 4-block drought 존재. spec §5 정의상 "one or more no-cider blocks = 0" — 자동 적용 |

P1 total: **16 / 20**

## Top 3 Repair Units or Alias Note

(grade가 YELLOW이므로 repair units 출력)

ceiling rule 재확인: spec §6 `any no-cider block → YELLOW ceiling`은 no-cider 카운트가 0이 되기 전까지 풀리지 않는다. 따라서 11블록 (`1, 5, 8, 19, 25, 27, 31, 32, 33, 34, 44`) **전수**를 cider blocks로 이동시키는 것이 GREEN 진입의 단일 조건이다. 아래 3개 unit은 풀-웨이브 수술 없이 11블록을 모두 한 줄짜리 mid-block proof로 채우는 가장 작은 수익 단위로 정렬한 것이다.

1. **B31~B34 4-block drought 분쇄 (가장 무거운 단일 무더기)**
   - B31 크립토 윈터: 박성호 또는 리스크팀이 "이 사람은 하락도 매수 캘린더로 쓴다" 류 한 줄 공식 갱신 + 현금 90% 비중 자체에 대한 외부 재평가 토큰
   - B32 생산지옥: 마이클이 테슬라 평단 260달러 매수 시점에서 한 줄이라도 "왜 지금이냐"에서 "어느 cycle인지 묻는다"로 전환 — observer 갱신
   - B33 어둠 속의 씨앗: 정민재 또는 제이슨이 14조 포지션 구조도를 받아보고 침묵으로 굴복 — silent observer-update beat
   - B34 폭풍 전야: 제3자 (PB 또는 가문 인사 1인)가 헷지 1.5조 지출을 보고 "왜 이걸 같이 사느냐"고 묻고, 한시우가 답하지 않음으로써 다음 블록 proof를 예약
   - 이 unit만 단독으로 처리해도 ceiling은 풀리지 않는다 — 나머지 7블록(B1, B5, B8, B19, B25, B27, B44)이 여전히 no-cider이기 때문. 단, 4-block consecutive drought라는 가장 큰 reader-felt 공백을 가장 먼저 메우는 효과가 있어 우선순위 최상위

2. **prep / 매집 / OTC 블록 7곳에 mid-block observer-update beat 1줄씩 (B1, B8, B19, B25, B27, B44 + B5 회식)**
   - B1 회귀, 그리고 선언: 아버지 한정호의 마지막 한 줄에 "재롱 수준" 너머의 미세 흔들림(예: 비서를 한 번 부르려다 멈추는 정도) 1줄 — 회귀 선언이 가족 시야에서 0이 아닌 입력으로 닿았음을 표시
   - B5 가족 회식: 형 한태준 또는 비서가 50억 결산 숫자를 우연히 듣고 흠칫하는 비공식 token 1줄 (line 481 비서 지시 직전 위치). 동시에 "활약 후 태도 변화 없음" forbidden flatten 경계도 회복
   - B8 역배팅: 마이클 첸의 술자리 한 줄을 농담에서 "기록"으로 미세 전환 — 골드만 시스템 안에서 한시우 이름이 처음 파일링되는 토큰
   - B19 사토시의 선물 / B25 마운트곡스 / B27 이더리움: OTC 딜러(제이슨) 또는 ETH 재단 측에서 "강도 변화"가 아닌 라벨 전환 한 줄 — 예: 제이슨이 "미친 부자 → 라인 안 사람"으로 분류 변경, ETH 측에서 한국 패밀리오피스 형식 인지
   - B44 피의 여름: 손익표만 있는 reward에 마이클 또는 정민재의 한 줄 — "이 평가손이 다음 카드를 부르고 있다"는 same-block next-card receipt
   - 이 7블록까지 전부 처리되면 비로소 no-cider 카운트가 0이 되고 §6 ceiling이 풀린다. 풀-웨이브 수술 금지 — 각 블록당 1줄 추가만 허용

3. **자산→방화벽/패밀리오피스 환전 토큰을 mid-arc에 분산 (P0-4 thin pass + P1#4 동시 회수)**
   - 현재 BI `success_device`의 "운용권 봉인" 축이 B57~59에만 몰려 있어 P0-4의 reward token이 자산 숫자에 한 줄로만 의존하는 thin pass가 됨
   - B19 (BTC 매집), B27 (ETH OTC), B32 (테슬라) 중 최소 1곳에 "운용 방화벽 / SPV 분리 / 가족 자산과의 차단" 한 줄 환전 토큰 삽입 (이 unit은 unit 2와 일부 블록을 공유 — 한 줄에 observer beat + 환전 토큰을 함께 박을 수 있음)
   - 이 unit은 ceiling 자체를 푸는 unit이 아니라, ceiling이 풀린 뒤 raw 점수를 16 → 17~18로 끌어올려 GREEN band 안정권에 자리잡게 하는 보조 unit

## Concise Rationale

이 페어의 핵심 강점은 (1) `production-pair-benchmark-spec-v1` P0 6게이트를 모두 통과한다는 점 — 특히 TR B2~B4의 cycle reading proof가 게이트 1·2·3·6을 동시에 채운다, (2) `block 1 → block 2` 게이트 연결이 thin이지만 깨끗하다 — TR B6의 골드만 라인 토큰이 TR B7 CDS 루트로 retroactive backfill 없이 흘러간다, (3) 60블록 전체 cider ledger의 강한 윈도우(11~20, 41~50, 51~60)에서 reward cadence가 반복 가능한 단일 loop로 닫혀 있다.

그러나 결정적인 약점은 두 가지다. 첫째, full-block cider scan에서 11블록의 no-cider가 적발되었고 그 중 B31~B34에 4-block consecutive drought가 있다. spec §6의 `any no-cider block` cap rule이 단일 결정타로 발동되며, 이 cap은 spec §8.3 첫 줄과 직접 연결되어 raw P1 점수와 무관하게 등급을 YELLOW에 잠근다. 둘째, P0-4 (visible reward token) 게이트가 thin pass다 — TR B2~B6의 reward 본문이 자산 숫자(20→70억) 위주이고 status token (PB 톤 갱신, 증권가 소문, 골드만 라인)이 한 줄로만 박혀 있어, spec §6의 borderline cap "early reward asset-only and lacks status or authority shift"가 보조 신호로 함께 누적된다. P1 axis 4가 1점에 머문 것도 이 구조 때문이다.

raw P1 = 16/20은 GREEN band(13~16)의 상단이지만, 본 페어는 spec §8 grade decision table을 충실히 따를 때 (§8.3 첫 줄의 "any no-cider block exists" 조건으로) GREEN으로 진입할 수 없고 YELLOW에 고정된다. 그리고 spec §6의 `any no-cider block → YELLOW ceiling` cap rule은 4-block drought 하나만 해결한다고 풀리지 않는다 — no-cider 카운트가 **0**이 되기 전까지, 즉 11개 no-cider 블록(`1, 5, 8, 19, 25, 27, 31, 32, 33, 34, 44`) 전수에 same-block receipt가 박히기 전까지 ceiling은 그대로 유지된다. 따라서 B31~B34 drought 분쇄는 reader-felt 공백이 가장 큰 단일 무더기를 가장 먼저 지우는 우선순위 최상위 unit일 뿐, 그 자체로 등급 자물쇠를 푸는 키는 아니다. GREEN 진입의 진짜 단일 조건은 11블록 전수의 cider 채움이며, 그 이후에야 raw 점수도 16 → 17~18로 함께 올라 GREEN band 안정권에 자리잡는다.

다른 11개 메인 페어와 비교했을 때 이 페어는 stage2 oil/gold/Lehman 구간에서 가장 dense한 cider density를 가지고 있어 raw P1 점수는 GREEN 후보였지만, drought 단일 사건과 cap 규칙이 일관되게 작동해 YELLOW로 내려앉았다. 수리 단위 1번 (4블록 drought 분쇄)만 해결되어도 grade는 즉시 GREEN 후보로 회귀할 수 있으며, 풀-웨이브 수술이 아니라 각 블록당 한 줄짜리 observer beat 추가만으로 충분하다.

watchpoint 재확인: 자산 증가만으로 status/authority/next-gate token을 대체한 블록은 발견되지 않았다 — 모든 주요 cider 블록이 적어도 한 종의 권위/접근권/운용권 토큰을 동반한다. 단, drought 4블록은 정확히 이 watchpoint가 우려한 "asset gain만 남는 구간"의 잠재 영역이며, 수리 1번의 우선순위가 가장 높은 이유이기도 하다.

read-only true benchmark audit complete; no pair files mutated
