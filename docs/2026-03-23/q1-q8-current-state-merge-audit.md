Date: 2026-03-23
Status: final (3-pass audited)
Document Type: Q1-Q8 merge-audit report
Canonical Path: `docs/2026-03-23/q1-q8-current-state-merge-audit.md`
Source Order: `docs/2026-03-23/q1-q8-current-state-parallel-deep-survey-order.md`
Temp Mirror Path: none

---

# Q1-Q8 Current State Merge Audit

## 1. Executive Summary

8개 Opus TF deep-dive 결과를 live workspace에 다시 대조한 결과, 이번 배치의 결론은 다음과 같다.

- `Q1~Q8` 전수조사 자체는 유효하다.
- 다만 **stale claim 4건**, **shifted claim 2건**, **confidence gate 위반 2건**이 섞여 있다.
- fresh run 재시도 전에 바로 수정해야 하는 축은 **Q3 / Q4 / Q6**이다.
- **Q8**은 이미 active execution SSOT 2건으로 대부분 흡수되고 있다.
- **Q5 / Q7**은 위험 자체는 유효하지만 장기-run 전제와 구조 리팩토링 성격이 강해서, 이번 rerun 직전 선수정 축으로는 한 단계 낮춘다.

전체 판정:
- `fresh-run-before-fix`: **no**
- 이유:
  - Q3 `LLM-Director 정합성 불일치`
  - Q4 feedback loss
  - Q6 retrieval silent degradation
  - Q8 observability / retention parity gaps

## 2. Axis Status Matrix

| Axis | Source Doc | Doc Status After Audit | Confidence | Merge Verdict |
|---|---|---|---|---|
| Q1 | `docs/2026-03-23/opus/q1-generation-quality-deep-dive.md` | final 유지 | 96% | mostly valid, 1 stale |
| Q2 | `docs/2026-03-23/opus/q2-fix-retry-deep-dive.md` | final 유지 | 95% | valid, 1 stale |
| Q3 | `docs/2026-03-23/opus/q3-verdict-accuracy-deep-dive.md` | final 유지 | 95% | high-priority pre-rerun |
| Q4 | `docs/2026-03-23/opus/q4-feedback-loop-deep-dive.md` | final 유지 | 96% | high-priority pre-rerun |
| Q5 | `docs/2026-03-23/opus/q5-long-term-consistency-deep-dive.md` | provisional로 정정 | 94% | mixed, 2 shifted/stale |
| Q6 | `docs/2026-03-23/opus/q6-selective-retrieval-deep-dive.md` | final 유지 | 95% | high-priority pre-rerun |
| Q7 | `docs/2026-03-23/opus/q7-context-reception-deep-dive.md` | provisional로 정정 | 94% | long-run structural |
| Q8 | `docs/2026-03-23/opus/q8-logging-retention-deep-dive.md` | final 유지 | 96% | largely absorbed by active SSOTs |

## 3. Stale / Shifted Findings

### 3.1 Stale

1. `Q1 H-2 / Q2 H-3` Stage 3 pass rate >100% mismatch
- stale
- live code at `modules/domain/agents/three_phase_blueprint_generator.py:254-260` already uses `phase3_pass + phase3_reject` as terminal denominator

2. `Q5 P1-7` growth_keywords hardcoded mojibake / broken severity downgrade
- stale as a bug claim
- live code at `modules/validation/continuity_validator.py:1009-1016` already has restored Korean keywords
- remaining issue is parameterization/configurability, not mojibake breakage

3. `Q5 current-state linkage to situation report risk register`
- stale by dependency
- the earlier situation report still carried pre-fix wording, but current live code no longer supports that exact bug framing

4. `Q8` 일부 Stage 4 DB retention 문제 서술
- partially stale in severity framing
- Stage 4 raw retention and detail columns are already expanded by the active DB logging wave
- remaining gap is more about Stage 2/3 parity and caller-side truncation than Stage 4 total absence

### 3.2 Shifted

1. `Q5 P0-1` no cross-system atomicity
- shifted, not refuted
- live code now has `_save_world_state_atomic()` and rollback handling in `modules/core/stage4_post_pass_runtime.py:1070` and `modules/core/stage4_post_processor.py:795`
- remaining risk is `best-effort atomicity / rollback-based consistency`, not total absence of atomic protection

2. `Q8` Stage 2/3 DB rationale gap
- shifted toward existing active queue
- live code still shows Stage 2/3 `save_stage_attempt()` parity gaps, but this is not a fresh new queue item; it belongs under the already-active DB logging max-retention item

## 4. Active Queue Absorption Map

### 4.1 Already Covered by Active SSOTs

Covered by [db-logging-integrity-post-audit-execution-ssot.md](/c:/Users/User/Desktop/글도비/docs/2026-03-23/db-logging-integrity-post-audit-execution-ssot.md):
- Q8 caller-side DB truncation (`base_agent.py`, Stage 2/3/4 rationale persistence)
- Stage 4 detail/raw payload retention
- DB-side max-retention parity work

Covered by [console-log-max-display-post-audit-execution-ssot.md](/c:/Users/User/Desktop/글도비/docs/2026-03-23/console-log-max-display-post-audit-execution-ssot.md):
- Q8 console truncation
- advisory/operator max-display
- score/adaptive provenance visibility

### 4.2 Not Yet Covered by Active SSOTs

These remain the main pre-rerun code-fix candidates:
- Q3 verdict-accuracy chain
- Q4 feedback-loop fidelity
- Q6 silent retrieval degradation

## 5. Pre-Fresh-Run Fix Ranking

### Rank 1. Q3 Verdict Accuracy

Primary file:
- `modules/domain/agents/director_ensemble.py`

Why first:
- directly tied to the observed `LLM-Director 정합성 불일치`
- fresh run failure evidence already points here
- not merely observability; this is decision-path correctness

Priority cluster:
- V60.97 swap re-evaluation / unconditional reset path
- adaptive decision guard / error handling
- `ep_type` forwarding

Merge classification:
- `fix before rerun`

### Rank 2. Q4 Feedback Loop Fidelity

Primary files:
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_retry_runtime.py`

Why second:
- even if verdict path is fixed, the next generation round still loses corrective signal if `rejection_reason` and `contradiction_details` keep shrinking
- directly affects repair convergence

Priority cluster:
- preserve original `rejection_reason`
- reduce/avoid contradiction detail shrink
- remove multi-layer truncation in re-audit handoff

Merge classification:
- `fix before rerun`

### Rank 3. Q6 Retrieval Silent Degradation

Primary files:
- `modules/core/vec_memory.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/context_advisor.py`

Why third:
- a fresh run can look "successful" while actually running on degraded retrieval
- at minimum, observability fixes must land before rerun

Priority cluster:
- multi-query fallback warning
- advisor fallback warning
- embedding cache invalidation on model change
- slot truncation before priority sort

Merge classification:
- `minimum observability fix before rerun`

## 6. Deferred After Rerun

### Q5 Long-Term Consistency
- keep as structural follow-up
- some findings are real, but the report is provisional and partly shifted
- prioritize after a corrected rerun or longer-run test

### Q7 Context Reception
- keep as structural follow-up
- real long-run budget and truncation concerns
- but current document is provisional and most claims are long-run / high-episode scenarios rather than immediate rerun blockers

### Q1 Generation Quality
- most of Q1 is either already healthy or overlaps with Q3/Q4
- pass-rate mismatch claim is stale
- leave as lower priority unless rerun still shows generation collapse after Q3/Q4 fixes

## 7. Recommended Immediate Synthesis

The next Codex-controlled action should not be a full refactor wave.

It should be a bounded pre-rerun execution synthesis with three components:

1. `Q3 verdict accuracy pre-rerun fixes`
2. `Q4 feedback-fidelity pre-rerun fixes`
3. `Q6 retrieval observability pre-rerun fixes`

And a note that:
- `Q8` work is already in the active queue and should not spawn a duplicate execution SSOT
- `Q5/Q7` stay deferred unless a corrected rerun still fails in those dimensions

## 8. Governance Corrections Applied

Already corrected in live docs:
- `Q5` report status lowered to provisional
- `Q7` report status lowered to provisional

Still to keep in mind:
- no action-bearing promotion should use stale Q1/Q2 pass-rate claims
- Q5 atomicity wording should be treated as `best-effort atomicity gap`, not `no atomicity at all`

## 9. Confidence And Limits

Estimated confidence: **96%**

Basis:
- all 8 reports were inspected
- high-severity cross-axis findings were rechecked against live code
- stale claims were directly verified in source
- active queue absorption was checked against current execution SSOTs and queue state

Residual limits:
- not every P2/P3 item was rechecked line by line
- Q5/Q7 are still partly long-run hypothetical without a corrected rerun
- final execution synthesis is not created in this document

## 10. 3-Pass Audit Record

### Pass 1. Inventory
- confirmed all 8 terminal reports arrived
- collected status, confidence, and fresh-run gating from each report

### Pass 2. Live Recheck
- rechecked high-severity and likely stale items against live code
- confirmed stale pass-rate claims, stale growth_keywords bug framing, and shifted atomicity framing

### Pass 3. Merge Classification
- grouped findings into:
  - absorbed by active SSOT
  - fix before rerun
  - minimum observability before rerun
  - deferred after rerun
- produced a single rerun-oriented ranking
