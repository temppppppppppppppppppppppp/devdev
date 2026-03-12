# preprocess contracts

이 폴더는 전처리 SSOT의 실행 계약층이다.

원칙:

- 사람 설명은 `md`
- 실행 계약과 상태 규칙은 `json`
- 이 폴더의 JSON은 `README.md`와 `docs/`의 설명 문서를 대체하지 않는다
- 반대로 단계 판정, 필수 파일, stop/go, handoff는 이 폴더의 JSON이 기계 계약이 된다

현재 포함:

- `schema_version.json`
- `stage_machine.json`
- `artifact_contracts.json`
- `quality_gates.json`
- `profile_catalog.json`
- `handoff_rules.json`
- `sequential_run_status.schema.json`
- `audit_status.schema.json`

현재 범위:

- 상위 계약층 + 작품별 상태 JSON 표준 스키마까지 1차 도입
- 실제 작품 인스턴스(`treatments/preprocess/{work_id}/sequential_run_status.json`, `audit_status.json`)는 아직 비강제 단계

읽기 순서:

1. `전처리_ssot/README.md`
2. `전처리_ssot/docs/SSOT_stage0_preprocess_integrated_order.md`
3. `전처리_ssot/docs/30_ops/migration_notes/README.md`
4. 이 폴더의 JSON

작품별 상태 JSON 표준:

- `전처리_ssot/contracts/sequential_run_status.schema.json`
- `전처리_ssot/contracts/audit_status.schema.json`

실제 배치 경로:

- `treatments/preprocess/{work_id}/sequential_run_status.json`
- `treatments/preprocess/{work_id}/audit_status.json`
