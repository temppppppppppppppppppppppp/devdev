"""
0점/누락 파일 패치 스크립트
============================
_metadata.json에서 score < 50인 파일 + 누락 파일을 자동 탐지하여 재생성.

사전 조건:
  1. Chrome 디버깅 모드:
     chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\\chrome_debug"
  2. Gemini (gemini.google.com) 로그인 + Pro 사용 가능 상태

사용법:
  python run_patch.py                          # 대화형
  python run_patch.py --project test --stage 3 # 비대화형
  python run_patch.py --project test --stage 4
"""

import argparse
import os
import sys

# Windows UTF-8 강제
if sys.platform == "win32":
    try:
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except (AttributeError, OSError):
        pass

os.system("")  # ANSI 활성화

from pathlib import Path


def select_project(name: str = None) -> Path:
    root = Path(__file__).parent / "projects"
    root.mkdir(exist_ok=True)
    projects = sorted([d for d in root.iterdir() if d.is_dir()])

    if not projects:
        print("  프로젝트가 없습니다.")
        sys.exit(1)

    # --project 인자로 지정된 경우
    if name:
        for p in projects:
            if p.name == name:
                print(f"  프로젝트: {p.name}")
                return p
        print(f"  [ERROR] 프로젝트 '{name}' 없음.")
        print(f"  사용 가능: {', '.join(p.name for p in projects)}")
        sys.exit(1)

    if len(projects) == 1:
        print(f"  프로젝트: {projects[0].name}")
        return projects[0]

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
    parser = argparse.ArgumentParser(description="0점/누락 파일 패치")
    parser.add_argument("--project", type=str, help="프로젝트 이름 (예: test)")
    parser.add_argument("--stage", type=int, choices=[3, 4], help="스테이지 (3 또는 4)")
    args = parser.parse_args()

    print(f"\n{'=' * 55}")
    print("  0점/누락 파일 패치 (Patch)")
    print(f"{'=' * 55}")

    project = select_project(args.project)

    from bridge.runner import BridgeRunner

    runner = BridgeRunner(project)

    # 스테이지 선택
    stage = args.stage
    if not stage:
        print("\n  스테이지 선택:")
        print("  3. Stage 3 (Blueprint)")
        print("  4. Stage 4 (원고)")
        sc = input("  선택 (3/4): ").strip()
        stage = int(sc) if sc in ("3", "4") else None

    if stage == 3:
        runner._patch_stage3()
    elif stage == 4:
        runner._patch_stage4()
    else:
        print("  잘못된 선택.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Ctrl+C — 중단합니다.")
        sys.exit(0)
    except Exception as e:
        print(f"\n  [ERROR] {e}")
        import traceback

        traceback.print_exc()
