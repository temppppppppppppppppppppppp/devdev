# JSON 계약층 로드맵

> purpose: `md 설명 / json 계약` 구조로 넘어가기 위한 JSON 파일 세트와 도입 순서 고정

## 0. 목표

이 로드맵은 "무슨 JSON을 언제 만들 것인가"를 잠그는 문서다.

목표는 전처리 SSOT와 blockguide의 운영 계약을 prose 추론이 아니라
구조화된 상태와 규칙으로 읽게 만드는 것이다.

## 1. 1차 JSON 계약 세트

### 1.1 상위 계약층

향후 canonical target path:

```text
전처리_ssot/contracts/
├── stage_machine.json
├── artifact_contracts.json
├── quality_gates.json
├── profile_catalog.json
├── handoff_rules.json
├── sequential_run_status.schema.json
└── audit_status.schema.json
```

역할:

- `stage_machine.json`
  - Stage 0 / Planning / Production / BI / Audit 판정
- `artifact_contracts.json`
  - 단계별 필수 파일, 필수 슬롯, canonical path
- `quality_gates.json`
  - stop/go 조건, hard fail, soft warning
- `profile_catalog.json`
  - 현대판타지 all-genre 프로파일 정의와 해석축
- `handoff_rules.json`
  - 단계 전환 전 확인할 상태, 금지 조건
- `sequential_run_status.schema.json`
  - 작품별 순차 진행 상태 JSON의 표준 스키마
- `audit_status.schema.json`
  - 작품별 최신 감리 상태 JSON의 표준 스키마

### 1.2 작품별 상태층

작품별 canonical target path:

```text
treatments/preprocess/{work_id}/
├── source_manifest.json
├── profile_lock.json
├── material_bundle_summary.json
├── phase0_ready_snapshot.json
├── sequential_run_status.json
└── audit_status.json
```

역할:

- 기존 4개 Stage 0 계약 파일은 유지
- `sequential_run_status.json` 추가
- `audit_status.json` 추가

### 1.3 상태 JSON 표준은 먼저 잠근다

실제 작품 인스턴스를 강제하기 전에,
상위 계약층에서 먼저 아래 두 파일의 표준 스키마를 잠근다.

- `전처리_ssot/contracts/sequential_run_status.schema.json`
- `전처리_ssot/contracts/audit_status.schema.json`

## 2. 단계별 도입 순서

### Phase A. 문서 기준 잠금

이번 단계다.

- migration charter 작성
- contract inventory 작성
- roadmap 작성
- schema package plan 작성
- 95% confidence audit 통과

### Phase B. 상위 계약 JSON 도입

선행 조건:

- Phase A complete
- 경로와 ownership 충돌 없음

도입:

- `stage_machine.json`
- `artifact_contracts.json`
- `quality_gates.json`
- `profile_catalog.json`
- `handoff_rules.json`

### Phase C. 작품별 상태 JSON 인스턴스 도입

선행 조건:

- 상위 계약 JSON이 blockguide / preprocess SSOT에서 참조 가능

도입:

- `treatments/preprocess/{work_id}/sequential_run_status.json`
- `treatments/preprocess/{work_id}/audit_status.json`

이 단계에서는 MD 상태 파일을 즉시 지우지 않는다.
JSON과 병행 운영 후 의미가 안정되면 정리한다.

### Phase D. harness 참조 전환

선행 조건:

- JSON 계약 파일이 실제로 존재
- 1개 이상 pilot `work_id`에서 검증

도입:

- SSOT와 harness 문구에서 prose 설명 아래에 canonical JSON 참조 추가
- stage detection과 handoff를 prose 추론이 아니라 JSON 기준으로 읽게 전환

## 3. 왜 이 순서여야 하는가

이 순서가 아닌 경우의 문제:

- JSON 파일부터 만들면 ownership 충돌이 남는다
- 작품별 상태 파일부터 만들면 상위 오더가 그 파일을 읽지 못한다
- harness를 먼저 바꾸면 아직 존재하지 않는 JSON을 참조하게 된다

따라서:

1. 기준 문서
2. 상위 계약
3. 작품별 상태
4. harness 참조 전환

이 순서로 가야 한다.

## 4. pilot 검증 순서

첫 pilot은 아래 순서를 권장한다.

1. `chaebol_allowance_zero`
2. `us_ai_exile_monopoly`
3. `chaebol_ent_empire`

이유:

- 기업 성장형, AI/테크형, 엔터형으로 프로파일이 나뉜다
- 기존 자료와 비교 자산이 많다
- 전처리 SSOT 허브에 이미 일부 정리본이 있다

## 5. 완료 기준

아래면 JSON 계약층 1차 준비 완료다.

- 상위 계약 JSON 5종의 역할과 target path가 잠겼다
- 상태 JSON 표준 스키마 2종과 실제 target instance path가 잠겼다
- 기존 4개 Stage 0 계약 파일과 충돌이 없다
- README / SSOT / migration docs가 같은 용어를 쓴다
- 95% confidence audit가 PASS다
