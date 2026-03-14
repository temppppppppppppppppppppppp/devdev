# GMR-E State, Cache, Concurrency & Recovery Findings

> Date: 2026-03-13
> Commit: `d9825a69`
> Workspace State: dirty

## PASS 1 관찰

- `BaseAgent`는 클래스 레벨 `_context_caches`를 사용한다.
- project switch 시에는 `BaseAgent._context_caches.clear()`가 수행된다.
- safe-op reset/rewind/rollback/wipe는 writer/director/state_extractor 및 일부 app cache만 수동 무효화한다.
- Stage 4 advisory chain과 post-select 검사는 `ThreadPoolExecutor` 병렬 실행을 사용한다.

## PASS 2 교차 검증

- `main_a.py:1043-1049`는 project-local API key reload 시 context cache를 clear한다.
- `main_a.py:3228-3348` safe-op wrapper는 `_context_caches.clear()`를 호출하지 않는다.
- `stage4_interview_round.py:3815-3879` advisory chain은 timeout/exception을 cancel 후 계속 진행한다.

## PASS 3 최종 findings

### [GMR-E-001] BaseAgent context cache invalidation은 존재하지만 safe-op 복구면과 통합돼 있지 않다

- Severity: `P1`
- Evidence:
  - `main_a.py:1043-1049`
  - `main_a.py:3228-3348`
  - `modules/domain/agents/base_agent.py:1765-1848`
- Why macro risk:
  - project switch는 클래스 캐시를 clear하지만 rollback/wipe/reset/rewind는 app/agent별 cache만 선택적으로 무효화한다.
  - “프로젝트 전환”과 “runtime time-travel”이 서로 다른 cache invalidation semantics를 갖는다.
- Recommended next order:
  - safe-op 후 BaseAgent class cache 정책을 별도 재검토하는 메모리 계약 오더 필요.

### [GMR-E-002] Stage 4 병렬 advisory는 의도적으로 fail-open이다

- Severity: `P2`
- Evidence:
  - `modules/core/stage4_interview_round.py:2529-2588`
  - `modules/core/stage4_interview_round.py:3815-3879`
- Why macro risk:
  - advisory/post-select chain은 병렬성과 진행 지속을 우선하며, 일부 future 실패나 timeout은 warning/debug 후 계속 진행한다.
  - 이는 throughput 관점에서는 합리적이지만, validation completeness를 항상 보장하지는 않는다.
- Recommended next order:
  - advisory completeness와 advisory availability를 분리해 기록하는 후속 오더 필요.

## Closed assumptions

- “context cache는 전혀 무효화되지 않는다” 가설은 기각한다.
- 현재 문제는 invalidation 부재가 아니라 invalidation semantics의 비대칭이다.

## Last Verified
- Date: 2026-03-13
- Commit: `d9825a69`
- Workspace State: dirty
- Code Sync (Yes/No): Yes
- Verified By: Codex
