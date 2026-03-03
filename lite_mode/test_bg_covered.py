"""창 가린 상태 테스트 — 10초 후 전송 (그 사이 다른 창으로 가리기)"""

import io
import os
import sys
import tempfile
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, ".")
from bridge.gemini_driver import GeminiDriver

d = GeminiDriver(model="pro")

print("=" * 50)
print("  10초 안에 Chrome 창을 다른 창으로 가리세요!")
print("=" * 50)
for i in range(10, 0, -1):
    print(f"  {i}...", flush=True)
    time.sleep(1)

print("\n[1] Visibility 확인...")
hidden = d.driver.execute_script("return document.hidden;")
state = d.driver.execute_script("return document.visibilityState;")
print(f"    hidden={hidden}, state={state}")

# 파일 첨부 테스트
tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8")
tmp.write("이것은 백그라운드 테스트 파일입니다. 숫자: 42")
tmp.close()

print("\n[2] send_with_file 테스트 (창 가린 상태)...")
start = time.time()
resp = d.send_with_file(tmp.name, "첨부 파일에 있는 숫자가 뭐야? 숫자만 답해.")
elapsed = int(time.time() - start)
os.unlink(tmp.name)

print(f"    응답 ({elapsed}초): {resp[:150]}...")
if resp.startswith("[TIMEOUT]") or resp.startswith("[EMPTY]"):
    print("    [FAIL] 응답 실패")
else:
    print("    [OK] 파일 첨부 + 응답 성공")

# 텍스트 전송 테스트
print("\n[3] send_prompt 테스트 (창 가린 상태)...")
start = time.time()
resp2 = d.send_prompt("3 * 7 = ? 숫자만 답해.")
elapsed = int(time.time() - start)
print(f"    응답 ({elapsed}초): {resp2[:150]}...")
if resp2.startswith("[TIMEOUT]") or resp2.startswith("[EMPTY]"):
    print("    [FAIL] 응답 실패")
else:
    print("    [OK] 텍스트 전송 + 응답 성공")

print("\n[완료]")
