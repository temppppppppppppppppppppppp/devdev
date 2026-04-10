# office_checkup_next_day Repair Spec

Date: 2026-04-10
Status: bounded repair spec
Target:

- `office_checkup_next_day`
- current state: `repair-worth-it`, opening `YELLOW`, declared-contract mismatch

---

## 1. Core Diagnosis

Debt type:

- `opening contract vs actual delivery mismatch`
- plus localized middle/late drag

Current reading:

- operator memo still says scaffold is repair-worthy, not rebuild-worthy
- but deployable audit found a harder problem than paperwork:
  - declared opening bundle contract says:
    - signboard `B03`
    - reevaluation `B05`
    - next ticket `B03`
  - actual delivery reads closer to:
    - signboard practical `B07`
    - reevaluation practical `B08`
    - next ticket practical `B09`

Additional local drag clusters:

- `B23~B25`
- `B31~B35`
- `B61~B67`

Sources:

- [current-yellow-salvageability-split.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-10/current-yellow-salvageability-split.md)
- [terminal_03_office_checkup_deployable_greenplus_audit.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-10/terminal_03_office_checkup_deployable_greenplus_audit.md)
- [07_office_checkup_next_day_tr_block_070_draft.json](/C:/Users/wjjo/Desktop/글도비/treatments/07_office_checkup_next_day_tr_block_070_draft.json)
- [office_checkup_next_day_phase0_design.json](/C:/Users/wjjo/Desktop/글도비/treatments/phase0/office_checkup_next_day_phase0_design.json)
- [material_bundle_summary.json](/C:/Users/wjjo/Desktop/글도비/treatments/preprocess/office_checkup_next_day/material_bundle_summary.json)

---

## 2. Repair Surface

Recommended surface:

- `preprocess + phase0 + TR`

Why:

- this is the one current queue member where the contract surface itself is implicated
- if we only edit TR without deciding which opening contract is authoritative, the pair can become cleaner while still staying mismatched on paper

Preferred operator path:

1. treat the current contract as the intended target
2. compress the TR opening to deliver that contract more honestly
3. only if that fails, downgrade the declared contract to match actual delivery

Meaning:

- preferred path is `delivery-up`, not `contract-down`

---

## 3. Bounded Edit Window

Primary authority window:

- `opening contract fields`
  - `material_bundle_summary.json`
  - `phase0_design.json`
- `TR B01~B09`

Secondary drag window:

- `B23~B25`
- `B31~B35`
- `B61~B67`

What to do:

- make `B03` feel like a real signboard, not just one-person notice
- make `B05` carry actual reevaluation, not discovery-only movement
- make the next battlefield ticket legible before `B09`
- then shave the later local drag clusters without disturbing the authority ladder through `B30/B40/B50/B60/B69`

What not to do:

- do not start with a global rewrite
- do not blunt the office/power chain into generic corporate noise
- do not let contract cleanup become cosmetic-only paperwork

---

## 4. Preserve

Must preserve:

- current authority ladder checkpoint sequence through `B30/B40/B50/B60/B69`
- the office/decision battlefield identity
- the feeling that the pair is dense rather than empty

---

## 5. Success Condition

This repair is successful only if:

- declared contract and actual delivery no longer diverge on opening timing
- opening pacing can exit `YELLOW`
- the later local drag clusters shrink without breaking the authority ladder
- the pair can be re-audited without depending on "contract exists, but actual delivery is elsewhere"

---

## 6. Operator Note

This is the hardest repair among the current four.

Shortest reading:

- align authority first
- then compress opening
- then clean the later drag pockets
