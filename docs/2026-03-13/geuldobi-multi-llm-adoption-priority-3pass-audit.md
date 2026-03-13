# 글도비 Multi-LLM 도입 우선순위 3PASS 감리

> 작성일: 2026-03-13
> 대상 문서: `docs/2026-03-13/geuldobi-multi-llm-adoption-priority-ssot.md`
> 상태: 감리 완료
> 확신도: **95%**

---

## 0. 감리 요약

본 감리는 2026-03-13 시점에서 글도비용 hosted API 모델 도입 우선순위를 검증하기 위한 3PASS 감리다.

최종 판정:

- `Gemini 2.5 Pro > Claude Sonnet 4.6 > GPT-5.1 > Grok 4.1 Fast Reasoning`
- 위 순서는 글도비 기준으로 방어 가능하다
- 전제는 `시스템 변경 비용 제외`
- 그리고 `4천 자 이상 한국어 장문을 안정적으로 쓸 수 있는 모델만 포함`

문서 자체 기준 retained `P0 / P1 / P2`는 없다.

남는 불확실성은 두 가지뿐이다.

- Anthropic / OpenAI / xAI는 아직 글도비 풀파이프라인에서 live A/B 실증이 없다
- xAI 가격 근거 정밀도는 다른 3사보다 약간 낮다
- Google `Gemini 3.1 Pro Preview`와 xAI `Grok 4.20 Beta`는 둘 다 최신 flagship 비교축에선 중요하지만, preview/beta 상태라 production ROI 본표에는 바로 편입하지 않았다

이 두 항목은 `즉시 프로덕션 전환` 확신도에는 영향을 주지만, `도입 우선순위` 자체를 뒤집을 정도는 아니다.

---

## 1. Pass 1: 소스 검증

### 1.1 외부 공식 소스 검증

확인한 공식 소스:

- Google 공식 모델 문서
- Google 공식 가격 문서
- Google 공식 changelog
- Google 공식 지원 언어 문서
- Anthropic 공식 모델 문서
- Anthropic 공식 가격 문서
- OpenAI 공식 모델 문서
- OpenAI 공식 GPT-4.1 / GPT-5 문서
- OpenAI 공식 가격 문서
- xAI 공식 모델 문서
- xAI 공식 release notes

정밀도 메모:

- xAI 가격표는 Google / Anthropic / OpenAI보다 공개 문서에서 직접 표 추출이 덜 안정적이다.
- 그러나 xAI가 현재 순위에서 4위인 점을 감안하면, 이 정밀도 차이는 전체 순위를 바꿀 정도는 아니다.

### 1.2 글도비 내부 소스 검증

확인한 내부 문서:

- `docs/2026-03-12/TF-LLM-gemini-vs-grok-api-comparison.md`
- `docs/2026-03-10/TF-MULTI-LLM-provider-transition-spec.md`
- `docs/2026-02-27/opus_handoff_1m_context_audit.md`
- `docs/2026-03-11/00-test-02-03-control-treatment-crosscheck-report-OPUS.md`
- `docs/stage_map/metrics_baseline.md`
- `docs/stage_map/FILL_ORDER.md`
- `docs/poc/why_this_system.md`

### 1.3 Pass 1 결론

확정된 사실:

- 글도비 Stage 4 최소 원고 길이는 명시적으로 `4000자`
- Gemini 2.5 Pro가 저장소 내부 실증 근거가 가장 강함
- cheap lite/flash 계열은 글도비 한국어 장문 기준을 자동 통과한다고 볼 수 없음
- 기존 `Gemini vs Grok` 비교 문서만으로는 4개 벤더 전체 우선순위를 고정하기 어려움
- 최신 reasoning flagship 비교를 하려면 `Gemini 3.1 Pro Preview`와 `Grok 4.20 Beta`를 별도 보조 비교축으로 다뤄야 함

---

## 2. Pass 2: 순위 논리 교차 검증

### 2.1 검증한 주장

1. 시스템 변경 비용을 제외해도 Gemini 2.5 Pro가 1위인가
2. 첫 비구글 비교 대상으로 Claude Sonnet 4.6이 맞는가
3. OpenAI 1차 후보는 GPT-4.1이 아니라 GPT-5.1인가
4. Grok 4.1 Fast Reasoning은 production replacement보다 experiment 후보로 보는 게 맞는가
5. 최신 reasoning flagship 비교축은 production ROI 본표와 분리하는 게 맞는가

### 2.2 교차 검증 결과

#### 주장 1: Gemini 2.5 Pro가 1위 유지

상태: `확인`

근거:

- 글도비 내부 실증이 가장 강함
- 출력 길이 여유가 충분함
- 컨텍스트 여유가 충분함
- 한국어 지원이 공식 문서에 있음
- 가격도 현재 quality tier 안에서 방어 가능함

#### 주장 2: Claude Sonnet 4.6이 첫 외부 비교 대상

상태: `확인`

근거:

- 외부 후보 중 장문 문장감 가설이 가장 강함
- 다국어 / engaging response 포지셔닝이 분명함
- 출력 길이 여유가 충분함
- Grok보다 narrative 비교 대상으로 적절함

#### 주장 3: OpenAI 1차 후보는 GPT-5.1

상태: `확인, 단 예비 후보 메모 포함`

근거:

- `128K` 출력 여유가 장문 실험에 유리함
- GPT-4.1은 `~1M context`가 더 중요해질 때 쓰는 예비 카드로 두는 편이 합리적임

#### 주장 4: Grok 4.1 Fast Reasoning은 실험 우선

상태: `확인`

근거:

- 가격 / 컨텍스트 매력은 큼
- 하지만 한국어 장문 실증은 네 벤더 중 가장 약함
- 글도비 기준 핵심은 `싼 토큰`이 아니라 `안정적인 한국어 원고 생산`임

#### 주장 5: 최신 reasoning flagship 비교축은 별도 분리

상태: `확인`

근거:

- Google 쪽 최신 reasoning flagship은 `Gemini 3.1 Pro Preview`
- xAI 쪽 최신 reasoning flagship은 `Grok 4.20 Beta`
- 둘 다 최신 비교 대상으로는 가치가 있음
- 그러나 둘 다 preview/beta 성격이라 production ROI 본표와 같은 레벨로 섞으면 판단이 흐려짐
- 따라서 본표는 `production ROI`, 보조 메모는 `최신 flagship 비교`로 분리하는 쪽이 타당함

---

## 3. Pass 3: 오탐 제거

### 3.1 기각한 과장 주장

- `Grok이 제일 싸니까 1위여야 한다`
  - 기각: 싼 가격과 긴 컨텍스트만으로 글도비 장문 품질을 보장할 수 없다

- `GPT-4.1이 context가 더 크니 GPT-5.1보다 무조건 위다`
  - 기각: 이번 SSOT는 max context 단일 지표가 아니라 장문 ROI 우선순위를 고정하는 문서다

- `Claude는 문장감이 좋으니 Gemini보다 위다`
  - 기각: 글도비 내부 실증 근거는 Gemini 쪽이 압도적으로 강하다

- `Gemini 1위는 그냥 현재 코드베이스가 구글이라서다`
  - 보정: 전환 비용 때문만은 아니지만, 내부 실증 근거가 Google 쪽에 편향된 것도 사실이다. 따라서 본 SSOT의 1위는 `절대 우위`가 아니라 `현재 확보된 근거 기준 우위`로 읽어야 한다

### 3.2 기각한 과소 주장

- `4대 메이저라는 표현 자체가 틀렸다`
  - 기각: 본 문서는 글도비 hosted frontier shortlist 정의 문서다

- `모든 벤더를 글도비에서 live A/B 하기 전엔 95% 확신도를 줄 수 없다`
  - 기각: 그 수준의 실증은 cutover 판단에는 필요하지만, 우선순위 SSOT를 잠그는 데까지는 요구되지 않는다

---

## 4. 확신도 계산

시작 점수: `70`

- `+10` 4개 벤더 공식 소스 확인
- `+10` 글도비 내부 장문 기준 및 실증 근거 교차 확인
- `+5` 예비 후보 / 제외 후보 기준 정리
- `+5` 오탐 제거 후 순위 안정화 완료
- `-4` Anthropic / OpenAI / xAI의 글도비 live A/B 실증 부재
- `-1` xAI 가격 근거 정밀도가 다른 3사보다 약간 낮음

최종 확신도: **95%**

이 `95%`의 의미:

- `도입 우선순위 문서`로는 충분히 방어 가능
- 그러나 `2~4위 모델이 즉시 글도비 production에 안전하다`는 뜻은 아님

---

## 5. 최종 감리 판정

본 SSOT는 글도비 multi-LLM 도입 우선순위 기준 문서로 사용 가능하다.

최종 유지 순위:

1. `Gemini 2.5 Pro`
2. `Claude Sonnet 4.6`
3. `GPT-5.1`
4. `Grok 4.1 Fast Reasoning`

운영 메모:

- 이후 실제 벤더 A/B 실험 결과가 쌓이면 순위는 다시 조정될 수 있다
- 그 전까지는 본 문서를 글도비 multi-LLM 도입 우선순위 SSOT로 본다
