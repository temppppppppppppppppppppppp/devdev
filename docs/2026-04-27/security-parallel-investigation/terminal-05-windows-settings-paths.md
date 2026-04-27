# T05 Windows Settings Path Survey

Date: 2026-04-27
Terminal: T05
Primary GitHub issue: #68 [SEC] Move local app settings to approved user config directory
Related issue: #66 [SEC] Remove secrets from code/config and standardize runtime config loading
Workspace: `C:\Users\wjjo\Desktop\글도비`
Baseline commit: `a3d826978d530ab61d3765e5e095890fa6533ea7`
Document type: read-only investigation report (no source code changes)
Mode: read-only, no source/config/git mutation; no secret values printed

## Scope

Survey Windows local settings paths and write-location behavior for the engine (Python), the desktop shell (Electron), and the build/packaging scripts. Identify every place runtime code reads or writes:

- `.env` files
- cwd-relative settings/logs
- `%APPDATA%`, `%LOCALAPPDATA%`, `%PROGRAMFILES%`
- Electron `userData` / `app.getPath(...)`
- install directory / build / dist directories
- arbitrary user-supplied paths

Recommend a single approved Windows path policy. Leave secret-storage mechanism design as a coupled question that overlaps T01 (root secrets) and T03 (Vertex auth). Leave EXE access-control hooks to T08.

Files inspected (each read once, line-numbered evidence below):

- `modules/core/runtime_paths.py`
- `modules/core/config_manager.py`
- `main_a.py` (selected regions only — 227 KB)
- `build/backend_entry.py`
- `build/build_release.ps1`
- `배포_패키징.ps1` (workspace-root packaging script)
- `geuldobi-desktop/main.js` (compatibility shim)
- `geuldobi-desktop/src/main.js` (authoritative Electron entry per `runtime_paths.py:24-28`)
- `geuldobi-desktop/package.json`

Out of scope for T05: full secret inventory (T01), runtime config topology beyond path resolution (T02), Vertex/GCP auth (T03), full desktop IPC surface (T04), release packaging mechanics beyond write-location policy (T06), dev/test separation (T07), EXE access control design (T08), CI guardrails (T09), security-response doc map (T10).

## Commands / Evidence

Read-only inspections only. No `rg` (denied at dispatch baseline). Used `Grep` (ripgrep through tool wrapper) and `Read` against listed paths. Spot checks via `git ls-files`.

### E1. Engine runtime path contract — `modules/core/runtime_paths.py`

- `runtime_paths.py:24-51` defines `RUNTIME_AUTHORITY_CONTRACT`. The only Windows-style path declared here is the desktop pre-bridge boot log:
  - `runtime_paths.py:39-43` — `desktop_pre_bridge.path = "%LOCALAPPDATA%/Geuldobi/electron-main.log"`, authority `desktop_local_appdata`.
  - `runtime_paths.py:44-49` — `engine_bootstrap_fallback.path = "logs/error.log"`, authority `workspace_level`. This is workspace-relative, not `%APPDATA%`-anchored.
- `runtime_paths.py:67-78` — `resolve_engine_root` honors `GEULDOBI_ENGINE_ROOT`, else `Path(default_root).resolve()`. `resolve_workspace_root` honors `GEULDOBI_WORKSPACE`, else falls through to engine root.
- `runtime_paths.py:81-85` — `resolve_projects_root` honors `GEULDOBI_PROJECTS_ROOT`, else `<workspace_root>/projects`.
- `runtime_paths.py:88-102` — `resolve_project_dir` rejects empty names, requires `relative_to(projects_root)` to avoid path traversal, and forbids `candidate == projects_root`. This is correct sandboxing for one specific surface but it does not address the broader `Path.cwd()` usage elsewhere.

Net: this contract names `%LOCALAPPDATA%/Geuldobi/electron-main.log` as the only authoritative Windows-anchored path. Everything else falls back to engine root or workspace root, which is then defined elsewhere as `Path.cwd()` (see E2) or as the desktop-injected `Documents/글도비` (see E5).

### E2. Engine `ConfigManager` — `modules/core/config_manager.py`

- `config_manager.py:20-30` — `__init__` sets `self.root = Path.cwd()`, then unconditionally creates `self.projects_dir = self.root / "projects"` and `self.logs_dir = self.root / "logs"` with `mkdir(parents=True, exist_ok=True)`.
- `config_manager.py:59-60` — `_validation_yaml_path()` returns `self.root / "config/settings/validation.yaml"` (cwd-relative).
- `config_manager.py:62-63` — `_settings_json_path()` returns `self.root / "config" / "settings.json"` (cwd-relative).
- `config_manager.py:65-75` — `_load_agents_from_yaml()` reads `Path(__file__).parent.parent.parent / "config" / "models.yaml"` — engine-root-relative, NOT cwd-relative. So `models.yaml` lives where the source bundle is staged (in packaged mode, `<resources>/engine/config/models.yaml`).
- `config_manager.py:124-155` — both `validation.yaml` and `settings.json` are read via `open(yaml_path, encoding="utf-8")` and `open(json_path, encoding="utf-8")`. Read-only at this surface, but the cwd anchor means the file location is not stable across runtime contexts.
- `git ls-files` confirms `config/models.yaml` and `config/settings.json` are both tracked. (Tracking risk for `config/settings.json` belongs to T01; T05's concern is path policy.)

Net: `ConfigManager` conflates engine source root with operator cwd. In packaged mode the desktop sets `cwd = Documents/글도비` (E5), so `ConfigManager` will look for `<Documents>/글도비/config/settings.json`, which does not ship there. `models.yaml` is the only file currently anchored to a stable engine path.

### E3. Engine boot — `main_a.py`

- `main_a.py:20-24` — `_resolve_boot_error_log_path` returns `os.environ.get("GEULDOBI_WORKSPACE") or os.getcwd()` joined with `logs/error.log`. In packaged mode the env var is injected by Electron (E5); in dev/manual mode this becomes the engine source root.
- `main_a.py:147-149` — `from dotenv import load_dotenv` and immediate `load_dotenv(override=True)` at import time. Per `python-dotenv` defaults, this scans for `.env` starting from cwd upward. So whatever directory the process was launched from supplies API keys via `override=True`, taking precedence over already-set environment variables.
- `main_a.py:386` — `SovereignApp.__init__` re-runs `load_dotenv(override=True)`, with the same cwd-anchored search.
- `main_a.py:365` — `_APP_ROOT = Path(__file__).resolve().parent`. This is the engine source root, used by `_get_projects_root()` and `_get_project_dir()` only as a default for `resolve_projects_root` / `resolve_project_dir`. The actual `GEULDOBI_PROJECTS_ROOT` env var (E5) overrides this in packaged mode.
- `main_a.py:1257-1274` — `_reload_project_environment(project_name)` reads `<project_dir>/.env` and runs `load_dotenv(project_env_path, override=True)`. In packaged mode `<project_dir>` resolves under `Documents/글도비/projects/<name>/`, so per-project secrets land in the user's Documents tree.

Net: `.env` discovery is cwd-anchored at boot, then per-project-anchored after project bind. The boot path is unstable between dev (engine root) and packaged (Documents/글도비). The per-project path puts API keys into the same directory the user opens for manuscripts, with `override=True`.

### E4. Packaged backend entry — `build/backend_entry.py`

- `backend_entry.py:8-23` — when `sys.frozen` (PyInstaller bundle):
  - `backend_dir = dirname(sys.executable)`
  - `resources_dir = dirname(backend_dir)` — i.e., `<install>/resources/`
  - `engine_root = resources_dir / engine`
  - `python_path = resources_dir / python-embed / python.exe`
  - `workspace_root = environ.get("GEULDOBI_WORKSPACE") or os.getcwd()` — relies on Electron to inject the env var; if absent, falls through to cwd, which is set by Electron to `Documents/글도비` (E5) in packaged mode. In a manually-launched `backend.exe` (no Electron parent), workspace_root becomes whatever the user's cwd was.
  - sets `GEULDOBI_ENGINE_ROOT`, `GEULDOBI_PYTHON_PATH`, defaults `GEULDOBI_PACKAGED_RUNTIME_MODEL` and `GEULDOBI_PROJECTS_ROOT = workspace_root/projects`.
- `backend_entry.py:31` — runs `uvicorn.run(app, host="127.0.0.1", port=8300, ...)`.

Net: `engine_root` and `python_path` come from the executable location (read-only Program Files area). `workspace_root` defaults to cwd, which is operator-controlled. No `%APPDATA%`/`%LOCALAPPDATA%` policy is enforced at this layer; it is delegated to the Electron parent.

### E5. Electron authoritative entry — `geuldobi-desktop/src/main.js`

(`geuldobi-desktop/main.js` is a one-line shim re-exporting `src/main.js` per `geuldobi-desktop/main.js:1-9`.)

- `src/main.js:1-15` — imports `electron`, `fs`, `os`, `path`. Defines `EARLY_DEBUG_LOG_PATH = path.join(process.env.LOCALAPPDATA || os.homedir()/AppData/Local, "Geuldobi", "electron-main.log")`. Matches the contract in `runtime_paths.py:39-43`.
- `src/main.js:30-31` — `fs.mkdirSync` + `fs.appendFileSync` writes there. mkdir recursive is correct.
- `src/main.js:194-203` — `getLocalAppDataRoot()` returns `process.env.LOCALAPPDATA` on win32, else `homedir/AppData/Local`. `getAppDir()` returns `<localAppData>/Geuldobi`. This is the single Electron-side application config root.
- `src/main.js:206-213` — `getWorkspaceDir()`:
  - `app.isPackaged` → `app.getPath("documents")/글도비` (Korean-named, may be in OneDrive-redirected Documents).
  - dev mode → `path.resolve(__dirname, "..", "..")` (project root).
- `src/main.js:215-216` — `getPackagedWorkspaceSeedDir()` returns `process.resourcesPath/workspace-seed` (read-only, under install dir).
- `src/main.js:241-269` — `syncPackagedWorkspaceSeed()` copies `bible/`, `treatments/`, `projects/` from the read-only seed into the user's Documents/글도비 only if the destination does not already exist. mkdir recursive on workspace.
- `src/main.js:271` — `SETTINGS_PATH = path.join(getAppDir(), "settings.json")` — i.e., `%LOCALAPPDATA%/Geuldobi/settings.json`.
- `src/main.js:299-303` — `persistDesktopSettings(path, settings)` mkdir recursive then `fs.writeFileSync(... JSON.stringify(settings, null, 2), "utf8")`.
- `src/main.js:273-296` — `buildDefaultDesktopSettings()` declares the schema persisted there: `apiKey1`, `extraKeys`, `slackWebhook`, `timeout`, `keyRotate`, `qualityGate`, `targetLength`, `project`. Confirms that **API keys and Slack webhook are stored in plaintext JSON inside `%LOCALAPPDATA%/Geuldobi/settings.json`**. (T05 records the location only; T01/T03 own the secret-storage redesign.)
- `src/main.js:386-396` — `ensureFirstRunFlag()` writes `<appDir>/.first_run` ISO timestamp.
- `src/main.js:463-506` — `startBackend()`:
  - dev: `cmd = process.env.PYTHON_PATH || "python"`, `cwd = path.resolve(__dirname, "..", "..")` (engine root).
  - packaged: `cmd = process.resourcesPath/backend/backend.exe`, `workspace = getWorkspaceDir()` (= `Documents/글도비`), `fs.mkdirSync(workspace, recursive)`, `cwd = workspace`. Spawns with env `GEULDOBI_PACKAGED_RUNTIME_MODEL`, `GEULDOBI_WORKSPACE = Documents/글도비`, `GEULDOBI_PROJECTS_ROOT = Documents/글도비/projects`.
- `src/main.js:860-882` — `bridge.saveSettings` IPC handler writes to `SETTINGS_PATH` after `serializeDesktopSettingsPayload`. `bridge.loadSettings` reads from the same path.
- `src/main.js:886-898` — `getEngineRoot()` packaged → `process.resourcesPath/engine`, dev → engine root. `getMaterialRoot()` packaged → `getWorkspaceDir()` (Documents/글도비), dev → engine root.
- `src/main.js:901-902` — `getMaterialVisibilityConfigPath()` = `<materialRoot>/config/material_visibility.json`. In packaged mode this is `Documents/글도비/config/material_visibility.json`, while the engine ConfigManager (E2) is reading `<cwd>/config/settings.json` from the same Documents directory. So the desktop and the Python engine **share a Documents-rooted config dir at runtime** — but the desktop owns `%LOCALAPPDATA%/Geuldobi/settings.json` separately.
- `src/main.js:1013-1018` — `getProjectsDir()` packaged → `<workspace>/projects`, dev → `<engineRoot>/projects`.
- `src/main.js:1043-1048` — `getWorkGuardLibraryDir()` packaged → `<workspace>/work_guards`, dev → engine-root-adjacent.
- `src/main.js:1140-1205` — `author_directives.txt` and `work_guard.yaml` are read/written under each project's `config/` directory inside the workspace.

Net: the Electron side enforces a clean two-zone policy in packaged mode: `%LOCALAPPDATA%/Geuldobi/` for app settings and debug logs, `Documents/글도비/` for user-visible artifacts. Engine-side code (E2/E3) does not yet honor that split.

### E6. Electron `package.json` build manifest — `geuldobi-desktop/package.json`

- `package.json:33-36` — Windows target = NSIS, `signAndEditExecutable: false`. Code signing is therefore disabled at this layer (T06/T08 concern, recorded for context).
- `package.json:37-44` — `nsis.allowToChangeInstallationDirectory: true`. Operator may install outside `%PROGRAMFILES%\Geuldobi`. As long as the install directory is treated read-only by runtime code (which is currently the case for `process.resourcesPath`), this is acceptable, but a non-standard install location combined with `cwd = Documents/글도비` means there is no fixed `Program Files` assumption.
- `package.json:45-86` — `extraResources` bundles `dist/backend`, `dist/engine`, `python-embed`, `dist/workspace-seed` into the install directory. Filters exclude `*.log`, `*.tmp`, `*.bak` — they do not exclude `.env`, credentials, or stray secrets in those staging directories. (T06 owns the bundling-exclusion redesign; T05 only flags the path.)

### E7. Build script — `build/build_release.ps1`

- `build_release.ps1:26-37` — defines `PROJECT_ROOT`, `BUILD_DIR`, `DIST_DIR = PROJECT_ROOT/dist`. All paths are relative to the script location. No hardcoded `C:\` paths.
- `build_release.ps1:75-91` — `Sync-EngineBundle` stages `main_a.py`, `modules`, `config`, `datasets`, `libraries`, `lite_mode` into `dist/engine`. So `config/` (including `config/settings.json` and `config/models.yaml`) is shipped to the install directory. Coupled to T01/T06.
- `build_release.ps1:138-144` — runs `geuldobi-desktop/scripts/build_workspace_seed.py` to populate `dist/workspace-seed`. The seed contents become the initial Documents/글도비 tree on first run (E5).
- `build_release.ps1:158-159` — verifies packaged resources under `geuldobi-desktop/dist/win-unpacked/resources/`.

Net: build output writes only under workspace-relative `dist/`. Path policy at this layer is fine. The risk is what the bundle includes (T01/T06).

### E8. Workspace ZIP packaging — `배포_패키징.ps1`

- `배포_패키징.ps1:5` — `$output = "C:\gldobi_deploy.zip"`. Hardcoded absolute path under `C:\`.
- `배포_패키징.ps1:79` — `$tempDir = "C:\gldobipack_temp"`. Hardcoded absolute path under `C:\`.
- `배포_패키징.ps1:8-32` — folder excludes include `.git`, `.venv`, `projects`, `logs`, `lite_mode`, `test_mode`, `datasets`, `tools`, `tools2`, `scripts`. Note that `lite_mode`, `test_mode`, `datasets`, `tools`, `tools2`, and `scripts` are excluded here but `build_release.ps1:81-84` re-bundles `lite_mode` and `datasets` into `dist/engine`. Two scripts disagree about what counts as production payload (handoff to T06/T07).
- `배포_패키징.ps1:35-44` — file excludes include `.env`, `crash_dump.log`, `error.log`. They do **not** exclude `geuldobi-vertex-key.json`, `github-recovery-codes.txt`, or the `secrets/` directory. These are all root-level files per the dispatch evidence basis (`security-issues-parallel-investigation-dispatch.md:43`). Redacted-finding-only here; T01 owns the leak inventory.
- `배포_패키징.ps1:54-95` — collects via recursive `Get-ChildItem` from script directory, copies into the hardcoded temp dir, then `Compress-Archive`. No write to `%APPDATA%` or `%LOCALAPPDATA%`.

Net: packaging script writes outside the workspace into hardcoded `C:\gldobi_deploy.zip` / `C:\gldobipack_temp`. Requires write access to `C:\` root and is not policy-compliant from a Windows path standpoint. Exclusion list is partial.

## Findings

Severity uses dispatch §4 levels. T05 owns path-policy findings only; secret-handling and packaging findings are flagged here for the right terminal.

### F1 [P0, T05] — `ConfigManager.root = Path.cwd()` is a runtime path-policy violation

`modules/core/config_manager.py:21-30,60,63` anchors `projects_dir`, `logs_dir`, `validation.yaml`, and `settings.json` to whatever directory the Python process was started in. In packaged mode the desktop forces `cwd = Documents/글도비` (E5), but in any other launch context (manual `python main_a.py`, automation, `pytest`, future install variants) the same code writes `projects/` and `logs/` into the engine source bundle or the operator's terminal cwd. This makes the path policy unstable and undermines a single-approved-path claim.

Why P0: it is the one place that reaches into the filesystem and creates directories at import time without consulting the runtime authority contract from `runtime_paths.py`. Coupled to #66 because `config/settings.json` is currently committed to the engine source tree.

### F2 [P0, T05] — Engine boot `load_dotenv(override=True)` runs against unbounded cwd

`main_a.py:147-149,386` runs `load_dotenv(override=True)` at module import and again in `SovereignApp.__init__`. python-dotenv resolves `.env` by walking up from cwd. In dev mode this is the workspace root (which historically held `.env`). In packaged mode this is `Documents/글도비`, which is user-writable and may be OneDrive-synced. Anyone who drops a `.env` into the workspace overrides the Electron-injected environment with `override=True`.

Why P0: silent override of credential environment variables based on an operator-controlled path is a credential-hijack surface. Coupled to #66 (#67 if it touches Vertex creds). T03 owns the Vertex-specific implication.

### F3 [P1, T05] — Per-project `.env` lives inside the user's Documents tree with `override=True`

`main_a.py:1257-1274` reads `<project_dir>/.env` and runs `load_dotenv(...override=True)`. In packaged mode `<project_dir>` resolves under `Documents/글도비/projects/<name>/`. Result: every project gets a plaintext credential file inside the user's documents folder, eligible for OneDrive backup and easy file-share. The `override=True` flag means a project-local `.env` silently outranks `%LOCALAPPDATA%` settings.

Why P1: legitimate per-project credential isolation is reasonable, but the location and the `override=True` semantics create a credential-sprawl pattern that contradicts Issue #68's "approved user config directory" goal. Recommend moving per-project credentials into a sibling structure under `%LOCALAPPDATA%/Geuldobi/projects/<name>/` and switching to `override=False` so that user-level settings take precedence.

### F4 [P1, T05] — Two `settings.json` surfaces with disjoint owners

- `%LOCALAPPDATA%/Geuldobi/settings.json` (Electron, `src/main.js:271,299-302,860-882`) holds `apiKey1`, `extraKeys`, `slackWebhook`, etc. in plaintext.
- `<engine_root_or_cwd>/config/settings.json` (Python, `config_manager.py:62-63,134-155`) holds validation thresholds and similar config, currently tracked in git.

These two files share a name and an owner-blurry purpose. The Python side has no view of the Electron settings file, and the Electron side has no view of the engine's `validation.yaml`. Future contributors may store the same setting in both files.

Why P1: it is a path-policy ambiguity that affects #68 directly. Recommend renaming one of them (for example, the engine-side file to `config/runtime_validation.yaml`-only) so there is a single canonical `settings.json` that always lives under `%LOCALAPPDATA%/Geuldobi/`.

### F5 [P1, T05] — `runtime_paths.py` contract acknowledges only one Windows path

`runtime_paths.py:39-43` is the only place in the engine that names `%LOCALAPPDATA%`, and only for the desktop pre-bridge boot log. The contract does not declare:

- where settings.json should live (Electron decided unilaterally),
- where per-project secrets should live,
- whether logs should ever land outside the workspace.

Why P1: there is no engine-owned policy text to point new code at. Adding 2–3 entries to `RUNTIME_AUTHORITY_CONTRACT` would close most of the remaining ambiguity without rewriting any actual loader.

### F6 [P1, T05] — `backend_entry.py` falls through to cwd when Electron does not inject env

`build/backend_entry.py:13` — `workspace_root = os.environ.get("GEULDOBI_WORKSPACE") or os.getcwd()`. If a user double-clicks `backend.exe` directly (no Electron parent), workspace_root becomes the operator's working directory, which by default is the install directory under `Program Files` for explorer launches. The backend then attempts to mkdir `projects/` and `logs/` under the install root, which will fail under standard Windows ACLs and may emit a confusing error or partially write into a temp shadow.

Why P1: Issue #68 expects the runtime to never assume install-dir write access. Recommend hardcoding a fallback of `<%LOCALAPPDATA%>/Geuldobi/workspace` in `backend_entry.py` instead of `os.getcwd()`, so a stray launch still lands under the user's writable area.

### F7 [P2, T05 → T06] — `배포_패키징.ps1` writes to hardcoded `C:\` paths

`배포_패키징.ps1:5,79` — output `C:\gldobi_deploy.zip`, temp `C:\gldobipack_temp`. This is a developer convenience script that is shipped in-tree, not an end-user installer. Path policy still matters because contributors run it locally and any partial run leaves residue at `C:\`.

Why P2: not a runtime user-facing surface, but the file lives in the workspace and is cited by #69/#70 territory. T06 owns release packaging design; T05 records the path violation only.

### F8 [P2, T05 → T01/T06] — packaging exclusion lists and bundle inclusion conflict on path policy

- `배포_패키징.ps1:8-44` excludes `.env`, `lite_mode`, `test_mode`, `datasets`, `scripts`, `tools`, `tools2`, `projects`, `logs`. Does **not** exclude `geuldobi-vertex-key.json`, `github-recovery-codes.txt`, `secrets/`, `dist/`, `build/`, `geuldobi-desktop/`.
- `build/build_release.ps1:81-84` (`Sync-EngineBundle`) re-bundles `lite_mode` and `datasets` into `dist/engine`, contradicting the ZIP exclusion list.
- `geuldobi-desktop/package.json:45-86` filter excludes `*.log,*.tmp,*.bak` only; does not strip `.env` or credentials staged into `dist/backend` or `dist/engine`.

Why P2 from T05's path-policy angle (T01/T06 will own the actual fix): these surfaces decide which files end up where on a target machine. They should agree.

### F9 [P3, T05] — `Documents/글도비` is a non-ASCII workspace path

`src/main.js:209` — `path.join(documentsDir, "글도비")`. Korean directory name is intentional for user discoverability. It interacts cleanly on modern Windows, but tooling that assumes ASCII or uses naive `cp949` parsing (already a known workspace risk per AGENTS.md UTF-8 rules) can mis-handle it. Document this as the canonical workspace path and ensure all logging serializes it as UTF-8.

Why P3: low likelihood, but worth pinning in the policy table so future code does not silently rename to ASCII.

## Remediation Candidates

T05 proposes only path-policy changes; secret-storage redesign belongs to T01/T03, packaging redesign to T06.

### R1 — Approved Windows path policy table (proposal)

| Surface | Approved path | Owner | Writable by runtime |
| --- | --- | --- | --- |
| App settings (non-secret) | `%LOCALAPPDATA%/Geuldobi/settings.json` | Electron | yes |
| App debug log (pre-bridge) | `%LOCALAPPDATA%/Geuldobi/electron-main.log` | Electron | yes |
| Credential vault (secrets) | `%LOCALAPPDATA%/Geuldobi/secrets/` (DPAPI- or OS-keychain-backed; never plaintext settings.json) | Electron + engine bridge | yes — per-key separately |
| User workspace root | `%USERPROFILE%/Documents/글도비/` | Electron | yes |
| Project artifacts | `<workspace>/projects/<name>/` | engine | yes |
| Project per-run logs | `<workspace>/projects/<name>/logs/` | engine | yes |
| Engine boot fallback log | `<workspace>/logs/error.log` | engine | yes |
| Engine source bundle | `<install_dir>/resources/engine/` | installer | **no** (read-only at runtime) |
| Embedded Python | `<install_dir>/resources/python-embed/` | installer | **no** |
| Workspace seed | `<install_dir>/resources/workspace-seed/` (copied lazily into Documents/글도비 on first run) | installer | **no** |

This is a documentation-only artifact for now. Wire-up belongs to a future implementation wave.

### R2 — Add policy entries to `runtime_paths.py:RUNTIME_AUTHORITY_CONTRACT`

Append `user_settings_path` (`%LOCALAPPDATA%/Geuldobi/settings.json`), `user_workspace_path` (`Documents/글도비`), `secret_store_path` (`%LOCALAPPDATA%/Geuldobi/secrets/`), and `engine_install_root` (`<install>/resources/engine`, read-only). Keep the existing `boot_log_surfaces` block.

### R3 — Make `ConfigManager.root` honor the runtime authority contract

Replace `Path.cwd()` with `resolve_workspace_root(_APP_ROOT)` (or an analogous helper that honors `GEULDOBI_WORKSPACE`). Stop creating `projects/` and `logs/` inside `__init__` for `Path.cwd()`. Keep `models.yaml` resolution as `Path(__file__).parent.parent.parent / "config" / "models.yaml"` (engine-anchored) — that one is correct.

### R4 — Defer or relocate engine-level `load_dotenv(override=True)`

Either:

- (preferred) drop `load_dotenv` calls from `main_a.py:149,386` entirely, in favor of explicit env loading from a single `%LOCALAPPDATA%/Geuldobi/.env` (or the secret store from R1), or
- (minimal) restrict `load_dotenv` to a known absolute path resolved through `runtime_paths.py`, and switch `override=True` to `override=False` so user-level settings are not silently shadowed by a stray `.env`.

T03 should make the call on the Vertex/GCP side.

### R5 — Migrate per-project `.env` to a controlled location

`main_a.py:1257-1274` should read project credentials from `%LOCALAPPDATA%/Geuldobi/projects/<name>/credentials.env` (or the R1 secret store keyed by project name), not from `<workspace>/projects/<name>/.env`. Switch to `override=False`. Decision shared with T01 and T03.

### R6 — Harden `backend_entry.py` fallback

Replace `os.environ.get("GEULDOBI_WORKSPACE") or os.getcwd()` with `os.environ.get("GEULDOBI_WORKSPACE") or os.path.join(os.environ["LOCALAPPDATA"], "Geuldobi", "workspace")`. This guarantees a writable workspace even when `backend.exe` is launched without the Electron parent.

### R7 — Repath `배포_패키징.ps1` outputs

Change hardcoded `C:\gldobi_deploy.zip` and `C:\gldobipack_temp` to a script-relative `dist/release/` (or `$env:LOCALAPPDATA/Geuldobi/release-staging/`). Adds nothing to security guarantees by itself; it is path-policy hygiene the in-tree script should respect. Implementation belongs to T06.

## Dependencies On Other Terminals

- **T01 (root secret inventory)**: must decide what to do with `geuldobi-vertex-key.json`, `github-recovery-codes.txt`, `secrets/`, the tracked `config/settings.json`, and the historically committed root `.env`. T05's path policy assumes those are removed/relocated. The `%LOCALAPPDATA%/Geuldobi/secrets/` proposal in R1 is conditional on T01's verdict.
- **T02 (runtime config topology)**: needs to confirm whether collapsing `validation.yaml` and `settings.json` into a single user-side file is feasible, and whether there are other config surfaces (e.g., `config/models.yaml`) that should keep their current engine-anchored location.
- **T03 (Vertex auth)**: owns the `GOOGLE_APPLICATION_CREDENTIALS` migration; T05's R4/R5 must not contradict whatever Vertex's auth flow ends up doing.
- **T04 (desktop config surfaces)**: should confirm there is no other Electron-side write target (e.g., `localStorage`, hidden cache files in `app.getPath("userData")`) beyond the ones T05 listed, and that the IPC surface for `bridge.saveSettings` does not also write to a second location.
- **T06 (release packaging)**: owns the actual exclusion-list redesign for `배포_패키징.ps1`, `build/build_release.ps1`, and `geuldobi-desktop/package.json:extraResources`. T05's findings F7/F8 hand off there.
- **T07 (dev/test separation)**: owns the `lite_mode`/`test_mode`/`datasets` bundling-vs-excluding contradiction noted in F8. T05 only flags the path mismatch.
- **T08 (EXE access control)**: needs to know that `backend.exe` is currently launchable directly (E4, F6) without Electron, which is one of the chokepoints for Issue #70.
- **T09 (CI guardrails)**: should add a guard that asserts `Path.cwd()` is not used as a config root in `modules/core/`.
- **T10 (security response doc map)**: T05's R1 path policy table is intended as raw input for the consolidated security response document.

## Open Questions

1. Does the project want a single `%LOCALAPPDATA%/Geuldobi/settings.json` that holds both Electron-managed settings and Python-managed validation thresholds, or two files (`settings.json` for user prefs, `runtime_validation.yaml` for engine policy)?
2. Should secret material live in (a) DPAPI-protected store via Windows Credential Manager, (b) a separate `%LOCALAPPDATA%/Geuldobi/secrets/` directory with restrictive ACL, or (c) an external KMS? T05 cannot decide alone.
3. For per-project credentials, should the override behavior be removed entirely (single global vault) or preserved (per-project isolation) but in a non-Documents path?
4. Is the current ASCII fallback `path.join(os.homedir(), "AppData", "Local")` (E5, `src/main.js:198`) acceptable, or should the desktop hard-fail when `process.env.LOCALAPPDATA` is missing? On modern Windows this fallback is fine, but the dual code path adds an attack surface for env-spoofing.
5. Does the operator want `Documents/글도비` to remain the Korean-named user workspace, or is there appetite to switch to an ASCII path under `%PUBLIC%/Documents` to simplify CI tooling?

## Closure Recommendation

T05 alone cannot close Issue #68. T05 produces:

- a documented current-state map of every Windows-relevant read/write path (E1–E8),
- a proposed approved-path table for the workspace (R1) ready for review,
- a list of code-level remediations (R2–R7) with explicit dependencies on T01, T02, T03, T04, T06, T07, T08, T09, T10.

Proposed closure path for #68:

1. Land R1 (the path policy table) as a documentation artifact under `docs/2026-04-27/security-parallel-investigation/` after T01–T10 finish, merged through T10's security response doc.
2. Implement R2 (`runtime_paths.py` contract entries) as a small follow-up phase scoped to the engine, no behavior change.
3. Implement R3 (`ConfigManager.root` switch) and R6 (`backend_entry.py` fallback) together as the first behavior change. Coordinate with T02 to confirm no other consumer relies on `Path.cwd()`.
4. Implement R4/R5 (`load_dotenv` migration) only after T01 and T03 publish their secret-storage decisions.
5. Implement R7 in a packaging follow-up owned by T06.
6. Closure of #68 itself happens after R3 and R6 ship and a fresh packaged run shows zero writes outside `%LOCALAPPDATA%/Geuldobi/` and `Documents/글도비/`.

T05 confidence: high on the current-state mapping; moderate on R1 because secret storage and per-project isolation policy still need T01/T03 input. No source code was modified in this wave.

---

3-pass audit (T05-internal):

- Pass 1 — structure: scope, commands/evidence, findings, remediation, deps, open questions, closure all present and in dispatch order. PASS.
- Pass 2 — evidence: each finding cites file path and line range; no raw secret values printed; severity labels per dispatch §4. PASS.
- Pass 3 — readability/handoff: dependencies on T01–T10 explicit; remediations are recommendations, not patches; UTF-8 safe; Korean path `글도비` retained as authoritative workspace name. PASS.

Estimated T05-internal confidence: 95%.
