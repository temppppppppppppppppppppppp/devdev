# Pitch Philosophy

Date: 2026-04-05
Status: active
Scope: canonical philosophy and minimum contract for `material_ssot/20_pitch`

## 1. Role

- bridge `research -> pitch -> Stage0 preprocess -> Phase0 design`
- freeze work-level pitch truth before Phase0 expands it into block architecture
- give humans and external models one bounded planning unit with stable authority

## 2. Default Operating Mode

- default operating mode is `single`
- build or revise one work-level pitch unit at a time
- if handing a pitch task to Opus or another external model, pass exactly one `work_id`, one current authority bundle, and one clear output target
- parallel ideation is burst-only and never changes final authority away from the canonical pitch file
- large downstream artifacts must not be written in one huge overwrite just because the target file is singular
- if the next unit is `Phase0`, `TR`, or `BI`, keep the current bounded unit as the save unit and preserve parseable JSON after each save step

Authority note:

- planning semantics come from `docs/blockguide/treatment-planning-harness.md`
- operator mode semantics come from `docs/implementation/single-ide-default-policy.md`
- this document defines the pitch-stage bridge, not the downstream TR or BI schema

## 3. Core Philosophy

### 3.1 Self-Interest First

- the protagonist must want something concrete now
- the protagonist must want something bigger later
- actions must produce visible gain, avoid visible loss, or seize leverage for the next move
- "good person" is not a sufficient engine

### 3.2 Measurable Growth Resource

- every pitch needs a controllable growth resource
- the resource can be cashflow, authority, information, cases, fans, contracts, standards, or operating rights
- if the story cannot name the resource, it is not ready for Phase0

### 3.3 Information Asymmetry Before Force

- the protagonist needs a real information gap, not only confidence
- competence should appear as a process: detect -> intervene -> prove -> get paid
- raw talent without proof scenes is not enough

### 3.4 Rational Opposition

- opponents are not cartoon villains
- old winners should be treated as people who had the right answer for the previous era
- pressure should come from incentives, structure, timing, and risk, not only emotion

### 3.5 Early Reader Conversion

- the pitch must promise a visible opening spike
- episodes 1 to 3 need a felt reward, authority move, or public proof
- the first block reward must open the next block instead of ending the engine

### 3.6 Repeatable Loop

- a good pitch has a repeatable loop, not one lucky reversal
- preferred form: hidden bottleneck -> intervention -> reward -> next gate
- each reward should land in `cashflow`, `people`, or `rules`

### 3.7 Contamination Guard

- define what the work must not drift into
- ban false substitutes such as romance filler, family melodrama, vibe-only victory, or fake domain shortcuts when they break the family promise

## 4. Minimum Pitch Contract

Every canonical pitch should explicitly lock the following:

- `one_line_premise`
- `why_now`
- `family`
- `primary_profile`
- `secondary_profile` when needed
- `protagonist_position`
- `long_term_goal`
- `short_term_goal`
- `information_gap`
- `competence_process`
- `core_engine`
- `major_materials`
- `opening_spike`
- `episodes_1_to_3_impact`
- `first_block_problem`
- `first_block_reward`
- `repeatable_loop`
- `promise_to_reader`
- `contamination_guard`
- `phase0_handoff_note`

## 5. Hard Gate

Do not promote a pitch as canonical if any of these are missing or vague:

- `long_term_goal`
- `short_term_goal`
- `information_gap`
- `competence_process`
- `major_materials`
- `opening_spike`
- `first_block_reward`
- `promise_to_reader`

Reject or hold the pitch if:

- the work depends on vibes instead of a controllable resource
- the protagonist wins because opponents are stupid
- the domain materials stay abstract where the family promise needs concrete truth
- the first spike comes too late to convert the reader
- the pitch cannot explain how block 1 opens block 2

## 6. Canon Output Shape

Use this document shape for canonical work-level pitch files under `canon/`:

1. `Authority`
2. `Pitch Truth`
3. `Early Conversion`
4. `Phase0 Handoff Note`

The file should be compact enough for operator handoff, but complete enough to replace bootstrap notes.

## 7. Large Artifact Write Discipline

- this pitch stage may hand off to large live JSON artifacts, but handoff size does not authorize large single-write behavior
- if the output file is operationally large, write by the current bounded execution unit and keep the on-disk file parseable between saves
- do not ask an external model to generate or overwrite a full `70-block TR` or similarly large live artifact in one shot
- for `TR`, follow family production rules first; for `BI`, prefer schema-valid incremental saves over monolithic replacement
- if write stability and generation density conflict, stabilize the save path first and continue in smaller units
