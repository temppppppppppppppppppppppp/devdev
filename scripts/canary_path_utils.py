from __future__ import annotations

from pathlib import Path


CANARY_ROOT_NAME = "_canary"


def projects_root(app_root: str | Path) -> Path:
    return (Path(app_root).resolve() / "projects").resolve()


def canary_root(app_root: str | Path) -> Path:
    return (projects_root(app_root) / CANARY_ROOT_NAME).resolve()


def project_name_from_path(app_root: str | Path, project_path: str | Path) -> str:
    path = Path(project_path).resolve()
    root = projects_root(app_root)
    try:
        return path.relative_to(root).as_posix()
    except Exception:
        return path.name


def resolve_workspace_project_dir(
    app_root: str | Path,
    project_name: str,
    *,
    prefer_canary: bool,
    require_exists: bool,
) -> Path:
    raw_name = str(project_name or "").strip().replace("\\", "/")
    if not raw_name:
        raise ValueError("project is required")

    candidate_path = Path(raw_name)
    if candidate_path.is_absolute():
        return candidate_path.resolve()

    root = projects_root(app_root)
    explicit_projects_prefix = "projects/"
    explicit_canary_prefix = f"{CANARY_ROOT_NAME}/"
    if raw_name.startswith(explicit_projects_prefix):
        return _resolve_under_projects_root(app_root, raw_name[len(explicit_projects_prefix) :])
    if raw_name.startswith(explicit_canary_prefix):
        return _resolve_under_projects_root(app_root, raw_name)

    primary_name = f"{CANARY_ROOT_NAME}/{raw_name}" if prefer_canary else raw_name
    secondary_name = raw_name if prefer_canary else f"{CANARY_ROOT_NAME}/{raw_name}"
    primary = _resolve_under_projects_root(app_root, primary_name)
    secondary = _resolve_under_projects_root(app_root, secondary_name)

    if require_exists:
        if primary.exists():
            return primary
        if secondary.exists():
            return secondary
    return primary


def _resolve_under_projects_root(app_root: str | Path, relative_name: str) -> Path:
    root = projects_root(app_root)
    candidate = (root / relative_name).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("invalid project path") from exc
    if candidate == root:
        raise ValueError("invalid project path")
    return candidate
