"""ValidationOrchestrator 핵심 경로 테스트."""

from unittest.mock import MagicMock

from modules.validation.blocking_validator import BlockingValidator
from modules.validation.validation_orchestrator import ValidationOrchestrator


def _minimal_context() -> dict:
    return {
        "mode": "MANUSCRIPT",
        "encyclopedia": {},
        "martial_hud": {},
        "blueprint": {},
        "history": [],
        "npc_profiles": {},
    }


def test_orchestrator_loads_extended_genre_profile():
    orch = ValidationOrchestrator(config={}, client=None, genre="composer", context={})
    assert orch.threshold_profile["base_threshold"] == 71


def test_build_reject_result_normalizes_stage_key():
    orch = ValidationOrchestrator(config={}, client=None, genre="wuxia", context={})
    result = orch._build_reject_result_v59("PRE-LLM", {"passed": False}, "fail")
    assert result["final_decision"] == "REJECT"
    assert "pre_llm_result" in result
    assert result["early_exit_stage"] == "PRE-LLM"


def test_calculate_adaptive_threshold_is_clamped():
    orch = ValidationOrchestrator(config={}, client=None, genre="medical", context={})
    orch.consecutive_fails = 5
    threshold = orch.calculate_adaptive_threshold_v59(
        ep_num=50,
        validation_context={"pattern_analysis": {"repetition_score": 90, "diversity_score": 20}},
    )
    assert 60 <= threshold <= 90


def test_episode_type_adjustment_treats_opening_as_higher_bar():
    orch = ValidationOrchestrator(config={}, client=None, genre="wuxia", context={})

    adjustment = orch._get_episode_type_adjustment_v59(1)

    assert adjustment == 5


def test_episode_type_adjustment_combines_strongest_positive_and_negative_only():
    orch = ValidationOrchestrator(config={}, client=None, genre="wuxia", context={})

    adjustment = orch._get_episode_type_adjustment_v59(5)

    assert adjustment == 2


def test_episode_type_adjustment_uses_strongest_positive_for_volume_finale():
    orch = ValidationOrchestrator(config={}, client=None, genre="wuxia", context={})

    adjustment = orch._get_episode_type_adjustment_v59(50)

    assert adjustment == 7


def test_validate_short_circuit_on_blocking_failure():
    """[TF-36] BLOCKING 실패 시 즉시 REJECT 대신 advisory 전달 + 감점."""
    orch = ValidationOrchestrator(config={"use_pre_llm": False}, client=None, genre="wuxia", context={})
    orch.continuity = MagicMock()
    orch.blocking = MagicMock()
    orch.continuity.validate.return_value = {"passed": True, "violations": [], "warning_count": 0}
    orch.blocking.validate.return_value = {"passed": False, "failures": [{"reason": "too short"}]}

    result = orch.validate(1, "테스트 원고", _minimal_context())
    # [TF-36] 대원칙 1: 즉시 REJECT 대신 advisory + 감점 → Director 판정 위임
    assert "_blocking_advisory" in result
    assert result["_blocking_advisory"]["source"] == "BlockingValidator"
    # 감점이 적용되어 총점이 낮아지고, REJECT 판정은 점수 기반으로 이루어짐
    assert result["final_decision"] in ("REJECT", "CONDITIONAL_PASS")  # 점수에 따라 결정


def test_validate_parallel_sync_falls_back_to_sync_when_parallel_fails():
    orch = ValidationOrchestrator(config={}, client=None, genre="wuxia", context={})
    orch.validate_parallel_v59 = MagicMock(side_effect=RuntimeError("parallel failed"))
    orch.validate = MagicMock(return_value={"final_decision": "PASS"})

    result = orch.validate_parallel_sync_v59(1, "원고", _minimal_context())
    assert result["final_decision"] == "PASS"
    orch.validate.assert_called_once()


def test_validate_surfaces_blocking_degraded_advisory_without_failure():
    orch = ValidationOrchestrator(config={"use_pre_llm": False}, client=None, genre="wuxia", context={})
    orch.continuity = MagicMock()
    orch.consistency = MagicMock()
    orch.blocking = MagicMock()
    orch.continuity.validate.return_value = {"passed": True, "violations": [], "warning_count": 0}
    orch.consistency.validate.return_value = {
        "passed": True,
        "unjustifiable_violations": [],
        "justifiable_violations": [],
        "score_penalty": 0,
        "feedback": "",
    }
    orch.blocking.validate.return_value = {
        "passed": True,
        "failures": [],
        "warnings": ["degraded: relationship_consistency"],
        "degraded_checks": ["relationship_consistency"],
    }

    result = orch.validate(1, "테스트 원고", _minimal_context())

    assert "_blocking_advisory" in result
    assert result["_blocking_advisory"]["severity"] == "MEDIUM"
    assert result["_blocking_advisory"]["warnings"] == ["degraded: relationship_consistency"]
    assert result["_blocking_advisory"]["degraded_checks"] == ["relationship_consistency"]


def test_validate_surfaces_scene_separation_warning_as_director_advisory():
    """Visible scene header 없는 separation gap은 Blocking 실패가 아니라 Director advisory로 전달된다."""
    orch = ValidationOrchestrator(
        config={
            "use_pre_llm": False,
            "use_adaptive_threshold": False,
            "use_retrospective": False,
            "use_self_consistency": False,
            "scoring_threshold": 60,
        },
        client=None,
        genre="wuxia",
        context={},
    )
    orch.continuity = MagicMock()
    orch.consistency = MagicMock()
    orch.scoring = MagicMock()
    orch.advisory = MagicMock()
    orch.blocking = BlockingValidator(enable_justification_checks=False)

    orch.continuity.validate.return_value = {"passed": True, "violations": [], "warning_count": 0}
    orch.consistency.validate.return_value = {
        "passed": True,
        "unjustifiable_violations": [],
        "justifiable_violations": [],
        "score_penalty": 0,
        "feedback": "",
    }
    orch.scoring.pass_threshold = 60
    orch.scoring.validate_v59.return_value = {
        "total_score": 82,
        "breakdown": {},
        "feedback": "ok",
    }
    orch.advisory.validate.return_value = {"suggestions": []}

    manuscript = "헤더 없는 산문 원고입니다. 장면의 체류와 감정선이 이어졌다. " * 170
    context = {
        **_minimal_context(),
        "blueprint": {
            "scene_breakdown": {
                "scene_1": {"description": "객잔 도착"},
                "scene_2": {"description": "비밀 문서 확보"},
                "scene_3": {"description": "추격전"},
                "scene_4": {"description": "새 단서 발견"},
                "scene_5": {"description": "다음 목표 확정"},
            }
        },
    }

    result = orch.validate(7, manuscript, context)

    assert result["blocking_result"]["passed"] is True
    assert result["blocking_result"]["failures"] == []
    assert any("scene_completeness" in warning for warning in result["blocking_result"]["warnings"])
    assert "_blocking_advisory" in result
    assert result["_blocking_advisory"]["severity"] == "MEDIUM"
    assert result["_blocking_advisory"]["failures"] == []
    assert any(
        "scene_completeness" in warning and "Director advisory" in warning
        for warning in result["_blocking_advisory"]["warnings"]
    )
