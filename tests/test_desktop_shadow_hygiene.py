import json
from pathlib import Path


ROOT = Path(".")
PACKAGE_JSON = json.loads((ROOT / "geuldobi-desktop/package.json").read_text(encoding="utf-8"))
RUNTIME_CONTRACT = json.loads(
    (ROOT / "docs/implementation/desktop-runtime-contract-v1.json").read_text(encoding="utf-8")
)
IPC_SURFACE_CONTRACT = json.loads(
    (ROOT / "docs/implementation/desktop-ipc-surface-contract-v1.json").read_text(encoding="utf-8")
)
ROOT_MAIN = (ROOT / "geuldobi-desktop/main.js").read_text(encoding="utf-8")
LIVE_MAIN = (ROOT / "geuldobi-desktop/src/main.js").read_text(encoding="utf-8")
ROOT_DEBUG_MAIN = (ROOT / "main.js").read_text(encoding="utf-8")
PRELOAD = (ROOT / "geuldobi-desktop/src/preload.js").read_text(encoding="utf-8")
CONTROL_PLANE_JS = (ROOT / "geuldobi-desktop/src/desktop_control_plane_contract.js").read_text(encoding="utf-8")
INDEX_HTML = (ROOT / "geuldobi-desktop/src/index.html").read_text(encoding="utf-8")
SPLASH_JS = (ROOT / "geuldobi-desktop/src/splash/splash.js").read_text(encoding="utf-8")


def test_root_main_is_only_a_compatibility_shim():
    assert PACKAGE_JSON["main"] == RUNTIME_CONTRACT["authoritative_electron_entry"] == "src/main.js"
    assert IPC_SURFACE_CONTRACT["authoritative_electron_entry"] == "geuldobi-desktop/src/main.js"
    assert "Legacy compatibility shim only." in ROOT_MAIN
    assert "Authoritative Electron entry: geuldobi-desktop/src/main.js" in ROOT_MAIN
    assert 'module.exports = require("./src/main.js");' in ROOT_MAIN


def test_root_main_no_longer_carries_runtime_logic_or_stale_contract():
    assert "GEULDOBI_ENGINE_EXE" not in ROOT_MAIN
    assert 'ipcMain.handle(' not in ROOT_MAIN
    assert 'project:list-work-guard-templates' not in ROOT_MAIN
    assert 'project:apply-work-guard-template' not in ROOT_MAIN
    assert "Manual debug shadow entry only." in ROOT_DEBUG_MAIN
    assert "Authoritative Electron entry lives at geuldobi-desktop/src/main.js." in ROOT_DEBUG_MAIN
    assert 'module.exports = require("./geuldobi-desktop/src/main.js");' in ROOT_DEBUG_MAIN
    assert 'ipcMain.handle(' not in ROOT_DEBUG_MAIN
    assert "GEULDOBI_ENGINE_EXE" not in ROOT_DEBUG_MAIN
    assert "GEULDOBI_ENGINE_EXE" not in LIVE_MAIN
    assert 'ipcMain.handle(IPC_CHANNELS.project.listWorkGuardTemplates' in LIVE_MAIN


def test_dead_candidate_ipc_surfaces_are_split_from_live_inventory():
    live_methods = {entry["name"]: entry["channel"] for entry in IPC_SURFACE_CONTRACT["live_preload_methods"]}
    dead_methods = {entry["name"]: entry["channel"] for entry in IPC_SURFACE_CONTRACT["dead_candidate_preload_methods"]}

    assert live_methods["getStatus"] == "bridge:status"
    assert dead_methods == {
        "getWorkspacePath": "workspace:get-path",
    }
    assert "getStatus" in INDEX_HTML
    assert "getWorkspacePath" not in INDEX_HTML
    assert "getStatus" not in SPLASH_JS
    assert "getWorkspacePath" not in SPLASH_JS
    assert "PRELOAD_METHOD_CHANNELS" in PRELOAD
    assert "IPC_CHANNELS" in LIVE_MAIN

    for method_name, channel in live_methods.items():
        assert method_name in PRELOAD
        assert channel in CONTROL_PLANE_JS

    for method_name, channel in dead_methods.items():
        assert method_name in PRELOAD
        assert channel in CONTROL_PLANE_JS
        assert "Dead-candidate compatibility surface." in PRELOAD
        assert "Dead-candidate compatibility surface." in LIVE_MAIN
