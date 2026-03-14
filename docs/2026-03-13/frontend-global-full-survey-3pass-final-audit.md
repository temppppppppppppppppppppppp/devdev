# 프론트엔드 전역 전량 전수조사 3PASS 최종 감사

> 작성일: 2026-03-13
> 기준 오더: [frontend-global-full-survey-audit-order.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/frontend-global-full-survey-audit-order.md)
> 조사 모드: read-only / code-and-test verification
> 테스트 증거: `python -m pytest -q ...` 프론트/브리지 표적 묶음 `196 passed in 4.52s`

## Executive Summary

이번 전수조사의 결론은 다음과 같다.

- renderer action surface와 project/settings/work_guard wiring은 현재 코드 기준으로 생각보다 잘 닫혀 있다.
- 이전에 강하게 의심되던 `project root split`, `work_guard template 미구현`, `Frontier Lag 미연결`, `sanitization helper 부재`는 현재 코드와 표적 테스트 기준으로 기각됐다.
- 대신 retained finding은 `runtime bug`보다 `계약 drift`, `패키징 모델 불일치`, `shadow surface`, `회귀 신뢰도 부족`에 몰려 있다.
- 가장 강한 문제는 release artifact model이다.
  - 문서와 env는 `engine.exe / 소스 코드 비공개`를 말하지만,
  - 실제 build와 packaged resources는 `main_a.py + modules + config + embedded python` source bundle을 실어 나른다.
- 두 번째 문제는 Stage 0 external contract의 숨은 분기다.
  - UI는 `sub_key 1..7`로 고정했지만,
  - validator와 prompt-map은 여전히 `sub_key 0` interactive path를 허용한다.
- 세 번째 문제는 회귀망 신뢰도다.
  - 현재 많은 테스트가 source-string guard에 의존하고,
  - desktop 기본 `npm test`는 real-app bridge/risk/runtime-path 테스트를 포함하지 않는다.

최종 retained finding은 `P1 1건`, `P2 4건`, `P3 2건`이다. 읽기 전용 조사 + 표적 pytest 기준 확신도 상한은 `90%`다.

## 1. 조사 범위

이번 감사는 아래 6개 terminal을 전량 실행했다.

1. Renderer action surface
2. Project/settings/material surface
3. Electron shell / IPC / splash
4. Bridge / runner / backend contract
5. Packaging / runtime bundle / asset inventory
6. Regression trust / coverage closure

실행 산출물:

- [FGS-T1-renderer-action-surface-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/FGS-T1-renderer-action-surface-findings.md)
- [FGS-T2-project-settings-material-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/FGS-T2-project-settings-material-findings.md)
- [FGS-T3-shell-ipc-splash-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/FGS-T3-shell-ipc-splash-findings.md)
- [FGS-T4-bridge-runner-contract-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/FGS-T4-bridge-runner-contract-findings.md)
- [FGS-T5-packaging-bundle-asset-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/FGS-T5-packaging-bundle-asset-findings.md)
- [FGS-T6-regression-trust-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/FGS-T6-regression-trust-findings.md)

## 2. PASS 1 요약

- `T1`: renderer action map, Stage 0 submenu, Frontier Lag, sanitization, quality/safe-ops panel 조사
- `T2`: project/settings/work_guard/material/workspace surface 조사
- `T3`: shell, preload, splash, shadow main, temp Electron script 조사
- `T4`: bridge, runner, validator, prompt-map, Stage 0 submenu contract 조사
- `T5`: build_release, backend_entry, package extraResources, packaged resources inventory, `UI/` archive 조사
- `T6`: package test script, source-string regression, behavior-first bridge tests, uncovered surfaces 조사

PASS1 후보 총계는 `17건`이었다.

## 3. PASS 2 교차 검증

### 3.1 표적 pytest 실행

다음 묶음을 읽기 전용 근거층으로 실행했다.

```text
tests/test_run_validator.py
tests/test_api_contract.py
tests/test_frontend_frontier_lag_wiring.py
tests/test_frontend_stage0_connectivity.py
tests/test_ui_renderer_sanitization.py
tests/test_desktop_contract_refresh.py
tests/test_desktop_work_guard_template_contract.py
tests/test_process_runner_stage0_inputs.py
tests/test_bridge_server_http_contract.py
tests/test_bridge_server_desktop_risk_gate.py
tests/test_bridge_quality_summary.py
tests/test_runtime_paths.py
tests/test_process_runner.py
tests/test_project_support.py
tests/test_project_manager_hud_helpers.py
```

결과:

- `196 passed in 4.52s`

### 3.2 현재 코드가 닫은 항목

아래는 이번 감사에서 재확인 후 기각한 항목이다.

- Stage 0 `1..7` renderer label drift
- Frontier Lag renderer wiring 누락
- renderer sanitization helper 부재
- project settings surface와 runtime path 분리
- work_guard template bridge 미구현
- packaged project root split 지속
- `UI/` archive shipping hypothesis

즉, 현재 프론트 surface의 핵심 리스크는 “아예 안 붙어 있음”보다 “붙어 있지만 계약과 문서가 미세하게 갈라짐”에 가깝다.

## 4. PASS 3 확정 findings

### FGS-T3-001

- Severity: `P3`
- Claim: root-level `geuldobi-desktop/main.js` shadow copy가 live entry `src/main.js`와 드리프트했다.
- Direct evidence:
  - `geuldobi-desktop/package.json:5`
  - `geuldobi-desktop/src/main.js:619`, `:761`, `:774`
  - `geuldobi-desktop/main.js`에는 동일 IPC 구간 부재
- Counter-evidence review:
  - builder shipping pattern은 `src/**/*`만 포함한다.
  - 즉시 제품 버그는 아니지만 maintenance split-brain이다.
- Status: `confirmed`

### FGS-T4-001

- Severity: `P2`
- Claim: Stage 0 `sub_key 0` interactive path가 external contract에 남아 있지만 desktop UI와 frontend 회귀망은 `1..7`만 전제로 한다.
- Direct evidence:
  - `modules/api/run_validator.py:27`
  - `docs/implementation/prompt-map-v1.json:7`
  - `modules/core/stage01_helpers.py:403`
- Counter-evidence review:
  - live desktop bug는 아니다.
  - 그러나 hidden interactive branch를 validator와 문서가 계속 허용하는 split contract다.
- Status: `confirmed`

### FGS-T5-001

- Severity: `P1`
- Claim: release guide는 `engine.exe / 소스 코드 비공개`를 말하지만 실제 packaged artifact는 source-tree engine bundle이다.
- Direct evidence:
  - `geuldobi-desktop/package.json:39-56`
  - `build/build_release.ps1:27-64`, `:113-117`
  - `build/backend_entry.py:19-25`
  - `dist/engine/main_a.py` 실존
  - `geuldobi-desktop/dist/win-unpacked/resources/engine/main_a.py` 실존
  - `geuldobi-desktop/DESKTOP-GUIDE.md:4`, `:17`, `:24-25`
- Counter-evidence review:
  - 현재 빌드가 동작하는 것은 맞다.
  - 그러나 배포 모델, confidentiality 설명, artifact expectation이 더 이상 일치하지 않는다.
- Status: `confirmed`

### FGS-T5-002

- Severity: `P2`
- Claim: main process가 `resources/engine/engine.exe`를 env로 주입하지만 build는 그 파일을 만들지 않아 packaged launch가 항상 fallback 경로를 탄다.
- Direct evidence:
  - `geuldobi-desktop/src/main.js:167`
  - `modules/api/process_runner.py:190-196`
  - `build/build_release.ps1:27-64`
- Counter-evidence review:
  - `tests/test_process_runner.py`가 fallback path를 정상으로 잠가 기능적 붕괴는 막는다.
  - 그 대신 env/build/runtime semantics는 분열된 상태다.
- Status: `confirmed`

### FGS-T6-001

- Severity: `P2`
- Claim: desktop 기본 `npm test` 게이트가 real-app bridge/risk/runtime-path 검증을 포함하지 않아 green signal의 coverage가 좁다.
- Direct evidence:
  - `geuldobi-desktop/package.json:11`
  - `tests/test_desktop_contract_refresh.py:11-17`
- Counter-evidence review:
  - omitted 테스트들은 존재하고 수동 실행 시 통과한다.
  - 문제는 package-level default gate가 그것을 보지 않는 점이다.
- Status: `confirmed`

### FGS-T6-002

- Severity: `P2`
- Claim: splash lifecycle, material IPC, workspace path/open, offline mode는 live surface가 있으나 자동 테스트 증거가 없다.
- Direct evidence:
  - `geuldobi-desktop/src/splash/splash.js`
  - `geuldobi-desktop/src/preload.js:32-34`, `:52-53`
  - `geuldobi-desktop/src/main.js:511-572`, `:795-804`
  - `geuldobi-desktop/src/index.html:7737`
- Counter-evidence review:
  - 코드 surface는 존재하고 정적 읽기만으로 즉시 bug라고 단정할 수는 없다.
  - 다만 자동화 evidence layer에는 비어 있다.
- Status: `confirmed`

### FGS-T6-003

- Severity: `P3`
- Claim: 주요 프론트엔드 regression이 source-string assertion 비중이 높아 behavior drift를 놓칠 수 있다.
- Direct evidence:
  - `tests/test_frontend_stage0_connectivity.py`
  - `tests/test_ui_renderer_sanitization.py`
  - `tests/test_desktop_work_guard_template_contract.py`
  - `tests/test_desktop_contract_refresh.py`
- Counter-evidence review:
  - source-string guards는 빠르고 유용하다.
  - 다만 stateful renderer/IPC surface의 주 보호막으로는 약하다.
- Status: `confirmed`

## 5. 기각 findings

- Stage 0 `1..7` renderer/menu parity broken
- Frontier Lag not wired
- work_guard template bridge missing
- project root split still open
- `UI/` archive is live runtime dependency
- dynamic HTML sanitization absent

## 6. bucket coverage 표

| Bucket | 결과 | 비고 |
|-------|------|------|
| Renderer action surface | `closed-without-retained-finding` | sanitization, Stage 0, Frontier Lag 현재 일치 |
| Project/settings/material | `closed-without-retained-finding` | runtime path/wiring 현재 일치 |
| Shell / preload / splash | `retained` | shadow main divergence |
| Bridge / runner / backend contract | `retained` | Stage 0 hidden `sub_key 0` |
| Packaging / bundle / assets | `retained` | source bundle vs engine.exe contract drift |
| Regression trust | `retained` | default gate 범위 부족 + behavior test 공백 |

## 7. 확신도 ledger

- 시작점: `70`
- T1~T6 전량 인벤토리 완료: `+10`
- 코드/문서/파일시스템 2중 근거 확보: `+5`
- 표적 pytest 196건 green: `+10`
- 오탐 제거 완료: `+5`
- live Electron, packaged installer, splash/material/manual flow 미검증: `-10`

최종 확신도 상한: `90%`

## 8. 결론

현재 프론트엔드 전역 상태는 “renderer 자체가 무너진 상태”는 아니다. 오히려 renderer/bridge/project settings wiring은 꽤 잘 잠겨 있다. 문제는 프론트엔드와 패키징이 외부에 약속하는 계약이 코드와 조금씩 갈라져 있다는 점이다. 우선순위는 명확하다.

1. packaging artifact model을 문서와 코드 중 하나에 맞춰 단일화
2. Stage 0 external contract에서 `sub_key 0` 정리
3. desktop 기본 test gate에 real-app bridge/risk/runtime-path 계열 편입
4. splash/material/workspace/offline behavior-first coverage 추가
5. shadow `geuldobi-desktop/main.js` 정리

이번 턴은 조사와 문서화까지만 수행했다. 코드 수정은 하지 않았다.
