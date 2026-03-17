"""
글도비라이트 V63.3 — Selenium Bridge ($0) [test_mode copy]
==========================================
Gemini 웹 자동화로 웹소설 생산. API 키 불필요.

Authority label: COMPATIBILITY / MAINTENANCE ONLY
    This is NOT part of the supported runtime authority chain.
    Supported path: geuldobi-desktop/src/main.js -> bridge_server -> process_runner -> main_a.py
    See modules/core/runtime_paths.py RUNTIME_AUTHORITY_CONTRACT for the canonical map.

사전 조건:
  1. Chrome 디버깅 모드:
     chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\\chrome_debug"
  2. Gemini (gemini.google.com) 로그인 상태

의존성:
  pip install selenium webdriver-manager beautifulsoup4

사용법:
  python main_lite.py
"""

import sys

# Windows UTF-8 강제
if sys.platform == "win32":
    try:
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

from pathlib import Path


def select_project() -> Path:
    """프로젝트 폴더 선택/생성"""
    root = Path("projects")
    root.mkdir(exist_ok=True)
    projects = sorted([d for d in root.iterdir() if d.is_dir()])

    if not projects:
        print("\n  프로젝트가 없습니다. 새 이름을 입력하세요.")
        name = input("  프로젝트명: ").strip() or "my_novel"
        p = root / name
        p.mkdir(parents=True, exist_ok=True)
        return p

    print("\n  프로젝트 선택:")
    for i, d in enumerate(projects, 1):
        print(f"    {i}. {d.name}")
    print(f"    {len(projects) + 1}. [새 프로젝트]")

    while True:
        raw = input(f"\n  선택 (1-{len(projects) + 1}): ").strip()
        try:
            idx = int(raw)
            if 1 <= idx <= len(projects):
                return projects[idx - 1]
            if idx == len(projects) + 1:
                name = input("  프로젝트명: ").strip() or "my_novel"
                p = root / name
                p.mkdir(parents=True, exist_ok=True)
                return p
        except ValueError:
            pass
        print("  잘못된 선택.")


def main():
    print("=" * 55)
    print("  글도비라이트 V63.3 — Selenium Bridge ($0)")
    print("  Gemini 웹 자동화 웹소설 생산")
    print("=" * 55)

    project = select_project()

    # 하위 폴더 자동 생성
    for d in ["treatment", "stage2", "stage3", "stage4"]:
        (project / d).mkdir(exist_ok=True)

    print(f"\n  프로젝트: {project.name}")
    print(f"  위치: {project.resolve()}")

    from bridge.runner import BridgeRunner

    BridgeRunner(project).run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  종료합니다.")
        sys.exit(0)
    except Exception as e:
        print(f"\n  오류: {e}")
        import traceback

        traceback.print_exc()
