"""ValidationOrchestrator 핵심 경로 테스트."""

from unittest.mock import MagicMock

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


def test_validate_short_circuit_on_blocking_failure():
    orch = ValidationOrchestrator(config={"use_pre_llm": False}, client=None, genre="wuxia", context={})
    orch.continuity = MagicMock()
    orch.blocking = MagicMock()
    orch.continuity.validate.return_value = {"passed": True, "violations": [], "warning_count": 0}
    orch.blocking.validate.return_value = {"passed": False, "failures": [{"reason": "too short"}]}

    result = orch.validate(1, "테스트 원고", _minimal_context())
    assert result["final_decision"] == "REJECT"
    assert "BLOCKING" in result["reason"]


def test_validate_parallel_sync_falls_back_to_sync_when_parallel_fails():
    orch = ValidationOrchestrator(config={}, client=None, genre="wuxia", context={})
    orch.validate_parallel_v59 = MagicMock(side_effect=RuntimeError("parallel failed"))
    orch.validate = MagicMock(return_value={"final_decision": "PASS"})

    result = orch.validate_parallel_sync_v59(1, "원고", _minimal_context())
    assert result["final_decision"] == "PASS"
    orch.validate.assert_called_once()
