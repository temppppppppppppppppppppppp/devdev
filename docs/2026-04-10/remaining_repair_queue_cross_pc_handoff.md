# Remaining Repair Queue Cross-PC Handoff

Date: 2026-04-10
Status: active continuation packet
Audience:

- another PC operator
- future Codex continuation

Purpose:

- let the remaining non-RED queue continue on another machine without rebuilding context
- keep future repair work fast, bounded, and consistent with current governance

---

## 1. Non-Negotiable Boundaries

Do not do:

- do not reopen any `RED`
- do not touch runtime pipeline
- do not touch `글도비_파이어플라이`
- do not widen a bounded repair into a prestige rewrite
- do not rewrite benchmark alias files just because one pacing field changed

Current hard law:

- `RED` = terminal archive / anti-benchmark
- `GREEN` = provisional keep unless separately closed out
- `deployable GREENPLUS` = separate manual closeout, not automatic after a repair

---

## 2. Current Truth Snapshot

As of this packet:

- completed same-day repair archives:
  - `chaebol_ent_empire`
  - `pantech_cyworld_reborn`
- remaining current repair-worth-it shelf:
  - `wuxia_heavenly_physician`
  - `office_checkup_next_day`
  - `smart_new_hire`

Operational state:

- opening pacing triage:
  - `RED 3 / YELLOW 2 / GREEN 9 / UNTRIAGED 1`
- current YELLOW salvageability split:
  - `repair-worth-it 3 / kill-candidate 0`

Primary SSOT:

- [production-pair-operational-registry-v1.md](/C:/Users/wjjo/Desktop/글도비/material_ssot/00_governance/production-pair-operational-registry-v1.md)
- [production-pair-operational-registry-v1.json](/C:/Users/wjjo/Desktop/글도비/material_ssot/00_governance/production-pair-operational-registry-v1.json)

---

## 3. Read Order

If continuing from another PC, read in this order:

1. [remaining_repair_queue_cross_pc_handoff.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-10/remaining_repair_queue_cross_pc_handoff.md)
2. [repair-first_queue_execution_specs.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-10/repair-first_queue_execution_specs.md)
3. [current-yellow-salvageability-split.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-10/current-yellow-salvageability-split.md)
4. target-specific repair spec
5. target work guard
6. target TR draft
7. target repair note if one already exists

Use these target specs:

- [repair_spec_wuxia_heavenly_physician.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-10/repair_spec_wuxia_heavenly_physician.md)
- [repair_spec_office_checkup_next_day.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-10/repair_spec_office_checkup_next_day.md)

For `smart_new_hire`:

- no bounded execution spec exists yet
- if this work is chosen next, first create:
  - `docs/2026-04-10/repair_spec_smart_new_hire.md`

---

## 4. Current Queue and Best Next Step

Recommended next repair order:

1. `wuxia_heavenly_physician`
2. `office_checkup_next_day`
3. `smart_new_hire` after a fresh bounded spec is written

Why:

- `wuxia` is still the cleanest bounded `TR only` job
- `office` is harder because it is `preprocess + phase0 + TR`
- `smart_new_hire` still needs a spec before execution

---

## 5. Target-by-Target Continuation Notes

### 5.1 `wuxia_heavenly_physician`

Current debt:

- whole-run `YELLOW`
- late-run opponent pressure fade
- especially:
  - `B61`
  - `B65`
  - `B66`
  - `B70`

Surface:

- `TR only`

Primary window:

- `B60~B66`

Tail check:

- `B67~B70`

Success condition:

- whole-run pacing re-audit exits `YELLOW`
- late blocks no longer feel like blank-opponent drag
- craft rhythm survives

Files:

- [09_wuxia_heavenly_physician_tr_block_070_draft.json](/C:/Users/wjjo/Desktop/글도비/treatments/09_wuxia_heavenly_physician_tr_block_070_draft.json)
- [repair_spec_wuxia_heavenly_physician.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-10/repair_spec_wuxia_heavenly_physician.md)
- [green-whole-run-pacing-reaudit-wave.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-10/green-whole-run-pacing-reaudit-wave.md)

### 5.2 `office_checkup_next_day`

Current debt:

- opening `YELLOW`
- declared contract vs actual delivery mismatch
- additional local drag:
  - `B23~B25`
  - `B31~B35`
  - `B61~B67`

Surface:

- `preprocess + phase0 + TR`

Authority-first rule:

1. decide whether current opening contract remains authoritative
2. prefer `delivery-up`, not `contract-down`
3. only then clean later drag pockets

Files:

- [07_office_checkup_next_day_tr_block_070_draft.json](/C:/Users/wjjo/Desktop/글도비/treatments/07_office_checkup_next_day_tr_block_070_draft.json)
- [office_checkup_next_day_phase0_design.json](/C:/Users/wjjo/Desktop/글도비/treatments/phase0/office_checkup_next_day_phase0_design.json)
- [material_bundle_summary.json](/C:/Users/wjjo/Desktop/글도비/treatments/preprocess/office_checkup_next_day/material_bundle_summary.json)
- [repair_spec_office_checkup_next_day.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-10/repair_spec_office_checkup_next_day.md)

### 5.3 `smart_new_hire`

Current debt:

- still `repair-worth-it`
- no current bounded execution spec
- saved truth currently ends at `B45`

Known concentration:

- `ARC-05`
- especially `B41~B45`

Required first step:

- create `repair_spec_smart_new_hire.md`
- do not start editing the TR before the spec exists

Files:

- [smart_new_hire_tr_block_001_draft.json](/C:/Users/wjjo/Desktop/글도비/treatments/smart_new_hire_tr_block_001_draft.json)
- [smart_new_hire_phase0_design.json](/C:/Users/wjjo/Desktop/글도비/treatments/phase0/smart_new_hire_phase0_design.json)
- [smart_new_hire_live_status.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-09/smart_new_hire_live_status.md)

---

## 6. Validation Commands

Run these after every bounded repair:

```powershell
python C:\Users\wjjo\Desktop\글도비\scripts\production_pair_opening_pacing_triage_runner.py --treatment <TR_PATH>
python C:\Users\wjjo\Desktop\글도비\scripts\production_pair_whole_run_pacing_triage_runner.py --treatment <TR_PATH>
python C:\Users\wjjo\Desktop\글도비\scripts\validate_material_ssot.py
```

Use whole-run triage especially for:

- `wuxia_heavenly_physician`

Use opening triage especially for:

- `office_checkup_next_day`

Use both once a new `smart_new_hire` repair spec is executed.

---

## 7. If a Repair Succeeds

Create one execution note:

- `docs/2026-04-10/<work_id>_repair_note.md`

Then update current-state surfaces:

- [production-pair-opening-pacing-triage-wave.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-10/production-pair-opening-pacing-triage-wave.md)
- [current-yellow-salvageability-split.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-10/current-yellow-salvageability-split.md)
- [repair-first_queue_execution_specs.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-10/repair-first_queue_execution_specs.md)
- [production-pair-operational-registry-v1.md](/C:/Users/wjjo/Desktop/글도비/material_ssot/00_governance/production-pair-operational-registry-v1.md)
- [production-pair-operational-registry-v1.json](/C:/Users/wjjo/Desktop/글도비/material_ssot/00_governance/production-pair-operational-registry-v1.json)

Do **not** automatically update:

- historical Sonnet audit artifacts
- historical order docs

Those stay as audit trail unless they are explicitly being rewritten as current-state docs.

---

## 8. Where To Append Future Context

If another PC works on this queue, append a new dated entry at the bottom of **this file** first.

Append format:

```md
## Session Log - YYYY-MM-DD HH:MM

- operator:
- target:
- files touched:
- commands run:
- result:
- unresolved:
- next admissible step:
```

Reason:

- future Codex can reopen one file and instantly recover:
  - what was attempted
  - what changed
  - what still blocks closure

---

## 9. Shortest Reading

If someone else continues this work:

- read this file first
- do `wuxia` before `office`
- do not touch `smart_new_hire` until a fresh bounded spec exists
- append every continuation session to this same file before leaving
