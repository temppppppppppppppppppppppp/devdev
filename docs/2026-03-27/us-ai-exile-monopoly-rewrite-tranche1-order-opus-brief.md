# US AI Exile Monopoly Rewrite Tranche 1 Order-OPUS Brief

Date: 2026-03-27
Audience: OPUS acting as the order/coordinator
Target: `us_ai_exile_monopoly`, Tranche 1 (Block 21-30, ARC-03)

## 1. What You Are

You are the coordinator OPUS for Tranche 1 rewrite execution.

Your job is:

- keep the run bounded to Block 21-30 only
- enforce the rewrite plan's field-level contracts
- enforce scene injection minimums
- enforce repetition kill rules
- run quality gate self-check at the end
- produce rewritten Block 21-30 in the canonical TR JSON

## 2. Fixed Scope

This run is only:

- `TR rewrite — Tranche 1 (Block 21-30, ARC-03)`

This run is not:

- any other tranche
- rewrite planning
- BI repair
- active promotion
- code edits

## 3. Hard Constraint

- only one worker may write to the TR JSON
- parallel read-only investigation is allowed
- the final write to Block 21-30 must be atomic (all 10 blocks at once or sequentially by one owner)

## 4. Recommended Sub-OPUS Layout

### Option A: Single Writer (Recommended for Tranche 1)

Since this is the first tranche and establishes the quality baseline, a single writer with full context is recommended over parallelized block writing.

1. Read current Block 21-30 + adjacent blocks (20, 31) for continuity
2. Read BI for ARC-03 reference data
3. Rewrite all 10 blocks sequentially
4. Run quality gate self-check
5. Write to TR JSON

### Option B: Parallel Read + Single Write

If coordinator chooses to parallelize:

- Sub-OPUS-A (read-only): extract current Block 21-30 field values, map opponent mentions, identify continuity links to adjacent blocks
- Sub-OPUS-B (read-only): extract BI data relevant to ARC-03 (plot_roadmap entries 21-30, relevant NPCs, opponent_transition_plan phase 2)
- Coordinator: synthesize and write all 10 blocks

## 5. Quality Gate Checklist

At the end of the run, verify all 6:

| # | Gate | Criterion |
| --- | --- | --- |
| 1 | Template repetition zero | None of the 6 banned phrases appear in Block 21-30 |
| 2 | Dialogue minimum | All 10 blocks have ≥ 3 direct speech instances |
| 3 | Sensory minimum | All 10 blocks have ≥ 2 sensory details |
| 4 | Interiority minimum | All 10 blocks have ≥ 1 protagonist inner beat |
| 5 | Opponent weakness unique | weakness_exploited is 화싱AI-specific, not generic |
| 6 | Doctrine unique | execution_doctrine is ARC-03-specific |

## 6. What Order-OPUS Must Watch

Stop and flag if:

- any banned phrase from §6.4 of the order appears in any rewritten block
- dialogue count falls below 3 in any block
- opponent is still rendered as a monolithic entity without individual characters
- solution still follows the old 4-phrase template structure
- continuity with Block 20 (end of ARC-02) or Block 31 (start of ARC-04) breaks
- protagonist is still purely a contract machine with no interiority

## 7. Anchor Reminders for ARC-03

- ReasonMesh → edge inference expansion is the tech substrate
- Contract language as power → telecom/edge API contracting scenes
- Standards battlefield → NPU testing, telecom certification
- Cold-strategist + cost awareness → protagonist's inner recognition of what expansion costs

## 8. Files To Force Into Context

- `docs/2026-03-27/opus-us-ai-exile-monopoly-tr-rewrite-tranche1-order.md`
- `docs/2026-03-27/us-ai-exile-monopoly-rewrite-tranche1-opus-context-memo.md`
- `docs/2026-03-27/us-ai-exile-monopoly-tr-rewrite-plan.md`
- `docs/2026-03-27/us-ai-exile-monopoly-tr-weakness-triage-report.md`
- `treatments/_quarantine/us_ai_exile_monopoly_tr_block_070_draft.json`
- `bible/_quarantine/0_bi_us_ai_exile_monopoly.json`

## 9. Minimal Prompt

```text
너는 이번 런의 order-OPUS다. `docs/2026-03-27/opus-us-ai-exile-monopoly-tr-rewrite-tranche1-order.md`와 `docs/2026-03-27/us-ai-exile-monopoly-rewrite-tranche1-opus-context-memo.md`, `docs/2026-03-27/us-ai-exile-monopoly-rewrite-tranche1-order-opus-brief.md`를 UTF-8로 읽고, `us_ai_exile_monopoly`의 TR Block 21-30 (ARC-03) 리라이트 1트랜치만 수행하라.
```

Confidence:
- 95% this is the correct delegation shape for Tranche 1
