"""[P7-05] Stage4 FailureLearner feedback loop tests.

Verifies that the P6-01 patch correctly wires the FailureLearner injected
via _failure_learner in validation_context into ValidationOrchestrator's
BLOCKING tier, and that a missing/None _failure_learner does not crash.

These tests mock the full pipeline — they only instantiate
ValidationOrchestrator with a minimal config and mock the individual
sub-validators.
"""

from unittest.mock import MagicMock

from modules.validation.validation_orchestrator import ValidationOrchestrator

# Minimal config that avoids real LLM calls and skips optional tiers
_MINIMAL_CONFIG = {
    "use_pre_llm": False,
    "use_self_consistency": False,
    "use_adaptive_threshold": False,
    "use_retrospective": False,
    "use_reflexion": False,
    "scoring_threshold": 70,
    "scoring_model": "gemini-2.5-pro",
    "advisory_model": "gemini-2.5-flash",
}

# A manuscript that is 1000 Korean characters (passes minimum-length check)
_MANUSCRIPT = "가" * 1000


def _make_orchestrator() -> ValidationOrchestrator:
    """Build a ValidationOrchestrator with all external calls mocked."""
    orch = ValidationOrchestrator(config=_MINIMAL_CONFIG, client=None, genre="wuxia")
    # Stub out tiers that make real LLM calls
    orch.scoring = MagicMock()
    orch.scoring.pass_threshold = 70
    orch.scoring.validate = MagicMock(
        return_value={
            "passed": True,
            "score": 80,
            "feedback": "",
            "violations": [],
        }
    )
    # [TF-36] advisory 전환 후 SCORING까지 진행하므로 validate_v59도 stub
    orch.scoring.validate_v59 = MagicMock(
        return_value={
            "total_score": 50,
            "message": "fallback",
            "feedback": "",
            "score_breakdown": {},
        }
    )
    orch.advisory = MagicMock()
    orch.advisory.validate = MagicMock(
        return_value={
            "passed": True,
            "suggestions": [],
            "feedback": "",
        }
    )
    # [TF-36] CatharsisTimer/ActionSceneEvaluator stub
    orch.catharsis_timer = MagicMock()
    orch.catharsis_timer.check_catharsis_timing = MagicMock(return_value={"status": "ok"})
    orch.action_evaluator = MagicMock()
    orch.action_evaluator.evaluate = MagicMock(return_value={"action_scene_count": 0, "total_score": 0})
    return orch


# ---------------------------------------------------------------------------
# Test 1: BLOCKING failure calls failure_learner.record_failure(stage=4, ...)
# ---------------------------------------------------------------------------


def test_blocking_failure_calls_failure_learner_record_failure():
    orch = _make_orchestrator()

    # Force BLOCKING to fail with a specific failure entry
    orch.blocking = MagicMock()
    orch.blocking.validate = MagicMock(
        return_value={
            "passed": False,
            "failures": [
                {
                    "type": "dead_npc_resurrection",
                    "reason": "사망 NPC 행동 감지",
                    "check": "dead_npc_resurrection",
                    "severity": "CRITICAL",
                }
            ],
            "failure_count": 1,
            "warnings": [],
        }
    )

    # Also stub continuity to pass so BLOCKING is reached
    orch.continuity = MagicMock()
    orch.continuity.validate = MagicMock(
        return_value={
            "tier": "CONTINUITY",
            "passed": True,
            "violations": [],
            "warnings": [],
            "message": "OK",
            "violation_count": 0,
            "warning_count": 0,
        }
    )
    orch.consistency = MagicMock()
    orch.consistency.validate = MagicMock(
        return_value={
            "passed": True,
            "unjustifiable_violations": [],
            "justifiable_violations": [],
            "score_penalty": 0,
            "feedback": "",
        }
    )

    failure_learner = MagicMock()
    validation_context = {
        "mode": "MANUSCRIPT",
        "encyclopedia": {"npcs": [], "items": [], "locations": []},
        "martial_hud": {},
        "_failure_learner": failure_learner,
    }

    result = orch.validate(ep_num=5, manuscript=_MANUSCRIPT, validation_context=validation_context)

    # [TF-36] 대원칙 1: BLOCKING 실패 → advisory 전달 + 감점 → REJECT (점수 기반)
    assert result["final_decision"] == "REJECT"
    assert "_blocking_advisory" in result
    # record_failure must have been called at least once with stage=4
    assert failure_learner.record_failure.called, "FailureLearner.record_failure must be called when BLOCKING fails"
    call_kwargs = failure_learner.record_failure.call_args_list[0]
    # Works for both positional and keyword calls
    args, kwargs = call_kwargs
    stage_val = kwargs.get("stage") if "stage" in kwargs else (args[0] if args else None)
    assert stage_val == 4, f"record_failure must be called with stage=4, got stage={stage_val}"


# ---------------------------------------------------------------------------
# Test 2: _failure_learner=None in context does not crash ValidationOrchestrator
# ---------------------------------------------------------------------------


def test_blocking_failure_with_none_failure_learner_does_not_crash():
    orch = _make_orchestrator()

    orch.blocking = MagicMock()
    orch.blocking.validate = MagicMock(
        return_value={
            "passed": False,
            "failures": [
                {
                    "type": "minimum_length",
                    "reason": "분량 미달",
                    "check": "minimum_length",
                    "severity": "CRITICAL",
                }
            ],
            "failure_count": 1,
            "warnings": [],
        }
    )

    orch.continuity = MagicMock()
    orch.continuity.validate = MagicMock(
        return_value={
            "tier": "CONTINUITY",
            "passed": True,
            "violations": [],
            "warnings": [],
            "message": "OK",
            "violation_count": 0,
            "warning_count": 0,
        }
    )
    orch.consistency = MagicMock()
    orch.consistency.validate = MagicMock(
        return_value={
            "passed": True,
            "unjustifiable_violations": [],
            "justifiable_violations": [],
            "score_penalty": 0,
            "feedback": "",
        }
    )

    validation_context = {
        "mode": "MANUSCRIPT",
        "encyclopedia": {"npcs": [], "items": [], "locations": []},
        "martial_hud": {},
        "_failure_learner": None,  # explicitly None
    }

    # Should not raise
    result = orch.validate(ep_num=5, manuscript=_MANUSCRIPT, validation_context=validation_context)
    # [TF-36] 대원칙 1: BLOCKING 실패 → advisory + 감점 → REJECT (점수 기반)
    assert result["final_decision"] == "REJECT"
    assert "_blocking_advisory" in result


# ---------------------------------------------------------------------------
# Test 3: _failure_learner absent from context does not crash
# ---------------------------------------------------------------------------


def test_blocking_failure_without_failure_learner_key_does_not_crash():
    orch = _make_orchestrator()

    orch.blocking = MagicMock()
    orch.blocking.validate = MagicMock(
        return_value={
            "passed": False,
            "failures": [{"type": "BLOCKING", "reason": "generic", "check": "test", "severity": "HIGH"}],
            "failure_count": 1,
            "warnings": [],
        }
    )

    orch.continuity = MagicMock()
    orch.continuity.validate = MagicMock(
        return_value={
            "tier": "CONTINUITY",
            "passed": True,
            "violations": [],
            "warnings": [],
            "message": "OK",
            "violation_count": 0,
            "warning_count": 0,
        }
    )
    orch.consistency = MagicMock()
    orch.consistency.validate = MagicMock(
        return_value={
            "passed": True,
            "unjustifiable_violations": [],
            "justifiable_violations": [],
            "score_penalty": 0,
            "feedback": "",
        }
    )

    validation_context = {
        "mode": "MANUSCRIPT",
        "encyclopedia": {"npcs": [], "items": [], "locations": []},
        "martial_hud": {},
        # No "_failure_learner" key at all
    }

    result = orch.validate(ep_num=5, manuscript=_MANUSCRIPT, validation_context=validation_context)
    # [TF-36] 대원칙 1: BLOCKING 실패 → advisory + 감점 → REJECT (점수 기반)
    assert result["final_decision"] == "REJECT"
    assert "_blocking_advisory" in result
