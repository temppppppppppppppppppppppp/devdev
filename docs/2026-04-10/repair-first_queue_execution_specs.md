# Repair-First Queue Execution Specs

Date: 2026-04-10
Status: active operator spec
Scope:

- current `repair-worth-it` shelf
- bounded repair execution planning for:
  - `wuxia_heavenly_physician`
  - `office_checkup_next_day`
- completed same-day bounded repair archive:
  - `chaebol_ent_empire`
  - `pantech_cyworld_reborn`
- cross-PC continuation packet:
  - [remaining_repair_queue_cross_pc_handoff.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-10/remaining_repair_queue_cross_pc_handoff.md)

---

## 1. Role

This document answers one question:

- if we actually repair the current non-RED queue, how should we do it without drifting into rebuild

Reading rule:

- `RED` is closed and not reopened
- this queue is not about proving they are good already
- this queue is about whether targeted repair is cheaper than rebuild and where the cut line should be

---

## 2. Execution Law

Common guard:

- do not touch `RED`
- do not widen scope into full-wave rewrite unless the spec explicitly says so
- preserve `_total_blocks`, block order, and core fantasy
- preserve existing arc spine unless the spec explicitly says contract realignment is required
- repair should first target:
  - opening compression mismatch
  - signboard timing
  - repeated defeat grammar
  - late-run opponent pressure fade
- after each repair unit, re-run:
  - opening pacing triage
  - whole-run pacing check if relevant
  - deployable `GREENPLUS` read only after the pair clears `YELLOW`

Not allowed:

- prestige-driven rewrite
- "while we are here" broad surgery
- repair that changes the work into a different lane
- repair that erases the pair's existing benchmark strengths

---

## 3. Priority Order

Recommended repair order:

1. `wuxia_heavenly_physician`
2. `office_checkup_next_day`

Why this order:

- `wuxia_heavenly_physician` is a bounded late-run pressure reinjection job
- `office_checkup_next_day` is the most complex because it requires contract-vs-delivery reconciliation before it can close cleanly
- `chaebol_ent_empire` already exited opening `YELLOW` via the same-day targeted repair recorded in [chaebol_ent_empire_opening_signboard_compression_repair_note.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-10/chaebol_ent_empire_opening_signboard_compression_repair_note.md)
- `pantech_cyworld_reborn` already exited opening `YELLOW` via the same-day bounded repair recorded in [pantech_cyworld_reborn_cadence_and_reevaluation_surface_repair_note.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-10/pantech_cyworld_reborn_cadence_and_reevaluation_surface_repair_note.md)

---

## 4. Pair Specs

- [repair_spec_wuxia_heavenly_physician.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-10/repair_spec_wuxia_heavenly_physician.md)
- [repair_spec_office_checkup_next_day.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-10/repair_spec_office_checkup_next_day.md)
- historical completed spec:
  - [repair_spec_chaebol_ent_empire.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-10/repair_spec_chaebol_ent_empire.md)
  - [repair_spec_pantech_cyworld_reborn.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-10/repair_spec_pantech_cyworld_reborn.md)

---

## 5. Operator Reading

Current reading:

- these two are still active repair jobs
- none has crossed into archive-first territory
- but none should be touched without a bounded spec
- `chaebol_ent_empire` is no longer part of the active repair queue after the same-day opening signboard compression repair
- `pantech_cyworld_reborn` is no longer part of the active repair queue after the same-day bounded cadence + reevaluation-surface repair
- `smart_new_hire` remains current `repair-worth-it` backlog, but no bounded execution spec has been published yet

The point of this queue is not to make all two active spec targets deployable immediately.
The point is to:

1. remove the local pacing debt
2. get them out of current `YELLOW`
3. only then decide whether any deserves a fresh sell-in closeout
