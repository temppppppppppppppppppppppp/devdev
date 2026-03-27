# OPUS Empire Youngest Weakness Report Order

Date: 2026-03-27
Track: narrative pipeline
Status: active
Scope: single-work OPUS order for `empire_youngest_allsector`
Predecessor: `docs/2026-03-27/empire-youngest-truth-reaudit-report.md`

## 1. Order Intent

This order fixes the target to `empire_youngest_allsector` and asks OPUS to complete exactly one bounded unit:

- `weakness report`

The preceding `truth-reconciliation re-audit` established:

- 70/70 blocks exist (count clean)
- Block 1-5 + Block 70 = full narrative quality (~32 blocks total)
- Block 32-43 = mid-band compression (200-300 words per block)
- Block 44-69 = inline JSON 1-line format (350-500 chars per block)
- 38/70 blocks are in summary/inline state
- pair is present but not probe-ready

This is not a fresh TR generation order.
This is not a revival-stage probe.
This is not a BI redesign.
This is a structured gap catalog that enables targeted revision later.

## 2. Non-Negotiable Rules

- UTF-8 only
- read re-audit report first, then live pair files
- one work, one owner, one unit
- no same-work concurrent editing
- no code or system edits
- do not regenerate TR blocks in this run
- do not redesign BI in this run
- do not promote to active path in this run
- do not run revival-stage probe in this run
- do not rewrite blocks — only catalog their weaknesses

## 3. Canonical Target

- work_id: `empire_youngest_allsector`
- TR: `treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json`
- BI: `bible/_quarantine/0_bi_empire_youngest_allsector.json`

## 4. Live Facts From Re-Audit

These are verified truths from the preceding re-audit. Do not re-verify — use as starting facts.

1. TR block count: `70` (confirmed by direct read)
2. BI plot_roadmap count: `70` (confirmed)
3. BI internal structure: NPC_Timeline(10), HistoricalEvents(13), OpponentTransitionPlan(3 phases)
4. sequential_run_status: `run_class=sequential_production`, `last_sequential_block_pass=70`, `manual_audit_ready=true`
5. phase0_ready_snapshot: `manual_audit_pass=true`

Quality distribution (re-audit finding):

| Zone | Blocks | State |
|------|--------|-------|
| Early engine | 1-5 | full narrative (~100 lines/block) |
| Front half | 6-31 | presumed adequate (not fully sampled) |
| Mid-band | 32-43 | compressed (200-300 words/block) |
| Rear half | 44-69 | inline JSON 1-line format (350-500 chars) |
| Finale | 70 | full narrative restored |

## 5. Weakness Report Scope

The report must catalog — not fix — the following 5 axes:

### Axis 1: Block-Level Scene-Deficit Catalog (Block 32-43)

For each block in 32-43:

- block_id
- current content summary (1 line)
- what scene/tension is missing
- what the block should feel like if restored

Do not rewrite the block. Only describe the gap.

### Axis 2: Inline-to-Narrative Restoration Inventory (Block 44-69)

For each block in 44-69:

- block_id
- current inline content (quoted)
- minimum narrative elements needed for restoration
- priority: `high` / `medium` / `low`

Group by priority tier.

### Axis 3: 타자 POV Diminishing Returns Analysis

Identify all 타자 POV blocks (known: 15, 25, 36, 41, 46, 52 — verify and extend if more exist).

For each:

- block_id
- POV character
- what it adds vs what it costs (protagonist agency loss)
- recommendation: `keep` / `merge into protagonist POV` / `cut`

### Axis 4: Emotional Arc Gap Map

Track these relationship lines across all 70 blocks:

- 최다은 (known touchpoints: ~Block 50, 70 — find all)
- 정하윤 (CFO→CIO evolution)
- 이준혁 (sibling conflict line)
- 오승아 (adversary→legal ally)

For each:

- block_ids where they appear
- gap intervals (consecutive blocks without appearance)
- where a 1-block emotional beat insertion would close the longest gap

### Axis 5: Sector Texture Recovery List

For each sector entry in Block 32-69:

- sector name
- block_id
- current state: `timing summary` / `partial scene` / `full scene`
- one concrete scene suggestion that would restore domain-specific pressure

Do not write the scene. Only name it.

## 6. Mandatory Reads

Read in this order:

1. `docs/2026-03-27/empire-youngest-truth-reaudit-report.md`
2. `treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json` (full read)
3. `bible/_quarantine/0_bi_empire_youngest_allsector.json` (full read)

Optional if needed:

4. `docs/blockguide/SSOT_blockguide-integrated-order.md`

## 7. Fixed Creative Constraints

Do not wash out these anchors:

- 2045 → 2025 regression frame
- credit-card `3,000만 원` BTC seed start
- `세 개씩. 쉬지 않고.` execution doctrine
- all-sector rolling structure
- independent-capital rule: no family money
- family-collapse memory: semiconductor delay / sibling conflict / PF crisis
- low-affect protagonist engine with delayed emotional cracks

When cataloging weaknesses, judge against these anchors.
A block that technically has content but washes out these anchors is still a gap.

## 8. Deliverable

Save exactly one main report:

- `docs/2026-03-27/empire-youngest-weakness-report.md`

Structure:

```
# Empire Youngest — Weakness Report

## 0. Summary Stats
- total blocks: 70
- full narrative quality: N blocks
- compressed: N blocks
- inline summary: N blocks
- scene-deficit blocks requiring attention: N

## 1. Block-Level Scene-Deficit Catalog (Block 32-43)
[table]

## 2. Inline-to-Narrative Restoration Inventory (Block 44-69)
[grouped by priority]

## 3. 타자 POV Diminishing Returns
[table + recommendations]

## 4. Emotional Arc Gap Map
[per character]

## 5. Sector Texture Recovery List
[per sector]

## 6. Revision Priority Matrix
[top 10 blocks by impact if restored]

## 7. Next Unit Recommendation
[exactly one]

## 8. Handoff
[flat format]
```

## 9. Stop Conditions

Stop immediately and report if:

- TR or BI cannot be parsed cleanly as UTF-8
- block boundaries are ambiguous (cannot determine where one block ends and another begins)
- the catalog itself would require runtime generation to answer a static question
- the weakness report exceeds 50 blocks of attention (scope creep — the report should catalog, not fix)

If ambiguity arises, choose the smaller next step.

## 10. Expected Next Unit After This Order

- if weakness report cleanly catalogs all gaps: `targeted TR revision` (Block 32-69 restoration)
- if weakness report reveals structural problems beyond block-level gaps: `TR architecture reassessment`
- if weakness report is trivial (fewer than 5 real gaps): `revival-stage probe`

## 11. Handoff Format

End with:

```text
work_id: empire_youngest_allsector
current_stage: audit_or_repair
finished_unit: weakness report
changed_files: ...
next_unit: ...
stop_reason: ...
```

## 12. 3-Pass Self Audit

### Pass 1. Contract Alignment

- target is fixed to one `work_id`
- scope is catalog-only, no block rewriting
- no same-work parallel editing is authorized
- no fresh generation stages are mixed in
- predecessor re-audit is referenced, not duplicated

### Pass 2. Operational Usefulness

- 5 axes cover the full weakness surface discovered in re-audit
- each axis has explicit per-block output format
- revision priority matrix enables targeted follow-up
- stop conditions prevent scope creep into rewriting

### Pass 3. Integrity

- saved under dated `docs/2026-03-27/`
- UTF-8 only
- no code-edit instructions
- no multi-unit overreach

Confidence:
- 97% that `weakness report` is the correct next OPUS unit for this pair
