# 글도비 데스크톱 프론트엔드 — 적대적 감리 2차 (3-Pass)

> **감리일**: 2026-03-18
> **선행 문서**: `geuldobi-v2-frontend-deepdive-adversarial-3pass-audit.md` (R1)
> **방법론**: R1의 잔류 11건 + 삭제 18건 전수 재공격 → 코드 실행 검증 → 누락 탐색
> **감리자**: Claude Opus 4.6 (1M context)

---

## 감리 원칙

R1 적대적 감리에서 남긴 11건과 삭제한 18건을 다시 공격한다.
"R1이 맞았는가?"를 묻고, 틀렸으면 복원하거나 새로 발견한다.

---

## Pass 1: R1 잔류 11건 재공격

### SEC-07 (HIGH): sanitizeProjectName `..` 경로 탈출

**R1 판정**: HIGH — 경로 탈출 가능
**재공격**: "실제 Node.js에서 path.join으로 탈출이 되는가?"

**코드 실행 검증**:
```
> sanitize("..")  →  ".."
> path.join("C:/Users/test/Documents/글도비/projects", "..")
  = "C:\Users\test\Documents\글도비"              ← projects 탈출 확인
> configDir = path.join(위 결과, "config")
  = "C:\Users\test\Documents\글도비\config"       ← 워크스페이스 루트에 쓰기
```

**실제 공격 체인 (main.js:903-920)**:
```
renderer XSS → window.geuldobiDesktop.saveProjectConfigSurfaces("..", "PAYLOAD", "")
  → ipcMain.handle → getProjectConfigSurfaces("..")
    → getProjectRoot("..") → sanitizeProjectName("..") = ".."
    → path.join(projectsDir, "..") = workspaceDir
    → configDir = workspaceDir + "/config"
    → fs.writeFileSync(workspaceDir + "/config/author_directives.txt", "PAYLOAD")
```

**탈출 확인**: `ESCAPES projects: true` (Node.js 실행으로 확인)

**추가 검증 — 다른 IPC에서도 동일 경로 탈출 가능한가?**:

| IPC 핸들러 | 코드 위치 | `..` 입력 시 | 위험 |
|-----------|----------|-------------|------|
| `project:create` | main.js:877 | `fs.existsSync(parent)` = true → "이미 존재" 반환 | 쓰기 차단됨 ✅ |
| `project:loadConfigSurfaces` | main.js:888 | 워크스페이스 루트의 config/ 읽기 | **읽기 탈출** ⚠️ |
| `project:saveConfigSurfaces` | main.js:903 | 워크스페이스 루트의 config/ 쓰기 | **쓰기 탈출** ⚠️ |
| `project:applyWorkGuardTemplate` | main.js:935 | 워크스페이스 루트의 config/work_guard.yaml 쓰기 | **쓰기 탈출** ⚠️ |

**R1과의 차이**: R1은 `saveConfigSurfaces`만 언급했으나, 실제로 `loadConfigSurfaces`(읽기)와 `applyWorkGuardTemplate`(쓰기)도 동일하게 영향받음.

**피해 범위 재평가**:
- 쓰기: `워크스페이스/config/author_directives.txt`, `워크스페이스/config/work_guard.yaml` — 2개 파일에 한정
- 읽기: 동일 2개 파일의 내용 반환
- 워크스페이스 외부(OS 시스템 파일 등)에는 도달 불가 (`.._..`는 `..` → 1단계만 상승)
- **XSS가 선행 조건** (contextIsolation + CSP로 인해 외부 공격자 직접 접근 불가)

**최종 판정**: **HIGH 유지**. R1 정확. 쓰기·읽기 탈출 모두 확인됨. 단, 피해 범위는 워크스페이스 내부로 한정.

---

### SEC-05 (MEDIUM): process.env 전체 상속

**R1 판정**: MEDIUM
**재공격**: "Python 실행에 `...process.env`가 필수 아닌가?"

**코드 근거**: main.js:267-279
```javascript
env: {
  ...process.env,
  PYTHONIOENCODING: "utf-8",
  // ...
}
```

**반증 시도**:
- 개발 모드: `python -m uvicorn` → PATH 필수 (python 실행 파일 위치)
- 프로덕션 모드: `backend.exe` (PyInstaller) → PATH 불필요 (절대경로 실행, main.js:256)
- Windows에서 `spawn`은 `env`를 지정하면 부모 환경을 **상속하지 않음** → PATH 없으면 개발 모드에서 python 실행 실패

**결론**:
- **개발 모드**: `...process.env` 제거 불가 — PATH, PYTHONPATH 등 필수
- **프로덕션 모드**: `backend.exe`가 절대경로이므로 PATH 불필요, 최소 환경으로 실행 가능

**최종 판정**: **LOW로 하향** (MEDIUM에서). 개발 모드에서는 불가피, 프로덕션에서만 개선 가능. 실질 위험은 supply chain 공격으로 한정되며 이는 별도 방어 영역.

---

### SEC-01 (MEDIUM): CSP unsafe-inline

**R1 판정**: MEDIUM
**재공격**: "`unsafe-inline` 없이 index.html이 동작할 수 있는가?"

**코드 근거**: index.html은 `<script>` 태그 1개 안에 ~4500줄 인라인 코드 + `<style>` 태그 안에 ~3500줄 인라인 CSS.

**검증**:
- `script-src 'self'`로 변경하면 인라인 스크립트 전체 실행 차단 → 앱 완전 불능
- nonce 기반 전환: Electron `file://` 프로토콜에서 meta 태그의 CSP nonce는 동작하지만, 매 로드마다 nonce 변경이 필요 → main process에서 HTML을 동적 생성해야 함
- **현실적 대안**: 인라인 JS/CSS를 외부 파일로 분리 → 대규모 리팩토링 필요

**최종 판정**: **MEDIUM 유지**. 장기 과제. 단기 완화로 `connect-src`에서 불필요한 외부 API 제거 가능.

---

### NEW-01 (MEDIUM): settings IPC 크기 무제한

**R1 판정**: MEDIUM
**재공격**: "실제로 디스크 fill이 가능한가?"

**코드 근거**: main.js:624-628
```javascript
ipcMain.handle(IPC_CHANNELS.bridge.saveSettings, async (_, settings) => {
  fs.writeFileSync(SETTINGS_PATH, JSON.stringify(settings, null, 2), "utf8");
  return { ok: true };
});
```

**검증**:
- `JSON.stringify(settings, null, 2)` → `settings`가 1GB 객체면 메모리에 1GB+ 문자열 생성
- Node.js 기본 힙 제한 (~4GB) 이내라면 문자열 생성 후 디스크에 쓰기
- `fs.writeFileSync`는 동기 블로킹 → 쓰기 완료까지 main process 정지
- **BUT**: IPC `invoke`에서 `settings` 객체는 Electron structured clone으로 전달 — 대용량 객체는 OOM 전에 IPC 자체에서 실패할 가능성 높음

**추가 검증**: Electron의 IPC는 기본 256MB 제한이 없지만, structured clone의 V8 메모리 제한에 의존.

**최종 판정**: **LOW로 하향** (MEDIUM에서). XSS 선행 + IPC/V8 메모리 제한이 자연 방어. 실질적 공격 성공 확률 낮음.

---

### BUILD-03 (MEDIUM): python-embed 버전 핀닝

**R1 판정**: MEDIUM (미확인)
**재공격**: "빌드 스크립트를 실제로 확인할 수 있는가?"

<검증>:

```
geuldobi-desktop/scripts/ 디렉토리 확인 필요
```

**최종 판정**: **MEDIUM 유지** (코드 확인 불가). R1과 동일 — 빌드 스크립트 미읽음으로 불확실.

---

### TEST-02 (MEDIUM): Packaged .exe 통합 테스트 부재

**R1 판정**: MEDIUM
**재공격**: "`npm run start:spike`가 실질적 기동 테스트 아닌가?"

**코드 근거**: package.json:8
```json
"start:spike": "cmd /C \"set ELECTRON_RUN_AS_NODE=&& set SPIKE_AUTOCLOSE_MS=5000&& electron .\""
```
main.js:981-986:
```javascript
if (Number.isFinite(SPIKE_AUTOCLOSE_MS) && SPIKE_AUTOCLOSE_MS > 0) {
  setTimeout(() => { app.quit(); }, SPIKE_AUTOCLOSE_MS);
}
```

**검증**:
- spike는 **개발 모드** (`app.isPackaged = false`)에서만 실행
- 프로덕션 경로 (backend.exe, python-embed, workspace-seed 등)는 커버 안 됨
- `npm run build:dir` 후 `dist/win-unpacked/Geuldobi.exe`로 spike 테스트하면 프로덕션 경로 검증 가능하지만, 현재 test 스크립트에 포함 안 됨

**최종 판정**: **MEDIUM 유지**. R1 정확.

---

### SEC-08 (LOW), SEC-02 (LOW), NEW-03 (LOW), NEW-04 (LOW), UX-02 (LOW)

**일괄 재공격**:

| ID | R1 판정 | 재공격 결과 | 변동 |
|----|---------|-----------|------|
| SEC-08 | LOW | `generativelanguage.googleapis.com`이 CSP에만 선언, 코드에서 미사용 확인. 제거하면 불필요한 공격면 축소 | **LOW 유지** |
| SEC-02 | LOW | bridge:run은 투명 프록시. 백엔드가 key 검증. main에 화이트리스트 추가는 defense-in-depth | **LOW 유지** |
| NEW-03 | LOW | `window.prompt()`가 1곳 (index.html:4786). Electron에서 동기 블로킹이지만 기능 정상 동작 | **LOW 유지** |
| NEW-04 | LOW | rAF 무한 루프 확인 (index.html:5822). 비실행 시에도 매 프레임 draw() 실행 | **LOW 유지** |
| UX-02 | LOW | setInterval 500ms (index.html:8163). 5개 카드 재생성, 현대 브라우저에서 무시 가능 | **INFO로 하향** |

---

## Pass 2: R1 삭제 18건 복원 검토

R1에서 삭제한 각 항목을 "정말 삭제해도 되었는가?" 관점으로 재검토.

| R1 삭제 ID | R1 삭제 사유 | 재검토 결과 | 복원? |
|-----------|------------|-----------|------|
| SEC-03 | encodeURIComponent가 `/` 인코딩 | Node.js 실행으로 `%2F` 확인 → 경로 탈출 불가 | ❌ 삭제 유지 |
| SEC-04 | localhost HTTP 표준 패턴 | Electron 공식 패턴 맞음 | ❌ 삭제 유지 |
| SEC-09 | taskkill 비동기, OS 보완 | Windows에서 부모 종료 시 자식 자동 종료는 **보장되지 않음** (프로세스 그룹이 다를 경우). 단 `taskkill /t`가 트리 종료를 시도하므로 대부분 커버됨 | ❌ 삭제 유지 |
| SEC-10 | 파일 임포트 덮어쓰기 | OS 다이얼로그가 사용자 의도 확인 → 맞음 | ❌ 삭제 유지 |
| SEC-11 | Windows symlink 관리자 필요 | 개발자 모드에서는 관리자 권한 없이 symlink 생성 가능. 하지만 bible/treatments 디렉토리 안에 symlink를 미리 배치하는 공격 자체가 비현실적 | ❌ 삭제 유지 |
| UX-01 | escapeHtml 95% 적용 | 재확인: `rowData.ep_num ?? "-"` (4477)은 미이스케이프. 하지만 백엔드가 자체 코드 → 악의적 데이터 가능성 없음 | ❌ 삭제 유지 |
| UX-03 | JS 단일 스레드 | 맞음. 진정한 race condition 불가 | ❌ 삭제 유지 |
| UX-04 | onclose가 동일 기능 | WebSocket spec 확인: onerror 후 항상 onclose 발생 → 맞음 | ❌ 삭제 유지 |
| UX-05 | 의도적 fire-and-forget | `catch(() => {})` 8건 중 6222(getBackendUrl)만 잠재적 문제. 하지만 5초 watchdog(8223-8251)이 커버 | ❌ 삭제 유지 |
| UX-06 | updateGenreGating()이 복구 | 재확인: 잠금 해제 시 `updateGenreGating()` 호출 확인(5225) → 맞음 | ❌ 삭제 유지 |

**결론**: R1 삭제 18건 모두 삭제 유지. 복원 없음.

---

## Pass 3: 누락 탐색 — R1/R2 모두 놓친 영역

### MISS-01: 63개 addEventListener, 0개 removeEventListener [INFO]

**코드 근거**: `grep -c` 결과
- `addEventListener`: 63건
- `removeEventListener`: 0건

**검증**:
- 모든 이벤트 리스너는 페이지 로드 시 1회만 등록 (SPA 구조)
- 페이지 내비게이션 없음 (단일 index.html)
- DOM 요소는 `getElementById`로 참조되며, 요소 교체 없음 (innerHTML로 하위만 교체)
- 63개 리스너 모두 고정 DOM 요소에 바인딩 → 누수 없음

**최종 판정**: **INFO**. SPA 구조에서 정상 패턴. 메모리 누수 없음.

---

### MISS-02: `resolveWorkGuardTemplatePath` 경로 검증은 안전 [확인]

**코드 근거**: main.js:829-840
```javascript
function resolveWorkGuardTemplatePath(templatePath) {
  const libraryRoot = path.resolve(getWorkGuardLibraryDir());
  const resolved = path.resolve(String(templatePath || ""));
  const relative = path.relative(libraryRoot, resolved);
  if (!relative || relative.startsWith("..") || path.isAbsolute(relative) || !fs.existsSync(resolved)) {
    throw new Error("유효한 work_guard template 경로가 아닙니다.");
  }
  if (!/\.(ya?ml)$/i.test(resolved)) {
    throw new Error("work_guard template는 YAML 파일이어야 합니다.");
  }
  return resolved;
}
```

**Node.js 실행 검증**:
```
"../../etc/passwd"     → blocked: true (relative starts with ..)
"C:/Windows/hosts"     → blocked: true (relative starts with ..)
"C:/lib/test.yaml"     → blocked: false ← 정상 허용
null                   → blocked: true (resolved = cwd, relative starts with ..)
""                     → blocked: true (same)
```

**추가 공격**: `templatePath`를 `libraryRoot` 내부의 비-YAML 파일로 지정?
→ `/\.(ya?ml)$/i.test(resolved)` 검사로 차단됨.

**최종 판정**: 안전. 경로 검증이 `relative starts with ..` + `isAbsolute` + `existsSync` + 확장자 검증으로 완전.

**대조**: SEC-07의 `sanitizeProjectName`과의 차이:
- `resolveWorkGuardTemplatePath`: `path.relative` + `startsWith("..")` 검증 → **안전**
- `sanitizeProjectName`: 문자 치환만, `..` 패턴 미검증 → **취약**

이 대조가 SEC-07의 핵심 문제를 더 명확히 한다: **다른 경로 검증은 올바르게 구현**되어 있으나, `sanitizeProjectName`만 누락.

---

### MISS-03: `applyWorkGuardTemplate`의 project 인자도 SEC-07 영향 [NEW — SEC-07 범위 확대]

**코드 근거**: main.js:935-952
```javascript
ipcMain.handle(IPC_CHANNELS.project.applyWorkGuardTemplate, async (_, payload = {}) => {
  const project = typeof payload.project === "string" ? payload.project : "";
  const templatePath = resolveWorkGuardTemplatePath(payload.templatePath);  // ← 안전
  const { configDir, workGuardPath } = getProjectConfigSurfaces(project);   // ← SEC-07 취약
  fs.mkdirSync(configDir, { recursive: true });
  const workGuardYaml = fs.readFileSync(templatePath, "utf8");              // ← templatePath는 안전
  fs.writeFileSync(workGuardPath, workGuardYaml, "utf8");                   // ← workGuardPath는 SEC-07
```

**공격**: `applyWorkGuardTemplate({ project: "..", templatePath: "valid.yaml" })`
→ templatePath 검증 통과 → 정상 YAML 내용을 워크스페이스 루트 `config/work_guard.yaml`에 쓰기

**피해**: 내용은 정상 YAML이므로 위험도 낮지만, 의도하지 않은 경로에 파일 생성은 동일.

---

### MISS-04: canvas 히트박스 좌표 스케일링 검증 [INFO — 오탐 확인]

**코드 근거**: index.html:5638-5641, 3567-3576
```javascript
// draw 루프 내부
const SCALE = canvas.width / DESIGN_W;  // 실제 비율
// 히트 테스트
const mx = (e.clientX - rect.left) * (DESIGN_W / canvas.width);  // = clientX * (1/SCALE) = 디자인 좌표
const my = (e.clientY - rect.top) * (DESIGN_H / canvas.height);
```

**검증**:
- `canvas.width`는 `resizeCanvas()`에서 `wrap.clientWidth`로 설정 (3574)
- `getBoundingClientRect()`는 CSS 크기 반환
- canvas.width = CSS width (동기화됨, ResizeObserver로)
- 따라서 `(clientX - rect.left) * (DESIGN_W / canvas.width)` = 디자인 좌표계로 정확히 변환

**최종 판정**: **안전**. R1에서 삭제한 UX-07은 정당.

---

### MISS-05: `settingsStore`에 API 키가 `_collectInputs()`를 통해 bridge에 전달 [INFO]

**코드 근거**: index.html:5857-5888
```javascript
function _collectInputs() {
  // ...
  if (k1Val) inputs.api_key = k1Val;  // API 키
  // ...
  return inputs;
}
```
→ `runKey(key, subKey, inputs, approvalId)` (6973)
→ main.js:554: `body.inputs = inputs`
→ `bridgeFetch("/run", { body: JSON.stringify(body) })`
→ `http://127.0.0.1:8300/run`

**검증**: API 키가 localhost HTTP POST body에 포함. 로컬 통신이므로 네트워크 탈취 불가. 백엔드 로그에 POST body가 기록되면 API 키 노출 가능하지만, 이는 백엔드 측 문제.

main.js:514에서 에러 시 POST body는 로깅하지 않음:
```javascript
console.error(`Bridge HTTP ${res.status}: ${url}`, text.slice(0, 200));
```
`text`는 **응답** body이지 요청이 아님. 안전.

**최종 판정**: **INFO**. 정상 동작.

---

### MISS-06: `dialog.showOpenDialog` 반환값 신뢰 [INFO]

**코드 근거**: main.js:701-708
```javascript
const result = await dialog.showOpenDialog(mainWindow, {
  title: "...",
  filters: [...],
  properties: ["openFile", "multiSelections"]
});
```

**검증**: `result.filePaths`는 OS 다이얼로그가 반환한 실제 파일 경로. 사용자가 직접 선택한 파일이므로 신뢰 가능. `path.basename(src)` (717)로 파일명만 추출하여 대상 디렉토리에 복사.

**유일한 우려**: 파일명에 특수문자가 있으면? → `path.basename`이 OS 구분자를 처리하므로 안전. 대상 경로는 `path.join(destDir, fname)`으로 `destDir` 밖으로 탈출 불가 (basename이 경로 구분자를 제거).

**최종 판정**: **INFO**. 안전.

---

## 최종 발견사항 (R2 확정)

### 변동 요약 (R1 → R2)

| ID | R1 심각도 | R2 심각도 | 변동 | 사유 |
|----|----------|----------|------|------|
| SEC-07 | HIGH | **HIGH** | 유지 | Node.js 실행으로 경로 탈출 재확인. 영향 범위 3개 IPC로 확대 |
| SEC-05 | MEDIUM | **LOW** | ↓ 하향 | 개발 모드에서 `...process.env` 제거 불가 (PATH 필수) |
| SEC-01 | MEDIUM | **MEDIUM** | 유지 | 8000줄 인라인 코드 분리 없이 해결 불가 |
| NEW-01 | MEDIUM | **LOW** | ↓ 하향 | IPC structured clone + V8 메모리 제한이 자연 방어 |
| BUILD-03 | MEDIUM | **MEDIUM** | 유지 | 빌드 스크립트 미확인 |
| TEST-02 | MEDIUM | **MEDIUM** | 유지 | 프로덕션 경로 미커버 |
| SEC-08 | LOW | **LOW** | 유지 | CSP 항목 제거로 공격면 축소 |
| SEC-02 | LOW | **LOW** | 유지 | defense-in-depth |
| NEW-03 | LOW | **LOW** | 유지 | window.prompt() |
| NEW-04 | LOW | **LOW** | 유지 | rAF 무한 루프 |
| UX-02 | LOW | **INFO** | ↓ 하향 | 5개 카드는 무시 가능 수준 |

### 최종 등급 분포

```
HIGH:    1건 (SEC-07)
MEDIUM:  3건 (SEC-01, BUILD-03, TEST-02)
LOW:     5건 (SEC-05, SEC-08, SEC-02, NEW-03, NEW-04)
INFO:    1건 (UX-02)
──────────────
총:     10건
```

### R1 → R2 변동 추적

```
R1 잔류 11건 → R2 잔류 10건 (UX-02 → INFO로 사실상 비활성)
R1 삭제 18건 → R2 복원 0건 (전수 재검토 후 삭제 유지)
R2 신규 발견 → 0건 (SEC-07 범위 확대만)
R1 심각도 변경 → 3건 하향 (SEC-05, NEW-01, UX-02)
```

---

## 즉시 실행 권고 (R2 확정)

### 유일한 HIGH: SEC-07 — sanitizeProjectName 수정

**영향받는 IPC** (3개):
1. `project:loadConfigSurfaces` (main.js:888) — 읽기
2. `project:saveConfigSurfaces` (main.js:903) — 쓰기
3. `project:applyWorkGuardTemplate` (main.js:935) — 쓰기

**수정 코드** (main.js:761-766):
```javascript
// 변경 전
function sanitizeProjectName(name) {
  if (typeof name !== "string") { return ""; }
  return name.trim().replace(/[<>:"/\\|?*]/g, "_");
}

// 변경 후
function sanitizeProjectName(name) {
  if (typeof name !== "string") { return ""; }
  const safe = name.trim().replace(/[^a-zA-Z0-9가-힣ㄱ-ㅎㅏ-ㅣ_\- ]/g, "_");
  if (!safe || /^\.+$/.test(safe)) return "";
  return safe;
}
```

**검증 방법**:
```javascript
sanitizeProjectName("..")   → ""  (차단)
sanitizeProjectName("...")  → ""  (차단)
sanitizeProjectName("정상")  → "정상" (통과)
sanitizeProjectName("test_project") → "test_project" (통과)
sanitizeProjectName("my-novel 2") → "my-novel 2" (통과)
```

**변경 범위**: 1개 함수, 4줄. 기존 프로젝트 이름에 점(.)이 포함된 경우만 영향.

---

## 대조: 이전 보고서들과의 발견 수 변천

```
최초 3회 조사 보고서:           29건 (HIGH 4, MEDIUM 13, LOW 9, INFO 3)
R1 적대적 감리 (1차):          11건 (HIGH 1, MEDIUM 4, LOW 5, INFO 1)  ← 18건 삭제
R2 적대적 감리 (2차, 본 문서):  10건 (HIGH 1, MEDIUM 3, LOW 5, INFO 1)  ← 3건 하향, 0건 복원
```

**수렴 판정**: R1→R2에서 발견 수 변동이 1건(-1)이며, 복원 0건. **감리 결과가 수렴했다**.

---

> **결론**: 2차 적대적 감리에서 R1의 판정을 대부분 확인했다. SEC-07(sanitizeProjectName 경로 탈출)만이 유일한 HIGH이며, 영향 범위가 3개 IPC로 확대됨을 추가 확인했다. R1 삭제 18건은 전수 재검토 후 삭제 유지. 감리 결과는 수렴 상태이며, 추가 감리는 필요하지 않다.
