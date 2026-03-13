# One-Stop Frontier Lag 실행 SSOT 3Pass 감리

작성일: 2026-03-13  
대상 SSOT: `docs/2026-03-13/one-stop-frontier-lag-execution-ssot.md`

## Executive Summary

- 감리 결과: `execution-ready`
- 사용자가 제안한 `Stage 3 = frontier-1 / Stage 4 = frontier-2` 규칙은 코드 현실과 맞는다.
- 기존 `tail holdback` 초안보다 상태 전이가 더 단순하고 resume 친화적이다.
- 최종 확신도는 `95%`다.

## Pass 1: 문제 정의 재확인

- 기존 `6번`은 설계 frontier를 Stage 3/4가 그대로 따라간다.
  - `main_a.py:3598`
  - `main_a.py:3636`
- 따라서 현재 구조는 Arc 경계의 미래 정보를 마지막 blueprint/manuscript에 반영하지 못한다.
- 사용자가 제시한 예:
  - 13 → `Stage 3 12`, `Stage 4 11`
  - 16 → `Stage 3 15`, `Stage 4 14`
  는 `미래 arc 정보 부족` 문제를 완화하는 일관된 규칙으로 해석된다.

## Pass 2: 설계 적합성 검증

### 1. True final arc 정의

- 올바르다.
- `진짜 마지막 아크`는 `현재 마지막으로 설계된 arc`가 아니라 `plot_roadmap 마지막 block`이어야 한다.
- 이 정의가 없으면 non-final frontier도 잘못 full close될 수 있다.

### 2. Frontier lag 규칙

- 적절하다.
- non-final frontier에서는:
  - 설계는 미래 1화 더 앞서 있고
  - blueprint는 manuscript보다 1화 더 앞서 있다
- 이 구조는 Stage 4에 항상 “다음 blueprint 한 장”을 남기므로 continuity/hook 품질에 이점이 있다.

### 3. Wrapper 중심 구현

- 적절하다.
- Stage 3/4는 이미 `target_ep` 기반으로 잘 동작한다.
- 따라서 이번 기능은 engine 내부보다 wrapper에서 frontier 계산을 추가하는 게 맞다.

## Pass 3: 오탐 및 과잉 범위 제거

- 아래는 이번 구현 범위에서 제외하는 것이 맞다.
  - Stage 3/4 prompt 강화
  - Stage 2 pacing heuristic 수정
  - 새 DB schema
  - 6번 의미 변경
  - 2episode 초과 lag
- 이유:
  - 모두 현재 목표보다 크다.
  - 지금 포함하면 “frontier lag 실행 모드”라는 핵심이 흐려진다.

## Retained Design Decisions

### D-1. 기존 tail-holdback 초안보다 frontier-lag가 우선

- 이유:
  - 실행 규칙이 더 단순하다.
  - rerun 시 backlog가 자동으로 풀린다.
  - 별도 `tail close` phase가 필요 없다.

### D-2. Final frontier full-close 유지

- 이유:
  - true final arc는 더 이상 미래 block이 없으므로 lag 이득이 사라진다.
  - final close 예외를 두지 않으면 ending이 영원히 유예될 위험이 있다.

### D-3. 13→12/11, 16→15/14 예시는 유효한 acceptance example

- 이유:
  - Stage 2 가변 페이싱과 충돌하지 않는다.
  - ep_count 최소 3 조건 때문에 non-final frontier에서도 계산이 성립한다.

## Open Questions

- 없음

현재 기준으로 blocker가 되는 미해결 질문은 없다.

## Final Judgment

- SSOT는 prior draft보다 개선됐다.
- true final arc 정의가 명확해졌고, frontier lag 수식도 일관적이다.
- 구현 범위는 여전히 wrapper 중심의 소규모다.
- 따라서 본 문서는 `execution-ready`로 확정한다.

## Confidence Ledger

- `70`: One-Stop / Stage 2 / Stage 3 / Stage 4 baseline 재확인
- `+10`: true final arc 정의를 plot_roadmap 기준으로 잠금
- `+10`: frontier lag 규칙이 resume semantics와 충돌하지 않음을 확인
- `+5`: prior tail-holdback draft 대비 단순화 및 과잉 범위 제거
- 최종: `95`

## Notes

- 이번 턴은 문서화와 3-pass 감리만 수행했다.
- 코드 수정, 테스트 실행, rerun은 아직 하지 않았다.
