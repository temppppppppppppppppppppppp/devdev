"""최소화 상태 개별 메서드 테스트 — 각각 15초 타임아웃"""

import io
import sys
import threading

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# 직접 연결 (GeminiDriver 안 거침)
opts = Options()
opts.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
d = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)


def timeout_test(name, fn, sec=15):
    result = [None]

    def run():
        try:
            result[0] = fn()
        except Exception as e:
            result[0] = f"ERROR: {e}"

    t = threading.Thread(target=run)
    t.start()
    t.join(timeout=sec)
    if t.is_alive():
        print(f"  [{name}] TIMEOUT ({sec}s) - BLOCKED", flush=True)
        return False
    else:
        print(f"  [{name}] OK: {str(result[0])[:100]}", flush=True)
        return True


print("=== 최소화 상태 개별 테스트 ===\n", flush=True)

# 1. execute_script 기본
timeout_test("JS기본", lambda: d.execute_script("return 1+1;"))

# 2. document.hidden
timeout_test("hidden", lambda: d.execute_script("return document.hidden;"))

# 3. URL 읽기
timeout_test("URL", lambda: d.current_url)

# 4. find_element
timeout_test("find_input", lambda: d.find_element(By.CSS_SELECTOR, "div[contenteditable='true']").tag_name)

# 5. JS로 텍스트 입력
timeout_test(
    "JS입력",
    lambda: d.execute_script("""
    var box = document.querySelector("div[contenteditable='true']");
    if (!box) return "NO_BOX";
    box.focus();
    box.innerText = "test";
    box.dispatchEvent(new Event('input', {bubbles: true}));
    return "len=" + box.innerText.length;
"""),
)

# 6. JS로 전송버튼 찾기
timeout_test(
    "JS전송btn",
    lambda: d.execute_script("""
    var sels = ["button[aria-label*='Send']", "button[aria-label*='전송']", "button[aria-label*='보내기']"];
    for (var i = 0; i < sels.length; i++) {
        var b = document.querySelector(sels[i]);
        if (b) return sels[i] + " disabled=" + b.disabled;
    }
    return "NOT_FOUND";
"""),
)

# 7. JS로 전송버튼 클릭
timeout_test(
    "JS클릭",
    lambda: d.execute_script("""
    var sels = ["button[aria-label*='Send']", "button[aria-label*='전송']", "button[aria-label*='보내기']"];
    for (var i = 0; i < sels.length; i++) {
        var b = document.querySelector(sels[i]);
        if (b) { b.click(); return "clicked " + sels[i]; }
    }
    return "NOT_FOUND";
"""),
)

# 8. 파일 input 찾기
timeout_test(
    "file_input",
    lambda: d.execute_script("""
    var inputs = document.querySelectorAll('input[type="file"]');
    return "file inputs: " + inputs.length;
"""),
)

# 9. WebDriverWait (presence)
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

timeout_test(
    "Wait_presence",
    lambda: WebDriverWait(d, 5)
    .until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true']")))
    .tag_name,
)


# 10. send_keys (네이티브)
def test_sendkeys():
    box = d.find_element(By.CSS_SELECTOR, "div[contenteditable='true']")
    box.send_keys("x")
    return "sent"


timeout_test("send_keys", test_sendkeys)

print("\n=== 완료 ===", flush=True)
