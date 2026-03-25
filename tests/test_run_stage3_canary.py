import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import scripts.run_stage3_canary as canary_script


def test_run_stage3_canary_calls_stage3_only_and_analyzes():
    """Stage 3 canary must call _run_stage3_only, never any Stage 4 method."""
    stage3_orch = MagicMock()
    stage3_orch.stage_3_batch_blueprinting = MagicMock(return_value={"success_count": 4, "fail_count": 0})

    app = SimpleNamespace(
        _get_int_input=None,
        _stage3_orch=stage3_orch,
        pass_rate_monitor=MagicMock(),
        _flush_audit_buffer=MagicMock(),
        memory=None,
        current_project=SimpleNamespace(db=MagicMock()),
    )
    app.current_project.db.conn = MagicMock()
    app.current_project.db.close = MagicMock()

    with (
        patch.object(canary_script, "_load_project_genre", return_value={"type": "wuxia", "name": "wuxia"}),
        patch.object(canary_script, "_boot_app", return_value=app),
        patch.object(canary_script, "analyze_canary", return_value={"hard_gates": {"status": "pass"}}) as analyze,
        patch("modules.core.stage3_context.Stage3Context") as mock_ctx_cls,
    ):
        mock_ctx_cls.from_app.return_value = MagicMock()
        result = canary_script.run_canary("test_s3_canary", target_ep=4)

    stage3_orch.stage_3_batch_blueprinting.assert_called_once_with(target_ep=4)
    app.pass_rate_monitor.save.assert_called_once()
    app._flush_audit_buffer.assert_called_once()
    analyze.assert_called_once_with("test_s3_canary", target_ep=4)
    assert result["hard_gates"]["status"] == "pass"

    # Stage 4 was never called
    assert not hasattr(app, "_stage_4_v2_chief_writer")
    assert not hasattr(app, "_one_stop_pipeline_frontier_lag")


def test_run_stage3_canary_sets_stage3_context():
    """Verify that Stage3Context.from_app is called before stage3 invocation."""
    observed = {}
    stage3_orch = MagicMock()

    def _capture_call(**kwargs):
        observed["ctx_at_call"] = stage3_orch.ctx
        return {"success_count": 1, "fail_count": 0}

    stage3_orch.stage_3_batch_blueprinting = MagicMock(side_effect=_capture_call)

    app = SimpleNamespace(
        _get_int_input=None,
        _stage3_orch=stage3_orch,
        pass_rate_monitor=MagicMock(),
        _flush_audit_buffer=MagicMock(),
        memory=None,
        current_project=SimpleNamespace(db=MagicMock()),
    )
    app.current_project.db.conn = MagicMock()
    app.current_project.db.close = MagicMock()

    fake_ctx = MagicMock(name="fake_stage3_ctx")
    with (
        patch.object(canary_script, "_load_project_genre", return_value={"type": "wuxia", "name": "wuxia"}),
        patch.object(canary_script, "_boot_app", return_value=app),
        patch.object(canary_script, "analyze_canary", return_value={}),
        patch("modules.core.stage3_context.Stage3Context") as mock_ctx_cls,
    ):
        mock_ctx_cls.from_app.return_value = fake_ctx
        canary_script.run_canary("test_s3_ctx", target_ep=4)

    mock_ctx_cls.from_app.assert_called_once_with(app)
    assert observed["ctx_at_call"] is fake_ctx


def test_analyze_stage3_canary_writes_summary(tmp_path):
    summary = {
        "summary_role": "stage3_only_canary",
        "project": "s3test",
        "hard_gates": {"status": "pass", "errors": [], "warnings": []},
    }

    with (
        patch.object(canary_script, "PROJECT_ROOT", tmp_path),
        patch.object(canary_script, "build_stage3_canary_summary", return_value=summary),
    ):
        project_root = tmp_path / "projects" / "s3test"
        (project_root / "logs").mkdir(parents=True, exist_ok=True)
        result = canary_script.analyze_canary("s3test", target_ep=4)

    assert result["summary_role"] == "stage3_only_canary"
    summary_path = project_root / "logs" / "stage3_canary_summary.json"
    assert summary_path.exists()
    saved = json.loads(summary_path.read_text(encoding="utf-8"))
    assert saved["hard_gates"]["status"] == "pass"


def test_stage3_canary_summary_gates_pass():
    """build_stage3_canary_summary gates should pass when all blueprints exist."""
    from modules.core.stage4_canary_tools import _evaluate_stage3_canary_gates

    detail = [
        {"ep_num": 1, "attempt_count": 1, "final_verdict": "PASS", "final_score": 90, "all_verdicts": ["PASS"]},
        {"ep_num": 2, "attempt_count": 1, "final_verdict": "PASS", "final_score": 88, "all_verdicts": ["PASS"]},
        {"ep_num": 3, "attempt_count": 2, "final_verdict": "PASS", "final_score": 85, "all_verdicts": ["REJECT", "PASS"]},
        {"ep_num": 4, "attempt_count": 1, "final_verdict": "PASS", "final_score": 92, "all_verdicts": ["PASS"]},
    ]

    result = _evaluate_stage3_canary_gates(
        target_ep=4,
        blueprint_db_count=4,
        blueprint_file_count=4,
        attempt_detail=detail,
        sink_alignment_summary={"status": "ok"},
    )
    assert result["status"] == "pass"
    assert result["errors"] == []


def test_stage3_canary_summary_gates_fail_on_missing_blueprints():
    from modules.core.stage4_canary_tools import _evaluate_stage3_canary_gates

    result = _evaluate_stage3_canary_gates(
        target_ep=4,
        blueprint_db_count=2,
        blueprint_file_count=2,
        attempt_detail=[
            {"ep_num": 1, "attempt_count": 1, "final_verdict": "PASS", "final_score": 90, "all_verdicts": ["PASS"]},
            {"ep_num": 2, "attempt_count": 1, "final_verdict": "PASS", "final_score": 88, "all_verdicts": ["PASS"]},
        ],
        sink_alignment_summary={"status": "ok"},
    )
    assert result["status"] == "fail"
    assert any("blueprint_db_count_short" in e for e in result["errors"])


def test_stage3_canary_summary_gates_fail_on_rejected_episode():
    from modules.core.stage4_canary_tools import _evaluate_stage3_canary_gates

    detail = [
        {"ep_num": 1, "attempt_count": 1, "final_verdict": "PASS", "final_score": 90, "all_verdicts": ["PASS"]},
        {"ep_num": 2, "attempt_count": 3, "final_verdict": "REJECT", "final_score": 40, "all_verdicts": ["REJECT", "REJECT", "REJECT"]},
    ]
    result = _evaluate_stage3_canary_gates(
        target_ep=2,
        blueprint_db_count=1,
        blueprint_file_count=1,
        attempt_detail=detail,
        sink_alignment_summary={"status": "ok"},
    )
    assert result["status"] == "fail"
    assert any("ep2_final_verdict:REJECT" in e for e in result["errors"])


def test_stage3_attempt_detail_builder():
    from modules.core.stage4_canary_tools import _build_stage3_attempt_detail

    rows = [
        {"ep_num": 1, "attempt_num": 1, "verdict": "REJECT", "score": 40},
        {"ep_num": 1, "attempt_num": 2, "verdict": "PASS", "score": 85},
        {"ep_num": 2, "attempt_num": 1, "verdict": "PASS", "score": 90},
    ]
    detail = _build_stage3_attempt_detail(rows)
    assert len(detail) == 2
    assert detail[0]["ep_num"] == 1
    assert detail[0]["attempt_count"] == 2
    assert detail[0]["final_verdict"] == "PASS"
    assert detail[0]["all_verdicts"] == ["REJECT", "PASS"]
    assert detail[1]["ep_num"] == 2
    assert detail[1]["attempt_count"] == 1


def test_parse_args_prepare():
    with patch("sys.argv", ["run_stage3_canary.py", "prepare", "--source-project", "src", "--target-project", "tgt"]):
        args = canary_script.parse_args()
    assert args.command == "prepare"
    assert args.source_project == "src"
    assert args.target_project == "tgt"
    assert args.from_ep == 1
    assert not args.force


def test_parse_args_full():
    with patch("sys.argv", [
        "run_stage3_canary.py", "full",
        "--source-project", "src",
        "--target-project", "tgt",
        "--target-ep", "8",
        "--force",
    ]):
        args = canary_script.parse_args()
    assert args.command == "full"
    assert args.target_ep == 8
    assert args.force
