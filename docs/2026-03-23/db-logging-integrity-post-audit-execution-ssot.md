# DB Logging Integrity Max-Retention Execution SSOT

Date: 2026-03-23
Status: execution-ready
Canonical Path: `docs/2026-03-23/db-logging-integrity-post-audit-execution-ssot.md`
Temp Mirror Path: `docs/temp/db-logging-integrity-post-audit-execution-ssot.md`
Commit State:
- Baseline Commit: `a3b9a286`
- Baseline Dirty Summary: `dirty: pre-existing prompt/doc/runtime edits plus new 2026-03-23 survey artifacts`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-23/opus/db-logging-integrity-audit.md`
Evidence Artifacts:
- `live code inspection only; no separate evidence manifest`
Side-Effect Coverage: covered

## 1. Intent
- Reframe DB logging integrity around a temporary but explicit `max-retention` policy.
- Preserve as much runtime evidence as possible during the current transition phase so operator, audit, and future refactor work can answer who decided what, why, and with which raw inputs.
- Treat later pruning, normalization, or archival as a separate cleanup phase after the system stabilizes.

## 2. Baseline Facts
- SQLite `TEXT` columns are not the limiting factor in the currently observed losses. The main losses come from Python-side truncation and from payloads never entering a persistence sink.
- The survey's truncation claims are directionally correct in live code:
  - `llm_calls.error_msg[:80]`
  - `llm_calls.thinking_snippet[:5000]`
  - multiple `[:500]` rationale fields in `director_selections` and `stage_attempts`
- The survey's `error_category` claim is materially correct but mechanically imprecise:
  - Stage 4 keeps `error_category` in runtime flow and pass-rate telemetry
  - the DB attempt path loses it because `Stage4InterviewRound._build_stage4_db_attempt_payload()` omits it before `save_stage_attempt()` is called
  - the existing DB contract already supports `failure_category`, so the short-term fix path is available
- High-loss areas are not limited to simple truncation:
  - full Director thinking is not durably persisted
  - raw advisory `structured_warnings` are summarized but not durably preserved
  - ensemble comparison reasoning is compressed into shorter rationale fields
  - attempt-level breakdowns and patch context remain partially buried or absent from query-friendly sinks

## 3. Operating Policy
- During the current transition phase, default policy is `store as much as practical`.
- For DB-bound text fields backed by `TEXT`, do not truncate in Python unless a field is explicitly designated as a bounded operator label or key.
- For large runtime payloads, store both:
  - a query-friendly summary surface
  - a raw or near-raw adjunct surface
- Prefer forward-only retention upgrades over immediate cleanup, pruning, or storage optimization.
- If two sinks exist, summary and raw should both survive unless there is a specific, documented safety reason not to do so.

## 4. Scope
Included:
- `modules/core/db_manager.py`
- `modules/core/db_bootstrap_runtime.py`
- `modules/protocols/db_repository.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_director_runtime.py`
- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage2_finalizer.py`
- `modules/domain/agents/director_ensemble.py`
- targeted tests for DB logging and Stage 3/4 persistence surfaces

Excluded:
- verdict policy changes
- retry policy changes
- prompt content changes
- pruning, compression, archival, or cleanup of retained data
- backfill of historical rows unless implementation proves it is low-risk and explicitly worth doing

## 5. Pass 1. Inventory Summary
- Current losses split into two classes.

Class A. Python truncation against `TEXT` targets:
- `llm_calls.error_msg[:80]`
- `llm_calls.thinking_snippet[:5000]`
- `stage_attempts.reject_reason[:500]`
- `stage_attempts.selection_reason[:500]`
- `stage_attempts.verdict_reason[:500]`
- `stage_attempts.open_review[:500]`
- `stage_attempts.fix_scope_reasoning[:500]`
- `stage_attempts.runtime_advisory[:500]`
- `stage_attempts.retry_directives[:500]`
- equivalent rationale truncations in `director_selections`

Class B. Data never reaches a durable DB sink:
- full Director thinking
- full or structured advisory warnings
- full ensemble comparison reasoning
- Stage 4 failure category on attempt rows
- per-attempt score breakdown in DB
- initial vs final verdict split where firewall rewrites outcome
- patch context fields that are currently query-hostile or submerged in generic blobs

## 6. Pass 2. Semantic Classification
- Class A. Immediate max-retention policy flips
  - remove Python truncation for `TEXT`-backed diagnostic/rationale fields
- Class B. Existing-contract enrichment
  - map already-available runtime fields into existing DB fields where the contract already allows it
  - example: Stage 4 `error_category -> failure_category`
- Class C. Dual-write retention expansion
  - keep compact/query surfaces while adding raw adjunct persistence for large payloads
- Class D. New schema / bounded runtime-module work
  - introduce new retention tables or columns for raw payload families that do not fit current sinks

## 7. Side-Effect Map
- file writes / artifacts:
  - not primary scope
- DB / schema / transaction boundaries:
  - primary scope
  - expected to touch insert/update contracts, bootstrap schema, and read-side tests
- JSONL / log / audit sinks:
  - existing sinks remain; DB becomes less lossy, not less verbose
- console / UI / operator output:
  - no required change, but new retention should make console-only evidence less authoritative
- rollback / recovery / retry:
  - must remain behaviorally unchanged
- cache / global state:
  - not primary scope
- bootstrap fallback / config-env mutation:
  - schema changes, if any, must route through existing bootstrap/migration authority

## 8. Realization Architecture
- Use a two-layer retention model.

Layer 1. Query-friendly summary rows
- existing `stage_attempts`
- existing `director_selections`
- existing `llm_calls`
- preserve or extend these so operators can query by verdict, failure category, stage, attempt, patch status, and other compact dimensions

Layer 2. Raw or near-raw adjunct retention
- add dedicated retention surfaces for large blobs that do not fit cleanly in the summary tables
- target payload families:
  - Director thinking
  - advisory structured warnings
  - ensemble comparison rationale
  - per-attempt score breakdown and patch context when summary columns are insufficient

Design rule:
- summary rows answer `what happened`
- adjunct rows answer `why it happened`

## 9. Execution Tranches
1. Policy flip tranche: remove lossy truncation where DB `TEXT` already exists
   - eliminate Python truncation for diagnostic and rationale text unless the field is intentionally bounded metadata
   - minimum starting targets:
     - `llm_calls.error_msg`
     - `llm_calls.thinking_snippet`
     - `stage_attempts` rationale fields
     - `director_selections` rationale fields
2. Existing-contract enrichment tranche
   - Stage 4 DB attempt payload must carry:
     - `failure_category` from `error_category`
   - preserve current pass-rate and summary paths
3. Queryable Stage 4 detail tranche
   - persist `initial_verdict`, `final_verdict`, `score_breakdown`, and patch-context fields in queryable form
   - if current tables cannot carry them cleanly, add bounded columns or a linked detail table
4. Raw rationale retention tranche
   - persist full Director thinking
   - persist full ensemble comparison reasoning
   - persist advisory structured warning payloads or a normalized raw bundle per attempt
5. Validator detail retention tranche
   - persist raw or near-raw outputs from:
     - pre-LLM validator
     - arc draft validator
     - constitutional checker
6. Verification and read-path tranche
   - add tests proving summary and raw sinks stay linked by attempt/session keys
   - confirm read surfaces can recover both compact and raw views without ambiguity

## 10. Acceptance Criteria
- Python truncation is removed for all in-scope `TEXT`-backed rationale/diagnostic fields unless a field is explicitly designated as bounded metadata
- Stage 4 attempt rows retain failure classification
- full Director thinking is durably recoverable from DB-linked retention
- raw advisory warning evidence is durably recoverable from DB-linked retention
- ensemble comparison reasoning is durably recoverable beyond a short 500-char summary
- compact query surfaces remain usable for operator queries
- no change to verdict logic, retry logic, or pass/fail authority

## 11. Verification Plan
- `python -m py_compile modules/core/db_manager.py modules/core/db_bootstrap_runtime.py modules/protocols/db_repository.py modules/core/stage4_interview_round.py modules/core/stage4_director_runtime.py modules/core/stage4_post_pass_runtime.py modules/core/stage3_orchestrator.py modules/core/stage2_finalizer.py modules/domain/agents/director_ensemble.py`
- targeted low-memory pytest shards covering:
  - DB logging persistence
  - Stage 3/4 attempt persistence
  - director selection persistence
  - bootstrap schema and migration coverage
  - read-path recovery for newly retained raw payloads
- fresh live path after implementation:
  - one Stage 3 lane
  - one Stage 4 lane
  - inspect both compact summary rows and raw adjunct payload retrieval
- `python scripts/check_utf8_hygiene.py docs/2026-03-23/db-logging-integrity-post-audit-execution-ssot.md docs/temp/db-logging-integrity-post-audit-execution-ssot.md`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py`

## 12. Guardrails
- Do not treat storage growth as a reason to reintroduce truncation during this transition-phase item.
- Do not bundle cleanup, archival, or compression into the same execution wave.
- Do not change authority, routing, verdict semantics, or retry semantics.
- Keep summary sinks and raw sinks linked by stable keys.
- If a raw payload is too large for an existing table shape, add an adjunct retention surface rather than silently trimming.
- If a field remains intentionally bounded, document why it is metadata rather than evidence.

## 13. Temp Queue Notes
- temp status: pending
- cleanup condition:
  - remove the temp mirror after realization and Codex closure
- roadmap dependency:
  - `docs/2026-03-23/max-retention-observability-execution-roadmap.md`

## 14. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 15. 3-Pass Audit Record
- Pass 1: re-scoped the document from low-blast bugfixes to explicit max-retention policy, per user instruction
- Pass 2: separated `truncation`, `existing-contract enrichment`, and `new adjunct retention` into distinct realization classes
- Pass 3: rechecked canonical/temp queue semantics, side-effect coverage, and the no-cleanup-during-transition rule

## 16. Confidence
- Estimated confidence: 96%
- Residual uncertainty:
  - exact schema shape for raw adjunct retention should be chosen during implementation Pass 1
  - historical backfill remains intentionally undecided
