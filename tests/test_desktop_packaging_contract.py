import json
from pathlib import Path


ROOT = Path(".")
PACKAGE_JSON = json.loads((ROOT / "geuldobi-desktop/package.json").read_text(encoding="utf-8"))
BUILD_RELEASE = (ROOT / "build/build_release.ps1").read_text(encoding="utf-8")
BACKEND_ENTRY = (ROOT / "build/backend_entry.py").read_text(encoding="utf-8")
DESKTOP_MAIN = (ROOT / "geuldobi-desktop/src/main.js").read_text(encoding="utf-8")
DESKTOP_GUIDE = (ROOT / "geuldobi-desktop/DESKTOP-GUIDE.md").read_text(encoding="utf-8")
RUNTIME_CONTRACT = json.loads(
    (ROOT / "docs/implementation/desktop-runtime-contract-v1.json").read_text(encoding="utf-8")
)
BUILD_RELEASE_NORMALIZED = BUILD_RELEASE.replace("\\\\", "\\")


def test_packaged_resources_stage_backend_engine_bundle_and_embedded_python():
    resources = PACKAGE_JSON["build"]["extraResources"]
    mapped = {(item["from"], item["to"]) for item in resources}
    expected = {
        (item["from"], item["to"]) for item in RUNTIME_CONTRACT["extra_resources"]
    }
    assert mapped == expected


def test_build_release_verifies_source_bundle_packaging_inventory():
    assert f'$RUNTIME_CONTRACT = "{RUNTIME_CONTRACT["runtime_model_id"]}"' in BUILD_RELEASE
    assert "Sync-EngineBundle" in BUILD_RELEASE
    assert "Assert-PackagedResources" in BUILD_RELEASE
    assert "runtime contract: $RUNTIME_CONTRACT" in BUILD_RELEASE
    for resource in RUNTIME_CONTRACT["packaged_resource_inventory"]:
        assert resource.replace("/", "\\") in BUILD_RELEASE_NORMALIZED


def test_backend_entry_and_desktop_main_align_on_source_bundle_runtime():
    assert f'const PACKAGED_RUNTIME_MODEL = "{RUNTIME_CONTRACT["runtime_model_id"]}";' in DESKTOP_MAIN
    assert f'PACKAGED_RUNTIME_MODEL = "{RUNTIME_CONTRACT["runtime_model_id"]}"' in BACKEND_ENTRY
    for env_name in RUNTIME_CONTRACT["desktop_main_packaged_env"]:
        assert env_name in DESKTOP_MAIN
    for env_name in RUNTIME_CONTRACT["backend_entry_packaged_env"]:
        assert env_name in BACKEND_ENTRY
    assert 'GEULDOBI_ENGINE_EXE' not in DESKTOP_MAIN
    assert 'backend.exe' in DESKTOP_MAIN
    assert PACKAGE_JSON["main"] == RUNTIME_CONTRACT["authoritative_electron_entry"]


def test_package_build_scripts_stage_workspace_seed_before_builder():
    scripts = PACKAGE_JSON["scripts"]
    assert "prepare:workspace-seed" in scripts
    assert "build_workspace_seed.py" in scripts["prepare:workspace-seed"]
    assert "prepare:workspace-seed" in scripts["build"]
    assert "prepare:workspace-seed" in scripts["build:dir"]


def test_desktop_main_seeds_packaged_workspace_materials_before_backend_boot():
    assert 'path.join(process.resourcesPath, "workspace-seed")' in DESKTOP_MAIN
    assert 'for (const folder of ["bible", "treatments", "projects"])' in DESKTOP_MAIN
    assert "syncPackagedWorkspaceSeed();" in DESKTOP_MAIN


def test_desktop_guide_describes_source_bundle_runtime_not_engine_exe_product():
    assert RUNTIME_CONTRACT["runtime_model_id"] in DESKTOP_GUIDE
    assert "Authoritative Electron entry: `geuldobi-desktop/src/main.js`" in DESKTOP_GUIDE
    assert "engine source bundle" in DESKTOP_GUIDE
    assert "resources/engine/main_a.py" in DESKTOP_GUIDE
    assert "resources/python-embed/python.exe" in DESKTOP_GUIDE
    assert "resources/workspace-seed/seed-manifest.json" in DESKTOP_GUIDE
    assert "engine.exe" not in DESKTOP_GUIDE
