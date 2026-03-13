"""Shared runtime path resolution for engine/workspace/project roots."""

from __future__ import annotations

import os
from pathlib import Path


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
