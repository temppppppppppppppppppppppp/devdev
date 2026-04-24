#!/usr/bin/env python3
"""Summarize bounded episode corpora to build 2~6 episode bundle density baselines."""

from __future__ import annotations

# utf8-hygiene: allow-file -- legacy density regex patterns use Hangul-adjacent optional tokens.

import argparse
import json
import math
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

UTC = timezone.utc
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

AMOUNT_RE = re.compile(r"\d[\d,.]*\s*(?:억|조|만|원|%|달러|위안|배)?")
ORG_RE = re.compile(
    r"[가-힣A-Za-z0-9]{2,}(?:사|그룹|회사|공장|호텔|병원|은행|연합|센터|재단|증권|캐피탈|인베스트먼트|파트너스|자산운용)"
)
QUOTE_PREFIX_RE = re.compile(r"^[\"'“”‘’「『\-—]")
EPISODE_RE = re.compile(r"(\d+)")


@dataclass(slots=True)
class EpisodeMetrics:
    episode_no: int
    char_count: int
    paragraph_count: int
    sentence_count: int
    quote_paragraph_count: int
    amount_mentions: int
    org_mentions: int
    domain_anchor_mentions: int
    domain_anchor_per_1000_chars: float
    quote_paragraph_ratio: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corpus-dir",
        action="append",
        default=[],
        help="Episode corpus directory containing ep*.txt files. May be passed multiple times.",
    )
    parser.add_argument(
        "--window-sizes",
        default="2,3,4,5,6",
        help="Comma-separated rolling window sizes to summarize.",
    )
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout")
    return parser.parse_args()


def decode_text_file(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp949", "euc-kr"):
        try:
            return raw.decode(encoding).replace("\r\n", "\n").replace("\r", "\n")
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore").replace("\r\n", "\n").replace("\r", "\n")


def parse_episode_no(path: Path) -> int:
    match = EPISODE_RE.search(path.stem)
    if not match:
        raise ValueError(f"episode number missing in filename: {path}")
    return int(match.group(1))


def list_episode_files(corpus_dir: Path) -> list[Path]:
    return sorted(
        [path for path in corpus_dir.rglob("ep*.txt") if path.is_file()],
        key=lambda item: parse_episode_no(item),
    )


def split_paragraphs(text: str) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if paragraphs:
        return paragraphs
    return [line.strip() for line in text.splitlines() if line.strip()]


def count_sentences(text: str) -> int:
    parts = [part.strip() for part in re.split(r"[.!?…]+", text) if part.strip()]
    return len(parts) if parts else 1


def quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return round(float(values[0]), 2)
    ordered = sorted(float(value) for value in values)
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return round(ordered[int(position)], 2)
    low_value = ordered[lower]
    high_value = ordered[upper]
    interpolated = low_value + (high_value - low_value) * (position - lower)
    return round(interpolated, 2)


def average(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def relativize(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except Exception:
        return str(path)


def build_episode_metrics(text: str, *, episode_no: int) -> EpisodeMetrics:
    normalized = text.strip()
    paragraphs = split_paragraphs(normalized)
    quote_paragraph_count = sum(1 for paragraph in paragraphs if QUOTE_PREFIX_RE.match(paragraph))
    amount_mentions = len(AMOUNT_RE.findall(normalized))
    org_mentions = len(ORG_RE.findall(normalized))
    domain_anchor_mentions = amount_mentions + org_mentions
    char_count = len(normalized)
    return EpisodeMetrics(
        episode_no=episode_no,
        char_count=char_count,
        paragraph_count=len(paragraphs),
        sentence_count=count_sentences(normalized),
        quote_paragraph_count=quote_paragraph_count,
        amount_mentions=amount_mentions,
        org_mentions=org_mentions,
        domain_anchor_mentions=domain_anchor_mentions,
        domain_anchor_per_1000_chars=round(domain_anchor_mentions / max(char_count, 1) * 1000, 2),
        quote_paragraph_ratio=round(quote_paragraph_count / max(len(paragraphs), 1), 3),
    )


def summarize_series(metrics: list[EpisodeMetrics]) -> dict[str, Any]:
    if not metrics:
        return {}
    char_counts = [item.char_count for item in metrics]
    paragraph_counts = [item.paragraph_count for item in metrics]
    sentence_counts = [item.sentence_count for item in metrics]
    anchor_densities = [item.domain_anchor_per_1000_chars for item in metrics]
    quote_ratios = [item.quote_paragraph_ratio for item in metrics]
    return {
        "episode_count": len(metrics),
        "episode_span": [metrics[0].episode_no, metrics[-1].episode_no],
        "char_count": {
            "min": min(char_counts),
            "p25": quantile(char_counts, 0.25),
            "p50": quantile(char_counts, 0.5),
            "p75": quantile(char_counts, 0.75),
            "max": max(char_counts),
            "avg": average(char_counts),
        },
        "paragraph_count": {
            "p25": quantile(paragraph_counts, 0.25),
            "p50": quantile(paragraph_counts, 0.5),
            "p75": quantile(paragraph_counts, 0.75),
            "avg": average(paragraph_counts),
        },
        "sentence_count": {
            "p25": quantile(sentence_counts, 0.25),
            "p50": quantile(sentence_counts, 0.5),
            "p75": quantile(sentence_counts, 0.75),
            "avg": average(sentence_counts),
        },
        "domain_anchor_per_1000_chars": {
            "p25": quantile(anchor_densities, 0.25),
            "p50": quantile(anchor_densities, 0.5),
            "p75": quantile(anchor_densities, 0.75),
            "avg": average(anchor_densities),
        },
        "quote_paragraph_ratio": {
            "p25": quantile(quote_ratios, 0.25),
            "p50": quantile(quote_ratios, 0.5),
            "p75": quantile(quote_ratios, 0.75),
            "avg": average(quote_ratios),
        },
    }


def summarize_windows(metrics: list[EpisodeMetrics], window_size: int) -> dict[str, Any]:
    if len(metrics) < window_size:
        return {"window_count": 0}

    windows: list[dict[str, Any]] = []
    for start_index in range(len(metrics) - window_size + 1):
        chunk = metrics[start_index : start_index + window_size]
        char_count = sum(item.char_count for item in chunk)
        paragraph_count = sum(item.paragraph_count for item in chunk)
        sentence_count = sum(item.sentence_count for item in chunk)
        domain_anchor_mentions = sum(item.domain_anchor_mentions for item in chunk)
        quote_paragraph_count = sum(item.quote_paragraph_count for item in chunk)
        windows.append(
            {
                "start_episode": chunk[0].episode_no,
                "end_episode": chunk[-1].episode_no,
                "char_count": char_count,
                "paragraph_count": paragraph_count,
                "sentence_count": sentence_count,
                "domain_anchor_per_1000_chars": round(domain_anchor_mentions / max(char_count, 1) * 1000, 2),
                "quote_paragraph_ratio": round(quote_paragraph_count / max(paragraph_count, 1), 3),
            }
        )

    char_counts = [window["char_count"] for window in windows]
    paragraph_counts = [window["paragraph_count"] for window in windows]
    sentence_counts = [window["sentence_count"] for window in windows]
    anchor_densities = [window["domain_anchor_per_1000_chars"] for window in windows]
    quote_ratios = [window["quote_paragraph_ratio"] for window in windows]
    return {
        "window_count": len(windows),
        "char_count": {
            "p25": quantile(char_counts, 0.25),
            "p50": quantile(char_counts, 0.5),
            "p75": quantile(char_counts, 0.75),
            "avg": average(char_counts),
        },
        "paragraph_count": {
            "p25": quantile(paragraph_counts, 0.25),
            "p50": quantile(paragraph_counts, 0.5),
            "p75": quantile(paragraph_counts, 0.75),
            "avg": average(paragraph_counts),
        },
        "sentence_count": {
            "p25": quantile(sentence_counts, 0.25),
            "p50": quantile(sentence_counts, 0.5),
            "p75": quantile(sentence_counts, 0.75),
            "avg": average(sentence_counts),
        },
        "domain_anchor_per_1000_chars": {
            "p25": quantile(anchor_densities, 0.25),
            "p50": quantile(anchor_densities, 0.5),
            "p75": quantile(anchor_densities, 0.75),
            "avg": average(anchor_densities),
        },
        "quote_paragraph_ratio": {
            "p25": quantile(quote_ratios, 0.25),
            "p50": quantile(quote_ratios, 0.5),
            "p75": quantile(quote_ratios, 0.75),
            "avg": average(quote_ratios),
        },
        "example_windows": windows[:3],
    }


def summarize_corpus(corpus_dir: Path, *, window_sizes: list[int]) -> dict[str, Any]:
    episode_files = list_episode_files(corpus_dir)
    if not episode_files:
        raise ValueError(f"no episode files found under {corpus_dir}")
    metrics = [
        build_episode_metrics(decode_text_file(path), episode_no=parse_episode_no(path))
        for path in episode_files
    ]
    return {
        "label": corpus_dir.name,
        "corpus_dir": relativize(corpus_dir),
        "episode_files": len(episode_files),
        "series_summary": summarize_series(metrics),
        "window_summaries": {str(size): summarize_windows(metrics, size) for size in window_sizes},
        "sample_episodes": [asdict(item) for item in metrics[:3]],
    }


def parse_window_sizes(raw: str) -> list[int]:
    results: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        value = int(part)
        if value <= 0:
            raise ValueError("window sizes must be positive integers")
        results.append(value)
    if not results:
        raise ValueError("at least one window size is required")
    return sorted(set(results))


def main() -> int:
    args = parse_args()
    if not args.corpus_dir:
        raise SystemExit("at least one --corpus-dir is required")
    window_sizes = parse_window_sizes(args.window_sizes)
    corpus_dirs = [Path(raw) if Path(raw).is_absolute() else ROOT / raw for raw in args.corpus_dir]
    payload = {
        "_schema_version": "bundle_density_snapshot.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "window_sizes": window_sizes,
        "corpora": [summarize_corpus(path, window_sizes=window_sizes) for path in corpus_dirs],
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.json or not args.output:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
