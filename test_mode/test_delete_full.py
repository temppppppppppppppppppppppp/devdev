"""삭제 전체 흐름 테스트 — 실제로 삭제까지"""

import io
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, ".")
from bridge.gemini_driver import GeminiDriver

d = GeminiDriver(model="pro")


# 세션 수 카운트
def count_sessions():
    return d.driver.execute_script("""
        return document.querySelectorAll('a[href*="/app/"]').length;
    """)


before = count_sessions()
print(f"[시작] 사이드바 세션 수: {before}")

# 테스트 메시지 전송
print("[1] 테스트 메시지 전송...")
resp = d.send_prompt("테스트")
print(f"  응답: {resp[:50]}...")
print(f"  URL: {d.driver.current_url}")

after_send = count_sessions()
print(f"  전송 후 세션 수: {after_send}")

# 삭제 시도
print("\n[2] _delete_current_chat() 호출...")
result = d._delete_current_chat()
print(f"  결과: {result}")
time.sleep(2)

after_del = count_sessions()
print(f"  삭제 후 세션 수: {after_del}")

if after_del < after_send:
    print(f"  [OK] 삭제 성공 ({after_send} -> {after_del})")
else:
    print(f"  [FAIL] 삭제 안 됨 ({after_send} -> {after_del})")

    # 실패 시 수동 진단: 드롭다운 메뉴가 떠 있는지 확인
    menus = d.driver.execute_script("""
        const panels = document.querySelectorAll('.mat-mdc-menu-panel, [role="menu"]');
        const results = [];
        for (const p of panels) {
            const items = p.querySelectorAll('[role="menuitem"], button');
            const texts = [];
            for (const item of items) texts.push(item.textContent.trim());
            results.push({visible: getComputedStyle(p).display, items: texts});
        }
        return JSON.stringify(results);
    """)
    print(f"  현재 열린 메뉴: {menus}")

    # 확인 모달이 떠 있는지
    dialogs = d.driver.execute_script("""
        const dlgs = document.querySelectorAll(
            'mat-dialog-container, [role="dialog"], [role="alertdialog"]');
        const results = [];
        for (const d of dlgs) {
            const btns = d.querySelectorAll('button');
            const texts = [];
            for (const b of btns) texts.push(b.textContent.trim());
            results.push({btns: texts, text: d.textContent.trim().substring(0, 100)});
        }
        return JSON.stringify(results);
    """)
    print(f"  현재 열린 다이얼로그: {dialogs}")

print(f"\n[종료] 최종 세션 수: {count_sessions()}")
