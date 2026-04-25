from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

DEFAULT_CANARY_DIR_NAME = "canary"
LEGACY_CANARY_ROOT_NAME = "_canary"
GEULDOBI_CANARY_ROOT_ENV = "GEULDOBI_CANARY_ROOT"
GEULDOBI_PROJECTS_ROOT_ENV = "GEULDOBI_PROJECTS_ROOT"


def projects_root(app_root: str | Path) -> Path:
    return (Path(app_root).resolve() / "projects").resolve()


def canary_root(app_root: str | Path) -> Path:
    explicit = os.environ.get(GEULDOBI_CANARY_ROOT_ENV)
    if explicit:
        return Path(explicit).resolve()
    return (Path(app_root).resolve() / DEFAULT_CANARY_DIR_NAME).resolve()


def legacy_canary_root(app_root: str | Path) -> Path:
    return (projects_root(app_root) / LEGACY_CANARY_ROOT_NAME).resolve()


def project_name_from_path(app_root: str | Path, project_path: str | Path) -> str:
    path = Path(project_path).resolve()
    root = canary_root(app_root)
    try:
        return path.relative_to(root).as_posix()
    except Exception:
        pass

    root = projects_root(app_root)
    try:
        return path.relative_to(root).as_posix()
    except Exception:
        return path.name


def canary_projects_root_for_path(app_root: str | Path, project_path: str | Path) -> Path:
    path = Path(project_path).resolve()
    root = canary_root(app_root)
    try:
        path.relative_to(root)
        return root
    except Exception:
        return projects_root(app_root)


def canary_runtime_env(app_root: str | Path, *, project_path: str | Path | None = None) -> dict[str, str]:
    env = dict(os.environ)
    root = canary_root(app_root) if project_path is None else canary_projects_root_for_path(app_root, project_path)
    env[GEULDOBI_PROJECTS_ROOT_ENV] = str(root)
    return env


@contextmanager
def scoped_canary_projects_root(app_root: str | Path, *, project_path: str | Path | None = None):
    root = canary_root(app_root) if project_path is None else canary_projects_root_for_path(app_root, project_path)
    previous = os.environ.get(GEULDOBI_PROJECTS_ROOT_ENV)
    os.environ[GEULDOBI_PROJECTS_ROOT_ENV] = str(root)
    try:
        yield root
    finally:
        if previous is None:
            os.environ.pop(GEULDOBI_PROJECTS_ROOT_ENV, None)
        else:
            os.environ[GEULDOBI_PROJECTS_ROOT_ENV] = previous


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
        raise ValueError("absolute project paths are not allowed for canary project resolution")

    explicit_projects_prefix = "projects/"
    explicit_new_canary_prefix = f"{DEFAULT_CANARY_DIR_NAME}/"
    explicit_legacy_canary_prefix = f"{LEGACY_CANARY_ROOT_NAME}/"
    if raw_name.startswith(explicit_projects_prefix):
        return _resolve_under_projects_root(app_root, raw_name[len(explicit_projects_prefix) :])
    if raw_name.startswith(explicit_new_canary_prefix):
        return _resolve_under_canary_root(app_root, raw_name[len(explicit_new_canary_prefix) :])
    if raw_name.startswith(explicit_legacy_canary_prefix):
        return _resolve_canary_candidate(
            app_root,
            raw_name[len(explicit_legacy_canary_prefix) :],
            require_exists=require_exists,
        )

    if prefer_canary:
        return _resolve_canary_candidate(app_root, raw_name, require_exists=require_exists)

    primary = _resolve_under_projects_root(app_root, raw_name)
    secondary = _resolve_under_legacy_canary_root(app_root, raw_name)

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


def _resolve_canary_candidate(app_root: str | Path, relative_name: str, *, require_exists: bool) -> Path:
    primary = _resolve_under_canary_root(app_root, relative_name)
    secondary = _resolve_under_legacy_canary_root(app_root, relative_name)
    if require_exists:
        if primary.exists():
            return primary
        if secondary.exists():
            return secondary
    return primary


def _resolve_under_canary_root(app_root: str | Path, relative_name: str) -> Path:
    return _resolve_under_root(canary_root(app_root), relative_name)


def _resolve_under_legacy_canary_root(app_root: str | Path, relative_name: str) -> Path:
    return _resolve_under_root(legacy_canary_root(app_root), relative_name)


def _resolve_under_root(root: Path, relative_name: str) -> Path:
    candidate = (root / relative_name).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("invalid project path") from exc
    if candidate == root:
        raise ValueError("invalid project path")
    return candidate
