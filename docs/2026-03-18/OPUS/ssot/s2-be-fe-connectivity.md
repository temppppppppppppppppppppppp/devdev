# S2: BE-FE 연결성 SSOT

> 최종 갱신: 2026-03-18
> 소스 문서: be-fe-connectivity-deepdive-full-survey, be-fe-connectivity-frontend-improvement-survey
> 감리 이력: 3PASS 감리 (사실 확인 → 교차 일관성 → 완전성 검증)

---

## 1. 개관

5-layer architecture, port 8300, 25 live IPC + 1 dead-candidate + 9 REST/WS endpoints + 8 WS event types + 7 contract documents + 12 ErrorEnvelope codes.

**핵심 수치 (코드 검증 완료)**:

| 지표 | 수치 | 1차 근거 |
|------|------|---------|
| Live IPC 메서드 | 25 | `preload.js:5-30` (PRELOAD_METHOD_CHANNELS.live 키 25개) |
| Dead-candidate IPC | 1 | `preload.js:32-34` (deadCandidate.getWorkspacePath) |
| HTTP REST 엔드포인트 | 8 | `bridge_server.py` (@app.get/post 데코레이터 8개) |
| WebSocket 엔드포인트 | 1 | `bridge_server.py` (@app.websocket("/events")) |
| WS 이벤트 타입 | 8 | `event-schema-v1.json:20-29` (enum 8개) |
| 직접 네트워크 표면 | 3 | `index.html:6173`, `splash.js:14`, `index.html:7715` |
| ErrorEnvelope 코드 | 13 | `bridge_server.py` (RunValidator + RiskApprovalGate + PromptBroker) |
| Bridge 전송 오류 코드 | 2 | `main.js:111-114` (NETWORK_ERROR, HTTP_*) |
| 계약 문서 | 7 | 5 JSON/YAML + 2 소스 내 계약 |
| 회귀 테스트 파일 | 6 | `tests/test_desktop_*.py` + `tests/test_runtime_*.py` + `tests/test_bridge_server_*.py` + `tests/test_regression_*.py` |
| Backend 포트 | 8300 | `main.js:107` (STATUS_BASE_URL) |
| PromptBroker 입력 타입 | 6 | enum, int, string, bool, enter, multiline |

**건강도**: 28/29 Active (96.6%) — Dead 1건(getWorkspacePath), Degraded 0, Orphan 0.

---

## 2. 아키텍처 계층

### 2.1 L1 Renderer — 보안 경계

**소스 파일**: `geuldobi-desktop/src/index.html` (8266줄), `geuldobi-desktop/src/splash/splash.js` (90줄)

#### 2.1.1 보안 속성

| 속성 | 값 | 근거 |
|------|----|------|
| `contextIsolation` | `true` | `main.js:365` |
| `nodeIntegration` | `false` | `main.js:366` |
| CSP `connect-src` (main) | `ws://127.0.0.1:8300`, `https://generativelanguage.googleapis.com` | `index.html:6` `<meta>` 태그 |
| CSP `connect-src` (splash) | `http://127.0.0.1:8300` | `splash.html` `<meta>` 태그 |
| CSP `script-src` | `'self' 'unsafe-inline'` | `index.html:6` (단일 파일 구조상 불가피) |
| 경로 탈출 방지 | `..`, `/`, `\` 검사 | `main.js:738` (deleteMaterialFile), `main.js:833` (resolveWorkGuardTemplatePath) |

#### 2.1.2 Renderer 직접 네트워크 접근 (3개 승인 표면)

| # | 표면 | 소스 위치 | 대상 URL | 용도 |
|---|------|-----------|---------|------|
| 1 | WebSocket 이벤트 스트림 | `index.html:6168-6222` | `ws://127.0.0.1:8300/events` | 실시간 런 이벤트 수신, 자동 재연결 (3초) |
| 2 | Splash status 폴링 | `splash.js:12-62` | `http://127.0.0.1:8300/status` | 1초 간격, 최대 30회 실패 허용 |
| 3 | Gemini API 키 검증 | `index.html:7715-7725` | `https://generativelanguage.googleapis.com/v1beta/models` | 설정 탭 API 키 테스트 |

**설계 원칙**: Renderer의 직접 네트워크 접근은 3개 승인 표면으로 엄격 제한. 모든 HTTP 뮤테이션은 IPC 브릿지 경유 필수.

#### 2.1.3 Splash Bootstrap 시퀀스

```
DOMContentLoaded
  -> getSplashConfig() [IPC invoke]
  -> setInterval(1000ms): fetchStatus("http://127.0.0.1:8300/status") [직접 fetch]
  -> state === "idle" 감지
  -> notifyBackendReady() [IPC send - 단방향]
  -> main.js: switchToMain("backend-idle")
  -> splashWindow.close() -> mainWindow.show() -> app:ready 이벤트 발행
```

| 안전망 파라미터 | 값 | 근거 |
|----------------|----|----|
| Splash fallback 타임아웃 | 8000ms | `main.js:106` SPLASH_FALLBACK_MS |
| 폴링 실패 한도 | 30회 | `splash.js:6` MAX_POLL_FAILS |
| 개별 fetch 타임아웃 | 5000ms | `splash.js:17` AbortSignal.timeout(5000) |

---

### 2.2 L2 Preload Bridge — 25 live + 1 dead-candidate

**소스 파일**: `geuldobi-desktop/src/preload.js` (97줄)

#### 2.2.1 전체 IPC 메서드 인벤토리 (25 live + 1 dead-candidate)

| # | 메서드명 | IPC 채널 | 소유 도메인 | 전송 유형 | Active Consumer | preload.js 행 |
|---|---------|---------|-----------|----------|----------------|-------------|
| 1 | `getSplashConfig` | `splash:get-config` | splash bootstrap | invoke (양방향) | splash.js:71 | L6 |
| 2 | `notifyBackendReady` | `splash:backend-ready` | splash bootstrap | send (단방향) | splash.js:35 | L7 |
| 3 | `onAppReady` | `app:ready` | desktop handoff | on (수신) | index.html | L8 |
| 4 | `runKey` | `bridge:run` | desktop run control | invoke | index.html | L9 |
| 5 | `stopRun` | `bridge:stop` | desktop run control | invoke | index.html | L10 |
| 6 | `getStatus` | `bridge:status` | command readiness | invoke | index.html:6188, 6218 | L11 |
| 7 | `getQualitySummary` | `bridge:get-quality-summary` | quality operator | invoke | index.html | L12 |
| 8 | `getQualityDashboard` | `bridge:get-quality-dashboard` | quality operator | invoke | index.html | L13 |
| 9 | `getSafeOpsPreview` | `bridge:get-safe-ops-preview` | safe-op operator | invoke | index.html | L14 |
| 10 | `saveQualityReview` | `bridge:save-quality-review` | quality operator | invoke | index.html | L15 |
| 11 | `getBackendUrl` | `bridge:get-url` | WS bootstrap | invoke | index.html:6172 | L16 |
| 12 | `getCliContract` | `bridge:get-cli-contract` | stage 0 contract UI | invoke | index.html | L17 |
| 13 | `saveSettings` | `bridge:save-settings` | settings persistence | invoke | index.html:5983, 7961 | L18 |
| 14 | `loadSettings` | `bridge:load-settings` | settings persistence | invoke | index.html | L19 |
| 15 | `listMaterialFiles` | `material:list-files` | material manager | invoke | index.html | L20 |
| 16 | `importMaterialFile` | `material:import-file` | material manager | invoke | index.html | L21 |
| 17 | `deleteMaterialFile` | `material:delete-file` | material manager | invoke | index.html | L22 |
| 18 | `resolvePrompt` | `bridge:resolve-prompt` | mode-b prompt loop | invoke | index.html:6376 | L23 |
| 19 | `listProjects` | `project:list` | project selector | invoke | index.html | L24 |
| 20 | `createProject` | `project:create` | project selector | invoke | index.html | L25 |
| 21 | `loadProjectConfigSurfaces` | `project:load-config-surfaces` | project config | invoke | index.html | L26 |
| 22 | `saveProjectConfigSurfaces` | `project:save-config-surfaces` | project config | invoke | index.html | L27 |
| 23 | `listWorkGuardTemplates` | `project:list-work-guard-templates` | work guard UI | invoke | index.html:7686 | L28 |
| 24 | `applyWorkGuardTemplate` | `project:apply-work-guard-template` | work guard UI | invoke | index.html:7805 | L29 |
| 25 | `openWorkspaceFolder` | `workspace:open-folder` | workspace utility | invoke | index.html | L30 |
| DC | `getWorkspacePath` | `workspace:get-path` | **dead-candidate** | invoke | **없음** | L33 |

**수정 이력**: 1차 소스(deepdive-full-survey) 아키텍처 다이어그램에서 "23개 live"로 표기했으나, 동 문서 인벤토리 테이블 및 2차 소스(frontend-improvement-survey), 실제 코드(`preload.js:5-30`)에서 25개로 확인. 본 SSOT에서 **25 live**로 정정.

#### 2.2.2 Preload 설계 특성

1. **채널 상수 하드코딩**: `require("./desktop_control_plane_contract")` 대신 로컬 `PRELOAD_METHOD_CHANNELS` 정의 — sandboxed preload에서 packaged Electron의 상대 경로 require 불안정 (`preload.js:3` 주석)
2. **이중 정의 동기화**: `desktop_control_plane_contract.js`의 `PRELOAD_METHOD_CHANNELS`와 `preload.js` 로컬 복사본이 동일 채널 문자열을 유지해야 함
3. **Dead-candidate 관리**: `getWorkspacePath`는 명시적으로 `deadCandidate` 객체에 분리 (`preload.js:32-34`), `must_not_be_treated_as_live: true` 계약 명시

---

### 2.3 L3 Electron Main Process — bridgeFetch, transport protocol

**소스 파일**: `geuldobi-desktop/src/main.js` (1010줄)

#### 2.3.1 bridgeFetch 전송 프로토콜

```javascript
// main.js:494-549
async function bridgeFetch(urlPath, options = {}) {
  // 타임아웃: BRIDGE_FETCH_TIMEOUT_MS = 5000ms (main.js:108)
  // 성공: backend JSON 그대로 반환
  // HTTP 오류: { ok: false, code: "HTTP_{status}", data: { envelope_version, ... } }
  // 네트워크 오류: { ok: false, code: "NETWORK_ERROR", data: { ... } }
}
```

**Desktop Bridge Transport 계약** (`api-contract-v1.yaml:85-121`):

| 속성 | 값 | 코드 근거 |
|------|----|----------|
| `envelope_version` | `desktop_bridge_v1` | `main.js:114` DESKTOP_BRIDGE_TRANSPORT.envelopeVersion |
| `networkErrorCode` | `NETWORK_ERROR` | `main.js:112` DESKTOP_BRIDGE_TRANSPORT.networkErrorCode |
| `httpErrorPrefix` | `HTTP_` | `main.js:113` DESKTOP_BRIDGE_TRANSPORT.httpErrorPrefix |
| `request_timeout_ms` | `5000` | `main.js:108` BRIDGE_FETCH_TIMEOUT_MS |

**핵심**: Renderer는 bridgeFetch 결과만 받으므로, backend `ErrorEnvelope.code`와 desktop transport `code`를 구별 가능해야 함. `data.backend_code` / `data.backend_message` 필드로 원본 backend 오류를 에코.

#### 2.3.2 IPC 핸들러 -> bridgeFetch 라우팅 매핑 (8개)

| # | IPC 채널 | Backend Route | HTTP Method | main.js 행 | bridge_server.py 행 |
|---|----------|-------------|------------|-----------|---------------------|
| 1 | `bridge:run` | `/run` | POST | L551 | L1839 |
| 2 | `bridge:stop` | `/stop` | POST | L561 | L1982 |
| 3 | `bridge:status` | `/status` | GET | L566 | L2000 |
| 4 | `bridge:get-quality-summary` | `/quality/summary?project=&lookback=` | GET | L578 | L2043 |
| 5 | `bridge:get-quality-dashboard` | `/quality/dashboard?project=&lookback=` | GET | L588 | L2060 |
| 6 | `bridge:get-safe-ops-preview` | `/safe-ops/preview?project=` | GET | L598 | L2074 |
| 7 | `bridge:save-quality-review` | `/quality/review` | POST | L603 | L2090 |
| 8 | `bridge:resolve-prompt` | `/run/{run_id}/input` | POST | L615 | L1952 |

**BRIDGE_MANAGED_ROUTES SSOT**: `desktop_control_plane_contract.js:77-85` (7개 정적 경로) + `buildRunInputRoute()` (1개 동적 경로, L87-89)

#### 2.3.3 로컬 전용 핸들러 (17개, backend 미경유)

| # | IPC 채널 | 처리 위치 | main.js 행 | 설명 |
|---|----------|----------|-----------|------|
| 1 | `bridge:get-url` | main.js 로컬 | L570 | WS/HTTP URL 상수 반환 |
| 2 | `bridge:get-cli-contract` | main.js 로컬 | L574 | CLI 계약 (장르 인덱스 매핑, 10개 장르) 반환 |
| 3 | `bridge:save-settings` | main.js -> 파일시스템 | L624 | `%LOCALAPPDATA%/Geuldobi/settings.json` 쓰기 |
| 4 | `bridge:load-settings` | main.js -> 파일시스템 | L636 | 동일 경로 읽기 |
| 5 | `material:list-files` | main.js -> 파일시스템 | L672 | `bible/`, `treatments/` 파일 목록 |
| 6 | `material:import-file` | main.js -> 파일시스템 | L694 | dialog.showOpenDialog -> fs.copyFileSync |
| 7 | `material:delete-file` | main.js -> 파일시스템 | L733 | 경로 탈출 방지 검사 후 fs.unlinkSync |
| 8 | `project:list` | main.js -> 파일시스템 | L846 | 프로젝트 디렉토리 목록 |
| 9 | `project:create` | main.js -> 파일시스템 | L867 | 새 프로젝트 디렉토리 생성 |
| 10 | `project:load-config-surfaces` | main.js -> 파일시스템 | L888 | author_directives.txt + work_guard.yaml 읽기 |
| 11 | `project:save-config-surfaces` | main.js -> 파일시스템 | L903 | author_directives.txt + work_guard.yaml 쓰기 |
| 12 | `project:list-work-guard-templates` | main.js -> 파일시스템 | L922 | YAML 템플릿 열거 |
| 13 | `project:apply-work-guard-template` | main.js -> 파일시스템 | L935 | 라이브러리 경로 검증 + YAML 덮어쓰기 |
| 14 | `workspace:open-folder` | main.js -> shell.openPath | L956 | 탐색기 열기 |
| 15 | `splash:get-config` | main.js 로컬 | L479 | 스플래시 설정 반환 |
| 16 | `splash:backend-ready` | main.js ipcMain.on | L487 | 스플래시 -> 메인 전환 트리거 |
| 17 | `app:ready` | main.js send | L460 | 메인 윈도우 표시 알림 |

#### 2.3.4 Backend 프로세스 수명주기

```
app.whenReady()
  -> syncPackagedWorkspaceSeed()     # 패키징 모드: workspace-seed -> 내 문서/글도비
  -> startBackend()                  # spawn(backend.exe | python -m uvicorn)
  -> bootstrapWindows()              # splash + main 윈도우 생성

startBackend():
  개발: python -m uvicorn modules.api.bridge_server:app --port 8300
  배포: resources/backend/backend.exe
  환경변수: GEULDOBI_DESKTOP_MODE=1, PYTHONIOENCODING=utf-8, PYTHONUNBUFFERED=1
  배포 추가: GEULDOBI_PACKAGED_RUNTIME_MODEL, GEULDOBI_WORKSPACE, GEULDOBI_PROJECTS_ROOT

  자동 재시작: 비정상 종료 시 2초 후 재시작 (최대 2회, main.js:237 MAX_BACKEND_RESTARTS)
  stdout/stderr: 콘솔 + debugLog 파일 기록

window-all-closed / before-quit:
  -> stopBackend() -> taskkill /pid {pid} /t /f (Windows)
```

---

### 2.4 L4 FastAPI Bridge Server — 9 endpoints, validation gate chain

**소스 파일**: `modules/api/bridge_server.py` (87KB, ~2155줄)

#### 2.4.1 엔드포인트 인벤토리 (8 HTTP + 1 WS = 9)

| # | 경로 | 메서드 | 용도 | 응답 코드 | bridge_server.py 행 |
|---|------|--------|------|----------|---------------------|
| 1 | `/run` | POST | 메뉴 키 실행 | 202, 400, 403, 409 | L1839 |
| 2 | `/run/{run_id}/input` | POST | Mode B 프롬프트 응답 | 200, 400, 409 | L1952 |
| 3 | `/stop` | POST | 실행 중지 (멱등) | 200 | L1982 |
| 4 | `/status` | GET | 러너 상태 조회 | 200 | L2000 |
| 5 | `/quality/summary` | GET | 품질 요약 | 200, 400, 500 | L2043 |
| 6 | `/quality/dashboard` | GET | 품질 대시보드 | 200, 400, 500 | L2060 |
| 7 | `/safe-ops/preview` | GET | 안전 연산 미리보기 | 200, 400, 500 | L2074 |
| 8 | `/quality/review` | POST | 운영자 품질 리뷰 저장 | 200, 400, 500 | L2090 |
| 9 | `/events` | WS | 실시간 이벤트 스트림 | -- | L2137 |

#### 2.4.2 검증 게이트 체인 (POST /run)

```
POST /run 수신
  -> T4: RunValidator
       ALLOWED_KEYS = {"0","1","2","3","4","6","7","44","77","88","99"}
         (control_plane_contract.py:21-24 PUBLIC_RUN_KEYS)
       key="0" -> ALLOWED_STAGE0_SUB_KEYS = {"1","2","3","4","5","6","7"}
         (control_plane_contract.py:25 PUBLIC_STAGE0_SUB_KEYS)
       key="5" -> 차단 (INTERNAL_UI_ACTION_KEYS, desktop exit 전용)
  -> T6: RiskApprovalGate (key in {"44","77","88","99"})
         (control_plane_contract.py:30 RISK_KEYS)
       dual-control 승인 기록 확인
       만료 검사 (expires_at)
       감사 로그: logs/risk-approval-log.jsonl
  -> T7: ProcessRunner
       spawn main_a.py + stdin 시퀀스 전달
       Mode B: PromptBroker 연동
```

#### 2.4.3 ErrorEnvelope 코드 체계 (13개)

| # | 코드 | 발행 조건 | 게이트 |
|---|------|----------|--------|
| 1 | `INVALID_KEY` | 허용되지 않은 메뉴 키 | T4 RunValidator |
| 2 | `SUB_KEY_REQUIRED` | key=0인데 sub_key 미제공 | T4 RunValidator |
| 3 | `SUB_KEY_NOT_ALLOWED` | key!=0인데 sub_key 제공 | T4 RunValidator |
| 4 | `INVALID_SUB_KEY` | 유효하지 않은 sub_key 값 | T4 RunValidator |
| 5 | `RUN_ALREADY_ACTIVE` | 이미 실행 중 | T7 ProcessRunner |
| 6 | `RISK_APPROVAL_REQUIRED` | 위험 키에 대한 승인 필요 | T6 RiskApprovalGate |
| 7 | `RISK_APPROVAL_EXPIRED` | 승인 만료 | T6 RiskApprovalGate |
| 8 | `RISK_APPROVAL_DUAL_CONTROL_REQUIRED` | 이중 통제 미충족 | T6 RiskApprovalGate |
| 9 | `INVALID_PROMPT_ID` | run_id에 속하지 않는 prompt_id | PromptBroker |
| 10 | `PROMPT_ALREADY_RESOLVED` | 이미 처리된 프롬프트 | PromptBroker |
| 11 | `INTERNAL_ERROR` | 서버 내부 오류 | 전역 |
| 12 | `INVALID_PROJECT` | 유효하지 않은 프로젝트 | Quality/SafeOps 핸들러 |
| 13 | `INVALID_REQUEST` | 일반 요청 검증 실패 | `/quality/review` POST (`bridge_server.py:2096,2111`) |

---

### 2.5 L5 Python Engine — stdin/stdout/stderr + filesystem

**소스 파일**: `main_a.py` (237KB), `modules/domain/agents/` (47 에이전트)

#### 2.5.1 Engine <-> Bridge 연결점

Engine은 Bridge Server가 spawn한 별도 프로세스:

| 연결 채널 | 방향 | 프로토콜 |
|----------|------|---------|
| stdin | Bridge -> Engine | 텍스트 시퀀스 (메뉴 키 전달) |
| stdout | Engine -> Bridge | 텍스트 출력 (ANSI 스트립 후 WS broadcast) |
| stderr | Engine -> Bridge | 로그/오류 (진단 목적) |
| 파일시스템 | 양방향 | `project_data.db`, `logs/*.jsonl`, `artifacts/` |

---

## 3. 데이터 흐름

### 3.1 정방향: 사용자 액션 -> DB

**에피소드 생성 실행 (key=4) 전체 경로**:

```
[1] 사용자 UI: "4번 키 실행" 클릭
    | window.geuldobiDesktop.runKey("4", null, {}, null)

[2] preload.js: ipcRenderer.invoke("bridge:run", {key:"4", subKey:null, inputs:{}, approvalId:null})
    | Electron IPC (프로세스 간 직렬화)

[3] main.js ipcMain.handle("bridge:run") (L551):
    body = { key: "4" }
    | bridgeFetch("/run", { method: "POST", body: JSON.stringify(body) })
    | fetch("http://127.0.0.1:8300/run", ...) + 5초 타임아웃

[4] bridge_server.py POST /run (L1839):
    T4: RunValidator.validate(key="4") -> OK (ALLOWED_KEYS 포함)
    T6: RiskApprovalGate 스킵 (key not in RISK_KEYS)
    T7: ProcessRunner.start(key="4", mode="b")
    | 응답: 202 { ok:true, run_id:"uuid", code:"OK" }

[5] ProcessRunner:
    spawn("python", ["main_a.py"], env={GEULDOBI_DESKTOP_MODE:"1"})
    stdin 시퀀스: "4\n" (메뉴 선택)

[6] main_a.py:
    Stage 4 진입 -> ChiefWriter.generate_ensemble()
    -> 3개 후보 원고 생성 (Gemini 2.5 Pro)
    -> 6-tier Validation Pipeline
    -> Director 최종 판정 (PASS / PASS_WITH_FIX / REJECT)
    -> DBManager.save_manuscript() [SQLite 트랜잭션]

[7] stdout 이벤트 스트림:
    Engine stdout -> ProcessRunner.on_line callback
    -> WSManager.broadcast(run_id, {type:"stdout", payload:{text:"..."}})
    -> WebSocket -> Renderer 실시간 표시

[8] 완료:
    Engine exit(0) -> ProcessRunner.on_exit
    -> WSManager.broadcast(run_id, {type:"run_completed", payload:{returncode:0, ...}})
    -> PromptBroker.cleanup_run(run_id)
```

**위험 연산 실행 (key=44) 추가 경로**:

```
[4'] bridge_server.py POST /run (L1839):
    T4: RunValidator.validate(key="44") -> OK
    T6: RiskApprovalGate.validate(key="44", approval_id="APPROVAL-001")
        -> ApprovalRecord 조회
        -> 이중 통제 검증 (approved_by_primary != approved_by_secondary)
        -> 만료 검사 (expires_at > now)
        -> 감사 로그 기록 -> logs/risk-approval-log.jsonl

[실패 시] 403 { ok:false, code:"RISK_APPROVAL_REQUIRED" }
         -> main.js bridgeFetch -> HTTP_403 transport 오류로 변환
         -> Renderer에서 transport 코드와 backend_code 분리 표시
```

---

### 3.2 역방향: WebSocket 이벤트 스트림 (8 types with payload)

#### 3.2.1 전체 이벤트 타입 인벤토리

| # | 이벤트 타입 | 방향 | payload 필수 필드 | 발행 시점 |
|---|------------|------|------------------|----------|
| 1 | `run_started` | Server->Client | `key` | ProcessRunner 시작 직후 |
| 2 | `stdout` | Server->Client | `text` | Engine stdout 라인마다 |
| 3 | `prompt_request` | Server->Client | `prompt_id`, `step_id`, `input_type`, `default`, `timeout_sec` | PromptBroker.request_input() |
| 4 | `prompt_resolved` | Server->Client | `prompt_id`, `value`, `source` | PromptBroker.resolve() |
| 5 | `prompt_timeout` | Server->Client | `prompt_id`, `applied_default` | 타임아웃 시 |
| 6 | `run_completed` | Server->Client | `returncode` | Engine 정상 종료 (exit 0) |
| 7 | `run_failed` | Server->Client | `returncode` | Engine 비정상 종료 (exit != 0) |
| 8 | `run_stopped` | Server->Client | (없음) | 사용자 중지 요청 처리 |

근거: `event-schema-v1.json:20-29` enum 목록

#### 3.2.2 이벤트 봉투 스키마 (event-schema-v1.json)

```json
{
  "event_version": "v1",        // const "v1"
  "seq": "<integer >= 1>",      // monotonic sequence
  "run_id": "<uuid>",           // 실행 식별자
  "type": "<event_type>",       // enum (위 8개 타입)
  "ts": "<ISO 8601 datetime>",  // 발행 시각
  "payload": { ... }            // 타입별 조건부 스키마
}
```

스키마 특성: JSON Schema draft 2020-12, `allOf` + `if/then` 조건부 검증으로 타입별 payload 강제 (`event-schema-v1.json`, 272줄).

#### 3.2.3 run_completed/run_failed 진단 payload

```json
{
  "returncode": 0,
  "key": "4",
  "sub_key": null,
  "mode": "b",
  "started_at": "2026-03-18T10:30:00Z",
  "duration_ms": 125000,
  "last_prompt_step": "confirm_production",
  "stdout_tail": ["마지막 5줄..."],
  "stderr_tail": ["오류 로그..."],
  "stderr_authoritative": true,
  "stderr_decode_policy": "utf-8",
  "failure_phase": null
}
```

---

### 3.3 Mode B 프롬프트 루프

```
[Engine] main_a.py stdout: "PROMPT_REQUEST:{json}" 인식
    |
[ProcessRunner] 파싱 -> PromptBroker.request_input(run_id, PromptState)
    |
[PromptBroker] WS 이벤트 발행:
    {
      event_version: "v1",
      seq: 42,
      run_id: "uuid",
      type: "prompt_request",
      ts: "2026-03-18T10:30:00+00:00",
      payload: {
        prompt_id: "p-001",
        step_id: "select_project",
        input_type: "enum",
        default: "1",
        timeout_sec: 300,
        prompt_text: "프로젝트를 선택하세요",
        options: [{ key: "1", label: "0_260318" }]
      }
    }
    |
[Renderer] WebSocket 수신 -> 프롬프트 UI 렌더링
    |
[사용자] 선택 입력
    |
[Renderer] window.geuldobiDesktop.resolvePrompt(runId, "p-001", "1")
    | IPC bridge:resolve-prompt
    | bridgeFetch("/run/{run_id}/input", POST, {prompt_id:"p-001", value:"1"})
    |
[PromptBroker] resolve(run_id, "p-001", "1")
    -> prompt.resolved = True, prompt.value = "1"
    -> prompt._event.set() (asyncio.Event 해제)
    -> WS prompt_resolved 이벤트 발행
    |
[Engine] await 해제 -> 선택값 "1" 수신 -> 실행 계속
```

**타임아웃 흐름**:
```
asyncio.wait_for(timeout=prompt.timeout_sec) 만료
  -> prompt.value = prompt.default
  -> WS prompt_timeout 이벤트: { prompt_id, applied_default }
  -> Engine은 default 값으로 계속 진행
```

**스레드 안전**: `prompt_broker.py:72` — `_lock = threading.Lock()`, 중복 입력 차단.

---

### 3.4 설정/자재 데이터 흐름

#### 3.4.1 Settings 영속화

```
[Renderer] saveSettings(settings)
  -> IPC bridge:save-settings (main.js:624)
  -> fs.writeFileSync(SETTINGS_PATH, JSON.stringify(settings), "utf8")
  -> SETTINGS_PATH = %LOCALAPPDATA%/Geuldobi/settings.json

[Renderer] loadSettings()
  -> IPC bridge:load-settings (main.js:636)
  -> fs.readFileSync(SETTINGS_PATH, "utf8") -> JSON.parse
  -> 손상 시: .bak 백업 후 null 반환
```

#### 3.4.2 Material 파일 관리

```
listMaterialFiles("bible")   -> fs.readdirSync(materialRoot/bible) -> [{name, size, isDir}]
importMaterialFile("bible")  -> dialog.showOpenDialog -> fs.copyFileSync(src, dest)
deleteMaterialFile("bible", "foo.json") -> 경로 탈출 방지 검사 -> fs.unlinkSync

경로 탈출 방지: fileName에 "..", "/", "\" 포함 시 거부 (main.js:738)
```

#### 3.4.3 Project Config 데이터 흐름

```
loadProjectConfigSurfaces(project) (main.js:888)
  -> {projectRoot}/config/author_directives.txt (없으면 기본 템플릿)
  -> {projectRoot}/config/work_guard.yaml (없으면 빈 문자열)

saveProjectConfigSurfaces(project, authorDirectives, workGuardYaml) (main.js:903)
  -> fs.writeFileSync 두 파일 동시 저장

applyWorkGuardTemplate(project, templatePath) (main.js:935)
  -> resolveWorkGuardTemplatePath: 라이브러리 경로 내 검증 + YAML 확장자 검사 (main.js:833)
  -> 템플릿 내용 -> work_guard.yaml 덮어쓰기
```

---

## 4. 계약 및 테스트

### 4.1 7 contract documents

| # | 계약 파일 | 용도 | 규격 | 행수 |
|---|----------|------|------|------|
| 1 | `docs/implementation/api-contract-v1.yaml` | OpenAPI 3.1.0 API 명세 | OpenAPI | 541 |
| 2 | `docs/implementation/event-schema-v1.json` | WebSocket 이벤트 JSON Schema | JSON Schema draft 2020-12 | 272 |
| 3 | `docs/implementation/desktop-ipc-surface-contract-v1.json` | IPC 메서드 인벤토리 | 자체 규격 | 181 |
| 4 | `docs/implementation/desktop-runtime-contract-v1.json` | 패키징 리소스 명세 | 자체 규격 | 48 |
| 5 | `docs/implementation/surface-containment-contract-v1.json` | 표면 분류 (live/shadow/residue) | 자체 규격 | 68 |
| 6 | `modules/api/control_plane_contract.py` | 제어면 권한 계약 (Python) | Python source | 93 |
| 7 | `geuldobi-desktop/src/desktop_control_plane_contract.js` | IPC 채널 정의 (JavaScript) | JS source | 97 |

#### 4.1.1 계약 <-> 코드 정합성 대조 결과

**IPC Surface 계약 vs preload.js**:

| 계약 (desktop-ipc-surface-contract-v1.json) | preload.js | 일치 여부 |
|---------------------------------------------|------------|----------|
| live 메서드 25개 | 25개 (getSplashConfig ~ openWorkspaceFolder) | **일치** |
| dead-candidate 1개 (getWorkspacePath) | 1개 (deadCandidate 객체) | **일치** |
| 채널 문자열 매핑 | PRELOAD_METHOD_CHANNELS.live 키 매핑 | **일치** |

**API 계약 vs bridge_server.py**:

| 계약 경로 (api-contract-v1.yaml) | 구현 | 일치 |
|---------------------------------|------|-----|
| POST /run -> 202, 400, 403, 409 | RunValidator + RiskApprovalGate + ProcessRunner | **일치** |
| POST /run/{run_id}/input -> 200, 400, 409 | PromptBroker.resolve() | **일치** |
| POST /stop -> 200 | ProcessRunner.stop() (멱등) | **일치** |
| GET /status -> 200 | state snapshot + pending_prompts | **일치** |
| GET /quality/summary -> 200, 400, 500 | project 파라미터 검증 + DB 조회 | **일치** |
| GET /quality/dashboard -> 200, 400, 500 | 동일 구조 | **일치** |
| GET /safe-ops/preview -> 200, 400, 500 | 프로젝트별 안전 연산 미리보기 | **일치** |
| POST /quality/review -> 200, 400, 500 | 운영자 리뷰 DB 저장 | **일치** |
| WS /events -> 8개 이벤트 타입 | WSManager + PromptBroker 이벤트 발행 | **일치** |

**RunRequest 스키마 vs control_plane_contract.py**:

| 계약 필드 | 계약 값 | Python 코드 | 일치 |
|----------|---------|------------|-----|
| `key` enum | `['0','1','2','3','4','6','7','44','77','88','99']` | `PUBLIC_RUN_KEYS` (`control_plane_contract.py:21-24`) | **일치** |
| `sub_key` enum | `['1','2','3','4','5','6','7']` | `PUBLIC_STAGE0_SUB_KEYS` (`control_plane_contract.py:25`) | **일치** |
| risk keys | 403 응답 유발 | `RISK_KEYS = frozenset({"44","77","88","99"})` (`control_plane_contract.py:30`) | **일치** |

**Desktop Bridge Transport 계약 vs main.js**:

| 계약 (api-contract-v1.yaml x-desktop-bridge-transport) | main.js 코드 | 일치 |
|---------------------------------------------------------|-------------|-----|
| `envelope_version: desktop_bridge_v1` | `main.js:114` | **일치** |
| `network_error_code: NETWORK_ERROR` | `main.js:112` | **일치** |
| `http_error_code_format: HTTP_<status_code>` | `main.js:113` | **일치** |
| `request_timeout_ms: 5000` | `main.js:108` | **일치** |

**CSP 계약 vs HTML 소스**:

| 계약 (api-contract-v1.yaml csp_connect_src) | HTML 소스 | 일치 |
|---------------------------------------------|----------|-----|
| main_window: `https://generativelanguage.googleapis.com`, `ws://127.0.0.1:8300` | index.html:6 CSP meta | **일치** |
| splash_window: `http://127.0.0.1:8300` | splash.html CSP meta | **일치** |

**정합성 총평**: 계약 <-> 코드 불일치 **0건**.

---

### 4.2 6 regression test files

| # | 테스트 파일 | 커버 대상 |
|---|------------|----------|
| 1 | `tests/test_desktop_contract_refresh.py` | desktop-ipc-surface-contract + desktop-runtime-contract + surface-containment-contract 정합성 |
| 2 | `tests/test_desktop_transport_contract.py` | desktop bridge transport 봉투 + WS 이벤트 타입/payload 계약 |
| 3 | `tests/test_desktop_packaging_contract.py` | 패키징 리소스 인벤토리 + env 변수 |
| 4 | `tests/test_runtime_authority_contract.py` | 제어면 권한 경로 + 권위 싱크 |
| 5 | `tests/test_bridge_server_desktop_risk_gate.py` | 위험 키 승인 게이트 동작 |
| 6 | `tests/test_regression_validation_tier_contract.py` | 검증 티어 회귀 |

**계약 문서 내 명시 참조 테스트 함수** (api-contract-v1.yaml):

| 테스트 함수 | 검증 내용 |
|--------------------------------------------|----------|
| `test_approved_direct_surface_inventory_matches_source_code` | 승인 직접 표면 3개가 소스 코드와 일치 |
| `test_renderer_csp_connect_src_matches_documented_direct_allowlist` | CSP connect-src가 계약과 일치 |
| `test_bridge_managed_backend_routes_match_main_process_bridge` | bridgeFetch 라우팅이 계약과 일치 |
| `test_desktop_bridge_transport_contract_matches_main_process_source` | transport 봉투 규격 일치 |
| `test_runtime_websocket_event_types_match_schema_and_emitters` | WS 이벤트 타입 8개가 스키마/emitter와 일치 |
| `test_runtime_websocket_payload_contract_matches_renderer_and_backend_usage` | 이벤트 payload 구조 일치 |

---

### 4.3 ErrorEnvelope 13 codes + Bridge Transport 2 codes

**Backend ErrorEnvelope** (13개):

| # | 코드 | HTTP 상태 | 발행 게이트 |
|---|------|----------|-----------|
| 1 | `INVALID_KEY` | 400 | T4 RunValidator |
| 2 | `SUB_KEY_REQUIRED` | 400 | T4 RunValidator |
| 3 | `SUB_KEY_NOT_ALLOWED` | 400 | T4 RunValidator |
| 4 | `INVALID_SUB_KEY` | 400 | T4 RunValidator |
| 5 | `RUN_ALREADY_ACTIVE` | 409 | T7 ProcessRunner |
| 6 | `RISK_APPROVAL_REQUIRED` | 403 | T6 RiskApprovalGate |
| 7 | `RISK_APPROVAL_EXPIRED` | 403 | T6 RiskApprovalGate |
| 8 | `RISK_APPROVAL_DUAL_CONTROL_REQUIRED` | 403 | T6 RiskApprovalGate |
| 9 | `INVALID_PROMPT_ID` | 400 | PromptBroker |
| 10 | `PROMPT_ALREADY_RESOLVED` | 409 | PromptBroker |
| 11 | `INTERNAL_ERROR` | 500 | 전역 |
| 12 | `INVALID_PROJECT` | 400 | Quality/SafeOps 핸들러 |

**Desktop Bridge Transport** (2개, `main.js:111-114`):

| 코드 | 발행 조건 |
|------|----------|
| `NETWORK_ERROR` | fetch 실패 (타임아웃 포함) |
| `HTTP_{status}` | HTTP 비-2xx 응답 (예: HTTP_403, HTTP_409) |

**네임스페이스 분리**: backend 코드 (`INVALID_KEY` 등)와 transport 코드 (`NETWORK_ERROR`, `HTTP_*`)는 명확히 구분됨. Renderer는 `data.backend_code`로 원본 backend 오류에 접근.

---

## 5. 수치 요약표

| 지표 | 수치 | 근거 |
|------|------|------|
| 총 IPC 메서드 (live) | **25** | `preload.js:5-30` |
| 총 IPC 메서드 (dead-candidate) | **1** | `preload.js:32-34` |
| Bridge-Managed IPC (bridgeFetch 경유) | **8** | `desktop_control_plane_contract.js:77-89` |
| 로컬 전용 IPC (backend 미경유) | **17** | 25 - 8 = 17 |
| 총 HTTP REST 엔드포인트 | **8** | `bridge_server.py` @app.get/post 8개 |
| 총 WebSocket 엔드포인트 | **1** | `bridge_server.py` @app.websocket("/events") |
| 총 WS 이벤트 타입 | **8** | `event-schema-v1.json:20-29` |
| 총 직접 네트워크 표면 | **3** | WS + splash polling + Gemini fetch |
| 총 ErrorEnvelope 코드 | **13** | bridge_server.py 전수 (INVALID_REQUEST 포함) |
| 총 Bridge 전송 오류 코드 | **2** | `main.js:111-114` (NETWORK_ERROR, HTTP_*) |
| 총 PromptBroker 입력 타입 | **6** | enum, int, string, bool, enter, multiline |
| 총 계약 문서 | **7** | 5 JSON/YAML + 2 소스 내 계약 |
| 총 회귀 테스트 파일 (계약 관련) | **6** | `tests/test_desktop_*.py` 등 |
| Backend 포트 | **8300** | `main.js:107` STATUS_BASE_URL |
| bridgeFetch 타임아웃 | **5000ms** | `main.js:108` BRIDGE_FETCH_TIMEOUT_MS |
| Splash fallback 타임아웃 | **8000ms** | `main.js:106` SPLASH_FALLBACK_MS |
| Splash 폴링 실패 한도 | **30회** | `splash.js:6` MAX_POLL_FAILS |
| Backend 자동 재시작 한도 | **2회** | `main.js:237` MAX_BACKEND_RESTARTS |
| 장르 인덱스 매핑 | **10개** | `main.js:121-132` CLI_CONTRACT.genreIndexMap |
| Python 에이전트 수 | **47** | `modules/domain/agents/` |
| Validation Pipeline 티어 | **6** | 6-tier validation |
| index.html 총 줄 수 | **8266** | CSS ~2765 + HTML ~714 + JS ~4778 |
| 연결 건강도 (Active) | **28/29** (96.6%) | 25 live + 3 직접 = 28 Active, 1 Dead |
| 계약 <-> 코드 불일치 | **0건** | 3PASS 감리 결과 |
| 3방향 교차 모순 | **0건** | 방향 A/B/C 교차 대조 |
| 미커버 채널/스키마 | **0건** | 완전성 검증 결과 |

---

## 6. 발견 사항

### 6.1 강점

| # | 강점 | 근거 |
|---|------|------|
| S1 | **엄격한 Renderer 네트워크 격리** | 3개 승인 직접 표면만 허용, 나머지 전부 IPC 브릿지 경유. CSP 강제. `main.js:365-366` contextIsolation=true, nodeIntegration=false |
| S2 | **계약 기반 개발** | 7개 계약 문서가 코드와 1:1 매핑. 6개 회귀 테스트 파일이 drift 감시 |
| S3 | **단일 검증 지점 원칙** | 키 검증은 backend RunValidator 단독 (`control_plane_contract.py:21-30`). FE는 전달만 -- 이중 검증 동기화 문제 없음 |
| S4 | **Transport 오류 네임스페이스 분리** | `NETWORK_ERROR`/`HTTP_*` (desktop transport, `main.js:111-114`) vs `INVALID_KEY`/... (backend) 명확 구분 |
| S5 | **멱등 중지 + 자동 재시작** | `/stop` 멱등성, backend 비정상 종료 시 최대 2회 자동 재시작 (`main.js:237`) |
| S6 | **이벤트 스키마 조건부 검증** | `event-schema-v1.json`이 allOf+if/then으로 타입별 payload 구조 강제 (272줄, JSON Schema draft 2020-12) |
| S7 | **Mode B 프롬프트 브로커** | 스레드 안전 (`prompt_broker.py:72` threading.Lock), 중복 입력 차단, 타임아웃 + default 적용 |
| S8 | **권한 경로 문서화** | `control_plane_contract.py` (93줄)가 전체 권한 경로와 권위 싱크/동반자 스냅샷을 명시 |

### 6.2 관리 주의점

| # | 주의점 | 위험도 | 설명 | 근거 |
|---|--------|--------|------|------|
| W1 | **채널 이중 정의** | 중 | `preload.js`와 `desktop_control_plane_contract.js`의 채널 문자열 동기화 필요. 한쪽만 수정 시 침묵 실패 가능. `test_desktop_contract_refresh.py`가 커버하나 수동 검증도 권장 | `preload.js:3` 주석, `desktop_control_plane_contract.js` |
| W2 | **CLI_CONTRACT 정적 하드코딩** | 저 | 장르 인덱스 매핑이 `main.js:117-133`에 하드코딩 (10개 장르). `config/genres/` 변경 시 수동 동기화 필요 | `main.js:121-132` genreIndexMap |
| W3 | **Settings JSON 손상 복구** | 저 | `.bak` 백업 + null 반환 전략 (`main.js:636`). 이중 손상 시 설정 유실 가능하나 치명적이지 않음 | `main.js:636` loadSettings |
| W4 | **Backend 재시작 한도** | 저 | `MAX_BACKEND_RESTARTS=2` (`main.js:237`). 3회 연속 실패 시 사용자에게 명시적 안내 부재 (콘솔 경고만, `main.js:321`) | `main.js:237, 321` |
| W5 | **`.catch(() => {})` 무시 패턴** | 저-중 | index.html 내 8건. 특히 `resolvePrompt` 자동 응답 실패 무시(`index.html:6376`)는 Mode B 실행 흐름에서 사일런트 오류 유발 가능 | `index.html:5983, 6222, 6253, 6376, 7686, 7800, 7805, 7961` |
| W6 | **`_ws.onerror = () => {}`** | 저 | WS 에러 원인을 전혀 기록하지 않음 | `index.html:6221` |
| W7 | **CORS 미구현** | 저 (현재) | 로컬 전용(127.0.0.1:8300)이므로 정상 동작. 원격 배포 시 CORS 설정 필요 | `bridge_server.py` |
| W8 | **세션/인증 없음** | 저 (현재) | Electron Main Process가 유일한 HTTP 클라이언트. 원격 배포 시 인증 추가 필요 | `bridge_server.py` |

### 6.3 프론트엔드 구조 현황

프론트엔드 내부 구현 상세(Renderer 구조, 전역 상태, 보안 검증, 에러 핸들링) → **S3 (프론트엔드 SSOT)** 참조.

요약: `index.html` 8,266줄 바닐라 JS 모놀리스, 보안 발견 1 HIGH / 3 MEDIUM / 11 LOW / 4 INFO (→ S3 §6 참조).

---

## [부록 A] 감리 이력

### 3PASS 감리 결과

#### PASS 1: 사실 확인

| 검증 항목 | 코드 근거 | 판정 |
|----------|----------|------|
| Renderer contextIsolation=true | `main.js:365` | **확인** |
| WebSocket URL ws://127.0.0.1:8300/events | `main.js:109`, `index.html` CSP, `api-contract-v1.yaml:29` | **확인** |
| bridgeFetch 타임아웃 5000ms | `main.js:108` BRIDGE_FETCH_TIMEOUT_MS | **확인** |
| PromptBroker 스레드 안전 (threading.Lock) | `prompt_broker.py:72` | **확인** |
| 자동 재시작 최대 2회 | `main.js:237` MAX_BACKEND_RESTARTS = 2 | **확인** |
| Splash 폴링 간격 1초 | `splash.js:62` setInterval(..., 1000) | **확인** |
| Material 경로 탈출 방지 | `main.js:738` "..", "/", "\\" 검사 | **확인** |
| Dead-candidate 1개 | `preload.js:32-34`, `desktop-ipc-surface-contract-v1.json:171-179` | **확인** |
| Risk keys 4개 | `control_plane_contract.py:30` frozenset({"44","77","88","99"}) | **확인** |
| Event schema 8개 타입 | `event-schema-v1.json:20-29` enum 목록 | **확인** |
| Live IPC 메서드 25개 | `preload.js:5-30` PRELOAD_METHOD_CHANNELS.live 키 25개 | **확인** |
| ipcMain.handle/on 핸들러 25개 | `main.js` 전수 | **확인** |
| bridge_server.py 엔드포인트 9개 | 8 HTTP + 1 WS | **확인** |

**PASS 1 결과**: 근거 없는 서술 **0건**.

#### PASS 2: 교차 일관성

| 대조 쌍 | 모순 | 판정 |
|---------|------|------|
| A-아키텍처 vs B-흐름 | 없음 | **일관** |
| A-아키텍처 vs C-계약 | 없음 | **일관** |
| B-흐름 vs C-계약 | 없음 | **일관** |
| 전체 수치 일관성 (메서드 수, 엔드포인트 수, 이벤트 타입 수) | 없음 | **일관** |
| 1차 소스 vs 2차 소스 교차 대조 | IPC 메서드 수 불일치 정정 (23->25) | **정정 후 일관** |

**PASS 2 결과**: 소스 간 모순 **1건 정정** (deepdive-full-survey 다이어그램 "23 live" -> 실제 코드 25 live).

#### PASS 3: 완전성 검증

| 검증 항목 | 상태 | 비고 |
|----------|------|------|
| 모든 IPC 채널 추적됨 | **완전** | 25 live + 1 DC = 전수 |
| 모든 HTTP 엔드포인트 추적됨 | **완전** | 9개 = 전수 |
| 모든 WS 이벤트 타입 추적됨 | **완전** | 8개 = 전수 |
| 모든 ErrorEnvelope 코드 추적됨 | **완전** | 13개 = 전수 |
| 모든 직접 네트워크 표면 추적됨 | **완전** | 3개 = 전수 |
| Console Relay 채널 | **완전** | 진단 전용, 비계약 (의도적) |
| 파일시스템 접점 추적 | **완전** | settings, material, project, workspace |
| Backend 프로세스 수명주기 | **완전** | spawn -> restart -> taskkill |
| 건강도 평가 | **완전** | 28 Active / 0 Degraded / 1 Dead / 0 Orphan |

**PASS 3 결과**: 누락 채널/스키마/테스트 **0건**.

### 정정 사항 기록

| # | 원본 위치 | 원본 값 | 정정 값 | 근거 |
|---|----------|---------|---------|------|
| C1 | deepdive-full-survey 2.1 다이어그램 (L57) | "23개 live 메서드 + 1개 dead-candidate" | "25개 live 메서드 + 1개 dead-candidate" | `preload.js:5-30` 키 전수 카운트 = 25. 동 문서 2.3.1 테이블도 25개 나열. 2차 소스(frontend-improvement-survey)도 25 live 기재 |

---

## [부록 B] 근거 파일

### B.1 Frontend 소스

| 파일 | 행수 | 역할 |
|------|------|------|
| `geuldobi-desktop/src/main.js` | 1010 | Electron 메인 프로세스, IPC 핸들러 25개, backend spawn, bridgeFetch |
| `geuldobi-desktop/src/preload.js` | 97 | IPC 브릿지, contextBridge 노출 (25 live + 1 DC) |
| `geuldobi-desktop/src/index.html` | 8266 | 메인 Renderer UI (CSS+HTML+JS 인라인 모놀리스) |
| `geuldobi-desktop/src/desktop_control_plane_contract.js` | 97 | IPC 채널 상수, Bridge 라우트 매핑 SSOT |
| `geuldobi-desktop/src/console_relay.js` | 57 | 콘솔 메시지 릴레이 (진단 전용, 비계약) |
| `geuldobi-desktop/src/splash/splash.js` | 90 | 백엔드 준비 폴링 |
| `geuldobi-desktop/src/splash/splash.html` | -- | 스플래시 화면 |
| `geuldobi-desktop/src/splash/splash.css` | -- | 스플래시 스타일 |
| `geuldobi-desktop/package.json` | -- | Electron 40.8.0, 빌드 설정 |

### B.2 Backend 소스

| 파일 | 크기 | 역할 |
|------|------|------|
| `modules/api/bridge_server.py` | 87KB (~2155줄) | FastAPI 서버, REST 8개 + WebSocket 1개 |
| `modules/api/process_runner.py` | 31KB (~800줄) | 서브프로세스 관리 (Mode A/B) |
| `modules/api/prompt_broker.py` | 206줄 | Mode B 프롬프트 브로커 (스레드 안전) |
| `modules/api/run_validator.py` | 3.7KB | T4 요청 검증 |
| `modules/api/risk_approval.py` | 8.3KB | T6 위험 승인 게이트 |
| `modules/api/prompt_classifier.py` | 6.3KB | 프롬프트 분류 |
| `modules/api/control_plane_contract.py` | 93줄 | 제어면 권한 계약 (PUBLIC_RUN_KEYS, RISK_KEYS 등) |
| `main_a.py` | 237KB | Python Engine 메인 (47 LLM agents + 6-tier validation) |

### B.3 계약 문서

| 파일 | 규격 | 행수 |
|------|------|------|
| `docs/implementation/api-contract-v1.yaml` | OpenAPI 3.1.0 | 541 |
| `docs/implementation/event-schema-v1.json` | JSON Schema draft 2020-12 | 272 |
| `docs/implementation/desktop-ipc-surface-contract-v1.json` | 자체 규격 | 181 |
| `docs/implementation/desktop-runtime-contract-v1.json` | 자체 규격 | 48 |
| `docs/implementation/surface-containment-contract-v1.json` | 자체 규격 | 68 |

### B.4 회귀 테스트

| 파일 | 커버 대상 |
|------|----------|
| `tests/test_desktop_contract_refresh.py` | IPC/runtime/surface 계약 정합성 |
| `tests/test_desktop_transport_contract.py` | Bridge transport + WS 이벤트 |
| `tests/test_desktop_packaging_contract.py` | 패키징 리소스 |
| `tests/test_runtime_authority_contract.py` | 제어면 권한 |
| `tests/test_bridge_server_desktop_risk_gate.py` | 위험 게이트 |
| `tests/test_regression_validation_tier_contract.py` | 검증 티어 |

### B.5 소스 문서

| 문서 | 역할 |
|------|------|
| `docs/2026-03-18/OPUS/geuldobi-v2-be-fe-connectivity-deepdive-full-survey.md` | 3방향 독립 조사 + 교차 대조 + 3PASS 감리 원본 |
| `docs/2026-03-18/OPUS/geuldobi-v2-be-fe-connectivity-frontend-improvement-survey.md` | BE-FE 연결 전체 맵 + 건강도 평가 + FE 개선점 |
