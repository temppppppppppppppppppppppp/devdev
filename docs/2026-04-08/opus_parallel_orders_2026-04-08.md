# Opus Parallel Orders 2026-04-08

Date: 2026-04-08
Status: operator-ready
Scope: short copy-pasteable Opus orders under the new delegation bootstrap system

## 1. Master Order

Use one section below per Opus thread.

Common hard laws:

- read `material_ssot/00_governance/delegation-envelope-spec-v1.md` first
- if a work-level current-truth doc exists, read it before any older handoff
- edit only the files explicitly named in your section
- do not edit shared governance or family SSOT docs
- do not widen your task into a later stage
- stop after the named validation and report exact changed files

## 2. Work 01 — `quiet_chaebol_heir`

```text
Task: one-work-only `canon_tighten` for `quiet_chaebol_heir`.

Read in this order:
1. material_ssot/00_governance/delegation-envelope-spec-v1.md
2. docs/2026-04-08/quiet_chaebol_heir_live_status.md
3. material_ssot/20_pitch/README.md
4. material_ssot/20_pitch/material-benchmark-readiness-harness-v1.md
5. material_ssot/20_pitch/intake/fresh_20260408_batch01/01_quiet_chaebol_heir.md

Write scope:
- material_ssot/20_pitch/intake/fresh_20260408_batch01/01_quiet_chaebol_heir.md only

Task goal:
- tighten the current selection-ready candidate so the Phase0 handoff is sharper and the sibling/competition ladder reads cleanly
- do not create preprocess, Phase0, TR, BI, or work_guard artifacts

Hard stops:
- no downstream file creation
- no canon promotion side effects in shared README files

Validation:
- python -X utf8 scripts/material_readiness_validator.py --path material_ssot/20_pitch/intake/fresh_20260408_batch01/01_quiet_chaebol_heir.md

Final report:
- changed files
- 3 bullet summary of what became clearer
```

## 3. Work 02 — `hoegui_surgeon`

```text
Task: one-work-only `root_admit` for `hoegui_surgeon`.

Read in this order:
1. material_ssot/00_governance/delegation-envelope-spec-v1.md
2. docs/2026-04-08/hoegui_surgeon_live_status.md
3. docs/blockguide/delegation-bootstrap.md
4. material_ssot/20_pitch/canon/hoegui_surgeon.md
5. docs/2026-04-06/02_hoegui_surgeon_context_handoff.md
6. treatments/preprocess/hoegui_surgeon/02_phase0_work/phase0_fixed.json
7. work_guards/12_hoegui_surgeon.yaml
8. treatments/preprocess/hoegui_surgeon/03_tr_blocks/tr_block_001_010.json
9. treatments/preprocess/hoegui_surgeon/03_tr_blocks/tr_block_011_015.json
10. treatments/preprocess/hoegui_surgeon/03_tr_blocks/tr_block_016_020.json

Write scope:
- treatments/phase0/hoegui_surgeon_phase0_design.json
- treatments/hoegui_surgeon_tr_block_020_draft.json
- docs/2026-04-08/hoegui_surgeon_live_status.md

Task goal:
- admit the already-saved legacy Phase0 and Blocks 1-20 into current-root live paths
- preserve story content; this is normalization, not continuation

Hard stops:
- do not write Block 21+
- do not create BI
- do not edit shared harness/governance docs

Validation:
- python -c "import json, pathlib; json.load(open(r'C:\\Users\\wjjo\\Desktop\\글도비\\treatments\\phase0\\hoegui_surgeon_phase0_design.json', encoding='utf-8')); json.load(open(r'C:\\Users\\wjjo\\Desktop\\글도비\\treatments\\hoegui_surgeon_tr_block_020_draft.json', encoding='utf-8')); print('ok')"

Final report:
- changed files
- admitted saved boundary
- anything ambiguous that still blocks Block 21 continuation
```

## 4. Work 03 — `jangyeongshil_industrial_revolution`

```text
Task: one-work-only `tr_continue` for `jangyeongshil_industrial_revolution`.

Read in this order:
1. material_ssot/00_governance/delegation-envelope-spec-v1.md
2. docs/2026-04-08/jangyeongshil_industrial_revolution_live_status.md
3. docs/blockguide/delegation-bootstrap.md
4. docs/blockguide/treatment-production-harness-v2.md
5. material_ssot/20_pitch/canon/jangyeongshil_industrial_revolution.md
6. treatments/phase0/jangyeongshil_industrial_revolution_phase0_design.json
7. treatments/jangyeongshil_industrial_revolution_tr_block_025_draft.json
8. docs/2026-04-06/jangyeongshil_industrial_revolution_production_status.md

Write scope:
- treatments/jangyeongshil_industrial_revolution_tr_block_025_draft.json only

Task goal:
- continue the live TR from Block 26 through Block 30 in the same file

Hard stops:
- no BI refresh
- no work_guard publish inference
- keep the saved boundary and metadata consistent

Validation:
- python -c "import json; json.load(open(r'C:\\Users\\wjjo\\Desktop\\글도비\\treatments\\jangyeongshil_industrial_revolution_tr_block_025_draft.json', encoding='utf-8')); print('ok')"

Final report:
- changed files
- new saved boundary
- any newly opened foreshadows/callback obligations
```

## 5. Work 04 — `manual_meridian_archivist`

```text
Task: one-work-only `tr_merge_rebuild` for `manual_meridian_archivist`.

Read in this order:
1. material_ssot/00_governance/delegation-envelope-spec-v1.md
2. docs/2026-04-08/manual_meridian_archivist_live_status.md
3. docs/wuxguide/delegation-bootstrap.md
4. docs/wuxguide/wuxia-production-harness.md
5. material_ssot/20_pitch/canon/manual_meridian_archivist.md
6. treatments/phase0/manual_meridian_archivist_phase0_design.json
7. work_guards/11_manual_meridian_archivist.yaml
8. treatments/manual_meridian_archivist_tr_block_070_draft.json
9. docs/2026-04-06/manual_meridian_archivist_context_handoff_b22.md
10. docs/2026-04-06/manual_meridian_archivist_context_handoff_b26.md

Write scope:
- treatments/manual_meridian_archivist_tr_block_070_draft.json
- docs/2026-04-08/manual_meridian_archivist_live_status.md only if the saved boundary truly advances

Task goal:
- reconstruct or merge Block 22-25 into the same live TR file
- stop after Block 25 is serialized

Hard stops:
- do not continue into Block 26+
- do not rename the file
- do not treat filename `070` as proof that Block 22+ is already saved

Validation:
- python -c "import json; json.load(open(r'C:\\Users\\wjjo\\Desktop\\글도비\\treatments\\manual_meridian_archivist_tr_block_070_draft.json', encoding='utf-8')); print('ok')"

Final report:
- changed files
- saved boundary before/after
- which handoff points were actually serialized
```

## 6. Work 05 — `jaebeol3se_loss_line`

```text
Task: one-work-only `canon_tighten` for `jaebeol3se_loss_line`.

Read in this order:
1. material_ssot/00_governance/delegation-envelope-spec-v1.md
2. docs/2026-04-08/jaebeol3se_loss_line_live_status.md
3. material_ssot/20_pitch/README.md
4. material_ssot/20_pitch/material-benchmark-readiness-harness-v1.md
5. material_ssot/20_pitch/synthesis/investment_dokshik_jaebeol3se_working_synthesis.md
6. material_ssot/20_pitch/synthesis/investment_dokshik_jaebeol3se_checklist_audit.md
7. treatments/phase0/jaebeol3se_loss_line_phase0_design.json
8. treatments/preprocess/jaebeol3se_loss_line/context_handoff_20260406.md

Write scope:
- material_ssot/20_pitch/canon/jaebeol3se_loss_line.md only

Task goal:
- restore the missing current-root canon pitch anchor so later root admission and continuation have a stable pitch authority again
- match the currently saved downstream truth; do not rewrite the work concept

Hard stops:
- no TR continuation
- no BI refresh
- no shared README edits

Validation:
- python -X utf8 scripts/material_readiness_validator.py --path material_ssot/20_pitch/canon/jaebeol3se_loss_line.md
- python -X utf8 scripts/material_promotion_gate.py --stage canon --path material_ssot/20_pitch/canon/jaebeol3se_loss_line.md

Final report:
- changed files
- restored authority anchors
- any remaining blocker before `root_admit`
```

## 7. Operator Note

If all five threads run in parallel, the clean integration order afterward should be:

1. `quiet_chaebol_heir`
2. `jaebeol3se_loss_line`
3. `hoegui_surgeon`
4. `manual_meridian_archivist`
5. `jangyeongshil_industrial_revolution`

Reason:

- `quiet` and `jaebeol` are authority-anchor cleanup tasks
- `hoegui` is a normalization task
- `manual` and `jang` are actual downstream narrative updates and should be reviewed after the authority/normalization lanes settle
