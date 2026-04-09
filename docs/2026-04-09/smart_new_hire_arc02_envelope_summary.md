# smart_new_hire ARC-02 envelope summary

Date: 2026-04-09
Source: `treatments/smart_new_hire_tr_block_001_draft.json` (saved boundary: Block 20, ARC-02 full)
Authority: read-only extract. The TR file above is the binding truth. This summary is a convenience snapshot, not an authority.
Scope: Block 11-20 only (ARC-02 `파일럿은 실적이 된다`).
Companion: `docs/2026-04-09/smart_new_hire_arc01_envelope_summary.md` (Block 1-10, ARC-01).

## 1. Capital Chain (strict equality, Block 11-20)

| Block | Title | capital_before | capital_after |
|---|---|---|---|
| 11 | 데이터 풀 | 조건부 파일럿 검토권 + 현장/재무 데이터 풀 접근 입장권 | 현장 원장 3필드 + 재무 집계 3필드 읽기 전용 실접근 (오세린 로그 공동 열람 포함) |
| 12 | 체크리스트 | 현장 원장 3필드 + 재무 집계 3필드 읽기 전용 실접근 (오세린 로그 공동 열람 포함) | 파일럿 공통 체크리스트 v0.1 서식 owner |
| 13 | 점장 회의 | 파일럿 공통 체크리스트 v0.1 서식 owner | 현장 병목 순서 회의록 owner (점장 4인 직접 지목) |
| 14 | 병목 맵 (quiet) | 현장 병목 순서 회의록 owner (점장 4인 직접 지목) | 동일 + 내부 원칙표 v0.2 '지목 영수증 보존' 조항 추가 |
| 15 | 첫 반전 | 동일 + 내부 원칙표 v0.2 | 조건부 첫 반전 증거 owner + 거래처 협상 배석권 입장권 + 감사 대응 근거 등록 |
| 16 | 협상 배석 | 조건부 첫 반전 증거 owner + 거래처 협상 배석권 입장권 + 감사 대응 근거 등록 | 계약 조항 사전 리뷰 담당 + 조항 17 owner 명시 수정 약속 기록 |
| 17 | 역풍 (defeat) | 계약 조항 사전 리뷰 담당 + 조항 17 owner 명시 수정 약속 기록 | 동일 + 조건부 파일럿 검토권 검토 중지 상태 (방어선 4개 유지) |
| 18 | 반증표 | 동일 + 조건부 파일럿 검토권 검토 중지 상태 (방어선 4개 유지) | 계약 조항 사전 리뷰 담당 + 조건부 파일럿 검토권 복원 + 재무 공동 반증표 owner + 산식 희석 구조 감사 근거 등록 |
| 19 | 권역 보고 | (위 Block 18 capital_after) | 권역 보고서 공동 발제자 + 임원 질문 10개 preview owner |
| 20 | 질문권 | 권역 보고서 공동 발제자 + 임원 질문 10개 preview owner | 권역 운영 수정권 + 임원 질문 직접 응답권 + ARC-03 특수 검토 자료 담당 입장권 |

Block 11-20 capital chain strict equality: verified `A5 PASS` in Block 1-20 self-audit.

## 2. Cider Ledger (ARC-02)

| Block | has_cider | receipt_type | pain_only_exit | notes |
|---|---|---|---|---|
| 11 | true | access | false | 입장권 → 실접근 전환 (풀 전체가 아닌 세 필드 좁은 요청) |
| 12 | true | proof | false | 파일럿 공통 체크리스트 v0.1 공식 채택 (부서 서식 관성 돌파) |
| 13 | true | reevaluation | false | 점장 4인 직접 지목 회의록 (본사-현장 해석 구조 변경) |
| 14 | false | null | false | quiet block, 원칙표 v0.2 '지목 영수증은 합치지 않는다' 조항, `is_quiet_block: true`, tension_level 3 — Phase0 `quiet_blocks: [14]` lock |
| 15 | true | next_gate_opening | false | 조건부 반전 증거 + 감사 대응 근거 등록 + 거래처 협상 배석권 입장권 |
| 16 | true | visible_token | false | 계약 조항 사전 리뷰 담당 + 조항 17 owner 명시 수정 약속 기록 |
| 17 | **false** | **null** | **false** | **defeat block**, `is_defeat_block: true`, tension_level 9, emotional_beat defeat/9 — Phase0 `defeat_blocks: [17]` lock |
| 18 | true | proof | false | 파일럿 검토권 복원 + 재무 공동 반증표 owner + 산식 희석 구조 감사 근거 등록 |
| 19 | true | visible_token | false | 권역 보고서 공동 발제자 + 임원 질문 10개 preview owner |
| 20 | true | next_gate_opening | false | 권역 운영 수정권 + 임원 질문 직접 응답권 + ARC-03 특수 검토 자료 담당 입장권 (ARC-02 Phase0 exit 일치) |

Pain_only_exit는 defeat block(17)을 포함해 전 블록 `false` — contamination guard 준수.

## 3. Defeat Block Audit (Block 17)

Phase0 lock: `ARC-02 defeat_blocks: [17]`.

### Defeat 발생 구조
- 공격 축: 기존 KPI 해석 권한 기반 (채널전략 실무 라인)
- 공격 무기: '채널 전체 KPI 1.3% 악화' (산식 자체는 사실)
- 공격 목적: 파일럿 반전 수치가 기존 부서 권한 기반을 흔들지 못하게 하는 것
- 결과: 조건부 파일럿 검토권이 '검토 중지 상태'로 일시 동결 (line 종료는 아님)

### Defeat 방어선 (사전 등록된 4개)
Block 17의 defeat가 line 종료가 아닌 일시 동결로 제한된 이유 — 모두 이전 블록에서 사전 등록된 자산:

1. **Block 15 조건문 세 줄** — 점장 지목 영수증 유지 / 원본 플래그 이중 찍힘 제거 감사 로그 / 파일럿 종료 조건 변경 금지. 산식 공격이 조건문 안쪽까지는 들어오지 못함.
2. **Block 15 감사 대응 근거 등록** — 오세린이 조건문 자체를 감사 대응 근거로 등록함. 감사 권한은 기존 KPI 해석 권한보다 상위.
3. **Block 13 점장 4인 직접 지목 영수증 원본 보존** — Block 14 원칙표 v0.2 '지목 영수증은 합치지 않는다' 조항 덕에 '본사 신입 해석'으로 축소되지 않음. 현장 발언이 발언 그대로 남아 있어 defeat 공격이 현장 근거를 건드리지 못함.
4. **Block 11 오세린 재무 공동 검토 라인** — 재무 공동 검토 라인은 흔들리지 않음. Block 16의 계약 조항 사전 리뷰 담당 + 조항 17 수정 약속도 그대로 유지.

### Defeat 회수 경로 (Block 17 → Block 18)
- Block 18에서 '반박표' 대신 '같은 표' 구조로 산식 자체를 건드리지 않고 산식 희석 구조를 감사 근거에 등록
- 결과: 검토 중지 해제 + 재무 공동 반증표 owner 신규 확보 + 산식 희석 구조 감사 근거 등록 = defeat 이전보다 **구조적으로 더 강한 자리**

### Self-audit 증거
- `A8d Phase0 defeat_blocks lock [17]: PASS`
- `A8e Block 17 defeat schema (no cider, pain_only_exit=false, tension>=8, beat=defeat): PASS`
- `A11 pain_only_exit all false (inc. defeat block): PASS`
- `A23 Block 18 recovers Block 17 defeat (검토 중지 → 복원): PASS`
- `A24 Block 17 cites Block 15 조건문 방어선: PASS`

## 4. Callback / Foreshadow Matrix (ARC-02)

| Block | callback_sources | foreshadow_targets |
|---|---|---|
| 11 | 4, 8, 10 | 12, 13, 15, 17, 33 |
| 12 | 3, 7, 8, 11 | 13, 14, 15, 29, 49 |
| 13 | 4, 7, 12 | 14, 15, 19, 24 |
| 14 | 8, 13 | 15, 17, 19, 49 |
| 15 | 4, 10, 13, 14 | 16, 17, 19, 39 |
| 16 | 5, 7, 15 | 17, 19, 29, 35, 39 |
| 17 | 10, 13, 14, 15 | 18, 19, 37 |
| 18 | 11, 12, 15, 17 | 19, 20, 37, 39, 49 |
| 19 | 7, 13, 14, 18 | 20, 21, 23, 46 |
| 20 | 7, 13, 17, 18, 19 | 21, 22, 23, 39, 47 |

Invariants: callback_sources backward-only (< block_no), foreshadow_targets forward-only (> block_no) — `A12/A13 PASS`.

Cross-ARC anchor 회수 상태 (Block 11-20가 실제로 Block 1-10 자산을 회수한 기록):
- B4 원장 원본 조회권 → B11 (신입 좁은 접근 선례), B13 (C 점장 이중 찍힘 발언 근거), B15 (반전 직접 원인)
- B5 line freeze → B16 (거래처 재계약 협상 직접 이어짐)
- B7 세 칸 비교표 + 발언 아끼기 → B12 (여섯 칸 확장), B16 (협상 방식), B19 (보고서 상단), B20 (임원 회의 진화)
- B8 원칙표 v0.1 → B11 (권한 경계선), B12 (기존 서식 보존), B14 (원칙표 v0.2 확장)
- B10 목적/통과/종료 세 조건 → B11 (근거), B15 (조건문 세 줄), B17 (defeat 방어선)
- B13 점장 회의 '물어볼 자리' → B19 (권역 질문 10개 preview), B20 (답변 + 다음 질문 2개)

Forward 전개 (ARC-03 이후로 심어진 foreshadow):
- → B21 '특수 검토' (ARC-03 entry): B19/B20에서 ARC-03 특수 검토 호출 통로 언급
- → B22 '충돌 봉합', B23 '의제 전환', B24 'cross-team' (ARC-03 front): B20에서 채널전략 라인 관계 구조 변경
- → B29 '방향 설계안' (ARC-03): B12 체크리스트 / B16 조항 리뷰 확장
- → B33 '공동 검토선' (ARC-04): B11 오세린 로그 공동 열람 / B15 감사 근거
- → B35 '실행 책임표' (ARC-04): B16 계약 조항 리뷰 방식
- → B37 '예산 동결 defeat' (ARC-04): B17 defeat 방어선 패턴 재사용 + B18 산식 희석 구조
- → B39 '공동 결재 복원' (ARC-04): B15/B16/B18/B20 재무 공동 라인 누적
- → B46 '심사 자료' (ARC-05): B19 질문 10개 preview 방식
- → B47 '독자 조건표' (ARC-05): B20 권역 운영 수정권
- → B49 '기준표' (ARC-05): B12 여섯 칸 서식 + B14 원칙표 v0.2 + B18 같은 표

## 5. POV / Location / Time Coverage (ARC-02)

- POV: 윤도혁 (10/10, Phase0 POV lock 준수)
- Location type: 본사 (9/10) + 사적 공간 (1/10, Block 14 quiet는 자택 책상). ARC-02는 현장 진입 아크이지만 실제 장면은 본사 내부에서 처리 — 세광리테일 본사 3층(점장 회의) / 9층(협상) / 11층(채널운영팀) / 15층(임원 회의) + 재무 파트너 좌석 + IT 운영 파트
- In-story time: 2026년 3월 넷째 주 월요일 (B11) ~ 2026년 5월 첫째 주 월요일 (B20) = 약 6주
- Phase0 ARC-02 time_window (`2026년 4월~2026년 7월`) 내부에 대체로 들어가며, 3월 넷째 주 ~ 4월 첫째 주 구간은 ARC-01과 overlap 허용 구간 사용

## 6. Doctrine Line (Block 11-20 execution_doctrine 요약)

11. 풀 전체를 요구하지 말고, 통과 조건 증명에 필요한 최소 필드를 gatekeeper별로 분리 요청한다.
12. 기존 서식을 버리지 말고, 그 위에 세 축 공통 순서 한 층을 얹어 owner 권한을 회수한다.
13. 현장에 답을 들고 가지 말고, 질문 틀만 들고 가서 현장이 순서를 직접 지목하게 한다.
14. 현장의 지목 영수증은 합치지 않는다. 반전 데이터가 합쳐 줄 때까지 원본 발언을 보존한다. (원칙표 v0.2)
15. 반전 수치를 먼저 자랑하지 말고, 지목 원문과 조건문을 함께 걸어 방어 구조 안쪽에서 반전을 드러낸다.
16. 협상석에서는 주장을 늘리지 말고, 기존 문서에서 책임 주체가 명시되지 않은 조항을 먼저 짚는다.
17. defeat가 올 때 즉시 반박하지 않고, 사전에 등록해 둔 조건문과 감사 근거가 defeat를 line 종료가 아닌 일시 동결로 제한하도록 기다린다.
18. 해석 싸움이 될 수치 공격 앞에서는 반박표 대신 '같은 표'를 만들어 산식 구조 자체를 드러낸다.
19. 보고서를 먼저 쓰지 말고, 임원이 물을 질문 10개를 먼저 뽑아 역순으로 뼈대를 설계한다.
20. 좋은 답변으로 경계를 긋지 말고, 답변마다 다음 질문 2개를 같이 내놓아 권한을 다음 전장으로 이동시킨다.

## 7. ARC-02 Exit State → ARC-03 Entry Gate

- 최종 자원 상태(`Block 20 capital_after`): 권역 운영 수정권 + 임원 질문 직접 응답권 + ARC-03 특수 검토 자료 담당 입장권
- ARC-02 exit 조건(Phase0 locked `capital_target`): 파일럿 검토권 → 권역 운영 수정권 + 임원 질문권 ✅
- ARC-03 entry_function(Phase0 locked): 칭찬보다 ownerliness를 증명하는 아크
- ARC-03 Block 21 slot: `특수 검토` — 임원 특수 검토 자료의 초안을 맡는다
- ARC-03 defeat block: Block 25 `이름 없는 공` — 공로는 뺏기고 follow-up 책임만 남음. ARC-02 Block 17 방어선 패턴을 구조적으로 재사용할 필요 있음.

### 첫 ARC-03 블록이 재사용할 ARC-02 자산
- Block 12 여섯 칸 공통 상단 서식 → 특수 검토 자료 상단 틀
- Block 13 점장 회의 '물어볼 자리' 방식 → cross-team 호출에서 재사용
- Block 14 원칙표 v0.2 → 이름 없는 공 defeat 방어선 (해석 이동 차단)
- Block 15 조건문 세 줄 구조 → 특수 검토 자료 사전 방어 구조
- Block 18 '같은 표' 방식 → 의제 전환(B23) 기본 서식
- Block 19 질문 10개 preview → 특수 검토 자료 사전 배포 패턴
- Block 20 답변 + 다음 질문 2개 → ARC-03 임원 응대 전체의 표준 방식

## 8. Downstream Readiness

- **BI 초안**: 이전까지는 구조적으로 금지였으나, ARC-01 full + ARC-02 full이 저장된 현 시점부터 구조적 금지가 해제된다. opening envelope(B1-10)와 첫 아크 환전(B11-20)이 모두 disk에 있으므로 BI는 이제 '충분한 TR 근거' 조건을 만족한다. 다만 fresh operator order가 여전히 필수이며, 자동 시작 금지. BI 스코프 확정 시 필요한 것:
  - 화자 lock (1인칭 도혁 vs 3인칭)
  - 1화 분량 규칙 (보통 5,000~6,000자)
  - opening 2~6 cider ledger를 1화 안에 어디까지 반영할지
  - 파일럿 증거 구조 재사용 여부 (1화에 조건문 세 줄을 미리 심을지 여부)
- **work_guard**: BI 초안 이후의 경로. 현재 단계에서는 접근 금지 유지.
- **다음 tr_continue**: Block 21-25 (ARC-03 전반부), 5블록 캡 준수, Block 25 defeat 블록은 Block 17 방어선 패턴 재사용 필요.

## 9. Self-Audit Trail

Block 1-20 self-audit (2026-04-09 tr_continue ARC-02 back half):

- A1 schema parse: PASS
- A2 block count == 20: PASS
- A3 block_no sequential 1..20: PASS
- A4 Block 1-10 byte-exact (receipt_line): PASS
- A4b Block 11-15 byte-exact (receipt_line): PASS
- A5 capital chain strict equality Block 1-20: PASS
- A6 opening 2-6 canon ledger preserved: PASS
- A7 Block 1 not opening rescue: PASS
- A8 Block 8 quiet: PASS
- A8b Block 14 quiet: PASS
- A8c Phase0 quiet_blocks lock [8, 14]: PASS
- A8d Phase0 defeat_blocks lock [17]: PASS
- A8e Block 17 defeat schema (no cider, pain_only_exit=false, tension>=8, beat=defeat): PASS
- A9 Block 7+ not opening rescue: PASS
- A10 ARC-01 exit Block 10 = 파일럿 검토권: PASS
- A10b ARC-02 exit Block 20 = 권역 운영 수정권 + 임원 질문권: PASS
- A10c Block 11-20 titles match Phase0 ARC-02 slots: PASS
- A11 pain_only_exit all false (inc. defeat block): PASS
- A12 callback_sources backward-only: PASS
- A13 foreshadow_targets forward-only: PASS
- A14 special_ability stable (업무 비서형 안내문): PASS
- A15 contamination guard (약물/상태창/전지적 예지 없음): PASS
- A16 POV 윤도혁 stable: PASS
- A17 metadata (_total_blocks=20 / _saved_block_boundary=20 / _next_continuation_boundary=21): PASS
- A18 Block 16-20 receipt type diversity: PASS
- A20 no stray keys in Block 16-20: PASS
- A21 cross-audit Block 16-20 callback to Block 1-15: PASS
- A22 Block 20 opens Block 21 gate (ARC-03 entry): PASS
- A23 Block 18 recovers Block 17 defeat (검토 중지 → 복원): PASS
- A24 Block 17 cites Block 15 조건문 방어선: PASS
- A25 Block 11-20 in-story time within ARC-02 window: PASS

Overall: ALL PASS.
