Date: 2026-04-01
Status: parked memo
Confidence: 96%
Scope: `Stage2/3/4` 장기 구조 단순화 메모
Baseline Commit: `fd1707372bd7eb8ad23a5d4506ef556e3f72cc51`
Queue Impact: none

# Stage2/3/4 구조 단순화 장기 메모

## 요지

- 현재 파이프라인은 `5천 자 원고` 대비 구조가 과복잡한 편이다.
- 특히 `Stage3`가 `Stage2 authority`를 다시 번역하고 약화시키는 중간층으로 작동하는 구간이 있다.
- 장기 목표는 `Stage 숫자 축소` 자체보다 `authority handoff 축소`다.

## 현재 판단

- `Stage2`: 스켈레톤 / 전술 권위 원천
- `Stage3`: 장면 구체화라는 명목은 타당하지만, 현재 구현은 재해석/재번역 비용이 큼
- `Stage4`: 최종 원고화 + gate

즉 장기적으로는 아래 둘 중 하나를 목표 상태로 본다.

1. `Stage2 -> Stage4`
2. `Stage2 -> (internal Stage3 compiler/substep) -> Stage4`

핵심은 `Stage3를 독립 창작 단계로 유지할지`, 아니면 `compiler/substep`으로 낮출지 재판정하는 것이다.

## 왜 이 메모를 남기나

- 현재 구조부채의 큰 축 중 하나가 `Stage3`의 중간 번역층 성격이기 때문이다.
- 같은 truth가 `Stage2/3/4`에서 다른 이름과 다른 강도로 반복 전달된다.
- 이 문제는 기능 버그가 아니라 운영비, 디버깅비, 확장비를 키우는 장기 비용이다.

## 당장 하지 않을 것

- 지금 바로 `Stage3 삭제`
- 지금 바로 `Stage2/4` 전면 리라이트
- 지금 바로 전역 rename

## 선행 조건

- 현재 `0_0` parent lane canary / runtime 판정 먼저 확인
- 이후 `common vocabulary / contract normalization`을 bounded wave로 수행
- 그 다음 `Stage3 고유 책임`만 남기고 나머지 재해석 기능을 감산할지 판단

## 현재 잠정 원칙

- `Stage3`는 장기적으로 가장 먼저 압축 검토할 단계다.
- 하지만 목표는 `단계 삭제`가 아니라 `중복 번역층 제거`다.
- 이후 구조 단순화 wave를 열 때 이 메모를 출발점으로 삼는다.
