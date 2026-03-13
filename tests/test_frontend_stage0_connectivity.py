from pathlib import Path


INDEX_HTML = Path("geuldobi-desktop/src/index.html").read_text(encoding="utf-8")


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


def test_stage0_style_cache_mode_selector_exists():
    assert 'id="stage0StyleCacheMode"' in INDEX_HTML
    assert '>캐시 사용<' in INDEX_HTML
    assert '>캐시 무시 후 재분석<' in INDEX_HTML
    assert '>캐시 삭제 후 재분석<' in INDEX_HTML


def test_work_guard_template_controls_exist_in_project_tab():
    assert 'id="workGuardTemplateSelect"' in INDEX_HTML
    assert 'id="refreshWorkGuardTemplatesBtn"' in INDEX_HTML
    assert 'id="applyWorkGuardTemplateBtn"' in INDEX_HTML
    assert "root/work_guards" in INDEX_HTML
