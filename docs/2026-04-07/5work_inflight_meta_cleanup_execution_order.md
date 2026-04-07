# 5-Work In-Flight Meta Cleanup Execution Order

Date: 2026-04-07
Status: final
Document Type: bounded cleanup execution order
Canonical Path: `docs/2026-04-07/5work_inflight_meta_cleanup_execution_order.md`
Scope: active in-flight production works only
Execution Mode: `bounded narrative cleanup / artifact edits allowed / no operator-doc rewrites / no runtime stage work`
Owner: `Codex`
Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
Baseline Dirty Summary: this execution order governs only live narrative artifacts under `treatments/` and `bible/`; it does not touch queue docs, system-track artifacts, or the 2026-04-06 handoff/status docs

## 1. Purpose

This execution order realizes the merged finding from:

- `docs/2026-04-07/5work_inflight_meta_cleanup_bounded_survey.md`

The bounded goal is:

- remove legacy `Block / ARC / Phase / Bnn` wording from human-readable narrative fields in the five in-flight works
- preserve allowed structural metadata
- keep live production truth unchanged

This is not:

- operator handoff rewriting
- new TR generation
- TR merge recovery
- BI sync realization
- runtime canary or stage validation

## 2. Source Authority

Use these in order:

1. `docs/2026-04-06/meta-language-leak-context-handoff.md`
2. `docs/narrative-router/SSOT_narrative-router-integrated-order.md`
3. `docs/2026-04-07/5work_inflight_meta_cleanup_bounded_survey.md`
4. this execution order

Family overlays:

- `manual_meridian_archivist`: `docs/wuxguide/SSOT_wuxguide-integrated-order.md`
- `jangyeongshil_industrial_revolution`: `docs/blockguide/SSOT_blockguide-integrated-order.md`
- `hoegui_surgeon`: `docs/blockguide/SSOT_blockguide-integrated-order.md`
- `permit_window_grade9`: `docs/blockguide/SSOT_blockguide-integrated-order.md`
- `jaebeol3se_loss_line`: `docs/blockguide/SSOT_blockguide-integrated-order.md`

## 3. Execution Contract

### 3.1 Structural fields that must remain structural

Do not rewrite these just because they contain numbering:

- `block_id`
- `arc_id`
- `arc_no`
- `phase_no`
- `stage_no`
- `foreshadow_targets`
- `callback_sources`
- explicit saved-range metadata in operator docs

### 3.2 Human-readable leakage to rewrite

Rewrite these when they carry `Block / ARC / Phase / Stage / Bnn` wording:

- `content.*`
- `stakes`
- `reward`
- `power_shift.*`
- `relationship_delta.before`
- `relationship_delta.after`
- `genre_ext.section_rotation`
- `genre_ext.success_pattern`
- `genre_ext.capital_delta`
- `genre_ext.next_door`
- `foreshadow`
- `callback`
- `martial_ext.success_pattern`
- `martial_ext.injury_status.*`
- BI label fields such as `opponent_transition_plan[*].phase`

Inference rule:

- if the field is clearly prose, a short story-facing label, a reward line, a solution line, an event description, or an NPC/relationship note, treat it as human-readable even if the exact key is not listed above

### 3.3 Default processing unit

Default realization unit:

- when a live cleanup target spans more than `10` saved blocks, process it in `10-block` windows by default
- do not use full-file cleanup as the default just because the artifact is stored in a single draft file
- allow a smaller tail window only for the last residual range
- after each `10-block` window, run the validation contract before opening the next window

Default window map:

- `jangyeongshil_industrial_revolution`: `1-10`, `11-20`, `21-25`
- `hoegui_surgeon`: `1-10`, `11-20`
- `permit_window_grade9`: `1-10`, `11-20`, `21-30`, `31-35`
- `manual_meridian_archivist`: `1-10`, `11-21` or post-merge `11-20`, `21-25`
- `jaebeol3se_loss_line` TR: `1-10`, `11-20`, `21-30`, `31-40`, `41-50`, `51-57`

### 3.4 Parallelization policy

Default mode is sequential.

Allowed parallelism:

- limited work-level parallelism is allowed only for Tranche 1:
  - `hoegui_surgeon`
  - `permit_window_grade9`
  - `jangyeongshil_industrial_revolution`
- even in that case, each work must still advance one `10-block` window at a time
- never open two windows from the same work in parallel

Disallowed parallelism:

- do not run `manual_meridian_archivist` in parallel with its own merge-boundary uncertainty still unresolved
- do not run `jaebeol3se_loss_line` BI in parallel with its TR cleanup
- do not use parallel execution to skip per-window validation

Default operator reading:

- Tranche 1 may run in parallel by work
- after Tranche 1 closes, the remaining staged works run sequentially

### 3.5 Out of scope

Do not touch:

- the five 2026-04-06 handoff/status docs
- unsaved conversational summaries for `manual_meridian_archivist` `22-25`
- unwritten future blocks
- `jaebeol3se_loss_line` BI before its sync boundary is deliberately chosen

## 4. Merged Routing

From the bounded survey:

- `cleanup_now`: `jangyeongshil_industrial_revolution`, `hoegui_surgeon`, `permit_window_grade9`
- `staged_cleanup`: `manual_meridian_archivist`, `jaebeol3se_loss_line`
- `truth_repair_first`: none

Execution meaning:

- the first cleanup wave should start with stable saved TR artifacts, not with merge-boundary or stale-BI work
- `manual_meridian_archivist` is a low-density micro-wave
- `jaebeol3se_loss_line` is a high-density staged wave
- large-file cleanup should still advance in `10-block` sequential windows, not in one all-range patch

## 5. Tranche Plan

### Tranche 1. Shared Stable-Work TR Cleanup

Target works:

- `hoegui_surgeon`
- `permit_window_grade9`
- `jangyeongshil_industrial_revolution`

Mandatory fixes:

- strip `ARC-0N` or equivalent from `section_rotation`-style display labels
- rewrite `foreshadow` / `callback` prose so numbering lives in structure, not in story-facing sentences
- rewrite reward/power/next-door lines that currently narrate via `Block N` or `ARC-NN`

Typical touched paths:

- `TR: blocks[*].genre_ext.section_rotation`
- `TR: blocks[*].foreshadow[*]`
- `TR: blocks[*].callback[*]`
- `TR: blocks[*].content.reward`
- `TR: blocks[*].power_shift.*`
- `TR: blocks[*].genre_ext.next_door`
- `TR: relationship_delta.before/after`

Acceptance:

- story-facing text reads naturally without `Block / ARC / Bnn`
- structural numbering still survives in the allowed fields
- the next production pointer from each handoff doc remains unchanged
- each touched file/range is closed before the next `10-block` window opens

### Tranche 2. `manual_meridian_archivist` Saved-Scope Micro-Wave

Target work:

- `manual_meridian_archivist`

Stage order:

1. lock the cleanup boundary first
   - either saved `1-21` only
   - or post-merge `1-25` if merge recovery happens before the cleanup starts
2. then patch only the live saved scope in sequential windows
   - default: `1-10`, then `11-21`
   - post-merge alternative: `1-10`, `11-20`, then `21-25`

Mandatory fixes inside saved scope:

- `martial_ext.success_pattern`
- `martial_ext.injury_status.current`
- `martial_ext.injury_status.change`

Acceptance:

- no handoff-summary text is mistaken for merged TR truth
- no future `22-25` reconstruction assumptions leak into the patch

### Tranche 3. `jaebeol3se_loss_line` TR High-Density Wave

Target work:

- `jaebeol3se_loss_line` TR only

Stage order:

1. clean saved TR `1-57`
2. keep `58-60` unwritten scope untouched
3. do not patch the stale BI in the same first wave

Recommended internal grouping:

- saved `1-10`
- saved `11-20`
- saved `21-30`
- saved `31-40`
- saved `41-50`
- saved `51-57`

Mandatory fixes:

- `genre_ext.section_rotation`
- `foreshadow`
- `callback`
- `content.solution`
- `content.reward`
- other story-facing labels carrying `ARC-NN` or `Block N`

Acceptance:

- the saved TR reads naturally without arc/block meta in human-readable fields
- the saved future-production boundary remains `58-60 not yet produced`

### Tranche 4. `jaebeol3se_loss_line` BI Sync-Aligned Cleanup

Target work:

- `jaebeol3se_loss_line` BI

Entry condition:

- explicit decision to sync or deliberately patch the stale BI

Typical touched BI paths:

- `opponent_transition_plan[*].phase`
- `npc_timeline[*].arc_presence[*]`
- other story-facing labels that still mirror `ARC` / `Phase` wording

Acceptance:

- BI cleanup is done with sync awareness, not on a knowingly stale baseline
- BI wording changes do not invent arc truth that the unfinished TR has not yet locked

## 6. Guardrails

- Do not use the five handoff/status docs as patch targets.
- Do not rewrite `block_id`, `arc_id`, or other structural carriers.
- Do not widen into future or unwritten blocks.
- Do not claim `manual_meridian_archivist` `22-25` are live truth until they are actually merged.
- Do not clean `jaebeol3se_loss_line` BI as if it were current truth when the handoff itself marks it stale.
- Do not turn this wave into a pair-quality rewrite or a TR regeneration pass.
- Do not use console rendering as encoding evidence.

## 7. Validation Contract

After each `10-block` window or residual tail tranche:

1. byte-level UTF-8 read-back
2. JSON parse pass
3. touched-files-only grep for forbidden patterns
4. spot verify allowed structural fields still preserve numbering
5. confirm the next production pointer from the handoff/status doc did not change

Minimum grep targets after patch:

- `Block [0-9]+`
- `ARC-[0-9]+`
- `Phase [0-9]+`
- `Stage [0-9]+`
- `B[0-9]{1,3}`

Interpretation rule:

- zero hits is not required for the full file because structural metadata may still contain numbering
- zero hits is required in the touched human-readable fields

## 8. Stop Gates

Stop execution on a work if:

- UTF-8 read-back disagrees with editor preview
- a supposed wording fix changes production truth
- a field thought to be prose is actually the authoritative structural carrier
- `manual_meridian_archivist` merge recovery changes the live boundary mid-wave
- `jaebeol3se_loss_line` BI sync scope changes mid-wave
- a patch starts to require new TR generation instead of wording cleanup

## 9. Recommended Implementation Order

Highest ROI order:

1. Tranche 1 parallel group:
   - `hoegui_surgeon`
   - `permit_window_grade9`
   - `jangyeongshil_industrial_revolution`
   - rule: each work stays sequential by `10-block` window
2. `manual_meridian_archivist` after boundary lock
3. `jaebeol3se_loss_line` TR by `10-block` saved-range tranche
4. `jaebeol3se_loss_line` BI only after sync-boundary choice

Reason:

- front-loads the works with the cleanest shared cleanup template
- allows safe parallelism only where file ownership is disjoint
- keeps the low-density merge-boundary case (`manual_meridian_archivist`) off the first pass
- keeps the highest-density stale-BI case (`jaebeol3se_loss_line`) out of the template-discovery tranche

## 10. Deliverables

Realization under this order should produce:

- cleaned live TR files for the targeted saved ranges
- realization closed in `10-block` sequential windows by default for large files
- optional BI cleanup for `jaebeol3se_loss_line` only if the stale-BI entry condition is satisfied
- a short completion note documenting which works/tranches were actually realized

## 11. 3-Pass Audit

Pass 1:

- checked that the order remains bounded to narrative artifact cleanup and does not slide into handoff rewriting, merge recovery, or fresh production

Pass 2:

- rechecked each tranche against the survey so the staged routes for `manual_meridian_archivist` and `jaebeol3se_loss_line` stay explicit

Pass 3:

- rechecked stop gates, validation rules, and implementation order for hidden overreach
- confirmed the order stays executable without claiming stale or unmerged content is authoritative
- confirmed the default unit now stays `10-block sequential cleanup`, not whole-file realization
- confirmed the parallelization rule is bounded to work-level Tranche 1 only

Confidence: `96%`
