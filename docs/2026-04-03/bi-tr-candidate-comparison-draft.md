# BI/TR Candidate Comparison Draft

Date: 2026-04-03
Status: draft
Owner Lane: `IDE-2`
Purpose: compare `Golden Canary` and current BI/TR harness outputs before freezing `canonical v1`

## 1. Compared Candidates

### Candidate A. Golden Canary

- BI: `bible/01_bi_투자물_골든_카나리아 테스트.json`
- TR: `treatments/01_tr_투자물_골든_카나리아 테스트.json`

### Candidate B. Current Modern Builder Family

- BI: `bible/06_bi_gatekeeper_heir.json`
- TR: `treatments/06_gatekeeper_heir_tr_block_070_draft.json`

### Candidate C. Current Wuxia Builder Family

- BI: `bible/09_bi_wuxia_heavenly_physician.json`
- TR: `treatments/09_wuxia_heavenly_physician_tr_block_070_draft.json`

## 2. Evidence Snapshot

All three pairs were re-checked through `scripts/check_bi_tr_consumability.py::inspect_pair`.

### Golden Canary

- pair verdict: `pair pass / TR pass / BI standalone mixed`
- canonical block count: `60`
- effective BI root contains both `plot_roadmap` and `protagonist_config`
- runtime protagonist subset present:
  - `world_origin`
  - `incarnation_type`
  - `pov`
  - `external_pov_insert_policy`
- weakness:
  - embedded BI roadmap entries still warn because `block_no` is missing in each entry

### Gatekeeper Heir

- pair verdict: `pair pass / TR pass / BI standalone mixed`
- canonical block count: `70`
- effective BI root does not expose `plot_roadmap`
- effective BI root does not expose `protagonist_config`
- runtime protagonist subset missing:
  - `world_origin`
  - `incarnation_type`
  - `pov`
  - `external_pov_insert_policy`
- weakness:
  - pair only passes because TR can still generate a canonical roadmap
  - raw BI is not authoritative enough on its own

### Wuxia Heavenly Physician

- pair verdict: `pair pass / TR pass / BI standalone mixed`
- canonical block count: `70`
- effective BI root exposes `plot_roadmap` and `protagonist_config`
- weakness:
  - embedded BI roadmap is mostly `title/summary` shell entries with no Stage 2 consumer-backed payload
  - `protagonist_config` is family-rich but misses the runtime identity subset

## 3. Judgement By Criterion

### Criterion 1. Stage2 Intake Readiness

- `Golden Canary`: strongest of the three, but still `mixed`
- `Gatekeeper Heir`: not acceptable as canonical BI shape because effective root misses `plot_roadmap`
- `Wuxia`: closer on container shape, but roadmap payload is too thin for direct Stage2 trust

Interim call:

- `Golden Canary` wins as reference specimen
- current families still depend on TR-side salvage

### Criterion 2. Runtime Identity Contract Completeness

- `Golden Canary`: clear winner
- `Gatekeeper Heir`: fail
- `Wuxia`: fail for runtime identity, even though domain flavor is richer

Interim call:

- runtime-facing `protagonist_config` should follow the Golden Canary subset

### Criterion 3. Silent Overwrite Resistance

- `Golden Canary`: better, but not yet rewrite-proof
- `Gatekeeper Heir`: weak; Stage0 must reconstruct missing truth
- `Wuxia`: weak; Stage0 can ingest it, but runtime still cannot trust the BI payload as-is

Interim call:

- current builder outputs are not yet safe as canonical source artifacts

### Criterion 4. Source-of-Truth Convergence

- all three still suffer from split truth between raw BI, raw TR, and DB anchor
- `Golden Canary` is the closest to runtime truth
- `Gatekeeper Heir` and `Wuxia` still lean on compatibility bridges

Interim call:

- canonical `v1` must explicitly reduce DB-anchor-only truth and treatment-only truth

### Criterion 5. Family-Wide Reproducibility

- `Golden Canary`: best specimen, not yet proven as a builder-wide format
- `Gatekeeper Heir` and `Wuxia`: builder-backed, but they do not converge to one effective contract

Interim call:

- canonical `v1` cannot simply be "whatever the current builders emit"

## 4. Decision Direction

Current direction remains:

- `Golden Canary` should be treated as the better runtime reference specimen
- current builder families are useful as production harness inputs, not as final canonical truth
- the most realistic target is still `hybrid canonical v1`

Meaning:

- keep the effective BI root discipline proven by `Golden Canary`
- require runtime-facing `protagonist_config` keys at the effective BI root
- keep current harness reproducibility goals
- promote TR to one canonical outer container instead of letting multiple wrappers drift

## 5. Proposed Canonical v1 Shape

### BI

- canonical owner is the effective BI root, not a root-level sidecar field that runtime ignores
- effective BI root must always include:
  - `plot_roadmap`
  - `protagonist_config`
- `protagonist_config` must include the runtime identity subset:
  - `world_origin`
  - `incarnation_type`
  - `pov`
  - `external_pov_insert_policy`

### TR

- inner block schema can stay close to current canonical treatment blocks
- outer container should converge to one dict wrapper with metadata plus `blocks`
- raw list TR should become legacy-compatible input, not preferred output

## 6. Next Steps

Do these in order:

1. freeze `canonical v1` contract draft for BI effective root and TR wrapper
2. write a field mapping table from:
   - `Golden Canary`
   - modern builder output
   - wuxia builder output
   to canonical `v1`
3. define `legacy -> canonical` normalization rules before changing builders
4. add a read-side normalizer so runtime can distinguish:
   - `canonical pass`
   - `legacy compatibility pass`
5. update BI/TR builders to emit canonical `v1`
6. add fixture tests for:
   - Golden Canary pair
   - one modern pair
   - one wuxia pair
7. only after that, consider promoting the parked BI/TR normalization SSOT into active queue

## 7. Practical Recommendation For IDE-2

Immediate focus should be:

- document the canonical `v1` contract first
- avoid touching queue docs yet
- avoid rewriting Stage0 handoff logic before the contract is frozen
- treat current Stage0 rewrite paths as compatibility bridges, not final design
