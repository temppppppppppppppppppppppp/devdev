# narrative_ssot

Status: scaffold draft
Date: 2026-03-31

이 폴더는 서사 생산 체계를 한 폴더 안의 수직 계층으로 재정렬하기 위한 `v0.1` scaffold다.

현재 원칙:

- 기존 `treatments/`, `bible/`, `전처리_ssot/`, `docs/실물기반 사각지대 테스트/`는 유지한다.
- 이 폴더는 신규 canonical 후보 경로를 실험하는 안전한 병행 레이어다.
- `move`보다 `scaffold + contract pin + pilot`를 우선한다.
- 신규 작품 1개에만 pilot 적용하는 것을 기본값으로 둔다.

읽기 순서:

1. `00_governance/SSOT_narrative_factory_entry.md`
2. `30_harness/00_entry_router.md`
3. stage별 하네스 1개
4. 해당 schema
5. `40_contracts/quality_gates.json`

상위 폴더 역할:

- `00_governance/`: 권위, 경로, read order
- `10_reference_bank/`: few-shot / reference 연결층
- `30_harness/`: 사람용 실행 하네스
- `40_contracts/`: JSON 계약과 gate
- `50_projects/`: 작품별 수직 생산기지
- `90_migration/`: legacy 공존 규칙과 cutover 초안

빠른 시작:

```text
python -X utf8 scripts/create_narrative_project_scaffold.py --work-id <new_work_id>
python -X utf8 scripts/build_stage0_from_reference_selection.py --work-id <new_work_id>
python -X utf8 scripts/build_phase0_seed_from_stage0.py --work-id <new_work_id>
```

이 명령은 `_template`를 복제해 `50_projects/<new_work_id>/`를 만들고,
기본 placeholder를 해당 `work_id` 기준으로 다시 쓴다.
두 번째 명령은 `reference_selection.json`을 읽어 `source_manifest / profile_lock / material_bundle_summary / phase0_ready_snapshot`
초안을 실제 selected card 신호로 채우고, 필요하면 `work_identity_override / profile_override / opening_bundle_contract_override`
authority를 함께 잠근다.
세 번째 명령은 Stage0 authority를 바탕으로 `30_planning/phase0_design.json`의 planning seed를 채우고,
`work_identity_surface`까지 미러링해 naming drift를 줄인다.
