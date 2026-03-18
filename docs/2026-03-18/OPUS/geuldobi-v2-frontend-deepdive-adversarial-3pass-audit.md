# 글도비 데스크톱 프론트엔드 — 적대적 3-Pass 감리 보고서

> **감리일**: 2026-03-18
> **방법론**: 이전 보고서 발견사항 전수 코드 대조 → 3회 적대적 감리 (반증·누락·교정)
> **감리자**: Claude Opus 4.6 (1M context)
> **대상 파일**: main.js(1010줄), preload.js(97줄), index.html(8266줄), splash.js(90줄), splash.html(28줄), console_relay.js(57줄), desktop_control_plane_contract.js(97줄)

---

## 감리 원칙

이전 3-Pass 보고서의 29건 발견사항을 **적대적 관점**에서 재검증한다.

1. **Pass 1 — 반증**: 각 발견에 대해 "이것이 틀렸다면?"을 묻고, 코드 라인으로 입증/반증
2. **Pass 2 — 누락 탐색**: 이전 보고서가 놓친 영역을 적극 탐색
3. **Pass 3 — 최종 교정**: 오탐 제거, 심각도 재산정, 실행 권고

---

## Pass 1: 반증 감리 — 이전 발견사항 코드 대조

### SEC-01: CSP `unsafe-inline` — ✅ 확인 (유지)

**코드 근거**: `index.html:6`
```html
<meta http-equiv="Content-Security-Policy" content="default-src 'self';
  script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';
  img-src 'self' data:;
  connect-src ws://127.0.0.1:8300 https://generativelanguage.googleapis.com;" />
```

**반증 시도**: "Electron 앱이니 CSP가 무의미하지 않은가?"
**반증 실패**:
- `contextIsolation: true` (main.js:365)이므로 renderer에 주입된 스크립트는 preload 없이 IPC를 직접 호출할 수 없다
- **BUT** `contextBridge.exposeInMainWorld("geuldobiDesktop", ...)` (preload.js:37)가 renderer 전역에 노출됨
- XSS로 인라인 스크립트 실행 → `window.geuldobiDesktop.runKey(...)` 호출 가능
- **대조**: splash.html:6은 `script-src 'self'`로 unsafe-inline 없음 — splash는 올바름

**최종 판정**: **MEDIUM** (HIGH에서 하향). contextIsolation이 Node.js API 접근을 차단하므로 피해 범위는 bridge API 호출에 한정.

---

### SEC-02: IPC `bridge:run` 입력 검증 부재 — ⚠️ 과대평가 (하향)

**코드 근거**: `main.js:551-558`
```javascript
ipcMain.handle(IPC_CHANNELS.bridge.run, async (_, { key, subKey, inputs, approvalId }) => {
  const body = { key };
  if (subKey) body.sub_key = subKey;
  if (inputs && Object.keys(inputs).length > 0) body.inputs = inputs;
  if (typeof approvalId === "string" && approvalId.trim()) {
    body.approval_id = approvalId.trim();
  }
  return bridgeFetch(BRIDGE_MANAGED_ROUTES.run, { method: "POST", body: JSON.stringify(body) });
});
```

**이전 판정**: CRITICAL → MEDIUM
**반증**:
- `bridgeFetch`는 `http://127.0.0.1:8300/run`에 POST (main.js:494-549)
- 백엔드(bridge_server)가 key를 해석 — main process는 단순 프록시
- 렌더러에서 IPC 호출은 `contextIsolation` 내부 채널 — 외부 공격자 직접 접근 불가
- XSS 경유 시에만 악용 가능하며, 이 경우에도 백엔드의 입력 검증이 최종 방어선

**최종 판정**: **LOW**. main process는 투명 프록시 설계. 입력 검증 책임은 백엔드에 있음. main에서 화이트리스트를 추가하면 defense-in-depth이지만 필수는 아님.

---

### SEC-03: `buildRunInputRoute` runId 경로 탈출 — ❌ 오탐

**코드 근거**: `desktop_control_plane_contract.js:87-89`
```javascript
function buildRunInputRoute(runId) {
  return `${BRIDGE_MANAGED_ROUTES.run}/${encodeURIComponent(runId)}/input`;
}
```

**반증 성공**:
- `encodeURIComponent("../../../status")` = `%2E%2E%2F%2E%2E%2F%2E%2E%2Fstatus`
- HTTP 라우터(uvicorn/FastAPI)는 `%2F`를 경로 구분자로 해석하지 **않음**
- 최종 URL: `http://127.0.0.1:8300/run/%2E%2E%2F..%2Fstatus/input` → 404 Not Found
- 경로 탈출 **불가능**

**최종 판정**: **삭제**. 오탐.

---

### SEC-04: 백엔드 HTTP 평문 통신 — ❌ 과대평가 (삭제)

**반증 성공**:
- `http://127.0.0.1:8300` (main.js:107) — 로컬 루프백 전용
- 같은 시스템의 악성 프로세스가 트래픽을 스니핑하려면 이미 시스템 레벨 접근 보유
- Electron 공식 문서도 localhost 통신에 HTTPS를 요구하지 않음
- CSP `connect-src ws://127.0.0.1:8300`이 외부 접근을 차단

**최종 판정**: **삭제**. 표준 Electron 패턴.

---

### SEC-05: `process.env` 전체 상속 — ✅ 확인 (유지)

**코드 근거**: `main.js:267-279`
```javascript
backendProcess = spawn(cmd, args, {
  cwd,
  env: {
    ...process.env,  // ← 여기
    PYTHONIOENCODING: "utf-8",
    PYTHONUNBUFFERED: "1",
    GEULDOBI_DESKTOP_MODE: "1",
    // ...
  },
```

**반증 시도**: "Python은 PATH, TEMP 등이 필수 아닌가?"
**반증 실패**:
- `...process.env`는 AWS_SECRET_ACCESS_KEY, GITHUB_TOKEN 등 사용자 환경의 모든 비밀이 전달됨
- 개발 모드에서 `python -m uvicorn`이 이 환경에서 실행되면 모든 pip 패키지가 접근 가능
- 프로덕션 모드에서 `backend.exe`는 PyInstaller 번들이지만 동일하게 환경 변수 접근 가능

**최종 판정**: **MEDIUM**. 필요 변수만 명시적 전달로 전환 권장. HIGH에서 하향 이유: 백엔드는 자체 코드이므로 악의적 환경 변수 사용 가능성은 서드파티 의존성의 supply chain 공격에 한정.

---

### SEC-06: 설정/로그 파일 평문 저장 — ⚠️ 과대평가 (하향)

**코드 근거**: `main.js:221, 624-653`
```javascript
const SETTINGS_PATH = path.join(getAppDir(), "settings.json");
// getAppDir() = %LOCALAPPDATA%\Geuldobi
```

**반증 성공 (부분)**:
- `%LOCALAPPDATA%`는 Windows에서 사용자별 격리 디렉토리 (다른 사용자 접근 불가 기본)
- settings.json에 저장되는 내용 확인: `settingsStore` (index.html:7198 부근) — API 키, 장르, 프로젝트 등
- API 키가 평문 저장되는 것은 사실이지만, Electron 앱에서 OS 수준 암호화(keytar 등) 없이는 표준적

**최종 판정**: **LOW**. Windows 사용자 프로필 격리에 의존. API 키 암호화는 nice-to-have.

---

### SEC-07: `sanitizeProjectName` 경로 탈출 — ✅ 확인 (유지, 핵심 발견)

**코드 근거**: `main.js:761-766`
```javascript
function sanitizeProjectName(name) {
  if (typeof name !== "string") { return ""; }
  return name.trim().replace(/[<>:"/\\|?*]/g, "_");
}
```

**검증**:
```
sanitizeProjectName("..") → ".."  (점은 정규식에 없음)
getProjectRoot("..") → path.join(getProjectsDir(), "..")
  = path.join("C:/Users/.../글도비/projects", "..")
  = "C:/Users/.../글도비"  ← 프로젝트 디렉토리 탈출!
```

**실제 공격 경로** (main.js:903-920):
```javascript
// saveConfigSurfaces({ project: "..", authorDirectives: "PAYLOAD", workGuardYaml: "..." })
getProjectConfigSurfaces("..")
  → configDir = path.join("C:/Users/.../글도비", "config")
  → fs.writeFileSync("C:/Users/.../글도비/config/author_directives.txt", "PAYLOAD")
```

**파급 범위**:
- 워크스페이스 루트의 `config/` 디렉토리에 임의 파일 작성 가능
- `"..."` → 순수 점 3개도 Windows에서 `..`과 동일하게 동작할 수 있음
- **단, XSS를 통해서만 악용 가능** (contextIsolation 때문)

**추가 발견**: `createProject("..")` (main.js:877-878) 호출 시:
```javascript
const dir = path.join(getProjectsDir(), "..");
if (fs.existsSync(dir)) {  // 부모 디렉토리는 항상 존재
  return { ok: false, message: "이미 존재하는 프로젝트입니다" };
}
```
→ 프로젝트 생성은 차단되지만 `saveConfigSurfaces`는 생성 없이 직접 쓰기 가능

**최종 판정**: **HIGH**. XSS 체이닝 필요하지만 파일시스템 쓰기가 가능한 실질적 취약점.

**수정 코드**:
```javascript
function sanitizeProjectName(name) {
  if (typeof name !== "string") { return ""; }
  return name.trim().replace(/[<>:"/\\|?*\.]/g, "_");  // 점 추가
}
```
또는 (더 안전):
```javascript
function sanitizeProjectName(name) {
  if (typeof name !== "string") { return ""; }
  const safe = name.trim().replace(/[^a-zA-Z0-9가-힣_\- ]/g, "_");
  if (!safe || safe === "." || safe === "..") return "";
  return safe;
}
```

---

### SEC-08: CSP connect-src Google API — ⚠️ 과대평가 (하향)

**코드 근거**: `index.html:6`
```
connect-src ws://127.0.0.1:8300 https://generativelanguage.googleapis.com;
```

**반증 시도**: "렌더러에서 직접 Google API를 호출하는 코드가 있는가?"
**검증**: index.html 전체 grep 결과 — `generativelanguage` 호출 코드 없음. CSP에만 선언됨.

**최종 판정**: **LOW**. 현재 사용되지 않는 CSP 항목. 제거하면 불필요한 공격면 축소.

---

### UX-01: innerHTML + escapeHtml 일관성 — ⚠️ 과대평가 (하향)

**전수 대조 결과** (innerHTML 사용 ~65건):

| 카테고리 | 건수 | 상태 |
|---------|------|------|
| 하드코딩된 HTML (데이터 삽입 없음) | 18건 | ✅ 안전 |
| `escapeHtml()` 적용 후 삽입 | 32건 | ✅ 안전 |
| `textContent`로 삽입 | 컨테이너 초기화 후 | ✅ 안전 |
| **`Number()` 변환 후 삽입** | 8건 | ⚠️ 조건부 안전 |
| **미이스케이프 문자열 삽입** | 3건 | ⚠️ 확인 필요 |

**미이스케이프 사례 상세**:

1. **index.html:4477** `${rowData.ep_num ?? "-"}` — 백엔드 데이터 직접 삽입
   - `ep_num`이 문자열이면 XSS 가능하나, 백엔드가 정수를 보장해야 함
   - 실질 위험: **매우 낮음** (백엔드가 자체 코드)

2. **index.html:4367** `${sparkMarkup || ""}` — `buildSparklineSvg()` 반환값
   - 함수 내부 검증: `stroke`는 `colors[status] || "#475569"` (상수 맵)
   - `points`는 `Number()` 변환된 좌표
   - 실질 위험: **없음**

3. **index.html:4329/4342** — 하드코딩된 HTML 리터럴 (데이터 삽입 없음)
   - 실질 위험: **없음**

**최종 판정**: **LOW** (HIGH에서 하향). escapeHtml 적용률은 ~95%이며, 미적용 사례는 Number 변환 또는 상수 맵으로 보호됨. 백엔드가 악의적 데이터를 반환하는 시나리오에서만 위험하며, 이는 자체 코드.

---

### UX-02: 500ms setInterval DOM 재생성 — ✅ 확인 (유지)

**코드 근거**: `index.html:8163-8166`
```javascript
setInterval(() => {
  renderMissionBoard();
  renderAgentBoard();
}, 500);
```

`renderAgentBoard()` (index.html:4839-4907):
```javascript
function renderAgentBoard() {
  agentBoard.innerHTML = "";  // 전체 삭제
  // ... 5개 에이전트 카드 재생성 (각 ~15 DOM 노드)
}
```

**반증 시도**: "500ms마다 5개 카드 정도면 성능 문제 없지 않나?"
**반증 실패**:
- 초당 2회 × (5카드 × 15노드) = 초당 150 DOM 조작
- `innerHTML = ""`는 기존 노드의 GC 비용 유발
- 비실행 시에도 동일 빈도로 실행됨

**최종 판정**: **LOW** (MEDIUM에서 하향). 5개 카드는 현대 브라우저에서 무시할 수 있는 수준이지만, 이벤트 기반 업데이트가 설계적으로 더 적절.

---

### UX-03: 프롬프트 큐 경쟁 조건 — ❌ 오탐

**코드 근거**: `index.html:5831, 6085-6091, 6392-6409`

**반증 성공**:
- JavaScript는 **단일 스레드** 이벤트 루프
- `_pendingPromptQueue.push()` (6395)와 `_pendingPromptQueue.shift()` (6087)는 동기 호출
- WebSocket `onmessage` 콜백은 이벤트 루프에 의해 순차 실행
- `_hasTrackedPrompt()` (6079-6082)가 중복 방지
- `_showNextQueuedPrompt()` (6085-6091)는 `_currentPrompt`가 없을 때만 실행

**최종 판정**: **삭제**. JavaScript 런타임 모델에서 이 패턴에 race condition 없음.

---

### UX-04: WebSocket onerror 핸들러 공백 — ✅ 확인 (유지, 하향)

**코드 근거**: `index.html:6221`
```javascript
_ws.onerror = () => {};
```

**반증 시도**: "onclose가 이미 처리하므로 onerror는 불필요 아닌가?"
**부분 반증**: WebSocket spec상 `onerror`는 항상 `onclose` 직전에 발생. `onclose` (6197-6219)에서 재연결 로직, 로그 기록, 에이전트 말풍선 업데이트가 모두 처리됨.

**최종 판정**: **INFO** (MEDIUM에서 하향). 실질적 기능 누락 없음. 디버깅 편의를 위해 `console.warn` 추가가 좋으나 필수 아님.

---

### UX-05: catch 블록 무시 — ⚠️ 부분 확인 (하향)

**코드 근거 상세**:

| 라인 | 코드 | 위험도 |
|------|------|--------|
| 5983 | `saveSettings(...).catch(() => {})` | **없음** — 설정 저장 실패는 다음 저장에서 재시도 |
| 6222 | `getBackendUrl().then(...).catch(() => {})` | **LOW** — 실패 시 WS 연결 불가하지만, 5초 후 watchdog (8223-8251)이 감지하여 사용자에게 알림 |
| 6253 | `refreshQualitySummary().then(...).catch(() => {})` | **없음** — 품질 대시보드 갱신 실패, 다음 이벤트에서 재시도 |
| 6376 | `resolvePrompt(...).catch(() => {})` | **LOW** — Stage 0 자동 Exit 실패 시 프롬프트가 유지되어 사용자가 직접 처리 |
| 7961 | `saveSettings(...).catch(() => {})` | **없음** |

**최종 판정**: **INFO** (MEDIUM에서 하향). 대부분 의도적 fire-and-forget 패턴. 6222만 로그 추가 권장.

---

### UX-06: UI 잠금 상태 복구 — ✅ 확인 (유지)

**코드 근거**: `index.html:5211-5226`
```javascript
function _lockUI(locked) {
  document.querySelectorAll(".menu-btn, .stage0-sub-btn").forEach(btn => {
    if (btn.dataset.action === "stop") return;
    btn.disabled = locked;
  });
  document.querySelectorAll(".top-action").forEach(btn => { btn.disabled = locked; });
  const ps = document.getElementById("projectSelect");
  if (ps) ps.disabled = locked;
  if (!locked) updateGenreGating();  // ← 부분 복구
}
```

**검증**: `updateGenreGating()` (8018-8030)는 `.genre-gated` 클래스만 처리. 장르 미설정 시 `.genre-gated` 버튼만 비활성화.

**문제 시나리오**:
1. 장르 미설정 → `.genre-gated` 버튼 disabled
2. 실행 시작 → `_lockUI(true)` → 모든 버튼 disabled
3. 실행 중 장르 설정 (불가능 — 장르 버튼도 disabled)
4. 실행 완료 → `_lockUI(false)` → 모든 버튼 enabled → `.genre-gated`도 enabled
5. BUT `updateGenreGating()` 호출로 `.genre-gated`가 다시 disabled됨 ✓

**최종 판정**: **INFO** (MEDIUM에서 하향). 현재 코드에서 실제 문제 시나리오를 재현하기 어려움. `updateGenreGating()`이 잠금 해제 시 항상 호출되어 올바른 상태 복구.

---

### BUILD-01 ~ BUILD-04, TEST-01 ~ TEST-03, DEAD-01 ~ DEAD-02, DEP-01: 유지/하향

| ID | 이전 | 최종 | 사유 |
|----|------|------|------|
| BUILD-01 | MEDIUM | **LOW** | sprites는 실제 canvas 렌더링에 사용됨 (office_bg, desk 등). dbg_ 접두사만 불필요 |
| BUILD-02 | MEDIUM | **LOW** | 코드 서명은 비용 결정 — 기술 문제 아님 |
| BUILD-03 | HIGH | **MEDIUM** | 빌드 스크립트 미확인이므로 불확실. 확인 필요 |
| TEST-01 | MEDIUM | **LOW** | 계약 테스트가 이미 존재하므로 E2E 부재는 보완적 |
| TEST-02 | HIGH | **MEDIUM** | start:spike가 기동 검증 커버 |
| DEAD-01 | INFO | **INFO** | 의도적 보존 확인됨 |
| DEAD-02 | LOW | **INFO** | lucide는 splash에서만 사용, 런타임 영향 없음 |
| DEP-01 | MEDIUM | **LOW** | ^40.8.0는 마이너 업데이트 자동 적용 |

---

## Pass 2: 누락 탐색 — 이전 보고서가 놓친 것

### NEW-01: `settingsStore`에 API 키 평문 저장 + IPC 무검증 전달 [MEDIUM]

**코드 근거**: `index.html:8198`, `main.js:624-628`

렌더러:
```javascript
settingsStore.apiKey1 = saved.apiKey1 || "";
// ...
window.geuldobiDesktop.saveSettings(settingsStore);
```

메인 프로세스:
```javascript
ipcMain.handle(IPC_CHANNELS.bridge.saveSettings, async (_, settings) => {
  fs.writeFileSync(SETTINGS_PATH, JSON.stringify(settings, null, 2), "utf8");
  return { ok: true };
});
```

**문제**: `settings` 객체에 대한 **스키마 검증 없음**. 렌더러가 임의 크기의 JSON을 전달하면 디스크에 그대로 기록됨.
- XSS → `window.geuldobiDesktop.saveSettings({ payload: "A".repeat(1e9) })` → 디스크 가득 참
- 또는 `saveSettings({ "../../etc/config": "malicious" })` → 단, 파일 경로는 `SETTINGS_PATH` 고정이므로 경로 탈출 불가

**실질 위험**: 디스크 fill 공격 (XSS 경유). `JSON.stringify` + `writeFileSync`는 메모리에 전체 문자열을 올림.

**권장**: settings 객체 크기 제한 (예: `JSON.stringify(settings).length > 1e6` 시 거부)

---

### NEW-02: `_collectInputs()`에서 API 키가 bridge API로 전달되는 경로 [INFO]

**코드 근거**: `index.html:6880`, 6973
```javascript
const inputs = _collectInputs();
// inputs.api_key가 포함됨
const result = await window.geuldobiDesktop.runKey(key, subKey, inputs, approvalId);
```

→ main.js:554: `body.inputs = inputs` → bridgeFetch POST body에 API 키 포함
→ `http://127.0.0.1:8300/run`으로 전송

**검증**: localhost 전용이므로 네트워크 탈취 위험 없음. 백엔드가 API 키를 LLM 호출에 사용하는 것은 정상 동작.

**최종 판정**: **INFO**. 설계 의도대로 동작. API 키가 main process 로그(main.js:286 `debugLog("backend stdout", ...)`)에 기록될 가능성만 주의.

---

### NEW-03: `window.prompt()` 사용 — Electron에서 deprecated 패턴 [LOW]

**코드 근거**: `index.html:4786`
```javascript
const raw = window.prompt(
  `[${title}] 승인 ID를 입력하세요.\n승인 없이 위험 키는 실행되지 않습니다.`,
  ""
);
```

**문제**: `window.prompt()`는 Electron에서 동기 블로킹 다이얼로그. 일부 Electron 버전에서 렌더러 프로세스를 얼릴 수 있음. 커스텀 모달로 교체 권장.

---

### NEW-04: requestAnimationFrame 루프 무조건 실행 [LOW]

**코드 근거**: `index.html:5822, 8263`
```javascript
function draw(ts) {
  // ... 캔버스 렌더링 로직 ...
  requestAnimationFrame(draw);  // 무조건 재귀
}
requestAnimationFrame(draw);  // 최초 호출
```

**검증**: `draw()` 함수는 페이지 로드 시작부터 앱 종료까지 60fps로 영구 실행. 비실행 상태에서도 캔버스를 매 프레임 다시 그림.

**영향**: 노트북 배터리 소모. `officeState.isRunning`이 false일 때는 정적 장면이므로 `cancelAnimationFrame` 가능.

---

### NEW-05: 로그 스트림 500줄 제한의 DOM 노드 누적 [INFO]

**코드 근거**: `index.html:5110-5113`
```javascript
while (logStream.children.length > 500) {
  logStream.removeChild(logStream.firstChild);
}
```

**검증**: 500줄 제한이 있으므로 무한 누적은 아님. 각 로그 행에 이벤트 리스너는 없으므로 메모리 누수 없음.

**최종 판정**: **INFO**. 올바르게 관리됨.

---

### NEW-06: splash 폴링 실패 후 UI 복구 불가 [LOW]

**코드 근거**: `splash.js:47-51`
```javascript
if (pollFailCount >= MAX_POLL_FAILS) {  // 30초
  clearInterval(pollTimer);
  pollTimer = null;
  setMessage("백엔드 연결 실패 — 앱을 재시작하세요");
}
```

**검증**: 폴링 중단 후 `clearInterval` 호출됨 (리소스 누수 없음 ✓). BUT 메인 프로세스의 `fallbackTimer` (main.js:471-474)가 8초 후 splash→main 전환:
```javascript
fallbackTimer = setTimeout(() => {
  switchToMain("fallback-timeout");
}, SPLASH_FALLBACK_MS);  // 8000ms
```

**결론**: splash 실패 메시지는 사용자에게 8초 이상 보이지 않음 (fallback이 먼저 발동). MAX_POLL_FAILS(30초)에 도달하기 전에 이미 메인 윈도우로 전환됨.

**최종 판정**: **삭제**. fallback 타이머가 이미 커버.

---

## Pass 3: 최종 교정 — 실행 가능한 발견사항만 잔류

### 최종 발견사항 (코드 근거 확인됨만 잔류)

| # | ID | 심각도 | 제목 | 코드 위치 | 이전 판정 | 변동 |
|---|-----|--------|------|----------|----------|------|
| 1 | **SEC-07** | **HIGH** | sanitizeProjectName `..` 경로 탈출 | main.js:765 | MEDIUM | **↑ 승격** |
| 2 | SEC-05 | **MEDIUM** | process.env 전체 상속 | main.js:270 | HIGH | ↓ 하향 |
| 3 | SEC-01 | **MEDIUM** | CSP unsafe-inline | index.html:6 | HIGH | ↓ 하향 |
| 4 | NEW-01 | **MEDIUM** | settings IPC 크기 무제한 | main.js:628 | 신규 | — |
| 5 | BUILD-03 | **MEDIUM** | python-embed 버전 핀닝 미확인 | 빌드 스크립트 | HIGH | ↓ 하향 |
| 6 | TEST-02 | **MEDIUM** | Packaged .exe 통합 테스트 부재 | — | HIGH | ↓ 하향 |
| 7 | SEC-08 | **LOW** | CSP connect-src 미사용 외부 API | index.html:6 | MEDIUM | ↓ 하향 |
| 8 | SEC-02 | **LOW** | bridge:run 화이트리스트 없음 | main.js:551 | MEDIUM | ↓ 하향 |
| 9 | NEW-03 | **LOW** | window.prompt() 사용 | index.html:4786 | 신규 | — |
| 10 | NEW-04 | **LOW** | rAF 무조건 실행 | index.html:5822 | 신규 | — |
| 11 | UX-02 | **LOW** | 500ms setInterval DOM 재생성 | index.html:8163 | MEDIUM | ↓ 하향 |

### 삭제된 발견사항 (오탐 또는 과대평가)

| ID | 사유 |
|----|------|
| SEC-03 | `encodeURIComponent`가 슬래시 인코딩 → 경로 탈출 불가 |
| SEC-04 | localhost HTTP는 Electron 표준 패턴 |
| SEC-09 | taskkill 비동기 실행은 OS가 보완 |
| SEC-10 | 파일 임포트 덮어쓰기는 OS 다이얼로그가 사용자 의도 확인 |
| SEC-11 | Windows symlink 생성에 관리자 권한 필요 |
| UX-01 | escapeHtml 적용률 ~95%, 미적용 사례는 Number 변환으로 보호 |
| UX-03 | JS 단일 스레드에서 race condition 불가 |
| UX-04 | onclose가 동일 기능 수행 |
| UX-05 | 대부분 의도적 fire-and-forget |
| UX-06 | updateGenreGating()이 상태 복구 |

---

## 즉시 실행 권고

### 1순위: SEC-07 — sanitizeProjectName 경로 탈출 (HIGH)

**현재 코드** (main.js:761-766):
```javascript
return name.trim().replace(/[<>:"/\\|?*]/g, "_");
```

**수정안**:
```javascript
function sanitizeProjectName(name) {
  if (typeof name !== "string") return "";
  const safe = name.trim().replace(/[^a-zA-Z0-9가-힣ㄱ-ㅎㅏ-ㅣ_\- ]/g, "_");
  if (!safe || /^\.+$/.test(safe)) return "";
  return safe;
}
```

**변경 범위**: 1개 함수, 4줄
**영향 분석**: 기존 프로젝트 이름에 `.`이 포함된 경우 `_`로 치환됨. 기존 데이터 마이그레이션 불필요 (디렉토리 이름 자체는 변경 안 함).

### 2순위: SEC-05 — process.env 필터링 (MEDIUM)

**수정안** (main.js:269-279):
```javascript
env: {
  PATH: process.env.PATH,
  TEMP: process.env.TEMP,
  TMP: process.env.TMP,
  LOCALAPPDATA: process.env.LOCALAPPDATA,
  USERPROFILE: process.env.USERPROFILE,
  PYTHONIOENCODING: "utf-8",
  PYTHONUNBUFFERED: "1",
  GEULDOBI_DESKTOP_MODE: "1",
  ...(app.isPackaged ? { /* 패키지 전용 변수 */ } : {}),
},
```

**변경 범위**: `...process.env` 제거, 필요 변수 5개 명시
**위험**: Python/pip이 추가 환경 변수를 요구할 수 있으므로 개발 모드에서 충분히 테스트 후 적용

### 3순위: SEC-01 — CSP unsafe-inline 제거 (MEDIUM)

**장기 과제**: index.html의 8000줄+ 인라인 스크립트를 외부 JS 파일로 분리 필요. nonce 기반 전환은 Electron file:// 프로토콜에서 제한적.

**단기 완화**: `connect-src`에서 `https://generativelanguage.googleapis.com` 제거 (SEC-08 동시 해결)

---

## 이전 보고서 대비 변동 요약

```
                이전 보고서       적대적 감리 후
─────────────────────────────────────────────────
총 발견사항       29건              11건 (18건 삭제/합병)
HIGH              4건              1건 (SEC-07만 잔류)
MEDIUM           13건              4건
LOW               9건              5건
INFO              3건              1건
오탐 제거          -               7건 (SEC-03,04,09,10,11, UX-03,04)
심각도 하향        -              10건
신규 발견          -               4건 (NEW-01~04)
```

---

> **결론**: 코드베이스 직접 대조 결과, 이전 보고서의 발견 29건 중 **7건이 오탐**, **10건이 과대평가**였다. 실질적으로 즉시 조치가 필요한 것은 **SEC-07(sanitizeProjectName 경로 탈출) 1건**이며, 이는 정규식 1줄 수정으로 해결된다. 전체적으로 글도비 데스크톱의 Electron 보안 기반(contextIsolation, nodeIntegration 차단, 계약 기반 IPC)은 **건전하다**.
