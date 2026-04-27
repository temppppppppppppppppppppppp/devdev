# Issue #59 Stage4 Proof Digest And CoVe Advisory 10-Terminal Parallel Investigation Order

Date: 2026-04-27
Status: final - investigation order
GitHub Issue: `#59 [Stage4] Close proof-digest warn residues and CoVe advisory review`
GitHub URL: `https://github.com/temppppppppppppppppppppppp/devdev/issues/59`
Canonical Path: `docs/2026-04-27/issue-59-stage4-proof-digest-cove-advisory-10terminal-order.md`
Track: system order
Mode: survey / audit / order-pack only
Baseline Commit: `a3d826978d530ab61d3765e5e095890fa6533ea7`
Baseline Dirty Summary: dirty before this document was created: `docs/temp/queue-state.json` modified; existing untracked issue/security/temp investigation docs and directories present; no existing tracked code edits were touched by this order pack.
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Temp Queue Semantics: this is not an execution SSOT and is not mirrored into `docs/temp/`.

## Purpose

Create a 10-terminal parallel investigation order for Issue #59. The investigation target is the remaining Stage4 observability and authority residue around proof-digest `warn` status, selection/verdict/runtime advisory mismatch fields, rationale metadata gaps, and CoVe runtime advisory failures that appear after a preserved Director PASS.

This document is an order pack only. Terminals must not edit code, docs, DB, logs, benchmark records, or GitHub issues unless a later operator explicitly opens an implementation wave.

## Source Evidence

- GitHub Issue #59 says the remaining problem is Stage4 proof-digest mismatch fields, rationale metadata gaps, and CoVe runtime advisory failures after preserved Director PASS.
- `docs/2026-04-26/frontier-lag-5arc-post-run-merge-audit.md:148` says Stage4 runtime proof digest status is `warn` because selection/verdict/runtime advisory mismatch fields and rationale metadata gaps remain.
- `docs/2026-04-26/frontier-lag-5arc-post-run-merge-audit.md:237` recommends re-auditing Stage4 proof digest warnings separately.
- `docs/2026-04-27/auto-frontier-lag-5arc-runtime-analysis-ssot.md:38-39` still reports Stage3 and Stage4 current-session status as `warn`.
- `docs/2026-04-27/gcp-iam-5arc-live-run-handoff-current.md:122` says CoVe LLM runtime failures appeared after some PASSes while Stage4 preserved Director PASS.
- `docs/2026-04-27/gcp-iam-5arc-live-run-handoff-current.md:228` says the handoff does not treat Python advisory as quality judge.
- `modules/core/stage4_outcome_runtime.py:416-418` builds the CoVe runtime failure advisory and UI message that explicitly preserves Director PASS.
- `modules/core/stage4_outcome_runtime.py:492-504` handles CoVe fail-closed semantic rejection as a retry path, separate from runtime advisory failure.
- `modules/core/stage4_outcome_runtime.py:546-553` writes `STAGE4_COVE_RUNTIME_ADVISORY` with `director_pass_preserved=True`.
- `tests/test_stage4_orchestrator.py:1564-1618` pins that CoVe verify exceptions log advisory rows and preserve the PASS.
- `tests/test_failure_analyzer.py:3666-3675` pins clean Stage4 sink alignment when runtime advisory and rationale metadata agree.
- `tests/test_failure_analyzer.py:3738-3844` pins Stage4 runtime advisory and retry directive mismatch detection as `warn`.
- `modules/core/failure_analyzer.py:2423-2543` is the likely rationale mismatch and metadata gap collection surface.
- `modules/api/bridge_server.py:2073-2209` is the likely operator proof/status compaction surface.
- `scripts/backfill_benchmark_native_post_run_evidence.py:86-115`, `scripts/compare_benchmark_records.py:1570-1600`, and `scripts/report_benchmark_operator_lines.py:227-235` are benchmark/reporting consumers of proof digest and Stage4 live-session statuses.

## Global Rules For All 10 Terminals

- Read-only only. Do not modify files, run formatters, write temp docs, create commits, update DB rows, or update GitHub.
- Use UTF-8 reads. If console rendering looks broken, do not claim corruption from terminal output alone.
- Search with `rg` first, then inspect narrow files and line ranges.
- Keep findings bounded to inspected evidence. Mark evidence versus inference.
- Director PASS remains final narrative authority unless a later explicit policy changes that. Python advisory and runtime diagnostics must not mechanically overwrite Director judgment.
- Distinguish these four concepts in every report:
  - Director verdict or settled final authority row.
  - CoVe semantic fail-closed result that intentionally causes retry.
  - CoVe runtime failure advisory where PASS is preserved.
  - Proof digest or sink-alignment `warn` status as observability evidence.
- Runtime/advisory evidence must stay visible and typed for operators.
- Do not declare current 5-arc success or failure from stopped/provisional run evidence.
- Each terminal returns a compact report with:
  - `Finding Summary`
  - `Evidence`
  - `Risk / Gap`
  - `Suggested Contract Or Test`
  - `Implementation Owner Surface`
  - `Open Questions`

## Parallel Terminal Map

| Terminal | Lane | Primary Question |
| --- | --- | --- |
| T01 | Proof-digest producer and warn taxonomy | Where is Stage4 proof digest `warn` produced, and which fields actually drive the warning? |
| T02 | Settled DB and final authority truth | Do stage_attempts, director_selections, session decisions, and final artifact rows agree for Stage4 PASS/PASS_WITH_FIX attempts? |
| T03 | Rationale metadata and sink-alignment core | Are selection/verdict/runtime advisory/retry directive gaps real data gaps, expected companion absences, or analyzer false positives? |
| T04 | CoVe runtime advisory PASS-preserved path | Does a CoVe runtime exception remain typed as advisory after Director PASS across UI, log, JSONL, and audit_event sinks? |
| T05 | CoVe semantic fail-closed retry path | Which CoVe failure classes should be terminal/retry, and are they cleanly separated from runtime failure advisories? |
| T06 | Operator display and dashboard semantics | Could operators confuse proof-digest warn or CoVe runtime advisory with narrative failure, and where should labels improve? |
| T07 | Live-run evidence and current-session status | What exactly happened in the 2026-04-27 run, and which proof-digest warnings are current-session versus run-wide residue? |
| T08 | Benchmark and archive impact | Which benchmark/export/reporting fields should compare early-April versus current proof-digest warn and advisory rates? |
| T09 | Regression test gap design | What deterministic tests should pin #59 behavior before implementation? |
| T10 | Synthesis / implementation readiness | What minimal implementation tranches follow if the investigation confirms gaps? |

## Terminal Orders

### T01 - Proof-Digest Producer And Warn Taxonomy

Read targets:

- `modules/core/failure_analyzer.py`
- `modules/core/stage4_canary_tools.py`
- `scripts/run_auto_frontier_lag_harness.py`
- `scripts/run_stage34_canary.py`
- `docs/2026-04-26/frontier-lag-5arc-post-run-merge-audit.md:142-148`
- `docs/2026-04-26/frontier-lag-5arc-post-run-merge-audit.md:234-237`

Questions:

- Where is proof digest status computed or copied into runtime summaries?
- Which mismatch fields can turn Stage4 status to `warn`?
- Is `warn` a hard gate, soft diagnostic, or mixed concept in current code?
- Does current code distinguish run-wide proof digest from current-session sink alignment?

Return:

- A field-by-field warning taxonomy with file paths and line references.
- Whether each warning class is terminal, advisory, or display-only.
- Any ambiguity where code naming makes authority unclear.

### T02 - Settled DB And Final Authority Truth

Read targets:

- `modules/core/db_manager.py`
- `modules/core/failure_analyzer.py`
- `modules/core/stage4_director_runtime.py`
- `modules/core/stage4_outcome_runtime.py`
- Read-only DB schema or rows from `projects/01_골든카나리아/project_data.db` only if needed.
- `tests/test_failure_analyzer.py:3543-3844`

Questions:

- Which tables or rows are final authority for Stage4 verdict, score, selection reason, verdict reason, artifact path, content hash, runtime advisory, and retry directives?
- Do settled Director PASS rows get overwritten, shadowed, or contradicted by runtime advisory rows?
- Are DB rows missing rationale metadata, or are non-authority sinks being incorrectly treated as final sinks?
- What exact DB queries should a later implementation PR run read-only for proof?

Return:

- Authority-row map by field and table.
- Any real missing fields or mismatches observed in live or fixture evidence.
- Queries or fixtures needed for a later patch.

### T03 - Rationale Metadata And Sink-Alignment Core

Read targets:

- `modules/core/failure_analyzer.py`
- `tests/test_failure_analyzer.py`
- `modules/core/services/audit_service.py`
- `tests/test_audit_service.py`

Questions:

- How does sink alignment collect and compare `selection_reason`, `verdict_reason`, `comparison_notes`, `selected_candidate_advisory_struct`, `runtime_advisory`, and `retry_directives`?
- Which fields are required in final authority sinks versus companion/session/log sinks?
- Does the existing companion-missing-runtime-advisory test fully cover expected absences?
- Where could `rationale_metadata_missing` be overcounting advisory-only or companion-only cases?

Return:

- Analyzer decision tree for rationale metadata.
- Expected absence rules versus bug candidates.
- Tests that would fail if expected companion absences are counted as gaps.

### T04 - CoVe Runtime Advisory PASS-Preserved Path

Read targets:

- `modules/core/stage4_outcome_runtime.py:390-568`
- `modules/core/stage4_orchestrator.py`
- `tests/test_stage4_orchestrator.py:1564-1728`
- Any CoVe module found by `rg "chain_of_verification|quick_verify|cove" modules tests`

Questions:

- When `quick_verify` or `verify` raises, does Stage4 always preserve Director PASS?
- Which sinks receive the advisory: logging, UI, `episode_production.jsonl`, `audit_event`, runtime summary, and dashboard?
- Is there any branch where the runtime exception accidentally triggers retry or suppresses the final manuscript?
- Are early `return` statements in tests leaving intended assertions unreachable?

Return:

- PASS-preservation flow map.
- Sink coverage table.
- Test gaps around exceptions, source labels, and final manuscript preservation.

### T05 - CoVe Semantic Fail-Closed Retry Path

Read targets:

- `modules/core/stage4_outcome_runtime.py:470-528`
- `modules/core/stage4_outcome_runtime.py` CoVe call sites found by `rg "cove_fail_closed|provisional_pass_downgrade|CoVe"`
- `tests/test_stage4_orchestrator.py`
- CoVe validator/result type definitions found by `rg "ChainOfVerification|cove_result|correction_hints"`

Questions:

- Which CoVe result classes intentionally convert a PASS into retry?
- Which exceptions are runtime-advisory only?
- Are source labels such as `quick_verify` and `llm_verify` consistently typed?
- Should any runtime failure class become terminal, remain notice-only, or require better operator display?

Return:

- CoVe classification matrix: semantic fail, runtime failure, warning, skip.
- Current behavior and recommended policy for each class.
- Regression tests needed to keep semantic fail-closed separate from runtime advisory.

### T06 - Operator Display And Dashboard Semantics

Read targets:

- `modules/api/bridge_server.py:2073-2209`
- `modules/api/bridge_server.py` call sites around proof status and quality summary.
- `modules/core/services/audit_service.py`
- UI or desktop surfaces found by `rg "proof_digest|sink_alignment_summary|runtime_audit_summary|CoVe|advisory" UI geuldobi-desktop modules`
- `tests/test_bridge_quality_summary.py`
- `tests/test_audit_service.py`

Questions:

- How are proof digest, sink alignment, and runtime audit statuses shown to operators?
- Does the UI label `warn` as advisory evidence, final failure, or ambiguous warning?
- Is CoVe runtime advisory visible enough after PASS, without demoting the PASS?
- Are current `authority_role` labels sufficient for proof digest and sink alignment summaries?

Return:

- Operator-display surface map.
- Labeling risks and suggested copy/field names.
- Tests or snapshots needed for dashboard semantics.

### T07 - Live-Run Evidence And Current-Session Status

Read targets:

- `docs/2026-04-27/gcp-iam-5arc-live-run-handoff-current.md`
- `docs/2026-04-27/auto-frontier-lag-5arc-runtime-analysis-ssot.md`
- `docs/2026-04-26/frontier-lag-5arc-post-run-merge-audit.md`
- `projects/01_골든카나리아/logs/runtime_audit_summary.json` if present.
- `projects/01_골든카나리아/logs/runtime_audit.jsonl` and `episode_production.jsonl` compact read-only slices only if needed.
- `projects/01_골든카나리아/project_data.db` read-only only if needed.

Questions:

- Which warning residues are directly from the stopped 2026-04-27 run?
- Which are older run-wide residues carried into current summaries?
- Were CoVe runtime advisories observed after PASS in live evidence, or only in tests and handoff narrative?
- Which evidence is terminal, provisional, stale, or current-session scoped?

Return:

- Evidence table with source, scope, session/run id if available, and authority level.
- Any contradiction between docs, DB, logs, and runtime summaries.
- Minimal live-run proof queries for later implementation.

### T08 - Benchmark And Archive Impact

Read targets:

- `scripts/archive_benchmark_record.py`
- `scripts/backfill_benchmark_native_post_run_evidence.py`
- `scripts/compare_benchmark_records.py`
- `scripts/report_benchmark_operator_lines.py`
- `tests/test_archive_benchmark_record.py`
- `tests/test_backfill_benchmark_native_post_run_evidence.py`
- `tests/test_compare_benchmark_records.py`
- `benchmarks/README.md`
- Issues #62 and #65 if available.

Questions:

- Which benchmark payload fields currently preserve proof-digest status, operational status, Stage4 live-session status, and advisory warnings?
- Can early-April versus current comparisons distinguish reject-rate improvements from proof-digest/advisory residue?
- Should CoVe runtime advisory count become a benchmark metric?
- What fields must be added or normalized before benchmark comparisons are trustworthy?

Return:

- Benchmark field inventory.
- Proposed before/after metrics for Issue #59.
- Test additions for archive/backfill/compare/report scripts.

### T09 - Regression Test Gap Design

Read targets:

- `tests/test_stage4_orchestrator.py`
- `tests/test_failure_analyzer.py`
- `tests/test_audit_service.py`
- `tests/test_bridge_quality_summary.py`
- `tests/test_stage4_canary_tools.py`
- `tests/test_compare_benchmark_records.py`
- `modules/core/stage4_outcome_runtime.py`
- `modules/core/failure_analyzer.py`

Questions:

- Which current tests already pin #59 behavior?
- Which assertions are unreachable or too weak to catch regressions?
- What tests should be added before code changes?
- How can tests avoid live LLM calls while proving CoVe advisory, proof digest, and authority labeling behavior?

Return:

- Proposed test list by file owner.
- Minimal fixtures and expected assertions.
- Tests that should remain out of scope until after implementation.

### T10 - Synthesis / Implementation Readiness

Read targets:

- All terminal returns when available.
- Issue #59.
- This order document.
- Issues #58, #62, and #65 only for dependency context if available.

Questions:

- What is the smallest safe implementation tranche?
- Which findings are confirmed, inferred, or blocked on missing evidence?
- Which tests should land first?
- Which operator-display changes are required versus optional?
- What should remain out of scope for the first PR?

Return:

- One synthesis memo with:
  - confirmed proof-digest warn sources
  - confirmed CoVe advisory/fail-closed policy
  - implementation tranches
  - test plan
  - benchmark/reporting plan
  - authority guardrails
  - open questions

## Copy-Paste Terminal Prompts

### Prompt T01

You are Terminal T01 for Issue #59. Work read-only in `c:\Users\wjjo\Desktop\글도비`. Investigate Stage4 proof-digest producer and warn taxonomy. Do not edit files, DB, docs, or GitHub. Read `modules/core/failure_analyzer.py`, `modules/core/stage4_canary_tools.py`, `scripts/run_auto_frontier_lag_harness.py`, `scripts/run_stage34_canary.py`, `docs/2026-04-26/frontier-lag-5arc-post-run-merge-audit.md:142-148`, and `docs/2026-04-26/frontier-lag-5arc-post-run-merge-audit.md:234-237`. Find where proof digest or sink alignment status becomes `warn`, which fields drive it, and whether each warning is terminal, advisory, or display-only. Return a compact report with evidence paths/lines, field taxonomy, authority meaning, implementation owner surface, and open questions. Mark evidence versus inference.

### Prompt T02

You are Terminal T02 for Issue #59. Work read-only in `c:\Users\wjjo\Desktop\글도비`. Investigate settled DB and final authority truth for Stage4 PASS/PASS_WITH_FIX attempts. Do not edit files, DB, docs, or GitHub. Read `modules/core/db_manager.py`, `modules/core/failure_analyzer.py`, `modules/core/stage4_director_runtime.py`, `modules/core/stage4_outcome_runtime.py`, and `tests/test_failure_analyzer.py:3543-3844`. Use read-only DB inspection of `projects/01_골든카나리아/project_data.db` only if needed. Map which table/row is final authority for verdict, score, selection reason, verdict reason, artifact path, content hash, runtime advisory, and retry directives. Return authority-row map, any real missing fields or mismatches, suggested read-only queries, and open questions.

### Prompt T03

You are Terminal T03 for Issue #59. Work read-only in `c:\Users\wjjo\Desktop\글도비`. Investigate rationale metadata and sink-alignment core behavior. Do not edit files, DB, docs, or GitHub. Read `modules/core/failure_analyzer.py`, `tests/test_failure_analyzer.py`, `modules/core/services/audit_service.py`, and `tests/test_audit_service.py`. Explain how `selection_reason`, `verdict_reason`, `comparison_notes`, `selected_candidate_advisory_struct`, `runtime_advisory`, and `retry_directives` are collected and compared. Separate required final-authority metadata from expected companion/session/log absences. Return analyzer decision tree, expected absence rules, likely false positives, proposed tests, and open questions.

### Prompt T04

You are Terminal T04 for Issue #59. Work read-only in `c:\Users\wjjo\Desktop\글도비`. Investigate the CoVe runtime advisory PASS-preserved path. Do not edit files, DB, docs, or GitHub. Read `modules/core/stage4_outcome_runtime.py:390-568`, `modules/core/stage4_orchestrator.py`, `tests/test_stage4_orchestrator.py:1564-1728`, and relevant CoVe module paths found by `rg "chain_of_verification|quick_verify|cove" modules tests`. Determine whether `quick_verify` or `verify` runtime exceptions always preserve Director PASS and remain typed as advisory across logging, UI, `episode_production.jsonl`, `audit_event`, runtime summary, and dashboard. Return flow map, sink coverage table, test gaps, and open questions.

### Prompt T05

You are Terminal T05 for Issue #59. Work read-only in `c:\Users\wjjo\Desktop\글도비`. Investigate CoVe semantic fail-closed retry policy versus runtime failure advisory. Do not edit files, DB, docs, or GitHub. Read `modules/core/stage4_outcome_runtime.py:470-528`, other CoVe call sites found by `rg "cove_fail_closed|provisional_pass_downgrade|CoVe|cove_result|correction_hints" modules tests`, and `tests/test_stage4_orchestrator.py`. Build a classification matrix for CoVe semantic fail, runtime failure, warning, skip, and source labels such as `quick_verify` and `llm_verify`. Decide which classes are currently terminal/retry, notice-only, or ambiguous. Return evidence, recommended policy, regression tests, and open questions.

### Prompt T06

You are Terminal T06 for Issue #59. Work read-only in `c:\Users\wjjo\Desktop\글도비`. Investigate operator display and dashboard semantics. Do not edit files, DB, docs, or GitHub. Read `modules/api/bridge_server.py:2073-2209`, nearby proof/status call sites, `modules/core/services/audit_service.py`, `tests/test_bridge_quality_summary.py`, and `tests/test_audit_service.py`. Use `rg "proof_digest|sink_alignment_summary|runtime_audit_summary|CoVe|advisory" UI geuldobi-desktop modules` for UI surfaces. Determine whether operators can confuse proof-digest `warn` or CoVe runtime advisory with final narrative failure, and whether `authority_role` labels are sufficient. Return display surface map, label risks, suggested field/copy changes, tests, and open questions.

### Prompt T07

You are Terminal T07 for Issue #59. Work read-only in `c:\Users\wjjo\Desktop\글도비`. Investigate live-run evidence and current-session status. Do not edit files, DB, docs, or GitHub. Read `docs/2026-04-27/gcp-iam-5arc-live-run-handoff-current.md`, `docs/2026-04-27/auto-frontier-lag-5arc-runtime-analysis-ssot.md`, and `docs/2026-04-26/frontier-lag-5arc-post-run-merge-audit.md`. Inspect compact read-only slices of `projects/01_골든카나리아/logs/runtime_audit_summary.json`, `runtime_audit.jsonl`, `episode_production.jsonl`, and `project_data.db` only if needed. Classify warning residues as current-session, run-wide, stale, provisional, or terminal. Return evidence table, contradictions, suggested proof queries, and open questions.

### Prompt T08

You are Terminal T08 for Issue #59. Work read-only in `c:\Users\wjjo\Desktop\글도비`. Investigate benchmark and archive impact. Do not edit files, DB, docs, or GitHub. Read `scripts/archive_benchmark_record.py`, `scripts/backfill_benchmark_native_post_run_evidence.py`, `scripts/compare_benchmark_records.py`, `scripts/report_benchmark_operator_lines.py`, `tests/test_archive_benchmark_record.py`, `tests/test_backfill_benchmark_native_post_run_evidence.py`, `tests/test_compare_benchmark_records.py`, and `benchmarks/README.md`. If accessible, use Issues #62 and #65 only for dependency context. Identify fields needed to compare early-April versus current proof-digest status, Stage4 live-session status, CoVe advisory counts, reject/attempt rates, and runtime/cost side effects. Return field inventory, metric proposal, test additions, and open questions.

### Prompt T09

You are Terminal T09 for Issue #59. Work read-only in `c:\Users\wjjo\Desktop\글도비`. Investigate regression test gaps. Do not edit files, DB, docs, or GitHub. Read `tests/test_stage4_orchestrator.py`, `tests/test_failure_analyzer.py`, `tests/test_audit_service.py`, `tests/test_bridge_quality_summary.py`, `tests/test_stage4_canary_tools.py`, `tests/test_compare_benchmark_records.py`, `modules/core/stage4_outcome_runtime.py`, and `modules/core/failure_analyzer.py`. Identify current tests that already pin #59 behavior, weak or unreachable assertions, and deterministic tests needed before implementation. Avoid live LLM calls. Return proposed test list by file owner, minimal fixtures, expected assertions, out-of-scope tests, and open questions.

### Prompt T10

You are Terminal T10 for Issue #59. Work read-only in `c:\Users\wjjo\Desktop\글도비`. You are the synthesis lane. Do not edit files, DB, docs, or GitHub. After T01-T09 reports are available, synthesize them against Issue #59 and `docs/2026-04-27/issue-59-stage4-proof-digest-cove-advisory-10terminal-order.md`. Produce one compact implementation-readiness memo with confirmed proof-digest warn sources, confirmed CoVe advisory/fail-closed policy, inferred-only risks, blocked/missing evidence, minimal implementation tranches, test plan, benchmark/reporting plan, operator-display needs, authority guardrails, and out-of-scope items for the first PR. Do not invent evidence; cite terminal reports and repo paths.

## Synthesis Protocol

1. Run T01-T09 in parallel.
2. Do not let T10 start final synthesis until at least T01, T02, T03, T04, T05, and T09 return.
3. If any terminal finds a direct contradiction with Issue #59, T10 must list it as `CONTRADICTION` rather than smoothing it away.
4. If findings split between analyzer false positive, missing sink metadata, and operator-display ambiguity, prefer the smallest testable tranche first.
5. Do not promote this order pack into implementation authority without a new execution SSOT or explicit operator instruction.

## Side-Effect Coverage For This Order Pack

- File writes: this document only.
- DB writes: none.
- GitHub writes: none.
- Runtime/log writes: none.
- Temp queue mutation: none.
- Implementation side effects to inspect later: DB truth rows, JSONL/log/audit sinks, console/UI display, benchmark/archive records, canary summaries, and stopped-run handoff docs.

## 3-Pass Save Audit

Pass 1 - Structure and scope: PASS. The document is an investigation order pack, not an execution SSOT. It names Issue #59, source evidence, global rules, 10 terminal lanes, copy-paste prompts, synthesis protocol, and side-effect scope.

Pass 2 - Evidence and consistency: PASS. The order is based on current GitHub Issue #59 plus local docs, code, tests, bridge/dashboard, analyzer, and benchmark/reporting surfaces. It does not claim implementation readiness or final closure of proof-digest warnings.

Pass 3 - Actionability and guardrails: PASS. Each terminal has bounded read targets, questions, and return format. Read-only, Director-authority, CoVe advisory/fail-closed separation, and operator-visibility guardrails are explicit.

Estimated confidence: 96%.
