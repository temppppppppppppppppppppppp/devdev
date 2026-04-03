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

from modules.narrative_router.router import resolve_family_plugin, resolve_route
from scripts.check_bi_tr_consumability import inspect_pair


def build_command(*, builder_script: str, phase0: Path, draft: Path, output: Path) -> list[str]:
    return [
        sys.executable,
        "-X",
        "utf8",
        str(ROOT / builder_script),
        "--phase0",
        str(phase0),
        "--draft",
        str(draft),
        "--output",
        str(output),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Route BI generation through the narrative family contract.")
    parser.add_argument("--phase0", type=Path, required=True, help="Phase0 design JSON path")
    parser.add_argument("--draft", type=Path, required=True, help="Treatment draft JSON path")
    parser.add_argument("--output", type=Path, required=True, help="Output BI JSON path")
    parser.add_argument("--genre", help="Genre label such as wuxia, investment, alt_history")
    parser.add_argument("--family", help="Explicit family override such as blockguide or wuxguide")
    parser.add_argument("--dry-run", action="store_true", help="Print the resolved builder command without running it")
    parser.add_argument("--json", action="store_true", help="Print dry-run details as JSON")
    return parser


def _preview_messages(messages: list[str], *, limit: int = 2) -> str:
    if not messages:
        return ""
    preview = messages[:limit]
    suffix = f" ... (+{len(messages) - limit} more)" if len(messages) > limit else ""
    return " | ".join(preview) + suffix


def emit_contract_summary(*, draft: Path, output: Path):
    result = inspect_pair(bible_path=output, treatment_path=draft)
    verdicts = result.verdicts
    print(
        "[CHECK] "
        f"pair={verdicts['pair_consumability']} "
        f"| canonical={verdicts['pair_canonical_contract']} "
        f"(tr={verdicts['tr_canonical_contract']}, bi={verdicts['bi_canonical_contract']}) "
        f"| normalized={verdicts['normalized_pair_canonical_view']} "
        f"(tr={verdicts['normalized_tr_canonical_view']}, bi={verdicts['normalized_bi_canonical_view']}) "
        f"| blocks={result.canonical_block_count}"
    )
    if result.bible_canonical_errors:
        print(f"[CHECK] bible_canonical_errors: {_preview_messages(result.bible_canonical_errors)}")
    if result.treatment_canonical_errors:
        print(f"[CHECK] treatment_canonical_errors: {_preview_messages(result.treatment_canonical_errors)}")
    if result.bible_normalization_warnings:
        print(f"[CHECK] bible_normalization: {_preview_messages(result.bible_normalization_warnings)}")
    if result.treatment_normalization_warnings:
        print(f"[CHECK] treatment_normalization: {_preview_messages(result.treatment_normalization_warnings)}")
    return result


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    family = resolve_family_plugin(genre=args.genre, family_hint=args.family)
    route = resolve_route(genre=args.genre, family_hint=args.family)
    command = build_command(
        builder_script=family.contract.bi.builder_script,
        phase0=args.phase0,
        draft=args.draft,
        output=args.output,
    )

    if args.dry_run or args.json:
        payload = {
            "family": family.key,
            "hud_root": family.contract.bi.hud_root,
            "builder_script": family.contract.bi.builder_script,
            "audit_script": family.contract.bi.audit_script,
            "required_phase0_sections": list(family.contract.bi.required_phase0_sections),
            "required_phase0_design_fields": list(family.contract.bi.required_phase0_design_fields),
            "required_master_sections": list(family.contract.bi.required_master_sections),
            "route": route.to_dict(),
            "command": command,
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"family: {payload['family']}")
            print(f"hud_root: {payload['hud_root']}")
            print(f"builder: {payload['builder_script']}")
            print(f"audit: {payload['audit_script']}")
            print(f"command: {' '.join(command)}")
        return 0

    result = subprocess.run(command, check=False)
    exit_code = int(result.returncode)
    if exit_code == 0 and args.output.is_file():
        inspection = emit_contract_summary(draft=args.draft, output=args.output)
        if inspection.verdicts.get("pair_canonical_contract") != "pass":
            print("[ERROR] Routed BI build produced a non-canonical BI/TR pair; refusing success exit.")
            return 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
