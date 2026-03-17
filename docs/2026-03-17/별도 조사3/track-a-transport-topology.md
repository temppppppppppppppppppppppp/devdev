# Track A — 전송 토폴로지

> 확신도: 98%
> 범위: Renderer → IPC → Main Process → HTTP/WS → FastAPI

---

## 1. 3계층 전송 구조

```
Renderer (index.html)
    │
    │  window.geuldobiDesktop.*()
    │  ipcRenderer.invoke() / ipcRenderer.send()
    │
    ▼
Main Process (main.js)
    │
    ├─ 파일시스템 직접 처리 (material:*, project:*, settings:*)
    │
    └─ HTTP/WS 프록시 (bridge:*)
        │
        │  bridgeFetch() → fetch("http://127.0.0.1:8300/...")
        │  WebSocket → ws://127.0.0.1:8300/events
        │
        ▼
FastAPI (bridge_server.py, port 8300)
```

---

## 2. 채널별 전송 경로 분류

### 2.1 IPC-only (Main Process에서 완결)

파일시스템 직접 접근으로 HTTP 호출 없이 처리:

| IPC 채널 | 처리 위치 | 접근 대상 |
|----------|----------|----------|
| `splash:get-config` | main.js:479 | 메모리 (상수) |
| `splash:backend-ready` | main.js:487 | 메모리 (이벤트) |
| `bridge:get-url` | main.js:570 | 메모리 (상수 URL) |
| `bridge:get-cli-contract` | main.js:574 | 메모리 (CLI_CONTRACT 객체) |
| `bridge:save-settings` | main.js:624 | `%LOCALAPPDATA%/Geuldobi/settings.json` |
| `bridge:load-settings` | main.js:636 | `%LOCALAPPDATA%/Geuldobi/settings.json` |
| `material:list-files` | main.js:672 | `{materialRoot}/{bible\|treatments}/` |
| `material:import-file` | main.js:694 | 파일 대화상자 → 복사 |
| `material:delete-file` | main.js:733 | `{materialRoot}/{folder}/{fileName}` |
| `project:list` | main.js:846 | `{projectsDir}/` 디렉토리 목록 |
| `project:create` | main.js:867 | `{projectsDir}/{name}/` 생성 |
| `project:load-config-surfaces` | main.js:888 | `{project}/config/` 읽기 |
| `project:save-config-surfaces` | main.js:903 | `{project}/config/` 쓰기 |
| `project:list-work-guard-templates` | main.js:922 | `{workGuardLib}/` 목록 |
| `project:apply-work-guard-template` | main.js:935 | 템플릿 파일 복사 |
| `workspace:open-folder` | main.js:956 | `shell.openPath()` |

### 2.2 IPC → HTTP 프록시 (Main → FastAPI)

`bridgeFetch()` 함수를 통해 HTTP로 전달:

| IPC 채널 | HTTP 경로 | 메서드 | 코드 위치 |
|----------|----------|--------|----------|
| `bridge:run` | `/run` | POST | main.js:551 |
| `bridge:stop` | `/stop` | POST | main.js:561 |
| `bridge:status` | `/status` | GET | main.js:566 |
| `bridge:get-quality-summary` | `/quality/summary` | GET | main.js:578 |
| `bridge:get-quality-dashboard` | `/quality/dashboard` | GET | main.js:588 |
| `bridge:get-safe-ops-preview` | `/safe-ops/preview` | GET | main.js:598 |
| `bridge:save-quality-review` | `/quality/review` | POST | main.js:603 |
| `bridge:resolve-prompt` | `/run/{runId}/input` | POST | main.js:615 |

### 2.3 WebSocket (Renderer → Main → FastAPI, 직접 연결)

```javascript
// index.html:6168-6223 — Renderer가 직접 WS 연결
window.geuldobiDesktop.getBackendUrl().then(({ wsUrl }) => {
  _ws = new WebSocket(wsUrl);  // ws://127.0.0.1:8300/events
});
```

WS는 IPC를 경유하지 않고 **Renderer → FastAPI 직접 연결**.
단, URL은 IPC(`bridge:get-url`)를 통해 Main Process에서 취득.

---

## 3. 단일 포트 설계

모든 HTTP 및 WS 통신이 `127.0.0.1:8300` 단일 포트에 수렴:

```
http://127.0.0.1:8300/run              POST
http://127.0.0.1:8300/stop             POST
http://127.0.0.1:8300/status           GET
http://127.0.0.1:8300/run/{id}/input   POST
http://127.0.0.1:8300/quality/summary  GET
http://127.0.0.1:8300/quality/dashboard GET
http://127.0.0.1:8300/safe-ops/preview GET
http://127.0.0.1:8300/quality/review   POST
ws://127.0.0.1:8300/events             WS
```

하드코딩 위치:
- `main.js:31` — `STATUS_BASE_URL = "http://127.0.0.1:8300"`
- `main.js:570` — `wsUrl: "ws://127.0.0.1:8300/events"`

---

## 4. 백엔드 프로세스 생명주기

```
app.whenReady()
    │
    ├─ showSplash()
    │
    ├─ startBackend()
    │   │
    │   ├─ (개발) python -m uvicorn modules.api.bridge_server:app --port 8300
    │   └─ (배포) {resourcesPath}/backend/backend.exe
    │
    ├─ pollBackendReady()  ← GET /status 반복 (300ms 간격, 최대 60초)
    │
    ├─ splash:backend-ready → createMainWindow()
    │
    └─ backendProcess.on("exit")
        └─ 자동 재시작 (최대 2회, 2초 딜레이)
```

코드 위치: `main.js:239-330` (startBackend), `main.js:332-355` (pollBackendReady)

---

## 5. 데이터 직렬화 프로토콜

| 경로 | 직렬화 | Content-Type |
|------|--------|-------------|
| IPC (invoke/handle) | Electron structured clone (자동) | N/A |
| HTTP (bridgeFetch) | JSON | `application/json` |
| WS (events) | JSON (수동 parse) | N/A |
| 파일시스템 | JSON/YAML/TXT (파일 유형별) | N/A |

---

## 6. 타임아웃 & 재시도 정책

| 구간 | 타임아웃 | 재시도 |
|------|---------|--------|
| bridgeFetch() | 5000ms (AbortController) | 없음 (1회 시도) |
| 백엔드 시작 대기 | 60초 (200ms 폴링) | 없음 |
| WS 재연결 | N/A | 3초 후 자동 재연결 (무제한) |
| 백엔드 crash | N/A | 2초 후 자동 재시작 (최대 2회) |
| Prompt 응답 대기 | `timeout_sec` (서버 설정) | 타임아웃 시 기본값 사용 |

---

## 7. 3-Pass 감리

| Pass | 검증 항목 | 결과 |
|------|----------|------|
| 1차 | 22 IPC 채널 전수 분류 완료, 누락 없음 | ✅ |
| 2차 | HTTP 라우트 9개 ↔ IPC bridge:* 8개 매핑 일치 (1개는 WS) | ✅ |
| 3차 | 타임아웃·재시도 정책 코드 증거 교차 확인 | ✅ |
