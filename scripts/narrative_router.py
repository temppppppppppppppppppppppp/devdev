from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.narrative_router import resolve_route
from modules.narrative_router.families import get_builtin_families


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Resolve narrative family routing without touching family-specific harnesses.")
    parser.add_argument("--genre", help="Genre label such as wuxia, 무협, hunter, investment, alt_history.")
    parser.add_argument("--family", help="Explicit family hint such as blockguide or wuxguide.")
    parser.add_argument("--work-id", help="Canonical work_id for filesystem-based stage detection.")
    parser.add_argument("--phase0-exists", action="store_true", help="Treat phase0_design as already existing.")
    parser.add_argument("--tr-exists", action="store_true", help="Treat tr_block_070_draft as already existing.")
    parser.add_argument("--bi-exists", action="store_true", help="Treat BI JSON as already existing.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument("--list-families", action="store_true", help="List built-in family plugins.")
    return parser


def _print_families(as_json: bool) -> int:
    payload = [
        {
            "family": family.key,
            "display_name": family.display_name,
            "description": family.description,
            "integrated_order_path": family.integrated_order_path,
            "planning_required_preprocess_files": family.contract.planning.required_preprocess_files,
            "planning_readiness_flag_file": family.contract.planning.readiness_flag_file,
            "phase0_output_pattern": family.contract.planning.phase0_output_pattern,
            "tr_harness_script": family.contract.tr.harness_script,
            "hud_root": family.contract.bi.hud_root,
            "bi_builder_script": family.contract.bi.builder_script,
            "bi_audit_script": family.contract.bi.audit_script,
        }
        for family in get_builtin_families()
    ]
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    for item in payload:
        print(f"{item['family']}: {item['display_name']}")
        print(f"  - {item['description']}")
        print(f"  - {item['integrated_order_path']}")
        print(f"  - preprocess_required: {', '.join(item['planning_required_preprocess_files'])}")
        print(f"  - readiness_flag: {item['planning_readiness_flag_file']}")
        print(f"  - phase0_output: {item['phase0_output_pattern']}")
        print(f"  - tr_harness: {item['tr_harness_script']}")
        print(f"  - hud_root: {item['hud_root']}")
        print(f"  - bi_builder: {item['bi_builder_script']}")
        print(f"  - bi_audit: {item['bi_audit_script']}")
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.list_families:
        return _print_families(args.json)

    route = resolve_route(
        genre=args.genre,
        family_hint=args.family,
        work_id=args.work_id,
        phase0_exists=args.phase0_exists,
        tr_exists=args.tr_exists,
        bi_exists=args.bi_exists,
    )

    if args.json:
        print(json.dumps(route.to_dict(), ensure_ascii=False, indent=2))
        return 0

    print(f"family: {route.family}")
    print(f"display_name: {route.display_name}")
    if route.stage:
        print(f"stage: {route.stage}")
    print(f"integrated_order: {route.integrated_order_path}")
    print(f"planning: {route.planning_path}")
    print(f"production: {route.production_path}")
    print(f"bi: {route.bi_path}")
    print(f"preprocess_required: {', '.join(route.contract.planning.required_preprocess_files)}")
    print(f"readiness_flag: {route.contract.planning.readiness_flag_file}")
    print(f"phase0_output: {route.contract.planning.phase0_output_pattern}")
    print(f"tr_harness: {route.contract.tr.harness_script}")
    print(f"hud_root: {route.contract.bi.hud_root}")
    print(f"bi_builder: {route.contract.bi.builder_script}")
    print(f"bi_audit: {route.contract.bi.audit_script}")
    if route.artifact_state:
        print(f"work_id: {route.artifact_state.work_id}")
        print(f"preprocess_ready: {route.artifact_state.preprocess_ready}")
        print(f"manual_audit_pass: {route.artifact_state.manual_audit_pass}")
        print(f"phase0_path: {route.artifact_state.phase0_path}")
        print(f"tr_path: {route.artifact_state.tr_path}")
        print(f"bi_path: {route.artifact_state.bi_path}")
    for extra_path in route.extra_paths:
        print(f"extra: {extra_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
