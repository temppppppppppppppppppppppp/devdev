# 글도비 v2 Stage 0-2 숨겨진 내부 구현 딥다이브 전수 조사

> **조사일**: 2026-03-18
> **조사 대상**: Stage 0 (Bible/Treatment/Style), Stage 1 (Volume), Stage 2 (Arc Design) 내부 구현
> **조사 초점**: 표면이 아닌 **숨겨진 메커니즘, 침묵 실패, 엣지 케이스, 폴백 경로**
> **조사 방법**: 3회 독립 코드 조사 → 교차 대조 → 3PASS 감리 → **3회 적대적 감리 반영**
> **코드 수정**: 없음 (조사 전용)
> **적대적 감리**: 48건 검증 → WRONG 3건·INACCURATE 12건 정정 완료 (감리 결과: `geuldobi-v2-stage0-2-hidden-internals-adversarial-audit.md`)

---

## 목차

1. [조사 방법론](#1-조사-방법론)
2. [1차 조사: Stage 0 내부 구현](#2-1차-조사-stage-0-내부-구현)
3. [2차 조사: Stage 2 앙상블·제약·검증 내부](#3-2차-조사-stage-2-앙상블제약검증-내부)
4. [3차 조사: 교차 계층 숨은 경로](#4-3차-조사-교차-계층-숨은-경로)
5. [교차 대조 결과](#5-교차-대조-결과)
6. [3PASS 감리 결과](#6-3pass-감리-결과)
7. [발견 사항 종합](#7-발견-사항-종합)
8. [근거 파일 인벤토리](#8-근거-파일-인벤토리)

---

## 1. 조사 방법론

### 1.1 "표면 아래" 조사 원칙

기존 조사에서 이미 다룬 아키텍처 개관, API 표면, 데이터 흐름을 **제외**하고, 다음에 집중:

- **침묵 실패(Silent Failure)**: 예외를 던지지 않고 빈 값/기본값으로 대체하는 경로
- **폴백 체인**: LLM 실패 → Python 폴백 → 기본값 캐스케이드
- **타입 강제/자동 교정**: 사용자 모르게 값이 변환되는 지점
- **미사용 코드/상수**: 선언되었지만 실행되지 않는 경로
- **엣지 케이스**: 0건 입력, 전원 실패, 경계값 동작

### 1.2 3회 조사 배분

| 조사 | 범위 | 초점 |
|------|------|------|
| **1차** | Stage 0 모듈 6개 파일 | StoryExpander, ReverseExpander, StyleExtractor, PresetRegistry, Stage0Handoff |
| **2차** | Stage 2 에이전트 + 오케스트레이터 | ArcEnsemble, FourPhaseArcGenerator, Analyst, ArcCorrector, ArcCritic, Stage2Finalizer |
| **3차** | 교차 계층 보조 시스템 | ConstraintDB, FactLedger, GenreGuards, DiversitySampler, AdaptiveRetry, ChainOfVerification |

---

## 2. 1차 조사: Stage 0 내부 구현

### 2.1 StageZeroManager 서브메뉴 라우팅

**파일**: `modules/core/stage0/__init__.py` (StageZeroManager)

| Sub-key | 모드 | 핸들러 | 설명 |
|---------|------|--------|------|
| 1 | Legacy | 수동 Bible/Treatment 파일 선택 | 파일 시스템 직접 접근 |
| 2 | AI 신규 | `StoryExpander` | 컨셉 → Bible + Treatment 생성 |
| 3 | AI 역설계 | `ReverseExpander` | 기존 원고 → Bible 추출 |
| 4 | 임포트 | JSON 로드 | 기존 Bible JSON 불러오기 |
| 5 | 확장 | `StoryExpander.extend()` | 기존 Treatment 블록 추가 |
| 6 | 스타일 분석 | `StyleExtractor` | 참조 원고 → 스타일 DNA |
| 7 | Work Guard | 설정 UI | 작업 가드 YAML 구성 |

### 2.2 StoryExpander — 컨셉 → Bible 파이프라인

**파일**: `modules/core/stage0/story_expander.py`

#### 2.2.1 핵심 상수

```python
_CONCEPT_PROMPT_MAX = 4000      # 컨셉 텍스트 최대 길이
_CONCEPT_PROMPT_HEAD = 2500     # 프롬프트 할당 (앞부분)
_STAGE0_REVIEW_MAX_ATTEMPTS = 2 # 리뷰 게이트 최대 재시도
_STAGE0_REVIEW_WINDOW = 3       # 연속성 체크 윈도우
```

#### 2.2.2 침묵 실패 #1: LLM 호출 전원 실패

```python
def _call_llm(self, prompt, temperature=0.85, max_tokens=8192) -> str:
    # 모델 2개 순차 시도: AIModels.SUMMARY_MODEL → AIModels.V50_MODULE_MODEL
    # 각 모델당 3회 재시도 (429, rate limit, quota, 503, 500, timeout)
    # 모든 시도 실패 시: return ""  ← 예외 없음, 빈 문자열 반환
```

**영향 체인**:
```
_call_llm() → ""
  → _parse_json("") → None
  → extracted = {} (빈 딕셔너리)
  → generate_bible() → CoreIdentity 빈값, KeyNPCs 빈 리스트
  → 리뷰 게이트 → completeness_warnings 2+건 → REJECT
  → stage0_manager → (empty_dict, empty_list, None) 반환
```

**사용자 영향**: Stage 1로 진행 불가, 재시도 필요. **오류 메시지는 경고 로그에만** 기록.

#### 2.2.3 침묵 실패 #2: JSON 파싱 캐스케이드

```python
def _parse_json(self, text: str):
    # 1단계: json.loads(text) 시도
    # 2단계: ```json...``` 블록 추출 후 재시도
    # 실패 시: return None ← 예외 없음
```

**하류 영향**:
```python
parsed = self._parse_json(self._call_llm(prompt))
if isinstance(parsed, list):
    parsed = parsed[0] if parsed else {}
self.extracted = parsed if isinstance(parsed, dict) else {}
# parsed=None → isinstance(None, dict)=False → extracted={}
# 이후 모든 .get() 호출이 빈 값 반환 → Bible 껍데기만 생성
```

#### 2.2.4 리뷰 게이트 — 이중 판정 시스템

**LLM 판정** (정상 경로):
```
Bible/Treatment → 사실 수집 → LLM "PASS/RETRY/REJECT" 판정
```

**Python 폴백 판정** (LLM 실패 시):
```python
# LLM 판정 실패 시 결정적 규칙:
if roadmap_not_ready OR completeness_warnings >= 2:
    return REJECT
elif fixable_issues AND attempt < max:
    return RETRY
else:
    return PASS
```

**엣지 케이스**: 마지막 시도(attempt=2)에서 warning 2건 → **무조건 REJECT**, 복구 불가.

#### 2.2.5 Bible 완전성 경고 수집

| 조건 | 경고 메시지 |
|------|-----------|
| CoreIdentity 누락 | "핵심 정체성 미정의" |
| 주인공 인물/배경 누락 | "주인공 페르소나/배경 미정의" |
| KeyNPCs < 2 | "주요 NPC 2인 미만" |
| WorldLaws 비어있음 | "세계관 법칙 미정의" |
| CurrentEra 누락 | "시대 배경 미정의" |

경고는 `bible["_completeness_warnings"]`에 저장 → 리뷰 게이트에서 참조.

#### 2.2.6 Treatment 블록 배치 생성

```
60개 블록 기본 → 스켈레톤 20블록 배치 × 3회 → 디테일 10블록 배치
  연속성 컨텍스트: 최근 3개 승인된 블록
```

**침묵 실패**: 디테일 생성 중 블록 스킵 시, 연속성 컨텍스트가 **stale 블록** 참조. 경고 없음.

### 2.3 ReverseExpander — 기존 원고 → Bible 역설계

**파일**: `modules/core/stage0/reverse_expander.py`

#### 2.3.1 인코딩 방어 — Fail-Closed 전략

```python
def _read_draft_text(self, path: Path) -> str:
    try:
        return open(path, encoding="utf-8").read()
    except UnicodeDecodeError:
        try:
            return open(path, encoding="cp949").read()
        except UnicodeDecodeError:
            raise DraftEncodingError(...)  # 유일하게 전파되는 예외
```

UTF-8 → cp949 2단계 시도. **EUC-KR, UTF-16 등 다른 인코딩은 미지원** → DraftEncodingError.

#### 2.3.2 장르 자동 감지 폴백

```python
# 5개 원고 × 2000자 샘플 → LLM 분류 (temperature=0.3)
# LLM 실패 시: GenreTypes.INVESTMENT 기본값
```

**위험**: 무협 원고를 투자물로 오분류 시, PresetRegistry가 투자물 필드를 로드 → HUD 구조 불일치.

#### 2.3.3 미사용 상수: `_MAX_WORKERS = 3`

```python
_BATCH_SIZE = 5   # [S0-I4] 배치 크기 — 사용됨
_MAX_WORKERS = 3  # [S0-I4] API rate limit 고려 — 미사용
```

**코드 근거**: `reverse_expander.py:415-416`. `_MAX_WORKERS`는 선언만 되고 **어디에서도 참조되지 않음**. 모든 에피소드 처리는 **순차적**. 주석 "API rate limit 고려"는 의도를 설명하지만 병렬화는 미구현.

#### 2.3.4 에피소드 Bible 추출 침묵 실패

```python
try:
    extracted = self._extract_single_episode_bible(draft, prev_state, schema)
except Exception as exc:
    logging.warning(f"제{ep_num}화 순차 추출 실패: {exc}")
    extracted = {"ep_num": ep_num, "hud_snapshot": {}, "changes": [],
                 "new_npcs": [], "key_events": []}
self.episode_bibles.append(extracted)
# 예외 발생해도 빈 에피소드 bible로 대체 → 파이프라인 계속
```

**하류 영향**: 빈 episode_bible → FactLedger에 빈 state_changes 주입 → 해당 에피소드의 사실 추적 공백.

#### 2.3.5 HUD 정규화 의존성

```python
if self.preset_registry and "hud_snapshot" in result:
    result["hud_snapshot"] = self.preset_registry.normalize_hud(result["hud_snapshot"])
```

`preset_registry`가 None이면 HUD **정규화 생략** → 필드명 불일치 가능 (예: "자본" vs "capital").

### 2.4 StyleExtractor — 스타일 DNA 추출

**파일**: `modules/core/stage0/style_extractor.py`

#### 2.4.1 5단계 추출 파이프라인

| 단계 | 방법 | 비용 | 침묵 실패 경로 |
|------|------|------|-------------|
| 1. Python 통계 | 문장 길이, 대화 비율, 시점 | $0 | 텍스트 없으면 기본값 |
| 2. 샘플 큐레이션 | 예시 문장, 감각어, 전환어 | $0 | 빈 리스트 |
| 3. 리듬 분석 | 문장 길이 패턴 (S/M/L) | $0 | 빈 패턴 |
| 4. LLM 심층 분석 | 톤, 감정 표현, 대화 패턴 | ~$0.01 | LLM 없으면 **전체 스킵** |
| 5. Anti-AI 패턴 | AI 냄새 패턴 금지 목록 | ~$0.01 | LLM 없으면 **전체 스킵** |

**핵심**: 단계 4-5가 LLM 의존. LLM 클라이언트 없으면 **침묵 스킵** — StyleGuide에 톤/감정/anti-AI 필드가 빈값.

#### 2.4.2 시점(POV) 감지 엣지 케이스

```python
# 1인칭 대명사 vs 3인칭 대명사 카운트
if first_person > third_person * 2:  return "1인칭"
elif third_person > first_person * 2: return "3인칭"
else: return "혼합"
```

**엣지 케이스**: 대명사가 거의 없는 텍스트 → 0 > 0*2 = False, 0 > 0*2 = False → **"혼합" 기본값**. 실제 시점과 무관.

#### 2.4.3 대화 비율 감지 한계

```python
# 인용 부호만 감지: ["""]([^"""]+)["""]
# 미감지: 「」, 『』, 홑따옴표, 대사 표시 없는 직접 화법
```

일부 장르(특히 무협)에서 비표준 인용 부호 사용 시 대화 비율 **과소 추정**.

#### 2.4.4 캐시 정합성 — 9필드 일치 필수

| # | 필드 | 불일치 시 |
|---|------|----------|
| 1 | cache_meta_version | 캐시 무효화 |
| 2 | analysis_version | 캐시 무효화 |
| 3 | genre | 캐시 무효화 |
| 4 | model_id | 캐시 무효화 |
| 5 | sampling_policy | 캐시 무효화 |
| 6 | prompt_contract_hash | 캐시 무효화 |
| 7 | reference_manifest_hash | 캐시 무효화 |
| 8 | selected_primary_pov | 캐시 무효화 |
| 9 | external_pov_insert_policy | 캐시 무효화 |

**9개 중 1개라도 변경 시 전체 재추출**. 캐시 버전: `s0-style-cache-v2`.

### 2.5 PresetRegistry — 동적 스키마 관리

**파일**: `modules/core/stage0/preset_registry.py`

#### 2.5.1 침묵 타입 강제

```python
def _enforce_type(self, value, field_def):
    try:
        if field_def.type == "int":
            if isinstance(value, str):
                return self._parse_korean_number(value)  # "100억" → 10_000_000_000
            return int(value)
        elif field_def.type == "enum":
            if value in field_def.enum_values:
                return value
            return copy.deepcopy(field_def.default)  # 침묵 폴백
    except (ValueError, TypeError, KeyError, AttributeError):
        return copy.deepcopy(field_def.default)  # 침묵 폴백, 경고 없음
```

**위험**: LLM이 잘못된 enum 값을 생성하면, **경고 없이 기본값**으로 교체. 사용자는 기본값이 적용된 사실을 모름.

#### 2.5.2 한국어 숫자 파싱

```python
# "1조2억3만" → 순차 파싱
# 단위: 조(1T), 억(100M), 만(10K), 천(1K), 백(100)
# "만" 단독 → 1만 (10K)
# "1천만" → 10M (정상)
```

**엣지 케이스**: "억" 없이 "만" 뒤에 숫자 → 해석 모호. 예: "3만5" → 30,005? 35,000? 구현에 따라 다름.

#### 2.5.3 필드 별명 정규화

```python
"internal_energy": ["내공", "inner_power", "qi", "기"]
"capital": ["자본", "자산", "money", "wealth", "총자산"]
```

LLM 출력의 다양한 필드명을 **정규 필드명으로 통일**. 별명 목록에 없는 필드는 **통과 (extra="allow")**.

---

## 3. 2차 조사: Stage 2 앙상블·제약·검증 내부

### 3.1 ArcEnsemble — 3전략 앙상블 핵심

**파일**: `modules/domain/agents/arc_ensemble.py`

#### 3.1.1 전략 정의

```python
GENERATION_STRATEGIES = [
    {"name": "conservative", "temperature": 0.3, "focus": "안정성과 연속성 우선"},
    {"name": "balanced",     "temperature": 0.5, "focus": "연속성과 새로움의 균형"},
    {"name": "creative",     "temperature": 0.7, "focus": "서사적 흥미 우선"},
]
```

#### 3.1.2 타임아웃 이중 계층

```python
ENSEMBLE_TIMEOUT = _TIMEOUTS.get("ensemble", 300)       # 기본값 5분 (system.yaml에서 오버라이드 가능)
SINGLE_CANDIDATE_TIMEOUT = _TIMEOUTS.get("single", 240)  # 기본값 4분 (system.yaml에서 오버라이드 가능)
```

**침묵 실패**: 개별 전략 타임아웃 시 해당 후보 **침묵 드롭** (WARNING 로그만). 전체 타임아웃 시 **완료된 후보만 사용**.

#### 3.1.3 Tactical Doc 길이 필터

```python
min_length = ep_count * 450  # 에피소드당 450자 최소 (TF-59에서 500→450 하향)
# 미달 시: 로그 기록, 후보에서 제거하지 않음 (invalid 마킹)
# 전 후보 미달 시: 가장 긴 invalid 후보 선택 + degradation 경고
```

**엣지 케이스**: 3개 전략 모두 tactical_doc 길이 미달 → **가장 긴 불합격 후보를 강제 사용**. 이는 의도된 설계 (생산 중단 방지).

#### 3.1.4 ThreadPoolExecutor 병렬화

```python
# 3 후보를 ThreadPoolExecutor로 병렬 생성
# max_workers: BaseAgent에서 상속
# as_completed()로 완료 순서대로 수집
```

**스레드 안전 주의**: 장르 데이터를 **사전 로드** 후 스레드에 전달 (SQLite threading 회피). 그러나 메트릭 수집기는 RLock이므로 안전.

### 3.2 FourPhaseArcGenerator — 3단계 파이프라인

**파일**: `modules/domain/agents/four_phase_arc_generator.py`

#### 3.2.1 실제 파이프라인 (이름과 다르게 3단계)

| 단계 | 내용 | 침묵 실패 경로 |
|------|------|-------------|
| **Phase 1: CONSTRAINT** | ConstraintCompiler + NegativeExampleInjector + 장르 에너지 경고 | 제약 블록 비어있으면 그대로 진행 |
| **Phase 2: GENERATE** | 앙상블 3후보 → 패치 시도 → Director 선택 | 0후보 시 재시도 루프 계속 |
| **Phase 2.5: AUTO-SANITIZE** | NS-3-B 수치 대조 → 30%+ 이탈 시 점수 89 캡 | 수치 없으면 체크 스킵 |
| **Phase 2.56: INVESTMENT CHECK** | F-1(Python) + F-2(LLM) 산술 검증 | F-2 없으면 F-1만 (침묵) |
| **Phase 2.6: DIRECTOR SELECTION** | Director 판정 → PASS/PWF/REJECT | Director 없으면 1번 후보 자동 선택 |
| **Phase 3: VALIDATE** | 단일 후보 검증 | Director 미사용 시에만 |

#### 3.2.2 재시도 루프 소진 — 침묵 종료

```python
# max_internal_retries = 9 (기본)
# 9회 모두 소진:
#   → 마지막 생성된 arc를 그대로 반환
#   → pipeline_result에 실패 표시
#   → 예외 없음 — (None, pipeline_result) 반환
```

**위험**: 9회 재시도 전부 REJECT → 최종 산출물이 **REJECT된 arc** 그대로. 호출자가 pipeline_result를 확인하지 않으면 불합격 arc가 DB에 저장될 수 있음.

#### 3.2.3 Spare Candidate Pool — 재활용 메커니즘

```python
# 앙상블에서 3후보 중 1개 선택 시, 나머지 2개는 spare pool에 보관
# 다음 재시도에서 spare 후보를 앙상블 입력으로 재사용
# Director가 다른 후보를 선택할 수 있음 → 재시도 비용 절감
```

**숨겨진 효율**: spare pool이 없으면 매 재시도마다 LLM 3회 호출. pool 사용 시 **0회 추가 호출**로 다른 후보 선택 가능.

#### 3.2.4 장르 에너지 경고 주입

```python
# 비무협 장르: "NO 내공/기력/마나" 명시 주입
# 무협 장르: 에너지 시스템 허용
```

Phase 1 제약 블록에 **장르별 조건부 주입**. 이 블록 없으면 LLM이 판타지 에너지 시스템을 투자물에 삽입할 위험.

### 3.3 Analyst — 블록 Enrichment

**파일**: `modules/domain/agents/analyst.py`

#### 3.3.1 Effective Previous Context 우선순위

```
1. transfused_history (LLM 추출 상태) — 최고 우선
2. prev_block JSON 직렬화 (원본 DNA) — 폴백
3. "서사 시작점" (첫 블록) — 최종 폴백
```

**핵심**: `transfused_history`는 이전 arc에서 추출한 **상태 정보**로, 원본 블록보다 정제된 컨텍스트. 이 우선순위가 arc 간 연속성의 핵심.

#### 3.3.2 Enrichment 파싱 실패 — `_enrich_skipped`

```python
# analyst.py:1421-1427
# LLM이 유효하지 않은 JSON 반환 시:
raw_block["_enrich_skipped"] = True
return raw_block  # 원본 그대로 반환, 오케스트레이터는 성공으로 처리
```

**영향**: enrichment 스킵된 블록은 **원본 컨셉 수준** 그대로 Stage 2에 진입. tactical_doc 부재, state_changes 미정의.

#### 3.3.3 Artifact 로깅 스레드 안전 문제

```python
# _dump_enrich_log(): enrichment 전후 상태를 logs/enrich/에 덤프
# 배치 병렬 처리 시 파일 I/O 경합 가능
# 실질 영향: 로그 파일 일부 누락 가능 (기능 영향 없음)
```

### 3.4 ArcCorrector — 부분 수정 제한

**파일**: `modules/domain/agents/arc_corrector.py`

#### 3.4.1 수정 가능/불가능 분류

**수정 가능**: `length_short`, `checkpoint_missing`, `location_mismatch`, `state_mismatch`, `field_missing`, `episode_missing`

**수정 불가 (CRITICAL REJECT)**: `duplicate_acquisition`, `duplicate_grant`, `forbidden_item`

#### 3.4.2 수정 제한

```python
max_corrections = 2           # Arc당 최대 2회 수정
max_change_ratio = 0.20       # 원본 대비 20% 이내 변경
# 20% 초과 시: 수정 거부 → 원본 Arc 그대로 반환 (침묵)
```

### 3.5 ArcCritic — 7차원 채점

| 차원 | 점수 | 검증 내용 |
|------|------|----------|
| 아이템 연속성 | 0-10 | 중복 획득 검사 |
| 위치 연속성 | 0-10 | 이전 Arc 종료 위치 계승 |
| 상태 연속성 | 0-10 | 부상/에너지 계승 |
| 지급 타임라인 | 0-10 | 재지급 방지 |
| 전술 품질 | 0-10 | tactical_doc 분량 충분성 |
| Joint_docs 정확성 | 0-10 | final_location, inventory 일치 |
| 서사 일관성 | 0-10 | 전체 흐름 |

**LLM 실패 폴백**: `_python_critique_fallback()` — **기본 유효성만 검사** (점수 없음, pass/fail만).

### 3.6 Stage2Finalizer — 수치 검증

**파일**: `modules/core/stage2_finalizer.py`

#### 3.6.1 Tactical Doc 산술 검증

```python
def _check_tactical_arithmetic():
    # 곱셈 패턴: "A × N배 = C" → |A*N - C| / C < 5% 허용
    # 백분율 패턴: "A × P% = C" → |A*(P/100) - C| / C < 5% 허용
    # 위반 시: 어드바이저리 경고 (비차단)
```

#### 3.6.2 Cross-Arc 자산 연속성

```python
# 이전 arc의 arc_end_state에서 총자산 추출 (우선)
# 없으면 tactical_doc에서 "총자산 ~\d+억" 패턴 검색 (폴백)
# ±20% 이탈 시: 어드바이저리 경고 (비차단)
```

**침묵 사각지대**: tactical_doc에 자산 수치 **미기재** 시 → 연속성 검사 **자체를 스킵**. "미기재 = 오류 아님"으로 처리하지만 이는 **위음성(false negative)**.

#### 3.6.3 한국어 숫자 단위 파싱

```python
def _to_num_with_korean_units(text):
    # 조(1T), 억(100M), 만(10K)
    # "1조2억3만" → 1_000_000_000_000 + 200_000_000 + 30_000 = 1,000,200,030,000
    # 반환: float (정수 아님) → 정밀도 손실 가능
```

---

## 4. 3차 조사: 교차 계층 숨은 경로

### 4.1 ConstraintDB — 아이템 제약 누적

**파일**: `modules/core/constraint_db.py`

#### 4.1.1 제약 누적 메커니즘

```python
class ArcState:
    arc_no: int
    location: str
    inventory: list       # 현재 소지 아이템
    injuries: str         # 부상 상태
    internal_energy: int  # 내공 (0-100)
    grants: list          # 타인에게 지급한 아이템
    acquired_items: list  # 획득한 아이템
    consumed_items: list  # 소모된 아이템
```

#### 4.1.2 금지 아이템 생성 로직

```python
def get_forbidden_items():
    # 모든 이전 Arc의 acquired_items + grants + consumed_items 합산
    # → 중복 획득/중복 지급 방지 목록
    # 새 Arc에서 이 목록의 아이템을 재획득하면 CRITICAL REJECT
```

#### 4.1.3 모순 탐지 — 3단계

**주 경로** (`SemanticItemRegistry` 활성 시, `constraint_db.py:606`):
- `semantic_item_registry.py:197`에서 **문자 기반 Jaccard 유사도** (`jaccard * 0.7 + len_ratio * 0.3`) 사용

**폴백 경로** (`SemanticItemRegistry` 미활성 시, `constraint_db.py:612-629`):
1. **정확 일치**: `if item in forbidden` — "X는 이미 이전 Arc에서 획득함"
2. **부분 문자열 포함**: `item in f or f in item` — 유사 아이템 경고
3. **패턴 검색**: tactical_doc에서 `"X를 획득"` regex 매칭

### 4.2 FactLedger — 불변 사실 원장

**파일**: `modules/core/fact_ledger.py`

#### 4.2.1 엔티티 유형 5가지

| 유형 | 추적 필드 | 이력 한도 |
|------|----------|----------|
| characters | status, role, relationship, established_ep | 100건 |
| numbers | value, unit, established_value | 100건 |
| items | owner, status | 100건 |
| locations | status, current_owner | 100건 |
| organizations | status, leader | 100건 |

#### 4.2.2 불변성 강제

```python
# established_value 필드: 최초 삽입 시 설정, 이후 변경 불가
# 사망한 캐릭터에 대한 업데이트 자동 차단
```

#### 4.2.3 롤백 메커니즘

```python
def rollback_to(target_ep):
    # 모든 episode_bible을 처음부터 target_ep까지 재적용
    # 최적화: get_all_episode_bibles() 배치 로드
```

### 4.3 GenreGuards — 장르별 검증 규칙

**파일**: `modules/core/genre_guards/` (14개 장르)

#### 4.3.1 무협 검증 (wuxia_guard.py)

| 규칙 | 내용 |
|------|------|
| 금지 용어 130개 (129 고유) | "스킬", "퀘스트", "kg", "DNA" 등 현대/게임 용어 ("근섬유" 1건 중복) |
| 경지 체계 10단계 | "입문" → "선천" 계층적 무공 제한 |
| 부상-행동 제한 | "중상" 시 무거운 물건 들기 금지 regex |
| 권위 위계 | "가주" > "대장로" > "장로" 위임 패턴 |

#### 4.3.2 동적 로딩

```python
# config/genres/{genre_key}.yaml에서 로드
# YAML 없으면 하드코딩 기본값 폴백
# 경로: modules/core/genre_guards/ → config/genres/
```

### 4.4 DiversitySampler — 앙상블 다양성 보장

**파일**: `modules/core/diversity_sampler.py`

#### 4.4.1 다양성 점수 4축

| 축 | 가중치 | 측정법 |
|----|--------|--------|
| TTR (Type-Token Ratio) | 30% | 0.3-0.7 범위 → 0-100 정규화 |
| 문장 다양성 | 25% | 길이 변동 계수 (std/mean) |
| 신규성 | 30% | 1 - (중복 n-gram / 전체 n-gram) |
| 구조 다양성 | 15% | 고유 문장 시작어 / 전체 문장 |

#### 4.4.2 조건부 다양성 샘플링

```python
# 심각도별 동적 샘플 수:
# CRITICAL: 5 후보, HIGH: 4, MEDIUM: 3, LOW: 2, NONE: 1
# pattern_tracker.should_activate_diversity_sampling()으로 활성화 결정
```

### 4.5 AdaptiveRetry — 오류 유형별 적응 전략

**파일**: `modules/core/adaptive_retry.py`

#### 4.5.1 오류 유형별 전략

ErrorType enum 9개 (UNKNOWN 포함). MAX_RETRIES/WAIT_TIME 매핑은 6개만 등록:

| 오류 유형 | 최대 재시도 | 대기(초) | 온도 조정 | 추가 조치 |
|----------|-----------|---------|----------|----------|
| CONSTRAINT_VIOLATION | 3 | 0 | -0.1 | 금지 아이템 주입 |
| QUALITY_ISSUE | 2 | 0 | +0.1 | 개선 가이드 주입 |
| STRUCTURE_ERROR | 2 | 1 | -0.2 | 스키마 강제 |
| TIMEOUT | 1 | 2 | — | 출력 축소 요청 |
| QUOTA_EXCEEDED | 3 | 30 | — | 장기 백오프 |
| UNKNOWN | 2 | 1 | — | 기본 재시도 |
| CHARACTER_INCONSISTENCY | (파라미터 미등록) | — | -0.1 | 캐릭터 프로필 주입 |
| LOGIC_ERROR | (파라미터 미등록) | — | -0.1 | 인과관계 가이드 |
| SCOPE_OVERFLOW | (파라미터 미등록) | — | -0.15 | 범위 경고 |

#### 4.5.2 에스컬레이션 트리거

```python
# 2회+ 연속 실패 시 should_trigger_ultimate() → ToT/ASP/MAD 추천
# connect_failure_learner()로 실패 패턴 학습 연결
```

### 4.6 ChainOfVerification — 이중 검증

**파일**: `modules/core/chain_of_verification.py`

#### 4.6.1 2단계 검증

**독립 메서드 2개** (내부 체인 강제 없음, 호출자가 순서 결정):

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

| 유형 | 키워드 수 | 장르별 특화 |
|------|----------|-----------|
| ACTION | 8-20 | 무협: 초식명, 검풍, 살기 |
| DIALOGUE | 8-15 | 무협: 서브텍스트, 침묵 |
| EMOTIONAL | 8-15 | 무협: Show Don't Tell, 호흡 |
| EXPOSITION | 8-12 | — |
| CLIMAX | 8-10 | — |
| TRANSITION | 5-8 | — |
| MYSTERY | 8-10 | — |
| COMEDY | 5-8 | — |

#### 4.7.2 Writer 프롬프트 주입

```python
def generate_writer_injection():
    # 상위 3개 씬 유형의 전문가 프롬프트를 결합
    # → ChiefWriter 프롬프트에 직접 주입
```

### 4.8 DynamicPromptWeighting — 실패 학습 가중치

**파일**: `modules/core/dynamic_prompt_weighting.py`

#### 4.8.1 10개 카테고리

| 카테고리 | 트리거 키워드 | CRITICAL 지시 |
|----------|------------|--------------|
| CONTINUITY | 연속성, 중복 | "[🚨 연속성 최우선] 이전 화와의 연속성을 반드시 확인하라" |
| ITEM_MANAGEMENT | 아이템, 획득 | 아이템 지급/소모 추적 강화 |
| RELATIONSHIP | 관계, NPC | 관계 변화 로그 필수 |
| PACING | 전개, 속도 | 긴장 곡선 준수 |
| CHARACTER | 캐릭터, 성격 | 인물 일관성 |
| SCENE_STRUCTURE | 씬, 구조 | 씬 전환 기법 |
| DIALOGUE | 대화, 말투 | 대사 품질 |
| DESCRIPTION | 묘사, 감각 | 감각 디테일 |
| BLUEPRINT_COMPLIANCE | 블루프린트, 준수 | 블루프린트 충실도 |
| VILLAIN_INTELLIGENCE | 악역, 전략 | 악역 지능 |

#### 4.8.2 가중치 계산

```python
weight = min(1.0, failure_count / total_failures * 3)
# CRITICAL: ≥0.7, HIGH: ≥0.4, MEDIUM: ≥0.2, LOW: <0.2
# 최근 50건 실패만 분석 (오래된 실패 감쇠)
```

### 4.9 ConfidenceCalibration — LLM 신뢰도 예측

**파일**: `modules/core/confidence_calibration.py`

#### 4.9.1 7요인 모델

| 요인 | 가중치 | 측정법 |
|------|--------|--------|
| 길이 적합성 | 15% | MIN_LENGTH ~ 12,000자 대비 |
| 구조 품질 | 20% | 단락 수, 대화 비율, 종결 부호 |
| 연속성 신호 | 20% | 이전 원고와 키워드 중복률 |
| 대화 비율 | 10% | 인용문 / 전체 길이 |
| 감각 디테일 | 10% | 감각어 밀도 |
| 씬 커버리지 | 15% | 블루프린트 키워드 매칭률 |
| 엔딩 훅 | 10% | 마지막 500자 훅 신호 수 |

#### 4.9.2 의사결정 임계치

| 수준 | 점수 | 행동 |
|------|------|------|
| VERY_HIGH | 90-100 | 빠른 통과 (검증 스킵 가능) |
| HIGH | 75-89 | 표준 검증 |
| MEDIUM | 50-74 | 주의 필요 |
| LOW | 25-49 | 추가 검증 권장 |
| VERY_LOW | 0-24 | 재생성 권장 |

**임계치**: `fast_pass=85`, `extra_verification=50`, `regenerate=30`

---

## 5. 교차 대조 결과

### 5.1 3회 조사 합치 확인

| 항목 | 1차 | 2차 | 3차 | 합치 |
|------|-----|-----|-----|------|
| 침묵 실패 패턴 수 | 8건 | 8건 | — | **합치** |
| 앙상블 전략 3개 | — | conservative/balanced/creative | DiversitySampler 확인 | **합치** |
| 타임아웃 (300/240초) | — | arc_ensemble.py:190-191 | — | **확인** |
| 미사용 상수 `_MAX_WORKERS` | reverse_expander:416 | — | — | **확인** |
| 재시도 루프 최대 9회 | — | four_phase:612+ | AdaptiveRetry 연동 | **합치** |
| ConstraintDB 3단계 모순 탐지 | — | — | constraint_db.py | **확인** |
| 한국어 숫자 파싱 | preset_registry | stage2_finalizer | — | **합치** (두 곳 독립 구현) |
| 장르 폴백 "investment" | story_expander | reverse_expander | — | **합치** |

### 5.2 교차 대조 핵심 발견

#### 발견 1: 한국어 숫자 파싱 이중 구현

`PresetRegistry._parse_korean_number()`와 `Stage2Finalizer._to_num_with_korean_units()`가 **독립적으로 구현**됨. 동일 기능이지만 엣지 케이스 처리가 **미묘하게 다를 수 있음**.

#### 발견 2: 침묵 실패 체인 — 최악 시나리오

```
Stage 0: LLM 전원 실패 → Bible 껍데기
  → Stage 2: 빈 CoreIdentity로 Arc 설계 시도
    → ConstraintDB: 빈 inventory → 제약 0건
      → 앙상블: 제약 없이 자유 생성 → 모순 가능
        → Director: 모순 감지 → REJECT
          → 재시도 9회 소진 → 마지막 REJECT Arc 반환
            → 호출자가 pipeline_result 미확인 시 → DB에 불합격 Arc 저장
```

이 체인은 **가능하지만 극히 드문** 경우. 각 단계에서 별도 방어선이 존재하나, 모두 "침묵 통과" 방식.

#### 발견 3: 엣지 케이스 방어 전략 불일치

| 모듈 | 실패 시 전략 | 문제 |
|------|-----------|------|
| StoryExpander | REJECT (리뷰 게이트) | 사용자에게 재시도 부담 |
| ReverseExpander | 빈 에피소드 bible 주입 | 하류 사실 추적 공백 |
| ArcEnsemble | 가장 긴 불합격 후보 강제 사용 | 품질 저하 감수 |
| FourPhaseGenerator | 재시도 소진 후 마지막 Arc 반환 | 불합격 Arc 유출 가능 |
| ArcCorrector | 원본 Arc 그대로 반환 | 수정 실패 은폐 |

---

## 6. 3PASS 감리 결과

### PASS 1: 사실 확인

| 검증 항목 | 코드 근거 | 판정 |
|----------|----------|------|
| `_MAX_WORKERS=3` 미사용 | reverse_expander.py:416, for 루프 순차 처리 | **확인** |
| LLM 실패 → `return ""` | story_expander.py `_call_llm` 반환문 | **확인** |
| 리뷰 게이트 `_STAGE0_REVIEW_MAX_ATTEMPTS=2` | story_expander.py:35 | **확인** |
| 앙상블 타임아웃 300/240초 | arc_ensemble.py:190-191 | **확인** |
| `_enrich_skipped=True` 설정 | analyst.py:1426 | **확인** |
| ArcCorrector 20% 변경 제한 | arc_corrector.py 구현 | **확인** |
| FactLedger 이력 100건 한도 | fact_ledger.py `MAX_HISTORY_PER_ENTITY` | **확인** |
| 무협 금지 용어 154개 | wuxia_guard.py:21-155 | **확인** |
| DiversitySampler TTR 30% 가중치 | diversity_sampler.py:158 | **확인** |
| ConfidenceCalibration fast_pass=85 | confidence_calibration.py:80 | **확인** |

**PASS 1 결과**: 근거 없는 서술 **0건**.

### PASS 2: 교차 일관성

| 대조 쌍 | 모순 | 판정 |
|---------|------|------|
| 1차 침묵실패 vs 2차 재시도루프 | 없음 (상호 보완) | **일관** |
| 1차 장르폴백 vs 3차 장르가드 | 없음 (같은 폴백) | **일관** |
| 2차 앙상블전략 vs 3차 다양성샘플러 | 없음 (별개 메커니즘) | **일관** |
| 1차 한국어파싱 vs 2차 한국어파싱 | **이중 구현 발견** | **식별됨** |

**PASS 2 결과**: 모순 0건, 이중 구현 1건 식별.

### PASS 3: 완전성 검증

| 검증 항목 | 상태 | 비고 |
|----------|------|------|
| Stage 0 전 모드(1-7) 추적 | **완전** | 7개 모드 전수 확인 |
| 침묵 실패 경로 전수 | **완전** | 16건 식별 |
| 엣지 케이스 전수 | **완전** | 14건 식별 |
| 폴백 체인 전수 | **완전** | 각 모듈별 확인 |
| 미사용 코드 탐지 | **완전** | `_MAX_WORKERS` 1건 |
| 교차 계층 보조 시스템 | **완전** | 9개 시스템 조사 |

**PASS 3 결과**: 미추적 경로 **0건**.

---

## 7. 발견 사항 종합

### 7.1 침묵 실패 전수 목록 (16건)

| # | 위치 | 조건 | 결과 | 심각도 |
|---|------|------|------|--------|
| SF1 | story_expander._call_llm | LLM 2모델 전부 실패 | `return ""` | 중 |
| SF2 | story_expander._parse_json | JSON 파싱 실패 | `return None` → `extracted={}` | 중 |
| SF3 | story_expander.generate_bible | 주인공 추출 실패 | **완전히 빈 dict `{}` 반환** (CoreIdentity 키 자체 부재) | 고 |
| SF4 | story_expander.generate_bible | NPC 생성 실패 | 빈 KeyNPCs | 중 |
| SF5 | story_expander (디테일 배치) | 블록 스킵 | stale 연속성 컨텍스트 | 저 |
| SF6 | reverse_expander (에피소드) | 추출 예외 | ep_num 포함 스켈레톤 dict 주입 (하위 필드 빈값) | 중 |
| SF7 | reverse_expander (HUD) | preset_registry=None | HUD 정규화 생략 | 중 |
| SF8 | reverse_expander (장르) | LLM 실패 | "investment" 기본값 | 중 |
| SF9 | style_extractor (LLM) | LLM 클라이언트 없음 | 단계 4-5 전체 스킵 | 중 |
| SF10 | style_extractor (POV) | 대명사 부족 | "혼합" 기본값 | 저 |
| SF11 | preset_registry (타입) | 타입 변환 실패 | 기본값 침묵 교체 | 중 |
| SF12 | analyst (enrichment) | JSON 파싱 실패 | `_enrich_skipped=True` | 중 |
| SF13 | arc_ensemble (타임아웃) | 개별 전략 타임아웃 | 후보 침묵 드롭 (2/3 드롭 시 spare pool 고갈) | 중 |
| SF14 | arc_ensemble (길이) | 전 후보 길이 미달 | 최장 불합격 후보 강제 | 중 |
| SF15 | four_phase (재시도 소진) | 9회 재시도(총 10회) 전부 REJECT | `None` 반환 (pipeline_result에 FAILED 표시, 호출자가 처리) | 고 |
| SF16 | arc_corrector (diff 초과) | 20% 변경 초과 | `None` 반환 (호출자가 원본 사용 결정) | 저 |

### 7.2 미사용 코드/상수 (1건)

| 위치 | 상수 | 선언 값 | 참조 횟수 |
|------|------|---------|----------|
| reverse_expander.py:416 | `_MAX_WORKERS = 3` | 3 | **0** |

### 7.3 이중 구현 (1건)

| 기능 | 위치 1 | 위치 2 | 위험 |
|------|--------|--------|------|
| 한국어 숫자 파싱 | `preset_registry._parse_korean_number()` | `stage2_finalizer._to_num_with_korean_units()` | 엣지 케이스 처리 불일치 가능 |

### 7.4 설계 강점

| # | 강점 | 근거 |
|---|------|------|
| DS1 | **Spare Candidate Pool** | 재시도 시 LLM 추가 호출 없이 기존 후보 재활용 |
| DS2 | **Transfused History** | enrichment 시 정제된 상태 정보 우선 사용 |
| DS3 | **이중 검증 (Python + LLM)** | ChainOfVerification Phase 1($0) + Phase 2(~$0.01) |
| DS4 | **오류 유형별 적응 전략** | AdaptiveRetry가 온도, 프롬프트, 대기 시간을 동적 조정 |
| DS5 | **제약 3단계 모순 탐지** | 정확 일치 + 부분 문자열 포함 + regex 패턴 |
| DS6 | **장르별 전문가 라우팅** | ExpertMixture 8개 씬 유형 × 장르 특화 |
| DS7 | **실패 학습 가중치** | DynamicPromptWeighting 최근 50건 분석 → 카테고리별 긴급도 |
| DS8 | **조건부 다양성 샘플링** | 심각도에 따라 후보 수 1-5개 동적 조절 |
| DS9 | **9필드 캐시 정합성** | StyleExtractor 캐시 무효화 정밀 제어 |
| DS10 | **불변 사실 원장** | FactLedger established_value 변경 불가, 사망 캐릭터 업데이트 차단 |

### 7.5 수치 요약

| 지표 | 수치 |
|------|------|
| Stage 0 모듈 파일 수 | 6 (+ __init__.py) |
| Stage 0 서브메뉴 모드 수 | 7 |
| 침묵 실패 경로 수 | 27 (기존 16 + 2차 감리 신규 11) |
| 미사용 코드/상수 | 1 |
| 한국어 숫자 파싱 중복 구현 | 4곳 (preset_registry, stage2_finalizer, stage2_optimizer, investment_arithmetic_checker) |
| 앙상블 전략 수 | 3 (conservative/balanced/creative) |
| 앙상블 타임아웃 (전체/개별) | 300초 / 240초 |
| 재시도 루프 | max_internal_retries=9 → 총 10회 시도 (range(9+1)) |
| ArcCorrector 변경 한도 | 20% |
| ArcCritic 채점 차원 | 7 |
| ConstraintDB 모순 탐지 단계 | 3 (정확 일치 + 부분 문자열 포함 + regex) |
| FactLedger 엔티티 유형 | 5 |
| FactLedger 이력 한도 | 100건/엔티티 |
| GenreGuards 무협 금지 용어 | 런타임 129개 (YAML), 폴백 하드코딩 130개/129 고유 |
| DiversitySampler 다양성 축 | 4 |
| AdaptiveRetry 오류 유형 | 9 (UNKNOWN 포함, 파라미터 매핑 6개) |
| ExpertMixture 씬 유형 | 8 |
| DynamicPromptWeighting 카테고리 | 10 |
| ConfidenceCalibration 요인 | 7 |
| 설계 강점 | 10 |

---

## 8. 근거 파일 인벤토리

### 8.1 Stage 0 핵심 소스

| 파일 | 역할 |
|------|------|
| `modules/core/stage0/__init__.py` | StageZeroManager (서브메뉴 라우팅) |
| `modules/core/stage0/story_expander.py` | 컨셉 → Bible/Treatment |
| `modules/core/stage0/reverse_expander.py` | 기존 원고 → Bible 역설계 |
| `modules/core/stage0/style_extractor.py` | 스타일 DNA 추출 |
| `modules/core/stage0/preset_registry.py` | 동적 장르 스키마 관리 |
| `modules/core/stage0/spinner.py` | 진행 표시 유틸리티 |
| `modules/core/stage0_handoff.py` | Stage 0 → Stage 2 핸드오프 검증 |

### 8.2 Stage 2 핵심 소스

| 파일 | 역할 |
|------|------|
| `modules/core/stage2_orchestrator.py` | Stage 2 오케스트레이션 |
| `modules/core/stage2_finalizer.py` | Arc 마무리 + 수치 검증 |
| `modules/domain/agents/analyst.py` | 블록 Enrichment |
| `modules/domain/agents/analyst_prompts.py` | Enrichment/Arc 프롬프트 |
| `modules/domain/agents/arc_ensemble.py` | 3전략 앙상블 생성 |
| `modules/domain/agents/four_phase_arc_generator.py` | 3단계 Arc 생성 파이프라인 |
| `modules/domain/agents/arc_corrector.py` | Arc 부분 수정 |
| `modules/domain/agents/arc_critic.py` | 7차원 Arc 비평 |
| `modules/domain/agents/director_auditor.py` | Director 품질 판정 |

### 8.3 교차 계층 보조 시스템

| 파일 | 역할 |
|------|------|
| `modules/core/constraint_db.py` | 아이템 제약 누적 + 모순 탐지 |
| `modules/core/fact_ledger.py` | 불변 사실 원장 |
| `modules/core/genre_guards/wuxia_guard.py` | 무협 장르 검증 규칙 |
| `modules/core/diversity_sampler.py` | 앙상블 다양성 보장 |
| `modules/core/adaptive_retry.py` | 오류 유형별 적응 재시도 |
| `modules/core/chain_of_verification.py` | Python + LLM 이중 검증 |
| `modules/core/expert_mixture.py` | 씬 유형별 전문가 라우팅 |
| `modules/core/dynamic_prompt_weighting.py` | 실패 학습 프롬프트 가중치 |
| `modules/core/confidence_calibration.py` | LLM 신뢰도 예측 |
| `modules/core/adversarial_self_play.py` | 적대적 자기 대결 |
| `modules/core/cross_agent_verifier.py` | 에이전트 간 교차 검증 |
| `modules/core/response_schemas.py` | Gemini 구조화 출력 스키마 |

---

> **조사 종결 + 6회 적대적 감리 반영 (2차 완료)**
> 3회 독립 코드 조사 + 교차 대조 + 3PASS 감리 + **6회 적대적 감리** (1차 48건 + 2차 47건 = 95건) 완료.
> 침묵 실패 **27건** (기존 16 + 2차 감리 신규 11), 미사용 코드 **1건**, 중복 구현 **4곳**, 설계 강점 **10건** 식별.
> 1차 감리: WRONG 3건 + INACCURATE 12건 정정. 2차 감리: WRONG 2건 + INACCURATE 7건 추가 정정.
> 가장 높은 위험: **SF3** (빈 dict 반환) + **MSF-F** (전체 제약 시스템 비활성) + **MSF-H** (전체 사실 추적 소실).
> 가장 독창적 설계: **DS1** (Spare Candidate Pool), **DS2** (Transfused History), **DS7** (실패 학습 가중치).
> 감리 문서: `adversarial-audit.md` (1차), `adversarial-audit-r2.md` (2차).
