# smart_new_hire Repair Spec

Date: 2026-04-11
Status: bounded repair spec
Target:

- `smart_new_hire`
- current state: `repair-worth-it`, opening `YELLOW` under legacy heuristic, whole-run `GREEN`

---

## 1. Core Diagnosis

Debt type:

- primary: `ARC-05` front-half boundary compression drift
- sharpest weak unit: `B45`
- secondary signal: opening `YELLOW` exists, but it is not the first repair surface

Current reading:

- live saved truth currently ends at `B45`, and `B1~B40` remains structurally healthy
- `B41~B44` each still carry explicit opponent pressure plus clear receipts, so the front-half machine is not broken
- the softest point is `B45`, where the quiet lock is valid but the live boundary currently ends on:
  - quiet block
  - `opponent = null`
  - `receipt = null`
  - external asset delta `0`
- whole-run pacing triage on `2026-04-11` still returns `GREEN`, but it flags `late_blank_opponent_blocks = [45]`, which matches the boundary-softness read
- opening pacing triage on `2026-04-11` returns `YELLOW`, but that read is explicitly `legacy_heuristic` with `opening_contract_declared = false`
- preprocess, Phase0, and the live TR still agree that the `B2~B6` opening machine is strong, so this spec should not widen into opening rewrite first

Sources:

- [current-yellow-salvageability-split.md](/C:/Users/PC/Desktop/글도비/docs/2026-04-10/current-yellow-salvageability-split.md)
- [smart_new_hire_live_status.md](/C:/Users/PC/Desktop/글도비/docs/2026-04-09/smart_new_hire_live_status.md)
- [smart_new_hire_phase0_design.json](/C:/Users/PC/Desktop/글도비/treatments/phase0/smart_new_hire_phase0_design.json)
- [material_bundle_summary.json](/C:/Users/PC/Desktop/글도비/treatments/preprocess/smart_new_hire/material_bundle_summary.json)
- [smart_new_hire_tr_block_001_draft.json](/C:/Users/PC/Desktop/글도비/treatments/smart_new_hire_tr_block_001_draft.json)

---

## 2. Repair Surface

Recommended surface:

- `TR only`

Why:

- live authority already exists through `B45`
- `Phase0` `ARC-05` slot law is still correct; the profitable cut is local repair, not upstream redesign
- `B46+` is not saved truth yet, so the cheapest admissible move is to tighten the saved boundary before any continuation

Do not start with:

- opening rewrite
- `Phase0` rebuild
- `B46~B50` continuation generation
- retroactive prestige cleanup outside the saved `ARC-05` front half

---

## 3. Bounded Edit Window

Primary edit window:

- `B41~B45`

Mandatory anchor:

- `B45`

Support window:

- `B41~B44` only where needed to sharpen role separation and feed `B45` more cleanly

What to do:

- preserve the slot functions:
  - `B41 후보표`
  - `B42 누가 키웠나`
  - `B43 승진 과제`
  - `B44 공동권한의 대가`
  - `B45 줄 하나의 무게`
- keep `B45` quiet, but make it land as a hard doctrinal handoff rather than a soft vacuum
- sharpen the difference among `B41~B44` so the sequence does not read as repeated office/label/control variation
- give `B45` a cleaner carry-forward bridge into `B46~B48` without fabricating unsaved `B46+` truth
- keep the `title vs line below` doctrine, but trim any over-explanation that weakens the boundary edge

What not to do:

- do not reopen `B1~B40`
- do not force cider or an external attack onto `B45`; quiet lock must stay intact
- do not infer or write `B46~B50` inside this repair unit
- do not flatten the office-power lane into generic self-help doctrine

---

## 4. Preserve

Must preserve:

- the `B2~B6` first-block cider ledger and current opening machine
- `Phase0` quiet lock `B45` and defeat lock `B48`
- `B40 -> B41` capital handoff and current `ARC-05` entry state
- the ownerliness / structure-first lane, especially the `title != line below position` doctrine

---

## 5. Success Condition

This repair is successful only if:

- `B41~B45` no longer reads as four similar structure beats followed by a soft boundary vacuum
- `B45` stays quiet but becomes a decisive doctrinal handoff to `B46~B48`
- the next admissible move after the repair is fresh bounded continuation, not another spec rewrite
- post-repair re-triage can judge whether the legacy opening `YELLOW` still needs separate action

---

## 6. Operator Note

Shortest reading:

- leave opening alone for now
- repair `B41~B45`
- treat `B45` as the mandatory anchor
- keep `B45` quiet, but not slack
