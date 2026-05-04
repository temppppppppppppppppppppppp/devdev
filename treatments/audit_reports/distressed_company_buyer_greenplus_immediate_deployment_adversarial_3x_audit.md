# distressed_company_buyer GREENPLUS Immediate Deployment Adversarial 3x Audit

Date: 2026-05-02
Status: PASS
Work ID: `distressed_company_buyer`
Scope: current Phase0 / work_guard / TR 70 / BI 70 / registry promotion surface

Forbidden actions respected:

- no B071 generation
- no second BI generation
- no episode or manuscript packet generation
- no blanket promotion of other `GREENPLUS` rows
- no replacement claim against `golden_canary_deepclone_probe_a_fullblock_v1`

## 1. Current Claim Under Attack

Claim being attacked:

- `GREENPLUS`
- P0 hard gates: `6/6`
- P1 score: `20/20`
- full-block cider: `70/70`
- opening pacing triage: `GREEN`
- whole-run pacing triage: `GREEN`
- immediate material deployment: `PASS`

The attacker assumption for this audit is that the promotion may be a false positive caused by schema looseness, benchmark over-reading, or deployment overclaim.

## 2. Evidence Snapshot

Fresh validation commands passed during this audit:

- `python -X utf8 scripts/audit_bi_5pass.py --phase0 treatments/phase0/distressed_company_buyer_phase0_design.json --draft treatments/distressed_company_buyer_tr_block_070_draft.json --bi bible/0_bi_distressed_company_buyer.json --report treatments/preprocess/distressed_company_buyer/03_tr_blocks/bi_5pass_audit.md`
- `python -X utf8 scripts/check_bi_tr_consumability.py --bible bible/0_bi_distressed_company_buyer.json --treatment treatments/distressed_company_buyer_tr_block_070_draft.json`
- `python -X utf8 scripts/production_pair_normalization_runner.py --bible bible/0_bi_distressed_company_buyer.json --treatment treatments/distressed_company_buyer_tr_block_070_draft.json --state regenerated_pair`
- `python -X utf8 scripts/production_pair_opening_pacing_triage_runner.py --treatment treatments/distressed_company_buyer_tr_block_070_draft.json --json`
- `python -X utf8 scripts/production_pair_whole_run_pacing_triage_runner.py --treatment treatments/distressed_company_buyer_tr_block_070_draft.json --json`
- `python -X utf8 scripts/block_continuity_checker.py --work-id distressed_company_buyer --family blockguide`

Observed evidence:

- BI 5-pass: `PASS`
- BI meta leak count: `0`
- consumability: `pair=pass`, `canonical=pass`, `normalized=pass`, `blocks=70`
- normalization: `schema=pass`, `tierA=pass`, `tierB=normalized`, `evidence=serialized_canonical`, `migration_debt=no`
- opening pacing: `GREEN`, declared contract, signboard `B02`, reevaluation `B02`, ticket `B02`, reader-earning signal `B02`
- whole-run pacing: `GREEN`, no late blank-opponent blocks, no endgame low-stakes blocks, no slow windows
- continuity checker: `CLEAN`

## 3. Adversarial Audit 1 - Contract/Schema Attack

Attack questions:

- Did the BI amplification section create a schema or meta-text false pass?
- Did it desynchronize `MasterBible.plot_roadmap` from the TR?
- Did the pair remain canonical under the normalization runner?
- Did any hidden B071 or second-BI surface appear?

Findings:

- The earlier BI amplification wording that used literal numbered block labels inside the BI would have failed the BI meta-leak gate. The current BI no longer uses that numbered-block wording in the amplification ladder.
- Current BI 5-pass reports `bi_diegetic_meta_leak_count: 0` and all five passes `OK`.
- Pair consumability and normalization both pass after the BI amplification edit.
- The amplification section does not touch `plot_roadmap`; TR/BI roadmap sync remains anchored by the existing 70-block roadmap.

Verdict: PASS.

No contract blocker remains.

## 4. Adversarial Audit 2 - Benchmark/Reader-Reward Attack

Attack questions:

- Is `20/20` merely a prestige rewrite after a `19/20` audit?
- Does `BIAmplificationPower` actually add usable editorial force?
- Does the opening still pay inside the strict `TR 2~6` window?
- Does the late run preserve same-block receipts?

Findings:

- The upgraded BI section adds a commercial thesis, episode kernel, rights-bundle dictionary, receipt escalation ladder, anti-flattening rules, and scene-close reward checks.
- This is materially more than TR summarization; it tells a writer how to keep every scene paid through rights, debt order, cashflow, and control receipt.
- Opening pacing remains `GREEN`: first public signboard, representative reevaluation, next-battlefield ticket, and reader-earning signal all land at `B02`.
- Whole-run pacing remains `GREEN`; no late blank-opponent blocks, endgame low-stakes blocks, or slow windows were reported.
- Full-block cider claim remains supported by the existing 70/70 canonical `block_cider` surface and no no-cider regression was found.

Verdict: PASS.

`P1 20/20` is supportable after BI amplification. It is still a benchmark-material claim, not manuscript runtime proof.

## 5. Adversarial Audit 3 - Deployment/Overclaim Attack

Attack questions:

- Does immediate deployment overclaim beyond material-side authority?
- Does the row replace the donorized gold sample?
- Does this promotion accidentally open all `GREENPLUS` rows?
- Does donor adoption contaminate the native work surface?

Findings:

- The operational registry and overlay keep `distressed_company_buyer` as the third admitted immediate material-deployment row, not the gold-sample replacement.
- The closeout preserves the guard that non-promoted `GREENPLUS` rows remain benchmark/reference inventory until donor structure is separately applied, recorded, and closed.
- `BIAmplificationPower` uses native distressed-company rights-bundle language: certification rights, claim rights, route memory, debt order, and control receipt.
- No donor proper noun, family-name skin, fantasy UI, lottery/prophecy shortcut, charity-rescue drift, or illegal insider shortcut is used as the deployment basis.

Verdict: PASS.

Immediate deployment claim is bounded and safe.

## 6. Residual Risks

Residual risks are not blockers:

- This is not an episode/manuscript runtime proof.
- Downstream Geuldobi runtime probe remains a later boundary.
- `20/20` is a benchmark/material-side judgment; it should not be used as automatic proof that all generated episodes will preserve the same density without runtime QA.

## 7. Final Ruling

All three adversarial audits pass.

Final Director-style ruling:

- keep `GREENPLUS`
- keep `P1 20/20`
- keep immediate material-deployment status
- keep overclaim guard
- do not generate B071 or any new BI from this audit

Confidence: `97/100`.
