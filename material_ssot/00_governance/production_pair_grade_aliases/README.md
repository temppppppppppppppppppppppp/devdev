# Production Pair Grade Aliases

Snapshot date: `2026-04-08`

이 폴더는 live `TR + BI` pair의 등급 alias snapshot이다.
정본 파일명은 유지하고, 이 폴더에서만 `{등급}_...` 파일명으로 본다.

정식 등급 부여 기준은:

- `../production-pair-benchmark-spec-v1.md`

이 alias snapshot은 감으로 붙이지 않고, 위 benchmark spec의 `P0 hard gates -> cap rules -> P1 score -> grade decision` 순서로 판정한 뒤에만 갱신한다.

Operational interlock:

- live alias operation also follows `../production-pair-operating-policy-addendum-v1.md`
- untouched historical live pairs may temporarily keep a historical alias snapshot while carrying open `block_cider` migration debt
- no pair may newly earn or refresh `GREENPLUS` or `GREEN` while open migration debt remains
- report `benchmark grade` and `schema status` separately; do not collapse them into one label
- the current filename list is an alias snapshot, and its live freshness should still be read together with `../production-pair-operational-registry-v1.md`
- after the 2026-04-08 benchmark freshness wave, all aliased pairs listed below are benchmark-fresh on the current registry

Legend:
- `GREENPLUS_`: 지금 기준 상위권. protagonist-first 철학 보존도가 특히 높음.
- `GREEN_`: production ready 축에 들어가지만 일부 잔여 리스크가 있음.
- `YELLOW_`: 엔진은 강하지만 현재 철학 기준 보정 포인트가 남음.
- `RED_`: pair-level benchmark failure. promotion / alias 상향 전 대수선 필요.

Current aliases:
- `GREENPLUS_defense_defect_engineer.md`
- `GREENPLUS_office_checkup_next_day.md`
- `GREENPLUS_chaebol_allowance_zero.md`
- `GREENPLUS_chaebol_ent_empire.md`
- `GREENPLUS_투자물_골든_카나리아 테스트_canonical_v1.md`
- `GREENPLUS_wuxia_heavenly_physician.md`
- `GREENPLUS_pantech_cyworld_reborn.md`
- `GREEN_jangyeongshil_industrial_revolution.md`
- `GREEN_manual_meridian_archivist.md`
