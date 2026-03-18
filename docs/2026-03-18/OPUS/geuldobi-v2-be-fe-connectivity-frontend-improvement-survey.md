# BE-FE 연결성 및 프론트엔드 개선점 전역 조사

Date: 2026-03-18
Status: final (3-pass audited)
Scope: geuldobi-desktop/src/* ↔ modules/api/* 전 연결 표면
Applies To: Electron Renderer, Preload, Main Process, FastAPI bridge_server
Related Contracts:
  - docs/implementation/desktop-ipc-surface-contract-v1.json
  - docs/implementation/api-contract-v1.yaml
  - docs/implementation/desktop-runtime-contract-v1.json

---

## 1. 조사 범위 및 방법론

### 검사 대상

| 계층 | 파일 | 규모 |
|------|------|------|
| Preload | `geuldobi-desktop/src/preload.js` (97줄) | 25 live + 1 dead candidate 메서드 |
| Main Process | `geuldobi-desktop/src/main.js` (~1010줄) | 25개 ipcMain.handle/on 핸들러 |
| Control Plane Contract | `geuldobi-desktop/src/desktop_control_plane_contract.js` (97줄) | IPC 채널 + 라우트 SSOT |
| Renderer | `geuldobi-desktop/src/index.html` (8266줄) | 단일 파일 UI + 바닐라 JS |
| Splash | `geuldobi-desktop/src/splash/splash.js` (90줄) | 백엔드 상태 폴링 |
| FastAPI | `modules/api/bridge_server.py` (~2155줄) | 9개 HTTP/WS 엔드포인트 |
| Process Runner | `modules/api/process_runner.py` (~800줄) | subprocess 관리, Mode A/B |
| Prompt Broker | `modules/api/prompt_broker.py` (206줄) | Mode B 프롬프트 상태 관리 |

### 검사 방법

- 정적 코드 분석: 호출-피호출 추적 (preload → IPC channel → main.js handler → bridgeFetch → FastAPI endpoint)
- `desktop_control_plane_contract.js`를 IPC 채널 정의 SSOT로 사용하여 preload.js / main.js 양방향 대조
- bridge_server.py `@app.get/post/websocket` 데코레이터 전수 열거
- index.html 내 `window.geuldobiDesktop.*`, `fetch()`, `new WebSocket()` 호출 전수 검색

---

## 2. 아키텍처 현황 요약

### 2.1 3계층 IPC 구조

```
┌─────────────────────────────────┐
│  Renderer (index.html)          │
│  window.geuldobiDesktop.*       │
│  ← contextBridge 노출 API      │
└──────────┬──────────────────────┘
           │ ipcRenderer.invoke / .send
           ▼
┌──────────────────────────────────┐
│  Preload (preload.js)            │
│  contextBridge.exposeInMainWorld │
│  25 live + 1 dead candidate      │
└──────────┬───────────────────────┘
           │ IPC channel
           ▼
┌──────────────────────────────────┐
│  Main Process (main.js)          │
│  25개 ipcMain.handle/on          │
│  ├─ 8개: bridgeFetch → FastAPI   │
│  └─ 17개: 로컬 자체 처리         │
└──────────┬───────────────────────┘
           │ HTTP fetch (bridgeFetch)
           ▼
┌──────────────────────────────────┐
│  FastAPI bridge_server.py        │
│  http://127.0.0.1:8300           │
│  9개 엔드포인트 (8 HTTP + 1 WS)  │
└──────────────────────────────────┘
```

### 2.2 직접 네트워크 표면 (Renderer → Backend 직접, IPC 비경유)

| # | 표면 | 소스 위치 | 대상 |
|---|------|-----------|------|
| 1 | WebSocket | index.html:6173 | `ws://127.0.0.1:8300/events` |
| 2 | Splash status polling | splash/splash.js:14 | `http://127.0.0.1:8300/status` |
| 3 | Gemini API 키 검증 | index.html:7715 | `https://generativelanguage.googleapis.com/v1beta/models` |

### 2.3 데이터 흐름 다이어그램

```
사용자 입력 (실행 버튼 클릭)
  │
  ▼
Renderer: window.geuldobiDesktop.runKey(key, subKey, inputs)
  │ ipcRenderer.invoke("bridge:run", {...})
  ▼
Preload: 채널 "bridge:run" 전달
  │
  ▼
Main: ipcMain.handle("bridge:run") → bridgeFetch("/run", POST)
  │ HTTP POST http://127.0.0.1:8300/run
  ▼
bridge_server.py: POST /run
  │ T4(RunValidator) → T6(RiskApprovalGate) → ProcessRunner.start()
  │ 202 Accepted + run_id 반환
  ▼
WS /events: run_started → stdout → run_completed/run_failed 이벤트 스트림
  │
  ▼
Renderer: _ws.onmessage → _handleWsEvent() → UI 업데이트
```

---

## 3. BE-FE 연결 전체 맵

### 3.1 Bridge-Managed 경로 (8개: IPC → bridgeFetch → FastAPI)

| # | Preload 메서드 | IPC 채널 | Main Handler | HTTP 경로 | HTTP 메서드 | bridge_server.py 위치 |
|---|---------------|----------|--------------|-----------|-------------|----------------------|
| 1 | `runKey` | `bridge:run` | main.js:551 | `/run` | POST | L1839 |
| 2 | `stopRun` | `bridge:stop` | main.js:561 | `/stop` | POST | L1982 |
| 3 | `getStatus` | `bridge:status` | main.js:566 | `/status` | GET | L2000 |
| 4 | `getQualitySummary` | `bridge:get-quality-summary` | main.js:578 | `/quality/summary` | GET | L2043 |
| 5 | `getQualityDashboard` | `bridge:get-quality-dashboard` | main.js:588 | `/quality/dashboard` | GET | L2060 |
| 6 | `getSafeOpsPreview` | `bridge:get-safe-ops-preview` | main.js:598 | `/safe-ops/preview` | GET | L2074 |
| 7 | `saveQualityReview` | `bridge:save-quality-review` | main.js:603 | `/quality/review` | POST | L2090 |
| 8 | `resolvePrompt` | `bridge:resolve-prompt` | main.js:615 | `/run/{run_id}/input` | POST | L1952 |

**BRIDGE_MANAGED_ROUTES SSOT**: `desktop_control_plane_contract.js:77-85` (7개 정적 경로) + `buildRunInputRoute()` (1개 동적 경로, L87-89)

### 3.2 로컬 전용 경로 (17개: Main Process 자체 처리, 백엔드 미경유)

| # | Preload 메서드 | IPC 채널 | Main Handler | 역할 |
|---|---------------|----------|--------------|------|
| 1 | `getBackendUrl` | `bridge:get-url` | main.js:570 | WS/HTTP URL 반환 |
| 2 | `getCliContract` | `bridge:get-cli-contract` | main.js:574 | CLI 계약 상수 반환 |
| 3 | `saveSettings` | `bridge:save-settings` | main.js:624 | AppData JSON 쓰기 |
| 4 | `loadSettings` | `bridge:load-settings` | main.js:636 | AppData JSON 읽기 |
| 5 | `listMaterialFiles` | `material:list-files` | main.js:672 | bible/treatments 파일 목록 |
| 6 | `importMaterialFile` | `material:import-file` | main.js:694 | 파일 대화상자 → 복사 |
| 7 | `deleteMaterialFile` | `material:delete-file` | main.js:733 | 재료 파일 삭제 |
| 8 | `listProjects` | `project:list` | main.js:846 | 프로젝트 디렉토리 목록 |
| 9 | `createProject` | `project:create` | main.js:867 | 새 프로젝트 디렉토리 생성 |
| 10 | `loadProjectConfigSurfaces` | `project:load-config-surfaces` | main.js:888 | author_directives + work_guard 읽기 |
| 11 | `saveProjectConfigSurfaces` | `project:save-config-surfaces` | main.js:903 | author_directives + work_guard 쓰기 |
| 12 | `listWorkGuardTemplates` | `project:list-work-guard-templates` | main.js:922 | YAML 템플릿 열거 |
| 13 | `applyWorkGuardTemplate` | `project:apply-work-guard-template` | main.js:935 | 템플릿 → 프로젝트 적용 |
| 14 | `openWorkspaceFolder` | `workspace:open-folder` | main.js:956 | shell.openPath로 탐색기 열기 |
| 15 | `getSplashConfig` | `splash:get-config` | main.js:479 | 스플래시 설정 반환 |
| 16 | `notifyBackendReady` | `splash:backend-ready` | main.js:487 | 스플래시 → 메인 전환 트리거 |
| 17 | `onAppReady` | `app:ready` | main.js:460 (send) | 메인 윈도우 표시 알림 |

**참고**: `notifyBackendReady`는 `ipcRenderer.send` (단방향), `onAppReady`는 `ipcRenderer.on` (이벤트 리스너). 나머지는 모두 `ipcRenderer.invoke` (양방향 request-response).

### 3.3 Renderer 직접 접근 경로 (3개)

| # | 표면 | 소스 | 대상 URL | 비고 |
|---|------|------|----------|------|
| 1 | WebSocket 이벤트 스트림 | index.html:6168-6222 | `ws://127.0.0.1:8300/events` | 실시간 run 이벤트 수신, 자동 재연결 (3초) |
| 2 | Splash status 폴링 | splash/splash.js:12-62 | `http://127.0.0.1:8300/status` | 1초 간격, 최대 30회 실패 허용 |
| 3 | Gemini API 키 검증 | index.html:7715-7725 | `https://generativelanguage.googleapis.com` | 설정 탭에서 API 키 테스트용 |

**CSP 정합성**: index.html:6의 `connect-src` 지시문에 `ws://127.0.0.1:8300`과 `https://generativelanguage.googleapis.com`이 명시 허용됨. splash.html은 별도 CSP 관리.

### 3.4 Dead/Orphan 엔드포인트

| # | 메서드 | IPC 채널 | 분류 | 위치 |
|---|--------|----------|------|------|
| 1 | `getWorkspacePath` | `workspace:get-path` | **dead candidate** | preload.js:32-34 (`deadCandidate` 객체에 명시 분류), main.js:965-968 (핸들러 존재) |

**상세 분석**:
- preload.js에서 `PRELOAD_METHOD_CHANNELS.deadCandidate`에 명시적으로 분류됨 (L32-34)
- 주석: "Dead-candidate compatibility surface. No active renderer consumer today." (preload.js:94, main.js:964)
- `contextBridge`를 통해 `window.geuldobiDesktop.getWorkspacePath`로 노출은 되어 있으나 (preload.js:95), index.html에서 호출하는 코드 없음
- main.js에 `ipcMain.handle(IPC_CHANNELS.workspace.getPath, ...)` 핸들러는 유지 중 (main.js:965-968)
- `desktop_control_plane_contract.js`의 `IPC_CHANNELS.workspace.getPath`에 정의 존재 (L40)
- **판정**: 코드와 주석이 dead candidate임을 명확히 선언. 기능적으로 `openWorkspaceFolder`가 대체하고 있으며, 경로 반환만 필요한 소비자가 없음

---

## 4. 연결 지점별 건강도 평가

### 4.1 평가 기준

| 등급 | 정의 |
|------|------|
| **Active** | 호출-핸들러-엔드포인트 체인 완결, 실제 소비자 존재 |
| **Degraded** | 체인은 완결이나 일부 결함(에러 핸들링 누락, 타임아웃 미설정 등) |
| **Dead** | 코드가 존재하나 소비자 없음, 명시적 dead 분류 |
| **Orphan** | 한쪽만 존재 (핸들러는 있으나 호출 없음, 또는 그 반대) |

### 4.2 Bridge-Managed 8개 평가표

| # | 메서드 | 등급 | 근거 |
|---|--------|------|------|
| 1 | `runKey` | **Active** | Renderer 실행 버튼 → IPC → bridgeFetch → POST /run 완결 |
| 2 | `stopRun` | **Active** | Renderer 정지 버튼 → IPC → bridgeFetch → POST /stop 완결 |
| 3 | `getStatus` | **Active** | WS open/close 시 `_syncRuntimeStatus()` 자동 호출 (index.html:6188, 6218) |
| 4 | `getQualitySummary` | **Active** | `refreshQualitySummary()` 호출 체인 존재 |
| 5 | `getQualityDashboard` | **Active** | 품질 대시보드 탭 활성화 시 호출 |
| 6 | `getSafeOpsPreview` | **Active** | Safe Ops 패널 렌더링 시 호출 |
| 7 | `saveQualityReview` | **Active** | 운영자 품질 관측 저장 UI 연결 |
| 8 | `resolvePrompt` | **Active** | Mode B 프롬프트 응답 UI 연결 (index.html:6376 등) |

### 4.3 로컬 전용 17개 평가표

| # | 메서드 | 등급 | 근거 |
|---|--------|------|------|
| 1 | `getBackendUrl` | **Active** | `_connectWebSocket()` 호출 시 wsUrl 획득 (index.html:6172) |
| 2 | `getCliContract` | **Active** | Renderer 초기화 시 CLI 계약 로딩 |
| 3 | `saveSettings` | **Active** | 설정 변경 시 자동 저장 (index.html:5983, 7961) |
| 4 | `loadSettings` | **Active** | 앱 초기화 시 저장된 설정 복원 |
| 5 | `listMaterialFiles` | **Active** | 재료 파일 목록 UI 렌더링 |
| 6 | `importMaterialFile` | **Active** | 파일 가져오기 버튼 연결 |
| 7 | `deleteMaterialFile` | **Active** | 파일 삭제 버튼 연결 |
| 8 | `listProjects` | **Active** | 프로젝트 선택 드롭다운 렌더링 |
| 9 | `createProject` | **Active** | 프로젝트 생성 UI 연결 |
| 10 | `loadProjectConfigSurfaces` | **Active** | 프로젝트 선택 시 설정 로딩 |
| 11 | `saveProjectConfigSurfaces` | **Active** | 설정 저장 버튼 연결 |
| 12 | `listWorkGuardTemplates` | **Active** | 워크가드 템플릿 목록 렌더링 (index.html:7686) |
| 13 | `applyWorkGuardTemplate` | **Active** | 템플릿 적용 버튼 (index.html:7805) |
| 14 | `openWorkspaceFolder` | **Active** | 작업 폴더 열기 버튼 연결 |
| 15 | `getSplashConfig` | **Active** | splash.js:71에서 DOMContentLoaded 시 호출 |
| 16 | `notifyBackendReady` | **Active** | splash.js:35에서 /status idle 감지 후 호출 |
| 17 | `onAppReady` | **Active** | main.js:460에서 switchToMain 시 send, Renderer에서 이벤트 수신 |

### 4.4 직접 접근 3개 평가표

| # | 표면 | 등급 | 근거 |
|---|------|------|------|
| 1 | WebSocket `/events` | **Active** | 앱 초기화 시 자동 연결, 재연결 로직 포함 (index.html:6168-6222) |
| 2 | Splash polling | **Active** | splash.js:41-62 1초 간격 폴링, 성공 시 전환 |
| 3 | Gemini API 키 테스트 | **Active** | 설정 탭 테스트 버튼 동작 (index.html:7707-7725) |

### 4.5 Dead Candidate 1개 상세 분석

| 항목 | 상세 |
|------|------|
| 메서드 | `getWorkspacePath` |
| IPC 채널 | `workspace:get-path` |
| 등급 | **Dead** |
| Preload 선언 | preload.js:32-34 (`deadCandidate` 객체 내 분류) |
| Preload 노출 | preload.js:95 (`window.geuldobiDesktop.getWorkspacePath`) |
| Main 핸들러 | main.js:965-968 (존재, 동작 가능) |
| Renderer 호출 | **없음** (index.html 내 `getWorkspacePath` 호출 0건) |
| 대체 경로 | `openWorkspaceFolder` (같은 경로를 반환하면서 탐색기도 열어줌) |
| 위험도 | 매우 낮음 — 기능 중복, 호출자 부재, 명시적 dead 분류 |

### 4.6 종합 점수

| 분류 | Active | Degraded | Dead | Orphan | 합계 |
|------|--------|----------|------|--------|------|
| Bridge-Managed | 8 | 0 | 0 | 0 | 8 |
| 로컬 전용 | 17 | 0 | 0 | 0 | 17 |
| 직접 접근 | 3 | 0 | 0 | 0 | 3 |
| Dead Candidate | 0 | 0 | 1 | 0 | 1 |
| **합계** | **28** | **0** | **1** | **0** | **29** |

**건강도: 28/29 Active (96.6%)**

---

## 5. 프론트엔드 아키텍처 현황 분석

### 5.1 단일 파일 구조

`index.html` 8266줄 = CSS + HTML + JS 모놀리스:

| 영역 | 줄 범위 | 줄 수 (약) |
|------|---------|-----------|
| `<style>` (CSS) | L8 – L2772 | ~2765줄 |
| `<body>` (HTML 마크업) | L2773 – L3486 | ~714줄 |
| `<script>` (JavaScript) | L3487 – L8264 | ~4778줄 |
| **합계** | | **~8266줄** |

### 5.2 기술 스택

- 바닐라 JavaScript (프레임워크 없음)
- 번들러 없음 (raw inline `<script>`)
- 외부 라이브러리 없음 (lucide-icons 외)
- CSS 전체 inline (`<style>` 블록)

### 5.3 전역 상태 관리

주요 전역/모듈 스코프 상태 변수:

| 변수 | 위치 | 역할 |
|------|------|------|
| `officeState` | index.html:3581 | 메인 앱 상태 객체 (30+ 필드) |
| `_backendConnected` | index.html:5826 | WS 연결 상태 boolean |
| `_ws` | index.html:5827 | WebSocket 인스턴스 |
| `_wsReconnectTimer` | index.html:5828 | 재연결 타이머 |
| `_commandPathReady` | index.html:5829 | bridge /status 정상 응답 여부 |
| `_statusSyncInFlight` | index.html:5830 | 상태 동기화 Promise 중복 방지 |
| `_pendingPromptQueue` | index.html:5831 | Mode B 프롬프트 큐 |
| `_currentPrompt` | index.html:6344 | 현재 활성 프롬프트 상태 |
| `_bootPhase` | index.html:6345 | Stage 0 부트 단계 플래그 |
| `_safeOpsConfirmResolve` | index.html:3667 | Safe Ops 확인 콜백 |
| `_clickBubble` | index.html:3731 | UI 클릭 버블 상태 |
| `_noticeCursor`, `_noticeX`, ... | index.html:5755-5759 | 공지 마키 상태 |

**문제점**: 상태가 여러 `let` 변수로 분산되어 있어 상태 간 의존관계 파악과 디버깅이 어려움.

### 5.4 UI 구조

- **레이아웃**: CSS Grid 3행 (`grid-template-rows: auto auto 1fr`)
  - topbar: 프로젝트 선택, 액션 버튼
  - workspace-nav: 탭 네비게이션
  - workspace: 메인 콘텐츠 영역
- **탭 기반**: 실행(사무실), 품질 대시보드, 설정
- **Canvas 렌더링**: 사무실 시뮬레이션 (officeCanvas)
- **실시간 업데이트**: WS 이벤트 → 로그 스트림, 상태 배지, 품질 레이더

### 5.5 보안

| 항목 | 상태 | 위치 |
|------|------|------|
| `contextIsolation` | `true` | main.js:365 |
| `nodeIntegration` | `false` | main.js:366 |
| CSP | 적용 | index.html:6 |
| CSP `script-src` | `'self' 'unsafe-inline'` | 인라인 스크립트 허용 (단일 파일 구조상 필요) |
| CSP `connect-src` | `ws://127.0.0.1:8300 https://generativelanguage.googleapis.com` | 허용 도메인 2건 |
| 경로 탈출 방지 | 적용 | main.js:738 (deleteMaterialFile), main.js:833 (resolveWorkGuardTemplatePath) |

### 5.6 에러 핸들링

**`.catch(() => {})` 무시 패턴** — 8건 확인:

| # | 위치 | 컨텍스트 |
|---|------|---------|
| 1 | index.html:5983 | `saveSettings` 실패 무시 |
| 2 | index.html:6222 | `getBackendUrl` 실패 무시 |
| 3 | index.html:6253 | 상태 동기화 실패 무시 |
| 4 | index.html:6376 | `resolvePrompt` (자동 "5" 응답) 실패 무시 |
| 5 | index.html:7686 | `refreshWorkGuardTemplateList` 실패 무시 |
| 6 | index.html:7800 | 워크가드 템플릿 목록 새로고침 실패 무시 |
| 7 | index.html:7805 | `applySelectedWorkGuardTemplate` 실패 무시 |
| 8 | index.html:7961 | `saveSettings` 실패 무시 |

**영향도**: 대부분 비핵심 경로(설정 저장, 템플릿 목록)이나, #4의 `resolvePrompt` 자동 응답 실패 무시는 Mode B 실행 흐름에서 사일런트 오류를 유발할 수 있음.

---

## 6. 프론트엔드 개선점 (우선순위별)

### P0 — 즉시 (리스크 최소, 코드 변경 최소)

| # | 개선 항목 | 근거 | 예상 작업량 |
|---|----------|------|------------|
| 1 | Dead candidate `workspace:get-path` 정리 또는 잔존 의도 문서화 강화 | 코드+주석이 dead 선언하나 핸들러 유지 중 — 삭제 또는 deprecation 주석 통일 | 0.5h |
| 2 | `.catch(() => {})` 무시 패턴 점검 및 최소 `console.warn` 로깅 추가 | 8건 중 최소 `resolvePrompt` (index.html:6376)은 사일런트 실패 위험 | 1h |
| 3 | `_ws.onerror = () => {}` (index.html:6221) 무시 → 최소 로깅 | WS 에러 원인을 전혀 기록하지 않음 | 0.5h |

### P1 — 단기 (1~2주)

| # | 개선 항목 | 근거 | 예상 작업량 |
|---|----------|------|------------|
| 1 | CSS 외부 파일 분리 (~2765줄 → `styles.css`) | 캐싱 이점, 스타일 편집 독립성 | 2h |
| 2 | JavaScript 외부 파일 분리 (최소 3개: `ui.js`, `bridge.js`, `state.js`) | 4778줄 단일 스크립트 → 관심사 분리 | 8h |
| 3 | 전역 상태를 단일 `StateManager` 객체로 통합 | 10+ 분산 변수 → 중앙 관리, 변경 추적 가능 | 4h |
| 4 | CSP에서 `'unsafe-inline'` 제거 (외부 JS/CSS 분리 후 가능) | 보안 강화 — 현재는 단일 파일 구조상 불가피 | P1-1,2 선행 필요 |

### P2 — 중기 (1~2개월)

| # | 개선 항목 | 근거 |
|---|----------|------|
| 1 | **컴포넌트 모듈화**: 실행패널, 사무실패널, 로그패널, 설정패널 분리 | 현재 4778줄 JS가 모든 패널 로직을 혼재 |
| 2 | **빌드 파이프라인 도입** (esbuild 또는 vite) | JS 모듈 분리 후 번들링, 트리쉐이킹, 소스맵 |
| 3 | **TypeScript 점진적 전환** | preload.js, desktop_control_plane_contract.js부터 (IPC 타입 안전성) |
| 4 | **E2E 테스트 인프라** (Playwright) | IPC ↔ FastAPI 통합 경로 회귀 방지 |

### P3 — 장기 (별도 의사결정 게이트)

| # | 개선 항목 | 고려사항 |
|---|----------|---------|
| 1 | **프레임워크 도입 검토** | 프로젝트 규모(8266줄 UI) 대비 Svelte 권장 — 빌드 출력 크기 최소, 러닝커브 낮음 |
| 2 | **다크 모드 / 테마 시스템** | 현재 CSS 변수(`--bg`, `--surface` 등) 기반 → 테마 전환 인프라 준비됨 |
| 3 | **i18n 체계화** | 현재 한국어 하드코딩 — 다국어 필요 시 메시지 키 추출 |
| 4 | **a11y 체계화** | 시맨틱 HTML, ARIA 속성, 키보드 네비게이션 보강 |

---

## 7. TF 구성안

### 7.1 역할 정의

| 역할 | 인원 | 핵심 책임 |
|------|------|----------|
| FE 리드 | 1명 | 파일 분리 설계, 빌드 파이프라인 선정, 코드 리뷰 |
| FE 개발 | 1~2명 | CSS/JS 분리 실행, 컴포넌트화, StateManager 구현 |
| QA | 1명 | 회귀 테스트 — IPC 연결 무결성, WS 이벤트 스트림 무결성 |
| BE 리뷰어 | 0.5명 (겸직) | API 계약 무변경 확인, bridge_server.py 측 영향 없음 검증 |

### 7.2 마일스톤

| Phase | 범위 | 산출물 | 기간 |
|-------|------|--------|------|
| Phase 1 (P0+P1) | 데드코드 정리 + 파일 분리 + 상태 통합 | `styles.css`, `ui.js`, `bridge.js`, `state.js`, CSP 강화 | 2주 |
| Phase 2 (P2) | 컴포넌트화 + 빌드 도입 + TS 전환 시작 | esbuild/vite 설정, 패널 모듈 4개, preload.d.ts | 6주 |
| Phase 3 (P3) | 프레임워크 전환 | **별도 의사결정 게이트** 필요 — 현재 바닐라 JS로도 동작하므로 ROI 검토 | TBD |

### 7.3 위험 요소 및 제약

| # | 위험 | 완화 방안 |
|---|------|----------|
| 1 | 8266줄 단일 파일 분리 시 회귀 리스크 | IPC 채널 전수 테스트 (28 Active 경로 + 3 직접 접근), WS 이벤트 스트림 E2E |
| 2 | Electron 보안 설정 유지 필수 | `contextIsolation=true`, `nodeIntegration=false` 불변, CSP `'unsafe-inline'` 제거 방향 |
| 3 | API 계약 변경 없음 원칙 | FE 리팩토링은 Renderer 내부만 — preload.js, main.js, bridge_server.py 계약 불변 |
| 4 | Canvas 렌더링 로직 분리 복잡도 | 사무실 시뮬레이션(officeCanvas)은 독립 모듈로 추출 가능하나, officeState 의존이 깊음 |

---

## 8. 위험 요소 및 제약

### 8.1 CORS 미구현

- **현재 상태**: bridge_server.py에 CORS 미들웨어 없음
- **영향**: 로컬 전용(127.0.0.1:8300)이므로 현재 정상 동작
- **미래 리스크**: 원격 배포 또는 다중 오리진 접근 시 CORS 설정 필요

### 8.2 세션/인증 없음

- **현재 상태**: FastAPI 엔드포인트에 인증 미들웨어 없음
- **영향**: 로컬 신뢰 기반 — Electron Main Process가 유일한 HTTP 클라이언트(bridgeFetch)
- **미래 리스크**: 원격 배포 시 API 키 또는 세션 토큰 인증 추가 필요

### 8.3 WebSocket 단일 채널

- **현재 상태**: `/events` 1개 WS 엔드포인트, 모든 이벤트 타입을 단일 채널로 브로드캐스트
- **영향**: 현재 단일 Renderer 클라이언트이므로 충분
- **미래 리스크**: 다중 윈도우 또는 이벤트 유형별 구독 필터링 필요 시 채널 분리 또는 구독 모델 도입 고려

### 8.4 bridgeFetch 타임아웃

- **현재 상태**: 5초 고정 타임아웃 (`BRIDGE_FETCH_TIMEOUT_MS = 5000`, main.js:108)
- **영향**: `/run` POST는 즉시 202를 반환하므로 문제없으나, 대용량 품질 데이터 조회 시 잠재적 타임아웃
- **미래 리스크**: 프로젝트 규모 확대 시 `/quality/dashboard` 응답 지연 가능

---

## 9. 3-Pass 감리 기록

### Pass 1: 구조와 범위

- [x] 문서 유형이 survey와 일치
- [x] 포함/제외 범위 명시 (§1: geuldobi-desktop/src/* ↔ modules/api/*)
- [x] 관련 계약 문서 참조 정확 (3건 모두 docs/implementation/ 하위에 실재 확인)
- [x] 섹션 순서 적절 (범위→현황→맵→평가→개선→TF→위험→감리)

### Pass 2: 사실적 정확성

- [x] IPC 메서드 수 = preload.js 코드와 일치
  - live 25개: preload.js:5-31 `PRELOAD_METHOD_CHANNELS.live` 객체 키 25개 ✓
  - dead candidate 1개: preload.js:32-34 `deadCandidate.getWorkspacePath` ✓
  - 합계 26개 = contextBridge 노출 메서드 26개 (preload.js:37-96) ✓
- [x] API 엔드포인트 수 = bridge_server.py와 일치
  - `@app.post("/run")` L1839 ✓
  - `@app.post("/run/{run_id}/input")` L1952 ✓
  - `@app.post("/stop")` L1982 ✓
  - `@app.get("/status")` L2000 ✓
  - `@app.get("/quality/summary")` L2043 ✓
  - `@app.get("/quality/dashboard")` L2060 ✓
  - `@app.get("/safe-ops/preview")` L2074 ✓
  - `@app.post("/quality/review")` L2090 ✓
  - `@app.websocket("/events")` L2137 ✓
  - 합계 9개 (8 HTTP + 1 WS) ✓
- [x] 파일 경로 정확성 확인 (모든 경로 Glob/Read로 실재 검증)
- [x] 건강도 평가 근거 코드 행번호 대응 — 주요 위치 교차 확인 완료

### Pass 3: 완결성과 일관성

- [x] 개선점 우선순위 논리 일관 (P0=즉시/리스크 최소 → P1=구조적 기반 → P2=모듈화 → P3=프레임워크)
- [x] TF 구성과 마일스톤 정합 (Phase 1 = P0+P1, Phase 2 = P2, Phase 3 = P3)
- [x] 빠진 연결 지점 없음
  - Bridge-Managed 8개 = BRIDGE_MANAGED_ROUTES 7개 + buildRunInputRoute 1개 ✓
  - 로컬 전용 17개 = 25 live - 8 bridge = 17 ✓
  - 직접 접근 3개 = WS + splash polling + Gemini fetch ✓
  - Dead 1개 = workspace:get-path ✓
  - 총합 29개 = 25 live + 1 dead + 3 직접 ✓
- [x] 예상 독자가 수정 없이 활용 가능 — 모든 표에 소스 위치 명시, 판단 근거 기재
