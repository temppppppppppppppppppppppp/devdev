# S3: 프론트엔드 (Electron) SSOT

> 최종 갱신: 2026-03-18
> 소스: frontend-deepdive-3pass-audit, adversarial-3pass-audit R1/R2, react-adoption-deepdive-full-survey, react-migration-execution-roadmap
> 감리: 적대적 3-Pass 2회 (R1 + R2) + React 도입 조사 3PASS + 적대적 3PASS

---

## 1. 개관

| 항목 | 값 |
|------|-----|
| 런타임 | Electron 40.8.0 |
| 프레임워크 | 없음 (Vanilla JS monolith) |
| 번들러 | 없음 (직접 로드) |
| 아이콘 | Lucide (전체 번들) |
| 빌드 | electron-builder + NSIS (Windows) |
| 소스 파일 | main.js (1,010), preload.js (97), index.html (8,266) |
| 총 LOC | ~9,373 lines |

**설계 철학**: 단일 HTML 모놀리스. CSS/HTML/JS가 index.html 한 파일에 공존.
프레임워크 도입 없이 DOM 직접 조작으로 전체 UI를 구성한다.

---

## 2. Main Process (main.js, 1,010 lines)

### 2.1 Window Management

```
App ready
  → createSplashWindow()     # 스플래시 (480×360, frameless)
  → createMainWindow()       # 메인 (1400×900, minWidth 1024)
  → splash.close() on 'ready-to-show'
```

- 스플래시와 메인 윈도우 2단계 부팅
- 메인 윈도우: `minWidth: 1024, minHeight: 700`
- `nodeIntegration: false`, `contextIsolation: true` (보안 기본값 준수)

### 2.2 Backend Process Lifecycle

| 모드 | 경로 결정 | 비고 |
|------|-----------|------|
| dev | `python main_a.py` 직접 실행 | cwd = 프로젝트 루트 |
| prod | packaged .exe 경로 탐색 | resources/ 하위 |

- **Auto-restart**: 비정상 종료 시 최대 2회 재시작
- `process.env` 상속: 부모 프로세스 환경변수가 백엔드에 전달됨 (LOW 보안 이슈)
- 종료 시퀀스: `app.on('before-quit')` → 백엔드 프로세스 kill → 앱 종료

### 2.3 IPC Handlers

Main process에서 등록하는 IPC 핸들러 목록:

| 채널 | 방향 | 용도 |
|------|------|------|
| `bridge-fetch` | renderer → main | HTTP 프록시 (bridgeFetch) |
| `get-splash-config` | renderer → main | 스플래시 설정 조회 |
| `notify-backend-ready` | renderer → main | 백엔드 준비 완료 통지 |
| `switch-to-main` | renderer → main | 스플래시 → 메인 전환 |
| `read-settings` | renderer → main | settings.json 읽기 |
| `write-settings` | renderer → main | settings.json 쓰기 |
| `read-material` | renderer → main | 자료 파일 읽기 |
| `select-file` | renderer → main | 파일 선택 다이얼로그 |
| `select-directory` | renderer → main | 디렉토리 선택 다이얼로그 |
| `open-workspace` | renderer → main | 작업 폴더 열기 |
| `get-app-version` | renderer → main | 앱 버전 조회 |

- 전체 IPC 프로토콜 상세 → **S2 (BE-FE 연결 SSOT)** 참조

### 2.4 bridgeFetch Transport Protocol

```
Renderer (fetch 불가, CORS)
  → IPC 'bridge-fetch' { url, method, headers, body }
    → Main process: net.fetch() 실행
      → 응답 직렬화 → IPC 반환
```

- Electron의 `net` 모듈로 CORS 우회
- 요청/응답 모두 JSON 직렬화
- 타임아웃: main process 측 기본값 적용
- 상세 프로토콜 스펙 → **S2** 참조

### 2.5 File System Operations

| 작업 | 대상 | 경로 결정 |
|------|------|-----------|
| Settings R/W | settings.json | `app.getPath('userData')` |
| Material read | 사용자 자료 파일 | dialog 선택 경로 |
| Project I/O | 프로젝트 데이터 | workspace 하위 |
| Workspace open | 출력 폴더 | `shell.openPath()` |

- 모든 파일 I/O는 main process에서 수행 (renderer는 IPC 경유)

---

## 3. Preload Bridge (preload.js, 97 lines)

### 3.1 노출 API

```javascript
contextBridge.exposeInMainWorld("geuldobiDesktop", {
    bridgeFetch:       (url, options) => ipcRenderer.invoke('bridge-fetch', ...),
    getSplashConfig:   ()             => ipcRenderer.invoke('get-splash-config'),
    notifyBackendReady:()             => ipcRenderer.invoke('notify-backend-ready'),
    switchToMain:      ()             => ipcRenderer.invoke('switch-to-main'),
    readSettings:      ()             => ipcRenderer.invoke('read-settings'),
    writeSettings:     (data)         => ipcRenderer.invoke('write-settings', data),
    readMaterial:      (path)         => ipcRenderer.invoke('read-material', path),
    selectFile:        (options)      => ipcRenderer.invoke('select-file', options),
    selectDirectory:   ()             => ipcRenderer.invoke('select-directory'),
    openWorkspace:     (path)         => ipcRenderer.invoke('open-workspace', path),
    getAppVersion:     ()             => ipcRenderer.invoke('get-app-version'),
});
```

### 3.2 Channel Hardcoding Rationale

- 채널 이름이 문자열 리터럴로 하드코딩됨
- 이유: sandboxed preload 환경에서 외부 모듈 import 불안정
- 공유 상수 파일 사용 시 빌드 경로 문제 발생 위험
- **트레이드오프**: 채널명 불일치 위험 vs 빌드 안정성 → 현재 안정성 우선

### 3.3 보안 경계

- `contextIsolation: true` — renderer와 preload 컨텍스트 분리
- `nodeIntegration: false` — renderer에서 Node.js API 접근 차단
- `sandbox: true` (Electron 기본값)
- renderer → main 통신은 반드시 `ipcRenderer.invoke()` 경유

---

## 4. Renderer (index.html, 8,266 lines)

### 4.1 파일 구조

| 영역 | 라인 수 | 비율 |
|------|---------|------|
| CSS (인라인 `<style>`) | ~2,765 | 33.5% |
| HTML (마크업) | ~714 | 8.6% |
| JS (인라인 `<script>`) | ~4,778 | 57.8% |
| **합계** | **8,266** | 100% |

- 단일 파일에 모든 프론트엔드 코드 집중
- 외부 의존성: Lucide Icons CDN/번들만

### 4.2 Global State Variables

renderer JS 영역에서 관리되는 주요 전역 상태 (frontend-improvement-survey lines 276-294 기준):

| 변수 | 위치 (index.html) | 용도 |
|------|-------------------|------|
| `officeState` | :3581 | 사무실 캔버스 통합 상태 (30+ 필드) |
| `_backendConnected` | :5826 | 백엔드 연결 플래그 |
| `_ws` | :5827 | WebSocket 인스턴스 |
| `_wsReconnectTimer` | :5828 | WS 재연결 타이머 ID |
| `_commandPathReady` | :5829 | 커맨드 경로 준비 플래그 |
| `_statusSyncInFlight` | :5830 | 상태 동기화 진행 중 플래그 |
| `_pendingPromptQueue` | :5831 | 대기 프롬프트 큐 |
| `_currentPrompt` | :6344 | 현재 활성 프롬프트 |
| `_bootPhase` | :6345 | 부팅 단계 상태 |
| `_safeOpsConfirmResolve` | :3667 | 안전 확인 다이얼로그 resolve 콜백 |
| `_clickBubble` | :3731 | 클릭 버블 애니메이션 상태 |
| `_noticeCursor`, `_noticeX` | :5755-5759 | 공지 애니메이션 커서/좌표 |

### 4.3 Office Canvas + rAF Infinite Loop (LOW)

```javascript
function animateOffice() {
    // 사무실 캔버스 렌더링
    requestAnimationFrame(animateOffice);  // 무한 루프
}
```

- `requestAnimationFrame` 기반 무한 렌더 루프
- 사무실 뷰가 비활성일 때도 계속 실행됨
- **심각도**: LOW — 브라우저 탭 비활성 시 자동 throttle, 실측 CPU 영향 미미
- **개선안**: 뷰 전환 시 루프 정지/재개 (미착수)

### 4.4 Mission/Agent Board 500ms Rebuild (INFO)

```javascript
setInterval(() => {
    rebuildMissionBoard();  // 전체 DOM 재구성
}, 500);
```

- 500ms 간격으로 미션 보드 전체 DOM을 재구성
- Virtual DOM 없이 innerHTML 교체 방식
- **심각도**: INFO — 현재 에이전트 수에서는 성능 영향 미미
- **개선안**: 변경 감지 후 선택적 업데이트 (미착수)

### 4.5 Log Stream 500-Line Limit

- 로그 버퍼: 최대 500줄 유지
- 초과 시 오래된 로그부터 삭제 (FIFO)
- WebSocket으로 실시간 수신
- 자동 스크롤 (사용자 스크롤 위치 존중)

### 4.6 Error Handling

| 패턴 | 개수 | 위험도 | 설명 |
|------|------|--------|------|
| Silent `.catch(() => {})` | 8 | MEDIUM | 에러 무시, 디버깅 어려움 |
| `_ws.onerror = () => {}` | 1 | INFO | WebSocket 에러 무시 (R2에서 MEDIUM → INFO 하향) |
| `try/catch` with console.error | 다수 | — | 정상 패턴 |

Silent `.catch` 8개 위치 (index.html):
`:5983`, `:6222`, `:6253`, `:6376`, `:7686`, `:7800`, `:7805`, `:7961`

- 8개의 silent catch: 네트워크 실패, 파일 I/O 실패 등에서 에러를 삼킴
- **권장**: 최소한 console.warn 추가 + 사용자 facing 에러는 toast 알림

### 4.7 HTML Escape / XSS 방어

```javascript
function escapeHtml(text) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}
```

- `escapeHtml()` 유틸리티 존재
- innerHTML 사용 지점의 ~95%에서 적절히 이스케이프 적용
- 나머지 ~5%: 신뢰할 수 있는 내부 데이터 (서버 응답)로 판단하여 미적용
- **잔존 위험**: 서버 응답이 오염될 경우 XSS 가능 (현실적 위험은 낮음)

---

## 5. Splash Bootstrap

### 5.1 부팅 시퀀스

```
DOMContentLoaded
  → getSplashConfig()           # 백엔드 설정 조회
  → pollBackendReady()          # 백엔드 헬스체크 반복
    ├─ 성공 → notifyBackendReady()
    │         → switchToMain()  # 메인 윈도우 전환
    └─ 실패 → 재시도 (최대 MAX_POLL_FAILS회)
```

### 5.2 타이밍 이슈

| 파라미터 | 값 | 설명 |
|----------|-----|------|
| Poll interval | 1,000ms | 백엔드 헬스체크 간격 |
| MAX_POLL_FAILS | 30 | 최대 재시도 횟수 (= 30초) |
| Fallback timer | 8,000ms | 강제 전환 타이머 |

- **타이밍 충돌**: Fallback 8s 타이머가 MAX_POLL_FAILS 30s보다 먼저 발동
- 의미: 백엔드가 8초 내 미응답이면 폴링 루프 완료 전에 강제 전환됨
- **실제 영향**: 백엔드 평균 기동 시간 < 5초이므로 정상 동작에서는 문제 없음
- 백엔드가 8-30초 사이에 기동되는 엣지 케이스에서만 문제 가능

---

## 6. 보안

### 6.1 HIGH Severity

#### sanitizeProjectName 경로 탐색 (Path Traversal)

```javascript
function sanitizeProjectName(name) {
    return name.replace(/[<>:"/\\|?*]/g, '_');
}
```

- `..` 시퀀스가 필터링되지 않음
- 입력: `../../etc/passwd` → 출력: `....etcpasswd` (부분 치환만)
- 실제로 `..` 자체는 남아 있어 경로 탐색 가능
- **완화 요인**: Electron file dialog를 통한 입력이 대부분 → 사용자 직접 입력 경로 제한적
- **영향 범위 (SEC-07)**: 3개 IPC 핸들러 영향: `project:loadConfigSurfaces` (읽기), `project:saveConfigSurfaces` (쓰기), `project:applyWorkGuardTemplate` (쓰기)
- **권장**: `..` 명시적 필터링 또는 `path.resolve()` 후 허용 범위 검증

### 6.2 MEDIUM Severity

| 이슈 | 설명 | 상태 |
|------|------|------|
| CSP unsafe-inline | `<style>`, `<script>` 인라인 사용으로 CSP에 unsafe-inline 필요 | 구조적 제약 |
| python-embed 버전 고정 | 패키징된 Python 런타임 버전 고정, 보안 패치 지연 가능 | 모니터링 필요 |
| .exe 테스트 부재 | 패키징된 .exe에 대한 자동화 테스트 없음 | 미착수 |

### 6.3 LOW Severity

| ID | 이슈 | 설명 |
|----|------|------|
| — | process.env 상속 | 부모 환경변수가 백엔드에 전달 — 민감 변수 노출 가능 |
| — | 미사용 CSP origin | CSP에 불필요한 origin 포함 |
| — | main IPC key whitelist 부재 | IPC 핸들러에 허용 키 화이트리스트 없음 |
| — | window.prompt blocking | Electron에서 window.prompt() 차단됨 — 일부 코드 경로 영향 |
| — | rAF infinite loop | 비활성 뷰에서도 렌더 루프 지속 (4.3 참조) |
| NEW-01 | Settings IPC size unlimited | write-settings IPC에 페이로드 크기 제한 없음 (R2 후 LOW) |
| SEC-06 | Settings/log plaintext storage | settings.json, 로그 파일이 평문 저장 |
| BUILD-01 | Sprites bundling | Lucide 외 스프라이트 에셋 번들링 미최적화 |
| BUILD-02 | Code signing | 빌드 산출물(.exe)에 코드 서명 없음 |
| TEST-01 | IPC E2E test absence | IPC 채널에 대한 E2E 테스트 부재 |
| DEP-01 | Electron security patches | Electron 40.x 보안 패치 적시 적용 체계 미비 |

### 6.4 INFO Severity

| ID | 이슈 | 설명 |
|----|------|------|
| — | setInterval DOM rebuild | 500ms 간격 미션 보드 재구성 (4.4 참조) |
| — | Lucide full bundle | 전체 아이콘 번들 로드 — 실제 사용은 일부 |
| — | 단일 파일 모놀리스 | 8,266줄 단일 HTML — 유지보수 부담 |
| MISS-01 | addEventListener 누수 | 63개 addEventListener, 0개 removeEventListener — 장기 실행 시 리스너 누적 가능 |

---

## 7. React 도입 조사 결과

> 상세 조사서: `OPUS/react 도입/react-adoption-deepdive-full-survey.md` (1,130행)
> 실행 로드맵: `OPUS/react 도입/react-migration-execution-roadmap.md` (2,558행)

### 7.1 현재 프론트엔드 정량 지표

| 지표 | 수치 | 코드 근거 |
|------|------|----------|
| 함수 정의 (function + arrow) | 134개 | `index.html` 인라인 `<script>` |
| getElementById | 198회 | `index.html` |
| querySelector/All | 30회 (16+14) | `index.html` |
| innerHTML 대입 | 50회 | `index.html` |
| addEventListener | 63회 | `index.html` |
| removeEventListener | **0회** | `index.html` — 리스너 누수 |
| classList 조작 | 70회 | `index.html` |
| .style.* 직접 변경 | 33회 | `index.html` |
| CSS 클래스 (style 블록) | 281개 | `index.html:8-2772` |
| CSS custom properties | 11개 | `index.html` `:root` |
| @media 쿼리 | 3개 | 860px, 900px, 1280px |
| 렌더 함수 | 21개 | 15 display + 6 refresh/update |
| Canvas 드로잉 함수 | 16개 | `index.html:5233-5823` |
| UI 섹션 | 32개 | TopBar ~ PromptOverlay |
| 전역 상태 변수 | 21+개 | officeState 등 |

### 7.2 React 도입 시 위협 (22건)

| 심각도 | 건수 | 대표 위협 |
|--------|------|----------|
| **CRITICAL** | 2 | 21+ 전역 상태 마이그레이션 (B3.1), 하이브리드 DOM 소유권 충돌 (B3.2) |
| **HIGH** | 6 | CSP 깨짐 (B1.2), app:ready 타이밍 (B2.3), WS 라이프사이클 (B2.4), 이중 빌드 출력 (B5.1), dev/prod 경로 분기 (B5.3), 기존 테스트 5-6개 파괴 (B6.1) |
| **MEDIUM** | 6 | electron-builder 충돌, Vite file://, 순환 상태, 스프라이트 경로, 테스트 인프라 부재, StrictMode 이중 렌더 |
| **LOW** | 8 | contextIsolation 호환, bridgeFetch 무변경, Canvas 공존, ASAR, 번들 크기(+142KB), 가상 DOM 오버헤드, 메모리, 성능 |
| **블로커** | 0 | 없음 — 모든 위협에 완화책 존재 |

### 7.3 React 도입 시 이득 (정량)

| 현재 | React 전환 후 | 개선 |
|------|-------------|------|
| innerHTML 50건 | **0건** (JSX 자동 이스케이프) | XSS 표면 제거 |
| addEventListener 63 / removeEventListener 0 | useEffect cleanup 자동 | 리스너 누수 해소 |
| 전역 상태 21+개 분산 | Zustand 5 슬라이스 1 스토어 | 상태 추적 용이 |
| 500ms 폴링 (setInterval) | 리액티브 구독 | 불필요 렌더 제거 |
| CSS 281 전역 클래스 | CSS Modules 스코핑 | 클래스 충돌 제거 |
| 테스트 커버리지 0% | **70%** 가능 | 회귀 방지 |
| TypeScript 없음 | **전면 TypeScript** | 타입 안전 |
| 파일 1개 8,266행 | **~50파일** 각 100-300행 | 협업·유지보수 |

### 7.4 기술 선택 권장

| 항목 | 선택 | 이유 |
|------|------|------|
| 프레임워크 | **React 19** | Electron Canvas 통합 성숙도, 생태계, 커뮤니티 |
| 상태 관리 | **Zustand v5** | officeState 뮤테이션 패턴과 1:1 대응, 보일러플레이트 최소 |
| CSS | **CSS Modules** | Vite 네이티브 지원, 런타임 비용 0, 현재 CSS 변수 시스템 호환 |
| 빌드 | **electron-vite** | main/preload/renderer 3-프로세스 빌드 통합, HMR |
| 테스트 | **Vitest + React Testing Library** | Vite 네이티브 통합, Jest 호환 API |

### 7.5 마이그레이션 6단계 로드맵 요약

| Phase | 내용 | 예상 시간 | 검증 기준 |
|-------|------|----------|----------|
| **0** | 빌드 인프라 (electron-vite + React + TS) | 8-12h | `npm run dev` "Hello React" 표시 |
| **1** | 타입 기반 + Zustand 스토어 5개 + 훅 3개 | 16-24h | `tsc --noEmit` 에러 0건 |
| **2** | 공유 UI 컴포넌트 10개 (Button, Card, Modal 등) | 20-28h | Vitest 컴포넌트 테스트 통과 |
| **3** | 기능 패널 6개 (Settings→Log→Run→Quality→Office→Project) | 88-116h | 각 패널 기능 동일 확인 |
| **4** | 레이아웃 셸 + initializeWorkspaceLayout 대체 | 12-16h | 인라인 `<script>` 0행 |
| **5** | 정리 + 테스트 70% + strict mode | 16-24h | 레거시 코드 삭제 완료 |
| **총계** | — | **160-220h** | 1인 풀타임 ~6주, 2-3인 팀 ~3-4주 |

크리티컬 패스: Phase 0 → 1 → 2 → **3d (Quality, 최대 병목 24-32h)** → 4 → 5

### 7.6 권장 시기

| 시점 | 조치 |
|------|------|
| **지금~1.6.0** | 코드 수정 없음. 로드맵 확정만. |
| **1.6.0 직후** | Phase 0-1 실행 (빌드 인프라 + 타입/스토어) |
| **2.0.0 향해** | Phase 2-3 점진적 패널 전환 |
| **2.0.0 이후** | Phase 4-5 레이아웃 셸 완성 + 정리 |

### 7.7 비권장: 전면 재작성 (Big Bang)

1인 개발 체제에서 3-5주 FE 차단 → 백엔드 개발 중단 → 1.6.0/2.0.0 릴리스 목표 위협. 점진적 Strangler Fig 패턴 권장.

---

## 8. 수치 종합 요약표

| 지표 | 값 |
|------|-----|
| 총 소스 파일 | 3 (main.js, preload.js, index.html) |
| 총 LOC | 9,373 |
| IPC 채널 수 | 25 live + 1 DC (간략 그룹 11개, 전체 목록 → S2 §2.2) |
| 전역 상태 변수 | 13 (§4.2 주요) / 21+ (§7.1 전체 let 포함); officeState 30+ 하위 필드 별도 |
| Silent catch | 8 |
| innerHTML 사용 지점 | 다수 (~95% escaped) |
| HIGH 보안 이슈 | 1 (path traversal) — §7.2 마이그레이션 위협(HIGH 6건)은 별도 집계 |
| MEDIUM 보안 이슈 | 3 |
| LOW 보안 이슈 | 11 |
| INFO 이슈 | 4 |
| setInterval 활성 | 1 (500ms) |
| rAF 루프 | 1 (무한) |
| Electron 버전 | 40.8.0 |
| Node 버전 (Electron 내장) | Electron 40.x 번들 |

---

## [부록 A] 감리 이력

### Severity Progression: R1 → R2

| 이슈 | R1 판정 | R2 재판정 | 변동 사유 |
|------|---------|-----------|-----------|
| sanitizeProjectName path traversal | HIGH | HIGH | 유지 — 코드 미변경 |
| CSP unsafe-inline | HIGH | MEDIUM | 하향 — 단일 HTML 모놀리스에서 구조적 불가피 |
| Silent .catch | MEDIUM | MEDIUM | 유지 |
| process.env inheritance | MEDIUM | LOW | 하향 — 로컬 실행 환경에서 실질 위험 낮음 |
| rAF infinite loop | LOW | LOW | 유지 |
| setInterval rebuild | INFO | INFO | 유지 |
| Lucide full bundle | — | INFO | R2에서 신규 식별 |
| Fallback timer < MAX_POLL | — | LOW | R2에서 신규 식별 |

### 감리 방법론

1. **R1 (frontend-deepdive-3pass-audit)**: 코드 전수 조사 3-pass
   - Pass 1: 구조 파악 + 데이터 흐름 추적
   - Pass 2: 보안/에러 핸들링 집중 점검
   - Pass 3: 성능/유지보수성 평가

2. **R2 (adversarial-3pass-audit)**: 적대적 관점 재감리
   - Pass 1: R1 결과에 대한 반론 수집
   - Pass 2: 실제 공격 시나리오 시뮬레이션
   - Pass 3: severity 재판정 + 최종 확정

---

## [부록 B] 근거 파일

| 파일 | 위치 | LOC | 역할 |
|------|------|-----|------|
| main.js | frontend/main.js | 1,010 | Electron main process |
| preload.js | frontend/preload.js | 97 | Context bridge |
| index.html | frontend/index.html | 8,266 | Renderer (CSS+HTML+JS) |
| package.json | frontend/package.json | — | Electron 의존성 |
| electron-builder.yml | frontend/ | — | 빌드 설정 |
| frontend-deepdive-3pass-audit | OPUS/ | — | R1 감리 문서 |
| adversarial-3pass-audit | OPUS/ | — | R2-1 감리 문서 |
| adversarial-3pass-audit-r2 | OPUS/ | — | R2-2 감리 문서 |
| react-adoption-deepdive-full-survey | OPUS/react 도입/ | 1,130 | React 도입 전면 딥다이브 |
| react-migration-execution-roadmap | OPUS/react 도입/ | 2,558 | React 마이그레이션 실행 로드맵 |

---

## [부록 C] 관련 SSOT 참조

| 참조 | 내용 |
|------|------|
| S1 | 전체 아키텍처 개관 — 프론트엔드 위치 확인 |
| S2 | BE-FE 연결 — IPC 프로토콜 전체 스펙, bridgeFetch 상세 |
| S4 | LLM 통합 — WebSocket 경유 실시간 스트리밍 관련 |
| S5 | Stage 0-2 내부 — 프론트엔드에서 트리거하는 파이프라인 시작점 |

---

*끝 — S3 프론트엔드 (Electron) SSOT*
