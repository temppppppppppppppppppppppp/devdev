# 01 Golden Stage2 P0-P3 Bounded Survey

Date: 2026-04-06
Status: final
Document Type: bounded survey
Canonical Path: `docs/2026-04-06/01_golden_stage2_p0_p3_bounded_survey.md`
Source Order:
- `docs/2026-04-06/01_golden_stage2_p0_p3_full_survey_order.md`
Merged Lane Inputs:
- `docs/2026-04-06/01_golden_stage2_lane1_artifact_truth.md`
- `docs/2026-04-06/01_golden_stage2_lane2_observability.md`
- `docs/2026-04-06/01_golden_stage2_lane3_db_residue.md`
Confidence: `96%`
3-Pass Audit: `completed`

## 1. Coverage

This survey merged three read-only lanes and rechecked their strongest claims against source sinks before closing severity.

Project scope:

- `projects/01_투자물_골든_`

Primary source sinks rechecked by Codex:

- `projects/01_투자물_골든_/plans/arcs/arc_001.txt` through `arc_004.txt`
- `projects/01_투자물_골든_/logs/artifacts/stage2/arc_001/attempt_01/final_arc__creative.json`
- `projects/01_투자물_골든_/logs/artifacts/stage2/arc_002/attempt_01/final_arc__creative.json`
- `projects/01_투자물_골든_/logs/artifacts/stage2/arc_003/attempt_01/final_arc__balanced.json`
- `projects/01_투자물_골든_/logs/artifacts/stage2/arc_004/attempt_01/rejected_arc__conservative.json`
- `projects/01_투자물_골든_/logs/artifacts/stage2/arc_004/attempt_02/final_arc__creative.json`
- `projects/01_투자물_골든_/logs/session/ui_events.jsonl`
- `projects/01_투자물_골든_/logs/session/decisions.jsonl`
- `projects/01_투자물_골든_/logs/quality_metrics.jsonl`
- `projects/01_투자물_골든_/logs/pass_rate_monitor.json`
- `projects/01_투자물_골든_/logs/runtime_audit_summary.json`
- `projects/01_투자물_골든_/logs/session_20260406_151023.log`
- `projects/01_투자물_골든_/project_data.db`

Bounded scope only:

- accepted Stage 2 truth for `Arc 1` through `Arc 4`
- rejected `Arc 4` only as a comparison artifact
- interrupted `Arc 5` residue and observability
- no Stage 3 or Stage 4 reopening
- no code or artifact mutation

## 2. Findings

### F-1. Confirmed P1: console-level repair claim and saved artifact truth disagree on `internal_energy`

This is the strongest confirmed issue in the survey.

What the operator sees:

- `ui_events.jsonl` records auto-correct claims that `internal_energy` was removed from `arc_start_state` and/or `arc_end_state` for `Arc 1`, `Arc 3`, and `Arc 4`

What the saved accepted artifacts contain:

- `Arc 1` accepted artifact still has `internal_energy: 0` in both start and end state
- `Arc 3` accepted artifact still has `internal_energy: 100` in both start and end state
- `Arc 4` accepted artifact still has `internal_energy: 100` in both start and end state

Why this closes as P1:

- the operator-visible sink reports a family-contract cleanup as complete
- the accepted artifact bytes disagree
- the mismatch is not wording-only; it is a saved-contract mismatch in accepted output

Merged verdict:

- `confirmed P1`

### F-2. Confirmed P2: summary sinks become stale and misleading after the interrupted Stage 2 run

Two summary sinks remain frozen at the earlier Stage 0 shutdown:

- `logs/pass_rate_monitor.json`
- `logs/runtime_audit_summary.json`

Observed stale behavior:

- `pass_rate_monitor.json` still shows zero records even though Stage 2 later produced four accepted arcs and one rejected attempt
- `runtime_audit_summary.json` still reports the earlier zero-event shutdown state and wrong session lineage for the Stage 2 run

Higher-authority sinks disagree:

- `stage_attempts` contains five Stage 2 attempt records
- `director_selections` contains five matching selection records
- `decisions.jsonl` records the Arc 1 to Arc 4 verdict sequence
- `ui_events.jsonl` and the plain session log show the Stage 2 run in detail

Why this closes as P2:

- there is no artifact corruption or missing accepted truth
- but an operator who trusts the summary sinks alone gets the run state badly wrong
- this is an observability and post-interrupt summary-truth defect, not just a cosmetic inconvenience

Merged verdict:

- `confirmed P2`

### F-3. Confirmed P3: `Arc 5` is implicitly interrupted, not explicitly closed

The survey confirmed a narrow but real interruption-residue issue.

What exists for `Arc 5`:

- `ui_events.jsonl` shows preflight completion and generation startup
- the plain session log shows the run advanced into ensemble dispatch
- `llm_calls` has three completed `ep_num=22` preflight-side records

What does not exist for `Arc 5`:

- no `stage_attempts` row
- no `director_selections` row
- no `decisions.jsonl` record
- no `cost_log` row
- no saved Stage 2 artifact directory or file

Important closure:

- there is no hidden partial artifact
- there is no hidden partial verdict
- there is no identity collision with accepted `Arc 1` through `Arc 4`

Why this closes as P3:

- the operational risk is low because no authoritative accepted or rejected artifact was partially committed
- but the interruption state is implicit
- reconstructing the stop point requires combining at least `llm_calls`, `stage_attempts`, and the session log

Merged verdict:

- `confirmed P3`

### F-4. P2-candidate retained: `power_changes` chain is internally inconsistent across accepted artifacts

Codex rechecked the accepted artifacts and confirmed the lane's raw numbers:

- `Arc 1` `end_power = 15`
- `Arc 2` `start_power = 10`, `end_power = 25`
- `Arc 3` `start_power = 10`, `end_power = 25`
- `Arc 4` `start_power = 30`, `end_power = 45`

So the arc-to-arc chain does not carry forward cleanly.

Why this stays candidate instead of confirmed P2:

- the inconsistency is real at the artifact level
- but this bounded survey did not trace an active consumer that materially depends on `power_changes`
- the main business spine (`capital`, `total_assets`, `items`, `location`, `investment_calc`) remains coherent

Merged verdict:

- `P2-candidate`

### F-5. Confirmed P3: minor metadata duplication noise exists in accepted artifacts

Two low-severity metadata issues were confirmed:

- `npc_introductions` introduces 박성호 in both `Arc 1` and `Arc 2`
- `Arc 2` accepted artifact contains a duplicate/null-episode `relationship_changes` entry for 박성호

These do not break accepted artifact identity or the main narrative spine, but they create avoidable noise for any downstream metadata aggregator.

Merged verdict:

- `confirmed P3`

## 3. Non-Issues

### N-1. No confirmed P0

This survey found no:

- UTF-8 decode failure in inspected txt or JSON artifacts
- missing accepted artifact for any arc already marked PASS
- DB corruption signal in inspected truth tables
- accepted/rejected identity collision

### N-2. Accepted Stage 2 artifact identity is clean and recoverable

`stage_attempts`, `director_selections`, artifact path, and content hash all align for:

- `Arc 1` accepted creative
- `Arc 2` accepted creative
- `Arc 3` accepted balanced
- `Arc 4` rejected conservative
- `Arc 4` accepted creative

The rejected `Arc 4` artifact is cleanly distinguishable from the accepted retry.

### N-3. Main narrative business spine is coherent across accepted arcs

The strongest narrative-contract signals remain stable across accepted `Arc 1` through `Arc 4`:

- capital progression
- total asset progression
- equipment carryover
- location carryover
- accepted `investment_calc` values
- accepted `Arc 4` numeric truth aligning with the final txt and rejecting the earlier wrong candidate

This is why the correct global reading is not `Stage 2 content collapse`.

### N-4. `Arc 5` left no hidden accepted or rejected artifact

The interruption happened after preflight and dispatch, but before any verdict-carrying or artifact-carrying sink committed `Arc 5`.

That means resume/recovery can still anchor safely on accepted `Arc 4` truth.

### N-5. Console visibility of Director verdicts is strong

The operator-visible Stage 2 console trail does expose:

- Director PASS / PASS_WITH_FIX / REJECT verdicts
- the detailed `Arc 4` REJECT reason
- retry progression through accepted `Arc 4`

The observability weakness is concentrated in post-interrupt summary truth and false-closure auto-correct claims, not in Director verdict visibility.

## 4. Severity Verdict

Closed reading:

- `P0`: none confirmed
- `P1`: confirmed
- `P2`: confirmed
- `P3`: confirmed

Finding map:

| ID | Closed Severity | Reading |
|----|-----------------|---------|
| F-1 | `P1` | `internal_energy` removal is claimed in console but survives in accepted artifacts |
| F-2 | `P2` | `pass_rate_monitor.json` and `runtime_audit_summary.json` become stale and misleading after interruption |
| F-3 | `P3` | `Arc 5` interruption is implicit rather than explicitly marked |
| F-4 | `P2-candidate` | `power_changes` chain drift is real in accepted artifacts, but consumer impact not closed in this survey |
| F-5 | `P3` | duplicate NPC introduction / duplicate-null relationship metadata noise |

Merged summary:

- Stage 2 produced usable accepted artifacts through `Arc 4`
- the highest-confidence artifact defect is a saved-contract mismatch on family-field cleanup
- the highest-confidence operational defect is stale summary truth after interrupted runtime
- the interrupted `Arc 5` state is recoverable, but not explicitly marked

## 5. Minimal Next Wave

Smallest queue-safe follow-up, still bounded:

1. `artifact contract cleanup wave`
   - target: false-closure between auto-correct claims and saved accepted artifact bytes
   - first focus: `internal_energy`

2. `interrupted-run summary truth wave`
   - target: refresh or explicitly mark `pass_rate_monitor.json` and `runtime_audit_summary.json` after interrupted sessions

3. `explicit Arc interruption marker wave`
   - target: one authoritative sink that records `started but no verdict committed`
   - this would close the current P3 reconstruction burden

4. `power_changes consumer trace`
   - only then decide whether F-4 should be promoted from `P2-candidate` to confirmed severity

This survey does not justify:

- regenerating the existing accepted arcs
- reclassifying Stage 2 as a narrative-content failure
- promoting this above unrelated active work without a queue decision

## 6. Stop

read-only Stage 2 survey complete; no project artifacts mutated

## 7. 3-Pass Audit Note

Pass 1:

- merged the three lane outputs into one bounded reading
- removed duplicate phrasing and grouped findings by confirmed severity

Pass 2:

- rechecked the strongest claims directly against source artifacts, logs, and DB sinks
- corrected line-count and interruption wording from the raw lane outputs where needed

Pass 3:

- rechecked that the final survey does not overstate F-4 beyond surveyed evidence
- confirmed the final close is `usable Stage 2 with P1/P2/P3 defects`, not `Stage 2 collapse`
