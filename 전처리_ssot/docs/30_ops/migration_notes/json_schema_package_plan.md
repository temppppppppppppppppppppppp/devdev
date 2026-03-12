# JSON 스키마 패키지 계획

> purpose: 실제 JSON 계약층을 만들 때 어떤 패키지 구조와 버전 정책으로 갈지 미리 고정

## 0. 왜 스키마 패키지 계획이 필요한가

JSON 파일 이름만 정해 놓으면 곧바로 두 문제가 생긴다.

- 어떤 키가 필수인지 파일마다 흔들린다
- versioning 없이 수정하다가 harness와 상태 파일이 엇갈린다

그래서 구현 전이라도 패키지 구조와 버전 정책을 먼저 정해야 한다.

## 1. target package structure

```text
전처리_ssot/contracts/
├── schema_version.json
├── stage_machine.json
├── artifact_contracts.json
├── quality_gates.json
├── profile_catalog.json
├── handoff_rules.json
├── sequential_run_status.schema.json
└── audit_status.schema.json
```

`schema_version.json` 최소 슬롯:

```json
{
  "package_name": "preprocess_contracts",
  "version": "1.0.0-draft",
  "status": "design_locked",
  "updated_at": "2026-03-12",
  "compatibility": {
    "blockguide_md": "required",
    "work_status_json": "planned"
  }
}
```

## 2. work-level status package

작품별 상태 파일 인스턴스는 아래처럼 본다.

```text
treatments/preprocess/{work_id}/
├── source_manifest.json
├── profile_lock.json
├── material_bundle_summary.json
├── phase0_ready_snapshot.json
├── sequential_run_status.json
└── audit_status.json
```

원칙:

- Stage 0 계약 파일 4종은 `v1 carry-forward`
- 새 JSON 상태 파일은 `v1 introduce`
- 상태 파일은 상위 계약 JSON을 참조해야 한다

상위 표준 스키마:

- `전처리_ssot/contracts/sequential_run_status.schema.json`
- `전처리_ssot/contracts/audit_status.schema.json`

## 3. versioning 규칙

- major
  - 키 의미가 바뀌거나 필수 슬롯이 깨질 때만 증가
- minor
  - 새 선택 슬롯 추가, 새 warning 규칙 추가
- patch
  - 오탈자, 설명 보완, 값 목록 보정

금지:

- 문서만 바꾸고 schema version을 안 올리는 것
- 파일마다 버전 체계를 다르게 쓰는 것

## 4. slot design 원칙

모든 JSON 계약 파일은 아래 원칙을 따른다.

- 필수 슬롯과 선택 슬롯을 분리
- enum 값은 prose가 아니라 값 목록으로 고정
- boolean 게이트는 이름만 봐도 뜻이 드러나게 작성
- free text는 최소화하고, 필요한 경우 이유/메모용으로만 사용
- `hard_fail`과 `soft_warning`를 분리

## 5. audit friendliness 원칙

이 JSON 패키지는 사람이 쓰기보다 감리와 재개를 돕기 위한 것이다.

그래서:

- diff가 작아야 한다
- order가 안정적이어야 한다
- 키가 길어도 의미가 명확해야 한다
- 같은 정보를 다른 이름으로 두 번 담지 않는다

## 6. implementation 보류 조건

아래가 해결되기 전에는 실제 JSON 스키마 파일 생성 보류:

- stage detection prose와 target JSON 키 mapping이 명확하지 않다
- `sequential_run_status.md`와 새 JSON 상태 파일의 공존 규칙이 없다
- README가 여전히 prose만으로 실행 계약을 설명한다

즉, 이 문서는 "바로 파일 만들자"가 아니라
"어떤 패키지 구조로 만들지 미리 잠그자"가 목적이다.
