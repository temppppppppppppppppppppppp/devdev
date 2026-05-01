# 재벌가 후계자는 버려진 권리를 산다

Date: 2026-05-01
Status: canon_candidate
Work ID: `imf_allsector_rights_heir`
Family: `blockguide`

## Canon Lock

이 작품은 `1997 IMF all-sector rights rollup` 현대판타지 재벌 회귀물이다.

주인공은 선하거나 악해서 움직이지 않는다. 그는 이득과 효율을 기준으로 움직이고, 남들이 폐기하려는 자산에서 미래의 권리와 협상권을 먼저 산다.

## Core Identity

- Title: `재벌가 후계자는 버려진 권리를 산다`
- Protagonist: `강태준`
- Start year: `1997년 11월`
- Group: `세강그룹`
- Premise: 2026년 해체된 세강그룹의 잔해를 정리하던 강태준이 1997년 IMF 직전으로 돌아온다.
- Core fantasy: 모두가 적자, 잡자산, 낡은 계약, 부실채권이라고 버리는 것에서 미래의 통제권을 읽고, 돈보다 권한을 먼저 회수한다.

## Required Engine

반복 엔진:

1. 모두가 버리려는 권리/자산/계약이 등장한다.
2. 태준은 회귀 기억으로 위험 범위를 좁힌다.
3. 해결 근거는 현재 자료로 만든다.
4. proof는 권한 영수증으로 환전된다.
5. 그 권한이 다음 섹터 입장권을 연다.

권한 영수증:

- 자료 접근권
- 매각/해지/폐쇄 보류권
- 실사권
- 우선매수권
- 계약 재협상권
- 사장단 안건권
- sector TF owner
- 지주회사 재편 권한

## Sector Ladder

1. 냉장물류/유통
2. PC방/초고속인터넷/게임 유통
3. PCS/통신/단말 유통
4. NPL/워크아웃 기업
5. 반도체 부품/소재
6. 호텔/오피스/데이터센터 부지
7. 엔터/IP/광고망과 지주회사 재편

## Pacing Lock

- `1 TR block = downstream 2~6화 episode-bundle`.
- 모든 TR block에는 최소 두 사건이 있어야 한다.
- 첫 TR block의 주 사건은 `남서 냉장창고 매각 보류`.
- 첫 TR block의 부 사건은 `PC방/초고속 회선 장기계약 해지 보류`.
- 첫 블록부터 다른 섹터 표지가 실제 권한으로 열려야 한다.

## 3A. First-Block Cider Ledger

- block_no: 2
  has_cider: true
  same_block_receipt: 원본 손익표와 회선 계약 해지 목록 호출
  receipt_kind: proof
  bridge_or_payback_note: 주 사건과 부 사건이 같은 회의에서 열린다.

- block_no: 3
  has_cider: true
  same_block_receipt: 콜드체인 입찰 자격과 회선권 가치 분리
  receipt_kind: reevaluation
  bridge_or_payback_note: 두 helper가 각자 증거를 든다.

- block_no: 4
  has_cider: true
  same_block_receipt: 30일 권리 실사권과 계약 해지 보류권
  receipt_kind: access_shift
  bridge_or_payback_note: 권한이 공식 조건으로 내려온다.

- block_no: 5
  has_cider: true
  same_block_receipt: 숙련 shift와 회선권이 권리 목록에 등재
  receipt_kind: protection
  bridge_or_payback_note: 사람 보호가 권리 보존으로 환전된다.

- block_no: 6
  has_cider: true
  same_block_receipt: 매각 보류 공식화와 PC방/게임 유통 gate
  receipt_kind: next_gate_opening
  pain_only_exit: false
  bridge_or_payback_note: 첫 opening bundle이 다음 섹터로 닫힌다.

## 3B. Readiness Declaration

- selection-ready: yes
- Phase0-ready: yes
- all 2~6 ledger rows have has_cider true: yes
- block 1 used as opening rescue: no
- block 7+ used as opening rescue: no
- 정본 소스와 참고 소스가 분리되어 있다.
- primary profile은 `business_growth_profile`, secondary profile은 `investment_market_profile`로 제한된다.
- opening bundle에는 주 사건과 부 사건이 모두 있다.
- 주인공의 행동 기준은 이득과 효율이며, 대가 없는 선의는 금지된다.
- work_guard로 번역 가능한 tracking slot과 forbidden flattening이 충분히 명시되어 있다.

## Forbidden Flattenings

- 미래 주가/뉴스 찍기로만 돈 벌기.
- 선의로 사람을 구한다는 미담화.
- IMF 배경을 감상적 회상으로만 쓰기.
- 임원과 은행을 바보 악역으로 만들기.
- 모든 섹터를 백화점식 나열로 소비하기.
- 권한 없이 돈만 쌓기.
- proof와 receipt를 한 장면에서 뭉개기.

## 3-Pass Audit

Pass 1:

- 작품 정체성, 주인공, 시대, 그룹, 섹터 ladder를 잠갔다.

Pass 2:

- 사용자 pacing 조건과 자기중심성 조건을 canon rule로 승격했다.

Pass 3:

- Stage 0와 Phase 0, work_guard, TR production으로 바로 이어지는 canon candidate로 정리했다.

Estimated Confidence: 95%
