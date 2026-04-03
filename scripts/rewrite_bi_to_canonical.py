#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.core.response_schemas import validate_bible_canonical_structure
from modules.core.stage0_handoff import normalize_bible_to_canonical_view


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def canonicalize_bible_payload(bible: Any, *, treatment: Any | None = None) -> tuple[dict[str, Any], list[str]]:
    payload, warnings = normalize_bible_to_canonical_view(bible, treatment=treatment)
    master = payload.get("MasterBible")
    if isinstance(master, dict):
        if "plot_roadmap" in payload and isinstance(master.get("plot_roadmap"), list):
            payload.pop("plot_roadmap", None)
            warnings.append("removed root-level plot_roadmap sidecar from canonical BI copy")

        project_data = master.get("ProjectData")
        if isinstance(project_data, dict) and "protagonist_config" in project_data and isinstance(master.get("protagonist_config"), dict):
            project_data.pop("protagonist_config", None)
            warnings.append("removed ProjectData.protagonist_config sidecar from canonical BI copy")

    valid, errors, _warnings = validate_bible_canonical_structure(payload)
    if not valid:
        raise ValueError(f"canonical BI validation failed: {errors}")
    return payload, warnings


def derive_output_path(
    input_path: Path,
    *,
    in_place: bool,
    output_dir: Path | None,
    suffix: str,
) -> Path:
    if in_place:
        return input_path
    target_dir = output_dir or input_path.parent
    return target_dir / f"{input_path.stem}{suffix}{input_path.suffix}"


def rewrite_file(
    input_path: Path,
    *,
    treatment_path: Path | None,
    in_place: bool,
    output_dir: Path | None,
    suffix: str,
) -> dict[str, Any]:
    original = load_json(input_path)
    treatment = load_json(treatment_path) if treatment_path else None
    payload, warnings = canonicalize_bible_payload(original, treatment=treatment)
    output_path = derive_output_path(input_path, in_place=in_place, output_dir=output_dir, suffix=suffix)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "input": str(input_path),
        "output": str(output_path),
        "treatment": str(treatment_path) if treatment_path else None,
        "warnings": warnings,
        "in_place": in_place,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rewrite legacy BI JSON files into canonical BI payloads.")
    parser.add_argument("inputs", nargs="+", type=Path, help="Input BI JSON file(s)")
    parser.add_argument("--treatment", type=Path, help="Optional TR JSON used to project plot_roadmap")
    parser.add_argument("--in-place", action="store_true", help="Rewrite each file in place")
    parser.add_argument("--output-dir", type=Path, help="Destination directory for rewritten copies")
    parser.add_argument(
        "--suffix",
        default="_canonical_v1",
        help="Suffix for copied files when not using --in-place",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON summary")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    results = [
        rewrite_file(
            input_path=input_path,
            treatment_path=args.treatment,
            in_place=args.in_place,
            output_dir=args.output_dir,
            suffix=args.suffix,
        )
        for input_path in args.inputs
    ]

    if args.json:
        print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    else:
        for result in results:
            warn_count = len(result["warnings"])
            print(
                f"[OK] {result['input']} -> {result['output']} "
                f"(warnings={warn_count}, treatment={result['treatment'] or 'none'})"
            )
            if result["warnings"]:
                print(f"       warnings: {' | '.join(result['warnings'])}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
