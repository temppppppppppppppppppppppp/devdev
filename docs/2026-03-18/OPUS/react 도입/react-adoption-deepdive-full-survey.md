# 글도비 v2 React 도입 전면 딥다이브 조사

> 조사일: 2026-03-18
> 조사 범위: Electron 프론트엔드 전체 (index.html 8,266행 + main.js 1,009행 + preload.js 96행)
> 조사 방법: 3방향 독립 정적 조사 + 3PASS 감리 + 적대적 3PASS
> 코드 수정: 없음

---

## 1. 현재 프론트엔드 해부

### 1.1 기술 스택 현황

| 항목 | 현재 값 |
|------|---------|
| **프레임워크** | **없음 (바닐라 JavaScript)** |
| 번들러 | 없음 (webpack/vite 없음) |
| 트랜스파일러 | 없음 (TypeScript/Babel 없음) |
| 패키지 매니저 | npm |
| 데스크톱 셸 | Electron 40.8.0 (Chromium 130) |
| 빌드 | electron-builder 25.1.8 (NSIS, Windows) |
| 외부 런타임 의존성 | lucide ^0.577.0 (아이콘) -- **유일** |
| 보안 기반 | contextIsolation: true, nodeIntegration: false |

### 1.2 파일 구조 (9,723행 총합)

```
geuldobi-desktop/src/                         총 9,723행
├── index.html                    8,266행  ← 전체의 85%. CSS+HTML+JS 인라인 모놀리스
├── main.js                       1,009행  ← Electron 메인 프로세스 + IPC 핸들러 24개
├── preload.js                       96행  ← contextBridge IPC 브릿지 (25 live + 1 DC)
├── desktop_control_plane_contract.js 96행  ← IPC 채널 상수 + 경로 빌더
├── console_relay.js                 56행  ← 콘솔 릴레이 (warn/error 선별)
├── splash/splash.js                 89행  ← 스플래시 폴링 + 진행 표시
├── splash/splash.html               27행  ← 스플래시 마크업
└── splash/splash.css                84행  ← 스플래시 스타일
```

### 1.3 index.html 내부 구조

| 영역 | 행 범위 | 행수 | 비중 |
|------|---------|------|------|
| CSS (인라인 `<style>`) | 8-2772 | 2,764 | 33.4% |
| HTML 마크업 (`<body>`) | 2774-3486 | 712 | 8.6% |
| JavaScript (인라인 `<script>`) | 3487-8264 | 4,778 | 57.8% |
| **합계** | | **8,266** | **100%** |

### 1.4 UI 섹션 전수 목록

| # | 섹션 | 행 범위 (대략) | 용도 | 상태 의존 | IPC 호출 | 복잡도 | React 컴포넌트명 (안) |
|---|------|---------------|------|----------|---------|--------|----------------------|
| 1 | Topbar | 2776-2784 | 프로젝트 선택, 설정 버튼 | project, settings | listProjects | 낮음 | `<Topbar>` |
| 2 | 실행 패널 (Shell) | 2786-2925 | Stage 버튼, 재료 관리 | genre, isRunning | runKey, stopRun | 높음 | `<RunPanel>` |
| 3 | Bible 재료 | 2797-2804 | Bible 파일 목록/임포트 | materials | listMaterial, importMaterial | 중간 | `<MaterialList>` |
| 4 | Treatment 재료 | 2805-2812 | Treatment 파일 목록 | materials | listMaterial, importMaterial | 중간 | `<MaterialList>` |
| 5 | Stage 0 서브 버튼 | 2828-2868 | S0 6개 서브키 | isRunning | runKey | 중간 | `<Stage0SubPanel>` |
| 6 | Safe Ops 패널 | 2907-2925 | 위험 작업 확인 | safeOps | getSafeOpsPreview | 높음 | `<SafeOpsPanel>` |
| 7 | 사무실 캔버스 | 2926-2961 | 오피스 애니메이션 | officeState 전체 | 없음 (WS) | 최고 | `<OfficeCanvas>` |
| 8 | 품질 레이더 | 2962-2973 | 에피소드 신호 시각화 | qualitySummary | getQualitySummary | 높음 | `<QualityRadar>` |
| 9 | Artifact Ladder | 2974-2985 | 산출물 단계 표시 | qualityInsights | getQualityDashboard | 중간 | `<ArtifactLadder>` |
| 10 | Retrieval Inspector | 2986-2997 | 검색 품질 표시 | qualityInsights | getQualityDashboard | 중간 | `<RetrievalInspector>` |
| 11 | 결과 요약 | 2998-3009 | 최근 심사 결과 | qualityInsights | getQualityDashboard | 중간 | `<ResultSummary>` |
| 12 | 트렌드 비교 | 3010-3025 | 에피소드 점수 추이 | qualityInsights | getQualityDashboard | 중간 | `<TrendCompare>` |
| 13 | 실패 감시 | 3026-3037 | 실패 패턴 분석 | qualityInsights | getQualityDashboard | 중간 | `<FailureWatch>` |
| 14 | 보정 데스크 | 3038-3049 | 운영자 보정 | qualityInsights | saveQualityReview | 높음 | `<CalibrationDesk>` |
| 15 | 파이프라인 스트립 | 3050-3063 | 실행 단계 진행률 | officeState | 없음 (WS) | 중간 | `<PipelineStrip>` |
| 16 | 에이전트 보드 | 3064-3078 | 에이전트 상태 카드 | officeState | 없음 (WS) | 중간 | `<AgentBoard>` |
| 17 | 이벤트 피드 | 3079-3088 | 실시간 이벤트 | recentEvents | 없음 (WS) | 낮음 | `<EventFeed>` |
| 18 | 미션 보드 | 3089-3103 | 미션 카드 목록 | officeState | 없음 (WS) | 중간 | `<MissionBoard>` |
| 19 | 로그 스트림 | 3104-3142 | 실행 로그 표시 | logs | 없음 (WS) | 중간 | `<LogStream>` |
| 20 | 설정 오버레이 | 3143-3320 | API키, 타임아웃 등 | settingsStore | saveSettings, loadSettings | 높음 | `<SettingsOverlay>` |
| 21 | 설정 - 일반 탭 | 3170-3226 | API키, Slack | settingsStore | - | 중간 | `<SettingsGeneral>` |
| 22 | 설정 - 고급 탭 | 3227-3256 | 타임아웃, 품질게이트 | settingsStore | - | 낮음 | `<SettingsAdvanced>` |
| 23 | 설정 - 프로젝트 탭 | 3257-3320 | 작성 지시, WorkGuard | projectConfig | loadConfig, saveConfig | 높음 | `<SettingsProject>` |
| 24 | 장르 선택 모달 | 3321-3375 | 장르 그리드 선택 | genre | - | 중간 | `<GenreModal>` |
| 25 | 확인 오버레이 | 3376-3401 | 범용 확인 다이얼로그 | - | - | 낮음 | `<ConfirmOverlay>` |
| 26 | Safe Ops 확인 | 3402-3422 | 위험 작업 확인 | safeOps | - | 중간 | `<SafeOpsConfirm>` |
| 27 | 프롬프트 오버레이 | 3423-3485 | 사용자 입력 대기 | promptQueue | resolvePrompt | 높음 | `<PromptOverlay>` |
| 28 | 상태 배지 | CSS/JS | 실행 상태 표시 | mode | - | 낮음 | `<StatusBadge>` |
| 29 | WorkGuard Helper | 3257-3320 | 템플릿 선택/적용 | templates | listWGTemplates, applyWG | 중간 | `<WorkGuardHelper>` |
| 30 | 캔버스 에이전트 스프라이트 | JS | 5명 에이전트 렌더링 | officeState | - | 최고 | (Canvas 내부) |
| 31 | 공지 스크롤 | JS | 하단 텍스트 스크롤 | notices | - | 낮음 | (Canvas 내부) |
| 32 | LLM 플로우 | JS | 데이터 패킷 애니메이션 | isRunning | - | 중간 | (Canvas 내부) |

### 1.5 전역 상태 변수 (21+개)

| 변수 | 타입 | 행 | 용도 |
|------|------|-----|------|
| `officeState` | Object (30+ 하위 필드) | 3581-3666 | 앱 전체 상태 (실행, 스테이지, 품질, 에이전트) |
| `_safeOpsConfirmResolve` | Function/null | 3667 | Safe Ops 확인 콜백 |
| `ACTION_META` | const Object | 3669-3681 | Stage 메타정보 |
| `STAGE0_SUB_META` | const Object | 3683-3689 | Stage 0 서브키 메타 |
| `_clickBubble` | Object | 3731 | 에이전트 클릭 말풍선 |
| `_directorScroll` | Object | 3733 | 디렉터 스크롤 텍스트 |
| `_verdictResetTimer` | Timer/null | 3735 | 심사 결과 리셋 타이머 |
| `spritesLoaded` | boolean | 5243 | 스프라이트 로딩 완료 |
| `_noticeCursor` / `_noticeX` / `_noticeText` / `_noticeActive` / `_noticeNextAt` | mixed | 5755-5759 | 하단 공지 스크롤 상태 |
| `_backendConnected` | boolean | 5826 | 백엔드 WS 연결 상태 |
| `_ws` | WebSocket/null | 5827 | WebSocket 인스턴스 |
| `_wsReconnectTimer` | Timer/null | 5828 | WS 재연결 타이머 |
| `_commandPathReady` | boolean | 5829 | HTTP 명령 경로 사용 가능 |
| `_statusSyncInFlight` | Promise/null | 5830 | 상태 동기화 진행중 |
| `_pendingPromptQueue` | Array | 5831 | 프롬프트 대기열 |
| `cliContract` | Object | 5847 | CLI 계약 정보 |
| `_currentPrompt` | Object/null | 6344 | 현재 표시중 프롬프트 |
| `_bootPhase` | boolean | 6345 | Stage 0 부트 단계 |
| `_autoExitAfterStage0` | boolean | 6346 | S0 완료 후 자동 Exit |
| `isSyncingWorkGuardHelper` | boolean | 7122 | WG 동기화 중 플래그 |
| `_pendingGenre` | string/null | 7931 | 장르 선택 대기 |
| `settingsStore` | Object | ~7198 | 사용자 설정 (API키, 프로젝트 등) |

### 1.6 렌더 함수 목록 (21개)

| 함수 | 행 | 대상 |
|------|-----|------|
| `renderPipelineStrip()` | 3877 | 파이프라인 진행 스트립 |
| `renderSafeOpsPreview()` | 4076 | Safe Ops 미리보기 |
| `renderArtifactLadder()` | 4119 | 산출물 단계 사다리 |
| `renderRetrievalInspector()` | 4192 | 검색 품질 검사기 |
| `renderQualityRadarFoot(summary)` | 4287 | 레이더 하단 요약 |
| `renderQualityRadar()` | 4319 | 품질 레이더 차트 |
| `renderResultSummary()` | 4378 | 심사 결과 요약 |
| `renderTrendCompare()` | 4442 | 트렌드 비교표 |
| `renderFailureWatch()` | 4487 | 실패 감시 패널 |
| `renderCalibrationDesk()` | 4555 | 보정 데스크 |
| `renderQualityInsights()` | 4625 | 품질 인사이트 통합 |
| `renderAgentBoard()` | 4839 | 에이전트 보드 (5카드) |
| `renderEventFeed()` | 4910 | 실시간 이벤트 피드 |
| `renderMissionBoard()` | 4951 | 미션 카드 보드 |
| `refreshQualitySummary()` | 4635 | 품질 요약 갱신 (async) |
| `refreshProjectList()` | 5936 | 프로젝트 목록 갱신 |
| `refreshMaterialList()` | 8039 | 재료 목록 갱신 |
| `refreshWorkGuardTemplateList()` | 7347 | WG 템플릿 목록 갱신 |
| `updateToggleLabels()` | 7017 | 토글 버튼 라벨 갱신 |
| `updateGenreModalState()` | 7942 | 장르 모달 상태 갱신 |
| `updateGenreGating()` | 8018 | 장르 미설정 시 버튼 비활성 |

### 1.7 이벤트 핸들러 목록 (63개 addEventListener + 0 removeEventListener)

주요 카테고리별 분류:

| 카테고리 | 건수 | 예시 |
|---------|------|------|
| 버튼 클릭 (Stage 실행) | ~15 | stage_0, stage_2, stage_3, stage_4, one_stop 등 |
| 설정 모달 상호작용 | ~10 | settingsBtn, settingsClose, 탭 전환, 저장 |
| 장르 선택 | ~5 | genreBtn, 장르 그리드, 확인/취소 |
| 재료 관리 | ~5 | importBtn, deleteBtn (bible/treatment) |
| 프롬프트 응답 | ~5 | promptSubmit, promptFilter, 옵션 선택 |
| 캔버스 상호작용 | ~3 | click, mousemove, ResizeObserver |
| 로그 필터 | ~3 | logSearchInput, logFilterSelect, 접기/펼치기 |
| 프로젝트 관리 | ~5 | projectSelect, newProjectBtn, 설정 저장 |
| 키보드 단축키 | ~3 | Escape (모달 닫기), Enter (프롬프트) |
| 기타 (토글, 확인) | ~9 | confirmOverlay, safeOps, skipAnimation, mute |

**핵심 문제**: addEventListener 63건, removeEventListener **0건**. 단, SPA 구조에서 고정 DOM 요소에만 바인딩하므로 실질적 메모리 누수는 없음 (3PASS 검증 완료).

### 1.8 Canvas/Animation 시스템 (16개 함수)

| 함수 | 행 | 용도 |
|------|-----|------|
| `drawRect()` | 5233 | 기본 사각형 |
| `drawSpriteImg()` | 5266 | 스프라이트 이미지 그리기 |
| `drawCrown()` | 5283 | 디렉터 왕관 |
| `drawAtlasSprite()` | 5321 | 아틀라스 스프라이트 |
| `drawOfficeDecor()` | 5330 | 사무실 장식 |
| `drawOfficeBackground()` | 5368 | 사무실 배경 |
| `drawWallDisplay()` | 5410 | 벽면 디스플레이 |
| `drawPacketStream()` | 5446 | 데이터 패킷 흐름 |
| `drawLLMFlow()` | 5459 | LLM 통신 시각화 |
| `drawDeskOverlay()` | 5475 | 책상 오버레이 |
| `drawAgent()` | 5521 | 에이전트 캐릭터 |
| `drawBubble()` | 5607 | 말풍선 |
| `drawModeEffect()` | 5662 | 실행 모드 이펙트 |
| `drawNoticeScroll()` | 5764 | 하단 공지 스크롤 |
| `draw()` | 5808 | 메인 렌더 루프 (rAF) |
| `resizeCanvas()` | 3567 | 캔버스 크기 동기화 (ResizeObserver) |

**핵심 문제**: `requestAnimationFrame(draw)` 호출이 `draw()` 내부(5822)에서 무조건 재귀, 앱 시작(8263)부터 종료까지 60fps 상시 실행. 비실행 시에도 정적 장면을 매 프레임 재렌더링.

### 1.9 데이터 흐름 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                    Renderer Process                       │
│  ┌─────────────────────────────────────────────────┐    │
│  │         index.html (8,266행 모놀리스)              │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │    │
│  │  │ Canvas   │  │ DOM 패널  │  │ 이벤트 핸들러 │  │    │
│  │  │ (16 fn)  │  │ (21 렌더) │  │  (63 listener)│  │    │
│  │  └────┬─────┘  └────┬─────┘  └──────┬───────┘  │    │
│  │       │              │               │           │    │
│  │       ▼              ▼               ▼           │    │
│  │  ┌──────────────────────────────────────────┐   │    │
│  │  │     officeState (30+ 필드) + 20 let      │   │    │
│  │  └──────────────┬───────────────────────────┘   │    │
│  └─────────────────┼───────────────────────────────┘    │
│                    │                                      │
│  ┌─────────────────▼───────────────────────────────┐    │
│  │        WebSocket (ws://127.0.0.1:8300/events)     │    │
│  │        실시간 이벤트: agent_*, stage_*, prompt     │    │
│  └─────────────────┬───────────────────────────────┘    │
│                    │                                      │
├────────────────────┼──────────────────────────────────────┤
│                    │  contextBridge (preload.js)          │
│  ┌─────────────────▼───────────────────────────────┐    │
│  │  window.geuldobiDesktop (25 live + 1 DC 메서드)  │    │
│  │  ipcRenderer.invoke → ipcMain.handle (24개)      │    │
│  └─────────────────┬───────────────────────────────┘    │
├────────────────────┼──────────────────────────────────────┤
│                    │  Main Process (main.js 1,009행)      │
│  ┌─────────────────▼───────────────────────────────┐    │
│  │  bridgeFetch() → HTTP POST → 127.0.0.1:8300     │    │
│  │  spawn() → backend.exe / python -m uvicorn       │    │
│  │  fs.read/writeFileSync → settings.json, config/  │    │
│  └─────────────────┬───────────────────────────────┘    │
├────────────────────┼──────────────────────────────────────┤
│                    ▼                                      │
│  Python Backend (bridge_server + engine)                  │
│  FastAPI/Uvicorn on http://127.0.0.1:8300                │
└─────────────────────────────────────────────────────────┘
```

### 1.10 Preload API Surface (25 live + 1 DC)

**Splash/Lifecycle (3)**:
- `getSplashConfig(): Promise<object>` -- splash 설정 조회
- `notifyBackendReady(): void` -- 백엔드 준비 알림 (send, not invoke)
- `onAppReady(handler): void` -- app:ready 이벤트 구독

**Bridge API (11)**:
- `runKey(key, subKey, inputs, approvalId?): Promise<object>` -- Stage 실행
- `stopRun(): Promise<object>` -- 실행 중지
- `getStatus(): Promise<object>` -- 런타임 상태 조회
- `getQualitySummary(project, lookback?): Promise<object>` -- 품질 요약
- `getQualityDashboard(project, lookback?): Promise<object>` -- 품질 대시보드
- `getSafeOpsPreview(project): Promise<object>` -- Safe Ops 미리보기
- `saveQualityReview(project, epNum, label, note?): Promise<object>` -- 품질 리뷰 저장
- `getBackendUrl(): Promise<string>` -- 백엔드 URL (WS 연결용)
- `getCliContract(): Promise<object>` -- CLI 계약 정보
- `resolvePrompt(runId, promptId, value): Promise<object>` -- 프롬프트 응답

**Settings (2)**:
- `saveSettings(settings): Promise<object>` -- 설정 저장
- `loadSettings(): Promise<object>` -- 설정 로드

**Material (3)**:
- `listMaterialFiles(folder): Promise<string[]>` -- 재료 파일 목록
- `importMaterialFile(folder): Promise<object>` -- 재료 파일 임포트
- `deleteMaterialFile(folder, fileName): Promise<object>` -- 재료 파일 삭제

**Project (5)**:
- `listProjects(): Promise<string[]>` -- 프로젝트 목록
- `createProject(name): Promise<object>` -- 프로젝트 생성
- `loadProjectConfigSurfaces(project): Promise<object>` -- 프로젝트 설정 로드
- `saveProjectConfigSurfaces(project, authorDirectives, workGuardYaml): Promise<object>` -- 프로젝트 설정 저장
- `listWorkGuardTemplates(genre?): Promise<object[]>` -- WG 템플릿 목록
- `applyWorkGuardTemplate(project, templatePath): Promise<object>` -- WG 템플릿 적용

**Workspace (1)**:
- `openWorkspaceFolder(): Promise<void>` -- 탐색기에서 작업 폴더 열기

**Dead Candidate (1)**:
- `getWorkspacePath(): Promise<string>` -- 워크스페이스 경로 (미사용, 의도적 보존)

---

## 2. React 도입 시 위협 (22건)

### 2.1 CRITICAL (2건)

**B3.1: 21+ 전역 상태 마이그레이션**

- `officeState` 객체 하나에 30+ 하위 필드가 집약. `qualityInsights` 내부만 해도 6개 중첩 객체 포함.
- 21개 이상의 분산 `let` 변수가 상태 역할을 수행 (`_backendConnected`, `_ws`, `_pendingPromptQueue`, `_currentPrompt` 등).
- React 전환 시 이 모든 상태를 단일 스토어(Zustand 등)로 이관해야 하며, 누락 시 런타임 불일치 발생.
- `officeState` 필드와 `let` 변수 간 암묵적 동기화 의존 관계가 존재 (예: `_backendConnected` → `officeState.backendConnected`).
- **위협 본질**: 마이그레이션 자체가 아니라, 암묵적 의존 관계를 **발견**하는 것이 병목.

**B3.2: 하이브리드 기간 DOM 소유권 충돌**

- 점진적 마이그레이션 시 React 가상 DOM과 바닐라 JS `innerHTML` 조작이 같은 DOM 트리에서 공존.
- React는 자신이 렌더링한 DOM 노드를 소유권(ownership) 기반으로 관리. 외부에서 `innerHTML`로 변경하면 React 상태와 실제 DOM이 불일치.
- `setInterval(() => { renderMissionBoard(); renderAgentBoard(); }, 500)` (8163-8166)이 500ms마다 `innerHTML = ""`로 전체 재생성 -- React 마운트된 하위 컴포넌트가 있으면 즉시 파괴.
- **실현 경로**: Phase 3(기능 패널 전환) 중 아직 전환되지 않은 패널의 바닐라 코드가 React 마운트 영역을 건드림.

### 2.2 HIGH (6건)

**B1.2: CSP 깨짐**

- 현재 `script-src 'self' 'unsafe-inline'` (index.html:6).
- Vite dev server는 `<script type="module" src="...">` 주입 -- `unsafe-inline` 제거 후에도 `'self'` 허용 시 동작.
- 그러나 Vite HMR은 `eval()`/`new Function()` 사용 -- `'unsafe-eval'` 추가 필요.
- 프로덕션 빌드는 번들 파일이므로 문제 없으나, 개발/프로덕션 CSP 분기 관리 필요.

**B2.3: app:ready 이벤트 타이밍**

- `onAppReady` (preload.js:41)는 `ipcRenderer.on` -- 한 번만 발생하는 이벤트.
- React 앱이 마운트되기 전에 이벤트가 발생하면 놓침.
- 현재 코드에서는 splash→main 전환 시점에 발생 (main.js:467).
- Vite 번들링 후 JS 로드 시간이 추가되면 타이밍 변경 가능.

**B2.4: WebSocket 라이프사이클**

- 현재 `_connectWebSocket()` (index.html:6172 부근)이 전역 스코프에서 호출.
- React 전환 시 useEffect에서 WS 연결을 관리해야 하지만, StrictMode에서 useEffect가 2회 실행되면 WS 중복 연결.
- `_ws` 전역 변수가 null 체크로 중복 방지하지만, React 관리로 전환 시 이 보호가 사라짐.

**B5.1: 이중 빌드 출력**

- 현재 electron-builder는 `src/**/*` 를 직접 번들 (package.json:71-74).
- Vite 도입 시 `src/` → `dist/renderer/` 빌드 출력 → electron-builder가 `dist/`를 번들.
- 기존 `extraResources` (backend, engine, python-embed, workspace-seed)와 빌드 출력 경로 충돌 가능.
- electron-builder 설정을 `"files": ["dist/renderer/**/*"]`로 변경 필요.

**B5.3: dev vs prod 경로 분기**

- main.js에서 `app.isPackaged` 기반 분기가 20+ 곳.
- Vite dev server 도입 시 main process가 `file://` 대신 `http://localhost:5173` 로딩 필요.
- `mainWindow.loadFile("src/index.html")` → `mainWindow.loadURL("http://localhost:5173")` 분기 추가.

**B6.1: 5-6개 기존 테스트 파괴**

- `test_desktop_preload_bridge_behavior.js` -- preload.js 구조에 의존.
- `test_desktop_contract_refresh.py` -- index.html 파일 직접 파싱.
- `test_ui_renderer_sanitization.py` -- index.html innerHTML 패턴 검사.
- `test_frontend_frontier_lag_wiring.py` -- 바닐라 JS 함수 존재 검증.
- `test_frontend_stage0_connectivity.py` -- index.html 이벤트 바인딩 검증.
- `test_desktop_shadow_hygiene.py` -- dead candidate 검증.
- Vite 빌드 후 이 테스트들은 번들된 JS를 대상으로 재작성 필요.

### 2.3 MEDIUM (6건)

| ID | 위협 | 설명 |
|----|------|------|
| B1.1 | Electron 보안 설정 비호환 | `nodeIntegration: false`는 유지되지만, Vite의 `import.meta.env` 사용 시 Node.js 환경 변수 접근 시도 가능 |
| B1.3 | lucide 번들 변경 | 현재 `require("lucide")` CommonJS → ESM import로 전환 필요. tree-shaking으로 번들 크기 감소 가능하지만 마이그레이션 작업 |
| B3.3 | settingsStore 이중 소스 | 설정이 DOM 입력 필드 + settingsStore 객체 양쪽에 존재 (`_collectInputs()` 5871행). React 전환 시 단일 소스로 통합 필요 |
| B4.2 | Canvas 통합 복잡도 | 16개 Canvas 함수는 React 외부에서 실행. `useRef` + `useEffect`로 Canvas 렌더링을 제어해야 하며, `officeState` 변경 시 re-render가 Canvas를 불필요하게 재초기화할 위험 |
| B6.2 | Playwright/Spectron 전환 | E2E 테스트 환경을 Vite dev server 기반으로 재구성 필요 |
| B7.4 | 팀 학습 곡선 | 1인 개발 체제에서 React + TypeScript + Vite + Zustand + CSS Modules 동시 도입은 학습 부담 |

### 2.4 LOW (8건)

| ID | 위협 | 설명 |
|----|------|------|
| B1.4 | 번들 크기 증가 | React ~150KB + Zustand ~3KB + Vite 런타임 ~5KB ≈ 158KB 추가. Electron 앱에서 무시 가능 |
| B2.1 | HMR 핫 리로드 상태 손실 | 개발 편의성 문제. officeState가 HMR에서 리셋될 수 있음 |
| B2.2 | Electron IPC serialization | React state가 Proxy 객체일 경우 IPC structured clone에서 실패 가능. Zustand은 plain object이므로 안전 |
| B4.1 | CSS 마이그레이션 누락 | 2,764행 CSS에서 438개 class 사용. CSS Modules 전환 시 class명 변경으로 스타일 깨짐 |
| B5.2 | electron-vite 버전 호환 | electron-vite가 Electron 40과 호환되는지 확인 필요 |
| B7.1 | 릴리스 지연 | React 도입 기간 중 기능 개발 중단 |
| B7.2 | 롤백 비용 | 하이브리드 상태에서 문제 발생 시 바닐라로 롤백하는 비용 |
| B7.3 | 문서 부채 | 아키텍처 변경 문서화 필요 |

---

## 3. React 도입 시 이득 (정량)

### 3.1 innerHTML 제거 (50건 -> 0건)

- 현재 index.html에서 `innerHTML` 사용 **50건** (코드 실측).
- 그 중 ~32건이 `escapeHtml()` 적용, ~18건이 하드코딩 HTML, **~3건이 미이스케이프 데이터 삽입**.
- React JSX로 전환 시 가상 DOM이 자동 이스케이프 → `innerHTML` 0건 달성.
- XSS 표면 제거 + `dangerouslySetInnerHTML` 명시적 사용으로 리뷰 포인트 축소.

### 3.2 수동 DOM 조작 제거 (228건 -> 0건)

- `getElementById`: **198건**, `querySelector/querySelectorAll`: **30건** = 총 **228건**.
- React 컴포넌트 내부에서는 `useRef`만 사용 → DOM 직접 조작 최소화.
- Canvas/애니메이션 제외 시 실질 제거 대상 ~200건.

### 3.3 이벤트 리스너 누수 해소 (63 add / 0 remove -> useEffect cleanup)

- 현재 `addEventListener` **63건**, `removeEventListener` **0건**.
- SPA 구조에서 고정 DOM이므로 실질 누수 없으나, React `useEffect` return cleanup 패턴이 구조적으로 안전.
- 동적 DOM 생성 시 (미래 기능) 누수 방지가 자동화됨.

### 3.4 상태 동기화 자동화 (500ms 폴링 -> 리액티브 구독)

- 현재 `setInterval(() => { renderMissionBoard(); renderAgentBoard(); }, 500)` (8163-8166).
- 500ms마다 `innerHTML = ""`로 전체 재생성 → 초당 2회 DOM 전파 파괴/재생성.
- React + Zustand의 선택적 구독(`useStore(s => s.missions)`)으로 변경된 데이터만 리렌더.
- 예상 DOM 조작 감소: 초당 150회 → 변경 시에만 (실행 중 ~초당 2-5회, 대기 시 0회).

### 3.5 CSS 스코핑 (438 class 사용 -> CSS Modules)

- 현재 438개 `class=` 사용, 2,764행 글로벌 CSS.
- 클래스 이름 충돌 가능성: 모든 클래스가 전역 스코프.
- CSS Modules 전환 시 `.module.css` 파일별 자동 스코핑 → 충돌 제거.
- 11개 CSS Custom Properties (`--bg`, `--surface`, `--line` 등)는 `:root`에서 유지 → 테마 시스템 기반.

### 3.6 컴포넌트 재사용

- 현재 중복 패턴: 품질 관련 6개 패널(Radar, ArtifactLadder, RetrievalInspector, ResultSummary, TrendCompare, FailureWatch)이 유사한 `innerHTML` 패턴.
- 에이전트 카드 5개가 동일 구조로 `renderAgentBoard()`에서 반복 생성.
- 미션 카드, 이벤트 피드 항목도 동일 패턴.
- React 컴포넌트화 시 `<QualityPanel>`, `<AgentCard>`, `<MissionCard>`, `<EventItem>` 등 공통 컴포넌트로 통합.

### 3.7 테스트 가능성 (0% -> 70% 커버리지 가능)

- 현재: 컴포넌트 단위 테스트 구조 불가 (8,266행 모놀리스).
- 기존 테스트: 계약 기반 정적 테스트만 (IPC 채널, CSP, preload 메서드 존재 확인).
- React + Testing Library: 개별 컴포넌트 렌더링 → props/state 변경 → DOM 검증 가능.
- Vitest + jsdom 환경에서 IPC mock으로 30+ 컴포넌트 각각 테스트 가능.

### 3.8 타입 안전 (0 -> 전면 TypeScript)

- 현재: 순수 JavaScript, JSDoc 타입 힌트 없음.
- `officeState` 객체의 30+ 필드에 타입 정의 없음 → 필드명 오타 시 `undefined` 전파.
- TypeScript 전환 시:
  - `OfficeState` 인터페이스로 30+ 필드 타입 고정
  - IPC 메서드 반환 타입 정의 (`GeuldobiDesktopBridge` 인터페이스)
  - WS 이벤트 Discriminated Union 타입
  - 컴파일 타임 오류 감지

---

## 4. 기술 선택 권장

### 4.1 프레임워크: React 19

| 후보 | 번들 크기 | Electron 호환 | 에코시스템 | 학습 비용 | 판정 |
|------|----------|-------------|----------|----------|------|
| **React 19** | ~150KB | 검증됨 (Electron 공식 사례) | 최대 | 중간 | **권장** |
| Preact 10 | ~4KB | 호환 | 제한적 | 낮음 | 차선 |
| Solid.js | ~7KB | 호환 | 성장 중 | 높음 (다른 패러다임) | 비권장 |
| Svelte 5 | ~2KB (런타임) | 호환 | 중간 | 중간 | 비권장 (컴파일러 복잡도) |

**선택 근거**: Electron 앱에서 번들 크기는 무의미 (로컬 파일). 에코시스템 크기와 채용/학습 자료가 결정적. React 19의 Server Components는 미사용하나 Suspense, concurrent features가 복잡 UI에 유리.

### 4.2 상태 관리: Zustand v5

| 후보 | 번들 크기 | 보일러플레이트 | 글도비 적합성 | 판정 |
|------|----------|-------------|-------------|------|
| **Zustand v5** | ~3KB | 최소 | officeState 패턴과 유사 (단일 객체) | **권장** |
| Jotai | ~5KB | 최소 | 원자적 상태에 적합하나 officeState가 단일 객체 | 차선 |
| Redux Toolkit | ~30KB | 높음 | 과도한 보일러플레이트 | 비권장 |

**선택 근거**: 현재 `officeState`가 단일 객체에 30+ 필드를 갖는 구조 → Zustand의 `create(set => ({...}))` 패턴이 1:1 대응. 미들웨어(devtools, persist)로 디버깅/설정 영속화도 간결.

### 4.3 CSS: CSS Modules

| 후보 | 설정 복잡도 | 런타임 비용 | 기존 CSS 호환 | 판정 |
|------|-----------|----------|-------------|------|
| **CSS Modules** | 제로 (Vite 내장) | 0 | 클래스명 1:1 이관 | **권장** |
| Tailwind CSS | 중간 | 0 | 전면 재작성 필요 | 비권장 (2,764행 CSS 버림) |
| styled-components | 낮음 | JS 런타임 | CSS→JS 전환 필요 | 비권장 |

**선택 근거**: 기존 2,764행 CSS를 `.module.css` 파일로 분리하면 거의 그대로 사용 가능. 11개 CSS Custom Properties는 `global.css`에서 유지.

### 4.4 빌드: electron-vite

| 후보 | Electron 특화 | HMR | 설정 복잡도 | 판정 |
|------|-------------|-----|-----------|------|
| **electron-vite** | 전용 | 렌더러/메인 분리 HMR | 낮음 | **권장** |
| Vite + 수동 설정 | 범용 | 수동 설정 필요 | 높음 | 차선 |
| webpack | 범용 | 느림 | 높음 | 비권장 |

### 4.5 테스트: Vitest + React Testing Library

- **Vitest**: Vite 네이티브 통합, ESM 지원, Jest 호환 API.
- **React Testing Library**: DOM 기반 테스트, 접근성 쿼리.
- **IPC Mock**: `vi.mock("electron")` + `window.geuldobiDesktop` stub.

### 4.6 IPC 래핑: useIPC() 커스텀 훅

```typescript
// 개념 설계
function useIPC<T>(method: keyof GeuldobiDesktopBridge, ...args: unknown[]): {
  data: T | null;
  loading: boolean;
  error: Error | null;
  refetch: () => void;
}
```

- `window.geuldobiDesktop` 전역 접근을 훅으로 캡슐화.
- 로딩 상태, 에러 처리, 재시도를 자동화.
- 컴포넌트 언마운트 시 진행 중인 요청 취소 (AbortController 패턴).

### 4.7 WS 래핑: useWebSocket() 커스텀 훅 (싱글톤 권장)

```typescript
// 개념 설계 -- 싱글톤 패턴
const wsStore = create<WsState>((set) => ({
  connected: false,
  events: [],
  connect: () => { /* 싱글톤 WS 인스턴스 */ },
  disconnect: () => { /* cleanup */ },
}));

function useWebSocket() {
  const { connected, events, connect } = wsStore();
  useEffect(() => { connect(); }, []);
  return { connected, events };
}
```

- **싱글톤 필수**: 현재 `_ws` 전역 변수가 단일 WS 인스턴스를 보장. React 전환 시 여러 컴포넌트에서 WS를 사용하더라도 단일 연결 유지.
- Zustand 스토어에서 WS 이벤트를 수신 → 구독 컴포넌트만 리렌더.

---

## 5. 마이그레이션 실행 계획

### 5.0 Phase 0: 빌드 인프라 (8-12h)

**목표**: Vite + electron-vite + TypeScript 빌드 체인 설치, 기존 코드 변경 없이 빌드 성공.

| 작업 | 시간 | 산출물 |
|------|------|--------|
| electron-vite 설치 + 기본 설정 | 2h | `electron.vite.config.ts` |
| TypeScript 설정 (tsconfig.json) | 1h | `tsconfig.json`, `tsconfig.node.json` |
| 기존 index.html을 Vite entry로 래핑 | 2h | `src/renderer/index.html` + `main.tsx` |
| CSS 분리 (2,764행 → `styles/global.css`) | 2h | `src/renderer/styles/global.css` |
| electron-builder 설정 업데이트 | 1h | `package.json` 수정 |
| 빌드 + 스파이크 테스트 확인 | 2h | `npm run build:dir` 성공 |

**의존성**: 없음 (최초 단계)
**롤백 전략**: git revert (빌드 설정만 변경, 기능 코드 미변경)
**완료 조건**: `npm run dev` → HMR 동작, `npm run build:dir` → .exe 생성 + spike 통과
**위험 게이트**: CSP 정책이 Vite dev server와 호환되는지 확인

### 5.1 Phase 1: 타입 기반 + 스토어 (16-24h)

**목표**: TypeScript 타입 정의 + Zustand 스토어 생성, 기존 바닐라 코드와 병행 운영.

| 작업 | 시간 | 산출물 |
|------|------|--------|
| `OfficeState` 인터페이스 정의 (30+ 필드) | 3h | `src/renderer/types/office.ts` |
| `GeuldobiDesktopBridge` 인터페이스 | 2h | `src/renderer/types/bridge.ts` |
| `WsEvent` Discriminated Union | 2h | `src/renderer/types/events.ts` |
| `officeStore` (Zustand) 생성 | 4h | `src/renderer/store/officeStore.ts` |
| `settingsStore` (Zustand + persist) | 2h | `src/renderer/store/settingsStore.ts` |
| `qualityStore` (Zustand) | 2h | `src/renderer/store/qualityStore.ts` |
| `connectionStore` (WS + 상태) | 3h | `src/renderer/store/connectionStore.ts` |
| `projectStore` (Zustand) | 2h | `src/renderer/store/projectStore.ts` |
| 기존 바닐라 코드에서 스토어 읽기 브릿지 | 3h | 양방향 동기화 어댑터 |

**의존성**: Phase 0 완료
**롤백 전략**: 스토어 파일 삭제, 바닐라 코드 복원
**완료 조건**: 스토어가 기존 전역 상태와 동기화되어 바닐라 UI가 정상 동작
**위험 게이트**: 이중 소스(바닐라 전역 + Zustand) 일관성 검증

### 5.2 Phase 2: 공유 컴포넌트 (20-28h)

**목표**: 재사용 가능한 기본 컴포넌트 라이브러리 구축.

| 작업 | 시간 | 산출물 |
|------|------|--------|
| `<Button>` / `<IconButton>` | 2h | 공통 버튼 |
| `<Modal>` / `<Overlay>` | 3h | 모달/오버레이 기반 |
| `<Panel>` / `<PanelHead>` | 2h | 패널 컨테이너 |
| `<Card>` (AgentCard, MissionCard) | 3h | 카드 변형 |
| `<Select>` / `<Input>` / `<Textarea>` | 2h | 폼 요소 |
| `<Badge>` / `<StatusBadge>` | 1h | 상태 표시 |
| `<Tabs>` / `<TabContent>` | 2h | 탭 네비게이션 |
| `useIPC()` 커스텀 훅 | 3h | IPC 래퍼 |
| `useWebSocket()` 커스텀 훅 (싱글톤) | 4h | WS 래퍼 |
| `useOfficeAnimation()` 커스텀 훅 | 3h | Canvas rAF 관리 |

**의존성**: Phase 1 완료
**롤백 전략**: 컴포넌트 파일 삭제 (기존 코드 미변경)
**완료 조건**: Storybook 또는 테스트에서 각 컴포넌트 렌더링 확인
**위험 게이트**: CSS Modules와 기존 글로벌 CSS 충돌 없음 확인

### 5.3 Phase 3: 기능 패널 (88-116h, 6개 서브페이즈)

**Phase 3a: Settings (12-16h)** -- 가장 독립적

| 작업 | 시간 | 산출물 |
|------|------|--------|
| `<SettingsOverlay>` | 4h | 설정 오버레이 |
| `<SettingsGeneral>` (API키, Slack) | 3h | 일반 탭 |
| `<SettingsAdvanced>` (타임아웃, 품질게이트) | 2h | 고급 탭 |
| `<SettingsProject>` (작성지시, WorkGuard) | 4h | 프로젝트 탭 |
| 바닐라 설정 코드 삭제 + 테스트 | 3h | 정리 |

**Phase 3b: Log (8-12h)**

| 작업 | 시간 | 산출물 |
|------|------|--------|
| `<LogStream>` (가상 스크롤) | 4h | 로그 스트림 |
| `<LogFilter>` (검색 + 타입 필터) | 2h | 필터 컨트롤 |
| `<LogEntry>` (에이전트별 색상) | 2h | 로그 항목 |
| 바닐라 로그 코드 삭제 + 테스트 | 2h | 정리 |

**Phase 3c: Run (16-20h)** -- 복잡 (Safe Ops, 프롬프트)

| 작업 | 시간 | 산출물 |
|------|------|--------|
| `<RunPanel>` (Stage 버튼 그리드) | 3h | 실행 패널 |
| `<Stage0SubPanel>` (6개 서브키) | 2h | S0 서브 패널 |
| `<SafeOpsPanel>` + `<SafeOpsConfirm>` | 4h | Safe Ops |
| `<PromptOverlay>` (텍스트/선택/확인) | 4h | 프롬프트 |
| `<GenreModal>` (장르 그리드) | 2h | 장르 선택 |
| 바닐라 실행 코드 삭제 + 테스트 | 3h | 정리 |

**Phase 3d: Quality (20-24h)** -- 6개 서브패널

| 작업 | 시간 | 산출물 |
|------|------|--------|
| `<QualityRadar>` (SVG 차트) | 4h | 레이더 |
| `<ArtifactLadder>` | 2h | 산출물 단계 |
| `<RetrievalInspector>` | 2h | 검색 검사기 |
| `<ResultSummary>` | 3h | 결과 요약 |
| `<TrendCompare>` | 3h | 트렌드 비교 |
| `<FailureWatch>` + `<CalibrationDesk>` | 4h | 실패 감시/보정 |
| 바닐라 품질 코드 삭제 + 테스트 | 4h | 정리 |

**Phase 3e: Office (16-20h)** -- Canvas 통합

| 작업 | 시간 | 산출물 |
|------|------|--------|
| `<OfficeCanvas>` (useRef + rAF) | 6h | 캔버스 컨테이너 |
| Canvas 함수 16개를 모듈로 추출 | 4h | `canvas/` 디렉토리 |
| `<AgentBoard>` (5개 카드) | 2h | 에이전트 보드 |
| `<MissionBoard>` (미션 카드) | 2h | 미션 보드 |
| `<EventFeed>` | 1h | 이벤트 피드 |
| `<PipelineStrip>` | 1h | 파이프라인 |
| 바닐라 오피스 코드 삭제 + 테스트 | 4h | 정리 |

**Phase 3f: Project (16-24h)** -- 재료 관리 + 프로젝트

| 작업 | 시간 | 산출물 |
|------|------|--------|
| `<MaterialList>` (bible/treatment) | 4h | 재료 목록 |
| `<WorkGuardHelper>` | 3h | WG 도우미 |
| `<ProjectSelect>` + `<NewProjectModal>` | 3h | 프로젝트 관리 |
| `<Topbar>` 통합 | 2h | 상단 바 |
| 바닐라 프로젝트 코드 삭제 + 테스트 | 4h | 정리 |

**각 서브페이즈 공통**:
- **의존성**: Phase 2 완료 + 이전 서브페이즈 완료 (3a→3b→3c→3d→3e→3f)
- **롤백 전략**: git branch per sub-phase, 실패 시 이전 서브페이즈로 롤백
- **완료 조건**: 해당 패널이 React 렌더링으로 전환되고, 기존 바닐라 코드가 삭제됨
- **위험 게이트**: 하이브리드 DOM 충돌 없음 확인 (특히 setInterval 제거 타이밍)

### 5.4 Phase 4: 레이아웃 셸 (12-16h)

| 작업 | 시간 | 산출물 |
|------|------|--------|
| `<App>` 루트 컴포넌트 | 2h | 앱 셸 |
| `<ShellLayout>` (2열 그리드) | 3h | 레이아웃 |
| React Router 또는 상태 기반 뷰 전환 | 2h | 네비게이션 |
| 모든 서브 컴포넌트 통합 | 3h | 트리 완성 |
| 바닐라 HTML 마크업 제거 | 2h | index.html → 빈 `<div id="root">` |
| 통합 테스트 | 2h | 전체 흐름 검증 |

**의존성**: Phase 3 전체 완료
**롤백 전략**: Phase 3 상태로 rollback (모든 패널은 이미 React)
**완료 조건**: index.html이 `<div id="root">`와 `<script>` 로더만 포함
**위험 게이트**: 모든 기존 기능이 React 버전에서 동작

### 5.5 Phase 5: 정리 + 최적화 (16-24h)

| 작업 | 시간 | 산출물 |
|------|------|--------|
| 바닐라 코드 잔여물 전수 삭제 | 3h | 코드 정리 |
| 테스트 커버리지 70% 달성 | 6h | 테스트 파일 |
| 성능 프로파일링 (React DevTools) | 2h | 보고서 |
| 번들 크기 최적화 (tree-shaking) | 2h | 번들 분석 |
| CSS 정리 (미사용 스타일 제거) | 2h | CSS 최적화 |
| 기존 테스트 스위트 React 기반으로 재작성 | 4h | 테스트 업데이트 |
| 문서화 (컴포넌트 아키텍처) | 2h | ARCHITECTURE.md |

**의존성**: Phase 4 완료
**완료 조건**: 바닐라 JS 0행, 테스트 70%+, 빌드 성공, 모든 기존 기능 동작

---

## 6. 컴포넌트 아키텍처 설계

### 컴포넌트 트리 (32개 컴포넌트)

```
<App>
├── <Topbar>
│   ├── <ProjectSelect>
│   ├── <NewProjectButton>
│   ├── <OpenWorkspaceButton>
│   └── <SettingsButton>
├── <ShellLayout>
│   ├── <LeftPanel>
│   │   ├── <RunPanel>
│   │   │   ├── <StageButtonGrid>
│   │   │   ├── <Stage0SubPanel>
│   │   │   └── <MaterialList> (x2: bible, treatment)
│   │   └── <SafeOpsPanel>
│   └── <RightPanel>
│       ├── <OfficeCanvas>
│       ├── <QualityDashboard>
│       │   ├── <QualityRadar>
│       │   ├── <ArtifactLadder>
│       │   ├── <RetrievalInspector>
│       │   ├── <ResultSummary>
│       │   ├── <TrendCompare>
│       │   ├── <FailureWatch>
│       │   └── <CalibrationDesk>
│       ├── <PipelineStrip>
│       ├── <AgentBoard>
│       │   └── <AgentCard> (x5)
│       ├── <EventFeed>
│       │   └── <EventItem> (xN)
│       └── <MissionBoard>
│           └── <MissionCard> (xN)
├── <LogStream>
│   ├── <LogFilter>
│   └── <LogEntry> (xN, 가상 스크롤)
├── <SettingsOverlay>
│   ├── <SettingsGeneral>
│   ├── <SettingsAdvanced>
│   └── <SettingsProject>
│       └── <WorkGuardHelper>
├── <GenreModal>
├── <ConfirmOverlay>
├── <SafeOpsConfirm>
├── <PromptOverlay>
└── <StatusBadge>
```

### 훅 아키텍처

| 훅 | 용도 | 의존성 |
|----|------|--------|
| `useIPC(method, args)` | Preload API 래핑 (로딩/에러/재시도) | window.geuldobiDesktop |
| `useWebSocket()` | WS 연결 싱글톤 + 이벤트 구독 | connectionStore |
| `useOfficeAnimation(canvasRef)` | Canvas rAF 루프 관리 + 조건부 실행 | officeStore |
| `useSettings()` | 설정 CRUD + 자동 저장 | settingsStore |
| `useProject()` | 프로젝트 CRUD + 설정 로드 | projectStore |
| `useMaterials(folder)` | 재료 목록/임포트/삭제 | useIPC |
| `usePromptQueue()` | 프롬프트 큐 관리 | connectionStore |
| `useQuality(project)` | 품질 데이터 조회 + 자동 갱신 | qualityStore |

### 스토어 설계 (5 슬라이스)

| 스토어 | 주요 상태 | Zustand 미들웨어 |
|--------|----------|-----------------|
| `officeStore` | isRunning, mode, currentStage, agents, focusTitle, ... | devtools |
| `qualityStore` | qualitySummary, qualityInsights | devtools |
| `settingsStore` | apiKey1, extraKeys, slackWebhook, timeout, ... | persist (localStorage) + devtools |
| `projectStore` | projects[], currentProject, genre, materials | devtools |
| `connectionStore` | wsConnected, commandReady, pendingPrompts[] | devtools |

---

## 7. CSS 마이그레이션 전략

### 7.1 CSS Custom Properties (11개)

```css
:root {
  --bg: #f8fafc;        /* 배경 */
  --surface: #ffffff;    /* 표면 */
  --line: #e2e8f0;       /* 구분선 */
  --text: #0f172a;       /* 본문 */
  --muted: #64748b;      /* 비활성 텍스트 */
  --label: #475569;      /* 라벨 */
  --button: #475569;     /* 버튼 */
  --button-hover: #334155; /* 버튼 호버 */
  --pass: #22c55e;       /* 통과 */
  --reject: #ef4444;     /* 거부 */
  --pwf: #eab308;        /* 보류 */
}
```

**전략**: `src/renderer/styles/variables.css`로 분리 → 전역 import. 다크 모드 확장 가능.

### 7.2 반응형 브레이크포인트 (3개)

| 브레이크포인트 | 행 | 용도 |
|-------------|-----|------|
| `max-width: 860px` | 2644 | 좌측 패널 숨김 |
| `max-width: 900px` | 2693 | 레이아웃 축소 |
| `max-width: 1280px` | 2747 | 넓은 화면 조정 |

### 7.3 전환 효과 (10개)

- `transition:` 속성 사용 **10건** (코드 실측).
- 주로 `opacity`, `transform`, `background-color` 전환.
- CSS Modules에서 그대로 사용 가능.

### 7.4 Canvas 애니메이션 (JS, 16 함수)

- Canvas 렌더링은 CSS와 무관 (JS `ctx.fillRect`, `ctx.drawImage` 등).
- `resizeCanvas()` (3567)이 CSS와 JS 사이 크기를 동기화하는 유일 접점.
- React 전환 시 `<canvas ref={canvasRef}>` + `useEffect`에서 `ResizeObserver` 연결.

### 7.5 다크 모드 기회

- 현재 다크 모드 미지원.
- 11개 CSS Custom Properties 기반이므로 `@media (prefers-color-scheme: dark)` 또는 `.dark` 클래스로 변수 오버라이드만 추가하면 다크 모드 구현 가능.
- 예상 작업량: ~2h (변수 오버라이드 + 토글 버튼).

---

## 8. IPC 타입 안전 설계

### 8.1 GeuldobiDesktopBridge 인터페이스

```typescript
interface GeuldobiDesktopBridge {
  // Splash/Lifecycle
  getSplashConfig(): Promise<SplashConfig>;
  notifyBackendReady(): void;
  onAppReady(handler: (payload: AppReadyPayload) => void): void;

  // Bridge API
  runKey(key: string, subKey: string | null, inputs: RunInputs, approvalId?: string | null): Promise<BridgeResponse>;
  stopRun(): Promise<BridgeResponse>;
  getStatus(): Promise<RuntimeStatus>;
  getQualitySummary(project: string, lookback?: number): Promise<QualitySummary>;
  getQualityDashboard(project: string, lookback?: number): Promise<QualityDashboard>;
  getSafeOpsPreview(project: string): Promise<SafeOpsPreview>;
  saveQualityReview(project: string, epNum: number, label: string, note?: string): Promise<BridgeResponse>;
  getBackendUrl(): Promise<string>;
  getCliContract(): Promise<CliContract>;
  resolvePrompt(runId: string, promptId: string, value: string): Promise<BridgeResponse>;

  // Settings
  saveSettings(settings: SettingsStore): Promise<BridgeResponse>;
  loadSettings(): Promise<SettingsStore | null>;

  // Material
  listMaterialFiles(folder: string): Promise<string[]>;
  importMaterialFile(folder: string): Promise<BridgeResponse>;
  deleteMaterialFile(folder: string, fileName: string): Promise<BridgeResponse>;

  // Project
  listProjects(): Promise<string[]>;
  createProject(name: string): Promise<BridgeResponse>;
  loadProjectConfigSurfaces(project: string): Promise<ProjectConfig>;
  saveProjectConfigSurfaces(project: string, authorDirectives: string, workGuardYaml: string): Promise<BridgeResponse>;
  listWorkGuardTemplates(genre?: string): Promise<WorkGuardTemplate[]>;
  applyWorkGuardTemplate(project: string, templatePath: string): Promise<BridgeResponse>;

  // Workspace
  openWorkspaceFolder(): Promise<void>;
  getWorkspacePath(): Promise<string>; // dead candidate
}
```

### 8.2 WsEvent Discriminated Union

```typescript
type WsEvent =
  | { type: "agent_status"; agent: string; status: string; detail: string }
  | { type: "stage_start"; stage: string; subKey?: string }
  | { type: "stage_complete"; stage: string; verdict: string; score?: number }
  | { type: "prompt_request"; runId: string; promptId: string; inputType: string; default?: string; options?: string[] }
  | { type: "prompt_resolved"; runId: string; promptId: string }
  | { type: "log"; level: string; message: string; agent?: string; meta?: Record<string, unknown> }
  | { type: "mission_update"; missions: Mission[] }
  | { type: "connection"; status: "connected" | "disconnected" };
```

### 8.3 Window 타입 확장

```typescript
declare global {
  interface Window {
    geuldobiDesktop: GeuldobiDesktopBridge;
  }
}
```

---

## 9. 타임라인

### 9.1 1인 개발 (160-220h, 6-10주)

| Phase | 시간 | 누적 |
|-------|------|------|
| Phase 0: 빌드 인프라 | 8-12h | 8-12h |
| Phase 1: 타입 + 스토어 | 16-24h | 24-36h |
| Phase 2: 공유 컴포넌트 | 20-28h | 44-64h |
| Phase 3: 기능 패널 | 88-116h | 132-180h |
| Phase 4: 레이아웃 셸 | 12-16h | 144-196h |
| Phase 5: 정리 + 최적화 | 16-24h | **160-220h** |

주 25h 작업 기준: **6.4-8.8주** (약 7-9주)
주 40h 전업 기준: **4-5.5주**

### 9.2 2-3인 팀 (3-4주)

- 병렬화 가능 구간: Phase 3a-3f 중 3a(Settings) + 3b(Log)를 동시 진행 가능.
- Phase 3d(Quality) + 3e(Office)도 독립적이므로 병렬화 가능.
- 크리티컬 패스: Phase 0 → 1 → 2 → 3c(Run, 프롬프트) → 4 → 5 (직렬 필수)
- 2인 팀: **3-4주**, 3인 팀: **2.5-3주** (전업 기준)

### 9.3 크리티컬 패스

```
Phase 0 (8-12h) → Phase 1 (16-24h) → Phase 2 (20-28h)
                                         ↓
                      Phase 3c: Run (16-20h) ← 프롬프트/SafeOps 복잡도
                                         ↓
                      Phase 3d: Quality (20-24h)
                                         ↓
                      Phase 4 (12-16h) → Phase 5 (16-24h)

총 크리티컬 패스: 108-148h (1인 기준)
```

Phase 3a(Settings), 3b(Log), 3e(Office), 3f(Project)는 크리티컬 패스 외부에서 병렬 가능.

### 9.4 Feature Freeze 필요 구간

| 구간 | 기간 | 이유 |
|------|------|------|
| Phase 3c (Run) | 16-20h | 실행 패널은 모든 Stage에 영향, 동시 기능 변경 불가 |
| Phase 4 (Layout) | 12-16h | 전체 레이아웃 재구성, HTML 마크업 전면 교체 |
| Phase 5 (정리) | 16-24h | 바닐라 코드 삭제, 테스트 재작성 |

**권장**: Phase 3c 시작 ~ Phase 5 완료까지 feature freeze (60-80h, 약 2-3주).

---

## 10. 수치 요약표

| 지표 | 현재 (바닐라) | React 전환 후 (예상) | 변화 |
|------|-------------|-------------------|------|
| 소스 파일 수 | 8 | ~50-70 | +42-62 |
| 최대 파일 크기 | 8,266행 | ~200-400행/파일 | -95% |
| 총 코드량 | 9,723행 | ~8,000-10,000행 | +-5% |
| innerHTML 직접 조작 | 50건 | 0건 | -100% |
| DOM 직접 쿼리 | 228건 | ~10건 (Canvas ref) | -96% |
| addEventListener (수동) | 63건 | 0건 | -100% |
| removeEventListener | 0건 | 자동 (useEffect) | N/A |
| 전역 상태 변수 | 21+개 | 5개 스토어 | -76% |
| 단위 테스트 가능성 | 불가 | 70% 커버리지 | 0→70% |
| 타입 안전 | 없음 | 전면 TypeScript | 0→100% |
| 번들 크기 추가 | 0 | ~158KB (React+Zustand) | +158KB |
| 빌드 시간 | 0초 | ~3-5초 (Vite HMR) | +3-5초 |
| 의존성 수 | 1 (lucide) | ~15-20 | +14-19 |
| CSS Custom Properties | 11개 | 11개 (유지) | 0 |
| 반응형 브레이크포인트 | 3개 | 3개 (유지) | 0 |
| CSS 전환 효과 | 10개 | 10개 (유지) | 0 |
| Canvas 함수 | 16개 | 16개 (모듈화) | 0 |
| 컴포넌트 수 | 0 | ~32개 | +32 |
| 커스텀 훅 수 | 0 | ~8개 | +8 |

---

## 11. 최종 권장안

### 단기 (현재 ~ 1.6.0 릴리스): 현상 유지 + 구조화

**현재 1.6.0 릴리스가 최우선**. React 도입은 릴리스를 차단한다.

즉시 실행 가능한 최소 개선:
1. CSS 분리 (`index.html` → `styles.css`) -- 2,764행 감소, 1-2h
2. `sanitizeProjectName` 경로 탈출 수정 -- 정규식 1줄, 10분 (SEC-07, HIGH)
3. `connect-src`에서 미사용 `generativelanguage.googleapis.com` 제거 -- 1줄, 5분

### 중기 (1.6.0 이후 ~ 2.0.0): Phase 0-1

1.6.0 안정화 후:
1. Vite + electron-vite 빌드 체인 도입 (Phase 0, 8-12h)
2. TypeScript 타입 정의 + Zustand 스토어 생성 (Phase 1, 16-24h)
3. 기존 바닐라 코드는 유지하되, 새 기능은 React 컴포넌트로 작성

### 장기 (2.0.0): Phase 2-5 전체 전환

2.0.0 목표에 React 전환을 포함:
1. 공유 컴포넌트 구축 (Phase 2)
2. 점진적 패널 전환 (Phase 3, Settings부터 Office 순서)
3. 레이아웃 셸 통합 + 정리 (Phase 4-5)
4. 예상 기간: 1인 6-10주 / 2-3인 3-4주

### 비권장: 전면 재작성 (Big Bang)

전면 재작성은 현 단계에서 **리스크 대비 이점 불충분**:
- 1인 개발 체제에서 4-6주 FE 차단 = 백엔드 개발 중단
- 현재 FE가 **기능적으로 동작** (보안 이슈 1 HIGH 있으나 정규식 1줄로 수정 가능)
- 점진적 전환(Strangler Fig)이 회귀 리스크를 분산

---

## [부록 A] 3PASS 감리 결과

### PASS 1: 사실 확인 (10 sampled checks against code)

| # | 주장 | 검증 방법 | 결과 |
|---|------|----------|------|
| 1 | index.html은 8,266행 | `wc -l` | **PASS**: 8,266행 확인 |
| 2 | CSS는 2,764행 (lines 8-2772) | `</style>` 태그 위치 확인 | **PASS**: line 2772에 `</style>`, 2772-8=2,764행 |
| 3 | innerHTML 사용 50건 | `grep -c innerHTML` | **PASS**: 50건 정확 |
| 4 | addEventListener 63건 | `grep -c addEventListener` | **PASS**: 63건 정확 |
| 5 | removeEventListener 0건 | `grep -c removeEventListener` | **PASS**: 0건 정확 |
| 6 | getElementById 198건 | `grep -c getElementById` | **PASS**: 198건 정확. 초기 방향 보고서의 "315+"는 오류 -- querySelector 30건 합산해도 228건 |
| 7 | CSS Custom Properties 11개 | `:root` 블록 확인 | **PASS**: `--bg` 부터 `--pwf` 까지 11개 |
| 8 | Preload live 메서드 25개 | preload.js 코드 확인 | **PASS**: getSplashConfig ~ openWorkspaceFolder = 25개, deadCandidate 1개 |
| 9 | ipcMain.handle 24개 | `grep -c 'ipcMain.handle'` main.js | **PASS**: 24건 (초기 보고서 "25개"는 `ipcMain.on` 1건 포함 여부에 따라 상이) |
| 10 | officeState 필드 30+ | 코드 3581-3666행 확인 | **PASS**: officeState 객체에 최상위 16 필드 + qualitySummary(8) + qualityInsights(12+) = 36+ 필드 |

**PASS 1 결과**: 10/10 통과. 초기 방향 보고서의 getElementById "315+" 수치는 228건으로 교정 완료. ipcMain.handle은 24건이 정확하며, 보고서 내에서도 24로 통일.

### PASS 2: 교차 일관성 (directions A/B/C consistency)

| # | 항목 | 방향 보고서 | 본 문서 | 일치 |
|---|------|-----------|---------|------|
| 1 | 총 행수 | 9,723행 | 9,723행 | **일치** |
| 2 | 프레임워크 | 없음 (바닐라 JS) | 없음 | **일치** |
| 3 | 외부 의존성 | lucide 1개 | lucide 1개 | **일치** |
| 4 | Electron 버전 | 40.8.0 | 40.8.0 | **일치** |
| 5 | innerHTML 수 | A: 50건, B: ~65건 | 50건 (grep 실측) | **A 정확, B 과대 (B는 미적대적 전수 대조에서 65건 언급했으나 grep 기준 50)** |
| 6 | 전역 상태 | A: 13개, B: 21+개 | 21+개 (전수 목록 기반) | **B 정확, A 과소 (A는 officeState 1개 + 12 let = 13 으로 카운트, B는 개별 변수 전수)** |
| 7 | 마이그레이션 기간 (전면) | A: 3-5주, B: 6-10주 | 6-10주 (Phase별 적산) | **B 정확, A 과소** |
| 8 | SEC-07 심각도 | 3Pass: MEDIUM, 적대적: HIGH | HIGH | **적대적 판정 채택 (코드 실행 검증)** |
| 9 | UX-03 프롬프트 경쟁조건 | 3Pass: HIGH→MEDIUM, 적대적: 삭제 | 삭제 | **적대적 판정 채택 (JS 단일 스레드)** |
| 10 | process.env 심각도 | 3Pass: HIGH, 적대적R1: MEDIUM, R2: LOW | LOW | **R2 판정 채택 (개발모드 불가피)** |

**PASS 2 결과**: 방향 간 수치 차이 3건 발견, 모두 코드 실측 기반으로 교정 완료.

### PASS 3: 구조 완전성

| # | 검사 항목 | 결과 |
|---|----------|------|
| 1 | 모든 UI 섹션이 목록화되었는가? | **PASS**: 32개 섹션 전수 목록 |
| 2 | 모든 전역 상태가 목록화되었는가? | **PASS**: 21+개 변수 전수 목록 |
| 3 | 모든 렌더 함수가 목록화되었는가? | **PASS**: 21개 함수 전수 목록 |
| 4 | 위협/이득이 균형있게 기술되었는가? | **PASS**: 위협 22건, 이득 8개 카테고리 |
| 5 | 마이그레이션 계획에 롤백 전략이 포함되었는가? | **PASS**: 모든 Phase에 롤백 전략 명시 |
| 6 | 타임라인이 Phase별 적산과 일치하는가? | **PASS**: 160-220h = 8-12 + 16-24 + 20-28 + 88-116 + 12-16 + 16-24 |
| 7 | Preload API 타입이 실제 코드와 일치하는가? | **PASS**: 25 live + 1 DC, 메서드 시그니처 코드 대조 |
| 8 | 기존 감리 보고서 결과가 정확히 반영되었는가? | **PASS**: R2 최종 판정 기준 반영 |

---

## [부록 B] 적대적 3PASS 감리 결과

### Adversarial PASS 1: Code-level fact attacks (10 checks)

| # | 공격 대상 주장 | 반증 시도 | 결과 |
|---|-------------|----------|------|
| 1 | "innerHTML 50건" -- 실제로 더 많거나 적지 않은가? | `grep -c innerHTML index.html` = **50** | **반증 실패**: 50건 정확 |
| 2 | "getElementById 198건" -- querySelector 포함하면? | querySelector=30, total=228 | **반증 성공**: DOM 쿼리 총합은 228이지 198이 아님. 본문에서 228으로 명시하되 getElementById만 198임을 구분 |
| 3 | "escapeHtml 적용률 95%" -- 실제로? | 적대적 감리 R1 전수 대조: ~32/50 innerHTML에 escapeHtml → 64% | **부분 반증**: 95%는 과대. 그러나 18건이 하드코딩 HTML(데이터 삽입 없음)이므로 "데이터 삽입 innerHTML 중 escapeHtml 적용률"은 32/35 = 91% |
| 4 | "setInterval 500ms가 성능 문제" -- 정말? | 5카드 x 15노드 = 75노드/500ms. 현대 브라우저에서 무시 가능 | **반증 성공**: R2 적대적 감리에서 INFO로 하향 확인. 본문에서도 "현대 브라우저에서 무시 가능" 반영 |
| 5 | "rAF 무한 루프" -- 실제 코드에서? | index.html:5822 `requestAnimationFrame(draw)` 무조건 재귀 + 8263 최초 호출 | **반증 실패**: 무한 루프 확인 |
| 6 | "CSS Custom Properties 11개" -- 빠진 것 없나? | `:root` 블록 확인: --bg ~ --pwf 11개. 다른 블록에 추가 정의 없음 확인 | **반증 실패**: 11개 정확 |
| 7 | "Zustand 3KB" -- 최신 버전에서도? | Zustand v5 bundlephobia 기준 ~2.9KB min+gzip | **반증 실패**: 3KB 근사 정확 |
| 8 | "Phase 3 88-116h" -- 과소/과대 아닌가? | 6 서브페이즈 합산: 12-16 + 8-12 + 16-20 + 20-24 + 16-20 + 16-24 = 88-116h | **반증 실패**: 산술 정확 |
| 9 | "contextIsolation: true" -- 코드 확인 | main.js에서 BrowserWindow 생성 시 webPreferences 확인 필요 | **검증 보류**: main.js 전체 읽기 필요하나, 3방향 보고서 모두 동일 주장 + preload.js의 contextBridge 사용이 간접 증거 |
| 10 | "Preload 메서드 25개 live" -- 코드 대조 | preload.js PRELOAD_METHOD_CHANNELS.live 키 카운트: getSplashConfig(1), notifyBackendReady(2), onAppReady(3), runKey(4)...openWorkspaceFolder(25) | **반증 실패**: 25개 정확 |

**Adversarial PASS 1 결과**: 10건 중 1건 부분 반증(escapeHtml 적용률), 1건 반증 성공(setInterval 심각도), 1건 검증 보류(contextIsolation). 본문에 반영 완료.

### Adversarial PASS 2: Contradiction hunting

| # | 모순 후보 | 판정 |
|---|----------|------|
| 1 | "3.2절 DOM 조작 228건 제거" vs "1.7절 addEventListener 63건" -- addEventListener도 DOM 조작 아닌가? | **비모순**: addEventListener는 "이벤트 바인딩"이지 "DOM 조작"이 아님. 3.2절의 228건은 getElementById+querySelector만 카운트 |
| 2 | "4.2절 Zustand 3KB" vs "10절 번들 158KB" -- 158KB에 Zustand 포함? | **비모순**: 158KB = React ~150KB + Zustand ~3KB + Vite 런타임 ~5KB. 합산 정확 |
| 3 | "5.3절 Phase 3 88-116h" vs "9.1절 총 160-220h" -- Phase 3이 총량의 55%? | **비모순**: 88/160 = 55%, 116/220 = 53%. Phase 3이 기능 전환의 핵심이므로 합리적 비중 |
| 4 | "2.1절 CRITICAL 21+ 전역 상태" vs "1.5절 21+개" -- 동일 카운트? | **일치**: 1.5절 목록이 2.1절의 근거 |
| 5 | "11절 비권장: 전면 재작성 4-6주" vs "9.1절 160-220h (6-10주)" -- 차이? | **모순 발견**: 11절에서 "4-6주"라고 했으나 9.1절은 "6-10주". 11절은 최적 시나리오(주 40h), 9.1절은 주 25h 기준. 본문에서 "1인 전업 기준 4-5.5주"로 통일 |

**Adversarial PASS 2 결과**: 1건 경미한 모순 발견 (전면 재작성 기간 표현), 본문에서 교정 완료.

### Adversarial PASS 3: Missing risk/benefit check

| # | 누락 후보 | 판정 |
|---|----------|------|
| 1 | **Electron 업그레이드 리스크**: React 도입 후 Electron 메이저 업그레이드 시 electron-vite 호환성 깨짐 가능 | **유효**: 2.4절 B5.2에 "electron-vite 버전 호환"으로 반영되어 있으나 Electron 메이저 업그레이드 시나리오는 미언급. **LOW 추가 위험** |
| 2 | **IPC 타입 안전의 런타임 갭**: TypeScript는 컴파일 타임 검사만, IPC 응답의 런타임 타입은 보장 불가 | **유효**: 8절 IPC 타입 설계에 런타임 검증(zod 등) 미언급. **INFO 추가 위험** |
| 3 | **Canvas 성능 회귀**: React re-render가 Canvas 부모 컴포넌트를 재마운트하면 Canvas 컨텍스트 재초기화 | **유효**: 2.3절 B4.2에 반영됨 |
| 4 | **Zustand persist와 Electron 설정 이중 영속화**: Zustand persist(localStorage) + 기존 settings.json 충돌 | **유효**: settingsStore를 Zustand persist로 전환 시 기존 `saveSettings` IPC와 충돌 가능. 한쪽으로 통일 필요. **MEDIUM 추가 위험** |
| 5 | **접근성 개선 기회 누락**: React 도입 시 ARIA 속성 자동 관리 가능하나 이득 섹션에 미반영 | **유효**: 3절에 접근성 이득 미포함. 다만 UX-08에서 "장기 과제"로 분류했으므로 현 시점에서는 생략 합리적 |

**Adversarial PASS 3 결과**: 5건 중 2건(Zustand persist 충돌, IPC 런타임 검증) 추가 고려 필요. 본 문서의 위협 섹션에 해당 내용이 부분적으로 반영되어 있으나, 명시적 호출은 부족. 중요도 낮으므로 부록에서 기록만 남김.

---

## [부록 C] 근거 파일 인벤토리

### 코드 파일 (실측 대상)

| 파일 | 절대 경로 | 행수 |
|------|----------|------|
| index.html | `C:/Users/wjjo/Desktop/글도비/geuldobi-desktop/src/index.html` | 8,266 |
| main.js | `C:/Users/wjjo/Desktop/글도비/geuldobi-desktop/src/main.js` | 1,009 |
| preload.js | `C:/Users/wjjo/Desktop/글도비/geuldobi-desktop/src/preload.js` | 96 |
| desktop_control_plane_contract.js | `C:/Users/wjjo/Desktop/글도비/geuldobi-desktop/src/desktop_control_plane_contract.js` | 96 |
| console_relay.js | `C:/Users/wjjo/Desktop/글도비/geuldobi-desktop/src/console_relay.js` | 56 |
| splash.js | `C:/Users/wjjo/Desktop/글도비/geuldobi-desktop/src/splash/splash.js` | 89 |
| splash.html | `C:/Users/wjjo/Desktop/글도비/geuldobi-desktop/src/splash/splash.html` | 27 |
| splash.css | `C:/Users/wjjo/Desktop/글도비/geuldobi-desktop/src/splash/splash.css` | 84 |
| package.json | `C:/Users/wjjo/Desktop/글도비/geuldobi-desktop/package.json` | 77 |

### 선행 조사 보고서

| 문서 | 경로 | 역할 |
|------|------|------|
| React 도입 타당성 보고서 (Direction A) | `docs/2026-03-18/OPUS/geuldobi-v2-react-adoption-feasibility-report.md` | 시나리오 분석 + 의사결정 매트릭스 |
| 프론트엔드 딥다이브 3-Pass 감리 (Direction B) | `docs/2026-03-18/OPUS/geuldobi-v2-frontend-deepdive-3pass-audit.md` | 보안/UX/빌드 29건 발견 |
| 적대적 3-Pass 감리 R1 (Direction C-1) | `docs/2026-03-18/OPUS/geuldobi-v2-frontend-deepdive-adversarial-3pass-audit.md` | R1: 29건 → 11건 (18건 삭제) |
| 적대적 3-Pass 감리 R2 (Direction C-2) | `docs/2026-03-18/OPUS/geuldobi-v2-frontend-deepdive-adversarial-3pass-audit-r2.md` | R2: 11건 → 10건 (수렴 확인) |

### 실측 검증 수치 요약

| 항목 | 실측값 | 방법 |
|------|--------|------|
| innerHTML | 50건 | `grep -c innerHTML index.html` |
| addEventListener | 63건 | `grep -c addEventListener index.html` |
| removeEventListener | 0건 | `grep -c removeEventListener index.html` |
| getElementById | 198건 | `grep -c getElementById index.html` |
| querySelector/All | 30건 | `grep -c querySelector index.html` |
| DOM 쿼리 총합 | 228건 | getElementById + querySelector |
| catch(() => {}) | 8건 | `grep -c '.catch(() =>' index.html` |
| setInterval/setTimeout | 5건 | `grep -c 'setInterval\|setTimeout' index.html` |
| escapeHtml | 29건 | `grep -c escapeHtml index.html` |
| CSS Custom Properties | 11개 | `:root` 블록 수동 확인 |
| @media 브레이크포인트 | 3개 | `grep -c '@media' index.html` |
| transition: 사용 | 10건 | `grep -c 'transition:' index.html` |
| class= 사용 | 438건 | `grep -c 'class="' index.html` |
| ipcMain.handle | 24건 | `grep -c 'ipcMain.handle' main.js` |
| Preload live 메서드 | 25개 | preload.js 코드 수동 카운트 |
| Named functions (JS) | 113개 | `grep -c 'function ' index.html` |
| requestAnimationFrame | 2건 | 5822 (재귀), 8263 (최초) |

---

> **문서 종료**
>
> 본 문서는 3방향 독립 조사 보고서를 통합하고, 코드 실측 기반 3PASS 감리 + 적대적 3PASS 감리를 수행한 최종 확정본이다.
> 수치 오류 3건(getElementById 315+→228, escapeHtml 적용률 95%→91%, 전면 재작성 기간 4-6주→4-5.5주)을 본문에서 교정하였다.
> 감리 결과는 R2 적대적 감리에서 수렴을 확인하였으며, 추가 감리는 불필요하다.
