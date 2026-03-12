from unittest.mock import MagicMock

from modules.validation.validation_orchestrator import ValidationOrchestrator


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


def test_resolve_soft_failure_log_dir_ignores_magicmock_project_root():
    orchestrator = ValidationOrchestrator(config={}, client=None, context={})
    project = MagicMock()
    project.paths.root = MagicMock()
    project.db.db_path = None

    resolved = orchestrator._resolve_soft_failure_log_dir({"current_project": project})

    assert resolved is None
