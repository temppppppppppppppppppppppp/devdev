# MD + JSON 마이그레이션 헌장

> status: draft-fixed
> owner: preprocess SSOT
> target confidence: 95%+

## 0. 목적

이 헌장은 전처리 SSOT와 blockguide 운영 규칙을
`인간 설명은 md`, `실행 계약은 json` 구조로 재편하기 위한 상위 결정 문서다.

이번 문서의 목적은 구현이 아니라 아래 4가지를 먼저 잠그는 것이다.

1. 왜 갈아엎는지
2. 무엇을 바꾸고 무엇을 유지하는지
3. cutover 전에 어떤 준비 문서가 필요한지
4. 어느 시점에 실제 JSON 계약층 구현으로 넘어갈 수 있는지

## 1. 왜 이렇게 가야 하는가

현 상태 문제는 "문서가 적다"가 아니라
"운영 계약, 단계 판정, 재개 포인터, 감리 게이트가 prose 안에 섞여 있다"는 점이다.

이 상태의 문제:

- 컨텍스트가 컴팩트되면 규칙이 요약되며 해석이 흔들린다.
- `seed baseline`과 `sequential production`처럼 중요한 상태 구분이 문장 속에 묻힌다.
- stop/go 게이트를 기계적으로 검증하기 어렵다.
- 낮은 성능 모델이 설명은 읽어도 어떤 파일을 기준으로 멈춰야 하는지 놓치기 쉽다.

따라서:

- 사람이 이해해야 하는 철학, 예시, anti-pattern, why는 `md`
- 기계가 읽고 판정해야 하는 상태, 계약, 게이트, 프로파일, handoff는 `json`

이 분리를 먼저 선언해야 이후 구현과 감리가 흔들리지 않는다.

## 2. 이번 개편의 범위

포함:

- 전처리 SSOT와 blockguide의 실행 계약층을 `json`으로 분리할 준비
- 어떤 규칙을 `md`에 남기고 어떤 규칙을 `json`으로 내릴지 고정
- 향후 계약 파일 세트, 경로, cutover 순서를 문서화
- 95% confidence audit 기준 문서화

제외:

- 기존 정본 경로 `treatments/`, `bible/`의 즉시 변경
- 기존 루트 `docs/`의 즉시 삭제 또는 강제 이관
- 레거시 스크립트의 즉시 삭제
- 이 문서 패키지 단계에서 실제 JSON 계약 파일 전면 생성

## 3. 유지할 것

- 사용자용 진입점은 계속 `README.md`
- 상위 오더와 harness는 계속 `md`
- 작품별 Stage 0 계약 파일 4종은 계속 `json`
  - `source_manifest.json`
  - `profile_lock.json`
  - `material_bundle_summary.json`
  - `phase0_ready_snapshot.json`
- 최종 정본 경로는 계속 아래를 유지
  - `treatments/{work_id}_phase0_design.json`
  - `treatments/{work_id}_tr_block_070_draft.json`
  - `bible/0_bi_{work_id}.json`

## 4. 새로 도입할 것

향후 JSON 계약층의 최소 구성은 아래다.

- `stage_machine.json`
- `artifact_contracts.json`
- `quality_gates.json`
- `profile_catalog.json`
- `handoff_rules.json`
- `sequential_run_status.json`
- `audit_status.json`

도입 원칙:

- 설명 없는 JSON 금지
- JSON 없는 prose 계약 금지
- 같은 규칙을 `md`와 `json`에 다르게 적는 이중 진실 금지

## 5. cutover 기준

아래가 모두 만족돼야 구현 단계로 넘어간다.

1. 이 `migration_notes` 문서 세트가 95% confidence audit 통과
2. `md`와 `json` 소관 구분이 표로 잠김
3. JSON 계약 파일 세트와 target path가 결정됨
4. 기존 전처리 SSOT와 blockguide가 어떤 JSON을 읽어야 하는지 연결 관계가 정리됨
5. rollback 기준이 정의됨

## 6. rollback 기준

아래면 cutover를 보류하거나 되돌린다.

- JSON 계약 파일과 MD 설명이 충돌
- 낮은 성능 모델이 JSON 파일 이름과 역할을 구분하지 못함
- 기존 Stage 0 산출물 4종과 새 계약층이 이중 진실 상태가 됨
- `sequential_run_status`처럼 진행률 핵심 파일의 의미가 흔들림
- blockguide 상위 오더가 새 계약층을 읽지 못함

## 7. low-context / low-intelligence safe 원칙

이 전환은 똑똑한 에이전트만을 위한 설계가 아니다.

반드시 만족해야 하는 조건:

- 파일명이 역할을 바로 드러낸다.
- README 하나만 봐도 다음에 무엇을 읽을지 안다.
- JSON마다 상위 MD 설명 문서가 있다.
- 하나의 규칙에는 하나의 canonical location만 있다.
- 진행률과 handoff는 prose 추론이 아니라 상태 파일로 읽는다.

## 8. 최종 선언

이 문서의 결론은 단순하다.

- `md`는 사람과 에이전트의 설명층
- `json`은 실행 계약층
- 지금은 구현보다 기준을 잠그는 단계
- 95% confidence audit 전에는 실제 cutover 금지
