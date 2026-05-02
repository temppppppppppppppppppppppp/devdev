# Material-Side Pacing Range Harness Adversarial 3-Pass Audit

Date: 2026-05-02
Status: final
Scope: material-side immediate deployment harness after downstream episode pacing range gate insertion

## Verdict

`FAIL until cleanup`.

The new material-side range gate is directionally correct and should remain. However, it currently creates an authority mismatch: the governance docs now require a visible downstream episode pacing hint for immediate-use material, while the existing immediate-deployment shelf still names six rows without recorded per-block pacing range evidence.

Confidence: `96%`.

## Pass 1 - Contract Collision

Finding: `P0 / authority mismatch`.

- `material_ssot/README.md` now says immediate-deployment claims require a visible material-side downstream episode pacing hint or equivalent advisory range surface.
- `material_ssot/00_governance/production-pair-benchmark-spec-v1.md` now says missing or vague advisory range keeps a pair in benchmark/reference inventory.
- `docs/2026-04-29/material-side-immediate-deployment-overlay.md` still admits six immediate-deployment rows without naming the new pacing range surface.
- `material_ssot/00_governance/production-pair-operational-registry-v1.json` has no `downstream_episode_pacing_hint` or artifact field populated on the immediate-deployment rows.

Impact:

- An operator can read the overlay and registry as `immediate_deployable_material`, then read the new gate and conclude the same rows are not immediate-deployable.
- This is worse than a simple missing field because it affects the shelf label itself.

Required cleanup:

- Add a transition rule: either grandfather the existing six rows as `immediate_deployable_material_pending_range_hint_attachment`, or suspend immediate-use claims until a bounded range attachment audit closes each row.
- The safer reading is pending attachment, not silent grandfathering.

## Pass 2 - Surface Completeness

Finding: `P1 / range surface not yet operational enough`.

- The preferred field name `downstream_episode_pacing_hint` is now named.
- The minimum useful shape is named: `recommended_episode_count`, `acceptable_episode_range`, `stretch_cap`, and proof/receipt/next-gate beat.
- The exact placement is still loose. The docs do not yet lock whether the canonical TR path is `TR.blocks[*].genre_ext.downstream_episode_pacing_hint`, whether the BI mirror must be `MasterBible.plot_roadmap[*].genre_ext.downstream_episode_pacing_hint`, or whether a top-level BI summary is enough.
- Transitional equivalents are allowed, but no deprecation or acceptance limit is defined.

Impact:

- Different operators can attach different names and still claim compliance.
- TR/BI sync checks cannot become deterministic until the path and mirror rule are fixed.

Required cleanup:

- Declare a canonical path and allow transitional equivalents only for already-touched rows during the first retrofit wave.
- Require audits to report `TR coverage count`, `BI mirror count`, `mismatch count`, and `missing block ids`.

## Pass 3 - Cross-Doc Drift

Finding: `P0 / stale registry markdown`.

- `material_ssot/00_governance/production-pair-operational-registry-v1.json` records six immediate-deployment rows, including `pharma_cdmo_industry_heir`.
- `docs/2026-04-29/material-side-immediate-deployment-overlay.md` also lists six rows.
- `material_ssot/README.md` also lists six rows.
- `material_ssot/00_governance/production-pair-operational-registry-v1.md` still says the current shelf is five rows in multiple places and omits `pharma_cdmo_industry_heir` from the current inventory table.

Impact:

- The JSON and overlay say six; the markdown registry says five.
- Because the markdown registry is a human-facing operational surface, this can produce wrong operator routing even if the JSON is correct.

Required cleanup:

- Sync the registry markdown from the JSON/overlay and include the new range-hint gate language.

## Additional Findings

### Alias Snapshot Drift

Finding: `P1`.

`material_ssot/00_governance/production_pair_grade_aliases/README.md` lists current aliases but does not include `distressed_asset_heir` or `telecom_gate_monopoly_1997`, even though the registry records both as `GREENPLUS` immediate-deployment rows. The alias files themselves are also absent.

Required cleanup:

- Either create the missing alias files and update the README, or explicitly document that these immediate-deployment rows do not maintain alias snapshot files.

### Upstream Harness Gap

Finding: `P1`.

`material_ssot/20_pitch/material-benchmark-readiness-harness-v1.md` still allows `selection-ready` and `Phase0-ready` based on first-block cider ledger shape only. It does not yet require an upstream pacing-range handoff. `stage-read-order.md` sends fresh pitch promotion through that harness, so a new work can pass upstream material readiness without the range surface that now determines immediate-use classification downstream.

Required cleanup:

- Add an upstream advisory range check to the material benchmark readiness harness.
- For business-power or investment-family works, reference `material_ssot/20_pitch/investment-opening-pacing-spec-v1.md` as the default episode-side ruler.

## Final Recommendation

Do not revert the new range gate.

Next cleanup unit should be small and bounded:

1. Patch the registry markdown and overlay with an explicit `pending downstream episode pacing hint attachment` transition state.
2. Define canonical TR/BI range-hint paths.
3. Add the upstream range check to `material-benchmark-readiness-harness-v1.md`.
4. Then retrofit one pilot row, preferably `telecom_gate_monopoly_1997` or the planned `글도비_파이어플라이` test, before bulk-updating the six-row shelf.

## Follow-Up Cleanup Applied

Status: `PARTIAL REMEDIATION APPLIED`.

Applied in the same 2026-05-02 cleanup unit:

- overlay now reads the six admitted rows as `immediate_deployable_material_pending_downstream_episode_pacing_hint_attachment`
- registry markdown now includes `pharma_cdmo_industry_heir` in the six-row shelf and names the pending range attachment state
- registry JSON now records `range_attachment_status: pending_downstream_episode_pacing_hint_attachment` on the six admitted immediate-deployment rows
- canonical newly touched pair path is now locked as:
  - `TR.blocks[*].genre_ext.downstream_episode_pacing_hint`
  - `MasterBible.plot_roadmap[*].genre_ext.downstream_episode_pacing_hint`
- attachment audits now require `TR coverage count`, `BI mirror count`, `TR/BI mismatch count`, and `missing block ids`
- upstream material readiness harness now has a `Downstream Episode Pacing Range Check`

Remaining open work:

- no existing row is range-complete yet
- first pilot attachment is still needed, preferably `telecom_gate_monopoly_1997` or the planned `글도비_파이어플라이` experiment
- alias snapshot drift remains open for `distressed_asset_heir` and `telecom_gate_monopoly_1997`

## Evidence

- `material_ssot/README.md`: immediate-deployment range gate added under current immediate material deployment and TR block semantics.
- `material_ssot/00_governance/production-pair-benchmark-spec-v1.md`: advisory range gate now blocks immediate-use classification when missing or vague.
- `material_ssot/00_governance/production-pair-operating-policy-addendum-v1.md`: output contract now requires exact downstream episode pacing hint surface.
- `docs/2026-04-29/material-side-immediate-deployment-overlay.md`: six immediate-deployment rows listed without range-hint evidence.
- `material_ssot/00_governance/production-pair-operational-registry-v1.json`: six immediate-deployment rows parsed; no range-hint artifact field found.
- `material_ssot/00_governance/production-pair-operational-registry-v1.md`: stale five-row shelf language remains.
- `material_ssot/00_governance/production_pair_grade_aliases/README.md`: missing current alias entries for `distressed_asset_heir` and `telecom_gate_monopoly_1997`.
