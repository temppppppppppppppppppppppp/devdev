# Firefly Material-to-S4 Context Bridge Harness v1

Date: 2026-05-17
Status: governance note, research-derived, not production prompt
Source work: `chaebol3_sector_rotation_successor`
Issue: #157
Proof surfaces: `136/137`, `138/139`

## 0. Boundary

This is a material-side governance note.

It does not authorize:

- changing the production Firefly S4 prompt;
- Firefly DB/project mutation;
- `manuscript save`;
- production manuscript save;
- B11-B20;
- TR70;
- BI;
- work_guard publication.

It defines how material-side research may be converted into Firefly S4 Writer Context for future file-only tests.

## 0A. Immediate Answer For Future Operators

Do not create BI/TR and S2-S3-S4 at the same time.

Correct order:

1. First make the human story plan.
2. Then prove that the first episodes can become living prose.
3. Then translate the proven plan into BI/TR containers.
4. Then run Firefly's mainline: S2 arc, S3 blueprint, S4 manuscript.

BI/TR is a transport layer for Firefly. It is not the writer-facing plan.

For the current chaebol regression work, the human-facing planning unit is:

`독식형 15화 실물맛 기획안`

Do not call the writer-facing unit `context fill`, `payload`, `proof ladder`, `70-block plan`, or `file access plan`.

Detailed 70-block TR is blocked until the opening taste has passed a prose test. A thin later 70-slot map may be allowed only as a Firefly transport wrapper after the 15-episode taste plan is stable.

## 1. Core Rule

Do not feed S4 broad material philosophy.

For old technical dryruns, a concrete writer context was phrased as:

`room + object + practical cost + resisting actor + smaller permission + visible objection + final object/access + next gate`

That wording is now deprecated for writer-facing material.

For new or touched writer-facing material, translate the same need into PD/story language:

`where the scene happens + what money/person/status is at stake + who still treats the protagonist as too young + what the protagonist moves + whose attitude changes + what larger adult world opens`

The reusable story movement is:

`adult dismissal -> money/person move -> visible result -> changed attitude -> larger board`

This rule keeps the mainline as `S2 -> S3 -> S4`.
It does not add a new stage.

## 1A. Writer-Facing Language Firewall

For any new or touched writer-facing packet, episode note, style packet, or prose seed, reject the artifact if it uses production-machine wording as story language.

Blocked in writer-facing material:

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

Allowed story translations:

- `전담팀이 붙는다`
- `할아버지가 웃다가 멈춘다`
- `어른들이 더 이상 도련님 장난이라고 못 한다`
- `팀장이 남기로 한다`
- `돈의 크기 때문에 회의실 말투가 바뀐다`
- `다음 해외 일정이 열린다`
- `사촌 라인이 도윤을 귀찮은 학생이 아니라 위험한 손자로 본다`

Legacy audit files may mention blocked terms as examples. New story-facing packets may not.

## 2. Required Material Fields

Before asking Stage 4 to draft prose, the material unit must answer in story language:

| Field | What it must contain |
|---|---|
| `where_are_we` | the room, table, phone, office, car, school desk, trading room, or family space the reader can picture |
| `what_is_at_stake` | money, person, schedule, family standing, team loyalty, grandfather's attention, or public face |
| `who_underestimates_him` | who still treats the protagonist as too young, spoiled, ornamental, or temporary |
| `what_doyun_moves` | the money, person, call, schedule, bet, bonus, meeting, or decision Doyun changes |
| `who_changes_tone` | whose attitude shifts on page because the event is now too real to laugh off |
| `what_world_gets_bigger` | the larger adult board opened by the ending: team, family, overseas schedule, market, affiliate, or rival line |

Reject the unit if the answer is:

- "authority rises";
- "trust is earned";
- "competence is proved";
- "reader gets reward";
- "next sector opens."

Those are audit summaries, not story material.

## 3. S4 Context Mapping

Map the material fields into Firefly's existing S4 Writer Context:

| S4 field | Source |
|---|---|
| `work_frame` | `where_are_we` + what is happening there |
| `live_transaction` | `what_is_at_stake` + `what_doyun_moves` |
| `priced_loss` | money, schedule, person, family standing, or reputation translated into concrete cost |
| `resistant_witness` | `who_underestimates_him` + why that person cannot agree too easily |
| `position_change` | whose tone, seating, schedule, assignment, money, or attention changes |
| `behavior_ladder` | 3-5 visible actions, not explanations |
| `reader_visible_change` | changed money, people, family standing, or adult treatment |
| `ending_and_larger_board` | the ending beat + the larger adult world it opens |

## 4. Writer-Visible Conversion

The writer-visible note must strip labels.

Allowed:

```text
Use the factory quality table. Keep the defect tray, two sample shoes, chalkboard, spec sheet, glue powder, and production schedule visible.
The quality lead protects shipment credibility; the factory manager protects blame, wasted labor, and pay timing.
Doyun must ask for less than a product win: cut the shiny variant, keep the plain basic line, and attach payment only to passed sample count.
The objection must remain on the board or spec sheet.
End with the plain sample in the box, shiny sample out of the box, and a buyer or school desk becoming the next room.
```

Forbidden:

```text
Show the reward ladder and translate the protected asset into a reader receipt.
```

Reason:

The allowed note can become behavior.
The forbidden note becomes harness prose.

## 5. Required Post-Prose Audit

Every file-only prose dryrun using this bridge must audit:

- Did the room/object appear before meaning?
- Did practical resistance appear before curiosity or praise?
- Did the protagonist ask for less than obvious victory?
- Did an objection remain visible?
- Did the final beat visibly change money, people, schedule, family standing, or adult treatment?
- Did the next room or adult board grow from what happened in the episode?
- Did any line explain the mechanism instead of showing behavior?
- Did any production label leak into prose?
- Is the output still `draft_not_db_saved`?

If mechanism-explaining lines appear, patch them into hand, pen, box, phone, card, clock, shelf, board, door, or body behavior.

## 6. Proof Surfaces

| Proof | Surface | Result |
|---|---|---|
| `136/137` | buyer desk | phone, return ledger, sample box, memo; passed with watch |
| `138/139` | product-hand | defect tray, shoes, spec sheet, chalkboard, delivery label; passed with watch |

The bridge is stable enough for future file-only research tests.

It is not yet a production Firefly prompt change.

## 7. Next Governance Decision

Before production integration:

1. Open a separate Firefly-side implementation issue if the bridge should affect actual S4 context assembly.
2. Keep all tests file-only until that issue is scoped.
3. Do not merge this into BI/TR generation as broad labels.
4. Preserve line-level post-prose audit as mandatory.
