# TF-E: Cross-Cutting Write-Only Sinks

> 조사일: 2026-03-16
> 범위: cost_log / learnable / session logs / failure_analyzer / DPW / audit_service / soft_failures
> 방법: Grep 전체 .py 검색 + 인스턴스화 추적

---

## Signal Inventory

| # | Signal | Writer (file:line) | Reader | Runtime Impact | Status | Impact |
|---|--------|-------------------|--------|---------------|--------|--------|
| E-1 | `cost_log` DB 테이블 | db_manager.py:3646-3682 | **NONE** (get_cost_summary 호출자 0) | NO | **DEAD** | M |
| E-2 | `learnable` flag | soft_failure.py:92 | **NONE** (필터 로직 없음) | NO | **DEAD** | L |
| E-3 | `llm_io.jsonl` | session_logger.py:81-113 | **NONE** | NO | **WRITE-ONLY** | L |
| E-4 | `decisions.jsonl` | session_logger.py:115-142 | failure_analyzer.py:152-230 (사후 분석) | NO | **ANALYSIS-ONLY** | L |
| E-5 | `state_changes.jsonl` | session_logger.py:144-169 | **NONE** | NO | **WRITE-ONLY** | L |
| E-6 | `ui_events.jsonl` | session_logger.py:171-227 | **NONE** | NO | **WRITE-ONLY** | L |
| E-7 | `audit_service` | audit_service.py:45-56 | flush at shutdown (디스크 기록) | NO | **WRITE-ONLY** | L |
| E-8 | `soft_failures.jsonl` | soft_failure.py:169-170 | bridge_server.py:1166-1204 (진단 UI) | NO | **DIAGNOSTIC** | L |

### 참고: LIVE 시스템 (정상 루프 확인)

| Signal | Writer | Reader | Runtime Impact | Status |
|--------|--------|--------|---------------|--------|
| `DynamicPromptWeighter` | main_a.py:2063 (인스턴스화) | stage4_interview_round.py:1481 (프롬프트 주입) | **YES** | **LIVE** |
| `FailureLearner` | record_failure() (4곳) | DPW + AdaptiveManager | **YES** | **LIVE** |

---

## Detailed Findings

### [TF-E-1] cost_log — DEAD

- **Writer**: `DBManager.save_cost_record()` → `db_manager.py:3646-3682`
  - 호출처: main_a.py, stage2_finalizer.py, stage3_orchestrator.py, stage4_interview_round.py, stage4_post_processor.py
  - DB 테이블: `cost_log` (session_id, scope_type, total_calls, total_tokens, total_cost_usd, model_breakdown)
- **Reader**: `DBManager.get_cost_summary()` → `db_manager.py:3684-3698`
  - **호출자 0건** — 메서드 정의는 있으나 아무도 호출하지 않음
- **Status**: DEAD — 비용 데이터 축적되나 런타임/분석 모두 비소비
- **Evidence**: Grep `get_cost_summary` → db_manager.py 내부 정의만 히트
- **Impact**: M — 비용 모니터링/예산 제한 기능 없음. 무한 API 호출 가능
- **Remediation**: WIRE — 세션별 cost_limit 임계값 도입 또는 대시보드 연동 권장

### [TF-E-2] learnable flag — DEAD

- **Writer**: `report_soft_failure(..., learnable=True, ...)` → `soft_failure.py:92`
  - soft_failures.jsonl에 `"learnable": true` 필드로 기록
  - 호출처: failure_analyzer.py:44, session_logger.py:345, stage4_post_processor.py, validation_orchestrator.py
- **Reader**: **NONE**
  - bridge_server.py:1166-1204가 soft_failures.jsonl 읽지만 learnable 필터 **미적용**
  - learnable==True 이벤트를 수집/학습하는 로직 전무
- **Status**: DEAD — "학습 가능" 태깅만 하고 학습 파이프라인 없음
- **Evidence**: Grep `learnable` → soft_failure.py/호출처만 히트. 필터 로직 0건
- **Impact**: L — 의도된 "자동 학습" 기능 미구현 상태
- **Remediation**: REMOVE 또는 WIRE — learnable 이벤트 수집 → FailureLearner 연동 파이프라인 구축

### [TF-E-3] llm_io.jsonl — WRITE-ONLY

- **Writer**: `SessionLogger.log_llm_call()` → `session_logger.py:81-113`
  - BaseAgent.ask() 호출마다 프롬프트/응답/모델/duration 기록
- **Reader**: **NONE**
- **Status**: WRITE-ONLY — 디버깅/감사 목적 축적. 자동 분석 없음
- **Impact**: L — 순수 감사 로그. 런타임 영향 불필요할 수 있음
- **Remediation**: KEEP-AUDIT — 사후 분석용으로 가치 있음. 런타임 소비 불필요

### [TF-E-4] decisions.jsonl — ANALYSIS-ONLY

- **Writer**: `SessionLogger.log_decision()` → `session_logger.py:115-142`
  - Director 판정 경로 기록 (stage, ep_num, decision_type, result, score)
- **Reader**: `FailureAnalyzer._load_session_decision_entries()` → `failure_analyzer.py:152-230`
  - sink_alignment_summary() / cross-sink 정합성 검증용
  - **사후 분석 전용** — 런타임 영향 없음
- **Status**: ANALYSIS-ONLY
- **Impact**: L
- **Remediation**: KEEP-AUDIT

### [TF-E-5] state_changes.jsonl — WRITE-ONLY

- **Writer**: `SessionLogger.log_state_change()` → `session_logger.py:144-169`
  - WorldState/FactLedger 변경 기록
- **Reader**: **NONE**
- **Status**: WRITE-ONLY
- **Impact**: L
- **Remediation**: KEEP-AUDIT

### [TF-E-6] ui_events.jsonl — WRITE-ONLY

- **Writer**: `SessionLogger.log_ui_event()` → `session_logger.py:171-227`
  - 오퍼레이터 대면 UI 이벤트 기록
- **Reader**: **NONE**
- **Status**: WRITE-ONLY
- **Impact**: L
- **Remediation**: KEEP-AUDIT

### [TF-E-7] audit_service — WRITE-ONLY

- **Writer**: `AuditService.audit_event()` → `audit_service.py:45-56`
  - 인메모리 `_runtime_audit` 리스트에 축적 (cap 1000)
  - `flush_audit_buffer()` → `runtime_audit.jsonl`에 디스크 기록
- **Reader**: 없음 (shutdown 시 디스크 기록만)
  - `write_audit_summary()` → main_a.py:2964 (수동 호출, 사후 분석)
- **Status**: WRITE-ONLY (LIVE 인스턴스지만 런타임 결정에 무영향)
- **Impact**: L
- **Remediation**: KEEP-AUDIT

### [TF-E-8] soft_failures.jsonl — DIAGNOSTIC

- **Writer**: `report_soft_failure()` → `soft_failure.py:169-170`
  - 비차단 실패 이벤트 JSONL 기록
- **Reader**: `bridge_server.py:1166-1204` (_load_runtime_health)
  - 최근 N건 로드 → 진단 UI 표시
  - **learnable 필터 미적용**, 전체 이벤트 표시
- **Status**: DIAGNOSTIC — 읽히긴 하나 런타임 결정에 무영향
- **Impact**: L
- **Remediation**: KEEP-AUDIT

---

## Summary

| Status | Count | Signals |
|--------|-------|---------|
| **DEAD** | 2 | cost_log, learnable flag |
| **WRITE-ONLY** | 4 | llm_io.jsonl, state_changes.jsonl, ui_events.jsonl, audit_service |
| **ANALYSIS-ONLY** | 1 | decisions.jsonl |
| **DIAGNOSTIC** | 1 | soft_failures.jsonl |
| **LIVE** | 2 | DynamicPromptWeighter, FailureLearner (참고) |

### 구조적 패턴

**"기록은 하되 읽지 않는" 텔레메트리 과잉**: 8개 cross-cutting 신호 중 6개가 write-only. 시스템이 방대한 데이터를 축적하지만 런타임에 활용하는 경로는 DPW↔FailureLearner 단일 루프뿐.

**DEAD 신호 2건은 구현 미완성**:
- cost_log: get_cost_summary() 메서드까지 만들어놓고 호출처 없음
- learnable: 태깅 인프라 완성, 학습 파이프라인 미구축

### Remediation 우선순위

| 우선순위 | Signal | 조치 | 근거 |
|---------|--------|------|------|
| **P1** | cost_log | WIRE — 세션/아크별 비용 대시보드 또는 예산 임계값 | 비용 통제 필요 |
| **P2** | learnable | WIRE 또는 REMOVE — FailureLearner 연동 파이프라인 | 의도된 기능 미완성 |
| KEEP | llm_io/decisions/state_changes/ui_events | KEEP-AUDIT — 감사 로그 가치 | 사후 분석용 |
| KEEP | audit_service / soft_failures | KEEP-AUDIT | 진단/감사 목적 |
