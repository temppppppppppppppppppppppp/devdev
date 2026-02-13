"""
스테이지 비대화형 실행 스크립트
================================
사전 조건:
  1. Chrome 디버깅 모드:
     chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\\chrome_debug"
  2. Gemini (gemini.google.com) 로그인 + Pro 사용 가능 상태

사용법:
  python run_stage.py --project 조상님 --stage 2
  python run_stage.py --project 조상님 --stage 2 --visible
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


def select_project(name: str) -> Path:
    root = Path(__file__).parent / "projects"
    root.mkdir(exist_ok=True)
    projects = sorted([d for d in root.iterdir() if d.is_dir()])

    if not projects:
        print("  프로젝트가 없습니다.")
        sys.exit(1)

    for p in projects:
        if p.name == name:
            print(f"  프로젝트: {p.name}")
            return p

    print(f"  [ERROR] 프로젝트 '{name}' 없음.")
    print(f"  사용 가능: {', '.join(p.name for p in projects)}")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="스테이지 비대화형 실행")
    parser.add_argument("--project", type=str, required=True, help="프로젝트 이름 (예: 조상님)")
    parser.add_argument("--stage", type=int, choices=[2, 3, 4], required=True, help="스테이지 (2, 3, 4)")
    parser.add_argument("--visible", action="store_true", help="Chrome 창 표시 (기본: 숨김)")
    args = parser.parse_args()

    hide = not args.visible

    print(f"\n{'=' * 55}")
    print(f"  Stage {args.stage} 실행{' (Chrome 표시)' if args.visible else ''}")
    print(f"{'=' * 55}")

    project = select_project(args.project)

    # 하위 폴더 자동 생성
    for d in ["treatment", "stage2", "stage3", "stage4"]:
        (project / d).mkdir(exist_ok=True)

    from bridge.runner import BridgeRunner

    runner = BridgeRunner(project)

    if args.stage == 2:
        runner.run_stage_2(auto=True, hide=hide)
    elif args.stage == 3:
        runner.run_stage_3(auto=True, hide=hide)
    elif args.stage == 4:
        runner.run_stage_4(auto=True, hide=hide)


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
