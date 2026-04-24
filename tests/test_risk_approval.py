"""T6 — 위험키 승인 게이트 회귀 테스트.

커버 분기:
    RISK_APPROVAL_REQUIRED (없음/미등록)
    RISK_APPROVAL_EXPIRED
    RISK_APPROVAL_DUAL_CONTROL_REQUIRED
    정상 승인 통과
    감사 로그 기록 확인
"""

import json
from datetime import datetime, timedelta, timezone

UTC = timezone.utc
from pathlib import Path

import pytest

from modules.api.risk_approval import ApprovalRecord, RiskApprovalGate

# ─── 헬퍼 ───────────────────────────────────────────────────────────────────

_NOW = datetime.now(UTC)
_FUTURE = _NOW + timedelta(hours=2)
_PAST = _NOW - timedelta(hours=1)


def _record(
    approval_id: str = "APR-001",
    key: str = "44",
    primary: str = "alice",
    secondary: str = "bob",
    expires_at: datetime = _FUTURE,
    status: str = "approved",
) -> ApprovalRecord:
    return ApprovalRecord(
        approval_id=approval_id,
        key=key,
        ticket_id="OPS-0001",
        requested_by="requester",
        approved_by_primary=primary,
        approved_by_secondary=secondary,
        reason="test",
        created_at=_NOW - timedelta(hours=1),
        expires_at=expires_at,
        status=status,
    )


def _gate(tmp_path: Path, record: ApprovalRecord | None = None) -> RiskApprovalGate:
    gate = RiskApprovalGate(audit_log_path=tmp_path / "audit.jsonl")
    if record is not None:
        gate.register(record)
    return gate


# ─── RISK_APPROVAL_REQUIRED ──────────────────────────────────────────────────

def test_missing_approval_id_returns_403(tmp_path: Path) -> None:
    gate = _gate(tmp_path)
    result = gate.validate(key="44", approval_id=None, operator="op1")
    assert not result.ok
    assert result.http_status == 403
    assert result.code == "RISK_APPROVAL_REQUIRED"


def test_empty_approval_id_returns_403(tmp_path: Path) -> None:
    gate = _gate(tmp_path)
    result = gate.validate(key="44", approval_id="", operator="op1")
    assert not result.ok
    assert result.code == "RISK_APPROVAL_REQUIRED"


def test_unknown_approval_id_returns_403(tmp_path: Path) -> None:
    gate = _gate(tmp_path)
    result = gate.validate(key="44", approval_id="APR-UNKNOWN", operator="op1")
    assert not result.ok
    assert result.code == "RISK_APPROVAL_REQUIRED"


# ─── RISK_APPROVAL_EXPIRED ───────────────────────────────────────────────────

def test_expired_approval_returns_403(tmp_path: Path) -> None:
    rec = _record(expires_at=_PAST)
    gate = _gate(tmp_path, rec)
    result = gate.validate(key="44", approval_id=rec.approval_id, operator="op1", _now=_NOW)
    assert not result.ok
    assert result.http_status == 403
    assert result.code == "RISK_APPROVAL_EXPIRED"


# ─── RISK_APPROVAL_DUAL_CONTROL_REQUIRED ─────────────────────────────────────

def test_same_approver_returns_403(tmp_path: Path) -> None:
    rec = _record(primary="alice", secondary="alice")
    gate = _gate(tmp_path, rec)
    result = gate.validate(key="99", approval_id=rec.approval_id, operator="op1")
    assert not result.ok
    assert result.http_status == 403
    assert result.code == "RISK_APPROVAL_DUAL_CONTROL_REQUIRED"


# ─── 정상 통과 ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("key", ["44", "77", "88", "99"])
def test_valid_approval_passes_all_risk_keys(tmp_path: Path, key: str) -> None:
    rec = _record(key=key)
    gate = _gate(tmp_path, rec)
    result = gate.validate(key=key, approval_id=rec.approval_id, operator="op1")
    assert result.ok
    assert result.http_status == 202
    assert result.code == "OK"


# ─── 감사 로그 ───────────────────────────────────────────────────────────────

def test_audit_log_written_on_success(tmp_path: Path) -> None:
    rec = _record()
    gate = _gate(tmp_path, rec)
    gate.validate(key="44", approval_id=rec.approval_id, operator="op_audit")

    log_path = tmp_path / "audit.jsonl"
    assert log_path.exists()
    entries = [json.loads(line) for line in log_path.read_text().splitlines()]
    assert len(entries) == 1
    entry = entries[0]
    assert entry["approval_id"] == rec.approval_id
    assert entry["ok"] is True
    assert entry["verdict"] == "OK"
    assert entry["operator"] == "op_audit"
    assert "ticket_id" in entry
    assert "approved_by_primary" in entry
    assert "approved_by_secondary" in entry


def test_audit_log_written_on_failure(tmp_path: Path) -> None:
    gate = _gate(tmp_path)
    gate.validate(key="44", approval_id=None, operator="bad_op")

    log_path = tmp_path / "audit.jsonl"
    assert log_path.exists()
    entries = [json.loads(line) for line in log_path.read_text().splitlines()]
    assert entries[0]["ok"] is False
    assert entries[0]["verdict"] == "RISK_APPROVAL_REQUIRED"


def test_audit_log_accumulates_multiple_entries(tmp_path: Path) -> None:
    rec = _record()
    gate = _gate(tmp_path, rec)
    gate.validate(key="44", approval_id=None, operator="op1")           # fail
    gate.validate(key="44", approval_id=rec.approval_id, operator="op2")  # pass

    log_path = tmp_path / "audit.jsonl"
    entries = [json.loads(line) for line in log_path.read_text().splitlines()]
    assert len(entries) == 2
    assert entries[0]["ok"] is False
    assert entries[1]["ok"] is True


def test_expired_approval_logged(tmp_path: Path) -> None:
    rec = _record(expires_at=_PAST)
    gate = _gate(tmp_path, rec)
    gate.validate(key="77", approval_id=rec.approval_id, operator="op1", _now=_NOW)

    log_path = tmp_path / "audit.jsonl"
    entry = json.loads(log_path.read_text().splitlines()[0])
    assert entry["verdict"] == "RISK_APPROVAL_EXPIRED"
    assert "expires_at" in entry
