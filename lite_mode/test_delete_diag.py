"""삭제 단계별 진단 — 어디서 실패하는지 확인"""

import io
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, ".")
from bridge.gemini_driver import GeminiDriver

d = GeminiDriver(model="pro")
print(f"현재 URL: {d.driver.current_url}")

# 먼저 메시지 하나 보내서 세션 만들기
print("\n[준비] 테스트 메시지 전송...")
resp = d.send_prompt("안녕하세요. 테스트입니다.")
print(f"  응답: {resp[:80]}...")

url = d.driver.current_url
print(f"\n[Step 0] URL: {url}")
if "/app/" not in url or url.rstrip("/").endswith("/app"):
    print("  [X] 채팅 세션이 아님 (chatID 없음)")
    sys.exit(1)
chat_id = url.split("/app/")[-1].split("?")[0].split("#")[0]
print(f"  [OK] chatID: {chat_id}")

# Step 1: 사이드바
print("\n[Step 1] 사이드바 링크 확인...")
link_count = d.driver.execute_script("""
    return document.querySelectorAll('a[href*="/app/"]').length;
""")
print(f"  사이드바 링크 수: {link_count}")
if link_count < 2:
    print("  사이드바 닫힘 → 토글 시도")
    d.driver.execute_script("""
        const toggle = document.querySelector(
            'button[aria-label*="주 메뉴"],'
            + 'button[aria-label*="Main menu"],'
            + 'button[aria-label*="메뉴"],'
            + 'button[aria-label*="Close"]'
        );
        if (toggle) { toggle.click(); return "clicked"; }
        return "no toggle found";
    """)
    time.sleep(1.5)
    link_count = d.driver.execute_script("""
        return document.querySelectorAll('a[href*="/app/"]').length;
    """)
    print(f"  토글 후 링크 수: {link_count}")

# Step 2: 해당 채팅 링크 찾기
print(f"\n[Step 2] chatID={chat_id} 링크 찾기...")
link_info = d.driver.execute_script(
    """
    const cid = arguments[0];
    const all = document.querySelectorAll('a[href*="/app/"]');
    const results = [];
    for (const a of all) {
        const href = a.getAttribute("href") || "";
        results.push({
            href: href,
            text: a.textContent.trim().substring(0, 40),
            match: href.includes(cid)
        });
    }
    return JSON.stringify(results, null, 2);
""",
    chat_id,
)
print(f"  {link_info}")

# Step 3: 호버 → More options 확인
print("\n[Step 3] 호버 이벤트 디스패치...")
link = d.driver.execute_script(
    """
    const cid = arguments[0];
    let el = document.querySelector('a[href*="/app/' + cid + '"]');
    if (el) return el;
    const all = document.querySelectorAll('a[href*="/app/"]');
    for (const a of all) {
        if ((a.getAttribute("href") || "").includes(cid)) return a;
    }
    return null;
""",
    chat_id,
)

if not link:
    print("  [X] 링크 못 찾음")
    sys.exit(1)
print("  [OK] 링크 찾음")

d.driver.execute_script(
    """
    const link = arguments[0];
    let el = link;
    for (let i = 0; i < 5; i++) {
        if (!el) break;
        ['pointerenter','mouseenter','mouseover','focusin'].forEach(n => {
            el.dispatchEvent(new PointerEvent(n, {
                bubbles: true, composed: true, view: window
            }));
        });
        el = el.parentElement;
    }
""",
    link,
)
time.sleep(1)

# Step 4: More options 버튼 탐색
print("\n[Step 4] More options 버튼 탐색...")
btn_info = d.driver.execute_script(
    """
    const link = arguments[0];
    const results = [];

    // 부모 탐색
    let el = link;
    for (let i = 0; i < 7; i++) {
        el = el.parentElement;
        if (!el) break;
        const btns = el.querySelectorAll('button');
        for (const btn of btns) {
            const label = btn.getAttribute('aria-label') || '';
            const cls = btn.className || '';
            const text = btn.textContent.trim().substring(0, 20);
            const visible = getComputedStyle(btn).display !== 'none';
            const opacity = getComputedStyle(btn).opacity;
            results.push({
                level: i,
                label: label,
                class: cls.substring(0, 50),
                text: text,
                visible: visible,
                opacity: opacity,
                tag: btn.tagName
            });
        }
    }
    return JSON.stringify(results, null, 2);
""",
    link,
)
print("  부모 7단계 내 버튼들:")
print(f"  {btn_info}")

# 전체 aria-label 패턴 확인
all_btns = d.driver.execute_script("""
    const btns = document.querySelectorAll('button[aria-label]');
    const results = [];
    for (const btn of btns) {
        const label = btn.getAttribute('aria-label') || '';
        if (/more|option|옵션|더보기|삭제|delete|edit|수정/i.test(label)) {
            results.push(label);
        }
    }
    return results;
""")
print(f"\n  관련 aria-label 전체: {all_btns}")

print("\n[진단 완료]")
