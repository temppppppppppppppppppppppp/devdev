import json
from pathlib import Path


ROOT = Path(".")
PACKAGE_JSON = json.loads((ROOT / "geuldobi-desktop/package.json").read_text(encoding="utf-8"))
PROMPT_MAP = json.loads((ROOT / "docs/implementation/prompt-map-v1.json").read_text(encoding="utf-8"))
API_CONTRACT = (ROOT / "docs/implementation/api-contract-v1.yaml").read_text(encoding="utf-8")


def test_desktop_package_test_script_is_not_placeholder():
    script = PACKAGE_JSON["scripts"]["test"]
    assert "No tests configured" not in script
    assert "test_run_validator.py" in script
    assert "test_api_contract.py" in script
    assert "test_frontend_frontier_lag_wiring.py" in script
    assert "test_ui_renderer_sanitization.py" in script


def test_prompt_map_and_api_contract_include_key_7():
    assert "7" in PROMPT_MAP["keys"]
    assert "'7'" in API_CONTRACT


def test_frontier_lag_prompt_schema_matches_one_stop_shape():
    onestop = PROMPT_MAP["keys"]["6"]
    frontier = PROMPT_MAP["keys"]["7"]
    assert frontier["requires_sub_key"] is False
    assert frontier["steps"] == onestop["steps"]
