# Canon Field Integrity 100-Round Sweep Plan

> 관점: 직함/직업/능력/자산 등 다필드 연속성이 이벤트 근거 없이 역행하지 않는지 검증

## 핵심 질문
- core 필드가 episode 경계를 넘어 안정적으로 유지되는가?
- 변경은 반드시 이벤트 근거를 남기는가?
- override가 기록되고 재추적 가능한가?

## 10개 Phase × 10 Round
- Phase 1 (R01-R10): field registry 로드/기본값/fallback
- Phase 2 (R11-R20): canon facts 저장/조회 정합성
- Phase 3 (R21-R30): canon events append-only 무결성
- Phase 4 (R31-R40): regression_without_event 검증
- Phase 5 (R41-R50): state_machine 전이 규칙 검증
- Phase 6 (R51-R60): bounded_delta(수치 급변) 검증
- Phase 7 (R61-R70): mutual_exclusive 충돌 검증
- Phase 8 (R71-R80): Director override 사유 강제성
- Phase 9 (R81-R90): 컨텍스트 컴팩트 후 복원 정확도
- Phase 10 (R91-R100): 장기(10화+) 드리프트 회귀

## Round 출력 형식
```markdown
## Round N — [필드 정책 시나리오]
### Read Files
- file:line
### Canon Evidence
- 이전 사실값
- 신규 제안값
- 이벤트 근거 유무
### Policy Check
- strict/soft 판정
- warning/high_warning
### Findings
- BUG / RISK / SAFE
```

## 결과 파일
- `docs/codex_findings_canon_field_integrity_sweep100.md`

## 수동 검사 가드
- 금지: `rg`, `grep`, `freg`, `greg`, `Select-String`, 전역 검색
- 허용: 파일 직접 열람
- 필수: 모든 판단에 `file:line` 근거
