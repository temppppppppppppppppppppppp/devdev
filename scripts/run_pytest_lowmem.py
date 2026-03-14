"""Run pytest in small shards to trade runtime for lower peak memory."""

from __future__ import annotations

import argparse
import ctypes
import os
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGETS = ("tests",)
DEFAULT_CHUNK_SIZE = 12
DEFAULT_MEMORY_PAUSE_THRESHOLD = 90.0
DEFAULT_MEMORY_RESUME_THRESHOLD = 82.0
DEFAULT_MEMORY_POLL_SECONDS = 10.0


@dataclass(frozen=True)
class TargetPlan:
    batchable_paths: tuple[Path, ...]
    direct_targets: tuple[str, ...]

    @property
    def requires_direct_run(self) -> bool:
        return bool(self.direct_targets)


@dataclass(frozen=True)
class MemoryGuardConfig:
    pause_threshold_percent: float
    resume_threshold_percent: float
    poll_seconds: float


@dataclass(frozen=True)
class MemoryWaitResult:
    paused: bool
    initial_percent: float
    resumed_percent: float
    wait_cycles: int


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Low-memory pytest shard runner")
    parser.add_argument("targets", nargs="*", default=list(DEFAULT_TARGETS))
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--log-dir", default="")
    parser.add_argument("--keep-going", action="store_true")
    parser.add_argument("--capture", choices=("no", "fd", "sys"), default="no")
    parser.add_argument("--tb", default="short")
    parser.add_argument(
        "--disable-cacheprovider",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--disable-plugin-autoload",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    parser.add_argument(
        "--pytest-arg",
        dest="pytest_args",
        action="append",
        default=[],
        help="extra pytest arg, repeat as needed",
    )
    parser.add_argument(
        "--memory-pause-threshold-percent",
        type=float,
        default=DEFAULT_MEMORY_PAUSE_THRESHOLD,
    )
    parser.add_argument(
        "--memory-resume-threshold-percent",
        type=float,
        default=DEFAULT_MEMORY_RESUME_THRESHOLD,
    )
    parser.add_argument(
        "--memory-poll-seconds",
        type=float,
        default=DEFAULT_MEMORY_POLL_SECONDS,
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    log_dir = resolve_log_dir(args.log_dir)
    plan = classify_targets(args.targets)
    pytest_args = tuple(args.pytest_args)
    memory_guard = MemoryGuardConfig(
        pause_threshold_percent=float(args.memory_pause_threshold_percent),
        resume_threshold_percent=float(args.memory_resume_threshold_percent),
        poll_seconds=max(0.1, float(args.memory_poll_seconds)),
    )

    if plan.requires_direct_run:
        direct_memory_wait = wait_for_memory_headroom(
            guard=memory_guard,
            log_dir=log_dir,
            shard_label="direct",
        )
        command = build_direct_command(
            raw_targets=args.targets,
            capture=args.capture,
            tb=args.tb,
            basetemp=log_dir / "basetemp" / "direct",
            disable_cacheprovider=args.disable_cacheprovider,
            pytest_args=pytest_args,
        )
        result = run_shard(
            shard_label="direct",
            command=command,
            log_dir=log_dir,
            disable_plugin_autoload=args.disable_plugin_autoload,
            memory_wait=direct_memory_wait,
        )
        print(render_summary([result], log_dir))
        return result.returncode

    shard_results: list[ShardResult] = []
    for index, shard in enumerate(chunk_items(plan.batchable_paths, max(1, int(args.chunk_size))), start=1):
        memory_wait = wait_for_memory_headroom(
            guard=memory_guard,
            log_dir=log_dir,
            shard_label=f"shard_{index:03d}",
        )
        basetemp = log_dir / "basetemp" / f"shard_{index:03d}"
        command = build_pytest_command(
            shard=shard,
            capture=args.capture,
            tb=args.tb,
            basetemp=basetemp,
            disable_cacheprovider=args.disable_cacheprovider,
            pytest_args=pytest_args,
        )
        result = run_shard(
            shard_label=f"shard_{index:03d}",
            command=command,
            log_dir=log_dir,
            disable_plugin_autoload=args.disable_plugin_autoload,
            memory_wait=memory_wait,
        )
        shard_results.append(result)
        if result.returncode and not args.keep_going:
            break

    print(render_summary(shard_results, log_dir))
    return 0 if all(result.returncode == 0 for result in shard_results) else 1


def resolve_log_dir(raw_log_dir: str) -> Path:
    if raw_log_dir:
        target = Path(raw_log_dir)
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target = PROJECT_ROOT / "logs" / "pytest_lowmem" / stamp
    target.mkdir(parents=True, exist_ok=True)
    return target


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def classify_targets(targets: Iterable[str]) -> TargetPlan:
    batchable: list[Path] = []
    direct: list[str] = []

    for raw_target in targets:
        if "::" in raw_target:
            direct.append(raw_target)
            continue

        candidate = Path(raw_target)
        if not candidate.is_absolute():
            candidate = PROJECT_ROOT / candidate

        if candidate.is_dir():
            batchable.extend(sorted(candidate.rglob("test_*.py")))
            continue

        if candidate.is_file():
            batchable.append(candidate)
            continue

        direct.append(raw_target)

    unique_batchable = tuple(dict.fromkeys(path.resolve() for path in batchable))
    return TargetPlan(batchable_paths=unique_batchable, direct_targets=tuple(direct))


def current_system_memory_percent() -> float:
    if os.name == "nt":
        return current_system_memory_percent_windows()
    return current_system_memory_percent_posix()


def current_system_memory_percent_windows() -> float:
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    memory_status = MEMORYSTATUSEX()
    memory_status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory_status)):
        raise OSError("GlobalMemoryStatusEx failed")
    return float(memory_status.dwMemoryLoad)


def current_system_memory_percent_posix() -> float:
    meminfo = Path("/proc/meminfo")
    if not meminfo.exists():
        raise RuntimeError("system memory query is unavailable on this platform")

    values: dict[str, int] = {}
    for line in meminfo.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) >= 2:
            values[parts[0].rstrip(":")] = int(parts[1])

    total = values.get("MemTotal")
    available = values.get("MemAvailable")
    if not total or available is None:
        raise RuntimeError("MemTotal/MemAvailable missing from /proc/meminfo")
    used_ratio = (total - available) / total
    return round(used_ratio * 100, 2)


def wait_for_memory_headroom(
    *,
    guard: MemoryGuardConfig,
    log_dir: Path,
    shard_label: str,
    memory_percent_getter=current_system_memory_percent,
    sleep_fn=time.sleep,
) -> MemoryWaitResult:
    if guard.resume_threshold_percent > guard.pause_threshold_percent:
        raise ValueError("resume threshold must be <= pause threshold")

    log_path = log_dir / "memory_watchdog.log"
    initial_percent = float(memory_percent_getter())
    if initial_percent < guard.pause_threshold_percent:
        return MemoryWaitResult(
            paused=False,
            initial_percent=initial_percent,
            resumed_percent=initial_percent,
            wait_cycles=0,
        )

    wait_cycles = 0
    _append_memory_watchdog_log(
        log_path,
        (
            f"{_now_iso()} {shard_label} pause-start "
            f"memory={initial_percent:.2f}% threshold={guard.pause_threshold_percent:.2f}%"
        ),
    )
    current_percent = initial_percent
    while current_percent > guard.resume_threshold_percent:
        wait_cycles += 1
        sleep_fn(guard.poll_seconds)
        current_percent = float(memory_percent_getter())
        _append_memory_watchdog_log(
            log_path,
            (
                f"{_now_iso()} {shard_label} pause-wait "
                f"memory={current_percent:.2f}% resume={guard.resume_threshold_percent:.2f}% "
                f"cycle={wait_cycles}"
            ),
        )

    _append_memory_watchdog_log(
        log_path,
        (
            f"{_now_iso()} {shard_label} pause-end "
            f"memory={current_percent:.2f}% cycles={wait_cycles}"
        ),
    )
    return MemoryWaitResult(
        paused=True,
        initial_percent=initial_percent,
        resumed_percent=current_percent,
        wait_cycles=wait_cycles,
    )


def _append_memory_watchdog_log(log_path: Path, line: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"{line}\n")


def chunk_items(items: Iterable[Path], chunk_size: int) -> list[tuple[Path, ...]]:
    shard: list[Path] = []
    shards: list[tuple[Path, ...]] = []
    for item in items:
        shard.append(item)
        if len(shard) >= chunk_size:
            shards.append(tuple(shard))
            shard = []
    if shard:
        shards.append(tuple(shard))
    return shards


def build_pytest_command(
    *,
    shard: Iterable[Path],
    capture: str,
    tb: str,
    basetemp: Path,
    disable_cacheprovider: bool,
    pytest_args: tuple[str, ...],
) -> list[str]:
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        f"--tb={tb}",
        f"--capture={capture}",
        "--color=no",
        "--disable-warnings",
        "-o",
        "console_output_style=count",
        "-o",
        "log_cli=false",
        "--basetemp",
        str(basetemp),
    ]
    if disable_cacheprovider:
        command.extend(["-p", "no:cacheprovider"])
    command.extend(pytest_args)
    command.extend(str(path) for path in shard)
    return command


def build_direct_command(
    *,
    raw_targets: Iterable[str],
    capture: str,
    tb: str,
    basetemp: Path,
    disable_cacheprovider: bool,
    pytest_args: tuple[str, ...],
) -> list[str]:
    command = build_pytest_command(
        shard=(),
        capture=capture,
        tb=tb,
        basetemp=basetemp,
        disable_cacheprovider=disable_cacheprovider,
        pytest_args=pytest_args,
    )
    command.extend(raw_targets)
    return command


@dataclass(frozen=True)
class ShardResult:
    shard_label: str
    returncode: int
    stdout_log: Path
    stderr_log: Path
    command: tuple[str, ...]
    memory_wait: MemoryWaitResult


def run_shard(
    *,
    shard_label: str,
    command: list[str],
    log_dir: Path,
    disable_plugin_autoload: bool,
    memory_wait: MemoryWaitResult,
) -> ShardResult:
    stdout_log = log_dir / f"{shard_label}.stdout.log"
    stderr_log = log_dir / f"{shard_label}.stderr.log"
    basetemp_index = command.index("--basetemp") + 1
    Path(command[basetemp_index]).mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    if disable_plugin_autoload:
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"

    with stdout_log.open("w", encoding="utf-8") as stdout_handle, stderr_log.open(
        "w", encoding="utf-8"
    ) as stderr_handle:
        process = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            env=env,
            stdout=stdout_handle,
            stderr=stderr_handle,
            check=False,
        )

    return ShardResult(
        shard_label=shard_label,
        returncode=process.returncode,
        stdout_log=stdout_log,
        stderr_log=stderr_log,
        command=tuple(command),
        memory_wait=memory_wait,
    )


def render_summary(results: list[ShardResult], log_dir: Path) -> str:
    total = len(results)
    passed = sum(result.returncode == 0 for result in results)
    failed = total - passed
    lines = [
        f"log_dir: {log_dir}",
        f"shards_total: {total}",
        f"shards_passed: {passed}",
        f"shards_failed: {failed}",
    ]
    for result in results:
        lines.append(
            f"{result.shard_label}: rc={result.returncode} stdout={result.stdout_log.name} stderr={result.stderr_log.name}"
        )
        lines.append(
            "  memory_wait: "
            f"paused={str(result.memory_wait.paused).lower()} "
            f"initial={result.memory_wait.initial_percent:.2f}% "
            f"resumed={result.memory_wait.resumed_percent:.2f}% "
            f"cycles={result.memory_wait.wait_cycles}"
        )
        if result.returncode:
            lines.append(f"  command: {shlex.join(result.command)}")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
