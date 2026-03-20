import json
import re
import subprocess
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
MAIN_JS_PATH = ROOT / "geuldobi-desktop/src/main.js"
MAIN_JS = (ROOT / "geuldobi-desktop/src/main.js").read_text(encoding="utf-8")
MAIN_A = (ROOT / "main_a.py").read_text(encoding="utf-8")
GENRE_CONFIG_DIR = ROOT / "config" / "genres"

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


def _extract_cli_contract(source: str, *, anchor: str) -> tuple[int, dict[str, int]]:
    start = source.index(anchor)
    default_match = re.search(r"defaultGenreIndex:\s*(\d+)", source[start:])
    map_match = re.search(
        r"genreIndexMap:\s*(?:Object\.freeze\()?\{(?P<body>[^}]+)\}",
        source[start:],
        flags=re.S,
    )
    assert default_match, f"defaultGenreIndex not found near {anchor!r}"
    assert map_match, f"genreIndexMap not found near {anchor!r}"
    pairs = re.findall(r"([a-z_]+)\s*:\s*(\d+)", map_match.group("body"))
    return int(default_match.group(1)), {genre: int(index) for genre, index in pairs}


def _extract_engine_genre_index_map() -> dict[str, int]:
    index_to_const: dict[int, str] = {}
    current_index: int | None = None
    in_genres_block = False
    for line in MAIN_A.splitlines():
        if "genres = {" in line:
            in_genres_block = True
            continue
        if not in_genres_block:
            continue
        if line.strip() == "}":
            break
        index_match = re.match(r'\s*"(\d+)":\s*\{', line)
        if index_match:
            current_index = int(index_match.group(1))
            continue
        type_match = re.search(r'"type":\s*GenreTypes\.([A-Z_]+),', line)
        if current_index is not None and type_match:
            index_to_const[current_index] = type_match.group(1)
            current_index = None

    const_to_slug = {
        match.group(1): match.group(2)
        for match in re.finditer(r'GenreTypes\.([A-Z_]+):\s*"([a-z_]+)"', MAIN_A)
    }
    return {
        const_to_slug[genre_const]: index
        for index, genre_const in sorted(index_to_const.items())
    }


def _run_main_guardrail_helper(expression: str):
    script = f"""
const fs = require("fs");
const vm = require("vm");
const source = fs.readFileSync({json.dumps(str(MAIN_JS_PATH))}, "utf8");
const start = source.indexOf("const DESKTOP_PUBLIC_RUN_KEYS = Object.freeze([");
const end = source.indexOf("let mainWindow = null;", start);
if (start < 0 || end < 0) {{
  throw new Error("desktop main guardrail helpers not found");
}}
const helperSource = source.slice(start, end).trim();
const context = {{
  Buffer,
  DESKTOP_BRIDGE_TRANSPORT: {{ envelopeVersion: "desktop_bridge_v1" }},
  BRIDGE_MANAGED_ROUTES: {{ run: "/run" }},
}};
vm.runInNewContext(helperSource + "\\nthis.__result = " + {json.dumps(expression)} + ";", context);
process.stdout.write(JSON.stringify(context.__result));
"""
    completed = subprocess.run(
        ["node", "-e", script],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(completed.stdout)


def test_desktop_package_test_script_covers_official_live_surface_gate():
    script = PACKAGE_JSON["scripts"]["test"]
    explicit_alias = PACKAGE_JSON["scripts"]["test:desktop-contract"]
    assert "No tests configured" not in script
    assert explicit_alias == script
    for gate_check in OFFICIAL_DESKTOP_GATE_CHECKS:
        assert gate_check in script


def test_desktop_runtime_proof_commands_are_kept_in_package_and_guide():
    assert "start:spike" in PACKAGE_JSON["scripts"]
    assert "start:desktop-spike" in PACKAGE_JSON["scripts"]
    assert "SPIKE_AUTOCLOSE_MS=5000" in PACKAGE_JSON["scripts"]["start:spike"]
    assert PACKAGE_JSON["scripts"]["start:desktop-spike"] == PACKAGE_JSON["scripts"]["start:spike"]
    assert "npm test" in DESKTOP_GUIDE
    assert "npm run test:desktop-contract" in DESKTOP_GUIDE
    assert "npm run start:spike" in DESKTOP_GUIDE
    assert "npm run start:desktop-spike" in DESKTOP_GUIDE


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


def test_desktop_cli_contract_genre_map_matches_engine_and_genre_config_inventory():
    main_default, main_genre_map = _extract_cli_contract(
        MAIN_JS,
        anchor="const CLI_CONTRACT = Object.freeze({",
    )
    renderer_default, renderer_genre_map = _extract_cli_contract(
        INDEX_HTML,
        anchor="let cliContract = {",
    )
    engine_genre_map = _extract_engine_genre_index_map()
    config_genre_keys = {
        path.stem
        for path in GENRE_CONFIG_DIR.glob("*.yaml")
    }

    assert main_default == 3
    assert renderer_default == main_default
    assert renderer_genre_map == main_genre_map
    assert main_genre_map == engine_genre_map
    assert config_genre_keys == set(main_genre_map)


def test_desktop_main_guardrails_match_public_run_contract_and_settings_limit():
    assert "const SETTINGS_PAYLOAD_MAX_BYTES = 1024 * 1024;" in MAIN_JS
    assert "const DESKTOP_PUBLIC_RUN_KEYS = Object.freeze([\"0\", \"1\", \"2\", \"3\", \"4\", \"6\", \"7\", \"44\", \"77\", \"88\", \"99\"]);" in MAIN_JS

    allowed = _run_main_guardrail_helper(
        "({ allowed: isAllowedDesktopRunKey('44'), denied: isAllowedDesktopRunKey('5') })"
    )
    assert allowed == {"allowed": True, "denied": False}
    assert PUBLIC_RUN_KEYS == frozenset(_run_main_guardrail_helper("DESKTOP_PUBLIC_RUN_KEYS"))

    invalid_key = _run_main_guardrail_helper(
        "buildDesktopGuardError('INVALID_KEY', \"Key '5' is not allowed.\", '/run')"
    )
    assert invalid_key["code"] == "INVALID_KEY"
    assert invalid_key["data"]["backend_code"] == "INVALID_KEY"
    assert invalid_key["data"]["transport_status"] == 400

    oversized = _run_main_guardrail_helper(
        "serializeDesktopSettingsPayload({ payload: 'x'.repeat(1024 * 1024) })"
    )
    assert oversized["ok"] is False
    assert oversized["code"] == "SETTINGS_PAYLOAD_TOO_LARGE"
