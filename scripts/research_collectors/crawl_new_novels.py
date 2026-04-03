"""
카카오페이지 / 네이버시리즈 신작 웹소설 크롤러 v2
- 카카오: 리스트(__NEXT_DATA__) + 상세(viewCount, rating, description 등)
- 네이버: 리스트(HTML) + 상세(다운로드수, 장르, 출판사, 소개, 등급)
- 19금 필터링: 카카오 Nineteen / 네이버 19세 이용가 제외
출력: material_ssot/10_research/40_analysis/market_snapshots/YYYY-MM-DD/ 에 CSV + JSON
"""

import sys
import io

# Windows cp949 인코딩 문제 방지
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


# ── 카카오페이지 ──────────────────────────────────────────────

def crawl_kakao_new():
    """카카오페이지 웹소설 신작 리스트 (menu/10011/screen/101)"""
    url = "https://page.kakao.com/menu/10011/screen/101"
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()

    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', r.text, re.DOTALL)
    if not m:
        print("[카카오] __NEXT_DATA__ 를 찾을 수 없음")
        return []

    data = json.loads(m.group(1))
    queries = data["props"]["pageProps"]["initialProps"]["dehydratedState"]["queries"]

    results = []
    for query in queries:
        sections = query.get("state", {}).get("data", {}).get("sections", [])
        for section in sections:
            for group in section.get("groups", []):
                group_title = group.get("meta", {}).get("title", "")
                for item in group.get("items", []):
                    age = item.get("ageGrade", "")

                    # 19금 제외
                    if age == "Nineteen":
                        continue

                    event_meta = item.get("eventLog", {}).get("eventMeta", {})
                    series_id = event_meta.get("series_id", "")

                    results.append({
                        "source": "카카오페이지",
                        "group": group_title,
                        "title": item.get("title", ""),
                        "series_id": series_id,
                        "age_grade": age,
                        "badges": ", ".join(item.get("badgeList", [])),
                        "view_count_label": ", ".join(item.get("subtitleList", [])),
                        "genre": event_meta.get("subcategory", ""),
                        "provider": event_meta.get("provider", ""),
                        "category_type": item.get("categoryType", ""),
                        "url": f"https://page.kakao.com/content/{series_id}" if series_id else "",
                    })

    print(f"[카카오] {len(results)}건 수집 (19금 제외)")
    return results


def fetch_kakao_detail(series_id: str) -> dict:
    """카카오 상세: __NEXT_DATA__ > contentHomeOverview 에서 추출
    - viewCount, ratingCount, ratingSum, commentCount
    - authors, description, pubPeriod, startSaleDt, freeSlideCount
    """
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
                "authors": c.get("authors", ""),
                "description": c.get("description", ""),
                "pub_period": c.get("pubPeriod", ""),
                "start_sale_dt": c.get("startSaleDt", "")[:10] if c.get("startSaleDt") else "",
                "free_slide_count": c.get("freeSlideCount", 0),
                "on_issue": c.get("onIssue", ""),
            }

        return {}
    except Exception as e:
        print(f"  카카오 상세 에러 (series_id={series_id}): {e}")
        return {}


# ── 네이버 시리즈 공통 파서 ───────────────────────────────────

def _parse_naver_list_item(li, source: str) -> dict | None:
    """네이버 리스트 <li> 하나를 파싱"""
    a_tag = li.select_one("h3 a")
    if not a_tag:
        return None

    link_text = a_tag.get_text(strip=True)
    href = a_tag.get("href", "")

    # (N화/완결|미완결) 분리
    m = re.search(r"\((\d+)화/(완결|미완결)\)\s*$", link_text)
    if m:
        title = link_text[:m.start()].strip()
        ep_count = m.group(1)
        status = m.group(2)
    else:
        m2 = re.search(r"\(총\s*(\d+)화/(완결|미완결)\)", link_text)
        if m2:
            title = link_text[:m2.start()].strip()
            ep_count = m2.group(1)
            status = m2.group(2)
        else:
            title = a_tag.get("title", "") or link_text
            ep_count = ""
            status = ""

    title = re.sub(r"\s*\[무료연재\]\s*", "", title).strip()

    author_span = li.select_one("span.author")
    author = author_span.get_text(strip=True) if author_span else ""

    star_em = li.select_one("em.score_num")
    star = star_em.get_text(strip=True) if star_em else ""

    dsc = li.select_one("p.dsc")
    description = dsc.get_text(strip=True) if dsc else ""

    free_info = li.select_one("span.free_info")
    free_text = free_info.get_text(strip=True) if free_info else ""

    product_no = ""
    if "productNo=" in href:
        product_no = href.split("productNo=")[-1].split("&")[0]

    return {
        "source": source,
        "title": title,
        "author": author,
        "episodes": ep_count,
        "status": status,
        "star": star,
        "description": description,
        "free_info": free_text,
        "product_no": product_no,
        "url": f"https://series.naver.com{href}" if href.startswith("/") else href,
    }


# ── 네이버 시리즈 -- 신작 ────────────────────────────────────

def crawl_naver_recent(max_pages=5):
    """네이버시리즈 신작 웹소설 (recentList)"""
    base = "https://series.naver.com/novel/recentList.series"
    results = []

    for page in range(1, max_pages + 1):
        params = {"orderTypeCode": "new", "isFinished": "false", "page": page}
        r = requests.get(base, params=params, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"[네이버 신작] 페이지 {page} 실패: {r.status_code}")
            break

        soup = BeautifulSoup(r.text, "lxml")
        items = soup.select("ul.lst_list > li")
        if not items:
            items = soup.select("div.lst_thum_wrap li") or soup.select("ul.comic_lst > li")
        if not items:
            print(f"[네이버 신작] 페이지 {page} -- 항목 없음, 종료")
            break

        for li in items:
            row = _parse_naver_list_item(li, "네이버시리즈_신작")
            if row:
                results.append(row)

        print(f"[네이버 신작] 페이지 {page} -- {len(items)}건")
        time.sleep(0.5)

    print(f"[네이버 신작] 총 {len(results)}건 수집")
    return results


# ── 네이버 시리즈 -- 무료연재 검색 ────────────────────────────

def crawl_naver_free(max_pages=5):
    """네이버시리즈 '무료연재' 검색 결과"""
    base = "https://series.naver.com/search/search.series"
    results = []

    for page in range(1, max_pages + 1):
        params = {"t": "novel", "q": "무료연재", "page": page}
        r = requests.get(base, params=params, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"[네이버 무료연재] 페이지 {page} 실패: {r.status_code}")
            break

        soup = BeautifulSoup(r.text, "lxml")
        items = soup.select("ul.lst_list > li") or soup.select("ul.comic_lst > li")
        if not items:
            print(f"[네이버 무료연재] 페이지 {page} -- 항목 없음, 종료")
            break

        for li in items:
            row = _parse_naver_list_item(li, "네이버시리즈_무료연재")
            if row:
                results.append(row)

        print(f"[네이버 무료연재] 페이지 {page} -- {len(items)}건")
        time.sleep(0.5)

    print(f"[네이버 무료연재] 총 {len(results)}건 수집")
    return results


# ── 개별 작품 상세 (네이버) ───────────────────────────────────

def fetch_naver_detail(product_no: str) -> dict:
    """네이버 시리즈 작품 상세 페이지에서 추출:
    - 다운로드수: user_action_area > li:nth-child(2) > a > span
    - 소개: #content > div.end_dsc > div
    - 장르/출판사/등급: #content > ul.end_info
    """
    url = f"https://series.naver.com/novel/detail.series?productNo={product_no}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return {}

        soup = BeautifulSoup(r.text, "lxml")

        # 다운로드 수 -- user_action_area > ul > li:nth-child(2) > a > span
        download_count = ""
        dl_span = soup.select_one(
            "#content > div.end_head > div.user_action_area > ul > li:nth-child(2) > a > span"
        )
        if dl_span:
            download_count = dl_span.get_text(strip=True)

        # 소개글 -- #content > div.end_dsc > div
        intro = ""
        dsc_div = soup.select_one("#content > div.end_dsc > div")
        if dsc_div:
            intro = dsc_div.get_text(strip=True)[:500]
        else:
            # fallback
            dsc = soup.select_one(".end_dsc")
            if dsc:
                intro = dsc.get_text(strip=True)[:500]

        # end_info -- 장르/출판사/등급
        genre = ""
        publisher = ""
        age_grade = ""

        end_info = soup.select_one("#content > ul.end_info") or soup.select_one(".info_lst")
        if end_info:
            for li in end_info.select("ul > li") or end_info.select("li"):
                text = li.get_text(strip=True)
                spans = li.select("span")
                links = li.select("a")

                li_classes = li.get("class", [])
                if spans and "출판사" in spans[0].get_text():
                    publisher = links[0].get_text(strip=True) if links else ""
                elif spans and spans[0].get_text(strip=True) == "글":
                    pass
                elif "ing" in li_classes or "end" in li_classes:
                    pass  # 연재상태 (연재중/완결)
                elif "이용가" in text:
                    age_grade = text
                elif text in ("연재중", "완결", "휴재"):
                    pass  # class 없이 텍스트로만 상태 표시되는 경우
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
        print(f"  네이버 상세 에러 (productNo={product_no}): {e}")
        return {}


# ── 저장 ────────────────────────────────────────────────────

def save_results(all_results: list, prefix: str):
    """CSV + JSON으로 저장"""
    if not all_results:
        print(f"  {prefix}: 저장할 데이터 없음")
        return

    json_path = OUTPUT_DIR / f"{prefix}_{TODAY}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    csv_path = OUTPUT_DIR / f"{prefix}_{TODAY}.csv"
    all_keys = []
    seen = set()
    for row in all_results:
        for k in row.keys():
            if k not in seen:
                all_keys.append(k)
                seen.add(k)
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_results)

    print(f"  저장 완료: {json_path.name}, {csv_path.name}")


# ── 메인 ────────────────────────────────────────────────────

def main():
    print(f"=== 웹소설 신작 크롤링 v2 시작 ({TODAY}) ===\n")

    # 1) 카카오 리스트
    print("--- 카카오페이지 신작 ---")
    kakao = crawl_kakao_new()
    save_results(kakao, "kakao_new")

    # 2) 카카오 상세 보강
    has_kakao_detail = [x for x in kakao if x.get("series_id")]
    if has_kakao_detail:
        print(f"\n--- 카카오 상세 보강 ({len(has_kakao_detail)}건) ---")
        for i, item in enumerate(has_kakao_detail):
            detail = fetch_kakao_detail(item["series_id"])
            item.update(detail)
            if (i + 1) % 10 == 0:
                print(f"  {i+1}/{len(has_kakao_detail)} 처리됨")
            time.sleep(0.3)
        save_results(kakao, "kakao_detail")

    # 3) 네이버 신작
    print("\n--- 네이버 시리즈 신작 ---")
    naver_recent = crawl_naver_recent(max_pages=5)
    save_results(naver_recent, "naver_recent")

    # 4) 네이버 무료연재
    print("\n--- 네이버 시리즈 무료연재 ---")
    naver_free = crawl_naver_free(max_pages=5)
    save_results(naver_free, "naver_free")

    # 5) 네이버 상세 보강
    naver_all = naver_recent + naver_free
    has_naver_detail = [x for x in naver_all if x.get("product_no")]
    if has_naver_detail:
        print(f"\n--- 네이버 상세 보강 ({len(has_naver_detail)}건) ---")
        for i, item in enumerate(has_naver_detail):
            detail = fetch_naver_detail(item["product_no"])
            item.update(detail)

            # 19금 마킹 (나중에 필터링)
            if "19세" in item.get("age_grade", ""):
                item["_is_adult"] = True

            if (i + 1) % 10 == 0:
                print(f"  {i+1}/{len(has_naver_detail)} 처리됨")
            time.sleep(0.3)

        # 19금 제외
        naver_recent_clean = [x for x in naver_recent if not x.get("_is_adult")]
        naver_free_clean = [x for x in naver_free if not x.get("_is_adult")]

        removed = len(naver_all) - len(naver_recent_clean) - len(naver_free_clean)
        if removed:
            print(f"  19금 {removed}건 제외")

        # _is_adult 필드 제거
        for lst in [naver_recent_clean, naver_free_clean]:
            for item in lst:
                item.pop("_is_adult", None)

        save_results(naver_recent_clean, "naver_recent_detail")
        save_results(naver_free_clean, "naver_free_detail")

        naver_all_clean = naver_recent_clean + naver_free_clean
    else:
        naver_all_clean = naver_all

    # 6) 전체 통합 저장
    all_data = kakao + naver_all_clean
    save_results(all_data, "all_novels")

    print(f"\n=== 완료: 총 {len(all_data)}건 (19금 제외) ===")


if __name__ == "__main__":
    main()
