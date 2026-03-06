"""T6 — 위험키(44/77/88/99) 승인 게이트.

계약 근거: docs/implementation/api-contract-v1.yaml
체크리스트: docs/implementation/risk-approval-checklist.md
샘플 로그: docs/implementation/samples/risk-approval-log.samples.jsonl

오류코드:
    RISK_APPROVAL_REQUIRED              403  approval_id 없거나 레코드 없음
    RISK_APPROVAL_EXPIRED               403  expires_at 초과
    RISK_APPROVAL_DUAL_CONTROL_REQUIRED 403  primary == secondary approver

감사 로그: logs/risk-approval-log.jsonl (approval_id 기준 추적 가능)
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from modules.api.run_validator import ValidationResult

logger = logging.getLogger(__name__)

_DEFAULT_AUDIT_LOG = Path("logs/risk-approval-log.jsonl")


# ─── 데이터 클래스 ───────────────────────────────────────────────────────────

@dataclass
class ApprovalRecord:
    approval_id: str
    key: str
    ticket_id: str
    requested_by: str
    approved_by_primary: str
    approved_by_secondary: str
    reason: str
    created_at: datetime
    expires_at: datetime
    status: str  # "approved" | "expired" | "rejected_dual_control"

    @classmethod
    def from_dict(cls, d: dict) -> "ApprovalRecord":
        def _dt(s: str) -> datetime:
            return datetime.fromisoformat(s)

        return cls(
            approval_id=d["approval_id"],
            key=d["key"],
            ticket_id=d.get("ticket_id", ""),
            requested_by=d.get("requested_by", ""),
            approved_by_primary=d["approved_by_primary"],
            approved_by_secondary=d["approved_by_secondary"],
            reason=d.get("reason", ""),
            created_at=_dt(d["created_at"]),
            expires_at=_dt(d["expires_at"]),
            status=d.get("status", "approved"),
        )


# ─── 오류 헬퍼 ───────────────────────────────────────────────────────────────

def _err(code: str, message: str) -> ValidationResult:
    return ValidationResult(ok=False, http_status=403, code=code, message=message)


_OK_APPROVAL = ValidationResult(
    ok=True, http_status=202, code="OK", message="Approval validated."
)


# ─── 승인 게이트 ─────────────────────────────────────────────────────────────

class RiskApprovalGate:
    """위험키 승인 정책을 강제하고 감사 로그를 기록한다.

    Args:
        store: approval_id → ApprovalRecord 매핑 (런타임 주입).
        audit_log_path: JSONL 감사 로그 경로.
    """

    def __init__(
        self,
        store: Optional[Dict[str, ApprovalRecord]] = None,
        audit_log_path: Path = _DEFAULT_AUDIT_LOG,
    ) -> None:
        self._store: Dict[str, ApprovalRecord] = store if store is not None else {}
        self._audit_log_path = audit_log_path

    # ── 공개 API ────────────────────────────────────────────────────────────

    def register(self, record: ApprovalRecord) -> None:
        """테스트·운영에서 승인 레코드를 주입한다."""
        self._store[record.approval_id] = record

    def validate(
        self,
        key: str,
        approval_id: Optional[str],
        operator: str = "",
        _now: Optional[datetime] = None,
    ) -> ValidationResult:
        """위험키 승인을 검증하고 결과를 감사 로그에 기록한다.

        Args:
            key: 실행할 메뉴 키 ("44" | "77" | "88" | "99").
            approval_id: 클라이언트가 제출한 승인 ID.
            operator: 실행 요청자 식별자 (감사 로그용).
            _now: 현재 시각 주입 (테스트용). None 이면 실제 UTC 시각 사용.

        Returns:
            ValidationResult — ok=True 이면 실행 허용.
        """
        now = _now if _now is not None else datetime.now(tz=timezone.utc)

        # 1. approval_id 없음
        if not approval_id:
            logger.warning("RISK_APPROVAL_REQUIRED key=%r operator=%r", key, operator)
            result = _err(
                "RISK_APPROVAL_REQUIRED",
                "approval_id is required for risk key operations.",
            )
            self._write_audit(key, approval_id, operator, now, result)
            return result

        # 2. 레코드 조회 실패
        record = self._store.get(approval_id)
        if record is None:
            logger.warning(
                "RISK_APPROVAL_REQUIRED unknown approval_id=%r key=%r", approval_id, key
            )
            result = _err(
                "RISK_APPROVAL_REQUIRED",
                f"approval_id '{approval_id}' not found.",
            )
            self._write_audit(key, approval_id, operator, now, result)
            return result

        # 3. 만료 검사
        expires = record.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if now > expires:
            logger.warning(
                "RISK_APPROVAL_EXPIRED approval_id=%r expires_at=%s now=%s",
                approval_id,
                expires.isoformat(),
                now.isoformat(),
            )
            result = _err(
                "RISK_APPROVAL_EXPIRED",
                f"approval_id '{approval_id}' expired at {expires.isoformat()}.",
            )
            self._write_audit(key, approval_id, operator, now, result, record)
            return result

        # 4. Dual-control 검사 (primary != secondary)
        if record.approved_by_primary == record.approved_by_secondary:
            logger.warning(
                "RISK_APPROVAL_DUAL_CONTROL_REQUIRED approval_id=%r approver=%r",
                approval_id,
                record.approved_by_primary,
            )
            result = _err(
                "RISK_APPROVAL_DUAL_CONTROL_REQUIRED",
                "Primary and secondary approvers must be different people.",
            )
            self._write_audit(key, approval_id, operator, now, result, record)
            return result

        # 5. 통과 — 감사 로그 기록
        logger.info(
            "RISK_APPROVAL_OK approval_id=%r key=%r operator=%r", approval_id, key, operator
        )
        self._write_audit(key, approval_id, operator, now, _OK_APPROVAL, record)
        return _OK_APPROVAL

    # ── 내부 헬퍼 ───────────────────────────────────────────────────────────

    def _write_audit(
        self,
        key: str,
        approval_id: Optional[str],
        operator: str,
        ts: datetime,
        result: ValidationResult,
        record: Optional[ApprovalRecord] = None,
    ) -> None:
        """JSONL 감사 로그에 한 줄 추가한다."""
        entry: dict = {
            "log_id": str(uuid.uuid4()),
            "ts": ts.isoformat(),
            "key": key,
            "approval_id": approval_id,
            "operator": operator,
            "verdict": result.code,
            "ok": result.ok,
        }
        if record is not None:
            entry["ticket_id"] = record.ticket_id
            entry["approved_by_primary"] = record.approved_by_primary
            entry["approved_by_secondary"] = record.approved_by_secondary
            entry["expires_at"] = record.expires_at.isoformat()

        try:
            self._audit_log_path.parent.mkdir(parents=True, exist_ok=True)
            with self._audit_log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            logger.exception("Failed to write risk approval audit log")
