# Fresh Candidate Template v1

Status: active template
Scope: future intake candidate files under `material_ssot/20_pitch/intake/`

## 1. Before You Write

Read first:

- `material_ssot/20_pitch/cider-doctrine-v1.md`
- `material_ssot/20_pitch/material-benchmark-readiness-harness-v1.md`
- `material_ssot/20_pitch/pitch-philosophy.md`
- `material_ssot/20_pitch/pitch-selection-checklist.md`
- the correct synthesis template

## 2. Candidate Status Contract

This file must declare one of only three states:

- `draft`
- `hold`
- `selection-ready`

Rules:

- `draft` may expose holes
- `hold` means the idea has heat but cannot be promoted
- `selection-ready` is allowed only when all `2~6` ledger rows are `has_cider: true`

## 3. No Local Reinterpretation Contract

This file must not self-authorize promotion by:

- treating block `1` as opening cider
- treating block `7+` as opening rescue
- calling a false row `basically true`
- using `bridge_or_payback_note` as promotion proof
- calling vibes, theme, or later payoff a same-block receipt

If any of those happen, the status must fall back to `hold`.

## 4. Minimum Candidate Shape

1. `Candidate Frame`
2. `Pitch Truth`
3. `Early Conversion`
4. `First-Block Cider Ledger`
5. `Readiness Claim`
6. `Phase0 Handoff Note`

Inside `First-Block Cider Ledger`, write rows in this exact machine-readable shape:

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

## 5. Readiness Claim

The file must answer:

- `selection-ready: yes/no`
- `Phase0-ready: yes/no`
- `all 2~6 rows pay in-block: yes/no`
- `block 1 used as opening rescue: yes/no`
- `block 7+ used as opening rescue: yes/no`

If any answer is `no`, the file must not call itself `selection-ready`.

Before promotion, run:

- `python -X utf8 scripts/material_readiness_validator.py --path <intake-md>`
