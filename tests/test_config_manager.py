"""ConfigManager settings loader tests (Phase 5-B-1)."""

from pathlib import Path

from modules.core.config_manager import ConfigManager


def _write_validation_yaml(root: Path, body: str) -> None:
    settings_dir = root / "config" / "settings"
    settings_dir.mkdir(parents=True, exist_ok=True)
    (settings_dir / "validation.yaml").write_text(body, encoding="utf-8")


def test_load_settings_missing_file_returns_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cm = ConfigManager()

    assert cm.load_settings() == {}


def test_load_settings_reads_yaml(tmp_path, monkeypatch):
    _write_validation_yaml(
        tmp_path,
        "manuscript:\n  min_length: 4000\nfeature_flags:\n  enable_patch_mode: true\n",
    )
    monkeypatch.chdir(tmp_path)
    cm = ConfigManager()

    data = cm.load_settings()
    assert data["manuscript"]["min_length"] == 4000
    assert data["feature_flags"]["enable_patch_mode"] is True


def test_get_guard_threshold_returns_default_on_missing_key(tmp_path, monkeypatch):
    _write_validation_yaml(tmp_path, "manuscript:\n  min_length: 4000\n")
    monkeypatch.chdir(tmp_path)
    cm = ConfigManager()

    assert cm.get_guard_threshold("manuscript.unknown", 123) == 123


def test_get_guard_threshold_type_mismatch_fallback(tmp_path, monkeypatch):
    _write_validation_yaml(tmp_path, "manuscript:\n  min_length: oops\n")
    monkeypatch.chdir(tmp_path)
    cm = ConfigManager()

    assert cm.get_guard_threshold("manuscript.min_length", 4000) == 4000


def test_get_guard_threshold_numeric_coercion(tmp_path, monkeypatch):
    _write_validation_yaml(tmp_path, "thresholds:\n  hud_change: 1\n")
    monkeypatch.chdir(tmp_path)
    cm = ConfigManager()

    value = cm.get_guard_threshold("thresholds.hud_change", 0.1)
    assert value == 1.0


def test_get_validation_policy_alias(tmp_path, monkeypatch):
    _write_validation_yaml(tmp_path, "retry:\n  writer_max_attempts: 5\n")
    monkeypatch.chdir(tmp_path)
    cm = ConfigManager()

    assert cm.get_validation_policy("retry.writer_max_attempts", 3) == 5


def test_get_feature_flag_bool(tmp_path, monkeypatch):
    _write_validation_yaml(tmp_path, "feature_flags:\n  enable_npc_history: true\n")
    monkeypatch.chdir(tmp_path)
    cm = ConfigManager()

    assert cm.get_feature_flag("enable_npc_history", False) is True


def test_get_feature_flag_type_mismatch_fallback(tmp_path, monkeypatch):
    _write_validation_yaml(tmp_path, "feature_flags:\n  enable_npc_history: 1\n")
    monkeypatch.chdir(tmp_path)
    cm = ConfigManager()

    assert cm.get_feature_flag("enable_npc_history", False) is False


def test_cache_and_invalidate(tmp_path, monkeypatch):
    _write_validation_yaml(tmp_path, "manuscript:\n  min_length: 4000\n")
    monkeypatch.chdir(tmp_path)
    cm = ConfigManager()

    assert cm.get_guard_threshold("manuscript.min_length", 0) == 4000

    _write_validation_yaml(tmp_path, "manuscript:\n  min_length: 3500\n")
    # Cache still active
    assert cm.get_guard_threshold("manuscript.min_length", 0) == 4000

    cm.invalidate_settings_cache()
    assert cm.get_guard_threshold("manuscript.min_length", 0) == 3500


def test_force_reload_bypasses_cache(tmp_path, monkeypatch):
    _write_validation_yaml(tmp_path, "manuscript:\n  min_length: 4000\n")
    monkeypatch.chdir(tmp_path)
    cm = ConfigManager()
    assert cm.load_settings()["manuscript"]["min_length"] == 4000

    _write_validation_yaml(tmp_path, "manuscript:\n  min_length: 1234\n")
    assert cm.load_settings(force_reload=True)["manuscript"]["min_length"] == 1234
