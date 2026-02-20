# Prompt Budget Fidelity 100-Round Sweep Plan

> 관점: 컨텍스트 절삭/요약/압축 이후에도 필수 연속성 정보가 유지되는지 검증

## 핵심 질문
- 토큰 제한이 내려가도 core 사실이 유지되는가?
- truncate 정책이 정보 중요도 우선순위를 지키는가?
- Stage3/Stage4 prompt 간 정보 비대칭이 누적되지 않는가?

## 10개 Phase × 10 Round
- Phase 1 (R01-R10): 필수/선택 섹션 우선순위 검증
- Phase 2 (R11-R20): smart truncate 의미 손실 검증
- Phase 3 (R21-R30): world_state/fact_ledger 요약 품질
- Phase 4 (R31-R40): prev_manuscripts 대용량 절삭 검증
- Phase 5 (R41-R50): Stage3 vs Stage4 정보 비대칭
- Phase 6 (R51-R60): validator 경고 반영률
- Phase 7 (R61-R70): 핵심 엔티티 정보 생존율
- Phase 8 (R71-R80): 인코딩/다국어 텍스트 손실 패턴
- Phase 9 (R81-R90): 저예산 토큰 모드 품질 저하 곡선
- Phase 10 (R91-R100): budget profile A/B 비교

## Round 출력 형식
```markdown
## Round N — [budget 시나리오]
### Read Files
- file:line
### Prompt Sections
- 주입 전 길이
- 절삭 후 길이
- 삭제/유지 섹션
### Fidelity Check
- core fact 생존율
- narrative coherence 영향
### Findings
- BUG / RISK / SAFE
```

## 결과 파일
- `docs/codex_findings_prompt_budget_fidelity_sweep100.md`

## 수동 검사 가드
- 금지: `rg`, `grep`, `freg`, `greg`, `Select-String`, 전역 검색
- 허용: 파일 직접 열람
- 필수: 모든 판단에 `file:line` 근거
