# Track F — 오류 복원력

> 확신도: 96%
> 범위: IPC/HTTP/WS 전구간 오류 처리, 복구 메커니즘, 봉쇄 범위

---

## 1. 3중 오류 봉쇄 구조

```
Layer 1: IPC Envelope (Main Process)
    → bridgeFetch 실패 → { ok: false, code: "NETWORK_ERROR", data: { envelope_version: "desktop_bridge_v1" } }

Layer 2: HTTP Envelope (FastAPI)
    → 검증 실패 → { ok: false, code: "INVALID_KEY", message: "..." }
    → 서버 오류 → HTTP 500

Layer 3: WS Reconnect (Renderer)
    → 연결 끊김 → 3초 후 자동 재연결
```

---

## 2. Layer 1 — IPC 전송 오류 봉쇄

### bridgeFetch 에러 핸들러 (main.js:494-549)

```javascript
async function bridgeFetch(urlPath, options = {}) {
  const url = `${STATUS_BASE_URL}${urlPath}`;
  const timeoutController = new AbortController();
  const timeoutId = setTimeout(() => timeoutController.abort(), BRIDGE_FETCH_TIMEOUT_MS);

  try {
    const res = await fetch(url, { ...options, signal: timeoutController.signal });

    if (!res.ok) {
      // HTTP 에러 (4xx, 5xx)
      let backendPayload = null;
      const text = await res.text().catch(() => "");
      try { backendPayload = JSON.parse(text); } catch {}

      return {
        ok: false,
        code: `HTTP_${res.status}`,
        message: `서버 오류 (${res.status})`,
        data: {
          envelope_version: "desktop_bridge_v1",
          namespace: "desktop_transport",
          transport_status: res.status,
          url_path: urlPath,
          backend_code: backendPayload?.code || null,
          backend_message: backendPayload?.message || null
        }
      };
    }
    return await res.json();
  } catch (err) {
    const isTimeout = err?.name === "AbortError";
    return {
      ok: false,
      code: "NETWORK_ERROR",
      message: isTimeout ? "bridge timeout (5000ms)" : err.message,
      data: {
        envelope_version: "desktop_bridge_v1",
        namespace: "desktop_transport",
        transport_status: null,
        url_path: urlPath,
        backend_code: null,
        backend_message: null
      }
    };
  } finally {
    clearTimeout(timeoutId);
  }
}
```

### 에러 코드 체계

| 코드 | 발생 조건 | 사용자 메시지 |
|------|----------|-------------|
| `HTTP_400` | 요청 검증 실패 | "서버 오류 (400)" |
| `HTTP_403` | 리스크 승인 실패 | "서버 오류 (403)" |
| `HTTP_409` | 이미 실행 중 | "서버 오류 (409)" |
| `HTTP_500` | 서버 내부 오류 | "서버 오류 (500)" |
| `NETWORK_ERROR` | 연결 불가/타임아웃 | err.message 또는 "bridge timeout (5000ms)" |

### 핵심 설계 원칙

- **모든 bridgeFetch 호출은 예외를 던지지 않음** — 항상 `{ ok, code, message, data }` 반환
- Renderer는 `result.ok` 단일 체크로 성공/실패 분기 가능
- `data.backend_code`로 BE 측 구체적 에러 코드 접근 가능

---

## 3. Layer 2 — HTTP 응답 에러 봉쇄

### FastAPI 에러 엔벨로프 (bridge_server.py:169-176)

```python
def _err(code: str, message: str, run_id: str | None = None) -> dict:
    return {
        "ok": False,
        "run_id": run_id,
        "code": code,
        "message": message,
        "data": None
    }
```

### 엔드포인트별 에러 코드

| 엔드포인트 | 코드 | HTTP 상태 | 조건 |
|-----------|------|----------|------|
| POST /run | `INVALID_KEY` | 400 | 허용되지 않는 키 |
| POST /run | `SUB_KEY_REQUIRED` | 400 | key=0인데 sub_key 없음 |
| POST /run | `SUB_KEY_NOT_ALLOWED` | 400 | key≠0인데 sub_key 있음 |
| POST /run | `INVALID_SUB_KEY` | 400 | sub_key 범위 초과 |
| POST /run | `RUN_ALREADY_ACTIVE` | 409 | 이미 실행 중 |
| POST /run | `RISK_APPROVAL_REQUIRED` | 403 | 승인 없이 리스크 키 |
| POST /run | `RISK_APPROVAL_EXPIRED` | 403 | 승인 만료 |
| POST /run/{id}/input | `INVALID_PROMPT_ID` | 400 | 프롬프트 ID 불일치 |
| POST /run/{id}/input | `PROMPT_ALREADY_RESOLVED` | 409 | 이미 응답됨 |
| POST /quality/review | `INVALID_LABEL` | 400 | 화이트리스트 외 레이블 |
| POST /quality/review | `MISSING_PROJECT` | 400 | 프로젝트명 누락 |

---

## 4. Layer 3 — WebSocket 복원력

### 자동 재연결 (index.html:6168-6223)

```javascript
function _connectWebSocket() {
  window.geuldobiDesktop.getBackendUrl().then(({ wsUrl }) => {
    _ws = new WebSocket(wsUrl);

    _ws.onopen = () => {
      _backendConnected = true;
      // 연결 성공 → 상태 동기화
    };

    _ws.onclose = () => {
      _backendConnected = false;
      // 3초 후 자동 재연결 (무제한 재시도)
      _wsReconnectTimer = setTimeout(_connectWebSocket, 3000);
    };

    _ws.onerror = () => {};  // 무시 (onclose에서 처리)
  }).catch(() => {});
}
```

### WS 메시지 파싱 오류 처리

```javascript
_ws.onmessage = (event) => {
  try {
    _handleWsEvent(JSON.parse(event.data));
  } catch (e) {
    console.error("WS parse error:", e);
    // 파싱 실패 → 무시 (연결 유지)
  }
};
```

### 재연결 특성

| 항목 | 값 |
|------|-----|
| 재연결 딜레이 | 3초 고정 |
| 최대 재시도 | 무제한 |
| 백오프 | 없음 (고정 간격) |
| 상태 동기화 | onopen에서 품질 요약 새로고침 |

---

## 5. 백엔드 프로세스 복원력

### 자동 재시작 (main.js:300-320)

```javascript
backendProcess.on("exit", (code, signal) => {
  if (code !== 0 && !app.isQuitting && backendRestartCount < 2) {
    backendRestartCount++;
    setTimeout(() => startBackend(), 2000);
  }
});
```

| 항목 | 값 |
|------|-----|
| 최대 재시작 | 2회 |
| 재시작 딜레이 | 2초 |
| 정상 종료 (code=0) | 재시작 안 함 |
| 앱 종료 중 | 재시작 안 함 |

### 시작 대기 (main.js:332-355)

```javascript
function pollBackendReady() {
  // GET /status를 300ms 간격으로 폴링
  // 최대 60초 대기
  // 성공 시 splash:backend-ready 이벤트 발생
}
```

---

## 6. 파일시스템 오류 처리

### Settings 손상 복구 (main.js:636-653)

```javascript
ipcMain.handle("bridge:load-settings", async () => {
  try {
    const raw = fs.readFileSync(settingsPath, "utf-8");
    return { ok: true, settings: JSON.parse(raw) };
  } catch (e) {
    if (e.code === "ENOENT") {
      return { ok: true, settings: null };  // 파일 없음 → 기본값
    }
    // JSON 파싱 실패 → 백업 후 null 반환
    try {
      fs.renameSync(settingsPath, settingsPath + ".bak");
    } catch {}
    return { ok: true, settings: null };
  }
});
```

### Material 파일 오류 (main.js:672-750)

```javascript
// list-files: 디렉토리 없으면 빈 배열
if (!fs.existsSync(dir)) return { ok: true, files: [] };

// import-file: 복사 실패 시 에러 반환
try {
  fs.copyFileSync(src, dest);
} catch (e) {
  return { ok: false, message: e.message };
}

// delete-file: 경로 탈출 방지 후 삭제
if (fileName.includes("..")) return { ok: false, message: "invalid filename" };
```

### 프로젝트 설정 오류 (main.js:888-920)

```javascript
// load-config-surfaces: 파일 없으면 빈 문자열
let authorDirectives = "";
try {
  authorDirectives = fs.readFileSync(path, "utf-8");
} catch {}

// save-config-surfaces: 디렉토리 자동 생성
fs.mkdirSync(configDir, { recursive: true });
```

---

## 7. 오류 전파 경로 요약

```
서브프로세스 crash (returncode ≠ 0)
    → ProcessRunner._on_exit(code)
        → WS broadcast: { type: "run_failed", payload: { returncode } }
            → Renderer: appendLog("[System] 실행 실패")

FastAPI 내부 오류
    → JSONResponse(500, _err("INTERNAL_ERROR", ...))
        → bridgeFetch: { ok: false, code: "HTTP_500", data: { backend_code: "INTERNAL_ERROR" } }
            → Renderer: 에러 표시

백엔드 프로세스 죽음
    → main.js: backendProcess.on("exit")
        → 2초 후 재시작 (최대 2회)
        → WS 끊김 → Renderer: 3초 후 재연결 시도

네트워크 타임아웃
    → bridgeFetch: AbortController timeout (5000ms)
        → { ok: false, code: "NETWORK_ERROR", message: "bridge timeout" }
            → Renderer: 타임아웃 표시
```

---

## 8. 복원력 매트릭스

| 장애 시나리오 | 감지 | 복구 | 사용자 영향 |
|-------------|------|------|-----------|
| 백엔드 응답 지연 | 5초 타임아웃 | 없음 (1회 시도) | 에러 메시지 표시 |
| 백엔드 crash | exit 이벤트 | 자동 재시작 (2회) | 일시적 단절 |
| WS 연결 끊김 | onclose 이벤트 | 3초 후 재연결 | 실시간 업데이트 일시 중단 |
| Settings 파일 손상 | JSON.parse 실패 | .bak 백업 + null 반환 | 설정 초기화 |
| 프로젝트 디렉토리 없음 | ENOENT | 자동 생성 | 없음 |
| Material 디렉토리 없음 | existsSync | 빈 목록 반환 | 없음 |
| 리스크 키 미승인 | 403 응답 | 없음 (설계 의도) | 승인 필요 안내 |

---

## 9. 3-Pass 감리

| Pass | 검증 항목 | 결과 |
|------|----------|------|
| 1차 | 3중 봉쇄 구조 식별, 각 레이어 역할 분리 확인 | ✅ |
| 2차 | 에러 코드 11개 전수 확인, bridgeFetch 예외 불발생 보장 확인 | ✅ |
| 3차 | 복원력 매트릭스 7개 시나리오 코드 증거 교차 확인 | ✅ |
