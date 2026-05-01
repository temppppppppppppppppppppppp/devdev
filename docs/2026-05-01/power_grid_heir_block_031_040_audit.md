# power_grid_heir — Block 31~40 Self-Audit

Date: 2026-05-01
Harness reference: `docs/blockguide/treatment-production-harness-v2.md` 10-block self-audit gate
Audit window: Block 31-40 inside `treatments/power_grid_heir_tr_block_070_draft.json`
Audit type: production boundary review
Saved boundary at audit time: `_saved_blocks=40`

## 0. Verdict

**PASS**

Block 41 진입 허용. 데이터센터 전장은 `cloud margin inversion -> PPA limited renegotiation -> cooling permit loss -> complaint calendar -> investor appendix -> customer SLA dashboard -> outage benchmark -> site portfolio write-off -> observer seat -> pilot budget candidate gate`로 기능을 완주했다. 다음 창은 재무기획실, project finance covenant, credit risk, offtake letter 전장으로 이동해야 한다. BI는 아직 금지다.

## 1. 6-Axis Review

### Axis 1 — 주인공 우위와 간판 맛

**PASS**

- 도윤은 AI 성장 서사를 취소하지 않고 전력비, 냉각수, PPA, 고객 penalty를 붙여 판단 기준을 바꿨다.
- 고객, 투자자, 지역 broker, 전력 판매 파트너를 달래는 게 아니라 dashboard, appendix, calendar, screening table로 통제했다.
- 정식 권력을 빨리 요구하지 않고 observer seat와 예산 심사표부터 먹는 자기중심적 효율이 유지됐다.

### Axis 2 — 보상/인정 리듬

**PASS**

- Block 31: power-adjusted margin table 작성권 + 고객별 전력비 별첨 열람권
- Block 32: PPA limited renegotiation seat + offtake draft 작성권
- Block 33: cooling permit calendar + 환경청 보완 요청 원본 접근권, 권한 수치 손실
- Block 34: complaint calendar 관리권 + conditional land option
- Block 35: investor Q&A response right + power-risk appendix 승인권
- Block 36: 고객 SLA penalty renegotiation seat + power-risk dashboard 운영권
- Block 37: public outage proof package + customer incident briefing right
- Block 38: site portfolio map 승인권 + 대표 부지 write-off 권한, 권한 수치 손실
- Block 39: 90일 한정 observer seat + agenda pre-read + risk minutes 주석권
- Block 40: pilot budget candidate gate + screening table owner 권한

모든 블록의 `block_cider.has_cider`가 true이며, 손실 블록도 pain-only로 닫히지 않았다.

### Axis 3 — 자본/권력/조직 장악 축

**PASS**

권한 지표는 `18 -> 25`로 상승했다. 중간 손실은 두 번 있다.

- cooling permit 공개에서 `20 -> 18`: 본계약/PPA 속도 손실을 감수하고 permit calendar와 원본 접근권을 얻었다.
- site portfolio 재배열에서 `23 -> 21`: 대표 부지 sunk cost 일부를 write-off하고 기능별 portfolio map을 얻었다.

두 손실 모두 장기 이득을 남긴다. 첫 손실은 site portfolio 기준을 만들고, 두 번째 손실은 observer seat와 pilot budget screening table의 proof가 됐다.

### Axis 4 — opponent / method / stakes 반복

**PASS**

- opponent는 서민재, 전력 판매 파트너, 선우건설 site team, 지역 broker, 고객 법무팀, IR팀, 백인호로 순환한다.
- method는 net margin table, limited PPA amendment, permit calendar, complaint calendar, investor appendix, SLA dashboard, outage benchmark, site portfolio write-off, observer seat, screening table로 분화되어 있다.
- 장면 무대도 선우디지털 회의실, 전력 판매 파트너 협상실, site permit 상황실, 지역 농수로 사무실, investor hall, 고객 법무 회의, crisis monitoring room, site portfolio war room, board pre-briefing, budget screening room으로 이동한다.

### Axis 5 — Continuity와 열린 복선

**PASS**

- board observer 후보 gate는 실제 90일 observer seat로 승격됐다.
- power-risk appendix는 고객 SLA dashboard와 incident briefing으로 회수됐다.
- cooling permit calendar와 complaint calendar는 site portfolio map으로 회수됐다.
- public outage proof는 observer seat 심사의 외부 proof가 됐다.
- pilot budget 후보 gate는 다음 project finance/covenant 전장의 직접 입구가 됐다.

### Axis 6 — 다음 10블록 확장축

**PASS**

다음 창은 재무/PF 전장이다. 핵심 확장축:

1. PF covenant 벽
2. 백인호의 credit risk 반대
3. offtake letter seed
4. 은행단 haircut 요구
5. 손실 block과 담보 재평가
6. PPA/offtake 묶음 설계
7. competitor credit scare
8. pilot budget 조건부 승인
9. risk committee minutes 확보
10. 3000억 allocation authority

## 2. Machine Checks

- JSON parse: PASS
- saved blocks: 40
- block continuity: CLEAN
- natural-language meta leak scan: 0건
- mojibake/replacement-character scan: 0건
- `block_cider.has_cider`: 40/40 true
- `pain_only_exit`: 0건
- capital continuity: PASS, final `capital_after=25`
- status pointer after audit: Block 041

## 3. Top Risks

1. **PF 전장 진입 시 금융 설명 과다 위험** — covenant와 haircut은 강의가 아니라 risk minutes, screening table, bank call, offtake letter 장면으로 처리해야 한다.
2. **백인호 바보화 위험** — credit risk 반대는 합리적이어야 한다. 도윤은 그를 꺾기보다 covenant 조건과 담보 재평가로 이용해야 한다.
3. **pilot budget 과속 위험** — 아직 후보 gate다. 실제 allocation authority는 다음 10블록 끝에서 조건부로 열어야 한다.
4. **고객/투자자 리스크 단절 위험** — SLA dashboard와 investor appendix를 PF covenant의 revenue risk로 이어야 한다.
5. **자기중심성 희석 위험** — 금융 안정, 고객 보호, 지역 민원 관리는 선의가 아니라 예산 gate와 financing 조건을 열기 위한 계산이어야 한다.

## 4. Repair Targets

- same-turn repair 필요: 없음.
- next envelope 착수 전 확인:
  - 첫 장면은 재무기획실이나 risk committee에서 screening table이 covenant 벽에 막히는 장면으로 시작할 것.
  - 백인호는 감정적 반대자가 아니라 숫자와 신용등급을 보는 합리적 gatekeeper로 쓸 것.
  - offtake letter는 매출 확정이 아니라 금융기관이 보는 수요 proof seed로 작게 열 것.
  - 손실 블록은 반드시 담보 재평가나 haircut 완화 조건을 남길 것.

## 5. Next 10 Focus

1. **PF covenant wall** — screening table이 금융 covenant 조건과 충돌한다.
2. **credit risk opposition** — 백인호가 데이터센터 리스크를 신용등급과 차입 조건으로 반대한다.
3. **offtake seed** — 고객 dashboard와 PPA milestone을 offtake letter로 바꾼다.
4. **bank haircut** — 은행단이 담보가치를 깎으며 실제 자본 압박을 만든다.
5. **loss and collateral repricing** — 일부 담보를 낮게 인정하고 대신 covenant 구조를 얻는다.
6. **PPA/offtake package** — 전력 판매와 고객 수요를 하나의 financing package로 묶는다.
7. **credit scare** — 외부 경쟁사 신용 이벤트를 public proof로 환전한다.
8. **conditional pilot budget** — 전액 승인이 아니라 tranche 조건부 budget gate를 연다.

## 6. Gate Result

- 10-block self-audit: PASS
- repair required before Block 41: none
- Block 41 entry: allowed
- BI entry: blocked until full 70-block TR and source TR handoff gate PASS
