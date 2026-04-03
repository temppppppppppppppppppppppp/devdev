# 2026-04-03 Raw Ingest Bucket

Date: 2026-04-03
Status: first bounded cutover bucket from `로직_리서치/output`

Contents:

- raw collector ingest promoted from `로직_리서치/output/_*.jsonl`

Current count:

- `11` raw jsonl files

Split note:

- `_ebsdocu_raw.jsonl` was split into `_ebsdocu_raw.part01.jsonl` and `_ebsdocu_raw.part02.jsonl` to keep each file below the GitHub 100MB push limit

Source note:

- derived snapshots for the same collection wave live under `material_ssot/10_research/40_analysis/market_snapshots/2026-04-03/`
