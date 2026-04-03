"""
슈카월드 유튜브 채널 크롤러
- Phase 1: yt-dlp flat-playlist로 전체 영상 리스트 (제목/조회수/길이/설명)
- Phase 2: 최근 N개 영상 상세 메타 보강 (좋아요/태그/업로드일)
출력:
- raw jsonl: material_ssot/10_research/80_ingest_raw/YYYY-MM-DD/
- derived json/csv: material_ssot/10_research/40_analysis/market_snapshots/YYYY-MM-DD/
"""

import sys
import io
import subprocess
import json
import csv
import re
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
CHANNEL_URL = "https://www.youtube.com/channel/UCsJ6RuBiTVWRX156FVbeaGg/videos"
RAW_JSONL = RAW_DIR / "_syuka_raw.jsonl"


def phase1_flat_list():
    """yt-dlp flat-playlist로 전체 영상 메타 덤프"""
    print("--- Phase 1: 전체 리스트 수집 ---")

    # 이미 오늘 덤프가 있으면 재사용
    if RAW_JSONL.exists():
        with open(RAW_JSONL, encoding='utf-8') as f:
            count = sum(1 for _ in f)
        print(f"  기존 덤프 사용: {count}건")
    else:
        print("  yt-dlp 실행 중...")
        result = subprocess.run(
            ["yt-dlp", "--flat-playlist", "--dump-json", CHANNEL_URL],
            capture_output=True, text=True, encoding='utf-8', errors='replace',
            timeout=300
        )
        if result.returncode != 0:
            print(f"  yt-dlp 에러: {result.stderr[:300]}")
            return []

        RAW_JSONL.write_text(result.stdout, encoding='utf-8')
        count = result.stdout.count('\n')
        print(f"  {count}건 덤프 완료")

    # 파싱
    results = []
    with open(RAW_JSONL, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)

            # 설명에서 광고 부분 제거하고 핵심만
            desc = d.get("description", "") or ""
            # 첫 3줄 정도가 보통 핵심
            desc_lines = [l.strip() for l in desc.split('\n') if l.strip()]
            # 광고/링크 줄 제거
            desc_clean = []
            for l in desc_lines:
                if any(kw in l for kw in ['http', '👉', '🎤', '협찬', '광고', '#', '구독', '채널']):
                    continue
                desc_clean.append(l)
            desc_short = ' '.join(desc_clean[:5])[:200]

            duration_sec = d.get("duration") or 0
            duration_min = round(duration_sec / 60, 1) if duration_sec else 0

            results.append({
                "video_id": d.get("id", ""),
                "title": d.get("title", ""),
                "view_count": d.get("view_count", 0),
                "duration_min": duration_min,
                "description_short": desc_short,
                "url": d.get("webpage_url", ""),
            })

    print(f"  파싱 완료: {len(results)}건")
    return results


def phase2_enrich_recent(results: list, n=100):
    """최근 N개 영상의 상세 메타 보강 (좋아요/태그/업로드일)"""
    if not results:
        return

    recent = results[:n]
    print(f"\n--- Phase 2: 최근 {len(recent)}건 상세 보강 ---")

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

            # 업로드일
            upload_date = d.get("upload_date", "")
            if upload_date and len(upload_date) == 8:
                upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
            item["upload_date"] = upload_date

            item["like_count"] = d.get("like_count", 0)
            item["comment_count"] = d.get("comment_count", 0)
            item["tags"] = ", ".join(d.get("tags", []))
            item["categories"] = ", ".join(d.get("categories", []))

            # 설명 전문 (상세)
            desc_full = d.get("description", "") or ""
            desc_lines = [l.strip() for l in desc_full.split('\n') if l.strip()]
            desc_clean = [l for l in desc_lines if not any(kw in l for kw in ['http', '👉', '🎤', '협찬', '광고', '구독'])]
            item["description_full"] = '\n'.join(desc_clean[:10])

        except Exception as e:
            print(f"  에러 ({vid}): {e}")

        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(recent)} 처리됨")
        time.sleep(0.5)

    print(f"  상세 보강 완료")


def save_results(data: list, prefix: str):
    """CSV + JSON 저장"""
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


def main():
    print(f"=== 슈카월드 크롤링 시작 ({TODAY}) ===\n")

    # Phase 1
    results = phase1_flat_list()
    save_results(results, "syuka_all")

    # Phase 2 -- 최근 100건 상세
    phase2_enrich_recent(results, n=100)
    save_results(results[:100], "syuka_recent_detail")

    # 전체도 다시 저장 (상위 100건 보강된 상태)
    save_results(results, "syuka_all_enriched")

    print(f"\n=== 완료: 전체 {len(results)}건, 상세 100건 ===")


if __name__ == "__main__":
    main()
