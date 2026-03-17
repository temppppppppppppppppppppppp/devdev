"""Shared runtime path resolution for engine/workspace/project roots.

Supported runtime authority chain (Class A):
    desktop app (geuldobi-desktop/src/main.js)
      -> bridge_server (modules/api/bridge_server.py)
      -> process_runner (modules/api/process_runner.py)
      -> main_a.py
      -> stage pipeline (modules/core/)

Compatibility paths (Class B — labeled, not authoritative):
    root main.js               — debug shadow entry, re-exports desktop src/main.js
    geuldobi-desktop/main.js   — legacy shim, re-exports src/main.js
    lite_mode/                  — maintenance-only, not part of supported runtime
    test_mode/                  — maintenance-only, not part of supported runtime
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


RUNTIME_AUTHORITY_CONTRACT = {
    "supported_entry": "geuldobi-desktop/src/main.js",
    "supported_chain": [
        "geuldobi-desktop/src/main.js",
        "modules/api/bridge_server.py",
        "modules/api/process_runner.py",
        "main_a.py",
    ],
    "compatibility_entries": {
        "main.js": "debug_shadow_entry",
        "geuldobi-desktop/main.js": "legacy_shim",
        "lite_mode/": "maintenance_only",
        "test_mode/": "maintenance_only",
    },
    "boot_log_surfaces": {
        "desktop_pre_bridge": {
            "path": "%LOCALAPPDATA%/Geuldobi/electron-main.log",
            "authority": "desktop_local_appdata",
            "description": "Electron main-process boot/debug sink before bridge health is known.",
        },
        "engine_bootstrap_fallback": {
            "path": "logs/error.log",
            "authority": "workspace_level",
            "description": "main_a.py boot failure fallback before project-local runtime sinks exist.",
        },
    },
    "runtime_log_authority": "project_local",
}


def build_runtime_authority_summary() -> dict[str, Any]:
    return {
        "supported_entry": str(RUNTIME_AUTHORITY_CONTRACT.get("supported_entry") or ""),
        "supported_chain": list(RUNTIME_AUTHORITY_CONTRACT.get("supported_chain") or []),
        "compatibility_entries": dict(RUNTIME_AUTHORITY_CONTRACT.get("compatibility_entries") or {}),
        "boot_log_surfaces": {
            key: dict(value) if isinstance(value, dict) else {}
            for key, value in (RUNTIME_AUTHORITY_CONTRACT.get("boot_log_surfaces") or {}).items()
        },
        "runtime_log_authority": str(RUNTIME_AUTHORITY_CONTRACT.get("runtime_log_authority") or ""),
    }


def resolve_engine_root(default_root: str | Path) -> Path:
    explicit = os.environ.get("GEULDOBI_ENGINE_ROOT")
    if explicit:
        return Path(explicit).resolve()
    return Path(default_root).resolve()


def resolve_workspace_root(default_root: str | Path) -> Path:
    workspace = os.environ.get("GEULDOBI_WORKSPACE")
    if workspace:
        return Path(workspace).resolve()
    return resolve_engine_root(default_root)


def resolve_projects_root(default_root: str | Path) -> Path:
    explicit = os.environ.get("GEULDOBI_PROJECTS_ROOT")
    if explicit:
        return Path(explicit).resolve()
    return (resolve_workspace_root(default_root) / "projects").resolve()


def resolve_project_dir(project_name: str, default_root: str | Path) -> Path:
    projects_root = resolve_projects_root(default_root)
    normalized = str(project_name or "").strip()
    if not normalized:
        raise ValueError("project is required")

    candidate = (projects_root / normalized).resolve()
    try:
        candidate.relative_to(projects_root)
    except ValueError as exc:
        raise ValueError("invalid project path") from exc

    if candidate == projects_root:
        raise ValueError("invalid project path")
    return candidate
