# distressed_company_buyer Downstream Episode Pacing Hint Attachment Audit

Date: 2026-05-02
Status: PASS
Work ID: `distressed_company_buyer`
Scope: existing Phase0 / work_guard / TR 70 / BI 70 pair only

## 1. Pair Identity

- TR: `treatments/distressed_company_buyer_tr_block_070_draft.json`
- BI: `bible/0_bi_distressed_company_buyer.json`
- Phase0: `treatments/phase0/distressed_company_buyer_phase0_design.json`
- work_guard: `work_guards/distressed_company_buyer.yaml`
- family: `blockguide`
- operational state: `regenerated_pair`
- existing immediate deployment closeout: `treatments/audit_reports/distressed_company_buyer_immediate_deployment_adversarial_closeout.md`

## 2. Authority Files Read

- `material_ssot/README.md`
- `material_ssot/00_governance/stage-read-order.md`
- `material_ssot/00_governance/production-pair-operational-registry-v1.md`
- `material_ssot/00_governance/production-pair-operational-registry-v1.json`
- `docs/2026-04-29/material-side-immediate-deployment-overlay.md`
- `material_ssot/00_governance/production-pair-benchmark-spec-v1.md`
- `material_ssot/00_governance/production-pair-operating-policy-addendum-v1.md`
- `material_ssot/00_governance/downstream-episode-pacing-hint-attachment-harness-v1.md`
- `docs/narrative-router/SSOT_narrative-router-integrated-order.md`
- `AGENTS.narrative-router.md`
- `전처리_ssot/docs/blockguide/SSOT_blockguide-integrated-order.md`
- `docs/narrative-router/material-revival-ladder-harness.md`
- `material_ssot/50_tr/work-index/distressed_company_buyer.md`
- `material_ssot/60_bi/work-index/distressed_company_buyer.md`
- `treatments/phase0/distressed_company_buyer_phase0_design.json`
- `work_guards/distressed_company_buyer.yaml`
- `treatments/distressed_company_buyer_tr_block_070_draft.json`
- `bible/0_bi_distressed_company_buyer.json`
- `treatments/audit_reports/distressed_company_buyer_fast_webnovel_pacing_contract_audit.md`
- `treatments/audit_reports/distressed_company_buyer_blockwise_success_reward_expectation_3pass_audit.md`
- `treatments/audit_reports/distressed_company_buyer_immediate_deployment_adversarial_closeout.md`

## 3. Attachment Surface

Added only the canonical downstream range surface:

- `TR.blocks[*].genre_ext.downstream_episode_pacing_hint`
- `MasterBible.plot_roadmap[*].genre_ext.downstream_episode_pacing_hint`
- optional BI policy summary: `MasterBible.BIAmplificationPower.downstream_episode_pacing_hint_policy`

The range decision axis is fixed per block as:

`company pressure -> liability/proof -> acquisition/right move -> same-block receipt -> next company gate`

Range distribution:

| recommended | count |
| --- | ---: |
| `2` | 27 |
| `3` | 42 |
| `4` | 1 |

| acceptable range | count |
| --- | ---: |
| `2-3` | 44 |
| `3-4` | 26 |

This is not a uniform range stamp. Compact operating beats stay at `2-3`; legal, financing, or multi-party pressure beats use `3-4`; final launch close uses recommended `4`.

## 4. Validation

Fresh validation after attachment:

| check | result |
| --- | --- |
| JSON parse | PASS |
| TR block count | `70` |
| BI plot_roadmap count | `70` |
| TR coverage count | `70/70` |
| BI mirror count | `70/70` |
| TR/BI mismatch count | `0` |
| missing block ids | `0` |
| extra block ids | `0` |
| UTF-8 byte decode | PASS |
| UTF-8 hygiene script | PASS |
| B071+ check | PASS |
| BI/TR consumability | PASS |
| production pair normalization | `schema=pass`, `tierA=pass`, `tierB=normalized`, `migration_debt=no` |

Validation commands:

```bash
python -X utf8 scripts/check_utf8_hygiene.py treatments/distressed_company_buyer_tr_block_070_draft.json bible/0_bi_distressed_company_buyer.json
python -X utf8 scripts/check_bi_tr_consumability.py --bible bible/0_bi_distressed_company_buyer.json --treatment treatments/distressed_company_buyer_tr_block_070_draft.json --json
python -X utf8 scripts/production_pair_normalization_runner.py --bible bible/0_bi_distressed_company_buyer.json --treatment treatments/distressed_company_buyer_tr_block_070_draft.json --state regenerated_pair --json
```

Custom attachment sync check:

- `TR_HINT_COVERAGE 70 / 70`
- `BI_HINT_COVERAGE 70 / 70`
- `TR_BI_HINT_MISMATCH_COUNT 0`
- `MISSING_HINT_BLOCK_IDS []`
- `B071_PLUS_CHECK PASS`

## 5. Preservation Note

Preserved existing 70/70 pacing and payoff surfaces:

- `TR.blocks[*].genre_ext.webnovel_pacing_contract`: `70/70`
- `MasterBible.plot_roadmap[*].genre_ext.webnovel_pacing_contract`: `70/70`
- `TR.blocks[*].genre_ext.reader_payoff_ladder`: `70/70`
- `MasterBible.plot_roadmap[*].genre_ext.reader_payoff_ladder`: `70/70`
- `MasterBible.BIAmplificationPower.webnovel_growth_reward_engine`: present
- `MasterBible.BIAmplificationPower.webnovel_fast_pacing_engine`: present

Recognition/reward top-3 cadence was not rewritten. The new range surface points to rights/control/cash/status receipts and next company gates; it does not force praise or family/social recognition into every block.

## 6. Three-Pass Audit

### Pass 1 - Range Width Attack

Attack: The new hints may be too wide, vague, or uniformly stamped.

Result: PASS.

The attached hints use block-specific basis anchors from the existing `webnovel_pacing_contract`: pressure, liability/proof, right move, same-block receipt, and next gate. Distribution is mixed: `2`, `3`, and `4` recommended counts, with `2-3` and `3-4` acceptable ranges. No block recommends `5+`, and every hint names a concrete over-expansion smell in `do_not_expand_to`.

### Pass 2 - Reward Engine Drift Attack

Attack: The range surface may replace the distressed-company rights-bundle reward engine with generic pacing advice.

Result: PASS.

Each hint keeps the same operating loop already proven by the fast pacing audit: company pressure, present proof, right move, same-block receipt, and next company gate. Rewards remain meeting seat, data-room access, insurance/legal recognition, priority right, SPV/mandate, escrow/cashflow, certificate, or next data-room. Social recognition does not replace the operating receipt.

### Pass 3 - TR/BI Sync And Authority Drift Attack

Attack: TR and BI may disagree, or the new BI policy may drift from Phase0/work_guard/TR authority.

Result: PASS.

The TR hint object is mirrored into the matching BI plot_roadmap block with mismatch count `0`. Missing block ids are `0`. Phase0 and work_guard already define one TR block as a downstream `2~6` episode bundle with same-block receipt, and the new hints narrow that advisory range without changing S2, runtime schema, or the existing 70/70 `webnovel_pacing_contract`.

## 7. Final Ruling

PASS.

`distressed_company_buyer` now has downstream episode pacing hints at the canonical TR and BI paths with complete 70/70 coverage, zero TR/BI mismatches, zero missing block ids, UTF-8 hygiene PASS, and B071+ absent.

Registry closeout is authorized:

- set `range_attachment_status` to `range_complete`
- record `downstream_episode_pacing_hint_artifact`
- record `pacing_hint_surface`

Confidence: `97/100`.
