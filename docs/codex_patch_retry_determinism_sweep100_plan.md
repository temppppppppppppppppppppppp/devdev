# Patch-Retry 결정성 100-Round Sweep Plan

> 관점: Stage2 patch mode 확장 이후 재시도 품질이 "운빨"이 아니라 결정적으로 관리되는지 검증

## 핵심 질문
- 같은 실패 피드백이면 같은 수정 방향으로 수렴하는가?
- 재시도 횟수 증가가 품질을 올리는가, 아니면 잡음을 키우는가?
- rollback/retry 경계에서 상태 오염이 없는가?

## 10개 Phase × 10 Round
- Phase 1 (R01-R10): patch mode 진입/탈출 조건 정확성
- Phase 2 (R11-R20): feedback 전달 보존율(손실/왜곡)
- Phase 3 (R21-R30): retry 카운터/임계값/종료조건
- Phase 4 (R31-R40): snapshot-rollback 일관성
- Phase 5 (R41-R50): 부분 patch 병합 충돌
- Phase 6 (R51-R60): Stage2->Stage3->Stage4 전달 안정성
- Phase 7 (R61-R70): validator 경고와 retry 전략 상호작용
- Phase 8 (R71-R80): commit idempotency (중복 저장 방지)
- Phase 9 (R81-R90): 지연/비용 증가폭과 품질 상관
- Phase 10 (R91-R100): 복합 장애(LLM 거부+retry+rollback)

## Round 출력 형식
```markdown
## Round N — [retry 시나리오]
### Read Files
- file:line
### Retry Path Trace
- 진입 조건
- 피드백 전달
- 패치 적용/검증 결과
### Findings
- BUG / RISK / SAFE
### Determinism Verdict
- 동일 입력 재현성: High / Medium / Low
```

## 결과 파일
- `docs/codex_findings_patch_retry_determinism_sweep100.md`

## 수동 검사 가드
- 금지: `rg`, `grep`, `freg`, `greg`, `Select-String`, 전역 검색
- 허용: 파일 직접 열람
- 필수: 모든 판단에 `file:line` 근거
