# TF-DB-Retrieval-Consumption-Intelligence-Plan

> 인코딩: UTF-8
> 작성일: 2026-03-10
> 상태: 실행 문서 (P5 retrieval observability + P6 semantic slice 반영)
> 감리: 3-pass 완료
> 확신도: 97%
> 목적: 이미 구축된 DB/anchor/vector/state 계층을 `주요 에이전트가 실제로 더 똑똑하게 먹는 구조`로 재정렬하는 계획 정의

---

## 0. 결론

지금 글도비의 문제는 `DB가 없다`가 아니다.

문제는 아래다.

1. `저장`은 꽤 잘 되어 있다.
2. `요약`도 일부 잘 되어 있다.
3. 하지만 `무엇을 지금 꺼내와야 하는가`, `얼마나 압축할 것인가`, `에이전트가 실제로 그걸 소비하는가`가 Stage별로 비대칭이다.

판정:

- `GO`
- ROI 높음
- 새 장르 추가보다 우선순위 높음
- 방향은 `LLM이 직접 DB를 뒤지는 구조`보다 `얇은 Python 기본 주입 + LLM-guided read-only broker`가 맞다

---

## 1. 전수 조사 요약

### 1.1 저장 계층은 이미 충분히 있다

현재 이미 누적되는 주요 저장 표면:

- `anchors`: [db_manager.py](C:/Users/User/Desktop/글도비/modules/core/db_manager.py)
- `world_state`: [world_state.py](C:/Users/User/Desktop/글도비/modules/core/world_state.py)
- `fact_ledger`: [fact_ledger.py](C:/Users/User/Desktop/글도비/modules/core/fact_ledger.py)
- `state_tracker` 다수 summary: [state_tracker.py](C:/Users/User/Desktop/글도비/modules/domain/agents/state_tracker.py)
- `stage_attempts`: [db_manager.py](C:/Users/User/Desktop/글도비/modules/core/db_manager.py)
- `quality_dashboard`: [quality_dashboard.py](C:/Users/User/Desktop/글도비/modules/core/quality_dashboard.py)
- `vec_memory` dense/hybrid retrieval: [vec_memory.py](C:/Users/User/Desktop/글도비/modules/core/vec_memory.py)

즉 저장소 자체는 이미 `장기 연재용 기억 저장소` 역할을 할 수 있다.

### 1.2 Stage 2는 부분적으로만 똑똑하다

현재 Stage 2는:

- `context_advisor.plan_stage2_retrieval()` 경로가 켜져 있으면 slot 기반 retrieval을 탄다. [stage2_preflight.py](C:/Users/User/Desktop/글도비/modules/core/stage2_preflight.py)
- 꺼져 있거나 실패하면 `block_theme` 하나로 `retrieve_high_res_context()`를 탄다. [stage2_preflight.py](C:/Users/User/Desktop/글도비/modules/core/stage2_preflight.py)
- 여기에 `FactLedger 핵심 수치`만 얹는다. [stage2_preflight.py](C:/Users/User/Desktop/글도비/modules/core/stage2_preflight.py)
- 이번 배치부터 `work_guard.select_retrieval_focus()` 결과를 advisor에 넘기고, `[작품 추적 슬롯 요약]`을 `vector_context` 상단에 같이 주입한다. [stage2_preflight.py](C:/Users/User/Desktop/글도비/modules/core/stage2_preflight.py) [context_advisor.py](C:/Users/User/Desktop/글도비/modules/core/context_advisor.py)

평가:

- `기억 검색`은 있다
- `작품별 tracking_slots / registry_profiles`와의 결합도 1차 들어갔다
- 다만 fallback은 아직 `block_theme` 중심이라 더 정교한 broker fallback은 남아 있다

### 1.3 Stage 3는 Stage 4보다 약하다

현재 Stage 3는:

- optional `smart retrieval`이 있으면 multi-query를 통해 semantic context를 만든다. [stage3_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage3_orchestrator.py)
- static advisory로 `WorldState`, `StyleGuide`, `FactLedger`, `Treatment Block`을 붙인다. [stage3_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage3_orchestrator.py)
- 이번 배치부터 `work_focus`를 advisor에 같이 넘기고, `[작품 추적 슬롯 요약]`을 `semantic_context` 최상단에 고정한다. [stage3_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage3_orchestrator.py) [context_advisor.py](C:/Users/User/Desktop/글도비/modules/core/context_advisor.py)

평가:

- `semantic_context`는 존재하고 work-aware summary도 1차 들어갔다
- 그러나 semantic query slice나 coverage loop는 아직 Stage 4보다 약하다
- 즉 `Stage 4 > Stage 3 > Stage 2` 구조는 유지되지만 차이는 줄어들었다

### 1.4 Stage 4는 현재 가장 강하다

현재 Stage 4는:

- `select_retrieval_focus()`로 작품별 focus를 고른다. [work_guard.py](C:/Users/User/Desktop/글도비/modules/core/genre_guards/work_guard.py)
- `mandatory_context` 상단에 `[작품 추적 슬롯 요약]`을 넣는다. [stage4_context_builder.py](C:/Users/User/Desktop/글도비/modules/core/stage4_context_builder.py)
- `WorldState`, `FactLedger`, `StateTracker`, `Timeline`, `Vector retrieval`, `Treatment Block`, `Continuity Packet`을 함께 조립한다. [stage4_context_builder.py](C:/Users/User/Desktop/글도비/modules/core/stage4_context_builder.py)
- trim도 이제 일반 섹션보다 slot summary를 늦게 줄이게 되어 있다. [stage4_context_builder.py](C:/Users/User/Desktop/글도비/modules/core/stage4_context_builder.py)
- Director도 work review advisory를 받는다. [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py)

평가:

- `현재 retrieval intelligence의 중심축은 Stage 4`
- 여기까지는 꽤 괜찮다
- 하지만 Stage 2/3/Director retry와 아직 완전히 대칭은 아니다

### 1.5 주요 에이전트는 직접 DB를 질의하지 않는다

`Chief Writer`, `Director`, `Analyst`가 직접 DB를 두드리는 구조는 아니다.

실제 구조는:

- Python이 DB/anchor/vector/state에서 꺼낸다
- 요약/정렬/절삭한다
- `mandatory_context`, `semantic_context`, `director_feedback`로 LLM에 넣는다

평가:

- 이 구조 자체는 맞다
- 다만 `Python만으로 의미 질의를 다 해석한다`는 발상은 과하다
- Python은 `후보 추출 / 근거 반환 / 안전한 축소 질의`를 맡고, 의미 판정은 LLM이 맡는 쪽이 맞다
- 지금은 그 broker 지능이 Stage별로 uneven하다

---

## 2. 핵심 문제 정의

### 2.1 지금 병목은 저장이 아니라 retrieval/consumption이다

현 상태를 한 문장으로 줄이면:

`기억은 꽤 저장되는데, 지금 필요한 기억을 작품별로 정확히 꺼내오는 지능이 아직 Stage마다 다르다.`

### 2.2 현재 비효율

1. 같은 저장소가 있어도 Stage 2/3/4에서 retrieval 방식이 다르다
2. `tracking_slots`는 생겼는데 Stage 4에서 가장 잘 쓰이고, Stage 2/3는 아직 얕다
3. `registry_profiles`는 선언되기 시작했지만, 아직 진짜 DB-level selector로 매핑되지 않았다
4. `reference_anchor`는 keyword overlap 기반이라 작품 가드/registry-aware가 아니다. [reference_anchor.py](C:/Users/User/Desktop/글도비/modules/core/reference_anchor.py)
5. LLM은 주어진 것만 먹고, “이 정보 더 필요함”을 다시 retrieval로 되돌리는 후속 루프가 없다
6. `누가 주인공과 소꿉친구였나` 같은 의미 질의는 Python-only summary/path로는 약하다

### 2.3 따라서 목표는 “DB를 더 쌓기”가 아니다

목표는 아래 3개다.

1. `Retrieval`을 더 똑똑하게
2. `Summary Slot`을 더 relevant하게
3. `Consumption`이 실제 prompt에서 안 묻히게

### 2.4 Python-only는 한계가 있다

아래 같은 질의는 Python-only로 완전히 해결하기 어렵다.

- `누가 주인공과 소꿉친구였지?`
- `가장 가족 같은 조력자는 누구였지?`
- `사실상 라이벌 구도였던 인물이 누구지?`

이유:

- 명시 관계 필드가 없는 경우가 많다
- 표현이 `소꿉친구`, `어릴 적 동네 친구`, `초등학교 때부터 봐 온 사이`, `옛날부터 붙어 다녔다`처럼 다양하다
- 일부는 관계 taxonomy보다 서술 뉘앙스에 가깝다

따라서 정답은 아래다.

- Python: 후보군 추출, 근거 snippet 반환, read-only slice 제공
- LLM: 질문 의도 해석, 후보 비교, 최종 의미 판정

즉 `Python-only retrieval intelligence`가 아니라 `LLM-guided retrieval broker`가 목표여야 한다.

---

## 3. 실제 갭

### G1. unified retrieval contract가 부족하다

현재:

- Stage 2는 Stage 2 나름
- Stage 3는 Stage 3 나름
- Stage 4는 WorkGuard-aware

필요한 것:

- 공통 `retrieval intent` 계약
- `stage / work_identity / tracking_slots / scene_engines / registry_profiles / current_ep / arc context`를 공용 입력으로 받는 구조

### G2. registry-aware selector가 부족하다

현재:

- `WorldState.get_summary()`, `FactLedger.to_summary()`, `StateTracker.get_all_summaries()`는 있다
- 하지만 `tracking_slots=핵심 배우 라인`이면 정확히 어떤 state summary와 registry 조각을 우선 가져와야 하는지 공통 매핑이 없다

필요한 것:

- `tracking_slot -> registry source -> summary template` 매핑

예:

- `핵심 배우 라인` -> `talent_registry`, NPC relation, casting/fandom 관련 상태
- `시험평가권` -> defect registry, org registry, 관계 변화, commitment
- `추론 엔진 라이선스` -> numbers, organizations, known_attrs, promises

### G3. coverage loop가 없다

현재:

- retrieval을 한 번 조립하고 끝

부족한 것:

- 조립한 뒤 `mandatory_scene_engines / tracking_slots / role_fit`가 실제로 충분히 커버됐는지 검사
- 부족하면 targeted addendum을 한 번 더 붙이는 후속 retrieval

### G4. Stage 3 retrieval이 Stage 4보다 약하다

현재:

- Stage 3는 static advisory + optional SC
- 작품 정체성 SSOT와의 결합이 Stage 4보다 약하다

필요한 것:

- Blueprint도 `work-aware retrieval`로 끌어올리기
- 지금 Arc/Block에서 반드시 살아야 할 슬롯을 더 앞단에서 보장

### G5. observability는 생겼지만 retrieval 품질 계측은 부족하다

현재:

- `quality_dashboard`, `soft_failure`, `stage_attempts`, `Calibration Desk`는 있다

부족한 것:

- 어떤 retrieval slot이 실제로 prompt에 들어갔는지
- 어떤 slot이 trim에서 잘렸는지
- 어떤 slot이 Director/CW open_review에서 실제로 문제로 지적됐는지

즉 `retrieval effectiveness` 자체의 대시보드가 필요하다

---

## 4. 실행 방향

### P1. LLM-guided RetrievalBroker/Contract 통일

우선순위: 높음
상태: `3차 Director 확장 완료`

목표:

- Stage 2/3/4가 공통 retrieval contract를 쓰게 한다
- `work_guard.select_retrieval_focus()` 결과를 모든 stage가 같은 형식으로 받게 한다
- 필요 시 LLM이 `추가로 무엇이 필요한지` 좁게 요청하고, broker가 read-only slice를 반환하게 한다

후보 파일:

- [work_guard.py](C:/Users/User/Desktop/글도비/modules/core/genre_guards/work_guard.py)
- [stage2_preflight.py](C:/Users/User/Desktop/글도비/modules/core/stage2_preflight.py)
- [stage3_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage3_orchestrator.py)
- [stage4_context_builder.py](C:/Users/User/Desktop/글도비/modules/core/stage4_context_builder.py)

핵심:

- Stage 2/3에도 `tracking_slots / mandatory_scene_engines / registry_profiles`를 동일 semantics로 전달
- fallback도 `block_theme` 하나가 아니라 `work-aware query set`으로 바꾼다
- 자유 질의/생 SQL은 금지하고, broker 함수 집합만 허용한다
- 현재 1차 구현으로 [semantic_query_broker.py](C:/Users/User/Desktop/글도비/modules/core/semantic_query_broker.py)가 추가됐고, Stage 4는 관계 의미 질의를 source-backed read-only slice로 소비한다
- 현재 2차 구현으로 [context_advisor.py](C:/Users/User/Desktop/글도비/modules/core/context_advisor.py), [stage2_preflight.py](C:/Users/User/Desktop/글도비/modules/core/stage2_preflight.py), [stage3_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage3_orchestrator.py)가 `work_focus -> retrieval slot -> prompt summary` 계약을 공유한다
- 현재 3차 구현으로 relation-heavy slot은 `DB_NPC_RELATIONSHIP`까지 분기하고, Stage 2/3 summary와 Director memory context에도 semantic relation slice가 직접 주입된다

### P2. Registry-aware mapping 추가

우선순위: 높음
상태: `2차 일부 완료`

목표:

- `tracking_slot`을 실제 summary source와 연결

예시:

- `talent/casting/fandom` -> `npc_personality`, `relationship_changes`, `companion`, `known_attrs`, `organizations`
- `capital/license/spec/supply` -> `numbers`, `commitment`, `organizations`, `resolved_plots`
- `disciple growth` -> `protagonist_skills`, `npc_personality`, `relationship_changes`, `time_timeline`

핵심:

- `tracking_slots`가 선언적 문구에만 머무르지 않고 retrieval selector로 바뀌어야 한다
- 현재 1차 구현에선 `배우/인재/관계/제자/팬덤` 계열 slot은 `DB_NPC_HISTORY`, 나머지는 `VEC_MEMORY`로 보내는 휴리스틱 매핑이 들어갔다
- 현재 2차 구현에선 `소꿉친구/라이벌/멘토/은인/관계선/인맥` 같은 relation-heavy slot은 `DB_NPC_RELATIONSHIP`로 별도 분기한다

### P2A. 수동 규칙집/regex/taxonomy 강화

우선순위: 높음
상태: `1차 일부 완료`

목표:

- 애매한 의미 질의를 broker가 받아줄 수 있게 `수동 규칙집`을 만든다

필수 구성:

- `relation taxonomy`
  - 예: `소꿉친구`, `가족 같은 사이`, `라이벌`, `은인`, `보호 대상`
- `alias/synonym map`
  - 예: `소꿉친구 = 어린 시절 친구 / 동네 친구 / 어릴 때부터 함께`
- `manual regex/pattern set`
  - 이름 근접 출현
  - 관계 표현 근접 출현
  - 회상/소개 문장 패턴
- `source-backed answer`
  - 후보별 근거 ep / anchor / snippet / registry source 첨부

주의:

- 이 부분은 generic embedding만 믿고 넘기면 안 된다
- Python regex도 얕게가 아니라, 작품 도메인용 수동 규칙집 수준으로 만들어야 한다
- 현재 1차 구현에는 `소꿉친구 / 라이벌 / 멘토 / 조력자 / 은인 / 가족 같은 인물` taxonomy와 alias/pattern 세트가 포함된다

### P3. Coverage loop 도입

우선순위: 중간

목표:

- 첫 조립 후 `coverage check`
- 부족한 slot/scene_engine에 대해서만 `추가 retrieval` 1회

형태:

- warning-only
- non-blocking
- stage4 먼저

### P4. Director/CW consumption 고도화

우선순위: 중간

목표:

- `mandatory_context`에 들어갔다고 끝내지 말고
- Director/CW가 실제로 주의해야 할 `work drift`를 더 명시적으로 소비하게

형태:

- Director open_review 보조
- CW retry advisory 보조
- hard gate 금지

### P5. Retrieval observability

우선순위: 중간
상태: `Stage 2-3-4-Director retrieval observation 반영`

목표:

- `어떤 slot이 선택됐는지`
- `어떤 slot이 trim됐는지`
- `어떤 slot이 실제 경고/오류와 상관이 있었는지`

이를 `quality_dashboard`나 별도 sidecar로 집계

---

## 5. 추천 구현 순서

### 5.1 현재 구현 반영 (3차 완료)

이번 배치에서 실제로 반영된 것:

1. [semantic_query_broker.py](C:/Users/User/Desktop/글도비/modules/core/semantic_query_broker.py)
   - protagonist 중심 read-only 관계 broker
   - `WorldState / FactLedger / DB relationship edge/history / StateTracker` 근거 조합
   - `source-backed answer` 반환
2. [stage4_context_builder.py](C:/Users/User/Desktop/글도비/modules/core/stage4_context_builder.py)
   - `[작품 추적 슬롯 요약]` 내부에 `[관계 의미 질의]` slice 주입
   - explicit relation intent가 잡히거나 relation-heavy focus일 때만 작동
3. [context_advisor.py](C:/Users/User/Desktop/글도비/modules/core/context_advisor.py)
   - `work_focus`를 Stage 2/3 retrieval slot으로 변환
   - `tracking_slots / mandatory_scene_engines / registry_profiles`를 공통 category로 생성
   - 사람형 slot은 `DB_NPC_HISTORY`, relation-heavy slot은 `DB_NPC_RELATIONSHIP`, 나머지는 `VEC_MEMORY`로 2차 매핑
4. [stage2_preflight.py](C:/Users/User/Desktop/글도비/modules/core/stage2_preflight.py)
   - `work_focus`를 advisor에 전달
   - `[작품 추적 슬롯 요약]`을 `vector_context` 상단에 주입
   - relation-heavy focus면 `[관계 의미 질의]` slice도 같이 주입
   - `DB_NPC_RELATIONSHIP` source를 read-only relationship history로 실행
5. [stage3_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage3_orchestrator.py)
   - `work_focus`를 advisor에 전달
   - `[작품 추적 슬롯 요약]`을 `semantic_context` 최상단에 주입
   - relation-heavy focus면 `[관계 의미 질의]` slice도 같이 주입
   - `DB_NPC_RELATIONSHIP` source를 read-only relationship history로 실행
6. 테스트
   - [test_semantic_query_broker.py](C:/Users/User/Desktop/글도비/tests/test_semantic_query_broker.py)
   - [test_stage4_context_builder.py](C:/Users/User/Desktop/글도비/tests/test_stage4_context_builder.py)
   - [test_context_advisor.py](C:/Users/User/Desktop/글도비/tests/test_context_advisor.py)
   - [test_stage2_preflight.py](C:/Users/User/Desktop/글도비/tests/test_stage2_preflight.py)
   - [test_stage3_orchestrator.py](C:/Users/User/Desktop/글도비/tests/test_stage3_orchestrator.py)

현재 기준선:

- 타깃 회귀 `176 passed`
- 전체 `python -m pytest tests/ -q` -> `3881 passed, 16 skipped, 1 warning`
- `python -m pytest tests/ --collect-only -q` -> `3897 collected`

가장 ROI 높은 순서:

1. `tracking_slot -> registry source` 매핑표를 slot 범주별로 더 정교화
2. `semantic query slice`를 Director까지 확장
3. `Stage 4 coverage loop` warning-only 도입
4. `retrieval effectiveness` 로깅/대시보드 추가
5. 그 뒤에야 CW/Director advisory 승격

### P6. Semantic query slice 도입

우선순위: 중간
상태: `Stage 4 완료 / Stage 2-3-Director relation slice 반영`

목표:

- 아래 같은 질의를 broker 함수로 처리

예:

- `get_relationship_candidates(protagonist, relation_hint="소꿉친구")`
- `get_entity_history(name, lookback=30)`
- `get_registry_slice(profile_name, focus_terms)`
- `get_numbers(keys=[...])`
- `get_recent_related_events(query, lookback=20)`

제약:

- read-only
- schema-fixed
- source-backed
- 호출 횟수 제한
- SQL 문자열 직접 생성 금지
- 현재는 `관계 의미 질의`가 Stage 4, Stage 2/3, Director memory context까지 들어가 있고, `work_focus summary + relation slice + relationship db source`가 같은 contract로 묶이기 시작했다

---

## 6. 하지 말아야 할 것

1. `LLM이 직접 DB를 질의하게 만들기`
   - 과하고 통제 어렵다

2. `Python-only가 의미 질의까지 다 해결한다고 믿기`
   - 관계/회상/뉘앙스 질의는 한계가 분명하다

3. `전체 원고 풀컨텍스트만 계속 늘리기`
   - retrieval intelligence 문제를 가린다

4. `새 장르 대거 추가`
   - 지금 병목과 직접 연결되지 않는다

5. `바로 hard gate`
   - retrieval 오탐이 아직 충분히 교정되지 않았다

---

## 7. 최종 판정

이 주제는 `당장 들어갈 가치가 크다`.

이유:

- 이미 있는 DB/anchor/state 자산을 더 잘 쓰는 작업이다
- 새 대형 아키텍처보다 ROI가 높다
- `09/10/11` 같은 더 개성 강한 작품을 `investment shell` 안에서도 덜 평탄화하게 만들 수 있다
- 장기적으로는 `HUD 확장`보다 훨씬 건강한 방향이다

현재 최선의 한 줄 요약:

`글도비는 DB를 못 쓰는 시스템이 아니라, Stage 4만 상대적으로 잘 쓰고 있다. 다음 단계는 저장 확장이 아니라, Python 후보 추출 + LLM 의미 판정이 결합된 retrieval broker를 Stage 2/3/Director까지 끌어올리는 것이다.`
