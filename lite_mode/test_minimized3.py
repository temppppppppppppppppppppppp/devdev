"""최소화 상태 텍스트 전송 테스트"""

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

# 새 채팅
d.get("https://gemini.google.com/app")
time.sleep(5)

# Visibility 오버라이드
d.execute_script("""
    Object.defineProperty(Document.prototype, 'hidden', {get:function(){return false;}, configurable:true});
    Object.defineProperty(Document.prototype, 'visibilityState', {get:function(){return 'visible';}, configurable:true});
    document.addEventListener('visibilitychange', function(e){e.stopImmediatePropagation();}, true);
    window.addEventListener('blur', function(e){e.stopImmediatePropagation();}, true);
""")
print(f"hidden={d.execute_script('return document.hidden;')}", flush=True)

# 텍스트 입력
print("[1] 텍스트 입력...", flush=True)
d.execute_script("""
    var box = document.querySelector("div[contenteditable='true']");
    box.focus();
    box.innerText = "3 곱하기 7은? 숫자만 답해.";
    box.dispatchEvent(new Event('input', {bubbles: true}));
    box.dispatchEvent(new Event('change', {bubbles: true}));
    box.dispatchEvent(new KeyboardEvent('keydown', {key:' ',code:'Space',bubbles:true}));
    box.dispatchEvent(new KeyboardEvent('keyup', {key:' ',code:'Space',bubbles:true}));
""")
time.sleep(1)

# 전송 클릭
print("[2] 전송 클릭...", flush=True)
d.execute_script("""
    var sels = ["button[aria-label*='보내기']", "button[aria-label*='Send']", "button[aria-label*='전송']"];
    for (var i = 0; i < sels.length; i++) {
        var b = document.querySelector(sels[i]);
        if (b) { b.click(); return; }
    }
""")

# 응답 대기
print("[3] 응답 대기...", flush=True)
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

# 응답 읽기
resp = d.execute_script("""
    var els = document.querySelectorAll('.model-response-text');
    if (!els.length) return 'NONE';
    return els[els.length-1].innerText.substring(0, 200);
""")
print(f"\n[결과] {resp}", flush=True)
print("[OK]" if resp and resp != "NONE" else "[FAIL]", flush=True)
