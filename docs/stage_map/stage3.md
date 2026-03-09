# Stage 3 Map

## Scope
- Define what Stage 3 is responsible for.
  - Arc 기반 에피소드별 Blueprint 생성/검증/저장.
  - 파이프라인: Constraint 수집 -> Ensemble 3후보 생성 -> Director 비교선택+판정.
  - 순차 의존성 보장: 이전 화 Blueprint 없으면 다음 화 생성 중단.
- Out of scope:
  - 최종 원고 생성(Stage 4 책임).
  - Arc 설계 자체 생성/수정(Stage 2 책임).

## Why
- 왜 3개 후보 병렬 생성? 전략 다양성(액션/감정/대화)을 확보하고 Director가 상대 비교로 최적안을 고르기 위해서다.
- 왜 in-place patch? score >= 60 구간은 전면 재생성보다 단일 수정이 빠르고 비용이 낮기 때문이다.
- 왜 `quality_gate_score=90`? Director 비교 프롬프트의 90점 미만 REJECT 기준과 일치시켜 주권주의 역전을 막기 위해서다.
- 왜 PASS_WITH_FIX? (TF-27~34) Director가 "소수 수정 후 합격" 판정 시 fix_scope 기반 inplace/partial/full 라우팅. QualityGate는 PASS_WITH_FIX를 bypass하여 Director 주권 존중.

## Entry Points
- Primary:
  - `Stage3Orchestrator.stage_3_batch_blueprinting()` (`modules/core/stage3_orchestrator.py`)
- Secondary:
  - `ThreePhaseBlueprintGenerator.generate()` (`modules/domain/agents/three_phase_blueprint_generator.py`)
  - `UnifiedBlueprintValidator.validate()` (`modules/domain/agents/unified_blueprint_validator.py`)
  - `DirectorEnsembleSelector.compare_and_select_blueprint()` (`modules/domain/agents/director_ensemble.py`)

## Inputs
- Required:
  - `current_project.arcs` (없으면 즉시 종료).
  - 현재 화에 대응되는 `arc_data` (`ep_start`, `ep_end`, `tactical_doc` 등).
  - Director 에이전트 (`ctx.agents["director"]`) 및 `three_phase_bp` 에이전트.
- Optional:
  - `prev_blueprint`, `prev_blueprints[-30:]` (연속성/컨텍스트).
  - Entity Registry (`state_extractor` 경유 추출).
  - `state_tracker`, `world_state`, `fact_ledger` (lazy init).
  - VecMemory 기반 semantic context (`smart_retrieval.stage3_enabled` 시).
  - 이전 원고 전문(최근 30화), `protagonist_config`, `prev_hud`.

## Outputs
- Files:
  - `projects/{project}/plans/blueprints/blueprint_XXXX.txt` (human-readable 백업, primary source 아님).
- DB updates:
  - `blueprints` 테이블: `save_blueprint(ep_num, data)`로 저장.
  - 실패 기록: `cost_log`에 `stage3_reject` 이벤트 저장.
  - 품질 이벤트: `audit_event`/`quality_dashboard` 기록.
- In-memory state:
  - `prev_blueprints` 최근 30개 유지.
  - Arc 단위 Entity Registry 캐시 (`_entity_cache_arc_idx`, `_cached_entity_registry`).
  - 생성 결과 메타 `_stage3_meta`(verdict/score/quality_risk) 주입.

## Dependencies
- Internal modules:
  - `modules/core/stage3_orchestrator.py`
  - `modules/domain/agents/three_phase_blueprint_generator.py`
  - `modules/domain/agents/blueprint_ensemble.py`
  - `modules/domain/agents/unified_blueprint_validator.py`
  - `modules/domain/agents/director_ensemble.py`
  - `modules/models/blueprint.py` (Pydantic 검증)
  - `modules/core/project_manager.py` / `db_manager.py` (저장)
- External services/models:
  - BaseAgent `ask()` 기반 Gemini 호출(Ensemble 생성/Director 비교 선택).
  - optional Slack notifier (`modules.utils.notifier`).

## State and Cache
- Persistent state:
  - `blueprints` 테이블(JSON).
  - `cost_log`(실패/품질 리스크 메타).
  - `anchors`의 `world_state`, `fact_ledger`는 Stage 3에서 초기화/로드만 수행 가능.
- Runtime cache:
  - Arc 단위 Entity Registry 캐시(Arc 변경 전까지 재사용).
  - ThreePhase 내부 `constraint_block` 캐시(retry 반복 시 재사용).
  - Ensemble context cache (`_get_or_create_context_cache`, cache_type=`blueprint_ensemble`).
- Invalidation rules:
  - Arc 인덱스 변경 시 Entity Registry 캐시 재구축.
  - 실패 시 동일 에피소드 재시도에서 피드백만 갱신(초기 피드백 기준 재구성).
  - `prev_blueprints`는 30개 초과 시 앞부분 절삭.

## Failure and Recovery
- Common failure patterns:
  - 현재 화 Arc 컨텍스트 미검출/`ep_start` 누락.
  - 직전 화 Blueprint 부재(연속성 차단).
  - Ensemble 후보 생성 전부 실패 또는 Director REJECT 반복.
  - DB commit 실패/JSON 파싱 실패.
- Recovery flow:
  - Stage3Orchestrator는 실패 화에서 즉시 루프 중단(`break=True`), 후속 화 skip 금지.
  - ThreePhase retry 루프: `for retry in range(max_retries+1)`; Stage3 호출값 `max_retries=9` -> 최대 10회 시도.
  - 각 시도에서 후보 3개 생성 -> Director 비교/판정.
  - REJECT 피드백(점수/이슈/사유) 누적 후 다음 시도에 반영.
  - **PASS_WITH_FIX** (TF-27~34): fix_scope="inplace"면 LLM 1회 수정 + `validator.validate(all_candidates=None)` 재심사(최대 3회). partial/full이면 REJECT → retry 경로 위임.
- Fallback behavior:
  - in-place patch: 직전 REJECT 점수 `>= inplace_below(60)`일 때 단일 LLM 1회 수정.
  - `< 60`이면 전면 재생성, `< rewrite_below(50)`면 `_previous_best` 폐기.
  - 모든 재시도 실패 후에도 last score `>= rewrite_below(50)`이면 `PASS_WITH_WARNING` 허용.
  - Director 부재 시 `UnifiedBlueprintValidator`는 Python 경고만 남기고 PASS 처리.
  - **CentralSchemaBuilder** (TF-45): 장르별 스키마를 동적 생성하여 비무협 장르에 무협 전용 필드(내공, 무공 등)가 유입되는 프롬프트 오염을 근절.

## Manual Intervention Points
- User prompts:
  - 목표 생성 화수 입력 (`몇 화까지 설계도 생성?`).
- Approvals:
  - 코드상 별도 승인 단계 없음(Director 판정이 자동 게이트).
- Operator checks:
  - 시작 전 Arc 범위/기존 Blueprint, 원고 head 확인 로그.
  - 실패 시 `blueprint_fail` audit event와 `cost_log` 확인.

## Metrics
- Throughput:
  - 배치 결과 `success_count` / `fail_count` 출력.
  - `ThreePhaseBlueprintGenerator.get_stats()`의 `pass_rate` 출력.
- Error rate:
  - `phase3_reject` 카운트 및 `blueprint_fail` 이벤트로 추적.
- Latency:
  - Ensemble 내부 병렬 타이머 로그 (`PerfTimer:BlueprintEnsemble`).
  - 후보별 timeout: 전체 300s, 개별 240s.

## Tests
- Unit:
  - `tests/test_blueprint_patch_mode.py`
  - `tests/test_stage3_orchestrator.py`
- Integration:
  - `tests/e2e/test_l3_stage3_smoke.py`
  - `tests/stage3_isolated_test/test_stage3_arc3.py`
  - `tests/stage3_isolated_test/test_stage3_arc3_v2.py`
  - `tests/stage3_isolated_test/test_stage3_production.py`
- Regression:
  - `tests/chaos/test_stage3_metrics.py`
  - `tests/chaos/test_blueprint_none.py`

## Open Risks
- Risk 1:
  - Stage3 전용 `vector_max_results` 설정 키가 없고 Stage4 키(`context.vector_max_results_s4`)를 공유해 튜닝 결합도가 높음.
- Risk 2:
  - Director가 없으면 PASS로 진행되는 비차단 경로가 있어 운영 설정 오류 시 품질 게이트가 약화될 수 있음.

## Last Verified
- Date: 2026-03-10
- Commit: `3a00c12`
- Code Sync (Yes/No): Yes
- Verified By: Codex

