from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from modules.api.bridge_server import app
from modules.api.risk_approval import ApprovalRecord, RiskApprovalGate
from modules.core.metrics_collector import MetricsCollector

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "docs/2026-03-13/control-plane-approval-provenance-ssot.json"
MAIN_JS = (ROOT / "geuldobi-desktop/src/main.js").read_text(encoding="utf-8")
BRIDGE_SERVER = (ROOT / "modules/api/bridge_server.py").read_text(encoding="utf-8")
PROCESS_RUNNER = (ROOT / "modules/api/process_runner.py").read_text(encoding="utf-8")
METRICS_COLLECTOR = (ROOT / "modules/core/metrics_collector.py").read_text(encoding="utf-8")


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


def _load_contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _approval_record(approval_id: str = "APR-PROV-001") -> ApprovalRecord:
    now = datetime.now(UTC)
    return ApprovalRecord(
        approval_id=approval_id,
        key="44",
        ticket_id="OPS-PROV-001",
        requested_by="desktop-user",
        approved_by_primary="alice",
        approved_by_secondary="bob",
        reason="risk action",
        created_at=now - timedelta(minutes=5),
        expires_at=now + timedelta(minutes=30),
        status="approved",
    )


def test_control_plane_approval_provenance_contract_matches_live_sources() -> None:
    contract = _load_contract()

    assert contract["contract_id"] == "control-plane-approval-provenance-ssot-v1"
    assert 'body.approval_id = approvalId.trim();' in MAIN_JS
    assert "logs/risk-approval-log.jsonl" in BRIDGE_SERVER or "logs/risk-approval-log.jsonl" in (
        ROOT / "modules/api/risk_approval.py"
    ).read_text(encoding="utf-8")
    assert "GEULDOBI_RUN_ID" in PROCESS_RUNNER
    assert "GEULDOBI_RUN_ID" in METRICS_COLLECTOR
    assert "control-plane-provenance.jsonl" in BRIDGE_SERVER


def test_successful_risk_run_writes_approval_to_run_provenance_bridge(tmp_path: Path) -> None:
    gate = RiskApprovalGate(audit_log_path=tmp_path / "risk-approval-log.jsonl")
    approval = _approval_record()
    gate.register(approval)

    with TestClient(app) as client:
        client.app.state.runner = _DummyRunner()
        client.app.state.risk_gate = gate
        client.app.state.control_plane_provenance_log_path = tmp_path / "control-plane-provenance.jsonl"

        response = client.post("/run", json={"key": "44", "approval_id": approval.approval_id})

    assert response.status_code == 202
    payload = response.json()
    provenance_rows = [
        json.loads(line)
        for line in (tmp_path / "control-plane-provenance.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(provenance_rows) == 1
    row = provenance_rows[0]
    assert row["route"] == "/run"
    assert row["protocol_surface"] == "backend_cli_menu_protocol_wrapper"
    assert row["approval_id"] == approval.approval_id
    assert row["run_id"] == payload["run_id"]
    assert row["engine_env_run_id"] == payload["run_id"]
    assert row["risk_key"] is True


def test_status_reads_recent_control_plane_provenance_after_risk_run(tmp_path: Path) -> None:
    gate = RiskApprovalGate(audit_log_path=tmp_path / "risk-approval-log.jsonl")
    approval = _approval_record("APR-PROV-STATUS")
    gate.register(approval)

    with TestClient(app) as client:
        client.app.state.runner = _DummyRunner()
        client.app.state.risk_gate = gate
        client.app.state.control_plane_provenance_log_path = tmp_path / "control-plane-provenance.jsonl"

        response = client.post("/run", json={"key": "44", "approval_id": approval.approval_id})
        assert response.status_code == 202

        status_response = client.get("/status")

    assert status_response.status_code == 200
    payload = status_response.json()
    summary = payload["data"]["control_plane_provenance"]
    assert summary["available"] is True
    assert summary["recent_count"] == 1
    assert summary["risk_row_count"] == 1
    assert summary["latest"]["run_id"] == response.json()["run_id"]
    assert summary["latest"]["approval_id"] == approval.approval_id
    assert summary["latest"]["risk_key"] is True


def test_metrics_collector_uses_run_id_env_as_session_id(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GEULDOBI_RUN_ID", "run-provenance-123")
    collector = MetricsCollector.reset(tmp_path / "metrics")
    try:
        assert collector.session_id == "run-provenance-123"
    finally:
        monkeypatch.delenv("GEULDOBI_RUN_ID", raising=False)
        MetricsCollector.reset(tmp_path / "metrics")


def test_approval_failure_stays_in_backend_code_namespace_not_desktop_transport(tmp_path: Path) -> None:
    with TestClient(app) as client:
        client.app.state.runner = _DummyRunner()
        client.app.state.risk_gate = RiskApprovalGate(audit_log_path=tmp_path / "risk-approval-log.jsonl")
        client.app.state.control_plane_provenance_log_path = tmp_path / "control-plane-provenance.jsonl"

        response = client.post("/run", json={"key": "44"})

    assert response.status_code == 403
    payload = response.json()
    assert payload["code"] == "RISK_APPROVAL_REQUIRED"
    assert payload["run_id"] is None
    assert not (tmp_path / "control-plane-provenance.jsonl").exists()
    assert 'networkErrorCode: "NETWORK_ERROR"' in MAIN_JS
    assert 'httpErrorPrefix: "HTTP_"' in MAIN_JS
