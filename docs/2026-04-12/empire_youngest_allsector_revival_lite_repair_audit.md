Date: 2026-04-12
Status: active
Scope: `empire_youngest_allsector` quarantine pair revival audit

## 1. Target Pair

- TR: `treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json`
- BI: `bible/_quarantine/0_bi_empire_youngest_allsector.json`
- Phase 0: `treatments/_quarantine/empire_youngest_allsector_phase0_design.json`
- Current preprocess pointer: `treatments/preprocess/empire_youngest_allsector/sequential_run_status.json`

Current pointer truth:

- `last_sequential_block_pass = 70`
- `next_unit_type = bi_handoff`
- `manual_audit_ready = true`
- `resume_basis = manual_audit_pass`

## 2. Step 1. Pair Consumability

Command:

```text
python -X utf8 scripts/check_bi_tr_consumability.py --bible bible/_quarantine/0_bi_empire_youngest_allsector.json --treatment treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json --json
```

Result:

- `pair_consumability = pass`
- `bi_canonical_contract = pass`
- `tr_canonical_contract = pass`
- `normalized_pair_canonical_view = pass`
- `canonical_block_count = 70`
- runtime protagonist required keys: no missing keys

Interpretation:

- this pair is still ingestible by the current harness
- current work should not start with schema rescue
- the next judgment step is narrative spine quality, not contract normalization

## 3. Step 2. TR Static Audit Verdict

Verdict:

- `usable spine but mixed`

Why this is not `regenerate TR first`:

- full `70` blocks exist
- BI roadmap title chain matches the current TR title chain exactly (`70/70`)
- sector spread remains visible across the run
- explicit `genre_ext.opponent` objects are still present in all sampled late blocks
- late callback / foreshadow carry still survives through `B66~B70`

Why this is not `strong spine`:

- opening pacing triage on the current quarantine TR returns `RED` under `legacy_heuristic`
- whole-run pacing triage on the current quarantine TR returns `YELLOW`
- opening contract declaration is still absent as a declared field layer
- `B09`, `B10` still expose weak immediate-stakes presentation
- late endgame closes active resistance too early by collapsing multiple blocks into `없음` opponent states

Evidence:

- opening triage:
  - `triage_grade = RED`
  - `trigger_codes = [LEGACY-MACRO-OVERSTAY, LEGACY-SIGNBOARD-LATE]`
  - `first_public_signboard_block = 9`
  - `next_battlefield_ticket_block = null`
- whole-run triage:
  - `triage_grade = YELLOW`
  - `late_blank_opponent_blocks = [66, 68, 69, 70]`
  - `endgame_low_stakes_blocks = [66, 67, 68, 69]`
- manual spot check:
  - `B09 stakes = None`
  - `B10 stakes = None`
  - `B66 opponent = 없음(이미 제압)`
  - `B68 opponent = 없음`
  - `B69 opponent = 없음`

## 4. Step 2A. Lite Repair Audit

Default conclusion:

- do not enter full-wave surgery
- do not rebuild the entire TR
- run one bounded repair unit at a time

### Repair Unit 1

- Unit: `opening contract + public signboard repair`
- Blocks: `B02~B04`
- Cascade range: `B01~B10`
- Reason:
  - current opening reads as macro-overstay until `B09`
  - the pair needs an earlier visible contract declaration and battlefield ticket so opening discard risk is removed without changing the whole opening structure

### Repair Unit 2

- Unit: `late opposition carry restoration`
- Blocks: `B66, B68, B69`
- Cascade range: `B66~B70`
- Reason:
  - `phase3` opponent plan says `Citadel Capital + 채권단` should dominate `49~70`
  - current late blocks convert pressure into `없음` too early
  - the endgame needs residual institutional resistance or cost visibility, not blank-victory drift

### Repair Unit 3

- Unit: `opening crossover stakes restore`
- Blocks: `B09~B10`
- Cascade range: `B09~B12`
- Reason:
  - `B09`, `B10` currently lose immediate downside presentation right at the first sector completion pivot
  - this weakens the reader-earning ladder even if the macro opening contract is repaired

Recommended order:

1. Repair Unit 1
2. Repair Unit 2
3. Repair Unit 3

## 5. Execution Update

Executed on `2026-04-12`:

- `Repair Unit 1` completed
  - action: `B01~B10` declared opening contract layer added
  - result: opening pacing triage `GREEN`
  - evidence:
    - `evidence_mode = declared_contract`
    - `first_public_signboard_block = 2`
    - `representative_reevaluation_block = 3`
    - `next_battlefield_ticket_block = 2`
- `Repair Unit 2` completed
  - action: `B66~B69` opponent/cost carry restoration
  - result: whole-run pacing triage `GREEN`
  - evidence:
    - `late_blank_opponent_blocks = [70]`
    - `endgame_low_stakes_blocks = []`
- pair consumability recheck after repair:
  - `pair_consumability = pass`
  - `normalized_pair_canonical_view = pass`
- `legacy phase0 compatibility normalization` completed
  - action:
    - added `phase0_design.npc_timeline`
    - added `phase0_design.foreshadow_map`
    - added `phase0_design.partner_location_sector_distribution`
    - added missing arc-level `support_sectors`
  - result:
    - `build_bi_from_phase0_and_tr.py` probe now succeeds
    - probe output saved at `docs/temp/empire_youngest_allsector_bi_probe.json`
    - `plot_roadmap` hash sync = `OK`
- `bounded rehab wave 1` completed
  - action:
    - rewrote `B48`, `B49`, `B51`, `B69`
    - expanded stakes / consequence language
    - restored `B51` recognition signal
    - reduced local diegetic block-reference phrasing in touched callback / foreshadow text
  - result:
    - `critical_thin_blocks = []`
    - `recognition_signal_blocks = 21`
    - `max_recognition_gap_streak = 13`
    - fresh BI probe still `FAIL`, but the fail cluster is narrower and no longer includes thin / recognition-gap blockers
- `bounded rehab wave 2` completed
  - action:
    - rewrote `B44`, `B45`, `B47`
    - expanded short stakes into full downside/cost sentences
    - removed local `Bxx/Block xx` references from touched callback / foreshadow / future-prep text
    - replaced the explicit `Block 46` narrative aside inside `B45 reward` with diegetic carry language
  - result:
    - `short_stakes_blocks` no longer include `44`, `45`, `47`
    - current `short_stakes_blocks = [9, 10, 40, 53, 54, 55, 59, 60, 63, 64]`
    - `diegetic_meta_ref_count = 556`
    - fresh BI probe still `FAIL`, but the remaining short-stakes cluster has moved forward to `B53~B55` and later
- `bounded rehab wave 3` completed
  - action:
    - rewrote `B53`, `B54`, `B55`
    - expanded the `SMR / family-pressure / defense-drone` stakes layer
    - removed local `Bxx/Block xx` references from touched callback / foreshadow / future-prep text
  - result:
    - `short_stakes_blocks` no longer include `53`, `54`, `55`
    - current `short_stakes_blocks = [9, 10, 40, 59, 60, 63, 64]`
    - `diegetic_meta_ref_count = 535`
- `bounded rehab wave 4` completed
  - action:
    - rewrote `B59`, `B60`, `B63`, `B64`
    - expanded late-run stakes into full downside/cost sentences
    - added missing top-level stakes authority to `B09`, `B10`
    - expanded `B40` stakes so the early LP-failure risk reads as a real fund-loss gate
  - result:
    - `short_stakes_blocks = []`
    - `critical_thin_blocks = []`
    - `recognition_signal_blocks = 21`
    - `max_recognition_gap_streak = 13`
    - `diegetic_meta_ref_count = 508`
    - fresh BI probe still `FAIL`, but the short-stakes lane is now fully closed
- `bounded rehab wave 5` completed
  - action:
    - backfilled `genre_ext.block_cider` across the full run
    - normalized all `genre_ext.section_rotation` values into numberless natural-language labels
    - rebuilt the fresh BI probe and reran the 5-pass audit
  - result:
    - `block_cider_missing_blocks = []`
    - `no_cider_blocks = []`
    - `cider_receipt_line_missing_blocks = []`
    - `label_meta_ref_count = 0`
    - `hard_gate_failures = ['diegetic_meta_ref_zero', 'diegetic_block_ref_zero']`
    - fresh BI probe still `FAIL`, but the remaining blocker set is now limited to diegetic meta / block refs and NPC continuity
- `bounded rehab wave 6` completed
  - action:
    - rewrote all `regression_ext.future_prep.target_event` entries that used `Block/Bxx` references
    - replaced explicit block-number pointers with direct upcoming-event title carry
    - rebuilt the fresh BI probe and reran the 5-pass audit
  - result:
    - `diegetic_meta_ref_count = 450`
    - `diegetic_block_ref_count(alias) = 450`
    - `label_meta_ref_count = 0`
    - `npc_continuity_mismatch_count = 51`
    - fresh BI probe still `FAIL`, but the `future_prep.target_event` lane is now substantially cleaner
- `bounded rehab wave 7` completed
  - action:
    - rewrote the remaining low-count `content.context` / `content.reward` meta references
    - removed the obvious `Block 1` diegetic meta strings from `opponent.name`, `suspicion_from`, and `execution_doctrine`
    - rebuilt the fresh BI probe and reran the 5-pass audit
  - result:
    - `diegetic_meta_ref_count = 438`
    - `diegetic_block_ref_count(alias) = 438`
    - `label_meta_ref_count = 0`
    - `unresolved_foreshadow_count = 44`
    - `npc_continuity_mismatch_count = 51`
    - fresh BI probe still `FAIL`, but the low-risk context/reward lane is now cleaner without reopening the unresolved-foreshadow gate
- `bounded rehab wave 8` completed
  - action:
    - rewrote the `foreshadow` family to remove inline `Block/Bxx` references while preserving the natural-language meaning
    - normalized range references like `Block 3~4` / `Block 8~9` into non-numeric diegetic phrasing
    - rebuilt the fresh BI probe and reran the 5-pass audit
  - result:
    - `diegetic_meta_ref_count = 300`
    - `diegetic_block_ref_count(alias) = 300`
    - `label_meta_ref_count = 0`
    - `unresolved_foreshadow_count = 1`
    - `npc_continuity_mismatch_count = 51`
    - fresh BI probe still `FAIL`, but the foreshadow lane is now substantially cleaner and no longer the dominant unresolved-risk source
- `bounded rehab wave 9` completed
  - action:
    - added `callback_sources` across callback-bearing blocks so callback resolution is carried by explicit metadata
    - rewrote the `callback` family to remove inline `Block/Bxx` references while preserving callback meaning
    - rebuilt the fresh BI probe and reran the 5-pass audit
  - result:
    - `diegetic_meta_ref_count = 141`
    - `diegetic_block_ref_count(alias) = 141`
    - `label_meta_ref_count = 0`
    - `unresolved_foreshadow_count = 2`
    - `callback_ratio = 1.1`
    - `npc_continuity_mismatch_count = 51`
    - fresh BI probe still `FAIL`, but the callback lane is now substantially cleaner and no longer the dominant blocker
- `bounded rehab wave 10` completed
  - action:
    - normalized `relationship_delta.before` across the continuity-mismatch set so each block starts from the actual previous `after` state
    - kept the repaired TR as the authority source and rebuilt the fresh BI probe
    - reran the 5-pass audit after the continuity normalization
  - result:
    - `diegetic_meta_ref_count = 118`
    - `diegetic_block_ref_count(alias) = 118`
    - `label_meta_ref_count = 0`
    - `unresolved_foreshadow_count = 2`
    - `npc_continuity_mismatch_count = 0`
    - `callback_ratio = 1.1`
    - fresh BI probe still `FAIL`, but the NPC continuity lane is now closed
- `bounded rehab wave 11` completed
  - action:
    - rewrote the `future-knowledge` family in the live TR, focusing on `genre_ext.knowledge_used`, `regression_ext.timeline_knowledge.info_used`, and `regression_ext.future_prep.action`
    - replaced inline `Block/Bxx` references with carried event meaning so the future-knowledge lane reads diegetically inside the generated BI
    - kept the normalized phase0 as authority, rebuilt the fresh BI probe, and reran the 5-pass audit
  - result:
    - `diegetic_meta_ref_count = 102`
    - `diegetic_block_ref_count(alias) = 102`
    - `label_meta_ref_count = 0`
    - `unresolved_foreshadow_count = 2`
    - `npc_continuity_mismatch_count = 0`
    - `bi_diegetic_meta_leak_count = 114`
    - fresh BI probe still `FAIL`, but the future-knowledge lane is no longer the dominant BI-side leak source
- `bounded rehab wave 12` completed
  - action:
    - rewrote the `plot_roadmap.relationship_delta.before` lane to carry prior-state meaning without inline `Block/Bxx` references
    - rebuilt the fresh BI probe and checked the remaining relationship-before family directly
    - confirmed the targeted `before` lane itself is now numerically clean
  - result:
    - `plot_roadmap.relationship_delta.before = 0` by direct family check
    - `diegetic_meta_ref_count = 102`
    - `diegetic_block_ref_count(alias) = 102`
    - `label_meta_ref_count = 0`
    - `unresolved_foreshadow_count = 2`
    - `npc_continuity_mismatch_count = 0`
    - `bi_diegetic_meta_leak_count = 114`
    - fresh BI probe still `FAIL`, and this wave showed that `relationship_delta.before` was not the dominant counted BI-side leak family
- `bounded rehab wave 13` completed
  - action:
    - rewrote the `plot_roadmap.genre_ext.leverage_used[]` lane to carry prior-event meaning without inline `Block/Bxx` references
    - fixed the single continuity regression exposed during the rebuild by syncing the matching `relationship_delta.after` carry for `정하윤`
    - rebuilt the fresh BI probe, reran the 5-pass audit, and rechecked continuity metrics
  - result:
    - `plot_roadmap.genre_ext.leverage_used[] = 0` by direct family check
    - `diegetic_meta_ref_count = 83`
    - `diegetic_block_ref_count(alias) = 83`
    - `label_meta_ref_count = 0`
    - `unresolved_foreshadow_count = 2`
    - `npc_continuity_mismatch_count = 0`
    - `bi_diegetic_meta_leak_count = 96`
    - fresh BI probe still `FAIL`, but the leverage-used lane is now closed and the residual BI-side leak cluster is visibly smaller
- `bounded rehab wave 14` completed
  - action:
    - rewrote the `plot_roadmap.power_shift.antagonist` lane to carry escalation meaning without inline `Block/Bxx` references
    - rebuilt the fresh BI probe, reran the 5-pass audit, and directly rechecked the targeted antagonist family
  - result:
    - `plot_roadmap.power_shift.antagonist = 0` by direct family check
    - `diegetic_meta_ref_count = 83`
    - `diegetic_block_ref_count(alias) = 83`
    - `label_meta_ref_count = 0`
    - `unresolved_foreshadow_count = 2`
    - `npc_continuity_mismatch_count = 0`
    - `bi_diegetic_meta_leak_count = 96`
    - fresh BI probe still `FAIL`, and this wave confirmed that `power_shift.antagonist` was not a headline-dominant counted BI leak family
- `bounded rehab wave 15` completed
  - action:
    - rewrote the `plot_roadmap.genre_ext.success_pattern` lane to carry result meaning without inline `Block/Bxx` references
    - rebuilt the fresh BI probe, reran the 5-pass audit, and directly rechecked the targeted success-pattern family
  - result:
    - `plot_roadmap.genre_ext.success_pattern = 0` by direct family check
    - `diegetic_meta_ref_count = 77`
    - `diegetic_block_ref_count(alias) = 77`
    - `label_meta_ref_count = 0`
    - `unresolved_foreshadow_count = 2`
    - `npc_continuity_mismatch_count = 0`
    - `bi_diegetic_meta_leak_count = 89`
    - fresh BI probe still `FAIL`, but the success-pattern lane is now fully closed
- `bounded rehab wave 16` completed
  - action:
    - rewrote the `plot_roadmap.genre_ext.opening_progression` lane to preserve opening-contract meaning without inline `Block/Bxx` references
    - rebuilt the fresh BI probe, reran the 5-pass audit, and directly rechecked the targeted opening-progression family
  - result:
    - `plot_roadmap.genre_ext.opening_progression = 0` by direct family check
    - `diegetic_meta_ref_count = 69`
    - `diegetic_block_ref_count(alias) = 69`
    - `label_meta_ref_count = 0`
    - `unresolved_foreshadow_count = 2`
    - `npc_continuity_mismatch_count = 0`
    - `bi_diegetic_meta_leak_count = 79`
    - fresh BI probe still `FAIL`, but the opening-progression lane is now fully closed
- `bounded rehab wave 17` completed
  - action:
    - rewrote the `plot_roadmap.regression_ext.death_flag` lane to preserve fatal-risk carry without inline `Block/Bxx` references
    - rebuilt the fresh BI probe, reran the 5-pass audit, and directly rechecked the targeted death-flag family
  - result:
    - `plot_roadmap.regression_ext.death_flag = 0` by direct family check
    - `diegetic_meta_ref_count = 67`
    - `diegetic_block_ref_count(alias) = 67`
    - `label_meta_ref_count = 0`
    - `unresolved_foreshadow_count = 2`
    - `npc_continuity_mismatch_count = 0`
    - `bi_diegetic_meta_leak_count = 77`
    - fresh BI probe still `FAIL`, but the death-flag lane is now fully closed
- `bounded rehab wave 18` completed
  - action:
    - rewrote the `plot_roadmap.genre_ext.profit_loss` lane to preserve accounting/result carry without inline `Block/Bxx` references
    - rebuilt the fresh BI probe, reran the 5-pass audit, and directly rechecked the targeted profit-loss family
  - result:
    - `plot_roadmap.genre_ext.profit_loss = 0` by direct family check
    - `diegetic_meta_ref_count = 65`
    - `diegetic_block_ref_count(alias) = 65`
    - `label_meta_ref_count = 0`
    - `unresolved_foreshadow_count = 2`
    - `npc_continuity_mismatch_count = 0`
    - `bi_diegetic_meta_leak_count = 75`
    - fresh BI probe still `FAIL`, but the profit-loss lane is now fully closed
- `bounded rehab wave 19` completed
  - action:
    - rewrote the `plot_roadmap.power_shift.protagonist` lane and the short `plot_roadmap.genre_ext.opponent` weakness texts to preserve situation meaning without inline `Block/Bxx` references
    - rebuilt the fresh BI probe, reran the 5-pass audit, and directly rechecked the targeted protagonist/opponent families
  - result:
    - `plot_roadmap.power_shift.protagonist = 0` by direct family check
    - `plot_roadmap.genre_ext.opponent = 0` by direct family check
    - `diegetic_meta_ref_count = 61`
    - `diegetic_block_ref_count(alias) = 61`
    - `label_meta_ref_count = 0`
    - `unresolved_foreshadow_count = 2`
    - `npc_continuity_mismatch_count = 0`
    - `bi_diegetic_meta_leak_count = 71`
    - fresh BI probe still `FAIL`, but the protagonist/opponent short lanes are now fully closed
- `bounded rehab wave 20` completed
  - action:
    - rewrote the short `plot_roadmap.relationship_delta.after` lane to preserve relationship carry without inline `Block/Bxx` references
    - rebuilt the fresh BI probe, reran the 5-pass audit, and directly rechecked the targeted `after` family
  - result:
    - `plot_roadmap.relationship_delta.after = 0` by direct family check
    - `diegetic_meta_ref_count = 59`
    - `diegetic_block_ref_count(alias) = 59`
    - `label_meta_ref_count = 0`
    - `unresolved_foreshadow_count = 2`
    - `npc_continuity_mismatch_count = 0`
    - `bi_diegetic_meta_leak_count = 69`
    - fresh BI probe still `FAIL`, but the `relationship_delta.after` lane is now fully closed
- `bounded rehab wave 21` completed
  - action:
    - rewrote the short `plot_roadmap.genre_ext.time_pressure` lane to preserve timing judgment without inline `Block/Bxx` references
    - rebuilt the fresh BI probe, reran the 5-pass audit, and directly rechecked the targeted time-pressure family
  - result:
    - `plot_roadmap.genre_ext.time_pressure = 0` by direct family check
    - `diegetic_meta_ref_count = 57`
    - `diegetic_block_ref_count(alias) = 57`
    - `label_meta_ref_count = 0`
    - `unresolved_foreshadow_count = 2`
    - `npc_continuity_mismatch_count = 0`
    - `bi_diegetic_meta_leak_count = 67`
    - fresh BI probe still `FAIL`, but the short time-pressure lane is now fully closed
- `bounded rehab wave 22` completed
  - action:
    - rewrote the short `plot_roadmap.content.stakes` lane to preserve stakes carry without inline `Block/Bxx` references
    - rebuilt the fresh BI probe, reran the 5-pass audit, and directly rechecked the targeted content-stakes family
  - result:
    - `plot_roadmap.content.stakes = 0` by direct family check
    - `diegetic_meta_ref_count = 56`
    - `diegetic_block_ref_count(alias) = 56`
    - `label_meta_ref_count = 0`
    - `unresolved_foreshadow_count = 2`
    - `npc_continuity_mismatch_count = 0`
    - `bi_diegetic_meta_leak_count = 66`
    - fresh BI probe still `FAIL`, but the short content-stakes lane is now fully closed
- `bounded rehab wave 23` completed
  - action:
    - rewrote the short `plot_roadmap.regression_ext.future_prep` lane to preserve next-step carry without inline `Block/Bxx` references
    - rebuilt the fresh BI probe, reran the 5-pass audit, and directly rechecked the targeted future-prep family
  - result:
    - `plot_roadmap.regression_ext.future_prep = 0` by direct family check
    - `diegetic_meta_ref_count = 55`
    - `diegetic_block_ref_count(alias) = 55`
    - `label_meta_ref_count = 0`
    - `unresolved_foreshadow_count = 2`
    - `npc_continuity_mismatch_count = 0`
    - `bi_diegetic_meta_leak_count = 65`
    - fresh BI probe still `FAIL`, but the short future-prep lane is now fully closed
- `bounded rehab wave 24` completed
  - action:
    - rewrote the visible `content.context` lane that still carried `ARC-*` labels in summary text
    - confirmed the touched lane was cleaned, then rebuilt the fresh BI probe
  - result:
    - the visible `content.context` family was cleaned, but headline counts did not move
    - the pair remained on the same residual watchlist, so the next unit pivoted to directly counted `future_prep.action` strings
- `bounded rehab wave 25` completed
  - action:
    - rewrote the remaining `plot_roadmap.regression_ext.future_prep.action` strings into diegetic next-step phrasing
    - rebuilt the fresh BI probe and reran the 5-pass audit
  - result:
    - `diegetic_meta_ref_count = 26`
    - `diegetic_block_ref_count(alias) = 26`
    - `unresolved_foreshadow_count = 2`
    - `npc_continuity_mismatch_count = 0`
    - `bi_diegetic_meta_leak_count = 34`
- `bounded rehab wave 26` completed
  - action:
    - closed the remaining source-side `ARC-*` scalar lane in `opening_progression.next_battlefield_ticket`, `callback`, `profit_loss`, `content.reward`, and `power_shift.protagonist`
  - result:
    - `diegetic_meta_ref_count = 17`
    - `diegetic_block_ref_count(alias) = 17`
    - `bi_diegetic_meta_leak_count = 30`
- `bounded rehab wave 27` completed
  - action:
    - normalized `phase0_design.partner_location_sector_distribution.partners[*].cadence` from `ARC-*` labels into diegetic cadence descriptions
  - result:
    - fresh BI rebuild remained stable
    - `bi_diegetic_meta_leak_count = 25`
- `bounded rehab wave 28` completed
  - action:
    - normalized `phase0_design.arcs[*].arc_id` and `front_sector_by_arc[*].arc_id` into neutral stable slugs
  - result:
    - fresh BI rebuild remained stable
    - `bi_diegetic_meta_leak_count = 17`
- `bounded rehab wave 29` completed
  - action:
    - swept the report-surfaced residual `Block/Bxx/Phase` strings across opening signboards, stakes, foreshadow carry, `power_shift.antagonist`, and the late 공개매수 context lane
    - removed the last `??` placeholder in `phase0_design.opponent_transition_plan.phase3.defeat_climax`
  - result:
    - direct source-side meta scan now returns zero residual non-structural leaks
    - direct BI-side meta scan now returns zero residual non-structural leaks
- `bounded rehab wave 30` completed
  - action:
    - identified that a prior `build -> audit` check had been run in parallel, so the audit runner had read a stale probe file
    - reran the sequence correctly as `build -> audit` in serial
  - result:
    - fresh BI probe 5-pass audit now returns `PASS`
    - the remaining failure state was runner order, not pair content

Current interpretation:

- the pair is no longer sitting in the original `mixed because of pacing` state
- opening drag is cleared
- whole-run drag is cleared
- the old `phase0 missing field` blocker is cleared
- the old source-side thin/stakes/meta/NPC blockers are cleared
- the fresh BI probe is now audit-clean when built and audited in the correct serial order
- the remaining historical problem is the raw legacy quarantine BI schema, not the current repaired `phase0 + TR -> fresh BI probe` path
- this pair has moved from `rehab candidate` to `quarantine promotion candidate`

## 6. BI Audit Note

Legacy BI audit command attempted:

```text
python -X utf8 scripts/audit_bi_5pass.py --phase0 treatments/_quarantine/empire_youngest_allsector_phase0_design.json --draft treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json --bi bible/_quarantine/0_bi_empire_youngest_allsector.json --report docs/2026-04-12/empire_youngest_allsector_bi_5pass.md
```

Observed result:

- raw legacy BI audit still aborts before narrative judgment
- current abort point is `KeyError: 'AssetLibrary'`
- this is a legacy BI schema mismatch, not the current repaired pair path

Fresh BI probe commands:

```text
python -X utf8 scripts/build_bi_from_phase0_and_tr.py --phase0 treatments/_quarantine/empire_youngest_allsector_phase0_design.json --draft treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json --output docs/temp/empire_youngest_allsector_bi_probe.json
python -X utf8 scripts/audit_bi_5pass.py --phase0 treatments/_quarantine/empire_youngest_allsector_phase0_design.json --draft treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json --bi docs/temp/empire_youngest_allsector_bi_probe.json --report docs/2026-04-12/empire_youngest_allsector_bi_probe_5pass.md
```

Fresh BI probe observed result:

- fresh BI rebuild now succeeds
- fresh BI probe audit now returns `PASS` when run after the fresh build in serial order
- the prior `FAIL` state at the end of rehab was caused by a stale-probe audit run order, not by remaining pair content defects

Current source-side watchlist after bounded rehab wave 30:

- `production_density_gate = PASS`
- `short_stakes_blocks = []`
- `diegetic_meta_ref_count = 0`
- `diegetic_block_ref_count(alias) = 0`
- `label_meta_ref_count = 0`
- `unresolved_foreshadow_count = 0`
- `npc_continuity_mismatch_count = 0`
- `bi_diegetic_meta_leak_count = 0`

Interpretation:

- the old `phase0-shape / builder compatibility` issue is resolved
- the old source-side rehab blockers are resolved
- the fresh BI probe is now clean enough to treat as the authoritative post-rehab pair output
- do not spend more time on raw legacy BI schema rescue unless there is a separate historical reason to keep that artifact alive

## 7. Current Next Step

Current admissible next step:

- `active promotion complete`
- concretely:
  - the repaired pair has been copied into the live authority lane
  - use `treatments/phase0/empire_youngest_allsector_phase0_design.json`
  - use `treatments/empire_youngest_allsector_tr_block_070_draft.json`
  - use `bible/0_bi_empire_youngest_allsector.json`
  - promotion evidence is saved at `docs/2026-04-12/empire_youngest_allsector_promotion_note.md`
  - live BI PASS audit is saved at `docs/2026-04-12/empire_youngest_allsector_promotion_bi_5pass.md`

Not recommended next:

- reopening pacing repair
- reopening thin/stakes/meta cleanup
- raw legacy BI schema surgery without a separate explicit need
- full TR rewrite
