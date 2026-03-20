# Narrative Router README

Purpose:
- keep routed narrative-family entrypoints out of root `README.md`
- reduce merge-conflict surface with future mainline README changes

## Router Entry

```bash
python -X utf8 scripts/narrative_router.py --genre wuxia --work-id <work_id> --json
```

## Routed TR Entry

```bash
python -X utf8 scripts/narrative_tr_batch.py --genre wuxia prompt --start 1 --batch-size 3
python -X utf8 scripts/narrative_tr_batch.py --genre wuxia check --candidate treatments/<candidate>.json --draft treatments/<work_id>_tr_block_070_draft.json --start 1 --batch-size 3
python -X utf8 scripts/narrative_tr_batch.py --genre wuxia merge --draft treatments/<work_id>_tr_block_070_draft.json --candidate treatments/<candidate>.json --start 1 --batch-size 3
```

## Routed BI Entry

```bash
python -X utf8 scripts/build_narrative_bi.py --genre wuxia --phase0 treatments/<work_id>_phase0_design.json --draft treatments/<work_id>_tr_block_070_draft.json --output bible/0_bi_<work_id>.json
python -X utf8 scripts/audit_narrative_bi.py --genre wuxia --phase0 treatments/<work_id>_phase0_design.json --draft treatments/<work_id>_tr_block_070_draft.json --bi bible/0_bi_<work_id>.json --report bible/audit_reports/<work_id>_wuxia_bi_5pass.md
```

## Scope

These entrypoints are for narrative-pipeline TR/BI production only.
They do not modify the main Geuldobi runtime unless you explicitly wire them into it later.
