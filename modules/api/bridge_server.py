"""FastAPI 브리지 스켈레톤 — bridge_server.py (스파이크 3)

역할:
- POST /run      → T4(RunValidator) + T6(RiskApprovalGate) + ProcessRunner.start()
- POST /stop     → ProcessRunner.stop() (멱등)
- GET  /status   → 현재 러너 상태 반환
- WS   /events   → run 이벤트 실시간 스트림 (event-schema-v1.json 준수)
- POST /run/{run_id}/input → T5(PromptBroker) 위임 (Mode B)

기동:
    uvicorn modules.api.bridge_server:app --port 8300

판정:
    curl http://127.0.0.1:8300/status
    # → {"ok":true,"code":"OK","data":{"state":"idle"}}
"""

from __future__ import annotations

import importlib.util
import itertools
import json
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse

from modules.api.run_validator import validate_run_request, RISK_KEYS
from modules.api.risk_approval import RiskApprovalGate
from modules.api.process_runner import ProcessRunner

logger = logging.getLogger(__name__)

# ─── T5 PromptBroker — importlib 경로 로드 ───────────────────────────────────
# docs/implementation/prompt_broker.py 는 패키지가 아닌 독립 파일이므로
# importlib.util.spec_from_file_location 으로 직접 임포트.

_BROKER_PATH = Path(__file__).parent.parent.parent / "docs" / "implementation" / "prompt_broker.py"

def _load_prompt_broker_cls():
    if not _BROKER_PATH.exists():
        logger.warning("PromptBroker 파일 없음: %s — Mode B 비활성", _BROKER_PATH)
        return None
    try:
        spec = importlib.util.spec_from_file_location("_prompt_broker", _BROKER_PATH)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.PromptBroker, mod.PromptState
    except Exception:
        logger.exception("PromptBroker 로드 실패 — Mode B 비활성")
        return None

_broker_classes = _load_prompt_broker_cls()
PromptBroker = _broker_classes[0] if _broker_classes else None
PromptState = _broker_classes[1] if _broker_classes else None

# ─── seq 카운터 (전역, 단조 증가) ────────────────────────────────────────────
_seq_iter = itertools.count(1)

def _next_seq() -> int:
    return next(_seq_iter)

def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")

# ─── WS 연결 관리자 ──────────────────────────────────────────────────────────

class WSManager:
    """연결된 WebSocket 클라이언트 목록 유지 + 브로드캐스트."""

    def __init__(self) -> None:
        self._connections: List[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.append(ws)
        logger.debug("WS connected total=%d", len(self._connections))

    def disconnect(self, ws: WebSocket) -> None:
        try:
            self._connections.remove(ws)
        except ValueError:
            pass
        logger.debug("WS disconnected total=%d", len(self._connections))

    async def broadcast(self, event: dict) -> None:
        """event-schema-v1.json 형식 dict를 모든 클라이언트에 전송."""
        dead: List[WebSocket] = []
        for ws in list(self._connections):
            try:
                await ws.send_json(event)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    def emit_sync(self, run_id: str, event: dict) -> None:
        """PromptBroker emit_fn 인터페이스 — sync 진입점.

        asyncio.get_event_loop().is_running() 환경에서
        ensure_future로 비동기 broadcast를 예약한다.
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(self.broadcast(event))
            else:
                loop.run_until_complete(self.broadcast(event))
        except Exception:
            logger.exception("WS broadcast 실패 run_id=%r type=%r", run_id, event.get("type"))

# ─── 이벤트 빌더 헬퍼 ────────────────────────────────────────────────────────

def _build_event(run_id: str, event_type: str, payload: dict) -> dict:
    """event-schema-v1.json 필수 필드 전량 포함."""
    return {
        "event_version": "v1",
        "seq": _next_seq(),
        "run_id": run_id,
        "type": event_type,
        "ts": _ts(),
        "payload": payload,
    }

# ─── Envelope 헬퍼 (api-contract-v1.yaml) ────────────────────────────────────

def _accepted(run_id: str, message: str = "accepted") -> dict:
    return {"ok": True, "run_id": run_id, "code": "OK", "message": message, "data": {}}

def _ok(message: str = "ok") -> dict:
    return {"ok": True, "code": "OK", "message": message, "data": None}

def _err(code: str, message: str, run_id: Optional[str] = None) -> dict:
    return {"ok": False, "run_id": run_id, "code": code, "message": message, "data": None}

# ─── 앱 수명주기 ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    ws_manager = WSManager()
    runner = ProcessRunner()
    risk_gate = RiskApprovalGate()

    if PromptBroker is not None:
        broker = PromptBroker(
            emit_fn=ws_manager.emit_sync,
            seq_counter_fn=_next_seq,
        )
        logger.info("PromptBroker 활성화 — Mode B 사용 가능")
    else:
        broker = None
        logger.warning("PromptBroker 없음 — Mode B 비활성")

    app.state.ws_manager = ws_manager
    app.state.runner = runner
    app.state.risk_gate = risk_gate
    app.state.prompt_broker = broker

    yield

    # 종료 정리
    runner.stop()
    logger.info("bridge_server 종료")

# ─── FastAPI 앱 ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Geuldobi Bridge",
    version="v1",
    lifespan=lifespan,
)

# ─── POST /run ────────────────────────────────────────────────────────────────

@app.post("/run")
async def run_endpoint(request: Request) -> JSONResponse:
    """메뉴 key 실행 요청.

    T4 RunValidator → T6 RiskApprovalGate → ProcessRunner.start() 순서로 처리.
    202 Accepted + run_id 반환.
    """
    runner: ProcessRunner = request.app.state.runner
    risk_gate: RiskApprovalGate = request.app.state.risk_gate
    ws_manager: WSManager = request.app.state.ws_manager

    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content=_err("INVALID_KEY", "request body must be valid JSON"))

    key: str = str(body.get("key", ""))
    sub_key: Optional[str] = body.get("sub_key") or None
    approval_id: Optional[str] = body.get("approval_id") or None
    inputs: dict = body.get("inputs") or {}

    # T4: key / sub_key / 실행 상태 검증
    v = validate_run_request(key, sub_key, runner.state)
    if not v.ok:
        return JSONResponse(status_code=v.http_status, content=_err(v.code, v.message))

    # T6: 위험키 승인 게이트
    if key in RISK_KEYS:
        approval = risk_gate.validate(key, approval_id)
        if not approval.ok:
            return JSONResponse(status_code=approval.http_status, content=_err(approval.code, approval.message))

    run_id = str(uuid.uuid4())
    runner.start(key=key, run_id=run_id, sub_key=sub_key, inputs=inputs)
    logger.info("RUN_STARTED run_id=%r key=%r", run_id, key)

    # run_started 이벤트 브로드캐스트
    await ws_manager.broadcast(_build_event(run_id, "run_started", {"key": key}))

    return JSONResponse(status_code=202, content=_accepted(run_id))

# ─── POST /run/{run_id}/input ────────────────────────────────────────────────

@app.post("/run/{run_id}/input")
async def resolve_prompt(run_id: str, request: Request) -> JSONResponse:
    """Mode B 인터랙티브 프롬프트 응답 (T5 PromptBroker 위임).

    200 — 성공 (prompt_resolved WS 이벤트 발행됨)
    400 — INVALID_PROMPT_ID
    409 — PROMPT_ALREADY_RESOLVED
    """
    broker = request.app.state.prompt_broker
    if broker is None:
        return JSONResponse(status_code=400, content=_err("INVALID_PROMPT_ID", "Mode B is not available"))

    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content=_err("INVALID_PROMPT_ID", "request body must be valid JSON"))

    prompt_id: str = body.get("prompt_id", "")
    value = body.get("value")

    if not prompt_id:
        return JSONResponse(status_code=400, content=_err("INVALID_PROMPT_ID", "prompt_id is required"))

    status, error_code = broker.resolve(run_id, prompt_id, value)
    if status == "error":
        http_status = 409 if error_code == "PROMPT_ALREADY_RESOLVED" else 400
        return JSONResponse(status_code=http_status, content=_err(error_code, error_code.lower().replace("_", " ")))

    return JSONResponse(status_code=200, content=_ok("prompt accepted"))

# ─── POST /stop ───────────────────────────────────────────────────────────────

@app.post("/stop")
async def stop_endpoint(request: Request) -> JSONResponse:
    """현재 실행 중지 (멱등).

    실행 중이 아니어도 200 OK 반환.
    """
    runner: ProcessRunner = request.app.state.runner
    ws_manager: WSManager = request.app.state.ws_manager
    run_id = runner.run_id or "unknown"

    runner.stop()
    logger.info("STOP run_id=%r", run_id)

    return JSONResponse(status_code=200, content=_ok("stopped"))

# ─── GET /status ──────────────────────────────────────────────────────────────

@app.get("/status")
async def status_endpoint(request: Request) -> JSONResponse:
    """현재 러너 상태 조회.

    Returns:
        {"ok": true, "code": "OK", "data": {"state": "idle|running|...", "run_id": "..."}}
    """
    runner: ProcessRunner = request.app.state.runner

    data: dict = {"state": runner.state}
    if runner.run_id is not None:
        data["run_id"] = runner.run_id
    if runner.pid is not None:
        data["pid"] = runner.pid

    return JSONResponse(status_code=200, content={"ok": True, "code": "OK", "data": data})

# ─── WS /events ───────────────────────────────────────────────────────────────

@app.websocket("/events")
async def ws_events(websocket: WebSocket) -> None:
    """실시간 이벤트 스트림 (event-schema-v1.json 형식).

    클라이언트는 연결 후 JSON 이벤트를 수신한다.
    연결 유지용 ping은 uvicorn websockets 핸들러가 처리.
    """
    ws_manager: WSManager = websocket.app.state.ws_manager
    await ws_manager.connect(websocket)
    try:
        while True:
            # 클라이언트 메시지 수신 대기 (연결 유지)
            # Mode B에서 클라이언트가 텍스트를 보내면 무시 (입력은 /run/{id}/input 경로)
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(websocket)
