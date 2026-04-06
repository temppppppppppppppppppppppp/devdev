# 01 Golden Stage2 Lane 1: Artifact Truth

Date: 2026-04-06
Lane: artifact truth
Status: lane survey complete
Source order: `docs/2026-04-06/01_golden_stage2_p0_p3_full_survey_order.md`

## 1. Coverage

Inspected sinks:

- `plans/arcs/arc_001.txt` through `arc_004.txt` (full read, byte-level UTF-8)
- `logs/artifacts/stage2/arc_001/attempt_01/final_arc__creative.json` (accepted)
- `logs/artifacts/stage2/arc_002/attempt_01/final_arc__creative.json` (accepted)
- `logs/artifacts/stage2/arc_003/attempt_01/final_arc__balanced.json` (accepted)
- `logs/artifacts/stage2/arc_004/attempt_02/final_arc__creative.json` (accepted)
- `logs/artifacts/stage2/arc_004/attempt_01/rejected_arc__conservative.json` (rejected, cross-reference only)

Fields inspected per artifact:

- `state_constraints` (`arc_start_state`, `arc_end_state`, `investment_calc`, `items_acquired`, `items_consumed`, `power_changes`, `protagonist_items`, `relationship_changes`, `foreshadowings`, `continuity_checkpoints`)
- `joint_docs` (`final_location`, `physical_inventory`, `world_joint`)
- `state_changes` (`major_items`, `npc_introductions`, `relationship_changes`, `timeline`)
- `beat_sequence`
- `tactical_doc`

## 2. Findings

### F-1. `internal_energy` field survives in accepted artifacts (P1-candidate support)

The survey order's P1-candidate hypothesis is **confirmed from the artifact side**.

| Arc | Artifact | `arc_start_state.internal_energy` | `arc_end_state.internal_energy` |
|-----|----------|-----------------------------------|---------------------------------|
| 1   | accepted creative | `0` | `0` |
| 2   | accepted creative | absent | absent |
| 3   | accepted balanced | `100` | `100` |
| 4   | accepted creative (attempt_02) | `100` | `100` |
| 4   | rejected conservative (attempt_01) | absent | absent |

Evidence:

- Arc 1 artifact: `final_arc__creative.json` lines 307, 318
- Arc 3 artifact: `final_arc__balanced.json` lines 262, 277
- Arc 4 accepted artifact: `final_arc__creative.json` (attempt_02) lines 274, 291

If `ui_events.jsonl` records that genre-contract repair removed `internal_energy` for Arc 1, 3, and 4, then the saved artifacts **disagree**: the field still exists and carries values. This is a saved-contract mismatch, not wording-only.

Additionally, the values themselves are inconsistent: Arc 1 has `0`, while Arc 3 and Arc 4 have `100`, with no explicit narrative justification for the difference.

### F-2. `power_changes` carryover chain is broken across arcs

| Arc | `start_power` | `end_power` | Expected `start_power` (= prev arc `end_power`) |
|-----|---------------|-------------|--------------------------------------------------|
| 1   | 5  | 15 | n/a (first arc) |
| 2   | 10 | 25 | 15 |
| 3   | 10 | 25 | 25 |
| 4 (accepted) | 30 | 45 | 25 |

Every arc-to-arc transition has a start/end mismatch:

- Arc 1 ends at 15, but Arc 2 starts at 10 (delta: -5)
- Arc 2 ends at 25, but Arc 3 starts at 10 (delta: -15)
- Arc 3 ends at 25, but Arc 4 starts at 30 (delta: +5)

This is a state drift in the power scale. The numbers do not form a consistent chain. Each artifact appears to have been generated independently without reading the prior arc's `end_power`.

Severity hint: P2-class. The numeric spine for capital/equipment/items/location chains cleanly, but the power scale is decoupled. If `power_changes` is consumed by downstream stages, this is a silent logic error.

### F-3. `npc_introductions` duplicate for 박성호

- Arc 1 artifact: `state_changes.npc_introductions` records 박성호 at ep 3
- Arc 2 artifact: `state_changes.npc_introductions` records 박성호 at ep 7

The NPC is introduced twice across artifacts. If downstream consumers build a master NPC roster by aggregating `npc_introductions`, 박성호 will appear duplicated with conflicting introduction episodes.

Severity hint: P3-class. No data loss; downstream dedup is trivial.

### F-4. Duplicate/null-episode `relationship_changes` entries

- Arc 2 `state_changes.relationship_changes`: two entries for 박성호 — one with `episode: 10`, one with `episode: null` and empty `justification`/`trigger` fields
- Rejected Arc 4 `state_changes.relationship_changes`: same pattern — two entries for 박성호, one with `episode: 17`, one with `episode: null`

The null-episode entries appear to be malformed duplicates. They carry different `from`/`to` wording from the primary entries, creating ambiguity about which version is authoritative.

Severity hint: P3-class. Does not corrupt the primary entry, but adds noise for downstream relationship-tracking consumers.

### F-5. Accepted Arc 4 vs rejected Arc 4: investment_calc divergence (cross-reference)

| Field | Rejected (conservative) | Accepted (creative) | txt |
|-------|------------------------|---------------------|-----|
| Gold leverage | 5x | 7x | 7x |
| Gold 절반 익절 stated_profit | 500,000,000 | 750,000,000 | 750,000,000 |
| WTI 잔여 entry_price | 62.5 | 60 | not explicit |
| WTI 잔여 stated_profit | 500,000,000 | 175,000,000 | 175,000,000 |
| final_total_assets | 4,020,000,000 | 4,645,000,000 | ~46.4억 |

The accepted artifact is consistent with the arc txt on all explicit numeric claims. The rejected artifact diverged on leverage (5x vs txt's 7x), which cascaded into different profit calculations. This confirms the rejection was appropriate and the accepted artifact is the correct truth source.

Severity hint: non-issue for accepted truth; supports rejection legitimacy.

## 3. Non-Issues

### N-1. Arc txt Carryover Authority Packet vs artifact `state_constraints` — equipment/location/capital chain

All four arcs match cleanly:

| Transition | Equipment | Location | Capital | Total Assets |
|-----------|-----------|----------|---------|--------------|
| Arc 1 end → Arc 2 start | 3종 match | "서울 강남" match | 19.7억 match | 19.7억 match |
| Arc 2 end → Arc 3 start | 5종 match | SW인베스트먼트 match | 4.7억 match | 22.7억 match |
| Arc 3 end → Arc 4 start | 7종 match | SW인베스트먼트 match | 17.2억 match | 29.7억 match |

No missing or phantom items. No location drift. No capital discontinuity.

### N-2. `joint_docs.final_location` vs `arc_end_state.location`

All four arcs: exact string match.

### N-3. `joint_docs.physical_inventory` vs `arc_end_state.equipment`

All four arcs: item-for-item match (3종, 5종, 7종, 8종 respectively).

### N-4. `investment_calc` numeric consistency with txt body

All accepted artifacts' transaction details match the corresponding txt tactical doc amounts:

- Arc 2: WTI 매수 15억, entry ~60, leverage 3x
- Arc 3: WTI 절반 청산, 수익 5억 (+500,000,000)
- Arc 4: WTI 잔여 청산 수익 1.75억 (+175,000,000), 금 매수 15억 7x, 금 절반 익절 수익 7.5억 (+750,000,000)

### N-5. UTF-8 integrity

All inspected JSON and txt files decoded without error. No `U+FFFD`, triple-question placeholder, or mojibake detected in any field.

### N-6. `beat_sequence` and `tactical_doc` narrative consistency

All four accepted artifacts' beat sequences align with the corresponding arc txt beat sequences. Episode numbering, character actions, and event ordering are consistent.

### N-7. `items_consumed` minor differences

- Arc 2 artifact: "사무실 관리비" — txt doesn't explicitly list this in carryover but it's narratively present
- Arc 4 accepted: "해외 경제지 3종 구독료" — both txt and artifact mention this

These are wording-level, not structural.

## 4. Severity Hint

| ID | Severity | Description |
|----|----------|-------------|
| F-1 | **P1-candidate** | `internal_energy` survives in accepted artifacts for Arc 1, 3, 4 despite genre-contract repair claim. Values inconsistent (0 vs 100). Saved-contract mismatch. |
| F-2 | **P2-candidate** | `power_changes` start/end chain broken at every arc transition. Silent state drift if consumed downstream. |
| F-3 | P3 | 박성호 `npc_introductions` duplicate (Arc 1 ep 3 vs Arc 2 ep 7). |
| F-4 | P3 | Null-episode duplicate `relationship_changes` entries in Arc 2 and rejected Arc 4. |
| F-5 | non-issue | Rejected Arc 4 investment_calc diverges from accepted/txt, confirming rejection legitimacy. |

The numeric/business spine (capital, total_assets, equipment, location, items, investment_calc) is **coherent** across all four accepted arcs and their txt sources.

The primary artifact truth defect is F-1 (`internal_energy` survival), which directly supports the survey order's P1-candidate hypothesis.

F-2 (`power_changes` chain break) is a newly identified issue not in the provisional severity map, warranting P2 classification pending cross-lane validation.

## 5. Stop

read-only lane survey complete; no project artifacts mutated
