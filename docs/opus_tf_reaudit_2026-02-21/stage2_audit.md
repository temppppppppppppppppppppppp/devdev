# Stage 2 Opus TF Audit Report

**Date**: 2026-02-21
**Scope**: `stage2_orchestrator.py`, `stage2_validation_pipeline.py`, `stage2_finalizer.py`, `stage2_preflight.py`, `four_phase_arc_generator.py`, `arc_ensemble.py`, `continuity_arc.py`, `negative_example_injector.py`, `unified_arc_validator.py`, `constraint_compiler.py`, `preflight_checker.py`

## Findings

### S2-01. Director crash fallback auto-PASS violates Director sovereignty
- **TF**: TF-4 (Architecture)
- **Severity**: CRITICAL
- **File**: `modules/core/stage2_finalizer.py:142-149`
- **Content**: Director 에이전트 크래시 시 `decision: "PASS", score: 50` 폴백. Director가 Arc를 보지 못했는데 PASS 처리. `[V60.43]` 쿼터 감지 로직보다 먼저 catch하여 무효화.
- **Impact**: API 불안정 시 저품질 Arc가 Director 심사 없이 통과
- **Difficulty**: MEDIUM
- **Previous**: NEW

### S2-02. StateTracker rollback snapshot misses genre-specific registries
- **TF**: TF-2 (Data flow)
- **Severity**: CRITICAL
- **File**: `modules/core/stage2_preflight.py:601-620`
- **Content**: 스냅샷이 13개 필드 캡처하지만, `_populate_genre_registries_from_arc()` 이후 변이되는 `dungeon_clear_registry`, `skill_cooldown_registry`, `spell_repertoire` 누락. Director REJECT 후 롤백 시 팬텀 데이터 잔류.
- **Impact**: REJECT 후 재생성 시 잘못된 중복 감지
- **Difficulty**: LOW
- **Previous**: NEW

### S2-03. SemanticPlotGuard.check_new_arc() called twice on same arc
- **TF**: TF-3 (Validation)
- **Severity**: IMPORTANT
- **File**: `modules/core/stage2_finalizer.py:64, 293`
- **Content**: Director 심사 전(L64) + PASS 후(L293) 동일 arc에 대해 중복 호출. 두 번째 호출 결과는 로깅만 되고 의사결정에 영향 없음.
- **Impact**: 불필요한 임베딩 API 호출 비용
- **Difficulty**: LOW
- **Previous**: NEW

### S2-04. Legacy flow guard uses embedding threshold for Jaccard similarity
- **TF**: TF-3 (Validation)
- **Severity**: IMPORTANT
- **File**: `modules/core/stage2_validation_pipeline.py:691-713`
- **Content**: 레거시 폴백이 `SIMILARITY_THRESHOLD=0.85`를 Jaccard 유사도에 사용. 임베딩 코사인 유사도용 임계값이라 Jaccard 0.85는 거의 도달 불가 → 폴백 가드 사실상 비활성.
- **Impact**: NarrativeStructureAnalyzer 실패 시 정체 감지 우회
- **Difficulty**: LOW
- **Previous**: NEW

### S2-05. NegativeExampleInjector reads rejection_history without lock
- **TF**: TF-4 (Architecture)
- **Severity**: IMPORTANT
- **File**: `modules/domain/agents/negative_example_injector.py:288, 341`
- **Content**: `record_rejection()`은 `_rejection_lock` 사용하지만, `generate_injection()`과 `_select_relevant_categories()`는 lock 없이 읽기. `record_rejection`의 리스트 리바인드(L270) 시 동시 읽기 위험.
- **Impact**: CPython GIL 하에서 낮음, non-CPython에서 위험
- **Difficulty**: LOW
- **Previous**: NEW

### S2-06. PreflightChecker uses bare json.loads instead of _extract_json_robust
- **TF**: TF-1 (LLM interaction)
- **Severity**: IMPORTANT
- **File**: `modules/domain/agents/preflight_checker.py:155-156`
- **Content**: LLM 응답에 markdown fence나 trailing comma 있으면 `json.loads` 실패 → Python 폴백으로 전환. `_extract_json_robust()` 사용 시 해결 가능.
- **Impact**: 불필요한 품질 저하 폴백 발생
- **Difficulty**: LOW
- **Previous**: NEW

### S2-07. Quality gate early return produces minimal dict
- **TF**: TF-2 (Data flow)
- **Severity**: INSIGHT
- **File**: `modules/core/stage2_finalizer.py:200`
- **Content**: 조기 반환 시 `last_refined_context` 등 키 누락. 호출측 `.get()` 방어로 현재 안전.
- **Impact**: 향후 유지보수 위험
- **Difficulty**: LOW
- **Previous**: NEW

### S2-08. Non-ImportError exception in flow guard skips legacy fallback
- **TF**: TF-5 (Domain)
- **Severity**: INSIGHT
- **File**: `modules/core/stage2_validation_pipeline.py:687-689`
- **Content**: `NarrativeStructureAnalyzer` 런타임 오류 시 레거시 Jaccard 가드도 건너뜀
- **Impact**: S2-04와 결합 시 실질적 영향 낮음
- **Difficulty**: LOW
- **Previous**: NEW

### S2-09. Preflight error sets `_cached_preflight_result = {}` instead of None
- **TF**: TF-2 (Data flow)
- **Severity**: INSIGHT
- **File**: `modules/core/stage2_preflight.py:108-112`
- **Content**: 빈 dict vs None 이중 표현. 현재 동작 정상.
- **Impact**: 없음
- **Difficulty**: N/A
- **Previous**: NEW

### S2-10. FourPhase Arcs bypass DraftValidator and Consensus checks by design
- **TF**: TF-5 (Domain)
- **Severity**: INSIGHT
- **File**: `modules/core/stage2_preflight.py:558`
- **Content**: FourPhase Arc는 `draft_validator_passed=False`, `consensus_passed=False`로 진행. S2-01과 결합 시 쿼터 감지 안전장치도 우회.
- **Impact**: 설계상 의도적, S2-01 수정 시 해소
- **Difficulty**: N/A
- **Previous**: NEW

### S2-V1. S2#1 NegativeExampleInjector genre dispatch fix VERIFIED
- **Status**: CONFIRMED CORRECT (commit `5d073a7`)

## Summary: 2 CRITICAL, 4 IMPORTANT, 4 INSIGHT
