import re
from pathlib import Path
from urllib.parse import urlsplit

import yaml


ROOT = Path(__file__).resolve().parents[1]
API_CONTRACT = yaml.safe_load(
    (ROOT / "docs/implementation/api-contract-v1.yaml").read_text(encoding="utf-8")
)
INDEX_HTML = (ROOT / "geuldobi-desktop/src/index.html").read_text(encoding="utf-8")
SPLASH_HTML = (ROOT / "geuldobi-desktop/src/splash/splash.html").read_text(encoding="utf-8")
SPLASH_JS = (ROOT / "geuldobi-desktop/src/splash/splash.js").read_text(encoding="utf-8")
PRELOAD_JS = (ROOT / "geuldobi-desktop/src/preload.js").read_text(encoding="utf-8")
MAIN_JS = (ROOT / "geuldobi-desktop/src/main.js").read_text(encoding="utf-8")
CONTROL_PLANE_JS = (ROOT / "geuldobi-desktop/src/desktop_control_plane_contract.js").read_text(encoding="utf-8")


def _network_contract() -> dict:
    return API_CONTRACT["x-renderer-network-surfaces"]


def _parse_connect_src(html: str) -> frozenset[str]:
    match = re.search(r"connect-src ([^;\"]+);", html)
    assert match, "connect-src directive not found"
    return frozenset(match.group(1).split())


def _extract_direct_surfaces() -> dict[str, dict[str, str]]:
    status_base_match = re.search(r'const STATUS_BASE_URL = "([^\"]+)";', MAIN_JS)
    assert status_base_match, "STATUS_BASE_URL not found"
    status_base_url = status_base_match.group(1)

    ws_const_match = re.search(r'const EVENTS_WS_URL = "([^\"]+)";', MAIN_JS)
    assert ws_const_match, "EVENTS_WS_URL not found"
    assert "return { wsUrl: EVENTS_WS_URL, httpUrl: STATUS_BASE_URL };" in MAIN_JS
    ws_url = ws_const_match.group(1)
    ws_parts = urlsplit(ws_url)

    google_match = re.search(
        r"https://generativelanguage\.googleapis\.com(?P<path>/v1beta/models)\?key=",
        INDEX_HTML,
    )
    assert google_match, "direct Google API validation fetch not found"

    assert 'fetch(`${statusBaseUrl}/status`' in SPLASH_JS
    assert "new WebSocket(wsUrl)" in INDEX_HTML

    return {
        "splash_status_poll": {
            "owner": "splashWindow",
            "transport": "fetch",
            "origin": status_base_url,
            "path": "/status",
        },
        "runtime_events_stream": {
            "owner": "mainWindow",
            "transport": "websocket",
            "origin": f"{ws_parts.scheme}://{ws_parts.netloc}",
            "path": ws_parts.path,
        },
        "gemini_api_key_validation": {
            "owner": "mainWindow",
            "transport": "fetch",
            "origin": "https://generativelanguage.googleapis.com",
            "path": google_match.group("path"),
        },
    }


def _extract_bridge_managed_routes() -> frozenset[str]:
    route_patterns = {
        "/run": r"bridgeFetch\(BRIDGE_MANAGED_ROUTES\.run,",
        "/stop": r"bridgeFetch\(BRIDGE_MANAGED_ROUTES\.stop",
        "/status": r"bridgeFetch\(BRIDGE_MANAGED_ROUTES\.status\)",
        "/quality/summary": r"BRIDGE_MANAGED_ROUTES\.qualitySummary",
        "/quality/dashboard": r"BRIDGE_MANAGED_ROUTES\.qualityDashboard",
        "/safe-ops/preview": r"BRIDGE_MANAGED_ROUTES\.safeOpsPreview",
        "/quality/review": r"bridgeFetch\(BRIDGE_MANAGED_ROUTES\.qualityReview,",
        "/run/{run_id}/input": r"bridgeFetch\(buildRunInputRoute\(runId\)",
    }
    return frozenset(
        route
        for route, pattern in route_patterns.items()
        if re.search(pattern, MAIN_JS, flags=re.MULTILINE)
    )


def _extract_bridge_preload_methods() -> frozenset[str]:
    methods = {
        "runKey",
        "stopRun",
        "getStatus",
        "getQualitySummary",
        "getQualityDashboard",
        "getSafeOpsPreview",
        "saveQualityReview",
        "resolvePrompt",
    }
    return frozenset(
        method
        for method in methods
        if re.search(rf"\b{re.escape(method)}\s*:", PRELOAD_JS)
    )


def test_approved_direct_surface_inventory_matches_source_code():
    contract = _network_contract()["approved_direct"]
    actual = _extract_direct_surfaces()

    assert set(contract) == set(actual)
    for surface_name, actual_surface in actual.items():
        contract_surface = contract[surface_name]
        assert contract_surface["owner"] == actual_surface["owner"]
        assert contract_surface["transport"] == actual_surface["transport"]
        assert contract_surface["origin"] == actual_surface["origin"]
        assert contract_surface["path"] == actual_surface["path"]
        assert contract_surface["purpose"]
        assert contract_surface["allowed_reason"]
        assert contract_surface["source_files"]
        assert contract_surface["regression_tests"]


def test_bridge_managed_backend_routes_match_main_process_bridge():
    contract = _network_contract()["bridge_managed"]

    assert frozenset(contract["backend_routes"]) == _extract_bridge_managed_routes()
    assert frozenset(contract["preload_methods"]) == _extract_bridge_preload_methods()
    assert "const BRIDGE_MANAGED_ROUTES = Object.freeze" in CONTROL_PLANE_JS
    assert "function buildRunInputRoute(runId)" in CONTROL_PLANE_JS
    assert contract["owner"] == "preload_main_bridge"
    assert contract["purpose"]
    assert contract["allowed_reason"]
    assert contract["regression_tests"]


def test_renderer_csp_connect_src_matches_documented_direct_allowlist():
    contract = _network_contract()
    direct_surfaces = _extract_direct_surfaces()

    main_direct_origins = frozenset(
        surface["origin"]
        for surface in direct_surfaces.values()
        if surface["owner"] == "mainWindow"
    )
    splash_direct_origins = frozenset(
        surface["origin"]
        for surface in direct_surfaces.values()
        if surface["owner"] == "splashWindow"
    )

    assert _parse_connect_src(INDEX_HTML) == frozenset(
        contract["csp_connect_src"]["main_window"]["origins"]
    )
    assert _parse_connect_src(SPLASH_HTML) == frozenset(
        contract["csp_connect_src"]["splash_window"]["origins"]
    )
    assert _parse_connect_src(INDEX_HTML) == main_direct_origins
    assert _parse_connect_src(SPLASH_HTML) == splash_direct_origins
