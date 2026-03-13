# 시점 설계 의도 재정리 — 타자 시점 기반 주인공 고평가 관점 2PASS 감리

작성일: 2026-03-13  
판정: `clarification-ready`  
최종 확신도: `95%`

## 목적
- 본 문서는 기존 `혼합 시점` 조사 문서를 사용자 의도 기준으로 다시 해석하기 위한 보정 메모다.
- 사용자 의도는 `아무 데서나 POV를 섞고 싶다`가 아니라, `타자의 시점에서 주인공을 고평가하는 연출을 넣고 싶다`는 쪽으로 이해한다.
- 따라서 질문은 `혼합 시점 지원 여부`보다 `단일 주시점 + 제한적 타자 시점 삽입`을 시스템이 어떻게 다루는가로 재정렬된다.

## 관련 문서
- 기존 전수조사: [viewpoint-mixed-pov-full-survey-3pass-final-audit.md](/C:/Users/User/Desktop/글도비/docs/2026-03-13/viewpoint-mixed-pov-full-survey-3pass-final-audit.md)
- 기존 수정 오더: [viewpoint-mixed-pov-remediation-execution-ssot.md](/C:/Users/User/Desktop/글도비/docs/2026-03-13/viewpoint-mixed-pov-remediation-execution-ssot.md)

## Pass 1 — 컨텍스트 재수집

### 1. 시스템은 이미 `타자 시점 삽입`을 연출 장치로 전제한다
- `modules/domain/agents/blueprint_ensemble.py`의 scene preset은 아래를 명시적으로 가진다.
  - `side_glimpse`: 조연 시점 전환, 주인공 부재 장면, “저 사람 대단해” 반응
  - `villain_scheme`: 악역 시점 전환, 음모 노출
  - `omniscient_hint`: 전지적 시점 복선 암시
- 즉 시스템은 본래부터 `외부 시점으로 주인공의 위상/위협/반응을 보여주는 장치`를 planning 단계에 포함한다.

### 2. prompt asset도 이 장치를 적극 장려한다
- `config/prompts/ensemble.yaml`은 시점 전환 프리셋을 “적극 활용” 대상으로 둔다.
- 같은 파일은 `side_glimpse`를 `조연 시점에서 주인공에 대한 반응`으로 설명한다.
- `config/prompts/writer_rules.json`도 `시점 전환(POV Switching)` 보정 지침을 따로 둔다.
- 따라서 현재 시스템의 사고방식은 `주인공 1인칭 고정`보다 `필요 시 타자 시점 절편을 써도 된다` 쪽에 더 가깝다.

### 3. 하지만 이 장치와 `프로젝트 전체 혼합 시점`은 같은 개념이 아니다
- `Stage 0 POV = 혼합`은 작품 전체가 scene-level switching을 기본 계약으로 삼는다는 뜻에 가깝다.
- 반면 사용자가 말한 의도는 `주 시점은 유지하되, 필요할 때 타자 반응샷으로 주인공을 고평가`하는 것이다.
- 이 둘은 구분해야 한다.

### 4. 현재 구조는 이 둘을 명확히 구분하지 않는다
- `혼합`은 Stage 0 POV 옵션으로 존재한다.
- `side_glimpse / villain_scheme / omniscient_hint`도 별도 planning preset으로 존재한다.
- 그러나 `이 작품은 단일 주시점인데, 타자 반응샷만 제한적으로 허용한다`는 독립 축은 현재 보이지 않는다.
- 즉 시스템은 아래 세 가지를 별도로 모델링하지 않는다.
  1. 작품의 기본 POV
  2. 타자 시점 삽입 허용 여부
  3. 삽입 허용 범위와 빈도

## Pass 2 — 해석 보정 감리

## 핵심 판단

### A. 사용자 의도 기준으로는 `혼합 시점`이 과한 선택일 수 있다
- 주인공 고평가용 외부 시점이 필요하다는 이유만으로 작품 전체 POV를 `혼합`으로 두는 것은 과하다.
- 그 목적만 놓고 보면 더 자연스러운 개념은:
  - `기본 POV = 1인칭` 또는 `3인칭`
  - `타자 시점 절편 = 제한적 허용`
  이다.

### B. 현재 시스템은 이미 그 연출 장치를 일부 갖고 있다
- `side_glimpse`가 바로 그 장치다.
- 즉 “타자의 시점에서 주인공을 높여 보이기” 자체는 새 발명이 아니라 기존 프리셋의 intended use에 가깝다.

### C. 진짜 정리 포인트는 `혼합 POV 지원`이 아니라 `POV taxonomy`다
- 현 구조의 문제는 `타자 시점 반응샷`과 `프로젝트 전체 혼합 시점`이 같은 바구니에 들어가 있다는 점이다.
- 따라서 기존 조사에서 남긴 `planning/validation/SSOT drift` finding은 유지하되, 해석은 아래처럼 보정하는 것이 맞다.
  - 잘못된 해석: `혼합 POV 작품을 더 잘 지원해야 한다`
  - 더 정확한 해석: `기본 POV와 외부 시점 삽입 정책을 분리해서 정의해야 한다`

## 기존 Findings에 대한 보정

### 기존 P1: Stage 0 artifact POV drift
- 유지한다.
- 이 문제는 여전히 실문제다.
- 다만 이 finding이 곧 `혼합 POV를 기본으로 더 밀어야 한다`는 뜻은 아니다.

### 기존 P2: 혼합 POV planning contract 미정리
- 유지하되 표현을 보정한다.
- 실질적 요구는 `혼합 POV 일반화`보다 `타자 시점 절편의 목적·빈도·제약 명시화`에 더 가깝다.

### 기존 P2: mixed POV 위반 advisory-only
- 유지한다.
- 다만 향후 hardening은 `진짜 혼합 작품`과 `단일 POV + 반응샷 삽입 작품`을 분리해 다뤄야 한다.

## 설계 방향 제안
- 앞으로는 POV를 최소 2축으로 나누는 것이 가장 자연스럽다.
  - `primary_pov`: 1인칭 / 3인칭 / 전지적 / 혼합
  - `external_pov_insert_policy`: 금지 / 제한적 허용 / 적극 허용
- 글도비 투자물 같은 경우, 기본 운영값으로 더 그럴듯한 것은 아래다.
  - `primary_pov = 1인칭 또는 3인칭`
  - `external_pov_insert_policy = 제한적 허용`
  - 허용 목적: `주인공 위상 확인`, `타자 경악`, `적대자의 위협 체감`, `정보 격차 강조`

## 최종 결론
- 사용자 의도는 현재 시스템의 `side_glimpse`류 장치와 잘 맞는다.
- 다만 지금 구조는 이 의도를 `프로젝트 전체 혼합 시점`과 분리해 표현하지 못한다.
- 따라서 앞으로 정리해야 할 핵심은 `혼합 시점 강화` 자체보다, `기본 POV`와 `타자 시점 삽입 정책`의 분리다.

## Confidence Ledger
- `75` 코드/프롬프트/기존 조사 문서 재정렬 완료
- `+10` preset/prompt 근거와 사용자 의도 일치 확인
- `+10` 기존 findings 재해석 후 모순 제거
- `= 95`

남은 5%:
- 실제로 이 개념 분리를 코드/메뉴/로그에 반영한 상태는 아직 아니다.
- 따라서 이번 문서는 설계 의도 보정 문서이며, 구현 검증 문서는 아니다.
