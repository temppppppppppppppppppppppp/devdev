# -*- coding: utf-8 -*-
"""Build a reusable YouTube channel corpus for narrative ideation.

This script stays on the collection side only.
It gathers:

- channel-wide video index metadata
- per-video raw info JSON
- per-video raw caption JSON3 when available
- normalized SQLite / JSONL artifacts for later LLM-side ideation
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import requests

try:
    from yt_dlp import YoutubeDL
    from yt_dlp.utils import DownloadError
except Exception as exc:  # pragma: no cover - bounded import guard
    raise SystemExit(
        "yt-dlp is required. Install with: python -m pip install yt-dlp\n"
        f"Import error: {exc}"
    )


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = (
    ROOT
    / "narrative_ssot"
    / "10_reference_bank"
    / "source_corpora"
    / "youtube"
    / "syukaworld"
)
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/135.0.0.0 Safari/537.36"
)


@dataclass(slots=True)
class ChannelConfig:
    channel_url: str
    channel_slug: str
    tabs: list[str]
    langs: list[str]
    output_root: Path
    request_pause_seconds: float
    subtitle_pause_seconds: float
    max_videos: int | None
    artifact_batch_size: int | None
    use_existing_index: bool
    skip_artifacts: bool
    skip_db: bool


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _assert_within_workspace(path: Path) -> None:
    resolved_root = ROOT.resolve()
    resolved_path = path.resolve()
    if resolved_root not in [resolved_path, *resolved_path.parents]:
        raise RuntimeError(f"Path escaped workspace root: {resolved_path}")


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _extract_text(node: Any) -> str:
    if not isinstance(node, dict):
        return ""
    simple = node.get("simpleText")
    if isinstance(simple, str):
        return simple
    runs = node.get("runs")
    if isinstance(runs, list):
        return "".join(part.get("text", "") for part in runs if isinstance(part, dict))
    return ""


def _find_first(root: Any, key: str) -> dict[str, Any] | None:
    queue: deque[Any] = deque([root])
    while queue:
        current = queue.popleft()
        if isinstance(current, dict):
            if key in current and isinstance(current[key], dict):
                return current[key]
            queue.extend(current.values())
        elif isinstance(current, list):
            queue.extend(current)
    return None


def _iter_renderer_pairs(root: Any) -> Iterable[tuple[str, dict[str, Any]]]:
    queue: deque[Any] = deque([root])
    while queue:
        current = queue.popleft()
        if isinstance(current, dict):
            for renderer_key in ("videoRenderer", "gridVideoRenderer", "reelItemRenderer"):
                renderer = current.get(renderer_key)
                if isinstance(renderer, dict):
                    yield renderer_key, renderer
            queue.extend(current.values())
        elif isinstance(current, list):
            queue.extend(current)


def _find_continuation_token(root: Any) -> str | None:
    queue: deque[Any] = deque([root])
    while queue:
        current = queue.popleft()
        if isinstance(current, dict):
            command = current.get("continuationCommand")
            if isinstance(command, dict):
                token = command.get("token")
                if isinstance(token, str) and token:
                    return token
            queue.extend(current.values())
        elif isinstance(current, list):
            queue.extend(current)
    return None


def _thumbnail_url(node: Any) -> str:
    thumbnails = []
    if isinstance(node, dict):
        thumbnails = node.get("thumbnails") or []
    if thumbnails and isinstance(thumbnails[-1], dict):
        return thumbnails[-1].get("url", "")
    return ""


def _normalize_renderer(
    renderer_key: str,
    renderer: dict[str, Any],
    *,
    tab: str,
    crawl_position: int,
) -> dict[str, Any] | None:
    video_id = renderer.get("videoId")
    if not isinstance(video_id, str) or not video_id:
        return None

    title_node = renderer.get("title") or renderer.get("headline")
    published_node = renderer.get("publishedTimeText")
    view_node = renderer.get("viewCountText") or renderer.get("shortViewCountText")
    length_node = renderer.get("lengthText")
    description_node = renderer.get("descriptionSnippet")
    badges = renderer.get("badges") or []
    owner_node = renderer.get("ownerText") or renderer.get("shortBylineText") or {}

    badge_labels: list[str] = []
    for badge in badges:
        if not isinstance(badge, dict):
            continue
        label = _extract_text(badge.get("metadataBadgeRenderer") or {})
        if label:
            badge_labels.append(label)

    return {
        "video_id": video_id,
        "title": _extract_text(title_node),
        "source_tab": tab,
        "renderer_key": renderer_key,
        "crawl_position": crawl_position,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "published_text": _extract_text(published_node),
        "view_count_text": _extract_text(view_node),
        "length_text": _extract_text(length_node),
        "description_snippet": _extract_text(description_node),
        "owner_text": _extract_text(owner_node),
        "thumbnail_url": _thumbnail_url(renderer.get("thumbnail")),
        "badge_labels": badge_labels,
    }


def _get_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def _extract_youtube_config(html: str) -> dict[str, str]:
    patterns = {
        "api_key": r'"INNERTUBE_API_KEY":"([^"]+)"',
        "client_version": r'"INNERTUBE_CLIENT_VERSION":"([^"]+)"',
        "visitor_data": r'"VISITOR_DATA":"([^"]+)"',
    }
    config: dict[str, str] = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, html)
        if not match:
            raise RuntimeError(f"Missing YouTube config key: {name}")
        config[name] = match.group(1)
    return config


def _extract_initial_data(html: str) -> dict[str, Any]:
    patterns = [
        r"var ytInitialData = (\{.+?\});",
        r"ytInitialData\s*=\s*(\{.+?\});",
    ]
    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            return json.loads(match.group(1))
    raise RuntimeError("Failed to extract ytInitialData from channel page")


def _channel_metadata_from_initial(initial_data: dict[str, Any], channel_url: str) -> dict[str, Any]:
    renderer = _find_first(initial_data, "channelMetadataRenderer") or {}
    return {
        "title": renderer.get("title", ""),
        "channel_id": renderer.get("externalId", ""),
        "description": renderer.get("description", ""),
        "vanity_channel_url": renderer.get("vanityChannelUrl", channel_url),
        "rss_url": renderer.get("rssUrl", ""),
    }


def _browse_continuation(
    session: requests.Session,
    *,
    api_key: str,
    client_version: str,
    visitor_data: str,
    token: str,
) -> dict[str, Any]:
    url = f"https://www.youtube.com/youtubei/v1/browse?key={api_key}"
    payload = {
        "context": {
            "client": {
                "clientName": "WEB",
                "clientVersion": client_version,
                "hl": "ko",
                "gl": "KR",
                "visitorData": visitor_data,
            }
        },
        "continuation": token,
    }
    response = session.post(url, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def crawl_channel_index(config: ChannelConfig) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    session = _get_session()
    seen: dict[str, dict[str, Any]] = {}
    channel_metadata: dict[str, Any] | None = None

    for tab in config.tabs:
        tab_url = f"{config.channel_url.rstrip('/')}/{tab}"
        html = session.get(tab_url, timeout=30).text
        youtube_config = _extract_youtube_config(html)
        initial_data = _extract_initial_data(html)
        if channel_metadata is None:
            channel_metadata = _channel_metadata_from_initial(initial_data, config.channel_url)

        crawl_position = len(seen)
        for renderer_key, renderer in _iter_renderer_pairs(initial_data):
            record = _normalize_renderer(
                renderer_key,
                renderer,
                tab=tab,
                crawl_position=crawl_position,
            )
            if not record:
                continue
            crawl_position += 1
            seen.setdefault(record["video_id"], record)
            if config.max_videos and len(seen) >= config.max_videos:
                break
        if config.max_videos and len(seen) >= config.max_videos:
            break

        token = _find_continuation_token(initial_data)
        while token:
            payload = _browse_continuation(
                session,
                api_key=youtube_config["api_key"],
                client_version=youtube_config["client_version"],
                visitor_data=youtube_config["visitor_data"],
                token=token,
            )
            for renderer_key, renderer in _iter_renderer_pairs(payload):
                record = _normalize_renderer(
                    renderer_key,
                    renderer,
                    tab=tab,
                    crawl_position=crawl_position,
                )
                if not record:
                    continue
                crawl_position += 1
                seen.setdefault(record["video_id"], record)
                if config.max_videos and len(seen) >= config.max_videos:
                    break
            if config.max_videos and len(seen) >= config.max_videos:
                break
            token = _find_continuation_token(payload)
            if token:
                time.sleep(config.request_pause_seconds)
        if config.max_videos and len(seen) >= config.max_videos:
            break

    if channel_metadata is None:
        raise RuntimeError("Failed to resolve channel metadata")
    records = sorted(seen.values(), key=lambda row: row["crawl_position"])
    return channel_metadata, records


def _list_subtitle_files(video_dir: Path, langs: list[str]) -> list[Path]:
    found: list[Path] = []
    for lang in langs:
        found.extend(sorted(video_dir.glob(f"*.{lang}.json3")))
        found.extend(sorted(video_dir.glob(f"*.{lang}-orig.json3")))
    return found


def _download_video_artifacts(
    *,
    video: dict[str, Any],
    raw_root: Path,
    langs: list[str],
) -> dict[str, Any]:
    video_id = video["video_id"]
    video_dir = raw_root / "videos" / video_id
    video_dir.mkdir(parents=True, exist_ok=True)
    info_path = video_dir / f"{video_id}.info.json"
    subtitle_paths = _list_subtitle_files(video_dir, langs)
    if info_path.is_file() and subtitle_paths:
        return {
            "video_id": video_id,
            "status": "skipped_existing",
            "info_path": str(info_path.relative_to(ROOT)).replace("\\", "/"),
            "subtitle_paths": [
                str(path.relative_to(ROOT)).replace("\\", "/") for path in subtitle_paths
            ],
        }

    options = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "writeinfojson": True,
        "writeautomaticsub": True,
        "writesubtitles": True,
        "subtitleslangs": langs,
        "subtitlesformat": "json3",
        "paths": {"home": str(video_dir)},
        "outtmpl": {"default": f"{video_id}.%(ext)s"},
        "ignoreerrors": True,
    }

    error_message = ""
    try:
        with YoutubeDL(options) as ydl:
            ydl.download([video["url"]])
    except DownloadError as exc:
        error_message = str(exc)
    subtitle_paths = _list_subtitle_files(video_dir, langs)
    status = "caption_saved" if subtitle_paths else "info_only"
    if error_message and status != "caption_saved":
        status = "failed"

    return {
        "video_id": video_id,
        "status": status,
        "error": error_message,
        "info_path": (
            str(info_path.relative_to(ROOT)).replace("\\", "/") if info_path.is_file() else ""
        ),
        "subtitle_paths": [
            str(path.relative_to(ROOT)).replace("\\", "/") for path in subtitle_paths
        ],
    }


def fetch_all_video_artifacts(
    config: ChannelConfig,
    *,
    videos: list[dict[str, Any]],
    raw_root: Path,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for index, video in enumerate(videos, start=1):
        result = _download_video_artifacts(video=video, raw_root=raw_root, langs=config.langs)
        result["ordinal"] = index
        results.append(result)
        time.sleep(config.subtitle_pause_seconds)
    return results


def scan_existing_artifacts(
    *,
    videos: list[dict[str, Any]],
    raw_root: Path,
    langs: list[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for video in videos:
        video_id = video["video_id"]
        video_dir = raw_root / "videos" / video_id
        info_path = video_dir / f"{video_id}.info.json"
        subtitle_paths = _list_subtitle_files(video_dir, langs)
        if subtitle_paths:
            status = "caption_saved"
        elif info_path.is_file():
            status = "info_only"
        else:
            status = "indexed_only"
        rows.append(
            {
                "video_id": video_id,
                "status": status,
                "info_path": (
                    str(info_path.relative_to(ROOT)).replace("\\", "/")
                    if info_path.is_file()
                    else ""
                ),
                "subtitle_paths": [
                    str(path.relative_to(ROOT)).replace("\\", "/") for path in subtitle_paths
                ],
            }
        )
    return rows


def _parse_json3_segments(path: Path) -> dict[str, Any]:
    data = _read_json(path)
    events = data.get("events") or []
    segments: list[dict[str, Any]] = []
    for event in events:
        if not isinstance(event, dict):
            continue
        raw_segs = event.get("segs")
        if not isinstance(raw_segs, list):
            continue
        text = "".join(seg.get("utf8", "") for seg in raw_segs if isinstance(seg, dict))
        text = text.replace("\n", " ").strip()
        if not text:
            continue
        if segments and segments[-1]["text"] == text:
            continue
        segments.append(
            {
                "start_ms": int(event.get("tStartMs") or 0),
                "duration_ms": int(event.get("dDurationMs") or 0),
                "text": text,
            }
        )
    full_text = "\n".join(segment["text"] for segment in segments)
    compact_text = _clean_text(full_text)
    return {
        "segment_count": len(segments),
        "full_text": full_text,
        "compact_text": compact_text,
        "segments": segments,
    }


def _best_caption_path(video_dir: Path, langs: list[str]) -> Path | None:
    candidates = _list_subtitle_files(video_dir, langs)
    return candidates[0] if candidates else None


def _create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA journal_mode=WAL;
        DROP TABLE IF EXISTS channels;
        DROP TABLE IF EXISTS videos;
        DROP TABLE IF EXISTS transcript_segments;
        DROP TABLE IF EXISTS ingest_runs;
        CREATE TABLE channels (
            channel_slug TEXT PRIMARY KEY,
            channel_url TEXT NOT NULL,
            channel_title TEXT NOT NULL,
            channel_id TEXT,
            description TEXT,
            vanity_channel_url TEXT,
            rss_url TEXT,
            generated_at_utc TEXT NOT NULL,
            tabs_json TEXT NOT NULL,
            langs_json TEXT NOT NULL
        );
        CREATE TABLE ingest_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            generated_at_utc TEXT NOT NULL,
            indexed_video_count INTEGER NOT NULL,
            caption_saved_count INTEGER NOT NULL,
            output_root TEXT NOT NULL
        );
        CREATE TABLE videos (
            video_id TEXT PRIMARY KEY,
            channel_slug TEXT NOT NULL,
            channel_id TEXT,
            channel_title TEXT,
            source_tab TEXT NOT NULL,
            crawl_position INTEGER NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            published_text TEXT,
            view_count_text TEXT,
            length_text TEXT,
            description_snippet TEXT,
            owner_text TEXT,
            badge_labels_json TEXT,
            thumbnail_url TEXT,
            upload_date TEXT,
            timestamp INTEGER,
            duration_seconds INTEGER,
            description TEXT,
            availability TEXT,
            uploader TEXT,
            uploader_id TEXT,
            webpage_url TEXT,
            raw_info_path TEXT,
            raw_caption_path TEXT,
            transcript_lang TEXT,
            transcript_status TEXT NOT NULL,
            transcript_segment_count INTEGER NOT NULL DEFAULT 0,
            transcript_char_count INTEGER NOT NULL DEFAULT 0,
            transcript_text TEXT,
            transcript_compact_text TEXT,
            collected_at_utc TEXT NOT NULL
        );
        CREATE TABLE transcript_segments (
            video_id TEXT NOT NULL,
            lang TEXT NOT NULL,
            segment_index INTEGER NOT NULL,
            start_ms INTEGER NOT NULL,
            duration_ms INTEGER NOT NULL,
            text TEXT NOT NULL,
            PRIMARY KEY (video_id, lang, segment_index)
        );
        """
    )


def _create_fts(conn: sqlite3.Connection) -> bool:
    try:
        conn.execute("DROP TABLE IF EXISTS video_transcript_fts")
        conn.execute(
            """
            CREATE VIRTUAL TABLE video_transcript_fts USING fts5(
                video_id UNINDEXED,
                title,
                description,
                transcript_text
            )
            """
        )
        return True
    except sqlite3.OperationalError:
        return False


def build_normalized_corpus(
    config: ChannelConfig,
    *,
    channel_metadata: dict[str, Any],
    videos: list[dict[str, Any]],
    artifact_results: list[dict[str, Any]],
) -> dict[str, Any]:
    output_root = config.output_root
    raw_root = output_root / "raw"
    db_path = output_root / f"{config.channel_slug}.sqlite3"
    query_jsonl_path = output_root / "video_lookup.jsonl"
    transcript_jsonl_path = output_root / "transcript_documents.jsonl"

    _assert_within_workspace(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    artifact_by_id = {row["video_id"]: row for row in artifact_results}
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    _create_schema(conn)
    fts_enabled = _create_fts(conn)

    conn.execute(
        """
        INSERT INTO channels (
            channel_slug, channel_url, channel_title, channel_id,
            description, vanity_channel_url, rss_url, generated_at_utc,
            tabs_json, langs_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            config.channel_slug,
            config.channel_url,
            channel_metadata.get("title", ""),
            channel_metadata.get("channel_id", ""),
            channel_metadata.get("description", ""),
            channel_metadata.get("vanity_channel_url", ""),
            channel_metadata.get("rss_url", ""),
            _now_utc(),
            json.dumps(config.tabs, ensure_ascii=False),
            json.dumps(config.langs, ensure_ascii=False),
        ),
    )

    lookup_rows: list[dict[str, Any]] = []
    transcript_rows: list[dict[str, Any]] = []
    caption_saved_count = 0

    for video in videos:
        video_id = video["video_id"]
        video_dir = raw_root / "videos" / video_id
        info_path = video_dir / f"{video_id}.info.json"
        caption_path = _best_caption_path(video_dir, config.langs)
        artifact = artifact_by_id.get(video_id, {})
        info = _read_json(info_path) if info_path.is_file() else {}

        transcript_lang = ""
        transcript_status = artifact.get("status", "missing")
        transcript_segment_count = 0
        transcript_text = ""
        transcript_compact_text = ""
        raw_caption_rel = ""

        parsed_segments: list[dict[str, Any]] = []
        if caption_path and caption_path.is_file():
            parsed = _parse_json3_segments(caption_path)
            parsed_segments = parsed["segments"]
            transcript_segment_count = parsed["segment_count"]
            transcript_text = parsed["full_text"]
            transcript_compact_text = parsed["compact_text"]
            raw_caption_rel = str(caption_path.relative_to(ROOT)).replace("\\", "/")
            transcript_lang = caption_path.suffixes[-2].lstrip(".")
            transcript_status = "caption_saved"
            caption_saved_count += 1

        raw_info_rel = (
            str(info_path.relative_to(ROOT)).replace("\\", "/") if info_path.is_file() else ""
        )
        row = {
            "video_id": video_id,
            "channel_slug": config.channel_slug,
            "channel_id": info.get("channel_id", channel_metadata.get("channel_id", "")),
            "channel_title": info.get("channel", channel_metadata.get("title", "")),
            "source_tab": video["source_tab"],
            "crawl_position": video["crawl_position"],
            "title": info.get("title", video["title"]),
            "url": video["url"],
            "published_text": video.get("published_text", ""),
            "view_count_text": video.get("view_count_text", ""),
            "length_text": video.get("length_text", ""),
            "description_snippet": video.get("description_snippet", ""),
            "owner_text": video.get("owner_text", ""),
            "badge_labels_json": json.dumps(video.get("badge_labels", []), ensure_ascii=False),
            "thumbnail_url": video.get("thumbnail_url", ""),
            "upload_date": info.get("upload_date"),
            "timestamp": info.get("timestamp"),
            "duration_seconds": info.get("duration"),
            "description": info.get("description", ""),
            "availability": info.get("availability"),
            "uploader": info.get("uploader"),
            "uploader_id": info.get("uploader_id"),
            "webpage_url": info.get("webpage_url", video["url"]),
            "raw_info_path": raw_info_rel,
            "raw_caption_path": raw_caption_rel,
            "transcript_lang": transcript_lang,
            "transcript_status": transcript_status,
            "transcript_segment_count": transcript_segment_count,
            "transcript_char_count": len(transcript_compact_text),
            "transcript_text": transcript_text,
            "transcript_compact_text": transcript_compact_text,
            "collected_at_utc": _now_utc(),
        }
        conn.execute(
            """
            INSERT INTO videos (
                video_id, channel_slug, channel_id, channel_title, source_tab,
                crawl_position, title, url, published_text, view_count_text,
                length_text, description_snippet, owner_text, badge_labels_json,
                thumbnail_url, upload_date, timestamp, duration_seconds, description,
                availability, uploader, uploader_id, webpage_url, raw_info_path,
                raw_caption_path, transcript_lang, transcript_status,
                transcript_segment_count, transcript_char_count, transcript_text,
                transcript_compact_text, collected_at_utc
            ) VALUES (
                :video_id, :channel_slug, :channel_id, :channel_title, :source_tab,
                :crawl_position, :title, :url, :published_text, :view_count_text,
                :length_text, :description_snippet, :owner_text, :badge_labels_json,
                :thumbnail_url, :upload_date, :timestamp, :duration_seconds, :description,
                :availability, :uploader, :uploader_id, :webpage_url, :raw_info_path,
                :raw_caption_path, :transcript_lang, :transcript_status,
                :transcript_segment_count, :transcript_char_count, :transcript_text,
                :transcript_compact_text, :collected_at_utc
            )
            """,
            row,
        )

        if fts_enabled:
            conn.execute(
                """
                INSERT INTO video_transcript_fts (video_id, title, description, transcript_text)
                VALUES (?, ?, ?, ?)
                """,
                (video_id, row["title"], row["description"], row["transcript_compact_text"]),
            )

        for segment_index, segment in enumerate(parsed_segments):
            conn.execute(
                """
                INSERT INTO transcript_segments (
                    video_id, lang, segment_index, start_ms, duration_ms, text
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    video_id,
                    transcript_lang or "ko",
                    segment_index,
                    segment["start_ms"],
                    segment["duration_ms"],
                    segment["text"],
                ),
            )

        lookup_rows.append(
            {
                "video_id": video_id,
                "title": row["title"],
                "source_tab": row["source_tab"],
                "published_text": row["published_text"],
                "view_count_text": row["view_count_text"],
                "length_text": row["length_text"],
                "badge_labels": video.get("badge_labels", []),
                "description_preview": row["description"][:300],
                "raw_info_path": row["raw_info_path"],
                "raw_caption_path": row["raw_caption_path"],
                "transcript_status": row["transcript_status"],
            }
        )
        if transcript_text:
            transcript_rows.append(
                {
                    "video_id": video_id,
                    "title": row["title"],
                    "source_tab": row["source_tab"],
                    "published_text": row["published_text"],
                    "transcript_lang": row["transcript_lang"],
                    "segment_count": row["transcript_segment_count"],
                    "transcript_text": row["transcript_compact_text"],
                    "raw_caption_path": row["raw_caption_path"],
                }
            )

    conn.execute(
        """
        INSERT INTO ingest_runs (generated_at_utc, indexed_video_count, caption_saved_count, output_root)
        VALUES (?, ?, ?, ?)
        """,
        (
            _now_utc(),
            len(videos),
            caption_saved_count,
            str(output_root.relative_to(ROOT)).replace("\\", "/"),
        ),
    )
    conn.commit()
    conn.close()

    _write_jsonl(query_jsonl_path, lookup_rows)
    _write_jsonl(transcript_jsonl_path, transcript_rows)

    return {
        "db_path": str(db_path.relative_to(ROOT)).replace("\\", "/"),
        "query_jsonl_path": str(query_jsonl_path.relative_to(ROOT)).replace("\\", "/"),
        "transcript_jsonl_path": str(transcript_jsonl_path.relative_to(ROOT)).replace("\\", "/"),
        "fts_enabled": fts_enabled,
        "caption_saved_count": caption_saved_count,
    }


def parse_args(argv: list[str]) -> ChannelConfig:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel-url", required=True)
    parser.add_argument("--channel-slug", required=True)
    parser.add_argument(
        "--tabs",
        nargs="+",
        default=["videos", "streams"],
        help="Channel tabs to crawl. Default: videos streams",
    )
    parser.add_argument(
        "--langs",
        nargs="+",
        default=["ko"],
        help="Subtitle languages to request from yt-dlp. Default: ko",
    )
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--request-pause-seconds", type=float, default=0.35)
    parser.add_argument("--subtitle-pause-seconds", type=float, default=0.5)
    parser.add_argument("--max-videos", type=int)
    parser.add_argument(
        "--artifact-batch-size",
        type=int,
        help="Only fetch subtitles/info for the first N not-yet-saved videos from the chosen index.",
    )
    parser.add_argument(
        "--use-existing-index",
        action="store_true",
        help="Reuse channel_manifest.json + video_index.json if they already exist.",
    )
    parser.add_argument("--skip-artifacts", action="store_true")
    parser.add_argument("--skip-db", action="store_true")
    args = parser.parse_args(argv)
    output_root = args.output_root
    if not output_root.is_absolute():
        output_root = (ROOT / output_root).resolve()
    return ChannelConfig(
        channel_url=args.channel_url,
        channel_slug=args.channel_slug,
        tabs=args.tabs,
        langs=args.langs,
        output_root=output_root,
        request_pause_seconds=args.request_pause_seconds,
        subtitle_pause_seconds=args.subtitle_pause_seconds,
        max_videos=args.max_videos,
        artifact_batch_size=args.artifact_batch_size,
        use_existing_index=args.use_existing_index,
        skip_artifacts=args.skip_artifacts,
        skip_db=args.skip_db,
    )


def main(argv: list[str] | None = None) -> int:
    config = parse_args(argv or sys.argv[1:])
    _assert_within_workspace(config.output_root)
    config.output_root.mkdir(parents=True, exist_ok=True)

    raw_root = config.output_root / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)

    channel_manifest_path = config.output_root / "channel_manifest.json"
    video_index_path = config.output_root / "video_index.json"
    if config.use_existing_index and channel_manifest_path.is_file() and video_index_path.is_file():
        channel_metadata = _read_json(channel_manifest_path)["channel"]
        videos = _read_json(video_index_path)["videos"]
    else:
        channel_metadata, videos = crawl_channel_index(config)
        _write_json(
            channel_manifest_path,
            {
                "_schema_version": "youtube_channel_corpus.v1",
                "channel_slug": config.channel_slug,
                "channel_url": config.channel_url,
                "generated_at_utc": _now_utc(),
                "channel": channel_metadata,
                "tabs": config.tabs,
                "langs": config.langs,
                "indexed_video_count": len(videos),
                "paths": {
                    "raw_root": str(raw_root.relative_to(ROOT)).replace("\\", "/"),
                    "video_index_path": str(video_index_path.relative_to(ROOT)).replace("\\", "/"),
                },
                "notes": [
                    "Python collection only; downstream story judgment stays on the LLM side.",
                    "Channel crawling uses YouTube page metadata plus yt-dlp per-video raw artifact capture.",
                    "Subtitle availability depends on per-video auto-caption availability and YouTube rate limits.",
                ],
            },
        )
        _write_json(
            video_index_path,
            {
                "_schema_version": "youtube_channel_video_index.v1",
                "channel_slug": config.channel_slug,
                "generated_at_utc": _now_utc(),
                "video_count": len(videos),
                "videos": videos,
            },
        )

    artifact_results = scan_existing_artifacts(videos=videos, raw_root=raw_root, langs=config.langs)
    if not config.skip_artifacts:
        artifact_by_id = {row["video_id"]: row for row in artifact_results}
        pending_videos = [
            video
            for video in videos
            if artifact_by_id[video["video_id"]]["status"] not in ("caption_saved", "skipped_existing")
        ]
        if config.artifact_batch_size:
            pending_videos = pending_videos[: config.artifact_batch_size]
        new_results = fetch_all_video_artifacts(
            config,
            videos=pending_videos,
            raw_root=raw_root,
        )
        for row in new_results:
            artifact_by_id[row["video_id"]] = row
        artifact_results = [artifact_by_id[video["video_id"]] for video in videos]

    normalized = {
        "db_path": "",
        "query_jsonl_path": "",
        "transcript_jsonl_path": "",
        "fts_enabled": False,
        "caption_saved_count": 0,
    }
    if not config.skip_db:
        normalized = build_normalized_corpus(
            config,
            channel_metadata=channel_metadata,
            videos=videos,
            artifact_results=artifact_results,
        )

    failure_count = sum(1 for row in artifact_results if row.get("status") == "failed")
    caption_saved_count = sum(1 for row in artifact_results if row.get("status") == "caption_saved")
    info_only_count = sum(1 for row in artifact_results if row.get("status") == "info_only")
    skipped_existing_count = sum(
        1 for row in artifact_results if row.get("status") == "skipped_existing"
    )
    _write_json(config.output_root / "artifact_results.json", artifact_results)
    _write_json(
        config.output_root / "ingest_status.json",
        {
            "_schema_version": "youtube_channel_ingest_status.v1",
            "channel_slug": config.channel_slug,
            "generated_at_utc": _now_utc(),
            "indexed_video_count": len(videos),
            "artifact_summary": {
                "caption_saved_count": caption_saved_count,
                "info_only_count": info_only_count,
                "skipped_existing_count": skipped_existing_count,
                "failed_count": failure_count,
            },
            "normalized_outputs": normalized,
            "artifact_results_path": str(
                (config.output_root / "artifact_results.json").relative_to(ROOT)
            ).replace("\\", "/"),
            "notes": [
                "Use the SQLite corpus for exact lookup and transcript search.",
                "If failed_count > 0, rerun the same command; existing artifacts will be resumed/skipped.",
            ],
        },
    )

    print(f"Indexed {len(videos)} videos for channel '{config.channel_slug}'")
    print(f"Channel manifest: {channel_manifest_path}")
    print(f"Video index: {video_index_path}")
    print(f"Artifact results: {config.output_root / 'artifact_results.json'}")
    if not config.skip_db:
        print(f"SQLite corpus: {config.output_root / f'{config.channel_slug}.sqlite3'}")
        print(f"Lookup JSONL: {config.output_root / 'video_lookup.jsonl'}")
        print(f"Transcript JSONL: {config.output_root / 'transcript_documents.jsonl'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
