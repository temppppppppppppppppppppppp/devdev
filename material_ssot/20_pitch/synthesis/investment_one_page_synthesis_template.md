# Investment One-Page Synthesis Template

Status: operator template
Scope: investment-lane fresh candidate synthesis before canon selection

Primary upstream references:

- `material_ssot/10_research/20_fewshot_bank/investment_engine_pack.md`
- `material_ssot/20_pitch/cider-doctrine-v1.md`
- `material_ssot/20_pitch/material-benchmark-readiness-harness-v1.md`
- `material_ssot/20_pitch/pitch-selection-checklist.md`
- `material_ssot/20_pitch/protagonist-first-constitution.md`
- `work_guards/investment/default_work_guard.yaml`

Current lane constraint:

- active investment fresh candidates are `male protagonist only`

## 0. Header

- work_id:
- working title:
- protagonist sex: `male`
- status: `draft synthesis`
- selected deep engines:
  - engine 1:
  - engine 2:
  - engine 3:
  - optional engine 4:
  - optional engine 5:
- selected supporting material lanes:
  - lane 1:
  - optional lane 2:

## 1. One-Line Premise

- ``

Rule:

- write the premise as `저평가된 현재 자리 + 먼저 읽는 투자/산업 감각 + 평가 수정 + 자본 환전`

## 2. Why This Protagonist Stays

- why the protagonist does not resign even after the first payout:
- what information or access exists only if the protagonist stays in the company, desk, or family seat:
- what disappears if the protagonist exits too early:

## 3. Starting Position

- current job or family seat:
- current humiliation:
- what others misread about the protagonist:
- why the protagonist is not at fault:

## 4. Investment Edge

- what the protagonist reads first:
- what others cannot yet price correctly:
- how that read converts into a trade, hedge, or allocation move:
- what makes the move protagonist-only:

## 5. First Proof Scene

- room:
- audience:
- protagonist move:
- evaluator line:
- one-line proof:

Rule:

- the scene should end with `태도 변화` or `다시 봐야 한다`, not just profit

## 6. First Block Reward

- status or access first:
- authority or seat shift:
- initial capital or asset gain second:

Rule:

- write rewards in this order:
  1. evaluation revision
  2. access or authority token
  3. seed capital or realized gain

## 7. First-Block Cider Ledger (`2~6`)

```md
- block_no: 2
  has_cider: true/false
  same_block_receipt: ...
  receipt_kind: ...
  bridge_or_payback_note:

- block_no: 3
  has_cider: true/false
  same_block_receipt: ...
  receipt_kind: ...
  bridge_or_payback_note:

- block_no: 4
  has_cider: true/false
  same_block_receipt: ...
  receipt_kind: ...
  bridge_or_payback_note:

- block_no: 5
  has_cider: true/false
  same_block_receipt: ...
  receipt_kind: ...
  bridge_or_payback_note:

- block_no: 6
  has_cider: true/false
  same_block_receipt: ...
  receipt_kind: ...
  pain_only_exit: true/false
  bridge_or_payback_note:
```

Rule:

- investment lane also follows the same strict `2~6` readiness contract
- `selection-ready` requires all five rows to be `has_cider: true`
- if any row is false, the current verdict cannot rise above `HOLD`

## 8. Authority Gain Route

- Block 1:
- Block 2:
- Block 3:
- who must now explain themselves to the protagonist:
- what line, seat, or channel now opens:

## 9. Crisis 4-Element Check

- first read:
- response tool:
- minimum damage control:
- immediate recovery vector:

## 10. Reward Weight Check

- before rewrite risk:
  - asset-first wording:
  - status-first wording:
- corrected target wording:
  - evaluation revision first:
  - capital figure after:

## 11. Must-Not-Copy

- no exact app or cheat UI
- no copied ticker, company, or event number
- no quit-work fantasy opening
- no self-pity or apology arc
- no asset-first reward narration
- no insider-trading brag fantasy

## 12. Current Selection Guess

- innocence:
- first win = evaluation revision:
- proof scene:
- early reward = status first:
- ledger `2~6` all pay:
- crisis 4 elements:
- likely verdict: `PASS / HOLD / REJECT`

Use this exact readiness claim shape somewhere in the file:

```md
- selection-ready: yes/no
- Phase0-ready: yes/no
- all 2~6 rows pay in-block: yes/no
- block 1 used as opening rescue: yes/no
- block 7+ used as opening rescue: yes/no
```

## 13. Promotion Note

- if PASS:
  - move the locked truth into `20_pitch/canon/`
- after canon lock:
  - translate only the compressed runtime doctrine into work-specific `work_guard.yaml`
