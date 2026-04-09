# smart_new_hire ARC-03 envelope summary

Date: 2026-04-09
Source: `treatments/smart_new_hire_tr_block_001_draft.json` (saved boundary: Block 30, ARC-03 full)
Authority: read-only extract. The TR file above is the binding truth. This summary is a convenience snapshot, not an authority.
Scope: Block 21-30 only (ARC-03 `칭찬보다 ownerliness를 증명한다`).
Companions: `docs/2026-04-09/smart_new_hire_arc01_envelope_summary.md` (Block 1-10) · `docs/2026-04-09/smart_new_hire_arc02_envelope_summary.md` (Block 11-20).

## 1. Capital Chain (strict equality, Block 21-30)

| Block | Title | capital_before | capital_after |
|---|---|---|---|
| 21 | 특수 검토 | 권역 운영 수정권 + 임원 질문 직접 응답권 + ARC-03 특수 검토 자료 담당 입장권 | 특수 검토 자료 초안 담당 + sponsor 경로 lock (sponsor: 영업관리본부장, 경로: 임원 비서실 → 본부장 → 검토 임원) |
| 22 | 충돌 봉합 | (= Block 21 after) | + 세 부서 공동 검토 라인 lock |
| 23 | 의제 전환 | (= Block 22 after) | + 감사 근거 로그 인용 권한 회의 기록 명시 |
| 24 | cross-team | (= Block 23 after) | + cross-team 호출권 + 호출 접수 기준표 공식 규정 owner |
| 25 | 이름 없는 공 (defeat) | (= Block 24 after) | 동일 + 자료 상단 라벨 '초안 작성자 → follow-up 책임자' 변경 상태 + 일주일 내 규정 위반 재확인 약속 |
| 26 | 로그 복원 | (= Block 25 after) | 동일 + 자료 본문 owner 로그 세 개 입증 완료 + 재무 본부장급 공식 의견 사전 등록 (follow-up 책임자는 초안 작성자와 구조상 분리 불가) |
| 27 | owner | (= Block 26 after) | 특수 검토 자료 초안 담당 복원 + sponsor 경로 lock 확장 (5줄: sponsor / 경로 / 초안 작성자 / 공동 정리 책임자 / 검토 임원) + 세 부서 공동 검토 라인 lock + 감사 근거 로그 인용 권한 + cross-team 호출권 + 호출 접수 기준표 공식 규정 v2 (follow-up 책임자 승계 금지 수정 조항 포함) |
| 28 | 패턴표 (quiet) | (= Block 27 after) | 동일 + 반복 문제 패턴표 v0.1 + 원칙표 v0.3 '사전 방어선 설계' 조항 추가 (내부 doctrine 고정) |
| 29 | 방향 설계안 | (= Block 28 after) | 방향 설계안 owner + 세 분기 공식 서식 등록 (분기별 조건/owner/기간/종료 조건 네 칸 구조) + 재무 본부장급 공동 결재선 준 지분 |
| 30 | 임시 PM | (= Block 29 after) | 임시 PM 역할 + 공동 검토선 3인 필수 서명 구조 설계자 (PM: 도혁 / 공동 검토선: 한성우 + 오세린 + 채널전략팀장) + ARC-04 예산/책임선 전장 입장권 |

Block 21-30 capital chain strict equality: verified `A5 PASS` in Block 1-30 self-audit (2026-04-09). Same-turn repair 1건 기록: Block 28 capital_before·after 와 Block 29 capital_before 의 `위 자산 전부 유지` shorthand + `(5줄)`·`(follow-up 책임자 승계 금지 수정 조항 포함)` 괄호 축약이 Block 27 capital_after authoritative 풀 표기와 byte-exact 동기화로 정규화됨 (의미 변화 0).

## 2. Cider Ledger (ARC-03)

| Block | has_cider | receipt_type | pain_only_exit | notes |
|---|---|---|---|---|
| 21 | true | visible_token | false | 특수 검토 자료 초안 담당 공식 확정 + sponsor 경로 네 줄 lock |
| 22 | true | proof | false | 세 부서 공동 검토 라인 lock + 채널전략팀 첫 사전 조율 제안 |
| 23 | true | reevaluation | false | Block 18 감사 근거 로그 근거로 의제 전환 차단 + 감사 근거 로그 인용 권한 회의 기록 공식 명시 |
| 24 | true | visible_token | false | cross-team 호출권 + 호출 접수 기준표 공식 규정 owner (sponsor/통과/종료/follow-up 네 칸) |
| 25 | **false** | **null** | **false** | **defeat block**, `is_defeat_block: true`, tension_level 9, emotional_beat defeat/9 — Phase0 `defeat_blocks: [25]` lock. 공로 탈취 + 자료 상단 라벨 변경 + 일주일 내 규정 위반 재확인 조건 확보(회수 경로 다음 블록으로 이동) |
| 26 | true | proof | false | 자료 본문 owner 로그 세 개 입증 + 재무 본부장급 공식 의견 사전 등록 (ARC-02 Block 18 '같은 표' 구조 parity) |
| 27 | true | reevaluation | false | 본문 owner 복원 + sponsor 경로 5줄 확장 + 호출 접수 기준표 공식 규정 v2 (follow-up 책임자 승계 금지 수정 조항 포함) — defeat 회수 완결 |
| 28 | false | null | false | quiet block, 반복 문제 패턴표 v0.1 + 원칙표 v0.3 '사전 방어선 설계' 조항, `is_quiet_block: true`, tension_level 3 — Phase0 `quiet_blocks: [28]` lock |
| 29 | true | visible_token | false | 방향 설계안 owner + 세 분기 공식 서식 (조건/owner/기간/종료 조건 네 칸) + 재무 본부장급 공동 결재선 준 지분 |
| 30 | true | next_gate_opening | false | 임시 PM 역할 공식 부여 + 공동 검토선 3인 필수 서명 구조 등록 + ARC-04 예산/책임선 전장 입장권 (ARC-03 Phase0 exit 일치) |

Pain_only_exit는 defeat block(25)을 포함해 전 블록 `false` — contamination guard 준수.

## 3. Defeat Block Audit (Block 25)

Phase0 lock: `ARC-03 defeat_blocks: [25]`.

### Defeat 발생 구조
- 공격 축: 호출 접수 기준표 공식 규정의 `follow-up 책임자` 조항 해석 (본부 정치 안쪽 공로 이동)
- 공격 무기: 자료 상단 라벨 '초안 작성자 → follow-up 책임자' 변경 (본문은 건드리지 않음)
- 공격 목적: Block 21-24에서 도혁이 쌓은 특수 검토 자료 owner 지위를 `follow-up 책임자` 라벨로 이동시켜, 실제 공로가 다른 사람 이름으로 기록되게 하는 것
- 결과: 자료 본문은 그대로, 상단 라벨만 바뀐 상태로 defeat 발생. line 종료 아님

### Defeat 방어선 (사전 등록된 5개)
Block 25 defeat가 line 종료가 아닌 조건부 동결로 제한된 이유 — 모두 Block 21-24에서 사전 등록된 자산:

1. **Block 21 sponsor 경로 lock** — 자료 상단 네 줄 (sponsor / 경로 / 검토 임원) 이 원본 그대로 보존. 본문 작성자 이름이 sponsor 경로 안쪽에 박혀 있어 라벨 변경 한 번으로는 지워지지 않음.
2. **Block 22 세 부서 공동 검토 라인 lock + 기준/owner 라벨 방식** — 채널운영 / 채널전략 / 재무 세 칸 분리 서명 구조 덕에 한 부서가 owner를 일방적으로 이동시킬 수 없음.
3. **Block 23 감사 근거 로그 인용 권한 회의 기록 명시** — 감사 근거 로그는 본문 작성자 이름과 구조상 분리 불가. 감사 권한은 본부 정치 해석 권한보다 상위.
4. **Block 24 호출 접수 기준표 공식 규정 + follow-up 책임자 조항** — 호출 접수 기준표의 follow-up 책임자 조항 자체가 '본문 작성자와 동일해야 한다'를 공식 규정으로 담고 있음. 공격이 이 규정을 역이용하려 했지만 규정 원문이 방어선.
5. **자료 본문 원본 보존 + 일주일 내 규정 위반 재확인 약속** — Block 25 defeat 순간 도혁이 즉시 반박하지 않고 `일주일 내 규정 위반 재확인` 조건을 사전 등록된 규정으로 확보해 회수 경로를 Block 26-27로 넘김.

### Defeat 회수 경로 (Block 25 → Block 26-27)
- **Block 26**: 주장하지 않고 파일 이력(자료 본문 owner 로그 세 개)과 사전 등록된 규정 조항을 근거로 재무 본부장급 공식 의견 사전 등록. 재무 본부장급이 `감사 근거 로그 인용 권한은 본문 작성자 이름과 구조상 분리될 수 없고, follow-up 책임자는 호출 접수 기준표 공식 규정에 따라 초안 작성자와 동일해야 합니다` 공식 의견 회신. → Block 25 공격 무기(라벨 변경)의 구조적 근거가 회의실 밖에서 이미 무너짐.
- **Block 27**: 처벌 요구하지 않고 라벨 구조 자체를 5줄(sponsor / 경로 / 초안 작성자 / 공동 정리 책임자 / 검토 임원)로 확장. 이로써 `follow-up 책임자` 라벨과 `초안 작성자` 라벨이 동시에 자료 상단에 병존하게 되고, 호출 접수 기준표 공식 규정 v2에 `follow-up 책임자 승계 금지 수정 조항` 이 추가됨. 본문 owner 도혁 이름으로 복원 + 관계 구조(채널전략팀/공동 정리 책임자) 유지.
- **결과**: 본인 자리 복원 + 다음 defeat 선제 차단 doctrine(Block 28 패턴표 v0.1 + 원칙표 v0.3 '사전 방어선 설계') = defeat 이전보다 **구조적으로 더 강한 자리**. ARC-02 Block 17→18 회수 패턴과 완전 구조 parity.

### Self-audit 증거
- `A8d Phase0 defeat_blocks lock [17, 25]: PASS`
- `A8e Block 25 defeat schema (no cider, pain_only_exit=false, tension>=8, beat=defeat): PASS`
- `A11 pain_only_exit all false (inc. defeat block): PASS`
- `A23 Block 26-27 recovers Block 25 defeat (공로 탈취 → 본문 owner 복원 + 라벨 5줄 확장): PASS`
- `A24 Block 25 cites Block 21-24 사전 등록 방어선 5개: PASS`

## 4. Quiet Block Audit (Block 28)

Phase0 lock: `ARC-03 quiet_blocks: [28]`.

- `is_quiet_block: true`, `has_cider: false`, `tension_level: 3`, `emotional_beat: reflection/4`
- 위치: 세광리테일 본사 11층 채널운영팀 야근 자리 (사적/내부 공간 아님 — 본사 내부지만 회의 없는 혼자 정리 시간)
- doctrine: 반복 문제는 패턴표로 문서화하고, 동일 공격 재발 시 패턴표를 근거로 선제 방어선을 먼저 설계한다. 방어선 설계는 defeat가 온 뒤가 아니라 defeat가 예상될 때 미리 박는다.
- 내부 자산: 반복 문제 패턴표 v0.1 (Block 17 defeat + Block 25 defeat 공통 패턴 분석) + 원칙표 v0.3 '사전 방어선 설계' 조항 (Block 8 v0.1 → Block 14 v0.2 → Block 28 v0.3 진화 라인 고정)
- Block 8·14 quiet 블록과의 parity: 모두 tension≤4, has_cider=false, internal doctrine only, 공식 권한 변화 없음, 내부 자산만 축적

## 5. Callback / Foreshadow Matrix (ARC-03)

| Block | callback_sources | foreshadow_targets |
|---|---|---|
| 21 | 10, 19, 20 | 22, 23, 25, 35, 47 |
| 22 | 12, 17, 18, 21 | 23, 25, 35, 39 |
| 23 | 7, 18, 19, 22 | 24, 25, 37, 39 |
| 24 | 10, 17, 21, 23 | 25, 26, 27, 30, 40, 49 |
| 25 | 14, 17, 21, 22, 23, 24 | 26, 27, 28, 29, 30 |
| 26 | 14, 17, 23, 24, 25 | 27, 28, 29, 39, 49 |
| 27 | 3, 21, 22, 24, 26 | 28, 29, 30, 35, 37, 38, 39, 40 |
| 28 | 8, 14, 17, 25, 27 | 29, 30, 37, 49 |
| 29 | 9, 16, 22, 23, 28 | 30, 35, 39, 40, 49 |
| 30 | 22, 24, 27, 28, 29 | 31, 32, 33, 37, 39, 40, 47 |

Invariants: callback_sources backward-only (< block_no), foreshadow_targets forward-only (> block_no) — `A12/A13 PASS`.

Cross-ARC anchor 회수 상태 (Block 21-30이 실제로 Block 1-20 자산을 회수한 기록):
- B3 첫 자리 공식 확정 → B27 (owner 라벨 복원 순간 Block 3 공식 확정 패턴 재사용)
- B7 세 칸 비교표 → B22 (기준/owner 세 칸 분리 라벨), B23 (자료 순서 앞쪽으로 당기기)
- B8 원칙표 v0.1 → B28 (v0.3로 확장)
- B9 매장 첫 공식 발언권 → B29 (방향 설계안 owner 공식 지정)
- B10 파일럿 검토권 + 목적/통과/종료 세 조건 → B21 (ARC-03 entry 입장권), B24 (sponsor/통과/종료/follow-up 네 칸 기준표)
- B12 공통 체크리스트 서식 → B22 (세 부서 공동 검토 라인 서식)
- B14 원칙표 v0.2 → B25 (defeat 방어선 해석 차단), B26 (파일 이력 근거), B28 (v0.3 상속)
- B16 조항 17 수정 약속 → B29 (방향 설계안 공식 서식 등록 방식)
- B17 defeat 방어선 패턴 → B22·B25·B26·B27·B28 (전면 재사용)
- B18 감사 근거 등록 + 같은 표 → B22·B23·B26 ('같은 표' 구조 parity)
- B19 질문 10개 preview → B21 (sponsor 경로 lock 사전 설계)
- B20 답변 + 다음 질문 2개 → B21 (ARC-03 특수 검토 자료 담당 입장권 직접 환전)

Forward 전개 (ARC-04 이후로 심어진 foreshadow):
- → B31·B32·B33 (ARC-04 entry): B30 임시 PM 역할 + 공동 검토선 3인 필수 서명 구조가 ARC-04 킥오프 입구
- → B35 '실행 책임표' (ARC-04): B21 sponsor 경로 lock + B27 5줄 확장 + B29 세 분기 공식 서식
- → B37 '예산 동결 defeat' (ARC-04): B17 defeat 방어선 + B25 defeat 방어선 + B28 사전 방어선 설계 조항 패턴 재사용
- → B38 '관계 구조 침입' (ARC-04): B27 공동 정리 책임자 라벨 관계 구조
- → B39 '공동 결재 복원' (ARC-04): B22·B23·B26·B29 재무 공동 라인 누적
- → B40 'ARC-04 출구' (ARC-04): B24 cross-team 호출권 + B30 공동 검토선 3인 필수 서명 구조
- → B47 '독자 조건표' (ARC-05): B21 sponsor 경로 lock + B30 PM/공동 검토선 이중 구조
- → B49 '기준표' (ARC-05): B24 호출 접수 기준표 공식 규정 + B26 파일 이력 근거 + B28 원칙표 v0.3 + B29 세 분기 공식 서식

## 6. POV / Location / Time Coverage (ARC-03)

- POV: 윤도혁 (10/10, Phase0 POV lock 준수)
- Location type: 본사 (10/10) — 세광리테일 본사 11층 채널운영팀 + 15층 임원 특수 검토 회의실 / 영업관리본부장실 + 재무 파트너 좌석. ARC-03는 본사 임원 라인 진입 아크
- In-story time: 2026년 5월 둘째 주 월요일 (B21) ~ 2026년 7월 첫째 주 월요일 (B30) = 약 8주
- Phase0 ARC-03 time_window 내부

## 7. Doctrine Line (Block 21-30 execution_doctrine 요약)

21. 자료 작업 전에 sponsor와 경로를 네 줄로 자료 상단에 lock한다.
22. 기준 차이와 owner 차이가 있는 수치는 통합하지 말고, 세 칸 분리 + 기준/owner 라벨로 병렬 배치한다.
23. 발언 싸움 대신 이미 등록된 감사 근거 로그 한 줄을 자료 순서 앞쪽으로 당겨 의제 전환을 막는다.
24. 호출권을 받기 전에 sponsor/통과/종료/follow-up 네 칸 기준표를 먼저 박아 경계선을 설계한다.
25. 본문을 건드리지 않은 공로 이동 앞에서 즉시 반박하지 않고, 사전 등록된 규정으로 일주일 내 재확인 조건을 확보해 회수 경로를 다음 블록으로 넘긴다.
26. defeat 복원에서는 주장하지 말고, 파일 이력과 사전 등록된 규정 조항을 근거로 공식 의견을 먼저 확보한다.
27. defeat 회복에서는 처벌을 요구하지 말고, 라벨 구조 자체를 확장해 본문 owner 복원과 관계 구조 유지를 동시에 달성한다.
28. 반복 문제는 패턴표로 문서화하고, 동일 공격 재발 시 패턴표를 근거로 선제 방어선을 먼저 설계한다. 방어선 설계는 defeat가 온 뒤가 아니라 defeat가 예상될 때 미리 박는다.
29. 한 방향을 고르지 않고 세 분기 구조(조건/owner/기간/종료 조건 네 칸)로 병렬 제시해 세 임원/본부장을 동시에 붙잡는다.
30. PM 자리를 혼자 쥐지 말고, 공동 검토선 필수 서명 구조와 이중으로 설계해 단독 영웅화와 실행력 분산을 동시에 피한다.

## 8. ARC-03 Exit State → ARC-04 Entry Gate

- 최종 자원 상태(`Block 30 capital_after`): 임시 PM 역할 + 공동 검토선 3인 필수 서명 구조 설계자 (PM: 도혁 / 공동 검토선: 한성우 + 오세린 + 채널전략팀장) + ARC-04 예산/책임선 전장 입장권
- ARC-03 exit 조건(Phase0 locked `capital_target`): 특수 검토 자료 담당 → 임시 PM 역할 진입 ✅
- ARC-04 entry_function(Phase0 locked): 형의 라운드에서 본인 축을 유지하며 예산/책임선 전장에 보조 데이터 공급자로 진입하는 아크
- ARC-04 Block 31 slot: `킥오프` — 임시 PM 역할 + 공동 검토선 3인 필수 서명 구조의 첫 실행
- ARC-04 defeat block (Phase0 예상): Block 37 `예산 동결` — ARC-02 Block 17 + ARC-03 Block 25 방어선 패턴을 구조적으로 재사용 필요
- ARC-04 quiet block (Phase0 예상): Phase0 ARC-04 슬롯 참조

### 첫 ARC-04 블록이 재사용할 ARC-03 자산
- Block 21 sponsor 경로 lock → ARC-04 킥오프 자료 상단 틀
- Block 22 세 부서 공동 검토 라인 + 기준/owner 라벨 → ARC-04 예산 라운드 세 부서 분리 서식
- Block 24 호출 접수 기준표 공식 규정 v2 → cross-team 호출권 ARC-04 전체 재사용
- Block 26 파일 이력 + 사전 등록 규정 근거 → ARC-04 예산 동결 defeat 방어 기본 방식
- Block 27 라벨 구조 확장 doctrine → ARC-04 관계 구조 침입 대응
- Block 28 원칙표 v0.3 '사전 방어선 설계' → ARC-04 전체 defeat 선제 차단 doctrine
- Block 29 세 분기 공식 서식 → ARC-04 실행 책임표 기본 틀
- Block 30 공동 검토선 3인 필수 서명 구조 → ARC-04 예산 결재선 + ARC-05 독자 조건표 원형

## 9. Self-Audit Trail

Block 1-30 self-audit (2026-04-09 tr_continue ARC-03 back half, 동기화 재개 세션):

- A1 schema parse: PASS
- A2 block count == 30: PASS
- A3 block_no sequential 1..30: PASS
- A5 capital chain strict equality Block 1-30: PASS (same-turn repair 1건 적용 후 — Block 28 shorthand/괄호 축약 → Block 27 authoritative 풀 표기로 byte-exact 동기화, 의미 변화 0)
- A8 quiet blocks [8, 14, 28] (tension≤4, has_cider=false, is_quiet_block=true): PASS
- A8c Phase0 quiet_blocks lock [8, 14, 28]: PASS
- A8d Phase0 defeat_blocks lock [17, 25]: PASS
- A8e Block 25 defeat schema (no cider, pain_only_exit=false, tension>=8, beat=defeat): PASS
- A10 Block 10 contains 파일럿 (ARC-01 exit): PASS
- A10b Block 20 contains 권역 운영 수정권 (ARC-02 exit): PASS
- A10c Block 30 contains 임시 PM (ARC-03 exit): PASS
- A11 pain_only_exit all false (inc. defeat block 25): PASS
- A12 callback_sources backward-only: PASS
- A13 foreshadow_targets forward-only: PASS
- A15 contamination guard (약물/상태창/전지적 예지 없음): PASS
- A16 POV 윤도혁 stable: PASS
- A17 metadata (_total_blocks=30 / _saved_block_boundary=30 / _next_continuation_boundary=31): PASS
- A20 no stray keys (allowed: schema + block_no + callback_sources + foreshadow_targets + regression_ext + is_quiet_block + is_defeat_block): PASS
- A23 Block 26-27 recovers Block 25 defeat (공로 탈취 → 본문 owner 복원 + 라벨 5줄 확장): PASS
- A24 Block 25 cites Block 21-24 사전 등록 방어선 5개: PASS
- Stage 0 handoff validator (`scripts/stage0_handoff_validator.py --work-id smart_new_hire`): PASS

Overall: ALL PASS.
