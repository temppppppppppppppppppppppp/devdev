import json
import sqlite3
from pathlib import Path


ROOT = Path(".")
PACKAGE_JSON = json.loads((ROOT / "geuldobi-desktop/package.json").read_text(encoding="utf-8"))
BUILD_RELEASE = (ROOT / "build/build_release.ps1").read_text(encoding="utf-8")
BACKEND_ENTRY = (ROOT / "build/backend_entry.py").read_text(encoding="utf-8")
BACKEND_SPEC = (ROOT / "build/backend.spec").read_text(encoding="utf-8")
PREPARE_PYTHON_EMBED = (ROOT / "build/prepare_python_embed.ps1").read_text(encoding="utf-8")
DESKTOP_MAIN = (ROOT / "geuldobi-desktop/src/main.js").read_text(encoding="utf-8")
DESKTOP_GUIDE = (ROOT / "geuldobi-desktop/DESKTOP-GUIDE.md").read_text(encoding="utf-8")
RUNTIME_CONTRACT = json.loads(
    (ROOT / "docs/implementation/desktop-runtime-contract-v1.json").read_text(encoding="utf-8")
)
WORKSPACE_SEED_BUILDER = (ROOT / "geuldobi-desktop/scripts/build_workspace_seed.py").read_text(encoding="utf-8")
BUILD_RELEASE_NORMALIZED = BUILD_RELEASE.replace("\\\\", "\\")


def test_packaged_resources_stage_backend_engine_bundle_and_embedded_python():
    resources = PACKAGE_JSON["build"]["extraResources"]
    mapped = {(item["from"], item["to"]) for item in resources}
    expected = {
        (item["from"], item["to"]) for item in RUNTIME_CONTRACT["extra_resources"]
    }
    assert mapped == expected
    for resource in resources:
        filters = set(resource["filter"])
        assert "**/*" in filters
        assert "!**/*.log" in filters
        assert "!**/*.tmp" in filters
        assert "!**/*.bak" in filters


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


def test_workspace_seed_builder_uses_canonical_smoke_fixture_source():
    assert 'SAMPLE_PROJECT_SOURCE = ROOT / "projects" / "smoke_fixture_demo"' in WORKSPACE_SEED_BUILDER
    assert 'SAMPLE_PROJECT_TARGET = "investment_canary_demo"' in WORKSPACE_SEED_BUILDER


def test_canonical_smoke_fixture_source_meets_minimum_smoke_contract():
    source_root = ROOT / "projects" / "smoke_fixture_demo"
    db_path = source_root / "project_data.db"
    assert source_root.exists()
    assert db_path.exists()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT data FROM anchors WHERE key='arcs'").fetchone()
        assert row is not None and row["data"]
        arc_count = len(json.loads(row["data"]))
        blueprint_count = conn.execute("SELECT COUNT(*) AS c FROM blueprints").fetchone()["c"]
        manuscript_count = conn.execute("SELECT COUNT(*) AS c FROM manuscripts").fetchone()["c"]
    finally:
        conn.close()

    assert arc_count >= 3
    assert blueprint_count >= 3
    assert manuscript_count == 0


def test_backend_build_runtime_includes_google_genai_hiddenimports():
    assert '"google.genai"' in BACKEND_SPEC
    assert '"google.genai.types"' in BACKEND_SPEC


def test_build_scripts_install_google_genai_sdk_not_legacy_package_name():
    assert "google-genai" in PREPARE_PYTHON_EMBED
    assert "google-genai" in BUILD_RELEASE
    assert "google-generativeai" not in PREPARE_PYTHON_EMBED


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


def test_package_file_filters_drop_unused_debug_desk_sprites_only():
    files = PACKAGE_JSON["build"]["files"]

    assert "src/**/*" in files
    assert "!src/sprites/dbg_desk_*" in files
    assert "!src/sprites/dbg_sheet_*" not in files
