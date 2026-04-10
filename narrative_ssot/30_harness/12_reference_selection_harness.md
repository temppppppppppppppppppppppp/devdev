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
- file slug와 작품 타이틀이 다르거나 Stage0/Phase0에 `TODO` title이 남기 싫으면 `work_identity_override.title`로 명시 lock 허용
- 이름 표면 drift를 더 막고 싶으면 `work_identity_override.commercial_label`, `work_identity_override.slug_aliases`까지 같이 잠근다
- `work_identity_override.reason`에는 왜 title authority를 reference_selection에서 선점하는지 한 줄로 남긴다
- selected card 조합이 lane을 흔들 수 있으면 `profile_override.primary_profile`로 명시 lock 허용
- `profile_override.reason`에는 왜 heuristic inference를 덮는지 한 줄로 남긴다
- opening macro battlefield와 reader-earning path를 heuristic에 맡기기 싫으면 `opening_bundle_contract_override`로 잠근다
- `opening_bundle_contract_override`는 `TR 2~6` 윈도우와 `signboard / reevaluation / next-ticket` 블록을 함께 고정해야 한다
