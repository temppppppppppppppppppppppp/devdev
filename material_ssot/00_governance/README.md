# Governance

This directory owns the stage-axis governance for `material_ssot`.

Design baseline:

- `docs/2026-04-03/material-side-order-ssot-design.md`

Core docs:

- `authority-map.md`
- `stage-read-order.md`
- `donor-review-and-adoption-contract-v1.md`
- `downstream-episode-pacing-hint-attachment-harness-v1.md`
- `legacy-map.md`
- `work-coverage-matrix.md`
- `bootstrap-status.md`
- `production-pair-schema-standard-v1.md`
- `production-pair-operating-policy-addendum-v1.md`
- `production-pair-benchmark-spec-v1.md`
- `production-pair-operational-registry-v1.md`
- `pre-new-pitch-operational-readiness-v1.md`
- `external-model-benchmark-operation-harness-v1.md`
- `external-model-benchmark-launch-playbook-v1.md`
- `external-model-benchmark-prompt-template-v1.md`
- `external-model-material-benchmark-one-shot-order-template-v1.md`
- `external-model-material-benchmark-example-office_checkup_next_day-v1.md`
- `external-model-material-benchmark-example-line_stop_deputy-v1.md`

Live report exemplar:

- `docs/2026-04-07/material_benchmark_office_checkup_next_day_report.md`

Operator-training HOLD exemplar:

- `docs/2026-04-07/material_benchmark_line_stop_deputy_hold_example.md`

Operator-training REJECT exemplar:

- `docs/2026-04-07/material_benchmark_legacy_import_042_reject_example.md`

Quick operator card:

- `docs/2026-04-07/material_benchmark_pass_hold_reject_cheat_sheet.md`

Launch generator:

- `python -X utf8 scripts/material_benchmark_order_generator.py --pitch <pitch-md> [--promotion-intent none|canon|phase0]`
- `python -X utf8 scripts/material_benchmark_batch_generator.py [--path <dir>] [--promotion-intent auto|none|canon|phase0]`

Normalization runner:

- `python -X utf8 scripts/production_pair_normalization_runner.py`
- `python -X utf8 scripts/production_pair_normalization_runner.py --work-id <work_id> [--json]`

Pre-new-pitch gate:

- `python -X utf8 scripts/pre_new_pitch_readiness_gate.py`

Suggested read order:

1. `bootstrap-status.md`
2. `authority-map.md`
3. `legacy-map.md`
4. `stage-read-order.md`
5. `donor-review-and-adoption-contract-v1.md` before promoting fresh candidates into `Phase0` or calling a touched pair ready
6. `work-coverage-matrix.md`
7. `production-pair-schema-standard-v1.md` when normalizing or auditing existing `BI/TR` pairs
8. `production-pair-operating-policy-addendum-v1.md` when deciding live migration debt, donor decision visibility, grade refresh, or provenance fallback
9. `downstream-episode-pacing-hint-attachment-harness-v1.md` when attaching or auditing range-complete immediate-use pacing hints
10. `production-pair-operational-registry-v1.md` when reading current live inventory, durable pair state, or benchmark freshness
11. `production-pair-benchmark-spec-v1.md` after schema normalization is clear
12. `pre-new-pitch-operational-readiness-v1.md` before starting a fresh pitch wave

Role:

- define current canonical stage paths
- define what remains legacy, mirror, scaffold, or deferred
- define how a reader should traverse the material-side order without mixing family routing and system routing
- show which representative works are already connected end-to-end
- show which gaps remain before a later cutover wave
- define how existing live `TR + BI` pairs are benchmarked and grade-capped

This directory should remain documentation-first during the current bounded slice.
