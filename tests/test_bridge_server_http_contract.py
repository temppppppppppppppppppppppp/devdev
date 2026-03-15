from __future__ import annotations

from fastapi.testclient import TestClient

from modules.api.bridge_server import app


class _DummyRunner:
    def __init__(
        self,
        *,
        state: str = "idle",
        run_id: str | None = None,
        pid: int | None = None,
        diagnostics: dict | None = None,
    ) -> None:
        self.state = state
        self.run_id = run_id
        self.pid = pid
        self._diagnostics = diagnostics or {}
        self.start_calls: list[dict] = []
        self.stop_calls = 0

    async def start(
        self,
        *,
        key: str,
        run_id: str,
        sub_key: str | None = None,
        inputs: dict | None = None,
        on_line=None,
        on_exit=None,
        on_prompt=None,
        mode: str | None = None,
    ) -> None:
        self.start_calls.append(
            {
                "key": key,
                "run_id": run_id,
                "sub_key": sub_key,
                "inputs": inputs or {},
                "mode": mode,
            }
        )
        self.state = "running"
        self.run_id = run_id
        self.pid = 12345

    async def stop(self) -> None:
        self.stop_calls += 1
        self.state = "idle"
        self.run_id = None
        self.pid = None

    def get_runtime_diagnostics(self) -> dict:
        return dict(self._diagnostics)


class _DummyPromptBroker:
    def __init__(self, snapshot: dict | None = None) -> None:
        self.snapshot = snapshot or {"pending_prompt_count": 0, "pending_prompts": []}

    def snapshot_run(self, run_id: str) -> dict:
        return dict(self.snapshot)


def test_status_returns_runtime_state_model():
    with TestClient(app) as client:
        client.app.state.runner = _DummyRunner(state="starting", run_id="run-123", pid=999)

        response = client.get("/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["code"] == "OK"
    assert payload["data"] == {"state": "starting", "run_id": "run-123", "pid": 999}


def test_status_includes_runtime_resync_snapshot_when_prompt_is_pending():
    pending_prompt = {
        "prompt_id": "prompt-1",
        "step_id": "choice",
        "input_type": "enum",
        "default": "1",
        "timeout_sec": 300,
        "prompt_text": "계속할 옵션을 선택하세요",
        "options": [{"key": "1", "label": "계속"}],
    }

    with TestClient(app) as client:
        client.app.state.runner = _DummyRunner(
            state="running",
            run_id="run-123",
            pid=999,
            diagnostics={
                "key": "7",
                "mode": "B",
                "duration_ms": 1200,
                "last_prompt_step": "choice",
            },
        )
        client.app.state.prompt_broker = _DummyPromptBroker(
            {"pending_prompt_count": 1, "pending_prompts": [pending_prompt]}
        )

        response = client.get("/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["state"] == "running"
    assert payload["data"]["run_id"] == "run-123"
    assert payload["data"]["key"] == "7"
    assert payload["data"]["mode"] == "B"
    assert payload["data"]["duration_ms"] == 1200
    assert payload["data"]["last_prompt_step"] == "choice"
    assert payload["data"]["pending_prompt_count"] == 1
    assert payload["data"]["pending_prompts"] == [pending_prompt]


def test_run_invalid_key_returns_contract_error_from_real_app():
    with TestClient(app) as client:
        client.app.state.runner = _DummyRunner()
        response = client.post("/run", json={"key": "99999"})

    assert response.status_code == 400
    payload = response.json()
    assert payload["ok"] is False
    assert payload["code"] == "INVALID_KEY"


def test_run_key0_missing_sub_key_returns_contract_error_from_real_app():
    with TestClient(app) as client:
        client.app.state.runner = _DummyRunner()
        response = client.post("/run", json={"key": "0"})

    assert response.status_code == 400
    payload = response.json()
    assert payload["ok"] is False
    assert payload["code"] == "SUB_KEY_REQUIRED"


def test_run_key0_hidden_cancel_sub_key_is_rejected_from_real_app():
    with TestClient(app) as client:
        client.app.state.runner = _DummyRunner()
        response = client.post("/run", json={"key": "0", "sub_key": "0"})

    assert response.status_code == 400
    payload = response.json()
    assert payload["ok"] is False
    assert payload["code"] == "INVALID_SUB_KEY"


def test_run_rejects_when_runner_is_starting():
    with TestClient(app) as client:
        client.app.state.runner = _DummyRunner(state="starting", run_id="run-active", pid=222)

        response = client.post("/run", json={"key": "2"})

    assert response.status_code == 409
    payload = response.json()
    assert payload["ok"] is False
    assert payload["code"] == "RUN_ALREADY_ACTIVE"


def test_run_accepts_valid_request_through_real_app():
    with TestClient(app) as client:
        runner = _DummyRunner()
        client.app.state.runner = runner

        response = client.post("/run", json={"key": "2", "inputs": {"project_index": 1}})

    assert response.status_code == 202
    payload = response.json()
    assert payload["ok"] is True
    assert payload["code"] == "OK"
    assert payload["run_id"]
    assert runner.start_calls[0]["key"] == "2"
    assert runner.start_calls[0]["inputs"] == {"project_index": 1}
