# Stage234 Cross-PC Selection-Companion Patch-Trace Handoff Context

Date: 2026-04-15
Status: final (3-pass audited handoff context for continuing the bounded Stage4 residual patch on another PC after the snapshot/push of this patch wave; no fresh canary was run after the newest local patch)
Canonical Path: `docs/2026-04-15/stage234-cross-pc-selection-companion-patchtrace-handoff-context.md`
Audience:

- another PC operator
- future Codex continuation

## Purpose

- preserve the exact context after the pushed `runtime-authority sinkproof closure` and the follow-up `selection-companion / patch-trace` patch wave prepared on top of it
- let the next PC continue from `pull latest origin/main -> rerun focused validation -> fresh canary`
- prevent the aborted local `r5` canary attempt from being mistaken for completed proof or for committed evidence

## Authoritative Baseline

- branch: `main`
- published handoff head on `origin/main`: `cbb834101d62eb5ecb53b31d2fcb3d1a4bf8e565`
- published handoff commit title: `stage234: snapshot selection-companion residual handoff`
- historical pre-patch baseline on `origin/main`: `d9a010069e079452ef0927b9634e0e1724a9427d`
- historical baseline commit title: `stage234: snapshot runtime-authority sinkproof closure`
- patch-set provenance for this handoff:
  - the changes described below were authored on top of `d9a01006`
  - another PC should not reconstruct or re-invent that pre-push local state
  - once this handoff note is visible on another PC via `git pull`, the pulled `HEAD = cbb83410...` is the authoritative baseline for the next canary wave
- baseline meaning:
  - Stage4 final sink closure for `stage_attempts`, `hud_snapshot`, and `state_logs.actual_truth` is already committed and pushed
  - the last completed live-proof anchor before the newest local patch is:
    - [stage234-global-authority-alignment-post-runtime-authority-drift-live-canary-working-tree-3pass-audit.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-15/stage234-global-authority-alignment-post-runtime-authority-drift-live-canary-working-tree-3pass-audit.md:1)

## Patch Set Included In This Handoff Wave

These files make up the bounded follow-up patch wave that should now travel together with this handoff note on `main`.

Code / test files:

- [stage4_interview_round.py](/C:/Users/wjjo/Desktop/글도비/modules/core/stage4_interview_round.py:3407)
- [failure_analyzer.py](/C:/Users/wjjo/Desktop/글도비/modules/core/failure_analyzer.py:1741)
- [test_stage4_interview_round.py](/C:/Users/wjjo/Desktop/글도비/tests/test_stage4_interview_round.py:6610)
- [test_failure_analyzer.py](/C:/Users/wjjo/Desktop/글도비/tests/test_failure_analyzer.py:943)

Documentation / proof context:

- [stage234-global-authority-alignment-post-runtime-authority-drift-selection-companion-residual-current-head-3pass-audit.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-15/stage234-global-authority-alignment-post-runtime-authority-drift-selection-companion-residual-current-head-3pass-audit.md:1)
- this handoff note
- `projects/_canary/canary_0_0_stage4_ep2_sinkproof_r4_selectionresidual/`

Interpretation:

- `r4_selectionresidual` is the last completed canary proof and remains valid evidence
- the aborted local `r5_patchtraceclosure` attempt is intentionally not authoritative proof for this handoff wave

## What We Proved Before The Newest Local Patch

The last completed canary was `projects/_canary/canary_0_0_stage4_ep2_sinkproof_r4_selectionresidual/`.

Key confirmed facts from [canary_summary.json](/C:/Users/wjjo/Desktop/글도비/projects/_canary/canary_0_0_stage4_ep2_sinkproof_r4_selectionresidual/logs/canary_summary.json:1396):

- `final_authority_contract_summary.status = ok`
- `selection_role = historical_companion`
- the earlier `stage4_retry_contract_not_exercised` warning was already cleared there
- remaining warnings at that point were:
  - `patch_strategy_mismatches`
  - `sink_alignment_status:warn`

The bounded residual interpretation was already documented in:

- [stage234-global-authority-alignment-post-runtime-authority-drift-selection-companion-residual-current-head-3pass-audit.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-15/stage234-global-authority-alignment-post-runtime-authority-drift-selection-companion-residual-current-head-3pass-audit.md:1)

That audit concluded:

- the repaired final sink did not reopen
- the main remaining warn lane was a `director_selections` hybrid-companion contract plus one metadata completeness miss
- broader Stage234 rerun remained operator-gated

## What The New Local Patch Set Changes

### 1. Keep `director_selections` historical on patch-PASS flows

In [stage4_interview_round.py](/C:/Users/wjjo/Desktop/글도비/modules/core/stage4_interview_round.py:4763) and [stage4_interview_round.py](/C:/Users/wjjo/Desktop/글도비/modules/core/stage4_interview_round.py:4870):

- `_sync_pass_result_selection_rationale()` now accepts `preserve_historical_companion`
- Stage4 patch-PASS / trace-patch paths set that flag and skip `update_director_selection_rationale()`

Intent:

- stop mutating `director_selections` into a hybrid row
- keep it as a truthful `historical_companion`

### 2. Prefer nested `repair_contract` authority when rebuilding repair payloads

In [stage4_interview_round.py](/C:/Users/wjjo/Desktop/글도비/modules/core/stage4_interview_round.py:3407):

- `_build_repair_contract_payload_from_parts()` now reads nested `source["repair_contract"]`
- subtype, scope, provenance, provenance sources, and `target_kind` prefer nested repair-contract authority before weaker fallbacks

Intent:

- preserve `repair_contract_subtype` and related authority fields when patch re-audit already supplied the stronger nested contract

### 3. Stop analyzer warnings for raw pre-final companion drift

In [failure_analyzer.py](/C:/Users/wjjo/Desktop/글도비/modules/core/failure_analyzer.py:1741):

- `_collect_sink_alignment_raw_rationale_results()` now receives `authority_row`
- when `selection_companion_status == "pre_final_candidate"`, it skips:
  - `director_selections` contract alignment for `selection_contract_snapshot_raw`
  - feedback mismatch alignment for `feedback_provenance_raw`

Intent:

- treat pre-final raw rationale surfaces as historical evidence rather than false-positive final sink drift

### 4. Stop `episode_production` from over-projecting patch trace on non-patch regenerate rounds

In [stage4_interview_round.py](/C:/Users/wjjo/Desktop/글도비/modules/core/stage4_interview_round.py:7329):

- `_append_episode_log()` now only resolves patch-trace payloads when `is_patch` or `patch_fallback` is true
- non-patch rounds keep `fix_pack`, but no longer claim `patch_trace`
- `flags.patch_mode` now reflects `bool(is_patch)` instead of `bool(is_patch or _patch_trace)`

Intent:

- make `episode_production` agree with `stage_attempts` and `pass_rate_monitor`
- close the `patch_strategy_mismatches` / `raw_patch_trace_drift` class of warnings for regenerate rounds that are not true patch rounds

## Tests Already Run On This Machine

These all passed against the patch set described in this note:

1. `python -m pytest tests/test_stage4_interview_round.py -k "append_episode_log_persists_patch_trace_raw_record or append_episode_log_does_not_project_patch_trace_from_fix_pack_when_not_patch or pass_with_fix_episode_log_uses_final_attempt_meta_and_preserves_selection_meta or build_pass_result_logging_payload_preserves_nested_repair_contract_subtype" -q`
   - result: `4 passed, 306 deselected`
2. `python -m pytest tests/test_failure_analyzer.py -k "tracks_stage4_feedback_provenance_mismatch or ignores_prefinal_companion_contract_and_feedback_drift or tracks_stage4_patch_trace_mismatch or ignores_pre_final_director_companion_mismatch" -q`
   - result: `4 passed, 46 deselected`
3. `python scripts/check_utf8_hygiene.py modules/core/stage4_interview_round.py modules/core/failure_analyzer.py tests/test_stage4_interview_round.py tests/test_failure_analyzer.py`
   - result: passed

Important limit:

- no fresh completed canary exists yet for this newest local patch set

## Partial `r5` Canary Warning

This session briefly started a new canary target on the source machine:

- `projects/_canary/canary_0_0_stage4_ep2_sinkproof_r5_patchtraceclosure/`

That run was intentionally aborted before completion. The process was explicitly killed, and no lingering `run_stage4_canary.py` process remained afterward.

Treat `r5` as partial prep/runtime debris only:

- it contains prep files, session logs, and a live DB
- it does not count as completed proof
- do not cite it as evidence for closure
- it should not be the basis for the next PC's canary wave

## Recommended Read Order On The Next PC

1. [stage234-global-authority-alignment-post-runtime-authority-drift-live-canary-working-tree-3pass-audit.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-15/stage234-global-authority-alignment-post-runtime-authority-drift-live-canary-working-tree-3pass-audit.md:1)
2. [stage234-global-authority-alignment-post-runtime-authority-drift-selection-companion-residual-current-head-3pass-audit.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-15/stage234-global-authority-alignment-post-runtime-authority-drift-selection-companion-residual-current-head-3pass-audit.md:1)
3. this handoff note

## Exact Next Steps On Another PC

### 1. Re-establish the latest pushed baseline

Run:

```powershell
git switch main
git pull --ff-only origin main
git rev-parse HEAD
git status --short
```

Expected baseline:

- `HEAD = cbb834101d62eb5ecb53b31d2fcb3d1a4bf8e565`
- clean worktree after pull

Quick sanity check:

- confirm that this file exists at `docs/2026-04-15/stage234-cross-pc-selection-companion-patchtrace-handoff-context.md`
- confirm that the four code/test files above already include the patch-set logic from this note

### 2. Re-run the focused validation first

Run:

```powershell
python -m pytest tests/test_stage4_interview_round.py -k "append_episode_log_persists_patch_trace_raw_record or append_episode_log_does_not_project_patch_trace_from_fix_pack_when_not_patch or pass_with_fix_episode_log_uses_final_attempt_meta_and_preserves_selection_meta or build_pass_result_logging_payload_preserves_nested_repair_contract_subtype" -q
python -m pytest tests/test_failure_analyzer.py -k "tracks_stage4_feedback_provenance_mismatch or ignores_prefinal_companion_contract_and_feedback_drift or tracks_stage4_patch_trace_mismatch or ignores_pre_final_director_companion_mismatch" -q
python scripts/check_utf8_hygiene.py modules/core/stage4_interview_round.py modules/core/failure_analyzer.py tests/test_stage4_interview_round.py tests/test_failure_analyzer.py
```

Only move on if these stay green.

### 3. Prepare a fresh canary target with a new name

Do not reuse `r5_patchtraceclosure` as proof.

Recommended pattern:

```powershell
python scripts/run_stage4_canary.py prepare --source-project _canary/canary_0_0_stage4_ep2_sinkproof_r3_runtimeauth --target-project _canary/canary_0_0_stage4_ep2_sinkproof_r6_patchtraceclosure --from-ep 2 --force
python scripts/run_stage4_canary.py run --project _canary/canary_0_0_stage4_ep2_sinkproof_r6_patchtraceclosure --target-ep 2
```

If you prefer a different suffix, keep it new and clearly post-patch.

### 4. Evaluate the fresh canary against the actual residual goals

Primary success checks:

- `final_authority_contract_summary.status = ok`
- `selection_role = historical_companion`
- no reappearance of `stage4_retry_contract_not_exercised`
- `patch_strategy_mismatches` cleared
- `sink_alignment_status:warn` either cleared or reduced to a smaller explicitly understood residual

### 5. After proof, close the lane cleanly

If the fresh canary is good:

- update the relevant `2026-04-15` audit docs with the new proof anchor
- take a narrow snapshot commit
- then push `main`

If the canary still warns:

- compare the new summary to `r4_selectionresidual`
- treat new differences as bounded residual evidence, not as permission to reopen a broad Stage234 queue item automatically

## Operator Notes To Preserve

- do not reconstruct the old pre-push local patch state by hand; use the latest pulled `main` at `cbb83410...`
- `d9a01006` is historical provenance only, not the target baseline for the next PC
- do not treat `director_selections` as a second final sink; current intent is `historical_companion`
- do not trust the aborted `r5` attempt as proof
- keep the next wave bounded to `selection-companion / patch-trace` cleanup unless the fresh canary shows a truly new failure class
