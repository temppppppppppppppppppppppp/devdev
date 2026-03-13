"""
UI Discovery 테스트 — API 연결 + 파싱 검증
"""

# Manual-only probe. This file is intentionally outside the pytest collection path.

import json
import sys
from pathlib import Path

# bridge 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from bridge.ui_discovery import UI_ELEMENTS, UIDiscovery, _call_gemini_api


def test_env_loading():
    """1. .env 파일에서 API 키 로드 테스트"""
    print("=" * 50)
    print("TEST 1: .env 로딩")

    from bridge.gemini_driver import GeminiDriver

    key = GeminiDriver._load_api_key(Path(__file__).parent)

    if key:
        masked = key[:10] + "..." + key[-4:]
        print(f"  ✓ API 키 발견: {masked}")
        return key
    else:
        print("  ✗ API 키 없음!")
        return None


def test_api_call(api_key: str):
    """2. Gemini API 호출 테스트"""
    print("\n" + "=" * 50)
    print("TEST 2: Gemini API 호출")

    try:
        resp = _call_gemini_api(api_key, '다음 JSON만 반환하세요: {"status": "ok", "message": "연결 성공"}')
        print(f"  ✓ API 응답: {resp[:200]}")
        return True
    except Exception as e:
        print(f"  ✗ API 호출 실패: {e}")
        return False


def test_json_parsing():
    """3. JSON 파싱 로직 테스트"""
    print("\n" + "=" * 50)
    print("TEST 3: JSON 파싱")

    # UIDiscovery의 _parse_json을 직접 테스트
    # 임시 인스턴스 (driver 없이)

    test_cases = [
        # 깨끗한 JSON
        ('{"upload_menu_btn": "button[aria-label*=\\"Upload\\"]"}', True, "깨끗한 JSON"),
        # 마크다운 코드블록
        ('```json\n{"upload_menu_btn": "button.upload"}\n```', True, "마크다운 코드블록"),
        # 앞뒤 텍스트 포함
        ('Here is the result:\n{"send_btn": "button.send"}\nDone!', True, "앞뒤 텍스트"),
        # 잘못된 JSON
        ("not json at all", False, "잘못된 JSON"),
    ]

    # _parse_json은 인스턴스 메서드이므로, 클래스에서 직접 호출
    class FakeDriver:
        def execute_script(self, *a):
            return None

    ui = UIDiscovery.__new__(UIDiscovery)
    ui.driver = FakeDriver()
    ui._log = print
    ui._cache = {"selectors": {}, "updated": ""}

    all_pass = True
    for text, should_pass, desc in test_cases:
        result = ui._parse_json(text)
        ok = (result is not None) == should_pass
        status = "✓" if ok else "✗"
        print(f"  {status} {desc}: {result}")
        if not ok:
            all_pass = False

    return all_pass


def test_api_discovery(api_key: str):
    """4. 실제 DOM 샘플로 API 셀렉터 분석 테스트"""
    print("\n" + "=" * 50)
    print("TEST 4: API 셀렉터 분석 (샘플 DOM)")

    # Gemini 페이지의 실제 DOM을 시뮬레이션
    sample_dom = json.dumps(
        [
            {
                "tag": "button",
                "aria": "파일 업로드 메뉴 열기",
                "cls": "upload-menu-btn",
                "vis": True,
                "icon": "add_circle",
            },
            {"tag": "button", "aria": "메시지 전송", "cls": "send-button", "vis": True, "icon": "send"},
            {"tag": "div", "ce": "true", "cls": "ql-editor", "vis": True, "txt": ""},
            {"tag": "div", "cls": "model-picker-container", "vis": True, "txt": "2.0 Flash"},
            {"tag": "button", "aria": "중지", "cls": "stop-btn", "vis": False},
            {"tag": "button", "aria": "More options", "cls": "more-options", "vis": True, "icon": "more_vert"},
            {"tag": "div", "role": "menuitem", "txt": "삭제", "vis": False},
            {"tag": "model-response", "cls": "response-container", "vis": True},
        ]
    )

    elements_desc = "\n".join(
        f"  {i + 1}. {name}: {info['desc']}" for i, (name, info) in enumerate(UI_ELEMENTS.items())
    )

    prompt = f"""다음은 Google Gemini 웹 채팅 페이지에서 추출한 DOM 요소 목록입니다.

[DOM 요소 목록]
{sample_dom}

위 DOM에서 다음 UI 요소에 해당하는 CSS 셀렉터를 찾아주세요:
{elements_desc}

규칙:
1. document.querySelector()에서 사용 가능한 유효한 CSS 셀렉터
2. aria-label 기반은 부분 매칭(*=) 사용
3. 요소를 찾을 수 없으면 null

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
        result = _call_gemini_api(api_key, prompt)
        print(f"  API 원본 응답:\n  {result[:500]}")

        # 파싱 테스트
        ui = UIDiscovery.__new__(UIDiscovery)
        ui._log = lambda x: print(f"    {x}")
        parsed = ui._parse_json(result)

        if parsed:
            print("\n  ✓ 파싱 성공!")
            for name, sel in parsed.items():
                status = "✓" if sel and sel != "null" else "·"
                print(f"    {status} {name}: {sel}")
            return True
        else:
            print("  ✗ 파싱 실패")
            return False
    except Exception as e:
        print(f"  ✗ 에러: {e}")
        return False


def main():
    print("UI Discovery 테스트")
    print("=" * 50)

    results = []

    # Test 1
    api_key = test_env_loading()
    results.append(("env 로딩", api_key is not None))

    if not api_key:
        print("\nAPI 키 없이 계속할 수 없습니다.")
        return

    # Test 2
    results.append(("API 호출", test_api_call(api_key)))

    # Test 3
    results.append(("JSON 파싱", test_json_parsing()))

    # Test 4
    results.append(("API 분석", test_api_discovery(api_key)))

    # 결과 요약
    print("\n" + "=" * 50)
    print("결과 요약")
    print("=" * 50)
    for name, ok in results:
        print(f"  {'✓' if ok else '✗'} {name}")

    all_ok = all(ok for _, ok in results)
    print(f"\n{'모든 테스트 통과!' if all_ok else '일부 테스트 실패'}")


if __name__ == "__main__":
    main()
