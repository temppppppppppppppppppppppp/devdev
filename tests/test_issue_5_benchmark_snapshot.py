import importlib.util
import json
import subprocess
import sys
from pathlib import Path


def _load_issue_5_snapshot_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "issue_5_benchmark_snapshot.py"
    spec = importlib.util.spec_from_file_location("issue_5_benchmark_snapshot", script_path)
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


def _write_fake_gh(tmp_path: Path, *, log_path: Path, stdout_url: str) -> Path:
    if sys.platform == "win32":
        fake_gh = tmp_path / "gh.cmd"
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
                    f"echo {stdout_url}",
                ]
            ),
            encoding="utf-8",
        )
        return fake_gh

    fake_gh = tmp_path / "gh"
    fake_gh.write_text(
        "\n".join(
            [
                "#!/usr/bin/env sh",
                f"LOG={log_path}",
                ": > \"$LOG\"",
                "for arg in \"$@\"; do",
                "  printf '%s\\n' \"$arg\" >> \"$LOG\"",
                "done",
                "body=$(cat)",
                "printf '__BODY__%s\\n' \"$body\" >> \"$LOG\"",
                f"printf '%s\\n' '{stdout_url}'",
            ]
        ),
        encoding="utf-8",
    )
    fake_gh.chmod(0o755)
    return fake_gh


def test_build_issue_5_snapshot_payload_uses_latest_live_pair(tmp_path):
    module = _load_issue_5_snapshot_module()
    helper = _load_report_test_helpers()
    run_a = "20260423_120000__stage4-supervised__target-ep15__aaaa1111"
    run_b = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    helper._write_record(tmp_path, run_id=run_a, status="interrupted")
    helper._write_record(tmp_path, run_id=run_b, status="completed")

    payload = module.build_issue_5_snapshot_payload(
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
    )

    assert payload["compare_report_lines"] == [
        {
            "label": f"{run_a} -> {run_b}",
            "left_run_id": run_a,
            "right_run_id": run_b,
            "verdict": "better",
            "changed_sections": ["run_meta", "stage_metrics", "watchpoints"],
            "operator_report_line": (
                "status=clean; ci_gate=pass; gate_basis=clean; headline=no remediation needed"
            ),
        }
    ]


def test_issue_5_benchmark_snapshot_cli_defaults_to_markdown_preview(tmp_path):
    helper = _load_report_test_helpers()
    run_a = "20260423_120000__stage4-supervised__target-ep15__aaaa1111"
    run_b = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    helper._write_record(tmp_path, run_id=run_a, status="interrupted")
    helper._write_record(tmp_path, run_id=run_b, status="completed")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/issue_5_benchmark_snapshot.py",
            "--workspace-root",
            str(tmp_path),
            "--benchmark-root",
            "benchmarks",
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.startswith("## Issue #5 Benchmark Operator Snapshot\n")
    assert (
        f"- {run_a} -> {run_b}: status=clean; ci_gate=pass; gate_basis=clean; "
        "headline=no remediation needed; verdict=better; changed_sections=run_meta,stage_metrics,watchpoints"
    ) in result.stdout


def test_issue_5_benchmark_snapshot_cli_supports_report_json(tmp_path):
    helper = _load_report_test_helpers()
    run_a = "20260423_120000__stage4-supervised__target-ep15__aaaa1111"
    run_b = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    helper._write_record(tmp_path, run_id=run_a, status="interrupted")
    helper._write_record(tmp_path, run_id=run_b, status="completed")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/issue_5_benchmark_snapshot.py",
            "--workspace-root",
            str(tmp_path),
            "--benchmark-root",
            "benchmarks",
            "--report",
            "--format",
            "json",
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["compare_report_lines"] == [
        {
            "label": f"{run_a} -> {run_b}",
            "left_run_id": run_a,
            "right_run_id": run_b,
            "verdict": "better",
            "changed_sections": ["run_meta", "stage_metrics", "watchpoints"],
            "operator_report_line": (
                "status=clean; ci_gate=pass; gate_basis=clean; headline=no remediation needed"
            ),
        }
    ]


def test_issue_5_benchmark_snapshot_cli_posts_to_issue_5_shortcut(tmp_path):
    helper = _load_report_test_helpers()
    run_a = "20260423_120000__stage4-supervised__target-ep15__aaaa1111"
    run_b = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    helper._write_record(tmp_path, run_id=run_a, status="interrupted")
    helper._write_record(tmp_path, run_id=run_b, status="completed")
    log_path = tmp_path / "gh-args.txt"
    fake_gh = _write_fake_gh(
        tmp_path,
        log_path=log_path,
        stdout_url="https://github.com/example/repo/issues/5#issuecomment-3",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/issue_5_benchmark_snapshot.py",
            "--workspace-root",
            str(tmp_path),
            "--benchmark-root",
            "benchmarks",
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
    assert result.stdout.strip() == "https://github.com/example/repo/issues/5#issuecomment-3"
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
