# GDFS T4 UI / API / Desktop / Operator Surface Findings

작성일: 2026-03-13
상태: `PASS3 complete`
범위: `modules/api/bridge_server.py`, `modules/core/runtime_paths.py`, `modules/core/project_support.py`, `modules/core/quality_sidecar_bootstrap.py`, `docs/implementation/api-contract-v1.yaml`, `geuldobi-desktop/src/*`, `main.js`, 관련 계약 테스트
조사 모드: `read-only`, `operator-surface cross-check`, `UTF-8 only`

## Executive Summary

- old API contract 누락과 desktop risk approval bypass는 현재 코드와 테스트 기준으로 닫혔다.
- 하지만 operator-facing surface에는 아직 세 가지 retained drift가 남아 있다.
  - quality/safe-ops contract가 `project`를 optional로 문서화하지만 runtime은 non-empty project를 강제한다.
  - live websocket `/events` surface는 여전히 formal contract 바깥에 있다.
  - support/quality surface는 아직 `effective_pov`가 아니라 raw `pov`를 기본 표시값으로 쓴다.

## PASS 1 - 후보 수집

- 후보 A: old API contract가 `/quality/*`, `/safe-ops/*`, error code, port를 누락한다
- 후보 B: desktop risk key path가 `approval_id`를 우회한다
- 후보 C: `project` query requiredness가 문서와 runtime에서 다르다
- 후보 D: websocket `/events`가 live surface인데 contract/test gate 밖에 있다
- 후보 E: operator support detail이 raw POV만 노출한다

## PASS 2 - 교차 검증

### 제거 1. old API contract surface omission

- `docs/implementation/api-contract-v1.yaml`는 현재 `8300`, `/quality/summary`, `/quality/dashboard`, `/safe-ops/preview`, `/quality/review`, documented error codes를 모두 포함한다.
- `tests/test_api_contract.py:541-567`도 endpoint set, error code enum, status enum을 잠근다.
- 판정: `live-code-changed`로 닫힘.

### 제거 2. desktop risk approval bypass

- `geuldobi-desktop/src/preload.js:10-11`은 `approvalId`를 preload surface에 노출한다.
- `geuldobi-desktop/src/main.js:395-400`은 `approval_id`를 backend `/run` body로 전달한다.
- `modules/api/bridge_server.py:1283-1294`는 desktop mode에서도 valid `approval_id`를 요구한다.
- `tests/test_bridge_server_desktop_risk_gate.py:48-76`은 누락 시 `403 RISK_APPROVAL_REQUIRED`, valid approval 시 `202 OK`를 검증한다.
- 판정: `live-code-changed`로 닫힘.

## PASS 3 - 최종 확정 Findings

### [GDFS-T4-001] API contract는 optional project를 광고하지만 runtime은 required project를 강제한다

- Severity: `P1`
- 현상 요약:
  - `/quality/summary`, `/quality/dashboard`, `/safe-ops/preview`의 contract는 `project` query를 optional로 적는다.
  - 그러나 runtime은 blank project를 `INVALID_PROJECT`로 reject한다.
- 코드 근거:
  - `docs/implementation/api-contract-v1.yaml:111,146,181`
  - `modules/core/runtime_paths.py:30-34`
  - `modules/api/bridge_server.py:180-186`
  - `modules/api/bridge_server.py:1434-1469`
  - `tests/test_bridge_quality_summary.py:59-64`
- downstream 영향 경계:
  - operator-facing OpenAPI/document contract
  - desktop bridge caller
  - automated client or future SDK generation
- 현재 테스트 근거 또는 테스트 부재:
  - `tests/test_bridge_quality_summary.py:59-64`는 summary endpoint만 missing project reject를 잠근다.
  - `tests/test_api_contract.py:541-567`는 path 존재만 보며 requiredness를 잠그지 않는다.
  - dashboard/safe-ops missing-project rejection을 고정하는 회귀는 없다.
- baseline과의 관계:
  - `related-but-new-operator-contract-surface`
- 권장 후속 조치:
  - contract에서 세 endpoint의 `project`를 required로 승격한다.
  - contract regression에 requiredness assert를 추가한다.
  - dashboard/safe-ops missing-project reject regression을 별도로 추가한다.

### [GDFS-T4-002] live websocket `/events` surface는 여전히 formal API contract 밖에 있다

- Severity: `P2`
- 현상 요약:
  - backend와 desktop은 `/events` websocket을 실제로 사용하지만, 공식 contract와 contract test gate에는 해당 surface가 없다.
- 코드 근거:
  - `modules/api/bridge_server.py:1527`
  - `geuldobi-desktop/src/main.js:414`
  - `main.js:331`
  - `docs/implementation/api-contract-v1.yaml`에는 `/events` path 부재
  - `tests/test_api_contract.py:541-567`
- downstream 영향 경계:
  - renderer live event stream
  - desktop 운영 관측
  - backend/frontend contract freeze
- 현재 테스트 근거 또는 테스트 부재:
  - websocket `/events` path나 event envelope를 검증하는 전용 contract regression이 없다.
  - existing contract tests는 HTTP path subset만 확인한다.
- baseline과의 관계:
  - `related-but-retained`
  - 기존 `FBX-T3-001`과 같은 root cause이며 현재 코드 기준으로도 남아 있다.
- 권장 후속 조치:
  - `/events`를 formal contract 또는 별도 desktop live-event spec으로 승격한다.
  - event type/payload 최소 schema를 regression gate에 넣는다.

### [GDFS-T4-003] operator support surface는 아직 raw POV를 기본값으로 노출한다

- Severity: `P2`
- 현상 요약:
  - project support payload는 `effective_pov`를 계산하지만, bridge detail과 quality sidecar health는 아직 raw `pov`를 대표값으로 쓴다.
  - 따라서 runtime은 Bible 보정 POV로 동작해도 operator detail은 stale file POV를 보여 줄 수 있다.
- 코드 근거:
  - `modules/core/project_support.py:288-317`
  - `modules/api/bridge_server.py:523-536`
  - `modules/core/quality_sidecar_bootstrap.py:152-157`
  - `tests/test_project_support.py:80,119`
  - `tests/test_quality_sidecar_bootstrap.py`
- downstream 영향 경계:
  - bridge status/detail
  - quality sidecar health payload
  - operator support readiness view
- 현재 테스트 근거 또는 테스트 부재:
  - `tests/test_project_support.py`는 `effective_pov` 계산만 잠근다.
  - `tests/test_quality_sidecar_bootstrap.py`는 `style_pov`의 semantic correctness를 잠그지 않는다.
  - bridge detail 문자열이 raw POV 대신 effective POV를 쓰는지 확인하는 회귀가 없다.
- baseline과의 관계:
  - `related-but-retained`
  - 기존 `ROP-T4-002`를 current operator surface 기준으로 재확인했다.
- 권장 후속 조치:
  - bridge/quality support surface의 기본 표시값을 `effective_pov`로 바꾼다.
  - raw file POV를 유지해야 하면 label을 `raw_style_pov`로 분리한다.
  - stale file POV vs Bible POV mismatch regression을 operator surface까지 확장한다.

## PASS 요약

- PASS1 후보: `5`
- PASS2 제거: `2`
  - old API contract omission
  - desktop risk approval bypass
- PASS3 확정: `3`
  - `GDFS-T4-001`
  - `GDFS-T4-002`
  - `GDFS-T4-003`

## Resume Packet

- `Current phase`: `T4 completed`
- `Last completed pass`: `PASS 3`
- `Last completed surface`: `quality/safe-ops/API contract + desktop operator surface`
- `Next surface`: `T5 test / canary / runtime proof`
- `Reopen reason codes used`: `live-code-changed`, `operator-surface-mismatch`
- `Stop gate or blocker`: `none`
