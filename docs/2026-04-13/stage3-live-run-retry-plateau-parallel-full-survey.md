# Stage3 Live Run Retry Plateau Parallel Full Survey

- Date: 2026-04-13
- Scope: `000_260412_a` live Stage3 run follow-up, stopped during `ep2 retry 6/10`
- Mode: survey-only, parallel evidence collection across runtime log, console log, artifacts, DB sinks, validator/runtime code, and touched tests
- 3-pass audit: completed before save
- Confidence: 96%

## Scope

This survey answers one question: why did the live `Stage3` run spend `ep1` on `7` attempts and then plateau on `ep2` around repeated `66`-score rejects, despite the process still being alive.

This survey does not patch code. It fixes the fault family, severity, and likely execution route before any realization work.

## Evidence Sources

- Console run log: [0_temp.txt](/c:/Users/PC/Desktop/글도비/0_temp.txt)
- Session log: [session_20260412_231516.log](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/logs/session_20260412_231516.log)
- Stage2 tactical truth: [arc_001.txt](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/plans/arcs/arc_001.txt)
- Accepted Stage3 blueprint text: [blueprint_0001.txt](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/plans/blueprints/blueprint_0001.txt)
- Accepted Stage3 artifact JSON: [final_blueprint__dialogue_focused.json](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/logs/artifacts/stage3/ep_0001/attempt_07/final_blueprint__dialogue_focused.json)
- Runtime summaries:
  - [pass_rate_monitor.json](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/logs/pass_rate_monitor.json)
  - [quality_metrics.jsonl](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/logs/quality_metrics.jsonl)
  - [runtime_audit_summary.json](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/logs/runtime_audit_summary.json)
- DB sink truth: [project_data.db](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/project_data.db)
- Code paths:
  - [three_phase_blueprint_runtime.py](/c:/Users/PC/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py)
  - [unified_blueprint_validator.py](/c:/Users/PC/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py)
  - [blueprint_constraint_compiler.py](/c:/Users/PC/Desktop/글도비/modules/domain/agents/blueprint_constraint_compiler.py)
  - [validation_orchestrator.py](/c:/Users/PC/Desktop/글도비/modules/validation/validation_orchestrator.py)
  - [scoring_validator.py](/c:/Users/PC/Desktop/글도비/modules/validation/scoring_validator.py)
- Test contracts:
  - [test_blueprint_patch_mode.py](/c:/Users/PC/Desktop/글도비/tests/test_blueprint_patch_mode.py)
  - [test_stage3_clarity_density_wave1.py](/c:/Users/PC/Desktop/글도비/tests/test_stage3_clarity_density_wave1.py)

## Executive Summary

- `P0`: no crash or deadlock evidence
- `P1`: Stage3 is in a real retry plateau, not a hang
- `P1`: accepted Stage3 truth already drifted away from cleaner Stage2 tactical authority
- `P1`: the dominant waste is not raw LLM randomness but a control-plane pattern
  - advisory-quality issues still keep the local patch lane alive
  - evaluator parse fallback amplifies low-score plateau
  - in-flight retry evidence is under-persisted outside the session log
- Recommended next route: promote into existing Stage3 execution lanes, then apply fail-only hardening

## Findings

### 1. The live run was not hanging; it was spending cost inside a low-yield retry plateau

The process remained alive and kept advancing through `Phase 2` and `Phase 3`. The problem was not liveness. The problem was that `Stage3` kept reopening a low-value lane.

Evidence:

- `ep1` repeated `PASS_WITH_FIX unresolved after 3 patch attempts -> REJECT` and then only closed on attempt 7:
  - [0_temp.txt#L191](/c:/Users/PC/Desktop/글도비/0_temp.txt#L191)
  - [0_temp.txt#L261](/c:/Users/PC/Desktop/글도비/0_temp.txt#L261)
  - [0_temp.txt#L320](/c:/Users/PC/Desktop/글도비/0_temp.txt#L320)
  - [0_temp.txt#L367](/c:/Users/PC/Desktop/글도비/0_temp.txt#L367)
- `ep2` entered the same family again, then flattened at repeated `66` scores:
  - [0_temp.txt#L426](/c:/Users/PC/Desktop/글도비/0_temp.txt#L426)
  - [0_temp.txt#L452](/c:/Users/PC/Desktop/글도비/0_temp.txt#L452)
  - [0_temp.txt#L497](/c:/Users/PC/Desktop/글도비/0_temp.txt#L497)
  - [0_temp.txt#L519](/c:/Users/PC/Desktop/글도비/0_temp.txt#L519)
  - [0_temp.txt#L545](/c:/Users/PC/Desktop/글도비/0_temp.txt#L545)
  - [0_temp.txt#L571](/c:/Users/PC/Desktop/글도비/0_temp.txt#L571)
- Session log shows the runtime still making live calls and fallback evaluations rather than stalling:
  - [session_20260412_231516.log#L301](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/logs/session_20260412_231516.log#L301)
  - [session_20260412_231516.log#L345](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/logs/session_20260412_231516.log#L345)
  - [session_20260412_231516.log#L3430](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/logs/session_20260412_231516.log#L3430)

Conclusion:

- The operator symptom was “looks frozen.”
- The runtime truth was “still working, but inside a low-yield retry family.”

### 2. The accepted Stage3 blueprint already drifted away from Stage2 tactical authority

This is the most important content-truth finding. The run did not simply struggle and then settle on a clean output. The accepted `ep1` blueprint itself already carried a canonical truth drift.

Evidence:

- Stage2 tactical arc authority for this work is cleaner and explicitly anchored around `SW인베스트먼트`:
  - [arc_001.txt#L48](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/plans/arcs/arc_001.txt#L48)
  - [arc_001.txt#L56](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/plans/arcs/arc_001.txt#L56)
  - [arc_001.txt#L75](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/plans/arcs/arc_001.txt#L75)
- The accepted Stage3 blueprint text says `한정호그룹` in the opening integrated scenario:
  - [blueprint_0001.txt#L7](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/plans/blueprints/blueprint_0001.txt#L7)
- The accepted JSON artifact preserves the same drift:
  - [final_blueprint__dialogue_focused.json#L34](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/logs/artifacts/stage3/ep_0001/attempt_07/final_blueprint__dialogue_focused.json#L34)

This matters because the same live run later produced an entity-consistency reject telling the system to normalize `한진그룹` to `SW인베스트먼트`:

- [0_temp.txt#L279](/c:/Users/PC/Desktop/글도비/0_temp.txt#L279)
- [0_temp.txt#L281](/c:/Users/PC/Desktop/글도비/0_temp.txt#L281)

Inference:

- Stage2 is not the direct culprit here.
- Stage3 accepted an output that was already less canonical than the upstream tactical truth.

### 3. The entity truth seam looks over-compressed, not merely “model dumbness”

This finding is partly inferential, but the evidence is strong enough to elevate it.

Observed runtime symptom:

- A reject instruction insisted that `한진그룹` must be normalized to `SW인베스트먼트`:
  - [0_temp.txt#L279](/c:/Users/PC/Desktop/글도비/0_temp.txt#L279)
  - [0_temp.txt#L281](/c:/Users/PC/Desktop/글도비/0_temp.txt#L281)

Why this matters:

- `SW인베스트먼트` is a later operational vehicle in the tactical truth.
- Family-group / household authority in early episodes is a different narrative layer.
- Collapsing those layers into one canonical organization name causes misleading entity correction pressure.

Supporting signal:

- Stage3 context assembly already has an `episode_progression_packet` and institution truth surface, but it is still built through light extraction logic:
  - [blueprint_constraint_compiler.py#L122](/c:/Users/PC/Desktop/글도비/modules/domain/agents/blueprint_constraint_compiler.py#L122)
  - [blueprint_constraint_compiler.py#L787](/c:/Users/PC/Desktop/글도비/modules/domain/agents/blueprint_constraint_compiler.py#L787)
  - [blueprint_constraint_compiler.py#L897](/c:/Users/PC/Desktop/글도비/modules/domain/agents/blueprint_constraint_compiler.py#L897)
  - [blueprint_constraint_compiler.py#L968](/c:/Users/PC/Desktop/글도비/modules/domain/agents/blueprint_constraint_compiler.py#L968)

Conclusion:

- The observed entity failures are better explained as a Stage3 truth-routing seam than as pure candidate stupidity.

### 4. Advisory-only `scenario_density` still keeps the local patch lane alive

This is the clearest control-plane inefficiency inside the current contract.

Evidence from validator:

- `scenario_density` is still emitted with `advisory_only=True` and `director_focus=False`, but also carries `local_sentence` patch targets:
  - [unified_blueprint_validator.py#L2346](/c:/Users/PC/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py#L2346)
  - [unified_blueprint_validator.py#L2367](/c:/Users/PC/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py#L2367)
  - [unified_blueprint_validator.py#L2388](/c:/Users/PC/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py#L2388)
  - [unified_blueprint_validator.py#L2415](/c:/Users/PC/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py#L2415)
  - [unified_blueprint_validator.py#L2422](/c:/Users/PC/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py#L2422)
  - [unified_blueprint_validator.py#L2436](/c:/Users/PC/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py#L2436)

Evidence from runtime:

- advisory-only residuals can preserve low-score PASS posture and surface a `quality_gate_soft_override`:
  - [three_phase_blueprint_runtime.py#L1374](/c:/Users/PC/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py#L1374)
  - [three_phase_blueprint_runtime.py#L1402](/c:/Users/PC/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py#L1402)
  - [three_phase_blueprint_runtime.py#L1785](/c:/Users/PC/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py#L1785)
- when patch attempts exhaust, the runtime still adopts the latest patched blueprint and continues retrying:
  - [three_phase_blueprint_runtime.py#L1861](/c:/Users/PC/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py#L1861)
  - [three_phase_blueprint_runtime.py#L1865](/c:/Users/PC/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py#L1865)

Evidence from tests:

- current tests explicitly preserve advisory-only low-score behavior and local-sentence repair posture:
  - [test_blueprint_patch_mode.py#L409](/c:/Users/PC/Desktop/글도비/tests/test_blueprint_patch_mode.py#L409)
  - [test_blueprint_patch_mode.py#L1064](/c:/Users/PC/Desktop/글도비/tests/test_blueprint_patch_mode.py#L1064)
  - [test_blueprint_patch_mode.py#L1118](/c:/Users/PC/Desktop/글도비/tests/test_blueprint_patch_mode.py#L1118)
  - [test_stage3_clarity_density_wave1.py#L370](/c:/Users/PC/Desktop/글도비/tests/test_stage3_clarity_density_wave1.py#L370)

Conclusion:

- Stage3 already hard-blocks structural families such as `opening_anchor`, `scene_completeness`, and `episode_progression`.
- The remaining waste comes from advisory-quality families that still trigger concrete local patch loops with poor payoff.

### 5. Evaluator JSON parse fallback amplifies the plateau

The repeated low-score band was not coming from one clean LLM evaluation path. The session log shows recurrent evaluator parse failures, followed by Python fallback.

Evidence:

- repeated session warnings:
  - [session_20260412_231516.log#L586](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/logs/session_20260412_231516.log#L586)
  - [session_20260412_231516.log#L587](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/logs/session_20260412_231516.log#L587)
  - [session_20260412_231516.log#L751](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/logs/session_20260412_231516.log#L751)
  - [session_20260412_231516.log#L752](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/logs/session_20260412_231516.log#L752)
  - [session_20260412_231516.log#L3429](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/logs/session_20260412_231516.log#L3429)
  - [session_20260412_231516.log#L3430](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/logs/session_20260412_231516.log#L3430)
- scoring code falls back on evaluation failure:
  - [scoring_validator.py#L316](/c:/Users/PC/Desktop/글도비/modules/validation/scoring_validator.py#L316)
  - [scoring_validator.py#L318](/c:/Users/PC/Desktop/글도비/modules/validation/scoring_validator.py#L318)
  - [scoring_validator.py#L320](/c:/Users/PC/Desktop/글도비/modules/validation/scoring_validator.py#L320)
- validation orchestrator exits early on clear scores and treats that as cost saved:
  - [validation_orchestrator.py#L1029](/c:/Users/PC/Desktop/글도비/modules/validation/validation_orchestrator.py#L1029)
  - [validation_orchestrator.py#L1030](/c:/Users/PC/Desktop/글도비/modules/validation/validation_orchestrator.py#L1030)

Conclusion:

- Fallback is not just noisy telemetry.
- In this live run, it likely contributed directly to the repeated `56 -> 59 -> 66 -> 66 -> 66` plateau family.

### 6. In-flight S3 failure persistence is sparse; the session log is more authoritative than the summary sinks during the active run

This is an observability finding, not the primary content bug, but it matters operationally.

Evidence:

- DB sink truth for this project currently shows:
  - `stage_attempts = 4`
  - `director_selections = 4`
  - `attempt_raw_rationale = 0`
  - no `session_decisions` table
  - no `episode_production` table
- The only persisted Stage3 attempt row is the final `ep1 attempt 7 PASS 92` record.
- `runtime_audit_summary.json` still says Stage3 live session is absent:
  - [runtime_audit_summary.json#L169](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/logs/runtime_audit_summary.json#L169)
  - [runtime_audit_summary.json#L170](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/logs/runtime_audit_summary.json#L170)
- Yet the session log shows the live S3 run was active and advancing.

Conclusion:

- During interrupted or in-flight Stage3 runs, the session log is the most authoritative sink.
- DB and summary sinks are currently too sparse to stand alone for live retry diagnosis.

## What This Survey Rejects

- It is not primarily a `Stage2` tactical failure.
- It is not a pure `model non-determinism` story.
- It is not a true runtime deadlock or UI freeze.

## Recommended Execution Promotion

Promote this survey into the existing Stage3 execution queue rather than opening a brand-new owner lane.

Recommended targets:

- [0_0-stage3-contract-tightening-remediation-execution-ssot.md](/c:/Users/PC/Desktop/글도비/docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md)
- [0_0-stage3-partial-fix-hardening-remediation-execution-ssot.md](/c:/Users/PC/Desktop/글도비/docs/2026-04-07/0_0-stage3-partial-fix-hardening-remediation-execution-ssot.md)
- [0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md](/c:/Users/PC/Desktop/글도비/docs/2026-04-02/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md)

Recommended fail-only patch themes:

- strengthen Stage3 institution/entity truth pins so family-group authority is not over-collapsed into downstream vehicles such as `SW인베스트먼트`
- suppress low-yield advisory-driven `inplace` loops for repeated `scenario_density` and similar soft families
- harden evaluator-fallback handling when the same low-score family repeats after parse failures
- improve in-flight Stage3 failure sink surfacing so stop/go decisions do not depend almost entirely on the session log

## Final Judgment

This run exposed a real `Stage3 retry-efficiency` problem, but the root is still narrow enough for a fail-only patch tranche.

The most important correction is conceptual:

- The live problem is not “Sonnet is slow” or “the run froze.”
- The live problem is “Stage3 accepted drifted truth too easily, then spent too much cost trying to locally rescue advisory-quality candidates inside a fallback-amplified retry lane.”
