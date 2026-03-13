# 기본 POV + 타자 시점 삽입 정책 보강 실행 SSOT

작성일: 2026-03-13  
기준 문서:
- `viewpoint-mixed-pov-full-survey-3pass-final-audit.md`
- `viewpoint-external-pov-design-intent-2pass-audit.md`

상태: `execution-ready`

## Summary
- 이번 SSOT는 `혼합 POV 작품을 더 잘 지원하자`가 아니라, `기본 POV`와 `타자 시점 삽입 정책`을 분리해서 다루는 데 목적이 있다.
- 기본 전제는 다음과 같다.
  - 작품 전체의 주시점은 별도로 존재한다.
  - 타자 시점은 주인공 고평가, 외부 반응, 적대 시야, 정보 격차 연출을 위해 제한적으로 삽입될 수 있다.
- 따라서 해결 대상은 `혼합 시점 일반화`가 아니라 `POV taxonomy 정리`, `artifact/drift 해소`, `planning/validation 규칙 분리`다.

## Core Model

### 1. primary_pov
- 값: `1인칭 / 3인칭 / 전지적 / 혼합`
- 의미: 작품 전체를 지배하는 기본 시점 계약

### 2. external_pov_insert_policy
- 값: `금지 / 제한적 허용 / 적극 허용`
- 의미: 타자 시점 절편을 어느 정도 허용할지 정하는 별도 정책

### 3. intended use
- `side_glimpse`: 타자 반응샷, 주인공 위상/경악/평판 강화
- `villain_scheme`: 적대자 시야, 위협감/역정보/불안 조성
- `omniscient_hint`: 제한적 정보 격차 연출

## Remediation Scope

### R-1. Stage 0 POV taxonomy 분리
- 목표:
  - 프로젝트 설정에서 `primary_pov`와 `external_pov_insert_policy`를 별도 입력/저장한다.
- 구현 방향:
  - 기존 POV 선택은 `primary_pov`로 유지
  - 별도 선택 항목 추가
    - `외부 시점 삽입: 금지 / 제한적 허용 / 적극 허용`
  - default는 장르별로 결정하되, 투자물 계열은 우선 `제한적 허용`을 후보 기본값으로 검토
- 수용 기준:
  - `혼합`을 고르지 않아도 `타자 시점 반응샷` 허용 정책을 표현할 수 있다.

### R-2. Stage 0 artifact POV provenance 정리
- 목표:
  - style guide가 reference-derived POV와 project-selected POV를 혼동하지 않게 한다.
- 구현 방향:
  - `style_guide.json`에 아래 필드 분리
    - `extracted_pov`
    - `selected_primary_pov`
    - `effective_primary_pov`
    - `external_pov_insert_policy`
  - Stage 4는 raw `pov` 한 줄이 아니라 위 provenance를 읽어 적용한다.
- 수용 기준:
  - `전지적/3인칭/1인칭` 프로젝트가 전부 Stage 0 결과물에서 `1인칭`으로만 보이지 않는다.

### R-3. Planning 계층에 외부 시점 정책 반영
- 목표:
  - `side_glimpse / villain_scheme / omniscient_hint` 사용 조건을 `primary_pov`와 `external_pov_insert_policy`로 제어한다.
- 구현 방향:
  - `blueprint_ensemble.py`에서
    - `금지`: 타자 시점 프리셋 차단
    - `제한적 허용`: 반응샷/짧은 절편만 허용
    - `적극 허용`: scene-level 전략 허용
  - `혼합`은 여전히 별도 primary_pov로 유지하되, 그것과 외부 시점 정책을 같은 개념으로 취급하지 않는다.
- 수용 기준:
  - `1인칭 + 제한적 허용` 작품은 주시점은 유지하면서 필요한 타자 반응샷만 허용한다.
  - `혼합`은 여전히 더 넓은 switching 권한으로 유지된다.

### R-4. Validation 계층 분리
- 목표:
  - `진짜 혼합 POV 위반`과 `단일 POV 작품에서의 과도한 타자 시점 남용`을 구분해 다룬다.
- 구현 방향:
  - validator에 두 계층 추가
    - `primary_pov_consistency`
    - `external_pov_insert_policy_violation`
  - 예:
    - `1인칭 + 제한적 허용`인데 side_glimpse가 과다하면 경고/수정
    - `혼합`인데 same-scene mixed POV면 강한 위반
- 수용 기준:
  - 단일 POV 작품과 혼합 작품이 같은 규칙으로 뭉뚱그려지지 않는다.

### R-5. Observability 정리
- 목표:
  - Stage 3/4 로그와 summary에서 POV 의도와 실제 적용을 복원 가능하게 한다.
- 구현 방향:
  - 로그/summary에 아래를 남긴다.
    - `primary_pov`
    - `external_pov_insert_policy`
    - `style_guide_extracted_pov`
    - `effective_pov`
    - `external_pov_segments_count`
- 수용 기준:
  - 나중에 “왜 타자 시점이 들어갔는가”를 로그로 설명할 수 있다.

## Exclusions
- 문체/톤 전면 개편
- 모든 장르의 POV 철학 재정의
- UI/UX 디자인 작업  
  단, Stage 0 입력 surface는 후속 UI 연결 tranche에서 별도 반영 가능

## Verification Scenarios
- `primary_pov=1인칭`, `external_pov_insert_policy=제한적 허용`
  - side_glimpse 짧은 삽입 허용
  - 작품 전체가 혼합 POV로 오염되지 않음
- `primary_pov=1인칭`, `external_pov_insert_policy=금지`
  - 타자 시점 preset이 planning에서 배제됨
- `primary_pov=혼합`
  - 여전히 scene-level switching 규칙을 사용
  - same-scene mixing은 금지
- Stage 0 style guide와 Stage 4 runtime summary가 같은 POV provenance를 공유

## Assumptions
- 사용자 의도상 `혼합`은 계속 필요한 옵션이다.
- 하지만 `타자 시점 삽입`은 `혼합`과 다른 개념으로 다루는 것이 더 정확하다.
- 이번 SSOT는 기존 mixed-POV 오더를 대체한다기보다, 더 상위의 분류 기준으로 우선 적용된다.
