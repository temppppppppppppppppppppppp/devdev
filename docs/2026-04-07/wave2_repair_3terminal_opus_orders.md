# Wave 2 Repair 3-Terminal Opus Orders

Date: 2026-04-07
Status: active
Scope: Wave 2 active-pair repair execution for `03`, `04`, `01`

## Common Guard

- edit the target `TR` file directly
- do not touch `BI` or `work_guard`
- preserve `_total_blocks`, block order, and the existing engine
- repair only the flagged no-cider blocks named below
- every repaired block must gain a **same-block reader-countable receipt**
- do not solve a flagged block by moving payoff to the next block
- do not full-wave rewrite
- after edit, write a short markdown repair note under `docs/2026-04-07/`
- the repair note must name:
  - edited block numbers
  - exact receipt added per block
  - why each edited block now satisfies `has_cider:true`
  - what was intentionally left untouched

## Orders

1. `C:\Users\wjjo\Desktop\글도비\docs\2026-04-07\10pair_true_benchmark_terminal03_pair03_report.md`와 `C:\Users\wjjo\Desktop\글도비\treatments\03_chaebol_ent_empire_tr_block_070_draft.json`를 읽고, flagged no-cider blocks `4 / 16 / 23 / 28 / 34 / 47 / 55 / 63`만 full flagged-block sweep하라; 각 블록 안에 same-block token 또는 receipt를 직접 착륙시켜 `has_cider:true`로 전환하되, 특히 `55 / 63`은 report가 지적한 defeat_mechanic 뼈대를 보존한 채 same-block 회수 카드만 추가하라; 다른 블록과 사건 순서는 건드리지 말고, 수정 결과를 원본 TR 파일에 저장한 뒤 `C:\Users\wjjo\Desktop\글도비\docs\2026-04-07\wave2_pair03_repair_note.md`에 짧은 repair note를 작성하라.

2. `C:\Users\wjjo\Desktop\글도비\docs\2026-04-07\10pair_true_benchmark_terminal04_pair04_report.md`와 `C:\Users\wjjo\Desktop\글도비\treatments\04_defense_defect_engineer_tr_block_070_draft.json`를 읽고, flagged no-cider blocks `1 / 3 / 5 / 7 / 11 / 19 / 24 / 31 / 43 / 49 / 55 / 63 / 67`만 repair하라; report의 doctrine을 따라 대부분은 defeat-block same-block receipt 1줄, `B5`는 quiet access-shift token 1종, `B1`은 future-prep token 1줄로 처리하고, 다른 필드·다른 블록·phase checkpoint 구조는 건드리지 말라; 수정 결과를 원본 TR 파일에 저장한 뒤 `C:\Users\wjjo\Desktop\글도비\docs\2026-04-07\wave2_pair04_repair_note.md`에 짧은 repair note를 작성하라.

3. `C:\Users\wjjo\Desktop\글도비\docs\2026-04-07\10pair_true_benchmark_terminal01_pair01_report.md`와 `C:\Users\wjjo\Desktop\글도비\treatments\01_tr_투자물_골든_카나리아 테스트_canonical_v1.json`를 읽고, flagged no-cider blocks `1 / 5 / 8 / 19 / 25 / 27 / 31 / 32 / 33 / 34 / 44`만 full flagged-block sweep하라; report의 우선순위대로 `B31~B34` drought를 먼저 분쇄하고, 나머지 `B1 / B5 / B8 / B19 / B25 / B27 / B44`에는 observer-update beat 또는 mid-block next-card receipt를 1줄씩 추가해 `has_cider:true`로 전환하라; early reward thin-pass 구조를 악화시키지 말고, 다른 블록과 자산 곡선은 건드리지 말며, 수정 결과를 원본 TR 파일에 저장한 뒤 `C:\Users\wjjo\Desktop\글도비\docs\2026-04-07\wave2_pair01_repair_note.md`에 짧은 repair note를 작성하라.
