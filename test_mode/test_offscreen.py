"""화면 밖 이동 테스트 — 최소화 대신 (-3000, 0)으로 이동"""

import io
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

opts = Options()
opts.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
d = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)

# 최소화 복원 후 화면 밖으로
print("[0] 창을 화면 밖으로 이동...", flush=True)
d.set_window_position(-3000, 0)
d.set_window_size(1200, 900)
time.sleep(1)
print(f"    위치: {d.get_window_position()}", flush=True)

# 새 채팅
d.get("https://gemini.google.com/app")
time.sleep(5)

# Visibility 오버라이드
d.execute_script("""
    Object.defineProperty(Document.prototype, 'hidden', {get:function(){return false;}, configurable:true});
    Object.defineProperty(Document.prototype, 'visibilityState', {get:function(){return 'visible';}, configurable:true});
""")

# 텍스트 전송
print("[1] 전송...", flush=True)
d.execute_script("""
    var box = document.querySelector("div[contenteditable='true']");
    box.focus();
    box.innerText = "3*7=? 숫자만.";
    box.dispatchEvent(new Event('input', {bubbles: true}));
""")
time.sleep(0.5)
d.execute_script("""
    var sels = ["button[aria-label*='보내기']", "button[aria-label*='Send']", "button[aria-label*='전송']"];
    for (var i = 0; i < sels.length; i++) {
        var b = document.querySelector(sels[i]);
        if (b) { b.click(); return; }
    }
""")

# 응답 대기
print("[2] 응답 대기...", flush=True)
for i in range(120):
    stop = d.execute_script("""
        return document.querySelector("button[aria-label*='Stop'], button[aria-label*='중지']") ? 'GEN' : 'IDLE';
    """)
    rc = d.execute_script("return document.querySelectorAll('.model-response-text').length;")
    if i % 10 == 0:
        print(f"    {i}초 status={stop} resp={rc}", flush=True)
    if stop == "IDLE" and rc > 0 and i > 3:
        break
    time.sleep(1)

resp = d.execute_script("""
    var els = document.querySelectorAll('.model-response-text');
    if (!els.length) return 'NONE';
    return els[els.length-1].innerText.substring(0, 200);
""")
print(f"\n[결과] {resp}", flush=True)

if resp and resp != "NONE" and len(resp) > 0:
    print("[OK] 화면 밖 이동 방식 성공!", flush=True)
else:
    print("[FAIL]", flush=True)

# 창 복원
d.set_window_position(100, 100)
print("창 복원 완료", flush=True)
