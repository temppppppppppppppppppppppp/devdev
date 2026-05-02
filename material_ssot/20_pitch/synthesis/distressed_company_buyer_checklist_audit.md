# Pitch Selection Audit

Target:

- `material_ssot/20_pitch/synthesis/distressed_company_buyer_working_synthesis.md`

Date: 2026-05-01
Status: final audit for canon candidate
Verdict: `PASS` - canon candidate ready, Phase0 entry still requires Stage 0 handoff

## 1. P0 Hard Gates

| # | Question | Verdict | Evidence |
|---|---|---|---|
| 0 | male protagonist active lane | `PASS` | 한도윤, 남성 |
| 1 | innocence without self-fault | `PASS` | 도윤은 부도 회사를 망하게 한 사람이 아니라, 권한 없이 현장 실사와 보고서 초안만 담당하던 계약직 실사관이다 |
| 2 | non-begging protagonist | `PASS` | 인정 구걸이 아니라 온도 로그, 보험 약관, 납품 클레임, 창고 배정표를 맞춰 proof를 만든다 |
| 3 | first win creates evaluation revision | `PASS` | `트럭 사진이나 찍는 실사관`에서 `회의실 안에 앉혀야 하는 구조조정 플레이어`로 이동한다 |
| 4 | protagonist-only proof scene exists | `PASS` | 콜드체인 인증, 리콜 보험금, 새벽 배송 노선, 항만 냉장창고 우선권을 하나의 권리 묶음으로 보는 장면은 도윤의 실사 습관과 회귀 전 실패 기억이 있어야 가능하다 |
| 4A | first_block_cider_ledger selection-ready shape | `PASS` | blocks `2~6` 다섯 줄이 모두 있고, 전부 `has_cider: true`, same-block receipt가 있다 |
| 5 | early reward is status-first | `PASS` | 돈보다 채권단 회의석, 데이터룸 제한 접근권, 보험 원본 접근, 독점 실사권, 우선협상권, 다음 데이터룸 초대권이 먼저 붙는다 |
| 6 | no pure punishment spiral after first success | `PASS` | 모욕/책임전가 뒤 곧장 회의석, 직통선, 독점 실사권, 우선협상권, 첫 운송 오더가 연속 회수된다 |
| 7 | protagonist does not look incompetent | `PASS` | 실패 원인은 능력 부족이 아니라 보고서 위계, 채권단 담보 회수 관성, 소형 매물을 무시하는 시장 구조다 |
| 8 | reads the crisis first | `PASS` | 부도 자체가 아니라 해지 직전 인증, 지급 회피 보험금, 버려진 노선권, 현장 기억의 오분류를 먼저 읽는다 |
| 9 | enters the crisis with tools | `PASS` | 실사 체크리스트, 온도 로그, 보험 약관, 납품 클레임, 항만 창고 배정표, 운송기사 증언, SPV 인수 구조가 있다 |
| 10 | reward follows damage immediately | `PASS` | 문밖 대기와 고철 매각 위협은 같은 opening window 안에서 회의석, 데이터룸, 보험사 예비 인정, 다음 매물 초대권으로 회수된다 |
| 11 | no self-explanatory bragging | `PASS` | 미래를 안다고 장광설하지 않고, 현재 문서와 외부 증인의 태도 변화로 증명한다 |

P0 result: **12/12 PASS**

## 2. P1 Strong Preference Check

| # | Question | Verdict | Evidence |
|---|---|---|---|
| 12 | growth resource is concrete | `PASS` | 회의석, 데이터룸 접근권, 보험 원본 접근, 독점 실사권, 우선협상권, SPV 인수권, 다음 데이터룸 초대권 |
| 13 | protagonist is easy to defend | `PASS` | 독자는 바로 `쟤는 무능한 게 아니라 권한과 서명권이 없었던 거다`라고 변호할 수 있다 |
| 14 | desirability of becoming the protagonist | `PASS` | 남들이 고철로 넘길 회사를 권리 묶음과 현금흐름으로 바꾸는 우월감이 선명하다 |
| 15 | helpers change by logic before emotion | `PASS` | 채권은행, 보험사, 대형마트 구매담당자는 감동이 아니라 회수율, 지급 트리거, 배송 공백 리스크 때문에 태도를 바꾼다 |
| 16 | antagonists keep dignity | `PASS` | 파트너는 성과와 책임 회피를 보고, 은행은 회수율과 감사 리스크를 보고, 보험사는 지급 최소화를 본다 |
| 17 | protagonist face before domain | `PASS` | 구조조정 용어보다 `부도 회사 안의 살아 있는 권리를 먼저 사는 자기중심적 실사관` 얼굴이 먼저 선다 |
| 18 | first 3 blocks create reevaluation | `PASS` | 회의실 문밖 -> 데이터룸 접근 -> 보험사 예비 인정과 은행 직통선으로 초반 태도 변화가 빠르다 |
| 19 | impact remembered by causality | `PASS` | 온도 로그/약관/클레임/창고 배정표가 인증과 보험금과 노선권 proof로 연결된다 |
| 20 | crisis rhythm stays active | `PASS` | 각 row가 모욕/압박을 열고 같은 block 안에서 권한 영수증으로 닫는다 |
| 21 | lucky-cover margin exists | `PASS` | 주변은 `운 좋게 약관을 본 것`처럼 말할 수 있지만 독자는 실사 습관과 문서 대조가 원인임을 안다 |
| 22 | no unrecovered bleeding | `PASS` | 고철 매각, 책임전가, 공 가로채기, 보험 지급 회피가 모두 권한/현금흐름/다음 게이트로 회수된다 |

P1 result: **11/11 PASS**

## 3. User-Pacing Requirement Check

User requirement:

- 웹소설 페이싱은 빨라야 한다.
- `1 block`은 downstream `2~6화` 분량이다.
- 따라서 `1 block` 안에는 최소한 다른 사건 1개가 더 있어야 한다.
- 주인공은 자기중심적이어야 한다.
- 착함/악함보다 이득과 효율이 중요하다.

Audit result: `PASS`

- synthesis has a work-specific `TR Pacing Contract`.
- every first-block ledger row has `incident_beats` with at least two distinct beats.
- each row pays same-block authority, access, legal receipt, cashflow, or next-gate position.
- protagonist decision law is locked as profit, efficiency, legal protection, speed, leverage, or next-gate position.
- charity rescue is explicitly banned.

## 4. Donor Adoption Check

Donor decision: `adopted`

Donor lanes reviewed:

- `bulhaeng-chaebol`
- `jaebeol-jangnam-value`
- `jusigui-sin`
- `heuksujeo-founder-expansion`

Adopted generalized law:

- 압박이 먼저 온다.
- 주인공만 가능한 판독이 판을 뒤집는다.
- 같은 block 안에 권한 영수증이 떨어진다.
- 관찰자 태도가 바뀐다.
- 그 영수증이 다음 전장 입장권이 된다.

Blocked donor surfaces:

- donor proper nouns
- exact scene order
- stock prophecy
- chaebol-only skin
- benevolent rescue story
- fantasy UI that prints value answers

## 5. Blockers

### Blocker 1: legality / conflict-of-interest risk - controlled

회계법인 실사관이 바로 부도 회사를 사들이면 내부정보 거래처럼 보일 수 있다.

Canon에서 반드시 고정할 처리:

- 도윤은 자문 중인 상태에서 몰래 사지 않는다.
- 자문 종료, 공개입찰, 채권단 승인, 법원 일정, SPV 분리 중 하나 이상의 공개 영수증을 남긴다.
- 내부정보 꼼수가 아니라 `남들이 봐도 버린 공개 매물의 권리 구조를 더 잘 읽은 것`으로 처리한다.

### Blocker 2: charity rescue drift - controlled

부도 회사와 직원이 나오면 미담으로 흐를 위험이 있다.

현재 후보의 잠금:

- 도윤은 회사를 살리는 것이 더 싸고 빠르고 이득일 때만 살린다.
- 핵심 인력을 남기는 이유는 인증 유지, 노선 기억, 클레임 방어, 실행 속도 때문이다.
- 가치 없는 부품은 자른다.

### Blocker 3: asset-first drift - controlled

초반부터 큰돈만 나오면 현대판타지 사이다가 아니라 숫자 보고서가 된다.

Opening reward order:

1. 채권단 회의 동석권
2. 데이터룸 24시간 제한 접근권
3. 보험사 예비 인정 메일
4. 채권은행 직통선
5. 독점 실사권
6. 우선협상권
7. 첫 운송 오더와 다음 데이터룸 초대권

## 6. First-Block Cider Ledger Review

```md
- block_no: 2
  has_cider: true
  incident_beats: 채권단 회의 문밖 대기 모욕, 온도 로그와 납품 클레임 대조 proof
  same_block_receipt: 도윤이 냉동차 고철값보다 콜드체인 인증 유지 조건이 더 중요하다는 proof를 제시해 채권단 회의 동석권과 데이터룸 24시간 제한 접근권을 얻는다.
  receipt_kind: reevaluation
  bridge_or_payback_note:

- block_no: 3
  has_cider: true
  incident_beats: 현장 재실사에서 기사들의 노선 기억 확보, 보험사 지급 회피 논리 반박
  same_block_receipt: 도윤이 리콜 보험 약관의 지급 트리거와 실제 온도 이탈 기록을 맞춰 보험사 예비 인정 메일과 채권은행 직통선을 받는다.
  receipt_kind: proof
  bridge_or_payback_note:

- block_no: 4
  has_cider: true
  incident_beats: 대형마트 구매담당자 접촉, 경쟁 고철업자의 폐차 일괄매입 방해
  same_block_receipt: 도윤이 새벽 배송 노선과 인증 승계 가능성을 묶어 10일 독점 실사권과 조건부 공개입찰 참여 자격을 확보한다.
  receipt_kind: authority_shift
  bridge_or_payback_note:

- block_no: 5
  has_cider: true
  incident_beats: 항만 냉장창고 우선사용권 확인, 회계법인 파트너의 공 가로채기 시도 차단
  same_block_receipt: 도윤은 삼진콜드를 통째로 사지 않고 인증, 노선, 보험금, 창고 우선권만 남기는 SPV 인수안을 내 채권단 우선협상권과 회생안 제출권을 받는다.
  receipt_kind: legal_receipt
  bridge_or_payback_note:

- block_no: 6
  has_cider: true
  incident_beats: 보험금 예비 지급과 첫 임시 운송 오더, 다음 부도 매물 정보 유입
  same_block_receipt: 도윤이 보험금 일부와 대형마트 임시 운송 오더를 동시에 확보해 첫 현금흐름을 만들고, 채권은행으로부터 다음 부도 식품공장 데이터룸 초대권을 받는다.
  receipt_kind: next_gate_opening
  pain_only_exit: false
  bridge_or_payback_note:
```

Ledger verdict: **PASS**

- strict 2~6 window: `PASS`
- block 1 rescue: `none`
- block 7+ rescue: `none`
- all rows have same-block receipt: `PASS`
- all rows have at least two incident beats: `PASS`
- block 6 pain-only exit: `false`

## 7. Planning Candidate 7 Questions

1. What does the protagonist want now, and why must it move inside the first block?
   - 도윤은 삼진콜드가 이번 주 고철 매각으로 넘어가기 전에 회의석, 데이터룸 접근권, 독점 실사권, 우선협상권을 얻어야 한다. 매각이 끝나면 인증, 노선, 보험금, 창고 우선권이 흩어진다.

2. What information gap or reading edge belongs only to the protagonist?
   - 도윤은 회귀 전 실패 기억으로 목표물을 알고, 현재 실사관의 습관으로 온도 로그, 보험 약관, 납품 클레임, 항만 창고 배정표를 권리 묶음으로 읽는다.

3. What is the first-block proof scene that makes `저건 쟤라서 가능했다` undeniable?
   - 모두가 냉동차 고철값을 볼 때, 도윤은 `트럭은 고물입니다. 그런데 이 회사가 가진 콜드체인 인증은 아직 살아 있습니다`로 인증 유지 조건과 보험금 트리거를 연결한다.

4. What visible cider lands inside blocks `2~6`?
   - 회의석, 데이터룸 접근권, 보험사 예비 인정, 은행 직통선, 독점 실사권, 공개입찰 참여 자격, 우선협상권, 첫 운송 오더, 다음 데이터룸 초대권.

5. Who reevaluates the protagonist inside the first block, and how is that visible on-page?
   - 채권은행 팀장은 회의실 문을 열어 준다. 보험사 손해사정인은 지급 회피 논리를 수정한다. 대형마트 구매담당자는 새벽 배송 공백 리스크 때문에 도윤과 직접 통화한다.

6. How does that first-block reward open block 2?
   - 삼진콜드의 권리 묶음은 부도 식품공장 arc의 식품 제조 캐파, HACCP 인증, OEM 납품권으로 이어진다. 도윤은 물류 권리에서 제조 권리로 전장을 넓힌다.

7. What contamination would turn this opening into `고구마`, and how is it explicitly banned?
   - 파트너 모욕을 길게 끌기, 직원 구원 미담, 내부정보 불법거래, 미래지식 장광설, 고철값 대박 숫자만 제시하는 장면이 금지된다. 보상은 현재 문서 proof와 공개 영수증으로 같은 block 안에 찍힌다.

## 8. Work-Guard Freeze Check

1. one_line_truth promises reward and ascent:
   - `PASS` - 부도 회사의 살아 있는 권리를 사서 회의석, 접근권, 현금흐름, 다음 매물 입장권으로 올라간다.
2. mandatory_scene_engines include protagonist-only proof and evaluation revision:
   - `PASS` - 콜드체인 인증 proof와 채권은행/보험사/구매담당자 태도 변화가 있다.
3. tracking_slots/custom rules force first-block cider:
   - `PASS` - ledger `2~6`, incident beat minimum, self-interest filter가 잠겼다.
4. thresholds require visible reward inside one block:
   - `PASS` - each ledger row has same-block receipt.
5. forbidden_flattenings ban failure-only openings:
   - `PASS` - no pain-only exit, no charity rescue, no illegal insider shortcut.

Work-guard verdict: **freeze candidate after Phase0 truth lock**

## 9. Final Judgment

이 기획안은 현재 house philosophy 기준에서 **canon candidate ready**다.

- P0 12/12 PASS
- P1 11/11 PASS
- donor decision `adopted`
- opening `2~6` ledger 전부 same-block payback
- each first-block row has at least two incident beats
- Block 1 rescue 없음
- Block 7+ late rescue 없음
- protagonist engine is self-interested, efficient, and not charity-driven
- legal acquisition receipt guard is explicit

Verdict: **PASS - canon candidate ready**

Next step:

1. `material_ssot/20_pitch/canon/distressed_company_buyer.md` materialize.
2. `python -X utf8 scripts/material_readiness_validator.py --path material_ssot/20_pitch/canon/distressed_company_buyer.md`
3. `python -X utf8 scripts/material_promotion_gate.py --stage canon --path material_ssot/20_pitch/canon/distressed_company_buyer.md`
4. Then create Stage 0 preprocess artifacts before Phase0/TR/BI.

## 10. Document 3-Pass Audit

- Pass 1:
  - checked P0/P1 checklist against the synthesis.
  - result: all hard gates and preference gates pass.
- Pass 2:
  - checked the user-specific pacing and self-interest requirements.
  - result: row-level incident beats and self-interest filter are explicit.
- Pass 3:
  - checked downstream stage boundary.
  - result: canon candidate ready; Phase0/TR/BI still gated by Stage 0 and Phase0/work_guard order.
- Estimated confidence: 95%
