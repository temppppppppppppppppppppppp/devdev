# 10-Pair TR/BI Legacy Meta Cleanup Execution Order

Date: 2026-04-07
Status: final
Document Type: bounded cleanup execution order
Canonical Path: `docs/2026-04-07/10pair_tr_bi_legacy_meta_cleanup_execution_order.md`
Scope: live numbered `01-10` `TR/BI` pairs only
Execution Mode: `bounded narrative cleanup / artifact edits allowed / no docs/temp mutation / no stage runtime work`
Owner: `Codex`
Baseline Commit: `5c71b81a36ab2cbae824c630bb63219354b913a8`
Baseline Dirty Summary: unrelated system-track dirty files and queue docs are already present; this execution order governs only live pair artifact cleanup under `treatments/` and `bible/`

## 1. Purpose

This execution order exists to realize the merged finding from:

- `docs/2026-04-07/10pair_tr_bi_legacy_meta_cleanup_bounded_survey.md`

The bounded goal is:

- remove legacy `Block / ARC / Phase / Stage / Bnn` wording from human-readable `TR/BI` fields across live numbered pairs `01-10`
- preserve allowed structural metadata
- keep pair truth unchanged

This is not:

- pair re-planning
- new `TR` generation
- new `BI` generation
- stage runtime validation
- `docs/temp/` execution-queue work

## 2. Source Authority

Use these in order:

1. `docs/2026-04-06/meta-language-leak-context-handoff.md`
2. `docs/narrative-router/SSOT_bi-evolution-metadata-standard.md`
3. `docs/2026-04-07/10pair_tr_bi_legacy_meta_cleanup_bounded_survey.md`
4. this execution order

For family overlays:

- pairs `01-08`, `10`: `docs/blockguide/SSOT_blockguide-integrated-order.md`
- pair `09`: `docs/wuxguide/SSOT_wuxguide-integrated-order.md`

## 3. Execution Contract

### 3.1 Allowed fields that must remain structural

Do not rewrite these just because they contain numbering:

- `block_id`
- `arc_id`
- `arc_no`
- `phase_no`
- `stage_no`
- `foreshadow_targets`
- `callback_sources`
- `evolution`

### 3.2 Forbidden human-readable leakage

Rewrite these when they carry `Block / ARC / Phase / Stage / Bnn` wording:

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

Also apply the inference rule:

- if the field is clearly prose, a short label, a reward line, a solution line, an event title, an NPC description, a history summary, a capital-delta explanation, or a cadence string, treat it as human-readable even if the exact key is not named above

### 3.3 Non-goals inside the patch wave

Do not:

- alter protagonist truth
- alter pair identity
- redesign arcs
- normalize unrelated schema naming
- touch `evolution`
- touch system docs or queue files

## 4. Merged Routing

From the merged survey:

- `01-09`: `cleanup_now`
- `10`: `cleanup_now`, but with staged entry

Execution meaning:

- no pair needs `truth_repair_first`
- no pair currently needs `tr_completion_first`
- pair `10` should start from the BI-side narrow tranche before the larger TR-side rewrite

## 5. Tranche Plan

### Tranche 1. Shared Label Cleanup

Target pairs:

- `01`
- `02`
- `03`
- `04`
- `05`
- `06`
- `07`
- `08`
- `10` BI-side first

Mandatory fixes:

- strip leading `ARC-0N - ` or equivalent from `section_rotation`
- replace `Phase N: ...` with natural-language labels plus structural numbering stored separately
- normalize short label fields that currently hold `ARC-0N`, `Block N`, or `Bnn` as display text

Typical touched paths:

- `TR: blocks[*].genre_ext.section_rotation`
- `BI: MasterBible.plot_roadmap[*].genre_ext.section_rotation`
- `BI: WorldState.opponent_transition_plan[*].phase`
- pair-local BI label lists such as `npc_timeline[*].arc_presence[*]`

Acceptance:

- human-readable label fields contain natural language only
- structural numbering still survives in allowed fields

### Tranche 2. Shared Prose Normalization

Target pairs:

- `01`
- `02`
- `03`
- `04`
- `05`
- `06`
- `07`
- `08`

Mandatory fixes:

- rewrite `foreshadow` prose to remove `Block / ARC / Bnn` wording
- rewrite `callback` prose to remove `Block / ARC / Bnn` wording
- move structural anchors into `foreshadow_targets` / `callback_sources` if needed
- rewrite `content.context / reward / solution / event_villain / stakes` when they carry structural wording

Acceptance:

- prose remains meaningful without number-meta
- no pair loses its causal relation or callback target
- mirrored TR/BI text stays synchronized where the BI mirrors TR `plot_roadmap`

### Tranche 3. BI-Only Tail Cleanup

Target pairs:

- `02`
- `03`
- `04`
- `05`
- `06`
- `07`
- `08`
- `10`

Typical BI-only surfaces:

- `KeyNPCs[*].desc`
- `HistoricalEvents[*].summary`
- `CapitalCurve[*].event`
- `ArcSheets.*`
- `Seeds.*`
- `Partners[*].cadence`
- `portfolio_history[*].total_assets`
- `BusinessAxis.expansion_order`

Pair-specific notes:

- pair `02`: strip BOM in the same patch
- pair `04`: strip BOM in the same patch
- pair `04`: explicitly decide the borderline `Phase0` process-tag wording before patching
- pair `08`: leave `_creation_note` / `_schema_description` out of this narrative cleanup wave

Acceptance:

- BI-only prose fields no longer carry forbidden meta wording
- administrative fields outside the narrative cleanup scope remain untouched

### Tranche 4. Wuxguide Overlay

Target pair:

- `09`

Mandatory rules:

- preserve `evolution` exactly as allowed metadata
- normalize surrounding `Bnn` shorthand in:
  - `martial_ext`
  - treasures
  - NPC turning points
  - faction/commercial prose fields

Acceptance:

- no `evolution` field is rewritten or degraded
- wuxia-specific prose reads naturally without `Bnn` shorthand

### Tranche 5. Pair 10 Staged Entry

Target pair:

- `10`

Stage order:

1. BI-side narrow cleanup first
   - `opponent_transition_plan[*].phase`
   - `npc_timeline[*].arc_presence[*]`
   - `arcs[0].exit_function`
2. only then open the larger TR-side wave
   - `section_rotation`
   - `foreshadow`
   - `callback`
   - other prose carriers

Reason:

- the prior `TR incomplete vs BI ahead` blocker is no longer visible in file shape
- but pair `10` is still the newest recovered pair and should not be used as the first full TR rewrite target

Acceptance:

- BI-side labels are clean before the large TR rewrite starts
- TR-side cleanup preserves the now-live `Block 58-70` content

## 6. Pair Grouping

### Group A. Shared Blockguide Core

Pairs:

- `01`
- `02`
- `03`
- `04`
- `05`
- `06`
- `07`
- `08`

Shared execution logic:

- `Tranche 1 -> Tranche 2 -> Tranche 3`

### Group B. Wuxguide Exception

Pair:

- `09`

Shared execution logic:

- `Tranche 4`

### Group C. Cautious Blockguide Recovery

Pair:

- `10`

Shared execution logic:

- `Tranche 5`

## 7. Guardrails

- Do not touch `docs/temp/`.
- Do not widen into pair-quality rewrite.
- Do not rewrite `block_id`, `arc_id`, or `evolution`.
- Do not use console rendering as encoding evidence.
- Before touching pair `02` or `04`, confirm BOM via byte-level read-back and remove only the BOM, not content.
- Before touching pair `10` TR late blocks, re-read the current live file bytes in UTF-8 and avoid any patch based on stale survey assumptions.
- If any pair’s live truth now diverges from the merged survey, stop and refresh the survey before patching that pair.

## 8. Validation Contract

After each pair or tranche patch:

1. byte-level UTF-8 read-back
2. JSON parse pass
3. spot grep for forbidden patterns in touched files only
4. spot verify allowed structural fields still remain

Minimum grep targets after patch:

- `Block [0-9]+`
- `ARC-[0-9]+`
- `Phase [0-9]+`
- `Stage [0-9]+`
- `B[0-9]{1,3}`

Interpretation rule:

- zero hits is not required in the full file because allowed structural metadata may still contain numbering
- zero hits is required in the touched human-readable fields

## 9. Stop Gates

Stop execution on a pair if:

- UTF-8 read-back disagrees with editor preview
- a supposed wording fix changes pair truth
- a field thought to be human-readable is actually the authoritative structural carrier
- pair `10` late-block truth looks unstable on fresh read-back
- pair `09` `evolution` would be touched by the proposed patch

## 10. Recommended Implementation Order

Highest ROI order:

1. shared label cleanup template on `01-08`
2. pair `02` and `04` BOM removal during their BI touch
3. shared prose normalization on `01-08`
4. BI-only tail cleanup on `01-08`
5. wuxguide pair `09`
6. pair `10` BI-side narrow pass
7. pair `10` TR-side larger pass

Reason:

- front-loads the most reusable cleanup logic
- keeps the highest-risk recovered pair (`10`) off the first wide rewrite tranche
- isolates the only family exception (`09`)

## 11. Deliverables

Execution artifacts expected from this order:

- touched `treatments/` and `bible/` pair files only
- one post-execution audit note summarizing:
  - which pairs were completed
  - which pairs were deferred
  - which borderline policy calls were needed

Do not create `docs/temp/` mirrors for this narrative cleanup order.

## 12. 3-Pass Audit

Pass 1:

- converted the merged survey into an execution-focused document
- kept scope bounded to narrative artifact cleanup only

Pass 2:

- aligned tranche routing with the merged survey verdict
- carried forward the pair `07` / `10` caution logic and the pair `02` / `04` BOM note
- preserved the pair `09` `evolution` exception as an explicit guardrail

Pass 3:

- organized the work into reusable tranches instead of ten unrelated pair orders
- kept stop gates and validation rules explicit so patch work stays bounded
- ensured the document tells the next operator exactly what to touch, what not to touch, and in what order

Confidence: `96%`
