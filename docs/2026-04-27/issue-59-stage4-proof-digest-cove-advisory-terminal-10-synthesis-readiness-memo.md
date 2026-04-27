# Issue #59 Terminal T10 Synthesis Readiness Memo

Date: 2026-04-27
Status: pre-synthesis readiness memo (T01-T09 reports absent at write time)
Track: system order
Mode: read-only synthesis lane output
Order Pack: `docs/2026-04-27/issue-59-stage4-proof-digest-cove-advisory-10terminal-order.md`
GitHub Issue: `#59 [Stage4] Close proof-digest warn residues and CoVe advisory review`
Encoding: UTF-8
Temp Queue Semantics: not an execution SSOT, no `docs/temp/` mirror.

## Synthesis Gate Status

The order pack's synthesis protocol (§ Synthesis Protocol) requires that "T10 start final synthesis [only] after at least T01, T02, T03, T04, T05, and T09 return." At memo write time, no T01-T09 reports exist for #59 in the workspace. Verified by directory listing of `docs/2026-04-27/`: only `issue-59-stage4-proof-digest-cove-advisory-10terminal-order.md` is present for this issue; no `issue-59-*-parallel-investigation/` directory exists; no `terminal-0[1-9]-*.md` for #59 exists at root either.

Consequence: this memo cannot be the final synthesis. It records what the order pack already cites with line precision, what remains blocked on T01-T09, and the smallest implementation shape that the order pack itself supports prior to terminal evidence. All "confirmed" rows below are anchored to direct repo reads of the order pack's citations, not to terminal reports.

## Confirmed Proof-Digest Warn Sources

Confirmed by direct repo read of order pack citations:

- Run-level statement of the residue is `docs/2026-04-26/frontier-lag-5arc-post-run-merge-audit.md:148`: "Runtime proof digest status: `warn` because selection/verdict/runtime advisory mismatch fields and rationale metadata gaps remain in the proof digest." (verified)
- Recommendation to handle this separately is `docs/2026-04-26/frontier-lag-5arc-post-run-merge-audit.md:237`: "Re-audit Stage4 proof digest warnings separately if we want to close the remaining selection/verdict/runtime advisory mismatch signals." (verified)
- The order pack names the producer surface as `modules/core/failure_analyzer.py:2423-2543` and the operator-display compaction surface as `modules/api/bridge_server.py:2073-2209`. Source files exist. Per-line behavior, branch coverage, and warn taxonomy are T01 + T03 + T06 deliverables and remain pending.

Not yet confirmed without T01 / T02 / T03 / T07:

- Whether each warn class is terminal, advisory, or display-only.
- Whether `warn` is run-wide residue carried into the current run summary or a current-session sink-alignment failure.
- Whether DB authority rows (`stage_attempts`, `director_selections`, settled artifact rows) actually disagree with runtime advisory rows, or whether the analyzer is overcounting expected companion absences.

## Confirmed CoVe Advisory / Fail-Closed Policy

Confirmed by direct repo read of `modules/core/stage4_outcome_runtime.py`:

- Lines 396-418: when CoVe `quick_verify` / `verify` raises, Stage4 emits an `[Advisory:CoVeRuntime:{source_label}]` log line and a UI line `⚠️ [CoVe] {source_label} 검증 런타임 실패 → Director PASS 유지`. Director PASS is preserved by construction at this seam.
- Lines 479-526 (`_build_cove_retry_disposition`): when CoVe fires a semantic fail-closed result, the path returns `accepted=False, should_continue=True` and stamps the previous-attempt record with `retry_pathology_source="cove_fail_closed"`, `cove_fail_closed=True`, `cove_runtime_failure=False`, `provisional_pass_downgrade=True`. So semantic fail-closed and runtime failure are stamped on different fields and routed differently.
- Lines 528-567 (`_log_cove_runtime_advisory`): the runtime-advisory sink writes a `STAGE4_COVE_RUNTIME_ADVISORY` payload to `episode_production.jsonl` and (if available) calls `audit_event("stage4_cove_runtime_advisory", ...)`. Payload includes `director_pass_preserved: True`. So PASS preservation is also recorded structurally on the sink, not only as a UI string.

Confirmed by order-pack citation of `tests/test_stage4_orchestrator.py:1564-1618`: CoVe verify exceptions log advisory rows and preserve the PASS in test fixtures (existence of the test pin verified by order pack; test body reading is a T04/T09 task).

Not yet confirmed without T04 / T05 / T09:

- Whether every `quick_verify` / `verify` call site routes exceptions through the seam at lines 387-418, or whether some callsite path skips it (T04).
- Whether the CoVe semantic-fail classification matrix (semantic fail vs. runtime failure vs. warning vs. skip) is consistently applied across callers and source labels (`quick_verify`, `llm_verify`) (T05).
- Whether existing tests have unreachable assertions or weak coverage that could let a runtime exception silently demote a PASS into a retry (T04 + T09).

Working policy statement that the implementation must preserve, derived from confirmed evidence:

- CoVe runtime exception → Director PASS preserved, structured advisory written to log + UI + episode_production.jsonl + audit_event.
- CoVe semantic fail-closed → REJECT-class retry, recorded as `cove_fail_closed=True` and `provisional_pass_downgrade=True` on the previous-attempt packet.
- The two paths must remain non-overlapping in code, sinks, tests, and operator display.

## Inferred-Only Risks

These are inferred from the order pack and confirmed file reads; they need terminal evidence before they become policy claims.

- (Inferred) The proof-digest `warn` is partially or fully driven by analyzer false positives that count expected companion absences as gaps. Needs T03.
- (Inferred) Some warn fields aggregate run-wide residue across older sessions, so a clean current-session run still shows `warn`. Needs T07.
- (Inferred) Operator display in `bridge_server` may render `warn` and CoVe runtime advisory ambiguously, which could be read as narrative failure. Needs T06.
- (Inferred) Benchmark/archive scripts (`scripts/archive_benchmark_record.py`, `compare_benchmark_records.py`, `report_benchmark_operator_lines.py`) may not preserve enough field granularity to compare early-April vs. current proof-digest/advisory rates. Needs T08.
- (Inferred) The bucket-of-cases that map to runtime advisory but were never observed in the stopped 2026-04-27 live run cannot be ranked for fix priority without T07.

## Blocked / Missing Evidence

| Block | Why blocked | Owner terminal |
| --- | --- | --- |
| Field-by-field warn taxonomy with terminal/advisory/display-only classification | No T01 report | T01 |
| Authority-row map across `stage_attempts`, `director_selections`, settled rows; whether runtime advisory rows ever shadow Director PASS | No T02 report | T02 |
| Analyzer decision tree for `selection_reason / verdict_reason / comparison_notes / selected_candidate_advisory_struct / runtime_advisory / retry_directives` and the expected-absence rules | No T03 report | T03 |
| Sink coverage table for CoVe runtime advisory across log / UI / `episode_production.jsonl` / `audit_event` / runtime summary / dashboard | No T04 report | T04 |
| CoVe classification matrix and policy recommendation per class | No T05 report | T05 |
| Operator-display label inventory and ambiguity risks for `proof_digest`, `sink_alignment_summary`, `runtime_audit_summary`, CoVe advisory | No T06 report | T06 |
| Live-run evidence table separating current-session, run-wide, stale, provisional, terminal | No T07 report | T07 |
| Benchmark field inventory and proposed before/after metrics | No T08 report | T08 |
| Test-by-test gap analysis with proposed deterministic regression tests | No T09 report | T09 |
| Direct contradictions between #59 issue text, order pack, terminal findings | All terminals absent | T01-T09 |

## Minimal Implementation Tranches

These tranches assume that T01-T09 confirm the order pack's framing. Numbers here are the smallest units the order pack already supports without inventing evidence; each tranche must be re-validated after T01-T09 land.

1. Tranche A — CoVe runtime advisory PASS-preservation contract.
   - Lock the seam at `modules/core/stage4_outcome_runtime.py:387-418` and the sink at lines 528-567 behind explicit invariants: any `quick_verify` / `verify` exception preserves Director PASS, writes the advisory to log + UI + `episode_production.jsonl` + `audit_event`, and never demotes the manuscript.
   - Add deterministic tests (no live LLM) covering: exception classes, source labels, sink presence, PASS preservation in DB authority rows.
   - Touch surface stays inside `modules/core/stage4_outcome_runtime.py` and the test file `tests/test_stage4_orchestrator.py`.
2. Tranche B — CoVe semantic fail-closed vs. runtime failure separation.
   - Lock `modules/core/stage4_outcome_runtime.py:479-526` so semantic fail-closed flips `cove_fail_closed=True / cove_runtime_failure=False` and runtime failure flips the inverse, with no overlap.
   - Add a structural assertion in tests and (optionally) a runtime invariant assert behind a debug flag.
3. Tranche C — Proof-digest warn taxonomy normalization.
   - Based on T01 + T03, classify each warn field into terminal, advisory, or display-only. Surface the taxonomy as a typed enum or dataclass at the producer site (`modules/core/failure_analyzer.py:2423-2543` per order pack).
   - Operator-facing summary in `modules/api/bridge_server.py:2073-2209` then renders by category, not by free-text warn string.
4. Tranche D — Expected-absence rules in sink alignment.
   - Based on T03, separate "missing because companion sink does not own this field" from "missing because final authority sink dropped it." Adjust analyzer counters accordingly.
5. Tranche E — Operator-display label changes.
   - Based on T06, add or rename labels so `warn` is never rendered next to a Director PASS without an explicit "advisory" / "observability" qualifier.
6. Tranche F — Benchmark/reporting field additions.
   - Based on T08, add fields that let early-April vs. current comparisons distinguish reject-rate improvements from proof-digest/advisory residue.
7. Tranche G — Live-run evidence proof queries.
   - Based on T02 + T07, ship read-only DB / JSONL queries the operator can run to prove that current-session warn residue is bounded and PASS authority is intact.

First PR scope target: **Tranche A + Tranche B + matching tests only.** Everything else waits until T01-T09 land and the surviving root-cause set is locked.

## Test Plan

All tests deterministic, no live LLM calls.

- For Tranche A:
  - `tests/test_stage4_orchestrator.py` — extend the CoVe runtime-failure block (referenced by order pack at lines 1564-1618) to assert: (a) Director PASS row is preserved across DB-authority sinks; (b) UI message contains `Director PASS 유지`; (c) `episode_production.jsonl` receives a `STAGE4_COVE_RUNTIME_ADVISORY` payload with `director_pass_preserved: True`; (d) `audit_event` is invoked with `stage4_cove_runtime_advisory`.
- For Tranche B:
  - Same file, separate test that drives a CoVe semantic fail-closed result and asserts `cove_fail_closed=True / cove_runtime_failure=False`, `provisional_pass_downgrade=True`, and that the next attempt is treated as REJECT-class retry.
  - Mutation guard: a third test that asserts the two fields are mutually exclusive given a single CoVe outcome.
- For Tranche C / D (later PR):
  - `tests/test_failure_analyzer.py` — pin the typed taxonomy and the expected-absence rules. The order pack's existing tests at lines 3543-3844 are the starting point.
- For Tranche E (later PR):
  - `tests/test_bridge_quality_summary.py` — snapshot-style assertions on operator labels.
- For Tranche F (later PR):
  - `tests/test_archive_benchmark_record.py`, `tests/test_backfill_benchmark_native_post_run_evidence.py`, `tests/test_compare_benchmark_records.py` — field presence and comparator behavior.
- For Tranche G (later PR):
  - A small read-only proof-query test or canary script under `scripts/` whose contract is "run on a live DB, return structured proof"; tested with a fixture DB.

Out-of-scope tests for the first PR (defer until T09 lands or until a later tranche):
- Changing CoVe call sites outside `stage4_outcome_runtime.py`.
- Live multi-arc reproduction tests.
- Cross-issue test coupling with #58, #62, #65.

## Benchmark / Reporting Plan

Subject to T08:

- Add `proof_digest_status` (terminal/advisory/display-only counts), `cove_runtime_advisory_count`, `cove_fail_closed_count`, `pass_preserved_after_advisory_count`, `current_session_status` and `run_wide_status` as separate top-level benchmark payload fields.
- Update `scripts/compare_benchmark_records.py` to compare early-April vs. current per the new fields.
- Update `scripts/report_benchmark_operator_lines.py` so operator lines distinguish observability `warn` from quality regression.
- Confirm `scripts/backfill_benchmark_native_post_run_evidence.py` can fill the new fields from existing records.
- Do not promote any new field into a hard-gate metric in this PR cycle. Director PASS authority remains the narrative gate.

## Operator-Display Needs

Subject to T06:

- Anywhere the operator sees `warn` alongside a Director PASS, render an explicit "advisory" / "observability" qualifier and an `authority_role` label (e.g., `narrative_authority=director_pass`, `proof_evidence=warn`).
- CoVe runtime advisory should be visible after PASS with the existing `Director PASS 유지` phrasing already produced at `modules/core/stage4_outcome_runtime.py:417`. Do not weaken or hide it.
- The bridge / dashboard summaries (`modules/api/bridge_server.py:2073-2209`) should not use the same string for "Stage4 narrative failure" and "Stage4 proof-digest warn".

## Authority Guardrails

Locked, non-negotiable for any first PR:

- Director PASS remains final narrative authority. Python advisory and runtime diagnostics never mechanically flip a Director PASS to REJECT. (AGENTS.md §대원칙 #1, #3; order pack § Global Rules.)
- Proof-digest `warn` and CoVe runtime advisory are observability evidence. They must remain typed and visible, but they must not silently change the manuscript outcome.
- CoVe semantic fail-closed remains the only CoVe-driven path that legitimately converts a provisional PASS into a retry; this is already explicit at `stage4_outcome_runtime.py:492-504` and must not collapse into the runtime-advisory path.
- Any benchmark or reporting field additions must clearly label `objective_success / runtime_route / proof_evidence` as distinct from Director verdicts in UI and SSOT output. (Stabilization SSOT pass2 residual risk, `docs/2026-04-26/frontier-lag-clean-5arc-stabilization-execution-ssot.md` §9.4.)
- No DB writes, no GitHub writes, no `docs/temp/` mirror, no 5-arc restart from this memo.
- UTF-8 only for any new code/test/doc; respect AGENTS.md `Encoding Guardrails` and complexity guardrails (touched production functions stay below the 180-LOC band).

## Out-Of-Scope For The First PR

- Final synthesis claims about #59. They wait on T01-T09.
- Changes to Stage3->Stage4 handoff (that is #58 territory).
- Changes to ensemble genre alignment (that is #56 territory).
- Any change to the CoVe model selection, prompts, or hard-gate semantics.
- Operator-display copy changes that depend on T06's surface inventory.
- Benchmark schema changes that depend on T08's field inventory.
- Any test implementation outside `tests/test_stage4_orchestrator.py` for the first PR.
- Live-run evidence collection that requires restarting the stopped 2026-04-27 5-arc run.

## Open Questions Forwarded To T01-T09

1. T01: Are any of the proof-digest `warn` classes hard gates today, or are they all advisory? Where is the boundary in code?
2. T02: Do any `runtime_advisory` rows ever overwrite settled `director_selections` for the same attempt key? Is there a path where Director PASS authority is shadowed by an advisory row?
3. T03: How many of the current `rationale_metadata_missing` counts come from companion-only sinks vs. from final-authority sinks? Without that split, Tranche D risks regressing legitimate gap detection.
4. T04: Are there CoVe call sites outside `stage4_outcome_runtime.py:387-418` that raise without flowing through the runtime-advisory seam? If yes, list them.
5. T05: Is the `provisional_pass_downgrade` flag consumed anywhere beyond the previous-attempt packet, and does its consumer treat it as terminal or as retry context?
6. T06: Are there UI surfaces in `UI/`, `geuldobi-desktop/`, or bridge endpoints that display proof-digest `warn` without an `authority_role` qualifier?
7. T07: Did the stopped 2026-04-27 run actually emit any `STAGE4_COVE_RUNTIME_ADVISORY` event in `episode_production.jsonl`, or is the policy currently exercised only in tests?
8. T08: Which benchmark fields would change semantics if Tranche C's typed taxonomy lands? Are existing comparisons safe under a field rename?
9. T09: Are there existing tests with unreachable assertions (e.g., early `return` before the assertion) around CoVe runtime advisory or proof-digest warn?
10. Cross-cutting: are there any direct contradictions between Issue #59 text and what the code at `stage4_outcome_runtime.py` currently does? If yes, list as `CONTRADICTION` per order pack §Synthesis Protocol step 3.

## 3-Pass Save Audit

Pass 1 - structure and scope:

- PASS. The memo is a pre-synthesis readiness output, not an execution SSOT, not a patch order.
- PASS. Status of the synthesis gate (T01-T09 absent) is recorded explicitly.
- PASS. All sections requested by the user prompt are present and compact.

Pass 2 - evidence and authority:

- PASS. Every "confirmed" claim is anchored to a direct read of a file path the order pack already cited (`stage4_outcome_runtime.py:387-567`, `frontier-lag-5arc-post-run-merge-audit.md:148,237`).
- PASS. Inferred and blocked items are clearly separated from confirmed items.
- PASS. Director PASS authority and CoVe semantic-vs-runtime separation are preserved as guardrails.
- PASS. No invented terminal evidence; absence of T01-T09 is stated explicitly.

Pass 3 - actionability and guardrails:

- PASS. First-PR scope (Tranche A + B + tests) is small enough to ship without T01-T09, but tied to file:line surfaces already in the order pack.
- PASS. Out-of-scope list keeps the PR from sprawling into #56 / #58 / benchmark / display work that needs other terminals first.
- PASS. Each open question is owned by a specific terminal.

Estimated confidence at memo time, given that T01-T09 are absent: 88%. The memo is procedurally and source-anchored sound, but the implementation tranche ranking and test plan will need re-validation when T01-T09 land. Confidence is intentionally below 95%; this memo is not a final synthesis.
