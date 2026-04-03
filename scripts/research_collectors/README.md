# research_collectors

Date: 2026-04-03
Status: active runtime collector code root

이 경로는 research collector 실행 코드를 보관하는 runtime code root다.

역할:

- collection-only crawler scripts 실행
- raw ingest를 `material_ssot/10_research/80_ingest_raw/YYYY-MM-DD/`에 기록
- derived snapshot을 `material_ssot/10_research/40_analysis/market_snapshots/YYYY-MM-DD/`에 기록

권위 경계:

- human-facing research authority:
  - `material_ssot/10_research`
- runtime notes / legacy pointer surface:
  - `로직_리서치`

현재 스크립트:

- `crawl_new_novels.py`
- `crawl_syuka.py`
- `crawl_top100.py`
- `crawl_youtube.py`
