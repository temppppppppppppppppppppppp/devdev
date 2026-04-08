# 20_pitch

Role:

- become the canonical stage hub for pitch and intake
- separate canonical pitch state from intake and archive state
- stabilize work-level pitch anchors and imported legacy payloads
- define a reusable pitch philosophy and minimum contract for new work-level canon files
- keep a stable protagonist-first constitution and a reusable selection checklist for fresh candidates
- hold a normalized operator synthesis lane between research packs and canonical pitch freeze

Transition note:

- `material_ssot/20_pitch/intake/legacy_import` now stores migrated payloads from the old `전처리_ssot/기획안` bundle
- `material_ssot/20_pitch/synthesis` stores one-page operator syntheses assembled from normalized research packs before canon selection
- `material_ssot/20_pitch/quarantine` stores pitch-adjacent docs that are not current pitch truth
- `전처리_ssot/docs/10_pitches` remains a legacy transition source
- `전처리_ssot/기획안` is now a frozen pointer path and should not receive new payloads

Bootstrap rule:

- use `synthesis/` as the normalized landing lane for fresh-candidate one-page syntheses
- feed `synthesis/` from `10_research/20_fewshot_bank` and, when present, `10_research/30_work_materials/{work_id}/90_material_pack.json`
- run `pitch-selection-checklist.md` on a synthesis before promoting it
- use `canon/` to register work-level pitch anchors
- use `intake/legacy_import/` for migrated legacy pitch payloads
- use explicit deferred notes when a standalone pitch file does not yet exist
- use `quarantine/` only for non-canonical pitch-adjacent docs
- point new references to `material_ssot/20_pitch` paths, not the old bundle
- current operator policy for active fresh candidates is `male protagonist only`
- female-protagonist candidates may remain as archive or research material, but do not enter active selection, canon, or downstream handoff lanes

Current canon rule:

- `cider-doctrine-v1.md` is the fast-entry first-block catharsis contract and should be read first inside `20_pitch`
- `material-benchmark-readiness-harness-v1.md` is the readiness gate for `selection-ready`, `canon`, and `Phase0-ready` claims
- `material_ssot/00_governance/delegation-envelope-spec-v1.md` is the cross-stage task envelope contract for delegated or external-model work
- `material_ssot/00_governance/work-current-truth-template-v1.md` defines the preferred shape of work-level current-truth docs such as `{work_id}_live_status.md`
- `python -X utf8 scripts/pre_new_pitch_readiness_gate.py` is the repo-level preflight before starting a new fresh-pitch wave
- `python -X utf8 scripts/material_readiness_validator.py --path <md-or-dir>` is the machine gate for future canon/intake/synthesis files
- `python -X utf8 scripts/material_promotion_gate.py --stage canon|phase0 --path <md> [--work-id <work_id>]` is the promotion gate for actual canon / Phase0 transitions
- `material_ssot/00_governance/production-pair-operational-registry-v1.md` is the current pair-side operational registry when a pitch operator needs family exemplars or benchmark freshness reading
- the machine gate targets candidate/canon/working-synthesis docs only; checklist audits, integration handoffs, and retire notes are not promotion targets
- `pitch-philosophy.md` is the canonical pitch philosophy and minimum contract
- `protagonist-first-constitution.md` is the current house-law document for protagonist design
- `pitch-selection-checklist.md` is the current fresh-candidate selection checklist
- `work-guard-translation-map.md` is the canonical bridge from pitch house law into downstream `work_guard.yaml` semantics
- `synthesis/` is the normalized operator handoff lane, not canonical pitch truth
- `canon/office_checkup_next_day.md` is the first active canonical pitch exemplar
- `canon/pantech_cyworld_reborn.md` is the second active canonical pitch exemplar
- other `canon/` work files may remain anchor notes until they are upgraded into full canonical pitch docs
- when a work has live or in-flight downstream artifacts, pair the pitch authority with a current-truth doc before delegating the next task

Current downstream companion pack:

- use the dated operator pack below when a pitch is being translated into a work-specific `work_guard`
- these docs are operating companions, not replacements for the canonical law docs above
- `python -X utf8 scripts/run_work_guard_v1.py --path <yaml>`
- `docs/2026-04-06/work-guard-validator-checklist-spec.md`
- `docs/2026-04-06/wg-v2-freeze-checklist.md`
- `docs/2026-04-06/wg-v3-drift-audit-card.md`

Large artifact write discipline:

- downstream `Phase0`, `TR`, and `BI` files may be large, but they must still be written by bounded unit
- do not treat a singular target path as permission for one-shot full overwrite
- if a downstream artifact is too large for a stable single save, keep JSON parseable and save incrementally by the active bounded unit
