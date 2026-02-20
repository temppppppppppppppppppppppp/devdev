# Resume/Replay Idempotency 100-Round Sweep Plan

> 관점: 중단/재개/재실행 상황에서 중복 커밋, 상태 꼬임, 재현 불가를 제거

## 핵심 질문
- 같은 체크포인트에서 재개하면 동일 결과를 재현하는가?
- 재실행 시 side effect가 중복 발생하지 않는가?
- rollback 후 replay가 정확히 같은 상태를 만든는가?

## 10개 Phase × 10 Round
- Phase 1 (R01-R10): checkpoint 생성 시점 검증
- Phase 2 (R11-R20): Stage별 재개(0/2/3/4) 정확도
- Phase 3 (R21-R30): 동일 ep 재실행 중복 write 방지
- Phase 4 (R31-R40): rollback->replay 정합성
- Phase 5 (R41-R50): commit 경계 장애 원자성
- Phase 6 (R51-R60): 캐시 무효화/복구 일관성
- Phase 7 (R61-R70): 다중 arc 전환 경계 재개
- Phase 8 (R71-R80): 외부 장애 후 재개 안정성
- Phase 9 (R81-R90): 수동介入 후 자동 경로 복귀
- Phase 10 (R91-R100): chaos replay 종합

## Round 출력 형식
```markdown
## Round N — [resume/replay 시나리오]
### Read Files
- file:line
### Checkpoint State
- 저장된 cursor/snapshot
### Replay Trace
- 재개 위치
- 재실행 경로
- 중복 side effect 여부
### Findings
- BUG / RISK / SAFE
```

## 결과 파일
- `docs/codex_findings_resume_replay_idempotency_sweep100.md`

## 수동 검사 가드
- 금지: `rg`, `grep`, `freg`, `greg`, `Select-String`, 전역 검색
- 허용: 파일 직접 열람
- 필수: 모든 판단에 `file:line` 근거
