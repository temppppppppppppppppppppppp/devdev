import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads(
    (ROOT / "docs" / "implementation" / "surface-containment-contract-v1.json").read_text(encoding="utf-8")
)


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_live_and_shadow_entries_follow_contract():
    package = json.loads((ROOT / CONTRACT["live_surfaces"]["desktop_package"]["path"]).read_text(encoding="utf-8"))
    assert package["main"] == CONTRACT["live_surfaces"]["desktop_package"]["main"]

    src_main = _read(CONTRACT["live_surfaces"]["desktop_entry"]["path"])
    assert 'const electron = require("electron");' in src_main

    desktop_shadow = _read(CONTRACT["shadow_surfaces"][0]["path"])
    assert "Legacy compatibility shim only." in desktop_shadow
    assert "Authoritative Electron entry: geuldobi-desktop/src/main.js" in desktop_shadow
    assert 'module.exports = require("./src/main.js");' in desktop_shadow

    root_shadow = _read(CONTRACT["shadow_surfaces"][1]["path"])
    assert "Manual debug shadow entry only." in root_shadow
    assert "Authoritative Electron entry lives at geuldobi-desktop/src/main.js." in root_shadow
    assert 'module.exports = require("./geuldobi-desktop/src/main.js");' in root_shadow
    assert "ipcMain.handle(" not in root_shadow


def test_manual_only_surfaces_are_marked_and_not_live_entries():
    expected_markers = {
        "lite_mode/bridge/ui_discovery.py": "Manual-only helper.",
        "lite_mode/bridge/gemini_driver.py": "Manual-only helper.",
        "lite_mode/manual_ui_discovery_probe.py": "Manual-only probe.",
        "tools/normalize_arcs_db.py": "[manual-only]",
        "tools/fix_future_items.py": "[manual-only]",
        "tools2/expand_ep15.py": "[manual-only]",
        "tools2/style_transfer.py": "[manual-only]",
        "main_tools/blueprint_editor.py": "[manual-only]",
    }

    for entry in CONTRACT["manual_only_surfaces"]:
        rel_path = entry["path"]
        text = _read(rel_path)
        assert expected_markers[rel_path] in text
        assert rel_path != CONTRACT["live_surfaces"]["desktop_entry"]["path"]


def test_residue_surfaces_are_tracked_separately_from_live_inventory():
    residue_dirs = CONTRACT["residue_surfaces"]["directories"]
    residue_globs = CONTRACT["residue_surfaces"]["globs"]

    for rel_path in residue_dirs:
        assert (ROOT / rel_path).exists()

    matched = set()
    for pattern in residue_globs:
        matched.update(path.name for path in ROOT.glob(pattern))

    assert matched
    assert "temp-electron-paths.js" in matched
    assert "temp-run-packaged.ps1" in matched


def test_manual_and_residue_surfaces_are_excluded_from_legacy_packaging_scope():
    packaging = _read("배포_패키징.ps1")

    for path_name in [
        "test_mode",
        "lite_mode",
        "spikes",
        "MagicMock",
        "tmp_stage2_digest_debug",
        "rlhf_data",
        "datasets",
    ]:
        assert f'"{path_name}"' in packaging


def test_manual_and_prototype_surfaces_are_excluded_from_broad_ruff_scope():
    pyproject = tomllib.loads(_read("pyproject.toml"))
    excludes = set(pyproject["tool"]["ruff"]["extend-exclude"])

    assert {"test_mode", "lite_mode", "spikes"}.issubset(excludes)


def test_future_generated_residue_paths_are_ignored_after_tracked_cleanup():
    ignore_lines = set(_read(".gitignore").splitlines())

    assert {
        "MagicMock/",
        "tmp_stage2_digest_debug/",
        "test_mode/projects/",
        "lite_mode/projects/",
    }.issubset(ignore_lines)
