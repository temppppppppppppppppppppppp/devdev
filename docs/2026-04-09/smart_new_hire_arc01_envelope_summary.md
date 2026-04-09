# smart_new_hire ARC-01 envelope summary

Date: 2026-04-09
Source: `treatments/smart_new_hire_tr_block_001_draft.json` (saved boundary: Block 10, ARC-01 full)
Authority: read-only extract. The TR file above is the binding truth. This summary is a convenience snapshot, not an authority.
Scope: Block 1-10 only (ARC-01 `숫자를 읽는 신입`).

## 1. Capital Chain (strict equality, Block 1-10)

| Block | Title | capital_before | capital_after |
|---|---|---|---|
| 1 | 사탕 하나 | 회의실 세팅만 맡는 신입 동선 | 전일 매출 취합 파일 읽기 전용 접근 |
| 2 | 숨김 열 | 전일 매출 취합 파일 읽기 전용 접근 | 전사 공유 메일 실명 노출 |
| 3 | 예외코드 | 전사 공유 메일 실명 노출 | 오전 브리핑 시트 owner |
| 4 | 원장 원본 | 오전 브리핑 시트 owner | 원장 원본 조회권 |
| 5 | 리베이트 라인 | 원장 원본 조회권 | 부서장 메모 상신 + 문제 line freeze |
| 6 | 교체권 | 부서장 메모 상신 + 문제 line freeze | 거래처 교체 검토권 + 소액 실행 예산 + 임원 리뷰 배석권 |
| 7 | 배석 | 거래처 교체 검토권 + 소액 실행 예산 + 임원 리뷰 배석권 | 임원 질문 응답권 + 후속 검토 자료 초안 담당 |
| 8 | 정답 말고 책임자 (quiet) | 임원 질문 응답권 + 후속 검토 자료 초안 담당 | 임원 질문 응답권 + 후속 검토 자료 초안 담당 (내부 doctrine 고정) |
| 9 | 비교표 | 임원 질문 응답권 + 후속 검토 자료 초안 담당 (내부 doctrine 고정) | 파일럿 검토안 초안 담당 |
| 10 | 파일럿 | 파일럿 검토안 초안 담당 | 조건부 파일럿 검토권 + 현장/재무 데이터 풀 접근 입장권 |

Each row's `capital_before` equals the previous row's `capital_after` byte-exact. Verified by `A5 capital chain strict equality: PASS` in Block 1-10 self-audit.

## 2. Cider Ledger

Opening envelope cider ledger (canon §3A lock — must not change under `tr_continue`):

| Block | has_cider | receipt_type | pain_only_exit |
|---|---|---|---|
| 2 | true | proof | false |
| 3 | true | reevaluation | false |
| 4 | true | visible_token | false |
| 5 | true | protection | false |
| 6 | true | next_gate_opening | false |

Post-opening conversion (Block 7-10):

| Block | has_cider | receipt_type | notes |
|---|---|---|---|
| 7 | true | proof | 임원 회의 질문 방향 전환 |
| 8 | false | null | quiet block, internal doctrine pass, `is_quiet_block: true`, tension_level 3 |
| 9 | true | reevaluation | 파일럿 후보 비교표가 조직의 공통 서식으로 채택 |
| 10 | true | next_gate_opening | ARC-01 → ARC-02 환전, 현장/재무 데이터 풀 접근 입장권 |

Block 1 is `access` (setup payment, not opening rescue). Block 7+ does not carry opening rescue duty. Block 8 is the Phase0-locked quiet block (`quiet_blocks: [8]`).

## 3. Callback / Foreshadow Matrix

| Block | callback_sources | foreshadow_targets |
|---|---|---|
| 1 | — | 2, 3, 5, 8 |
| 2 | 1 | 3, 4, 5, 7 |
| 3 | 2 | 4, 5, 8, 33 |
| 4 | 3 | 5, 6, 33, 39 |
| 5 | 3, 4 | 6, 7, 33, 39 |
| 6 | 4, 5 | 7, 9, 10, 32 |
| 7 | 4, 5, 6 | 9, 10, 23, 29 |
| 8 | 1, 2, 3, 4, 5, 6, 7 | 9, 10, 35, 49 |
| 9 | 7, 8 | 10, 11, 12, 14 |
| 10 | 6, 7, 8, 9 | 11, 12, 17, 37 |

Invariants verified in audit: callback_sources strictly backward (< block_no), foreshadow_targets strictly forward (> block_no).

Cross-ARC foreshadow anchors (Block 1-10 → later blocks):
- → B17 (ARC-02 defeat block `역풍`): 조건부 파일럿 검토권의 종료 조건 장치가 defeat 방어로 회수된다
- → B23 (ARC-03 의제 전환): 세 칸 비교표 형식이 임원 회의 의제 전환 도구로 계승된다
- → B29 (ARC-03 방향 설계안): 후속 검토 자료 초안 서식이 ARC-03 방향 설계안의 뼈대가 된다
- → B32 (ARC-04 owner 충돌): 소액 실행 예산 경계선 설계가 예산 코드 owner 충돌의 전사가 된다
- → B33 (ARC-04 공동 검토선): 오세린과의 좁은 통로가 공식 공동 검토선의 씨앗이다
- → B35 (ARC-04 실행 책임표): 원칙표 v0.1이 실행 책임표의 초기 서식이 된다
- → B37 (ARC-04 예산 동결 defeat): 종료 조건 설계가 defeat 이후 보호선 재가동의 근거가 된다
- → B39 (ARC-04 공동 결재): 재무 공동 숫자 축이 joint authority의 원형으로 회수된다
- → B49 (ARC-05 기준표): 원칙표 v0.1이 '사람이 아니라 재사용 가능한 구조' 증명의 출발점이 된다

## 4. POV / Location / Time Coverage

- POV: 윤도혁 (10/10 블록, Phase0 POV lock 준수)
- Location type: 본사 (10/10 블록) — ARC-01은 전 구간 세광리테일 본사 11층 채널운영팀 ~ 15층 임원 회의실 ~ 재무 파트너 좌석으로 제한
- In-story time window: 2026년 3월 첫째 주 월요일 아침 (B1) ~ 2026년 3월 셋째 주 금요일 오후 (B10) = 약 3주
- Phase0 ARC-01 time_window (`2026년 3월~2026년 4월`) 내부에 안전하게 들어감

## 5. Doctrine Line (Block 별 execution_doctrine 요약)

1. 숫자를 고치기 전에 먼저 그 숫자에 닿는 권한을 확보한다.
2. 숫자를 다 설명하기보다 판단 흐름을 바꾸는 한 줄을 먼저 만든다.
3. 정답보다 먼저 owner를 세워야 조직이 움직인다.
4. 증상에 반응하지 말고 원본을 잡아 원인을 증명한다.
5. 정답을 보여 주는 데서 멈추지 않고, 조직이 바로 쓸 보호선까지 설계한다.
6. 결정을 대신 내리지 말고, 상급자가 고를 수 있는 경계선을 먼저 그려 권한을 회수한다.
7. 배석자의 힘은 발언이 아니라 회의 직전에 올려 둔 한 장의 구성이다.
8. 정답을 혼자 알고, 책임자부터 세운다. 근거는 원본, 권한 경계선은 상급자, 보호선은 좁게, 다음 전장은 이전 블록의 영수증으로만. (원칙표 v0.1)
9. 후보 한 곳을 찍지 말고, 선택 축 세 개와 묶음 세 개로 상급자의 결정 공간을 설계한다.
10. 승인 자체를 목표로 삼지 말고, 목적/통과 조건/종료 조건을 같이 설계해 다음 전장의 입장권까지 같은 회의에서 회수한다.

## 6. ARC-01 Exit State → ARC-02 Entry Gate

- 최종 자원 상태(`Block 10 capital_after`): 조건부 파일럿 검토권 + 현장/재무 데이터 풀 접근 입장권
- ARC-01 exit 조건(Phase0 locked): 파일럿 검토권 확보 ✅
- ARC-02 entry_function(Phase0 locked): 팀 안 유능함을 현장 실적으로 환전하는 아크
- ARC-02 Block 11 slot: `데이터 풀` — 파일럿 대상 데이터 풀에 처음 접근한다
- 첫 ARC-02 블록이 재사용할 ARC-01 자산:
  - Block 10의 조건부 검토권 → 현장 실접근 전환의 근거
  - Block 4의 원장 원본 조회권 → 데이터 풀 요청 시 검증 가능한 요청 이력
  - Block 7의 세 칸 비교표 / Block 8의 원칙표 v0.1 → 실접근 범위 설계 서식

## 7. Downstream Readiness

- BI 초안: 아직 금지 상태. Block 1-10만으로 BI 초안을 열 수 있다는 자동 추론은 불가. fresh operator order 필요.
- work_guard: BI 초안 이후의 경로. 현재 단계에서 접근 금지.
- 다음 tr_continue: Block 11-15 (ARC-02 전반부), 5블록 캡 준수.

## 8. Self-Audit Trail

Block 1-10 self-audit (2026-04-09 tr_continue):

- A1 schema parse: PASS
- A2 block count == 10: PASS
- A3 block_no sequential 1..10: PASS
- A4 Block 1-5 byte-exact (receipt_line 해시 일치): PASS
- A5 capital chain strict equality: PASS (Block 7/9 초안 드리프트는 동일 세션에서 수리)
- A6 opening 2-6 canon ledger preserved: PASS
- A7 Block 1 not opening rescue: PASS
- A8 Block 8 quiet (no cider, low tension, is_quiet_block): PASS
- A9 Block 7+ not opening rescue: PASS
- A10 ARC-01 exit = 파일럿 검토권: PASS
- A11 pain_only_exit all false: PASS
- A12 callback_sources backward-only: PASS
- A13 foreshadow_targets forward-only: PASS
- A14 special_ability stable (업무 비서형 안내문): PASS
- A15 contamination guard (약물/상태창/전지적 예지 없음): PASS
- A16 POV 윤도혁 stable: PASS
- A17 metadata (_total_blocks=10 / _saved_block_boundary=10 / _next_continuation_boundary=11): PASS

Overall: ALL PASS.
