# Wave 1 Repair 3-Terminal Opus Orders

Date: 2026-04-07
Status: active
Scope: Wave 1 active-pair repair execution for `08`, `09`, `07`

## Common Guard

- edit the target `TR` file directly
- do not touch `BI` or `work_guard`
- preserve `_total_blocks`, block order, and existing engine
- repair only the flagged no-cider blocks named below
- every repaired block must gain a **same-block reader-countable receipt**
- no full-wave rewrite
- after edit, write a short markdown repair note under `docs/2026-04-07/`
- the repair note must name:
  - edited block numbers
  - exact receipt added per block
  - why each edited block now satisfies `has_cider:true`
  - what was intentionally left untouched

## Orders

1. `C:\Users\wjjo\Desktop\글도비\docs\2026-04-07\10pair_true_benchmark_terminal08_pair08_report.md`와 `C:\Users\wjjo\Desktop\글도비\treatments\08_pantech_cyworld_reborn_tr_block_070_draft.json`를 읽고, flagged no-cider blocks `B04 / B57 / B63 / B66`만 repair하라; benchmark report의 repair unit 취지를 따르되 target TR의 해당 블록 안에 same-block receipt 1건씩 직접 착륙시켜 `has_cider:true`로 전환하고, 다른 블록은 건드리지 말라; 수정 결과를 TR 원본 파일에 저장하고 `C:\Users\wjjo\Desktop\글도비\docs\2026-04-07\wave1_pair08_repair_note.md`에 짧은 repair note를 작성하라.

2. `C:\Users\wjjo\Desktop\글도비\docs\2026-04-07\10pair_true_benchmark_terminal09_pair09_report.md`와 `C:\Users\wjjo\Desktop\글도비\treatments\09_wuxia_heavenly_physician_tr_block_070_draft.json`를 읽고, flagged no-cider blocks `13 / 28 / 29`만 repair하라; report의 Top 3 Repair Units를 그대로 실행하되 wuxguide 톤과 `진단 -> 처방 -> 시술 -> 경과` 리듬을 보존한 채 각 블록 안에 same-block receipt를 넣어 `has_cider:true`로 전환하고, 특히 `28`은 손해와 동시에 next-card receipt가 블록 안에 보이게 하라; 수정 결과를 TR 원본 파일에 저장하고 `C:\Users\wjjo\Desktop\글도비\docs\2026-04-07\wave1_pair09_repair_note.md`에 짧은 repair note를 작성하라.

3. `C:\Users\wjjo\Desktop\글도비\docs\2026-04-07\10pair_true_benchmark_terminal07_pair07_report.md`와 `C:\Users\wjjo\Desktop\글도비\treatments\07_office_checkup_next_day_tr_block_070_draft.json`를 읽고, flagged no-cider blocks `1 / 25 / 32 / 35 / 43 / 48 / 53 / 63 / 65 / 66`만 full flagged-block sweep하라; report의 Repair-1/2/3 우선순위를 따르되 본문 엔진과 사건 순서를 바꾸지 말고 각 대상 블록에 same-block receipt 또는 micro-token을 직접 부착해 `has_cider:true`로 전환하라; 수정 결과를 TR 원본 파일에 저장하고 `C:\Users\wjjo\Desktop\글도비\docs\2026-04-07\wave1_pair07_repair_note.md`에 짧은 repair note를 작성하라.
