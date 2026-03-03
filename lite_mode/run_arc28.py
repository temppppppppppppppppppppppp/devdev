"""Arc #28만 수동 재생성"""

import io
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from pathlib import Path

from bridge.gemini_driver import GeminiDriver
from bridge.prompt_builder import PromptBuilder

proj = Path("projects/test")
pb = PromptBuilder()

# 데이터 준비
bible = (proj / "bible.txt").read_text(encoding="utf-8") if (proj / "bible.txt").exists() else ""
block = (proj / "treatment/block_028.txt").read_text(encoding="utf-8")
prev_arc = ""
prev_path = proj / "stage2/arc_027.txt"
if prev_path.exists():
    prev_arc = prev_path.read_text(encoding="utf-8")

# 히스토리
hist_path = proj / "stage2/_history.txt"
history = hist_path.read_text(encoding="utf-8") if hist_path.exists() else ""

# 컨텍스트 조립
ctx = pb.build_arc_context(bible, block, prev_arc)
if history:
    ctx += f"\n\n{'=' * 50}\n[이전 분배표 누적 (참고용)]\n{'=' * 50}\n{history}"

ctx_path = proj / "stage2/arc_028_context.txt"
ctx_path.write_text(ctx, encoding="utf-8")

ep_per_arc = 5
arc_no = 28
ep_start = (28 - 1) * ep_per_arc + 1
instr = pb.build_arc_instruction(arc_no, ep_start, ep_per_arc)

print(f"컨텍스트: {len(ctx):,}자", flush=True)
print(f"Arc #{arc_no} (제{ep_start}~{ep_start + ep_per_arc - 1}화)", flush=True)

# Gemini 전송
d = GeminiDriver(model="pro", hide=True)
print("전송 중...", flush=True)
start = time.time()
resp = d.send_with_file(str(ctx_path), instr)
elapsed = int(time.time() - start)

if resp.startswith("[TIMEOUT]") or resp.startswith("[EMPTY]"):
    print(f"[FAIL] {resp} ({elapsed}초)", flush=True)
    d.show_window()
    sys.exit(1)

# 저장
out = proj / "stage2/arc_028.txt"
out.write_text(resp, encoding="utf-8")
print(f"[OK] arc_028.txt 저장 ({len(resp):,}자, {elapsed}초)", flush=True)

d.show_window()
