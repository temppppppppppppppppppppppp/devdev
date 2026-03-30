# Protagonist-First TR-BI Pair Survey 4-Terminal Master Order

Date: 2026-03-30
Status: final (3-pass audited)
Document Type: survey master order
Canonical Path: `docs/2026-03-30/protagonist-first-tr-bi-pair-survey-4terminal-master-order.md`
Track: narrative pipeline
Scope: live `treatments/` + `bible/` pair survey only
Mode: parallel compact pair audit

## 1. Intent

This order surveys one bounded question only:

- do the current live `TR + BI` pairs in `treatments/` and `bible/` actually preserve our `주인공 둥기둥기 first` philosophy?

This is not:

- a code audit
- a member/runtime authority audit
- a patch order
- an execution SSOT
- a pair promotion order

This is a pair-truth survey.
The primary evidence is the live JSON artifact body itself.

## 2. Target Inventory

Survey these live pairs only.

| Work | Family | TR Path | BI Path | Lane |
| --- | --- | --- | --- | --- |
| `chaebol_ent_empire` | `blockguide` | `treatments/chaebol_ent_empire_tr_block_070_draft.json` | `bible/0_bi_chaebol_ent_empire.json` | T1 |
| `투자물_골든_카나리아 테스트` | `blockguide` | `treatments/01_tr_투자물_골든_카나리아 테스트.json` | `bible/01_bi_투자물_골든_카나리아 테스트.json` | T1 |
| `pantech_cyworld_reborn` | `blockguide` | `treatments/pantech_cyworld_reborn_tr_block_070_draft.json` | `bible/0_bi_pantech_cyworld_reborn.json` | T2 |
| `wuxia_heavenly_physician` | `wuxguide` | `treatments/wuxia_heavenly_physician_tr_block_070_draft.json` | `bible/0_bi_wuxia_heavenly_physician.json` | T3 |
| `wuxia_third_rate_sect_master` | `wuxguide` | `treatments/_quarantine/wuxia_third_rate_sect_master_tr_block_070_draft.json` | `bible/_quarantine/0_bi_wuxia_third_rate_sect_master.json` | T4 |

Reason for `T1 = 2 works`:

- `chaebol_ent_empire` and `골든 카나리아` are the best intra-family calibration pair for the same philosophy lens
- `pantech` and `wuxia_third_rate_sect_master` are each too large to share a lane comfortably

## 3. Common Rules For All 4 Lanes

- survey only
- code changes forbidden
- artifact regeneration forbidden
- `docs/temp/`, queue docs, execution SSOT, roadmap creation forbidden
- pair promotion / quarantine mutation forbidden
- do not overwrite another lane's report
- use live artifact body as primary evidence
- audit reports are secondary context only
- if old audit text conflicts with live JSON body, live JSON body wins
- findings first
- file/line anchors when citing docs or code
- JSON evidence may cite block numbers / section keys instead of line anchors when more practical

Mandatory negative rules:

- do not judge from filename reputation
- do not trust stale pass/fail labels
- do not stop at BI metadata only; inspect TR body too
- do not stop at TR body only; inspect BI protagonist encoding too
- do not confuse `pure punishment tension` with `good hardship`
- do not mark family-specific semantics as drift if they still preserve protagonist-first reward logic

## 4. Philosophy Rubric

All lanes must use this exact bounded rubric.
Do not invent a different philosophy frame.

### R1. Protagonist Reward Visibility

- after a meaningful protagonist success, does the story give visible recognition / reward / leverage?
- if success is followed only by suspicion, punishment, or silence, mark drift

### R2. Reward Dwell Time

- after a win, does the pair allow at least some short-lived enjoyment / leverage / utilization?
- if reward is instantly stripped or nullified, mark drift

### R3. Pain Aesthetic

- when the protagonist suffers, is the suffering still aspirational / cool / growth-bearing?
- if the protagonist is merely humiliated, helpless, or bleak without payoff, mark drift

### R4. Vector Direction

- if the surface looks punitive, is the deeper vector still protective / strategic / reversal-ready?
- if the dominant reader emotion is only frustration or unfairness, mark drift

### R5. Exclusive Protagonist Engine

- does the pair preserve a protagonist-only advantage, information gap, or unique conversion engine?
- if anyone could replace the protagonist without collapsing the story engine, mark drift

### R6. Genre Contract Stability

- does the pair keep the promised family contract and tone?
- if the pair betrays its own no-romance / growth / business-power / wuxia promise in a way that weakens protagonist-first reading, mark drift

### R7. BI Amplification

- does the BI materially reinforce the protagonist-first engine found in the TR?
- if BI only mirrors block summaries and fails to encode reward logic / protagonist edge / current leverage, mark drift

## 5. Required Survey Method

Do not brute-force summarize every block.
Use bounded windows first, then expand only if needed.

Minimum TR windows per work:

- blocks `1-10`
- one middle stress window chosen by the lane reviewer
- blocks `61-70`

Minimum BI sections per work:

- `ProjectData.CoreIdentity`
- protagonist HUD / actual truth
- public reputation or equivalent outward image field
- `GenreRules`
- `plot_roadmap` sample windows aligned to the TR windows

Expansion rule:

- if a serious protagonist-first drift appears in the bounded windows, expand only around the proving blocks
- do not escalate to a full 70-block summary unless the verdict truly cannot be proven otherwise

## 6. Common OPUS Survey Prompt

```text
Narrative-pipeline survey order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/narrative-router/SSOT_narrative-router-integrated-order.md
3. docs/narrative-router/what-how-craft-harness.md
4. docs/narrative-router/material-revival-ladder-harness.md
5. docs/2026-03-30/protagonist-first-tr-bi-pair-survey-4terminal-master-order.md
6. your lane's family integrated order and planning/production/BI harnesses

Task:
Survey your assigned live TR-BI pair lane only.
Judge whether the pair preserves `주인공 둥기둥기 first`.

Hard constraints:
- survey only
- no code changes
- no artifact rewrites
- no docs/temp edits
- no queue or roadmap edits
- no shared report overwrite
- use live JSON body as primary evidence
- findings first
- keep scope to your lane only

You must classify each pair in your lane as:
- green
- yellow
- red

You must separately score:
- TR protagonist-first verdict
- BI protagonist-first verdict
- pair-level combined verdict

Mandatory output fields for every pair:
- work_id
- family
- TR verdict
- BI verdict
- pair verdict
- strongest confirming evidence
- strongest violating evidence
- whether this pair can serve as a protagonist-first reference pair: yes / no
```

## 7. Lane Map

All lane reports should be saved under:

- `docs/2026-03-30/opus-protagonist-first-pair-survey/`

### T1. Blockguide Calibration Lane

Save to:

- `docs/2026-03-30/opus-protagonist-first-pair-survey/t1-blockguide-calibration-lane.md`

Assigned works:

- `chaebol_ent_empire`
- `투자물_골든_카나리아 테스트`

Read in addition to the common read order:

- `docs/blockguide/SSOT_blockguide-integrated-order.md`
- `docs/blockguide/treatment-planning-harness.md`
- `docs/blockguide/treatment-production-harness-v2.md`
- `docs/blockguide/bi-production-harness-v1.md`

Primary artifact paths:

- `treatments/chaebol_ent_empire_tr_block_070_draft.json`
- `bible/0_bi_chaebol_ent_empire.json`
- `treatments/01_tr_투자물_골든_카나리아 테스트.json`
- `bible/01_bi_투자물_골든_카나리아 테스트.json`

Focus questions:

- do both blockguide pairs reward protagonist wins quickly enough?
- which pair better preserves `reward dwell` rather than `win -> immediate new punishment`?
- is `골든 카나리아` actually a stronger protagonist-first reference, or merely denser?
- does either BI encode protagonist leverage better than the TR body deserves?

Extra rule:

- do not average the two works into one verdict
- verdict each work separately, then add a short comparison note

### T2. Pantech Cyworld Heavy Lane

Save to:

- `docs/2026-03-30/opus-protagonist-first-pair-survey/t2-pantech-cyworld-heavy-lane.md`

Assigned work:

- `pantech_cyworld_reborn`

Read in addition to the common read order:

- `docs/blockguide/SSOT_blockguide-integrated-order.md`
- `docs/blockguide/treatment-planning-harness.md`
- `docs/blockguide/treatment-production-harness-v2.md`
- `docs/blockguide/bi-production-harness-v1.md`

Primary artifact paths:

- `treatments/pantech_cyworld_reborn_tr_block_070_draft.json`
- `bible/0_bi_pantech_cyworld_reborn.json`

Secondary context only:

- `treatments/preprocess/pantech_cyworld_reborn/source_manifest.json`
- `treatments/preprocess/pantech_cyworld_reborn/profile_lock.json`
- `treatments/preprocess/pantech_cyworld_reborn/material_bundle_summary.json`
- `treatments/preprocess/pantech_cyworld_reborn/phase0_ready_snapshot.json`

Focus questions:

- does this pair make the protagonist feel admired for judgment and leverage, not just nostalgia or corporate scale?
- when setbacks hit, do they still carry positive vector / reversal potential?
- does the BI keep the protagonist-first engine legible, or drown it in world/business data?

### T3. Wuxia Heavenly Physician Live Lane

Save to:

- `docs/2026-03-30/opus-protagonist-first-pair-survey/t3-wuxia-heavenly-physician-live-lane.md`

Assigned work:

- `wuxia_heavenly_physician`

Read in addition to the common read order:

- `docs/wuxguide/SSOT_wuxguide-integrated-order.md`
- `docs/wuxguide/wuxia-planning-harness.md`
- `docs/wuxguide/wuxia-production-harness.md`
- `docs/wuxguide/wuxia-bi-production-harness.md`

Primary artifact paths:

- `treatments/wuxia_heavenly_physician_tr_block_070_draft.json`
- `bible/0_bi_wuxia_heavenly_physician.json`

Secondary context only:

- `bible/audit_reports/wuxia_heavenly_physician_wuxia_bi_5pass.md`
- `treatments/preprocess/wuxia_heavenly_physician/source_manifest.json`
- `treatments/preprocess/wuxia_heavenly_physician/profile_lock.json`

Focus questions:

- does the pair preserve a wuxia-appropriate version of protagonist reward, not just block survival?
- is medical/martial pain still stylized as aspirational rather than degrading?
- does the BI preserve the protagonist's unique information or healing/martial engine clearly enough?

### T4. Wuxia Third-Rate Sect Master Quarantine Stress-Test Lane

Save to:

- `docs/2026-03-30/opus-protagonist-first-pair-survey/t4-wuxia-third-rate-quarantine-lane.md`

Assigned work:

- `wuxia_third_rate_sect_master`

Read in addition to the common read order:

- `docs/wuxguide/SSOT_wuxguide-integrated-order.md`
- `docs/wuxguide/wuxia-planning-harness.md`
- `docs/wuxguide/wuxia-production-harness.md`
- `docs/wuxguide/wuxia-bi-production-harness.md`

Primary artifact paths:

- `treatments/_quarantine/wuxia_third_rate_sect_master_tr_block_070_draft.json`
- `bible/_quarantine/0_bi_wuxia_third_rate_sect_master.json`

Secondary context only:

- `treatments/preprocess/wuxia_third_rate_sect_master/source_manifest.json`
- `treatments/preprocess/wuxia_third_rate_sect_master/profile_lock.json`
- `treatments/preprocess/wuxia_third_rate_sect_master/material_bundle_summary.json`
- `treatments/preprocess/wuxia_third_rate_sect_master/phase0_ready_snapshot.json`

Focus questions:

- does the quarantine-level TR still preserve protagonist-first value, or is it mostly pressure / repetition / punishment drift?
- is the quarantine BI more optimistic than the underlying TR deserves?
- does this pair act as a useful failure detector for protagonist-first drift in wuxguide?

Special rule:

- treat quarantine placement as provenance context, not as an automatic invalidation
- if the pair identity itself looks unsound, report that as a `pair provenance risk`, not as a made-up content verdict

## 8. Required Output Shape

Every lane report must end with this flat section:

```text
lane: ...
work_id: ...
family: ...
TR verdict: green / yellow / red
BI verdict: green / yellow / red
pair verdict: green / yellow / red
strongest confirming evidence: ...
strongest violating evidence: ...
reference pair candidate: yes / no
```

If a lane has two works, repeat the block twice.

## 9. Desired Merge Outcome

After all 4 lanes return, Codex will merge for:

- which pairs truly preserve protagonist-first
- which pairs fake protagonist-first through density or metadata only
- which family better preserves the philosophy in live artifacts
- whether any current pair can be treated as a live reference baseline

The merge target is not:

- “which work is more fun”

The merge target is:

- “which live pairs actually preserve reward-first protagonist philosophy in TR and BI together”

## 10. Dispatch Lines

Use exactly one of the following:

- `docs/2026-03-30/protagonist-first-tr-bi-pair-survey-4terminal-master-order.md + 넌 1번 터미널`
- `docs/2026-03-30/protagonist-first-tr-bi-pair-survey-4terminal-master-order.md + 넌 2번 터미널`
- `docs/2026-03-30/protagonist-first-tr-bi-pair-survey-4terminal-master-order.md + 넌 3번 터미널`
- `docs/2026-03-30/protagonist-first-tr-bi-pair-survey-4terminal-master-order.md + 넌 4번 터미널`

## 11. 3-Pass Self Audit

### Pass 1. Scope Audit

- the order is bounded to live `TR + BI` artifact survey only
- the order does not drift into runtime/code/member audit
- the order keeps the user's target question central: `주인공 둥기둥기 first` alignment

### Pass 2. Operational Audit

- all five target pairs are assigned
- the four-terminal split is practical
- the heaviest single works are isolated
- the calibration pair is intentionally grouped only once

### Pass 3. Integrity Audit

- saved under dated `docs/2026-03-30/`
- UTF-8 only
- no queue/temp mutation instructions
- no patch or artifact rewrite instructions
