# QI-1: 원고 품질 개선 명세 (엔딩 반복 + 클로닝 강화 + 감성 하드코딩 제거)

> 작성일: 2026-03-09
> 상태: **감리 3·4·5차 3연속 PASS — 구현 승인**
> 구현: **완료 (A1~A6 + B2~B5 + C1~C4) / B1(레퍼런스 원고 배치) 사용자 제공 대기**
> 재검증: **2026-03-10 코드베이스 3pass 완료**
> 관련: `pacing-improvement-spec.md` (PC-1, 페이싱)

---

## 0. 2026-03-10 코드베이스 재검증 (3pass)

### Pass 1. 항목별 구현 확인

#### A. 엔딩 후킹 다양화

| 항목 | 상태 | 코드 근거 | 테스트/감리 메모 |
|---|---|---|---|
| QI-1-A1 | 완료 | `config/prompts/ensemble.yaml:337`에 선언문 금지, 엔딩 유형 다양화, 이전 화 구조 회피 가이드가 반영됨 | 전용 테스트는 없지만 설정값 자체는 코드 기준 확정 |
| QI-1-A2 | 완료 | `modules/domain/agents/chief_writer_quality.py:704-729`에서 리터럴 20자 매칭이 키워드 2개 이상 의미 매칭으로 교체됨 | 전용 회귀 테스트는 얕다. 구현 존재와 호출 경로는 코드로 확인 |
| QI-1-A3 | 완료 | `modules/core/pattern_tracker.py:67-90`, `modules/core/pattern_tracker.py:240-244`에 `recent_ending_texts` 필드와 실제 엔딩 문구 수집/요약이 존재 | `tests/test_pattern_tracker.py:45-54`는 요약 텍스트 경로를 간접 커버하나, 새 필드 전용 회귀는 얕다 |
| QI-1-A4 | 완료 | `modules/core/stage4_types.py:81`, `modules/core/writing_directive_generator.py:48-75,203`, `modules/domain/agents/chief_writer_context.py:272-279`에 `ending_avoid_phrases` 생성·병합·주입 경로가 모두 존재 | `tests/test_writing_directive.py:1-74`는 기본 parse/generate를 커버하나 회피 문구 병합 전용 테스트는 없다 |
| QI-1-A5 | 완료 | `modules/domain/agents/chief_writer_quality.py:277-278`, `modules/domain/agents/chief_writer_quality.py:732-764`에 `3-gram` 자카드 기반 엔딩 참신성 체크가 추가됨 | 전용 회귀 테스트는 없다. self-critique 체크리스트 편입은 코드로 확인 |
| QI-1-A6 | 완료 | `modules/domain/agents/blueprint_ensemble.py:47-73`에 action/emotion/dialogue 전략별 엔딩 유형 지시가 들어감 | 전용 테스트는 없지만 프롬프트 자산에 직접 반영됨 |

#### B. 투자물 클로닝 강화

| 항목 | 상태 | 코드 근거 | 테스트/감리 메모 |
|---|---|---|---|
| QI-1-B1 | 사용자 제공 대기 | 현재 인벤토리는 `config/style_references/investment/참조작품1/0_합본.txt` 중심이며, 폴더에도 단일 참조작품만 확인됨 | 코드 변경 대상이 아니라 외부 자산 배치 작업이다 |
| QI-1-B2 | 완료 | `modules/core/stage0/style_extractor.py:244`, `modules/core/stage0/style_extractor.py:499-522`, `modules/core/stage0/style_extractor.py:785`에 `genre` 동기화와 투자물 전용 가중치 분기가 존재 | Stage 0 회귀 테스트는 제한적이므로 구현 완료와 테스트 밀도는 분리해서 봐야 한다 |
| QI-1-B3 | 완료 | `modules/core/stage0/style_extractor.py:695-704`에 투자/재벌 장르 전용 Anti-AI 힌트가 들어감 | 전용 테스트는 없지만 프롬프트 본문에 직접 반영됨 |
| QI-1-B4 | 완료 | `modules/core/stage0/style_extractor.py:51`, `modules/core/stage0/style_extractor.py:185-192`, `modules/core/stage0/style_extractor.py:314`에 투자물 전용 섹션과 `genre` 전달이 구현됨 | 전용 회귀 테스트는 없지만 `to_prompt()` 경로는 코드상 확정 |
| QI-1-B5 | 완료 | `modules/core/stage0/style_extractor.py:73-90`에 투자물 1인칭 제한 규칙이 추가됨 | 전용 테스트는 없고, Stage 0 POV 메뉴 테스트와는 별도다 |

#### C. 감성/톤 하드코딩 제거

| 항목 | 상태 | 코드 근거 | 테스트/감리 메모 |
|---|---|---|---|
| QI-1-C1 | 완료 | `modules/core/character_voice_profiler.py:75-103` 주석이 검출용 참고 예시로 바뀌었고, 실제 사용처도 `modules/core/character_voice_profiler.py:260-271`의 분석 로직에 한정됨 | “하드코딩 삭제”가 아니라 “검출용/참고용 전환”으로 보는 것이 정확하다 |
| QI-1-C2 | 완료 | `modules/core/character_voice.py:88-96`가 감탄사 예시 풀로 정리됐고, 사용처는 `modules/core/character_voice.py:176-184`의 검출 로직이다 | 역시 삭제가 아니라 예시/분석용 전환이다 |
| QI-1-C3 | 완료(주경로) | `modules/domain/agents/chief_writer.py:171,648,948`, `modules/domain/agents/chief_writer_context.py:69,1073-1092`, `modules/core/stage4_orchestrator.py:688-695`, `modules/domain/agents/writer.py:66`에서 기본값 제거와 Bible 기반 로드가 반영됨 | `tests/test_chief_writer_context.py:197-205`, `tests/test_chief_writer.py:627-639`, `tests/integration/test_patch_wiring.py:613,702,796,880`, `tests/test_pass_with_fix.py:105`가 관련 경로를 일부 커버한다 |
| QI-1-C4 | 완료 | `modules/core/lore_manager.py:128-133`에서 기본 톤이 빈 문자열로 바뀌고, 빈 톤이면 톤 라인을 생략한다 | 전용 회귀 테스트는 없다 |

### Pass 2. QI-1 외 기적용 보강

| 문제군 | 기적용 보강 | 코드 근거 | 의미 |
|---|---|---|---|
| 엔딩 후킹 | CW 품질게이트 밖에서도 ending_hook 연결을 별도 감시 | `modules/core/cross_agent_verifier.py:198-255`, `modules/core/writer_template.py:133-183,362-365`, `modules/core/constitutional_checker.py:276-278,428-460`, `modules/core/context_advisor.py:436-444`, `modules/core/dynamic_prompt_weighting.py:130` | QI-1-A2/A6 효과가 CW 단일 레이어에만 머물지 않고 Stage 2~4의 보조 검증·주입 회로로 확장돼 있음 |
| 투자물 집필 규칙 | Stage 0 외에도 Chief Writer 프롬프트에 투자물 전용 규칙을 추가 주입 | `modules/domain/agents/chief_writer_prompts.py:32`, `modules/domain/agents/chief_writer_context.py:418-450` | B4/B5가 Stage 0 style guide에만 갇히지 않고 실제 집필 컨텍스트까지 확장돼 있음 |
| 투자물 수치/상태 일관성 | 투자물 전용 산술 검산, 금융 상태 추적, Director advisory 경로가 별도로 존재 | `modules/core/response_schemas.py:255-272`, `modules/domain/agents/state_tracker.py:252,1445-1477`, `modules/domain/agents/state_tracker_financial.py:20-80`, `modules/domain/agents/four_phase_arc_generator.py:695-764`, `modules/core/stage4_post_processor.py:208-229` | 투자물 품질은 단순 문체 클로닝을 넘어 수치/상태 일관성 레이어까지 이미 보강돼 있음 |
| 투자물 운영 커버리지 | 투자물 감지·라이브러리·수치 advisory 경로에 테스트가 일부 존재 | `tests/test_stage2_pipeline.py:308-316`, `tests/test_state_tracker.py:384-395`, `tests/test_investment_math_wiring.py:51-88` | 구현 완료와 별개로 투자물 운영 경로 일부는 회귀 보호도 확보돼 있음 |

### Pass 3. 오탐 제거

- `QI-1은 미착수 설계서다`는 오탐다. 코드 기준으로는 `A1~A6 + B2~B5 + C1~C4`가 이미 반영돼 있다.
- `B1도 코드 미완료 항목이다`는 오탐다. B1은 시스템 준비가 아니라 사용자 제공 레퍼런스 원고 수량의 문제다.
- `C1/C2가 키워드 테이블을 아직 가지고 있으니 미구현이다`도 오탐다. 이 두 항목의 목표는 삭제가 아니라 `검출용/예시 풀 전환`이며, 현재 코드는 그 상태에 맞다.
- `C3가 모든 레거시 경로까지 완전 무결하게 청소됐다`는 과장이다. 주경로는 완료됐지만, `modules/domain/agents/writer.py:58-127`의 레거시 폴백은 1화에서 빈 `intro_dna` 헤더가 남을 여지가 있다. 다만 `rg -n "write_v20_manuscript\\(" main_a.py modules tests` 기준 호출 경로는 검출되지 않아 운영 리스크는 낮다.
- 구현 완료와 테스트 완료는 같은 말이 아니다. A1/A2/A5/B2~B5/C1/C2/C4는 코드 반영은 확인됐지만 dedicated regression test는 얕거나 없다.

## 1. 문제 정의 (3건)

### 1-A. 엔딩 후킹 반복 (AI티)

**증상**: "이제 내 세상이 올 것이다" 류의 선언문 엔딩이 매 화 반복. AI가 쓴 느낌.

**근본 원인 분석**:

| # | 원인 | 위치 | 영향도 |
|---|------|------|--------|
| E-1 | `ending_hook` 50자 제한만 있고 품질/다양성 가이드 없음 | `ensemble.yaml` L334 | **HIGH** |
| E-2 | `_check_ending_hook_presence()`가 앞 20자 **리터럴 매칭** 강제 → CW가 Blueprint 문구 그대로 복사 | `chief_writer_quality.py` L710-712 | **CRITICAL** |
| E-3 | PatternTracker가 엔딩 **카테고리만** 추적 (선언문/수사의문문/차가운미소), **구체 문구** 미추적 | `pattern_tracker.py` L52-58, L275-287 | **HIGH** |
| E-4 | WritingDirective에 `ending_phrases_to_avoid` 필드 없음 → CW가 최근 엔딩 문구를 모름 | `writing_directive_generator.py` | **HIGH** |
| E-5 | Blueprint 3개 전략(action/emotion/dialogue)이 ending_hook 생성을 차별화하지 않음 | `blueprint_ensemble.py` | **MEDIUM** |
| E-6 | Self-critique에 "엔딩 참신성" 체크 없음 (presence만 체크, novelty 미체크) | `chief_writer_quality.py` L209-275 | **HIGH** |

### 1-B. 원고 클로닝 약점 (투자물)

**증상**: 레퍼런스 문체를 충분히 모방하지 못함.

**근본 원인 분석**:

| # | 원인 | 위치 | 영향도 |
|---|------|------|--------|
| C-1 | `config/style_references/investment/` 디렉토리에 레퍼런스 존재하나 `참조작품1` 1편뿐 (합본 백업+스타일 JSON+시드만). 다양성 부족 | Stage 0 | **HIGH** |
| C-2 | `_score_sentence()` 감각어·액션 동사 기준이 무협 편향 (시큰/찌릿/베었/찔렀) — 투자물 부적합 | `style_extractor.py` L392-418 | **HIGH** |
| C-3 | Anti-AI 패턴이 범용 (감정 직접 서술 금지 등) → 투자물 특화 패턴 없음 | `style_extractor.py` L534-568 | **MEDIUM** |
| C-4 | `StyleGuide.to_prompt()`에 투자물 전용 섹션 없음 (금융 용어법, 수치 서술 패턴) | `style_extractor.py` L108-176 | **MEDIUM** |
| C-5 | POV 규칙이 장르 불인지 — 투자물 1인칭 시 "시장 전체 조망 불가" 제약 없음 | `style_extractor.py` L71-106 | **LOW** |

### 1-C. 감성/톤 하드코딩 (레거시)

**증상**: 시니컬 캐릭터가 항상 욕설. 캐릭터 감정이 단조로움.

**전수조사 결과**:

| # | 하드코딩 | 위치 | 심각도 |
|---|---------|------|--------|
| T-1 | `PERSONALITY_PATTERNS`: aggressive→["죽여","박살","꺼져","닥쳐","빌어먹을"], cold→["상관없","필요없"], warm→["걱정","괜찮","고마워"] | `character_voice_profiler.py` L75-102 | **P1** |
| T-2 | `EXCLAMATION_PATTERNS`: CRUDE→["쳇","젠장","씨발","빌어먹을"] | `character_voice.py` L83-91 | **P1** |
| T-3 | `intro_dna` 기본값 = `"CYNICAL"` (4파일 7곳) → 1화 주인공 자동 시니컬 | `chief_writer.py` L170/L645/L943, `chief_writer_context.py` L68/L1060, `stage4_orchestrator.py` L686, `writer.py` L66 | **P1** |
| T-4 | `emotion_keywords` 5개 감정만 (despair/frustration/neutral/hope/triumph) | `emotion_tracker.py` L68-133 | **P2** |
| T-5 | `StyleGuide.tone` 5개 고정 (냉소적/유머/진지/가벼움/어두움) | `style_extractor.py` L25 | **P2** |
| T-6 | `ENSEMBLE_STRATEGIES` 3개 고정 (balanced/narrative/tension) | `chief_writer.py` L67-105 | **P2** |
| T-7 | `VoiceStyle` enum 8개 고정 (formal/informal/archaic/crude/noble/martial/scholarly/merchant) | `character_voice.py` L29-40 | **P2** |
| T-8 | `LoreManager` 기본 톤 = `"격조 있는 무인"` (무협 레거시) | `lore_manager.py` L126-137 | **P1** |

---

## 2. 제안 항목

### QI-1-A: 엔딩 후킹 다양화 (6건)

#### QI-1-A1: ending_hook 품질 가이드 추가

**변경 대상**: `ensemble.yaml` L334

| 현재 | 변경 |
|------|------|
| `"ending_hook": "다음 화 연결 훅 (50자 이내)"` | `"ending_hook": "다음 화 연결 훅 (50자 이내). 선언문('~시작이었다') 연속 사용 금지. 수사의문문·감각묘사·대사 중단·상황 반전 등 매 화 다른 유형 사용. 이전 화 ending_hook과 동일 구조 금지."` |

#### QI-1-A2: CW 엔딩 검증 완화 — 리터럴 매칭 → 의미 매칭

**변경 대상**: `chief_writer_quality.py` L710-712

| 현재 | 변경 |
|------|------|
| `key_fragment = ending_hook[:20]` + `if key_fragment not in tail` (앞 20자 리터럴 매칭) | ending_hook **핵심 키워드 2~3개** 추출 → 키워드 중 2개 이상이 마지막 500자에 포함되면 PASS. 문구 그대로 복사할 필요 없이, **훅의 의미만 반영**하면 합격. |

**변경 코드 (안)**:
```python
# 기존: 리터럴 20자 매칭
# key_fragment = ending_hook[:20]
# if key_fragment not in tail: → severity="high"

# 변경: 핵심 키워드 매칭
import re
keywords = [w for w in re.findall(r"[가-힣]{2,}|[a-zA-Z]{3,}", ending_hook) if len(w) >= 2]
top_keywords = keywords[:5]  # 최대 5개 키워드
if len(top_keywords) < 2:
    return []  # 키워드 부족 → 검사 스킵
matched = sum(1 for kw in top_keywords if kw in tail)
if matched < 2:
    return [{"type": "missing_ending_hook", ..., "severity": "medium"}]  # high→medium 하향
```

**사이드 이펙트**:
- 기존: CW가 ending_hook 문구를 **그대로 복사** → 반복 느낌의 근본 원인
- 변경 후: CW가 ending_hook의 **의미를 자기 문체로 재해석** 가능
- severity `high→medium` 하향 → 엔딩 누락 시 즉시 재작성 대신 advisory 수준
- **위험**: 너무 느슨하면 ending_hook 무시 가능 → `matched < 2` 임계값으로 최소 보장

#### QI-1-A3: PatternTracker에 엔딩 문구 레벨 추적 추가

**변경 대상**: `pattern_tracker.py`

| 현재 | 변경 |
|------|------|
| `_classify_endings()`: 카테고리만 반환 ("선언문", "수사의문문") | 카테고리 + **실제 엔딩 마지막 30자** 수집. `PatternReport.recent_ending_texts: list[str]` 필드 추가. |

**추가 필드**: `PatternReport` (L62-70, 클래스 정의)에 `recent_ending_texts: list[str] = field(default_factory=list)` 추가. `build_report()`에서 직전 N화 원고의 마지막 50자를 수집하여 저장.

#### QI-1-A4: WritingDirective에 회피 목록 추가

**변경 대상**: `writing_directive_generator.py`

| 현재 | 변경 |
|------|------|
| `ending_style` (카테고리만) | `ending_style` + `ending_avoid_phrases: list[str]` (직전 3화 엔딩 문구) |

CW 프롬프트에 "아래 엔딩 문구는 이미 사용했으므로 피하세요:" 주입.

#### QI-1-A5: Self-critique 엔딩 참신성 체크 추가

**변경 대상**: `chief_writer_quality.py` self-critique 체크리스트

현재 체크 11개 (L209-305, `_check_*` 메서드 10개 + 인라인 분량 체크 1건). **12번째 체크 추가**:
- `_check_ending_novelty()`: 현재 원고 마지막 50자 vs `WritingDirective.ending_avoid_phrases` 비교. 3-gram 자카드 유사도 60% 초과 시 severity="medium" 이슈 반환.

#### QI-1-A6: Blueprint 전략별 엔딩 유형 차별화

**변경 대상**: `blueprint_ensemble.py`

3개 전략(action/emotion/dialogue)에 ending_hook 유형 지시 추가:
- action 전략: "물리적 위기/액션 클리프행어로 끝낼 것"
- emotion 전략: "감정적 반전/내면 갈등 여운으로 끝낼 것"
- dialogue 전략: "대사 중단/대화 반전으로 끝낼 것"

---

### QI-1-B: 투자물 클로닝 강화 (5건)

#### QI-1-B1: 레퍼런스 원고 배치

**현황**: `config/style_references/investment/` 디렉토리에 `참조작품1` 1편 + 합본 백업 + 스타일 JSON 존재. 기존 캐시(`style_guide.json`)도 있음.
**작업**: 추가 레퍼런스 원고 4편+ 배치하여 총 5편 이상 확보. 다양한 투자물 문체 샘플링.
- 사용자가 직접 제공해야 함 (저작권). 시스템은 준비 완료.

#### QI-1-B2: `_score_sentence()` 장르별 가중치 분기

**변경 대상**: `style_extractor.py` L392-418

| 현재 | 변경 |
|------|------|
| 감각어 +3 (시큰/찌릿/매캐 등), 액션동사 +2 (베었/찔렀/날렸) — 무협 편향 | `genre` 파라미터 추가 (현재 미수신 → `StyleExtractor.__init__`에 genre 저장 후 `self.genre` 참조). 투자물: **금융 서술어** +3 (매수/매도/레버리지/수익률/청산/포지션), **수치 표현** +2 (N억/N%/N배), **협상·심리전 동사** +2 (제안했다/거절했다/계산했다/판단했다). 기존 감각어는 장르 공통으로 +1 유지. |

#### QI-1-B3: 투자물 Anti-AI 패턴 추가

**변경 대상**: `style_extractor.py` L534-568 (`_generate_anti_patterns`)

LLM 프롬프트에 장르 힌트 추가: "이 작품은 {genre} 장르입니다. 해당 장르에서 AI가 특히 빠지기 쉬운 패턴을 포함해주세요."
투자물 예시 패턴: "수치 과도 반올림", "모든 투자가 성공하는 비현실적 전개", "금융 용어 영어 병기 남용", "숫자 없는 추상적 투자 서술".

#### QI-1-B4: `to_prompt()` 투자물 전용 섹션

**변경 대상**: `style_extractor.py` `to_prompt()` 메서드 (L108-176)

장르가 `investment`일 때 추가 섹션:
```
## 투자물 문체 규칙
- 금융 거래 장면: 구체적 수치(진입가, 매도가, 수익률)를 대사/서술에 자연스럽게 녹일 것
- 전문 용어: 첫 등장 시 맥락으로 설명, 이후 약어 허용 (PER, ROE 등)
- 캐릭터별 금융 지식 깊이: PB는 전문 용어 자유 사용, 초보 투자자는 쉬운 말 사용
```

#### QI-1-B5: POV 장르 인식

**변경 대상**: `style_extractor.py` `_get_pov_rules()` (L71-106)

투자물 1인칭 시 추가 규칙: "주인공의 분석·계산·직감만 서술 가능. 다른 투자자의 의도나 시장 전체 조망은 표정·행동·뉴스 매체를 통해서만 간접 전달."

---

### QI-1-C: 감성/톤 하드코딩 제거 (P1 4건)

#### QI-1-C1: PERSONALITY_PATTERNS 제거 또는 참고용 전환

**변경 대상**: `character_voice_profiler.py` L75-102

| 현재 | 변경 |
|------|------|
| `PERSONALITY_PATTERNS["aggressive"]["keywords"] = ["죽여","박살","꺼져","닥쳐","빌어먹을"]` → Python이 이 키워드를 **직접 주입** | 현재도 Python은 키워드를 검출(분석)에만 사용하고 프롬프트에 직접 주입하지 않음. 변경: 키워드 목록을 **LLM 프롬프트 예시**로 전환 — "참고할 수 있는 표현 예시이며, 캐릭터의 상황·관계·감정에 따라 자유롭게 변형하세요." 검출 기능 유지, 키워드 풀을 더 다양하게 확장. |

**대원칙 1 준수**: Python은 수집·포맷팅만. 어떤 표현을 쓸지는 LLM 판단.

#### QI-1-C2: EXCLAMATION_PATTERNS 동적화

**변경 대상**: `character_voice.py` L83-91

| 현재 | 변경 |
|------|------|
| `VoiceStyle.CRUDE: ["쳇","젠장","씨발","빌어먹을"]` → 무조건 이 감탄사 사용 | CRUDE 키워드를 **예시 풀**로 확장 + "상황에 따라 강도 조절" 지시. 진지한 장면에서는 "젠장" 수준, 극한 상황에서만 강한 표현. LLM이 맥락 판단. |

#### QI-1-C3: `intro_dna` 기본값 제거 → Bible/Treatment 참조

**변경 대상**: 4파일 7곳

| 파일 | 위치 | 현재 | 변경 |
|------|------|------|------|
| `chief_writer.py` | L170, L645, L943 | `intro_dna: str = "CYNICAL"` (3곳) | `intro_dna: str = ""` |
| `chief_writer_context.py` | L68, L1060 | `intro_dna: str = "CYNICAL"` (2곳) | `intro_dna: str = ""` |
| `stage4_orchestrator.py` | L686 | `intro_dna = "CYNICAL"` | Bible `protagonist_config.personality`에서 동적 로드. 없으면 빈 문자열. |
| `writer.py` | L66 | `intro_dna="CYNICAL"` | `intro_dna=""` |

**_get_dna_instruction() 수정** (L1060-1072): `intro_dna`가 빈 문자열이면 DNA 지시 블록 전체 생략(`return ""`) → CW가 Blueprint/Treatment 기반으로 자유 서술. 현재 빈 문자열이어도 `[제1화 특수 DNA 적용]: ` 라인이 출력되므로 분기 추가 필수.

#### QI-1-C4: LoreManager 기본 톤 장르 동적화

**변경 대상**: `lore_manager.py` L126-137

| 현재 | 변경 |
|------|------|
| `tone = self.speech_style.get("tone", "격조 있는 무인")` (무협 하드코딩) | `tone = self.speech_style.get("tone", "")` (빈 문자열 기본값). 빈 톤이면 페르소나 가이드에서 톤 라인 생략 → LLM이 캐릭터 속성에서 자체 판단. |

---

### P2 유보 항목 (4건)

| # | 항목 | 사유 |
|---|------|------|
| T-4 | `emotion_keywords` 5→15 확장 | 감정 감지 정확도 개선이나, 현 시스템에서 감정 감지가 advisory 수준이므로 ROI 낮음 |
| T-5 | `StyleGuide.tone` 5→자유 입력 | Stage 0 전체 리팩토링 필요. 현재 enum 기반 분기 다수 |
| T-6 | `ENSEMBLE_STRATEGIES` 동적화 | CW 핵심 아키텍처 변경. 위험도 HIGH |
| T-7 | `VoiceStyle` enum 확장 | 사용처 다수. 호환성 검토 필요 |

---

## 3. 적용 전략

```
Phase 1 (LOW risk):   QI-1-A1 + QI-1-A4 + QI-1-A5 + QI-1-A6
                      ← 프롬프트 가이드 + WritingDirective 필드 + self-critique + Blueprint 전략
Phase 2 (MED risk):   QI-1-A2 + QI-1-A3
                      ← ending_hook 검증 완화 + PatternTracker 문구 추적
Phase 3 (MED risk):   QI-1-C1 + QI-1-C2 + QI-1-C3 + QI-1-C4
                      ← 하드코딩 제거 4건 (P1)
Phase 4 (LOW risk):   QI-1-B1~B5
                      ← 투자물 클로닝 (레퍼런스 배치 + 장르 분기)
```

**Phase 1이 엔딩 반복 문제의 80% 해소 기대** — Blueprint 가이드 + 회피 목록 + 참신성 체크.
Phase 2는 근본 원인(리터럴 매칭) 수정. Phase 1 효과 확인 후.
Phase 3은 감성 하드코딩 제거. 독립 적용 가능.
Phase 4는 사용자 레퍼런스 원고 준비 후.

---

## 4. 영향받는 기존 시스템

| 시스템 | 영향 | 대응 |
|--------|------|------|
| TF-54 WritingDirective | `ending_avoid_phrases` 필드 추가 | PatternReport 연동 |
| Self-critique 체크리스트 | 12번째 체크 추가 | 기존 11개 체크 불변 |
| Blueprint 3전략 | ending_hook 유형 지시 추가 | 기존 전략 로직 불변 |
| `_check_ending_hook_presence` | 리터럴→키워드 매칭 전환 | severity high→medium |
| 대원칙 1 | Python 판단 제거 확인 | T-1~T-4 전부 "LLM 판단" 패턴으로 전환 |
| 대원칙 3 | Director 주권 불변 | 신규 체크는 advisory 수준 |
| Stage 0 StyleExtractor | 장르 분기 추가 | 기존 무협 로직 불변 |
| 1화 DNA 시스템 | CYNICAL 기본값 제거 | Bible 참조 폴백 |

---

## 5. 롤백 계획

- **Phase 1 롤백**: YAML 1곳 + .py 3곳 원복 (git revert)
- **Phase 2 롤백**: .py 2곳 원복
- **Phase 3 롤백**: .py 6파일 원복 (character_voice_profiler.py, character_voice.py, chief_writer.py, chief_writer_context.py, stage4_orchestrator.py, writer.py, lore_manager.py → 실제 7파일이나 git revert 1커밋)
- **Phase 4 롤백**: style_extractor.py 3곳 원복 + 레퍼런스 파일 제거

---

## 6. 검증 계획

1. 기존 테스트 3,614개 전량 PASS 확인
2. 실파이프라인 1회 → 엔딩 5화 연속 비교 (동일 구조 반복 여부)
3. 실파이프라인 1회 → 1화 주인공 톤 다양성 확인 (CYNICAL 기본값 제거 효과)
4. character_voice_profiler 단위 테스트 → 키워드 직접 주입 vs 예시 전환 검증
5. PatternTracker 단위 테스트 → recent_ending_texts 수집 검증

---

## 7. 감리 이력

| 차수 | 결과 | 지적 사항 | 대응 |
|------|------|-----------|------|
| 1차 | FAIL (3건) | ①T-3 stage4_orchestrator.py L515→L686 ②T-7 VoiceStyle 7→8개(MERCHANT 누락) ③C-1 "미배치"→실제 파일 존재(참조작품1 1편+JSON) | 전량 반영 |
| 2차 | FAIL (1건+W4) | ①self-critique 라인 범위 L209-275→L209-305 ②ending_hook 영어 키워드 누락 가능(W) ③PatternReport L72→L62(W) ④intro_dna CYNICAL 4파일 7곳(3파일→4파일 확장)(W) ⑤_score_sentence genre 미수신(W) | 전량 반영: 라인 범위 교정+regex에 영어 추가+PatternReport L62+intro_dna 7곳 명시+genre 파라미터 주의 |
| 3차 | **PASS** (W2) | ①Phase 3 롤백 파일 수 4→7(실제 고유 파일)(W-LOW) ②QI-1-C1 현재 상태 설명(검출 vs 주입) 교정(W-LOW) | W 반영: 롤백 7파일 명시+QI-1-C1 현행 동작 정확 기술 |
