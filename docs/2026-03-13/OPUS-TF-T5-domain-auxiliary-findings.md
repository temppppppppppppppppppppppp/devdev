# OPUS TF Terminal 5 — 도메인 로직 & 보조 시스템 전량 조사 보고서

> **조사일**: 2026-03-13
> **범위**: Genre Guards 13개, 세계상태 6개, NPC/캐릭터 11개, 서사분석 9개, 지능전략 8개, 실패/피드백 4개, 기타 16개, API 6개, Desktop 4개 — 총 77개 모듈 + 관련 테스트 전량
> **방법론**: 6-Point Inspection (Null/None, 분기, 데이터흐름, 에러처리, 계약준수, 테스트갭)
> **5Pass 감리**: P1 4건 중 3건 오탐/경미화 판정, P2 핵심 10건 중 5건 오탐/경미화 판정

---

## 종합 통계 (5Pass 감리 후 확정)

| Severity | 감리 전 | 오탐/경미화 | **확정** | 설명 |
|----------|---------|-----------|---------|------|
| **P0-CRITICAL** | 0 | — | **0** | 런타임 크래시 / 데이터 손실 |
| **P1-IMPORTANT** | 4 | -3 (오탐2, 경미화1) | **1** | 기능 오동작 (silent wrong result) |
| **P2-MODERATE** | 36 | -4 (오탐2, 경미화2) + 1 (P1→P2) | **31** | 성능·관측성·유지보수 결함 |
| **P3-MINOR** | 53 | +6 (P1/P2 하향분) | **59** | 코드 위생 (동작 무영향) |
| **삭제** | — | +2 (완전 오탐) | — | ORDER BY 존재, setdefault 방어 |
| **합계** | **93** | | **91** | |

### 대원칙 준수 현황
- **대원칙 1** (Python 수집만, 판단은 LLM): 위반 0건. MartialManager 내공 강제 회복(T5-AUX-14)만 경계 사례 (P2).
- **대원칙 2** (팩트시트 수정은 LLM만): 준수. 모든 Python 갱신은 LLM state_changes 기반.
- **대원칙 3** (디렉터 주권): 위반 0건. Guard/Advisory 모두 보고만.
- **대원칙 4** (사망 캐릭터): WorldState 가드 완비. **FactLedger에 가드 부재** (T5-WS-016, P1).

---

## 5Pass 감리 결과 요약

### P1 감리 (4건 → 1건 확정)

| 원래 ID | 판정 | 근거 | 확정 등급 |
|---------|------|------|----------|
| T5-WS-016 FactLedger 사망NPC | **True Positive** | WorldState는 5개 섹션 전부 dead_npcs 가드, FactLedger는 0개. `_upsert_character`에서 기존 엔트리 있으면 status 보존되나, 엔트리 없는 상태에서 dead NPC 유입 시 alive 신규등록 | **P1 유지** |
| T5-NAR-05 foreshadow start_ep | **오탐** | `start_episode=0`과 `arc_no=0`은 "미설정" 센티널. 1-indexed 시스템에서 실제 0값 발생 불가. `0 or fallback`은 의도된 falsy 폴백 | P3 하향 |
| T5-INT-05 TreeOfThoughts | **오탐** | `explore_blueprint`는 호출자 0건 (dead code). 유일한 best_path 소비자는 `explore()` 사용 + `getattr` 방어 적용 | P3 하향 |
| T5-API-01 state enum | **경미화** | Contract YAML만 outdated. 프론트엔드가 state를 strict 검증하지 않음. `starting`은 수ms 과도상태로 관측 확률 극히 낮음. `waiting_input`은 WebSocket으로 대체됨 | P2 하향 |

### P2 핵심 감리 (10건 → 진짜 4건, 오탐 2건, 경미화 2건)

| 원래 ID | 판정 | 근거 | 확정 |
|---------|------|------|------|
| T5-GG-016 StyleGuard | **True Positive** | StyleGuard 반환 dict에 warning_violations/has_warning/warning_summary 키 전무. WorkGuard 경고 전량 소실 | P2 유지 |
| T5-NAR-08/09 "팽무진" | **True Positive** | 3곳에 하드코딩. protagonist_name 파라미터와 별도로 "팽무진" 추가 체크. 다른 작품에서 오동작 확실 | P2 유지 |
| T5-NAR-13 faction 전파 | **True Positive** | should_npc_know는 5단계(same_location/same_faction/isolated/nearby/distant), propagate_event는 3단계만. same_faction(1화→5화 지연)과 isolated(영구미전파→5화 전파) 모두 불일치 | P2 유지 |
| T5-API-03~05 contract | **True Positive** | 포트 8000→실제 8300, 에러코드 3개 미등재, 엔드포인트 4개 미등재 | P2 유지 |
| T5-WS-002/018 raw attrs | **경미화** | `get_npc_role_snapshot()`에 `isinstance(attr, dict)` 방어 존재. 크래시/데이터 손실 없음. prev/changed_ep 추적만 불가 | P3 하향 |
| T5-INT-03/04 None 전파 | **경미화** | generator_fn이 None 반환하는 실제 경로 미확인. 상위 호출부에서 None 체크 수행. 이론적 가능성만 | P3 하향 |
| T5-WS-003/004 rollback 정렬 | **오탐** | `db_manager.py` L1337: `ORDER BY ep_num` 명시 존재. 정렬 보장됨 | **삭제** |
| T5-INT-01/02 KeyError | **오탐** | `record_failure`에서 `setdefault(stage, defaultdict(int))` 방어. 실제 호출은 항상 stage 2/3/4 | **삭제** |

---

## P1 — IMPORTANT (확정 1건)

### [T5-WS-016] FactLedger 사망 NPC 재등록 경로 — 대원칙 4 관련
- **Severity**: P1
- **파일**: `modules/core/fact_ledger.py` L220-255
- **현상**: WorldState는 `npc_introductions`/`npc_personality_changes`/`npc_movements` 등 5개 섹션 전부에 `if name in dead_npcs: continue` 가드가 있으나, FactLedger의 `npc_movements`(L220)/`npc_personality_changes`(L231)/`npc_npc_relationships`(L246)/`npc_injuries`(L210)/`relationship_changes`(L157) **5개 섹션 전부** 사망 NPC 가드 없음.
- **실질 위험**: `_upsert_character`에서 기존 엔트리가 있으면 `status=None` 호출 시 dead 유지 (LOW). 그러나 ledger 리셋 후 또는 엔트리가 없는 상태에서 dead NPC가 유입되면 alive로 신규등록 (MEDIUM).
- **5Pass 검증**: WorldState L282/L334/L360/L387/L568/L592/L618에 가드 존재 확인. FactLedger에 0건 확인. **True Positive**.
- **수정안**: 5개 섹션에 `if chars.get(name, {}).get("status") == "dead": continue` 가드 추가.

---

## P2 — MODERATE (확정 31건)

### Genre Guards (5건)

| ID | 파일 | 요약 |
|----|------|------|
| T5-GG-001 | `fantasy_guard.py` L347 | `validate_v20_manuscript`에서 `_is_figurative_use()` 필터 누락 → 비유적 사용 오탐 |
| T5-GG-004 | `hunter_guard.py` L644 | `_compare_ranks` ValueError 시 0 반환 → 알 수 없는 등급=동등 판정 |
| T5-GG-014 | `work_guard.py` | `validate_v20_manuscript` 오버라이드 없음 → WuxiaGuard 현대표기 검사 래핑 시 미실행 |
| T5-GG-015 | `work_guard.py` L794 | `warning_violations` 키 반환 계약 불일치 (BaseGuard 미포함) |
| T5-GG-016 | `style_guard.py` L99 | WorkGuard warning_violations를 StyleGuard가 소실 → Director 작품 정체성 경고 누락 |

### WorldState / FactLedger / NPC (4건, 감리 후 3건 삭제/하향)

| ID | 파일 | 요약 |
|----|------|------|
| T5-WS-005 | `fact_ledger.py` L383 | `_upsert_character` status 누락 시 alive 고정 → T5-WS-016 연계 |
| T5-WS-006 | `fact_ledger.py` L129 | 처리 순서 의존 + npc_movements 사망NPC 가드 부재 → T5-WS-016 연계 |
| T5-WS-011 | `state_tracker.py` L187 | `full_extract_from_arcs` 핵심 4종 예외 시 전체 arc 중단 |
| T5-WS-020 | 테스트 전체 | `rollback_to` 테스트 부재 (핵심 데이터 경로) |

### 서사분석 (6건)

| ID | 파일 | 요약 |
|----|------|------|
| T5-NAR-03 | `information_diffusion.py` L51 | O(N) DB 호출 — 100화+ 시 100+ 쿼리 |
| T5-NAR-06 | `foreshadow_tracker.py` L431 | DELETE+INSERT 트랜잭션 부분 실패 시 rollback 의존 |
| T5-NAR-08 | `semantic_item_registry.py` L553 | **"팽무진" 하드코딩** → 다른 작품에서 주인공 아이템 누락 |
| T5-NAR-09 | `semantic_item_registry.py` L451 | T5-NAR-08과 동일 "팽무진" 하드코딩 |
| T5-NAR-13 | `information_diffusion.py` L392 | **`propagate_event`에 same_faction/isolated 전파 누락** (should_npc_know 5단계 vs propagate_event 3단계 불일치) |
| T5-NAR-17 | `semantic_item_registry.py` L785 | 싱글톤 프로젝트 간 공유 → 크로스프로젝트 오염 |

### 기타 보조모듈 (9건)

| ID | 파일 | 요약 |
|----|------|------|
| T5-AUX-01 | `adversarial_self_play.py` L267 | 빈 dict → 빈 JSON 문자열이 adversary loop 진입 |
| T5-AUX-05 | `cross_agent_verifier.py` L396 | 원고 8K 절삭 → 엔딩훅 포함 후반부 누락 |
| T5-AUX-06 | `data_collector.py` L183 | `create_training_pair` thread-safety 없음 |
| T5-AUX-07 | `data_collector.py` L96 | stats 카운터 lock 밖에서 갱신 |
| T5-AUX-10 | `reference_anchor.py` L104 | BaseAgent private 메서드 `_extract_json_robust` 호출 |
| T5-AUX-14 | `martial_manager.py` L369 | 내공 강제 회복 — 대원칙 1 경계 사례 |
| T5-AUX-15 | `martial_manager.py` L409 | `save_v20_anchor` 존재 미검증 → AttributeError 위험 |
| T5-AUX-16 | `lore_manager.py` L209 | DBManager cursor 직접 접근 → lock 우회 |
| T5-AUX-18 | `quality_sidecar_bootstrap.py` L113 | DB `_lock`/`conn.cursor()` private 멤버 직접 접근 |
| T5-AUX-19 | `investment_arithmetic_checker.py` L303 | 배열 길이 불일치 시 불완전 거래 현금 합산 반영 |

### API / Desktop (7건, +1 P1→P2 하향분)

| ID | 파일 | 요약 |
|----|------|------|
| T5-API-01 | `process_runner.py` L39 / `api-contract-v1.yaml` L173 | ★5Pass P1→P2: State enum 불일치 (contract outdated, 기능 무영향) |
| T5-API-02 | `geuldobi-desktop/src/main.js` L192 | startupTimer 미정리 → 백엔드 즉사 시 15초 후 null 참조 |
| T5-API-03 | `api-contract-v1.yaml` L6 | **포트 8000 vs 실제 8300** 불일치 |
| T5-API-04 | `api-contract-v1.yaml` L190 | 프로덕션 에러코드 3개 (`INTERNAL_ERROR`/`INVALID_REQUEST`/`INVALID_PROJECT`) contract 미등재 |
| T5-API-05 | `api-contract-v1.yaml` | 프로덕션 엔드포인트 4개 (`/quality/summary`/`/quality/dashboard`/`/safe-ops/preview`/`/quality/review`) contract 미등재 |
| T5-API-06 | `bridge_server.py` L605 | DBManager private `_director_stage_predicate` 호출 + raw SQL |
| T5-API-07 | `geuldobi-desktop/main.js` | 구버전 dead file (src/main.js와 중복, WorkGuard 기능 누락) |

---

## P3 — MINOR (확정 59건, 주요 항목만 요약)

### 5Pass에서 P1/P2→P3 하향된 항목 (6건)
| 원래 ID | 원래 등급 | 하향 사유 |
|---------|----------|----------|
| T5-NAR-05 foreshadow start_ep | P1 | 0=미설정 센티널, 1-indexed 시스템에서 실발생 불가 |
| T5-INT-05 TreeOfThoughts best_path | P1 | explore_blueprint 호출자 0건 (dead code) |
| T5-WS-002/018 npc_introductions raw | P2 | isinstance(attr, dict) 방어 존재, 크래시 없음 |
| T5-INT-03/04 DiversitySampler None | P2 | generator_fn None 반환 경로 미확인, 이론적 가능성만 |

### 테스트 커버리지 갭 (15건)
| 모듈 | 전용 테스트 |
|------|------------|
| HunterGuard V57 메서드 (던전/각성) | 없음 |
| InvestmentGuard V57 메서드 (투자규모/수익률) | 없음 |
| WorldState/FactLedger `rollback_to` | 없음 |
| EmotionArcTracker | 없음 |
| CharacterVoiceTracker/Profiler | 없음 |
| StateDeltaTracker | 없음 |
| NarrativeDiversityEngine | 없음 |
| InformationDiffusion | 없음 |
| PacingAnalyzer | 없음 |
| AgentIntelligence | 없음 |
| DiversitySampler | 없음 |
| TreeOfThoughts | 없음 |
| ContextCompression | 없음 |
| ExpertMixture / DynamicPromptWeighting | 없음 |
| bridge_server HTTP 통합 테스트 | 없음 |

### 코드 위생 (주요 패턴)
- 미사용 표현식: `base_guard.py` L647, `feedback_system.py` L109/L762, `power_scaling.py` L358, `reference_anchor.py` L180
- 중복: `wuxia_guard.py` "근섬유" 2중 등록, `base_guard.py` L671/681 `npc_name_esc` 중복 선언
- 하드코딩 모델명: `multi_agent_deliberation.py` L184 (`"gemini-2.5-flash"` 리터럴 vs AIModels 상수)
- 직접 Gemini import: `narrative_structure_analyzer.py` L18 (`from google.genai import types`)
- 문서 부정확: CLAUDE.md "truth_gate.py P2 메타용어 감지" → 실제는 `chief_writer_quality.py`
- CLAUDE.md "14파일 21곳 protagonist_items 폴백" → 실제 **18파일 35곳**

### 5Pass에서 삭제된 오탐 항목 (2건)
| 원래 ID | 삭제 사유 |
|---------|----------|
| T5-WS-003/004 rollback_to 정렬 | `db_manager.py` L1337에 `ORDER BY ep_num` 명시 존재 |
| T5-INT-01/02 FailureLearner KeyError | `record_failure`에서 `setdefault` 방어 + 실제 호출 항상 stage 2/3/4 |

---

## 특별 조사: protagonist_items 폴백 전수 확인

| 항목 | CLAUDE.md | 실제 |
|------|-----------|------|
| 폴백 패턴 적용 | 14파일 21곳 | **18파일 35곳** |
| 폴백 누락 (위험) | — | **2건** |
| 폴백 누락 (확인필요) | — | 1건 |

**누락 2건:**
1. `modules/domain/agents/constraint_compiler.py` L104 — `items_acquired`만 읽음
2. `modules/domain/agents/negative_example_injector.py` L262 — `items_acquired`만 읽음

---

## 특별 조사: 비무협 장르 오염 3단 방어

| 방어 단계 | 상태 | 비고 |
|-----------|------|------|
| 1단: genre_schema_builder | 10종 전량 커버 | 빈틈 없음 |
| 2단: analyst._build_genre_placeholders | 10종 전량 커버 | 빈틈 없음 |
| 3단: 메타용어 감지 | **CLAUDE.md 부정확** | truth_gate가 아닌 chief_writer_quality._check_system_term_exposure()가 전담 |

실질적 방어 공백: **없음** (3단은 모듈만 다르고 방어 자체는 작동)

---

## 액션 플랜 (5Pass 감리 후 확정)

### 즉시 수정 권장 (P1 확정 1건)

| 우선순위 | ID | 작업 | 예상 난이도 |
|---------|-----|------|-----------|
| 1 | T5-WS-016 | FactLedger 사망NPC 가드 5개 섹션 추가 | 낮음 |

### 단기 수정 권장 (P2 핵심 6건)

| 우선순위 | ID | 작업 | 난이도 |
|---------|-----|------|--------|
| 1 | T5-GG-016 | StyleGuard warning_violations 전파 | 낮음 |
| 2 | T5-NAR-08/09 | "팽무진" 하드코딩 제거 (protagonist_name 활용) | 낮음 |
| 3 | T5-NAR-13 | propagate_event에 same_faction/isolated 분기 추가 | 중간 |
| 4 | T5-API-03~05 | api-contract-v1.yaml 현행화 (포트/에러코드/엔드포인트) | 낮음 |
| 5 | T5-API-01 | contract state enum 동기화 (starting 추가, waiting_input 제거) | 낮음 |
| 6 | T5-WS-020 | rollback_to 단위 테스트 추가 | 중간 |

### 문서 갱신

| 항목 | 변경 |
|------|------|
| CLAUDE.md protagonist_items | "14파일 21곳" → "18파일 35곳" |
| CLAUDE.md 비무협 3단 방어 | "truth_gate.py P2" → "chief_writer_quality.py _check_system_term_exposure()" |

---

## 5Pass 감리 기록

### Pass 1 — P1 4건 개별 코드 대조
- [x] T5-WS-016: WorldState 7곳 가드 vs FactLedger 0곳 확인 → **True Positive**
- [x] T5-NAR-05: 0=센티널, 1-indexed 시스템, 의도된 falsy 폴백 → **오탐 (P3)**
- [x] T5-INT-05: explore_blueprint 호출자 0건, explore()만 사용 + getattr 방어 → **오탐 (P3)**
- [x] T5-API-01: contract outdated, 프론트엔드 strict 검증 없음 → **경미화 (P2)**

### Pass 2 — P2 핵심 10건 코드 대조
- [x] T5-GG-016: StyleGuard 반환 dict에 warning 키 전무 확인 → **True Positive**
- [x] T5-WS-002/018: isinstance(attr, dict) 방어 존재 확인 → **경미화 (P3)**
- [x] T5-WS-003/004: db_manager.py ORDER BY ep_num 확인 → **오탐 (삭제)**
- [x] T5-NAR-08/09: 3곳 하드코딩 확인, protagonist_name과 별도 체크 → **True Positive**
- [x] T5-NAR-13: 5단계 vs 3단계 불일치 확인 → **True Positive**
- [x] T5-INT-01/02: setdefault 방어 + stage 2/3/4 고정 확인 → **오탐 (삭제)**
- [x] T5-INT-03/04: None 반환 경로 미확인 → **경미화 (P3)**
- [x] T5-API-03~05: 포트/에러코드/엔드포인트 불일치 확인 → **True Positive**

### Pass 3 — 종합 통계 재계산
- [x] P1: 4→1, P2: 36→31 (+1 P1 하향), P3: 53→59 (+6 하향), 삭제: 2건

### Pass 4 — 액션 플랜 정합성
- [x] 삭제/하향 항목이 액션 플랜에서 제거 확인
- [x] 확정 P1/P2 항목이 액션 플랜에 반영 확인
- [x] 문서 갱신 항목 2건 유지

### Pass 5 — 최종 검수
- [x] 모든 ID가 본문과 액션 플랜에서 일관성 있게 사용됨
- [x] 감리 근거가 코드 라인 번호와 함께 기록됨
- [x] 오탐 판정 근거가 재현 가능한 수준으로 상세함
- [x] 대원칙 위반 현황이 감리 결과를 반영하여 정확함

---

*Terminal 5 조사 종료. P0 0건, P1 확정 1건. 5Pass 감리 완료.*
