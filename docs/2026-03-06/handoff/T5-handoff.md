# T5 Handoff — Mode B 입력 라우트 / WS 이벤트

- terminal: T5
- role: Mode B 입력/이벤트
- status: COMPLETE
- last_seen_broadcast_seq: [2026-03-06T00:00:00+09:00] CODE_LOCK 선언

---

## 산출물

| 파일 | 역할 |
|------|------|
| `docs/implementation/prompt_broker.py` | PromptBroker 클래스 — prompt 생애주기 추적 + WS emit |
| `docs/implementation/input_route.py` | FastAPI 라우트 — `POST /run/{run_id}/input` |

---

## 구현 상세

### PromptBroker (`prompt_broker.py`)

| 메서드 | 역할 |
|--------|------|
| `request_input(run_id, prompt)` | `prompt_request` 발행 → asyncio.wait_for 대기 → 타임아웃 시 `prompt_timeout` 발행 |
| `resolve(run_id, prompt_id, value)` | `prompt_resolved` 발행, 오류 코드 반환 |
| `cleanup_run(run_id)` | run 종료 시 관련 prompt_id 정리 |

- **스레드 안전**: `threading.Lock`으로 내부 Dict 보호. `resolve()`는 동기 호출 가능.
- **이벤트 스키마 준수**: `_build_event()`가 `event_version/seq/run_id/type/ts/payload` 전량 포함.
- **생성자 주입**: `emit_fn(run_id, event_dict)` + `seq_counter_fn() -> int` — WS 브로드캐스트 구현체와 seq 관리는 호출자가 주입.

### 이벤트 왕복 흐름

```
runner                   PromptBroker              client (WS)
  |                           |                         |
  |--- await request_input -->|                         |
  |                           |--- prompt_request ----->|
  |                           |<-- /run/{id}/input -----|  (resolve 호출)
  |                           |--- prompt_resolved ---->|
  |<-- return value ----------|                         |
```

타임아웃 경로:
```
  |                           |--- prompt_request ----->|
  |                           |  (timeout_sec 경과)
  |                           |--- prompt_timeout ----->|  (source: "default" 적용)
  |<-- return default --------|                         |
```

### input_route (`input_route.py`)

- **정상**: `200 OkEnvelope {ok: true, code: "OK"}`
- **오류 400**: `prompt_id` 누락 또는 run에 속하지 않는 id → `INVALID_PROMPT_ID`
- **오류 409**: 이미 처리된 id → `PROMPT_ALREADY_RESOLVED`
- Body 파싱 실패(JSON 오류) → `400 INVALID_PROMPT_ID`

---

## 완료 기준 체크

| 기준 | 결과 |
|------|------|
| `prompt_request → input → prompt_resolved` 왕복 경로 구현 | PASS |
| timeout 분기 (`prompt_timeout` + default 적용) 구현 | PASS |
| 이벤트 스키마 필수 필드 (`event_version/seq/run_id/type/ts/payload`) 준수 | PASS |
| `INVALID_PROMPT_ID` (400) 처리 | PASS |
| `PROMPT_ALREADY_RESOLVED` (409) 처리 | PASS |
| 중복 입력 차단 (resolved=True 후 재입력) | PASS |

---

## 통합 시 주의사항

1. **app.state.prompt_broker** — FastAPI 앱 초기화 시 PromptBroker 인스턴스 등록 필요:
   ```python
   import itertools
   _seq = itertools.count(1)
   app.state.prompt_broker = PromptBroker(
       emit_fn=ws_manager.broadcast,
       seq_counter_fn=lambda: next(_seq),
   )
   ```

2. **cleanup_run() 호출** — `run_completed` / `run_failed` 이벤트 발행 직후 호출하여 메모리 해제.

3. **asyncio 루프 공유** — `request_input()`은 runner와 동일한 이벤트 루프에서 await해야 함. `prompt._event`는 루프 생성 시점에 바인딩됨.

4. **prompt-map-v1.json 연동** — runner가 `request_input()` 호출 시 `step_id`/`input_type`/`options`/`default`/`timeout_sec`를 prompt-map에서 읽어 `PromptState` 생성.

---

## T3 계약 대조 (event-schema-v1.json)

| type | 발행 조건 | payload 필수 필드 | 구현 위치 |
|------|-----------|-------------------|----------|
| `prompt_request` | `request_input()` 진입 시 | `prompt_id, step_id, input_type, default, timeout_sec` | `prompt_broker.py:request_input` |
| `prompt_resolved` | `resolve()` 성공 시 | `prompt_id, value, source="user"` | `prompt_broker.py:resolve` |
| `prompt_timeout` | `asyncio.TimeoutError` 발생 시 | `prompt_id, applied_default` | `prompt_broker.py:request_input` |
