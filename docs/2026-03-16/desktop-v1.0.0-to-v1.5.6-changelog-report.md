# Geuldobi Desktop v1.0.0 → v1.5.6 변경 보고서

## 요약

- **Spike 프로토타입에서 풀스택 데스크톱 앱으로 전환**: Splash + 오피스 씬 뷰어 수준(780줄 HTML)에서 8,168줄의 완전한 파이프라인 제어 UI로 성장
- **백엔드 자동 기동/종료**: uvicorn 프로세스를 Electron이 spawn하고 수명주기 관리 (자동 재시작 최대 2회)
- **IPC 채널 3개 → 30개+**: Splash 전환만 지원하던 preload bridge가 파이프라인 실행, 품질 대시보드, 프로젝트/재료 관리, 설정 영속화, WebSocket 이벤트 스트림까지 포괄
- **빌드/배포 파이프라인 구축**: electron-builder NSIS 설치기, PyInstaller 백엔드 번들, workspace-seed 동기화 완비
- **모듈 분리 완료**: 인라인 매직 스트링 → `desktop_control_plane_contract.js` (IPC 채널 SSOT) + `console_relay.js` (렌더러 콘솔 릴레이)

## 버전 이력

| 버전 | 커밋 | 날짜 | 주요 변경 |
|------|------|------|-----------|
| 1.0.0 | `43f91a02` | 2026-03-08 | 초기 Spike 4: Splash + 오피스 씬 스켈레톤 |
| 1.0.0 | `7f0a4e53` | 2026-03-09 | 오피스 씬 스프라이트 + 백엔드 재시작 제한 + CSP |
| 1.0.0 | `0bb45a23` | 2026-03-09 | 스프라이트 에셋 + DESKTOP-GUIDE.md 추가 |
| 1.0.0 | `3a00c127` | 2026-03-09 | 배포 빌드 파이프라인 + MMO 공지 스크롤 + Stage 0 경고창 |
| 1.0.0 | `d2d935be` | 2026-03-10 | UI 대폭 확장 (+1,178줄) — 품질 대시보드, 이벤트 피드 |
| 1.0.0 | `ea5ae7fb` | 2026-03-10 | 품질/프로바이더/UI 업그레이드 (+625줄) |
| 1.0.0 | `3614a7c4` | 2026-03-11 | 프로젝트 관리 IPC + 설정 패널 + WorkGuard 헬퍼 (+2,554줄) |
| 1.0.0 | `19505108` | 2026-03-12 | 카나리아 자동화 + 로깅 강화 |
| 1.5.0 | `fb74b5f5` | 2026-03-13 | 버전 1.5.0 범프 + 재료 관리 IPC + 프로젝트 IPC 확장 (+1,699줄) |
| 1.5.0 | `e6b81439` | 2026-03-14 | console_relay.js 분리 + 루트 main.js 정리 |
| 1.5.0 | `4457bb02` | 2026-03-14 | desktop_control_plane_contract.js 도입 + IPC 리팩토링 |
| 1.5.0 | `d6c81c19` | 2026-03-16 | UI 개편 + preload/main.js IPC 보강 (+260줄) |
| 1.5.6 | `58538b37` | 2026-03-16 | workspace-seed + build scripts + control-plane provenance |

## 카테고리별 개선사항

### 1. UI/UX 변경

**오피스 씬 (Canvas 기반 픽셀아트 렌더링)**
- v1.0.0: 5개 에이전트(Writer, Analyst, Critic, Director, Manager) 기본 걷기/앉기 포즈, 단색 배경
- v1.5.6: LimeZu RPG Maker MV 타일셋 기반 오피스 배경 + 가구 데코 + 벽면 디스플레이
- 스프라이트 33개 추가 (캐릭터 15개 + 가구/배경 18개)
- Director 독립 배치 (오른쪽), 나머지 4명 2x2 그룹
- 스테이지별 에이전트 활성/비활성 (30% 투명도)
- 패킷 스트림 애니메이션 (에이전트 간 LLM 통신 시각화)
- MMO 스타일 공지 스크롤 (1분 간격 배경 안내 메시지)
- Director 분석 스크롤 + 상태 말풍선 (Arc/BP/원고 진행 표시)
- Manager 로그→말풍선 연결 (12개 파이프라인 상태 패턴)
- 왕관 아이콘 (Director 식별)

**대시보드 패널 (신규)**
- Quality Radar: 프로젝트별 품질 요약 (점수/트렌드)
- Quality Dashboard: 스파크라인 SVG + 시그널 분석
- Quality Insights: 관측 라벨별 분류 표시
- Trend Compare: 회차 간 품질 비교
- Failure Watch: 실패 패턴 모니터링
- Result Summary: 실행 결과 요약
- Calibration Desk: 보정 데스크
- Artifact Ladder: 아티팩트 상태 계층 표시
- Retrieval Inspector: 컨텍스트 검색 내역 검사
- Safe Ops Preview: 안전 작업 미리보기 (확인 다이얼로그 포함)
- Agent Board: 에이전트별 상태 보드
- Event Feed: 실시간 이벤트 피드
- Mission Board: 미션 현황 보드
- Pipeline Strip: 파이프라인 단계 표시 바

**프로젝트/설정 UI (신규)**
- 프로젝트 목록 표시 + 신규 프로젝트 생성
- 장르 선택 모달 (10개 장르, CLI_CONTRACT 기반)
- 설정 패널 (탭 기반): 프로젝트, 재료, 모델, 워크스페이스
- Author Directives 편집기 (텍스트에어리어)
- WorkGuard YAML 편집기 + 헬퍼 폼 (YAML 파싱/생성)
- WorkGuard 템플릿 목록 + 적용 기능
- Bible/Treatment 재료 파일 목록 + 임포트/삭제
- 로그 필터링 (verdict 기반)
- Stage 0 개선 중 경고창 (4개 옵션)

**WebSocket 이벤트 스트림 (신규)**
- `ws://127.0.0.1:8300/events` 실시간 연결
- 자동 재연결 (연결 끊김 시)
- 이벤트별 에이전트 상태 업데이트 + 말풍선 + 로그 동기화
- 프롬프트 다이얼로그 (Mode B 인터랙티브 입력)
- 런타임 상태 스냅샷 동기화

**유틸리티 함수 (신규 105개)**
- v1.0.0: 18개 함수
- v1.5.6: 123개 함수
- 주요 추가: `escapeHtml()`, `sanitizeToken()`, `wrapBubbleText()`, `formatDuration()`, `buildSparklineSvg()`, `parseHelperStateFromYaml()`, `mergeHelperStateIntoYaml()` 등

### 2. 아키텍처 변경

**모듈 분리**
- `console_relay.js` (56줄, 신규): 렌더러 프로세스 콘솔 메시지 릴레이. `warn`/`error` 레벨만 메인 프로세스 로그로 전달. `attachConsoleRelay()`, `buildConsoleRelayEntry()`, `normalizeConsoleSeverity()`, `shouldRelayConsoleMessage()` 4개 함수 export.
- `desktop_control_plane_contract.js` (96줄, 신규): IPC 채널명 SSOT. `IPC_CHANNELS` (5개 네임스페이스, 26개 채널), `PRELOAD_METHOD_CHANNELS` (21 live + 1 deadCandidate), `BRIDGE_MANAGED_ROUTES` (7개 HTTP 엔드포인트), `buildRunInputRoute()` export. main.js와 preload.js 양쪽에서 참조.

**IPC 채널 확장**
| 네임스페이스 | v1.0.0 | v1.5.6 |
|-------------|--------|--------|
| splash | 2개 (`get-config`, `backend-ready`) | 2개 (변경 없음) |
| app | 1개 (`ready`) | 1개 (변경 없음) |
| bridge | 0개 | 11개 (`run`, `stop`, `status`, `get-url`, `get-cli-contract`, `get-quality-summary`, `get-quality-dashboard`, `get-safe-ops-preview`, `save-quality-review`, `resolve-prompt`, `save-settings`, `load-settings`) |
| material | 0개 | 3개 (`list-files`, `import-file`, `delete-file`) |
| project | 0개 | 6개 (`list`, `create`, `load-config-surfaces`, `save-config-surfaces`, `list-work-guard-templates`, `apply-work-guard-template`) |
| workspace | 0개 | 2개 (`open-folder`, `get-path`) |
| **합계** | **3개** | **25개** |

**Preload Bridge API**
- v1.0.0: 3개 메서드 (`getSplashConfig`, `notifyBackendReady`, `onAppReady`)
- v1.5.6: 25개 live 메서드 + 1개 deadCandidate 메서드

**Bridge HTTP Proxy**
- `bridgeFetch()` 신규 — 메인 프로세스에서 `http://127.0.0.1:8300` 프록시
- 타임아웃 5초, `AbortController` 기반
- 구조화된 에러 응답 (`NETWORK_ERROR`, `HTTP_{status}`)
- `DESKTOP_BRIDGE_TRANSPORT` envelope 규격 (`desktop_bridge_v1`)

**디버그 로깅 시스템 (신규)**
- `earlyDebugLog()`: require 전 로깅 (pid, execPath, resourcesPath, cwd)
- `debugLog()`: 정상 부팅 후 로깅
- 로그 경로: `%LOCALAPPDATA%/Geuldobi/electron-main.log`
- `uncaughtException`, `unhandledRejection` 전역 핸들러
- 윈도우별 이벤트 로깅: `did-finish-load`, `did-fail-load`, `render-process-gone`

### 3. 기능 추가

**백엔드 프로세스 관리**
- `startBackend()`: 개발 모드 `python -m uvicorn` / 배포 모드 `backend.exe` spawn
- `stopBackend()`: Windows `taskkill /t /f` / Unix `SIGTERM`
- 자동 재시작 (최대 2회, 2초 딜레이)
- 기동 타임아웃 경고 (15초)
- 환경 변수 주입: `GEULDOBI_DESKTOP_MODE`, `GEULDOBI_PACKAGED_RUNTIME_MODEL`, `GEULDOBI_WORKSPACE`, `GEULDOBI_PROJECTS_ROOT`

**프로젝트 관리**
- `listProjects()`: 프로젝트 디렉토리 목록 (lexical sort, main_a.py 호환)
- `createProject()`: 안전한 이름 sanitize + 디렉토리 생성
- `loadProjectConfigSurfaces()` / `saveProjectConfigSurfaces()`: author_directives.txt + work_guard.yaml 관리
- `listWorkGuardTemplates()`: 장르별 YAML 템플릿 탐색
- `applyWorkGuardTemplate()`: 경로 탈출 방지 + YAML 검증 후 적용

**재료 파일 관리**
- `listMaterialFiles()`: bible/treatments 폴더 파일 목록
- `importMaterialFile()`: OS 파일 선택 다이얼로그 → 복사
- `deleteMaterialFile()`: 경로 탈출 방지 (`..`, `/`, `\` 차단) + 삭제

**설정 영속화**
- `saveSettings()` / `loadSettings()`: `%LOCALAPPDATA%/Geuldobi/settings.json`
- 깨진 JSON 자동 백업 (`.bak`) + null 반환

**Workspace Seed 동기화**
- `syncPackagedWorkspaceSeed()`: 패키징 모드에서 `resources/workspace-seed` → `내 문서/글도비` 복사
- `copyMissingTree()`: 재귀적 누락 파일만 복사 (기존 파일 보존)
- 대상 폴더: `bible`, `treatments`, `projects`

**CLI Contract 브릿지**
- `CLI_CONTRACT`: 10개 장르 인덱스 맵, 기본 장르(investment=3), 프로젝트 정렬 순서
- 프론트엔드 장르 선택 → 백엔드 CLI 인덱스 변환

**Quality API Surface**
- `getQualitySummary()`: 프로젝트별 품질 요약 (lookback N회)
- `getQualityDashboard()`: 대시보드 데이터
- `getSafeOpsPreview()`: 안전 작업 미리보기
- `saveQualityReview()`: 운영자 품질 리뷰 저장
- `resolvePrompt()`: Mode B 프롬프트 응답

### 4. 보안/안정성

**Context Isolation 유지**
- `contextIsolation: true`, `nodeIntegration: false` — v1.0.0부터 유지
- Preload script를 통한 안전한 IPC 브릿지만 허용

**경로 탈출 방지**
- `sanitizeProjectName()`: `<>:"/\|?*` 문자 → `_` 치환
- `deleteMaterialFile()`: `..`, `/`, `\` 포함 시 거부
- `resolveWorkGuardTemplatePath()`: 라이브러리 루트 밖 경로 거부 + YAML 확장자 검증

**에러 처리 강화**
- `uncaughtException` / `unhandledRejection` 전역 핸들러
- `bridgeFetch()` 네트워크 에러/타임아웃 구조화된 응답
- 설정 파일 JSON 파싱 실패 시 백업 + 정상 반환
- `earlyDebugLog()` 실패 무시 (디버그 로깅 자체가 앱 크래시 유발 방지)
- `did-fail-load`, `render-process-gone` 이벤트 로깅

**CSP 메타태그**
- 7f0a4e53에서 추가 (Content-Security-Policy)

**Backend 장애 복원**
- 비정상 종료 시 자동 재시작 (최대 2회)
- `app.isQuitting` 플래그로 정상 종료 시 재시작 방지
- `before-quit` 이벤트에서 백엔드 정리

### 5. 빌드/배포

**electron-builder 설정 (신규)**
- `appId`: `com.geuldobi.desktop`
- `productName`: `Geuldobi`
- 대상: Windows NSIS 설치기
- 설치 언어: 한국어, 영어
- 설치 경로 변경 허용 (`allowToChangeInstallationDirectory: true`)
- 코드 서명 비활성화 (`signAndEditExecutable: false`)

**extraResources 번들**
- `../dist/backend` → `resources/backend` (PyInstaller 빌드)
- `../dist/engine` → `resources/engine`
- `../python-embed` → `resources/python-embed`
- `../dist/workspace-seed` → `resources/workspace-seed`

**빌드 스크립트**
- `scripts/build_workspace_seed.py` (113줄): bible/treatments/projects 시드 데이터 수집 → `dist/workspace-seed/`
- `scripts/build_app_icon.py` (94줄): 앱 아이콘 생성

**npm scripts 확장**
- v1.0.0: `start`, `start:spike`, `test`
- v1.5.6: + `prepare:workspace-seed`, `build` (workspace-seed 준비 + electron-builder), `build:dir`
- `test`: Python pytest 16개 + Node.js 테스트 3개 통합 실행

### 6. 의존성 변경

| 패키지 | v1.0.0 | v1.5.6 | 변경 |
|--------|--------|--------|------|
| electron | ^40.8.0 (dev) | ^40.8.0 (dev) | 유지 |
| cross-env | ^10.1.0 (dev) | 제거 | 삭제 |
| electron-builder | 없음 | ^25.1.8 (dev) | 신규 추가 |
| lucide | ^0.577.0 | ^0.577.0 | 유지 |

**description 변경**
- v1.0.0: `"Spike 4: Electron splash skeleton for Geuldobi desktop"`
- v1.5.6: `"글도비 — AI 웹소설 자동 생성 데스크톱"`

## 파일별 변경 요약

| 파일 | v1.0.0 줄수 | v1.5.6 줄수 | 변화량 | 주요 변경 |
|------|------------|------------|--------|-----------|
| `src/main.js` | 160 | 1,010 | +850 | 백엔드 관리, bridgeFetch, 22개 IPC 핸들러, 디버그 로깅, 프로젝트/재료/설정/workspace 관리 |
| `src/preload.js` | 7 | 97 | +90 | 3개 → 26개 API 메서드, 채널명 SSOT 참조 |
| `src/index.html` | 780 | 8,168 | +7,388 | 18개 → 123개 함수, 대시보드 12종, WebSocket, 설정 패널, 프로젝트 관리, 장르 모달 |
| `src/console_relay.js` | 없음 | 56 | +56 | 신규 — 렌더러 콘솔 릴레이 |
| `src/desktop_control_plane_contract.js` | 없음 | 96 | +96 | 신규 — IPC 채널/라우트 SSOT |
| `src/splash/splash.js` | 71 | 89 | +18 | 타임아웃 조정, 폴링 개선 |
| `src/splash/splash.html` | - | - | +3 | 미세 조정 |
| `src/splash/lucide.js` | 없음 | 19,306 | +19,306 | Lucide 아이콘 라이브러리 번들 |
| `src/sprite_test.html` | 없음 | 153 | +153 | 스프라이트 테스트 페이지 |
| `src/sprites/*.png` | 없음 | 33개 | +33 | 캐릭터(5종x3포즈) + 가구/배경 18종 |
| `package.json` | 17줄 | 81줄 | +64 | 빌드 설정, npm scripts, 의존성 변경 |
| `DESKTOP-GUIDE.md` | 없음 | 360 | +360 | 데스크톱 앱 가이드 문서 |
| `scripts/build_app_icon.py` | 없음 | 94 | +94 | 앱 아이콘 빌드 스크립트 |
| `scripts/build_workspace_seed.py` | 없음 | 113 | +113 | 워크스페이스 시드 빌드 스크립트 |
| `main.js` (루트) | 없음 | 9 | +9 | 루트 진입점 (src/main.js 위임) |
| `temp-electron-loadcheck.js` | 없음 | 13 | +13 | 디버그용 임시 파일 |
| `temp-electron-paths.js` | 없음 | 7 | +7 | 디버그용 임시 파일 |

## 통계

| 항목 | 값 |
|------|-----|
| 총 커밋 수 | 12 |
| 개발 기간 | 2026-03-08 ~ 2026-03-16 (9일) |
| 신규 파일 수 | 39개 (JS 4 + HTML 1 + PNG 33 + MD 1) |
| 총 변경 줄 수 | +33,898 / -1,040 (순증 32,858줄) |
| main.js 증가율 | 531% (160 → 1,010줄) |
| preload.js 증가율 | 1,271% (7 → 97줄) |
| index.html 증가율 | 947% (780 → 8,168줄) |
| IPC 채널 증가 | 3개 → 25개 (733% 증가) |
| JS 함수 수 증가 | 18개 → 123개 (583% 증가) |
| 빌드 스크립트 | 0개 → 2개 (207줄) |
| 테스트 통합 | 0개 → 19개 (pytest 16 + node 3) |
