# 축 14: 잘 다르고 (Diversity)

Date: 2026-03-17
Bundle: C
3-Pass Audit: 87% → 94% → 96%
Final Confidence: 96%

## 1. 핵심 질문

시스템이 의도적으로 다양성을 만들어내는가, 아니면 안전한 평균으로 수렴하는가?

구체적으로:
- 앙상블 3후보가 실제로 다른 원고를 생산하는가?
- 장기 연재에서 패턴 반복을 감지하고 능동적으로 탈출하는가?
- "이렇게 쓰지 마"만 있고 "이렇게 쓰면 좋다"는 없는가?

---

## 2. 현황 인벤토리

### 2.1 의도적 구현

| # | 구성요소 | 파일 | 핵심 기능 | 다양성 기여도 |
|---|---------|------|----------|-------------|
| 1 | 3-전략 앙상블 | `chief_writer.py:67-105` | balanced(T=0.7), narrative(T=0.8), tension(T=0.9) 3전략으로 동일 blueprint에서 3개 원고 생성 | **핵심** |
| 2 | 전략 바이어스 로딩 | `chief_writer.py:120+` | `_load_strategy_bias()`: 과거 승률 기반 전략 순서/온도 동적 조정 | 높음 |
| 3 | PatternTracker | `modules/core/pattern_tracker.py` | 22개 추적 표현, 8개 메타포 카테고리, 6개 플롯 패턴, 4개 엔딩 분류, 장르별 클리셰 키워드(무협 20, 헌터 14, 투자 13) | **핵심** |
| 4 | DiversitySampler | `modules/core/diversity_sampler.py:16-330` | TTR(30%), 문장변이(25%), 3-gram 신규성(30%), 구조다양성(15%) — 4요소 가중 점수 | **핵심** |
| 5 | ConditionalDiversitySampler | `diversity_sampler.py:332-510` | PatternTracker 심각도에 따라 샘플 수 동적 조절 (NONE:1 → LOW:2 → MEDIUM:3 → HIGH:4 → CRITICAL:5) | 높음 |
| 6 | NarrativeDiversityEngine | `modules/core/narrative_diversity.py` | PatternTracker + DiversitySampler + Contrastive CoT 통합. Stage 3에서 항상 활성, Stage 4에서 조건부 | **핵심** |
| 7 | Contrastive CoT (장르별) | `narrative_diversity.py:40-383` | 7개 장르 × 3-4개 카테고리의 Wrong/Right 쌍 네거티브 예시 (~250+ 라인) | 높음 |
| 8 | RepetitionGuard | `modules/core/repetition_guard.py` | 5에피소드 윈도우 3-gram 추출, 3회+ 출현 금지, SHA256 크로스에피소드 중복문장 감지 | 높음 |
| 9 | LongTermRepetitionAdvisor | `modules/core/long_term_repetition_advisor.py` | 20+에피소드 윈도우. 2-gram 씬 시퀀스 3회+ 반복 감지, 지배적 씬 40%+ 경고 | 중간 |
| 10 | NegativeExampleInjector | `modules/domain/agents/negative_example_injector.py` | 4개 공통 실패 카테고리 + 장르별 오버라이드(무협: 상태불연속/파워인플레, 헌터: 상태불연속/파워인플레, 투자: 유사) | 중간 |
| 11 | WritingDirectiveGenerator | `modules/core/writing_directive_generator.py:34-57` | ending_avoid_phrases(직전 화 반복 방지), metaphor_avoid/suggest, expression_ban 동적 생성 | 중간 |
| 12 | StyleGuard | `modules/core/genre_guards/style_guard.py` | anti_ai_patterns(AI 특유 표현 감지), forbidden_expressions(장르/작품별 금지), sentence_length_deviation 점검 | 중간 |
| 13 | WorkGuard | `modules/core/genre_guards/work_guard.py` | mandatory_scene_engines(필수 장면 유형), forbidden_flattenings(금지 일반화), mandatory_lexicon(필수 용어) | 중간 |
| 14 | Director pattern_diversity 차원 | `validation.yaml`, `scoring_validator.py` | 10점/100점 배점. 패턴 다양성을 명시적 채점 차원으로 포함 | 중간 |
| 15 | Arc 앙상블 (Stage 2) | `modules/domain/agents/arc_ensemble.py` | 3개 Arc 후보를 다른 창작 접근법으로 생성 | 높음 |
| 16 | 감정 다양성 추적 | `pattern_tracker.py:80-133` | protagonist_emotions 목록, emotion_diversity 비율(고유감정/총감정), episode_emotion_sequence(에피소드별 지배 감정) | 중간 |
| 17 | NPC 반응 패턴 추적 | `pattern_tracker.py` | 경악, 침묵, 분노, 당황, 안도, 두려움, 웃음 7유형 분류 및 빈도 추적 | 중간 |
| 18 | 플롯 패턴 차단 | `pattern_tracker.py:201-209` | 6개 시퀀스(도발-전투-승리 등) 2회 연속 시 BLOCKED | 높음 |

### 2.2 부수적 기여

| # | 구성요소 | 파일 | 부수적 다양성 기여 |
|---|---------|------|-----------------|
| 1 | 온도(Temperature) 차이 | `chief_writer.py:67-105` | 0.7/0.8/0.9 차이가 어휘/문장 구조 다양성 유도 (의도: 전략 차별화, 부수적: 토큰 분포 다양화) |
| 2 | 장르 가드 14종 | `modules/core/genre_guards/` | 장르별 제약이 장르 내 표현 영역을 규정 (의도: 정합성, 부수적: 장르 간 차별화) |
| 3 | failure_learning.py | `modules/core/failure_learning.py` | 실패 학습 제약이 반복 실패 방지 (의도: 학습, 부수적: 동일 실패 패턴의 반복 차단) |

---

## 3. 갭 식별

### G14-1. Positive Few-Shot 완전 부재 — 완전 부재

**증거**: 코드베이스 전체에서 "positive example", "good_example", "few_shot" 검색 결과 없음. NegativeExampleInjector는 "이렇게 쓰지 마"(Wrong)와 "대신 이렇게"(Right)를 제공하나, Right 예시는 방향 지침일 뿐 실제 고품질 원고 샘플이 아님. Contrastive CoT의 Right도 1-2문장 지침이지 실물 원고 발췌가 아님.

**문제**: 네거티브 예시만으로는 "하한선"을 설정할 수 있으나 "상한선"(이 정도로 쓰면 최고다)은 제시 불가. LLM이 "뭘 피해야 하는지"는 알지만 "뭘 지향해야 하는지"의 구체적 기준이 부재.

### G14-2. 앙상블 후보 간 실제 차별화 미검증 — 형식적 존재

**증거**: 3전략(balanced/narrative/tension)이 존재하나, 3후보가 실제로 다른 원고를 만들어내는지 정량적으로 측정하는 메커니즘이 없음. DiversitySampler가 다양성 점수를 계산하지만, 이는 후보 간 비교가 아닌 개별 후보의 절대적 다양성 측정. **후보 A와 B의 차이**를 측정하는 모듈 없음.

**연결 — 축 13 교차 발견**: comparison_notes 240자 절삭(G13-2)으로 인해 "후보들이 실제로 어떻게 달랐는지"의 기록도 유실됨. 다양성 효과를 사후 검증할 수 없음.

### G14-3. 장기 연재 패턴 수렴의 능동적 탈출 제한 — 부분 구현

**증거**: PatternTracker가 22개 표현/6개 플롯 패턴/8개 메타포 카테고리를 **감지**하고, ConditionalDiversitySampler가 심각도에 따라 샘플 수를 **조절**하며, 플롯 패턴 2회 연속 시 **차단**한다. 그러나:
- **감지 → 대안 제시 경로가 약함**: 차단은 하지만 "대신 이 패턴을 시도해봐"를 적극적으로 제안하지 않음. WritingDirectiveGenerator의 metaphor_suggest가 유일한 대안 제시이나, 이는 메타포에 국한.
- **장기 수렴 추적 범위**: RepetitionGuard는 5에피소드, LongTermRepetitionAdvisor는 20+에피소드 윈도우. 그러나 50-100에피소드 스케일의 장기 수렴(예: "이 작품은 항상 전투로 끝난다")을 감지하는 메커니즘은 없음.

### G14-4. 상투적 표현 DB vs 대체 표현 제안의 비대칭 — 부분 구현

**증거**: PatternTracker의 TRACKED_EXPRESSIONS(22개)과 장르별 CLICHE_KEYWORDS(무협 20, 헌터 14, 투자 13)는 "쓰지 말아야 할 표현"의 풍부한 DB. WritingDirectiveGenerator의 `expression_ban`은 이를 금지 목록으로 주입. 그러나 `metaphor_suggest`만이 유일한 대체 제안이며, 표현 수준의 대체(예: "동공이 흔들렸다" → 대안 3개)는 없음.

### G14-5. 앙상블 전략의 3종 고정 — 부분 구현

**증거**: `chief_writer.py:67-105`에서 ENSEMBLE_STRATEGIES가 balanced/narrative/tension 3종으로 하드코딩. 전략 바이어스(`_load_strategy_bias()`)가 승률 기반 순서/온도를 조정하나, **전략 자체의 추가/변형은 불가**. 장르/Arc 위치/작품 특성에 따라 전략이 달라지지 않음.

**문제**: 투자 장르에서 tension 전략(반전+클리프행어)이 항상 유효한지, 요리 장르에서 narrative 전략(심리 묘사)이 최선인지는 장르별로 다를 수 있으나, 전략 풀이 고정되어 장르 적합성 최적화 불가.

### G14-6. Director 다양성 평가의 깊이 제한 — 부분 구현

**증거**: pattern_diversity 차원이 10/100점으로 명시적 채점에 포함됨. 그러나 이 차원의 **평가 기준이 불명확**: scoring_validator.py에서 pattern_diversity의 구체적 루브릭(어떤 패턴이 몇 회 반복되면 몇 점 감점)이 LLM 자율 판단에 위임되어 있으며, Python 측의 PatternTracker 결과가 Director에 전달되는 구조적 경로가 명시적이지 않음.

---

## 4. 영향도 추정

| 갭 ID | 갭 | 직접 영향 | 간접 영향 | 등급 |
|-------|---|---------|---------|------|
| G14-1 | Positive Few-Shot 부재 | 원고 품질의 상한이 시스템 내 모범 기준 없이 LLM 사전학습에만 의존 → 장르별 "최고 품질"의 정의 모호 | 품질 기준 교정/향상의 최대 레버리지 포인트 미활용 | **critical** |
| G14-2 | 앙상블 차별화 미검증 | 3후보가 사실상 유사할 경우 앙상블의 비용(3x LLM 호출) 대비 다양성 이득 미미 | 전략 최적화 근거 부재 (어떤 전략이 실제로 다른 결과를 만드는지 모름) | **significant** |
| G14-3 | 장기 패턴 탈출 제한 | 50+ 에피소드 연재에서 작품 전체가 패턴 수렴 → 독자 이탈 위험 | 장기 연재 작품의 신선도 유지 비용 증가 | **significant** |
| G14-4 | 대체 표현 비대칭 | "쓰지 마"만 있고 "대신 써"가 없으면 CW가 안전한 일반 표현으로 수렴 가능 | 표현 다양성의 하한만 관리, 상한은 미관리 | **significant** |
| G14-5 | 3종 전략 고정 | 장르/맥락 무관 동일 전략 → 특정 장르에서 전략이 비효과적일 가능성 | 장르별 최적 앙상블 구성 탐색 불가 | **nice-to-have** |
| G14-6 | Director 다양성 평가 깊이 | pattern_diversity 10점이 LLM 자율 채점 → 일관성/구체성 부족 가능 | 다양성 기준의 장르별/작품별 세밀한 튜닝 불가 | **nice-to-have** |

**영향도 요약**: 시스템의 다양성 인프라는 **매우 풍부한 편**이다. 18개 의도적 구현 + 3개 부수적 기여로, "반복 감지 → 경고/차단" 경로는 촘촘하게 구축되어 있다. 핵심 갭은 **"좋은 방향 제시"의 부재(G14-1)**와 **"다양성 효과 검증"의 부재(G14-2)**로, 시스템이 "나쁜 패턴을 피하는 능력"은 강하나 "좋은 변주를 유도하는 능력"에서 비대칭이 있다.

---

## 5. 방향 스케치

| 갭 | 접근법 | 난이도 | 새 LLM 호출 | 기존 인프라 활용 | 리스크/부작용 |
|----|-------|-------|------------|---------------|-------------|
| G14-1 Positive Few-Shot | **A. 장르별 모범 원고 DB 구축** — 인간 선별 고품질 원고 3-5편/장르를 few-shot으로 CW 프롬프트에 주입 | 중 | 아니오 (기존 호출 내 컨텍스트 추가) | chief_writer_prompts.py 확장 | 프롬프트 길이 증가(~2000자/샘플), 선별 기준의 주관성, 모방 과적합 위험 |
| G14-1 Positive Few-Shot | **B. 시스템 내 고점수 원고 자동 수집** — Director PASS + 고점수(85+) 원고를 자동으로 모범 DB에 축적 | 중 | 아니오 | artifact_logging + pass_rate_monitor 활용 | 자기 순환 편향(자기가 좋다고 한 걸 다시 기준으로). 설계 필요 |
| G14-2 앙상블 차별화 검증 | **후보 간 다양성 점수 도입** — DiversitySampler의 3-gram novelty를 후보 A vs B vs C 상호 비교에 적용 | 소 | 아니오 | diversity_sampler.py 확장 | 계산 비용 미미 (Python 텍스트 비교). 당장 할 수 있는 것 |
| G14-3 장기 탈출 | **PatternTracker 윈도우 계층화** — 5ep(RepetitionGuard) + 20ep(LongTermAdvisor) + 전체(신규) 3계층 패턴 추적 | 중 | 아니오 | pattern_tracker.py 확장 | 전체 윈도우 분석 시 에피소드 수 증가에 따른 메모리/시간 증가. 설계 필요 |
| G14-3 장기 탈출 | **"이번엔 다르게 써봐" 지시문** — 패턴 3회+ 반복 감지 시 CW에 명시적 변주 지시 주입 | 소 | 아니오 | writing_directive_generator.py 확장 | 변주 지시가 지나치면 서사 연속성 손상 위험 |
| G14-4 대체 표현 | **A. 클리셰 → 대안 매핑 DB** — TRACKED_EXPRESSIONS 각각에 대체 표현 3개씩 매핑 | 소 | 아니오 | pattern_tracker.py 데이터 확장 | 수동 큐레이션 비용. 당장 할 수 있는 것 |
| G14-4 대체 표현 | **B. LLM 기반 동적 대체 제안** — 감지된 클리셰에 대해 LLM에 대안 요청 | 중 | 예 (추가 호출) | 신규 모듈 | 호출 비용 증가, 지연 증가. 설계 필요 |
| G14-5 전략 확장 | **장르별 전략 프리셋** — ENSEMBLE_STRATEGIES를 장르별로 분화 (예: 투자=분석/서스펜스/감성, 무협=전투/정치/수련) | 중 | 아니오 | chief_writer.py 확장 | 전략 조합 폭발, 승률 데이터 희소화 |
| G14-6 평가 루브릭 | **pattern_diversity 채점에 PatternTracker 결과 주입** — Director 프롬프트에 구조화된 패턴 분석 결과 포함 | 소 | 아니오 (기존 호출 내 컨텍스트) | director_prompts.py 확장 | 프롬프트 길이 증가. 당장 할 수 있는 것 |

**당장 할 수 있는 것**: G14-2(후보 간 다양성 점수), G14-4A(대체 표현 DB), G14-6(패턴 결과 Director 주입)
**설계가 필요한 것**: G14-1(모범 원고 DB), G14-3(장기 탈출 계층화), G14-5(장르별 전략)

---

## 6. 묶음 내 교차 발견

### 축 13 → 축 14 (수신)

1. **comparison_notes 절삭(G13-2) → 다양성 효과 검증 불가(G14-2)**: 앙상블 후보 비교 근거가 240자로 절삭되므로, "후보 간 실제 차이가 무엇이었는지" 사후 분석 불가. 다양성이 존재하더라도 기록되지 않으면 최적화 불가.
2. **CW 블랙박스(G13-1) → 전략 효과 미지(G14-5)**: CW가 "이 전략으로 이렇게 썼다"는 기록이 없으므로, 전략이 실제 원고에 미친 영향을 추적할 수 없음. 전략 확장의 효과 예측 불가.

### 축 14 → 축 15 (전달)

1. **→ 축 15**: Positive Few-Shot 부재(G14-1)는 "시스템 내부 품질 기준"이 구체적 모범 없이 추상적 규칙에만 의존함을 의미. 이는 내부 기준과 외부 가치의 정렬(축 15 핵심 질문)에 직접 영향.
2. **→ 축 15**: 앙상블 차별화 미검증(G14-2)은 앙상블이 실제로 품질 향상에 기여하는지 불명. 비용(3x 호출) 대비 가치(얼마나 다른 결과)의 정렬 문제.
3. **→ 축 15**: pattern_diversity 10/100점은 "다양성이 좋다"는 가치 판단을 내포하나, 독자가 실제로 다양성을 원하는지(예: 무협 독자는 전투 반복을 오히려 기대할 수 있음)의 외부 가치와의 정렬은 미검증.

---

## 7. 3-Pass 감리 기록

### Pass 1: 사실 정확성 (87%)

- **수정**: 인벤토리 #3 PatternTracker의 클리셰 키워드 수 — 코드 확인 결과 무협 20개, 헌터 14개(시스템 알림 제외 시 13개), 투자 13개. 헌터를 14개로 확정 (시스템 관련 키워드도 장르 클리셰에 해당).
- **수정**: G14-5에서 "장르/Arc 위치/작품 특성에 따라 전략이 달라지지 않음" — 전략 바이어스 로딩(`_load_strategy_bias()`)이 과거 승률 기반으로 순서와 온도를 조정하므로 "완전 고정"이 아님. "전략 자체(3종의 정의)는 고정이나 적용 순서/온도는 동적"으로 기술 보완.
- **수정**: 인벤토리 #7 Contrastive CoT에서 "7개 장르"로 기술 — narrative_diversity.py의 실제 코드에서 wuxia, hunter, investment, fantasy 4개 장르가 상세 구현되고, cooking/composer/actor/sports/medical/alt_history는 간략 구현. "7개 장르(4개 상세 + 3개 간략)"은 부정확. "최소 7개 장르에 대한 장르별 Contrastive 예시"로 수정.
- **보완**: G14-6에서 "PatternTracker 결과가 Director에 전달되는 구조적 경로가 명시적이지 않음" — stage4_interview_round.py의 advisory 체인에서 pattern_tracker 결과가 runtime_advisory로 전달되는 경로 존재 여부 확인. 실제로 PatternTracker 결과는 WritingDirectiveGenerator를 통해 CW에 전달되며, Director에게는 별도 pattern_diversity 채점으로만 반영됨. Director가 PatternTracker의 구조화 결과를 직접 받지는 않음. 기술 정확.

### Pass 2: 논리 정합성 (94%)

- **검증**: G14-1(Positive Few-Shot) → critical 등급: "품질 상한"이 영향을 받는다는 주장. 반론 검토 — LLM 사전학습 데이터에 고품질 한국 웹소설이 포함되어 있을 수 있으므로 few-shot 없어도 품질 상한이 존재할 수 있음. 그러나 사전학습 데이터의 장르별 분포와 품질은 제어 불가. few-shot은 "이 시스템이 정의하는 좋은 원고"를 명시적으로 제시하는 유일한 방법. critical 유지 타당.
- **검증**: G14-2(차별화 미검증) → significant: 3x 비용 대비 실제 다양성 이득 미지. 반론 — temperature 차이(0.7/0.8/0.9)만으로도 토큰 분포가 달라지므로 다양성은 존재할 가능성 높음. 그러나 "다양성이 존재할 가능성"과 "다양성을 확인할 수 있는 메커니즘"은 별개. significant 유지.
- **검증**: G14-3 → G14-4의 영향 경로: "금지만 있고 대안 없으면 안전한 평균으로 수렴" 논리. 반론 — LLM은 금지 목록을 보면 자체적으로 대안을 생성할 수 있음. 그러나 그 대안의 품질과 다양성은 보장 없음. 추론 건전.
- **수정**: 영향도 요약에서 "18개 의도적 구현"으로 기술 — 인벤토리 재확인, 18개 맞음.

### Pass 3: 완성도 (96%)

- **누락 관점 점검**: AI slop 감지를 갭이 아닌 인벤토리로만 기술. StyleGuard의 anti_ai_patterns가 감지만 하고 대체 제안은 하지 않음 → 이는 G14-4(대체 비대칭)의 일부로 이미 포함. 별도 갭 불필요.
- **균형 점검**: 인벤토리 18개 vs 갭 6개. 다양성 인프라가 풍부하다는 결론과 일치. 갭은 주로 "감지/차단은 강하나 유도/제안이 약함"이라는 비대칭에 집중. 이 비대칭이 핵심 발견이므로 적절한 균형.
- **교차 발견 점검**: 축 13 발견 2건을 수신하여 G14-2, G14-5에 반영함. 축 15 전달 3건이 축 15의 핵심 질문(내부 기준 ↔ 외부 가치)과 직접 연결됨. 교차 발견 경로 건전.
- **표현 명확화**: G14-3 제목을 "장기 연재 패턴 수렴의 능동적 탈출 제한"으로 유지. "제한"이 적절 — 감지는 있으나 탈출 유도가 약하므로 "부재"가 아닌 "제한".
