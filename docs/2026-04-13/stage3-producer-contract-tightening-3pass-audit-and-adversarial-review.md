# Stage3 Producer Contract Tightening 3-Pass Audit And Adversarial Review

Date: 2026-04-13
Status: final
Audit Type: `3-pass audit + 1x adversarial review`
Canonical Path: `docs/2026-04-13/stage3-producer-contract-tightening-3pass-audit-and-adversarial-review.md`
Baseline Commit: `32d6f0c8b56898fd8a370ae13684043d4cfda91a`
Baseline Dirty Summary: `snapshot main plus local Stage3 producer tranche/doc/test edits and live-run artifacts remain present; no audit-time revert performed`
Evidence Artifacts:
- `docs/2026-04-13/stage3-producer-3pass-audit-adversarial-evidence.json`
- `0_temp.txt`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/core/response_schemas.py`
- `config/prompts/ensemble.yaml`
- `modules/domain/agents/unified_blueprint_validator.py`
- `tests/test_blueprint_ensemble_generate_ensemble.py`
- `tests/test_unified_blueprint_validator_lane_c.py`
- `tests/test_blueprint_patch_mode.py`

## 1. Intent

Re-audit the current `Stage3 producer smartening` tranche after the latest cheap-admission hardening, then run one explicit adversarial pass before any new live-proof claim.

This audit answers four questions:

1. did the landed producer tranche remain coherent across prompt, schema, cheap admission, validator, and runtime?
2. did the tranche reopen any fresh `P0/P1` seam?
3. does one hostile review still find bypasses large enough to matter operationally?
4. should the queue direction change before the next bounded `ep7/ep8` rerun?

## 2. Scope

Included:

- `Stage3` producer prompt contract
- `Stage3` response schema and cheap-admission gate
- validator alignment on `opening_transition`, `protagonist_state`, `scene_completeness`, and `tactical_semantic_fidelity`
- current regression coverage and one explicit adversarial review pass

Excluded:

- broad `Director` retuning
- broad `Stage4` semantic judge retuning
- live rerun execution in this turn
- new code realization beyond audit/evidence documentation

## 3. Pass 1. Inventory

Current landed producer-side tightening is real and test-backed.

1. Prompt layer now states `opening_transition`, scene completeness, and tactical-authority expectations explicitly in `config/prompts/ensemble.yaml`.
2. Cheap admission in `modules/domain/agents/blueprint_ensemble.py` now rejects:
   - missing or invalid `opening_transition`
   - empty or placeholder `protagonist_state`
   - scene shells whose `key_events` are not actionable
   - some obvious tactical-authority intrusion cases before validator spend
3. Downstream validator ownership remains intact in `modules/domain/agents/unified_blueprint_validator.py`; this tranche did not move final truth ownership away from the validator/runtime surfaces.
4. Fresh regression status stayed green during this audit:
   - `pytest tests/test_blueprint_ensemble_generate_ensemble.py -q` -> `26 passed`
   - `pytest tests/test_unified_blueprint_validator_lane_c.py -q` -> `29 passed`
   - `pytest tests/test_blueprint_patch_mode.py -q` -> `74 passed`

Pass 1 result:

- no fresh `P0/P1` reopen from the landed tranche itself
- producer-side strictness is materially higher than the pre-tranche state
- the tranche is not yet fully parity-closed across `prompt -> schema -> cheap admission`

## 4. Pass 2. Semantic Findings

### Finding 1 — `P2`

`BLUEPRINT_SCHEMA` still accepts payloads that omit `opening_transition` and `protagonist_state`, even though the producer contract now treats both as materially binding.

Evidence:

- `modules/core/response_schemas.py` keeps `BLUEPRINT_SCHEMA.required` at `["episode_number", "scene_breakdown", "integrated_scenario"]`
- `modules/domain/agents/blueprint_ensemble.py` rejects missing `opening_transition` and non-meaningful `protagonist_state` only after response extraction / sanitize
- `docs/2026-04-13/stage3-producer-3pass-audit-adversarial-evidence.json` records:
  - `"schema_missing_opening_transition_and_protagonist_state_still_valid": true`

Meaning:

- this is not a truth-corruption bug
- it is still avoidable spend and contract drift
- the prompt/schema/cheap-gate stack is tighter than before, but not fully aligned yet

### Finding 2 — `P2`

The new producer-side tactical intrusion detector can be neutralized by authority text that merely contains intrusion markers as backstory or memory, because the current gate short-circuits once both an entry marker and a conflict marker appear anywhere in `tactical_excerpt`.

Evidence:

- `modules/domain/agents/blueprint_ensemble.py`:
  - `_detect_unauthorized_tactical_intrusion(...)` returns early when authority text already contains both marker families
  - that logic does not distinguish current-episode authorization from quoted memory / past reference / caution text
- `docs/2026-04-13/stage3-producer-3pass-audit-adversarial-evidence.json` records:
  - `"tactical_intrusion_marker_under_backstory_authority": ""`
  - `"sanitize_allows_intrusion_under_backstory_authority": true`
  - the hostile candidate still survives sanitize with `opening_transition.type = "jump_opening"`

Meaning:

- this does not reopen a truth-authority bug because validator/runtime still remain downstream backstops
- it does weaken the intended cost-first producer barrier
- the exact class most at risk is `authority mentions intrusion lexically, but only as memory/reference`, while the live candidate invents a new present-tense intrusion

### Finding 3 — `P3`

Regression coverage is healthy for the landed tranche, but the new adversarial seams are not yet pinned by tests.

Evidence:

- current Stage3 producer tests cover:
  - opening-transition normalization/inference
  - placeholder protagonist-state rejection
  - scene-completeness gaps
  - one direct tactical-intrusion reject case
- there is no committed regression test yet for:
  - schema-level omission parity
  - tactical-authority backstory-marker bypass

Meaning:

- present coverage is good enough for landed bounded work
- it is not yet sufficient to claim the producer gate is adversarially sealed

## 5. Adversarial Pass

One hostile pass was run directly against the current `Stage3` producer helpers.

Hostile probes:

1. schema parity probe
   - payload omitted `opening_transition` and `protagonist_state`
   - `validate_response_against_schema(..., BLUEPRINT_SCHEMA)` still returned `True`
2. tactical-authority backstory probe
   - authority text mentioned `괴한` / `협박` only as past memory
   - candidate then introduced a new present-tense `괴한 난입 -> 멱살 -> 협박` sequence
   - `_detect_unauthorized_tactical_intrusion(...)` returned empty
   - sanitize still admitted the candidate

Adversarial conclusion:

- the landed producer tranche is directionally correct
- the tranche is not yet adversarially sealed
- the residual seams are bounded, static, and local to the same `Stage3` producer owner surface

## 6. Pass 3. Execution Consequence

Queue consequence:

- no fresh `P0/P1`
- no new queue family
- no roadmap override from this audit alone

Operational reading:

1. the current workspace is safe to keep as the live audit baseline
2. the next bounded `ep7/ep8` rerun is still valid if the operator wants live proof first
3. if the operator wants the strictest cost-first posture before spending on rerun, one more bounded static slice is justified inside the same parent lane:
   - close `BLUEPRINT_SCHEMA` parity for producer-binding fields, or add an equally early fail-closed pre-schema contract gate
   - harden tactical-authority detection so lexical backstory mention does not count as present-tense authorization

This audit does **not** promote those two residuals to a new active queue item yet.

## 7. Final Verdict

- `fresh P0`: none found
- `fresh P1`: none found
- `fresh P2`: two bounded residuals
  - schema/producer contract parity drift
  - tactical-authority backstory-marker bypass
- `fresh P3`: regression-net gap for those adversarial seams

Recommended reading:

- keep the current parent owner unchanged
- treat this audit as the new current-state check for `Stage3 producer` quality
- do not claim the producer gate is fully sealed until either:
  - the two residuals are patched, or
  - a fresh rerun proves they are operationally irrelevant for the current episode family

Confidence: `96%`
