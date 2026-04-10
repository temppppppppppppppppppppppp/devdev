# Production Pair Operational Registry v1

Date: 2026-04-10 (last updated; initial 2026-04-08 benchmark freshness wave)
Status: active
Scope: durable operational registry for current schema-clean production pairs

## 1. Role

Use this registry when you need the current operator reading of:

- full pair inventory beyond numbered slot manifests
- durable operational state after the 2026-04-08 canonicalization wave
- benchmark alias presence
- benchmark freshness
- opening pacing triage status
- whether a pair is safe to cite as a current family baseline, or should stay reference-only

Machine-readable SSOT:

- `production-pair-operational-registry-v1.json`

Freshness closeout artifact:

- `docs/2026-04-08/production-pair-benchmark-freshness-wave.md`

## 2. Reading Rule

- `schema status = pass` means the pair is clean under the current normalization contract
- `benchmark freshness = current` means a fresh benchmark or bounded benchmark-preservation audit exists after the latest material touch/regeneration
- `benchmark freshness = pending_refresh` means a historical benchmark result exists, but the pair was materially touched or regenerated after that benchmark snapshot, or a previously current positive reading was withdrawn after a false-pass finding
- `benchmark freshness = unbenchmarked` means no benchmark-grade artifact exists yet
- `reference_pair` is non-live and never counts as active baseline inventory
- `opening pacing triage` is a separate operator field from `benchmark alias`
- `opening pacing triage = YELLOW` means `opening exemplar use suspended pending manual re-audit`; it does not automatically rewrite alias filenames
- `opening pacing triage = RED` means discard/archive-first reading at the opening-pacing layer
- `benchmark_alias = GREENPLUS` alone does not mean deployable live sell-in quality
- operational deployable `GREENPLUS` requires stricter closure:
  - `benchmark_freshness = current`
  - opening pacing triage currently `GREEN`
  - no whole-run `YELLOW` or `UNTRIAGED` hold
  - no active repair / re-audit / hold note
  - no remaining legacy-heuristic-only ambiguity for the opening claim
- if those are not all true, read the row as a historical benchmark snapshot, not a current sales-facing top shelf

## 3. Current Inventory

| work_id | family | inventory role | durable operational state | schema | alias | benchmark freshness | opening pacing triage | opening exemplar use |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `투자물_골든_카나리아 테스트_canonical_v1` | `blockguide` | `numbered_live_pair` | `newly_touched_live_pair` | `pass` | `GREENPLUS` | `current` | `GREEN` | provisional keep; not a discard candidate, but not a fresh declared-contract opening exemplar certification |
| `chaebol_allowance_zero` | `blockguide` | `numbered_live_pair` | `newly_touched_live_pair` | `pass` | `RED` | `current` | `RED` | negative exemplar archive; withdrawn GREENPLUS tombstone retained as anti-benchmark |
| `chaebol_ent_empire` | `blockguide` | `numbered_live_pair` | `newly_touched_live_pair` | `pass` | `GREENPLUS` | `current` | `GREEN` | provisional keep after targeted opening compression repair; not a fresh declared-contract opening exemplar certification |
| `defense_defect_engineer` | `blockguide` | `numbered_live_pair` | `regenerated_pair` | `pass` | `GREENPLUS` | `current` | `GREEN` | deployable GREENPLUS certified by 2026-04-10 manual closeout; current sell-in top shelf |
| `office_checkup_next_day` | `blockguide` | `numbered_live_pair` | `newly_touched_live_pair` | `pass` | `GREENPLUS` | `current` | `YELLOW` | repair-first YELLOW; office/decision battlefield overstay candidate |
| `pantech_cyworld_reborn` | `blockguide` | `numbered_live_pair` | `newly_touched_live_pair` | `pass` | `GREENPLUS` | `current` | `GREEN` | provisional keep after bounded cadence + reevaluation-surface repair; not a fresh declared-contract opening exemplar certification |
| `wuxia_heavenly_physician` | `wuxguide` | `numbered_live_pair` | `regenerated_pair` | `pass` | `GREENPLUS` | `current` | `GREEN` | opening GREEN only; whole-run pacing re-audit downgraded it to YELLOW because late blank-opponent drag appears in B61/B65/B66/B70 |
| `jangyeongshil_industrial_revolution` | `blockguide` | `unslotted_live_pair` | `new_live_pair` | `pass` | `GREEN` | `current` | `RED` | negative exemplar archive on opening pacing; spot audit confirmed work-level opening promise miss despite positive alias history |
| `manual_meridian_archivist` | `wuxguide` | `unslotted_live_pair` | `new_live_pair` | `pass` | `GREEN` | `current` | `GREEN` | provisional keep; not a discard candidate, but not a fresh declared-contract opening exemplar certification |

## 4. Slot Manifest Interlock

- `docs/2026-04-07/01_10_canonical_pair_manifest.md` still governs numbered `01~10` slot interpretation
- this registry governs the actual full operational inventory, including unslotted live works
- do not assume numbered-slot manifest and full live inventory are identical

## 5. Current Operator Rule

- use `20_pitch` canon and readiness docs for fresh pitch selection and Phase0 promotion gates
- use this registry when you need pair-side family exemplars or benchmark-freshness truth
- current aliased pairs are benchmark-fresh unless they explicitly carry `pending_refresh` or withdrawn-historical notes; still respect inventory roles and the `GREEN` vs `GREENPLUS` shelf split when citing them operationally
- `GREENPLUS` should be read quality-first and money-first:
  - not `pretty good`
  - not `repairable later`
  - but `good enough to trust as real market-facing material`
- also respect `opening pacing triage`
- `YELLOW` triage pair is not a discard archive yet, but opening exemplar use is suspended until manual re-audit
- `RED` triage pair is archive-first, not repair-first
- practical reading:
  - if a row still says `provisional keep`, `repair-first`, `whole-run YELLOW`, `UNTRIAGED`, or similar qualifier, do not treat it as deployable `GREENPLUS` even if the alias column still shows `GREENPLUS`

## 6. 2026-04-10 Update Log

- `RED` is terminal in current operator governance
  - `negative exemplar archive`
  - no repair budget
  - do not reopen unless the governing law itself changes
- opening pacing triage wave recorded under `docs/2026-04-10/production-pair-opening-pacing-triage-wave.md`
  - scope: currently discoverable live `TR` inventory (`15` pairs)
  - result: `RED 3 / YELLOW 2 / GREEN 9 / UNTRIAGED 1`
  - operator law:
    - `RED` = `negative exemplar archive`
    - `YELLOW` = `manual re-audit before repair`
    - `GREEN` = provisional keep, not an automatic alias refresh order
    - `UNTRIAGED` = opening evidence window incomplete; hold until `B01~B10` exists
  - working queue split:
    - `kill-first review`: none (resolved by spot audit: `jangyeongshil_industrial_revolution` -> `RED`, later bounded repair moved `pantech_cyworld_reborn` to provisional keep)
    - `repair-first`: `office_checkup_next_day`, `smart_new_hire`
    - `forensic re-audit`: none (resolved by spot audit: `jaebeol3se_loss_line` -> `RED`)
- whole-run pacing re-audit wave recorded under `docs/2026-04-10/green-whole-run-pacing-reaudit-wave.md`
  - scope: prior `opening GREEN` queue (`7` pairs)
  - result: `YELLOW 1 / GREEN 5 / UNTRIAGED 1`
  - operator effect:
    - `wuxia_heavenly_physician` is no longer a full-run `GREEN`; late-run drag makes it whole-run `YELLOW`
    - `africa_farm_king` is not full-run `GREEN`; whole-run status is `UNTRIAGED` until more blocks exist
    - block-level manual spot-audit on the remaining `GREEN 5` found no additional downgrade case; keep shelf stands
  - registry effect:
    - `opening_pacing_triage` field added to schema-clean tracked pairs
    - `YELLOW` triage does not automatically rewrite `benchmark_alias`
    - `office_checkup_next_day`, `jangyeongshil_industrial_revolution` opening exemplar use suspended pending manual re-audit
- current `YELLOW` salvageability split recorded under `docs/2026-04-10/current-yellow-salvageability-split.md`
  - scope: opening `YELLOW 2` + whole-run `YELLOW 1`
  - result: `repair-worth-it 3 / kill-candidate 0`
  - operator effect:
    - no additional `RED` promotion from the current `YELLOW` shelf
    - next step is repair-cost ordering, not further discard escalation
- targeted opening compression repair for `chaebol_ent_empire` recorded under `docs/2026-04-10/chaebol_ent_empire_opening_signboard_compression_repair_note.md`
  - operator effect:
    - live opening signboard moved from `B09` to `B08`
    - pair `03` exits opening `YELLOW` and returns to provisional `GREEN` keep
    - deployable closeout is still separate because opening authority remains `legacy_heuristic`
- bounded cadence + reevaluation-surface repair for `pantech_cyworld_reborn` recorded under `docs/2026-04-10/pantech_cyworld_reborn_cadence_and_reevaluation_surface_repair_note.md`
  - operator effect:
    - live opening representative reevaluation moved from `B10` to `B02`
    - pair `08` exits opening `YELLOW` and returns to provisional `GREEN` keep
    - deployable closeout is still separate because opening authority remains `legacy_heuristic`
- deployable `GREENPLUS` clarification tightened
  - `GREENPLUS` is now explicitly read as a quality-first, sales-facing top shelf rather than a loose historical compliment band
  - a bare `benchmark_alias = GREENPLUS` is insufficient for operational sell-in use unless the stricter registry closures are also satisfied
  - until re-closed under that stricter law, treat existing `GREENPLUS` filename snapshots as benchmark-historical, not automatic ROI-positive deployment proof
- deployable `GREENPLUS` closeout recorded under `docs/2026-04-10/deployable-greenplus-closeout.md`
  - scope: current `benchmark_alias = GREENPLUS` live shelf (`6` rows)
  - result: `deployable GREENPLUS 1 / historical-only GREENPLUS snapshot 5`
  - operator effect:
    - `defense_defect_engineer` is the first row re-closed as live sell-in top shelf
    - use explicit closeout, not filename prestige, before any market-facing exemplar claim
- `defense_defect_engineer` deployable closeout recorded under `docs/2026-04-10/defense_defect_engineer_deployable_greenplus_closeout.md`
  - operator effect:
    - removes the remaining opening `legacy_heuristic` ambiguity for pair `04`
    - upgrades pair `04` from historical-only `GREENPLUS` snapshot to current deployable `GREENPLUS`
- `chaebol_allowance_zero` current live alias fixed to `RED` after the opening pacing false-pass triage
  - operator artifact:
    - `docs/2026-04-09/chaebol_allowance_zero_opening_pacing_false_pass_triage.md`
  - registry reading:
    - `benchmark_alias = RED`
    - `benchmark_freshness = current`
    - withdrawn historical tombstone retained at `production_pair_grade_aliases/GREENPLUS_chaebol_allowance_zero.md`
    - operator use = RED negative exemplar / anti-benchmark only
  - do not cite this pair as a current family baseline or opening exemplar
- `jangyeongshil_industrial_revolution` record updated after TR Block 70 completion + bi_refresh + 3 independent audit layers (all PASS)
  - audit trail:
    - `docs/2026-04-09/jangyeongshil_industrial_revolution_bi_audit_report.md` (7-Pass mechanical audit)
    - `docs/2026-04-09/jangyeongshil_industrial_revolution_3pass_audit_report.md` (3-Pass philosophy audit)
  - canon §5.2 4-step formula 70/70 (100% completeness)
  - Post-Patron Independence Lock 8/8 stages
  - BI verbatim-sync contract 100% (0 orphan chunks in BI plot_roadmap vs TR)
  - opponent top share 24.3% (under 30% threshold)
  - unique invention/method each 67/70 (95.7% unique)
  - benchmark_alias remains `GREEN` (unslotted); numbered-slot promotion and GREENPLUS upgrade require separate family-wide orders
  - Phase 3 automated checker waiver active (`docs/2026-04-09/jangyeongshil_industrial_revolution_phase3_waiver.md`)
