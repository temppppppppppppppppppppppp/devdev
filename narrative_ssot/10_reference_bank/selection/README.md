# reference_selection

Status: scaffold draft
Date: 2026-03-31

이 폴더는 작품별로 어떤 few-shot card를 실제로 선택했고, 왜 선택했는지 잠그는 계약 자리다.

핵심 원칙:

- `reference_selection.json`이 없으면 few-shot 적용 증거가 약한 상태로 본다.
- raw source path보다 `saved card`와 `handoff_label`을 우선 기록한다.
- `must_not_copy`와 `contamination_risk` 검토 여부를 같이 남긴다.

