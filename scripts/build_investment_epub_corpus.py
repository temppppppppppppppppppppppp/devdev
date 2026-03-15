from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.investment_corpus_support import (  # noqa: E402 - entrypoint path bootstrap must precede imports
    build_corpus,
    dump_json,
    load_title_manifest,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a UTF-8 txt corpus from trusted investment EPUB sources.")
    parser.add_argument(
        "--source-root", required=True, help="NAS or local root that contains [연재] title directories."
    )
    parser.add_argument(
        "--output-root",
        default="data/investment_corpus",
        help="Local output root for txt files, manifest.json, and errors.log.",
    )
    parser.add_argument(
        "--titles-manifest",
        default=str(Path(__file__).with_name("investment_epub_title_manifest.json")),
        help="JSON manifest that locks the candidate title set.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    titles = load_title_manifest(Path(args.titles_manifest))
    manifest = build_corpus(
        source_root=Path(args.source_root),
        output_root=Path(args.output_root),
        titles=titles,
        manifest_path=Path(args.titles_manifest),
    )
    print(dump_json(manifest["summary"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
