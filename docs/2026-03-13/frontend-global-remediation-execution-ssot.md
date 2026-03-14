# 프론트엔드 전역 remediation 실행 SSOT

> 작성일: 2026-03-13
> 상태: `execution-ready`
> 문서 역할: [frontend-global-full-survey-3pass-final-audit.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/frontend-global-full-survey-3pass-final-audit.md), [frontend-global-full-survey-3pass-reaudit.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/frontend-global-full-survey-3pass-reaudit.md) 기준으로 retained frontend finding `7건`의 수정 범위와 순서를 잠그는 단일 실행 SSOT
> 금지사항: 이 문서는 코드 수정, 테스트 실행, rerun 기록 문서가 아니다. 범위 고정, work package 정의, acceptance 잠금까지만 담당한다.

## 1. 기준 문서

- [frontend-global-full-survey-audit-order.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/frontend-global-full-survey-audit-order.md)
- [frontend-global-full-survey-3pass-final-audit.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/frontend-global-full-survey-3pass-final-audit.md)
- [frontend-global-full-survey-3pass-reaudit.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/frontend-global-full-survey-3pass-reaudit.md)
- [FGS-T3-shell-ipc-splash-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/FGS-T3-shell-ipc-splash-findings.md)
- [FGS-T4-bridge-runner-contract-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/FGS-T4-bridge-runner-contract-findings.md)
- [FGS-T5-packaging-bundle-asset-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/FGS-T5-packaging-bundle-asset-findings.md)
- [FGS-T6-regression-trust-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/FGS-T6-regression-trust-findings.md)

## 2. Executive Summary

이번 실행 SSOT의 목표는 retained frontend finding `7건`을 무작정 다 고치는 것이 아니라, 실제 수정 묶음으로 재조합해 다음 네 축으로 닫는 것이다.

1. packaging artifact model 단일화
2. Stage 0 external contract 정렬
3. regression gate 확장과 behavior-first coverage 보강
4. shell/shadow surface 정리

핵심 원칙은 단순하다.

- 문서가 거짓말하면 문서를 고치거나 빌드를 바꿔야 한다.
- hidden contract가 남아 있으면 UI/validator/prompt-map/runner 중 하나로 정렬해야 한다.
- source-string guard는 유지해도 되지만, behavior-first gate가 함께 있어야 한다.
- shipping 대상이 아닌 shadow surface는 제거하거나 명시적으로 비활성화해야 한다.

## 3. Scope

포함:

- [geuldobi-desktop/package.json](C:/Users/User/Desktop/글도비/geuldobi-desktop/package.json)
- [geuldobi-desktop/DESKTOP-GUIDE.md](C:/Users/User/Desktop/글도비/geuldobi-desktop/DESKTOP-GUIDE.md)
- [geuldobi-desktop/src/main.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/main.js)
- [geuldobi-desktop/main.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/main.js)
- [geuldobi-desktop/src/preload.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/preload.js)
- [geuldobi-desktop/src/index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html)
- [geuldobi-desktop/src/splash/splash.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/splash/splash.js)
- [build/build_release.ps1](C:/Users/User/Desktop/글도비/build/build_release.ps1)
- [build/backend_entry.py](C:/Users/User/Desktop/글도비/build/backend_entry.py)
- [modules/api/process_runner.py](C:/Users/User/Desktop/글도비/modules/api/process_runner.py)
- [modules/api/run_validator.py](C:/Users/User/Desktop/글도비/modules/api/run_validator.py)
- [docs/implementation/prompt-map-v1.json](C:/Users/User/Desktop/글도비/docs/implementation/prompt-map-v1.json)
- 관련 frontend/bridge/runtime tests

제외:

- desktop visual redesign
- prompt 내용 재설계
- Stage 2~4 알고리즘 품질 개선
- installer signing/SmartScreen 문제
- unrelated backend refactor

## 4. 실행 원칙

### 원칙 A. 배포 모델은 하나만 남긴다

- `engine.exe` closed-binary 모델과 `source bundle + embedded python` 모델을 동시에 말하는 상태는 금지한다.
- build, env, docs, packaged inventory가 같은 모델을 설명해야 한다.

### 원칙 B. external Stage 0 contract는 hidden branch를 허용하지 않는다

- UI가 노출하지 않는 `sub_key`를 validator/prompt-map/real app이 계속 허용하면 안 된다.
- internal-only branch를 유지할 거면 explicit internal contract로 격리한다.

### 원칙 C. default gate는 retained risk를 직접 덮어야 한다

- `npm test` green은 desktop 기본 품질 신호다.
- retained finding과 직접 연결되는 bridge/risk/runtime-path suite를 package gate에서 빼면 안 된다.

### 원칙 D. source-string guard는 보조막이다

- DOM 존재, literal presence 검사는 유지 가능하다.
- 그러나 splash/material/workspace/offline/Stage 0 contract처럼 stateful surface는 behavior-first test가 필요하다.

### 원칙 E. shadow surface는 방치하지 않는다

- shipping path가 아니더라도, live copy와 drift한 duplicate entry는 삭제 또는 inert marking이 필요하다.

## 5. Package Map

| Work Package | 포함 finding |
|--------------|--------------|
| `FG-E1` Packaging Model Unification | `FGS-T5-001`, `FGS-T5-002` |
| `FG-E2` Stage 0 External Contract Closure | `FGS-T4-001` |
| `FG-E3` Regression Gate Expansion | `FGS-T6-001`, `FGS-T6-002`, `FGS-T6-003` |
| `FG-E4` Shell Shadow Hygiene | `FGS-T3-001` |

## 6. Work Packages

### FG-E1. Packaging Model Unification

대상 finding:

- `FGS-T5-001`
- `FGS-T5-002`

대상 파일:

- [geuldobi-desktop/package.json](C:/Users/User/Desktop/글도비/geuldobi-desktop/package.json)
- [build/build_release.ps1](C:/Users/User/Desktop/글도비/build/build_release.ps1)
- [build/backend_entry.py](C:/Users/User/Desktop/글도비/build/backend_entry.py)
- [geuldobi-desktop/src/main.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/main.js)
- [geuldobi-desktop/DESKTOP-GUIDE.md](C:/Users/User/Desktop/글도비/geuldobi-desktop/DESKTOP-GUIDE.md)

구현 원칙:

- 실제 배포 모델을 `engine.exe`로 맞출지, `source bundle + embedded python`으로 맞출지 먼저 선택한다.
- 선택 후 아래 네 층을 동시에 정렬한다.
  - build output
  - main process env
  - backend entry env
  - user-facing guide
- fallback 경로가 정상 경로라면 warning/fallback이라는 표현도 정리한다.

acceptance:

- packaged resource inventory, build script, `main.js`, `backend_entry.py`, `DESKTOP-GUIDE.md`가 같은 artifact model을 설명한다.
- `GEULDOBI_ENGINE_EXE`가 유지되면 실제 packaged artifact에 해당 파일이 존재한다.
- `GEULDOBI_ENGINE_EXE`가 제거되면 runner와 guide도 source-bundle launch semantics로 정렬된다.
- “소스 코드 비공개” 문구는 실제 배포물과 일치할 때만 유지된다.

필수 테스트/검증:

- packaged resource inventory check
- `tests/test_process_runner.py`
- build/doc contract regression

### FG-E2. Stage 0 External Contract Closure

대상 finding:

- `FGS-T4-001`

대상 파일:

- [modules/api/run_validator.py](C:/Users/User/Desktop/글도비/modules/api/run_validator.py)
- [modules/api/process_runner.py](C:/Users/User/Desktop/글도비/modules/api/process_runner.py)
- [docs/implementation/prompt-map-v1.json](C:/Users/User/Desktop/글도비/docs/implementation/prompt-map-v1.json)
- [geuldobi-desktop/src/index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html)
- 필요 시 [modules/core/stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py)

구현 원칙:

- 선택지는 둘뿐이다.
  - external contract를 `1..7`로 닫는다.
  - `0`을 internal-only branch로 격리하고 desktop/public contract에서 제거 사실을 명시한다.
- UI, validator, prompt-map, bridge, runner, tests가 모두 같은 결론을 따라야 한다.

acceptance:

- real `/run` contract와 desktop renderer가 같은 Stage 0 submenu 집합을 공유한다.
- source-string tests와 behavior-first tests가 같은 sub_key 집합을 잠근다.
- hidden `sub_key 0`을 그대로 public contract에 남기는 상태는 사라진다.

필수 테스트/검증:

- `tests/test_run_validator.py`
- `tests/test_process_runner_stage0_inputs.py`
- `tests/test_frontend_stage0_connectivity.py`
- real app Stage 0 contract test

### FG-E3. Regression Gate Expansion

대상 finding:

- `FGS-T6-001`
- `FGS-T6-002`
- `FGS-T6-003`

대상 파일:

- [geuldobi-desktop/package.json](C:/Users/User/Desktop/글도비/geuldobi-desktop/package.json)
- [tests/test_desktop_contract_refresh.py](C:/Users/User/Desktop/글도비/tests/test_desktop_contract_refresh.py)
- frontend/bridge/runtime 관련 tests

구현 원칙:

- 기본 `npm test`는 retained finding과 직접 연결된 suite를 포함해야 한다.
- source-string guard를 삭제할 필요는 없지만, 최소한 아래 surface는 behavior-first test가 필요하다.
  - splash readiness/handoff
  - material file IPC
  - workspace open/path bridge
  - offline mode placeholder/rendering
  - real-app Stage 0 public contract

acceptance:

- `npm test` 기본 게이트가 bridge/risk/runtime-path 계열을 포함한다.
- splash/material/workspace/offline 중 최소 핵심 1차 behavior coverage가 추가된다.
- source-string test만 green이어도 semantic drift가 통과하는 상태를 줄인다.

필수 테스트/검증:

- package test script refresh
- `tests/test_bridge_server_http_contract.py`
- `tests/test_bridge_server_desktop_risk_gate.py`
- `tests/test_bridge_quality_summary.py`
- `tests/test_runtime_paths.py`
- 신규 splash/material/workspace/offline behavior tests

### FG-E4. Shell Shadow Hygiene

대상 finding:

- `FGS-T3-001`

대상 파일:

- [geuldobi-desktop/main.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/main.js)
- [geuldobi-desktop/src/main.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/main.js)
- 관련 guide 문서

구현 원칙:

- root-level duplicate main은 live copy와 drift한 상태로 남기지 않는다.
- 선택지는 셋이다.
  - 삭제
  - thin redirect/inert stub
  - generated mirror로 전환
- 단순 방치 금지.

acceptance:

- maintainer가 `geuldobi-desktop/main.js`를 열어도 live entry와 헷갈리지 않는다.
- live entry는 `src/main.js` 하나로 명시된다.
- shadow file이 남아도 drift를 만들지 않는 구조로 고정된다.

필수 테스트/검증:

- package main path contract 확인
- shadow file hygiene regression 또는 docs lint-level check

## 7. 우선순위

1. `FG-E1 Packaging Model Unification`
2. `FG-E2 Stage 0 External Contract Closure`
3. `FG-E3 Regression Gate Expansion`
4. `FG-E4 Shell Shadow Hygiene`

이 순서를 고정하는 이유:

- packaging model이 가장 강한 `P1`이며, docs/build/env를 동시에 오염시킨다.
- Stage 0 hidden contract는 external/public API drift이므로 다음으로 닫아야 한다.
- regression gate 확장은 앞의 계약을 잠그는 수단이다.
- shadow hygiene는 중요하지만 shipping semantics가 정렬된 뒤 처리해도 된다.

## 8. 완료 기준

- retained finding `7건`이 모두 work package에 1:1 매핑된다.
- 과잉 범위가 없다.
- excluded scope가 유지된다.
- acceptance가 build/docs/tests/runtime contract 기준으로 측정 가능하다.
- 후속 구현자는 이 문서만 보고도 수정 순서와 proof gate를 이해할 수 있다.

## 9. 이번 턴 범위

- 이번 턴은 remediation execution SSOT 작성까지가 범위다.
- 코드 수정과 실제 테스트 보강은 후속 구현 턴에서 수행한다.
