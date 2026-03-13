# 기본 POV + 타자 시점 삽입 정책 보강 오더 — 2PASS 감리

작성일: 2026-03-13  
대상 SSOT: `viewpoint-primary-pov-external-insert-remediation-execution-ssot.md`  
최종 판정: `execution-ready`  
최종 확신도: `95%`

## Pass 1 — 문제-수정 축 정렬
- 이 오더는 기존 `혼합 POV` 조사 결과를 사용자 의도에 맞게 재분류한다.
- 가장 중요한 보정은 아래다.
  - `혼합 POV 일반화`를 목표로 하지 않음
  - `기본 POV`와 `타자 시점 삽입 정책`을 분리함
- 따라서 retained finding과 수정 축의 정렬은 다음처럼 읽는 것이 맞다.
  - Stage 0 artifact drift -> `R-2`
  - planning gap -> `R-3`
  - advisory-only validation -> `R-4`
  - 복원성 부족 -> `R-5`

## Pass 2 — 실행 가능성과 과잉 범위 검증
- `R-1`과 `R-2`는 Stage 0 설정/산출물 계층만 손보면 된다.
- `R-3`과 `R-4`는 blueprint planning, validator, director advisory 계층의 계약 정리로 충분하다.
- `R-5`는 기존 logging hardening 패턴을 재사용할 수 있다.
- 과잉 범위로 보이는 항목은 제외돼 있다.
  - prompt 철학 전면 개편
  - 작품 톤 재조정
  - UI 리디자인
- false positive 방지 측면에서도 더 낫다.
  - `혼합 작품`과 `단일 시점 + 반응샷 허용 작품`을 구분할 수 있기 때문이다.

## 최종 판단
- 이 오더가 기존 mixed-POV 오더보다 사용자 의도와 더 정확히 맞는다.
- 구현 난이도는 중간이지만, 설계 명확성은 더 높다.
- 따라서 앞으로 POV 관련 수정이 필요하면 우선 기준 문서는 이 새 SSOT로 보는 것이 맞다.

## Confidence Ledger
- `75` 기존 조사/의도 보정 문서와의 정렬 완료
- `+10` 수정 범위가 retained finding에 직접 대응함
- `+10` false positive/과잉 범위 감소 효과 확인
- `= 95`

남은 5%:
- 실제 구현 후에는 `혼합 작품`, `단일 POV + 제한적 타자 삽입 작품`, `금지 작품` 3케이스를 runtime으로 다시 봐야 한다.
