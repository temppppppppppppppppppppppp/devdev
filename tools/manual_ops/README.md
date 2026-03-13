# Manual Ops

Scripts under `tools/` that rely on hard-coded paths, direct DB mutation, or one-off operator workflows are manual-only utilities.

Current manual-only scripts:
- `normalize_arcs_db.py`
- `db_porter.py`
- `fix_future_items.py`
- `make_BP.py`
- `concat_txt.py`

These scripts are not part of the production runtime, API/Desktop bridge, or CI/pytest contract.
