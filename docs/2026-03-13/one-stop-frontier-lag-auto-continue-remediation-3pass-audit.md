# One-Stop Frontier Lag 자동 연속 실행 수정 3PASS 감리

> 작성일: 2026-03-13
> 대상 SSOT: `docs/2026-03-13/one-stop-frontier-lag-auto-continue-remediation-execution-ssot.md`

---

## Executive Summary

- 판정: `execution-ready`
- 최종 확신도: `95%`
- 결론:
  - `7번`의 batch 경계 승인 프롬프트는 unattended long run 목적과 충돌한다.
  - 이를 제거하고 `batch size 고정 자동 반복`으로 바꾸는 방향이 가장 ROI가 높다.
  - `6번`은 그대로 두므로, “사용자 승인 기반 배치 처리”가 꼭 필요하면 기존 `6` 또는 작은 batch 실행으로 대응 가능하다.

---

## Pass 1. 문제 정의 감리

- 실제 승인 지점은 `_one_stop_pipeline_frontier_lag()` 내부 `계속할까요?`와 `추가로 몇 개 Arc...` 입력이다.
- Arc 간 hard stop은 이 프롬프트가 아니라 Stage 2/3 실패 경로에 있다.
- 따라서 사용자 지적은 정확하다.

판정:

- 문제 정의 타당
- 수정 범위는 `7번 wrapper` 한정이 맞다.

---

## Pass 2. 대안 비교 감리

검토 대안:

1. 승인 프롬프트 유지
2. 승인만 제거하고 다음 batch 크기는 다시 질문
3. 승인 제거 + 초기 입력을 batch size로 고정해 자동 반복
4. `7번` 자체를 “끝까지 무조건 전부” 모드로 변경

판정:

- 1은 현재 요구와 충돌
- 2는 여전히 장기 unattended run에 입력이 남는다
- 4는 사용자가 `1Arc 단위`로도 돌리고 싶을 때 과하다
- 3이 가장 균형적이다

결론:

- `batch size 고정 자동 반복`이 최적안

---

## Pass 3. 위험 감리

주요 위험:

- `target_count` 의미가 바뀌어 혼동될 수 있음
- 마지막 tranche 처리에서 off-by-one 가능성
- `6번`과 역할이 겹쳐질 수 있음

완화:

- SSOT에서 `target_count -> batch size`로 명시적 재정의
- `min(remaining_design, batch_size)` 규칙 고정
- `6번`은 기존 “입력한 수만큼만 처리” 의미를 유지

최종 판정:

- 위험은 방어 가능
- 구현 blocker 없음

---

## Confidence Ledger

- `70`: 승인 지점과 current control flow 확인
- `+10`: 대안 비교 후 batch size 자동 반복안 확정
- `+10`: `6`/`7` 역할 분리 유지 확인
- `+5`: hard stop 유지 범위 명시

최종 확신도: `95%`
