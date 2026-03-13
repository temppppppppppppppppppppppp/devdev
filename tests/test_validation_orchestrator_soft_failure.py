from unittest.mock import MagicMock

from modules.validation.validation_orchestrator import ValidationOrchestrator

_MINIMAL_CONFIG = {
    "use_pre_llm": False,
    "use_self_consistency": False,
    "use_adaptive_threshold": False,
    "use_retrospective": False,
    "use_reflexion": False,
    "scoring_threshold": 70,
}
_MANUSCRIPT = "가" * 1000


def _make_orchestrator():
    orchestrator = ValidationOrchestrator(config=_MINIMAL_CONFIG, client=None, context={})
    orchestrator.scoring = MagicMock()
    orchestrator.scoring.pass_threshold = 70
    orchestrator.scoring.validate_v59 = MagicMock(
        return_value={"total_score": 50, "message": "fallback", "feedback": "", "score_breakdown": {}}
    )
    orchestrator.advisory = MagicMock()
    orchestrator.advisory.validate = MagicMock(return_value={"passed": True, "suggestions": [], "feedback": ""})
    orchestrator.continuity = MagicMock()
    orchestrator.continuity.validate = MagicMock(
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
    orchestrator.consistency = MagicMock()
    orchestrator.consistency.validate = MagicMock(
        return_value={
            "passed": True,
            "unjustifiable_violations": [],
            "justifiable_violations": [],
            "score_penalty": 0,
            "feedback": "",
        }
    )
    orchestrator.blocking = MagicMock()
    orchestrator.blocking.validate = MagicMock(
        return_value={
            "passed": False,
            "failures": [{"type": "BLOCKING", "reason": "boom", "description": "boom"}],
            "failure_count": 1,
            "warnings": [],
        }
    )
    orchestrator.catharsis_timer = MagicMock()
    orchestrator.catharsis_timer.check_catharsis_timing = MagicMock(return_value={"status": "ok"})
    orchestrator.action_evaluator = MagicMock()
    orchestrator.action_evaluator.evaluate = MagicMock(return_value={"action_scene_count": 0, "total_score": 0})
    orchestrator._record_failure_to_reflexion = MagicMock()
    return orchestrator


def test_report_soft_failure_relays_to_audit_event(tmp_path):
    orchestrator = ValidationOrchestrator(config={}, client=None, context={})
    audit_event = MagicMock()

    orchestrator._report_soft_failure(
        {"audit_event": audit_event, "project_dir": tmp_path},
        "failure_learner_record_failure",
        RuntimeError("failure memory down"),
        ep_num=12,
        message="FailureLearner.record_failure failed during blocking advisory collection",
        extra={"validator": "BlockingValidator"},
    )

    audit_event.assert_called_once()
    call_args = audit_event.call_args.args
    assert call_args[0] == "soft_failure"
    assert "failure_learner_record_failure" in call_args[1]
    assert call_args[2]["component"] == "validation_orchestrator"
    assert call_args[2]["ep_num"] == 12
    assert (tmp_path / "logs" / "soft_failures.jsonl").exists()


def test_validate_reports_soft_failure_when_failure_learner_record_raises(tmp_path):
    orchestrator = _make_orchestrator()
    audit_event = MagicMock()
    failure_learner = MagicMock()
    failure_learner.record_failure.side_effect = RuntimeError("failure memory down")

    result = orchestrator.validate(
        ep_num=12,
        manuscript=_MANUSCRIPT,
        validation_context={
            "_failure_learner": failure_learner,
            "audit_event": audit_event,
            "project_dir": tmp_path,
            "mode": "MANUSCRIPT",
        },
    )

    assert result["final_decision"] == "REJECT"
    audit_event.assert_called_once()
    call_args = audit_event.call_args.args
    assert call_args[0] == "soft_failure"
    assert "failure_learner_record_failure" in call_args[1]
    assert call_args[2]["ep_num"] == 12
    assert call_args[2]["component"] == "validation_orchestrator"
    assert (tmp_path / "logs" / "soft_failures.jsonl").exists()


def test_validate_parallel_sync_reports_soft_failure_when_failure_learner_record_raises(tmp_path):
    orchestrator = _make_orchestrator()
    audit_event = MagicMock()
    failure_learner = MagicMock()
    failure_learner.record_failure.side_effect = RuntimeError("parallel failure memory down")

    result = orchestrator.validate_parallel_sync_v59(
        ep_num=13,
        manuscript=_MANUSCRIPT,
        validation_context={
            "_failure_learner": failure_learner,
            "audit_event": audit_event,
            "project_dir": tmp_path,
            "mode": "MANUSCRIPT",
        },
    )

    assert result["final_decision"] == "REJECT"
    audit_event.assert_called_once()
    call_args = audit_event.call_args.args
    assert call_args[0] == "soft_failure"
    assert "failure_learner_record_failure_parallel" in call_args[1]
    assert call_args[2]["ep_num"] == 13
    assert call_args[2]["component"] == "validation_orchestrator"
    assert call_args[2]["extra"]["mode"] == "parallel"
    assert (tmp_path / "logs" / "soft_failures.jsonl").exists()


def test_resolve_soft_failure_log_dir_ignores_magicmock_project_root():
    orchestrator = ValidationOrchestrator(config={}, client=None, context={})
    project = MagicMock()
    project.paths.root = MagicMock()
    project.db.db_path = None

    resolved = orchestrator._resolve_soft_failure_log_dir({"current_project": project})

    assert resolved is None
