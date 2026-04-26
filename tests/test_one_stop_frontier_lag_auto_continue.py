import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch

from main_a import SovereignApp


def _make_stage_context_module(class_name: str):
    mod = ModuleType(f"fake_{class_name.lower()}")

    class _Ctx:
        @staticmethod
        def from_app(app):
            return SimpleNamespace(app=app)

    setattr(mod, class_name, _Ctx)
    return mod


def _build_frontier_app(
    *,
    total_arcs: int,
    batch_size: int,
    stage3_results,
    plans,
    manuscripts_after,
    initial_designed_arcs: int = 0,
):
    app = SovereignApp.__new__(SovereignApp)
    arcs = []
    arc_specs = [{"ep_start": i * 3 + 1, "ep_end": i * 3 + 3} for i in range(total_arcs)]
    for idx in range(min(initial_designed_arcs, len(arc_specs))):
        next_arc = dict(arc_specs[idx])
        next_arc["arc_no"] = idx + 1
        arcs.append(next_arc)

    async def _stage2_async_logic(target_arc_count=1):
        if len(arcs) < len(arc_specs):
            next_arc = dict(arc_specs[len(arcs)])
            next_arc["arc_no"] = len(arcs) + 1
            arcs.append(next_arc)

    def _load_anchor(key):
        if key == "arcs":
            return arcs
        raise AssertionError(f"unexpected anchor key: {key}")

    db = SimpleNamespace(load_anchor=MagicMock(side_effect=_load_anchor))
    app.current_project = SimpleNamespace(
        master_bible={
            "MasterBible": {
                "plot_roadmap": [
                    {
                        "block_no": i + 1,
                        "title": f"Arc {i + 1}",
                        "key_events": [f"event_{i + 1}"],
                    }
                    for i in range(total_arcs)
                ]
            }
        },
        db=db,
    )
    app.ui = SimpleNamespace(log=MagicMock())
    app._ui_service = SimpleNamespace(
        get_choice_input=MagicMock(return_value="2"),
        confirm=MagicMock(return_value=False),
        pause=MagicMock(),
    )
    app._show_resume_status = MagicMock()
    app._get_int_input = MagicMock(return_value=batch_size)
    app._get_max_episode_from_manuscripts = MagicMock(side_effect=manuscripts_after)
    plan_calls = {"idx": 0}

    def _resolve_plan(*, total_arcs, designed_arcs):
        idx = plan_calls["idx"]
        if idx < len(plans):
            plan_calls["idx"] += 1
            return plans[idx]
        return plans[-1]

    app._resolve_one_stop_frontier_lag_plan = MagicMock(side_effect=_resolve_plan)
    app._stage2_orch = SimpleNamespace(ctx=None, stage_2_arcs_async_logic=_stage2_async_logic)
    app._stage3_orch = SimpleNamespace(
        ctx=None,
        stage_3_batch_blueprinting=MagicMock(side_effect=stage3_results),
    )
    app._stage_4_v2_chief_writer = MagicMock()
    app.state_tracker = None
    app._state_tracker_loaded_arcs = 0
    return app


def test_frontier_lag_uses_default_batch_without_boundary_input():
    app = _build_frontier_app(
        total_arcs=2,
        batch_size=2,
        stage3_results=[
            {"success_count": 1, "fail_count": 0},
            {"success_count": 1, "fail_count": 0},
        ],
        plans=[
            {
                "true_final_arc_no": 2,
                "designed_frontier_arc_no": 1,
                "frontier_ep_start": 1,
                "frontier_ep_end": 3,
                "stage3_target": 2,
                "stage4_target": 1,
                "stage3_alignment": "aligned",
                "stage4_alignment": "aligned",
                "bp_max": 2,
                "ms_max": 1,
            },
            {
                "true_final_arc_no": 2,
                "designed_frontier_arc_no": 2,
                "frontier_ep_start": 4,
                "frontier_ep_end": 6,
                "stage3_target": 6,
                "stage4_target": 6,
                "stage3_alignment": "aligned",
                "stage4_alignment": "aligned",
                "bp_max": 6,
                "ms_max": 6,
            },
        ],
        manuscripts_after=[0, 1, 1, 6],
    )

    fake_stage2 = _make_stage_context_module("Stage2Context")
    fake_stage3 = _make_stage_context_module("Stage3Context")

    with patch.dict(
        sys.modules,
        {"modules.core.stage2_context": fake_stage2, "modules.core.stage3_context": fake_stage3},
    ):

        def _input_side_effect(prompt=""):
            if prompt == "[Enter] 메뉴로 돌아가기":
                return ""
            raise AssertionError(f"unexpected input prompt: {prompt}")

        with patch("builtins.input", side_effect=_input_side_effect):
            result = SovereignApp._one_stop_pipeline_frontier_lag(app)

    app._get_int_input.assert_called_once_with(
        "👉 이번 실행에서 몇 개 Arc를 처리할까요? (1~2, 기본: 2): ",
        default=2,
        min_val=1,
        max_val=2,
    )
    assert app._stage3_orch.stage_3_batch_blueprinting.call_count == 2
    assert app._stage_4_v2_chief_writer.call_count == 2
    assert all(call.kwargs.get("skip_pause") is True for call in app._stage_4_v2_chief_writer.call_args_list)
    assert result["requested_arc_limit"] == 2
    assert result["requested_limit_hit"] is True
    default_batch_logs = [
        call.args[0] for call in app.ui.log.call_args_list if "auto-selected default batch_size" in str(call.args[0])
    ]
    assert len(default_batch_logs) == 1
    assert "auto-selected default batch_size: 2" in default_batch_logs[0]
    auto_continue_logs = [
        call.args[0] for call in app.ui.log.call_args_list if "승인 없이 자동 계속" in str(call.args[0])
    ]
    assert auto_continue_logs == []


def test_frontier_lag_auto_shrinks_last_tranche_to_remaining():
    app = _build_frontier_app(
        total_arcs=4,
        batch_size=4,
        stage3_results=[
            {"success_count": 1, "fail_count": 0},
            {"success_count": 1, "fail_count": 0},
            {"success_count": 1, "fail_count": 0},
            {"success_count": 1, "fail_count": 0},
        ],
        plans=[
            {
                "true_final_arc_no": 4,
                "designed_frontier_arc_no": 1,
                "frontier_ep_start": 1,
                "frontier_ep_end": 3,
                "stage3_target": 2,
                "stage4_target": 1,
                "stage3_alignment": "aligned",
                "stage4_alignment": "aligned",
                "bp_max": 2,
                "ms_max": 1,
            },
            {
                "true_final_arc_no": 4,
                "designed_frontier_arc_no": 2,
                "frontier_ep_start": 4,
                "frontier_ep_end": 6,
                "stage3_target": 5,
                "stage4_target": 4,
                "stage3_alignment": "aligned",
                "stage4_alignment": "aligned",
                "bp_max": 5,
                "ms_max": 4,
            },
            {
                "true_final_arc_no": 4,
                "designed_frontier_arc_no": 3,
                "frontier_ep_start": 7,
                "frontier_ep_end": 9,
                "stage3_target": 8,
                "stage4_target": 7,
                "stage3_alignment": "aligned",
                "stage4_alignment": "aligned",
                "bp_max": 8,
                "ms_max": 7,
            },
            {
                "true_final_arc_no": 4,
                "designed_frontier_arc_no": 4,
                "frontier_ep_start": 10,
                "frontier_ep_end": 12,
                "stage3_target": 12,
                "stage4_target": 12,
                "stage3_alignment": "aligned",
                "stage4_alignment": "aligned",
                "bp_max": 12,
                "ms_max": 12,
            },
        ],
        manuscripts_after=[0, 1, 1, 4, 4, 7, 7, 12],
    )

    fake_stage2 = _make_stage_context_module("Stage2Context")
    fake_stage3 = _make_stage_context_module("Stage3Context")

    with patch.dict(
        sys.modules,
        {"modules.core.stage2_context": fake_stage2, "modules.core.stage3_context": fake_stage3},
    ):

        def _input_side_effect(prompt=""):
            if prompt == "[Enter] 메뉴로 돌아가기":
                return ""
            raise AssertionError(f"unexpected input prompt: {prompt}")

        with patch("builtins.input", side_effect=_input_side_effect):
            result = SovereignApp._one_stop_pipeline_frontier_lag(app)

    app._get_int_input.assert_called_once_with(
        "👉 이번 실행에서 몇 개 Arc를 처리할까요? (1~4, 기본: 3): ",
        default=3,
        min_val=1,
        max_val=4,
    )
    assert app._stage3_orch.stage_3_batch_blueprinting.call_count == 4
    assert result["requested_arc_limit"] == 4
    assert result["requested_limit_hit"] is True
    default_batch_logs = [
        call.args[0] for call in app.ui.log.call_args_list if "auto-selected default batch_size" in str(call.args[0])
    ]
    assert len(default_batch_logs) == 1
    assert "auto-selected default batch_size: 3" in default_batch_logs[0]
    auto_continue_logs = [
        call.args[0] for call in app.ui.log.call_args_list if "승인 없이 자동 계속" in str(call.args[0])
    ]
    assert len(auto_continue_logs) == 1
    assert "다음 tranche: 1개" in auto_continue_logs[0]


def test_frontier_lag_interactive_requested_arc_limit_stops_at_requested_total():
    app = _build_frontier_app(
        total_arcs=4,
        batch_size=2,
        stage3_results=[
            {"success_count": 1, "fail_count": 0},
            {"success_count": 1, "fail_count": 0},
            {"success_count": 1, "fail_count": 0},
        ],
        plans=[
            {
                "true_final_arc_no": 4,
                "designed_frontier_arc_no": 1,
                "frontier_ep_start": 1,
                "frontier_ep_end": 3,
                "stage3_target": 2,
                "stage4_target": 1,
                "stage3_alignment": "aligned",
                "stage4_alignment": "aligned",
                "bp_max": 2,
                "ms_max": 1,
            },
            {
                "true_final_arc_no": 4,
                "designed_frontier_arc_no": 2,
                "frontier_ep_start": 4,
                "frontier_ep_end": 6,
                "stage3_target": 5,
                "stage4_target": 4,
                "stage3_alignment": "aligned",
                "stage4_alignment": "aligned",
                "bp_max": 5,
                "ms_max": 4,
            },
            {
                "true_final_arc_no": 4,
                "designed_frontier_arc_no": 3,
                "frontier_ep_start": 7,
                "frontier_ep_end": 9,
                "stage3_target": 8,
                "stage4_target": 7,
                "stage3_alignment": "aligned",
                "stage4_alignment": "aligned",
                "bp_max": 8,
                "ms_max": 7,
            },
        ],
        manuscripts_after=[0, 1, 1, 4, 4, 7],
    )

    fake_stage2 = _make_stage_context_module("Stage2Context")
    fake_stage3 = _make_stage_context_module("Stage3Context")

    with patch.dict(
        sys.modules,
        {"modules.core.stage2_context": fake_stage2, "modules.core.stage3_context": fake_stage3},
    ):

        def _input_side_effect(prompt=""):
            if prompt == "[Enter] 메뉴로 돌아가기":
                return ""
            raise AssertionError(f"unexpected input prompt: {prompt}")

        with patch("builtins.input", side_effect=_input_side_effect):
            result = SovereignApp._one_stop_pipeline_frontier_lag(app)

    app._get_int_input.assert_called_once_with(
        "👉 이번 실행에서 몇 개 Arc를 처리할까요? (1~4, 기본: 3): ",
        default=3,
        min_val=1,
        max_val=4,
    )
    assert app._stage3_orch.stage_3_batch_blueprinting.call_count == 2
    assert app._stage_4_v2_chief_writer.call_count == 2
    assert result["arcs_advanced"] == 2
    assert result["requested_arc_limit"] == 2
    assert result["requested_limit_hit"] is True
    auto_continue_logs = [
        call.args[0] for call in app.ui.log.call_args_list if "승인 없이 자동 계속" in str(call.args[0])
    ]
    assert auto_continue_logs == []
    limit_logs = [call.args[0] for call in app.ui.log.call_args_list if "요청된 Arc 경계 도달" in str(call.args[0])]
    assert len(limit_logs) == 1


def test_frontier_lag_final_close_propagates_skip_pause():
    app = _build_frontier_app(
        total_arcs=2,
        batch_size=1,
        stage3_results=[{"success_count": 1, "fail_count": 0}],
        plans=[
            {
                "true_final_arc_no": 2,
                "designed_frontier_arc_no": 2,
                "frontier_ep_start": 4,
                "frontier_ep_end": 6,
                "stage3_target": 6,
                "stage4_target": 6,
                "stage3_alignment": "aligned",
                "stage4_alignment": "aligned",
                "bp_max": 6,
                "ms_max": 2,
            }
        ],
        manuscripts_after=[2, 4],
        initial_designed_arcs=2,
    )

    fake_stage3 = _make_stage_context_module("Stage3Context")

    with patch.dict(sys.modules, {"modules.core.stage3_context": fake_stage3}):
        with patch("builtins.input") as mocked_input:
            result = SovereignApp._one_stop_pipeline_frontier_lag(app, wait_for_menu_return=False)

    app._get_int_input.assert_not_called()
    app._stage3_orch.stage_3_batch_blueprinting.assert_called_once_with(target_ep=6)
    app._stage_4_v2_chief_writer.assert_called_once_with(target_ep=6, skip_pause=True)
    mocked_input.assert_not_called()
    assert result["arcs_advanced"] == 0
    assert result["total_manuscripts"] == 2
    assert result["stop_reason"] == "completed"


def test_frontier_lag_final_close_helper_returns_payload():
    app = _build_frontier_app(
        total_arcs=2,
        batch_size=1,
        stage3_results=[{"success_count": 1, "fail_count": 0}],
        plans=[
            {
                "true_final_arc_no": 2,
                "designed_frontier_arc_no": 2,
                "frontier_ep_start": 4,
                "frontier_ep_end": 6,
                "stage3_target": 6,
                "stage4_target": 6,
                "stage3_alignment": "aligned",
                "stage4_alignment": "aligned",
                "bp_max": 6,
                "ms_max": 2,
            }
        ],
        manuscripts_after=[2, 4],
        initial_designed_arcs=2,
    )

    fake_stage3 = _make_stage_context_module("Stage3Context")

    with patch.dict(sys.modules, {"modules.core.stage3_context": fake_stage3}):
        result = SovereignApp._run_frontier_lag_final_close(
            app,
            total_arcs=2,
            all_arcs=app.current_project.db.load_anchor("arcs"),
        )

    app._stage3_orch.stage_3_batch_blueprinting.assert_called_once_with(target_ep=6)
    app._stage_4_v2_chief_writer.assert_called_once_with(target_ep=6, skip_pause=True)
    assert result == {
        "manuscripts_delta": 2,
        "stop_reason": None,
        "final_plan": {
            "true_final_arc_no": 2,
            "designed_frontier_arc_no": 2,
            "frontier_ep_start": 4,
            "frontier_ep_end": 6,
            "stage3_target": 6,
            "stage4_target": 6,
            "stage3_alignment": "aligned",
            "stage4_alignment": "aligned",
            "bp_max": 6,
            "ms_max": 2,
        },
    }


def test_prepare_frontier_lag_batch_request_respects_override_and_requested_limit():
    app = _build_frontier_app(
        total_arcs=4,
        batch_size=1,
        stage3_results=[],
        plans=[
            {
                "true_final_arc_no": 4,
                "designed_frontier_arc_no": 1,
                "frontier_ep_start": 1,
                "frontier_ep_end": 3,
                "stage3_target": 2,
                "stage4_target": 1,
                "stage3_alignment": "aligned",
                "stage4_alignment": "aligned",
                "bp_max": 2,
                "ms_max": 1,
            }
        ],
        manuscripts_after=[0],
        initial_designed_arcs=1,
    )

    result = SovereignApp._prepare_frontier_lag_batch_request(
        app,
        total_arcs=4,
        all_arcs=app.current_project.db.load_anchor("arcs"),
        max_arc_advances=2,
        batch_size_override=3,
    )

    app._get_int_input.assert_not_called()
    assert result == {
        "designed_arcs": 1,
        "remaining_design": 3,
        "requested_arc_limit": 2,
        "requested_limit_hit": False,
        "stop_reason": "completed",
        "batch_size": 3,
        "target_count": 2,
    }


def test_frontier_lag_final_close_blocks_when_stage4_backlog_makes_no_progress():
    app = _build_frontier_app(
        total_arcs=2,
        batch_size=1,
        stage3_results=[{"success_count": 1, "fail_count": 0}],
        plans=[
            {
                "true_final_arc_no": 2,
                "designed_frontier_arc_no": 2,
                "frontier_ep_start": 4,
                "frontier_ep_end": 6,
                "stage3_target": 6,
                "stage4_target": 6,
                "stage3_alignment": "aligned",
                "stage4_alignment": "backlog",
                "bp_max": 6,
                "ms_max": 2,
            }
        ],
        manuscripts_after=[2, 2],
        initial_designed_arcs=2,
    )

    fake_stage3 = _make_stage_context_module("Stage3Context")

    with patch.dict(sys.modules, {"modules.core.stage3_context": fake_stage3}):
        with patch("builtins.input") as mocked_input:
            result = SovereignApp._one_stop_pipeline_frontier_lag(app, wait_for_menu_return=False)

    app._get_int_input.assert_not_called()
    app._stage3_orch.stage_3_batch_blueprinting.assert_called_once_with(target_ep=6)
    app._stage_4_v2_chief_writer.assert_called_once_with(target_ep=6, skip_pause=True)
    mocked_input.assert_not_called()
    assert result["arcs_advanced"] == 0
    assert result["total_manuscripts"] == 0
    assert result["stop_reason"] == "stage4_final_close_no_progress"


def test_finalize_frontier_lag_result_returns_payload_without_pause():
    app = _build_frontier_app(
        total_arcs=2,
        batch_size=1,
        stage3_results=[],
        plans=[
            {
                "true_final_arc_no": 2,
                "designed_frontier_arc_no": 2,
                "frontier_ep_start": 4,
                "frontier_ep_end": 6,
                "stage3_target": 6,
                "stage4_target": 6,
                "stage3_alignment": "aligned",
                "stage4_alignment": "aligned",
                "bp_max": 6,
                "ms_max": 2,
            }
        ],
        manuscripts_after=[0],
        initial_designed_arcs=2,
    )
    app._pause = MagicMock()

    result = SovereignApp._finalize_frontier_lag_result(
        app,
        total_arcs=2,
        arcs_advanced=1,
        arcs_skipped=0,
        total_manuscripts=3,
        requested_arc_limit=2,
        requested_limit_hit=False,
        stop_reason="completed",
        wait_for_menu_return=False,
    )

    app._pause.assert_not_called()
    assert result == {
        "arcs_advanced": 1,
        "arcs_skipped": 0,
        "arc_units_processed": 1,
        "total_manuscripts": 3,
        "requested_arc_limit": 2,
        "requested_limit_hit": False,
        "stop_reason": "completed",
        "final_plan": {
            "true_final_arc_no": 2,
            "designed_frontier_arc_no": 2,
            "frontier_ep_start": 4,
            "frontier_ep_end": 6,
            "stage3_target": 6,
            "stage4_target": 6,
            "stage3_alignment": "aligned",
            "stage4_alignment": "aligned",
            "bp_max": 6,
            "ms_max": 2,
        },
    }


def test_frontier_lag_arc_step_helper_returns_continue_on_stage3_skip():
    app = _build_frontier_app(
        total_arcs=2,
        batch_size=1,
        stage3_results=[{"success_count": 0, "fail_count": 1}],
        plans=[
            {
                "true_final_arc_no": 2,
                "designed_frontier_arc_no": 1,
                "frontier_ep_start": 1,
                "frontier_ep_end": 3,
                "stage3_target": 2,
                "stage4_target": 1,
                "stage3_alignment": "backlog",
                "stage4_alignment": "backlog",
                "bp_max": 0,
                "ms_max": 0,
            }
        ],
        manuscripts_after=[0, 0],
    )
    app._ui_service.get_choice_input.return_value = "1"

    fake_stage2 = _make_stage_context_module("Stage2Context")
    fake_stage3 = _make_stage_context_module("Stage3Context")

    with patch.dict(
        sys.modules,
        {"modules.core.stage2_context": fake_stage2, "modules.core.stage3_context": fake_stage3},
    ):
        result = SovereignApp._run_frontier_lag_arc_step(
            app,
            current_arc_no=1,
            total_arcs=2,
            stage3_failure_policy="skip",
        )

    app._stage_4_v2_chief_writer.assert_not_called()
    assert result == {
        "arcs_advanced_delta": 0,
        "arcs_skipped_delta": 1,
        "manuscripts_delta": 0,
        "status": "continue",
        "stop_reason": None,
        "stage3_failure_policy": "skip",
        "skip_reason": "stage3_generation_failed",
    }


def test_ensure_frontier_lag_arc_ready_stops_when_stage2_does_not_create_arc():
    app = _build_frontier_app(
        total_arcs=2,
        batch_size=1,
        stage3_results=[{"success_count": 1, "fail_count": 0}],
        plans=[],
        manuscripts_after=[0, 0],
    )

    async def _no_stage2_generation(target_arc_count=1):
        return None

    app._stage2_orch = SimpleNamespace(ctx=None, stage_2_arcs_async_logic=_no_stage2_generation)
    fake_stage2 = _make_stage_context_module("Stage2Context")

    with patch.dict(sys.modules, {"modules.core.stage2_context": fake_stage2}):
        result = SovereignApp._ensure_frontier_lag_arc_ready(app, current_arc_no=1)

    assert result == {
        "status": "stop",
        "payload": {
            "arcs_advanced_delta": 0,
            "manuscripts_delta": 0,
            "status": "stop",
            "stop_reason": "stage2_arc_missing_after_generation",
        },
    }


def test_run_frontier_lag_stage4_sync_blocks_when_backlog_has_no_progress():
    app = _build_frontier_app(
        total_arcs=2,
        batch_size=1,
        stage3_results=[{"success_count": 1, "fail_count": 0}],
        plans=[],
        manuscripts_after=[0, 0],
    )

    result = SovereignApp._run_frontier_lag_stage4_sync(
        app,
        frontier_plan={
            "stage4_target": 1,
            "stage4_alignment": "backlog",
        },
    )

    app._stage_4_v2_chief_writer.assert_called_once_with(target_ep=1, skip_pause=True)
    assert result == {
        "arcs_advanced_delta": 0,
        "manuscripts_delta": 0,
        "status": "stop",
        "stop_reason": "stage4_no_progress_blocked",
    }


def test_run_frontier_lag_stage4_sync_blocks_when_partial_progress_misses_target():
    app = _build_frontier_app(
        total_arcs=2,
        batch_size=1,
        stage3_results=[{"success_count": 1, "fail_count": 0}],
        plans=[],
        manuscripts_after=[1, 3],
    )

    result = SovereignApp._run_frontier_lag_stage4_sync(
        app,
        frontier_plan={
            "stage4_target": 4,
            "stage4_alignment": "backlog",
        },
    )

    app._stage_4_v2_chief_writer.assert_called_once_with(target_ep=4, skip_pause=True)
    assert result == {
        "arcs_advanced_delta": 0,
        "manuscripts_delta": 2,
        "status": "stop",
        "stop_reason": "stage4_target_not_reached",
    }


def test_frontier_lag_keeps_stage3_abort_prompt():
    app = _build_frontier_app(
        total_arcs=2,
        batch_size=1,
        stage3_results=[{"success_count": 0, "fail_count": 1}],
        plans=[
            {
                "true_final_arc_no": 2,
                "designed_frontier_arc_no": 1,
                "frontier_ep_start": 1,
                "frontier_ep_end": 3,
                "stage3_target": 2,
                "stage4_target": 1,
                "stage3_alignment": "backlog",
                "stage4_alignment": "backlog",
                "bp_max": 0,
                "ms_max": 0,
            }
        ],
        manuscripts_after=[0, 0],
    )

    fake_stage2 = _make_stage_context_module("Stage2Context")
    fake_stage3 = _make_stage_context_module("Stage3Context")

    with patch.dict(
        sys.modules,
        {"modules.core.stage2_context": fake_stage2, "modules.core.stage3_context": fake_stage3},
    ):
        with patch("builtins.input", return_value="2") as mocked_input:
            result = SovereignApp._one_stop_pipeline_frontier_lag(app, stage3_failure_policy="operator_prompt")

    app._get_int_input.assert_called_once_with(
        "👉 이번 실행에서 몇 개 Arc를 처리할까요? (1~2, 기본: 2): ",
        default=2,
        min_val=1,
        max_val=2,
    )
    mocked_input.assert_not_called()
    app._ui_service.get_choice_input.assert_called_once()
    assert "건너뛰고 다음 Arc로?" in app._ui_service.get_choice_input.call_args.args[0]
    app._ui_service.pause.assert_called_once_with("[Enter] 메뉴로 돌아가기", prompt_id="frontier_lag_return_to_menu")
    app._stage_4_v2_chief_writer.assert_not_called()
    assert result["stop_reason"] == "stage3_user_abort"


def test_frontier_lag_stage3_failure_defaults_to_strict_stop():
    app = _build_frontier_app(
        total_arcs=2,
        batch_size=1,
        stage3_results=[{"success_count": 0, "fail_count": 1}],
        plans=[
            {
                "true_final_arc_no": 2,
                "designed_frontier_arc_no": 1,
                "frontier_ep_start": 1,
                "frontier_ep_end": 3,
                "stage3_target": 2,
                "stage4_target": 1,
                "stage3_alignment": "backlog",
                "stage4_alignment": "backlog",
                "bp_max": 0,
                "ms_max": 0,
            }
        ],
        manuscripts_after=[0, 0],
    )

    fake_stage2 = _make_stage_context_module("Stage2Context")
    fake_stage3 = _make_stage_context_module("Stage3Context")

    with patch.dict(
        sys.modules,
        {"modules.core.stage2_context": fake_stage2, "modules.core.stage3_context": fake_stage3},
    ):
        with patch("builtins.input") as mocked_input:
            result = SovereignApp._one_stop_pipeline_frontier_lag(app, wait_for_menu_return=False)

    mocked_input.assert_not_called()
    app._ui_service.get_choice_input.assert_not_called()
    app._stage_4_v2_chief_writer.assert_not_called()
    assert result["arcs_advanced"] == 0
    assert result["arcs_skipped"] == 0
    assert result["stop_reason"] == "stage3_strict_failure_stop"


def test_frontier_lag_blocks_arc_advance_when_stage4_backlog_makes_no_progress():
    app = _build_frontier_app(
        total_arcs=2,
        batch_size=1,
        stage3_results=[{"success_count": 1, "fail_count": 0}],
        plans=[
            {
                "true_final_arc_no": 2,
                "designed_frontier_arc_no": 1,
                "frontier_ep_start": 1,
                "frontier_ep_end": 3,
                "stage3_target": 2,
                "stage4_target": 1,
                "stage3_alignment": "backlog",
                "stage4_alignment": "backlog",
                "bp_max": 0,
                "ms_max": 0,
            }
        ],
        manuscripts_after=[0, 0],
    )

    fake_stage2 = _make_stage_context_module("Stage2Context")
    fake_stage3 = _make_stage_context_module("Stage3Context")

    with patch.dict(
        sys.modules,
        {"modules.core.stage2_context": fake_stage2, "modules.core.stage3_context": fake_stage3},
    ):
        with patch("builtins.input") as mocked_input:
            result = SovereignApp._one_stop_pipeline_frontier_lag(app, wait_for_menu_return=False)

    app._stage_4_v2_chief_writer.assert_called_once_with(target_ep=1, skip_pause=True)
    mocked_input.assert_not_called()
    assert result["arcs_advanced"] == 0
    assert result["total_manuscripts"] == 0
    assert result["stop_reason"] == "stage4_no_progress_blocked"


def test_frontier_lag_requested_arc_limit_stops_mid_auto_continue():
    app = _build_frontier_app(
        total_arcs=4,
        batch_size=3,
        stage3_results=[
            {"success_count": 1, "fail_count": 0},
            {"success_count": 1, "fail_count": 0},
            {"success_count": 1, "fail_count": 0},
            {"success_count": 1, "fail_count": 0},
        ],
        plans=[
            {
                "true_final_arc_no": 4,
                "designed_frontier_arc_no": 1,
                "frontier_ep_start": 1,
                "frontier_ep_end": 3,
                "stage3_target": 2,
                "stage4_target": 1,
                "stage3_alignment": "aligned",
                "stage4_alignment": "aligned",
                "bp_max": 2,
                "ms_max": 1,
            },
            {
                "true_final_arc_no": 4,
                "designed_frontier_arc_no": 2,
                "frontier_ep_start": 4,
                "frontier_ep_end": 6,
                "stage3_target": 5,
                "stage4_target": 4,
                "stage3_alignment": "aligned",
                "stage4_alignment": "aligned",
                "bp_max": 5,
                "ms_max": 4,
            },
            {
                "true_final_arc_no": 4,
                "designed_frontier_arc_no": 3,
                "frontier_ep_start": 7,
                "frontier_ep_end": 9,
                "stage3_target": 8,
                "stage4_target": 7,
                "stage3_alignment": "aligned",
                "stage4_alignment": "aligned",
                "bp_max": 8,
                "ms_max": 7,
            },
            {
                "true_final_arc_no": 4,
                "designed_frontier_arc_no": 4,
                "frontier_ep_start": 10,
                "frontier_ep_end": 12,
                "stage3_target": 12,
                "stage4_target": 12,
                "stage3_alignment": "aligned",
                "stage4_alignment": "aligned",
                "bp_max": 12,
                "ms_max": 12,
            },
        ],
        manuscripts_after=[0, 1, 1, 4, 4, 7, 7, 12],
    )

    fake_stage2 = _make_stage_context_module("Stage2Context")
    fake_stage3 = _make_stage_context_module("Stage3Context")

    with patch.dict(
        sys.modules,
        {"modules.core.stage2_context": fake_stage2, "modules.core.stage3_context": fake_stage3},
    ):
        with patch("builtins.input") as mocked_input:
            result = SovereignApp._one_stop_pipeline_frontier_lag(
                app,
                max_arc_advances=2,
                batch_size_override=3,
                wait_for_menu_return=False,
            )

    assert app._get_int_input.call_count == 0
    assert app._stage3_orch.stage_3_batch_blueprinting.call_count == 2
    assert app._stage_4_v2_chief_writer.call_count == 2
    mocked_input.assert_not_called()
    assert result["arcs_advanced"] == 2
    assert result["requested_limit_hit"] is True
    assert result["stop_reason"] == "requested_arc_limit_reached"
    limit_logs = [call.args[0] for call in app.ui.log.call_args_list if "요청된 Arc 경계 도달" in str(call.args[0])]
    assert len(limit_logs) == 1
