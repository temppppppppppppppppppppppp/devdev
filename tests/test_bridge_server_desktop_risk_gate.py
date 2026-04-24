from __future__ import annotations

from datetime import datetime, timedelta, timezone

UTC = timezone.utc

from fastapi.testclient import TestClient

from modules.api.bridge_server import app
from modules.api.risk_approval import ApprovalRecord, RiskApprovalGate


class _DummyRunner:
    def __init__(self) -> None:
        self.state = "idle"
        self.run_id = None
        self.pid = 12345

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
        self.state = "running"
        self.run_id = run_id

    async def stop(self) -> None:
        self.state = "idle"
        self.run_id = None

    def get_runtime_diagnostics(self) -> dict:
        return {}


def _approval_record(approval_id: str = "APR-DESKTOP-001") -> ApprovalRecord:
    now = datetime.now(UTC)
    return ApprovalRecord(
        approval_id=approval_id,
        key="44",
        ticket_id="OPS-DESKTOP-001",
        requested_by="desktop-user",
        approved_by_primary="alice",
        approved_by_secondary="bob",
        reason="desktop risk action",
        created_at=now - timedelta(minutes=5),
        expires_at=now + timedelta(minutes=30),
        status="approved",
    )


def test_desktop_mode_risk_key_requires_approval_id(monkeypatch, tmp_path):
    monkeypatch.setenv("GEULDOBI_DESKTOP_MODE", "1")
    with TestClient(app) as client:
        client.app.state.runner = _DummyRunner()
        client.app.state.risk_gate = RiskApprovalGate(audit_log_path=tmp_path / "risk-approval-log.jsonl")

        response = client.post("/run", json={"key": "44"})

    assert response.status_code == 403
    payload = response.json()
    assert payload["ok"] is False
    assert payload["code"] == "RISK_APPROVAL_REQUIRED"


def test_desktop_mode_risk_key_accepts_valid_approval_id(monkeypatch, tmp_path):
    monkeypatch.setenv("GEULDOBI_DESKTOP_MODE", "1")
    gate = RiskApprovalGate(audit_log_path=tmp_path / "risk-approval-log.jsonl")
    approval = _approval_record()
    gate.register(approval)

    with TestClient(app) as client:
        client.app.state.runner = _DummyRunner()
        client.app.state.risk_gate = gate

        response = client.post("/run", json={"key": "44", "approval_id": approval.approval_id})

    assert response.status_code == 202
    payload = response.json()
    assert payload["ok"] is True
    assert payload["code"] == "OK"
    assert payload["run_id"]
