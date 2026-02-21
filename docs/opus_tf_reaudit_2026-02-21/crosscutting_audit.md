# Cross-Cutting Infrastructure Opus TF Audit Report

**Date**: 2026-02-21
**Scope**: `validation_orchestrator.py`, `pre_llm_validator.py`, `blocking_validator.py`, `consistency_validator.py`, `continuity_validator.py`, `base_agent.py`, `db_manager.py`, `world_state.py`, `fact_ledger.py`, `prompt_builder.py`, `prompt_loader.py`

## Findings

### XC-01. validate() sync path does not apply adaptive threshold
- **TF**: TF-3 (Validation)
- **Severity**: IMPORTANT
- **File**: `modules/validation/validation_orchestrator.py:207-558 vs 966-1183`
- **Content**: 동기 `validate()`는 정적 `pass_threshold` 사용, 비동기 `validate_parallel_v59()`는 adaptive threshold 적용. 폴백 시 다른 임계값으로 판정. `_record_validation_history_v59()`도 미호출 → streak 데이터 스테일.
- **Impact**: 병렬→동기 폴백 시 판정 기준 불일치
- **Difficulty**: MEDIUM
- **Previous**: NEW

### XC-04. ContinuityValidator uses current HUD as fallback for previous HUD
- **TF**: TF-2 (Data flow)
- **Severity**: IMPORTANT
- **File**: `modules/validation/continuity_validator.py:211-214`
- **Content**: 이전 에피소드 HUD 로딩 실패 시 현재 HUD를 "이전"으로 가정. 동일 데이터 비교 → 위반 미감지(false negative) 또는 현재 상태를 이전으로 오인(false positive).
- **Impact**: 초기 개발/DB 이슈 시 연속성 검증 무력화
- **Difficulty**: MEDIUM
- **Previous**: NEW

### XC-05. BaseAgent class-level mutable state shared across threads without full protection
- **TF**: TF-4 (Architecture)
- **Severity**: IMPORTANT
- **File**: `modules/domain/agents/base_agent.py:136,143,147-154`
- **Content**: `_context_caches` 읽기/쓰기 시 lock 미사용. `_rotation_count` 리셋(L358)이 `_rotation_lock` 밖에서 실행. ThreadPoolExecutor 병렬 사용 시 TOCTOU 위험.
- **Impact**: 병렬 앙상블 평가 시 경쟁 조건
- **Difficulty**: MEDIUM
- **Previous**: NEW

### XC-07. WorldState.last_updated_ep returns mixed int/str types
- **TF**: TF-2 (Data flow)
- **Severity**: IMPORTANT
- **File**: `modules/core/world_state.py:93-96,392-395`
- **Content**: `source="arc"` 시 `f"arc@{ep_num}"` (str), 그 외 `ep_num` (int). 프로퍼티는 `-> int` 선언. 숫자 비교/포맷팅 오류 가능.
- **Impact**: "제arc@5화 기준" 같은 이상한 출력 + 비교 오류
- **Difficulty**: LOW
- **Previous**: NEW

### XC-10. ConsistencyValidator relation_dynamics violations always go to justifiable
- **TF**: TF-3 (Validation)
- **Severity**: IMPORTANT
- **File**: `modules/validation/consistency_validator.py:126-131`
- **Content**: `_check_relation_dynamics` 위반이 `has_justification` 값과 무관하게 항상 `justifiable`에 추가. `state_action`은 정상 분기. 관계 모순이 REJECT 트리거 불가.
- **Impact**: 정당화 없는 관계 모순도 경고만 → 일관성 검증 약화
- **Difficulty**: LOW
- **Previous**: NEW

### XC-02. Sync path missing Pre-LLM adjustment vs parallel path
- **TF**: TF-2 (Data flow)
- **Severity**: INSIGHT
- **File**: `modules/validation/validation_orchestrator.py:1132-1152 vs 455-487`
- **Content**: 병렬 경로에 pre_llm_adjustment (-1) 미적용 → 1점 차이
- **Impact**: 미미한 점수 불일치
- **Difficulty**: LOW
- **Previous**: NEW

### XC-03. PreLLMValidator always returns passed=True (dead REJECT path)
- **TF**: TF-3 (Validation)
- **Severity**: INSIGHT
- **File**: `modules/validation/pre_llm_validator.py:132`
- **Content**: `passed=True` 고정 → 오케스트레이터의 `if not passed` 분기 도달 불가 (dead code)
- **Impact**: 방어적 코드, 기능적 영향 없음
- **Difficulty**: N/A
- **Previous**: NEW

### XC-06. commit_episode_factory manual lock pattern (correct with RLock)
- **TF**: TF-4 (Architecture)
- **Severity**: INSIGHT
- **File**: `modules/core/db_manager.py:1125,1278-1279`
- **Content**: 수동 acquire/release 패턴이지만 RLock 재진입으로 정상 동작
- **Impact**: 없음
- **Difficulty**: N/A
- **Previous**: NEW

### XC-08. Parallel CONSISTENCY REJECT uses **results spread (correct)
- **TF**: TF-2 (Data flow)
- **Severity**: INSIGHT
- **File**: `modules/validation/validation_orchestrator.py:1097-1110`
- **Content**: 구조 불일치이나 `**results`로 필요 데이터 포함
- **Impact**: 없음
- **Difficulty**: N/A
- **Previous**: NEW

### XC-09. PromptLoader singleton _cache reset in __new__ (correct)
- **TF**: TF-4 (Architecture)
- **Severity**: INSIGHT
- **File**: `modules/core/prompt_loader.py:31,41`
- **Content**: 싱글톤 패턴으로 정상 동작
- **Impact**: 없음
- **Difficulty**: N/A
- **Previous**: NEW

### XC-11. FactLedger/WorldState don't auto-save after update
- **TF**: TF-2 (Data flow)
- **Severity**: INSIGHT
- **File**: `modules/core/fact_ledger.py:208`, `modules/core/world_state.py:240`
- **Content**: `update_from_state_changes()` 후 호출자가 `save()` 책임. `rollback_to()`는 자동 저장. 설계적 선택(배치 저장).
- **Impact**: 크래시 시 갱신 소실 가능, 에피소드 바이블로 복구 가능
- **Difficulty**: LOW
- **Previous**: NEW

### XC-12. _extract_json_robust seen_ids discard in finally (correct)
- **TF**: TF-2 (Data flow)
- **Severity**: INSIGHT
- **File**: `modules/domain/agents/base_agent.py:981-983`
- **Content**: MAX_DEPTH(20) + MAX_VISITS(100)으로 보호, 정상 설계
- **Impact**: 없음
- **Difficulty**: N/A
- **Previous**: NEW

### XC-13. BlockingValidator degraded mode silently passes
- **TF**: TF-3 (Validation)
- **Severity**: INSIGHT
- **File**: `modules/validation/blocking_validator.py:179-190`
- **Content**: 일관성 서브모듈 예외 시 `passed=True, degraded=True`. `_degraded_count` 누적하지만 에스컬레이션 메커니즘 없음.
- **Impact**: 지속적 모듈 버그 시 일관성 검증 영구 우회
- **Difficulty**: LOW
- **Previous**: 부분적 기존 (I-C03)

### XC-14. Parallel PASS threshold hardcoded to 85 (sync uses max(85, pass_threshold))
- **TF**: TF-3 (Validation)
- **Severity**: INSIGHT
- **File**: `modules/validation/validation_orchestrator.py:1159`
- **Content**: 병렬 경로 PASS 임계값 85 하드코딩 vs 동기 경로 `max(85, pass_threshold)`
- **Impact**: 고임계값 에피소드(권말)에서 병렬 경로가 약간 더 관대
- **Difficulty**: LOW
- **Previous**: NEW

## Summary: 0 CRITICAL, 5 IMPORTANT, 9 INSIGHT
