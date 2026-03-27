# Empire Youngest Weakness Report — Order-OPUS Brief

Date: 2026-03-27
Audience: OPUS acting as the single worker (no sub-dispatch needed)
Target work_id: `empire_youngest_allsector`

## 1. What You Are

You are a single worker-OPUS for this run.

This unit does not require sub-OPUS dispatch because:

- the task is sequential (read full TR → read full BI → catalog per block)
- there is no parallel truth-gathering step — all truth was already established in the re-audit
- the output is one coherent document, not a synthesis of independent findings

Your job:

- read the full TR (70 blocks) and full BI
- produce a structured 5-axis weakness catalog
- do not rewrite any blocks
- return one deliverable

## 2. Fixed Scope

This run is only:

- `weakness report`

This run is not:

- truth-reconciliation re-audit (already done)
- TR regeneration
- BI redesign
- revival-stage probe
- active promotion

## 3. Input Chain

Read in this exact order:

1. `docs/2026-03-27/empire-youngest-truth-reaudit-report.md` — predecessor findings
2. `docs/2026-03-27/opus-empire-youngest-weakness-report-order.md` — full order
3. `treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json` — full TR
4. `bible/_quarantine/0_bi_empire_youngest_allsector.json` — full BI

## 4. The 5 Axes

### Axis 1: Scene-Deficit Catalog (Block 32-43)

Per block: block_id, current content (1 line), missing scene/tension, what restored block should feel like.

### Axis 2: Inline Restoration Inventory (Block 44-69)

Per block: block_id, current inline content (quoted), minimum narrative elements for restoration, priority (high/medium/low). Group by priority.

### Axis 3: 타자 POV Diminishing Returns

All 타자 POV blocks. Per block: block_id, POV character, value vs cost, recommendation (keep/merge/cut).

### Axis 4: Emotional Arc Gap Map

Characters: 최다은, 정하윤, 이준혁, 오승아.
Per character: appearance block_ids, gap intervals, suggested insertion points.

### Axis 5: Sector Texture Recovery

Per sector entry in Block 32-69: sector, block_id, current state (timing summary/partial scene/full scene), one concrete scene name.

### Synthesis: Revision Priority Matrix

Top 10 blocks ranked by restoration impact. Consider: narrative centrality, protagonist engine survival, emotional arc gap closure, sector texture recovery.

## 5. Creative Anchors To Judge Against

A block that washes out any of these is a gap even if it has content:

- 2045 → 2025 regression frame
- credit-card `3,000만 원` BTC seed
- `세 개씩. 쉬지 않고.` doctrine
- independent-capital rule
- family-collapse 3-axis memory
- low-affect protagonist engine
- 0원 → 200조 all-sector build

## 6. What To Watch

- Do not let the catalog become a rewrite. "Block 35 needs X" is a catalog entry. Writing the actual X is a rewrite.
- Do not inflate priorities. If a block is low-impact summary that works fine as connective tissue, mark it `low`.
- Do not hand-wave mid-band compression. "Blocks 32-43 are compressed" is not a catalog — each block must have its own gap entry.
- Do not skip Block 44-69 because they are inline. Each inline block must be inventoried.

## 7. Deliverable

- `docs/2026-03-27/empire-youngest-weakness-report.md`

## 8. Next Unit After This

- if catalog is clean and actionable: `targeted TR revision`
- if structural problems found: `TR architecture reassessment`
- if fewer than 5 real gaps: `revival-stage probe`

## 9. Minimal Prompt

```text
너는 이번 런의 worker-OPUS다. `docs/2026-03-27/opus-empire-youngest-weakness-report-order.md`와 `docs/2026-03-27/empire-youngest-weakness-opus-context-memo.md`를 UTF-8로 읽고, `empire_youngest_allsector`에 대해 `weakness report` 1단위만 수행하라. TR 전체와 BI 전체를 읽고, 5축 gap catalog + revision priority matrix를 작성하라. 블록 수정 금지 — 카탈로그만.
```

Confidence:
- 98% this is the correct delegation shape for the weakness report unit
