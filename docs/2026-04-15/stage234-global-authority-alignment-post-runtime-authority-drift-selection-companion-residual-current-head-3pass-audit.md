# Stage234 Global Authority Alignment Post-Runtime-Authority-Drift Selection-Companion Residual Current-Head 3-Pass Audit

Date: 2026-04-15
Status: final (3-pass audited; bounded sibling residual definition for the remaining Stage4 selection-companion warn lane after the sinkproof closure)
Canonical Path: `docs/2026-04-15/stage234-global-authority-alignment-post-runtime-authority-drift-selection-companion-residual-current-head-3pass-audit.md`
Commit State:
- Baseline Commit: `d9a010069e079452ef0927b9634e0e1724a9427d`
- Baseline Dirty Summary: `clean`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-04-14/0_0-stage234-global-authority-alignment-bounded-remediation-execution-ssot.md`
- `docs/2026-04-15/stage234-global-authority-alignment-post-runtime-authority-drift-working-tree-3pass-audit.md`
- `docs/2026-04-15/stage234-global-authority-alignment-post-runtime-authority-drift-live-canary-working-tree-3pass-audit.md`
Evidence Artifacts:
- `modules/core/stage4_interview_round.py`
- `modules/core/db_manager.py`
- `modules/core/failure_analyzer.py`
- `modules/core/stage4_canary_tools.py`
- `projects/_canary/canary_0_0_stage4_ep2_sinkproof_r3_runtimeauth/logs/canary_summary.json`
- `projects/_canary/canary_0_0_stage4_ep2_sinkproof_r3_runtimeauth/project_data.db`
Side-Effect Coverage: covered (Stage4 companion row persistence, raw rationale persistence, final sink authority row, canary hard-gate classification)
Confidence: `96%`

## 1. Intent

Isolate the remaining `sink_alignment_status:warn` lane after the `runtime-authority-drift live-canary closure` and answer one queue question:

- does the current workspace need a new Stage234 execution SSOT item, or is the remaining risk narrow enough to live as a sibling residual audit until an operator explicitly asks for `warn -> green` cleanup?

This audit does not reopen the repaired final sink and does not consume broader rerun authorization.

## 2. Pass 1. Structure and Scope

Included surfaces:

1. Stage4 `director_selections` companion-row lifecycle
2. Stage4 `attempt_raw_rationale` selection-surface / contract-snapshot rows
3. Stage4 `stage_attempts` final authority row for the same `attempt_key`
4. Stage4 canary hard-gate logic that currently converts the residual into `sink_alignment_status:warn`

Excluded surfaces:

1. broader Stage3/Stage234 rerun
2. retry-path proof; that remains the separate `stage4_retry_contract_not_exercised` warning
3. the already repaired final sink hole around `save_stage_attempt()`

Governing lane facts from the latest canonical docs:

1. the repaired final sink is now live-proven on `projects/_canary/canary_0_0_stage4_ep2_sinkproof_r3_runtimeauth`
2. the remaining Stage4 warning is explicitly lower authority than the repaired final sink
3. the latest Stage234 execution SSOT still treats broader rerun as operator-gated, so a new queue item should only be opened if the residual is bigger than a compact local observability fix

## 3. Pass 2. Evidence and Consistency

### 3.1 Raw selection rows are captured from the pre-fix selection surface

`modules/core/stage4_interview_round.py` shows that Stage4 persists the selection companion before any patch re-audit finalization:

1. `_persist_director_selection()` chooses `selected_before_fix` when the selection verdict is `PASS_WITH_FIX`
2. the same method builds `selection_kwargs` from the pre-fix selection surface
3. `_build_stage4_raw_rationale_records()` then persists:
   - `selection_contract_snapshot_raw`
   - `selection_surface_raw`
   from that same pre-fix `selection_kwargs` / `selection_advisory` payload

This means the raw selection records are intentionally a pre-final snapshot, not the final Stage4 authority row.

### 3.2 Final Stage4 authority is persisted later on a different surface

The same file later persists the final artifact through the pass-result logging path:

1. `_build_pass_result_logging_payload()` snapshots `patched_after_fix` when patch flow is exercised
2. the authoritative final row lands in `stage_attempts`
3. the canary summary already labels that final authority contract as:
   - `final_authority_sink = stage_attempts`
   - `selection_role = historical_companion`

So the final sink and the raw selection companion are already modeled as different authority planes.

### 3.3 The current companion row is hybrid, not purely historical

The residual comes from one more layer: `modules/core/db_manager.py` only partially re-syncs the companion row after patch re-audit.

`update_director_selection_rationale()` updates only:

1. `selection_reason`
2. `verdict_reason`
3. `fix_scope`
4. `advisory_warnings`

It does not update:

1. `verdict`
2. `candidate_key`
3. `content_hash`
4. `artifact_path`

Inference from the code and the DB row together:

- `director_selections` is intended to remain a historical companion row
- but the final rationale/advisory backfill mutates that historical row into a hybrid row
- the row therefore looks half pre-final and half post-patch

### 3.4 Direct DB evidence confirms the hybrid-row shape

For `attempt_key = s4:ep2:arc1:a1:20260415_145712` on the live-proof canary DB:

`stage_attempts` says:

1. `verdict = PASS`
2. `candidate_key = A|InPlace 수정`
3. `artifact_path = logs/artifacts/stage4/ep_0002/attempt_01/patched_after_fix__A_InPlace.txt`
4. `advisory_flags.gate_semantics.gate_basis = patch_reaudit_pass`

`director_selections` says:

1. `verdict = PASS_WITH_FIX`
2. `candidate_key = A|균형 전략`
3. `artifact_path = logs/artifacts/stage4/ep_0002/attempt_01/selected_before_fix__A.txt`
4. but `selection_reason` / `verdict_reason` already contain the final post-patch PASS wording
5. and `advisory_warnings.gate_semantics` also already carries the final `patch_reaudit_pass` semantics

`attempt_raw_rationale` preserves the pre-final companion snapshot:

1. `selection_contract_snapshot_raw` still reports `PASS_WITH_FIX` and `director_primary_pass_with_fix`
2. `selection_surface_raw` still points at `selected_before_fix__A.txt`

This is not a final sink regression. It is a hybrid companion-row contract.

### 3.5 Failure analysis already half-acknowledges the design, but the gate still warns

`modules/core/failure_analyzer.py` already recognizes the companion nature:

1. `selection_companion_status = pre_final_candidate` is collected as an explicit diagnostic
2. `final_authority_contract` says `stage_attempts` is authoritative and `director_selections` is historical companion review history
3. several structured sink comparisons skip `director_selections` when the row is marked `pre_final_candidate`

But the same analyzer still counts the raw selection drift as issues:

1. `raw_rationale_surface_mismatches`
2. `raw_rationale_contract_mismatches`

and those raw mismatches still contribute to `sink_alignment_summary.status = warn`.

### 3.6 One more metadata miss is still bundled into the same warning

The same canary summary also shows one structured metadata miss:

1. `gate_repair_metadata_missing`
2. field: `repair_contract_subtype`
3. sink: `pass_rate_monitor`

`modules/core/stage4_canary_tools.py` currently surfaces `sink_alignment_status:warn` whenever:

1. sink alignment is not `ok`, and
2. final-authority / companion / gate-repair digests do not fully settle to `ok`

So the current Stage4 warning is a bundle of:

1. hybrid pre-final selection companion drift
2. one missing `repair_contract_subtype` gate-repair metadata field

## 4. Pass 3. Execution and Queue Judgment

This residual does not warrant a new execution SSOT item yet.

Reasoning:

1. the repaired final authority sink is already live-proven
2. the remaining issue is bounded to Stage4 companion observability semantics plus one metadata completeness miss
3. opening a new queue item would add noise to an already crowded temp roadmap without changing broader Stage234 rerun posture

The correct current classification is:

- `sibling residual audit anchor`
- not `new open Stage234 realization lane`

If an operator later wants `warn -> green` cleanup, the likely patch shape is still compact and local:

1. choose one truthful contract for `director_selections`
2. either keep it fully historical and stop backfilling final rationale/advisory onto that row
3. or promote it to a true final companion row by updating verdict/candidate/artifact/content-hash consistently after patch re-audit
4. then decide whether raw selection rows should remain purely historical evidence rather than sink-alignment warning inputs
5. separately decide whether `repair_contract_subtype` is mandatory on `pass_rate_monitor` for this patch-reaudit path

## 5. Judgment

Bounded conclusion:

1. the remaining Stage4 `sink_alignment_status:warn` is not a reopen of the repaired final sink
2. the main residual is a hybrid companion-row contract around `director_selections` plus one metadata completeness miss
3. the current workspace does not need a new execution SSOT or temp-queue mirror for this alone
4. this audit is sufficient as the canonical sibling-residual anchor until an operator explicitly asks for hard-gate cleanup

## 6. Next Step

Recommended next step order:

1. keep the Stage234 execution SSOT and roadmap unchanged for now
2. if the goal is simply stronger proof coverage, run the separate retry-path canary first
3. if the goal is `warn -> green`, open a compact local Stage4 observability fix from this audit rather than a new broad Stage234 queue item
