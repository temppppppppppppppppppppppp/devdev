# Repair-First Queue Execution Specs

Date: 2026-04-11
Status: active operator spec
Scope:

- current `repair-worth-it` shelf
- completed bounded repair archive:
  - `smart_new_hire`
  - `office_checkup_next_day`
  - `wuxia_heavenly_physician`
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

1. no unexecuted bounded repair spec is currently waiting
2. no current active `repair-worth-it` shelf item remains after `smart_new_hire` closed its opening manual re-audit on `2026-04-11`

Why this order:

- `wuxia_heavenly_physician` already exited whole-run `YELLOW` via the `2026-04-11` bounded late-run pressure reinjection repair
- `office_checkup_next_day` already exited both opening and whole-run `YELLOW` via the `2026-04-11` bounded authority-first repair
- `chaebol_ent_empire` already exited opening `YELLOW` via the same-day targeted repair recorded in [chaebol_ent_empire_opening_signboard_compression_repair_note.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-10/chaebol_ent_empire_opening_signboard_compression_repair_note.md)
- `pantech_cyworld_reborn` already exited opening `YELLOW` via the same-day bounded repair recorded in [pantech_cyworld_reborn_cadence_and_reevaluation_surface_repair_note.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-10/pantech_cyworld_reborn_cadence_and_reevaluation_surface_repair_note.md)
- `smart_new_hire` is still the only current `repair-worth-it` shelf item at the opening-layer reading, but both its bounded `ARC-05` front-half repair and its planned `B46~B50` continuation already executed on `2026-04-11`
- `smart_new_hire` then also cleared its opening `YELLOW` via the same-day declared-contract closeout (`signboard B02 / reevaluation B03 / ticket B06`)
- the repaired surface no longer ends on `late_blank_opponent`, and the opening layer no longer falls back to legacy heuristic, so no active repair-first lane remains

---

## 4. Pair Specs

- no currently unexecuted bounded execution spec
- completed bounded repair:
  - [repair_spec_smart_new_hire.md](/C:/Users/PC/Desktop/글도비/docs/2026-04-10/repair_spec_smart_new_hire.md)
  - [smart_new_hire_repair_note.md](/C:/Users/PC/Desktop/글도비/docs/2026-04-11/smart_new_hire_repair_note.md)
- completed spec archive:
  - [repair_spec_office_checkup_next_day.md](/C:/Users/PC/Desktop/글도비/docs/2026-04-10/repair_spec_office_checkup_next_day.md)
  - [office_checkup_next_day_repair_note.md](/C:/Users/PC/Desktop/글도비/docs/2026-04-11/office_checkup_next_day_repair_note.md)
  - [repair_spec_wuxia_heavenly_physician.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-10/repair_spec_wuxia_heavenly_physician.md)
  - [wuxia_heavenly_physician_repair_note.md](/C:/Users/PC/Desktop/글도비/docs/2026-04-11/wuxia_heavenly_physician_repair_note.md)
- historical completed spec:
  - [repair_spec_chaebol_ent_empire.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-10/repair_spec_chaebol_ent_empire.md)
  - [repair_spec_pantech_cyworld_reborn.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-10/repair_spec_pantech_cyworld_reborn.md)

---

## 5. Operator Reading

Current reading:

- `office_checkup_next_day` is no longer part of the active repair queue after the `2026-04-11` bounded authority-first repair
- `wuxia_heavenly_physician` is no longer part of the active repair queue after the `2026-04-11` bounded late-run pressure reinjection repair
- `smart_new_hire` is no longer part of the active repair queue after the `2026-04-11` opening manual re-audit closed the last remaining opening-layer `YELLOW`
- none has crossed into archive-first territory
- `smart_new_hire` now reads as a repaired live pair:
  - `B45` no longer closes the saved boundary as blank-opponent softness
  - `B46~B50` are serialized through the `ARC-05` exit (`승진 + 독자 line`)
  - opening pacing now returns `GREEN` under declared contract with `B02 / B03 / B06`
  - do not reopen `B01~B10` or `B41~B50` before a concrete inconsistency or a fresh non-repair lane
- `chaebol_ent_empire` is no longer part of the active repair queue after the same-day opening signboard compression repair
- `pantech_cyworld_reborn` is no longer part of the active repair queue after the same-day bounded cadence + reevaluation-surface repair
- no active `repair-worth-it` backlog item remains in this spec after the `2026-04-11` closeout

The point of this queue is not to make every repaired pair deployable immediately.
The point is to:

1. remove the local pacing debt
2. get them out of current `YELLOW`
3. only then decide whether any deserves a fresh sell-in closeout
