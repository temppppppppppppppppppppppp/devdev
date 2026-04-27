# T04 Desktop Config Surfaces

Date: 2026-04-27
Workspace: `C:\Users\wjjo\Desktop\글도비`
Baseline commit: `a3d826978d530ab61d3765e5e095890fa6533ea7`
Primary issues: #66, #68, #70
Document type: read-only investigation report. Not an execution SSOT, not a code-patch order.
Encoding: UTF-8.

## Scope

Map the Electron/desktop config and settings bridge surfaces that touch secrets, runtime config, IPC, file I/O, and startup. Files inspected:

- `geuldobi-desktop/main.js` (compat shim)
- `geuldobi-desktop/preload.js` (compat shim)
- `geuldobi-desktop/src/main.js` (1267 LOC, authoritative Electron main)
- `geuldobi-desktop/src/preload.js` (91 LOC, authoritative preload)
- `geuldobi-desktop/src/desktop_control_plane_contract.js` (98 LOC)
- `geuldobi-desktop/src/desktop_bridge_client.js` (62 LOC)
- `geuldobi-desktop/src/renderer_state_bootstrap.js` (661 LOC, DOM rendering only)
- `geuldobi-desktop/src/renderer_state_react_helpers.js` (181 LOC, React render helpers only)
- `geuldobi-desktop/src/console_relay.js` (56 LOC, surveyed via grep — `webContents.on("console-message", …)` relay only)
- `geuldobi-desktop/src/index.html` (settings UI and renderer logic, surveyed via targeted grep + ranged read)
- `geuldobi-desktop/package.json`

Out of scope for this report:

- Python runtime config loading (T02).
- Vertex/GCP auth (T03).
- Final Windows path policy (T05).
- Release packaging exclusion design (T06).
- EXE access-control authorization model (T08).

## Commands / Evidence

Direct reads of files listed above (UTF-8 only). Targeted greps:

- `Grep "localStorage|sessionStorage|window.geuldobiDesktop|saveSettings|loadSettings|apiKey|extraKeys|slackWebhook|fetch\(|http://|https://|window.geuldobi" -- geuldobi-desktop/src` (matches captured below by file:line).
- `Grep "localStorage|fetch\(|XMLHttpRequest|require\(|fs\.|spawn|exec|ipcMain|ipcRenderer|contextBridge|webContents" -- geuldobi-desktop/src/console_relay.js` confirmed `console_relay.js` only attaches a `webContents.on("console-message", …)` listener; no IPC, fs, or fetch surfaces.

Key anchors (file:line, redacted where relevant):

- `geuldobi-desktop/src/main.js:11-15` — `EARLY_DEBUG_LOG_PATH` computed from `%LOCALAPPDATA%/Geuldobi/electron-main.log`.
- `geuldobi-desktop/src/main.js:107` — `STATUS_BASE_URL = "http://127.0.0.1:8300"` (localhost only).
- `geuldobi-desktop/src/main.js:108-115` — `BRIDGE_FETCH_TIMEOUT_MS = 5000`, `EVENTS_WS_URL = "ws://127.0.0.1:8300/events"`, frozen `DESKTOP_BRIDGE_TRANSPORT` envelope.
- `geuldobi-desktop/src/main.js:134-140` — frozen `DESKTOP_PUBLIC_RUN_KEYS` allowlist + `isAllowedDesktopRunKey()` guard for `bridge:run`.
- `geuldobi-desktop/src/main.js:136` — `SETTINGS_PAYLOAD_MAX_BYTES = 1024 * 1024` (1 MiB cap on `saveSettings`).
- `geuldobi-desktop/src/main.js:158-183` — `serializeDesktopSettingsPayload` enforces JSON-serializable + size cap.
- `geuldobi-desktop/src/main.js:194-202` — `getLocalAppDataRoot()` / `getAppDir()` resolve to `%LOCALAPPDATA%/Geuldobi` (or `~/AppData/Local/Geuldobi` fallback).
- `geuldobi-desktop/src/main.js:205-213` — `getWorkspaceDir()` resolves to `<Documents>/글도비` in packaged mode, repo root in dev mode.
- `geuldobi-desktop/src/main.js:215-269` — packaged `workspace-seed` sync from `process.resourcesPath/workspace-seed` into `<Documents>/글도비/{bible,treatments,projects}`.
- `geuldobi-desktop/src/main.js:271` — `SETTINGS_PATH = path.join(getAppDir(), "settings.json")` (module-load constant, no user override).
- `geuldobi-desktop/src/main.js:273-297` — `buildDefaultDesktopSettings()` and normalizer; default schema includes `apiKey1`, `extraKeys` (object map), `slackWebhook`, `timeout`, `keyRotate`, `qualityGate`, `targetLength`, `project`.
- `geuldobi-desktop/src/main.js:299-384` — `persistDesktopSettings`, `readDesktopSettingsFile`, `recoverDesktopSettingsFromBackup`, `factoryResetDesktopSettings`, `loadDesktopSettingsFromDisk`. Persists plaintext JSON. On JSON corruption: rename to `<settings>.bak` and recover; on `.bak` corruption: factory-reset.
- `geuldobi-desktop/src/main.js:386-396` — `ensureFirstRunFlag()` writes `%LOCALAPPDATA%/Geuldobi/.first_run`.
- `geuldobi-desktop/src/main.js:463-558` — `startBackend()` spawns dev `python -m uvicorn modules.api.bridge_server:app --port 8300` or packaged `<resources>/backend/backend.exe`. Env passes through `process.env` plus `GEULDOBI_DESKTOP_MODE=1`, packaged adds `GEULDOBI_PACKAGED_RUNTIME_MODEL`, `GEULDOBI_WORKSPACE`, `GEULDOBI_PROJECTS_ROOT`. `cmd, args, cwd` are written to the debug log at `geuldobi-desktop/src/main.js:490`.
- `geuldobi-desktop/src/main.js:508-517` — `backendProcess.stdout/stderr` are mirrored verbatim into both `console.log` and `debugLog` (the `electron-main.log` file).
- `geuldobi-desktop/src/main.js:560-581` — `stopBackend()` uses Windows `taskkill /pid /t /f` for tree termination.
- `geuldobi-desktop/src/main.js:585-621, 624-669` — `createMainWindow()` and `createSplashWindow()` set `contextIsolation: true`, `nodeIntegration: false`.
- `geuldobi-desktop/src/main.js:707-718` — `splash:get-config` returns `firstRun`, `fallbackMs`, `statusBaseUrl` to renderer.
- `geuldobi-desktop/src/main.js:722-777` — `bridgeFetch()` posts to `STATUS_BASE_URL + urlPath`. **No `Authorization` or auth header is sent**; only `Content-Type: application/json`.
- `geuldobi-desktop/src/main.js:779-856` — IPC handlers for run/stop/status/quality/safe-ops/quality-review/resolve-prompt all delegate to `bridgeFetch` with `BRIDGE_MANAGED_ROUTES`.
- `geuldobi-desktop/src/main.js:806-808` — `bridge:get-url` returns `{ wsUrl, httpUrl }` (localhost) to the renderer.
- `geuldobi-desktop/src/main.js:860-882` — IPC handlers for `bridge:save-settings` / `bridge:load-settings` (the **plaintext** persistence path).
- `geuldobi-desktop/src/main.js:886-927` — `getEngineRoot()`, `getMaterialRoot()`, `getMaterialVisibilityConfigPath()`, `getAllowedMaterialFiles()`. Material visibility config at `<materialRoot>/config/material_visibility.json`; missing file → return `null` → no allowlist filter applied.
- `geuldobi-desktop/src/main.js:929-1009` — `material:list-files`, `material:import-file`, `material:delete-file`. Folder restricted to `bible|treatments`. Delete rejects filenames containing `..`, `/`, `\`.
- `geuldobi-desktop/src/main.js:1011-1102` — project IPC. `sanitizeProjectName()` trims, rejects all-dots, replaces non-`[a-zA-Z0-9가-힣ㄱ-ㅎㅏ-ㅣ_\- ]` with `_`. `resolveWorkGuardTemplatePath()` uses `path.relative(libraryRoot, resolved)` containment check + YAML extension check.
- `geuldobi-desktop/src/main.js:1109-1215` — project IPC handlers (list/create/load+save config surfaces, list+apply work_guard templates).
- `geuldobi-desktop/src/main.js:1219-1225` — `workspace:open-folder` uses `shell.openPath`.
- `geuldobi-desktop/src/main.js:1230-1267` — `app.whenReady` boot order: `syncPackagedWorkspaceSeed → startBackend → bootstrapWindows`. `before-quit` and `window-all-closed` both call `stopBackend`. **No pre-startup auth/license/allowlist gate**.
- `geuldobi-desktop/src/preload.js:34-91` — `contextBridge.exposeInMainWorld("geuldobiDesktop", { … })` exposes exactly the methods declared in `LIVE_PRELOAD_METHOD_NAMES` (frozen contract).
- `geuldobi-desktop/src/desktop_control_plane_contract.js:5-89` — frozen `IPC_CHANNELS`, `PRELOAD_METHOD_CHANNELS`, `BRIDGE_MANAGED_ROUTES`, `buildRunInputRoute`. Single source of truth for channel names; preload and main.js both consume it.
- `geuldobi-desktop/src/desktop_bridge_client.js:8-52` — renderer-side facade verifies all `LIVE_PRELOAD_METHOD_NAMES` are wired before use; throws otherwise.
- `geuldobi-desktop/src/index.html:6` — Content Security Policy:
  ```
  default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src ws://127.0.0.1:8300 https://generativelanguage.googleapis.com;
  ```
- `geuldobi-desktop/src/index.html:3176-3206` — settings UI: `apiKey1` is `<input type="password">`; placeholder hint shows `AIza...` (Google API key prefix), `extraKeysToggle` reveals additional 8 inputs (`apiKey2` … `apiKey9`); `slackWebhook` is `<input type="text">` with `https://hooks.slack.com/...` placeholder.
- `geuldobi-desktop/src/index.html:9432-9451` — `testKey1Btn` click handler does:
  ```js
  const res = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models?key=${encodeURIComponent(key)}`
  );
  ```
  This sends the user's API key in the URL query string directly from the renderer to Google's external service. There is no main-process broker; the renderer reads the key from the DOM input and emits it.
- `geuldobi-desktop/src/index.html:9584-9605, 9718-9722, 7493-7501` — settings save path: renderer mutates `settingsStore.{apiKey1, slackWebhook, extraKeys[2..9], …}` and calls `window.geuldobiDesktop.saveSettings(settingsStore)` → IPC → `fs.writeFileSync(SETTINGS_PATH, JSON.stringify(...), "utf8")` (plaintext).
- `geuldobi-desktop/src/index.html:10025-10073` — load settings on app boot: `await window.geuldobiDesktop.loadSettings()` populates `settingsStore.apiKey1`, `settingsStore.slackWebhook`, `settingsStore.extraKeys`.
- `geuldobi-desktop/package.json:6-14` — start script forces `set ELECTRON_RUN_AS_NODE=` (clears the var) before launching electron; test scripts spawn pytest with desktop contract suites and node-based preload bridge tests.
- `geuldobi-desktop/package.json:29-92` — `electron-builder` config: target NSIS, `signAndEditExecutable: false`, `oneClick: false`, `extraResources` pulls `../dist/backend`, `../dist/engine`, `../python-embed`, `../dist/workspace-seed` with filters excluding `*.log|*.tmp|*.bak`. `files` includes `src/**/*`, excludes `node_modules/.cache` and `src/sprites/dbg_desk_*`.

No raw secret values were read from any file or paste-buffered into this report. The placeholder strings `AIza...` and `https://hooks.slack.com/...` shown above come from non-sensitive UI placeholders, not from a populated `settings.json`.

## Findings

### F1 [P0] Renderer issues a direct outbound fetch with the user's API key in the URL query string

`geuldobi-desktop/src/index.html:9432-9451` performs `fetch("https://generativelanguage.googleapis.com/v1beta/models?key=" + encodeURIComponent(key))` from the renderer context. The CSP at `index.html:6` explicitly allows this destination via `connect-src https://generativelanguage.googleapis.com`. Risks:

- API keys placed in URL query strings end up in any HTTP intermediary's logs that Electron's network stack might respect (corporate proxy, captive portal, MITM diagnostic tooling, Chromium's net-export, devtools network panel that some Electron builds expose).
- There is no main-process broker; the renderer holds the cleartext key, reads it from the DOM, and emits it. Anything that can XSS the renderer can exfiltrate the key (see F4 on `unsafe-inline`).
- This pattern is also a #67 surface (Google auth governance), because it ties the desktop's "key validation" UX to a shared developer API key class rather than to a brokered identity.

### F2 [P0] Plaintext local settings file holds up to 9 API keys plus a Slack webhook

`geuldobi-desktop/src/main.js:271-302, 860-882` writes settings via `fs.writeFileSync(SETTINGS_PATH, JSON.stringify(settings, null, 2), "utf8")` and reads them back unencrypted. The default schema at `main.js:273-284` includes `apiKey1`, `extraKeys` (a 2..9 indexed map populated by `index.html:9584-9605`), and `slackWebhook`. The location is `%LOCALAPPDATA%/Geuldobi/settings.json` (and a `.bak` mirror written during recovery at `main.js:359-378`).

- No OS keystore (Windows Credential Manager / DPAPI) integration.
- Any process with read access on the user account, any backup tool that snapshots `%LOCALAPPDATA%`, or any cloud sync tooling that includes that folder, sees plaintext keys.
- Settings live alongside `electron-main.log` and the `.first_run` marker in the same folder, so the file class is "user runtime config", not "secret store".
- This is also a #68 surface because the chosen Windows path is sane (`%LOCALAPPDATA%`), but the **content class** mixes secrets with non-secrets in one JSON document; #68's "approved user config directory" should probably distinguish those.

### F3 [P1] Renderer-side `apiKey1` is type=password but is round-tripped to disk in cleartext

`index.html:3183` uses `<input type="password" id="apiKey1">`, and `index.html:9426-9427` includes a "show key" toggle that flips `type` between `password` and `text`. The DOM treatment is fine for shoulder-surfing; the real exposure is that the value is then sent verbatim to `saveSettings` (see F2) and persisted in cleartext. The visual cue is therefore misleading and may mask the real risk class to the operator.

### F4 [P1] Content Security Policy allows `script-src 'unsafe-inline'` and `style-src 'unsafe-inline'`

`index.html:6` weakens CSP for both scripts and styles. The renderer is roughly 10000 LOC of inline templates and uses `innerHTML` in places (e.g. `renderer_state_bootstrap.js:192-209` where filenames are passed through `escapeHtml` first — that one looks safe). But `'unsafe-inline'` removes the structural guarantee against any future HTML-injection regression in this large file, and the same CSP also whitelists `https://generativelanguage.googleapis.com` (F1) and `ws://127.0.0.1:8300`. Combined with F2 storing plaintext keys in a known location and F1 demonstrating that an outbound channel to a key-accepting endpoint is reachable from the renderer, the residual CSP weakness becomes a key-exfiltration risk class, not just a "best practice" finding.

### F5 [P1] Backend HTTP bridge has no authentication header

`bridgeFetch()` at `main.js:722-777` hits `http://127.0.0.1:8300` with `Content-Type: application/json` and nothing else. The bridge listener is localhost-only, but on a multi-user Windows host, any process running as the same user (or with sufficient privilege) can also discover and call port 8300. Run-control endpoints (`/run`, `/stop`, `/run/<id>/input`) are reachable. This is the natural chokepoint the #70 access-control work will need to harden; T08 owns the design choice (per-session token vs. allowlisted user identity vs. signed license token), but the surface is captured here for completeness.

### F6 [P1] `electron-main.log` accumulates spawn args, env-derived paths, and verbatim backend stdout/stderr in cleartext

`main.js:11-35, 67-87, 490, 508-517` write to `%LOCALAPPDATA%/Geuldobi/electron-main.log`:

- `main.js prelocal-require` line includes `pid, execPath, resourcesPath, cwd`.
- `startBackend` line includes `cmd, args, cwd`. `cmd` may include the value of `process.env.PYTHON_PATH`.
- Every `backendProcess.stdout/stderr` chunk is appended verbatim. If the backend ever logs a token, a header, an environment dump (`os.environ`), or a stack trace that includes a credential, that value lands in this file.
- The file is append-only with no rotation cap.

This is a secondary leak channel: secrets are not deliberately routed here, but anything the backend prints flows here unfiltered.

### F7 [P1] `material_visibility.json` defaults to "no allowlist" when the config file is missing or malformed

`main.js:901-927` returns `null` for `getAllowedMaterialFiles(folder)` when the visibility config is absent or the JSON is invalid; `main.js:929-951` then treats `null` as "skip the allowlist filter" and returns every file. So if the config file is deleted, mistyped, or shipped empty, the desktop UI lists every file in `bible/` and `treatments/`. This is a fail-open posture, not a secret exposure per se, but it weakens the "what the user sees" boundary that #66/#68 try to establish.

### F8 [P2] No startup chokepoint where access control would attach

`main.js:1230-1253` runs `app.whenReady → syncPackagedWorkspaceSeed → startBackend → bootstrapWindows` with no gate. There is no module that performs a license check, an internal-account login, an allowlist check, or a token verification before `bootstrapWindows` runs and `bridgeFetch` is reachable. T08 is the owner for the model itself; T04 just records that the chokepoint surface is currently empty and that `app.whenReady` (and the `bridgeFetch` wrapper at `main.js:722`) are the two natural insertion points.

### F9 [P2] Workspace seed is copied from `process.resourcesPath/workspace-seed` into Documents on every packaged launch

`main.js:215-269` copies `bible/`, `treatments/`, `projects/` from the packaged seed into `<Documents>/글도비` whenever a target file does not already exist. If the packaged seed ever ships with test, internal, or stale files, those files appear under the user's Documents folder. T06 owns the packaging exclusion plan; T04 records the consumer side here.

### F10 [P2] `apiKey1` placeholder string is `"AIza..."`

`index.html:3183` uses `placeholder="AIza..."`, which leaks the expected key class (Google API key) to anyone who opens the settings UI or inspects the source bundle. Not a secret in itself, but it tightens the threat model for #67: an attacker who gets the `settings.json` knows immediately it contains Google-class keys, not arbitrary tokens.

### F11 [P2] Settings save IPC has size and JSON guards but no field-level validation

`main.js:158-183, 860-878` enforces `SETTINGS_PAYLOAD_MAX_BYTES = 1 MiB` and rejects non-JSON-serializable payloads, but does not validate that `apiKey1` is a string, that `extraKeys` keys are within `2..9`, that `slackWebhook` is a URL, or that `timeout`/`keyRotate`/`qualityGate`/`targetLength` are numeric. A renderer compromise can write a settings file with arbitrary nested structure (within 1 MiB and JSON-serializable). This is mostly a robustness finding, but pairs with F2 because the file is plaintext and consumed by the Python backend.

### Positive findings (recorded so the remediation plan does not regress them)

- `contextIsolation: true` and `nodeIntegration: false` are set on both windows (`main.js:591-595, 636-640`).
- The preload exposes a frozen, enumerable contract; renderer-side facade verifies completeness before use (`desktop_bridge_client.js:8-43`).
- IPC channel names are centralized in `desktop_control_plane_contract.js` and frozen, removing channel-name drift between preload and main.
- `material:delete-file` rejects filenames containing `..`, `/`, or `\` (`main.js:996-999`).
- `sanitizeProjectName` restricts the charset and rejects pure-dot names (`main.js:1020-1029`).
- `resolveWorkGuardTemplatePath` does a containment check via `path.relative` plus YAML extension enforcement (`main.js:1092-1103`).
- `bridge:run` keys are restricted to a frozen public allowlist (`main.js:134-140`).
- `electron-builder` excludes `*.log|*.tmp|*.bak` from `extraResources` and `node_modules/.cache` from packaged sources (`package.json:48-91`).
- Compat shims at `geuldobi-desktop/main.js` and `geuldobi-desktop/preload.js` are inert (`require("./src/main.js")` / `require("./src/preload.js")`); no stale IPC surfaces remain at the legacy paths.

## Remediation Candidates

Listed without prescribing implementation. T08 owns the access-control choice; T05 owns the path policy; T06 owns the packaging exclusion plan. T04 only proposes desktop-side levers.

1. **Move API key validation behind the main process.** Replace the renderer-side fetch at `index.html:9432-9451` with an `ipcRenderer.invoke("bridge:test-key", { keyId })` call that runs in the main process, sends the key as a request header (e.g. `x-goog-api-key`) instead of a URL parameter, and never returns the key value to the renderer. (Pairs with #66.)

2. **Stop persisting raw API keys in `settings.json`.** Either (a) move secrets to Windows Credential Manager via `keytar`/native equivalent and store only an opaque key handle in `settings.json`, or (b) remove the desktop's responsibility for holding API keys at all and route all model calls through the backend with backend-owned credentials. (#66 / #67.)

3. **Tighten CSP.** Remove `'unsafe-inline'` from `script-src` (and ideally `style-src`) by extracting the inline scripts in `index.html` into bundled files. Once F1 is fixed, `connect-src` can drop `https://generativelanguage.googleapis.com` entirely. (#66.)

4. **Send a per-process auth header on every `bridgeFetch` call.** Generate a random token at main-process startup, pass it to the spawned backend via env (e.g. `GEULDOBI_BRIDGE_TOKEN`), and require the same token on every HTTP call from `main.js:722-777` and on the WebSocket handshake. This closes the localhost-shared-tenancy gap and gives T08 a foundation for #70.

5. **Filter `electron-main.log` for known-secret patterns** before append, or scope the file to a separate "diagnostics-on" toggle. At minimum, do not log `cmd, args, cwd` of the backend spawn at info level if `args` may ever carry a secret in the future.

6. **Default `material_visibility.json` to fail-closed.** When the config is missing or malformed, return an empty list and surface a UI banner, instead of unfiltered listing.

7. **Add field-level validation to `bridge:save-settings`** beyond the size/JSON guard, so a compromised renderer cannot write arbitrary structure into the file consumed by the Python backend.

8. **Expose a startup gate slot** in `main.js:1230-1253` (between `app.whenReady` and `bootstrapWindows`) that T08's chosen authorization model can attach to. Today there is no place to insert such a check without rewriting the boot sequence.

## Dependencies On Other Terminals

- **T01** (root secret inventory): if `settings.json` ever appears under the repo or under `dist/`, T01 should record it; T04 only inspects code paths that produce it.
- **T02** (Python runtime config topology): the desktop writes to `<materialRoot>/config/material_visibility.json` and `<projectRoot>/config/{author_directives.txt, work_guard.yaml}`; T02 should record the consumer side in Python.
- **T03** (Vertex auth flow): F1 (Google API key validation in renderer) is desktop-side, but the auth model classification is T03's call (developer key vs brokered identity).
- **T05** (Windows settings path): T04 confirms the desktop already lives under `%LOCALAPPDATA%/Geuldobi` and `<Documents>/글도비`; T05 should decide whether the secrets layer belongs in the same path or in a separate keystore.
- **T06** (release packaging): F9 (workspace seed) and the `extraResources` block in `package.json` are T06's territory for inclusion/exclusion design.
- **T08** (EXE access control): F5 (no auth header) and F8 (no startup chokepoint) are the desktop-side hooks T08 will design against.
- **T09** (CI/release guardrails): a guardrail that blocks committing or shipping a populated `settings.json` would close the residual leak from F2.

## Open Questions

- Is the Google API key validation in `index.html:9432-9451` ever exercised in production, or is it dev-only? If dev-only, it can be removed wholesale rather than rebrokered.
- Are there other renderer paths that read `settingsStore.apiKey1` and emit it externally? A 10000+ LOC inline `index.html` is hard to fully audit by grep alone; a follow-up surface-only audit may be needed.
- Does the backend (`bridge_server.py`) read any of `apiKey1`/`extraKeys`/`slackWebhook` via the desktop-managed `settings.json`, or does it use its own config path? T02 should confirm.
- Should `extraKeys` keep the 2..9 layout, or collapse into a single rotation pool with explicit index? Pure desktop-shape question, not security.
- Is `signAndEditExecutable: false` in `package.json:35` deliberate (no code-signing yet) or a temporary state? Code-signing is part of #70's threat model and T06/T08 likely own the answer.

## Closure Recommendation

Status: **investigation complete, do not close issues #66 / #68 / #70 yet**.

T04 evidence is sufficient to feed the consolidated security remediation roadmap (per the dispatch's §7), but not sufficient to close any of the source issues by itself:

- #66 (P0 secrets standardization) needs F1 + F2 + F3 + F4 + F11 addressed in code, not in a report.
- #68 (P1 user config directory) is partially confirmed (`%LOCALAPPDATA%` is already in use), but the secrets-vs-non-secrets split inside `settings.json` is the unresolved part T05 should rule on.
- #70 (P2 EXE access control) inherits F5 + F8 as its desktop-side surface; T08 owns the authorization model.

Suggested next step (per dispatch §7): merge T01–T10 reports into `docs/2026-04-27/security-remediation-roadmap.md` and let that roadmap, after the document 3-pass audit, gate any code change. T04 is read-only and writes only this report path.
