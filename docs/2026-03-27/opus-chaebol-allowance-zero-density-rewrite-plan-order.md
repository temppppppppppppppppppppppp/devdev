# OPUS Chaebol Allowance Zero Density Rewrite-Plan Order

Date: 2026-03-27
Track: narrative pipeline
Status: active
Scope: single-work OPUS order for `chaebol_allowance_zero`

## 1. Order Intent

This order fixes the target to `chaebol_allowance_zero` and asks OPUS to complete exactly one bounded unit:

- `density-recovery rewrite plan`

Current lane truth:

- family: `blockguide`
- entry type: existing `TR + BI` pair in `_quarantine`
- the current uncertainty is not whether material exists
- the current uncertainty is which live pair path is authoritative and how to recover narrative density without drifting away from the work's core

This is not a fresh Planning, fresh TR, or fresh BI generation order.

## 2. Non-Negotiable Rules

- UTF-8 only
- read router -> family SSOT -> relevant revival context before doing anything else
- one work, one owner, one unit
- no same-work concurrent editing
- no code or system edits
- do not rewrite the live pair in this run
- do not redesign BI in this run
- do not promote to active path in this run
- do not force runtime probe in this run

## 3. Canonical Live Target

Use the currently existing live pair for diagnosis:

- TR: `treatments/_quarantine/chaebol_allowance_zero_tr_block_070_draft.json`
- BI: `bible/_quarantine/0_bi_chaebol_allowance_zero.json`

Live shape notes:

- the `TR` is a raw `list`, not `dict.blocks`
- the roadmap sits at `MasterBible.plot_roadmap`, not top-level `plot_roadmap`

Treat these as the authoritative live pair for this order unless direct file evidence disproves them.

## 4. Source-Authority Conflict

There is a live path conflict that must be acknowledged, not ignored.

1. `treatments/preprocess/chaebol_allowance_zero/source_manifest.json`
   - still lists root canonical sources:
   - `treatments/chaebol_allowance_zero_tr_block_070_draft.json`
   - `bible/0_bi_chaebol_allowance_zero.json`
2. `docs/2026-03-24/chaebol_allowance_zero_4axis_audit_report.md`
   - also cites missing root paths such as:
   - `treatments/chaebol_allowance_zero_tr_block_070_draft.json`
   - `bible/chaebol_allowance_zero_bi.json`
3. current live workspace
   - does not contain those root pair files
   - does contain the quarantine pair and duplicate BI variants

Therefore the order must first fix:

- live pair truth
- duplicate-path status
- stale-path authority downgrade

## 5. Proven Prior Checks

These older checks remain useful evidence, but they do not close the current question by themselves.

1. `treatments/preprocess/chaebol_allowance_zero/phase0_ready_snapshot.json`
   - `manual_audit_pass = true`
2. `treatments/audit_reports/chaebol_allowance_zero_full_retry_vs_failed_audit.md`
   - retry `TR` materially improved over failed baseline
3. `bible/audit_reports/chaebol_allowance_zero_bi_5pass.md`
   - structure / sync `PASS`
4. `bible/audit_reports/chaebol_allowance_zero_bi_retry_vs_failed.md`
   - retry `BI` supersedes failed `BI`
5. `docs/2026-03-24/chaebol_allowance_zero_4axis_audit_report.md`
   - system fit `PASS`
   - narrative consistency `CONDITIONAL PASS`
   - TR-BI consistency `PASS / CONDITIONAL`
   - density / looseness `FAIL`

Interpretation:

- the pair is structurally consumable
- the failure is primarily narrative density and template repetition
- this is not a simple schema patch problem

## 6. Why This Run Exists

The live material has two separate problems:

1. path authority drift
2. density collapse after the early hand-crafted band

The 4-axis audit isolates the main weakness:

- `Block 1-6` = high-density manual band
- `Block 7-70` = template-heavy low-density band

Immediate blocker issues called out there:

- 2006 regression point vs 2018 story start gap
- Block 13 opponent mismatch
- historical events underfilled after the first band
- FinanceHUD / seed-state lag
- large mid/late sections reading like skeletonized operations summary

Therefore the honest next task is not `promotion`, not `probe`, and not blind full rewrite.

The honest next task is:

- produce a bounded density-recovery rewrite plan

## 7. Mandatory Reads

Read these in order:

1. `docs/narrative-router/SSOT_narrative-router-integrated-order.md`
2. `docs/blockguide/SSOT_blockguide-integrated-order.md`
3. `docs/narrative-router/material-revival-ladder-harness.md`
4. `docs/2026-03-24/chaebol_allowance_zero_4axis_audit_report.md`
5. `treatments/preprocess/chaebol_allowance_zero/source_manifest.json`
6. `treatments/preprocess/chaebol_allowance_zero/phase0_ready_snapshot.json`
7. `treatments/audit_reports/chaebol_allowance_zero_full_retry_vs_failed_audit.md`
8. `bible/audit_reports/chaebol_allowance_zero_bi_5pass.md`
9. `bible/audit_reports/chaebol_allowance_zero_bi_retry_vs_failed.md`
10. `treatments/_quarantine/chaebol_allowance_zero_tr_block_070_draft.json`
11. `bible/_quarantine/0_bi_chaebol_allowance_zero.json`

## 8. Immediate Goal

Execute exactly one bounded `density-recovery rewrite plan` for `chaebol_allowance_zero`.

The plan must answer:

- what the authoritative live pair is
- which issues are immediate blockers versus later-wave cleanup
- which block range should be rewritten first
- what must be preserved so the work does not drift into generic market-investment spectacle

## 9. Planning Method

### 9.1 Canonical Pair / Duplicate-Path Truth

Verify, at minimum:

- which pair files actually exist now
- which documents still point at missing root files
- which duplicate BI files remain reference-only
- whether the canonical live pair should stay in `_quarantine` for the next wave

### 9.2 Failure-to-Retry Delta Reuse

Extract what is still worth preserving from the retry wave:

- opponent diversity gains
- weakness diversity gains
- B2B support-system cashflow emphasis
- title sequence / arc sequence / core hook continuity

Do not let the rewrite plan throw away the parts the retry already fixed.

### 9.3 Rewrite-Band Segmentation

Use the 4-axis audit and direct TR sampling to segment the rewrite work.

Required segmentation:

- benchmark band: `Block 1-6`
- first rewrite band: `Block 7-15`
- second rewrite band: `Block 16-35`
- later rewrite band: `Block 36-70`

Judge:

- repeated `solution` cadence
- repeated `weakness_exploited`
- lack of concrete item / event / heavyweight pressure
- low scene pressure
- missing historical / market / policy anchors
- whether the band still functions as treatment or only as plot skeleton

### 9.4 Immediate-Fix vs Rewrite-Wave Split

Separate:

- immediate blockers:
  - 2006 -> 2018 gap
  - Block 13 opponent mismatch
  - canonical-path truth
- later-wave rewrites:
  - Block 7-70 density recovery
  - heavyweights / historical events / item density
  - HUD / seed-state cleanup

### 9.5 Next-Unit Decision

At the end of the planning run, choose exactly one next unit:

- `rewrite block wave 1`
- `canonical-path patch`
- `weakness report only`

Do not choose more than one.

## 10. Fixed Creative Constraints

Do not wash out these anchors:

- support-system cashflow warfare
- funeral / catering / hotel / factory / hospital / settlement / nationwide operations ladder
- `business_growth_profile` + `office_power_profile`
- no free family bailout
- inheritance is not the growth engine
- repeated cashflow and approval choke points are the battlefield

Known drift to avoid:

- turning the work into pure stock-market or M&A spectacle
- flattening all operations into one generic “operations business” blob
- losing the B2B daily-expense choke-point premise

## 11. Deliverable

Save exactly one main report:

- `docs/2026-03-27/chaebol-allowance-zero-density-rewrite-plan.md`

The report should include:

- target pair paths
- path-authority note
- duplicate-file note
- preserved strengths from the retry version
- rewrite-band segmentation
- immediate-fix list
- first-wave rewrite recommendation
- final verdict: `pass`, `mixed`, or `fail`
- next unit only

## 12. Stop Conditions

Stop immediately and report if any of the following occurs:

- canonical pair identity cannot be fixed because duplicate variants conflict materially
- live pair contents cannot be parsed cleanly as UTF-8
- the plan would require immediate broad rewrite to answer a bounded planning question
- confidence falls below 95% for the chosen next unit and no smaller bounded step exists

If the truth is mixed, do not escape into vague optimism.
Record the ambiguity and choose the smaller next step.

## 13. Expected Next Unit After This Order

- if path truth is clear and wave segmentation is clear: `rewrite block wave 1`
- if path truth is still the primary blocker: `canonical-path patch`
- if the material is not worth another wave now: `weakness report only`

## 14. Handoff Format

End with this exact flat report:

```text
work_id: chaebol_allowance_zero
current_stage: audit_or_repair
finished_unit: density-recovery rewrite plan
changed_files: ...
next_unit: ...
stop_reason: ...
```

## 15. 3-Pass Self Audit

### Pass 1. Contract Alignment

- target is fixed to one `work_id`
- order stays inside router + blockguide + existing-pair planning boundaries
- no same-work parallel editing is authorized
- no fresh generation stages are mixed in

### Pass 2. Operational Usefulness

- the next unit is singular and concrete: `density-recovery rewrite plan`
- stale root-path authority is surfaced explicitly
- deliverable and stop conditions are explicit

### Pass 3. Integrity

- saved under dated `docs/2026-03-27/`
- UTF-8 only
- no code-edit instructions
- no multi-unit overreach beyond one bounded planning step

Confidence:
- 97% that `density-recovery rewrite plan` is the correct next OPUS unit for this pair
