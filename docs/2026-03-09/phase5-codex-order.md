# Phase 5 코덱스 오더 — SC (Style Cloning 강화)

> ⚠️ **반드시 UTF-8 인코딩으로 읽을 것**
> 작성일: 2026-03-09
> 상태: 감리 완료 — 구현 대기
> 전수 조사: 3회 완료 (오탐 제거)

---

## 현상 분석

참조 원고 `config/style_references/investment/참조작품1/0_합본.txt`:
- 파일 크기: 10,348,911 bytes / **4,247,609자** (UTF-8)
- 유니코드 따옴표 대화: **41,378개** (\u201c\u201d 사용)

현재 StyleExtractor 파이프라인 커버리지:

| 단계 | 데이터량 | 커버리지 |
|------|----------|----------|
| 원본 | 4,247,609자 | 100% |
| Python 샘플링 (`MAX_ANALYSIS_CHARS=500,000`) | 50만자 | ~12% |
| LLM 전달 (`_sample_batches` 3×8,000) | 2.4만자 | ~0.6% |
| LLM 심층분석 (`_deep_llm_analysis`) | 2만자 캡 | ~0.5% |
| Anti-AI 분석 (`_generate_anti_patterns`) | 8,000자 | ~0.2% |
| 최종 `style_guide.json` | 12,601자 | ~0.3% |

### 구체적 문제점
1. **샘플 구간 부족**: 초반/중반/후반 3구간만 → 작품 전체 문체 변화 누락
2. **대표 문장 25개 한계**: 420만자 원고에서 상위 25개는 너무 적음
3. **모범 문단 8개 한계**: 다양한 씬 유형 커버 불가
4. **CW가 원작 원문 미참조**: CW는 `to_prompt()` 결과(~2,000자 규칙)만 받음. 원작 문체를 직접 보지 못함
5. **LLM 1회 분석**: 2만자 1회 분석으로는 깊이 부족
6. **모범 문단 스코어링 무협 편향**: `_SENSORY_WORDS`/`_ACTION_VERBS` 기반 → 투자물 문단 미선별

### 기존 인프라 현황 (전수 조사 확인)

**StyleGuide 데이터 플로우**:
```
Stage 0: StyleExtractor.extract_from_references(genre)
  → StyleGuide 생성 → style_guide.json 캐싱 (config/style_references/{genre}/)
  → DB anchor 저장 (current_project.save_v20_anchor("style_guide", guide.to_dict()))

Stage 4: stage4_orchestrator._prepare_stage4_session() L1317
  → current_project.load_v20_anchor("style_guide")
  → StyleGuide.from_dict(saved_style)
  → loaded_sg.to_prompt() → style_guide 문자열 (~2,000자)
  → _SessionConfig.style_guide에 저장

Stage 4 → CW: stage4_interview_round._build_common_writer_kwargs() L206
  → _common_writer_kwargs["style_guide"] = style_guide
  → chief_writer.generate_ensemble(style_guide=style_guide)
  → context_builder.build_common_context(style_guide=style_guide)
  → build_chief_writer_main_prompt(style_guide=...) L441
  → common_context 문자열에 포함 → 캐싱 대상
```

**CW 캐싱 구조**:
```
chief_writer.generate_ensemble() L260-268:
  cache_info = self._get_or_create_context_cache(
      cache_type="manuscript",
      content=common_context,  ← bible+style_guide+blueprint+prev_ms+hud+arc_doc+...
      ttl_seconds=600,         ← 10분
      project_name=f"ep{ep_num}",
  )
  → 3개 전략(balanced/narrative/tension)이 같은 ep 내에서 캐시 공유
  → ep 변경 시 blueprint/prev_manuscript 변동 → content_hash MISS → 재생성
```

**핵심 제약**: `common_context`는 ep별로 변동 → 참조 원고 발췌를 여기에 넣어도 **매 ep마다 재캐싱**. 24시간 TTL 무의미. 다만 **같은 ep 내 3전략 공유** 시 발췌 포함분 토큰 절감 (3회→1회).

---

## Part A: StyleExtractor 개선 (5 TF)

> 대상 파일: `modules/core/stage0/style_extractor.py` (단일 파일)
> 난이도: LOW
> 비용: Stage 0 1회성 (매 에피소드 아님)

### TF-SC1: 샘플 구간 확대
- `_sample_batches()`: `num_batches` 기본값 3 → **6**
- `_deep_llm_analysis()`: `batch_size` 8000 → **10000**
- `combined_sample` 캡: `[:20000]` → `[:50000]`
- **효과**: LLM 전달량 2.4만 → 6만자 (~2.5배)

### TF-SC2: 대표 샘플 풀 확대
- `_curate_samples()` 저장 상한:
  - `sample_sentences`: `[:25]` → `[:50]`
  - `sample_dialogues`: `[:15]` → `[:30]`
  - `exemplary_passages`: `[:8]` → `[:15]`
  - `scene_transitions`: `[:8]` → `[:12]`
- `to_prompt()` 출력 캡:
  - `exemplary_passages[:5]` → `[:8]`
  - `sample_dialogues[:5]` → `[:8]`
  - `scene_transitions[:5]` → `[:8]`
  - `signature_expressions[:8]` → `[:12]`
  - `anti_ai_patterns[:10]` → `[:15]`
  - `forbidden_expressions[:8]` → `[:10]`

### TF-SC3: Python 샘플링 커버리지 확대
- `extract_from_drafts()`: `MAX_ANALYSIS_CHARS` 500,000 → **1,000,000** (~24% 커버리지)
- `_sample_text()`: 3분할 → **5분할** (초반/초중반/중반/중후반/후반)
  ```python
  # 현재 (3분할)
  chunk = max_chars // 3
  mid = len(text) // 2
  return text[:chunk] + "\n\n" + text[mid - chunk//2 : mid + chunk//2] + "\n\n" + text[-chunk:]

  # 변경 (5분할)
  chunk = max_chars // 5
  q1, q2, q3 = len(text) // 4, len(text) // 2, len(text) * 3 // 4
  return (text[:chunk] + "\n\n"
      + text[q1 - chunk//2 : q1 + chunk//2] + "\n\n"
      + text[q2 - chunk//2 : q2 + chunk//2] + "\n\n"
      + text[q3 - chunk//2 : q3 + chunk//2] + "\n\n"
      + text[-chunk:])
  ```
- `_analyze_rhythm()`: `drafts[:20]` → `drafts[:50]`

### TF-SC4: 다회차 LLM 분석
- `_deep_llm_analysis()`: 단일 호출 → **2회 분할**
  - 1회차: 전반부 3배치 → 톤/묘사/어휘/감정/액션스타일
  - 2회차: 후반부 3배치 → 대화패턴/서명표현/금지표현
  - 결과 병합: `{**result1, **result2}` (후반부가 전반부 키 보완)
- **비용**: LLM 1회 → 2회 (Stage 0 1회성, API 0.5초 딜레이 유지)

### TF-SC5: 모범 문단 장르별 스코어링
- `_curate_samples()` 모범 문단 점수 계산 (L401-412):
  - 현재: `_SENSORY_WORDS * 3 + _ACTION_VERBS * 1 - _CLICHE_MARKERS * 2 + 대화포함 +2` (무협 편향)
  - 변경: `self.genre` 분기 추가
    ```python
    if self.genre in ("investment", "투자물"):
        score = sum(3 for w in _INVESTMENT_FINANCE_WORDS if w in p)
        score += sum(2 for w in _INVESTMENT_NEGOTIATION_VERBS if w in p)
        if _INVESTMENT_NUMERIC_RE.search(p):
            score += 2
    else:
        score = sum(3 for w in _SENSORY_WORDS if w in p)
        score += sum(1 for v in _ACTION_VERBS if v in p)
    score -= sum(2 for c in _CLICHE_MARKERS if c in p)
    if '"' in p or '\u201c' in p:
        score += 2
    ```
  - `_score_sentence()`과 동일한 장르 분기 패턴

---

## Part B: CW 참조 원고 발췌 주입 (4 TF)

> 난이도: LOW
> 비용: 발췌 50K자가 common_context에 추가 → 같은 ep 내 3전략 캐시 공유로 토큰 절감

### TF-RC1: StyleGuide에 참조 원고 발췌 필드 추가
- 파일: `modules/core/stage0/style_extractor.py`
- `StyleGuide` dataclass (L20): `reference_excerpt: str = ""` 필드 추가
- `extract_from_drafts()` (L306): `merged["reference_excerpt"] = self._build_reference_excerpt(sampled_text)` 추가
- 신규 메서드 `_build_reference_excerpt(sampled_text: str) -> str`:
  - `_curate_samples()`에서 이미 선별한 `exemplary_passages`를 활용
  - 추가로: 점수 상위 **대화+서술 혼합 문단** (200~800자, 대화 1개+ 포함)을 **50,000자 상한**으로 수집
  - 선별 기준: `_score_sentence` 점수 기반 (장르 분기 적용됨)
  - 발췌 앞에 `[참조 원고 발췌 — 이 문체를 따라 쓸 것]` 헤더 추가
- `style_guide.json` 크기 영향: 12KB → ~62KB (캐시 파일, 1회성)

### TF-RC2: CW common_context에 발췌 섹션 추가
- 파일: `modules/domain/agents/chief_writer_context.py`
- `build_common_context()` 파라미터 (L43): `reference_excerpt: str = ""` 추가
- `build_chief_writer_main_prompt()` 호출부 (L419-450): `reference_excerpt_section` 인자 추가
- 파일: `modules/domain/agents/chief_writer_prompts.py`
- `build_chief_writer_main_prompt()` (L50): `reference_excerpt_section: str = ""` 파라미터 추가
- 프롬프트 템플릿 (L88~): `{style_guide}` 블록 직후에 배치:
  ```
  {reference_excerpt_section}
  ```
- `chief_writer_context.py` L441 이후:
  ```python
  reference_excerpt_section=(
      f"\n## 참조 원고 발췌 (이 문체를 따라 쓸 것)\n{self.host._escape_braces(reference_excerpt)}"
      if reference_excerpt else ""
  ),
  ```

### TF-RC3: Stage4 → CW 배선
- 파일: `modules/core/stage4_orchestrator.py`
- `_prepare_stage4_session()` (L1317-1337): `loaded_sg` 로드 시 `reference_excerpt` 추출
  ```python
  reference_excerpt = loaded_sg.reference_excerpt if hasattr(loaded_sg, "reference_excerpt") else ""
  ```
- `_SessionConfig` (L155): `reference_excerpt: str = ""` 필드 추가
- `_SessionConfig` 반환부 (L1382-1395): `reference_excerpt=reference_excerpt` 추가
- 파일: `modules/core/stage4_types.py`
- `_RoundContext` dataclass (slots=True): `reference_excerpt: str = ""` 필드 추가
- 파일: `modules/core/stage4_context_builder.py`
- `build_round_context()`: `reference_excerpt` 파라미터 추가 + `_RoundContext` 생성 시 전달
- 파일: `modules/core/stage4_orchestrator.py` (2차 수정 — `build_round_context()` 호출부)
- `build_round_context()` 호출 시 `reference_excerpt=session.reference_excerpt` 전달
- 파일: `modules/core/stage4_interview_round.py`
- `_build_common_writer_kwargs()` (L199-229): `"reference_excerpt": round_ctx.reference_excerpt` 추가
- 파일: `modules/domain/agents/chief_writer.py`
- `generate_ensemble()` (L142-188): `reference_excerpt: str = ""` 파라미터 추가
- `build_common_context()` 호출부 (L220-258): `reference_excerpt=reference_excerpt` 전달
- **참고 (P2)**: `regenerate_with_feedback()`/`_generate_candidates_with_partial()` 재시도 경로에서는 reference_excerpt 미전달. round 0 캐시에서 이미 common_context에 포함되어 있으므로 허용.

### TF-RC4: CW InPlace 패치 경로 배선
- 파일: `modules/core/stage4_interview_round.py`
- `_execute_pass_with_fix_loop()` L1303: `style_guide=style_guide` 전달 시 `reference_excerpt` 도 전달 확인
- `_run_full_rewrite_round()` L1877: 동일 확인
- **핵심**: `_common_writer_kwargs`에 이미 포함되므로 `**_common_writer_kwargs` 전개 시 자동 전달. 단, **InPlace 경로**(`chief_writer.inplace_patch()`)는 `generate_ensemble`과 별도 호출 — InPlace는 원고 수정이므로 reference_excerpt 불필요. **추가 배선 불필요**.

---

## 전수 조사 결과 — 오탐/폐기 항목

| 항목 | 결과 | 이유 |
|------|------|------|
| ~~dialogue_ratio=0.0 regex 버그~~ | **오탐** | regex `["""]`는 `\u201c\u201d`를 정상 매칭. 41,378개 대화 감지됨. `dialogue_ratio=0.0`은 **캐시 재생성 필요** (style_guide.json이 옛날 분석 결과). SC 구현 후 캐시 삭제→재생성하면 해결 |
| ~~TF-SC5 (대화 regex 강화)~~ | **폐기** | 원고가 `\u201c\u201d` 사용, 기존 regex 정상 작동. 기본 `"` 추가 불필요 |
| ~~TF-RC5 (별도 캐시 분리)~~ | **폐기** | Gemini `cached_content` 1개 제한. common_context에 합치는 TF-RC2가 현실적 |
| ~~24시간 TTL~~ | **축소** | common_context가 ep별 변동 → TTL 확대 효과 없음. 기존 600초 유지 |

---

## 실행 순서

```
Step 1: TF-SC3 (Python 샘플링 커버리지 1M + 5분할 + 리듬 50화)
Step 2: TF-SC2 (대표 샘플 풀 확대 — 저장 상한 + to_prompt 출력 캡)
Step 3: TF-SC5 (모범 문단 장르별 스코어링)
Step 4: TF-SC1 (LLM 배치 6구간 + 배치크기 10K + 합산캡 50K)
Step 5: TF-SC4 (다회차 LLM 분석 2회 분할)
Step 6: TF-RC1 (StyleGuide.reference_excerpt 필드 + _build_reference_excerpt)
Step 7: TF-RC2 (CW common_context 참조 원고 발췌 섹션 추가)
Step 8: TF-RC3 (Stage4 → CW reference_excerpt 배선)
Step 9: TF-RC4 (InPlace 경로 확인 — 추가 배선 불필요 확인)
Step 10: 캐시 삭제 (style_guide.json) → 재생성 필요 고지
Step 11: 테스트 실행 → 3,614 passed 유지
```

---

## 체크리스트

### Part A: StyleExtractor 개선 (파일 1개)
- [ ] TF-SC3: MAX_ANALYSIS_CHARS 500K → 1M
- [ ] TF-SC3: _sample_text 3분할 → 5분할
- [ ] TF-SC3: _analyze_rhythm drafts[:20] → [:50]
- [ ] TF-SC2: _curate_samples 저장 상한 확대 (sentences 50, dialogues 30, passages 15, transitions 12)
- [ ] TF-SC2: to_prompt() 출력 캡 확대 (passages 8, dialogues 8, transitions 8, expressions 12, anti_ai 15, forbidden 10)
- [ ] TF-SC5: _curate_samples 모범 문단 장르별 스코어링 (investment 분기)
- [ ] TF-SC1: _sample_batches num_batches 3→6
- [ ] TF-SC1: _deep_llm_analysis batch_size 8K→10K, combined_sample 캡 20K→50K
- [ ] TF-SC4: _deep_llm_analysis 2회 분할 (전반부 톤/묘사, 후반부 대화/표현)

### Part B: CW 참조 원고 발췌 주입 (파일 5개)
- [ ] TF-RC1: StyleGuide dataclass `reference_excerpt: str = ""` 필드 추가
- [ ] TF-RC1: `_build_reference_excerpt()` 신규 메서드 (50K자 상한, 대화+서술 혼합 문단)
- [ ] TF-RC1: `extract_from_drafts()` 병합에 reference_excerpt 추가
- [ ] TF-RC2: `chief_writer_context.build_common_context()` 파라미터 추가
- [ ] TF-RC2: `chief_writer_prompts.build_chief_writer_main_prompt()` 파라미터 + 템플릿 추가
- [ ] TF-RC3: `stage4_orchestrator._prepare_stage4_session()` reference_excerpt 추출
- [ ] TF-RC3: `_SessionConfig` 필드 추가
- [ ] TF-RC3: `stage4_types._RoundContext` 필드 추가
- [ ] TF-RC3: `stage4_context_builder.build_round_context()` 파라미터 + 전달
- [ ] TF-RC3: `stage4_orchestrator` → `build_round_context()` 호출 시 전달
- [ ] TF-RC3: `stage4_interview_round._build_common_writer_kwargs()` 배선
- [ ] TF-RC3: `chief_writer.generate_ensemble()` 파라미터 추가 + 전달
- [ ] TF-RC4: InPlace 경로 확인 (추가 배선 불필요)
- [ ] 테스트: 3,614 passed 유지
- [ ] 캐시 삭제 고지: `config/style_references/investment/style_guide.json` 삭제 후 Stage 0 재실행 필요

---

## 수정 대상 파일 목록

| 파일 | TF | 변경 내용 |
|------|-----|----------|
| `modules/core/stage0/style_extractor.py` | SC1~5, RC1 | 전량 (상수, 메서드, dataclass) |
| `modules/domain/agents/chief_writer_context.py` | RC2 | `build_common_context()` 파라미터 1개 + 섹션 조립 1줄 |
| `modules/domain/agents/chief_writer_prompts.py` | RC2 | `build_chief_writer_main_prompt()` 파라미터 1개 + 템플릿 1줄 |
| `modules/core/stage4_orchestrator.py` | RC3 | `_prepare_stage4_session()` 2줄 + `_SessionConfig` 1줄 + `build_round_context()` 호출 1줄 |
| `modules/core/stage4_types.py` | RC3 | `_RoundContext` 필드 1줄 |
| `modules/core/stage4_context_builder.py` | RC3 | `build_round_context()` 파라미터 1개 + 전달 1줄 |
| `modules/core/stage4_interview_round.py` | RC3 | `_build_common_writer_kwargs` 1줄 |
| `modules/domain/agents/chief_writer.py` | RC3 | `generate_ensemble()` 파라미터 1개 + 전달 1줄 |

---

## 비용 분석

| 항목 | 현재 | 변경 후 |
|------|------|---------|
| Stage 0 LLM 호출 | 2~3회 | 4~5회 (1회성, 캐시 재생성 시에만) |
| style_guide.json 크기 | 12KB | ~65KB (reference_excerpt 50K 포함) |
| CW common_context 크기 | ~30K자 | ~80K자 (발췌 50K 추가) |
| CW 캐시 TTL | 600초 유지 | 변동 없음 |
| CW 같은 ep 내 토큰 절감 | 캐시 HIT 2/3 | 동일 (발췌 포함분도 캐시 공유) |

**ROI**: Stage 0 1회성 비용 미미. CW common_context +50K는 Gemini 2M 컨텍스트 대비 2.5% → 충분히 여유. 캐시 내 발췌 포함으로 **3전략 중 2회는 발췌 토큰 무과금**.
