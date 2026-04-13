# S2 S3 S4 Producer Smarts Bounded 3-Pass Audit

- Date: 2026-04-13
- Scope: current `main@32d6f0c8` static re-audit of the bounded `s2-s3-s4` producer-smart tranche that now spans Stage2 arc candidate scoring, Stage3 blueprint candidate admission, and Stage4 manuscript candidate admission
- Mode: survey-only, 3-pass re-audit; no new queue lane opened in this document turn
- Canonical Path: `docs/2026-04-13/s2-s3-s4-producer-smarts-bounded-3pass-audit.md`
- Baseline Commit: `32d6f0c8b56898fd8a370ae13684043d4cfda91a`
- Baseline Dirty Summary: `dirty: active Stage3 queue docs/temp mirrors, live 000_260412_a run artifacts, local provider/model edits, and bounded s2-s3-s4 producer-smarts code/tests already present`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none during this audit`
- Side-Effect Coverage: code, targeted tests, queue anchors, and operator-visible log surfaces inspected; no queue membership, DB schema, or runtime artifact truth was mutated in this audit
- Confidence: `97%`

## Purpose

This audit answers one bounded question:

- did the recent `s2-s3-s4` producer-smart tranche land coherently enough to justify the next live proof step, and what residual risks remain after the landing

This is an audit document, not a new execution SSOT.

This document does not open a new queue family.

## Evidence Anchors

Prior authority / queue anchors:

- `docs/2026-04-13/stage3-ep8-cw-director-root-cause-parallel-survey.md`
- `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
- `docs/2026-04-01/active-temp-execution-roadmap.md`
- `docs/2026-04-13/stage3-cross-pc-proof-rerun-handoff-context.md`

Current code owners:

- `modules/core/scene_obligation_heuristics.py`
- `modules/domain/agents/arc_ensemble.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/chief_writer.py`
- `modules/core/writer_template.py`

Targeted validation shards:

- `tests/test_arc_ensemble_lane_a.py`
- `tests/test_blueprint_ensemble_generate_ensemble.py`
- `tests/test_chief_writer_candidate_lane_f.py`
- `tests/test_chief_writer_generate_ensemble_lane_b.py`
- `tests/test_stage23_stage4_readiness_wave1.py`
- `tests/test_blueprint_patch_mode.py`

## Executive Summary

- No fresh `P0/P1` reopen was found inside the bounded `s2-s3-s4` producer-smart tranche.
- The tranche landed as a real upstream tightening, not cosmetic logging:
  - Stage2 now distinguishes `mission packet exists` from `mission packet is actionable`
  - Stage3 now distinguishes `scene shell exists` from `scene shell can guide generation`
  - Stage4 now distinguishes `candidate exists` from `candidate materially realizes the blueprint contract`
- The tranche does not fully close the broader quality problem by itself:
  - Stage2 still uses a score penalty rather than a hard fail for generic episode-detail beats
  - Stage3 still leaves deeper tactical/authority drift to validator/runtime
  - Stage4 still uses bounded materialization/anchor heuristics, not a full semantic judge
- The current queue reading remains correct: no new queue lane is needed, and the immediate next action stays one bounded `ep7/ep8` proof rerun.

## Findings

### 1. No fresh `P0/P1` reopen was found in the bounded tranche

The landed surfaces are coherent with the earlier `ep8` root-cause reading:

- `arc_ensemble.py` now penalizes generic `episode_details` beats instead of only checking presence
- `blueprint_ensemble.py` now rejects structurally weak scene shells before validator spend
- `chief_writer.py` now filters under-materialized manuscript candidates before Director selection when at least one better candidate exists

Targeted shards stayed green on the live workspace, and no contradiction appeared between the earlier Stage3 root-cause survey and the current cross-stage producer gate.

Conclusion:

- this bounded tranche is safe to treat as landed
- no fresh same-family `P0/P1` was reopened by the new producer gate

### 2. Stage2 now reads actionability, not just field presence

Shared helper `has_actionable_obligation_text(...)` now exists in `scene_obligation_heuristics.py:112`.

Stage2 uses that helper in `arc_ensemble.py:274` and `arc_ensemble.py:503` to penalize `episode_details` packets whose beats are present but too generic to guide downstream generation.

This closes a real quality gap:

- previous logic mainly rewarded coverage and presence
- current logic also asks whether the per-episode beats contain concrete obligations instead of placeholder labels like `setup`, `progress`, or `climax`

Important bound:

- this is still a scoring penalty, not a hard reject
- if every candidate is generic, the least-bad generic candidate can still survive Director selection

Conclusion:

- this is a real `P2 -> lower-P2/P3` improvement
- it improves candidate ranking earlier, but it does not yet fail closed on all-generic Stage2 mission packets

### 3. Stage3 now blocks generic scene shells before validator spend

Stage3 `_scene_has_meaningful_payload(...)` in `blueprint_ensemble.py:807` now uses actionable-text checks for:

- scene summary / description / goal / content
- `key_events`

The Stage3 admission gate in `blueprint_ensemble.py:841` now fails candidates when they have:

- missing or invalid `opening_transition`
- no meaningful `protagonist_state`
- fewer than two informative scenes

This is the cleanest closure of the earlier `ep8` producer-drift finding:

- cheap candidate admission is now much closer to the validator contract
- obviously weak shells no longer wait until expensive downstream validation to be rejected

Conclusion:

- this is the highest-value part of the tranche
- it directly reduces one of the clearest expensive churn families from the `ep8` rerun evidence

### 4. Stage4 now prunes under-materialized manuscripts before Director, but keeps degraded-mode resilience

`chief_writer.py:194` builds a bounded manuscript contract diagnostic using:

- writer-template validation
- scene materialization against blueprint obligations
- opening-anchor hit in the early manuscript

`chief_writer.py:239` converts that diagnostic into admission reasons such as:

- `template_contract_failed`
- `scene_obligation_under_materialized`
- `tail_scene_not_reflected`
- `opening_anchor_missing`

`chief_writer.py:261` and `chief_writer.py:811` then prune weak candidates before Director selection, but only when at least one candidate clears the gate.

This matters because it keeps both goals at once:

- better Director spend when there is at least one materially grounded manuscript
- no total collapse into empty output when all candidates are weak and the runtime still needs a fallback path

Conclusion:

- this is a bounded quality-floor improvement, not an over-aggressive fail-closed rewrite
- the fallback-preserving design is correct for the current queue posture

### 5. Side effects stayed bounded and honest

Observed side-effect surfaces for this tranche:

- console / operator:
  - Stage4 may now emit a bounded `[Writer] x/y candidates cleared scene/materialization gate` operator line
- retry / recovery:
  - Stage4 intentionally keeps the original candidate set when every candidate fails the new contract gate
- file / DB / schema:
  - no new persistence or schema surface was introduced by this tranche
- queue / roadmap:
  - no queue membership change is required from this audit alone

Conclusion:

- the tranche changes quality gating behavior more than sink topology
- there is no fresh persistence or queue-authority risk from this landing

### 6. Residual risks remain, but they are bounded and lower severity

Residual `P2/P3` watch items after the landing:

1. Stage2 generic mission packets are still score-down, not fail-closed.
2. Stage3 tactical/authority drift still remains primarily validator/runtime-owned; this tranche does not attempt broad tactical-semantic retuning.
3. Stage4 manuscript admission is still heuristic:
   - template validation
   - scene materialization
   - opening anchor
  It is not a full semantic continuity judge.

Conclusion:

- this tranche raises the quality floor and trims obvious waste
- it does not fully replace the later live proof step or broader long-horizon Polaris/DecisionKernel work

## Ownership Verdict

- `Stage2 producer scoring`: improved and coherent
- `Stage3 producer admission`: primary landed improvement
- `Stage4 writer-side admission`: secondary but meaningful landed improvement
- `Director`: not reopened as the main owner of the `ep8` blocker family by this audit
- `validator/runtime`: still own deeper authority and repair-route enforcement after the producer gate

## Execution Consequence

Keep the active queue shape.

Do not open a new queue lane.

Keep the current owner reading:

- parent owner: `0_0-stage3-contract-tightening-remediation`
- sibling support: `0_0-stage3-opening-transition-contract-normalization-remediation`
- broader cross-stage support remains in the existing Stage2/Stage4 lanes already present in the roadmap

Immediate next action remains:

1. one bounded paid `ep7/ep8` proof rerun
2. verify that Stage3 producer admission now cuts under-structured candidates before validator churn
3. verify that Stage4 writer-side candidate pruning reduces weak-manuscript spend without collapsing fallback behavior
4. only after that rerun, decide whether any residual `P1/P2` family still justifies another bounded static tranche

Explicit non-goals from this audit:

- no new queue family
- no broad Director retuning
- no broad tactical-semantic heuristic rewrite
- no claim that Stage2 or Stage4 are fully closure-clean from this static audit alone

## Verification

Fresh targeted sequential shards on the live workspace:

- `pytest tests/test_arc_ensemble_lane_a.py -k "generic_episode_details_beats or mission_packet or tactical_meta_vocabulary" -q`
  - `3 passed`
- `pytest tests/test_blueprint_ensemble_generate_ensemble.py -k "generic_scene_shells or missing_opening_transition_contract or empty_protagonist_state_contract or sanitizes_contaminated_key_events" -q`
  - `4 passed`
- `pytest tests/test_chief_writer_candidate_lane_f.py -k "finalize_generate_ensemble_candidates" -q`
  - `2 passed`
- `pytest tests/test_chief_writer_generate_ensemble_lane_b.py -k "finalize_generate_ensemble_candidates or owner_shell_coordinates_helper_chain" -q`
  - `2 passed`
- `pytest tests/test_stage23_stage4_readiness_wave1.py -k "stage4_readiness_contract_gaps or off_arc_intrusion or skips_tactical_intrusion_flag or disguised_intrusion" -q`
  - `4 passed`
- `pytest tests/test_blueprint_patch_mode.py -k "escalates_structural_binding_categories_to_full_regenerate or escalates_contract_blocked_scene_model_to_full_regenerate or pass_with_fix_unresolved" -q`
  - `3 passed`

Supplemental verification:

- `python -m py_compile ...`
  - touched runtime/test files compiled successfully
- `python scripts/check_utf8_hygiene.py ...`
  - passed for the touched code/test/doc files in this audit cycle

## 3-Pass Audit

Pass 1. Structure and scope:

- kept the document as an audit rather than silently widening it into a new execution SSOT
- bounded scope to the newly landed `s2-s3-s4` producer-smart tranche
- kept queue consequences explicit and non-expansive

Pass 2. Evidence and consistency:

- rechecked the earlier `ep8` root-cause survey against the live producer gate now in code
- checked current queue docs so the recommendation stays lane-consistent
- checked code, tests, and side-effect surfaces so the audit is not based on prose alone

Pass 3. Execution and readability:

- converted the landing state into one clear next action
- kept residual risks explicit instead of overclaiming closure
- kept broader retuning and longer-horizon refactors deferred behind fresh rerun proof

Confidence after 3-pass re-audit: `97%`
