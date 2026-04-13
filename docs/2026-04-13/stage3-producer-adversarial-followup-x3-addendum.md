# Stage3 Producer Adversarial Follow-Up X3 Addendum

Date: 2026-04-13
Status: final
Audit Type: `3 additional adversarial reviews`
Canonical Path: `docs/2026-04-13/stage3-producer-adversarial-followup-x3-addendum.md`
Prior Audit:
- `docs/2026-04-13/stage3-producer-contract-tightening-3pass-audit-and-adversarial-review.md`
Baseline Commit: `32d6f0c8b56898fd8a370ae13684043d4cfda91a`
Baseline Dirty Summary: `snapshot main plus local Stage3 producer/doc/test/live-run artifacts remain present; no audit-time revert performed`
Evidence Artifacts:
- `docs/2026-04-13/stage3-producer-adversarial-followup-x3-evidence.json`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/core/stage_cross_stage_contract.py`
- `tests/test_blueprint_ensemble_generate_ensemble.py`
- `tests/test_unified_blueprint_validator_lane_c.py`
- `tests/test_stage23_stage4_readiness_wave1.py`

## 1. Intent

Run three more hostile probes against the current `Stage3 producer` hardening after the first adversarial review had already found:

- schema/producer contract parity drift
- tactical-authority backstory-marker bypass

This addendum asks a narrower question:

- does another three-pass hostile sweep still keep the residuals in `P2/P3`, or is there now a stronger seam that should outrank the planned `ep7/ep8` rerun?

## 2. Scope

Included:

- `opening_transition` producer/validator parity
- `scene_completeness` cheap-admission strength
- `tactical_semantic_fidelity` synonym coverage under Korean runtime language

Excluded:

- new code realization
- queue mirror refresh
- rerun execution

## 3. Pass 1. Probe Inventory

Three distinct hostile probes were executed.

1. `opening_transition declared-vs-inferred mismatch`
2. `generic verby scene shell`
3. `Korean synonym tactical intrusion`

All raw outputs are recorded in:

- [stage3-producer-adversarial-followup-x3-evidence.json](/c:/Users/PC/Desktop/글도비/docs/2026-04-13/stage3-producer-adversarial-followup-x3-evidence.json)

## 4. Pass 2. Findings

### Finding 1 — `P2`

Producer cheap admission still allows a declared `opening_transition.type` that is syntactically valid but semantically contradictory to the inferred continuity contract.

Evidence:

- hostile candidate declared `direct_continuation`
- producer cheap admission returned `""`
- sanitize admitted the candidate
- validator later produced:
  - `opening_transition.type mismatch: declared 'direct_continuation' vs normalized 'jump_opening'`

Meaning:

- this remains a producer-only parity seam
- it does not bypass final truth ownership
- it still spends avoidable validator/runtime budget

### Finding 2 — `P3`

`scene_completeness` cheap admission is stronger than before, but it is still coarse enough to admit generic low-information verb shells.

Evidence:

- hostile candidate used scenes such as:
  - `He handles the situation.`
  - `He thinks about the next move.`
- producer cheap admission returned `""`
- validator later flagged downstream categories:
  - `scenario_density`
  - `opening_transition`
  - `continuity`
  - `timeline_specificity`

Meaning:

- the new gate is correctly blocking empty shells
- it is not yet blocking generic action-looking filler
- this is cost leakage, not a truth-corruption seam

### Finding 3 — `P1`

There is a stronger Korean synonym hole in `tactical_semantic_fidelity` than the earlier backstory-marker bypass.

Evidence:

- hostile candidate used current-episode physical coercion language outside the authorized tactical excerpt:
  - `들이닥쳐`
  - `팔목을 비틀다`
  - `주먹을 들이밀다`
  - `입막음을 강요하다`
- producer results:
  - cheap admission returned `""`
  - `_detect_unauthorized_tactical_intrusion(...)` returned `""`
  - sanitize admitted the candidate
- validator results:
  - with sufficient anchors/titles/locations/density, `_python_pre_validate(...)` returned `0` issues
  - specifically, no `tactical_semantic_fidelity` issue was emitted

Meaning:

- this is no longer only a `producer` seam
- the current tactical intrusion family is lexically too narrow in both producer and validator
- an unauthorized physical-threat event can be phrased in Korean synonym form and survive the full Python prevalidation surface

Severity reading:

- classify as `fresh P1`
- bounded, local, and patchable inside the current `Stage3` parent owner
- still serious enough to outrank another proof rerun if the goal is trustworthy tactical-authority enforcement

## 5. Validation Notes

Fresh validation during this addendum:

- `pytest tests/test_blueprint_ensemble_generate_ensemble.py -q` -> `26 passed`
- `pytest tests/test_unified_blueprint_validator_lane_c.py -q` -> `29 passed`
- `pytest tests/test_stage23_stage4_readiness_wave1.py -k "off_arc_intrusion or skips_tactical_intrusion_flag or disguised_intrusion" -q` -> `3 passed`

Additional note:

- full `tests/test_stage23_stage4_readiness_wave1.py -q` is **not** fully green right now
- two failures remain on stale expectations that still assert `fix_scope == "inplace"` for categories now promoted to `full`
- those failures are unrelated to the new hostile probes, but they do remain test-debt noise inside that file

## 6. Pass 3. Execution Consequence

This addendum changes the current priority reading.

Previous reading:

- one more bounded static tranche was optional
- the next `ep7/ep8` rerun remained acceptable as the immediate next proof step

Updated reading after hostile follow-up:

1. do **not** treat the producer/validator tactical-authority surface as rerun-ready
2. the immediate-next safest move is one bounded static patch inside the same parent lane:
   - widen Korean tactical intrusion coverage beyond the current marker lexicon
   - close producer and validator parity on that lexicon together
   - add regression tests for the newly proven synonym family
3. only after that patch should the next bounded `ep7/ep8` rerun resume as the authoritative proof step

Queue reading:

- no new queue family
- same parent Stage3 owner
- immediate-next residual changes from `rerun-first` to `patch tactical synonym hole first`

## 7. Final Verdict

- `fresh P0`: none
- `fresh P1`: one
  - Korean synonym tactical intrusion bypass survives producer and validator prevalidation
- `fresh P2`: one
  - declared opening-transition mismatch still leaks to validator
- `fresh P3`: one
  - generic verby scene shells still leak through cheap admission

Operational conclusion:

- the earlier first adversarial review found producer-side cost leaks
- this additional `x3` follow-up found one stronger truth-adjacent enforcement gap
- the tactical synonym hole is now the front `Stage3 producer/validator` blocker

Confidence: `97%`
