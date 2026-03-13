# 글도비 Multi-LLM 도입 우선순위 SSOT

> 작성일: 2026-03-13
> 상태: 실행 기준 SSOT
> 범위: Google / Anthropic / OpenAI / xAI의 hosted API 모델만 포함
> 정책: 모델 변경에 따른 시스템 수정 비용은 순위 산정에서 제외
> 게이트: 글도비 Stage 4 최소 기준인 `4,000자 이상` 한국어 장문을 안정적으로 쓸 수 있는 후보만 포함
> 우선순위 기준 문서: `docs/2026-03-12/TF-LLM-gemini-vs-grok-api-comparison.md`를 참고하되, 최종 우선순위는 본 문서를 SSOT로 고정

---

## 0. 결론 요약

2026년 3월 13일 기준, 글도비의 multi-LLM 도입 우선순위는 아래로 고정한다.

1. **Google Gemini 2.5 Pro**
2. **Anthropic Claude Sonnet 4.6**
3. **OpenAI GPT-5.1**
4. **xAI Grok 4.1 Fast Reasoning**

이 순위는 업계 전체 모델 순위가 아니다.  
글도비가 당장 비교 대상으로 삼을 만한 `4대 메이저 hosted frontier API` 후보군 안에서, `4천 자 이상 한국어 장문 안정성`을 기준으로 정한 실무 우선순위다.

핵심 해석은 다음과 같다.

- 글도비 기준 현재 ROI 1위 baseline은 여전히 **Gemini 2.5 Pro**다.
- 구글 외 첫 비교 대상은 **Claude Sonnet 4.6**이 맞다.
- OpenAI 라인을 열 경우 1차 후보는 **GPT-5.1**이고, **GPT-4.1**은 예비 후보로 둔다.
- xAI는 **Grok 4.1 Fast Reasoning**이 가장 흥미로운 실험 후보지만, 한국어 장문 실증이 상대적으로 약하므로 즉시 교체 1순위는 아니다.

본 문서의 순위 확신도는 아래 감리 문서에서 잠근다.

- `docs/2026-03-13/geuldobi-multi-llm-adoption-priority-3pass-audit.md`

여기서 말하는 `95% 확신도`는 `도입 우선순위 판단`에 대한 것이며, `즉시 프로덕션 전환 안정성`을 뜻하지는 않는다.

---

## 1. 범위 고정

### 1.1 포함 벤더

- Google
- Anthropic
- OpenAI
- xAI

본 문서에서 `4대 메이저`라고 부르는 범위는 위 네 벤더다.  
이는 글도비 실무용 hosted API shortlist를 뜻하는 정의이지, 시장 전체를 망라한다는 뜻은 아니다.

### 1.2 제외 범위

- 오픈웨이트 / 셀프호스팅 모델
- hosted frontier API로 직접 비교하기 어려운 특수 벤더
- preview/beta 성격이 강한 모델
- UI/브리지/백엔드 수정 비용
- 테스트 재작성 비용
- provider 전환에 따른 운영 비용

### 1.3 글도비 기준 게이트

후보 모델은 아래 조건을 모두 만족해야 한다.

- 한국어 장문 생성이 `화당 4,000자 이상`에서 현실적으로 가능해야 한다
- 출력 길이와 컨텍스트 여유가 글도비 Stage 2~4에 맞아야 한다
- hosted API가 실사용 가능한 수준이어야 한다
- 단순 벤치마크 점수만 높고 한국어 장문 근거가 없는 모델은 1차 우선순위에서 제외한다

글도비 내부 기준선:

- `Stage 4 manuscript min=4000, target=5000, max=15000`

근거 문서:

- `docs/stage_map/metrics_baseline.md`
- `docs/stage_map/FILL_ORDER.md`

---

## 2. 순위 산정 방식

### 2.1 ROI 정의

이번 문서에서 ROI는 아래를 뜻한다.

1. 글도비형 한국어 장문 품질 신뢰도
2. `4,000자 이상` 안정 통과 가능성
3. 출력 길이 / 컨텍스트 여유
4. API 성숙도와 구조화 출력 적합성
5. 가격 효율

### 2.2 가중치

- 한국어 장문 적합성: `40`
- 출력 길이 / 컨텍스트 여유: `20`
- API 성숙도: `15`
- 가격 효율: `25`

정량 벤치마크 표를 만든 것이 아니라, 글도비 도입 우선순위를 잠그기 위한 실무 판단 규칙이다.

---

## 3. 최종 우선순위

| 순위 | 벤더 | 모델 | 4천 자 이상 한국어 장문 필터 통과 이유 | ROI 판정 |
|---|---|---|---|---|
| 1 | Google | **Gemini 2.5 Pro** | 글도비 내부 실증이 가장 많고, 1M급 컨텍스트와 65,536 출력 여유를 가지며 가격도 방어 가능 | **현재 production ROI 1위** |
| 2 | Anthropic | **Claude Sonnet 4.6** | 다국어/문장 완성도 가설이 강하고, 64K 출력 여유가 있으며 외부 비교 후보 중 문장형 품질 기대가 가장 높음 | **비구글 비교 ROI 1위** |
| 3 | OpenAI | **GPT-5.1** | 128K 출력 여유, 높은 API 성숙도, Claude 대비 상대적으로 나은 가격 구조 | **OpenAI 진입 ROI 1위** |
| 4 | xAI | **Grok 4.1 Fast Reasoning** | 2M급 컨텍스트와 매우 공격적인 가격이 장점 | **실험 ROI 높음, 한국어 품질 확신은 가장 낮음** |

---

## 3-A. 최신 reasoning flagship 비교 메모

위 표는 `현재 글도비 production ROI 우선순위`다.  
별도로, 2026년 3월 기준 최신 reasoning flagship끼리 비교하면 아래처럼 본다.

- Google 최신 reasoning flagship: `Gemini 3.1 Pro Preview`
- xAI 최신 reasoning flagship: `Grok 4.20 Beta`

현재 판단:

- `최신 flagship 대 최신 flagship` 비교축은 의미가 있다.
- 다만 이 비교는 `preview/beta 축`이므로, 위 production ROI 순위표와 같은 층위로 섞지 않는다.

### Gemini 3.1 Pro Preview

Google 공식 문서 기준:

- model code: `gemini-3.1-pro-preview`
- input limit: `1,048,576`
- output limit: `65,536`
- 가격:
  - `<= 200K prompt`: input `$2.00/M`, output `$12.00/M`
  - `> 200K prompt`: input `$4.00/M`, output `$18.00/M`

해석:

- `Gemini 2.5 Pro`보다 더 비싸다.
- production ROI만 보면 바로 1순위로 올릴 이유는 부족하다.
- 대신 최신 reasoning/agentic 성능 비교축에서는 Google 대표 모델로 봐야 한다.

### Grok 4.20 Beta

xAI 공식 문서 기준:

- `newest flagship model`
- context `2,000,000`
- capabilities: `structured outputs`, `reasoning`, `agentic tool calling`

해석:

- 서류상으론 매우 공격적이다.
- 다만 beta 성격이 강하고, 한국어 장문 품질 실증은 여전히 부족하다.
- 따라서 `Grok 4.20 Beta`는 `최신 비교 대상`으로는 유효하지만, 곧바로 글도비 production 1순위 후보로 올리지는 않는다.

### 최신 flagship 비교 결론

- `순수 최신 reasoning flagship 비교`에선 `Gemini 3.1 Pro Preview vs Grok 4.20 Beta`가 맞다.
- 하지만 `글도비 production ROI 순위`는 여전히 `Gemini 2.5 Pro` baseline을 유지하는 쪽이 맞다.
- 이유는 간단하다.
  - `Gemini 3.1 Pro`는 아직 preview
  - `Grok 4.20`도 beta
  - 둘 다 글도비 한국어 장문 실증이 부족하다

즉:

- `최신 모델끼리 누가 더 세냐`라는 질문과
- `지금 글도비가 어떤 모델부터 비교 도입해야 하느냐`는 다른 질문이다.

---

## 4. 모델별 판단 근거

### 4.1 1위: Gemini 2.5 Pro

1위를 유지하는 이유:

- 글도비 내부 실증 근거가 가장 강하다.
- `docs/2026-02-27/opus_handoff_1m_context_audit.md` 기준으로 Stage 2, Stage 3, Chief Writer, Director 모두 `gemini-2.5-pro` 중심의 1M 컨텍스트 전략을 전제로 튜닝돼 있다.
- `docs/2026-03-11/00-test-02-03-control-treatment-crosscheck-report-OPUS.md` 기준으로 `2.5-pro` control run은 4화 완주에 성공했고, 저가 lite 프로파일은 완주에 실패했다.
- Google 공식 문서 기준:
  - context 약 `1,048,576`
  - max output `65,536`
  - 한국어 지원 명시
  - 가격 약 `input $1.25/M`, `output $10/M`

의미:

- 글도비는 일반 챗봇 품질이 아니라 `복합 컨텍스트 하의 한국어 장문 생산 안정성`이 핵심이다.
- 이 저장소 안에서 그 요구를 가장 직접적으로 입증한 모델이 Gemini 2.5 Pro다.

약점:

- 최저가는 아니다.
- `docs/poc/why_this_system.md`가 지적한 Google 단일 의존 리스크는 여전히 있다.

최종 판정:

- **새 벤더가 글도비 실런타임에서 더 높은 한국어 장문 ROI를 입증하기 전까지 1위 baseline 유지**

### 4.2 2위: Claude Sonnet 4.6

구글 외 첫 비교 대상으로 잡는 이유:

- Anthropic 공식 문서가 Claude 4 계열을 `multilingual tasks`, `engaging responses` 측면에서 강하게 포지셔닝한다.
- 공식 문서 기준:
  - 기본 `200K` context, `1M beta` 옵션
  - `64K` max output
  - 가격 약 `input $3/M`, `output $15/M`

Gemini를 못 넘는 이유:

- 가격이 더 비싸다.
- 글도비 내부 한국어 장문 실증은 아직 Gemini만큼 없다.
- 기본 context는 Gemini 1M급보다 보수적이다.

그래도 2위인 이유:

- 외부 비교 후보 중 `장문 문장감` 기대치가 가장 높다.
- Grok보다 글도비형 글쓰기 품질 가설이 강하고, OpenAI보다 prose-first 비교 대상으로 잡기 좋다.

최종 판정:

- **비구글 첫 실험 벤더는 Claude Sonnet 4.6이 맞다**

### 4.3 3위: GPT-5.1

OpenAI 1차 후보로 두는 이유:

- OpenAI 공식 문서 기준:
  - context `400,000`
  - max output `128,000`
  - 가격 약 `input $1.25/M`, `output $10/M`
- 출력 여유가 매우 넓어서 장문 생성 실험에 유리하다.
- API 성숙도가 높고 문서화가 잘 되어 있다.

Claude보다 아래인 이유:

- 글도비 내부 한국어 장문 근거가 약하다.
- Anthropic에 비해 `문장형 창작물` 측면의 직접적 포지셔닝이 덜 강하다.

GPT-4.1보다 우선인 이유:

- 이번 기준은 `최대 컨텍스트`만이 아니라 `4천 자 이상 한국어 장문 출력 안정성`이다.
- `128K` max output은 GPT-5.1 쪽이 더 매력적이다.

예비 후보 메모:

- `GPT-4.1`은 near-1M context가 더 중요해질 때 쓰는 OpenAI 예비 카드로 남긴다.

최종 판정:

- **OpenAI 첫 비교 모델은 GPT-5.1**

### 4.4 4위: Grok 4.1 Fast Reasoning

후보군에 넣는 이유:

- xAI 모델 문서와 공식 스니펫 기준:
  - `2M`급 context
  - structured outputs/tooling 지원
  - 매우 낮은 가격대
- 서류상 ROI는 가장 공격적이다.

그래도 4위인 이유:

- 한국어 장문 품질 실증이 네 벤더 중 가장 약하다.
- 기존 비교 문서 `docs/2026-03-12/TF-LLM-gemini-vs-grok-api-comparison.md`도 Grok의 한국어 장문 적합성은 직접 검증이 더 필요하다고 판단했다.
- 값싼 토큰과 긴 컨텍스트가 곧장 한국어 원고 품질로 이어지는 것은 아니다.

근거 정밀도 주의:

- xAI 공개 문서는 가격표 추출 정밀도가 Google / Anthropic / OpenAI보다 약간 떨어진다.
- 따라서 본 문서의 xAI 가격행은 `현재 기준 최선의 공식 확인값`으로 읽어야 한다.

최종 판정:

- **고수익 실험 후보는 맞지만, 즉시 production 교체 1순위는 아니다**

---

## 5. 예비 후보와 제외 후보

### 5.1 예비 후보

| 모델 | 예비로 둔 이유 |
|---|---|
| OpenAI `GPT-4.1` | `~1M` context 쪽이 더 중요해질 경우 OpenAI 비교축으로 가치 있음 |
| Google `Gemini 2.5 Flash` | 비용 절감 실험 가치는 있지만, 저가 tier가 글도비 장문 하중을 못 버틴 근거가 이미 있음 |

### 5.2 1차 우선순위 제외

| 모델 | 제외 이유 |
|---|---|
| Anthropic `Claude Opus 4.1` | Sonnet 4.6 대비 ROI가 불리함 |
| xAI `Grok 4.20 Beta` | beta 성격이 강함 |
| lite / mini / haiku 계열 저가 모델 | 글도비의 `4천 자 이상 한국어 원고` 기준을 안정적으로 넘긴다는 확신이 부족함 |

---

## 6. 글도비 도입 순서

글도비가 실제로 multi-LLM 비교를 연다면 순서는 아래로 고정한다.

1. `Gemini 2.5 Pro`를 baseline으로 유지
2. `Claude Sonnet 4.6` 비교
3. `GPT-5.1` 비교
4. `Grok 4.1 Fast Reasoning` 비교
5. `GPT-4.1`은 `400K context`가 부족하다고 판단될 때만 예비 비교축으로 사용

주의:

- 이 문서는 `우선순위 SSOT`이지 `즉시 전환 명령서`가 아니다.

---

## 7. 최종 결론

- 글도비 기준 `4대 메이저`는 실무적으로 **Google / Anthropic / OpenAI / xAI**로 묶어도 된다.
- `4천 자 이상 한국어 장문`이라는 기준을 걸면, 값싼 모델이 자동으로 상위권이 되지는 않는다.
- 시스템 수정 비용을 제외해도 1위는 여전히 **Gemini 2.5 Pro**다.
- 첫 비구글 비교 대상은 **Claude Sonnet 4.6**이 맞다.
- Grok은 실험 가치는 높지만, 즉시 production 전환 1순위는 아니다.

---

## 8. 근거 소스

### 8.1 공식 벤더 문서

- Google Gemini models: https://ai.google.dev/gemini-api/docs/models
- Google pricing: https://ai.google.dev/pricing
- Google Gemini changelog: https://ai.google.dev/gemini-api/docs/changelog
- Google supported languages: https://ai.google.dev/gemini-api/docs/languages
- Anthropic models overview: https://docs.anthropic.com/en/docs/about-claude/models/overview
- Anthropic pricing: https://www.anthropic.com/pricing#anthropic-api
- OpenAI models overview: https://platform.openai.com/docs/models
- OpenAI GPT-4.1: https://platform.openai.com/docs/models/gpt-4.1
- OpenAI GPT-5: https://platform.openai.com/docs/models/gpt-5
- OpenAI pricing: https://platform.openai.com/docs/pricing
- xAI models overview: https://docs.x.ai/docs/models
- xAI release notes: https://docs.x.ai/docs/release-notes
- xAI Grok 4.1 Fast Reasoning: https://docs.x.ai/docs/models/grok-4.1-fast-reasoning

### 8.2 글도비 내부 문서

- `docs/2026-03-12/TF-LLM-gemini-vs-grok-api-comparison.md`
- `docs/2026-03-10/TF-MULTI-LLM-provider-transition-spec.md`
- `docs/2026-02-27/opus_handoff_1m_context_audit.md`
- `docs/2026-03-11/00-test-02-03-control-treatment-crosscheck-report-OPUS.md`
- `docs/stage_map/metrics_baseline.md`
- `docs/stage_map/FILL_ORDER.md`
- `docs/poc/why_this_system.md`
