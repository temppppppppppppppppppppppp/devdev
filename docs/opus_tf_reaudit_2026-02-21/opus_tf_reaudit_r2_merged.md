# Opus TF 전 스테이지 재감리 R2 통합 보고서

**Date**: 2026-02-21
**Auditor**: Opus TF R2 (5 parallel agents)
**Commit baseline**: `e8b2a48` (이전 감사 24건 수정 완료 후)

---

## 1. Executive Summary

| Stage | CRITICAL | IMPORTANT | INSIGHT | Total |
|-------|----------|-----------|---------|-------|
| Stage 0/1 | 0 | 2 | 6 | 8 |
| Stage 2 | 0 | 2 | 5 | 7 |
| Stage 3 | 0 | 1 | 7 | 8 |
| Stage 4 | 0 | 4 | 8 | 12 |
| Cross-cutting | 0 | 2 | 8 | 10 |
| **Total** | **0** | **11** | **34** | **45** |

### Top 3 Clusters

1. **Sync/Parallel 검증 경로 불일치** (R2-XC-01, R2-XC-03): sync `validate()` 경로에 adaptive threshold 계산과 validation history 기록이 누락되어, sync/parallel 경로 간 일관성 없는 점수 판정
2. **데이터 소스 오정렬** (R2-S4-01, R2-S01-01, R2-S2-12): 벡터 메모리의 state_changes 소스 오류, episode_bibles 인덱스 오정렬, financial_number_registry 롤백 누락
3. **StateTracker 롤백 누락** (R2-S2-11, R2-S2-12): `four_phase_asp` 생성 방식에서 롤백 스킵, 투자 장르 financial_registry 롤백 누락

---

## 2. 이전 감사 수정 — Regression Check

### 전량 검증 완료 (24건 수정 + 2건 스킵)

| ID | Title | Status |
|----|-------|--------|
| S2-01 | Director crash fallback auto-PASS | ✅ Fix verified |
| S2-02 | StateTracker rollback snapshot registry | ✅ Fix verified |
| S2-03 | check_new_arc() 중복 호출 | ✅ Fix verified |
| S2-04 | Jaccard 전용 임계값 분리 | ✅ Fix verified |
| S2-05 | NegativeExampleInjector 읽기 lock | ✅ Fix verified |
| S2-06 | PreflightChecker json.loads → _extract_json_robust | ✅ Fix verified |
| S3-01 | 연속성 REJECT 시 stats/_previous_best 미갱신 | ✅ Fix verified |
| S3-02 | _handle_failure 순차 의존성 파괴 | ✅ Fix verified |
| S3-04 | feedback retry간 누적 | ✅ Fix verified |
| S3-09 | PASS_WITH_WARNING Director REJECT 오버라이드 | ✅ Fix verified |
| S3-10 | _escape_braces not on pov_constraint | ✅ Fix verified |
| S3-11 | score_breakdown 미반환 | ✅ Fix verified |
| S4-01 | CoVe REJECT 시 state_updates 소실 | ✅ Fix verified |
| S4-02 | WorldState/FactLedger arc_data.state_changes 사용 | ⚠️ **Partial** — WorldState/FactLedger 수정 OK, 벡터 메모리 블록 누락 → R2-S4-01 |
| S4-07 | 품질 회귀 감지 stage=2 하드코딩 | ✅ Fix verified |
| XC-01 | validate() sync 경로 adaptive threshold 미적용 | ✅ Fix verified (상수 추출 완료, 그러나 R2-XC-01에서 더 넓은 이슈 발견) |
| XC-04 | ContinuityValidator 현재 HUD→이전 HUD 폴백 | ✅ Fix verified |
| XC-05 | BaseAgent _init_api_keys TOCTOU | ✅ Fix verified |
| XC-07 | WorldState.last_updated_ep int/str 혼합 | ✅ Fix verified |
| XC-10 | relation_dynamics 위반 항상 justifiable | ✅ Fix verified |
| XC-14 | Parallel PASS threshold hardcoded 85 | ✅ Fix verified |
| S01-01 | arcs_anchor dict 분기 dead code | ✅ Fix verified |
| S01-03 | Self-critic revised_arc 미사용 | ✅ Fix verified |
| S01-04 | story_expander 빈 Bible 검증 게이트 | ✅ Fix verified |
| S01-02 | persist_to_vectordb ep_num-1 인덱싱 | ⚠️ **재분류** — FALSE ALARM 아님, 실제 버그 → R2-S01-01 |
| XC-03 | PreLLMValidator always passed=True | ✅ 의도적 설계 확인 (대원칙 #1) |

---

## 3. IMPORTANT Findings (11건)

### Stage 0/1

#### R2-S01-01. persist_to_vectordb episode_bibles 인덱스 오정렬

- **File**: `modules/core/stage0/reverse_expander.py:453-454`
- **TF**: TF-2 (데이터 흐름)
- **Content**: `episode_bibles[ep_num - 1]`로 접근하지만, `episode_bibles` 리스트는 `raw_drafts` 순회 순서로 생성되어 인덱스 `i`에 대응. 에피소드 번호가 1이 아닌 번호에서 시작하면 잘못된 episode_bible 참조.
- **Impact**: 벡터 DB에 잘못된 NPC/아이템 causal_links 저장 (cross-episode 데이터 오염)
- **Fix**: 동일 파일 L896의 올바른 패턴(`{eb.get("ep_num"): eb for eb in self.episode_bibles}` dict 맵)으로 교체
- **Difficulty**: LOW

#### R2-S01-02. analyst.py genre_library_map에 alt_history 누락

- **File**: `modules/domain/agents/analyst.py:1414-1422`
- **TF**: TF-5 (도메인)
- **Content**: `genre_library_map`에 `"alt_history"` 엔트리 없음. `config/prompts/analyst_libraries_alt_history.json` 파일은 존재하지만 무협 기본 라이브러리로 폴백.
- **Impact**: 대체역사 장르 Arc 설계 시 전용 28개 narrative archetype 미사용, 무협 패턴 참조
- **Fix**: `"alt_history": "analyst_libraries_alt_history.json"` 1줄 추가
- **Difficulty**: LOW

### Stage 2

#### R2-S2-11. StateTracker rollback skipped for `four_phase_asp`

- **File**: `modules/core/stage2_finalizer.py:483`
- **TF**: TF-2 (데이터 흐름)
- **Content**: 롤백 조건이 `generation_method == "four_phase"`인데, ASP 적용 시 `"four_phase_asp"`로 변경되어 롤백 스킵. REJECT된 Arc의 NPC 사망/스킬/관계 팬텀 데이터 잔류.
- **Impact**: 재시도 시 팬텀 NPC 사망, 중복 스킬 경고 등 StateTracker 오염
- **Fix**: `generation_method == "four_phase"` → `generation_method.startswith("four_phase")`
- **Difficulty**: LOW

#### R2-S2-12. Investment genre financial_number_registry 롤백 누락

- **File**: `modules/core/stage2_preflight.py:601-623, 652-656`
- **TF**: TF-2 (데이터 흐름), TF-5 (도메인)
- **Content**: StateTracker 스냅샷에 `financial_number_registry` 미포함 + 즉시 DB 저장으로 REJECT 시 팬텀 재무 데이터 잔류.
- **Impact**: 투자 장르 한정 — 재시도 시 잘못된 환율/자산/레버리지 데이터 참조
- **Fix**: 스냅샷에 `financial_number_registry` 추가 + DB 저장을 Director PASS 이후로 이동
- **Difficulty**: MEDIUM

### Stage 3

#### R2-S3-01. director_ensemble scene_breakdown list 타입 미처리

- **File**: `modules/domain/agents/director_ensemble.py:212-213`
- **TF**: TF-2 (데이터 흐름), TF-3 (검증 정확성)
- **Content**: `scene_breakdown`이 list일 때 `isinstance(_sb, dict)` 실패 → `scene_count = 0` → 정상 Blueprint를 "씬 부족"으로 REJECT.
- **Impact**: 단일 후보 평가/LLM 비교 실패 폴백 경로에서 list 타입 Blueprint 무조건 REJECT
- **Fix**: `isinstance(_sb, (dict, list))` 로 변경
- **Difficulty**: LOW

### Stage 4

#### R2-S4-01. 벡터 메모리 state_changes 소스 오류 (S4-02 잔여)

- **File**: `modules/core/stage4_post_processor.py:166`
- **TF**: TF-2 (데이터 흐름)
- **Content**: 벡터 메모리의 event_types/entity_names가 Arc 계획 단계의 `arc_data.state_changes`에서 추출됨. 실제 에피소드 산출물인 `final_state_updates`를 사용해야 함.
- **Impact**: 벡터 검색 시 부정확한 이벤트 태깅 → 맥락 검색 품질 저하
- **Fix**: `_sc_raw = final_state_updates or {}` 로 변경
- **Difficulty**: LOW

#### R2-S4-02. writer_prompt_builders 저지위 키워드 감지 dead code

- **File**: `modules/core/writer_prompt_builders.py:69-72`
- **TF**: TF-3 (검증 정확성)
- **Content**: `low_status_keywords` 매치 후 반드시 `reputation` 필드 파싱 필요 → reputation 없으면 `low_status_high_authority` 제약 절대 미등록 (키워드 감지가 사실상 dead code).
- **Impact**: 저지위 캐릭터의 권위 비약 서사가 제한되지 않음
- **Fix**: 키워드 매치와 reputation 매치를 독립 조건으로 분리
- **Difficulty**: LOW

#### R2-S4-03. REJECT 경로에서 시스템 감지 피드백 소실

- **File**: `modules/core/stage4_interview_round.py:681-683`
- **TF**: TF-2 (데이터 흐름)
- **Content**: REJECT 시 `director_feedback`가 현재 라운드 내용으로 완전 교체. 이전 라운드의 연속성 충돌 경고/V67 모순 경고 등 시스템 감지 피드백 소실.
- **Impact**: 다음 라운드에서 이전에 감지된 구조적 문제가 반복될 수 있음
- **Fix**: 시스템 감지 라인(`[연속성 충돌]`, `[V67]`, `[CoVe]`)만 보존하여 append
- **Difficulty**: MEDIUM

#### R2-S4-04. Interview round 30화 원고 중복 DB 조회

- **File**: `modules/core/stage4_interview_round.py:442-452`
- **TF**: TF-4 (아키텍처)
- **Content**: `stage4_context_builder`에서 이미 로드한 30화 원고를 interview_round에서 다시 개별 DB 조회. 에피소드당 최대 30회 불필요 I/O.
- **Impact**: 성능 저하 (기능 정확성 문제 아님)
- **Fix**: `_RoundContext`에 `prev_manuscripts_list` 추가하여 재사용
- **Difficulty**: MEDIUM

### Cross-cutting

#### R2-XC-01. Sync validate() 경로에 adaptive threshold 계산 누락

- **File**: `modules/validation/validation_orchestrator.py:209-560`
- **TF**: TF-3 (검증 정확성)
- **Content**: sync `validate()` 메서드에서 `calculate_adaptive_threshold_v59()` 미호출. 정적 base threshold만 사용. parallel 경로와 다른 기준으로 판정.
- **Impact**: sync 경로 사용 시 (director_auditor, batch_validator, fallback) adaptive threshold 미적용
- **Fix**: sync `validate()` 시작부에 adaptive threshold 계산 추가
- **Difficulty**: MEDIUM

#### R2-XC-03. Sync validate()가 validation history 미기록

- **File**: `modules/validation/validation_orchestrator.py:209-560`
- **TF**: TF-3 (검증 정확성)
- **Content**: sync 경로에서 `_record_validation_history_v59()` 미호출. consecutive_passes/fails 미갱신, validation_history 미축적.
- **Impact**: R2-XC-01과 결합 — sync 경로가 adaptive behavior에서 완전히 단절
- **Fix**: sync `validate()` 반환 전에 history 기록 추가
- **Difficulty**: LOW

---

## 4. INSIGHT Findings (34건)

<details>
<summary>전체 INSIGHT 목록 (접기/펼치기)</summary>

### Stage 0/1 (6건)

| ID | Title | 비고 |
|----|-------|------|
| R2-S01-03 | reverse_expander._extract_npcs dict 반환 가능 | list 래핑 미적용 (S01-06 재확인) |
| R2-S01-04 | generate_from_concept Bible 실패해도 Treatment 생성 진행 | 불필요 LLM 비용 + 고아 파일 |
| R2-S01-05 | Block 확장/스타일 분석에서 Enter 2회 요구 | UX 불편 (S01-05 재확인) |
| R2-S01-06 | style_extractor._llm_call 모델명 하드코딩 | AIModels 상수 미사용 |
| R2-S01-07 | reverse_expander._extract_protagonist list 반환 시 크래시 | LLM이 list 응답하면 AttributeError |
| R2-S01-08 | VecMemory lock=None | No longer an issue — _db_lock() graceful no-op |

### Stage 2 (5건)

| ID | Title | 비고 |
|----|-------|------|
| R2-S2-13 | _stage2_flow_guard NarrativeStructureAnalyzer 매 validation 재생성 | 불필요 LLM 비용 |
| R2-S2-14 | ArcDraftValidator.validate() 2회 호출 (constraint_block 유/무) | 약한 1차 + 강한 2차, 중복 연산 |
| R2-S2-15 | Quality gate가 short tactical_doc (< 1500 chars)에서 바이패스 | 다층 검증으로 영향 제한적 |
| R2-S2-16 | SemanticPlotGuard Jaccard-like ratio 짧은 키워드셋 오탐 가능 | advisory only, 노이즈만 증가 |
| R2-S2-17 | _compute_preflight None vs {} 센티널 불일치 | 기능 영향 없음, 가독성 이슈 |

### Stage 3 (7건)

| ID | Title | 비고 |
|----|-------|------|
| R2-S3-02 | phase1_complete stats 인플레이션 | 통계 정확성만 (S3-03 재확인) |
| R2-S3-03 | Quality Gate REJECT 시 feedback 유실 | score_breakdown으로 보완됨 |
| R2-S3-04 | 연속성 REJECT 시 _prev_reject_strategy 미갱신 | 연속성은 전략 독립적 |
| R2-S3-05 | PASS_WITH_WARNING 경로 Pydantic 검증 미적용 | graceful degradation으로 영향 미미 |
| R2-S3-06 | 연속성 검사 best_blueprint만 대상 | 전략 독립적 위치 연속성 (S3-08 재확인) |
| R2-S3-07 | _build_reader_feedback_context thread 내 DB 접근 | check_same_thread=False + try/except로 안전 |
| R2-S3-08 | _handle_success 무결성/커밋 실패 시 break 미설정 | 다음 사이클에서 즉시 차단됨 |

### Stage 4 (8건)

| ID | Title | 비고 |
|----|-------|------|
| R2-S4-I01 | error 후보가 Director에 도달 가능 | 불필요 LLM 비용 |
| R2-S4-I02 | CoVe REJECT 시 Director 피드백 완전 교체 | 의도적 설계 가능 (S4-04 재확인) |
| R2-S4-I03 | truncation 패턴 비-bracket 헤더 미분리 | fallback truncation 발동 (S4-12 재확인) |
| R2-S4-I04 | cumulative_bible 수집 후 미활용 | dead_npcs 외 사장 (S4-09 재확인) |
| R2-S4-I05 | Writer fallback _escape_braces 후 슬라이싱 순서 | 원본 기준보다 적은 텍스트 포함 |
| R2-S4-I06 | EMPTY 경로 previous_attempt에 best_manuscript 미포함 | 빈 문자열 폴백으로 동작 정상 |
| R2-S4-I07 | 5회 소진 시 비대화형 모드 자동 건너뛰기 | _choice=2 고정 |
| R2-S4-I08 | _count_recent_cliches 현재 원고 합산 | 임계값 false positive 미미 |

### Cross-cutting (8건)

| ID | Title | 비고 |
|----|-------|------|
| R2-XC-02 | VecMemory nested lock (safe with RLock) | 설계상 안전 |
| R2-XC-04 | WorldState._INIT_STATE mutable class variable | deep-copy 사용으로 안전 |
| R2-XC-05 | FactLedger rollback state_changes + full bible 이중 처리 | idempotent upsert로 안전 |
| R2-XC-06 | VecMemory standalone mode 무 lock | 테스트 전용 |
| R2-XC-07 | RETROSPECTIVE REJECT result keys 일부 누락 | .get() 사용으로 안전 |
| R2-XC-08 | PreLLM early REJECT dead code | 대원칙 #1 의도 (XC-02/XC-03 재확인) |
| R2-XC-09 | WorldState.update_from_state_changes 단일 exception wrapper | 부분 실패 시 전체 스킵 |
| R2-XC-10 | DBManager 단일 공유 cursor + RLock | 설계 선택, 안전 |

</details>

---

## 5. 이전 감사 대비 변동표

| Category | R1 (이전) | R2 (현재) | Notes |
|----------|-----------|-----------|-------|
| CRITICAL | 2 | 0 | 전량 수정 완료, regression 없음 |
| IMPORTANT | 20 | 11 | 이전 20건 전량 수정 (1건 partial → R2-S4-01), 신규 11건 발견 |
| INSIGHT | 34 | 34 | 이전 INSIGHT 대부분 재확인, 신규 교체 |
| **Total** | **56** | **45** | CRITICAL 0건 달성 |

---

## 6. 도메인별 교차 참조 매트릭스

| 렌즈 | CRITICAL | IMPORTANT | INSIGHT |
|------|----------|-----------|---------|
| TF-1 LLM 상호작용 | 0 | 0 | 5 (R2-S2-13, R2-S2-14, R2-S4-I03, R2-S4-I05, R2-S01-06) |
| TF-2 데이터 흐름 | 0 | 6 (R2-S01-01, R2-S4-01, R2-S2-12, R2-S4-03, R2-S3-01, R2-S2-11) | 12 |
| TF-3 검증 정확성 | 0 | 3 (R2-XC-01, R2-XC-03, R2-S4-02) | 5 |
| TF-4 아키텍처 | 0 | 1 (R2-S4-04) | 8 |
| TF-5 도메인 | 0 | 1 (R2-S01-02) | 4 |

---

## 7. 우선순위 Tier 분류

### Tier 1 — 즉시 수정 (데이터 정확성 직접 영향)

| # | ID | Title | Difficulty |
|---|-----|-------|-----------|
| 1 | R2-S01-02 | analyst.py genre_library_map에 alt_history 누락 | LOW |
| 2 | R2-S4-01 | 벡터 메모리 state_changes 소스 오류 | LOW |
| 3 | R2-S2-11 | StateTracker rollback skipped for four_phase_asp | LOW |
| 4 | R2-S3-01 | director_ensemble scene_breakdown list 미처리 | LOW |

### Tier 2 — 다음 스프린트 (정확성/일관성 개선)

| # | ID | Title | Difficulty |
|---|-----|-------|-----------|
| 5 | R2-XC-01 | Sync validate() adaptive threshold 누락 | MEDIUM |
| 6 | R2-XC-03 | Sync validate() validation history 미기록 | LOW |
| 7 | R2-S01-01 | episode_bibles 인덱스 오정렬 | LOW |
| 8 | R2-S4-02 | 저지위 키워드 감지 dead code | LOW |

### Tier 3 — 품질 개선 (가치 있지만 긴급하지 않음)

| # | ID | Title | Difficulty |
|---|-----|-------|-----------|
| 9 | R2-S2-12 | Investment genre financial_registry 롤백 누락 | MEDIUM |
| 10 | R2-S4-03 | REJECT 시 시스템 감지 피드백 소실 | MEDIUM |
| 11 | R2-S4-04 | 30화 원고 중복 DB 조회 | MEDIUM |

---

## 8. 감사 범위

| Stage | 파일 수 | 총 줄수 |
|-------|---------|---------|
| Stage 0/1 | 6 | ~4,500 |
| Stage 2 | 8 | ~4,800 |
| Stage 3 | 6 | ~4,200 |
| Stage 4 | 10 | ~6,500 |
| Cross-cutting | 16 | ~10,700 |
| **Total** | **46** | **~30,700** |
