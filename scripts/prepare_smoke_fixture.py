"""Prepare the bounded smoke fixture target project from the canonical source.

Usage:
    python scripts/prepare_smoke_fixture.py --force
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.smoke_fixture_tools import prepare_smoke_fixture_project  # noqa: E402
from scripts.smoke_fixture_contract import (  # noqa: E402
    BOUND_SMOKE_TARGET_PROJECT,
    CANONICAL_SMOKE_SOURCE_PROJECT,
)


DEFAULT_SOURCE_PROJECT = CANONICAL_SMOKE_SOURCE_PROJECT
DEFAULT_TARGET_PROJECT = BOUND_SMOKE_TARGET_PROJECT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare the bounded smoke fixture target project")
    parser.add_argument("--source-project", default=DEFAULT_SOURCE_PROJECT)
    parser.add_argument("--target-project", default=DEFAULT_TARGET_PROJECT)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_root = PROJECT_ROOT / "projects" / args.source_project
    target_root = PROJECT_ROOT / "projects" / args.target_project
    payload = prepare_smoke_fixture_project(source_root, target_root, force=args.force)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
