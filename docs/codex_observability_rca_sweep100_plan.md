# Observability & RCA 100-Round Sweep Plan

> 관점: 장애가 났을 때 "무엇이 왜 실패했는지"를 빠르게 재현/설명할 관측 데이터가 있는지 검증

## 핵심 질문
- 로그/메트릭만으로 원인을 재구성 가능한가?
- warning/high_warning가 실제 운영 의사결정에 충분한가?
- silent pass가 문제 은닉으로 작동하지 않는가?

## 10개 Phase × 10 Round
- Phase 1 (R01-R10): 로그 표준(모듈/ep/round) 준수율
- Phase 2 (R11-R20): warning/high_warning 분류 일관성
- Phase 3 (R21-R30): stage trace 상관키 유무
- Phase 4 (R31-R40): validator 근거 추적성(file:line)
- Phase 5 (R41-R50): silent-pass 남용 점검
- Phase 6 (R51-R60): DB/API/파일 장애 로그 품질
- Phase 7 (R61-R70): 재시도 경로에서 최초 원인 보존
- Phase 8 (R71-R80): 비용/지연/실패율 지표 누락 탐색
- Phase 9 (R81-R90): RCA 재현성(동일 로그로 동일 결론)
- Phase 10 (R91-R100): 운영 알람 임계값 검증

## Round 출력 형식
```markdown
## Round N — [관측 시나리오]
### Read Files
- file:line
### Signal Inventory
- 로그
- 메트릭
- 상태 스냅샷
### RCA Feasibility
- 원인 재구성 가능 여부
- 추가 필요 신호
### Findings
- BUG / RISK / SAFE
```

## 결과 파일
- `docs/codex_findings_observability_rca_sweep100.md`

## 수동 검사 가드
- 금지: `rg`, `grep`, `freg`, `greg`, `Select-String`, 전역 검색
- 허용: 파일 직접 열람
- 필수: 모든 판단에 `file:line` 근거
