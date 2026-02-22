# Validation & Quality 모듈 2차 전수조사 보고서

**일시**: 2026-02-22
**감사자**: Claude Opus 4.6
**범위**: modules/validation/*.py + modules/domain/agents/{continuity_manuscript,director_auditor}.py
**목적**: 1차 수정 검증 + 신규 이슈 발굴

---

## 1. 1차 수정 검증 결과

### 1-A. V-P1-2: GENRE_WEIGHTS 10장르 확장 -- PASS

**파일**: `modules/validation/scoring_validator.py` L678-808

10개 장르 전량 확인:

| 장르 | 키 | 항목 수 | 특화 가중치 (>1.2) |
|------|-----|---------|-------------------|
| 무협 | wuxia | 10 | sensory_balance(1.3), reader_satisfaction(1.3) |
| 헌터 | hunter | 10 | commercial_appeal(1.3), reader_satisfaction(1.2) |
| 투자 | investment | 10 | vocabulary_diversity(1.2), character_consistency(1.2), emotion_arc(1.2), pattern_diversity(1.2) |
| 판타지 | fantasy | 10 | sensory_balance(1.2), commercial_appeal(1.2), reader_satisfaction(1.2) |
| 작곡가 | composer | 10 | prose_rhythm(1.3), emotion_arc(1.3), vocabulary_diversity(1.2), sensory_balance(1.2) |
| 요리 | cooking | 10 | sensory_balance(1.5) |
| 대체역사 | alt_history | 10 | vocabulary_diversity(1.3), character_consistency(1.3), dialogue_quality(1.2) |
| 배우 | actor | 10 | show_dont_tell(1.3), character_consistency(1.2), emotion_arc(1.2), dialogue_quality(1.2) |
| 스포츠 | sports | 10 | prose_rhythm(1.3), reader_satisfaction(1.2), sensory_balance(1.2) |
| 의학 | medical | 10 | vocabulary_diversity(1.3), character_consistency(1.2), emotion_arc(1.2), show_dont_tell(1.2) |

**판정**: 전량 10항목 x 10장르 = 100개 엔트리. 누락 없음.

### 1-B. V-P1-5: CatharsisTimer 10장르 -- PASS

**파일**: `modules/validation/catharsis_timer.py`

| 데이터 구조 | 장르 수 | 비고 |
|-------------|---------|------|
| CATHARSIS_INDICATORS | 10 + common | 각 장르 10개 키워드 |
| STRONG_CATHARSIS_WEIGHTS | 10 + common | 장르별 3-4개 강가중치 |
| FRUSTRATION_INDICATORS | 10 + common | 각 장르 7-10개 키워드 |
| get_recommended_catharsis_type() | 10 + default | 장르별 5개 추천 |

**판정**: 10장르 전량 확장 완료. 누락 없음.

### 1-C. V-P2-2: THRESHOLD_PROFILES 10장르 -- PASS

**파일**: `modules/validation/validation_orchestrator.py` L80-151 (`GENRE_THRESHOLD_PROFILES`)

10개 장르 전량 확인:

| 장르 | base_threshold | 특징적 가중치 |
|------|---------------|--------------|
| wuxia | 70 | action_weight=1.2 |
| hunter | 68 | action_weight=1.3, commercial_weight=1.2 |
| investment | 72 | dialogue_weight=1.2, emotion_weight=1.2 |
| fantasy | 69 | action_weight=1.2, commercial_weight=1.2 |
| composer | 71 | emotion_weight=1.3 |
| cooking | 70 | 균형형 |
| alt_history | 72 | dialogue_weight=1.2 |
| actor | 70 | dialogue_weight=1.3, emotion_weight=1.2 |
| sports | 69 | action_weight=1.3 |
| medical | 73 | dialogue_weight=1.2, emotion_weight=1.2 |

**판정**: 전량 확인 완료. base_threshold 분포 합리적 (68-73).

### 1-D. V-I4: 예외 세분화 -- PASS

**파일**: `modules/validation/blocking_validator.py`

- `_check_relationship_consistency()` L179-185: `(ImportError, TypeError, AttributeError)` re-raise + `(ValueError, KeyError, RuntimeError)` graceful degradation
- `_check_information_consistency()` L187-194: 동일 패턴
- `blocking_validator_consistency_checks.py` 내부:
  - `_check_relationship_consistency()` L291-295: 동일 패턴
  - `_check_information_consistency()` L362-366: 동일 패턴

**판정**: 프로그래밍 오류(Import/Type/Attribute)는 re-raise, 런타임 오류(Value/Key/Runtime)는 degraded 반환. 4곳 모두 올바르게 구현됨.

### 1-E. V-I5: try/finally 임계값 복원 -- PASS

**파일**: `modules/validation/validation_orchestrator.py`

- `validate()` L288-300: `_original_threshold` 저장 -> try 내부에서 adaptive 설정 -> finally에서 복원
- `validate_parallel_v59()` L1043-1058: 동일 패턴

**판정**: 두 경로(sync/async) 모두 try/finally 적용 완료. 예외 발생 시에도 pass_threshold 복원 보장.

---

## 2. 신규 이슈

### 2-1. [P3] ConsistencyValidator._load_guard_for_genre() 장르 커버리지 불완전

**파일**: `modules/validation/consistency_validator.py` L48-73
**심각도**: P3 (Low)
**설명**: `_load_guard_for_genre()`가 wuxia, hunter, investment만 하드코딩 분기 처리. 나머지 7개 장르(fantasy, composer, cooking, alt_history, actor, sports, medical)는 `None` 반환되어 Guard 기반 검증 전체 스킵.

그러나 `ScoringValidator._load_guard_for_genre()` (L63-73)는 `create_genre_guard()` 팩토리 함수를 사용하여 모든 장르를 올바르게 로드함.

**영향**: ConsistencyValidator에서 상태-행동 일관성(`_check_state_action_consistency`), 직위/호칭 일관성(`_check_hierarchy_consistency`), 권위 위임, 미해결 갈등, 빌런 반응 검증이 7개 장르에서 항상 `{"passed": True}`를 반환.

**권장**: ConsistencyValidator도 `create_genre_guard()` 팩토리 패턴으로 전환.

```python
# 현재 (하드코딩 3장르)
def _load_guard_for_genre(self, genre: str):
    if genre == "wuxia": ...
    elif genre == "hunter": ...
    elif genre == "investment": ...

# 권장 (팩토리 패턴, ScoringValidator와 동일)
def _load_guard_for_genre(self, genre: str):
    if not genre:
        return None
    try:
        from modules.core.genre_guards import create_genre_guard
        return create_genre_guard(genre)
    except Exception as e:
        logging.warning(f"[WARNING] Guard load failed ({genre}): {e}")
        return None
```

### 2-2. [P3] ActionSceneEvaluator 장르 키워드 3장르만 정의

**파일**: `modules/validation/action_scene_evaluator.py` L20-64
**심각도**: P3 (Low)
**설명**: `ACTION_KEYWORDS` dict에 wuxia, hunter, investment만 정의. 나머지 7개 장르에서는 wuxia 키워드로 fallback (`ACTION_KEYWORDS.get(genre, ACTION_KEYWORDS["wuxia"])`).

`ACTION_DENSITY_THRESHOLDS`도 동일하게 3장르만 정의 (L120-124).

**영향**: 스포츠 장르에서 "공격/방어/검/도" 같은 무협 키워드 기준으로 액션 씬을 감지하므로, 경기 장면이 비액션으로 분류될 수 있음. 의학 장르에서 수술 장면이 액션 씬으로 감지되지 않음.

**권장**: 최소한 sports(경기 키워드), medical(수술 키워드), actor(액션 연기 키워드) 정도 추가 권장.

### 2-3. [P3] ScoringValidator.GENRE_THRESHOLDS 4장르만 정의

**파일**: `modules/validation/scoring_validator.py` L29-34
**심각도**: P3 (Low, 실 영향 낮음)
**설명**: `GENRE_THRESHOLDS` dict에 wuxia, hunter, investment, fantasy만 정의. 나머지 6장르는 `default_pass_threshold=70` 사용.

**영향**: validation.yaml의 `scoring.genre_thresholds`에도 4장르만 명시 (L33-37). 누락 장르는 70점 기준. validation_orchestrator.py의 `GENRE_THRESHOLD_PROFILES`는 10장르 전량 정의되어 있어 적응형 임계값에는 영향 없음. 그러나 `ScoringValidator.__init__`에서 직접 참조하는 threshold는 4장르만 커버.

**실 영향**: ValidationOrchestrator가 `self.scoring.pass_threshold`를 adaptive threshold로 덮어쓰므로(`L293`, `L1047`), 실제 운영 시 ScoringValidator의 자체 threshold는 무시됨. 따라서 실 영향 무.

### 2-4. [P4] _validate_parallel_body에서 pre_llm_adjustment 누락

**파일**: `modules/validation/validation_orchestrator.py` L1060-1235
**심각도**: P4 (Cosmetic, 실 영향 미미)
**설명**: `_validate_sync_body()` (L302-615)에서는 Pre-LLM 감점(`pre_llm_adjustment`, L510-514)을 적용하지만, `_validate_parallel_body()` (L1060-1235)에서는 Pre-LLM 감점을 적용하지 않음.

```python
# _validate_sync_body L510-514 (적용됨)
pre_llm_adjustment = 0
_pre_llm = results.get("pre_llm_result")
if _pre_llm and _pre_llm.get("score_deduction", 0) > 0:
    pre_llm_adjustment = -1

# _validate_parallel_body L1202 (pre_llm_adjustment 누락)
adjusted_total = total_score + catharsis_adjustment + action_adjustment + consistency_penalty
```

**영향**: 병렬 검증 경로에서 Pre-LLM 경고가 있어도 점수에 반영되지 않음. 그러나 Pre-LLM 감점은 최대 -1점이고, `[V60.56]` 이후 PreLLMValidator는 항상 `passed=True`이므로 실 영향 미미.

### 2-5. [P4] _validate_parallel_body에서 Retrospective 검증 누락

**파일**: `modules/validation/validation_orchestrator.py`
**심각도**: P4 (Cosmetic)
**설명**: `_validate_sync_body()` L544-585에서 Retrospective Validator(장기 일관성 검증)를 실행하지만, `_validate_parallel_body()`에서는 이 단계가 완전히 누락됨.

**영향**: 병렬 검증 경로 사용 시 장기 일관성 위반(CRITICAL/HIGH/MEDIUM)이 감지되지 않음. 그러나 병렬 검증은 `validate_parallel_sync_v59()`를 통해 호출되며, asyncio 실패 시 `validate()`로 fallback하므로 대부분의 실 운영에서는 동기 경로를 거침.

### 2-6. [P3] _validate_parallel_body에서 Self-Refine 판단 누락

**파일**: `modules/validation/validation_orchestrator.py`
**심각도**: P3 (Low)
**설명**: `_validate_sync_body()` L432-452에서 Self-Refine 권장 여부를 판정하여 `refine_recommended`, `refine_reason` 플래그를 결과에 포함하지만, `_validate_parallel_body()`에서는 이 판정이 누락됨.

**영향**: 병렬 검증 경로에서 88-90점 구간이나 중요 화수(1, 25, 50...)에서도 Self-Refine 권장 플래그가 설정되지 않음.

### 2-7. [I-NEW-1] validation.yaml에 GENRE_THRESHOLD_PROFILES 미반영

**파일**: `config/settings/validation.yaml`
**심각도**: Improvement (개선 아이디어)
**설명**: `GENRE_THRESHOLD_PROFILES` (10장르 base_threshold + 4개 가중치)가 validation_orchestrator.py에 하드코딩되어 있고, validation.yaml에는 해당 프로파일이 없음. `scoring.genre_thresholds`는 4장르만 존재.

**현재 상태**: threshold_helper.py의 `_threshold()` 함수가 YAML 우선, Python 기본값 fallback 패턴이므로, YAML에 없어도 Python 기본값이 사용됨. 하지만 SSOT(Single Source of Truth) 원칙에 따르면 YAML에 선언하는 것이 바람직.

**권장**: `adaptive_threshold.genre_profiles.*` 키로 YAML 외부화 고려.

---

## 3. 반환값 흐름 정확성 분석

### 3-1. _validate_sync_body 반환값 흐름

```
validate() [L258-300]
  |-- _original_threshold 저장
  |-- try:
  |     |-- adaptive_threshold 계산/설정
  |     |-- _validate_sync_body() 호출 [L302-615]
  |         |-- PRE-LLM (TIER 0.25) -- warning만, REJECT 없음
  |         |-- CONTINUITY (TIER 0.5) -- REJECT 가능 (즉시 반환)
  |         |-- BLOCKING (TIER 1) -- REJECT 가능 (즉시 반환)
  |         |-- CONSISTENCY (TIER 1.5) -- unjustifiable 있으면 REJECT (즉시 반환)
  |         |-- SCORING (TIER 2) -- Self-Consistency 조건부
  |         |-- Self-Refine 판정 (플래그만)
  |         |-- ADVISORY (TIER 3) -- suggestions만
  |         |-- CatharsisTimer + ActionSceneEvaluator -- 점수 조정
  |         |-- Pre-LLM 감점 (-1점 캡)
  |         |-- Consistency 감점
  |         |-- Retrospective (3화+ 조건부) -- CRITICAL REJECT 가능
  |         |-- 최종 판정 (PASS/CONDITIONAL_PASS/REJECT)
  |         |-- _record_validation_history_v59()
  |         |-- return results
  |-- finally:
        |-- pass_threshold 복원
```

**판정**: 동기 경로 반환값 흐름 정확. 모든 조기 종료(REJECT) 시 필요 정보 포함됨.

### 3-2. _validate_parallel_body 반환값 흐름

```
validate_parallel_v59() [L1023-1058]
  |-- _original_threshold 저장
  |-- try:
  |     |-- adaptive_threshold 계산/설정
  |     |-- _validate_parallel_body() 호출 [L1060-1235]
  |         |-- Stage 1 (순차): PRE-LLM -> CONTINUITY -> BLOCKING
  |         |   (각 단계 REJECT 가능, _build_reject_result_v59()로 즉시 반환)
  |         |-- Stage 2 (병렬): CONSISTENCY + SCORING + ADVISORY
  |         |   (ThreadPoolExecutor, return_exceptions=True)
  |         |   (예외 발생 시 None -> 안전 폴백 dict 할당)
  |         |-- CONSISTENCY unjustifiable -> REJECT (즉시 반환)
  |         |-- Stage 3: CatharsisTimer + ActionSceneEvaluator
  |         |-- 점수 조정 (pre_llm_adjustment 누락 -- 2-4)
  |         |-- 최종 판정
  |         |-- _record_validation_history_v59()
  |         |-- return results
  |-- finally:
        |-- pass_threshold 복원
```

**주요 차이점**:
1. Pre-LLM 감점 누락 (2-4)
2. Retrospective 검증 누락 (2-5)
3. Self-Refine 플래그 누락 (2-6)
4. Pre-LLM REJECT 경로 존재 (`L1069-1072`): `_validate_parallel_body`에서는 `not pre_llm_result["passed"]` 시 REJECT를 반환하지만, 현재 PreLLMValidator는 항상 `passed=True`이므로 dead code임. 일관성 관점에서 sync body에는 이 분기가 없으므로 비대칭.

### 3-3. Validation -> Director 판정 -> 재작성 루프 연계

**파일**: `modules/domain/agents/director_auditor.py`

```
DirectorQualityAuditor.audit_manuscript() [L322-675]
  |-- Python 사전 검증 (_pre_llm_warnings 수집)
  |    |-- 죽은 NPC -> LLM 경고 전달
  |    |-- 장르 위반 -> LLM 경고 전달
  |    |-- 주인공 설정 위반 -> LLM 경고 전달
  |-- 원고 역사 충돌 검사 -> CONFLICT 시 즉시 REJECT
  |-- Entity 일관성 검증 -> REJECT 시 즉시 반환
  |-- 캐릭터 논리 검증 (assess_character_logic)
  |    |-- CRITICAL 1개 또는 MAJOR 2개+ -> REJECT
  |-- V0128 경로 (use_v0128=True):
  |    |-- _audit_with_v0128() -> audit_manuscript_v0128()
  |    |    |-- ValidationOrchestrator.validate() 호출
  |    |    |-- PASS/CONDITIONAL_PASS -> "PASS", REJECT -> "REJECT"
  |-- Legacy 경로 (use_v0128=False):
       |-- 분량 체크, RepetitionGuard, LLM 프롬프트
```

**연계 정확성**:
- `audit_manuscript_v0128()` L246-265: `validate()` 결과를 래핑하여 Director의 기존 인터페이스(`decision`, `score`, `reason`, `feedback`)로 변환. `CONDITIONAL_PASS`를 `PASS`로 매핑하는 것은 의도적 설계 (Director가 "PASS인가 아닌가"만 판단).
- V0128 경로에서 `scoring_threshold: 70` (L225)은 `validation.yaml`의 `scoring.default_pass_threshold: 70`과 일치 (`[TF-I06]` 주석 확인).
- 재작성 루프는 상위 레벨(main_a.py Stage 4)에서 `decision == "REJECT"` 시 Writer에게 피드백과 함께 재작성 요청. 이 연계는 정상.

---

## 4. 10개 장르 가중치 합리성 분석

### 4-1. GENRE_WEIGHTS 가중치 합계 비교

각 장르의 가중치 합계(10개 항목)를 비교하여 장르 간 편향 확인:

| 장르 | 가중치 합계 | 평균 | 최대 항목 |
|------|-----------|------|----------|
| wuxia | 10.6 | 1.06 | reader_satisfaction=1.3, sensory_balance=1.3 |
| hunter | 10.7 | 1.07 | commercial_appeal=1.3 |
| investment | 10.6 | 1.06 | 4개 항목 1.2 |
| fantasy | 10.8 | 1.08 | 3개 항목 1.2 |
| composer | 10.9 | 1.09 | prose_rhythm=1.3, emotion_arc=1.3 |
| cooking | 10.7 | 1.07 | sensory_balance=1.5 |
| alt_history | 10.9 | 1.09 | vocabulary_diversity=1.3, character_consistency=1.3 |
| actor | 10.9 | 1.09 | show_dont_tell=1.3 |
| sports | 10.9 | 1.09 | prose_rhythm=1.3 |
| medical | 10.9 | 1.09 | vocabulary_diversity=1.3 |

**판정**: 가중치 합계 범위 10.6~10.9로 장르 간 편차 3% 이내. `[TF-C02]` 장르 가중치 영향력 +-1점 캡이 적용되므로 실 영향 무시할 수 있는 수준. **합리적**.

### 4-2. GENRE_THRESHOLD_PROFILES base_threshold 분포

| base_threshold | 장르 |
|---------------|------|
| 68 | hunter |
| 69 | fantasy, sports |
| 70 | wuxia, cooking, actor |
| 71 | composer |
| 72 | investment, alt_history |
| 73 | medical |

**판정**: 액션 중심 장르(hunter, sports, fantasy)가 낮고, 전문성/논리 중심 장르(medical, investment, alt_history)가 높음. 직관적으로 합리적. medical의 73은 의학 용어 정확성 요구 반영.

### 4-3. CatharsisTimer 키워드 품질

몇 가지 주목할 점:
- `sports` FRUSTRATION_INDICATORS에 "도핑 의혹"이 포함되어 있어, 의도적 서사 요소(갈등 유발)도 좌절로 카운트됨. 서사적 긴장감과 좌절의 구분이 명확하지 않으나, 독자 체감 기준으로는 적절.
- `medical` CATHARSIS_INDICATORS에 "펠로우 합격"이 있어, 한국 의학 체계 반영 확인.
- 모든 장르의 키워드 수: 카타르시스 10개, 좌절 7-10개로 균형.

---

## 5. 추가 관찰 사항

### 5-1. [OBS-1] PreLLMValidator 내부 모순: 클래스 독스트링 vs 코드

**파일**: `modules/validation/pre_llm_validator.py`

- 독스트링 L28: "원고 검증 전 9가지 Python 기반 검사"
- 모듈 독스트링 L1-19: "10가지 Python 기반 검사" (V70 POV 추가)
- `validate()` L138: `"check_count": 10`

실제 검사 수는 10개(V70 POV 포함)이므로 클래스 독스트링만 구버전. 기능에 영향 없음.

### 5-2. [OBS-2] blocking_validator_consistency_checks.py의 `import re` 중복

**파일**: `modules/validation/blocking_validator_consistency_checks.py`

- L6: `import re` (모듈 레벨)
- L71: `import re` (`_check_physical_capability` 내부)
- L185: `import re` (`_check_authority_exercise` 내부)

함수 내부 `import re`는 불필요한 중복. 모듈 레벨 import가 이미 존재하므로 동작에는 영향 없으나, 코드 위생 관점에서 정리 대상.

### 5-3. [OBS-3] validate_parallel_v59 vs validate의 PRE-LLM 처리 비대칭

**파일**: `modules/validation/validation_orchestrator.py`

| 항목 | validate (sync) | validate_parallel_v59 (async) |
|------|----------------|------------------------------|
| PRE-LLM REJECT | 없음 (항상 passed=True) | 있음 (L1069-1072, dead code) |
| PRE-LLM 감점 | -1점 (L510-514) | 없음 |
| Self-Refine 판정 | 있음 (L432-452) | 없음 |
| Retrospective | 있음 (L544-585) | 없음 |

sync 경로에 있는 기능이 async 경로에 누락된 3건. 반면 async 경로에만 있는 PRE-LLM REJECT 분기는 dead code. 양쪽의 동작이 비대칭이지만, async 경로는 실질적으로 sync fallback으로 처리되는 경우가 많아 실 영향은 제한적.

### 5-4. [OBS-4] _get_fallback_constitution()의 3장르 한정

**파일**: `modules/validation/validation_orchestrator.py` L911-959

`_get_fallback_constitution()`의 `genre_amendments`가 wuxia, hunter, investment 3장르만 정의. 나머지 7장르는 base constitution만 적용.

**영향**: QualityConstitution 모듈이 로드 실패할 때만 사용되는 fallback이므로 실 영향 낮음. 하지만 장기적으로 10장르 확장 고려.

### 5-5. [OBS-5] _get_genre_item_note()의 3장르 한정

**파일**: `modules/validation/scoring_validator.py` L909-933

`_get_genre_item_note()`의 notes dict에 wuxia, hunter, investment만 정의. 나머지 7장르에서는 빈 문자열 반환 (`notes.get(genre, {}).get(item_name, "")`).

**영향**: 피드백 품질 저하(장르 특화 설명 없음). 기능 장애는 아님.

### 5-6. [OBS-6] _get_genre_specific_feedback()의 3장르 한정

**파일**: `modules/validation/scoring_validator.py` L1043-1084

`_get_genre_specific_feedback()`에서 wuxia, hunter, investment만 분기 처리. 나머지 7장르에서는 빈 리스트 반환.

**영향**: 장르 특화 피드백 부재. OBS-5와 동일 패턴.

---

## 6. 종합 평가

### 6-1. 1차 수정 검증 결과 요약

| 항목 | 상태 | 비고 |
|------|------|------|
| V-P1-2 (GENRE_WEIGHTS 10장르) | PASS | 100개 엔트리 전량 확인 |
| V-P1-5 (CatharsisTimer 10장르) | PASS | 4개 구조 전량 확인 |
| V-P2-2 (THRESHOLD_PROFILES 10장르) | PASS | base_threshold 분포 합리적 |
| V-I4 (예외 세분화) | PASS | 4곳 모두 올바른 패턴 |
| V-I5 (try/finally) | PASS | sync/async 양 경로 확인 |

**결론**: 1차 감사에서 발견된 P1/P2/개선 아이디어 수정 사항 전량 정상 반영 확인.

### 6-2. 신규 발견 이슈 요약

| ID | 심각도 | 파일 | 설명 |
|----|--------|------|------|
| 2-1 | P3 | consistency_validator.py | Guard 로드 3장르 한정 (팩토리 미사용) |
| 2-2 | P3 | action_scene_evaluator.py | 액션 키워드 3장르만 정의 |
| 2-3 | P3 | scoring_validator.py | GENRE_THRESHOLDS 4장르 (실 영향 무) |
| 2-4 | P4 | validation_orchestrator.py | parallel body pre_llm_adjustment 누락 |
| 2-5 | P4 | validation_orchestrator.py | parallel body Retrospective 누락 |
| 2-6 | P3 | validation_orchestrator.py | parallel body Self-Refine 누락 |
| 2-7 | Idea | validation.yaml | GENRE_THRESHOLD_PROFILES YAML 미외부화 |

### 6-3. 관찰 사항 요약 (OBS)

| ID | 파일 | 설명 |
|----|------|------|
| OBS-1 | pre_llm_validator.py | 독스트링 "9가지" (실제 10가지) |
| OBS-2 | blocking_validator_consistency_checks.py | import re 중복 3곳 |
| OBS-3 | validation_orchestrator.py | sync/async 경로 기능 비대칭 |
| OBS-4 | validation_orchestrator.py | fallback constitution 3장르 한정 |
| OBS-5 | scoring_validator.py | genre_item_note 3장르 한정 |
| OBS-6 | scoring_validator.py | genre_specific_feedback 3장르 한정 |

### 6-4. 전체 판정

**안정성**: 높음. 1차 수정 전량 정상 반영. 신규 P1/P2 없음.

**커버리지 갭**: 10장르 확장은 핵심 구조(GENRE_WEIGHTS, CatharsisTimer, THRESHOLD_PROFILES)에서 완료되었으나, 보조 구조(ConsistencyValidator Guard 로드, ActionSceneEvaluator 키워드, fallback constitution, genre-specific feedback)에서 3-4장르 한정 구현이 잔존. 이들은 모두 P3 수준으로 기능 장애를 유발하지 않으나, 장기적 품질 향상을 위해 점진적 확장 권장.

**병렬 경로 비대칭**: `_validate_parallel_body`에서 3개 기능(pre_llm 감점, Retrospective, Self-Refine)이 누락된 것은 설계 의도인지 구현 누락인지 확인 필요. 실 운영에서 async 경로는 sync fallback으로 처리되는 경우가 많아 즉각적 위험은 낮지만, 향후 async 경로가 기본이 되면 문제 될 수 있음.

---

*End of Report*
