# Frontend-Backend Global Remediation Execution SSOT

> 작성일: 2026-03-13
> 상태: `execution-ready`
> 확신도 목표: `95%`
> 기준 조사:
> - `frontend-backend-global-consolidated-findings.md`
> - `frontend-backend-global-consolidated-findings-3pass-reaudit.md`
> 문서 역할: 전역 전수조사 retained open set을 `실행 단위`, `순서`, `acceptance`, `gate`로 다시 잠그는 remediation 실행 오더

## Executive Summary

- 이번 실행 범위는 survey retained set `P2 6건`, `P3 1건`을 중복 없는 remediation unit `5개`로 재배열하는 것이다.
- 목표는 `renderer direct surface ownership`, `desktop bridge/live-event contract`, `packaged runtime artifact contract`, `stale/dead surface hygiene`, `official desktop gate`를 다시 같은 SSOT로 맞추는 것이다.
- 현재 기준 `P0`, `P1`은 없다. 따라서 이번 오더는 emergency patch가 아니라 contract/test/build drift 정렬용 실행 문서다.
- 권장 실행 순서는 `FBX-E1 -> FBX-E2 -> FBX-E3 -> FBX-E4 -> FBX-E5`다.
- 이번 턴의 산출물은 문서뿐이며, 실제 코드 수정은 이 SSOT를 기준으로 한 후속 execution 턴에서만 수행한다.

## Scope

포함:
- `geuldobi-desktop/src/index.html`
- `geuldobi-desktop/src/splash/splash.js`
- `geuldobi-desktop/src/preload.js`
- `geuldobi-desktop/src/main.js`
- `modules/api/bridge_server.py`
- `docs/implementation/api-contract-v1.yaml`
- `geuldobi-desktop/package.json`
- `build/build_release.ps1`
- `build/backend_entry.py`
- `geuldobi-desktop/main.js`
- `geuldobi-desktop/DESKTOP-GUIDE.md`
- desktop/bridge 관련 focused pytest 및 package gate

제외:
- renderer monolith 전면 분해
- CSP strict mode 전환
- Stage 2~4 생성 로직 변경
- unrelated backend feature 추가
- installer 제작, version bump, release publishing

## Baseline Retained Set -> Execution Unit Mapping

| Finding | Severity | Execution Unit | 실행 의미 |
|---------|----------|----------------|-----------|
| `FBX-T1-001` | `P2` | `FBX-E1` | direct network ownership allowlist |
| `FBX-T2-001` | `P2` | `FBX-E2` | desktop transport error contract |
| `FBX-T3-001` | `P2` | `FBX-E2` | live websocket contract/regression |
| `FBX-T5-001` | `P2` | `FBX-E3` | packaged artifact contract normalization |
| `FBX-T5-002` | `P2` | `FBX-E4` | stale root entry containment |
| `FBX-T6-001` | `P2` | `FBX-E5` | official desktop gate expansion |
| `FBX-T2-002` | `P3` | `FBX-E4` | dead-candidate IPC inventory split |

## Public Contracts To Preserve

- `window.geuldobiDesktop.*`의 live run/quality/project/material/work_guard surface는 유지한다.
- `POST /run`, `POST /stop`, `GET /status`, `POST /run/{run_id}/input`, `GET /quality/summary`, `GET /quality/dashboard`, `GET /safe-ops/preview`, `POST /quality/review`의 backend route는 유지한다.
- renderer가 실제로 쓰는 direct surface는 `splash /status`, `WS /events`, `Google API key validation fetch`를 출발점으로 삼는다.
- dev spike와 expanded pytest gate는 remediation 후에도 유지한다.

## Execution Units

### FBX-E1. Renderer Direct Surface Ownership SSOT

목표:
- renderer가 직접 소유하는 network surface를 `approved direct`와 `bridge-managed`로 명시 분리한다.

작업:
- direct `fetch`/`WebSocket` allowlist를 문서와 focused regression으로 고정한다.
- `connect-src`와 실제 live allowlist가 어긋나지 않도록 정렬한다.
- operator-facing connectivity 문서에 direct ownership surface를 별도 표로 유지한다.

비포함:
- direct surface를 전부 preload로 강제 이전하는 구조 개편
- renderer DOM 구조 리팩터

acceptance:
- unclassified direct network surface가 없다.
- direct surface는 owner, 목적, 허용 이유, 회귀 근거를 가진다.

### FBX-E2. Desktop Bridge Transport + Websocket Contract Normalization

목표:
- Electron main transport error namespace와 backend API contract, live websocket `/events` schema를 함께 문서화하고 회귀로 고정한다.

기본 방향:
- backend enum에 transport failure를 억지로 섞기보다, `desktop bridge contract`를 별도 층으로 명시하는 쪽을 기본값으로 둔다.

작업:
- `bridgeFetch()`의 `HTTP_*`, `NETWORK_ERROR` code space를 SSOT 문서와 테스트로 고정한다.
- `/events` websocket event 종류와 필수 payload 필드를 계약 문서 또는 별도 desktop live-event spec에 올린다.
- focused regression에 main-process transport mapping과 websocket schema 검증을 추가한다.

비포함:
- backend route 재설계
- websocket stream을 HTTP polling으로 교체하는 변경

acceptance:
- renderer/operator 문서가 transport failure code space를 정확히 설명한다.
- `/events`는 contract와 regression gate 안에 들어온다.
- UI가 받는 desktop error namespace와 backend error namespace의 경계가 명시된다.

### FBX-E3. Packaged Runtime Artifact Contract Normalization

목표:
- packaged runtime이 `engine.exe`를 primary로 쓰는지, source-tree engine bundle fallback을 primary로 쓰는지 하나의 계약으로 통일한다.

기본 방향:
- release policy가 실제 `engine.exe` 산출을 요구하지 않는 한, 우선순위는 `현실 artifact topology에 맞춘 문서/env/test 정렬`에 둔다.

작업:
- `src/main.js`, `build_release.ps1`, `backend_entry.py`, `DESKTOP-GUIDE.md`가 같은 artifact 계약을 바라보게 정렬한다.
- build verification에 artifact presence 또는 fallback contract 검증을 추가한다.
- `engine.exe-first`와 `fallback-first` 중 실제 채택 경로를 하나로 확정한다.

비포함:
- Windows installer 제작
- backend/engine 배포 파이프라인 전면 재설계

acceptance:
- packaged guide와 실제 artifact 구성이 서로 모순되지 않는다.
- release diagnostics가 존재하지 않는 `engine.exe`를 전제하지 않는다.
- build/test 문서에서 packaged runtime primary path가 단일 의미로 설명된다.

### FBX-E4. Stale Root Entry + Dead IPC Containment

목표:
- active가 아닌 root `geuldobi-desktop/main.js`와 dead-candidate IPC surface를 `live surface`와 섞이지 않게 고정한다.

작업:
- root `geuldobi-desktop/main.js`를 `dead/stale/high-risk drift source` 중 명시 상태로 분류하고 개발자 문서에 반영한다.
- 가능하면 stale copy 자체를 제거하거나, 제거하지 못하면 강한 warning/guard를 둔다.
- `getStatus()`, `getWorkspacePath()` 등 dead-candidate IPC를 live inventory와 분리한 문서/테스트 규칙을 둔다.

비포함:
- preload surface 전면 축소
- main process 전체 구조 재배치

acceptance:
- active entry가 `src/main.js`임을 오해할 여지가 없다.
- stale root copy에 대한 drift 재주입 가능성이 줄어든다.
- live IPC 목록과 dead-candidate 목록이 분리된다.

### FBX-E5. Official Desktop Gate Expansion

목표:
- 공식 `npm test` 또는 동등 CI gate가 실제 live bridge/dashboard/risk/package surface를 충분히 덮도록 확장한다.

작업:
- 최소 포함 세트를 `test_bridge_server_http_contract.py`, `test_bridge_server_desktop_risk_gate.py`, `test_bridge_quality_summary.py`까지 올린다.
- `FBX-E1`, `FBX-E2`, `FBX-E3`, `FBX-E4`에서 추가되는 focused regression을 official gate에 편입한다.
- release checklist에 `start:spike` runtime proof를 유지한다.

비포함:
- 모든 테스트를 단일 mega script로 합치는 재구조화
- unrelated slow end-to-end suite 추가

acceptance:
- official desktop gate가 현재 live surface를 false green 없이 대표한다.
- package/CI 문서가 실제 release confidence와 같은 범위를 본다.

## Recommended Execution Order

1. `FBX-E1`
- direct surface owner/allowlist를 먼저 고정해야 이후 bridge/ws contract 경계가 흔들리지 않는다.

2. `FBX-E2`
- desktop transport namespace와 websocket contract를 정리해야 gate 확장 범위가 정확해진다.

3. `FBX-E3`
- package/runtime artifact 의미를 하나로 정해야 guide와 release diagnostics가 안정된다.

4. `FBX-E4`
- stale/dead surface 정리는 active contract가 정해진 뒤 수행하는 편이 안전하다.

5. `FBX-E5`
- 마지막에 official gate를 넓혀야 새 contract와 artifact semantics를 한 번에 잠글 수 있다.

## Verification Plan

- focused pytest
  - `tests/test_bridge_server_http_contract.py`
  - `tests/test_bridge_server_desktop_risk_gate.py`
  - `tests/test_bridge_quality_summary.py`
  - `tests/test_desktop_contract_refresh.py`
  - `tests/test_desktop_work_guard_template_contract.py`
  - plus `FBX-E1~E4` 신규 focused regression
- package gate
  - `npm --prefix geuldobi-desktop test`
- runtime proof
  - `npm --prefix geuldobi-desktop run start:spike`
- static inventory
  - `rg`로 direct `fetch`, `WebSocket`, preload surface, `ipcMain.handle/on`, route inventory 재검증

## Exit Criteria

1. direct network ownership과 bridge-managed ownership이 문서/테스트에서 분리 고정된다.
2. desktop transport error namespace와 websocket `/events` contract가 명시된다.
3. packaged runtime artifact 설명과 실제 staging 결과가 같은 의미를 가진다.
4. stale root entry와 dead-candidate IPC가 live path와 분리된다.
5. official desktop gate가 live bridge/dashboard/risk/package surface를 대표한다.
6. remediation 후 postfix 3PASS에서 unresolved `P1` 0건, 목표 confidence `95%`를 방어한다.

## Compaction / Resume Packet

- `Current phase`: `remediation execution order authored`
- `Last completed pass`: `execution SSOT draft complete`
- `Last completed surface`: `retained set -> execution unit mapping`
- `Next surface`: `frontend-backend-global-remediation-3pass-audit.md`
- `Reopen reason codes used`: `none`
- `Stop gate or blocker`: `implementation not started`
