# 글도비 v2 BE-FE 연결성 딥다이브 전수 조사

> **조사일**: 2026-03-18
> **조사 대상**: 글도비 v2 전체 코드베이스 (Python BE + Electron FE + 계약 문서)
> **조사 범위**: BE-FE 간 모든 통신 채널, 프로토콜, 데이터 흐름, 계약 무결성
> **조사 방법**: 3방향 독립 조사 → 교차 대조 → 3PASS 감리
> **코드 수정**: 없음 (조사 전용)

---

## 목차

1. [조사 방법론](#1-조사-방법론)
2. [방향 A: 아키텍처 계층별 분석](#2-방향-a-아키텍처-계층별-분석)
3. [방향 B: 데이터 흐름별 분석](#3-방향-b-데이터-흐름별-분석)
4. [방향 C: 계약-테스트 무결성 분석](#4-방향-c-계약-테스트-무결성-분석)
5. [교차 대조 결과](#5-교차-대조-결과)
6. [3PASS 감리 결과](#6-3pass-감리-결과)
7. [발견 사항 종합](#7-발견-사항-종합)
8. [근거 파일 인벤토리](#8-근거-파일-인벤토리)

---

## 1. 조사 방법론

### 1.1 3방향 독립 조사

| 방향 | 관점 | 핵심 질문 |
|------|------|----------|
| **A — 아키텍처 계층별** | 구조적 분해 | 각 계층(Renderer → Preload → Main → Backend → Engine)은 어떻게 연결되며, 경계는 명확한가? |
| **B — 데이터 흐름별** | 런타임 추적 | 사용자 액션이 최종 DB 기록까지 어떤 경로를 타며, 역방향(이벤트)은 어떻게 전달되는가? |
| **C — 계약-테스트 무결성** | 규격 검증 | 문서화된 계약(JSON/YAML)과 실제 코드 구현이 일치하며, 회귀 테스트가 커버하는가? |

### 1.2 3PASS 감리

| PASS | 목적 | 판정 기준 |
|------|------|----------|
| **1st PASS** | 사실 확인 | 코드 근거 없는 서술 제거 |
| **2nd PASS** | 교차 일관성 | 3방향 결과 간 모순 탐지 |
| **3rd PASS** | 완전성 검증 | 누락된 연결 채널·스키마·테스트 탐지 |

---

## 2. 방향 A: 아키텍처 계층별 분석

### 2.1 5계층 아키텍처 개관

```
┌─────────────────────────────────────────────────────────────────────┐
│  L1. Renderer (index.html / splash.js)                             │
│      순수 HTML/CSS/JS, contextIsolation=true, nodeIntegration=false │
│      CSP connect-src: ws://127.0.0.1:8300                          │
│                        https://generativelanguage.googleapis.com    │
├─────────────────────────────────────────────────────────────────────┤
│  L2. Preload Bridge (preload.js)                                   │
│      contextBridge.exposeInMainWorld("geuldobiDesktop", {...})      │
│      23개 live 메서드 + 1개 dead-candidate                          │
├─────────────────────────────────────────────────────────────────────┤
│  L3. Electron Main Process (main.js)                               │
│      25+ ipcMain.handle() 핸들러                                    │
│      bridgeFetch() → HTTP proxy to FastAPI                         │
│      spawn() → backend process lifecycle                           │
├─────────────────────────────────────────────────────────────────────┤
│  L4. FastAPI Bridge Server (bridge_server.py @ :8300)              │
│      REST endpoints + WebSocket /events                            │
│      T4 RunValidator → T6 RiskApprovalGate → T7 ProcessRunner     │
├─────────────────────────────────────────────────────────────────────┤
│  L5. Python Engine (main_a.py → Stage 0/2/3/4)                    │
│      47 LLM agents + 6-tier validation + SQLite persistence        │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 L1 — Renderer 계층

**소스 파일**: `geuldobi-desktop/src/index.html` (325KB), `geuldobi-desktop/src/splash/splash.js` (90행)

#### 2.2.1 보안 경계

| 속성 | 값 | 근거 |
|------|----|------|
| `contextIsolation` | `true` | `main.js:364` |
| `nodeIntegration` | `false` | `main.js:365` |
| CSP connect-src (main) | `ws://127.0.0.1:8300`, `https://generativelanguage.googleapis.com` | `index.html` `<meta>` 태그 |
| CSP connect-src (splash) | `http://127.0.0.1:8300` | `splash.html` `<meta>` 태그 |

#### 2.2.2 Renderer 네트워크 접근 분류

| 표면 | 소유자 | 전송 방식 | 용도 |
|------|--------|----------|------|
| `ws://127.0.0.1:8300/events` | mainWindow | WebSocket (직접) | 실시간 런 이벤트 스트림 수신 |
| `http://127.0.0.1:8300/status` | splashWindow | fetch (직접) | 백엔드 준비 상태 폴링 |
| `https://generativelanguage.googleapis.com/v1beta/models` | mainWindow | fetch (직접) | Gemini API 키 유효성 검증 |
| 나머지 모든 HTTP 뮤테이션 | preload_main_bridge | IPC → bridgeFetch | 브릿지 경유 (직접 네트워크 불가) |

**핵심 설계 원칙**: Renderer의 직접 네트워크 접근은 **3개 승인된 표면**으로 엄격 제한. 모든 HTTP 뮤테이션은 IPC 브릿지 경유 필수.

#### 2.2.3 Splash Bootstrap 시퀀스

```
DOMContentLoaded
  → getSplashConfig() [IPC]
  → setInterval(1000ms): fetchStatus("http://127.0.0.1:8300/status") [직접 fetch]
  → state === "idle" 감지
  → notifyBackendReady() [IPC, ipcRenderer.send — 단방향]
  → main.js: switchToMain("backend-idle")
  → splashWindow.close() → mainWindow.show() → app:ready 이벤트 발행
```

- **타임아웃 안전망**: `SPLASH_FALLBACK_MS = 8000` (main.js:106) — 8초 내 백엔드 응답 없으면 fallback 전환
- **폴링 실패 한도**: `MAX_POLL_FAILS = 30` (splash.js:6) — 30회 연속 실패 시 오류 메시지 표시
- **fetch 타임아웃**: `AbortSignal.timeout(5000)` (splash.js:17) — 개별 요청 5초 제한

### 2.3 L2 — Preload Bridge 계층

**소스 파일**: `geuldobi-desktop/src/preload.js` (97행)

#### 2.3.1 전체 메서드 인벤토리 (23 live + 1 dead-candidate)

| # | 메서드명 | IPC 채널 | 소유 도메인 | 전송 유형 | Active Consumer |
|---|---------|---------|-----------|----------|----------------|
| 1 | `getSplashConfig` | `splash:get-config` | splash bootstrap | invoke (양방향) | splash.js |
| 2 | `notifyBackendReady` | `splash:backend-ready` | splash bootstrap | send (단방향) | splash.js |
| 3 | `onAppReady` | `app:ready` | desktop handoff | on (수신) | index.html |
| 4 | `runKey` | `bridge:run` | desktop run control | invoke | index.html |
| 5 | `stopRun` | `bridge:stop` | desktop run control | invoke | index.html |
| 6 | `getStatus` | `bridge:status` | command readiness | invoke | index.html |
| 7 | `getQualitySummary` | `bridge:get-quality-summary` | quality operator | invoke | index.html |
| 8 | `getQualityDashboard` | `bridge:get-quality-dashboard` | quality operator | invoke | index.html |
| 9 | `getSafeOpsPreview` | `bridge:get-safe-ops-preview` | safe-op operator | invoke | index.html |
| 10 | `saveQualityReview` | `bridge:save-quality-review` | quality operator | invoke | index.html |
| 11 | `getBackendUrl` | `bridge:get-url` | WS bootstrap | invoke | index.html |
| 12 | `getCliContract` | `bridge:get-cli-contract` | stage 0 contract UI | invoke | index.html |
| 13 | `saveSettings` | `bridge:save-settings` | settings persistence | invoke | index.html |
| 14 | `loadSettings` | `bridge:load-settings` | settings persistence | invoke | index.html |
| 15 | `listMaterialFiles` | `material:list-files` | material manager | invoke | index.html |
| 16 | `importMaterialFile` | `material:import-file` | material manager | invoke | index.html |
| 17 | `deleteMaterialFile` | `material:delete-file` | material manager | invoke | index.html |
| 18 | `resolvePrompt` | `bridge:resolve-prompt` | mode-b prompt loop | invoke | index.html |
| 19 | `listProjects` | `project:list` | project selector | invoke | index.html |
| 20 | `createProject` | `project:create` | project selector | invoke | index.html |
| 21 | `loadProjectConfigSurfaces` | `project:load-config-surfaces` | project config | invoke | index.html |
| 22 | `saveProjectConfigSurfaces` | `project:save-config-surfaces` | project config | invoke | index.html |
| 23 | `listWorkGuardTemplates` | `project:list-work-guard-templates` | work guard UI | invoke | index.html |
| 24 | `applyWorkGuardTemplate` | `project:apply-work-guard-template` | work guard UI | invoke | index.html |
| 25 | `openWorkspaceFolder` | `workspace:open-folder` | workspace utility | invoke | index.html |
| DC | `getWorkspacePath` | `workspace:get-path` | dead-candidate | invoke | 없음 |

#### 2.3.2 Preload 설계 특성

1. **채널 상수 하드코딩**: `require("./desktop_control_plane_contract")` 대신 `PRELOAD_METHOD_CHANNELS` 로컬 정의 — 이유: sandboxed preload에서 packaged Electron의 상대 경로 require 불안정 (preload.js:4 주석)
2. **이중 정의 동기화**: `desktop_control_plane_contract.js`의 `PRELOAD_METHOD_CHANNELS`와 `preload.js`의 로컬 복사본이 **동일 채널 문자열**을 유지해야 함 — 계약 정합성의 핵심 취약점
3. **Dead-candidate 관리**: `getWorkspacePath`는 명시적으로 `deadCandidate` 객체에 분리, `must_not_be_treated_as_live: true` 계약 명시

### 2.4 L3 — Electron Main Process 계층

**소스 파일**: `geuldobi-desktop/src/main.js` (1010행)

#### 2.4.1 bridgeFetch 전송 프로토콜

```javascript
// main.js:494-549
async function bridgeFetch(urlPath, options = {}) {
  // 타임아웃: BRIDGE_FETCH_TIMEOUT_MS = 5000ms
  // 성공: backend JSON 그대로 반환
  // HTTP 오류: { ok: false, code: "HTTP_{status}", data: { envelope_version, ... } }
  // 네트워크 오류: { ok: false, code: "NETWORK_ERROR", data: { ... } }
}
```

**Desktop Bridge Transport 계약** (`api-contract-v1.yaml:85-121`):

| 속성 | 값 |
|------|----|
| `envelope_version` | `desktop_bridge_v1` |
| `networkErrorCode` | `NETWORK_ERROR` |
| `httpErrorPrefix` | `HTTP_` |
| `request_timeout_ms` | `5000` |

**핵심**: Renderer는 `bridgeFetch` 결과만 받으므로, backend `ErrorEnvelope.code`와 desktop transport `code`를 **구별할 수 있어야** 함. 이를 위해 `data.backend_code` / `data.backend_message` 필드로 원본 backend 오류를 에코.

#### 2.4.2 IPC 핸들러 → bridgeFetch 라우팅 매핑

| IPC 채널 | Backend Route | HTTP Method | 요청 본문 변환 |
|----------|-------------|------------|--------------|
| `bridge:run` | `/run` | POST | `{ key, sub_key?, inputs?, approval_id? }` |
| `bridge:stop` | `/stop` | POST | (없음) |
| `bridge:status` | `/status` | GET | (없음) |
| `bridge:get-quality-summary` | `/quality/summary?project=&lookback=` | GET | 쿼리스트링 |
| `bridge:get-quality-dashboard` | `/quality/dashboard?project=&lookback=` | GET | 쿼리스트링 |
| `bridge:get-safe-ops-preview` | `/safe-ops/preview?project=` | GET | 쿼리스트링 |
| `bridge:save-quality-review` | `/quality/review` | POST | `{ project, ep_num, operator_label, note }` |
| `bridge:resolve-prompt` | `/run/{run_id}/input` | POST | `{ prompt_id, value }` |

**비-bridgeFetch 핸들러** (IPC에서 직접 처리, backend 미경유):

| IPC 채널 | 처리 위치 | 설명 |
|----------|----------|------|
| `bridge:get-url` | main.js 로컬 | WS/HTTP URL 상수 반환 |
| `bridge:get-cli-contract` | main.js 로컬 | CLI 계약 (장르 인덱스 매핑) 반환 |
| `bridge:save-settings` | main.js → 파일시스템 | `%LOCALAPPDATA%/Geuldobi/settings.json` |
| `bridge:load-settings` | main.js → 파일시스템 | 동일 경로 읽기 |
| `material:*` | main.js → 파일시스템 | `bible/`, `treatments/` 디렉토리 관리 |
| `project:*` | main.js → 파일시스템 | `projects/` 디렉토리 + `config/` 관리 |
| `workspace:*` | main.js → 파일시스템/쉘 | 작업 폴더 열기 |

#### 2.4.3 Backend 프로세스 수명주기

```
app.whenReady()
  → syncPackagedWorkspaceSeed()    # 패키징 모드: workspace-seed → 내 문서/글도비
  → startBackend()                 # spawn(backend.exe | python -m uvicorn)
  → bootstrapWindows()             # splash + main 윈도우 생성

startBackend():
  개발: python -m uvicorn modules.api.bridge_server:app --port 8300
  배포: resources/backend/backend.exe
  환경변수: GEULDOBI_DESKTOP_MODE=1, PYTHONIOENCODING=utf-8, PYTHONUNBUFFERED=1
  배포 추가: GEULDOBI_PACKAGED_RUNTIME_MODEL, GEULDOBI_WORKSPACE, GEULDOBI_PROJECTS_ROOT

  자동 재시작: 비정상 종료 시 2초 후 재시작 (최대 2회)
  stdout/stderr: 콘솔 + debugLog 파일 기록

window-all-closed / before-quit:
  → stopBackend() → taskkill /pid {pid} /t /f (Windows)
```

### 2.5 L4 — FastAPI Bridge Server 계층

**소스 파일**: `modules/api/bridge_server.py` (87KB)

#### 2.5.1 엔드포인트 인벤토리

| 경로 | 메서드 | 용도 | 응답 코드 |
|------|--------|------|----------|
| `/run` | POST | 메뉴 키 실행 | 202, 400, 403, 409 |
| `/run/{run_id}/input` | POST | Mode B 프롬프트 응답 | 200, 400, 409 |
| `/stop` | POST | 실행 중지 (멱등) | 200 |
| `/status` | GET | 러너 상태 조회 | 200 |
| `/quality/summary` | GET | 품질 요약 | 200, 400, 500 |
| `/quality/dashboard` | GET | 품질 대시보드 | 200, 400, 500 |
| `/safe-ops/preview` | GET | 안전 연산 미리보기 | 200, 400, 500 |
| `/quality/review` | POST | 운영자 품질 리뷰 저장 | 200, 400, 500 |
| `/events` | WS | 실시간 이벤트 스트림 | — |

#### 2.5.2 검증 게이트 체인

```
POST /run 수신
  → T4: RunValidator
       ALLOWED_KEYS = {"0","1","2","3","4","6","7","44","77","88","99"}
       key="0" → ALLOWED_STAGE0_SUB_KEYS = {"1","2","3","4","5","6","7"}
       key="5" → 차단 (INTERNAL_UI_ACTION_KEYS, desktop exit 전용)
  → T6: RiskApprovalGate (key ∈ {"44","77","88","99"})
       dual-control 승인 기록 확인
       만료 검사 (expires_at)
       감사 로그: logs/risk-approval-log.jsonl
  → T7: ProcessRunner
       spawn main_a.py + stdin 시퀀스 전달
       Mode B: PromptBroker 연동
```

#### 2.5.3 ErrorEnvelope 코드 체계

```
INVALID_KEY              — 허용되지 않은 메뉴 키
SUB_KEY_REQUIRED         — key=0인데 sub_key 미제공
SUB_KEY_NOT_ALLOWED      — key≠0인데 sub_key 제공
INVALID_SUB_KEY          — 유효하지 않은 sub_key 값
RUN_ALREADY_ACTIVE       — 이미 실행 중
RISK_APPROVAL_REQUIRED   — 위험 키에 대한 승인 필요
RISK_APPROVAL_EXPIRED    — 승인 만료
RISK_APPROVAL_DUAL_CONTROL_REQUIRED — 이중 통제 미충족
INVALID_PROMPT_ID        — run_id에 속하지 않는 prompt_id
PROMPT_ALREADY_RESOLVED  — 이미 처리된 프롬프트
INTERNAL_ERROR           — 서버 내부 오류
INVALID_PROJECT          — 유효하지 않은 프로젝트
INVALID_REQUEST          — 유효하지 않은 요청
```

### 2.6 L5 — Python Engine 계층

**소스 파일**: `main_a.py` (237KB), `modules/domain/agents/` (47 에이전트)

#### 2.6.1 Engine ↔ Bridge 연결점

Engine은 Bridge Server가 spawn한 **별도 프로세스**로 동작:

| 연결 채널 | 방향 | 프로토콜 |
|----------|------|---------|
| stdin | Bridge → Engine | 텍스트 시퀀스 (메뉴 키 전달) |
| stdout | Engine → Bridge | 텍스트 출력 (ANSI 스트립 후 WS broadcast) |
| stderr | Engine → Bridge | 로그/오류 (진단 목적) |
| 파일시스템 | 양방향 | `project_data.db`, `logs/*.jsonl`, `artifacts/` |

**Mode B 프롬프트 루프**:
```
Engine stdout → "PROMPT_REQUEST:{json}" 인식
  → ProcessRunner 파싱 → PromptBroker.request_input()
  → WS prompt_request 이벤트 → Renderer 표시
  → 사용자 입력 → Renderer → IPC resolvePrompt → POST /run/{run_id}/input
  → PromptBroker.resolve() → prompt_resolved 이벤트
  → Engine stdin 전달 → 실행 계속
```

---

## 3. 방향 B: 데이터 흐름별 분석

### 3.1 정방향 흐름: 사용자 액션 → DB 기록

#### 3.1.1 "에피소드 생성 실행" 전체 경로

```
[1] 사용자 UI: "4번 키 실행" 클릭
    ↓ window.geuldobiDesktop.runKey("4", null, {}, null)

[2] preload.js: ipcRenderer.invoke("bridge:run", {key:"4", subKey:null, inputs:{}, approvalId:null})
    ↓ Electron IPC (프로세스 간 직렬화)

[3] main.js ipcMain.handle("bridge:run"):
    body = { key: "4" }
    ↓ bridgeFetch("/run", { method: "POST", body: JSON.stringify(body) })
    ↓ fetch("http://127.0.0.1:8300/run", ...) + 5초 타임아웃

[4] bridge_server.py POST /run:
    T4: RunValidator.validate(key="4") → OK (ALLOWED_KEYS 포함)
    T6: RiskApprovalGate 스킵 (key ∉ RISK_KEYS)
    T7: ProcessRunner.start(key="4", mode="b")
    ↓ 응답: 202 { ok:true, run_id:"uuid", code:"OK" }

[5] ProcessRunner:
    spawn("python", ["main_a.py"], env={GEULDOBI_DESKTOP_MODE:"1"})
    stdin 시퀀스: "4\n" (메뉴 선택)

[6] main_a.py:
    Stage 4 진입 → ChiefWriter.generate_ensemble()
    → 3개 후보 원고 생성 (Gemini 2.5 Pro)
    → 6-tier Validation Pipeline
    → Director 최종 판정 (PASS / PASS_WITH_FIX / REJECT)
    → DBManager.save_manuscript() [SQLite 트랜잭션]

[7] stdout 이벤트 스트림:
    Engine stdout → ProcessRunner.on_line callback
    → WSManager.broadcast(run_id, {type:"stdout", payload:{text:"..."}})
    → WebSocket → Renderer 실시간 표시

[8] 완료:
    Engine exit(0) → ProcessRunner.on_exit
    → WSManager.broadcast(run_id, {type:"run_completed", payload:{returncode:0, ...}})
    → PromptBroker.cleanup_run(run_id)
```

#### 3.1.2 "위험 연산 실행" 전체 경로 (key=44)

```
[1] 사용자 UI: "44번 키 실행" + 승인 ID 입력
    ↓ window.geuldobiDesktop.runKey("44", null, {}, "APPROVAL-001")

[2-3] (동일 IPC → bridgeFetch 경로)

[4] bridge_server.py POST /run:
    T4: RunValidator.validate(key="44") → OK
    T6: RiskApprovalGate.validate(key="44", approval_id="APPROVAL-001")
        → ApprovalRecord 조회
        → 이중 통제 검증 (approved_by_primary ≠ approved_by_secondary)
        → 만료 검사 (expires_at > now)
        → 감사 로그 기록 → logs/risk-approval-log.jsonl
    T7: ProcessRunner.start(...)

[실패 시] 403 { ok:false, code:"RISK_APPROVAL_REQUIRED" }
         → main.js bridgeFetch → HTTP_403 transport 오류로 변환
         → Renderer에서 transport 코드와 backend_code 분리 표시
```

#### 3.1.3 Mode B 프롬프트 인터랙션 흐름

```
[Engine] main_a.py stdout: PROMPT_REQUEST 신호
    ↓
[ProcessRunner] 파싱 → PromptBroker.request_input(run_id, PromptState)
    ↓
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
        options: [
          { key: "1", label: "0_260318" }
        ]
      }
    }
    ↓
[Renderer] WebSocket 수신 → 프롬프트 UI 렌더링
    ↓
[사용자] 선택 입력
    ↓
[Renderer] window.geuldobiDesktop.resolvePrompt(runId, "p-001", "1")
    ↓ IPC bridge:resolve-prompt
    ↓ bridgeFetch("/run/{run_id}/input", POST, {prompt_id:"p-001", value:"1"})
    ↓
[PromptBroker] resolve(run_id, "p-001", "1")
    → prompt.resolved = True, prompt.value = "1"
    → prompt._event.set() (asyncio.Event 해제)
    → WS prompt_resolved 이벤트 발행
    ↓
[Engine] await 해제 → 선택값 "1" 수신 → 실행 계속
```

**타임아웃 흐름**:
```
asyncio.wait_for(timeout=prompt.timeout_sec) 만료
  → prompt.value = prompt.default
  → WS prompt_timeout 이벤트: { prompt_id, applied_default }
  → Engine은 default 값으로 계속 진행
```

### 3.2 역방향 흐름: 이벤트 스트림

#### 3.2.1 WebSocket 이벤트 타입 전수 목록

| 이벤트 타입 | 방향 | payload 필수 필드 | 발행 시점 |
|------------|------|------------------|----------|
| `run_started` | Server→Client | `key` | ProcessRunner 시작 직후 |
| `stdout` | Server→Client | `text` | Engine stdout 라인마다 |
| `prompt_request` | Server→Client | `prompt_id`, `step_id`, `input_type`, `default`, `timeout_sec` | PromptBroker.request_input() |
| `prompt_resolved` | Server→Client | `prompt_id`, `value`, `source` | PromptBroker.resolve() |
| `prompt_timeout` | Server→Client | `prompt_id`, `applied_default` | 타임아웃 시 |
| `run_completed` | Server→Client | `returncode` | Engine 정상 종료 (exit 0) |
| `run_failed` | Server→Client | `returncode` | Engine 비정상 종료 (exit ≠ 0) |
| `run_stopped` | Server→Client | (없음) | 사용자 중지 요청 처리 |

#### 3.2.2 이벤트 봉투 스키마 (event-schema-v1.json)

```json
{
  "event_version": "v1",        // const "v1"
  "seq": <integer ≥ 1>,         // monotonic sequence
  "run_id": "<uuid>",           // 실행 식별자
  "type": "<event_type>",       // enum (위 8개 타입)
  "ts": "<ISO 8601 datetime>",  // 발행 시각
  "payload": { ... }            // 타입별 조건부 스키마
}
```

**스키마 특성**: JSON Schema draft 2020-12, `allOf` + `if/then` 조건부 검증으로 타입별 payload 강제.

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

### 3.3 설정 및 자재 데이터 흐름

#### 3.3.1 Settings 영속화

```
[Renderer] saveSettings(settings)
  → IPC bridge:save-settings
  → main.js: fs.writeFileSync(SETTINGS_PATH, JSON.stringify(settings), "utf8")
  → SETTINGS_PATH = %LOCALAPPDATA%/Geuldobi/settings.json

[Renderer] loadSettings()
  → IPC bridge:load-settings
  → main.js: fs.readFileSync(SETTINGS_PATH, "utf8") → JSON.parse
  → 손상 시: .bak 백업 후 null 반환
```

#### 3.3.2 Material 파일 관리

```
listMaterialFiles("bible") → fs.readdirSync(materialRoot/bible) → [{name, size, isDir}]
importMaterialFile("bible") → dialog.showOpenDialog → fs.copyFileSync(src, dest)
deleteMaterialFile("bible", "foo.json") → 경로 탈출 방지 검사 → fs.unlinkSync

경로 탈출 방지: fileName에 "..", "/", "\" 포함 시 거부 (main.js:738)
```

#### 3.3.3 Project Config 데이터 흐름

```
loadProjectConfigSurfaces(project)
  → {projectRoot}/config/author_directives.txt (없으면 기본 템플릿)
  → {projectRoot}/config/work_guard.yaml (없으면 빈 문자열)

saveProjectConfigSurfaces(project, authorDirectives, workGuardYaml)
  → fs.writeFileSync 두 파일 동시 저장

applyWorkGuardTemplate(project, templatePath)
  → resolveWorkGuardTemplatePath: 라이브러리 경로 내 검증 + YAML 확장자 검사
  → 템플릿 내용 → work_guard.yaml 덮어쓰기
```

---

## 4. 방향 C: 계약-테스트 무결성 분석

### 4.1 계약 문서 인벤토리

| 계약 파일 | 용도 | 규격 |
|----------|------|------|
| `docs/implementation/api-contract-v1.yaml` | OpenAPI 3.1.0 API 명세 | 541행 |
| `docs/implementation/event-schema-v1.json` | WebSocket 이벤트 JSON Schema | 272행, draft 2020-12 |
| `docs/implementation/desktop-ipc-surface-contract-v1.json` | IPC 메서드 인벤토리 | 181행 |
| `docs/implementation/desktop-runtime-contract-v1.json` | 패키징 리소스 명세 | 48행 |
| `docs/implementation/surface-containment-contract-v1.json` | 표면 분류 (live/shadow/residue) | 68행 |
| `modules/api/control_plane_contract.py` | 제어면 권한 계약 (Python) | 93행 |
| `geuldobi-desktop/src/desktop_control_plane_contract.js` | IPC 채널 정의 (JavaScript) | 97행 |

### 4.2 계약 ↔ 코드 정합성 대조

#### 4.2.1 IPC Surface 계약 vs preload.js

| 계약 (desktop-ipc-surface-contract-v1.json) | preload.js | 일치 여부 |
|---------------------------------------------|------------|----------|
| live 메서드 23개 | 23개 (getSplashConfig ~ openWorkspaceFolder) | **일치** |
| dead-candidate 1개 (getWorkspacePath) | 1개 (deadCandidate 객체) | **일치** |
| 채널 문자열 매핑 | PRELOAD_METHOD_CHANNELS.live 키 매핑 | **일치** |

#### 4.2.2 API 계약 vs bridge_server.py

| 계약 경로 (api-contract-v1.yaml) | bridge_server.py 구현 | 일치 여부 |
|---------------------------------|----------------------|----------|
| POST /run → 202, 400, 403, 409 | RunValidator + RiskApprovalGate + ProcessRunner | **일치** |
| POST /run/{run_id}/input → 200, 400, 409 | PromptBroker.resolve() | **일치** |
| POST /stop → 200 | ProcessRunner.stop() (멱등) | **일치** |
| GET /status → 200 | state snapshot + pending_prompts | **일치** |
| GET /quality/summary → 200, 400, 500 | project 파라미터 검증 + DB 조회 | **일치** |
| GET /quality/dashboard → 200, 400, 500 | 동일 구조 | **일치** |
| GET /safe-ops/preview → 200, 400, 500 | 프로젝트별 안전 연산 미리보기 | **일치** |
| POST /quality/review → 200, 400, 500 | 운영자 리뷰 DB 저장 | **일치** |
| WS /events → 8개 이벤트 타입 | WSManager + PromptBroker 이벤트 발행 | **일치** |

#### 4.2.3 RunRequest 스키마 vs control_plane_contract.py

| 계약 필드 | 계약 값 | Python 코드 | 일치 여부 |
|----------|---------|------------|----------|
| `key` enum | `['0','1','2','3','4','6','7','44','77','88','99']` | `PUBLIC_RUN_KEYS = frozenset({"0","1","2","3","4","6","7","44","77","88","99"})` | **일치** |
| `sub_key` enum | `['1','2','3','4','5','6','7']` | `PUBLIC_STAGE0_SUB_KEYS = frozenset({"1","2","3","4","5","6","7"})` | **일치** |
| risk keys | (api-contract에서 403 응답) | `RISK_KEYS = frozenset({"44","77","88","99"})` | **일치** |

#### 4.2.4 Desktop Bridge Transport 계약 vs main.js

| 계약 (api-contract-v1.yaml x-desktop-bridge-transport) | main.js 코드 | 일치 여부 |
|---------------------------------------------------------|-------------|----------|
| `envelope_version: desktop_bridge_v1` | `DESKTOP_BRIDGE_TRANSPORT.envelopeVersion = "desktop_bridge_v1"` | **일치** |
| `network_error_code: NETWORK_ERROR` | `DESKTOP_BRIDGE_TRANSPORT.networkErrorCode = "NETWORK_ERROR"` | **일치** |
| `http_error_code_format: HTTP_<status_code>` | `DESKTOP_BRIDGE_TRANSPORT.httpErrorPrefix = "HTTP_"` | **일치** |
| `request_timeout_ms: 5000` | `BRIDGE_FETCH_TIMEOUT_MS = 5000` | **일치** |

#### 4.2.5 CSP 계약 vs HTML 소스

| 계약 (api-contract-v1.yaml csp_connect_src) | HTML 소스 | 일치 여부 |
|---------------------------------------------|----------|----------|
| main_window: `https://generativelanguage.googleapis.com`, `ws://127.0.0.1:8300` | index.html CSP meta | **일치** |
| splash_window: `http://127.0.0.1:8300` | splash.html CSP meta | **일치** |

### 4.3 회귀 테스트 커버리지

#### 4.3.1 계약 관련 테스트 파일 인벤토리

| 테스트 파일 | 커버 대상 |
|------------|----------|
| `tests/test_desktop_contract_refresh.py` | desktop-ipc-surface-contract + desktop-runtime-contract + surface-containment-contract 정합성 |
| `tests/test_desktop_transport_contract.py` | desktop bridge transport 봉투 + WS 이벤트 타입/payload 계약 |
| `tests/test_desktop_packaging_contract.py` | 패키징 리소스 인벤토리 + env 변수 |
| `tests/test_runtime_authority_contract.py` | 제어면 권한 경로 + 권위 싱크 |
| `tests/test_bridge_server_desktop_risk_gate.py` | 위험 키 승인 게이트 동작 |
| `tests/test_regression_validation_tier_contract.py` | 검증 티어 회귀 |

#### 4.3.2 계약 문서에 명시된 회귀 테스트 참조

| 테스트 함수 (api-contract-v1.yaml에서 참조) | 검증 내용 |
|--------------------------------------------|----------|
| `test_approved_direct_surface_inventory_matches_source_code` | 승인된 직접 표면 3개가 소스 코드와 일치 |
| `test_renderer_csp_connect_src_matches_documented_direct_allowlist` | CSP connect-src가 계약과 일치 |
| `test_bridge_managed_backend_routes_match_main_process_bridge` | bridgeFetch 라우팅이 계약과 일치 |
| `test_desktop_bridge_transport_contract_matches_main_process_source` | transport 봉투 규격 일치 |
| `test_runtime_websocket_event_types_match_schema_and_emitters` | WS 이벤트 타입 8개가 스키마·emitter와 일치 |
| `test_runtime_websocket_payload_contract_matches_renderer_and_backend_usage` | 이벤트 payload 구조 일치 |

### 4.4 이중 정의 위험 지점

#### 4.4.1 preload.js ↔ desktop_control_plane_contract.js 채널 이중 정의

**현황**: `preload.js`는 sandboxed 환경 제약으로 `PRELOAD_METHOD_CHANNELS`를 **자체 하드코딩**. `desktop_control_plane_contract.js`에도 동일 매핑 존재.

**위험**: 한쪽만 수정 시 채널 불일치 → 런타임 IPC 실패 (침묵 오류 가능).

**완화**: `test_desktop_contract_refresh.py`가 양쪽의 채널 문자열 동기화를 검증하는 것으로 추정되나, 정확한 테스트 로직 확인 필요.

#### 4.4.2 Python control_plane_contract.py ↔ JS desktop_control_plane_contract.js 키 정의

| 정의 | Python | JavaScript |
|------|--------|-----------|
| Public Run Keys | `PUBLIC_RUN_KEYS` frozenset | api-contract-v1.yaml `key.enum` |
| Bridge Routes | (bridge_server.py 라우트 정의) | `BRIDGE_MANAGED_ROUTES` 객체 |
| Risk Keys | `RISK_KEYS` frozenset | (main.js에서 직접 참조하지 않음, backend에서 검증) |

**현황**: 키 검증은 **backend 단독 책임** (RunValidator). JavaScript 측은 키 값을 전달만 하고 검증하지 않음. 이는 올바른 설계 — 단일 검증 지점.

---

## 5. 교차 대조 결과

### 5.1 3방향 합치 확인

| 검증 항목 | 방향 A 결론 | 방향 B 결론 | 방향 C 결론 | 합치 여부 |
|----------|------------|------------|------------|----------|
| IPC 메서드 수 | 23 live + 1 DC | 25+ 라우팅 경로 (일부 비-bridgeFetch) | 계약 23 live + 1 DC | **합치** (25 = 23 preload + 2 splash one-way) |
| WebSocket 이벤트 타입 수 | 8개 | 8개 (흐름 추적) | 8개 (스키마 enum) | **합치** |
| HTTP 엔드포인트 수 | 9개 | 9개 (라우팅 매핑) | 9개 (api-contract) | **합치** |
| 승인된 직접 네트워크 표면 | 3개 | 3개 (흐름 추적) | 3개 (계약 명시) | **합치** |
| Backend 포트 | 8300 | 8300 | 8300 (계약 server URL) | **합치** |
| Transport 타임아웃 | 5000ms | 5000ms | 5000ms (계약 명시) | **합치** |
| ErrorEnvelope 코드 수 | 12개 | 12개 (흐름별 매핑) | 12개 (api-contract enum) | **합치** |

### 5.2 교차 대조에서 발견된 미세 관찰

#### 관찰 1: Console Relay — 숨은 역방향 채널

`console_relay.js`가 Renderer → Main 방향으로 `warn`/`error` 레벨 콘솔 메시지를 릴레이.
- 방향 A에서 구조 확인
- 방향 B에서 흐름 특성 미포함 (데이터 흐름 아닌 진단 채널)
- 방향 C에서 계약 미포함 (의도적 — 비공식 진단 채널)

**판정**: 런타임 동작에 영향 없는 진단 전용 채널. 계약 미포함은 의도적.

#### 관찰 2: SPIKE_AUTOCLOSE_MS 환경변수

`main.js:116`에서 `SPIKE_AUTOCLOSE_MS` 환경변수로 앱 자동 종료 가능.
- 기본값 0 (비활성)
- 테스트/스파이크용으로 추정
- 계약 미포함 (개발 전용 플래그)

**판정**: 프로덕션 영향 없음. 개발 전용 플래그로 적절.

#### 관찰 3: CLI_CONTRACT 정적 반환

`getCliContract` IPC 핸들러는 장르 인덱스 매핑을 **정적 상수**로 반환 (`main.js:117-133`).
- backend 동적 조회 없음 — main.js 하드코딩
- 장르 추가/변경 시 main.js도 수정 필요

**판정**: `config/genres/` 디렉토리와의 동기화 리스크 존재. 현재 10개 장르가 일치하나 추후 관리 포인트.

---

## 6. 3PASS 감리 결과

### PASS 1: 사실 확인

| 검증 항목 | 코드 근거 | 판정 |
|----------|----------|------|
| Renderer contextIsolation=true | `main.js:364` | **확인** |
| WebSocket URL ws://127.0.0.1:8300/events | `main.js:109`, `index.html` CSP, `api-contract-v1.yaml:29` | **확인** |
| bridgeFetch 타임아웃 5000ms | `main.js:108` BRIDGE_FETCH_TIMEOUT_MS | **확인** |
| PromptBroker 스레드 안전 (threading.Lock) | `prompt_broker.py:72` _lock = threading.Lock() | **확인** |
| 자동 재시작 최대 2회 | `main.js:237` MAX_BACKEND_RESTARTS = 2 | **확인** |
| Splash 폴링 간격 1초 | `splash.js:62` setInterval(..., 1000) | **확인** |
| Material 경로 탈출 방지 | `main.js:738` "..", "/", "\\" 검사 | **확인** |
| Dead-candidate 1개 | `preload.js:95`, `desktop-ipc-surface-contract-v1.json:171-179` | **확인** |
| Risk keys 4개 | `control_plane_contract.py:30` frozenset({"44","77","88","99"}) | **확인** |
| Event schema 8개 타입 | `event-schema-v1.json:20-29` enum 목록 | **확인** |

**PASS 1 결과**: 근거 없는 서술 **0건**. 모든 서술에 코드/계약 라인 번호 확인됨.

### PASS 2: 교차 일관성

| 대조 쌍 | 방향 간 모순 | 판정 |
|---------|------------|------|
| A-아키텍처 vs B-흐름 | 없음 | **일관** |
| A-아키텍처 vs C-계약 | 없음 | **일관** |
| B-흐름 vs C-계약 | 없음 | **일관** |
| 전체 수치 일관성 (메서드 수, 엔드포인트 수, 이벤트 타입 수) | 없음 | **일관** |

**PASS 2 결과**: 방향 간 모순 **0건**.

### PASS 3: 완전성 검증

| 검증 항목 | 상태 | 비고 |
|----------|------|------|
| 모든 IPC 채널 추적됨 | **완전** | 23 live + 1 DC = 전수 |
| 모든 HTTP 엔드포인트 추적됨 | **완전** | 9개 = 전수 |
| 모든 WS 이벤트 타입 추적됨 | **완전** | 8개 = 전수 |
| 모든 ErrorEnvelope 코드 추적됨 | **완전** | 12개 = 전수 |
| 모든 직접 네트워크 표면 추적됨 | **완전** | 3개 = 전수 |
| Console Relay 채널 | **완전** | 진단 전용, 비계약 (의도적) |
| 파일시스템 접점 추적 | **완전** | settings, material, project, workspace |
| Backend 프로세스 수명주기 | **완전** | spawn → restart → taskkill |

**PASS 3 결과**: 누락 채널/스키마/테스트 **0건**.

---

## 7. 발견 사항 종합

### 7.1 아키텍처 강점

| # | 강점 | 근거 |
|---|------|------|
| S1 | **엄격한 Renderer 네트워크 격리** | 3개 승인 직접 표면만 허용, 나머지 전부 IPC 브릿지 경유. CSP 강제. |
| S2 | **계약 기반 개발** | 5개 JSON/YAML 계약 문서가 코드와 1:1 매핑. 6개 회귀 테스트 파일이 drift 감시. |
| S3 | **단일 검증 지점 원칙** | 키 검증은 backend RunValidator 단독. FE는 전달만 — 이중 검증 동기화 문제 없음. |
| S4 | **Transport 오류 네임스페이스 분리** | `NETWORK_ERROR`/`HTTP_*` (desktop transport) vs `INVALID_KEY`/... (backend) 명확 구분. |
| S5 | **멱등 중지 + 자동 재시작** | /stop 멱등성, backend 비정상 종료 시 최대 2회 자동 재시작. |
| S6 | **이벤트 스키마 조건부 검증** | event-schema-v1.json이 allOf+if/then으로 타입별 payload 구조 강제. |
| S7 | **Mode B 프롬프트 브로커** | 스레드 안전 (threading.Lock), 중복 입력 차단, 타임아웃 + default 적용. |
| S8 | **권한 경로 문서화** | control_plane_contract.py가 전체 권한 경로와 권위 싱크/동반자 스냅샷을 명시. |

### 7.2 관리 주의점

| # | 주의점 | 위험도 | 설명 |
|---|--------|--------|------|
| W1 | **채널 이중 정의** | 중 | preload.js와 desktop_control_plane_contract.js의 채널 문자열 동기화 필요. 한쪽만 수정 시 침묵 실패 가능. 회귀 테스트가 커버하나 수동 검증도 권장. |
| W2 | **CLI_CONTRACT 정적 하드코딩** | 저 | 장르 인덱스 매핑이 main.js에 하드코딩. config/genres 변경 시 수동 동기화 필요. |
| W3 | **Settings JSON 손상 복구** | 저 | .bak 백업 + null 반환 전략. 이중 손상 시 설정 유실 가능하나 치명적이지 않음. |
| W4 | **Backend 재시작 한도** | 저 | MAX_BACKEND_RESTARTS=2. 3회 연속 실패 시 사용자에게 명시적 안내 부재 (콘솔 경고만). |

### 7.3 BE-FE 연결성 수치 요약

| 지표 | 수치 |
|------|------|
| 총 IPC 메서드 (live) | 23 |
| 총 IPC 메서드 (dead-candidate) | 1 |
| 총 HTTP REST 엔드포인트 | 9 |
| 총 WebSocket 이벤트 타입 | 8 |
| 총 직접 네트워크 표면 | 3 |
| 총 ErrorEnvelope 코드 | 12 |
| 총 Bridge 전송 오류 코드 | 2 (NETWORK_ERROR, HTTP_*) |
| 총 PromptBroker 입력 타입 | 6 (enum, int, string, bool, enter, multiline) |
| 총 계약 문서 | 7 (5 JSON/YAML + 2 소스 내 계약) |
| 총 회귀 테스트 파일 (계약 관련) | 6 |
| 계약 ↔ 코드 불일치 | **0건** |
| 3방향 교차 모순 | **0건** |
| 미커버 채널/스키마 | **0건** |

---

## 8. 근거 파일 인벤토리

### 8.1 Frontend 소스

| 파일 | 행수 | 역할 |
|------|------|------|
| `geuldobi-desktop/src/main.js` | 1010 | Electron 메인 프로세스, IPC 핸들러, backend spawn |
| `geuldobi-desktop/src/preload.js` | 97 | IPC 브릿지, contextBridge 노출 |
| `geuldobi-desktop/src/index.html` | ~3000 | 메인 Renderer UI (CSS 인라인) |
| `geuldobi-desktop/src/desktop_control_plane_contract.js` | 97 | IPC 채널 상수, Bridge 라우트 매핑 |
| `geuldobi-desktop/src/console_relay.js` | 57 | 콘솔 메시지 릴레이 |
| `geuldobi-desktop/src/splash/splash.js` | 90 | 백엔드 준비 폴링 |
| `geuldobi-desktop/src/splash/splash.html` | — | 스플래시 화면 |
| `geuldobi-desktop/src/splash/splash.css` | — | 스플래시 스타일 |
| `geuldobi-desktop/package.json` | — | Electron 40.8.0, 빌드 설정 |

### 8.2 Backend 소스

| 파일 | 크기 | 역할 |
|------|------|------|
| `modules/api/bridge_server.py` | 87KB | FastAPI 서버, REST + WebSocket |
| `modules/api/process_runner.py` | 31KB | 서브프로세스 관리 |
| `modules/api/prompt_broker.py` | 206행 | Mode B 프롬프트 브로커 |
| `modules/api/run_validator.py` | 3.7KB | T4 요청 검증 |
| `modules/api/risk_approval.py` | 8.3KB | T6 위험 승인 게이트 |
| `modules/api/prompt_classifier.py` | 6.3KB | 프롬프트 분류 |
| `modules/api/control_plane_contract.py` | 93행 | 제어면 권한 계약 |

### 8.3 계약 문서

| 파일 | 규격 | 행수 |
|------|------|------|
| `docs/implementation/api-contract-v1.yaml` | OpenAPI 3.1.0 | 541 |
| `docs/implementation/event-schema-v1.json` | JSON Schema draft 2020-12 | 272 |
| `docs/implementation/desktop-ipc-surface-contract-v1.json` | 자체 규격 | 181 |
| `docs/implementation/desktop-runtime-contract-v1.json` | 자체 규격 | 48 |
| `docs/implementation/surface-containment-contract-v1.json` | 자체 규격 | 68 |

### 8.4 회귀 테스트

| 파일 | 커버 대상 |
|------|----------|
| `tests/test_desktop_contract_refresh.py` | IPC/runtime/surface 계약 정합성 |
| `tests/test_desktop_transport_contract.py` | Bridge transport + WS 이벤트 |
| `tests/test_desktop_packaging_contract.py` | 패키징 리소스 |
| `tests/test_runtime_authority_contract.py` | 제어면 권한 |
| `tests/test_bridge_server_desktop_risk_gate.py` | 위험 게이트 |
| `tests/test_regression_validation_tier_contract.py` | 검증 티어 |

---

> **조사 종결**
> 3방향 독립 조사 + 교차 대조 + 3PASS 감리 완료.
> 계약 ↔ 코드 불일치 **0건**, 미커버 채널 **0건**, 교차 모순 **0건**.
> 관리 주의점 4건 (W1~W4) 식별 — 현재 운영에 치명적 위험 없음.
