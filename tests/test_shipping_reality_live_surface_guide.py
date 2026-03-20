import json
from pathlib import Path


ROOT = Path(".")
PACKAGE_JSON = json.loads((ROOT / "geuldobi-desktop/package.json").read_text(encoding="utf-8"))
DESKTOP_GUIDE = (ROOT / "geuldobi-desktop/DESKTOP-GUIDE.md").read_text(encoding="utf-8")
SHIPPING_GUIDE = (
    ROOT / "docs/2026-03-13/shipping-reality-live-surface-guide.md"
).read_text(encoding="utf-8")
RUNTIME_CONTRACT = json.loads(
    (ROOT / "docs/implementation/desktop-runtime-contract-v1.json").read_text(encoding="utf-8")
)
SURFACE_CONTAINMENT = json.loads(
    (ROOT / "docs/implementation/surface-containment-contract-v1.json").read_text(encoding="utf-8")
)
IPC_CONTRACT = json.loads(
    (ROOT / "docs/implementation/desktop-ipc-surface-contract-v1.json").read_text(encoding="utf-8")
)


def test_shipping_guide_freezes_current_runtime_model_and_live_entry():
    assert RUNTIME_CONTRACT["runtime_model_id"] == "source_bundle_primary"
    assert PACKAGE_JSON["main"] == RUNTIME_CONTRACT["authoritative_electron_entry"] == "src/main.js"
    assert "Runtime model: `source_bundle_primary`" in SHIPPING_GUIDE
    assert "Authoritative Electron entry: `geuldobi-desktop/src/main.js`" in SHIPPING_GUIDE
    assert "`engine.exe` is not the shipped primary runtime artifact." in SHIPPING_GUIDE


def test_shipping_guide_classifies_live_shadow_alternate_and_reference_surfaces():
    assert SURFACE_CONTAINMENT["live_surfaces"]["desktop_entry"]["path"] == "geuldobi-desktop/src/main.js"
    assert any(
        entry["path"] == "geuldobi-desktop/main.js"
        for entry in SURFACE_CONTAINMENT["shadow_surfaces"]
    )
    assert any(entry["path"] == "main.js" for entry in SURFACE_CONTAINMENT["shadow_surfaces"])
    assert "lite_mode/" in SHIPPING_GUIDE
    assert "test_mode/" in SHIPPING_GUIDE
    assert "UI/" in SHIPPING_GUIDE
    assert "Compatibility shim only" in SHIPPING_GUIDE
    assert IPC_CONTRACT["authoritative_electron_entry"] == "geuldobi-desktop/src/main.js"


def test_shipping_guide_and_desktop_guide_mark_npm_test_as_subset_gate():
    test_script = PACKAGE_JSON["scripts"]["test"]
    assert "pytest -q" in test_script
    assert PACKAGE_JSON["scripts"]["test:desktop-contract"] == test_script
    assert "npm --prefix geuldobi-desktop test" in SHIPPING_GUIDE
    assert "npm --prefix geuldobi-desktop run test:desktop-contract" in SHIPPING_GUIDE
    assert "curated subset" in SHIPPING_GUIDE
    assert "not the full repo regression envelope" in SHIPPING_GUIDE
    assert "npm test" in DESKTOP_GUIDE
    assert "npm run test:desktop-contract" in DESKTOP_GUIDE
    assert "desktop subset gate" in DESKTOP_GUIDE
    assert "not the full repo regression envelope" in DESKTOP_GUIDE
    assert "npm run start:spike" in SHIPPING_GUIDE
    assert "npm run start:desktop-spike" in SHIPPING_GUIDE
    assert "npm run start:spike" in DESKTOP_GUIDE
    assert "npm run start:desktop-spike" in DESKTOP_GUIDE
