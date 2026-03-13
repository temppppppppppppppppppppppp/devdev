# 시점·혼합 시점 보강 오더 — 3PASS 감리

작성일: 2026-03-13  
대상 SSOT: `viewpoint-mixed-pov-remediation-execution-ssot.md`  
최종 판정: `execution-ready`  
최종 확신도: `95%`

## Pass 1 — 오더 범위 검증
- 오더가 retained finding만 치는지 확인했다.
- `R-1`은 Stage 0 artifact POV drift를 직접 겨냥한다.
- `R-2`는 mixed POV planning gap을 직접 겨냥한다.
- `R-3`는 advisory-only 문제를 직접 겨냥한다.
- `R-4`는 post-mortem 복원성 부족을 보강한다.
- prompt 철학 전면 개편, UI 개편, 레퍼런스 corpus 교체는 범위 밖으로 분리돼 있어 과하지 않다.

## Pass 2 — 실행 가능성 검증
- `R-1`은 `stage0/style_extractor.py`와 Stage 0 저장 계층에서 닫을 수 있다.
- `R-2`는 `blueprint_ensemble.py`와 planning prompt layer에서 닫을 수 있다.
- `R-3`는 validator/quality gate/director advisory 계층에서 닫을 수 있다.
- `R-4`는 기존 logging/summary hardening 패턴을 재사용 가능하다.
- 즉 새 대형 스키마 개편 없이도 1차 구현이 가능하다.

## Pass 3 — 오탐 제거 및 수용 기준 보정
- 아래 가설은 오더에서 제외하는 게 맞다고 판단했다.
  - `혼합 시점을 기본 시점으로 승격해야 한다`
  - `Stage 4에서 무조건 scene separator를 강제 삽입해야 한다`
  - `reference corpus를 전부 교체해야만 해결된다`
- 반대로 false positive 방지 기준을 오더에 추가해야 한다고 판단했다.
  - 정상적인 `scene-level mixed POV`는 과잉 차단하면 안 된다
  - non-mixed POV 프로젝트에 불필요한 switching 제약을 과하게 넣으면 안 된다

## 최종 판단
- 문서는 retained finding과 직접 연결된다.
- 수정 범위가 넓지만 과도하지는 않다.
- `혼합 시점 미지원` 같은 과장된 목표가 아니라 `SSOT 정리 + planning/validation hardening`으로 축이 잘 맞춰져 있다.

## Confidence Ledger
- `70` retained finding과 수정 항목의 1:1 매핑 완료
- `+10` 코드 surface 실행 가능성 확인
- `+10` 로그/테스트/산출물과 수용 기준 연동 완료
- `+5` 오탐과 과잉 범위 제거
- `= 95`

95%를 넘기지 않은 이유:
- 실제 mixed POV 원고를 새 hardening 이후 재생성해보는 runtime 검증은 아직 수행 전이다.
- 따라서 본 감리 문서는 `실행 오더로서 95%`이며, 구현 후에는 별도 postfix 감리가 필요하다.
