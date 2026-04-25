# Codebase Parallel Memory Persistence Telemetry Deep Dive Wave3 Synthesis

Date: 2026-04-25
Status: final-survey
Canonical Path: `docs/2026-04-25/codebase-parallel-memory-persistence-telemetry-deep-dive-wave3-synthesis.md`
Temp Mirror Path: not applicable; survey-only output, no execution queue opened

Commit State:

- Baseline Commit: `d354e57a5c6e57cf3026350e27c3edc9909f28f4`
- Baseline Dirty Summary: `clean`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

Source Inputs:

- `AGENTS.md`
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/document-3pass-audit-harness.md`
- `docs/2026-04-23/stage234-session-memory-max-utilization-execution-ssot.md`
- `docs/2026-04-25/stage234-session-memory-resume-context.md`
- `docs/2026-04-25/codebase-parallel-maintenance-deep-dive-wave2-synthesis.md`
- five read-only parallel explorer lanes:
  - session memory / context cache
  - DB telemetry transaction boundaries
  - FactLedger / memory-bank truth substrate
  - runtime audit / operator evidence sinks
  - tests / CI coverage
- local source re-checks on the highest-risk findings

Scope:

- This is a system-track maintenance deep dive.
- This is not a feature-design document.
- No code was patched.
- No temp execution SSOT mirror was created.
- No live run, canary, or pytest shard was executed.

## Executive Synthesis

The workspace is ready to continue work on latest `main`, and PR #28 is merged. The prior S2/S3/S4 session-memory lane is closed and materially present in code, but this deeper pass found that the next reliability risks are not "more memory" features. They are proof and persistence seams around the memory substrate:

1. truth stores can report save success too optimistically
2. telemetry sinks can break outer DB transactions
3. Stage4 pass-rate evidence may be silently dropped by the new session-memory envelope payload
4. operator evidence is still truncated or stale in several companion surfaces
5. CI protects smoke coverage, not the full memory/persistence/telemetry reliability net

This wave confirms the user's governance concern: Python evidence should stay evidence. The critical follow-up is not to let Python telemetry, regex-like probes, or companion summaries become hidden authorities or silently corrupt the Director/fact-ledger truth path.

## Ranked Findings

### P0. FactLedger / WorldState persistence can falsely appear successful

Severity: critical for truth-store integrity

Why it matters:

FactLedger and WorldState are canonical memory/truth substrates. If their save path reports success after `DBManager.save_anchor()` returns `False`, Stage4 post-pass code can treat failed persistence as acceptable. A corrupt or unreadable anchor can also collapse into an empty ledger and later be saved over the real fact state.

Evidence:

- `modules/core/db_manager.py:1128` returns `False` on `save_anchor` failure.
- `modules/core/fact_ledger.py:235` calls `self.db.save_anchor(...)` but does not check the boolean result.
- `modules/core/world_state.py:176` has the same success-assumption shape.
- `modules/core/db_manager.py:1132` returns `{}` for missing and corrupt anchor JSON, so callers cannot distinguish "absent" from "degraded/corrupt".
- `modules/core/fact_ledger.py:199` treats falsey load as non-degraded empty ledger.
- `main_a.py:3946` logs FactLedger as new based on `last_updated_ep`.

Side effects:

- prompt fact memory can silently reset
- Stage4 post-pass can log or proceed as if WorldState/FactLedger persisted
- later save can overwrite an authoritative anchor with an empty reconstructed ledger

Recommended next action:

- Open a focused `fact-ledger-worldstate-save-integrity` execution SSOT.
- Patch `FactLedger.save()` and `WorldState.save()` to propagate `False`.
- Distinguish missing anchor from corrupt/degraded anchor before allowing save.
- Add regression tests for `save_anchor=False`, corrupt anchor load, and no-save-on-degraded-load.

### P0. Stage4 pass-rate evidence can be silently dropped by session-memory envelope payload

Severity: critical for observability/proof integrity

Why it matters:

The new Stage4 session-memory envelope is correctly attached to DB advisory flags, but the pass-rate monitor payload projection also exposes `session_memory_envelope` at top level. `PassRateMonitor.record_attempt()` does not accept that keyword. The call is wrapped in a broad exception handler, so Stage4 can continue while `pass_rate_monitor.json` loses the attempt evidence.

Evidence:

- `modules/core/stage4_interview_round.py:8518` attaches the session-memory envelope.
- `modules/core/stage4_interview_round.py:8564` expands `_build_stage4_attempt_contract_projection(...)` into the pass-rate payload.
- `modules/core/stage4_interview_round.py:8757` calls `pass_rate_monitor.record_attempt(**payload)`.
- `modules/core/pass_rate_monitor.py:276` defines `record_attempt(...)` without `session_memory_envelope`.

Side effects:

- Stage4 attempts can disappear from pass-rate monitor proof.
- benchmark/canary evidence can become thinner without an operator-visible error.
- the DB advisory path still persists the envelope, so the bug can hide behind a healthy DB sink.

Recommended next action:

- Hotfix the payload contract before opening broader memory work.
- Either keep `session_memory_envelope` inside `advisory_flags` only or teach `PassRateMonitor` to accept explicit metadata.
- Add an integration regression that calls the real `record_attempt(**payload)` path with an envelope.

### P1. DB telemetry writes can commit unrelated outer transactions

Severity: high

Why it matters:

Telemetry should be companion evidence. It must not decide transaction boundaries for business or truth-store writes. Two telemetry sinks still call `commit()` unconditionally.

Evidence:

- `modules/core/db_manager.py:3212` unconditionally commits in `save_llm_call`.
- `modules/core/db_manager.py:3266` unconditionally commits in `save_context_cache_attempt`.
- `modules/core/db_manager.py:3370` shows `save_stage_attempt` already uses a nested transaction guard.
- `modules/core/db_manager.py:3497` shows `save_ui_event` already uses a nested transaction guard.
- `modules/core/stage4_post_processor.py:1023` commits any pending transaction before its own primary DB transaction.
- `modules/core/db_manager.py:1201` unconditionally commits in `upsert_canonical_fact`.

Side effects:

- later rollback can become partial
- telemetry can persist business/truth data prematurely
- canonical facts can escape Stage4's expected atomic WorldState/FactLedger transaction

Recommended next action:

- Open `db-telemetry-transaction-boundary` after the P0 proof hotfix, or combine it with the truth-store execution SSOT if the patch is small.
- Convert LLM/cache telemetry to the same nested-guard pattern as `save_stage_attempt` and `save_ui_event`.
- Make `upsert_canonical_fact()` transaction-aware.
- Replace Stage4 pre-commit with an explicit transaction-owner policy.

### P1. DB `TEXT` operator evidence is still truncated by Python

Severity: high

Why it matters:

Workspace policy says DB `TEXT` diagnostic and judgment fields should not be Python-truncated. `ui_events.message` is a durable operator evidence sink, but Python stores only `message[:4000]`.

Evidence:

- `modules/core/db_manager.py:3434` defines `save_ui_event`.
- `modules/core/db_manager.py:3489` stores `str(message or "")[:4000]`.
- `modules/core/db_bootstrap_runtime.py:578` defines `ui_events.message` as `TEXT`.

Side effects:

- long Director thinking or operator-facing rationale can appear in console but not survive in DB
- later audit can lack the exact displayed evidence

Recommended next action:

- Remove DB-layer truncation.
- Keep compaction only in UI/dashboard read paths.
- Add a long-message regression for `ui_events.message`.

### P1. Runtime evidence remains partly stale or project-scoped instead of run-scoped

Severity: high for benchmark/canary proof

Why it matters:

PR #28 fixed the direct-supervised false-success condition, but several downstream evidence surfaces can still mix old and new proof or show old summaries as available.

Evidence:

- `scripts/archive_benchmark_record.py:168` collects project-level stage metrics.
- `scripts/archive_benchmark_record.py:194` stores `runtime_audit_tag` from the latest summary without run freshness checks.
- `modules/api/bridge_server.py:2093` loads `runtime_audit_summary.json` when the file exists.
- `modules/core/stage4_canary_tools.py:986` reads `runtime_audit_summary.json` as a companion signal.
- `modules/core/services/audit_service.py:818` includes only a compact recent event window in the summary.

Side effects:

- long-lived project logs can leak old pass/cost/episode data into new benchmark records
- dashboard can expose a stale summary as available after a failed or interrupted run
- operators can over-trust companion snapshots even though durable authority lives in DB/JSONL/artifacts

Recommended next action:

- Add run/session freshness metadata to runtime summaries and dashboard loaders.
- Scope benchmark stage metrics by session id, launch baseline, or explicit run id.
- Add `summary_window` and `event_window_truncated` disclosure to compact summaries.

### P2. Stage4 Director vector memory is not in the initial Director decision prompt

Severity: medium

Why it matters:

This is not necessarily a bug, but it is an important design fact. Stage4 Director vector memory is collected and used in post-select continuity/history checks, but it does not appear to feed the first Director review decision. If the intended contract is "S4 memory affects Director selection/REJECT immediately", the implementation is incomplete.

Evidence:

- `modules/core/stage4_director_runtime.py:184` collects director memory context.
- `modules/core/stage4_director_runtime.py:635` returns pre-validation output.
- `modules/core/stage4_postselect_runtime.py:496` uses director memory after positive selection.
- `modules/domain/agents/director_continuity.py:688` contains the continuity use path.

Side effects:

- first Director pass/reject can ignore SC-5 memory context
- memory evidence may be visible in later checks but not where operators expect it

Recommended next action:

- Make an explicit Director-sovereignty design call:
  - either keep this post-select only and document it
  - or inject a bounded memory summary into the first Director decision packet

### P2. Context cache stale-hit and lineage gaps remain

Severity: medium

Why it matters:

Context cache is a performance/proof substrate, not an authority. Still, stale cache names and disconnected telemetry can create confusing proof.

Evidence:

- `modules/domain/agents/base_agent.py:2268` hashes content for cache keying.
- `modules/domain/agents/base_agent.py:2280` reuses cached name during TTL.
- `modules/domain/agents/base_agent.py:2374` falls back after cache creation failure.
- `modules/domain/agents/base_agent.py:2426` falls back to direct `ask()` when no cache name exists.
- `modules/domain/agents/base_agent.py:2448` uses `cached_content` for cached LLM calls.
- `modules/core/db_bootstrap_runtime.py:419` creates `llm_calls`.
- `modules/core/db_bootstrap_runtime.py:475` creates `context_cache_attempts`.

Side effects:

- cached-content failure can repeat until TTL expiry if stale entries are not evicted
- `llm_calls` and `context_cache_attempts` require inference joins instead of direct cache lineage
- a Python-only continuity path can create cache attempts that are not actual LLM cached-context usage

Recommended next action:

- Evict cache key on cached-content call failure.
- Add cache lineage fields or a joinable cache attempt id.
- Separate "cache created for Python analysis" from "cached_content used in LLM call" in telemetry.

### P2. CI protects smoke confidence, not the full reliability net

Severity: medium-high

Why it matters:

The current CI passed PR #28, but the reliability surfaces in this survey are broader than the focused PR gate.

Evidence:

- `.github/workflows/test.yml:40` runs raw `pytest -v` on a fixed focused list.
- `.github/workflows/test.yml:82` makes Codecov non-blocking.
- `scripts/run_pytest_lowmem.py` exists but is not exercised by the workflow.
- tests exist for DB recovery, rollback, process runner, telemetry propagation, session logger, desktop JS contracts, and cache runtime behavior, but many are outside CI.

Side effects:

- future memory/persistence regressions can merge with green CI
- desktop and low-memory runner guarantees remain local-only

Recommended next action:

- Add a required reliability shard using the low-memory runner.
- Add a desktop Node contract job.
- Promote rollback/recovery and telemetry/logging tests into CI.

## Healthy Boundaries Confirmed

- Local `main` is current at merge commit `d354e57a5c6e57cf3026350e27c3edc9909f28f4`.
- No active system execution queue exists in `docs/temp/`.
- PR #28 fixed Stage4 direct-supervised stale `stage4_complete` fallback success.
- S2 memory reaches Arc ensemble through `s2_vector_ctx` / `vector_context`.
- S3 memory reaches Blueprint generation through semantic context, budget arbitration, and observability flags.
- Stage4 session-memory envelope is provider-neutral and persisted into DB `stage_attempts.advisory_flags`.
- Provider-native Sessions, Live API, and Memory Bank remain deferred sidecars, not authoritative state.

## Suggested Execution Order

1. `stage4-pass-rate-session-envelope-contract`
   - Hotfix the apparent new observability regression.
   - Small surface, high confidence, likely fastest safety win.

2. `fact-ledger-worldstate-save-integrity`
   - Protect the truth-store substrate from false success and degraded empty overwrite.
   - Include `canonical_facts` transaction awareness if scope stays bounded.

3. `db-telemetry-transaction-boundary`
   - Normalize `save_llm_call`, `save_context_cache_attempt`, `save_attempt_raw_rationale`, and related rollback cleanup.
   - Revisit Stage4 primary DB pending transaction policy.

4. `operator-evidence-full-retention`
   - Remove Python-side DB `TEXT` truncation for `ui_events`.
   - Add read-side compaction only.

5. `runtime-evidence-run-scope-freshness`
   - Add run/session freshness to summaries, dashboard, benchmark archive, and canary proof.

6. `ci-reliability-gate`
   - Add low-memory reliability shard and desktop JS contract job.

7. `stage4-director-memory-design`
   - Decide whether S4 Director memory is post-select only or belongs in the initial Director decision packet.

## Non-Goals

- No provider-native memory migration is recommended from this survey.
- No Python rule should become the final PASS/REJECT judge.
- No regex or telemetry sink should outrank Director, FactLedger, WorldState, DB attempt truth, or artifact truth.

## Document 3-Pass Audit

Pass 1 - Structure and scope:

- The document is a survey synthesis, not an execution SSOT.
- Canonical path is explicit.
- Temp mirror is marked not applicable.
- Scope, non-goals, source inputs, and execution order are explicit.

Pass 2 - Evidence and consistency:

- High-priority claims cite live source paths and line anchors inspected on current `main`.
- Findings separate authority, persistence, telemetry, operator evidence, and CI coverage.
- The document does not claim live-run proof.
- The document preserves Director sovereignty and Python-as-evidence governance.

Pass 3 - Actionability and readability:

- Each finding includes severity, why it matters, evidence, side effects, and next action.
- Suggested execution order is explicit and bounded.
- No implementation queue was opened without a dedicated execution SSOT.

Estimated confidence:

- Survey synthesis confidence: `95%`

Confidence limits:

- Confidence is high for prioritization and execution-doc selection.
- Confidence is not a substitute for a focused execution SSOT re-audit before patching.
- No live canary or full pytest run was executed in this survey wave.
