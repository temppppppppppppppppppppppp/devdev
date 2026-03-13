# SZ0-T4 Style Extraction & Downstream Injection Findings

> 작성일: 2026-03-13
> 상태: 3pass complete
> 범위: `modules/core/stage0/style_extractor.py` (1,143줄), downstream injection path (`stage4_orchestrator.py`, `chief_writer.py`, `chief_writer_context.py`, `chief_writer_prompts.py`)

---

## Executive Summary

Style Extractor는 5단계(통계→큐레이션→리듬→LLM심층→Anti-AI)로 원고 문체를 분석하여 `StyleGuide` dataclass를 생성하고, Stage 4 Chief Writer 프롬프트에 직접 주입한다. 사전 배정된 3개 이슈(P2-6, P2-7, P2-8)를 중심으로 3pass 감사를 수행했다.

**확정 Findings: 3건** (P2 1건, P3 2건)
- SZ0-T4-001 (P2): `reference_excerpt` 50KB + `to_prompt()` 출력이 truncation 없이 CW 프롬프트에 주입되어 토큰 예산 압박 가능
- SZ0-T4-002 (P3): `_score_sentence()`, `_score_passage()`의 키워드 기반 점수 산출은 대원칙 위반이 아닌 통계적 필터링
- SZ0-T4-003 (P3): StyleGuide가 Director 심사 없이 CW에 직접 주입되나, 이는 "집필 지시" 영역으로 Director 주권 위반이 아님

**오탐 제거: 2건**

---

## PASS 1 - 후보 수집

### 후보 A — `_score_sentence()` / `_score_passage()` Python 자동 점수 (P2-6)

- **확신도**: MED
- **태그**: `principle-1`, `scoring`, `judgment-vs-processing`
- **근거**: `style_extractor.py:628-670` (`_score_sentence`), `554-570` (`_score_passage`)
  - 하드코딩된 감각어/클리셰/액션동사 사전으로 문장·문단에 수치 점수 부여
  - 점수 기반 정렬 후 상위 N개를 `sample_sentences`, `exemplary_passages`, `reference_excerpt`에 선별
  - "이 문장이 좋은가?"라는 판단을 Python이 수행하는 것처럼 보임
- **반론 후보**: CLAUDE.md 명시 — "타입 변환, 필드명 정규화, 포맷 변환, 통계적 점수"는 위반 아님

### 후보 B — `reference_excerpt` 50KB 상한 토큰 예산 압박 (P2-7)

- **확신도**: HIGH
- **태그**: `token-budget`, `prompt-size`, `downstream`
- **근거**: `style_extractor.py:576-626` — `max_chars = 50_000`
  - `to_prompt()` 출력 (최대 ~5-8KB) + `reference_excerpt` (최대 50KB) = 최대 ~58KB
  - CW 프롬프트에 `style_guide` 파라미터와 `reference_excerpt_section`이 별도로 주입됨 (`chief_writer_context.py:500-501`, `chief_writer_prompts.py:72-75`)
  - `reference_excerpt`는 `smart_truncate()` 미적용 — `prev_manuscripts_text`는 적용되나(`chief_writer_context.py:467`) `reference_excerpt`는 raw 주입
  - 50KB ≈ 약 25,000 한국어 토큰. CW 프롬프트의 다른 컨텍스트(이전 원고, Blueprint, HUD 등)와 합산 시 Gemini 컨텍스트 윈도우 압박 가능

### 후보 C — StyleGuide→CW Director 우회 (P2-8)

- **확신도**: MED
- **태그**: `principle-3`, `director-sovereignty`, `bypass`
- **근거**: `stage4_orchestrator.py:1492-1564`
  - StyleGuide를 로드하여 `to_prompt()` 결과를 `_SessionConfig.style_guide`에 직접 저장
  - 이후 `_RoundContext` → `ChiefWriter.generate_ensemble()` → CW 프롬프트로 전달
  - Director는 **원고 품질**을 심사하지, 스타일 가이드 자체를 심사하지 않음
- **반론 후보**: StyleGuide는 "집필 지시서"에 해당. Director 주권은 "원고 합격/불합격/수정 지시" 결정권이지, 집필 파라미터 설정 권한이 아님

### 후보 D — `_llm_call()` 폴백 체인에서 `_ensure_client()` 직접 Gemini 초기화

- **확신도**: LOW
- **태그**: `provider-abstraction`, `direct-client`
- **근거**: `style_extractor.py:1057-1068`
  - `_ensure_client()`가 `google.genai.Client`를 직접 생성하나, `_llm_call()`은 `generate_content_via_router()`를 사용
  - router가 client를 무시할 수 있으므로 직접 client 생성이 불필요할 수 있음
  - 단 `generate_content_via_router()`의 시그니처가 `client` 파라미터를 수용하므로 호환

### 후보 E — 캐시 무효화 시 `_cache_meta_matches()` 누락 키 허용

- **확신도**: LOW
- **태그**: `cache-integrity`
- **근거**: `style_extractor.py:338-350`
  - `required_keys` 9개를 모두 비교하지만, `cached_meta`에 키가 없으면 `None == current_value`로 불일치 판정
  - 구형 캐시(`s0-style-cache-v1`)는 `selected_primary_pov` 등이 없어 자동 재분석 강제
  - ROP-T4 감사에서도 이 동작 확인 완료 (PASS2 교차 검증 C에서 제거)

---

## PASS 2 - 교차 검증

### 교차 검증 A — `_score_sentence()` / `_score_passage()` 대원칙 1 위반 여부

**검증 방법**: 함수 동작 분석 + CLAUDE.md 위반/비위반 기준 대조

1. `_score_sentence()` (L628-670): 감각어 매칭 +3, 의성어 +2, 클리셰 -3, 짧은 문장 보너스 +1, 동사 어미 +0.5
2. `_score_passage()` (L554-570): 감각어 +3, 액션동사 +1, 클리셰 -2, 대화 포함 +2
3. 이 점수는 **"품질 판단"이 아니라 "특징 밀도 측정"**:
   - "이 문장이 좋다/나쁘다"를 판정하는 것이 아니라, "감각어가 많고 클리셰가 적은 문장"을 상위로 정렬
   - 결과는 `sample_sentences`, `exemplary_passages`에 선별 → LLM에게 "이런 느낌으로 쓰라"는 예시로 전달
   - LLM이 최종적으로 이 예시를 어떻게 활용할지 판단
4. CLAUDE.md 명시: "통계적 점수"는 위반 아님
5. 비교: `numeric_consistency_checker.py`(NC 체크)도 Python-only 9개 검사를 수행하며, 이는 공인된 "수집" 패턴

**결론**: 후보 A는 **대원칙 위반 아님**. 통계적 필터링으로 분류. 단, P3 정보성 finding으로 기록 (향후 혼동 방지).

### 교차 검증 B — `reference_excerpt` 50KB 토큰 예산

**검증 방법**: downstream 주입 경로 전수 추적

1. `style_extractor.py:576-626` — `_build_reference_excerpt()`:
   - 200-800자 문단 중 대화 포함 + 서술 40자 이상만 선별
   - `max_chars = 50_000` 하드코딩
   - `_latest_curated_passages` + 점수 기반 후보를 순차 추가
2. `stage4_orchestrator.py:1513` — `reference_excerpt = getattr(loaded_sg, "reference_excerpt", "")`
3. `chief_writer_context.py:472-474` — `reference_excerpt_section` 생성 시 `self.host._escape_braces(reference_excerpt)` 적용, **truncation 없음**
4. `chief_writer_prompts.py:75` — 프롬프트에 `reference_excerpt_section` 직접 삽입
5. `to_prompt()` (L125-202): 최대 출력 크기 추정:
   - 핵심 DNA: ~200자
   - POV 규칙: ~500자
   - 리듬/감정/Anti-AI/모범문단/대화/전환/밀도/표현: ~3,000-5,000자
   - 합계: ~3,500-5,500자
6. **총 주입 크기**: `to_prompt()` ~5KB + `reference_excerpt` 최대 50KB = **최대 ~55KB**
7. CW 프롬프트의 다른 대형 컨텍스트:
   - `prev_manuscripts_section` (이전 30화 원고 전문) — `smart_truncate()` 적용 (MAX_CONTEXT_CHARS = 1,000,000자)
   - `scene_breakdown`, `hud_report`, `arc_doc` 등
8. Gemini 2.5 Pro 컨텍스트 윈도우 = 1M 토큰. 55KB ≈ 27,500 토큰으로 윈도우의 ~2.75%
9. **실제 위험**: 1M 토큰 모델에서는 즉시 문제 아님. 그러나:
   - `reference_excerpt`만 유일하게 `smart_truncate()` 미적용
   - `prev_manuscripts_section`과 합산 시 대용량 프로젝트(100화+)에서 총 프롬프트 크기 급증 가능
   - fallback 모델(Flash 등)의 윈도우가 더 작을 경우 문제 발생 가능

**결론**: 후보 B는 **P2 확정**. 50KB 자체보다 truncation guard 부재가 핵심 문제.

### 교차 검증 C — Director 우회 여부

**검증 방법**: 대원칙 3 "디렉터 주권주의" 정의 대조

1. CLAUDE.md: "Director가 최종 **품질 결정권**. Chief Writer·Analyst 등은 **초안 제출**만, **합격/불합격/수정 지시**는 Director가 내림."
2. StyleGuide는 **집필 파라미터**(톤, 시점, 리듬, 금지 표현)이지 **원고 품질 판정**이 아님
3. 유사 패턴:
   - `config/prompts/*.yaml` — 43개 외부화된 프롬프트도 Director 심사 없이 CW에 직접 주입
   - `WritingDirective` — Director 심사 없이 CW에 직접 주입
   - `genre_guards/*.py` — 장르별 규칙도 Director 심사 없이 적용
4. Director의 역할: **원고가 생성된 후** 품질을 심사. 집필 지시서를 사전 심사하는 것은 아키텍처 범위 밖
5. Director는 StyleGuide 준수 여부를 간접적으로 평가 — self-critique 체크 15(톤 일관성), 16(POV 일관성)

**결론**: 후보 C는 **대원칙 위반 아님**. P3 정보성 finding으로 기록.

### 교차 검증 D — `_ensure_client()` 직접 Gemini 초기화

**검증 방법**: `generate_content_via_router()` 호출 시 client 활용 경로 확인

1. `_llm_call()` (L1088): `generate_content_via_router(client=self.client, ...)` — router에 client 전달
2. `llm_generate.py`의 `generate_content_via_router()`는 router를 통해 적절한 provider로 라우팅
3. `_ensure_client()`는 router가 없을 때의 직접 client 초기화 — legacy 호환
4. CLAUDE.md 명시: "`gemini_provider.py`(합법) + `vertex_provider.py`(합법)"만 직접 `generate_content()` 허용이지만, `_ensure_client()`는 `generate_content()`를 직접 호출하지 않음
5. `generate_content_via_router()`를 사용하므로 router 추상화 계약 준수

**결론**: 후보 D **제거**. router 추상화를 정상 사용.

### 교차 검증 E — 캐시 무효화 키 누락 허용

**검증 방법**: ROP-T4 감사 결과 교차 참조

1. ROP-T4 PASS2 교차 검증 C에서 동일 이슈 검증 완료
2. `s0-style-cache-v1` 포맷은 `cache_meta_version` 불일치로 자동 재분석 강제
3. 새로 생성된 캐시는 9개 키 모두 포함

**결론**: 후보 E **제거**. 기존 감사에서 검증 완료.

---

## PASS 3 - 최종 확정 Findings

### 1. ID: `SZ0-T4-001`

2. Severity: **P2**
3. 현상 요약:
   - `reference_excerpt` (최대 50,000자)가 `smart_truncate()` 없이 CW 프롬프트에 raw 주입된다.
   - `to_prompt()` 출력(~5KB)과 합산하면 스타일 관련 주입만 최대 ~55KB.
   - `prev_manuscripts_section`, `scene_breakdown` 등 다른 대형 컨텍스트와 합산 시 총 프롬프트 크기가 예측 불가능하게 커질 수 있다.
   - 현재 Gemini 2.5 Pro (1M 토큰)에서는 즉시 문제가 아니나, fallback 모델이나 향후 모델 변경 시 위험.
4. 코드 근거:
   - `modules/core/stage0/style_extractor.py:577` — `max_chars = 50_000` 하드코딩
   - `modules/domain/agents/chief_writer_context.py:472-474` — `reference_excerpt` raw 주입, truncation guard 없음
   - `modules/domain/agents/chief_writer_prompts.py:75` — `reference_excerpt_section` 프롬프트 직접 삽입
   - 대조: `chief_writer_context.py:467` — `prev_manuscripts_text`는 `smart_truncate()` 적용
5. downstream 영향 경계:
   - CW 프롬프트 토큰 예산 (특히 fallback 모델 사용 시)
   - 대용량 프로젝트(100화+)에서 `prev_manuscripts_section` + `reference_excerpt` 합산 크기
   - Gemini API 비용 (불필요하게 큰 프롬프트)
6. 현재 테스트 근거 또는 테스트 부재:
   - `reference_excerpt` 크기 제한을 검증하는 테스트 없음
   - CW 프롬프트 총 크기를 검증하는 테스트 없음
7. 기존 문서와의 중복 여부:
   - `docs/stage_map/stage0.md:87` — "`reference_excerpt`는 최대 50,000자"로 문서화되어 있으나, downstream truncation guard 부재는 미언급
   - ROP-T4 감사와 중복 없음
8. 권장 후속 조치:
   - `chief_writer_context.py`에서 `reference_excerpt` 주입 시 `smart_truncate()` 또는 별도 상한(예: 30,000자) 적용
   - 또는 `_build_reference_excerpt()`의 `max_chars`를 validation.yaml SSOT로 외부화
   - CW 프롬프트 전체 크기를 모니터링하는 canary 추가 고려

### 2. ID: `SZ0-T4-002`

2. Severity: **P3** (정보성)
3. 현상 요약:
   - `_score_sentence()` (L628-670)과 `_score_passage()` (L554-570)는 하드코딩된 키워드 사전으로 문장/문단에 수치 점수를 부여한다.
   - 대원칙 1 "Python은 수집만, 판단은 LLM이" 위반 여부가 사전 이슈로 제기되었으나, **위반 아님**으로 판정한다.
4. 판정 근거:
   - 함수는 "이 문장이 좋은가?"를 판단하는 것이 아니라, "감각어 밀도가 높고 클리셰가 적은" 문장을 통계적으로 필터링한다.
   - 결과는 LLM에게 전달되는 예시 선별에만 사용된다. 최종 판단(이 예시를 어떻게 활용할지)은 LLM이 수행한다.
   - CLAUDE.md 명시: "통계적 점수"는 위반 아님.
   - 시스템 내 유사 패턴: `numeric_consistency_checker.py` (Python-only 9개 검사), `pattern_tracker.py` (LLM 0회) 모두 공인된 수집 패턴.
5. 코드 근거:
   - `modules/core/stage0/style_extractor.py:628-670` — `_score_sentence()`
   - `modules/core/stage0/style_extractor.py:554-570` — `_score_passage()`
   - `modules/core/stage0/style_extractor.py:209-241` — 키워드 사전 (`_SENSORY_WORDS`, `_CLICHE_MARKERS`, `_ACTION_VERBS`, `_INVESTMENT_*`)
6. 후속 조치: 없음. 현행 유지.

### 3. ID: `SZ0-T4-003`

2. Severity: **P3** (정보성)
3. 현상 요약:
   - StyleGuide는 Stage 0에서 생성되어 Director 심사 없이 Stage 4 CW 프롬프트에 직접 주입된다.
   - 대원칙 3 "디렉터 주권주의" 위반 여부가 사전 이슈로 제기되었으나, **위반 아님**으로 판정한다.
4. 판정 근거:
   - 대원칙 3의 범위: "합격/불합격/수정 지시"는 **원고 품질** 결정권. StyleGuide는 **집필 파라미터**(톤, 시점, 리듬 규칙)이지 원고 자체가 아님.
   - 유사 패턴: `config/prompts/*.yaml` (43개), `WritingDirective`, `genre_guards/*.py` 모두 Director 심사 없이 CW에 직접 주입.
   - Director는 StyleGuide 준수 여부를 **간접적으로** 평가: self-critique 체크 15(톤 일관성), 16(POV 일관성)이 Director에게 보고됨.
   - Stage 4 로드 시 Bible POV 우선 보정(`stage4_orchestrator.py:1500-1509`)으로 StyleGuide 내 POV 오류도 runtime에서 교정됨.
5. 코드 근거:
   - `modules/core/stage4_orchestrator.py:1492-1564` — StyleGuide 로드 + `_SessionConfig` 저장
   - `modules/domain/agents/chief_writer_context.py:500-501` — CW 프롬프트 주입
   - Director 에이전트 코드 (`director*.py`) — StyleGuide 참조 없음 (확인 완료)
6. 후속 조치: 없음. 현행 아키텍처 적합.

---

## 오탐 제거 요약

| 후보 | 내용 | 제거 사유 |
|------|------|-----------|
| D | `_ensure_client()` 직접 Gemini Client 생성 | `generate_content_via_router()` 사용으로 router 추상화 준수. Client 객체는 router에 전달만 됨 |
| E | 캐시 `_cache_meta_matches()` 누락 키 허용 | ROP-T4 감사 PASS2-C에서 검증 완료. 구형 캐시는 `cache_meta_version` 불일치로 자동 재분석 강제 |

---

## Coverage Gap Log

### Gap 1: `to_prompt()` + `reference_excerpt` 합산 크기 모니터링

- CW 프롬프트 전체 크기를 runtime에서 측정/경고하는 메커니즘이 없다.
- `smart_truncate()`가 `prev_manuscripts_text`에만 적용되고 `reference_excerpt`에는 미적용.
- 향후 대용량 프로젝트에서 프롬프트 크기 초과 시 조용히 실패할 수 있다.

### Gap 2: `_score_sentence()` / `_score_passage()` 키워드 사전 커버리지

- 현재 10개 장르 중 투자물만 장르별 사전(`_INVESTMENT_*`)이 있다.
- 나머지 9개 장르는 무협 기본 사전(`_SENSORY_WORDS`, `_ACTION_VERBS`)을 공유.
- 로맨스, 요리, 작곡가 등 비전투 장르에서 감각어/액션동사 사전이 부적합할 수 있으나, 이는 품질 최적화 이슈이지 정합성 결함은 아님.

### Gap 3: `_deep_llm_analysis()` front/back 샘플 중복 가능성

- `style_extractor.py:754-755`: `back_samples = samples[3:] or samples[-3:]`
- 원고가 6화 미만일 때 `samples`가 6개 미만이면 `samples[3:]`가 빈 리스트 → `samples[-3:]`로 폴백 → front/back 샘플이 동일해질 수 있다.
- 영향: LLM 분석이 전반부 편향. 실제 위험은 낮음 (소규모 원고 분석 시에만 발생).

### Gap 4: ROP-T4 기존 findings 연계

- ROP-T4-001 (P1): live artifact POV provenance 미갱신 — 이번 감사 범위와 직접 관련 없으나, StyleGuide cache가 구형 포맷일 때 `_apply_pov_contract()`가 runtime 보정을 수행한다는 점은 확인됨.
- ROP-T4-002 (P2): operator surface raw POV 노출 — StyleGuide `to_prompt()` 출력은 `effective_pov` 보정 후 생성되므로 CW 프롬프트에는 영향 없음. 단 operator dashboard에서는 여전히 raw POV가 보일 수 있음.

### Gap 5: `_llm_call()` 전 모델 실패 시 빈 dict 미반환

- `_llm_call()` (L1101): 전 모델 실패 시 `raise last_err` — 호출부 `_deep_llm_analysis()` (L801-802)와 `_generate_anti_patterns()` (L879-881)에서 `except Exception`으로 잡아 `{}`를 반환.
- 에러 처리 자체는 정상. 단, 전 모델 실패 시 `qualitative = {}`가 되어 스타일 가이드에 LLM 분석 결과가 완전히 누락될 수 있다. 이는 graceful degradation으로 의도된 동작.
