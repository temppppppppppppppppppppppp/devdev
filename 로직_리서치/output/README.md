# output

Date: 2026-04-03
Status: legacy pointer only

This folder is no longer the canonical or runtime home for collector outputs.

Current canonical locations:

- raw ingest:
  - `material_ssot/10_research/80_ingest_raw/2026-04-03/`
- derived snapshots:
  - `material_ssot/10_research/40_analysis/market_snapshots/2026-04-03/`

Remaining rule:

- runtime collectors now write directly into `material_ssot` dated buckets
- no new collector output should be created in this folder
