# Gemini 컨텍스트 윈도우 활용 감사

> 작성: 2026-03-10
> 상태: 감리 완료 (3-pass, 실행 문서형)
> 기준: 현재 작업 트리 기준 코드 감리. 코드 수정은 수행하지 않음.
> 범위: Stage 0, Stage 2, Stage 3, Stage 4의 LLM 입력 경로, 하드코딩 절삭, 컨텍스트 예산, 캐시 경로
> 확신도: 95%

---

## 결론

- **가장 확실한 병목은 Stage 2 Director Arc 선택부**다. `modules/domain/agents/director_ensemble.py`에서 `block_summary`, `prev_arc_context`, `constraint_block`, `advisory`가 고정 절삭된다.
- **Stage 0은 구조적으로 적은 문맥을 쓰는 편이지만, 그 안에서도 불필요한 절삭이 명확히 존재**한다. `concept[:500]`, `raw_drafts[:3]`, `content[:4000]`, `content[:6000]`가 대표적이다.
- **Stage 3과 Stage 4는 이미 대형 컨텍스트 경로와 캐시 경로를 갖고 있다.** 따라서 이 둘의 핵심 과제는 "더 많이 넣기"보다 "빠진 데이터를 올바른 위치에 배선하기"다.
- 기존 문서에 있던 `실측 9KB`, `315KB`, `99.6% 활용` 같은 수치는 최신 아티팩트에서 호출 단위로 재검증되지 않아, 이번 실행 문서에서는 **코드상 확정 가능한 사실만 유지**했다.

---

## Pass 1 - 기준선 확정

### 런타임 예산 SSOT

| 항목 | 값 | 근거 |
|---|---:|---|
| `context.max_context_chars` | 1,000,000 | `config/settings/validation.yaml:75` |
| `context.mandatory_context_max` | 400,000 | `config/settings/validation.yaml:76` |
| `context.director_mandatory_max` | 400,000 | `config/settings/validation.yaml:77` |
| `context.lookback_excerpt_chars` | 5,000 | `config/settings/validation.yaml:78` |
| `context.lookback_total_chars` | 40,000 | `config/settings/validation.yaml:79` |
| `context.vector_max_results_s4` | 50 | `config/settings/validation.yaml:80` |
| `context.vector_max_results_s2` | 40 | `config/settings/validation.yaml:81` |
| `context.canonical_facts_budget` | 13,000 | `config/settings/validation.yaml:83` |
| `context.timeline_budget` | 3,000 | `config/settings/validation.yaml:84` |
| Context cache 생성 최소 길이 | 50,000자 | `modules/domain/agents/base_agent.py:1596-1645` |

### 해석

- 예산 상한은 이미 충분히 크다.
- 따라서 현재 문제는 "모델 창이 작다"가 아니라 **큰 창을 써야 할 지점에서 아직 작은 창 시대의 절삭 코드가 남아 있다**는 데 있다.

---

## Pass 2 - 코드 대조 검증

### A. 즉시 처리할 병목

| ID | Stage | 근거 | 판정 | 설명 |
|---|---|---|---|---|
| CTX-P0-1 | S2 | `modules/domain/agents/director_ensemble.py:393-421` | 확정 | Director Arc 선택 프롬프트가 `state_constraints[:1000]`, `joint_docs[:1000]`, `block_summary[:4000]`, `prev_arc_context[:6000]`, `constraint_block[:4000]`, `advisory[:4000]`에 의존한다. 최종 의사결정 지점에 하드 절삭이 집중되어 있다. |
| CTX-P0-2 | S0 | `modules/core/stage0/story_expander.py:246-257`, `404-432` | 확정 | NPC 생성과 skeleton 생성이 모두 `self.concept[:500]`만 사용한다. 초기 입력이 긴 작품일수록 손실이 커진다. |
| CTX-P0-3 | S0 | `modules/core/stage0/reverse_expander.py:248-255`, `363-368` | 확정 | Master Bible은 `raw_drafts[:3]`와 화당 `content[:4000]`만 사용하고, episode bible은 화당 `content[:6000]`만 사용한다. Stage 0 역추출 경로가 의도적으로 작은 샘플에 묶여 있다. |

### B. 중요한 구조 결함

| ID | Stage | 근거 | 판정 | 설명 |
|---|---|---|---|---|
| CTX-P1-1 | S0 | `modules/core/stage0/story_expander.py:442-471` | 확정 | `_generate_details()`는 skeleton의 `block_id`, `title`만 넣고 상세를 생성한다. concept, genre, theme, world law가 직접 재주입되지 않는다. |
| CTX-P1-2 | S0 | `modules/core/stage0/style_extractor.py:686-693` | 확정 | Anti-pattern 생성은 `passages[:5]` 또는 `drafts[0][:5000]`만 본다. 참조 원고 샘플링 편향이 크다. |
| CTX-P1-3 | S2 | `modules/core/stage2_preflight.py:211-225`, `596-603` | 확정 | StyleGuide는 Stage 2에서 `max_chars=500` 요약본으로만 Analyst 문맥 앞단에 주입된다. 문체 신호는 있으나 매우 얇다. |
| CTX-P1-4 | S2 | `modules/domain/agents/arc_ensemble.py:393-400`, `modules/domain/agents/base_agent.py:1643-1650` | 확정 | Arc ensemble 캐시 경로는 존재하지만 shared context가 50,000자 미만이면 캐시가 생성되지 않는다. "캐시 사용 가능"과 "실제 캐시 생성"은 구분해야 한다. |
| CTX-P1-5 | S3 | `modules/core/stage3_orchestrator.py:839-849`, `883-899` | 확정 | Stage 3는 StyleGuide/FactLedger/seed advisory를 `semantic_context`로 주입하지만, WorldState 요약은 Blueprint 생성 호출에 직접 배선되지 않는다. |
| CTX-P1-6 | S4 | `modules/core/truth_gate.py:404-412`, `modules/core/npc_drift_advisor.py:117-131`, `modules/core/info_paradox_checker.py:167-193`, `modules/core/relationship_drift_advisor.py:96-106`, `modules/core/long_term_repetition_advisor.py:64-69` | 확정 | Stage 4 advisory 다수가 `manuscript[:3000]` 또는 `[:4000]`를 사용한다. 현재 원고가 8K 내외라면 후반부 감시가 약해진다. |
| CTX-P1-7 | S4 | `modules/core/stage4_interview_round.py:933-1131`, `modules/domain/agents/chief_writer.py:806-878`, `1211-1251` | 확정 | Advisory chain 결과는 Director mandatory context에 직접 들어가지만, ChiefWriter는 Director가 재가공한 `director_feedback`만 받는다. raw advisory는 직접 보지 못한다. |

### C. 병목으로 보기 어려운 항목

| ID | Stage | 근거 | 판정 | 설명 |
|---|---|---|---|---|
| CTX-N-1 | S3 | `modules/domain/agents/blueprint_ensemble.py:187-210`, `763-830` | 보정 | Blueprint ensemble은 이전 Blueprint 전문과 이전 원고 전문을 크게 받을 수 있고, shared context 캐시 경로도 있다. Stage 3 전체를 "저활용 단계"로 보기는 어렵다. |
| CTX-N-2 | S4 | `modules/core/stage4_context_builder.py:1302-1415`, `modules/domain/agents/chief_writer_context.py:403-415`, `modules/domain/agents/director_ensemble.py:655-777` | 보정 | Stage 4는 이전 원고 30화 전문, mandatory context, stable context cache를 모두 갖는다. 따라서 Stage 4의 주 문제는 총량 부족보다 세부 snippet 전략과 배선 문제다. |

### D. 오탐 제거 / 서술 보정

- `prev_manuscript[-2500:]`는 **Stage 4 전체 역사 절삭이 아니다**.  
  근거: `modules/domain/agents/chief_writer_context.py:185-187`는 직전 화 엔딩/다이제스트용이고, 전체 이전 원고는 별도 `prev_manuscripts_text`로 `modules/core/stage4_context_builder.py:1302-1415`, `modules/domain/agents/chief_writer_context.py:403-415`, `modules/domain/agents/director_ensemble.py:655-777`에서 공급된다.
- Stage 4 advisory 충돌은 완전 무방비가 아니다.  
  근거: `modules/core/stage4_interview_round.py:934-935`에서 `_suppress_conflicting_advisories()`를 이미 호출한다.
- Blueprint Director는 Stage 2 Arc Director와 동일한 급의 병목으로 보기 어렵다.  
  근거: `modules/domain/agents/director_ensemble.py:97-127`에서 후보별 `integrated_scenario` 전문을 그대로 포함한다. 하드 절삭은 `arc_tactical_ep[:6000]` 정도에 국한된다.
- `smart_truncate()`는 head-only 절삭이 아니다.  
  근거: `modules/core/constants.py:156-174`는 head와 tail을 같이 보존한다.

---

## Pass 3 - 실행 계획으로 재구성

## 우선순위

### P0

| 작업 ID | 변경 목표 | 수정 위치 | 완료 기준 |
|---|---|---|---|
| ACT-P0-1 | Stage 2 Director Arc 선택부의 하드 절삭 상향 또는 설정 외부화 | `modules/domain/agents/director_ensemble.py` | `block_summary`, `prev_arc_context`, `constraint_block`, `advisory`, 후보 요약 cap이 하드코드가 아니라 정책값으로 관리되고, Arc 선택 시 이전 맥락 손실이 현저히 줄어든다. |
| ACT-P0-2 | Stage 0 `concept[:500]` 제거 또는 상향 | `modules/core/stage0/story_expander.py` | NPC/skeleton 생성이 500자 고정 절삭에 묶이지 않는다. 긴 concept에서 후반 설정이 보존된다. |
| ACT-P0-3 | ReverseExpander master/episode bible 샘플 윈도우 확장 | `modules/core/stage0/reverse_expander.py` | Master Bible이 3화 x 4K 고정에 묶이지 않고, episode bible도 6K 고정 상한을 완화하거나 설정화한다. |

### P1

| 작업 ID | 변경 목표 | 수정 위치 | 완료 기준 |
|---|---|---|---|
| ACT-P1-1 | Stage 0 detail 생성에 concept/genre/theme 재주입 | `modules/core/stage0/story_expander.py` | `_generate_details()`가 skeleton title만이 아니라 최소한 concept과 genre를 함께 참조한다. |
| ACT-P1-2 | Stage 3 Blueprint에 WorldState 직접 주입 | `modules/core/stage3_orchestrator.py` 또는 `modules/domain/agents/three_phase_blueprint_generator.py` | Blueprint 생성 프롬프트가 StyleGuide/FactLedger뿐 아니라 현재 WorldState의 핵심 요약도 받는다. |
| ACT-P1-3 | Stage 4 advisory snippet을 full text 또는 head+tail 전략으로 교체 | `modules/core/truth_gate.py`, `modules/core/npc_drift_advisor.py`, `modules/core/info_paradox_checker.py`, `modules/core/relationship_drift_advisor.py`, `modules/core/long_term_repetition_advisor.py` | 후반부 결말/반전/보상 구간이 advisory 사각지대에서 벗어난다. |
| ACT-P1-4 | Raw advisory 요약을 CW 재시도 경로에도 전달 | `modules/core/stage4_interview_round.py`, `modules/domain/agents/chief_writer.py` | REJECT/PASS_WITH_FIX 시 CW가 Director 요약 외에 advisory 핵심 원인을 구조적으로 재수신한다. |

### P2

| 작업 ID | 변경 목표 | 수정 위치 | 완료 기준 |
|---|---|---|---|
| ACT-P2-1 | Stage 2 StyleGuide 500자 요약 완화 | `modules/core/stage2_preflight.py` | Analyst 문맥의 StyleGuide 신호가 500자보다 넓어지고, 문체/금지 표현 손실이 줄어든다. |
| ACT-P2-2 | StyleExtractor anti-pattern 샘플링 다변화 | `modules/core/stage0/style_extractor.py` | `passages[:5]` 또는 `drafts[0][:5000]` 단일 편향을 줄이고 샘플 대표성이 개선된다. |

---

## 구현 순서 제안

1. `ACT-P0-1`부터 처리한다. Stage 2 최종 의사결정자 병목이라 ROI가 가장 높다.
2. 그다음 `ACT-P0-2`, `ACT-P0-3`으로 Stage 0 입력 손실을 줄인다.
3. 이후 `ACT-P1-3`으로 Stage 4 advisory front-bias를 줄인다.
4. 마지막으로 `ACT-P1-2`, `ACT-P1-4`처럼 배선 계열 개선을 적용한다.

---

## 검증 게이트

### 정적 확인

- Stage 2: `modules/domain/agents/director_ensemble.py`에 남아 있는 하드 슬라이스(`[:1000]`, `[:4000]`, `[:6000]`) 재검색
- Stage 0: `modules/core/stage0/story_expander.py`, `modules/core/stage0/reverse_expander.py`의 고정 cap 재검색
- Stage 4: advisory 파일들에서 `manuscript[:3000]`, `manuscript[:4000]` 재검색

### 테스트 우선순위

- `tests/test_stage2_preflight.py`
- `tests/test_four_phase_arc_generator.py`
- `tests/test_stage3_orchestrator.py`
- `tests/test_stage4_context_builder.py`
- `tests/test_stage4_interview_round.py`
- `tests/test_chief_writer.py`

### 스모크 경로

- `scripts/run_stage2_smoke.py`
- `scripts/run_stage3_smoke.py`
- `scripts/run_stage4_smoke.py`

### 런타임 로그 확인 포인트

- Stage 2 Director 선택 프롬프트 조립 시 절삭 로그 또는 길이 로그 추가 여부
- Context cache 생성/재사용 로그  
  근거: `modules/domain/agents/base_agent.py:1633-1679`
- Stage 4 Director mandatory context가 400K 상한에 걸렸는지 여부  
  근거: `modules/domain/agents/director_ensemble.py:693-720`

---

## 최종 판단

- 이번 감사 기준으로 **실제 수정을 먼저 해야 하는 곳은 Stage 2 Director Arc 선택부와 Stage 0 입력 절삭부**다.
- **Stage 3/4는 "큰 창을 못 쓰는 시스템"이 아니라, 이미 큰 창을 쓰고 있으나 일부 입력 배선과 snippet 전략이 아쉬운 시스템**에 가깝다.
- 따라서 후속 작업도 "전 스테이지 일괄 확장"이 아니라 **Stage 2 의사결정 병목 제거 -> Stage 0 입력 손실 축소 -> Stage 4 advisory 사각지대 보강** 순서가 맞다.

---

## 감리 기록

| Pass | 수행 내용 | 결과 |
|---|---|---|
| Pass 1 | 설정값과 캐시 정책 SSOT 확정 | 예산 상한은 충분하고, 병목은 하드 절삭/배선 문제임을 확인 |
| Pass 2 | 코드 라인 단위 근거 검증 및 오탐 제거 | Stage 2 P0, Stage 0 P0, Stage 4 보정 사항 확정 |
| Pass 3 | 작업 순서, 완료 기준, 검증 게이트로 문서 재구성 | 실행 가능한 감사 문서 형태로 전환 완료 |

잔여 불확실성:

- 호출 단위 실제 prompt char 수와 cache hit ratio는 최신 메트릭 파일만으로는 재현되지 않았다.
- 따라서 이번 문서는 "활용률 몇 %"보다 "어디서 무엇이 잘리는가"에 초점을 맞췄다.
