"""Shared material visibility helpers for pipeline-facing selectors."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "material_visibility.json"


def _load_visibility_config(root: Path = ROOT) -> dict[str, Any]:
    config_path = root / "config" / "material_visibility.json"
    if not config_path.is_file():
        return {}
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _allowed_file_names(folder: str, root: Path = ROOT) -> set[str] | None:
    payload = _load_visibility_config(root)
    folders = payload.get("folders")
    if not isinstance(folders, dict):
        return None
    folder_payload = folders.get(folder)
    if not isinstance(folder_payload, dict):
        return None
    visible_files = folder_payload.get("visible_files")
    if not isinstance(visible_files, list):
        return None
    allowed = {str(value).strip() for value in visible_files if str(value).strip()}
    return allowed


def list_visible_material_files(folder: str, root: Path = ROOT) -> list[Path]:
    folder_path = root / folder
    if not folder_path.is_dir():
        return []
    files = sorted(path for path in folder_path.glob("*.json") if path.is_file())
    allowed = _allowed_file_names(folder, root)
    if allowed is None:
        return files
    return [path for path in files if path.name in allowed]


def visibility_config_path(root: Path = ROOT) -> Path:
    return root / "config" / "material_visibility.json"
