# Boundary Reconciliation Memo

- title_id: wuxia__title__gonryun_mahyeop
- scope: ep001-020
- task_type: tranche boundary reconciliation
- status: candidate
- date: 2026-03-20
- input_shards: ep001-010, ep011-020

---

## 1. Arc Continuity Judgment

### Arc 001: sect_reformation_and_power_consolidation (ep001-013)

- **Shard 1 claim**: arc incomplete at ep010, extends into ep011+.
- **Shard 2 claim**: arc completes at ep013 with 2-year timeskip as completion marker.
- **Reconciliation judgment**: **AGREE with shard 2**. Arc 001 spans ep001-013. The shard boundary at ep010/011 is mid-arc, not a structural break. Evidence:
  - ep010-011 are continuous (Paeng Ganghwi conversation carries across without interruption).
  - ep011-012 resolve shard 1's open boundary issues (Paeng Suwon's "one more confirmation" = Heo Jik bimu; Paeng Ganghwi's ki-hyeol fully treated).
  - ep013 scene 035 contains a 2-year timeskip that confirms sect reformation is stable and ongoing, closing the arc's central question ("can Kunlun be reformed?").
- **Sub-phase reconciliation**: merge shard 1's 4 sub-phases with shard 2's 1 sub-phase into a single 5-sub-phase arc:
  1. identity_concealment_and_entry (ep001-002)
  2. martial_arts_restoration_conflict (ep003-005)
  3. resource_acquisition_and_authority (ep005-007)
  4. external_contact_and_reputation_seed (ep007-010)
  5. external_validation_and_alliance (ep011-013)

### Arc 002: elder_rescue_and_elixir_quest (ep013-020+)

- **Shard 2 claim**: arc opens at ep013 scene 036 (Unhu collapse), incomplete at ep020.
- **Reconciliation judgment**: **AGREE**. Arc 002 is well-evidenced but open-ended. The "어라?" cliffhanger at ep020 prevents arc closure within this tranche.
- **Sub-phase structure accepted as-is from shard 2** (4 sub-phases: crisis_and_emergency_treatment, elixir_planning_and_resource_dispatch, protagonist_solo_expedition, elixir_production_and_sect_mobilization).

### Cross-Arc Continuity

Arc 001 and Arc 002 share ep013 as a hinge episode (see section 2). The two arcs are causally linked: the reformed sect's capability (arc 001 output) is the primary tool for the rescue quest (arc 002). This is a **seamless arc transition**, not a break-and-restart.

---

## 2. Hinge Episode Judgment: ep013

**Decision: ep013 IS a hinge episode.**

Evidence:

| criterion | ep013 evidence |
|-----------|---------------|
| closes prior arc | scene 034: Paeng family departs (external validation thread complete). scene 035: 2-year timeskip confirms sect reformation stable |
| opens next arc | scene 036: Unhu collapses — inciting incident for arc 002 |
| contains irreversible state change | 2-year timeskip compresses all remaining reformation work; Unhu's collapse is a one-way event |
| shifts narrative register | comedy-dominant tone (scenes 034-035) → crisis tone (scene 036) within the same episode |

ep013 contains three scenes that span both arcs. For merge purposes:
- scene 034 belongs to arc 001 (Paeng farewell + political calculation = arc 001 closure)
- scene 035 belongs to arc 001 (timeskip + training maturity = arc 001 final confirmation)
- scene 036 belongs to arc 002 (Unhu collapse = arc 002 inciting incident)

The merge artifact must tag ep013 as `hinge` and allow scene-level dual-arc assignment.

---

## 3. Scene-Boundary Conflicts

### 3.1 Shard-Edge Continuity (ep010 → ep011)

- Shard 1 scene 028 ends with "그걸 어찌 알았나?" (open dialogue).
- Shard 2 scene 031 begins with the same dialogue continuing ("뻔히 보이니까요").
- **Conflict: none.** The dialogue is a single continuous scene split by the shard boundary. scene 028 and scene 031 share the same narrative thread (Paeng Ganghwi ki-hyeol discussion).
- **Merge directive**: merge scene 028 (shard 1) and scene 031 (shard 2) into a single scene in the reconciled output. Assign merged scene to ep010-011 range. The exit_state of the merged scene should be: "protagonist reveals diagnostic ability; relationship opens."

### 3.2 Scene ID Continuity

- Shard 1: scenes 001-028 (28 scenes)
- Shard 2: scenes 029-054 (24 scenes, but should become 23 after merging 028+031)
- After merge: 51 scenes across ep001-020.
- **No numbering conflicts.** Shard 2 correctly started at 029.

### 3.3 Other Boundary Issues

No other scene-boundary conflicts found. All `* * *` markers and episode boundaries align between the two shards.

---

## 4. Open Carryover Seeds (Preserved)

All five items below remain open. No evidence of closure within ep001-020.

| # | seed | introduced | status | rationale for keeping open |
|---|------|-----------|--------|---------------------------|
| 1 | **ep020 "어라?"** — Banseondan result unknown | ep020 final line | OPEN | ep020 ends on cliffhanger; no resolution text exists |
| 2 | **운후 회복** — dantian fully restored? martial arts regained? | ep014-015 (temporary fix), ep016-020 (elixir quest) | OPEN | elixir not yet administered; temporary fix is explicitly time-limited (~1 year) |
| 3 | **무림맹 합류** — Murim League revival, protagonist's participation | ep012 (3-year timeline proposed) | OPEN | ~2.8 years elapsed by ep020; no departure from Kunlun for League purposes |
| 4 | **천마신교 내부 변동** — Demon Sect internal chaos, unknown attacker on 쌍각사룡 | ep018 ("교에 무슨 일이 있긴 한가 본데") | OPEN | protagonist explicitly dismissed it; no further information |
| 5 | **백가상단 보답** — Baek family's return gift from 무각사룡 tails | ep019 ("가문을 반석에 올릴" + "은공에게도 선물") | OPEN | no return visit or delivery within ep001-020 |

Additionally, these shard-1 seeds are now **resolved**:

| seed | resolution |
|------|-----------|
| Paeng Suwon's "one more confirmation" | Resolved ep011: Heo Jik bimu proved Kunlun's strength |
| Paeng Ganghwi's succession rivalry (half-brother) | Partially resolved ep012: ki-hyeol healed, but succession subplot still open — downgraded to background seed |
| Protagonist's internal energy imbalance | Resolved ep013 scene 035: 2-year training period allowed rebalancing ("비정상적으로 높았던 내공에 맞춰 다른 부분들을 끌어올릴 수 있었으니") |
| Demon Sect dormancy (elders worry about next Jincheonma) | Not resolved but subsumed into seed #4 (천마신교 내부 변동) — promote to tranche-level open seed |

---

## 5. Merge Directives for Next Run

The next operator should perform a **tranche merge** to produce a unified title-tranche bundle for `wuxia__title__gonryun_mahyeop__ep001-020`. The following directives apply:

### 5.1 Arc Merge

- Produce one unified `arc_cadence__wuxia__gonryun_mahyeop__ep001-020.json` containing:
  - arc_001 (ep001-013, complete, 5 sub-phases)
  - arc_002 (ep013-020+, incomplete, 4 sub-phases)
- Tag ep013 as `hinge: true`.
- Carry all 5 open seeds into the merged arc file.

### 5.2 Scene Merge

- Produce one unified `scene_boundary__wuxia__gonryun_mahyeop__ep001-020.md` containing 51 scenes.
- Merge shard-1 scene 028 + shard-2 scene 031 into one scene (renumber accordingly).
- Final scene count: 51.

### 5.3 Scene Card Merge

- Produce one unified `scene_cards__wuxia__gonryun_mahyeop__ep001-020.json`.
- Concatenate shard-1 cards (9) + shard-2 cards (7) = 16 candidate cards.
- All remain `candidate` status.
- Do not promote any card.

### 5.4 Episode Segmentation Merge

- Produce one unified `episode_segmentation__wuxia__gonryun_mahyeop__ep001-020.md` with all 20 episodes in a single registry table.

### 5.5 Shard Summary Merge

- Produce one unified `shard_summary__wuxia__gonryun_mahyeop__ep001-020.md` that reconciles metrics from both shards.
- Total: 20 episodes, 51 scenes, 2 arcs, 9 sub-phases, 5 open seeds, 0 unresolved boundary conflicts.

### 5.6 Shard Artifact Retention

- Retain original shard artifacts (ep001-010, ep011-020) as historical records.
- Do not delete or overwrite them.
- The merged artifacts supersede them for tranche-level work.

### 5.7 Post-Merge Gate

- After merge, the title-tranche bundle must pass pass1 → pass2 → pass3 → adversarial review before title two (pagong_geomje) starts.
