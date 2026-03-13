# One-Stop Frontier Lag 자동 연속 실행 Post-Fix 3PASS Closure

> 작성일: 2026-03-13
> 상태: closed
> 기준 SSOT: `docs/2026-03-13/one-stop-frontier-lag-auto-continue-remediation-execution-ssot.md`
> 선행 감리: `docs/2026-03-13/one-stop-frontier-lag-auto-continue-remediation-3pass-audit.md`

---

## 0. 최종 결론

이번 수정 범위는 `closed`로 판정한다.

- `7번 Frontier Lag`은 batch 경계에서 더 이상 `계속할까요?` 승인을 요구하지 않는다.
- 최초 입력값은 `총 처리량`이 아니라 `batch size`로 고정됐다.
- 남은 Arc는 같은 batch size로 자동 연속 진행되고, 마지막 tranche는 `min(remaining, batch_size)`로 자동 축소된다.
- `Stage 3` 실패 시 `건너뛰고 다음 Arc로?` hard stop 프롬프트는 유지된다.
- 전체 테스트 스위트까지 green이다.

최종 확신도는 `95%`다.

---

## 1. 구현 내용

수정 파일:

- `main_a.py`
- `tests/test_one_stop_frontier_lag_auto_continue.py`
- `tests/test_pass_with_fix.py`

핵심 변경:

### 1.1 batch 경계 승인 제거

- `_one_stop_pipeline_frontier_lag()`에서 아래 입력을 제거했다.
  - `계속할까요?`
  - `추가로 몇 개 Arc를 설계할까요?`

### 1.2 batch size 고정 자동 반복

- 최초 입력값을 `batch_size`로 저장
- 이후 `remaining_design > 0`이면
  - `target_count = min(remaining_design, batch_size)`
  - 로 재계산해 자동 연속 실행

### 1.3 hard stop 유지

- 아래는 그대로 유지했다.
  - `Stage 2` 설계 실패
  - `Stage 2` 결과 확인 실패
  - `Stage 3` 실패/예외 후 사용자 선택
  - `KeyboardInterrupt`

### 1.4 regression 추가

- `tests/test_one_stop_frontier_lag_auto_continue.py`
  - batch size `1`에서 자동 연속 실행
  - 마지막 tranche 자동 축소
  - `Stage 3` abort prompt 유지

---

## 2. 검증

### 2.1 문법 확인

```text
python -m py_compile main_a.py tests/test_one_stop_frontier_lag_auto_continue.py tests/test_pass_with_fix.py
```

- 결과: 통과

### 2.2 focused regression

```text
pytest -q tests/test_one_stop_frontier_lag.py tests/test_one_stop_frontier_lag_auto_continue.py tests/test_main_a_rollback.py
```

- 결과: `13 passed in 2.15s`

### 2.3 전체 테스트 스위트

```text
pytest -q
```

- 결과: `4055 passed, 16 skipped, 1 warning`

warning:

- `tests/stage4_v2_test/test_batch_1_to_10.py` 의 기존 `PytestCollectionWarning` 1건

---

## 3. Post-Fix 3PASS 감리

### Pass 1. 구현-SSOT 대조

확인 항목:

- 승인 프롬프트 제거가 실제로 batch 경계에만 적용됐는가
- `target_count -> batch_size` 의미 재정의가 코드와 일치하는가
- `6번`은 건드리지 않았는가

판정:

- 일치
- 수정 범위는 `7번 wrapper`에만 머물렀다.

### Pass 2. 동작 감리

확인 항목:

- `batch_size=1`에서 Arc 1개 처리 후 Arc 2개째로 자동 진입하는가
- 마지막 tranche에서 `remaining`만큼 자동 축소되는가
- `Stage 3` 실패 시 hard stop prompt가 남아 있는가

판정:

- 일치
- focused regression 3축 모두 통과

### Pass 3. 회귀 감리

감리 중 실제 발견 이슈:

- 전체 스위트에서 `tests/test_pass_with_fix.py` fixture가 `validate_arc_data_fields`를 `MagicMock`로 암묵 생성해, 이전 Stage 2 helper 보강과 충돌했다.

대응:

- `tests/test_pass_with_fix.py`의 Stage 2 context mock에 `validate_arc_data_fields = None`을 명시했다.

재판정:

- 이 이슈는 `7번 Frontier Lag` 구현 자체의 결함이 아니라 test fixture realism 문제였다.
- 대응 후 전체 스위트 green으로 닫혔다.

---

## 4. 최종 Findings

### Closed

- `7번` batch 경계 사용자 승인 필요
- `1Arc` 단위 long run 시 다음 Arc 진입에 사람 입력이 필요하던 장애물
- 마지막 tranche 수동 batch 재입력 필요

### Observation

- 메서드 말미의 `[Enter] 메뉴로 돌아가기`는 그대로 남아 있다.
- 이건 batch 경계 승인 문제가 아니라 메뉴 복귀 입력이므로 이번 범위의 장애물로 보지 않는다.

---

## 5. 확신도 Ledger

- `70`: SSOT 범위 구현 완료
- `+10`: focused regression `13 passed`
- `+5`: batch 승인 제거 / hard stop 유지 분리 확인
- `+5`: 전체 테스트 스위트 `4055 passed`
- `+5`: 감리 중 발견된 fixture realism 문제 대응 완료

최종 확신도: `95%`

---

## 6. 닫힘 판단

이번 수정은 사용자가 지적한 장애물을 정확히 제거했다.

- `7번`은 이제 unattended long run에 맞게 동작한다.
- `6번`의 기존 의미를 흔들지 않았다.
- 문제 발견 시 대응까지 끝났고, 전체 테스트 스위트도 green이다.

따라서 현재 상태는 `execution complete / postfix 3PASS complete / test suite green / closed`다.
