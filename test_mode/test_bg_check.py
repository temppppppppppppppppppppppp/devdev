"""최소화 상태 진단 — 입력창/버튼 상태 확인"""

import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

opts = Options()
opts.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
d = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)

print("URL:", d.current_url)

# 입력창에 텍스트가 남아있는지
box_text = d.execute_script("""
    var box = document.querySelector("div[contenteditable='true']");
    if (!box) return "NO_BOX";
    return "len=" + box.innerText.length + " text=" + box.innerText.substring(0, 80);
""")
print("Input box:", box_text)

# 전송 버튼 상태
btn_info = d.execute_script("""
    var sels = ["button[aria-label*='Send']", "button[aria-label*='전송']", "button[aria-label*='보내기']"];
    for (var i = 0; i < sels.length; i++) {
        var b = document.querySelector(sels[i]);
        if (b) return sels[i] + " disabled=" + b.disabled + " display=" + getComputedStyle(b).display;
    }
    return "NOT_FOUND";
""")
print("Send btn:", btn_info)

# 응답 영역
resp_count = d.execute_script("""
    var sels = [".model-response-text", ".response-container", "model-response"];
    for (var i = 0; i < sels.length; i++) {
        var els = document.querySelectorAll(sels[i]);
        if (els.length > 0) return sels[i] + " count=" + els.length;
    }
    return "no responses found";
""")
print("Responses:", resp_count)

# 중지 버튼 (생성 중인지)
stop = d.execute_script("""
    var btn = document.querySelector("button[aria-label*='Stop'], button[aria-label*='중지']");
    return btn ? "GENERATING" : "IDLE";
""")
print("Status:", stop)

# hidden 상태
hidden = d.execute_script("return document.hidden;")
vis = d.execute_script("return document.visibilityState;")
print("Visibility: hidden=" + str(hidden) + " state=" + str(vis))
