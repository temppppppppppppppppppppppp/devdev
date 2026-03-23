Date: 2026-03-23
Document Type: evidence manifest
Axis: Q2 — fix/retry quality
Terminal: T2

## Source Anchors

### Stage 4 Retry Runtime
| Finding | File | Line(s) | Evidence Type |
|---|---|---|---|
| Re-audit feedback truncation | `modules/core/stage4_retry_runtime.py` | 600, 602 | live source |
| PASS_WITH_FIX loop bounded at max_fix=3 | `modules/core/stage4_retry_runtime.py` | 107, 119 | live source |
| Iteration gate: empty feedback → abort | `modules/core/stage4_retry_runtime.py` | 340-360 | live source |
| Iteration gate: fix_scope partial/full → abort | `modules/core/stage4_retry_runtime.py` | 382-389 | live source |
| Patch guard: min length | `modules/core/stage4_retry_runtime.py` | 478-498 | live source |
| Patch guard: preserve ratio | `modules/core/stage4_retry_runtime.py` | 500-526 | live source |
| Re-audit verdict: PASS + quality floor | `modules/core/stage4_retry_runtime.py` | 670-685 | live source |
| Re-audit verdict: PASS_WITH_FIX → continue | `modules/core/stage4_retry_runtime.py` | 710-723 | live source |
| Re-audit verdict: REJECT → break | `modules/core/stage4_retry_runtime.py` | 725-737 | live source |
| Finalization: PASS_WITH_FIX exhausted → adopt latest | `modules/core/stage4_retry_runtime.py` | 767-775 | live source |
| Retry lane routing: inplace/patch/rewrite | `modules/core/stage4_retry_runtime.py` | 825-886 | live source |
| Inplace retry lane: guard checks | `modules/core/stage4_retry_runtime.py` | 888-949 | live source |
| Patch/rewrite retry lane | `modules/core/stage4_retry_runtime.py` | 951-1016 | live source |
| ASP correction: round>=2 | `modules/core/stage4_retry_runtime.py` | 1018-1051 | live source |

### Three-Phase Blueprint Runtime
| Finding | File | Line(s) | Evidence Type |
|---|---|---|---|
| total_attempts increment (per episode) | `modules/domain/agents/three_phase_blueprint_runtime.py` | 162 | live source |
| Retry strategy feedback: score breakdown [:1200] | `modules/domain/agents/three_phase_blueprint_runtime.py` | 187-188 | live source |
| Inplace patch threshold: retry>0, fix_scope not partial/full, score>=inplace_threshold | `modules/domain/agents/three_phase_blueprint_runtime.py` | 340-345 | live source |
| Phase 3 quality gate: PASS + score<90 → REJECT | `modules/domain/agents/three_phase_blueprint_runtime.py` | 681-686 | live source |
| Reject state: double-count path (phase3_pass at 1106, phase3_reject at 976) | `modules/domain/agents/three_phase_blueprint_runtime.py` | 976, 1106 | live source |
| Continuity reject: phase3_reject increment | `modules/domain/agents/three_phase_blueprint_runtime.py` | 526 | live source |
| Validation reject: phase3_reject increment | `modules/domain/agents/three_phase_blueprint_runtime.py` | 1152 | live source |
| Terminal failure: emergency fallback score>=REWRITE | `modules/domain/agents/three_phase_blueprint_runtime.py` | 1062-1072 | live source |
| Terminal failure: feedback log [:200] | `modules/domain/agents/three_phase_blueprint_runtime.py` | 1077 | live source |
| Generate entry: max_retries=9, total 10 tries | `modules/domain/agents/three_phase_blueprint_runtime.py` | 1305, 1335 | live source |

### Three-Phase Blueprint Generator
| Finding | File | Line(s) | Evidence Type |
|---|---|---|---|
| Stats init: total_attempts, phase3_pass, phase3_reject | `modules/domain/agents/three_phase_blueprint_generator.py` | 58-62 | live source |
| Pass rate calculation: phase3_pass / (pass+reject) | `modules/domain/agents/three_phase_blueprint_generator.py` | 257-262 | live source |

### Chief Writer
| Finding | File | Line(s) | Evidence Type |
|---|---|---|---|
| regenerate_with_feedback: builds enhanced feedback + strategy hints → generate_ensemble() | `modules/domain/agents/chief_writer.py` | 946-1065 | live source |
| inplace_patch: LLM 1-call fix, temperature=0.3 | `modules/domain/agents/chief_writer.py` | 1792-1837 | live source |
| patch_with_feedback: PATCH_MODE_PROMPT + single_strategy bounded regen | `modules/domain/agents/chief_writer.py` | 1955-2060 | live source |
| Strategy bias: QR-3 lookback=20 win rate adjustment | `modules/domain/agents/chief_writer.py` | 120-172 | live source |

### Stage 2 Finalizer
| Finding | File | Line(s) | Evidence Type |
|---|---|---|---|
| PASS_WITH_FIX loop entry | `modules/core/stage2_finalizer.py` | 760-761 | live source |
| Loop implementation | `modules/core/stage2_finalizer.py` | 2120-2180 | live source |
| Fix instruction resolution | `modules/core/stage2_finalizer.py` | 2182-2203 | live source |
| Patch application | `modules/core/stage2_finalizer.py` | 2205-2229 | live source |
| Patch analysis (guards + arithmetic + pressure) | `modules/core/stage2_finalizer.py` | 2231-2299 | live source |

### Stage 4 Interview Round (supporting)
| Finding | File | Line(s) | Evidence Type |
|---|---|---|---|
| _evaluate_pass_with_fix_contract | `modules/core/stage4_interview_round.py` | 1669-1692 | live source |
| _enforce_pass_with_fix_contract (downgrade path) | `modules/core/stage4_interview_round.py` | 1728-1767 | live source |
| _extract_fix_feedback (60-line assembly) | `modules/core/stage4_interview_round.py` | 5083-5142 | live source |
| _get_inplace_success_rate (PF-4 telemetry) | `modules/core/stage4_interview_round.py` | 226-252 | live source |

### Director Ensemble (referenced, not primary)
| Finding | File | Line(s) | Evidence Type |
|---|---|---|---|
| V60.97 swap block | `modules/domain/agents/director_ensemble.py` | 889-896 | fresh-run report P1-1 |

### Fresh Run Evidence
| Finding | Source | Evidence Type |
|---|---|---|
| Ep5 REJECT cascade (V60.97) | `docs/2026-03-23/fresh-run-3pass-audit-report.md` P1-1 | post-run audit |
| Ep6 7-retry storm | `docs/2026-03-23/fresh-run-3pass-audit-report.md` P1-2 | post-run audit |
| Pass rate > 100% (166.7%, 185.7%) | `docs/2026-03-23/fresh-run-3pass-audit-report.md` P3-2 | post-run audit |
| TF-H patch 7 rounds length gap | `docs/2026-03-23/fresh-run-3pass-audit-report.md` P1-3 | post-run audit |

## Inventory Notes

- Total files read in primary scope: 4
- Total supporting files read: 2 (stage4_interview_round.py, three_phase_blueprint_generator.py)
- Context docs read: 9 (per survey order Section 9)
- No evidence artifacts generated (live source inspection only)
- All line numbers verified against live workspace at baseline commit `a3b9a286`
