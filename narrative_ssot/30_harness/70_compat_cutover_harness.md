# Compat Cutover Harness

Status: scaffold draft
Date: 2026-03-31

## Goal

새 scaffold path와 legacy path가 충돌 없이 공존하게 만든다.

## Safe Mode

- pilot work만 scaffold-first
- all existing works remain legacy-first
- legacy export path stays available

## Current Export Targets

- `treatments/{work_id}_phase0_design.json`
- `treatments/{work_id}_tr_block_070_draft.json`
- `bible/0_bi_{work_id}.json`

## Conflict Rule

- cutover가 명시되지 않은 경우 legacy authority가 우선한다
- pilot work에서만 scaffold authority를 실험할 수 있다

