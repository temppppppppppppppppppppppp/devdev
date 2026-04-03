# Reference Bank

Status: scaffold draft
Date: 2026-03-31

이 폴더는 few-shot / reference layer의 새 상위 자리다.

V0.1에서는 아직 실제 reference bank를 이 폴더로 완전 이관하지 않는다.
대신 아래 3가지를 먼저 고정한다.

- 작품별 `reference_selection` 계약
- 현재 authoritative reference bank로 가는 mirror 안내
- `reference_card_manifest.json` + `cards/` mirror

현재 authoritative 경로:

- `material_ssot/10_research/20_fewshot_bank/`

현재 mirror 경로:

- `narrative_ssot/10_reference_bank/reference_card_manifest.json`
- `narrative_ssot/10_reference_bank/cards/`
- `narrative_ssot/10_reference_bank/mirror_status.json`

동기화 명령:

```text
python -X utf8 scripts/sync_narrative_reference_bank.py
```
