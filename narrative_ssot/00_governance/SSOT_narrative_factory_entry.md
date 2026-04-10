# SSOT Narrative Factory Entry

Status: scaffold draft
Date: 2026-03-31

## Purpose

`narrative_ssot/`의 엔트리 문서다.
이 문서는 새 수직 계층 구조에서 무엇을 먼저 읽고, 무엇이 아직 legacy authoritative인지 고정한다.

## Read Order

1. 이 문서
2. `authority_map.md`
3. `../30_harness/00_entry_router.md`
4. 해당 stage 하네스
5. 해당 stage schema
6. `../40_contracts/quality_gates.json`

## Current Operating Mode

현재 모드는 `dual-path safe mode`다.

- 신규 scaffold path를 열어 둔다.
- 기존 경로를 끊지 않는다.
- legacy와 scaffold가 충돌하면 명시적으로 cutover되지 않은 축에서는 legacy가 우선한다.

## Current Stage Chain

추천 생산 체인:

1. `reference_selection`
2. `source_manifest`
3. `profile_lock`
4. `material_bundle_summary`
5. `phase0_ready_snapshot`
6. `phase0_design`
7. `tr_block_070_draft`
8. `bi_output`
9. `release_gate`

## Immediate Rule

- 신규 작품 pilot 외에는 기존 작품을 여기로 자동 이관하지 않는다.
- `reference_selection` 없이 few-shot 적용 완료라고 판정하지 않는다.
- `phase0` 없이 TR 금지
- `verified TR` 없이 BI 금지
- `release_gate` PASS 전 완료 선언 금지
