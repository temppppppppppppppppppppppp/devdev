from unittest.mock import MagicMock

from modules.domain.agents.state_extractor import StateExtractor


def _make_extractor(*, genre_name: str = "투자", genre_type: str = "investment") -> StateExtractor:
    extractor = StateExtractor.__new__(StateExtractor)
    ctx = MagicMock()
    ctx.guard.get_genre_name.return_value = genre_name
    project = MagicMock()
    project.genre = {"name": genre_name, "type": genre_type}
    ctx.current_project = project
    extractor.context = ctx
    return extractor


def test_validate_and_fix_result_downgrades_non_wuxia_soft_fatigue_constraints():
    extractor = _make_extractor()
    raw = {
        "protagonist_state": {
            "injuries": [{"name": "신경계 피로", "severity": "Moderate", "recovery_days": 2}],
            "internal_energy": {"current_percent": 35},
        },
        "inventory": {"current_items": []},
        "next_arc_constraints": {
            "must_start_with": "이전 상태 계승",
            "recovery_scene_required": True,
            "min_time_skip_days": 2,
        },
    }

    out = extractor._validate_and_fix_result(raw, {"joint_docs": {}})

    assert out["next_arc_constraints"]["recovery_scene_required"] is False
    assert out["next_arc_constraints"]["must_start_with"] is None
    assert out["next_arc_constraints"]["min_time_skip_days"] == 0


def test_validate_and_fix_result_keeps_non_wuxia_physical_injury_hard():
    extractor = _make_extractor()
    raw = {
        "protagonist_state": {
            "injuries": [{"name": "골절된 손목", "severity": "중상", "recovery_days": 5}],
            "internal_energy": {"current_percent": 35},
        },
        "inventory": {"current_items": []},
    }

    out = extractor._validate_and_fix_result(raw, {"joint_docs": {}})

    assert out["next_arc_constraints"]["recovery_scene_required"] is True
    assert out["next_arc_constraints"]["must_start_with"] == "이전 상태 계승"
    assert out["next_arc_constraints"]["min_time_skip_days"] == 5


def test_generate_constraint_prompt_softens_non_wuxia_soft_state_language():
    extractor = _make_extractor()
    state = {
        "protagonist_state": {
            "injuries": [{"name": "신경계 피로", "severity": "Moderate", "recovery_days": 2}],
            "internal_energy": {"current_percent": 35, "recovery_needed_days": 3},
        },
        "inventory": {"current_items": []},
        "forbidden_in_next_arc": {},
        "next_arc_constraints": {
            "recovery_scene_required": False,
            "must_start_with": None,
            "min_time_skip_days": 0,
        },
    }

    prompt = extractor.generate_constraint_prompt(state)

    assert "SOFT STATE ADVISORY" in prompt
    assert "일상 회복 가능" in prompt
    assert "회복 장면 필수" not in prompt
    assert "위반 시 즉시 REJECT" not in prompt


def test_fallback_extraction_treats_non_wuxia_soft_state_as_advisory():
    extractor = _make_extractor()
    arc_data = {
        "arc_no": 1,
        "joint_docs": {"final_location": "여의도", "physical_inventory": []},
        "status_shadow": {"expected_injuries": "신경계 피로 Moderate", "internal_energy_loss": "70%"},
        "state_constraints": {"arc_end_state": {}},
        "tactical_doc": "시장 마감 후 피로가 누적되었다.",
    }

    out = extractor._fallback_extraction(arc_data)

    assert out["next_arc_constraints"]["recovery_scene_required"] is False
    assert out["next_arc_constraints"]["must_start_with"] is None
    assert out["protagonist_state"]["internal_energy"]["current_percent"] == 100
