from types import SimpleNamespace
from unittest.mock import MagicMock

from main_a import SovereignApp


def _make_app(*, arcs, bp_max: int, next_ep: int):
    app = SovereignApp.__new__(SovereignApp)
    db = SimpleNamespace(
        load_anchor=MagicMock(return_value=arcs),
        get_latest_blueprint_number=MagicMock(return_value=bp_max),
    )
    app.current_project = SimpleNamespace(
        db=db,
        get_latest_episode_number=MagicMock(return_value=next_ep),
    )
    return app


def test_compute_frontier_targets_non_final_frontier_uses_minus_one_minus_two():
    app = SovereignApp.__new__(SovereignApp)

    plan = app._compute_frontier_targets(
        ep_start=11,
        ep_end=13,
        designed_frontier_arc_no=3,
        true_final_arc_no=10,
    )

    assert plan["is_true_final_frontier"] is False
    assert plan["stage3_target"] == 12
    assert plan["stage4_target"] == 11


def test_compute_frontier_targets_true_final_frontier_full_closes():
    app = SovereignApp.__new__(SovereignApp)

    plan = app._compute_frontier_targets(
        ep_start=14,
        ep_end=16,
        designed_frontier_arc_no=4,
        true_final_arc_no=4,
    )

    assert plan["is_true_final_frontier"] is True
    assert plan["stage3_target"] == 16
    assert plan["stage4_target"] == 16


def test_resolve_one_stop_frontier_lag_plan_reports_aligned_non_final_frontier():
    app = _make_app(
        arcs=[
            {"ep_start": 1, "ep_end": 4},
            {"ep_start": 5, "ep_end": 10},
            {"ep_start": 11, "ep_end": 13},
        ],
        bp_max=12,
        next_ep=12,  # manuscripts written through ep 11
    )

    plan = app._resolve_one_stop_frontier_lag_plan(total_arcs=10)

    assert plan["designed_frontier_arc_no"] == 3
    assert plan["true_final_arc_no"] == 10
    assert plan["stage3_target"] == 12
    assert plan["stage4_target"] == 11
    assert plan["bp_max"] == 12
    assert plan["ms_max"] == 11
    assert plan["stage3_alignment"] == "aligned"
    assert plan["stage4_alignment"] == "aligned"


def test_resolve_one_stop_frontier_lag_plan_reports_backlog_for_true_final_frontier():
    app = _make_app(
        arcs=[
            {"ep_start": 1, "ep_end": 4},
            {"ep_start": 5, "ep_end": 8},
            {"ep_start": 9, "ep_end": 13},
            {"ep_start": 14, "ep_end": 16},
        ],
        bp_max=15,
        next_ep=15,  # manuscripts written through ep 14
    )

    plan = app._resolve_one_stop_frontier_lag_plan(total_arcs=4)

    assert plan["is_true_final_frontier"] is True
    assert plan["stage3_target"] == 16
    assert plan["stage4_target"] == 16
    assert plan["stage3_alignment"] == "backlog"
    assert plan["stage4_alignment"] == "backlog"


def test_resolve_one_stop_frontier_lag_plan_reports_ahead_when_old_full_close_exists():
    app = _make_app(
        arcs=[
            {"ep_start": 1, "ep_end": 4},
            {"ep_start": 5, "ep_end": 10},
            {"ep_start": 11, "ep_end": 13},
        ],
        bp_max=13,
        next_ep=14,  # manuscripts written through ep 13
    )

    plan = app._resolve_one_stop_frontier_lag_plan(total_arcs=10)

    assert plan["stage3_target"] == 12
    assert plan["stage4_target"] == 11
    assert plan["stage3_alignment"] == "ahead"
    assert plan["stage4_alignment"] == "ahead"


def test_resolve_one_stop_frontier_lag_plan_returns_none_without_designed_arcs():
    app = _make_app(arcs=[], bp_max=0, next_ep=1)

    assert app._resolve_one_stop_frontier_lag_plan(total_arcs=5) is None
