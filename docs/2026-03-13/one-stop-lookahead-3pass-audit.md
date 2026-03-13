# One-Stop Lookahead 변형 실행 SSOT 3Pass 감리

작성일: 2026-03-13  
대상 SSOT: `docs/2026-03-13/one-stop-lookahead-execution-ssot.md`

## Executive Summary

- 감리 결과: `execution-ready`
- 문서는 기존 `6번`의 구조적 약점을 정확히 겨냥하고 있으며, 과잉 범위를 피하고 있다.
- 최종 권고는 `6 유지 / 7 신설 / wrapper 중심 구현 / 1화 tail holdback`이다.
- 확신도는 `95%`다.

## Pass 1: 문제 정의 검증

- SSOT의 문제 정의는 코드와 일치한다.
- 현재 `6번`은 Arc N 설계 후 곧바로 `arc_ep_end`까지 Stage 3/4를 진행한다.
  - `main_a.py:3598`
  - `main_a.py:3636`
- 따라서 Arc N 마지막 화는 Arc N+1 설계 결과를 보지 못한다.
- 사용자가 제기한 문제는 실제 구조적 약점으로 본다.

## Pass 2: 설계 적합성 검증

### 1. `6 유지 / 7 신설`

- 적절하다.
- 이유:
  - 기존 smoke/quick path를 유지
  - 의미가 다른 모드를 억지로 덮어쓰지 않음
  - 회귀 범위를 분리 가능

### 2. wrapper 중심 구현

- 적절하다.
- 이유:
  - Stage 3/4는 이미 `target_ep` 기반 resume contract를 갖고 있다.
  - `target_ep`를 body/tail로 나누는 일은 wrapper가 맡는 것이 가장 blast radius가 작다.
  - Stage 3/4 내부 context builder를 직접 뜯는 건 1차 구현 과잉이다.

### 3. explicit DB state 비필수

- 적절하다.
- 이유:
  - `latest_blueprint_number`, `latest_episode_number`, `arcs`로 상태 추론이 가능하다.
  - Stage 3은 기존 blueprint skip, Stage 4는 next unwritten 방식이라 자연스럽게 resume된다.
- 결론:
  - 1차 구현은 추론 기반이 맞다.
  - 별도 checkpoint는 후속 개선으로 미뤄도 된다.

## Pass 3: 과잉 범위 제거

- 아래 항목은 SSOT에서 제외된 것이 맞다.
  - Stage 3 prompt/context 개선
  - Stage 4 writer/director prompt 개선
  - 6번 모드 의미 변경
  - DB schema 추가
  - holdback 2화 이상 확장
- 이유:
  - 모두 현재 목표인 `tail 1화 lookahead`보다 넓다.
  - 지금 묶으면 설계는 멋있어 보여도 구현 ROI가 급격히 떨어진다.

## Retained Design Decisions

### D-1. body/tail split은 `ep_end-1` / `ep_end`

- 이유:
  - 문제의 핵심이 “마지막 화”의 미래 정보 부족이기 때문이다.
- 대안 기각:
  - 2화 이상 holdback은 복잡도만 증가

### D-2. final arc는 예외적으로 full close

- 이유:
  - 다음 arc가 없으므로 lookahead 이득이 없다.
- 대안 기각:
  - final arc tail 수동 승인 모드는 1차 구현 과잉

### D-3. planner helper 분리

- 이유:
  - 지금 `main_a.py`의 `_one_stop_pipeline()`는 이미 길다.
  - lookahead 상태 분기는 pure helper로 분리해야 테스트 가능성이 생긴다.

## Open Questions

- 없음

이번 감리 기준으로는 blocker가 되는 미해결 질문은 없다.

## Final Judgment

- SSOT는 충분히 구체적이다.
- 구현 범위는 작고, 코드 현실과 맞는다.
- 새 기능은 구조 개선 효과가 분명하며 기존 `6`과 충돌하지 않는다.
- 따라서 본 문서는 `execution-ready`로 확정한다.

## Confidence Ledger

- `70`: One-Stop / Stage 3 / Stage 4 현재 contract 확인
- `+10`: body/tail split을 wrapper에서 처리 가능함을 코드로 확인
- `+10`: resume semantics를 기존 DB/파일 상태로 추론 가능함을 확인
- `+5`: 과잉 범위 제거 및 final arc 예외 정책 확정
- 최종: `95`

## Notes

- 이번 턴은 문서화와 3-pass 감리만 수행했다.
- 코드 수정, 테스트 실행, rerun은 아직 하지 않았다.
