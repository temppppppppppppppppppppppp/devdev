"""
Treatment 분리기
================
하나의 txt 파일을 ⓚ 기준으로 잘라서
projects/{프로젝트}/treatment/block_001.txt, block_002.txt, ... 로 저장.

사용법:
  python split_treatment.py
"""

import sys
from pathlib import Path

DELIMITER = "ⓚ"


def select_project() -> Path:
    root = Path("projects")
    root.mkdir(exist_ok=True)
    projects = sorted([d for d in root.iterdir() if d.is_dir()])

    if not projects:
        print("  프로젝트가 없습니다. 먼저 main_lite.py를 실행하세요.")
        sys.exit(1)

    print("\n  프로젝트 선택:")
    for i, d in enumerate(projects, 1):
        print(f"    {i}. {d.name}")

    while True:
        raw = input(f"\n  선택 (1-{len(projects)}): ").strip()
        try:
            idx = int(raw)
            if 1 <= idx <= len(projects):
                return projects[idx - 1]
        except ValueError:
            pass


def main():
    print("=" * 50)
    print(f"  Treatment 분리기 (구분자: {DELIMITER})")
    print("=" * 50)

    # 파일 선택
    src = input("\n  Treatment 원본 파일 경로: ").strip().strip('"')
    src = Path(src)
    if not src.exists():
        print(f"  파일 없음: {src}")
        return

    text = src.read_text(encoding="utf-8")

    # ⓚ로 분리
    blocks = [b.strip() for b in text.split(DELIMITER) if b.strip()]

    # 헤더/설명 부분 스킵 (=== 로 시작하는 블록)
    cleaned = []
    for b in blocks:
        lines = b.strip().split("\n")
        # 첫 줄이 === 로 시작하면 설명 블록 → 스킵
        if lines[0].startswith("==="):
            continue
        cleaned.append(b)

    if not cleaned:
        print("  블록이 없습니다. ⓚ 구분자를 확인하세요.")
        return

    print(f"\n  {len(cleaned)}개 블록 발견")
    for i, b in enumerate(cleaned, 1):
        preview = b[:60].replace("\n", " ")
        print(f"    {i}. {preview}...")

    # 프로젝트 선택
    project = select_project()
    treatment_dir = project / "treatment"
    treatment_dir.mkdir(exist_ok=True)

    # 기존 파일 확인
    existing = sorted(treatment_dir.glob("block_*.txt"))
    if existing:
        print(f"\n  [!] treatment/ 에 이미 {len(existing)}개 파일 있음")
        choice = input("  덮어쓰기? (y/N): ").strip().lower()
        if choice != "y":
            print("  취소.")
            return

    # 저장
    for i, block in enumerate(cleaned, 1):
        out = treatment_dir / f"block_{i:03d}.txt"
        out.write_text(block, encoding="utf-8")

    print(f"\n  {len(cleaned)}개 블록 → {treatment_dir}/")
    for i in range(1, len(cleaned) + 1):
        print(f"    block_{i:03d}.txt")
    print("\n  완료!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n  취소.")
