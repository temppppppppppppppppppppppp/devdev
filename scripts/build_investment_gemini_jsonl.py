from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.investment_corpus_support import DEFAULT_SYSTEM_INSTRUCTION, build_gemini_dataset, dump_json  # noqa: E402


def _legacy_char_to_token_count(value: int | None, *, fallback: int) -> int:
    if value is None:
        return fallback
    return max(1, round(value / 2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Gemini supervised-tuning JSONL from extracted investment txt.")
    parser.add_argument(
        "--input-root",
        default="data/investment_corpus",
        help="Corpus root that already contains manifest.json and titles/<slug>/*.txt",
    )
    parser.add_argument(
        "--system-instruction",
        default=DEFAULT_SYSTEM_INSTRUCTION,
        help="Short fixed system instruction for continuation-style supervised tuning.",
    )
    parser.add_argument("--holdout-fraction", type=float, default=0.15, help="Deterministic title-level holdout ratio.")
    parser.add_argument("--prompt-tokens", type=int, default=1200, help="Approximate prompt window size in tokens.")
    parser.add_argument(
        "--completion-tokens",
        type=int,
        default=1200,
        help="Approximate completion window size in tokens.",
    )
    parser.add_argument("--stride-tokens", type=int, default=600, help="Stride between local continuation windows.")
    parser.add_argument(
        "--bridge-prompt-tokens",
        type=int,
        default=800,
        help="Approximate prompt tail size for cross-episode bridge examples.",
    )
    parser.add_argument(
        "--bridge-completion-tokens",
        type=int,
        default=1000,
        help="Approximate completion head size for cross-episode bridge examples.",
    )
    parser.add_argument(
        "--no-bridge-examples",
        action="store_true",
        help="Disable cross-episode bridge examples and keep only local continuation windows.",
    )
    parser.add_argument("--prompt-chars", type=int, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--completion-chars", type=int, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--stride-chars", type=int, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--bridge-prompt-chars", type=int, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--bridge-completion-chars", type=int, default=None, help=argparse.SUPPRESS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = build_gemini_dataset(
        input_root=Path(args.input_root),
        system_instruction=args.system_instruction,
        holdout_fraction=args.holdout_fraction,
        prompt_tokens=_legacy_char_to_token_count(args.prompt_chars, fallback=args.prompt_tokens),
        completion_tokens=_legacy_char_to_token_count(args.completion_chars, fallback=args.completion_tokens),
        stride_tokens=_legacy_char_to_token_count(args.stride_chars, fallback=args.stride_tokens),
        bridge_prompt_tokens=_legacy_char_to_token_count(
            args.bridge_prompt_chars,
            fallback=args.bridge_prompt_tokens,
        ),
        bridge_completion_tokens=_legacy_char_to_token_count(
            args.bridge_completion_chars,
            fallback=args.bridge_completion_tokens,
        ),
        include_bridge_examples=not args.no_bridge_examples,
    )
    print(dump_json(manifest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
