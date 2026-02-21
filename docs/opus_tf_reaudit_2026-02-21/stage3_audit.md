# Stage 3 Opus TF Audit Report

**Date**: 2026-02-21
**Scope**: `stage3_orchestrator.py`, `stage3_context.py`, `blueprint_ensemble.py`, `three_phase_blueprint_generator.py`, `continuity_blueprint.py`

## Findings

### S3-01. Continuity REJECT consumes retry without updating phase3 stats or _previous_best
- **TF**: TF-3 (Validation)
- **Severity**: IMPORTANT
- **File**: `modules/domain/agents/three_phase_blueprint_generator.py:316-321`
- **Content**: 연속성 REJECT 시 `continue`로 Phase 3 통계/`_previous_best`/`pipeline_result["phases"]["validate"]` 갱신 건너뜀. 다음 retry의 패치 모드가 스테일 데이터로 동작.
- **Impact**: 패치 모드 비효율 + 통계 부정확
- **Difficulty**: MEDIUM
- **Previous**: NEW

### S3-02. `_handle_failure` advances to next episode, breaking sequential dependency
- **TF**: TF-2 (Data flow)
- **Severity**: IMPORTANT
- **File**: `modules/core/stage3_orchestrator.py:559,565`
- **Content**: 실패 시 `next_ep: working_ep + 1` 반환 → 다음 에피소드의 순차 의존성 체크에서 즉시 중단. `fail_count >= 3` 로직 사실상 도달 불가(dead code).
- **Impact**: 첫 실패 후 루프 즉시 종료, 연속 실패 카운터 무의미
- **Difficulty**: LOW
- **Previous**: NEW

### S3-04. feedback variable accumulates across retries without reset
- **TF**: TF-1 (LLM interaction)
- **Severity**: IMPORTANT
- **File**: `modules/domain/agents/three_phase_blueprint_generator.py:123-128,294,319,368,380`
- **Content**: `feedback`가 retry마다 누적(연속성 오류 + 품질 게이트 + 이전 피드백). LLM에 중복/모순 피드백 전달.
- **Impact**: 컨텍스트 토큰 낭비 + LLM 혼란
- **Difficulty**: LOW
- **Previous**: NEW

### S3-09. PASS_WITH_WARNING fallback overrides Director REJECT verdicts
- **TF**: TF-3 (Validation)
- **Severity**: IMPORTANT
- **File**: `modules/domain/agents/three_phase_blueprint_generator.py:422-432`
- **Content**: 모든 retry 소진 후 best_blueprint이 있으면 `PASS_WITH_WARNING`으로 저장. Director가 명시적으로 REJECT했어도 Blueprint 사용됨. `quality_risk=True` 플래그 설정되지만 Stage 4에서 미확인.
- **Impact**: Director REJECT된 Blueprint가 Stage 4에 전달
- **Difficulty**: HIGH
- **Previous**: NEW

### S3-11. score_breakdown never populated by UnifiedBlueprintValidator
- **TF**: TF-2 (Data flow)
- **Severity**: IMPORTANT
- **File**: `modules/domain/agents/three_phase_blueprint_generator.py:385-389`
- **Content**: `validation_result.get("score_breakdown", {})` 항상 `{}` — `UnifiedBlueprintValidator`가 해당 키 미반환. 패치 모드에 세부 점수 피드백 누락.
- **Impact**: 패치 품질 저하
- **Difficulty**: MEDIUM
- **Previous**: NEW

### S3-03. Continuity REJECT bypass inflates phase1_complete stats
- **TF**: TF-3 (Validation)
- **Severity**: INSIGHT
- **File**: `modules/domain/agents/three_phase_blueprint_generator.py:186,303`
- **Content**: 연속성 REJECT 시 phase3_pass/reject 미증가 → 통계 비대칭
- **Impact**: 통과율 오표시
- **Difficulty**: LOW
- **Previous**: NEW

### S3-05. _format_prev_info_expanded independent section truncation
- **TF**: TF-1 (LLM interaction)
- **Severity**: INSIGHT
- **File**: `modules/domain/agents/blueprint_ensemble.py:746-764`
- **Content**: Blueprint(100K) + manuscript(100K) 독립 절삭 후 smart_truncate(200K). direct_prev 섹션 크기 미제한.
- **Impact**: 최종 smart_truncate로 안전
- **Difficulty**: LOW
- **Previous**: NEW

### S3-07. `_python_precheck` depends on `_ci.acquire_patterns` without null guard
- **TF**: TF-4 (Architecture)
- **Severity**: INSIGHT
- **File**: `modules/domain/agents/continuity_blueprint.py:284-307`
- **Content**: ContinuityInspector 초기화 실패 시 AttributeError
- **Impact**: 정상 운영에서 발생 확률 낮음
- **Difficulty**: LOW
- **Previous**: NEW

### S3-08. Continuity check uses best_blueprint only, not all_candidates
- **TF**: TF-3 (Validation)
- **Severity**: INSIGHT
- **File**: `modules/domain/agents/three_phase_blueprint_generator.py:313-314`
- **Content**: 앙상블 최선 후보만 연속성 검사. 실패 시 나머지 후보 미검토.
- **Impact**: 연속성 REJECT 시 불필요한 재생성
- **Difficulty**: MEDIUM
- **Previous**: NEW

### S3-10. `_escape_braces` not applied to `pov_constraint`
- **TF**: TF-1 (LLM interaction)
- **Severity**: INSIGHT
- **File**: `modules/domain/agents/blueprint_ensemble.py:380`
- **Content**: 현재 POV 제약 문자열에 중괄호 없어 안전. 향후 변경 시 KeyError 위험.
- **Impact**: 현재 없음
- **Difficulty**: LOW
- **Previous**: NEW

### S3-12. protagonist_config None guard confirmed safe
- **TF**: TF-4 (Architecture)
- **Severity**: INSIGHT
- **File**: `modules/domain/agents/blueprint_ensemble.py:122`
- **Content**: isinstance 가드로 None 보호 확인
- **Impact**: 없음
- **Difficulty**: N/A
- **Previous**: NEW

### S3-13. Timeline header shows count instead of actual episode range
- **TF**: TF-1 (LLM interaction)
- **Severity**: INSIGHT
- **File**: `modules/domain/agents/continuity_blueprint.py:403-406`
- **Content**: 윈도우 로딩 시 "제1화 ~ 제N화" 헤더가 실제 에피소드 범위와 불일치
- **Impact**: LLM에 오해 유발 가능, 개별 항목은 정확
- **Difficulty**: LOW
- **Previous**: NEW

### S3-06. Pydantic roundtrip timing with _stage3_meta (NO BUG)
- **Severity**: INSIGHT (confirmed correct)

## Summary: 0 CRITICAL, 4 IMPORTANT, 8 INSIGHT
