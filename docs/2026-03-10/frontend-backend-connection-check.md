# 프론트엔드-백엔드 연결 체크 기준선

> 상태: 체크 문서 작성 완료
> 인코딩: UTF-8
> 목적: `TF-MULTI-LLM-provider-transition-spec.md` 진행 전/후로 Electron UI와 FastAPI 브리지 연결 상태를 같은 기준으로 점검하기 위한 기준선 문서
> 코드 수정: 없음

## 범위

- 프론트엔드: Electron desktop shell
  - `geuldobi-desktop/src/main.js`
  - `geuldobi-desktop/src/preload.js`
  - `geuldobi-desktop/src/index.html`
- 백엔드: FastAPI bridge + subprocess runner
  - `modules/api/bridge_server.py`
  - `modules/api/process_runner.py`
  - `modules/api/prompt_broker.py`

## 현재 정적 기준선

### 연결 구조

1. Electron main process가 `uvicorn modules.api.bridge_server:app --port 8300`을 자동 기동한다.
2. Renderer는 preload를 통해 직접 Node 접근 없이 IPC로만 bridge를 호출한다.
3. Electron main process가 HTTP 요청을 `http://127.0.0.1:8300`으로 프록시한다.
4. Renderer는 WebSocket만 직접 `ws://127.0.0.1:8300/events`에 연결한다.
5. FastAPI bridge는 `/run`, `/stop`, `/status`, `/events`, `/run/{run_id}/input`를 제공한다.
6. 예외적으로 renderer는 설정 화면의 API key 테스트에서 Google endpoint로 직접 `fetch()`를 호출한다. 이 경로는 bridge 경로와 분리해서 봐야 한다.

### 포트 / URL SSOT

| 항목 | 값 | 근거 |
|---|---|---|
| HTTP base URL | `http://127.0.0.1:8300` | `geuldobi-desktop/src/main.js` |
| WS URL | `ws://127.0.0.1:8300/events` | `geuldobi-desktop/src/main.js`, `preload.js` |
| CSP connect-src | `http://127.0.0.1:8300 ws://127.0.0.1:8300` 허용 | `geuldobi-desktop/src/index.html` |
| Backend app | `modules.api.bridge_server:app` | `geuldobi-desktop/src/main.js` |

### 프론트 노출 API

`window.geuldobiDesktop` 기준:

- `runKey(key, subKey, inputs)`
- `stopRun()`
- `getStatus()`
- `getBackendUrl()`
- `resolvePrompt(runId, promptId, value)`
- `saveSettings()`, `loadSettings()`
- `listProjects()`, `createProject()`
- `listMaterialFiles()`, `importMaterialFile()`, `deleteMaterialFile()`
- `openWorkspaceFolder()`, `getWorkspacePath()`

### 백엔드 핵심 엔드포인트

| 메서드 | 경로 | 용도 |
|---|---|---|
| `POST` | `/run` | 메뉴 키 실행 시작 |
| `POST` | `/stop` | 실행 중단 |
| `GET` | `/status` | runner 상태 조회 |
| `WS` | `/events` | 실행 이벤트 스트림 |
| `POST` | `/run/{run_id}/input` | Mode B 프롬프트 응답 |

### Mode B 상호작용 범위

`ProcessRunner.MODE_B_KEYS`:

- `0`, `1`, `2`, `3`, `4`, `5`, `6`, `44`, `77`, `88`, `99`

즉 현재는 거의 전체 메뉴가 prompt broker 경로를 탈 수 있다고 보고 체크해야 한다.

## 정적 판정

- 포트, URL, CSP, IPC, FastAPI route 표면 사이에 현재 정적 불일치는 보이지 않는다.
- 현재 리스크는 구조 mismatch보다 `런타임 기동`, `WS 이벤트 수신`, `Mode B prompt 왕복`, `중단 처리` 같은 동작 면에 있다.

## 점검 체크리스트

### A. 변경 전 기준선 체크

1. Electron 실행 시 splash가 뜨고 backend auto-start가 시작되는지 확인
2. backend ready 이후 main window로 정상 전환되는지 확인
3. `getStatus()` 또는 `GET /status`가 `idle` 또는 실행 중 상태를 정상 반환하는지 확인
4. Renderer가 `getBackendUrl()`로 받은 WS URL에 연결 가능한지 확인
5. `POST /run`이 `202 Accepted`와 `run_id`를 반환하는지 확인
6. `/events`에서 `run_started`, `stdout`, `run_completed` 또는 `run_failed`를 수신하는지 확인
7. Mode B prompt가 발생할 때 `prompt_request -> /run/{run_id}/input -> prompt_resolved` 왕복이 되는지 확인
8. `POST /stop`이 멱등적으로 동작하는지 확인
9. 프로젝트 목록/생성 IPC가 Electron main을 통해 정상 작동하는지 확인
10. workspace path/open-folder, material file 관리 IPC가 정상 작동하는지 확인

### B. MULTI-LLM 이후 재체크

1. `/run` request body 변경이 Renderer/Electron main/bridge_server 세 층에서 동시에 반영됐는지 확인
2. provider/model 설정 저장 위치가 renderer 설정값과 backend 실행값 사이에서 어긋나지 않는지 확인
3. `/events` payload schema가 기존 UI 파서와 호환되는지 확인
4. prompt broker가 provider 전환 후에도 timeout/default/resolved 동작을 유지하는지 확인
5. stop/restart 시 이전 provider 세션 상태가 다음 실행에 누수되지 않는지 확인
6. renderer의 direct external fetch(API key 테스트)와 CSP `connect-src`가 provider 전환 후에도 깨지지 않는지 확인

## 실행 순서

### 1차 체크

- 목적: 구조 변경 전 기준선 확보
- 최소 확인:
  - app launch
  - `/status`
  - `/run`
  - `/events`
  - `/stop`
  - Mode B 1회

### 주의 메모

- 위험키(`44`, `77`, `88`, `99`)는 desktop mode에서 `approval_id` 없이 자동 승인될 수 있다.
- 따라서 현재 연결 체크의 핵심은 "승인 UI 존재 여부"가 아니라 "`/run` 요청이 desktop mode 규칙에 맞게 통과/거절되는지"다.

### 2차 체크

- 시점: `TF-MULTI-LLM-provider-transition-spec.md` 반영 직후
- 목적: 연결 회귀 확인
- 1차 체크 항목 전량 재실행

## 권장 확인 파일

- 프론트
  - `geuldobi-desktop/src/main.js`
  - `geuldobi-desktop/src/preload.js`
  - `geuldobi-desktop/src/index.html`
  - `geuldobi-desktop/DESKTOP-GUIDE.md`
- 백엔드
  - `modules/api/bridge_server.py`
  - `modules/api/process_runner.py`
  - `modules/api/prompt_broker.py`
- 테스트
  - `tests/test_process_runner.py`
  - `tests/test_run_validator.py`
  - `tests/test_risk_approval.py`

## 기록 양식

### 1차 체크 결과

- 실행 일시: `2026-03-10 14:52:04 +09:00`
- Electron 기동: `PASS` — `npm run start:spike` 실기동에서 `[backend] DEV mode`, `splash window shown`, `GET /status 200`, `switched to main window (backend-idle)`, `auto-close after 5000ms` 로그 확인
- Splash -> Main 전환: `PASS` — splash fallback 전에 `backend-idle` 이유로 main window 전환 확인
- `/status`: `PASS` — 수동 bridge 기동 후 `idle`, `/run` 직후 `running(run_id/pid 포함)`, `/stop` 후 다시 `idle` 확인
- `/run`: `PASS` — `POST /run` with `{"key":"1","inputs":{"stdin_lines":["3",""]}}` 가 `202 Accepted` + `run_id` 반환
- `/events`: `PASS` — `/events` WS에서 `run_started=1`, `stdout=108`, `prompt_request=3`, `prompt_resolved=3`, `run_stopped=1` 수신
- Mode B prompt 왕복: `PASS` — `prompt_request -> POST /run/{run_id}/input -> prompt_resolved` 3회 확인
  - 확인된 prompt 예시: 프로젝트 선택 `Choice`, 메뉴 선택 `Choice`, 분기 프롬프트 `[1] 진행 [2] 스킵 (기본: 1):`
  - 응답은 모두 bridge에서 `200 OK`로 수용됨
- `/stop`: `PASS` — `POST /stop` 가 `200 OK` 반환, 같은 run_id로 `run_stopped` WS 이벤트 수신, 최종 `/status=idle`
- Project/Workspace IPC: `미실행` — 이번 1차는 최소 런타임 기준선 범위만 수행. `main.js` handler 존재는 정적으로 확인
- Material IPC: `미실행` — dialog/renderer 자동화 부재로 1차 최소 범위에서 제외. `main.js` handler 존재는 정적으로 확인
- 종합 판정: `PASS` — 구조 변경 전 프론트-브리지-엔진 연결 기준선 확보 완료
- 보조 회귀: `pytest tests/test_process_runner.py tests/test_run_validator.py tests/test_risk_approval.py -q` → `86 passed`

### 2차 체크 결과

- 실행 일시: `2026-03-10 16:36:24 +09:00`
- 구조 변경 내용: `TF-MULTI-LLM-provider-transition-spec.md` 기준 `Phase 0-4.5` 반영. backend/provider/router/Vertex 준비는 추가됐지만 프론트 IPC/bridge contract 표면은 유지됨
- Electron 기동: `PASS` — `npm run start:spike` 실기동에서 `[backend] DEV mode`, `splash window shown`, `GET /status 200`, `switched to main window (backend-idle)`, `auto-close after 5000ms` 재확인
- `/status`: `PASS` — 독립 bridge 재기동 후 초기 `idle`, `/run` 직후 `running(run_id/pid 포함)`, `/stop` 후 최종 `idle` 재확인
- `/run`: `PASS` — `POST /run` with `{"key":"1","inputs":{"project_index":1}}` 가 `202 Accepted` + `run_id` 반환
- `/events`: `PASS` — `/events` WS에서 `run_started=1`, `stdout=124`, `prompt_request=1`, `prompt_resolved=1`, `run_stopped=1` 수신
- Mode B prompt 왕복: `PASS` — 실측 prompt는 `[1] 진행  [2] 스킵 (기본: 1):` 1건이었고, `POST /run/{run_id}/input` 로 값 `1` 응답 후 `prompt_resolved` 확인
- `/stop`: `PASS` — `POST /stop` 후 동일 run_id로 `run_stopped` WS 이벤트 수신, 최종 `/status=idle`
- 회귀 여부: `PASS` — `pytest tests/test_process_runner.py tests/test_run_validator.py tests/test_risk_approval.py tests/test_api_contract.py -q` → `136 passed`
- 추가 메모: `Project/Workspace IPC`, `Material IPC`는 이번 2차에서도 런타임 자동화 없이 `main.js/preload.js` 핸들러 존재만 정적 재확인
- 종합 판정: `PASS` — 멀티-LLM/Vertex 준비 이후에도 프론트-브리지-백엔드 연결 기준선 유지

## 현재 메모

- 1차/2차 체크가 모두 완료되었고, 이 문서는 이제 `변경 전 기준선 + 변경 후 실측 결과`를 함께 담는 문서다.
- 현재까지는 backend/provider 표면만 변했고, 프론트 IPC/bridge 계약은 유지되었다.
- 남은 미실행 범위는 `Project/Workspace/Material IPC`의 동적 자동화 확인뿐이며, 실제 프론트 수정이 들어갈 때 함께 보는 편이 효율적이다.
