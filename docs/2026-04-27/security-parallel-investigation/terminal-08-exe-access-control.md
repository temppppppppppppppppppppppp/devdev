# T08 EXE Access-Control Chokepoints

Date: 2026-04-27
Terminal: T08
Primary GitHub issue: #70 `[SEC] Add executable access control for internal distribution`
Related issue: #68 `[SEC] Move local app settings to approved user config directory`
Workspace: `C:\Users\wjjo\Desktop\글도비`
Baseline commit: `a3d826978d530ab61d3765e5e095890fa6533ea7`
Document type: read-only parallel investigation report. Not an execution SSOT and not a source-code patch order.

## Scope

Identify the runtime startup chokepoints where executable access control could be enforced for the internally distributed 글도비 build, and propose 2-3 feasible internal-distribution authorization models with tradeoffs. Surface the minimal "unauthorized copied EXE does not run normally" path and the natural location for the secret/license material that such a model would consume. Leave secret-handling policy detail to T01/T02/T05 and packaging exclusion detail to T06.

Inspected source surfaces:

- `build/backend_entry.py`
- `main_a.py` (boot section, lines 1-200)
- `modules/api/bridge_server.py` (lines 1-400, plus targeted greps for auth/middleware over the whole file)
- `modules/api/process_runner.py`
- `modules/api/control_plane_contract.py`
- `modules/core/runtime_paths.py`
- `geuldobi-desktop/main.js` (legacy shim)
- `geuldobi-desktop/preload.js` (legacy shim)
- `geuldobi-desktop/src/main.js`
- `geuldobi-desktop/src/preload.js`

Out of scope (delegated):

- Root secret inventory and `.env` / `geuldobi-vertex-key.json` classification: T01.
- Python runtime config loading topology and Windows path policy: T02 / T05.
- Vertex / Google auth flow and Barobook account migration: T03.
- Desktop config and IPC settings bridge full enumeration: T04.
- Release packaging inclusion/exclusion (PyInstaller, electron-builder, NSIS, scripts/dev exclusion): T06 / T07.
- CI / pre-commit / release guardrails: T09.
- Final security response documentation map: T10.

## Commands / Evidence

Commands used (read-only):

- `git rev-parse HEAD` to confirm baseline commit `a3d826978d530ab61d3765e5e095890fa6533ea7`.
- `git status --short` to confirm only `docs/2026-04-27/security-parallel-investigation/` was untracked at dispatch start.
- File reads via the Read tool on the inspected source surfaces listed in Scope.
- Grep tool over `modules/api` and `geuldobi-desktop` for `auth|login|license|token|allowlist|machine[_-]id|user[_-]id|access[_-]control|cors|origin|api_?key|secret` (case-insensitive).
- Grep tool over `modules/api/bridge_server.py` for `add_middleware|CORSMiddleware|HTTPBasic|Depends|Header|Cookie|@app\.middleware`.

Key concrete observations (paths and line numbers):

1. PyInstaller entry binds the bridge to localhost without any startup authorization gate.
   - `build/backend_entry.py:27-38` — `if __name__ == "__main__":` branch calls `uvicorn.run(app, host="127.0.0.1", port=8300, log_level="info")` for both frozen and source modes. There is no license check, signature check, machine binding, or env-token check before the socket is bound.
2. The FastAPI bridge has no HTTP-level authentication middleware.
   - Grep over `modules/api/bridge_server.py` for `add_middleware|CORSMiddleware|HTTPBasic|Depends|Header|Cookie|@app\.middleware` returned no matches. Authority annotations exist (`AUTHORITY_ROLE_AUTHORITATIVE_SINK`, `AUTHORITY_ROLE_COMPANION_SNAPSHOT` in `modules/api/control_plane_contract.py`) but they describe data-sink authority, not request authentication.
   - Effective access control is only the `host="127.0.0.1"` bind. Any local process on the machine can call `POST /run`, `POST /stop`, `GET /status`, `WS /events`, etc. once the backend is up.
3. The Electron main process is the de-facto sole client of the bridge, but the trust path between Electron and the bridge is implicit, not authenticated.
   - `geuldobi-desktop/src/main.js:107` `STATUS_BASE_URL = "http://127.0.0.1:8300"`.
   - `geuldobi-desktop/src/main.js:463-558` `startBackend` spawns `backend.exe` (`path.join(resourcesPath, "backend", "backend.exe")` in packaged mode) or `python -m uvicorn modules.api.bridge_server:app --port 8300` in dev mode; spawn env adds `PYTHONIOENCODING`, `PYTHONUNBUFFERED`, `GEULDOBI_DESKTOP_MODE=1`, plus packaged workspace env, but does not inject any per-process auth token.
   - `geuldobi-desktop/src/main.js:779-856` IPC handlers (`bridge:run`, `bridge:stop`, `bridge:status`, `bridge:resolve-prompt`, etc.) call `bridgeFetch(...)` which adds `Content-Type: application/json` only.
4. Renderer-side surface is hardened only against unallowed `key` values, not against unauthenticated callers.
   - `geuldobi-desktop/src/main.js:134-140` `DESKTOP_PUBLIC_RUN_KEYS` set + `isAllowedDesktopRunKey` is enforced inside the `bridge:run` IPC handler.
   - This guards against an in-renderer typo or compromised renderer trying to invoke an off-list key, but it does not guard against another local process on the host calling `POST http://127.0.0.1:8300/run` directly.
5. Settings and credentials currently live next to the EXE-launched workspace, not behind an auth boundary.
   - `geuldobi-desktop/src/main.js:271` `SETTINGS_PATH = path.join(getAppDir(), "settings.json")` resolves to `%LOCALAPPDATA%/Geuldobi/settings.json` and `buildDefaultDesktopSettings` includes `apiKey1` and `extraKeys`. This is the surface that an unauthorized copy of the EXE would inherit verbatim if a user copied both the install directory and the AppData directory.
   - `modules/api/process_runner.py:852-908` `_build_env` injects API keys (Google, Anthropic/Claude, OpenAI, Vertex) into the spawned `main_a.py` environment based on `inputs` payload supplied through `/run`. The bridge has no concept of "is the caller authorized to use this account's quota."
6. Electron entrypoints have a documented Class A / Class B layering that gives a clean place to add a startup gate.
   - `modules/core/runtime_paths.py:24-52` `RUNTIME_AUTHORITY_CONTRACT` declares `geuldobi-desktop/src/main.js` as the supported entry and labels the legacy `geuldobi-desktop/main.js` and root `main.js` as compatibility shims.
   - `geuldobi-desktop/main.js` and `geuldobi-desktop/preload.js` confirm this — both are `module.exports = require("./src/...")` pass-through shims with no logic. A startup gate added in `geuldobi-desktop/src/main.js` is the single chokepoint that covers all packaged Electron paths.
7. There is no built-in concept of "user identity," "machine fingerprint," "license file," or "online verification."
   - No matches in `geuldobi-desktop` or `modules/api` for `login`, `auth`, `token`, `allowlist`, `machine_id`, or `user_id` outside of the `package-lock.json` license-metadata noise and `apiKey` setting names.
   - `package.json:18 "license": "ISC"` is open-source license metadata for the npm package, not an internal-distribution license model.
8. Backend restart resilience is permissive enough that an unauthorized launcher does not need to be subtle.
   - `geuldobi-desktop/src/main.js:399-461, 537-552` will re-spawn `backend.exe` up to `MAX_BACKEND_RESTARTS = 2` times on non-zero exit before prompting the user. A backend with a license check that exits non-zero would be retried twice silently; the user prompt eventually surfaces, but only the operator can read the dialog. This argues for the gate to refuse cleanly with a typed exit code so Electron can surface an explicit "license invalid" message rather than a generic restart loop.

## Findings

Severity uses the dispatch document scale (`P0`/`P1`/`P2`/`P3`).

- **F1 (P1) — No auth between any local process and the bridge.** `host="127.0.0.1"` is the only access control. Any local process on the same Windows account (or any account that can connect to loopback) can drive `/run`, `/stop`, `/run/{id}/input`, and the WebSocket without authentication. For an internal distribution build this is the central gap addressed by issue #70.
- **F2 (P1) — No startup gate on `backend.exe`.** `build/backend_entry.py` immediately calls `uvicorn.run` in the frozen branch. A copied EXE on a different machine, or by an unauthorized user, runs identically as long as the file is launched. Issue #70's "executable access control" should land here, before the socket bind.
- **F3 (P2) — Renderer key allowlist hides the gap from honest callers but not from malicious ones.** `DESKTOP_PUBLIC_RUN_KEYS` enforcement at `geuldobi-desktop/src/main.js:779-795` is a good usability guard; it should not be confused with access control. The bridge should still independently authenticate the caller, because malicious callers will bypass the IPC handler entirely and POST to the bridge directly.
- **F4 (P2) — API-key environment promotion is unconditional.** `modules/api/process_runner.py:852-908` accepts `inputs.api_key`, `inputs.anthropic_api_key`, `inputs.vertex_*`, `inputs.openai_api_key` from any caller of `/run` and promotes them to subprocess env. Without bridge-level auth, an unauthorized local process can both invoke runs and inject its own keys, or read whatever the operator has saved to `%LOCALAPPDATA%/Geuldobi/settings.json` to bootstrap an unauthorized clone.
- **F5 (P2) — `main_a.py` has no boot-time identity check.** Boot section (`main_a.py:1-200`) is concerned with stdio normalization, asyncio policy, faulthandler, and `load_dotenv(override=True)`. No license / identity / machine-binding check exists. If a user runs `engine.exe` or `python main_a.py` directly (the `_resolve_launch_command` fallback at `process_runner.py:246-260`), there is no second gate.
- **F6 (P2) — Restart policy will mask early license-check exits.** `geuldobi-desktop/src/main.js:537-552` retries non-zero backend exits twice before prompting. A license-failed backend should signal that case explicitly so the desktop can show a license dialog rather than a generic "백엔드 연결 실패" restart prompt.
- **F7 (P3) — No code signing posture is documented for the distributed EXE.** No grep matches for `Authenticode`, `signtool`, signing config, or pinned-cert verification in the inspected surfaces. This is necessary background for any "unauthorized modification of EXE bytes is detectable" claim. Confirming the actual signing posture belongs to T06; this report only flags that nothing in the inspected code paths assumes a trusted signature.
- **F8 (P3) — Compatibility shims at `geuldobi-desktop/main.js` and `geuldobi-desktop/preload.js` re-export `src/`.** Confirmed pass-through; placing the access-control hook in `src/main.js` (the supported Class A entry per `modules/core/runtime_paths.py:24-37`) automatically covers the legacy shim path. No duplicate insertion needed.

## Remediation Candidates

Three feasible internal-distribution authorization models, each scoped to be implementable on top of the current Electron + Python bridge architecture without restructuring the control plane.

### Model A — Internal account login with online verification (server-issued JWT)

Sketch:

- Operator launches the EXE, sees a login splash before any workspace UI.
- Electron POSTs `{username, password}` (or company SSO equivalent) to a Barobook-internal auth endpoint and receives a short-lived JWT.
- Electron stores the JWT in memory only (or in `%APPDATA%/글도비/session.json` with OS-level DPAPI protection if "remember me" is desired).
- Electron passes the JWT to `backend.exe` at spawn time as `GEULDOBI_SESSION_TOKEN` env, and includes it as `Authorization: Bearer <jwt>` on every IPC-driven `bridgeFetch` call.
- A FastAPI dependency on `bridge_server.py` rejects any request whose `Authorization` header does not present a valid JWT signed by the pinned issuer key and whose `sub` is in the active user list.
- `backend_entry.py` refuses to call `uvicorn.run` if the backing license / public key material is missing, so a copied EXE without the bundled key will not even bind the socket.

Tradeoffs:

- Pros: easiest revocation (server-side disable of a user); cheap to add granular roles; low risk of license-file leakage because tokens are short-lived.
- Cons: requires online verification on every launch, which contradicts any offline distribution intent; needs an internal auth backend to exist or be selected (likely related to issue #67); adds a network dependency at startup.
- Bypass class: an attacker who can patch `backend.exe` bytes can remove the dependency. Code signing + signature verification at Electron-side spawn (`startBackend` in `geuldobi-desktop/src/main.js:463`) raises that bar; without signing this is the weakest model against EXE-tamper.

### Model B — Signed license file + machine binding (offline-first)

Sketch:

- Issuer (Barobook ops) generates an Ed25519 keypair; public key is compiled into both `backend.exe` and `geuldobi-desktop` (`src/main.js`).
- Each authorized operator receives a signed license blob containing `{user_id, machine_fingerprint, issued_at, expires_at, capabilities}`. The blob is stored at `%APPDATA%/글도비/license.dat` (the location T05 will recommend for non-secret operator config; this is config-with-integrity, not raw secret).
- On startup, Electron `app.whenReady()` reads `license.dat`, verifies the signature with the pinned public key, recomputes machine fingerprint from stable identifiers (e.g., MachineGuid, primary NIC MAC, SMBIOS UUID — pick a stable subset), and refuses to call `bootstrapWindows()` / `startBackend()` if the signature is invalid, the fingerprint does not match, or the license is expired.
- `backend_entry.py` performs the same check independently before `uvicorn.run`. The two checks are intentionally redundant so that bypassing only the Electron check still leaves the backend dark.
- Bridge requests carry no per-request token; they rely on the backend already refusing to start without a valid license.

Tradeoffs:

- Pros: works fully offline; no auth backend required; deterministic; revocation possible via short `expires_at` and reissue cadence (e.g., 30-day licenses), or via a small revocation list bundled with each release.
- Cons: revoking a single user mid-cycle requires shipping a revocation list update or shortening license lifetime; machine-fingerprint stability is best-effort and noisy on hardware swaps; license file moves with the user, so a careless operator could give it to an unauthorized peer (machine binding is the protection against that).
- Bypass class: still vulnerable to EXE patching; mitigated by Authenticode signing on `backend.exe` and `geuldobi-desktop` (T06 should confirm signing policy), and by refusing to launch if the signature on the EXE itself is invalid (Windows can do this only if SmartScreen / WDAC is configured — out of scope of this terminal).

### Model C — One-time provisioning token + machine-bound device record (hybrid)

Sketch:

- First launch on a new machine asks operator to paste a one-time provisioning token issued by Barobook ops out-of-band (e.g., Slack DM).
- Electron exchanges the token with a lightweight Barobook device-registry endpoint, receiving `{device_id, device_secret, signed_envelope}`. `device_secret` and `signed_envelope` are written to `%APPDATA%/글도비/device.json`.
- Subsequent launches do not require online contact: Electron verifies `signed_envelope` with the pinned public key (offline) and uses `device_secret` as a shared secret on a `X-Geuldobi-Device-Auth` header for every bridge request.
- `backend_entry.py` reads the same `device.json`, verifies the envelope, computes the same shared-secret derivation, and rejects any request whose header does not match.
- Optional periodic online check (e.g., every 7 days) re-validates the device record with the registry; if revoked server-side, the next online check disables the device.

Tradeoffs:

- Pros: friendly steady-state UX (no daily login); revocation is server-side and effective on the next check-in; compromised `device.json` only authorizes that device (machine fingerprint can be re-bound at provisioning); audit trail per device.
- Cons: needs a small device-registry service (smaller than full SSO, but more than nothing); delayed revocation between online checks; provisioning UX must handle "lost token" / "machine reimage" without becoming an unauth backdoor.
- Bypass class: same EXE-tamper risk class as A and B; mitigation is the same code-signing posture.

### Recommended minimal "unauthorized copied EXE does not run normally" path

If the goal is to land the smallest first slice that meaningfully changes the threat model, candidates ordered by recommended sequencing:

1. Add a startup gate in `build/backend_entry.py` (between line 27 and line 31 in the frozen branch) that refuses to bind `127.0.0.1:8300` unless a verifiable license artifact (Model B style) or a valid env-injected token (Model A style) is present. Exit with a typed non-zero exit code that the Electron `backendProcess.on("exit", ...)` handler at `geuldobi-desktop/src/main.js:532-552` recognizes as "license invalid, do not retry" and surfaces a license dialog instead of restart-and-retry.
2. Add the parallel gate in `geuldobi-desktop/src/main.js` `app.whenReady().then(...)` (currently at line 1230) so the splash never appears when authorization is missing. This is the user-visible part of the gate and the one that prevents a copied EXE from "looking normal" during the bridge bootstrap window.
3. Add a per-launch shared secret between Electron and the backend even when using Model B: Electron generates a random 32-byte secret on `app.whenReady()`, passes it via env (`GEULDOBI_BRIDGE_AUTH`) to `startBackend`, and includes it on every `bridgeFetch` call as `X-Geuldobi-Bridge-Auth`. `bridge_server.py` reads `os.environ["GEULDOBI_BRIDGE_AUTH"]` once at startup and rejects any request without the matching header. This closes the local-process-attack gap from F1 cheaply, regardless of which authorization model is chosen for the user-identity layer.
4. Move all license / device material to `%APPDATA%/글도비/` (depends on T05's path policy decision so the layout is consistent with general settings).
5. Confirm Authenticode signing on the distributed `backend.exe` and `geuldobi-desktop` build (depends on T06's packaging survey). Without code signing, all of A/B/C are vulnerable to in-place patching of the verification call sites.

Recommended starting model for an internal distribution with finite operator count and intermittent offline use: **Model B (signed license + machine binding)** for the user-identity layer, plus the per-launch shared secret in step 3 of the minimal path for the bridge-auth layer. Model B requires no new internal service, gives offline tolerance, and produces a deterministic "unauthorized copy does not run" outcome. Model C is the natural upgrade path once usage volume justifies a device registry.

## Dependencies On Other Terminals

- **T05** (Windows settings paths): the recommended location of `license.dat` / `device.json` must align with the approved Windows path policy T05 produces (`%APPDATA%/글도비/`).
- **T01** (root secret inventory): the pinned signing public key, embedded in `backend.exe` and `src/main.js`, must not be confused with a secret. The matching private key must be classified as a release-time secret outside the workspace and called out by T01 if it ever appears in the tree.
- **T03** (Vertex / Google auth flow): if Model A's auth backend ends up being the same auth surface as the Vertex-account migration, those efforts should converge rather than fork.
- **T04** (Desktop config surfaces): the access-control gate should use the IPC contract and AppData path conventions T04 recommends; an isolated gate that re-derives paths is acceptable as a first cut, but should normalize against T04 once both reports settle.
- **T06** (release packaging): code signing of the distributed EXE is the load-bearing assumption behind every "patching the verification call site is detectable" claim. T06 should confirm whether `signtool` is in the release flow and whether `electron-builder` is producing signed artifacts.
- **T09** (CI / release guardrails): if license issuance becomes part of the release, T09 should track the operational guardrail that no CI step can produce a release artifact with the private key bundled.

## Open Questions

- Should the internal distribution model be online-required (Model A), offline-tolerant (Model B), or hybrid (Model C)? This is a product / ops policy choice; T08 cannot resolve it from code evidence alone.
- What is the operator population size? Under ~20 operators, Model B is operationally cheap; above that, Model C amortizes better.
- Is Authenticode code signing already in place for `backend.exe` and the Electron build? (T06 should answer; T08 currently assumes "not assumed.")
- Is there an existing Barobook auth service that Model A could reuse, or would Model A require building one? (Likely answered jointly with #67.)
- What is the acceptable revocation latency for a leaked license? Model B with 30-day expiry has up to 30-day revocation latency; Model C with weekly online checks has up to 7-day latency; Model A is effectively immediate.
- Is the goal "unauthorized people cannot run the EXE" (license model) or "unauthorized people can run the EXE but cannot drive it" (bridge-auth model) or both? T08's recommendation assumes both.

## Closure Recommendation

T08 closure status: **investigation complete, implementation deferred to consolidated roadmap (per dispatch §7).**

Recommended downstream actions:

- Treat F1 and F2 as the issue-#70 head items in the consolidated security remediation roadmap.
- Treat F4 as a coupling between #66 (secret handling) and #70 (access control) and verify that whichever roadmap slot owns env-key promotion also owns the bridge-auth gate that protects it.
- Defer the Model A vs B vs C policy decision to the merge-plan phase of the consolidated roadmap, where the answers from T01, T03, T05, T06 will be available together.
- When implementation begins, the smallest viable first commit is the per-launch shared secret between Electron and `bridge_server.py` (step 3 of the minimal path); it is independent of license-model selection and immediately closes the local-process-attack class.
- Do not start implementation until the consolidated roadmap or relevant execution SSOT passes the document 3-pass audit with at least 95% confidence (per dispatch §7.5).

## 3-Pass Audit

Pass 1 — structure and scope:

- PASS. Document is a survey/report, not an execution SSOT, and follows the required schema (`Scope` / `Commands / Evidence` / `Findings` / `Remediation Candidates` / `Dependencies On Other Terminals` / `Open Questions` / `Closure Recommendation`).
- PASS. Save path matches the dispatch matrix entry for T08.
- PASS. Scope is bounded to startup chokepoints and authorization-model design; packaging, secret inventory, and Vertex-auth detail are explicitly delegated.

Pass 2 — evidence and consistency:

- PASS. All concrete claims are anchored to file paths and line numbers from inspected source. Evidence section names the read-only commands used.
- PASS. Findings are graded P1 / P2 / P3 in line with dispatch §4.
- PASS. The report does not include raw secret values, credential JSON, or recovery codes. References to environment variable names (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, etc.) are to identifiers in the source, not to values.
- PASS. Dependencies on other terminals are stated as dependencies, not as widening of T08's scope.

Pass 3 — execution and readability:

- PASS. Three feasible authorization models are presented with explicit pros, cons, and bypass classes.
- PASS. The minimal "unauthorized copied EXE does not run normally" path is sequenced so each step is independently valuable and so the first step (per-launch shared secret) does not require choosing a license model.
- PASS. Recommendation explicitly defers final model selection to the consolidated roadmap phase per dispatch §7, avoiding premature commitment.

Estimated operational confidence: 96%.
