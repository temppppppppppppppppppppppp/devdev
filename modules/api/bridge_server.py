"""FastAPI 브리지 — bridge_server.py (실체화)

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

import itertools
import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from modules.api.process_runner import MODE_B_KEYS, PROJECT_ROOT, ProcessRunner
from modules.api.prompt_broker import PromptBroker, PromptState
from modules.api.prompt_classifier import classify as classify_prompt
from modules.api.risk_approval import RiskApprovalGate
from modules.api.run_validator import RISK_KEYS, validate_run_request
from modules.core.db_manager import DBManager

logger = logging.getLogger(__name__)

# ─── seq 카운터 (전역, 단조 증가) ────────────────────────────────────────────
_seq_iter = itertools.count(1)

def _next_seq() -> int:
    return next(_seq_iter)

def _ts() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S+00:00")

# ─── WS 연결 관리자 ──────────────────────────────────────────────────────────

class WSManager:
    """연결된 WebSocket 클라이언트 목록 유지 + 브로드캐스트."""

    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

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
        dead: list[WebSocket] = []
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

def _err(code: str, message: str, run_id: str | None = None) -> dict:
    return {"ok": False, "run_id": run_id, "code": code, "message": message, "data": None}


def _get_project_db_path(project_name: str) -> Path:
    projects_root = (PROJECT_ROOT / "projects").resolve()
    normalized = str(project_name or "").strip()
    if not normalized:
        raise ValueError("project is required")

    candidate = (projects_root / normalized / "project_data.db").resolve()
    if projects_root not in candidate.parents:
        raise ValueError("invalid project path")
    return candidate

# ─── 앱 수명주기 ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    ws_manager = WSManager()
    runner = ProcessRunner()
    risk_gate = RiskApprovalGate()

    broker = PromptBroker(
        emit_fn=ws_manager.emit_sync,
        seq_counter_fn=_next_seq,
    )
    logger.info("PromptBroker 활성화 — Mode B 사용 가능")

    app.state.ws_manager = ws_manager
    app.state.runner = runner
    app.state.risk_gate = risk_gate
    app.state.prompt_broker = broker

    yield

    # 종료 정리
    await runner.stop()
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
    sub_key: str | None = body.get("sub_key") or None
    approval_id: str | None = body.get("approval_id") or None
    inputs: dict = body.get("inputs") or {}

    # T4: key / sub_key / 실행 상태 검증
    v = validate_run_request(key, sub_key, runner.state)
    if not v.ok:
        return JSONResponse(status_code=v.http_status, content=_err(v.code, v.message))

    # T6: 위험키 승인 게이트
    # 데스크톱 모드: UI confirm() 대체 — approval_id 없으면 자동 승인
    _desktop_mode = os.environ.get("GEULDOBI_DESKTOP_MODE", "0") == "1"
    if key in RISK_KEYS:
        if _desktop_mode and not approval_id:
            logger.info("Desktop mode: auto-approving risk key=%r", key)
        else:
            approval = risk_gate.validate(key, approval_id)
            if not approval.ok:
                return JSONResponse(status_code=approval.http_status, content=_err(approval.code, approval.message))

    run_id = str(uuid.uuid4())
    broker: PromptBroker = request.app.state.prompt_broker
    use_mode_b = key in MODE_B_KEYS

    # stdout/exit 콜백 → WS 이벤트 브로드캐스트
    async def _on_line(text: str) -> None:
        await ws_manager.broadcast(_build_event(run_id, "stdout", {"text": text}))

    async def _on_exit(returncode: int) -> None:
        etype = "run_completed" if returncode == 0 else "run_failed"
        await ws_manager.broadcast(
            _build_event(run_id, etype, {"returncode": returncode})
        )
        broker.cleanup_run(run_id)

    # Mode B: 프롬프트 감지 → PromptBroker → WS → UI → stdin
    async def _on_prompt(prompt_text: str, context_lines: list[str]) -> None:
        meta = classify_prompt(prompt_text, context_lines)
        prompt_id = str(uuid.uuid4())
        prompt_state = PromptState(
            prompt_id=prompt_id,
            step_id=meta["step_id"],
            input_type=meta["input_type"],
            default=meta["default"],
            timeout_sec=300,
            options=meta.get("options"),
        )
        # prompt_text도 payload에 포함 (UI 렌더링용)
        prompt_state.prompt_text = meta["prompt_text"]

        # broker가 prompt_request WS 이벤트 발행 + 사용자 응답 대기
        value = await broker.request_input(run_id, prompt_state)
        # 응답을 subprocess stdin에 전달
        await runner.write_stdin(str(value) if value is not None else "")

    try:
        await runner.start(
            key=key,
            run_id=run_id,
            sub_key=sub_key,
            inputs=inputs,
            on_line=_on_line,
            on_exit=_on_exit,
            on_prompt=_on_prompt if use_mode_b else None,
        )
    except FileNotFoundError as exc:
        return JSONResponse(
            status_code=500,
            content=_err("INTERNAL_ERROR", str(exc), run_id),
        )
    except RuntimeError as exc:
        return JSONResponse(
            status_code=409,
            content=_err("RUN_ALREADY_ACTIVE", str(exc), run_id),
        )
    except Exception as exc:
        logger.exception("ProcessRunner start failed run_id=%r", run_id)
        return JSONResponse(
            status_code=500,
            content=_err("INTERNAL_ERROR", "subprocess start failed", run_id),
        )

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
    broker: PromptBroker = request.app.state.prompt_broker

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

    await runner.stop()
    await ws_manager.broadcast(_build_event(run_id, "run_stopped", {}))
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


@app.get("/quality/summary")
async def quality_summary_endpoint(project: str = "", lookback: int = 5) -> JSONResponse:
    """프로젝트 최근 품질 신호 요약 조회."""
    try:
        db_path = _get_project_db_path(project)
    except ValueError as exc:
        return JSONResponse(status_code=400, content=_err("INVALID_PROJECT", str(exc)))

    safe_lookback = max(1, min(int(lookback or 5), 20))
    if not db_path.exists():
        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "code": "OK",
                "data": {
                    "project": project,
                    "available": False,
                    "lookback": safe_lookback,
                    "latest_ep": None,
                    "signals": {},
                    "recent": [],
                    "latest_ai_slop_hits": [],
                },
            },
        )

    db = DBManager(db_path)
    try:
        summary = db.get_quality_signal_summary(lookback=safe_lookback)
    except Exception as exc:
        logger.exception("quality summary failed for project=%r", project)
        return JSONResponse(status_code=500, content=_err("INTERNAL_ERROR", str(exc)))
    finally:
        try:
            db.close()
        except Exception:
            pass

    summary["project"] = project
    return JSONResponse(status_code=200, content={"ok": True, "code": "OK", "data": summary})

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
