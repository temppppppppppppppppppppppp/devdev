# Cider Doctrine v1

Date: 2026-04-07
Status: active
Scope: first-block catharsis contract for `material_ssot/20_pitch`

## 1. First-Read Law

- when a model enters `material_ssot` pitch work, this doctrine should be read before premise expansion, Phase0, `TR`, or `BI`
- for judgment, `first block` means strictly blocks or episodes `2~6`
- every first block must contain at least one visible `cider`
- a first block that ends with only failure, humiliation, scolding, suspicion, probation, delay, or `later payoff` does not pass
- pain is allowed only when it cashes out inside the same block as recovery asset, evaluation revision, protection, authority, or the next gate
- if the work cannot name the first-block cider in one plain sentence, hold it before `Phase0`

### 1.1 Strict Window Rule

- for first-block judgment, count episodes or blocks `2~6` only
- do not count episode or block `1` as first-block `cider`; it is opening setup, not the catharsis window
- do not count episode or block `7+` as first-block `cider`; that is late rescue, not valid first-block conversion
- if the first concrete reward lands at episode or block `7` or later, the opening fails
- if proof happens in `2~6` but reevaluation or token first lands at `7+`, the opening still fails

### 1.2 First-Block Ledger Rule

- every fresh pitch or planning unit should write `first_block_cider_ledger`
- the ledger is a fixed five-row table for blocks `2, 3, 4, 5, 6`
- each row must mark:
  - `has_cider: true/false`
  - `cider_elements`
  - `visible_reward_token`
  - `bridge_or_payback_note`
  - `pain_only_exit`
- blank is never acceptable
- in exploratory draft work, `false` may appear only as a hole marker and the default verdict is `HOLD`
- in `selection-ready`, `canon`, or `Phase0-ready` judgment, every row for `2~6` must be `has_cider: true`
- `bridge_or_payback_note` may explain a thin receipt, but it may not rescue a false row
- if `block 6` closes as `pain_only_exit: true`, the opening fails

### 1.3 Readiness Rule

- use `material-benchmark-readiness-harness-v1.md` for future material-side readiness audits
- `draft` may expose holes
- `selection-ready` may not carry holes
- any false row in blocks `2~6` means:
  - `HOLD` for fresh candidate
  - no canon promotion
  - no `Phase0-ready` promotion
- `work_guard` compression may not override a false row upstream

## 2. Minimum First-Block Conversion

Every first block must lock all of the following:

1. `protagonist-only proof`
   - the reader must feel `저건 쟤라서 가능했다`
2. `evaluation revision`
   - someone with weight must update how they see the protagonist
3. `visible reward token`
   - a thing the reader can count or feel lands on-page
4. `next gate opening`
   - the reward opens block 2 instead of ending the engine
5. `no pain-only exit`
   - failure or humiliation may appear, but the block cannot close on failure or humiliation alone

## 3. Preferred Visible Reward Tokens

- real-name call
- seat at the table
- `CC` / report-line entry
- direct report right
- approval right
- project or `TF` assignment
- budget speech right
- signature right
- permit hold
- protection from a higher line
- public reevaluation
- enemy stance shift
- next battlefield entry ticket

## 4. Planning Candidate 7 Questions

Use these seven questions as the compact `planning_candidate` gate.

1. What does the protagonist want now, and why must it move inside the first block?
2. What information gap or reading edge belongs only to the protagonist?
3. What is the first-block proof scene that makes `저건 쟤라서 가능했다` undeniable?
4. What visible cider lands inside episodes `2~6`?
5. Who reevaluates the protagonist inside the first block, and how is that visible on-page?
6. How does that first-block reward open block 2?
7. What contamination would turn this opening into `고구마`, and how is it explicitly banned?

Hard rule:

- if any one of the seven cannot be answered in plain language, default to `HOLD`
- if questions `3`, `4`, or `6` are weak, do not promote into `Phase0`
- if question `4` is answered with block `1` or block `7+`, treat it as unanswered and default to `HOLD`
- if any `first_block_cider_ledger` row in `2~6` is `false`, treat the candidate as `HOLD` until the hole is repaired

## 5. Work Guard 5-Point Freeze Check

Use these five checks before `WG-V2 PASS`.

1. Does `one_line_truth` promise reward and ascent, not theme, suffering, or atmosphere alone?
2. Do `mandatory_scene_engines` include both protagonist-only proof and visible evaluation revision?
3. Do `tracking_slots` and `custom_rules` force first-block cider to open the next gate?
4. Do `evaluation_thresholds` or equivalent rules explicitly require first-block visible reward inside one block?
5. Do `forbidden_flattenings` ban failure-only, humiliation-only, or `success -> pure punishment spiral` openings?

Freeze rule:

- all five should read as `yes`
- one weak item is `HOLD`
- a guard that cannot prove first-block cider should not freeze
- a guard translated from an upstream ledger with any false row should not freeze

## 6. Operator Shorthand

- `proof alone is not cider`
- `pain alone is not tension`
- `failure alone is not depth`
- `first block must pay`
- `block 2 opens with reward earned in block 1`
