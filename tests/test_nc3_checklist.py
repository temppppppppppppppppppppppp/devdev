"""
[NC-3] Director 일관성 체크리스트 스키마 확장 테스트
"""

import logging

from modules.core.response_schemas import DIRECTOR_AUDIT_SCHEMA

# ── 체크리스트 12개 키 정의 ──────────────────────────────────
NC3_KEYS = [
    "numeric_accuracy",
    "arithmetic",
    "title_consistency",
    "scene_overlap",
    "percent_calculation",
    "event_ordering",
    "space_continuity",
    "npc_identity",
    "time_progression",
    "opening_diversity",
    "timeline_arc_consistency",  # [NS-4] Arc 간 시간 연속성
    "fiction_term_leak",          # [TF-57-A] 집필 시스템 내부 용어 누출
]


# ── 1. director.yaml에 consistency_checklist 출력 형식 존재 ──
def test_director_yaml_has_checklist_format():
    """director.yaml ENSEMBLE_VARIABLE_PROMPT에 consistency_checklist 출력 형식이 포함되어 있는지 확인"""
    from modules.core.prompt_loader import PromptLoader

    loader = PromptLoader()
    variable = loader.get_raw("director", "ENSEMBLE_VARIABLE_PROMPT") or ""
    assert "consistency_checklist" in variable, "ENSEMBLE_VARIABLE_PROMPT에 consistency_checklist 누락"


# ── 2. director.yaml에 12개 항목 지시 텍스트 존재 ──
def test_director_yaml_has_checklist_instructions():
    """director.yaml ENSEMBLE_VARIABLE_PROMPT에 NC-3 체크 지시 텍스트가 포함되어 있는지 확인"""
    from modules.core.prompt_loader import PromptLoader

    loader = PromptLoader()
    variable = loader.get_raw("director", "ENSEMBLE_VARIABLE_PROMPT") or ""
    assert "[NC-3]" in variable, "ENSEMBLE_VARIABLE_PROMPT에 [NC-3] 지시 누락"
    assert "일관성 체크리스트" in variable


# ── 3. director.yaml에 12개 key 전량 포함 ──
def test_director_yaml_has_all_12_keys():
    """director.yaml의 출력 형식에 12개 key가 모두 포함되어 있는지 확인"""
    from modules.core.prompt_loader import PromptLoader

    loader = PromptLoader()
    variable = loader.get_raw("director", "ENSEMBLE_VARIABLE_PROMPT") or ""
    for key in NC3_KEYS:
        assert key in variable, f"ENSEMBLE_VARIABLE_PROMPT에 key '{key}' 누락"


# ── 4. DIRECTOR_AUDIT_SCHEMA에 consistency_checklist 존재 ──
def test_schema_has_consistency_checklist():
    """DIRECTOR_AUDIT_SCHEMA에 consistency_checklist 프로퍼티가 존재하는지 확인"""
    props = DIRECTOR_AUDIT_SCHEMA.properties
    assert "consistency_checklist" in props, "DIRECTOR_AUDIT_SCHEMA에 consistency_checklist 누락"


# ── 5. 스키마에 12개 key 전량 포함 ──
def test_schema_has_all_12_keys():
    """consistency_checklist 스키마에 12개 key가 모두 포함되어 있는지 확인"""
    checklist_schema = DIRECTOR_AUDIT_SCHEMA.properties["consistency_checklist"]
    for key in NC3_KEYS:
        assert key in checklist_schema.properties, f"스키마에 key '{key}' 누락"


# ── 6. 전체 OK → 점수 변동 없음 ──
def test_all_ok_no_score_change():
    """전체 OK이면 python_warnings 점수 변동 없음"""
    checklist = {k: "OK" for k in NC3_KEYS}
    result = _build_mock_result(checklist=checklist, pw=10)
    score = _apply_nc3_logic(result, score=95)
    assert score == 95, f"전체 OK인데 점수가 변동됨: {score}"
    assert result["score_breakdown"]["python_warnings"] == 10


# ── 7. ISSUE 3건+ → python_warnings 상한 3 ──
def test_issue_3_plus_caps_python_warnings():
    """ISSUE 3건 이상이면 python_warnings가 3으로 제한됨"""
    checklist = {k: "OK" for k in NC3_KEYS}
    checklist["numeric_accuracy"] = "ISSUE"
    checklist["arithmetic"] = "ISSUE"
    checklist["scene_overlap"] = "ISSUE"
    result = _build_mock_result(checklist=checklist, pw=10)
    score = _apply_nc3_logic(result, score=95)
    assert result["score_breakdown"]["python_warnings"] == 3
    # 총점도 감소해야 함 (10→3 = -7)
    assert score == 88


# ── 8. 체크리스트 누락 → 점수 변동 없음 ──
def test_missing_checklist_no_penalty():
    """체크리스트가 누락되어도 점수 변동 없음 (안정화 기간)"""
    result = _build_mock_result(checklist=None, pw=10)
    score = _apply_nc3_logic(result, score=95)
    assert score == 95
    assert result["score_breakdown"]["python_warnings"] == 10


# ── 9. 반환 dict에 consistency_checklist 전파 ──
def test_checklist_propagated_in_return():
    """반환 dict에 consistency_checklist가 포함되는지 확인"""
    checklist = {k: "OK" for k in NC3_KEYS}
    result = _build_mock_result(checklist=checklist, pw=10)
    _apply_nc3_logic(result, score=95)
    assert "consistency_checklist" in result
    assert result["consistency_checklist"] == checklist


# ── 10. ISSUE 2건 → 경고 로깅만, 감점 없음 ──
def test_issue_2_no_penalty(caplog):
    """ISSUE 2건이면 경고만 남기고 감점하지 않음"""
    checklist = {k: "OK" for k in NC3_KEYS}
    checklist["numeric_accuracy"] = "ISSUE"
    checklist["arithmetic"] = "ISSUE"
    result = _build_mock_result(checklist=checklist, pw=10)
    with caplog.at_level(logging.WARNING):
        score = _apply_nc3_logic(result, score=95)
    assert score == 95
    assert result["score_breakdown"]["python_warnings"] == 10
    assert any("[NC-3]" in r.message for r in caplog.records)


# ── 11. ENSEMBLE_SELECTION_PROMPT에도 checklist 형식 존재 ──
def test_ensemble_selection_prompt_has_checklist():
    """ENSEMBLE_SELECTION_PROMPT에도 consistency_checklist 출력 형식이 포함되어 있는지"""
    from modules.core.prompt_loader import PromptLoader

    loader = PromptLoader()
    selection = loader.get_raw("director", "ENSEMBLE_SELECTION_PROMPT") or ""
    assert "consistency_checklist" in selection, "ENSEMBLE_SELECTION_PROMPT에 consistency_checklist 누락"


# ═══════════════════════════════════════════════════════════════
# [NC-3B] score_breakdown 합산 Self-Consistency 테스트
# ═══════════════════════════════════════════════════════════════


def test_score_breakdown_sum_matches_no_change():
    """합산이 score와 일치하면 변동 없음"""
    score = 95
    result = {
        "score_breakdown": {
            "continuity_contradiction": 35,
            "blueprint_coverage": 20,
            "quality_engagement": 20,
            "length": 10,
            "python_warnings": 10,
        }
    }
    score = _apply_nc3b_breakdown_check(result, score)
    assert score == 95


def test_score_breakdown_sum_mismatch_corrected():
    """합산 ≠ score 시 breakdown 합산으로 교정"""
    score = 75  # LLM이 실수로 75를 씀
    result = {
        "score_breakdown": {
            "continuity_contradiction": 35,
            "blueprint_coverage": 20,
            "quality_engagement": 20,
            "length": 10,
            "python_warnings": 8,
        }
    }
    # 합산 = 93
    score = _apply_nc3b_breakdown_check(result, score)
    assert score == 93


def test_score_breakdown_empty_no_correction():
    """breakdown이 비어 있으면 교정 안 함"""
    score = 75
    result = {"score_breakdown": {}}
    score = _apply_nc3b_breakdown_check(result, score)
    assert score == 75


def test_score_breakdown_clamp_100():
    """합산이 100 초과 시 100으로 클램프"""
    score = 80
    result = {
        "score_breakdown": {
            "continuity_contradiction": 50,
            "blueprint_coverage": 30,
            "quality_engagement": 30,
            "length": 10,
            "python_warnings": 10,
        }
    }
    # 합산 = 130
    score = _apply_nc3b_breakdown_check(result, score)
    assert score == 100


def test_score_breakdown_negative_sum_no_correction():
    """합산이 0 이하면 이상 데이터로 간주하여 교정하지 않음"""
    score = 50
    result = {
        "score_breakdown": {
            "continuity_contradiction": -10,
            "blueprint_coverage": -5,
            "quality_engagement": 0,
            "length": 0,
            "python_warnings": 0,
        }
    }
    # 합산 = -15 → _sb_sum > 0 불충족 → 교정 안 함
    score = _apply_nc3b_breakdown_check(result, score)
    assert score == 50


def test_few_shot_example_in_variable_prompt():
    """director.yaml ENSEMBLE_VARIABLE_PROMPT에 NC-3B few-shot 예시가 존재하는지"""
    from modules.core.prompt_loader import PromptLoader

    loader = PromptLoader()
    variable = loader.get_raw("director", "ENSEMBLE_VARIABLE_PROMPT") or ""
    assert "NC-3B" in variable, "ENSEMBLE_VARIABLE_PROMPT에 [NC-3B] few-shot 예시 누락"
    assert "consistency_checklist 응답 예시" in variable
    assert "score_breakdown 5개 항목의 합산이 반드시 score와 일치" in variable


# ═══════════════════════════════════════════════════════════════
# 헬퍼 함수 — director_ensemble.py의 NC-3 로직을 재현
# ═══════════════════════════════════════════════════════════════


def _apply_nc3b_breakdown_check(result, score):
    """director_ensemble.py의 NC-3B breakdown 합산 검증 로직 재현"""
    _sb_raw = result.get("score_breakdown", {})
    if isinstance(_sb_raw, dict) and _sb_raw:
        _sb_sum = sum(v for v in _sb_raw.values() if isinstance(v, int | float))
        if _sb_sum != score and _sb_sum > 0:
            score = max(0, min(100, _sb_sum))
    return score


def _build_mock_result(checklist, pw=10):
    """테스트용 Director 응답 mock 생성"""
    result = {
        "score_breakdown": {
            "continuity_contradiction": 35,
            "blueprint_coverage": 20,
            "quality_engagement": 20,
            "length": 10,
            "python_warnings": pw,
        },
        "consistency_checklist": checklist,
    }
    return result


def _apply_nc3_logic(result, score):
    """director_ensemble.py의 NC-3 로직을 그대로 재현"""
    _checklist = result.get("consistency_checklist") or {}
    _nc3_keys = NC3_KEYS

    if isinstance(_checklist, dict) and _checklist:
        _issue_count = sum(1 for k in _nc3_keys if str(_checklist.get(k, "")).upper() == "ISSUE")
        if _issue_count > 0:
            logging.warning(
                "[NC-3] consistency_checklist ISSUE %d건 감지: %s",
                _issue_count,
                [k for k in _nc3_keys if str(_checklist.get(k, "")).upper() == "ISSUE"],
            )
        if _issue_count >= 3:
            _sb = result.get("score_breakdown", {})
            if isinstance(_sb, dict):
                _pw = _sb.get("python_warnings", 10)
                if isinstance(_pw, int | float) and _pw > 3:
                    logging.info(
                        "[NC-3] python_warnings %d → 3 (ISSUE %d건)",
                        _pw,
                        _issue_count,
                    )
                    _sb["python_warnings"] = 3
                    _new_total = sum(v for v in _sb.values() if isinstance(v, int | float))
                    if _new_total < score:
                        score = _new_total
    else:
        logging.info("[NC-3] Director가 consistency_checklist를 생략함 — 감점 없음 (안정화 기간)")

    return score
