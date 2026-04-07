# 10-Pair TR/BI Legacy Meta Cleanup Bounded Survey

Date: 2026-04-07
Status: final
Document Type: bounded merge survey
Canonical Path: `docs/2026-04-07/10pair_tr_bi_legacy_meta_cleanup_bounded_survey.md`
Scope: live numbered `01-10` `TR/BI` pairs only
Merge Owner: `Codex`
Execution Mode: `10-lane Opus read-only survey -> Codex merge/audit`
Baseline Commit: `5c71b81a36ab2cbae824c630bb63219354b913a8`
Baseline Dirty Summary: active unrelated system-track dirty files and `docs/temp/` queue artifacts already exist; this merge survey does not mutate pair artifacts or queue docs

## 1. Source Inputs

Merged lane outputs:

- `docs/2026-04-07/10pair_meta_cleanup_terminal01_pair01.md`
- `docs/2026-04-07/10pair_meta_cleanup_terminal02_pair02.md`
- `docs/2026-04-07/10pair_meta_cleanup_terminal03_pair03.md`
- `docs/2026-04-07/10pair_meta_cleanup_terminal04_pair04.md`
- `docs/2026-04-07/10pair_meta_cleanup_terminal05_pair05.md`
- `docs/2026-04-07/10pair_meta_cleanup_terminal06_pair06.md`
- `docs/2026-04-07/10pair_meta_cleanup_terminal07_pair07.md`
- `docs/2026-04-07/10pair_meta_cleanup_terminal08_pair08.md`
- `docs/2026-04-07/10pair_meta_cleanup_terminal09_pair09.md`
- `docs/2026-04-07/10pair_meta_cleanup_terminal10_pair10.md`

Policy anchors:

- `docs/2026-04-07/10pair_tr_bi_legacy_meta_cleanup_10terminal_opus_order.md`
- `docs/2026-04-06/meta-language-leak-context-handoff.md`
- `docs/narrative-router/SSOT_bi-evolution-metadata-standard.md`
- `docs/2026-04-06/10pair_tr_bi_consistency_bounded_survey.md`

Codex spot-check anchors:

- `bible/07_bi_office_checkup_next_day.json`
- `treatments/07_office_checkup_next_day_tr_block_070_draft.json`
- `bible/10_bi_jaebeol3se_loss_line.json`
- `treatments/10_jaebeol3se_loss_line_tr_block_070_draft.json`
- `bible/02_bi_chaebol_allowance_zero.json`
- `bible/04_bi_defense_defect_engineer.json`

## 2. Executive Verdict

Across the live numbered `01-10` pair set:

- `cleanup_now`: `10` pairs
- `truth_repair_first`: `0`
- `tr_completion_first`: `0` on current file-state baseline
- `no_action`: `0`
- `P2`: `10`
- `P1/P0`: `0`

High-level reading:

- the legacy meta-wording problem is not local or cosmetic; it is present in every live numbered pair
- the dominant leak class is stable across the set:
  - `label_meta_ref`: `"ARC-0N - ..."` / `"Phase N: ..."` prefixes in human-readable labels
  - `diegetic_meta_ref`: `Block N` / `ARC-NN` / `Bnn` wording embedded in prose-facing `foreshadow`, `callback`, `content.*`, and asset-description fields
- no pair is currently blocked at merge time by a still-live `truth_repair_first` or `tr_completion_first` condition
- pair `10` still deserves cautious execution sequencing, but the specific prior blocker from `2026-04-06` (`TR incomplete vs BI ahead`) is no longer visible in the current baseline

## 3. Aggregate Scoreboard

| Pair | Severity | Route | Smallest Cleanup Unit | Main Leak Shape | Merge Note |
| --- | --- | --- | --- | --- | --- |
| `01` | `P2` | `cleanup_now` | `TR + BI` | `section_rotation` + mirrored `foreshadow/callback` prose | mechanically isolatable |
| `02` | `P2` | `cleanup_now` | `TR + BI` | mirrored `foreshadow/callback/context/solution` + `Phase N` labels | BI BOM cleanup can ride same patch |
| `03` | `P2` | `cleanup_now` | `TR + BI` | mirrored `callback/foreshadow` prose + `section_rotation/methods` labels | broad but pair truth clean |
| `04` | `P2` | `cleanup_now` | `TR + BI` | `section_rotation`, `target_event`, `ripple_effect`, `Phase N` labels | BI BOM + borderline `Phase0` tag decision |
| `05` | `P2` | `cleanup_now` | `TR + BI` | mirrored `section_rotation`, `target_event`, `foreshadow/callback`, BI ArcSheet/Seed tails | wording cleanup separable |
| `06` | `P2` | `cleanup_now` | `TR + BI` | saturated `foreshadow/callback` prose + `section_rotation` / `phase` labels | BI-only `KeyNPCs.desc` and `portfolio_history` prose also dirty |
| `07` | `P2` | `cleanup_now` | `TR + BI` | mirrored `foreshadow/callback/content.*` + BI-only NPC/phase/history prose | prior truth blocker no longer observable |
| `08` | `P2` | `cleanup_now` | `TR + BI` | mirrored prose leaks + BI `OpponentTransitionPlan.phases.phase` | `_creation_note/_schema_description` stay out of scope |
| `09` | `P2` | `cleanup_now` | `TR + BI` | wuxguide `Bnn` shorthand in `martial_ext`, treasures, NPC turning points | preserve `evolution` untouched |
| `10` | `P2` | `cleanup_now` | staged: `BI first`, then larger `TR + BI` wave | `section_rotation` saturation + `foreshadow/callback` prose + BI `phase/arc_presence` labels | prior `TR incomplete` file-shape blocker no longer visible |

## 4. Cross-Pair Findings

### 4.1 Universal leak families

The lane outputs agree on three repeated surfaces:

1. `section_rotation`-family label leakage
   - usually `"ARC-0N - ..."` or `"ARC-0N ..."`
   - present in most `blockguide` pairs and mirrored into BI `plot_roadmap`
2. `foreshadow / callback` prose leakage
   - prose lines keep `Block N`, `ARC-NN`, or `Bnn` wording instead of leaving structure to `foreshadow_targets` / `callback_sources`
3. BI-side label leakage outside the TR mirror
   - especially `opponent_transition_plan[*].phase`
   - plus pair-local surfaces such as `npc_timeline[*].arc_presence[*]`, `ArcSheets`, `CapitalCurve.event`, `HistoricalEvents.summary`, `KeyNPCs.desc`

This is strong evidence that the workspace does not need ten unrelated cleanup styles.
It needs one shared cleanup doctrine with small pair-local overlays.

### 4.2 Pair truth is not the live blocker

The 10 lanes uniformly reported wording cleanup as separable from deeper truth repair.
Codex spot-check agrees with that reading for the two previously sensitive pairs:

- pair `07`
  - `BI protagonist_config.incarnation_type = "각성"`
  - `TR blocks[0].regression_ext.is_regressor = false`
  - `TR blocks[69].regression_ext.is_regressor = false`
  - `BI financial_status.company_state` now reflects late-state authority, not the old start-state mismatch
- pair `10`
  - `len(TR) = 70`
  - last TR block is `Block 70`
  - `BI _sync_manifest.tr_block_count = 70`
  - late TR blocks have non-empty `content.context`

Important boundary:

- this clears the prior file-shape blocker
- it does not itself certify that every new late TR block is narratively perfect
- that quality question belongs to a later pair-quality or repair pass, not this wording survey

### 4.3 Two BI files still carry UTF-8 BOM

Codex byte-level read-back confirmed:

- `bible/02_bi_chaebol_allowance_zero.json` starts with UTF-8 BOM
- `bible/04_bi_defense_defect_engineer.json` starts with UTF-8 BOM

These are not promoted to `P0`.
They are hygiene issues that should be removed opportunistically in the same bounded cleanup wave touching those BI files.

### 4.4 Wuxguide exception is narrow and explicit

Pair `09` is the only `wuxguide` pair.
The lane output is consistent with policy:

- `evolution` remains allowed structural metadata and should stay untouched
- the cleanup target is the surrounding `Bnn` shorthand in `martial_ext`, treasures, key turning points, and faction/commercial prose fields

This means the validator or patch logic must support one small family overlay rather than a totally different wave.

## 5. Routing Decision

### 5.1 Immediate route

On the current baseline, the merged route is:

- `10 / 10 = cleanup_now`

That does not mean one giant all-pair patch.
It means no pair currently needs to be sent backward to `truth_repair_first` or `tr_completion_first` before a wording-cleanup execution plan is written.

### 5.2 Practical execution grouping

The lane outputs support this bounded grouping:

1. shared `blockguide` label cleanup template
   - strip `ARC-0N - ` from `section_rotation`
   - split `Phase N: ...` into structure + natural-language label
2. shared `foreshadow / callback` prose normalization template
   - keep meaning in prose
   - move numbering into `foreshadow_targets` / `callback_sources`
3. pair-local BI tail cleanup
   - NPC descriptions
   - history summaries
   - asset/event labels
   - BOM removal where applicable
4. wuxguide overlay for pair `09`
   - preserve `evolution`
   - normalize `Bnn` shorthand elsewhere

### 5.3 Pair `10` execution caution

Pair `10` stays in `cleanup_now`, but should not lead the first broad TR rewrite wave.

Best sequencing from the merged evidence:

1. start with the smaller BI-side cleanup:
   - `opponent_transition_plan[*].phase`
   - `npc_timeline[*].arc_presence[*]`
   - `arcs[0].exit_function`
2. only after that open the larger TR-side `section_rotation` / `foreshadow` / `callback` sweep

That keeps the most recently recovered pair off the critical first rewrite path while still respecting the lane verdict.

## 6. Recommended Next Step

The correct next artifact is:

- a bounded `cleanup execution order`, not another survey

That execution order should:

- keep pair ownership explicit
- start from the shared normalization templates the lanes converged on
- separate `TR+BI mirrored fields` from `BI-only tail fields`
- include a BOM-removal note for pairs `02` and `04`
- include a `pair 09 wuxguide preserve-evolution` rule
- include a `pair 10 staged entry` rule

Recommended wave shape:

1. write one execution order for pairs `01-09`, grouped by shared fix template
2. write one narrower child order for pair `10`

This is higher ROI than writing ten pair-specific execution orders from scratch.

## 7. Final Call

The 10-lane Opus wave did what it needed to do:

- it proved the problem is live across all `10` numbered pairs
- it proved the problem is still bounded and structurally repetitive
- it removed the need for another discovery survey before execution planning

Current merged reading:

- all `10` pairs are active cleanup candidates
- no pair currently needs to be rerouted to truth repair first
- pair `10` needs cautious sequencing, not a different route
- pair `09` needs a small wuxguide exception, not a separate doctrine

## 8. 3-Pass Audit

Pass 1:

- merged all `10` lane outputs into one bounded survey
- kept the document as a merge survey rather than inflating it into an execution SSOT

Pass 2:

- cross-checked the lane verdicts against the source terminal docs
- performed Codex spot-checks for pair `07`, pair `10`, and the BOM claims for pairs `02` and `04`
- confirmed the current live baseline commit remains `5c71b81a36ab2cbae824c630bb63219354b913a8`

Pass 3:

- normalized the aggregate result into one scoreboard and one routing decision
- separated `cleanup_now` from actual execution sequencing so the next document can stay implementation-focused
- kept the non-goals explicit: this document does not patch files and does not replace the later execution order

Confidence: `97%`
