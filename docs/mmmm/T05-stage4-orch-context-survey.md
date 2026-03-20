# T05 — Stage 4 Core Orchestration Survey

**6PASS-CLEARED** | COLLECTOR ONLY | NO EXECUTION AUTHORITY

**Terminal**: T05
**영역**: Stage 4 Core Orchestration
**Date**: 2026-03-20
**Baseline Commit**: `d0fa70f1`
**Confidence**: 96%

---

## 1. Scope & Files

| 파일 | 라인 수 | 역할 |
|------|---------|------|
| `modules/core/stage4_orchestrator.py` | 1,757 | Stage4 메인 루프, 면담 결과 처리, 에스컬레이션 |
| `modules/core/stage4_context.py` | 271 | Stage4Context DI 컨텍스트 (30 __slots__) |
| `modules/core/stage4_context_builder.py` | 2,975 | 에피소드 컨텍스트 수집, 프롬프트 조립, budget 관리 |
| `modules/core/stage4_types.py` | 91 | _RoundContext(36필드), _InterviewRoundResult, WritingDirective |
| `modules/core/stage4_canary_tools.py` | 936 | 카나리 프로젝트 준비/분석 (스크립트/테스트 전용) |
| **합계** | **6,030** | |

**관련 테스트 4파일 (221 tests):**
- `tests/test_stage4_orchestrator.py` (1,337 lines, 61 tests)
- `tests/test_stage4_context_builder.py` (1,664 lines, 105+ tests)
- `tests/test_stage4_context.py` (391 lines, 30 tests)
- `tests/test_stage4_cv_context.py` (567 lines, 25 tests)

---

## 2. TF Registry

### P2-MEDIUM (3건)

#### T05-TF-001 — Stage4Context Docstring DRIFT (확장 슬롯 수 불일치)
```
ID: T05-TF-001
Severity: P2-MEDIUM
Category: DRIFT
Surface: modules/core/stage4_context.py:34-38
Evidence:
  - stage4_context.py:34-38 docstring:
    "[4C-2b] 확장 13종: memory, world_state, fact_ledger, character_voice,
     perf_timer, foreshadow_tracker, failure_learner, diversity_engine,
     semantic_plot_guard, selected_genre, quality_dashboard,
     pacing_analyzer, pass_rate_monitor"
  - stage4_context.py:56 실제 __slots__: `"context_advisor"` — docstring 누락
  - stage4_context.py:69 실제 __slots__: `"emotion_tracker"` — docstring 누락 (주석: [TF7-P2-06])
  - 실제 확장 슬롯 = 15종 (docstring 기재 13 + context_advisor + emotion_tracker)
Inference: 후속 패치(context_advisor 추가, TF7-P2-06 emotion_tracker 추가) 시 docstring 갱신 누락.
  리팩터링 시 슬롯 수를 docstring 기준으로 세면 2개 누락 위험.
Uncertainty: 없음 — 코드 직접 확인
Cross-Ref: T01 (app write-back에서 emotion_tracker 전달 여부)
```

#### T05-TF-002 — self.app 직접 접근이 DI ctx 패턴을 우회
```
ID: T05-TF-002
Severity: P2-MEDIUM
Category: CONTRACT-VIOLATION
Surface: modules/core/stage4_orchestrator.py:329-333
Evidence:
  - stage4_orchestrator.py:329:
    `inspect.getattr_static(self.app, "_generate_reverse_feedback_stage4_to_3")`
  - stage4_orchestrator.py:333:
    `callback = getattr(self.app, "_generate_reverse_feedback_stage4_to_3", None)`
  - Stage4Orchestrator 내 self.app 직접 접근은 이 2줄 + L222(생성자) + L234(lazy ctx init) 뿐
  - 나머지 전체 orchestrator는 self.ctx를 통해 접근하는 DI 패턴 준수
  - Stage4Context.from_app()에는 이 콜백이 없음
    (Grep "reverse_feedback" in stage4_context.py → 0 matches)
Inference: `_generate_reverse_feedback_stage4_to_3`가 Stage4Context 콜백으로 등록되지 않아
  self.app을 직접 참조. DI 순수성이 깨짐. 테스트에서 ctx만 mock하면 이 경로가 테스트 불가.
Uncertainty: 의도적 설계일 수 있음 (콜백 추가 비용 vs 1곳 접근)
Cross-Ref: T01 (app의 _generate_reverse_feedback_stage4_to_3 정의 위치)
```

#### T05-TF-003 — canary_tools _normalize_from_ep() from_ep=1 하드코딩
```
ID: T05-TF-003
Severity: P2-MEDIUM
Category: HARDCODING
Surface: modules/core/stage4_canary_tools.py:40-44
Evidence:
  - stage4_canary_tools.py:40-44:
    ```python
    def _normalize_from_ep(from_ep: int) -> int:
        normalized = max(1, int(from_ep or 1))
        if normalized != 1:
            raise ValueError("Stage 4 canary prep currently supports only from_ep=1")
        return normalized
    ```
  - 4개 public 함수(L57, L90, L116, L139)가 모두 이 함수를 호출
  - from_ep 파라미터가 API에 존재하지만 1 이외의 값은 항상 ValueError
Inference: API surface가 확장성을 암시하지만 구현은 from_ep=1만 지원.
  호출자가 from_ep>1로 호출하면 런타임 실패.
Uncertainty: "currently supports" 주석이 의도적 제한임을 시사. 향후 확장 계획일 수 있음.
Cross-Ref: 없음
```

### P3-LOW (5건)

#### T05-TF-004 — _LOG_FILE_NAMES 미사용 상수 (DEAD-CODE)
```
ID: T05-TF-004
Severity: P3-LOW
Category: DEAD-CODE
Surface: modules/core/stage4_canary_tools.py:15-21
Evidence:
  - stage4_canary_tools.py:15-21:
    ```python
    _LOG_FILE_NAMES = (
        "episode_production.jsonl",
        "pass_rate_monitor.json",
        "quality_metrics.jsonl",
        "runtime_audit.jsonl",
        "runtime_audit_summary.json",
    )
    ```
  - Grep "_LOG_FILE_NAMES" in entire codebase → 1 match (정의 자체뿐)
  - 파일 내에서도 L15 정의 외 참조 0건
Inference: 과거 로그 파일 이름 목록으로 사용되었거나 미래용으로 선언되었으나 현재 미사용.
Uncertainty: 없음
Cross-Ref: 없음
```

#### T05-TF-005 — orchestrator L851 주석 STALE ("50,000자 상한")
```
ID: T05-TF-005
Severity: P3-LOW
Category: STALE
Surface: modules/core/stage4_orchestrator.py:851-852
Evidence:
  - stage4_orchestrator.py:851:
    `# [V67] mandatory_context 우선순위 기반 스마트 트렁케이션 (50,000자 상한)`
  - stage4_orchestrator.py:852:
    `_mc_max = _threshold("context.mandatory_context_max", 80000)`
    → 코드 default = 80,000
  - config/settings/validation.yaml:76:
    `mandatory_context_max: 400000  # [1M-CTX-P0] 200000 → 400000`
    → live 값 = 400,000
  - 주석의 "50,000자" vs 코드 default 80,000 vs YAML 실제 400,000 — 3단계 불일치
Inference: V67 → 1M-CTX-P0 업그레이드 시 주석만 갱신되지 않음. 기능에 영향 없음 (주석일 뿐).
Uncertainty: 없음
Cross-Ref: T17 (validation.yaml 키 참조 정합성)
```

#### T05-TF-006 — orchestrator L1592 로그 메시지 STALE ("5번 기회")
```
ID: T05-TF-006
Severity: P3-LOW
Category: STALE
Surface: modules/core/stage4_orchestrator.py:1592
Evidence:
  - stage4_orchestrator.py:1592:
    `self.ctx.ui.log("   • Director 면담: 5번 기회 (패치 모드 전 라운드 적용)")`
  - stage4_orchestrator.py:999:
    `_max_rounds = int(_threshold("retry.director_max_attempts", 5))`
    → 코드 default = 5
  - config/settings/validation.yaml:95:
    `director_max_attempts: 10`
    → live 값 = 10
  - UI 로그가 "5번"이라고 표시하지만 실제 면담은 최대 10번 수행
Inference: validation.yaml이 10으로 설정되었으나 UI 로그 문자열은 하드코딩된 "5번" 유지.
  사용자에게 잘못된 정보 제공. 기능에는 영향 없음.
Uncertainty: 없음
Cross-Ref: T17 (validation.yaml director_max_attempts)
```

#### T05-TF-007 — _SessionConfig ↔ _RoundContext 의도적 5-field 중복
```
ID: T05-TF-007
Severity: P3-LOW
Category: STALE
Surface: modules/core/stage4_orchestrator.py:175-197, modules/core/stage4_types.py:16-61
Evidence:
  - stage4_orchestrator.py:176-182 (_SessionConfig):
    chief_writer, manuscript_validator, consistency_validator,
    blocking_validator, continuity_validator, story_context, style_guide
  - stage4_types.py:25-53 (_RoundContext):
    동일 7필드 중복 (chief_writer~continuity_validator 5 + story_context + style_guide)
  - 양쪽 docstring에 의도적 중복 명시:
    stage4_orchestrator.py:179: "NOTE: chief_writer~continuity_validator, story_context, style_guide는
    _RoundContext(stage4_types.py)와 의도적으로 중복됩니다."
    stage4_types.py:19: 동일 문구
  - 실제 복사 경로: orchestrator L682-694에서 SessionConfig unpack → L907-928에서
    build_round_context()에 전달
Inference: 아키텍처 문서화가 양쪽 docstring에 존재하므로 의도적. slots=True로 다중 상속 제한됨.
  단, 유지보수 시 한쪽만 수정하면 불일치 위험.
Uncertainty: 없음
Cross-Ref: 없음
```

#### T05-TF-008 — stage4_canary_tools.py 프로덕션 미사용 (스크립트/테스트 전용)
```
ID: T05-TF-008
Severity: P3-LOW
Category: COVERAGE-GAP
Surface: modules/core/stage4_canary_tools.py (전체 936 lines)
Evidence:
  - Grep "from modules.core.stage4_canary" in modules/ → 0 matches
  - Grep "import stage4_canary" in modules/ → 0 matches
  - Grep "stage4_canary" in main_a.py → 0 matches
  - 사용처:
    - scripts/run_stage4_canary.py:22-26 (import)
    - scripts/run_stage34_canary.py:25-29 (import)
    - tests/test_stage4_canary_tools.py:7-12 (import)
    - tests/test_run_stage4_canary.py (mock)
    - tests/test_run_stage34_canary.py (mock)
Inference: 순수 ops/testing 인프라. 프로덕션 코드 경로에서 절대 호출되지 않음.
  modules/core/ 디렉토리에 위치하지만 성격상 scripts/ 또는 tools2/ 에 더 적합.
Uncertainty: 의도적 배치일 수 있음 (DBManager 접근을 위해)
Cross-Ref: T20 (scripts 분류)
```

### P4-OBSERVATION (14건)

#### T05-TF-009 — _RoundContext 36필드 전수 사용 확인 (SYNC)
```
ID: T05-TF-009
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/stage4_types.py:16-61
Evidence:
  - _RoundContext 36 fields 전수 (L25-61)
  - Producer: stage4_context_builder.py:2938-2975 (build_round_context)
  - Consumer: stage4_interview_round.py L1776-1916 (run method unpack)
  - 최다 참조: arc_data (38 refs), blueprint (11 refs), next_ep (7 refs)
  - 최소 참조: manuscript_validator, blocking_validator, mandatory_context, reference_excerpt (1 ref each)
  - Dead fields: 0
Inference: 전체 필드가 producer→consumer 경로를 갖고 있음. 미사용 필드 없음.
Uncertainty: 없음
Cross-Ref: T06 (interview_round의 consumer 측)
```

#### T05-TF-010 — 조건부 모듈 8종 _CONDITIONAL_MODULE_KEYS ↔ get_module() 완전 매칭 (SYNC)
```
ID: T05-TF-010
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/stage4_context.py:6-15, modules/core/stage4_orchestrator.py:1036,
         modules/core/stage4_interview_round.py:1982,3429,3458,3475,4298,4312,4715
Evidence:
  - stage4_context.py:6-15 정의 8종:
    pre_director_checklist, confidence_calibrator, prompt_weighter, cross_verifier,
    chain_of_verification, adversarial_self_play, tree_of_thoughts, multi_agent_deliberation
  - get_module() 호출 8종:
    - orchestrator:1036 "chain_of_verification"
    - interview_round:1982 "prompt_weighter"
    - interview_round:3429 "pre_director_checklist"
    - interview_round:3458 "confidence_calibrator"
    - interview_round:3475 "cross_verifier"
    - interview_round:4298 "tree_of_thoughts"
    - interview_round:4312 "multi_agent_deliberation"
    - interview_round:4715 "adversarial_self_play"
  - 정의 8종 = 사용 8종 (완전 매칭)
Inference: S-13 패턴이 의도대로 동작. 미등록/미사용 키 없음.
Uncertainty: 없음
Cross-Ref: T15 (각 조건부 모듈의 내부 로직)
```

#### T05-TF-011 — 12 콜백 전수 소비 확인 (SYNC)
```
ID: T05-TF-011
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/stage4_context.py:40-44
Evidence:
  - Docstring 12종 = 직접 슬롯 7 + property 콜백 5
  - 직접 슬롯 7종 사용처:
    get_int_input → orchestrator:1388,1671
    build_item_acquisition_timeline → context_builder:2143
    load_narrative_summaries → context_builder:2759
    get_protagonist_name → context_builder:104, post_processor:1604
    generate_narrative_summary → post_processor:734
    flush_audit_buffer → orchestrator:1476,1754
    safe_commit → orchestrator:1478,1746
  - Property 5종 사용처:
    extract_npc_profiles → interview_round:4761
    generate_writer_guidance_v60_8 → context_builder:2877
    enrich_director_result → interview_round:1069
    audit_event → orchestrator:277, interview_round:1092
    write_audit_summary → orchestrator:1737
  - 12/12 모두 최소 1곳 이상 호출됨
Inference: 콜백 인프라 완전 사용. 미사용 콜백 없음.
Uncertainty: 없음
Cross-Ref: T01 (app에서 콜백 주입 시점)
```

#### T05-TF-012 — Episode 루프 5개 종료 경로 (SYNC)
```
ID: T05-TF-012
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/stage4_orchestrator.py:676-971
Evidence:
  - _run_interview_loop() 종료 조건 5가지:
    1. L698-700: total_planned_ep ≤ 0 → "블루프린트 없음" → return False
    2. L718-720: loop_guard > max_loops → "루프 제한 도달" → break
    3. L725-728: next_ep > target_ep → "목표 회차 도달" → break
    4. L732-734: blueprint 없음 → "Blueprint 없음" → break
    5. L745-747: arc_data 없음 → "Arc 데이터 없음" → break
  - 추가: L954-956: DB 저장 실패 → break
  - max_loops 공식 (L702-704):
    `max(1, min((target_ep or total_planned_ep) - latest_ep + 5, 100))`
Inference: 루프 무한 실행 방지가 다층으로 구현됨. Safety guard(L718)가 최종 방어선.
Uncertainty: 없음
Cross-Ref: 없음
```

#### T05-TF-013 — 3 lazy sub-module + ctx 무효화 패턴 (SYNC)
```
ID: T05-TF-013
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/stage4_orchestrator.py:224-294
Evidence:
  - 3개 lazy sub-module:
    L224: self._post_processor (Stage4PostProcessor)
    L225: self._context_builder (Stage4ContextBuilder)
    L226: self._interview_round (Stage4InterviewRound)
  - Property 초기화: L246-257 (post_processor, context_builder), L290-293 (interview_round)
  - ctx setter L237-243:
    ```python
    @ctx.setter
    def ctx(self, value):
        self._ctx = value
        self._post_processor = None
        self._context_builder = None
        self._interview_round = None
    ```
  - ctx 변경 시 3개 sub-module 캐시 전부 무효화 → 재생성 보장
Inference: DI 컨텍스트 교체 시 sub-module 불일치 방지. 안전한 설계.
Uncertainty: 없음
Cross-Ref: 없음
```

#### T05-TF-014 — prepare_episode_context 16-key 반환 + 3-tier lookback (SYNC)
```
ID: T05-TF-014
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/stage4_context_builder.py:1948-2186
Evidence:
  - 반환 dict 16 keys:
    arc_pos, total_ep_in_arc, arc_tactical, prev_text, prev_ending,
    prev_manuscripts_text, episode_digest, hud_report, current_inventory,
    current_martial_arts, cumulative_bible, dead_npcs, item_acquisition_timeline,
    chain_link_section, world_state_summary, recent_scene_keywords
  - 3-tier lookback (prev_manuscripts_text 조립):
    Tier1 (L1965-1989): ep-30 ~ ep-1 전문
    Tier2 (L1991-2017): ep-60 ~ ep-31 요약
    Tier3 (L2019-2065): 61화 이전 아크 요약
Inference: 에피소드 컨텍스트가 체계적으로 수집됨. 장기 연재 시 3-tier로 과거 이력을 보존.
Uncertainty: 없음
Cross-Ref: T04 (stage3→stage4 handoff 데이터)
```

#### T05-TF-015 — build_mandatory_context 3-tier 611줄 조립 (SYNC)
```
ID: T05-TF-015
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/stage4_context_builder.py:2299-2909
Evidence:
  - 611줄 메서드, 5-key dict 반환:
    reference_anchor_prompt, mandatory_context, anti_trope_prompt,
    justification_prompt, reflexion_prompt
  - 3-tier 조립:
    Tier 0 (Canonical): world_state, fact_ledger, continuity_packet, npc_boundary
    Tier 1 (Smart Retrieval): work_identity, retrieval_plan, vector_context
    Tier 2 (Advisory): failure_context, ambient_npcs, series_summary,
      state_tracker 16 types, extended_lookback, foreshadow, pacing
  - 3-round budget iteration (L2815-2834):
    compose → detect coverage gaps → inject warnings → re-compose
  - Budget tracker: _stage4_context_budget_meta에 8 keys 기록
Inference: 프롬프트 조립이 코드베이스에서 가장 복잡한 단일 메서드. 계층적 우선순위 관리.
Uncertainty: 없음
Cross-Ref: T17 (prompt template keys)
```

#### T05-TF-016 — TF-49b preflight fail-open + 2-stage severity 필터 (SYNC)
```
ID: T05-TF-016
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/stage4_orchestrator.py:403-615
Evidence:
  - L411: 전체 실패 시 pass 반환 (fail-open)
  - L526-541: Stage 1 — FALSE_POSITIVE_PATTERNS (13 patterns) → severity downgrade to "low"
  - L542-562: Stage 2 — CRITICAL_PATTERNS (11 patterns) 미매칭 → severity downgrade to "low"
  - L565-566: severity="high"인 이슈만 실패 판정
  - L606: advisory 전달 방식 — passed=True 고정 (블루프린트 미수정)
Inference: 웹소설 도메인 특화 가짜양성 필터. 과도한 reject 방지. Director에 advisory 전달만.
Uncertainty: 없음
Cross-Ref: T14 (validation pipeline)
```

#### T05-TF-017 — V75-D→V75-B 에스컬레이션 체인 (SYNC)
```
ID: T05-TF-017
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/stage4_orchestrator.py:1243-1372
Evidence:
  - Step 1 V75-D (L1243-1321): LOGIC_ERROR N연속 → inplace blueprint 패치 (1회 제한)
    - quality_risk Blueprint → threshold=1 (L1247), 일반 → threshold=2 (L1247)
    - _inplace_attempted flag로 1회 제한 (L988, L1253)
  - Step 2 V75-B (L1323-1372): inplace 후에도 실패 → 전면 재생성 (1회 제한)
    - _blueprint_regenerated flag로 1회 제한 (L989, L1324)
    - 재생성도 실패 시 Arc 재생성 권고 (L1376-1378)
  - 에스컬레이션 로그: episode_production.jsonl (L1312-1321, L1362-1372)
Inference: 3단계 에스컬레이션: 원고 재작성 → 블루프린트 패치 → 블루프린트 재생성 → 아크 재생성 권고.
  각 단계 1회 제한으로 무한 재생성 방지.
Uncertainty: 없음
Cross-Ref: T04 (stage3 blueprint 재생성)
```

#### T05-TF-018 — CoVe 3-path PASS→REJECT 변환 (SYNC)
```
ID: T05-TF-018
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/stage4_orchestrator.py:1036-1123
Evidence:
  - Path 1 (L1058-1076): CoVe LLM verify → should_regenerate=True → REJECT
  - Path 2 (L1081-1102): CoVe LLM verify runtime 실패 → REJECT (fail-closed)
  - Path 3 (L1103-1123): CoVe quick_verify runtime 실패 → REJECT (fail-closed)
  - 3 경로 모두: final_manuscript=None, final_title=None → continue (다음 라운드 소비)
  - 라운드 소모 가시화 로그: L1070-1075, L1096-1101, L1117-1122
Inference: CoVe는 fail-closed 정책. 검증 실패 또는 런타임 에러 모두 REJECT 처리.
  라운드를 소비하므로 max_rounds에 영향.
Uncertainty: 없음
Cross-Ref: T15 (chain_of_verification 내부 로직)
```

#### T05-TF-019 — max_loops guard 공식 (SYNC)
```
ID: T05-TF-019
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/stage4_orchestrator.py:701-704
Evidence:
  - L702-704:
    ```python
    max_loops = max(
        1, min((target_ep or total_planned_ep) - self.ctx.current_project.get_latest_episode_number() + 5, 100)
    )
    ```
  - 주석 L701: "[Sweep45] max(1, ...) — latest_ep > total_planned_ep 시 음수 방지"
  - +5 여유분: 에피소드 번호 갱신 타이밍에 의한 off-by-one 방어
  - 상한 100: 무한 루프 절대 방지
  - 하한 1: 음수/0 방지
Inference: 안전한 루프 바운드. Sweep45에서 수정된 이력.
Uncertainty: 없음
Cross-Ref: 없음
```

#### T05-TF-020 — 테스트 커버리지 221 tests across 4 files (SYNC)
```
ID: T05-TF-020
Severity: P4-OBSERVATION
Category: SYNC
Surface: tests/test_stage4_orchestrator.py, test_stage4_context_builder.py,
         test_stage4_context.py, test_stage4_cv_context.py
Evidence:
  - test_stage4_orchestrator.py: 13 test classes, 61 tests
    (patch mode, audit, session prep, round outcome, NPC overexposure, cross-ep repetition)
  - test_stage4_context_builder.py: 12 test classes, 105+ tests
    (context tiers, budget, retrieval, work focus, scene similarity)
  - test_stage4_context.py: 2 test classes, 30 tests
    (DI context, from_app factory, callbacks, orchestrator integration)
  - test_stage4_cv_context.py: 6 test classes, 25 tests
    (protagonist, prev_hud, NPC profiles, karma, villain/authority context)
  - 주요 커버리지 갭:
    - _run_interview_loop() 직접 통합 테스트 없음 (mock 기반)
    - _regenerate_blueprint() 단위 테스트 제한적
    - context_builder 예외 경로 일부 미테스트
Inference: 테스트 커버리지 높음. 주요 비즈니스 로직 경로 대부분 커버.
Uncertainty: 실제 pytest 실행 없이 정적 분석 기반 판단
Cross-Ref: T20 (전체 테스트 커버리지)
```

#### T05-TF-021 — WritingDirective 소비 경로 (SYNC)
```
ID: T05-TF-021
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/stage4_types.py:77-92
Evidence:
  - 정의: stage4_types.py:77-92 (8 fields + is_empty() method)
  - 생성: stage4_interview_round.py:1715-1753 (PatternTracker + WritingDirectiveGenerator)
  - 소비: stage4_interview_round.py:2205 ("[WritingDirective]" 섹션으로 주입)
  - 추가 소비: chief_writer_context.py, chief_writer_quality.py
Inference: stage4_types.py에서 정의, interview_round에서 생성/소비, chief_writer에서 활용.
  3 모듈간 공유 타입으로 I-17 패턴 준수.
Uncertainty: 없음
Cross-Ref: T08 (ChiefWriter의 WritingDirective 활용)
```

#### T05-TF-022 — Stage4Context property 콜백 패턴 (SYNC)
```
ID: T05-TF-022
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/stage4_context.py:162-225
Evidence:
  - 5개 콜백이 property로 구현 (직접 __slots__가 아닌 _stage4_context_budget_meta에 저장):
    extract_npc_profiles (L187-192)
    generate_writer_guidance_v60_8 (L194-200)
    enrich_director_result (L202-208)
    audit_event (L210-216)
    write_audit_summary (L218-224)
  - _get_callback/_set_callback 헬퍼 (L166-184):
    `_stage4_context_budget_meta["_callbacks"]` dict에 저장/조회
  - __init__에서 property setter 경유 설정 (L152-159)
  - 나머지 7개 콜백은 직접 __slots__ (L73-79)
Inference: 2종 콜백 저장 방식 공존. 이유 미기재이나 __slots__ 추가 없이 콜백 확장 가능한 패턴.
  budget_meta dict 재사용으로 메모리 절약 의도일 수 있음.
Uncertainty: 2종 방식 공존 이유 불명확
Cross-Ref: 없음
```

---

## 3. Evidence Inventory

| TF ID | Evidence 유형 | 핵심 파일:라인 |
|-------|-------------|---------------|
| TF-001 | 코드 vs Docstring 비교 | stage4_context.py:34-38 vs L56,L69 |
| TF-002 | 코드 패턴 분석 | stage4_orchestrator.py:329,333 |
| TF-003 | 코드 + ValueError | stage4_canary_tools.py:40-44 |
| TF-004 | Grep 0 matches | stage4_canary_tools.py:15-21 |
| TF-005 | 코드 vs 주석 vs YAML | orchestrator:851 vs validation.yaml:76 |
| TF-006 | 하드코딩 로그 vs YAML | orchestrator:1592 vs validation.yaml:95 |
| TF-007 | 양쪽 Docstring 인용 | orchestrator:179, types:19 |
| TF-008 | Grep import 분석 | modules/ 0건, scripts/ 2건, tests/ 3건 |
| TF-009 | 전수 필드 매칭 | types:25-61 → interview_round:1776-1916 |
| TF-010 | 8종 키 ↔ 8종 호출 | context:6-15 → orch:1036 + interview_round 7곳 |
| TF-011 | 12종 콜백 호출처 | context:40-44 → 4 파일 분산 |
| TF-012 | 5개 종료 조건 | orchestrator:698-747 |
| TF-013 | Lazy init + setter | orchestrator:224-243 |
| TF-014 | 16-key dict + 3-tier | context_builder:1948-2186 |
| TF-015 | 611-line method | context_builder:2299-2909 |
| TF-016 | 2-stage filter | orchestrator:526-566 |
| TF-017 | 3-step escalation | orchestrator:1243-1372 |
| TF-018 | 3 REJECT paths | orchestrator:1036-1123 |
| TF-019 | Guard 공식 | orchestrator:702-704 |
| TF-020 | Test class/method 전수 | 4 test files |
| TF-021 | Import/usage chain | types:77 → interview_round:1715-2205 |
| TF-022 | Property mechanism | context:162-225 |

---

## 4. Side-Effect Surface

### stage4_orchestrator.py
| 위치 | Side-effect | 대상 |
|------|-------------|------|
| L394 | world_state.add_world_law() | WorldState 메모리 |
| L508-517 | generate_content_via_router() | Gemini API 호출 (TF-49b preflight) |
| L660-661 | director.ask() | Gemini API 호출 (chain_link 추출) |
| L1458 | append_jsonl_record() | episode_production.jsonl 파일 쓰기 |
| L1511 | current_project.save_episode_blueprint() | DB 쓰기 (blueprint 재생성) |
| L941-953 | post_processor.process_pass_result() | DB 쓰기 + 파일 쓰기 |
| L962-964 | pass_rate_monitor.check_alerts() | 경보 소비 |

### stage4_context_builder.py
| 위치 | Side-effect | 대상 |
|------|-------------|------|
| L1673-1704 | _stage4_context_budget_meta 갱신 | ctx 메모리 상태 |
| L959 | dashboard.record_retrieval_observation() | QualityDashboard 상태 |
| L977 | dashboard.record_hud_anomaly() | QualityDashboard 상태 |

### stage4_canary_tools.py
| 위치 | Side-effect | 대상 |
|------|-------------|------|
| L65,98 | shutil.rmtree() | 디렉토리 삭제 |
| L67,100 | shutil.copytree() | 프로젝트 복제 |
| L76,109 | _write_json() | JSON 파일 쓰기 |
| L124,147 | DB DELETE 17-19 테이블 | DB 일괄 삭제 |
| L128,151 | 파일 시스템 정리 | drafts/, logs/, memory/ 삭제 |

---

## 5. Facts

1. Stage4Orchestrator는 1개 진입점(`stage_4_v2_chief_writer`)에서 시작하여 session prep → interview loop → outcome handling → post processing 순서로 실행된다.
2. DI 컨텍스트(Stage4Context)는 30 __slots__ + 5 property 콜백 = 35 접근점을 가진다.
3. _RoundContext는 36 필드를 가지며 모두 활성 사용된다.
4. 조건부 모듈 8종은 `conditional_modules` dict로 통합되어 `get_module()` 헬퍼로 접근한다.
5. 에피소드 루프(outer)는 5개 종료 조건 + max_loops 100 상한을 갖는다.
6. 면담 루프(inner)는 `retry.director_max_attempts` (live 값 10, default 5)로 제한된다.
7. CoVe 사후검증은 fail-closed 정책으로 3가지 경로에서 PASS→REJECT 전환이 가능하다.
8. V75-D/V75-B 에스컬레이션 체인은 각 1회 제한으로 무한 재생성을 방지한다.
9. stage4_canary_tools.py는 프로덕션 코드에서 호출되지 않는 ops/testing 전용 모듈이다.
10. build_mandatory_context()는 611줄로 코드베이스 내 가장 복잡한 단일 메서드이며, 3-tier 조립 + 3-round budget iteration을 수행한다.

---

## 6. Inferences

1. T05-TF-001 docstring DRIFT는 유지보수 위험: 슬롯 수를 docstring 기준으로 세면 2개가 누락됨.
2. T05-TF-002 self.app 직접 접근은 DI 테스트 격리를 깨뜨릴 수 있음: ctx만 mock하는 테스트에서 `_generate_reverse_feedback_stage4_to_3` 경로가 커버되지 않음.
3. mandatory_context 80,000→400,000 변경 시 orchestrator L851 주석과 L1592 UI 로그가 갱신되지 않았으며, 사용자에게 부정확한 정보를 표시함.
4. canary_tools의 from_ep=1 제한은 API 확장성을 제한하지만, 현재 사용 패턴에서는 문제없음.
5. build_mandatory_context()의 복잡도(611줄)는 분리 후보이나, 현재 내부 구조(tier 분리)가 논리적이며 동작함.

---

## 7. Uncertainty / Contradictions

1. **T05-TF-002 의도성**: `_generate_reverse_feedback_stage4_to_3`가 ctx에 등록되지 않은 것이 의도적 설계인지 누락인지 불명확. 동적 검증으로 main_a.py에서 해당 메서드 존재 여부 확인 필요.
2. **T05-TF-022 2종 콜백 방식**: 직접 slots 7개와 property 5개의 분리 기준 불명확. 주석이나 commit 이력에서 근거를 찾을 수 있을 것.
3. **테스트 커버리지 수치**: 정적 분석 기반 221 tests 산출. 실제 pytest 실행 시 parameterize 등으로 수치가 달라질 수 있음.

---

## 8. Cross-Ref to Adjacent Terminals

| 인접 터미널 | 교차 영역 | 관련 TF |
|------------|----------|---------|
| T01 (SovereignApp) | app → Stage4Context.from_app() DI 주입 | TF-001, TF-002, TF-011 |
| T04 (Stage3) | stage3 blueprint → stage4 consumption, V75-B 재생성 | TF-017 |
| T06 (Interview) | _RoundContext producer→consumer, CoVe, 조건부 모듈 | TF-009, TF-010, TF-018 |
| T14 (Validation) | TF-49b preflight, validation thresholds | TF-016 |
| T15 (Quality Intel) | 8 conditional modules 내부 로직 | TF-010 |
| T17 (Config) | validation.yaml 키 참조 정합성 | TF-005, TF-006 |
| T20 (Cross-Cut) | canary_tools scripts 분류, 테스트 전체 | TF-008, TF-020 |

---

## 9. Candidate Watchlist

1. **build_mandatory_context() 분리 후보**: 611줄 단일 메서드. Tier 0/1/2를 별도 메서드로 추출 가능.
2. **Property 콜백 통합**: 2종 콜백 저장 방식(직접 slots vs property/_callbacks dict)을 하나로 통합 가능.
3. **canary_tools 위치 이동**: modules/core/ → tools2/ 또는 scripts/ 이동 고려.
4. **max_rounds UI 동적 표시**: L1592 하드코딩 "5번" → `_max_rounds` 변수 참조로 변경.

---

## 10. 6Pass Audit Log

### Pass 1 — 구조/범위
- T05 범위 5개 파일 전수 조사 완료 (6,030 lines)
- 관련 테스트 4개 파일 분석 완료 (3,959 lines, 221 tests)
- 필수 조사 6항목 모두 수행
- TF 22개 (최소 기대 10-18 범위 충족)
→ **PASS**

### Pass 2 — 증거/일관성
- 모든 TF에 파일:라인 Evidence 존재
- 코드 스니펫 직접 인용 (TF-001,003,005,006 등)
- Grep 결과 기반 부재 증명 (TF-004,008)
- YAML vs 코드 교차 검증 (TF-005,006)
→ **PASS**

### Pass 3 — 실행가능성
- P2 3건: 모두 코드 수정으로 해결 가능 (docstring 갱신, 콜백 등록, from_ep 제한 문서화)
- P3 5건: 주석/로그 갱신, dead code 제거
- P4 14건: 관측 기록으로 실행 불필요
→ **PASS**

### Pass 4 — 적대적: 스코프 과잉/누락
- "context_builder를 더 깊이 조사해야 한다" → 611줄 메서드 분석, 3-tier 구조, 16-key 반환 모두 문서화 → **반박 실패**
- "interview_round도 T05 범위다" → interview_round는 T06 범위. T05는 orchestrator 측에서 호출하는 인터페이스만 조사 → **반박 실패**
→ **PASS**

### Pass 5 — 적대적: 증거 거짓/과장
- "TF-005의 400,000 값이 틀렸을 수 있다" → validation.yaml:76 직접 확인, 주석까지 "[1M-CTX-P0] 200000 → 400000" 명시 → **반박 실패**
- "TF-002의 DI 우회가 문제가 아니다" → 사실 자체는 확인됨 (self.app 직접 접근). 문제 여부는 severity 판단이며 evidence는 정확 → **반박 실패**
→ **PASS**

### Pass 6 — 적대적: severity 과대/과소
- "TF-001을 P3로 내려야 한다" → docstring 불일치는 리팩터링 시 슬롯 누락 위험이므로 P2 유지 정당 → **반박 실패**
- "TF-004를 P4로 내려야 한다" → 7줄 미사용 상수는 P3이 적절. P4까지 내릴 근거 없음 → **반박 실패**
- "TF-006을 P2로 올려야 한다" → 사용자 UI 표시 오류이나 기능에 영향 없음. P3 유지 → **반박 실패**
→ **PASS**

**6PASS 전체 통과 — 확신도 96%**
