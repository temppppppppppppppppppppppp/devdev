<!-- [참고자료] -->
# Codebase Global ROL System Full Survey 3-Pass Audit

Date: 2026-03-14
Status: final
Canonical Path: `docs/2026-03-14/codebase-global-rol-system-full-survey-3pass-audit.md`
Evidence Artifacts:
- `docs/2026-03-14/codebase-global-rol-system-survey-inventory.json`
- `docs/2026-03-14/codebase-global-rol-system-survey-side-effects.json`
- `docs/2026-03-14/codebase-global-rol-system-survey-entrypoints.txt`
- `docs/2026-03-14/codebase-global-rol-system-survey-regression-surface.txt`
Side-Effect Coverage: covered
Confidence Target: 95%

## 1. Intent
- Perform a codebase-global system-track survey over the active live surfaces.
- Cover macro topology, micro hotspots, and side-effects in one bounded audit.
- Produce execution-ready follow-on documents for action-bearing areas without starting implementation.

## 2. Scope and Evidence Basis

### 2.1 Included Live Scope
- `main_a.py`
- `modules/`
- `scripts/`
- `tests/`
- `UI/`
- `geuldobi-desktop/`
- `config/`
- root-level live scripts: `smoke_sc.py`, `fix_costs.py`, `fix_costs2.py`, `RESET.py`, `main.js`

### 2.2 Excluded by Rule
- dependency or build surfaces: `node_modules/`, `dist/`, `build/`
- cache or generated state: `.git/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `.hypothesis/`
- binary or archive artifacts such as `.zip`, `.exe`, `.dll`, `.asar`, `.png`, `.ttf`

### 2.3 Baseline Counts
- active surveyed files after exclusions: `720`
- dominant roots: `tests 346`, `modules 265`, `config 55`, `scripts 25`, `geuldobi-desktop 15`, `UI 8`
- dominant extensions: `.py 581`, `.json 49`, `.yaml 24`, `.js 13`

## 3. Pass 1. Inventory Baseline

### 3.1 Active Entry Surfaces
- engine bootstrap and runtime shell: `main_a.py`
- backend control plane: `modules/api/bridge_server.py`
- subprocess runner boundary: `modules/api/process_runner.py`
- desktop authoritative entry: `geuldobi-desktop/src/main.js`
- desktop compatibility shim: `geuldobi-desktop/main.js`
- root debug shadow entry: `main.js`
- smoke and canary helpers: `scripts/run_stage2_smoke.py`, `scripts/run_stage3_smoke.py`, `scripts/run_stage4_smoke.py`, `scripts/run_stage4_canary.py`, `scripts/run_stage34_canary.py`, `smoke_sc.py`

### 3.2 Highest-Code Hotspots
- `main_a.py`: `4222` LOC
- `modules/core/stage4_interview_round.py`: `4847` LOC
- `modules/core/db_manager.py`: `3504` LOC
- `modules/core/stage4_context_builder.py`: `2691` LOC
- `modules/api/bridge_server.py`: `1764` LOC
- `modules/api/process_runner.py`: `794` LOC
- `modules/core/stage0/__init__.py`: `811` LOC
- `geuldobi-desktop/src/main.js`: `898` LOC

### 3.3 Side-Effect Density Snapshot
- `print(...)`: `671`
- `ui.log(...)`: `768`
- `logging.*(...)`: `1784`
- `console.print(...)`: `47`
- `input(...)`: `70`
- write sinks: `open(..., 'a'/'w'/'x') 47`, `write_text(...) 175`, `json.dump(...) 25`
- persistence markers: `sqlite/session logger/audit` related hits `420`
- subprocess markers: `13`
- network markers: `52`

## 4. Pass 2. Tranche Findings

### Tranche A. Macro Topology
- The runtime is centered on one large Python bootstrap shell in `main_a.py` that composes services, guards, agents, Stage 0 to Stage 4 orchestration, shutdown, metrics, and persistence.
- The desktop stack is a separate control plane made of Electron main/preload/renderer plus a FastAPI backend and a subprocess runner.
- The repository also carries a large regression and operator-governance surface, not just product code.

### Tranche B. Runtime Core
- `main_a.py` is still the dominant runtime authority and contains bootstrap I/O normalization, faulthandler setup, env loading, project selection, DB wiring, session logging, audit wiring, optional module bootstrap, shutdown sequencing, and residual operator-visible prints.
- Stage runtime complexity is concentrated in `modules/core/stage2_*`, `stage3_orchestrator.py`, `stage4_orchestrator.py`, `stage4_context_builder.py`, and `stage4_interview_round.py`.
- Boot, runtime, and shutdown concerns are not yet cleanly separated.

### Tranche C. Domain and Agent Layer
- The agent layer is deep and heavy: `state_tracker_npc.py`, `four_phase_arc_generator.py`, `base_agent.py`, `chief_writer.py`, `analyst.py`, `director_ensemble.py`, and `director_auditor.py` are all large hotspots.
- Operator-facing traces still emerge from deep agent modules, especially through `print`, `logging`, and mixed runtime diagnostics.
- The layer is heavily coupled to stage orchestration and runtime state transport.

### Tranche D. Persistence and Observability
- `modules/core/db_manager.py` is a large SQLite authority with integrity recovery, WAL setup, migrations, anchors, blueprints, logs, and state tables.
- `modules/core/session_logger.py` persists only selected JSONL categories (`llm_io`, `decisions`, `state_changes`) and is not yet the complete operator-event sink.
- `modules/core/logger.py` is file-oriented and removes console `StreamHandler` usage from the root logger.
- `modules/core/studio_visualizer.py::log()` is the current dual sink for human-visible runtime lines: Rich console output plus `logging.getLogger("UI").info(...)`.

### Tranche E. Operator Surface and App Shell
- Stage 0 remains highly interactive and CLI-shaped. `modules/core/stage0/__init__.py` alone contains `100` raw `print(...)` calls and `14` `input(...)` calls.
- `modules/core/services/ui_service.py` still uses direct `print` and `input` for selection flows even though other runtime paths prefer `ui.log` and Rich table output.
- `geuldobi-desktop/src/main.js` owns the authoritative desktop runtime with many IPC handlers and backend spawn logic.
- `geuldobi-desktop/src/preload.js` exposes the bridge surface; `geuldobi-desktop/src/splash/splash.js` still directly polls `/status`.

### Tranche F. Quality and Regression Surface
- The regression surface is large: `308` Python tests, `4` JavaScript tests, plus e2e/integration/chaos/property partitions and fixture-heavy stage projects.
- Canary and smoke helpers are live mutation tools, not read-only checks. `scripts/run_stage4_canary.py` and `scripts/run_stage34_canary.py` boot `SovereignApp`, patch input, write JSON summaries, and mutate project logs.
- The test tree mixes contract tests, live mutation helpers, fixture projects, and historical result artifacts.

### Tranche G. Scripts and Utility Surface
- The script surface is split between product-facing smoke/canary helpers, governance automation (`ops_validator.py`, `sync_temp_queue_state.py`, roadmap/evidence generators), and large one-off builders.
- Some utilities are clearly standalone, but some scripts exercise runtime code paths directly and should be treated as operational surfaces.

### Tranche H. Cross-Cutting Contracts and Config
- Prompt and config surfaces are material: `config/prompts/` has `23` YAML prompt files, led by a large `director.yaml`.
- Desktop/API/event contracts live in `docs/implementation/desktop-runtime-contract-v1.json`, `desktop-ipc-surface-contract-v1.json`, `api-contract-v1.yaml`, and `event-schema-v1.json`.
- The repository still carries large text and seed assets that affect runtime behavior, especially `config/style_references/` and `modules/core/laws/seeds/*.json`.

## 5. Cross-Cutting Side-Effect Map
- File writes and artifact generation:
  - Stage 0 writes work-guard YAML and generated artifacts.
  - canary scripts write summary JSON into project `logs/`.
  - desktop main writes `electron-main.log` and settings JSON.
- DB writes and transaction boundaries:
  - `DBManager` owns direct SQLite writes and migrations.
  - runtime boot and shutdown in `main_a.py` still explicitly commit and close persistence surfaces.
- JSONL and audit sinks:
  - `SessionLogger` and `AuditService` are partial durable sinks.
  - backend control-plane provenance writes JSONL via `append_jsonl_record`.
- Console and UI output:
  - runtime output remains split across `print`, `ui.log`, `console.print`, and file logging.
- Subprocess and network:
  - Electron main spawns the backend.
  - `ProcessRunner` spawns `main_a.py`.
  - splash and main renderer consume `/status` and `/events`.
- Config and bootstrap mutation:
  - Stage 0 and project config surfaces mutate per-project YAML and config assets.

## 6. Risk Register
- Runtime authority remains overly centralized in `main_a.py`, which increases regression blast radius.
- Operator-visible output is not yet governed by one durable contract; console visibility and durable logging are still separate in practice.
- Stage 0 is still a CLI-era surface embedded in a repository that also has desktop and bridge surfaces.
- Desktop authority is split correctly between `geuldobi-desktop/main.js` and `geuldobi-desktop/src/main.js`, but a root `main.js` debug shadow still exists and can confuse ownership if not explicitly fenced.
- Regression surfaces are broad but not clearly tiered between read-only contract checks and mutation-heavy canary runs.

## 7. Pass 3. Action-Bearing Area Map

| Area | Classification | Governing Execution Doc | Notes |
| --- | --- | --- | --- |
| Operator-visible runtime event durability | action-bearing | `docs/2026-03-14/residual-print-ui-log-db-full-survey-3pass-execution-ssot.md` | existing canonical doc; keep in queue |
| Runtime bootstrap and orchestration hardening | action-bearing | `docs/2026-03-14/runtime-bootstrap-orchestration-hardening-execution-ssot.md` | new |
| Stage 0 operator surface contract hardening | action-bearing | `docs/2026-03-14/stage0-operator-surface-contract-hardening-execution-ssot.md` | new |
| Desktop control-plane surface hardening | action-bearing | `docs/2026-03-14/desktop-control-plane-surface-hardening-execution-ssot.md` | new |
| Regression and canary surface rationalization | action-bearing | `docs/2026-03-14/regression-canary-surface-rationalization-execution-ssot.md` | new |
| Domain-agent prompt and seed assets | no-execution-doc-required | governed by runtime/bootstrap and observability docs | defer unless contract drift becomes concrete |
| Static UI art and archive assets | no-execution-doc-required | not primary runtime code | keep excluded from implementation planning |

## 8. Completion Note
- All eight global survey tranches were covered.
- Included and excluded scope were recorded.
- Side-effects were explicitly surveyed.
- Action-bearing areas were mapped to execution docs or marked as not requiring one.
- Because multiple execution SSOTs are active or newly created, an aggregate roadmap is required and is produced with this survey bundle.
