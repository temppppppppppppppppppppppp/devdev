# T02 Runtime Config Loading Topology

Terminal: T02
Primary GitHub issues: #66 (`[SEC] Remove secrets from code/config and standardize runtime config loading`), #68 (`[SEC] Move local app settings to approved user config directory`)
Workspace: `C:\Users\wjjo\Desktop\글도비`
Baseline commit: `a3d826978d530ab61d3765e5e095890fa6533ea7` (per dispatch §1)
Document type: read-only investigation report. Not an execution SSOT, not a source-code patch order.
Mode: read-only. No source/config/env/GitHub/git state was modified during this investigation.

## Scope

Map the Python runtime config loading and settings-ownership topology so #66 (secret-handling standardization) and #68 (approved settings location) can be planned without ambiguity about which file is authoritative for what.

In-scope file inspection (full reads):
- `main_a.py` (227 KB; full grep + targeted reads at L140-174, L385-399, L1248-1274, L1418-1450, L1934-1955)
- `modules/core/config_manager.py`
- `modules/core/models_config.py`
- `modules/core/runtime_paths.py`
- `modules/core/llm_provider.py`
- `modules/core/llm_router.py`
- `modules/core/provider_mode.py`
- `config/models.yaml`
- `config/settings.json`
- `config/settings/validation.yaml` (existence + tracking confirmed; not full-read)

Explicitly out of scope (owned by other terminals):
- Root secret inventory (T01).
- Vertex AI / Google auth flow detail (T03). T02 only maps the registration surface in the router.
- Electron / desktop config surfaces and IPC (T04).
- Windows write-location policy and APPDATA target (T05).
- Release packaging inclusion/exclusion (T06).
- `tools/`, `tests/`, `scripts/`, `smoke_sc.py`, `visual_lab/` `load_dotenv` sites (T07).

## Commands / Evidence

Primary read-only commands run from workspace root:

- `git ls-files | grep -E '^(main_a\.py|modules/core/(config_manager|models_config|runtime_paths|llm_provider|llm_router|provider_mode)\.py|config/(models\.yaml|settings\.json))$'` → confirmed all 9 in-scope files are tracked.
- `git ls-files config/` → confirmed `config/models.yaml`, `config/settings.json`, and `config/settings/validation.yaml` are all tracked.
- `ls config/settings/` → confirmed `validation.yaml` exists on disk (alongside `item_suffixes.yaml`, `stage4_policy_digest.json`).
- Grep over `main_a.py` for `dotenv|load_dotenv|\.env|settings|config|models\.yaml|runtime_paths|APPDATA|LOCALAPPDATA|Program Files` (case-insensitive) → 4 distinct `load_dotenv` sites in `main_a.py` (L147, L149, L386, L1263), plus settings/config call sites at L1437, L1443, L1937-1947.
- Repo-wide grep `load_dotenv|from dotenv|import dotenv` → all matches outside the in-scope set are in `tools/`, `tests/`, `scripts/`, `smoke_sc.py`, `visual_lab/` (T07 territory; flagged as dependencies, not findings).
- Grep `os\.environ\[|os\.environ\.setdefault|os\.environ\.update|os\.environ\.pop|environ\.clear` over `modules/core/` → **no matches**. Core modules only read env via `os.environ.get` / `os.getenv`. Mutation is concentrated in `main_a.py` `load_dotenv(...)` calls.
- Grep `os\.environ\[|setdefault|update|pop|clear` over `main_a.py` → **no matches**. Confirms `main_a.py` mutates env only through `load_dotenv(...)`.

Secret-handling stance during investigation:
- No raw `.env` / credential JSON / token / API-key values were opened, copied, printed, or saved.
- All findings reference paths and line numbers only; no value bytes are quoted.

## Findings

Severity legend per dispatch §4: `P0` highest, `P3` lowest.

### F1 — Module-import-time `.env` load mutates process env globally on every import (P1)

Where: `main_a.py:147-149`

```
from dotenv import load_dotenv
load_dotenv(override=True)  # comment claims: Slack 알림용 환경변수 먼저 로드
```

What it does:
- `load_dotenv()` with no path falls back to dotenv's CWD-walk discovery to locate a `.env`.
- `override=True` forces values from the discovered `.env` to **replace** any pre-set `os.environ` entries (e.g., values injected by Electron parent process, CI runner, or system env).
- Runs unconditionally at module-import time, before `SovereignApp` ever instantiates.

Risk for #66:
- Any process that imports `main_a` inherits this mutation, including unintended importers (smoke scripts, helper modules, ad-hoc REPL). Today the obvious importers are intentional (`build/backend_entry.py` → `main_a`), but the surface is wider than the runtime entry chain in `runtime_paths.RUNTIME_AUTHORITY_CONTRACT`.
- `override=True` defeats the parent-process secret-injection model that the desktop/bridge layer might want to use for #66. If the desktop later wants to push runtime credentials through environment without touching disk, the on-disk `.env` would silently win.

### F2 — Project-scoped `.env` reload mutates process-global env without snapshot/restore (P1; documented multi-project P0 risk)

Where: `main_a.py:1257-1274` (`SovereignApp._reload_project_environment`)

```
project_env_path = self._get_project_dir(project_name) / ".env"
...
load_dotenv(project_env_path, override=True)
...
self.sys = StudioSystem(api_client=build_google_genai_client())
get_shared_llm_router(force_reload=True)
BaseAgent.refresh_runtime_provider_state()
BaseAgent._init_api_keys()
```

What it does:
- Reads `projects/<name>/.env` and overlays it onto process `os.environ` with `override=True`.
- Couples the env mutation with `StudioSystem` rebuild, LLM router force-reload, and `BaseAgent` provider-state refresh — so "config-only reload" cannot be expressed without rebuilding runtime objects.

Risk for #66:
- Process-global env mutation is documented as **safe today** in `docs/2026-04-06/5arc-terminal2-control-plane-topology-survey.md` only because the boot flow never re-binds two projects in one process. The prior survey labels this as **P1 today, P0 if multi-project ever lands**. Same conclusion holds at the current commit.
- No env snapshot is taken before the overlay. After running this path with project A's `.env`, then project B's `.env`, A's keys remain in `os.environ` for any name not present in B's `.env`. This is silent cross-project leakage.
- The reloader does not redact / clear `VERTEX_API_KEY`, `VERTEX_PROJECT_ID`, `VERTEX_LOCATION`, `GOOGLE_APPLICATION_CREDENTIALS`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, or `GOOGLE_API_KEY` between projects.

### F3 — `SovereignApp.__init__` calls `load_dotenv(override=True)` again, redundant with module-import-time call (P3)

Where: `main_a.py:386`

```
def __init__(self):
    load_dotenv(override=True)
    ...
```

What it does:
- A second cwd-relative `.env` overlay at instance construction.

Risk:
- Low security risk on its own. Concern is **provenance ambiguity** — readers of the codebase cannot tell from a single grep whether the canonical secret-load happens at import (L149), at `__init__` (L386), or at project rebind (L1263). All three exist. This redundancy makes #66 remediation harder to validate because there is no single chokepoint to instrument.

### F4 — Two divergent code paths resolve `config/models.yaml`, only one honors `GEULDOBI_ENGINE_ROOT` (P2)

Where:
- `modules/core/models_config.py:111-121` — `resolve_models_yaml_path()`:
  - Reads `os.environ["GEULDOBI_ENGINE_ROOT"]` if set (this is the path `build/backend_entry.py` sets in packaged mode per the file's own docstring).
  - Otherwise falls back to `Path(__file__).resolve().parents[2] / "config" / "models.yaml"`.
- `modules/core/config_manager.py:65-75` — `_load_agents_from_yaml()`:
  - Hardcodes `Path(__file__).parent.parent.parent / "config" / "models.yaml"`.
  - Ignores `GEULDOBI_ENGINE_ROOT`.

What it does:
- Two readers of the same logical file, with different resolution policies. In dev mode (running from repo root) they happen to coincide because `__file__` of both modules sits at `modules/core/...` and the parent walk lands on the repo root.
- In packaged / frozen mode (PyInstaller), `__file__` of frozen modules can resolve under the extraction directory. The env-aware path will follow `GEULDOBI_ENGINE_ROOT`; the env-unaware path may not.

Risk for #66:
- "Authoritative source" of model routing data has two readers with potentially divergent resolution when packaged. Even if both happen to land on the same file today, the design lets them drift. Anyone debugging "which models.yaml did the runtime actually read?" must inspect both resolvers.

### F5 — `config/settings.json` has two readers with different fallback orders (P2)

Where:
- `modules/core/config_manager.py:62-63, 134-155` — `ConfigManager._settings_json_path()` returns `Path.cwd() / "config" / "settings.json"`. Cached via `_settings_json_cache`. Used by `get_guard_threshold_contract()` as the **compatibility** layer for validation thresholds.
- `main_a.py:1934-1947` — `SovereignApp._load_validation_settings()` does its own direct read:
  - First try: `self.current_project.paths.config / "settings.json"` (project-scoped).
  - Fallback: `Path("config/settings.json")` (cwd-relative root config).
  - Returns `{}` on `FileNotFoundError | json.JSONDecodeError | OSError`.
  - Bypasses `ConfigManager.load_settings_json()` entirely. No cache, no provenance contract.

What it does:
- Two paths into the same file with different scoping rules and no shared cache. Project-scoped read can shadow root config silently.

Risk for #66 / #68:
- Settings-ownership is genuinely ambiguous: is the canonical `settings.json` the project copy or the root copy? `ConfigManager` says root; `_load_validation_settings` says project-then-root. The two callers will disagree if a project ships its own `settings.json`.
- Cwd-relative reads in both paths break the moment `cwd != engine root` (see F8).

### F6 — `validation.yaml` is the documented authoritative source; settings.json `validation.*` is compatibility (clarification, not a finding) (P3)

Verified evidence:
- `config_manager.py:177-211` (`get_guard_threshold_contract`) labels `config/settings/validation.yaml:<key>` as `authoritative_source` and `config/settings.json:validation.<key>` as `compatibility_source`.
- `git ls-files` confirms `config/settings/validation.yaml` is tracked.
- `ls config/settings/` confirms it is present on disk.

This is consistent design, not a defect. Recorded here only because the dispatch flagged "undocumented fallback order" as a concern; T02 confirms the order **is** documented in `get_guard_threshold_contract` provenance fields (`authoritative_source`, `compatibility_source`, `effective_source`, `used_compatibility`). Good model. The only risk is that callers who skip `ConfigManager` (e.g., F5) lose this provenance.

### F7 — Provider env-var registry is name-only, but documents `GOOGLE_APPLICATION_CREDENTIALS` as a Vertex auth surface (P2 — T03 dependency)

Where: `modules/core/llm_router.py:18-37` (`DEFAULT_PROVIDER_CONFIGS`).

What it does:
- Registers env-var **names** for secret material (`GOOGLE_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `VERTEX_API_KEY`, `VERTEX_PROJECT_ID`, `VERTEX_LOCATION`, `GOOGLE_APPLICATION_CREDENTIALS`).
- Does **not** read or store secret values. Names are passed into provider constructors (`_build_provider`) which read env at call time.
- Provider configs can be overridden by `config/models.yaml:providers.*` via `_load_provider_configs()`.

Risk for #66 / #67:
- Clean name-only separation. No secrets in code or YAML.
- However, by listing `GOOGLE_APPLICATION_CREDENTIALS` (path to service-account JSON) as a supported auth surface, the runtime advertises that "service-account JSON file at a configurable path" is a valid bootstrap. T01 has flagged a `geuldobi-vertex-key.json` at repo root; that file is the consumer side of this contract. This is a legitimate Google SDK pattern, but it means the secret-handling story for #66 must specifically address "where does the service-account JSON live, and how does runtime discover it?" Pure env-var rotation alone is insufficient.
- T03 owns the full Vertex/GCP auth flow and Barobook account migration question. T02 only flags the registration surface.

### F8 — Cwd-relative path resolution defeats the engine-root anchor and conflicts with #68 intent (P1)

Where:
- `config_manager.py:21` — `self.root = Path.cwd()` (ConfigManager root).
- `config_manager.py:62-63` — `self.root / "config" / "settings.json"`.
- `config_manager.py:59-60` — `self.root / "config/settings/validation.yaml"`.
- `main_a.py:1939` — `Path("config/settings.json")` fallback.
- `main_a.py:147-149, 386` — `load_dotenv()` no-path discovery walks cwd upward.

What it does:
- All four sites resolve config via the process's working directory rather than via `runtime_paths.resolve_engine_root(...)`.

Risk for #68:
- When a packaged EXE is launched from somewhere other than the engine root (Electron main, double-click from arbitrary folder, scheduled-task working directory), these reads silently miss and either return `{}` or read a *different* file from the user's cwd if one happens to be there.
- `runtime_paths.py:67-78` already provides `resolve_engine_root(default)` (env override `GEULDOBI_ENGINE_ROOT`) and `resolve_workspace_root(default)` (env override `GEULDOBI_WORKSPACE`). These are the right anchors. Neither `ConfigManager` nor the inline `_load_validation_settings` use them.
- This conflicts directly with #68 intent ("Move local app settings to approved user config directory"). Today, settings.json lives at engine-root `config/`, but at runtime it is read from cwd, which can be neither the engine root nor an approved Windows user config directory.

### F9 — Provider-mode rewriter and forced-model pin are env-driven escape hatches (P3 — observability concern)

Where: `modules/core/provider_mode.py:7-10` (`PROVIDER_MODE_ENV = "GEULDOBI_PROVIDER_MODE"`) and `modules/core/models_config.py:51` (`FORCE_GOOGLE_MODEL_ENV = "GEULDOBI_FORCE_GOOGLE_MODEL"`).

What it does:
- `GEULDOBI_PROVIDER_MODE` (values: `gemini_direct`, `vertex_ai`, `ambient`) silently rewrites every Gemini model name in `models.yaml` payload at load time (`apply_provider_mode_to_models_payload`).
- `GEULDOBI_FORCE_GOOGLE_MODEL` pins every Gemini-family role to one model name across `agents`, `role_constants`, `sub_components`, `fallback_chain`.

Risk:
- Not a secret-handling issue. Listed because #66 ("standardize runtime config loading") implies traceability. These env vars mutate the in-memory config payload after disk read, so any audit trail that quotes `models.yaml` content must also capture `GEULDOBI_PROVIDER_MODE` and `GEULDOBI_FORCE_GOOGLE_MODEL`. Currently no `ConfigManager.build_config_authority_summary` field exposes these. Provenance gap, not a vulnerability.

### F10 — `ConfigManager.__init__` mkdirs `projects/` and `logs/` under cwd (P2 for #68)

Where: `config_manager.py:24-30`.

```
self.root = Path.cwd()
self.projects_dir = self.root / "projects"
self.projects_dir.mkdir(parents=True, exist_ok=True)
self.logs_dir = self.root / "logs"
self.logs_dir.mkdir(parents=True, exist_ok=True)
```

What it does:
- On every `ConfigManager` construction, materializes `projects/` and `logs/` directories under cwd.
- Ignores `GEULDOBI_WORKSPACE` and `GEULDOBI_PROJECTS_ROOT` from `runtime_paths.py`.

Risk for #68:
- Packaged EXE launched from `Program Files\...\` would attempt to mkdir under `Program Files\...` (likely permission-denied; or worse, written to a virtualized location depending on Windows UAC behavior).
- Packaged EXE launched from user desktop would scatter `projects/` and `logs/` at the user's cwd — violates "approved user config directory" intent.
- T05 owns the write-location remediation, but T02 records the trigger here because it sits in the runtime-config layer.

## Remediation Candidates

These are candidates for a later remediation phase, not patches to apply now. Order is rough priority; final scope decisions belong to the consolidated security roadmap.

1. **Single secret-load chokepoint (addresses F1, F2, F3).** Replace the three `load_dotenv(override=True)` sites in `main_a.py` with one explicit `_bootstrap_runtime_environment(project: str | None)` call invoked from `SovereignApp._init_core_runtime_state`. Take a `dict(os.environ)` snapshot before any overlay; on project rebind, restore-then-overlay rather than overlay-on-top.
2. **Replace cwd-relative reads with engine-root-anchored reads (addresses F4, F5, F8, F10).** Make `ConfigManager` accept (or import) `runtime_paths.resolve_engine_root(...)` instead of `Path.cwd()`. Have `_load_validation_settings` in `main_a.py` delegate to `ConfigManager.load_settings_json()` so there is a single reader.
3. **Unify `models.yaml` resolution (addresses F4).** Replace the inline `Path(__file__).parent.parent.parent / "config" / "models.yaml"` walk in `config_manager.py:_load_agents_from_yaml` with a call to `models_config.resolve_models_yaml_path()`. One env-aware resolver, one caller pattern.
4. **Decouple secret reload from runtime rebuild (addresses F2).** Split `_reload_project_environment` into `_reload_project_secrets` (env snapshot/restore/overlay only) and `_rebuild_runtime_clients` (StudioSystem / router / BaseAgent). Composability matters for testing and for future multi-project support.
5. **Surface runtime-mode env vars in `build_config_authority_summary` (addresses F9).** Add `GEULDOBI_PROVIDER_MODE`, `GEULDOBI_FORCE_GOOGLE_MODEL`, `GEULDOBI_ENGINE_ROOT`, `GEULDOBI_WORKSPACE`, `GEULDOBI_PROJECTS_ROOT` to the authority summary so any boot log captures the active runtime envelope.
6. **Document the auth surfaces (T03 boundary).** Whatever decision T03 reaches for #67, ensure `DEFAULT_PROVIDER_CONFIGS` in `llm_router.py` becomes the single registry of supported auth env names. Today it already is; the remediation is to keep it that way and add an explicit "secret material" tag on the dict shape.

## Dependencies On Other Terminals

- **T01 (root secret inventory):** F1 / F8 conclusions assume the cwd-discovered `.env` is the file T01 inventories at repo root. If T01 finds additional `.env` siblings (e.g., `.env.local`, `.env.production`), F1's risk picture broadens.
- **T03 (Vertex AI auth flow):** F7 only maps the registration surface. T03 must own the question of how `GOOGLE_APPLICATION_CREDENTIALS` and `geuldobi-vertex-key.json` should evolve under #67.
- **T04 (desktop config surfaces):** T04 must confirm whether Electron `main.js` injects any env into the spawned Python process. If so, that envelope is what F1's `override=True` overrides.
- **T05 (Windows settings paths):** Owns the write-location remediation that F8 / F10 trigger on. T02 records that the *read-side* anchor is missing; T05 decides what the *write-side* anchor should be (likely `%APPDATA%/글도비/`).
- **T06 (release packaging):** Must verify whether `build/backend_entry.py` actually sets `GEULDOBI_ENGINE_ROOT` in the packaged EXE. F4 / F8 risk magnitude depends on the answer.
- **T07 (dev/test separation):** All `load_dotenv` sites in `tools/`, `tests/`, `scripts/`, `smoke_sc.py`, `visual_lab/`, `tools2/` were observed but are out of scope here. T07 owns their classification (production-adjacent vs. throwaway).
- **T09 (CI / pre-commit guardrails):** F1's "every importer mutates env" surface is best caught with a lint/CI rule. T09 should consider whether to flag `load_dotenv(override=True)` outside an approved chokepoint.

## Open Questions

1. Does `build/backend_entry.py` set `GEULDOBI_ENGINE_ROOT` in packaged mode? (T06 should answer; T02 read the assertion in `models_config.py:115-119` docstring but did not inspect `backend_entry.py`.)
2. Are there callers that rely on the `_reload_project_environment` side effect of rebuilding `StudioSystem` / `LLMRouter`? Splitting per remediation #4 needs that map.
3. Does any project ship a non-empty `projects/<name>/config/settings.json` today? If so, F5's "two readers with different fallback orders" has live divergence today and is P1 instead of P2.
4. Should `GOOGLE_APPLICATION_CREDENTIALS` continue to be a supported auth surface post-#67, or does T03's recommendation deprecate it in favor of pure env-var or workload-identity flows?
5. Does the desktop layer ever launch the Python backend with `cwd` set to anything other than the engine root? (T04.) If never, F8 risk drops materially. If sometimes, F8 is P1.

## Closure Recommendation

- **Do not close #66 on T02 evidence alone.** F1, F2, and F8 each block #66 closure independently. Remediation candidates 1 and 2 must land before #66 can be marked mitigated.
- **Do not close #68 on T02 evidence alone.** F8 and F10 directly contradict #68 intent. T05's write-location decision plus remediation candidate 2 are both prerequisites.
- T02 itself is closure-ready as a read-only investigation report: scope is bounded, evidence is recorded with paths and line numbers, no source/config edits were made, and no secret values appear in the report.
- Recommend the consolidated roadmap (`docs/2026-04-27/security-remediation-roadmap.md`, per dispatch §7) treat F1+F2 as a single chokepoint workstream, F4+F5+F8+F10 as a single anchor-policy workstream, and F9 as a documentation-only follow-up.

Estimated investigation confidence: 92%. Confidence is bounded by the open questions above (#1, #3, #5 in particular), all of which require evidence owned by other terminals.
