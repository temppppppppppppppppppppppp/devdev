# TF-7-M 감사 보고서 — YAML / Prompt Config 안전성

## 감사 파일 목록
- `config/settings/validation.yaml`
- `config/system.yaml`
- `config/settings.json`
- `config/models.yaml`
- `config/prompts/analyst.yaml`
- `config/prompts/arc_generator.yaml`
- `config/prompts/blueprint_generator.yaml`
- `config/prompts/chief_writer.yaml`
- `config/prompts/director.yaml`
- `config/prompts/emotion_tracker.yaml`
- `config/prompts/ensemble.yaml`
- `modules/core/prompt_loader.py`
- `modules/core/config_manager.py`
- `modules/validation/threshold_helper.py`
- `modules/validation/scoring_validator.py`
- `modules/core/stage2_validation_pipeline.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_orchestrator.py`
- `modules/domain/agents/base_agent.py`
- `modules/domain/agents/analyst_prompt_api.py`
- `modules/domain/agents/analyst_prompts.py`
- `modules/domain/agents/director_auditor.py`
- `main_a.py`

## TF-6 G 패치 validation.yaml 반영 확인 (체크리스트)

| 키 | `validation.yaml` 존재 | 코드 소비 | 런타임 동작 |
|---|---|---|---|
| `smart_retrieval.slot_max_chars_default` | X | `modules/core/stage4_interview_round.py:464` | `_threshold(..., 1500)` 기본값 fallback |
| `smart_retrieval.max_npcs_per_slot` | X | `modules/core/stage4_interview_round.py:465` | `_threshold(..., 5)` 기본값 fallback |
| `scope.min_beats_floor` | X | `modules/core/stage2_validation_pipeline.py:620` | `_threshold(..., 1)` 기본값 fallback |
| `scope.min_avg_words` | X | `modules/core/stage2_validation_pipeline.py:621` | `_threshold(..., 6)` 기본값 fallback |
| `scope.min_word_per_beat` | X | `modules/core/stage2_validation_pipeline.py:622` | `_threshold(..., 4)` 기본값 fallback |
| `scope.min_diversity` | X | `modules/core/stage2_validation_pipeline.py:623` | `_threshold(..., 0.6)` 기본값 fallback |
| `scope.max_stagnation_hits` | X | `modules/core/stage2_validation_pipeline.py:711` | `_threshold(..., 3)` 기본값 fallback |
| `scoring.sanitize_max_chars` | X | `modules/validation/scoring_validator.py:15` | `_threshold(..., 3000)` 기본값 fallback |
| `scoring.cv_optimal_low` | X | `modules/validation/scoring_validator.py:16` | `_threshold(..., 0.35)` 기본값 fallback |
| `scoring.cv_optimal_high` | X | `modules/validation/scoring_validator.py:17` | `_threshold(..., 0.55)` 기본값 fallback |
| `scoring.wuxia_martial_min` | X | `modules/validation/scoring_validator.py:18` | `_threshold(..., 3)` 기본값 fallback |
| `scoring.hunter_system_min` | X | `modules/validation/scoring_validator.py:19` | `_threshold(..., 5)` 기본값 fallback |

근거:
- `config/settings/validation.yaml:160`~`config/settings/validation.yaml:171`에 `smart_retrieval`은 있으나 세부 키가 없음.
- `config/settings/validation.yaml:30`~`config/settings/validation.yaml:51`의 `scoring`에 상기 세부 키가 없음.
- `config/settings/validation.yaml:25`~`config/settings/validation.yaml:28`의 `scope`에 상기 세부 키가 없음.
- `_threshold` fallback 규약: `modules/validation/threshold_helper.py:10`~`modules/validation/threshold_helper.py:22`.

## TF-5 L-3 / TF-6 G system.yaml 반영 확인

- `config/system.yaml:7`~`config/system.yaml:29`에는 `thinking_budget_map`, `api`, `network_retry`, `key_rotation`만 존재.
- `modules/domain/agents/base_agent.py:974`는 `retry.max_json_payload`를 읽고 기본값 `500_000`으로 fallback.
- `modules/domain/agents/base_agent.py:1153`~`modules/domain/agents/base_agent.py:1154`는 `cache.context_max_entries`, `cache.min_content_chars`를 읽고 기본값 `50`, `50000` fallback.
- `retry.director_max_attempts`는 `system.yaml`이 아니라 `validation.yaml` 경로에서 사용됨:
  - 정의: `config/settings/validation.yaml:75`~`config/settings/validation.yaml:80`
  - 소비: `modules/core/stage4_orchestrator.py:540`

## 발견 이슈 (총 3건)

### [TF-7-M-1] `validation.yaml` SSOT 선언과 달리 다수 임계값이 파일에 누락되어 코드 기본값으로만 고정됨 (MEDIUM)
**근거 파일/줄**
- `config/settings/validation.yaml:2`~`config/settings/validation.yaml:6` (YAML SSOT 및 ConfigManager 경로 명시)
- `config/settings/validation.yaml:25`~`config/settings/validation.yaml:28` (`scope` 최소 키만 존재)
- `config/settings/validation.yaml:30`~`config/settings/validation.yaml:51` (`scoring` 최소 키만 존재)
- `config/settings/validation.yaml:160`~`config/settings/validation.yaml:171` (`smart_retrieval` 일부 키만 존재)
- `modules/core/stage2_validation_pipeline.py:620`~`modules/core/stage2_validation_pipeline.py:623`, `modules/core/stage2_validation_pipeline.py:711`
- `modules/core/stage4_interview_round.py:464`~`modules/core/stage4_interview_round.py:465`
- `modules/validation/scoring_validator.py:15`~`modules/validation/scoring_validator.py:19`
- `modules/validation/threshold_helper.py:10`~`modules/validation/threshold_helper.py:22`

**문제**
- 런타임은 누락 키를 조용히 기본값으로 대체한다.
- 운영자가 `validation.yaml`만 보고 튜닝해도 실제로 반영되지 않는 항목이 존재한다.

**영향**
- 임계값 변경 통제가 “코드 기본값”에 잠겨 설정 기반 운영성이 떨어진다.
- SSOT 문서/설정과 실행값이 분리되어 장애 분석 시 혼선을 유발한다.

**Caller→Callee 계약 추적**
- Caller: `stage2_validation_pipeline`, `stage4_interview_round`, `scoring_validator`
- Callee: `_threshold` → `ConfigManager.get_guard_threshold()` → `validation.yaml`

**Bug-vs-intent 근거**
- 파일 헤더가 YAML SSOT를 명시하지만 실제 키셋이 코드 소비 키와 불일치한다.
- fallback 자체는 의도된 안전장치이나, SSOT 목표와는 충돌한다.

**권장 수정 방향**
- 누락된 12개 키를 `validation.yaml`에 명시적으로 추가.
- `ConfigManager` 로드 시 “코드 소비 키 누락” 경고를 1회 집계 출력.

### [TF-7-M-2] `settings.json.validation` 값 대부분이 실행 경로에 연결되지 않아 사실상 dead config 상태 (MEDIUM)
**근거 파일/줄**
- `config/settings.json:6`~`config/settings.json:13` (`scoring_model`, `advisory_model`, `consistency_votes` 등 선언)
- `main_a.py:1564`~`main_a.py:1567` (`validation.use_v0128`만 사용)
- `modules/domain/agents/director_auditor.py:222`~`modules/domain/agents/director_auditor.py:228` (V0128 기본 config 하드코딩)
- `modules/validation/validation_orchestrator.py:217`~`modules/validation/validation_orchestrator.py:227` (전달된 config 값 사용)

**문제**
- `settings.json`에 적힌 validation 파라미터 중 실질적으로 소비되는 것은 `use_v0128`만 확인됨.
- 실제 V0128 실행 모델/투표수는 DirectorAuditor 기본값이 우선한다.

**영향**
- 운영자가 `settings.json`을 수정해도 기대한 모델/투표 정책이 바뀌지 않을 수 있다.
- 설정 파일 신뢰성이 떨어져 운영 실수 가능성이 증가한다.

**Caller→Callee 계약 추적**
- Caller: `main_a` (settings 읽기)
- Callee: `Director.set_v0128_enabled()`만 호출
- 별도 경로: `DirectorQualityAuditor`가 `ValidationOrchestrator` config를 자체 생성

**Bug-vs-intent 근거**
- 동일 파일에 validation 상세 키가 존재하므로 운영 설정 의도를 내포하지만, 실행 경로는 해당 키들을 소비하지 않는다.

**권장 수정 방향**
- `settings.json.validation`을 `DirectorQualityAuditor._audit_with_v0128()` 기본 config로 merge.
- 또는 `settings.json`에서 dead key를 제거하고 단일 설정 소스로 이전.

### [TF-7-M-3] Analyst 프롬프트 외부화가 부분 완료 상태라 YAML/파이썬 이중 소스가 공존함 (LOW)
**근거 파일/줄**
- `config/prompts/analyst.yaml:5`, `config/prompts/analyst.yaml:29`, `config/prompts/analyst.yaml:112`, `config/prompts/analyst.yaml:188`, `config/prompts/analyst.yaml:546` (정의된 키 5개)
- `modules/domain/agents/analyst_prompt_api.py:68`~`modules/domain/agents/analyst_prompt_api.py:74` (`RECOVERY_PROMPT`, `VOLUME_STRATEGY_PROMPT` 로드 시도 후 fallback)
- `modules/domain/agents/analyst_prompts.py:611`, `modules/domain/agents/analyst_prompts.py:675` (fallback 본문 소스)

**문제**
- 일부 프롬프트는 YAML에 없고 legacy 파이썬 상수/함수로 유지된다.

**영향**
- 프롬프트 변경 지점이 분산되어 릴리즈/검증 비용이 증가한다.

**Bug-vs-intent 근거**
- `analyst.yaml` 상단 주석이 외부화 파일임을 선언하므로, 부분 외부화 상태는 목표 대비 미완결로 판단.

**권장 수정 방향**
- `RECOVERY_PROMPT`, `VOLUME_STRATEGY_PROMPT`를 `analyst.yaml`로 이관하고 fallback 제거(또는 deprecation 로그 추가).

## Risk (총 2건)

### [TF-7-M-R1] `system.yaml` 미정의 키(`retry.max_json_payload`, `cache.*`)는 모두 하드코딩 fallback으로 동작함 (MEDIUM, Risk)
**근거 파일/줄**
- `config/system.yaml:7`~`config/system.yaml:29` (해당 키 부재)
- `modules/domain/agents/base_agent.py:974` (`retry.max_json_payload`)
- `modules/domain/agents/base_agent.py:1153`~`modules/domain/agents/base_agent.py:1154` (`cache.context_max_entries`, `cache.min_content_chars`)

**Risk 판단 근거**
- 현재는 안전 fallback으로 동작하지만, 운영자가 YAML에서 조정 가능하다고 오해할 수 있다.
- 즉시 장애는 없어 Risk로 분류.

### [TF-7-M-R2] PromptLoader는 mtime 감시가 없어 프로세스 실행 중 YAML 수정이 자동 반영되지 않음 (MEDIUM, Risk)
**근거 파일/줄**
- `modules/core/prompt_loader.py:72`~`modules/core/prompt_loader.py:73` (도메인 캐시 히트 시 즉시 반환)
- `modules/core/prompt_loader.py:189`~`modules/core/prompt_loader.py:195` (수동 invalidate API만 제공)
- `main_a.py:938`~`main_a.py:941` (프로젝트 전환 시 1회 invalidate)

**Risk 판단 근거**
- 핫픽스 운영에서 “파일만 교체하면 즉시 반영” 가정이 깨질 수 있다.
- 의도된 캐시 전략일 수 있으므로 Risk로 분류.

## YAML 프롬프트 매핑 테이블 (코드 사용 O/X)

| YAML 키 | 사용 경로 | 사용 여부 |
|---|---|---|
| `chief_writer.PROMPT_TEMPLATE_OUTPUT` | `modules/domain/agents/chief_writer_prompts.py:21` | O |
| `chief_writer.COMMON_RULES_SECTION` | `modules/domain/agents/chief_writer_prompts.py:25` | O |
| `chief_writer.WRITING_GUIDELINES_SECTION` | `modules/domain/agents/chief_writer_prompts.py:29` | O |
| `chief_writer.PRIMITIVE_CONSTRAINT_FALLBACK` | `modules/domain/agents/chief_writer_prompts.py:33` | O |
| `chief_writer.MODERN_ORIGIN_SECTION` | `modules/domain/agents/chief_writer_prompts.py:37` | O |
| `chief_writer.PATCH_MODE_PROMPT` | `modules/domain/agents/chief_writer.py:729` | O |
| `arc_generator.ARC_PATCH_MODE_PROMPT` | `modules/domain/agents/four_phase_arc_generator.py:497` | O |
| `blueprint_generator.BLUEPRINT_PATCH_MODE_PROMPT` | `modules/domain/agents/three_phase_blueprint_generator.py:493` | O |
| `director.ENSEMBLE_SELECTION_PROMPT` | `modules/domain/agents/director_ensemble.py:342` | O |
| `director.MANUSCRIPT_HISTORY_CONFLICT_PROMPT` | `modules/domain/agents/director_continuity.py:388`, `modules/domain/agents/director_continuity.py:721` | O |
| `director.STRATEGIC_AUDIT_PROMPT_V30` | `modules/domain/agents/director_auditor.py:757` | O |
| `director.DIRECTOR_AUDIT_PROMPT_V30` | `modules/domain/agents/director_auditor.py:636` | O |
| `ensemble.ENSEMBLE_ARC_PROMPT` | `modules/domain/agents/arc_ensemble.py:386` | O |
| `ensemble.BLUEPRINT_GENERATION_PROMPT` | `modules/domain/agents/blueprint_ensemble.py:382` | O |
| `emotion_tracker.GENERATE_RECOMMENDATION__NEGATIVE_STREAK` | `modules/core/emotion_tracker.py:200` | O |
| `emotion_tracker.GENERATE_RECOMMENDATION__POSITIVE_STREAK` | `modules/core/emotion_tracker.py:235` | O |
| `analyst.POST_STITCH_REPAIR_PROMPT` | `modules/domain/agents/analyst_prompt_api.py:29` | O |
| `analyst.ENRICH_BLOCK_PROMPT_V30` | `modules/domain/agents/analyst_prompt_api.py:37` | O |
| `analyst.PLAN_VOLUME_PROMPT_V25` | `modules/domain/agents/analyst_prompt_api.py:41` | O |
| `analyst.PLAN_ARC_PROMPT_V25` | `modules/domain/agents/analyst_prompt_api.py:46` | O |
| `analyst.ANALYST_SELF_CRITIC_PROMPT` | `modules/domain/agents/analyst_prompt_api.py:64` | O |
| `analyst.RECOVERY_PROMPT` | `modules/domain/agents/analyst_prompt_api.py:68` (YAML 미존재) | X (legacy fallback) |
| `analyst.VOLUME_STRATEGY_PROMPT` | `modules/domain/agents/analyst_prompt_api.py:73` (YAML 미존재) | X (legacy fallback) |

## [FP] 오탐 목록

### [FP-1] `retry.director_max_attempts`가 `system.yaml`에 없어 재시도 제어가 죽었다
- **판정**: 오탐
- **수동 근거**:
  - `config/settings/validation.yaml:75`~`config/settings/validation.yaml:80`에 `retry.director_max_attempts` 존재.
  - `modules/core/stage4_orchestrator.py:540`에서 `_threshold("retry.director_max_attempts", 5)`로 실제 사용.

### [FP-2] 모델 ID가 Claude 계열로 남아 있어 현재 코드와 불일치한다
- **판정**: 오탐
- **수동 근거**:
  - `config/models.yaml:2`~`config/models.yaml:26`은 Gemini 계열 모델만 사용.
  - `modules/domain/agents/base_agent.py:44`~`modules/domain/agents/base_agent.py:49` fallback chain도 Gemini 계열.

### [FP-3] PromptLoader 파서가 현재 프롬프트 YAML 키를 파싱하지 못한다
- **판정**: 오탐
- **수동 근거**:
  - 파서 규칙: `modules/core/prompt_loader.py:87` (`^[A-Z][A-Z0-9_]+:\s*\|`)
  - 실제 키 예시: `config/prompts/director.yaml:3`, `config/prompts/ensemble.yaml:3`, `config/prompts/chief_writer.yaml:3` (규칙 충족).

### [FP-4] UTF-8 BOM 때문에 YAML 첫 키 인식이 깨진다
- **판정**: 오탐
- **수동 근거**:
  - 대상 파일 선두 바이트 확인 시 BOM(`EF BB BF`) 미검출 (`config/settings/validation.yaml`, `config/system.yaml`, `config/models.yaml`, `config/prompts/*.yaml`).

## 요약 테이블

| 분류 | 건수 | 항목 |
|---|---:|---|
| MEDIUM | 2 | `TF-7-M-1`, `TF-7-M-2` |
| LOW | 1 | `TF-7-M-3` |
| Risk | 2 | `TF-7-M-R1`, `TF-7-M-R2` |
| FP | 4 | `FP-1~4` |
