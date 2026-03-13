# UI Codebase Health Remediation Execution SSOT

작성일: 2026-03-13  
상태: `execution-ready`

## Executive Summary

- 기준 문서: [ui-codebase-health-full-survey-3pass-final-audit.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/ui-codebase-health-full-survey-3pass-final-audit.md)
- 이번 오더는 retained finding `3건`만 닫는다.
- 범위:
  - `key 7` UI-bridge dead path 제거
  - renderer `innerHTML` 동적 주입면 sanitization
  - desktop test/docs gate 최신화
- 금지:
  - 새 기능 추가
  - UI 레이아웃 개편
  - Electron security model 전면 재설계
  - build/version bump

## Remediation Scope

### E-1. `Frontier Lag key 7` contract alignment

대상:
- [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html)
- [run_validator.py](C:/Users/User/Desktop/글도비/modules/api/run_validator.py)
- [api-contract-v1.yaml](C:/Users/User/Desktop/글도비/docs/implementation/api-contract-v1.yaml)
- [prompt-map-v1.json](C:/Users/User/Desktop/글도비/docs/implementation/prompt-map-v1.json)
- [test_run_validator.py](C:/Users/User/Desktop/글도비/tests/test_run_validator.py)
- [test_api_contract.py](C:/Users/User/Desktop/글도비/tests/test_api_contract.py)

수정 목표:
- UI에 노출된 `key 7`을 backend validator와 계약 문서가 동일하게 허용한다.
- `6` 기존 동작은 보존한다.
- stale test가 `7`을 invalid로 고정하는 상태를 제거한다.

완료 기준:
- `/run` validator가 `key 7`을 `202 OK`로 받는다.
- API contract와 prompt map이 `7`을 포함한다.
- 관련 테스트가 `7`을 valid path로 검증한다.

### E-2. renderer sanitization hardening

대상:
- [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html)

수정 목표:
- backend/DB/user/file-name 유래 문자열이 `innerHTML`로 들어가는 지점에 escape helper를 강제한다.
- 정적 HTML skeleton과 내부 생성 SVG는 유지하되, 동적 문자열만 escaping한다.
- `unsafe-inline` CSP 자체는 이번 범위에서 유지하되, injection surface를 닫는다.

완료 기준:
- retained report가 지목한 `innerHTML` 동적 주입면에 공통 escape helper가 적용된다.
- raw payload가 HTML로 해석되지 않고 text로 렌더링된다.
- quality/office/project surface 기존 렌더링은 유지된다.

### E-3. desktop gate refresh

대상:
- [package.json](C:/Users/User/Desktop/글도비/geuldobi-desktop/package.json)
- [test_frontend_frontier_lag_wiring.py](C:/Users/User/Desktop/글도비/tests/test_frontend_frontier_lag_wiring.py)
- [test_run_validator.py](C:/Users/User/Desktop/글도비/tests/test_run_validator.py)
- [test_api_contract.py](C:/Users/User/Desktop/글도비/tests/test_api_contract.py)
- 필요 시 새 focused test

수정 목표:
- desktop package 자체의 `test` script가 실제 gate 역할을 하게 만든다.
- UI surface와 validator/API contract drift가 같은 suite 안에서 같이 잡히게 만든다.

완료 기준:
- `geuldobi-desktop/package.json`의 `test` script가 실질적인 focused regression을 실행한다.
- `key 7` 계약과 sanitization regression이 테스트로 고정된다.

## Non-Goals

- CSP에서 inline script 제거
- renderer monolith 분해
- packaged runtime/build contract 재개편
- Safe Ops, Quality Radar, Office UX 재설계

## Implementation Order

1. `E-1` contract alignment
2. `E-2` sanitization helper 도입과 동적 surface 적용
3. `E-3` desktop gate refresh
4. focused regression
5. Electron desktop spike
6. post-fix 3-pass re-audit

## Test Plan

- `python -m pytest -q tests/test_run_validator.py tests/test_api_contract.py tests/test_frontend_frontier_lag_wiring.py`
- sanitization 전용 test가 추가되면 같은 focused set에 포함
- `npm run start:spike` in [geuldobi-desktop](C:/Users/User/Desktop/글도비/geuldobi-desktop)

필수 확인:
- `validate_run_request("7", None, "idle") -> OK`
- API contract/prompt map/test가 모두 `7`을 일치되게 표현
- HTML-like payload가 renderer에서 escaped text로 남음
- desktop spike에서 splash -> backend -> main window -> `/status` -> `/quality/dashboard`가 유지됨

## Risks

- sanitization 범위를 과도하게 넓히면 SVG/정적 markup까지 깨질 수 있다.
- `package.json` test script를 잘못 묶으면 Windows 경로/working directory 문제가 생길 수 있다.
- stale doc/test를 일부만 고치면 `green but misleading` 상태가 계속 남는다.

## Final Exit Criteria

- retained `P1/P2`가 모두 닫힌다.
- focused regression green
- desktop spike green
- post-fix 3-pass 재감리에서 새 `P0/P1/P2` 없음
