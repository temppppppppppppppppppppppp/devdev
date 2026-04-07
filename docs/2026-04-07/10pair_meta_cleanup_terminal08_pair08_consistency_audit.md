# Pair 08 Meta-Cleanup Consistency Audit
**Date:** 2026-04-07  
**Files Audited:**
- TR: C:/Users/wjjo/Desktop/글도비/treatments/08_pantech_cyworld_reborn_tr_block_070_draft.json (280.6 KB, 70 blocks)
- BI: C:/Users/wjjo/Desktop/글도비/bible/08_bi_pantech_cyworld_reborn.json (353.1 KB, 70 plot_roadmap entries)

---

## A. Cross-File Checks (TR ↔ BI)

### A1. Plot Roadmap Mirror Integrity
**Status:** PASS

All 70 blocks in TR.blocks[*] are byte-for-byte identical to BI.MasterBible.plot_roadmap[*].

### A2. NPC Name Consistency
**Status:** WARN

Four NPCs not directly referenced in TR structured fields:
- 영수현, 박제인, 오영진, 이혜미

### A3. KeyNPCs key_blocks Alignment
**Status:** WARN

Six block references are missing from TR:
- 이혜미: Blocks 30, 70
- 박제인: Blocks 27, 68
- 이윤호: Block 68
- 박석준: Blocks 22, 70
- 김지은: Blocks 47, 63
- 정준호: Block 63

### A4. Capital Trajectory Consistency
**Status:** PASS

All 70 blocks form continuous chain. Portfolio history matches capital_after values.

### A5. Decline Blocks Consistency
**Status:** WARN

Block 21 missing from BI decline_blocks despite having negative capital_delta (-60원).
- TR: [4, 7, 13, 17, **21**, 23, 27, 34, 38, 43, 47, 53, 57, 63, 66]
- BI: [4, 7, 13, 17, 23, 27, 34, 38, 43, 47, 53, 57, 63, 66]

### A6. Death Flag Track Consistency
**Status:** PASS

Blocks [1, 7, 17, 34, 47, 63, 70] correctly listed.

### A7. Slip-Up Track Consistency
**Status:** PASS

Blocks [5, 29, 56] correctly listed.

### A8. ArcStructure ↔ OpponentTransitionPlan Alignment
**Status:** PASS

All 7 arcs align properly with matching arc_ids and block_ranges.

### A9. Seeds Planted_ep / Harvested_ep Alignment
**Status:** PASS

All seeds have valid ranges with planted_ep < harvested_ep in [1, 70].

---

## B. Within-File Structural Checks (TR)

### B1. Block No Sequence
**Status:** PASS

All 70 blocks sequential: block_no [1-70], block_id [Block 1 - Block 70].

### B2. Foreshadow Targets / Callback Sources Validity
**Status:** PASS

All references valid:
- foreshadow_targets: all future blocks (target > block_no)
- callback_sources: all past blocks (source < block_no)
- All in range [1, 70]

### B3. Foreshadow / Callback Array - Targets / Sources Consistency
**Status:** WARN

Two blocks have empty target arrays despite having prose content:
- Block 51: callback has 1 entry but callback_sources = []
- Block 56: foreshadow has 1 entry but foreshadow_targets = []

### B4. Arc Name Paraphrase Consistency
**Status:** PASS

Arc1-Arc7 successfully replaced with arc_no. All paraphrases consistently applied.

---

## C. Within-File Structural Checks (BI)

### C1. KeyNPCs Schema Uniformity
**Status:** PASS

All 15 entries have required fields: name and desc.

### C2. PayoffTrack New Object Schemas
**Status:** PASS

- power_payoff.milestones: objects with event, block keys
- foreshadow_payoff.notable_long_arcs: objects with seed, payoff, planted_block, harvested_block, span_blocks
- span_blocks calculation verified correct

### C3. Suspicion Escalation Blocks vs Slip-Up Track
**Status:** PASS

PayoffTrack.slip_up_track.suspicion_escalation_blocks [5, 29, 56] matches triggered_blocks.

### C4. HistoricalEvents Block Validity
**Status:** PASS

All 11 events have valid block numbers in [1, 70].

---

## Summary

**4 checks with findings (13 specific problems):**

| Issue | Count | Severity |
|-------|-------|----------|
| A3: NPC key_blocks missing | 6 | Medium |
| A5: Block 21 missing from decline_blocks | 1 | Medium |
| B3: Blocks without targets/sources | 2 | Low |
| A2: NPCs without structured refs | 4 | Low |

---

## Recommended Fixes

**[FIX-1]** Add Block 21 to BI.MasterBible.PayoffTrack.capital_payoff.decline_blocks
- Current: [4, 7, 13, 17, 23, 27, 34, 38, 43, 47, 53, 57, 63, 66]
- Target: [4, 7, 13, 17, 21, 23, 27, 34, 38, 43, 47, 53, 57, 63, 66]

**[FIX-2]** Verify 이혜미 key_blocks: Remove 30, 70 if not in TR
- File: BI.MasterBible.AssetLibrary.KeyNPCs[3].key_blocks

**[FIX-3]** Verify 박제인 key_blocks: Remove 27, 68 if not in TR
- File: BI.MasterBible.AssetLibrary.KeyNPCs[4].key_blocks

**[FIX-4]** Verify 이윤호 key_blocks: Remove 68 if not in TR
- File: BI.MasterBible.AssetLibrary.KeyNPCs[2].key_blocks

**[FIX-5]** Verify 박석준 key_blocks: Remove 22, 70 if not in TR
- File: BI.MasterBible.AssetLibrary.KeyNPCs[9].key_blocks

**[FIX-6]** Verify 김지은 key_blocks: Remove 47, 63 if not in TR
- File: BI.MasterBible.AssetLibrary.KeyNPCs[10].key_blocks

**[FIX-7]** Verify 정준호 key_blocks: Remove 47, 63 if not in TR
- File: BI.MasterBible.AssetLibrary.KeyNPCs[11].key_blocks

**[FIX-8]** Extract callback_sources for TR.blocks[50]
- File: TR.blocks[50].callback_sources
- Current: []
- Action: Extract block references from callback prose

**[FIX-9]** Extract foreshadow_targets for TR.blocks[55]
- File: TR.blocks[55].foreshadow_targets
- Current: []
- Action: Extract block references from foreshadow prose

---

## Conclusion

The cleanup was largely successful. The plot_roadmap mirror is intact, capital trajectories are continuous, and most structural fields are properly populated. The 9 identified issues are correctable without major restructuring:

1. One block missing from decline_blocks
2. Six blocks with incorrect NPC key_blocks references
3. Two blocks with incomplete callback/foreshadow mappings

The underlying data quality is good; these are boundary cases from the cleanup process.
