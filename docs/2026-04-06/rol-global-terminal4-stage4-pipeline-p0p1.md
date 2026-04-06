# Terminal 4 — Stage4 Pipeline P0-P1 Survey

Date: 2026-04-06
Terminal: 4
Owner: Stage4 consumer, gate, repair-contract, numeric carryover, authority readback
Mode: read-only global severity sweep
Baseline Commit: `0d7c077a9e6f14575aba7fc509b836d218db610d`

## Severity Verdict

**No live P0 found in this lane.**

**P1 candidates: 2 items (bounded, documented in existing queue)**

---

## Findings

### P1-1: Numeric Carryover Authority Surface Separation Incomplete

**Entry → Owner → Sink → Consequence:**

- Entry: `Stage4ContextBuilder._build_numeric_carryover_authority_block()` injects `fact_ledger.get_numbers()` carryover baseline values into the writer prompt (`stage4_context_builder.py:1006-1049`)
- Owner: `Stage4PostPassRuntime._persist_manager_delta_outputs()` builds `state_truth_owner_contract` with `numeric_carryover_authority` family (`stage4_post_pass_runtime.py:915-926`)
- Sink: `episode_bible.state_truth_owner_contract` and `state_log` via `save_episode_bible()` and `_persist_manager_state_log()` (`stage4_post_pass_runtime.py:956, 966-980`)
- Consequence: The writer prompt receives the carryover baseline numeric authority block. If the LLM generates a manuscript with a modified numeric value (e.g., asset total changed by a plot event), the `_build_state_truth_owner_contract()` function (`stage4_post_pass_runtime.py:128-216`) records `fact_ledger_carryover_baseline` as the authoritative owner. However, the post-pass persistence does not autonomously reconcile the new manuscript truth against the carryover baseline — that reconciliation depends on `NumericConsistencyChecker._is_numeric_carryover_authority_mismatch()` (`numeric_consistency_checker.py:550-579`) firing during the next episode's pre-validation.

**Why P1, not P0:** The mismatch is detected advisory-only at the next episode boundary. It does not cause a destructive overwrite or false PASS on the current episode. The risk is that a legitimately changed numeric value from the current episode's plot events (e.g., asset acquisition) gets flagged as a continuity violation in the next episode rather than being promoted to the new carryover baseline. This creates a **bounded false positive in the advisory layer**, not a false canonical persistence.

**Why not P2:** The mismatch can cause the retry loop to waste rounds rejecting correct manuscripts that reflect legitimate plot-driven numeric changes. For a production fresh run, this matters because `numeric_carryover_authority` contradiction type triggers strong advisory escalation (`_STRONG_ADVISORY_KEYS` includes `truth_gate` in `stage4_interview_round.py:2645`), which can force `PASS → PASS_WITH_FIX → REJECT` cascades.

**Narrowest owner files:** `stage4_context_builder.py`, `stage4_post_pass_runtime.py`

### P1-2: Repair-Contract Grammar / Provenance Sink Alignment Gap

**Entry → Owner → Sink → Consequence:**

- Entry: `Stage4InterviewRound._enforce_pass_with_fix_contract()` (`stage4_interview_round.py:2522-2572`) downgrades `PASS_WITH_FIX` to `REJECT` when fix_scope/fix_pack contract is incomplete, setting `repair_scope` and `gate_basis`
- Owner: `_normalize_director_gate_semantics()` (`stage4_interview_round.py:2603-2719`) merges `authoritative_fix_scope`, `repair_scope`, `gate_basis`, `strong_advisory_escalation` into the director result dict
- Sink: `save_stage_attempt()` in `db_manager.py:3067-3178` persists `fix_scope`, `verdict`, `initial_verdict`, `advisory_flags`, but does **not** have dedicated columns for `repair_scope`, `gate_basis`, `repair_contract`, or `authoritative_fix_scope`
- Readback: `FailureAnalyzer._collect_sink_alignment_gate_repair_results()` (`failure_analyzer.py:1041-1158`) cross-checks `repair_scope`, `repair_contract_subtype`, `repair_contract_provenance`, `scope_authority_fix_scope`, `scope_authority_authoritative_fix_scope` across five sinks — but `stage_attempts` table lacks these columns, so the alignment check hits the `gate_repair_metadata_missing` bucket

**Why P1, not P0:** The `stage_attempts` table stores `fix_scope` and `advisory_flags` JSON, so the core verdict and fix_scope are preserved. The missing columns mean the **readback layer** (`FailureAnalyzer.sink_alignment_summary()`) reports structural mismatches that are actually metadata-absence artifacts rather than true verdict disagreements. This does **not** cause false PASS or destructive overwrite. It causes **operator-facing summary readback to overcount mismatches**, potentially leading to inflated mismatch reports that obscure real issues.

**Why not P2:** The `sink_alignment_summary` is consumed by operator dashboards and downstream queue decisions. Systematic phantom mismatches on `repair_scope`, `gate_basis`, `repair_contract_subtype` can cause an operator to misjudge the actual pipeline health, which qualifies as "operator가 runtime state를 안전하지 않게 오판할 정도의 sink mismatch".

**Narrowest owner files:** `stage4_interview_round.py`, `failure_analyzer.py`, `db_manager.py`

---

## Answers to Required Questions

### 1. Stage4에서 false PASS_WITH_FIX, wrong fix_scope/repair_scope authority, numeric carryover misauthority가 live P0-P1인가

**False PASS_WITH_FIX: No live P0-P1.**

The `_enforce_pass_with_fix_contract()` gate (`stage4_interview_round.py:2522-2572`) is well-structured:
- If `fix_scope != "inplace"`, it rejects the `PASS_WITH_FIX` and downgrades to `REJECT`
- If `fix_pack` is missing required fields (`patch_targets`, `must_fix`, `do_not_regress`, `success_condition`), it downgrades
- The `_normalize_director_gate_semantics()` catches blank/invalid `authoritative_fix_scope` via the `[DCM-T2]` validation block and gates `PASS_WITH_FIX` to `REJECT` (`stage4_interview_round.py:2675-2719`)
- The strong advisory escalation path (`Lane2-G1`, line 2642-2673) properly escalates `PASS → PASS_WITH_FIX`, and if the resulting `PASS_WITH_FIX` has no valid scope, `Lane2-G2` immediately catches it and reverts to `REJECT` with `partial` scope

A false PASS_WITH_FIX surviving the gate is not a live risk.

**Wrong fix_scope/repair_scope authority: Bounded P1 (P1-2 above).**

The runtime correctly sets `repair_scope` on the director result dict. The gap is in the persistence-to-readback chain, not in the live verdict path.

**Numeric carryover misauthority: Bounded P1 (P1-1 above).**

### 2. gate → repair → persistence → summary readback 중 어디가 가장 먼저 틀어지나

**Persistence → readback seam** is where the chain first diverges.

- **Gate** is solid: `_normalize_director_gate_semantics()` + `_enforce_pass_with_fix_contract()` produce correct `repair_scope`, `gate_basis`, `authoritative_fix_scope` in the director result dict
- **Repair** is solid: `Stage4RejectRuntime._build_numeric_carryover_operator_notes()` correctly checks `repair_subtype == "numeric_carryover_authority"` and injects appropriate operator notes (`stage4_reject_runtime.py:286-332`)
- **Persistence** is where the first gap appears: `save_stage_attempt()` stores `fix_scope` but not `repair_scope` or `gate_basis` as first-class columns. The `advisory_flags` JSON blob carries some of this data, but it's not schema-guaranteed
- **Summary readback** amplifies the gap: `FailureAnalyzer` tries to cross-reference fields that aren't consistently stored, producing phantom mismatches

### 3. current front queue와 직접 연결되는 P1이 실제로 남아 있나

Yes. Both P1 items connect to the active front queue:

- **P1-1 (numeric carryover authority)** maps directly to the `0_0-stage4-consumer-contract-normalization-remediation` queue item, specifically the "numeric asset authority / carryover owner-boundary" seam noted in the execution roadmap (§1, priority 1)
- **P1-2 (repair-contract grammar/sink gap)** maps directly to `0_0-stage4-repair-contract-normalization-remediation` (priority 2), specifically the "shared naming, sink visibility for repair-contract metadata" seam

Both P1 items are already documented and queued. This survey confirms they remain live and correctly prioritized.

### 4. 가장 좁은 owner set은 무엇인가

1. `modules/core/stage4_interview_round.py` — gate enforcement, repair scope assignment, verdict normalization
2. `modules/core/stage4_post_pass_runtime.py` — state truth owner contract, numeric carryover authority persistence
3. `modules/core/failure_analyzer.py` — readback alignment checking, phantom mismatch generation

---

## Watchlist Only (Not P0-P1)

### W-1: `_merge_storage_only_state_change_families` fallback when `actual_truth` is empty

`_persist_manager_delta_outputs()` at line 910 calls `_merge_storage_only_state_change_families()` with `actual_truth if actual_truth else final_state_updates`. When `actual_truth` is empty, the fallback to `final_state_updates` means the Director's extracted state changes become the authoritative `persisted_state_changes`. This is documented in the `state_truth_owner_contract` as `actual_truth_fallback_used: true`, and the contract correctly records `actual_truth_primary_owner: "director_state_updates_fallback"`. This is a **design choice**, not a bug, but it means the manager pipeline's extraction quality directly affects persistence fidelity. Watchlist for future state-extraction reliability work.

### W-2: `save_stage_attempt` non-blocking silently drops rows

`save_stage_attempt()` catches all exceptions and returns `False` without raising (`db_manager.py:3170-3178`). This is intentional (non-blocking telemetry), but it means Stage4 telemetry rows can silently disappear if SQLite is locked, disk is full, or schema migration hasn't run. This is acceptable for advisory telemetry but becomes a concern if `FailureAnalyzer` readback is used for authoritative pipeline health judgments.

### W-3: `_build_post_select_conflict_contract` type inference is heuristic

The function at `stage4_interview_round.py:127-187` infers `conflict_type` from string matching (`"Continuity" in line` → `continuity`, `"History" in line` → `history`, else `check_error`). This is adequate for current use but could misclassify a conflict if the LLM returns unexpected formatting. Not P1 because the downstream behavior (REJECT) is correct regardless of the specific `conflict_type` label.

### W-4: Post-select `fix_scope` hardcoded to `"full"`

At `stage4_interview_round.py:5004-5009`, post-select conflict downgrades always set `repair_scope="full"` and `fix_scope="full"`. This is conservative and correct for safety, but it means even a minor proper-noun continuity conflict triggers a full rewrite attempt. This could waste retry budget but does not create false acceptance.

---

## Fresh Run Requirement Assessment

**Static evidence is sufficient** to confirm these P1 items. Both are already corroborated by:
- The existing queue documentation (`execution-roadmap.md` priorities 1 and 2)
- Code-level contract analysis above
- Previous fresh run evidence (`projects/00_20260403` and `r2` sinkproof canary results)

A fresh run would provide additional runtime confirmation of P1-2 (whether phantom mismatches actually appear in the readback), but it is **not required** to confirm the P1 severity. The static code paths are clear.

---

## 3-Pass Audit Record

### Pass 1. Structure and Scope
- Document type: severity survey (read-only)
- Scope: Stage4 consumer, gate, repair-contract, numeric carryover, authority readback
- Focus files verified against filesystem: all 6 files exist and were read
- Output contract compliance: findings first, severity stated, exact file paths included

### Pass 2. Evidence and Consistency
- P1-1 evidence chain: `_build_numeric_carryover_authority_block` → `_build_state_truth_owner_contract` → `save_episode_bible` → `NumericConsistencyChecker` (next ep). Internally consistent.
- P1-2 evidence chain: `_enforce_pass_with_fix_contract` → `_normalize_director_gate_semantics` → `save_stage_attempt` (missing columns) → `FailureAnalyzer._collect_sink_alignment_gate_repair_results` (phantom mismatches). Internally consistent.
- Roadmap queue mapping verified: P1-1 → priority 1, P1-2 → priority 2. Matches `execution-roadmap.md` §4.
- No overclaiming beyond inspected code evidence.

### Pass 3. Execution and Readability
- Findings are actionable: owner files and specific line ranges identified
- Watchlist items clearly separated from P1 items
- No queue change proposed, no code patch applied
- Future implementation notes provided within P1 descriptions (the existing queue already has these)

Confidence: 96%

---

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-06 output
