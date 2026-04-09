# Production Pair Operational Registry v1

Date: 2026-04-09 (last updated; initial 2026-04-08 benchmark freshness wave)
Status: active
Scope: durable operational registry for current schema-clean production pairs

## 1. Role

Use this registry when you need the current operator reading of:

- full pair inventory beyond numbered slot manifests
- durable operational state after the 2026-04-08 canonicalization wave
- benchmark alias presence
- benchmark freshness
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

## 3. Current Inventory

| work_id | family | inventory role | durable operational state | schema | alias | benchmark freshness | operator use |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `투자물_골든_카나리아 테스트_canonical_v1` | `blockguide` | `numbered_live_pair` | `newly_touched_live_pair` | `pass` | `GREENPLUS` | `current` | benchmark-fresh numbered live pair; safe for current family baseline reading |
| `chaebol_allowance_zero` | `blockguide` | `numbered_live_pair` | `newly_touched_live_pair` | `pass` | `GREENPLUS` (historical withdrawn) | `pending_refresh` | withdrawn false-pass record; negative exemplar only, not safe for current family baseline reading |
| `chaebol_ent_empire` | `blockguide` | `numbered_live_pair` | `newly_touched_live_pair` | `pass` | `GREENPLUS` | `current` | benchmark-fresh live pair; safe for current family baseline reading |
| `defense_defect_engineer` | `blockguide` | `numbered_live_pair` | `regenerated_pair` | `pass` | `GREENPLUS` | `current` | benchmark-fresh regenerated live pair; safe for current family baseline reading |
| `office_checkup_next_day` | `blockguide` | `numbered_live_pair` | `newly_touched_live_pair` | `pass` | `GREENPLUS` | `current` | benchmark-fresh live pair; safe for current family baseline reading |
| `pantech_cyworld_reborn` | `blockguide` | `numbered_live_pair` | `newly_touched_live_pair` | `pass` | `GREENPLUS` | `current` | benchmark-fresh live pair; safe for current family baseline reading |
| `wuxia_heavenly_physician` | `wuxguide` | `numbered_live_pair` | `regenerated_pair` | `pass` | `GREENPLUS` | `current` | benchmark-fresh regenerated live pair; safe for current family baseline reading |
| `jangyeongshil_industrial_revolution` | `blockguide` | `unslotted_live_pair` | `new_live_pair` | `pass` | `GREEN` | `current` | 2026-04-09: TR Block 1-70 complete + bi_refresh + 3 audit layers PASS (5-Pass self / 7-Pass mechanical / 3-Pass philosophy). canon §5.2 4-step formula 70/70 (100%), Lock 8/8, BI verbatim-sync 100%. Still outside numbered-slot manifest |
| `manual_meridian_archivist` | `wuxguide` | `unslotted_live_pair` | `new_live_pair` | `pass` | `GREEN` | `current` | benchmark-fresh unslotted live pair; positive alias granted, still outside numbered-slot manifest |

## 4. Slot Manifest Interlock

- `docs/2026-04-07/01_10_canonical_pair_manifest.md` still governs numbered `01~10` slot interpretation
- this registry governs the actual full operational inventory, including unslotted live works
- do not assume numbered-slot manifest and full live inventory are identical

## 5. Current Operator Rule

- use `20_pitch` canon and readiness docs for fresh pitch selection and Phase0 promotion gates
- use this registry when you need pair-side family exemplars or benchmark-freshness truth
- current aliased pairs are benchmark-fresh unless they explicitly carry `pending_refresh` or withdrawn-historical notes; still respect inventory roles and the `GREEN` vs `GREENPLUS` shelf split when citing them operationally

## 6. 2026-04-09 Update Log

- `chaebol_allowance_zero` positive reading withdrawn after the opening pacing false-pass triage
  - operator artifact:
    - `docs/2026-04-09/chaebol_allowance_zero_opening_pacing_false_pass_triage.md`
  - registry reading:
    - `benchmark_alias = GREENPLUS` is preserved as a historical snapshot only
    - `benchmark_freshness = pending_refresh`
    - operator use = withdrawn false-pass record / negative exemplar only
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
