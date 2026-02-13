"""채팅 삭제 방법 탐색 — 사이드바 열기 + 컨텍스트 메뉴 + 대체 방법"""

import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

opts = Options()
opts.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)

# 현재 URL에서 chat ID 추출
url = driver.current_url
print(f"URL: {url}")

# 1. 사이드바 열기
print("\n=== 1. 사이드바 열기 ===")
driver.execute_script("""
    var links = document.querySelectorAll('a[href*="/app/"]');
    if (links.length < 3) {
        var toggle = document.querySelector(
            'button[aria-label*="주 메뉴"],'
            + 'button[aria-label*="Main menu"],'
            + 'button[aria-label*="메뉴"]'
        );
        if (toggle) { toggle.click(); return "sidebar toggled"; }
        return "toggle not found";
    }
    return "sidebar already open";
""")
time.sleep(1.5)

# 2. 첫 번째 대화 링크에 JS 우클릭
print("\n=== 2. JS 컨텍스트 메뉴 ===")
r2 = driver.execute_script("""
    var links = document.querySelectorAll('a[data-test-id="conversation"]');
    if (links.length === 0) {
        links = document.querySelectorAll('a.conversation');
    }
    if (links.length === 0) return "no conversation links";

    var link = links[0];
    // 컨텍스트 메뉴 이벤트 발생
    var rect = link.getBoundingClientRect();
    link.dispatchEvent(new PointerEvent("contextmenu", {
        bubbles: true, cancelable: true, composed: true,
        view: window,
        clientX: rect.left + 50, clientY: rect.top + 10
    }));
    return "contextmenu on: " + link.getAttribute("href") + " (rect: " + rect.width + "x" + rect.height + ")";
""")
print(r2)
time.sleep(1.5)

# 3. 메뉴 확인
r3 = driver.execute_script("""
    var info = [];
    var overlays = document.querySelectorAll(".cdk-overlay-pane");
    info.push("overlays: " + overlays.length);
    overlays.forEach(function(o, i) {
        var txt = o.textContent.trim().substring(0, 200);
        if (txt) info.push("  overlay " + i + ": " + txt);
    });

    var items = document.querySelectorAll('[role="menuitem"], [role="menuitemradio"], [role="option"]');
    info.push("menu items: " + items.length);
    items.forEach(function(it) {
        info.push("  " + it.tagName + " role=" + it.getAttribute("role") + " text=" + it.textContent.trim().substring(0, 60));
    });

    // mat-menu
    var mats = document.querySelectorAll("mat-menu, .mat-mdc-menu-panel, .mat-menu-panel");
    info.push("mat-menu/panel: " + mats.length);

    return info.join("\\n");
""")
print(r3)

# ESC 닫기
driver.execute_script("document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));")
time.sleep(0.5)

# 4. 대화 링크에 hover → 3초 대기 → 변화 확인
print("\n=== 4. Hover 후 변화 ===")
r4 = driver.execute_script("""
    var links = document.querySelectorAll('a[data-test-id="conversation"]');
    if (links.length === 0) return "no links";

    var link = links[0];
    // hover events
    ["pointerenter","mouseenter","mouseover","focusin","focus"].forEach(function(n) {
        link.dispatchEvent(new PointerEvent(n, {
            bubbles: true, composed: true, view: window
        }));
    });
    return "hover dispatched, rect=" + link.getBoundingClientRect().width + "x" + link.getBoundingClientRect().height;
""")
print(r4)
time.sleep(2)

r5 = driver.execute_script("""
    var info = [];
    // 전체 대화 컨테이너 내부 버튼 확인
    var containers = document.querySelectorAll(".conversation-items-container, .conversations-container");
    containers.forEach(function(c) {
        var btns = c.querySelectorAll("button, [role=button]");
        info.push("container buttons: " + btns.length);
        btns.forEach(function(b) {
            var label = b.getAttribute("aria-label") || "";
            var txt = b.textContent.trim().substring(0, 30);
            var vis = getComputedStyle(b).visibility;
            var dis = getComputedStyle(b).display;
            var w = b.getBoundingClientRect().width;
            info.push("  BTN aria=" + label + " text=" + txt + " vis=" + vis + " display=" + dis + " width=" + w);
        });
    });

    // 사이드바 전체에서 mat-icon 확인 (three dots icon 등)
    var sideNav = document.querySelector(".sidenav-with-history-container, chat-history");
    if (sideNav) {
        var icons = sideNav.querySelectorAll("mat-icon, .mat-icon");
        info.push("\\nsidebar mat-icons: " + icons.length);
        icons.forEach(function(ic) {
            info.push("  ICON text=" + ic.textContent.trim() + " class=" + (ic.className || "").substring(0, 40));
        });
    }

    return info.join("\\n");
""")
print(r5)

# 5. long press 시뮬레이션
print("\n=== 5. Long press 시뮬레이션 ===")
r6 = driver.execute_script("""
    var links = document.querySelectorAll('a[data-test-id="conversation"]');
    if (links.length === 0) return "no links";
    var link = links[0];

    link.dispatchEvent(new PointerEvent("pointerdown", {
        bubbles: true, composed: true, view: window,
        button: 0, buttons: 1
    }));
    return "pointerdown dispatched";
""")
print(r6)
time.sleep(2)

r7 = driver.execute_script("""
    var links = document.querySelectorAll('a[data-test-id="conversation"]');
    var link = links[0];
    link.dispatchEvent(new PointerEvent("pointerup", {
        bubbles: true, composed: true, view: window, button: 0
    }));

    // 메뉴 확인
    var info = [];
    var overlays = document.querySelectorAll(".cdk-overlay-pane");
    info.push("overlays after long press: " + overlays.length);
    overlays.forEach(function(o, i) {
        var txt = o.textContent.trim().substring(0, 200);
        if (txt) info.push("  overlay " + i + ": " + txt);
    });
    return info.join("\\n");
""")
print(r7)

print("\n=== 완료 ===")
