# migration_notes

`migration_notes/`는 전처리 SSOT를 갈아엎기 전에 기준을 잠그는 문서 묶음이다.

핵심 원칙:

- 인간 설명은 `md`
- 실행 계약과 상태는 `json`
- 아직 구현 전이라도 먼저 문서로 cutover 기준을 잠근다
- 95% 확신도 전에는 실제 계약층 전환에 들어가지 않는다

읽기 순서:

1. `md_json_migration_charter.md`
2. `md_json_contract_inventory.md`
3. `json_contracts_roadmap.md`
4. `json_schema_package_plan.md`
5. `md_json_migration_95_confidence_audit.md`
6. `json_contracts_seed_3pass_audit.md`

이 폴더의 역할:

- 왜 `md + json` 이원화로 가는지 설명
- 무엇을 `md`에 남기고 무엇을 `json`으로 내릴지 결정
- 향후 JSON 계약층의 파일 세트와 경로를 고정
- 문서 패키지가 실제 cutover를 버틸 만큼 단단한지 3-pass로 재감리
- 실제 생성된 JSON 계약 시드가 문서와 맞는지 다시 3-pass로 재감리

금지:

- 이 문서만 보고 바로 스크립트나 기존 정본 경로를 바꾸지 않는다
- `md`를 전부 `json`으로 바꾸려 하지 않는다
- 95% confidence audit 없이 계약층 구현을 시작하지 않는다
