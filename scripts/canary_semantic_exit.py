"""Shared process exit helpers for canary proof payloads."""

from __future__ import annotations

from typing import Any

PASS_STATUS = "pass"
ARCHIVE_OK_STATUS = "ok"


def semantic_exit_code(
    payload: dict[str, Any],
    *,
    proof_keys: tuple[str, ...] = ("hard_gates",),
    require_archive_ok: bool = True,
) -> int:
    """Return a shell exit code from an already-authored proof payload.

    This helper does not adjudicate narrative quality. It only reflects the
    status fields already produced by the runtime/LLM proof surface.
    """

    return 0 if semantic_success(payload, proof_keys=proof_keys, require_archive_ok=require_archive_ok) else 1


def semantic_success(
    payload: dict[str, Any],
    *,
    proof_keys: tuple[str, ...] = ("hard_gates",),
    require_archive_ok: bool = True,
) -> bool:
    if not isinstance(payload, dict):
        return False
    proof = _first_proof(payload, proof_keys)
    if not proof:
        return False
    if str(proof.get("status", "") or "").strip().lower() != PASS_STATUS:
        return False
    if require_archive_ok and _archive_failed(payload):
        return False
    return True


def guarded_stage4_exit_code(payload: dict[str, Any]) -> int:
    return 0 if guarded_stage4_success(payload) else 1


def guarded_stage4_success(payload: dict[str, Any]) -> bool:
    if not isinstance(payload, dict):
        return False
    if payload.get("success") is not True:
        return False
    return not _archive_failed(payload)


def _first_proof(payload: dict[str, Any], proof_keys: tuple[str, ...]) -> dict[str, Any]:
    for key in proof_keys:
        proof = payload.get(key)
        if isinstance(proof, dict):
            return proof
    return {}


def _archive_failed(payload: dict[str, Any]) -> bool:
    archive = payload.get("benchmark_archive")
    if not isinstance(archive, dict) or "status" not in archive:
        return False
    return str(archive.get("status", "") or "").strip().lower() != ARCHIVE_OK_STATUS
