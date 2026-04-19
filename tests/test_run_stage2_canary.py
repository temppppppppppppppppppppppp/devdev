import json
import sys
from unittest.mock import patch

import scripts.run_stage2_canary as canary_script


def test_run_stage2_canary_invokes_headless_runner_and_analyzes():
    project_root = canary_script.PROJECT_ROOT / "projects" / "_canary" / "s2_canary"

    with (
        patch.object(canary_script, "resolve_workspace_project_dir", return_value=project_root),
        patch.object(canary_script, "project_name_from_path", return_value="_canary/s2_canary"),
        patch.object(canary_script.subprocess, "run") as run_subprocess,
        patch.object(canary_script, "analyze_canary", return_value={"hard_gates": {"status": "pass"}}) as analyze,
    ):
        result = canary_script.run_canary("s2_canary", target_arc_count=2, expected_final_arcs=5)

    run_subprocess.assert_called_once_with(
        [
            sys.executable,
            str(canary_script.PROJECT_ROOT / "scripts" / "canary_stage2_headless.py"),
            "_canary/s2_canary",
            "2",
        ],
        cwd=canary_script.PROJECT_ROOT,
        check=True,
    )
    analyze.assert_called_once_with("_canary/s2_canary", expected_final_arcs=5)
    assert result["hard_gates"]["status"] == "pass"


def test_analyze_stage2_canary_writes_summary(tmp_path):
    project_root = tmp_path / "projects" / "s2test"
    (project_root / "logs").mkdir(parents=True, exist_ok=True)
    summary = {
        "summary_role": "stage2_only_canary",
        "project": "s2test",
        "hard_gates": {"status": "pass", "errors": [], "warnings": []},
    }

    with (
        patch.object(canary_script, "resolve_workspace_project_dir", return_value=project_root),
        patch.object(canary_script, "build_stage2_canary_summary", return_value=summary),
    ):
        result = canary_script.analyze_canary("s2test", expected_final_arcs=5)

    assert result["summary_role"] == "stage2_only_canary"
    summary_path = project_root / "logs" / "stage2_canary_summary.json"
    assert summary_path.exists()
    saved = json.loads(summary_path.read_text(encoding="utf-8"))
    assert saved["hard_gates"]["status"] == "pass"


def test_parse_args_full_stage2_canary():
    with patch(
        "sys.argv",
        [
            "run_stage2_canary.py",
            "full",
            "--source-project",
            "src",
            "--target-project",
            "tgt",
            "--keep-arcs",
            "3",
            "--target-arc-count",
            "2",
            "--force",
        ],
    ):
        args = canary_script.parse_args()
    assert args.command == "full"
    assert args.keep_arcs == 3
    assert args.target_arc_count == 2
    assert args.force is True
