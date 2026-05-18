# Firefly S4 Scene-Native Material Bridge v1

Date: 2026-05-17
Status: active operator bridge
Scope: material-side `pitch -> work_guard -> Phase0 -> TR -> BI` creation when the material is expected to feed Firefly S2-S3-S4 or any close writer pipeline

## 1. Purpose

This bridge exists because a material can pass broad `BI/TR/GUARD` shape and still fail at Stage 4 writing.

The failure mode is not usually logic absence. It is that the writer receives:

- sector lists instead of rooms;
- reward labels instead of visible object movement;
- future-knowledge summaries instead of current-scene proof;
- authority words instead of people protecting rank, money, responsibility, and procedure;
- a full premise packet when the writer needs the next narrow scene.

This document does not replace the material-side stage chain.

It adds one compatibility requirement:

`BI/TR/GUARD` must preserve scene-native material that a Stage 4 writer can immediately dramatize without exposing harness language.

## 2. Operating Rule

For any material intended to feed Firefly or writer-facing output, every upstream layer must answer:

`What does the reader see move on the page?`

### 2A. PD Taste Firewall

New or touched writer-facing material must not sound like a schema, test plan, or internal production table.

Blocked in writer-facing packets, episode notes, and prose seeds:

- `파일 접근권`
- `파일 열람권`
- `열람 시간`
- `access token`
- `next gate`
- `reward token`
- `receipt`
- `context fill`
- `payload`
- `operator`
- `harness`
- `proof ladder`

If the story needs that meaning, write it as taste:

- a bigger amount is entrusted;
- a team chooses to stay;
- the grandfather asks one more question;
- an adult stops joking;
- a rival can no longer treat the protagonist as a child;
- the protagonist's room, money, people, or schedule gets larger.

This firewall is stricter than legacy bridge wording. Legacy terms may remain in old audits, but a new/touched writer-facing packet fails if it uses them as story language.

Acceptable answers include:

- a file moves to the top of a stack;
- a room route changes;
- a phone call is made earlier than planned;
- a chair, badge, account, quote sheet, meeting slot, desk access, or report line opens;
- a person changes behavior because their responsibility, money, rank, deadline, or liability changed.

Weak answers include:

- `authority increases`;
- `reward paid`;
- `reader receipt`;
- `sector rotation`;
- `the protagonist proves competence`;
- `the gate opens`;
- `future knowledge is used`.

Those may remain planning labels, but they are not enough for writer handoff.

## 3. Stage Placement

### 3.1 Pitch / Canon

Pitch canon must lock the commercial truth, but for Firefly compatibility it must also carry one compact opening-bundle seed:

- protagonist current seat;
- immediate personal pressure;
- first proof surface;
- first resisting actor and why resistance is rational;
- first visible receipt;
- first next gate.

Do not promote a pitch to Firefly-compatible if it only has premise, sector list, and reward promise.

### 3.2 Work Guard

`work_guard.yaml` remains compressed runtime doctrine.

It should not contain the full scene ledger. It should contain:

- 2-4 tracking slots that preserve authority movement;
- 2-3 mandatory scene engines that force proof into visible people/object movement;
- forbidden flattenings that block report-like S4 output;
- evaluation thresholds that keep opening reward inside the opening window.

### 3.3 Phase0 / TR

Phase0 and TR must carry a `scene_native_handoff` equivalent, even if not literally named that in schema.

Required semantics per planning bundle:

- `published_episode_range_hint`: expected 2-6 episode range for this planning bundle;
- `inherited_reward_or_opening_pressure`: what the scene starts with;
- `room_or_surface`: where the pressure becomes visible;
- `human_cost`: whose money, rank, job, responsibility, family standing, deadline, or liability is at stake;
- `resistant_actor_and_reason`: who blocks and why they are rational;
- `protagonist_narrow_action`: the smallest action that only this protagonist can take now;
- `visible_object_or_access_change`: what physically or procedurally changes;
- `authority_conversion`: how money/info/proof becomes access, loyalty, permission, shield, meeting right, or next file;
- `next_named_gate`: the next concrete room, file, person, call, account, badge, table, or meeting.

The important part is not field naming. The important part is that the information survives into S3/S4.

### 3.4 BI

BI may amplify the work, but it must not flatten the Stage 4 handoff.

BI should preserve:

- first 300-500 character role clarity;
- regression/return ignition surface when applicable;
- protagonist weapon in action, not exposition;
- opening proof-to-reward-to-next-gate chain;
- recurring authority ladder;
- anti-flattening rules specific to this work.

BI must not turn the material into a distant encyclopedia of sectors.

## 4. Firefly Compatibility Minimum

A Firefly-compatible material seed must have at least one opening bundle with:

- 3-5 expected published episodes, soft cap 5;
- opening setup that does not pretend to be first cider;
- proof before long family/world explanation;
- rational resistance;
- same-bundle visible receipt;
- money/information converted into authority or access;
- next named gate.

If any of these are missing, do not generate 70 TR blocks to compensate.

Fix the material seed first.

## 4A. B1-B2 Micro-Canary Gate

For new Firefly/S4-bound material, apply:

`material_ssot/00_governance/firefly-b1-b2-micro-canary-before-70-harness-v1.md`

This means the bridge is not proven by a complete sector atlas, a long Phase0 draft, or a 70-block TR attempt.

The bridge is proven when B1-B2, or a compressed EP001 micro-canary, shows:

- current-scene pressure;
- protagonist role clarity;
- first narrow proof;
- rational adult/system resistance;
- visible adult/system behavior cost;
- small access/time/reclassification receipt;
- next named gate.

Until that proof exists, do not call the material Phase0-final, TR70-ready, BI-ready, immediate-use, or range-complete.

## 5. Stop Rules

Stop before Phase0/TR/BI if:

- source use is still raw NAS prose rather than function-level translation;
- there is no work-specific `work_guard` draft;
- `run_work_guard_v1.py` fails or holds;
- WG-V2 manual audit rejects signature scene, protagonist weapon, or reward vector;
- the opening proof window depends on block 7+;
- the material gives sector names but not rooms, blockers, objects, and authority movement;
- the first block can stretch beyond 5 published episodes without proof, receipt, and next gate.

## 6. Non-Goals

This bridge does not:

- replace Firefly S2-S3-S4;
- create a new runtime schema;
- permit donor sentence, dialogue, unique object-chain, or scene-order copying;
- authorize 70-block TR generation from a selection-ready pitch alone;
- turn a smoke seed into production canon.

## 7. Operator Conclusion

The material-side question is no longer just:

`Does this BI/TR/GUARD have commercial logic?`

For writer-facing material, also ask:

`Can S4 write the next scene like a human manuscript without seeing our harness words?`

If the answer is no, the next task is not more blocks.

The next task is a tighter scene-native handoff.

## 8. 3-Pass Self-Audit

Pass 1 - stage fit: PASS. This bridge leaves the official material-side stage order intact and only adds a compatibility requirement for writer-facing handoff.

Pass 2 - anti-overreach: PASS. It is not a schema migration, runtime feature, or automatic validator gate. It is an operator bridge and stop-rule card.

Pass 3 - Firefly fit: PASS_WITH_WATCH. It directly reflects the S4 finding that prose improves when material arrives as people, rooms, objects, rational resistance, visible movement, and next gate rather than broad BI/TR labels. Watch item: future work should promote these semantics into concrete TR/BI fields only after one candidate proves useful.
