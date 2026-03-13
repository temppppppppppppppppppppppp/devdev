"""
[V1] UI Discovery — Gemini 웹 UI 셀렉터 자동 탐지
=================================================
Selenium DOM 덤프 → Gemini API 분석 → 셀렉터 캐싱.
Google이 Gemini UI를 변경해도 자동 적응.

사용법:
    ui = UIDiscovery(driver, api_key="...", cache_dir=Path("./"))
    ui.calibrate()                       # 시작 시 1회
    sel = ui.get("upload_menu_btn")      # 캐싱된 셀렉터 반환
    ui.invalidate("upload_menu_btn")     # 실패 시 무효화 → 재탐지

비용: 캘리브레이션 1회당 Flash API 호출 1회 ≈ $0.001 이하
"""

# Manual-only helper. This module is not part of the production API/Desktop runtime path.

import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

# ── 탐지 대상 UI 요소 ──────────────────────────────────

UI_ELEMENTS = {
    "upload_menu_btn": {
        "desc": "채팅 입력창 왼쪽에 있는 '+' 또는 첨부(클립) 아이콘 버튼. 클릭하면 '파일 업로드', '사진 찍기' 등의 옵션이 있는 드롭다운 메뉴가 열림. 메뉴 안의 '파일 업로드' 항목이 아니라, 메뉴를 여는 버튼 자체.",
        "fallback_selectors": [
            "button[aria-label*='첨부']",
            "button[aria-label*='Attach']",
            "button[aria-label*='Add']",
            "button[aria-label*='추가']",
            "button[aria-label*='Upload']",
            "button[aria-label*='파일 업로드']",
        ],
    },
    "upload_file_option": {
        "desc": "드롭다운 메뉴에서 '파일 업로드' 또는 'Upload file' 텍스트가 있는 메뉴 항목",
        "fallback_texts": ["파일 업로드", "파일업로드", "Upload file", "Upload a file", "내 컴퓨터에서 업로드"],
        "fallback_container": [
            '[role="menuitem"]',
            '[role="option"]',
            ".mat-menu-item",
            ".mdc-list-item",
            ".cdk-overlay-pane button",
            'div[class*="menu"]',
        ],
    },
    "send_btn": {
        "desc": "채팅 메시지를 전송하는 버튼 (전송/Send 아이콘)",
        "fallback_selectors": [
            "button[aria-label*='전송']",
            "button[aria-label*='Send']",
            "button[aria-label*='보내기']",
            "button.send-button",
        ],
    },
    "input_box": {
        "desc": "사용자가 프롬프트/메시지를 입력하는 텍스트 입력 영역 (contenteditable div 또는 textarea)",
        "fallback_selectors": [
            "div[contenteditable='true']",
            "textarea",
        ],
    },
    "model_picker": {
        "desc": "AI 모델(Pro, Flash, Think 등)을 선택하는 드롭다운 피커 영역",
        "fallback_selectors": [
            ".model-picker-container",
            "[class*='model-picker']",
            "[class*='model-selector']",
        ],
    },
    "stop_btn": {
        "desc": "AI 응답 생성 중에 나타나는 중지/Stop 버튼",
        "fallback_selectors": [
            "button[aria-label*='중지']",
            "button[aria-label*='Stop']",
            "button[aria-label*='stop']",
        ],
    },
    "more_options_btn": {
        "desc": "사이드바 채팅 항목의 더보기(⋮) 버튼 — 호버 시 나타남. 점 3개 아이콘.",
        "fallback_selectors": [
            "button[aria-label*='More']",
            "button[aria-label*='더보기']",
            "button[aria-label*='옵션']",
            "button[aria-label*='option']",
        ],
    },
    "delete_option": {
        "desc": "채팅 삭제 메뉴 항목 (⋮ 클릭 후 나타나는 '삭제' 또는 'Delete')",
        "fallback_texts": ["삭제", "Delete"],
        "fallback_container": [
            '[role="menuitem"]',
            '[role="option"]',
            ".mat-menu-item",
            ".mdc-list-item",
        ],
    },
    "response_container": {
        "desc": "AI 모델 응답이 표시되는 컨테이너 영역 (model-response, .markdown 등)",
        "fallback_selectors": [
            "model-response .markdown",
            "model-response message-content",
            "model-response",
            ".response-container .markdown",
            "message-content",
        ],
    },
}


# ── DOM 덤프 JS ─────────────────────────────────────

_DOM_DUMP_JS = """
(function() {
    const result = [];
    const sels = 'button, input, textarea, [role="button"], [role="menuitem"], '
        + '[role="option"], [contenteditable], [role="tab"], select, '
        + 'mat-icon, [class*="picker"], [class*="upload"], [class*="send"], '
        + '[class*="model"], [class*="menu"], [aria-label], [class*="sidebar"], '
        + '[class*="response"], [class*="message"], model-response, message-content';

    const seen = new Set();
    document.querySelectorAll(sels).forEach((el) => {
        if (result.length >= 250 || seen.has(el)) return;
        seen.add(el);

        const rect = el.getBoundingClientRect();
        const info = { tag: el.tagName.toLowerCase() };

        if (el.id) info.id = el.id;
        if (el.className && typeof el.className === 'string') {
            const cls = el.className.split(/\\s+/).filter(c => c).slice(0, 6);
            if (cls.length) info.cls = cls.join(' ');
        }
        if (el.type) info.type = el.type;

        const role = el.getAttribute('role');
        if (role) info.role = role;

        const aria = el.getAttribute('aria-label');
        if (aria) info.aria = aria;

        const ce = el.getAttribute('contenteditable');
        if (ce) info.ce = ce;

        const txt = (el.textContent || '').trim();
        if (txt && txt.length < 60) info.txt = txt;
        else if (txt) info.txt = txt.slice(0, 60) + '…';

        for (const attr of el.attributes) {
            if (attr.name.startsWith('data-') && attr.value) {
                if (!info.data) info.data = {};
                info.data[attr.name] = attr.value.slice(0, 40);
            }
        }

        const matIcon = el.querySelector && el.querySelector('mat-icon');
        if (matIcon) {
            const iname = matIcon.getAttribute('data-mat-icon-name')
                || matIcon.getAttribute('fontIcon')
                || matIcon.textContent.trim();
            if (iname) info.icon = iname;
        }

        info.vis = rect.width > 0 && rect.height > 0;

        let p = el.parentElement;
        const pList = [];
        for (let j = 0; j < 3 && p; j++) {
            const pi = { tag: p.tagName.toLowerCase() };
            if (p.className && typeof p.className === 'string') {
                const fc = p.className.split(/\\s+/)[0];
                if (fc) pi.cls = fc;
            }
            const pr = p.getAttribute('role');
            if (pr) pi.role = pr;
            pList.push(pi);
            p = p.parentElement;
        }
        if (pList.length) info.p = pList;

        result.push(info);
    });

    return JSON.stringify(result);
})()
"""


# ── Gemini API 호출 ─────────────────────────────────


def _call_gemini_api(api_key: str, prompt: str, model: str = "gemini-2.0-flash") -> str:
    """Gemini API 호출 (표준 라이브러리만 사용, 추가 의존성 없음)"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 4096,
        },
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        raise RuntimeError(f"Gemini API 호출 실패: {e}")


# ── 메인 클래스 ─────────────────────────────────────


class UIDiscovery:
    """Gemini 웹 UI 셀렉터 자동 탐지 시스템"""

    CACHE_FILE = "_ui_cache.json"
    CACHE_MAX_AGE_HOURS = 72  # 3일마다 재검증

    def __init__(self, driver, api_key: str, cache_dir: Path, log_func=None):
        self.driver = driver
        self.api_key = api_key
        self.cache_dir = cache_dir
        self.cache_path = cache_dir / self.CACHE_FILE
        self._log = log_func or print
        self._cache = self._load_cache()

    # ── 캐시 관리 ─────────────────────────────────

    def _load_cache(self) -> dict:
        if self.cache_path.exists():
            try:
                data = json.loads(self.cache_path.read_text(encoding="utf-8"))
                if "selectors" in data:
                    return data
            except Exception:
                pass
        return {"selectors": {}, "updated": "", "page_hash": ""}

    def _save_cache(self):
        self._cache["updated"] = datetime.now().isoformat()
        self.cache_path.write_text(json.dumps(self._cache, ensure_ascii=False, indent=2), encoding="utf-8")

    def _is_cache_fresh(self) -> bool:
        ts = self._cache.get("updated", "")
        if not ts:
            return False
        try:
            dt = datetime.fromisoformat(ts)
            return (datetime.now() - dt) < timedelta(hours=self.CACHE_MAX_AGE_HOURS)
        except Exception:
            return False

    # ── 캘리브레이션 ─────────────────────────────

    def calibrate(self, force: bool = False):
        """UI 셀렉터 캘리브레이션 — 캐시 유효하면 스킵"""
        if not force and self._is_cache_fresh():
            # 핵심 셀렉터가 현재 페이지에서 유효한지 확인
            if self._validate_critical():
                self._log("[UI탐지] 캐시 유효 ✓")
                return True
            self._log("[UI탐지] 캐시 셀렉터 무효 → 재탐지")
        else:
            reason = "강제" if force else "캐시 없음/만료"
            self._log(f"[UI탐지] 캘리브레이션 시작 ({reason})")

        ok = self._discover()
        if ok:
            self._log("[UI탐지] 캘리브레이션 완료 ✓")
        else:
            self._log("[UI탐지] 캘리브레이션 실패 — 폴백 모드")
        return ok

    def _validate_critical(self) -> bool:
        """핵심 셀렉터들이 현재 페이지에서 유효한지 확인"""
        critical = ["upload_menu_btn", "input_box"]
        for name in critical:
            sel = self._cache.get("selectors", {}).get(name)
            if not sel:
                return False
            try:
                found = self.driver.execute_script(f'return document.querySelector("{sel}") !== null;')
                if not found:
                    return False
            except Exception:
                return False
        return True

    # ── 탐지 로직 ────────────────────────────────

    def _discover(self) -> bool:
        """DOM 덤프 → Gemini API → 셀렉터 추출 → 검증 → 캐싱"""

        # Step 1: DOM 덤프
        try:
            dom_json = self.driver.execute_script(_DOM_DUMP_JS)
        except Exception as e:
            self._log(f"[UI탐지] DOM 덤프 실패: {e}")
            return self._fallback_discover()

        # Step 2: Gemini API 분석
        elements_desc = "\n".join(
            f"  {i + 1}. {name}: {info['desc']}" for i, (name, info) in enumerate(UI_ELEMENTS.items())
        )

        prompt = f"""다음은 Google Gemini 웹 채팅 페이지(gemini.google.com/app)에서 추출한 인터랙티브 DOM 요소 목록입니다.
각 요소의 tag, cls(class), role, aria(aria-label), txt(textContent), icon, ce(contenteditable) 등이 포함됩니다.
vis=true이면 현재 화면에 보이는 요소입니다. p는 부모 요소 정보입니다.

[DOM 요소 목록]
{dom_json}

위 DOM에서 다음 UI 요소에 해당하는 CSS 셀렉터를 찾아주세요:
{elements_desc}

★★★ 중요 주의사항 ★★★
- upload_menu_btn: 채팅 입력창 왼쪽의 '+' 또는 첨부 아이콘 버튼 (드롭다운 메뉴를 여는 버튼)
- upload_file_option: 그 드롭다운 메뉴 안의 '파일 업로드' 텍스트가 있는 항목
- 이 둘은 반드시 다른 요소여야 합니다! upload_menu_btn은 항상 화면에 보이는 버튼이고, upload_file_option은 메뉴가 열려야 보이는 항목입니다.
- upload_menu_btn의 aria-label에는 보통 '파일 업로드'가 아닌 '첨부', 'Attach', 'Add', '추가' 등이 포함됩니다.

규칙:
1. document.querySelector()에서 사용 가능한 유효한 CSS 셀렉터
2. 가능한 구체적이고 안정적인 셀렉터 (id → aria-label → role+class 순서)
3. aria-label 기반은 부분 매칭(*=) 사용
4. 요소를 찾을 수 없으면 null
5. 한국어 UI와 영어 UI 모두 고려

반드시 아래 JSON 형식으로만 응답 (다른 텍스트 금지):
{{
  "upload_menu_btn": "selector or null",
  "upload_file_option": "selector or null",
  "send_btn": "selector or null",
  "input_box": "selector or null",
  "model_picker": "selector or null",
  "stop_btn": "selector or null",
  "more_options_btn": "selector or null",
  "delete_option": "selector or null",
  "response_container": "selector or null"
}}"""

        try:
            result = _call_gemini_api(self.api_key, prompt)
            selectors = self._parse_json(result)
        except Exception as e:
            self._log(f"[UI탐지] API 분석 실패: {e}")
            return self._fallback_discover()

        if not selectors:
            self._log("[UI탐지] API 응답 파싱 실패")
            return self._fallback_discover()

        # Step 3: 셀렉터 검증 + 폴백 보완
        valid = {}
        for name in UI_ELEMENTS:
            sel = selectors.get(name)
            if sel and sel != "null" and sel != "None":
                if self._test_selector(sel):
                    valid[name] = sel
                    continue

            # API 결과 실패 → 폴백 셀렉터 시도
            fb_sel = self._try_fallback(name)
            if fb_sel:
                valid[name] = fb_sel

        # Step 4: upload_menu_btn 실제 클릭 검증
        if "upload_menu_btn" in valid:
            if not self._verify_upload_btn(valid["upload_menu_btn"]):
                self._log("[UI탐지] upload_menu_btn 클릭 검증 실패 → 재탐색")
                # 입력창 주변 버튼 순회하며 진짜 메뉴 버튼 찾기
                real_sel = self._find_real_upload_btn()
                if real_sel:
                    valid["upload_menu_btn"] = real_sel
                    self._log(f"[UI탐지] 진짜 업로드 버튼 발견: {real_sel}")
                else:
                    del valid["upload_menu_btn"]
                    self._log("[UI탐지] 업로드 버튼 탐색 실패")

        self._cache["selectors"] = valid
        self._save_cache()

        self._log(f"[UI탐지] {len(valid)}/{len(UI_ELEMENTS)} 요소 발견")
        return len(valid) >= 3  # 최소 3개는 찾아야 성공

    def _parse_json(self, text: str) -> dict | None:
        """API 응답에서 JSON 추출"""
        text = text.strip()
        # 마크다운 코드 블록 제거
        if "```" in text:
            parts = text.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                if part.startswith("{"):
                    text = part
                    break
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # { } 블록만 추출 시도
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    return None
        return None

    def _test_selector(self, selector: str) -> bool:
        """셀렉터가 현재 페이지에서 요소를 찾는지 확인"""
        try:
            # 셀렉터에 특수문자가 있으면 JS 에러 방지
            safe_sel = selector.replace("\\", "\\\\").replace('"', '\\"')
            return self.driver.execute_script(
                f'try {{ return document.querySelector("{safe_sel}") !== null; }} catch(e) {{ return false; }}'
            )
        except Exception:
            return False

    def _try_fallback(self, name: str) -> str | None:
        """UI_ELEMENTS에 정의된 폴백 셀렉터 시도"""
        info = UI_ELEMENTS.get(name, {})

        # 타입 1: 직접 셀렉터 목록
        for sel in info.get("fallback_selectors", []):
            if self._test_selector(sel):
                return sel

        # 타입 2: 텍스트 매칭 (메뉴 항목 등)
        texts = info.get("fallback_texts", [])
        containers = info.get("fallback_container", [])
        if texts and containers:
            for container_sel in containers:
                for text in texts:
                    # JS로 텍스트 매칭 확인
                    try:
                        found = self.driver.execute_script(f"""
                            const els = document.querySelectorAll(
                                '{container_sel}');
                            for (const el of els) {{
                                if (el.textContent.includes(
                                    '{text}')) return true;
                            }}
                            return false;
                        """)
                        if found:
                            return container_sel
                    except Exception:
                        continue

        return None

    def _fallback_discover(self) -> bool:
        """API 없이 로컬 폴백 셀렉터만으로 탐지"""
        self._log("[UI탐지] 폴백 모드 — 로컬 셀렉터 탐색")
        valid = {}
        for name in UI_ELEMENTS:
            sel = self._try_fallback(name)
            if sel:
                valid[name] = sel

        if valid:
            self._cache["selectors"] = valid
            self._save_cache()
            self._log(f"[UI탐지] 폴백: {len(valid)}/{len(UI_ELEMENTS)}")

        return len(valid) >= 2

    # ── 업로드 버튼 클릭 검증 ────────────────────

    def _verify_upload_btn(self, selector: str) -> bool:
        """업로드 버튼을 실제 클릭 → 드롭다운 메뉴가 열리는지 확인"""
        try:
            # 오버레이 수 기록
            before = self.driver.execute_script(
                'return document.querySelectorAll(".cdk-overlay-pane, [role=menu], [role=listbox]").length;'
            )

            # 클릭
            safe_sel = selector.replace("\\", "\\\\").replace('"', '\\"')
            clicked = self.driver.execute_script(f'''
                const btn = document.querySelector("{safe_sel}");
                if (!btn) return false;
                btn.click();
                return true;
            ''')
            if not clicked:
                return False

            time.sleep(1)

            # 오버레이가 새로 생겼는지 확인
            after = self.driver.execute_script(
                'return document.querySelectorAll(".cdk-overlay-pane, [role=menu], [role=listbox]").length;'
            )

            # 메뉴에 '파일 업로드' 텍스트가 있는지 확인
            has_upload = self.driver.execute_script("""
                const texts = ["파일 업로드", "Upload file", "Upload a file"];
                const items = document.querySelectorAll(
                    '[role="menuitem"], [role="option"], '
                    + '.mat-menu-item, .mdc-list-item');
                for (const item of items) {
                    const t = (item.textContent || "").trim();
                    for (const target of texts) {
                        if (t.includes(target)) return true;
                    }
                }
                return false;
            """)

            # ESC로 메뉴 닫기
            self.driver.execute_script(
                "document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));"
            )
            time.sleep(0.5)

            if has_upload:
                self._log("[UI탐지] upload_menu_btn 클릭 검증 성공 ✓")
                return True

            # 오버레이 수 변화만이라도 있으면 부분 성공
            if after > before:
                self._log("[UI탐지] upload_menu_btn 메뉴 열림 (텍스트 불일치)")
                return True

            return False

        except Exception as e:
            self._log(f"[UI탐지] 검증 예외: {e}")
            return False

    def _find_real_upload_btn(self) -> str | None:
        """입력창 주변 버튼을 순회하며 진짜 업로드 메뉴 버튼 탐색"""
        try:
            # 입력 영역 근처의 모든 버튼 수집
            buttons = self.driver.execute_script("""
                const results = [];
                // contenteditable 입력창 찾기
                const input = document.querySelector(
                    "div[contenteditable='true']");
                if (!input) return results;

                // 입력창의 조상 컨테이너에서 버튼 탐색
                let container = input;
                for (let i = 0; i < 5; i++) {
                    container = container.parentElement;
                    if (!container) break;
                }
                if (!container) return results;

                const btns = container.querySelectorAll('button');
                btns.forEach((btn, idx) => {
                    const rect = btn.getBoundingClientRect();
                    if (rect.width === 0) return;
                    results.push({
                        idx: idx,
                        aria: btn.getAttribute('aria-label') || '',
                        cls: btn.className || '',
                        text: (btn.textContent || '').trim().slice(0, 30),
                    });
                });
                return results;
            """)

            if not buttons:
                return None

            self._log(f"[UI탐지] 입력창 주변 버튼 {len(buttons)}개 발견")

            # 각 버튼을 순서대로 클릭해보며 메뉴가 열리는지 테스트
            for btn_info in buttons:
                idx = btn_info["idx"]
                aria = btn_info.get("aria", "")

                # 전송 버튼은 건너뛰기
                if any(x in aria for x in ["전송", "Send", "보내기", "마이크", "음성"]):
                    continue

                try:
                    # 클릭
                    self.driver.execute_script(f"""
                        const input = document.querySelector(
                            "div[contenteditable='true']");
                        let container = input;
                        for (let i = 0; i < 5; i++) {{
                            container = container.parentElement;
                            if (!container) break;
                        }}
                        const btns = container.querySelectorAll('button');
                        if (btns[{idx}]) btns[{idx}].click();
                    """)
                    time.sleep(1)

                    # 메뉴 열렸나?
                    has_upload = self.driver.execute_script("""
                        const texts = ["파일 업로드", "Upload file"];
                        const items = document.querySelectorAll(
                            '[role="menuitem"], [role="option"], '
                            + '.mat-menu-item, .mdc-list-item, '
                            + '.cdk-overlay-pane button');
                        for (const item of items) {
                            const t = (item.textContent || "").trim();
                            for (const target of texts) {
                                if (t.includes(target)) return true;
                            }
                        }
                        return false;
                    """)

                    # ESC로 닫기
                    self.driver.execute_script(
                        "document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));"
                    )
                    time.sleep(0.5)

                    if has_upload:
                        # 이 버튼의 고유 셀렉터 생성
                        sel = self.driver.execute_script(f"""
                            const input = document.querySelector(
                                "div[contenteditable='true']");
                            let container = input;
                            for (let i = 0; i < 5; i++) {{
                                container = container.parentElement;
                                if (!container) break;
                            }}
                            const btn = container.querySelectorAll(
                                'button')[{idx}];
                            if (!btn) return null;
                            // aria-label 기반 셀렉터 생성
                            const a = btn.getAttribute('aria-label');
                            if (a) return "button[aria-label='" + a + "']";
                            // id 기반
                            if (btn.id) return "#" + btn.id;
                            // data-* 기반
                            for (const attr of btn.attributes) {{
                                if (attr.name.startsWith('data-')
                                    && attr.value) {{
                                    return "button[" + attr.name
                                        + "='" + attr.value + "']";
                                }}
                            }}
                            // 폴백: nth-child
                            return null;
                        """)
                        return sel

                except Exception:
                    continue

            return None

        except Exception as e:
            self._log(f"[UI탐지] 버튼 탐색 예외: {e}")
            return None

    # ── 외부 인터페이스 ──────────────────────────

    def get(self, element_name: str) -> str | None:
        """캐싱된 셀렉터 반환. 없으면 None."""
        return self._cache.get("selectors", {}).get(element_name)

    def get_all(self) -> dict:
        """모든 캐싱된 셀렉터 반환"""
        return dict(self._cache.get("selectors", {}))

    def invalidate(self, element_name: str):
        """특정 셀렉터 무효화 — 다음 calibrate에서 재탐지"""
        sels = self._cache.get("selectors", {})
        if element_name in sels:
            del sels[element_name]
            self._save_cache()
            self._log(f"[UI탐지] {element_name} 무효화")

    def invalidate_all(self):
        """모든 셀렉터 무효화"""
        self._cache["selectors"] = {}
        self._cache["updated"] = ""
        self._save_cache()
        self._log("[UI탐지] 전체 무효화")

    def recalibrate(self):
        """강제 재캘리브레이션"""
        return self.calibrate(force=True)
