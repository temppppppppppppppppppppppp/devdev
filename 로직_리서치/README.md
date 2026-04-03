# 로직_리서치

Date: 2026-04-03
Status: legacy runtime note root

이 경로는 더 이상 research SSOT가 아니다.

현재 역할:

- legacy runtime note와 backward pointer 보관
- non-SSOT research runtime root라는 분류 유지
- collector code와 canonical output sink를 안내하는 진입점 역할

권위 경계:

- canonical research authority:
  - `material_ssot/10_research`
- canonical operator registry:
  - `material_ssot/10_research/00_registry`
- canonical promoted snapshots:
  - `material_ssot/10_research/40_analysis/market_snapshots`
- canonical promoted raw ingest:
  - `material_ssot/10_research/80_ingest_raw`

현재 로컬 규칙:

- collector code home:
  - `scripts/research_collectors`
- `output/`은 pointer-only legacy surface다.
- 사람이 읽는 정본이나 stage-consumable 결과는 `material_ssot` 경로를 먼저 본다.
- 새 collector run은 `scripts/research_collectors`에서 실행한다.
