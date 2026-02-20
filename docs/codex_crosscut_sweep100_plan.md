# 크로스컷 시나리오 주도 100-Round Sweep Plan

## 기존 스윕과의 차이점

| 관점 | 기존 sweep100_manual | 기존 debug_sweep100 | **본 플랜 (신규)** |
|------|---------------------|--------------------|--------------------|
| 축 | 파일별 순차 읽기 | 파일별 순차 읽기 | **시나리오/데이터 흐름 축** |
| 단위 | 1 라운드 = 1~2 파일 | 1 라운드 = 1~2 파일 | 1 라운드 = **1개 end-to-end 시나리오** |
| 검증 대상 | caller-callee 계약 | 크래시 패턴 매칭 | **경계 입력이 파이프라인을 관통할 때 전체 경로** |
| 강점 | 모듈 내부 완결성 높음 | 패턴별 수색 체계적 | **모듈 간 연결(seam) 버그 발견에 강함** |
| 약점 | 모듈 간 상호작용 사각 | 같은 파이프라인 중복 | **단일 파일 깊이 상대적 약함** |

> **핵심 아이디어**: "LLM이 Episode 1에서 빈 딕트를 반환하면?"처럼 **특정 경계 시나리오 하나를 던지고**, 그 데이터가 Stage 0 → 2 → 3 → 4 → PostProcessor까지 관통하며 각 모듈에서 어떻게 처리되는지 추적한다.

---

## 라운드 구조 — 10개 카테고리 × 10 시나리오

### Phase 1: 빈값/None 관통 (R01–R10)

경계 데이터가 파이프라인 전체를 관통할 때 각 스테이지별 처리.

| Round | 시나리오 | 관통 경로 |
|-------|---------|-----------|
| R01 | LLM이 Arc 생성에서 **빈 dict `{}`** 반환 | `analyst.py` → `stage2_preflight` → `stage2_validation_pipeline` → `stage2_finalizer` |
| R02 | LLM이 Arc 생성에서 **`None`** 반환 | 동일 경로, `_extract_json_robust` 분기 확인 |
| R03 | LLM Blueprint 응답이 **빈 문자열 `""`** | `blueprint_ensemble` → `stage3_orchestrator` → DB commit |
| R04 | LLM 원고 응답이 **list `["text"]`** (dict 대신) | `chief_writer` → `stage4_interview_round` → `director_auditor` |
| R05 | `arc_data.get("ep_count")` = **`None`** 관통 | `analyst` → `stage2_validation_pipeline:ep_count` int 캐스트 경로 |
| R06 | `arc_data.get("ep_start")` = **string `"5"`** 관통 | `analyst` → 산술 연산 → `stage2_finalizer` |
| R07 | `state_changes` = **string (list 대신)** 관통 | `state_extractor` → `stage4_post_processor` 반복문 |
| R08 | `blueprint.get("scenes")` = **`None`** | `blueprint_ensemble` → `stage4_context_builder` 장면 반복 |
| R09 | `selected_candidate` = **`None`** (key 있으나 값 null) | `director_ensemble` → `stage4_interview_round` chained `.get()` |
| R10 | `physical_inventory` = **dict 혼재 `[str, {"name":"검"}]`** | `state_tracker` → `continuity_inspector` → `stage2_validation_pipeline` set연산 |

### Phase 2: Episode 경계 조건 (R11–R20)

Episode 1 (첫 회차), 단일 Arc, 마지막 Episode 등 경계 상황.

| Round | 시나리오 | 관통 경로 |
|-------|---------|-----------|
| R11 | Episode 1 — `episode-1=0` → 이전 원고 조회 빈 결과 | `stage4_context_builder` → `lookback_digest` → `chief_writer_context` |
| R12 | 단일 Arc(1개) — `volumes_strategy=[]` | `stage2_orchestrator` → `stage2_preflight` → `StateTracker` |
| R13 | 마지막 Episode — Arc 경계 넘김 | `stage3_orchestrator` → `stage4_orchestrator` 루프 종료 |
| R14 | Arc 롤백 후 `existing_tracker_arcs > len(all_refined_arcs)` | `stage2_orchestrator:161` StateTracker 리빌드 경로 |
| R15 | Blueprint 실패 후 다음 에피소드 연속성 검사 | `stage3_orchestrator:259` 이전 blueprint 부재 → 강제 중단 |
| R16 | 5라운드 인터뷰 전부 REJECT → 폴백 | `stage4_orchestrator:641` `get_int_input` 비대화형 |
| R17 | CoVe `should_regenerate=True` 후 재시도 피드백 | `stage4_orchestrator:621` PASS 후보 오버라이드 |
| R18 | DB commit 실패 후 StateTracker 스냅샷 롤백 | `stage2_finalizer:311` 롤백 무결성 |
| R19 | 에피소드 0건(arcless) 상태에서 Stage 3 진입 | `stage3_orchestrator:69` 전제 가드 |
| R20 | 다중 Arc 병렬 처리 후 순서 복원 | `stage2_orchestrator:308` `_success_indices + recovery_map` |

### Phase 3: 동시성/스레드 안전 (R21–R30)

ThreadPoolExecutor, 공유 상태, 캐시 경쟁.

| Round | 시나리오 | 관통 경로 |
|-------|---------|-----------|
| R21 | ChiefWriter 3-전략 병렬 생성 중 1개 타임아웃 | `chief_writer:252` → `as_completed` → 부분 수집 |
| R22 | `base_agent._context_caches` 병렬 read/write 경쟁 | `base_agent:1079` 무잠금 dict 접근 |
| R23 | `_quota_exhausted_models` 병렬 갱신 경쟁 | `base_agent` 무잠금 dict 접근 |
| R24 | `_cumulative_bible_cache` 무한 성장 | `db_manager` 메모리 누수 경로 |
| R25 | Stage2 preflight `ThreadPoolExecutor` `with` 블록 종료 대기 | `stage2_preflight:103` cancel 미동작 |
| R26 | `arc_ensemble` Future cancel 결과 미확인 | `arc_ensemble:184` |
| R27 | `blueprint_ensemble` Future cancel 결과 미확인 | `blueprint_ensemble:224` |
| R28 | `consensus_validator` Future cancel 결과 미확인 | `consensus_validator:264` |
| R29 | `director_auditor` 병렬 감사 스레드 정리 | `director_auditor:895` |
| R30 | `adaptive_retry._failures` 리스트 무한 성장 | `adaptive_retry` 메모리 누수 |

### Phase 4: 캐시 정합성 (R31–R40)

캐시 키/값 불일치, 스테이지간 캐시 전파.

| Round | 시나리오 | 관통 경로 |
|-------|---------|-----------|
| R31 | `cumulative_state_cache` ctx↔app 동기화 불일치 | `stage2_preflight:147` → `prompt_builder:530` stale 캐시 |
| R32 | `_cumulative_state_cache_key` 업데이트 → app 캐시 미반영 | `stage2_preflight:391` key-only sync |
| R33 | Arc 카운트 변경 후 캐시 hit/miss 전환 | `prompt_builder:530` 캐시 키 검증 |
| R34 | Entity registry 캐시 무효화 인덱스 리셋 | `stage3_orchestrator:365` 추출 실패 후 `-1` |
| R35 | Stage4 `_lazy_init` 후 ctx reset 시 서브모듈 무효화 | `stage4_orchestrator:233` |
| R36 | `stage_rejection_history` = `None` 상태에서 REJECT 처리 | `stage2_finalizer:668` append |
| R37 | ScoringValidator `pass_threshold` 동적 변경 후 일관성 | 적응형 난이도와 고정 가중치 간 상호작용 |
| R38 | 에피소드 간 `world_state` 롤백 후 `fact_ledger` 정합 | `world_state` → `fact_ledger` 리플레이 |
| R39 | Stage2 → Stage3 context 전달 시 슬롯 바인딩 누락 | `stage2_context` → `stage3_context` 전환 |
| R40 | Director 캐싱 무효화 타이밍 문제 | `director_caching:175` |

### Phase 5: 프롬프트/템플릿 인젝션 (R41–R50)

사용자/LLM 입력이 프롬프트 템플릿에 주입될 때 발생하는 문제.

| Round | 시나리오 | 관통 경로 |
|-------|---------|-----------|
| R41 | 원고 텍스트에 `{current_state_json}` 리터럴 포함 | `manager.py:140` chained `.replace()` 오염 |
| R42 | 피드백/원고에 `{}` 중괄호 → f-string 충돌 | `chief_writer:735` brace escape |
| R43 | LLM 응답에 `{` 포함 → `format()` KeyError | `prompt_builder` 전체 경로 |
| R44 | 패치 모드 프롬프트 로더 실패 → 폴백 템플릿 | `chief_writer:686` |
| R45 | `re.compile()` 에 LLM 유래 미이스케이프 문자열 | `chief_writer_quality` 정규식, genre guard 정규식 |
| R46 | Arc `NPC_name`에 정규식 메타문자 (`(`, `[`) 포함 | `continuity_manuscript` → 정규식 매칭 |
| R47 | YAML 프롬프트 키가 코드 기대와 불일치 | `prompt_loader` → `analyst_prompts` → `director_prompts` |
| R48 | `arc_position_guide` 에피소드 비율 0.0 / 1.0 경계 | `prompt_builder:50` |
| R49 | `high_impact_zone` 장면 수 0 / 1 경계 | `prompt_builder:122` |
| R50 | 프롬프트 mandatory context 오버사이즈 절삭 | `stage4_orchestrator:478` section-drop |

### Phase 6: 장르/도메인 분기 (R51–R60)

장르별 가드/전략 분기 경로.

| Round | 시나리오 | 관통 경로 |
|-------|---------|-----------|
| R51 | 무협 장르 → `wuxia_guard` 금기어 정규식 이스케이프 | `base_guard` → `wuxia_guard` |
| R52 | 헌터 장르 → `hunter_guard` 오버라이드 경로 | `base_guard` → `hunter_guard` → deep validation |
| R53 | 투자 장르 → `investment_guard` + financial_registry | `stage2_orchestrator:178` 조건부 persist |
| R54 | 판타지 장르 → `fantasy_guard` 최소 검증 | `fantasy_guard:333` |
| R55 | 요리/작곡 장르 → 특화 가드 체인 | `cooking_guard` + `composer_guard` |
| R56 | 미지정 장르 → `base_guard` 기본 경로 | Guard 체인에서 매칭 실패 시 |
| R57 | Guard 체인 순서: GenreGuard → WorkGuard → StyleGuard | `__init__.py:70` 래퍼 로직 |
| R58 | `martial_manager` 전투 파워 계산 0 나누기 | `martial_manager:564` 파워 스케일링 |
| R59 | `power_scaling` 극단값 입력 | `power_scaling:502` |
| R60 | 장르별 `strategies/*.py` 전략 선택 분기 | `SovereignApp` 장르 설정 → 전략 로드 |

### Phase 7: DB/IO 장애 시나리오 (R61–R70)

DB 오류, 파일 I/O 실패, 네트워크 타임아웃.

| Round | 시나리오 | 관통 경로 |
|-------|---------|-----------|
| R61 | SQLite `safe_commit` 실패 → 롤백 누락 | `stage2_finalizer:311` → `db_manager` |
| R62 | `get_all_episode_bibles()` 중 JSON 파싱 깨짐 | `db_manager:767` row-level 가드 부재 |
| R63 | `vec_memory.memorize_v20_episode()` 부분 DML 트랜잭션 누수 | `vec_memory:228` rollback 미호출 |
| R64 | 프로젝트 파일 I/O 실패 (권한/잠금) | `project_manager` → `stage4_post_processor` |
| R65 | YAML 설정 파일 로드 실패 | `config_manager` → `prompt_loader` |
| R66 | Gemini API 타임아웃 → `base_agent.ask()` 재시도 | `base_agent` → `adaptive_retry` |
| R67 | API 할당 초과 → `_quota_exhausted_models` 갱신 | `base_agent` 모델 전환 경로 |
| R68 | DB RLock 재진입 데드락 시나리오 | `db_manager:56` reentrant lock 경계 |
| R69 | Episode Bible JSON 저장 → 조회 라운드트립 | `db_manager` JSON string 보존 |
| R70 | `crash_dump.log` 기록 실패 시 파이프라인 영향 | `main_a.py` 에러 핸들링 |

### Phase 8: 상태 추적 정합 (R71–R80)

StateTracker, NPC, Plot, FactLedger 간 상태 일관성.

| Round | 시나리오 | 관통 경로 |
|-------|---------|-----------|
| R71 | NPC 사망 처리 후 다음 에피소드 재등장 | `state_tracker_npc` → `continuity_manuscript` |
| R72 | NPC 관계 변경 + 팩션 이동 동시 발생 | `relationship_tracker_npc` + `relationship_tracker_factions` |
| R73 | Plot resolved 후 재참조 | `state_tracker_plots:942` resolved 처리 |
| R74 | `full_extract_from_arcs` 누적 추출 순서 | `state_tracker:1453` |
| R75 | `state_delta_tracker` 델타 비교 타입 불일치 | `state_delta_tracker:419` |
| R76 | `continuity_inspector` facade → `continuity_manuscript` 위임 완전성 | `continuity_inspector:546` |
| R77 | `continuity_arc` 이전 Arc 미존재 → 빈 이력 비교 | `continuity_arc:1002` |
| R78 | `world_state` 롤백 후 entity 이력 제한 위반 | `world_state:426` |
| R79 | `fact_ledger` 엔티티 병합 충돌 | `fact_ledger:540` |
| R80 | `cross_agent_verifier` 교차 검증 결과 병합 | `cross_agent_verifier:492` |

### Phase 9: Validation 파이프라인 상호작용 (R81–R90)

다중 validator 결과 합산, 판정 전파.

| Round | 시나리오 | 관통 경로 |
|-------|---------|-----------|
| R81 | `blocking_validator` BLOCK → 나머지 validator 스킵 | `validation_orchestrator` 조건부 skip |
| R82 | `pre_llm_validator` 감점 합산 → 총점 오류 | `pre_llm_validator` + `scoring_validator` |
| R83 | `scoring_validator` 가중치 합산 100% 초과/미달 | `scoring_validator` 가중치 체계 |
| R84 | `consistency_validator` + `continuity_validator` 이중 감점 | 동일 이슈 중복 패널티 |
| R85 | `retrospective_validator` 과거 데이터 DB 조회 실패 | `retrospective_validator:269` |
| R86 | `action_scene_evaluator` 빈 장면 → 점수 0 | `action_scene_evaluator:455` |
| R87 | `catharsis_timer` 타이밍 역전 | `catharsis_timer:223` |
| R88 | `batch_validator` + `advisory_validator` 결과 병합 | `batch_validator:298` + `advisory_validator:181` |
| R89 | Validator 결과 `verdict` 가 PASS인데 점수가 기준 미달 | `validation_orchestrator` 최종 verdict 결정 |
| R90 | `blocking_validator_entity_checks` + `scene_checks` 결합 | 엔티티/장면 동시 블로킹 |

### Phase 10: 초기화/종료/전체 흐름 (R91–R100)

SovereignApp 생애주기, Stage 전환, 종합 시나리오.

| Round | 시나리오 | 관통 경로 |
|-------|---------|-----------|
| R91 | `SovereignApp.__init__` 초기화 순서 의존성 | `main_a.py` L1-750 |
| R92 | Stage 0 → Stage 2 전환 시 상태 잔류 | `stage0` → `main_a.py` DI 바인딩 |
| R93 | Stage 2 → Stage 3 전환 시 context 슬롯 전환 | `stage2_context` → `stage3_context` |
| R94 | Stage 3 → Stage 4 전환 시 tracker 동기화 | `stage3_orchestrator` → `stage4_orchestrator` |
| R95 | 전체 파이프라인 정상 흐름 1-arc 1-episode | 전체 E2E |
| R96 | 전체 파이프라인 다중 arc 다중 episode | 전체 E2E |
| R97 | 중간 실패 후 재개 (`resume_condition`) | `main_a.py` 재개 로직 |
| R98 | 세션 종료 → `run_post_episode_tasks` 대화형 입력 | `stage4_post_processor:614` |
| R99 | `constants.py` 하드코딩 값 변경 시 연쇄 영향 | `constants:762` → 전체 참조 |
| R100 | 전체 미커버 seam 점검 (Phase 1-9 결과 교차 검증) | 종합 |

---

## 실행 규칙

### 라운드별 출력 형식

```markdown
## Round N — [시나리오 한줄 요약]

### 시나리오 정의
- **경계 입력**: [정확한 입력 값/상태]
- **기대 동작**: [정상적으로 처리되어야 할 방식]
- **관통 경로**: `파일A:함수` → `파일B:함수` → `파일C:함수`

### 경로 추적 (각 파일별)
**[파일A:L100]**
- 코드: `실제 코드 copy-paste`
- 입력 처리: [경계 입력이 여기서 어떻게 처리되는지]
- 다음 단계로 전달되는 값: [변환 결과]

**[파일B:L200]**
- 코드: `실제 코드 copy-paste`
- 입력 처리: [변환된 데이터가 여기서 어떻게 처리되는지]
- 문제점 or 안전 이유: [구체적 설명]

### 발견
- **BUG / RISK / SAFE**: [판정]
- **근거**: [코드 인용 + 추적 결과]
- **기존 스윕 교차**: [기존 sweep100_manual 또는 debug_sweep100에서 커버 여부]

---
## Round N 완료
```

### 핵심 규칙
1. **파일은 직접 읽는다** — 시나리오 경로상의 모든 파일을 실제로 열어 읽는다.
2. **최소 3개 파일 관통** — 매 라운드 최소 3개 파일의 코드를 추적한다.
3. **기존 스윕 교차 확인** — 기존 sweep100_manual / debug_sweep100에서 동일 파일·라인이 이미 검사되었으면 명시한다.
4. **FP 방지** — `codex_debug_sweep100_order.md` §4의 FP-1~FP-10 룰을 매 라운드 참조한다.
5. **코드 수정 금지** — 탐지·보고만 한다.

### 체크포인트 (매 10라운드)
```markdown
## Checkpoint — Round XX

| Metric | Value |
|--------|-------|
| Bugs (CRITICAL/HIGH/MEDIUM) | N (C: a, H: b, M: c) |
| Risks | N |
| Safe (확인 완료) | N |
| 기존 스윕 중복 | N |
| 신규 발견 (기존 미커버) | N |
| 관통 파일 수 (누적) | N |
```

---

## 검증 계획

### 자체 검증
- 모든 라운드에 시나리오 정의 + 경로 추적 + 발견 존재 확인
- 매 라운드 최소 3개 파일 코드 인용 확인
- FP-1~10 교차 확인 누락 여부

### 기존 스윕 대비 부가가치
- sweep100_manual에서 커버하지 못한 **모듈 간 seam 버그** 발견 건수
- debug_sweep100에서 커버하지 못한 **시나리오 기반** 신규 발견 건수

---

## 결과 파일
- 플랜: `docs/codex_crosscut_sweep100_plan.md`
- 결과: `docs/codex_findings_crosscut_sweep100.md`

---

## 무중단 수동검사 강제 가드 (필수)

본 섹션은 본 플랜 수행 시 우선 적용되는 강제 규칙이다.

### 1) 수동 검사 강제 / 검색 금지
- 금지 도구: `rg`, `grep`, `freg`, `Select-String`, 그 외 패턴 검색 기반 코드 스캔 전부.
- 허용 방식: 파일을 직접 열람하여 라인 단위로 확인 (`Get-Content` 등 단순 열람만 허용).
- 근거 규칙: 모든 판단은 `file:line` 형태의 수동 열람 근거를 포함해야 한다.
- 위반 처리: 검색 기반 근거가 1회라도 발견되면 해당 라운드는 무효로 간주하고 재수행한다.

### 2) 무중단 수행 규칙
- 기본 원칙: Round 1~100은 사용자 재질문 없이 연속 수행한다.
- 중단 허용(하드 블로커) 조건:
  - 대상 파일 실존 불가
  - 파일 권한/잠금으로 열람 불가
  - 문서/코드 파손으로 구문 단위 판독 자체가 불가
- 하드 블로커 발생 시 반드시 아래 포맷으로 1회 보고 후 즉시 재개 조건을 명시한다:
  - `Blocker`: [원인]
  - `Last Completed Round`: [N]
  - `Resume Condition`: [필요 조치]

### 3) 라운드 출력 스키마 (고정)
- 각 라운드는 아래 섹션을 반드시 모두 포함:
  - `Read Files`
  - `Manual Inspection Evidence`
  - `Confirmed Bugs`
  - `Risks`
  - `False Positives Excluded`
  - `Test Gaps`
- `Manual Inspection Evidence`는 최소 2개 bullet, 최소 1개 이상의 `file:line` 포함 필수.
- `Confirmed Bugs`가 `none`이 아닌 경우:
  - `[P0-..P3-]` severity 태그 필수
  - `file:line` 필수
  - `intent check` 설명 필수
- 각 라운드에 `Intent Alignment Check`를 추가한다:
  - `Candidate Intent`
  - `Intent Evidence (file:line)`
  - `Conflict Evidence (file:line or none)`
  - `Decision (Aligned / Conflict / Unclear)`

### 4) 체크포인트/품질 게이트
- 매 10라운드마다 체크포인트를 작성한다.
- 체크포인트에는 최소 아래 항목을 포함한다:
  - Cumulative Confirmed Bugs (P0~P3 분해)
  - Cumulative Risks
  - Cumulative False Positives Excluded
  - Cumulative Test Gaps
  - Phase False-Positive Ratio
  - Consecutive Empty Rounds
  - Manual Evidence Compliance Rate

### 5) 오탐 방지 / 설계 의도 보존 게이트
- `BUG` 확정 전 아래 항목을 모두 기록한다:
  - `Intent Source`: 주석/함수명/정책명/상수/가드 로직 근거 (`file:line`)
  - `Caller Contract`: 상위 호출자 기대 동작 근거 (`file:line`)
  - `Fallback Policy`: 비차단/Advisory/Fallback 경로 존재 여부 (`file:line`)
  - `Reachability`: 실제 도달 가능한 호출 경로 (`file:line`)
  - `Blast Radius`: 장애 전파 범위와 발현 조건
- 판정 규칙:
  - 의도 근거와 충돌 근거가 동시에 존재하면 `Confirmed Bugs` 금지, `Risks`로 분류
  - 정책 의도와 합치하고 가드가 존재하면 `False Positives Excluded`로 분류
  - 의도와 명확히 충돌 + 도달 가능 + 보호 부재일 때만 `Confirmed Bugs`로 확정
- 금지 규칙:
  - 단일 라인/단일 파일 근거만으로 버그 확정 금지 (최소 2파일 근거 필수)
  - 일반 베스트 프랙티스 위반만으로 버그 확정 금지
- 기록 의무:
  - 모든 BUG/RISK 항목에 `intent check: pass/fail/unclear` 표기
  - `unclear`는 BUG 금지, RISK로 유지 후 후속 검증 항목에 추가

### 6) 판정 주권 규칙 (Director Sovereignty / 내각제)
- Python/정적 규칙/검증 스크립트는 `WARNING` 또는 `ADVISORY`까지만 가능하며, 단독 `REJECT`/`BLOCK` 판정은 금지한다.
- 자동 검사의 역할은 이상 징후 플래그와 근거 수집 보조에 한정한다.
- 최종 판정 주권:
  - `REJECT`/`PASS` 최종 결정은 Director LLM(단일 또는 ensemble)만 수행한다.
- 충돌 처리:
  - Python 경고 vs Director 승인: `False Positives Excluded`로 기록
  - Python 경고 vs Director 반려: Director 근거와 함께 `Confirmed Bugs` 또는 `Risks`로 기록
- Director 판정 불가(응답 없음/보류) 시:
  - `Pending Director Decision`으로 기록하고 `REJECT` 확정 금지

### 7) 최종 유효성 판정 (완료 조건)
- 아래 검증을 모두 통과해야 완료로 인정한다:
- `python scripts/validate_manual_sweep.py docs/codex_findings_crosscut_sweep100.md --from-round 1 --to-round 100`
- `python scripts/validate_manual_sweep.py docs/codex_findings_crosscut_sweep100.md --from-round 1 --to-round 100 --max-fp-ratio 0.35 --max-fp-streak 2`
- 위 Python 검증은 문서 형식/근거 충족 여부 확인용이며, 최종 내용 판정(REJECT/PASS) 권한이 아니다.
- 검증 실패 시 실패 라운드를 수정하고 재검증한다.
