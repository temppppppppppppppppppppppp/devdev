# Golden Canary Stage4 ep14 Strong Advisory Localfix Backfill 3-Pass Audit

Date: 2026-04-22
Status: final
Topic: `golden-canary-stage4-ep14-strong-advisory-localfix-backfill`
Scope: `ep14` guarded rerun failure, inherited `scene_model` fix-pack sentinel, bounded remediation seam
Commit State:
- Baseline Commit: `4a8f03a9370ba06eacdb3075389147c74056bc8c`
- Baseline Dirty Summary: `dirty: tracked runtime artifacts in benchmarks and projects/골든 카나리아 logs/db; untracked drafts and stage4 artifacts for ep_0011-ep_0014`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Intent

- Run an adversarial 3-pass audit before patching the `ep14` rerun blocker.
- Lock what actually persisted, what actually failed, and what the smallest safe remediation surface is.
- Keep the conclusion bounded to inspected runtime evidence and live code.

## 2. Scope

Included:

- `projects/골든 카나리아/logs/stage4_direct_supervised_guarded_result.json`
- `projects/골든 카나리아/logs/episode_production.jsonl`
- `projects/골든 카나리아/logs/session_20260422_191329.log`
- `projects/골든 카나리아/drafts/`
- `projects/골든 카나리아/logs/artifacts/stage4/ep_0014/`
- `modules/core/db_manager.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_reject_runtime.py`
- `tests/test_stage4_advisory_escalation_seam.py`
- `tests/test_stage4_interview_round.py`

Excluded:

- broader Stage4 owner-surface reduction work
- fresh guarded rerun execution
- unrelated parked `docs/temp/` items beyond queue ordering impact

## 3. Adversarial Pass 1. Artifact Truth and Persistence

Findings:

- Persisted drafts stop at `ep_0013`. `projects/골든 카나리아/drafts/` contains `ep_0011.*`, `ep_0012.*`, `ep_0013.*`, and no `ep_0014.txt` or `ep_0014.settlement.json`.
- `projects/골든 카나리아/logs/stage4_direct_supervised_guarded_result.json` reports `latest_written_ep_after=14`, but that is not proof that `ep14` persisted.
- `modules/core/db_manager.py:1898-1902` shows `get_latest_episode_number()` returns `MAX(ep_num) + 1`, so the guarded result field reflects the next target counter, not the persisted frontier.
- `projects/골든 카나리아/logs/episode_production.jsonl` shows rerun progress past the earlier `ep10` frontier:
  - `ep11 attempt 2 -> PASS 96 -> logs/artifacts/stage4/ep_0011/attempt_02/final_manuscript__A.txt`
  - `ep13 attempt 1 -> PASS 90 -> logs/artifacts/stage4/ep_0013/attempt_01/final_manuscript__A.txt`
- `ep14` has five completed attempts with no persisted final manuscript. On-disk artifacts under `projects/골든 카나리아/logs/artifacts/stage4/ep_0014/attempt_01..05/` are all reject artifacts.

Adversarial consequence:

- Any plan that treats `latest_written_ep_after=14` as persisted `ep14` authority is unsound.
- The authoritative persisted frontier after this rerun is `ep13`, with `ep14` as the active blocker.

## 4. Adversarial Pass 2. Gate and Contract Causality

Runtime evidence:

- `projects/골든 카나리아/logs/episode_production.jsonl` records five completed `ep14` attempts:
  - `2026-04-22T20:11:23`, attempt `1`, selected `A`, `director_verdict=PASS`, `final_verdict=REJECT`, `gate_basis=strong_advisory_escalation_non_local_fix`
  - `2026-04-22T20:19:12`, attempt `2`, selected `A`, same gate basis
  - `2026-04-22T20:27:32`, attempt `3`, selected `B`, same gate basis
  - `2026-04-22T20:35:35`, attempt `4`, selected `A`, same gate basis
  - `2026-04-22T20:47:55`, attempt `5`, selected `C`, same gate basis
- `projects/골든 카나리아/logs/session/decisions.jsonl` shows two distinct invalid-contract shapes inside the same loop:
  - attempt `4` already carried `target_kind="local_phrase"` but still had blank `do_not_regress` and blank `success_condition`
  - attempt `5` reverted to inherited `target_kind="scene_model"` again
- `projects/골든 카나리아/logs/session_20260422_191329.log:5952-5994` shows the final completed attempt flow:
  - Director produced `PASS`
  - strong advisory escalation promoted `PASS -> PASS_WITH_FIX` for `flashback,npc_drift`
  - the lane then forced `REJECT` because the local fix contract was invalid
  - round `6/10` started immediately after the fifth reject
- `projects/골든 카나리아/logs/stage4_direct_supervised_guarded_result.json` records `terminated_by_monitor=true`, `termination_reason=stage4_round_limit_exceeded`, `terminated_attempt_num=6`, `latest_round_seen=6`, which matches monitor termination at the round-6 boundary before a completed attempt-6 row existed.

Code-path evidence:

- `modules/core/stage4_interview_round.py:2572-2585` rejects `fix_pack.target_kind == "scene_model"` as non-local.
- `modules/core/stage4_interview_round.py:3256-3287` escalates strong advisory classes from `PASS` to `PASS_WITH_FIX`.
- `modules/core/stage4_interview_round.py:3369-3423` then fail-closes that escalated result to `REJECT` unless `fix_scope=inplace` and the fix-pack contract is truly ready.
- `modules/core/stage4_interview_round.py:2929-3125` is the seam that tries to backfill strong-advisory local fix contracts.
- `modules/core/stage4_interview_round.py:2976-2977` currently short-circuits when the inherited `fix_pack.target_kind == "scene_model"`, so advisory-specific local builders never get to replace that inherited non-local contract.
- The same backfill function also fills generic `patch_targets` and `must_fix` for local targets but leaves `do_not_regress` and `success_condition` empty when no specialized builder succeeds, which matches the invalid local contract shape observed on attempt `4`.
- `modules/core/stage4_reject_runtime.py:720-765` synthesizes the inherited non-local sentinel with `patch_targets=["scene-model rewrite boundary"]` and `target_kind="scene_model"`.
- `tests/test_stage4_interview_round.py:11484-11638` already locks that reject logging behavior as intentional for genuinely non-local retries.

Adversarial conclusion:

- The loop is not random scoring noise.
- The loop is a contract deadlock: a runtime-synthesized non-local `scene_model` sentinel is inherited into later attempts, and the strong-advisory backfill seam refuses to replace it even when `npc_drift` or `flashback` metadata could synthesize a bounded local fix contract.

## 5. Adversarial Pass 3. Remediation Minimality and Regression Risk

Smallest safe remediation:

- Patch only `modules/core/stage4_interview_round.py` inside `_backfill_strong_advisory_fix_pack()`.
- Detect the specific inherited runtime `scene_model` sentinel used for reject routing.
- When that sentinel is present and an existing advisory-specific builder can synthesize a local contract, treat the inherited sentinel as replaceable and let the current zero-to-local synth path return the local fix-pack.
- When the target is already local but the generic backfill leaves the contract incomplete, synthesize the missing `do_not_regress` and `success_condition` fields in the same bounded seam.
- Preserve the current behavior for explicit or genuinely non-local `scene_model` contracts.

Why this is the minimal fix:

- It does not weaken `_evaluate_fix_pack_contract()`.
- It does not change generic `PASS_WITH_FIX` handling.
- It does not change reject-runtime sentinel generation for truly non-local retries.
- It only removes an over-broad early return that blocks already-existing local builders from doing their job.

Required regression coverage:

- positive: inherited runtime `scene_model` sentinel + `npc_drift` local metadata -> stays `PASS_WITH_FIX` with local target
- positive: inherited runtime `scene_model` sentinel + `flashback` local metadata -> same policy if local builder is available
- positive: already-local fix-pack with blank guard/success fields becomes contract-ready through bounded generic completion
- negative: explicit or genuinely scene-level `scene_model` contract still rejects
- negative: generic `_enforce_pass_with_fix_contract()` still downgrades raw `scene_model` targets to `REJECT`

## 6. Operating Consequence

- Proceed with a bounded code fix and targeted regression tests.
- Do not rerun the guarded lane until the patch and tests are green.
- Treat this audit as the governing fact base for the execution SSOT created in the same batch.

## 7. Confidence

- Pass 1 confidence: 98/100
- Pass 2 confidence: 97/100
- Pass 3 confidence: 96/100
- Final estimated confidence: 97/100

The audit is above the 95% save gate and is fit to govern the bounded remediation below.
