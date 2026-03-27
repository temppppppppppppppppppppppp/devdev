# OPUS Pantech Revival-Stage Probe Order

Date: 2026-03-27
Track: narrative pipeline
Status: active
Scope: single-work OPUS order for `pantech_cyworld_reborn`

## 1. Order Intent

This order fixes the target to `pantech_cyworld_reborn` and asks OPUS to advance exactly one remaining revival-ladder unit.

Current lane truth:
- family: `blockguide`
- entry type: existing `TR + BI` pair revival
- current pair location: `_quarantine`
- smallest remaining unproven step: `revival-stage probe`

This is not a fresh Planning or fresh TR/BI generation order.

## 2. Non-Negotiable Rules

- UTF-8 only
- read router -> family SSOT -> revival ladder before doing anything else
- one work, one owner, one unit
- no same-work concurrent editing
- no code or system edits
- do not regenerate TR
- do not redesign BI from scratch unless a concrete contract blocker invalidates the existing repaired BI
- do not promote to active path in the same run
- do not run Stage 4 in the same run

## 3. Canonical Target

- work_id: `pantech_cyworld_reborn`
- TR: `treatments/_quarantine/07_pantech_cyworld_reborn_tr_block_070_draft.json`
- BI: `bible/_quarantine/07_pantech_cyworld_reborn_bi.json`

Treat these quarantine files as the authoritative pair for this order.

## 4. Proven Prior Steps

The following steps are already evidenced and should not be re-litigated unless the live files contradict them.

1. Pair consumability survey:
   - `docs/2026-03-26/pantech-cyworld-bi-tr-consumability-survey.md`
2. Pair consumability repair:
   - `docs/2026-03-26/pantech-cyworld-bi-tr-consumability-repair-report.md`
3. TR static audit:
   - `docs/2026-03-27/pantech-cyworld-tr-static-quality-audit.md`
   - verdict: `usable spine but mixed`
4. BI repair:
   - `docs/2026-03-27/pantech-cyworld-bi-repair-note.md`
   - verdict: `pass`
5. Revival canary:
   - `docs/2026-03-27/pantech-cyworld-revival-canary-report.md`
   - verdict: `pass`

Interpretation:
- TR is good enough to probe
- BI repair is already done
- runtime contract blockers are currently cleared

## 5. Preprocess Gate Truth

The work already has Stage 0 artifacts and locked manual audit.

Required truth:
- `treatments/preprocess/pantech_cyworld_reborn/source_manifest.json`
- `treatments/preprocess/pantech_cyworld_reborn/profile_lock.json`
- `treatments/preprocess/pantech_cyworld_reborn/material_bundle_summary.json`
- `treatments/preprocess/pantech_cyworld_reborn/phase0_ready_snapshot.json`

Expected gate:
- `manual_audit_pass == true`

Do not spend this run rebuilding preprocess artifacts unless the live files contradict the saved gate.

## 6. Mandatory Reads

Read these in order:

1. `docs/narrative-router/SSOT_narrative-router-integrated-order.md`
2. `docs/blockguide/SSOT_blockguide-integrated-order.md`
3. `docs/narrative-router/material-revival-ladder-harness.md`
4. `docs/2026-03-26/pantech-cyworld-bi-tr-consumability-repair-report.md`
5. `docs/2026-03-27/pantech-cyworld-tr-static-quality-audit.md`
6. `docs/2026-03-27/pantech-cyworld-bi-repair-note.md`
7. `docs/2026-03-27/pantech-cyworld-revival-canary-report.md`

## 7. Immediate Goal

Execute exactly one bounded `revival-stage probe` for `pantech_cyworld_reborn`.

The probe must answer:
- does the repaired quarantine pair admit cleanly into the current runtime?
- does Stage 2 keep the tech/startup + chaebol business texture alive?
- does Stage 3 produce sceneable blueprint output instead of flattening into abstract summary?

## 8. Probe Method

### 8.1 Runtime Admission

Verify, at minimum:
- pair loads without contract failure
- `plot_roadmap` is recognized as ready
- protagonist-facing runtime keys are present enough for current handoff
- no new schema drift appears

### 8.2 Stage 2 Bounded Probe

Run a bounded Stage 2 test on the early high-signal window only.

Preferred window:
- Arc 1 / Block 1-10 range

What to judge:
- telecom / certification / QA / app / first-screen / payment chokepoints still read as the real battlefield
- regression protagonist engine still reads clearly
- the result is an arc document with actual scene pressure, not only deal summary

### 8.3 Stage 3 Bounded Probe

Generate one Episode 1 blueprint from the Stage 2 result.

What to judge:
- blueprint has scene structure
- character voices separate cleanly
- spatial and sensory cues exist
- the work still feels like Korean 2006 mobile-platform warfare plus chaebol succession pressure, not generic civic infrastructure abstraction

## 9. Fixed Creative Constraints

Do not wash out these anchors:

- 2006~2007 Korean IT transition timing
- Pantech + Cyworld dual-revival engine
- telecom certification / QA / first-screen / payment chokepoints
- regression slip-up pressure
- chaebol succession pressure
- capital-structure and audit pressure running in parallel

Known weakness to watch:
- back-half thematic drift toward public infrastructure expansion

Probe rule:
- if the generated output already drifts too early into generic smart-city abstraction, call that out explicitly
- do not try to repair the drift in the same run

## 10. Deliverable

Save exactly one main report:

- `docs/2026-03-27/pantech-cyworld-revival-stage-probe-report.md`

The report should include:
- target pair paths
- runtime admission result
- Stage 2 bounded result
- Stage 3 bounded result
- what survived runtime translation
- what weakened or flattened
- final verdict: `pass`, `mixed`, or `fail`
- next unit only

## 11. Stop Conditions

Stop immediately and report if any of the following occurs:

- live pair contents contradict the cited canary/repair artifacts
- pair identity becomes ambiguous
- a contract blocker appears that cannot be cleared without opening another ladder step
- the probe would require promotion or Stage 4 to answer the current question
- confidence falls below 95% and no smaller bounded next step exists

If a trivial contract blocker appears that should have been handled by a promotion patch, do not improvise a broad rewrite.
Record the blocker and stop with a smaller next-unit recommendation.

## 12. Expected Next Unit After This Order

- if probe passes: `active promotion`
- if probe is mixed because of trivial contract blockers: `promotion patch`
- if probe fails because runtime translation collapses: `TR/BI weakness report only`, then stop

## 13. Handoff Format

End with this exact flat report:

```text
work_id: pantech_cyworld_reborn
current_stage: audit_or_repair
finished_unit: revival-stage probe
changed_files: ...
next_unit: ...
stop_reason: ...
```

## 14. 3-Pass Self Audit

### Pass 1. Contract Alignment

- target is fixed to one `work_id`
- order stays inside router + blockguide + revival-ladder boundaries
- no same-work parallel editing is authorized
- no fresh generation stages are skipped into

### Pass 2. Operational Usefulness

- the next unit is singular and concrete: `revival-stage probe`
- prior proven steps are enumerated so OPUS does not restart the ladder from zero
- deliverable and stop conditions are explicit

### Pass 3. Integrity

- saved under dated `docs/2026-03-27/`
- UTF-8 only
- no code-edit instructions
- no multi-unit overreach beyond one bounded revival step

Confidence:
- 96% that `revival-stage probe` is the correct next OPUS unit for this pair
