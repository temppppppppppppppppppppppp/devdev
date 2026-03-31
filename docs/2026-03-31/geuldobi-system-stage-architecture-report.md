Date: 2026-03-31
Status: final (3-pass audited)
Document Type: 개발부서용 시스템 아키텍처 보고서
Canonical Path: `docs/2026-03-31/geuldobi-system-stage-architecture-report.md`
Temp Mirror Path: none
Audience: development organization
Scope:
- 글도비 시스템을 사업 설명이 아니라 기술 파이프라인 기준으로 설명
- control plane, orchestration, stage pipeline, persistence, observability 포함
- 각 production stage의 입력, 처리, 출력, 권한 구조 설명
Excluded Scope:
- 작품 family별 narrative router 세부 규칙
- `docs/temp/` 아래 개별 remediation queue 문서
- control-plane contract 밖의 UI/desktop 디자인 상세
Evidence Basis:
- `main_a.py`
- `modules/core/stage01_helpers.py`
- `modules/core/stage2_orchestrator.py`
- `modules/core/stage2_finalizer.py`
- `modules/core/stage3_orchestrator.py`
- `modules/domain/agents/three_phase_blueprint_runtime.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_post_processor.py`
- `modules/core/stage4_post_pass_runtime.py`
- `modules/api/bridge_server.py`
- `modules/api/process_runner.py`
- `modules/core/db_manager.py`
- `modules/core/world_state.py`
- `modules/core/fact_ledger.py`
- `modules/core/pass_rate_monitor.py`
- `docs/2026-03-23/llm-codebase-orientation-pack.md`
Side-Effect Coverage:
- file writes: covered
- DB writes: covered
- JSON/log/metrics sinks: covered
- world-state and fact-state mutation: covered
- rollback/recovery surfaces: covered at summary level

# 글도비 시스템 스테이지 아키텍처 보고서

## 1. 요약

글도비는 단일 프롬프트로 웹소설을 한 번에 생성하는 시스템이 아니다. 작품 설계 자산을 단계적으로 분해하고, 각 단계를 검증과 판정, 저장, 관측 가능성까지 포함한 파이프라인으로 운영하는 장기 연재용 생산 엔진이다.

생산 파이프라인은 크게 다음과 같이 이해하면 된다.

`Phase 0 / Stage 0 -> Stage 1 (선택) -> Stage 2 -> Stage 3 -> Stage 4`

실제 핵심 production line만 압축하면 다음과 같다.

`Stage 0 -> Stage 2 -> Stage 3 -> Stage 4`

`Stage 1`은 권 단위 전략을 보강하는 선택형 오버레이 단계이며, 없더라도 Stage 2는 진행할 수 있다. 이 점은 메뉴와 런타임 모두에서 명시돼 있다. 근거: [main_a.py](/c:/Users/User/Desktop/글도비/main_a.py#L2163), [main_a.py](/c:/Users/User/Desktop/글도비/main_a.py#L2203), [stage01_helpers.py](/c:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py#L818)

시스템 레벨 설계 원칙은 다음과 같이 정리된다.

- Python은 수집, 정규화, 검증, 라우팅, 저장을 담당한다.
- LLM 에이전트는 후보 산출물 생성과 보조 분석을 담당한다.
- 최종 품질 판정 권한은 Director에 있다.
- 운영 진실은 콘솔이 아니라 DB와 파일 sink에 남는다.

이 권한 분리는 stage pipeline과 persistence layer 모두에서 드러난다. 근거: [llm-codebase-orientation-pack.md](/c:/Users/User/Desktop/글도비/docs/2026-03-23/llm-codebase-orientation-pack.md#L93), [db_manager.py](/c:/Users/User/Desktop/글도비/modules/core/db_manager.py#L51)

## 2. 전체 구조

### 2.1 시스템 레이어

개발부서 기준으로 보면 글도비는 다음 다섯 레이어로 나뉜다.

1. 진입점 및 control plane
2. stage orchestration layer
3. domain agent 및 validation layer
4. persistence 및 state layer
5. observability 및 operator debugging layer

### 2.2 진입점 및 Control Plane

진입 경로는 두 가지다.

- 운영자 경로: `main_a.py`가 인터랙티브 메뉴를 통해 stage 실행을 디스패치한다. 근거: [main_a.py](/c:/Users/User/Desktop/글도비/main_a.py#L2194), [main_a.py](/c:/Users/User/Desktop/글도비/main_a.py#L2231)
- 외부 control-plane 경로: FastAPI bridge가 데스크톱 또는 외부 호출자를 위해 엔진을 감싼다. 근거: [bridge_server.py](/c:/Users/User/Desktop/글도비/modules/api/bridge_server.py#L2311), [bridge_server.py](/c:/Users/User/Desktop/글도비/modules/api/bridge_server.py#L2454), [bridge_server.py](/c:/Users/User/Desktop/글도비/modules/api/bridge_server.py#L2472), [bridge_server.py](/c:/Users/User/Desktop/글도비/modules/api/bridge_server.py#L2532)

FastAPI bridge는 production logic 자체를 재구현하지 않는다. 실행 요청을 검증하고, 위험 승인을 통과시키고, 엔진 subprocess를 띄우고, runtime event를 스트리밍하는 역할만 한다. subprocess 수명주기 owner는 `ProcessRunner`다. 근거: [process_runner.py](/c:/Users/User/Desktop/글도비/modules/api/process_runner.py#L250), [process_runner.py](/c:/Users/User/Desktop/글도비/modules/api/process_runner.py#L296), [process_runner.py](/c:/Users/User/Desktop/글도비/modules/api/process_runner.py#L398), [process_runner.py](/c:/Users/User/Desktop/글도비/modules/api/process_runner.py#L468)

### 2.3 Stage Orchestration Layer

최상위 owner는 `main_a.py`의 `SovereignApp`이다. 다만 현재의 역할은 과거식 거대 실행 객체라기보다 운영자 인터페이스와 top-level coordination에 가깝다.

주요 책임은 다음과 같다.

- 프로젝트/장르 선택
- Stage 0/1/2/3/4 진입 라우팅
- one-stop pipeline 변형 진입
- 종료 시 세션 단위 persistence 훅

각 주요 stage는 전용 owner shell을 가진다.

- Stage 0/1: [stage01_helpers.py](/c:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py)
- Stage 2: [stage2_orchestrator.py](/c:/Users/User/Desktop/글도비/modules/core/stage2_orchestrator.py)
- Stage 3: [stage3_orchestrator.py](/c:/Users/User/Desktop/글도비/modules/core/stage3_orchestrator.py)
- Stage 4: [stage4_orchestrator.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py)

즉 현재 구조는 `main_a.py`가 운영자 entry를 맡고, 실제 stage logic은 stage owner로 분해된 형태다. 근거: [llm-codebase-orientation-pack.md](/c:/Users/User/Desktop/글도비/docs/2026-03-23/llm-codebase-orientation-pack.md#L99)

### 2.4 Domain Agent 및 Validation Layer

각 stage owner 내부의 의미적 작업은 agent/runtime 모듈에 위임된다.

- Stage 2: Analyst + preflight/finalizer 계열
- Stage 3: ThreePhaseBlueprint runtime
- Stage 4: ChiefWriter, context builder, Python prevalidator, Director review

이 레이어는 후보 산출물을 생성하거나 평가하는 곳이다. 하지만 여기서 생성된 결과만으로는 최종 truth가 되지 않는다. truth가 되려면 persistence sink에 정착되어야 한다.

### 2.5 Persistence 및 State Layer

영속화의 중심 owner는 `DBManager`이며, 장기 상태는 별도 manager가 맡는다.

- DB sink owner: [db_manager.py](/c:/Users/User/Desktop/글도비/modules/core/db_manager.py#L51)
- world-state manager: [world_state.py](/c:/Users/User/Desktop/글도비/modules/core/world_state.py#L121)
- fact ledger: [fact_ledger.py](/c:/Users/User/Desktop/글도비/modules/core/fact_ledger.py#L119)

Persistence model은 크게 세 가지를 혼합한다.

- 시도, 선택, 비용, UI event, manuscript, blueprint, episode bible, state log 같은 테이블 기반 DB 저장
- `bible`, `volumes`, `arcs`, `world_state`, `fact_ledger` 같은 anchor 기반 장문 상태 저장
- 프로젝트 `drafts/` 아래 reader-facing 원고 파일 저장

### 2.6 Observability Layer

주요 관측 표면은 다음과 같다.

- console/UI log
- audit event
- DB telemetry table
- pass-rate monitor convenience cache

`pass_rate_monitor.json`은 권위 있는 진실 소스가 아니라 operator convenience cache라는 점이 코드에 명시돼 있다. 최종 시도/판정 truth는 DB sink에 있다. 근거: [pass_rate_monitor.py](/c:/Users/User/Desktop/글도비/modules/core/pass_rate_monitor.py#L1)

### 2.7 참조용 시스템 다이어그램

```text
외부 호출자 / 운영자
    -> main_a.py 메뉴 또는 FastAPI bridge
    -> stage orchestrator
    -> agent/runtime generation + validation
    -> Director adjudication
    -> DB/file/state sinks
    -> metrics / audit / dashboard / WS events
```

## 3. 권한 구조와 진실 소스

### 3.1 최종 권한

글도비는 다수결형 생성 시스템이 아니다. 최종 품질 판정 권한은 중앙집중형이다.

- Stage 2와 Stage 3는 validation/finalization pipeline을 통해 artifact 채택 여부를 정한다.
- Stage 4는 Director review가 최종 gate다.

특히 Stage 4에서 Python prevalidation은 advisory-only이며, Director 권한을 대체하지 않는다. 이 구조는 Stage 4 내부 phase 정의에 직접 드러난다. 근거: [stage4_orchestrator.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py#L2514), [stage4_interview_round.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2846)

### 3.2 Durable Truth

개발 관점에서 “실제로 무엇이 일어났는가”를 확인할 때의 신뢰 순서는 다음과 같다.

1. DB truth
2. file artifact
3. audit summary
4. console output

중요한 DB truth sink는 다음과 같다.

- `save_director_selection(...)`: [db_manager.py](/c:/Users/User/Desktop/글도비/modules/core/db_manager.py#L2255)
- `save_stage_attempt(...)`: [db_manager.py](/c:/Users/User/Desktop/글도비/modules/core/db_manager.py#L2995)
- `save_ui_event(...)`: [db_manager.py](/c:/Users/User/Desktop/글도비/modules/core/db_manager.py#L3152)
- `save_cost_record(...)`: [db_manager.py](/c:/Users/User/Desktop/글도비/modules/core/db_manager.py#L3297)

orientation pack도 같은 원칙을 설명한다. 콘솔은 “지금 무슨 일이 벌어지는가”를 보는 용도이고, durable truth는 DB와 관련 sink에 있다. 근거: [llm-codebase-orientation-pack.md](/c:/Users/User/Desktop/글도비/docs/2026-03-23/llm-codebase-orientation-pack.md#L212)

### 3.3 장기 상태 진실

장기 연재 정합성에서 핵심인 manager는 두 개다.

- `WorldStateManager`: 현재 세계의 진실, 압박 벡터, NPC 생사, 아이템, 장소, 세계 법칙을 유지한다. 근거: [world_state.py](/c:/Users/User/Desktop/글도비/modules/core/world_state.py#L121), [world_state.py](/c:/Users/User/Desktop/글도비/modules/core/world_state.py#L176), [world_state.py](/c:/Users/User/Desktop/글도비/modules/core/world_state.py#L1233)
- `FactLedger`: 캐릭터 상태, 아이템, 장소, 조직, 숫자 팩트를 누적 관리한다. 근거: [fact_ledger.py](/c:/Users/User/Desktop/글도비/modules/core/fact_ledger.py#L119), [fact_ledger.py](/c:/Users/User/Desktop/글도비/modules/core/fact_ledger.py#L206), [fact_ledger.py](/c:/Users/User/Desktop/글도비/modules/core/fact_ledger.py#L610)

둘 다 episode-bible 히스토리를 기준으로 rollback replay를 지원한다. 근거: [world_state.py](/c:/Users/User/Desktop/글도비/modules/core/world_state.py#L1434), [fact_ledger.py](/c:/Users/User/Desktop/글도비/modules/core/fact_ledger.py#L824)

## 4. Stage 모델

### 4.1 Stage 목록

| Stage | 주 역할 | 주요 입력 | 주요 출력 | 필수 여부 |
| --- | --- | --- | --- | --- |
| Phase 0 / Stage 0 | 프로젝트 초기화 및 source asset 정규화 | Bible, Treatment, concept, 역설계 원고, style reference | Bible, `plot_roadmap`, style guide, preset state | 필수 |
| Stage 1 | 권 단위 전략 보강 | Stage 0 roadmap | `volumes` anchor | 선택 |
| Stage 2 | Arc tactical design | Bible roadmap, optional volume strategy, prior arc state | refined arcs, arc summaries, volume summaries | 필수 |
| Stage 3 | Episode blueprinting | refined arcs, prior blueprints, semantic context, long-memory state | episode blueprints | 필수 |
| Stage 4 | Manuscript production and settlement | blueprint, context packets, style guide, prior state | draft file, episode bible, world state, fact ledger, telemetry | 필수 |

### 4.2 명명 주의점

운영 문서와 코드에서 다음 명명 비대칭이 존재한다.

- 메뉴에서는 초기화 단계를 `Phase 0`이라고 부른다.
- helper/runtime에서는 같은 경계를 `Stage 0`이라고 부르는 경우가 많다.

운영상으로는 같은 경계다. 근거: [main_a.py](/c:/Users/User/Desktop/글도비/main_a.py#L2167), [stage01_helpers.py](/c:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py#L130)

## 5. 스테이지별 상세

### 5.1 Phase 0 / Stage 0: 프로젝트 초기화 및 Handoff 준비

#### 역할

Stage 0은 외부 프로젝트 입력을 엔진이 소비할 수 있는 기본 상태로 변환하는 단계다. 후속 생성 단계가 사용하게 될 기반 설계 자산을 정리하는 ingest + normalization layer라고 보면 된다.

#### 입력

- Bible/Treatment 파일
- concept 기반 생성 입력
- 기존 원고 기반 역설계 입력
- style reference 분석 입력
- 프로젝트 단위 protagonist/POV 설정

메인 operator entry는 [stage01_helpers.py](/c:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py#L130) 이다.

#### 주요 처리

Stage 0은 크게 세 가지 책임을 가진다.

1. source ingestion 및 프로젝트 bootstrap
2. Stage 2로 넘기기 위한 handoff normalization
3. style/preset/guard 계열의 선택적 보강

가장 중요한 handoff artifact는 `plot_roadmap`다. Stage 0은 roadmap가 Stage 2 readiness를 만족하는지 확인한 뒤에만 Bible과 관련 anchor를 저장한다. 근거: [stage01_helpers.py](/c:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py#L703)

또한 기존 draft manuscript가 있으면 이를 프로젝트 history에 동기화하여, 시스템이 완전한 신규 프로젝트만 가정하지 않도록 만든다. 근거: [stage01_helpers.py](/c:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py#L325)

#### 출력

- `bible` anchor
- `plot_roadmap`
- optional `style_guide` anchor
- optional `preset_state` anchor
- treatment JSON 파일
- 기존 원고 history sync 결과

#### 개발 관점 의미

Stage 0이 없으면 Stage 2 이하 단계가 프로젝트 구조를 런타임에서 즉석 추론해야 한다. 그러면 authority boundary가 흐려지고 장애 위치도 모호해진다. Stage 0은 Stage 2가 “무엇을 받는지”를 명확하게 만든다.

### 5.2 Stage 1: 권 단위 전략 오버레이

#### 역할

Stage 1은 Stage 0의 roadmap를 권 단위 전략 문서로 확장하는 단계다. 필수 stage가 아니라 planning amplifier에 가깝다.

#### 입력

- Stage 0에서 생성된 `plot_roadmap`
- Bible 안의 프로젝트 메타 정보

#### 주요 처리

Stage 1은 다음을 수행한다.

- roadmap 로드
- arc를 권 단위로 slicing
- analyst를 통해 각 권의 전략 문서 생성
- 분량과 미래 권 누수 검증
- 결과를 `volumes` anchor에 저장

근거: [stage01_helpers.py](/c:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py#L786), [stage01_helpers.py](/c:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py#L836), [stage01_helpers.py](/c:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py#L1023)

#### 출력

- `volumes` anchor
- optional volume table

#### 개발 관점 의미

Stage 1은 Stage 2에 상위 전략 scaffold를 제공하지만, Stage 2가 Stage 1에 hard dependency를 갖지는 않는다. 이 점 때문에 아키텍처 문서에서 선택형 오버레이라는 점을 분명히 써야 한다.

### 5.3 Stage 2: Arc Tactical Design

#### 역할

Stage 2는 roadmap block을 refined arc로 구체화하는 단계다. 여기서부터 시스템은 추상적인 작품 설계가 아니라 실행 가능한 story structure를 다루기 시작한다.

#### 입력

- Stage 0 Bible과 `plot_roadmap`
- optional `volumes` 전략
- 기존에 저장된 prior arc
- state-tracker 및 constraint state

#### 주요 처리

Stage 2 owner는 `_bootstrap_stage2_arc_pipeline(...)`에서 실행 상태를 준비한다. 근거: [stage2_orchestrator.py](/c:/Users/User/Desktop/글도비/modules/core/stage2_orchestrator.py#L278)

이후 단계는 크게 다음 흐름으로 진행된다.

1. pipeline bootstrap 및 readiness check
2. batch enrichment 및 preflight analysis
3. 단일 arc validation
4. PASS finalization 및 persistence

메인 async entry는 [stage2_orchestrator.py](/c:/Users/User/Desktop/글도비/modules/core/stage2_orchestrator.py#L889) 이다. validation과 finalization이 분리돼 있는 점이 중요하다. 근거: [stage2_orchestrator.py](/c:/Users/User/Desktop/글도비/modules/core/stage2_orchestrator.py#L1372), [stage2_orchestrator.py](/c:/Users/User/Desktop/글도비/modules/core/stage2_orchestrator.py#L1439)

PASS가 나면 refined arc를 append하고, `arcs` anchor를 저장하고, dependency 및 constraint state를 갱신하며, 필요 시 volume/series summary도 생성한다. 근거: [stage2_finalizer.py](/c:/Users/User/Desktop/글도비/modules/core/stage2_finalizer.py#L1347), [stage2_finalizer.py](/c:/Users/User/Desktop/글도비/modules/core/stage2_finalizer.py#L1458)

#### 출력

- `arcs` anchor
- arc dependency link
- constraint DB update
- `volume_summary_{n}` anchor
- `series_summary` anchor
- stage attempt, director selection, pass-rate metric, cost record

#### 개발 관점 의미

Stage 2는 planning과 execution 사이의 경계다. 여기서 생성된 arc 품질이 낮으면 이후 Stage 3과 Stage 4의 retry 비용이 급증한다.

### 5.4 Stage 3: Episode Blueprinting

#### 역할

Stage 3은 회차별 blueprint를 생성하는 단계다. blueprint는 “이번 화에서 무엇을 어떻게 실현해야 하는가”를 정의하는 production contract다.

#### 입력

- current arc data
- previous blueprint
- entity registry / cumulative state
- semantic retrieval context
- world-state와 fact-ledger에서 파생된 장기 기억 context

stage entry owner는 [stage3_orchestrator.py](/c:/Users/User/Desktop/글도비/modules/core/stage3_orchestrator.py#L549) 이고, 실제 blueprint retry loop는 [three_phase_blueprint_runtime.py](/c:/Users/User/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py#L1536) 에 있다.

#### 주요 처리

Stage 3은 다음 흐름으로 동작한다.

1. context assembly 및 retrieval budget 계산
2. multi-retry blueprint generation
3. validation 및 adjudication
4. success persistence 또는 failure recording

성공 경로는 `_handle_success(...)`에 분명하게 드러난다. blueprint를 annotate하고, 저장하고, observability payload를 남긴다. 근거: [stage3_orchestrator.py](/c:/Users/User/Desktop/글도비/modules/core/stage3_orchestrator.py#L1727)

실패 경로는 reject reason, attempt metadata, quality dashboard signal을 남긴다. 근거: [stage3_orchestrator.py](/c:/Users/User/Desktop/글도비/modules/core/stage3_orchestrator.py#L2535)

#### 출력

- 저장된 episode blueprint
- stage attempt
- director selection record
- cost record
- observability 및 failure history

#### 개발 관점 의미

Stage 3은 자유 서술 생성 직전의 마지막 구조화 단계다. Stage 3 품질이 흔들리면 Stage 4는 불안정한 blueprint를 실현하려고 하면서 retry와 reject 비용이 커진다.

### 5.5 Stage 4: Sovereign Production

#### 역할

Stage 4는 원고 production과 settlement를 담당하는 단계다. 외부에서 가장 눈에 띄는 단계지만, 실제로는 앞 단계 산출물을 기반으로 최종 commit을 수행하는 단계다.

#### 입력

- episode blueprint
- arc context
- mandatory context packet
- style guide 및 reference excerpt
- prior manuscript 및 prior state context

owner는 [stage4_orchestrator.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py#L2507) 이고, session setup은 [stage4_orchestrator.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py#L2460) 에 있다.

#### 주요 처리

Stage 4는 내부적으로 명시적인 subphase를 가진다.

1. prompt assembly
2. Chief Writer ensemble generation
3. Python prevalidation
4. Director interview/review

이 정의는 Stage 4 orchestrator docstring과 round runtime 양쪽에 모두 드러난다. 근거: [stage4_orchestrator.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py#L2514), [stage4_interview_round.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2798)

round runtime을 보면 경계가 더 명확하다.

- generation phase: [stage4_interview_round.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2823)
- Python validation phase: [stage4_interview_round.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2846)
- Director review phase: [stage4_interview_round.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2855)

#### PASS 정착 처리

Stage 4가 PASS 되면 `Stage4PostProcessor`가 원고를 정착시킨다.

- draft file write
- capital/manager output reconcile
- voice, foreshadow 등 side system update
- episode-bible delta 생성 및 저장
- world-state / fact-ledger atomic persistence
- cost / quality telemetry 기록

원고 파일 저장과 post-pass 흐름은 다음 위치가 핵심이다. 근거: [stage4_post_processor.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_post_processor.py#L715), [stage4_post_processor.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_post_processor.py#L767)

장기 상태 정착은 `Stage4PostPassRuntime`가 맡는다. episode-bible 저장, state-log 저장, world-state/fact-ledger atomic update가 여기서 이뤄진다. 근거: [stage4_post_pass_runtime.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_post_pass_runtime.py#L772), [stage4_post_pass_runtime.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_post_pass_runtime.py#L879), [stage4_post_pass_runtime.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_post_pass_runtime.py#L1179)

#### 출력

- project `drafts/` 아래 reader-facing 원고 파일
- episode bible delta
- state log 및 summary
- world-state snapshot update
- fact-ledger update
- quality signal, cost record, observability artifact

#### 개발 관점 의미

Stage 4는 단순 텍스트 생성 단계가 아니다. 원고를 생성하면서 동시에 narrative state를 commit하는 단계다. 그래서 이전 stage보다 persistence와 observability 복잡도가 훨씬 높다.

## 6. Persistence 및 데이터 표면

### 6.1 주요 Durable Sink

핵심 durable surface는 다음과 같다.

- `project_data.db` via `DBManager`
- project `drafts/ep_XXXX.txt`
- 장기 공유 상태용 DB anchor

DB layer는 runtime telemetry, state, artifact linkage를 함께 담는다. 근거: [db_manager.py](/c:/Users/User/Desktop/글도비/modules/core/db_manager.py#L51)

### 6.2 Anchor 기반 공유 문서

중요 anchor는 다음과 같다.

- `bible`
- `volumes`
- `arcs`
- `world_state`
- `fact_ledger`
- volume/series summary 계열

이 구조 덕분에 시스템은 LLM에게 모든 과거 원고를 매번 다시 읽히지 않고도 장기 상태를 재사용할 수 있다.

### 6.3 원고 파일

reader-facing draft file은 Stage 4 post-processing에서 저장된다. 저장 경로와 UTF-8 write가 코드에 명시돼 있다. 근거: [stage4_post_processor.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_post_processor.py#L715)

## 7. Observability 및 디버깅 경로

### 7.1 권장 디버깅 순서

개발부서에서 장애를 볼 때는 보통 다음 순서가 가장 효율적이다.

1. entry/execution 문제면 `/status` 또는 control-plane runtime snapshot 확인
2. 실시간 문제면 console과 recent runtime tail 확인
3. verdict 문제면 `stage_attempts`와 `director_selections` 확인
4. artifact 문제면 draft file과 episode-bible row 확인
5. continuity 문제면 `world_state`와 `fact_ledger` 확인

### 7.2 Metrics 및 Convenience View

`PassRateMonitor`는 빠른 operator summary에는 유용하지만, truth source는 아니다. 주요 메서드는 attempt recording과 episode ROL 계산이다. 근거: [pass_rate_monitor.py](/c:/Users/User/Desktop/글도비/modules/core/pass_rate_monitor.py#L176), [pass_rate_monitor.py](/c:/Users/User/Desktop/글도비/modules/core/pass_rate_monitor.py#L267), [pass_rate_monitor.py](/c:/Users/User/Desktop/글도비/modules/core/pass_rate_monitor.py#L412)

### 7.3 Control-Plane 진단 표면

FastAPI bridge는 다음 API를 노출한다.

- `/run`
- `/stop`
- `/status`
- `/quality/dashboard`
- websocket `/events`

즉 외부 도구는 interactive menu loop에 직접 들어가지 않고도 run state와 dashboard summary를 조회할 수 있다. 근거: [bridge_server.py](/c:/Users/User/Desktop/글도비/modules/api/bridge_server.py#L2311), [bridge_server.py](/c:/Users/User/Desktop/글도비/modules/api/bridge_server.py#L2454), [bridge_server.py](/c:/Users/User/Desktop/글도비/modules/api/bridge_server.py#L2472), [bridge_server.py](/c:/Users/User/Desktop/글도비/modules/api/bridge_server.py#L2532)

## 8. 개발부서 관점 해석

개발부서가 글도비를 볼 때 가장 중요한 해석은 다음과 같다.

- 글도비는 거대한 단일 prompt가 아니라 artifact pipeline이다.
- 각 stage는 더 넓은 planning unit을 더 좁은 execution unit으로 내려보낸다.
- Stage 4는 생성 단계이면서 settlement 단계이기 때문에 비용과 복잡도가 가장 높다.
- 장기 연재 continuity는 prompt memory만으로 해결하지 않고, `world_state`와 `fact_ledger`로 외재화한다.
- runtime truth는 authoritative sink와 convenience view를 의도적으로 분리해 놓았다.

따라서 시스템 작업은 대체로 다음 네 가지 중 하나로 분류하는 편이 맞다.

1. control-plane 문제
2. stage-boundary contract 문제
3. persistence/settlement 문제
4. observability/truth-source 문제

이 프레임이 단순히 “단계별로 웹소설을 쓰는 시스템”이라고 설명하는 것보다 개발부서에는 훨씬 유효하다.

## 9. 제한 사항 및 주의점

- `Phase 0`과 `Stage 0`은 같은 경계지만 명칭이 혼재한다.
- `Stage 1`은 실제 stage이지만 optional이므로 architecture diagram에서 hard dependency처럼 그리면 안 된다.
- `pass_rate_monitor.json`을 최종 truth source로 취급하면 안 된다.
- console output만으로 persistence 또는 continuity 버그를 판정하면 안 된다.
- Stage 4 내부 복잡도는 retry, review, patch, post-pass settlement 때문에 이전 stage보다 훨씬 높다.

## 10. 개발관리자용 1문단 요약

글도비는 프로젝트 입력을 Bible과 roadmap로 정규화한 뒤, 이를 arc 단위 전술 설계로 세분화하고, 다시 회차별 blueprint로 확장한 다음, 최종적으로 writer plus director review loop를 통해 원고를 생산하는 단계형 fiction production engine이다. 시스템 구조상 Python은 라우팅, 검증, 영속화, 장기 상태 관리를 맡고, LLM 에이전트는 각 단계에서 후보 산출물 생성과 비평을 담당한다. 운영상 진실은 콘솔이 아니라 DB와 artifact sink에 남기 때문에, 장기 연재 continuity, rollback, observability, external control-plane access를 production time에 함께 지원할 수 있다.

## 11. 3-Pass Audit Record

Pass 1. Structure and Scope
- 문서 유형이 요청과 일치함: 개발부서용 시스템 보고서
- 전체 샷과 stage 상세가 모두 포함됨
- control plane, persistence, observability가 명시적으로 포함됨
- PASS

Pass 2. Evidence and Consistency
- stage 순서가 `main_a.py` 메뉴와 orientation pack topology와 일치함
- optional `Stage 1` 의미가 live code 및 menu warning과 일치함
- persistence/observability 관련 주장이 실제 확인한 파일 범위를 넘지 않음
- PASS

Pass 3. Execution and Readability
- 문서가 개발 독자 기준으로 바로 사용 가능함
- 권한 모델과 debugging path가 명시적임
- narrative-router나 temp queue 영역으로 불필요하게 번지지 않음
- PASS

## 12. Confidence

Estimated confidence: `97%`

Reasoning:
- stage boundary와 ownership은 live entry point와 orchestrator 코드에 직접 반영돼 있어 신뢰도가 높음
- persistence/observability surface는 sink owner가 코드에 명시돼 있어 신뢰도가 높음
- 향후 ownership drift가 생기면 이 보고서도 같이 갱신되어야 한다는 점만 남은 리스크임
