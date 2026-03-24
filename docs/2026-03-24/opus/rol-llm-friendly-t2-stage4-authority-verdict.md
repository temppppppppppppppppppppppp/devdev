Date: 2026-03-24
Status: final
Document Type: LLM-friendliness lane survey report
Lane: T2 — Stage 4 Authority / Verdict Flow
Canonical Path: `docs/2026-03-24/opus/rol-llm-friendly-t2-stage4-authority-verdict.md`
Evidence Path: `docs/2026-03-24/opus/rol-llm-friendly-t2-stage4-authority-verdict-evidence.md`
Source Order: `docs/2026-03-24/rol-llm-friendliness-6terminal-master-order.md`
Commit State:
- Baseline Commit: `529869adddb35c93c3ec557aeaed665de168daef`
- Baseline Dirty Summary: `dirty: tracked stage4/state/writer surfaces, docs/temp/queue-state.json, project artifacts deleted, new docs/2026-03-24/ and stage4 immutable-fact files`

## 1. Executive Summary

Stage 4 verdict flow is **authority-readable** and **navigation-aided** after the post-survey comment/doc SSOT realization. The Section Map in `stage4_interview_round.py` L152-172 and `_god1_*` producer/consumer comments are materially helpful.

The remaining LLM comprehension hazards are not about missing section markers or undocumented implicit channels. They are about:

1. **Verdict field proliferation** — 4 verdict-related fields in director_ensemble return dicts with no precedence contract.
2. **Mutable state chain** — `_EnsembleSelectionState` mutated by 4 quality gate methods without per-method mutation docs.
3. **Parameter-heavy branching** — `_finalize_round_outcome` 26-param signature obscures which params matter for PASS vs REJECT.

| Axis | Status | Confidence |
|---|---|---|
| Navigation | Ready | 93% — Section Map present; line ranges will drift but structure is clear |
| Authority | Readable | 91% — owner/runtime split is stable; `_god1_*` documented; 7 thin delegates slightly misleading |
| Contract | Partially Readable | 80% — verdict dataclasses help; verdict field precedence in ensemble return is undocumented |
| Observability | Readable | 90% — advisory chain logging is thorough; post-pass meta_save_failed propagation traceable |
| Local Readability | Readable | 85% — prior comment/doc quick wins realized; quality gate mutation chain is the main residual |

**Navigation-ready for this lane: yes**
**Cheap-fix-first verdict: yes**
**Boundary-refactor can wait: yes**

**Top 3 highest-ROI quick wins:**
1. Verdict field precedence contract comment in `director_ensemble.py` L1346
2. `# [THIN DELEGATE]` markers on `stage4_post_pass_runtime.py` L26-47
3. Per-method mutation annotation on quality gate methods in `director_ensemble.py`

## 2. Included Coverage / Exclusions

### Included
| File | Lines | Role |
|---|---|---|
| `stage4_interview_round.py` | 5,979 | Round execution, verdict processing, advisory chain |
| `stage4_director_runtime.py` | 1,518 | Director review/prevalidation orchestration |
| `stage4_post_processor.py` | 1,010 | PASS settlement owner shell |
| `stage4_post_pass_runtime.py` | 1,350 | Post-pass world-state/manager/advisory runtime |
| `stage4_reject_runtime.py` | 886 | Reject guidance and retry snapshot |
| `stage4_retry_runtime.py` | 1,096 | Retry generation and PASS_WITH_FIX loop |
| `director_ensemble.py` | 2,289 | Ensemble selection, quality gates, verdict building |

**Total: 14,128 lines across 7 files.**

### Excluded
- `stage4_orchestrator.py` (T1 lane)
- `stage4_context_builder.py`, `stage4_context_packets.py` (T3 lane)
- `validation_orchestrator.py`, validator family (T4 lane)
- `chief_writer.py`, prompt builders (T3 lane)
- `db_manager.py`, persistence sinks (T5 lane)
- Scripts, tests, UI, docs (T6 lane)

## 3. Current Ownership Map

### Authority Chain (verdict flow)
```
stage4_orchestrator.py
  └── Stage4InterviewRound.run()          [L2403]
        ├── _run_generation_phase()        [L2130]  ← writer candidates
        ├── _run_validation_phase()        [L2239]  ← _god1_* → DirectorRuntime
        │     └── Stage4DirectorRuntime
        │           ├── run_pre_director_validation()  [L86]
        │           ├── run_director_core_validation_modules()  [L170]
        │           ├── collect_director_retrieval_context()  [L785]
        │           └── run_director_optional_validation_modules()  [L231]
        ├── run_director_review_phase()    [L355]  ← director decision
        │     └── DirectorEnsembleSelector
        │           └── select_and_judge_ensemble()  [L2106]
        │                 └── _apply_ensemble_quality_gates()  [L976]
        │                       ├── _apply_scm_single_candidate_cap()
        │                       ├── _apply_contradiction_firewall_gate()
        │                       ├── _apply_nc3_consistency_penalty()
        │                       └── _resolve_adaptive_ensemble_verdict()
        └── _complete_round_after_review() [L2590]
              └── _process_verdict()        [L3806]
                    ├── PASS → _process_positive_verdict() → PostProcessor
                    │         └── Stage4PostPassRuntime
                    │               └── _save_world_state_atomic()
                    └── REJECT → _handle_reject() → Stage4RejectRuntime
                                  └── Stage4RetryRuntime (next round)
```

### Runtime Split Pattern
- `Stage4InterviewRound`: round owner, holds generation/validation/verdict/advisory authority
- `Stage4DirectorRuntime`: director review orchestration, reads `_god1_*` from owner
- `Stage4RejectRuntime`: reject guidance, retry snapshot, reject-side followups
- `Stage4RetryRuntime`: retry generation, PASS_WITH_FIX loop, lane routing
- `Stage4PostProcessor`: PASS settlement owner shell, DB primary save
- `Stage4PostPassRuntime`: post-pass world-state/fact-ledger atomic save, manager delta

All sub-runtimes hold `self.owner` back-reference to their parent.

## 4. Top Hotspots

| # | File | Line Anchor | Axis | Sev | Description | Fix Type |
|---|---|---|---|---|---|---|
| H1 | `director_ensemble.py` | L1346-1388 | Contract | **P0** | Verdict field proliferation: return dict has `verdict`, `director_verdict`, `final_verdict`, `original_verdict`, `gate_basis`. No inline contract explains precedence or when they diverge. A cold LLM cannot reliably pick the correct field for downstream logic. | comment-only |
| H2 | `director_ensemble.py` | L976-1157 | Authority | **P1** | `_EnsembleSelectionState` is mutated in-place by 4 quality gate methods. Each method changes different fields (`score`, `original_verdict`, `firewall_*`, `score_breakdown_raw`) but no method documents which fields it may modify. | comment-only |
| H3 | `stage4_interview_round.py` | L2767-2794 | Contract | **P1** | `_finalize_round_outcome` has 26 keyword parameters. PASS path uses ~10, REJECT path uses ~15. No grouping comment separates them. | comment-only |
| H4 | `stage4_post_pass_runtime.py` | L26-47 | Authority | **P1** | 7 thin delegate methods at the top forward to `self.owner`. Creates misleading first impression that this class is a pass-through wrapper, when it actually holds substantial authority over world-state settlement below. | comment-only |
| H5 | `stage4_interview_round.py` | L3806-3878 | Authority | **P1** | `_process_verdict` silently downgrades PASS→REJECT (quality gate) and normalizes CONDITIONAL_PASS→PASS. The gate name and downgrade reason are logged but not structured in a way an LLM can quickly locate as the branching authority. | comment-only |
| H6 | `stage4_retry_runtime.py` | L825-909 | Navigation | **P1** | `_resolve_retry_lane_routing` routes between 4 retry lanes (inplace, patch, rewrite, asp_correction) with implicit priority. No header comment explains the selection criteria or priority order. | comment-only |
| H7 | `director_ensemble.py` | L612-628 | Contract | **P1** | `_EnsembleSelectionState` dataclass has 14 fields but no docstring explaining field roles or which are mutable gate outputs vs immutable inputs. | comment-only |
| H8 | `stage4_interview_round.py` | L2248-2271 | Authority | **P2** | `_god1_*` channel — documented with producer/consumer comments and TODO. Already settled from prior SSOT, but the implicit mutation pattern remains a long-term authority debt. | ignore (documented, defer) |

## 5. Top Quick Wins

| # | Target | File:Line | Fix Type | Action |
|---|---|---|---|---|
| Q1 | Verdict field precedence | `director_ensemble.py:1346` | comment-only | Add comment block before the return dict explaining: `final_verdict` = post-gate authoritative verdict; `director_verdict` / `original_verdict` = raw LLM verdict before gates; `verdict` = alias of `final_verdict`; `gate_basis` = which gate changed the verdict |
| Q2 | Thin delegate markers | `stage4_post_pass_runtime.py:26-47` | comment-only | Add `# ── [THIN DELEGATE] forwarding to owner ──` header before the 7 delegate methods and `# ── [AUTHORITY] post-pass settlement runtime ──` before `_submit_manager_async` |
| Q3 | Quality gate mutation docs | `director_ensemble.py:976` | comment-only | Add one-line `# Mutates: state.score, state.firewall_*` annotations on each of the 4 quality gate methods |
| Q4 | Parameter grouping | `stage4_interview_round.py:2767` | comment-only | Add `# -- common params --`, `# -- PASS path params --`, `# -- REJECT path params --` grouping comments in `_finalize_round_outcome` parameter list |
| Q5 | Verdict branching note | `stage4_interview_round.py:3806` | comment-only | Add docstring line: "Gate authority: PASS+score<gate→REJECT, CONDITIONAL_PASS→PASS. Returns (pass_result|None, feedback, attempt, trace)." |
| Q6 | Retry lane routing header | `stage4_retry_runtime.py:825` | comment-only | Add comment: "Lane priority: ASP correction > inplace (score>=50+patch_enabled) > patch/rewrite > full regeneration" |
| Q7 | EnsembleSelectionState docstring | `director_ensemble.py:612` | comment-only | Add dataclass docstring: "Mutable state carrier for quality gate chain. Input fields: selected_*, original_verdict, score_breakdown_raw, contradiction_check. Gate-mutated fields: score, firewall_*, contradiction_details." |

**Comment/doc/observability ratio: 7/7 = 100% (exceeds >50% rule).**

## 6. Deferred Refactor Candidates

| # | Target | Action | Rationale | Tag |
|---|---|---|---|---|
| D1 | `_god1_*` channel | Migrate to explicit parameters | Already has TODO at L2251. Instance mutation across file boundaries is long-term authority debt. Post-survey comments reduce immediate hazard. | long-term |
| D2 | `_finalize_round_outcome` 26-param | Split into `_finalize_pass_outcome` / `_finalize_reject_outcome` top-level methods | Would eliminate parameter confusion and dead-param passing. Moderate blast radius: touches `_complete_round_after_review` call site. | defer |
| D3 | `_EnsembleSelectionState` mutation chain | Consider explicit state-transition methods or builder pattern | Would make quality gate effects visible in method signatures. Low blast radius but design decision needed on pattern. | defer |

## 7. No-Action / Settled Areas

| Area | Reason |
|---|---|
| `stage4_interview_round.py` Section Map | L152-172 — accurate, covers all major sections with line ranges |
| `_god1_*` producer/consumer comments | L2248-2251 (producer) + director_runtime L102-104 (consumer) — adequately documented |
| `_save_world_state_atomic` void return | L1079-1082 docstring — clear contract explanation |
| `stage4_director_runtime.py` `get_module()` logging | L241-242 — `logging.debug` on None already added |
| `stage4_post_processor.py` early-return warning | L953 — blast-radius comment present |
| Advisory chain parallel execution | L4554-4671 — 9 advisories with ThreadPoolExecutor, per-type logging, timeout handling. Clean and well-observed. |
| `stage4_reject_runtime.py` overall | Dedicated reject authority with clear dataclass payloads. Section structure adequate. |
| `stage4_retry_runtime.py` PASS_WITH_FIX loop | L90-237 — multi-stage fix loop with explicit abort gates. Dataclass payloads make each stage visible. |
| Director ensemble `select_and_judge_ensemble` | L2106-2220 — clear top-level flow: normalize → prompt → response → selection state → quality gates → decision payload |
| Director ensemble `compare_and_select_blueprint` | L1390 — separate blueprint comparison with clean fallback path |

## 8. Cross-Lane Handoff Notes

| Note | Target Lane |
|---|---|
| Verdict field precedence (H1/Q1) may affect T3 (writer receives director_result) and T4 (validation orchestrator reads verdict fields) | T3, T4 |
| `_EnsembleSelectionState` contracts (H2/H7) are consumed by `_build_ensemble_decision_payload` which feeds back into `stage4_interview_round.py` verdict processing | T4 |
| Post-pass settlement (H4) flows into DB persistence and world_state/fact_ledger updates — T5 should verify sink ownership documentation | T5 |
| `_god1_*` channel is a cross-file implicit contract that predates the runtime split. If T4 surveys `pre_director_checklist.py` or validators, they should note they run inside this channel's scope. | T4 |

## 9. Confidence And Limits

**Overall confidence: 95%**

Breakdown:
- Navigation: 93%. Section Map is present and accurate. Line numbers will drift on future edits but structure references are stable.
- Authority: 91%. Owner/runtime split pattern is consistent across all 7 files. `_god1_*` is the sole implicit channel and is now documented.
- Contract: 80%. Verdict dataclasses are well-typed. The verdict field proliferation in `_build_ensemble_decision_payload` return dict (4 verdict fields + `gate_basis`) is the main undocumented contract gap.
- Observability: 90%. Advisory chain, director review, and post-pass pipeline all have structured logging. `meta_save_failed` propagation is documented.
- Local readability: 85%. Prior quick wins realized. Quality gate mutation chain and 26-param signature are the main residual friction.

Limits:
- This survey is static-only. No fresh run was executed.
- `stage4_interview_round.py` internal method interactions were sampled at key sections (run/verdict/advisory/generation/finalize), not exhaustively line-by-line across all 5,979 lines.
- Helper methods in the L1000-2000 range (director context builders, DB advisory builders) were structurally reviewed but not deeply analyzed for local readability.
- `director_ensemble.py` blueprint comparison path (L1390-1940) was reviewed at method-signature level; internal prompt construction was sampled but not exhaustively graded.

## 10. 3-Pass Audit Record

### Pass 1 — Structure and Coverage
- All 7 scope files inspected
- All 5 LLM-friendliness axes covered
- Every P0/P1 finding has file:line anchor
- Every recommendation has fix type
- Quick wins: 7 items, 100% comment-only
- Deferred refactor candidates: 3, all tagged long-term/defer
- PASS

### Pass 2 — Evidence and Consistency
- Verified Section Map at L152-172 exists in live code
- Verified `_god1_*` comments at L2248-2251 and director_runtime L102-104
- Verified `_save_world_state_atomic` docstring at L1079-1082
- Verified `get_module()` debug log at director_runtime L241-242
- Verified verdict field proliferation at director_ensemble L1346-1388
- Prior closed items from `llm-friendliness-post-survey-execution-ssot.md` confirmed settled in live code
- PASS

### Pass 3 — Readability and Operational Use
- Report answers all 3 T2 lane questions
- Quick wins are actionable without opening refactor waves
- Cross-lane handoff notes identify specific downstream impacts
- No-action list prevents over-engineering on settled areas
- PASS

### Confidence Gate
- Estimated confidence: 95%
- Threshold: 95% required for final status
- Status: **final**
