# Tranche E — Operator Surface and App Shell: Global Survey Draft

**Status:** DRAFT / NOT AUTHORITY / COLLECTOR ONLY / NO EXECUTION AUTHORITY
**Date:** 2026-03-20
**Terminal:** 4
**Mode:** survey-only, side-effects included
**Baseline Commit:** d0fa70f1 (dirty — see git status)

---

## 1. Scope

### Included

- `geuldobi-desktop/` — Electron app shell, preload, IPC, renderer, splash, vendor, sprites
- `UI/` — legacy asset staging directory
- `modules/api/bridge_server.py` — Python FastAPI backend bridge
- `modules/core/studio_visualizer.py` — Rich console operator output
- `modules/core/services/ui_service.py` — CLI operator input
- `modules/core/quality_dashboard.py` — quality metrics surface
- `modules/core/spinners.py` — animated operator feedback
- `config/prompts/*.yaml` — operator-visible prompt templates
- `docs/implementation/desktop-ipc-surface-contract-v1.json` — IPC authority contract
- Desktop-related tests in `tests/` — TF evidence
- `docs/2026-03-13/shipping-reality-live-surface-guide.md` — shipping freeze reference

### Excluded

- `main_a.py` runtime internals (covered by Tranche B)
- `modules/core/` non-operator internal pipeline (covered by Tranche C)
- `modules/domain/agents/` agent internals (Tranche C)
- Persistence/DB internals (Tranche D)
- `scripts/`, `tests/` as primary targets (Tranche F/G)
- `.git/`, `__pycache__/`, `.venv/`, `node_modules/`

---

## 2. Operator Surface Inventory

### 2.1 Desktop App (Primary Operator Interface)

| Surface | File | Lines | Role |
|---------|------|-------|------|
| Electron main process | `geuldobi-desktop/src/main.js` | 1,237 | Window management, backend lifecycle, IPC routing, settings persistence |
| Preload bridge | `geuldobi-desktop/src/preload.js` | 91 | Context-isolated IPC exposure to renderer |
| Main UI | `geuldobi-desktop/src/index.html` | ~10,082 | Full operator dashboard: topbar, workspace nav, run/office/quality/project views |
| Control plane contract | `geuldobi-desktop/src/desktop_control_plane_contract.js` | 98 | IPC channel definitions, bridge-managed route map |
| Bridge client | `geuldobi-desktop/src/desktop_bridge_client.js` | 62 | Renderer-side bridge validation utilities |
| Console relay | `geuldobi-desktop/src/console_relay.js` | 56 | Renderer warn/error relay to main debug log |
| Quality bootstrap | `geuldobi-desktop/src/quality_page_bootstrap.js` | 916 | Quality dashboard: radar, result summary, retrieval, safe-ops, trends, failures, calibration |
| Quality React helpers | `geuldobi-desktop/src/quality_react_helpers.js` | 769 | React card components for quality rendering |
| Quality React runtime | `geuldobi-desktop/src/quality_react_runtime.js` | 30 | React 18 dual-API bridge (legacy render + createRoot) |
| State bootstrap | `geuldobi-desktop/src/renderer_state_bootstrap.js` | 661 | Live state: mission board, agent sprites, event feed, pipeline strip, prompt resolver |
| State React helpers | `geuldobi-desktop/src/renderer_state_react_helpers.js` | 181 | Agent board, event feed, pipeline strip React components |
| Splash HTML | `geuldobi-desktop/src/splash/splash.html` | 27 | Startup splash screen |
| Splash JS | `geuldobi-desktop/src/splash/splash.js` | 89 | Backend readiness polling (1s interval, max 30 failures) |
| Splash CSS | `geuldobi-desktop/src/splash/splash.css` | 84 | Splash styling with loading animation |
| Lucide icons | `geuldobi-desktop/src/splash/lucide.js` | 19,306 | Vendored icon library |
| React vendor | `geuldobi-desktop/src/vendor/react.production.min.js` | — | React 18.3.1 minified |
| ReactDOM vendor | `geuldobi-desktop/src/vendor/react-dom.production.min.js` | — | ReactDOM 18.3.1 minified |
| Sprites | `geuldobi-desktop/src/sprites/` (27 PNGs) | — | Agent avatars (analyst/critic/director/manager/writer) + office environment |
| Root main.js shim | `geuldobi-desktop/main.js` | 9 | Legacy compatibility shim → `./src/main.js` |
| Root preload.js shim | `geuldobi-desktop/preload.js` | 7 | Legacy compatibility shim → `./src/preload.js` |

**Total desktop JS (excluding vendor/lucide):** ~4,100 lines

### 2.2 Python CLI Operator Surfaces

| Surface | File | Approx Lines | Role |
|---------|------|-------------|------|
| Studio Visualizer | `modules/core/studio_visualizer.py` | ~400 | Rich console panels, agent messages, HUD tables, menus, spinners |
| UI Service | `modules/core/services/ui_service.py` | 296 | Bible/treatment selection, int/choice input, confirm/pause |
| Quality Dashboard | `modules/core/quality_dashboard.py` | ~1,272 | Stage stats, trend analysis, regression detection, bias audit, retrieval summary |
| Spinners | `modules/core/spinners.py` | ~300 | Animated stage spinners with themed emoji + verb cycles |

### 2.3 Backend Bridge (API Layer)

| Surface | File | Lines | Role |
|---------|------|-------|------|
| Bridge server | `modules/api/bridge_server.py` | ~2,320 | FastAPI on port 8300: /run, /stop, /status, /events WS, /quality/*, /safe-ops/preview |

### 2.4 Legacy Asset Directory

| Surface | Path | Contents |
|---------|------|----------|
| UI/ | `UI/` | ~337 MB of graphic assets: RPG Maker tilesets, character generator, interior tiles. NOT operator-facing code. Pure asset staging. |

---

## 3. Desktop/App Shell Map

### 3.1 Architecture

```
Electron Main Process (src/main.js, 1237 lines)
 ├── Backend Process Management (startBackend / stopBackend)
 │   ├── DEV:  python -m uvicorn modules.api.bridge_server:app --port 8300
 │   └── PROD: resources/backend/backend.exe
 ├── Window Management
 │   ├── Splash Window (400x260, frameless, polls /status)
 │   └── Main Window (1100x720, contextIsolation:true, nodeIntegration:false)
 ├── Settings Persistence (%LOCALAPPDATA%/Geuldobi/settings.json + .bak)
 ├── IPC Handlers (25 channels)
 └── Packaged Workspace Seed Sync (first-run non-destructive copy)

Preload Layer (src/preload.js, 91 lines)
 └── contextBridge.exposeInMainWorld("geuldobiDesktop", {...25 methods})

Renderer Process (src/index.html, ~10K lines + 6 JS modules)
 ├── 4 Workspace Views: Run / Office / Quality / Project
 ├── Quality Dashboard (7 insight sections, radar, calibration desk)
 ├── State Manager (officeState object, plain JS mutation)
 ├── WebSocket listener (ws://127.0.0.1:8300/events)
 └── CSS-based view switching (no router library)

Python Backend (modules/api/bridge_server.py, ~2320 lines)
 ├── POST /run (202, spawns ProcessRunner)
 ├── POST /stop (200, idempotent)
 ├── GET  /status (runner state + diagnostics + pending prompts)
 ├── POST /run/{run_id}/input (Mode B prompt resolution)
 ├── GET  /quality/summary
 ├── GET  /quality/dashboard (16-section response)
 ├── GET  /safe-ops/preview
 ├── POST /quality/review (operator observation persistence)
 └── WS   /events (real-time stdout + lifecycle events)
```

### 3.2 Key Constants (from src/main.js)

| Constant | Value | Notes |
|----------|-------|-------|
| STATUS_BASE_URL | `http://127.0.0.1:8300` | Hardcoded, localhost-only |
| EVENTS_WS_URL | `ws://127.0.0.1:8300/events` | WebSocket real-time feed |
| BRIDGE_FETCH_TIMEOUT_MS | 5000 | Per-request fetch timeout |
| SPLASH_FALLBACK_MS | 8000 | Splash → main fallback timer |
| PACKAGED_RUNTIME_MODEL | `"source_bundle_primary"` | Not engine.exe |
| SETTINGS_PAYLOAD_MAX_BYTES | 1,048,576 | 1MB settings size limit |
| DESKTOP_PUBLIC_RUN_KEYS | `["0","1","2","3","4","6","7","44","77","88","99"]` | 11 keys |
| CLI_CONTRACT.defaultGenreIndex | 3 | Investment genre default |
| Max backend restarts | 2 | Dialog after 2 consecutive failures |

### 3.3 Packaged Resources (from package.json `extraResources`)

| From | To | Filter |
|------|----|--------|
| `../dist/backend` | `backend` | Excludes *.log, *.tmp, *.bak |
| `../dist/engine` | `engine` | Excludes *.log, *.tmp, *.bak |
| `../python-embed` | `python-embed` | Excludes *.log, *.tmp, *.bak |
| `../dist/workspace-seed` | `workspace-seed` | Excludes *.log, *.tmp, *.bak |

### 3.4 Package Metadata

- **Name:** geuldobi-desktop
- **Version:** 1.5.7
- **Main entry:** `src/main.js`
- **Type:** commonjs
- **Electron:** ^40.8.0
- **React/ReactDOM:** ^18.3.1 (devDependencies + vendored production builds)
- **Lucide:** ^0.577.0 (runtime dependency)
- **Build target:** Windows NSIS installer
- **App ID:** com.geuldobi.desktop

### 3.5 Content Security Policy (from index.html)

```
default-src 'self';
script-src 'self' 'unsafe-inline';
style-src 'self' 'unsafe-inline';
img-src 'self' data:;
connect-src ws://127.0.0.1:8300 https://generativelanguage.googleapis.com;
```

**Fact:** 3 approved direct network surfaces:
1. `splash_status_poll` — fetch to `/status` (splash window)
2. `runtime_events_stream` — WebSocket to `/events` (main window)
3. `gemini_api_key_validation` — fetch to Google API (main window)

All other backend communication is bridge-managed (via IPC → main process fetch).

### 3.6 Surface Classification

| Classification | Path | Evidence |
|----------------|------|----------|
| **Live (authoritative)** | `geuldobi-desktop/src/main.js` | package.json `"main"`, contract JSON, guide |
| **Shadow (shim)** | `geuldobi-desktop/main.js` | "Legacy compatibility shim only." — re-exports src/main.js |
| **Shadow (shim)** | `geuldobi-desktop/preload.js` | "Compatibility preload shim only." — re-exports src/preload.js |
| **Reference archive** | `UI/` | Graphics staging only, no code |
| **Manual-only** | `lite_mode/`, `test_mode/` | Per shipping freeze note |

---

## 4. Preload / Bridge / IPC Boundary Notes

### 4.1 Live Preload Methods (25 total)

Verified across three independent sources with exact match:
- `desktop-ipc-surface-contract-v1.json` → 25 entries in `live_preload_methods`
- `src/preload.js` → 25 keys in `PRELOAD_METHOD_CHANNELS.live`
- `src/desktop_control_plane_contract.js` → 25 keys in `PRELOAD_METHOD_CHANNELS.live`

| # | Method | Channel | Owner |
|---|--------|---------|-------|
| 1 | getSplashConfig | splash:get-config | splash bootstrap |
| 2 | notifyBackendReady | splash:backend-ready | splash bootstrap |
| 3 | onAppReady | app:ready | desktop handoff |
| 4 | runKey | bridge:run | desktop run control |
| 5 | stopRun | bridge:stop | desktop run control |
| 6 | getStatus | bridge:status | command readiness / reconnect resync |
| 7 | getQualitySummary | bridge:get-quality-summary | quality operator surface |
| 8 | getQualityDashboard | bridge:get-quality-dashboard | quality operator surface |
| 9 | getSafeOpsPreview | bridge:get-safe-ops-preview | safe-op operator surface |
| 10 | saveQualityReview | bridge:save-quality-review | quality operator surface |
| 11 | getBackendUrl | bridge:get-url | renderer websocket bootstrap |
| 12 | getCliContract | bridge:get-cli-contract | stage 0 contract UI |
| 13 | saveSettings | bridge:save-settings | settings persistence |
| 14 | loadSettings | bridge:load-settings | settings persistence |
| 15 | listMaterialFiles | material:list-files | material manager |
| 16 | importMaterialFile | material:import-file | material manager |
| 17 | deleteMaterialFile | material:delete-file | material manager |
| 18 | resolvePrompt | bridge:resolve-prompt | mode-b prompt loop |
| 19 | listProjects | project:list | project selector |
| 20 | createProject | project:create | project selector |
| 21 | loadProjectConfigSurfaces | project:load-config-surfaces | project config surface |
| 22 | saveProjectConfigSurfaces | project:save-config-surfaces | project config surface |
| 23 | listWorkGuardTemplates | project:list-work-guard-templates | work guard template UI |
| 24 | applyWorkGuardTemplate | project:apply-work-guard-template | work guard template UI |
| 25 | openWorkspaceFolder | workspace:open-folder | workspace utility |

**Dead candidate methods:** 0 (empty list in contract JSON)

### 4.2 Bridge-Managed HTTP Routes (7 + 1 builder)

| Key | Route | Method |
|-----|-------|--------|
| run | /run | POST |
| stop | /stop | POST |
| status | /status | GET |
| qualitySummary | /quality/summary | GET |
| qualityDashboard | /quality/dashboard | GET |
| safeOpsPreview | /safe-ops/preview | GET |
| qualityReview | /quality/review | POST |
| (dynamic) | /run/{runId}/input | POST (buildRunInputRoute) |

### 4.3 IPC Transport Contract

| Field | Value |
|-------|-------|
| Envelope version | `desktop_bridge_v1` |
| Network error code | `NETWORK_ERROR` |
| HTTP error format | `HTTP_<status_code>` |
| Request timeout | 5000ms |
| Error payload shape | `{ok, code, message, data: {backend_code, backend_message, transport_status}}` |

### 4.4 WebSocket Event Types

Verified from bridge_server.py `_build_event()` calls:
- `run_started`, `stdout`, `run_completed`, `run_failed`, `run_stopped`
- `prompt_request`, `prompt_resolved`, `prompt_timeout`

Event schema: `{event_version, seq, run_id, type, ts, payload}`

### 4.5 Preload Duplication Note

**Fact:** `src/preload.js` hardcodes all 25 channel strings inline rather than importing from `desktop_control_plane_contract.js`. Comment at line 3: "Sandboxed preload scripts cannot rely on local relative require() in packaged Electron."

**Fact:** Both files define `PRELOAD_METHOD_CHANNELS.live` independently. The control_plane_contract.js builds its map from `IPC_CHANNELS` object; preload.js uses literal strings.

**Inference:** This creates a sync maintenance burden — any channel rename requires updating both files. Currently in perfect sync.

### 4.6 Security Boundaries

| Boundary | Implementation |
|----------|---------------|
| Context isolation | `contextIsolation: true`, `nodeIntegration: false` |
| Run key allowlist | `DESKTOP_PUBLIC_RUN_KEYS` validated before bridge:run handler |
| Path traversal guard | `fileName.includes("..") || fileName.includes("/") || fileName.includes("\\")` → reject |
| Project name sanitize | Whitelist regex: `/[^a-zA-Z0-9가-힣ㄱ-ㅎㅏ-ㅣ_\- ]/g` → underscore; pure dots → reject |
| Settings size limit | 1MB max (`SETTINGS_PAYLOAD_MAX_BYTES`) |
| Risk approval gate | Key "44" in desktop mode requires `approval_id` |
| XSS protection | `escapeHtml()` + `sanitizeToken()` on 30+ dynamic surfaces in index.html |
| CSP | connect-src limited to localhost:8300 + googleapis |

---

## 5. Prompt / Output Path Notes

### 5.1 Desktop Renderer Output Paths

**4 Workspace Views (CSS class toggle, no URL router):**

| View | Key | Contents |
|------|-----|----------|
| Run | `run` | Execution control buttons + live log panel (WebSocket stdout) |
| Office | `office` | Canvas sprite animation + mission board (verdict/score/stage tracking) |
| Quality | `quality` | 7 insight panels: radar (CED/Slop/gzip/Rhythm/Density), result summary, retrieval inspector, safe-ops preview, artifact ladder, trend compare, failure watch, calibration desk + agent board + event feed + pipeline strip |
| Project | `project` | Material accordion (bible/treatments) + settings form (API key, genre, timeout, quality gate, target length) + author directives + work guard YAML |

### 5.2 Quality Dashboard Sections (API → Renderer)

Response from `/quality/dashboard` includes up to 16+ sections:
- quality_summary, quality_signal_snapshot, result_summary
- config_authority_summary, control_plane_authority_summary, runtime_authority_summary
- gate_repair_summary, episode_trend, compare_rows, score_trend
- stage_stats, common_violations, failure_patterns, runtime_health
- proof_status, sink_alignment_summary, runtime_audit_summary
- retrieval_summary, cost_summary, patch_effectiveness
- episode_rol, arc_cost_correlation, calibration

### 5.3 Operator Quality Review Labels

Whitelist-validated labels for `POST /quality/review`:
- "좋음" (Good)
- "경계" (Caution)
- "AI 티" (AI Slip)
- "지나친 단조" (Too Flat)
- "과잉 설명" (Over-Explained)

### 5.4 CLI Console Output (Rich)

| Element | Method | Visual |
|---------|--------|--------|
| Title panel | `studio_visualizer.title()` | Magenta bordered panel |
| Agent message | `studio_visualizer.print_agent()` | Color-coded emoji panel (🧠 Analyst, 🎬 Director, ✍️ Writer, etc.) |
| Status HUD | `studio_visualizer.show_status()` | ROUNDED table: episode, module, seeds |
| Menu | `studio_visualizer.menu()` | Bold yellow numbered items |
| Spinner | `spinners.StageSpinner` | Themed emoji + verb cycle per stage |
| Progress | `studio_visualizer.get_progress_bar()` | Rich ProgressBar with spinner + percentage |

### 5.5 Operator Event Sink Schema

```json
{
  "seq": int,
  "level": "info|warning|error|debug",
  "component": "UI|Stage0|Stage2|Stage3|Stage4|QA",
  "stage": 0-4,
  "event_kind": "log|menu|menu_option|prompt|prompt_response|selection|summary",
  "render_format": "text|menu|prompt|input|selection|summary",
  "message": string,
  "visible": boolean,
  "prompt_id": string,
  "meta": dict
}
```

Events flow: StudioVisualizer → operator_event_sink callback → bridge_server → WS /events → renderer

### 5.6 Settings Persistence

**Path:** `%LOCALAPPDATA%/Geuldobi/settings.json` (+ `.bak` backup)

**Default fields:** apiKey1, extraKeys (obj), slackWebhook, timeout=300, keyRotate=10, qualityGate=90, targetLength=5000, project

**Recovery chain:**
1. Primary OK → use
2. Primary corrupt + backup OK → restore from .bak, log recovery
3. Both corrupt → factory reset to defaults

---

## 6. Side-Effect Sweep

### 6.1 File Writes / Artifact Generation

| Actor | Write Target | Trigger |
|-------|-------------|---------|
| main.js (Electron) | `%LOCALAPPDATA%/Geuldobi/settings.json` | saveSettings IPC |
| main.js (Electron) | `%LOCALAPPDATA%/Geuldobi/settings.json.bak` | Pre-write backup |
| main.js (Electron) | `%LOCALAPPDATA%/Geuldobi/electron-main.log` | Debug logging |
| main.js (Electron) | `{workspace}/bible/`, `{workspace}/treatments/`, `{workspace}/projects/` | First-run seed sync (non-destructive) |
| main.js (Electron) | `{project}/config/author_directives.txt` | saveProjectConfigSurfaces |
| main.js (Electron) | `{project}/config/work_guard.yaml` | saveProjectConfigSurfaces / applyWorkGuardTemplate |
| bridge_server.py | `logs/control-plane-provenance.jsonl` | Run lifecycle events |
| bridge_server.py | `{project}/project_data.db` | Quality review persistence |
| process_runner | subprocess stdout/stderr capture | Runtime |

### 6.2 DB Writes

| Surface | DB | Operation |
|---------|-----|-----------|
| `/quality/review` | `{project}/project_data.db` | INSERT quality observation |
| Quality dashboard read | `{project}/project_data.db` | SELECT only (companion_snapshot role) |

### 6.3 Console/UI Output

- Electron renderer: DOM mutation via React + vanilla JS (no external side effects)
- Rich console: ANSI terminal output (transient)
- WebSocket: broadcast to all connected WS clients

### 6.4 Cache / State Mutation

| Cache | Location | Trigger |
|-------|----------|---------|
| officeState | Renderer memory | WebSocket events, API responses |
| settingsStore | Renderer memory | loadSettings IPC |
| Backend runner state | bridge_server memory | /run, /stop lifecycle |
| Prompt broker | bridge_server memory | /run (Mode B), /run/{id}/input |

### 6.5 Rollback / Recovery

| Scenario | Recovery |
|----------|----------|
| Settings corrupt | Auto-restore from .bak |
| Settings + backup corrupt | Factory reset to defaults |
| Backend 2x restart failure | Dialog: retry or quit |
| Splash 30s poll failure | "백엔드 연결 실패" message (no auto-recovery) |
| Bridge fetch timeout | NETWORK_ERROR code returned to renderer |

### 6.6 Config Mutation

- Settings JSON: overwritten on each save (full replace, not merge)
- Author directives: overwritten on save
- Work guard YAML: overwritten on save or template apply
- No hot-reload; backend restart needed for engine config changes

### 6.7 Not Applicable

- No database schema migration from operator surface
- No JSONL log rotation from operator surface
- No env var mutation at runtime

---

## 7. Facts

These are verified from live code inspection.

1. **F-01** — Desktop version is 1.5.7 (package.json line 3)
2. **F-02** — 25 live preload methods, 0 dead candidates. Verified across JSON contract, preload.js, and control_plane_contract.js — exact match.
3. **F-03** — 7 bridge-managed HTTP routes + 1 dynamic route builder (`buildRunInputRoute`)
4. **F-04** — React 18.3.1 (verified from vendor JS `c.version="18.3.1"`)
5. **F-05** — Root `main.js` and `preload.js` are shims only. Verified: `main.js` = 9 lines, `preload.js` = 7 lines, both re-export `./src/` counterparts.
6. **F-06** — CSP connect-src: `ws://127.0.0.1:8300 https://generativelanguage.googleapis.com` — only two origins.
7. **F-07** — Backend port 8300 is hardcoded in both main.js and splash.js. Not configurable.
8. **F-08** — PACKAGED_RUNTIME_MODEL = `"source_bundle_primary"` — no engine.exe in packaged model.
9. **F-09** — 11 public run keys: 0,1,2,3,4,6,7,44,77,88,99. Key 5 is internal-only (exit_app).
10. **F-10** — Desktop test gate: 19 suites (16 Python + 3 Node.js) in `npm test` and `npm run test:desktop-contract`.
11. **F-11** — `UI/` directory is ~337MB of graphic assets (RPG Maker tilesets, character generator). Contains no operator-facing code.
12. **F-12** — No URL-based routing in renderer. Views switch via CSS class toggle on `.workspace-view[data-view]`.
13. **F-13** — No build step / bundler for renderer JS. All scripts loaded directly via `<script>` tags.
14. **F-14** — Quality React rendering uses dual-mode: checks `global.React` availability, falls back to vanilla DOM if absent.
15. **F-15** — `escapeHtml()` and `sanitizeToken()` protect 30+ dynamic HTML interpolation surfaces.
16. **F-16** — Settings backup chain: primary → .bak → factory defaults. Verified in test_desktop_settings_recovery.py.
17. **F-17** — Preload channel strings are hardcoded inline (not imported from contract module) due to sandboxed packaged Electron limitation.
18. **F-18** — Splash polls /status every 1s, max 30 consecutive failures before showing error message.
19. **F-19** — index.html CSP allows `'unsafe-inline'` for script-src and style-src. This is intentional for React inline rendering.
20. **F-20** — Work guard template system: list templates → select → copy to project config folder.

---

## 8. Inferences

These are derived from evidence but not directly stated in code.

1. **I-01** — The dual PRELOAD_METHOD_CHANNELS definition (preload.js + control_plane_contract.js) creates a maintenance sync risk. Currently in perfect sync, but any channel rename requires coordinated two-file edit. This is an architectural choice due to Electron sandboxing constraints, not a bug.

2. **I-02** — The `'unsafe-inline'` CSP for script-src is a pragmatic choice for the React island pattern (inline createElement calls). Tightening to nonce-based CSP would require a build step, which the project currently avoids.

3. **I-03** — The hardcoded port 8300 means parallel desktop instances would conflict. This appears intentional for single-instance desktop app usage.

4. **I-04** — The 1MB settings size limit (`SETTINGS_PAYLOAD_MAX_BYTES`) is generous for a JSON config file. The actual settings object has ~8 fields. This limit is defensive, not operational.

5. **I-05** — The `UI/` directory at ~337MB appears to be asset staging for sprite/tile generation, not active operator surface. Its classification as "reference archive" in the shipping freeze note is consistent.

6. **I-06** — The quality dashboard's 16-section response structure suggests the API layer is designed to serve a potentially richer future UI. Many sections may return empty/default data for early-stage projects.

7. **I-07** — The bridge_server.py at ~2,320 lines is the largest single file in the operator surface layer. It handles HTTP routing, WebSocket management, process lifecycle, prompt brokering, quality aggregation, and provenance logging. Possible candidate for future decomposition.

8. **I-08** — Backend restart guard (max 2 attempts → dialog) implies the system expects occasional backend crashes but treats 3+ consecutive failures as requiring operator intervention.

---

## 9. Uncertainty / Contradictions

### Contradictions

| ID | Surface | Observation | Severity |
|----|---------|-------------|----------|
| **CTR-01** | DESKTOP-GUIDE.md vs package.json | Guide references "Geuldobi Setup 1.5.6.exe" (lines 106, 112, 153) but package.json version is 1.5.7. Stale version string in documentation. | LOW — cosmetic, documentation only |
| **CTR-02** | TF agent report vs live code | One exploration agent reported "23 live preload methods" and another reported "18-item gate check list". Live code verification shows **25** preload methods and **19** gate checks. The TF test `test_desktop_contract_refresh.py` uses `OFFICIAL_DESKTOP_GATE_CHECKS` with 19 entries (lines 23-43). The contract JSON has 25 entries. No agent report is authoritative; live code is. | INFO — agent report imprecision, not a codebase contradiction |

### Uncertainties

| ID | Surface | Question | Impact |
|----|---------|----------|--------|
| **UNC-01** | Splash fallback timing | main.js `SPLASH_FALLBACK_MS=8000` vs splash.js max poll failures = 30 (30s). The 8s fallback in main.js preempts the 30s splash error. However, the exact interaction between these two timers is not documented inline. | LOW — both paths lead to operator-visible error, just different timing |
| **UNC-02** | Mode B prompt timeout | bridge_server.py handles `prompt_timeout` events, but the exact timeout duration was not found as a constant in the explored surface. May be configured elsewhere. | LOW — operational, not architectural |
| **UNC-03** | `test_desktop_material_offline_behavior.js` and `test_splash_runtime_behavior.js` | These are in the npm test gate (package.json) but were not in the TF exploration agent's file list. Their content was not verified in this survey. | LOW — they exist (listed in package.json) but content not read |
| **UNC-04** | Electron auto-updater | DESKTOP-GUIDE.md section 8 describes `electron-updater` as a future addition ("나중에"). Current package.json has no `electron-updater` dependency. Status: not yet implemented. | INFO — future feature, no current impact |
| **UNC-05** | Gemini API key in CSP | CSP allows `https://generativelanguage.googleapis.com` in connect-src. The direct surface contract test says this is for "gemini_api_key_validation". It's unclear if the renderer makes direct Gemini API calls or if this is only for key validation. | LOW — security surface question |

---

## 10. Candidate Watchlist

| ID | Item | Reason | Watch Category |
|----|------|--------|----------------|
| **W-01** | DESKTOP-GUIDE.md version "1.5.6" → should be "1.5.7" | Stale documentation | stale |
| **W-02** | Dual PRELOAD_METHOD_CHANNELS definition | Maintenance sync risk between preload.js and control_plane_contract.js | uncertain |
| **W-03** | `'unsafe-inline'` in CSP script-src | Pragmatic but weakens CSP. Future build step could enable nonce-based approach | watchlist |
| **W-04** | bridge_server.py size (~2,320 lines) | Largest operator surface file. Combines HTTP routing, WS, process lifecycle, quality aggregation | watchlist |
| **W-05** | Port 8300 hardcoded | No configuration path for port. Parallel instance conflict risk | watchlist |
| **W-06** | No build step for renderer JS | 6 JS modules + vendor loaded via raw script tags. Works but limits future optimization (tree shaking, minification, CSP nonces) | watchlist |
| **W-07** | `test_desktop_material_offline_behavior.js` and `test_splash_runtime_behavior.js` content | In gate but not verified in this survey | uncertain |
| **W-08** | Splash lucide.js at 19,306 lines | Vendored full icon library for single icon usage (pen-line). Could be subset. | watchlist |

---

## 11. TF Evidence Notes

### Tests Used as Evidence (with live code cross-reference status)

| Test File | Key Assertion | Live Code Match |
|-----------|---------------|-----------------|
| `test_desktop_contract_refresh.py` | 19-item gate list; PUBLIC_RUN_KEYS = 11 items across 4 surfaces; genre map stable | MATCH — package.json `test` script contains all 19; index.html data-key attributes match |
| `test_desktop_direct_surface_contract.py` | 3 approved direct surfaces; 7 bridge-managed routes; CSP connect-src locked | MATCH — index.html CSP verified; route map verified in control_plane_contract.js |
| `test_desktop_packaging_contract.py` | PACKAGED_RUNTIME_MODEL = "source_bundle_primary"; workspace-seed folders | MATCH — main.js constant verified; package.json extraResources verified |
| `test_desktop_shadow_hygiene.py` | Root main.js/preload.js are shims only, no ipcMain logic | MATCH — root main.js = 9 lines, preload.js = 7 lines, both re-export only |
| `test_desktop_transport_contract.py` | Envelope "desktop_bridge_v1"; timeout 5000ms; 7+ event types | MATCH — constants verified in main.js |
| `test_desktop_backend_restart_guard.py` | Dialog on 2x restart failure; buttons: retry/quit | NOT VERIFIED — main.js has restart logic but exact dialog wording not independently verified in this survey |
| `test_desktop_project_name_sanitization.py` | Whitelist regex + pure-dot rejection | NOT VERIFIED — sanitizer function exists in main.js but regex not independently extracted |
| `test_desktop_settings_recovery.py` | Primary→backup→factory chain; default values | MATCH — main.js settings handling verified |
| `test_desktop_preload_bridge_behavior.js` | 25 methods in API; frozen bridge facade | MATCH — preload.js has 25 methods; createDesktopBridgeFacade exists in bridge_client.js |
| `test_bridge_quality_summary.py` | authority_role="companion_snapshot"; 16+ dashboard sections | MATCH — bridge_server.py dashboard response structure |
| `test_shipping_reality_live_surface_guide.py` | source_bundle_primary frozen; 1 live + 2 shadow surfaces | MATCH — all three surface files verified |
| `test_bridge_server_http_contract.py` | /status, /run schemas; error codes | NOT INDEPENDENTLY VERIFIED — test uses TestClient mocks |
| `test_bridge_server_desktop_risk_gate.py` | Risk key "44" requires approval_id | NOT INDEPENDENTLY VERIFIED — test uses TestClient mocks |
| `test_ui_renderer_sanitization.py` | escapeHtml + sanitizeToken on 30+ surfaces | MATCH — index.html contains both functions |
| `test_surface_containment_contract.py` | 1 live + 2 shadows + manual-only markers | MATCH — file contents verified |
| `test_desktop_work_guard_template_contract.py` | Template methods in preload + control plane + main | MATCH — listWorkGuardTemplates and applyWorkGuardTemplate in all three |

### TF-to-Live Contradiction Count: **0**

No contradictions found between TF test assertions and live code state for the surfaces verified in this survey.

### Tests in Gate but Not Explored in This Survey

These tests are part of the 19-item npm test gate but cover non-desktop runtime surfaces:
- `test_run_validator.py` — run request validation logic
- `test_api_contract.py` — API schema contract
- `test_frontend_frontier_lag_wiring.py` — frontier mode wiring
- `test_frontend_stage0_connectivity.py` — stage 0 UI connectivity
- `test_process_runner_stage0_inputs.py` — process runner input handling
- `test_runtime_paths.py` — runtime path resolution

These are adjacent to the desktop surface but more properly belong to Tranche B (runtime core) or Tranche H (cross-cutting contracts).

---

## Appendix: File Inventory Summary

| Category | File Count | Total LOC (approx) |
|----------|-----------|---------------------|
| Desktop JS (src/, excluding vendor/lucide) | 10 | ~4,100 |
| Desktop HTML (src/) | 1 | ~10,082 |
| Desktop CSS (splash/) | 1 | 84 |
| Splash (html+js+css) | 3 | ~200 |
| Vendor JS (react + lucide) | 3 | ~19,450 |
| Root shims | 2 | 16 |
| Sprites | 27 PNG files | N/A |
| Python operator surfaces | 4 modules | ~2,270 |
| Bridge server | 1 module | ~2,320 |
| Config/prompts | 9+ YAML files | ~3,000+ |
| Desktop tests (Python) | 13 files | ~4,000+ |
| Desktop tests (Node.js) | 3 files | ~600+ |
| IPC contract JSON | 1 file | 172 |
| Package metadata | 2 files (json + lock) | ~200K |

---

*END OF DRAFT — This document is collector output. It does not declare severity, resolution status, or execution authority.*
