# Opus TF 전 스테이지 재감사 통합 보고서

**Date**: 2026-02-21
**Auditor**: Opus TF (5 parallel agents)
**Commit baseline**: `5d073a7` (S2#1 NegativeExampleInjector genre dispatch fix 포함)

---

## 1. Executive Summary

| Stage | CRITICAL | IMPORTANT | INSIGHT | Total |
|-------|----------|-----------|---------|-------|
| Stage 0/1 | 0 | 4 | 3 | 7 |
| Stage 2 | 2 | 4 | 4 | 10 |
| Stage 3 | 0 | 4 | 8 | 12 |
| Stage 4 | 0 | 3 | 10 | 13 |
| Cross-cutting | 0 | 5 | 9 | 14 |
| **Total** | **2** | **20** | **34** | **56** |

### Top 3 Clusters

1. **Director 권한 우회** (S2-01, S3-09): Director 크래시 시 auto-PASS, retry 소진 시 PASS_WITH_WARNING — 대원칙 #3 위반 2건
2. **WorldState/FactLedger 데이터 소스 오류** (S4-02, XC-07): V68 장기 일관성 시스템이 잘못된 데이터 사용, 타입 혼동
3. **동기/비동기 경로 불일치** (XC-01, XC-14, XC-02): 검증 파이프라인의 sync/parallel 경로가 다른 임계값/점수 적용

---

## 2. CRITICAL Findings (2건)

### S2-01. Director crash fallback auto-PASS
- **File**: `modules/core/stage2_finalizer.py:142-149`
- **TF**: TF-4 (Architecture)
- **Content**: Director 에이전트 크래시 시 `decision: "PASS", score: 50` 폴백. Director가 Arc를 보지 못했는데 PASS 처리. 대원칙 #3 직접 위반.
- **Impact**: API 불안정 시 저품질 Arc가 Director 심사 없이 통과
- **Fix**: 폴백을 REJECT으로 변경하거나, 예외를 전파하여 retry 루프에서 처리

### S2-02. StateTracker rollback snapshot misses genre-specific registries
- **File**: `modules/core/stage2_preflight.py:601-620`
- **TF**: TF-2 (Data flow)
- **Content**: 스냅샷 13개 필드 중 `dungeon_clear_registry`, `skill_cooldown_registry`, `spell_repertoire` 누락. Director REJECT 후 롤백 시 팬텀 데이터 잔류.
- **Impact**: 장르별(헌터/판타지) 레지스트리에 REJECT된 Arc 데이터 누적
- **Fix**: 스냅샷 deepcopy 블록에 3개 필드 추가

---

## 3. IMPORTANT Findings (20건)

### Tier 1 — 데이터 흐름 정확성 (수정 권장)

| ID | Title | File | Difficulty |
|----|-------|------|------------|
| S4-02 | WorldState/FactLedger가 arc_data.state_changes 사용 (final_state_updates 아님) | `stage4_post_processor.py:429,450` | MEDIUM |
| S4-07 | 품질 회귀 감지 stage=2 하드코딩 (stage=4 여야 함) | `stage4_post_processor.py:509` | LOW |
| XC-07 | WorldState.last_updated_ep int/str 혼합 | `world_state.py:93-96` | LOW |
| S4-01 | CoVe REJECT 시 state_updates 소실 | `stage4_orchestrator.py:568-574` | LOW |

### Tier 2 — 검증 정확성

| ID | Title | File | Difficulty |
|----|-------|------|------------|
| XC-01 | validate() sync 경로에 adaptive threshold 미적용 | `validation_orchestrator.py` | MEDIUM |
| XC-10 | relation_dynamics 위반이 항상 justifiable로 분류 | `consistency_validator.py:126-131` | LOW |
| XC-04 | ContinuityValidator가 현재 HUD를 이전 HUD로 폴백 | `continuity_validator.py:211-214` | MEDIUM |
| S3-09 | PASS_WITH_WARNING이 Director REJECT 오버라이드 | `three_phase_blueprint_generator.py:422-432` | HIGH |
| S2-04 | 레거시 flow guard가 임베딩 임계값으로 Jaccard 비교 | `stage2_validation_pipeline.py:691-713` | LOW |

### Tier 3 — LLM 상호작용

| ID | Title | File | Difficulty |
|----|-------|------|------------|
| S2-06 | PreflightChecker bare json.loads → _extract_json_robust 미사용 | `preflight_checker.py:155-156` | LOW |
| S01-03 | Self-critic final_arc 수정본 미사용 (pass/fail 게이트만) | `analyst.py:836-864` | MEDIUM |
| S01-04 | story_expander LLM 실패 시 빈 Bible 생성 | `story_expander.py:55-75` | MEDIUM |
| S3-04 | feedback 변수가 retry마다 누적 (reset 없음) | `three_phase_blueprint_generator.py` | LOW |

### Tier 4 — 아키텍처/스레드 안전

| ID | Title | File | Difficulty |
|----|-------|------|------------|
| XC-05 | BaseAgent class-level mutable state 불완전 lock | `base_agent.py` | MEDIUM |
| S2-05 | NegativeExampleInjector 읽기 시 lock 미사용 | `negative_example_injector.py` | LOW |
| S2-03 | SemanticPlotGuard.check_new_arc() 동일 arc 2회 호출 | `stage2_finalizer.py:64,293` | LOW |
| S01-01 | arcs_anchor dict/list 타입 불일치 (dead code) | `analyst.py:927-929` | LOW |
| S01-02 | persist_to_vectordb ep_num-1 인덱싱 오류 (비연속 에피소드) | `reverse_expander.py:453` | LOW |
| S3-01 | 연속성 REJECT 시 stats/_previous_best 미갱신 | `three_phase_blueprint_generator.py:316-321` | MEDIUM |
| S3-11 | score_breakdown이 UnifiedBlueprintValidator에서 미반환 | `three_phase_blueprint_generator.py:385-389` | MEDIUM |
| S3-02 | _handle_failure가 실패 에피소드 건너뛰어 순차 의존성 파괴 | `stage3_orchestrator.py:559,565` | LOW |

---

## 4. INSIGHT Findings (34건)

<details>
<summary>전체 INSIGHT 목록 (접기/펼치기)</summary>

| ID | Title | Stage |
|----|-------|-------|
| S01-05 | Double input() in block extension | 0/1 |
| S01-06 | _extract_npcs may return dict | 0/1 |
| S01-07 | VecMemory lock=None | 0/1 |
| S2-07 | Quality gate early return minimal dict | 2 |
| S2-08 | Non-ImportError skips legacy fallback | 2 |
| S2-09 | _cached_preflight_result = {} vs None | 2 |
| S2-10 | FourPhase bypasses DraftValidator by design | 2 |
| S3-03 | Continuity REJECT inflates phase1_complete | 3 |
| S3-05 | Independent section truncation | 3 |
| S3-07 | _ci.acquire_patterns null guard | 3 |
| S3-08 | Continuity check best_blueprint only | 3 |
| S3-10 | _escape_braces not on pov_constraint | 3 |
| S3-12 | protagonist_config None guard (safe) | 3 |
| S3-13 | Timeline header count vs range | 3 |
| S3-06 | Pydantic roundtrip timing (correct) | 3 |
| S4-03 | time_warnings accumulate across rounds | 4 |
| S4-04 | CoVe overwrites all director_feedback | 4 |
| S4-05 | Mandatory context truncation order | 4 |
| S4-06 | prev_manuscripts loaded twice | 4 |
| S4-08 | Empty manuscript candidates to Director | 4 |
| S4-09 | cumulative_bible collected but unused | 4 |
| S4-10 | save_manuscript commits before tracker | 4 |
| S4-11 | Patch mode single_strategy filter | 4 |
| S4-12 | Truncation split pattern misses headers | 4 |
| S4-13 | Manuscript cache thread safety (safe) | 4 |
| XC-02 | Sync missing pre_llm_adjustment | XC |
| XC-03 | PreLLMValidator always passed=True | XC |
| XC-06 | Manual lock pattern (correct) | XC |
| XC-08 | Parallel REJECT spread (correct) | XC |
| XC-09 | PromptLoader singleton (correct) | XC |
| XC-11 | FactLedger/WorldState no auto-save | XC |
| XC-12 | _extract_json_robust seen_ids (correct) | XC |
| XC-13 | BlockingValidator degraded counter no escalation | XC |
| XC-14 | Parallel PASS threshold hardcoded 85 | XC |

</details>

---

## 5. 이전 감사 대비 변동표

| Category | Count | Notes |
|----------|-------|-------|
| S2#1 genre dispatch | FIXED | commit `5d073a7` — 검증 완료 (S2-V1) |
| 신규 발견 | 56건 | CRITICAL 2 + IMPORTANT 20 + INSIGHT 34 |
| 이전 TF 55건 대비 | — | 이전 수정 완료 건은 재감사 범위에서 regression 없음 확인 |

---

## 6. 도메인별 교차 참조 매트릭스

| 렌즈 | CRITICAL | IMPORTANT | INSIGHT |
|------|----------|-----------|---------|
| TF-1 LLM 상호작용 | 0 | 4 (S2-06, S01-03, S01-04, S3-04) | 8 |
| TF-2 데이터 흐름 | 1 (S2-02) | 8 (S4-02, S4-07, XC-07, S4-01, XC-04, S01-01, S01-02, S3-11) | 8 |
| TF-3 검증 | 0 | 5 (XC-01, XC-10, S3-09, S2-04, S3-02) | 6 |
| TF-4 아키텍처 | 1 (S2-01) | 3 (XC-05, S2-05, S2-03) | 8 |
| TF-5 도메인 | 0 | 0 | 4 |

---

## 7. 우선순위 Tier 분류

### Tier 1 — 즉시 수정 (CRITICAL + 고영향 IMPORTANT)
1. **S2-01**: Director crash → REJECT으로 변경 (대원칙 위반)
2. **S2-02**: StateTracker 스냅샷에 3개 레지스트리 추가
3. **S4-02**: WorldState/FactLedger 데이터 소스를 final_state_updates로 변경
4. **S4-07**: `stage=2` → `stage=4` (1글자 수정)

### Tier 2 — 다음 스프린트 (정확성 개선)
5. **XC-01**: sync 경로에 adaptive threshold 적용
6. **XC-10**: relation_dynamics 위반 justifiable/unjustifiable 분기
7. **S2-06**: `json.loads` → `_extract_json_robust` (1줄 수정)
8. **XC-07**: WorldState.last_updated_ep 타입 통일
9. **S3-09**: PASS_WITH_WARNING 정책 재검토

### Tier 3 — 품질 개선 (가치 있지만 긴급하지 않음)
10. **S01-03**: self-critic final_arc 소비
11. **S3-04**: feedback 변수 retry 간 리셋
12. **S01-04**: story_expander 빈 Bible 검증 게이트
13. **S2-04**: Jaccard 전용 임계값 상수 도입

### Tier 4 — 방어적 개선 (INSIGHT급)
- 스레드 안전성 강화 (XC-05, S2-05)
- Dead code 정리 (XC-03, S01-01)
- 중복 호출 제거 (S2-03, S4-06)
