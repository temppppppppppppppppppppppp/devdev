"""Bounded smoke test for the runtime/control-plane authority contract.

Validates that:
- RUNTIME_AUTHORITY_CONTRACT declares one supported chain
- CONTROL_PLANE_AUTHORITY_CONTRACT distinguishes authoritative sinks from companion snapshots
- Compatibility entries reference actual filesystem paths
- Root main.js and geuldobi-desktop/main.js are labeled as non-authoritative
- Supported chain entries exist
"""

import json
from pathlib import Path

from modules.api.control_plane_contract import (
    AUTHORITY_ROLE_AUTHORITATIVE_SINK,
    AUTHORITY_ROLE_COMPANION_SNAPSHOT,
    CONTROL_PLANE_AUTHORITY_CONTRACT,
    PUBLIC_RUN_KEYS,
    build_control_plane_authority_summary,
    get_control_plane_authority_role,
)
from modules.core.runtime_paths import RUNTIME_AUTHORITY_CONTRACT, build_runtime_authority_summary

ROOT = Path(__file__).resolve().parents[1]


def test_runtime_authority_contract_has_single_supported_entry():
    entry = RUNTIME_AUTHORITY_CONTRACT["supported_entry"]
    assert isinstance(entry, str) and entry
    assert (ROOT / entry).exists(), f"supported entry {entry} not found"


def test_runtime_authority_contract_supported_chain_files_exist():
    chain = RUNTIME_AUTHORITY_CONTRACT["supported_chain"]
    assert isinstance(chain, list) and len(chain) >= 3
    for path_str in chain:
        assert (ROOT / path_str).exists(), f"chain entry {path_str} not found"


def test_runtime_authority_contract_compatibility_entries_labeled():
    compat = RUNTIME_AUTHORITY_CONTRACT["compatibility_entries"]
    assert isinstance(compat, dict) and len(compat) >= 2
    for path_str, label in compat.items():
        assert isinstance(label, str) and label
        candidate = ROOT / path_str.rstrip("/")
        assert candidate.exists(), f"compatibility entry {path_str} not found"


def test_root_main_js_is_compatibility_entry():
    compat = RUNTIME_AUTHORITY_CONTRACT["compatibility_entries"]
    assert "main.js" in compat
    assert compat["main.js"] == "debug_shadow_entry"

    content = (ROOT / "main.js").read_text(encoding="utf-8")
    assert "shadow" in content.lower() or "debug" in content.lower()


def test_desktop_main_js_shim_is_compatibility_entry():
    compat = RUNTIME_AUTHORITY_CONTRACT["compatibility_entries"]
    assert "geuldobi-desktop/main.js" in compat
    assert compat["geuldobi-desktop/main.js"] == "legacy_shim"

    content = (ROOT / "geuldobi-desktop" / "main.js").read_text(encoding="utf-8")
    assert "shim" in content.lower() or "compatibility" in content.lower()


def test_lite_mode_and_test_mode_are_compatibility_entries():
    compat = RUNTIME_AUTHORITY_CONTRACT["compatibility_entries"]
    assert "lite_mode/" in compat
    assert compat["lite_mode/"] == "maintenance_only"
    assert "test_mode/" in compat
    assert compat["test_mode/"] == "maintenance_only"


def test_boot_and_runtime_log_authority_distinct():
    boot_surfaces = RUNTIME_AUTHORITY_CONTRACT["boot_log_surfaces"]
    assert boot_surfaces["desktop_pre_bridge"]["path"].endswith("electron-main.log")
    assert boot_surfaces["desktop_pre_bridge"]["authority"] == "desktop_local_appdata"
    assert boot_surfaces["engine_bootstrap_fallback"]["path"] == "logs/error.log"
    assert boot_surfaces["engine_bootstrap_fallback"]["authority"] == "workspace_level"
    assert RUNTIME_AUTHORITY_CONTRACT["runtime_log_authority"] == "project_local"


def test_runtime_authority_contract_matches_packaged_electron_entry():
    package_json = json.loads((ROOT / "geuldobi-desktop" / "package.json").read_text(encoding="utf-8"))
    assert package_json["main"] == "src/main.js"
    assert RUNTIME_AUTHORITY_CONTRACT["supported_entry"] == "geuldobi-desktop/src/main.js"


def test_runtime_authority_summary_round_trips_contract():
    summary = build_runtime_authority_summary()
    assert summary["supported_entry"] == RUNTIME_AUTHORITY_CONTRACT["supported_entry"]
    assert summary["boot_log_surfaces"]["engine_bootstrap_fallback"]["path"] == "logs/error.log"


def test_control_plane_authority_has_authoritative_sinks():
    sinks = CONTROL_PLANE_AUTHORITY_CONTRACT["authoritative_sinks"]
    assert isinstance(sinks, dict) and len(sinks) >= 1
    assert "control_plane_provenance" in sinks


def test_control_plane_authority_has_companion_snapshots():
    companions = CONTROL_PLANE_AUTHORITY_CONTRACT["companion_snapshots"]
    assert isinstance(companions, dict) and len(companions) >= 3
    for key, description in companions.items():
        assert "not durable authority" in description.lower() or "not durable" in description.lower()


def test_control_plane_authority_has_compatibility_paths():
    compat = CONTROL_PLANE_AUTHORITY_CONTRACT["compatibility_paths"]
    assert isinstance(compat, dict) and len(compat) >= 1
    assert "INTERNAL_STAGE0_SUB_KEYS" in compat


def test_public_run_keys_are_present():
    assert isinstance(PUBLIC_RUN_KEYS, frozenset)
    assert len(PUBLIC_RUN_KEYS) >= 5


def test_control_plane_authority_role_lookup_matches_contract():
    assert get_control_plane_authority_role("/status") == AUTHORITY_ROLE_COMPANION_SNAPSHOT
    assert get_control_plane_authority_role("/quality/summary") == AUTHORITY_ROLE_COMPANION_SNAPSHOT
    assert get_control_plane_authority_role("control_plane_provenance") == AUTHORITY_ROLE_AUTHORITATIVE_SINK


def test_control_plane_authority_summary_round_trips_contract():
    summary = build_control_plane_authority_summary()
    assert summary["authoritative_sinks"]["control_plane_provenance"] == "logs/control-plane-provenance.jsonl"
    assert summary["companion_snapshots"]["/quality/summary"].startswith("read-only subset")
