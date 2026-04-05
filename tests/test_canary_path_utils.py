from pathlib import Path

from scripts.canary_path_utils import project_name_from_path, resolve_workspace_project_dir


def test_resolve_workspace_project_dir_prefers_canary_root_for_new_target(tmp_path):
    (tmp_path / "projects").mkdir()

    target = resolve_workspace_project_dir(
        tmp_path,
        "stage4_ep3_probe_r1",
        prefer_canary=True,
        require_exists=False,
    )

    assert target == (tmp_path / "projects" / "_canary" / "stage4_ep3_probe_r1").resolve()


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
    project_path = tmp_path / "projects" / "_canary" / "canary___000403_stage4_ep3_numauth_r3"
    project_path.mkdir(parents=True)

    assert project_name_from_path(tmp_path, project_path) == "_canary/canary___000403_stage4_ep3_numauth_r3"
