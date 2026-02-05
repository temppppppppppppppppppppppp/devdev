#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
[V60.97] Reverse Bible - 원고에서 Bible 역설계 CLI 도구

기존 원고를 분석하여 MasterBible JSON을 생성합니다.

사용법:
    python tools2/reverse_bible.py --input 원고.txt --output bible.json --genre investment
    python tools2/reverse_bible.py -i 원고.txt -o bible.json -g wuxia

옵션:
    --input, -i     : 입력 원고 파일 경로 (필수)
    --output, -o    : 출력 Bible JSON 경로 (기본: bible/extracted_bible.json)
    --genre, -g     : 장르 (wuxia/hunter/investment, 기본: wuxia)
    --mode, -m      : 추출 모드 (starting_point/current_state, 기본: starting_point)
    --encoding, -e  : 파일 인코딩 (기본: utf-8)
"""

import sys
import os
import json
import argparse
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv(project_root / ".env")


def create_minimal_context():
    """최소 컨텍스트 생성 (독립 실행용)"""
    class MinimalContext:
        def __init__(self):
            self.master_bible = {}
            self.arcs = []

        def get_causal_history_summary(self):
            return ""

    return MinimalContext()


def create_gemini_client():
    """Gemini 클라이언트 생성"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("[ERROR] GOOGLE_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("       .env 파일에 GOOGLE_API_KEY=your_key 형태로 추가하세요.")
        sys.exit(1)

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        return client
    except ImportError:
        print("[ERROR] google-genai 패키지가 설치되지 않았습니다.")
        print("       pip install google-genai 로 설치하세요.")
        sys.exit(1)


def read_manuscript(file_path: str, encoding: str = "utf-8") -> str:
    """원고 파일 읽기"""
    path = Path(file_path)

    if not path.exists():
        print(f"[ERROR] 파일을 찾을 수 없습니다: {file_path}")
        sys.exit(1)

    try:
        with open(path, "r", encoding=encoding) as f:
            content = f.read()
        return content
    except UnicodeDecodeError:
        # UTF-8 실패 시 cp949 시도
        try:
            with open(path, "r", encoding="cp949") as f:
                content = f.read()
            print(f"[INFO] cp949 인코딩으로 읽음")
            return content
        except:
            print(f"[ERROR] 파일 인코딩을 읽을 수 없습니다. --encoding 옵션을 지정하세요.")
            sys.exit(1)


def save_bible(bible: dict, output_path: str):
    """Bible JSON 저장"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(bible, f, ensure_ascii=False, indent=2)

    print(f"\n[SUCCESS] Bible 저장 완료: {path}")


def main():
    parser = argparse.ArgumentParser(
        description="원고에서 Bible(설정집) 역설계",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python tools2/reverse_bible.py -i 기타/원고.txt -o bible/new_bible.json -g investment
  python tools2/reverse_bible.py --input novel.txt --genre wuxia
        """
    )

    parser.add_argument(
        "-i", "--input",
        required=True,
        help="입력 원고 파일 경로"
    )
    parser.add_argument(
        "-o", "--output",
        default="bible/extracted_bible.json",
        help="출력 Bible JSON 경로 (기본: bible/extracted_bible.json)"
    )
    parser.add_argument(
        "-g", "--genre",
        choices=["wuxia", "hunter", "investment"],
        default="wuxia",
        help="장르 선택 (기본: wuxia)"
    )
    parser.add_argument(
        "-m", "--mode",
        choices=["starting_point", "current_state"],
        default="starting_point",
        help="추출 모드 (기본: starting_point)"
    )
    parser.add_argument(
        "-e", "--encoding",
        default="utf-8",
        help="파일 인코딩 (기본: utf-8)"
    )
    parser.add_argument(
        "--model",
        default="gemini-2.5-pro",
        help="사용할 모델 (기본: gemini-2.5-pro)"
    )

    args = parser.parse_args()

    # 배너
    print("=" * 60)
    print("  [V60.97] Reverse Bible - 원고 역설계 도구")
    print("=" * 60)
    print(f"  입력: {args.input}")
    print(f"  출력: {args.output}")
    print(f"  장르: {args.genre}")
    print(f"  모드: {args.mode}")
    print(f"  모델: {args.model}")
    print("=" * 60)

    # 1. 원고 읽기
    print("\n[1/3] 원고 로딩 중...")
    manuscript = read_manuscript(args.input, args.encoding)
    print(f"      원고 길이: {len(manuscript):,}자")

    # 2. 클라이언트 & 컨텍스트 생성
    print("\n[2/3] Gemini 클라이언트 초기화...")
    client = create_gemini_client()
    context = create_minimal_context()

    # 3. BibleExtractor 실행
    print("\n[3/3] Bible 추출 시작...")
    from modules.domain.agents.bible_extractor import BibleExtractor

    extractor = BibleExtractor(context, client, args.model)
    bible = extractor.extract_from_manuscript(
        manuscript=manuscript,
        genre=args.genre,
        extract_mode=args.mode
    )

    # 4. 저장
    save_bible(bible, args.output)

    # 5. 요약 출력
    print("\n" + "=" * 60)
    print("  추출 결과 요약")
    print("=" * 60)

    master = bible.get("MasterBible", {})
    project = master.get("ProjectData", {})
    meta = project.get("MetaInfo", {})
    core = project.get("CoreIdentity", {})
    assets = master.get("AssetLibrary", {})
    seeds = master.get("Seeds", [])

    print(f"  제목: {meta.get('title', '?')}")
    print(f"  주인공: {core.get('protagonist', '?')}")
    print(f"  장르: {meta.get('genre_archetype', '?')}")
    print(f"  NPC 수: {len(assets.get('KeyNPCs', []))}명")
    print(f"  아이템 수: {len(assets.get('KeyItems', []))}개")
    print(f"  복선 수: {len(seeds)}개")
    print("=" * 60)

    print("\n완료! 생성된 Bible을 확인하고 필요시 수정하세요.")


if __name__ == "__main__":
    main()
