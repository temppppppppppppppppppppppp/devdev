# Codebase Parallel Deep Survey Wave1 Synthesis

Date: 2026-04-25
Status: final wave1 synthesis; not a full deep-global bundle closure
Canonical Path: `docs/2026-04-25/codebase-parallel-deep-survey-wave1-synthesis.md`
Temp Mirror Path: not applicable; this is a survey synthesis, not an execution SSOT

Commit State:
- Baseline Commit: `2bcb2db2c4364400628cb55890609aee1f0a9db3`
- Baseline Dirty Summary: `clean`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## Scope

This document captures the first parallel read-only system-track survey wave after the Stage234 session-memory work and the Stage4 HUD snapshot residual fix were closed.

The intent is to identify high-leverage future waves without patching code or creating an execution queue in the same turn.

Included live-code surfaces:
- `main_a.py`
- `modules/core/`
- `modules/domain/`
- `modules/api/`
- `modules/ui/`
- `geuldobi-desktop/`
- `scripts/`
- `tests/`
- `config/`
- `contracts/`
- `.github/workflows/`
- recent canonical session-memory docs from `docs/2026-04-23/` through `docs/2026-04-25/`

Excluded or reference-only surfaces:
- historical docs not tied to the current wave
- generated logs and project artifacts, except as side-effect path references
- live canary/runtime replay; no fresh live run was performed
- implementation; no files were patched beyond this survey document

Path census from live workspace:

| Surface | Files | Primary meaning |
| --- | ---: | --- |
| `main_a.py` | 1 | CLI/runtime entry and compatibility shell |
| `modules/core/` | 219 | runtime orchestration, persistence, Stage2/3/4, observability |
| `modules/domain/` | 57 | agent/domain generation and validation logic |
| `modules/api/` | 7 | bridge server, process runner, control-plane contracts |
| `modules/ui/` | 1 | Python UI service surface |
| `geuldobi-desktop/` | 58 | Electron shell, IPC, renderer, packaging |
| `scripts/` | 119 | canary, smoke, ops, migration, corpus, sync utilities |
| `tests/` | 513 | Python/JS regression, contract, chaos, e2e surfaces |
| `config/` | 63 | model, system, validation, prompt/runtime settings |
| `contracts/` | 11 | JSON schemas and runtime contracts |
| `.github/workflows/` | 1 | CI workflow |

## Parallel Lanes

Five read-only explorer lanes inspected different risk surfaces:

| Lane | Focus |
| --- | --- |
| Memory/Core Truth | session memory, FactLedger, WorldState, anchors, carryover, truth pins |
| Stage2/Stage3/Stage4 Runtime | orchestration, retry, semantic budget, interruption/resume |
| Persistence/Observability | DB, JSONL, audit, logs, rollback, config/env side effects |
| Operator/App Shell | Electron, bridge server, process runner, UI/HUD truth surfaces |
| Quality/Scripts/Contracts | tests, smoke/canary, scripts, config, stale references |

No lane edited files. No lane ran live canaries or broad pytest shards.

## Pass 1 - Inventory Findings

Runtime topology:
- `main_a.py` remains the operator-facing runtime shell and delegates Stage2/Stage3/Stage4 to orchestrators.
- Stage2, Stage3, and Stage4 have separate context snapshots from app state.
- Stage4 lazy-initializes `WorldStateManager` and `FactLedger` before `Stage4Context.from_app`.
- Desktop flow is Electron IPC -> FastAPI bridge -> `ProcessRunner` -> `main_a.py` subprocess.
- Durable truth is primarily project DB, anchors, `stage_attempts`, episode logs, and stage artifacts.
- `/status`, runtime audit summary, session JSONL, and renderer HUDs are companion surfaces, not durable authority.

Memory/core truth:
- Persisted Stage4 attempt hydration appears materially closed versus the older 2026-04-23 risk docs.
- `session_memory_envelope` preserves structured retry/truth/carryover context through `stage_attempts`.
- FactLedger and WorldState are DB-backed anchor surfaces with caller-save mutation boundaries.
- Truth pins persist more strongly than they are always visible in compact retry prompt surfaces.

Persistence and side effects:
- DB sinks include `manuscripts`, `blueprints`, `anchors`, `stage_attempts`, `attempt_raw_rationale`, `llm_calls`, `context_cache_attempts`, `ui_events`, quality tables, world/fact tables, and vector/retrieval tables.
- JSONL/log sinks include `logs/session/*.jsonl`, `episode_production.jsonl`, `runtime_audit.jsonl`, `runtime_audit_summary.json`, `soft_failures.jsonl`, `control-plane-provenance.jsonl`, and risk-approval logs.
- File/artifact sinks include Stage4 manuscript exports, emergency dumps, settlement packets, canary prep/summary artifacts, and logged stage artifacts.

Operator surface:
- Active UI surface is `geuldobi-desktop/` plus `modules/api/`; root `UI/` is absent.
- Renderer state can be optimistic before `/run` success.
- Verdict HUD parsing is stdout-pattern based and can diverge from persisted quality truth.
- Backend restart can reset in-memory bridge/process state while durable process truth must be recovered from DB/log/provenance surfaces.

Quality and contracts:
- Tests are broad and memory-sensitive; default safe verification should remain targeted sequential shards.
- Smoke/canary scripts are more formally tiered than direct-supervised runners.
- Several governance/script references are stale or absent in the live workspace.

Complexity hotspots:
- Production `180+ LOC` functions found: 20.
- Production owner classes with `50+` direct methods found: 16.
- Top owner-pressure classes include `Stage4InterviewRound`, `SovereignApp`, `DBManager`, `StateTracker`, `ChiefWriter`, `FailureAnalyzer`, `Stage4Orchestrator`, and `Stage4ContextBuilder`.

## Pass 2 - Risk Classification

### P1 Candidates

These are not declared confirmed runtime failures, but they are strong future-wave candidates because multiple evidence surfaces point at the same risk shape.

1. Stage4 partial settlement boundary

`Stage4PostProcessor._save_pass_result_primary_db` commits manuscript/HUD primary DB work before later post-pass metadata and settlement work. If post-pass metadata fails, `process_pass_result` returns `False` while the manuscript body may already be persisted. This is intentionally logged, but future resume and operator-status logic must distinguish `manuscript exists` from `PASS fully settled`.

Evidence:
- `modules/core/stage4_post_processor.py:890`
- `modules/core/stage4_post_processor.py:1287`
- Stage2/3/4 runtime lane report

2. API stop path may bypass in-process graceful cleanup

`ProcessRunner.stop()` terminates and then kills the subprocess if needed. Stage4 has `KeyboardInterrupt` handling and audit/commit cleanup, but external termination can bypass the same Python-level cleanup path.

Evidence:
- `modules/api/process_runner.py:413`
- `modules/core/stage4_orchestrator.py` interruption handling surface inspected by runtime lane
- Operator/app shell lane report

### P2 Candidates

1. DB evidence preservation policy mismatch

The workspace policy says DB diagnostic/judgment/reason fields should not be truncated by Python, but some TEXT-like evidence fields are still sliced before DB insertion.

Evidence:
- `modules/core/db_manager.py:2580` truncates `operator_label`
- `modules/core/db_manager.py:3489` truncates UI event `message`
- `modules/core/db_manager.py:3492` truncates `prompt_id`
- `modules/core/db_manager.py:3493` truncates `artifact_path`
- `modules/core/vec_memory.py` metadata truncation reported by persistence lane

2. TruthGate advisory status versus hard governance invariant

The workspace invariant says deceased-character action/dialogue must be REJECT. The inspected `TruthGate.validate()` path always returns `blocking: False`; Stage4 post-pass treats TruthGate warnings as advisory. This may be enforced elsewhere, so the finding is scoped to this inspected gate and needs a focused authority trace before implementation.

Evidence:
- `modules/core/truth_gate.py:24`
- `modules/core/truth_gate.py:58`
- `AGENTS.md` deceased-character invariant
- Memory/Core Truth lane report

3. Runtime telemetry transaction inconsistency

Some telemetry sinks respect outer transactions, while `save_llm_call` and `save_context_cache_attempt` commit unconditionally. This can prematurely commit when telemetry is invoked inside a broader transaction boundary.

Evidence:
- `modules/core/db_manager.py:3212`
- `modules/core/db_manager.py:3266`
- Persistence/Observability lane report

4. Direct-supervised runner tiering gap

Direct-supervised runners are mutating operational tools, but they are less formally classified than smoke/canary paths in regression tier inventory.

Evidence:
- `scripts/run_stage2_direct_supervised.py`
- `scripts/run_stage3_direct_supervised.py`
- `scripts/run_stage4_direct_supervised_guarded.py`
- `scripts/regression_validation_tiers.py`
- Quality/Scripts/Contracts lane report

### P3 Candidates

1. Operator display truth can drift from durable truth

Renderer/HUD status uses local optimistic state, stdout parsing, and `/status` companion snapshots. Durable authority remains DB/log/provenance surfaces.

Evidence:
- `modules/api/control_plane_contract.py`
- `modules/api/bridge_server.py`
- `geuldobi-desktop/src/index.html`
- Operator/App Shell lane report

2. Stale governance and operator references

Live workspace lacks some paths referenced by governance/README materials.

Evidence:
- `docs/2026-03-23/llm-codebase-orientation-pack.md`: absent
- `scripts/generate_evidence_manifest.py`: absent
- `scripts/generate_tr_bibles.py`: absent
- `scripts/generate_stagewise_manuscript_truth_report.py`: absent
- `UI/`: absent
- `README.md:226`
- `docs/implementation/system-order-init-harness.md:133`

3. JSONL helper parent-directory fragility

`append_jsonl_record` does not create parent directories. Many callers create parent directories first, but future sink callers can fail if they assume the helper owns that contract.

Evidence:
- `modules/core/jsonl_io.py:13`
- Persistence/Observability lane report

4. Truth-pin visibility cap

Structured truth pins persist, but compact retry prompt surfaces may only show a bounded top subset. This is acceptable as a budget strategy, but it depends on ordering and severity ranking staying correct.

Evidence:
- `modules/core/session_memory_envelope.py`
- `modules/core/stage4_interview_round.py`
- `modules/domain/agents/chief_writer.py`
- Memory/Core Truth lane report

5. Complexity pressure remains concentrated

Recent waves closed specific residual bugs, but owner pressure remains high in core Stage4, DB, and app shell owners. New work in those files should prefer boundary design and small patches over same-owner helper accumulation.

Evidence:
- AST inventory in this wave: `20` production functions at `180+ LOC`
- AST inventory in this wave: `16` production owner classes at `50+` methods

## Pass 3 - Execution Shape

No execution SSOT was created in this wave. Recommended future waves are:

1. `stage4-pass-settlement-authority-recheck`

Goal: prove and, if needed, harden the distinction between `manuscript persisted`, `post-pass metadata settled`, and `PASS fully authoritative`.

Likely surfaces:
- `modules/core/stage4_post_processor.py`
- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/services/audit_service.py`
- `tests/test_stage4_post_processor.py`
- `tests/test_stage4_orchestrator.py`

2. `api-graceful-stop-interruption-contract`

Goal: design a graceful stop/interrupt path that lets runtime cleanup execute before terminate/kill fallback.

Likely surfaces:
- `modules/api/process_runner.py`
- `modules/api/bridge_server.py`
- `geuldobi-desktop/src/main.js`
- `tests/test_process_runner.py`
- desktop bridge tests

3. `db-evidence-preservation-policy-alignment`

Goal: remove or justify Python-side truncation before DB persistence for diagnostic/judgment/reason/evidence TEXT fields.

Likely surfaces:
- `modules/core/db_manager.py`
- `modules/core/vec_memory.py`
- `modules/core/soft_failure.py`
- DB manager and observability tests

4. `truth-gate-hard-authority-trace`

Goal: trace every deceased-character enforcement path and decide whether `TruthGate` should become blocking, stay advisory, or feed a separate hard gate.

Likely surfaces:
- `modules/core/truth_gate.py`
- Stage4 post-pass and validation paths
- Director/blocking validator surfaces
- `tests/test_truth_gate.py`
- canonical constraint tests

5. `operator-authority-display-contract`

Goal: make the UI show which status is durable authority versus companion telemetry, especially after backend restart, stop, or partial settlement.

Likely surfaces:
- `modules/api/control_plane_contract.py`
- `modules/api/bridge_server.py`
- `geuldobi-desktop/src/index.html`
- desktop/API contract tests

6. `governance-stale-reference-cleanup`

Goal: repair absent orientation/script/UI references or replace them with current authoritative paths.

Likely surfaces:
- `AGENTS.md`
- `README.md`
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/codebase-global-survey-coverage-contract.md`
- `scripts/README.md`

## Side-Effect Matrix

| Category | Coverage |
| --- | --- |
| File writes/artifacts | Covered by Stage4 post-processor, artifact logging, canary, desktop, and script lanes |
| DB writes | Covered by DBManager, FactLedger, WorldState, quality, stage attempt, and telemetry sink survey |
| JSONL/log/audit sinks | Covered by session logger, audit service, episode production, provenance, risk approval, and JSONL helper survey |
| Console/UI output | Covered by app shell, bridge, process runner, renderer HUD/stdout parsing survey |
| Rollback/recovery/retry | Covered by Stage2/3/4 runtime, project service, canary cleanup, and post-pass retry survey |
| Cache/global state | Covered by VecMemory, session memory envelope, context cache attempts, and app context snapshot survey |
| Config/env/bootstrap | Covered by process runner env, model/config/settings surfaces, and DB bootstrap survey |
| Generated artifact body truth | Deferred; no fresh live run or artifact body audit in this wave |

## Contradiction And Uncertainty Ledger

| Item | Status | Confidence impact |
| --- | --- | --- |
| `TruthGate` advisory path versus deceased-character hard invariant | Open; requires full Director/blocking-validator authority trace | Caps any hard-gate claim below execution-ready confidence |
| Stage4 partial-settlement behavior | Open as risk; code confirms boundary, live replay not performed | Needs focused execution SSOT before patching |
| DB truncation policy mismatch | Strong code evidence; exact policy classification per field still needs local scope review | Good future P2 wave |
| Operator display truth mismatch | Strong architecture evidence; no live Electron run | Needs live/UI verification before UX patch |
| Missing orientation pack and scripts | Confirmed absent in live workspace | Good governance cleanup candidate |
| Full deep-global completion | Not claimed | This is wave1 synthesis only |

## Document 3-Pass Audit

Pass 1 - Structure and scope:
- Document type is survey synthesis, not execution SSOT.
- Scope, included paths, excluded paths, baseline commit, and dirty state are explicit.
- No `docs/temp` mirror is created because no execution queue item is being produced.

Pass 2 - Evidence and consistency:
- High-level claims are tied to live-code paths, explorer lane findings, or explicit path existence checks.
- The stale-reference claims were confirmed with `Test-Path`.
- The complexity counts were generated with AST-based inventory over production Python surfaces.
- No live-run success or failure is claimed.

Pass 3 - Execution/readability:
- Future waves are named and bounded.
- The document avoids implementation authorization.
- Risks are separated from confirmed failures.
- Uncertainties are explicit enough for the next operator to avoid re-inventing the same survey.

Estimated confidence:
- Bounded wave1 synthesis confidence: `95%`
- Full deep-global bundle closure confidence: not claimed

Reasons confidence is not higher:
- no fresh live canary or Electron run
- no broad pytest shard execution
- no generated artifact body truth audit
- no execution SSOT or single roadmap created yet

## Closure

This wave confirms that the recently closed session-memory work is not the obvious next failure surface. The higher-value future targets are now around pass-settlement authority, graceful interruption, DB evidence preservation, hard truth-gate authority, operator truth display, governance drift, and complexity pressure.

The next step should be a focused execution SSOT for one of the P1/P2 candidates, not another broad blind survey.
