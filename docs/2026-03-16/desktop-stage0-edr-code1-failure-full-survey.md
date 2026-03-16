Date: 2026-03-16
Status: final
Canonical Path: docs/2026-03-16/desktop-stage0-edr-code1-failure-full-survey.md
Topic: desktop-stage0-edr-code1-failure
Source Survey Docs: none
Evidence Artifacts:
- docs/2026-03-16/desktop-stage0-edr-code1-failure-evidence.txt
Side-Effect Coverage:
- file writes
- DB writes
- JSONL/log/audit sinks
- console/UI output
- rollback/retry/recovery
- cache/global state
- config/env/bootstrap fallback

Commit State:
- Baseline Commit: 5a0177666e6877070d726d983d3c3e1d03e812d2
- Baseline Dirty Summary: dirty: 1 tracked, 1 untracked; hotspots: projects/0_260316/project_data.db, projects/0_260316/0_temp.txt
- Resume Commit: same-as-baseline
- Resume Drift Summary: none

# Findings

## High — `edr` failure never reached durable project bootstrap

The strongest live evidence is that `C:\Users\wjjo\Documents\글도비\projects\edr` exists only as an empty directory created by the desktop main process, while none of the runtime artifacts guaranteed by `ProjectContext` exist.

Concrete evidence:
- `C:\Users\wjjo\Documents\글도비\projects\edr` exists.
- `C:\Users\wjjo\Documents\글도비\projects\edr\project_data.db` is absent.
- `C:\Users\wjjo\Documents\글도비\projects\edr\logs\` is absent.
- `C:\Users\wjjo\Documents\글도비\projects\edr\config\`, `drafts\`, `memory\`, `plans\` are absent.
- By contrast, `C:\Users\wjjo\Documents\글도비\projects\test` contains all of those artifacts plus session logs and metrics.

Code path evidence:
- `geuldobi-desktop/src/main.js` project creation IPC only performs `mkdirSync` for the project root.
- `main_a.py` calls `_bind_selected_project()` before any Stage 0 runtime work.
- `modules/core/system.py` `boot_v20_project()` immediately instantiates `ProjectContext`.
- `modules/core/project_manager.py` `ProjectContext.__init__()` immediately creates `config/`, `drafts/`, `memory/`, `plans/`, and `project_data.db`.

Assessment:
- The packaged `edr` failure occurred before `ProjectContext` durable side effects landed.
- The first failing phase is therefore not Stage 0 inner runtime bootstrap.
- The failure boundary is earlier: between project selection handoff and project runtime binding, most narrowly in the `_select_project()` -> `_bind_selected_project()` -> `boot_v20_project()` bootstrap corridor.

## High — pre-bind failures are poorly observable in the current desktop runtime path

The packaged failure produced a `/run` accepted record and a renderer-visible `code: 1`, but no durable traceback in either the `edr` project tree or the workspace root logs.

Concrete evidence:
- `electron-main.log` shows packaged `/run` acceptance at `2026-03-16T04:07:52Z`.
- `control-plane-provenance.jsonl` records run_id `99ae02c3-8e5a-4e0f-bc76-9733521d5988`.
- `C:\Users\wjjo\Documents\글도비\projects\edr\logs\` does not exist.
- `C:\Users\wjjo\Documents\글도비\logs\error.log` does not exist.

Code path evidence:
- `main_a.py` only retargets `StudioLogger` and `SessionLogger` after `current_project` is bound.
- `_run_main_process()` has a traceback sink, but only for exceptions after boot reaches that method.
- `if __name__ == "__main__": SovereignApp().boot()` has no outer persistence wrapper.

Assessment:
- A failure that occurs before or during `_bind_selected_project()` can escape with only process return code and ephemeral stderr.
- This explains why the packaged desktop UI surfaced only `code: 1` and why the workspace has no durable traceback artifact for `edr`.

## Medium — the desktop run contract still depends on numeric project selection for engine boot

The renderer sends both `project_name` and `project_index`, but the runner’s Mode B stdin sequence uses numeric `project_index` to drive engine project selection.

Concrete evidence:
- `geuldobi-desktop/src/index.html` `_collectInputs()` includes both `inputs.project_index` and `inputs.project_name`.
- `modules/api/process_runner.py` `_build_stdin_sequence()` writes the boot sequence using `project_index`.
- `modules/api/process_runner.py` `_resolve_requested_project_name()` is used only for metadata helpers such as genre-alignment checks, not as the direct stdin selection token.

Assessment:
- This is a structural regression surface because a stale or drifted index can select the wrong project even when `project_name` is correct.
- For the specific `edr` failure, current evidence suggests the second packaged attempt had already switched the renderer to `project=edr` before `/run`, so index drift is not proven as the immediate cause.
- It remains a likely remediation substrate because the current contract makes pre-bind failures harder to diagnose and easier to misroute.

## Medium — the second packaged failure is the `edr`-specific one; the first accepted run appears earlier in the session

The evidence shows two packaged `/run` acceptances on 2026-03-16. Only the later one has an explicit `project=edr` dashboard selection immediately preceding it.

Concrete evidence:
- `control-plane-provenance.jsonl` records:
  - `343432eb-8348-407e-898b-d76b6f33166e` at `2026-03-16T04:06:47+00:00`
  - `99ae02c3-8e5a-4e0f-bc76-9733521d5988` at `2026-03-16T04:07:52+00:00`
- `electron-main.log` immediately before the later run shows:
  - `GET /quality/dashboard?project=test`
  - `GET /quality/dashboard?project=edr`
  - then `POST /run`

Assessment:
- The later run is the strongest `edr`-scoped failure instance.
- The earlier accepted run likely belongs to a prior attempt before explicit `edr` selection and should not be treated as primary `edr` evidence without extra confirmation.

# Pass 1 Inventory

## Runtime surfaces inspected
- Installed packaged desktop runtime:
  - `C:\Users\wjjo\AppData\Local\Programs\Geuldobi\Geuldobi.exe`
  - `%LOCALAPPDATA%\Geuldobi\electron-main.log`
- Workspace runtime evidence:
  - `C:\Users\wjjo\Documents\글도비\logs\control-plane-provenance.jsonl`
  - `C:\Users\wjjo\Documents\글도비\projects\edr`
  - `C:\Users\wjjo\Documents\글도비\projects\test`
  - `C:\Users\wjjo\Documents\글도비\bible`
  - `C:\Users\wjjo\Documents\글도비\treatments`
- Code paths:
  - `geuldobi-desktop/src/index.html`
  - `geuldobi-desktop/src/main.js`
  - `modules/api/bridge_server.py`
  - `modules/api/process_runner.py`
  - `main_a.py`
  - `modules/core/system.py`
  - `modules/core/project_manager.py`
  - `modules/core/logger.py`
  - `modules/core/session_logger.py`

## Durable artifact inventory
- `projects/edr`
  - present: project root directory only
  - absent: `project_data.db`, `logs/`, `config/`, `drafts/`, `memory/`, `plans/`
- `projects/test`
  - present: `project_data.db`, `config/`, `drafts/`, `memory/`, `plans/`, `logs/`, metrics, session JSONL, Stage 0 success logs

# Pass 2 Semantic Classification

## Desktop renderer/main
- New project creation is a shallow filesystem action.
- Project selection state is maintained in `projectConfig.project` and `projectConfig.projectIndex`.
- Run payload generation is explicit and includes both name and index.

## Bridge / runner
- `/run` accepts the request and persists provenance before the engine exits.
- Runner diagnostics are only useful if stdout/stderr or prompt metadata survive long enough to be captured.
- Current Mode B contract still routes engine project selection through numeric stdin.

## Engine bootstrap
- `boot()` is linear and front-loads project binding before Stage 0 runtime work.
- A failure before `ProjectContext` binding yields no project-local DB or logs.
- A failure before `_run_main_process()` bypasses the richer exception persistence path.

## Stage 0 inner runtime
- The comparison project `test` proves that once boot reaches Stage 0 runtime, durable session logs include `Stage 0`, Bible selection, Treatment selection, and completion markers.
- None of those artifacts exist for `edr`.
- Therefore the `edr` packaged failure did not reach inner Stage 0 interaction.

# Side-Effect Sweep

## File writes
- Confirmed durable write for `edr`: empty project root directory created by desktop main process.
- Missing durable writes for `edr`: all project bootstrap subdirs, DB, logs, metrics, session files.

## DB writes
- No `project_data.db` for `edr`.
- Therefore no durable anchor writes, no genre info persistence, and no UI-event DB persistence occurred for `edr`.

## JSONL / log / audit sinks
- Provenance sink wrote the packaged `/run` acceptance.
- No `edr` session log, no `ui_events.jsonl`, no metrics JSON, no project-local `error.log`.
- No workspace-root `logs/error.log` was present either.

## Console / UI output
- Renderer showed run acceptance then `실행 실패 (code: 1)`.
- No engine-side durable UI or session transcript for `edr` exists.

## Rollback / retry / recovery
- Two packaged `/run` acceptances were recorded in the broader session.
- The later attempt is the `edr`-correlated one.
- No orphaned durable project artifacts were left except the empty project root.

## Cache / global / bootstrap
- Project list ordering is lexical in both renderer/main and engine.
- Saved project and selected project can diverge from numeric boot selection if the index becomes stale.
- Project-local env reload happens before `boot_v20_project()`, but for `edr` there was no `.env` to load.

# Comparison: `edr` vs `test`

## `edr`
- Empty root directory only.
- No DB.
- No logs.
- No evidence of `ProjectContext` bootstrap.
- No evidence of Stage 0 menu entry.

## `test`
- Fully bootstrapped project structure and DB.
- Durable session logs.
- Explicit Stage 0 menu and selection prompts captured.
- Successful Stage 0 completion path already proven by prior ProcessRunner evidence.

## Structural divergence point
- The first divergence is before `ProjectContext` durable bootstrap.
- That places the earliest failure phase in the project selection handoff / project bind corridor, not in Stage 0 runtime bootstrap.

# Open Questions / Assumptions

## Open questions
- The exact thrown exception text for the `edr` packaged run is still missing.
- It is not yet proven whether the throw happened:
  - inside `_select_project()` after stdin handoff,
  - in `_reload_project_environment()`,
  - or in the first call into `boot_v20_project()`.

## Assumptions
- The later accepted run (`99ae02c3-8e5a-4e0f-bc76-9733521d5988`) is the authoritative `edr` run because `electron-main.log` shows `project=edr` immediately before it.
- `projects/test` remains a valid comparison baseline for a successful Stage 0 path.

# Execution-Doc Readiness

Current remediation substrate is identifiable but not yet 95% decision-safe.

Likely remediation substrate:
- desktop project create/select/run contract
- Mode B project selection contract between renderer and runner
- pre-bind exception capture and durable stderr persistence

Likely regression surface:
- new-project runs from packaged desktop
- project selection/index drift
- project-local log retarget timing
- pre-Stage-0 bootstrap visibility

Execution SSOT is intentionally deferred in this turn because the exact pre-bind exception site is still unresolved.
