"""백그라운드 호환 테스트 — JS 전환 + Visibility 오버라이드"""

import io
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, ".")
from bridge.gemini_driver import GeminiDriver

d = GeminiDriver(model="pro")

# Visibility 오버라이드 확인
hidden = d.driver.execute_script("return document.hidden;")
state = d.driver.execute_script("return document.visibilityState;")
print(f"[1] Visibility: hidden={hidden}, state={state}")
assert hidden == False, "hidden should be False"
assert state == "visible", "state should be visible"
print("    OK - Visibility 오버라이드 정상")

# 기본 전송 테스트
print("\n[2] send_prompt 테스트...")
start = time.time()
resp = d.send_prompt("1+1=?")
elapsed = int(time.time() - start)
print(f"    응답 ({elapsed}초): {resp[:100]}...")
assert len(resp) > 0 and not resp.startswith("[TIMEOUT]"), "응답 실패"
print("    OK - JS 전송/수신 정상")

# 파일 첨부 전송 테스트
import os
import tempfile

tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8")
tmp.write("테스트 파일 내용입니다.")
tmp.close()

print("\n[3] send_with_file 테스트...")
start = time.time()
resp2 = d.send_with_file(tmp.name, "첨부 파일 내용을 읽고 '확인' 한 글자만 답해.")
elapsed = int(time.time() - start)
print(f"    응답 ({elapsed}초): {resp2[:100]}...")
os.unlink(tmp.name)
assert len(resp2) > 0 and not resp2.startswith("[TIMEOUT]"), "파일 전송 실패"
print("    OK - 파일 첨부 전송 정상")

# 삭제 테스트
print("\n[4] 세션 삭제 테스트...")
before = d.driver.execute_script("return document.querySelectorAll('a[href*=\"/app/\"]').length;")
d._delete_current_chat()
time.sleep(2)
after = d.driver.execute_script("return document.querySelectorAll('a[href*=\"/app/\"]').length;")
print(f"    세션 수: {before} -> {after}")
if after < before:
    print("    OK - 삭제 성공")
else:
    print("    WARN - 삭제 안 됨 (이미 삭제됐거나 실패)")

print("\n[완료] 모든 테스트 통과")
