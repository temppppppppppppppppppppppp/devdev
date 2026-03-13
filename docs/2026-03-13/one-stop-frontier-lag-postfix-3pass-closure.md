# One-Stop Frontier Lag Post-Fix 3Pass Closure

작성일: 2026-03-13  
대상 SSOT: `docs/2026-03-13/one-stop-frontier-lag-execution-ssot.md`  
대상 감리: `docs/2026-03-13/one-stop-frontier-lag-3pass-audit.md`

## Executive Summary

- 판정: `closed`
- 구현 상태:
  - 기존 `6`은 유지
  - 새 `7`은 `Frontier Lag` 모드로 추가
- 최종 확신도: `95%`

## Implemented Changes

### 1. 메뉴 및 디스패치 추가

- 메인 메뉴에 `7 = One-Stop Frontier Lag`를 추가했다.
  - `main_a.py:2144`
- 디스패치에서 새 wrapper로 연결했다.
  - `main_a.py:2177`

### 2. Frontier planner helper 추가

- `true final arc` / `designed frontier` / `Stage 3/4 target` 계산을 pure helper로 분리했다.
  - `_compute_frontier_targets()`
  - `main_a.py:3469`
- runtime 정렬 상태를 한 번에 반환하는 plan resolver를 추가했다.
  - `_resolve_one_stop_frontier_lag_plan()`
  - `main_a.py:3495`

### 3. 새 wrapper 구현

- `_one_stop_pipeline_frontier_lag()`를 추가했다.
  - `main_a.py:3531`
- 핵심 규칙:
  - non-final frontier:
    - `Stage 3 target = frontier ep_end - 1`
    - `Stage 4 target = frontier ep_end - 2`
  - true final frontier:
    - `Stage 3 target = frontier ep_end`
    - `Stage 4 target = frontier ep_end`
- `remaining`은 manuscript 완료 arc가 아니라 `추가 설계 가능 arc 수` 기준으로 계산해, 사용자가 원한 `3arc -> 4arc` frontier 전진 흐름과 맞췄다.
  - `main_a.py:3549`
  - `main_a.py:3600`
  - `main_a.py:3758`

## Pass 1

- SSOT의 핵심 요구는 그대로 구현됐다.
  - `6` 유지
  - `7` 신설
  - wrapper-only 방식
  - true final arc 예외 유지
- 설계 frontier 기준으로 `target_ep`를 계산하도록 분리되어, Stage 3/4 엔진 내부 수정은 발생하지 않았다.

## Pass 2

- helper 테스트로 아래 acceptance example을 고정했다.
  - non-final `13 -> 12/11`
  - final `16 -> 16/16`
  - old full-close 상태에서 `ahead` 판정
  - 설계 arc 없음 시 `None`
- 테스트 파일:
  - `tests/test_one_stop_frontier_lag.py`

## Pass 3

- 오탐 후보였던 `fully_done_arcs 기반 재시작`은 이번 모드에선 부적합하다고 재확인했다.
- 대신 `designed frontier 기반 remaining`으로 잠가, rerun 시 `3arc에서 멈춘 뒤 다음 실행에서 4arc로 전진` 시나리오가 자연스럽게 동작하도록 맞췄다.
- 새 `P0 / P1 / P2` retained finding은 없다.

## Verification

실행 근거:

- `python -m py_compile main_a.py`
- `pytest -q tests/test_one_stop_frontier_lag.py tests/test_main_a_rollback.py`
  - 결과: `10 passed`
- `pytest -q tests/test_stage3_orchestrator.py tests/test_run_stage4_canary.py tests/test_main_a_rollback.py tests/test_one_stop_frontier_lag.py`
  - 결과: `70 passed`

## Residual Risk

- `runtime-only observation` 1건:
  - 새 `7` 메뉴를 실제 interactive live run으로 아직 끝까지 태우지는 않았다.
  - 다만 menu wiring, helper acceptance example, `target_ep` 계약 회귀, `py_compile`까지 확보돼 blocker로 보지는 않는다.

## Confidence Ledger

- `70`: SSOT 요구사항과 구현 표면 일치
- `+10`: helper 분리로 true final / frontier / alignment 계산을 명시적으로 고정
- `+10`: acceptance example 및 alignment 분기 테스트 추가
- `+5`: Stage 3 target contract 회귀와 main_a 회귀를 함께 통과
- `-0`: 새로운 retained finding 없음
- 최종: `95`

## Final Judgment

- 이번 구현은 사용자가 정의한 `frontier lag` 규칙과 일치한다.
- 기존 `6`을 보존하면서 `7`을 독립 모드로 추가한 결정도 적절하다.
- 현재 기준으로는 `execution complete / post-fix audit complete / 95% confidence`로 닫는다.
