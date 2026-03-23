# Q1-Q8 R2 Merge Audit

Date: 2026-03-23
Status: final (3-pass audited)
Document Type: Q1-Q8 R2 merge-audit report
Canonical Path: `docs/2026-03-23/q1-q8-r2-merge-audit.md`
Source Order: `docs/2026-03-23/q1-q8-r2-parallel-deep-survey-order.md`
Temp Mirror Path: none
Source Survey Docs:
- `docs/2026-03-23/opus/r2-q1-generation-quality.md`
- `docs/2026-03-23/opus/r2-q2-fix-retry.md`
- `docs/2026-03-23/opus/r2-q3-verdict-accuracy.md`
- `docs/2026-03-23/opus/r2-q4-feedback-fidelity.md`
- `docs/2026-03-23/opus/r2-q5-long-term-consistency.md`
- `docs/2026-03-23/opus/r2-q6-selective-retrieval.md`
- `docs/2026-03-23/opus/r2-q7-context-reception.md`
- `docs/2026-03-23/opus/r2-q8-logging-retention.md`
- `docs/2026-03-23/q1-q8-current-state-merge-audit.md`
- `docs/2026-03-23/pre-rerun-root-cause-merge-audit.md`
- `docs/2026-03-23/pre-rerun-root-cause-fix-cluster-execution-ssot.md`
- `docs/2026-03-23/console-log-max-display-post-audit-execution-ssot.md`
- `docs/2026-03-23/db-logging-integrity-post-audit-execution-ssot.md`
Commit State:
- Baseline Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
- Baseline Dirty Summary: `R2 lane reports were produced against a dirty 2026-03-23 workspace with docs/runtime/test edits and fresh-run artifacts present`
- Resume Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
- Resume Drift Summary: `same HEAD; merge audit rechecked live source for Q3 downstream verdict handling, Q8 Stage 2/3 DB parity, and current closure docs`

---

## 1. Executive Summary

The R2 bundle is now complete with this merge audit.

Merge result:
- `Q1` is mostly historical at this point. Its two dirty partial fixes were already absorbed and closed by the pre-rerun fix cluster.
- `Q2` is substantially improved and no longer a rerun blocker.
- `Q3` still contains one live correctness bug: `CONDITIONAL_PASS` from the V60.97 branch is not treated as positive downstream.
- `Q4` core fidelity work is resolved, but some operator/logging truncation remains on secondary paths.
- `Q5` remains a long-run structural axis, not a pre-rerun blocker.
- `Q6` observability fixes landed and made retrieval degradation interpretable; remaining issues are quality degraders, not blockers.
- `Q7` remains long-run structural and is not a near-term rerun blocker.
- `Q8` is partly stale as a queue guide because the large DB/console SSOTs are closed, but it still correctly identifies live Stage 2/3 parity gaps.

Overall merge verdict:
- `fresh-run-before-fix`: yes, technically
- `fix-first for ROI`: also yes

The highest-ROI remaining fixes before the next rerun are:
1. Q3 downstream `CONDITIONAL_PASS` recognition
2. Q8 Stage 2/3 `save_stage_attempt()` rationale parity
3. Q4/Q8 residual operator and JSONL truncation cleanup

## 2. Bundle Completion Check

Required lane reports were present:
- `docs/2026-03-23/opus/r2-q1-generation-quality.md`
- `docs/2026-03-23/opus/r2-q2-fix-retry.md`
- `docs/2026-03-23/opus/r2-q3-verdict-accuracy.md`
- `docs/2026-03-23/opus/r2-q4-feedback-fidelity.md`
- `docs/2026-03-23/opus/r2-q5-long-term-consistency.md`
- `docs/2026-03-23/opus/r2-q6-selective-retrieval.md`
- `docs/2026-03-23/opus/r2-q7-context-reception.md`
- `docs/2026-03-23/opus/r2-q8-logging-retention.md`

This merge audit fills the missing Codex synthesis layer required by the order document.

## 3. Axis Status Matrix

| Axis | R2 lane verdict | Merge verdict | Current operational meaning |
|---|---|---|---|
| Q1 | mixed delta, mostly non-blocking | partly stale, mostly absorbed | use only for residual generation-quality debt, not current rerun blocking |
| Q2 | core fix/retry fidelity improved | valid | no immediate blocker |
| Q3 | one ineffective fix + one new live bug | valid and urgent | highest-priority correctness residual |
| Q4 | core feedback fidelity resolved | valid with lower-severity residuals | not a rerun blocker, but secondary observability debt remains |
| Q5 | long-run structural | valid but deferred | not a near-term rerun blocker |
| Q6 | 4 fixes verified, 5 quality degraders remain | valid | rerun now yields interpretable retrieval evidence |
| Q7 | long-run structural | valid, one stale subclaim | defer after rerun |
| Q8 | DB/console wave mostly landed | partly stale as queue framing, still useful for residual parity gaps | keep only Stage 2/3 and residual logging/persistence gaps |

## 4. Stale And Shifted Findings

### 4.1 Q1 stale or absorbed

- `docs/2026-03-23/opus/r2-q1-generation-quality.md` correctly records `H-2` as resolved, but its two `partially-resolved (dirty)` items are no longer pending in the current state.
- The scene-detection and blueprint temporal-handoff fixes were already realized and closed under:
  - `docs/2026-03-23/pre-rerun-root-cause-fix-cluster-execution-ssot.md`
- Merge classification:
  - `scene detection false-positive`: absorbed by closed pre-rerun fix cluster
  - `blueprint time_flow contamination handoff`: absorbed by closed pre-rerun fix cluster

### 4.2 Q5 shifted framing

- `docs/2026-03-23/opus/r2-q5-long-term-consistency.md` already corrects the old "no atomicity" framing to `best-effort atomicity with snapshot rollback`.
- Current live source supports that shifted framing:
  - `modules/core/stage4_post_pass_runtime.py:1070`
  - `modules/core/stage4_post_processor.py:795`
- Merge classification:
  - keep as a structural consistency risk
  - do not treat as immediate absence of rollback or total persistence failure

### 4.3 Q7 stale subclaim

- `docs/2026-03-23/opus/r2-q7-context-reception.md` correctly marks the old Director `200K` claim as stale.
- Merge classification:
  - keep Q7 as long-run budget-pressure debt
  - drop the old "Director 200K hard cap" claim from any new action list

### 4.4 Q8 stale queue framing

- `docs/2026-03-23/opus/r2-q8-logging-retention.md` still reads partly like an execution guide for an active Stage 4 DB/console retention wave.
- That queue framing is stale because:
  - `docs/2026-03-23/console-log-max-display-post-audit-execution-ssot.md` is closed
  - `docs/2026-03-23/db-logging-integrity-post-audit-execution-ssot.md` is closed
- Merge classification:
  - keep only live residuals from Q8
  - do not reopen the broad closed Stage 4 DB/console waves as if they were still active

## 5. Still-Live Findings

### 5.1 Q3 live correctness residual

`docs/2026-03-23/opus/r2-q3-verdict-accuracy.md` is still live on its main remaining issue.

Source evidence:
- `modules/domain/agents/director_ensemble.py:1187`
- `modules/domain/agents/director_ensemble.py:1194`
- `modules/core/stage4_interview_round.py:3787`

Current behavior:
- `_apply_ensemble_quality_gates()` can leave `final_verdict = "CONDITIONAL_PASS"` in the V60.97 branch.
- `_process_verdict()` still treats only `PASS` and `PASS_WITH_FIX` as positive verdicts.
- Therefore the intended "keep CONDITIONAL_PASS if threshold passed" branch still falls through to the reject path downstream.

Merge classification:
- severity: P1
- type: `contract-cleanup`
- rerun effect: not guaranteed to trigger, but still the top correctness residual

### 5.2 Q8 Stage 3 DB rationale parity gap

Source evidence:
- `modules/core/stage3_orchestrator.py:1858`
- `modules/core/stage3_orchestrator.py:2624`

Current behavior:
- Stage 3 `save_stage_attempt()` calls still do not forward `selection_reason`, `verdict_reason`, `open_review`, `fix_scope_reasoning`, `runtime_advisory`, and `retry_directives`.

Merge classification:
- severity: P1
- type: `contract-cleanup`
- rerun effect: non-blocking, but keeps Stage 3 DB rows diagnostically thin

### 5.3 Q8 Stage 2 DB rationale parity gap

Source evidence:
- `modules/core/stage2_finalizer.py:2691`
- `modules/core/stage2_finalizer.py:2829`
- `modules/core/stage2_finalizer.py:2837`

Current behavior:
- Stage 2 `save_stage_attempt()` calls still omit the richer rationale fields.
- Stage 2 also still slices `reject_reason[:500]` before persistence.

Merge classification:
- severity: P1
- type: `contract-cleanup`
- rerun effect: non-blocking, but leaves Stage 2 rows thinner than Stage 4 rows

### 5.4 Q4 and Q8 residual logging / settlement truncation

Source evidence:
- `modules/core/stage4_reject_runtime.py:548`
- `modules/core/stage4_reject_runtime.py:568`
- `modules/core/stage4_reject_runtime.py:580`
- `modules/core/stage4_reject_runtime.py:604`
- `modules/core/stage4_interview_round.py:5369`
- `modules/core/stage4_interview_round.py:5370`
- `modules/core/stage4_interview_round.py:5434`
- `modules/core/stage4_interview_round.py:5436`
- `modules/core/stage3_orchestrator.py:2260`
- `modules/core/stage3_orchestrator.py:2261`
- `modules/core/stage3_orchestrator.py:2262`
- `modules/core/stage3_orchestrator.py:2263`

Current behavior:
- The core retry/reject guidance path is much better than R1.
- But secondary operator, session logger, and JSONL settlement paths still contain `[:100]`, `[:150]`, `[:200]`, `[:300]`, and `[:500]` caps.

Merge classification:
- severity: P2
- type: `observability-only`
- rerun effect: non-blocking, but still reduces post-run forensic quality

### 5.5 Q6 quality degraders that still persist

`docs/2026-03-23/opus/r2-q6-selective-retrieval.md` remains current on the following:
- NPC entity matching weakness
- hybrid RRF asymmetry
- work-focus substring false positives
- silent budget exhaustion in context packet assembly
- tier ordering / cap fragility

Merge classification:
- severity: mixed P1/P2
- type: mostly `contract-cleanup` or `observability-only`
- rerun effect: now interpretable, not opaque

## 6. Closed Or Already-Absorbed Findings

These should not be reopened as fresh execution waves from the R2 bundle:

- Q1 scene-detection false-positive fix
- Q1 blueprint temporal-handoff fix
- Q2 main feedback-fidelity fixes already landed
- Q4 core `rejection_reason` preservation and `contradiction_details` preservation
- Q6 warning and cache-invalidation fixes from `79f570f2`
- Q8 broad Stage 4 DB max-retention wave
- Q8 broad Stage 4 console max-display wave

Operational rule from this merge:
- treat the closed SSOTs as authority for "large wave completed"
- only spin up residual work if it is clearly live in source now

## 7. Pre-Rerun Fix Ranking

### Rank 1. Q3 downstream positive-verdict recognition

Reason:
- This is the only remaining live correctness bug in the R2 bundle that can directly distort verdict semantics.

Primary targets:
- `modules/domain/agents/director_ensemble.py`
- `modules/core/stage4_interview_round.py`

Recommended fix type:
- `contract-cleanup`

### Rank 2. Q8 Stage 2/3 `save_stage_attempt()` parity

Reason:
- This is the biggest remaining DB-truth asymmetry after the max-retention wave.
- It is small, bounded, and high-value for learning from failures.

Primary targets:
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage2_finalizer.py`

Recommended fix type:
- `contract-cleanup`

### Rank 3. Q4/Q8 residual operator and JSONL truncation cleanup

Reason:
- Not a logic blocker, but still costs evidence quality.
- Bounded and easy to verify.

Primary targets:
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage3_orchestrator.py`

Recommended fix type:
- `observability-only`

## 8. Deferred After Rerun

Keep deferred unless a corrected rerun still exposes them:

- Q5 long-run consistency architecture
- Q7 context-reception long-run budget pressure
- Q1 generation-quality cleanup items such as ensemble winner ranking and diversity/operator surfacing
- Q6 structural retrieval-quality cleanup that does not block interpretability

## 9. Operational Consequence

This R2 bundle does not justify another broad survey-first cycle before the next rerun.

It does justify one small residual fix cluster:
- Q3 downstream verdict semantics
- Q8 Stage 2/3 DB parity
- Q4/Q8 residual observability cleanup

After that, the next rerun should be more valuable than another deep survey round.

## 10. Confidence And Limits

Estimated confidence: **96%**

Why this is above the save gate:
- all eight R2 lane reports were re-read
- the missing merge layer is now materialized
- the most likely stale claims were checked against live source and current closure docs
- the live-source rechecks were focused on the current highest-value residuals

Limits:
- not every P2/P3 sentence in every lane was re-verified line-by-line
- current merge centers on current-state actionability, not on preserving every historical nuance from the lane reports
- fresh rerun evidence after the last residual fix cluster is still not part of this document

## 11. 3-Pass Audit Record

### Pass 1. Structure and Scope

- confirmed this document is a merge-audit, not an execution SSOT
- confirmed scope is the R2 bundle only
- confirmed no temp mirror is required

### Pass 2. Evidence and Consistency

- rechecked the missing merge-layer requirement in the order doc
- rechecked Q1 stale/absorbed claims against the closed pre-rerun fix cluster
- rechecked Q8 stale queue framing against the closed DB/console SSOTs
- rechecked live source for Q3 downstream verdict handling and Q8 Stage 2/3 parity gaps

### Pass 3. Execution and Readability

- reduced the bundle to stale, absorbed, live, and deferred findings
- ranked only current high-ROI residuals
- stated the operating consequence clearly: small residual fix cluster, then rerun
