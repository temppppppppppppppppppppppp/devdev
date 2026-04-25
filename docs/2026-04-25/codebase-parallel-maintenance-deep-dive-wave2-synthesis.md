# Codebase Parallel Maintenance Deep Dive Wave2 Synthesis

Date: 2026-04-25
Status: final-survey
Canonical Path: `docs/2026-04-25/codebase-parallel-maintenance-deep-dive-wave2-synthesis.md`
Temp Mirror Path: not applicable; survey-only output, no execution queue opened

Commit State:

- Baseline Commit: `ccc3ac914fe32a2179b96636ea0c6d352e2e2713`
- Baseline Dirty Summary: `clean`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

Source Inputs:

- `AGENTS.md`
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/codebase-global-survey-coverage-contract.md`
- `docs/implementation/deep-global-integrity-survey-harness.md`
- six read-only parallel explorer lanes:
  - runtime core / stage authority
  - persistence / observability
  - operator API / desktop shell
  - tests / CI / validation scripts
  - governance / process contracts
  - domain / agent / prompt / truth layer
- local verification snippets and AST hotspot inventory

Scope:

- This is a maintenance deep-dive survey, not an implementation wave.
- No code was patched.
- No temp execution SSOT mirror was created.
- No live run, canary, or full pytest suite was executed.
- `python scripts/ops_validator.py --strict` passed before survey synthesis and reported no active temp execution mirrors.

## Executive Synthesis

The codebase is materially stronger after the Stage4 settlement status merge, but the next risk layer is broader than a single sink. The most important remaining issues cluster around:

1. hard authority gates that can degrade into advisory text
2. run-completion surfaces that can report success after no-op, stale evidence, or swallowed failure
3. CI and validation surfaces that currently over-signal confidence
4. persistence/telemetry sinks that can interfere with transactions or lose operator evidence
5. governance docs/scripts that can resurrect stale queues or final-looking unaudited documents

The best next maintenance wave should not be a new feature. It should be an authority and verification-hardening wave.

## Ranked Findings

### P0. Critical/blocking validation can remain advisory-only

Severity: high

Why it matters:

- Workspace governance says death-state violations are hard REJECT semantics.
- Live validation has paths where blocking failures become advisory feedback or warnings, not necessarily mechanical rejection.
- This creates a mismatch between the absolute invariant and runtime enforcement.

Evidence:

- `modules/validation/validation_orchestrator.py:524` forwards blocking failures as Director advisory.
- `modules/validation/validation_orchestrator.py:784` applies a capped advisory penalty.
- `modules/validation/validation_orchestrator.py:809` can still produce `PASS` or `CONDITIONAL_PASS` by score.
- `modules/core/stage4_interview_round.py:5967` appends BlockingValidator failures into warning/focus surfaces.
- `modules/core/stage4_interview_round.py:3788` strong-advisory keys do not include a structured blocking-critical key.
- `modules/core/stage3_orchestrator.py:2124` and `:2161` show Stage3 has a stronger Python precheck override path, so Stage3/Stage4 semantics are inconsistent.

Side effects:

- A dead/deceased/destroyed entity violation can depend on prompt text and Director interpretation instead of a uniform hard gate.
- Missing or degraded `state_tracker` can weaken Stage4 behavior because Stage4 accepts a nullable tracker path.

Recommended next action:

- Create a focused execution SSOT for `blocking-critical-authority-gate`.
- Define one cross-stage contract: structured detection is suspected evidence, Director remains the only `PASS` / `REJECT` authority, and Python must never hard-veto a Director verdict.
- Add regression where Director returns PASS despite a CRITICAL blocking failure and runtime must not accept plain PASS.

### P1. OneStop/Stage4 can report completion after Stage4 no-op or swallowed failure

Severity: high

Why it matters:

- The system can look complete to operators even when Stage4 produced no valid manuscript progress.
- This is the same family as the settlement authority issue, but one layer higher: run-level completion truth.

Evidence:

- `main_a.py:4694` calls Stage4 in the OneStop path.
- `main_a.py:4697` logs success.
- `main_a.py:4701` catches Stage4 exception as best-effort.
- `main_a.py:4705` still returns `status="completed"`.
- `modules/core/stage4_orchestrator.py:1263` and `:1642` can break on missing blueprint/no input.
- `modules/core/stage4_orchestrator.py:2806` can still emit `stage4_complete` from the outer Stage4 runtime surface.

Side effects:

- Operator UI, benchmark records, or canary summaries can show green after no-op or partial progress.
- Later stages may trust gaps as completed work.

Recommended next action:

- Create a `stage-run-result-authority` execution SSOT.
- Introduce or normalize a `StageRunResult` contract with statuses such as `completed`, `blocked`, `no_progress`, `missing_input`, `runtime_error`, `operator_stopped`.
- Make OneStop and Stage4 direct-supervised runners consume that status instead of success logs or stale audit tags.

### P1. CI gives broad false confidence

Severity: high

Why it matters:

- Recent PR CI went green, but the workflow did not run the Stage4 tests that validated the actual change.
- This is not merely incomplete coverage; it can mislead us into believing authority surfaces are protected.

Evidence:

- `.github/workflows/test.yml:40` runs a focused PR gate list.
- The focused list includes Stage2-heavy tests but does not include `tests/test_stage4_post_processor.py`, `tests/test_stage4_orchestrator.py`, or the JS desktop tests.
- `geuldobi-desktop/package.json:13` lists desktop JS tests that GitHub CI does not run.
- `.github/workflows/test.yml:113` and `:117` run `black` and `isort` checks with `|| true`, so those steps cannot fail CI.
- `.github/workflows/test.yml:137` syntax-check compiles only selected top-level globs, leaving several module subtrees outside direct syntax coverage.

Side effects:

- Regression gates can pass while Stage4, desktop, runner, property, e2e, or chaos surfaces are broken.
- Coverage upload is based on a partial subset and can overstate PR confidence.

Recommended next action:

- Add tiered CI jobs:
  - contract-safe governance/tests
  - Stage4 authority shard
  - runner/canary contract shard
  - desktop JS contract shard
  - recursive syntax/compileall shard
- Keep full suite memory-conservative and scheduled if too expensive for every PR.

### P1. Stage4 direct-supervised can false-pass from stale runtime audit state

Severity: high

Why it matters:

- Direct-supervised runners are used for operational proof and benchmark/canary-like evidence.
- If stale `runtime_audit_summary.json` can mark a new run complete, archived proof becomes unreliable.

Evidence:

- `scripts/run_stage4_direct_supervised.py:74` treats `after_latest_ep >= target_ep or runtime_audit_tag == "stage4_complete"` as success.
- `scripts/run_stage4_direct_supervised_guarded.py:213` has the same fallback shape.
- These scripts write result summaries used by benchmark/archive helpers.

Side effects:

- A previous `stage4_complete` can make a new partial run appear successful.
- Benchmark or operator evidence can become stale-authority proof.

Recommended next action:

- Require run-scoped session ID, mtime, or post-launch audit evidence.
- Add regression: `after_latest_ep < target_ep` plus stale `stage4_complete` must fail.

### P1. Telemetry writes can prematurely commit outer DB transactions

Severity: high

Why it matters:

- Telemetry sinks are supposed to be companion evidence, not transaction authorities.
- A telemetry write inside a business transaction should not commit unrelated pending business data.

Evidence:

- `modules/core/db_manager.py:3212` unconditionally commits in `save_llm_call`.
- `modules/core/db_manager.py:3266` unconditionally commits in `save_context_cache_attempt`.
- `modules/core/db_manager.py:3321` and `:3468` show `save_stage_attempt` and `save_ui_event` already respect nested transaction state.

Side effects:

- A later rollback can become partial because telemetry committed the transaction early.
- Runtime evidence can mutate business persistence boundaries.

Recommended next action:

- Add nested transaction guards to telemetry writes.
- Add rollback regression tests that place telemetry calls inside an outer transaction.

### P1. Operator `/stop` can leave stale prompt state

Severity: high for operator reliability, medium for data integrity

Why it matters:

- PromptBroker state is cleaned on normal process exit, but `/stop` bypasses the normal `_on_exit` callback path.
- Stale prompts can survive invisibly and confuse resume/status behavior.

Evidence:

- `modules/api/bridge_server.py:2415` cleans broker state in `_on_exit`.
- `modules/api/bridge_server.py:2518` `/stop` calls `runner.stop()` and broadcasts `run_stopped`.
- `modules/api/process_runner.py:439` cancels the read task during stop.
- No equivalent `broker.cleanup_run(run_id)` call is present in `/stop`.

Side effects:

- Pending prompt records can remain after stop.
- UI status may resurface stale prompt expectations.

Recommended next action:

- Add prompt cleanup on `/stop`.
- Add regression for stop-during-prompt.

### P2. Localhost control plane has no per-launch auth token

Severity: medium-high

Why it matters:

- The bridge binds to localhost, but any local process can call `/run`, `/stop`, and `/events`.
- Risk gates protect dangerous keys, but non-risk run/stop/log subscription still lacks a session boundary.

Evidence:

- `geuldobi-desktop/src/main.js:722` bridge fetch sends JSON headers only.
- `modules/api/bridge_server.py:2375` accepts `/run` without a per-launch token.
- `modules/api/bridge_server.py:2673` exposes WebSocket events without auth.

Side effects:

- A local process could start/stop non-risk runs or subscribe to logs.

Recommended next action:

- Generate a per-launch token in Electron.
- Pass it to backend env.
- Require it on HTTP and WebSocket routes, with tests for missing/wrong token.

### P2. Strong advisory escalation depends on text-marker parsing

Severity: medium-high

Why it matters:

- Binding gate behavior should not depend on exact rendered Korean/English headers.
- Text marker drift can silently weaken enforcement while preserving human-visible warnings.

Evidence:

- `modules/core/stage4_director_runtime.py:1323` infers advisory summaries via substring scans like `[TruthGate`, `[LM-B]`, and `Flashback`.
- `modules/core/stage4_interview_round.py:3791` uses that summary for binding escalation.
- `tests/test_stage4_interview_round.py:8214` codifies marker-style summaries.

Side effects:

- Header rename, translation, or formatter change can drop a hard-ish advisory gate.

Recommended next action:

- Pass structured advisory objects with `kind`, `severity`, and `binding`.
- Render display text separately from binding semantics.

### P2. Governance automation can write final human-facing docs without LLM 3-pass promotion

Severity: medium-high

Why it matters:

- Workspace policy says Python collects; LLM judges and finalizes human-facing docs.
- Some scripts can produce final-looking docs directly.

Evidence:

- `AGENTS.md:104` and `docs/implementation/document-3pass-audit-harness.md:35` require draft -> pass1 -> pass2 -> pass3 -> final save.
- `scripts/run_stale_reference_sweep.py:60` and `:95` write final findings/summary docs directly.
- `scripts/populate_process_health_scorecard.py:125` and `:141` computes health/action judgments and writes `Status: final`.

Side effects:

- Process docs can look authoritative without LLM audit.
- The “Python collects only” contract weakens.

Recommended next action:

- Default generated human-facing docs to `Status: draft`.
- Add `--write-final` only for already audited input, or split raw evidence from final interpretation.

### P2. Stale governance references and temp return anchors can resurrect dead work

Severity: medium

Why it matters:

- The current active queue is empty, but stale temp notes still point to missing queue authorities.
- Active docs advertise missing scripts.

Evidence:

- `docs/temp/our-usual-work-return-anchor-note.md:18` points to `docs/temp/queue-state.json`, a missing roadmap, and a missing temp execution SSOT.
- `docs/temp/our-usual-work-return-anchor-note.md:29` claims an active `system-maturity-next-band-wave1` item.
- `AGENTS.md:187` and `docs/implementation/evidence-manifest-harness.md:8` advertise missing `scripts/generate_evidence_manifest.py`.
- `scripts/README.md:19` advertises missing `generate_tr_bibles.py`.
- `scripts/process_and_audit_tr_bi_loop.py:68` calls missing `generate_tr_bibles.py`.

Side effects:

- “우리 원래 하던 거” style resume phrases can re-open nonexistent work.
- Operators can follow dead commands.

Recommended next action:

- Archive/delete stale temp return anchor or replace it with a current init-harness pointer.
- Restore missing scripts or update references.
- Add an active-doc broken-reference checker.

### P2. Prompt/config surfaces can silently degrade

Severity: medium

Why it matters:

- Prompt and provider contracts are core runtime behavior.
- Silent fallback means a prompt or model config can degrade without a hard operator signal.

Evidence:

- `modules/core/prompt_loader.py:11` preserves missing keys via `SafeDict`.
- `modules/core/prompt_loader.py:161` returns the original template on formatting failure.
- `tests/test_prompt_loader.py:147` expects unresolved placeholders to remain.
- `modules/domain/agents/chief_writer_prompts.py:11` uses empty fallback for required Chief Writer prompt sections.
- `modules/core/models_config.py:60` swallows model YAML load errors and returns `{}`.

Side effects:

- Literal `{placeholder}` or missing common rules can reach the LLM.
- Malformed model config can fall back quietly.

Recommended next action:

- Add strict required-variable contracts for production prompt keys.
- Make core Chief Writer sections fail closed or emit operator-visible degraded prompt status.
- Report model YAML parse/load failures in config health summaries.

### P2. FactLedger degraded load can be overwritten by empty save

Severity: medium

Why it matters:

- FactLedger is canonical memory/state substrate.
- A transient DB/read failure should not become canonical fact loss.

Evidence:

- `modules/core/fact_ledger.py:199` load failure sets degraded and returns an empty ledger.
- `modules/core/fact_ledger.py:235` `save()` writes current ledger unconditionally.
- `tests/test_fact_ledger.py:249` checks degraded state but not save-block behavior.

Side effects:

- A later save can persist empty degraded state over real facts.

Recommended next action:

- Block save while degraded unless explicit recovery succeeded.
- Add `no_save_on_degraded_load` regression.

### P3. Owner pressure remains a regression seam

Severity: medium

Evidence from AST inventory:

- `Stage4InterviewRound`: 181 direct methods
- `SovereignApp`: 178 direct methods
- `DBManager`: 143 direct methods
- `Stage4Orchestrator`: 71 direct methods
- `Stage4ContextBuilder`: 70 direct methods
- `Stage4PostProcessor.process_pass_result`: 179 LOC after formatting, one line below the `180+` high-risk band

Recommended next action:

- Avoid adding same-owner helpers in these classes.
- Prefer module-boundary extraction around:
  - stage run result contracts
  - blocking critical gate semantics
  - bridge lifecycle/status
  - DB telemetry transaction boundaries

## Suggested Execution Order

1. `blocking-critical-authority-gate` execution SSOT
   - Highest semantic risk because it touches absolute invariants.
   - Needs careful design to preserve Director sovereignty while preventing plain PASS on critical violations.

2. `stage-run-result-authority` execution SSOT
   - Covers OneStop false completion, Stage4 direct-supervised stale audit false-pass, and run lifecycle truth.
   - Should define a shared result/status contract before patching.

3. `ci-tiered-regression-gate` execution SSOT
   - Prevents future false confidence.
   - Should add Stage4 authority tests, runner-contract tests, desktop JS tests, and recursive syntax compile.

4. `db-telemetry-transaction-boundary` execution SSOT
   - Small, high-value persistence hardening.
   - Likely suitable for a compact focused patch after execution doc validation.

5. `operator-bridge-stop-and-lifecycle` execution SSOT
   - Prompt cleanup is small.
   - Lifecycle durability and localhost token are broader and should be split if needed.

6. `governance-stale-reference-and-final-doc-automation` execution SSOT
   - Prevents stale queue resurrection and unaudited final docs.
   - Strong ROI, but less runtime-critical than P0/P1 code authority.

## Areas That Look Healthy

- Stage4 PASS settlement is now materially stronger:
  - primary DB transaction
  - settlement packet
  - human-facing txt export
  - `stage4_pass_settlement_status`
  - non-visible `ui_events` structured status when DB telemetry is available
- Session memory envelope handling is JSON-safe, deep-copied, and covered by focused tests.
- Legacy desktop shims are clean compatibility wrappers.
- Electron windows use `contextIsolation: true` and `nodeIntegration: false`.
- `ops_validator.py --strict` reports no active temp execution queue.
- UTF-8 hygiene enforcement is strong enough for normal touched-file workflows, though allow-marker rationale enforcement can improve.

## Survey Uncertainties

- No live runtime replay was performed.
- No full pytest suite or canary was run.
- Some findings are based on static control-flow and may need focused current-state re-audit before implementation.
- CI coverage counts are approximate from file inventory and workflow inspection, not from an executed coverage report.

## Document 3-Pass Audit

Pass 1 - Structure and scope:

- This is a system-track survey synthesis, not an execution SSOT.
- Canonical path is explicit.
- Temp mirror is marked not applicable.
- Scope, non-goals, source inputs, and uncertainties are explicit.

Pass 2 - Evidence and consistency:

- High-priority claims cite live code paths or active docs.
- Findings are grouped by operational meaning rather than by source lane.
- The survey does not claim live-run proof.
- The survey does not open temp queue state.
- The prior Stage4 settlement change is recognized as healthy rather than re-opened.

Pass 3 - Actionability and readability:

- Findings include severity, reason, side effects, and recommended next action.
- Suggested execution order is explicit.
- The top candidates are execution-document ready but not automatically queued.
- Guardrails preserve survey-only mode.

Estimated confidence:

- Survey synthesis confidence: `95%`

Confidence limits:

- confidence is high for prioritization and next-wave selection
- confidence is not a substitute for a focused execution SSOT re-audit before patching
