# 00_0405 Stage2 Terminal 1 Artifact Roundtrip Ledger

Date: 2026-04-05
Status: final
Document Type: terminal survey output
Canonical Path: `docs/2026-04-05/00_0405-stage2-terminal1-artifact-roundtrip-ledger.md`
Track: system
Mode: read-only artifact truth survey
Confidence: `96%`

## Coverage

- `projects/00_0405/plans/arcs/arc_002.txt`
- `projects/00_0405/plans/arcs/arc_003.txt`
- `projects/00_0405/plans/arcs/arc_004.txt`
- `projects/00_0405/logs/artifacts/stage2/arc_002/attempt_01/final_arc__balanced.json`
- `projects/00_0405/logs/artifacts/stage2/arc_004/attempt_01/final_arc__balanced.json`
- `projects/00_0405/logs/runtime_audit.jsonl`
- `docs/2026-04-05/00_0405-stage2-artifact-truth-observability-bounded-survey.md`
- `docs/2026-04-05/00_0405-stage2-artifact-truth-observability-evidence.json`

Scope was intentionally narrow:

- txt artifact truth
- selected Stage2 packet truth
- carryover-relevant runtime audit proof

## Findings

### 1. Arc2 txt ending and selected packet ending do not round-trip the same location truth

`arc_002.txt` ends the arc in the Yeouido SOHO office, while the selected Stage2 artifact already ends in the Gangnam representative office.

- txt ending: `Yeouido SW Investment SOHO office` [arc_002.txt:83](C:/Users/User/Desktop/글도비/projects/00_0405/plans/arcs/arc_002.txt#L83)
- selected artifact ending: `Gangnam-gu Teheran-ro SW Investment representative office` [final_arc__balanced.json:251](C:/Users/User/Desktop/글도비/projects/00_0405/logs/artifacts/stage2/arc_002/attempt_01/final_arc__balanced.json#L251)
- next arc txt start already follows the Gangnam packet truth [arc_003.txt:16](C:/Users/User/Desktop/글도비/projects/00_0405/plans/arcs/arc_003.txt#L16)

This is a real round-trip drift, not just wording variation.

### 2. Arc4 txt start-state drops the Ecuador memo that the selected packet still carries

`arc_003.txt` still carries the Ecuador memo in start-state gear, and the selected Stage2 packet for arc 4 still carries it too.

- arc3 txt start gear includes the memo [arc_003.txt:18](C:/Users/User/Desktop/글도비/projects/00_0405/plans/arcs/arc_003.txt#L18)
- arc4 selected packet start gear includes the memo [final_arc__balanced.json:267](C:/Users/User/Desktop/글도비/projects/00_0405/logs/artifacts/stage2/arc_004/attempt_01/final_arc__balanced.json#L267)
- arc4 txt start gear drops it [arc_004.txt:18](C:/Users/User/Desktop/글도비/projects/00_0405/plans/arcs/arc_004.txt#L18)

That means the selected carryover packet survives, but the human-readable txt artifact trims part of it away before the next arc starts.

### 3. Arc4 location/state packet stays overly frozen until the end-state jump

Arc 4 reuses the same office/state framing across multiple episode starts and ends:

- start-state office with WTI/Ecuador screen context [arc_004.txt:16](C:/Users/User/Desktop/글도비/projects/00_0405/plans/arcs/arc_004.txt#L16)
- same office packet still repeats later in the arc [arc_004.txt:32](C:/Users/User/Desktop/글도비/projects/00_0405/plans/arcs/arc_004.txt#L32) [arc_004.txt:69](C:/Users/User/Desktop/글도비/projects/00_0405/plans/arcs/arc_004.txt#L69)
- then the final txt end-state jumps to `private office` [arc_004.txt:84](C:/Users/User/Desktop/글도비/projects/00_0405/plans/arcs/arc_004.txt#L84)
- the selected packet also encodes a more precise late-night personal office end-state [final_arc__balanced.json:258](C:/Users/User/Desktop/글도비/projects/00_0405/logs/artifacts/stage2/arc_004/attempt_01/final_arc__balanced.json#L258)

This is weaker than finding 1 and 2, but it still points to packet-to-txt state packaging lag.

### 4. Runtime audit confirms the system is actively repairing Stage2 carryover packaging

The runtime audit shows repeated deterministic repair activity:

- arc 2 auto-correct rewrites start location, end location, and prior-arc item disappearance [runtime_audit.jsonl:4](C:/Users/User/Desktop/글도비/projects/00_0405/logs/runtime_audit.jsonl#L4)
- arc 3 auto-correct repeats the same pattern [runtime_audit.jsonl:7](C:/Users/User/Desktop/글도비/projects/00_0405/logs/runtime_audit.jsonl#L7)
- arc 4 auto-correct again rewrites tactical-doc location and end-state location [runtime_audit.jsonl:10](C:/Users/User/Desktop/글도비/projects/00_0405/logs/runtime_audit.jsonl#L10)

So the round-trip drift is not speculative. The pipeline itself is already compensating for it.

## Non-Issues

### 1. Numeric/business spine is broadly coherent

The business-state ladder still holds:

- arc2 selected packet total assets: `2.3B KRW` [final_arc__balanced.json:253](C:/Users/User/Desktop/글도비/projects/00_0405/logs/artifacts/stage2/arc_002/attempt_01/final_arc__balanced.json#L253)
- arc3 txt total assets: `3.0B KRW` [arc_003.txt:75](C:/Users/User/Desktop/글도비/projects/00_0405/plans/arcs/arc_003.txt#L75)
- arc4 selected packet total assets: `3.0B KRW` at start [final_arc__balanced.json:273](C:/Users/User/Desktop/글도비/projects/00_0405/logs/artifacts/stage2/arc_004/attempt_01/final_arc__balanced.json#L273)
- arc4 txt total assets: `4.5B KRW` at end [arc_004.txt:87](C:/Users/User/Desktop/글도비/projects/00_0405/plans/arcs/arc_004.txt#L87)

This is not a broken numeric progression case.

### 2. The core story progression is still readable and sequential

Despite packet drift, the macro sequence still reads coherently:

- WTI entry and first proof in arc 2
- PB dominance and partial realization in arc 3
- gold entry and later profit-taking in arc 4

That is why this lane should not be described as `Stage2 content collapse`.

## Owner Verdict

Primary owner is still `Stage2 contract normalization / artifact emission`, not Stage3 or Stage4.

More specifically, this terminal's evidence points to:

- Stage2 packet truth surviving in selected artifact JSON
- Stage2 txt artifact not fully reflecting the same normalized carryover truth
- runtime auto-correct repeatedly compensating for that gap

So the best owner reading is:

- `Stage2 packet-to-txt round-trip weakness`

and not:

- `Stage3 transform failure as the first visible issue in this specific 00_0405 slice`

## Minimal Next Wave

The smallest queue-safe next wave from this terminal alone would be:

1. preserve selected Stage2 packet truth as the authoritative carryover packet
2. trace where final arc txt packaging drops or rewrites that packet
3. normalize only location/item/state carryover round-trip at Stage2 emission time

Bounded owner candidates:

- Stage2 artifact emission surfaces
- Stage2 post-process / auto-correct writeback surfaces

This still remains a future upstream wave and does not justify promoting Stage2 above the active Stage4 queue.

## Stop

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-05 output

3-pass audit note:

- pass 1: verified txt vs selected artifact line anchors for arc2, arc3, and arc4
- pass 2: rejected numeric-collapse framing and isolated packet round-trip drift as the stronger reading
- pass 3: rechecked runtime audit repairs and aligned the verdict with the parked Stage2 normalization lane
