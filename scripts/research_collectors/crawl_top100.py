"""
카카오페이지 / 네이버시리즈 TOP 랭킹 크롤러
- 카카오: screen/64 LandingRanking (50건) + 상세 보강
- 네이버: top100List 주간 (100건, 5페이지) + 상세 보강
- 19금 제외, 현판 편향 필터
출력: material_ssot/10_research/40_analysis/market_snapshots/YYYY-MM-DD/ 에 CSV + JSON
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import requests
from bs4 import BeautifulSoup
import json
import csv
import re
import time
from datetime import datetime
from pathlib import Path

try:
    from .runtime_paths import ensure_dated_analysis_bucket
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from runtime_paths import ensure_dated_analysis_bucket

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
}

TODAY = datetime.now().strftime("%Y%m%d")
RUN_DAY = datetime.now().strftime("%Y-%m-%d")
OUTPUT_DIR = ensure_dated_analysis_bucket(RUN_DAY)


# ── 카카오 TOP ───────────────────────────────────────────────

def crawl_kakao_top():
    """카카오페이지 웹소설 인기 랭킹 (screen/64)"""
    url = "https://page.kakao.com/menu/10011/screen/64"
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()

    m = re.search(r'__NEXT_DATA__.*?>(.*?)</script>', r.text, re.DOTALL)
    if not m:
        print("[카카오 TOP] __NEXT_DATA__ 없음")
        return []

    data = json.loads(m.group(1))
    queries = data["props"]["pageProps"]["initialProps"]["dehydratedState"]["queries"]

    results = []
    for query in queries:
        sections = query.get("state", {}).get("data", {}).get("sections", [])
        for section in sections:
            if section.get("type") != "LandingRanking":
                continue
            for group in section.get("groups", []):
                for rank_idx, item in enumerate(group.get("items", []), 1):
                    age = item.get("ageGrade", "")
                    if age == "Nineteen":
                        continue

                    event_meta = item.get("eventLog", {}).get("eventMeta", {})
                    series_id = event_meta.get("series_id", "")
                    subtitles = item.get("subtitleList", [])

                    # subtitleList: ['235.5만', '연재중', '샤이나크'] 형태
                    view_label = subtitles[0] if len(subtitles) > 0 else ""
                    status = subtitles[1] if len(subtitles) > 1 else ""
                    author = subtitles[2] if len(subtitles) > 2 else ""

                    results.append({
                        "source": "카카오_TOP",
                        "rank": rank_idx,
                        "title": item.get("title", ""),
                        "series_id": series_id,
                        "genre": event_meta.get("subcategory", ""),
                        "author": author,
                        "view_count_label": view_label,
                        "status": status,
                        "age_grade": age,
                        "url": f"https://page.kakao.com/content/{series_id}" if series_id else "",
                    })

    print(f"[카카오 TOP] {len(results)}건 수집 (19금 제외)")
    return results


def fetch_kakao_detail(series_id: str) -> dict:
    """카카오 상세 보강"""
    url = f"https://page.kakao.com/content/{series_id}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return {}

        m = re.search(r'__NEXT_DATA__.*?>(.*?)</script>', r.text, re.DOTALL)
        if not m:
            return {}

        data = json.loads(m.group(1))
        queries = data["props"]["pageProps"]["initialProps"]["dehydratedState"]["queries"]

        for q in queries:
            overview = q.get("state", {}).get("data", {}).get("contentHomeOverview")
            if not overview:
                continue
            c = overview.get("content", {})
            sp = c.get("serviceProperty", {})

            rating_count = sp.get("ratingCount", 0)
            rating_sum = sp.get("ratingSum", 0)
            avg_rating = round(rating_sum / rating_count, 2) if rating_count else 0

            return {
                "view_count": sp.get("viewCount", 0),
                "comment_count": sp.get("commentCount", 0),
                "rating_count": rating_count,
                "avg_rating": avg_rating,
                "description": c.get("description", ""),
                "pub_period": c.get("pubPeriod", ""),
                "start_sale_dt": c.get("startSaleDt", "")[:10] if c.get("startSaleDt") else "",
                "free_slide_count": c.get("freeSlideCount", 0),
            }

        return {}
    except Exception as e:
        print(f"  카카오 상세 에러 ({series_id}): {e}")
        return {}


# ── 네이버 TOP 100 ───────────────────────────────────────────

def crawl_naver_top100():
    """네이버시리즈 주간 TOP 100 (5페이지 x 20건)"""
    base = "https://series.naver.com/novel/top100List.series"
    results = []

    for page in range(1, 6):
        params = {"rankingTypeCode": "WEEKLY", "categoryCode": "ALL", "page": page}
        r = requests.get(base, params=params, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"[네이버 TOP] 페이지 {page} 실패: {r.status_code}")
            break

        soup = BeautifulSoup(r.text, "lxml")
        items = soup.select("ul.comic_top_lst > li")
        if not items:
            print(f"[네이버 TOP] 페이지 {page} -- 항목 없음")
            break

        for li in items:
            # 순위
            rank_em = li.select_one("div.top_numb em")
            rank = rank_em.get_text(strip=True) if rank_em else ""

            # 순위 변동
            change_em = li.select_one("span.top_uds em")
            rank_change = change_em.get_text(strip=True) if change_em else ""

            # 제목
            a_tag = li.select_one("div.comic_cont h3 a")
            if not a_tag:
                continue
            title = a_tag.get_text(strip=True)
            href = a_tag.get("href", "")

            # 별점
            star_em = li.select_one("em.score_num")
            star = star_em.get_text(strip=True) if star_em else ""

            # 작가
            author_span = li.select_one("span.author")
            author = author_span.get_text(strip=True) if author_span else ""

            # 화수/완결
            ellipsis_spans = li.select("span.ellipsis")
            ep_info = ""
            for sp in ellipsis_spans:
                txt = sp.get_text(strip=True)
                if "화" in txt:
                    ep_info = txt
                    break

            # 설명
            dsc = li.select_one("p.dsc")
            description = dsc.get_text(strip=True) if dsc else ""

            # 무료 정보
            free_info = li.select_one("span.free_info")
            free_text = free_info.get_text(strip=True) if free_info else ""

            # productNo
            product_no = ""
            if "productNo=" in href:
                product_no = href.split("productNo=")[-1].split("&")[0]

            results.append({
                "source": "네이버_TOP100",
                "rank": rank,
                "rank_change": rank_change,
                "title": title,
                "author": author,
                "star": star,
                "episodes_info": ep_info,
                "description": description,
                "free_info": free_text,
                "product_no": product_no,
                "url": f"https://series.naver.com{href}" if href.startswith("/") else href,
            })

        print(f"[네이버 TOP] 페이지 {page} -- {len(items)}건")
        time.sleep(0.5)

    print(f"[네이버 TOP] 총 {len(results)}건 수집")
    return results


def fetch_naver_detail(product_no: str) -> dict:
    """네이버 상세: 다운로드수/장르/출판사/등급/소개"""
    url = f"https://series.naver.com/novel/detail.series?productNo={product_no}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return {}

        soup = BeautifulSoup(r.text, "lxml")

        # 로그인 필요 페이지 체크
        if "연령 확인" in soup.get_text()[:500]:
            return {"_login_required": True}

        # 다운로드 수
        download_count = ""
        dl_span = soup.select_one(
            "#content > div.end_head > div.user_action_area > ul > li:nth-child(2) > a > span"
        )
        if dl_span:
            download_count = dl_span.get_text(strip=True)

        # 소개글
        intro = ""
        dsc_div = soup.select_one("#content > div.end_dsc > div")
        if dsc_div:
            intro = dsc_div.get_text(strip=True)[:500]
        else:
            dsc = soup.select_one(".end_dsc")
            if dsc:
                intro = dsc.get_text(strip=True)[:500]

        # 장르/출판사/등급
        genre = ""
        publisher = ""
        age_grade = ""

        end_info = soup.select_one("#content > ul.end_info") or soup.select_one(".info_lst")
        if end_info:
            for li in end_info.select("ul > li") or end_info.select("li"):
                text = li.get_text(strip=True)
                li_classes = li.get("class", [])
                spans = li.select("span")
                links = li.select("a")

                if spans and "출판사" in spans[0].get_text():
                    publisher = links[0].get_text(strip=True) if links else ""
                elif spans and spans[0].get_text(strip=True) == "글":
                    pass
                elif "ing" in li_classes or "end" in li_classes:
                    pass
                elif "이용가" in text:
                    age_grade = text
                elif text in ("연재중", "완결", "휴재"):
                    pass
                elif text and not genre:
                    genre = text

        return {
            "download_count": download_count,
            "genre": genre,
            "publisher": publisher,
            "age_grade": age_grade,
            "intro": intro,
        }
    except Exception as e:
        print(f"  네이버 상세 에러 ({product_no}): {e}")
        return {}


# ── 저장 ────────────────────────────────────────────────────

def save_results(data: list, prefix: str):
    if not data:
        print(f"  {prefix}: 데이터 없음")
        return

    json_path = OUTPUT_DIR / f"{prefix}_{TODAY}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    csv_path = OUTPUT_DIR / f"{prefix}_{TODAY}.csv"
    all_keys = []
    seen = set()
    for row in data:
        for k in row.keys():
            if k not in seen:
                all_keys.append(k)
                seen.add(k)
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(data)

    print(f"  저장: {json_path.name}, {csv_path.name}")


# ── 메인 ────────────────────────────────────────────────────

def main():
    print(f"=== TOP 랭킹 크롤링 시작 ({TODAY}) ===\n")

    # 1) 카카오 TOP
    print("--- 카카오 TOP ---")
    kakao = crawl_kakao_top()
    save_results(kakao, "kakao_top")

    # 카카오 상세 보강
    has_detail = [x for x in kakao if x.get("series_id")]
    if has_detail:
        print(f"\n--- 카카오 TOP 상세 보강 ({len(has_detail)}건) ---")
        for i, item in enumerate(has_detail):
            detail = fetch_kakao_detail(item["series_id"])
            item.update(detail)
            if (i + 1) % 10 == 0:
                print(f"  {i+1}/{len(has_detail)} 처리됨")
            time.sleep(0.3)
        save_results(kakao, "kakao_top_detail")

    # 2) 네이버 TOP 100
    print("\n--- 네이버 TOP 100 ---")
    naver = crawl_naver_top100()
    save_results(naver, "naver_top100")

    # 네이버 상세 보강
    has_naver = [x for x in naver if x.get("product_no")]
    if has_naver:
        print(f"\n--- 네이버 TOP 상세 보강 ({len(has_naver)}건) ---")
        for i, item in enumerate(has_naver):
            detail = fetch_naver_detail(item["product_no"])

            # 19금 마킹
            if "19세" in detail.get("age_grade", ""):
                item["_is_adult"] = True

            # 로그인 필요 마킹
            if detail.pop("_login_required", False):
                item["_login_required"] = True

            item.update(detail)
            if (i + 1) % 10 == 0:
                print(f"  {i+1}/{len(has_naver)} 처리됨")
            time.sleep(0.3)

        # 19금 제외
        naver_clean = [x for x in naver if not x.get("_is_adult")]
        removed = len(naver) - len(naver_clean)
        if removed:
            print(f"  19금 {removed}건 제외")

        for item in naver_clean:
            item.pop("_is_adult", None)
            item.pop("_login_required", None)

        save_results(naver_clean, "naver_top100_detail")
    else:
        naver_clean = naver

    # 3) 현판 필터 — 통합
    kakao_hyunpan = [x for x in kakao if x.get("genre") == "현판"]
    naver_hyunpan = [x for x in naver_clean if x.get("genre") == "현판"]
    all_hyunpan = kakao_hyunpan + naver_hyunpan

    print(f"\n--- 현판 필터 ---")
    print(f"  카카오 현판: {len(kakao_hyunpan)}건 / 전체 {len(kakao)}건")
    print(f"  네이버 현판: {len(naver_hyunpan)}건 / 전체 {len(naver_clean)}건")
    save_results(all_hyunpan, "top_hyunpan")

    # 4) 전체 통합
    all_data = kakao + naver_clean
    save_results(all_data, "top_all")

    print(f"\n=== 완료: 전체 {len(all_data)}건 / 현판 {len(all_hyunpan)}건 ===")


if __name__ == "__main__":
    main()
