"""
[V63.4] Gemini Web Driver - Selenium 자동화
=============================================
순수 Selenium만으로 파일 업로드 + 채팅 자동화.
pyautogui/ctypes/IME 불필요. HTMLInputElement.click() hijack 방식.

사전 조건:
  chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\\chrome_debug"

의존성:
  pip install selenium webdriver-manager beautifulsoup4
"""

import json
import os
import re
import time
from pathlib import Path

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

try:
    from bridge.ui_discovery import UIDiscovery
except ImportError:
    try:
        from ui_discovery import UIDiscovery
    except ImportError:
        UIDiscovery = None


def _extract_text(html: str) -> str:
    """HTML에서 텍스트 추출 (Gemini 응답용)"""
    soup = BeautifulSoup(html, "html.parser")
    for tag in [
        "source-footnote",
        "sources-carousel-inline",
        "source-inline-chips",
        "mat-icon",
        "share-button",
        "more-button",
        "thumbs-up-down",
    ]:
        for t in soup.select(tag):
            t.decompose()
    text = soup.get_text("\n\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return _clean_response(text)


def _clean_response(text: str) -> str:
    """Gemini 응답 노이즈 제거"""
    # 앞부분 노이즈: "분석\n분석\n쿼리 성공" 등 Gemini UI 잔여물
    text = re.sub(r"^(?:분석\s*\n*)+(?:쿼리 성공\s*\n*)?", "", text, flags=re.MULTILINE).lstrip()
    # 뒷부분 노이즈: 끝에서부터 반복 제거 (2패스)
    tail_patterns = [
        r"\n*소스\s*$",  # Gemini "소스" 꼬리표
        r"\n*Would you like.*$",
        r"\n*Do you want.*$",
        r"\n*Let me know.*$",
        r"\n*If you need.*$",
        r"\n*Is there anything.*$",
        r"\n*도움이 되셨.*$",
        r"\n*수정이 필요하.*$",
        r"\n*추가로 원하시.*$",
        r"\n*더 필요하신.*$",
        r"\n*다른 것이 필요.*$",
        r"\n*.*드릴까요.*$",
        r"\n*.*할까요\??\s*$",
        r"\n*.*하시겠어요.*$",
    ]
    for _ in range(2):  # 2패스: 소스 제거 후 영어 멘트 제거
        for p in tail_patterns:
            text = re.sub(p, "", text)
        text = text.rstrip()
    return text.rstrip()


# ── 응답 셀렉터 (우선순위) ──────────────────────────────

# Gemini 모델 응답 영역 — 구체적 → 범용 순서로 시도
_RESPONSE_SELECTORS = [
    "model-response .markdown",  # 표준 마크다운 응답
    "model-response message-content",  # 메시지 콘텐츠
    "model-response",  # 모델 응답 루트
    ".response-container .markdown",  # 대체 구조
    "message-content",  # 최후 폴백
]

# 생성 중 표시 (중지 버튼)
_STOP_SELECTOR = "button[aria-label*='중지'], button[aria-label*='Stop'], button[aria-label*='stop']"


# ── 메인 드라이버 ────────────────────────────────────────


class GeminiDriver:
    """Gemini 웹 Selenium 자동화 드라이버 (pyautogui 불필요)"""

    # 모델명 → 메뉴 텍스트 매핑
    MODEL_MAP = {
        "fast": "빠른 모드",
        "think": "사고 모드",
        "pro": "Pro",
    }

    def __init__(
        self,
        debug_port: int = 9222,
        model: str = "pro",
        hide: bool = False,
        log_func=None,
        api_key: str = "",
        cache_dir: Path = None,
    ):
        self._log = log_func or print
        opts = Options()
        opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
        try:
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=opts,
            )
        except Exception as e:
            raise RuntimeError(
                f"Chrome 디버깅 모드 연결 실패 (port {debug_port}).\n"
                f"먼저 실행: chrome.exe --remote-debugging-port={debug_port} "
                f'--user-data-dir="C:\\chrome_debug"\n'
                f"에러: {e}"
            )
        self.wait = WebDriverWait(self.driver, 15)
        self._model = model
        self._hidden = False
        self._ui = None  # UIDiscovery 인스턴스

        # Gemini 페이지가 아닌 경우 이동
        if "gemini.google.com" not in self.driver.current_url:
            self.driver.get("https://gemini.google.com/app")
            time.sleep(4)

        # 항상 최대화로 시작 — UI 요소가 제대로 렌더링되어야 함
        try:
            self.driver.maximize_window()
        except Exception:
            pass
        time.sleep(1)

        self._install_upload_interceptor()

        # UI 자동 탐지 — API 키가 있으면 활성화
        if not api_key:
            api_key = self._load_api_key(cache_dir)
        if api_key and UIDiscovery:
            try:
                cd = cache_dir or Path(".")
                self._ui = UIDiscovery(self.driver, api_key, cd, log_func=self._log)
                self._ui.calibrate()
            except Exception as e:
                self._log(f"[UI탐지] 초기화 실패: {e} — 하드코딩 모드")
                self._ui = None

        self.select_model(model)

        # 모든 초기화 완료 후 숨기기
        if hide:
            self.hide_window()

    @staticmethod
    def _load_api_key(cache_dir: Path = None) -> str:
        """cache_dir 또는 상위에서 .env 파일 읽어 API 키 추출"""
        search = []
        if cache_dir:
            search.append(cache_dir / ".env")
            search.append(cache_dir.parent / ".env")
        search.append(Path(".") / ".env")
        search.append(Path(".").parent / ".env")
        for p in search:
            try:
                if p.exists():
                    for line in p.read_text(encoding="utf-8").splitlines():
                        line = line.strip()
                        if line.startswith("GOOGLE_API_KEY"):
                            return line.split("=", 1)[1].strip()
            except Exception:
                continue
        return ""

    def hide_window(self):
        """Chrome 창을 화면 밖으로 이동 (최소화 대신 — 렌더링 유지)"""
        try:
            # 최소화 상태면 먼저 복원
            self.driver.set_window_size(1200, 900)
            self.driver.set_window_position(-3000, 0)
            self._hidden = True
        except Exception:
            pass

    def show_window(self):
        """Chrome 창을 화면 안으로 복원"""
        try:
            self.driver.set_window_position(100, 100)
            self._hidden = False
        except Exception:
            pass

    def _install_upload_interceptor(self):
        """HTMLInputElement.click() hijack — 파일 다이얼로그 차단
        + Page Visibility API 오버라이드 — 백그라운드 쓰로틀링 방지"""
        self.driver.execute_script("""
            if (window._uploadInterceptorInstalled) return;

            // ── 파일 업로드 인터셉터 ──
            const origClick = HTMLInputElement.prototype.click;
            HTMLInputElement.prototype.click = function() {
                if (this.type === 'file') {
                    window._interceptedFileInput = this;
                    return;
                }
                return origClick.call(this);
            };
            window._interceptedFileInput = null;

            // ── Page Visibility 오버라이드 (항상 visible) ──
            Object.defineProperty(Document.prototype, 'hidden', {
                get: () => false, configurable: true
            });
            Object.defineProperty(Document.prototype, 'visibilityState', {
                get: () => 'visible', configurable: true
            });
            document.addEventListener('visibilitychange', e => {
                e.stopImmediatePropagation();
            }, true);
            window.addEventListener('blur', e => {
                e.stopImmediatePropagation();
            }, true);

            window._uploadInterceptorInstalled = true;
        """)

    def select_model(self, model: str = ""):
        """Gemini 모델/모드 선택. model: 'fast'|'think'|'pro'"""
        target = model or self._model
        label = self.MODEL_MAP.get(target, target)

        # 현재 선택된 모델 확인
        current = self.driver.execute_script("""
            const picker = document.querySelector('.model-picker-container');
            return picker ? picker.textContent.trim() : '';
        """)
        if label in current:
            return  # 이미 선택됨

        # 드롭다운 열기 — 여러 셀렉터 시도
        picker_sels = [".model-picker-container"]
        if self._ui:
            ui_sel = self._ui.get("model_picker")
            if ui_sel and ui_sel not in picker_sels:
                picker_sels.insert(0, ui_sel)

        self.driver.execute_script(f"""
            const sels = {json.dumps(picker_sels)};
            for (const sel of sels) {{
                // 드롭다운 아이콘 먼저 시도
                const icon = document.querySelector(
                    sel + ' mat-icon.dropdown-icon');
                if (icon) {{ icon.click(); return; }}
                const picker = document.querySelector(sel);
                if (picker) {{ picker.click(); return; }}
            }}
            // 폴백: model/picker 관련 클래스 탐색
            const fb = document.querySelector(
                '[class*="model-picker"], [class*="model-selector"]');
            if (fb) fb.click();
        """)
        time.sleep(1)

        # 옵션 클릭 (menuitemradio 포함 — Gemini 2025 UI)
        clicked = self.driver.execute_script(
            """
            const target = arguments[0];
            const items = document.querySelectorAll(
                '.mat-mdc-menu-panel button, '
                + '[role="menuitem"], [role="menuitemradio"], [role="option"], '
                + '.cdk-overlay-pane button');
            for (const item of items) {
                if (item.textContent.includes(target)) {
                    item.click();
                    return true;
                }
            }
            return false;
        """,
            label,
        )

        if clicked:
            self._log(f"[모델] {label} 선택")
        else:
            self._log(f"[모델] {label} 선택 실패 (수동 확인 필요)")
            # ESC로 메뉴 닫기
            self.driver.execute_script(
                "document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));"
            )
        time.sleep(0.5)

    def get_current_model(self) -> str:
        """현재 선택된 Gemini 모델명 반환 (UI에서 읽음)"""
        # 시도할 셀렉터 목록
        sels = [".model-picker-container"]
        if self._ui:
            ui_sel = self._ui.get("model_picker")
            if ui_sel and ui_sel not in sels:
                sels.insert(0, ui_sel)

        for sel in sels:
            try:
                current = self.driver.execute_script(f'''
                    const el = document.querySelector("{sel}");
                    return el ? el.textContent.trim() : '';
                ''')
                if current:
                    for key, label in self.MODEL_MAP.items():
                        if label in current:
                            return label
                    if current:
                        return current
            except Exception:
                continue

        # 폴백: 페이지 전체에서 모델명 텍스트 탐색
        try:
            result = self.driver.execute_script("""
                const models = ["2.0 Pro", "2.0 Flash", "사고 모드",
                                "Deep Research", "1.5 Pro", "1.5 Flash"];
                // 모델 관련 요소 탐색
                const sels = [
                    '[class*="model"]', '[class*="picker"]',
                    '[data-model]', '[aria-label*="model"]',
                    'button[class*="chip"]',
                ];
                for (const sel of sels) {
                    for (const el of document.querySelectorAll(sel)) {
                        const t = el.textContent.trim();
                        for (const m of models) {
                            if (t.includes(m)) return m;
                        }
                    }
                }
                return '';
            """)
            if result:
                for key, label in self.MODEL_MAP.items():
                    if label in result:
                        return label
                return result
        except Exception:
            pass

        return "알 수 없음"

    def _scroll_bottom(self):
        try:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)
        except Exception:
            pass

    def _count_responses(self) -> int:
        """현재 페이지의 모델 응답 개수"""
        for sel in _RESPONSE_SELECTORS:
            elems = self.driver.find_elements(By.CSS_SELECTOR, sel)
            if elems:
                return len(elems)
        return 0

    # ── 파일 업로드 (순수 Selenium) ───────────────────────

    def _click_upload_menu(self) -> bool:
        """업로드 메뉴 열기 → '파일 업로드' 옵션 클릭. 성공 시 True."""
        # Step A: 업로드 메뉴 버튼 클릭
        # A-0: UIDiscovery 발견 셀렉터 우선 시도
        ui_sel = self._ui.get("upload_menu_btn") if self._ui else None
        menu_clicked = False
        if ui_sel:
            try:
                menu_clicked = self.driver.execute_script(f'''
                    const btn = document.querySelector("{ui_sel}");
                    if (btn) {{ btn.click(); return true; }}
                    return false;
                ''')
            except Exception:
                pass
            if menu_clicked:
                time.sleep(0.8)
                # 발견된 업로드 옵션 셀렉터도 시도
                ui_opt = self._ui.get("upload_file_option") if self._ui else None
                if ui_opt:
                    try:
                        opt_ok = self.driver.execute_script(f'''
                            const els = document.querySelectorAll("{ui_opt}");
                            const targets = ["파일 업로드", "파일업로드",
                                "Upload file", "Upload a file"];
                            for (const el of els) {{
                                const txt = (el.textContent || "").trim();
                                for (const t of targets) {{
                                    if (txt.includes(t)) {{
                                        el.click(); return true;
                                    }}
                                }}
                            }}
                            return false;
                        ''')
                        if opt_ok:
                            time.sleep(1)
                            return True
                    except Exception:
                        pass
                # 발견 셀렉터로 옵션 못 찾으면 아래 폴백으로

        # A-1: 하드코딩 폴백 (다양한 셀렉터 시도)
        if not menu_clicked:
            menu_clicked = self.driver.execute_script("""
                const sels = [
                    "button[aria-label*='파일 업로드']",
                    "button[aria-label*='업로드']",
                    "button[aria-label*='Upload']",
                    "button[aria-label*='upload']",
                    "button[aria-label*='첨부']",
                    "button[aria-label*='Attach']",
                    "button[data-test-id*='upload']",
                ];
            for (const sel of sels) {
                const btn = document.querySelector(sel);
                if (btn) { btn.click(); return true; }
            }
            // 폴백: 아이콘 기반 — + 버튼이나 클립/파일 아이콘
            const btns = document.querySelectorAll(
                'button mat-icon, button svg');
            for (const icon of btns) {
                const name = (icon.getAttribute('data-mat-icon-name') || '')
                    + (icon.getAttribute('fontIcon') || '')
                    + (icon.textContent || '');
                if (/attach|upload|add_circle|clip/i.test(name)) {
                    icon.closest('button').click();
                    return true;
                }
            }
            return false;
        """)
        if not menu_clicked:
            return False
        time.sleep(0.8)

        # Step B: '파일 업로드' 옵션 클릭 (메뉴 팝업에서)
        opt_clicked = self.driver.execute_script("""
            // 메뉴 아이템/옵션/버튼 전부 탐색
            const targets = [
                "파일 업로드", "파일업로드", "Upload file",
                "Upload a file", "내 컴퓨터에서 업로드"
            ];
            const sels = [
                '[role="menuitem"]', '[role="option"]',
                '.mat-menu-item', '.mdc-list-item',
                '.cdk-overlay-pane button',
                '.cdk-overlay-pane [role="menuitem"]',
                'button', 'div[class*="menu"]',
            ];
            for (const sel of sels) {
                for (const el of document.querySelectorAll(sel)) {
                    const txt = (el.textContent || "").trim();
                    for (const t of targets) {
                        if (txt.includes(t)) {
                            el.click();
                            return true;
                        }
                    }
                }
            }
            return false;
        """)
        if not opt_clicked:
            return False
        time.sleep(1)
        return True

    def upload_file(self, file_path: str):
        """Gemini 웹에 파일 업로드 — OS 다이얼로그 없이 send_keys 직접 주입"""
        abs_path = os.path.abspath(file_path)

        # interceptor 재설치 (페이지 이동 후 초기화됐을 수 있음)
        self._install_upload_interceptor()

        # 최대 5회 재시도 — 메뉴 클릭 + 파일 주입
        menu_opened = False
        for attempt in range(5):
            if self._click_upload_menu():
                menu_opened = True
                break
            self._log(f"[!] 업로드 메뉴 열기 실패 → 재시도 ({attempt + 1}/5)")
            # ESC로 혹시 열린 오버레이 닫기
            self.driver.execute_script(
                "document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));"
            )
            time.sleep(2)
            # 3회 실패 후 페이지 리셋 시도
            if attempt == 2:
                self._log("[!] 페이지 리셋 후 재시도")
                self.new_chat()
                self._install_upload_interceptor()
                time.sleep(2)

        if not menu_opened:
            self._log("[FAIL] 업로드 메뉴를 열 수 없습니다")
            return False

        # 약관 동의 모달 자동 닫기 (첫 업로드 시 1회 표시)
        try:
            ok_btn = self.driver.execute_script("""
                const btns = document.querySelectorAll(
                    '.cdk-overlay-pane button, [mat-dialog-actions] button, '
                    + '[role="dialog"] button, [role="alertdialog"] button');
                for (const b of btns) {
                    const txt = (b.textContent || "").trim();
                    if (txt === "확인" || txt === "OK" || txt === "동의"
                        || txt === "Got it" || txt === "I understand") {
                        return b;
                    }
                }
                return null;
            """)
            if ok_btn:
                ok_btn.click()
                self._log("[업로드] 약관 동의 모달 자동 닫기")
                time.sleep(1)
                # 모달 닫힌 후 다시 업로드 메뉴 클릭
                self._click_upload_menu()
        except Exception:
            pass

        # input[type=file] 찾기 — 최대 3회 재시도
        target = None
        for fi_attempt in range(3):
            # 방법 1: DOM에서 직접 찾기
            inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            if inputs:
                target = inputs[-1]
                break

            # 방법 2: interceptor가 캡처한 요소
            target = self.driver.execute_script("return window._interceptedFileInput")
            if target:
                break

            # 방법 3: JS로 숨겨진 file input까지 탐색
            target = self.driver.execute_script("""
                const all = document.querySelectorAll('input');
                for (const inp of all) {
                    if (inp.type === 'file' || inp.accept) return inp;
                }
                return null;
            """)
            if target:
                break

            if fi_attempt < 2:
                self._log(f"[!] 파일 input 못 찾음 → 재시도 ({fi_attempt + 1}/3)")
                if fi_attempt == 0:
                    # 1차: interceptor 재설치 + 메뉴 다시 클릭
                    self._install_upload_interceptor()
                    time.sleep(1)
                    self._click_upload_menu()
                    time.sleep(2)
                else:
                    # 2차: 현재 세션 삭제 + 페이지 완전 리로드 후 재시도
                    self._log("[!] 세션 리셋 후 재시도")
                    self.reset_session()
                    self._install_upload_interceptor()
                    time.sleep(2)
                    self._click_upload_menu()
                    time.sleep(2)

        if not target:
            self._log("[FAIL] 파일 input 요소를 찾을 수 없습니다")
            return False

        # display 강제 + send_keys로 파일 주입
        self.driver.execute_script(
            "arguments[0].style.display='block';arguments[0].style.visibility='visible';", target
        )
        target.send_keys(abs_path)

        # 업로드 완료 대기 — JS 폴링 (Gemini UI 변경에 강건)
        base = os.path.splitext(os.path.basename(abs_path))[0]
        uploaded = False
        # JS로 파일명 포함 요소를 한번에 탐색 (셀렉터 다수 시도)
        js_check = f'''
            const base = "{base}";
            const sels = [
                "div[data-test-id='file-name']",
                "[class*='file']", "[class*='chip']",
                "[class*='attachment']", "[class*='upload-item']"
            ];
            for (const s of sels) {{
                for (const el of document.querySelectorAll(s)) {{
                    if (el.textContent.includes(base)) return true;
                }}
            }}
            return false;
        '''
        deadline = time.time() + 15  # 최대 15초 폴링
        while time.time() < deadline:
            try:
                if self.driver.execute_script(js_check):
                    uploaded = True
                    break
            except Exception:
                pass
            time.sleep(1)

        if not uploaded:
            # 확인 실패해도 send_keys는 완료됨 → 경고만 남기고 진행
            self._log(f"[!] 파일 업로드 확인 불가 (UI 변경 가능) — 계속 진행: {os.path.basename(abs_path)}")
        time.sleep(2)

    # ── 메시지 입력/전송 ─────────────────────────────────

    def send_message(self, text: str):
        """채팅 입력창에 텍스트 입력 (전부 JS — 백그라운드 호환)"""
        inject_js = """
            const box = document.querySelector("div[contenteditable='true']")
                     || document.querySelector("textarea");
            if (!box) return false;
            box.focus();
            if (box.tagName === 'TEXTAREA') {
                var setter = Object.getOwnPropertyDescriptor(
                    HTMLTextAreaElement.prototype, 'value').set;
                setter.call(box, arguments[0]);
            } else {
                box.innerText = arguments[0];
            }
            box.dispatchEvent(new Event('input', {bubbles: true}));
            box.dispatchEvent(new Event('change', {bubbles: true}));
            box.dispatchEvent(new KeyboardEvent('keydown', {
                key: ' ', code: 'Space', bubbles: true}));
            box.dispatchEvent(new KeyboardEvent('keyup', {
                key: ' ', code: 'Space', bubbles: true}));
            // 입력 확인
            var content = box.tagName === 'TEXTAREA' ? box.value : box.innerText;
            return content.length > 10;
        """
        for attempt in range(3):
            ok = self.driver.execute_script(inject_js, text)
            if ok:
                time.sleep(0.5)
                return True
            if attempt < 2:
                self._log(f"[!] 텍스트 입력 실패 → 재시도 ({attempt + 1}/3)")
                time.sleep(1)
                # 입력창 강제 리프레시
                self.driver.execute_script("""
                    var box = document.querySelector("div[contenteditable='true']")
                           || document.querySelector("textarea");
                    if (box) { box.innerHTML = ""; box.focus(); }
                """)
                time.sleep(0.5)
        self._log("[!] 텍스트 입력 3회 실패 — 세션 리셋 필요")
        return False

    def click_send(self):
        """전송 버튼 클릭 (전부 JS — 백그라운드 호환)"""
        self.driver.execute_script("""
            const sels = [
                "button[aria-label*='전송']",
                "button[aria-label*='Send']",
                "button[aria-label*='보내기']",
                "button.send-button",
                "button[mat-icon-button] mat-icon[data-mat-icon-name='send']"
            ];
            for (const sel of sels) {
                const btn = document.querySelector(sel);
                if (btn) { btn.click(); return; }
            }
            // 폴백: Enter 이벤트
            const box = document.querySelector("div[contenteditable='true']")
                     || document.querySelector("textarea");
            if (box) {
                box.dispatchEvent(new KeyboardEvent('keydown', {
                    key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true
                }));
            }
        """)
        time.sleep(2)

    # ── 응답 대기/추출 ───────────────────────────────────

    def wait_for_response(self, timeout: int = 180) -> bool:
        """AI 응답 완료까지 대기. True=완료, False=타임아웃.

        2단계:
          1) 중지 버튼 등장 대기 (생성 시작 확인) — 최대 120초
          2) 중지 버튼 소멸 대기 (생성 완료 확인) — timeout초
        사고모드(Deep Think) 사용 시 시작까지 오래 걸릴 수 있음.
        """
        self._scroll_bottom()
        before_count = self._count_responses()

        # ── Phase 1: 생성 시작 대기 (중지 버튼 or 새 응답 등장) ──
        deadline = time.time() + 120
        started = False
        while time.time() < deadline:
            # 중지 버튼이 나타났으면 → 생성 시작됨
            stops = self.driver.find_elements(By.CSS_SELECTOR, _STOP_SELECTOR)
            if stops:
                started = True
                break
            # 응답 개수가 늘었으면 → 이미 완료 (짧은 응답)
            if self._count_responses() > before_count:
                time.sleep(1)
                return True
            time.sleep(0.5)

        if not started:
            # 120초 내 시작 신호 없음 — 그래도 응답 있는지 확인
            time.sleep(3)
            return self._count_responses() > before_count

        # ── Phase 2: 생성 완료 대기 (중지 버튼 소멸) ──
        try:
            WebDriverWait(self.driver, timeout).until_not(
                EC.presence_of_element_located((By.CSS_SELECTOR, _STOP_SELECTOR))
            )
            time.sleep(2)
            self._scroll_bottom()
            return True
        except TimeoutException:
            return False

    def get_last_response(self) -> str:
        """마지막 AI 응답 텍스트 추출 (우선순위 셀렉터 탐색)"""
        return self.get_response_at(-1)

    def get_response_at(self, index: int) -> str:
        """특정 인덱스의 AI 응답 추출. -1이면 마지막."""
        best = ""

        for sel in _RESPONSE_SELECTORS:
            elems = self.driver.find_elements(By.CSS_SELECTOR, sel)
            if elems:
                try:
                    target = elems[index]
                except IndexError:
                    target = elems[-1]
                text = _extract_text(target.get_attribute("innerHTML"))
                if len(text) > len(best):
                    best = text

        if best:
            return best

        # 범용 폴백
        elems = self.driver.find_elements(By.CSS_SELECTOR, ".model-response, .markdown")
        if elems:
            try:
                target = elems[index]
            except IndexError:
                target = elems[-1]
            text = _extract_text(target.get_attribute("innerHTML"))
            if text:
                return text
            try:
                text = _extract_text(target.find_element(By.XPATH, "./..").get_attribute("innerHTML"))
                if text:
                    return text
            except Exception:
                pass

        return ""

    # ── 세션 제어 ────────────────────────────────────────

    def _dismiss_overlays(self):
        """열린 메뉴/모달/툴팁 닫기 — 삭제 전 정리용"""
        self.driver.execute_script("""
            // ESC 키 디스패치 → 메뉴/모달 닫기
            document.dispatchEvent(new KeyboardEvent('keydown',
                {key:'Escape', code:'Escape', bubbles:true}));
            // cdk-overlay-backdrop 클릭 (Angular Material 모달 닫기)
            const backdrop = document.querySelector('.cdk-overlay-backdrop');
            if (backdrop) backdrop.click();
        """)
        time.sleep(0.3)

    def is_alive(self) -> bool:
        """브라우저 연결 상태 확인"""
        try:
            _ = self.driver.current_url
            return True
        except Exception:
            return False

    def _delete_current_chat(self) -> bool:
        """현재 채팅 삭제 — chatID 기반, 최소화/다중창 환경 지원.

        핵심 전략:
          1. URL에서 chatID 추출 (다중 창에서도 정확히 특정)
          2. 사이드바에서 해당 링크 찾기 (순서 무관)
          3. JS hover 이벤트 + 강제 visible로 More options 표시
          4. 드롭다운 "삭제" → 확인 모달 "삭제" (offsetParent 미사용)
        """
        try:
            # ── Step 0: 사전 정리 + chatID 추출 ──
            self._dismiss_overlays()
            url = self.driver.current_url
            if "/app/" not in url or url.rstrip("/").endswith("/app"):
                return False
            chat_id = url.split("/app/")[-1].split("?")[0].split("#")[0]
            if not chat_id:
                return False

            # ── Step 1: 사이드바 열기 (닫혀있으면 토글) ──
            self.driver.execute_script("""
                const links = document.querySelectorAll('a[href*="/app/"]');
                if (links.length < 2) {
                    const toggle = document.querySelector(
                        'button[aria-label*="주 메뉴"],'
                        + 'button[aria-label*="Main menu"],'
                        + 'button[aria-label*="메뉴"],'
                        + 'button[aria-label*="Close"]'
                    );
                    if (toggle) toggle.click();
                }
            """)
            time.sleep(1)

            # ── Step 2: 사이드바에서 대화 링크 찾기 ──
            link = self.driver.execute_script(
                """
                const cid = arguments[0];
                // 정확한 href 매칭
                let el = document.querySelector('a[href*="/app/' + cid + '"]');
                if (el) return el;
                // 부분 매칭
                const all = document.querySelectorAll('a[href*="/app/"]');
                for (const a of all) {
                    if ((a.getAttribute("href") || "").includes(cid)) return a;
                }
                return null;
            """,
                chat_id,
            )
            if not link:
                self._log("[삭제] 사이드바에서 대화 링크 못 찾음")
                return False

            # ── Step 3: 호버 이벤트 디스패치 (More options 표시 트리거) ──
            #   CSS :hover는 최소화 시 작동 안 함 → JS 이벤트로 Angular 반응 유도
            self.driver.execute_script(
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
            time.sleep(0.8)

            # ── Step 4: More options 버튼 찾기 + 강제 visible + 클릭 ──
            clicked_more = self.driver.execute_script(
                """
                const link = arguments[0];
                const cid = arguments[1];
                const FORCE_SHOW = 'opacity:1!important;visibility:visible!important;'
                    + 'display:inline-flex!important;pointer-events:auto!important;'
                    + 'position:relative!important;';

                // A. 링크 부모 탐색 → aria-label 패턴 매칭
                const ariaRe = /more|option|옵션|더보기/i;
                let el = link;
                for (let i = 0; i < 7; i++) {
                    el = el.parentElement;
                    if (!el) break;
                    const btns = el.querySelectorAll('button');
                    for (const btn of btns) {
                        const label = btn.getAttribute('aria-label') || '';
                        if (ariaRe.test(label)) {
                            btn.style.cssText += FORCE_SHOW;
                            btn.click();
                            return true;
                        }
                    }
                }

                // B. 폴백: chatID를 공유하는 컨테이너의 아이콘 전용 버튼
                el = link;
                for (let i = 0; i < 7; i++) {
                    el = el.parentElement;
                    if (!el) break;
                    const btns = el.querySelectorAll('button');
                    for (const btn of btns) {
                        // 아이콘만 있고 텍스트 거의 없는 버튼 (More options 패턴)
                        const hasIcon = btn.querySelector('mat-icon, svg, .icon');
                        const txt = btn.textContent.trim();
                        if (hasIcon && txt.length < 5) {
                            btn.style.cssText += FORCE_SHOW;
                            btn.click();
                            return true;
                        }
                    }
                }

                // C. 최후: 전체 More options 중 chatID 컨테이너에 속한 것
                const allMore = document.querySelectorAll(
                    'button[aria-label*="More"], button[aria-label*="옵션"]');
                for (const btn of allMore) {
                    let p = btn;
                    for (let j = 0; j < 10; j++) {
                        p = p.parentElement;
                        if (!p) break;
                        if (p.querySelector('a[href*="' + cid + '"]')) {
                            btn.style.cssText += FORCE_SHOW;
                            btn.click();
                            return true;
                        }
                    }
                }
                return false;
            """,
                link,
                chat_id,
            )

            if not clicked_more:
                self._log("[삭제] More options 버튼 못 찾음")
                return False
            time.sleep(0.8)

            # ── Step 5: "삭제" 메뉴 아이템 클릭 ──
            for attempt in range(2):
                clicked_del = self.driver.execute_script("""
                    const sels = '[role="menuitem"],[role="option"],'
                        + '.mat-menu-item,.mdc-list-item';
                    const items = document.querySelectorAll(sels);
                    for (const item of items) {
                        const t = item.textContent.trim();
                        if (t.includes('삭제') || t === 'Delete') {
                            item.click();
                            return true;
                        }
                    }
                    return false;
                """)
                if clicked_del:
                    break
                time.sleep(0.8)  # 메뉴 렌더링 대기 후 재시도

            if not clicked_del:
                self._log("[삭제] '삭제' 메뉴 못 찾음")
                return False
            time.sleep(1)

            # ── Step 6: 확인 모달 "삭제" 클릭 ──
            #   offsetParent 미사용 (최소화 시 null)
            #   대신 dialog 컨테이너 스코핑 + DOM 역순 폴백
            for attempt in range(3):
                confirmed = self.driver.execute_script("""
                    // A. 다이얼로그 컨테이너 내부에서 찾기
                    const dlgSels = [
                        'mat-dialog-container', '[role="dialog"]',
                        '[role="alertdialog"]', '.cdk-overlay-pane'
                    ];
                    for (const sel of dlgSels) {
                        for (const dlg of document.querySelectorAll(sel)) {
                            for (const btn of dlg.querySelectorAll('button')) {
                                const t = btn.textContent.trim();
                                if (t === '삭제' || t === 'Delete') {
                                    btn.click();
                                    return true;
                                }
                            }
                        }
                    }
                    // B. DOM 역순 폴백 (모달 = DOM 끝에 추가됨)
                    const all = Array.from(document.querySelectorAll('button'));
                    for (let i = all.length - 1; i >= 0; i--) {
                        const t = all[i].textContent.trim();
                        if (t === '삭제' || t === 'Delete') {
                            all[i].click();
                            return true;
                        }
                    }
                    return false;
                """)
                if confirmed:
                    break
                time.sleep(0.5)  # 모달 렌더링 대기

            if confirmed:
                time.sleep(1)
                self._log("[삭제] 성공")
                return True
            else:
                self._log("[삭제] 확인 모달 버튼 못 찾음")
                return False

        except Exception as e:
            self._log(f"[삭제] 예외: {e}")
            return False

    def new_chat(self):
        """새 채팅 세션 시작 + 모델 재선택.
        driver.get()으로 전체 페이지 리로드 — SPA 내비게이션으로는
        입력창 상태가 리셋되지 않는 문제 방지."""
        try:
            self.driver.get("https://gemini.google.com/app")
        except Exception:
            self.driver.refresh()
        time.sleep(5)
        self._install_upload_interceptor()
        self.select_model()

    def reset_session(self):
        """현재 채팅 삭제 → 새 채팅 세션 시작"""
        was_hidden = self._hidden
        try:
            # 삭제 시 창이 보여야 ⋮ 버튼이 렌더링됨
            if was_hidden:
                self.show_window()
                time.sleep(1)
            self._delete_current_chat()
            time.sleep(3)
        except Exception:
            pass
        self.new_chat()
        if was_hidden:
            self.hide_window()

    # ── 통합 메서드 ──────────────────────────────────────

    def send_with_file(self, file_path: str, prompt: str) -> str:
        """파일 업로드 + 프롬프트 전송 → 응답 텍스트 반환"""
        result = self.upload_file(file_path)
        if result is False:
            return "[EMPTY] 파일 업로드 실패 — 세션 리셋 필요"
        if not self.send_message(prompt):
            return "[EMPTY] 텍스트 입력 실패 — 세션 리셋 필요"
        before = self._count_responses()
        self.click_send()
        if not self.wait_for_response():
            return "[TIMEOUT] 응답 시간 초과"
        # before 인덱스 = 새로 생긴 응답 (0-based)
        resp = self.get_response_at(before)
        if not resp:
            resp = self.get_last_response()  # 폴백
        if not resp:
            return "[EMPTY] 응답을 추출할 수 없습니다"
        return resp

    def send_prompt(self, prompt: str) -> str:
        """프롬프트만 전송 (파일 없이) → 응답 텍스트 반환"""
        if not self.send_message(prompt):
            return "[EMPTY] 텍스트 입력 실패 — 세션 리셋 필요"
        before = self._count_responses()
        self.click_send()
        if not self.wait_for_response():
            return "[TIMEOUT] 응답 시간 초과"
        resp = self.get_response_at(before)
        if not resp:
            resp = self.get_last_response()
        if not resp:
            return "[EMPTY] 응답을 추출할 수 없습니다"
        return resp
