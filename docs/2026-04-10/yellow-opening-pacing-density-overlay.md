# YELLOW Opening Pacing Density Overlay

Date: 2026-04-10
Status: active operator overlay
Scope: `opening pacing triage = YELLOW` queue only

Operator note:

- `jaebeol3se_loss_line` was later promoted out of the active YELLOW queue by `docs/2026-04-10/jaebeol3se_loss_line_forensic_spot_audit.md`
- references to that work below are retained as historical pre-override evidence
- `chaebol_ent_empire` later exited the active YELLOW queue via the targeted repair recorded in [chaebol_ent_empire_opening_signboard_compression_repair_note.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-10/chaebol_ent_empire_opening_signboard_compression_repair_note.md)
- references to that work below are retained as historical pre-repair density evidence
- `pantech_cyworld_reborn` later exited the active YELLOW queue via the bounded repair recorded in [pantech_cyworld_reborn_cadence_and_reevaluation_surface_repair_note.md](/C:/Users/wjjo/Desktop/글도비/docs/2026-04-10/pantech_cyworld_reborn_cadence_and_reevaluation_surface_repair_note.md)
- references to that work below are retained as historical pre-repair density evidence

Primary question:

- among the current `YELLOW` queue, which pairs are merely pacing-late,
- and which pairs are also thin enough to become future `RED` candidates once the `2~6 episode bundle density` law closes?

This document does **not** upgrade the density law to a hard gate yet.
It is an operator overlay for ordering the manual re-audit queue.

---

## 1. Reading Rule

Use three layers separately:

1. `opening pacing triage`
2. `opening-local bundle density proxy`
3. `future empirical density law` from the bounded corpus pack

Current density proxy inputs:

- opening average `bundle_size`
- opening minimum `bundle_size`
- opening average reward chars
- current pacing trigger

Important:

- `bundle_size` is still a material-side proxy, not a direct downstream episode-text equivalent
- so this document may raise `RED candidate` suspicion,
- but it does not by itself archive a pair

---

## 2. Current YELLOW Queue

### 2.1 Raw overlay

| work_id | opening avg bundle chars | opening min bundle chars | opening avg reward chars | pacing trigger | density read |
| --- | --- | --- | --- | --- | --- |
| `jangyeongshil_industrial_revolution` | `408.7` | `224` | `75.6` | signboard `B10` | thin |
| `pantech_cyworld_reborn` | `561.4` | `434` | `103.7` | reevaluation `B10` | thin-low |
| `chaebol_ent_empire` | `687.7` | `495` | `167.2` | signboard `B09` | mid |
| `office_checkup_next_day` | `1046.1` | `834` | `172.4` | office battlefield overstay + reevaluation `B08` | dense |
| `smart_new_hire` | `975.0` | `771` | `133.7` | office battlefield overstay + reevaluation missing | dense |
| `jaebeol3se_loss_line` | `947.3` | `351` | `205.3` | ticket `B09` | dense but unstable |

Reference anchors:

- `chaebol_allowance_zero`:
  - opening avg bundle chars `640.2`
  - opening min bundle chars `548`
  - opening avg reward chars `103.2`
  - current pacing archive anchor = `RED`
- `defense_defect_engineer`:
  - opening avg bundle chars `847.7`
  - opening min bundle chars `759`
  - opening avg reward chars `181.5`
  - current pacing keep anchor = `GREEN`
- `투자물_골든_카나리아 테스트_canonical_v1`:
  - opening avg bundle chars `932.0`
  - opening min bundle chars `483`
  - opening avg reward chars `214.9`
  - current pacing keep anchor = `GREEN`

### 2.2 Immediate observation

The current `YELLOW` queue is not one family.

It splits into three groups:

1. `thin + late`
2. `dense but pacing-late`
3. `dense but structurally unstable`

---

## 3. Grouping

### 3.1 Thin + late

#### `jangyeongshil_industrial_revolution`

- opening avg bundle chars `408.7`
- opening min bundle chars `224`
- opening avg reward chars `75.6`
- signboard `B10`

Operator reading:

- this is the strongest current `future RED candidate` inside the YELLOW queue
- it is not just late
- it is also materially thin in the opening bundle proxy

#### `pantech_cyworld_reborn`

- opening avg bundle chars `561.4`
- opening min bundle chars `434`
- opening avg reward chars `103.7`
- reevaluation `B10`

Operator reading:

- thinner than the current keep anchors
- not as severe as `jangyeongshil`
- but if empirical density law hardens, this is a plausible `RED candidate`
- this is now historical pre-repair reading only; the pair has since exited the active opening `YELLOW` queue

### 3.2 Mid density + late signboard

#### `chaebol_ent_empire`

- opening avg bundle chars `687.7`
- opening min bundle chars `495`
- opening avg reward chars `167.2`
- signboard `B09`

Operator reading:

- this currently reads more like `repair-late`, not `discard-thin`
- density alone does not make it the first archive candidate
- this is now historical pre-repair reading only; the pair has since exited the active opening `YELLOW` queue

### 3.3 Dense but pacing-late

#### `office_checkup_next_day`

- opening avg bundle chars `1046.1`
- opening min bundle chars `834`
- opening avg reward chars `172.4`
- office battlefield overstay
- reevaluation `B08`

Operator reading:

- clearly not thin
- if this pair goes `RED`, it would be because pacing law strengthens, not because density collapses
- this is a `repair-first` shape, not an `archive-first` shape

#### `smart_new_hire`

- opening avg bundle chars `975.0`
- opening min bundle chars `771`
- opening avg reward chars `133.7`
- office battlefield overstay
- reevaluation missing

Operator reading:

- again, not thin
- the problem is battlefield residence / cadence, not bundle emptiness
- this is also `repair-first`

### 3.4 Dense but structurally unstable

#### `jaebeol3se_loss_line`

- opening avg bundle chars `947.3`
- opening min bundle chars `351`
- opening avg reward chars `205.3`
- ticket `B09`
- other current hard-gate failures are noisy and meta-heavy

Operator reading:

- the opening is not thin in gross volume
- but it is unstable in another way:
  - late ticket
  - noisy hard-gate failures
  - local variance spike from thin early blocks to swollen later blocks

This is not the first density-RED candidate.
It is a `manual forensic re-audit` candidate.

---

## 4. Provisional Order

If we are asking:

`which YELLOW might actually be RED once 2~6 bundle density becomes a harder law?`

Current order is:

1. `jangyeongshil_industrial_revolution`
2. `chaebol_ent_empire`
3. `jaebeol3se_loss_line`
4. `office_checkup_next_day`
5. `smart_new_hire`
6. `pantech_cyworld_reborn`

Spot-audit override:

- `pantech_cyworld_reborn` is removed from immediate kill-first review by `docs/2026-04-10/yellow-kill-first-spot-audit.md`

If we are asking:

`which YELLOW should be repaired first because they are dense enough to be worth saving?`

Current order is:

1. `office_checkup_next_day`
2. `smart_new_hire`
3. `chaebol_ent_empire`
4. `pantech_cyworld_reborn`
5. `jaebeol3se_loss_line`
6. `jangyeongshil_industrial_revolution`

---

## 5. Immediate Operator Rule

Until the empirical density pack closes:

- `jangyeongshil_industrial_revolution` is `RED candidate` territory
- `pantech_cyworld_reborn` no longer stays in the active `YELLOW` queue after the same-day bounded repair; keep the density read only as historical pre-repair evidence
- `office_checkup_next_day` and `smart_new_hire` are `repair-first YELLOW`
- `jaebeol3se_loss_line` is `forensic re-audit YELLOW`
- `chaebol_ent_empire` no longer stays in the active `YELLOW` queue after the same-day targeted repair; keep the density read only as historical pre-repair evidence

This lets us narrow the next expensive manual audit wave without pretending the density law is already closed.

---

## 6. Working Disposition

Current cost-first split:

- `kill-first review / RED candidate`
  - `jangyeongshil_industrial_revolution`
- `repair-first YELLOW`
  - `office_checkup_next_day`
  - `smart_new_hire`
- `forensic re-audit`
  - `jaebeol3se_loss_line`
- historical completed repair archive
  - `chaebol_ent_empire`
  - `pantech_cyworld_reborn`

Operator rule:

- `kill-first review`에는 repair 예산을 먼저 넣지 않는다.
- `repair-first YELLOW`만 salvage budget 후보로 본다.
- `forensic re-audit`는 원인 판독이 끝나기 전까지 repair / discard를 모두 보류한다.
- `docs/2026-04-10/yellow-kill-first-spot-audit.md` 기준으로 `pantech_cyworld_reborn`은 kill-first review에서 해제한다.
- `docs/2026-04-10/jaebeol3se_loss_line_forensic_spot_audit.md` 기준으로 `jaebeol3se_loss_line`은 active YELLOW queue에서 제거되고 `RED`로 승격된다.
