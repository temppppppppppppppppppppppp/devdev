# Pitch Philosophy

Date: 2026-04-06
Status: active
Scope: canonical philosophy, selection gate, and minimum contract for `material_ssot/20_pitch`

## 1. Role

- bridge `research -> pitch -> Stage0 preprocess -> Phase0 design`
- decide whether a work deserves a real `work_id` and Stage 0 spend before expansion
- freeze work-level pitch truth before Phase0 expands it into block architecture
- give humans and external models one bounded planning unit with stable authority

Important operational note:

- a legacy file under `intake/legacy_import/` or an old candidate under any folder does not become an active candidate just because it exists on disk
- active candidate status now comes from philosophy alignment first, then selection, then handoff
- current operator lane excludes female-protagonist candidates from active promotion
- female-protagonist ideas can remain as archived material, but they do not enter the active `synthesis -> canon -> Stage0/Phase0` route

## 2. Default Operating Mode

- default operating mode is `single`
- build or revise one work-level pitch unit at a time
- parallel ideation is burst-only and never changes final authority away from the selected pitch file
- no work should be promoted into Stage 0 or Phase0 just because it has a flashy premise
- active fresh-candidate selection assumes a male protagonist
- large downstream artifacts must not be written in one huge overwrite just because the target file is singular
- if the next unit is `Phase0`, `TR`, or `BI`, keep the current bounded unit as the save unit and preserve parseable JSON after each save step

Authority note:

- planning semantics come from `docs/blockguide/treatment-planning-harness.md` and `docs/wuxguide/wuxia-planning-harness.md`
- operator mode semantics come from `docs/implementation/single-ide-default-policy.md`
- this document defines the pitch-stage bridge and selection gate, not the downstream TR or BI schema
- deeper house-law references:
  - `material_ssot/20_pitch/protagonist-first-constitution.md`
  - `material_ssot/20_pitch/pitch-selection-checklist.md`
  - `material_ssot/20_pitch/work-guard-translation-map.md`
- downstream work-guard operator companions:
  - `docs/2026-04-06/work-guard-validator-checklist-spec.md`
  - `docs/2026-04-06/wg-v2-freeze-checklist.md`
  - `docs/2026-04-06/wg-v3-drift-audit-card.md`
- use the dated companion docs for translation/freeze/drift operations, while keeping philosophy authority in `material_ssot/20_pitch`

## 3. Our Philosophy

### 3.1 Protagonist-First, `둥기둥기 first`

- the first question is not "is the world interesting?" but "does the story reward the protagonist in a way the reader can feel?"
- meaningful protagonist success must create visible reward, recognition, protection, or a larger gate
- especially in episodes 1 to 3, `success -> pure punishment spiral` is forbidden as the dominant reward vector
- "you were not expelled", "you are under suspicion now", or "people still hate you but maybe later" is not a strong enough first reward

### 3.2 Self-Interest First

- the protagonist must want something concrete now
- the protagonist must want something bigger later
- actions must produce visible gain, avoid visible loss, or seize leverage for the next move
- "good person" is not a sufficient engine

### 3.3 Controllable Growth Resource

- every pitch needs a controllable growth resource
- the resource can be cashflow, approval rights, permit codes, cases, fans, standards, project ownership, realm progress, manual access, faction protection, or operating rights
- if the story cannot name the resource, it is not ready for Phase0

### 3.4 Visible Reward Tokens

- rewards must land as things the reader can count or feel
- for `blockguide`, preferred tokens are `cashflow`, `CC line`, `approval right`, `permit hold`, `project ownership`, `standard clause`, `signature right`, `seat at the table`
- for `wuxguide`, preferred tokens are `realm breakthrough`, `manual access`, `treasure`, `elder protection`, `faction seat`, `jianghu reputation`, `inheritance clue`
- the first block reward must open the next block instead of ending the engine

### 3.5 Information Gap Before Force

- the protagonist needs a real information gap, not only confidence
- competence should appear as a process: `detect -> intervene -> prove -> cash out`
- raw talent without public proof scenes is not enough

### 3.6 Rational Opposition

- opponents are not cartoon villains
- old winners should be treated as people who had the right answer for the previous era
- pressure should come from incentives, structure, timing, and risk, not only emotion

### 3.7 Domain Truth Over Vibes

- the family promise must be paid in concrete domain truth
- no vibe-only victory
- no abstract "power struggle" when the real promise is permits, audits, standards, surgery, faction rank, manuals, logistics, or contracts

### 3.8 Repeatable Engine

- a good pitch has a repeatable loop, not one lucky reversal
- preferred form: `hidden bottleneck -> intervention -> proof -> reward -> next gate`
- if the reader cannot see how block 1 opens block 2, the pitch is not ready

### 3.9 Pain Budget And Recovery Vector

- pain is allowed
- humiliation is allowed
- defeat is allowed
- but pain must stay growth-bearing, protective, or upward-pointing
- the opening cannot teach the reader that helping, winning, or proving oneself mostly leads to punishment

### 3.10 Contamination Guard

- define what the work must not drift into
- ban false substitutes such as romance filler, family melodrama, vibe-only victory, punishment pump, or fake domain shortcuts when they break the family promise

## 4. Pre-Canon Selection Gate

A fresh idea is allowed into active candidate status only if it can answer all of the following in plain language:

- what does the protagonist want right now
- what does the protagonist want later
- what controllable growth resource is being accumulated
- what information gap only the protagonist can exploit
- what the opening spike is
- what the first earned success is
- what the first visible reward is
- how that first reward opens the next gate
- what the work must not drift into

Hard reject examples:

- female protagonist candidate under the current operator lane
- first success yields mostly suspicion, probation, surveillance, exile threat, or "at least you survived"
- the engine depends on the protagonist being nice, patient, sacrificial, or endlessly misunderstood without leverage
- the reward is only emotional validation with no visible power token
- the domain materials stay generic enough to swap with any other office or jianghu story
- the reader promise centers theme, atmosphere, or setting more than protagonist ascent

## 5. Minimum Pitch Contract

Every fresh canonical pitch, and every fresh intake-batch entry that wants selection consideration, should explicitly lock the following:

- `one_line_premise`
- `why_now`
- `family`
- `primary_profile`
- `secondary_profile` when needed
- `protagonist_position`
- `long_term_goal`
- `short_term_goal`
- `controllable_growth_resource`
- `information_gap`
- `competence_process`
- `core_engine`
- `major_materials`
- `opening_spike`
- `episodes_1_to_3_impact`
- `first_block_problem`
- `first_block_reward`
- `opening_reward_vector`
- `repeatable_loop`
- `promise_to_reader`
- `contamination_guard`
- `phase0_handoff_note`

## 6. Hard Gate

Do not promote a pitch as canonical if any of these are missing or vague:

- `long_term_goal`
- `short_term_goal`
- `controllable_growth_resource`
- `information_gap`
- `competence_process`
- `major_materials`
- `opening_spike`
- `first_block_reward`
- `opening_reward_vector`
- `promise_to_reader`

Reject or hold the pitch if:

- the work depends on vibes instead of a controllable resource
- the protagonist wins because opponents are stupid
- the domain materials stay abstract where the family promise needs concrete truth
- the first spike comes too late to convert the reader
- the first visible reward is only survival, probation, or "not expelled"
- the opening asks the reader to endure pain first and trust that compensation may arrive much later
- the pitch cannot explain how block 1 opens block 2

## 7. Output Shapes

Canonical work-level pitch files under `canon/` should use this shape:

1. `Authority`
2. `Pitch Truth`
3. `Early Conversion`
4. `Phase0 Handoff Note`

Fresh intake-batch files under `intake/` should use this shape:

1. `Candidate Frame`
2. `Pitch Truth`
3. `Early Conversion`
4. `Why It Passes Philosophy`
5. `Phase0 Handoff Note`

The file should be compact enough for operator handoff, but complete enough to make selection judgment possible.

## 8. Large Artifact Write Discipline

- this pitch stage may hand off to large live JSON artifacts, but handoff size does not authorize large single-write behavior
- if the output file is operationally large, write by the current bounded execution unit and keep the on-disk file parseable between saves
- do not ask an external model to generate or overwrite a full `70-block TR` or similarly large live artifact in one shot
- for `TR`, follow family production rules first
- for `BI`, prefer schema-valid incremental saves over monolithic replacement
- if write stability and generation density conflict, stabilize the save path first and continue in smaller units
