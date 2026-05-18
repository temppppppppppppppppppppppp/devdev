# International Group EP001-EP003 S4 Compact Writer Seed Audit v1

Date: 2026-05-17
Status: adversarial audit complete
Target: `87_international_group_ep001_003_s4_compact_writer_seed_v1.md`
Work ID: `chaebol3_sector_rotation_successor`
Issue: #157

## 0. Verdict

`PASS_WITH_WATCH`

87 is usable as a compact writer seed for an EP001-EP003 S4 canary.

It does not authorize:

- production manuscript;
- Firefly DB/project mutation;
- B11-B20 expansion;
- production TR70;
- production BI.

It authorizes:

- one research-only S4 canary using section 4 or one of the section 5 dispatches;
- director readback after output.

## 1. Audit Standard

The seed must answer the user's core concern:

`Can our material make S4 write like a human scene, not like AI planning prose?`

Audit gates:

- compact enough for writer handoff;
- no raw planning labels in the payload;
- current-scene pressure before business exposition;
- visible adult behavior cost;
- no one-document miracle;
- no source contamination;
- no over-clean proof ladder;
- enough friction to prevent AI-slop smoothness.

## 2. Pass 1 - Writer-Facing Compression

Verdict: `PASS`

Evidence:

- Section 4 is a single pasteable payload.
- Section 5 gives one-episode dispatches.
- The payload uses rooms, objects, and adult motives instead of block logic.
- It blocks production terms from the scene.

Watch:

- Do not pass sections 0-3 or 6-7 to S4.
- If using section 5, pass only one dispatch plus necessary character names.

## 3. Pass 2 - Label Leakage

Verdict: `PASS_WITH_WATCH`

Evidence:

- The writer-facing payload does not mention TR, BI, block, audit, canary, source safety, or receipt.
- It does include `초반 3화`, `1화`, `2화`, `3화`, which are writer-facing and acceptable.
- The dispatches say `Write EP001 only`, etc. That is operational but not manuscript-visible.

Watch:

- If this becomes a Firefly prompt, keep "do not expose production words" but avoid overloading the prompt with evaluation language.

## 4. Pass 3 - Opening Human Attachment

Verdict: `PASS`

Evidence:

- 문도윤 starts as `문준하 아들`, folder courier, dead heir's son, wrong wrist/date body.
- The seed asks for sensory rupture: ink, rubber, phone, date stamp.
- The social wound appears before LC mechanics.

Watch:

- S4 output must not turn 문도윤 into a calm consultant in the first paragraph.

## 5. Pass 4 - Adult Behavior Cost

Verdict: `PASS`

Evidence:

- 박윤재 moves for procedure/meeting accident.
- 김태완 moves for bank responsibility/superior blame.
- 문태섭 moves only under founder-authority condition.
- 문성필 keeps resisting for sale momentum.
- 한기철 gives hostile facts, not warmth.

This prevents adults from becoming praise machines.

Watch:

- The prose must show these costs through behavior, not exposition.

## 6. Pass 5 - One-Document Miracle Guard

Verdict: `PASS`

Evidence:

- Section 4 explicitly says 문도윤 is not saving the group.
- The first 3 episodes only open: folder route, 72-hour condition, telex access, Busan payroll evidence, crisis-cell note.
- It bans "LC 한 장으로 그룹 구하기."

Watch:

- If S4 writes "모든 것이 바뀌었다" too early, reject and patch.

## 7. Pass 6 - Friction / Anti-Slop

Verdict: `PASS_WITH_WATCH`

Evidence:

- The seed repeatedly demands distrust, conditions, and self-protection.
- It asks that adults keep blocking instead of becoming impressed.
- It includes hostile Busan facts and failure penalties.

Watch:

- The payload is still quite clear and orderly. S4 may produce too-clean scenes if the generation prompt asks for full compliance.
- The canary should be judged by whether characters resist in their own words and rhythms, not by whether all beats are checked off.

## 8. Pass 7 - Source Safety

Verdict: `PASS`

Evidence:

- Uses fictional names: 해문그룹, 문도윤, 문태섭, 문성필, 박윤재, 김태완, 한기철.
- Real history is only broad pressure: 1985 collapse, creditor bank, export/Busan pressure.
- No donor prose, dialogue, or distinctive donor scene chain is present.
- Famous-person/global gates are banned from EP001-EP003.

Watch:

- Later sector gates need another audit before real-person names enter.

## 9. Pass 8 - S4 Canopy / Too Much Hand-Holding

Verdict: `PASS_WITH_WATCH`

The seed is intentionally more directive than natural prose because it is a canary seed.

Potential risk:

- The seed names endings very explicitly, so S4 may write toward visible objects but miss local rhythm.

Mitigation:

- Use the one-episode dispatches for actual canary.
- Ask for one episode at a time.
- Audit line-level human resistance after generation.

## 10. Required Next Step

Recommended next unit:

`Run a research-only EP001 S4 canary from 87 section 5.`

Minimum readback:

- first 300-500 character attachment;
- object movement;
- adult behavior cost;
- no LC miracle;
- no production language;
- next door.

Allowed fallback:

- prepare a Firefly handoff file without running generation, if the operator wants to keep all mutation out of Firefly.

Do not do next:

- generate B11-B20;
- production TR70;
- production BI;
- Firefly DB/project mutation.
