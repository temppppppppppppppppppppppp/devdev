# Canonical Pitch Template v1

Status: active template
Scope: future canonical pitch docs under `material_ssot/20_pitch/canon/`

## 1. Before You Write

Read first:

- `material_ssot/20_pitch/cider-doctrine-v1.md`
- `material_ssot/20_pitch/material-benchmark-readiness-harness-v1.md`
- `material_ssot/20_pitch/pitch-philosophy.md`
- `material_ssot/20_pitch/protagonist-first-constitution.md`
- `material_ssot/20_pitch/pitch-selection-checklist.md`
- the correct family planning harness

## 2. No Local Reinterpretation Contract

This file has no authority to reinterpret house law.

It must not:

- relax `first block` away from strict `2~6`
- use block `1` as opening cider proof
- use block `7+` as opening rescue
- call a draft with false ledger rows `selection-ready`
- use `bridge_or_payback_note` as promotion proof
- freeze a `work_guard` ahead of an unresolved upstream ledger

If any of the above would be required, the file must stop at `HOLD`, not self-upgrade.

## 3. Minimum Canon Shape

1. `Authority`
2. `Pitch Truth`
3. `Early Conversion`
4. `First-Block Cider Ledger`
5. `Readiness Declaration`
6. `Phase0 Handoff Note`

## 4. First-Block Cider Ledger Rule

The canon pitch must include exact rows for `2, 3, 4, 5, 6`.

Each row must name:

- `block_no`
- `has_cider`
- `same_block_receipt`
- `receipt_kind`
- `pain_only_exit`

Write the rows in this exact machine-readable shape:

```md
- block_no: 2
  has_cider: true
  same_block_receipt: ...
  receipt_kind: ...
  bridge_or_payback_note:

- block_no: 3
  has_cider: true
  same_block_receipt: ...
  receipt_kind: ...
  bridge_or_payback_note:

- block_no: 4
  has_cider: true
  same_block_receipt: ...
  receipt_kind: ...
  bridge_or_payback_note:

- block_no: 5
  has_cider: true
  same_block_receipt: ...
  receipt_kind: ...
  bridge_or_payback_note:

- block_no: 6
  has_cider: true
  same_block_receipt: ...
  receipt_kind: ...
  pain_only_exit: false
  bridge_or_payback_note:
```

For canon lock:

- all rows must be `has_cider: true`
- `same_block_receipt` must be explicit
- `block 6 pain_only_exit` must be `false`

## 5. Readiness Declaration

The file must explicitly state all of the following:

- `selection-ready: yes/no`
- `Phase0-ready: yes/no`
- `all 2~6 ledger rows have has_cider true: yes/no`
- `block 1 used as opening rescue: yes/no`
- `block 7+ used as opening rescue: yes/no`

If any answer blocks promotion, the file must say so plainly.

Before canon lock, run:

- `python -X utf8 scripts/material_readiness_validator.py --path <canon-md>`
