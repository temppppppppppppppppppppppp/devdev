# -*- coding: utf-8 -*-
"""Build a business-only trend slice from the broader KR serial platform corpus.

Collection / formatting only:
- reads the already-collected platform trend SQLite corpus
- applies transparent keyword scoring for business / office / chaebol relevance
- saves filtered entry/work slices + exact-count rollups

LLM-side work happens later:
- deciding which slice signals are actually worth stealing
- turning the slice into source manifests or concept engines
- judging idea quality, novelty, or market fit
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DB = (
    ROOT
    / "narrative_ssot"
    / "10_reference_bank"
    / "source_corpora"
    / "platform_trends"
    / "kr_serial_platforms"
    / "platform_trends.sqlite3"
)
DEFAULT_OUTPUT_ROOT = (
    ROOT
    / "narrative_ssot"
    / "10_reference_bank"
    / "source_corpora"
    / "platform_trends"
    / "kr_serial_platforms"
    / "business_trend_slice"
)


POSITIVE_BUCKETS: dict[str, dict[str, Any]] = {
    "chaebol_power": {
        "weight": 6,
        "keywords": [
            "재벌",
            "후계자",
            "오너 일가",
            "오너",
            "그룹",
            "회장",
            "부회장",
            "전무",
            "상무",
            "사장",
            "대표이사",
            "ceo",
            "재벌가",
            "재벌집",
        ],
    },
    "office_operator": {
        "weight": 5,
        "keywords": [
            "회사원",
            "회사",
            "사원",
            "말단",
            "대리",
            "과장",
            "부장",
            "팀장",
            "본부",
            "재무",
            "감사",
            "프로젝트",
            "결재",
            "직장",
            "협회장",
            "공무원",
            "감정사",
            "변호사",
            "엔지니어",
        ],
    },
    "money_game": {
        "weight": 5,
        "keywords": [
            "투자",
            "주식",
            "증권",
            "펀드",
            "계좌",
            "수익률",
            "코인",
            "돈 복사",
            "돈이 미쳤",
            "돈을",
            "로또",
            "자산",
            "부업",
        ],
    },
    "industry_scale": {
        "weight": 5,
        "keywords": [
            "반도체",
            "빅테크",
            "ai",
            "제약회사",
            "건설",
            "에너지",
            "방산",
            "마트",
            "대기업",
            "게임 개발",
            "저작권료",
        ],
    },
    "media_ip_business": {
        "weight": 4,
        "keywords": [
            "ott",
            "스트리밍",
            "디렉터",
            "프로듀서",
            "pd",
            "탑스타",
            "작곡",
            "출판사",
            "인세",
            "저작권료",
            "연예",
        ],
    },
    "global_scale": {
        "weight": 2,
        "keywords": [
            "미국",
            "아메리카",
            "글로벌",
            "해외",
            "세계",
            "국정원",
            "중동",
        ],
    },
}

POSITIVE_GENRE_TOKENS = {
    "현대판타지": 4,
    "현판": 4,
    "sf": 2,
    "드라마": 1,
}

NEGATIVE_BUCKETS: dict[str, dict[str, Any]] = {
    "romance_noise": {
        "weight": 7,
        "keywords": [
            "로맨스",
            "로판",
            "bl",
            "19금",
            "남편",
            "아내",
            "와이프",
            "애인",
            "하룻밤",
            "임신",
            "키스",
            "짝사랑",
            "결혼",
            "신부",
            "오메가",
            "알파",
            "며느리",
            "연애",
            "집착",
            "남주",
            "여주",
            "첫사랑",
            "하이틴",
        ],
    },
    "fantasy_noise": {
        "weight": 5,
        "keywords": [
            "황제",
            "황자",
            "황녀",
            "공작",
            "영애",
            "왕자",
            "왕비",
            "제국",
            "왕국",
            "이세계",
            "마왕",
            "소드마스터",
            "마도서",
            "귀족",
            "북부대공",
        ],
    },
    "genre_noise": {
        "weight": 5,
        "keywords": [
            "무협",
            "무림",
            "천마",
            "당가",
            "검귀",
            "검성",
            "헌터",
            "탑",
            "던전",
            "아포칼립스",
            "상태창",
            "마법사",
            "귀환한",
        ],
    },
}

STRONG_DIRECT_KEYWORDS = {
    "재벌",
    "후계자",
    "재무",
    "재무본부",
    "투자",
    "주식",
    "증권",
    "계좌",
    "수익률",
    "회사원",
    "사원",
    "대리",
    "팀장",
    "본부",
    "감사",
    "반도체",
    "빅테크",
    "ott",
    "디렉터",
    "ceo",
    "오너",
    "그룹",
    "대기업",
    "저작권료",
    "마트",
    "회장",
}

ADJACENT_INCLUDE_KEYWORDS = {
    "공무원",
    "감정사",
    "변호사",
    "작곡",
    "출판사",
    "인세",
    "엔지니어",
    "미국",
    "게임 개발",
}


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else (ROOT / path).resolve()


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip().lower()


def _normalize_title_for_key(title: str) -> str:
    base = re.sub(r"\[[^]]+\]", " ", title or "")
    base = re.sub(r"\([^)]*\)", " ", base)
    base = re.sub(r"\s+", " ", base)
    return base.strip().lower()


def _parse_badges(raw: str) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    visible: list[str] = []
    for item in data:
        text = str(item).strip()
        if not text:
            continue
        if re.search(r"[가-힣]", text):
            visible.append(text)
    return visible


def _looks_like_work(row: sqlite3.Row) -> bool:
    return any(
        [
            row["product_id"],
            row["creator"],
            row["genre_text"],
            row["subcategory"],
            row["intro_text"],
        ]
    )


def _build_work_key(row: sqlite3.Row) -> str:
    product_id = (row["product_id"] or "").strip()
    if product_id:
        return f"{row['platform']}:{product_id}"
    creator = _normalize_text(row["creator"] or "")
    normalized_title = _normalize_title_for_key(row["title"] or "")
    if creator:
        return f"{row['platform']}:title:{normalized_title}:creator:{creator}"
    return f"{row['platform']}:title:{normalized_title}"


def _collect_matches(text: str, keywords: list[str]) -> list[str]:
    return sorted({keyword for keyword in keywords if keyword in text})


def _score_row(row: sqlite3.Row) -> dict[str, Any]:
    badges = _parse_badges(row["badge_labels_json"])
    title = row["title"] or ""
    intro = row["intro_text"] or ""
    genre = row["genre_text"] or ""
    subcategory = row["subcategory"] or ""
    creator = row["creator"] or ""
    title_norm = _normalize_text(title)
    intro_norm = _normalize_text(intro)
    meta_norm = _normalize_text(" ".join([title, row["title_raw"] or "", intro, genre, subcategory, creator, " ".join(badges)]))
    genre_norm = _normalize_text(f"{genre} {subcategory}")

    positive_matches: dict[str, list[str]] = {}
    negative_matches: dict[str, list[str]] = {}
    positive_score = 0
    negative_score = 0

    for bucket, config in POSITIVE_BUCKETS.items():
        matches = _collect_matches(meta_norm, config["keywords"])
        if matches:
            positive_matches[bucket] = matches
            positive_score += len(matches) * int(config["weight"])

    genre_positive_hits: list[str] = []
    for token, weight in POSITIVE_GENRE_TOKENS.items():
        if token in genre_norm:
            genre_positive_hits.append(token)
            positive_score += weight
    if genre_positive_hits:
        positive_matches["genre_fit"] = sorted(set(genre_positive_hits))

    for bucket, config in NEGATIVE_BUCKETS.items():
        matches = _collect_matches(meta_norm, config["keywords"])
        if matches:
            negative_matches[bucket] = matches
            negative_score += len(matches) * int(config["weight"])

    title_direct_hits = sorted({keyword for keyword in STRONG_DIRECT_KEYWORDS if keyword in title_norm})
    if title_direct_hits:
        positive_matches["title_direct"] = title_direct_hits
        positive_score += len(title_direct_hits) * 4

    title_bucket_hits = {
        bucket: _collect_matches(title_norm, config["keywords"])
        for bucket, config in POSITIVE_BUCKETS.items()
    }
    title_bucket_hits = {bucket: hits for bucket, hits in title_bucket_hits.items() if hits}
    title_positive_bucket_count = sum(
        1
        for bucket in ("chaebol_power", "office_operator", "money_game", "industry_scale", "media_ip_business")
        if title_bucket_hits.get(bucket)
    )
    if title_bucket_hits:
        positive_matches["title_bucket_hits"] = {
            bucket: hits for bucket, hits in title_bucket_hits.items()
        }

    adjacent_hits = sorted({keyword for keyword in ADJACENT_INCLUDE_KEYWORDS if keyword in meta_norm})
    if adjacent_hits:
        positive_matches["adjacent_operator"] = adjacent_hits
        positive_score += len(adjacent_hits)

    if row["platform"] == "munpia" and "현대판타지" in genre_norm:
        positive_score += 2
    if row["platform"] == "kakaopage" and "현판" in genre_norm:
        positive_score += 2

    core_bucket_hits = sum(
        len(positive_matches.get(bucket, []))
        for bucket in ("chaebol_power", "office_operator", "money_game", "industry_scale", "media_ip_business")
    )
    is_romance_dominant = "romance_noise" in negative_matches and core_bucket_hits <= 2 and len(title_direct_hits) <= 1
    is_fantasy_dominant = (
        ("fantasy_noise" in negative_matches or "genre_noise" in negative_matches)
        and core_bucket_hits <= 1
        and len(title_direct_hits) == 0
        and "현대판타지" not in genre_norm
        and "현판" not in genre_norm
    )
    lacks_title_business_signal = title_positive_bucket_count == 0 and len(title_direct_hits) == 0

    relevance_score = positive_score - negative_score
    include = _looks_like_work(row) and (
        (
            relevance_score >= 8
            and (core_bucket_hits >= 1 or len(title_direct_hits) >= 1)
            and not is_romance_dominant
            and not is_fantasy_dominant
            and (
                not lacks_title_business_signal
                or "현대판타지" in genre_norm
                or "현판" in genre_norm
            )
        )
        or (
            len(title_direct_hits) >= 2
            and relevance_score >= 4
            and not is_romance_dominant
        )
    )

    if "romance_noise" in negative_matches and "현대판타지" not in genre_norm and "현판" not in genre_norm:
        include = False
    if not genre_norm and lacks_title_business_signal:
        include = False

    business_buckets = sorted(
        bucket
        for bucket in ("chaebol_power", "office_operator", "money_game", "industry_scale", "media_ip_business", "global_scale")
        if positive_matches.get(bucket)
    )
    if not business_buckets and positive_matches.get("adjacent_operator"):
        business_buckets = ["adjacent_operator"]

    return {
        "include": include,
        "relevance_score": relevance_score,
        "positive_score": positive_score,
        "negative_score": negative_score,
        "positive_matches": positive_matches,
        "negative_matches": negative_matches,
        "business_buckets": business_buckets,
        "core_bucket_hit_count": core_bucket_hits,
        "title_direct_hits": title_direct_hits,
        "title_bucket_hits": title_bucket_hits,
        "genre_norm": genre_norm,
        "is_romance_dominant": is_romance_dominant,
        "is_fantasy_dominant": is_fantasy_dominant,
    }


def _row_to_entry_doc(row: sqlite3.Row, score: dict[str, Any], work_id: str) -> dict[str, Any]:
    return {
        "entry_id": row["entry_id"],
        "work_id": work_id,
        "platform": row["platform"],
        "surface_id": row["surface_id"],
        "surface_label": row["surface_label"],
        "surface_kind": row["surface_kind"],
        "rank_in_surface": row["rank_in_surface"],
        "title": row["title"],
        "creator": row["creator"] or "",
        "genre_text": row["genre_text"] or "",
        "subcategory": row["subcategory"] or "",
        "date_text": row["date_text"] or "",
        "intro_text": row["intro_text"] or "",
        "promo_text": row["promo_text"] or "",
        "score_text": row["score_text"] or "",
        "product_id": row["product_id"] or "",
        "source_url": row["source_url"] or "",
        "source_surface_url": row["source_surface_url"] or "",
        "business_relevance_score": score["relevance_score"],
        "positive_score": score["positive_score"],
        "negative_score": score["negative_score"],
        "business_buckets": score["business_buckets"],
        "positive_matches": score["positive_matches"],
        "negative_matches": score["negative_matches"],
        "title_direct_hits": score["title_direct_hits"],
        "is_romance_dominant": score["is_romance_dominant"],
        "is_fantasy_dominant": score["is_fantasy_dominant"],
    }


def _merge_match_maps(target: dict[str, set[str]], source: dict[str, list[str]]) -> None:
    for key, values in source.items():
        target.setdefault(key, set()).update(values)


def _build_work_docs(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for entry in entries:
        work = grouped.setdefault(
            entry["work_id"],
            {
                "work_id": entry["work_id"],
                "platform": entry["platform"],
                "title": entry["title"],
                "creator": entry["creator"],
                "genre_text": entry["genre_text"],
                "subcategory": entry["subcategory"],
                "product_id": entry["product_id"],
                "source_url": entry["source_url"],
                "surface_labels": set(),
                "entry_ids": [],
                "surface_count": 0,
                "max_business_relevance_score": entry["business_relevance_score"],
                "avg_score_total": 0,
                "positive_matches": {},
                "negative_matches": {},
                "business_buckets": set(),
                "sample_intro": entry["intro_text"],
                "date_texts": set(),
            },
        )
        work["entry_ids"].append(entry["entry_id"])
        work["surface_labels"].add(entry["surface_label"])
        if entry["date_text"]:
            work["date_texts"].add(entry["date_text"])
        work["surface_count"] += 1
        work["avg_score_total"] += entry["business_relevance_score"]
        if entry["business_relevance_score"] > work["max_business_relevance_score"]:
            work["max_business_relevance_score"] = entry["business_relevance_score"]
            work["sample_intro"] = entry["intro_text"] or work["sample_intro"]
            if entry["genre_text"]:
                work["genre_text"] = entry["genre_text"]
            if entry["subcategory"]:
                work["subcategory"] = entry["subcategory"]
            if entry["source_url"]:
                work["source_url"] = entry["source_url"]
        _merge_match_maps(work["positive_matches"], entry["positive_matches"])
        _merge_match_maps(work["negative_matches"], entry["negative_matches"])
        work["business_buckets"].update(entry["business_buckets"])

    docs: list[dict[str, Any]] = []
    for work in grouped.values():
        entry_count = len(work["entry_ids"]) or 1
        docs.append(
            {
                "work_id": work["work_id"],
                "platform": work["platform"],
                "title": work["title"],
                "creator": work["creator"],
                "genre_text": work["genre_text"],
                "subcategory": work["subcategory"],
                "product_id": work["product_id"],
                "source_url": work["source_url"],
                "surface_count": work["surface_count"],
                "surface_labels": sorted(work["surface_labels"]),
                "entry_ids": work["entry_ids"],
                "max_business_relevance_score": work["max_business_relevance_score"],
                "avg_business_relevance_score": round(work["avg_score_total"] / entry_count, 2),
                "business_buckets": sorted(work["business_buckets"]),
                "positive_matches": {key: sorted(values) for key, values in sorted(work["positive_matches"].items())},
                "negative_matches": {key: sorted(values) for key, values in sorted(work["negative_matches"].items())},
                "sample_intro": work["sample_intro"] or "",
                "date_texts": sorted(work["date_texts"]),
            }
        )
    docs.sort(
        key=lambda item: (
            -item["surface_count"],
            -item["max_business_relevance_score"],
            item["platform"],
            item["title"],
        )
    )
    return docs


def _build_rollup(entries: list[dict[str, Any]], works: list[dict[str, Any]]) -> dict[str, Any]:
    platform_entry_counts = Counter(entry["platform"] for entry in entries)
    platform_work_counts = Counter(work["platform"] for work in works)
    bucket_entry_counts = Counter()
    bucket_work_counts = Counter()
    keyword_counts = Counter()
    direct_keyword_counts = Counter()

    for entry in entries:
        for bucket in entry["business_buckets"]:
            bucket_entry_counts[(entry["platform"], bucket)] += 1
            bucket_entry_counts[("__all__", bucket)] += 1
        for values in entry["positive_matches"].values():
            if isinstance(values, dict):
                for nested_values in values.values():
                    keyword_counts.update(nested_values)
            else:
                keyword_counts.update(values)
        direct_keyword_counts.update(entry["title_direct_hits"])

    for work in works:
        for bucket in work["business_buckets"]:
            bucket_work_counts[(work["platform"], bucket)] += 1
            bucket_work_counts[("__all__", bucket)] += 1

    def _bucket_view(counter: Counter[tuple[str, str]]) -> dict[str, list[dict[str, Any]]]:
        by_platform: dict[str, list[dict[str, Any]]] = {}
        for platform in sorted({platform for platform, _ in counter.keys()}):
            rows = [
                {"bucket": bucket, "count": count}
                for (plat, bucket), count in counter.items()
                if plat == platform
            ]
            rows.sort(key=lambda item: (-item["count"], item["bucket"]))
            by_platform[platform] = rows
        return by_platform

    top_works = [
        {
            "platform": work["platform"],
            "title": work["title"],
            "surface_count": work["surface_count"],
            "max_business_relevance_score": work["max_business_relevance_score"],
            "business_buckets": work["business_buckets"],
        }
        for work in works[:30]
    ]

    return {
        "_schema_version": "business_trend_slice_rollup.v1",
        "input_corpus": str(DEFAULT_INPUT_DB.relative_to(ROOT)).replace("\\", "/"),
        "entry_count": len(entries),
        "work_count": len(works),
        "entry_counts_by_platform": dict(sorted(platform_entry_counts.items())),
        "work_counts_by_platform": dict(sorted(platform_work_counts.items())),
        "entry_bucket_counts": _bucket_view(bucket_entry_counts),
        "work_bucket_counts": _bucket_view(bucket_work_counts),
        "top_positive_keywords": [
            {"keyword": keyword, "count": count}
            for keyword, count in keyword_counts.most_common(80)
        ],
        "top_title_direct_keywords": [
            {"keyword": keyword, "count": count}
            for keyword, count in direct_keyword_counts.most_common(40)
        ],
        "top_works_by_surface_coverage": top_works,
    }


def _build_schema(schema_path: Path) -> dict[str, Any]:
    return {
        "_schema_version": "business_trend_slice_schema.v1",
        "schema_path": str(schema_path.relative_to(ROOT)).replace("\\", "/"),
        "purpose": "Material-side slice for modern business / office-power / chaebol-adjacent trends from KR serial platforms.",
        "authority_note": "Python only filters and formats transparent signals. Final relevance and concept judgment stay on the LLM side.",
        "entry_fields": {
            "business_relevance_score": "positive exact-match score minus noise penalty",
            "business_buckets": "matched lanes such as chaebol_power / office_operator / money_game / industry_scale / media_ip_business",
            "positive_matches": "transparent include-side keyword hits grouped by bucket",
            "negative_matches": "transparent noise-side keyword hits grouped by bucket",
            "title_direct_hits": "strong direct packaging words seen in the title itself",
        },
        "work_fields": {
            "surface_count": "how many platform surfaces repeated this work in the slice",
            "max_business_relevance_score": "best entry-level score across duplicated surfaces",
            "avg_business_relevance_score": "mean score across duplicated surfaces",
            "surface_labels": "which screens surfaced the work",
        },
    }


def _create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP TABLE IF EXISTS entries;
        DROP TABLE IF EXISTS works;
        CREATE TABLE entries (
            entry_id TEXT PRIMARY KEY,
            work_id TEXT NOT NULL,
            platform TEXT NOT NULL,
            surface_id TEXT NOT NULL,
            surface_label TEXT NOT NULL,
            surface_kind TEXT NOT NULL,
            rank_in_surface INTEGER,
            title TEXT NOT NULL,
            creator TEXT,
            genre_text TEXT,
            subcategory TEXT,
            date_text TEXT,
            intro_text TEXT,
            promo_text TEXT,
            score_text TEXT,
            product_id TEXT,
            source_url TEXT,
            source_surface_url TEXT,
            business_relevance_score INTEGER NOT NULL,
            positive_score INTEGER NOT NULL,
            negative_score INTEGER NOT NULL,
            business_buckets_json TEXT NOT NULL,
            positive_matches_json TEXT NOT NULL,
            negative_matches_json TEXT NOT NULL,
            title_direct_hits_json TEXT NOT NULL,
            is_romance_dominant INTEGER NOT NULL,
            is_fantasy_dominant INTEGER NOT NULL
        );
        CREATE TABLE works (
            work_id TEXT PRIMARY KEY,
            platform TEXT NOT NULL,
            title TEXT NOT NULL,
            creator TEXT,
            genre_text TEXT,
            subcategory TEXT,
            product_id TEXT,
            source_url TEXT,
            surface_count INTEGER NOT NULL,
            surface_labels_json TEXT NOT NULL,
            entry_ids_json TEXT NOT NULL,
            max_business_relevance_score REAL NOT NULL,
            avg_business_relevance_score REAL NOT NULL,
            business_buckets_json TEXT NOT NULL,
            positive_matches_json TEXT NOT NULL,
            negative_matches_json TEXT NOT NULL,
            sample_intro TEXT,
            date_texts_json TEXT NOT NULL
        );
        """
    )
    conn.commit()


def _write_db(path: Path, entries: list[dict[str, Any]], works: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    _create_schema(conn)
    conn.executemany(
        """
        INSERT INTO entries (
            entry_id, work_id, platform, surface_id, surface_label, surface_kind, rank_in_surface,
            title, creator, genre_text, subcategory, date_text, intro_text, promo_text, score_text,
            product_id, source_url, source_surface_url, business_relevance_score, positive_score,
            negative_score, business_buckets_json, positive_matches_json, negative_matches_json,
            title_direct_hits_json, is_romance_dominant, is_fantasy_dominant
        ) VALUES (
            :entry_id, :work_id, :platform, :surface_id, :surface_label, :surface_kind, :rank_in_surface,
            :title, :creator, :genre_text, :subcategory, :date_text, :intro_text, :promo_text, :score_text,
            :product_id, :source_url, :source_surface_url, :business_relevance_score, :positive_score,
            :negative_score, :business_buckets_json, :positive_matches_json, :negative_matches_json,
            :title_direct_hits_json, :is_romance_dominant, :is_fantasy_dominant
        )
        """,
        [
            {
                **entry,
                "business_buckets_json": json.dumps(entry["business_buckets"], ensure_ascii=False),
                "positive_matches_json": json.dumps(entry["positive_matches"], ensure_ascii=False),
                "negative_matches_json": json.dumps(entry["negative_matches"], ensure_ascii=False),
                "title_direct_hits_json": json.dumps(entry["title_direct_hits"], ensure_ascii=False),
                "is_romance_dominant": int(entry["is_romance_dominant"]),
                "is_fantasy_dominant": int(entry["is_fantasy_dominant"]),
            }
            for entry in entries
        ],
    )
    conn.executemany(
        """
        INSERT INTO works (
            work_id, platform, title, creator, genre_text, subcategory, product_id, source_url,
            surface_count, surface_labels_json, entry_ids_json, max_business_relevance_score,
            avg_business_relevance_score, business_buckets_json, positive_matches_json,
            negative_matches_json, sample_intro, date_texts_json
        ) VALUES (
            :work_id, :platform, :title, :creator, :genre_text, :subcategory, :product_id, :source_url,
            :surface_count, :surface_labels_json, :entry_ids_json, :max_business_relevance_score,
            :avg_business_relevance_score, :business_buckets_json, :positive_matches_json,
            :negative_matches_json, :sample_intro, :date_texts_json
        )
        """,
        [
            {
                **work,
                "surface_labels_json": json.dumps(work["surface_labels"], ensure_ascii=False),
                "entry_ids_json": json.dumps(work["entry_ids"], ensure_ascii=False),
                "business_buckets_json": json.dumps(work["business_buckets"], ensure_ascii=False),
                "positive_matches_json": json.dumps(work["positive_matches"], ensure_ascii=False),
                "negative_matches_json": json.dumps(work["negative_matches"], ensure_ascii=False),
                "date_texts_json": json.dumps(work["date_texts"], ensure_ascii=False),
            }
            for work in works
        ],
    )
    conn.commit()
    conn.close()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-db", type=Path, default=DEFAULT_INPUT_DB)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    input_db = _resolve(args.input_db)
    output_root = _resolve(args.output_root)

    conn = sqlite3.connect(input_db)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM entries ORDER BY platform, surface_id, rank_in_surface, entry_id").fetchall()
    conn.close()

    included_entries: list[dict[str, Any]] = []
    for row in rows:
        score = _score_row(row)
        if not score["include"]:
            continue
        work_id = _build_work_key(row)
        included_entries.append(_row_to_entry_doc(row, score, work_id))

    included_entries.sort(
        key=lambda item: (
            -item["business_relevance_score"],
            item["platform"],
            item["title"],
            item["entry_id"],
        )
    )
    works = _build_work_docs(included_entries)
    rollup = _build_rollup(included_entries, works)
    schema = _build_schema(output_root / "business_slice_schema.json")

    output_root.mkdir(parents=True, exist_ok=True)
    _write_json(output_root / "business_slice_schema.json", schema)
    _write_jsonl(output_root / "business_trend_entries.jsonl", included_entries)
    _write_jsonl(output_root / "business_trend_works.jsonl", works)
    _write_json(output_root / "business_trend_rollup.json", rollup)
    _write_json(
        output_root / "collection_status.json",
        {
            "_schema_version": "business_trend_slice_status.v1",
            "input_db": str(input_db.relative_to(ROOT)).replace("\\", "/"),
            "output_root": str(output_root.relative_to(ROOT)).replace("\\", "/"),
            "entry_count": len(included_entries),
            "work_count": len(works),
            "notes": [
                "Slice uses transparent keyword scoring only.",
                "Positive/negative keyword groups are declared in the script and written through to JSONL/SQLite.",
                "Final concept judgment stays on the LLM side.",
            ],
        },
    )
    _write_db(output_root / "business_trend_slice.sqlite3", included_entries, works)

    print(f"Business trend entries: {len(included_entries)}")
    print(f"Business trend works: {len(works)}")
    print(f"Input DB: {input_db}")
    print(f"Output root: {output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
