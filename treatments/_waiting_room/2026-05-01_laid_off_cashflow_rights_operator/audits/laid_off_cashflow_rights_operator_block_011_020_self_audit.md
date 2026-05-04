# laid_off_cashflow_rights_operator — Block 011~020 Self-Audit

Date: 2026-05-01
Harness reference: `docs/blockguide/treatment-production-harness-v2.md` §1.1C 10-block 자체 감리
Audit window: `Block 011~020`
Audit type: waiting-room material-side self-audit
Saved boundary at audit time: Block 020
Next unit before this audit: `ARC-02 10-block 자체 감리`

## 0. Verdict

**PASS**

Block 021 진입 허용. ARC-02는 `폐기 라인의 가격`에서 출발해 `AS 대행권`, `D-RN 라벨/라우팅`, `물량 통제`, `SPV 첫 계약`, `달러 RMA mismatch sample gate`까지 한 단계씩 권리를 누적하며 닫혔다.

Same-turn repair: 없음.

## 1. 6-Axis Review

### Axis 1 — 빠른 페이싱과 2사건 밀도

**PASS**

- Block 011~020 전부 `pacing_contract.incident_count = 2`.
- 각 블록이 하나의 회의나 설명으로 닫히지 않고, 첫 사건과 역제안/반격/절차 지연/현장 흔들림을 함께 품는다.
- 후반부 017~020은 특히 `물량 유출 -> 고용 포획 -> 정산 계좌 공백 -> 보류금/SPV 계약`으로 사건 단위가 빠르게 바뀐다.

### Axis 2 — 주인공 자기중심성

**PASS**

- 모든 블록에 `protagonist_drive.self_centered_axis`가 존재한다.
- 도윤은 선의나 복수보다 자기 권한, 수수료, 접근권, 계좌, SPV 계약을 먼저 요구한다.
- 현장 인센티브도 선행이 아니라 처리 지연 보험료로 설계되어 작품 규칙과 맞는다.

### Axis 3 — Receipt 누적 연속성

**PASS**

- Block 011: `AS 대행권 가격표 v0`
- Block 012: `조건부 AS 파일럿 승인권`
- Block 013: `AS 대행 파일럿 약정서`
- Block 014: `성공품 21대 추가 단가표`
- Block 015: `월 300대 반복 처리 물량`
- Block 016: `D-RN 라벨 + 라우팅 코드`
- Block 017: `D-RN 물량 통제권`
- Block 018: `외부 운영자/SPV 승계 조건`
- Block 019: `외부 운영 정산 코드 + 입금 계좌 등록 요청`
- Block 020: `SPV 첫 계약 + 60일 우선 판매권 + 달러 RMA gate`

Capital continuity check도 Block 012~020 전부 직전 `capital_after`와 다음 `capital_before`가 일치했다. Block 011은 ARC-01의 Block 010 receipt에서 정상 출발한다.

### Axis 4 — 적대 분화와 전장 이동

**PASS**

- 적대축은 `서태오/제조사 품질 기준`, `제조사 클레임팀`, `최문식`, `다온 PB사업부`, `그린로지스`, `법무/회계 결재선`으로 분화된다.
- PB사업부가 016, 019, 020에 반복 등장하지만 기능이 다르다: 브랜드명 금지, cost center 흡수, 내부 귀속/판매권 방어.
- 그린로지스는 017 이후 직접 적대보다 보관비/재입고 압박으로 후퇴해 과사용 위험이 낮다.

### Axis 5 — Arc Close와 다음 Gate

**PASS**

- ARC-02 출구는 `리퍼브권/AS 대행권`을 실제 판매권과 SPV 계약으로 변환한다.
- Block 020은 첫 486만 원 보류를 단순 고통으로 끝내지 않고, 보류금 이전 조항과 우선 판매권 receipt로 환전한다.
- `달러 RMA mismatch sample`, `supplier debit note`, `해외 정산일 오류`, `Mira`가 ARC-03 진입 gate로 열렸다.

### Axis 6 — Webnovel Cider Contract

**PASS**

- Block 011~020 전부 `genre_ext.block_cider.has_cider = true`.
- `pain_only_exit = false` 유지.
- same-block reward가 숫자 또는 문서 receipt로 남는다.

## 2. Machine Checks

- JSON parse: PASS for TR 001~020 and `production_status.json`
- Phase0 schema: PASS
- BI seed schema: PASS
- work_guard V1: PASS
- UTF-8 readback: PASS
- Block 011~020 incident count: all `2`
- Block 011~020 self-interest axis: all present
- Block 011~020 cider: all true
- Capital continuity: Block 012~020 exact match; Block 011 starts from Block 010 receipt

## 3. Top Risks For Block 021~030

1. **Mira 자동 돈벌이화 위험** — Block 021에서 AI 계약 비교 도구가 등장할 수 있지만, 판단자는 도윤이어야 한다. Mira는 `계약 리스크 표시 보조자`로 제한한다.
2. **달러 RMA 파일 질감 부족 위험** — ARC-03은 숫자/환율/정산일 파일이 중심이다. sample, debit note, 송장, 계좌, 정산일 같은 문서 질감을 매 블록에 유지해야 한다.
3. **첫 486만 원 보류금 회수 지연 위험** — 보류금은 바로 입금되지 않았으므로 ARC-03 초반에 `보류금 계정 -> SPV 계좌 이전 예정` 상태를 잊지 말아야 한다.
4. **PB사업부 잔여 반발 과사용 위험** — Block 021부터는 PB사업부를 주 적대로 끌고 가면 ARC-02가 늘어진다. ARC-03의 전면 적대는 해외소싱팀, 은행 외환 담당자, 해외 공급사 쪽으로 넘긴다.
5. **도윤의 이득/효율 축 약화 위험** — 달러 정산 arc에서 도윤이 회사 손실을 고치는 해결사처럼 보이면 안 된다. 다음 파일 접근권, 달러 계좌, 해외 계약 gate를 먼저 요구해야 한다.
6. **Arc 전환 속도 저하 위험** — Block 021은 새 전장이므로 설명이 길어지기 쉽다. `AI 표시 -> 도윤 수동 검증 -> 달러 정산 오류 proof -> 다음 gate`까지 같은 블록 안에 넣어야 한다.

## 4. Repair Targets

- same-turn repair: 없음.
- next envelope 착수 전 필수 repair: 없음.
- writing-level guard:
  - Block 021에서 Mira는 보조 도구로만 사용.
  - Block 021 안에 달러 RMA mismatch sample의 구체 필드 2개 이상 포함.
  - Block 021 안에 도윤의 요구 receipt를 `해외 계약 파일 접근권` 또는 `달러 오류 proof`로 남길 것.

## 5. Next 10 Focus

1. `Mira`는 자동 수익 장치가 아니라 계약 비교/리스크 표시 보조 도구로 고정.
2. 달러 RMA mismatch sample을 실제 정산일 오류 proof로 바꾸기.
3. supplier debit note와 해외 공급사 책임선을 분리하기.
4. 은행 외환 담당자 gate를 열어 달러 계좌 필요성을 만들기.
5. 도윤권리운영 SPV를 다온 직원이 아니라 외부 운영자로 인식시키기.
6. ARC-03 출구에서 해외 총판권 또는 물류 gate로 이어지는 다음 권리를 남기기.

## 6. 3-Pass Audit Note

- Pass 1: Block 011~020 필드 evidence 확인. 사건 수, cider, self-axis, receipt, next_gate 모두 통과.
- Pass 2: 반복/드리프트 검토. PB사업부 반복은 기능 차이가 있어 PASS, 그린로지스는 직접 적대에서 보관비 압박으로 변주되어 PASS.
- Pass 3: 다음 arc handoff 검토. 달러 RMA gate가 명확하고, top_risks/next_10_focus가 Block 021 진입 전 가드로 충분하므로 최종 PASS.

## 7. Gate Result

- Harness §1.1C rule 1: PASS
- Rule 2: PASS. Block 021이 아니라 Block 011~020 자체 감리를 먼저 수행함.
- Rule 3: PASS. 6-axis review 완료.
- Rule 4: PASS. `PASS/FAIL`, `top_risks`, `repair_targets`, `next_10_focus` 포함.
- Rule 5: 적용 없음. FAIL이 없으므로 same-window repair 불필요.

**Block 021 진입 허용.**
