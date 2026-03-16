# TF-F: Working Loop Verification

> 조사일: 2026-03-16
> 범위: 정상 루프 13건 약식 추적 + 경계 조건 점검
> 방법: 코드 직접 읽기 + producer→consumer 양방향 추적

---

## Signal Inventory

| # | Loop | Producer | Consumer | Status | Edge Condition |
|---|------|----------|----------|--------|----------------|
| F-1 | S4 Retry on REJECT | orchestrator.py:967-1089 | interview_round.py:1485-1491 | **WORKING** | 없음 |
| F-2 | S2 Arc Validation → Retry | validation_pipeline.py:28-151 | stage2_orchestrator.py:674-679 | **WORKING** | FourPhase pre-fail |
| F-3 | S3 Blueprint Retry | stage3_orchestrator.py:1309-1326 | ThreePhaseBlueprinter 내부 | **WORKING** | max_retries=9 하드코딩 |
| F-4 | Structured Feedback → Prompt | feedback_system.py:32-76 | interview_round.py:1490 | **WORKING** | 없음 |
| F-5 | DPW → Writer Prompt | dynamic_prompt_weighting.py:270 | interview_round.py:1481 | **WORKING** | failure_learner 없으면 graceful 빈문자열 |
| F-6 | StateTracker → HUD → CW | context_builder.py:1756-1983 | context_builder.py:1983 | **WORKING** | lazy-init 오류 시 non-fatal |
| F-7 | FactLedger → Continuity | fact_ledger.py:66-740 | stage3_orchestrator.py:1206 | **FRAGILE** | advisory-only, hard validation 아님 |
| F-8 | score_breakdown → Decision | Director agent | feedback_system.py:130 | **WORKING** | 점수 구조 변동 (정규화 존재) |
| F-9 | quantify_reject_feedback | feedback_system.py:101-227 | 유틸리티 (선택적 호출) | **WORKING** | 메인 루프 외 사용 |
| F-10 | reverse_feedback S4→S3 | feedback_system.py:600-648 | 수동/선택적 | **FRAGILE** | 자동 주입 없음 |
| F-11 | reverse_feedback S3→S2 | feedback_system.py:650-689 | 수동/선택적 | **FRAGILE** | 3회 연속 실패 조건부 |
| F-12 | adaptive_feedback_intensity | feedback_system.py:766-835 | stage2_finalizer.py:1305 | **WORKING** | S2에서 정상 연결 확인 |
| F-13 | classify_rejection_feedback | feedback_system.py:837-886 | state_service.py:237 | **WORKING** | 유틸리티 (선택적) |

---

## Detailed Findings

### [TF-F-1] Stage 4 Retry on REJECT — WORKING

- **Producer**: `stage4_orchestrator.py:967-1089` — 메인 retry 루프 (`for interview_round in range(_max_rounds)`)
- **Feedback 생성**: `stage4_interview_round.py:3440-3670` — `_handle_reject`가 `_feedback_provenance`에서 `director_feedback` 구성
- **Feedback 주입**: `stage4_interview_round.py:1485-1491` — `_common_writer_kwargs["director_feedback"]`
- **Consumer**: `_generate_candidates()`가 `director_feedback` 수신
- **추가 메커니즘**:
  - `previous_attempt` dict로 REJECT 메타데이터 보존 (L3534-3562)
  - Weighted prompt injection 적용 (L1477-1487)
  - Advisory digest 병합 (L2071)
  - CoVe LLM REJECT → PASS 다운그레이드 + retry (L1011-1029)
  - Plateau detection → fix_scope 에스컬레이션 (L1102-1129)
- **Edge Condition**: 없음. 가장 견고한 루프.

### [TF-F-2] Stage 2 Arc Validation → Retry — WORKING

- **Validation Chain**:
  1. DraftValidator (L69-87)
  2. SelfReflector + Consensus (L69-87)
  3. Flow Guard + Duplicate Guard (L96-105)
  4. Full DraftValidator + ArcCorrector (L108-117)
  5. ContinuityInspector (L122-136)
- **Consumer**: `stage2_orchestrator.py:674-679` — `action=='retry'` 감지 → attempt 증가
- **Feedback 전달**: `current_feedback` → FourPhase에 전달 (L677)
- **Edge Condition**: FourPhase pre-validation 실패 시 attempt 소모 without validation (L649-654). **잠재적 갭** — validation 없이 attempt 카운트만 증가.

### [TF-F-3] Stage 3 Blueprint Retry — WORKING

- **Producer**: `stage3_orchestrator.py:1309-1326` — `three_phase_bp.generate(max_retries=9)`
- **내부 루프**: ThreePhaseBlueprinter 내부에서 생성→검증→재생성
- **Edge Condition**: `max_retries=9` 하드코딩 (L1314). 설정 파일 미연동. 단일 에피소드 실패 시 Arc 수준 retry 미트리거 (L847).

### [TF-F-4] Structured Feedback → Prompt Injection — WORKING

- **Producer**: `feedback_system.py:32-43` — `build_structured_feedback()` dict 생성
- **Formatter**: `feedback_system.py:59-76` — `format_feedback_for_prompt()` 문자열 변환
- **Consumer**: `stage4_interview_round.py:1490-1491` — `director_feedback` kwarg로 주입
- **Edge Condition**: PASS decision 시 빈 문자열 반환 (L61-62). **정상 동작**.

### [TF-F-5] DynamicPromptWeighting → Writer Prompt — WORKING

- **Producer**: `dynamic_prompt_weighting.py:270-302` — `get_weighted_prompt()`
- **Consumer**: `stage4_interview_round.py:1477-1487` — director_feedback 앞에 주입
- **Data Flow**: FailureLearner → 카테고리 빈도 계산 → 가중치 → 상위 N개 directive 선택
- **Edge Condition**: `failure_learner=None` → 빈 문자열 반환 (L284-285). **Graceful degradation**.

### [TF-F-6] StateTracker → HUD → Context Window — WORKING

- **Producer**: `stage4_context_builder.py:1756-1983` — `get_hud_report()`
- **State Tracking**: L2339-2360 — 16항목 요약
- **HUD Integration**: L1902-1923 — 장르별 HUD (투자물: capital snapshot 포함)
- **Consumer**: L1983 — round_ctx에 전달
- **Edge Condition**: StateTracker 초기화 실패 시 non-fatal 로깅 (L698-701). **안전**.

### [TF-F-7] FactLedger → Continuity Check — FRAGILE ⚠️

- **Producer**: `fact_ledger.py:66-740` — 사망/아이템/스킬/관계 추적
- **Consumer**: `stage3_orchestrator.py:1206-1208` — advisory 생성용
- **문제**: FactLedger 출력이 **advisory-only**. hard validation 트리거가 아님.
  - `summarize_fact_ledger_numbers_block()` → advisory 텍스트 생성
  - validation 판정에 직접 영향 없음
- **Edge Condition**: FactLedger 충돌(NPC 사망 후 재등장 등)이 감지되어도 hard reject 없이 advisory 경고만 발생. **검증 루프 미약**.
- **Remediation**: FactLedger 충돌 시 hard constraint violation으로 에스컬레이션 권장

### [TF-F-8] score_breakdown → Pass/Reject Decision — WORKING

- **Producer**: Director agent가 score_breakdown 생성
- **Consumer**: `feedback_system.py:130-151` — quantify 시 score_breakdown 활용
- **Pass Threshold**: `director.py:50` — `_threshold("scoring.default_pass_threshold", 60)`
- **Edge Condition**: score_breakdown 구조가 가변적 (dict with score/max sub-fields 또는 flat int/float). **정규화 함수 존재** (feedback_system.py:83-99).

### [TF-F-9] quantify_reject_feedback — WORKING

- **Producer**: `feedback_system.py:101-227` — REJECT 사유를 수치로 정량화
- **기능**: 분량 부족 → "대화 +300자, 묘사 +400자" 수준 구체화
- **Edge Condition**: 메인 S4 루프에서 항상 호출되지는 않음 (선택적 유틸리티). 호출 시 정상 작동.

### [TF-F-10] reverse_feedback S4→S3 — FRAGILE ⚠️

- **Producer**: `feedback_system.py:600-648` — `generate_reverse_feedback_stage4_to_3()`
- **기능**: S4 Writer reject 사유 분석 → S3 Blueprint 설계에 건축적 가이드 제공
- **Consumer**: **자동 주입 없음**. 수동/선택적 호출 설계.
- **Edge Condition**: Stage 4에서 반복 reject 시 S3 Blueprint 재설계 트리거가 없음. S4 retry만 반복.
- **Remediation**: S4 reject 3회 연속 시 S3 Blueprint 재생성 + reverse_feedback 자동 주입 권장

### [TF-F-11] reverse_feedback S3→S2 — FRAGILE ⚠️

- **Producer**: `feedback_system.py:650-689` — `generate_reverse_feedback_stage3_to_2()`
- **조건**: `len(architect_failures) >= 3` (L652) — 3회 연속 실패 시에만 활성화
- **Consumer**: **자동 주입 없음**. 수동/선택적.
- **Edge Condition**: S3에서 3회 미만 실패 시 완전 무시. S2 Arc 재설계 트리거 부재.

### [TF-F-12] adaptive_feedback_intensity — WORKING

- **Producer**: `feedback_system.py:766-835` — stage/retry별 피드백 강도 조절
- **Consumer**: `stage2_finalizer.py:1305-1306` — pass_threshold 설정에 활용
- **전략**: Attempt 0(상세/70점) → 1(집중/65) → 2+(최소/55)
- **Edge Condition**: S4에서는 내부적으로 참조되나 명시적 호출 미확인. **S2에서는 정상 연결**.

### [TF-F-13] classify_rejection_feedback — WORKING

- **Producer**: `feedback_system.py:837-886` — REJECT 사유를 카테고리별 구조화
- **Consumer**: `state_service.py:237-239` (thin wrapper)
- **카테고리**: 분량/씬 누락/연속성/아이템/관계/Show Don't Tell/기타
- **Edge Condition**: 키워드 미매칭 시 "기타 문제" fallback (L878-880). **안전**.

---

## Summary

| Status | Count | Loops |
|--------|-------|-------|
| **WORKING** | 10 | F-1,2,3,4,5,6,8,9,12,13 |
| **FRAGILE** | 3 | F-7 (FactLedger advisory-only), F-10 (S4→S3 auto 없음), F-11 (S3→S2 auto 없음) |
| **BROKEN** | 0 | — |

### 구조적 패턴

**Forward 루프 견고 / Reverse 루프 미약**:
- S4 retry (F-1), S2 retry (F-2), S3 retry (F-3): 모두 정상 작동
- DPW/HUD/Feedback formatting: 정상
- **역방향 피드백 (F-10, F-11)**: 구현되어 있으나 **자동 주입 미연결**
- **FactLedger (F-7)**: 데이터 축적하나 **hard validation 미연결**

### 경계 조건 요약

| Loop | Edge Condition | 심각도 |
|------|---------------|--------|
| F-2 | FourPhase pre-fail 시 attempt 소모 without validation | LOW |
| F-3 | max_retries=9 하드코딩, 설정 미연동 | LOW |
| F-7 | FactLedger 충돌 → advisory만, hard reject 없음 | **MEDIUM** |
| F-10 | S4 반복 reject 시 S3 재설계 미트리거 | **MEDIUM** |
| F-11 | S3 3회 미만 실패 시 S2 재설계 미트리거 | LOW |

### Remediation 우선순위

| 우선순위 | Loop | 조치 |
|---------|------|------|
| **P1** | F-7 | FactLedger 충돌 → hard constraint violation 에스컬레이션 |
| **P2** | F-10 | S4 reject 3회 연속 시 S3 Blueprint 재생성 자동 트리거 |
| P3 | F-11 | S3 반복 실패 시 S2 Arc 재설계 자동 트리거 |
| KEEP | F-2,3 | 현행 유지 (경계 조건 영향도 낮음) |
