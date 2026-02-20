# 패치 이후 추가 Sweep 확장 계획 (Post-Patch Sweep Expansion)

## 목적
- 기존 4개 스윕(`lifecycle`, `reverse_exception`, `contract_compliance`, `adversarial`)이 놓치기 쉬운
  "패치 안정화 이후 리그레션"을 별도 축으로 검증한다.
- 특히 `Stage2 patch mode 확장`과 `Canon OS v2` 도입 이후의 장기 드리프트를 조기 탐지한다.

---

## 신규 Sweep 묶음 (100 Round 기준)

## Plan A: Patch-Retry 결정성 Sweep 100

- 파일명: `docs/codex_patch_retry_determinism_sweep100_plan.md`
- 결과: `docs/codex_findings_patch_retry_determinism_sweep100.md`
- 질문: "같은 입력/같은 피드백에서 재시도 경로가 안정적으로 같은 품질을 재현하는가?"

### 10개 Phase
- Phase 1 (R01-R10): Patch mode 진입 조건, fallback 조건, 분기 정확도
- Phase 2 (R11-R20): 피드백 보존/손실, patch instruction 전달 충실도
- Phase 3 (R21-R30): 재시도 카운터/임계값, 무한 재시도 방지
- Phase 4 (R31-R40): snapshot/rollback 이후 상태 복원 일관성
- Phase 5 (R41-R50): 부분 패치 병합 충돌(문장/장면/state_changes) 처리
- Phase 6 (R51-R60): Stage2 결과가 Stage3/Stage4로 넘어갈 때 품질 역전 여부
- Phase 7 (R61-R70): validator 경고와 patch 전략의 상호작용
- Phase 8 (R71-R80): DB 커밋/재시도 사이 idempotency 보장
- Phase 9 (R81-R90): 비용/지연 증가폭(패치 라운드 추가의 운영 한계)
- Phase 10 (R91-R100): 복합 실패(LLM 거부+부분 patch+rollback) 종합

---

## Plan B: Canon Field Integrity Sweep 100

- 파일명: `docs/codex_canon_field_integrity_sweep100_plan.md`
- 결과: `docs/codex_findings_canon_field_integrity_sweep100.md`
- 질문: "직함/직업/능력/자산 등 core 필드가 이벤트 근거 없이 역행하지 않는가?"

### 10개 Phase
- Phase 1 (R01-R10): `field registry` 로드/기본값/미정의 필드 처리
- Phase 2 (R11-R20): facts write/read 라운드트립, 타입 정합
- Phase 3 (R21-R30): events append-only, 이벤트 누락 탐지
- Phase 4 (R31-R40): `regression_without_event` 규칙 검증
- Phase 5 (R41-R50): `state_machine` 전이 위반 검증
- Phase 6 (R51-R60): `bounded_delta` 수치 급변 검증 (재산/평판/경지)
- Phase 7 (R61-R70): `mutual_exclusive` 충돌 검증 (직업/상태 이중기재)
- Phase 8 (R71-R80): Director override 사유 로그 강제성 검증
- Phase 9 (R81-R90): 컨텍스트 컴팩트 후 snapshot+event 재구성 정확도
- Phase 10 (R91-R100): 10화 이상 장기 드리프트 회귀 테스트

---

## Plan C: Resume/Replay Idempotency Sweep 100

- 파일명: `docs/codex_resume_replay_idempotency_sweep100_plan.md`
- 결과: `docs/codex_findings_resume_replay_idempotency_sweep100.md`
- 질문: "중단/재개/재실행 시 중복 커밋 없이 같은 상태를 복원하는가?"

### 10개 Phase
- Phase 1 (R01-R10): stage checkpoint 생성 타이밍 검증
- Phase 2 (R11-R20): Stage0/2/3/4 재시작 복원 검증
- Phase 3 (R21-R30): 동일 에피소드 재실행 시 중복 write 방지
- Phase 4 (R31-R40): rollback 후 replay 정확도
- Phase 5 (R41-R50): commit 직전/직후 장애에서 원자성 보장
- Phase 6 (R51-R60): 캐시 무효화와 복원 상태 정합
- Phase 7 (R61-R70): multi-arc 전환 중 resume 경계 테스트
- Phase 8 (R71-R80): 외부 장애(API/DB/파일) 후 재개 안정성
- Phase 9 (R81-R90): 수동介入 이후 자동 경로 복귀 가능성
- Phase 10 (R91-R100): chaos replay (다중 장애 조합)

---

## Plan D: Prompt Budget Fidelity Sweep 100

- 파일명: `docs/codex_prompt_budget_fidelity_sweep100_plan.md`
- 결과: `docs/codex_findings_prompt_budget_fidelity_sweep100.md`
- 질문: "컨텍스트 절삭/압축 이후에도 핵심 연속성 정보가 살아남는가?"

### 10개 Phase
- Phase 1 (R01-R10): section 우선순위(필수/선택) 적용 정확도
- Phase 2 (R11-R20): smart truncate 이후 의미 손실 여부
- Phase 3 (R21-R30): world_state/fact_ledger 요약 주입 품질
- Phase 4 (R31-R40): prev_manuscripts 대용량 주입 시 절삭 정책
- Phase 5 (R41-R50): Stage3와 Stage4 prompt 간 정보 비대칭
- Phase 6 (R51-R60): validator 경고가 prompt에 반영되는 비율
- Phase 7 (R61-R70): 장면 전환/핵심 엔티티 정보 유지율
- Phase 8 (R71-R80): 다국어/인코딩 텍스트 포함 시 손실 패턴
- Phase 9 (R81-R90): token budget 하향 시 품질 저하 곡선
- Phase 10 (R91-R100): 극단 budget(저예산/고예산) 비교

---

## Plan E: Observability & RCA Sweep 100

- 파일명: `docs/codex_observability_rca_sweep100_plan.md`
- 결과: `docs/codex_findings_observability_rca_sweep100.md`
- 질문: "문제가 났을 때 원인을 빠르게 재현/설명할 관측 데이터가 충분한가?"

### 10개 Phase
- Phase 1 (R01-R10): 로그 표준(모듈명, 에피소드, 라운드) 준수율
- Phase 2 (R11-R20): warning/high_warning 분류 일관성
- Phase 3 (R21-R30): stage 전환 trace 상관키 존재 여부
- Phase 4 (R31-R40): validator 결과의 근거 링크(파일/라인) 추적성
- Phase 5 (R41-R50): silent-pass 남용 여부
- Phase 6 (R51-R60): DB/파일/API 장애 시 에러 표준화
- Phase 7 (R61-R70): 재시도 경로에서 최초 원인 보존 여부
- Phase 8 (R71-R80): 비용/지연/실패율 관측값 누락 점검
- Phase 9 (R81-R90): 사후 분석(RCA) 재현 가능성
- Phase 10 (R91-R100): 운영 대시보드 임계값 유효성

---

## 권장 실행 순서 (패치 이후)

1. `codex_patch_retry_determinism_sweep100_plan.md`
2. `codex_canon_field_integrity_sweep100_plan.md`
3. `codex_resume_replay_idempotency_sweep100_plan.md`
4. `codex_prompt_budget_fidelity_sweep100_plan.md`
5. `codex_observability_rca_sweep100_plan.md`
6. 기존 4대 스윕 재실행 (`contract` -> `reverse` -> `lifecycle` -> `adversarial`)

---

## 수동 검사 강제 가드 (요약)

- 금지: `rg`, `grep`, `freg`, `greg`, `Select-String`, IDE 전역 검색.
- 허용: 파일 직접 열람 기반 수동 판정.
- 필수 근거: 모든 finding은 `file:line` 명시.
- 무중단 원칙: 하드 블로커 외 중단 금지.
- 컨텍스트 컴팩트 시: 마지막 완료 라운드 기준 즉시 재개.
