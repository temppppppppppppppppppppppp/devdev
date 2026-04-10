from __future__ import annotations

from pathlib import Path

import scripts.bundle_density_snapshot as snapshot_script


def _write_episode(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_summarize_corpus_builds_episode_and_window_quantiles(temp_dir) -> None:
    corpus_dir = temp_dir / "corpus"
    _write_episode(
        corpus_dir / "ep001.txt",
        "\"서두 대사\"\n\n한빛캐피탈 회의실에서 120억 원 계약이 열렸다. 모두가 다시 봤다.",
    )
    _write_episode(
        corpus_dir / "ep002.txt",
        "다음 날 유성그룹 본사에서 35억 원 역제안이 나왔다.\n\n\"바로 들어가죠.\"",
    )
    _write_episode(
        corpus_dir / "ep003.txt",
        "조정실 브리핑. 대창증권 보고서가 올라오고 7% 수익률이 찍혔다.",
    )

    result = snapshot_script.summarize_corpus(corpus_dir, window_sizes=[2, 3])

    assert result["label"] == "corpus"
    assert result["series_summary"]["episode_count"] == 3
    assert result["series_summary"]["char_count"]["p50"] is not None
    assert result["series_summary"]["domain_anchor_per_1000_chars"]["p50"] > 0
    assert result["window_summaries"]["2"]["window_count"] == 2
    assert result["window_summaries"]["3"]["window_count"] == 1
    assert result["window_summaries"]["2"]["char_count"]["p50"] > result["series_summary"]["char_count"]["p50"]


def test_parse_window_sizes_dedupes_and_sorts() -> None:
    assert snapshot_script.parse_window_sizes("6,2,4,2") == [2, 4, 6]
