# One-Stop Frontier Lag 자동 연속 실행 수정 SSOT

> 작성일: 2026-03-13
> 상태: execution-ready
> 대상 코드: `main_a.py`
> 선행 문서:
> - `docs/2026-03-13/one-stop-frontier-lag-execution-ssot.md`
> - `docs/2026-03-13/one-stop-frontier-lag-postfix-3pass-closure.md`

---

## 0. Summary

- 대상은 `7번 One-Stop Frontier Lag` 메뉴다.
- 현재 장애물은 `1개 batch` 완료 후 다음 batch 진입 전에 사용자 승인(`계속할까요?`)이 필요하다는 점이다.
- 수정 목표는 `승인 없는 연속 실행`이다.
- 초기 입력은 유지하되, 의미를 `이번 실행의 batch size`로 고정한다.
- 이후 남은 Arc는 같은 batch size로 자동 연속 진행한다.
- hard stop은 유지한다.
  - `Stage 2` 설계 실패
  - `Stage 3` 실패 후 사용자 중단 선택
  - `KeyboardInterrupt`
  - 기타 치명 예외

---

## 1. Baseline Facts

- 현재 `7번`은 `_one_stop_pipeline_frontier_lag()`로 연결된다.
  - `main_a.py`
- 현재 구현은 아래 순서를 쓴다.
  1. 초기 `target_count` 입력
  2. 해당 수만큼 frontier 전진
  3. `remaining_design > 0`이면 `계속할까요?` 승인 입력
  4. 계속이면 다시 `추가로 몇 개 Arc를 설계할까요?` 입력
- 즉 unattended long run에서 batch 경계마다 사람 입력이 필요하다.

---

## 2. Problem Definition

### P-1. 아크 간 승인 프롬프트가 자동 장기 런을 방해함

- 현재 문제는 Arc 내부가 아니라 batch 경계에 있다.
- 특히 `target_count=1`이면 Arc 1개가 끝날 때마다 승인이 필요하다.
- 사용자가 잠자는 동안 `15arc` 같은 장기 run을 태우는 시나리오와 충돌한다.

### P-2. 승인 제거 시 의미론 drift 위험

- `계속할까요?`를 단순 제거하면 `target_count`가 무엇을 의미하는지 불명확해질 수 있다.
- 따라서 `target_count`의 의미를 문서로 재정의해야 한다.

---

## 3. New Contract

### D-1. `target_count`는 총 처리량이 아니라 batch size다

- 첫 입력에서 받은 `target_count`는 `한 번에 몇 Arc 폭으로 반복할지`를 뜻한다.
- 예:
  - `1`을 입력하면 `1Arc 단위`로 자동 연속 실행
  - `3`을 입력하면 `3Arc 묶음` 단위로 자동 연속 실행

### D-2. batch 경계 승인 프롬프트는 제거한다

- 제거 대상:
  - `계속할까요? (1=계속 / 2=중단...)`
  - `추가로 몇 개 Arc를 설계할까요?...`
- 이 두 입력은 더 이상 받지 않는다.

### D-3. 같은 batch size로 남은 Arc를 자동 소진한다

- `remaining_design > 0`이면
  - `target_count = min(remaining_design, batch_size)`
  - 로 재계산해 다음 tranche를 자동 실행한다.
- 즉 batch 폭만 유지하고, 마지막 tranche는 남은 수에 맞춰 자동 축소한다.

### D-4. hard stop은 유지한다

- 아래 상황에서는 기존처럼 중단한다.
  - `Stage 2` 설계 실패
  - `Stage 2` 설계 결과 확인 실패
  - `Stage 3` 실패 후 사용자가 `중단` 선택
  - `KeyboardInterrupt`
  - 치명 예외

---

## 4. Scope

### E-1. 승인 제거

- `_one_stop_pipeline_frontier_lag()`에서 batch 종료 후 승인/추가입력 루프 제거

### E-2. batch size 고정 자동 반복

- 최초 입력값을 `batch_size`로 저장
- `remaining_design`이 남아 있는 동안
  - `target_count = min(remaining_design, batch_size)`
  - 로 tranche를 자동 반복

### E-3. 로그 보강

- batch 종료 시 아래를 명시한다.
  - 이번 tranche 완료
  - 남은 Arc 수
  - 다음 tranche auto-continue 여부
  - 실제 적용될 다음 `target_count`

### E-4. 회귀 테스트

- 새 테스트는 최소 아래를 덮어야 한다.
  - batch 경계 승인 프롬프트가 더 이상 호출되지 않음
  - batch size `1`에서 auto-continue
  - 마지막 tranche에서 `min(remaining, batch_size)` 자동 축소
  - 기존 hard stop 경로는 유지

---

## 5. Non-Goals

- `6번 One-Stop` 의미 변경
- `Frontier Lag` target 계산 규칙 변경
- `Stage 3/4` 엔진 내부 계약 변경
- `Stage 3` 실패 시 skip/abort 정책 제거

---

## 6. Acceptance Criteria

- `7번` 실행 중 Arc 1개 처리 후 Arc 2개째 진입에 추가 승인 입력이 필요하지 않다.
- 최초 batch size 입력 후, 남은 Arc가 있으면 자동으로 다음 tranche를 수행한다.
- 마지막 tranche는 남은 Arc 수만큼 자동 축소된다.
- `Stage 2`/`Stage 3` hard stop 규칙은 기존처럼 유지된다.
- `6번` 동작은 바뀌지 않는다.

---

## 7. Verification Plan

- unit / focused tests
  - batch 경계에서 `input("계속할까요?")` 미호출
  - initial `batch_size=1`, `remaining_design=3`일 때 자동 3회 tranche 진행
  - initial `batch_size=3`, `remaining_design=5`일 때 `3 + 2`로 자동 진행
- static check
  - `python -m py_compile main_a.py`
- final
  - 전체 테스트 스위트
