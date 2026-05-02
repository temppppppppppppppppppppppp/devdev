# distressed_company_buyer Range Attachment Consistency 1-Pass Audit

Date: 2026-05-02
Status: PASS
Scope: 1-pass consistency check after downstream episode pacing hint attachment

## 1. Target

- TR: `treatments/distressed_company_buyer_tr_block_070_draft.json`
- BI: `bible/0_bi_distressed_company_buyer.json`
- attachment audit: `treatments/audit_reports/distressed_company_buyer_downstream_episode_pacing_hint_attachment_audit.md`
- registry JSON: `material_ssot/00_governance/production-pair-operational-registry-v1.json`
- registry MD: `material_ssot/00_governance/production-pair-operational-registry-v1.md`

This is a one-pass consistency audit only. It does not replace the attachment audit's 3-pass closeout.

## 2. Consistency Result

| check | result |
| --- | --- |
| JSON parse | PASS |
| TR block count | `70` |
| BI plot_roadmap count | `70` |
| TR downstream hint coverage | `70/70` |
| BI downstream hint mirror coverage | `70/70` |
| TR/BI downstream hint mismatch | `0` |
| missing TR block ids | `0` |
| missing BI block ids | `0` |
| hint minimum shape missing count | `0` |
| vague wording ids | `0` |
| B071+ | absent |
| UTF-8 hygiene | PASS |
| pair consumability | PASS |
| normalization | `schema=pass`, `tierA=pass`, `tierB=normalized`, `migration_debt=no` |

Range distribution remains non-uniform:

- recommended `2`: `27`
- recommended `3`: `42`
- recommended `4`: `1`
- acceptable `2-3`: `44`
- acceptable `3-4`: `26`

## 3. Preservation Check

Existing 70/70 surfaces remain present:

- TR `webnovel_pacing_contract`: `70/70`
- BI `webnovel_pacing_contract`: `70/70`
- TR `reader_payoff_ladder`: `70/70`
- BI `reader_payoff_ladder`: `70/70`
- `MasterBible.BIAmplificationPower.webnovel_growth_reward_engine`: present

Recognition/reward top-3 cadence is not overwritten by the new range field.

## 4. Registry Check

Registry JSON for `distressed_company_buyer`:

- `range_attachment_status`: `range_complete`
- `downstream_episode_pacing_hint_artifact`: `treatments/audit_reports/distressed_company_buyer_downstream_episode_pacing_hint_attachment_audit.md`
- `pacing_hint_surface.audit`: `treatments/audit_reports/distressed_company_buyer_downstream_episode_pacing_hint_attachment_audit.md`

Registry MD:

- row says `range-complete immediate material`
- update log references the distressed-company attachment audit

## 5. Verdict

PASS.

The downstream episode pacing hint surface is consistent across TR, BI, registry JSON, registry MD, and the attachment audit. No corrective patch is required.
