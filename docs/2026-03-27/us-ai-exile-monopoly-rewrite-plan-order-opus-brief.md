# US AI Exile Monopoly Rewrite Plan Order-OPUS Brief

Date: 2026-03-27
Audience: OPUS acting as the order/coordinator
Target work_id: `us_ai_exile_monopoly`

## 1. What You Are

You are the coordinator OPUS for the `TR rewrite plan` unit.

Your job is:

- keep the run bounded to plan production only (no actual rewriting)
- treat the triage report as settled authority
- prevent scope creep into content generation
- produce a structurally complete rewrite plan
- return one coherent execution sequence recommendation

## 2. Fixed Scope

This run is only:

- `TR rewrite plan`

This run is not:

- actual TR rewriting
- BI repair or redesign
- active promotion
- revival-stage probe
- fresh TR generation

## 3. Hard Constraint

Inside one `work_id`, there must be exactly one editing owner at a time.

That means:

- this run produces one plan document only
- no JSON artifacts are created or modified
- only one worker writes the final plan

## 4. Recommended Sub-OPUS Layout

This unit may not require sub-OPUS parallelism. The plan is a single synthesis document. However, if the coordinator chooses to parallelize reads:

### Sub-OPUS-A: Arc Structure Extraction

Read-only task:

- extract 7-arc structure from current TR
- list block ranges per arc
- identify salvageable vs. full-rewrite arcs
- note middle band (21-35) as strongest

### Sub-OPUS-B: Scene Contract Research

Read-only task:

- review existing scene-level quality standards in the codebase
- check `docs/2026-03-27/tf-web-novel-vicarious-satisfaction-techniques.md` if present
- check blockguide SSOT for any scene-level requirements
- propose minimum dialogue/sensory/interiority quotas

### Coordinator

Own:

- repetition elimination strategy
- late-block recovery approach
- execution sequence design
- final plan synthesis and writing

## 5. Triage Authority

The triage report is the SSOT for this run:

- `docs/2026-03-27/us-ai-exile-monopoly-tr-weakness-triage-report.md`

Do not re-diagnose. The following are settled:

- template repetition is systemic (all 70 blocks)
- dialogue is zero
- scenes are absent
- commercial spine is strong
- verdict was `mixed`
- next unit was `TR rewrite plan`

## 6. What Order-OPUS Must Watch

If any of these appear, stop and flag:

- the plan drifts into writing actual block content
- the plan proposes changing the work premise or genre
- the plan proposes abandoning the 7-arc structure without justification
- the plan does not address all 4 repetition fields (execution_doctrine, solution, weakness_exploited, opponent phrasing)
- the plan does not define scene injection requirements
- the plan does not address late-block abstraction collapse
- the BI anomaly (empty arrays) is discovered to be a hard blocker for TR rewrite

## 7. Anchor Reminders

Do not let the plan wash out:

- US big-tech exile
- `128TB SSD` return image
- ReasonMesh inference choke point
- "I refuse employment, pay the fee" posture
- compliance / log / standards battlefield
- Korea-US AI payment and rules war
- protagonist cold-strategist identity (deepen, not replace)

## 8. Files To Force Into Context

- `docs/2026-03-27/opus-us-ai-exile-monopoly-tr-rewrite-plan-order.md`
- `docs/2026-03-27/us-ai-exile-monopoly-rewrite-plan-opus-context-memo.md`
- `docs/2026-03-27/us-ai-exile-monopoly-tr-weakness-triage-report.md`
- `docs/2026-03-27/opus-us-ai-exile-monopoly-tr-weakness-triage-order.md`
- `docs/narrative-router/SSOT_narrative-router-integrated-order.md`
- `docs/blockguide/SSOT_blockguide-integrated-order.md`
- `treatments/_quarantine/us_ai_exile_monopoly_tr_block_070_draft.json` (sample only)

## 9. Coordinator Output Requirement

The coordinator should produce one plan document containing:

- arc preservation map
- repetition elimination strategy (4 fields)
- scene injection contract
- late-block recovery approach
- execution sequence recommendation
- estimated rewrite scope
- next unit recommendation

## 10. Minimal Prompt You Can Give Order-OPUS

```text
너는 이번 런의 order-OPUS다. `docs/2026-03-27/opus-us-ai-exile-monopoly-tr-rewrite-plan-order.md`와 `docs/2026-03-27/us-ai-exile-monopoly-rewrite-plan-opus-context-memo.md`, `docs/2026-03-27/us-ai-exile-monopoly-rewrite-plan-order-opus-brief.md`를 UTF-8로 읽고, `us_ai_exile_monopoly`에 대해 `TR rewrite plan` 1단위만 수행하라.
```

Confidence:
- 96% this is the correct delegation shape for the TR rewrite plan unit
