# OPUS US AI Exile Monopoly TR Weakness Triage Order

Date: 2026-03-27
Track: narrative pipeline
Status: active
Scope: single-work OPUS order for `us_ai_exile_monopoly`

## 1. Order Intent

This order fixes the target to `us_ai_exile_monopoly` and asks OPUS to complete exactly one bounded unit:

- `source-TR weakness triage`

Current lane truth:

- family: `blockguide`
- entry type: existing `TR + BI` pair in `_quarantine`
- pair admission is not the current uncertainty
- the current uncertainty is whether the source `TR` is narratively salvageable enough for revival, or whether it is only structurally consumable

This is not a fresh Planning, fresh TR, or fresh BI generation order.

## 2. Non-Negotiable Rules

- UTF-8 only
- read router -> family SSOT -> relevant revival context before doing anything else
- one work, one owner, one unit
- no same-work concurrent editing
- no code or system edits
- do not regenerate TR in this run
- do not redesign BI in this run
- do not promote to active path in this run
- do not force runtime probe in this run just to escape narrative weakness

## 3. Canonical Target

- work_id: `us_ai_exile_monopoly`
- TR: `treatments/_quarantine/us_ai_exile_monopoly_tr_block_070_draft.json`
- BI: `bible/_quarantine/0_bi_us_ai_exile_monopoly.json`

Treat these quarantine files as the authoritative pair for this order.

Ignore non-canonical duplicates for this run:

- `treatments/_quarantine/08_us_ai_exile_monopoly_tr_block_070_draft.json`
- `bible/_quarantine/08_us_ai_exile_monopoly_bi.json`
- `bible/_quarantine/us_ai_exile_monopoly_bi.json`

## 4. Live Facts Already Visible

The following live facts are already visible and should be treated as the current default truth unless a direct file read disproves them.

1. TR artifact count:
   - live `TR` currently contains `70` blocks
2. BI structure:
   - live `MasterBible.plot_roadmap` currently contains `70` entries
   - `AssetLibrary.KeyNPCs` count: `10`
   - `WorldState.opponent_transition_plan` count: `3`
   - `WorldState.front_sector_by_arc` count: `7`
3. no current preprocess base:
   - `treatments/preprocess/us_ai_exile_monopoly/` is not present right now
4. direct repetition signal from live TR:
   - `execution_doctrine` is repeated verbatim across blocks
   - `weakness_exploited` repeats in long runs
   - `solution` paragraphs reuse the same contract-first cadence

## 5. Proven Prior Checks

These older checks are useful evidence, but they do not close the current question by themselves.

1. `docs/2026-03-10/us_ai_exile_monopoly_tr_3pass_audit.md`
   - result: `PASS`
2. `docs/2026-03-10/us_ai_exile_monopoly_density_and_tr_bi_3pass_audit.md`
   - result: `PASS`
3. `docs/2026-03-10/us_ai_exile_monopoly_blockguide_updated_reaudit.md`
   - result: `PASS`
4. `treatments/audit_reports/us_ai_exile_monopoly_tr_gate_20260312.md`
   - result: `PASS`
5. `bible/audit_reports/us_ai_exile_monopoly_bi_5pass_20260312.md`
   - result: `PASS`

Interpretation:

- structure and density gates passed
- pair parsing and synchronization passed
- this does not yet prove sceneability or runtime-worth narrative texture

## 6. Conflict To Reconcile

Two later sources narrow the real problem:

1. `docs/2026-03-12/codex_chaebol_allowance_zero_post_script_patch_quality_comparison.md`
   - generic BI builder also builds this work
   - but the AI lane still fails because source `TR` hits `source_tr_weakness_repeat_gate`
2. `docs/2026-03-26/blockguide-quarantine-static-quality-survey.md`
   - strong commercial hook
   - weak sceneability
   - near-zero dialogue
   - summary-only business slabs
   - repeated template execution

Therefore the honest next task is not `BI repair`, not `promotion`, and not `Stage probe`.

The honest next task is:

- isolate the real source-TR weakness
- decide whether the pair has a usable spine or needs rewrite-first treatment

## 7. Mandatory Reads

Read these in order:

1. `docs/narrative-router/SSOT_narrative-router-integrated-order.md`
2. `docs/blockguide/SSOT_blockguide-integrated-order.md`
3. `docs/narrative-router/material-revival-ladder-harness.md`
4. `docs/2026-03-10/us_ai_exile_monopoly_tr_3pass_audit.md`
5. `docs/2026-03-10/us_ai_exile_monopoly_density_and_tr_bi_3pass_audit.md`
6. `treatments/audit_reports/us_ai_exile_monopoly_tr_gate_20260312.md`
7. `bible/audit_reports/us_ai_exile_monopoly_bi_5pass_20260312.md`
8. `docs/2026-03-12/codex_chaebol_allowance_zero_post_script_patch_quality_comparison.md`
9. `docs/2026-03-26/blockguide-quarantine-static-quality-survey.md`
10. `treatments/_quarantine/us_ai_exile_monopoly_tr_block_070_draft.json`
11. `bible/_quarantine/0_bi_us_ai_exile_monopoly.json`

## 8. Immediate Goal

Execute exactly one bounded `source-TR weakness triage` for `us_ai_exile_monopoly`.

The triage must answer:

- what is the real source weakness now
- whether the weakness is narrative-only or contract-relevant
- whether the current pair is still a salvageable spine or is rewrite-first
- what the smallest honest next unit is

## 9. Triage Method

### 9.1 Canonical Pair / Duplicate-Path Truth

Verify, at minimum:

- the canonical pair paths
- duplicate-path presence
- which earlier audits refer to root paths versus quarantine paths
- whether those older audits can still be treated as relevant evidence

### 9.2 Repetition Map

Build a small repetition ledger for:

- `solution`
- `weakness_exploited`
- `execution_doctrine`
- opponent phrasing

Rule:

- do not let numeric uniqueness metrics alone override direct phrase repetition evidence
- if 70 unique `deal_type` values still produce the same reading experience, say so directly

### 9.3 Bounded Sceneability Sample

Sample the pair without inflating into a rewrite.

Recommended windows:

- early hook: `Block 1-5`
- middle pressure: `Block 21-35`
- late escalation: `Block 55-70`

Judge:

- dialogue presence or absence
- scene pressure versus contract summary
- voice separation between protagonist, opponent, and partners
- spatial / sensory cues
- whether AI domain texture survives beyond price-sheet abstraction
- whether the protagonist reads like a person or only a contract machine

### 9.4 Spine Decision

At the end of the triage, choose exactly one next unit:

- `fresh TR static audit`
- `TR rewrite plan`
- `weakness report only`

Do not choose more than one.

## 10. Fixed Creative Constraints

Do not wash out these anchors:

- US big-tech exile -> Korea return
- `128TB SSD` return image
- ReasonMesh / inference-engine monopoly hook
- hiring refusal -> usage-fee demand
- standards / compliance / audit-log / data-ownership battlefield
- Korea-US AI bottleneck war
- contract language as power, not only code performance

Known weakness to watch:

- near-zero dialogue
- human friction replaced by contract-summary slabs
- repeated `weakness_exploited` phrasing
- protagonist affect flattening into one-note coldness
- “AI domain texture” collapsing into generic price-table repetition

## 11. Deliverable

Save exactly one main report:

- `docs/2026-03-27/us-ai-exile-monopoly-tr-weakness-triage-report.md`

The report should include:

- target pair paths
- duplicate-path truth note
- prior-pass evidence note
- direct repetition ledger
- bounded sceneability findings
- what remains commercially strong
- what fails narratively
- final verdict: `pass`, `mixed`, or `fail`
- next unit only

## 12. Stop Conditions

Stop immediately and report if any of the following occurs:

- canonical pair identity cannot be fixed because duplicate variants conflict materially
- live pair contents cannot be parsed cleanly as UTF-8
- the triage would require broad rewrite to answer a bounded diagnosis question
- confidence falls below 95% for the chosen next unit and no smaller bounded step exists

If the truth is mixed, do not escape into generic optimism.
Record the weakness and choose the smaller next step.

## 13. Expected Next Unit After This Order

- if a usable spine survives and the weakness is bounded: `fresh TR static audit`
- if source TR clearly collapses into repeated contract-summary execution: `TR rewrite plan`
- if the pair is structurally parseable but operationally not worth reviving now: `weakness report only`

## 14. Handoff Format

End with this exact flat report:

```text
work_id: us_ai_exile_monopoly
current_stage: audit_or_repair
finished_unit: source-TR weakness triage
changed_files: ...
next_unit: ...
stop_reason: ...
```

## 15. 3-Pass Self Audit

### Pass 1. Contract Alignment

- target is fixed to one `work_id`
- order stays inside router + blockguide + existing-pair triage boundaries
- no same-work parallel editing is authorized
- no fresh generation stages are mixed in

### Pass 2. Operational Usefulness

- the next unit is singular and concrete: `source-TR weakness triage`
- old metric PASS evidence is retained but not over-trusted
- deliverable and stop conditions are explicit

### Pass 3. Integrity

- saved under dated `docs/2026-03-27/`
- UTF-8 only
- no code-edit instructions
- no multi-unit overreach beyond one bounded diagnosis step

Confidence:
- 97% that `source-TR weakness triage` is the correct next OPUS unit for this pair
