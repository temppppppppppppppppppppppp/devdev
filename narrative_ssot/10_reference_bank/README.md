# Reference Bank

Status: cards mirror plus archive residue shell
Date: 2026-04-05

이 폴더는 few-shot / reference layer 전체 authority가 아니라,
`cards` mirror와 residue pointer를 모아 둔 얇은 shell이다.

현재 live mirror 기능은 아래 항목만 담당한다.

- 현재 authoritative few-shot bank로 가는 mirror 안내
- `reference_card_manifest.json` + `cards/` mirror
- residue/pointer 하위 폴더 상태 라벨링

현재 authoritative 경로:

- `material_ssot/10_research/20_fewshot_bank/`

현재 mirror 경로:

- `narrative_ssot/10_reference_bank/reference_card_manifest.json`
- `narrative_ssot/10_reference_bank/cards/`
- `narrative_ssot/10_reference_bank/mirror_status.json`

현재 live mirror scope:

- `cards/` and `reference_card_manifest.json` only
- other subdirectories under `10_reference_bank` are not synced as an authority surface

현재 transition residue:

- old reference-bank `source_corpora` root
- `source_corpora` subtree는 더 이상 canonical research root가 아니다
- corpus refresh나 재실행은 `material_ssot` canonical lanes에서 수행한다
- 세부 canonical path는 `source_corpora/README.md`와 각 subtree README를 따른다

현재 draft/archive residue:

- `narrative_ssot/10_reference_bank/idea_engine_db/`
- 이 폴더는 modern-business ideation draft bank를 보관하는 archive residue다
- 현재 runtime/harness 소비처는 없고, stage authority로 취급하지 않는다
- 세부 상태와 source pointer는 `idea_engine_db/README.md`를 따른다

현재 pointer-only note:

- `narrative_ssot/10_reference_bank/selection/`
- shared selection sink가 아니라 `reference_selection` 계약 설명용 pointer다
- 실제 작품별 selection artifact는 `narrative_ssot/50_projects/{work_id}/10_reference_selection/`에 저장한다

동기화 명령:

```text
python -X utf8 scripts/sync_narrative_reference_bank.py
```
