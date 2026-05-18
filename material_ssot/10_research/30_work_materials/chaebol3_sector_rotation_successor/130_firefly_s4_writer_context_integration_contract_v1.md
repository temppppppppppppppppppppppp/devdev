# Firefly S4 Writer Context Integration Contract v1

Date: 2026-05-17
Status: integration contract draft, research-only
Work ID: `chaebol3_sector_rotation_successor`
Issue: #157
Evidence: `116`, `118/121`, `122/124`, `127/129`

## 0. Boundary

This is a research-only integration contract.

It does not authorize:

- B11-B20;
- TR70;
- BI;
- Firefly DB/project mutation;
- `manuscript save`;
- production manuscript save;
- production S4 prompt change;
- work_guard publication.

It defines how compact material handoffs may be translated into Firefly S4 Writer Context fields in a future research dry run.

## 1. Problem

The material side now has scene-native packets that work in file-only smoke.

But if Firefly S4 receives them as raw research text, it will likely expose labels, write report-like prose, or explain the mechanism.

The missing piece is a small translation contract:

`compact material packet -> filled S4 Writer Context -> prose -> post-write audit`

This contract keeps S2-S3-S4 as the mainline. It does not add a new stage.

## 2. Source Fields From Compact Material

Each unit from a `116`-style compact handoff must provide these fields:

| Compact material field | Meaning | Example from passed smokes |
|---|---|---|
| `room_surface` | where the pressure is visible | finance small room, quality table, buyer desk |
| `live_objects` | objects that must move or remain | green card, import-material file, sample box, chalkboard |
| `starting_pressure` | what can fail now | budget precedent, defective shiny line, return calls |
| `resisting_actor` | who resists on page | finance manager, factory manager, buyer |
| `protected_cost` | what the actor protects | file hierarchy, blame, parent calls, shelf risk |
| `smaller_permission` | what Doyun asks for instead of victory | one hour, passed-count pay, 30 pairs |
| `visible_objection` | dissent that remains written/visible | no front display, no full budget, shiny line hold |
| `final_object_position` | where the reward physically lands | file on desk, plain sample in box, box beside phone |
| `next_gate` | next concrete door | import-material search, buyer/school desk, public-use trial |

## 3. Mapping To Firefly S4 Writer Context

Use this mapping in a future dry run.

| Firefly S4 Writer Context field | Fill from compact material | Must not become |
|---|---|---|
| `work_frame` | `room_surface` + current task | abstract "this episode is about reward" |
| `live_transaction` | `starting_pressure` + `smaller_permission` | general plot summary |
| `priced_loss` | `protected_cost` in money, blame, calls, labor, access, hierarchy | vague risk |
| `resistant_witness` | `resisting_actor` plus why they cannot simply agree | flat antagonist |
| `access_gain` | `final_object_position` + exact permission | praise, trust, recognition |
| `behavior_ladder` | three to five visible actions from objection to object placement | explanation ladder |
| `final_price_tag_translation` | what changed in cost/access/responsibility | metaphor or theme |
| `final_receipt_and_next_gate` | object/access in hand and next door | unrelated cliffhanger |

## 4. Writer-Facing Conversion Rule

Before drafting prose, strip all labels.

The writer should see:

- room;
- people;
- objects;
- practical fear;
- smaller ask;
- final placement.

The writer should not see:

- reward ladder;
- receipt;
- protected asset;
- canary;
- compact handoff;
- AI-slop;
- harness;
- "the protagonist's competence is narrowing."

Instead of:

`Doyun's competence is narrowing the claim.`

Use:

`Doyun lowers 60 pairs to 30 before the buyer can send the box back.`

Instead of:

`The final receipt is object position.`

Use:

`The box remains beside the phone and return ledger.`

## 5. Required Post-Draft Audit

Every research dry run using this contract must run a line-level audit that asks:

1. Did the prose show the room before explaining the meaning?
2. Did the resisting actor ask practical questions before curiosity/praise?
3. Did Doyun ask for less than the obvious victory?
4. Did one objection remain visible?
5. Did the final beat leave an object/access token in place?
6. Did the prose contain a line explaining why the object matters?
7. Did any dialogue sound like a checklist?
8. Did the output remain `draft_not_db_saved`?

If answer 6 or 7 is yes:

- patch the line;
- replace explanation with hand, pen, box, phone, card, clock, shelf, board, or door behavior;
- re-audit.

## 6. Minimum Dry Run Packet Shape

A future Firefly-side file-only dry run should include:

```json
{
  "status": "draft_not_db_saved",
  "source": "116_style_compact_material",
  "s4_writer_context": {
    "work_frame": "...",
    "live_transaction": "...",
    "priced_loss": "...",
    "resistant_witness": "...",
    "access_gain": "...",
    "behavior_ladder": ["...", "...", "..."],
    "final_price_tag_translation": "...",
    "final_receipt_and_next_gate": "..."
  },
  "prose": "...",
  "post_write_micro_audit": {
    "s4_writer_context_used": true,
    "s4_writer_context_status": "pass|warn|fail",
    "revision_required": true
  }
}
```

This JSON is a planning shape only. Do not save it through Firefly DB.

## 7. Current Evidence Mapping

| Evidence | Surface | Contract lesson |
|---|---|---|
| `118/121` | finance/file-room | object access must stay supervised; remove thesis-clean explanation |
| `122/124` | product-hand | future-knowledge/meta should become touch/material failure |
| `127/129` | buyer desk | risk questions must precede box opening; final reward is box placement |

## 8. Decision

Next unit:

`Create one sample S4 Writer Context fill for EP007 buyer desk using this contract, file-only, no prose generation yet.`

Reason:

The buyer-desk prose already passed. Now test whether the context fields can carry it without leaking labels.

Stoplines:

- no B11-B20;
- no TR70;
- no BI;
- no Firefly DB/project mutation;
- no production manuscript save.
