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
REACT_VENDOR = ROOT / "geuldobi-desktop/src/vendor/react.production.min.js"
REACT_DOM_VENDOR = ROOT / "geuldobi-desktop/src/vendor/react-dom.production.min.js"
QUALITY_REACT_RUNTIME = ROOT / "geuldobi-desktop/src/quality_react_runtime.js"
QUALITY_REACT_HELPERS = ROOT / "geuldobi-desktop/src/quality_react_helpers.js"
QUALITY_PAGE_BOOTSTRAP = ROOT / "geuldobi-desktop/src/quality_page_bootstrap.js"
RENDERER_STATE_REACT_HELPERS = ROOT / "geuldobi-desktop/src/renderer_state_react_helpers.js"
RENDERER_STATE_BOOTSTRAP = ROOT / "geuldobi-desktop/src/renderer_state_bootstrap.js"
QUALITY_REACT_HELPERS_JS = QUALITY_REACT_HELPERS.read_text(encoding="utf-8")
QUALITY_PAGE_BOOTSTRAP_JS = QUALITY_PAGE_BOOTSTRAP.read_text(encoding="utf-8")
RENDERER_STATE_REACT_HELPERS_JS = RENDERER_STATE_REACT_HELPERS.read_text(encoding="utf-8")
RENDERER_STATE_BOOTSTRAP_JS = RENDERER_STATE_BOOTSTRAP.read_text(encoding="utf-8")


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


def _extract_int_constant(source: str, name: str) -> int:
    match = re.search(rf"const {re.escape(name)} = (\d+);", source)
    assert match, f"{name} not found"
    return int(match.group(1))


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


def test_main_process_fallback_preempts_splash_30_second_failure_banner():
    splash_fallback_ms = _extract_int_constant(MAIN_JS, "SPLASH_FALLBACK_MS")
    max_poll_fails = _extract_int_constant(SPLASH_JS, "MAX_POLL_FAILS")

    assert splash_fallback_ms == 8000
    assert max_poll_fails == 30
    assert "fallbackMs: SPLASH_FALLBACK_MS" in MAIN_JS
    assert 'switchToMain("fallback-timeout")' in MAIN_JS
    assert splash_fallback_ms < max_poll_fails * 1000


def test_quality_radar_react_island_is_additive_and_vendor_local():
    assert REACT_VENDOR.exists()
    assert REACT_DOM_VENDOR.exists()
    assert QUALITY_REACT_RUNTIME.exists()
    assert QUALITY_REACT_HELPERS.exists()
    assert QUALITY_PAGE_BOOTSTRAP.exists()
    assert RENDERER_STATE_REACT_HELPERS.exists()
    assert RENDERER_STATE_BOOTSTRAP.exists()
    assert 'src="./vendor/react.production.min.js"' in INDEX_HTML
    assert 'src="./vendor/react-dom.production.min.js"' in INDEX_HTML
    assert 'src="./quality_react_runtime.js"' in INDEX_HTML
    assert 'src="./quality_react_helpers.js"' in INDEX_HTML
    assert 'src="./quality_page_bootstrap.js"' in INDEX_HTML
    assert 'src="./renderer_state_react_helpers.js"' in INDEX_HTML
    assert 'src="./renderer_state_bootstrap.js"' in INDEX_HTML
    assert "window.GeuldobiQualityReactRuntime" in INDEX_HTML
    assert "window.GeuldobiQualityReactRuntime.createRegistry()" in INDEX_HTML
    assert "window.GeuldobiQualityReactHelpers" in INDEX_HTML
    assert "window.GeuldobiQualityPageBootstrap" in INDEX_HTML
    assert "window.GeuldobiRendererStateReactHelpers" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap" in INDEX_HTML
    assert "renderResultSignalAlerts" in QUALITY_REACT_HELPERS_JS
    assert "renderResultSummaryCopy" in QUALITY_REACT_HELPERS_JS
    assert "renderResultIssueList" in QUALITY_REACT_HELPERS_JS
    assert "renderResultActionGrid" in QUALITY_REACT_HELPERS_JS
    assert "renderResultNextAction" in QUALITY_REACT_HELPERS_JS
    assert "renderRetrievalSummaryStrip" in QUALITY_REACT_HELPERS_JS
    assert "renderRetrievalStageGrid" in QUALITY_REACT_HELPERS_JS
    assert "renderRetrievalWarningList" in QUALITY_REACT_HELPERS_JS
    assert "renderRetrievalRecentList" in QUALITY_REACT_HELPERS_JS
    assert "renderQualityTrendSummary" in QUALITY_REACT_HELPERS_JS
    assert "renderQualityCompareBody" in QUALITY_REACT_HELPERS_JS
    assert "renderFailureStageStatsGrid" in QUALITY_REACT_HELPERS_JS
    assert "renderFailurePatternList" in QUALITY_REACT_HELPERS_JS
    assert "renderFailureRangeList" in QUALITY_REACT_HELPERS_JS
    assert "renderSafeOpsGrid" in QUALITY_REACT_HELPERS_JS
    assert "renderCalibrationSummary" in QUALITY_REACT_HELPERS_JS
    assert "renderQualityObservationList" in QUALITY_REACT_HELPERS_JS
    assert "renderQualityAdvisoryList" in QUALITY_REACT_HELPERS_JS
    assert "renderArtifactLadder" in QUALITY_REACT_HELPERS_JS
    assert "renderQualityRadarFoot" in QUALITY_REACT_HELPERS_JS
    assert "renderQualityRadarCards" in QUALITY_REACT_HELPERS_JS
    assert "function renderAgentBoard({" in RENDERER_STATE_REACT_HELPERS_JS
    assert "function renderEventFeed({" in RENDERER_STATE_REACT_HELPERS_JS
    assert "function renderPipelineStrip({" in RENDERER_STATE_REACT_HELPERS_JS
    assert "function scheduleOfficeCanvasResize() {" in INDEX_HTML
    assert "function renderMissionBoardSection({" in RENDERER_STATE_BOOTSTRAP_JS
    assert "function refreshBackendStatusBadge({" in RENDERER_STATE_BOOTSTRAP_JS
    assert "function setStateBadge({" in RENDERER_STATE_BOOTSTRAP_JS
    assert "function setEffectBanner({" in RENDERER_STATE_BOOTSTRAP_JS
    assert "function setLastActionText({" in RENDERER_STATE_BOOTSTRAP_JS
    assert "function buildLogRow({" in RENDERER_STATE_BOOTSTRAP_JS
    assert "function renderMaterialEmpty({" in RENDERER_STATE_BOOTSTRAP_JS
    assert "function buildMaterialFileItem({" in RENDERER_STATE_BOOTSTRAP_JS
    assert "function setWorkspaceView({" in RENDERER_STATE_BOOTSTRAP_JS
    assert "function buildWorkspacePanel({" in RENDERER_STATE_BOOTSTRAP_JS
    assert "function createWorkspaceScaffold({" in RENDERER_STATE_BOOTSTRAP_JS
    assert "function buildProjectActionRow({" in RENDERER_STATE_BOOTSTRAP_JS
    assert "function mountRunWorkspace({" in RENDERER_STATE_BOOTSTRAP_JS
    assert "function mountQualityWorkspace({" in RENDERER_STATE_BOOTSTRAP_JS
    assert "function mountOfficeWorkspace({" in RENDERER_STATE_BOOTSTRAP_JS
    assert "function mountProjectWorkspace({" in RENDERER_STATE_BOOTSTRAP_JS
    assert "function setAccordionCollapsed({" in RENDERER_STATE_BOOTSTRAP_JS
    assert "function toggleAccordionCollapsed({" in RENDERER_STATE_BOOTSTRAP_JS
    assert "function updateGenreGating({" in RENDERER_STATE_BOOTSTRAP_JS
    assert "function setSettingsTab({" in RENDERER_STATE_BOOTSTRAP_JS
    assert "function setSettingsOverlayOpen({" in RENDERER_STATE_BOOTSTRAP_JS
    assert "function setGenreModalOpen({" in RENDERER_STATE_BOOTSTRAP_JS
    assert "function setGenreConfirmModalOpen({" in RENDERER_STATE_BOOTSTRAP_JS
    assert "function setPromptOverlayOpen({" in RENDERER_STATE_BOOTSTRAP_JS
    assert "function setPromptState({" in RENDERER_STATE_BOOTSTRAP_JS
    assert "function setVerdictState({" in RENDERER_STATE_BOOTSTRAP_JS
    assert "function setActionState({" in RENDERER_STATE_BOOTSTRAP_JS
    assert "function pushEventFeed({" in RENDERER_STATE_BOOTSTRAP_JS
    assert "function updateGenreModalState({" in RENDERER_STATE_BOOTSTRAP_JS
    assert "function updateToggleLabels({" in RENDERER_STATE_BOOTSTRAP_JS
    assert "function setLogPanelCollapsed({" in RENDERER_STATE_BOOTSTRAP_JS
    assert "function applyLogFilter({" in RENDERER_STATE_BOOTSTRAP_JS
    assert "function renderInsights(renderers = {})" in QUALITY_PAGE_BOOTSTRAP_JS
    assert "function renderQualityRadarSection({" in QUALITY_PAGE_BOOTSTRAP_JS
    assert "function renderResultSummarySection({" in QUALITY_PAGE_BOOTSTRAP_JS
    assert "function renderRetrievalInspectorSection({" in QUALITY_PAGE_BOOTSTRAP_JS
    assert "function renderSafeOpsPreviewSection({" in QUALITY_PAGE_BOOTSTRAP_JS
    assert "function renderArtifactLadderSection({" in QUALITY_PAGE_BOOTSTRAP_JS
    assert "function renderTrendCompareSection({" in QUALITY_PAGE_BOOTSTRAP_JS
    assert "function renderFailureWatchSection({" in QUALITY_PAGE_BOOTSTRAP_JS
    assert "function renderCalibrationDeskSection({" in QUALITY_PAGE_BOOTSTRAP_JS
    assert "async function refreshSummary({" in QUALITY_PAGE_BOOTSTRAP_JS
    assert "async function loadSafeOpsPreview({" in QUALITY_PAGE_BOOTSTRAP_JS
    assert "function mergeDashboardData(fallback, data)" in QUALITY_PAGE_BOOTSTRAP_JS
    assert "function renderReactTree(container, rootKey, tree)" in INDEX_HTML
    assert "window.GeuldobiQualityReactRuntime?.renderTree" in INDEX_HTML
    assert "function renderSafeOpsGridReact(actionRows = [], emptyText = \"\")" in INDEX_HTML
    assert "function renderQualityRadarReactCards(summary, emptyState = null)" in INDEX_HTML
    assert "function renderQualityRadarFootReact(sentenceCount = 0, hits = [])" in INDEX_HTML
    assert "function renderArtifactLadderReact(artifact, emptyState = null)" in INDEX_HTML
    assert "function renderResultSignalAlertsReact(alerts = [])" in INDEX_HTML
    assert "function renderResultSummaryCopyReact(headline = \"\", reason = \"\")" in INDEX_HTML
    assert "function renderResultIssueListReact(issues = [], emptyText = \"\")" in INDEX_HTML
    assert "function renderResultActionGridReact(cards = [])" in INDEX_HTML
    assert "function renderResultNextActionReact(text = \"\")" in INDEX_HTML
    assert "function renderQualityTrendSummaryReact(chips = [])" in INDEX_HTML
    assert "function renderQualityCompareBodyReact(compareRows = [], emptyText = \"\")" in INDEX_HTML
    assert "function renderFailureStageStatsGridReact(stageStats = [], emptyText = \"\")" in INDEX_HTML
    assert "function renderFailurePatternListReact(items = [], emptyText = \"\")" in INDEX_HTML
    assert "function renderFailureRangeListReact(ranges = [], emptyText = \"\")" in INDEX_HTML
    assert "function renderCalibrationSummaryReact(summaryChips = [])" in INDEX_HTML
    assert "function renderQualityObservationListReact(recentObservations = [], emptyText = \"\")" in INDEX_HTML
    assert "function renderQualityAdvisoryListReact(candidates = [], emptyText = \"\")" in INDEX_HTML
    assert "function renderPipelineStripReact(pipelineOrder = [])" in INDEX_HTML
    assert "function renderAgentBoardReact(agentList = [], activeKeys = [])" in INDEX_HTML
    assert "function renderEventFeedReact(recentEvents = [], emptyText = \"\")" in INDEX_HTML
    assert "function renderRetrievalSummaryStripReact(summaryChips = [])" in INDEX_HTML
    assert "function renderRetrievalStageGridReact(stageRows = [], emptyText = \"\")" in INDEX_HTML
    assert "function renderRetrievalWarningListReact(warnings = [], emptyText = \"\")" in INDEX_HTML
    assert "function renderRetrievalRecentListReact(recentRows = [], emptyText = \"\")" in INDEX_HTML
    assert 'renderReactTree(\n          safeOpsGrid,\n          "safeOpsGrid",' in INDEX_HTML
    assert 'renderReactTree(\n          qualityRadar,\n          "qualityRadar",' in INDEX_HTML
    assert 'renderReactTree(\n          qualityRadarFoot,\n          "qualityRadarFoot",' in INDEX_HTML
    assert 'renderReactTree(\n          artifactLadderGrid,\n          "artifactLadderGrid",' in INDEX_HTML
    assert 'renderReactTree(\n          resultSignalAlerts,\n          "resultSignalAlerts",' in INDEX_HTML
    assert 'renderReactTree(\n          resultSummaryHeadline,\n          "resultSummaryHeadline",' in INDEX_HTML
    assert 'renderReactTree(\n          resultSummaryReason,\n          "resultSummaryReason",' in INDEX_HTML
    assert 'renderReactTree(\n          resultIssueList,\n          "resultIssueList",' in INDEX_HTML
    assert 'renderReactTree(\n          resultActionGrid,\n          "resultActionGrid",' in INDEX_HTML
    assert 'renderReactTree(\n          resultNextAction,\n          "resultNextAction",' in INDEX_HTML
    assert 'renderReactTree(\n          qualityTrendSummary,\n          "qualityTrendSummary",' in INDEX_HTML
    assert 'renderReactTree(\n          qualityCompareBody,\n          "qualityCompareBody",' in INDEX_HTML
    assert 'renderReactTree(\n          stageStatsGrid,\n          "stageStatsGrid",' in INDEX_HTML
    assert 'renderReactTree(\n          failurePatternList,\n          "failurePatternList",' in INDEX_HTML
    assert 'renderReactTree(\n          failureRangeList,\n          "failureRangeList",' in INDEX_HTML
    assert 'renderReactTree(\n          calibrationSummary,\n          "calibrationSummary",' in INDEX_HTML
    assert 'renderReactTree(\n          qualityObservationList,\n          "qualityObservationList",' in INDEX_HTML
    assert 'renderReactTree(\n          qualityAdvisoryList,\n          "qualityAdvisoryList",' in INDEX_HTML
    assert "renderTree(container, rootKey" in RENDERER_STATE_REACT_HELPERS_JS
    assert 'renderReactTree(\n          retrievalSummaryStrip,\n          "retrievalSummaryStrip",' in INDEX_HTML
    assert 'renderReactTree(\n          retrievalStageGrid,\n          "retrievalStageGrid",' in INDEX_HTML
    assert 'renderReactTree(\n          retrievalWarningList,\n          "retrievalWarningList",' in INDEX_HTML
    assert 'renderReactTree(\n          retrievalRecentList,\n          "retrievalRecentList",' in INDEX_HTML
    assert "!renderSafeOpsGridReact(actionRows, \"운영 작업 preview가 아직 없습니다.\")" in INDEX_HTML
    assert "if (renderQualityRadarReactCards(summary)) {" in INDEX_HTML
    assert "if (renderQualityRadarFootReact(sentenceCount, hits)) {" in INDEX_HTML
    assert "if (renderArtifactLadderReact(artifact)) {" in INDEX_HTML
    assert "if (!renderResultSignalAlertsReact(alerts)) {" in INDEX_HTML
    assert "!renderResultSummaryCopyReact(" in INDEX_HTML
    assert "if (!renderResultIssueListReact([], \"이번 화의 핵심 이슈 3개가 여기에 표시됩니다.\")) {" in INDEX_HTML
    assert "!renderResultActionGridReact([" in INDEX_HTML
    assert "!renderResultNextActionReact(" in INDEX_HTML
    assert "if (!renderQualityTrendSummaryReact(chips)) {" in INDEX_HTML
    assert "!renderQualityCompareBodyReact(compareRows, \"최근 회차 비교 데이터가 아직 없습니다.\")" in INDEX_HTML
    assert "!renderFailureStageStatsGridReact(stageStats, \"Stage별 pass rate / avg score가 누적되면 여기에 표시됩니다.\")" in INDEX_HTML
    assert "!renderFailurePatternListReact(topTypes || [], \"주요 실패 패턴이 아직 충분히 쌓이지 않았습니다.\")" in INDEX_HTML
    assert "!renderFailureRangeListReact(ranges, \"회차 구간별 실패 경향이 아직 없습니다.\")" in INDEX_HTML
    assert "if (!renderCalibrationSummaryReact(summaryChips)) {" in INDEX_HTML
    assert "!renderQualityObservationListReact(" in INDEX_HTML
    assert "!renderQualityAdvisoryListReact(" in INDEX_HTML
    assert "if (!renderRetrievalSummaryStripReact(summaryChips)) {" in INDEX_HTML
    assert "!renderRetrievalStageGridReact(stageRows, \"Stage별 retrieval 관측이 아직 없습니다.\")" in INDEX_HTML
    assert "!renderRetrievalWarningListReact(" in INDEX_HTML
    assert "if (!renderRetrievalRecentListReact(recent, \"최근 retrieval 샘플이 아직 없습니다.\")) {" in INDEX_HTML
    assert "window.GeuldobiQualityPageBootstrap?.renderInsights" in INDEX_HTML
    assert "window.GeuldobiQualityPageBootstrap?.renderQualityRadarSection" in INDEX_HTML
    assert "window.GeuldobiQualityPageBootstrap?.renderResultSummarySection" in INDEX_HTML
    assert "window.GeuldobiQualityPageBootstrap?.renderRetrievalInspectorSection" in INDEX_HTML
    assert "window.GeuldobiQualityPageBootstrap?.renderSafeOpsPreviewSection" in INDEX_HTML
    assert "window.GeuldobiQualityPageBootstrap?.renderArtifactLadderSection" in INDEX_HTML
    assert "window.GeuldobiQualityPageBootstrap?.renderTrendCompareSection" in INDEX_HTML
    assert "window.GeuldobiQualityPageBootstrap?.renderFailureWatchSection" in INDEX_HTML
    assert "window.GeuldobiQualityPageBootstrap?.renderCalibrationDeskSection" in INDEX_HTML
    assert "window.GeuldobiQualityPageBootstrap?.refreshSummary" in INDEX_HTML
    assert "window.GeuldobiQualityPageBootstrap?.loadSafeOpsPreview" in INDEX_HTML
    assert "window.GeuldobiRendererStateReactHelpers?.renderPipelineStrip" in INDEX_HTML
    assert "window.GeuldobiRendererStateReactHelpers?.renderAgentBoard" in INDEX_HTML
    assert "window.GeuldobiRendererStateReactHelpers?.renderEventFeed" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap?.renderMissionBoardSection" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap?.refreshBackendStatusBadge" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap?.setStateBadge" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap?.setEffectBanner" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap?.setLastActionText" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap?.buildLogRow" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap?.renderMaterialEmpty" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap?.buildMaterialFileItem" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap?.setWorkspaceView" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap?.buildWorkspacePanel" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap?.createWorkspaceScaffold" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap?.buildProjectActionRow" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap?.mountRunWorkspace" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap?.mountQualityWorkspace" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap?.mountOfficeWorkspace" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap?.mountProjectWorkspace" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap?.setAccordionCollapsed" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap?.toggleAccordionCollapsed" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap?.updateGenreGating" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap?.setSettingsTab" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap?.setSettingsOverlayOpen" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap?.setGenreModalOpen" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap?.setGenreConfirmModalOpen" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap?.setPromptOverlayOpen" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap?.setPromptState" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap?.setVerdictState" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap?.setActionState" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap?.pushEventFeed" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap?.updateGenreModalState" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap?.updateToggleLabels" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap?.setLogPanelCollapsed" in INDEX_HTML
    assert "window.GeuldobiRendererStateBootstrap?.applyLogFilter" in INDEX_HTML
    assert 'if (viewName === "office") {' in INDEX_HTML
    assert "scheduleOfficeCanvasResize();" in INDEX_HTML
    assert "requestAnimationFrame(() => {" in INDEX_HTML
    assert "const empty = document.createElement(\"div\");" in INDEX_HTML
