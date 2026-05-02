# Downstream Episode Pacing Hint Attachment Harness v1

Date: 2026-05-02
Status: active
Scope: material-side attachment harness for advisory downstream episode pacing hints on live `TR + BI` pairs

## 1. Role

This harness defines how to attach `downstream_episode_pacing_hint` to material-side `TR + BI` pairs.

It exists to reduce downstream S2 expansion drift before manuscript generation.

This harness does not:

- modify S2 contracts
- modify runtime schema requiredness
- replace `webnovel_pacing_contract`
- replace `reader_payoff_ladder`
- allow Python to decide narrative pacing quality

LLM operators decide the pacing range. Python may only collect coverage, parseability, sync, and hygiene evidence.

## 2. Entry Conditions

Use this harness when:

- a pair is called immediate-use, range-complete, or `즉시전력`
- an existing immediate-deployment row has `range_attachment_status: pending_downstream_episode_pacing_hint_attachment`
- a live pair already has `webnovel_pacing_contract` but lacks bounded episode range guidance
- a new promotion order wants immediate material deployment in the current range-gated shelf

Do not use this harness to bulk-rewrite unrelated TR/BI content.

## 3. Canonical Paths

Attach the hint at both paths:

- `TR.blocks[*].genre_ext.downstream_episode_pacing_hint`
- `MasterBible.plot_roadmap[*].genre_ext.downstream_episode_pacing_hint`

Optional BI policy summary:

- `MasterBible.BIAmplificationPower.downstream_episode_pacing_hint_policy`

Transitional names such as `episode_pacing_hint` or `s2_pacing_hint` are readable only as legacy input. Newly touched material should write the canonical field name.

## 4. Minimum Shape

Each block hint must include:

```json
{
  "recommended_episode_count": "2",
  "acceptable_episode_range": "2-3",
  "stretch_cap": "4",
  "do_not_expand_to": "5+",
  "must_land_inside_range": {
    "proof": "episode 1-2",
    "receipt": "episode 2-3",
    "next_gate": "episode 3"
  },
  "range_reason": "pressure, proof, same-block receipt, and next gate can close without a second macro-battlefield"
}
```

Allowed value style:

- integers as strings or numbers are acceptable during transition
- ranges should be simple bounded strings such as `2-3`
- `do_not_expand_to` should name the overlong shape, not merely say `avoid slow pacing`

## 5. Range Decision Rules

Default range is not always `2-6`.

Use the block's actual pressure and receipt shape:

- `2`: one clear pressure line, one proof/action, one same-block receipt, one next-gate hook
- `2-3`: default strong business-power block; proof and receipt both need air but no extra battlefield
- `3`: heavier proof, negotiation, or public reevaluation but still one macro-battlefield
- `3-4`: large operating proof plus visible settlement, rights transfer, or multi-party reevaluation
- `4`: exceptional dense block with multiple hard assets, not a default
- `5+`: suspect unless explicitly justified by a major structural reason

For opening business-power or investment-family material, use the stricter upstream ruler:

- healthy target: `3 episodes`
- soft ceiling: `4 episodes`
- `5+ episodes`: slow-by-design suspicion

## 6. Required Block Closure Logic

Every hint must close the same loop:

`pressure -> operating/billing/data proof -> right or settlement receipt -> next gate`

For non-telecom works, substitute the domain assets, but preserve the loop:

`pressure -> actionable proof -> rights/control/cash/status receipt -> next gate`

Do not let family recognition, social approval, or court politics replace the operating reward engine.

## 7. Attachment Procedure

1. Read the pair authority:
   - Phase0
   - `work_guard`
   - TR
   - BI
   - latest benchmark or immediate-deployment closeout
   - latest pacing audit
2. Preserve existing:
   - `webnovel_pacing_contract`
   - `reader_payoff_ladder`
   - `BIAmplificationPower.*fast_pacing*`
3. Attach only the missing `downstream_episode_pacing_hint` surface.
4. Mirror the TR hint into BI plot roadmap without changing block meaning.
5. Do not add `B071+`.
6. Do not change S2, runtime code, or strict normalization repair.

## 8. Attachment Audit

Every attachment must produce an audit with:

- pair identity
- authority files read
- `TR coverage count`
- `BI mirror count`
- `TR/BI mismatch count`
- `missing block ids`
- JSON parse result
- UTF-8 hygiene result
- `B071+` check
- preservation note for existing pacing/payoff surfaces
- three adversarial passes:
  - pass 1: range too wide or too vague
  - pass 2: reward engine drift
  - pass 3: TR/BI sync and authority drift

PASS requires:

- all live TR blocks covered
- all live BI roadmap blocks mirrored
- mismatch count `0`
- no missing block ids
- no generic `fast enough` or `good rhythm` wording
- no `5+` recommendation without explicit structural justification

## 9. Registry Closeout

After PASS:

- set the row's `range_attachment_status` to `range_complete`
- record `downstream_episode_pacing_hint_artifact`
- record a compact `pacing_hint_surface` object:
  - `tr`
  - `bi`
  - `coverage`
  - `audit`

Before PASS:

- keep `range_attachment_status: pending_downstream_episode_pacing_hint_attachment`
- do not call the row range-complete immediate-use material

## 10. Return-To-Sender Smells

Reject or hold if:

- every block blindly says `2-6`
- every block blindly says `2-3` without block-specific reason
- range reason only repeats plot summary
- proof, receipt, and next gate are not named
- social/family recognition replaces the rights/control/cash/status receipt
- TR and BI disagree
- attachment changes core TR/BI plot content instead of adding the hint surface

## 11. One-Line Rule

`Range is a throttle, not decoration.`
