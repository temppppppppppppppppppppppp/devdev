"""Export captioned YouTube videos into LLM-ready idea packets.

This script does not judge idea quality.
It packages already collected evidence so an LLM can later extract:

- hidden structure outside the obvious topic
- bottleneck / corridor hints
- chaebolizable leverage
- early backstab scene candidates
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = (
    ROOT
    / "material_ssot"
    / "10_research"
    / "40_analysis"
    / "source_corpora"
    / "youtube"
    / "syukaworld"
    / "syukaworld.sqlite3"
)
DEFAULT_OUTPUT = (
    ROOT
    / "material_ssot"
    / "10_research"
    / "40_analysis"
    / "source_corpora"
    / "youtube"
    / "syukaworld"
    / "idea_packets_recent.jsonl"
)
DEFAULT_SCHEMA_OUTPUT = (
    ROOT
    / "material_ssot"
    / "10_research"
    / "40_analysis"
    / "source_corpora"
    / "youtube"
    / "syukaworld"
    / "idea_packet_schema.json"
)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _build_schema(schema_path: Path) -> dict[str, Any]:
    return {
        "_schema_version": "youtube_idea_packet_schema.v1",
        "schema_path": str(schema_path.relative_to(ROOT)).replace("\\", "/"),
        "purpose": "LLM-side extraction target for turning economic video evidence into modern business / chaebol ideation seeds.",
        "authority_note": "Collection stays on Python; extraction judgment and concept selection stay on the LLM side.",
        "packet_fields": {
            "surface_issue": "영상 표면 주제가 무엇인지 짧게 요약",
            "hidden_structure_outside_information": "표면 주제 뒤에 숨은 진짜 구조/권력선/돈줄",
            "real_bottleneck_or_corridor": "반드시 지나가야 하는 관문, 병목, 회랑 후보",
            "chaebolizable_sector": "재벌물/기업물로 전환하기 좋은 섹터나 계열사 포지션",
            "power_fantasy_translation": "독자 대리만족으로 바꾸면 무엇이 되는지",
            "early_backstab_scene": "1~3화 초반 뒤통수 장면의 한 줄 구상",
            "octopus_group_expansion_path": "문어발식으로 다음 계열사나 인접 섹터를 어떻게 붙일지",
            "must_not_literal_copy": "원본 영상 표현이나 사례를 그대로 베끼면 안 되는 요소",
            "confidence": "low / medium / high",
        },
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--schema-output", type=Path, default=DEFAULT_SCHEMA_OUTPUT)
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument(
        "--order",
        choices=["recent", "oldest"],
        default="recent",
        help="Sort by upload_date/timestamp when available, else crawl order.",
    )
    parser.add_argument(
        "--min-transcript-chars",
        type=int,
        default=300,
        help="Skip tiny transcripts under this compact char count.",
    )
    return parser.parse_args(argv)


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else (ROOT / path).resolve()


def _query_rows(conn: sqlite3.Connection, order: str, limit: int, min_chars: int) -> list[sqlite3.Row]:
    order_sql = (
        """
        CASE WHEN upload_date IS NOT NULL AND upload_date != '' THEN upload_date ELSE '' END DESC,
        CASE WHEN timestamp IS NOT NULL THEN timestamp ELSE 0 END DESC,
        crawl_position ASC
    """
        if order == "recent"
        else """
        CASE WHEN upload_date IS NOT NULL AND upload_date != '' THEN upload_date ELSE '99999999' END ASC,
        CASE WHEN timestamp IS NOT NULL THEN timestamp ELSE 9999999999 END ASC,
        crawl_position ASC
    """
    )
    query = f"""
        SELECT
            video_id, channel_slug, channel_title, title, url,
            source_tab, crawl_position, published_text, upload_date,
            timestamp, duration_seconds, description, raw_info_path,
            raw_caption_path, transcript_lang, transcript_segment_count,
            transcript_char_count, transcript_compact_text
        FROM videos
        WHERE transcript_status = 'caption_saved'
          AND transcript_char_count >= ?
        ORDER BY {order_sql}
        LIMIT ?
    """
    return conn.execute(query, (min_chars, limit)).fetchall()


def _packet_from_row(row: sqlite3.Row, schema_ref: str) -> dict[str, Any]:
    transcript = row["transcript_compact_text"] or ""
    return {
        "packet_id": f"yt-{row['video_id']}",
        "source_type": "youtube_video",
        "channel_slug": row["channel_slug"],
        "channel_title": row["channel_title"],
        "video_id": row["video_id"],
        "title": row["title"],
        "url": row["url"],
        "source_tab": row["source_tab"],
        "published_text": row["published_text"],
        "upload_date": row["upload_date"],
        "timestamp": row["timestamp"],
        "duration_seconds": row["duration_seconds"],
        "transcript_lang": row["transcript_lang"],
        "transcript_segment_count": row["transcript_segment_count"],
        "transcript_char_count": row["transcript_char_count"],
        "description": row["description"] or "",
        "transcript_excerpt_head": transcript[:2000],
        "transcript_excerpt_tail": transcript[-1000:] if len(transcript) > 1000 else transcript,
        "transcript_text": transcript,
        "source_paths": {
            "raw_info_path": row["raw_info_path"],
            "raw_caption_path": row["raw_caption_path"],
        },
        "llm_extraction_schema_ref": schema_ref,
        "llm_output_template": {
            "surface_issue": "",
            "hidden_structure_outside_information": "",
            "real_bottleneck_or_corridor": "",
            "chaebolizable_sector": "",
            "power_fantasy_translation": "",
            "early_backstab_scene": "",
            "octopus_group_expansion_path": "",
            "must_not_literal_copy": [],
            "confidence": "",
        },
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    db_path = _resolve(args.db)
    output_path = _resolve(args.output)
    schema_output_path = _resolve(args.schema_output)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = _query_rows(conn, order=args.order, limit=args.limit, min_chars=args.min_transcript_chars)
    conn.close()

    schema = _build_schema(schema_output_path)
    _write_json(schema_output_path, schema)
    schema_ref = str(schema_output_path.relative_to(ROOT)).replace("\\", "/")

    packets = [_packet_from_row(row, schema_ref) for row in rows]
    _write_jsonl(output_path, packets)

    print(f"Exported {len(packets)} idea packets")
    print(f"DB: {db_path}")
    print(f"Schema: {schema_output_path}")
    print(f"Output: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
