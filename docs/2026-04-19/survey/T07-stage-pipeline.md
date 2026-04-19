# T07: Stage 파이프라인 (Stage0~4) 흐름 분석

Surveyor: Claude Code (Terminal 7)
Date: 2026-04-19
Scope: Stage0→1→2→3→4 전이 흐름, 진입/종료 조건, 핸드오프 계약, 복구 경로, Arc 교차점

## 1. Executive Summary

- 성숙도 판정: **Pre-production** (완결된 5단계 파이프라인 + 계약 기반 핸드오프 + 다층 복구 경로 구축, 그러나 운영 자동화·동시성·정합성 갭 잔존)
- 한줄 요약: 5단계 파이프라인은 "계약 우선 설계(contract-first)"로 Stage2→4 간 권위 패킷(`cross_stage_authority_packet.v1`)을 명시적으로 전달하고, Stage3는 에피소드 단위·Stage4는 라운드 단위로 최대 5~9회까지 적응형 재시도를 돌리지만, 실패 경로의 일부가 `input()` 기반 대화형 폴백에 묶여 있어 무인 운영 시 파이프라인이 정지할 수 있다.

## 2. 강점 (Strengths)

**(S1) 명시적 단계 오케스트레이터 분리 — "Orchestrator per Stage"**
- `modules/core/stage2_orchestrator.py:79` (`Stage2Orchestrator`, 1,773 LOC)
- `modules/core/stage3_orchestrator.py:808` (`Stage3Orchestrator`, 3,586 LOC)
- `modules/core/stage4_orchestrator.py:533` (`Stage4Orchestrator`, 2,802 LOC)
- `modules/core/stage0/__init__.py:53` (`StageZeroManager`, 1,060 LOC)
- 각 Stage가 자체 Context DI (`Stage2Context.from_app`, `Stage3Context.from_app`, `Stage4Context.from_app`)를 통해 `SovereignApp` 상태를 얕게 스냅샷 — 테스트 격리·대리 실행 가능.
- `main_a.py:2254` `_dispatch_main_process_choice`는 Stage 진입점을 숫자 메뉴 → 얇은 델리게이트로 고정 (`_stage_2_arcs` → `Stage2Orchestrator.stage_2_arcs_async_logic`).

**(S2) Stage 간 명시 계약 (schema-versioned handoff)**
- `modules/core/stage0_handoff.py:11~15` — `STAGE0_CONTRACT_SCHEMA = "stage0.material.v1"`. Treatment=canonical, Bible=projection 으로 "단일 진실(single-source)" 분리.
- `modules/core/stage0_handoff.py:617` `check_plot_roadmap_ready()` — Stage2 진입 전 precondition gate. `Stage2Orchestrator._bootstrap_stage2_arc_pipeline` (stage2_orchestrator.py:304) 에서 즉시 호출.
- `modules/core/cross_stage_authority_packet.py:157` `build_cross_stage_authority_packet()` — Stage2 finalizer가 생성해 Stage3/4로 전달하는 권위 패킷 (`CROSS_STAGE_AUTHORITY_PACKET_VERSION = "cross_stage_authority_packet.v1"`). 위치/장비/부상/내공/자본 등의 field_authority 소스 우선순위를 명시.
- `modules/core/stage_cross_stage_contract.py:7~16` — `OPENING_TRANSITION_DIRECT/EXPLICIT/JUMP` 3종 타입으로 Stage3→Stage4 장면 전이 계약 정규화.

**(S3) 에피소드 순차 의존성 강제 (continuity enforcement)**
- `stage3_orchestrator.py:1148~1159` — `working_ep > 1`이면 `prev_bp_check = get_blueprint(working_ep-1)` 존재 여부를 검사하고, 없으면 `continuity_block` audit_event를 발행하며 break.
- `stage3_orchestrator.py:952` `production_head = max(existing_bp_max, existing_ms_max_ep)` — Blueprint 테이블과 원고 테이블을 동시에 참조해 자동 재개 지점을 도출 (MVP 수준의 fresh-start 로직이 아니라 두 소스 중 큰 값 우선).
- `stage2_orchestrator.py:374~387` — Manuscript에서 Arc 번호 역추적해 Arc/원고 드리프트 탐지 후 경고.

**(S4) 다층 복구 경로 (retry → human-in-loop → abort)**
- **Stage3 per-episode**: `stage3_envelope_builder.py:188` `max_retries=9` (ThreePhase Blueprint 내부 재시도).
- **Stage4 per-episode round loop**: `stage4_orchestrator.py:587~594` `_get_stage4_max_rounds()` 기본 5라운드; `stage4_orchestrator.py:1862~1895` 소진 시 "최선 결과물 채택/건너뛰기/인간 검토" 3지선다.
- **Stage2 per-arc**: `stage2_orchestrator.py:707~774` `_handle_stage2_arc_failure` — 4지선다 (건너뛰기/중단/자동 재시도/수동 개입). 실패 리포트를 `logs/arc_{N}_failure_report.txt`로 상세 기록.
- **V75-B blueprint regeneration**: `stage4_orchestrator.py:1862~1864` — 라운드 소진 + blueprint_regenerated 플래그 → "Arc 재생성 제안" (Stage4→Stage2 역방향 escalation 힌트).
- **V75-D inplace patch**: `stage4_orchestrator.py:1961~2211` `_apply_v75d_inplace_repair` — 원고 in-place 패치로 재생성 회피.

**(S5) LLM 호출·비용 최적화 계층**
- `stage3_orchestrator.py:1377~1479` `_collect_stage3_smart_retrieval_bundle` — `SemanticQueryBroker` 기반 selective retrieval; feature flag (`smart_retrieval.enabled`) + stage-specific toggle 분리.
- `modules/domain/agents/blueprint_ensemble.py:437~438` `self.max_workers = 3` — fan-out 3-worker ThreadPoolExecutor.
- MEMORY.md 기준 6개 고비용 사이트에 Context Caching 적용 완료 (ChiefWriter/ArcEnsemble/BlueprintEnsemble fan-out, DirectorEnsemble stable/variable, DirectorContinuity Blueprint/Manuscript).
- `stage3_orchestrator.py:3550` `save_cost_record()` — 에피소드별 토큰 비용 DB 기록.

**(S6) 관측성(Observability) 기본기 보유**
- `stage3_orchestrator.py:95~125` `_build_stage3_observability_flags()` — `source_anchor_summary` 등 판정 근거를 구조화해 UI 로그와 DB 모두에 적재.
- `stage3_orchestrator.py:2216,2231` `db.save_stage_attempt()` + `db.save_director_selection()` — attempt-key 기반 판정 추적.
- `stage4_orchestrator.py:1920~1931` Shadow-mode로 다른 `max_rounds`와의 회귀 비교 로그.

## 3. 개선 필수 (Critical Issues) — P0

**(P0-1) Stage2 실패 경로의 대화형 `input()` 블로킹 — 무인 운영 정지 위험**
- `stage2_orchestrator.py:713` `user_choice = (await asyncio.to_thread(input, "   선택 (기본: 2): ")).strip()`
- `stage2_orchestrator.py:737~746` 수동 개입(옵션 4)에서 추가 `input()`로 대기.
- **영향**: `_one_stop_pipeline_frontier_lag` (main_a.py:4041~) 자동 체인에서 Arc 실패가 발생하면 `EOFError`로 기본값 "2"(중단) 처리는 되지만 오퍼레이터 개입 없이는 재시도 불가. 크론/배치 환경에서 Arc 1개 실패가 전체 파이프라인을 중단시킨다.
- **권장 조치**: policy.yaml 기반 non-interactive 기본 전략 (`stage2.arc_failure.default_action: skip|abort|retry_once`) 도입. `EOFError` 폴백이 무조건 "abort"인 현재 동작은 `_get_stage4_exhaustion_default_choice()` (stage4_orchestrator.py:614)와 같은 정책 기반 분기로 통일.

**(P0-2) `_init_state_tracker_if_needed` 경로 중복 — 책임 소유권 혼선**
- `stage3_orchestrator.py:1062~1085` 와 `stage2_orchestrator.py:344~358` 가 둘 다 `StateTracker`를 새로 만들고 `full_extract_from_arcs`를 호출한다.
- 주석(`stage3_orchestrator.py:1054~1061`)은 "Stage3가 authoritative lazy-init source"라고 선언하지만, Stage2도 `existing_tracker_arcs == 0` 조건에서 동일 초기화 수행.
- **영향**: Stage2 async 배치가 StateTracker를 비동기로 갱신하는 동안 Stage3가 들어와 재생성할 경우 NPC 레지스트리·financial_registry 덮어쓰기 레이스 발생 가능. `bind_db` 재실행이 WAL 커서에 영향을 줄 수 있음.
- **권장 조치**: state_tracker 초기화를 `SovereignApp._bootstrap_runtime_state` 같은 단일 지점으로 통합하고, Stage2/3는 `assert app.state_tracker is not None` 가드만 유지.

**(P0-3) Stage3 실패 시 `break=True`가 fail_count=1인데도 루프 종료**
- `stage3_orchestrator.py:3349~3354` `_handle_failure`가 항상 `"break": True` 반환.
- 주석(3294행)은 "순차 의존성" 때문이라 설명하지만, 복수 에피소드 배치에서 1개 실패 시 나머지 에피소드 생성이 전부 중단된다.
- **영향**: One-Stop 파이프라인에서 Stage3 중간 실패가 Stage4 진입 자체를 막는다. 복구를 위해선 사용자가 수동으로 실패 에피소드만 재시도해야 함.
- **권장 조치**: 실패 에피소드를 skip-list에 넣고 다음 에피소드로 넘어가는 옵션(`stage3.failure.continue_on_fail: true`)을 추가하거나, 실패 직후 1회 자동 재시도(`adaptive_retry` 훅)를 걸어 단발성 실패를 흡수.

## 4. 개선 권장 (Major Issues) — P1

**(P1-1) 에피소드 경계 탐지 소스가 2중 경로 (blueprint + manuscript)**
- `stage3_orchestrator.py:940~952` — `get_latest_blueprint_number()` vs `get_max_episode_from_manuscripts()` 의 max 값.
- `stage2_orchestrator.py:374~378` 도 유사한 manuscript 스캔.
- **영향**: 원고가 수동 편집되어 에피소드 번호가 뒤엉키면 Blueprint와 manuscript 테이블이 상충하는 "max"를 내놓고, max() 선택으로 Blueprint 없는 ep로 점프해 다음 화에서 `continuity_block`을 유발.
- **권장 조치**: `ProductionHeadResolver` 클래스로 일원화, disagreement 시 경고 + 운영자 확인 필요.

**(P1-2) 에피소드 재시도 한계가 계층마다 따로 정의됨 — 총 재시도 한도 불명**
- Stage3 ThreePhase: `stage3_envelope_builder.py:188` `max_retries=9`.
- Stage4 라운드: `stage4_orchestrator.py:594` `default=5`.
- AdaptiveRetry: `modules/core/adaptive_retry.py:79~86` 에러 타입별 1~3회.
- Constants: `modules/core/constants.py:230` `MAX_RETRY_PER_EPISODE = 10`.
- **영향**: 최악의 경우 1개 에피소드에 Stage3(9) + Stage4(5) + AdaptiveRetry(3) = 수십 회 LLM 호출 누적. 비용 폭주 위험. 정책 일관성이 PolicyDigest 하나에만 있고 adaptive_retry는 별도 상수로 관리됨.
- **권장 조치**: `stage4_policy_digest.py:67` 와 같은 정책 레지스트리를 `modules/core/retry_policy.py`로 승격해 전 경로의 재시도 한도를 단일 source-of-truth로 통합.

**(P1-3) stage4_* 파일 폭증 (LOC 분포 불균형)**
- `stage4_interview_round.py` 8,193 LOC (가장 큰 단일 파일).
- `stage4_context_builder.py` 3,388 LOC, `stage4_orchestrator.py` 2,802 LOC.
- **영향**: Stage4만 27개 파일 48,000+ LOC. 파일 경계가 책임보다는 크기 제약에 따라 나뉘어 있어 변경 영향 분석이 어렵다.
- **권장 조치**: 라운드 로직(`_run_interview_round_step`, `_handle_round_outcome`)을 "state machine per round" 패턴으로 재구성. 현재의 Runtime 클래스(Retry/Reject/PostPass/Postselect)들이 `Stage4InterviewRound` owner 포인터로 엮여 있어 테스트 격리가 어려움.

**(P1-4) `_one_stop_pipeline_frontier_lag` 예외 처리가 str-기반 에러 메시지 트렁케이션**
- `main_a.py:4067~4068`, `4100~4101`, `4120~4121` — 전부 `str(err)[:100]` 로잉 후 일반 `dict`로 `stop_reason` 반환.
- **영향**: 실패 분류가 문자열 기반이라 downstream에서 구조화된 알림·복구가 불가. Traceback은 콘솔에만 출력.
- **권장 조치**: `StageFailureReason(Enum)` 도입, `dataclass` 반환 타입으로 `stage`, `reason_code`, `recoverable`, `trace` 필드 구분.

**(P1-5) Stage간 예외 경계가 bare-ish (`except Exception`) 다발**
- `modules/core/stage*.py` 22개 파일에서 총 419개 `except Exception` (Grep count). 이 중 상당수가 `non-blocking`/`silent pass` 경로.
- **영향**: Stage3 보조 초기화 실패(`_init_state_tracker_if_needed` stage3_orchestrator.py:1082~1085)가 비차단으로 진행되지만, 이후 `state_tracker`가 None인 상태로 downstream에 흘러가 조용한 데이터 누락 유발 가능.
- **권장 조치**: `non_blocking` 실패들을 `logging.warning` + metrics counter 증분으로 통일하고, 연속 3회 실패 시 hard-fail로 전환하는 circuit-breaker 도입.

**(P1-6) Stage0→Stage1 공식 경계가 `_stage_1_volumes` 얇은 델리게이트로만 존재**
- `main_a.py:2855~2857` — Stage1은 `Stage01Helpers.stage_1_volumes()` 단일 메서드.
- Stage1용 orchestrator/context가 없고 `StageZeroManager`가 Bible/Treatment를 통째로 소유 → Volume 전략이 Stage0 내부 서브-아티팩트 수준.
- **영향**: Stage1이 "단계"로 번호가 매겨져 있지만 실제로는 Stage0의 보조 작업. 감사용 용어 정리가 필요.
- **권장 조치**: 이름을 "Stage0b Volumes" 또는 "Pre-Arc Volume Strategy"로 재명명하거나, 또는 정식 Stage1Orchestrator로 승격.

## 5. 개선 검토 (Minor Issues) — P2

**(P2-1) `status_shadow`·`joint_docs`·`arc_end_state` 3중 소스 — 권위 우선순위 추론 복잡**
- `modules/core/cross_stage_authority_packet.py:11~28` 에서 이미 `_OPENING_SOURCE_PRECEDENCE` 등 명시되었지만, `arc_state_utils.py:51~92` 의 fallback 체인과 다름.
- **권장 조치**: `arc_state_utils.compute_terminal_arc_state`를 `cross_stage_authority_packet.resolve_cross_stage_authority_packet`에 위임하도록 리팩터링.

**(P2-2) `stage4_orchestrator._prepare_stage4_session` 부작용이 많음**
- `stage4_orchestrator.py:2701~2746` 내부에서 `_initialize_session_agents`, `_prepare_session_environment`, `_prepare_session_ui` 등 6~8개 부작용 호출.
- **권장 조치**: 순수 빌더(`_build_session_config`)와 부작용 단계(`_bootstrap_session_side_effects`)를 분리.

**(P2-3) 실패 리포트 파일명 규칙이 Stage별로 다름**
- Stage2: `logs/arc_{N}_failure_report.txt` (stage2_orchestrator.py:777).
- Stage3/4: session logger + DB (`save_stage_attempt`).
- **권장 조치**: `logs/failures/{stage}/{id}.json` 구조로 일원화하고 자동 rotation.

**(P2-4) `Stage0/__init__.py`가 1,060 LOC로 module-init 치고 큼**
- `modules/core/stage0/__init__.py:53` `StageZeroManager` 본체가 전부 `__init__.py`에 들어 있음.
- **권장 조치**: `stage0/manager.py`로 분리.

**(P2-5) `_one_stop_pipeline` 와 `_one_stop_pipeline_frontier_lag` 분기 중복**
- main_a.py:2268~2271 메뉴 6/7가 유사하지만 독립 경로.
- **권장 조치**: `OneStopStrategy(name)` 단일 진입점으로 통합, strategy가 "full" vs "frontier_lag" 만 스위치.

## 6. 수치 지표 (Metrics)

| 항목 | 수치 | 출처 |
|------|------|------|
| Stage0 모듈 | 6 files / 5,720 LOC | stage0/ + stage0_*.py |
| Stage2 모듈 | 8 files / 12,472 LOC | stage2_*.py |
| Stage3 모듈 | 3 files / 3,961 LOC | stage3_*.py |
| Stage4 모듈 | 16 files / 27,896 LOC | stage4_*.py |
| Stage4 단일 최대 파일 | 8,193 LOC | stage4_interview_round.py |
| Orchestrator 본체 합계 | 8,161 LOC | stage2/3/4_orchestrator.py |
| 파이프라인 총 LOC | ~49,500 (modules/core/stage*.py) | wc -l |
| Stage 오케스트레이터 내 `except Exception` | 419건 | grep count |
| Stage3 내부 max_retries | 9 | stage3_envelope_builder.py:188 |
| Stage4 기본 max_rounds | 5 | stage4_orchestrator.py:594 |
| Stage4 ensemble workers | 3 (병렬) | blueprint_ensemble.py:438 |
| Stage3 history cache limit | `_STAGE3_HISTORY_CACHE_LIMIT` | stage3_orchestrator.py:989 |
| 공식 지원 장르 | 9 (MVP) | stage0/__init__.py:62~73 |
| 계약 스키마 버전 | `stage0.material.v1`, `cross_stage_authority_packet.v1` | stage0_handoff.py:12, cross_stage_authority_packet.py:9 |

**파이프라인 전이 흐름 (요약 다이어그램)**

```
Stage0 (StageZeroManager)
  ├─ ProjectData/Bible/Treatment 생성
  ├─ build_stage0_bible_contract → MasterBible.plot_roadmap
  └─ check_plot_roadmap_ready() gate
        ▼
Stage1 (_stage_1_volumes, 얇은 델리게이트)
  └─ volumes_strategy 산출 (선택적)
        ▼
Stage2Orchestrator (async, per-Arc 배치)
  ├─ _bootstrap_stage2_arc_pipeline (plot_roadmap 재검증)
  ├─ _run_stage2_batch_enrichment (3 semaphore)
  ├─ _handle_stage2_finalize_transition → verdict ∈ {PASS, RETRY, REJECT}
  ├─ build_cross_stage_authority_packet (stage2_finalizer 내)
  └─ save_anchor("arcs", ...) 및 constraint_db 갱신
        ▼
Stage3Orchestrator (sync, per-Episode 순차)
  ├─ _init_state_tracker/world_state/fact_ledger_if_needed (lazy)
  ├─ production_head = max(existing_bp, existing_ms)
  ├─ _process_single_episode (continuity precheck)
  ├─ ThreePhaseBlueprintAgent.generate(max_retries=9, ensemble=3)
  └─ save_episode_blueprint / save_stage_attempt / save_cost_record
        ▼
Stage4Orchestrator (sync, per-Episode + per-Round)
  ├─ _prepare_stage4_session (style_guide, agents, 등)
  ├─ _run_interview_loop → _run_episode_loop_iteration
  ├─ interview_round.run (max 5회, Chief Writer 3-worker ensemble)
  ├─ V75-D inplace patch / V75-B blueprint regen escalation
  ├─ PASS_WITH_FIX / REJECT retry lanes (stage4_retry_runtime)
  └─ save_manuscript / save_episode_quality_label
```

## 7. 성숙도 근거 (Maturity Evidence)

| 차원 | 수준 | 근거 |
|------|------|------|
| **계약 명세** | Pre-production | `STAGE0_CONTRACT_SCHEMA`, `CROSS_STAGE_AUTHORITY_PACKET_VERSION` 등 semver-like 계약 + field_authority 명시 |
| **상태 관리** | MVP→Pre-production 전환기 | StateTracker/WorldState/FactLedger 삼두체제 lazy-init 중복 (P0-2) |
| **복구 전략** | MVP+ | 4층 retry(3 ensemble → 9 blueprint → 5 round → 3 adaptive)는 구성되었으나 통합 정책 부재 (P1-2) |
| **무인 운영** | POC→MVP | Stage2 실패 시 `input()` 블로킹 (P0-1) — 완전 무인 실행 미보장 |
| **관측성** | Pre-production | observability_flags, attempt_key, cost_record 등 구조화 로그 축적 경로 존재 |
| **테스트 커버리지** | Pre-production (MEMORY 기준 3,170 tests passing) | T05 트랙 결과 참조 |
| **성능/비용** | MVP+ | Context Caching 6 사이트 적용, 그러나 4층 retry 누적 시 비용 천장 없음 (P1-2) |
| **문서/통치** | Pre-production | AGENTS.md + docs/implementation/ SSOT + VSX 계약 문서 풍부 |

**종합**: Stage 파이프라인은 "production-level contracts"와 "MVP-level automation"이 공존하는 Pre-production 단계. 계약·관측 측면은 프로덕션에 근접하지만, 무인 운영과 재시도 예산 통제가 실제 프로덕션 투입의 blocker.

## 8. 권장 로드맵 (Recommendations)

**Tier 1 (production blocker — 2~4주 내)**
1. P0-1: Stage2 실패 경로 non-interactive policy 도입 — 무인 배치 운영 가능케 함.
2. P0-2: StateTracker 초기화 단일화 — race condition 제거.
3. P0-3: Stage3 부분 실패 시 skip/continue 옵션 — One-Stop 파이프라인 탄력성 회복.

**Tier 2 (기술 부채 정리 — 1~2분기)**
4. P1-2: 전역 `RetryPolicy` 도입 (`retry_policy.py`) — 재시도 예산 천장 + 비용 추적 통합.
5. P1-3: `stage4_interview_round.py` 8K LOC 분해 — state machine 리팩터링.
6. P1-1: `ProductionHeadResolver` — Blueprint/Manuscript 드리프트 감지.
7. P1-4: `StageFailureReason` enum + dataclass — 구조화된 에러 모델.

**Tier 3 (아키텍처 정비 — 2~4분기)**
8. P1-5: `except Exception` 경로에 circuit-breaker 도입.
9. P1-6: Stage1 공식 승격 또는 재명명.
10. P2-2: `_prepare_stage4_session` 순수/부작용 분리.
11. P2-5: One-Stop strategy 통합.
12. P2-1: `arc_state_utils`를 cross_stage_authority_packet에 위임.

**Tier 4 (관측성 강화 — 지속)**
13. P2-3: 실패 리포트 포맷 일원화 (`logs/failures/{stage}/{id}.json`).
14. PolicyDigest (stage4_policy_digest.py:67)를 Stage0/2/3에도 확장.
15. 에피소드별 `total_retry_count` 메트릭 + 비용 대시보드.
