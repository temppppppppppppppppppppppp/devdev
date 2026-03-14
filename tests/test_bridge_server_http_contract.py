from __future__ import annotations

from fastapi.testclient import TestClient

from modules.api.bridge_server import app


class _DummyRunner:
    def __init__(self, *, state: str = "idle", run_id: str | None = None, pid: int | None = None) -> None:
        self.state = state
        self.run_id = run_id
        self.pid = pid
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
        return {}


def test_status_returns_runtime_state_model():
    with TestClient(app) as client:
        client.app.state.runner = _DummyRunner(state="starting", run_id="run-123", pid=999)

        response = client.get("/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["code"] == "OK"
    assert payload["data"] == {"state": "starting", "run_id": "run-123", "pid": 999}


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
