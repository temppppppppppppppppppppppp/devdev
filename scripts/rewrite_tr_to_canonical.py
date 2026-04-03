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

from modules.core.stage0_handoff import canonicalize_treatment_payload as shared_canonicalize_treatment_payload


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def canonicalize_treatment_payload(treatment: Any) -> tuple[dict[str, Any], list[str]]:
    return shared_canonicalize_treatment_payload(treatment)


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
    in_place: bool,
    output_dir: Path | None,
    suffix: str,
) -> dict[str, Any]:
    original = load_json(input_path)
    payload, warnings = canonicalize_treatment_payload(original)
    output_path = derive_output_path(input_path, in_place=in_place, output_dir=output_dir, suffix=suffix)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "input": str(input_path),
        "output": str(output_path),
        "block_count": payload["_total_blocks"],
        "warnings": warnings,
        "in_place": in_place,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rewrite legacy TR JSON files into canonical tr.v1 payloads.")
    parser.add_argument("inputs", nargs="+", type=Path, help="Input TR JSON file(s)")
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
                f"(blocks={result['block_count']}, warnings={warn_count})"
            )
            if result["warnings"]:
                print(f"       warnings: {' | '.join(result['warnings'])}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
