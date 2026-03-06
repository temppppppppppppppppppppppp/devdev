"""
FastAPI 라우트: POST /run/{run_id}/input  (input_route.py)

Mode B 인터랙티브 프롬프트 응답 처리.
api-contract-v1.yaml 계약 준수:
  - 200: prompt accepted (OkEnvelope)
  - 400: INVALID_PROMPT_ID (ErrorEnvelope)
  - 409: PROMPT_ALREADY_RESOLVED (ErrorEnvelope)

사용법 (FastAPI app에 등록):
    from docs.implementation.input_route import router as input_router
    app.include_router(input_router)
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()


# ------------------------------------------------------------------
# Envelope 헬퍼 (api-contract-v1.yaml OkEnvelope / ErrorEnvelope)
# ------------------------------------------------------------------

def _ok(message: str = "prompt accepted") -> dict:
    return {
        "ok": True,
        "code": "OK",
        "message": message,
        "data": None,
    }


def _error(code: str, message: str) -> dict:
    return {
        "ok": False,
        "code": code,
        "message": message,
        "data": None,
    }


# ------------------------------------------------------------------
# POST /run/{run_id}/input
# ------------------------------------------------------------------

@router.post("/run/{run_id}/input")
async def resolve_prompt(run_id: str, request: Request) -> JSONResponse:
    """
    pending prompt에 사용자 응답 주입.

    Body: { "prompt_id": str, "value": any }

    Responses:
      200 — prompt accepted, prompt_resolved WS 이벤트 발행됨
      400 — INVALID_PROMPT_ID (prompt_id 누락 또는 run에 속하지 않음)
      409 — PROMPT_ALREADY_RESOLVED (중복 입력)
    """
    broker = request.app.state.prompt_broker

    # Body 파싱
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content=_error("INVALID_PROMPT_ID", "request body must be valid JSON"),
        )

    prompt_id: str = body.get("prompt_id", "")
    value = body.get("value")

    if not prompt_id:
        return JSONResponse(
            status_code=400,
            content=_error("INVALID_PROMPT_ID", "prompt_id is required"),
        )

    # PromptBroker에 위임
    status, error_code = broker.resolve(run_id, prompt_id, value)

    if status == "error":
        http_status = 409 if error_code == "PROMPT_ALREADY_RESOLVED" else 400
        return JSONResponse(
            status_code=http_status,
            content=_error(error_code, error_code.lower().replace("_", " ")),
        )

    return JSONResponse(status_code=200, content=_ok())
