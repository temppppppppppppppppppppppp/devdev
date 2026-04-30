"""Stage4 manuscript truth manifest helpers."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

STAGE4_TRUTH_MANIFEST_VERSION = "stage4_truth_manifest_v1"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: object) -> str:
    return sha256_bytes(str(text or "").encode("utf-8"))


def build_human_facing_draft_text(*, title: str, manuscript: str) -> str:
    return f"# {str(title or '').strip()}\n\n{str(manuscript or '')}"


def normalize_manuscript_for_equivalence(text: object, *, title: str = "") -> tuple[str, dict[str, bool]]:
    """Normalize representation-only differences for manuscript equivalence checks."""

    original = str(text or "")
    normalized = original.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    flags = {
        "line_ending_normalization_applied": normalized != original,
        "title_header_normalization_applied": False,
        "blank_line_normalization_applied": False,
    }

    title_text = str(title or "").strip()
    if title_text:
        header_pattern = rf"^\s*#\s*{re.escape(title_text)}\s*\n+"
        without_header = re.sub(header_pattern, "", normalized, count=1)
        if without_header != normalized:
            normalized = without_header
            flags["title_header_normalization_applied"] = True

    blank_normalized = re.sub(r"\n{3,}", "\n\n", normalized).strip()
    if blank_normalized != normalized:
        flags["blank_line_normalization_applied"] = True
    return blank_normalized, flags


def _read_bytes(path: Path | None) -> bytes:
    if path is None or not path.exists():
        return b""
    return path.read_bytes()


def _decode_utf8(data: bytes) -> str:
    return data.decode("utf-8") if data else ""


def _resolve_relative_path(project_root: Path | None, relative_path: object) -> Path | None:
    value = str(relative_path or "").strip()
    if not value:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return path if project_root is None else project_root / path


def _manifest_entry(
    *,
    role: str,
    text: str,
    raw_bytes: bytes | None = None,
    path: str = "",
    title: str = "",
    fallback_raw_hash: str = "",
) -> dict[str, Any]:
    normalized_text, flags = normalize_manuscript_for_equivalence(text, title=title)
    raw_hash = sha256_bytes(raw_bytes) if raw_bytes is not None else sha256_text(text) if text else ""
    if not raw_hash:
        raw_hash = str(fallback_raw_hash or "").strip()
    return {
        "role": role,
        "path": str(path or ""),
        "raw_hash": raw_hash,
        "raw_byte_hash": raw_hash,
        "normalized_hash": sha256_text(normalized_text) if normalized_text else "",
        "char_count": len(text or ""),
        "normalization": flags,
    }


def build_stage4_truth_manifest(
    *,
    ep_num: int,
    title: str,
    db_manuscript: str,
    draft_path: str,
    artifact_meta: dict[str, Any] | None = None,
    project_root: Path | str | None = None,
    settlement_path: str = "",
    fully_settled: bool = False,
) -> dict[str, Any]:
    """Build raw and normalized manuscript equivalence proof for a settled episode."""

    artifact_meta = dict(artifact_meta or {}) if isinstance(artifact_meta, dict) else {}
    root_path = Path(project_root) if isinstance(project_root, str | Path) else None
    artifact_path = str(artifact_meta.get("artifact_path") or "").strip()
    artifact_file = _resolve_relative_path(root_path, artifact_path)
    artifact_bytes = _read_bytes(artifact_file)
    artifact_text = _decode_utf8(artifact_bytes)
    draft_file = _resolve_relative_path(root_path, draft_path)
    draft_bytes = _read_bytes(draft_file)
    if draft_bytes:
        draft_text = _decode_utf8(draft_bytes)
    else:
        draft_text = build_human_facing_draft_text(title=title, manuscript=db_manuscript)
        draft_bytes = draft_text.encode("utf-8")
    db_bytes = str(db_manuscript or "").encode("utf-8")

    entries = {
        "db_manuscript": _manifest_entry(
            role="db_manuscript",
            text=db_manuscript,
            raw_bytes=db_bytes,
            title=title,
        ),
        "final_artifact": _manifest_entry(
            role="final_artifact",
            text=artifact_text,
            raw_bytes=artifact_bytes if artifact_bytes else None,
            path=artifact_path,
            title=title,
            fallback_raw_hash=str(artifact_meta.get("content_hash") or ""),
        ),
        "human_facing_draft": _manifest_entry(
            role="human_facing_draft",
            text=draft_text,
            raw_bytes=draft_bytes,
            path=draft_path,
            title=title,
        ),
    }
    normalized_hashes = {
        key: value.get("normalized_hash", "")
        for key, value in entries.items()
        if str(value.get("normalized_hash") or "").strip()
    }
    unique_hashes = {value for value in normalized_hashes.values() if value}
    reasons: list[str] = []
    if artifact_path and artifact_file is not None and not artifact_file.exists():
        reasons.append("final_artifact_missing")
    equivalent = len(unique_hashes) == 1 and len(normalized_hashes) == len(entries) and not reasons
    if not equivalent and "normalized_hash_mismatch" not in reasons:
        reasons.append("normalized_hash_mismatch")

    return {
        "manifest_version": STAGE4_TRUTH_MANIFEST_VERSION,
        "ep_num": int(ep_num or 0),
        "equivalent": equivalent,
        "reasons": reasons,
        "fully_settled": bool(fully_settled),
        "settlement_packet_path": str(settlement_path or ""),
        "accepted_attempt_key": str(artifact_meta.get("attempt_key") or ""),
        "artifact_class": Path(artifact_path).name.split("__", 1)[0] if artifact_path else "",
        "entries": entries,
    }


def verify_stage4_truth_manifest(manifest: dict[str, Any] | None) -> dict[str, Any]:
    """Return a compact audit verdict for a Stage4 truth manifest."""

    if not isinstance(manifest, dict):
        return {
            "equivalent": False,
            "severity": "blocker",
            "reasons": ["truth_manifest_missing"],
        }
    reasons = [str(item) for item in manifest.get("reasons", []) if str(item or "").strip()]
    equivalent = bool(manifest.get("equivalent")) and not reasons
    missing = any(reason.endswith("_missing") for reason in reasons)
    severity = "ok" if equivalent else "blocker" if missing else "warning"
    return {
        "equivalent": equivalent,
        "severity": severity,
        "reasons": reasons,
        "manifest_version": str(manifest.get("manifest_version") or ""),
        "fully_settled": bool(manifest.get("fully_settled")),
    }
