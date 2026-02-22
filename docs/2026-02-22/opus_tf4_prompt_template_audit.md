# Opus TF4: Prompt Template 전면 감사 보고서

> 작성일: 2026-02-22
> 범위: config/prompts/*.yaml 40개 + modules/ 내 Python 하드코딩 프롬프트 전수 조사

---

## 1. YAML 프롬프트 인벤토리

### 1-1. 전체 요약

| 항목 | 수치 |
|------|------|
| YAML 파일 수 | **40개** |
| 정의된 키 수 | **81개** |
| 총 줄 수 | **4,156줄** |
| 총 문자 수 | ~108,945자 (키 값 합계) |

### 1-2. 파일별 상세

| 파일명 | 키 수 | 줄 수 |
|--------|-------|-------|
| advisory_validator.yaml | 1 | 14 |
| agent_intelligence.yaml | 1 | 13 |
| analyst.yaml | 5 | 591 |
| arc_corrector.yaml | 1 | 38 |
| arc_critic.yaml | 1 | 103 |
| arc_generator.yaml | 1 | 20 |
| bible_extractor.yaml | 6 | 118 |
| block_enricher.yaml | 5 | 227 |
| blueprint_generator.yaml | 1 | 20 |
| chief_writer.yaml | 6 | 73 |
| consensus_validator.yaml | 1 | 45 |
| continuity_arc.yaml | 2 | 181 |
| continuity_blueprint.yaml | 1 | 119 |
| continuity_manuscript.yaml | 1 | 125 |
| critic.yaml | 2 | 92 |
| director.yaml | 4 | 458 |
| director_auditor.yaml | 1 | 51 |
| director_continuity.yaml | 2 | 74 |
| director_ensemble.yaml | 2 | 59 |
| emotion_tracker.yaml | 2* | 58 |
| ensemble.yaml | 2 | 339 |
| genre_stage.yaml | 1 | 29 |
| manager.yaml | 1 | 106 |
| narrative_diversity.yaml | 1 | 26 |
| narrative_structure_analyzer.yaml | 1 | 38 |
| preflight_checker.yaml | 1 | 93 |
| quality_constitution.yaml | 4 | 262 |
| reference_anchor.yaml | 1 | 42 |
| repetition_guard.yaml | 1 | 20 |
| reverse_expander.yaml | 4 | 85 |
| scoring_validator.yaml | 1 | 51 |
| self_reflection.yaml | 1 | 18 |
| stage4_orchestrator.yaml | 1 | 18 |
| state_extractor.yaml | 1 | 122 |
| state_locked_arc_generator.yaml | 4 | 132 |
| story_expander.yaml | 5 | 108 |
| style_extractor.yaml | 2 | 44 |
| unified_arc_validator.yaml | 1 | 64 |
| weaver.yaml | 1 | 24 |
| writer.yaml | 1 | 56 |

> `*` emotion_tracker.yaml에서 `GENERATE_RECOMMENDATION__RECOMMENDATION` 키가 **2회 중복 정의**됨 (뒤의 것이 앞을 덮어씀). 아래 섹션 8 참조.

---

## 2. 미사용 YAML 키

PromptLoader.load() / .get_raw() 호출을 전수 스캔한 결과, **60개 YAML 키가 코드에서 참조되지 않는다.** 이들은 YAML에 정의되어 있으나 실제로는 Python 인라인 상수가 `.format()`으로 직접 치환되어 사용된다.

### 2-1. 미사용 이유: Inline Fallback 패턴 (17개 키)

다음 에이전트들은 YAML에 동일 키가 존재하나, 코드가 PromptLoader를 거치지 않고 **모듈 레벨 상수를 직접 `.format()` 호출**하는 패턴이다. YAML은 "작성만 되었고 연결되지 않은" 상태이다.

| YAML 도메인/키 | Python 소스 | 상태 |
|----------------|-------------|------|
| `arc_corrector/CORRECTION_PROMPT` | `arc_corrector.py:43` | 인라인 직접 사용 |
| `arc_critic/ARC_CRITIQUE_PROMPT` | `arc_critic.py:20` | 인라인 직접 사용 |
| `block_enricher/BLOCK_ENRICHMENT_PROMPT` | `block_enricher.py:20` | 인라인 직접 사용 |
| `block_enricher/ENRICHMENT_VALIDATION_PROMPT` | `block_enricher.py:99` | 인라인 직접 사용 |
| `block_enricher/DIRECTOR_BLOCK_AUDIT_PROMPT` | `block_enricher.py:132` | 인라인 직접 사용 |
| `block_enricher/CHECK_CAUSAL_ERRORS__PROMPT` | `block_enricher.py` | YAML 전용 (미연결) |
| `block_enricher/RE_ENRICH_WITH_CAUSAL_FIX__PROMPT` | `block_enricher.py` | YAML 전용 (미연결) |
| `consensus_validator/CONSENSUS_VALIDATION_PROMPT` | `consensus_validator.py:298` | 인라인 직접 사용 |
| `continuity_arc/ARC_CONTINUITY_INSPECTION_PROMPT` | `continuity_arc.py:362` | 인라인 직접 사용 |
| `continuity_arc/JOINT_DOCS_EXTRACTION_PROMPT` | `continuity_arc.py:532` | 인라인 직접 사용 |
| `continuity_blueprint/CONTINUITY_INSPECTION_PROMPT` | `continuity_blueprint.py:221` | 인라인 직접 사용 |
| `continuity_manuscript/MANUSCRIPT_CONTINUITY_PROMPT` | `continuity_manuscript.py:276` | 인라인 직접 사용 |
| `manager/UPDATE_STATE_PROMPT_V25` | `manager.py` | 인라인 직접 사용 |
| `preflight_checker/PREFLIGHT_ANALYSIS_PROMPT` | `preflight_checker.py:147` | 인라인 직접 사용 |
| `state_extractor/STATE_EXTRACTION_PROMPT` | `state_extractor.py:233` | 인라인 직접 사용 |
| `unified_arc_validator/UNIFIED_VALIDATION_PROMPT` | `unified_arc_validator.py:538` | 인라인 직접 사용 |
| `state_locked_arc_generator/*` (3키) | `state_locked_arc_generator.py` | 인라인 직접 사용 |

### 2-2. 미사용 이유: 에이전트 내부에서 참조 없음 (43개 키)

다음 YAML 키는 PromptLoader.load()로도 호출되지 않고, 동명의 인라인 상수도 연결되지 않았다. 대부분 YAML 외부화 작업(V70) 때 YAML에 복사만 해두고 전환 코드를 작성하지 않은 것으로 보인다.

| 도메인 | 미사용 키 |
|--------|-----------|
| advisory_validator | `SUGGEST_EXPRESSION_IMPROVEMENTS__PROMPT` |
| agent_intelligence | `INIT_EXEMPLARS__CONTENT` |
| bible_extractor | 6개 전부 (`EXTRACT_BASIC_INFO__PROMPT` 외 5개) |
| critic | `GET_LLM_CRITIQUE__PROMPT`, `DEEP_REVIEW_PROMPT` |
| director_auditor | `ASSESS_CHARACTER_LOGIC__PROMPT` |
| director_continuity | `VALIDATE_ENTITY_CONSISTENCY__PROMPT`, `CHECK_MANUSCRIPT_HISTORY_WITH_CACHE__PROMPT` |
| director_ensemble | `QUICK_JUDGE_SINGLE__PROMPT` |
| emotion_tracker | `GENERATE_RECOMMENDATION__RECOMMENDATION` |
| genre_stage | `STAGE3_MEDICAL` |
| narrative_diversity | `GET_ARCHITECT_INJECTION__INJECTION` |
| narrative_structure_analyzer | `NARRATIVE_EXTRACTION_PROMPT` |
| quality_constitution | 4개 전부 (`QUALITY_CONSTITUTION`, `WUXIA_AMENDMENTS` 등) |
| reference_anchor | `EXTRACT_ANCHORS_FROM_MANUSCRIPT__PROMPT` |
| repetition_guard | `GENERATE_CORRECTION_PROMPT__PROMPT` |
| reverse_expander | 4개 전부 |
| scoring_validator | `CALCULATE_LLM_SCORES__PROMPT` |
| self_reflection | `IMPROVEMENT_PROMPT` |
| stage4_orchestrator | `EXTRACT_CHAIN_LINK__PROMPT` |
| story_expander | 5개 전부 |
| style_extractor | 2개 전부 |
| weaver | `GENERATE_ARC_DRIVE__DYNAMIC_PROMPT` |
| writer | `WRITE_V20_MANUSCRIPT__DYNAMIC_PROMPT` |

### 2-3. YAML에 없으나 코드에서 참조되는 키 (2개)

| 도메인/키 | 참조 위치 | 폴백 처리 |
|-----------|-----------|-----------|
| `analyst/RECOVERY_PROMPT` | `analyst_prompt_api.py:68` | legacy `analyst_prompts.get_recovery_prompt()` 폴백 |
| `analyst/VOLUME_STRATEGY_PROMPT` | `analyst_prompt_api.py:73` | legacy `analyst_prompts.get_volume_strategy_prompt()` 폴백 |

이 2개는 PromptLoader.load()를 호출하나 YAML에 키가 없어 항상 None이 반환되고, 인라인 폴백 함수가 실행된다.

---

## 3. 하드코딩 프롬프트 (YAML 외부화 미완료)

코드베이스 내에서 **216개의 대형 프롬프트 문자열**(300자 이상)이 발견되었다. 이 중 YAML 외부화가 필요한 주요 항목은 다음과 같다.

### 3-1. 대형 하드코딩 프롬프트 Top 15

| 크기 | 파일 | 상수/함수명 | 외부화 가능 |
|------|------|-------------|-------------|
| 12,310자 | `analyst_prompts.py:198` | `PLAN_ARC_PROMPT_V25` | YAML에 동일본 존재 (이원화) |
| 5,312자 | `director_prompts.py:285` | `DIRECTOR_AUDIT_PROMPT_V30` | YAML에 동일본 존재 (이원화) |
| 4,841자 | `quality_constitution.py:10` | `QUALITY_CONSTITUTION` | YAML에 동일본 존재 (이원화) |
| 4,275자 | `continuity_arc.py:17` | `ARC_CONTINUITY_INSPECTION_PROMPT` | YAML에 동일본 존재 (이원화) |
| 3,795자 | `director_prompts.py:10` | `ENSEMBLE_SELECTION_PROMPT` | YAML에 동일본 존재 (이원화) |
| 3,649자 | `manager.py:9` | `UPDATE_STATE_PROMPT_V25` | YAML에 동일본 존재 (이원화) |
| 3,372자 | `continuity_blueprint.py:16` | `CONTINUITY_INSPECTION_PROMPT` | YAML에 동일본 존재 (이원화) |
| 3,355자 | `continuity_manuscript.py:17` | `MANUSCRIPT_CONTINUITY_PROMPT` | YAML에 동일본 존재 (이원화) |
| 3,181자 | `state_extractor.py:57` | `STATE_EXTRACTION_PROMPT` | YAML에 동일본 존재 (이원화) |
| 2,909자 | `analyst_prompts.py:613` | `get_recovery_prompt()` | YAML 미존재, 외부화 필요 |
| 2,587자 | `preflight_checker.py:21` | `PREFLIGHT_ANALYSIS_PROMPT` | YAML에 동일본 존재 (이원화) |
| 2,581자 | `director_prompts.py:206` | `STRATEGIC_AUDIT_PROMPT_V30` | YAML에 동일본 존재 (이원화) |
| 2,540자 | `analyst_prompts.py:33` | `ENRICH_BLOCK_PROMPT_V30` | YAML에 동일본 존재 (이원화) |
| 2,313자 | `arc_critic.py:20` | `ARC_CRITIQUE_PROMPT` | YAML에 동일본 존재 (이원화) |
| 2,247자 | `analyst_prompts.py:119` | `PLAN_VOLUME_PROMPT_V25` | YAML에 동일본 존재 (이원화) |

### 3-2. f-string 생성 프롬프트 (외부화 어려움)

다음은 **f-string으로 동적 조립**되어 YAML 외부화가 어려운 프롬프트이다.

| 크기 | 파일 | 함수명 | 비고 |
|------|------|--------|------|
| 1,893자 | `writer.py:162` | `write_v20_manuscript` 내부 | 복수 변수 조합, f-string |
| 1,618자 | `scoring_validator.py:188` | 인라인 | constitution + 원고를 f-string 조합 |
| 1,512자 | `wuxia_guard.py:224` | `get_v20_purism_prompt()` | 장르별 Guard, f-string 필수 (FORBIDDEN_TERMS 동적) |
| 1,451자 | `tree_of_thoughts.py:594` | ToT Arc Generator | approach별 동적 조합 |
| 1,409자 | `director_continuity.py:71` | Entity 검증 | f-string, validate 맥락 주입 |
| 1,305자 | `constraint_compiler.py:370` | 제약 프롬프트 | 동적 조건별 생성 |
| 1,265자 | `director_auditor.py:124` | 캐릭터 논리 감사 | f-string 맥락 조합 |
| 1,243자 | `chief_writer_prompts.py:75` | `build_chief_writer_main_prompt()` | 18개 매개변수의 대형 f-string 템플릿 |
| 1,238자 | `analyst_prompts.py:705` | `get_surgery_prompt()` | f-string, 4개 매개변수 |
| ~933자 | `stage2_optimizer.py:117` | 최적화 프롬프트 | f-string |

### 3-3. 장르 Guard 내 하드코딩 프롬프트 (10개 장르)

모든 장르 Guard는 `get_v20_purism_prompt()`에서 f-string으로 프롬프트를 생성한다. `FORBIDDEN_TERMS`, `MANDATORY_CONCEPTS` 등 동적 리스트를 포함하므로 단순 YAML 외부화가 어렵다.

| Guard | 파일 | 예상 크기 |
|-------|------|-----------|
| WuxiaGuard | `wuxia_guard.py:222` | ~1,512자 |
| HunterGuard | `hunter_guard.py:208` | ~700자 |
| InvestmentGuard | `investment_guard.py:192` | ~900자 |
| ComposerGuard | `composer_guard.py:206` | ~700자 |
| CookingGuard | `cooking_guard.py:194` | ~700자 |
| AltHistoryGuard | `alt_history_guard.py:226` | ~800자 |
| ActorGuard | `actor_guard.py:192` | ~700자 |
| SportsGuard | `sports_guard.py:185` | ~700자 |
| MedicalGuard | `medical_guard.py:188` | ~700자 |
| FantasyGuard | `fantasy_guard.py:150` | ~500자 |

---

## 4. 장르별 프롬프트 커버리지

### 4-1. 장르 Guard 프롬프트 (get_v20_purism_prompt) -- Stage 2/4에 주입

모든 10개 장르가 `get_v20_purism_prompt()`를 구현하고 있으며, Stage 2 Arc 생성(`analyst.py`)과 Stage 4 원고 생성(`chief_writer.py`)에서 `{genre_prompt}` 슬롯에 주입된다.

| 장르 | Guard 파일 | purism 프롬프트 | 비고 |
|------|-----------|-----------------|------|
| 무협 (wuxia) | wuxia_guard.py | 있음 | 가장 상세 (7조항+) |
| 헌터 (hunter) | hunter_guard.py | 있음 | 8조항 |
| 투자 (investment) | investment_guard.py | 있음 | 9조항 + 체크리스트 |
| 작곡가 (composer) | composer_guard.py | 있음 | 8조항 |
| 요리 (cooking) | cooking_guard.py | 있음 | 8조항 |
| 대체역사 (alt_history) | alt_history_guard.py | 있음 | 8조항 |
| 배우 (actor) | actor_guard.py | 있음 | 8조항 |
| 스포츠 (sports) | sports_guard.py | 있음 | 8조항 |
| 의학 (medical) | medical_guard.py | 있음 | 8조항 |
| 판타지 (fantasy) | fantasy_guard.py | 있음 | 간결 (약 500자) |

### 4-2. genre_stage.yaml -- Stage 3 Blueprint 특화 프롬프트

**현재 genre_stage.yaml에는 `STAGE3_MEDICAL` 1개만 존재**하며, 코드에서 **전혀 참조되지 않는다.**

| 장르 | Stage 2 프롬프트 | Stage 3 프롬프트 | YAML 정의 |
|------|-----------------|-----------------|-----------|
| 무협 | Guard 경유 | 없음 | 없음 |
| 헌터 | Guard 경유 | 없음 | 없음 |
| 투자 | Guard 경유 | 없음 | 없음 |
| 작곡가 | Guard 경유 | 없음 | 없음 |
| 요리 | Guard 경유 | 없음 | 없음 |
| 대체역사 | Guard 경유 | 없음 | 없음 |
| 배우 | Guard 경유 | 없음 | 없음 |
| 스포츠 | Guard 경유 | 없음 | 없음 |
| 의학 | Guard 경유 | 없음 | STAGE3_MEDICAL (미참조) |
| 판타지 | Guard 경유 | 없음 | 없음 |

**결론**: Stage 3 Blueprint 생성에서 장르별 특화 프롬프트가 주입되는 경로가 없다. `genre_stage.yaml`의 `STAGE3_MEDICAL`은 작성만 되었고 연결되지 않았다. Blueprint 생성(`blueprint_ensemble.py`)은 `ensemble.yaml`의 범용 프롬프트만 사용한다.

---

## 5. Placeholder 미치환 위험

### 5-1. SafeDict 보호 경로 (안전)

PromptLoader.load()는 내부에서 `SafeDict`를 사용하므로, 누락된 변수는 `{variable_name}` 형태 그대로 남지만 KeyError는 발생하지 않는다. 다음 경로는 안전하다:
- `analyst_prompt_api.py` -- PromptLoader.load() + SafeDict 이중 보호
- `chief_writer_prompts.py` -- PromptLoader.load() 경유
- `arc_ensemble.py`, `blueprint_ensemble.py` -- PromptLoader.load() + `_escape_braces()` 전처리
- `director_auditor.py`, `director_ensemble.py`, `director_continuity.py` -- PromptLoader.load() 경유

### 5-2. `.format()` 직접 사용 경로 (위험)

다음 40개 위치에서 인라인 상수를 `.format()` (SafeDict 미사용)으로 치환한다. **누락된 키가 있으면 `KeyError` 크래시가 발생**한다.

**높은 위험** (대형 프롬프트, 외부 데이터 의존):

| 파일 | 라인 | 상수명 | 위험도 |
|------|------|--------|--------|
| `analyst.py:1085,1101` | `.format()` | template 동적 | **HIGH** -- LLM 응답 내 `{}`가 오면 KeyError |
| `arc_corrector.py:252,301,383` | `.format()` | `CORRECTION_PROMPT` | MEDIUM |
| `arc_critic.py:150` | `.format()` | `ARC_CRITIQUE_PROMPT` | MEDIUM |
| `block_enricher.py:322,419,461` | `.format()` | 3개 상수 | MEDIUM |
| `continuity_arc.py:362,532` | `.format()` | 2개 상수 | MEDIUM |
| `continuity_blueprint.py:221` | `.format()` | `CONTINUITY_INSPECTION_PROMPT` | MEDIUM |
| `continuity_manuscript.py:276` | `.format()` | `MANUSCRIPT_CONTINUITY_PROMPT` | MEDIUM |
| `state_extractor.py:233,787` | `.format()` | 2개 상수 | MEDIUM |
| `state_locked_arc_generator.py:367,398,437` | `.format()` | 3개 상수 | MEDIUM |

**경감 요인**: 대부분의 `.format()` 호출에서 필요한 키를 모두 명시적으로 전달하므로, 정상 경로에서는 문제가 없다. 그러나 LLM 응답이나 사용자 입력에 `{}`가 포함된 경우 크래시 가능성이 있다.

### 5-3. 이스케이프 방어 현황

`base_agent.py:779`의 `_escape_braces()` 메서드가 중괄호를 이중화(`{{`, `}}`)하여 `.format()` 안전성을 확보한다. 대부분의 Stage 2/4 오케스트레이터와 Director 계열 에이전트에서 사용 중이다.

**미방어 에이전트** (직접 `.format()` 사용, `_escape_braces` 미호출):
- `arc_corrector.py`
- `block_enricher.py`
- `consensus_validator.py`
- `narrative_structure_analyzer.py`
- `self_reflection.py` (단, V70에서 수동 이스케이프 추가됨)

---

## 6. 프롬프트 일관성

### 6-1. 역할(Role) 정의 -- 47개 발견

모든 역할 정의는 YAML과 Python 인라인에서 **동일한 문자열**로 작성되어 있어 불일치는 없다. 이는 YAML이 인라인 상수의 "복사본"이기 때문이다.

### 6-2. 유사 역할의 차별화

| 역할 A | 역할 B | 차이점 |
|--------|--------|--------|
| "웹소설 1타 편집장 (Chief Director)" | "웹소설 유료 연재 시장의 1타 편집장 (Pacing & Volume Specialist)" | 같은 Director 에이전트에서 다른 프롬프트에 사용. 전자는 앙상블 선택용, 후자는 원고 심사용. 의도적 차별화. |
| "원고 연속성 검증 전문가 (Manuscript Continuity Inspector)" | "원고 연속성 전문가 (Manuscript Continuity Expert)" | 전자는 `continuity_manuscript.yaml`, 후자는 `director.yaml`. 기능 중복 가능성 있음. |
| "서사 상태 추출 전문가 (State Extraction Specialist)" | "독자 만족도 분석 전문가" | 같은 `state_extractor.py` 내 다른 기능. 의도적 분리. |

### 6-3. 인라인-YAML 이원화 불일치 위험

현재 **17개 프롬프트**가 Python 인라인 상수와 YAML에 동일 키로 존재하나, **코드는 인라인만 사용**한다. 이 상태에서 YAML 내용을 수정해도 시스템에 반영되지 않아, 관리자가 "YAML을 수정했는데 왜 안 바뀌지?" 혼란에 빠질 수 있다.

---

## 7. 프롬프트 길이 분포

### 7-1. 통계 (YAML 81개 키 기준)

| 지표 | 값 |
|------|-----|
| 최소 | 105자 |
| 최대 | 12,280자 |
| 평균 | 1,345자 |
| 중앙값 | 588자 |

### 7-2. 구간 분포

| 구간 | 키 수 |
|------|-------|
| < 500자 | 37개 (46%) |
| 500자 ~ 1,000자 | 16개 (20%) |
| 1,000자 ~ 3,000자 | 15개 (18%) |
| 3,000자 ~ 5,000자 | 9개 (11%) |
| 5,000자 이상 | 3개 (4%) |

### 7-3. Top 10 대형 프롬프트

| 순위 | 문자 수 | 도메인/키 |
|------|---------|-----------|
| 1 | **12,280자** | `analyst/PLAN_ARC_PROMPT_V25` |
| 2 | **7,929자** | `ensemble/ENSEMBLE_ARC_PROMPT` |
| 3 | **5,567자** | `director/DIRECTOR_AUDIT_PROMPT_V30` |
| 4 | **4,810자** | `quality_constitution/QUALITY_CONSTITUTION` |
| 5 | **4,312자** | `director/ENSEMBLE_SELECTION_PROMPT` |
| 6 | **4,232자** | `continuity_arc/ARC_CONTINUITY_INSPECTION_PROMPT` |
| 7 | **3,650자** | `ensemble/BLUEPRINT_GENERATION_PROMPT` |
| 8 | **3,621자** | `manager/UPDATE_STATE_PROMPT_V25` |
| 9 | **3,333자** | `continuity_blueprint/CONTINUITY_INSPECTION_PROMPT` |
| 10 | **3,316자** | `continuity_manuscript/MANUSCRIPT_CONTINUITY_PROMPT` |

`PLAN_ARC_PROMPT_V25`는 12,280자로 단일 프롬프트 중 최대이며, JSON 출력 형식 + Few-Shot 예시 + Chain-of-Thought 단계 + 상태 추적 규칙이 모두 포함되어 있다.

---

## 8. 중복 프롬프트

### 8-1. 완전 이원화 (Python 인라인 + YAML 동일본)

다음 17개 프롬프트는 Python 인라인 상수와 YAML 파일에 **사실상 동일한 내용**이 존재한다. 코드는 인라인만 사용하므로 YAML은 사문화된 복사본이다.

| 도메인 | 키 수 | Python 소스 |
|--------|-------|-------------|
| analyst | 5 | `analyst_prompts.py` |
| director | 4 | `director_prompts.py` |
| continuity_arc | 2 | `continuity_arc.py` |
| continuity_blueprint | 1 | `continuity_blueprint.py` |
| continuity_manuscript | 1 | `continuity_manuscript.py` |
| manager | 1 | `manager.py` |
| preflight_checker | 1 | `preflight_checker.py` |
| block_enricher | 3 (+2 YAML전용) | `block_enricher.py` |
| consensus_validator | 1 | `consensus_validator.py` |
| state_extractor | 1 | `state_extractor.py` |
| state_locked_arc_generator | 3 | `state_locked_arc_generator.py` |
| unified_arc_validator | 1 | `unified_arc_validator.py` |
| arc_corrector | 1 | `arc_corrector.py` |
| arc_critic | 1 | `arc_critic.py` |
| quality_constitution | 1 (+3 장르별) | `quality_constitution.py` |

> **위험**: 어느 한쪽(Python 또는 YAML)만 수정하면 불일치가 발생한다. 현재는 YAML이 참조되지 않아 문제가 없으나, 향후 YAML 전환 시 동기화 실패 위험이 있다.

### 8-2. YAML 내 키 중복

`emotion_tracker.yaml`에서 `GENERATE_RECOMMENDATION__RECOMMENDATION` 키가 **2번 정의**되어 있다(L4, L32). PromptLoader의 단순 파서에서는 뒤의 정의가 앞을 덮어쓴다. 의도는 "부정적 감정 지속 시"와 "긍정적 감정 지속 시" 두 가지 추천을 분리하려는 것으로 보이나, 키가 동일하여 **첫 번째 추천(절망 속 희망 씨앗)이 소실**된다.

### 8-3. 유사 내용 중복

| 프롬프트 A | 프롬프트 B | 유사도 | 비고 |
|-----------|-----------|--------|------|
| `state_extractor/STATE_EXTRACTION_PROMPT` | `state_locked_arc_generator/STATE_EXTRACTION_PROMPT` | 키 이름 동일 | 다른 YAML 파일, 다른 내용. 혼동 위험 |
| `continuity_blueprint` 전체 | `continuity_manuscript` 전체 | 구조 유사 | 역할이 유사 (연속성 검증). 의도적 분리이나 공통 부분 추출 가능 |

---

## 9. 종합 발견 사항 및 권고

### 9-1. 핵심 문제 (Severity: HIGH)

| # | 문제 | 영향 | 권고 |
|---|------|------|------|
| H-1 | **YAML-인라인 이원화**: 17개 프롬프트가 YAML과 Python 양쪽에 존재하나 YAML은 미참조 | YAML 수정이 무시됨; 관리 혼란 | 각 에이전트에 `_prompt_api.py` 래퍼 패턴(analyst_prompt_api.py 방식)을 적용하여 YAML을 SSOT로 전환 |
| H-2 | **`.format()` 미보호**: 14개 에이전트가 SafeDict 없이 `.format()` 사용 | LLM 응답 내 `{}`로 KeyError 크래시 | PromptLoader.load() 전환 또는 SafeDict 적용 |
| H-3 | **emotion_tracker.yaml 키 중복**: 동일 키 2회 정의로 첫 번째 정의 소실 | 감정 추천 기능의 절반 손실 | 키를 `RECOMMENDATION__NEGATIVE_STREAK`와 `RECOMMENDATION__POSITIVE_STREAK`로 분리 |

### 9-2. 중간 문제 (Severity: MEDIUM)

| # | 문제 | 영향 | 권고 |
|---|------|------|------|
| M-1 | **60개 미사용 YAML 키**: 정의만 있고 참조 없음 | 유지보수 비용, 혼란 | 에이전트별 PromptLoader 전환 작업을 단계적으로 진행; 전환 완료 전까지 YAML에 `# [PENDING] 미연결` 주석 추가 |
| M-2 | **genre_stage.yaml 미연결**: STAGE3_MEDICAL 작성 후 코드 미연결 | Stage 3 장르 특화 프롬프트 미작동 | Blueprint 생성 경로에 genre_stage 로드 로직 추가 |
| M-3 | **장르 Guard 프롬프트 YAML 미외부화**: 10개 Guard의 f-string 프롬프트가 코드에만 존재 | 프롬프트 수정 시 코드 변경 필요 | 정적 부분은 YAML로 분리, 동적 리스트(`FORBIDDEN_TERMS` 등)는 placeholder로 처리 |

### 9-3. 낮은 문제 (Severity: LOW)

| # | 문제 | 영향 | 권고 |
|---|------|------|------|
| L-1 | **`PLAN_ARC_PROMPT_V25` 과대 크기**: 12,280자, 단일 프롬프트 최대 | 토큰 비용, 가독성 저하 | 반복 규칙(Few-Shot 예시)을 분리하여 조건부 주입 |
| L-2 | **chief_writer_prompts.py `build_chief_writer_main_prompt`**: 18개 매개변수의 대형 f-string | YAML 외부화 어려움 | 현 구조 유지하되, 각 섹션(`{feedback_section}` 등)의 빌더를 개별 YAML로 외부화 검토 |
| L-3 | **analyst 2개 키 YAML 부재**: RECOVERY_PROMPT, VOLUME_STRATEGY_PROMPT | 항상 폴백 경로 실행 | analyst.yaml에 두 키 추가 |

### 9-4. 외부화 우선순위 권고

YAML 전환 작업의 ROI가 높은 순서:

1. **1단계**: 이미 YAML이 있는 17개 에이전트에 PromptLoader 래퍼 적용 (인라인 제거)
2. **2단계**: `quality_constitution.py`, `manager.py`, `state_extractor.py` 등 독립 상수 파일의 YAML 전환
3. **3단계**: `chief_writer_prompts.py`의 `build_chief_writer_main_prompt()` 등 f-string 대형 템플릿은 현 구조 유지 (YAML 외부화 효과 낮음)
4. **4단계**: 장르 Guard 프롬프트는 정적 부분만 YAML 분리 검토

---

## 10. 통계 요약

| 항목 | 수치 |
|------|------|
| YAML 파일 | 40개 |
| YAML 정의 키 | 81개 |
| 코드에서 실제 참조되는 YAML 키 | **21개** (26%) |
| 미사용 YAML 키 | **60개** (74%) |
| Python 하드코딩 대형 프롬프트 | 216개 (300자+) |
| 인라인-YAML 이원화 프롬프트 | 17개 |
| SafeDict 미사용 `.format()` 위치 | 40개 |
| 장르 Guard purism 프롬프트 | 10개 (모두 인라인) |
| genre_stage.yaml Stage 3 프롬프트 | 1개 (미연결) |
| YAML 내 키 중복 | 1건 (emotion_tracker) |
| [Role] 정의 | 47개 (불일치 0건) |
