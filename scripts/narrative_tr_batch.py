#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.narrative_router import resolve_family_plugin, resolve_route


def build_command(*, harness_script: str, passthrough: list[str]) -> list[str]:
    return [
        sys.executable,
        "-X",
        "utf8",
        str(ROOT / harness_script),
        *passthrough,
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Route TR batch prompt/check/merge commands through the narrative family contract."
    )
    parser.add_argument("--genre", help="Genre label such as wuxia, investment, alt_history")
    parser.add_argument("--family", help="Explicit family override such as blockguide or wuxguide")
    parser.add_argument("--dry-run", action="store_true", help="Print the resolved harness command without running it")
    parser.add_argument("--json", action="store_true", help="Print dry-run details as JSON")
    return parser


def main() -> int:
    parser = build_parser()
    args, passthrough = parser.parse_known_args()

    family = resolve_family_plugin(genre=args.genre, family_hint=args.family)
    route = resolve_route(genre=args.genre, family_hint=args.family)
    harness_script = family.contract.tr.harness_script
    if not harness_script:
        raise SystemExit(f"Family '{family.key}' does not define a TR harness script yet.")

    command = build_command(harness_script=harness_script, passthrough=passthrough)

    if args.dry_run or args.json:
        payload = {
            "family": family.key,
            "tr_harness_script": harness_script,
            "continuity_profile": family.contract.tr.continuity_profile,
            "canonical_axes": list(family.contract.tr.canonical_axes),
            "route": route.to_dict(),
            "command": command,
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"family: {payload['family']}")
            print(f"tr_harness: {payload['tr_harness_script']}")
            print(f"continuity_profile: {payload['continuity_profile']}")
            print(f"canonical_axes: {', '.join(payload['canonical_axes'])}")
            print(f"command: {' '.join(command)}")
        return 0

    result = subprocess.run(command, check=False)
    return int(result.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
