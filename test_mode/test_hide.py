"""hide_window 통합 테스트"""

import io
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, ".")
from bridge.gemini_driver import GeminiDriver

print("[1] GeminiDriver(hide=True)...", flush=True)
d = GeminiDriver(model="pro", hide=True)
pos = d.driver.get_window_position()
print(f"    위치: {pos} hidden={d._hidden}", flush=True)

print("[2] 전송 테스트...", flush=True)
start = time.time()
resp = d.send_prompt("2+2=? 숫자만.")
elapsed = int(time.time() - start)
print(f"    응답 ({elapsed}초): {resp[:80]}", flush=True)

print("[3] show_window()...", flush=True)
d.show_window()
pos2 = d.driver.get_window_position()
print(f"    위치: {pos2} hidden={d._hidden}", flush=True)

print("[OK] 완료", flush=True)
