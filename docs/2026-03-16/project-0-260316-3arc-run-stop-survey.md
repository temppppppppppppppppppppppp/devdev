# Project 0_260316 3-Arc Run Stop Survey

Date: 2026-03-16
Status: final
Scope: `projects/0_260316` 3아크 의도 런 중단 지점 전수 조사
Confidence: 96%
Audit: draft -> pass1 -> pass2 -> pass3 complete

Commit State:
- Baseline Commit: `5a0177666e6877070d726d983d3c3e1d03e812d2`
- Baseline Dirty Summary: `dirty: 1 untracked; hotspot: projects/0_260316/0_temp.txt`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

Evidence Artifacts:
- `projects/0_260316/0_temp.txt`
- `projects/0_260316/logs/session_20260316_110204.log`
- `projects/0_260316/logs/session/ui_events.jsonl`
- `projects/0_260316/logs/session/state_changes.jsonl`
- `projects/0_260316/logs/episode_production.jsonl`
- `projects/0_260316/logs/runtime_audit_summary.json`
- `projects/0_260316/logs/soft_failures.jsonl`
- `projects/0_260316/drafts/`
- `projects/0_260316/plans/arcs/`
- `projects/0_260316/plans/blueprints/`
- `projects/0_260316/project_data.db`
- `crash_dump.log` (timestamp cross-check only; runtime-cause authority 아님)

Side-Effect Coverage:
- file writes and runtime artifacts: covered
- DB persistence and sink alignment: covered
- JSONL/log/audit sinks: covered
- console and operator-visible output: covered
- rollback/recovery/retry paths: covered
- cache/global state mutation traces: covered
- config/env/bootstrap mutation: not applicable in this survey scope

## Intent

사용자 질문은 두 가지였다.

1. `projects/0_260316`가 실제로 3아크 의도 런이었는가
2. 맞다면 어디까지 진행됐고 어디서 멈췄는가

이번 조사는 구현이나 재실행이 아니라, 현재 프로젝트 폴더와 로그/DB/실물 산출물을 교차해 중단 지점을 고정하는 survey-only 작업으로 제한했다.

## Pass 1 Inventory

### 1.1 파일/산출물 인벤토리

- `stage0_output/style_guide.json` 존재
- `plans/arcs/arc_001.txt` ~ `arc_003.txt` 존재
- `plans/blueprints/blueprint_0001.txt` ~ `blueprint_0011.txt` 존재
- `drafts/ep_0001.txt` ~ `ep_0006.txt` 존재
- `logs/artifacts/stage2/arc_001` ~ `arc_003` 존재
- `logs/artifacts/stage3/ep_0001` ~ `ep_0011` 존재
- `logs/artifacts/stage4/ep_0001` ~ `ep_0006` 존재
- `logs/artifacts/stage4/ep_0007`는 존재하지 않음
- `project_data.db` 존재, `PRAGMA integrity_check = ok`

### 1.2 DB 인벤토리

조사 시점 최종 DB 기준:

- `blueprints`: 11 rows, `MAX(ep_num)=11`
- `manuscripts`: 6 rows, `MAX(ep_num)=6`
- `episode_meta`: 6 rows, `MAX(ep_num)=6`
- `stage_attempts WHERE stage=4`: 11 rows, `MAX(ep_num)=6`
- `director_selections WHERE stage=4`: 11 rows, `MAX(ep_num)=6`
- `state_logs`: 6 rows

의미:

- Stage 3은 11화까지 확정 저장됨
- Stage 4는 6화까지만 확정 저장됨
- 7화에 대한 Stage 4 확정 행은 DB에 없음

### 1.3 로그/세션 인벤토리

- 세션 평문 로그: `logs/session_20260316_110204.log`
- 구조화 UI 로그: `logs/session/ui_events.jsonl`
- 구조화 의사결정 로그: `logs/session/decisions.jsonl`
- 구조화 상태 변화 로그: `logs/session/state_changes.jsonl`
- 화별 생산 로그: `logs/episode_production.jsonl`
- 런타임 요약: `logs/runtime_audit_summary.json`
- soft failure sink: `logs/soft_failures.jsonl`

## Pass 2 Semantic Classification

### 2.1 이 런의 실제 의도

`0_temp.txt`와 `ui_events.jsonl` 기준으로 이번 실행은 일반 Stage 4 단발이 아니라 `Frontier Lag` 모드였다.

확인된 흐름:

- Arc 2까지 원고 6화 완성
- 이후 `FrontierLag`로 Arc 3 설계 진행
- Stage 3 목표를 `target <= ep 11`까지 끌어올림
- Stage 4 목표를 `target <= ep 10`으로 재동기화함

즉 "3아크 런"의 의미는 아래와 같이 분리된다.

- Stage 2 frontier: Arc 3까지
- Stage 3 frontier: ep 11까지
- Stage 4 frontier target: ep 10까지

따라서 3아크 의도 자체는 맞다. 다만 그 의미가 "12화 원고 완성"은 아니고, Frontier Lag 규칙에 맞춰 설계/블루프린트/원고가 서로 다른 lag를 유지하는 구조였다.

### 2.2 실제로 확정된 최종 지점

확정 저장 기준 최종 상태:

- Arc 설계: 3개 완료
- Blueprint: 11화 완료
- Manuscript: 6화 완료

마지막 확정 Stage 4 성공 증거:

- `episode_production.jsonl` 마지막 화수는 6화
- `state_changes.jsonl` 마지막 화수도 6화
- `drafts/ep_0006.txt`가 마지막 원고 파일
- `logs/artifacts/stage4/ep_0006/.../final_manuscript__B.txt` 존재

7화는 아래까지만 진행됐다.

- Stage 4 resume
- `제7화 집필 시작`
- `Round 1/10`
- `Chief Writer 앙상블 생성 중`
- context cache 생성
- 병렬 LLM 호출 시작

그 이후:

- `director_selections` 없음
- `stage_attempts` 없음
- `episode_meta` 없음
- `manuscripts` 없음
- `logs/artifacts/stage4/ep_0007/` 디렉터리 없음

즉 7화는 "착수"만 있었고 "선택/검증/저장" 단계에 전혀 도달하지 못했다.

### 2.3 중단 유형 분류

이번 중단은 작업 내부 REJECT/FAIL이 아니라, managed failure path 바깥의 abrupt interruption으로 분류하는 것이 가장 타당하다.

근거:

- 세션 로그 말단이 예외 처리나 종료 메시지 없이 HTTP 응답 대기 중간에서 끝남
- `0_temp.txt`도 7화 앙상블 생성 spinner 중 콘솔 프롬프트로 복귀한 흔적을 보임
- `soft_failures.jsonl`에는 7화 중단을 설명할 신규 치명 오류가 없음
- `runtime_audit_summary.json`의 마지막 authoritative event는 `2026-03-16 12:55:35`의 `blueprint_success`

가장 가능성 높은 해석:

- Python이 앱 내부 예외를 정리하고 종료한 것이 아니라
- 외부 종료, 콘솔 종료, 프로세스 강제 종료, 호스트 측 인터럽트 중 하나로 세션이 끊겼다

현재 워크스페이스 증거만으로는 그 이상을 특정할 수 없다.

## Artifact Truth

### 3.1 원고 파일

- `drafts/ep_0001.txt` ~ `ep_0006.txt` 모두 UTF-8로 정상 decode됨
- 각 화 본문은 실재 파일과 DB row 둘 다 존재
- 파일판과 DB판 문자열이 1:1 동일하지는 않지만, 이는 손상보다 저장 형식 차이로 해석하는 것이 맞다

구체적으로:

- 파일판은 `# 제목` 헤더를 포함
- DB판은 `title` 컬럼과 `content` 컬럼으로 분리 저장
- 예시로 6화는 파일판과 DB판의 본문 tail이 일치하며, 차이는 제목 헤더 분리에 수렴한다

따라서 manuscript file/DB mismatch는 corruption 근거가 아니라 serialization shape 차이로 분류한다.

### 3.2 블루프린트 파일

- `plans/blueprints/blueprint_0001.txt` ~ `blueprint_0011.txt` 모두 UTF-8로 정상 decode됨
- DB의 `blueprints.data`는 JSON source
- 파일판은 사람 읽는 formatted txt render

따라서 blueprint file/DB mismatch 역시 expected shape difference다. 손상 증거가 아니다.

### 3.3 Stage 4 artifact frontier

Stage 4 artifact는 6화까지만 존재한다.

- `logs/artifacts/stage4/ep_0001` ~ `ep_0006`: 존재
- `logs/artifacts/stage4/ep_0007`: 없음

이 점은 "7화 저장 직전 실패"보다 더 이른 단계, 즉 candidate materialization 이전 혹은 초입 중단을 시사한다.

## Metadata Truth

### 4.1 authoritative sink 정합성

권위 sink 간 결론은 서로 맞는다.

- `episode_production.jsonl`: 마지막 확정 화 = 6
- `state_changes.jsonl`: 마지막 화 = 6
- `manuscripts`: 마지막 화 = 6
- `drafts/`: 마지막 파일 = 6
- `blueprints`: 마지막 화 = 11
- `plans/blueprints/`: 마지막 파일 = 11

정리하면:

- Arc/Blueprint 쪽은 Arc 3 기준까지 잘 밀렸고
- Manuscript만 ep 7 진입 초반에서 끊겼다

### 4.2 non-blocking warning

반복적으로 남은 soft failure는 아래 하나다.

- `failure_analyzer.sink_alignment_final_authority_contract`
- 예외: `AttributeError: 'types.SimpleNamespace' object has no attribute 'get_stage4_final_authority_rows'`

하지만 이 경고는 5화, 6화, 11화 blueprint 직후에도 있었고 실제 진행은 계속되었다. 즉 이번 중단의 직접 원인으로 보지 않는다.

### 4.3 crash dump 분류

루트 `crash_dump.log`는 존재하지만 이번 런의 근거로 사용하면 안 된다.

- 마지막 수정 시각이 `2026-03-16 10:56:09`
- 내용은 `pytest` 종료 시점 stack overflow dump
- 이번 프로젝트 세션의 12:55~12:56 구간보다 앞선 별도 사건이다

따라서 이번 7화 중단과는 무관한 오래된 crash evidence로 분류한다.

## Narrative Truth

실물 본문 기준으로 6화 종료와 7화 설계 연결은 자연스럽다.

6화 원고 요점:

- WTI 6월물 15억 원, 3배 레버리지 매수 포지션 진입
- 박성호는 공포와 경외감 속에서 체결 확인서를 듦
- 한시우는 결과를 이미 아는 듯 창밖을 바라보는 장면으로 닫힘

7화 blueprint 요점:

- 거래 직후 박성호의 극심한 불안과 한시우의 평정심이 이어짐
- 강남 테헤란로 사무실로 이동
- 시장의 소폭 하락에 박성호가 흔들리지만 한시우는 동요 없음
- 이후 형의 수하들이 강철 문을 부수려는 물리적 위협으로 긴장 축이 전환됨

즉 6화 cliffhanger에서 7화 설계로 넘어가는 narrative bridge는 정상이다.

이번 중단은 narrative contradiction이 아니라 runtime interruption 문제다.

## Side-Effect Sweep

### 6.1 파일 쓰기

확정 파일 쓰기는 아래까지 확인된다.

- `drafts/ep_0006.txt`
- `plans/blueprints/blueprint_0011.txt`
- Stage 2/3/4 artifact trees for confirmed episodes/arcs

7화 Stage 4의 파일 쓰기는 확인되지 않는다.

### 6.2 DB 쓰기

확정 DB writes는 아래까지 확인된다.

- blueprint 11
- manuscript 6
- episode_meta 6
- state_logs 6
- stage4 attempt rows up to episode 6

7화 Stage 4 관련 DB commit은 없다.

### 6.3 로그/감사 sink

로그는 7화 초입까지 기록되다가 세션 로그 말단에서 갑자기 끊긴다.

- UI logs: 7화 시작까지 있음
- session log: chief writer ensemble HTTP 요청 진행 중단
- runtime audit summary: 7화 Stage 4 결과 미반영

### 6.4 rollback/recovery/retry

이번 중단 시점에는 아래 흔적이 없다.

- rollback 실행 없음
- recovery 루틴 실행 없음
- retry round 시작 없음
- compensation/cleanup 로그 없음

즉 시스템이 "실패를 인식하고 복구한 뒤 멈춘 것"이 아니라, 복구 루틴 진입 전에 런이 끊긴 상태다.

### 6.5 cache/global state

7화 직전 아래 state mutation은 확인된다.

- manuscript context cache 생성
- `story_context` 조립
- vec retrieval 수행
- ChiefWriter 병렬 호출 3개 시작

하지만 이들은 모두 persistence commit 이전의 in-flight state다.

### 6.6 조사 과정에서 발생한 파일 레벨 변화

초기 인벤토리 시점에는 `project_data.db-wal`과 `project_data.db-shm`가 존재했다. SQLite 조회 이후 현재는 main DB만 남고 WAL/SHM은 사라졌다.

현재 확인 결과:

- `PRAGMA integrity_check = ok`
- logical row counts 변화 없음

따라서 이 변화는 조사 중 SQLite checkpoint/merge 성격의 파일 레벨 변화로 기록하고, 내용 손상 증거로 보지 않는다.

## Conclusion

결론은 아래 다섯 줄로 요약된다.

1. 사용자 판단대로 이번 프로젝트는 실제로 3아크 의도 런이었다.
2. 다만 Frontier Lag 규칙상 의도된 종착점은 `Arc 3 설계 + Blueprint ep11 + Manuscript ep10 target`이지, 즉시 12화 원고 완성은 아니었다.
3. 실제 확정 상태는 `Arc 3 완료 / Blueprint 11화 완료 / Manuscript 6화 완료`다.
4. 중단 지점은 `제7화 Round 1 Chief Writer 앙상블 생성` 초입이며, 선택/저장 단계에는 도달하지 못했다.
5. 현재 증거로 가장 타당한 분류는 in-app validation failure가 아니라 managed failure path 바깥의 abrupt interruption이다.

## Recovery Posture

현재 상태는 복구 가능하다.

- wipe나 rewind를 할 근거는 없다
- manuscript frontier는 6화에서 멈춰 있으므로, 재개 시 7화부터 다시 잡히는 것이 자연스럽다
- Stage 2/3 산출물은 현재 증거상 유효하다
- 우선순위는 "왜 외부 종료가 났는지 재현/보강"이지 "프로젝트 산출물 정리"가 아니다

이번 턴 범위에서는 survey-only로 종료한다. 실행 SSOT나 패치는 만들지 않았다.

## Non-Goals

- 원인 코드를 수정하지 않음
- 런을 재실행하지 않음
- Stage 2/3/4 로직 리팩터링하지 않음
- 작품 품질 감리로 범위를 확장하지 않음
