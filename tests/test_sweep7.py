"""[Sweep7] Runtime safety regressions."""

import asyncio
from unittest.mock import MagicMock


def test_batch_validator_gather_exception_is_isolated(monkeypatch):
    """Single gather exception should not crash the full batch result."""
    from modules.validation import batch_validator as bv

    async def _fake_gather(*aws, **kwargs):
        for aw in aws:
            if hasattr(aw, "close"):
                aw.close()
        assert kwargs.get("return_exceptions") is True
        return [RuntimeError("boom"), {"ep_num": 2, "result": {"ok": True}, "success": True}]

    monkeypatch.setattr(bv.asyncio, "gather", _fake_gather)

    validator = bv.BatchValidator(orchestrator=MagicMock(), max_concurrent=2)
    manuscripts = [
        {"ep_num": 1, "manuscript": "a", "validation_context": {}},
        {"ep_num": 2, "manuscript": "b", "validation_context": {}},
    ]

    results = asyncio.run(validator.validate_batch_async(manuscripts))

    assert len(results) == 2
    assert results[0]["success"] is False
    assert "boom" in results[0]["error"]
    assert results[1]["success"] is True


def test_validation_orchestrator_parallel_scoring_failure_nonblocking():
    """Scoring failure should not cancel consistency/advisory in parallel stage."""
    from modules.validation.validation_orchestrator import ValidationOrchestrator

    config = {
        "use_parallel_validation": True,
        "use_pre_llm": False,
        "use_self_consistency": False,
    }
    orch = ValidationOrchestrator(config=config, client=None, genre="wuxia", context={})

    orch.continuity.validate = MagicMock(return_value={"passed": True, "violations": []})
    orch.blocking.validate = MagicMock(return_value={"passed": True, "failures": []})
    orch.consistency.validate = MagicMock(
        return_value={"unjustifiable_violations": [], "score_penalty": 0, "feedback": ""}
    )
    orch.scoring.validate = MagicMock(side_effect=RuntimeError("scoring failed"))
    orch.advisory.validate = MagicMock(return_value={"suggestions": []})
    orch.catharsis_timer.check_catharsis_timing = MagicMock(return_value={"status": "ok"})
    orch.action_evaluator.evaluate = MagicMock(return_value={"action_scene_count": 0})

    result = asyncio.run(
        orch.validate_parallel_v59(
            ep_num=10,
            manuscript="테스트 원고 " * 800,
            validation_context={},
        )
    )

    assert result["consistency_result"]["score_penalty"] == 0
    assert result["advisory_result"]["suggestions"] == []
    assert isinstance(result["scoring_result"], dict)
    assert result["scoring_result"]["total_score"] == 0


def test_validation_orchestrator_parallel_advisory_failure_uses_suggestions_fallback():
    """Advisory task failure should fallback to suggestions key, not warnings."""
    from modules.validation.validation_orchestrator import ValidationOrchestrator

    config = {
        "use_parallel_validation": True,
        "use_pre_llm": False,
        "use_self_consistency": False,
    }
    orch = ValidationOrchestrator(config=config, client=None, genre="wuxia", context={})

    orch.continuity.validate = MagicMock(return_value={"passed": True, "violations": []})
    orch.blocking.validate = MagicMock(return_value={"passed": True, "failures": []})
    orch.consistency.validate = MagicMock(
        return_value={"unjustifiable_violations": [], "score_penalty": 0, "feedback": ""}
    )
    orch.scoring.validate = MagicMock(return_value={"total_score": 75, "breakdown": {}, "feedback": ""})
    orch.advisory.validate = MagicMock(side_effect=RuntimeError("advisory failed"))
    orch.catharsis_timer.check_catharsis_timing = MagicMock(return_value={"status": "ok"})
    orch.action_evaluator.evaluate = MagicMock(return_value={"action_scene_count": 0})

    result = asyncio.run(
        orch.validate_parallel_v59(
            ep_num=10,
            manuscript="테스트 원고 " * 800,
            validation_context={},
        )
    )

    assert result["advisory_result"]["suggestions"] == []
