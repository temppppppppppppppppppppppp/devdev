"""NAS EPUB → 실물기반 사각지대 테스트 원고 추출 스크립트.

장르별 대표 작품에서 연속 20화를 txt로 추출한다.
기존 investment_corpus_support.py의 extract_epub_text()를 재사용.

Usage:
    python scripts/extract_manuscript_samples.py
    python scripts/extract_manuscript_samples.py --max-episodes 30
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.investment_corpus_support import (  # noqa: E402
    extract_epub_text,
    list_selected_epubs,
    parse_episode_number,
    select_ssot_dir,
    title_dir_for,
)

NAS_ROOT = Path(r"\\172.16.10.120\소설사업부\판무사업팀\2. 연재 진행 파일\1. 제작 진행 연재_Epub")
OUTPUT_ROOT = ROOT / "docs" / "실물기반 사각지대 테스트" / "원고"

# 장르별 대표 작품 (연재 폴더명에서 [연재] 제외한 이름)
# 장르 분류는 제목 기반 추정 — 필요 시 사용자가 수정
SAMPLE_TITLES: dict[str, list[str]] = {
    "투자물": [
        "회귀 후 몰빵투자로 재벌 되기",
        "금수저 투자백서",
    ],
    "무협": [
        "검신재림",
        "곤륜패선",
    ],
    "헌터물": [
        "만렙 사냥꾼, 회귀하다",
        "SSS급 블러드 헌터!",
    ],
    "판타지": [
        "9서클 소드마스터",
        "환생했더니 정령군주",
    ],
    "재벌물": [
        "재벌 3세는 총수가 되고 싶다",
        "독식하는 재벌 3세",
    ],
    "배우물": [
        "연기를 너무 잘함",
        "천재 배우, 이름을 얻다",
    ],
    "스포츠": [
        "괴물투수",
        "축구 천재가 돌아왔다",
    ],
    "대체역사": [
        "눈 떠보니 갑신정변",
        "고려는 천조국이 되기로 하였습니다",
    ],
}


def find_title_dir(title: str) -> Path | None:
    """NAS에서 [연재] 접두사 포함 폴더를 찾는다."""
    candidates = [
        NAS_ROOT / f"[연재]{title}",
        NAS_ROOT / f"[연재] {title}",
        NAS_ROOT / f"[연재]_{title}",
    ]
    for c in candidates:
        if c.exists():
            return c
    # 부분 매칭 시도
    for d in NAS_ROOT.iterdir():
        if title in d.name:
            return d
    return None


def extract_title(title: str, genre: str, max_episodes: int) -> dict:
    """한 작품에서 최대 max_episodes화를 추출한다."""
    title_dir = find_title_dir(title)
    if not title_dir:
        return {"title": title, "genre": genre, "status": "not_found", "episodes": 0}

    try:
        selection = select_ssot_dir(title, title_dir)
    except Exception as e:
        return {"title": title, "genre": genre, "status": f"ssot_error: {e}", "episodes": 0}

    epubs = list_selected_epubs(selection)
    if not epubs:
        return {"title": title, "genre": genre, "status": "no_epubs", "episodes": 0}

    # 에피소드 번호 기반 숫자 정렬, 상위 max_episodes만
    def _ep_sort_key(p: Path) -> int:
        try:
            return parse_episode_number(p.name)
        except ValueError:
            return 999999

    epubs = sorted(epubs, key=_ep_sort_key)[:max_episodes]

    out_dir = OUTPUT_ROOT / f"{genre}_{title}"
    out_dir.mkdir(parents=True, exist_ok=True)

    extracted = 0
    errors = []
    for epub_path in epubs:
        try:
            episode = extract_epub_text(epub_path)
            ep_num = episode.episode if episode.episode > 0 else extracted + 1
            out_file = out_dir / f"ep{ep_num:03d}.txt"
            out_file.write_text(episode.text, encoding="utf-8")
            extracted += 1
        except Exception as e:
            errors.append(f"{epub_path.name}: {e}")

    return {
        "title": title,
        "genre": genre,
        "status": "ok",
        "episodes": extracted,
        "errors": errors[:5] if errors else [],
        "output_dir": str(out_dir),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="장르별 실물 원고 샘플 추출")
    parser.add_argument("--max-episodes", type=int, default=20, help="작품당 최대 추출 화수")
    args = parser.parse_args()

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    results = []
    for genre, titles in SAMPLE_TITLES.items():
        for title in titles:
            print(f"[{genre}] {title} ...", end=" ", flush=True)
            result = extract_title(title, genre, args.max_episodes)
            print(f"→ {result['status']} ({result['episodes']}화)")
            results.append(result)

    # 매니페스트 저장
    manifest_path = OUTPUT_ROOT / "manifest.json"
    manifest_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n매니페스트: {manifest_path}")

    total = sum(r["episodes"] for r in results)
    ok = sum(1 for r in results if r["status"] == "ok")
    print(f"완료: {ok}/{len(results)} 작품, 총 {total}화 추출")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
