"""Helpers for snapshotting attempt artifacts into stable log paths."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Any

from modules.core.soft_failure import report_soft_failure, resolve_project_log_dir


def build_candidate_key(*, label: str = "", strategy: str = "", fallback: str = "") -> str:
    """Build a compact candidate key shared across sinks."""
    parts = [str(value).strip() for value in (label, strategy) if str(value or "").strip()]
    if parts:
        return "|".join(parts)
    return str(fallback or "").strip()


def normalize_artifact_meta(
    meta: Any,
    *,
    fallback_candidate_key: str = "",
    fallback_content_hash: str = "",
    fallback_artifact_path: str = "",
) -> dict[str, str]:
    """Normalize artifact linkage metadata into a stable dict shape."""
    if not isinstance(meta, dict):
        meta = {}
    return {
        "candidate_key": str(meta.get("candidate_key", "") or fallback_candidate_key or "").strip(),
        "content_hash": str(meta.get("content_hash", "") or fallback_content_hash or "").strip(),
        "artifact_path": str(meta.get("artifact_path", "") or fallback_artifact_path or "").strip(),
    }


def snapshot_logged_artifact(
    project,
    *,
    stage: int,
    ep_num: int | None = None,
    arc_num: int | None = None,
    attempt_num: int = 1,
    candidate_key: str = "",
    artifact_kind: str = "artifact",
    payload: Any = None,
) -> dict:
    """Persist a stable snapshot for an attempt and return linkage metadata."""
    serialized = _serialize_payload(payload)
    content_hash = hashlib.sha256(serialized["hash_bytes"]).hexdigest() if serialized["hash_bytes"] else ""
    artifact_path = ""
    root = _resolve_project_root(project)
    if root is not None and serialized["text"]:
        try:
            stage_dir = root / "logs" / "artifacts" / f"stage{int(stage or 0)}"
            scope_dir = stage_dir / _build_scope_dir(stage=int(stage or 0), ep_num=ep_num, arc_num=arc_num)
            scope_dir = scope_dir / f"attempt_{max(1, int(attempt_num or 1)):02d}"
            scope_dir.mkdir(parents=True, exist_ok=True)
            filename = (
                f"{_slugify(artifact_kind) or 'artifact'}__{_slugify(candidate_key) or 'unknown'}{serialized['suffix']}"
            )
            file_path = scope_dir / filename
            _write_artifact_snapshot(file_path, serialized["text"])
            artifact_path = file_path.relative_to(root).as_posix()
        except Exception as exc:
            logging.warning("[artifact_logging] snapshot persistence failed: %s", str(exc)[:160])
            report_soft_failure(
                component="artifact_logging",
                operation="snapshot_logged_artifact",
                message="artifact snapshot persistence failed",
                exc=exc,
                stage=stage,
                ep_num=ep_num,
                log_dir=resolve_project_log_dir(project),
                extra={
                    "artifact_kind": str(artifact_kind or ""),
                    "candidate_key": str(candidate_key or ""),
                    "attempt_num": max(1, int(attempt_num or 1)),
                },
            )

    return {
        "candidate_key": str(candidate_key or "").strip(),
        "content_hash": content_hash,
        "artifact_path": artifact_path,
    }


def _serialize_payload(payload: Any) -> dict[str, bytes | str]:
    if payload is None:
        return {"text": "", "hash_bytes": b"", "suffix": ".txt"}

    if isinstance(payload, str):
        text = payload
        return {
            "text": text,
            "hash_bytes": text.encode("utf-8"),
            "suffix": ".txt",
        }

    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    pretty = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str)
    return {
        "text": pretty,
        "hash_bytes": canonical.encode("utf-8"),
        "suffix": ".json",
    }


def _write_artifact_snapshot(file_path: Path, text: str) -> None:
    file_path.write_text(text, encoding="utf-8")


def _resolve_project_root(project) -> Path | None:
    if project is None:
        return None

    paths = getattr(project, "paths", None)
    root = getattr(paths, "root", None)
    if isinstance(root, (str, Path)):
        return Path(root)

    db = getattr(project, "db", None)
    db_path = getattr(db, "db_path", None)
    if isinstance(db_path, (str, Path)):
        return Path(db_path).parent

    return None


def _build_scope_dir(*, stage: int, ep_num: int | None, arc_num: int | None) -> Path:
    if stage == 2 and arc_num is not None:
        return Path(f"arc_{int(arc_num):03d}")
    if ep_num is not None:
        return Path(f"ep_{int(ep_num):04d}")
    if arc_num is not None:
        return Path(f"arc_{int(arc_num):03d}")
    return Path("unknown_scope")


def _slugify(value: str) -> str:
    text = re.sub(r"[^0-9A-Za-z._-]+", "_", str(value or "").strip())
    return text.strip("._-")
