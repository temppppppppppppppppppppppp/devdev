# Opus TF-4: Dead Code 전면 감사 보고서

> 감사일: 2026-02-22
> 감사 범위: modules/, main_a.py, config/, tests/conftest.py
> 감사 도구: ruff F401/F841 + ripgrep 수동 추적 + 코드 직접 확인

---

## 총괄 요약

| 카테고리 | 항목 수 | 추정 삭제 가능 줄 수 |
|---------|---------|-------------------|
| 1. 미사용 전략 모듈 (strategies/) | 9 파일 | ~315줄 |
| 2. 미사용 코어 모듈 (전체 파일) | 5 파일 | ~2,489줄 |
| 3. 미사용 지역 변수 (F841) | 74건 | ~90줄 |
| 4. 호출 없는 public 메서드 | 10건 | ~120줄 |
| 5. 레거시/Deprecated 코드 | 4건 | ~35줄 |
| 6. 미사용 설정 키 (YAML) | 3 섹션 | ~20줄 |
| 7. 미사용 테스트 fixture | 5건 | ~40줄 |
| 8. 미사용 예외 클래스 | 2건 | ~10줄 |
| **합계** | | **~3,119줄** |

---

## 1. 미사용 전략 모듈 (modules/domain/strategies/)

**상태**: 전체 디렉토리가 코드베이스 어디에서도 import되지 않음. 내부 상호참조만 존재.

| 파일 | 줄 수 | 내용 요약 | 삭제 위험도 |
|------|------|----------|-----------|
| `modules/domain/strategies/__init__.py` | 0 | 빈 파일 | safe |
| `modules/domain/strategies/base_strategy.py` | 18 | ABC 추상 클래스. `studio_system.api_client`, `studio_system.law` 참조 | safe |
| `modules/domain/strategies/wuxia_strategy.py` | 42 | 무협 장르 시스템 프롬프트 생성. MartialHUD 접근 | safe |
| `modules/domain/strategies/hunter_strategy.py` | 41 | 헌터물 장르 시스템 프롬프트 생성. HunterHUD 접근 | safe |
| `modules/domain/strategies/investment_strategy.py` | 42 | 투자물 장르 시스템 프롬프트 생성. FinanceHUD 접근 | safe |
| `modules/domain/strategies/composer_strategy.py` | 43 | 작곡가물 장르 시스템 프롬프트 생성. ComposerHUD 접근 | safe |
| `modules/domain/strategies/cooking_strategy.py` | 43 | 요리물 장르 시스템 프롬프트 생성. CookingHUD 접근 | safe |
| `modules/domain/strategies/sports_strategy.py` | 43 | 스포츠물 장르 시스템 프롬프트 생성. SportsHUD 접근 | safe |
| `modules/domain/strategies/medical_strategy.py` | 43 | 의학물 장르 시스템 프롬프트 생성. MedicalHUD 접근 | safe |

**분석**: 이 모듈들은 장르별 Writer 시스템 프롬프트를 생성하는 레거시 Strategy 패턴의 잔재. 현재 시스템에서는 `genre_stage_prompts.py`, `genre_guards/`, `writer_prompt_builders.py` 등이 이 역할을 대체. 외부 import가 전무하므로 디렉토리 전체 삭제 안전.

**추정 삭제 가능 줄 수**: ~315줄

---

## 2. 미사용 코어 모듈 (전체 파일 단위)

### 2-A. `modules/core/models.py` (41줄) -- safe

- **위치**: `modules/core/models.py` L1-41
- **내용**: `Bible` 클래스 정의. `project_name`, `genre`, `world`, `characters` 등 속성 보유
- **분석**: `from modules.core.models import` 패턴이 코드베이스 전체에서 0건. `modules/models/` (Pydantic 모델 패키지)와 별개의 완전히 독립된 레거시 클래스. 현재 시스템은 `master_bible` dict를 직접 사용.
- **삭제 위험도**: safe

### 2-B. `modules/core/ab_testing.py` (464줄) -- safe

- **위치**: `modules/core/ab_testing.py` L1-465
- **내용**: `ABTestingFramework` + `quick_ab_test()`. Legacy vs V0128 Director A/B 테스트 프레임워크
- **분석**: `test_sweep30.py`에서만 import (기능 존재 확인 테스트). 프로덕션 코드(main_a.py, orchestrator 등)에서 호출하는 곳 없음. `audit_manuscript_v0128` 같은 레거시 API에 의존.
- **삭제 위험도**: safe (sweep30 테스트도 함께 삭제)

### 2-C. `modules/core/manuscript_enhancer.py` (788줄) -- safe

- **위치**: `modules/core/manuscript_enhancer.py` L1-788
- **내용**: `ManuscriptEnhancer` 클래스. V55 원고 품질/분량 향상 모듈
- **분석**: 현재 main_a.py에서 import 없음. `백업의백업의백업/main_a - 복사본.py`와 `test_v55_modules.py`에서만 참조. V60+ 이후 Chief Writer 체계가 이 기능을 대체.
- **삭제 위험도**: safe (test_v55_modules.py 관련 테스트도 정리 필요)

### 2-D. `modules/core/finetuning_automation.py` (425줄) -- safe

- **위치**: `modules/core/finetuning_automation.py` L1-425
- **내용**: `FineTuningManager`. Gemini Fine-tuning API 자동화 프레임워크
- **분석**: `tools2/test_phase3_systems.py`에서만 import. 프로덕션 코드에서 사용하는 곳 없음. Gemini Fine-tuning API 자체가 프로젝트에서 미사용.
- **삭제 위험도**: safe

### 2-E. `modules/core/progress_manager.py` (359줄) -- safe

- **위치**: `modules/core/progress_manager.py` L1-359
- **내용**: `ProgressManager`. 프로젝트 진행 상황 추적 + 리포트 생성
- **분석**: `_ag_deep.py`와 `_ag_scan.py`(분석 스크립트)에서만 감지됨. 프로덕션/테스트 코드에서 import 0건. 현재 시스템은 DB 직접 조회 + 대시보드로 대체.
- **삭제 위험도**: safe

### 2-F. `modules/core/semantic_cache.py` (420줄) -- caution

- **위치**: `modules/core/semantic_cache.py` L1-420
- **내용**: `SemanticCache`, `BlueprintCache`, `DescriptionCache`. 의미론적 유사도 기반 캐시
- **분석**: `test_sweep38.py`에서만 import. 프로덕션 코드에서 사용 0건. `백업의백업의백업/main_a - 복사본.py`에서 구 사용 흔적. `base_agent.py`의 Context Caching이 이 역할 대체.
- **삭제 위험도**: caution (sweep38 테스트 연쇄 삭제 필요)

**소계**: ~2,489줄 (전 모듈 삭제 시)

---

## 3. 미사용 지역 변수 (ruff F841) -- 74건

ruff F841 검출. 할당되었으나 이후 참조되지 않는 변수들.

### 주요 패턴별 분류

#### 3-A. 구조분해 후 미사용 (stage4_orchestrator.py) -- 7건

| 파일 | 라인 | 변수명 | 삭제 위험도 |
|------|-----|--------|-----------|
| `modules/core/stage4_orchestrator.py` | L354 | `current_inventory` | caution |
| `modules/core/stage4_orchestrator.py` | L355 | `current_martial_arts` | caution |
| `modules/core/stage4_orchestrator.py` | L356 | `dead_npcs` | caution |
| `modules/core/stage4_orchestrator.py` | L357 | `item_acquisition_timeline` | caution |
| `modules/core/stage4_orchestrator.py` | L385 | `reference_anchor_prompt` | caution |
| `modules/core/stage4_orchestrator.py` | L388 | `justification_prompt` | caution |
| `modules/core/stage4_orchestrator.py` | L389 | `reflexion_prompt` | caution |

**분석**: `prepare_episode_context()`가 반환하는 dict에서 구조분해하지만 이후 사용하지 않음. 다만 향후 확장 시 재사용 가능성이 있으므로 `_ =` 패턴으로 명시적 무시 처리 권장.

#### 3-B. 관계 추적기 미사용 경로 (relationship_tracker_factions.py) -- 5건

| 파일 | 라인 | 변수명 | 삭제 위험도 |
|------|-----|--------|-----------|
| `modules/core/relationship_tracker_factions.py` | L259 | `positive_path` | safe |
| `modules/core/relationship_tracker_factions.py` | L260 | `negative_path` | safe |
| `modules/core/relationship_tracker_factions.py` | L261 | `submission_path` | safe |
| `modules/core/relationship_tracker_factions.py` | L262 | `liberation_path` | safe |
| `modules/core/relationship_tracker_factions.py` | L713 | `power_balance` | safe |

#### 3-C. 검증 파이프라인 미사용 피드백 (stage2_validation_pipeline.py) -- 3건

| 파일 | 라인 | 변수명 | 삭제 위험도 |
|------|-----|--------|-----------|
| `modules/core/stage2_validation_pipeline.py` | L411 | `fix_instructions` | safe |
| `modules/core/stage2_validation_pipeline.py` | L476 | `detailed_feedback` | safe |
| `modules/core/stage2_validation_pipeline.py` | L505 | `structured_arc_feedback` | safe |

#### 3-D. 에이전트 미사용 변수 -- 기타 다수

| 파일 | 라인 | 변수명 | 삭제 위험도 |
|------|-----|--------|-----------|
| `modules/core/adaptive_retry.py` | L846 | `success` | safe |
| `modules/core/feedback_system.py` | L109 | `score_breakdown` | safe |
| `modules/core/feedback_system.py` | L762 | `feedback_lower` | safe |
| `modules/core/genre_guards/base_guard.py` | L495 | `delegation_required` | safe |
| `modules/core/genre_guards/base_guard.py` | L622 | `current_relation` | safe |
| `modules/core/power_scaling.py` | L359 | `matched_keywords` | safe |
| `modules/core/pre_director_narrative_checker.py` | L174 | `ALLOWED_TRANSITIONS` (12줄 dict) | safe |
| `modules/core/pre_director_narrative_checker.py` | L287 | `encyclopedia` | safe |
| `modules/core/prompt_optimizer.py` | L394 | `filepath` | safe |
| `modules/core/quality_amplifier.py` | L367 | `relationship_markers` | safe |
| `modules/core/reference_anchor.py` | L177 | `anchor_type` | safe |
| `modules/core/relationship_tracker_npc.py` | L142 | `negative_path` | safe |
| `modules/core/semantic_item_registry.py` | L437 | `old_owner` | safe |
| `modules/core/spinners.py` | L196 | `session_elapsed` | safe |
| `modules/core/stage0/reverse_expander.py` | L810 | `changes` | safe |
| `modules/domain/agents/analyst.py` | L588 | `content_sample` | safe |
| `modules/domain/agents/arc_corrector.py` | L106 | `issue_type` | safe |
| `modules/domain/agents/arc_corrector.py` | L215 | `result` | safe |
| `modules/domain/agents/arc_draft_validator.py` | L518 | `prev_content` | safe |
| `modules/domain/agents/arc_draft_validator.py` | L523 | `has_end_state` | safe |
| `modules/domain/agents/chief_writer.py` | L867 | `e` (except var) | safe |
| `modules/domain/agents/chief_writer_context.py` | L108 | `assets` | safe |
| `modules/domain/agents/constraint_compiler.py` | L198 | `shadow` | safe |
| `modules/domain/agents/constraint_compiler.py` | L200 | (arc_end_state 추정) | safe |
| `modules/domain/agents/continuity_arc.py` | L473, L596, L793 | 3건 | safe |
| `modules/domain/agents/continuity_blueprint.py` | L343, L376 | 2건 | safe |
| `modules/domain/agents/continuity_manuscript.py` | L983 | 1건 | safe |
| `modules/domain/agents/director_auditor.py` | L601, L607, L633 | 3건 | safe |
| `modules/domain/agents/director_continuity.py` | L616, L617, L621 | 3건 | safe |
| `modules/domain/agents/director_ensemble.py` | L197 | 1건 | safe |
| `modules/domain/agents/four_phase_arc_generator.py` | L188 | 1건 | safe |
| `modules/domain/agents/state_extractor.py` | L303 | 1건 | safe |
| `modules/domain/agents/state_tracker.py` | L481 | 1건 | safe |
| `modules/domain/agents/state_tracker_npc.py` | L710, L711 | 2건 | safe |
| `modules/validation/batch_validator.py` | L274 | 1건 | safe |
| `modules/validation/blocking_validator_consistency_checks.py` | L254 | 1건 | safe |
| `modules/validation/consistency_validator.py` | L239 | 1건 | safe |
| `modules/validation/pre_llm_validator.py` | L327, L329 | 2건 | safe |
| `modules/validation/scoring_validator.py` | L424, L440 | 2건 | safe |
| `modules/validation/validation_orchestrator.py` | L749, L778, L972 | 3건 | safe |

**추정 삭제 가능 줄 수**: ~90줄 (대부분 단일 행, ALLOWED_TRANSITIONS만 12줄 블록)

---

## 4. 호출 없는 public 메서드

### 4-A. `project_manager.py` (ProjectContext)

| 메서드 | 라인 | 줄 수 | 내용 | 삭제 위험도 |
|--------|-----|------|------|-----------|
| `get_lore_data()` | L660 | 3 | 특정 인물/아이템 설정 DB 인출. 프로덕션 호출 0건 | safe |
| `get_all_lore_by_category()` | L664 | 3 | 카테고리별 로어 전체 인출. 프로덕션 호출 0건 | safe |
| `record_surgery_result()` | L924 | 3 | 수술 결과 DB 저장. 프로덕션 호출 0건 | safe |
| `get_surgery_intelligence()` | L928 | 13 | 수술 기록 → 반성문 생성. 프로덕션 호출 0건 | safe |

### 4-B. `db_manager.py` (DBManager)

| 메서드 | 라인 | 줄 수 | 내용 | 삭제 위험도 |
|--------|-----|------|------|-----------|
| `archive_seed()` | L1007 | 7 | 복선 아카이브. protocol 정의 + 자체 정의만 존재. 호출 0건 | caution |
| `get_active_seeds()` | L1570 | 6 | 활성 복선 목록 조회. protocol 정의 + 자체 정의만 존재. 호출 0건 | caution |
| `get_all_manuscripts()` | L1688 | 5 | 전체 원고 조회. 백업 코드에서만 참조 | safe |
| `get_all_blueprints()` | L1694 | 34 | 전체 설계도 조회. 백업 코드에서만 참조 | safe |

### 4-C. `weaver.py` (Weaver)

| 메서드 | 라인 | 줄 수 | 내용 | 삭제 위험도 |
|--------|-----|------|------|-----------|
| `assign_seeds_to_arcs()` | L144 | 3 | Deprecated 메서드 (V37에서 Drive 로직으로 대체됨). `pass`만 존재 | safe |

### 4-D. `db_manager.py` 미사용 예외 클래스

| 클래스 | 라인 | 줄 수 | 내용 | 삭제 위험도 |
|--------|-----|------|------|-----------|
| `DBIntegrityError` | L30 | 4 | 정의만 존재, raise/catch 0건 | caution |
| `DBTransactionError` | L42 | 4 | 정의만 존재, raise/catch 0건 | caution |

**분석**: `DBIntegrityError`, `DBTransactionError`는 `DBError`를 상속하며 프로토콜 계약에서 참조될 가능성 있음. `archive_seed`/`get_active_seeds`는 `db_repository.py` Protocol에 정의되어 있어 Protocol 계약 파기 위험.

**추정 삭제 가능 줄 수**: ~120줄

---

## 5. 레거시/Deprecated 코드

### 5-A. `chief_writer.py` -- hud_snapshot 데드 경로

- **위치**: `modules/domain/agents/chief_writer.py` L864-866
- **내용**: `hud_snapshot = past_ms.get("hud_snapshot", {})` -- manuscripts 테이블에 hud_snapshot 컬럼이 없어 항상 `{}` 반환
- **분석**: 코드 자체에 `# [V70] NOTE: manuscripts 테이블에 hud_snapshot 컬럼 없음 -- 항상 {} 반환 (dead code)` 주석 존재. 그러나 `_get_cached_manuscript()`에서 `hud_snapshot` 키를 반환하므로, 호출 체인 전체(chief_writer_context.py L738-740 등)도 실질적으로 항상 빈 dict를 처리.
- **삭제 위험도**: caution (hud_snapshot 로직 전체 정리 필요, 파급 범위 넓음)
- **추정 삭제 가능 줄 수**: ~15줄 (chief_writer 내부만)

### 5-B. `weaver.py` -- Deprecated assign_seeds_to_arcs

- **위치**: `modules/domain/agents/weaver.py` L143-146
- **내용**: `# [Deprecated]` 주석 + `pass` 메서드
- **삭제 위험도**: safe
- **추정 삭제 가능 줄 수**: ~4줄

### 5-C. `power_scaling.py` -- 레거시 호환 dict

- **위치**: `modules/core/power_scaling.py` L144-145
- **내용**: `GROWTH_JUSTIFICATIONS = {"수련": 15, "비급": 25, ...}` -- `# 레거시 호환용` 주석
- **삭제 위험도**: caution (외부 참조 가능성 낮으나 확인 필요)
- **추정 삭제 가능 줄 수**: ~1줄

### 5-D. `metrics_collector.py` -- 레거시 모델 비용 항목

- **위치**: `modules/core/metrics_collector.py` L70
- **내용**: `"gemini-2.0-flash": {"input": 0.075, "output": 0.30},  # legacy (비용 추적용 유지)`
- **삭제 위험도**: safe (2.0-flash는 사용되지 않음)
- **추정 삭제 가능 줄 수**: ~1줄

### 5-E. `pre_director_narrative_checker.py` -- ALLOWED_TRANSITIONS 미사용

- **위치**: `modules/core/pre_director_narrative_checker.py` L173-184
- **내용**: 12줄짜리 dict 할당 후 이후 코드에서 참조 없음 (ruff F841 감지)
- **삭제 위험도**: safe
- **추정 삭제 가능 줄 수**: ~12줄

---

## 6. 미사용 설정 키 (config/settings/validation.yaml)

YAML 파일에 `# [xfail-sweep] ... unused` 주석이 직접 표기되어 있으나, 실제 코드에서 `_threshold()` 호출로 참조되는지 전수 확인.

| 섹션 | 라인 | 줄 수 | _threshold() 호출 여부 | 삭제 위험도 |
|------|-----|------|---------------------|-----------|
| `writing:` (L86-89) | L86-89 | 4 | 0건 -- 미사용 확인 | safe |
| `thresholds:` (L93-101) | L93-101 | 9 | 0건 -- 미사용 확인 | safe |
| `volume:` (L111-115) | L111-115 | 5 | 0건 -- constants.py VolumeSettings가 하드코드 | safe |

**참고**: `patch_mode:` (L105-107)는 `# [xfail-sweep] unused` 태그가 있으나, `constants.py` L569-570에서 `_LazyThreshold("patch_mode.rewrite_below", 50)` / `_LazyThreshold("patch_mode.patch_below", 80)`로 **실제 참조됨**. 삭제 금지.

**추정 삭제 가능 줄 수**: ~20줄 (주석 포함)

---

## 7. 미사용 테스트 fixture (tests/conftest.py)

| Fixture | 라인 | 줄 수 | 사용 테스트 수 | 삭제 위험도 |
|---------|-----|------|-------------|-----------|
| `temp_db` | L43-52 | 10 | 0건 (conftest 정의만) | safe |
| `blocking_validator_config` | L272-273 | 2 | 0건 (conftest 정의만) | safe |
| `scoring_validator_config` | L277-283 | 7 | 0건 (conftest 정의만) | safe |
| `agent_config` | L287-302 | 16 | 0건 (conftest 정의만) | safe |
| `initialized_test_db` | L346-355 | 10 | 0건 (conftest 정의만) | safe |

**부수 삭제**: `create_test_db_with_tables()` 함수 (L305-342, 38줄) -- `initialized_test_db`에서만 사용, 함께 삭제 가능.

**추정 삭제 가능 줄 수**: ~83줄 (fixture 45줄 + helper 38줄)

---

## 삭제 우선순위 권장

### Tier 1: 즉시 삭제 가능 (safe, 의존성 없음) -- ~3,200줄

1. **`modules/domain/strategies/` 디렉토리 전체** (315줄) -- 외부 참조 0건
2. **`modules/core/models.py`** (41줄) -- import 0건
3. **`modules/core/ab_testing.py`** (464줄) -- sweep30 테스트 함께 삭제
4. **`modules/core/manuscript_enhancer.py`** (788줄) -- test_v55 관련 테스트 정리
5. **`modules/core/finetuning_automation.py`** (425줄) -- tools2 테스트만 참조
6. **`modules/core/progress_manager.py`** (359줄) -- 프로덕션 import 0건
7. **미사용 conftest fixture 5건 + helper** (83줄)
8. **validation.yaml `writing`/`thresholds`/`volume` 섹션** (20줄)
9. **weaver.assign_seeds_to_arcs()** (4줄)
10. **project_manager 4 dead methods** (22줄)

### Tier 2: 주의하여 삭제 (caution, Protocol 계약 확인 필요) -- ~550줄

1. **`modules/core/semantic_cache.py`** (420줄) -- sweep38 테스트 연쇄 삭제 필요
2. **db_manager `archive_seed`/`get_active_seeds`** -- Protocol 정의에서도 제거 필요
3. **db_manager `get_all_manuscripts`/`get_all_blueprints`** -- Protocol 정의에서도 제거 필요
4. **`DBIntegrityError`/`DBTransactionError`** -- Protocol 참조 확인 필요
5. **stage4_orchestrator 구조분해 7건** -- `_ =` 패턴으로 전환 권장

### Tier 3: 점진적 정리 (74건 F841 변수) -- ~90줄

- ruff F841 74건은 기능에 영향 없으나, 코드 가독성 향상을 위해 점진적 제거 권장
- 특히 `ALLOWED_TRANSITIONS` (12줄 블록)은 미래 참조 의도가 있었으나 구현 미완으로 판단

---

## 비고

### 검사에서 제외한 항목

- **`백업의백업의백업/` 디렉토리**: 백업 디렉토리 전체가 dead code이나, 사용자 의도적 보존으로 감사 대상 제외
- **`tools2/` 디렉토리**: 개발 도구 스크립트로 프로덕션 파이프라인 외부. dead code 판단 기준 제외
- **`_ag_deep.py`, `_ag_scan.py`**: 분석 스크립트로 감사 제외
- **ruff F401 (unused import)**: 전량 통과 (0건). 이전 E-2 정리에서 해결 완료

### data_collector.py (457줄) 참고

- 프로덕션 코드에서 import 0건이나, `tools2/` 내 3개 스크립트에서 사용
- tools2가 프로덕션 외부이므로 Tier 1 삭제 후보이지만, RLHF 데이터 수집 인프라로서 향후 사용 가능성이 있어 보류 권장
