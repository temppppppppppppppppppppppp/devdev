from pathlib import Path

import main_a


def test_main_a_bootstraps_engine_sys_path_before_modules_import():
    source = Path("main_a.py").read_text(encoding="utf-8")

    bootstrap_call = source.index("_bootstrap_engine_sys_path()")
    modules_import = source.index("import modules.core.spinners as _spinners_mod")

    assert bootstrap_call < modules_import


def test_boot_failure_traceback_persists_to_workspace_log(tmp_path, monkeypatch):
    monkeypatch.setenv("GEULDOBI_WORKSPACE", str(tmp_path))

    try:
        raise RuntimeError("boot smoke")
    except RuntimeError:
        error_log = main_a._persist_boot_failure_traceback()

    expected = tmp_path / "logs" / "error.log"
    assert error_log == str(expected)
    assert expected.exists()
    contents = expected.read_text(encoding="utf-8")
    assert "RuntimeError: boot smoke" in contents
