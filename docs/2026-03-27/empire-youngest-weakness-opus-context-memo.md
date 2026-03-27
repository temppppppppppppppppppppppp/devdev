# Empire Youngest Weakness Report — OPUS Context Memo

Date: 2026-03-27
Purpose: minimal handoff memo for worker OPUS
Target: `empire_youngest_allsector`

## 1. Current Truth

- family: `blockguide`
- mode: existing `TR + BI` pair weakness cataloging
- canonical pair is still in `_quarantine`
- preceding unit: `truth-reconciliation re-audit` (completed, verdict MIXED)
- this unit: `weakness report`
- this is not TR regeneration, BI redesign, or revival-stage probe

## 2. Canonical Pair Paths

- TR: `treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json`
- BI: `bible/_quarantine/0_bi_empire_youngest_allsector.json`

## 3. What The Re-Audit Found

Re-audit report: `docs/2026-03-27/empire-youngest-truth-reaudit-report.md`

Key findings you should treat as starting facts:

1. 70/70 blocks exist — count is clean
2. quality is split:
   - Block 1-5 + 70: full narrative (~100 lines/block)
   - Block 6-31: presumed adequate (front half)
   - Block 32-43: compressed (200-300 words/block, timing summary, scene loss)
   - Block 44-69: inline JSON 1-line format (350-500 chars, no scene)
3. 타자 POV blocks (15, 25, 36, 41, 46, 52): formulaic pattern, diminishing returns
4. 최다은 감정선: Block 50 → Block 70, 20-block gap with no progression
5. sector texture: Block 32+ collapses domain-specific scene into timing summary

The re-audit verdict was `MIXED` and chose `weakness report only` as next unit.

## 4. Why This Run Exists

The pair cannot go to revival-stage probe because:

- a probe on Block 32-69 would only report "this is a summary, not narrative" 38 times
- a structured gap catalog is needed first so that targeted revision knows exactly what to fix

This run produces that catalog.

## 5. What To Do

Read the full TR and BI, then catalog weaknesses across 5 axes:

1. **Scene-Deficit Catalog** — Block 32-43, per-block gap description
2. **Inline Restoration Inventory** — Block 44-69, per-block with priority tiers
3. **타자 POV Analysis** — all POV blocks, keep/merge/cut recommendation
4. **Emotional Arc Gap Map** — 최다은, 정하윤, 이준혁, 오승아 across all 70 blocks
5. **Sector Texture Recovery** — per-sector, per-block, one concrete scene name

Then synthesize into a **Revision Priority Matrix** (top 10 blocks by impact).

## 6. Fixed Creative Anchors

Preserve — judge gaps against these:

- 2045 → 2025 regression frame
- `세 개씩. 쉬지 않고.` doctrine
- independent-capital rule
- all-sector rolling expansion
- family-collapse 3-axis memory (semiconductor delay / sibling conflict / PF crisis)
- low-affect protagonist with delayed emotional fracture
- credit-card `3,000만 원` BTC seed

## 7. Do Not Do In This Run

- no block rewriting or regeneration
- no BI redesign
- no active promotion
- no revival-stage probe
- no code edits
- catalog only — describe gaps, do not fill them

## 8. Main Order Doc

Read and follow:

- `docs/2026-03-27/opus-empire-youngest-weakness-report-order.md`

## 9. Expected Deliverable

- `docs/2026-03-27/empire-youngest-weakness-report.md`

## 10. Suggested One-Line OPUS Prompt

```text
너는 이번 런의 worker-OPUS다. `docs/2026-03-27/opus-empire-youngest-weakness-report-order.md`와 `docs/2026-03-27/empire-youngest-weakness-opus-context-memo.md`를 UTF-8로 읽고, `empire_youngest_allsector`에 대해 `weakness report` 1단위만 수행하라. TR 전체와 BI 전체를 읽고, 5축 gap catalog + revision priority matrix를 작성하라. 블록 수정 금지 — 카탈로그만.
```

Confidence:
- 97% this memo is sufficient for low-overhead worker OPUS handoff
