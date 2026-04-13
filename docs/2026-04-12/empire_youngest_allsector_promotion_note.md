# empire_youngest_allsector promotion note

Date: `2026-04-12`

## Scope

- promote the repaired quarantine pair into the live authority lane
- preserve `_quarantine` provenance
- verify the live pair with a fresh BI build and 5-pass audit

## Promoted live authority paths

- Phase 0: `treatments/phase0/empire_youngest_allsector_phase0_design.json`
- TR: `treatments/empire_youngest_allsector_tr_block_070_draft.json`
- BI: `bible/0_bi_empire_youngest_allsector.json`

## Provenance preservation

- preserved source Phase 0: `treatments/_quarantine/empire_youngest_allsector_phase0_design.json`
- preserved source TR: `treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json`
- preserved historical legacy BI: `bible/_quarantine/0_bi_empire_youngest_allsector.json`

## Byte / hash check

- quarantine Phase 0 -> live Phase 0: byte-identical
  - sha256: `fda1c64cce74a58024f368823e7a6ac7bfab2744a3a18edf57cc41633b594afa`
- quarantine TR -> live TR: byte-identical
  - sha256: `4f7f9be0a60dada47af4d6d162a5f3ef00850471406550b6bb8f6b3e75728b6d`
- temp probe BI -> live BI: not byte-identical by design
  - reason: live BI was rebuilt from live Phase 0 / live TR, so source-path metadata points at the promoted authority paths

## Live verification

- command:
  - `python -X utf8 scripts/build_bi_from_phase0_and_tr.py --phase0 treatments/phase0/empire_youngest_allsector_phase0_design.json --draft treatments/empire_youngest_allsector_tr_block_070_draft.json --output bible/0_bi_empire_youngest_allsector.json`
  - `python -X utf8 scripts/audit_bi_5pass.py --phase0 treatments/phase0/empire_youngest_allsector_phase0_design.json --draft treatments/empire_youngest_allsector_tr_block_070_draft.json --bi bible/0_bi_empire_youngest_allsector.json --report docs/2026-04-12/empire_youngest_allsector_promotion_bi_5pass.md`
  - `python -X utf8 scripts/validate_material_ssot.py`
- result:
  - fresh BI 5-pass: `PASS`
  - `production_density_gate = PASS`
  - `diegetic_meta_ref_count = 0`
  - `diegetic_block_ref_count(alias) = 0`
  - `label_meta_ref_count = 0`
  - `unresolved_foreshadow_count = 0`
  - `npc_continuity_mismatch_count = 0`
  - `bi_diegetic_meta_leak_count = 0`
  - `validate_material_ssot.py = PASS`

## Status decision

- verdict: `active promotion complete`
- current lane status: `live authority pair ready`
- next admissible step: optional bounded Stage 4 canary, or family/registry-side promotion bookkeeping if this pair is being considered for broader exemplar use
