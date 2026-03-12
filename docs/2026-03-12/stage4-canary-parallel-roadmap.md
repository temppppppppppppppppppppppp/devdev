# Stage 4 Canary Parallel Roadmap

작성일: 2026-03-12

목적: limited canary rerun 전에 병렬로 끝낼 수 있는 작업을 먼저 닫아 canary 1회의 가치와 재현성을 높인다.

## 결론

canary 전에 병렬로 해둘 가치가 큰 작업은 3개였다.

1. `safe Stage4-only prep`
2. `official canary runner`
3. `auto summary/analyzer`

이 3개는 실제 canary 시간을 줄이는 작업이라기보다, `실패한 canary를 다시 준비하는 시간`과 `판정에 쓰는 시간`을 줄인다. Stage 4 canary는 한번 돌리는 데 오래 걸리므로, 수동 copy/reset/log 확인을 반복하는 구조를 먼저 없애는 것이 ROI가 높다.

## 왜 선행해야 하는가

- 수동 project copy + 수동 DB 정리는 반복 가능성이 낮고, FTS/로그/메모리 상태를 어지럽히기 쉽다.
- ad-hoc inline harness는 `pass_rate_monitor.save()` 같은 종료 save 경로를 놓치기 쉽다.
- canary가 길게 돌고 나서야 sink mismatch를 발견하면 재실행 비용이 크다.

따라서 canary 자체보다 먼저 `준비 자동화`와 `사후 판정 자동화`를 닫는 것이 맞다.

## 병렬 작업 축

### Lane A. Safe Prep

목표:
- baseline project를 복사하되 source project는 건드리지 않는다.
- target copy에서는 Stage 3 blueprint를 유지하고, Stage 4 산출물만 제거한다.

현재 구현:
- `modules/core/stage4_canary_tools.py`
- `scripts/run_stage4_canary.py prepare`

핵심 계약:
- 유지: `blueprints`, `plans/blueprints`, stage0/setup 자산
- 제거: `manuscripts`, `state_logs`, `episode_bibles`, `stage4 director_selections`, `stage4 stage_attempts`, `drafts`, `logs`, `memory`
- 현재는 `from_ep=1`만 지원한다. 부분 rerun canary는 코드에서 거부한다.

주의:
- `ProjectService.wipe_production_data()`는 `blueprints`까지 지우므로 Stage 4 rerun baseline prep에는 쓰지 않는다.

### Lane B. Official Runner

목표:
- inline 임시 스크립트 대신 repeatable한 canary 실행 경로를 만든다.
- boot, Stage 4 run, `pass_rate_monitor.save()`, audit flush를 한 경로로 묶는다.

현재 구현:
- `scripts/run_stage4_canary.py run`
- `scripts/run_stage4_canary.py full`

핵심 계약:
- `SovereignApp.boot()`의 공식 초기화 경로를 사용한다.
- main menu loop만 우회한다.
- run 종료 후 `pass_rate_monitor.save()`와 audit flush를 명시적으로 호출한다.

### Lane C. Auto Summary

목표:
- canary 종료 직후 raw sink를 수동으로 뒤지지 않고 go/no-go를 빠르게 판단한다.

현재 구현:
- `modules/core/stage4_canary_tools.py`
- `scripts/run_stage4_canary.py analyze`

수집 항목:
- `runtime_audit_summary.tag`
- draft count
- `FailureAnalyzer.patch_trace_summary()`
- `FailureAnalyzer.sink_alignment_summary()`
- stage4 attempt count
- director stage4 row count

출력:
- `projects/<name>/logs/canary_summary.json`
- `hard_gates`는 운영 체크리스트와 같은 fail-close 기준을 따른다.

## 현재 상태

완료:
- `prepare` 자동화
- `run` 자동화
- `analyze` 자동화
- source/target 불변성 테스트
- Stage4-only cleanup 테스트

검증:
- `pytest -q tests/test_stage4_canary_tools.py`
- `python scripts/run_stage4_canary.py analyze --project 00_test_05 --target-ep 4`
- `python scripts/run_stage4_canary.py prepare --source-project 00_test_02 --target-project 00_test_06 --force`

## 권장 실행 순서

1. `prepare`
2. `analyze`로 baseline이 비워졌는지 확인
3. `run`
4. `analyze`로 hard gate 판정

예시:

```powershell
python scripts/run_stage4_canary.py prepare --source-project 00_test_02 --target-project 00_test_06 --force
python scripts/run_stage4_canary.py analyze --project 00_test_06 --target-ep 4
python scripts/run_stage4_canary.py run --project 00_test_06 --target-ep 4
python scripts/run_stage4_canary.py analyze --project 00_test_06 --target-ep 4
```

또는 한 번에:

```powershell
python scripts/run_stage4_canary.py full --source-project 00_test_02 --target-project 00_test_06 --target-ep 4 --force
```

## canary 직전 남은 판단

자동화 이후에도 사람 판단이 필요한 것은 2개다.

1. 어떤 baseline/project를 canary 대상으로 쓸지
2. `PASS_WITH_FIX`가 실제로 뜰 가능성이 높은 케이스를 추가로 잡을지

현재 기준 추천:
- mainline canary: `00_test_02` 계열
- `PASS_WITH_FIX` structural inplace 검증은 별도 PWF-likely case를 한 번 더 선정

## 운영 해석

이 로드맵의 목적은 live rerun 자체를 미루자는 것이 아니다. canary 1회를 더 비싸게 만들지 않기 위해, `수동 prep`과 `수동 판정`을 먼저 자동화한 것이다.

즉 다음 단계는 추가 개발보다 `준비된 canary를 실제로 한 번 태우는 것`에 가깝다.
