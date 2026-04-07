# 글도비 API 기반 유지 여부 및 구독형 대체 가능성 효용 분석 보고서

- 작성일: 2026-04-07
- 상태: final (3-pass 감리 통과)
- 문서 경로: `docs/2026-04-07/geuldobi-api-vs-subscription-utility-analysis-report.md`
- 질문:
  - 글도비는 왜 API 기반으로 가야 하는가
  - 구독형 AI 글쓰기만으로 대체 가능한가
  - 둘 중 무엇이 더 효율적인가
- 목적: 글도비의 현재 시스템 정의를 기준으로 `API 유지`, `구독형 대체`, `혼합 운영`의 효용을 비교하고, 어떤 목표에서 어떤 선택이 맞는지 경영/운영 관점으로 정리한다.
- 범위:
  - 글도비 현재 코드베이스와 운영 문서 기준 시스템 적합성 판단
  - 구독형 vs API의 운영 효용 비교
  - 비용, 통제, 재현성, 자동화, 관측성, 조직 운영 측면의 장단점
  - 글도비에 맞는 권장 운영모델 제안
- 비범위:
  - 특정 벤더의 월 예상 청구액 정밀 산정
  - 모델 품질 벤치마크 실험 자체
  - 즉시 구현 변경 또는 아키텍처 마이그레이션 실행
- Evidence Basis:
  - 워크스페이스:
    - `README.md`
    - `config/models.yaml`
    - `modules/api/control_plane_contract.py`
    - `modules/api/bridge_server.py`
    - `modules/api/process_runner.py`
    - `modules/core/db_manager.py`
    - `docs/2026-04-03/0_0-stage34-ep2-focused-bounded-canary-r5-audit.md`
    - `docs/2026-04-06/01_golden_stage2_lane3_db_residue.md`
    - `docs/2026-04-06/5arc-terminal1-provider-env-guard-survey.md`
  - 외부 공식 자료:
    - OpenAI Help Center: ChatGPT Plus
    - OpenAI: API Pricing
    - Google AI for Developers: Using Gemini API keys
    - Google AI for Developers: Gemini Batch API
    - Google One Help: Google AI Pro membership
- Commit State:
  - Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
  - Baseline Dirty Summary: `dirty: tracked 180, untracked 124`
- Confidence:
  - 96%: 글도비 현재 시스템 정의와 API 적합성 판단
  - 94%: 구독형이 유리한 사용 구간 분리
  - 88%: 정확한 총비용 우열. 현재 문서는 벤더별 가격표와 로컬 운영 증거는 봤지만, 실제 월간 호출량/좌석수/편집 인건비를 넣은 정밀 TCO 모델링까지 하지는 않았다.

---

## 0. 핵심 결론

1. **글도비는 단순한 "AI로 글을 쓰는 채팅 도구"가 아니라, Stage 0~4 파이프라인, Director 심사, DB 저장, 로그, 데스크톱 control plane을 가진 운영 시스템이다.** 이 정의를 유지하는 한, 시스템의 중심축은 구독형보다 API가 맞다.
2. **하지만 모든 글쓰기 업무를 API로 돌릴 필요는 없다.** 기획 발상, 문체 탐색, 아이디어 브레인스토밍, 장면 대안 탐색 같은 인간 주도 작업은 구독형이 더 싸고 빠를 수 있다.
3. **따라서 글도비의 최적 해법은 "구독형 or API"의 단일 선택이 아니라 `권한 있는 생산 라인은 API`, `탐색/실험 라인은 구독형`인 혼합 운영 모델이다.**
4. **"API로 안 가도 되느냐"라는 질문에 대한 답은 조건부 YES다.** 다만 그 경우에는 글도비를 지금 같은 생산 시스템이 아니라, 인간 작가의 보조 글쓰기 툴로 재정의해야 한다.
5. **반대로 현재 가치제안이 `자동화된 장편 생산 파이프라인`이라면 API는 선택이 아니라 기반 인프라에 가깝다.**

---

## 1. 먼저 정의해야 할 것: 글도비는 "대화 도구"인가, "생산 시스템"인가

이 질문은 모델 품질 문제가 아니라 **운영 단위가 무엇인가**의 문제다.

| 운영 단위 | 더 잘 맞는 수단 | 이유 |
|---|---|---|
| 한 명이 대화창에서 초안을 만들고 손으로 다듬는 작업 | 구독형 | 사람의 사고 흐름과 대화형 UX가 핵심이기 때문 |
| 정해진 입력을 받아 Stage를 순차 실행하고 산출물/로그/비용을 남기는 작업 | API | 프로그램 호출, 저장, 재시도, 계측이 필요하기 때문 |
| 대량 평가, 후보 병렬 생성, 회귀 점검, 후처리 | API | 배치/자동화/기록성이 필요하기 때문 |
| 아이디어 확장, 장면 대안, 즉흥 대화 | 구독형 | 고정 좌석비로 빠르게 반복하기 좋기 때문 |

글도비의 현재 레포 구조는 명확히 후자다.

- `README.md`는 글도비를 `Stage 0 -> 4` 생산 파이프라인, Director 중심 심사, SQLite 상태 저장, Electron control plane이 묶인 시스템으로 설명한다.
- `modules/api/control_plane_contract.py`는 데스크톱 렌더러 -> IPC -> `bridge_server /run` -> `ProcessRunner` -> `main_a.py`로 이어지는 **공개 실행 경로**를 계약으로 둔다.
- 같은 파일은 `control_plane_provenance`, `project_data_db`, `episode_production_log`를 authoritative sink로 규정한다.
- `modules/api/bridge_server.py`는 `/run`, `/status`, `/quality/dashboard` 등 운영 엔드포인트를 제공한다.
- `modules/core/db_manager.py`는 `save_cost_record`, `get_cost_summary`, `save_ui_event` 등 비용/운영/가시성용 sink를 갖고 있다.
- `config/models.yaml`은 Gemini/Anthropic/OpenAI/Vertex를 provider 단위로 라우팅할 수 있게 설계되어 있다.

즉, 글도비는 "웹앱 구독형 AI에 글 써 달라고 묻는 행위"를 넘어서 **실행, 저장, 계측, 검증, 복구를 가진 시스템**이다.

---

## 2. 구독형이 강한 영역

구독형 AI는 과소평가하면 안 된다. 특정 상황에서는 API보다 효율이 더 좋다.

### 2.1 장점

- **초기 진입 비용이 낮다.** 계정과 결제만 있으면 바로 시작할 수 있다.
- **고정 좌석비 구조**라서 저빈도 사용자에게는 예산 예측이 쉽다.
- **대화형 UX가 좋다.** 사람이 아이디어를 밀고 당기며 쓰기에 편하다.
- **프롬프트/코드/DB/로그 인프라가 거의 필요 없다.**
- **작가 1인 혹은 소규모 팀의 수작업 편집 루프**에는 속도가 빠르다.

### 2.2 구독형이 맞는 작업

- 작품 아이디어 탐색
- 제목/로그라인/캐치카피 초안
- 장면 대안 3~5개 빠르게 뽑기
- 기존 원고 문장 다듬기
- 인간 편집자가 직접 읽고 선택하는 브레인스토밍
- 초기에 "정말 이 시스템이 필요한가"를 검증하는 MVP 단계

### 2.3 구독형이 특히 유리한 조건

- 하루 호출량이 낮다
- 산출물을 기계가 아니라 사람이 최종 정리한다
- 로그/DB/재현성이 필수는 아니다
- 실패한 출력의 복구 비용이 낮다
- 출력 포맷이 자유문 텍스트 위주다

요약하면, **구독형은 사람의 생산성을 높이는 도구**로 매우 효율적이다.

---

## 3. 그런데 왜 글도비는 API 축이 필요한가

여기부터가 핵심이다. 아래 판단은 워크스페이스 구조와 외부 공식 문서를 함께 본 **추론**이다.

### 3.1 글도비의 본체는 "대화"가 아니라 "런"이다

구독형 앱은 기본적으로 사람이 UI에서 대화한다. 반면 글도비는:

- 실행 키를 받아
- 특정 Stage를 돌리고
- 산출물을 저장하고
- 결과를 DB와 로그에 남기고
- 실패 시 재시도/분석/감리를 거친다

이 운영 단위는 `chat session`이 아니라 **`run/job`** 이다.  
`modules/api/bridge_server.py`의 `/run`과 `ProcessRunner` 구조는 이 사실을 그대로 보여 준다.

이 지점에서 이미 API 적합성이 커진다. 왜냐하면 시스템은 대화보다 **호출 가능성, 자동 실행, 결과 수집**을 요구하기 때문이다.

### 3.2 글도비는 구조화된 산출물과 권한 체계를 요구한다

글도비는 Director, Stage, quality dashboard, authoritative sink 개념을 갖는다.  
이 말은 곧:

- 결과가 저장되어야 하고
- 어떤 경로로 생성됐는지 추적 가능해야 하며
- 다음 Stage가 읽을 수 있게 형식화되어야 하고
- 실패 시 같은 조건으로 다시 돌릴 수 있어야 한다는 뜻이다.

구독형 UI는 이런 흐름을 사람이 수동으로 메꿔야 한다.  
반면 API는 호출 단위로 입력/출력/메타데이터를 붙일 수 있어서 시스템 계약을 세우기 쉽다.

### 3.3 글도비는 관측성과 비용 계측을 이미 가치로 삼고 있다

`DBManager`에는 비용과 운영 이벤트를 저장하는 함수가 있고, `bridge_server`는 `/quality/dashboard`와 cost summary를 노출한다.  
즉 글도비는 "글이 나왔느냐"만 보는 것이 아니라:

- 어떤 비용으로
- 어떤 Stage에서
- 어떤 품질 경로를 거쳐
- 어떤 실패/재시도가 있었는지

를 함께 본다.

이건 API 쪽이 훨씬 잘 맞는다.  
구독형은 좌석 기반 사용에는 편하지만, **호출 단위 비용/품질/재시도 경로를 시스템적으로 계측하는 데는 불리하다.**

### 3.4 글도비는 멀티 프로바이더 / 멀티 모델 운영을 염두에 둔다

`config/models.yaml`은 Gemini, Anthropic, OpenAI, Vertex를 provider 레벨에서 바꿔 끼울 수 있게 설계되어 있다.  
이 구조는 특정 웹앱 한 곳에서 사람이 쓰는 운영보다, **백엔드가 모델을 라우팅하고 폴백을 거는 운영**에 가깝다.

즉 글도비는 처음부터:

- 모델 교체
- provider fallback
- 성격 다른 모델 배정
- 비용/속도/품질 균형

을 시스템 레벨에서 다루려는 구조다. 이 역시 API 친화적이다.

### 3.5 배치, 비동기, 가격 최적화는 API에서만 열린다

외부 공식 문서가 말하는 것도 같다.

- OpenAI는 ChatGPT Plus를 웹앱 구독으로 설명하면서, **API 사용은 별도 과금**이라고 명시한다.
- OpenAI API Pricing은 **Batch API 50% 절감**, Priority processing, Flex processing 같은 운영 옵션을 제공한다.
- Google Gemini API는 **Google Cloud project / billing / collaborator control**과 연결되어 있고, Batch API는 **표준 interactive API 비용의 50%**라고 밝힌다.
- Google AI Pro는 **개인 Google Account로 가입하는 멤버십**이며, Gemini app Pro/Ultra 접근 같은 사용자용 혜택 중심이다.

즉 벤더들도 제품을 이렇게 나눈다:

- **구독형**: 사람 1명이 앱 안에서 쓰는 대화형 상품
- **API**: 프로젝트, 권한, 비용, 배치, 프로그램 통합을 전제로 한 시스템용 상품

글도비는 후자에 더 가깝다.

---

## 4. API가 주는 실질 효용

### 4.1 자동화

- Stage 단위 자동 실행
- 다회차/다후보 병렬 생성
- 재실행과 실패 복구
- 후처리/검증 파이프 연결

### 4.2 재현성

- 같은 입력으로 같은 파이프라인을 다시 돌릴 수 있다
- 실행 단위 로그를 남길 수 있다
- run 단위 비교가 가능하다

### 4.3 구조화

- JSON, DB row, audit log, summary 등 기계가 읽는 출력이 가능하다
- 다음 Stage에 계약된 형태로 넘길 수 있다

### 4.4 운영 가시성

- cost summary
- quality dashboard
- failure analyzer
- control-plane provenance

### 4.5 조직적 사용

- 한 명의 "대화창 사용자"가 아니라, 여러 역할과 프로세스가 같은 시스템을 공유할 수 있다
- 사람이 바뀌어도 파이프라인 자체는 남는다

### 4.6 스케일 경제

- 대량 평가/백필/후처리에는 배치 API가 더 유리하다
- 구독형은 사람의 시간을 절약하지만, API는 시스템의 시간을 절약한다

핵심 문장으로 줄이면 이렇다.

> 구독형은 `사람 1명의 사고 확장`에 강하고, API는 `반복 가능한 생산 공정`에 강하다.

---

## 5. 그렇다고 API가 무조건 정답은 아니다

글도비가 API 기반으로 가야 한다는 말은, API가 싸고 쉽다는 뜻이 아니다. 오히려 반대다.

### 5.1 API의 단점

- **엔지니어링 세금이 크다.**
  - 프롬프트 계약
  - 오류 처리
  - 재시도 로직
  - DB/로그 설계
  - 운영 UI
  - 회귀 테스트
- **비용이 가변적이다.**
  - 사용량이 늘면 바로 청구가 커진다
- **지연과 쿼터 문제가 생긴다.**
  - 로컬 문서 `docs/2026-04-03/0_0-stage34-ep2-focused-bounded-canary-r5-audit.md`는 Vertex AI API 지연이 10~40분 수준으로 발생해 카나리 검증이 막혔다고 기록한다.
- **멀티 프로젝트/멀티 키 운영도 별도 관리가 필요하다.**
  - `docs/2026-04-06/5arc-terminal1-provider-env-guard-survey.md`는 같은 프로세스 내 env bleed와 shared quota contention 리스크를 짚고 있다.
- **비용 기록도 시스템 설계에 따라 누락/집계 타이밍 이슈가 생긴다.**
  - `docs/2026-04-06/01_golden_stage2_lane3_db_residue.md`는 Arc 5에서 실제 LLM 비용은 있었지만 `cost_log` 집계는 완료 시점 이후라 반영되지 않았음을 보여 준다.

### 5.2 API가 오버엔지니어링이 되는 경우

- 작가 1명이 대부분 직접 쓰고
- 하루 산출량이 크지 않고
- 구조화된 저장/검증이 거의 필요 없고
- "좋은 문장 몇 개 빨리 얻기"가 본질일 때

이 경우에는 API 시스템을 유지하는 비용이, 실제 얻는 효용보다 커질 수 있다.

---

## 6. 그래서 "API로 안 가도 되는" 조건은 무엇인가

다음 조건을 받아들일 수 있다면, 글도비를 API 중심이 아닌 구독형 중심으로 재정의할 수 있다.

### 6.1 구독형 대체가 가능한 조건

- 글도비를 `생산 파이프라인`이 아니라 `작가 보조 툴`로 본다
- Stage 간 계약과 자동 handoff를 약하게 만든다
- DB/audit/log의 중요도를 낮춘다
- 사람이 직접 복붙/편집/선택하는 과정을 받아들인다
- 재현성보다 순간 생산성과 감각적 결과를 더 중시한다
- 운영 목표를 "한 사람이 더 잘 쓰게 돕기"로 좁힌다

### 6.2 그때 잃는 것

- 버튼 한 번으로 재실행되는 파이프라인
- provider routing / fallback / 자동 배치
- run 단위 비용/품질 계측
- 팀 단위 운영 일관성
- 후속 자동화 확장성

즉, **API를 버릴 수는 있지만, 그 대가로 글도비의 시스템성도 함께 버려야 한다.**

---

## 7. 글도비 기준 권장안: 혼합 운영

### 7.1 추천 구조

| 영역 | 권장 수단 | 이유 |
|---|---|---|
| 아이디어 발상, 로그라인, 장면 브레인스토밍 | 구독형 | 사람-대화 루프가 가장 빠름 |
| 문체 탐색, 대안 장면 실험 | 구독형 우선 | 실패 비용이 낮고 탐색성이 중요 |
| Stage 실행, 자동 handoff, 구조화 산출물 생성 | API | 시스템 계약이 필요 |
| quality/dashboard, cost, audit, recovery | API | 계측과 저장이 필요 |
| 대량 평가, 후처리, 회귀 점검 | API Batch | 비동기/대량 처리 효율 |
| 최종 인간 편집, 마감 직전 문장 polishing | 구독형 또는 로컬 툴 | 인간 판단 비중이 높음 |

### 7.2 실무 해석

- **탐색면**은 구독형으로 가볍게 돌려도 된다.
- **권한 있는 생산면**은 API에 남겨야 한다.
- 사람이 읽고 버리는 임시 결과는 구독형으로 충분하다.
- 다음 Stage가 읽고, DB가 저장하고, 감사 문서가 참조하는 결과는 API로 생성하는 편이 맞다.

이 구조는 비용도 줄인다.  
비싼 API 호출을 "권한 있는 산출물"에 집중하고, 사람의 사고 보조는 구독형 좌석으로 처리하면 된다.

---

## 8. 최종 판정

### 8.1 한 문장 판정

**글도비는 현재 정의를 유지하는 한 API 기반이 맞고, 구독형은 대체재가 아니라 보완재로 쓰는 것이 효율적이다.**

### 8.2 더 직설적으로 말하면

- "그냥 AI로 글을 쓰고 싶다"면 구독형으로도 충분하다.
- "글도비처럼 단계, 권한, 저장, 검증, 운영 UI가 있는 시스템을 돌리고 싶다"면 API가 필요하다.
- "API 없이도 되지 않나"라는 질문은 가능하다. 다만 그건 **글도비를 다른 제품으로 바꾸는 선택**이다.

### 8.3 최종 권고

1. **글도비의 backbone은 API로 유지한다.**
2. **브레인스토밍/탐색/인간 편집면은 구독형으로 분리한다.**
3. **앞으로의 비용 논쟁은 `API vs 구독형` 이분법이 아니라, `어떤 surface를 authoritative production line으로 둘 것인가` 기준으로 결정한다.**

---

## 9. 3-Pass Audit Summary

### Pass 1. Structure and Scope

- 문서 유형을 `효용 분석 보고서`로 고정했다.
- 범위는 시스템 적합성, 운영 효용, 권장안으로 제한했다.
- 정밀 TCO 계산, 구현 변경은 비범위로 분리했다.

### Pass 2. Evidence and Consistency

- 워크스페이스의 파이프라인/DB/control plane/비용 추적 근거를 직접 확인했다.
- 외부 사실은 OpenAI/Google 공식 문서만 사용했다.
- "API가 더 낫다"는 단정 대신, 어떤 목표에서 더 낫다고 명시했다.

### Pass 3. Execution and Readability

- 구독형이 맞는 경우와 API가 맞는 경우를 분리했다.
- 글도비에 대한 최종 권고를 `혼합 운영`으로 구체화했다.
- 다음 의사결정 기준을 `authoritative production surface`로 정리해 후속 운영 판단에 바로 쓸 수 있게 했다.

### Final Save Gate

- Estimated confidence: **95%**
- final save 적합 판정: **YES**

---

## External References

- OpenAI Help Center, What is ChatGPT Plus?: https://help.openai.com/en/articles/6950777-what-is-chatgpt-plus
- OpenAI API Pricing: https://openai.com/api/pricing/
- Google AI for Developers, Using Gemini API keys: https://ai.google.dev/gemini-api/docs/api-key
- Google AI for Developers, Gemini Batch API: https://ai.google.dev/gemini-api/docs/batch-api
- Google One Help, Get a Google AI Pro membership: https://support.google.com/googleone/answer/16476811?hl=en
