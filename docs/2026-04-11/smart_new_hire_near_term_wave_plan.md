# smart_new_hire Near-Term Wave Plan

Date: 2026-04-12
Status: pipeline complete (live BI saved, audit PASS)
Scope:

- `smart_new_hire`
- post-TR material-side execution after full 70-block completion
- serial authority writes remain mandatory

## 1. Current Reading

- the serial live `TR` lane is complete
- full TR authority now exists at `treatments/smart_new_hire_tr_block_070_draft.json`
- `treatments/smart_new_hire_tr_block_001_draft.json` remains as a synced mirror, not an open continuation target
- there is no active repair-first lane on this pair
- live BI exists at `bible/0_bi_smart_new_hire.json`
- raw BI build passed on `2026-04-12`
- BI 5-pass audit passed on `2026-04-12`
- there is no active write lane on this pair

## 2. Immediate Next Lane

- keep `bible/0_bi_smart_new_hire.json` as the live BI authority
- keep `bible/audit_reports/smart_new_hire_bi_5pass.md` as the current BI audit authority
- preserve the `070` draft as the source authority and the `001` mirror as a synced reference only
- current gates satisfied:
  - opening pacing `GREEN`
  - whole-run pacing `GREEN`
  - block continuity `CLEAN`
  - Stage 0 handoff validator `PASS`
  - BI build `PASS`
  - BI 5-pass audit `PASS`

## 3. Optional Side Lanes

- `work_guard` retrofill remains allowed as a separate fresh-order standardization lane
- optional `work_guard` retrofill remains a separate fresh-order standardization lane
- no multi-writer execution against the live `TR`

## 4. Do Not Do

- do not reopen `B61~B70` absent a concrete inconsistency
- do not attempt a fictional `B71+` continuation
- do not restart repair-first work on this pair
- do not reopen the pair for continuation absent a fresh operator order
- do not let missing `work_guard` rewrite the completed stage reading
