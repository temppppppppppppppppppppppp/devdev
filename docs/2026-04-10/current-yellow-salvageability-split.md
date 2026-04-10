# Current YELLOW Salvageability Split

Date: 2026-04-10
Status: active operator memo
Scope:

- current repair-candidate `YELLOW` shelf
- opening `YELLOW 2`
- plus whole-run `YELLOW 1`

Primary question:

- should any current `YELLOW` be promoted to `RED`
- or are they still cheaper to repair than rebuild

---

## 1. Reading Rule

- `repair-worth-it`:
  - debt is local/compressible
  - scaffold still works
  - targeted rewrite is cheaper than rebuild
- `kill-candidate`:
  - opening or late pacing debt is structural
  - phase0 or arc spine is poisoned enough that rebuild is cheaper

`RED` remains terminal.
This memo is about whether current `YELLOW` should be promoted there.

---

## 2. Result

Summary:

- `repair-worth-it`: `3`
- `kill-candidate`: `0`

Operator reading:

- no current `YELLOW` gets promoted to `RED` in this pass
- the present repair queue stays a repair queue
- budget should go to targeted compression / cadence rewrite, not rebuild

---

## 3. Pair Calls

### 3.1 `office_checkup_next_day`

- ruling: `repair-worth-it`
- why:
  - opening contract is valid and early receipts land on time
  - biggest debt is local drag in `B23-B25`, `B31-B35`, and especially `B61-B67`
  - authority ladder still converts cleanly through `B30`, `B40`, `B50`, `B60`, `B69`
- references:
  - [07_office_checkup_next_day.yaml](/C:/Users/wjjo/Desktop/글도비/work_guards/07_office_checkup_next_day.yaml#L74)
  - [07_office_checkup_next_day_tr_block_070_draft.json](/C:/Users/wjjo/Desktop/글도비/treatments/07_office_checkup_next_day_tr_block_070_draft.json#L3182)
  - [07_office_checkup_next_day_tr_block_070_draft.json](/C:/Users/wjjo/Desktop/글도비/treatments/07_office_checkup_next_day_tr_block_070_draft.json#L5880)
  - [07_office_checkup_next_day_tr_block_070_draft.json](/C:/Users/wjjo/Desktop/글도비/treatments/07_office_checkup_next_day_tr_block_070_draft.json#L6656)
  - [office_checkup_next_day_phase0_design.json](/C:/Users/wjjo/Desktop/글도비/treatments/phase0/office_checkup_next_day_phase0_design.json#L977)

### 3.2 `smart_new_hire`

- ruling: `repair-worth-it`
- why:
  - `B1-B40` machine is functioning and phase0 alignment is intact
  - debt is concentrated in `ARC-05` front half, especially `B41-B45`, where office/label/control framing repeats too similarly
  - current saved truth ends at `B45`, so this is a bounded but still positive salvage call
- references:
  - [smart_new_hire_tr_block_001_draft.json](/C:/Users/wjjo/Desktop/글도비/treatments/smart_new_hire_tr_block_001_draft.json#L4825)
  - [smart_new_hire_tr_block_001_draft.json](/C:/Users/wjjo/Desktop/글도비/treatments/smart_new_hire_tr_block_001_draft.json#L5364)
  - [smart_new_hire_phase0_design.json](/C:/Users/wjjo/Desktop/글도비/treatments/phase0/smart_new_hire_phase0_design.json#L168)
  - [smart_new_hire_live_status.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-09/smart_new_hire_live_status.md#L86)

### 3.3 `wuxia_heavenly_physician`

- ruling: `repair-worth-it`
- why:
  - whole-run `YELLOW` is real, but the debt is concentrated in late opponent fade and overlong `B60-B66` conversion/training blocks
  - `ARC-07` phase0 spine is still coherent, and the final boss/finale structure remains intact
  - repair target is late compression plus opponent-pressure reinjection, not rebuild
- references:
  - [09_wuxia_heavenly_physician_tr_block_070_draft.json](/C:/Users/wjjo/Desktop/글도비/treatments/09_wuxia_heavenly_physician_tr_block_070_draft.json#L5970)
  - [09_wuxia_heavenly_physician_tr_block_070_draft.json](/C:/Users/wjjo/Desktop/글도비/treatments/09_wuxia_heavenly_physician_tr_block_070_draft.json#L6308)
  - [09_wuxia_heavenly_physician_tr_block_070_draft.json](/C:/Users/wjjo/Desktop/글도비/treatments/09_wuxia_heavenly_physician_tr_block_070_draft.json#L6478)
  - [09_wuxia_heavenly_physician_tr_block_070_draft.json](/C:/Users/wjjo/Desktop/글도비/treatments/09_wuxia_heavenly_physician_tr_block_070_draft.json#L6814)
  - [wuxia_heavenly_physician_phase0_design.json](/C:/Users/wjjo/Desktop/글도비/treatments/phase0/wuxia_heavenly_physician_phase0_design.json#L1)

---

## 4. Queue Closeout

Current queue:

- `repair-worth-it`
  - `office_checkup_next_day`
  - `smart_new_hire`
  - `wuxia_heavenly_physician`

- `kill-candidate`
  - none

Operator reading:

- do not spend more time trying to promote these `YELLOW` works into `RED`
- the better next step is repair-cost ordering inside this queue
- `chaebol_ent_empire` left the current `YELLOW` shelf after the targeted opening compression repair recorded in [chaebol_ent_empire_opening_signboard_compression_repair_note.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-10/chaebol_ent_empire_opening_signboard_compression_repair_note.md)
- `pantech_cyworld_reborn` left the current `YELLOW` shelf after the bounded cadence + reevaluation-surface repair recorded in [pantech_cyworld_reborn_cadence_and_reevaluation_surface_repair_note.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-10/pantech_cyworld_reborn_cadence_and_reevaluation_surface_repair_note.md)

---

## 5. Next Admissible Step

1. order the `repair-worth-it` queue by cheapest/highest-yield repair
2. start with localized compression jobs before any broad rewrite
3. keep `RED` shelf closed; this memo found no new archive candidate
