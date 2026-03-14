from __future__ import annotations

from pathlib import Path

from scripts import run_pytest_lowmem


def test_classify_targets_collects_batchable_paths(tmp_path: Path) -> None:
    tests_dir = tmp_path / "tests"
    nested = tests_dir / "nested"
    nested.mkdir(parents=True)
    (tests_dir / "test_a.py").write_text("def test_a():\n    assert True\n", encoding="utf-8")
    (nested / "test_b.py").write_text("def test_b():\n    assert True\n", encoding="utf-8")
    (nested / "helper.py").write_text("x = 1\n", encoding="utf-8")

    plan = run_pytest_lowmem.classify_targets([str(tests_dir)])

    assert plan.direct_targets == ()
    assert plan.batchable_paths == (
        (tests_dir / "nested" / "test_b.py").resolve(),
        (tests_dir / "test_a.py").resolve(),
    )


def test_classify_targets_marks_nodeids_direct() -> None:
    plan = run_pytest_lowmem.classify_targets(["tests/test_logger.py::test_root_bootstrap_log_survives"])

    assert plan.requires_direct_run is True
    assert plan.batchable_paths == ()
    assert plan.direct_targets == ("tests/test_logger.py::test_root_bootstrap_log_survives",)


def test_chunk_items_respects_chunk_size(tmp_path: Path) -> None:
    items = tuple((tmp_path / f"test_{index}.py") for index in range(5))

    shards = run_pytest_lowmem.chunk_items(items, 2)

    assert shards == [
        items[0:2],
        items[2:4],
        items[4:5],
    ]


def test_build_pytest_command_uses_low_memory_defaults(tmp_path: Path) -> None:
    command = run_pytest_lowmem.build_pytest_command(
        shard=(tmp_path / "tests" / "test_sample.py",),
        capture="no",
        tb="short",
        basetemp=tmp_path / "basetemp",
        disable_cacheprovider=True,
        pytest_args=("-k=logger",),
    )

    assert command[:4] == [run_pytest_lowmem.sys.executable, "-m", "pytest", "-q"]
    assert "--capture=no" in command
    assert "--tb=short" in command
    assert "console_output_style=count" in command
    assert ["-p", "no:cacheprovider"] == command[command.index("-p") : command.index("-p") + 2]
    assert "-k=logger" in command
    assert str(tmp_path / "tests" / "test_sample.py") in command


def test_build_direct_command_preserves_raw_targets(tmp_path: Path) -> None:
    command = run_pytest_lowmem.build_direct_command(
        raw_targets=("tests/test_logger.py::test_root_bootstrap_log_survives",),
        capture="fd",
        tb="long",
        basetemp=tmp_path / "basetemp",
        disable_cacheprovider=False,
        pytest_args=(),
    )

    assert "--capture=fd" in command
    assert "--tb=long" in command
    assert "tests/test_logger.py::test_root_bootstrap_log_survives" == command[-1]


def test_wait_for_memory_headroom_returns_immediately_under_threshold(tmp_path: Path) -> None:
    guard = run_pytest_lowmem.MemoryGuardConfig(
        pause_threshold_percent=90.0,
        resume_threshold_percent=82.0,
        poll_seconds=0.01,
    )

    result = run_pytest_lowmem.wait_for_memory_headroom(
        guard=guard,
        log_dir=tmp_path,
        shard_label="shard_001",
        memory_percent_getter=lambda: 74.0,
        sleep_fn=lambda _: None,
    )

    assert result == run_pytest_lowmem.MemoryWaitResult(
        paused=False,
        initial_percent=74.0,
        resumed_percent=74.0,
        wait_cycles=0,
    )
    assert not (tmp_path / "memory_watchdog.log").exists()


def test_wait_for_memory_headroom_pauses_until_resume_threshold(tmp_path: Path) -> None:
    readings = iter([93.0, 91.0, 84.0, 81.5])
    sleep_calls: list[float] = []
    guard = run_pytest_lowmem.MemoryGuardConfig(
        pause_threshold_percent=90.0,
        resume_threshold_percent=82.0,
        poll_seconds=0.5,
    )

    result = run_pytest_lowmem.wait_for_memory_headroom(
        guard=guard,
        log_dir=tmp_path,
        shard_label="shard_002",
        memory_percent_getter=lambda: next(readings),
        sleep_fn=sleep_calls.append,
    )

    assert result.paused is True
    assert result.initial_percent == 93.0
    assert result.resumed_percent == 81.5
    assert result.wait_cycles == 3
    assert sleep_calls == [0.5, 0.5, 0.5]
    log_text = (tmp_path / "memory_watchdog.log").read_text(encoding="utf-8")
    assert "shard_002 pause-start memory=93.00%" in log_text
    assert "shard_002 pause-end memory=81.50% cycles=3" in log_text


def test_render_summary_includes_memory_wait(tmp_path: Path) -> None:
    result = run_pytest_lowmem.ShardResult(
        shard_label="shard_001",
        returncode=0,
        stdout_log=tmp_path / "stdout.log",
        stderr_log=tmp_path / "stderr.log",
        command=("python", "-m", "pytest"),
        memory_wait=run_pytest_lowmem.MemoryWaitResult(
            paused=True,
            initial_percent=91.0,
            resumed_percent=80.5,
            wait_cycles=2,
        ),
    )

    summary = run_pytest_lowmem.render_summary([result], tmp_path)

    assert "memory_wait: paused=true initial=91.00% resumed=80.50% cycles=2" in summary
