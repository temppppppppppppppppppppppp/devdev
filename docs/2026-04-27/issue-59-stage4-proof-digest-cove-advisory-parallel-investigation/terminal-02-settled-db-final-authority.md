# Issue #59 Terminal 02 - Settled DB Final Authority

Status: final after 3-pass adversarial audit  
Scope: final authority across Director rows, settled Stage4 rows, post-select rejection, and CoVe advisory

## Finding Summary

Stage4 has at least three authority layers that must stay distinct:

- Director selection authority: `director_selections` records the Director's candidate selection and initial/final Director verdict.
- Settled attempt authority: `stage_attempts` records the attempt's final runtime-settled verdict for the stage attempt.
- Advisory side channels: CoVe runtime advisory and proof digest warn explain evidence/verification conditions but do not by themselves rewrite Director authority.

Current-session DB evidence shows why this split matters. In session `20260427_070604`, the latest Stage4 `ep9` Director rows are `PASS_WITH_FIX`, while the matching `stage_attempts` rows are `REJECT` after post-select conflict handling:

- `s4:ep9:arc2:a1:20260427_070604`: Director `PASS_WITH_FIX`, settled attempt `REJECT`
- `s4:ep9:arc2:a2:20260427_070604`: Director `PASS_WITH_FIX`, settled attempt `REJECT`

That is not the same thing as a CoVe runtime failure. It is a post-select/runtime settlement outcome.

## Evidence

- `stage_attempts` current rows include `ep9` attempt 1 and 2 as `REJECT` with scores 94 and 93.
- `director_selections` current rows for the same attempt keys show `PASS_WITH_FIX`.
- `modules/core/stage4_outcome_runtime.py` preserves Director PASS when CoVe quick/LLM verification raises runtime exceptions.
- The same module converts semantic CoVe critical verification into an explicit fail-closed retry disposition only when `VerificationResult.should_regenerate` is true.
- Live logs show five `STAGE4_COVE_RUNTIME_ADVISORY` events in `projects/01_골든카나리아/logs/episode_production.jsonl`, all carrying `director_pass_preserved=true`.

## Risk / Gap

If dashboards or benchmark records only show a single final status, they can blur:

- Director selected candidate
- runtime post-select rejection
- CoVe runtime advisory
- CoVe semantic fail-closed retry
- proof-digest evidence warn

That would make later reject-rate and runtime comparisons hard to trust.

## Suggested Contract Or Test

Add an authority contract table to Stage4 summaries:

- `director_verdict`: from `director_selections`
- `settled_attempt_verdict`: from `stage_attempts`
- `post_select_override_reason`: from runtime/post-select fields when applicable
- `cove_runtime_advisory`: advisory only, PASS preserved
- `cove_fail_closed`: semantic retry/downgrade path
- `proof_digest_status`: evidence alignment only

Test expectation: an attempt key can legally have Director `PASS_WITH_FIX` and settled attempt `REJECT` when a post-select conflict fires, and that state must not be labeled as CoVe runtime failure.

## Implementation Owner Surface

- `modules/core/stage4_outcome_runtime.py`
- `modules/core/failure_analyzer.py`
- `modules/core/stage4_canary_tools.py`
- `scripts/compare_benchmark_records.py`

## Open Questions

- Should `director_selections` gain an explicit `settlement_phase` or should downstream surfaces derive it from `stage_attempts`?
- Should current dashboards show both Director verdict and settled attempt verdict side by side for Stage4?

## 3-Pass Save Audit

- Pass 1: Attempt-key level DB evidence checked against both `stage_attempts` and `director_selections`.
- Pass 2: CoVe advisory and post-select rejection were separated.
- Pass 3: No final narrative quality judgment was inferred from proof-digest or Python-only telemetry.

