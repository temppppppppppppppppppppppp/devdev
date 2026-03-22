import asyncio
from unittest.mock import MagicMock

from modules.validation.validation_orchestrator import ValidationOrchestrator


def test_apply_advisory_penalties_caps_continuity_and_blocking_penalties():
    orchestrator = ValidationOrchestrator.__new__(ValidationOrchestrator)

    total = orchestrator._apply_advisory_penalties(
        100,
        {
            "_continuity_advisory": {"violations": [1, 2, 3, 4]},
            "_blocking_advisory": {"failures": [1, 2, 3, 4, 5]},
        },
    )

    assert total == 65


def test_finalize_validation_result_respects_unconditional_pass_floor():
    orchestrator = ValidationOrchestrator.__new__(ValidationOrchestrator)
    orchestrator._generate_detailed_feedback = MagicMock(return_value="details")
    orchestrator._record_validation_history_v59 = MagicMock()

    results = {}
    finalized = orchestrator._finalize_validation_result(
        ep_num=12,
        total_score=84,
        results=results,
        adaptive_threshold=70,
        pass_threshold=70,
    )

    assert finalized["final_decision"] == "CONDITIONAL_PASS"
    assert finalized["adaptive_threshold"] == 70
    assert finalized["detailed_feedback"] == "details"
    orchestrator._record_validation_history_v59.assert_called_once_with(12, 84, True)


def test_run_parallel_stage2_validators_normalizes_consistency_runtime_failure():
    orchestrator = ValidationOrchestrator.__new__(ValidationOrchestrator)
    orchestrator.max_parallel_workers = 2
    orchestrator.use_self_consistency = False
    orchestrator.client = None
    orchestrator.consistency = MagicMock()
    orchestrator.consistency.validate.side_effect = RuntimeError("boom")
    orchestrator.scoring = MagicMock()
    orchestrator.scoring.validate_v59 = MagicMock(return_value={"total_score": 77, "feedback": "ok"})
    orchestrator.advisory = MagicMock()
    orchestrator.advisory.validate = MagicMock(return_value={"suggestions": []})

    results = {}
    scoring_result, consistency_penalty = asyncio.run(
        orchestrator._run_parallel_stage2_validators("manuscript", {}, results)
    )

    assert scoring_result["total_score"] == 77
    assert consistency_penalty == 0
    assert results["_consistency_advisory"]["severity"] == "CRITICAL"
    assert results["scoring_result"]["total_score"] == 77
