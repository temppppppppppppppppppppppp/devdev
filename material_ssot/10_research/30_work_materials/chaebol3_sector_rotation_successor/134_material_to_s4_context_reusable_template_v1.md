# Material-to-S4 Context Reusable Template v1

Date: 2026-05-17
Status: reusable template draft, research-only
Work ID: `chaebol3_sector_rotation_successor`
Issue: #157
Evidence: `116`, `118/121`, `122/124`, `127/129`, `130/131`, `132/133`

## 0. Boundary

This template is a material-side bridge.

It does not authorize:

- B11-B20;
- TR70;
- BI;
- Firefly DB/project mutation;
- `manuscript save`;
- production manuscript save;
- production S4 prompt change;
- work_guard publication.

It exists to translate a compact material unit into Firefly's existing S4 Writer Context shape before any file-only prose test.

## 1. Why This Exists

The passed canaries show a repeated failure mode:

Good material becomes weaker prose when S4 receives philosophy, audit language, or broad BI/TR labels.

The fix is not to abandon S2-S3-S4.

The fix is:

`compact material unit -> S4 Writer Context fill -> stripped writer view -> file-only prose -> line-level audit`

This template standardizes that middle layer.

## 2. Required Input: Compact Material Unit

Each unit must be no larger than one scene or one tight episode surface.

Required source fields:

| Field | Required answer |
|---|---|
| `unit_id` | human-readable source pointer, such as `H07 / EP007 buyer desk` |
| `room_surface` | where the pressure is visible |
| `live_objects` | 3-6 objects that move, remain, are withheld, or change hands |
| `starting_pressure` | what can fail in this room now |
| `resisting_actor` | who resists on page |
| `protected_cost` | what that actor protects in money, blame, calls, time, access, hierarchy, or reputation |
| `smaller_permission` | what Doyun asks for instead of victory |
| `visible_objection` | dissent or limit that remains on paper, object, body, or desk |
| `final_object_position` | where the reward physically lands |
| `next_gate` | the next concrete door, person, file, room, call, or shipment path |

Reject the unit if any answer is abstract:

- "authority rises";
- "reader feels reward";
- "trust begins";
- "competence is proved";
- "the next sector opens."

## 3. S4 Writer Context Fill

Fill Firefly's existing S4 context fields with material-side content.

```json
{
  "status": "draft_not_db_saved",
  "source": {
    "compact_material": "...",
    "passed_canary_or_audit": "..."
  },
  "boundary": {
    "firefly_db_mutation": false,
    "manuscript_save": false,
    "production_manuscript_save": false,
    "production_s4_prompt_change": false,
    "b11_b20_authorized": false,
    "tr70_authorized": false,
    "bi_authorized": false
  },
  "s4_writer_context": {
    "work_frame": "room_surface + current task in one sentence",
    "live_transaction": "starting_pressure + smaller_permission",
    "priced_loss": "protected_cost translated into concrete money/blame/call/time/access/hierarchy",
    "resistant_witness": "resisting_actor + why agreement is unsafe for them",
    "access_gain": "final_object_position + exact permission or tolerated access",
    "behavior_ladder": [
      "visible action 1",
      "visible action 2",
      "visible action 3",
      "visible action 4"
    ],
    "final_price_tag_translation": "what changed in cost/access/responsibility, without theme language",
    "final_receipt_and_next_gate": "object/access in place + next concrete gate"
  },
  "writer_do_not_show": [
    "reward ladder",
    "receipt",
    "protected asset",
    "canary",
    "compact handoff",
    "AI-slop",
    "harness",
    "the protagonist's competence is narrowing"
  ]
}
```

## 4. Writer-Visible View

Before prose, strip labels into a scene-facing note.

Allowed writer-visible note:

```text
Use the school-supply buyer desk. Keep the phone, return ledger, sample box, front display, and memo visible.
The buyer protects return calls, delivery penalties, parent complaints, and shelf space.
Doyun must ask for less than a comeback display: 30 pairs, return cap 3, no front display, school calls handled directly.
The objection must remain written.
End with the box still beside the phone and return ledger, and the next door being the school goods shipment/public-use trial.
```

Forbidden writer-visible note:

```text
Show the reward ladder. Translate the protected asset. Make the final receipt clear.
```

Reason:

The first note can become human behavior.
The second note becomes harness prose.

## 5. Post-Context Audit

Before prose, audit the filled context.

| Check | Pass condition |
|---|---|
| room before theme | first field contains a visible room/surface |
| object count | at least 3 concrete objects appear |
| practical resistance | actor protects a concrete cost, not ego alone |
| smaller ask | Doyun asks for less than obvious victory |
| visible objection | some limit remains written/placed/withheld |
| final object/access | ending changes object/access position |
| no future proof shortcut | future knowledge is not used as explanation |
| boundary explicit | file-only and no DB/save/prompt-change are explicit |

If any check fails, patch the context before prose.

## 6. Post-Prose Audit

After a file-only prose dry run, audit line by line.

Reject or patch if prose contains:

- a sentence explaining why the object matters instead of showing object behavior;
- dialogue that sounds like checklist fulfillment;
- praise/trust replacing small permission;
- curiosity before practical risk;
- final beat as theme, mood, or vague anticipation;
- production labels such as canary, packet, receipt, harness, S4, context, audit.

Required final beat:

- one object/access token remains in place;
- one resisting actor's cost is still visible;
- the next gate is opened by the same token, not by a new teaser.

## 7. Known Surface Lessons

| Evidence | Surface | Reusable rule |
|---|---|---|
| `118/121` | finance/file-room | access is stronger when supervised and limited; remove thesis-clean explanation |
| `122/124` | product-hand | product proof must be touch/material/count, not product concept |
| `127/129` | buyer desk | risk questions must precede box opening; final reward is object placement |
| `132/133` | S4 context fill | field names can carry context, but writer-visible prose must strip labels |

## 8. Next Authorized Unit

Use this template for one file-only prose dry run from `132`.

Stoplines:

- no DB mutation;
- no `manuscript save`;
- no production prompt change;
- no B11-B20;
- no TR70;
- no BI.
