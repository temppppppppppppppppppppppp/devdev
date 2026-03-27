# OPUS Empire Youngest Truth-Reaudit Order

Date: 2026-03-27
Track: narrative pipeline
Status: active
Scope: single-work OPUS order for `empire_youngest_allsector`

## 1. Order Intent

This order fixes the target to `empire_youngest_allsector` and asks OPUS to complete exactly one bounded unit:

- `truth-reconciliation re-audit`

Current lane truth:

- family: `blockguide`
- entry type: existing `TR + BI` pair in `_quarantine`
- the pair is not missing
- the current uncertainty is not pair existence
- the current uncertainty is source authority conflict between older survey text and current live artifacts

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
- do not force runtime probe in this run just to escape ambiguity

## 3. Canonical Target

- work_id: `empire_youngest_allsector`
- TR: `treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json`
- BI: `bible/_quarantine/0_bi_empire_youngest_allsector.json`

Treat these quarantine files as the authoritative pair for this order.

## 4. Live Facts Already Visible

The following live facts are already visible and should be treated as the current default truth unless a direct file read disproves them.

1. TR artifact count:
   - live `TR` currently contains `70` blocks
2. BI roadmap count:
   - live `BI.plot_roadmap` currently contains `70` entries
3. BI structure depth:
   - `NPC_Timeline` count: `10`
   - `HistoricalEvents` count: `13`
   - `OpponentTransitionPlan`: `phase1 / phase2 / phase3`
4. sequential status:
   - `treatments/preprocess/empire_youngest_allsector/sequential_run_status.json`
   - `run_class = sequential_production`
   - `last_sequential_block_pass = 70`
   - `next_unit_type = bi_handoff`
   - `manual_audit_ready = true`
5. Stage 0 gate:
   - `treatments/preprocess/empire_youngest_allsector/phase0_ready_snapshot.json`
   - `manual_audit_pass = true`

## 5. Conflict To Reconcile

One existing survey currently conflicts with the live pair:

- `docs/2026-03-26/blockguide-quarantine-static-quality-survey.md`

That survey says:

- `TR actual 43`
- `TR only 43/70 blocks complete`
- `requires 27 new blocks before pipeline entry`

The current live pair and status files do not match those claims.

Therefore the honest next task is not blind promotion and not blind regeneration.
The honest next task is:

- verify live truth
- downgrade stale authority if needed
- sample whether `70 existing blocks` also means `70 runtime-usable blocks`

## 6. Mandatory Reads

Read these in order:

1. `docs/narrative-router/SSOT_narrative-router-integrated-order.md`
2. `docs/blockguide/SSOT_blockguide-integrated-order.md`
3. `docs/narrative-router/material-revival-ladder-harness.md`
4. `docs/2026-03-26/blockguide-quarantine-static-quality-survey.md`
5. `treatments/preprocess/empire_youngest_allsector/sequential_run_status.json`
6. `treatments/preprocess/empire_youngest_allsector/phase0_ready_snapshot.json`
7. `treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json`
8. `bible/_quarantine/0_bi_empire_youngest_allsector.json`

## 7. Immediate Goal

Execute exactly one bounded `truth-reconciliation re-audit` for `empire_youngest_allsector`.

The re-audit must answer:

- what is the live artifact truth right now
- which older claims are stale or still valid
- whether the pair is merely present or actually usable for runtime progression
- what the smallest honest next unit is

## 8. Re-Audit Method

### 8.1 Artifact Truth Ledger

Verify, at minimum:

- exact TR block count
- exact BI roadmap count
- preprocess gate truth
- sequential status truth
- pair identity coherence under one `work_id`

### 8.2 Authority Reconciliation

Build a small truth table:

- claim
- source
- live evidence
- verdict: `confirmed`, `stale`, or `partially true`

Minimum claims to reconcile:

- `TR actual 43`
- `27 new blocks required`
- `rear half only 1-2 line summaries`

Rule:

- live artifact truth outranks stale survey prose
- but stale survey warnings may still remain useful if the weakness survives bounded sampling

### 8.3 Bounded Static Sampling

Sample the pair without inflating into a full rewrite.

Recommended windows:

- early engine: `Block 1-5`
- suspected compression zone: `Block 32-43`
- late payoff zone: `Block 65-70`

Judge:

- protagonist engine survival
- `3개씩. 쉬지 않고.` doctrine survival
- sector texture versus timing-summary flattening
- repeated `타자 POV` pattern risk
- mid-band compression risk
- whether the late-game payoff still reads like narrative rather than only capital arithmetic

### 8.4 Next-Unit Decision

At the end of the re-audit, choose exactly one next unit:

- `revival-stage probe`
- `fresh TR static audit`
- `weakness report only`

Do not choose more than one.

## 9. Fixed Creative Constraints

Do not wash out these anchors:

- 2045 -> 2025 regression frame
- credit-card `3,000만 원` BTC seed start
- `세 개씩. 쉬지 않고.` execution doctrine
- all-sector rolling structure
- independent-capital rule: no family money
- family-collapse memory: semiconductor delay / sibling conflict / PF crisis
- low-affect protagonist engine with delayed emotional cracks

Known weakness to watch:

- mid-band compression around the `Block 32-43` region
- `타자 POV` patterned repetition
- sector knowledge collapsing into timing summary rather than domain-specific scene pressure

## 10. Deliverable

Save exactly one main report:

- `docs/2026-03-27/empire-youngest-truth-reaudit-report.md`

The report should include:

- target pair paths
- live artifact ledger
- source-authority reconciliation table
- bounded static sampling results
- what remains strong
- what still looks padded, thin, or formulaic
- final verdict: `pass`, `mixed`, or `fail`
- next unit only

## 11. Stop Conditions

Stop immediately and report if any of the following occurs:

- live pair contents cannot be parsed cleanly as UTF-8
- pair identity becomes ambiguous
- count truth cannot be verified from direct file read
- the re-audit would require runtime generation to answer a static-truth question
- confidence falls below 95% for the chosen next unit and no smaller bounded step exists

If the truth is mixed, do not escape into vague optimism.
Record the ambiguity and choose the smaller next step.

## 12. Expected Next Unit After This Order

- if live truth is clean and bounded sampling holds: `revival-stage probe`
- if live truth is clean but structural weakness needs formal documentation: `fresh TR static audit`
- if the pair is present but not honestly probe-ready: `weakness report only`

## 13. Handoff Format

End with this exact flat report:

```text
work_id: empire_youngest_allsector
current_stage: audit_or_repair
finished_unit: truth-reconciliation re-audit
changed_files: ...
next_unit: ...
stop_reason: ...
```

## 14. 3-Pass Self Audit

### Pass 1. Contract Alignment

- target is fixed to one `work_id`
- order stays inside router + blockguide + existing-pair audit boundaries
- no same-work parallel editing is authorized
- no fresh generation stages are mixed in

### Pass 2. Operational Usefulness

- the next unit is singular and concrete: `truth-reconciliation re-audit`
- stale authority conflict is made explicit instead of hidden
- deliverable and stop conditions are explicit

### Pass 3. Integrity

- saved under dated `docs/2026-03-27/`
- UTF-8 only
- no code-edit instructions
- no multi-unit overreach beyond one bounded audit step

Confidence:
- 97% that `truth-reconciliation re-audit` is the correct next OPUS unit for this pair
