# TF-Work-Guard-Identity-SSOT-Plan

> 인코딩: UTF-8
> 작성일: 2026-03-10
> 상태: 실행 문서 / 2차 구현 완료 / calibration pending
> 감리: 3-pass 완료
> 확신도: 97%
> 목적: `investment` 기반 파이프라인을 유지하면서, 작품 고유 정체성을 `WorkGuard` 중심 SSOT로 끌어올리는 개선안 정의

---

## 0. 결론

장르를 계속 늘리는 것보다, 현재 시스템에서는 아래 전략이 더 현실적이다.

1. `base genre`는 계속 `investment`로 유지
2. `WorkGuard`를 `작품 정체성 SSOT`로 확장
3. `HUD + Registry + Summary Slot` 3층 기억 구조로 처리
4. `Retrieval + Summarization + Consumption`을 별도 고도화 축으로 본다
5. `StyleGuide`는 문체/말맛 보정 전용으로 유지

이 방식이 맞는 이유:

- 현재 파이프라인은 `investment` 경로에 가장 잘 최적화돼 있다.
- `entertainment / defense_business / ai_business`를 새 장르로 바로 넣으면 미지원 장르 폴백 리스크가 있다.
- 반면 작품별 핵심 자산/사업축/금지 템플릿은 장르보다 `작품 가드`가 더 잘 표현한다.
- 그리고 복잡한 작품 정보는 `HUD` 하나에 다 얹는 방식보다 `레지스트리 + 요약 슬롯`이 훨씬 확장성이 좋다.
- 마지막으로, 저장만 잘해도 소용없다. 실제 성능 병목은 `무엇을 꺼내오고, 얼마나 압축하고, 프롬프트에서 실제로 소비시키는가`에 있다.

### 0.1 현재 구현 상태

이번 1~2차 배치에서 이미 반영된 것:

- 데스크톱 설정의 `작가 지시사항` / `작품 가드 YAML`이 실제 `{project}/config/*.txt|yaml`로 write-through
- `WorkGuard`가 `work_identity / tracking_slots / registry_profiles`를 로드
- `get_v20_purism_prompt()`에 `작품 정체성 SSOT`, `우선 추적 슬롯`, `레지스트리 프로파일` 섹션 추가
- `mandatory_lexicon` 결핍 warning-only 검증 추가
- `select_retrieval_focus()`로 stage별 핵심 `tracking_slots / scene_engines / registry_profiles` 선택
- Stage 4 mandatory_context에 `[작품 추적 슬롯 요약]` 블록을 최상단 우선 주입
- Stage 4 state summary가 work focus 기준으로 먼저 정렬되고, slot summary는 `일반 섹션 -> 보호 섹션 -> 비상 trim` 순서로 보호
- Director `open_review`에 `work identity drift` 표면화 완료
- `run_deep_validation()`에 `mandatory_scene_engines` 누락 warning-only 검증 추가
- `run_deep_validation()`에 `forbidden_flattenings` runtime warning-only 검증 추가
- `role_fit_constraints` 기반 직업 적합성 common rule / 예외 / warning-only 검증 추가
- `mandatory_scene_engines / forbidden_flattenings / role_fit_constraints` warning payload에 calibration용 구조화 필드 추가

이번 배치에서 아직 남겨둔 것:

- `mandatory_scene_engines / forbidden_flattenings` heuristic 오탐 보정
- `role_fit_constraints` 표현 패턴/예외 규칙 고도화

---

## 1. 현재 시스템 현황

### 1.1 이미 있는 것

현재 `WorkGuard`는 이미 존재한다.

- 위치: `modules/core/genre_guards/work_guard.py`
- 체인: `GenreGuard -> WorkGuard -> StyleGuard`

현재 YAML로 다룰 수 있는 키:

- `extra_forbidden_terms`
- `extra_allowed_terms`
- `extra_mandatory_concepts`
- `extra_forbidden_patterns`
- `custom_rules`
- `character_constraints`

현재 역할:

- 작품별 금기어 추가
- 작품별 필수 개념 추가
- 작품 전용 규칙을 purism prompt에 주입
- 캐릭터 제약 일부를 warning-only로 검사

### 1.2 현재 부족한 것

지금 `WorkGuard`는 `금지/허용/캐릭터 제약` 중심이라, 아래 같은 `작품 정체성`을 SSOT로 잡기엔 부족하다.

- 이 작품의 핵심 사업축이 무엇인가
- 무엇을 자산으로 추적해야 하는가
- 어떤 템플릿으로 평탄화되면 안 되는가
- 어떤 갈등축이 빠지면 작품이 무너지는가
- 어떤 용어군은 반드시 살아 있어야 하는가
- 어떤 종류의 장면이 일정 간격으로 재등장해야 하는가

즉 지금은 `작품 금지 가드`는 되지만, `작품 정체성 가드`는 아직 약하다.

### 1.2A HUD 단독 접근의 한계

복잡한 작품은 `HUD`만으로 안정적으로 추적할 수 없다.

예:

- 무협 문파물: 문파 후배 10명 이상의 성장 단계
- 엔터 타이쿤물: 배우/연습생/제작진/포맷/IP의 동시 추적
- 방산 기업물: 결함선, 시험평가권, 공급망, 규격권의 병행 추적
- AI 사업물: 라이선스, 엔진 버전, 고객사, 감사 로그, 규격 전쟁

이걸 모두 HUD 필드로 밀어 넣으면:

- HUD가 비대해짐
- 프롬프트에 매번 전부 못 넣음
- 지금 중요한 정보와 장기 보존 정보가 섞여서 오히려 추적성이 떨어짐

판정:

- `HUD 확장만으로 해결`은 틀린 방향
- `작품별 레지스트리 + 현재 화 요약 슬롯`이 필요

### 1.2B 현재 코드에 이미 있는 레지스트리 표면

완전히 없는 개념은 아니다. 현재도 아래 저장소가 이미 있다.

- `WorldState`
  - `alive_npcs`, `active_plots`, `motivations`, `promises`, `cumulative_elapsed`
- `FactLedger`
  - `characters`, `numbers`, `items`, `locations`, `organizations`
- `StateTracker`
  - `npc_registry`, `entity_name_registry`, `financial_number_registry`, `item_state_registry`

즉 필요한 것은 `새 메모리 시스템 발명`이 아니라,
`작품별로 어떤 축을 어느 레지스트리에 넣고, 무엇을 요약 슬롯으로 뽑을지`를 고정하는 일이다.

### 1.2C 현재 코드에 이미 있는 retrieval/summary 표면

요약/선별 능력도 완전 빈 상태는 아니다.

- `WorldState.get_summary()`
- `FactLedger` 숫자 요약
- `StateTracker`의 다수 `get_*_summary()`
- `Stage4ContextBuilder`의 headroom + context budget + lookback digest
- `ChiefWriterContext`의 plot event / NPC last state 추출
- `Writer`의 relevant anchor 조회

즉 지금 부족한 것은:

- 저장소가 없는 것
- 요약기가 없는 것

이 아니라,

- 작품별로 무엇을 relevant하게 볼지의 기준
- 어떤 registry를 어느 stage에서 우선 소비할지의 계약
- 요약 결과를 실제 prompt 입력에서 잃지 않게 하는 소비 우선순위

이 3가지다.

### 1.3 현재 UI/설정 표면의 한계

관련 UI는 아주 얇게만 존재한다.

- 데스크톱 설정 탭에 `작품 가드 YAML` textarea가 있다.
- 하지만 구조화된 선택지(예: "지금 보강하시겠습니까?", "엔터 타이쿤형으로 강화", "방산 기업형으로 강화")는 없다.
- 현재 UI는 raw YAML 입력칸 1개뿐이다.

더 중요한 점:

- UI 문구는 `{project}/config/work_guard.yaml`에 저장되는 것처럼 보인다.
- 실제 구현은 `%LOCALAPPDATA%/Geuldobi/settings.json`에만 저장한다.
- 엔진이 읽는 실제 파일은 여전히 `{project}/config/work_guard.yaml`이다.

판정:

- 현재 UI는 `WorkGuard 보강 UI`가 아니라 `보여주기용 raw 설정칸`에 가깝다.
- 따라서 이번 개선은 `UI 확장`보다 `WorkGuard 스키마/소비 경로 확정`이 먼저다.

---

## 2. 왜 장르 확장보다 작품 가드가 맞는가

### 2.1 새 장르 추가의 비용

`entertainment / defense_business / ai_business`를 새 장르로 공식 편입하려면 아래를 같이 늘려야 한다.

- `GenreTypes`
- genre guard factory
- validation threshold profile
- genre laws / hints / style extractor 분기
- scoring / constitution / action/catharsis 피드백 분기
- e2e smoke / fixture / selected_genre 경로

즉 범위가 작지 않다.

### 2.2 작품 가드 확장의 장점

반면 `investment` 기반을 유지하고 `WorkGuard`만 두껍게 만들면:

- 기존 HUD / continuity / Stage 2~4 파이프라인을 그대로 활용
- 작품 고유성만 additive하게 올릴 수 있음
- `03/04/08` 같은 현재 investment-shell 작품과도 호환
- `09/10/11` 같은 더 개성 강한 BI 후보도 흡수 가능

판정:

- 단기: `investment + strong WorkGuard`
- 중장기: 필요시 일부 장르만 별도 승격

---

## 3. 목표 상태

`WorkGuard`를 아래 3계층으로 본다.

### 3.1 Tier A. 금지/제약

현재 이미 있는 역할.

- 금기어
- 금지 패턴
- 캐릭터 제약

### 3.2 Tier B. 작품 정체성

이번에 강화해야 하는 핵심.

- 핵심 사업축
- 핵심 자산 종류
- 주인공 edge
- 절대 빠지면 안 되는 갈등 엔진
- 평탄화 금지 템플릿

### 3.3 Tier C. 프롬프트/검증 소비 계약

`WorkGuard` 정보가 실제로 아래로 흘러가야 한다.

- Stage 2 Arc
- Stage 3 Blueprint
- Stage 4 CW retry
- Director advisory

즉 `YAML -> prompt -> advisory -> operator visibility`까지 이어지는 구조가 목표다.

### 3.4 Tier D. 기억 구조 설계

작품별 복잡성은 아래 3층으로 처리한다.

#### A. HUD

상위 지표만 둔다.

예:

- 문파 위상 / 자금 / 총 제자 수 / 핵심 전력 수
- 엔터 회사 현금 / 핵심 IP 수 / 데뷔조 상태 / 배우 라인 상태
- 방산 통제권 / 시험권 / 공급망 장악도
- AI 엔진 점유 / 라이선스 수 / 규격 장악도

#### B. Work Registry

작품별 개별 객체를 저장하는 실제 기억 저장소.

예:

- 문파 후배별 성장표
- 배우/연습생별 상태표
- 협력사/부품 라인별 통제 상태
- 고객사/라이선스/감사 로그 상태

#### C. Summary Slot

현재 화에 필요한 것만 압축해서 프롬프트에 준다.

예:

- "핵심 후배 3명"
- "이번 화와 직접 연결되는 배우 2명"
- "현재 시험평가권 충돌과 직접 연결되는 공급망 2개"
- "이번 계약과 직접 엮인 고객사 1개 + 라이선스 분쟁 1개"

원칙:

- 모든 것을 HUD에 넣지 않는다
- 모든 것을 매 화 프롬프트에 넣지 않는다
- Registry는 길게, Summary Slot은 짧게 유지한다

### 3.5 Tier E. Retrieval / Summarization / Consumption

복잡한 작품의 핵심 병목은 메모리 양이 아니라 메모리 지능이다.

따라서 아래 3축을 독립적으로 설계한다.

#### A. Retrieval

질문:

- 이번 화에 무엇이 정말 relevant한가?
- 후배 20명 중 지금 누구를 꺼내와야 하는가?
- 사업축 8개 중 이번 장면과 직접 연결되는 축은 무엇인가?

원칙:

- recency만으로 뽑지 않는다
- `tracking_slots`, `mandatory_scene_engines`, 현재 갈등축을 기준으로 뽑는다

#### B. Summarization

질문:

- 꺼내온 정보를 어떤 길이와 형식으로 압축할 것인가?

원칙:

- Stage 2는 구조적 요약
- Stage 3은 장면 설계용 요약
- Stage 4는 원고 직접 소비용 요약

즉 같은 registry라도 stage별 summary 포맷은 달라야 한다.

#### C. Consumption

질문:

- 요약이 실제 prompt에서 살아남는가?
- context budget trim에서 밀려나지 않는가?
- retry/advisory 경로로도 다시 들어가는가?

원칙:

- summary는 만들어 놓고 버리지 않는다
- mandatory slot과 advisory slot을 분리한다
- trim 시 `작품 정체성 slot`이 일반 배경 텍스트보다 먼저 남게 해야 한다

---

## 4. 제안 스키마

기존 키는 유지하고, 아래를 additive하게 붙인다.

```yaml
work_identity:
  work_type: "엔터 타이쿤 성장물"
  one_line_truth: "사람을 발굴하고 포지셔닝해 스타 IP 기업으로 키우는 이야기"
  protagonist_weapon:
    - "스타 감각"
    - "포지셔닝 판단"
    - "팬덤 접점 설계"
  business_axes:
    - "배우"
    - "연습생"
    - "아이돌"
    - "유튜버/스트리머"
    - "셰프/F&B"
    - "팬덤 플랫폼"
  control_axes:
    - "캐스팅 권한"
    - "데뷔조 설계"
    - "포맷 기획"
    - "브랜드화"
  mandatory_scene_engines:
    - "인재 발굴"
    - "포지셔닝 재배치"
    - "팬덤/시장 반응 확인"
    - "엔터 현장 의사결정"
  forbidden_flattenings:
    - "단순 M&A/주식 매매물처럼 흐르기"
    - "사람 대신 숫자만으로 승부 보기"
    - "엔터 현장성 없이 투자 용어만 반복"
  mandatory_lexicon:
    - "캐스팅"
    - "쇼케이스"
    - "팬덤"
    - "포맷"
    - "브랜드"
  tracking_slots:
    - "핵심 배우 라인"
    - "핵심 연습생 라인"
    - "주력 포맷/IP"
    - "외부 제작 파트너"
  registry_profiles:
    - name: "talent_registry"
      purpose: "배우/연습생/창작자 성장 상태 추적"
      required_fields: ["name", "tier", "current_position", "recent_growth", "risk"]
    - name: "ip_registry"
      purpose: "작품 포맷/IP 상태 추적"
      required_fields: ["name", "type", "status", "owner", "momentum"]
```

### 4.1 핵심 필드 의미

- `work_type`
  - 이 작품이 독자에게 어떻게 읽혀야 하는지
- `one_line_truth`
  - 이 작품을 한 문장으로 설명하는 정체성 SSOT
- `protagonist_weapon`
  - 주인공이 이기는 고유 무기
- `business_axes`
  - 작품이 다루는 핵심 사업군/자산군
- `control_axes`
  - 주인공이 장악해야 하는 권한 축
- `mandatory_scene_engines`
  - 일정 주기 재등장해야 하는 대표 장면 엔진
- `forbidden_flattenings`
  - investment 공용 템플릿으로 눌릴 때 막아야 하는 방향
- `mandatory_lexicon`
  - 빠지면 작품 맛이 약해지는 용어군
- `tracking_slots`
  - Stage 2~4에서 요약으로 유지해야 할 메모리 슬롯
- `registry_profiles`
  - HUD에 올리지 않을 세부 상태를 어떤 레지스트리 형태로 장기 저장할지 정의

### 4.2 예시: 문파물/기업물 공통 사고방식

무협 문파물 예시:

- HUD:
  - 문파 위상
  - 총 제자 수
  - 핵심 전력
- Registry:
  - 후배별 경지 / 무기 / 충성 / 최근 성장 / 병목
- Summary Slot:
  - 이번 화 핵심 후배 2~4명

엔터 타이쿤물 예시:

- HUD:
  - 현금 흐름
  - 핵심 IP 수
  - 데뷔조 상태
- Registry:
  - 배우/연습생별 성장 상태
  - 포맷/IP별 추진 상태
- Summary Slot:
  - 이번 화 핵심 배우/연습생/포맷

### 4.3 Retrieval 규칙 예시

문파물:

- `tracking_slots`에 `핵심 후배 라인`, `문파 내부 서열`, `외부 적대 문파`가 있으면
- 현재 화가 수련/문파 운영 화인지 결전 화인지에 따라 retrieval 우선순위를 바꾼다

엔터 타이쿤물:

- `mandatory_scene_engines`가 `인재 발굴`, `포지셔닝`, `팬덤 반응`이면
- 현재 화가 오디션 화인지 계약 화인지에 따라
  - 배우 registry
  - 연습생 registry
  - 포맷/IP registry
  중 하나를 우선 가져온다

---

## 5. 소비 지점 설계

### 5.1 WorkGuard prompt 주입

현재 `custom_rules`처럼 prompt에 붙는 것에서 한 단계 확장한다.

추가 섹션 예:

- `[작품 정체성 핵심]`
- `[필수 사업축]`
- `[평탄화 금지]`
- `[반드시 기억할 추적 슬롯]`

### 5.2 Stage 2 / Stage 3

목표:

- Arc/Blueprint가 `generic investment loop`로 수렴하는 것을 방지

주입 예:

- 이 작품의 핵심 승리 방식
- 반드시 등장해야 하는 장면 엔진
- 숫자만이 아니라 어떤 자산/권한이 움직여야 하는지

### 5.3 Stage 4 CW retry

목표:

- CW가 투자물 공용 표현으로 회귀하는 것을 완화

주입 예:

- “이번 화가 작품 정체성보다 generic investment 문법으로 흐른 부분”
- “필수 lexicon/scene engine 누락”
- “사업축이 너무 숫자 설명으로만 처리된 부분”

### 5.4 Director advisory

하드 게이트가 아니라 advisory-only로 먼저 간다.

예:

- `work_identity_drift`
- `business_axis_missing`
- `flattened_to_generic_investment`

### 5.5 직업 적합성 common rule

`genre`와 별개로, 작품 전반에 깔리는 공통 규칙으로 둔다.

- 인물은 자신의 직업/역할/훈련 이력에 맞게 행동해야 한다
- 별도 빌드업 없이 직업 밖 전문 행동을 갑자기 수행하면 안 된다
- 전문성은 `이력`, `훈련`, `이중 커리어`, `위장 신분`, `사건 해금` 중 하나로 근거가 있어야 한다
- 예외는 작품별 `work_guard.yaml`에 명시한다

예:

- 은행원/PB가 사전 맥락 없이 아이돌 퍼포먼스/무대 연출 전문성을 보이면 이탈
- 셰프가 사전 근거 없이 법률/금융/군사 판단까지 자연스럽게 해버리면 이탈
- 장교/기사/무인이 별도 설정 없이 엔터/협상/회계까지 만능 수행하면 이탈

즉 `직업에 맞게 행동하라`는 common rule로 두고, 작품별 예외만 `WorkGuard`에 적는 구조가 맞다.

---

## 6. 작품별 예시

### 6.1 09 엔터 타이쿤형

핵심:

- 사람 발굴
- 포지셔닝
- 포맷/IP 확장

금지:

- 주식/인수합병 일변도
- 엔터 현장 없이 IR 언어만 반복

### 6.2 10 방산 기업형

핵심:

- 결함 판독
- 시험평가권
- 규격권
- 공급망 장악

금지:

- 일반 투자 협상물처럼 평탄화
- 기술 병목 없이 재무 숫자만 반복

### 6.3 11 AI 사업형

핵심:

- 추론 엔진 병목
- 라이선스
- 감사 로그/규격화
- 독점 구조

금지:

- 흔한 스타트업 투자유치물화
- compute/control/license 맥락 누락

---

## 7. 구현 우선순위

### P1. 문서/스키마 확장

- `work_guard.yaml` 확장 키 설계
- 예시 템플릿 3종 작성
- 기존 키와 역호환 유지

상태: 완료

### P2. Registry 프로파일 정의

- `tracking_slots`와 별개로 `registry_profiles` 표준 정의
- 작품별로 무엇을 HUD가 아닌 Registry에 둘지 템플릿화
- `WorldState / FactLedger / StateTracker` 중 어느 저장소를 우선 쓸지 매핑

### P3. Retrieval 우선순위 규칙 정의

- `tracking_slots` 기반 relevant selection 규칙
- `mandatory_scene_engines` 기반 scene-type selection 규칙
- stage별 registry retrieval contract 정의

상태: 1차 완료

### P4. Settings 저장 배선 복구

- 데스크톱 `workGuardYaml`을 실제 `{project}/config/work_guard.yaml`로 write-through
- `authorDirectives`도 `{project}/config/author_directives.txt`에 맞춰 저장
- `AppData settings.json`은 UI 상태 보존용으로만 사용

상태: 1차 완료

### P5. prompt 주입

- `get_v20_purism_prompt()`에 정체성 섹션 추가
- Stage 2/3 prompt에 요약 주입
- summary slot이 context trim에서 먼저 보존되도록 우선순위 정의

상태: 1차 완료

### P6. advisory 검증

- `run_deep_validation()`에 `mandatory_lexicon` 결핍
- `forbidden_flattenings` regex/pattern
- `mandatory_scene_engines` 부재를 warning-only로 추가

상태: lexicon + prompt-level advisory + runtime warning 1차 완료 / role-fit pending

### P7. Director 표면화

- `open_review`에 `work identity drift` 문구 추가
- score schema 확대는 나중에 판단

상태: 1차 완료

### P8. 직업 적합성 common rule

- `role_fit_constraints` 또는 동등 키 설계
- common rule: `직업/역할에 맞게 행동하라`
- work-level exception: 이중 커리어/과거 훈련/위장 신분 등 예외 허용 조건만 명시
- Stage 3 blueprint advisory + Stage 4 CW/Director advisory-only로 먼저 연결

상태: 1차 완료 / pattern refinement pending

---

## 8. 금지 사항

- 새 장르 3개를 먼저 늘리기
- `investment` 경로를 바로 버리기
- `WorkGuard`를 hard gate로 바로 승격하기
- 사업축/정체성 규칙을 Python 단독 REJECT로 처리하기
- 현재 raw textarea UI만 믿고 `work_guard.yaml`이 실제로 저장된다고 가정하기
- 작품별 세부 상태를 전부 HUD에 억지로 집어넣기
- Registry를 많이 쌓기만 하고 retrieval/summary/consumption 계약 없이 방치하기

대원칙:

- Python은 수집/경고
- 최종 판단은 Director/LLM

---

## 9. 최종 판단

이 방향은 현실적이고 ROI도 높다.

이유:

- 현재 시스템 위에 additive하게 얹힌다
- `03/04/08` 레거시와 `09/10/11` 승격 후보를 모두 수용한다
- 장르 확장보다 범위가 작고 효과가 크다
- 작품 고유성을 `genre`가 아니라 `work identity`로 고정할 수 있다

한 줄 결론:

`다양한 기업/재벌/사업물을 똑똑하게 처리하려면, 새 장르를 계속 늘리기보다 investment 셸 위에 WorkGuard를 작품 정체성 SSOT로 키우는 쪽이 맞다.`
