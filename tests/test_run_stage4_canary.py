import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import scripts.run_stage4_canary as canary_script


def setup_function():
    canary_script.os.environ.pop("GEULDOBI_PROVIDER_MODE", None)


def test_run_canary_saves_and_flushes_before_analyze():
    app = SimpleNamespace(
        _get_int_input=None,
        _stage_4_v2_chief_writer=MagicMock(),
        pass_rate_monitor=MagicMock(),
        _flush_audit_buffer=MagicMock(),
        memory=None,
        current_project=SimpleNamespace(db=MagicMock()),
    )
    app.current_project.db.conn = MagicMock()
    app.current_project.db.close = MagicMock()

    with (
        patch.object(canary_script, "_load_project_genre", return_value={"type": "investment", "name": "investment"}),
        patch.object(canary_script, "_boot_app", return_value=app),
        patch.object(canary_script, "analyze_canary", return_value={"hard_gates": {"status": "pass"}}) as analyze,
    ):
        result = canary_script.run_canary("00_test_06", target_ep=4)

    app._stage_4_v2_chief_writer.assert_called_once_with(limit_mode=False, target_ep=4)
    app.pass_rate_monitor.save.assert_called_once()
    app._flush_audit_buffer.assert_called_once()
    analyze.assert_called_once_with("_canary/00_test_06", target_ep=4)
    assert result["hard_gates"]["status"] == "pass"


def test_run_canary_bootstraps_missing_pass_rate_monitor():
    monitor = MagicMock()
    app = SimpleNamespace(
        _get_int_input=None,
        _stage_4_v2_chief_writer=MagicMock(),
        pass_rate_monitor=None,
        _flush_audit_buffer=MagicMock(),
        memory=None,
        current_project=SimpleNamespace(db=MagicMock()),
    )
    app.current_project.db.conn = MagicMock()
    app.current_project.db.close = MagicMock()

    with (
        patch.object(canary_script, "_load_project_genre", return_value={"type": "investment", "name": "investment"}),
        patch.object(canary_script, "_boot_app", return_value=app),
        patch.object(canary_script, "PassRateMonitor", return_value=monitor) as prm_cls,
        patch.object(canary_script, "analyze_canary", return_value={"hard_gates": {"status": "pass"}}),
    ):
        canary_script.run_canary("00_test_06", target_ep=4)

    prm_cls.assert_called_once_with(canary_script.PROJECT_ROOT / "projects" / "_canary" / "00_test_06")
    assert app.pass_rate_monitor is monitor
    monitor.save.assert_called_once()
    app._stage_4_v2_chief_writer.assert_called_once_with(limit_mode=False, target_ep=4)


def test_run_canary_without_genre_raises():
    with patch.object(canary_script, "_load_project_genre", return_value={}):
        try:
            canary_script.run_canary("00_test_06", target_ep=4)
        except RuntimeError as exc:
            assert "genre_info" in str(exc)
        else:
            raise AssertionError("expected RuntimeError for missing genre")


def test_run_canary_gemini_direct_provider_mode_scrubs_non_gemini_env(monkeypatch):
    app = SimpleNamespace(
        _get_int_input=None,
        _stage_4_v2_chief_writer=MagicMock(),
        pass_rate_monitor=MagicMock(),
        _flush_audit_buffer=MagicMock(),
        memory=None,
        current_project=SimpleNamespace(db=MagicMock()),
    )
    app.current_project.db.conn = MagicMock()
    app.current_project.db.close = MagicMock()

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant")
    monkeypatch.setenv("CLAUDE_API", "sk-claude")
    monkeypatch.setenv("VERTEX_API_KEY", "vk")
    monkeypatch.setenv("VERTEX_PROJECT_ID", "proj")
    monkeypatch.setenv("VERTEX_LOCATION", "us-central1")
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/tmp/sa.json")

    def fake_boot(*_args, **_kwargs):
        assert "ANTHROPIC_API_KEY" not in canary_script.os.environ
        assert "CLAUDE_API" not in canary_script.os.environ
        assert "VERTEX_API_KEY" not in canary_script.os.environ
        assert "VERTEX_PROJECT_ID" not in canary_script.os.environ
        assert "VERTEX_LOCATION" not in canary_script.os.environ
        assert "GOOGLE_APPLICATION_CREDENTIALS" not in canary_script.os.environ
        assert canary_script.os.environ["GEULDOBI_PROVIDER_MODE"] == "gemini_direct"
        return app

    with (
        patch.object(canary_script, "_load_project_genre", return_value={"type": "investment", "name": "investment"}),
        patch.object(canary_script, "_boot_app", side_effect=fake_boot),
        patch.object(canary_script, "analyze_canary", return_value={"hard_gates": {"status": "pass"}}),
    ):
        canary_script.run_canary("00_test_06", target_ep=4, provider_mode="gemini_direct")

    assert canary_script.os.environ["ANTHROPIC_API_KEY"] == "sk-ant"
    assert canary_script.os.environ["CLAUDE_API"] == "sk-claude"
    assert canary_script.os.environ["VERTEX_API_KEY"] == "vk"
    assert canary_script.os.environ["VERTEX_PROJECT_ID"] == "proj"
    assert canary_script.os.environ["VERTEX_LOCATION"] == "us-central1"
    assert canary_script.os.environ["GOOGLE_APPLICATION_CREDENTIALS"] == "/tmp/sa.json"
    assert "GEULDOBI_PROVIDER_MODE" not in canary_script.os.environ


def test_run_canary_ambient_provider_mode_preserves_non_gemini_env(monkeypatch):
    app = SimpleNamespace(
        _get_int_input=None,
        _stage_4_v2_chief_writer=MagicMock(),
        pass_rate_monitor=MagicMock(),
        _flush_audit_buffer=MagicMock(),
        memory=None,
        current_project=SimpleNamespace(db=MagicMock()),
    )
    app.current_project.db.conn = MagicMock()
    app.current_project.db.close = MagicMock()

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant")

    def fake_boot(*_args, **_kwargs):
        assert canary_script.os.environ["ANTHROPIC_API_KEY"] == "sk-ant"
        assert canary_script.os.environ["GEULDOBI_PROVIDER_MODE"] == "ambient"
        return app

    with (
        patch.object(canary_script, "_load_project_genre", return_value={"type": "investment", "name": "investment"}),
        patch.object(canary_script, "_boot_app", side_effect=fake_boot),
        patch.object(canary_script, "analyze_canary", return_value={"hard_gates": {"status": "pass"}}),
    ):
        canary_script.run_canary("00_test_06", target_ep=4, provider_mode="ambient")

    assert canary_script.os.environ["ANTHROPIC_API_KEY"] == "sk-ant"
    assert "GEULDOBI_PROVIDER_MODE" not in canary_script.os.environ


def test_run_canary_vertex_provider_mode_preserves_vertex_env(monkeypatch):
    app = SimpleNamespace(
        _get_int_input=None,
        _stage_4_v2_chief_writer=MagicMock(),
        pass_rate_monitor=MagicMock(),
        _flush_audit_buffer=MagicMock(),
        memory=None,
        current_project=SimpleNamespace(db=MagicMock()),
    )
    app.current_project.db.conn = MagicMock()
    app.current_project.db.close = MagicMock()

    monkeypatch.setenv("VERTEX_API_KEY", "vk")
    monkeypatch.setenv("VERTEX_PROJECT_ID", "proj")

    def fake_boot(*_args, **_kwargs):
        assert canary_script.os.environ["VERTEX_API_KEY"] == "vk"
        assert canary_script.os.environ["VERTEX_PROJECT_ID"] == "proj"
        assert canary_script.os.environ["GEULDOBI_PROVIDER_MODE"] == "vertex_ai"
        return app

    with (
        patch.object(canary_script, "_load_project_genre", return_value={"type": "investment", "name": "investment"}),
        patch.object(canary_script, "_boot_app", side_effect=fake_boot),
        patch.object(canary_script, "analyze_canary", return_value={"hard_gates": {"status": "pass"}}),
    ):
        canary_script.run_canary("00_test_06", target_ep=4, provider_mode="vertex_ai")

    assert canary_script.os.environ["VERTEX_API_KEY"] == "vk"
    assert canary_script.os.environ["VERTEX_PROJECT_ID"] == "proj"
    assert "GEULDOBI_PROVIDER_MODE" not in canary_script.os.environ


def test_run_canary_restores_inherited_provider_mode(monkeypatch):
    app = SimpleNamespace(
        _get_int_input=None,
        _stage_4_v2_chief_writer=MagicMock(),
        pass_rate_monitor=MagicMock(),
        _flush_audit_buffer=MagicMock(),
        memory=None,
        current_project=SimpleNamespace(db=MagicMock()),
    )
    app.current_project.db.conn = MagicMock()
    app.current_project.db.close = MagicMock()

    monkeypatch.setenv("GEULDOBI_PROVIDER_MODE", "vertex_ai")

    def fake_boot(*_args, **_kwargs):
        assert canary_script.os.environ["GEULDOBI_PROVIDER_MODE"] == "vertex_ai"
        return app

    with (
        patch.object(canary_script, "_load_project_genre", return_value={"type": "investment", "name": "investment"}),
        patch.object(canary_script, "_boot_app", side_effect=fake_boot),
        patch.object(canary_script, "analyze_canary", return_value={"hard_gates": {"status": "pass"}}),
    ):
        canary_script.run_canary("00_test_06", target_ep=4)

    assert canary_script.os.environ["GEULDOBI_PROVIDER_MODE"] == "vertex_ai"


def test_prepare_canary_routes_new_target_into_canary_root(tmp_path):
    source_root = tmp_path / "projects" / "__000403"
    source_root.mkdir(parents=True)

    with (
        patch.object(canary_script, "PROJECT_ROOT", tmp_path),
        patch.object(canary_script, "prepare_stage4_canary_project", return_value={"ok": True}) as prepare,
    ):
        payload = canary_script.prepare_canary("__000403", "canary___000403_stage4_ep3_numauth_r3", from_ep=3, force=False)

    assert payload == {"ok": True}
    prepare.assert_called_once_with(
        source_root.resolve(),
        (tmp_path / "projects" / "_canary" / "canary___000403_stage4_ep3_numauth_r3").resolve(),
        from_ep=3,
        force=False,
    )


def test_run_canary_boots_nested_canary_project_name(tmp_path):
    project_root = tmp_path / "projects" / "_canary" / "proof_refresh"
    project_root.mkdir(parents=True)

    app = SimpleNamespace(
        _get_int_input=None,
        _stage_4_v2_chief_writer=MagicMock(),
        pass_rate_monitor=MagicMock(),
        _flush_audit_buffer=MagicMock(),
        memory=None,
        current_project=SimpleNamespace(db=MagicMock()),
    )
    app.current_project.db.conn = MagicMock()
    app.current_project.db.close = MagicMock()

    with (
        patch.object(canary_script, "PROJECT_ROOT", tmp_path),
        patch.object(canary_script, "_load_project_genre", return_value={"type": "investment", "name": "investment"}),
        patch.object(canary_script, "_boot_app", return_value=app) as boot,
        patch.object(canary_script, "analyze_canary", return_value={"hard_gates": {"status": "pass"}}),
    ):
        canary_script.run_canary("proof_refresh", target_ep=4)

    boot.assert_called_once_with("_canary/proof_refresh", {"type": "investment", "name": "investment"})


def test_analyze_canary_writes_summary_and_companion_audit(tmp_path):
    project_root = tmp_path / "projects" / "proof_refresh"
    (project_root / "logs").mkdir(parents=True, exist_ok=True)
    summary_payload = {
        "project_locator": "projects/proof_refresh",
        "proof_record_summary": {"classification": "current"},
        "companion_audit_summary": {"status": "fail", "row_count": 1},
        "hard_gates": {"status": "fail"},
    }

    with (
        patch.object(canary_script, "PROJECT_ROOT", tmp_path),
        patch.object(canary_script, "build_stage4_canary_summary", return_value=summary_payload),
    ):
        result = canary_script.analyze_canary("proof_refresh", target_ep=4)

    assert result == summary_payload
    summary_path = project_root / "logs" / "canary_summary.json"
    companion_path = project_root / "logs" / "canary_companion_audit.json"
    assert json.loads(summary_path.read_text(encoding="utf-8")) == summary_payload
    assert json.loads(companion_path.read_text(encoding="utf-8")) == {
        "project_locator": "projects/proof_refresh",
        "proof_record_summary": {"classification": "current"},
        "companion_audit_summary": {"status": "fail", "row_count": 1},
    }


def test_branch_inventory_writes_output(tmp_path):
    project_root = tmp_path / "projects" / "proof_refresh"
    (project_root / "logs").mkdir(parents=True, exist_ok=True)

    with (
        patch.object(canary_script, "PROJECT_ROOT", tmp_path),
        patch.object(
            canary_script,
            "build_stage4_branch_inventory",
            return_value={"summary_role": "stage4_runtime_branch_proof_inventory", "entries_considered": 1},
        ),
    ):
        result = canary_script.branch_inventory(["proof_refresh"], output_path="docs/out.json")

    assert result["entries_considered"] == 1
    out_path = tmp_path / "docs" / "out.json"
    assert json.loads(out_path.read_text(encoding="utf-8")) == {
        "summary_role": "stage4_runtime_branch_proof_inventory",
        "entries_considered": 1,
    }
