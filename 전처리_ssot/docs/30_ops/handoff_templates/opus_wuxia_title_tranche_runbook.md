# Opus Wuxia Title-Tranche Runbook

Date: 2026-03-20
Status: final
Scope: first Opus execution runbook for the decomposition base
Authority: canonical under `전처리_ssot/docs/30_ops/handoff_templates`
Confidence Target: 95%
Current Confidence: 95% for first-run operator handoff

## 1. Intent

- Tell Opus exactly what to do for the first wuxia pilot tranche.
- Prevent over-scoped runs, self-approval, and context bleed.
- Make the first execution reproducible even if a different operator runs it later.

## 2. Core Rule

Do not tell Opus:

- "build the wuxia pack"
- "decompose all three titles"
- "read everything and summarize"

Tell Opus only one unit at a time:

1. segmentation shard
2. segmentation shard
3. title-tranche merge
4. independent audit

Every step after step 1 should start in a fresh context.

## 3. Required Files to Read First

Opus must read these files in UTF-8 before writing anything:

1. `C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\30_ops\genre_decomposition_base_roadmap.md`
2. `C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\30_ops\genre_pack_registry.md`
3. `C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\30_ops\tranche_manifests\tranche_manifest__wuxia__t1__2026-03-20.json`

The audit run must also read:

4. `C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\30_ops\audit_checklists\audit_checklist__genre_decomposition_title_tranche__v1.md`

## 4. First Target

Use only this first target:

- `title_id`: `wuxia__title__gonryun_mahyeop`
- `title_slug`: `gonryun_mahyeop`
- title: `곤륜마협`
- source root: `C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\원고\무협_곤륜마협`

Do not touch title two until the title-one tranche survives `pass1`, `pass2`, `pass3`, and adversarial review.

## 5. Output Roots

Write title-local outputs only under these paths:

- `C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\20_db_and_materials\materials\genre_notes\wuxia\by_title\gonryun_mahyeop`
- `C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\20_db_and_materials\materials\scene_bank\wuxia\by_title\gonryun_mahyeop\scene_cards`
- `C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\20_db_and_materials\materials\scene_bank\wuxia\by_title\gonryun_mahyeop\block_cards`
- `C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\20_db_and_materials\materials\scene_bank\wuxia\by_title\gonryun_mahyeop\hook_payoff`
- `C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\20_db_and_materials\materials\scene_bank\wuxia\by_title\gonryun_mahyeop\voice`

Audit outputs belong under:

- `C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\30_ops\phase0_ready_reviews`

## 6. Exact Execution Order

### 6.1 Run A: Segmentation Shard 1

Scope:

- `곤륜마협` `ep001-010`

Expected outputs:

- episode segmentation note
- scene boundary sheet
- arc candidate map
- shard summary sheet

Do not ask for:

- genre-level taxonomy
- canonical promotion
- title two comparison

### 6.2 Run B: Segmentation Shard 2

Scope:

- `곤륜마협` `ep011-020`

Expected outputs:

- episode segmentation note
- scene boundary sheet
- arc candidate map
- shard summary sheet

Run in fresh context. It may read Run A outputs, but it must not inherit hidden chain-of-thought or self-approval.

### 6.3 Run C: Title-Tranche Merge

Scope:

- merge `ep001-010` and `ep011-020`
- produce title-tranche bundle for `곤륜마협 ep001-020`

Expected outputs:

- `title_registry__wuxia__gonryun_mahyeop.md`
- `arc_cadence__wuxia__gonryun_mahyeop__ep001-020.json`
- `scene_cards__wuxia__gonryun_mahyeop__ep001-020.json`
- `block_cards__wuxia__gonryun_mahyeop__ep001-020.json`
- `hook_payoff__wuxia__gonryun_mahyeop__ep001-020.md`
- one or more `voice_card__...`
- `anti_pattern_notes__wuxia__gonryun_mahyeop__ep001-020.md`
- `status_matrix__wuxia__gonryun_mahyeop__ep001-020.md`
- `handoff_note__wuxia__gonryun_mahyeop__ep001-020.md`

Status cap:

- everything remains `candidate`

### 6.4 Run D: Independent Audit

Scope:

- audit only the title-tranche bundle from Run C

Expected outputs:

- `audit_checklist__gonryun_mahyeop_ep001-020__v1.md`
- `findings__gonryun_mahyeop_ep001-020__v1.md`
- `pass_fail_decision__gonryun_mahyeop_ep001-020__v1.md`
- `required_remediation__gonryun_mahyeop_ep001-020__v1.md`
- `status_transition__gonryun_mahyeop_ep001-020__v1.md`

Hard rule:

- this run must use fresh context
- this run must not be framed as "please validate your own previous output"

## 7. Copy-Paste Prompt: Run A

```text
You are the operator for one bounded preprocessing unit only.

Read these files in UTF-8 first:
1. C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\30_ops\genre_decomposition_base_roadmap.md
2. C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\30_ops\genre_pack_registry.md
3. C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\30_ops\tranche_manifests\tranche_manifest__wuxia__t1__2026-03-20.json

Then perform only this unit:
- genre_family: wuxia
- title_id: wuxia__title__gonryun_mahyeop
- title: 곤륜마협
- episode shard: ep001-010
- task type: first-pass structural segmentation only

Source root:
C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\원고\무협_곤륜마협

Write outputs only under:
- C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\20_db_and_materials\materials\genre_notes\wuxia\by_title\gonryun_mahyeop
- C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\20_db_and_materials\materials\scene_bank\wuxia\by_title\gonryun_mahyeop\scene_cards

Required outputs for this run:
1. episode segmentation note
2. scene boundary sheet
3. arc candidate map
4. shard summary sheet

Execution rules:
- Do not produce genre-level conclusions.
- Do not compare title two or title three.
- Do not promote anything above candidate.
- Do not skip evidence anchors.
- Segment and summarize only what happens in order.
- Mark open boundary issues explicitly.

Stop after this shard is complete and report:
- files written
- unresolved boundary questions
- whether the shard is ready for tranche merge
```

## 8. Copy-Paste Prompt: Run C

Use this only after Run A and Run B both exist.

```text
You are the operator for one bounded preprocessing unit only.

Read these files in UTF-8 first:
1. C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\30_ops\genre_decomposition_base_roadmap.md
2. C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\30_ops\genre_pack_registry.md
3. C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\30_ops\tranche_manifests\tranche_manifest__wuxia__t1__2026-03-20.json

Then read the existing shard outputs for:
- wuxia__title__gonryun_mahyeop
- ep001-010
- ep011-020

Perform only this unit:
- task type: title-tranche merge
- scope: 곤륜마협 ep001-020

Write outputs only under:
- C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\20_db_and_materials\materials\genre_notes\wuxia\by_title\gonryun_mahyeop
- C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\20_db_and_materials\materials\scene_bank\wuxia\by_title\gonryun_mahyeop\scene_cards
- C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\20_db_and_materials\materials\scene_bank\wuxia\by_title\gonryun_mahyeop\block_cards
- C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\20_db_and_materials\materials\scene_bank\wuxia\by_title\gonryun_mahyeop\hook_payoff
- C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\20_db_and_materials\materials\scene_bank\wuxia\by_title\gonryun_mahyeop\voice

Required outputs:
1. title_registry__wuxia__gonryun_mahyeop.md
2. arc_cadence__wuxia__gonryun_mahyeop__ep001-020.json
3. scene_cards__wuxia__gonryun_mahyeop__ep001-020.json
4. block_cards__wuxia__gonryun_mahyeop__ep001-020.json
5. hook_payoff__wuxia__gonryun_mahyeop__ep001-020.md
6. voice card file(s) if materially distinct
7. anti_pattern_notes__wuxia__gonryun_mahyeop__ep001-020.md
8. status_matrix__wuxia__gonryun_mahyeop__ep001-020.md
9. handoff_note__wuxia__gonryun_mahyeop__ep001-020.md

Execution rules:
- Everything must remain candidate.
- Every reusable claim needs evidence anchors.
- Labels must be functional, not source-surface labels.
- Separate transferable core from non-transferable residue.
- Do not produce canonical or genre-pack conclusions.

Stop after the title-tranche bundle is complete and report:
- files written
- highest-risk overfit points
- what the independent audit should attack first
```

## 9. Copy-Paste Prompt: Run D

```text
You are the independent reviewer for one bounded preprocessing audit unit only.

Read these files in UTF-8 first:
1. C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\30_ops\genre_decomposition_base_roadmap.md
2. C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\30_ops\tranche_manifests\tranche_manifest__wuxia__t1__2026-03-20.json
3. C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\30_ops\audit_checklists\audit_checklist__genre_decomposition_title_tranche__v1.md

Then read the completed title-tranche bundle for:
- wuxia__title__gonryun_mahyeop
- ep001-020

Perform only this unit:
- task type: independent audit
- scope: 곤륜마협 ep001-020 title-tranche bundle

Write outputs only under:
- C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\30_ops\phase0_ready_reviews

Required outputs:
1. audit_checklist__gonryun_mahyeop_ep001-020__v1.md
2. findings__gonryun_mahyeop_ep001-020__v1.md
3. pass_fail_decision__gonryun_mahyeop_ep001-020__v1.md
4. required_remediation__gonryun_mahyeop_ep001-020__v1.md
5. status_transition__gonryun_mahyeop_ep001-020__v1.md

Audit rules:
- This is not an author continuation. Review from fresh context.
- Primary focus is bugs, overfit risk, evidence weakness, status misuse, and transfer failure.
- Do not rewrite the tranche. Audit it.
- Force one decision: pass, fail, or return_for_remediation.

Stop after the audit bundle is complete and report:
- pass/fail decision
- top 5 findings by severity
- whether title two may start
```

## 10. Short Practical Rule

If you are using Opus in chat rather than inside the workspace:

- attach the roadmap
- attach the tranche manifest
- attach only the target episode files for the current shard
- paste the matching prompt from this runbook

Do not attach all 100 episodes or the whole corpus.

## 11. 3-Pass Record

### Pass 1 Result

- Locked the first execution target to `곤륜마협` only.
- Broke execution into bounded runs rather than one giant ask.

### Pass 2 Result

- Added exact file paths, output roots, and required artifacts.
- Added separate prompts for shard, merge, and audit.

### Pass 3 Result

- Added fresh-context rules and explicit stop conditions.
- Added a chat-mode fallback rule for cases where Opus does not share workspace access.

## 12. Adversarial Review Record

Primary attacks considered:

- Opus being asked to decompose the whole lane at once
- merge and audit happening in the same conversational context
- audit silently turning into author continuation

Mitigations added:

- one-unit-only rule
- fresh-context requirement
- explicit output bundles and stop conditions
