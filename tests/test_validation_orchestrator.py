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
