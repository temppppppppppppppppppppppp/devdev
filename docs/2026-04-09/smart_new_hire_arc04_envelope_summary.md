# smart_new_hire ARC-04 envelope summary

Date: 2026-04-09
Source: `treatments/smart_new_hire_tr_block_001_draft.json` (saved boundary: Block 40, ARC-04 full)
Authority: read-only extract. The TR file above is the binding truth. This summary is a convenience snapshot, not an authority.
Scope: Block 31-40 only (ARC-04 `예산과 책임선의 전쟁`).
Companions: `docs/2026-04-09/smart_new_hire_arc01_envelope_summary.md` · `arc02_envelope_summary.md` · `arc03_envelope_summary.md`.
Role: Block 31-40 self-audit (§1.1C 네 번째 10-block gate) deliverable.

## 1. Capital Chain (strict equality, Block 31-40)

| Block | Title | capital_delta |
|---|---|---|
| 31 | 킥오프 | + 킥오프 회의록 4문서 (일정표 v1 / owner 재작성표 v1 / 주간 진척도 보고 양식 / 공동 검토선 서명 주기 규정) + 예산 코드 owner 확인 공식 요청 등록 (Block 37 defeat 공격 표면 1차 봉합) |
| 32 | owner 충돌 | + 예산 코드 owner 확인 공식 답변 수신 + owner 분리 구조 회의록 각주 1번 공식 등록 + 집행 개시 신호 '재무 축 사전 서명 + PM 개시 요청서' 두 문서 결합 구조 (2차 봉합) |
| 33 | 공동 검토선 | + 재무-실행 공식 공동 검토선 각주 2번 등록 + 주 2회 정기 검토 + 공동 검토선 서명 주기 규정 v2 (결정/실무 이중 구조, 3차 봉합) |
| 34 | 정답 말고 책임자 (quiet) | + 원칙표 v0.4 'owner 없는 정답은 조직에서 죽는다' 조항 (외부 자산 변화 0, 내부 doctrine 고정) |
| 35 | 실행 책임표 | + 실행 책임표 v0.1 (분기 × 여덟 열 index + status view, 주간 보고 기준 서식 + 재무-실행 정기 검토 기준 서식) |
| 36 | 숫자 전쟁 | + 현업/재무 숫자 병렬 비교표 v0.1 + 분기 1 숫자 차이 구조 진단 사전 등록 (세 원인 병렬: 집행 시점/반영 주기/측정 기준, 4차 봉합) |
| 37 | 예산 동결 (defeat) | + 분기 1 예산 외부 동결 상태 (재무 라인 외부 상위 권한 직접 동결) + 5겹 방어선 + 두 각주 + index 유지 확인 + 동결 해제 조건부 경로 등록 |
| 38 | 우회 기준안 | + 예외 집행 기준표 v0.1 (owner 기록 누적 세 조건) + 우회 승인선 (재무 본부장급 + 오세린 두 서명 결합) + 분기 1 종료 조건 판단 회의 준비 서식 v0.1 |
| 39 | 공동 결재 | + 분기 1 예산 동결 부분 해제 + 우회 승인선 공식 발동 + 공동 결재 행 공식 복원 (재무 본부장급 + 영업관리본부장 두 라인 서명 결합) + joint authority 실체화 첫 순간 |
| 40 | 이름이 빠지지 않는 보고서 | = 임시 PM → 공동권한 실체 이동 + budget pre-check 공식 확정 + 이름이 빠지지 않는 보고서 구조 등록 (여섯 줄 owner 라벨) + ARC-05 승진 심사 진입 입장권 |

Block 31-40 capital chain strict equality: verified `A5 PASS` in Block 1-40 self-audit (2026-04-09, §1.1C gate). Same-turn repair: 0건.

## 2. Cider Ledger (ARC-04)

| Block | has_cider | receipt_type | pain_only_exit | notes |
|---|---|---|---|---|
| 31 | true | visible_token | false | 킥오프 회의록 4문서 공식 등록 + 예산 코드 owner 확인 공식 요청 (Block 37 defeat 공격 표면 1차 봉합) |
| 32 | true | reevaluation | false | owner 분리 구조 회의록 각주 1번 + 집행 개시 신호 두 문서 결합 구조 (2차 봉합) |
| 33 | true | visible_token | false | 재무-실행 공식 공동 검토선 각주 2번 + 결정/실무 공동 검토선 이중 구조 (3차 봉합) |
| 34 | false | null | false | quiet block, 원칙표 v0.4 내부 doctrine 고정, `is_quiet_block: true`, tension_level 3, emotional_beat reflection/4 — Phase0 `quiet_blocks: [34]` lock |
| 35 | true | visible_token | false | 실행 책임표 v0.1 분기 × 여덟 열 index + 주간 보고 기준 서식 + 채널전략팀장 '공동 설계자' 층위 관계 두 번째 전환 |
| 36 | true | proof | false | 현업/재무 숫자 병렬 비교표 v0.1 + 분기 1 숫자 차이 구조 진단 사전 등록 (4차 봉합, Block 37 defeat 직전 마지막 사전 봉합) |
| 37 | **false** | **null** | **false** | **defeat block**, `is_defeat_block: true`, tension_level 9, emotional_beat defeat/9 — Phase0 `defeat_blocks: [37]` lock. 재무 라인 외부 상위 권한의 직접 동결 조치, 공격 자체에 대응하지 않고 5겹 방어선 유지 사실을 회수 경로 근거로 Block 38-39에 인계 |
| 38 | true | reevaluation | false | 예외 집행 기준표 v0.1 + 우회 승인선 + 분기 1 종료 조건 판단 회의 준비 서식 v0.1 (defeat 회수 시작) |
| 39 | true | proof | false | 우회 승인선 공식 발동 + 공동 결재 행 공식 복원 + joint authority 실체화 첫 순간 (defeat 회수 완결, 단 최종 exit는 Block 40) |
| 40 | true | next_gate_opening | false | 임시 PM → 공동권한 실체 + budget pre-check 공식 확정 + 이름이 빠지지 않는 보고서 구조 + ARC-05 진입 입장권 (ARC-04 Phase0 exit 일치) |

Pain_only_exit 전 블록 `false` — contamination guard 준수.

## 3. Defeat Block Audit (Block 37)

Phase0 lock: `ARC-04 defeat_blocks: [37]`.

### Defeat 발생 구조 (세 번째 변주)
- 공격 축: 재무 라인 외부 상위 권한 (재무 본부장급 위쪽, 실명 미정) — ARC-04 구조 밖의 외부 권한
- 공격 무기: '분기 1 예산 코드 선제 동결' — 구조적 근거 없이 권한 자체로 집행을 멈추는 형태
- 공격 목적: 분기 1 종료 조건 판단 회의(10일 뒤)까지 집행을 멈춰 '분기 1 실패 책임자' 라벨을 임시 PM에 붙이는 것
- 결과: 집행 개시 신호 구조와 무관하게 예산 코드 자체가 잠긴 상태, line 종료 아님

### Defeat 5겹 방어선 (Block 31-36 사전 등록)
Block 37 defeat가 line 종료가 아닌 구조 유지 가능 동결로 제한된 이유 — 모두 Block 31-36에서 사전 등록된 자산:

1. **Block 31 예산 코드 owner 확인 공식 요청** — 예산 코드 owner가 재무 본부장급 라인에 있다는 사실이 공식 답변으로 등록되어 있어 외부 동결 조치의 구조적 근거가 이미 부재함
2. **Block 32 owner 분리 각주 1번 + 집행 개시 신호 두 문서 결합 구조** — 집행 개시 신호가 '재무 축 사전 서명 + PM 개시 요청서' 두 문서 결합으로 발동된다는 구조가 회의록 각주로 박혀 있어, 외부 동결 조치도 이 구조를 우회할 수 없음
3. **Block 33 재무-실행 공식 공동 검토선 각주 2번 + 주 2회 정기 검토** — 재무 라인 안쪽에 실무 공동 검토선이 이미 등록되어 있어 Block 38 예외 집행 기준표의 설계 공간이 구조 안쪽에 존재
4. **Block 35 실행 책임표 v0.1 index + 분기별 owner 로그** — 어떤 안건이 어디서 멈췄는지 5초 안에 식별 가능한 상태, Block 38 예외 집행 기준표 '70% 진척' 조건의 근거
5. **Block 36 현업/재무 숫자 병렬 비교표 v0.1 + 분기 1 숫자 차이 구조 진단 사전 등록** — '집행 관리 실패' 프레임이 성립할 수 없도록 세 원인(집행 시점/반영 주기/측정 기준) 병렬 명시로 봉합, Block 37 공격이 외부 권한 직접 동결 형태로만 들어올 수 있게 공격 경로를 좁힘

### Defeat 회수 경로 (Block 37 → Block 38-39)
- **Block 37 (defeat 발생)**: 즉시 반박하지 않고 5겹 방어선 유지 확인 + 재무 본부장급에게 구조적 해석 메모 전달 + 한성우/채널전략팀장에게 상황 공유. 공격 자체에 대응하지 않고 '구조 유지 사실'을 회수 경로 근거로 다음 블록에 인계. (Block 25 defeat 회수 방식의 ARC-04 버전 재사용)
- **Block 38 (회수 시작)**: 예외 집행 기준표 v0.1 설계. 기준을 '정답' 기준이 아닌 'owner 기록 누적 세 조건'(70% 진척 + 집행 개시 신호 두 문서 결합 사전 완료 + 정기 검토 2주 이상 기록)으로 좁힘. 우회 승인선 = 재무 본부장급 + 오세린 두 서명 결합으로 별도 등록(기존 공동 검토선 3인 구조 건드리지 않음). Block 34 원칙표 v0.4 'owner 없는 정답은 조직에서 죽는다' 조항이 기준표 설계 근거
- **Block 39 (회수 완결)**: 우회 승인선 첫 발동과 동시에 공동 결재 행 구조를 설계해 '발동 메커니즘 + 결재 메커니즘' 역할 분리 이중 구조를 박음. 영업관리본부장을 공동 결재 행 첫 서명자로 참여시켜 '분기 1은 재무 라인이 구해줬다' 프레임 차단. joint authority 실체화 첫 순간. Phase0 ARC-04 exit_function 구조적 기초 완성
- **Block 40 (ARC-04 exit)**: 이름이 빠지지 않는 보고서 구조(여섯 줄 owner 라벨)로 보고 서식 자체에 owner를 박아 단독 영웅화와 자발적 양보 두 위험을 동시에 차단. budget pre-check 공식 확정. 임시 PM → 공동권한 실체 이동. Phase0 ARC-04 capital_target 정확 달성

### Self-audit 증거
- `A8d Phase0 defeat_blocks lock [17, 25, 37]: PASS`
- `A8e Block 37 defeat schema (no cider, pain_only_exit=false, tension>=8, beat=defeat): PASS`
- `A8f defeat 3-variation (Block 17 산식 공격 / Block 25 라벨 이동 공격 / Block 37 외부 권한 직접 동결 공격): PASS`
- `A11 pain_only_exit all false (inc. defeat block 37): PASS`
- `A23a Block 38 starts Block 37 recovery (예외 집행 기준표): PASS`
- `A23b Block 39 completes defeat recovery (공동 결재 복원): PASS`
- `A24 Block 37 cites 5겹 방어선: PASS`

### Defeat 3-변주 완결
ARC-02 Block 17 / ARC-03 Block 25 / ARC-04 Block 37 세 defeat가 모두 다른 공격 형태를 가지면서 동일한 회수 doctrine(반박 대신 규정 재확인 + 구조 안쪽에서 예외 기준표 + 역할 분리 이중 구조)으로 회수됨. smart_new_hire의 'defeat 회수 3단 패턴'이 Block 37-40 회수 구간에서 doctrine으로 고정.

## 4. Quiet Block Audit (Block 34)

Phase0 lock: `ARC-04 quiet_blocks: [34]`.

- `is_quiet_block: true`, `has_cider: false`, `tension_level: 3`, `emotional_beat: reflection/4`
- 위치: 세광리테일 본사 11층 채널운영팀 야근 자리 (혼자 정리 시간)
- doctrine: 반복된 패턴은 외부에 발신하지 말고 내부 doctrine 파일에 한 줄씩 쌓는다. owner 없는 정답은 조직에서 죽는다.
- 외부 자산 변화: 0 (내부 판단 기준만 1단계 추가)
- 내부 자산 추가: 원칙표 v0.4 'owner 없는 정답은 조직에서 죽는다' 조항 + 반복 문제 패턴표 v0.1 'owner 부재 → 정답 무력화' 항목
- Block 8 · 14 · 28 quiet 블록과의 parity: 모두 tension≤4, has_cider=false, internal doctrine only, 공식 권한 변화 없음, 내부 자산만 축적

## 5. Callback / Foreshadow Matrix (ARC-04)

| Block | callback_sources | foreshadow_targets |
|---|---|---|
| 31 | 24, 28, 29, 30 | 32, 33, 35, 37, 39 |
| 32 | 25, 27, 30, 31 | 33, 35, 37, 38 |
| 33 | 11, 18, 30, 32 | 35, 37, 39, 40 |
| 34 | 8, 13, 14, 17, 25, 28, 33 | 35, 37, 47, 49 |
| 35 | 12, 22, 27, 29, 30, 34 | 36, 37, 38, 40, 47 |
| 36 | 18, 22, 26, 33, 35 | 37, 38, 39, 40 |
| 37 | 17, 25, 28, 31, 32, 33, 34, 35, 36 | 38, 39, 40 |
| 38 | 15, 28, 32, 34, 35, 37 | 39, 40, 47 |
| 39 | 18, 30, 32, 33, 37, 38 | 40, 47 |
| 40 | 3, 10, 20, 25, 27, 30, 34, 35, 37, 38, 39 | 47 |

Invariants: callback_sources backward-only (< block_no), foreshadow_targets forward-only (> block_no) — `A12/A13 PASS`.

Cross-ARC anchor 회수 상태 (Block 31-40 → Block 1-30 자산 회수):
- B3 첫 자리 공식 확정 → B40 (ARC-04 출구 공동권한 실체 누적 확정)
- B8 원칙표 v0.1 → B34 (v0.4 상속)
- B10 ARC-01 exit / B20 ARC-02 exit / B30 ARC-03 exit → B40 (4단계 exit 누적 구조 완결)
- B11 오세린 재무 공동 검토 라인 → B33 (재무-실행 공식 공동 검토선)
- B12 공통 체크리스트 → B35 (실행 책임표 v0.1)
- B13 C 점장 'owner 없었다' 발언 → B34 (원칙표 v0.4 직접 근거)
- B14 v0.2 → B34 (v0.4 상속)
- B15 조건문 세 줄 → B38 (예외 집행 기준표 세 조건)
- B17 defeat 회수 패턴 → B37 (3번째 defeat 변주)
- B18 '같은 표' 방식 → B36 (현업/재무 병렬 비교), B39 (공동 결재 행)
- B22 기준/owner 세 칸 분리 → B36 (병렬 비교 세 원인)
- B25 defeat 회수 방식 → B37 (ARC-04 버전 재사용), B40 ('이름 없는 공' → '이름이 빠지지 않는 보고서' 구조 반전)
- B26 파일 이력 근거 → B36 (차이 구조 사전 등록)
- B27 5줄 라벨 → B40 (여섯 줄 owner 라벨 확장)
- B28 원칙표 v0.3 '사전 방어선 설계' → B31-36 (실체화 첫 사용), B37 (실제 defeat 앞에서 작동), B38
- B29 세 분기 공식 서식 → B31 (일정표 v1), B35 (분기 × 여덟 열)
- B30 공동 검토선 3인 필수 서명 → B31-33 (ARC-04 킥오프 구조), B39 (joint authority 실체화), B40 (보고서 구조 핵심)

Forward 전개 (ARC-05 이후로 심어진 foreshadow):
- → B47 '독자 조건표' (ARC-05): B34 원칙표 v0.4 + B35 실행 책임표 + B38 예외 집행 기준표 + B39 역할 분리 이중 구조 + B40 이름이 빠지지 않는 보고서 구조 전부 합류
- → B49 '기준표' (ARC-05): B34 반복 문제 패턴표 v0.1 '내부 doctrine 4단계 라인' 진화
- ARC-06 혁신 PMO 축 / ARC-07 파이널에서 smart_new_hire 버전 '세 축 결합' 구조로 재사용 예약

## 6. POV / Location / Time Coverage (ARC-04)

- POV: 윤도혁 (10/10, Phase0 POV lock 준수)
- Location type: 본사 (10/10) — 세광리테일 본사 11층 채널운영팀 + 15층 영업관리본부장실 / 재무 본부장급 사무실 + 재무 파트너 좌석
- In-story time: 2026년 10월 첫째 주 월요일 (B31) ~ 2026년 12월 셋째 주 토요일 (B40) = 약 11주
- Phase0 ARC-04 time_window (`2026년 10월~2027년 1월`) 내부

## 7. Doctrine Line (Block 31-40 execution_doctrine 요약)

31. 주장하지 말고 킥오프 시작 10분 안에 일정표 + owner 재작성표 + 보고 양식 + 서명 주기 네 개 문서를 종이로 먼저 올리고, 예상되는 defeat의 공격 표면을 공식 안건으로 먼저 등록한다.
32. owner 충돌 앞에서 owner를 당겨오지 말고, 공식 각주로 분리 구조와 집행 개시 신호 규칙을 명시해 권한 범위를 건드리지 않고 공격 표면만 봉합한다.
33. 공동 검토선을 확장하려 하지 말고, 그 안쪽에 범위가 다른 실무선을 별도 등록해 결정선의 원형을 보존하면서 실무 공백만 봉합한다.
34. 반복된 패턴은 외부에 발신하지 말고 내부 doctrine 파일에 한 줄씩 쌓는다. owner 없는 정답은 조직에서 죽는다.
35. 외부 제안을 내부 doctrine에 맞춰 'owner 박는 index 서식'으로 재설계해 기존 문서의 authoritative 지위를 유지하면서 파편화만 봉합한다.
36. 숫자가 다를 때 통합하지 말고 병렬 배치하고, 차이 칸에 세 원인을 명시해 '차이는 오류가 아니라 구조'임을 사전 등록한다.
37. 외부 권한 범위 밖에서 들어온 공격 앞에서 즉시 반박하지 말고, 사전 등록된 방어선 구조가 유지되고 있다는 사실 자체를 다음 블록의 회수 근거로 인계한다.
38. 외부 권한 조치를 무력화하지 말고, 구조 안쪽에서 'owner 기록 누적' 기준표로 예외 경로를 설계해 동결 범위 밖 집행을 확보한다.
39. 우회 승인선 발동과 동시에 공동 결재 행 구조를 설계해 '발동/결재' 역할 분리 이중 구조를 박고, 최상위 후원자를 공동 결재 행 서명자로 참여시켜 양쪽 라인 동시 통과점 인정을 구조화한다.
40. 보고서를 'owner 박는 서식'으로 설계해 전체 owner 라벨이 구조적으로 박히게 만들고, 한 명이라도 빠지면 서식 자체가 성립하지 않게 한다. 단독 영웅화와 자발적 양보 두 위험을 서식 구조 자체로 차단한다.

## 8. ARC-04 Exit State → ARC-05 Entry Gate

- 최종 자원 상태(`Block 40 capital_after`): 임시 PM 역할 → 공동권한 실체 (재무 본부장급 + 영업관리본부장 공동 결재 행 + 공동 검토선 3인 필수 서명 + 재무-실행 공식 공동 검토선 + 우회 승인선 이중 구조가 모두 한 서식에 결합) + budget pre-check 공식 확정 + 이름이 빠지지 않는 보고서 구조 등록 (여섯 줄 owner 라벨) + ARC-05 승진 심사 진입 입장권
- ARC-04 exit 조건(Phase0 locked `capital_target`): 임시 PM → 공동권한 + budget pre-check ✅
- ARC-04 exit_function(Phase0 locked): 현업 line과 재무 line이 동시에 도혁을 통과점으로 인정한다 ✅ (Block 39 joint authority 실체화 첫 순간 → Block 40 이름이 빠지지 않는 보고서 서식 안쪽에 구조적으로 박힘)
- ARC-05 entry_function(Phase0 locked): ownerliness 증명 (Phase0 ARC-05 참조)
- ARC-05 Block 41 slot: Phase0 ARC-05 block_slots 참조

### 첫 ARC-05 블록이 재사용할 ARC-04 자산
- Block 31 킥오프 회의록 4문서 구조 → ARC-05 승진 심사 초기 자료 서식
- Block 32 owner 분리 각주 방식 → ARC-05 심사 기준과 심사 권한 분리 구조
- Block 33 결정/실무 공동 검토선 이중 구조 → ARC-05 심사위원 vs 심사 대상 구조
- Block 34 원칙표 v0.4 → ARC-05 전체 doctrine 기초
- Block 35 실행 책임표 v0.1 → ARC-05 심사 자료 기본 서식
- Block 38 예외 집행 기준표 세 조건 → ARC-05 심사 기준표 원형
- Block 39 우회 승인선 + 공동 결재 행 역할 분리 → ARC-05 독자 조건표 설계 원형
- Block 40 이름이 빠지지 않는 보고서 구조 → ARC-05 승진 심사 자료 서식

## 9. Self-Audit Trail

Block 1-40 self-audit (2026-04-09 tr_continue ARC-04 full, envelope 36-40 + §1.1C 10-block gate):

- A1 schema parse: PASS
- A2 block count == 40: PASS
- A3 block_no sequential 1..40: PASS
- A5 capital chain strict equality Block 1-40: PASS
- A8c Phase0 quiet_blocks lock [8, 14, 28, 34]: PASS
- A8 quiet 8 / 14 / 28 / 34 schema (tension≤4, has_cider=false): PASS
- A8d Phase0 defeat_blocks lock [17, 25, 37]: PASS
- A8e defeat 17 / 25 / 37 schema (no cider, pain_only_exit=false, tension≥8, beat=defeat): PASS
- A8f defeat 3-variation (Block 17 산식 공격 / Block 25 라벨 이동 공격 / Block 37 외부 권한 직접 동결 공격): PASS
- A8g Phase0 ARC-04 quiet_blocks [34] match: PASS
- A8h Phase0 ARC-04 defeat_blocks [37] match: PASS
- A10 Block 10 contains 파일럿 (ARC-01 exit): PASS
- A10b Block 20 contains 권역 운영 수정권 (ARC-02 exit): PASS
- A10c Block 30 contains 임시 PM (ARC-03 exit): PASS
- A10d Block 40 contains 공동권한 + budget pre-check (ARC-04 exit, Phase0 capital_target 정확 달성): PASS
- A11 pain_only_exit all false (inc. defeat blocks 17/25/37): PASS
- A12 callback_sources backward-only: PASS
- A13 foreshadow_targets forward-only: PASS
- A15 contamination guard (약물/상태창/전지적 예지 없음): PASS
- A16 POV 윤도혁 stable (40/40): PASS
- A17 metadata (_total_blocks=40 / _saved_block_boundary=40 / _next_continuation_boundary=41): PASS
- A20 no stray keys: PASS
- A23a Block 38 starts Block 37 recovery (예외 집행 기준표): PASS
- A23b Block 39 completes defeat recovery (공동 결재 복원): PASS
- A24 Block 37 cites 5겹 방어선: PASS
- A25 Block 36-40 in ARC-04 time window: PASS
- Stage 0 handoff validator (`scripts/stage0_handoff_validator.py --work-id smart_new_hire`): PASS

Overall: ALL PASS. §1.1C 네 번째 10-block self-audit gate (Block 31-40 window) 통과.
