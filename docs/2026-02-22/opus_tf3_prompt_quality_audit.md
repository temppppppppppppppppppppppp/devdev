# Opus TF-3: Prompt Engineering Quality & LLM Integration Audit

> 작성일: 2026-02-22
> 감사자: Claude Opus 4.6
> 대상: 글도비 AI 웹소설 자동 생성 시스템 전체 (V64+)
> 범위: 프롬프트 크기 관리, JSON 파싱 견고성, YAML 로더, 모델 폴백, 컨텍스트 캐싱, 토큰 카운팅, 응답 후처리

---

## Executive Summary

글도비의 LLM 연동 패턴은 전반적으로 **성숙한 방어 체계**를 갖추고 있다. `base_agent.py`의 다층 폴백 체인, `_extract_json_robust()`의 5단계 복구 파이프라인, Gemini의 `response_mime_type: "application/json"` 강제, `response_schema` 스키마 제약 활용 등은 프로덕션급 설계이다.

그러나 **200화 장기연재 시 프롬프트 폭발 문제가 최대 리스크**로 식별되었다. 이전 30화 원고 전문을 프롬프트에 삽입하는 V67 패턴은 150,000~225,000자(약 100K~150K 토큰)를 단일 프롬프트에 주입하며, 이는 Gemini 1M 토큰 윈도우의 10~15%를 원고 역사만으로 소비한다. 여기에 Blueprint, HUD, Arc, Guard 프롬프트 등 나머지 컨텍스트를 합치면 한 번의 Director 앙상블 호출이 **300K~500K 토큰**에 도달할 수 있다.

### 위험도 요약

| 항목 | 위험도 | 근거 |
|------|--------|------|
| 프롬프트 크기 관리 | **HIGH** | V67 "30화 전문" 주입이 200화 시 150K자+, Director 호출은 3개 원고 포함 시 250K자+ |
| JSON 파싱 견고성 | **LOW** | 5단계 복구 + 스키마 강제 + 크기 가드 |
| YAML 프롬프트 로더 | **LOW** | SafeDict 폴백, 캐싱, 싱글톤 |
| 모델 폴백 체인 | **LOW** | 3-pro -> 2.5-pro -> 2.5-flash, 쿼터 캐시, 키 순환 |
| 컨텍스트 캐싱 | **MEDIUM** | TTL 30분 고정, content_hash 기반 무효화는 건전하나 stale 위험 존재 |
| 토큰 카운팅 | **MEDIUM** | 휴리스틱 추정만 존재 (한글 1.5자/토큰), 사전 절삭 없음 |
| 응답 후처리 | **LOW** | process_node 재귀 평탄화 + 크기 가드 + 방문 횟수 제한 |

---

## 1. Prompt Size Management (프롬프트 크기 관리)

### 1.1 각 Stage별 프롬프트 크기 추정

#### Stage 2 (Arc/Blueprint 생성)

| 구성요소 | 추정 크기 (자) | 비고 |
|----------|---------------|------|
| 기본 프롬프트 (YAML) | ~5,000 | `config/prompts/analyst.yaml` etc. |
| 이전 Arc 요약 | ~3,000~10,000 | prev_arcs 수에 비례 |
| 현재 블록 DNA | ~1,000~3,000 | treatment 블록 |
| 벡터 검색 결과 | ~5,000~12,000 | vector_max_results_s2=12 |
| NegativeExample | ~2,000 | 안티패턴 |
| Entity Registry | ~2,000~5,000 | NPC 목록 |
| **합계 (초기)** | **~20,000~40,000자** | **~13K~27K 토큰** |

**평가**: Stage 2는 Gemini 1M/2M 토큰 대비 2~3% 수준. 200화에서도 안전하다. 이전 Arc 요약은 누적되지만 요약이므로 선형 증가가 제한적이다.

#### Stage 4 (원고 생성) - ChiefWriter

| 구성요소 | 추정 크기 (자) | 비고 |
|----------|---------------|------|
| 메인 프롬프트 템플릿 | ~3,000 | `build_chief_writer_main_prompt()` |
| Blueprint (scene_breakdown) | ~3,000~8,000 | 6-8 씬 |
| 직전 원고 엔딩 | 2,500 | `prev_manuscript[-2500:]` |
| 에피소드 다이제스트 | ~500~1,500 | regex 기반 추출 |
| HUD 리포트 | ~1,000~3,000 | 주인공 상태 |
| Arc 전술 문서 | ~2,000~5,000 | tactical_doc |
| 미래/과거 침범 방지 | ~1,000~3,000 | 아이템, 무공, 사망 NPC 목록 |
| 장르 Guard/Purism | ~500~2,000 | 장르별 |
| 공통 규칙 + 집필 지침 | ~3,000 | YAML 기반 |
| 캐릭터 보이스 | ~500~1,000 | NPC별 말투 |
| 세계 상태 요약 | ~5,000 | `get_summary(max_chars=5000)` |
| 확장 Lookback | ~4,000 | `lookback_total_chars: 4000` |
| **V67 이전 30화 원고 전문** | **~150,000~225,000** | **5,000~7,500자 x 30화** |
| 연결고리 | ~500 | chain_link |
| 스타일 가이드 | ~500~1,000 | |
| 전략 인스트럭션 | ~500 | balanced/narrative/tension |
| 출력 포맷 | ~500 | JSON schema |
| **합계 (V67 포함)** | **~180,000~260,000자** | **~120K~175K 토큰** |
| **합계 (V67 제외)** | **~25,000~40,000자** | **~17K~27K 토큰** |

#### Stage 4 (원고 심사) - Director 앙상블

| 구성요소 | 추정 크기 (자) | 비고 |
|----------|---------------|------|
| 선택 프롬프트 템플릿 | ~3,000 | `ENSEMBLE_SELECTION_PROMPT` |
| Blueprint | ~5,000 | |
| 직전 화 엔딩/다이제스트 | ~3,000 | |
| **V67 이전 30화 원고 전문** | **~150,000~225,000** | 동일 |
| **3개 후보 원고** | **~15,000~22,500** | 5,000~7,500자 x 3 |
| Python 경고 | ~1,500 | 3개 후보 x 500자 |
| 평가 기준 + 출력 형식 | ~3,000 | |
| **합계** | **~180,000~260,000자** | **~120K~175K 토큰** |

### 1.2 smart_truncate와 ContextLimits

**핵심 코드** (`modules/core/constants.py` L132-153):
```python
class ContextLimits:
    MAX_CONTEXT_CHARS = 800_000  # 800K 문자 (Gemini 1.05M 토큰 입력 기준 안전 마진)

def smart_truncate(text, max_chars=ContextLimits.MAX_CONTEXT_CHARS, head_chars=80_000):
    # head 80K + tail (나머지) 보존, 중간 생략
```

이 800K 제한은 **이전 30화 원고 전문 (`prev_manuscripts_text`)에만 적용**되며, 다른 컨텍스트 요소는 별도 절삭 없이 프롬프트에 합산된다.

### 1.3 200화 장기연재 시 프롬프트 폭발 시나리오

200화 시점에서 V67 "이전 30화 전문" 주입의 크기:
- 화당 평균 원고: 5,000~7,500자
- 30화 전문: **150,000~225,000자** (~100K~150K 토큰)
- `smart_truncate`에 의해 800K 자로 절삭됨 → 30화 전문은 이 한도 이내

**문제점**: `smart_truncate`는 `prev_manuscripts_text` 전체에 적용되지만, 이것이 프롬프트의 **다른 요소와 합산된 후의 총량은 검사하지 않는다**. Director 앙상블 호출의 경우:
- prev_manuscripts_text: ~200K자
- 3개 후보 원고: ~22K자
- 기타 컨텍스트: ~15K자
- **총합: ~237K자 (~158K 토큰)**

이는 Gemini 2.5 Pro/Flash의 1M 토큰 입력 한도 내에서 안전하지만, **비용과 지연 시간이 선형으로 증가**한다.

### 1.4 Findings

| ID | 심각도 | 내용 |
|----|--------|------|
| P-1 | **HIGH** | 프롬프트 총 크기를 API 호출 전에 검증하는 게이트가 없음. `ask()` 메서드는 `len(base_prompt)`만 로깅할 뿐, 실제로 `MAX_CONTEXT_CHARS`를 초과하는지 검사하지 않음 |
| P-2 | **MEDIUM** | V67 이전 30화 전문은 200화에서도 30화 고정이지만, 원고당 분량이 커질 경우(10,000자+) 300K자까지 갈 수 있음. `smart_truncate`가 방어하나, 절삭 시 head 80K + tail 방식으로 중간 화가 유실됨 |
| P-3 | **MEDIUM** | Director 앙상블에서 3개 후보 원고 전문 + 30화 전문 + 평가 프롬프트를 단일 호출에 넣는 패턴은 비용 효율이 낮음. Context Caching이 Director에 적용되어 있으나(`create_manuscript_cache`), 30화 전문은 매번 프롬프트 본문에도 삽입됨 |
| P-4 | **LOW** | `ENSEMBLE_TIMEOUT = 600`초 (10분)이지만, 150K+ 토큰 프롬프트의 응답 지연은 고려되지 않음 |

---

## 2. JSON Parsing Robustness (JSON 파싱 견고성)

### 2.1 핵심 파서: `_extract_json_robust()`

**위치**: `modules/domain/agents/base_agent.py` L916-1039

이 메서드는 **5단계 복구 파이프라인**을 구현:

1. **크기 가드**: 500KB 초과 시 절삭 (`_MAX_JSON_PAYLOAD = 500_000`)
2. **자가 치유**: 괄호 불균형 감지 → 강제 폐쇄, 홀수 따옴표 → 보충
3. **마크다운 코드블록 제거**: `` ```json `` / `` ``` `` 래핑 strip
4. **2단계 파싱**: `json.loads(strict=False)` → `ast.literal_eval()` → `_parse_and_repair_hard()`
5. **정규식 폴백**: `tactical_doc`, `content`, `scene_breakdown`, `integrated_scenario` 키별 강제 추출

### 2.2 Gemini `response_mime_type: "application/json"` 활용

`base_agent.py`의 `ask()` 메서드는 **모든 호출에 `response_mime_type: "application/json"`을 강제** (L315):
```python
config_params = {
    "response_mime_type": "application/json",
}
```

이는 Gemini API가 JSON 형식만 출력하도록 제약하며, 마크다운 래핑이나 추가 텍스트 문제를 근본적으로 방지한다.

### 2.3 `response_schema` 스키마 강제

`modules/core/response_schemas.py`에서 정의된 Gemini Schema 객체:
- `BLOCKING_RESULT_SCHEMA`
- `SCORING_RESULT_SCHEMA`
- `ADVISORY_RESULT_SCHEMA`
- `ARC_DESIGN_SCHEMA`

Analyst, Director 등 핵심 에이전트가 `response_schema` 파라미터로 전달하여 **구조적 출력을 API 레벨에서 강제**.

### 2.4 BaseAgent를 우회하는 직접 API 호출

60개 파일에서 `json.loads` 또는 `_extract_json_robust`를 사용. 일부 에이전트는 `base_agent.ask()` 대신 직접 `client.models.generate_content()`를 호출:

- `advisory_validator.py` L138-140: 직접 호출, `response_mime_type: "application/json"` 적용
- `scoring_validator.py` L231-235: 동일 패턴
- `writer.py` L227-231: 직접 호출
- `weaver.py` L62-66: 직접 호출
- `state_tracker_npc.py` L663-667: 직접 호출 (max_output_tokens: 256)
- `tree_of_thoughts.py` L642-645: 직접 호출

이들은 `response_mime_type: "application/json"`을 적용하지만, `_extract_json_robust()`의 5단계 복구는 각자 별도로 호출해야 한다.

### 2.5 `_parse_and_repair_hard()` 정규식 2-pass

**위치**: L1041-1084

`ast.literal_eval` 실패 시 정규식으로:
- Pass 1: 문자열 값 (`"key": "value"`) 추출
- Pass 2: 숫자/불리언/null 값 추출

이 접근법은 **중첩 객체/배열을 처리하지 못함**. 그러나 `response_mime_type: "application/json"`이 근본 방어를 하므로, 이 코드는 거의 실행되지 않을 것이다.

### 2.6 Findings

| ID | 심각도 | 내용 |
|----|--------|------|
| J-1 | **LOW** | `response_mime_type: "application/json"` + 5단계 복구는 충분히 견고함 |
| J-2 | **INFO** | `_parse_and_repair_hard()` 정규식은 중첩 JSON 미지원이나, 폴백 경로에서만 실행되므로 실질적 영향 없음 |
| J-3 | **INFO** | 직접 API 호출 경로(6개 파일)도 모두 `response_mime_type: "application/json"` 적용. `_extract_json_robust` 호출은 호출자 책임이나, 대부분 올바르게 사용 중 |

---

## 3. Prompt YAML Loader (프롬프트 YAML 로더)

### 3.1 PromptLoader 구현

**위치**: `modules/core/prompt_loader.py`

| 특성 | 구현 상태 |
|------|-----------|
| 싱글톤 | Double-checked locking (`_instance_lock`) |
| 캐싱 | `_cache_lock` 보호 딕셔너리 |
| 누락 키 방어 | `load()` → `None` 반환, 호출측에서 폴백 상수 사용 |
| 변수 치환 | `SafeDict` + `format_map` (누락 키는 `{key}` 그대로 유지) |
| 파일 미존재 | `{}` 반환, 빈 캐시 저장 |
| 인코딩 | `utf-8` 명시 |
| YAML 파서 | **자체 구현 (PyYAML 미사용)**: `KEY: |` 패턴 정규식 매칭 |

### 3.2 자체 YAML 파서의 한계

PromptLoader는 PyYAML 대신 **자체 정규식 파서**를 사용 (L77-133):
```python
key_pattern = re.compile(r"^([A-Z][A-Z0-9_]+):\s*\|")
```

이 파서는:
- **지원**: `KEY_NAME: |` + 인덴트된 멀티라인 블록
- **미지원**: YAML 앵커(&, *), 중첩 딕셔너리, 리스트, 인라인 값, 조건부 키
- **안전**: 현재 40개 YAML 파일이 모두 `KEY: |` 형식이므로 동작에 문제 없음

### 3.3 폴백 패턴

`chief_writer_prompts.py`의 전형적 패턴:
```python
def _load_prompt(key, fallback):
    loaded = _PROMPT_LOADER.load("chief_writer", key)
    return loaded if loaded is not None else fallback
```

`_FALLBACK_EMPTY = ""`이므로, YAML 로드 실패 시 **빈 문자열이 프롬프트에 삽입**된다. 이는 안전하지만, 핵심 프롬프트(COMMON_RULES_SECTION, WRITING_GUIDELINES_SECTION)가 누락되면 품질 저하가 발생한다.

### 3.4 Findings

| ID | 심각도 | 내용 |
|----|--------|------|
| Y-1 | **LOW** | 자체 YAML 파서는 현재 파일 구조에 맞게 동작하나, 향후 복잡한 YAML 구조(중첩 맵, 앵커)를 추가하면 파싱 실패 |
| Y-2 | **MEDIUM** | YAML 로드 실패 시 `_FALLBACK_EMPTY = ""`로 빈 프롬프트가 삽입되는 것은 조용한 품질 저하를 유발. 핵심 키 누락 시 경고 로깅이 `debug` 레벨로만 남음 (L70) |
| Y-3 | **INFO** | `SafeDict.__missing__`으로 미치환 변수는 `{key}` 그대로 노출 → LLM이 플레이스홀더를 보게 됨 |

---

## 4. Model Fallback Chain (모델 폴백 체인)

### 4.1 모델 할당 구조

**`config/models.yaml`**:
```yaml
agents:
  chief_writer: "gemini-3-pro-preview"    # 최고 품질 (원고 생성)
  director: "gemini-2.5-pro"              # 고품질 (심사)
  analyst: "gemini-3-pro-preview"         # 고품질 (Arc 설계)
  block_enricher: "gemini-3-flash-preview" # 보조 (블록 강화)
  arc_critic: "gemini-2.5-flash"          # 경량 (검증)
```

### 4.2 폴백 체인

```
gemini-3-pro-preview → gemini-2.5-pro
gemini-3-flash-preview → gemini-2.5-flash
gemini-2.5-flash → gemini-2.5-flash (자기 자신 = 종단)
```

**의도**: 3세대 모델 쿼터 소진 시 2.5세대로 폴백. `gemini-2.5-pro`가 최종 방어선.

### 4.3 쿼터 캐시 (`_quota_exhausted_models`)

- 429/ResourceExhausted 발생 시 해당 모델을 **1시간 캐시** (`_QUOTA_CACHE_DURATION: 3600`)
- 다음 호출에서 캐시된 모델은 스킵 → 즉시 폴백 모델 사용
- `threading.Lock` 보호 (I-18)
- 키 순환 시 캐시 전량 초기화 (`_quota_exhausted_models.clear()`)

### 4.4 API 키 순환

- `GOOGLE_API_KEY`, `_2`, `_3` ... `_9`까지 최대 9개 키 지원
- 429 발생 시 `_key_rotation_pending = True` → 다음 `ask()` 호출에서 키 전환
- **전체 키 순환 완료 시 더 이상 순환하지 않음** (V62.3: `_rotation_count >= len(keys) - 1`)
- 키 순환 시 **Context Cache 전량 무효화** (API 키별 캐시 격리)

### 4.5 Rate Limit vs Quota 구분 대응

```
Rate Limit (429 + rate/limit) → 30초 → 60초 → 90초 백오프 (같은 모델, 최대 3회)
Quota Exhausted (resource_exhausted) → 즉시 폴백 모델 전환
gemini-3-pro Rate Limit → 즉시 폴백 (할당량 부족 모델이므로)
```

### 4.6 Findings

| ID | 심각도 | 내용 |
|----|--------|------|
| F-1 | **LOW** | 폴백 체인 설계가 건전. 3세대 → 2.5세대 → 2.5-flash 순서로 비용/품질 균형 |
| F-2 | **INFO** | `gemini-2.5-flash → gemini-2.5-flash` (자기 자신)는 종단이므로, 2.5-flash까지 소진되면 예외 발생. 그러나 2.5-flash는 쿼터가 넉넉하므로 실질적 위험 없음 |
| F-3 | **INFO** | gemini-3-pro-preview의 Rate Limit은 "즉시 폴백"으로 적절히 처리 |

---

## 5. Context Caching (컨텍스트 캐싱)

### 5.1 구현 개요

**위치**: `base_agent.py` L1088-1313

| 특성 | 값 |
|------|---|
| 캐시 키 | `{cache_type}_{project_name}_{content_hash_16}` |
| 해시 | MD5 16자리 |
| TTL | 30분 (기본, 호출자 지정 가능) |
| 최소 캐싱 크기 | 50,000자 (32K 토큰 하한 추정) |
| 최대 캐시 수 | 50개 (`_CONTEXT_CACHE_MAX`) |
| LRU 정리 | 50개 초과 시 `created_at` 기준 오래된 것 제거 |
| 키 순환 시 | `_context_caches.clear()` (전량 무효화) |
| 스레드 안전 | `_cache_lock` (threading.Lock) |

### 5.2 사용처

1. **Director 원고 캐시** (`director_caching.py`): 전체 이전 원고 합본을 Gemini Context Caching API로 캐싱. 원고 수가 동일하면 재사용.
2. **Director 연속성 검증** (`director_continuity.py`): Blueprint/원고 연속성 검증 시 캐시 사용.
3. **ChiefWriter**: `merge_contexts_for_caching()`으로 Blueprint/Manuscript 리스트를 캐싱 텍스트로 병합.

### 5.3 캐시 무효화 조건

| 조건 | 무효화 방식 |
|------|------------|
| TTL 만료 (30분) | `created_at` 기반, 조회 시 만료 검사 후 삭제 |
| API 키 순환 | `_context_caches.clear()` (전량) |
| 429/quota 발생 | 키 순환 예약 → 차후 전량 무효화 |
| 에피소드 롤백 | `Director.invalidate_caches()` 호출 |
| content_hash 변경 | 새 해시 → 새 캐시 생성 |

### 5.4 Stale 캐시 위험 분석

**시나리오**: 에피소드 N-1 완료 후 Director가 원고 캐시를 생성 → 30분 TTL 내에 에피소드 N의 ChiefWriter가 같은 캐시를 사용 → **에피소드 N-1 원고가 캐시에 없음** (캐시 생성 시점이 N-1 완료 전이면).

**현재 방어**: `DirectorCachingManager.create_manuscript_cache()`에서 `_cached_manuscript_count`를 확인하여, 원고 수가 변경되면 새 캐시를 생성 (L123-125).

```python
if self.manuscript_cache_name and self._cached_manuscript_count == len(manuscripts_compiled):
    return self.manuscript_cache_name  # 재사용
```

이는 **원고 수 기반 무효화**이므로, 같은 에피소드 번호에서 원고 내용이 변경된 경우(롤백 후 재생성) stale 데이터를 사용할 수 있다. 그러나 `Director.invalidate_caches()`가 롤백 시 호출되므로 실질적 위험은 낮다.

### 5.5 Findings

| ID | 심각도 | 내용 |
|----|--------|------|
| C-1 | **LOW** | content_hash + TTL + 원고 수 기반 무효화는 대부분의 stale 시나리오를 방어 |
| C-2 | **MEDIUM** | TTL 30분 고정은 장시간 세션(야간 운영)에서 불필요한 캐시 재생성을 유발. 에피소드 완료 이벤트 기반 무효화가 더 효율적 |
| C-3 | **INFO** | 캐시 최소 크기 50,000자 (L1139)는 Gemini 32K 토큰 최소 요건의 안전 마진. 적절 |

---

## 6. Token Counting (토큰 카운팅)

### 6.1 현재 구현

**위치**: `modules/core/metrics_collector.py` L242-258

```python
def estimate_tokens(self, text, is_input=True):
    korean_chars = sum(1 for c in text if "가" <= c <= "힣")
    other_chars = len(text) - korean_chars
    return int(korean_chars / 1.5 + other_chars / 4)
```

이 휴리스틱은:
- 한글: 1.5자당 1토큰
- 영어/기타: 4자당 1토큰
- **용도**: 비용 추적 전용 (`MetricsCollector`). 프롬프트 크기 제어에는 사용되지 않음.

### 6.2 프롬프트 크기 제어의 부재

**현재 시스템에는 프롬프트를 API에 전달하기 전 토큰 수를 측정하고, 초과 시 절삭하는 메커니즘이 없다.**

유일한 크기 제어:
1. `smart_truncate()`: `prev_manuscripts_text`에 800K 자 제한
2. `ContextCompressor`: Stage 4 컨텍스트에 대한 압축 (목표 60%)
3. `_apply_context_budget()`: SC 벡터 검색 결과에 대한 50K 자 예산
4. `_MAX_JSON_PAYLOAD = 500_000`: 응답 파싱 시 크기 제한

그러나 **프롬프트 조립 완료 후 총 크기를 측정하고 API 입력 한도와 비교하는 단계는 없다**.

### 6.3 Gemini countTokens API 미사용

Gemini API는 `countTokens` 메서드를 제공하여 정확한 토큰 수를 사전에 계산할 수 있다. 현재 글도비는 이 API를 사용하지 않는다.

### 6.4 Findings

| ID | 심각도 | 내용 |
|----|--------|------|
| T-1 | **MEDIUM** | 프롬프트 총 토큰 수를 API 호출 전에 검증하는 게이트가 없음. Gemini의 1M/2M 토큰 한도를 초과하면 API 오류가 발생하며, 현재 이 오류는 일반 예외로 처리됨 (폴백 모델 전환) |
| T-2 | **LOW** | `estimate_tokens()` 휴리스틱은 +-20% 오차 범위. 비용 추적에는 충분하나, 크기 제어에는 부정확 |
| T-3 | **INFO** | `countTokens` API 호출 비용은 무료이나, 매 호출마다 추가 지연이 발생. 선택적 적용 권장 |

---

## 7. Response Post-Processing (응답 후처리)

### 7.1 원고 추출 (ChiefWriter → Director)

ChiefWriter의 응답은 JSON 형식:
```json
{
  "title": "...",
  "content": "5,000자 이상 원고",
  "state_updates": {...},
  "writing_strategy": "balanced",
  "key_scenes_covered": [...]
}
```

`_extract_json_robust()`의 `process_node()` 재귀 평탄화가 이 구조를 처리:
- 최대 재귀 깊이: 20
- 최대 방문 횟수: 100 (`_MAX_VISITS`)
- 순환 참조 감지: `id()` 기반 `seen_ids`

### 7.2 연속 이어쓰기 (Continuation)

`ask()` 메서드는 `MAX_TOKENS`/`LENGTH` finish reason 발생 시 **최대 5회 이어쓰기** (L352-587):

```python
MAX_CONTINUATIONS = 5
WARN_THRESHOLD = 3
```

이어쓰기 시 **Overlap-Aware Merge**:
- 앞 응답 끝 100자와 뒤 응답 시작 100자를 대조
- 최장 겹침 구간을 찾아 중복 제거 후 접합
- 후행 이스케이프(`\`) 강제 제거

### 7.3 Blueprint/Arc 추출

Blueprint Ensemble의 응답은 `_extract_json_robust()`로 파싱 후, `scene_breakdown`, `integrated_scenario`, `ending_hook` 등 핵심 키를 추출. 정규식 폴백이 이들 키를 개별 복구.

Arc 설계의 응답은 `ARC_DESIGN_SCHEMA`로 스키마 강제. 이 경우 Gemini가 스키마에 맞는 JSON만 생성하므로 파싱 실패 확률이 극히 낮다.

### 7.4 `_validate_response()` 사후 검증

**위치**: L830-857

백업 모델 응답에 대한 간이 검증:
1. 최소 길이 10자
2. JSON 시작 문자 (`{` 또는 `[`)
3. 괄호 균형 (오차 2 이내)
4. 핵심 필드 존재 (`content`, `tactical_doc`, `integrated_scenario`, `title`, `state_updates`)

### 7.5 Pydantic 모델 검증

`modules/models/arc.py`, `modules/models/blueprint.py`, `modules/models/manuscript.py`에서 Pydantic BaseModel을 정의:
```python
class ArcData(BaseModel):
    model_config = ConfigDict(extra="allow")
    arc_num: int
    tactical_doc: str | dict
    ...
```

`extra="allow"`로 미정의 키를 수용하면서, 필수 필드의 타입 검증을 수행.

### 7.6 Findings

| ID | 심각도 | 내용 |
|----|--------|------|
| R-1 | **LOW** | 연속 이어쓰기의 Overlap-Aware Merge는 견고. Circuit Breaker(5회)로 비용 폭증 방지 |
| R-2 | **LOW** | `_validate_response()`의 핵심 필드 리스트가 하드코딩되어 있어, 새 에이전트 추가 시 업데이트 필요 |
| R-3 | **INFO** | Pydantic `extra="allow"`는 LLM의 예측 불가 키를 안전 수용하는 적절한 전략 |

---

## 8. Cross-Cutting Concerns (횡단 관심사)

### 8.1 중괄호 이스케이프 (`_escape_braces`)

모든 사용자 데이터(director_feedback, arc_doc, hud_report 등)는 프롬프트 삽입 전 `_escape_braces()`로 처리:
```python
text.replace("{", "{{").replace("}", "}}")
```
- 중복 이스케이프 방지: 이미 `{{`가 있으면 스킵
- `escape_utils.py`의 독립 유틸리티 우선 사용

이는 f-string 프롬프트에서 `KeyError` 및 `IndexError`를 방지하는 필수 방어이다.

### 8.2 `response_mime_type: "application/json"` 일관성

모든 `ask()` 호출과 직접 API 호출에서 `response_mime_type: "application/json"`이 설정됨. 이는 Gemini가 JSON 외 텍스트를 출력하지 않도록 강제하여, 마크다운 래핑이나 사족 텍스트 문제를 근본 방지한다.

**예외**: `story_expander.py`, `reverse_expander.py`는 `response_mime_type`을 설정하지 않는 경우가 있다 (Stage 0 자유 텍스트 생성).

### 8.3 Temperature 전략

| 에이전트 | Temperature | 근거 |
|----------|------------|------|
| ChiefWriter (balanced) | 0.7 | 안정적 품질 |
| ChiefWriter (narrative) | 0.8 | 창의성 |
| ChiefWriter (tension) | 0.8 | 창의성 |
| Director (앙상블) | 0.3 | 일관된 판정 |
| Director (연속성) | 0.1 | 엄격한 검증 |
| Analyst (첫 시도) | 0.5 | 표준 |
| Analyst (재시도) | 0.6-0.7 | 다양성 증가 |
| StateTracker | 0.0 | 결정적 추출 |

이 전략은 각 역할에 적합하다. 특히 Director의 낮은 temperature는 일관된 심사를 보장한다.

---

## 9. Recommendations (권장 사항)

### 9.1 Critical (즉시 개선 권장)

| # | 제안 | 관련 Finding |
|---|------|-------------|
| R1 | **프롬프트 크기 사전 검증 게이트 추가**: `ask()` 호출 전 `len(prompt)`을 Gemini 입력 한도(1M 토큰 ~ 1.5M 자)와 비교하는 가드 추가. 초과 시 `ContextCompressor`를 자동 적용하거나 `smart_truncate` 호출 | P-1, T-1 |
| R2 | **V67 "30화 전문" 전략 재검토**: 전문 삽입 대신 (a) 요약+핵심 사실 추출 or (b) Context Caching API로 분리 전송 or (c) 최근 5화 전문 + 나머지 요약 하이브리드 | P-2, P-3 |

### 9.2 Medium (다음 스프린트 권장)

| # | 제안 | 관련 Finding |
|---|------|-------------|
| R3 | YAML 핵심 키 누락 시 `WARNING` 레벨 로깅: `COMMON_RULES_SECTION`, `WRITING_GUIDELINES_SECTION` 등 핵심 키 누락 시 `debug` → `warning` 변경 | Y-2 |
| R4 | Context Cache TTL을 에피소드 완료 이벤트 기반으로 전환: TTL 30분 고정 대신, 에피소드 완료 시 캐시 갱신 | C-2 |
| R5 | `countTokens` API 선택적 활용: Director 앙상블 호출 등 대형 프롬프트에 대해서만 사전 토큰 측정 | T-3 |

### 9.3 Low (기술 부채 관리)

| # | 제안 | 관련 Finding |
|---|------|-------------|
| R6 | `_validate_response()` 핵심 필드 리스트를 에이전트별 레지스트리로 외부화 | R-2 |
| R7 | YAML 파서를 PyYAML로 전환하거나, 자체 파서의 지원 구문 범위를 문서화 | Y-1 |

---

## 10. Architecture Diagram (프롬프트 흐름도)

```
User Input (Treatment/Bible)
    │
    ▼
┌─────────────┐     config/prompts/*.yaml
│  Stage 0    │◄────────────────────────────
│  (Setup)    │     PromptLoader (싱글톤)
└─────┬───────┘
      │
      ▼
┌─────────────┐     ARC_DESIGN_SCHEMA
│  Stage 2    │◄── response_schema 강제
│ (Arc/BP)    │     + ContextCompressor
│             │     + VecMemory 검색
└─────┬───────┘
      │
      ▼
┌─────────────────────────────────────────────┐
│  Stage 4 — ChiefWriter                      │
│  ┌──────────────────────────────────────┐   │
│  │ Prompt Assembly (~180K~260K 자)       │   │
│  │ ● Blueprint + Scene Breakdown        │   │
│  │ ● V67: 30화 원고 전문 (★ 최대 구간)   │   │
│  │ ● HUD + WorldState + Guard/Purism    │   │
│  │ ● 전략 인스트럭션 (3종 병렬)           │   │
│  └──────────────────────────────────────┘   │
│           │                                  │
│           ▼                                  │
│  ┌────────────────┐                         │
│  │ BaseAgent.ask() │                         │
│  │ ● response_mime_type: JSON               │
│  │ ● 폴백 체인: 3-pro → 2.5-pro            │
│  │ ● 연속 이어쓰기 (MAX 5회)                │
│  │ ● _extract_json_robust (5단계)           │
│  └────────┬───────┘                         │
│           │ 3개 후보                          │
│           ▼                                  │
│  ┌────────────────────────────────┐         │
│  │ Director Ensemble Selection    │         │
│  │ ● 30화 전문 + 3 후보 + 평가    │         │
│  │ ● Context Cache (원고 합본)    │         │
│  │ ● PASS / REJECT 판정          │         │
│  └────────┬───────────────────────┘         │
│           │                                  │
│           ▼                                  │
│  PASS → 후처리 (State 추출, DB 저장)          │
│  REJECT → 피드백 반영 → ChiefWriter 재호출    │
└─────────────────────────────────────────────┘
```

---

## 11. Token Budget Projection (200화 시뮬레이션)

### 가정
- 화당 평균 원고: 6,000자
- 한글 비율: 80%
- 토큰 변환: 한글 1.5자/토큰, 영문 4자/토큰

### 시나리오별 프롬프트 크기

| 시나리오 | 화수 | V67 30화 전문 크기 | 총 프롬프트 (CW) | 총 프롬프트 (Dir) | Gemini 한도 대비 |
|----------|------|-------------------|-----------------|------------------|----------------|
| 초기 (1-10화) | 10 | ~60K자 (~40K tok) | ~100K자 (~67K tok) | ~120K자 (~80K tok) | **8%** |
| 중기 (50화) | 50 | ~180K자 (~120K tok) | ~220K자 (~147K tok) | ~260K자 (~173K tok) | **17%** |
| 후기 (100화) | 100 | ~180K자 (~120K tok) | ~220K자 (~147K tok) | ~260K자 (~173K tok) | **17%** |
| 장기 (200화) | 200 | ~180K자 (~120K tok) | ~220K자 (~147K tok) | ~260K자 (~173K tok) | **17%** |

**결론**: V67의 "최근 30화만" 윈도우는 200화에서도 프롬프트 크기를 일정하게 유지한다. 이는 **설계 의도대로 동작**한다. 다만 30화 전문이 프롬프트의 ~70%를 차지하므로, 이 비중을 줄이면 다른 컨텍스트(Guard, 세계관, 캐릭터 보이스 등)에 더 많은 여유를 확보할 수 있다.

### 비용 영향

1M 토큰 기준 Gemini 2.5-pro 비용:
- 입력: $1.25/1M 토큰
- 에피소드당 Director 앙상블 1회: ~173K 입력 토큰 → ~$0.22
- 에피소드당 ChiefWriter 3회(3 전략): ~147K x 3 = ~441K 입력 토큰 → ~$0.55
- **에피소드당 주요 LLM 호출 비용: ~$0.77 (입력만)**

200화 총 비용 (입력 토큰만): ~$154

---

## Appendix A: Key File References

| 파일 | 경로 | 역할 |
|------|------|------|
| base_agent.py | `modules/domain/agents/base_agent.py` | 모든 LLM 호출의 기반 (ask, 폴백, JSON 파싱) |
| prompt_loader.py | `modules/core/prompt_loader.py` | YAML 프롬프트 로더 (싱글톤) |
| context_compression.py | `modules/core/context_compression.py` | Python 기반 컨텍스트 압축 |
| constants.py | `modules/core/constants.py` | ContextLimits, smart_truncate |
| metrics_collector.py | `modules/core/metrics_collector.py` | 토큰 추정, 비용 계산 |
| response_schemas.py | `modules/core/response_schemas.py` | Gemini JSON 스키마 정의 |
| chief_writer_context.py | `modules/domain/agents/chief_writer_context.py` | CW 프롬프트 조립 |
| chief_writer_prompts.py | `modules/domain/agents/chief_writer_prompts.py` | CW 프롬프트 템플릿 |
| director_ensemble.py | `modules/domain/agents/director_ensemble.py` | Director 앙상블 선택 |
| director_caching.py | `modules/domain/agents/director_caching.py` | Director 캐싱 관리 |
| stage4_context_builder.py | `modules/core/stage4_context_builder.py` | Stage 4 컨텍스트 수집 |
| context_advisor.py | `modules/core/context_advisor.py` | Smart Retrieval 계획 |
| models.yaml | `config/models.yaml` | 에이전트별 모델 할당 |
| system.yaml | `config/system.yaml` | BaseAgent 운영 파라미터 |
| validation.yaml | `config/settings/validation.yaml` | 검증 임계값, 컨텍스트 예산 |

---

## Appendix B: JSON Parsing Flow

```
LLM Response (text)
    │
    ▼
_extract_json_robust()
    │
    ├─ [Guard] len > 500KB → 절삭
    │
    ├─ [Self-Heal] 괄호 불균형 → 강제 폐쇄
    │   홀수 따옴표 → 보충
    │
    ├─ [Strip] ```json ... ``` 제거
    │
    ├─ [Extract] regex: ({...}) 또는 ([...])
    │
    ├─ [Parse 1] json.loads(strict=False)
    │   └─ 성공 → process_node() 평탄화
    │
    ├─ [Parse 2] ast.literal_eval()
    │   └─ 성공 → process_node() 평탄화
    │
    ├─ [Hard Repair] _parse_and_repair_hard()
    │   ├─ null/true/false → Python 리터럴
    │   ├─ ast.literal_eval() 재시도
    │   └─ 실패 → regex 2-pass (문자열 + 숫자)
    │
    └─ [Field Extraction] 개별 키 regex
        ├─ "tactical_doc": "..."
        ├─ "content": "..."
        ├─ "scene_breakdown": {...}
        └─ "integrated_scenario": "..."
            └─ 전부 실패 → {"parsing_error": True}
```

---

*End of Audit Report*
