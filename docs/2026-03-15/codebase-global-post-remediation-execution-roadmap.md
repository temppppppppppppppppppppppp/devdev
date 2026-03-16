<!-- [참고자료] -->
# codebase-global-post-remediation Aggregate Execution Roadmap

Date: 2026-03-15
Status: closed
Canonical Path: `docs/2026-03-15/codebase-global-post-remediation-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Commit State:
- Baseline Commit: `bbb00a77c7356a32fe6358642cff0d3d445b7e8e`
- Baseline Dirty Summary: `dirty: AGENTS/docs/harness/menu7 docs edits, active roadmap/temp edits, harness/test edits, deleted local transcript file, unrelated pdf/style/log artifacts, and untracked post-remediation docs plus projects/000/`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `every queued lane is complete; the two older completed temp residues are now closure-refreshed and the temp queue is exhausted`
Predecessor: `codebase-global-log-evidence-merged-execution-roadmap.md`
Post-Remediation Survey: `docs/2026-03-15/codebase-global-post-remediation-deep-global-survey.md` (96/100)
TF Composition: `docs/2026-03-15/codebase-global-post-remediation-tf-composition.md` (14 items; residual `TF-012` through `TF-020` are absorbed by the new integrated lane)
Queue Snapshot:
- none; queue exhausted after final closure refresh

## 1. Purpose
- Govern the action-bearing execution queue created by the post-remediation survey bundle.
- Keep one roadmap with SSOT authority across completed residue, active operator/control-plane items, the bounded `projects/000` manuscript-truth lane, and the residual survey-followup lane.
- Keep project-scoped manuscript memos such as the `projects/00_260315` OPUS contradiction doc out of the active queue unless they are revalidated for the current target scope.

## 2. Queue Inventory

| Item | Canonical Path | Temp Path | Status | Notes |
| --- | --- | --- | --- | --- |
| persistence/observability finalization and sink alignment | `docs/2026-03-15/persistence-observability-finalization-and-sink-alignment-remediation-execution-ssot.md` | `docs/temp/persistence-observability-finalization-and-sink-alignment-remediation-execution-ssot.md` | completed | Lane 1 fully implemented in `bbb00a77`; canonical closure refreshed and temp mirror removed |
| source text and runtime/output encoding hygiene | `docs/2026-03-15/source-text-and-runtime-encoding-hygiene-remediation-execution-ssot.md` | `docs/temp/source-text-and-runtime-encoding-hygiene-remediation-execution-ssot.md` | completed | Lane 2 fully resolved in `d2982aa2` + `bbb00a77`; canonical closure refreshed and temp mirror removed |
| menu7 desired Arc input contract | `docs/2026-03-15/menu7-desired-arc-input-contract-remediation-execution-ssot.md` | `docs/temp/menu7-desired-arc-input-contract-remediation-execution-ssot.md` | completed | `TF-010` implemented in live workspace; temp mirror removed after closure refresh |
| backend-front/control-plane connectivity | `docs/2026-03-15/backend-front-control-plane-connectivity-hardening-remediation-execution-ssot.md` | `docs/temp/backend-front-control-plane-connectivity-hardening-remediation-execution-ssot.md` | completed | `TF-007` through `TF-009` implemented with targeted regression coverage plus minimal desktop `start:spike` runtime proof; temp mirror removed after closure refresh |
| runtime/operator surface unification | `docs/2026-03-15/runtime-operator-surface-unification-refresh-remediation-execution-ssot.md` | `docs/temp/runtime-operator-surface-unification-refresh-remediation-execution-ssot.md` | completed | `TF-011` closed with shared UIService prompt helpers, ProjectService callback injection, fallback prompt telemetry alignment, and a saved prompt-authority chain note |
| stagewise manuscript truth and narrative continuity follow-up | `docs/2026-03-15/stagewise-manuscript-truth-and-narrative-continuity-followup-execution-ssot.md` | `docs/temp/stagewise-manuscript-truth-and-narrative-continuity-followup-execution-ssot.md` | completed | Bounded helper/report lane closed with saved `projects/000` report/json authority; temp mirror removed after closure refresh |
| post-remediation unqueued survey follow-ups | `docs/2026-03-15/post-remediation-unqueued-survey-followups-execution-ssot.md` | `docs/temp/post-remediation-unqueued-survey-followups-execution-ssot.md` | completed | Integrated residual lane is fully realized; TF-019 is now complete and the temp mirror is removed after closure refresh |

## 3. Dependency Graph
- ~~`persistence finalization -> source-text-and-runtime-encoding hygiene`~~ (both complete)
- ~~`source-text-and-runtime-encoding hygiene -> menu7 desired Arc input contract`~~ (predecessor complete)
- ~~`source-text-and-runtime-encoding hygiene -> backend-front/control-plane connectivity`~~ (predecessor complete)
- ~~`menu7 desired Arc input contract -> runtime/operator surface unification`~~ (complete)
- ~~`backend-front/control-plane connectivity -> runtime/operator surface unification`~~ (complete)
- ~~`runtime/operator surface unification -> stagewise manuscript truth and narrative continuity follow-up`~~ (complete)
- ~~`stagewise manuscript truth and narrative continuity follow-up -> post-remediation unqueued survey follow-ups`~~ (predecessor complete)
- `persistence finalization -> post-remediation unqueued survey follow-ups`
- ~~`runtime/operator surface unification -> post-remediation unqueued survey follow-ups`~~ (complete)
- shared substrate:
  - stabilized persistence and encoding lanes are already complete
  - the manuscript-truth lanes and residual integrated lane all reuse those closures without reopening them

## 4. Execution Order
Priority basis:
- `docs/implementation/queue-priority-rubric.md`
- `docs/2026-03-15/codebase-global-post-remediation-tf-composition.md`

1. ~~persistence/observability finalization and sink alignment~~ **COMPLETE** (`bbb00a77`)
2. ~~source text and runtime/output encoding hygiene~~ **COMPLETE** (`d2982aa2` + `bbb00a77`)
3. ~~menu7 desired Arc input contract~~ **COMPLETE** (`main_a.py` + targeted FrontierLag tests)
4. ~~backend-front/control-plane connectivity~~ **COMPLETE** (`TF-007` through `TF-009`)
5. ~~runtime/operator surface unification~~ **COMPLETE** (`TF-011`)
6. ~~stagewise manuscript truth and narrative continuity follow-up~~ **COMPLETE** (`stagewise manuscript truth report helper + saved projects/000 authority`)
7. ~~post-remediation unqueued survey follow-ups~~ **COMPLETE** (`TF-012`, `TF-014`, `TF-015`, `TF-016`, and `TF-019` implemented; `TF-013`, `TF-017`, `TF-018`, and `TF-020` closed)

## 5. Per-Item Plan

### persistence/observability finalization and sink alignment — COMPLETE
- goal:
  - stop late writes after close, finalize summary at a quiescent point, unify session/sink lineage, restore artifact-hash truth, and eliminate teardown exceptions plus Stage 4 rationale mismatches
- status:
  - complete in `bbb00a77`
- evidence:
  - bounded persistence validation and the post-remediation survey bundle
- temp cleanup action:
  - complete; temp mirror removed after final closure refresh

### source text and runtime/output encoding hygiene — COMPLETE
- goal:
  - remove active source corruption and make operator/output hygiene tooling trustworthy
- status:
  - complete in `d2982aa2` + `bbb00a77`
- evidence:
  - encoding boundary, mojibake, and UTF-8 hygiene test suites
- temp cleanup action:
  - complete; temp mirror removed after final closure refresh

### menu7 desired Arc input contract
- goal:
  - let the operator choose the desired Arc total from menu `7` while keeping Frontier Lag automatic afterward
- prerequisites:
  - source/output hygiene is already stabilized
- execution notes:
  - preserve harness bypass semantics and failure-path prompts
- completion signal:
  - menu `7` asks exactly once for the desired Arc total, Enter keeps the default, and the requested-limit stop is honored
- temp cleanup action:
  - complete; temp mirror removed after closure refresh

### backend-front/control-plane connectivity
- goal:
  - separate command readiness from websocket readiness and close prompt/reconnect drift with runtime proof
- status:
  - complete in the current workspace
- evidence:
  - renderer/backend contract is explicit and regression-tested
  - `/status` reconnect snapshots and queued prompt replay are active
  - `npm run start:spike` completed as a minimum desktop handoff runtime proof
- temp cleanup action:
  - complete; temp mirror removed after closure refresh

### runtime/operator surface unification
- goal:
  - reduce remaining prompt-authority fragmentation without re-owning the dedicated menu7 Arc-count contract
- status:
  - complete in the current workspace
- evidence:
  - `main_a.py` now routes continuation/skip/pause prompts through `UIService`
  - `ProjectService` destructive prompts now use injected shared callbacks in the live app path
  - `docs/2026-03-15/runtime-operator-prompt-authority-chain.md` captures the prompt lifecycle across CLI and desktop broker mode
  - fallback prompt telemetry emits hidden `prompt_response` events
- temp cleanup action:
  - complete; temp mirror removed after closure refresh

### stagewise manuscript truth and narrative continuity follow-up
- goal:
  - turn direct `projects/000` artifact, metadata, and terminal manuscript checks into one reusable audit/report authority instead of ad hoc post-run grep
- status:
  - complete in the current workspace
- evidence:
  - `modules/core/stagewise_manuscript_truth_report.py` now builds one bounded cross-stage authority surface from Stage 2/3/4 artifacts plus JSONL sinks
  - `scripts/generate_stagewise_manuscript_truth_report.py` now materializes the saved report for a target project
  - `docs/2026-03-15/stagewise-manuscript-truth-and-narrative-continuity-report.md`
  - `docs/2026-03-15/stagewise-manuscript-truth-and-narrative-continuity-report.json`
- temp cleanup action:
  - complete; temp mirror removed after closure refresh

### post-remediation unqueued survey follow-ups
- goal:
  - realize only the final 2026-03-15 survey findings that were not yet represented by a temp execution SSOT, covering `TF-012` through `TF-020`
- status:
  - complete in the current workspace
- prerequisites:
  - completed persistence/encoding lanes stay authoritative
  - backend-front/runtime predecessors are now complete and should not be reopened here
  - the manuscript-truth follow-up lane has already published its bounded `projects/000` audit authority before this lane re-entered Stage 4 follow-up work
- evidence:
  - `modules/core/db_manager.py` now exposes richer persisted Stage 4 attempt lineage through `get_stage_attempts_for_arc()`
  - `modules/core/stage4_context_builder.py` now includes representative rejection and retry/advisory guidance in the mandatory Stage 4 failure context
  - targeted regression coverage was added in `tests/test_db_manager.py` and `tests/test_stage4_context_builder.py`
  - `docs/2026-03-15/tf-013-db-connection-pooling-evaluation.md` retains the current single-connection SQLite model and records why pooling does not merit a successor lane yet
  - `docs/2026-03-15/tf-017-jsonl-sink-consolidation-evaluation.md` retains the current split JSONL sink lock strategy and records why global unification does not merit a successor lane yet
  - `docs/2026-03-15/tf-018-di-context-slot-audit-evaluation.md` retains the current DI structure and refreshes live slot-inventory authority without promoting a Stage 2 refactor lane
  - `docs/2026-03-15/tf-020-test-coverage-mapping-report.md` saves the current module-level coverage baseline and blocker map without widening into immediate test-fix implementation
  - `docs/2026-03-16/tf-014-console-print-audit.md` records the bounded runtime print cleanup and the retained bootstrap/spinner allowlist boundary
  - `docs/2026-03-16/tf-015-ruff-auto-fix.md` records the completed mechanical Ruff cleanup and the remaining manual `E402` set
  - `docs/2026-03-16/tf-016-ruff-manual-fix.md` records the explicit suppression of the intentional script-entrypoint `E402` cases
  - `docs/2026-03-16/tf-019-guard-chain-config-validation.md` records the fail-fast `work_guard.yaml` validation seam and the summary-surface validity reporting
- execution notes:
  - tranche `1`: `TF-012` Stage 4 context/DB retrieval/reject persistence follow-up is complete
  - tranche `2`: `TF-013`, `TF-017`, `TF-018`, and `TF-020` are complete as decision/report artifacts
  - tranche `3`: bounded code-health hardening `TF-014`, `TF-015`, `TF-016`, and `TF-019` are complete
- completion signal:
  - the integrated lane is either fully realized and closed or split into explicit successor execution SSOTs with the parent lane closed
- temp cleanup action:
  - complete; temp mirror removed after closure refresh

## 6. Shared Risks And Side-Effects
- shared write paths:
  - runtime source files, tests, prompt/config surfaces, desktop control-plane files, real output artifacts under `projects/000`, dated docs, and optional lint/coverage artifacts
- shared DB/schema touchpoints:
  - the residual integrated lane touches Stage 4 retrieval helpers and the DB connection model, but should avoid opportunistic schema expansion
- shared logs/UI surfaces:
  - operator-visible prompt text, bridge diagnostics, Stage 4 rationale visibility, and diagnostic print/log behavior
- rollback/recovery concerns:
  - shutdown lifecycle, reconnect behavior, prompt timeout/default handling, Stage 4 carryover integrity, terminal manuscript audit authority, contradiction-regression behavior, and startup config validation
- queue collision or ordering risks:
  - the residual integrated lane should now treat the saved `projects/000` manuscript-truth report as predecessor authority rather than re-surveying that bounded surface ad hoc
  - re-introducing project-scoped manuscript memos into the active queue without a scope revalidation would contaminate `projects/000` authority with foreign-session conclusions
  - leaving completed mirrors in temp without later closure cleanup will keep the queue noisier than necessary, so closure remains required

## 7. Status Ledger

| Item | Status | Last Update | Blocker |
| --- | --- | --- | --- |
| persistence/observability finalization and sink alignment | completed | 2026-03-16 | none |
| source text and runtime/output encoding hygiene | completed | 2026-03-16 | none |
| menu7 desired Arc input contract | completed | 2026-03-15 | none |
| backend-front/control-plane connectivity | completed | 2026-03-15 | none |
| runtime/operator surface unification | completed | 2026-03-15 | none |
| stagewise manuscript truth and narrative continuity follow-up | completed | 2026-03-15 | none |
| post-remediation unqueued survey follow-ups | completed | 2026-03-16 | none |

## 8. Queue Cleanup Rule
- remove a temp execution SSOT mirror immediately after that item is realized and closed
- keep canonical dated docs
- when all items are completed, remove `docs/temp/execution-roadmap.md`
- remove `docs/temp/queue-state.json` if present
- leave `docs/temp/README.md`
