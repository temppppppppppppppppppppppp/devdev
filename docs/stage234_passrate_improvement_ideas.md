# Stage 2/3/4 Pass-Rate Improvement Ideas (Practical)

## Goal
- Improve real pass rate of Stage 2/3/4 without turning the pipeline into a heavy over-engineered system.
- Keep current architecture principles:
  - Director remains final judge.
  - Patch mode remains available from score >= 50.
  - Focus on quality gain per additional token/call, not feature count.

## Observed Current State (Code-Based)

### Stage 2
- Patch mode trigger exists and is active:
  - `modules/core/stage2_preflight.py:482`
- Max attempts is fixed at 5 in preflight:
  - `modules/core/stage2_preflight.py:179`
- Quality gate is active (PASS -> REJECT if score < quality gate):
  - `modules/core/stage2_finalizer.py:181`
  - `modules/core/stage2_finalizer.py:191`
- Quota fallback can override to PASS (score 50 path):
  - `modules/core/stage2_finalizer.py:145`
  - `modules/core/stage2_finalizer.py:172`

### Stage 3
- Generator has patch mode trigger:
  - `modules/domain/agents/three_phase_blueprint_generator.py:169`
- Quality gate is active:
  - `modules/domain/agents/three_phase_blueprint_generator.py:278`
  - `modules/domain/agents/three_phase_blueprint_generator.py:286`
- On exhausted retries, generator may emit `PASS_WITH_WARNING`:
  - `modules/domain/agents/three_phase_blueprint_generator.py:332`
- Orchestrator currently accepts only strict PASS for success:
  - `modules/core/stage3_orchestrator.py:324`

### Stage 4
- Patch mode and quality gate are active:
  - `modules/core/stage4_interview_round.py:127`
  - `modules/core/stage4_interview_round.py:688`
- Feedback package for retry is richer than Stage 2/3:
  - `modules/core/stage4_interview_round.py:750`
  - `modules/core/stage4_interview_round.py:752`
- ChiefWriter actually consumes those fields for retry prompts:
  - `modules/domain/agents/chief_writer.py:594`
  - `modules/domain/agents/chief_writer.py:600`
- ASP is wired conditionally (`round_num >= 2`) and appended as extra candidate:
  - `modules/core/stage4_interview_round.py:229`
  - `modules/core/stage4_interview_round.py:251`

### TOT / MAD / Adaptive
- ToT, ASP, MAD are initialized in app bootstrap:
  - `main_a.py:1657`
  - `main_a.py:1664`
  - `main_a.py:1671`
- Stage4 context includes ASP only (not ToT/MAD):
  - `modules/core/stage4_context.py:44`
  - `modules/core/stage4_context.py:151`
- Adaptive strategy mapping references ToT/MAD/ASP:
  - `modules/core/adaptive_retry.py:486`
  - `modules/core/adaptive_retry.py:491`
- But runtime call-path usage of adaptive guidance in Stage 2/3/4 is effectively not wired.

## Practical Improvement Ideas (Prioritized)

## P0 (Low-Risk, Immediate ROI)

### P0-1. Normalize retry feedback schema across Stage 2/3 to Stage 4 level
- Why:
  - Stage 4 retries have structured signals (`score_breakdown`, `selection_reason`, `validation_warnings`) and therefore better targeted next attempts.
  - Stage 2/3 feedback is comparatively thinner.
- Idea:
  - Reuse Stage 4 style feedback envelope for Stage 2/3 reject payloads.
  - Keep fields optional for backward compatibility.
- Expected effect:
  - Better patch quality in retry loops with minimal architecture change.

### P0-2. Treat Stage 3 `PASS_WITH_WARNING` as controlled continuation mode
- Why:
  - Generator already emits `PASS_WITH_WARNING` (`three_phase_blueprint_generator.py:332`), but orchestrator accepts only strict `PASS` (`stage3_orchestrator.py:324`).
- Idea:
  - Allow a policy flag:
    - strict mode: current behavior.
    - practical mode: accept `PASS_WITH_WARNING` and mark downstream risk note.
- Expected effect:
  - Reduced avoidable fail-stop in Stage 3 with transparent quality marker.

### P0-3. Harden Stage 2 quota fallback semantics
- Why:
  - Current quota path can force PASS at score 50 (`stage2_finalizer.py:145`, `:172`) even under quality gate conditions.
- Idea:
  - Keep fallback, but classify it as explicit degraded outcome (`PASS_DEGRADED` or tagged PASS) and require stronger next-stage verification.
- Expected effect:
  - Preserves robustness under quota failures while lowering silent-quality debt.

### P0-4. Unify retry budget semantics to one visible config source
- Why:
  - Stage2 and Stage4 are effectively 5 tries, Stage3 uses `max_retries=4` call style in orchestrator (`stage3_orchestrator.py:439`) and different local semantics.
- Idea:
  - Keep same behavior, but expose one consistent config naming and per-stage override.
- Expected effect:
  - Fewer operator mistakes and clearer pass-rate tuning.

### P0-5. Fix feedback broadcast problem — route strategy-specific feedback to its owner only
- Why:
  - Current implementation broadcasts identical feedback to all 3 ensemble candidates.
  - Feedback includes strategy-specific signals (`선택된 전략: action`, `score_breakdown`, `selection_reason`) that are only relevant to the rejected candidate.
  - All candidates receive `[CRITICAL] Director REJECT 피드백 — 100% 반영 필수` prefix, forcing LLM to apply irrelevant corrections.
  - Evidence:
    - `blueprint_ensemble.py:180-196` — ThreadPoolExecutor submits same `feedback` to all 3 strategies.
    - `chief_writer.py:588` — `선택된 전략: {previous_attempt.get("strategy")}` included but broadcast to all.
    - `chief_writer.py:610` — `generate_ensemble()` passes single `enhanced_feedback` to all candidates.
- Idea:
  - Split feedback into two layers:
    - **Common feedback**: general Director notes applicable to any candidate (e.g., "연속성 위반", "분량 부족").
    - **Strategy-specific feedback**: score_breakdown, selection_reason, strategy-targeted corrections → only to the strategy that was rejected.
  - Non-selected strategies receive only common feedback + "이전 라운드에서 {strategy} 전략이 선택되었으나 불합격. 차별화된 접근 필요." one-liner.
- Expected effect:
  - Each candidate generates genuinely different retry output instead of all 3 converging on the same correction.
  - Higher diversity = higher chance that at least one candidate passes.

### P0-6. Single-candidate refinement mode (score >= 50)
- Why:
  - When score >= 50, the best candidate is close to passing. Regenerating all 3 from scratch wastes 2/3 of API calls.
  - Current patch mode already acknowledges score >= 50 is fixable, but still generates 3 full candidates on retry.
- Idea:
  - **Score >= 50 (any candidate)**: Enter single-candidate refinement mode.
    - Select the highest-scoring candidate.
    - Tie-breaking: choose the candidate whose reject reasons are easiest to fix (fewer structural issues, more surface-level corrections).
    - Give only this candidate iterative feedback across subsequent retry rounds.
    - Other 2 candidates are not regenerated (API cost → 1/3).
  - **Score < 50 (all candidates)**: Full 3-candidate regeneration with broadcast feedback (current behavior).
  - Director still judges the single refined candidate normally — no governance change.
- Expected effect:
  - API cost reduction: ~67% fewer generation calls per retry round when score >= 50.
  - Better convergence: focused refinement on a near-passing candidate instead of shotgun regeneration.
  - Compatible with patch mode: single-candidate refinement naturally feeds into existing patch logic.
- Implementation notes:
  - Stage 4: `stage4_interview_round.py` interview loop — add branch after Director scoring.
  - Stage 3: `blueprint_ensemble.py` — add equivalent branch in retry path.
  - Stage 2: `stage2_preflight.py` — apply same pattern to arc retry.
  - New field in feedback envelope: `refinement_mode: "single" | "full"` for downstream clarity.

## P1 (Targeted Intelligence Wiring, Not Always-On)

### P1-1. Keep ASP as first conditional intelligence module in all stages
- Why:
  - Stage4 already uses practical rule (`round_num >= 2`) and candidate append model.
- Idea:
  - Reuse same pattern for Stage2/3 only after second reject.
  - Never let ASP finalize; Director/final validator remains judge.
- Expected effect:
  - Quality improvement with bounded cost and low governance risk.

### P1-2. Add ToT only for structure failures
- Why:
  - Adaptive mapping already indicates structure-related errors -> ToT (`adaptive_retry.py:488`, `:489`).
- Idea:
  - Trigger once when reject reason bucket is structural (flow, dependency, sequence).
  - Do not chain ToT repeatedly in one stage attempt window.
- Expected effect:
  - Better rescue for structural collapse without runaway token burn.

### P1-3. Add MAD only for hard constraint conflicts
- Why:
  - Adaptive mapping links constraint/logical conflict -> MAD (`adaptive_retry.py:490`, `:491`).
- Idea:
  - Trigger once when constraints conflict across signals (blueprint/state/rules).
  - Keep MAD output as advisory input for rewrite, not direct verdict.
- Expected effect:
  - Better conflict resolution in edge cases while avoiding routine latency.

## P2 (Measurement First, Then Expansion)

### P2-1. Add reject-reason buckets as first-class metrics
- Buckets:
  - quality_below_gate
  - structure_error
  - constraint_violation
  - continuity_conflict
  - quota_degraded
- Expected effect:
  - You can decide objectively whether ToT/MAD/ASP are helping or just adding cost.

### P2-2. Run canary rollout before full enable
- Idea:
  - Enable P1 logic on limited episodes/projects first.
  - Compare pass-rate delta and token-cost delta per stage.
- Expected effect:
  - Prevents large-scale regression from globally wiring new modules.

## Recommended Rollout Order
1. **P0-5** feedback routing fix (broadcast → strategy-specific). Foundation for all other feedback improvements.
2. **P0-6** single-candidate refinement mode (score >= 50 → 1 candidate). Immediate API cost reduction.
3. **P0-1** retry feedback normalization (Stage2/3 → Stage 4 level schema).
4. **P0-2** Stage3 `PASS_WITH_WARNING` policy gate.
5. **P0-3** quota fallback tagging and downstream handling.
6. **P0-4** retry budget config unification.
7. **P1-1** ASP conditional reuse in Stage2/3.
8. **P1-2** ToT and **P1-3** MAD as single-shot conditional plugins.
9. **P2** metrics + canary before broad rollout.

## What To Avoid (Overengineering Traps)
- Do not run ToT + MAD + ASP always-on in every retry.
- Do not let auxiliary modules decide final PASS/REJECT.
- Do not add deep new architecture before reject-reason metrics are stabilized.
- Do not increase retries blindly without improving feedback quality first.

## Short Conclusion
- The best practical path is:
  1. **Fix feedback routing first** — stop broadcasting strategy-specific feedback to all candidates. This is the root cause of retry diversity collapse.
  2. **Single-candidate refinement** — score >= 50 means the candidate is close. Refine 1 instead of regenerating 3. Saves ~67% API cost per retry round.
  3. **Normalize feedback schema** — bring Stage 2/3 feedback up to Stage 4 level (structured fields).
  4. **Reuse ASP conditionally** — only after 2nd reject, as extra candidate.
  5. **Wire ToT/MAD by error type** — structural → ToT, constraint conflict → MAD. Once per retry window.
  6. **Measure before scaling** — reject-reason buckets + canary rollout.
- This gives higher pass rate with controlled cost and lower regression risk.
