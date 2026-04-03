# 로직_리서치 Source Registry

Date: 2026-04-03
Status: active runtime-source registry

## 1. Current Classification

- path: `로직_리서치`
- authority label: `non-ssot legacy runtime note root`
- current role: legacy runtime note root + pointer surface for collector lineage

## 2. Current Surfaces

### A. Collector Scripts

- canonical runtime code home:
  - `scripts/research_collectors`
- active scripts:
  - `scripts/research_collectors/crawl_new_novels.py`
  - `scripts/research_collectors/crawl_syuka.py`
  - `scripts/research_collectors/crawl_top100.py`
  - `scripts/research_collectors/crawl_youtube.py`

### B. Operator Note

- canonical runbook:
  - `material_ssot/10_research/00_registry/youtube-parallel-collector-runbook.md`
- legacy pointer:
  - `로직_리서치/ORDER_youtube_parallel.md`

### C. Raw Ingest

- current canonical bucket:
  - `material_ssot/10_research/80_ingest_raw/2026-04-03/`
- current promoted count:
  - `11` raw jsonl files
- oversized raw bucket handling:
  - `_ebsdocu_raw.jsonl` was split into `_ebsdocu_raw.part01.jsonl` and `_ebsdocu_raw.part02.jsonl` for GitHub pushability while preserving line-delimited raw evidence
- legacy runtime pointer:
  - `로직_리서치/output/README.md`

### D. Derived Snapshots

- current canonical bucket:
  - `material_ssot/10_research/40_analysis/market_snapshots/2026-04-03/`
- current promoted count:
  - `88` json/csv snapshot files
- legacy runtime pointer:
  - `로직_리서치/output/README.md`

### E. Disposable Cache

- `__pycache__/`

## 3. Target Mapping

- crawler scripts:
  - canonical runtime code home: `scripts/research_collectors/`
- raw ingest:
  - canonical bucket: `material_ssot/10_research/80_ingest_raw/YYYY-MM-DD/`
- derived snapshots:
  - canonical bucket: `material_ssot/10_research/40_analysis/market_snapshots/YYYY-MM-DD/`
- operator note:
  - canonical home: `material_ssot/10_research/00_registry/`

## 4. Immediate Rule

- do not treat `로직_리서치` as a human-facing research authority root
- when a result should be cited or consumed by stage SSOT, first promote it into `material_ssot`
- 2026-04-03 first bounded cutover completed for `output/`
- 2026-04-03 operator note promotion completed for the YouTube parallel runbook
- 2026-04-03 crawler code cutover completed into `scripts/research_collectors/`
