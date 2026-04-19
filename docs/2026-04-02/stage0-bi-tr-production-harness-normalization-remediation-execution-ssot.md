Date: 2026-04-02
Status: parked (2026-04-19 reactivation refresh; first bounded source-of-truth declaration tranche landed on 2026-04-07, the remaining runtime handoff and production-harness normalization debt is still real, and the honest queue reading is now parked Stage0 source-of-truth debt rather than active implementation progress)
Canonical Path: `docs/2026-04-02/stage0-bi-tr-production-harness-normalization-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage0-bi-tr-production-harness-normalization-remediation-execution-ssot.md`
Baseline Commit: `eac3386ce3b19f720e6e12548721df5abe2ee755`
Baseline Dirty Summary: `dirty: prior Stage3 and Stage4 bounded tranches, the Stage0 enrich tranche, and queue docs were already in flight during the 2026-04-07 re-audit`
Source Survey Docs:
- `docs/2026-04-02/stage0-bible-generation-dna-sync-stage2-consume-bounded-survey.md`
- `docs/2026-04-19/stage0-bi-tr-production-harness-normalization-reactivation-refresh.md`
Evidence Artifacts:
- `docs/2026-04-02/stage0-bible-generation-dna-sync-stage2-consume-evidence.json`
Side-Effect Coverage:
- `scripts/build_bi_from_phase0_and_tr.py` routed BI builder contract
- `scripts/build_wuxia_bi_from_phase0_and_tr.py` family-specific BI builder contract
- `modules/core/project_manager.py` DNA sync and DB bible anchor overwrite path
- `modules/core/stage0_handoff.py` Stage0 contract declaration and canonical payload normalization path
- `modules/core/stage2_orchestrator.py` downstream consume path
- `modules/core/stage2_preflight.py` downstream readiness path

# 1. Answer First

This lane is no longer unopened.

The first bounded tranche is now landed, and it does one narrow job: declare the Stage0 source-of-truth split explicitly instead of leaving it implicit in builder, sync, and handoff side effects.

The landed contract says:

- `treatment.blocks` is the canonical material source
- `MasterBible` is a BI projection artifact, not the upstream material owner
- `db_anchor:bible` is the runtime handoff owner
- `MasterBible.plot_roadmap` remains the structured authority for the BI-side roadmap projection
- Stage2 intake still consumes the runtime handoff path rather than the raw BI file directly

This is intentionally bounded.

- broad Stage0 builder redesign is still deferred
- broad Stage2 or Stage4 rewrite from inside this lane is still deferred
- runtime handoff normalization is still the next tranche, not closure

# 2. Why This Lane Exists

The structural debt was never just "the BI file is inconsistent."

The real split-truth problem is that runtime behavior is spread across:

- builder output
- treatment material
- compatibility sync and roadmap backfill
- DB bible anchor overwrite
- Stage2 runtime intake

That means the practical contract is a chain, not a single artifact schema.

This lane exists to normalize that chain in a controlled order:

1. declare owners and boundaries
2. reduce compatibility-bridge authority
3. normalize the production harness only after the runtime handoff contract is explicit

# 3. Landed Tranche: Source-of-Truth Declaration

Date landed: `2026-04-07`

Primary code anchors:

- `modules/core/stage0_handoff.py`
- `modules/core/project_manager.py`
- `modules/core/stage2_orchestrator.py`

Primary test anchors:

- `tests/test_bi_tr_canonical_contract.py`
- `tests/test_stage0_handoff_ingress.py`
- `tests/test_stage2_orchestrator.py`
- `tests/test_blockguide_bi_builder.py`
- `tests/test_wuxia_bi_builder_contract.py`

What changed:

- canonical treatment payloads now carry a structured `_stage0_contract`
- canonical BI payloads now carry a structured `_stage0_contract`
- stale `MasterBible._stage0_contract` sidecars are stripped from the canonical BI copy
- DNA sync now logs that it remains a compatibility bridge and reports the runtime handoff owner explicitly
- Stage2 bootstrap now surfaces the Stage0 runtime handoff contract instead of silently depending on DB anchor truth

# 4. Current Findings After Re-Audit

1. The builder side is not the main ambiguity anymore.
   - current BI builders can emit `plot_roadmap`, `protagonist_config`, and normalized treatment linkage

2. Runtime still treats the DB bible anchor as the effective handoff truth.
   - `force_sync_v25_dna()` remains in the path
   - roadmap backfill and save behavior still shape the runtime payload

3. Stage2 trust is attached to the runtime handoff path, not to the raw BI artifact path.

4. The unresolved risk is therefore owner ambiguity, not just missing fields.

5. The first tranche materially improves this by expressing:
   - artifact role
   - artifact truth
   - field authority
   - runtime handoff owner
   - projection source

# 5. Scope

## Included in this lane

- Stage0 BI/TR production-harness contract inventory
- source-of-truth declaration for treatment, BI projection, and DB handoff roles
- explicit authority for `plot_roadmap`
- compatibility-bridge demotion language and transport
- minimal downstream surfacing into Stage2

## Excluded from this tranche

- broad builder rewrite
- projection-model conversion
- Stage2 or Stage4 major intake redesign
- canary or live proof work
- queue reprioritization

# 6. Execution Shape

## Tranche 1

source-of-truth declaration

Status: landed

- declare treatment vs BI vs DB runtime roles structurally
- attach `_stage0_contract` to canonical payloads
- surface the runtime handoff owner in Stage2-facing logs

## Tranche 2

runtime handoff normalization

Status: next bounded continuation

- reduce `force_sync_v25_dna()` and roadmap backfill toward a narrower compatibility bridge
- make Stage2 handoff transport explicit without broad Stage2 logic churn
- continue reducing silent overwrite behavior

## Tranche 3

production harness normalization

Status: deferred

- choose between `canonical material schema -> BI/TR projection`
- or keep dual artifacts with a fixed, explicit contract

# 7. Queue Placement

This lane is now a partially realized long-horizon Stage0 source-of-truth lane.

It remains below the proof-deferred front stack and below the already active Stage4, Stage3, and Stage2 normalization families because:

- the runtime is not currently blocked by this lane
- the blast radius is still wider than the nearer bounded slices
- the landed tranche only established contract truth; it did not finish the handoff normalization

Queue implication:

- this tranche removes the last `pending` code-first lane from the current queue
- after this update there is no remaining unopened implementation lane in the active queue snapshot
- code-first continuation should stay inside this active Stage0 BI/TR lane unless the queue is explicitly redefined

# 8. Next Action

Continue `Tranche 2: runtime handoff normalization`.

Bounded priorities for the next pass:

- keep `force_sync_v25_dna()` framed as a compatibility bridge
- keep `db_anchor:bible` as the currently declared runtime handoff owner until the replacement boundary is ready
- normalize Stage2 intake transport without broad Stage2 prompt or runtime redesign
- do not widen into full builder-family refactors

# 9. Validation Targets For This Tranche

Focused validation for the landed tranche must stay centered on:

- `tests/test_bi_tr_canonical_contract.py`
- `tests/test_stage0_handoff_ingress.py`
- `tests/test_stage2_orchestrator.py`
- `tests/test_blockguide_bi_builder.py`
- `tests/test_wuxia_bi_builder_contract.py`

Static checks must also cover the touched Stage0 and Stage2 files plus this SSOT and temp mirror through UTF-8 hygiene and queue validators.

# 10. 3-Pass Audit

Pass 1. Structure / scope
- the lane is now recorded as active and partially realized rather than promoted pending
- the landed tranche, deferred tranches, and non-goals are separated clearly
- owner language is tied to concrete runtime boundaries

Pass 2. Evidence / consistency
- the 2026-04-02 survey and evidence artifacts still anchor the lane rationale
- the 2026-04-07 re-audit confirmed that live code still routes runtime truth through the DB bible anchor
- the landed contract matches the current `stage0_handoff -> project_manager -> stage2_orchestrator` chain

Pass 3. Execution / readability
- the next bounded continuation is explicit
- overreach is trimmed: no broad builder rewrite, no proof claim, no queue reorder
- queue truth now reflects that this lane is active rather than unopened

Confidence: `97%`

# 11. 2026-04-19 Reactivation Refresh

Source doc:

- `docs/2026-04-19/stage0-bi-tr-production-harness-normalization-reactivation-refresh.md`

Current reading:

- the first bounded source-of-truth declaration tranche is landed
- the remaining runtime handoff and production-harness normalization work is still real
- the lane is not stale, but it is also not active progress anymore

Queue consequence:

- keep this lane visible
- keep the temp mirror
- treat it as parked Stage0 source-of-truth debt rather than active implementation progress
