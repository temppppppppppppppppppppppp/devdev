#!/usr/bin/env python3
"""Repo-level preflight gate before starting a fresh pitch wave."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REGISTRY_JSON = ROOT / "material_ssot" / "00_governance" / "production-pair-operational-registry-v1.json"


def run_command(label: str, args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        args,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    print(f"[{label}] {'PASS' if proc.returncode == 0 else 'FAIL'}")
    if proc.stdout.strip():
        print(proc.stdout.rstrip())
    if proc.stderr.strip():
        print(proc.stderr.rstrip())
    print()
    return proc.returncode, proc.stdout, proc.stderr


def load_registry() -> dict:
    if not REGISTRY_JSON.is_file():
        return {}
    return json.loads(REGISTRY_JSON.read_text(encoding="utf-8"))


def render_registry_summary() -> bool:
    data = load_registry()
    entries = data.get("pairs")
    if not isinstance(entries, list):
        print("[registry] FAIL")
        print("Operational registry JSON is missing or malformed.")
        print()
        return False

    pending_refresh = [
        entry["work_id"]
        for entry in entries
        if isinstance(entry, dict)
        and entry.get("benchmark_alias")
        and entry.get("benchmark_freshness") == "pending_refresh"
    ]
    unbenchmarked = [
        entry["work_id"]
        for entry in entries
        if isinstance(entry, dict) and entry.get("benchmark_freshness") == "unbenchmarked"
    ]

    print("[registry] PASS")
    print(f"tracked pairs: {len(entries)}")
    print(f"historical aliases pending freshness refresh: {len(pending_refresh)}")
    if pending_refresh:
        print("  - " + ", ".join(pending_refresh))
    print(f"schema-clean but unbenchmarked live pairs: {len(unbenchmarked)}")
    if unbenchmarked:
        print("  - " + ", ".join(unbenchmarked))
    if not pending_refresh and not unbenchmarked:
        print("all tracked pairs carry current benchmark artifacts.")
    print()
    return True


def main() -> int:
    python = sys.executable

    material_code, _, _ = run_command(
        "material_ssot",
        [python, "-X", "utf8", str(ROOT / "scripts" / "validate_material_ssot.py")],
    )
    pair_code, pair_stdout, _ = run_command(
        "pair_normalization",
        [python, "-X", "utf8", str(ROOT / "scripts" / "production_pair_normalization_runner.py")],
    )
    pitch_code, _, _ = run_command(
        "pitch_readiness",
        [python, "-X", "utf8", str(ROOT / "scripts" / "material_readiness_validator.py"), "--path", str(ROOT / "material_ssot" / "20_pitch")],
    )

    registry_ok = render_registry_summary()

    if material_code != 0 or pair_code != 0 or pitch_code != 0 or not registry_ok:
        print("Pre-New-Pitch Readiness Result: FAIL")
        return 1

    if "schema=fail" in pair_stdout:
        print("Pre-New-Pitch Readiness Result: FAIL")
        print("Normalization runner reported at least one non-passing pair.")
        return 1

    print("Pre-New-Pitch Readiness Result: PASS")
    print("Core governance, pair normalization, and pitch readiness gates are all green.")
    print("Use the operational registry for benchmark freshness before citing active pair baselines.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
