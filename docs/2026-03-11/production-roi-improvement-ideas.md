# 글도비 실생산 ROI 개선 아이디어 메모

## 목적

이 문서는 글도비의 `실제 생산 비용`, `wall-clock 시간`, `retry 증폭`을 줄이는 방향의 개선 아이디어를 따로 모아두기 위한 기술 메모다.  
핵심 원칙은 아래와 같다.

- `새 CLI` 자체보다 `실제 호출량/지연/재시도`를 줄이는 쪽이 ROI가 높다.
- `운영 레이어용 도구`와 `실생산 직접 개선 수단`을 구분한다.
- 지금 바로 붙일 수 있는 것과, 아직 시기상조인 것을 분리한다.

## 요약

현재 글도비에서 실생산 ROI가 높은 후보는 아래 순서로 본다.

1. `Vertex Context Caching`
2. `Prompt prefix 정규화`
3. `Batch Prediction`으로 비실시간 작업 분리
4. `LiteLLM` 기반 라우팅/예산 제어
5. `자체 호스팅(vLLM speculative decoding)`은 장기 검토

한 줄 결론:

`지금 당장 ROI가 높은 것은 CLI 추가가 아니라 캐싱, 라우팅, 배치 분리다.`

## 아이디어 목록

| 항목 | 적용 위치 | 기대 효과 | 현재 적합도 | 메모 |
| --- | --- | --- | --- | --- |
| Vertex Context Caching | Stage 2/3/4 공통 prefix | 토큰 비용 절감, 응답 지연 완화 | 매우 높음 | Bible, Treatment, Style Guide, 고정 규칙에 직결 |
| Prompt prefix 정규화 | PromptLoader / stage context builder | cache hit 상승, 프롬프트 안정화 | 매우 높음 | 캐싱과 세트로 움직여야 의미가 큼 |
| Batch Prediction | 사후 품질 평가, 비교 채점, 백필 | 온라인 추론 부하 분리 | 높음 | 생성 본체보다 보조 작업에 적합 |
| LiteLLM 라우팅 | 모델 게이트웨이 | `pro/lite` 혼합 운용, fallback, budget control | 중상 | 지금처럼 `00_test_02/03` 비교 실험할 때 특히 유용 |
| vLLM speculative decoding | self-host open model 경로 | 속도 개선 가능 | 낮음 | 현재 Vertex Gemini hosted path에는 직접 적용 어려움 |

## 1. Vertex Context Caching

### 왜 ROI가 높은가

- 글도비는 Bible, Treatment, Style Guide, 안전 규칙, 세계관 상태 등 `반복 prefix`가 길다.
- 이 구조는 context caching의 ROI가 높다.
- 특히 같은 프로젝트에서 Arc/EP를 연속 생산할 때 공통 컨텍스트를 반복 전송하는 비용이 크다.

### 글도비에 맞는 적용 포인트

- Stage 2
  - Bible
  - Treatment block
  - 장르 고정 규칙
- Stage 3
  - Arc tactical_doc
  - 세계관/인물 고정 정보
- Stage 4
  - Style guide
  - 장기 시리즈 규칙
  - 고정 안전 규칙

### 기대 효과

- 입력 토큰 비용 절감
- 프롬프트 조립량 감소
- 동일 prefix 반복 시 응답 시간 일부 감소 가능

### 적용 시 주의점

- 캐시 hit를 높이려면 prefix가 안정적으로 같아야 한다.
- 즉, prompt 앞부분의 순서/표현이 자주 바뀌면 효과가 줄어든다.
- 그래서 `Prompt prefix 정규화`와 같이 가야 한다.

## 2. Prompt Prefix 정규화

### 왜 필요한가

캐싱은 `있다`보다 `맞게 쓴다`가 중요하다.  
글도비는 현재도 rich prompt를 많이 쓰지만, 고정 문맥이 Stage/round별로 미세하게 흔들리면 cache hit가 떨어질 수 있다.

### 적용 포인트

- PromptLoader의 공통 system block 순서 고정
- Stage 4 context builder의 stable context/headroom 블록 정렬
- 고정 규칙, 금지 규칙, style guide 요약의 위치 고정

### 기대 효과

- Context Caching 효과 극대화
- 프롬프트 비교/감리도 쉬워짐
- retry 간 의미 없는 prompt drift 감소

## 3. Batch Prediction으로 비실시간 작업 분리

### 왜 ROI가 있는가

지금 비용/시간의 핵심은 `실시간 생성 파이프라인`이 다 떠안고 있다는 점이다.  
그런데 아래 작업은 꼭 온라인일 필요가 없다.

- 사후 quality rescoring
- 비교 채점
- 보고서용 요약/집계
- 백필/재평가
- 대규모 calibration 데이터 생성

### 글도비 적용 후보

- `quality_metrics` 백필
- 여러 run의 비교 리포트 생성
- batch 수동감리 보조 요약
- 대량 프로젝트의 retrospective scoring

### 기대 효과

- 온라인 Stage 4 latency 감소
- 실시간 실패 시에도 부가 계산 비용 분리
- 비용 관리가 쉬워짐

### 주의점

- Arc/EP 본생성은 여전히 온라인 품질 관리가 필요하다.
- Batch Prediction은 `본체 대체`가 아니라 `주변부 분리`에 적합하다.

## 4. LiteLLM 기반 라우팅

### 왜 후보인가

지금 이미 `00_test_02`와 `00_test_03`처럼 모델 조합 실험을 하고 있다.  
이 실험을 계속할수록 `모델 게이트웨이`의 가치가 커진다.

### 글도비에서 기대할 수 있는 것

- `writer-lite / director-pro`
- `all-pro / all-lite`
- fallback 체인
- budget ceiling
- 환경별 모델 조합 스위칭

### ROI가 높은 상황

- 비용/품질 trade-off 실험이 잦을 때
- 프로젝트별 다른 키/모델 정책을 쓸 때
- 장기적으로 Gemini 외 모델도 비교할 가능성이 생길 때

### 지금 당장 도입해야 하나

- `즉시 필수`는 아니다.
- 다만 `모델 실험이 반복되면` 빠르게 ROI가 생긴다.

## 5. 자체 호스팅 / vLLM speculative decoding

### 왜 지금은 후순위인가

- vLLM speculative decoding은 주로 self-hosted open model 경로에서 의미가 크다.
- 현재 글도비 주 경로는 Vertex Gemini hosted API다.
- 즉, 지금 당장 붙여도 구조적으로 직접 효익을 내기 어렵다.

### 언제 검토할 가치가 생기나

- 자체 GPU 인프라 검토 시
- 반복 작업 일부를 open model로 내려서 처리하고 싶을 때
- 장기적으로 비용 상한이 크게 문제될 때

## 운영 레이어 vs 실생산 레이어

아래 구분은 유지하는 것이 좋다.

### 운영 레이어용

- Workspace/Docs/Sheets/Chat
- Gemini CLI / Codex / Claude Code
- 승인/보고/알림/운영 보조

### 실생산 직접 개선용

- Context Caching
- Prompt prefix 정규화
- Batch Prediction
- LiteLLM 라우팅
- 장기적으로 self-host inference

즉, `도구를 더 붙이는 것`과 `실제 생산을 싸고 빠르게 만드는 것`은 구분해서 봐야 한다.

## 권장 우선순위

### 지금 바로 검토

1. `Vertex Context Caching`
2. `Prompt prefix 정규화`
3. `Batch Prediction으로 보조 작업 분리`

### 다음 실험 단계에서 검토

4. `LiteLLM`

### 장기 검토

5. `vLLM / self-host path`

## 적용 전 체크 질문

1. 이 아이디어가 `Stage 4 호출 횟수`를 줄이는가, 아니면 단순히 도구만 늘리는가
2. 이 아이디어가 `입력 토큰`을 줄이는가
3. 이 아이디어가 `retry amplification`을 줄이는가
4. 이 아이디어가 `운영 복잡도`를 지나치게 올리지 않는가

위 질문에 2개 이상 `예`가 나오면 실생산 ROI 후보로 본다.

## 메모

- 현재 글도비의 주 병목은 대체로 `LLM 응답 속도 x 호출 횟수`다.
- 따라서 가장 큰 개선은 보통 `더 똑똑한 도구`보다 `덜 부르게 만드는 구조`에서 나온다.
- `캐싱`, `라우팅`, `배치 분리`는 이 조건에 직접 닿는 후보들이다.

최종 상태: 2026-03-11 기준 실생산 ROI 아이디어 메모  
성격: 백로그/기술 메모  
용도: 후속 개선 배치 설계 참고
