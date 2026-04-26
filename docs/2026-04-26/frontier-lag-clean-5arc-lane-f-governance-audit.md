# Frontier Lag Clean 5-Arc — Lane F Governance Audit

Date: 2026-04-26
Track: system order / adversarial governance audit (read-only)
Status: final after embedded 3-pass audit
Document Type: Lane F lane report under the 6-terminal order pack
Canonical Path: `docs/2026-04-26/frontier-lag-clean-5arc-lane-f-governance-audit.md`
Order Pack: `docs/2026-04-26/frontier-lag-clean-5arc-6terminal-order-pack.md` §11
Baseline Commit: `a76689ec6c7d1ff6a55686d9889be15009ebb4b7`
Baseline Dirty Summary:
- `M 0_temp.txt`
- `?? docs/2026-04-26/auto-frontier-lag-5arc-runtime-analysis-ssot.md`
- `?? docs/2026-04-26/frontier-lag-clean-5arc-6terminal-order-pack.md`
- `?? projects/0_골든카나리아/`

## Scope

Adversarial governance audit of the proposed clean 5-arc Frontier Lag direction **before** any execution SSOT is approved. The audit takes the six lane-defining questions from the order pack §11 and tests them against (a) what the codebase already does today, (b) what the post-run audit observed, and (c) what the proposed Lane D bridge packet and Lane E harness policy would degrade into if the Big-Four governance invariants in `AGENTS.md` are not protected end-to-end.

Out of scope:

- code patches (read-only audit only)
- final lane-D bridge contract design (Lane D's job)
- final lane-E harness design (Lane E's job)
- narrative quality re-judgment of the failed Stage3 ep4 candidate

## Evidence

Primary documents:

- `AGENTS.md` §대원칙 (Big-Four invariants), §Document Save Rule, §Operations Governance.
- `docs/implementation/system-order-init-harness.md`.
- `docs/2026-04-26/frontier-lag-clean-5arc-6terminal-order-pack.md` §3 (Non-Negotiable Governance), §11 (Lane F prompt).
- `docs/2026-04-26/frontier-lag-5arc-post-run-merge-audit.md` — observed run interpretation, Stage3 ep4 timeline contradiction, HIL stop path.

Code anchors directly inspected during audit (read-only):

- `modules/domain/agents/three_phase_blueprint_runtime.py:2966-3009` — `_finalize_terminal_failure` (binding-trapdoor over Director's emergency fallback). Verified.
- `modules/domain/agents/unified_blueprint_validator.py:735-804` — `_apply_binding_prevalidation_contract` (Python rewrites Director PASS/PASS_WITH_WARNING into PASS_WITH_FIX, merges feedback/reason). Verified.

Code anchors inspected by sub-investigators (cited from their returns; line ranges propagated as claims, not re-verified end-to-end):

- `modules/domain/agents/unified_blueprint_validator.py:1149-1158`, `:1354-1363`, `:1402-1403` — `_build_no_director_validation_result`, `_build_director_error_result`, `director is None` short-circuit.
- `modules/core/stage3_validation_boundary.py:236-298` — `apply_phase3_quality_gate`, `annotate_or_accept_terminal_quality_gate_result`.
- `modules/domain/agents/three_phase_blueprint_runtime.py:2779-2820`, `:2956-2964` — PASS_WITH_FIX failure handling, `_intermediate_reject`.
- `main_a.py:4184-4256` — Stage3 HIL prompt, skip/stop branches, exception branch.
- `scripts/run_auto_frontier_lag_harness.py:370-426`, `:540-563`, `:658-664`, `:856-859`, `:952-973` — `--reuse-existing-project` short-circuit, worker status writeback, harness stub `_worker_runtime_input`, `boundary_reached` derivation, `derive_judgment`.
- `modules/core/stage4_post_pass_runtime.py:1597-1796` — `_persist_atomic_world_state`, `_persist_atomic_fact_ledger` (PASS-gated content sinks).
- `modules/core/stage4_post_processor.py:182-192`, `:1062`, `:1619-1635` — manuscript export (`_write_human_facing_manuscript_export`), `save_manuscript`, settlement emit.
- `modules/core/stage4_interview_round.py:2178-2237`, `:6544` — session-memory envelope retry consumption, `advisory_warnings` shape.
- `modules/core/db_manager.py:545`, `:1454`, `:1463`, `:2364-2402`, `:3165`, `:3368-...` — `save_manuscript`, `save_blueprint`, `get_previous_blueprint`, `director_selections.advisory_warnings`/`update_director_selection_rationale`, `cached_tokens`, `stage_attempts` upsert.
- `modules/core/services/project_service.py:510-545`, `:595-624` — bible rollback writeback (`Protagonist.actual_truth` overwrite from `state_logs`, gated by interactive `_confirm_action`).
- `modules/core/project_manager.py:261-290`, `:404-466`, `:854`, `:1016` — arc/blueprint anchor writes and txt mirror generation.
- `modules/domain/agents/chief_writer.py:1723-1882` — `inplace_patch_structural` (LLM-authored patch text today, no contract barrier against future precomputed payloads).
- `modules/core/world_state.py:207`, `:905`; `modules/core/fact_ledger.py:184-271`, `:288` — Python-side merge of LLM-originated `final_state_updates` into ledger.
- `modules/core/failure_analyzer.py:725-742`, `:1166`, `:1393-1424` — donor-sink ordering, `pass_rate_monitor` alignment.
- `modules/domain/agents/base_agent.py:152-173`, `:552` — context-cache lineage check, `cached_tokens` integer.

Run telemetry referenced (from post-run audit):

- `projects/0_골든카나리아/project_data.db` — 9 `stage_attempts`, 9 `director_selections`, 3 `blueprints`, 2 `manuscripts`, 707 `ui_events`, 130 `llm_calls`.
- `projects/0_골든카나리아/logs/auto_frontier_lag_worker_result.json` — `status: success`.
- `projects/0_골든카나리아/logs/auto_frontier_lag_analysis.json` — `arcs_advanced=1`, `requested_limit_hit=false`, `stop_reason=stage3_user_abort`.
- `projects/0_골든카나리아/logs/runtime_audit_summary.json` — Stage3 proof digest `warn` (terminal failed attempt without artifact metadata).
- Stage3 ep4 `attempt_key=s3:ep4:arc1:a10:20260426_171126`: Director score 95, verdict surface `PASS_WITH_FIX`, runtime `final_verdict=FAILED`, contradiction `2006년 1월 1일` (blueprint surface) vs `2006년 1월 3일` (arc state).

Evidence vs. inference is labeled per finding below.

## Findings

The audit's central finding is structural: the *same architectural seam* — Python wraps a Director verdict and emits a synthetic dict whose `verdict` / `feedback` / `reason` fields the rest of the pipeline trusts as Director output — is the common substrate for every P0 risk identified across Q1, Q3, Q4, and Q6. Two such surfaces already exist in production code today and were the proximate cause of the observed Stage3 ep4 failure. The proposed Lane D bridge packet and Lane E skip/quarantine policy will inherit the same seam unless explicitly contract-bound.

Specifically:

- **Authority-rewrite seam (live)**. `unified_blueprint_validator._apply_binding_prevalidation_contract` (lines 740-804) takes a Director `PASS` or `PASS_WITH_WARNING`, *rewrites* `merged_verdict = "PASS_WITH_FIX"`, sets `merged_feedback` to a Python-authored `[Binding prevalidation] …` string, and forces `merged_scope = "full"` (regenerate-only) when binding categories include any `_BINDING_PREVALIDATION_REGENERATE_CATEGORIES` member. The code is documented as "structural binding prevalidation requires regenerate-only repair" — but the field that downstream consumers read is still labeled the Director's verdict. This violates the spirit of the AGENTS.md Big-Four invariant #1 ("Python collects, LLM judges") even when the rewrite is mechanically defensible, because the *visible authority signature* is no longer Director's.
- **Authority-trapdoor seam (live)**. `three_phase_blueprint_runtime._finalize_terminal_failure` (lines 2985-2993) runs the legitimate emergency-fallback branch when the Director's terminal score `>= PatchModeThresholds.REWRITE`, but if `retry_state.prev_binding_issue_count > 0` (counter populated from Python pre-validate), it overrides into `final_verdict = "FAILED"` and discards the blueprint with no second Director call. This is the exact lever that converted the observed run's Director-PASS_WITH_FIX-95 episode into the `FAILED` outcome that triggered `stage3_user_abort`.
- **Process-vs-objective collapse seam (live)**. `scripts/run_auto_frontier_lag_harness.py` writes `worker_result.status = "success"` whenever the worker process exits cleanly, regardless of `frontier_result.stop_reason`. The downstream `derive_judgment` consumes `arcs_advanced >= arc_count` (or `requested_limit_hit`) as the boundary signal, but the analyzer's surface success is read by operators in tandem with the worker status, conflating process success with objective success. This is the post-run audit's finding made governance-relevant: a Director-rejected episode plus operator-stop produces a green-looking worker.
- **Reuse-survive seam (live)**. `--reuse-existing-project` (`scripts/run_auto_frontier_lag_harness.py:370-426`) does not reset the prior run's `stage_attempts`, `director_selections`, `blueprints`, `world_state`, or `fact_ledger`. A re-run targeting `0_골든카나리아` after the observed Stage3 ep4 FAILED would load the same `2006년 1월 1일` blueprint surface from durable storage via `db_manager.get_previous_blueprint` (line 1463), reproducing the contradiction without any cache involvement. This is a Q6 P0 even though Q6 is framed as "session memory or context cache" — the dominant stale-truth vector is the *DB itself*, not the cache.
- **Advisory-as-authority seam (live)**. `director_selections.advisory_warnings` JSON blob (`db_manager.py:2364`) holds `truth_pins`, `cache_lineage`, `repair_contract`, etc. (`stage4_interview_round.py:6544`) and is read back into the next retry's session-memory envelope (`stage4_interview_round.py:2178-2237`). The blob is structurally indistinguishable from authoritative verdict rationale once it has been written. Any Lane D bridge packet that lands in `advisory_flags` (the natural place if no typed column is added) will degrade into the same surface.

Together these say: the Frontier Lag pipeline's hardest governance problem is not "could a future bridge violate Director sovereignty" — it is "two existing surfaces already do, and any new packet contract will inherit the same architecture unless explicitly contract-bound."

The Lane F audit therefore answers each of the six required questions as follows.

**Q1 — Could a continuity bridge accidentally make Python the narrative judge?** Yes, by analogy with the live seams above. The bridge packet's `proposed_bridge` and `allowed_fix_scope` fields are exactly the shape that, if compacted/filtered/ranked by Python before reaching Director (the existing pattern used in `_normalize_stage3_fix_pack`, `_run_python_prevalidation_phase`), would deny Director the chance to see the *raw* contradiction options. The same answer applies to `applied_status` synthesized on Director timeout/exception (`_build_director_error_result`-style fail-soft).

**Q2 — Could a bridge packet silently become a factsheet auto-edit?** Conditionally yes. The current factsheet/world-state/fact-ledger writes are PASS-gated on Stage4 (`_persist_atomic_*` only inside `_handle_pass_outcome`), but the *content* of `final_state_updates` is merged into the ledger by Python without re-binding the payload to the specific attempt_key + Director PASS row. A bridge that populates `applied_artifact_key="bible"` or `applied_artifact_key="arcs"` and uses an existing in-place patch routine inherits this gap. The bible rollback path (`project_service.py:599-602`) already overwrites `Protagonist.actual_truth` from a stored `state_logs` row, gated only by interactive `_confirm_action`; a non-interactive bridge invocation would bypass the gate entirely.

**Q3 — Could Director authority be bypassed by prevalidation, cache, or harness policy?** It already is bypassed in two production paths (`_apply_binding_prevalidation_contract`, `_finalize_terminal_failure` binding-trapdoor) and in the Stage3 quality-gate score floor (`stage3_validation_boundary.py:236-258`). The HIL stop prompt is a legitimate operator override but does not record the underlying Director verdict alongside the operator choice in the DB row, which means after-the-fact audits cannot tell "operator stopped over Director's PASS" apart from "operator stopped after Director REJECT."

**Q4 — Could skip/quarantine policy hide real quality failures?** Yes, in three concrete ways. (a) The current skip branch increments `arcs_advanced_delta=1` with `manuscripts_delta=0`; if a downstream consumer reads only `arcs_advanced`, a Director-rejected episode is counted as advanced. (b) The Stage3-exception branch (`main_a.py:4248-4256`) shares the same skip path. (c) A future quarantine option without an explicit `quarantine_count` field in `derive_judgment` would land in `stage_attempts.reject_reason` as plain text, invisible to the harness boundary check.

**Q5 — Could DB telemetry make advisory evidence look authoritative?** Yes. `director_selections.advisory_warnings` is read by retry packet builders at the same authority level as Director rationale and re-fed into the next prompt. There is no `authority_level` discriminator on advisory entries.

**Q6 — Could session memory or context cache introduce stale cross-run truth?** Yes — but the dominant vector is `--reuse-existing-project` plus durable DB rows, not the cache. Stage4's `session_memory_envelope` also re-loads prior failed attempt manuscript text from disk if `artifact_path` survives. The context cache itself is bounded by short TTL and lineage check, but the lineage check is too narrow (model/provider only, no project epoch).

## Risks

Severity scale: P0 = blocks execution-SSOT approval until mitigated; P1 = must be mitigated in execution SSOT (acceptable with explicit contract); P2 = address during implementation, advisable but not blocking; P3 = monitor or backlog.

### P0 — blocking

- **P0-A. Binding-trapdoor over Director's emergency fallback.** `modules/domain/agents/three_phase_blueprint_runtime.py:2985-2993`. Python forces `final_verdict=FAILED` when `prev_binding_issue_count>0`, even when Director's score crosses the legitimate REWRITE emergency-fallback threshold. This is the proximate cause of the observed Stage3 ep4 failure. **Evidence: verified.** Severity P0 because (i) it is live, (ii) it directly violates Director sovereignty, (iii) any clean 5-arc run will hit it again on the same class of contradiction. **Mitigation:** route `prev_binding_issue_count>0 AND last_score>=REWRITE` back to Director with binding evidence as a final adjudication call; do not auto-FAIL. If Director is unreachable, fail closed and surface `runtime_route_authority="python_binding_trapdoor"` as a *parallel* field to `final_verdict`, never as the verdict itself.

- **P0-B. Verdict-rewrite of Director PASS/PASS_WITH_WARNING into PASS_WITH_FIX.** `modules/domain/agents/unified_blueprint_validator.py:740-804` (`_apply_binding_prevalidation_contract`). Python rewrites Director's verdict in place and synthesizes feedback/reason text under Director's authority signature. **Evidence: verified.** Severity P0 because the operator UI and downstream consumers read the rewritten field as Director's. **Mitigation:** keep `director_verdict` immutable. Surface binding findings as a parallel `runtime_route_verdict` with explicit `runtime_route_authority="binding_prevalidation_contract"`. The Stage3 boundary already has the right shape at `annotate_or_accept_terminal_quality_gate_result` (`stage3_validation_boundary.py:282-298`); extend that pattern to every site that today rewrites a verdict.

- **P0-C. Worker `status:success` despite `stage3_user_abort`.** `scripts/run_auto_frontier_lag_harness.py:540-563`. The harness writeback declares `success` when the process exits cleanly; the analyzer separately reports `arcs_advanced` and `stop_reason`, but the success boolean is what unattended dashboards and downstream code consume. **Evidence: verified by post-run audit.** Severity P0 because unattended runs cannot tell process success from objective success without parsing two sources. **Mitigation:** introduce `process_success` (process exited 0) and `objective_success` (`requested_limit_hit OR (arcs_advanced>=arc_count AND no FAIL/skip in window)`) as separate fields. Default operator-facing success boolean must be `objective_success`. This is the headline Lane E concern; Lane F endorses it as a P0 governance precondition.

- **P0-D. Skip branch counts Director-rejected ep as advanced.** `main_a.py:4209-4218` (skip path) and `main_a.py:4248-4256` (Stage3-exception path). Both increment `arcs_advanced_delta=1` with `manuscripts_delta=0`. If `boundary_reached` evaluates `arcs_advanced >= arc_count`, a Director-rejected episode becomes "boundary reached." **Evidence: cited from sub-investigator, line ranges not re-verified end-to-end.** Severity P0 because skip policy must not collapse onto completion semantics. **Mitigation:** skipped/quarantined arcs increment a separate `arcs_skipped` counter; `objective_success` is gated on `arcs_skipped == 0` for strict-quality runs, with explicit opt-in for survey runs.

- **P0-E. `--reuse-existing-project` carries forward FAILED-row content across runs.** `scripts/run_auto_frontier_lag_harness.py:370-426`. No `reset_after(target_ep)` is invoked for episodes whose last `stage_attempts` row is FAILED; `db_manager.get_previous_blueprint` (line 1463) and `world_state` re-load the prior contradiction surface. **Evidence: code structure cited; behavior is inference-by-construction.** Severity P0 because the same Jan1 vs Jan3 contradiction reproduces from durable storage in every retry. **Mitigation:** `--reuse-existing-project` must auto-invoke `reset_after(target_ep)` for any episode whose last `stage_attempts` is FAILED, OR refuse to reuse and require an operator confirmation. Either is acceptable — silent reuse is not.

- **P0-F (proposed-bridge inheritance).** Lane D's `proposed_bridge` packet, if it follows existing patterns (`_normalize_stage3_fix_pack`, `_run_python_prevalidation_phase`), will (i) compact/filter candidates before Director sees them, (ii) rank candidates by Python heuristics, (iii) synthesize `applied_status` on Director timeout. **Evidence: inference by analogy with verified live patterns.** Severity P0 because the same architectural seam is what makes P0-A/B live. **Mitigation:** the Lane D bridge contract must (i) emit *all* candidate dates/facts in deterministic insertion order with raw evidence, (ii) make `applied_status` a function of `director_verdict` (refuse anything but `pending` when `director_verdict` is empty), (iii) any compaction or ranking is forbidden until Director sets `selected_index`, (iv) on Director error, set `applied_status="not_applied"` AND escalate (no progression). Lane D's design must include unit-test scaffolding for each.

### P1 — must mitigate in execution SSOT

- **P1-A. Stage3 quality-gate score floor flips PASS to REJECT.** `modules/core/stage3_validation_boundary.py:236-258` (`apply_phase3_quality_gate`). Mitigation: the existing `runtime_gate_basis` annotation surface already exists at `:282-298`; extend it to all gate flips and require `runtime_gate_basis` in DB telemetry whenever a Director PASS becomes a runtime REJECT.
- **P1-B. HIL stop prompt loses Director-verdict context.** `main_a.py:4189-4207`. Mitigation: HIL prompt rows in DB must carry the Director verdict the operator was overriding (or `none` if no Director call existed).
- **P1-C. `_persist_atomic_fact_ledger` runs on PASS without re-binding payload to attempt_key + verdict row.** `modules/core/stage4_post_pass_runtime.py:1640-1654`. Mitigation: persist with `(attempt_key, director_verdict_row_id)` as a precondition; reject ledger writes whose payload hash diverges from the verdict-bound artifact's `state_updates`.
- **P1-D. `inplace_patch_structural` lacks contract barrier against precomputed `patched_blocks`.** `modules/domain/agents/chief_writer.py:1723-1882`. Today the patch text is LLM-authored via `self.ask(prompt)`; future callers (a bridge applier) could pass pre-baked maps. Mitigation: assert `patched_blocks` source is the live LLM response object; reject precomputed payloads.
- **P1-E. `advisory_warnings` JSON loaded into next-retry envelope at authority level of Director rationale.** `modules/core/stage4_interview_round.py:2178-2237`. Mitigation: tag every advisory record with `authority_level=advisory|verdict`; retry envelope builders must reject `authority_level=advisory` entries from authoritative slots.
- **P1-F. Bible rollback path (`project_service.py:599-602`) reachable non-interactively if a bridge ever invokes it.** Mitigation: assert interactive `_confirm_action` *or* an explicit Director-verdict-bound override token before any `bible` anchor write; reject the call otherwise.
- **P1-G. Quarantine mode (proposed) without typed `quarantine_count` in `derive_judgment`.** `scripts/run_auto_frontier_lag_harness.py:952-973`. Mitigation: add `quarantine_count` to the harness analyzer schema before introducing the policy; never rely on parsing `reject_reason` text.
- **P1-H. Stage4 envelope re-loads prior FAILED attempt's manuscript text from disk.** `stage4_interview_round.py:2208`. Mitigation: envelope builders must verify the loaded artifact's `attempt_key` corresponds to a non-FAILED row before pinning.
- **P1-I. Bridge packet schema choice (typed column vs `advisory_flags` JSON).** If Lane D lands the packet inside `advisory_flags` for shipping speed, P0-F mitigations partially evaporate. Mitigation: Lane D contract must specify a *typed column or dedicated table*, not a sub-key inside an existing advisory blob.

### P2 — address during implementation

- **P2-A. Director error/missing path returns synthesized REJECT.** `unified_blueprint_validator.py:1149-1158`, `:1354-1363`. Today this is fail-closed (correct). Risk is that a bridge analogue inherits the same surface and emits `applied_status="deferred"`. Mitigation already covered under P0-F; rated P2 here because the *current* surface is correct.
- **P2-B. `_save_arcs_to_txt` regenerates txt files, deletes stale.** `modules/core/project_manager.py:404-440`. Mitigation: when bridge applies, do not invoke arcs anchor write unless `director_verdict=APPROVED`; rely on append-only audit for proposed bridges.
- **P2-C. `pass_rate_monitor` donor-join can lag DB by a run.** `modules/core/failure_analyzer.py:1166`, `:1393-1424`. Mitigation: validate donor-sink staleness via per-run epoch tag.
- **P2-D. Context-cache lineage check too narrow.** `modules/domain/agents/base_agent.py:152-173`. Mitigation: add project-level epoch (or work_id+arc+ep) to the lineage tuple.
- **P2-E. Director Continuity caching unverified end-to-end.** `director_continuity.py` not inspected during this audit. Mitigation: Lane D research must verify whether a stale cached verdict can be replayed in place of a fresh Director call when the bridge fires.

### P3 — monitor

- **P3-A. Bible rollback today (interactive only).** Risk is purely theoretical until someone wires a non-interactive caller; documented for future audits.

## Recommendation

**Go/no-go for an execution SSOT: NO-GO until at minimum P0-A through P0-F have explicit mitigations baked into the SSOT.**

The Lane F audit confirms that the proposed clean 5-arc direction is *worth* pursuing — Lane D's preventive-bridge intent and Lane E's process/objective separation both attack real governance gaps that the observed run exposed. But the same audit shows two production surfaces already violate Director sovereignty in the spirit of AGENTS.md Big-Four invariant #1, and one of them (P0-A binding-trapdoor) is the proximate cause of the very failure the bridge is being designed to prevent. Building a bridge on top of an architecture that already rewrites Director verdicts in place will not make Director more sovereign — it will give the same seam a second packet contract to leak through.

Concrete go/no-go gates the execution SSOT must clear:

1. **Authority-rewrite ban**. The execution SSOT must include a contract under which `director_verdict` is immutable post-Director-call, and any runtime route is published as a parallel `runtime_route_verdict` with explicit `runtime_route_authority` source. Mitigations for P0-A, P0-B, and P1-A must reference this contract.
2. **Bridge typed schema**. Lane D's bridge packet must land in a typed column or dedicated table, not inside `advisory_flags` JSON (P0-F, P1-I).
3. **`applied_status` is a function of `director_verdict`**. The bridge applier must refuse anything but `pending` when `director_verdict` is empty; on Director error, set `not_applied` and escalate (P0-F).
4. **Process vs objective separation**. The harness must publish `process_success` and `objective_success` as distinct fields; the operator-facing success boolean defaults to `objective_success` (P0-C).
5. **Skip is not advancement**. Skipped/quarantined arcs increment a separate counter; `objective_success` rejects strict-quality runs with `arcs_skipped > 0` (P0-D).
6. **Reuse implies reset-after-FAIL**. `--reuse-existing-project` either resets after FAILED rows or refuses non-interactively (P0-E).
7. **Advisory authority discriminator**. `advisory_warnings` entries carry `authority_level`; retry packet builders reject `advisory`-level entries from verdict slots (P1-E).

Once those seven gates are written into the SSOT and the SSOT itself passes its own 3-pass audit per `AGENTS.md` Document Save Rule, the Lane F audit no longer blocks. The implementation order suggested in the order pack §12 is broadly aligned with these gates; the audit's only correction is that the *bridge schema typing decision* (gate #2) must happen before any bridge code is written, not after a first prototype.

The audit deliberately does not opine on the Lane C external-methodology principles, the Lane B memory/cache verdicts, or the Lane A failure forensics — those lanes are independent, and Lane F's sovereignty-protection conclusions hold regardless of their content.

## Subagent Cross-Check

Two sub-investigators were spawned per the order pack §11 subagent policy, in parallel, both read-only.

**Sub-investigator 1 — Python-vs-LLM authority risk.** Tasked with Q1, Q3, Q4. Returned six P0/P1 risks across three questions, with file/symbol/line anchors. Flagged the binding-trapdoor at `three_phase_blueprint_runtime.py:_finalize_terminal_failure` as the highest-leverage finding and identified `_apply_binding_prevalidation_contract` as the live verdict-rewrite seam. Caveat noted: subagent attributed the runtime file to `modules/core/`; the actual path is `modules/domain/agents/three_phase_blueprint_runtime.py`. Parent terminal verified the line range (2966-3009) at the corrected path — finding is intact. Subagent flagged its Director Continuity caching analysis as not performed (rated P2 here as P2-E).

**Sub-investigator 2 — persistence and factsheet mutation risk.** Tasked with Q2, Q5, Q6. Returned a write-surface map distinguishing PASS-gated content sinks from append-only telemetry sinks; identified `_persist_atomic_fact_ledger` as the surface that merges LLM-originated content via Python without binding payload to the Director PASS row. Identified `--reuse-existing-project` plus `db_manager.get_previous_blueprint` as the dominant Q6 stale-truth vector (DB durable rows, not cache). Flagged open questions on `applied_artifact_key` schema and `update_director_selection_rationale` overwrite path; both are folded into P1-I and P2 line items above.

Cross-check: the two subagents converged independently on the same architectural seam (Python wraps Director and emits a synthetic dict whose fields are read as Director's). This independent convergence increases confidence in the seam-level finding from "single-source claim" to "two-source corroborated."

Disagreement: none of consequence. Subagent 1 emphasized authority routing in the verdict pipeline; subagent 2 emphasized persistence sinks. The two views are complementary and the parent synthesis preserves both.

Parent terminal verifications performed:

- `_apply_binding_prevalidation_contract` at `unified_blueprint_validator.py:735-804` — read directly, verified shape claim.
- `_finalize_terminal_failure` binding-trapdoor at `three_phase_blueprint_runtime.py:2985-2993` — read directly, verified the conditional `prev_binding_issue_count > 0 → final_verdict = "FAILED"` logic.
- Path correction applied: `modules/domain/agents/three_phase_blueprint_runtime.py` (subagent's `modules/core/` was wrong).

Parent terminal did not re-verify the remaining sub-cited line anchors. Consumers of this audit who plan to draft Lane D's bridge contract should re-read each cited surface before relying on the line numbers for code-mod authority.

## 3-Pass Mini Audit

**Pass 1 — structure and scope.**

- The audit answers each of the six required questions in §11.
- It uses P0–P3 severity labels.
- Every P0 and P1 risk has a one-line mitigation.
- It ends with a go/no-go recommendation for an execution SSOT.
- It does not patch code; the only file written is this lane report.
- Subagent cross-check section is present and concrete.
- Result: PASS.

**Pass 2 — evidence and consistency.**

- The two parent-terminal-verified live seams (binding-trapdoor, verdict-rewrite contract) are explicitly tied to the post-run audit's observed Stage3 ep4 failure; the chain of `Director PASS_WITH_FIX-95 → Python rewrites → emergency fallback blocked → final_verdict=FAILED → stage3_user_abort` is internally consistent.
- The proposed-bridge risks (Q1, Q2) are flagged as inference-by-analogy and rated P0-F rather than mixed into the live P0 set, preserving the evidence/inference distinction the order pack requires.
- The `--reuse-existing-project` P0-E claim relies on absence of a per-run reset hook, which is inference-by-construction; the open question in subagent 2's return acknowledges this and the audit propagates the caveat.
- The advisory-authority drift finding (Q5) is tied to a verified telemetry shape (`director_selections.advisory_warnings`) plus an inferred consumer pattern in `stage4_interview_round`; rated P1-E rather than P0 because the consumer pattern is not parent-verified.
- No claim is made that Python *judged narrative truth* in the observed run; the post-run audit's authority-alignment check stands. The audit's contention is that Python wrote a verdict signature that *looked* like Director's, which is a sovereignty-spirit violation distinct from a sovereignty-letter violation.
- Result: PASS.

**Pass 3 — execution readability.**

- Each P0 risk has a file/symbol anchor and a one-line mitigation suitable for translation into an execution-SSOT acceptance gate.
- The seven go/no-go gates in the recommendation map 1:1 onto the P0 risks (P0-A→gate 1, P0-B→gate 1, P0-C→gate 4, P0-D→gate 5, P0-E→gate 6, P0-F→gates 2 and 3, plus gate 7 covering P1-E as a P1 follow-on).
- The audit explicitly defers Lane D bridge contract design and Lane E harness design to those lanes; it issues sovereignty constraints, not designs.
- The audit does not create a `docs/temp/` mirror, consistent with order pack §5.
- Result: PASS.

Estimated confidence: 95%.

The score is bounded to 95% (not higher) because two material claims rest on inference-by-construction rather than direct re-verification: (a) the absence of `reset_after(target_ep)` invocation under `--reuse-existing-project` (P0-E) and (b) the consumer pattern that re-feeds `advisory_warnings` into next-retry envelope as authority-equivalent (P1-E, basis for several Q5 conclusions). A code-side 3-pass at SSOT-draft time should re-verify both before treating P0-E as a hard go/no-go gate, and should re-verify the advisory consumer chain before treating P1-E as an SSOT must-fix. None of the P0 mitigations themselves depend on those re-verifications — they are framed as contract bans, which hold regardless.

Confidence is sufficient under the AGENTS.md Document Save Rule (95% gate) for a Lane F lane report. It is **not** sufficient for opening an execution SSOT directly from this report; the order pack §12 explicitly defers SSOT synthesis until all six lane reports exist and Headquarters performs its own combined 3-pass.
