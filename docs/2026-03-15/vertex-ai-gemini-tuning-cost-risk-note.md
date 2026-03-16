<!-- [참고자료] -->
# Vertex AI Gemini 튜닝 비용 리스크 메모

> 작성일: 2026-03-15  
> 목적: `프로젝트승인요청서-글도비.md` 보강용 별도 메모  
> 작성 기준 시점: 2026-03-15 오후  
> 범위: Vertex AI Gemini 2.5 Pro supervised tuning 비용 리스크, 2026-03-15 실제 시도/취소 사건, 축소 실험안

---

## 1. 이 메모의 결론

2026-03-15 실제 업로드/튜닝 시도 결과, `Gemini 2.5 Pro supervised tuning`은 현재 준비된 전체 pseudo 코퍼스 기준으로 **실험용이라 보기 어려운 비용 규모**로 판단된다. 오늘 생성했다가 취소한 튜닝 잡은 `대기 중 -> 취소됨`으로 마감되었고, 큰 비용이 이미 확정되었을 가능성은 낮아 보인다. 그러나 Billing 반영 지연이 있을 수 있으므로 최종 청구는 사후 확인이 필요하다.

따라서 현 시점 권고는 아래와 같다.

1. 전체 pseudo 코퍼스를 그대로 관리형 튜닝에 투입하지 않는다.
2. 첫 실험은 `1작품 / 1 epoch` 단위로 시작한다.
3. 그 다음 단계는 `4작품 축소셋 / 1 epoch`로 올린다.
4. 비용 승인 문서에는 `운영형 API 비용`과 `관리형 튜닝 일회성 실험비`를 분리해 적는다.

---

## 2. 2026-03-15 실제 사건 요약

2026-03-15 `Vertex AI Studio > 관리형 튜닝` 화면에서 `gemini-2.5-pro` 기반 조정 작업을 생성했고, 이름은 `genre-investment-2.5pro`였다. 콘솔 관찰 기준 상태 흐름은 아래와 같았다.

- 생성 시각: `2026-03-15 12:20:24`
- 최종 확인 상태: `취소됨`
- 취소 반영 시각: `2026-03-15 12:23:37`

중간에 `실행 중` 상태로 넘어간 흔적은 콘솔에서 확인되지 않았다. 이 메모는 이를 근거로 `큐 대기 단계에서 취소되었을 가능성이 높다`고 본다. 다만 실제 청구는 Billing 반영 이후에만 확정된다.

---

## 3. 현재 기준 활성 업로드 대상

2026-03-15 현재, 과거의 대형 raw/pseudo JSONL은 실수 업로드 방지를 위해 워크스페이스에서 제거했다. 현재 활성 업로드 대상은 `특정 현판 작품` 단일 작품을 `제어형 style-control SFT`로 재구성한 저비용 셋이다.

- train: [train.jsonl](C:/Users/User/Desktop/글도비/data/investment_corpus_pseudo/style_control/독식하는_재벌_3세_3epoch_under_200k/train.jsonl)
- val: [val.jsonl](C:/Users/User/Desktop/글도비/data/investment_corpus_pseudo/style_control/독식하는_재벌_3세_3epoch_under_200k/val.jsonl)
- dataset manifest: [dataset_manifest.json](C:/Users/User/Desktop/글도비/data/investment_corpus_pseudo/style_control/독식하는_재벌_3세_3epoch_under_200k/dataset_manifest.json)

현재 활성 셋 수치는 아래와 같다.

- 작품 수: `1`
- train episode 수: `638`
- holdout episode 수: `113`
- train 샘플 수: `1,276`
- val 샘플 수: `226`
- 추정 학습 토큰: `1,415,931`
- 1 epoch 원화 참고치: 약 `52,035원`
- 3 epoch 원화 참고치: 약 `156,106원`

즉, 현재 기준 실제로 다시 올릴 수 있는 셋은 `독식하는_재벌_3세_3epoch_under_200k`뿐이다.

---

## 4. 공식 가격 근거

2026-03-15 확인 기준, Google 공식 `Vertex AI Pricing` 페이지에는 `Gemini 2.5 Pro Supervised fine-tuning` 가격이 **`1M training tokens 당 $25`**로 표시되어 있다. 또한 Google 공식 supervised tuning 문서는 tuning job 생성 시 `Cloud Storage URI`의 JSONL 학습셋/검증셋을 사용하고, `epoch count`를 지정한다고 설명한다.

이 메모의 비용 추정은 아래 공식 정보에 기초한다.

- `Gemini 2.5 Pro Supervised fine-tuning`: `$25 / 1M training tokens`
- tuning job 생성 방식: `Create tuned model`, `Cloud Storage JSONL`, `epoch count`

출처:

- [Vertex AI Pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing)
- [Tune Gemini models by using supervised fine-tuning](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini-use-supervised-tuning)
- [Prepare supervised fine-tuning data for Gemini models](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini-supervised-tuning-prepare)

---

## 5. 내부 비용 추정 방식

내부 추정은 [investment_corpus_support.py](C:/Users/User/Desktop/글도비/scripts/investment_corpus_support.py)의 `estimate_token_count()` 휴리스틱을 사용했다. 즉, 아래 수치는 **사전 의사결정용 추정치**이며 실제 Billing token과 완전히 일치한다고 볼 수는 없다.

계산식은 단순하다.

`추정 학습 토큰 수 / 1,000,000 x 25 USD`

원화 값은 2026-03-15 내부 판단용 환산치 `1 USD 약 1,470원 내외`를 적용한 참고값이며, 실제 결제 금액은 USD 청구 시점 환율과 수수료에 따라 달라질 수 있다.

---

## 6. 비용 추정 시나리오

### 6.1 전체 pseudo 코퍼스 그대로 사용할 경우

- train 샘플: `26,708`
- 추정 학습 토큰: `62,196,881`
- 1 epoch: 약 `$1,554.92`
- 1 epoch 원화 참고치: 약 `2,284,551원`
- 3 epoch: 약 `$4,664.76`
- 3 epoch 원화 참고치: 약 `6,853,652원`

이 수치는 실험성 1차 시도라고 보기에는 과도하다. 오늘 실제 취소 사건도 이 전체셋 기준 시도에서 발생했다.

### 6.2 축소안 1: 4작품 실험셋

검토된 4작품:

- 금수저 투자백서
- 특정 현판 작품
- 연봉 1조 신입사원
- 검은 머리 미국 대재벌!

추정 수치:

- 총 샘플: `6,964`
- 추정 학습 토큰: `16,069,454`
- 1 epoch: 약 `$401.74`
- 1 epoch 원화 참고치: 약 `590,252원`
- 3 epoch: 약 `$1,205.22`
- 3 epoch 원화 참고치: 약 `1,770,757원`

이 안은 아직도 결재가 필요한 비용 수준이지만, 전체셋보다는 실험 가능한 범주에 들어온다.

주의:

- 4작품 전부를 train에 넣기보다, 최소 1작품은 holdout으로 분리하는 구성이 바람직하다.

### 6.3 축소안 2: 1작품 실험셋

후보:

- 특정 현판 작품

추정 수치:

- 화수: `751`
- 샘플: `2,442`
- 추정 학습 토큰: `5,598,891`
- 1 epoch: 약 `$139.97`
- 1 epoch 원화 참고치: 약 `205,650원`
- 3 epoch: 약 `$419.91`
- 3 epoch 원화 참고치: 약 `616,949원`

이 안은 현재 시점에서 가장 현실적인 `관리형 튜닝 파일럿`으로 판단된다.

### 6.4 현재 활성안: 제어형 style-control SFT 저비용 셋

현재는 단일 작품조차 `원문 이어쓰기 창` 그대로 쓰지 않고, `제어값 + 짧은 앵커 + 특정 구간 생성` 구조로 다시 잘랐다. 사용한 출력 경로는 아래와 같다.

- [train.jsonl](C:/Users/User/Desktop/글도비/data/investment_corpus_pseudo/style_control/독식하는_재벌_3세_3epoch_under_200k/train.jsonl)
- [val.jsonl](C:/Users/User/Desktop/글도비/data/investment_corpus_pseudo/style_control/독식하는_재벌_3세_3epoch_under_200k/val.jsonl)

추정 수치:

- train 샘플: `1,276`
- val 샘플: `226`
- 추정 학습 토큰: `1,415,931`
- 1 epoch: 약 `$35.40`
- 1 epoch 원화 참고치: 약 `52,035원`
- 3 epoch: 약 `$106.20`
- 3 epoch 원화 참고치: 약 `156,106원`

즉, `통원문 3 epoch 약 685만 원` 대비 현재 활성 셋은 `3 epoch 약 15.6만 원` 수준으로 내려왔다. 이 차이 때문에라도 SFT는 반드시 잘라서 넣어야 한다.

---

## 7. 운영 판단

현재 문맥에서 중요한 것은 `운영형 Vertex API 비용`과 `관리형 튜닝 실험비`를 섞지 않는 것이다.

1. 운영형 API 비용은 `arc당 약 9,000원`, Vertex Batch 가정 적용 시 `약 6,300원` 축에서 관리하는 문제다.
2. 관리형 튜닝은 `한 번의 실험 자체가 수십만~수백만 원`이 될 수 있다.
3. 따라서 승인 문서에서는 `평시 운영비`와 `튜닝 실험비`를 별도 항목으로 분리해야 한다.
4. 지금 당장 관리형 튜닝을 승격하려면, 최소한 `튜닝 1회 상한`, `허용 epoch`, `파일럿 작품 수`를 먼저 고정해야 한다.

---

## 8. 권고안

### 8.1 즉시 권고

1. 전체 pseudo 코퍼스로 `Gemini 2.5 Pro` 관리형 튜닝을 재시도하지 않는다.
2. 현재 활성 업로드 대상은 `독식하는_재벌_3세_3epoch_under_200k` 셋 하나로 제한한다.
3. 이 셋은 `1 epoch`부터 볼 수 있지만, 비용 상한만 놓고 보면 `3 epoch`도 약 `15.6만 원` 수준이라 통제 가능하다.
4. 단일 작품 결과가 유의미할 때만 `4작품 축소셋 / 1 epoch`로 확장한다.

### 8.2 승인 문서 반영 문구

승인 문서에는 아래 취지로 들어가는 것이 맞다.

> Vertex AI 관리형 튜닝은 향후 품질 상향 경로로 유효하나, 전체 corpus를 그대로 사용할 경우 1회 실험비가 수백만 원 규모까지 커질 수 있다. 따라서 초기 파일럿은 대표 작품 단일셋 또는 4작품 축소셋의 1 epoch 범위에서만 제한적으로 운영하고, 본격 예산은 운영형 API 비용과 별도 승인 항목으로 관리하는 것이 타당하다.

---

## 9. 왜 통원문 SFT가 아니라 제어형 SFT인가

핵심 이유는 비용과 학습 효율 두 가지다.

1. `통원문 -> sliding window` 방식은 샘플 수와 토큰 수가 급격하게 불어난다.
2. 실제로 전체 pseudo 코퍼스를 그대로 넣으면 `3 epoch 약 685만 원` 추정치가 나왔다.
3. 반면 `제어값 + 앵커 + 특정 구간 생성`으로 재구성하면 같은 작품에서도 `3 epoch 약 15.6만 원` 수준으로 떨어진다.
4. `문체/페이싱 규칙 학습`이 목표일 때는 원문 전체를 통으로 압축 기억시키는 것보다, 제어 가능한 조건에서 특정 구간을 쓰게 하는 편이 목적 적합도가 높다.

즉, 현재 목적은 `작품 전체 암기`가 아니라 `문체, 대사 리듬, 장면 전환, 회차 마감 방식`의 재현성 향상이다. 이 목적에는 통원문보다 제어형 SFT가 더 맞다.

### 9.1 현재 제어형 SFT 입력 구조

현재 활성 셋은 아래 요소를 입력으로 사용한다.

- 장르
- 시점
- 톤
- 회차 목표
- 구간 목표
- 갈등 강도
- 장면 수
- 대사 비율
- 클리프행어 유형
- 전개 속도
- 도입 방식
- 문체 규칙
- 도입 앵커

출력은 회차 전체가 아니라 아래 두 가지 구간형 샘플이다.

- 중반 전개 이어쓰기
- 종결 장면 작성

이 구조를 택한 이유는 `문체 규칙`과 `페이싱 제어값`을 입력단에 명시해, 모델이 단순 복제보다 `조건을 만족하는 스타일 재현`을 배우게 하기 위함이다.

### 9.2 기대 효과

기대 효과는 아래 수준으로 잡는 것이 맞다.

1. 프롬프트를 덜 빡세게 줘도 웹소설식 문장 호흡이 더 빨리 붙는다.
2. 대사 비율, 전개 속도, 회차 마감 톤 같은 `회차 감각`이 더 안정적으로 붙는다.
3. 재벌/기업물 어휘 습관과 장면 전환 리듬이 더 쉽게 재현된다.
4. 반대로 장편 설계, 복선 장기 회수, 수백 화급 전체 일관성까지 이것만으로 해결되지는 않는다.

즉 기대치는 `드라마틱한 전모델 교체`가 아니라, `문체와 회차 운용 감각의 체감 개선`으로 잡아야 한다.

---

## 10. 장편 소설 아키텍처 판단: 왜 Hierarchical Pipeline인가

엄밀히 말해 장편 소설 시스템의 연구 구현은 다양하다. 다만 2026-03 기준 실무 관점에서 크게 묶으면 아래 두 갈래로 정리하는 것이 타당하다.

1. `Hierarchical pipeline`
2. `Rolling memory writer`

여기서 `Rolling memory writer`는 논문 고유명사가 아니라, 이 메모에서 쓰는 운영용 묶음 이름이다. 즉 `직전 본문 + 요약 메모리 + retrieval 조각`을 계속 굴리며 순차 생성하는 구조를 뜻한다.

### 10.1 왜 두 갈래로 보는가

이 분류는 아래 1차 자료들을 종합한 운영상 추론이다.

- `DOME`는 장문 스토리 생성을 크게 `outline/plan을 두고 쓰는 계열`과 `preceding content를 따라 점진적으로 쓰는 계열`로 구분하고, 후자는 거시적 계획 부재가 문제라고 본다.
- `DOC`는 chapter plotting -> passage planning -> generation의 계층 구조가 장문 일관성과 제어 가능성에 유리하다고 제시한다.
- `Agents' Room / Tell Me A Story`는 specialized agent와 narrative-theory 기반 writers' room 구성을 전제로 한다.
- `SCORE`와 `LongStory`는 memory, state tracking, summarization, retrieval을 붙여 장문 일관성을 보완하려는 계열이다.

즉 실무적으로는 `계층적으로 계획/분해하고 쓰는 구조`와 `메모리/요약/검색을 굴리며 연속 작성하는 구조`가 주요 두 축이라고 보는 편이 맞다.

### 10.2 왜 우리는 Hierarchical Pipeline 방향으로 잡았는가

결론부터 말하면, 우리 목표가 `회사 운영형 장편 소설 생산 체계`이기 때문이다.

계층형 파이프라인이 맞는 이유는 아래와 같다.

1. 장편은 `작품 전체 목표 -> arc -> 회차 -> 장면`으로 쪼개야 품질 통제가 가능하다.
2. 문체는 tuning으로 어느 정도 밀 수 있어도, `복선 배치`, `회차 역할`, `arc 단위 보상`, `장기 수익형 연재 속도`는 상위 계획이 없으면 흔들린다.
3. 운영 시스템은 실패 지점을 찾아야 하므로, outline/arc/episode/scene 단위로 책임이 분해되어 있어야 디버깅이 가능하다.
4. 향후 사람 검수, 재시도, 비용 통제, A/B 비교도 계층형 파이프라인 쪽이 훨씬 쉽다.

한마디로 `Hierarchy는 장편 운영의 뼈대`이고, memory는 그 뼈대 위에 붙는 보조 장치다.

### 10.3 Rolling Memory Writer의 치명적 단점

Rolling memory writer 계열은 짧은 데모나 단기 실험에는 편하지만, 장편 운영의 코어 아키텍처로 두기에는 단점이 크다.

1. 요약 손실이 누적된다.  
   회차가 길어질수록 이전 내용을 압축한 요약이 계속 다음 회차의 입력이 되므로, 빠진 정보와 왜곡이 누적된다.
2. retrieval miss가 조용히 터진다.  
   필요한 장면/설정/감정선이 안 뽑혀도 시스템은 보통 멈추지 않고 그냥 써 버린다. 그래서 오류가 나중에야 보인다.
3. 거시 계획이 약하다.  
   국소 문맥은 그럴듯해도, arc 보상이나 복선 회수는 쉽게 새거나 흐려진다.
4. 평가와 디버깅이 어렵다.  
   실패 원인이 프롬프트인지, summary인지, retrieval인지, 모델 생성인지 분리하기 어렵다.
5. 장기 연재에서 비용과 불안정성이 같이 커진다.  
   회차가 쌓일수록 메모리 갱신, retrieval 품질, 요약 재생성 비용이 함께 누적된다.

즉 Rolling memory writer는 `보조 장치`로는 유용하지만, `주 아키텍처`로 삼기엔 리스크가 크다.

### 10.4 최종 결론

결론은 명확하다.

1. 우리 시스템의 주 아키텍처는 `Hierarchical pipeline`이 맞다.
2. `Rolling memory writer`는 독립 노선이 아니라, 필요할 때 계층형 파이프라인 아래에 붙는 보조 메모리 장치로 보는 것이 맞다.
3. 튜닝 역시 이 철학과 맞춰 `통원문 압축`이 아니라 `제어 가능한 회차 구간 샘플`로 만드는 것이 타당하다.

즉 `Hierarchy가 뼈대`, `memory는 보조`, `tuning은 스타일 적응층`이라는 구도가 현재 판단 기준으로 가장 합리적이다.

### 10.5 왜 이 방향이 연구적으로도 정통파에 가깝다고 보는가

이 대목에서 중요한 것은 `글도비가 혼자 이상한 방향으로 튄 것인가` 여부다. 현재 확인되는 바는 반대에 가깝다.

1. 최근 장편 생성 연구들은 대체로 `그냥 길게 쓰기`보다 `계획`, `구조 분해`, `memory`, `retrieval`, `revision`을 붙이는 쪽으로 이동하고 있다.
2. 즉 문제 정의 자체가 이미 `장편은 계층적 구조 없이 버티기 어렵다`는 쪽으로 수렴하고 있다.
3. 글도비가 택한 `Stage 0 -> Stage 2 -> Stage 3 -> Stage 4` 분해, arc 단위 운영, blueprint 기반 생성, retrieval 보강은 이 흐름과 정렬된다.
4. 따라서 글도비의 방향성은 `괴상한 사설 구조`라기보다, 장편 서사 생성 문제를 실무형 생산 파이프라인으로 가져온 사례에 가깝다.

물론 이것이 곧바로 `글도비의 우월성`을 뜻하는 것은 아니다. 다만 최소한 아래 정도는 말할 수 있다.

- 장편 서사 생성에서 hierarchy-first 접근은 연구적으로 낯선 변칙이 아니다.
- rolling memory만으로 버티는 순차 생성보다, 구조 분해와 보조 memory를 결합하는 편이 더 널리 관찰되는 방향이다.
- 따라서 글도비는 `문제 자체를 잘못 정의한 시스템`이 아니라, 현재 장편 생성 연구의 중심 과제를 회사 운영형 생산 체계로 구현하려는 시도라고 볼 수 있다.

즉, 이 프로젝트는 `혼자만의 이상한 발명`이 아니라, `장편 생성의 주류 문제설정 위에서 실무형 운영 시스템을 만들고 있는 작업`에 더 가깝다.

### 10.6 개발부서 관점: 왜 여러 갈래 중 이 갈래를 택했는가

이 파트는 기술 선택 근거를 개발부서 기준으로 정리한 것이다. 질문은 단순하다.

> 장편 소설 시스템을 만들 때 여러 방식이 있는데, 왜 글도비는 `hierarchical pipeline + planning-execution loop` 쪽을 택했는가?

결론부터 말하면, `250화 이상 장편 웹소설을 회사 운영형 생산 체계로 만들려면 그 방향이 가장 통제 가능하기 때문`이다.

#### 10.6.1 비교 대상이 되는 대표 갈래

장편 생성 시스템을 실무적으로 놓고 보면 대략 아래 갈래들이 있다.

1. `single-pass / direct generation`
   - 큰 프롬프트 한 번으로 바로 길게 쓰는 방식
2. `rolling memory writer`
   - 직전 본문, 요약 메모리, retrieval 조각을 계속 이어 붙이며 순차 생성하는 방식
3. `hierarchical pipeline`
   - 작품 -> arc -> 회차 -> 장면으로 분해한 뒤 단계별 산출물을 만들고, 그 위에서 원고를 생성하는 방식
4. `multi-agent writers' room`
   - planner, writer, critic, editor 같은 역할을 나눠 협업시키는 방식

여기서 3번과 4번은 배타적이지 않다. 실제로는 `hierarchical pipeline` 위에 `writers' room`을 얹는 경우가 많다. 글도비도 이 조합에 가깝다.

#### 10.6.2 왜 single-pass를 버렸는가

single-pass는 구현이 가장 간단하지만, 장편 운영 체계로는 약점이 명확하다.

1. 실패 원인 분리가 안 된다.
   - 결과가 나빠도 plan이 없으니 어느 단계에서 틀렸는지 알 수 없다.
2. 재현성이 낮다.
   - 같은 조건에서도 출력 편차가 커지고, 품질 통제가 어렵다.
3. 장기 구조 유지가 약하다.
   - 250화 이상에서는 arc 역할, 복선, 회수 타이밍이 쉽게 붕괴한다.
4. 운영 시스템으로 확장하기 어렵다.
   - 로그, 심사, 재시도, 비용 통제, 사람 개입 지점을 잡기 어렵다.

즉 single-pass는 `데모`나 `개별 샘플 생성`에는 쓸 수 있어도, `회사 운영형 장편 생산`의 뼈대로 두기엔 약하다.

#### 10.6.3 왜 rolling memory writer를 주 아키텍처로 두지 않았는가

rolling memory writer는 얼핏 단순하고 유연해 보인다. 하지만 장편 운영 관점에서는 구조적 약점이 있다.

1. `요약 드리프트`
   - 이전 회차를 요약한 메모리가 다음 회차의 입력이 되고, 그 결과가 다시 요약되면서 서사가 점점 평탄화되거나 왜곡된다.
2. `retrieval 불확실성`
   - 필요한 설정이나 감정선을 못 뽑아도 시스템은 중단되지 않고 그냥 이어 쓴다.
   - 그래서 오류가 나중에 축적된 뒤에야 드러난다.
3. `거시 설계 약화`
   - 국소 장면은 그럴듯해도, arc 단위 보상 구조와 장기 플롯은 쉽게 흔들린다.
4. `디버깅 난도`
   - 문제 발생 시 원인이 summary인지, retrieval miss인지, prompt 충돌인지, 생성 품질인지 분리하기 어렵다.
5. `운영 비용 누적`
   - 장기 연재로 갈수록 memory 갱신, retrieval budget, summary regeneration 비용이 계속 쌓인다.

개발부서 기준으로 가장 큰 문제는 4번이다. `문제가 생겼을 때 어느 모듈을 고쳐야 하는지`가 불분명하면 운영 시스템으로 굴리기 어렵다.

#### 10.6.4 왜 hierarchical pipeline을 택했는가

글도비는 반대로 `분해 가능한 시스템`을 지향했다. 이게 hierarchical pipeline을 택한 핵심 이유다.

1. `책임 단위 분해`
   - 작품 목표, arc 목표, 회차 역할, 장면 배치를 각각 분리해 다룰 수 있다.
2. `오류 위치 추적`
   - 실패가 Stage 0, Arc 설계, Blueprint, Manuscript 생성 중 어디에서 났는지 추적 가능하다.
3. `재시도 비용 절감`
   - 전체를 다시 쓰지 않고, 문제 난 단계만 다시 생성하거나 수정할 수 있다.
4. `사람 개입 지점 명확화`
   - 기획, 감리, 수정 승인, 규칙 조정, QA를 단계별로 끼워 넣기 쉽다.
5. `장기 운영 적합성`
   - 250화 이상 연재에서 arc와 회차 역할을 명시적으로 유지할 수 있다.
6. `데이터화 용이성`
   - tuning, analytics, failure log, QA 기준선을 모두 단계별 산출물과 연결할 수 있다.

즉 개발부서 관점에서 hierarchy는 단순히 문학적 미학이 아니라, `시스템 공학적 디버깅 가능성`을 확보하는 선택이다.

#### 10.6.5 왜 planning-execution loop를 붙였는가

hierarchy만 있고 loop가 없으면, 단계는 많아도 실질 품질 개선이 어렵다. 그래서 글도비는 `planning-execution loop`를 붙였다.

구조는 단순하다.

1. 계획한다.
   - Stage 0에서 구조화
   - Stage 2에서 arc 설계
   - Stage 3에서 blueprint 작성
2. 실행한다.
   - Stage 4에서 원고 생성
3. 검사한다.
   - Director, advisory chain, validation
4. 다시 수정한다.
   - reject / revise / retry

이 loop를 붙인 이유는 아래와 같다.

1. 장편은 1회 생성으로 안정화되지 않는다.
2. 검수 결과가 다음 계획에 반영되어야 품질이 누적된다.
3. 실패 패턴을 시스템 자산으로 축적하려면, 계획과 실행 사이의 피드백 고리가 필요하다.

즉 `planning-execution loop`는 hierarchy를 실제 운영 구조로 만드는 핵심이다.

#### 10.6.6 왜 writers' room만으로 설명하지 않았는가

개발부서 입장에서는 `writers' room`이 설명력이 부족하다. 이유는 이것이 역할 구조는 설명하지만, 데이터 흐름과 실패 경계를 충분히 설명하지 못하기 때문이다.

`writers' room`은 누가 무슨 역할을 맡는지는 설명하지만,

- 어떤 산출물이 어디서 만들어지고
- 어느 단계가 SSOT이며
- 실패 시 어디서 재시도하는지
- memory와 retrieval이 어느 단계에 붙는지

까지 자동으로 설명해 주지는 않는다.

그래서 글도비의 핵심 표현은 `writers' room`보다 `hierarchical pipeline + planning-execution loop`가 더 정확하다.  
`writers' room`은 그 위에 얹힌 운영 방식으로 보는 편이 맞다.

#### 10.6.7 현재 글도비가 이 선택을 실제로 반영하고 있는가

로컬 구현 기준으로는 이미 상당 부분 반영되어 있다.

1. 승인요청서가 Stage 0 -> 2 -> 3 -> 4 구조를 명시한다.
2. validation은 `opening`, `climax`, `arc_finale`, `volume_finale`처럼 장기 운영 규칙을 이미 가진다.
3. Stage 4는 blueprint의 scene breakdown, arc data, episode bible, retrieval advisory를 받아 원고에 반영한다.
4. 즉 글도비는 개념만 hierarchy인 것이 아니라, 코드와 운영 문서 수준에서도 hierarchy-first 구조를 채택하고 있다.

물론 아직 `250화 이상 production-proven`이라고 말할 단계는 아니다. 하지만 방향 자체는 이미 구현물과 정렬되어 있다.

#### 10.6.8 개발부서용 최종 결론

개발부서 관점에서 보면, 글도비가 `hierarchical pipeline + planning-execution loop`를 택한 이유는 아래 한 문장으로 요약된다.

> 장편 웹소설을 회사 운영형 시스템으로 만들려면, 생성 품질보다 먼저 `통제 가능성`, `디버깅 가능성`, `재시도 비용`, `장기 구조 유지`를 잡아야 하고, 그 요구조건을 가장 잘 만족하는 쪽이 hierarchy-first 구조이기 때문이다.

즉 이 선택은 취향 문제가 아니라, `250화 이상 장편을 운영 시스템으로 만들기 위한 공학적 선택`에 가깝다.

참고 근거:

- [Vertex AI Pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing)
- [Prepare supervised fine-tuning data for Gemini models](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini-supervised-tuning-prepare)
- [DOME: Dynamic Multi-Agent Story Generation with Outline Expansion and Memory-Enhanced Revision](https://arxiv.org/abs/2405.16113)
- [DOC: A Hierarchical Story Generation Framework through Dynamic Outline Construction](https://arxiv.org/abs/2212.10077)
- [Agents' Room / Tell Me A Story](https://arxiv.org/abs/2410.02603)
- [SCORE: Story Coherence and Retrieval Enhancement for Long Narrative Generation](https://arxiv.org/abs/2503.23512)
- [LongStory: Long and Consistent Story Generation with AI through Planning, Retrieval and Interaction](https://arxiv.org/abs/2409.19676)

---

## 11. 메모 상태

- 상태: 2026-03-15 별도 메모 초안 작성 후 3-pass 점검 완료본
- 신뢰 수준: 95%

남은 불확실성:

1. 실제 청구 토큰은 Google 내부 billing token 기준이라 내부 추정치와 차이가 있을 수 있다.
2. 2026-03-15 취소된 잡의 실제 청구액은 Billing 반영 이후에만 확정된다.
3. 단일 작품 또는 4작품 축소셋의 실제 품질 향상 폭은 아직 실험 전이다.
