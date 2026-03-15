from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.investment_corpus_support import (  # noqa: E402
    DEFAULT_STYLE_CONTROL_GENRE,
    DEFAULT_USD_KRW_RATE,
    GEMINI_SUPERVISED_TUNING_USD_PER_MILLION_TOKENS,
    STYLE_CONTROL_SYSTEM_INSTRUCTION,
    build_style_control_dataset,
    dump_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a control-conditioned Gemini JSONL dataset for one title.",
    )
    parser.add_argument(
        "--input-root",
        default="data/investment_corpus_pseudo",
        help="Corpus root containing manifest.json and titles/<slug>/*.txt",
    )
    parser.add_argument("--title", required=True, help="Exact title name inside corpus manifest.")
    parser.add_argument(
        "--output-root",
        default=None,
        help="Optional output root. Defaults to <input-root>/style_control/<slug>",
    )
    parser.add_argument("--genre", default=DEFAULT_STYLE_CONTROL_GENRE, help="Genre control string.")
    parser.add_argument(
        "--system-instruction",
        default=STYLE_CONTROL_SYSTEM_INSTRUCTION,
        help="System instruction used in the JSONL records.",
    )
    parser.add_argument(
        "--holdout-fraction",
        type=float,
        default=0.15,
        help="Deterministic episode-level holdout ratio for validation.",
    )
    parser.add_argument("--body-anchor-tokens", type=int, default=220, help="Opening anchor size for body examples.")
    parser.add_argument(
        "--body-completion-tokens",
        type=int,
        default=900,
        help="Middle-section completion window size.",
    )
    parser.add_argument(
        "--ending-prompt-tokens",
        type=int,
        default=220,
        help="Tail prompt size for ending examples.",
    )
    parser.add_argument(
        "--ending-completion-tokens",
        type=int,
        default=700,
        help="Ending completion window size.",
    )
    parser.add_argument(
        "--usd-per-million-tokens",
        type=float,
        default=GEMINI_SUPERVISED_TUNING_USD_PER_MILLION_TOKENS,
        help="Training pricing assumption in USD per 1M tokens.",
    )
    parser.add_argument(
        "--usd-krw-rate",
        type=float,
        default=DEFAULT_USD_KRW_RATE,
        help="USD/KRW assumption used for local cost estimation.",
    )
    return parser.parse_args()


def _default_output_root(input_root: Path, title: str) -> Path:
    slug = (
        title.replace(" ", "_").replace("/", "_").replace("\\", "_").replace("!", "").replace("?", "").replace(",", "")
    )
    return input_root / "style_control" / slug


def main() -> int:
    args = parse_args()
    input_root = Path(args.input_root)
    output_root = Path(args.output_root) if args.output_root else _default_output_root(input_root, args.title)
    manifest = build_style_control_dataset(
        input_root=input_root,
        title=args.title,
        output_root=output_root,
        genre=args.genre,
        system_instruction=args.system_instruction,
        holdout_fraction=args.holdout_fraction,
        body_anchor_tokens=args.body_anchor_tokens,
        body_completion_tokens=args.body_completion_tokens,
        ending_prompt_tokens=args.ending_prompt_tokens,
        ending_completion_tokens=args.ending_completion_tokens,
        usd_per_million_tokens=args.usd_per_million_tokens,
        usd_krw_rate=args.usd_krw_rate,
    )
    print(dump_json(manifest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
