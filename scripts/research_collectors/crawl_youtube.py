"""
유튜브 채널 크롤러 (범용)
- Phase 1: yt-dlp flat-playlist로 전체 영상 리스트
- Phase 2: 최근 N개 상세 메타 보강 (좋아요/태그/업로드일)
출력:
- raw jsonl: material_ssot/10_research/80_ingest_raw/YYYY-MM-DD/
- derived json/csv: material_ssot/10_research/40_analysis/market_snapshots/YYYY-MM-DD/
사용법: python scripts/research_collectors/crawl_youtube.py <channel_key>
        python scripts/research_collectors/crawl_youtube.py all
"""

import sys
import io
import subprocess
import json
import csv
import time
from datetime import datetime
from pathlib import Path

try:
    from .runtime_paths import ensure_dated_analysis_bucket, ensure_dated_raw_bucket
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from runtime_paths import ensure_dated_analysis_bucket, ensure_dated_raw_bucket

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

TODAY = datetime.now().strftime("%Y%m%d")
RUN_DAY = datetime.now().strftime("%Y-%m-%d")
OUTPUT_DIR = ensure_dated_analysis_bucket(RUN_DAY)
RAW_DIR = ensure_dated_raw_bucket(RUN_DAY)

# ── 채널 레지스트리 ──────────────────────────────────────────

CHANNELS = {
    "syuka": {
        "name": "슈카월드",
        "channel_id": "UCsJ6RuBiTVWRX156FVbeaGg",
        "tags": "경제, 시사, 투자",
        "detail_count": 100,
    },
    "pirates": {
        "name": "지식해적단",
        "channel_id": "UC9cCBxBAQW2CzLYeT20q49A",
        "tags": "군사, 방산, 역사, 국방",
        "detail_count": 100,
    },
    "minani": {
        "name": "지식인미나니",
        "channel_id": "UCZN-9omBiFx9F1FZC23nYkw",
        "tags": "상식, 교양, 지식",
        "detail_count": 100,
    },
    "boda": {
        "name": "보다BODA",
        "channel_id": "UCoCvTlU0KpNYwnMIgs7MPrA",
        "tags": "다큐, 시사, 사회",
        "detail_count": 100,
    },
    "techmong": {
        "name": "테크몽",
        "channel_id": "UCFX6adXoyQKxft933NB3rmA",
        "tags": "IT, 기술, 테크",
        "detail_count": 100,
    },
    "worldhistory": {
        "name": "벌거벗은세계사",
        "channel_id": "UC-9RQCJ0gS_Kgt7J0SVrE8w",
        "tags": "세계사, 역사, 교양",
        "detail_count": 100,
    },
    "eo": {
        "name": "EO",
        "channel_id": "UCQ2DWm5Md16Dc3xRwwhVE7Q",
        "tags": "스타트업, 비즈니스, 창업",
        "detail_count": 100,
    },
    "changeground": {
        "name": "체인지그라운드",
        "channel_id": "UCtfGLmp6xMwvPoYpI-A5Kdg",
        "tags": "자기계발, 동기부여, 성장",
        "detail_count": 100,
    },
    "yumat": {
        "name": "유맛",
        "channel_id": "UCkQRkuNtkfOu66sywD2OKtA",
        "tags": "경제, 부동산, 재테크",
        "detail_count": 100,
    },
    "ebsdocu": {
        "name": "EBS다큐",
        "channel_id": "UCFCtZJTuJhE18k8IXwmXTYQ",
        "tags": "다큐, 기업, 산업, 패러다임",
        "detail_count": 100,
        "filter_keywords": [
            # 기업/재벌
            "기업", "재벌", "회장", "CEO", "경영", "그룹", "회사", "창업", "사업",
            "삼성", "현대", "SK", "LG", "롯데", "포스코", "한화", "CJ", "두산",
            # 산업/경제
            "산업", "경제", "수출", "무역", "제조", "공장", "생산", "물류",
            "반도체", "배터리", "자동차", "조선", "철강", "화학", "에너지",
            "AI", "인공지능", "로봇", "테크", "IT", "디지털", "플랫폼",
            # 금융/투자
            "금융", "은행", "투자", "주식", "부동산", "자산", "펀드", "증권",
            # 패러다임/변화
            "혁신", "패러다임", "전환", "미래", "위기", "도전", "성장", "몰락",
            "글로벌", "세계", "시장", "경쟁", "전쟁",
            # 인물/리더십
            "리더", "천재", "전략", "비전", "결단",
        ],
    },
}


# ── Phase 1: 전체 리스트 ─────────────────────────────────────

def phase1_flat_list(key: str, channel: dict) -> list:
    name = channel["name"]
    cid = channel["channel_id"]
    raw_path = RAW_DIR / f"_{key}_raw.jsonl"

    print(f"--- {name} Phase 1: 전체 리스트 ---")

    if raw_path.exists():
        with open(raw_path, encoding='utf-8') as f:
            count = sum(1 for _ in f)
        print(f"  기존 덤프 사용: {count}건")
    else:
        print("  yt-dlp 실행 중 (스트리밍)...")
        with open(raw_path, "w", encoding="utf-8") as out_f:
            proc = subprocess.Popen(
                ["yt-dlp", "--flat-playlist", "--dump-json",
                 f"https://www.youtube.com/channel/{cid}/videos"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding='utf-8', errors='replace'
            )
            count = 0
            for line in proc.stdout:
                out_f.write(line)
                count += 1
                if count % 100 == 0:
                    print(f"    {count}건 수집 중...")
            proc.wait()
            if proc.returncode != 0 and count == 0:
                print(f"  yt-dlp 에러: {proc.stderr.read()[:300]}")
                raw_path.unlink(missing_ok=True)
                return []
        print(f"  덤프 완료: {count}건")

    filter_kw = channel.get("filter_keywords")

    results = []
    skipped = 0
    with open(raw_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)

            title = d.get("title", "")
            desc = d.get("description", "") or ""

            # 키워드 필터 — 제목+설명에 하나라도 매칭되면 통과
            if filter_kw:
                haystack = title + " " + desc
                if not any(kw in haystack for kw in filter_kw):
                    skipped += 1
                    continue

            desc_lines = [l.strip() for l in desc.split('\n') if l.strip()]
            desc_clean = [l for l in desc_lines
                          if not any(kw in l for kw in ['http', '👉', '🎤', '협찬', '광고', '#', '구독', '채널', '💀'])]
            desc_short = ' '.join(desc_clean[:5])[:200]

            duration_sec = d.get("duration") or 0
            duration_min = round(duration_sec / 60, 1) if duration_sec else 0

            results.append({
                "source": name,
                "video_id": d.get("id", ""),
                "title": title,
                "view_count": d.get("view_count", 0),
                "duration_min": duration_min,
                "description_short": desc_short,
                "url": d.get("webpage_url", ""),
            })

    if filter_kw:
        print(f"  파싱: {len(results)}건 (필터 통과) / {skipped}건 제외")
    else:
        print(f"  파싱: {len(results)}건")
    return results


# ── Phase 2: 상세 보강 ───────────────────────────────────────

def phase2_enrich(results: list, n: int):
    if not results:
        return

    recent = results[:n]
    print(f"  상세 보강: {len(recent)}건")

    for i, item in enumerate(recent):
        vid = item["video_id"]
        if not vid:
            continue
        try:
            result = subprocess.run(
                ["yt-dlp", "--dump-json", "--skip-download",
                 f"https://www.youtube.com/watch?v={vid}"],
                capture_output=True, text=True, encoding='utf-8', errors='replace',
                timeout=30
            )
            if result.returncode != 0:
                continue

            d = json.loads(result.stdout)

            upload_date = d.get("upload_date", "")
            if upload_date and len(upload_date) == 8:
                upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
            item["upload_date"] = upload_date
            item["like_count"] = d.get("like_count", 0)
            item["comment_count"] = d.get("comment_count", 0)
            item["tags"] = ", ".join(d.get("tags", []))
            item["categories"] = ", ".join(d.get("categories", []))

            desc_full = d.get("description", "") or ""
            desc_lines = [l.strip() for l in desc_full.split('\n') if l.strip()]
            desc_clean = [l for l in desc_lines
                          if not any(kw in l for kw in ['http', '👉', '🎤', '협찬', '광고', '구독'])]
            item["description_full"] = '\n'.join(desc_clean[:10])

        except Exception as e:
            print(f"    에러 ({vid}): {e}")

        if (i + 1) % 10 == 0:
            print(f"    {i+1}/{len(recent)} 처리됨")
        time.sleep(0.5)


# ── 저장 ────────────────────────────────────────────────────

def save_results(data: list, prefix: str):
    if not data:
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

def run_channel(key: str):
    channel = CHANNELS[key]
    name = channel["name"]
    detail_n = channel["detail_count"]

    results = phase1_flat_list(key, channel)
    save_results(results, f"yt_{key}_all")

    phase2_enrich(results, n=detail_n)
    save_results(results[:detail_n], f"yt_{key}_detail")
    save_results(results, f"yt_{key}_enriched")

    print(f"  {name} 완료: 전체 {len(results)}건, 상세 {min(detail_n, len(results))}건\n")


def main():
    args = sys.argv[1:] if len(sys.argv) > 1 else ["all"]
    target = args[0]

    print(f"=== 유튜브 크롤링 시작 ({TODAY}) ===\n")

    if target == "all":
        for key in CHANNELS:
            run_channel(key)
    elif target in CHANNELS:
        run_channel(target)
    else:
        print(f"알 수 없는 채널: {target}")
        print(f"사용 가능: {', '.join(CHANNELS.keys())}, all")
        return

    print("=== 완료 ===")


if __name__ == "__main__":
    main()
