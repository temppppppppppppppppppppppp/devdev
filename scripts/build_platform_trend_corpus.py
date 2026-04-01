# -*- coding: utf-8 -*-
"""Build a public-platform trend corpus for Korean serial novel platforms.

Collection only:
- requests public HTML / embedded JSON
- saves raw snapshots
- normalizes visible title/copy/badge/date signals into SQLite + JSONL
- computes lightweight exact-count rollups without judging idea quality

LLM-side work happens later:
- interpreting the signals
- deciding what is trend vs. noise
- converting platform packaging into usable concept engines
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = (
    ROOT
    / "narrative_ssot"
    / "10_reference_bank"
    / "source_corpora"
    / "platform_trends"
    / "kr_serial_platforms"
)
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/135.0.0.0 Safari/537.36"
)
HEADERS = {"User-Agent": USER_AGENT}
KAKAO_MENU_UID = 10011
KAKAO_SCREEN_IDS = [63, 64, 68, 70, 73, 74, 76, 84, 85, 90, 91, 92, 94, 101, 105, 181]
TREND_CUES = [
    "회귀",
    "천재",
    "재벌",
    "후계자",
    "망나니",
    "회사",
    "대기업",
    "투자",
    "돈",
    "미국",
    "빅테크",
    "AI",
    "반도체",
    "감정사",
    "변호사",
    "의사",
    "공무원",
    "배우",
    "작곡",
    "디렉터",
    "탑스타",
    "무당",
    "헌터",
    "각성",
    "귀환",
    "아포칼립스",
    "탑",
    "상태창",
    "계약",
    "코인",
    "로또",
    "중동",
    "독재자",
    "게임",
    "OTT",
    "현판",
    "무협",
    "판타지",
]
TITLE_SIGNAL_STOPWORDS = {
    "독점",
    "단행본",
    "선공개",
    "bl",
    "19세",
    "완전판",
    "무료연재",
    "신규",
    "신작",
    "시리즈",
    "에디션",
    "외전",
    "4월",
    "3월",
    "매일10시무료",
    "무료",
    "연재",
    "완결",
    "미완결",
    "선",
}


@dataclass(slots=True)
class CrawlConfig:
    output_root: Path
    request_pause_seconds: float
    naver_recent_pages: int
    naver_recommend_pages: int
    naver_category_pages: int
    naver_special_pages: int
    skip_raw: bool


def _assert_within_workspace(path: Path) -> None:
    resolved_root = ROOT.resolve()
    resolved_path = path.resolve()
    if resolved_root not in [resolved_path, *resolved_path.parents]:
        raise RuntimeError(f"Path escaped workspace root: {resolved_path}")


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _extract_digits(text: str) -> str:
    return "".join(re.findall(r"\d+", text))


def _extract_product_no(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    values = query.get("productNo")
    if values:
        return values[0]
    match = re.search(r"productNo=(\d+)", url)
    return match.group(1) if match else ""


def _tokenize_title(text: str) -> list[str]:
    tokens = re.findall(r"[0-9A-Za-z가-힣%]+", text)
    normalized: list[str] = []
    for token in tokens:
        low = token.lower()
        if len(low) >= 2 or low in {"ai", "bl"}:
            normalized.append(low)
    return normalized


def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def _save_raw_html(config: CrawlConfig, *, platform: str, surface_id: str, html: str) -> str:
    raw_path = config.output_root / "raw" / platform / f"{surface_id}.html"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(html, encoding="utf-8")
    return str(raw_path.relative_to(ROOT)).replace("\\", "/")


def _fetch(session: requests.Session, config: CrawlConfig, *, platform: str, surface_id: str, url: str) -> tuple[str, str]:
    response = session.get(url, timeout=30)
    response.raise_for_status()
    html = response.text
    raw_rel = ""
    if not config.skip_raw:
        raw_rel = _save_raw_html(config, platform=platform, surface_id=surface_id, html=html)
    time.sleep(config.request_pause_seconds)
    return html, raw_rel


def _naver_list_entry(card: Any, *, platform: str, surface_id: str, surface_label: str, source_url: str, rank_in_surface: int) -> dict[str, Any]:
    link = card.select_one("h3 a[href]") or card.select_one("a.pic[href]")
    href = link.get("href", "") if link else ""
    full_url = urljoin("https://series.naver.com", href)
    title_text = link.get_text(" ", strip=True) if link else ""
    badges = [_clean_text(node.get_text(" ", strip=True)) for node in card.select("h3 em, a.pic em.ico, a.pic em.sticker") if _clean_text(node.get_text(" ", strip=True))]
    info = card.select_one("p.info")
    author = _clean_text(info.select_one(".author").get_text(" ", strip=True)) if info and info.select_one(".author") else ""
    score = _clean_text(info.select_one(".score_num").get_text(" ", strip=True)) if info and info.select_one(".score_num") else ""
    free_info = _clean_text(info.select_one(".free_info").get_text(" ", strip=True)) if info and info.select_one(".free_info") else ""
    info_text = _clean_text(info.get_text(" ", strip=True)) if info else ""
    date_match = re.search(r"\d{4}\.\d{2}\.\d{2}\.", info_text)
    date_text = date_match.group(0) if date_match else ""
    description = _clean_text(card.select_one("p.dsc").get_text(" ", strip=True)) if card.select_one("p.dsc") else ""
    image = card.select_one("a.pic img")
    image_alt = image.get("alt", "") if image else ""
    title_base = re.sub(r"\([^)]*\)\s*$", "", title_text).strip()
    return {
        "platform": platform,
        "surface_id": surface_id,
        "surface_label": surface_label,
        "surface_kind": "list",
        "rank_in_surface": rank_in_surface,
        "title": title_base or image_alt or title_text,
        "title_raw": title_text,
        "creator": author,
        "genre_text": "",
        "date_text": date_text,
        "score_text": score,
        "promo_text": free_info,
        "intro_text": description,
        "badge_labels": badges,
        "product_id": _extract_product_no(full_url),
        "entry_type": "title_card",
        "subcategory": "",
        "source_url": full_url or source_url,
        "source_surface_url": source_url,
    }


def _parse_naver_recent_like(html: str, *, surface_id: str, surface_label: str, source_url: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("ul.lst_list li")
    rows: list[dict[str, Any]] = []
    for index, card in enumerate(cards, start=1):
        rows.append(
            _naver_list_entry(
                card,
                platform="naver_series",
                surface_id=surface_id,
                surface_label=surface_label,
                source_url=source_url,
                rank_in_surface=index,
            )
        )
    return rows


def _parse_naver_top100(html: str, *, source_url: str, surface_id: str, surface_label: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict[str, Any]] = []
    for index, card in enumerate(soup.select(".top100 li"), start=1):
        title_link = card.select_one("h3 a[href]")
        if not title_link:
            continue
        href = title_link.get("href", "")
        full_url = urljoin("https://series.naver.com", href)
        badges = [_clean_text(node.get_text(" ", strip=True)) for node in card.select("h3 em, a.pic em.ico, a.pic em.sticker") if _clean_text(node.get_text(" ", strip=True))]
        info = card.select_one(".comic_cont p.info")
        author = _clean_text(info.select_one(".author").get_text(" ", strip=True)) if info and info.select_one(".author") else ""
        score = _clean_text(info.select_one(".score_num").get_text(" ", strip=True)) if info and info.select_one(".score_num") else ""
        genre = _clean_text(info.select_one(".genre").get_text(" ", strip=True)) if info and info.select_one(".genre") else ""
        rank_text = _clean_text(card.select_one(".top_num").get_text(" ", strip=True)) if card.select_one(".top_num") else str(index)
        rows.append(
            {
                "platform": "naver_series",
                "surface_id": surface_id,
                "surface_label": surface_label,
                "surface_kind": "ranking",
                "rank_in_surface": int(_extract_digits(rank_text) or index),
                "title": re.sub(r"\([^)]*\)\s*$", "", title_link.get_text(" ", strip=True)).strip(),
                "title_raw": title_link.get_text(" ", strip=True),
                "creator": author,
                "genre_text": genre,
                "date_text": "",
                "score_text": score,
                "promo_text": "",
                "intro_text": "",
                "badge_labels": badges,
                "product_id": _extract_product_no(full_url),
                "entry_type": "top100_card",
                "subcategory": "",
                "source_url": full_url,
                "source_surface_url": source_url,
            }
        )
    return rows


def build_naver_surfaces(config: CrawlConfig) -> list[dict[str, Any]]:
    surfaces: list[dict[str, Any]] = []
    for page in range(1, config.naver_recent_pages + 1):
        surfaces.append(
            {
                "platform": "naver_series",
                "surface_id": f"naver_recent_p{page}",
                "surface_label": f"recentList.page{page}",
                "surface_type": "recent",
                "url": f"https://series.naver.com/novel/recentList.series?page={page}",
                "parser": "naver_recent_like",
            }
        )
    surfaces.append(
        {
            "platform": "naver_series",
            "surface_id": "naver_top100",
            "surface_label": "top100",
            "surface_type": "ranking",
            "url": "https://series.naver.com/novel/top100List.series",
            "parser": "naver_top100",
        }
    )
    for page in range(1, config.naver_recommend_pages + 1):
        surfaces.append(
            {
                "platform": "naver_series",
                "surface_id": f"naver_recommend_p{page}",
                "surface_label": f"recommendList.page{page}",
                "surface_type": "recommend",
                "url": f"https://series.naver.com/novel/recommendList.series?page={page}",
                "parser": "naver_recent_like",
            }
        )
    for genre_code, genre_label in [("201", "romance"), ("202", "fantasy"), ("207", "ropan")]:
        for page in range(1, config.naver_category_pages + 1):
            surfaces.append(
                {
                    "platform": "naver_series",
                    "surface_id": f"naver_genre_{genre_label}_p{page}",
                    "surface_label": f"genre.{genre_label}.page{page}",
                    "surface_type": "genre",
                    "url": f"https://series.naver.com/novel/categoryProductList.series?categoryTypeCode=genre&genreCode={genre_code}&page={page}",
                    "parser": "naver_recent_like",
                }
            )
    for free_code, label in [("HOURLYFREE", "freepass"), ("FREEFROMTODAY", "daily10free"), ("TIMEDEAL", "timedeal")]:
        for page in range(1, config.naver_special_pages + 1):
            surfaces.append(
                {
                    "platform": "naver_series",
                    "surface_id": f"naver_special_{label}_p{page}",
                    "surface_label": f"special.{label}.page{page}",
                    "surface_type": "special",
                    "url": f"https://series.naver.com/novel/specialFreeList.series?specialFreeTypeCode={free_code}&page={page}",
                    "parser": "naver_recent_like",
                }
            )
    return surfaces


def _munpia_card_entry(card: Any, *, surface_id: str, surface_label: str, source_url: str, rank_in_surface: int, entry_type: str) -> dict[str, Any] | None:
    title_node = card.select_one(".novel-title")
    if not title_node:
        title_node = card.select_one(".title strong")
    title = _clean_text(title_node.get_text(" ", strip=True)) if title_node else ""
    if not title:
        return None
    href = ""
    if card.name == "a":
        href = card.get("href", "")
    elif card.select_one("a[href]"):
        href = card.select_one("a[href]").get("href", "")
    full_url = urljoin("https://novel.munpia.com", href)
    genre = _clean_text(card.select_one(".novel-genre").get_text(" ", strip=True)) if card.select_one(".novel-genre") else _clean_text(card.select_one(".genre").get_text(" ", strip=True)) if card.select_one(".genre") else ""
    author = _clean_text(card.select_one(".novel-author").get_text(" ", strip=True)) if card.select_one(".novel-author") else _clean_text(card.select_one(".author").get_text(" ", strip=True)) if card.select_one(".author") else ""
    rank_text = _clean_text(card.select_one(".rank-num").get_text(" ", strip=True)) if card.select_one(".rank-num") else str(rank_in_surface)
    product_id_match = re.search(r"/(\d+)$", href)
    return {
        "platform": "munpia",
        "surface_id": surface_id,
        "surface_label": surface_label,
        "surface_kind": "ranking" if "best" in surface_id else "home",
        "rank_in_surface": int(_extract_digits(rank_text) or rank_in_surface),
        "title": title,
        "title_raw": title,
        "creator": author,
        "genre_text": genre,
        "date_text": "",
        "score_text": "",
        "promo_text": "",
        "intro_text": "",
        "badge_labels": [],
        "product_id": product_id_match.group(1) if product_id_match else "",
        "entry_type": entry_type,
        "subcategory": "",
        "source_url": full_url or source_url,
        "source_surface_url": source_url,
    }


def _parse_munpia_home(html: str, *, source_url: str, surface_id: str, surface_label: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for tab_id in ["BEST-NOVEL-PRO", "BEST-NOVEL-REGULAR", "BEST-NOVEL-FREE"]:
        section = soup.select_one(f"#{tab_id}")
        if not section:
            continue
        for index, li in enumerate(section.select("ul > li"), start=1):
            row = _munpia_card_entry(
                li,
                surface_id=surface_id,
                surface_label=f"{surface_label}.{tab_id.lower()}",
                source_url=source_url,
                rank_in_surface=index,
                entry_type="home_spotlight",
            )
            if not row:
                continue
            key = (row["title"], row["source_url"])
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)
    for index, anchor in enumerate(soup.select(".top-banner-slide a"), start=1):
        image = anchor.select_one("img")
        title = image.get("alt", "").strip() if image else ""
        if not title:
            continue
        rows.append(
            {
                "platform": "munpia",
                "surface_id": surface_id,
                "surface_label": f"{surface_label}.top_banner",
                "surface_kind": "promotion",
                "rank_in_surface": index,
                "title": title,
                "title_raw": title,
                "creator": "",
                "genre_text": "",
                "date_text": "",
                "score_text": "",
                "promo_text": "",
                "intro_text": "",
                "badge_labels": [],
                "product_id": "",
                "entry_type": "home_banner",
                "subcategory": "",
                "source_url": urljoin("https://www.munpia.com", anchor.get("href", "")),
                "source_surface_url": source_url,
            }
        )
    return rows


def _parse_munpia_best(html: str, *, source_url: str, surface_id: str, surface_label: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for index, card in enumerate(soup.select("a.novel-wrap"), start=1):
        row = _munpia_card_entry(
            card,
            surface_id=surface_id,
            surface_label=surface_label,
            source_url=source_url,
            rank_in_surface=index,
            entry_type="best_card",
        )
        if not row:
            continue
        key = (row["title"], row["source_url"])
        if key in seen:
            continue
        seen.add(key)
        rows.append(row)
    return rows


def _parse_munpia_event_list(html: str, *, source_url: str, surface_id: str, surface_label: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict[str, Any]] = []
    for index, card in enumerate(soup.select(".event-list"), start=1):
        title = _clean_text(card.select_one(".event-title").get_text(" ", strip=True)) if card.select_one(".event-title") else ""
        if not title:
            continue
        desc = _clean_text(card.select_one(".event-discript").get_text(" ", strip=True)) if card.select_one(".event-discript") else ""
        href = card.select_one("a[href]").get("href", "") if card.select_one("a[href]") else ""
        rows.append(
            {
                "platform": "munpia",
                "surface_id": surface_id,
                "surface_label": surface_label,
                "surface_kind": "event",
                "rank_in_surface": index,
                "title": title,
                "title_raw": title,
                "creator": "",
                "genre_text": "",
                "date_text": desc,
                "score_text": "",
                "promo_text": desc,
                "intro_text": "",
                "badge_labels": [],
                "product_id": "",
                "entry_type": "event_card",
                "subcategory": "",
                "source_url": urljoin("https://www.munpia.com", href),
                "source_surface_url": source_url,
            }
        )
    return rows


def build_munpia_surfaces() -> list[dict[str, Any]]:
    return [
        {
            "platform": "munpia",
            "surface_id": "munpia_home",
            "surface_label": "home",
            "surface_type": "home",
            "url": "https://novel.munpia.com/",
            "parser": "munpia_home",
        },
        {
            "platform": "munpia",
            "surface_id": "munpia_best_newbie",
            "surface_label": "best.newbie",
            "surface_type": "ranking",
            "url": "https://www.munpia.com/page/j/view/w/best/plsa.newbie",
            "parser": "munpia_best",
        },
        {
            "platform": "munpia",
            "surface_id": "munpia_best_finish",
            "surface_label": "best.finish",
            "surface_type": "ranking",
            "url": "https://www.munpia.com/page/j/view/w/best/plsa.finish",
            "parser": "munpia_best",
        },
        {
            "platform": "munpia",
            "surface_id": "munpia_event_list",
            "surface_label": "event.list",
            "surface_type": "event",
            "url": "https://www.munpia.com/page/j/view/s/event/list",
            "parser": "munpia_event_list",
        },
    ]


def _extract_next_data(html: str) -> dict[str, Any]:
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
    if not match:
        raise RuntimeError("Missing __NEXT_DATA__ block")
    return json.loads(match.group(1))


def _kakao_event_url_from_scheme(scheme: str) -> str:
    match = re.search(r"hash_uid=([a-zA-Z0-9]+)", scheme)
    if match:
        return f"https://page.kakao.com/event/{match.group(1)}"
    return ""


def _kakao_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if isinstance(item, str):
                cleaned = _clean_text(item)
                if cleaned:
                    out.append(cleaned)
            elif isinstance(item, dict):
                text = _clean_text(item.get("title", "") or item.get("name", "") or item.get("value", ""))
                if text:
                    out.append(text)
        return out
    if isinstance(value, str):
        cleaned = _clean_text(value)
        return [cleaned] if cleaned else []
    return []


def _parse_kakao_item(
    item: dict[str, Any],
    *,
    surface_id: str,
    surface_label: str,
    source_url: str,
    section_type: str,
    group_type: str,
    rank_in_surface: int,
) -> dict[str, Any] | None:
    event_meta = (item.get("eventLog") or {}).get("eventMeta") or {}
    title = _clean_text(item.get("title", "") or event_meta.get("name", "") or item.get("altText", ""))
    if not title:
        return None
    scheme = item.get("scheme", "")
    source_item_url = _kakao_event_url_from_scheme(scheme) or source_url
    badges = _kakao_string_list(item.get("badgeList")) + _kakao_string_list(item.get("metaList"))
    if isinstance(item.get("statusBadge"), dict):
        badges.extend(_kakao_string_list(item["statusBadge"].get("text")))
    series_id = str(event_meta.get("series_id") or item.get("seriesId") or "")
    subtitle = _clean_text(item.get("subtitle", "") or item.get("caption", "") or item.get("description", ""))
    entry_type = item.get("type", "")
    return {
        "platform": "kakaopage",
        "surface_id": surface_id,
        "surface_label": surface_label,
        "surface_kind": section_type,
        "rank_in_surface": rank_in_surface,
        "title": title,
        "title_raw": title,
        "creator": "",
        "genre_text": event_meta.get("subcategory", "") or "",
        "date_text": "",
        "score_text": "",
        "promo_text": subtitle,
        "intro_text": subtitle,
        "badge_labels": badges,
        "product_id": series_id,
        "entry_type": entry_type or group_type,
        "subcategory": event_meta.get("subcategory", "") or "",
        "source_url": source_item_url,
        "source_surface_url": source_url,
    }


def _parse_kakao_surface(html: str, *, source_url: str, surface_id: str, surface_label: str) -> list[dict[str, Any]]:
    obj = _extract_next_data(html)
    data = obj["props"]["pageProps"]["initialProps"]["dehydratedState"]["queries"][0]["state"]["data"]
    rows: list[dict[str, Any]] = []
    for section_index, section in enumerate(data.get("sections") or [], start=1):
        section_type = section.get("type", f"section_{section_index}")
        for group_index, group in enumerate(section.get("groups") or [], start=1):
            group_type = group.get("type", f"group_{group_index}")
            for item_index, item in enumerate(group.get("items") or [], start=1):
                if not isinstance(item, dict):
                    continue
                row = _parse_kakao_item(
                    item,
                    surface_id=surface_id,
                    surface_label=surface_label,
                    source_url=source_url,
                    section_type=section_type,
                    group_type=group_type,
                    rank_in_surface=item_index,
                )
                if row:
                    rows.append(row)
    return rows


def build_kakao_surfaces(session: requests.Session, config: CrawlConfig) -> list[dict[str, Any]]:
    root_url = f"https://page.kakao.com/menu/{KAKAO_MENU_UID}"
    html, raw_rel = _fetch(session, config, platform="kakaopage", surface_id="kakaopage_root", url=root_url)
    obj = _extract_next_data(html)
    discovered: dict[int, str] = {}
    queue: list[Any] = [obj]
    while queue:
        current = queue.pop()
        if isinstance(current, dict):
            if current.get("type") in ("SUBTAB", "LANDING") and isinstance(current.get("id"), str):
                screen_id = _extract_digits(current["id"])
                if screen_id:
                    discovered[int(screen_id)] = current.get("title", "")
            queue.extend(current.values())
        elif isinstance(current, list):
            queue.extend(current)

    surfaces: list[dict[str, Any]] = [
        {
            "platform": "kakaopage",
            "surface_id": "kakaopage_root",
            "surface_label": "menu.root",
            "surface_type": "root",
            "url": root_url,
            "parser": "kakao_surface",
            "raw_path": raw_rel,
        }
    ]
    for screen_id in KAKAO_SCREEN_IDS:
        title = discovered.get(screen_id, "")
        surfaces.append(
            {
                "platform": "kakaopage",
                "surface_id": f"kakaopage_screen_{screen_id}",
                "surface_label": title or f"screen.{screen_id}",
                "surface_type": "screen",
                "url": f"https://page.kakao.com/menu/{KAKAO_MENU_UID}/screen/{screen_id}",
                "parser": "kakao_surface",
                "requested_screen_id": screen_id,
            }
        )
    return surfaces


def _create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA journal_mode=WAL;
        DROP TABLE IF EXISTS surfaces;
        DROP TABLE IF EXISTS entries;
        CREATE TABLE surfaces (
            surface_id TEXT PRIMARY KEY,
            platform TEXT NOT NULL,
            surface_label TEXT NOT NULL,
            surface_type TEXT NOT NULL,
            source_url TEXT NOT NULL,
            raw_path TEXT,
            parser TEXT NOT NULL,
            entry_count INTEGER NOT NULL,
            collected_at_utc TEXT NOT NULL
        );
        CREATE TABLE entries (
            entry_id TEXT PRIMARY KEY,
            platform TEXT NOT NULL,
            surface_id TEXT NOT NULL,
            surface_label TEXT NOT NULL,
            surface_kind TEXT NOT NULL,
            rank_in_surface INTEGER,
            title TEXT NOT NULL,
            title_raw TEXT,
            creator TEXT,
            genre_text TEXT,
            date_text TEXT,
            score_text TEXT,
            promo_text TEXT,
            intro_text TEXT,
            badge_labels_json TEXT,
            product_id TEXT,
            entry_type TEXT,
            subcategory TEXT,
            source_url TEXT,
            source_surface_url TEXT
        );
        """
    )


def _parser_dispatch(parser_name: str):
    return {
        "naver_recent_like": _parse_naver_recent_like,
        "naver_top100": _parse_naver_top100,
        "munpia_home": _parse_munpia_home,
        "munpia_best": _parse_munpia_best,
        "munpia_event_list": _parse_munpia_event_list,
        "kakao_surface": _parse_kakao_surface,
    }[parser_name]


def _collect_entries(session: requests.Session, config: CrawlConfig) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    surfaces = build_naver_surfaces(config) + build_munpia_surfaces() + build_kakao_surfaces(session, config)
    surface_rows: list[dict[str, Any]] = []
    entry_rows: list[dict[str, Any]] = []
    for surface in surfaces:
        platform = surface["platform"]
        surface_id = surface["surface_id"]
        raw_rel = surface.get("raw_path", "")
        html, fetched_raw_rel = _fetch(
            session,
            config,
            platform=platform,
            surface_id=surface_id,
            url=surface["url"],
        )
        if fetched_raw_rel:
            raw_rel = fetched_raw_rel
        parser = _parser_dispatch(surface["parser"])
        parsed = parser(
            html,
            source_url=surface["url"],
            surface_id=surface_id,
            surface_label=surface["surface_label"],
        )
        for index, row in enumerate(parsed, start=1):
            row["entry_id"] = f"{surface_id}:{index}"
            entry_rows.append(row)
        surface_rows.append(
            {
                "surface_id": surface_id,
                "platform": platform,
                "surface_label": surface["surface_label"],
                "surface_type": surface["surface_type"],
                "source_url": surface["url"],
                "raw_path": raw_rel,
                "parser": surface["parser"],
                "entry_count": len(parsed),
                "collected_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        )
    return surface_rows, entry_rows


def _build_rollups(entries: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    token_counts: dict[str, Counter[str]] = defaultdict(Counter)
    signal_token_counts: dict[str, Counter[str]] = defaultdict(Counter)
    cue_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in entries:
        if not any([row.get("product_id"), row.get("creator"), row.get("genre_text"), row.get("subcategory")]):
            continue
        platform = row["platform"]
        title = row["title"]
        for token in _tokenize_title(title):
            token_counts[platform][token] += 1
            token_counts["__all__"][token] += 1
            if token not in TITLE_SIGNAL_STOPWORDS:
                signal_token_counts[platform][token] += 1
                signal_token_counts["__all__"][token] += 1
        title_lower = title.lower()
        for cue in TREND_CUES:
            if cue.lower() in title_lower:
                cue_counts[platform][cue] += 1
                cue_counts["__all__"][cue] += 1
    token_rollup = {
        "_schema_version": "platform_title_token_rollup.v1",
        "top_tokens_by_platform": {
            platform: [{"token": token, "count": count} for token, count in counter.most_common(120)]
            for platform, counter in token_counts.items()
        },
    }
    signal_token_rollup = {
        "_schema_version": "platform_title_signal_rollup.v1",
        "top_signal_tokens_by_platform": {
            platform: [{"token": token, "count": count} for token, count in counter.most_common(120)]
            for platform, counter in signal_token_counts.items()
        },
    }
    cue_rollup = {
        "_schema_version": "platform_cue_rollup.v1",
        "cue_counts_by_platform": {
            platform: [{"cue": cue, "count": count} for cue, count in counter.most_common()]
            for platform, counter in cue_counts.items()
        },
    }
    return token_rollup, signal_token_rollup, cue_rollup


def _save_db(output_root: Path, surfaces: list[dict[str, Any]], entries: list[dict[str, Any]]) -> str:
    db_path = output_root / "platform_trends.sqlite3"
    conn = sqlite3.connect(db_path)
    _create_schema(conn)
    for row in surfaces:
        conn.execute(
            """
            INSERT INTO surfaces (
                surface_id, platform, surface_label, surface_type, source_url,
                raw_path, parser, entry_count, collected_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["surface_id"],
                row["platform"],
                row["surface_label"],
                row["surface_type"],
                row["source_url"],
                row["raw_path"],
                row["parser"],
                row["entry_count"],
                row["collected_at_utc"],
            ),
        )
    for row in entries:
        conn.execute(
            """
            INSERT INTO entries (
                entry_id, platform, surface_id, surface_label, surface_kind, rank_in_surface,
                title, title_raw, creator, genre_text, date_text, score_text,
                promo_text, intro_text, badge_labels_json, product_id,
                entry_type, subcategory, source_url, source_surface_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["entry_id"],
                row["platform"],
                row["surface_id"],
                row["surface_label"],
                row["surface_kind"],
                row["rank_in_surface"],
                row["title"],
                row["title_raw"],
                row["creator"],
                row["genre_text"],
                row["date_text"],
                row["score_text"],
                row["promo_text"],
                row["intro_text"],
                json.dumps(row["badge_labels"], ensure_ascii=False),
                row["product_id"],
                row["entry_type"],
                row["subcategory"],
                row["source_url"],
                row["source_surface_url"],
            ),
        )
    conn.commit()
    conn.close()
    return str(db_path.relative_to(ROOT)).replace("\\", "/")


def parse_args(argv: list[str]) -> CrawlConfig:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--request-pause-seconds", type=float, default=0.2)
    parser.add_argument("--naver-recent-pages", type=int, default=10)
    parser.add_argument("--naver-recommend-pages", type=int, default=5)
    parser.add_argument("--naver-category-pages", type=int, default=5)
    parser.add_argument("--naver-special-pages", type=int, default=3)
    parser.add_argument("--skip-raw", action="store_true")
    args = parser.parse_args(argv)
    output_root = args.output_root if args.output_root.is_absolute() else (ROOT / args.output_root).resolve()
    return CrawlConfig(
        output_root=output_root,
        request_pause_seconds=args.request_pause_seconds,
        naver_recent_pages=args.naver_recent_pages,
        naver_recommend_pages=args.naver_recommend_pages,
        naver_category_pages=args.naver_category_pages,
        naver_special_pages=args.naver_special_pages,
        skip_raw=args.skip_raw,
    )


def main(argv: list[str] | None = None) -> int:
    config = parse_args(argv or sys.argv[1:])
    _assert_within_workspace(config.output_root)
    config.output_root.mkdir(parents=True, exist_ok=True)
    session = _session()

    surfaces, entries = _collect_entries(session, config)
    token_rollup, signal_token_rollup, cue_rollup = _build_rollups(entries)

    _write_json(config.output_root / "surface_registry.json", {"surfaces": surfaces})
    _write_jsonl(config.output_root / "platform_trend_entries.jsonl", entries)
    _write_json(config.output_root / "platform_title_token_rollup.json", token_rollup)
    _write_json(config.output_root / "platform_title_signal_rollup.json", signal_token_rollup)
    _write_json(config.output_root / "platform_cue_rollup.json", cue_rollup)
    db_rel = _save_db(config.output_root, surfaces, entries)

    by_platform = Counter(row["platform"] for row in entries)
    _write_json(
        config.output_root / "collection_status.json",
        {
            "_schema_version": "platform_trend_collection_status.v1",
            "surface_count": len(surfaces),
            "entry_count": len(entries),
            "entry_count_by_platform": dict(by_platform),
            "db_path": db_rel,
            "notes": [
                "Counts reflect visible public HTML / embedded JSON only.",
                "Rollups are exact-count helpers, not qualitative trend judgments.",
            ],
        },
    )

    print(f"Collected {len(entries)} entries across {len(surfaces)} surfaces")
    print(f"DB: {config.output_root / 'platform_trends.sqlite3'}")
    print(f"Entries JSONL: {config.output_root / 'platform_trend_entries.jsonl'}")
    print(f"Token rollup: {config.output_root / 'platform_title_token_rollup.json'}")
    print(f"Signal rollup: {config.output_root / 'platform_title_signal_rollup.json'}")
    print(f"Cue rollup: {config.output_root / 'platform_cue_rollup.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
