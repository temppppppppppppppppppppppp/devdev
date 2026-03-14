# Stage 0 Operator Surface Contract Hardening Execution SSOT

Date: 2026-03-14
Status: completed
Canonical Path: `docs/2026-03-14/stage0-operator-surface-contract-hardening-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage0-operator-surface-contract-hardening-execution-ssot.md`
Source Survey Docs:
- `docs/2026-03-14/codebase-global-rol-deep-global-survey.md`
- `docs/2026-03-14/codebase-global-rol-system-full-survey-3pass-audit.md`
- `docs/2026-03-14/residual-print-ui-log-db-full-survey-3pass-execution-ssot.md`
Evidence Artifacts:
- `docs/2026-03-14/codebase-global-rol-deep-survey-side-effects.json`
- `docs/2026-03-14/codebase-global-rol-deep-survey-entrypoints.txt`
- `docs/2026-03-14/codebase-global-rol-deep-survey-regression-surface.txt`
- `docs/2026-03-14/codebase-global-rol-system-survey-side-effects.json`
- `docs/2026-03-14/codebase-global-rol-system-survey-entrypoints.txt`
- `docs/2026-03-14/codebase-global-rol-system-survey-regression-surface.txt`
Side-Effect Coverage: covered
Confidence Target: 95%
Live Workspace Revalidation: 2026-03-14 PASS
Revalidated Confidence: 97%

## 1. Intent
- Replace the remaining CLI-era Stage 0 interaction model with a governed operator surface contract.
- Make Stage 0 prompts, selections, progress frames, and file writes observable and durable.
- Align Stage 0 with the desktop bridge and the operator-event persistence direction already captured by the residual-print execution doc.

## 2. Baseline Facts
- `modules/core/stage0/__init__.py` is `811` LOC and contains `100` raw `print(...)` calls, `14` `input(...)` calls, `7` `open_write` hits, and `4` `json.dump(...)` hits.
- `modules/core/stage01_helpers.py` is `905` LOC and already acts as a live Stage 0/1 surface with `105` `ui.log(...)` calls, `19` `input(...)` calls, `2` write openings, and `2` `json.dump(...)` hits.
- `modules/core/services/ui_service.py` is `149` LOC and still contains `5` raw `print(...)` calls plus direct `input(...)` for bible/treatment and integer-choice flows.
- `modules/core/stage0/spinner.py` owns `40` `console.print(...)` calls, so Stage 0 already has a second console path besides raw `print`.
- Stage 0 performs real side effects such as work-guard YAML creation, template import, and project-scoped configuration writes.

## 3. Pass 1. Inventory Summary
- dominant files:
  - `modules/core/stage0/__init__.py`
  - `modules/core/stage01_helpers.py`
  - `modules/core/services/ui_service.py`
  - `modules/core/stage0/style_extractor.py`
  - `modules/core/stage0/reverse_expander.py`
  - `modules/core/stage0/story_expander.py`
- key operator interactions:
  - genre and project setup
  - Stage 0 recovery and Stage 1 volume-boundary helper menus
  - bible and treatment selection
  - work-guard template import and reset
  - style extraction and cache choices

## 4. Pass 2. Semantic Classification

### Class A. Human Prompt/Selection Surfaces
- menu display
- numeric choice input
- empty-default fallback behavior

### Class B. Progress and Status Surfaces
- spinner output
- selection confirmation lines
- style extraction and generation progress

### Class C. Mutable Project Configuration Surfaces
- work-guard YAML creation, import, deletion
- project config and support material selection

## 5. Side-Effect Map
- file writes and artifacts:
  - work-guard YAML writes and deletes
  - stage-specific JSON outputs and style artifacts
- console and UI:
  - raw `print`, `console.print`, and partial `ui.log` coexist
- input:
  - Stage 0 depends on direct blocking `input(...)`
- config mutation:
  - project-local config files are changed during Stage 0 operations

## 6. Realization Architecture
- Define a Stage 0 operator contract that distinguishes:
  - display events
  - prompt requests
  - prompt resolutions
  - selection summaries
  - mutation confirmations
- Route Stage 0 output through a shared adapter instead of direct `print` and `input` calls.
- Coordinate persistence with the operator-event substrate from the residual-print execution doc so Stage 0 events are durable and analyzable.

## 7. Execution Tranches
1. Define the Stage 0 menu/prompt/selection event contract and the minimum durable fields.
2. Add an adapter layer around `modules/core/stage0/__init__.py` and `modules/core/services/ui_service.py`.
3. Normalize spinner/progress output into the same operator surface contract.
4. Align desktop prompt resolution and Stage 0 operator persistence with the new contract.

Implementation note:
- 2026-03-14 current workspace now lands typed `menu_block`, `prompt`, `selection`, and `summary` helpers in `StudioVisualizer`.
- `modules/core/stage0/__init__.py`, `modules/core/services/ui_service.py`, and `modules/core/stage01_helpers.py` now route Stage 0 prompt and selection surfaces through that typed operator contract.
- `modules/core/stage0/style_extractor.py` now emits progress through a callback-based reporting surface instead of raw prints.
- `modules/core/stage0/spinner.py` remains the only Stage 0 console-specialized surface, and its residual raw prints are limited to fallback blank-line rendering and file-bottom demo/test code rather than active Stage 0 workflows.

## 8. Acceptance Criteria
- Stage 0 no longer depends on free-form raw `print` as its primary operator surface.
- Prompt and selection flows can be represented consistently in CLI, Rich, and desktop contexts.
- Stage 0 writes that mutate project config can be tied to operator-visible confirmation events.
- Existing Stage 0 regression tests can be updated without reintroducing direct console ownership drift.

## 9. Verification Plan
- `tests/test_ui_service.py`
- `tests/test_stage0_*`
- `tests/test_frontend_stage0_connectivity.py`
- desktop prompt-path contract checks after the Stage 0 contract is defined

## 9A. Current-State Revalidation
- Revalidated against live workspace state in `modules/core/stage01_helpers.py`, `modules/core/services/ui_service.py`, `modules/core/services/project_service.py`, and `modules/core/stage0/__init__.py`.
- Stage 0 no longer depends on raw `print(...)` in its primary interactive surfaces: `modules/core/stage0/__init__.py`, `modules/core/services/ui_service.py`, `modules/core/stage0/style_extractor.py`, and `modules/core/stage01_helpers.py` now carry `0` raw `print(...)` calls.
- Stage 0 prompt paths now run through typed UI helpers when a live `StudioVisualizer` is present, while retaining guarded fallback `input(...)` only for non-UI test or shim paths.
- `tests/test_ui_service.py`, `tests/test_stage0_fixes.py`, `tests/test_stage0_work_guard_style_cache.py`, `tests/test_stage01_helpers.py`, `tests/test_stage01_fixes.py`, `tests/test_process_runner_stage0_inputs.py`, and `tests/test_frontend_stage0_connectivity.py` all pass against the new contract.
- `ProjectService` now emits structured destructive-operation outcomes and partial restore failures through `ui.log`. That strengthens the case for a typed operator contract because mutation confirmation and runtime-restore status are becoming richer than plain prompt/print flows.
- No contradictory desktop-first or silent-automation path has landed in current code; the live Stage 0 operator surface now routes through the same operator-event persistence direction established by the residual-print execution work.
- Revalidation outcome: document direction confirmed; the planned Stage 0 operator contract is landed; this execution SSOT is complete.

## 10. Guardrails
- Do not collapse Stage 0 into silent automation; preserve explicit operator checkpoints.
- Do not start with global `print` replacement inside Stage 0.
- Do not diverge from the operator-event persistence direction already queued in the residual-print execution doc.

## 11. Temp Queue Notes
- temp status: completed
- cleanup condition: remove mirror after implementation and closure
- roadmap dependency: execute after operator-event substrate and runtime bootstrap ownership are stabilized

## 12. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

Closure note:
- This execution SSOT is closed as completed on 2026-03-14.
- The temp mirror should be removed from the active execution queue after roadmap sync.
