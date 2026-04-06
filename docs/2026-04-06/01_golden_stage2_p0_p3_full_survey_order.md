# 01 Golden Stage2 P0-P3 Full Survey Order

Date: 2026-04-06
Status: final
Document Type: operator parallel survey order with provisional severity map
Canonical Path: `docs/2026-04-06/01_golden_stage2_p0_p3_full_survey_order.md`
Temp Mirror Path: `(none - order only)`
Track: narrative project audit
Mode: read-only 3-lane parallel survey; no regeneration; no code patching; final audit reserved for Codex
Confidence: `97%`

## 1. Purpose

This order splits the Stage 2 investigation for project `01_투자물_골든_` into three non-overlapping survey lanes.

The lanes do not write the final merged survey.

They only gather bounded evidence and write lane-local findings.

Codex performs the final merge, severity closure, and document audit after the three lane outputs land.

The question is not:

- `did the story itself collapse`

The question is:

- `does accepted Stage 2 artifact truth stay consistent with the operator-visible correction trail`
- `did the interrupted Arc 5 run leave any P0-P3 class residue`
- `which issues are true artifact defects versus interrupted-run observability gaps`

## 2. Frozen Baseline

Project root:

- `projects/01_투자물_골든_`

Live run status fixed by current evidence:

- accepted Stage 2 artifact JSON exists for `Arc 1` through `Arc 4`
- `Arc 4` had one rejected attempt and one accepted retry
- `Arc 5` entered preflight and generation startup, then stopped before any final verdict or artifact save

Higher-authority sinks for this wave:

- `project_data.db` tables `stage_attempts`, `director_selections`, `llm_calls`, `cost_log`
- `logs/artifacts/stage2/**`
- `logs/session/ui_events.jsonl`
- `logs/session/decisions.jsonl`
- `logs/session_20260406_151023.log`

Lower-authority or stale-after-interrupt sinks for this wave:

- `logs/pass_rate_monitor.json`
- `logs/runtime_audit_summary.json`

Family resolution for this survey is already fixed:

- `blockguide`

This wave is not a fresh narrative-production order.

It is a read-only audit of Stage 2 outputs already generated inside the project.

## 3. Fixed Read Before Starting

Every lane reads these first:

- `AGENTS.md`
- `docs/narrative-router/SSOT_narrative-router-integrated-order.md`
- `docs/blockguide/SSOT_blockguide-integrated-order.md`
- `docs/2026-04-06/01_golden_stage2_p0_p3_full_survey_order.md`

No lane needs to reopen broader system-track harnesses for this wave.

## 4. Global Guardrails

1. Do not regenerate Stage 2 content.
2. Do not patch code or mutate project data.
3. Do not modify `docs/temp/`.
4. Treat user interruption as an operational fact, not automatic narrative-content failure.
5. Promote severity only when at least two independent sinks support the claim.
6. Prefer byte-level UTF-8 reads when quoting artifact truth.
7. Findings first; summaries second.
8. Each terminal writes only its own lane output file.
9. No lane writes `01_golden_stage2_p0_p3_bounded_survey.md`.
10. Final cross-lane audit and severity closure are reserved for Codex.

## 5. Provisional Severity Map

### P0

Current bounded read found no confirmed `P0`.

Specifically, this pass found no:

- UTF-8 decode failure in inspected Stage 2 artifacts
- missing accepted artifact for `Arc 1` through `Arc 4`
- DB corruption signal in the inspected Stage 2 truth tables

### P1 Candidate

`auto-correct false-closure on field removal`

Evidence already visible:

- `logs/session/ui_events.jsonl` records that `arc_start_state` / `arc_end_state` removed `internal_energy` for `Arc 1`, `Arc 3`, and `Arc 4`
- accepted final artifacts for the same arcs still contain `internal_energy`

Why this is P1-candidate worthy:

- the console claims a genre-contract repair completed
- the saved accepted JSON disagrees
- if downstream consumers trust the saved artifact, the wrong family field still survives

### P2 Candidates

`interrupt-time stale summary sinks`

Evidence already visible:

- `logs/pass_rate_monitor.json` still shows the earlier Stage 0 timestamp and zero records
- `logs/runtime_audit_summary.json` still reflects the old shutdown summary and does not describe the Stage 2 run that produced four accepted arcs
- meanwhile DB + artifact sinks clearly show accepted `Arc 1` through `Arc 4`

Why this is P2-candidate worthy:

- an operator reading only summary sinks gets the wrong run state
- proof-digest style summaries degrade sharply after interrupted shutdown

### P3 Candidate

`Arc 5 partial residue without explicit interrupted-run closure`

Evidence already visible:

- UI and plain log show `Arc 5` preflight completion and generation startup
- `llm_calls` has `ep_num=22` preflight-side activity, while the plain log shows `ArcEnsembleGenerator` call start without a later completed Stage 2 attempt record
- no matching `stage_attempts`, `director_selections`, or saved Stage 2 artifact exists for `Arc 5`

Why this is P3-candidate worthy:

- the run is recoverable, but the closure state is implicit rather than explicit
- manual resume requires reading multiple sinks instead of one final interrupted marker

## 6. Terminal Ownership

### Terminal 1

- owner: `artifact truth lane`
- mission: `accepted artifact truth / txt round-trip / state-carryover ledger`
- focus:
  - `plans/arcs/arc_001.txt` through `arc_004.txt`
  - accepted Stage 2 artifact JSON for `Arc 1` through `Arc 4`
  - rejected `Arc 4` artifact only where it helps explain a saved-contract mismatch
  - `joint_docs.final_location`
  - `arc_start_state` / `arc_end_state`
  - `items_acquired` / `items_consumed`
  - `investment_calc`
  - numeric and carryover spine
- output:
  - `docs/2026-04-06/01_golden_stage2_lane1_artifact_truth.md`

### Terminal 2

- owner: `observability lane`
- mission: `console / sink visibility / stale-summary mapping`
- focus:
  - `logs/session/ui_events.jsonl`
  - `logs/session/decisions.jsonl`
  - `logs/quality_metrics.jsonl`
  - `logs/pass_rate_monitor.json`
  - `logs/runtime_audit_summary.json`
  - `logs/session_20260406_151023.log`
  - what the operator can see directly
  - what remains hidden or stale after interruption
- output:
  - `docs/2026-04-06/01_golden_stage2_lane2_observability.md`

### Terminal 3

- owner: `db residue lane`
- mission: `DB truth / Arc 5 residue / recoverability`
- focus:
  - `project_data.db`
  - `stage_attempts`
  - `director_selections`
  - `llm_calls`
  - `cost_log`
  - `logs/artifacts/stage2/**`
  - whether any hidden partial commit exists for `Arc 5`
  - whether accepted/rejected artifact identity remains recoverable
- output:
  - `docs/2026-04-06/01_golden_stage2_lane3_db_residue.md`

## 7. Required Questions Per Lane

### Terminal 1 Questions

1. Where does `arc txt` truth diverge from accepted Stage 2 artifact truth?
2. Which divergences are wording-only, and which are saved-contract mismatches?
3. Does the numeric/business spine remain coherent even where packet cleanup is weak?
4. Beyond `internal_energy`, do other false-cleanup fields or item/state drifts survive?

### Terminal 2 Questions

1. Which high-signal Stage 2 reasons are visible in console/UI?
2. Which high-signal reasons remain only in lower-level or stale sinks?
3. Which summary sinks become misleading after the interrupted `Arc 5` run?
4. Can an operator recover the real state from logs alone without touching DB?

### Terminal 3 Questions

1. Does any hidden partial commit exist for `Arc 5`?
2. Are accepted and rejected artifacts, attempts, and selections still recoverable without identity collision?
3. Which DB sinks remain authoritative after interruption, and which do not?
4. Is `Arc 5` best classified as `cleanly interrupted before verdict`, or is there stronger residue?

## 8. Output Contract

Each lane writes exactly one lane-local output file.

Lane outputs must use this section shape:

1. `Coverage`
2. `Findings`
3. `Non-Issues`
4. `Severity Hint`
5. `Stop`

Required stop line for every lane:

- `read-only lane survey complete; no project artifacts mutated`

Final merged outputs are reserved for Codex only:

- `docs/2026-04-06/01_golden_stage2_p0_p3_bounded_survey.md`
- optional `docs/2026-04-06/01_golden_stage2_p0_p3_evidence.json`

The three lanes must not overwrite each other and must not write the final merged survey.

## 9. Paste-Ready Orders

### Terminal 1

```text
Narrative-project read-only survey lane. This lane owns `01_투자물_골든_ Stage 2 artifact truth`.

Read first:
- AGENTS.md
- docs/narrative-router/SSOT_narrative-router-integrated-order.md
- docs/blockguide/SSOT_blockguide-integrated-order.md
- docs/2026-04-06/01_golden_stage2_p0_p3_full_survey_order.md

Fixed premises:
- Do not regenerate Stage 2 content.
- No code patching.
- Do not mutate project files or docs/temp.
- Do not write the final merged survey.
- Write exactly one lane output file.

Inspect:
- projects/01_투자물_골든_/plans/arcs/arc_001.txt through arc_004.txt
- projects/01_투자물_골든_/logs/artifacts/stage2/arc_001/attempt_01/final_arc__creative.json
- projects/01_투자물_골든_/logs/artifacts/stage2/arc_002/attempt_01/final_arc__creative.json
- projects/01_투자물_골든_/logs/artifacts/stage2/arc_003/attempt_01/final_arc__balanced.json
- projects/01_투자물_골든_/logs/artifacts/stage2/arc_004/attempt_01/rejected_arc__conservative.json
- projects/01_투자물_골든_/logs/artifacts/stage2/arc_004/attempt_02/final_arc__creative.json

Questions:
1. Where does arc txt truth diverge from accepted artifact truth?
2. Which differences are wording-only versus saved-contract mismatches?
3. Does the numeric/business spine remain coherent?
4. Beyond internal_energy, do any other cleanup mismatches survive?

Output:
- docs/2026-04-06/01_golden_stage2_lane1_artifact_truth.md

Section shape:
1. Coverage
2. Findings
3. Non-Issues
4. Severity Hint
5. Stop

Required stop line:
- read-only lane survey complete; no project artifacts mutated
```

### Terminal 2

```text
Narrative-project read-only survey lane. This lane owns `01_투자물_골든_ Stage 2 observability`.

Read first:
- AGENTS.md
- docs/narrative-router/SSOT_narrative-router-integrated-order.md
- docs/blockguide/SSOT_blockguide-integrated-order.md
- docs/2026-04-06/01_golden_stage2_p0_p3_full_survey_order.md

Fixed premises:
- Do not regenerate Stage 2 content.
- No code patching.
- Do not mutate project files or docs/temp.
- Do not write the final merged survey.
- Write exactly one lane output file.

Inspect:
- projects/01_투자물_골든_/logs/session/ui_events.jsonl
- projects/01_투자물_골든_/logs/session/decisions.jsonl
- projects/01_투자물_골든_/logs/quality_metrics.jsonl
- projects/01_투자물_골든_/logs/pass_rate_monitor.json
- projects/01_투자물_골든_/logs/runtime_audit_summary.json
- projects/01_투자물_골든_/logs/session_20260406_151023.log

Questions:
1. Which Stage 2 reasons are visible in console/UI and which are not?
2. Which sinks become stale or misleading after the interrupted Arc 5 run?
3. Can an operator recover true run state from logs alone?
4. Where do console claims disagree with saved artifact truth?

Output:
- docs/2026-04-06/01_golden_stage2_lane2_observability.md

Section shape:
1. Coverage
2. Findings
3. Non-Issues
4. Severity Hint
5. Stop

Required stop line:
- read-only lane survey complete; no project artifacts mutated
```

### Terminal 3

```text
Narrative-project read-only survey lane. This lane owns `01_투자물_골든_ Stage 2 DB residue and Arc 5 closure`.

Read first:
- AGENTS.md
- docs/narrative-router/SSOT_narrative-router-integrated-order.md
- docs/blockguide/SSOT_blockguide-integrated-order.md
- docs/2026-04-06/01_golden_stage2_p0_p3_full_survey_order.md

Fixed premises:
- Do not regenerate Stage 2 content.
- No code patching.
- Do not mutate project files or docs/temp.
- Do not write the final merged survey.
- Write exactly one lane output file.

Inspect:
- projects/01_투자물_골든_/project_data.db
- project_data.db tables: stage_attempts, director_selections, llm_calls, cost_log
- projects/01_투자물_골든_/logs/artifacts/stage2/**
- projects/01_투자물_골든_/logs/session_20260406_151023.log
- projects/01_투자물_골든_/logs/session/ui_events.jsonl

Questions:
1. Does any hidden partial commit exist for Arc 5?
2. Are attempt/artifact identities still cleanly recoverable?
3. Which DB sinks remain authoritative after interruption?
4. Is Arc 5 best classified as cleanly interrupted before verdict, or is stronger residue present?

Output:
- docs/2026-04-06/01_golden_stage2_lane3_db_residue.md

Section shape:
1. Coverage
2. Findings
3. Non-Issues
4. Severity Hint
5. Stop

Required stop line:
- read-only lane survey complete; no project artifacts mutated
```

## 10. Codex Audit Reservation

After the three lane outputs land, Codex alone performs the final merge.

Codex responsibilities:

- re-read the three lane outputs
- re-check any conflicting claim against source sinks
- close the final `P0/P1/P2/P3` severity verdict
- write `docs/2026-04-06/01_golden_stage2_p0_p3_bounded_survey.md`
- run 3-pass audit on the merged human-facing survey before final save

The lanes do not self-merge and do not perform the final severity closure.

## 11. Stop Conditions

Any lane must stop immediately and escalate if it proves one of:

- accepted artifact bytes are corrupted or undecodable
- accepted artifact truth is missing for an arc already marked PASS in DB
- accepted and rejected artifacts share the same persisted identity in a way that breaks recoverability

Otherwise each lane stops after:

- clearing or strengthening its assigned hypotheses
- writing one lane-local document
- leaving final merge and audit to Codex

## 12. Current Best Reading

The current best bounded reading is:

- `no confirmed P0`
- `one strong P1 candidate` around false-reported field cleanup versus saved artifact truth
- `one strong P2 class observability gap` caused by interrupted-run stale summary sinks
- `one likely P3 operational residue` around incomplete `Arc 5` closure marking

So the next correct move is:

- `parallel survey and classify`

not:

- `resume blind`
- `patch blind`
- `declare Stage 2 clean`

## 13. 3-Pass Audit Note

Pass 1:

- restructured the document from a single-lane order into a non-overlapping 3-lane parallel order
- added lane-local output contracts so the terminals do not collide on one file

Pass 2:

- checked that the new lane split matches the actual evidence families: artifact truth, observability, and DB residue
- reserved final severity closure and final merged survey writing for Codex only

Pass 3:

- re-checked that the document now explicitly contains paste-ready lane orders
- re-checked that no lane is instructed to overwrite `01_golden_stage2_p0_p3_bounded_survey.md`
- confirmed this remains a read-only survey order rather than an execution SSOT
