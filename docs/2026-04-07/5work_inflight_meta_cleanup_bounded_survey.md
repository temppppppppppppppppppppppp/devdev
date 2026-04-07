# 5-Work In-Flight Meta Cleanup Bounded Survey

Date: 2026-04-07
Status: final
Document Type: bounded merge survey
Canonical Path: `docs/2026-04-07/5work_inflight_meta_cleanup_bounded_survey.md`
Scope: active in-flight production works identified by the 2026-04-06 handoff/status docs
Merge Owner: `Codex`
Execution Mode: `live artifact read-only survey -> bounded cleanup routing`
Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
Baseline Dirty Summary: no new queue or system-track mutation is introduced here; this survey only classifies cleanup readiness for live narrative artifacts under `treatments/` and `bible/`

## 1. Source Inputs

Primary handoff/status docs:

- `docs/2026-04-06/manual_meridian_archivist_context_handoff_b26.md`
- `docs/2026-04-06/jangyeongshil_industrial_revolution_production_status.md`
- `docs/2026-04-06/02_hoegui_surgeon_context_handoff.md`
- `docs/2026-04-06/permit_window_grade9_tr_production_status.md`
- `docs/2026-04-06/jaebeol3se_loss_line_tr_production_handoff.md`

Policy anchors:

- `docs/2026-04-06/meta-language-leak-context-handoff.md`
- `docs/narrative-router/SSOT_narrative-router-integrated-order.md`
- `docs/blockguide/SSOT_blockguide-integrated-order.md`
- `docs/wuxguide/SSOT_wuxguide-integrated-order.md`
- `docs/2026-04-07/10pair_tr_bi_legacy_meta_cleanup_bounded_survey.md`
- `docs/2026-04-07/10pair_tr_bi_legacy_meta_cleanup_execution_order.md`

Live artifact anchors:

- `treatments/manual_meridian_archivist_tr_block_070_draft.json`
- `treatments/jangyeongshil_industrial_revolution_tr_block_010_draft.json`
- `treatments/jangyeongshil_industrial_revolution_tr_block_011_015_draft.json`
- `treatments/jangyeongshil_industrial_revolution_tr_block_016_020_draft.json`
- `treatments/jangyeongshil_industrial_revolution_tr_block_021_025_draft.json`
- `treatments/preprocess/hoegui_surgeon/03_tr_blocks/tr_block_001_010.json`
- `treatments/preprocess/hoegui_surgeon/03_tr_blocks/tr_block_011_015.json`
- `treatments/preprocess/hoegui_surgeon/03_tr_blocks/tr_block_016_020.json`
- `treatments/preprocess/permit_window_grade9/03_tr_blocks/block_001.json`
- `treatments/preprocess/permit_window_grade9/03_tr_blocks/block_035.json`
- `treatments/10_jaebeol3se_loss_line_tr_block_070_draft.json`
- `bible/10_bi_jaebeol3se_loss_line.json`

## 2. Executive Verdict

Across the five in-flight works:

- `cleanup_now`: `3`
- `staged_cleanup`: `2`
- `truth_repair_first`: `0`
- `no_action`: `0`
- `P2`: `5`
- `P1/P0`: `0`

High-level reading:

- all five works still carry live `Block / ARC / Phase / Bnn` wording in human-readable narrative fields
- the listed 2026-04-06 handoff/status docs also contain heavy block/arc wording, but that is operator-facing context and should stay out of patch scope
- this is mostly a `TR` cleanup wave, not a broad `TR + BI` wave
- only `jaebeol3se_loss_line` has a live BI-side overlay worth tracking, and that BI is already marked stale by its own handoff
- no surveyed work shows a current narrative truth blocker that must be repaired before a bounded wording-cleanup execution order can be written

## 3. Aggregate Scoreboard

| Work | Family | Live State | Severity | Route | Smallest Cleanup Unit | Main Leak Shape | Merge Note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `manual_meridian_archivist` | `wuxguide` | TR saved `1-21`; `22-25` produced but not merged | `P2` | `staged_cleanup` | saved TR only, or post-merge `1-25` | residual `Block N` in injury status + `ARC-01` in `success_pattern` | do not pretend the handoff summary is merged truth |
| `jangyeongshil_industrial_revolution` | `blockguide` | TR saved `1-25`; `26` next | `P2` | `cleanup_now` | saved TR files `001-025` | `Block N` / `ARC-NN` in `foreshadow`, `callback`, `reward`, `next_door`, relation labels | clean separably from future production |
| `hoegui_surgeon` | `blockguide` | TR saved `1-20`; `21` next | `P2` | `cleanup_now` | saved TR files `001-020` | saturated `section_rotation = ARC-0N ...` plus callback/reward arc labels | strong shared template candidate |
| `permit_window_grade9` | `blockguide` | TR saved `1-35`; `36` next | `P2` | `cleanup_now` | saved TR files `001-035` | `ARC-0N` reward/power lines + `Bnn` in callback/relationship prose | strong shared template candidate |
| `jaebeol3se_loss_line` | `blockguide` | TR saved `1-57`; `58-60` not yet produced; BI stale | `P2` | `staged_cleanup` | TR first, BI later | heavy `section_rotation`, `foreshadow`, `content.solution` block refs; BI `phase` labels also dirty | do not waste effort cleaning stale BI before sync boundary is chosen |

## 4. Cross-Work Findings

### 4.1 Operator docs are evidence, not patch targets

The five handoff/status docs are full of `Block`, `ARC`, `Phase 0`, and `TR` references because their job is operator resumption.

That wording is not the problem this wave is trying to solve.

Patch-scope rule:

- use those docs to determine current saved range, next production pointer, and family overlay
- do not clean their block/arc terminology as part of the narrative artifact wave

### 4.2 Shared live leak families

The bounded scan found the same leak families across the active works:

1. label leakage
   - `section_rotation`
   - `next_door`
   - `success_pattern`
   - short reward/power labels that still surface `ARC-0N`
2. prose leakage
   - `foreshadow`
   - `callback`
   - `content.reward`
   - `content.solution`
   - `relationship_delta.before/after`
3. stale BI label leakage
   - currently observed only on `jaebeol3se_loss_line`
   - especially `opponent_transition_plan[*].phase`

This is enough to justify a separate in-flight cleanup order instead of burying these works inside the numbered-pair wave.

### 4.3 Heuristic density snapshot

Codex collected human-readable-path hits only, excluding obvious structural keys such as `block_id` and operator-only docs.

Result:

- `manual_meridian_archivist`: `4` hits
- `jangyeongshil_industrial_revolution`: `26` hits
- `hoegui_surgeon`: `30` hits
- `permit_window_grade9`: `27` hits
- `jaebeol3se_loss_line`: `166` hits

Interpretation:

- the first wave should not start with `jaebeol3se_loss_line`
- `hoegui_surgeon` and `permit_window_grade9` provide the cleanest reusable cleanup template
- `manual_meridian_archivist` is real but low-density and should be routed by merge-boundary stability, not by urgency

### 4.4 Work-specific route notes

#### 4.4.1 `manual_meridian_archivist`

Current evidence shows only a small number of saved-scope leaks.
However, the handoff explicitly says `Block 22-25` were produced in conversation and not merged into the live draft.

So the true route is:

- no truth repair is required before a cleanup order is written
- but a full-work cleanup pass should not assume `1-25` is live truth yet
- safest bounded choice is either:
  - clean saved `1-21` only, or
  - merge `22-25` first, then clean `1-25`

#### 4.4.2 `jangyeongshil_industrial_revolution`

The saved split TR files show repeated block/arc anchors inside `foreshadow`, `callback`, `reward`, and `next_door`.
These are classic human-readable cleanup targets and do not require new generation.

#### 4.4.3 `hoegui_surgeon`

This work is the clearest shared-template case.
`section_rotation` is repeatedly stored as `ARC-01` / `ARC-02` style display text, and several reward/power lines also carry arc labels.

#### 4.4.4 `permit_window_grade9`

The work is structurally stable through saved `Block 35`, but its human-readable power/reward/callback surfaces still carry `ARC-0N` and `Bnn` wording.
The dominant leak is not file-shape instability but lingering meta-language in story-facing lines.

#### 4.4.5 `jaebeol3se_loss_line`

This is the highest-density work by a large margin.
The live TR draft still carries widespread `ARC-0N` and `Block N` wording in human-readable fields, and the live BI still carries `Phase N: ...` style labels.

Important boundary:

- the handoff itself says the BI is old and needs sync
- so BI cleanup is real but should be staged behind either:
  - explicit BI sync work, or
  - a deliberate decision to patch the stale BI anyway

### 4.5 Truth blocker check

This survey did not find a current `truth_repair_first` condition analogous to the prior numbered-pair blockers.

What it did find instead:

- `manual_meridian_archivist`: merge-boundary caution
- `jaebeol3se_loss_line`: stale-BI caution

Those are execution-shape constraints, not narrative-truth blockers.

## 5. Recommended Execution Grouping

The evidence supports this bounded grouping:

1. shared stable-work TR cleanup template
   - `hoegui_surgeon`
   - `permit_window_grade9`
   - `jangyeongshil_industrial_revolution`
2. low-density staged micro-wave
   - `manual_meridian_archivist`
   - only after saved-range boundary is explicitly locked
3. high-density saved-TR wave
   - `jaebeol3se_loss_line` TR only
   - do not bundle the stale BI into the same first patch
4. sync-aligned BI cleanup
   - `jaebeol3se_loss_line` BI
   - only when the sync boundary is chosen

Default realization unit:

- do not treat a whole saved draft as one cleanup patch just because it lives in one file
- for works larger than `10` saved blocks, use `10-block sequential cleanup` as the default realization unit
- partial tail windows are allowed only for the last residual range such as `21-25`, `31-35`, or `51-57`

## 6. Recommended Next Step

Write one execution order dedicated to these five in-flight works with three explicit protections:

1. operator docs out of patch scope
2. `manual_meridian_archivist` merge-boundary stop gate
3. `jaebeol3se_loss_line` stale-BI stop gate
4. `10-block sequential cleanup` as the default realization unit for large files

## 7. Non-Goals

This survey does not authorize:

- handoff/status doc rewriting
- new TR generation
- merging `manual_meridian_archivist` `22-25`
- producing `jaebeol3se_loss_line` `58-60`
- BI sync realization
- full pair-quality repair beyond meta wording cleanup

## 8. 3-Pass Audit

Pass 1:

- rechecked the five listed handoff/status docs in UTF-8 to confirm current saved range and next production pointer
- separated operator-facing docs from artifact cleanup scope before classifying leak severity

Pass 2:

- rechecked live `treatments/` and `bible/` anchors with human-readable-path filtering rather than raw grep totals
- confirmed that `manual_meridian_archivist` and `jaebeol3se_loss_line` are staged because of execution shape, not because of truth failure

Pass 3:

- reread the merged verdict for wording drift and overclaim risk
- confirmed the document stays bounded to survey/order production and does not silently escalate into artifact patching

Confidence: `96%`
