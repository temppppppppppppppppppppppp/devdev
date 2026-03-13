# One-Stop Frontier Lag 실행 SSOT

작성일: 2026-03-13  
대상 코드: `main_a.py`, `modules/core/stage3_orchestrator.py`, `modules/core/stage4_orchestrator.py`  
선행 문서: `docs/2026-03-13/one-stop-lookahead-execution-ssot.md`  
문서 상태: `supersedes prior tail-holdback draft`

## Summary

- 기존 `6번 One-Stop`은 유지한다.
- 새 `7번`은 `tail 1화 유예`보다 한 단계 더 명확한 `frontier lag` 모드로 정의한다.
- 핵심 규칙:
  - `진짜 마지막 아크`가 아니면
  - `Stage 3 target = designed frontier ep_end - 1`
  - `Stage 4 target = designed frontier ep_end - 2`
- 여기서 `진짜 마지막 아크`는 `현재 마지막으로 설계된 아크`가 아니라 `Bible MasterBible.plot_roadmap의 마지막 block에 대응하는 arc`를 뜻한다.
- 즉 non-final frontier에서는 항상 `설계 > 블루프린트 > 원고`가 한 에피소드씩 어긋난 상태를 유지한다.

## Why This Revision

- 기존 초안은 `Arc N tail 1화`를 다음 Arc 설계 뒤 닫는 방식이었다.
- 그 방식도 맞는 방향이지만, 실행/재실행 관점에서는 상태 분기가 더 많다.
- 사용자가 제안한 `frontier lag` 규칙은 더 단순하다.
  - 현재 설계 frontier만 보면 된다.
  - 다음 실행 때 frontier가 확장되면 이전 holdback이 자동으로 풀린다.
  - per-arc tail close phase를 별도로 만들 필요가 없다.

## Baseline Facts

- 현재 `6번`은 Arc-by-Arc One-Stop이다.
  - 메뉴 라벨: `main_a.py:2143`
  - 분기: `main_a.py:2173-2174`
- 현재 `_one_stop_pipeline()`은 다음 순서를 쓴다.
  - Arc N 설계 보장
  - `Stage 3 target_ep = arc_ep_end`
  - `Stage 4 target_ep = arc_ep_end`
  - `main_a.py:3466`
  - `main_a.py:3598`
  - `main_a.py:3636`
- `Stage 3`는 `target_ep`까지 blueprint를 채우고 기존 blueprint는 스킵한다.
  - `modules/core/stage3_orchestrator.py:478`
  - `modules/core/stage3_orchestrator.py:575-586`
  - `modules/core/stage3_orchestrator.py:707`
- `Stage 4`는 `get_latest_episode_number()`가 가리키는 다음 미작성 화부터 `target_ep`까지 쓴다.
  - `modules/core/project_manager.py:640`
  - `modules/core/db_manager.py:2250`
  - `modules/core/stage4_orchestrator.py:582-617`
- Stage 2의 arc count 기준은 `MasterBible.plot_roadmap` 길이다.
  - `modules/core/stage2_orchestrator.py:156-177`
  - `main_a.py:3478-3481`

## Definitions

### D-1. True Final Arc

- `true_final_arc_no = len(MasterBible.plot_roadmap)`
- `arc_no == true_final_arc_no`인 arc만 `진짜 마지막 아크`다.
- `현재 마지막으로 설계된 arc`는 final arc일 수도 있고 아닐 수도 있다.
- 따라서 `designed frontier arc`와 `true final arc`를 혼동하면 안 된다.

### D-2. Designed Frontier

- `designed_frontier_arc_no = len(db.load_anchor("arcs") or [])`
- `designed_frontier_ep_end = arcs[-1].ep_end`
- 이 값이 현재 설계 완료 최전선이다.

### D-3. Frontier Lag

- `designed_frontier_arc_no < true_final_arc_no`일 때:
  - `stage3_target = designed_frontier_ep_end - 1`
  - `stage4_target = designed_frontier_ep_end - 2`
- `designed_frontier_arc_no == true_final_arc_no`일 때:
  - 최종 아크 예외 처리로 `stage3_target = designed_frontier_ep_end`
  - `stage4_target = designed_frontier_ep_end`

## User Example Revalidated

### Example A. 3아크까지 설계, 3아크가 13화까지

- 전제:
  - 3아크는 아직 true final arc가 아님
  - Stage 2 가변 페이싱 결과 `arc3.ep_end = 13`
- 적용:
  - `Stage 3 target = 12`
  - `Stage 4 target = 11`
- 해석:
  - 13화는 미래 arc context 없으므로 blueprint 유예
  - 12화는 blueprint는 있지만 manuscript 유예

### Example B. 다음 실행에서 4아크까지 설계, 4아크가 16화까지

- 전제:
  - 4아크도 아직 true final arc가 아님
  - 새 Stage 2 결과 `arc4.ep_end = 16`
- 적용:
  - `Stage 3 target = 15`
  - `Stage 4 target = 14`
- 해석:
  - 이전에 hold된 12~13화가 자연스럽게 Stage 4/Stage 3 범위 안으로 들어온다.
  - 별도 `tail close` phase를 짤 필요가 없다.

이 두 예시는 현재 설계와 모순되지 않고, 오히려 wrapper 수준 구현을 단순하게 만든다.

## Orchestration Policy

### Rule 1. `6`은 그대로 둔다

- `6`은 현재처럼 `full arc close` 모드로 유지한다.
- 빠른 검증/오염 감지 path를 보존한다.

### Rule 2. `7`은 frontier lag 모드다

- 새 메뉴 `7`은 `One-Stop Frontier Lag`로 정의한다.
- 예시 라벨:
  - `🧭 One-Stop Frontier Lag`
  - `🧭 One-Stop+1: Blueprint/Manuscript Lag`

### Rule 3. Stage 2만 frontier를 전진시킨다

- `7`의 본질은 Stage 2가 frontier를 민 뒤, Stage 3/4는 그 frontier를 일부러 덜 따라가는 것이다.
- 즉 제어점은 Stage 3/4 내부가 아니라 `main_a.py` wrapper에 있다.

### Rule 4. Stage 3/4 내부 엔진은 건드리지 않는다

- Stage 3/4는 이미 `target_ep`와 resume semantics를 갖고 있다.
- 1차 구현은 wrapper에서 `target_ep`를 계산해서 넘기는 방식이 정답이다.

## Required Computation

각 배치 반복에서 아래를 계산한다.

- `true_final_arc_no`
- `designed_frontier_arc_no`
- `designed_frontier_ep_end`
- `is_true_final_frontier = designed_frontier_arc_no == true_final_arc_no`

그 다음:

- if `is_true_final_frontier`:
  - `stage3_target = designed_frontier_ep_end`
  - `stage4_target = designed_frontier_ep_end`
- else:
  - `stage3_target = designed_frontier_ep_end - 1`
  - `stage4_target = designed_frontier_ep_end - 2`

경계값 방어:

- Stage 2 min ep_count는 3이므로 non-final frontier에서도 `stage4_target >= arc_ep_start`는 성립한다.
- 그래도 계산식은 `max(0, ...)` 또는 `max(ep_start, ...)`로 방어한다.

## Resume Semantics

새 DB schema는 1차 구현에 필수 아니다.

이유:

- `Stage 3`는 `target_ep` 이전 blueprint를 자동 스킵한다.
- `Stage 4`는 next unwritten episode부터 `target_ep`까지 간다.
- 따라서 `latest_blueprint_number`, `latest_episode_number`, `arcs`만으로 현재 lag 상태를 충분히 추론할 수 있다.

### State Inference

- `bp_max = latest_blueprint_number`
- `ms_max = get_latest_episode_number() - 1`
- `frontier_s3_target`, `frontier_s4_target`를 계산한 뒤 아래처럼 본다.

non-final frontier 기준:

- `bp_max < frontier_s3_target`: Stage 3 backlog 존재
- `bp_max == frontier_s3_target`: Stage 3 aligned
- `ms_max < frontier_s4_target`: Stage 4 backlog 존재
- `ms_max == frontier_s4_target`: Stage 4 aligned

final frontier 기준:

- `bp_max == designed_frontier_ep_end` and `ms_max == designed_frontier_ep_end`면 fully closed

## Work Packages

### E-1. Frontier planner helper 추가

- `main_a.py`에 pure helper 추가
- 책임:
  - true final arc 판정
  - designed frontier 산출
  - stage3/stage4 target 계산
  - resume 상태 분류

추천 helper:

- `_resolve_one_stop_frontier_lag_plan()`
- `_compute_frontier_targets()`
- `_is_true_final_arc()`

### E-2. 메뉴 `7` 추가

- 메인 메뉴 map에 `7` 추가
- dispatch에 새 wrapper 연결

추천 wrapper:

- `_one_stop_pipeline_frontier_lag()`

### E-3. Stage 2 / 3 / 4 wrapper 호출 정렬

- Stage 2는 기존과 동일하게 Arc를 설계한다.
- 설계 직후 `designed_frontier`를 다시 읽는다.
- 계산된 target으로:
  - `stage_3_batch_blueprinting(target_ep=stage3_target)`
  - `stage_4_v2_chief_writer(target_ep=stage4_target)`

### E-4. 상태 로그 보강

- `7` 전용 로그에 아래를 보여준다.
  - true final arc no
  - designed frontier arc no
  - designed frontier ep_end
  - computed stage3 target
  - computed stage4 target
  - current bp_max / ms_max

### E-5. Final arc full-close 예외

- designed frontier가 true final arc에 도달한 순간, lag를 해제한다.
- 이때는 backlog 포함 전체를 마무리한다.

## Non-Goals

- Stage 3 context contract 수정
- Stage 4 writer/director prompt 수정
- 6번 의미 변경
- DB checkpoint table 추가
- 2episode 이상 lag 확장

## Acceptance Criteria

- 메인 메뉴에 `7`이 추가된다.
- `6`은 기존 동작을 유지한다.
- non-final frontier에서:
  - `Stage 3 target = frontier_ep_end - 1`
  - `Stage 4 target = frontier_ep_end - 2`
- final frontier에서:
  - `Stage 3/4 모두 frontier_ep_end`까지 full close
- rerun/resume 시 중복 생성 없이 이어서 동작한다.
- 사용자가 제시한 13→12/11, 16→15/14 예시를 planner가 그대로 재현한다.

## Verification Plan

- pure planner unit tests
  - frontier 3 / total 10 / ep_end 13 → `(12, 11)`
  - frontier 4 / total 10 / ep_end 16 → `(15, 14)`
  - frontier == final / ep_end N → `(N, N)`
- orchestration test
  - Stage 2 후 frontier 재계산
  - Stage 3/4 target 호출값 검증
- resume test
  - partial blueprint backlog
  - partial manuscript backlog
  - final frontier close

## Deliverables

- 코드:
  - `main_a.py`
  - 필요 시 소규모 pure helper
- 테스트:
  - planner/orchestration/resume 타깃 회귀
- 문서:
  - post-fix 3-pass closure
