# Opus TF-5: 전체 시스템 디버깅 감사 오더 (12 TF)

> **[Codex 감사 작업 지시 — 반드시 준수]**
>
> ## 도구 제한
> - `rg`, `grep`, `fgrep`, `ag`, `ack` 등 **자동 검색 도구 사용 금지**.
> - 반드시 해당 파일을 **직접 열어(Read/cat)** 라인 단위로 수동 확인할 것.
> - 파일 경로, 라인 번호, 코드 존재/부재, 수치를 주장할 때는 **해당 라인을 직접 읽은 뒤 인용**할 것.
> - "아마 있을 것이다", "보통 이렇게 되어 있다" 등 **추측 기반 주장 금지**. 직접 확인 못 하면 "미확인"으로 표기.
>
> ## 감사 방법론
> - **디버깅 위주**: 코드 결함, 논리 오류, 데이터 흐름 단절, 엣지 케이스를 찾는다.
> - 코드 스타일/리팩토링 제안은 하지 않는다. **버그와 결함만** 보고한다.
> - 실제 실행 경로를 **호출자 → 피호출자** 순으로 추적하여 도달 가능한 결함만 보고한다.
> - 테스트에서만 도달 가능하고 프로덕션에서 도달 불가능한 경로는 **제외**한다.
> - 오탐(false positive)은 **신뢰도를 떨어뜨리므로** 확실한 것만 보고한다.
> - "~할 수도 있다" 식의 가능성 나열은 하지 않는다. **실제 코드 경로에서 발생하는 것만** 보고한다.
>
> ## 이슈 분류 기준
> - **CRITICAL**: 프로덕션 크래시, 데이터 손실, 무한 루프. 즉시 수정 필요.
> - **HIGH**: 잘못된 결과, 기능 미작동, silent data corruption. 1일 내 수정.
> - **MEDIUM**: 성능 병목, 부분적 기능 저하, 방어 코드 누락. 1주 내 수정.
> - **LOW**: 코드 위생, 미사용 변수, 주석 불일치. 여유 시 수정.
>
> ## 보고 형식 (이슈당)
> ```
> ### [{ID}] {제목} — {CRITICAL|HIGH|MEDIUM|LOW}
> - **위치**: 파일명:라인번호
> - **코드 인용**: (해당 라인 직접 인용, 3~5줄)
> - **현상**: (무엇이 잘못되었는지)
> - **재현 시나리오**: (어떤 입력/조건에서 발생하는지)
> - **영향**: (프로덕션에서 어떤 결과를 초래하는지)
> - **수정 제안**: (구체적 코드 변경안, 1~3줄)
> ```
>
> ## 특별 주의 — Tier 1~5 회귀 점검
> - 최근 Tier 1~5에서 변경된 코드의 **회귀 여부를 특별히 확인**할 것.
> - 변경 태그: `[NPC-L1]`, `[NPC-L2]`, `[Tier4-12]`, `[Phase A-3]`, `[SC-Skip]`, `SafeDict`, `format_map`
> - 이 태그가 있는 라인 주변 ±20줄을 집중 점검할 것.
> - 각 TF는 자신의 담당 파일만 감사한다. 다른 TF 영역은 침범하지 않는다.
> - 종합 보고서(`opus_tf5_consolidated_debug_report.md`)에서 cross-TF 이슈를 별도 정리한다.

---

> 감사일: 2026-02-22
> 감사자: Claude Opus 4.6 × 12 TF (병렬)
> 방법론: 디버깅 위주 전체 시스템 조사
> 대상: 글도비 현재 HEAD (Tier 1~5 반영 완료)
> 테스트 기준선: 2,339 passed, ruff 0 violations
> 코드베이스: core 117파일 58K줄 + agents 46파일 31K줄 = **~90K줄**

---

## 배경

TF-4 Production Hardening 감사 Tier 1~5 전량 반영 후 코드베이스 전체를
**디버깅 관점**으로 재조사한다. 12개 TF가 병렬로 각 영역을 담당하여
잔존 결함, 회귀 버그, 엣지 케이스를 발굴한다.

### Tier 1~5 변경 요약 (회귀 점검 대상)

| Tier | 주제 | 핵심 변경 파일 |
|------|------|--------------|
| 1 | bind_db 배선 + rollback + YAML 중복 키 | stage2/3_orchestrator, main_a, emotion_tracker |
| 2 | Dead Code ~3,000줄 제거 | strategies/ 삭제, 5 모듈 삭제, conftest, validation.yaml |
| 3 | 비용 최적화 Phase A | models.yaml, director, director_auditor, stage4_interview_round |
| 4 | 스케일링 + 캐싱 | db_manager, state_tracker_plots, arc/blueprint_ensemble, stage4_context_builder |
| 5 | 프롬프트 외부화 + YAML 위생 | prompt_loader, 33개 YAML 삭제, 11개 에이전트 SafeDict 전환 |

---

## TF 구성 (12개 병렬)

| TF | 주제 | 대상 줄 수 | 산출물 |
|----|------|----------|--------|
| A | Stage 2 파이프라인 | ~4,268줄 | `opus_tf5_stage2_debug_audit.md` |
| B | Stage 4 파이프라인 | ~5,944줄 | `opus_tf5_stage4_debug_audit.md` |
| C | NPC / State 무결성 | ~4,487줄 | `opus_tf5_npc_state_debug_audit.md` |
| D | 인프라 계층 | ~5,273줄 | `opus_tf5_infra_debug_audit.md` |
| E | Director 체인 | ~1,420줄+ | `opus_tf5_director_debug_audit.md` |
| F | main_a.py + 통합 시나리오 | ~3,600줄+ | `opus_tf5_integration_debug_audit.md` |
| **G** | **Stage 0 + Stage 3** | **~5,208줄** | `opus_tf5_stage0_3_debug_audit.md` |
| **H** | **Genre Guards (14파일)** | **~6,709줄** | `opus_tf5_genre_guards_debug_audit.md` |
| **I** | **Continuity Inspector 체인** | **~3,173줄** | `opus_tf5_continuity_debug_audit.md` |
| **J** | **Arc/Blueprint 생성 체인** | **~4,764줄** | `opus_tf5_arc_gen_debug_audit.md` |
| **K** | **Validation 파이프라인 전면** | **~8,193줄** | `opus_tf5_validation_debug_audit.md` |
| **L** | **운영 계측 + 설정 정합성** | **~3,927줄** | `opus_tf5_ops_config_debug_audit.md` |

---

## TF-A: Stage 2 파이프라인 디버깅

### 대상 파일
- `modules/core/stage2_orchestrator.py` (828줄)
- `modules/core/stage2_validation_pipeline.py` (725줄)
- `modules/core/stage2_finalizer.py` (694줄)
- `modules/core/stage2_preflight.py` (1,021줄)

### 검증 관점

**A-1: SC(Smart Context) Stage 2 통합**
- `stage2_preflight.py` L640~690: `_execute_stage2_retrieval_plan()` 호출 경로 추적
- `context_advisor.plan_stage2_retrieval()` 반환값이 None일 때 폴백 경로 확인
- `_threshold("smart_retrieval.enabled")` + `_threshold("smart_retrieval.stage2_enabled")` 이중 조건
- per-slot 절단 후 글로벌 예산(`plan.total_budget_chars`) 가드 존재 여부 확인

**A-2: StateTracker 스냅샷 복구**
- `stage2_preflight.py` L814~841: `st_snapshot` 생성/복구 시점 일치 여부
- `stage2_finalizer.py` L334~342: DB 실패 시 StateTracker 롤백 — 부분 커밋 방지
- deepcopy 오버헤드 — 200화 시 st_snapshot 크기 추정

**A-3: Validation Pipeline 체이닝**
- DraftValidator → SelfReflector → Consensus → FlowGuard → DuplicateGuard → ContinuityInspector 순서
- 각 Validator 실패 시 전파 vs early return
- warnings 누적 — `validation_results` dict 키 충돌 여부

**A-4: Patch Mode 분기**
- `stage2_orchestrator.py` L403, L538~554: previous_attempt 기반 패치 모드 진입 조건
- `stage2_preflight.py` L698~748: 패치 모드 분기 내 SC 검색 작동 여부

**A-5: 병렬 실행 안전성**
- ThreadPoolExecutor arc_drive + preflight 병렬 — 예외 전파 확인
- `arc_ensemble.py` L179~200: as_completed() timeout 처리 — 부분 결과 시 crash 여부

---

## TF-B: Stage 4 파이프라인 디버깅

### 대상 파일
- `modules/core/stage4_orchestrator.py` (844줄)
- `modules/core/stage4_context_builder.py` (885줄)
- `modules/core/stage4_interview_round.py` (959줄)
- `modules/core/stage4_post_processor.py` (719줄)
- `modules/domain/agents/chief_writer.py` (938줄)
- `modules/domain/agents/chief_writer_context.py` (1,107줄)
- `modules/domain/agents/chief_writer_quality.py` (492줄)

### 검증 관점

**B-1: 3단계 하이브리드 컨텍스트 (Tier 4 회귀)**
- `stage4_context_builder.py` L335~441:
  - Tier 1: `get_manuscripts_range()` off-by-one 여부
  - Tier 2: `episode_meta` 직접 쿼리 — cursor thread safety
  - Tier 3: arc_summary 앵커 — `arc_max_ep < tier2_start` 필터 정확성
  - ep1 시나리오: 모두 빈 결과 시 처리

**B-2: Post-selection Validation (Tier 3 회귀)**
- `stage4_interview_round.py` L682~741:
  - Continuity check 조건 `round_num == 0` 의도 확인
  - History check regex 파싱 실패 시 DB fallback 비용
  - PASS→REJECT downgrade 시 feedback 중복 여부

**B-3: SC-5 Director 벡터 메모리 주입**
- `stage4_interview_round.py` L417~523:
  - `_director_memory_context` 크기 제한 없음 — 컨텍스트 윈도우 초과 가능성
  - slot.max_chars 적용 확인 (SC P1-2 수정 반영)

**B-4: ChiefWriter 앙상블**
- 32개 필드 컨텍스트 — 누락 필드 시 KeyError 가능성
- self-critique + rubric eval 모두 실패 시 처리

---

## TF-C: NPC / State 무결성 디버깅

### 대상 파일
- `modules/domain/agents/state_tracker.py` (1,527줄)
- `modules/domain/agents/state_tracker_plots.py` (952줄)
- `modules/domain/agents/state_tracker_npc.py` (2,008줄)

### 검증 관점

**C-1: bind_db 생명주기 (Tier 1 회귀)**
- 3곳 bind_db 호출 확인 + 미호출 시 silent fail vs crash

**C-2: 사망 NPC 추적**
- deceased=True 설정 경로 — regex 미매칭 시 사망 감지 실패
- dead_npcs 이중 소스 불일치 (state_tracker vs Bible)

**C-3: resolved_plots 상한 (Tier 4 회귀)**
- max_items=30 — 최신/최오래 어느 쪽 유지? 모든 호출부 적용 확인

**C-4: NPC Registry 롤백 (Tier 1 회귀)**
- state_tracker = None 후 다음 에피소드에서 새 생성 확인
- 롤백 후 vec_memory 벡터 잔존 여부

**C-5: regex 폴백 정합성**
- 25개+ 모듈 레벨 regex 한국어 매칭 정확도

---

## TF-D: 인프라 계층 디버깅

### 대상 파일
- `modules/core/db_manager.py` (2,092줄)
- `modules/core/vec_memory.py` (951줄)
- `modules/core/prompt_loader.py` (195줄)
- `modules/core/base_agent.py` (1,362줄)
- `modules/core/context_advisor.py` (673줄)

### 검증 관점

**D-1: DB 스레드 안전성** — RLock 보호 범위, get_manuscripts_range lock 확인
**D-2: VecMemory LIKE 이스케이프** — replace 순서, SQLite backslash escape 지원
**D-3: PromptLoader 안전성 (Tier 5 회귀)** — 삭제 YAML 로드 시 None 반환, 호출부 체크
**D-4: Context Caching** — 50개 상한 초과 처리, API 실패 폴백, TTL 만료
**D-5: ContextAdvisor** — LLM JSON 파싱 실패 폴백, genre_hints 9종 포함 확인

---

## TF-E: Director 체인 디버깅

### 대상 파일
- `modules/domain/agents/director.py` (357줄)
- `modules/domain/agents/director_auditor.py` (1,063줄)
- `modules/domain/agents/director_continuity.py`
- `modules/domain/agents/director_ensemble.py`
- `modules/domain/agents/director_grading.py`
- `modules/domain/agents/director_caching.py`

### 검증 관점

**E-1: SC-Skip 임계값 (Tier 3 회귀)** — ambiguous_lower=50, upper=60, 경계값 처리
**E-2: 5개 서브모듈 위임** — lazy/eager 초기화, AttributeError 가능성, 상태 공유
**E-3: Director Audit 체인** — audit_manuscript → check_character_logic → entity_consistency 흐름
**E-4: Director Ensemble Selection** — 3후보 비교 선택 로직, 동점 처리

---

## TF-F: main_a.py + 통합 시나리오 디버깅

### 대상 파일
- `main_a.py` (3,099줄)
- `modules/core/services/project_service.py` (273줄)
- `config/models.yaml` (36줄)
- `config/settings/validation.yaml` (171줄)

### 검증 관점

**F-1: Cold Start (ep1)** — 빈 데이터 전체 경로, StateTracker 초기화
**F-2: Hot Path (ep30+)** — resolved_plots 상한, 3단계 하이브리드 크기, 캐시 교체
**F-3: 롤백 시나리오** — vec_memory 벡터 잔존, episode_meta 정합성, arc_summary 정합성
**F-4: ContextAdvisor 배선 (SC P0-1 회귀)** — Stage 2/3/4 경로별 가용성
**F-5: 모델 설정 정합성 (Tier 3 회귀)** — manager=gemini-2.5-flash 유효성, fallback_chain

---

## TF-G: Stage 0 + Stage 3 파이프라인 디버깅

### 대상 파일
- `modules/core/stage0/__init__.py` (579줄) — StageZeroManager
- `modules/core/stage0/preset_registry.py` (714줄) — 장르 프리셋
- `modules/core/stage0/story_expander.py` (556줄) — 컨셉→Bible 생성
- `modules/core/stage0/reverse_expander.py` (1,150줄) — 원고→Bible 역설계
- `modules/core/stage0/style_extractor.py` (772줄) — 문체 DNA 추출
- `modules/core/stage3_orchestrator.py` (660줄) — Blueprint 배치 생성
- `modules/core/stage3_context.py` (111줄) — Stage 3 DI 컨텍스트

### 검증 관점

**G-1: Bible 생성 실패 처리**
- `stage0/__init__.py` L237~239: StoryExpander 실패 시 빈 dict 반환 → Treatment 생성 건너뜀
- Bible JSON 스키마 검증 — 필수 필드 누락 시 후속 Stage 크래시 여부
- 주인공 이름 추출 실패 시 기본값 "주인공" — HUD 일관성 영향

**G-2: 역설계(ReverseExpander) 견고성**
- `reverse_expander.py` (1,150줄): 원고 파일 인코딩 (UTF-8/CP949) 처리
- episode_bibles 추출 실패 시 부분 결과 처리
- 대량 원고(100화+) 입력 시 메모리/토큰 제한

**G-3: Stage 3 Blueprint 연속성**
- `stage3_orchestrator.py` L266~278: 직전 화 Blueprint 없음 시 break=True → 후속 에피소드 전체 중단
- Entity Registry 캐시 — Arc 수정 후 재생성 시 stale 데이터 가능성
- SC [S3-I1] 실패 시 SilentPass → 문제 추적 어려움

**G-4: 프리셋 동기화**
- `preset_registry.py`: SUPPORTED_GENRES vs GenreTypes.all() 중복 정의
- NPC HUD 프리셋 — 장르별 필드 정의 불일치 여부
- protagonist_config 스키마 — 모듈 간 접근 방식 통일 여부

**G-5: StyleExtractor 안전성**
- `style_extractor.py`: 참조 원고 경로 검증, 빈 파일 처리
- StyleGuide 생성 후 주입 경로 — 명시적 주입 누락 가능성

---

## TF-H: Genre Guards 디버깅 (14파일)

### 대상 파일
- `modules/core/genre_guards/base_guard.py` (829줄)
- `modules/core/genre_guards/wuxia_guard.py` (661줄)
- `modules/core/genre_guards/hunter_guard.py` (866줄)
- `modules/core/genre_guards/investment_guard.py` (643줄)
- `modules/core/genre_guards/alt_history_guard.py` (491줄)
- `modules/core/genre_guards/composer_guard.py` (517줄)
- `modules/core/genre_guards/cooking_guard.py` (510줄)
- `modules/core/genre_guards/medical_guard.py` (468줄)
- `modules/core/genre_guards/sports_guard.py` (461줄)
- `modules/core/genre_guards/actor_guard.py` (463줄)
- `modules/core/genre_guards/fantasy_guard.py` (357줄)
- `modules/core/genre_guards/style_guard.py` (167줄)
- `modules/core/genre_guards/work_guard.py` (203줄)
- `modules/core/genre_guards/__init__.py` (73줄) — 팩토리

### 검증 관점

**H-1: BaseGuard 수치 변환**
- `base_guard.py` L83~90: `convert_to_numeric()` — "무공", "무형" 등 0이 아닌 값 처리
- 한글 수사 변환 정확도 (일/이/삼/... + 만/억/조)
- 갑자 단위 변환 — 엣지 케이스

**H-2: 비유적 사용 필터 [S-10]**
- `base_guard.py` L154: 금기어 주변 컨텍스트 윈도우 5자 — 너무 좁아 오탐 가능
- "검기가 칼바람처럼" — 비유인데 금기어 "칼바람" 감지 여부

**H-3: run_deep_validation() 다형성**
- 10종 Guard 전부 override 구현하는지
- Guard별 커스텀 검증 — 장르 간 불균형 (일부 Guard는 기본 구현만)
- YAML 로드 실패 시 하드코딩 폴백 — config/genres/{genre}.yaml 없을 때

**H-4: Guard 팩토리**
- `__init__.py`: 장르명→Guard 클래스 매핑 — 미등록 장르 처리 (KeyError vs None)
- WorkGuard + StyleGuard 래핑 — 래핑 순서가 결과에 미치는 영향
- Guard 체인: Genre → Work → Style 순서 확인

**H-5: 장르별 금기어 정합성**
- 각 Guard의 FORBIDDEN_TERMS — 중복, 누락, 오등록 여부
- 장르 간 금기어 충돌 (예: "마법"이 wuxia에선 금기이지만 fantasy에선 허용)

---

## TF-I: Continuity Inspector 체인 디버깅

### 대상 파일
- `modules/domain/agents/continuity_arc.py` (1,014줄)
- `modules/domain/agents/continuity_blueprint.py` (479줄)
- `modules/domain/agents/continuity_manuscript.py` (1,222줄)
- `modules/domain/agents/consensus_validator.py` (458줄)

### 검증 관점

**I-1: Arc 연속성 검증**
- `continuity_arc.py` L362: `ARC_CONTINUITY_INSPECTION_PROMPT.format_map(SafeDict(...))` — Tier 5 SafeDict 전환 확인
- `_arc_python_precheck()` L593~793: 200줄 Python 사전 검증 — 엣지 케이스 (빈 Arc, 1화짜리 Arc)
- Joint Docs 추출 L524~571: LLM 응답 파싱 실패 시 처리

**I-2: Blueprint 연속성 검증**
- `continuity_blueprint.py` L221: SafeDict 전환 확인
- 직전 Blueprint 없을 때 (첫 에피소드) 처리
- Entity Registry 불일치 감지 정확도

**I-3: 원고 연속성 검증 (최대 파일)**
- `continuity_manuscript.py` (1,222줄):
  - `_check_skill_timeline()` L942~1011: 스킬 습득 순서 검증 — 상태 미추적 시 false positive
  - `_check_relationship_jump()` L505~577: 관계 급변 감지 임계값 — 웹소설 특성상 급변 허용?
  - `_check_villain_intelligence()` L577~654: 악역 정보 진화 추적 — 악역 없는 장르(요리, 작곡) 처리
  - `_check_time_flow()` L654~721: 시간 흐름 역행 감지 — 회상 장면 오탐

**I-4: 합의 검증**
- `consensus_validator.py` L298: SafeDict 전환 확인
- 3명 검증자 합의 로직 — 2:1 분할 시 처리 (다수결? 보수적?)
- perspective_name별 bias — 동일 프롬프트에 다른 관점 주입 효과

---

## TF-J: Arc/Blueprint 생성 체인 디버깅

### 대상 파일
- `modules/domain/agents/analyst.py` (1,475줄)
- `modules/domain/agents/four_phase_arc_generator.py` (825줄)
- `modules/domain/agents/arc_corrector.py` (585줄)
- `modules/domain/agents/block_enricher.py` (879줄)
- `modules/domain/agents/state_extractor.py` (859줄)
- `modules/domain/agents/weaver.py` (141줄)

### 검증 관점

**J-1: FourPhaseArcGenerator (주력 Arc 생성기)**
- `four_phase_arc_generator.py` L136~452: 메인 generate() — 4단계 흐름 중 어느 단계 실패 시 전체 실패?
- `patch_arc_with_feedback()` L452~645: 패치 모드 — 원본 Arc 보존 여부
- `_determine_ep_count()` L82~136: 화수 결정 — 최소/최대 범위, 이상 값 입력 시

**J-2: Analyst 레거시 경로**
- `analyst.py`: FourPhase 실패 시 fallback `plan_single_arc_v20()` — 실제 호출되는 조건
- `_validate_arc_state_continuity_v60()` L252~306: 상태 연속성 — FourPhase와 중복 검증?
- treatment_raw_part JSON 파싱 실패 시 빈 리스트 반환 — 후속 로직 영향

**J-3: Arc 자동 수정**
- `arc_corrector.py`: SafeDict 전환 확인 (Tier 5 회귀)
- 수정 범위 제한 — 전체 Arc 재생성 vs 부분 교체 판단 기준
- `_replace_episode_section()` / `_insert_episode_section()` — 위치 계산 오류 가능성

**J-4: Block 농축**
- `block_enricher.py`: SafeDict 전환 확인 (Tier 5 회귀)
- 병렬 농축 `enrich_all_blocks_parallel()` — 순서 보장 여부
- `_check_causal_errors()` L738~809: 인과 오류 감지 후 재농축 — 무한 루프 방지

**J-5: 상태 추출기**
- `state_extractor.py` L233: SafeDict 전환 확인
- `extract_cumulative_state()` L271~393: 누적 상태 — 200화 시 데이터 크기
- `_fallback_extraction()` L542~626: LLM 실패 시 regex 폴백 — 정확도

---

## TF-K: Validation 파이프라인 전면 디버깅

### 대상 파일
- `modules/validation/validation_orchestrator.py` (1,522줄)
- `modules/validation/scoring_validator.py` (1,258줄)
- `modules/validation/continuity_validator.py` (985줄)
- `modules/validation/consistency_validator.py` (617줄)
- `modules/validation/blocking_validator.py` (211줄)
- `modules/validation/blocking_validator_entity_checks.py` (476줄)
- `modules/validation/blocking_validator_scene_checks.py` (462줄)
- `modules/validation/blocking_validator_consistency_checks.py` (379줄)
- `modules/validation/pre_llm_validator.py` (494줄)
- `modules/validation/advisory_validator.py` (211줄)
- `modules/validation/retrospective_validator.py` (365줄)
- `modules/validation/catharsis_timer.py` (395줄)

### 검증 관점

**K-1: Validation Orchestrator 흐름**
- `validation_orchestrator.py` (1,522줄): Pre-LLM → Blocking → Advisory → Scoring → Director 순서
- Blocking 실패 시 Director 심사 스킵 여부 — REJECT 즉시 반환?
- 각 단계 예외 시 전체 파이프라인 중단 vs 다음 단계 진행

**K-2: Blocking Validator — 사망자 검사**
- `blocking_validator_entity_checks.py`: deceased=True NPC의 직접 등장 감지
- 대원칙 4 준수: "회상/언급은 허용, 행동/대사는 금지" — 구분 로직 정확도
- npc_history 미초기화 시 모든 NPC false positive 여부

**K-3: Scoring Validator**
- `scoring_validator.py` (1,258줄): LLM 점수 vs Python 점수 병렬 — 불일치 처리
- 장르별 임계값 (`validation.yaml` scoring 섹션) — 점수 스케일 일관성
- 점수 계산 시 NaN/None 방어

**K-4: Pre-LLM Validator**
- `pre_llm_validator.py` (494줄): 괄호 짝 검사, 숫자 한글 변환, 금기어 검사
- V70 시점(POV) 일관성 체크 — 1인칭/3인칭 혼용 감지 정확도
- 한국어 특수 패턴 (의성어/의태어) 오탐 가능성

**K-5: Catharsis Timer + Retrospective**
- `catharsis_timer.py`: 카타르시스 타이밍 계산 — 좌절 연속 N화 후 해소 강제
- `retrospective_validator.py`: 에피소드 완결 후 회고 — 누적 불일치 추적

---

## TF-L: 운영 계측 + 설정 정합성 디버깅

### 대상 파일
- `modules/core/quality_dashboard.py` (1,100줄)
- `modules/core/pass_rate_monitor.py` (550줄)
- `modules/core/stage2_optimizer.py` (898줄)
- `modules/core/data_collector.py` (457줄)
- `modules/core/narrative_diversity.py` (592줄)
- `modules/core/self_reflection.py` (328줄)
- `config/settings/validation.yaml` (171줄)
- `config/models.yaml` (36줄)
- `config/system.yaml` (30줄)
- `config/smart_retrieval/genre_hints.yaml` (61줄)

### 검증 관점

**L-1: Quality Dashboard**
- `quality_dashboard.py` (1,100줄):
  - `detect_score_regression()` L748~851: 점수 회귀 감지 — 윈도우 크기(5) 충분한지
  - `detect_quality_drift()` L979~1031: 품질 편차 — 기준선 설정 시점
  - `detect_director_bias()` L1031~1087: Director 편향 — 전략별 승률 편향 임계값
  - 메트릭 저장 — DB vs 인메모리, 재시작 시 유실 여부

**L-2: PassRate Monitor**
- `pass_rate_monitor.py`:
  - 통과율 추세 — 하락 알림 임계값
  - 패치 효과 분석 — 패치 전/후 비교 로직 정확성

**L-3: Stage2 Optimizer**
- `stage2_optimizer.py` (898줄):
  - `auto_correct()`: 자동 수정 범위 — 의도치 않은 데이터 변경 가능성
  - `_remove_duplicate_items()`: 중복 판정 기준 — 이름 유사도 vs 정확 매칭
  - `amplify_constraints()`: 제약 강화 — 과도한 제약으로 생성 실패 유발

**L-4: 설정 파일 정합성**
- `validation.yaml`:
  - smart_retrieval 섹션: enabled=false — 활성화 시 예산 설정 충분한지 (S2:20K, S4:50K)
  - feature_flags 6종 전부 true — 누락 flag 시 기본값 확인
  - adaptive_threshold floor=60 — 모든 장르에서 적절한지
- `models.yaml`:
  - 20개 에이전트 모델 지정 — 미지정 에이전트의 기본 모델
  - fallback_chain — 순환 참조 가능성
- `system.yaml`:
  - max_context_chars: 900,000 — Gemini 모델별 실제 한도와 비교
  - 네트워크 재시도 22회 ~10분 — 과도한 대기 시간?

**L-5: Data Collector**
- `data_collector.py`: 학습 데이터 생성 — PII(개인정보) 포함 가능성
- 통계 수집 — 동시성 안전성 (멀티스레드 업데이트)

---

## 산출물

각 TF는 **독립 보고서**를 `docs/2026-02-22/` 하위에 작성한다.

| TF | 산출물 파일명 |
|----|-------------|
| A | `opus_tf5_stage2_debug_audit.md` |
| B | `opus_tf5_stage4_debug_audit.md` |
| C | `opus_tf5_npc_state_debug_audit.md` |
| D | `opus_tf5_infra_debug_audit.md` |
| E | `opus_tf5_director_debug_audit.md` |
| F | `opus_tf5_integration_debug_audit.md` |
| G | `opus_tf5_stage0_3_debug_audit.md` |
| H | `opus_tf5_genre_guards_debug_audit.md` |
| I | `opus_tf5_continuity_debug_audit.md` |
| J | `opus_tf5_arc_gen_debug_audit.md` |
| K | `opus_tf5_validation_debug_audit.md` |
| L | `opus_tf5_ops_config_debug_audit.md` |
| **종합** | `opus_tf5_consolidated_debug_report.md` |

### 종합 보고서 형식

```markdown
# Opus TF-5: 전체 시스템 디버깅 감사 종합 보고서

> 감사일: 2026-02-22
> 감사자: Claude Opus 4.6 × 12 TF
> 대상: ~90K줄 (core 58K + agents 31K)

## Executive Summary
| 위험도 | 건수 |
|--------|------|
| CRITICAL | N |
| HIGH | N |
| MEDIUM | N |
| LOW | N |

## Cross-TF 이슈
(여러 TF 영역에 걸친 문제)

## TF별 요약
### TF-A: Stage 2 ...
### TF-B: Stage 4 ...
### TF-C: NPC/State ...
### TF-D: 인프라 ...
### TF-E: Director ...
### TF-F: 통합 시나리오 ...
### TF-G: Stage 0/3 ...
### TF-H: Genre Guards ...
### TF-I: Continuity ...
### TF-J: Arc/Blueprint 생성 ...
### TF-K: Validation ...
### TF-L: 운영 계측/설정 ...

## Tier 1~5 회귀 확인 결과
(각 Tier 변경 코드의 회귀 여부)

## Codex 핸드오프 권장 작업
### 즉시 수정 (CRITICAL/HIGH)
### 중기 수정 (MEDIUM)
### 장기 (LOW)
```

---

## 실행 지시 (Codex)

### 진행 상태

| TF | 상태 | 비고 |
|----|------|------|
| B | **완료** | HIGH 1, MEDIUM 2 → 감리 CONFIRMED 3/3 |
| A | **완료** | HIGH 1, MEDIUM 1 (재검증 완료) |
| C | **완료** | HIGH 1, MEDIUM 1 |
| D | **완료** | HIGH 2, MEDIUM 1 |
| E | **완료** | HIGH 1, MEDIUM 1 |
| F | **완료** | HIGH 2, MEDIUM 1 |
| G | **완료** | HIGH 2, MEDIUM 1 |
| H | **완료** | HIGH 1, MEDIUM 2 |
| I | **완료** | HIGH 1, MEDIUM 2 |
| J | **완료** | HIGH 2 |
| K | **완료** | HIGH 2, MEDIUM 1 |
| L | **완료** | HIGH 2, MEDIUM 1 |

### TF-B 확정 이슈 (패치 보류 — 전체 감사 완료 후 일괄 처리)

| ID | 위험도 | 파일 | 요약 |
|----|--------|------|------|
| B-1 | HIGH | `stage4_post_processor.py` L165,299,316 | Manager future 타임아웃 시 `audit={}` 유지 → 정산 전량 유실 |
| B-2 | MEDIUM | `stage4_context_builder.py` L386 / `stage4_interview_round.py` L908 | Tier2 `[EP N summary] text` vs 파서 `]\n` 포맷 불일치 → 11~30화 충돌검사 누락 |
| B-3 | MEDIUM | `blueprint.py` L39 / `context_advisor.py` L587 / `stage4_context_builder.py` L92 | `scene_breakdown` dict 계약 vs SC list-only 처리 → scene_context 슬롯 비활성 |

### 실행 순서

1. **나머지 11개 TF (A, C~L)를 순차적으로 감사한다.**
   - 각 TF당 1개 보고서를 `docs/2026-02-22/` 하위에 작성한다.
   - 파일명은 위 산출물 테이블을 따른다.
   - 반드시 **이 문서 상단의 [Codex 감사 작업 지시]를 준수**한다.
   - TF-B 보고서(`opus_tf5_stage4_debug_audit.md`)를 품질 기준으로 삼는다.

2. **순서 권장**: A → C → D → E → F → G → H → I → J → K → L
   - A(Stage2)와 C(NPC/State)를 먼저: B(Stage4) 이슈와 겹치는 파일이 있어 교차 확인 가능
   - G~L은 독립적이므로 순서 무관

3. **각 TF 완료 후 이 테이블의 상태를 업데이트**한다.

4. **12개 TF 전량 완료 후**:
   - 종합 보고서(`opus_tf5_consolidated_debug_report.md`) 작성
   - 발견된 모든 이슈를 위험도별로 집계
   - Cross-TF 이슈 (여러 TF에 걸친 문제) 별도 정리
   - **패치는 종합 보고서 완성 후 별도 오더로 진행** (이 감사 내에서는 코드를 수정하지 않는다)

### 주의사항

- **코드 수정 금지**: 이 감사는 조사/문서화만 한다. 버그를 발견해도 코드를 고치지 않는다.
- **오탐 최소화**: TF-B 감리에서 3/3 CONFIRMED (FALSE POSITIVE 0건)이었다. 이 수준을 유지할 것.
- **B-1~B-3과 관련된 파일**을 다른 TF에서 다시 만나면, B 이슈와 독립적인 새 이슈만 보고한다 (중복 보고 금지).
- **파일을 직접 열지 않고 주장하면 안 된다.** 모든 라인 번호와 코드 인용은 실제 파일 내용 확인 후 기재.

---

*Generated for Codex execution — Claude Opus 4.6 × 12 TF parallel debug audit*
*Total coverage: ~90K lines across 163 modules*
