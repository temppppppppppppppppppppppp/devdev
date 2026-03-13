import os

from modules.core import runtime_paths
from modules.core.project_manager import ProjectContext
from modules.core.system import StudioSystem


def test_resolve_projects_root_prefers_explicit_env(monkeypatch, tmp_path):
    explicit_root = tmp_path / "explicit-projects"
    monkeypatch.setenv("GEULDOBI_PROJECTS_ROOT", str(explicit_root))
    monkeypatch.setenv("GEULDOBI_WORKSPACE", str(tmp_path / "workspace"))

    assert runtime_paths.resolve_projects_root(tmp_path / "engine") == explicit_root.resolve()


def test_resolve_projects_root_falls_back_to_workspace(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    monkeypatch.delenv("GEULDOBI_PROJECTS_ROOT", raising=False)
    monkeypatch.setenv("GEULDOBI_WORKSPACE", str(workspace))

    assert runtime_paths.resolve_projects_root(tmp_path / "engine") == (workspace / "projects").resolve()


def test_resolve_project_dir_rejects_escape(monkeypatch, tmp_path):
    monkeypatch.setenv("GEULDOBI_PROJECTS_ROOT", str(tmp_path / "projects"))

    try:
        runtime_paths.resolve_project_dir("..", tmp_path / "engine")
    except ValueError as exc:
        assert "invalid project path" in str(exc)
    else:
        raise AssertionError("expected invalid project path")


def test_project_context_defaults_to_explicit_projects_root(monkeypatch, tmp_path):
    explicit_root = tmp_path / "external-projects"
    monkeypatch.setenv("GEULDOBI_PROJECTS_ROOT", str(explicit_root))

    ctx = ProjectContext("demo")
    try:
        assert ctx.paths.root == (explicit_root / "demo").resolve()
        assert ctx.paths.db_file == (explicit_root / "demo" / "project_data.db").resolve()
    finally:
        ctx.close()


def test_project_context_does_not_reload_workspace_env(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("GOOGLE_API_KEY=root-key\n", encoding="utf-8")
    monkeypatch.setenv("GEULDOBI_PROJECTS_ROOT", str(tmp_path / "external-projects"))
    monkeypatch.setenv("GOOGLE_API_KEY", "project-key")

    ctx = ProjectContext("demo")
    try:
        assert os.environ["GOOGLE_API_KEY"] == "project-key"
    finally:
        ctx.close()


def test_studio_system_boot_uses_explicit_projects_root(tmp_path):
    explicit_root = tmp_path / "external-projects"
    sys = StudioSystem(api_client=None)

    sys.boot_v20_project("demo", genre="investment", projects_root=explicit_root)
    try:
        assert sys.project.paths.root == (explicit_root / "demo").resolve()
        assert sys.project.paths.db_file == (explicit_root / "demo" / "project_data.db").resolve()
    finally:
        sys.project.close()
