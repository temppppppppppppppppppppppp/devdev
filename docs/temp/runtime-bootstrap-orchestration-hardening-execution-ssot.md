# Runtime Bootstrap and Orchestration Hardening Execution SSOT

Date: 2026-03-14
Status: ready for implementation
Canonical Path: `docs/2026-03-14/runtime-bootstrap-orchestration-hardening-execution-ssot.md`
Temp Mirror Path: `docs/temp/runtime-bootstrap-orchestration-hardening-execution-ssot.md`
Source Survey Docs:
- `docs/2026-03-14/codebase-global-rol-deep-global-survey.md`
- `docs/2026-03-14/codebase-global-rol-system-full-survey-3pass-audit.md`
Evidence Artifacts:
- `docs/2026-03-14/codebase-global-rol-deep-survey-inventory.json`
- `docs/2026-03-14/codebase-global-rol-deep-survey-side-effects.json`
- `docs/2026-03-14/codebase-global-rol-deep-survey-entrypoints.txt`
- `docs/2026-03-14/codebase-global-rol-system-survey-inventory.json`
- `docs/2026-03-14/codebase-global-rol-system-survey-side-effects.json`
- `docs/2026-03-14/codebase-global-rol-system-survey-entrypoints.txt`
Side-Effect Coverage: covered
Confidence Target: 95%
Live Workspace Revalidation: 2026-03-14 PASS
Revalidated Confidence: 96%

## 1. Intent
- Reduce runtime authority concentration in `main_a.py`.
- Separate bootstrap, service composition, stage attachment, and shutdown behavior into explicit seams.
- Make later observability, Stage 0, and desktop changes lower-risk by shrinking the live blast radius.

## 2. Baseline Facts
- `main_a.py` is `4222` LOC and still performs stdio bootstrap, faulthandler setup, env load, project selection, DB/session/audit service wiring, optional module bootstrap, stage orchestration, and shutdown.
- `modules/core/stage01_helpers.py` is now a live `905` LOC seam carrying Stage 0 and Stage 1 helper flows, including `105` `ui.log(...)` calls and `19` `input(...)` calls.
- `main_a.py` still contains `44` raw `print(...)` calls, `247` `ui.log(...)` calls, `11` `input(...)` calls, and multiple DB commit/rollback paths.
- `modules/core/stage4_interview_round.py`, `modules/core/stage4_context_builder.py`, `modules/core/stage3_orchestrator.py`, and `modules/core/stage2_*` remain tightly coupled to the app shell.
- Shutdown behavior still mixes metrics, pass-rate persistence, failure learning, cache saves, DB close, and memory close in one path.

## 3. Pass 1. Inventory Summary
- Boot authority:
  - `main_a.py`
  - `modules/core/stage01_helpers.py`
  - `modules/core/services/*.py`
  - `modules/core/system.py`
- High-risk orchestration neighbors:
  - `modules/core/stage4_interview_round.py`
  - `modules/core/stage4_context_builder.py`
  - `modules/core/stage4_orchestrator.py`
  - `modules/core/stage3_orchestrator.py`
  - `modules/core/stage2_preflight.py`
- Persistence hooks reached during bootstrap or shutdown:
  - `modules/core/db_manager.py`
  - `modules/core/session_logger.py`
  - `modules/core/services/audit_service.py`

## 4. Pass 2. Semantic Classification

### Class A. Bootstrap Shell Responsibilities
- console and stderr bootstrap
- env and model/config load
- project and genre selection
- service factory and dependency wiring

### Class B. Runtime Composition Responsibilities
- stage orchestrator construction
- agent lazy-load and optional feature activation
- project-local guard attachment

### Class C. Shutdown and Durability Responsibilities
- audit flush
- metrics and pass-rate persistence
- DB commit and close
- vector-memory close and cleanup

## 5. Side-Effect Map
- file writes and artifacts:
  - crash dump bootstrap
  - metrics and error logs
  - project-local artifacts during runtime and shutdown
- DB and transaction boundaries:
  - explicit commit/rollback paths in the app shell
  - project DB open/close authority during boot and stop
- JSONL and audit sinks:
  - session logger and audit service wired from boot
- console and UI:
  - mixed `print`, `ui.log`, and logging paths inside bootstrap and shutdown
- input and operator prompts:
  - project and stage gating prompts still pass through the app shell

## 6. Realization Architecture
- Introduce a small `BootContext` or equivalent runtime composition object that owns:
  - selected project and genre
  - persistence handles
  - UI/operator sink
  - stage service wiring
- Split the current shell into:
  - bootstrap coordinator
  - runtime composition builder
  - shutdown coordinator
- Move explicit side-effect ownership behind narrow methods so later queue items can depend on stable surfaces.

## 7. Execution Tranches
1. Define runtime composition and shutdown ownership boundaries from the current `main_a.py` shell.
2. Extract bootstrap and shutdown coordination into explicit units without changing user-visible behavior.
3. Move stage attachment and optional-module activation behind composition helpers.
4. Re-audit operator-visible outputs and persistence hooks after extraction, then refresh dependent execution docs.

## 8. Acceptance Criteria
- `main_a.py` no longer owns all bootstrap, runtime, and shutdown responsibilities directly.
- DB, session logger, audit, and UI sinks have explicit ownership boundaries.
- Stage attachment no longer requires a monolithic app shell for every dependency.
- Existing smoke/canary entry surfaces still have a stable boot path after the refactor.

## 9. Verification Plan
- targeted runtime boot smoke on the extracted composition path
- regression sweep over Stage 2/3/4 orchestrator construction
- validator plus current-state document re-audit before implementation start

## 9A. Current-State Revalidation
- Revalidated against live workspace changes in `main_a.py`, `modules/api/bridge_server.py`, `modules/api/process_runner.py`, `modules/core/services/project_service.py`, `modules/domain/agents/base_agent.py`, and `tests/test_main_a_boot_binding.py`.
- `main_a.py` remains `4222` LOC with `44` raw `print(...)`, `247` `ui.log(...)`, and `11` `input(...)` calls, so the monolithic runtime shell problem is still present.
- `_reload_project_environment()` in `main_a.py` still resets `BaseAgent` key state only when a project-local `.env` exists; the new boot-binding test now explicitly asserts that cache/key state is preserved when no project env is rebound. That makes runtime ownership extraction more important, not less, because shell code still owns global agent cache transitions.
- `ProjectService` now carries a structured `DestructiveOpResult` plus partial runtime-restore failure reporting. This adds a clearer runtime-restore seam, but it remains attached to the live app shell and does not remove the broader `main_a.py` authority concentration.
- Revalidation outcome: document direction unchanged; prerequisites unchanged; this item should still follow the operator-event substrate decision.

## 10. Guardrails
- Do not mix this work with behavioral changes to stage logic.
- Do not silently rewrite operator-visible messages while extracting ownership.
- Do not modify the current queue order without refreshing the aggregate roadmap.

## 11. Temp Queue Notes
- temp status: pending
- cleanup condition: remove mirror after implementation and closure
- roadmap dependency: execute after the operator-event substrate decision is stable

## 12. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document
