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


def _build_one_stop_app(
    *,
    total_arcs: int,
    stage3_results,
    manuscripts_after,
    initial_designed_arcs: int = 0,
):
    app = SovereignApp.__new__(SovereignApp)
    arc_specs = [{"ep_start": i * 3 + 1, "ep_end": i * 3 + 3} for i in range(total_arcs)]
    arcs = []
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
        if key == "bible":
            return {
                "MasterBible": {
                    "plot_roadmap": [
                        {"block_no": i + 1, "title": f"Arc {i + 1}", "key_events": [f"event_{i + 1}"]}
                        for i in range(total_arcs)
                    ]
                }
            }
        raise AssertionError(f"unexpected anchor key: {key}")

    db = SimpleNamespace(load_anchor=MagicMock(side_effect=_load_anchor))
    app.current_project = SimpleNamespace(
        master_bible={
            "MasterBible": {
                "plot_roadmap": [
                    {"block_no": i + 1, "title": f"Arc {i + 1}", "key_events": [f"event_{i + 1}"]}
                    for i in range(total_arcs)
                ]
            }
        },
        db=db,
        get_latest_episode_number=MagicMock(return_value=1),
    )
    app.ui = SimpleNamespace(log=MagicMock())
    app._ui_service = SimpleNamespace(
        get_choice_input=MagicMock(return_value="2"),
        pause=MagicMock(),
    )
    app._show_resume_status = MagicMock()
    app._get_int_input = MagicMock(return_value=1)
    app._pause = MagicMock()
    app._get_max_episode_from_manuscripts = MagicMock(side_effect=manuscripts_after)
    app._stage2_orch = SimpleNamespace(ctx=None, stage_2_arcs_async_logic=_stage2_async_logic)
    app._stage3_orch = SimpleNamespace(
        ctx=None,
        stage_3_batch_blueprinting=MagicMock(side_effect=stage3_results),
    )
    app._stage_4_v2_chief_writer = MagicMock()
    app.state_tracker = None
    app._state_tracker_loaded_arcs = 0
    return app


def _run_one_stop_arc_step(app, *, current_arc_no: int = 1, total_arcs: int = 2):
    fake_stage2 = _make_stage_context_module("Stage2Context")
    fake_stage3 = _make_stage_context_module("Stage3Context")
    with patch.dict(
        sys.modules,
        {"modules.core.stage2_context": fake_stage2, "modules.core.stage3_context": fake_stage3},
    ):
        return SovereignApp._run_one_stop_arc_step(app, current_arc_no=current_arc_no, total_arcs=total_arcs)


def test_run_one_stop_arc_step_returns_continue_on_stage3_skip():
    app = _build_one_stop_app(
        total_arcs=2,
        stage3_results=[{"success_count": 0, "fail_count": 1}],
        manuscripts_after=[0, 0],
    )
    app._ui_service.get_choice_input.return_value = "1"

    result = _run_one_stop_arc_step(app)

    app._stage_4_v2_chief_writer.assert_not_called()
    assert result == {
        "status": "continue",
        "arcs_completed_delta": 1,
        "manuscripts_delta": 0,
    }


def test_run_one_stop_arc_step_returns_completed_when_stage4_reaches_arc_target():
    app = _build_one_stop_app(
        total_arcs=2,
        stage3_results=[{"success_count": 3, "fail_count": 0}],
        manuscripts_after=[0, 3],
    )

    result = _run_one_stop_arc_step(app)

    app._stage_4_v2_chief_writer.assert_called_once_with(target_ep=3, skip_pause=True)
    assert result == {
        "status": "completed",
        "arcs_completed_delta": 1,
        "manuscripts_delta": 3,
    }


def test_run_one_stop_arc_step_returns_incomplete_when_stage4_does_not_reach_arc_target():
    app = _build_one_stop_app(
        total_arcs=2,
        stage3_results=[{"success_count": 3, "fail_count": 0}],
        manuscripts_after=[0, 2],
    )

    result = _run_one_stop_arc_step(app)

    assert result == {
        "status": "stage4_incomplete",
        "arcs_completed_delta": 0,
        "manuscripts_delta": 2,
    }


def test_run_one_stop_arc_step_returns_error_when_stage4_raises():
    app = _build_one_stop_app(
        total_arcs=2,
        stage3_results=[{"success_count": 3, "fail_count": 0}],
        manuscripts_after=[0, 1],
    )
    app._stage_4_v2_chief_writer.side_effect = RuntimeError("stage4 boom")

    result = _run_one_stop_arc_step(app)

    assert result == {
        "status": "stage4_error",
        "arcs_completed_delta": 0,
        "manuscripts_delta": 1,
    }


def test_run_one_stop_arc_step_allows_zero_delta_when_arc_already_written():
    app = _build_one_stop_app(
        total_arcs=2,
        stage3_results=[{"success_count": 0, "fail_count": 0}],
        manuscripts_after=[3, 3],
        initial_designed_arcs=1,
    )

    result = _run_one_stop_arc_step(app)

    assert result == {
        "status": "completed",
        "arcs_completed_delta": 1,
        "manuscripts_delta": 0,
    }


def test_prepare_one_stop_batch_request_uses_default_when_input_missing():
    app = _build_one_stop_app(
        total_arcs=4,
        stage3_results=[],
        manuscripts_after=[0],
    )
    app._get_int_input.return_value = None

    result = SovereignApp._prepare_one_stop_batch_request(
        app,
        fully_done_arcs=1,
        total_arcs=4,
        designed_arcs=3,
        remaining=3,
    )

    assert result == 3
    app._get_int_input.assert_called_once_with(
        "👉 몇 개 Arc를 처리할까요? (1~3, 기본: 3): ",
        default=3,
        min_val=1,
        max_val=3,
    )


def test_resolve_one_stop_continue_request_returns_none_on_user_stop():
    app = _build_one_stop_app(
        total_arcs=4,
        stage3_results=[],
        manuscripts_after=[0],
    )
    app._ui_service.get_choice_input.return_value = "2"

    result = SovereignApp._resolve_one_stop_continue_request(app, remaining=2)

    assert result is None
    app._get_int_input.assert_not_called()


def test_finalize_one_stop_result_logs_summary_and_pauses():
    app = _build_one_stop_app(
        total_arcs=3,
        stage3_results=[],
        manuscripts_after=[0],
        initial_designed_arcs=2,
    )

    SovereignApp._finalize_one_stop_result(
        app,
        total_arcs=3,
        fully_done_arcs=1,
        arcs_completed=1,
        total_manuscripts=4,
    )

    app._pause.assert_called_once_with("[Enter] 메뉴로 돌아가기", prompt_id="one_stop_return_to_menu")
    logged_messages = [str(call.args[0]) for call in app.ui.log.call_args_list]
    assert any("Arc 처리: 1개 (Arc 2~2)" in message for message in logged_messages)
    assert any("생산 원고: 약 4화" in message for message in logged_messages)
