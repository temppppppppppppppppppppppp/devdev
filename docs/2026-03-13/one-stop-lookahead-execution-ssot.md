# One-Stop Lookahead 변형 실행 SSOT

작성일: 2026-03-13  
대상 코드: `main_a.py`, `modules/core/stage3_orchestrator.py`, `modules/core/stage4_orchestrator.py`

## Summary

- 목표는 기존 `6번 One-Stop`을 대체하는 것이 아니라, `7번 Lookahead 변형`을 새로 추가하는 것이다.
- 현재 `6번`은 Arc N 설계 직후 `Stage 3 target_ep=arc_ep_end`, `Stage 4 target_ep=arc_ep_end`를 그대로 수행한다.
- 이 구조는 Arc N의 마지막 화가 Arc N+1 정보를 전혀 보지 못한 채 blueprint/원고로 확정되는 약점을 가진다.
- 새 `7번`은 `Arc N의 마지막 화 blueprint/원고를 유예`하고, `Arc N+1 설계 완료 후` 그 정보를 들고 Arc N의 마지막 화를 닫는 변형이다.
- 구현 원칙은 `Stage 3/4 내부 엔진 변경 최소화`, `main_a.py 오케스트레이션 중심`, `resume는 기존 DB/파일 상태로 추론`이다.

## Baseline Facts

- 메인 메뉴 `6`은 현재 `🔄 One-Stop: Arc-by-Arc 자동 파이프라인`이다.
  - `main_a.py:2143`
  - `main_a.py:2173-2174`
- 현재 `_one_stop_pipeline()`은 Arc 단위로 아래 순서를 쓴다.
  - Arc N 설계
  - `Stage 3 target_ep=arc_ep_end`
  - `Stage 4 target_ep=arc_ep_end`
  - 다음 Arc로 이동
  - `main_a.py:3466`
  - `main_a.py:3598`
  - `main_a.py:3636`
- `Stage 3`는 `target_ep`까지 blueprint를 채우며, 기존 blueprint는 스킵한다.
  - `modules/core/stage3_orchestrator.py:478`
  - `modules/core/stage3_orchestrator.py:575-586`
  - `modules/core/stage3_orchestrator.py:707`
- `Stage 4`는 `get_latest_episode_number()`가 가리키는 다음 미작성 화부터 `target_ep`까지 쓴다.
  - `modules/core/project_manager.py:640`
  - `modules/core/db_manager.py:2250`
  - `modules/core/stage4_orchestrator.py:582-617`
- 따라서 wrapper에서 `target_ep`만 잘라 주면, `마지막 화 유예`는 Stage 3/4 내부 대공사 없이 구현 가능하다.

## Problem Statement

- 기존 `6번`은 Arc를 “설계부터 마지막 원고까지” 한 번에 밀어 Arc 경계의 미래 정보를 잃는다.
- 특히 손해가 큰 지점은 아래다.
  - Arc 마지막 화의 ending hook
  - 다음 Arc 전환부의 복선/회수
  - 투자물/장기 서사에서 다음 block 전략을 미리 반영해야 하는 closing scene
- 사용자가 원하는 것은 “Arc body는 지금 진행하되, Arc tail 1화는 다음 Arc 설계 후 닫는” 변형이다.

## Desired Mode

- 새 메뉴 `7`을 추가한다.
- 가칭:
  - `🧭 One-Stop+1: Arc Tail Holdback`
  - 또는 `🧭 One-Stop: Lookahead Tail-Holdback`
- 동작 원칙:
  - Arc N body (`ep_start ~ ep_end-1`)는 현재 Arc 설계 직후 진행
  - Arc N tail (`ep_end`)은 유예
  - Arc N+1 설계가 완료되면 Arc N tail의 Stage 3/4를 진행
  - 마지막 Arc는 예외적으로 full close 허용

## Orchestration Design

### Rule 1. `6번`은 유지한다

- 기존 `6`은 빠른 검증/오염 감지용으로 유지한다.
- 새 전략은 `7`로 분기한다.
- 이유:
  - 기존 사용자 습관 보존
  - 빠른 smoke path 유지
  - 새 모드의 resume semantics가 다르므로 의미를 분리해야 한다

### Rule 2. Arc body / tail을 wrapper가 잘라서 Stage 3/4에 전달한다

- 새 helper 개념:
  - `body_end = arc_ep_end - 1`
  - `tail_ep = arc_ep_end`
- Stage 3:
  - body는 `target_ep=body_end`
  - tail은 `target_ep=tail_ep`
- Stage 4:
  - body는 `target_ep=body_end`
  - tail은 `target_ep=tail_ep`
- Stage 3/4 내부 엔진은 바꾸지 않는다. 기존 `target_ep` semantics를 그대로 활용한다.

### Rule 3. 다음 Arc 설계는 현재 Arc tail close보다 먼저 온다

- Arc N 처리 순서:
  - Arc N 설계 보장
  - Arc N body Stage 3
  - Arc N body Stage 4
  - Arc N+1 설계 보장
  - Arc N tail Stage 3
  - Arc N tail Stage 4
- 이렇게 하면 Arc N tail은 Arc N+1 tactical context가 설계된 뒤 닫힌다.

### Rule 4. 마지막 Arc는 예외 처리한다

- 마지막 Arc는 `다음 Arc`가 없으므로 holdback 이득이 없다.
- 따라서 마지막 Arc는 기존 `6`처럼 full close한다.
- 즉:
  - non-final arc: body first, tail delayed
  - final arc: full run

## Resume Semantics

- 새 DB schema나 별도 checkpoint table은 1차 구현에 필수 아님.
- 이유:
  - `Stage 3`는 기존 blueprint를 자동 스킵한다.
  - `Stage 4`는 `get_latest_episode_number()` 기준 다음 미작성 화부터 시작한다.
  - `arcs` anchor와 `latest_blueprint_number`, `latest_episode_number`로 현재 위치를 충분히 추론할 수 있다.

### Inference Rules

- Arc N 상태는 아래로 판정한다.
  - `latest_written < ep_start`: 미시작
  - `ep_start <= latest_written < ep_end-1`: body 진행 중
  - `latest_written == ep_end-1` and next arc 미설계: tail 대기
  - `latest_written == ep_end-1` and next arc 설계됨: tail ready
  - `latest_written >= ep_end`: arc closed
- `latest_blueprint_number`가 `ep_end`까지 가 있고 `latest_written == ep_end-1`이면:
  - tail blueprint는 이미 있고 tail manuscript만 남은 상태로 본다

### Completion Definition

- 기존 `6`의 `fully_done_arcs`는 `latest_written >= arc.ep_end`다.
- `7`도 최종 closed arc 정의는 동일하게 유지한다.
- 다만 중간 상태 로그는 아래를 추가로 보여준다.
  - `body_done / tail_deferred / next_arc_ready`

## Work Packages

### E-1. Planner helper 추출

- `main_a.py` 내부에 pure helper를 추가한다.
- 책임:
  - current arc / next arc / final arc 판정
  - body target / tail target 계산
  - 현재 resume 상태 계산
- 추천 이름 예시:
  - `_resolve_one_stop_lookahead_plan()`
  - `_classify_lookahead_arc_state()`

### E-2. 메뉴 `7` 추가

- 메인 메뉴에 `7` 항목 추가
- dispatch는 새 wrapper 함수로 연결
- 추천 이름:
  - `_one_stop_pipeline_lookahead()`

### E-3. Arc processing loop 구현

- 현재 `_one_stop_pipeline()`를 복제하지 말고, 가능한 범위에서 공통 하위 helper를 뽑는다.
- 최소 공통 함수 후보:
  - `ensure_arc_designed(arc_no)`
  - `run_stage3_until(target_ep)`
  - `run_stage4_until(target_ep)`
- 단, 1차 구현에서 과도한 공통화는 금지한다.

### E-4. Resume/status 출력 보강

- `_show_resume_status()`는 그대로 두고, `7번` 전용 상태 로그를 추가한다.
- 최소 표시는 아래로 충분하다.
  - 현재 arc
  - body 범위
  - tail ep
  - next arc designed 여부
  - tail blueprint/tail manuscript 완료 여부

### E-5. Final arc 예외 및 경계값 방어

- `ep_count <= 1` 같은 비정상 경계값이면 holdback을 비활성화하고 full close로 폴백한다.
- Stage 2가 가변 페이싱이더라도 `body_end = ep_end - 1`만 일관되게 쓰면 된다.
- final arc에서는 next arc 설계 시도를 하지 않는다.

## Non-Goals

- Stage 3 semantic context 자체를 고치지 않는다.
- Stage 4 writer/director prompt를 바꾸지 않는다.
- `6번` 의미를 변경하지 않는다.
- 새 DB table, migration, anchor를 1차 구현의 필수로 삼지 않는다.
- `holdback 2화 이상`으로 확장하지 않는다. 1차는 tail 1화만 유예한다.

## Acceptance Criteria

- 메인 메뉴에 `7`이 추가된다.
- `6`은 기존대로 동작한다.
- non-final arc에서:
  - body만 먼저 Stage 3/4 처리된다.
  - tail은 next arc 설계 전까지 처리되지 않는다.
  - next arc 설계 후 tail이 처리된다.
- final arc에서는 full close가 된다.
- rerun/resume 시 중복 작성 없이 이어서 진행된다.
- 기존 `target_ep` 기반 Stage 3/4 resume contract를 깨지 않는다.

## Verification Plan

- pure planner unit test
  - current arc / next arc designed 여부 / final arc 여부에 따른 plan 산출 검증
- one-stop lookahead orchestration test
  - body target과 tail target 호출 순서 검증
- resume test
  - `latest_written == ep_end-1` + next arc 미설계
  - `latest_written == ep_end-1` + next arc 설계됨
  - `latest_blueprint_number == ep_end` + manuscript 미완료
- final arc test
  - holdback 없이 full close 검증

## Deliverables

- 코드:
  - `main_a.py`
  - 필요 시 소규모 pure helper 추가
- 테스트:
  - planner/orchestration/resume 중심 타깃 회귀
- 문서:
  - post-fix 3-pass closure
