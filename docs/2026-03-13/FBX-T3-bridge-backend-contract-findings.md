# FBX-T3 Bridge Backend Contract Findings

> 작성일: 2026-03-13
> 상태: `completed`
> 범위: `modules/api/bridge_server.py`, `modules/api/run_validator.py`, `modules/api/risk_approval.py`, `docs/implementation/api-contract-v1.yaml`
> 방법: `route inventory + contract cross-check + 3PASS`

## 결론

- retained `P0`: 0건
- retained `P1`: 0건
- retained `P2`: 1건
- 핵심 결론: HTTP endpoints와 risk gate는 대체로 문서와 맞지만, live websocket surface는 계약 문서 밖에 남아 있다.

## PASS 1

- backend live surface:
  - `POST /run`
  - `POST /run/{run_id}/input`
  - `POST /stop`
  - `GET /status`
  - `GET /quality/summary`
  - `GET /quality/dashboard`
  - `GET /safe-ops/preview`
  - `POST /quality/review`
  - `WS /events`
- `run_endpoint()`는 `validate_run_request()`와 `RiskApprovalGate.validate()`를 거쳐 `ProcessRunner.start()`로 이어진다.
- quality/safe-ops endpoints는 read-only 집계이며 `quality_review_endpoint()`만 write path다.

## PASS 2

- `tests/test_bridge_server_http_contract.py`는 `/run`, `/status`의 기본 envelope을 검증한다.
- `tests/test_bridge_server_desktop_risk_gate.py`는 desktop mode risk key의 `approval_id` 강제를 검증한다.
- `tests/test_bridge_quality_summary.py`는 quality/safe-ops/read-only aggregation과 review write를 검증한다.
- `docs/implementation/api-contract-v1.yaml`는 HTTP endpoints를 문서화하지만, websocket `/events` surface는 포함하지 않는다.

## PASS 3

### [FBX-T3-001] Live websocket `/events` surface is outside the formal API contract

- **Severity**: `P2`
- **현상**: renderer는 websocket `/events`를 live로 사용하고 backend도 이를 제공하지만, 공식 API contract에는 해당 surface와 event envelope가 없다.
- **코드 근거**:
  - `modules/api/bridge_server.py:1527`
  - `geuldobi-desktop/src/index.html:5972-5973`
  - `docs/implementation/api-contract-v1.yaml`에는 `/events` path 부재
- **사용자/운영 영향**: live event schema drift가 문서형 계약 바깥에서 일어나면 UI/ops가 contract green 상태로 남아도 runtime stream이 깨질 수 있다.
- **테스트 근거**:
  - `rg -n "events|websocket|run_started|run_completed|run_failed|run_stopped" tests -g "*.py"` 결과 websocket contract용 전용 회귀 부재
  - existing tests는 HTTP endpoints 위주다.
- **중복 여부**: `none`
- **권장 후속 조치**: 다음 문서화 단계에서 websocket event schema와 `/events`를 별도 desktop bridge contract로 승격한다.

## Retained Open Set

- `P2`: `FBX-T3-001`

## Resume Packet

- `Current phase`: `FBX-T3 completed`
- `Last completed pass`: `PASS 3`
- `Last completed surface`: `backend route + api contract cross-check`
- `Next surface`: `FBX-T4 process runner / engine handoff`
- `Reopen reason codes used`: `none`
- `Stop gate or blocker`: `none`
