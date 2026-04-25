import json
import subprocess
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


def test_residue_surfaces_are_removed_or_tracked_separately_from_live_inventory():
    removed_dirs = CONTRACT["residue_surfaces"]["removed_tracked_directories"]
    removed_project_dirs = CONTRACT["residue_surfaces"]["removed_tracked_project_directories"]
    removed_temp_paths = CONTRACT["residue_surfaces"]["removed_tracked_temp_paths"]
    preserved_evidence_files = CONTRACT["residue_surfaces"]["preserved_evidence_files"]
    removed_spike_paths = CONTRACT["residue_surfaces"]["removed_tracked_spike_paths"]
    preserved_spike_summary_docs = CONTRACT["residue_surfaces"]["preserved_spike_summary_docs"]
    removed_files = CONTRACT["residue_surfaces"]["removed_tracked_files"]

    for rel_path in removed_dirs:
        assert not (ROOT / rel_path).exists()

    for rel_path in removed_files:
        assert not (ROOT / rel_path).exists()

    tracked_project_residue = subprocess.check_output(
        ["git", "ls-files", "--", *removed_project_dirs],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    )
    assert tracked_project_residue == ""

    tracked_temp_residue = subprocess.check_output(
        ["git", "ls-files", "--", *removed_temp_paths],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    )
    assert tracked_temp_residue == ""

    tracked_spike_residue = subprocess.check_output(
        ["git", "ls-files", "--", *removed_spike_paths],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    )
    assert tracked_spike_residue == ""

    for rel_path in preserved_evidence_files:
        assert (ROOT / rel_path).exists()

    for rel_path in preserved_spike_summary_docs:
        assert (ROOT / rel_path).exists()

    tracked_preserved_evidence = subprocess.check_output(
        ["git", "ls-files", "--", *preserved_evidence_files],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    )
    assert set(tracked_preserved_evidence.splitlines()) == set(preserved_evidence_files)


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
    ignored_future_dirs = CONTRACT["residue_surfaces"]["ignored_future_directories"]
    ignored_future_root_temp_paths = CONTRACT["residue_surfaces"]["ignored_future_root_temp_paths"]

    assert {f"{path_name}/" for path_name in ignored_future_dirs}.issubset(ignore_lines)
    assert set(ignored_future_root_temp_paths).issubset(ignore_lines)
