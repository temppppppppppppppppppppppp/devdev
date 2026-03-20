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


def build_command(*, audit_script: str, phase0: Path, draft: Path, bi: Path, report: Path) -> list[str]:
    return [
        sys.executable,
        "-X",
        "utf8",
        str(ROOT / audit_script),
        "--phase0",
        str(phase0),
        "--draft",
        str(draft),
        "--bi",
        str(bi),
        "--report",
        str(report),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Route BI audit through the narrative family contract.")
    parser.add_argument("--phase0", type=Path, required=True, help="Phase0 design JSON path")
    parser.add_argument("--draft", type=Path, required=True, help="Treatment draft JSON path")
    parser.add_argument("--bi", type=Path, required=True, help="Bible JSON path")
    parser.add_argument("--report", type=Path, required=True, help="Markdown report output path")
    parser.add_argument("--genre", help="Genre label such as wuxia, investment, alt_history")
    parser.add_argument("--family", help="Explicit family override such as blockguide or wuxguide")
    parser.add_argument("--dry-run", action="store_true", help="Print the resolved audit command without running it")
    parser.add_argument("--json", action="store_true", help="Print dry-run details as JSON")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    family = resolve_family_plugin(genre=args.genre, family_hint=args.family)
    route = resolve_route(genre=args.genre, family_hint=args.family)
    command = build_command(
        audit_script=family.contract.bi.audit_script,
        phase0=args.phase0,
        draft=args.draft,
        bi=args.bi,
        report=args.report,
    )

    if args.dry_run or args.json:
        payload = {
            "family": family.key,
            "hud_root": family.contract.bi.hud_root,
            "audit_script": family.contract.bi.audit_script,
            "required_master_sections": list(family.contract.bi.required_master_sections),
            "route": route.to_dict(),
            "command": command,
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"family: {payload['family']}")
            print(f"hud_root: {payload['hud_root']}")
            print(f"audit: {payload['audit_script']}")
            print(f"command: {' '.join(command)}")
        return 0

    result = subprocess.run(command, check=False)
    return int(result.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
