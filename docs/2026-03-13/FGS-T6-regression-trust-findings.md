# FGS-T6 Regression Trust Findings

> 작성일: 2026-03-13
> 상태: `PASS3 complete`
> 범위: package test script, frontend/bridge regression set, coverage closure

## 조사 범위

- `geuldobi-desktop/package.json`
- `tests/test_desktop_contract_refresh.py`
- `tests/test_frontend_stage0_connectivity.py`
- `tests/test_frontend_frontier_lag_wiring.py`
- `tests/test_ui_renderer_sanitization.py`
- `tests/test_desktop_work_guard_template_contract.py`
- `tests/test_bridge_server_http_contract.py`
- `tests/test_bridge_server_desktop_risk_gate.py`
- `tests/test_bridge_quality_summary.py`
- `tests/test_process_runner_stage0_inputs.py`
- `tests/test_run_validator.py`

## PASS 1 사실 수집

- desktop package test script는 8개 pytest 파일만 실행한다.
- `test_desktop_contract_refresh.py`는 package test script에 특정 파일명이 들어있는지만 본다.
- `test_frontend_stage0_connectivity.py`, `test_ui_renderer_sanitization.py`, `test_desktop_work_guard_template_contract.py`는 주로 source-string assertion 기반이다.
- 반면 `test_bridge_server_http_contract.py`, `test_bridge_server_desktop_risk_gate.py`, `test_bridge_quality_summary.py`, `test_runtime_paths.py`는 더 behavior-oriented한 real-app 또는 runtime-path 검증이다.
- `splash`, material IPC, workspace open/path, offline mode 관련 자동 테스트 흔적은 찾지 못했다.

## PASS 2 교차 검증

- 표적 pytest 묶음 실행 결과는 `196 passed in 4.52s`였다.
- green signal 자체는 긍정적이지만, package-level `npm test`가 실제로 실행하는 목록은 더 좁다.
- 따라서 현재 회귀망은 “일부 고신뢰 테스트가 존재함”과 “desktop package 기본 게이트는 그 전부를 돌리지 않음”이 동시에 참이다.

## PASS 3 오탐 제거

- `FGS-T6-H1`: 프론트엔드 회귀망이 전혀 없다
  - 판정: `rejected`
  - 이유: source-string 기반이라도 다수의 focused regression이 존재하고 이번 실행에서도 green이었다.

## 확정 findings

### FGS-T6-001

- Severity: `P2`
- 현상 요약: `npm test` 기본 게이트가 real-app HTTP contract, desktop risk gate, runtime path 계열 테스트를 포함하지 않아 package-level green signal의 신뢰도가 제한된다.
- 코드 근거:
  - `geuldobi-desktop/package.json:11`
  - `tests/test_desktop_contract_refresh.py:11-17`
- 보조 근거:
  - 존재하지만 package script에서 빠진 테스트: `tests/test_bridge_server_http_contract.py`, `tests/test_bridge_server_desktop_risk_gate.py`, `tests/test_bridge_quality_summary.py`, `tests/test_runtime_paths.py`
- counter-evidence review:
  - 더 넓은 pytest 묶음을 수동 실행하면 해당 테스트들은 통과한다.
  - 문제는 “존재 여부”가 아니라 기본 desktop gate의 coverage 범위다.
- 상태: `confirmed`
- 권장 후속 조치:
  - desktop package test script에 real-app bridge/risk/runtime-path 계열을 편입

### FGS-T6-002

- Severity: `P2`
- 현상 요약: splash lifecycle, material IPC, workspace open/path, offline mode는 live surface가 존재하지만 관련 자동 테스트 증거를 찾지 못했다.
- 코드 근거:
  - `geuldobi-desktop/src/splash/splash.js`
  - `geuldobi-desktop/src/preload.js:32-34`, `:52-53`
  - `geuldobi-desktop/src/main.js:511-572`, `:795-804`
  - `geuldobi-desktop/src/index.html:7737`
- 보조 근거:
  - 테스트 디렉터리 검색 결과 `splash`, `getWorkspacePath`, `openWorkspaceFolder`, `listMaterialFiles`, `importMaterialFile`, `deleteMaterialFile` 관련 자동 테스트 히트 없음
- counter-evidence review:
  - 코드 surface는 구현돼 있고, 수동 사용 시 동작할 가능성은 높다.
  - 다만 현재 자동화 증거층에는 비어 있다.
- 상태: `confirmed`
- 권장 후속 조치:
  - splash readiness, material file ops, workspace path bridge, offline placeholder를 behavior-first 테스트로 추가

### FGS-T6-003

- Severity: `P3`
- 현상 요약: 주요 프론트엔드 회귀 테스트가 source-string assertion 비중이 높아, DOM 존재는 잠가도 실제 이벤트 wiring/state transition behavior drift는 놓칠 수 있다.
- 코드 근거:
  - `tests/test_frontend_stage0_connectivity.py`
  - `tests/test_ui_renderer_sanitization.py`
  - `tests/test_desktop_work_guard_template_contract.py`
  - `tests/test_desktop_contract_refresh.py`
- 보조 근거:
  - 위 테스트들은 파일 텍스트 내 문자열 존재를 주로 확인한다.
  - behavior-first 예시는 `tests/test_bridge_server_http_contract.py`처럼 별도에 존재하지만 package 기본 게이트에는 포함되지 않는다.
- counter-evidence review:
  - source-string tests는 빠르고 drift 감지에 유용하다.
  - 다만 단독 신뢰 원천으로 쓰기엔 stateful UI surface가 너무 넓다.
- 상태: `confirmed`
- 권장 후속 조치:
  - source-string guard는 유지하되, state transition/IPC payload 중심 behavior tests를 병행

## 기각 findings

- frontend regression net absent

## coverage gap / open question

- 실제 Electron window lifecycle, splash-to-main handoff, packaged asset load는 live automation이 없어 `needs-live-check`로 남는다.

## PASS 요약

- PASS1 후보 4건
- PASS2 제거 1건
- 최종 3건
