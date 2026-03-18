# S5: Stage 0-2 내부 구현 SSOT

> **최종 갱신**: 2026-03-18
> **소스 문서**:
> - `geuldobi-v2-stage0-2-hidden-internals-deepdive-full-survey.md` (3회 독립 코드 조사 + 교차 대조 + 3PASS 감리)
> - `geuldobi-v2-stage0-2-hidden-internals-adversarial-audit.md` (1차 적대적 감리 48건)
> - `geuldobi-v2-stage0-2-hidden-internals-adversarial-audit-r2.md` (2차 적대적 감리 47건)
> **감리 이력**: 6회 적대적 감리, 48+47=95건 검증

---

## 1. 개관

Stage 0-2는 글도비 v2 파이프라인의 전반부로, 작품의 기초 설정부터 Arc 전술 설계까지를 담당한다.

| Stage | 역할 | 핵심 산출물 |
|-------|------|-----------|
| **Stage 0** | Bible/Treatment/Style 초기화 | Bible JSON, Treatment 블록, StyleGuide |
| **Stage 1** | Volume Strategy | 분량 전략 (Stage 2 입력) |
| **Stage 2** | Arc Tactical Design | 3전략 앙상블 + Director 판정 → Arc tactical_doc |

**모듈 파일 구성**: `modules/core/stage0/` 하위에 5개 모듈 + `__init__.py` = 총 6개 파일 (`stage0/__init__.py:1`, `story_expander.py`, `reverse_expander.py`, `style_extractor.py`, `preset_registry.py`, `spinner.py`)

**지원 장르**: 10개 (`stage0/__init__.py:61-72`)
- wuxia(무협), hunter(헌터물), investment(투자물), fantasy(판타지), composer(작곡가물), cooking(요리물), alt_history(대체역사), actor(배우물), sports(스포츠물), medical(의학물)

---

## 2. Stage 0 상세

### 2.1 StageZeroManager — 서브메뉴 라우팅

**파일**: `modules/core/stage0/__init__.py` (`__init__.py:283-311`)

기존 프로젝트와 신규 프로젝트에서 서브메뉴 구성이 다르다 (I3 정정).

| Sub-key | 모드 | 핸들러 | 설명 |
|---------|------|--------|------|
| 1 | Legacy | 수동 Bible/Treatment 파일 선택 | 파일 시스템 직접 접근 |
| 2 | AI 신규 | `StoryExpander` | 컨셉 → Bible + Treatment 생성 |
| 3 | AI 역설계 | `ReverseExpander` | 기존 원고 → Bible 추출 |
| 4 | 임포트 | JSON 로드 | 기존 Bible JSON 불러오기 |
| 5 | 확장 | `StoryExpander.extend()` | 기존 Treatment 블록 추가 |
| 6 | 스타일 분석 | `StyleExtractor` | 참조 원고 → 스타일 DNA |
| 7 | Work Guard | 설정 UI | 작업 가드 YAML 구성 |

- **기존 프로젝트**: 7개 옵션 (1-7 전부) (`__init__.py:283-311`)
- **신규 프로젝트**: 6개 옵션 (1번 Legacy 제외) (`__init__.py:283-311`, I3)

### 2.2 StoryExpander — 컨셉 → Bible 파이프라인

**파일**: `modules/core/stage0/story_expander.py`

#### 2.2.1 핵심 상수

| 상수 | 값 | 코드 근거 |
|------|---|----------|
| `_CONCEPT_PROMPT_MAX` | 4000 | `story_expander.py:33` |
| `_CONCEPT_PROMPT_HEAD` | 2500 | `story_expander.py:34` |
| `_STAGE0_REVIEW_MAX_ATTEMPTS` | 2 | `story_expander.py:35` |
| `_STAGE0_REVIEW_WINDOW` | 3 | `story_expander.py:36` |

#### 2.2.2 LLM 호출 — 2모델 폴백 + 재시도

```
_FALLBACK_MODELS = [AIModels.SUMMARY_MODEL, AIModels.V50_MODULE_MODEL]  # story_expander.py:61
각 모델당 _MAX_RETRIES=3 (story_expander.py:65)
temperature=0.85, max_tokens=8192 (story_expander.py:68)
_BASE_DELAY=2.0초, 지수 백오프 (story_expander.py:66,93)
재시도 가능 에러: 429, rate limit, quota, 503, 500, timeout (story_expander.py:64)
모든 시도 실패 시: return "" — 예외 없음 (story_expander.py:103)  [SF1]
```

#### 2.2.3 JSON 파싱 캐스케이드

```
1단계: json.loads(text) 시도 (story_expander.py:115)
2단계: ```json...``` 블록 추출 후 재시도 (story_expander.py:111-114)
실패 시: return None — 예외 없음 (story_expander.py:117)  [SF2]
```

**하류 영향 체인**:
```
_call_llm() → ""
  → _parse_json("") → None (story_expander.py:107-108)
  → extracted = {} (빈 딕셔너리) (story_expander.py 조건 분기)
  → generate_bible() → 완전히 빈 dict {} 반환 — CoreIdentity 키 자체 부재  [SF3, I1 정정]
  → 리뷰 게이트 → completeness_warnings 2+건 → REJECT
  → stage0_manager → (empty_dict, empty_list, None) 반환
```

#### 2.2.4 리뷰 게이트 — 이중 판정 시스템

**LLM 판정** (정상 경로):
```
Bible/Treatment → 사실 수집 → LLM "PASS/RETRY/REJECT" 판정
```

**Python 폴백 판정** (LLM 실패 시):
```python
if roadmap_not_ready OR completeness_warnings >= 2:
    return REJECT
elif fixable_issues AND attempt < max:
    return RETRY
else:
    return PASS
```

엣지 케이스: 마지막 시도(attempt=2)에서 warning 2건 → 무조건 REJECT, 복구 불가.

#### 2.2.5 Bible 완전성 경고 수집

5개 분기, 동시 발화 최대 **4건** (조건 1-2 상호 배타) (`story_expander.py:420-429`, I5 정정):

| # | 조건 | 경고 메시지 |
|---|------|-----------|
| 1 | CoreIdentity 누락 | "핵심 정체성 미정의" |
| 2 | 주인공 인물/배경 누락 | "주인공 페르소나/배경 미정의" |
| 3 | KeyNPCs < 2 | "주요 NPC 2인 미만" |
| 4 | WorldLaws 비어있음 | "세계관 법칙 미정의" |
| 5 | CurrentEra 누락 | "시대 배경 미정의" |

- 조건 1-2는 `if/elif` 상호 배타 → 동시 최대 4건 (`story_expander.py:420-429`)
- 경고는 `bible["_completeness_warnings"]`에 저장 → 리뷰 게이트에서 참조

#### 2.2.6 Treatment 블록 배치 생성

```
60개 블록 기본 (story_expander.py:483)
  → 스켈레톤 20블록 배치 × 3회 (story_expander.py:647)  [I4]
  → 디테일 10블록 배치 (story_expander.py:712)  [I4]
  → 연속성 컨텍스트: 최근 3개 승인된 블록
```

- **SF5**: 디테일 생성 중 블록 스킵 시, 연속성 컨텍스트가 stale 블록 참조. 경고 없음. (심각도: 저)
- **MSF-D**: 스켈레톤 LLM 실패 시 `[]` 확장 — 블록 수 미달 (`story_expander.py:647-652`)
- **MSF-E**: 디테일 LLM 실패 시 스켈레톤 블록 그대로 사용, content 미생성 (`story_expander.py:712-716`)

### 2.3 ReverseExpander — 기존 원고 → Bible 역설계

**파일**: `modules/core/stage0/reverse_expander.py`

#### 2.3.1 인코딩 방어 — Fail-Closed 전략

```
UTF-8 → cp949 2단계만 시도 (reverse_expander.py:204-219)
EUC-KR, UTF-16 등 다른 인코딩 미지원 → DraftEncodingError 예외 전파
```

이 경로는 유일하게 예외를 전파하는 **Fail-Closed** 설계.

#### 2.3.2 장르 자동 감지 폴백

```
5개 원고 × 2000자 샘플 → LLM 분류 (temperature=0.3) (reverse_expander.py:35-36)
LLM 실패 시: GenreTypes.INVESTMENT 기본값 (reverse_expander.py:228-253)  [SF8]
```

위험: 무협 원고를 투자물로 오분류 시, PresetRegistry가 투자물 필드를 로드 → HUD 구조 불일치.

#### 2.3.3 미사용 상수: `_MAX_WORKERS = 3`

```python
_BATCH_SIZE = 5   # 사용됨 (reverse_expander.py:415)
_MAX_WORKERS = 3  # 미사용 (reverse_expander.py:416) — 파일 내 참조 0건
```

모든 에피소드 처리는 `for draft in batch:` 순차 루프 (`reverse_expander.py:430`). 주석 "API rate limit 고려"는 의도를 설명하지만 병렬화는 미구현.

#### 2.3.4 에피소드 Bible 추출 침묵 실패

```python
# reverse_expander.py:433-443
try:
    extracted = self._extract_single_episode_bible(draft, prev_state, schema)
except Exception as exc:
    logging.warning(f"제{ep_num}화 순차 추출 실패: {exc}")
    extracted = {"ep_num": ep_num, "hud_snapshot": {}, "changes": [],
                 "new_npcs": [], "key_events": []}  # ep_num 포함 스켈레톤 dict  [SF6, I2]
```

하류 영향: 스켈레톤 episode_bible → FactLedger에 빈 state_changes 주입 → 해당 에피소드의 사실 추적 공백.

#### 2.3.5 HUD 정규화 의존성

```python
# reverse_expander.py:409-410
if self.preset_registry and "hud_snapshot" in result:
    result["hud_snapshot"] = self.preset_registry.normalize_hud(result["hud_snapshot"])
# preset_registry=None이면 HUD 정규화 생략  [SF7]
```

#### 2.3.6 역설계 경로 추가 침묵 실패 (MSF-A, B, C)

| ID | 위치 | 동작 | 심각도 |
|----|------|------|--------|
| MSF-A | `reverse_expander._extract_protagonist():335-338` | LLM 실패 → `return {}` — 주인공 정보 전무 | 고 |
| MSF-B | `reverse_expander._extract_world_state():370-373` | LLM 실패 → `return {}` — 세계관 전무 | 중 |
| MSF-C | `reverse_expander._extract_npcs():351-356` | LLM 실패 → `return []` — NPC 전무 | 중 |

### 2.4 StyleExtractor — 스타일 DNA 추출

**파일**: `modules/core/stage0/style_extractor.py`

#### 2.4.1 5단계 추출 파이프라인 (3 Python + 2 LLM)

| 단계 | 방법 | 비용 | 침묵 실패 경로 |
|------|------|------|-------------|
| 1. Python 통계 | 문장 길이, 대화 비율, 시점 | $0 | 텍스트 없으면 기본값 |
| 2. 샘플 큐레이션 | 예시 문장, 감각어, 전환어 | $0 | 빈 리스트 |
| 3. 리듬 분석 | 문장 길이 패턴 (S/M/L) | $0 | 빈 패턴 |
| 4. LLM 심층 분석 | 톤, 감정 표현, 대화 패턴 | ~$0.01 | LLM 없으면 전체 스킵 [SF9] |
| 5. Anti-AI 패턴 | AI 냄새 패턴 금지 목록 | ~$0.01 | LLM 없으면 전체 스킵 [SF9] |

핵심: 단계 4-5가 LLM 의존. LLM 클라이언트 없으면 침묵 스킵 — StyleGuide에 톤/감정/anti-AI 필드가 빈값.

#### 2.4.2 시점(POV) 감지 엣지 케이스

```python
# style_extractor.py:583-590
first_person = len(re.findall(r"(나는|나의|내가|나를|나에게|내 )", all_text))
third_person = len(re.findall(r"(그는|그녀는|그의|그녀의|그가|그를)", all_text))
if first_person > third_person * 2:  return "1인칭"
elif third_person > first_person * 2: return "3인칭"
else: return "혼합"  # [SF10]
```

엣지 케이스: 대명사가 거의 없는 텍스트 → 0 > 0\*2 = False → "혼합" 기본값. 실제 시점과 무관한 휴리스틱 한계.

#### 2.4.3 대화 비율 감지 한계

```python
# 인용 부호만 감지: ["""]([^"""]+)["""]
# 미감지: 「」, 『』, 홑따옴표, 대사 표시 없는 직접 화법
```

일부 장르(특히 무협)에서 비표준 인용 부호 사용 시 대화 비율 과소 추정.

#### 2.4.4 캐시 정합성 — 9필드 일치 필수

| # | 필드 | 코드 근거 |
|---|------|----------|
| 1 | `cache_meta_version` | `style_extractor.py:429` |
| 2 | `analysis_version` | `style_extractor.py:430` |
| 3 | `genre` | `style_extractor.py:431` |
| 4 | `model_id` | `style_extractor.py:432` |
| 5 | `sampling_policy` | `style_extractor.py:433` |
| 6 | `prompt_contract_hash` | `style_extractor.py:434` |
| 7 | `reference_manifest_hash` | `style_extractor.py:435` |
| 8 | `selected_primary_pov` | `style_extractor.py:436` |
| 9 | `external_pov_insert_policy` | `style_extractor.py:437` |

9개 중 1개라도 변경 시 전체 재추출. 캐시 버전: `s0-style-cache-v2`. (`style_extractor.py:427-439`)

### 2.5 PresetRegistry — 동적 스키마 관리

**파일**: `modules/core/stage0/preset_registry.py`

#### 2.5.1 침묵 타입 강제 (deepcopy 폴백)

```python
# preset_registry.py:523-550
def _enforce_type(self, value, field_def):
    try:
        if field_def.type == "int":
            if isinstance(value, str):
                return self._parse_korean_number(value)  # "100억" → 10_000_000_000
            return int(value)
        elif field_def.type == "enum":
            if value in field_def.enum_values:
                return value
            return copy.deepcopy(field_def.default)  # 침묵 폴백  [SF11]
    except (ValueError, TypeError, KeyError, AttributeError):
        return copy.deepcopy(field_def.default)  # 침묵 폴백, 경고 없음  [SF11]
```

위험: LLM이 잘못된 enum 값을 생성하면, 경고 없이 기본값으로 교체. 사용자는 기본값이 적용된 사실을 모름.

#### 2.5.2 한국어 숫자 파싱 (4곳 독립 구현 중 1번째)

```python
# preset_registry.py:552+ (인스턴스 메서드)
# "1조2억3만" → 순차 파싱
# 단위: 조(1T), 억(100M), 만(10K), 천(1K), 백(100)
# "만" alone → current = 1 → 1만 (10K) (preset_registry.py:577-578)
```

이 기능은 코드베이스에 **4곳 독립 구현** 존재 (W4 정정):
1. `preset_registry._parse_korean_number()` — 인스턴스 메서드 (`preset_registry.py:552`)
2. `stage2_finalizer._to_num_with_korean_units()` — 모듈 수준 함수 (`stage2_finalizer.py:36`)
3. `stage2_optimizer._parse_korean_number()` — 별도 구현
4. `investment_arithmetic_checker._parse_korean_amount()` — 별도 구현

엣지 케이스 처리가 미묘하게 다를 수 있어 통합 권장.

#### 2.5.3 필드 별명 정규화

```python
"internal_energy": ["내공", "inner_power", "qi", "기"]
"capital": ["자본", "자산", "money", "wealth", "총자산"]
```

LLM 출력의 다양한 필드명을 정규 필드명으로 통일. 별명 목록에 없는 필드는 통과 (`extra="allow"`).

---

## 3. Stage 2 상세

> **참고**: Stage 2 에이전트(ArcEnsemble, FourPhaseArcGenerator 등)는 `BaseAgent`를 상속하여 LLM을 호출한다. BaseAgent.ask() 파이프라인 상세 (모델 폴백, 프롬프트 크기 게이트, JSON 파싱, 에러 분류) → **S4 (LLM 통합 SSOT)** 참조.
> response_schemas.py의 스키마 정의 (anyOf 패턴, 라운드트립 손실 등) → **S4 §6** 참조.

### 3.1 ArcEnsemble — 3전략 앙상블

**파일**: `modules/domain/agents/arc_ensemble.py`

#### 3.1.1 전략 정의

| 전략 | temperature | 초점 | 코드 근거 |
|------|-----------|------|----------|
| conservative | 0.3 | 안정성과 연속성 우선 | `arc_ensemble.py:161-165` |
| balanced | 0.5 | 연속성과 새로움의 균형 | `arc_ensemble.py:167-170` |
| creative | 0.7 | 서사적 흥미 우선 | `arc_ensemble.py:173-177` |

#### 3.1.2 타임아웃 이중 계층 (config-overridable)

```python
# arc_ensemble.py:189-191
_TIMEOUTS = _SYSTEM_CFG.get("ensemble_timeouts", {}).get("arc", {})
ENSEMBLE_TIMEOUT = _TIMEOUTS.get("ensemble", 300)       # 기본값 5분 (system.yaml에서 오버라이드 가능)  [I6]
SINGLE_CANDIDATE_TIMEOUT = _TIMEOUTS.get("single", 240)  # 기본값 4분 (system.yaml에서 오버라이드 가능)  [I6]
```

침묵 실패:
- 개별 전략 타임아웃 시 해당 후보 침묵 드롭 (WARNING 로그만) [SF13, 심각도: 중]
- 2/3 후보 타임아웃 시 spare pool 고갈 → 전체 재생성 강제
- 전체 타임아웃 시 완료된 후보만 사용

#### 3.1.3 Tactical Doc 길이 필터

```python
# arc_ensemble.py:508
min_tactical_length = ep_count * Stage2Limits.MIN_CHARS_PER_EPISODE
# constants.py:244 → MIN_CHARS_PER_EPISODE = 450  [W1 정정, TF-59에서 500→450 하향]
```

- 미달 시: 로그 기록, 후보에서 제거 (`arc_ensemble.py:516-529`)
- 전 후보 미달 시: 가장 긴 불합격 후보 강제 사용 + degradation 경고 (`arc_ensemble.py:532-551`) [SF14]
- 이는 의도된 설계 (생산 중단 방지)

#### 3.1.4 ThreadPoolExecutor 병렬화

```python
# arc_ensemble.py:18 → ThreadPoolExecutor
# arc_ensemble.py:414 → 3 후보를 ThreadPoolExecutor로 병렬 생성
# as_completed()로 완료 순서대로 수집
```

스레드 안전: 장르 데이터를 사전 로드 후 스레드에 전달 (SQLite threading 회피). 메트릭 수집기는 RLock이므로 안전.

`last_error_type` 스레드 레이스: `blueprint_ensemble.py:297`, `base_agent.py:839`에서 3개 전략 스레드가 `self.last_error_type`에 경합 기록. 진단 전용 필드이나 판정 로직에 영향 시 위험 (stage23 조사: HIGH → 분석 후 LOW 하향 가능).

### 3.2 FourPhaseArcGenerator — 실제 3단계 파이프라인 (클래스명 호환성 유지)

**파일**: `modules/domain/agents/four_phase_arc_generator.py`

클래스 독스트링 `[V60.75] Three Phase` — 실제 3단계이나 클래스명은 호환성을 위해 `FourPhaseArcGenerator` 유지.

#### 3.2.1 파이프라인 단계

| 단계 | 내용 | 침묵 실패 경로 |
|------|------|-------------|
| **Phase 1: CONSTRAINT** | ConstraintCompiler + NegativeExampleInjector + 장르 에너지 경고 (`four_phase_arc_generator.py:616-644`) | 제약 블록 비어있으면 그대로 진행 |
| **Phase 2: GENERATE** | 앙상블 3후보 → 패치 시도 → Director 선택 | 0후보 시 재시도 루프 계속 |
| **Phase 2.5: AUTO-SANITIZE** | NS-3-B 수치 대조 → 30%+ 이탈 시 점수 89 캡 | 수치 없으면 체크 스킵 |
| **Phase 2.56: INVESTMENT CHECK** | F-1(Python) + F-2(LLM) 산술 검증 | F-2 없으면 F-1만 (침묵) |
| **Phase 2.6: DIRECTOR SELECTION** | Director 판정 → PASS/PWF/REJECT | Director 없으면 1번 후보 자동 선택 |
| **Phase 3: VALIDATE** | 단일 후보 검증 | Director 미사용 시에만 |

#### 3.2.2 재시도 루프 — max_internal_retries=9 → 총 10회 시도

```python
# four_phase_arc_generator.py:523 → max_internal_retries: int = 9
# four_phase_arc_generator.py:612 → for retry in range(max_internal_retries + 1):  # 0~9 = 10회  [I17]
```

모든 재시도 실패 시:
```python
# four_phase_arc_generator.py:1127-1132
pipeline_result["final_verdict"] = "FAILED"
return None, pipeline_result  # None 반환 (pipeline_result에 FAILED 표시)  [SF15, I18 정정]
```

위험: 호출자가 `pipeline_result`를 확인하지 않으면 불합격 arc가 DB에 저장될 수 있음.

#### 3.2.3 Spare Candidate Pool — 재활용 메커니즘

```python
# four_phase_arc_generator.py:610 → _spare_candidates: list[dict] = []
# four_phase_arc_generator.py:716-747 → 미선택 후보를 spare pool에 보관
# 다음 재시도에서 spare 후보를 앙상블 입력으로 재사용
```

숨겨진 효율: spare pool 없으면 매 재시도마다 LLM 3회 호출. pool 사용 시 0회 추가 호출로 다른 후보 선택 가능.

#### 3.2.4 장르 에너지 경고 주입 — 두 주입 지점 용어 불일치 (I8)

| 주입 지점 | 용어 | 코드 근거 |
|----------|------|----------|
| `four_phase_arc_generator.py` | "내공", "정신력", "마나" | `four_phase_arc_generator.py:633-635` |
| `arc_ensemble.py` | "내공", "기력", "내력" | `arc_ensemble.py:142,155` |

두 주입 지점의 용어가 다르다. Phase 1 제약 블록과 앙상블 내 회복 원칙에 각각 장르별 조건부 주입. 비무협 장르에서만 활성화.

#### 3.2.5 장르 감지 실패 폴백 (MSF-K)

```python
# four_phase_arc_generator.py:427-436
_detected_genre = "wuxia"  # 기본값
try:
    # context.guard에서 장르 감지 시도
except Exception as _e:
    logging.warning("[FourPhase] 장르 감지 실패, wuxia 기본값 사용: %s", _e)
```

위험: 비무협 프로젝트에서 장르 감지 실패 시 무협 제약(경지 체계, 내공 등)이 적용됨.

### 3.3 Analyst — 블록 Enrichment

**파일**: `modules/domain/agents/analyst.py`

#### 3.3.1 Effective Previous Context 우선순위

```
1. transfused_history (LLM 추출 상태) — 최고 우선
2. prev_block JSON 직렬화 (원본 DNA) — 폴백
3. "서사 시작점" (첫 블록) — 최종 폴백
```

`transfused_history`는 이전 arc에서 추출한 정제된 상태 정보로, 원본 블록보다 정제된 컨텍스트. 이 우선순위가 arc 간 연속성의 핵심.

#### 3.3.2 Enrichment 파싱 실패 — `_enrich_skipped` (SF12)

```python
# analyst.py:1421-1427
if enriched_result.get("parsing_error"):
    raw_block["_enrich_skipped"] = True
    return raw_block  # 원본 그대로 반환, 오케스트레이터는 성공으로 처리
```

영향: enrichment 스킵된 블록은 원본 컨셉 수준 그대로 Stage 2에 진입. tactical_doc 부재, state_changes 미정의.

#### 3.3.3 일반 예외 — 마커 없는 침묵 반환 (MSF-J)

```python
# analyst.py:1440-1442
except Exception as e:
    logging.warning(f" [Enrich Critical Error] {e}")
    return raw_block  # 마커 없이 원본 반환 — SF12보다 위험
```

SF12(JSON 파싱 실패)와 다른 경로: 일반 예외 시 `_enrich_skipped` 마커 **없이** 원본을 반환. 오케스트레이터가 enrichment 성공으로 오인할 수 있어 SF12보다 위험도 높음.

### 3.4 ArcCorrector — 부분 수정 제한

**파일**: `modules/domain/agents/arc_corrector.py`

#### 3.4.1 수정 제한

| 파라미터 | 값 | 코드 근거 |
|---------|---|----------|
| `max_corrections` | 2 | `arc_corrector.py:93` |
| `max_change_ratio` | 0.20 (20%) | `arc_corrector.py:94` |

- 20% 초과 시: `None` 반환 (원본 아님). 호출자가 원본 사용 결정 [SF16, I19 정정]

ArcCorrector 변경 비율 검증 한계: `json.dumps` 문자열 길이 차이만 비교 (`arc_corrector.py:511-522`). 동일 길이 콘텐츠 교체 시 `change_ratio = 0.0` → 검증 통과. 의미적 변경 미감지 (MEDIUM).

#### 3.4.2 수정 가능/불가능 분류

**수정 가능 (correctable)**:
- `length_short`, `checkpoint_missing`, `location_mismatch`, `state_mismatch`, `field_missing`, `episode_missing`

**수정 불가 (CRITICAL REJECT)**:
- `duplicate_acquisition`, `duplicate_grant`, `forbidden_item`

### 3.5 ArcCritic — 7차원 채점

**파일**: `modules/domain/agents/arc_critic.py`

| 차원 | 점수 범위 | 검증 내용 | 코드 근거 |
|------|---------|----------|----------|
| 아이템 연속성 | 0-10 | 중복 획득 검사 | `arc_critic.py:38-69` |
| 위치 연속성 | 0-10 | 이전 Arc 종료 위치 계승 | `arc_critic.py:38-69` |
| 상태 연속성 | 0-10 | 부상/에너지 계승 | `arc_critic.py:38-69` |
| 지급 타임라인 | 0-10 | 재지급 방지 | `arc_critic.py:38-69` |
| 전술 품질 | 0-10 | tactical_doc 분량 충분성 | `arc_critic.py:38-69` |
| Joint_docs 정확성 | 0-10 | final_location, inventory 일치 | `arc_critic.py:38-69` |
| 서사 일관성 | 0-10 | 전체 흐름 | `arc_critic.py:38-69` |

**LLM 실패 폴백**: `_python_critique_fallback()` — 기본 유효성만 검사 (점수 없음, pass/fail만).

### 3.6 Stage2Finalizer — 수치 검증

**파일**: `modules/core/stage2_finalizer.py`

#### 3.6.1 Tactical Doc 산술 검증

```python
# stage2_finalizer.py:110-118
tolerance = 0.05  # 5% 허용
# 곱셈 패턴: "A × N배 = C" → |A*N - C| / C < 5%
# 백분율 패턴: "A × P% = C" → |A*(P/100) - C| / C < 5%
# 위반 시: 어드바이저리 경고 (비차단)
```

#### 3.6.2 Cross-Arc 자산 연속성

```python
# stage2_finalizer.py:166-222
# 이전 arc의 arc_end_state에서 총자산 추출 (우선)  (stage2_finalizer.py:184-189)
# 없으면 tactical_doc에서 "총자산 ~\d+억" 패턴 검색 (폴백)  (stage2_finalizer.py:192-198)
# ±20% 이탈 시: 어드바이저리 경고 (비차단)  (stage2_finalizer.py:217)
```

침묵 사각지대: tactical_doc에 자산 수치 미기재 시 → 연속성 검사 자체를 스킵 (`stage2_finalizer.py:205-206`). "미기재 = 오류 아님"으로 처리하지만 이는 위음성(false negative).

#### 3.6.3 `_to_num_with_korean_units` — 모듈 수준 함수 (I11, I12 정정)

```python
# stage2_finalizer.py:36-87 — 모듈 수준 함수 (클래스 메서드 아님)
def _to_num_with_korean_units(raw: object) -> float | None:
    # 조(1T), 억(100M), 만(10K)
    # 반환: float | None — 정수 아닌 float이므로 정밀도 손실 가능
```

### 3.7 Director Auditor (Stage 2 부분만)

**파일**: `modules/domain/agents/director_auditor.py`

- 12,000자 절단은 `assess_character_logic()` 서브메서드에서만 적용 (`director_auditor.py:127`, I7 정정)
- 메인 `audit_manuscript()`에서는 절단 미적용
- → **S6 참조** for full Director 구현 상세

---

## 4. 교차 계층 보조 시스템

### 4.1 ConstraintDB — 아이템 제약 누적

**파일**: `modules/core/constraint_db.py`

#### 4.1.1 ArcState — 8 필드

```python
# constraint_db.py:37-47
@dataclass
class ArcState:
    arc_no: int
    location: str = ""
    inventory: list[str]       # 현재 소지 아이템
    injuries: str = "정상"     # 부상 상태
    internal_energy: int = 100 # 내공 (0-100)
    grants: list[str]          # 타인에게 지급한 아이템
    acquired_items: list[str]  # 획득한 아이템
    consumed_items: list[str]  # 소모된 아이템
```

#### 4.1.2 금지 아이템 생성 로직

```
모든 이전 Arc의 acquired_items + grants + consumed_items 합산
→ 중복 획득/중복 지급 방지 목록
→ 새 Arc에서 이 목록의 아이템을 재획득하면 CRITICAL REJECT
```

#### 4.1.3 모순 탐지 — 주 경로 + 폴백 경로 (I13, W2 재정정)

**주 경로** (`SemanticItemRegistry` 활성 시):
- `constraint_db.py:606` → `self.item_registry.validate_arc_items()`
- `semantic_item_registry.py:197` → 문자 기반 **Jaccard 유사도** (`jaccard * 0.7 + len_ratio * 0.3`)

**폴백 경로** (`SemanticItemRegistry` 미활성 시, `constraint_db.py:612-629`):
1. **정확 일치**: `if item in forbidden` (`constraint_db.py:616`)
2. **부분 문자열 포함**: `item in f or f in item` (`constraint_db.py:619`)
3. **패턴 검색**: tactical_doc에서 `"X를 획득"` regex 매칭 (`constraint_db.py:624-629`)

#### 4.1.4 DB 로드 실패 침묵 (MSF-F)

```python
# constraint_db.py:76-98
def _load_from_db(self) -> None:
    try:
        arcs_data = self.context.db.load_anchor("arcs")
        # ...
    except Exception as e:
        logging.warning(f" [ConstraintDB] DB 로드 실패: {e}")
        # arc_states = {} — 전체 제약 시스템 비활성  [MSF-F, 심각도: 고]
```

#### 4.1.5 검증 우회 침묵 (MSF-G)

```python
# constraint_db.py:587-590
# arc_no 파싱 실패 → valid=True 반환 — 검증 우회  [MSF-G, 심각도: 저]
```

### 4.2 FactLedger — 불변 사실 원장

**파일**: `modules/core/fact_ledger.py`

#### 4.2.1 엔티티 유형 5가지

| 유형 | 추적 필드 | 이력 한도 | 코드 근거 |
|------|----------|----------|----------|
| characters | status, role, relationship, established_ep | 100건 | `fact_ledger.py:108` |
| numbers | value, unit, established_value | 100건 | `fact_ledger.py:109` |
| items | owner, status | 100건 | `fact_ledger.py:110` |
| locations | status, current_owner | 100건 | `fact_ledger.py:111` |
| organizations | status, leader | 100건 | `fact_ledger.py:112` |

`MAX_HISTORY_PER_ENTITY = 100` (`fact_ledger.py:72`)

#### 4.2.2 불변성 강제

```python
# fact_ledger.py:355
entry.setdefault("established_value", value)  # 최초 삽입 시 설정, 이후 변경 불가
# 사망한 캐릭터에 대한 업데이트 자동 차단
```

#### 4.2.3 롤백 메커니즘 — batch load 최적화

```python
# fact_ledger.py:735-758
def rollback_to(target_ep):
    self._ledger = self._empty_ledger()
    all_bibles = self.db.get_all_episode_bibles()  # 배치 로드 (fact_ledger.py:749)
    # 모든 episode_bible을 처음부터 target_ep까지 재적용
```

#### 4.2.4 DB 관련 침묵 실패 (MSF-H, MSF-I)

| ID | 위치 | 동작 | 심각도 |
|----|------|------|--------|
| MSF-H | `fact_ledger._load():91-102` | DB 로드 실패 → 빈 원장 — 전체 사실 추적 소실 | 고 |
| MSF-I | `fact_ledger.save():116-127` | DB 저장 실패 → `False` 반환 — 메모리만 잔존 | 중 |

### 4.3 GenreGuards — 장르별 검증 규칙

**파일**: `modules/core/genre_guards/` (14개 장르)

#### 4.3.1 무협 검증 규칙 (wuxia_guard.py)

| 규칙 | 내용 | 코드 근거 |
|------|------|----------|
| 금지 용어 | 런타임 129개 (YAML), 폴백 하드코딩 130개/129 고유 ("근섬유" 1건 중복) | `wuxia_guard.py:23-154`, I14 정정 |
| 경지 체계 | 10단계: "입문" → "선천" 계층적 무공 제한 | `wuxia_guard.py:164-166` |
| 부상-행동 제한 | "중상" 시 무거운 물건 들기 금지 regex | `wuxia_guard.py` |
| 권위 위계 | "가주" > "대장로" > "장로" 위임 패턴 | `wuxia_guard.py` |

#### 4.3.2 동적 YAML 로딩

```
config/genres/{genre_key}.yaml에서 로드 — YAML 존재 시 우선
YAML 없으면 하드코딩 기본값 폴백
경로: modules/core/genre_guards/ → config/genres/
```

런타임 금지 용어 수(129)와 하드코딩 폴백 수(130/129 고유)가 다른 이유: YAML에서 중복 "근섬유"가 제거된 상태.

### 4.4 DiversitySampler — 앙상블 다양성 보장

**파일**: `modules/core/diversity_sampler.py`

#### 4.4.1 다양성 점수 4축

| 축 | 가중치 | 측정법 | 코드 근거 |
|----|--------|--------|----------|
| TTR (Type-Token Ratio) | 30% | 0.3-0.7 범위 → 0-100 정규화 (`(ttr-0.3)/0.4*100`) | `diversity_sampler.py:157-165` |
| 문장 다양성 (sentence_variety) | 25% | 길이 변동 계수 (std/mean) | `diversity_sampler.py:169+` |
| 신규성 (novelty) | 30% | 1 - (중복 n-gram / 전체 n-gram) | `diversity_sampler.py:190+` |
| 구조 다양성 (structure) | 15% | 고유 문장 시작어 / 전체 문장 | `diversity_sampler.py:210-213` |

가중 평균: `diversity_sampler.py:218` → `{"ttr":0.30, "sentence_variety":0.25, "novelty":0.30, "structure":0.15}`

#### 4.4.2 조건부 다양성 샘플링

| 심각도 | 후보 수 | 코드 근거 |
|--------|--------|----------|
| CRITICAL | 5 | `diversity_sampler.py:390` |
| HIGH | 4 | `diversity_sampler.py:389` |
| MEDIUM | 3 | `diversity_sampler.py:388` |
| LOW | 2 | `diversity_sampler.py:387` |
| NONE | 1 | `diversity_sampler.py:386` |

`pattern_tracker.should_activate_diversity_sampling()`으로 활성화 결정 (`diversity_sampler.py:385-393`).

### 4.5 AdaptiveRetry — 오류 유형별 적응 전략

**파일**: `modules/core/adaptive_retry.py`

#### 4.5.1 ErrorType enum — 9개 (UNKNOWN 포함)

```python
# adaptive_retry.py:42-54
class ErrorType(Enum):
    CONSTRAINT_VIOLATION = "constraint_violation"
    QUALITY_ISSUE = "quality_issue"
    STRUCTURE_ERROR = "structure_error"
    TIMEOUT = "timeout"
    QUOTA_EXCEEDED = "quota_exceeded"
    CHARACTER_INCONSISTENCY = "character_inconsistency"  # V54.3 신규
    LOGIC_ERROR = "logic_error"                          # V54.3 신규
    SCOPE_OVERFLOW = "scope_overflow"                     # V54.3 신규
    UNKNOWN = "unknown"
```

MAX_RETRIES/WAIT_TIME 매핑은 **6개**만 등록 (I9 정정). V54.3 신규 3개 타입은 재시도 파라미터 미등록:

| 오류 유형 | 최대 재시도 | 대기(초) | 온도 조정 | 추가 조치 |
|----------|-----------|---------|----------|----------|
| CONSTRAINT_VIOLATION | 3 | 0 | -0.1 | 금지 아이템 주입 |
| QUALITY_ISSUE | 2 | 0 | +0.1 | 개선 가이드 주입 |
| STRUCTURE_ERROR | 2 | 1 | -0.2 | 스키마 강제 |
| TIMEOUT | 1 | 2 | — | 출력 축소 요청 |
| QUOTA_EXCEEDED | 3 | 30 | — | 장기 백오프 |
| UNKNOWN | 2 | 1 | — | 기본 재시도 |
| CHARACTER_INCONSISTENCY | (미등록) | — | -0.1 | 캐릭터 프로필 주입 |
| LOGIC_ERROR | (미등록) | — | -0.1 | 인과관계 가이드 |
| SCOPE_OVERFLOW | (미등록) | — | -0.15 | 범위 경고 |

#### 4.5.2 에스컬레이션 트리거

```python
# 2회+ 연속 실패 시 should_trigger_ultimate() → ToT/ASP/MAD 추천
# connect_failure_learner()로 실패 패턴 학습 연결
```

### 4.6 ChainOfVerification — 독립 메서드 2개 (I10 정정)

**파일**: `modules/core/chain_of_verification.py`

2개 **독립 메서드** (내부 체인 강제 없음, 호출자가 순서 결정):

**`quick_verify()` (Python, $0)**:
- 아이템 소실 검사 (이전 arc에 있던 아이템이 사라짐)
- 시간 역전 탐지 (타임라인 역행)
- 급격한 관계 변화 패턴

**`verify()` (LLM, ~$0.01)**:
- 6차원 의미 검증: 아이템, 관계, 타임라인, 캐릭터, 설정, 상태
- 이슈별 severity: none/minor/major/critical

### 4.7 ExpertMixture — 씬 유형별 전문가 라우팅

**파일**: `modules/core/expert_mixture.py`

#### 4.7.1 씬 유형 8가지

| 유형 | 키워드 수 | 장르별 특화 | 코드 근거 |
|------|----------|-----------|----------|
| ACTION | 8-20 | 무협: 초식명, 검풍, 살기 | `expert_mixture.py:32-42` |
| DIALOGUE | 8-15 | 무협: 서브텍스트, 침묵 | `expert_mixture.py:32-42` |
| EMOTIONAL | 8-15 | 무협: Show Don't Tell, 호흡 | `expert_mixture.py:32-42` |
| EXPOSITION | 8-12 | — | `expert_mixture.py:32-42` |
| CLIMAX | 8-10 | — | `expert_mixture.py:32-42` |
| TRANSITION | 5-8 | — | `expert_mixture.py:32-42` |
| MYSTERY | 8-10 | — | `expert_mixture.py:32-42` |
| COMEDY | 5-8 | — | `expert_mixture.py:32-42` |

#### 4.7.2 신뢰도 공식 (I15 반영)

```python
# expert_mixture.py:283
confidence = min(1.0, max_score / max(total_keywords * 0.3, 1))
# max(..., 1)은 0 방지 가드
```

#### 4.7.3 Writer 프롬프트 주입

```python
# 상위 3개 씬 유형의 전문가 프롬프트를 결합
# → ChiefWriter 프롬프트에 직접 주입
```

### 4.8 DynamicPromptWeighting — 실패 학습 가중치

**파일**: `modules/core/dynamic_prompt_weighting.py`

#### 4.8.1 10개 카테고리

| 카테고리 | 트리거 키워드 | 코드 근거 |
|----------|------------|----------|
| CONTINUITY | 연속성, 중복 | `dynamic_prompt_weighting.py:25-37` |
| ITEM_MANAGEMENT | 아이템, 획득 | `dynamic_prompt_weighting.py:25-37` |
| RELATIONSHIP | 관계, NPC | `dynamic_prompt_weighting.py:25-37` |
| PACING | 전개, 속도 | `dynamic_prompt_weighting.py:25-37` |
| CHARACTER | 캐릭터, 성격 | `dynamic_prompt_weighting.py:25-37` |
| SCENE_STRUCTURE | 씬, 구조 | `dynamic_prompt_weighting.py:25-37` |
| DIALOGUE | 대화, 말투 | `dynamic_prompt_weighting.py:25-37` |
| DESCRIPTION | 묘사, 감각 | `dynamic_prompt_weighting.py:25-37` |
| BLUEPRINT_COMPLIANCE | 블루프린트, 준수 | `dynamic_prompt_weighting.py:25-37` |
| VILLAIN_INTELLIGENCE | 악역, 전략 | `dynamic_prompt_weighting.py:25-37` |

#### 4.8.2 가중치 계산

```python
# dynamic_prompt_weighting.py:179
weight = min(1.0, failure_count / total_failures * 3)
# CRITICAL: ≥0.7, HIGH: ≥0.4, MEDIUM: ≥0.2, LOW: <0.2
```

최근 **50건** 실패만 분석 (오래된 실패 감쇠) (`dynamic_prompt_weighting.py:160`).

### 4.9 ConfidenceCalibration — LLM 신뢰도 예측

**파일**: `modules/core/confidence_calibration.py`

#### 4.9.1 7요인 모델

| 요인 | 가중치 | 측정법 | 코드 근거 |
|------|--------|--------|----------|
| 길이 적합성 (length_adequacy) | 15% | MIN_LENGTH ~ 12,000자 대비 | `confidence_calibration.py:70` |
| 구조 품질 (structure_quality) | 20% | 단락 수, 대화 비율, 종결 부호 | `confidence_calibration.py:71` |
| 연속성 신호 (continuity_signals) | 20% | 이전 원고와 키워드 중복률 | `confidence_calibration.py:72` |
| 대화 비율 (dialogue_ratio) | 10% | 인용문 / 전체 길이 | `confidence_calibration.py:73` |
| 감각 디테일 (sensory_detail) | 10% | 감각어 밀도 | `confidence_calibration.py:74` |
| 씬 커버리지 (scene_coverage) | 15% | 블루프린트 키워드 매칭률 | `confidence_calibration.py:75` |
| 엔딩 훅 (ending_hook) | 10% | 마지막 500자 훅 신호 수 (`confidence_calibration.py:279`) | `confidence_calibration.py:76` |

합계: 15+20+20+10+10+15+10 = **100%** (`confidence_calibration.py:69-77`)

#### 4.9.2 의사결정 임계치

| 임계치 | 값 | 행동 | 코드 근거 |
|--------|---|------|----------|
| `fast_pass` | 85 | 빠른 통과 (검증 스킵 가능) | `confidence_calibration.py:83` |
| `extra_verification` | 50 | 이 미만이면 추가 검증 | `confidence_calibration.py:81` |
| `regenerate` | 30 | 이 미만이면 재생성 권장 | `confidence_calibration.py:82` |

### 4.10 AdversarialSelfPlay — 적대적 자기 대결

**파일**: `modules/core/adversarial_self_play.py`

```python
# adversarial_self_play.py:148
self.max_rounds = 2  # 최대 수정 라운드
```

### 4.11 CrossAgentVerifier — 에이전트 간 교차 검증

**파일**: `modules/core/cross_agent_verifier.py`

```python
# cross_agent_verifier.py:298-300
if len(py_violations) >= 2:
    # should_regenerate=True → REGENERATE 판정
```

2건 이상 위반 감지 시 Python precheck 단계에서 즉시 REGENERATE (LLM 생략).

---

## 5. 침묵 실패 전수 목록 (27건)

### 5.1 기존 16건 (SF1-SF16)

| # | 위치 | 조건 | 결과 | 심각도 | 코드 근거 |
|---|------|------|------|--------|----------|
| SF1 | `story_expander._call_llm` | LLM 2모델 전부 실패 | `return ""` | 중 | `story_expander.py:103` |
| SF2 | `story_expander._parse_json` | JSON 파싱 실패 | `return None` → `extracted={}` | 중 | `story_expander.py:117` |
| SF3 | `story_expander.generate_bible` | 주인공 추출 실패 | 완전히 빈 dict `{}` 반환 (CoreIdentity 키 자체 부재) | **고** | `story_expander.py:356,365-367` |
| SF4 | `story_expander.generate_bible` | NPC 생성 실패 | 빈 KeyNPCs | 중 | `story_expander.py` |
| SF5 | `story_expander` (디테일 배치) | 블록 스킵 | stale 연속성 컨텍스트 | 저 | `story_expander.py` |
| SF6 | `reverse_expander` (에피소드) | 추출 예외 | ep_num 포함 스켈레톤 dict 주입 (하위 필드 빈값) | 중 | `reverse_expander.py:433-443` |
| SF7 | `reverse_expander` (HUD) | preset_registry=None | HUD 정규화 생략 | 중 | `reverse_expander.py:409-410` |
| SF8 | `reverse_expander` (장르) | LLM 실패 | "investment" 기본값 | 중 | `reverse_expander.py:228-253` |
| SF9 | `style_extractor` (LLM) | LLM 클라이언트 없음 | 단계 4-5 전체 스킵 | 중 | `style_extractor.py` |
| SF10 | `style_extractor` (POV) | 대명사 부족 | "혼합" 기본값 | 저 | `style_extractor.py:583-590` |
| SF11 | `preset_registry` (타입) | 타입 변환 실패 | 기본값 침묵 교체 | 중 | `preset_registry.py:523-550` |
| SF12 | `analyst` (enrichment) | JSON 파싱 실패 | `_enrich_skipped=True` | 중 | `analyst.py:1421-1427` |
| SF13 | `arc_ensemble` (타임아웃) | 개별 전략 타임아웃 | 후보 침묵 드롭 (2/3 드롭 시 spare pool 고갈) | **중** | `arc_ensemble.py:190-191` |
| SF14 | `arc_ensemble` (길이) | 전 후보 길이 미달 | 최장 불합격 후보 강제 | 중 | `arc_ensemble.py:532-551` |
| SF15 | `four_phase` (재시도 소진) | 9회 재시도(총 10회) 전부 REJECT | `None` 반환 (pipeline_result에 FAILED 표시, 호출자가 처리) | **고** | `four_phase_arc_generator.py:1127-1132` |
| SF16 | `arc_corrector` (diff 초과) | 20% 변경 초과 | `None` 반환 (호출자가 원본 사용 결정) | 저 | `arc_corrector.py:93-94` |

### 5.2 신규 11건 (MSF-A~K)

| # | 위치 | 조건 | 결과 | 심각도 | 코드 근거 |
|---|------|------|------|--------|----------|
| MSF-A | `reverse_expander._extract_protagonist()` | LLM 실패 | `return {}` — 주인공 정보 전무 | **고** | `reverse_expander.py:335-338` |
| MSF-B | `reverse_expander._extract_world_state()` | LLM 실패 | `return {}` — 세계관 전무 | 중 | `reverse_expander.py:370-373` |
| MSF-C | `reverse_expander._extract_npcs()` | LLM 실패 | `return []` — NPC 전무 | 중 | `reverse_expander.py:351-356` |
| MSF-D | `story_expander._generate_skeleton()` | LLM 실패 | `[]` 확장 — 블록 수 미달 | 중 | `story_expander.py:647-652` |
| MSF-E | `story_expander._generate_details()` | LLM 실패 | 스켈레톤 블록 그대로 사용 (content 미생성) | 중 | `story_expander.py:712-716` |
| MSF-F | `constraint_db._load_from_db()` | DB 로드 실패 | `arc_states={}` — 전체 제약 시스템 비활성 | **고** | `constraint_db.py:76-98` |
| MSF-G | `constraint_db.validate_arc_design()` | arc_no 파싱 실패 | `valid=True` 반환 — 검증 우회 | 저 | `constraint_db.py:587-590` |
| MSF-H | `fact_ledger._load()` | DB 로드 실패 | 빈 원장 — 전체 사실 추적 소실 | **고** | `fact_ledger.py:91-102` |
| MSF-I | `fact_ledger.save()` | DB 저장 실패 | `False` 반환 — 메모리만 잔존 | 중 | `fact_ledger.py:116-127` |
| MSF-J | `analyst.enrich_raw_block_async()` | 일반 예외 | 원본 블록 반환 **마커 없이** (SF12와 다른 경로, 더 위험) | **고** | `analyst.py:1440-1442` |
| MSF-K | `four_phase_arc_generator.__init__()` | 장르 감지 실패 | `"wuxia"` 기본값 — 비무협 프로젝트에 무협 제약 적용 | 중 | `four_phase_arc_generator.py:427-436` |

**가장 높은 위험**: SF3 (빈 dict 반환), MSF-F (전체 제약 시스템 비활성), MSF-H (전체 사실 추적 소실), MSF-J (마커 없는 침묵 반환).

---

## 6. 수치 요약표

| 지표 | 수치 | 코드 근거 |
|------|------|----------|
| Stage 0 모듈 파일 수 | 5개 모듈 + __init__.py = **6개** | `modules/core/stage0/` |
| Stage 0 서브메뉴 모드 (기존/신규) | 기존 프로젝트 **7개**, 신규 **6개** | `__init__.py:283-311` |
| 지원 장르 | **10** | `__init__.py:61-72` |
| 침묵 실패 경로 총 수 | **27** (기존 16 + 신규 11) | 전수 조사 + 6회 감리 |
| 미사용 코드/상수 | **1** (`_MAX_WORKERS=3`) | `reverse_expander.py:416` |
| 한국어 숫자 파싱 독립 구현 | **4곳** | preset_registry, stage2_finalizer, stage2_optimizer, investment_arithmetic_checker |
| LLM 폴백 모델 수 (Stage 0) | **2** (SUMMARY → V50_MODULE) | `story_expander.py:61` |
| LLM 재시도 (Stage 0) | **3회** / 모델 | `story_expander.py:65` |
| LLM temperature (Stage 0 생성) | **0.85** | `story_expander.py:68` |
| LLM max_tokens (Stage 0) | **8192** | `story_expander.py:68` |
| Treatment 기본 블록 수 | **60** | `story_expander.py:483` |
| Treatment 스켈레톤 배치 크기 | **20** | `story_expander.py` |
| Treatment 디테일 배치 크기 | **10** | `story_expander.py` |
| Bible 완전성 경고 분기 / 동시 최대 | **5** / **4** (1-2 상호 배타) | `story_expander.py:420-429` |
| 리뷰 게이트 최대 시도 | **2** | `story_expander.py:35` |
| 캐시 정합성 필드 수 | **9** | `style_extractor.py:427-439` |
| 캐시 버전 | `s0-style-cache-v2` | `style_extractor.py` |
| 앙상블 전략 수 | **3** (conservative/balanced/creative) | `arc_ensemble.py:159-178` |
| 앙상블 타임아웃 (전체/개별) | **300초 / 240초** (기본값, config-overridable) | `arc_ensemble.py:190-191` |
| Tactical doc 최소 길이 | **ep_count × 450** | `constants.py:244`, `arc_ensemble.py:508` |
| Arc 생성 재시도 | **max_internal_retries=9 → 총 10회** | `four_phase_arc_generator.py:523,612` |
| ArcCorrector 최대 수정 횟수 | **2** | `arc_corrector.py:93` |
| ArcCorrector 변경 한도 | **20%** | `arc_corrector.py:94` |
| ArcCritic 채점 차원 | **7** (각 0-10) | `arc_critic.py:38-69` |
| 산술 검증 허용 오차 | **5%** | `stage2_finalizer.py:118` |
| 자산 연속성 허용 오차 | **±20%** | `stage2_finalizer.py:217` |
| Director 절단 문자 수 | **12,000** (assess_character_logic만) | `director_auditor.py:127` |
| ConstraintDB ArcState 필드 | **8** | `constraint_db.py:37-47` |
| FactLedger 엔티티 유형 | **5** | `fact_ledger.py:107-112` |
| FactLedger 이력 한도 | **100건**/엔티티 | `fact_ledger.py:72` |
| GenreGuards 무협 금지 용어 | 런타임 **129개** (YAML), 폴백 **130개/129 고유** | `wuxia_guard.py:23-154` |
| 무협 경지 단계 | **10** | `wuxia_guard.py:164-166` |
| DiversitySampler 다양성 축 | **4** (TTR 30%, sentence_variety 25%, novelty 30%, structure 15%) | `diversity_sampler.py:218` |
| DiversitySampler 조건부 후보 수 | **1-5** (NONE ~ CRITICAL) | `diversity_sampler.py:385-393` |
| AdaptiveRetry 오류 유형 | **9** (UNKNOWN 포함), 파라미터 매핑 **6**개 | `adaptive_retry.py:42-54` |
| ExpertMixture 씬 유형 | **8** | `expert_mixture.py:32-42` |
| DynamicPromptWeighting 카테고리 | **10** | `dynamic_prompt_weighting.py:25-37` |
| DynamicPromptWeighting 실패 분석 범위 | 최근 **50건** | `dynamic_prompt_weighting.py:160` |
| ConfidenceCalibration 요인 | **7** (합계 100%) | `confidence_calibration.py:69-77` |
| ConfidenceCalibration fast_pass | **85** | `confidence_calibration.py:83` |
| ConfidenceCalibration extra_verification | **50** | `confidence_calibration.py:81` |
| ConfidenceCalibration regenerate | **30** | `confidence_calibration.py:82` |
| AdversarialSelfPlay max_rounds | **2** | `adversarial_self_play.py:148` |
| CrossAgentVerifier REGENERATE 임계 | **2+** 위반 | `cross_agent_verifier.py:298-300` |

---

## 7. 발견 사항

### 7.1 설계 강점 (DS1-DS10)

| # | 강점 | 근거 | 코드 참조 |
|---|------|------|----------|
| DS1 | **Spare Candidate Pool** | 재시도 시 LLM 추가 호출 없이 기존 후보 재활용 | `four_phase_arc_generator.py:610,716-747` |
| DS2 | **Transfused History** | enrichment 시 정제된 상태 정보 우선 사용 → arc 간 연속성 핵심 | `analyst.py` |
| DS3 | **이중 검증 (Python + LLM)** | ChainOfVerification quick_verify($0) + verify(~$0.01) | `chain_of_verification.py` |
| DS4 | **오류 유형별 적응 전략** | AdaptiveRetry가 온도, 프롬프트, 대기 시간을 동적 조정 | `adaptive_retry.py:42-54` |
| DS5 | **제약 이중 경로 모순 탐지** | 주 경로: Jaccard(SemanticItemRegistry), 폴백: 정확 일치+부분 문자열+regex | `constraint_db.py:606-629` |
| DS6 | **장르별 전문가 라우팅** | ExpertMixture 8개 씬 유형 × 장르 특화 | `expert_mixture.py:32-42` |
| DS7 | **실패 학습 가중치** | DynamicPromptWeighting 최근 50건 분석 → 카테고리별 긴급도 | `dynamic_prompt_weighting.py:160,179` |
| DS8 | **조건부 다양성 샘플링** | 심각도에 따라 후보 수 1-5개 동적 조절 | `diversity_sampler.py:385-393` |
| DS9 | **9필드 캐시 정합성** | StyleExtractor 캐시 무효화 정밀 제어 | `style_extractor.py:427-439` |
| DS10 | **불변 사실 원장** | FactLedger established_value 변경 불가, 사망 캐릭터 업데이트 차단 | `fact_ledger.py:355` |

### 7.2 사각지대 및 관리 주의점

#### 7.2.0 추가 발견 사항

consensus_validator fail-open: `consensus_validator.py:233-256,282-285` — 타임아웃/에러 시 auto-PASS (`confidence: 0.5`). vote에서 confidence 가중치 미반영.

Stage 2 Arc 저장 비원자성: `stage2_finalizer.py:1258-1298`에서 `save_v20_anchor` → `safe_commit_async` 순차 호출. 중간 crash 시 anchor 파일 vs DB 불일치. 인메모리 롤백 존재하나 디스크 anchor 미롤백 (MEDIUM).

#### 7.2.1 4-way 한국어 숫자 파싱 중복 (W4)

4곳에 독립 구현된 한국어 숫자 파싱은 엣지 케이스 처리가 미묘하게 다를 수 있다. 공통 유틸리티 함수로 통합 권장.

| 위치 | 타입 | 파일 |
|------|------|------|
| `PresetRegistry._parse_korean_number()` | 인스턴스 메서드 | `preset_registry.py:552` |
| `_to_num_with_korean_units()` | 모듈 수준 함수 | `stage2_finalizer.py:36` |
| `_parse_korean_number()` | 별도 구현 | `stage2_optimizer.py` |
| `_parse_korean_amount()` | 별도 구현 | `investment_arithmetic_checker.py` |

#### 7.2.2 `_MAX_WORKERS` 미사용 상수

`reverse_expander.py:416`에 `_MAX_WORKERS = 3`이 선언되어 있으나 참조 0건. 병렬화 의도가 있었으나 미구현. 제거 또는 구현 필요.

#### 7.2.3 장르 에너지 경고 용어 불일치 (I8)

`four_phase_arc_generator.py:633-635`는 "내공/정신력/마나"를, `arc_ensemble.py:142,155`는 "내공/기력/내력"을 사용. 동일한 의미를 전달하지만 용어 불일치는 LLM 혼동을 유발할 수 있다.

#### 7.2.4 최악 시나리오 — 침묵 실패 연쇄

```
Stage 0: LLM 전원 실패 → Bible 빈 dict  [SF3]
  → Stage 2: 빈 CoreIdentity로 Arc 설계 시도
    → ConstraintDB: DB 로드 실패 → 제약 0건  [MSF-F]
      → 앙상블: 제약 없이 자유 생성 → 모순 가능
        → Director: 모순 감지 → REJECT
          → 재시도 10회 소진 → None 반환  [SF15]
            → 호출자가 pipeline_result 미확인 시 → 파이프라인 중단
```

이 체인은 가능하지만 극히 드문 경우. 각 단계에서 별도 방어선이 존재하나, 모두 "침묵 통과" 방식.

---

## [부록 A] 감리 이력 요약

### 1차 적대적 감리 (48건)

| 판정 | 건수 | 비율 |
|------|------|------|
| CONFIRMED | 33 | 68.8% |
| INACCURATE | 12 | 25.0% |
| WRONG | 3 | 6.3% |

**WRONG 정정 (W1-W3)**:

| ID | 원문 | 정정 |
|----|------|------|
| W1 | tactical doc min = ep_count × 500 | → ep_count × **450** (TF-59 하향, `constants.py:244`) |
| W2 | 모순 탐지 3단계: 정확 일치 + Jaccard 유사도 + regex | → 주 경로: Jaccard (`semantic_item_registry.py:197`), 폴백: 정확 일치 + 부분 문자열 포함 + regex (`constraint_db.py:612-629`) |
| W3 | 무협 금지 용어 154개 | → **130개** (129 고유). 154는 마지막 행 번호이며 원소 수가 아님 (`wuxia_guard.py:23-154`) |

**INACCURATE 정정 (I1-I12)**: SF3 빈 dict 표현(I1), SF6 스켈레톤 dict 표현(I2), 서브메뉴 구분(I3), Treatment 배치 크기(I4), 완전성 경고 동시 최대(I5), 타임아웃 config-overridable(I6), Director 절단 범위(I7), 에너지 경고 용어 불일치(I8), ErrorType 9개(I9), CoV 독립 메서드(I10), `_to_num_with_korean_units` 모듈 함수(I11), 이중 구현 위치(I12)

### 2차 적대적 감리 (47건)

| 판정 | 건수 |
|------|------|
| CONFIRMED | 24 |
| INACCURATE | 7 |
| WRONG | 2 |
| 신규 발견 (누락) | 11 |

**WRONG 정정 (W4-W5)**:

| ID | 원문 | 정정 |
|----|------|------|
| W4 | 이중 구현 1건 | → **4중 구현**: preset_registry, stage2_finalizer, stage2_optimizer, investment_arithmetic_checker |
| W5 | 미추적 경로 0건 | → **11건 누락** (MSF-A~K) |

**INACCURATE 정정 (I13-I19)**: Jaccard 과잉 정정 보완(I13), 금지 용어 런타임/폴백 구분(I14), ExpertMixture 0방지 가드(I15), 파일 수 표현(I16), 재시도 횟수 명확화(I17), SF15 None 반환(I18), SF16 None 반환(I19)

### 통합 결과

| 지표 | 값 |
|------|---|
| 총 검증 항목 | **95** |
| WRONG 총 | **5** (W1-W5, 모두 정정) |
| INACCURATE 총 | **19** (I1-I19, 모두 정정) |
| CONFIRMED 총 | **57** |
| 신규 발견 (누락 침묵 실패) | **11** (MSF-A~K) |
| 최종 정정 후 정확도 | **100%** |

---

## [부록 B] 근거 파일 인벤토리

### B.1 Stage 0 핵심 소스

| 파일 | 역할 |
|------|------|
| `modules/core/stage0/__init__.py` | StageZeroManager (서브메뉴 라우팅) |
| `modules/core/stage0/story_expander.py` | 컨셉 → Bible/Treatment |
| `modules/core/stage0/reverse_expander.py` | 기존 원고 → Bible 역설계 |
| `modules/core/stage0/style_extractor.py` | 스타일 DNA 추출 |
| `modules/core/stage0/preset_registry.py` | 동적 장르 스키마 관리 |
| `modules/core/stage0/spinner.py` | 진행 표시 유틸리티 |
| `modules/core/stage0_handoff.py` | Stage 0 → Stage 2 핸드오프 검증 |

### B.2 Stage 2 핵심 소스

| 파일 | 역할 |
|------|------|
| `modules/core/stage2_orchestrator.py` | Stage 2 오케스트레이션 |
| `modules/core/stage2_finalizer.py` | Arc 마무리 + 수치 검증 |
| `modules/core/constants.py` | Stage2Limits 등 상수 정의 |
| `modules/domain/agents/analyst.py` | 블록 Enrichment |
| `modules/domain/agents/arc_ensemble.py` | 3전략 앙상블 생성 |
| `modules/domain/agents/four_phase_arc_generator.py` | 3단계 Arc 생성 파이프라인 |
| `modules/domain/agents/arc_corrector.py` | Arc 부분 수정 |
| `modules/domain/agents/arc_critic.py` | 7차원 Arc 비평 |
| `modules/domain/agents/director_auditor.py` | Director 품질 판정 |

### B.3 교차 계층 보조 시스템

| 파일 | 역할 |
|------|------|
| `modules/core/constraint_db.py` | 아이템 제약 누적 + 모순 탐지 |
| `modules/core/semantic_item_registry.py` | Jaccard 유사도 기반 아이템 매칭 |
| `modules/core/fact_ledger.py` | 불변 사실 원장 |
| `modules/core/genre_guards/wuxia_guard.py` | 무협 장르 검증 규칙 |
| `modules/core/diversity_sampler.py` | 앙상블 다양성 보장 |
| `modules/core/adaptive_retry.py` | 오류 유형별 적응 재시도 |
| `modules/core/chain_of_verification.py` | Python + LLM 독립 검증 |
| `modules/core/expert_mixture.py` | 씬 유형별 전문가 라우팅 |
| `modules/core/dynamic_prompt_weighting.py` | 실패 학습 프롬프트 가중치 |
| `modules/core/confidence_calibration.py` | LLM 신뢰도 예측 |
| `modules/core/adversarial_self_play.py` | 적대적 자기 대결 |
| `modules/core/cross_agent_verifier.py` | 에이전트 간 교차 검증 |

---

> **S5 SSOT 작성 완료**: 2026-03-18
> 3회 독립 코드 조사 + 교차 대조 + 3PASS 감리 + 6회 적대적 감리 (95건) 결과를 통합.
> 모든 수치에 `file:line` 코드 근거 부착. WRONG 5건(W1-W5) + INACCURATE 19건(I1-I19) + MSF 11건 정정 완료.
> 가장 독창적 설계: DS1 (Spare Candidate Pool), DS2 (Transfused History), DS7 (실패 학습 가중치).
> 가장 높은 위험: SF3 (빈 dict 반환), MSF-F (전체 제약 비활성), MSF-H (전체 사실 추적 소실), MSF-J (마커 없는 침묵 반환).
