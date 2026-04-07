# 10-Pair TR/BI Legacy Meta Cleanup 10-Terminal Opus Order

Date: 2026-04-07
Status: final
Document Type: bounded parallel survey order
Canonical Path: `docs/2026-04-07/10pair_tr_bi_legacy_meta_cleanup_10terminal_opus_order.md`
Scope: live numbered `01-10` `TR/BI` pairs only
Execution Mode: `10 terminals / Opus / 1 pair per terminal / read-only survey / no repair / no pair mutation`
Final Merge Owner: `Codex`
Baseline Commit: `5c71b81a36ab2cbae824c630bb63219354b913a8`
Baseline Dirty Summary: active system-track dirty files and `docs/temp/` queue artifacts already exist; this narrative cleanup survey must not mutate `treatments/`, `bible/`, `docs/temp/`, or unrelated dirty files

## 1. Purpose

This order exists to answer one bounded question only:

- across the live numbered `01-10` `TR/BI` pairs, which pairs still carry disallowed legacy `Block / ARC / Phase / Stage` wording in human-readable fields, which pairs are structurally clean, and which pairs are blocked by upstream pair-truth repair before wording cleanup should start

This is not:

- direct `TR` or `BI` repair
- `TR 58-70` completion work
- promotion
- Stage 2/3/4 runtime probing
- pair regrading
- `docs/temp/` mutation

This document is the entry execution artifact for the cleanup survey wave.
Do not write the actual cleanup patch order until the lane outputs land and are merged.

## 2. Evidence Basis

Primary policy anchors:

1. `docs/narrative-router/SSOT_narrative-router-integrated-order.md`
2. `docs/narrative-router/material-revival-ladder-harness.md`
3. family integrated order:
   - `blockguide`: `docs/blockguide/SSOT_blockguide-integrated-order.md`
   - `wuxguide`: `docs/wuxguide/SSOT_wuxguide-integrated-order.md`
4. `docs/2026-04-06/meta-language-leak-context-handoff.md`
5. `docs/narrative-router/SSOT_bi-evolution-metadata-standard.md`
6. `docs/2026-04-06/10pair_tr_bi_consistency_bounded_survey.md`

Why a full 10-terminal split is justified:

- terminal capacity matches pair count, so one terminal per pair is the cleanest no-collision ownership model
- a UTF-8 read-only token prevalence scan on the live numbered set found English-form meta tokens in all `20` live artifacts
- those raw hits are not violation counts, but they prove the surface is wide enough that pair-level parallel review is justified

Raw scan snapshot for live numbered assets:

| Pair | TR raw English-form meta hits | BI raw English-form meta hits | Prior pair status |
| --- | ---: | ---: | --- |
| `01` | `291` | `325` | `clean` |
| `02` | `394` | `485` | `clean` |
| `03` | `156` | `207` | `clean` |
| `04` | `299` | `114` | `clean` |
| `05` | `614` | `668` | `clean` |
| `06` | `834` | `886` | `clean` |
| `07` | `352` | `388` | `mixed` |
| `08` | `316` | `387` | `clean` |
| `09` | `70` | `164` | `clean` |
| `10` | `685` | `29` | `mixed` |

Interpretation rule:

- use the raw counts only as triage evidence that meta wording is widespread
- do not treat raw counts as failure counts
- terminals must separate `allowed structural metadata` from `disallowed human-readable leakage`

## 3. Inventory

Confirmed live numbered pair inventory:

| Pair | TR | BI | Family Overlay |
| --- | --- | --- | --- |
| `01` | `treatments/01_tr_투자물_골든_카나리아 테스트_canonical_v1.json` | `bible/01_bi_투자물_골든_카나리아 테스트_canonical_v1.json` | `blockguide` |
| `02` | `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json` | `bible/02_bi_chaebol_allowance_zero.json` | `blockguide` |
| `03` | `treatments/03_chaebol_ent_empire_tr_block_070_draft.json` | `bible/03_bi_chaebol_ent_empire.json` | `blockguide` |
| `04` | `treatments/04_defense_defect_engineer_tr_block_070_draft.json` | `bible/04_bi_defense_defect_engineer.json` | `blockguide` |
| `05` | `treatments/05_failed_future_ceo_intern_tr_block_070_draft.json` | `bible/05_bi_failed_future_ceo_intern.json` | `blockguide` |
| `06` | `treatments/06_gatekeeper_heir_tr_block_070_draft.json` | `bible/06_bi_gatekeeper_heir.json` | `blockguide` |
| `07` | `treatments/07_office_checkup_next_day_tr_block_070_draft.json` | `bible/07_bi_office_checkup_next_day.json` | `blockguide` |
| `08` | `treatments/08_pantech_cyworld_reborn_tr_block_070_draft.json` | `bible/08_bi_pantech_cyworld_reborn.json` | `blockguide` |
| `09` | `treatments/09_wuxia_heavenly_physician_tr_block_070_draft.json` | `bible/09_bi_wuxia_heavenly_physician.json` | `wuxguide` |
| `10` | `treatments/10_jaebeol3se_loss_line_tr_block_070_draft.json` | `bible/10_bi_jaebeol3se_loss_line.json` | `blockguide` |

## 4. Required Read Order

Each terminal must read in this order before judging its assigned pair:

1. `docs/narrative-router/SSOT_narrative-router-integrated-order.md`
2. `docs/narrative-router/material-revival-ladder-harness.md`
3. family integrated order:
   - pairs `01-08`, `10`: `docs/blockguide/SSOT_blockguide-integrated-order.md`
   - pair `09`: `docs/wuxguide/SSOT_wuxguide-integrated-order.md`
4. `docs/2026-04-06/meta-language-leak-context-handoff.md`
5. `docs/narrative-router/SSOT_bi-evolution-metadata-standard.md`
6. `docs/2026-04-06/10pair_tr_bi_consistency_bounded_survey.md`
7. this order file

Reason for item `5`:

- `evolution` is metadata
- block-trace wording is allowed there
- terminals must not false-positive `evolution` as forbidden natural-language leakage

## 5. Bounded Audit Question

For each assigned pair, answer only these questions:

1. which human-readable or label fields still carry disallowed `Block / ARC / Phase / Stage` wording
2. which hits are `allowed structural metadata` and which are `diegetic_meta_ref` or `label_meta_ref`
3. can wording cleanup proceed now, or is it blocked by deeper pair-truth repair
4. what is the smallest cleanup unit:
   - `BI only`
   - `TR only`
   - `TR + BI`
   - `truth repair first`
   - `TR completion first`

Do not widen into:

- full pair redesign
- density grading
- runtime quality claims
- promotion claims
- block-by-block rewrite planning

## 6. Meta Classification Contract

Use the following classification language exactly.

### 6.1 Allowed Structural Metadata

These are allowed to carry structural numbering:

- `block_id`
- `arc_id`
- `arc_no`
- `phase_no`
- `stage_no`
- `foreshadow_targets`
- `callback_sources`
- `evolution`

Note:

- `evolution` is allowed because `docs/narrative-router/SSOT_bi-evolution-metadata-standard.md` explicitly treats it as metadata

### 6.2 Disallowed Human-Readable Leakage

These are disallowed when they carry `Block / ARC / Phase / Stage` wording:

- `content.*`
- `stakes`
- `power_shift.*`
- `relationship_delta.before`
- `relationship_delta.after`
- `genre_ext.method`
- `genre_ext.success_pattern`
- `foreshadow`
- `callback`
- `section_rotation`
- `arc_section`
- `phase`
- `phase_label`

Inference rule from `meta-language-leak-context-handoff.md`:

- if a field is clearly meant to be read as prose, a label, a short description, a reward line, a solution line, a payoff line, or a scene-facing summary, treat it as `human-readable` even if the policy note does not name that exact key

### 6.3 Output Labels

Use these labels only:

- `allowed_structural_meta`
- `diegetic_meta_ref`
- `label_meta_ref`
- `blocked_by_pair_truth`

## 7. Severity and Execution Route

### Severity

- `P0`
  - file missing
  - UTF-8 decode fails
  - JSON parse fails
- `P1`
  - pair truth is too unstable to isolate wording cleanup safely
  - wording is fused with a larger truth contradiction or incomplete production state
- `P2`
  - repeated disallowed meta leakage exists and bounded cleanup should be scheduled soon
- `P3`
  - sparse or cosmetic leakage only

### Execution Route

Each pair must end with exactly one route:

- `cleanup_now`
- `truth_repair_first`
- `tr_completion_first`
- `no_action`

Prior-survey constraint:

- pair `07` already has a live `BI metadata/end-state drift`
- pair `10` already has `TR incomplete vs BI ahead`
- terminals for `07` and `10` must explicitly separate meta-wording findings from those prior truth blockers

## 8. Terminal Ownership

Ownership is by pair. No terminal may write to another terminal's output file.

| Terminal | Pair | Output |
| --- | --- | --- |
| `01` | `01` | `docs/2026-04-07/10pair_meta_cleanup_terminal01_pair01.md` |
| `02` | `02` | `docs/2026-04-07/10pair_meta_cleanup_terminal02_pair02.md` |
| `03` | `03` | `docs/2026-04-07/10pair_meta_cleanup_terminal03_pair03.md` |
| `04` | `04` | `docs/2026-04-07/10pair_meta_cleanup_terminal04_pair04.md` |
| `05` | `05` | `docs/2026-04-07/10pair_meta_cleanup_terminal05_pair05.md` |
| `06` | `06` | `docs/2026-04-07/10pair_meta_cleanup_terminal06_pair06.md` |
| `07` | `07` | `docs/2026-04-07/10pair_meta_cleanup_terminal07_pair07.md` |
| `08` | `08` | `docs/2026-04-07/10pair_meta_cleanup_terminal08_pair08.md` |
| `09` | `09` | `docs/2026-04-07/10pair_meta_cleanup_terminal09_pair09.md` |
| `10` | `10` | `docs/2026-04-07/10pair_meta_cleanup_terminal10_pair10.md` |

Final merge output is reserved for Codex only:

- `docs/2026-04-07/10pair_tr_bi_legacy_meta_cleanup_bounded_survey.md`

## 9. Output Contract

Each terminal file must contain:

1. terminal scope
2. assigned pair and family
3. artifact truth:
   - file exists
   - UTF-8 decode succeeds
   - JSON parse succeeds
4. one short raw-count snapshot:
   - `TR raw meta-token hits`
   - `BI raw meta-token hits`
5. findings first:
   - `allowed_structural_meta`
   - `diegetic_meta_ref`
   - `label_meta_ref`
   - `blocked_by_pair_truth` if applicable
6. up to `5` concrete anchors total
   - key-path first
   - short explanation second
7. final severity
8. final execution route
9. one-line minimal next-step suggestion

Anchor style examples:

- `BI: section_rotation`
- `BI: foreshadow[2]`
- `TR: blocks[17].content.summary`
- `TR: blocks[44].callback[0]`
- `BI: protagonist_config.special_ability.evolution`

Do not dump large JSON excerpts.
Do not quote long passages.

## 10. Merge Rules

- no terminal edits live pair artifacts
- no terminal edits `docs/temp/`
- no terminal writes the final merged survey
- no terminal writes a patch execution order
- no terminal treats raw token counts as failure counts without field classification
- no terminal escalates pair `07` or `10` to `cleanup_now` unless the wording issue is cleanly separable from the prior truth blocker
- Codex will merge the `10` lane outputs afterward

Each terminal document must end with exactly this line:

`read-only terminal survey complete; no files mutated outside assigned docs/2026-04-07 output`

## 11. Paste-Ready Terminal Orders

### Opus Terminal 01

```text
서사 오더다. 기존 numbered pair 01의 legacy meta wording cleanup 여부만 read-only로 조사한다.

먼저 읽을 것:
1. C:\Users\User\Desktop\글도비\docs\narrative-router\SSOT_narrative-router-integrated-order.md
2. C:\Users\User\Desktop\글도비\docs\narrative-router\material-revival-ladder-harness.md
3. C:\Users\User\Desktop\글도비\docs\blockguide\SSOT_blockguide-integrated-order.md
4. C:\Users\User\Desktop\글도비\docs\2026-04-06\meta-language-leak-context-handoff.md
5. C:\Users\User\Desktop\글도비\docs\narrative-router\SSOT_bi-evolution-metadata-standard.md
6. C:\Users\User\Desktop\글도비\docs\2026-04-06\10pair_tr_bi_consistency_bounded_survey.md
7. C:\Users\User\Desktop\글도비\docs\2026-04-07\10pair_tr_bi_legacy_meta_cleanup_10terminal_opus_order.md

대상 pair:
- TR: C:\Users\User\Desktop\글도비\treatments\01_tr_투자물_골든_카나리아 테스트_canonical_v1.json
- BI: C:\Users\User\Desktop\글도비\bible\01_bi_투자물_골든_카나리아 테스트_canonical_v1.json

할 일:
- read-only bounded survey only
- allowed_structural_meta vs diegetic_meta_ref vs label_meta_ref를 분리
- pair 01만 조사
- no repair
- no code edits
- no docs/temp edits

산출물:
- C:\Users\User\Desktop\글도비\docs\2026-04-07\10pair_meta_cleanup_terminal01_pair01.md
```

### Opus Terminal 02

```text
서사 오더다. 기존 numbered pair 02의 legacy meta wording cleanup 여부만 read-only로 조사한다.

먼저 읽을 것:
1. C:\Users\User\Desktop\글도비\docs\narrative-router\SSOT_narrative-router-integrated-order.md
2. C:\Users\User\Desktop\글도비\docs\narrative-router\material-revival-ladder-harness.md
3. C:\Users\User\Desktop\글도비\docs\blockguide\SSOT_blockguide-integrated-order.md
4. C:\Users\User\Desktop\글도비\docs\2026-04-06\meta-language-leak-context-handoff.md
5. C:\Users\User\Desktop\글도비\docs\narrative-router\SSOT_bi-evolution-metadata-standard.md
6. C:\Users\User\Desktop\글도비\docs\2026-04-06\10pair_tr_bi_consistency_bounded_survey.md
7. C:\Users\User\Desktop\글도비\docs\2026-04-07\10pair_tr_bi_legacy_meta_cleanup_10terminal_opus_order.md

대상 pair:
- TR: C:\Users\User\Desktop\글도비\treatments\02_chaebol_allowance_zero_tr_block_070_draft.json
- BI: C:\Users\User\Desktop\글도비\bible\02_bi_chaebol_allowance_zero.json

할 일:
- read-only bounded survey only
- allowed_structural_meta vs diegetic_meta_ref vs label_meta_ref를 분리
- pair 02만 조사
- no repair
- no code edits
- no docs/temp edits

산출물:
- C:\Users\User\Desktop\글도비\docs\2026-04-07\10pair_meta_cleanup_terminal02_pair02.md
```

### Opus Terminal 03

```text
서사 오더다. 기존 numbered pair 03의 legacy meta wording cleanup 여부만 read-only로 조사한다.

먼저 읽을 것:
1. C:\Users\User\Desktop\글도비\docs\narrative-router\SSOT_narrative-router-integrated-order.md
2. C:\Users\User\Desktop\글도비\docs\narrative-router\material-revival-ladder-harness.md
3. C:\Users\User\Desktop\글도비\docs\blockguide\SSOT_blockguide-integrated-order.md
4. C:\Users\User\Desktop\글도비\docs\2026-04-06\meta-language-leak-context-handoff.md
5. C:\Users\User\Desktop\글도비\docs\narrative-router\SSOT_bi-evolution-metadata-standard.md
6. C:\Users\User\Desktop\글도비\docs\2026-04-06\10pair_tr_bi_consistency_bounded_survey.md
7. C:\Users\User\Desktop\글도비\docs\2026-04-07\10pair_tr_bi_legacy_meta_cleanup_10terminal_opus_order.md

대상 pair:
- TR: C:\Users\User\Desktop\글도비\treatments\03_chaebol_ent_empire_tr_block_070_draft.json
- BI: C:\Users\User\Desktop\글도비\bible\03_bi_chaebol_ent_empire.json

할 일:
- read-only bounded survey only
- allowed_structural_meta vs diegetic_meta_ref vs label_meta_ref를 분리
- pair 03만 조사
- no repair
- no code edits
- no docs/temp edits

산출물:
- C:\Users\User\Desktop\글도비\docs\2026-04-07\10pair_meta_cleanup_terminal03_pair03.md
```

### Opus Terminal 04

```text
서사 오더다. 기존 numbered pair 04의 legacy meta wording cleanup 여부만 read-only로 조사한다.

먼저 읽을 것:
1. C:\Users\User\Desktop\글도비\docs\narrative-router\SSOT_narrative-router-integrated-order.md
2. C:\Users\User\Desktop\글도비\docs\narrative-router\material-revival-ladder-harness.md
3. C:\Users\User\Desktop\글도비\docs\blockguide\SSOT_blockguide-integrated-order.md
4. C:\Users\User\Desktop\글도비\docs\2026-04-06\meta-language-leak-context-handoff.md
5. C:\Users\User\Desktop\글도비\docs\narrative-router\SSOT_bi-evolution-metadata-standard.md
6. C:\Users\User\Desktop\글도비\docs\2026-04-06\10pair_tr_bi_consistency_bounded_survey.md
7. C:\Users\User\Desktop\글도비\docs\2026-04-07\10pair_tr_bi_legacy_meta_cleanup_10terminal_opus_order.md

대상 pair:
- TR: C:\Users\User\Desktop\글도비\treatments\04_defense_defect_engineer_tr_block_070_draft.json
- BI: C:\Users\User\Desktop\글도비\bible\04_bi_defense_defect_engineer.json

할 일:
- read-only bounded survey only
- allowed_structural_meta vs diegetic_meta_ref vs label_meta_ref를 분리
- pair 04만 조사
- no repair
- no code edits
- no docs/temp edits

산출물:
- C:\Users\User\Desktop\글도비\docs\2026-04-07\10pair_meta_cleanup_terminal04_pair04.md
```

### Opus Terminal 05

```text
서사 오더다. 기존 numbered pair 05의 legacy meta wording cleanup 여부만 read-only로 조사한다.

먼저 읽을 것:
1. C:\Users\User\Desktop\글도비\docs\narrative-router\SSOT_narrative-router-integrated-order.md
2. C:\Users\User\Desktop\글도비\docs\narrative-router\material-revival-ladder-harness.md
3. C:\Users\User\Desktop\글도비\docs\blockguide\SSOT_blockguide-integrated-order.md
4. C:\Users\User\Desktop\글도비\docs\2026-04-06\meta-language-leak-context-handoff.md
5. C:\Users\User\Desktop\글도비\docs\narrative-router\SSOT_bi-evolution-metadata-standard.md
6. C:\Users\User\Desktop\글도비\docs\2026-04-06\10pair_tr_bi_consistency_bounded_survey.md
7. C:\Users\User\Desktop\글도비\docs\2026-04-07\10pair_tr_bi_legacy_meta_cleanup_10terminal_opus_order.md

대상 pair:
- TR: C:\Users\User\Desktop\글도비\treatments\05_failed_future_ceo_intern_tr_block_070_draft.json
- BI: C:\Users\User\Desktop\글도비\bible\05_bi_failed_future_ceo_intern.json

할 일:
- read-only bounded survey only
- allowed_structural_meta vs diegetic_meta_ref vs label_meta_ref를 분리
- pair 05만 조사
- no repair
- no code edits
- no docs/temp edits

산출물:
- C:\Users\User\Desktop\글도비\docs\2026-04-07\10pair_meta_cleanup_terminal05_pair05.md
```

### Opus Terminal 06

```text
서사 오더다. 기존 numbered pair 06의 legacy meta wording cleanup 여부만 read-only로 조사한다.

먼저 읽을 것:
1. C:\Users\User\Desktop\글도비\docs\narrative-router\SSOT_narrative-router-integrated-order.md
2. C:\Users\User\Desktop\글도비\docs\narrative-router\material-revival-ladder-harness.md
3. C:\Users\User\Desktop\글도비\docs\blockguide\SSOT_blockguide-integrated-order.md
4. C:\Users\User\Desktop\글도비\docs\2026-04-06\meta-language-leak-context-handoff.md
5. C:\Users\User\Desktop\글도비\docs\narrative-router\SSOT_bi-evolution-metadata-standard.md
6. C:\Users\User\Desktop\글도비\docs\2026-04-06\10pair_tr_bi_consistency_bounded_survey.md
7. C:\Users\User\Desktop\글도비\docs\2026-04-07\10pair_tr_bi_legacy_meta_cleanup_10terminal_opus_order.md

대상 pair:
- TR: C:\Users\User\Desktop\글도비\treatments\06_gatekeeper_heir_tr_block_070_draft.json
- BI: C:\Users\User\Desktop\글도비\bible\06_bi_gatekeeper_heir.json

할 일:
- read-only bounded survey only
- allowed_structural_meta vs diegetic_meta_ref vs label_meta_ref를 분리
- pair 06만 조사
- no repair
- no code edits
- no docs/temp edits

산출물:
- C:\Users\User\Desktop\글도비\docs\2026-04-07\10pair_meta_cleanup_terminal06_pair06.md
```

### Opus Terminal 07

```text
서사 오더다. 기존 numbered pair 07의 legacy meta wording cleanup 여부만 read-only로 조사한다.

먼저 읽을 것:
1. C:\Users\User\Desktop\글도비\docs\narrative-router\SSOT_narrative-router-integrated-order.md
2. C:\Users\User\Desktop\글도비\docs\narrative-router\material-revival-ladder-harness.md
3. C:\Users\User\Desktop\글도비\docs\blockguide\SSOT_blockguide-integrated-order.md
4. C:\Users\User\Desktop\글도비\docs\2026-04-06\meta-language-leak-context-handoff.md
5. C:\Users\User\Desktop\글도비\docs\narrative-router\SSOT_bi-evolution-metadata-standard.md
6. C:\Users\User\Desktop\글도비\docs\2026-04-06\10pair_tr_bi_consistency_bounded_survey.md
7. C:\Users\User\Desktop\글도비\docs\2026-04-07\10pair_tr_bi_legacy_meta_cleanup_10terminal_opus_order.md

대상 pair:
- TR: C:\Users\User\Desktop\글도비\treatments\07_office_checkup_next_day_tr_block_070_draft.json
- BI: C:\Users\User\Desktop\글도비\bible\07_bi_office_checkup_next_day.json

특이사항:
- prior survey에서 pair 07은 `BI metadata/end-state drift`가 이미 살아 있는 `mixed` pair다
- meta wording과 truth drift를 반드시 분리해서 적어라

할 일:
- read-only bounded survey only
- allowed_structural_meta vs diegetic_meta_ref vs label_meta_ref vs blocked_by_pair_truth를 분리
- pair 07만 조사
- no repair
- no code edits
- no docs/temp edits

산출물:
- C:\Users\User\Desktop\글도비\docs\2026-04-07\10pair_meta_cleanup_terminal07_pair07.md
```

### Opus Terminal 08

```text
서사 오더다. 기존 numbered pair 08의 legacy meta wording cleanup 여부만 read-only로 조사한다.

먼저 읽을 것:
1. C:\Users\User\Desktop\글도비\docs\narrative-router\SSOT_narrative-router-integrated-order.md
2. C:\Users\User\Desktop\글도비\docs\narrative-router\material-revival-ladder-harness.md
3. C:\Users\User\Desktop\글도비\docs\blockguide\SSOT_blockguide-integrated-order.md
4. C:\Users\User\Desktop\글도비\docs\2026-04-06\meta-language-leak-context-handoff.md
5. C:\Users\User\Desktop\글도비\docs\narrative-router\SSOT_bi-evolution-metadata-standard.md
6. C:\Users\User\Desktop\글도비\docs\2026-04-06\10pair_tr_bi_consistency_bounded_survey.md
7. C:\Users\User\Desktop\글도비\docs\2026-04-07\10pair_tr_bi_legacy_meta_cleanup_10terminal_opus_order.md

대상 pair:
- TR: C:\Users\User\Desktop\글도비\treatments\08_pantech_cyworld_reborn_tr_block_070_draft.json
- BI: C:\Users\User\Desktop\글도비\bible\08_bi_pantech_cyworld_reborn.json

할 일:
- read-only bounded survey only
- allowed_structural_meta vs diegetic_meta_ref vs label_meta_ref를 분리
- pair 08만 조사
- no repair
- no code edits
- no docs/temp edits

산출물:
- C:\Users\User\Desktop\글도비\docs\2026-04-07\10pair_meta_cleanup_terminal08_pair08.md
```

### Opus Terminal 09

```text
서사 오더다. 기존 numbered pair 09의 legacy meta wording cleanup 여부만 read-only로 조사한다.

먼저 읽을 것:
1. C:\Users\User\Desktop\글도비\docs\narrative-router\SSOT_narrative-router-integrated-order.md
2. C:\Users\User\Desktop\글도비\docs\narrative-router\material-revival-ladder-harness.md
3. C:\Users\User\Desktop\글도비\docs\wuxguide\SSOT_wuxguide-integrated-order.md
4. C:\Users\User\Desktop\글도비\docs\2026-04-06\meta-language-leak-context-handoff.md
5. C:\Users\User\Desktop\글도비\docs\narrative-router\SSOT_bi-evolution-metadata-standard.md
6. C:\Users\User\Desktop\글도비\docs\2026-04-06\10pair_tr_bi_consistency_bounded_survey.md
7. C:\Users\User\Desktop\글도비\docs\2026-04-07\10pair_tr_bi_legacy_meta_cleanup_10terminal_opus_order.md

대상 pair:
- TR: C:\Users\User\Desktop\글도비\treatments\09_wuxia_heavenly_physician_tr_block_070_draft.json
- BI: C:\Users\User\Desktop\글도비\bible\09_bi_wuxia_heavenly_physician.json

할 일:
- read-only bounded survey only
- wuxguide semantics를 적용
- allowed_structural_meta vs diegetic_meta_ref vs label_meta_ref를 분리
- pair 09만 조사
- no repair
- no code edits
- no docs/temp edits

산출물:
- C:\Users\User\Desktop\글도비\docs\2026-04-07\10pair_meta_cleanup_terminal09_pair09.md
```

### Opus Terminal 10

```text
서사 오더다. 기존 numbered pair 10의 legacy meta wording cleanup 여부만 read-only로 조사한다.

먼저 읽을 것:
1. C:\Users\User\Desktop\글도비\docs\narrative-router\SSOT_narrative-router-integrated-order.md
2. C:\Users\User\Desktop\글도비\docs\narrative-router\material-revival-ladder-harness.md
3. C:\Users\User\Desktop\글도비\docs\blockguide\SSOT_blockguide-integrated-order.md
4. C:\Users\User\Desktop\글도비\docs\2026-04-06\meta-language-leak-context-handoff.md
5. C:\Users\User\Desktop\글도비\docs\narrative-router\SSOT_bi-evolution-metadata-standard.md
6. C:\Users\User\Desktop\글도비\docs\2026-04-06\10pair_tr_bi_consistency_bounded_survey.md
7. C:\Users\User\Desktop\글도비\docs\2026-04-07\10pair_tr_bi_legacy_meta_cleanup_10terminal_opus_order.md

대상 pair:
- TR: C:\Users\User\Desktop\글도비\treatments\10_jaebeol3se_loss_line_tr_block_070_draft.json
- BI: C:\Users\User\Desktop\글도비\bible\10_bi_jaebeol3se_loss_line.json

특이사항:
- prior survey에서 pair 10은 `TR incomplete vs BI ahead`가 이미 살아 있는 `mixed` pair다
- meta wording 조사와 `TR 58-70 completion first` 판단을 반드시 분리해서 적어라

할 일:
- read-only bounded survey only
- allowed_structural_meta vs diegetic_meta_ref vs label_meta_ref vs blocked_by_pair_truth를 분리
- pair 10만 조사
- no repair
- no code edits
- no docs/temp edits

산출물:
- C:\Users\User\Desktop\글도비\docs\2026-04-07\10pair_meta_cleanup_terminal10_pair10.md
```

## 12. 3-Pass Audit

Pass 1. Structure and Scope

- fixed the document type as `bounded parallel survey order`
- fixed the scope to the live numbered `01-10` pair set only
- separated this survey order from later repair execution work

Pass 2. Evidence and Consistency

- re-checked the live pair inventory against the current `treatments/` and `bible/` files
- anchored the policy to `meta-language-leak-context-handoff.md` and `SSOT_bi-evolution-metadata-standard.md`
- carried forward the prior `10pair` consistency verdict so pair `07` and pair `10` are not mis-routed
- recorded baseline commit and dirty summary so the order does not collide with current unrelated workspace edits

Pass 3. Execution and Readability

- converted the wave into `10 terminals / 1 pair per terminal` because terminal capacity matches pair count
- kept output ownership non-overlapping by giving each terminal exactly one pair and one output file
- tightened the output contract so Opus must classify `allowed_structural_meta` versus actual leakage instead of blindly counting tokens
- added pair-specific guardrails for `07` and `10` so wording cleanup does not leapfrog existing truth blockers

Confidence: `97%`
