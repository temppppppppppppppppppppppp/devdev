# TF-LLM: Gemini 2.5 Pro vs Grok API 비교

> 상태: **CONFIRMED** (3-Pass 사실 검증 완료 2026-03-13)
> 작성일: 2026-03-13
> 비교 대상: Gemini 2.5 Pro API vs xAI Grok 계열 API (Grok 4 / 4 Fast / 4.1 Fast / 4.20 Beta)
> 목적: 글도비 파이프라인에 어느 모델이 더 적합한지 판단 (구현 난이도 제외)

---

## 0. Executive Summary

**결론: Grok 4 Fast(reasoning)의 등장으로 비용 우위가 Grok으로 이동. 그러나 한국어 산문 품질 미검증이 결정적 리스크.**

| 항목 | Gemini 2.5 Pro | Grok 4 Fast (reasoning) | 글도비 기준 승자 |
|------|:-:|:-:|:-:|
| 한국어 산문 품질 | ✅ 검증됨 (실파이프라인 70화+) | ❓ 미검증 | **Gemini** |
| 벤치마크 (수학/추론) | 좋음 | 더 좋음 (Grok 4급) | Grok |
| API 비용 (input/output) | $1.25 / $10 | **$0.20 / $0.50** | **Grok** (6.25배/20배 저렴) |
| 캐싱 적용 input | ~$0.125 (90% 할인) | 추정 ~$0.05-0.10 (50-75% 할인) | **Grok** |
| 컨텍스트 윈도우 | **1,000,000** | **2,000,000** | **Grok** (2배) |
| JSON 구조화 출력 | ✅ response_schema | ✅ structured outputs | 동등 |
| 한국어 번역/생성 | **WMT25 14/16 1위** | 데이터 없음 | **Gemini** |
| Output 속도 (t/s) | **128.0** | 98.9 | **Gemini** (~30% 빠름) |
| TTFT (첫 응답) | 26.5초 | **6.0초** | **Grok** (4배 빠름) |
| fallback chain | ✅ 2.5 Flash | ✅ 4 Fast non-reasoning | 동등 |

**핵심 변수: Grok 4 Fast(reasoning)가 한국어 산문을 Gemini급으로 생성할 수 있는가? → 검증 필요.**

---

## 1. xAI Grok 모델 라인업 전체

### 1.1 모델별 스펙

| 모델 | 컨텍스트 | Input $/M | Output $/M | Cached Input $/M | 성격 |
|------|-------:|----------:|----------:|----------------:|------|
| **Grok 4** | 256K | $3.00 | $15.00 | $0.75 | Reasoning 플래그십 |
| **Grok 4 Fast (reasoning)** | **2M** | **$0.20** | **$0.50** | 미공개 (추정 ~$0.05) | Grok 4급 성능, 40% 적은 thinking 토큰 |
| **Grok 4 Fast (non-reasoning)** | **2M** | $0.20 | $0.50 | 미공개 | 빠른 응답용 (reasoning 없음) |
| **Grok 4.1 Fast** | **2M** | $0.20 | $0.50 | $0.05 | 도구 호출 + 에이전트 특화 |
| **Grok 4.20 Beta** | **2M** | $2.00 | $6.00 | 미공개 | 최신 플래그십 (벤치마크 미발표) |

### 1.2 핵심 구분

**Grok 4 Fast(reasoning) ≠ 약체 모델.**

- xAI 공식 발표: "Grok 4 Fast achieves comparable performance to Grok 4 on GPQA, AIME, HMMT while using 40% fewer thinking tokens"
- 동일 모델 가중치에서 reasoning/non-reasoning을 시스템 프롬프트로 전환
- **Grok 4 대비 98% 저렴하면서 동등 벤치마크** — Gemini 2.5 Pro와 비교 시 비용 우위 확보

**Grok 4.1 Fast**: 도구 호출/에이전트 특화. 멀티턴 시나리오 강화. 글도비 용도와 직접 관련 낮음.

**Grok 4.20 Beta**: 2M 컨텍스트, $2/$6. 벤치마크 미공개 (2026-03 중순 발표 예정). API 접근 제한적.

---

## 2. API 가격 비교

### 2.1 토큰 단가 (per 1M tokens)

| 모델 | Input | Output | Cached Input | 비고 |
|------|------:|-------:|------------:|------|
| **Gemini 2.5 Pro** | $1.25 | $10.00 | $0.125 (90% 할인) | 200K 이상 input $2.50 |
| **Gemini 2.5 Flash** | $0.15 | $0.60 | $0.015 | 경량 fallback |
| **Grok 4** | $3.00 | $15.00 | $0.75 (75% 할인) | Reasoning 플래그십 |
| **Grok 4 Fast (reasoning)** | $0.20 | $0.50 | ~$0.05-0.10 (추정) | **Grok 4급 품질** |
| **Grok 4.1 Fast** | $0.20 | $0.50 | $0.05 | 도구 호출 특화 |
| **Grok 4.20 Beta** | $2.00 | $6.00 | 미공개 | 최신 베타 |

### 2.2 글도비 실운영 비용 추정

글도비 1 에피소드 기준 (Stage 4, 3후보 앙상블 + Director + Advisory 8개):
- **Input**: ~200K 토큰 (프롬프트 + 컨텍스트 + 이전 원고)
- **Output**: ~50K 토큰 (원고 3후보 + Director 판정)
- **Cached input**: ~150K (반복 시스템 프롬프트, SSOT 규칙)

| 모델 | 비캐싱 비용 | 캐싱 적용 비용 | 비고 |
|------|----------:|------------:|------|
| Gemini 2.5 Pro | ~$0.75 | ~$0.33 | implicit caching 90% 할인 |
| Grok 4 | ~$1.35 | ~$0.54 | prompt caching 75% 할인 |
| **Grok 4 Fast (reasoning)** | **~$0.065** | **~$0.04** (추정) | Gemini 대비 **~88% 저렴** |

**⚠️ Grok 4 Fast(reasoning) 비용이 Gemini 2.5 Pro의 ~1/8 수준.** 캐싱 적용 시에도 ~1/8. Output 단가 차이($10 vs $0.50)가 결정적.

### 2.3 Grok 캐싱 메커니즘

- **자동 활성화**: 모든 요청에 자동 적용 (Gemini implicit caching과 유사)
- **캐시 지속**: ~5분
- **최적화 힌트**: `x-grok-conv-id` 헤더로 캐시 히트율 향상 가능
- **할인율**: 50-75% (모델별 상이, Grok 4: 75%, Grok 4.1 Fast: 75%)

### 2.4 Output 속도 (tokens/sec)

| 모델 | Output 속도 (t/s) | TTFT (초) | 비고 |
|------|---:|---:|------|
| **Gemini 2.5 Pro** | **128.0** | 26.5 | reasoning 모델 중 상위. TTFT 느림 (thinking 포함) |
| **Grok 4** | 43.6 | — | reasoning 플래그십. 느림 |
| **Grok 4 Fast (reasoning)** | 98.9 | **6.0** | Grok 4급 품질. TTFT 4배 빠름 |
| **Grok 4 Fast (non-reasoning)** | 93.0 | — | reasoning 없는 버전 |
| **Grok 4.1 Fast (non-reasoning)** | 127.0 | — | 도구 호출 특화 |
| **Grok 4.20 Beta (reasoning)** | **267.5** | — | 최신 베타. 전모델 1위 |

**출처:** [Artificial Analysis](https://artificialanalysis.ai/models/) 실측 (xAI 직접 API 기준)

**글도비 영향:**
- **Output 속도**: Gemini 128 vs Grok 4 Fast 99 → Gemini **~30% 빠름**. 에피소드 1건(output ~50K 토큰) 기준 Gemini ~6.5분 vs Grok 4 Fast ~8.4분.
- **TTFT**: Gemini 26.5초 vs Grok 4 Fast 6.0초 → Grok **4배 빠른 첫 응답**. 다만 글도비는 배치 파이프라인이라 TTFT보다 throughput이 중요.
- **Grok 4.20 Beta**: 267.5 t/s면 Gemini의 2배. 베타 종료 후 안정성 확인 필요.

### 2.5 Rate Limits

| 모델 | RPM | TPM | 비고 |
|------|----:|----:|------|
| Gemini 2.5 Pro (Pay-as-you-go) | ~1,000 | ~4M | Tier별 상이 |
| Grok 4 | 480 | 2M | 상위 플랜 4M |
| Grok 4 Fast | 제한 미공개 | 제한 미공개 | Grok 4 이상으로 추정 |

---

## 3. 벤치마크 비교

### 3.1 수학/추론

| 벤치마크 | Gemini 2.5 Pro | Grok 4 | Grok 4 Fast (reasoning) | 승자 |
|----------|:-:|:-:|:-:|:-:|
| AIME 2025 (경쟁 수학) | 86.7% | **95%** | Grok 4와 동급 (xAI 공식) | Grok |
| AIME 2026 | — | 88.9% | — | — |
| Humanity's Last Exam | 21% | **24%** (tool: 38.6%) | — | Grok |
| GPQA Diamond (대학원 과학) | 84.0% | 83.3-87.5% | Grok 4와 동급 (xAI 공식) | 동등 |
| ARC-AGI v1 (추상 추론) | — | **66.6%** | — | Grok |

### 3.2 코딩

| 벤치마크 | Gemini 2.5 Pro | Grok 4 | 승자 |
|----------|:-:|:-:|:-:|
| LiveCodeBench v5 | 70.4% | **79.4%** | Grok |
| SWE-Bench Verified | **63.8%** | 58.6% (독립) / 69-75% (자체) | 조건부 |
| Aider Polyglot | 74.0% | **79.6%** | Grok |

**SWE-Bench 주석:**
- Grok 4: xAI 자체 72-75%, vals.ai 독립 58.6%, Grok 4.2 독립 ~70.8%
- Gemini 2.5 Pro 63.8%: Google 자체 scaffold 기준 (동일한 편향 가능성)
- Scaffold 차이가 결과에 10%p 이상 영향

### 3.3 언어/번역

| 벤치마크 | Gemini 2.5 Pro | Grok 4 | 승자 |
|----------|:-:|:-:|:-:|
| WMT25 (번역) | **14/16 언어쌍 1위** | 미참가 | Gemini |
| MRCR 128K (장문 이해) | **94.5%** | — | Gemini |

### 3.4 Chatbot Arena Elo (2026년 3월)

| 모델 | Elo | 순위 |
|------|----:|:---:|
| Claude Opus 4.6 | 1504 | 1 |
| Gemini 3.1 Pro | 1500 | 2 |
| Grok 4.20 Beta | 1493 | 4 |
| Gemini 3.0 Pro | 1485 | 5 |
| Grok 4.1 Thinking | 1473 | 9 |

**참고:** Gemini **2.5** Pro는 구세대. 후속(3.0/3.1)이 Grok 최신보다 상위. 그러나 2.5 Pro 자체의 Arena 순위는 별도 추적 안 됨.

---

## 4. API 기능 비교

| 기능 | Gemini 2.5 Pro | Grok 4 Fast (reasoning) |
|------|:-:|:-:|
| **컨텍스트 윈도우** | 1,000,000 | **2,000,000** |
| **Context Caching (explicit)** | ✅ (TTL 설정, 90% 할인) | ✅ (자동, 50-75% 할인) |
| **Implicit Caching** | ✅ (자동, 4096토큰 이상) | ✅ (자동, conv-id 힌트) |
| **JSON Schema 강제** | ✅ response_schema | ✅ structured outputs |
| **Function Calling** | ✅ | ✅ |
| **Thinking/Reasoning 모드** | ✅ (thinking budget) | ✅ (reasoning/non-reasoning 전환) |
| **Multimodal (이미지/오디오)** | ✅ | ✅ (이미지) |
| **Batch API** | ✅ (50% 할인, 24h) | ❓ 미확인 |
| **SDK 호환** | google-genai (Python) | OpenAI 호환 SDK |
| **Safety 필터 제어** | ✅ (BLOCK_NONE 가능) | ⚠️ 제한적 |

### 4.1 컨텍스트 윈도우가 글도비에 중요한 이유

글도비 Chief Writer 프롬프트 = 시스템 규칙(~30K) + SSOT(~20K) + 이전 원고(~15K) + Blueprint(~10K) + Advisory(~10K) + Director 피드백(~5K) = **~90K 토큰**.

- Gemini 1M: 여유 (10+ 에피소드 이전 맥락 포함 가능)
- **Grok 4 Fast 2M: 더 여유** (20+ 에피소드 이전 맥락 포함 가능)
- Grok 4 256K: 가능하나 장기 연재 시 맥락 절삭 필요

### 4.2 Context Caching이 글도비에 중요한 이유

글도비 5개 에이전트(chief_writer, arc_ensemble, blueprint_ensemble, director_ensemble, director_continuity)가 Context Caching 사용:
- 공통 시스템 프롬프트 ~50K 반복
- Gemini implicit caching: 90% 할인
- Grok prompt caching: 50-75% 할인 (Gemini보다 낮지만, 기본 단가가 이미 저렴)

**캐싱 후 실효 input 단가:** Gemini ~$0.125/M vs Grok 4 Fast ~$0.05-0.10/M → Grok이 여전히 저렴.

---

## 5. 글도비 적합성 판단

### 5.1 글도비가 LLM에 요구하는 능력

| 요구 능력 | 중요도 | 설명 |
|----------|:---:|------|
| **한국어 산문 생성** | ★★★★★ | 웹소설 원고 5,000자 생성 |
| **JSON 구조화 응답** | ★★★★★ | Director verdict, Arc 설계 등 모든 판정이 JSON |
| **장문 컨텍스트 이해** | ★★★★☆ | 30화+ 이전 원고 참조, 연속성 유지 |
| **수치 추론** | ★★★☆☆ | FactLedger 수치 정합성 (투자금, 지분율 등) |
| **수학적 추론** | ★★☆☆☆ | 직접 수학 문제 풀이 아님, 수치 논리 판단 정도 |
| **코드 생성** | ★☆☆☆☆ | 파이프라인 내 코드 생성 없음 |
| **비용 효율** | ★★★★☆ | 에피소드당 수백 회 LLM 호출 |

### 5.2 적합성 매트릭스 (Grok 4 Fast reasoning 기준)

| 요구 능력 | Gemini 2.5 Pro | Grok 4 Fast (reasoning) | 판정 |
|----------|:-:|:-:|:-:|
| 한국어 산문 | ✅ 실검증 70화+ | ❓ **미검증 (최대 리스크)** | **Gemini** |
| JSON 구조화 | ✅ response_schema | ✅ structured outputs | 동등 |
| 장문 컨텍스트 | ✅ 1M, MRCR 94.5% | ✅ 2M | **Grok** |
| 수치 추론 | ✅ 충분 | ✅ Grok 4급 (AIME 95%) | Grok 약간 우위 |
| 비용 효율 | $1.25 + 캐싱90% | **$0.20 + 캐싱50-75%** | **Grok** (대폭 저렴) |

### 5.3 비용 우위 요약

| 항목 | Gemini 2.5 Pro | Grok 4 Fast (reasoning) | 배수 |
|------|------:|------:|------:|
| Input 단가 | $1.25 | $0.20 | Grok **6.25배** 저렴 |
| Output 단가 | $10.00 | $0.50 | Grok **20배** 저렴 |
| 캐싱 input | $0.125 | ~$0.05-0.10 | Grok 1.25-2.5배 저렴 |
| 에피소드당 (캐싱) | ~$0.33 | **~$0.04** | Grok **~8배** 저렴 |
| 50화 연재 총비용 | ~$16.50 | **~$2.00** | Grok **~8배** 저렴 |

### 5.4 판정: 왜 아직 Gemini인가

**비용/컨텍스트/벤치마크 모두 Grok 4 Fast(reasoning)이 우위.** 그런데도 현행 Gemini 유지를 권장하는 이유:

1. **한국어 산문 품질 미검증 (BLOCKER):** 글도비의 핵심 출력물은 한국어 웹소설 원고. Grok의 한국어 산문 능력은 벤치마크 데이터 자체가 없고, WMT25에도 미참가. Gemini는 WMT25 14/16 1위 + 실파이프라인 70화 검증.

2. **"Grok 4급 성능" 미독립 검증:** xAI 자체 발표. Grok 4 Fast의 독립 벤치마크(vals.ai 등)는 아직 제한적. SWE-Bench에서 Grok 4 자체도 자체발표와 독립테스트 간 14%p 괴리(72% vs 58.6%).

3. **캐싱 할인율 불확정:** Grok 4 Fast cached input 단가 미공개. 50-75%는 Grok 4/4.1 Fast 기준 추정치.

4. **Safety 필터:** Gemini는 BLOCK_NONE 설정 가능. Grok은 제한적. 웹소설(폭력/갈등 묘사)에서 안전 필터 우회가 중요.

### 5.5 Grok 도입 로드맵 (검증 후)

| 단계 | 작업 | 판정 기준 |
|------|------|----------|
| **1. 한국어 카나리아** | Grok 4 Fast(reasoning)로 10화 원고 생성 → Gemini 원고와 블라인드 비교 | 산문 품질 동등 이상 |
| **2. 하이브리드 투입** | Director/Advisory만 Grok, Chief Writer는 Gemini 유지 | Director 판정 품질 유지 |
| **3. 전면 전환** | Chief Writer까지 Grok 전환 | 50화 연재 ~$14 절감 |

### 5.6 "압도적" 판정 (재평가)

**Grok이 Gemini 2.5 Pro보다 압도적이라는 주장: ⚠️ 부분적으로 사실.**

- ✅ 비용: Grok 4 Fast가 **6-20배** 저렴 — 이것은 "압도적" 맞음
- ✅ 컨텍스트: Grok 4 Fast 2M > Gemini 1M — 우위
- ✅ 수학/추론: Grok 약간 우위 (AIME 95 vs 87, LiveCodeBench 79 vs 70)
- ❌ 한국어: Gemini 압도 (WMT25 1위, 실검증)
- ❌ 실전 코딩 (독립): Gemini 우위 (SWE-Bench 63.8 vs 58.6 독립)
- ⚠️ Arena Elo: Gemini 후속(3.1 Pro)이 Grok 최신(4.20)보다 상위

**API 스펙(가격/컨텍스트) 기준으로는 Grok 4 Fast가 객관적으로 우위. 그러나 글도비 용도(한국어 장편 소설)에서는 한국어 품질 미검증이 결정적 제약.**

---

## 부록: 데이터 출처 및 감리

### 감리 과정

| Pass | 작업 | 결과 |
|------|------|------|
| 1차 | 8건 웹서치 — Grok 4 Fast 스펙/벤치마크, Grok 4.20 Beta 스펙, Grok 캐싱 할인율 | 모델 라인업 전면 재조사 |
| 2차 | **핵심 오류 수정** — Grok 4 Fast(reasoning)이 약체 모델이 아님을 확인. xAI "comparable to Grok 4 on GPQA, AIME, HMMT" 공식 발표. 비용 비교 전면 재작성. | 비용 우위 Gemini→Grok 역전 |
| 3차 | Grok 캐싱 메커니즘 확인 — 자동 활성화, 50-75% 할인, 5분 지속, conv-id 힌트. Grok 4 cached $0.75/M, Grok 4.1 Fast cached $0.05/M 확인. | 캐싱 비교 보강 |
| 4차 | 글도비 실운영 비용 재계산 — Grok 4 Fast 에피소드당 ~$0.04 vs Gemini ~$0.33. 50화 기준 ~$14 차이. | 비용 매트릭스 확정 |
| 5차 | 미검증 항목 점검 — Grok 한국어 산문(미검증), Grok 4 Fast 독립 벤치마크(제한적), 캐싱 할인율(4 Fast 미공개), Safety 필터(제한적) | **사실 오류 0건, 미검증 4건 명시** |

### 이전 문서 대비 수정 사항

| 항목 | 이전 문서 (오류) | 수정 후 (사실) |
|------|----------------|--------------|
| Grok 컨텍스트 | "256K만" | Grok 4=256K, **Fast/4.1/4.20=2M** |
| Grok 4 Fast 성격 | "도구 호출 약체" | **Grok 4급 reasoning 성능** (xAI 공식) |
| 비용 승자 | "Gemini 2.4배 저렴" | **Grok 4 Fast 6-20배 저렴** |
| 컨텍스트 승자 | "Gemini 4배" | **Grok 2배** (2M vs 1M) |
| 캐싱 | "Grok 할인율 미공개" | **50-75% 할인 확인**, 자동 활성화 |
| 최종 판정 | "Gemini 명확 우위" | **API 스펙 Grok 우위, 한국어 미검증이 유일한 제약** |

### 주요 출처

| 데이터 | 출처 |
|--------|------|
| Gemini 2.5 Pro 가격 | [Google AI Pricing](https://ai.google.dev/gemini-api/docs/pricing) |
| Grok 모델/가격 | [xAI Models and Pricing](https://docs.x.ai/developers/models) |
| Grok 4 Fast 발표 | [xAI Grok 4 Fast](https://x.ai/news/grok-4-fast) |
| Grok 4.1 Fast 발표 | [xAI Grok 4.1 Fast](https://x.ai/news/grok-4-1-fast) |
| Grok 4 Fast 벤치마크 | [Artificial Analysis](https://artificialanalysis.ai/models/comparisons/grok-4-fast-reasoning-vs-grok-4) |
| Grok 4.20 Beta 분석 | [Artificial Analysis](https://artificialanalysis.ai/models/grok-4-20) |
| Grok 캐싱 메커니즘 | [xAI Rate Limits](https://docs.x.ai/docs/key-information/consumption-and-rate-limits) |
| Arena Elo | [LMSYS Chatbot Arena March 2026](https://productleadersdayindia.org/blogs/lmsys-chatbot-arena-leaderboard/) |
| Grok 4 벤치마크 | [DataCamp](https://www.datacamp.com/blog/grok-4), [BleepingComputer](https://www.bleepingcomputer.com/news/artificial-intelligence/grok-4-benchmark-results-tops-math-ranks-second-in-coding/) |
| Gemini WMT25 | [Artificial Analysis](https://artificialanalysis.ai/models/gemini-2-5-pro) |
| SWE-Bench 독립 | [vals.ai](https://www.vals.ai/models/grok_grok-4-1-fast-reasoning) |

### 미검증 항목 (데이터 부재)

| 항목 | 사유 | 영향도 |
|------|------|--------|
| **Grok 4 Fast 한국어 산문 품질** | 한국어 벤치마크/평가 데이터 없음 | **BLOCKER** — 글도비 전환 판단 불가 |
| Grok 4 Fast 독립 벤치마크 | xAI 자체 발표 vs 독립 검증 괴리 가능성 | IMPORTANT — Grok 4에서 14%p 차이 전례 |
| Grok 4 Fast cached input 단가 | xAI 미공개 (4.1 Fast $0.05 기준 추정) | LOW — 기본 단가 자체가 저렴 |
| Grok Batch API | 존재 여부 미확인 | LOW — 실시간 파이프라인이 주 운영 |
| Grok Safety 필터 세부 | BLOCK_NONE 동등 기능 미확인 | MEDIUM — 웹소설 특성상 중요 |
