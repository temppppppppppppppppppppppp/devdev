# FBX-T6 Regression / Docs / Confidence Findings

> 작성일: 2026-03-13
> 상태: `completed`
> 범위: 관련 pytest, `README.md`, `geuldobi-desktop/DESKTOP-GUIDE.md`, remediation docs
> 방법: `gate inventory + runtime proof + 3PASS`

## 결론

- retained `P0`: 0건
- retained `P1`: 0건
- retained `P2`: 1건
- runtime proof: `npm --prefix geuldobi-desktop run start:spike` 성공
- 핵심 결론: 조사용 확장 회귀는 녹색이지만, package script의 공식 desktop gate는 live bridge/dashboard/risk coverage를 충분히 포함하지 않는다.

## PASS 1

- `package.json`의 공식 desktop test script는 아래만 포함한다.
  - `test_run_validator.py`
  - `test_api_contract.py`
  - `test_frontend_frontier_lag_wiring.py`
  - `test_frontend_stage0_connectivity.py`
  - `test_ui_renderer_sanitization.py`
  - `test_desktop_contract_refresh.py`
  - `test_desktop_work_guard_template_contract.py`
  - `test_process_runner_stage0_inputs.py`
- 이번 조사에서 추가로 고정한 회귀는 아래 3개다.
  - `tests/test_bridge_server_http_contract.py`
  - `tests/test_bridge_server_desktop_risk_gate.py`
  - `tests/test_bridge_quality_summary.py`

## PASS 2

- 확장 회귀군 실행 결과: `151 passed in 3.48s`
- runtime proof 실행 결과:
  - splash 표시
  - backend uvicorn 기동
  - `/status` 200
  - `WS /events` accepted
  - 5초 후 자동 종료
- `README.md`는 CLI 중심 개요를 제공하고, `DESKTOP-GUIDE.md`는 packaged desktop 동작을 설명하지만, 공식 `npm test` 범위는 bridge/dashboard/risk read path를 직접 포함하지 않는다.

## PASS 3

### [FBX-T6-001] Official desktop test gate under-covers live bridge/dashboard/risk surfaces

- **Severity**: `P2`
- **현상**: package script의 `npm test`가 bridge HTTP contract, desktop risk gate, quality dashboard/read-only payload 회귀를 포함하지 않는다.
- **코드 근거**:
  - `geuldobi-desktop/package.json:11`
  - 존재하는 but omitted tests:
    - `tests/test_bridge_server_http_contract.py`
    - `tests/test_bridge_server_desktop_risk_gate.py`
    - `tests/test_bridge_quality_summary.py`
- **사용자/운영 영향**: desktop package gate만 녹색이어도 live bridge/dashboard/risk surface는 regression을 놓칠 수 있다.
- **테스트 근거**:
  - 이번 조사에서 누락 3개를 추가 실행했고 `151 passed`를 확인했다.
  - `npm --prefix geuldobi-desktop run start:spike`도 성공했다.
- **중복 여부**: `none`
- **권장 후속 조치**: 이후 remediation 단계에서 desktop package test script 또는 동등한 CI gate에 omitted bridge 회귀를 포함한다.

## Retained Open Set

- `P2`: `FBX-T6-001`

## Resume Packet

- `Current phase`: `FBX-T6 completed`
- `Last completed pass`: `PASS 3`
- `Last completed surface`: `official gate vs expanded gate`
- `Next surface`: `consolidated findings`
- `Reopen reason codes used`: `none`
- `Stop gate or blocker`: `none`
