import importlib.util
import subprocess
import sys
from pathlib import Path


def _load_post_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "post_benchmark_operator_comment.py"
    spec = importlib.util.spec_from_file_location("post_benchmark_operator_comment", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_report_test_helpers():
    helper_path = Path(__file__).resolve().parents[1] / "tests" / "test_report_benchmark_operator_lines.py"
    spec = importlib.util.spec_from_file_location("test_report_benchmark_operator_lines", helper_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_build_comment_markdown_supports_pair_preview(tmp_path):
    module = _load_post_module()
    helper = _load_report_test_helpers()

    run_a = "20260423_120000__stage4-supervised__target-ep15__aaaa1111"
    run_b = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    left_root = helper._write_record(tmp_path, run_id=run_a, status="interrupted")
    right_root = helper._write_record(tmp_path, run_id=run_b, status="completed")

    markdown = module.build_comment_markdown(
        title="Preview Snapshot",
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
        pairs=[(str(left_root), str(right_root))],
    )

    assert markdown.startswith("## Preview Snapshot\n")
    assert "### Explicit Comparisons" in markdown
    assert (
        f"- {left_root} -> {right_root}: status=clean; ci_gate=pass; gate_basis=clean; "
        "headline=no remediation needed; verdict=better; changed_sections=run_meta,stage_metrics,watchpoints"
    ) in markdown


def test_post_issue_comment_invokes_gh_with_stdin(monkeypatch):
    module = _load_post_module()
    captured: dict[str, object] = {}

    def fake_run(*args, **kwargs):
        captured["args"] = args[0]
        captured["input"] = kwargs.get("input")

        class Result:
            stdout = "https://github.com/example/repo/issues/5#issuecomment-1\n"

        return Result()

    monkeypatch.setattr(module, "resolve_gh_executable", lambda explicit_path="": "gh")
    monkeypatch.setattr(module.subprocess, "run", fake_run)

    response = module.post_issue_comment(
        repo="owner/name",
        issue_number=5,
        markdown="## Snapshot\n",
    )

    assert captured["args"] == [
        "gh",
        "issue",
        "comment",
        "5",
        "--repo",
        "owner/name",
        "--body-file",
        "-",
    ]
    assert captured["input"] == "## Snapshot\n"
    assert response == "https://github.com/example/repo/issues/5#issuecomment-1"


def test_apply_issue_5_defaults_fills_repo_and_issue_when_requested():
    module = _load_post_module()
    args = module.argparse.Namespace(
        repo="",
        issue_number=0,
        issue_5_defaults=True,
    )

    resolved = module.apply_issue_5_defaults(args)

    assert resolved.repo == "temppppppppppppppppppppppp/devdev"
    assert resolved.issue_number == 5


def test_apply_issue_5_defaults_preserves_explicit_repo_and_issue():
    module = _load_post_module()
    args = module.argparse.Namespace(
        repo="owner/custom",
        issue_number=9,
        issue_5_defaults=True,
    )

    resolved = module.apply_issue_5_defaults(args)

    assert resolved.repo == "owner/custom"
    assert resolved.issue_number == 9


def test_apply_issue_5_snapshot_defaults_enables_issue_5_defaults_and_latest_pair():
    module = _load_post_module()
    args = module.argparse.Namespace(
        issue_5_defaults=False,
        latest_live_pair=False,
        issue_5_snapshot=True,
    )

    resolved = module.apply_issue_5_snapshot_defaults(args)

    assert resolved.issue_5_defaults is True
    assert resolved.latest_live_pair is True


def test_post_benchmark_operator_comment_cli_preview_outputs_markdown(tmp_path):
    helper = _load_report_test_helpers()
    run_a = "20260423_120000__stage4-supervised__target-ep15__aaaa1111"
    run_b = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    left_root = helper._write_record(tmp_path, run_id=run_a, status="interrupted")
    right_root = helper._write_record(tmp_path, run_id=run_b, status="completed")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/post_benchmark_operator_comment.py",
            "--workspace-root",
            str(tmp_path),
            "--benchmark-root",
            "benchmarks",
            "--title",
            "CLI Preview",
            "--pair",
            str(left_root),
            str(right_root),
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.startswith("## CLI Preview\n")
    assert "### Explicit Comparisons" in result.stdout


def test_build_comment_markdown_supports_latest_live_pair(tmp_path):
    module = _load_post_module()
    helper = _load_report_test_helpers()

    run_a = "20260423_120000__stage4-supervised__target-ep15__aaaa1111"
    run_b = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    helper._write_record(tmp_path, run_id=run_a, status="interrupted")
    helper._write_record(tmp_path, run_id=run_b, status="completed")

    markdown = module.build_comment_markdown(
        title="Preview Snapshot",
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
        latest_live_pair=True,
    )

    assert "### Explicit Comparisons" in markdown
    assert (
        f"- {run_a} -> {run_b}: status=clean; ci_gate=pass; gate_basis=clean; "
        "headline=no remediation needed; verdict=better; changed_sections=run_meta,stage_metrics,watchpoints"
    ) in markdown


def test_post_benchmark_operator_comment_cli_issue_5_defaults_posts_without_repo_args(tmp_path):
    helper = _load_report_test_helpers()
    run_a = "20260423_120000__stage4-supervised__target-ep15__aaaa1111"
    run_b = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    helper._write_record(tmp_path, run_id=run_a, status="interrupted")
    helper._write_record(tmp_path, run_id=run_b, status="completed")
    fake_gh = tmp_path / "gh.cmd"
    log_path = tmp_path / "gh-args.txt"
    fake_gh.write_text(
        "\n".join(
            [
                "@echo off",
                "setlocal EnableDelayedExpansion",
                f"set LOG={log_path}",
                "break>\"%LOG%\"",
                ":loop",
                "if \"%~1\"==\"\" goto afterargs",
                ">>\"%LOG%\" echo %~1",
                "shift",
                "goto loop",
                ":afterargs",
                "set /p BODY=",
                ">>\"%LOG%\" echo __BODY__!BODY!",
                "echo https://github.com/example/repo/issues/5#issuecomment-1",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/post_benchmark_operator_comment.py",
            "--workspace-root",
            str(tmp_path),
            "--benchmark-root",
            "benchmarks",
            "--latest-live-pair",
            "--issue-5-defaults",
            "--post",
            "--gh-path",
            str(fake_gh),
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=True,
    )

    log_lines = log_path.read_text(encoding="utf-8").splitlines()
    assert result.stdout.strip() == "https://github.com/example/repo/issues/5#issuecomment-1"
    assert log_lines[:6] == [
        "issue",
        "comment",
        "5",
        "--repo",
        "temppppppppppppppppppppppp/devdev",
        "--body-file",
    ]
    assert log_lines[6] == "-"
    assert any(line.startswith("__BODY__## Issue #5 Benchmark Operator Snapshot") for line in log_lines)


def test_post_benchmark_operator_comment_cli_issue_5_snapshot_posts_with_shortcut(tmp_path):
    helper = _load_report_test_helpers()
    run_a = "20260423_120000__stage4-supervised__target-ep15__aaaa1111"
    run_b = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    helper._write_record(tmp_path, run_id=run_a, status="interrupted")
    helper._write_record(tmp_path, run_id=run_b, status="completed")
    fake_gh = tmp_path / "gh.cmd"
    log_path = tmp_path / "gh-args.txt"
    fake_gh.write_text(
        "\n".join(
            [
                "@echo off",
                "setlocal EnableDelayedExpansion",
                f"set LOG={log_path}",
                "break>\"%LOG%\"",
                ":loop",
                "if \"%~1\"==\"\" goto afterargs",
                ">>\"%LOG%\" echo %~1",
                "shift",
                "goto loop",
                ":afterargs",
                "set /p BODY=",
                ">>\"%LOG%\" echo __BODY__!BODY!",
                "echo https://github.com/example/repo/issues/5#issuecomment-2",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/post_benchmark_operator_comment.py",
            "--workspace-root",
            str(tmp_path),
            "--benchmark-root",
            "benchmarks",
            "--issue-5-snapshot",
            "--post",
            "--gh-path",
            str(fake_gh),
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=True,
    )

    log_lines = log_path.read_text(encoding="utf-8").splitlines()
    assert result.stdout.strip() == "https://github.com/example/repo/issues/5#issuecomment-2"
    assert log_lines[:6] == [
        "issue",
        "comment",
        "5",
        "--repo",
        "temppppppppppppppppppppppp/devdev",
        "--body-file",
    ]
