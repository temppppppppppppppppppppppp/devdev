# Track E — 데이터 흐름 생애주기

> 확신도: 96%
> 범위: 사용자 입력 → 실행 → 결과 반환까지의 전체 데이터 흐름

---

## 1. 5단계 파이프라인 개요

```
Stage 1: 사용자 입력 수집 (Renderer UI)
    ↓
Stage 2: IPC 전달 + 변환 (Main Process)
    ↓
Stage 3: HTTP 요청 + 검증 (FastAPI)
    ↓
Stage 4: 서브프로세스 실행 (ProcessRunner → main_a.py)
    ↓
Stage 5: 실시간 결과 스트림 (WS → Renderer)
```

---

## 2. Stage 1 — 사용자 입력 수집

### 진입점: Renderer UI (index.html)

```
사용자 선택:
├── 장르 (genre_index: 1-10)
├── 프로젝트 (project_index: 1-N 또는 project_name)
├── 실행 키 (key: 0-7, 44, 77, 88, 99)
├── 서브 키 (sub_key: key=0일 때 1-7)
└── 승인 ID (approval_id: 리스크 키일 때)
```

### Renderer → Preload 호출

```javascript
// index.html 내부
const result = await window.geuldobiDesktop.runKey(key, subKey, inputs, approvalId);
```

`inputs` 객체 구조:
```json
{
  "genre_index": "3",
  "project_index": "1",
  "project_name": "test_project",
  "genre_type": "investment",
  "stage0_style_cache_mode": "use"
}
```

---

## 3. Stage 2 — IPC 전달 + 변환

### Preload → Main Process (ipcRenderer.invoke)

```javascript
// preload.js:42-47
runKey: (key, subKey, inputs, approvalId) =>
  ipcRenderer.invoke("bridge:run", { key, subKey, inputs, approvalId })
```

### Main Process 변환 (main.js:551-559)

```javascript
ipcMain.handle("bridge:run", async (_, { key, subKey, inputs, approvalId }) => {
  const body = { key };
  if (subKey) body.sub_key = subKey;           // camelCase → snake_case
  if (inputs) body.inputs = inputs;
  if (approvalId) body.approval_id = approvalId;  // camelCase → snake_case
  return bridgeFetch("/run", { method: "POST", body: JSON.stringify(body) });
});
```

변환 후 HTTP body:
```json
{
  "key": "3",
  "sub_key": null,
  "inputs": { "genre_index": "3", "project_index": "1" },
  "approval_id": null
}
```

---

## 4. Stage 3 — HTTP 요청 + 검증

### FastAPI 수신 (bridge_server.py:1782-1891)

```python
@app.post("/run")
async def run_endpoint(request: Request):
    body = await request.json()
    key = str(body.get("key", ""))
    sub_key = body.get("sub_key")
    approval_id = body.get("approval_id")
    inputs = body.get("inputs") or {}
```

### T4 검증 체인 (run_validator.py)

```
1. key ∈ PUBLIC_RUN_KEYS?               → NO: 400 INVALID_KEY
2. key = "0" and no sub_key?            → 400 SUB_KEY_REQUIRED
3. key ≠ "0" and sub_key present?       → 400 SUB_KEY_NOT_ALLOWED
4. sub_key ∈ ALLOWED_STAGE0_SUB_KEYS?   → NO: 400 INVALID_SUB_KEY
5. runner.state ∈ {starting, running, stopping}? → 409 RUN_ALREADY_ACTIVE
```

### T6 리스크 게이트 (risk_approval.py)

```
key ∈ RISK_KEYS (44, 77, 88, 99)?
├─ YES:
│   approval_id 존재?               → NO: 403 RISK_APPROVAL_REQUIRED
│   approval 만료?                  → YES: 403 RISK_APPROVAL_EXPIRED
│   primary == secondary approver?  → YES: 403 DUAL_CONTROL_REQUIRED
│   → 감사 로그 기록 (risk-approval-log.jsonl)
└─ NO: 건너뜀
```

### 실행 ID 생성

```python
run_id = str(uuid.uuid4())
```

---

## 5. Stage 4 — 서브프로세스 실행

### ProcessRunner.start() (process_runner.py)

```python
def start(self, key, run_id, inputs, on_line, on_exit, on_prompt):
    # 1. 장르/프로젝트 해석
    genre_type = _GENRE_INDEX_TO_TYPE.get(inputs.get("genre_index", "3"))
    project_name = _resolve_requested_project_name(inputs)

    # 2. 서브프로세스 fork
    cmd = [sys.executable, "main_a.py"]  # 또는 GEULDOBI_ENGINE_EXE
    proc = subprocess.Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)

    # 3. stdin 시퀀스 주입
    proc.stdin.write(genre_index + "\n")      # 장르 선택
    proc.stdin.write("\n")                     # 확인
    proc.stdin.write(project_index + "\n")     # 프로젝트 선택
    proc.stdin.write(key + "\n")               # 메뉴 키

    # 4. stdout 스트림 콜백
    for line in proc.stdout:
        on_line(line)  # → WS broadcast
```

### Mode B 프롬프트 감지 (prompt_classifier.py)

```
stdout 줄 분석:
├── "(Y/N):" 패턴 → input_type: "bool", step: "confirm"
├── "[Enter]" 패턴 → input_type: "enter", step: "continue"
├── "선택:" 패턴   → input_type: "enum", step: "choice"
├── "1~10" 패턴    → input_type: "int", step: "range_input"
└── ":" 패턴       → input_type: "string", step: "generic_input"

감지 시:
1. PromptBroker에 PromptState 등록
2. WS로 prompt_request 이벤트 전송
3. /run/{run_id}/input 응답 대기
4. 응답 수신 → stdin에 쓰기
5. WS로 prompt_resolved 이벤트 전송
```

---

## 6. Stage 5 — 실시간 결과 스트림

### WS 이벤트 흐름

```
FastAPI WSManager
    │
    │  broadcast(event)
    │
    ▼
WebSocket (ws://127.0.0.1:8300/events)
    │
    │  JSON 이벤트
    │
    ▼
Renderer (_handleWsEvent)
```

### 이벤트 시퀀스 (정상 실행)

```
1. run_started     { key: "3" }                         # 실행 시작
2. stdout          { text: "장르: 투자" }                 # 출력 줄
3. stdout          { text: "프로젝트: test_project" }     # 출력 줄
   ...
N-1. stdout        { text: "완료" }                       # 마지막 출력
N.   run_completed { returncode: 0 }                     # 실행 완료
```

### 이벤트 시퀀스 (프롬프트 포함)

```
1. run_started      { key: "4" }
2. stdout           { text: "..." }
3. prompt_request   { prompt_id, step_id, input_type, options, timeout_sec }
   ← 사용자 응답 대기 (Renderer UI에 프롬프트 표시)
   → POST /run/{id}/input { prompt_id, value }
4. prompt_resolved  { prompt_id, value }
5. stdout           { text: "..." }
   ...
N. run_completed    { returncode: 0 }
```

### 이벤트 시퀀스 (실패)

```
1. run_started    { key: "3" }
2. stdout         { text: "..." }
   ...
N. run_failed     { returncode: 1 }
```

### Renderer 이벤트 처리 (index.html:6225-6264)

```javascript
function _handleWsEvent(ev) {
  switch (ev.type) {
    case "run_started":
      appendLog(`[System] 실행 시작 (key: ${ev.payload.key})`);
      break;
    case "stdout":
      _handleStdoutLine(ev.payload.text);
      break;
    case "run_completed":
      refreshQualitySummary();
      appendLog("[System] 실행 완료");
      break;
    case "run_failed":
      appendLog("[System] 실행 실패");
      break;
    case "prompt":
      // 프롬프트 UI 표시
      break;
  }
}
```

---

## 7. 보조 데이터 흐름

### 7.1 품질 대시보드 조회

```
Renderer
  → IPC: bridge:get-quality-dashboard({ project, lookback })
    → Main: bridgeFetch("GET /quality/dashboard?project=...&lookback=5")
      → FastAPI: _build_quality_dashboard_payload()
        → DBManager.get_quality_signal_summary()
        → QualityDashboard.get_summary()
        → FailureAnalyzer.sink_alignment_summary()
        → PassRateMonitor.get_patch_effectiveness()
        → inspect_project_support_assets()
      ← JSON 응답 (40+ 필드)
    ← bridgeFetch 반환
  ← IPC 반환
← Renderer UI 업데이트
```

### 7.2 재료 파일 가져오기

```
Renderer
  → IPC: material:import-file("bible")
    → Main: dialog.showOpenDialog()
      ← 사용자 파일 선택
    → Main: fs.copyFileSync() × N
    ← { ok: true, imported: ["file1.json", "file2.json"] }
  ← Renderer 파일 목록 갱신
```

### 7.3 프로젝트 설정 저장

```
Renderer
  → IPC: project:save-config-surfaces({ project, authorDirectives, workGuardYaml })
    → Main: fs.writeFileSync(author_directives.txt)
    → Main: fs.writeFileSync(work_guard.yaml)
    ← { ok: true }
  ← Renderer 저장 완료 표시
```

---

## 8. 감사 추적 (Audit Trail)

### 제어 평면 출처 기록

```python
# bridge_server.py — POST /run 성공 시
_append_provenance_log({
    "ts": datetime.utcnow().isoformat(),
    "route": "/run",
    "key": key,
    "sub_key": sub_key,
    "approval_id": approval_id,
    "run_id": run_id,
    "mode": "B",
    "desktop_mode": bool(os.environ.get("GEULDOBI_DESKTOP_MODE"))
})
# → logs/control-plane-provenance.jsonl
```

### 리스크 승인 기록

```python
# risk_approval.py — 리스크 키 검증 시
_append_log({
    "ts": ...,
    "key": key,
    "approval_id": approval_id,
    "result": "accepted" | "rejected",
    "reason": ...
})
# → logs/risk-approval-log.jsonl
```

---

## 9. 3-Pass 감리

| Pass | 검증 항목 | 결과 |
|------|----------|------|
| 1차 | 5단계 파이프라인 경계 명확, 데이터 변환점 식별 완료 | ✅ |
| 2차 | WS 이벤트 시퀀스 3가지 시나리오 코드 증거 확인 | ✅ |
| 3차 | 보조 흐름 3개 + 감사 추적 2개 경로 확인 | ✅ |
