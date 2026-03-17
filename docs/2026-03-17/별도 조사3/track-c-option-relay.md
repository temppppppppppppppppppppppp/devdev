# Track C — 옵션 전달 정합성

> 확신도: 98%
> 범위: 장르맵, 프로젝트 인덱스, 정렬 순서, camelCase→snake_case 변환

---

## 1. 장르맵 양측 비교

### FE (main.js:117-133)

```javascript
const CLI_CONTRACT = Object.freeze({
  defaultGenreIndex: 3,      // "investment"
  projectIndexBase: 1,       // 1-based
  projectSort: "lexical",
  genreIndexMap: Object.freeze({
    wuxia: 1,
    hunter: 2,
    investment: 3,
    fantasy: 4,
    composer: 5,
    cooking: 6,
    alt_history: 7,
    actor: 8,
    sports: 9,
    medical: 10,
  }),
});
```

### BE (process_runner.py:92-103)

```python
_GENRE_INDEX_TO_TYPE = {
    "1": "wuxia",
    "2": "hunter",
    "3": "investment",
    "4": "fantasy",
    "5": "composer",
    "6": "cooking",
    "7": "alt_history",
    "8": "actor",
    "9": "sports",
    "10": "medical",
}
```

### 교차 검증 결과

| 인덱스 | FE (name→index) | BE (index→name) | 일치 |
|--------|-----------------|-----------------|------|
| 1 | wuxia: 1 | "1": "wuxia" | ✅ |
| 2 | hunter: 2 | "2": "hunter" | ✅ |
| 3 | investment: 3 | "3": "investment" | ✅ |
| 4 | fantasy: 4 | "4": "fantasy" | ✅ |
| 5 | composer: 5 | "5": "composer" | ✅ |
| 6 | cooking: 6 | "6": "cooking" | ✅ |
| 7 | alt_history: 7 | "7": "alt_history" | ✅ |
| 8 | actor: 8 | "8": "actor" | ✅ |
| 9 | sports: 9 | "9": "sports" | ✅ |
| 10 | medical: 10 | "10": "medical" | ✅ |

**10개 전부 완전 일치** ✅

---

## 2. 프로젝트 인덱스 정렬 정합성

### 정렬 알고리즘

```
FE: entries.sort()                    // JavaScript Array.sort() — 유니코드 사전순
BE: sorted(path.name for path ...)    // Python sorted() — 유니코드 사전순
```

### 인덱싱 방식

```
FE: CLI_CONTRACT.projectIndexBase = 1   // 1-based
BE: projects[project_index - 1]          // 1-based → 0-based 변환 (process_runner.py:162)
```

### 대체 방식 (project_name 직접 전달)

```python
# process_runner.py:143-148
explicit = str(inputs.get("project_name") or "").strip()
if explicit:
    return explicit  # 인덱스 해석 건너뜀
```

FE에서 `inputs.project_name`을 직접 전달하면 인덱스 해석을 우회. 양측 호환.

---

## 3. camelCase → snake_case 변환 매핑

Main Process의 IPC 핸들러에서 수동 변환. 6개 필드:

| Renderer (camelCase) | HTTP Body (snake_case) | IPC 핸들러 위치 |
|---------------------|----------------------|----------------|
| `subKey` | `sub_key` | main.js:554 (`bridge:run`) |
| `approvalId` | `approval_id` | main.js:557 (`bridge:run`) |
| `epNum` | `ep_num` | main.js:608 (`bridge:save-quality-review`) |
| `operatorLabel` | `operator_label` | main.js:609 (`bridge:save-quality-review`) |
| `promptId` | `prompt_id` | main.js:618 (`bridge:resolve-prompt`) |
| `runId` | URL path param | main.js:616 (`bridge:resolve-prompt`) |

### 변환 코드 증거

```javascript
// bridge:run (main.js:551-559)
ipcMain.handle(IPC_CHANNELS.bridge.run, async (_, { key, subKey, inputs, approvalId }) => {
  const body = { key };
  if (subKey) body.sub_key = subKey;                    // ← 변환
  if (inputs && Object.keys(inputs).length > 0) body.inputs = inputs;
  if (typeof approvalId === "string" && approvalId.trim()) {
    body.approval_id = approvalId.trim();               // ← 변환
  }
  return bridgeFetch(BRIDGE_MANAGED_ROUTES.run, { method: "POST", body: JSON.stringify(body) });
});

// bridge:save-quality-review (main.js:603-613)
ipcMain.handle(IPC_CHANNELS.bridge.saveQualityReview, async (_, { project, epNum, operatorLabel, note = "" }) => {
  return bridgeFetch(BRIDGE_MANAGED_ROUTES.qualityReview, {
    method: "POST",
    body: JSON.stringify({
      project,
      ep_num: epNum,                                    // ← 변환
      operator_label: operatorLabel,                    // ← 변환
      note,
    }),
  });
});

// bridge:resolve-prompt (main.js:615-620)
ipcMain.handle(IPC_CHANNELS.bridge.resolvePrompt, async (_, { runId, promptId, value }) => {
  return bridgeFetch(buildRunInputRoute(runId), {       // runId → URL path
    method: "POST",
    body: JSON.stringify({ prompt_id: promptId, value }), // ← 변환
  });
});
```

---

## 4. 실행 키 (Key) 화이트리스트 정합성

### FE 측

FE에서는 키 값을 **UI에서 직접 선택**하여 IPC로 전달. 키 유효성 검증은 **BE에서만** 수행.

### BE 측 (control_plane_contract.py:5-14)

```python
PUBLIC_RUN_KEYS = frozenset({"0", "1", "2", "3", "4", "6", "7", "44", "77", "88", "99"})
ALLOWED_STAGE0_SUB_KEYS = frozenset({"1", "2", "3", "4", "5", "6", "7"})
RISK_KEYS = frozenset({"44", "77", "88", "99"})
MODE_B_KEYS = PUBLIC_RUN_KEYS  # 모든 공개 키가 Mode B
```

### 검증 흐름

```
Renderer → IPC(key) → Main(bridgeFetch) → FastAPI(run_validator.py)
                                              ↓
                                    key ∈ PUBLIC_RUN_KEYS?
                                    ├─ NO → 400 INVALID_KEY
                                    └─ YES → 계속
```

FE는 **키 검증을 하지 않음** → BE가 단일 검증 권한. 이는 올바른 설계 (서버가 권위).

---

## 5. 품질 리뷰 레이블 화이트리스트

### BE 정의 (bridge_server.py:60-67)

```python
_QUALITY_REVIEW_LABELS = ("좋음", "경계", "AI 티", "지나친 단조", "과잉 설명")
```

### 검증 흐름

FE가 레이블을 선택하여 IPC → HTTP로 전달. BE에서 화이트리스트 검증:

```python
# bridge_server.py:2048-2055
operator_label = str(body.get("operator_label") or "").strip()
if operator_label not in _QUALITY_REVIEW_LABELS:
    return JSONResponse(
        status_code=400,
        content=_err("INVALID_LABEL", f"allowed: {_QUALITY_REVIEW_LABELS}")
    )
```

---

## 6. GET 요청 쿼리 파라미터 전달

### FE → BE 쿼리 파라미터

```javascript
// bridge:get-quality-summary (main.js:578-586)
const qs = `?project=${encodeURIComponent(project)}&lookback=${lookback}`;
return bridgeFetch(`${BRIDGE_MANAGED_ROUTES.qualitySummary}${qs}`);

// bridge:get-quality-dashboard (main.js:588-596)
const qs = `?project=${encodeURIComponent(project)}&lookback=${lookback}`;
return bridgeFetch(`${BRIDGE_MANAGED_ROUTES.qualityDashboard}${qs}`);

// bridge:get-safe-ops-preview (main.js:598-601)
const qs = `?project=${encodeURIComponent(project)}`;
return bridgeFetch(`${BRIDGE_MANAGED_ROUTES.safeOpsPreview}${qs}`);
```

- `project` 파라미터: `encodeURIComponent()` 적용 (한글 프로젝트명 안전)
- `lookback` 파라미터: 정수 (기본값 5)
- BE 측에서 `request.query_params.get()` 으로 수신

---

## 7. 입력 데이터 흐름 요약

```
Renderer UI
    │
    │  { key, subKey, inputs: { genre_index, project_index }, approvalId }
    │
    ▼
Preload (ipcRenderer.invoke)
    │
    │  window.geuldobiDesktop.runKey(key, subKey, inputs, approvalId)
    │
    ▼
Main Process (IPC handler)
    │
    │  { key, sub_key, inputs, approval_id }  ← camelCase→snake_case
    │
    ▼
bridgeFetch() → POST /run
    │
    │  JSON body: { "key": "3", "sub_key": null, "inputs": {...}, "approval_id": null }
    │
    ▼
FastAPI (bridge_server.py)
    │
    │  validate → risk gate → ProcessRunner.start()
    │
    ▼
main_a.py (subprocess)
```

---

## 8. 3-Pass 감리

| Pass | 검증 항목 | 결과 |
|------|----------|------|
| 1차 | 장르맵 10개 FE↔BE 1:1 대응 확인 | ✅ |
| 2차 | camelCase→snake_case 6개 필드 변환 코드 증거 확인 | ✅ |
| 3차 | 프로젝트 인덱스 정렬·base 일치, 키 화이트리스트 단일 권위(BE) 확인 | ✅ |
