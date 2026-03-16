import json
import re
from pathlib import Path

from modules.api.control_plane_contract import ALLOWED_STAGE0_SUB_KEYS

INDEX_HTML = Path("geuldobi-desktop/src/index.html").read_text(encoding="utf-8")
PROMPT_MAP = json.loads(Path("docs/implementation/prompt-map-v1.json").read_text(encoding="utf-8"))


def _stage0_renderer_sub_keys() -> set[str]:
    return set(
        re.findall(
            r'data-action="stage_0"[^>]*data-key="0"[^>]*data-sub-key="(\d+)"',
            INDEX_HTML,
        )
    )


def test_stage0_submenu_labels_match_backend_modes():
    expected_pairs = [
        ('data-sub-key="1"', "기존 방식 (Bible/Treatment 생성)"),
        ('data-sub-key="2"', "컨셉 → Bible 생성"),
        ('data-sub-key="3"', "역설계 — 기존 원고에서 추출"),
        ('data-sub-key="4"', "Bible JSON 임포트"),
        ('data-sub-key="5"', "Block 확장 — Treatment에 블록 추가"),
        ('data-sub-key="6"', "스타일 레퍼런스 분석"),
        ('data-sub-key="7"', "작품가드 설정 (선택)"),
    ]
    for sub_key, label in expected_pairs:
        assert sub_key in INDEX_HTML
        assert label in INDEX_HTML


def test_stage0_public_submenu_keys_match_prompt_map_and_validator_contract():
    renderer_sub_keys = _stage0_renderer_sub_keys()
    prompt_map_sub_keys = set(PROMPT_MAP["keys"]["0"]["allowed_sub_keys"])
    assert renderer_sub_keys == prompt_map_sub_keys
    assert renderer_sub_keys == set(ALLOWED_STAGE0_SUB_KEYS)
    assert "0" not in renderer_sub_keys


def test_stage0_style_cache_mode_selector_exists():
    assert 'id="stage0StyleCacheMode"' in INDEX_HTML
    assert '>캐시 사용<' in INDEX_HTML
    assert '>캐시 무시 후 재분석<' in INDEX_HTML
    assert '>캐시 삭제 후 재분석<' in INDEX_HTML


def test_investment_menu_badges_are_rendered_without_mutating_labels():
    assert '<span class="label">스타일 레퍼런스 분석</span><span class="menu-badge menu-badge-recommend">추천</span>' in INDEX_HTML
    assert '<span class="label">Frontier Lag</span><span class="menu-badge menu-badge-recommend">추천</span>' in INDEX_HTML
    assert '<span class="label">Arc 설계</span><span class="menu-badge menu-badge-discouraged">비추천</span>' in INDEX_HTML
    assert '<span class="label">Blueprint</span><span class="menu-badge menu-badge-discouraged">비추천</span>' in INDEX_HTML
    assert '<span class="label">원고 생산</span><span class="menu-badge menu-badge-discouraged">비추천</span>' in INDEX_HTML
    assert '<span class="label">One-Stop</span><span class="menu-badge menu-badge-discouraged">비추천</span>' in INDEX_HTML
    assert '<span class="label">컨셉 → Bible 생성</span><span class="menu-badge menu-badge-discouraged">비추천</span>' in INDEX_HTML
    assert '<span class="label">역설계 — 기존 원고에서 추출</span><span class="menu-badge menu-badge-discouraged">비추천</span>' in INDEX_HTML
    assert '<span class="label">Bible JSON 임포트</span><span class="menu-badge menu-badge-discouraged">비추천</span>' in INDEX_HTML
    assert '<span class="label">Block 확장 — Treatment에 블록 추가</span><span class="menu-badge menu-badge-discouraged">비추천</span>' in INDEX_HTML


def test_work_guard_template_controls_exist_in_project_tab():
    assert 'id="workGuardTemplateSelect"' in INDEX_HTML
    assert 'id="refreshWorkGuardTemplatesBtn"' in INDEX_HTML
    assert 'id="applyWorkGuardTemplateBtn"' in INDEX_HTML
    assert "root/work_guards" in INDEX_HTML
