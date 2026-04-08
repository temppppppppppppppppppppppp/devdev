# Pre-New-Pitch Operational Readiness v1

Date: 2026-04-08
Status: active
Scope: repo-level readiness gate before starting a fresh pitch wave

## 1. Role

This document closes the gap between:

- pair-side schema cleanup
- pitch-side readiness harnesses
- repo-level operator preflight

Use it before:

- a new fresh-pitch batch
- a new canon-selection wave
- a new pre-Phase0 promotion wave

## 2. Required PASS Set

Before a fresh pitch wave starts, the repo should pass all of:

1. governance substrate
   - `python -X utf8 scripts/validate_material_ssot.py`
2. live pair normalization inventory
   - `python -X utf8 scripts/production_pair_normalization_runner.py`
3. pitch-side readiness docs
   - `python -X utf8 scripts/material_readiness_validator.py --path material_ssot/20_pitch`

Convenience gate:

- `python -X utf8 scripts/pre_new_pitch_readiness_gate.py`

## 3. How To Read The Result

`PASS` means:

- governance docs and bounded authority paths are coherent
- tracked pairs are schema-clean under the current normalization contract
- pitch candidate/canon/synthesis docs are machine-valid under the readiness harness

`PASS` does not automatically mean:

- every benchmark-fresh pair should be treated as the same kind of operational reference; inventory-role distinctions still matter

That freshness is tracked separately in:

- `production-pair-operational-registry-v1.md`

## 4. Current Operator Rule

- for fresh pitch judgment, rely on `material-benchmark-readiness-harness-v1.md` and `material_promotion_gate.py`
- for pair-side family reference, consult `production-pair-operational-registry-v1.md`
- if a pair is `unslotted_live_pair`, respect that inventory role even when benchmark freshness is `current`
- numbered `GREEN` pairs are live and benchmark-fresh, but they still sit below the `GREENPLUS` exemplar shelf

## 5. Current 2026-04-08 Snapshot

- tracked pair inventory: schema-clean
- tracked pair inventory: benchmark-fresh
- `material_ssot/20_pitch`: validator-pass
- bounded governance substrate: validator-pass

This means new pitch work is operationally unblocked, and pair-side fresh baseline claims can rely on the current registry so long as inventory-role distinctions and the `GREEN` vs `GREENPLUS` shelf split are respected.
