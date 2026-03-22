from unittest.mock import MagicMock

from modules.core.stage01_helpers import Stage01Helpers


def _make_app():
    app = MagicMock()
    app.selected_genre = {"name": "무협", "type": "wuxia"}
    app.current_project.master_bible = {"MasterBible": {"existing": "value"}}
    return app


def test_resolve_phase0_extended_mode_maps_menu_choices():
    assert Stage01Helpers._resolve_phase0_extended_mode("2", True) == 1
    assert Stage01Helpers._resolve_phase0_extended_mode("7", True) == 6
    assert Stage01Helpers._resolve_phase0_extended_mode("2", False) is None
    assert Stage01Helpers._resolve_phase0_extended_mode("1", True) is None


def test_save_phase0_protagonist_config_updates_master_bible():
    app = _make_app()
    protagonist_config = {
        "world_origin": "현대인",
        "incarnation_type": "일반",
        "pov": "3인칭",
        "external_pov_insert_policy": "제한적 허용",
    }

    Stage01Helpers._save_phase0_protagonist_config(app, protagonist_config)

    saved = app.current_project.master_bible["MasterBible"]["protagonist_config"]
    assert saved == protagonist_config
    app.current_project.save_v20_anchor.assert_called_once_with("bible", app.current_project.master_bible)


def test_sync_phase0_existing_drafts_logs_new_project_when_empty():
    app = _make_app()
    app.current_project.paths.drafts.glob.return_value = []

    Stage01Helpers._sync_phase0_existing_drafts(app)

    app.current_project.sync_existing_manuscripts.assert_not_called()
    logged = " ".join(str(call) for call in app.ui.log.call_args_list)
    assert "New Project" in logged


def test_sync_phase0_existing_drafts_audits_nonfatal_sync_error():
    app = _make_app()
    app.current_project.paths.drafts.glob.return_value = [MagicMock()]
    app.current_project.sync_existing_manuscripts.side_effect = RuntimeError("sync crash")

    Stage01Helpers._sync_phase0_existing_drafts(app)

    app._audit_event.assert_called_once()
    assert app._audit_event.call_args.args[0] == "sync_error"
