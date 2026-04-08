# Pair 01 GREENPLUS Adjudication Checklist

Date: 2026-04-08
Status: resolved on 2026-04-08
Scope: historical working checklist used before the strict re-benchmark closeout

## 1. Role

Use this checklist before doing any broad rewrite on pair `01`.

The starting situation was split:

- `docs/2026-04-07/wave3_pair01_greenplus_audit_report.md` already argued `GREENPLUS`
- `material_ssot/00_governance/production_pair_grade_aliases/GREENPLUS_투자물_골든_카나리아 테스트_canonical_v1.md` now records the promoted live alias
- `docs/2026-04-08/production-pair-benchmark-freshness-wave.md` says the pair is benchmark-fresh, but conservatively kept below the `GREENPLUS` shelf

Outcome:

- `docs/2026-04-08/pair01-strict-rebenchmark-greenplus-report.md` resolved the adjudication in favor of `GREENPLUS`

## 2. Authority Stack

Primary decision documents:

- `material_ssot/00_governance/production-pair-benchmark-spec-v1.md`
- `material_ssot/00_governance/production-pair-operating-policy-addendum-v1.md`
- `material_ssot/00_governance/production-pair-operational-registry-v1.md`

Current pair surfaces:

- `treatments/01_tr_투자물_골든_카나리아 테스트_canonical_v1.json`
- `bible/01_bi_투자물_골든_카나리아 테스트_canonical_v1.json`

Historical benchmark evidence:

- `docs/2026-04-07/10pair_true_benchmark_terminal01_pair01_report.md`
- `docs/2026-04-07/wave3_pair01_greenplus_audit_report.md`
- `docs/2026-04-08/production-pair-benchmark-freshness-wave.md`

## 3. Current Working Read

Current live pair facts already confirmed:

- normalization status: `pass`
- full-block cider scan: `60/60 has_cider:true`
- no open schema migration debt
- early opening still carries the same concrete token chain described in the wave3 audit:
  - `B2` VIP line
  - `B3` exception account
  - `B4` seat / internal name-call approval
  - `B6` priority response list

Current likely bottleneck:

- the live `TR` now has receipts everywhere, but some `genre_ext.block_cider.receipt_line` values are still generic and may under-report how strong the same-block authority/status token really is
- the live `BI` still carries the wave3 amplification surfaces, but they sit under `MasterBible.ProjectData.CommercialCode`, so the operator shelf can still read the pair conservatively unless the benchmark artifact reasserts them clearly

Implication:

- do not start with large prose edits
- do not assume the pair still needs structural surgery
- first decide whether the current live pair already clears `GREENPLUS` under a fresh strict read

## 4. Phase 1: Strict Re-Benchmark First

Run a fresh read-only benchmark against the current live pair and answer only these questions:

1. does `P0` still pass `6/6` under the current files
2. is any `YELLOW` or `GREEN` cap still legitimately active
3. is the current `P1` total still `17~20`
4. does the current evidence still justify "block 1 is an exemplar of proof -> reevaluation -> reward -> next gate"

Required audit discipline:

- use `TR blocks 2~6` only for the opening gate proofs
- do not rescue a weak opening with `block 7+`
- do not use `work_guard` as the main proof for gate 6
- name exact `TR` anchors for every `P0` gate
- re-run the full-block cider scan over all `60` blocks

Decision outputs:

- `A. direct GREENPLUS`
- `B. GREEN because early reward is still read as asset-first`
- `C. GREEN because BI amplification still reads as too indirect`
- `D. GREEN because both B and C remain true`

If output is `A`, skip straight to Phase 4.

## 5. Phase 2: Canonical Evidence Sharpening Only

If the strict re-benchmark returns `B`, `C`, or `D`, start here before editing story payload.

### 5.1 TR evidence targets

Check `genre_ext.block_cider` on the opening blocks first:

| Block | same-block token that must remain legible | preferred receipt reading |
| --- | --- | --- |
| `B2` | VIP direct line opening | `direct_line` / internal line opening |
| `B3` | exception account / protocol exception | `exception_record` or protocol ownership |
| `B4` | seat or named internal approval | `seat_or_name_call` |
| `B5` | governance-tier wobble only | governance receipt, not a fake big win |
| `B6` | international entry ticket | `entry_ticket` / priority list access |

Working rule:

- if the reward paragraph is already strong but `block_cider.receipt_line` is too generic, sharpen the canonical receipt line first
- keep the same event, same chronology, same payoff
- prefer naming the authority/status token already present in the block over inventing a new token

### 5.2 BI evidence targets

The current live BI must be re-read through these fields:

- `MasterBible.ProjectData.CommercialCode.observer_tier_ladder`
- `MasterBible.ProjectData.CommercialCode.early_reward_token_contract`
- `MasterBible.ProjectData.CommercialCode.cider_ladder_per_window`

Benchmark-use question:

- do these fields materially sharpen the live `TR`, or are they merely restating what the `TR` already says

If the answer still feels ambiguous to an external auditor, the next benchmark artifact must explicitly map:

- `observer_tier_ladder tier_1` -> `B2/B3/B4/B5/B6`
- `early_reward_token_contract token_anchor_blocks` -> `B2/B3/B4/B6`
- `cider_ladder_per_window window_1_to_10` -> the current opening promise and downstream reward cadence

## 6. Phase 3: Only If Real Repair Is Still Needed

Touch prose only if Phase 2 still leaves the pair at `GREEN`.

Allowed repair shape:

- one-line same-block sharpening inside an existing `reward` field
- one-line same-block sharpening inside an existing `power_shift` field
- clarification inside `genre_ext.block_cider.receipt_line`

Forbidden repair shape:

- new macro event
- new outside savior
- chronology shift
- asset number rewrite
- replacing an authority token with a mere mood beat
- using `block 7+` to rescue `block 2~6`

Priority order if prose edits are still necessary:

1. `B2/B3/B4/B6`
2. `B5`
3. only then any later-window polishing

## 7. Promotion Closeout

If a fresh strict benchmark now justifies `GREENPLUS`, close the wave in this order:

1. write a new benchmark artifact for pair `01`
2. update or replace the alias record as `material_ssot/00_governance/production_pair_grade_aliases/GREENPLUS_투자물_골든_카나리아 테스트_canonical_v1.md`
3. refresh the alias index in `production_pair_grade_aliases/README.md`
4. update `material_ssot/00_governance/production-pair-operational-registry-v1.json`
5. update `material_ssot/00_governance/production-pair-operational-registry-v1.md`
6. update the pair note in `material_ssot/00_governance/production-pair-benchmark-spec-v1.md`
7. update `docs/2026-04-08/production-pair-benchmark-freshness-wave.md` so the 2026-04-08 operator shelf no longer describes pair `01` as below `GREENPLUS`

## 8. Guardrails

Do not lose these truths while chasing the higher grade:

- pair `01` is already schema-clean and benchmark-fresh
- the current live pair already has zero no-cider blocks
- the goal is not "more hype"
- the goal is "clearer proof that the current pair meets the published `GREENPLUS` contract"

Operator rule:

- if the pair still needs more than targeted opening-token sharpening after Phase 2, stop and re-evaluate whether the shelf disagreement is actually policy conservatism rather than pair weakness

## 9. Exit Criteria

The plan is complete only when one of these is true:

- `01` is freshly re-benchmarked and formally promoted to `GREENPLUS`, or
- a fresh benchmark artifact explains, with exact cap language, why the pair still remains `GREEN`

Anything weaker than that leaves the shelf disagreement unresolved.
