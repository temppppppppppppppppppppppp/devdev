# UI/Desktop Frontend Compact Survey

Date: 2026-03-26
Status: final
Scope: `geuldobi-desktop` renderer/Electron bridge surface and its desktop contract/test envelope
Canonical Path: `docs/2026-03-26/ui-desktop-frontend-compact-survey.md`

Commit State:
- Baseline Commit: `8ffd512defb17b6ff1c01c7995e9cceab49d81cf`
- Baseline Dirty Summary: `clean`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Scope and Evidence

This survey treated the active frontend surface as `geuldobi-desktop`, not the top-level `UI/` asset bundle. The inspection covered:

- renderer entry and inline runtime surface:
  - `geuldobi-desktop/src/index.html`
  - `geuldobi-desktop/src/renderer_state_bootstrap.js`
  - `geuldobi-desktop/src/quality_page_bootstrap.js`
- Electron shell and IPC bridge:
  - `geuldobi-desktop/src/main.js`
  - `geuldobi-desktop/src/preload.js`
  - `geuldobi-desktop/src/desktop_control_plane_contract.js`
  - `geuldobi-desktop/src/desktop_bridge_client.js`
- backend control-plane contract touched by the desktop shell:
  - `modules/api/control_plane_contract.py`
  - `modules/api/bridge_server.py`
  - `modules/api/process_runner.py`
- desktop/frontend regression and contract tests:
  - `tests/test_desktop_direct_surface_contract.py`
  - `tests/test_desktop_transport_contract.py`
  - `tests/test_ui_renderer_sanitization.py`
  - `tests/test_frontend_stage0_connectivity.py`
  - `tests/test_frontend_frontier_lag_wiring.py`
  - `tests/test_desktop_contract_refresh.py`
  - `tests/test_desktop_packaging_contract.py`
  - `tests/test_desktop_preload_bridge_behavior.js`
  - `tests/test_splash_runtime_behavior.js`
- operator-facing desktop guide:
  - `geuldobi-desktop/DESKTOP-GUIDE.md`
  - `geuldobi-desktop/package.json`

Executed validation during this survey:

- `python -m pytest tests/test_desktop_direct_surface_contract.py tests/test_desktop_transport_contract.py tests/test_ui_renderer_sanitization.py tests/test_frontend_stage0_connectivity.py tests/test_frontend_frontier_lag_wiring.py -q`
  - result: `26 passed`
- `npm --prefix geuldobi-desktop run test:desktop-contract`
  - result: `214 passed, 1 failed`
- `node tests/test_desktop_preload_bridge_behavior.js`
  - result: `pass`
- `node tests/test_desktop_material_offline_behavior.js`
  - result: `pass`
- `node tests/test_splash_runtime_behavior.js`
  - result: `pass`

Not executed in this pass:

- `npm run start:spike`
- `npm run start:desktop-spike`
- live packaged build or live Electron handoff proof

## 2. Side-Effect Coverage

Included side-effect surfaces:

- renderer direct network ownership
  - splash `/status` polling
  - main-window WebSocket `/events`
  - direct Google API key validation fetch
- preload IPC exposure and bridge-managed routes
- backend control-plane authority notes for `/status`, `/quality/summary`, `/quality/dashboard`, and `control_plane_provenance`
- settings save/load entrypoints in `main.js`
- packaged runtime/build gate references in `package.json` and `DESKTOP-GUIDE.md`

Not live-validated in this survey:

- actual settings file mutation under `%LOCALAPPDATA%`
- real `workspace:open-folder` operator path
- real splash-to-main runtime handoff

Accordingly, this survey is strong on static contract truth and focused test truth, but not yet on live runtime proof.

## 3. Current Surface Snapshot

- `geuldobi-desktop/src/index.html` remains the dominant renderer owner.
  - measured size in this workspace: about `10083` lines, `153` function declarations
  - inline usage includes `32` `window.geuldobiDesktop.*` bridge calls
- extracted helper modules exist and are additive, not yet a full renderer split:
  - `renderer_state_bootstrap.js`
  - `quality_page_bootstrap.js`
  - `quality_react_helpers.js`
  - `quality_react_runtime.js`
- Electron shell baseline is still sound:
  - `contextIsolation: true`
  - `nodeIntegration: false`
  - preload bridge at `geuldobi-desktop/src/preload.js`
- direct network surface is intentionally limited by contract:
  - splash `fetch http://127.0.0.1:8300/status`
  - main window `ws://127.0.0.1:8300/events`
  - renderer-side Gemini key validation against `https://generativelanguage.googleapis.com`

## 4. Findings

### F1. Official desktop gate is currently red, but the failing point is a stale survey/test parser rather than a proven renderer runtime break

Evidence:

- `npm --prefix geuldobi-desktop run test:desktop-contract` failed at:
  - `tests/test_desktop_contract_refresh.py::test_desktop_cli_contract_genre_map_matches_engine_and_genre_config_inventory`
- the test compares:
  - desktop `CLI_CONTRACT` from `geuldobi-desktop/src/main.js`
  - renderer `cliContract` from `geuldobi-desktop/src/index.html`
  - engine-derived genre map via `_extract_engine_genre_index_map()`
- `_extract_engine_genre_index_map()` still looks for an old `genres = { ... }` shape in `main_a.py`
- current engine code now exposes the genre catalog through `_build_genre_selection_catalog()` in `main_a.py`

Inference from sources:

- the gate is stale because the parser no longer matches the current engine structure, so it returns `{}` and trips a false mismatch.
- this is still operationally important because `npm test` and `npm run test:desktop-contract` are documented as the official desktop gate. A stale red gate blocks confidence and hides later Node checks when run through the chained package script.

Impact:

- desktop/frontend contract confidence is artificially degraded
- operators lose a clean official gate
- genuine FE regressions are harder to distinguish from stale contract checks

### F2. Renderer complexity is still too concentrated in `index.html`

Evidence:

- `geuldobi-desktop/src/index.html` is about `10083` lines with `153` function declarations
- the same file still owns:
  - runtime bridge status sync
  - WebSocket connection/reconnect logic
  - prompt modal flow
  - run button orchestration
  - settings UI and API key testing
  - material panel logic
  - canvas/office animation logic
  - large chunks of quality dashboard rendering

Assessment:

- helper extraction has started, but ownership is still overly centralized
- this is the most likely source of future FE drift, because contract changes, settings UX changes, and visual/runtime changes still collide inside one file

Impact:

- FE changes are slower to review
- contract mismatches become harder to localize
- test coverage can pass while maintainability keeps decaying

### F3. Settings UX is still Gemini-centric and not aligned with the current multi-provider direction

Evidence:

- settings tab label still presents a required `Gemini API Key`
- extra credentials are generic `API Key 2~9`, not provider-scoped
- API key test in renderer directly calls `https://generativelanguage.googleapis.com/v1beta/models?key=...`
- model tab is explicitly read-only and points operators back to `config/models.yaml`

Assessment:

- the FE still assumes a Google-first credential story
- this does not match the current stated direction of making `OpenAI / Claude / Vertex AI / Gemini` all usable
- even if backend/provider work lands first, desktop settings UX will lag behind unless redesigned

Impact:

- multi-provider rollout will feel unfinished from the operator surface
- provider onboarding will stay error-prone because credential semantics are not explicit in UI
- renderer CSP/direct-surface inventory will need expansion or redesign once new validation flows arrive

## 5. Positive Signals

- The desktop bridge contract is not ad hoc anymore.
  - `desktop_control_plane_contract.js` centralizes IPC channel names and bridge-managed route names.
- Security posture is reasonable for the current Electron shell.
  - `contextIsolation: true`
  - `nodeIntegration: false`
  - preload mediation instead of renderer Node access
  - CSP keeps direct connect targets narrow
- Contract documentation and static checks are mostly in sync.
  - focused Python FE/desktop tests passed
  - Node preload/material/splash checks passed
  - `DESKTOP-GUIDE.md` and `package.json` still agree on the official gate commands
- Preload drift risk is recognized and covered.
  - `preload.js` duplicates method-channel mapping for packaged-electron reasons
  - `tests/test_desktop_preload_bridge_behavior.js` explicitly checks lockstep against `desktop_control_plane_contract.js`

## 6. Recommended Next Actions

1. Restore the official desktop gate first.
   - update `tests/test_desktop_contract_refresh.py` so engine genre inventory is read from the current canonical source, not the stale `genres = {}` pattern
   - after that, re-run `npm run test:desktop-contract`

2. Treat `index.html` as a UI hotspot and continue extraction.
   - prioritize splitting:
     - settings/provider surface
     - transport/runtime sync
     - prompt modal flow
     - run-control orchestration
   - do not keep adding new provider UX logic to the monolithic inline renderer block

3. Redesign settings around provider/backend semantics before multi-provider rollout reaches UI.
   - separate provider credentials explicitly
   - avoid a single required `Gemini API Key` label
   - stop assuming Google-only direct validation from renderer

4. Run live runtime proof in the next UI pass.
   - `npm run start:spike`
   - optionally `npm run start:desktop-spike`
   - confirm splash handoff, command readiness, and basic settings/load path under live Electron

## 7. Survey Conclusion

The desktop/frontend surface is not in a collapsed state. Security baseline, bridge contract organization, and most static tests are healthy. The immediate problem is that the official desktop gate is red because one contract-refresh test has gone stale against the engine's current genre catalog shape.

The bigger structural problem is frontend concentration: `index.html` is still too large and still owns too many unrelated responsibilities. Separately, settings UX is materially behind the repo's current multi-provider direction and will become a visible mismatch once backend provider work advances.

3-pass audit status: complete
Estimated confidence: `0.96`
