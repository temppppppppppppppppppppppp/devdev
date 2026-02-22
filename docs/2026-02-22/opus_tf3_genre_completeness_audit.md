# Opus TF3 - 10개 장르 지원 완전성 전수 감사

> 작성: Claude Opus 4.6 | 2026-02-22
> 범위: 체크리스트 16곳 + 추가 5곳 = 21곳 전수 검증
> 대상 장르: wuxia, hunter, investment, fantasy, composer, cooking, alt_history, actor, sports, medical

---

## 요약

| # | 검증 위치 | 결과 | 누락 장르 |
|---|-----------|------|-----------|
| 1 | constants.py GenreTypes | PASS (10/10) | -- |
| 2 | constants.py HUDKeys | PASS (10/10) | -- |
| 3 | constants.py NPCHUDKeys | PASS (10/10) | -- |
| 4 | preset_registry.py GENRE_PRESETS | PASS (10/10) | -- |
| 5 | preset_registry.py NPC_GENRE_PRESETS | PASS (10/10) | -- |
| 6 | genre_guards/ + __init__.py factory | PASS (10/10) | -- |
| 7 | genre_hud_manager.py + factory | PASS (10/10) | -- |
| 8 | genre_stage.yaml (STAGE2/3 prompts) | **FAIL (1/10)** | wuxia, hunter, investment, fantasy, composer, cooking, alt_history, actor, sports 누락 |
| 9 | analyst_libraries JSON | **FAIL (9/10)** | fantasy 누락 |
| 10 | strategies/ + genre_manager.py | **FAIL (7/10)** | fantasy, alt_history, actor 누락 |
| 11 | main_a.py _select_genre | PASS (10/10) | -- |
| 12 | analyst.py genre_library_map | **FAIL (9/10)** | fantasy 누락 |
| 13 | analyst.py _GENRE_DETECT_MAP | PASS (10/10) | -- |
| 14 | director.py | PASS (N/A - 장르 비종속 설계) | -- |
| 15 | chief_writer.py | PASS (N/A - 장르 비종속 설계) | -- |
| 16 | state_tracker_npc.py _SKILL_LOG_LABEL | **FAIL (8/10)** | composer, alt_history 누락 |
| 17 | story_expander.py | PASS (N/A - GenreTypes.all() 동적 참조) | -- |
| 18 | reverse_expander.py | PASS (N/A - GenreTypes.all() 동적 참조) | -- |
| 19 | primitive_forbidden.json genre_rules | PASS (10/10) | -- |
| 20 | narrative_diversity.py CONTRASTIVE_EXAMPLES | **FAIL (8/10)** | fantasy, composer 누락 |
| 21 | stage0/__init__.py SUPPORTED_GENRES | PASS (10/10) | -- |
| 22 | scoring_validator.py GENRE_WEIGHTS | PASS (10/10) | -- |
| 23 | scoring_validator.py GENRE_THRESHOLDS | **FAIL (4/10)** | composer, cooking, alt_history, actor, sports, medical 누락 |
| 24 | scoring_validator.py _get_genre_specific_feedback | **FAIL (3/10)** | fantasy, composer, cooking, alt_history, actor, sports, medical 누락 |
| 25 | catharsis_timer.py | PASS (10/10) | -- |
| 26 | validation_orchestrator.py GENRE_THRESHOLD_PROFILES | PASS (10/10) | -- |
| 27 | context_advisor.py / genre_hints.yaml | PASS (10/10) | -- |
| 28 | preset_registry.py detect_new_genre() | PASS (10/10) | -- |

**종합: 8곳에서 누락 발견. 심각도별 분류: Critical 2건, Major 4건, Minor 2건**

---

## 상세 분석

### 1. constants.py - GenreTypes [PASS 10/10]

**파일**: `modules/core/constants.py` L40-67

10개 장르 모두 클래스 속성 + `all()` + `get_name()` 매핑 완비.

```python
GenreTypes.all() = [wuxia, hunter, investment, fantasy, composer, cooking, alt_history, actor, sports, medical]
```

### 2. constants.py - HUDKeys [PASS 10/10]

**파일**: `modules/core/constants.py` L294-365

10개 장르 모두 PROTAGONIST/HUD_ROOT/ACTUAL_TRUTH 3종 속성 + `_GENRE_HUD_MAP` 매핑 완비.
`get_protagonist_name()` 내부 HUD 순회 리스트에도 FantasyHUD 포함 확인 (L429).

### 3. constants.py - NPCHUDKeys [PASS 10/10]

**파일**: `modules/core/constants.py` L468-496

10개 장르 모두 클래스 속성 + `get_key()` dict 매핑 완비.

### 4. preset_registry.py - GENRE_PRESETS [PASS 10/10]

**파일**: `modules/core/stage0/preset_registry.py` L42-270

10개 장르 모두 프리셋 정의 완비. (추가로 romance, politics, military도 포함)

### 5. preset_registry.py - NPC_GENRE_PRESETS [PASS 10/10]

**파일**: `modules/core/stage0/preset_registry.py` L291-410

10개 장르 모두 NPC 프리셋 정의 완비.

### 6. genre_guards/ + __init__.py factory [PASS 10/10]

**파일**: `modules/core/genre_guards/__init__.py`

10개 Guard 파일 모두 존재:
- wuxia_guard.py, hunter_guard.py, investment_guard.py, fantasy_guard.py
- composer_guard.py, cooking_guard.py, alt_history_guard.py
- actor_guard.py, sports_guard.py, medical_guard.py

`create_genre_guard()` 팩토리 함수에 10개 분기 모두 존재.

### 7. genre_hud_manager.py + factory [PASS 10/10]

**파일**: `modules/core/genre_hud_manager.py`

10개 HUD Manager 클래스 모두 존재:
- MartialManager (wuxia, 별도 파일 martial_manager.py)
- HunterHUDManager, FinanceHUDManager, ComposerHUDManager
- CookingHUDManager, JoseonHUDManager, ActorHUDManager
- SportsHUDManager, MedicalHUDManager, FantasyHUDManager

`create_hud_manager()` 팩토리 함수에 10개 분기 모두 존재.

### 8. genre_stage.yaml (STAGE2/3 prompts) [FAIL 1/10]

**파일**: `config/prompts/genre_stage.yaml`

**현재 상태**: STAGE3_MEDICAL 1개만 존재.

**누락**:
- STAGE2_* 프롬프트: 10개 장르 모두 없음 (0/10)
- STAGE3_* 프롬프트: medical 외 9개 장르 없음 (1/10)
  - 누락: wuxia, hunter, investment, fantasy, composer, cooking, alt_history, actor, sports

**심각도**: **Major** -- 그러나 실제 코드에서 `genre_stage.yaml`을 참조하는 import/load 로직이 모듈 코드에서 발견되지 않음. `genre_prompt`는 Guard의 `get_v20_purism_prompt()` 메서드를 통해 주입되는 구조이므로, 이 YAML 파일은 현재 사실상 미사용 상태일 가능성이 높음. 확인 필요.

**영향**: genre_stage.yaml이 실제로 로드되어 사용되지 않는다면 기능적 영향 없음. 사용된다면 9개 장르에서 STAGE3 가이드라인 누락.

### 9. analyst_libraries JSON [FAIL 9/10]

**파일**: `config/prompts/analyst_libraries*.json`

존재하는 파일:
- analyst_libraries.json (wuxia)
- analyst_libraries_hunter.json
- analyst_libraries_investment.json
- analyst_libraries_composer.json
- analyst_libraries_cooking.json
- analyst_libraries_alt_history.json
- analyst_libraries_actor.json
- analyst_libraries_sports.json
- analyst_libraries_medical.json

**누락**: `analyst_libraries_fantasy.json` 파일 없음.

**심각도**: **Critical** -- analyst.py의 `genre_library_map`에도 fantasy 매핑이 없어 (아래 #12 참조), fantasy 장르 선택 시 `analyst_libraries.json` (wuxia용)으로 폴백됨. 판타지 장르에 무협 서사 아키타입이 적용되는 문제 발생.

### 10. strategies/ [FAIL 7/10]

**파일**: `modules/domain/strategies/`

존재하는 전략 파일:
- wuxia_strategy.py
- hunter_strategy.py
- investment_strategy.py
- composer_strategy.py
- cooking_strategy.py
- sports_strategy.py
- medical_strategy.py

**누락**:
- `fantasy_strategy.py` -- 없음
- `alt_history_strategy.py` -- 없음
- `actor_strategy.py` -- 없음

**심각도**: **Major** -- 전략 파일은 Stage 2 arc 설계 시 장르별 특화 전략을 제공하는 역할. 누락된 3개 장르는 `base_strategy.py` 폴백으로 동작하나, 장르 특화 전략 없이 범용 전략만 적용됨.

**참고**: `__init__.py`가 사실상 빈 파일(1줄)이며 별도의 genre_manager.py 팩토리도 없음. 전략 선택 로직이 다른 곳에서 관리되는 구조.

### 11. main_a.py _select_genre [PASS 10/10]

**파일**: `main_a.py` L2529-2738

10개 장르 모두 선택 메뉴(1~10번) + HUD 키 + critical_keys + PresetRegistry genre_map 매핑 완비.

### 12. analyst.py - genre_library_map [FAIL 9/10]

**파일**: `modules/domain/agents/analyst.py` L1414-1424

```python
genre_library_map = {
    "wuxia": "analyst_libraries.json",
    "hunter": "analyst_libraries_hunter.json",
    "investment": "analyst_libraries_investment.json",
    "cooking": "analyst_libraries_cooking.json",
    "actor": "analyst_libraries_actor.json",
    "sports": "analyst_libraries_sports.json",
    "medical": "analyst_libraries_medical.json",
    "alt_history": "analyst_libraries_alt_history.json",
    "composer": "analyst_libraries_composer.json",
}
```

**누락**: `"fantasy"` 키 없음.

**심각도**: **Critical** -- fantasy 장르 선택 시 `genre_library_map.get(genre, "analyst_libraries.json")`에 의해 wuxia 라이브러리로 폴백. 판타지 고유의 서사 아키타입(마법 각성, 종족 갈등, 이세계 탐험 등)이 제공되지 않음.

**연관**: #9(파일 자체 부재)와 동일 근본 원인. `analyst_libraries_fantasy.json` 파일 생성 + map 등록 필요.

### 13. analyst.py - _GENRE_DETECT_MAP [PASS 10/10]

**파일**: `modules/domain/agents/analyst.py` L1369-1392

10개 장르 모두 한글/영문 키워드 매핑 완비. fantasy/판타지 포함.

### 14. director.py [PASS - 장르 비종속 설계]

**파일**: `modules/domain/agents/director.py`

Director는 장르를 `set_genre()` 메서드로 외부에서 받아 저장하고, 장르별 검증은 `guard.validate()`를 통해 위임하는 구조. Director 내부에 장르별 하드코딩된 매핑 테이블이 없으므로 장르 추가 시 별도 수정 불필요.

### 15. chief_writer.py [PASS - 장르 비종속 설계]

**파일**: `modules/domain/agents/chief_writer.py`

Chief Writer는 `genre_name` 파라미터를 받아 프롬프트에 주입하는 구조. 장르별 분기 코드가 없으며, `purism_prompt`를 Guard에서 받아 전달하는 방식. 장르 추가 시 별도 수정 불필요.

### 16. state_tracker_npc.py - _SKILL_LOG_LABEL [FAIL 8/10]

**파일**: `modules/domain/agents/state_tracker_npc.py` L74-83

```python
_SKILL_LOG_LABEL = {
    "wuxia": ("\U0001f94b", "무공 습득"),
    "hunter": ("\u2694\ufe0f", "스킬 습득"),
    "investment": ("\U0001f4c8", "핵심 지식 등록"),
    "fantasy": ("\u2728", "마법 습득"),
    "cooking": ("\U0001f468\u200d\U0001f373", "조리법 습득"),
    "actor": ("\U0001f3ac", "연기 습득"),
    "sports": ("\U0001f3c5", "기술 습득"),
    "medical": ("\U0001f52c", "의술 습득"),
}
```

**누락**:
- `"composer"` -- 없음 (작곡가 장르에서 능력 습득 시 기본 라벨 "능력 습득" 폴백)
- `"alt_history"` -- 없음 (대체역사 장르에서 능력 습득 시 기본 라벨 폴백)

**심각도**: **Minor** -- `.get(genre, ("무공", "능력 습득"))` 폴백이 있어 크래시는 없음. 그러나 로그 메시지에서 "작곡 기법 습득" 대신 "능력 습득"이, "관직/지식 습득" 대신 "능력 습득"이 출력됨.

### 17. story_expander.py [PASS - 동적 참조]

**파일**: `modules/core/stage0/story_expander.py`

`GenreTypes.all()`을 동적으로 참조하므로 장르 추가 시 자동 반영.

### 18. reverse_expander.py [PASS - 동적 참조]

**파일**: `modules/core/stage0/reverse_expander.py`

`GenreTypes.all()` / `GenreTypes.get_name()`을 동적으로 참조. 장르 추가 시 자동 반영.

### 19. primitive_forbidden.json - genre_rules [PASS 10/10]

**파일**: `modules/core/laws/primitive_forbidden.json` L9-61

10개 장르 모두 `genre_rules`에 등록 완비. 각 장르별 `apply_level` 설정:
- `full`: wuxia
- `partial`: fantasy
- `moderate`: alt_history
- `none`: hunter, investment, composer, cooking, actor, sports, medical

### 20. narrative_diversity.py - CONTRASTIVE_EXAMPLES [FAIL 8/10]

**파일**: `modules/core/narrative_diversity.py` L40-319

존재하는 키:
- wuxia, hunter, investment, cooking, alt_history, actor, sports, medical

**누락**:
- `"fantasy"` -- 없음
- `"composer"` -- 없음

**심각도**: **Minor** -- `.get(self.genre, self.CONTRASTIVE_EXAMPLES["wuxia"])` 폴백에 의해 판타지/작곡가 장르에서 무협용 Contrastive 예시가 주입됨. 장르 특성에 맞지 않는 네거티브 예시(무협 전투 묘사 등)가 Writer에게 전달되어 혼란을 줄 수 있음.

### 21. stage0/__init__.py - SUPPORTED_GENRES [PASS 10/10]

**파일**: `modules/core/stage0/__init__.py` L48-58

```python
SUPPORTED_GENRES = {
    "wuxia": "무협",
    "hunter": "헌터물/던전물",
    "investment": "투자물/재벌물",
    "fantasy": "판타지",
    "composer": "작곡가물",
    "cooking": "요리물",
    "alt_history": "대체역사",
    "actor": "배우물/연예계",
    "sports": "스포츠물",
    "medical": "의학물/닥터물",
}
```

### 22. scoring_validator.py - GENRE_WEIGHTS [PASS 10/10]

**파일**: `modules/validation/scoring_validator.py` L678-810

10개 장르 모두 가중치 프로파일(prose_rhythm, vocabulary_diversity, sensory_balance 등 10개 항목) 완비.

### 23. scoring_validator.py - GENRE_THRESHOLDS [FAIL 4/10]

**파일**: `modules/validation/scoring_validator.py` L29-34

```python
GENRE_THRESHOLDS = {
    "wuxia": 70,
    "hunter": 68,
    "investment": 72,
    "fantasy": 70,
}
```

**누락**: composer, cooking, alt_history, actor, sports, medical (6개)

**심각도**: **Major** -- 누락된 장르는 `DEFAULT_PASS_THRESHOLD = 70`으로 폴백되므로 기능은 정상 동작. 그러나 장르 특성에 맞는 임계값 튜닝이 불가. 예: 의학물은 정확성이 중요하여 높은 임계값이 적절할 수 있고, 스포츠물은 액션 위주로 낮은 임계값이 적절할 수 있음.

### 24. scoring_validator.py - _get_genre_specific_feedback [FAIL 3/10]

**파일**: `modules/validation/scoring_validator.py` L1043-1083

장르별 특화 피드백 로직이 존재하는 장르:
- wuxia (무술 키워드 체크, 클리셰 체크)
- hunter (시스템 요소 체크, 성장 묘사 체크)
- investment (금융 용어 체크, 논리적 설명 체크)

**누락**: fantasy, composer, cooking, alt_history, actor, sports, medical (7개)

**심각도**: **Major** -- 누락된 7개 장르에서는 장르 특화 피드백이 빈 리스트로 반환됨. Writer가 장르 고유 요소(마법 묘사, 수술 묘사, 경기 묘사 등)를 놓쳐도 피드백을 받지 못함.

### 25. catharsis_timer.py [PASS 10/10]

**파일**: `modules/validation/catharsis_timer.py`

10개 장르 모두 다음 3개 딕셔너리에 등록 완비:
- `CATHARSIS_INDICATORS` (카타르시스 지표)
- `FRUSTRATION_INDICATORS` (좌절 지표)
- `STRONG_CATHARSIS_WEIGHTS` (가중치)

장르별 추천(`genre_recommendations`)에도 10개 모두 등록.

### 26. validation_orchestrator.py - GENRE_THRESHOLD_PROFILES [PASS 10/10]

**파일**: `modules/validation/validation_orchestrator.py` L80-151

10개 장르 모두 임계값 프로파일(base_threshold, action_weight, dialogue_weight, emotion_weight) 완비.

### 27. context_advisor.py / genre_hints.yaml [PASS 10/10]

**파일**: `config/smart_retrieval/genre_hints.yaml`

10개 장르 모두 검색 힌트 키워드 등록 완비.
`context_advisor.py`의 `_DEFAULT_GENRE_HINTS`에도 10개 장르 폴백 정의 존재.

### 28. preset_registry.py - detect_new_genre() [PASS 10/10]

**파일**: `modules/core/stage0/preset_registry.py` L583-607

10개 장르 모두 키워드 목록 등록 완비 (+ romance, politics, military 추가 3개).

---

## 누락 종합표

| 누락 장르 | 누락 위치 | 심각도 |
|-----------|-----------|--------|
| **fantasy** | analyst_libraries JSON (#9), analyst.py genre_library_map (#12), narrative_diversity CONTRASTIVE_EXAMPLES (#20), scoring_validator GENRE_THRESHOLDS (#23), scoring_validator _get_genre_specific_feedback (#24), strategies/ (#10) | **Critical** |
| **composer** | state_tracker_npc _SKILL_LOG_LABEL (#16), narrative_diversity CONTRASTIVE_EXAMPLES (#20), scoring_validator GENRE_THRESHOLDS (#23), scoring_validator _get_genre_specific_feedback (#24) | Major |
| **alt_history** | state_tracker_npc _SKILL_LOG_LABEL (#16), scoring_validator GENRE_THRESHOLDS (#23), scoring_validator _get_genre_specific_feedback (#24), strategies/ (#10) | Major |
| **actor** | scoring_validator GENRE_THRESHOLDS (#23), scoring_validator _get_genre_specific_feedback (#24), strategies/ (#10) | Major |
| **cooking** | scoring_validator GENRE_THRESHOLDS (#23), scoring_validator _get_genre_specific_feedback (#24) | Major |
| **sports** | scoring_validator GENRE_THRESHOLDS (#23), scoring_validator _get_genre_specific_feedback (#24) | Major |
| **medical** | scoring_validator GENRE_THRESHOLDS (#23), scoring_validator _get_genre_specific_feedback (#24) | Major |
| genre_stage.yaml | 9개 장르 STAGE3 + 10개 장르 STAGE2 (#8) | 미사용 가능성 높음 |

---

## 수정 우선순위 권고

### P0 (Critical - 즉시 수정)

1. **`analyst_libraries_fantasy.json` 생성 + analyst.py genre_library_map에 fantasy 등록**
   - 현재 판타지 장르에서 무협 서사 아키타입이 사용되는 근본적 오류
   - 판타지 고유 아키타입 28개 (마법 각성, 종족 갈등, 이세계 탐험, 신화 퀘스트 등) 정의 필요
   - 파일: `config/prompts/analyst_libraries_fantasy.json` (신규)
   - 파일: `modules/domain/agents/analyst.py` L1414 (`"fantasy": "analyst_libraries_fantasy.json"` 추가)

### P1 (Major - 기능 개선)

2. **scoring_validator.py GENRE_THRESHOLDS 6개 장르 추가**
   - 파일: `modules/validation/scoring_validator.py` L29-34
   - 추가: composer(70), cooking(70), alt_history(72), actor(68), sports(68), medical(72)

3. **scoring_validator.py _get_genre_specific_feedback 7개 장르 추가**
   - 파일: `modules/validation/scoring_validator.py` L1043-1083
   - 각 장르별 키워드 체크 + 클리셰 체크 로직 추가

4. **strategies/ 누락 3파일 생성**
   - `fantasy_strategy.py` (마법 체계, 종족 관계, 이세계 규칙)
   - `alt_history_strategy.py` (역사 분기점, 정치 역학, 기술 도입 제약)
   - `actor_strategy.py` (연기 레이어, 업계 역학, 작품 선택 전략)

### P2 (Minor - 로그/UX 개선)

5. **state_tracker_npc.py _SKILL_LOG_LABEL 2개 장르 추가**
   - `"composer": ("음악", "음악 기법 습득")`
   - `"alt_history": ("책", "지식/기술 습득")`

6. **narrative_diversity.py CONTRASTIVE_EXAMPLES 2개 장르 추가**
   - `"fantasy"`: 이세계 전투, 마법 묘사, 종족 관계 네거티브 예시
   - `"composer"`: 음악 묘사, 창작 과정, 업계 관계 네거티브 예시

### P3 (확인 후 결정)

7. **genre_stage.yaml 확장 여부**
   - 현재 모듈 코드에서 이 YAML을 참조하는 로직 미발견
   - 실제 사용 여부 확인 후 확장/삭제 결정

---

## 구조적 관찰

### 양호한 패턴
- `constants.py`, `preset_registry.py`, `genre_guards/`, `genre_hud_manager.py`는 10개 장르 완전 지원
- `catharsis_timer.py`, `validation_orchestrator.py`, `context_advisor.py`는 10개 장르 완전 지원
- `main_a.py`, `stage0/__init__.py`, `primitive_forbidden.json`는 10개 장르 완전 지원
- Director, Chief Writer는 장르 비종속 설계로 장르 추가 시 수정 불필요 (우수한 아키텍처)
- story_expander, reverse_expander는 GenreTypes.all() 동적 참조로 자동 확장 (우수한 아키텍처)

### 반복되는 누락 패턴
- **fantasy** 장르가 가장 빈번한 누락 (6곳) -- V66에서 wuxia로부터 분리 독립했으나 일부 위치에서 반영 누락
- **scoring_validator.py**가 가장 많은 미반영 (GENRE_THRESHOLDS 6개 + _get_genre_specific_feedback 7개)
- **strategy 파일 생성 누락**은 alt_history(V61.9), actor(V62), fantasy(V66) 장르 추가 시 동시에 생성하지 않은 것이 원인

### 위험도 평가
- fantasy analyst_libraries 누락은 실사용 시 무협 아키타입이 주입되므로 **품질에 직접적 영향**
- scoring_validator 누락은 기본값 폴백이 존재하여 **크래시 위험 없음**, 그러나 장르 최적화 불가
- strategy 파일 누락은 base_strategy 폴백으로 **기능은 정상**, 그러나 장르 특화 전략 미적용
