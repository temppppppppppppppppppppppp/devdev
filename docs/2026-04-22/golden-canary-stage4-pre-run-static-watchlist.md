# Golden Canary Stage4 Pre-Run Static Watchlist

Date: 2026-04-22
Status: ready
Track: system-track
Mode: pre-run static watchlist
Confidence: 0.95

## 1. Scope

- This document is a `pre-run static watchlist`, not a final conclusion.
- Target run: `projects/골든 카나리아`, `Stage 4 supervised`, `target_ep=5`.
- This watchlist is for blocker shortening and sink ordering before the next real run.
- Authority rule for later triage: `live evidence > this static watchlist > stale survey text > assumption`.
- Production code was not modified and `Stage 4` was not run for this watchlist.

## 2. Current known frontier and prior interruption summary

- `docs/2026-04-22/stage4-supervised-run-interruption-context.md` records the persisted stop frontier as:
- `Stage 3` blueprints through `ep16`
- `Stage 4` manuscripts through `ep3`
- `Stage 4 ep4` rejected 3 times
- `Stage 4 ep5` not started
- Current DB readback still matches that persisted frontier:
- `blueprints=16`
- `manuscripts=3`
- `stage_attempts(stage=4, ep_num=4)=3`
- `stage_attempts(stage=4, ep_num=5)=0`
- Important current contradiction, `needs live confirmation`:
- `logs/session/decisions.jsonl` and `logs/episode_production.jsonl` contain a later `ep4 attempt 4` PASS-like record at `2026-04-22 08:38:49`.
- No corresponding `manuscripts` row, no `drafts/ep_0004.txt`, no `STAGE4_POST_PASS_CONTRACT` for `ep4`, and no Stage 4 `pass_rate_monitor` record were found.
- Operational reading: persisted frontier is still `manuscripts through ep3`, while some operator-visible sinks contain a later provisional or incomplete `ep4` PASS trace.

## 3. Top risk watchlist

1. `ep4` timeline replay / already-completed event restaging remains the top blocker family.
The persisted latest `stage_attempts` row for `ep4` is `id=29`, `REJECT`, `score=40`, `primary_failure_layer=director_quality`, `gate_basis=continuity_firewall`, `repair_contract.subtype=타임라인`, `repair_contract.target_kind=scene_model`. The `attempt_03` artifact directly restages the Park Seong-ho meeting, the `20억` liquidation, and the corporate/account directive as if they were fresh events.

2. Frontier carryover between `ep3 -> ep4` is the likely root surface behind that replay.
`ep3` already contains the hotel meeting and the directive for liquidation plus corporate/account setup. `ep4 attempt_03` reopens the same beat instead of moving to downstream execution/reporting. The `attempt_04` artifact rewrites Scene 2 into Park Seong-ho execution/reporting, which is the right direction, but it is not yet persisted truth.

3. Retry / patch / fix-scope widening can hide the true blocker.
`runtime_audit.jsonl` shows `stage4_retry_pathology_signal` at `2026-04-22 07:46:10`, `07:52:26`, and `08:03:32`. The lane flips between `post_select_conflict` and `continuity_firewall`, while runtime routing widens repair scope beyond the original `authoritative_fix_scope`. This can make the operator chase local phrase noise after the problem has already widened to frontier or `scene_model`.

4. Numeric carryover warning residue remains a watch item, but current evidence does not support making it the dominant blame.
`modules/core/numeric_consistency_checker.py` now converts literal `won/krw` to 억 in `_to_eok()`, so the code-side patch is justified. But Stage 4 operator-visible sinks still show `numeric_carryover_authority` warnings rendered as `2000000000.0억` in `session/decisions.jsonl` and `episode_production.jsonl`. The live Stage 4 lane therefore still needs confirmation that the patch is actually propagating end to end.

5. Sink misalignment is itself a high-priority watch item.
`runtime_audit_summary.json` is stale and still tagged `stage3_complete`. `pass_rate_monitor.json` currently has no Stage 4 `ep4` rows. `session/decisions.jsonl` and `episode_production.jsonl` show a later `ep4 attempt 4` PASS-like trace not reflected in `stage_attempts`, `manuscripts`, `drafts`, or post-pass signals. The next stop can be mis-triaged if operators open the wrong sink first.

## 4. Code hotspot map

- `scripts/run_stage4_direct_supervised.py`
Why it matters: the direct supervised runner decides success partly from `latest_written_ep` and partly from `runtime_audit_summary.json`.
Failure shape: a stale `runtime_audit_summary` can mislead quick operator reading about whether Stage 4 actually advanced.
Live confirmation: after the next stop, compare `latest_written_ep`, `manuscripts`, and `runtime_audit_summary.tag`. If the summary tag lags again, treat it as companion metadata only.

- `modules/core/stage4_interview_round.py`
Why it matters: this is the main hotspot for continuity replay detection, fix-pack contract gating, attempt logging, and sink fan-out. `_is_continuity_replay_reject()` recognizes replay-like contradictions. `_evaluate_fix_pack_contract()` rejects `scene_model` targets as non-local. `_append_episode_log()` writes `episode_production.jsonl`. `_record_s4_attempt()` tries `pass_rate_monitor` and `stage_attempts`.
Failure shape: the lane can keep routing through local patch logic after the real blocker has widened to `scene_model`, or operator-visible sinks can diverge if one of the non-blocking writes fails.
Live confirmation: inspect the next `attempt_key` across `stage_attempts`, `episode_production`, and `session/decisions`. If `episode_production` advances without `stage_attempts`, the sink divergence is still live.

- `modules/core/stage4_director_runtime.py`
Why it matters: Director context includes Python validation warnings and shared failure warnings before the Director verdict is shaped.
Failure shape: numeric warning noise or shared advisory noise can coexist with the real continuity blocker and distort fix-scope interpretation.
Live confirmation: if the next stop still names completed-event repetition in `open_review` or `firewall_reason` while numeric warnings are merely advisory, continuity remains the lead blocker.

- `modules/core/stage4_orchestrator.py`
Why it matters: `_consume_episode_round_outcome()` only advances the episode frontier if `_process_episode_pass()` succeeds.
Failure shape: a PASS-like round can exist in decision logs while the frontier does not move if the later pass-processing path fails or the run stops mid-settlement.
Live confirmation: if a new PASS appears, verify that it also creates a new manuscript row or draft before treating the frontier as advanced.

- `modules/core/stage4_post_processor.py`
Why it matters: `_save_pass_result_primary_db()` is the manuscript persistence gate, and `_run_pass_result_post_pass_pipeline()` plus settlement/export steps decide whether the PASS is fully settled. The code explicitly warns that a later failure can leave the manuscript persisted while skipping remaining sinks.
Failure shape: incomplete PASS settlement, missing settlement packet, missing human-facing draft, or partial post-pass side effects.
Live confirmation: for the next PASS candidate, verify together: `manuscripts`, `drafts/ep_0004.txt`, `ep_0004.settlement.json`, and any Stage 4 post-pass contract signal. Do not trust a PASS without those surfaces lining up.

- `modules/core/stage4_post_pass_runtime.py`
Why it matters: it emits the Stage 4 post-pass contract signal and records carryover authority ownership.
Failure shape: if post-pass never fires, operators lose the clean sink that separates advisory warnings from settled state truth.
Live confirmation: a fully settled `ep4` PASS should emit `STAGE4_POST_PASS_CONTRACT` for `ep=4` in `runtime_audit.jsonl` and a matching contract entry in `episode_production.jsonl`.

- `modules/core/numeric_consistency_checker.py`
Why it matters: `_to_eok()` now handles `won/krw`, and `_build_fact_ledger_warning()` creates the `numeric_carryover_authority` warning family.
Failure shape: false-positive carryover mismatch warnings can still pollute operator-visible reasoning if the live path is using stale or non-normalized inputs.
Live confirmation: on the next stop, check whether numeric warnings still render raw KRW as `2000000000.0억`. If they disappear or normalize to `20.0억`, the numeric patch is likely working and continuity should stay the lead blocker.

- `modules/core/failure_analyzer.py`
Why it matters: it codifies the sink authority model used for cross-sink alignment. Its own note says Stage 4 final authority resolves from `stage_attempts`, while decision-history sinks are companion history.
Failure shape: operators can over-trust `director` or session-history surfaces and miss persisted truth.
Live confirmation: if sinks diverge again, keep `stage_attempts` and `manuscripts` above `session/decisions` and `episode_production` for final frontier calls.

## 5. Authoritative sink map

- First check: `projects/골든 카나리아/project_data.db` -> `stage_attempts`
Authoritative for persisted attempt truth. Use this first for the latest `ep4` or `ep5` verdict frontier. Key fields: `stage`, `ep_num`, `attempt_num`, `verdict`, `score`, `primary_failure_layer`, `reject_reason`, `open_review`, `attempt_key`, `artifact_path`.

- First check: `projects/골든 카나리아/project_data.db` -> `manuscripts`
Authoritative for whether a Stage 4 episode actually persisted as reader-facing manuscript truth. If `ep4` is absent here, the run did not complete a persisted Stage 4 advance, regardless of earlier PASS-like operator logs.

- Second check: `projects/골든 카나리아/logs/episode_production.jsonl`
High-value companion sink for round-level lifecycle, artifact references, `gate_basis`, `primary_failure_layer`, `repair_contract`, and `attempt_key`. Not self-sufficient as final authority because it mixes authoritative-looking manuscript rows with lifecycle-only rows such as retry pathology and patch snapshots.

- Second check: `projects/골든 카나리아/logs/session/decisions.jsonl`
High-value operator history sink for `selection_reason`, `verdict_reason`, `open_review`, `attempt_key`, and artifact references. Use it to understand what the Director believed at the time. Do not use it alone for final frontier truth.

- Third check: `projects/골든 카나리아/logs/runtime_audit.jsonl`
Operational event stream. Best for retry-pathology fingerprints, repair-scope widening, and post-pass contract presence. Not final attempt truth.

- Third check: `projects/골든 카나리아/logs/quality_metrics.jsonl`
Companion quality sink. Useful to confirm whether Stage 4 validation progressed past REJECT rows into settled PASS-side quality handling. In current evidence, `ep4` shows REJECT validations only and no later PASS validation.

- Fourth check: `projects/골든 카나리아/logs/pass_rate_monitor.json`
Companion cross-check only. In current evidence it is missing Stage 4 `ep4` rows entirely, so it should not be trusted as a leading sink for this lane until live re-confirmed.

- Do not open first: `projects/골든 카나리아/logs/runtime_audit_summary.json`
Operator summary only. It is currently stale and still tagged `stage3_complete`. Use only after DB and JSONL truth are already established.

- Artifact truth companion: `projects/골든 카나리아/logs/artifacts/stage4/ep_0004/...`
Use the artifact path from the latest authoritative or near-authoritative row to confirm whether the failure is true timeline replay, numeric-only noise, or later flashback/local-fix drift.

## 6. Live confirmation checklist

1. `Timeline replay remains the dominant blocker.`
Inspect `project_data.db -> stage_attempts` for the latest `stage=4`, `ep_num=4` row, then open the matching artifact under `logs/artifacts/stage4/ep_0004/...`. Confirm if `gate_basis=continuity_firewall` or `post_select_conflict` with replay-like `open_review` or `reject_reason`, and the artifact still stages the Park Seong-ho meeting / liquidation / account directive as a fresh event. Disprove if the latest authoritative artifact moves Scene 2 into execution/reporting and the reject reason shifts away from replay.

2. `A provisional PASS is being mistaken for persisted advancement.`
Inspect `stage_attempts`, `manuscripts`, `drafts`, `episode_production.jsonl`, `session/decisions.jsonl`, and `runtime_audit.jsonl` for the same `attempt_key`. Confirm if `session/decisions` or `episode_production` says PASS while `manuscripts`, `stage_attempts`, `drafts/ep_0004.txt`, and post-pass signals still do not exist. Disprove if all of those sinks align on the same successful `attempt_key`.

3. `Numeric warning residue is still polluting the Stage 4 lane after the won/krw patch.`
Inspect `episode_production.jsonl` and `session/decisions.jsonl` `runtime_advisory` or `warnings` text for `numeric_carryover_authority` entries, especially raw values like `2000000000.0억`. Confirm if the next stop still emits that raw-KRW rendering or if numeric warnings become the primary rejection basis. Disprove if warnings disappear or normalize cleanly to `20.0억` while continuity stays the dominant rejection family.

4. `Retry scope widening is hiding the real blocker.`
Inspect `runtime_audit.jsonl` `stage4_retry_pathology_signal` rows for `fix_scope`, `authoritative_fix_scope`, `repair_scope`, `fix_pack_ready`, `fix_pack_reason`, and `pathology_fingerprint`. Confirm if the lane keeps widening from local or inplace guidance into full rewrite without producing a settled frontier advance. Disprove if the next run keeps a stable scope and the sink family converges quickly.

5. `Frontier carryover from ep3 is still being consumed incorrectly.`
Inspect `drafts/ep_0003.txt`, the latest `ep4` artifact, and the matching `session/decisions.jsonl` row. Confirm if `ep3` already completed the meeting/directive beat while the new `ep4` artifact still reopens it as unresolved. Disprove if the new `ep4` artifact treats that beat as completed prior truth and only advances downstream consequences.

## 7. Operator fast-triage checklist after the next stop/fail

1. Open `project_data.db` first and check `stage_attempts` plus `manuscripts` for the latest Stage 4 persisted truth.
2. Copy the latest `attempt_key` from DB and join it against `episode_production.jsonl` and `logs/session/decisions.jsonl`.
3. Open the artifact file referenced by that `attempt_key` before reading summary prose.
4. If the artifact restages an already-completed meeting or directive, classify it as timeline replay first and only then review numeric warnings.
5. Open `runtime_audit.jsonl` next for `stage4_retry_pathology_signal` and any `STAGE4_POST_PASS_CONTRACT` presence or absence.
6. Use `quality_metrics.jsonl` to see whether the lane reached a later validation or post-pass surface after the stop.
7. Treat `pass_rate_monitor.json` and `runtime_audit_summary.json` as companion signals only, not as the first authority call.
8. If a PASS appears in `session/decisions` or `episode_production` without a new manuscript row or draft export, classify it as provisional until live evidence proves otherwise.

## 8. Confidence and known unknowns

- Confidence: `0.95`
- Highest-confidence static call: the dominant persisted blocker remains `ep4` timeline replay / completed-event repetition, not a small local wording problem.
- Biggest live-confirmation-first uncertainty: `2026-04-22 08:38:49` produced a later `ep4 attempt 4` PASS-like trace in `session/decisions` and `episode_production`, but that trace did not settle into `stage_attempts`, `manuscripts`, `drafts`, `pass_rate_monitor`, or post-pass signals. It is currently unsafe to treat that PASS as real frontier advancement without fresh live confirmation.
- Additional known unknowns:
- `pass_rate_monitor.json` is missing Stage 4 rows for the current watch surface, so sink-health itself must be revalidated live.
- `runtime_audit_summary.json` is stale enough that it cannot be used as a first-open frontier source.
- Plain `session_20260422_*.log` files referenced in older context were not present in the current workspace snapshot; only `logs/session/*.jsonl` surfaces were available for this survey.
