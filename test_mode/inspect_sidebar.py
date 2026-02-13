"""사이드바 우클릭 메뉴 + 채팅 삭제 방법 탐색"""

import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

opts = Options()
opts.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)

print(f"URL: {driver.current_url}\n")

# 1. 채팅 링크에서 conversation-items-container 내부 구조 상세 확인
print("=== 1. 채팅 아이템 상세 구조 ===")
r1 = driver.execute_script("""
    const containers = document.querySelectorAll(".conversation-items-container");
    if (containers.length === 0) return "conversation-items-container NOT FOUND";
    const first = containers[0];
    return "tag=" + first.tagName + " innerHTML=" + first.innerHTML.substring(0, 1500);
""")
print(r1)

# 2. 사이드바 첫 번째 채팅 링크에 우클릭
print("\n=== 2. 우클릭 테스트 ===")
links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/app/']")
chat_link = None
for a in links:
    href = a.get_attribute("href") or ""
    if "accounts.google" in href or "SignOut" in href:
        continue
    if "/app/" in href and len(href.split("/app/")[-1]) > 8:
        chat_link = a
        break

if chat_link:
    print(f"Target: {chat_link.get_attribute('href')}")
    ActionChains(driver).context_click(chat_link).perform()
    time.sleep(1.5)

    # 메뉴 확인
    r2 = driver.execute_script("""
        const info = [];
        const overlays = document.querySelectorAll(".cdk-overlay-pane");
        info.push("overlays: " + overlays.length);
        overlays.forEach(function(o, i) {
            var txt = o.textContent.trim().substring(0, 150);
            if (txt) info.push("  overlay " + i + ": " + txt);
        });

        var items = document.querySelectorAll('[role="menuitem"], [role="menuitemradio"], [role="option"]');
        info.push("menu items: " + items.length);
        items.forEach(function(it) {
            info.push("  " + it.tagName + " text=" + it.textContent.trim().substring(0, 60));
        });
        return info.join("\\n");
    """)
    print(r2)

    # ESC
    driver.execute_script("document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));")
    time.sleep(0.5)
else:
    print("채팅 링크 못 찾음")

# 3. 긴 누르기 (long press) 또는 다른 인터랙션 테스트
print("\n=== 3. 채팅 링크 hover → 변화 확인 ===")
if chat_link:
    ActionChains(driver).move_to_element(chat_link).perform()
    time.sleep(1)

    # hover 후 새로 나타난 버튼 탐색
    r3 = driver.execute_script("""
        var info = [];
        var containers = document.querySelectorAll(".conversation-items-container");
        containers.forEach(function(c) {
            var btns = c.querySelectorAll("button");
            info.push("buttons in conversation-items-container: " + btns.length);
            btns.forEach(function(b) {
                var label = b.getAttribute("aria-label") || "";
                var txt = b.textContent.trim().substring(0, 30);
                var vis = getComputedStyle(b).visibility;
                var dis = getComputedStyle(b).display;
                info.push("  BTN aria=" + label + " text=" + txt + " vis=" + vis + " display=" + dis);
            });
        });
        return info.join("\\n");
    """)
    print(r3)

# 4. conversations-container의 직접 자식 요소들
print("\n=== 4. conversations-container 자식 ===")
r4 = driver.execute_script("""
    var info = [];
    var containers = document.querySelectorAll(".conversations-container");
    info.push("conversations-container: " + containers.length);
    containers.forEach(function(c) {
        var children = c.children;
        info.push("  children: " + children.length);
        for (var i = 0; i < Math.min(children.length, 5); i++) {
            var ch = children[i];
            info.push("  child " + i + ": " + ch.tagName + " class=" + (ch.className || "").substring(0, 60));
            // check inner structure
            var innerBtns = ch.querySelectorAll("button, [role=button]");
            info.push("    buttons inside: " + innerBtns.length);
            innerBtns.forEach(function(b) {
                info.push("      BTN aria=" + (b.getAttribute("aria-label") || "") + " text=" + b.textContent.trim().substring(0, 30));
            });
        }
    });
    return info.join("\\n");
""")
print(r4)

print("\n=== 완료 ===")
