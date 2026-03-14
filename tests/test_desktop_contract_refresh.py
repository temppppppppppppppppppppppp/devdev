import json
import re
from pathlib import Path

import yaml

from modules.api.control_plane_contract import INTERNAL_UI_ACTION_KEYS, PUBLIC_RUN_KEYS
from modules.api.process_runner import MODE_B_KEYS


ROOT = Path(".")
PACKAGE_JSON = json.loads((ROOT / "geuldobi-desktop/package.json").read_text(encoding="utf-8"))
PROMPT_MAP = json.loads((ROOT / "docs/implementation/prompt-map-v1.json").read_text(encoding="utf-8"))
API_CONTRACT = yaml.safe_load((ROOT / "docs/implementation/api-contract-v1.yaml").read_text(encoding="utf-8"))
INDEX_HTML = (ROOT / "geuldobi-desktop/src/index.html").read_text(encoding="utf-8")
DESKTOP_GUIDE = (ROOT / "geuldobi-desktop/DESKTOP-GUIDE.md").read_text(encoding="utf-8")

OFFICIAL_DESKTOP_GATE_CHECKS = (
    "tests/test_run_validator.py",
    "tests/test_api_contract.py",
    "tests/test_frontend_frontier_lag_wiring.py",
    "tests/test_frontend_stage0_connectivity.py",
    "tests/test_ui_renderer_sanitization.py",
    "tests/test_desktop_contract_refresh.py",
    "tests/test_desktop_work_guard_template_contract.py",
    "tests/test_process_runner_stage0_inputs.py",
    "tests/test_bridge_server_http_contract.py",
    "tests/test_bridge_server_desktop_risk_gate.py",
    "tests/test_bridge_quality_summary.py",
    "tests/test_desktop_direct_surface_contract.py",
    "tests/test_desktop_transport_contract.py",
    "tests/test_desktop_packaging_contract.py",
    "tests/test_desktop_shadow_hygiene.py",
    "tests/test_runtime_paths.py",
    "node tests/test_desktop_preload_bridge_behavior.js",
    "node tests/test_desktop_material_offline_behavior.js",
    "node tests/test_splash_runtime_behavior.js",
)


def _desktop_public_run_keys() -> frozenset[str]:
    return frozenset(re.findall(r'data-key="(\d+)"', INDEX_HTML))


def _api_contract_run_keys() -> frozenset[str]:
    return frozenset(
        API_CONTRACT["components"]["schemas"]["RunRequest"]["properties"]["key"]["enum"]
    )


def test_desktop_package_test_script_covers_official_live_surface_gate():
    script = PACKAGE_JSON["scripts"]["test"]
    assert "No tests configured" not in script
    for gate_check in OFFICIAL_DESKTOP_GATE_CHECKS:
        assert gate_check in script


def test_desktop_runtime_proof_commands_are_kept_in_package_and_guide():
    assert "start:spike" in PACKAGE_JSON["scripts"]
    assert "SPIKE_AUTOCLOSE_MS=5000" in PACKAGE_JSON["scripts"]["start:spike"]
    assert "npm test" in DESKTOP_GUIDE
    assert "npm run start:spike" in DESKTOP_GUIDE


def test_public_run_key_inventory_is_aligned_across_contract_surfaces():
    assert frozenset(PROMPT_MAP["keys"]) == PUBLIC_RUN_KEYS
    assert _api_contract_run_keys() == PUBLIC_RUN_KEYS
    assert _desktop_public_run_keys() == PUBLIC_RUN_KEYS
    assert MODE_B_KEYS == PUBLIC_RUN_KEYS


def test_internal_exit_action_is_not_exposed_as_public_run_key():
    assert PROMPT_MAP["internal_actions"] == {"5": {"ui_only_action": "exit_app"}}
    assert INTERNAL_UI_ACTION_KEYS == {"5": "exit_app"}
    assert "5" not in PROMPT_MAP["keys"]
    assert "5" not in _api_contract_run_keys()
    assert "5" not in _desktop_public_run_keys()
    assert "5" not in MODE_B_KEYS


def test_frontier_lag_key_7_is_present_in_public_contract_and_runner_mode_b():
    assert "7" in PROMPT_MAP["keys"]
    assert "7" in _api_contract_run_keys()
    assert "7" in _desktop_public_run_keys()
    assert "7" in MODE_B_KEYS


def test_frontier_lag_prompt_schema_matches_one_stop_shape():
    onestop = PROMPT_MAP["keys"]["6"]
    frontier = PROMPT_MAP["keys"]["7"]
    assert frontier["requires_sub_key"] is False
    assert frontier["steps"] == onestop["steps"]
