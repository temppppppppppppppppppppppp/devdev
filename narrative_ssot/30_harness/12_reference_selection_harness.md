# Reference Selection Harness

Status: scaffold draft
Date: 2026-03-31

## Goal

작품별 few-shot 적용 흔적을 `reference_selection.json`으로 잠근다.

## Input

- current work intent
- saved reference cards
- `reference_card_manifest`
- contamination / must_not_copy review

## Output

- `50_projects/{work_id}/10_reference_selection/reference_selection.json`
- `50_projects/{work_id}/10_reference_selection/contamination_guard.json`

## Minimum Rules

- 선택 카드는 보통 2~4장
- `card_slug`, `track`, `handoff_label` 필수
- `selection_reason` 필수
- `must_not_copy_applied = true` 확인
- `contamination_risk_reviewed = true` 확인

