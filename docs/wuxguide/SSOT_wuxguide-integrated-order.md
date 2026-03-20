# Wuxguide Integrated Order

Date: 2026-03-20
Status: active
Scope: wuxia / xianxia narrative family
Entry Point: `docs/narrative-router/SSOT_narrative-router-integrated-order.md`

## 1. Purpose

- Provide a family SSOT for wuxia / xianxia planning, TR, BI, and audit.
- Preserve existing `blockguide` semantics for modern-fantasy business-power works.
- Make `MartialHUD` canonical for martial-family BI output.

## 2. Read Order

1. `docs/narrative-router/SSOT_narrative-router-integrated-order.md`
2. this file
3. `docs/wuxguide/wuxia-planning-harness.md`
4. `docs/wuxguide/wuxia-production-harness.md`
5. `docs/wuxguide/wuxia-bi-production-harness.md`

## 3. Family Identity

Choose `wuxguide` when the dominant story engine is martial-family first:

- realm progression
- internal-energy / cultivation gain
- martial-art acquisition or refinement
- sect / clan / jianghu politics
- revenge, grievance, inheritance, or manual / treasure pursuit

Do not choose `wuxguide` just because the story contains action scenes.

## 4. Shared Stage Policy

- `phase0_design` missing: planning
- `phase0_design` exists and `tr_block_070_draft` missing: production
- `tr_block_070_draft` exists and `0_bi_{work_id}.json` missing: BI
- existing BI still requires audit PASS before completion

## 5. Shared Artifact Paths

- `treatments/preprocess/{work_id}/source_manifest.json`
- `treatments/preprocess/{work_id}/profile_lock.json`
- `treatments/preprocess/{work_id}/material_bundle_summary.json`
- `treatments/preprocess/{work_id}/phase0_ready_snapshot.json`
- `treatments/{work_id}_phase0_design.json`
- `treatments/{work_id}_tr_block_070_draft.json`
- `bible/0_bi_{work_id}.json`

## 6. Canonical Semantic Shift

Inside `wuxguide`, the canonical BI root is `MartialHUD`.

- `FinanceHUD` is not canonical for this family.
- runtime aliasing is allowed only when a bridge explicitly requires it.
- the core progression axes are `realm`, `internal_energy`, `martial_arts`, `faction`, and `jianghu_reputation`.

## 7. Operator Runbook

Always start from the router:

```bash
python -X utf8 scripts/narrative_router.py --genre wuxia --work-id <work_id> --json
```

Resume rules:

1. If `stage == planning`, open `docs/wuxguide/wuxia-planning-harness.md`.
2. If `stage == production`, open `docs/wuxguide/wuxia-production-harness.md`.
3. If `stage == bi`, open `docs/wuxguide/wuxia-bi-production-harness.md`.
4. If `stage == audit_or_repair`, audit the BI first and repair the smallest failing layer.

If `artifact_state.preprocess_ready == false`, return to `전처리_ssot/docs/SSOT_stage0_preprocess_integrated_order.md` before family planning.

## 8. Routed CLI Examples

Planning gate check:

```bash
python -X utf8 scripts/narrative_router.py --genre wuxia --work-id <work_id>
```

TR prompt / check / merge:

```bash
python -X utf8 scripts/narrative_tr_batch.py --genre wuxia prompt --draft treatments/<work_id>_tr_block_070_draft.json --roadmap bible/0_bi_<work_id>.json --start 1 --batch-size 3
python -X utf8 scripts/narrative_tr_batch.py --genre wuxia check --candidate treatments/<candidate>.json --draft treatments/<work_id>_tr_block_070_draft.json --start 1 --batch-size 3 --report treatments/<work_id>_batch_check.md
python -X utf8 scripts/narrative_tr_batch.py --genre wuxia merge --draft treatments/<work_id>_tr_block_070_draft.json --candidate treatments/<candidate>.json --start 1 --batch-size 3 --report treatments/<work_id>_batch_merge.md
```

BI build and audit:

```bash
python -X utf8 scripts/build_narrative_bi.py --genre wuxia --phase0 treatments/<work_id>_phase0_design.json --draft treatments/<work_id>_tr_block_070_draft.json --output bible/0_bi_<work_id>.json
python -X utf8 scripts/audit_narrative_bi.py --genre wuxia --phase0 treatments/<work_id>_phase0_design.json --draft treatments/<work_id>_tr_block_070_draft.json --bi bible/0_bi_<work_id>.json --report bible/audit_reports/<work_id>_wuxia_bi_5pass.md
```

## 9. Guardrails

- Do not force `capital_before/after` into wuxia validation.
- Do not reuse `deal_type`, `business_lines`, `company_state`, or `starter_company` as primary martial-family anchors.
- Do not pass BI while `MartialHUD` is incomplete or out of sync with the final TR block.
