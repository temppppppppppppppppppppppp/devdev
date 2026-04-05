# reference_selection

Status: pointer note
Date: 2026-04-05

이 폴더는 shared selection sink가 아니라 `reference_selection` 계약을 설명하는 pointer note다.
실제 작품별 산출물은 `narrative_ssot/50_projects/{work_id}/10_reference_selection/` 아래에 저장한다.

핵심 원칙:

- `reference_selection.json`이 없으면 few-shot 적용 증거가 약한 상태로 본다.
- raw source path보다 `saved card`와 `handoff_label`을 우선 기록한다.
- `must_not_copy`와 `contamination_risk` 검토 여부를 같이 남긴다.

Operational pointer:

- schema: `narrative_ssot/40_contracts/reference/reference_selection.schema.json`
- harness: `narrative_ssot/30_harness/12_reference_selection_harness.md`
- scaffold writer: `scripts/create_narrative_project_scaffold.py`
