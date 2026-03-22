from unittest.mock import MagicMock, patch

from modules.core.stage01_helpers import Stage01Helpers


def _make_app():
    app = MagicMock()
    app.current_project.master_bible = {"MasterBible": {}}
    return app


def test_stage1_volumes_delegates_helper_family(monkeypatch):
    app = _make_app()
    helpers = Stage01Helpers(app=app)
    calls = []
    volume_inputs = {
        "bible_root": {"ProjectData": {}},
        "arcs_source": [{"arc": 1}, {"arc": 2}],
        "total_volumes": 2,
        "meta_info": "{}",
    }

    def fake_intro(self, app_arg):
        calls.append(("intro", app_arg))

    def fake_skip(self, app_arg):
        calls.append(("skip", app_arg))
        return False

    def fake_load(self, app_arg):
        calls.append(("load", app_arg))
        return volume_inputs

    def fake_plan(self, app_arg, *, bible_root, arcs_source, vol_idx, context_accumulator, meta_info):
        calls.append(("plan", vol_idx, context_accumulator, bible_root, tuple(arcs_source), meta_info))
        return "ok", {"volume": vol_idx}, f"ctx-{vol_idx}"

    def fake_finalize(self, app_arg, final_volumes):
        calls.append(("finalize", app_arg, final_volumes))

    monkeypatch.setattr(Stage01Helpers, "_log_stage1_volume_intro", fake_intro)
    monkeypatch.setattr(Stage01Helpers, "_should_skip_stage1_volumes", fake_skip)
    monkeypatch.setattr(Stage01Helpers, "_load_stage1_volume_inputs", fake_load)
    monkeypatch.setattr(Stage01Helpers, "_stage1_plan_single_volume", fake_plan)
    monkeypatch.setattr(Stage01Helpers, "_finalize_stage1_volumes", fake_finalize)

    helpers.stage_1_volumes()

    app._safe_commit.assert_called_once_with()
    assert calls == [
        ("intro", app),
        ("skip", app),
        ("load", app),
        ("plan", 1, "", {"ProjectData": {}}, ({"arc": 1}, {"arc": 2}), "{}"),
        ("plan", 2, "ctx-1", {"ProjectData": {}}, ({"arc": 1}, {"arc": 2}), "{}"),
        ("finalize", app, [{"volume": 1}, {"volume": 2}]),
    ]


def test_stage1_volumes_skip_short_circuits_commit_and_load(monkeypatch):
    app = _make_app()
    helpers = Stage01Helpers(app=app)

    monkeypatch.setattr(Stage01Helpers, "_log_stage1_volume_intro", lambda self, app_arg: None)
    monkeypatch.setattr(Stage01Helpers, "_should_skip_stage1_volumes", lambda self, app_arg: True)
    monkeypatch.setattr(
        Stage01Helpers,
        "_load_stage1_volume_inputs",
        lambda self, app_arg: (_ for _ in ()).throw(AssertionError("load should not run after skip")),
    )

    helpers.stage_1_volumes()

    app._safe_commit.assert_not_called()


def test_append_stage1_volume_context_compacts_older_summaries():
    context_accumulator = ""

    for vol_idx in range(1, 5):
        raw_doc = (f"권{vol_idx} 사건 요약 " * 80).strip()
        context_accumulator = Stage01Helpers._append_stage1_volume_context(context_accumulator, raw_doc, vol_idx)

    assert "[제 1권 요약]: (요약 생략)" in context_accumulator
    assert "[제 2권 요약]:" in context_accumulator
    assert "[제 3권 요약]:" in context_accumulator
    assert "[제 4권 요약]:" in context_accumulator
    assert "권4 사건 요약" in context_accumulator


def test_validate_stage1_volume_result_audits_boundary_reject():
    app = _make_app()
    helpers = Stage01Helpers(app=app)
    vol_data = {"strategy_doc": "현재 권 사건만 다룬다. " * 180}

    with patch.object(
        Stage01Helpers,
        "validate_volume_boundaries",
        return_value={"status": "REJECT", "reason": "미래 권(2권) 정보 누수 감지", "feedback": "현재 권만 유지"},
    ):
        ok = helpers._validate_stage1_volume_result(app, vol_data, 1)

    assert ok is False
    app._audit_event.assert_called_once_with(
        "volume_boundary_violation",
        "미래 권(2권) 정보 누수 감지",
        {"vol_no": 1, "feedback": "현재 권만 유지"},
    )
