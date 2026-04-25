import os
from pathlib import Path

from scripts.canary_path_utils import (
    canary_runtime_env,
    project_name_from_path,
    resolve_workspace_project_dir,
    scoped_canary_projects_root,
)


def test_resolve_workspace_project_dir_prefers_canary_root_for_new_target(tmp_path):
    (tmp_path / "projects").mkdir()

    target = resolve_workspace_project_dir(
        tmp_path,
        "stage4_ep3_probe_r1",
        prefer_canary=True,
        require_exists=False,
    )

    assert target == (tmp_path / "canary" / "stage4_ep3_probe_r1").resolve()


def test_resolve_workspace_project_dir_falls_back_to_legacy_canary_for_existing_read(tmp_path):
    legacy_project = tmp_path / "projects" / "_canary" / "stage4_ep3_probe_r1"
    legacy_project.mkdir(parents=True)

    target = resolve_workspace_project_dir(
        tmp_path,
        "stage4_ep3_probe_r1",
        prefer_canary=True,
        require_exists=True,
    )

    assert target == legacy_project.resolve()


def test_resolve_workspace_project_dir_falls_back_to_live_project_for_existing_source(tmp_path):
    live_project = tmp_path / "projects" / "__000403"
    live_project.mkdir(parents=True)

    source = resolve_workspace_project_dir(
        tmp_path,
        "__000403",
        prefer_canary=False,
        require_exists=True,
    )

    assert source == live_project.resolve()


def test_project_name_from_path_preserves_nested_canary_segment(tmp_path):
    project_path = tmp_path / "canary" / "canary___000403_stage4_ep3_numauth_r3"
    project_path.mkdir(parents=True)

    assert project_name_from_path(tmp_path, project_path) == "canary___000403_stage4_ep3_numauth_r3"


def test_project_name_from_path_preserves_legacy_canary_segment(tmp_path):
    project_path = tmp_path / "projects" / "_canary" / "canary___000403_stage4_ep3_numauth_r3"
    project_path.mkdir(parents=True)

    assert project_name_from_path(tmp_path, project_path) == "_canary/canary___000403_stage4_ep3_numauth_r3"


def test_scoped_canary_projects_root_restores_previous_env(tmp_path, monkeypatch):
    prior = str(tmp_path / "operator_projects")
    monkeypatch.setenv("GEULDOBI_PROJECTS_ROOT", prior)

    with scoped_canary_projects_root(tmp_path) as root:
        assert root == (tmp_path / "canary").resolve()
        assert Path(canary_runtime_env(tmp_path)["GEULDOBI_PROJECTS_ROOT"]) == (tmp_path / "canary").resolve()

    assert canary_runtime_env(tmp_path)["GEULDOBI_PROJECTS_ROOT"] == str((tmp_path / "canary").resolve())
    assert os.environ["GEULDOBI_PROJECTS_ROOT"] == prior
