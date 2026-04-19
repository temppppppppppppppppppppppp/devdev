# T01: main_a.py 모놀리스 분석

Surveyor: Claude Code (Terminal 1)
Date: 2026-04-19
Scope: `main_a.py` 단일 파일의 책임 분포, 결합도, 분리 후보, 성숙도 판정

## 1. Executive Summary

- **성숙도 판정: Pre-production**
- main_a.py는 219KB / **4,836 lines** (SURVEY-ORDER.md의 "~220,000 lines"는 바이트 수 혼동 — 실측 4,836줄). 단일 God-class `SovereignApp`이 **187개 메서드**와 약 40개 옵션 모듈 슬롯을 보유하나, **이미 Stage2/3/4 오케스트레이터·4개 서비스·BootstrapRuntime·Stage01Helpers·PromptBuilder·FeedbackSystem**으로의 대규모 분리가 진행 중이며 30개 `[COMPAT] thin delegate` 잔재가 그 흔적이다. 명확한 P0 블로커는 없으나, 프론티어-랙 / 원-스톱 / 셧다운 지속화 / 내러티브 요약 / 장르 선택 UI — 5개 기능 군집이 여전히 모노리스 내부에 남아 있어 완전한 Production 수준에는 도달하지 못했다.

## 2. 강점 (Strengths)

- **체계적인 경계 분리 이행 중**: `[V64.P3]`, `[Phase 4B-1]`, `[Phase 4C-1a]`, `[Phase 4C-1b]` 등 페이즈 마커로 추출 이력이 추적된다 (main_a.py:147-158, 388-393).
  - Stage2/3/4 Orchestrator 3개 (main_a.py:154-156, 391-393)
  - AuditService / UIService / StateService / ProjectService 4개 (main_a.py:147-150, 418-453)
  - SovereignBootstrapRuntime, Stage01Helpers, PromptBuilder, FeedbackSystem (main_a.py:152, 388-395)
- **부트 실패 관측성**: `_persist_boot_failure_traceback` 으로 크래시 전에 traceback을 파일로 내린다 (main_a.py:27-45, 4826-4836).
- **지연 로딩**: `_lazy_load_stage0`, `_lazy_load_agents`, `_lazy_load_v50_modules` 로 부팅 비용 제어 (main_a.py:189-345).
- **에러 핸들링 위생**: `except:` (bare) 0건. `except Exception` 67건은 모두 `as e` 또는 명시적 네임드 변수로 캡처됨 (main_a.py 전체 grep).
- **플랫폼 부트스트랩 모듈화**: Windows UTF-8 stdio, asyncio 정책을 부팅 첫 단계에서 명시적으로 처리 (main_a.py:47-178).
- **셧다운 훅 일원화**: `_handle_main_process_error` → `_shutdown_app` 경로가 명확히 연결되어 있고 `atexit.register(self._flush_audit_buffer)` 로 종료 플러시 보장 (main_a.py:2282-2303, 426).
- **동기/비동기 안전 커밋 분리**: `_safe_commit` / `_safe_commit_async` 분리 구현으로 트랜잭션 오남용 회피 (main_a.py:507-594).

## 3. 개선 필수 (Critical Issues) — P0

없음. 해당 파일은 명백한 프로덕션 블로커를 포함하지 않는다. (SQL/쉘 인젝션 표면 없음, 인증/인가 경로 없음, 멀티스레드 임계영역 부재, 글로벌 상태 5건은 모두 부팅 가드 플래그로 읽기 전용 패턴.)

## 4. 개선 권장 (Major Issues) — P1

### P1-1 — God-class 잔존: 187 메서드 / 약 40 옵션 슬롯

- **파일:라인**: `main_a.py:347` (클래스 선언), `main_a.py:455-492` (`_init_optional_module_slots`)
- **설명**: `_init_optional_module_slots` 가 `self.pacing_analyzer = None` 부터 `self.preset_registry = None` 까지 **30+ 개의 `None` 슬롯**을 한 번에 선언한다. 이는 "속성이 존재할 수도/없을 수도" 라는 모호성을 코드 전체로 전파시키는 고전적 God-object 안티패턴이다. 런타임에 `hasattr(self, ...)` 체크가 필요해지고, 실제로 `main_a.py:444-448` 의 `getattr(self, "...", None)` 패턴이 다수 등장한다.
- **영향도**: 클래스 불변식이 없음 → 테스트 이중, 초기화 순서 버그 리스크, IDE/타입체커 지원 저하.
- **권장 조치**: 선택 모듈 슬롯을 `OptionalModuleRegistry` 데이터클래스로 캡슐화하고 `SovereignApp.modules: OptionalModuleRegistry` 필드 하나로 치환. 단계적 이관 가능 (`@property` 호환 레이어 경유).

### P1-2 — 셧다운 지속화 12개 메서드 군집 (~450 라인)

- **파일:라인**: `main_a.py:2321-2769` (`_persist_shutdown_metrics` → `_persist_shutdown_project_state`)
- **설명**: 12개의 `_persist_shutdown_*` 메서드가 한 클래스에 몰려 있다. 각각 독립된 책임(cost scope, advisory, pass-rate, director-bias, quality-drift, trackers, failure-learner, character-voice, foreshadow, emotion, project-state)으로 `ShutdownService.persist_all(app)` 수준의 조율자를 추출하기 좋은 후보.
- **영향도**: 셧다운 경로 회귀 시 디버깅이 어렵다. `_close_shutdown_resources` (2770) 와의 순서 의존이 암묵적.
- **권장 조치**: `modules/core/services/shutdown_service.py` 로 추출, 현재 `self._audit_service` 등과 동일 패턴. 각 `_persist_shutdown_*` 는 서비스 메서드로 이관 후 main_a.py 에는 `self._shutdown_service.run()` 만 남긴다.

### P1-3 — `[COMPAT] thin delegate` 30건 — 제거 대기 중인 잔재

- **파일:라인**: main_a.py 전역 30건, 대표 사례 `main_a.py:2999-3022` (Stage2 계열 5건), `main_a.py:3047-3099` (PromptBuilder/Helpers 계열).
- **설명**: 이미 오케스트레이터/헬퍼로 이관된 메서드가 하위 호환용으로 main_a.py 에 남아 있다. 각 메서드 상단에 `[COMPAT] thin delegate — authority is Stage2Orchestrator` 주석이 명시되어 있으나, 호출부가 아직 이관되지 않아 존재.
- **영향도**: 파일 라인 수 팽창, "이 메서드의 소유자가 어디인가" 혼란, 이중 진실(양쪽 어디를 수정해야 하는가) 리스크.
- **권장 조치**: 각 COMPAT 메서드의 호출부를 grep → 오케스트레이터 직접 호출로 치환 → COMPAT shim 일괄 삭제. MEMORY.md의 "아직 쓰이는 호환 shim이 있다"는 명시 없음이므로 즉시 정리 가능.

### P1-4 — Frontier-Lag 파이프라인 6개 메서드 (~400 라인)

- **파일:라인**: `main_a.py:3978-4501` (`_resolve_one_stop_frontier_lag_plan` ~ `_one_stop_pipeline_frontier_lag`)
- **설명**: 프론티어 랙 보정 파이프라인 전체가 main_a.py 에 미추출. 최대 단일 메서드 `_one_stop_pipeline_frontier_lag` 132 라인. 해당 도메인은 stage3/4 와 상호작용이 많아 기존 Stage3Orchestrator / Stage4Orchestrator 와 동일 레이어 `FrontierLagOrchestrator` 로 분리가 적합.
- **영향도**: main_a.py 의 약 **8.3%** 가 이 기능 군집. 변경 시 모노리스 전체 리스크.
- **권장 조치**: `modules/core/frontier_lag_orchestrator.py` 생성. `ensure_arc_ready`, `run_stage3_sync`, `run_stage4_sync`, `run_arc_step`, `prepare_batch_request`, `finalize_result` 를 그대로 이관.

### P1-5 — One-Stop 파이프라인 5개 메서드 (~330 라인)

- **파일:라인**: `main_a.py:4565-4836` (`_prepare_one_stop_batch_request` ~ `_one_stop_pipeline`)
- **설명**: One-Stop 자동 실행 파이프라인. `_one_stop_pipeline` 99 라인 + `_run_one_stop_arc_step` 98 라인 + 주변 3개. Frontier-Lag 와 유사한 구조이며, 두 파이프라인이 `_prepare_*_batch_request` / `_finalize_*_result` 시그니처를 거의 평행 구조로 가진다.
- **영향도**: Frontier-Lag 와 중복 패턴. 공통 추상화 `PipelineOrchestratorBase` 가치 높음.
- **권장 조치**: Frontier-Lag 추출과 함께 `OneStopOrchestrator` 분리. 공통 `prepare_batch_request / finalize_result` 시그니처는 P2-4 참조.

### P1-6 — 내러티브 요약 생성 5개 메서드 (~210 라인)

- **파일:라인**: `main_a.py:3648-3856`
- **설명**: `_generate_narrative_summary`, `_resolve_narrative_summary_batch`, `_build_narrative_summary_combined_text`, `_build_narrative_summary_prompt`, `_persist_narrative_summary_anchor`, `_load_narrative_summaries` — LLM 호출/프롬프트 빌드/저장/로드 가 한 클래스에 혼재.
- **영향도**: SRP 위반. 내러티브 요약은 StateService 또는 별도 `NarrativeSummaryService` 책임.
- **권장 조치**: `modules/core/services/narrative_summary_service.py` 신규. 캐시 `self._narrative_summaries_cache` (main_a.py:417) 도 서비스로 이관.

### P1-7 — 장르 선택 UI/카탈로그 161 라인

- **파일:라인**: `main_a.py:3235-3395` (`_build_genre_selection_catalog`)
- **설명**: 9개 장르의 메타데이터·설명·색상·기본값을 **하드코딩된 거대한 dict 리터럴** 로 선언. 장르 추가 시 MEMORY.md의 16항목 체크리스트와 함께 이 파일도 수정해야 하는 2차 결합 지점.
- **영향도**: 장르별 설정이 `config/` 밖의 코드 상수로 흩어짐. T08 (Config/Data) 트랙의 "외부화된 설정 vs 하드코딩" 질문과 직결.
- **권장 조치**: 카탈로그를 `config/genres/catalog.yaml` 로 외부화, `_build_genre_selection_catalog` 은 로더로 축소.

## 5. 개선 검토 (Minor Issues) — P2

### P2-1 — `SovereignApp._foo(self, ...)` 정적 호출 스타일

- **파일:라인**: `main_a.py:1402-1408`
- **설명**: `SovereignApp._bind_selected_project(self, project_name)`, `SovereignApp._restore_boot_runtime_state(self)`, `SovereignApp._ensure_project_genre_alignment(self)`, `SovereignApp._initialize_project_genre_runtime(self)`, `SovereignApp._initialize_project_runtime_support(self, ...)` — 인스턴스 메서드를 클래스 바인딩 형태로 호출. 의도 불분명 (아마 mypy 유추 회피 또는 오타).
- **권장 조치**: `self._bind_selected_project(project_name)` 등 일반적 스타일로 정규화.

### P2-2 — Stage `_extended` / `_volumes` 1~3줄 래퍼

- **파일:라인**: `main_a.py:2843-2857` (`_phase_0_recovery`, `_stage_0_extended`, `_extend_blocks`, `_stage_1_volumes`)
- **설명**: 이름만 남고 본문이 사실상 위임 또는 비어있는 shell. 정리하거나 오케스트레이터로 흡수.
- **권장 조치**: 본문을 확인 후 inline 혹은 thin-delegate 일괄 삭제 (P1-3 과 함께).

### P2-3 — 오케스트레이터 context 재바인딩 반복 패턴

- **파일:라인**: `main_a.py:2971, 3231, 3943, 4065, 4158` — `self._stage{N}_orch.ctx = Stage{N}Context.from_app(self)` 5회 반복.
- **권장 조치**: `_bind_stage_context(self, orch, ctx_cls)` 헬퍼 1개로 공통화. 또는 오케스트레이터가 자신의 `bind(app)` 메서드를 제공.

### P2-4 — Frontier-Lag / One-Stop 공통 시그니처 미추상화

- **파일:라인**: `main_a.py:4321` (`_prepare_frontier_lag_batch_request`) / `main_a.py:4565` (`_prepare_one_stop_batch_request`), 각 `_finalize_*_result` 도 평행.
- **권장 조치**: P1-4/P1-5 추출 시 `PipelineOrchestratorBase.prepare_batch_request() / finalize_result()` 를 ABC 로 정의.

### P2-5 — 스테일 리뷰 주석

- **파일:라인**: `main_a.py:2305-2306` — `# SovereignApp 클래스 내부에 추가할 메서드 / # [수정] main_a.py / SovereignApp 클래스 내부 메서드` 는 리뷰 과정 잔존 메모.
- **권장 조치**: 삭제.

### P2-6 — `_simplify_prompt_for_retry` / `_build_strong_kind_feedback` / `_build_focused_context` 등 "한 줄 바디 + feedback_system 위임" 메서드

- **파일:라인**: `main_a.py:887-990` 구간 다수.
- **설명**: 대부분이 `return self._feedback_system.xxx(...)` 한 줄. P1-3 의 COMPAT 정리와 함께 호출부를 `self._feedback_system.xxx()` 로 이관 후 삭제 가능.

## 6. 수치 지표 (Metrics)

| 항목 | 측정값 |
|------|--------|
| 총 라인 수 | 4,836 |
| 파일 크기 | 219,989 bytes (~220 KB) |
| 모듈 레벨 정의 (class + def) | 10 (`BootstrapStatus` 1, 함수 9) |
| `SovereignApp` 메서드 수 | 187 |
| 임포트 라인 | 142 (modules/* 103) |
| `global` 선언 | 5 (모두 부팅 플래그) |
| `except Exception` | 67 |
| `except:` (bare) | 0 |
| `[COMPAT] thin delegate` 주석 | 30 |
| `self._stage[2-4]_orch` 참조 | 22 |
| `_persist_shutdown_*` 메서드 군집 | 12 (~450 라인) |
| Frontier-Lag 메서드 군집 | 6 (~400 라인, 3978-4501) |
| One-Stop 메서드 군집 | 5 (~330 라인, 4565-4836) |
| 내러티브 요약 메서드 군집 | 5 (~210 라인, 3648-3856) |
| 옵션 모듈 `None` 슬롯 (_init_optional_module_slots) | ~30 |
| 최장 단일 메서드 | `_build_genre_selection_catalog` 161 라인 (3235) |
| Top-level guard 패턴 | `if __name__ == "__main__":` + 보호된 traceback persist (4826-4836) |

## 7. 성숙도 근거 (Maturity Evidence)

**Pre-production 판정 근거**:

- **Production을 막는 요인**:
  - 187 메서드 God-class 구조 잔존 → 변경 영향 반경이 파일 전체
  - 5개 기능 군집(Frontier-Lag, One-Stop, Shutdown 지속화, 내러티브 요약, 장르 선택) 미추출
  - ~30 개 옵션 모듈 `None` 슬롯 → 런타임 불변식 부재
  - 30개 `[COMPAT] thin delegate` 잔재 → 이중 진실 리스크

- **MVP 이상임을 보이는 근거**:
  - 0건의 bare `except:` (에러 핸들링 위생 확보)
  - Stage2/3/4 Orchestrator, 4개 Service, BootstrapRuntime 이미 추출 완료 — 분리 방향성 명확
  - 부트 실패 traceback persistence 및 atexit flush 루틴 확보
  - 지연 로딩으로 부팅 비용 제어
  - Windows UTF-8/asyncio 플랫폼 부트스트랩 모듈화
  - 세션 로거 / 감사 서비스 / 메트릭 수집기 일관 연결

- **Production이 되려면 필요한 것**:
  - P1-2~P1-7 5개 추출 완료
  - P1-1 옵션 모듈 레지스트리 캡슐화
  - P1-3 COMPAT shim 일괄 제거

## 8. 권장 로드맵 (Recommendations)

**단기 (1–2 스프린트, ~150줄 감소 예상)**:
1. P1-3 — `[COMPAT] thin delegate` 30건 호출부 이관 후 일괄 삭제
2. P2-1, P2-3, P2-5 — 호출 스타일 정규화 및 죽은 주석/래퍼 제거
3. P2-6 — feedback_system 1-라인 위임 통합

**중기 (2–4 스프린트, ~1,000줄 감소 예상)**:
4. P1-2 `ShutdownService` 추출 (~450줄)
5. P1-6 `NarrativeSummaryService` 추출 (~210줄)
6. P1-7 장르 카탈로그 YAML 외부화 (~160줄 + T08 연계)

**장기 (병렬 4–6 스프린트)**:
7. P1-4 `FrontierLagOrchestrator` 추출 (~400줄)
8. P1-5 `OneStopOrchestrator` 추출 + P2-4 `PipelineOrchestratorBase` 공통화 (~330줄)
9. P1-1 `OptionalModuleRegistry` 데이터클래스 도입 — 단계적 이관

**최종 목표 상태**: main_a.py ≤ 1,500 라인, `SovereignApp` 는 부팅·서비스 와이어링·메인 루프 디스패처 세 책임만 보유. 모든 기능 로직은 orchestrator 또는 service 계층 소유.
