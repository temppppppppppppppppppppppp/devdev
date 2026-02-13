"""최소화 상태 전체 테스트 — 페이지 로딩 대기 포함"""

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

print(f"URL: {d.current_url}", flush=True)

# Gemini 메인으로 이동 (새 채팅)
print("[0] Gemini 새 채팅 이동...", flush=True)
d.get("https://gemini.google.com/app")
time.sleep(5)

# 전송 버튼 나올 때까지 대기
print("[1] 페이지 로딩 대기...", flush=True)
for i in range(30):
    btn = d.execute_script("""
        var sels = ["button[aria-label*='Send']", "button[aria-label*='전송']", "button[aria-label*='보내기']"];
        for (var j = 0; j < sels.length; j++) {
            if (document.querySelector(sels[j])) return sels[j];
        }
        return null;
    """)
    fi = d.execute_script("return document.querySelectorAll('input[type=file]').length;")
    if btn and fi > 0:
        print(f"    OK: btn={btn}, file_inputs={fi}", flush=True)
        break
    print(f"    대기 {i + 1}... btn={btn} fi={fi}", flush=True)
    time.sleep(2)
else:
    print("    FAIL: 30회 대기 후 포기", flush=True)
    sys.exit(1)

# Visibility 확인
hidden = d.execute_script("return document.hidden;")
print(f"\n[2] hidden={hidden}", flush=True)

# 인터셉터 설치
d.execute_script("""
    if (window._uploadInterceptorInstalled) return;
    var origClick = HTMLInputElement.prototype.click;
    HTMLInputElement.prototype.click = function() {
        if (this.type === 'file') { window._interceptedFileInput = this; return; }
        return origClick.call(this);
    };
    window._interceptedFileInput = null;
    Object.defineProperty(Document.prototype, 'hidden', {get: function(){return false;}, configurable: true});
    Object.defineProperty(Document.prototype, 'visibilityState', {get: function(){return 'visible';}, configurable: true});
    window._uploadInterceptorInstalled = true;
""")
print("[3] 인터셉터 설치 완료", flush=True)

# 텍스트 전송 테스트
print("\n[4] 텍스트 전송...", flush=True)
d.execute_script("""
    var box = document.querySelector("div[contenteditable='true']");
    box.focus();
    box.innerText = "1+1=? 숫자만 답해.";
    box.dispatchEvent(new Event('input', {bubbles: true}));
    box.dispatchEvent(new Event('change', {bubbles: true}));
""")
time.sleep(0.5)

d.execute_script("""
    var sels = ["button[aria-label*='전송']", "button[aria-label*='Send']", "button[aria-label*='보내기']"];
    for (var i = 0; i < sels.length; i++) {
        var b = document.querySelector(sels[i]);
        if (b) { b.click(); return; }
    }
""")
print("    전송 완료, 응답 대기...", flush=True)

# 응답 대기 (60초)
for i in range(60):
    stop = d.execute_script("""
        var b = document.querySelector("button[aria-label*='Stop'], button[aria-label*='중지']");
        return b ? 'GENERATING' : 'IDLE';
    """)
    resp_count = d.execute_script("""
        var els = document.querySelectorAll('.model-response-text');
        return els.length;
    """)
    if i % 5 == 0:
        print(f"    {i}초... status={stop} responses={resp_count}", flush=True)
    if stop == "IDLE" and resp_count > 0 and i > 5:
        break
    time.sleep(1)

# 응답 읽기
resp = d.execute_script("""
    var els = document.querySelectorAll('.model-response-text');
    if (els.length === 0) return 'NO_RESPONSE';
    return els[els.length - 1].innerText.substring(0, 200);
""")
print(f"\n[5] 응답: {resp}", flush=True)

if resp and resp != "NO_RESPONSE":
    print("\n[OK] 최소화 상태 전송+수신 성공!", flush=True)
else:
    print("\n[FAIL] 응답 없음", flush=True)
