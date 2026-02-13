"""불량 아크 일괄 재생성 스크립트
대상: arc_032, arc_034, arc_036, arc_044, arc_045, arc_048, arc_050
"""

import io
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from pathlib import Path

from bridge.gemini_driver import GeminiDriver
from bridge.prompt_builder import PromptBuilder

# ── 설정 ──
PROJ = Path("projects/test")
BAD_ARCS = [32, 34, 36, 44, 45, 48, 50]
EP_PER_ARC = 5
MAX_RETRY = 3

# 가비지 응답 감지
GARBAGE_PATTERNS = [
    "판정: PASS",
    "판정: FAIL",
    "점수:",  # Director 평가문
    "```python",
    "import ",
    "def ",
    "print(",  # Python 코드
    "코드 표시",
    "코드 출력",  # Gemini 코드 모드
]


def is_garbage(text: str) -> str:
    """가비지면 사유 반환, 정상이면 빈 문자열."""
    if len(text) < 200:
        return f"너무 짧음 ({len(text)}자)"
    first_200 = text[:200]
    for pat in GARBAGE_PATTERNS:
        if pat in first_200:
            return f"가비지 패턴 '{pat}' 감지"
    # 에피소드 번호가 하나도 없으면 의심
    import re

    if not re.search(r"제?\d+화|ep\s*\d+|에피소드\s*\d+", text, re.IGNORECASE):
        return "에피소드 번호 없음"
    return ""


def main():
    pb = PromptBuilder()
    bible = ""
    bible_path = PROJ / "bible.txt"
    if bible_path.exists():
        bible = bible_path.read_text(encoding="utf-8")

    hist_path = PROJ / "stage2/_history.txt"
    history = hist_path.read_text(encoding="utf-8") if hist_path.exists() else ""

    print("=== 불량 아크 재생성 ===")
    print(f"대상: {BAD_ARCS}")
    print(f"EP/Arc: {EP_PER_ARC}")
    print()

    driver = GeminiDriver(model="pro", hide=True)
    success = 0
    fail = 0

    for arc_no in BAD_ARCS:
        block_path = PROJ / f"treatment/block_{arc_no:03d}.txt"
        if not block_path.exists():
            print(f"[SKIP] block_{arc_no:03d}.txt 없음")
            fail += 1
            continue

        block_text = block_path.read_text(encoding="utf-8")

        # 이전 Arc
        prev_arc = ""
        prev_path = PROJ / f"stage2/arc_{arc_no - 1:03d}.txt"
        if prev_path.exists():
            prev_arc = prev_path.read_text(encoding="utf-8")

        # 컨텍스트
        ctx = pb.build_arc_context(bible, block_text, prev_arc)
        if history:
            ctx += f"\n\n{'=' * 50}\n[이전 분배표 누적 (참고용)]\n{'=' * 50}\n{history}"
        ctx_path = PROJ / f"stage2/arc_{arc_no:03d}_context.txt"
        ctx_path.write_text(ctx, encoding="utf-8")

        ep_start = (arc_no - 1) * EP_PER_ARC + 1
        instr = pb.build_arc_instruction(arc_no, ep_start, EP_PER_ARC)

        print(f"── Arc #{arc_no} (제{ep_start}~{ep_start + EP_PER_ARC - 1}화) ──", flush=True)
        print(f"   컨텍스트: {len(ctx):,}자", flush=True)

        ok = False
        for attempt in range(MAX_RETRY):
            start = time.time()
            resp = driver.send_with_file(str(ctx_path), instr)
            elapsed = int(time.time() - start)

            if resp.startswith("[TIMEOUT]") or resp.startswith("[EMPTY]"):
                print(f"   [{resp[:9]}] {elapsed}초 — 재시도 {attempt + 1}/{MAX_RETRY}", flush=True)
                driver.reset_session()
                time.sleep(3)
                continue

            # 가비지 체크
            reason = is_garbage(resp)
            if reason:
                print(
                    f"   [GARBAGE] {reason} ({len(resp)}자, {elapsed}초) — 재시도 {attempt + 1}/{MAX_RETRY}", flush=True
                )
                driver.reset_session()
                time.sleep(3)
                continue

            # 성공
            out = PROJ / f"stage2/arc_{arc_no:03d}.txt"
            out.write_text(resp, encoding="utf-8")
            print(f"   [OK] {len(resp):,}자 저장 ({elapsed}초)", flush=True)
            ok = True
            break

        if ok:
            success += 1
        else:
            print(f"   [FAIL] {MAX_RETRY}회 실패", flush=True)
            fail += 1

    print()
    print(f"=== 완료: 성공 {success} / 실패 {fail} ===")
    driver.show_window()


if __name__ == "__main__":
    main()
