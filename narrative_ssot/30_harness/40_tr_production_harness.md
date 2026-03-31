# TR Production Harness

Status: scaffold draft
Date: 2026-03-31

## Goal

`phase0_design` 기반으로 `TR`를 순차 생산한다.

## Required Inputs

- `30_planning/phase0_design.json`
- `40_contracts/production/tr_block_070_draft.schema.json`
- `40_contracts/production/sequential_run_status.schema.json`

## Required Outputs

- `40_production/tr_block_070_draft.json`
- `40_production/sequential_run_status.json`

## Rules

- 1-block sequential production
- same order max 5 blocks
- each 10 blocks self-audit gate
- resume authority = `sequential_run_status.json`

