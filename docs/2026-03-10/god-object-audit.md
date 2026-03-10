# God Object 및 후보 전수조사

> 작성: 2026-03-10
> 상태: 조사 완료
> 범위: `modules/` + `main_a.py` — 1,000줄 이상 Python 파일 전량 (20개)
> 기준: God Object = "2개 이상의 무관한 책임을 가진 클래스 또는 모듈"

---

## 판정 기준

| 등급 | 정의 | 조치 |
|------|------|------|
| **RESOLVED** | 이미 분할 완료, 추가 분할 0~1건 | 유지 |
| **MODERATE** | 잔여 분할 1~2건, 리스크 중간 | 선택적 |
| **SIGNIFICANT** | 잔여 분할 2~3건, 리스크 중~상 | 계획 권장 |
| **CRITICAL** | 잔여 분할 3건+, 진정한 God Object | 분할 필수 |

---

## Tier 1: RESOLVED (이미 분할 완료)

### 1. `stage4_interview_round.py` — 2,938줄, 32 메서드
- **분할 이력**: God-1~3 (run 782→404줄, _process_verdict 320→114줄, B-1-3b)
- **현재 구조**: run() 686줄 + advisory 11개(병렬) + setup 5개 + post-processing 3개
- **잔여**: 0~1건 (advisory를 별도 모듈로 추출 가능하나 ThreadPoolExecutor 병렬 구조상 이점 적음)
- **판정**: ✅ RESOLVED

### 2. `stage2_optimizer.py` — 1,213줄, 48 메서드 (8개 클래스)
- **구조**: StateSnapshotInjector / ArcAutoCorrector / NegativeConstraintAmplifier / FocusedFeedbackGenerator / FailureRecord / SessionFailureMemory / FewShotExampleManager / Stage2Optimizer
- **판정**: ✅ RESOLVED — 의도적 다중 클래스 설계, God Object 아님

### 3. `stage4_orchestrator.py` — 1,438줄, 18 메서드
- **분할 이력**: B-1-1~3 (2,481→883줄, -64%)
- **위임 대상**: stage4_post_processor, stage4_context_builder, stage4_interview_round
- **판정**: ✅ RESOLVED

### 4. `chief_writer.py` — 1,198줄, 44 메서드
- **분할 이력**: B-1-4~5 (2,255→854줄, -62%)
- **위임 대상**: chief_writer_context.py (1,295줄), chief_writer_quality.py (465줄)
- **판정**: ✅ RESOLVED

### 5. `stage3_orchestrator.py` — 1,253줄, 23 메서드
- **분할 이력**: DI 전환 완료 (19슬롯), lazy init 패턴
- **판정**: ✅ RESOLVED

### 6. `stage2_finalizer.py` — 1,570줄, 7 메서드
- **분할 이력**: B-1-7 분리 (stage2_orchestrator에서 추출)
- **판정**: ✅ RESOLVED

---

## Tier 2: MODERATE (잔여 분할 1~2건)

### 7. `stage2_preflight.py` — 1,261줄, 14 메서드
- **책임**: preflight 상태 설정(600줄) + arc 분석(150줄) + enrichment(300줄) + 컨텍스트 빌딩
- **잔여 기회**:
  1. `_preflight_state_setup()` + 4개 내부 함수 → `Stage2PreflightStateSetup` 클래스 (~450줄)
  2. `_preflight_arc_analysis()` + helpers → `Stage2ArcAnalyzer` 클래스 (~300줄)
- **리스크**: MEDIUM (내부 구현 리팩토링, 외부 API 불변)
- **판정**: ⚠️ MODERATE

### 8. `stage4_context_builder.py` — 1,685줄, 21 메서드
- **책임**: retrieval 계획 실행(500줄) + NPC roster 수집(200줄) + Continuity Packet(800줄) + 씬 유사도(300줄)
- **잔여 기회**:
  1. `ContinuityPacketBuilder` (~800줄, 엔티티 추출 + 패킷 생성)
  2. `ContextRetriever` (~500줄, retrieval plan 실행)
  3. `SceneSimilarityAdvisor` (~300줄, Python-only)
- **리스크**: MEDIUM (모듈 경계가 명확함)
- **판정**: ⚠️ MODERATE

### 9. `vec_memory.py` — 1,331줄, 40 메서드
- **책임**: 임베딩/캐싱(400줄) + 검색 전략(600줄, dense/keyword/hybrid/RRF) + 에피소드 저장(300줄) + 앵커 관리(200줄)
- **잔여 기회**:
  1. `HybridSearchEngine` (~600줄, knn + keyword + RRF)
  2. `EmbeddingCache` (~100줄)
- **리스크**: MEDIUM (검색 전략이 잘 분리됨)
- **판정**: ⚠️ MODERATE

### 10. `stage4_post_processor.py` — 1,301줄, 13 메서드
- **분할 이력**: B-1-9a (process_pass_result 813→238줄, -71%)
- **잔여 기회**:
  1. `StateChangeExtractor` (~200줄)
  2. `ManagerSubmitter` (~250줄, 비동기 제출)
- **리스크**: MEDIUM (상태 조정 순서 의존성)
- **판정**: ⚠️ MODERATE

---

## Tier 3: SIGNIFICANT (잔여 분할 2~3건)

### 11. `db_manager.py` — 2,840줄, 98 메서드
- **현재**: 단일 DBManager 클래스에 9~11개 무관한 도메인 집중
- **책임 목록**:
  | 카테고리 | 메서드 수 | 줄 수 |
  |----------|----------|-------|
  | 연결/트랜잭션 관리 | 15 | ~250 |
  | Manuscript/Blueprint CRUD | 6 | ~200 |
  | Bible/Lore 관리 | 15 | ~400 |
  | NPC 관계/이력 | 8 | ~300 |
  | Timeline/Arc 의존성 | 5 | ~150 |
  | FactLedger/Canonical Facts | 6 | ~250 |
  | 상태 로깅 | 5 | ~150 |
  | Karma 추적 | 3 | ~75 |
  | 롤백/동기화 | 10 | ~200 |
  | 비용/텔레메트리 | 8 | ~200 |
  | Director Selections | 6 | ~150 |
- **잔여 기회**:
  1. `NPCRelationshipStore` (~300줄, npc_relationship + npc_history)
  2. `TimelineStore` (~150줄, timeline_entries + arc_dependencies)
  3. `FactStore` (~250줄, canonical_facts + fact_ledger anchor)
  4. `TelemetryStore` (~200줄, cost_log + llm_calls + stage_attempts)
- **리스크**: MEDIUM-HIGH (SSOT 상태, db_repository protocol 동기화 필수)
- **주의**: DBManager는 현재 프로젝트 SSOT이므로 분할 시 `db_repository.py` protocol도 함께 변경 필요
- **판정**: ⚠️ SIGNIFICANT

### 12. `state_tracker_npc.py` — 2,201줄, 48 메서드
- **책임**: NPC 등록/추적(800줄) + 사망/스킬 검증(400줄) + 관계 추출(300줄) + 동행자 추적(350줄) + 감정(300줄)
- **잔여 기회**:
  1. `NPCDeathRegistry` (~200줄, 사망 등록/검증/추출)
  2. `NPCSkillRegistry` (~150줄, 스킬 등록/검증)
  3. `NPCCompanionTracker` (~350줄, 동행자 갱신/추적)
- **리스크**: MEDIUM (LLM 검증 interdependency)
- **판정**: ⚠️ SIGNIFICANT

### 13. `base_agent.py` — 1,875줄, 31 메서드
- **책임**: LLM 호출(800줄, ask + cached_context + model_stack) + JSON 파싱(300줄) + 컨텍스트 캐싱(150줄) + 텔레메트리(200줄)
- **잔여 기회**:
  1. `LLMRequestBuilder` (~400줄, 모델 스택 + 프롬프트 사이징 + 에러 분류)
  2. `JSONResponseParser` (~350줄, _extract_json_robust + _parse_and_repair_hard)
- **리스크**: MEDIUM-HIGH (순환 import 위험, key_rotation 공유 상태, 캐시 관리)
- **판정**: ⚠️ SIGNIFICANT

### 14. `state_tracker.py` — 1,668줄, 112 메서드
- **참고**: 112 메서드 중 **30+개가 state_tracker_npc.py로 위임** (forwarding methods)
- **실질 고유 책임**: 상태 생성/파싱(500줄) + 타임라인 검증(250줄) + 전환 계산(300줄) + 재무 추적(200줄) + 5종 registry summary(200줄)
- **잔여 기회**:
  1. `FinancialTracker` mixin (~200줄)
  2. `EntityTracker` mixin (~300줄)
- **리스크**: LOW-MEDIUM (mixin 패턴 이미 확립)
- **판정**: ⚠️ SIGNIFICANT (메서드 수 기준, 실질 복잡도는 MODERATE)

### 15. `four_phase_arc_generator.py` — 1,776줄, 14 메서드
- **숨은 복잡도**: `generate()` 메서드 **단일 1,022줄** (4개 Phase 순차 실행)
- **Phase 구조**:
  | Phase | 줄 수 | 내용 |
  |-------|-------|------|
  | Phase 1 (초기 경계) | ~150 | 블록 경계/에피소드 수 결정 |
  | Phase 2 (Arc 생성) | ~250 | LLM Arc 생성 + 검증 |
  | Phase 2.5 (교차 검증) | ~200 | NS-3-B + block_event_guard |
  | Phase 2.6 (Director 선택) | ~150 | Director compare_and_select_arc |
  | Phase 3-4 (후처리) | ~300 | 자동 보정 + EnsembleFB |
- **잔여 기회**:
  1. Phase 1 경계 계산 → `ArcBoundaryCalculator` (~150줄)
  2. Phase 2.5 교차 검증 → `BlockConstraintChecker` (~200줄)
  3. Phase 3-4 후처리 → `ArcPostProcessor` (~300줄)
- **리스크**: MEDIUM-HIGH (Phase 간 의존성 높음, 프롬프트 조립 복잡)
- **판정**: ⚠️ SIGNIFICANT

---

## Tier 4: CRITICAL (진정한 God Object)

### 16. `main_a.py` — 3,626줄, 92 메서드, class SovereignApp
- **진정한 God Object**: 8~9개 무관한 책임이 단일 클래스에 집중
- **책임 목록**:
  | 카테고리 | 메서드 수 | 줄 수 | 설명 |
  |----------|----------|-------|------|
  | 초기화/부트 | 15 | ~800 | 설정 로드, DB 초기화, 모델 검증 |
  | 프리셋/부트 관리 | 8 | ~300 | 장르 프리셋, 프로젝트 생성, 바이블 로드 |
  | 에이전트 부착 | 5 | ~400 | _init_core_agents, _init_v50_modules, lazy init |
  | Stage 0 헬퍼 | 8 | ~400 | NPC 등록, 문체 분석, 세계관 법칙 |
  | 피드백 생성 | 12 | ~500 | 전략 피드백, 가중치 주입, 히스토리 |
  | Stage 흐름 | 6 | ~800 | produce_episode, stage2→3→4 위임 |
  | 복구/유틸리티 | 38 | ~700 | 롤백, 상태 동기화, 버전 관리 |
- **분할 이력**: God-2에서 `_attach_agents()` 570→137줄 추출, 하지만 전체 3,626줄 중 일부에 불과
- **잔여 기회**:
  1. `BootSequence` (~500줄, 초기화 + DB + 모델) — MEDIUM 리스크
  2. `FeedbackGenerator` (~500줄, 전략 피드백 + 가중치 주입) — MEDIUM 리스크
  3. `StageFlowOrchestrator` (~400줄, Stage 2→3→4 위임) — HIGH 리스크 (핵심 경로)
  4. `RecoveryManager` (~300줄, 롤백 + 상태 동기화) — MEDIUM 리스크
- **리스크**: HIGH (진입점, 모든 의존성 교차점, 부트 시퀀스 부작용 복잡)
- **판정**: 🔴 CRITICAL — 코드베이스 유일의 진정한 God Object

---

## 요약 통계

| 등급 | 파일 수 | 총 줄 수 | 잔여 분할 기회 |
|------|---------|---------|--------------|
| RESOLVED | 6 | 8,871 | 0~3건 (전부 선택적) |
| MODERATE | 4 | 5,578 | 6~9건 |
| SIGNIFICANT | 5 | 10,162 | 12~17건 |
| CRITICAL | 1 | 3,626 | 3~4건 |
| **합계** | **16** | **28,237** | **21~33건** |

> 나머지 4개 파일 (analyst.py 1,680줄, chief_writer_context.py 1,295줄, validation_orchestrator.py 1,580줄, scoring_validator.py 1,272줄)은 각 1~2건 분할 가능하나 단일 책임에 가까워 MODERATE 하한.

---

## 분할 우선순위 권장

| 순위 | 대상 | 줄 수 | 기회 | 리스크 | 근거 |
|------|------|-------|------|--------|------|
| **1** | `main_a.py` SovereignApp | 3,626 | 3~4 | HIGH | 유일한 CRITICAL God Object, 8~9개 무관 책임 |
| **2** | `stage4_context_builder.py` | 1,685 | 2~3 | MEDIUM | CP/Retriever/SceneSim 3개 명확 경계 |
| **3** | `db_manager.py` DBManager | 2,840 | 3~4 | MEDIUM-HIGH | 98 메서드, 11개 도메인 혼합 |
| **4** | `four_phase_arc_generator.py` generate() | 1,776 | 2~3 | MEDIUM-HIGH | 단일 메서드 1,022줄, Phase별 분리 가능 |
| **5** | `state_tracker_npc.py` | 2,201 | 2~3 | MEDIUM | NPC 사망/스킬/동행자 분리 |
| **6** | `base_agent.py` | 1,875 | 1~2 | MEDIUM-HIGH | JSON 파서 분리 가치 있으나 순환 import 리스크 |
| **7** | `vec_memory.py` | 1,331 | 1~2 | MEDIUM | HybridSearch 엔진 분리 |

---

## 절대 하지 말 것

- `main_a.py` 분할 시 부트 시퀀스 순서를 변경하지 말 것 — 에이전트 lazy init, DB 초기화, 캐시 프라이밍 순서 의존
- `db_manager.py` 분할 시 `db_repository.py` protocol을 반드시 동기화할 것 — SSOT 위반 방지
- `base_agent.py` 분할 시 `key_rotation` 공유 상태와 `_model_stack` 캐시를 분리하지 말 것 — 경합 조건 유발
- 이미 RESOLVED인 6개 파일을 추가 분할하지 말 것 — 오케스트레이터 의미론 파괴 위험

---

## 참고: 기존 분할 이력 (CLAUDE.md 기준)

| 작업 | 원본 | 분할 결과 | 감소율 |
|------|------|-----------|--------|
| B-1-1~3 | stage4_orchestrator 2,481줄 | +post_processor +context_builder +interview_round | -64% |
| B-1-4~5 | chief_writer 2,255줄 | +chief_writer_context +chief_writer_quality | -62% |
| B-1-6~8 | stage2_orchestrator 2,639줄 | +validation_pipeline +finalizer +preflight | -66% |
| B-1-9 | 거대 함수 3개 | process_pass_result -71%, run_validation -83%, ask -57% | — |
| God-1 | interview_round.run() 782줄 | 404줄 + 5개 private 메서드 | -48% |
| God-2 | main_a._attach_agents() 570줄 | 137줄 + _init_core_agents/_init_v50_modules | -76% |
| God-3 | interview_round._process_verdict() 320줄 | 114줄 + 2개 private 메서드 | -64% |
