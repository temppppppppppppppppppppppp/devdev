from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.investment_corpus_support import build_pseudonymized_corpus, dump_json  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a pseudonymized investment corpus variant for Vertex training.")
    parser.add_argument(
        "--input-root",
        default="data/investment_corpus",
        help="Raw corpus root that already contains manifest.json and titles/<slug>/*.txt",
    )
    parser.add_argument(
        "--output-root",
        default="data/investment_corpus_pseudo",
        help="Output root for the pseudonymized corpus variant.",
    )
    parser.add_argument(
        "--min-person-frequency",
        type=int,
        default=5,
        help="Minimum repeated occurrence count before a person-name candidate is pseudonymized.",
    )
    parser.add_argument(
        "--min-org-frequency",
        type=int,
        default=3,
        help="Minimum repeated occurrence count before an organization-name candidate is pseudonymized.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = build_pseudonymized_corpus(
        input_root=Path(args.input_root),
        output_root=Path(args.output_root),
        min_person_frequency=args.min_person_frequency,
        min_org_frequency=args.min_org_frequency,
    )
    print(dump_json(manifest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
