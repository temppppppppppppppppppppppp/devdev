Date: 2026-03-27
Status: final
Document Type: gimmick-elegance lane survey report
Lane: T3 — Stage 4 Authority / Verdict / Retry Gimmicks
Canonical Path: `docs/2026-03-27/opus/rol-llm-gimmick-t3-stage4-authority-verdict.md`
Evidence Path: `docs/2026-03-27/opus/rol-llm-gimmick-t3-stage4-authority-verdict-evidence.md`
Source Order: `docs/2026-03-27/rol-llm-friendliness-gimmick-elegance-6terminal-master-order.md`
Prior Lane Report: `docs/2026-03-24/opus/rol-llm-friendly-t2-stage4-authority-verdict.md`

Commit State:
- Baseline Commit: `eb7a41d86a52b075861bcbd59a402622ab08d6cc`
- Baseline Dirty Summary: `dirty: tracked llm_router/provider/context/validator surfaces, docs/temp/queue-state.json, project logs/artifacts; untracked multi-provider docs, fact docs, anthropic_vertex provider scaffolding/tests`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Executive Summary

Stage 4's verdict pipeline contains **9 identifiable gimmicks** (special mechanisms beyond vanilla orchestration). Of these, **5 are elegant**, **3 are mixed**, and **1 is inelegant**.

The overall gimmick-elegance picture is **mixed**, but tilted positive. The pipeline's major design moves — advisory chain parallelism, PASS_WITH_FIX loop, contradiction firewall, and retry lane routing — are localized, owner-explicit, and traceable in 2-4 file hops. The inelegant `_god1_*` channel is the sole hidden mutable side-channel, and it is already documented with a migration TODO.

Since the prior 2026-03-24 wave, one material improvement landed: the **verdict-field precedence contract comment** at `director_ensemble.py:1346-1354` now explicitly declares field authority. This was the #1 hotspot in the prior wave and directly raises gimmick elegance.

The remaining quick-win surface is almost entirely comment-only: thin-delegate markers, quality-gate mutation annotations, and retry-lane priority headers. No boundary refactor is required to make Stage 4 gimmicks LLM-tractable.

| Verdict | Value |
|---|---|
| Navigation-ready for this lane | yes |
| Cheap-fix-first verdict | yes |
| Gimmick-elegance verdict | **mixed** (5 elegant, 3 mixed, 1 inelegant) |
| Boundary-refactor can wait | yes |

**Top 3 highest-ROI quick wins:**
1. `# [THIN DELEGATE]` / `# [AUTHORITY]` boundary markers on `stage4_post_pass_runtime.py:26-47`
2. Per-method `# Mutates:` annotations on 4 quality-gate methods in `director_ensemble.py:976-1157`
3. Retry lane priority comment on `stage4_retry_runtime.py:825`

## 2. Included Coverage / Exclusions

### Included
| File | Lines | Role |
|---|---|---|
| `stage4_interview_round.py` | 6,019 | Round execution, verdict processing, advisory chain |
| `stage4_director_runtime.py` | 1,518 | Director review/prevalidation orchestration |
| `stage4_post_processor.py` | 1,010 | PASS settlement owner shell |
| `stage4_post_pass_runtime.py` | 1,350 | Post-pass world-state/manager/advisory runtime |
| `stage4_reject_runtime.py` | 916 | Reject guidance and retry snapshot |
| `stage4_retry_runtime.py` | 1,096 | Retry generation and PASS_WITH_FIX loop |
| `director_ensemble.py` | 2,298 | Ensemble selection, quality gates, verdict building |

**Total: 14,207 lines across 7 files.**

### Excluded
- `stage4_orchestrator.py` (T1 lane)
- `stage4_context_builder.py`, `stage4_context_packets.py` (T4 lane)
- `validation_orchestrator.py`, validator family (T4 lane)
- `chief_writer.py`, prompt builders (T4 lane)
- `db_manager.py`, persistence sinks (T6 lane)
- Scripts, tests, UI, docs (T6 lane)

## 3. Current Read Order / Ownership / Gimmick Map

### Ownership Chain
```
stage4_orchestrator.py (T1)
  +-- Stage4InterviewRound.run()          [stage4_interview_round.py:2425]
        |-- _prepare_round_execution()     setup
        |-- _run_generation_phase()        writer candidates
        |-- _run_validation_phase()        _god1_* -> DirectorRuntime
        |     +-- Stage4DirectorRuntime
        |           |-- run_pre_director_validation()
        |           |-- run_director_core_validation_modules()
        |           |-- collect_director_retrieval_context()
        |           +-- run_director_optional_validation_modules()
        |-- run_director_review_phase()    director decision
        |     +-- DirectorEnsembleSelector
        |           +-- select_and_judge_ensemble()
        |                 +-- _apply_ensemble_quality_gates()
        |                       4 gate methods mutate _EnsembleSelectionState
        +-- _complete_round_after_review()
              +-- _process_verdict()
                    |-- PASS -> PostProcessor -> Stage4PostPassRuntime
                    +-- REJECT -> Stage4RejectRuntime -> Stage4RetryRuntime
```

### Gimmick Inventory (9 gimmicks)

| # | Gimmick | Owner File | Elegance | Hops |
|---|---|---|---|---|
| G1 | `_god1_*` channel | interview_round:2270 -> director_runtime:102 | **inelegant** | 2 files, hidden mutation |
| G2 | Verdict field proliferation + gate normalization | director_ensemble:1346-1397 | **elegant** (after Q1 contract comment) | 1 file |
| G3 | Quality gate mutation chain | director_ensemble:976-1157 | **mixed** | 1 file, 4 methods |
| G4 | Advisory chain (9 parallel advisories) | interview_round:4594-4711 | **elegant** | 1 file, ThreadPoolExecutor |
| G5 | Post-select conflict downgrade | interview_round:3635-3729 | **elegant** | 1 file, parallel checks |
| G6 | PASS_WITH_FIX loop | retry_runtime:90-236 | **elegant** | 1 file, dataclass payloads |
| G7 | Retry lane routing | retry_runtime:825-896 | **mixed** | 1 file, implicit priority |
| G8 | Contradiction firewall | director_ensemble:449-475 | **elegant** | 1 file, explicit criteria |
| G9 | IFC violation family escalation | reject_runtime:477-510 | **mixed** | 2 files (import from immutable_fact_contract) |

## 4. Top Hotspots

| # | File | Line Anchor | Axis | Sev | Description | Fix Type |
|---|---|---|---|---|---|---|
| H1 | `stage4_post_pass_runtime.py` | L26-47 | Gimmick Elegance | **P1** | 7 thin delegate methods at top forward to `self.owner` with no boundary marker. Creates false impression the entire class is a pass-through, hiding the substantial post-pass settlement authority below L54. A cold LLM may skip the class entirely. | comment-only |
| H2 | `director_ensemble.py` | L976-1157 | Gimmick Elegance | **P1** | `_EnsembleSelectionState` is mutated by 4 quality-gate methods (`_apply_scm_single_candidate_cap`, `_apply_contradiction_firewall_gate`, `_apply_nc3_consistency_penalty`, `_resolve_adaptive_ensemble_verdict`). None documents which fields it mutates. An LLM must read all 4 to understand the final state shape. | comment-only |
| H3 | `stage4_retry_runtime.py` | L825-896 | Gimmick Elegance | **P1** | `_resolve_retry_lane_routing` routes between inplace, patch, rewrite, and ASP correction with implicit boolean priority. No header comment states the selection hierarchy. | comment-only |
| H4 | `stage4_interview_round.py` | L2270-2280 | Gimmick Elegance | **P1** | `_god1_*` channel: 7 instance attributes smuggled via setattr as a round-local context bridge. Producer (L2274-2280) and consumer (`director_runtime.py:102-110`) have comments, and a migration TODO exists at L2273. Still the sole hidden mutable side-channel in Stage 4. | ignore (documented, defer) |
| H5 | `stage4_reject_runtime.py` | L477-510 | Gimmick Elegance | **P2** | IFC violation family classification imports from `stage4_immutable_fact_contract` module. The escalation decision (`should_escalate_to_rewrite`) depends on both violation families and consecutive empty patches. Tracing requires 2 file hops. The import boundary is clean but the escalation precedence is implicit. | comment-only |
| H6 | `stage4_interview_round.py` | L3635-3729 | Observability | **P2** | Post-select conflict checks (continuity + history) run in a parallel ThreadPoolExecutor. Both use `fail-closed` error handling, meaning a check error forces a conflict. This is a design decision but not annotated as such — an LLM might mistake it for a bug. | comment-only |

## 5. Top Quick Wins

| # | Target | File:Line | Fix Type | Action |
|---|---|---|---|---|
| Q1 | Thin delegate / authority boundary | `stage4_post_pass_runtime.py:26` | comment-only | Add `# -- [THIN DELEGATE] forwarding to owner --` before L26 and `# -- [AUTHORITY] post-pass settlement runtime --` before `_submit_manager_async` (L54) |
| Q2 | Quality gate mutation docs | `director_ensemble.py:976` | comment-only | Add `# Mutates: state.score` / `# Mutates: state.firewall_*, state.contradiction_details` / etc. one-line annotations on each of the 4 quality gate methods |
| Q3 | Retry lane priority header | `stage4_retry_runtime.py:825` | comment-only | Add comment block: "Lane routing priority: inplace (fix_scope==inplace + fix_pack ready) > patch (post_select_conflict or partial) > rewrite (full scope or fallback). ASP correction runs independently after candidate generation." |
| Q4 | Fail-closed annotation | `stage4_interview_round.py:3712` | comment-only | Add inline: `# [DESIGN] fail-closed: check error treated as conflict to prevent silent PASS on broken continuity` |
| Q5 | IFC escalation boundary | `stage4_reject_runtime.py:477` | comment-only | Add comment: "IFC escalation: if violation families include immutable-fact + patch_targets empty + consecutive_empty_patches >= threshold -> escalate fix_scope from inplace to partial" |
| Q6 | EnsembleSelectionState docstring | `director_ensemble.py:612` | comment-only | Add dataclass docstring: "Mutable state carrier for quality gate chain. Gate-mutated fields: score, firewall_*, contradiction_details. Inputs: selected_*, original_verdict, score_breakdown_raw." |
| Q7 | _god1_* scope annotation | `stage4_interview_round.py:2270` | doc-only | Refresh the migration TODO with current _god1_* field inventory (7 fields) and note that the channel is read-once per round, not accumulated across rounds |

**Comment/doc/observability ratio: 7/7 = 100% (exceeds >50% rule).**

## 6. Gimmick Elegance Judgment

### G1. `_god1_*` channel — INELEGANT
- **Owner**: `Stage4InterviewRound._run_validation_phase()` (producer), `Stage4DirectorRuntime.run_pre_director_validation()` (consumer)
- **Input contract**: implicit — 7 `setattr()` calls on the owner instance
- **Precedence**: not applicable (sole instance mutation channel in Stage 4)
- **Hidden state**: YES — round-local attributes set on the owner object, read via `getattr(owner, "_god1_*", None)` in another file
- **Hops**: 2 files
- **Mitigation**: producer/consumer comments and TODO are present since the prior wave. The channel is read-once per round and does not accumulate. It survives because both sides carry ownership annotations, but it fails the "no hidden mutable side channels" criterion.
- **Refactor justified**: yes, but long-term. Explicit parameter passing would eliminate the implicit contract.

### G2. Verdict field proliferation — ELEGANT (improved)
- **Owner**: `DirectorEnsembleSelector._build_ensemble_decision_payload()` at `director_ensemble.py:1346-1397`
- **Input contract**: `_EnsembleSelectionState` + gate outputs
- **Precedence**: EXPLICIT — the contract comment at L1346-1354 declares: `final_verdict` > `verdict` (alias) > `director_verdict`/`original_verdict` (raw) > `gate_basis` (explains delta)
- **Hidden state**: none — all fields in a single return dict
- **Hops**: 1 file
- **Prior wave status**: this was **H1/P0** in the 2026-03-24 T2 report. The precedence contract comment has been realized in live code. Gimmick is now elegant.

### G3. Quality gate mutation chain — MIXED
- **Owner**: `DirectorEnsembleSelector._apply_ensemble_quality_gates()` at `director_ensemble.py:976`
- **Input contract**: `_EnsembleSelectionState` dataclass (14 fields, no docstring explaining mutable vs immutable fields)
- **Precedence**: implicit — 4 methods run in sequence, each may mutate different fields
- **Hidden state**: mutation via `state.score = ...`, `state.firewall_triggered = True`, etc.
- **Hops**: 1 file
- **Assessment**: the gimmick is localized (all in one file), but precedence depends on call order and no method documents its mutation footprint. A `# Mutates:` annotation per method would make it elegant.

### G4. Advisory chain (9 parallel) — ELEGANT
- **Owner**: `Stage4InterviewRound._run_advisory_chain()` at `stage4_interview_round.py:4594`
- **Input contract**: candidates list + validation_results + next_ep + genre_name
- **Precedence**: all advisories are peers; no priority ordering needed (results merged into validation_results)
- **Hidden state**: none — each advisory uses a cloned validation_results copy; merged back explicitly
- **Hops**: 1 file (advisory methods are all private methods on the same class)
- **Assessment**: ThreadPoolExecutor(max_workers=9), per-advisory timeout 60s, overall 300s. Per-type logging and cancel-on-timeout. Clean, well-observed, composable.

### G5. Post-select conflict downgrade — ELEGANT
- **Owner**: `Stage4InterviewRound._run_post_select_checks()` at `stage4_interview_round.py:3635`
- **Input contract**: verdict, final_manuscript, final_state_updates, round_ctx
- **Precedence**: explicit — runs AFTER director verdict, can flip PASS->REJECT
- **Hidden state**: none — returns (verdict, feedback, attempt, error_category) tuple
- **Hops**: 1 file
- **Assessment**: parallel continuity + history conflict checks in ThreadPoolExecutor(max_workers=2). Fail-closed design (check error = conflict) is a deliberate design move. Would benefit from a one-line fail-closed annotation.

### G6. PASS_WITH_FIX loop — ELEGANT
- **Owner**: `Stage4RetryRuntime.execute_pass_with_fix_loop()` at `stage4_retry_runtime.py:90`
- **Input contract**: verdict, final_manuscript, director_result, etc.
- **Precedence**: explicit — runs only when verdict == "PASS_WITH_FIX"
- **Hidden state**: minimal — fix_ok flag tracks whether any iteration succeeded
- **Hops**: 1 file
- **Assessment**: up to 3 iterations with explicit abort gates. Each stage returns a typed dataclass payload. Iteration → patch attempt → guards → re-audit → verdict application. Cleanly decomposed.

### G7. Retry lane routing — MIXED
- **Owner**: `Stage4RetryRuntime._resolve_retry_lane_routing()` at `stage4_retry_runtime.py:825`
- **Input contract**: previous_attempt dict, prev_manuscript, round_num
- **Precedence**: IMPLICIT — 4 lanes (inplace, patch, rewrite, full) selected by boolean combinations. IFC consecutive-empty-patch escalation adds another implicit condition.
- **Hidden state**: none (returns typed dataclass)
- **Hops**: 1 file
- **Assessment**: the logic is correct and localized, but the priority hierarchy is only reconstructible by reading the boolean conditions. A header comment would make it elegant.

### G8. Contradiction firewall — ELEGANT
- **Owner**: `director_ensemble._classify_firewall_mode()` at `director_ensemble.py:449`
- **Input contract**: contradictions list, original_verdict, score, score_breakdown
- **Precedence**: explicit — only applies when original_verdict is PASS/PASS_WITH_FIX; otherwise returns "reject"
- **Hidden state**: none — pure function returning (mode, reason) tuple
- **Hops**: 1 file
- **Assessment**: checks if contradictions are fixable (proper noun, location, title drift) vs structural. Explicit criteria: score >= 80, contradictions <= 3, continuity_score >= 30, all fixable. Clean.

### G9. IFC violation family escalation — MIXED
- **Owner**: `Stage4RejectRuntime._build_reject_guidance_payload()` at `stage4_reject_runtime.py:477`
- **Input contract**: rejection_reason, fix_pack, patch_targets_empty, consecutive_empty_patches
- **Precedence**: implicit — escalation from inplace to partial depends on multiple conditions across two modules
- **Hidden state**: none
- **Hops**: 2 files (reject_runtime imports from stage4_immutable_fact_contract)
- **Assessment**: the import boundary is clean, but the escalation decision tree is implicit. A one-line annotation at the import site would clarify.

## 7. Deferred Refactor Candidates

| # | Target | Action | Rationale | Tag |
|---|---|---|---|---|
| D1 | `_god1_*` channel | Migrate to explicit parameters | TODO at L2273 exists. Instance mutation across file boundaries is the sole inelegant gimmick. Post-survey comments reduce immediate hazard. | long-term |
| D2 | `_EnsembleSelectionState` mutation chain | Consider explicit state-transition methods | Would make quality gate effects visible in method signatures. Low blast radius but design decision needed. | defer |
| D3 | `_finalize_round_outcome` 26-param signature | Split into PASS/REJECT top-level methods | Eliminates parameter confusion. Moderate blast radius. Carried forward from prior wave D2. | defer |

## 8. No-Action / Settled Areas

| Area | Reason |
|---|---|
| Verdict field precedence contract | `director_ensemble.py:1346-1354` — realized, explicit, accurate |
| Section Map | `stage4_interview_round.py:152-172` — accurate, covers all sections |
| `_god1_*` producer/consumer comments | L2270-2273 (producer) + `director_runtime.py:102-104` (consumer) — documented |
| Advisory chain parallelism | L4594-4711 — 9 advisories, ThreadPoolExecutor, per-type logging, timeout handling. Clean. |
| PASS_WITH_FIX loop | `stage4_retry_runtime.py:90-236` — dataclass payloads, explicit abort gates |
| Contradiction firewall | `director_ensemble.py:449-475` — pure function, explicit criteria |
| `stage4_reject_runtime.py` overall | Dedicated reject authority with clear dataclass payloads |
| `stage4_post_processor.py` early-return warning | Blast-radius comment present (settled prior wave) |
| `stage4_director_runtime.py` `get_module()` logging | `logging.debug` on None already present (settled prior wave) |

## 9. Cross-Lane Handoff Notes

| Note | Target Lane |
|---|---|
| Quality gate mutation chain (H2) feeds into the ensemble return dict consumed by T4 (validation orchestrator) and T1 (stage4_orchestrator) | T1, T4 |
| Post-pass settlement (H1) flows into world-state/fact-ledger/manager-delta updates — T5 (fact authority) should verify injection precedence against the per-work-fact-contract-alignment survey findings | T5 |
| Advisory chain (G4) produces warnings consumed by the Director input pack — T4 (writer/prompt) should note that advisory_parts merge into mandatory_context | T4 |
| IFC violation family (G9) imports from `stage4_immutable_fact_contract.py` which is a cross-module contract — T5 (fact authority/genre gimmick) should cover that module | T5 |
| Retry lane routing (G7) determines whether the next round uses inplace/patch/rewrite — T4 (writer/prompt) should note the downstream effect on chief_writer.inplace_patch vs generate_ensemble | T4 |

## 10. Confidence And Limits

**Overall confidence: 96%**

Breakdown:
- Gimmick inventory: 95%. All 9 identified gimmicks verified against live code. Possible minor gimmicks in deep helper methods (L1000-2000 range) were structurally reviewed but not individually graded.
- Elegance grading: 96%. Each gimmick graded against the 5-criterion test from the master order. Verdicts are evidence-based with file:line anchors.
- Prior wave delta: 98%. Verified that the verdict-field precedence comment (prior H1/Q1) exists in live code at `director_ensemble.py:1346-1354`. Confirmed that thin-delegate markers (prior Q2) and quality-gate mutation annotations (prior Q3) have NOT been realized yet.
- Cross-lane handoff accuracy: 90%. Handoffs are based on contract inspection, not runtime trace.

Limits:
- Static survey only. No fresh run.
- `stage4_interview_round.py` helper methods in the L1000-2000 range (director context builders, DB advisory builders) were structurally reviewed at method-signature level, not graded for gimmick elegance individually.
- `director_ensemble.py` blueprint comparison path (L1399-2298) was reviewed at method-signature level; internal prompt construction was not graded for gimmick elegance.
- Gimmick count (9) reflects mechanisms that materially alter verdict flow or require special knowledge. Routine patterns (error handling, logging, metrics) were not counted as gimmicks.

## 11. 3-Pass Audit Record

### Pass 1 — Structure and Scope
- Document type: gimmick-elegance lane survey report
- All 7 scope files inspected
- 9 gimmicks identified, each graded against the 5-criterion elegance test
- Every P0/P1 finding has file:line anchor
- Every recommendation has fix type
- Quick wins: 7 items, 100% comment/doc (exceeds >50% rule)
- Deferred refactor candidates: 3, all tagged long-term/defer (cap of 3 met)
- PASS

### Pass 2 — Evidence and Consistency
- Verified verdict-field precedence contract at `director_ensemble.py:1346-1354` (live code)
- Verified `_god1_*` comments at `stage4_interview_round.py:2270-2273` and `director_runtime.py:102-104` (live code)
- Verified advisory chain ThreadPoolExecutor at `stage4_interview_round.py:4621` (live code)
- Verified contradiction firewall at `director_ensemble.py:449-475` (live code)
- Verified PASS_WITH_FIX loop at `stage4_retry_runtime.py:90-236` with typed dataclass payloads (live code)
- Verified retry lane routing boolean conditions at `stage4_retry_runtime.py:866-896` (live code)
- Verified thin delegate methods at `stage4_post_pass_runtime.py:26-47` lack boundary markers (live code)
- Prior wave settled items confirmed still settled
- PASS

### Pass 3 — Readability and Operational Use
- Report answers all 4 T3 lane questions from the master order
- Gimmick-elegance judgment provides per-gimmick verdicts with evidence
- Quick wins are actionable without touching behavior
- Cross-lane handoff notes reference specific T1/T4/T5 scope files
- No scope creep into execution SSOT or code changes
- PASS

Estimated confidence: **96%**
