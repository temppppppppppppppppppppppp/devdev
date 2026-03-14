# Residual Print to UI Log + DB Persistence Full Survey 3-Pass Execution SSOT

Date: 2026-03-14
Status: in progress
Canonical Path: `docs/2026-03-14/residual-print-ui-log-db-full-survey-3pass-execution-ssot.md`
Temp Mirror Path: `docs/temp/residual-print-ui-log-db-full-survey-3pass-execution-ssot.md`
Source Survey Docs:
- `docs/2026-03-14/codebase-global-rol-deep-global-survey.md`
- `docs/2026-03-14/codebase-global-rol-system-full-survey-3pass-audit.md`
Evidence Artifacts:
- `00_test_print_ast.txt`
- `00_test_print.txt`
- `docs/2026-03-14/codebase-global-rol-deep-survey-side-effects.json`
Side-Effect Coverage: covered
Confidence Target: 95%
Live Workspace Revalidation: 2026-03-14 PASS
Revalidated Confidence: 96%
Primary References:
- `00_test_print_ast.txt`
- `00_test_print.txt`
- `main_a.py`
- `modules/core/logger.py`
- `modules/core/studio_visualizer.py`
- `modules/core/session_logger.py`
- `modules/core/db_manager.py`
- `modules/core/services/audit_service.py`

## 1. Intent
- Replace residual operator-visible runtime `print(...)` usage with a `ui.log`-centered surface.
- Persist the same operator-visible events to JSONL and DB so later LLM analysis can reconstruct what the operator saw.
- Do not start with blind search/replace. This order uses a full survey, semantic classification, and a 3-pass audit baseline.

## 2. Baseline Facts
- Bare `logging.*` is not the current operator console surface. `modules/core/logger.py` keeps file handlers and removes console `StreamHandler`.
- `modules/core/studio_visualizer.py::StudioVisualizer.log()` is the current dual sink: it writes to `console.print(...)` and `logging.getLogger("UI").info(...)`.
- `modules/core/session_logger.py` currently persists only `llm_io`, `decisions`, and `state_changes`.
- `modules/core/db_manager.py` already persists durable analysis sinks such as `llm_calls`, `director_selections`, and `stage_attempts`.
- Therefore the correct migration target is not bare `logging.*`. The correct target is an operator-visible `ui.log` surface backed by durable `ui_events`.

## 3. Pass 1. Full Survey Inventory

### 3.1 AST Baseline
The authoritative baseline is `00_test_print_ast.txt`, not raw grep hits.

- Total actual `print(...)` calls across `main_a.py`, `modules/`, `scripts/`, and `fix_costs.py`: `370`
- Total non-call `print` references: `1`
- Runtime-relevant subtotal in `main_a.py` + `modules/`: `284`
- Scripts/utilities subtotal in `scripts/` + `fix_costs.py`: `86`

### 3.2 Bucket Totals

| Bucket | Print calls |
| --- | ---: |
| `modules/core/stage0` | 117 |
| `modules/domain/agents` | 90 |
| `scripts/` | 78 |
| `main_a.py` | 44 |
| `modules/core` other | 28 |
| `fix_costs.py` | 8 |
| `modules/core/services` | 5 |

### 3.3 Top Files

| File | Print calls | Notes |
| --- | ---: | --- |
| `modules/core/stage0/__init__.py` | 100 | interactive Stage 0 CLI surface |
| `main_a.py` | 44 | bootstrap, shutdown, control-plane summaries |
| `modules/domain/agents/director_ensemble.py` | 29 | director comparison frames |
| `modules/core/stage4_interview_round.py` | 20 | mixed `ui.log` + residual `print` |
| `scripts/validate_manual_sweep.py` | 15 | script scope |
| `modules/domain/agents/three_phase_blueprint_generator.py` | 12 | deep agent console traces |
| `modules/domain/agents/base_agent.py` | 11 | API retry/error live traces |
| `modules/domain/agents/director_auditor.py` | 10 | Stage 4 audit frames |
| `modules/core/stage0/style_extractor.py` | 9 | Stage 0 progress surface |
| `fix_costs.py` | 8 | utility script scope |

### 3.4 Key Residual Patterns
- `main_a.py` contains early bootstrap prints, shutdown summaries, and persistence summaries.
- `modules/core/stage4_interview_round.py` already emits `self.ctx.ui.log(...)` beside residual `print(...)`, so it is a direct conversion target.
- `modules/domain/agents/director_ensemble.py`, `base_agent.py`, and `director_auditor.py` emit operator-facing frames from deep runtime code that does not own `self.ui`.
- `modules/core/stage0/__init__.py` is a large interactive menu flow built around `print(...)` + `input(...)`, so it cannot be migrated safely by simple line replacement.
- `modules/core/vec_memory.py` and `modules/core/genre_hud_manager.py` still contain raw `print` fallbacks.

## 4. Pass 2. Semantic Classification

### Class A. Direct Runtime `ui.log` Conversions
Files in this class already have direct access to `self.ui` or `ctx.ui`.

- `main_a.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/services/ui_service.py`

Expected action:
- Replace residual `print(...)` with `ui.log(...)` or a richer UI event helper.
- Preserve existing operator message wording unless normalization is explicitly required.
- Attach context fields where available: `stage`, `ep_num`, `round_num`, `attempt_key`, `component`.

### Class B. Callback-Injection Runtime Modules
Files in this class produce operator-visible traces but should not depend directly on the UI object.

- `modules/domain/agents/director_ensemble.py`
- `modules/domain/agents/base_agent.py`
- `modules/domain/agents/director_auditor.py`
- `modules/domain/agents/three_phase_blueprint_generator.py`
- `modules/domain/agents/arc_ensemble.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/chief_writer.py`
- `modules/domain/agents/analyst.py`
- `modules/domain/agents/unified_arc_validator.py`

Expected action:
- Introduce an injected operator event callback instead of importing UI surfaces directly.
- Keep `logging.*` and existing structured sinks where they already exist.
- Route human-facing frames through a shared bridge so the same event is visible on console and persisted.

### Class C. Interactive Stage 0 Surfaces
This class includes menu screens, prompts, selection flows, and progress helpers.

- `modules/core/stage0/__init__.py`
- `modules/core/stage0/style_extractor.py`
- `modules/core/stage0/spinner.py`
- `modules/core/services/ui_service.py`

Expected action:
- Do not convert these to blind `ui.log(...)` line dumps.
- Introduce typed helpers such as menu, prompt, selection, and summary events.
- Persist prompt text and operator selections with redaction guardrails where secrets may appear.

### Class D. Bootstrap and Fallback Exceptions
These cases exist before the full app context or UI context is available.

- `main_a.py` early faulthandler and import-error prints
- `modules/core/vec_memory.py` fallback lambda: `ui_log or print`
- `modules/core/genre_hud_manager.py` fallback logger assignment

Expected action:
- Replace raw fallback prints with a bootstrap-safe operator sink.
- Buffer pre-project events and flush them into project-scoped persistence once the project and session are bound.
- Keep a very small allowlist only where a true pre-runtime hard failure makes UI wiring impossible.

### Class E. Standalone Scripts and Utilities
These are not the first runtime remediation tranche.

- `scripts/`
- `fix_costs.py`

Expected action:
- Keep separate policy from the app runtime.
- Optional later alignment is acceptable, but script output should not block runtime migration.

## 5. Pass 3. Realization Architecture

### 5.1 Design Principle
One operator-visible event should fan out to multiple sinks.

Required sinks:
1. Console-visible surface
2. Session JSONL persistence
3. Project DB persistence
4. Existing text log file mirror

The operator-visible source of truth should be `ui.log` and the bridge behind it, not raw `print(...)`.

### 5.2 Proposed Runtime Surface
Retain `StudioVisualizer.log(text)` as the simple call site, but back it with a structured bridge.

Recommended additions:
- `StudioVisualizer.log(text, **context)` remains backward compatible.
- Add a bridge object such as `UIEventBridge` or `OperatorEventSink`.
- The bridge writes to:
  - `console.print(...)`
  - `logging.getLogger("UI").info(...)`
  - `SessionLogger.log_ui_event(...)`
  - `DBManager.save_ui_event(...)`

Deep runtime modules should receive the bridge as a callback, for example:
- `ui_event(...)`
- `ui_log(...)`
- `operator_sink(...)`

The name is flexible. The contract is not: one call must produce console visibility plus durable persistence.

### 5.3 Proposed Session JSONL Sink
Extend `SessionLogger` with a new category and API.

Recommended category:
- `ui_events`

Recommended method:
- `log_ui_event(...)`

Recommended JSONL location:
- `logs/session/ui_events.jsonl`

Recommended minimum fields:
- `ts`
- `session_id`
- `seq`
- `level`
- `component`
- `stage`
- `ep_num`
- `arc_num`
- `round_num`
- `attempt_key`
- `event_kind`
- `render_format`
- `message`
- `visible`
- `meta`

Rationale:
- `decisions.jsonl` captures decision semantics.
- `ui_events.jsonl` should capture what the operator actually saw.
- Both are needed for later LLM postmortem analysis.

### 5.4 Proposed DB Sink
Add a new durable table to `DBManager`.

Recommended table:
- `ui_events`

Recommended minimum columns:
- `id INTEGER PRIMARY KEY AUTOINCREMENT`
- `session_id TEXT`
- `ts TEXT NOT NULL`
- `seq INTEGER`
- `stage INTEGER`
- `ep_num INTEGER`
- `arc_num INTEGER`
- `round_num INTEGER`
- `attempt_key TEXT`
- `component TEXT NOT NULL`
- `event_kind TEXT NOT NULL`
- `level TEXT NOT NULL`
- `render_format TEXT NOT NULL DEFAULT 'text'`
- `message TEXT NOT NULL`
- `visible INTEGER NOT NULL DEFAULT 1`
- `selection_value TEXT`
- `prompt_id TEXT`
- `artifact_path TEXT`
- `meta_json TEXT`

Recommended indexes:
- `idx_ui_events_session`
- `idx_ui_events_stage_ep`
- `idx_ui_events_attempt_key`
- `idx_ui_events_component`
- `idx_ui_events_ts`

Recommended API:
- `save_ui_event(...)`

Rationale:
- `stage_attempts` and `director_selections` already model analysis-facing facts.
- `ui_events` adds the operator-visible timeline needed for reconstruction and later LLM reasoning.

### 5.5 Joinability Contract for LLM Analysis
Later analysis should be able to answer questions such as:
- What did the operator see before a Stage 4 reject?
- Which director frame was shown before a specific `attempt_key`?
- Which warnings were visible before a cost or drift summary?

Canonical join fields:
- `session_id`
- `stage`
- `ep_num`
- `round_num`
- `attempt_key`
- `component`

Expected joins:
- `ui_events` <-> `stage_attempts`
- `ui_events` <-> `director_selections`
- `ui_events` <-> `llm_calls`
- `ui_events` <-> `decisions.jsonl`
- `ui_events` <-> `runtime_audit_summary.json`

### 5.6 Bootstrap Buffer
`main_a.py` contains prints before the full project and session context is ready.

Required solution:
- Add a bootstrap operator-event buffer.
- Capture early messages before `current_project` and session log dir are bound.
- Flush buffered events into `ui_events.jsonl` and DB when the session becomes available.

This prevents a false exception rule where bootstrap prints remain permanent.

### 5.7 Stage 0 Interactive Design
Stage 0 is not just a logging problem. It is an operator interaction problem.

Required helpers:
- `ui.menu(...)`
- `ui.prompt(...)`
- `ui.selection(...)`
- `ui.summary(...)`

Persistence requirements:
- Persist the menu title and visible options.
- Persist the prompt text.
- Persist the selected value or normalized answer where safe.
- Add redaction rules for secrets and environment values.

This is the only way to make Stage 0 later analyzable by an LLM without reducing it to noisy plain text.

### 5.8 Audit and Proof Digest Integration
`AuditService` should surface whether operator-visible evidence is actually durable.

Recommended proof digest additions:
- `ui_events_jsonl_exists`
- `ui_events_db_available`
- `ui_events_count`
- `ui_event_coverage_status`

`runtime_audit_summary.json` should eventually confirm that operator-visible events are persisted, not only printed.

## 6. Recommended Execution Tranches

### Tranche 1. Persistence Substrate
Target files:
- `modules/core/session_logger.py`
- `modules/core/db_manager.py`
- `modules/core/studio_visualizer.py`
- `main_a.py`
- `modules/core/services/audit_service.py`

Deliverables:
- `ui_events.jsonl`
- `ui_events` DB table
- bootstrap buffer
- bridge wiring from app startup to project/session binding

Implementation note:
- 2026-03-14 current workspace now includes `SessionLogger.log_ui_event(...)`, `DBManager.save_ui_event(...)`, `StudioVisualizer` operator-event sink wiring, `main_a.py` bootstrap buffering, and `AuditService` proof-digest visibility for `ui_events`.
- Remaining work for this execution SSOT is Tranche 2+ runtime conversion and allowlist cleanup of residual `print(...)` call sites.

### Tranche 2. Direct Runtime Conversion
Target files:
- `main_a.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/services/ui_service.py`

Deliverables:
- replace residual direct runtime `print(...)`
- preserve console visibility
- persist equivalent operator events

Implementation note:
- 2026-03-14 current workspace now converts direct runtime progress/result frames in `modules/core/stage3_orchestrator.py`, `modules/core/stage4_orchestrator.py`, and `modules/core/stage4_interview_round.py` into `ui.log(...)` with operator-event metadata.
- `main_a.py` shutdown persistence and advisory summaries now route through a `_shutdown_log(...)` helper backed by `ui.log(...)`, while threaded metrics-report prints remain intentionally excluded from this tranche because the metrics worker currently emits from a separate thread.
- Remaining work in this tranche is now the explicit allowlist and the interactive/menu-heavy surfaces in `modules/core/services/ui_service.py` plus the remaining bootstrap/menu prints in `main_a.py`.

### Tranche 3. Domain-Agent Callback Rollout
Target files:
- `modules/domain/agents/director_ensemble.py`
- `modules/domain/agents/base_agent.py`
- `modules/domain/agents/director_auditor.py`
- related ensemble/agent files with human-facing frames

Deliverables:
- shared operator callback contract
- no direct UI dependency in deep runtime code
- persisted director and agent frames

### Tranche 4. Stage 0 Interactive Migration
Target files:
- `modules/core/stage0/__init__.py`
- `modules/core/stage0/style_extractor.py`
- `modules/core/stage0/spinner.py`
- `modules/core/services/ui_service.py`

Deliverables:
- typed menu/prompt/selection helpers
- persisted operator interaction trail
- no raw Stage 0 `print(...)` outside explicit demo blocks

### Tranche 5. Policy and Guardrails
Target files:
- AST guard test or lint script
- focused tests around new persistence sinks

Deliverables:
- runtime print allowlist
- regression guard against new raw prints in target runtime paths

## 7. Acceptance Criteria
- `main_a.py` + `modules/` contain no unallowlisted runtime `print(...)` calls after migration.
- `logs/session/ui_events.jsonl` exists for live project runs.
- `project_data.db` contains `ui_events` rows for the same runs.
- `StudioVisualizer.log(...)` remains console-visible while also becoming durable.
- Stage 4 operator-visible events can be joined to `stage_attempts`, `director_selections`, and decision logs by `session_id` and `attempt_key`.
- `runtime_audit_summary.json` exposes UI-event persistence status.
- Stage 0 prompts and selections become reconstructable without relying on raw terminal capture.

## 8. Verification Plan
- Re-run the AST inventory and compare against `00_test_print_ast.txt`.
- Add focused tests for `SessionLogger.log_ui_event(...)`.
- Add focused tests for `DBManager.save_ui_event(...)`.
- Add bridge tests for `StudioVisualizer.log(...)`.
- Add migration regressions for Stage 3 and Stage 4 operator-visible flows.
- Add a runtime print guard test for target runtime paths.

## 9. Non-Goals and Guardrails
- Do not treat bare `logging.*` as a substitute for operator-visible output.
- Do not attempt byte-perfect raw terminal tee capture as the first implementation substrate.
- Do not convert every `logging.debug(...)` into `ui.log(...)`.
- Do not backfill historical projects in this tranche.
- Do not let script-scoped `print(...)` block the runtime migration.
- Do not persist secret input values without explicit redaction rules.

## 9A. Current-State Revalidation
- Revalidated against live workspace changes in `main_a.py`, `modules/core/logger.py`, `modules/core/session_logger.py`, `modules/core/db_manager.py`, `modules/core/services/audit_service.py`, `modules/api/bridge_server.py`, and `modules/api/process_runner.py`.
- The required substrate is now present in live code: `SessionLogger.log_ui_event(...)`, `DBManager.save_ui_event(...)`, `StudioVisualizer` operator-event sink wiring, `main_a.py` bootstrap buffering, and `AuditService` proof-digest coverage for `ui_events` have all landed.
- `modules/core/stage4_interview_round.py` now carries `0` raw `print(...)` calls, while `main_a.py` is down to `13` residual `print(...)` calls that are concentrated in bootstrap fail-safe paths, threaded metrics reporting, protagonist/entity helper traces, and interactive menu surfaces.
- `modules/core/services/ui_service.py` remains intentionally raw-`print` heavy because it belongs to the later Stage 0 interactive migration tranche, not the direct runtime conversion tranche.
- `bridge_server.py` now writes `control-plane-provenance.jsonl` through an explicit helper path, which reinforces the multi-sink durability direction but does not supersede this operator-event substrate order.
- Revalidation outcome: document direction unchanged; tranche ordering unchanged; Tranche 1 is landed, Tranche 2 core-runtime conversion is materially advanced but not yet closed, and this document remains the first queue item and the prerequisite for later operator-surface work.

## 10. Final Order
The correct direction is:

- `print(...)` in runtime code should converge into a `ui.log`-centered operator surface.
- That surface must persist to both `ui_events.jsonl` and a DB `ui_events` table.
- The migration must be executed by class, not by blind replacement.
- The first implementation target is the substrate and direct-runtime class, then domain callbacks, then Stage 0 interactive conversion.

This gives the system a later-analyzable record of what the operator actually saw, while preserving live console usability.
