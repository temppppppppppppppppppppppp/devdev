# BI Build Harness

Status: scaffold draft
Date: 2026-03-31

## Goal

`phase0 + verified TR` 기반으로 `BI`를 만든다.

## Required Inputs

- `30_planning/phase0_design.json`
- verified `40_production/tr_block_070_draft.json`

## Required Output

- `50_bi/0_bi_{work_id}.json`

## Rule

- draft TR만 있고 verification이 없으면 BI 생성 금지
- builder는 `phase0_hash`, `tr_hash`를 기록해야 한다

