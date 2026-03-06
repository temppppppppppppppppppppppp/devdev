# 스파이크 3 결과 — FastAPI 브리지 스켈레톤

- 날짜: 2026-03-06
- 판정: **PASS**

---

## 판정 기준 충족

| 기준 | 결과 |
|------|------|
| uvicorn 기동 성공 | PASS |
| `GET /status` → `{"state":"idle"}` 응답 | **PASS** |
| T4 RunValidator 연결 (INVALID_KEY / SUB_KEY_REQUIRED) | PASS |
| T6 RiskApprovalGate 연결 (RISK_APPROVAL_REQUIRED) | PASS |
| ProcessRunner 상태 전이 (idle → running) | PASS |
| T5 PromptBroker importlib 로드 | PASS |

---

## 기동 명령

```bash
uvicorn modules.api.bridge_server:app --port 8300 --log-level warning
```

---

## 엔드포인트 응답 캡처

```
GET /status (기동 직후)
→ {"ok":true,"code":"OK","data":{"state":"idle"}}

POST /stop
→ {"ok":true,"code":"OK","message":"stopped","data":null}

POST /run {"key":"Z"}
→ 400 {"ok":false,"code":"INVALID_KEY","message":"Key 'Z' is not allowed.","data":null}

POST /run {"key":"0"}  (sub_key 누락)
→ 400 {"ok":false,"code":"SUB_KEY_REQUIRED","message":"sub_key is required when key=0.","data":null}

POST /run {"key":"44"}  (approval_id 없음)
→ 403 {"ok":false,"code":"RISK_APPROVAL_REQUIRED","message":"approval_id is required for risk key operations.","data":null}

POST /run {"key":"2"}
→ 202 {"ok":true,"run_id":"b8dcb030-...","code":"OK","message":"accepted","data":{}}

GET /status (run 직후)
→ {"ok":true,"code":"OK","data":{"state":"running","run_id":"b8dcb030-..."}}
```

---

## 산출물

| 파일 | 역할 | 줄 수 |
|------|------|-------|
| `modules/api/bridge_server.py` | FastAPI 앱 + 라우트 4개 + WS | 233줄 |
| `modules/api/process_runner.py` | subprocess 래퍼 스텁 | 88줄 |
| `modules/api/__init__.py` | ProcessRunner export 추가 | — |
| `requirements.txt` | fastapi / uvicorn / websockets 추가 | — |

---

## 모듈 연결 현황

| 모듈 | 터미널 | 연결 방식 | 상태 |
|------|--------|-----------|------|
| `run_validator.validate_run_request` | T4 | `from modules.api.run_validator import ...` | **연결됨** |
| `RiskApprovalGate.validate` | T6 | `from modules.api.risk_approval import ...` | **연결됨** |
| `PromptBroker` | T5 | `importlib.util.spec_from_file_location` (`docs/implementation/prompt_broker.py`) | **연결됨** |
| `ProcessRunner` | 스파이크3 신규 | `from modules.api.process_runner import ...` | **스텁 동작** |

---

## 스파이크 2 연결 후 작업 (TODO)

ProcessRunner는 현재 상태 추적만 실제 동작하는 스텁.
스파이크 2 PASS 후 아래 두 메서드에 실제 Popen 연결 필요:

```python
# process_runner.py
def start(self, key, run_id, ...):
    # asyncio.create_subprocess_exec(sys.executable, "main_a.py", ...)
    # proc.stdin.write(f"{key}\n")

async def read_stdout(self):
    # while True: line = await proc.stdout.readline()
```

---

## 환경

- Python 3.11
- fastapi 0.128.0
- uvicorn 0.40.0
- Windows 11
