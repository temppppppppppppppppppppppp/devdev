# Stage234 Feedback Routing Compact Survey

Date: 2026-04-12
Status: final
Scope: `Stage2` Arc ensemble retry feedback, `Stage3` Blueprint ensemble retry feedback, `Stage4` manuscript ensemble retry feedback
Method: live code inspection + targeted contract trace
3-Pass Audit: completed
Estimated Confidence: 97%

## 1. Intent

Decide whether `Stage2/3/4` currently deliver feedback that is appropriately matched to each candidate and whether a bounded patch tranche is justified before the next expensive fresh run.

## 2. Baseline Findings

- `Stage2`, `Stage3`, and `Stage4` all use an `ensemble-first, bespoke-later` pattern.
- First-round ensemble generation is still mostly driven by one shared feedback block, not per-candidate bespoke feedback.
- Retry and patch flows do carry progressively more specific feedback, but the precision differs by stage.
- `Stage4` has the highest ROI for a bounded patch because runtime cost is highest there and current retry feedback still collapses too much context into one shared `director_feedback` plus one targeted `strategy_specific_feedback`.

## 3. Stage-by-Stage Readout

### Stage2

- First ensemble run is shared-feedback dominant.
- Retry passes a shared `feedback` block to all Arc candidates and only adds `strategy_specific_feedback` to the previously selected strategy.
- Patch mode already narrows to one strategy, so selected-Arc remediation is reasonably specific once the lane leaves full ensemble generation.

Evidence:

- [four_phase_arc_runtime.py](C:/Users/PC/Desktop/글도비/modules/domain/agents/four_phase_arc_runtime.py)
- [arc_ensemble.py](C:/Users/PC/Desktop/글도비/modules/domain/agents/arc_ensemble.py)
- [stage2_orchestrator.py](C:/Users/PC/Desktop/글도비/modules/core/stage2_orchestrator.py)

### Stage3

- First ensemble run is also shared-feedback dominant.
- Retry state is richer than Stage2: previous selected strategy, selection reason, reject feedback, fix scope, and candidate advisories are already preserved.
- Retry injection is therefore materially better than Stage2, but it still fans back into one shared attempt feedback block plus one strategy-focused block.

Evidence:

- [three_phase_blueprint_runtime.py](C:/Users/PC/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py)
- [blueprint_ensemble.py](C:/Users/PC/Desktop/글도비/modules/domain/agents/blueprint_ensemble.py)
- [stage3_orchestrator.py](C:/Users/PC/Desktop/글도비/modules/core/stage3_orchestrator.py)

### Stage4

- First ensemble run is shared-feedback dominant.
- Retry, patch, and inplace patch paths are more elaborate than Stage2/3, but the common regenerate path still uses one shared `director_feedback` plus one targeted `strategy_specific_feedback`.
- `previous_attempt` already preserves enough selection and reject metadata to support a bounded `per-strategy feedback map` upgrade.
- This is the best first patch target because the stage is most expensive and the current collapse from structured retry evidence into one shared text block is the highest-value precision loss.

Evidence:

- [stage4_retry_runtime.py](C:/Users/PC/Desktop/글도비/modules/core/stage4_retry_runtime.py)
- [stage4_reject_runtime.py](C:/Users/PC/Desktop/글도비/modules/core/stage4_reject_runtime.py)
- [stage4_interview_round.py](C:/Users/PC/Desktop/글도비/modules/core/stage4_interview_round.py)
- [chief_writer.py](C:/Users/PC/Desktop/글도비/modules/domain/agents/chief_writer.py)

## 4. Recommendation

Proceed with a bounded cross-stage feedback-routing tranche in this order:

1. `Stage4`: introduce `strategy_feedback_map` for retry ensemble generation.
2. `Stage3`: reuse `candidate_advisories` plus retry state to build the same map shape.
3. `Stage2`: reuse quality/advisory flags to build a lighter version of that map.
4. Optional later follow-up: add candidate self-report evidence so Director can see what each candidate believes it addressed.

## 5. Guardrails

- Do not replace the existing shared `director_feedback`; keep it as the common hard-constraint layer.
- Do not let Python grade candidate self-report as truth; it can only be advisory evidence for Director.
- Keep backward compatibility with the current `strategy_specific_feedback` string until all three stages consume the map safely.
- Keep this as a routing-layer tranche, not a broad prompt rewrite or stage-architecture rewrite.

## 6. Operating Consequence

The compact execution move is justified.

- No new broad survey is needed.
- No new queue topic is needed.
- The existing `0_0-stage234-cross-stage-contract-normalization-remediation` lane can absorb this tranche.
