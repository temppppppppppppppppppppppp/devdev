"""
Gemini UI 셀렉터 진단 스크립트
Chrome --remote-debugging-port=9222 상태에서 실행
gemini.google.com/app 페이지가 열려있어야 함
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

opts = Options()
opts.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)

print(f"현재 URL: {driver.current_url}\n")

# 1. 모델 피커 관련 요소
print("=" * 60)
print("1. 모델 피커 관련 요소")
print("=" * 60)
result = driver.execute_script("""
    const info = [];

    // model-picker-container (기존)
    const picker = document.querySelector('.model-picker-container');
    info.push('[기존] .model-picker-container: ' + (picker ? picker.textContent.trim() : 'NOT FOUND'));

    // class에 model 포함
    const modelEls = document.querySelectorAll('[class*="model"]');
    info.push('\\n[class*="model"] 요소 (' + modelEls.length + '개):');
    modelEls.forEach((el, i) => {
        if (i < 15) {
            const tag = el.tagName;
            const cls = el.className.toString().substring(0, 80);
            const txt = el.textContent.trim().substring(0, 60);
            info.push('  ' + tag + ' | class=' + cls + ' | text=' + txt);
        }
    });

    // class에 picker 포함
    const pickerEls = document.querySelectorAll('[class*="picker"]');
    info.push('\\n[class*="picker"] 요소 (' + pickerEls.length + '개):');
    pickerEls.forEach((el, i) => {
        if (i < 10) {
            const tag = el.tagName;
            const cls = el.className.toString().substring(0, 80);
            const txt = el.textContent.trim().substring(0, 60);
            info.push('  ' + tag + ' | class=' + cls + ' | text=' + txt);
        }
    });

    // data-test-id에 model 포함
    const testIdEls = document.querySelectorAll('[data-test-id*="model"]');
    info.push('\\n[data-test-id*="model"] 요소 (' + testIdEls.length + '개):');
    testIdEls.forEach((el, i) => {
        const tag = el.tagName;
        const tid = el.getAttribute('data-test-id');
        const txt = el.textContent.trim().substring(0, 60);
        info.push('  ' + tag + ' | data-test-id=' + tid + ' | text=' + txt);
    });

    return info.join('\\n');
""")
print(result)

# 2. 입력 영역 근처 드롭다운/버튼
print("\n" + "=" * 60)
print("2. 입력 영역 근처 버튼/드롭다운")
print("=" * 60)
result2 = driver.execute_script("""
    const info = [];

    // contenteditable 근처 탐색
    const editor = document.querySelector("div[contenteditable='true']")
                || document.querySelector("textarea");
    if (!editor) {
        info.push('입력 영역 못 찾음');
        return info.join('\\n');
    }
    info.push('입력 영역: ' + editor.tagName + ' class=' + (editor.className || ''));

    // 입력 영역 부모들에서 button/select 요소 탐색
    let parent = editor;
    for (let i = 0; i < 10; i++) {
        parent = parent.parentElement;
        if (!parent) break;
        const btns = parent.querySelectorAll('button, [role="listbox"], [role="combobox"]');
        if (btns.length > 0 && btns.length < 30) {
            info.push('\\n부모 레벨 ' + i + ' (' + parent.tagName + '.' + (parent.className || '').substring(0,40) + '):');
            btns.forEach((b, j) => {
                if (j < 15) {
                    const label = b.getAttribute('aria-label') || '';
                    const txt = b.textContent.trim().substring(0, 50);
                    const cls = (b.className || '').toString().substring(0, 50);
                    info.push('  ' + b.tagName + ' | aria=' + label + ' | text=' + txt + ' | class=' + cls);
                }
            });
            break;
        }
    }
    return info.join('\\n');
""")
print(result2)

# 3. Pro/빠른 모드/사고 모드 텍스트가 포함된 요소
print("\n" + "=" * 60)
print("3. Pro / 빠른 모드 / 사고 모드 텍스트 포함 요소")
print("=" * 60)
result3 = driver.execute_script("""
    const info = [];
    const keywords = ['Pro', '빠른', 'Flash', 'Think', '사고', 'model', 'Gemini'];
    const allButtons = document.querySelectorAll('button');
    info.push('전체 버튼 수: ' + allButtons.length);
    info.push('\\n모델 관련 텍스트 포함 버튼:');
    allButtons.forEach(btn => {
        const txt = btn.textContent.trim();
        const label = btn.getAttribute('aria-label') || '';
        for (const kw of keywords) {
            if (txt.includes(kw) || label.includes(kw)) {
                const cls = (btn.className || '').toString().substring(0, 60);
                const parent_cls = btn.parentElement ? (btn.parentElement.className || '').toString().substring(0, 40) : '';
                info.push('  BTN | text=' + txt.substring(0,60) + ' | aria=' + label + ' | class=' + cls + ' | parent_class=' + parent_cls);
                break;
            }
        }
    });

    // 드롭다운/메뉴 관련
    const menus = document.querySelectorAll('[role="menu"], [role="listbox"], .mat-mdc-menu-panel');
    info.push('\\n현재 열린 메뉴: ' + menus.length + '개');
    menus.forEach(m => {
        info.push('  MENU | class=' + (m.className || '').toString().substring(0, 60) + ' | text=' + m.textContent.trim().substring(0, 80));
    });

    return info.join('\\n');
""")
print(result3)

# 4. 파일 업로드 관련 버튼
print("\n" + "=" * 60)
print("4. 파일 업로드 관련 버튼")
print("=" * 60)
result4 = driver.execute_script("""
    const info = [];
    const allButtons = document.querySelectorAll('button');
    info.push('업로드/파일/첨부 관련 버튼:');
    allButtons.forEach(btn => {
        const label = btn.getAttribute('aria-label') || '';
        const txt = btn.textContent.trim();
        if (label.includes('업로드') || label.includes('upload') || label.includes('Upload')
            || label.includes('파일') || label.includes('file') || label.includes('File')
            || label.includes('첨부') || label.includes('attach') || label.includes('Attach')
            || label.includes('Add') || label.includes('추가')) {
            const cls = (btn.className || '').toString().substring(0, 60);
            info.push('  BTN | aria=' + label + ' | text=' + txt.substring(0,40) + ' | class=' + cls);
        }
    });

    // input[type=file] 요소
    const fileInputs = document.querySelectorAll('input[type="file"]');
    info.push('\\ninput[type="file"]: ' + fileInputs.length + '개');
    fileInputs.forEach((inp, i) => {
        info.push('  INPUT | accept=' + (inp.accept || '') + ' | name=' + (inp.name || '') + ' | id=' + (inp.id || ''));
    });

    return info.join('\\n');
""")
print(result4)

# 5. 사이드바 More options 관련
print("\n" + "=" * 60)
print("5. 사이드바 / More options 관련")
print("=" * 60)
result5 = driver.execute_script("""
    const info = [];

    // 사이드바 대화 링크
    const links = document.querySelectorAll('a[href*="/app/"]');
    info.push('사이드바 대화 링크: ' + links.length + '개');
    links.forEach((a, i) => {
        if (i < 5) {
            info.push('  A | href=' + a.getAttribute('href') + ' | text=' + a.textContent.trim().substring(0, 40));
        }
    });

    // More/옵션 관련 버튼
    info.push('\\nMore/옵션 aria-label 버튼:');
    const allBtns = document.querySelectorAll('button');
    allBtns.forEach(btn => {
        const label = btn.getAttribute('aria-label') || '';
        if (/more|option|옵션|더보기|삭제/i.test(label)) {
            const vis = getComputedStyle(btn).visibility;
            const display = getComputedStyle(btn).display;
            const opacity = getComputedStyle(btn).opacity;
            info.push('  BTN | aria=' + label + ' | vis=' + vis + ' | display=' + display + ' | opacity=' + opacity);
        }
    });

    return info.join('\\n');
""")
print(result5)

print("\n" + "=" * 60)
print("진단 완료")
print("=" * 60)
