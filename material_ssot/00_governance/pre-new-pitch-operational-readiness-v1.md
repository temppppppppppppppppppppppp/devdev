# Pre-New-Pitch Operational Readiness v1

Date: 2026-04-09
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
- if a pair carries `pending_refresh` because a positive reading was withdrawn after a false-pass finding, treat it as a negative exemplar only
- numbered `GREEN` pairs are live and benchmark-fresh, but they still sit below the `GREENPLUS` exemplar shelf
- `GREENPLUS` exemplar shelf should be read as a deployable quality shelf, not a loose benchmark compliment
- if the registry row still carries provisional, repair-first, whole-run-unclean, or legacy-heuristic-only ambiguity, do not treat that pair as a current top-shelf sell-in reference even when the alias filename says `GREENPLUS`

## 5. Current 2026-04-09 Snapshot

- tracked pair inventory: schema-clean
- tracked pair inventory: benchmark-fresh except `chaebol_allowance_zero`, which is now a withdrawn false-pass historical record with `pending_refresh`
- `material_ssot/20_pitch`: validator-pass
- bounded governance substrate: validator-pass

This means new pitch work is operationally unblocked, and pair-side fresh baseline claims can rely on the current registry so long as inventory-role distinctions, withdrawn false-pass notes, and the `GREEN` vs `GREENPLUS` shelf split are respected.
