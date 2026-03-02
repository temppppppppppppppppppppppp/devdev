# Stage 4 Map

## Scope
- Blueprint를 입력으로 실제 원고를 생성하고, Director 심사/재시도 루프를 통해 회차 확정본을 저장한다.
- PASS 시 후처리로 Episode Bible, state_logs, world_state/fact_ledger, 벡터 메모리, 품질/비용 메트릭을 갱신한다.
- Out of scope: Arc 생성(Stage2), Blueprint 생성(Stage3), Stage 초기화/롤백 메뉴 처리(runbook/main_a).

## Why
- 왜 Blueprint를 DB에서만 읽나? `blueprints` 테이블을 SSOT로 고정해야 재시작/롤백/후처리 경로가 일관되기 때문이다.
- 왜 Chief Writer와 Director를 분리하나? 생성 책임(Writer)과 판정 책임(Director)을 분리해 품질 게이트의 독립성을 유지하기 위해서다.
- 왜 PASS 후에도 연속성/히스토리 후검증을 한 번 더 하나? 후보 선택 직후 충돌을 늦게라도 잡아 REJECT로 강등할 안전장치가 필요하기 때문이다.
- 왜 advisory 체인을 Director 앞에 배치하나? (LM-A~F) TruthGate → NpcDrift → NumericDrift → Flashback → InfoParadox → RelationshipDrift 순으로 advisory를 수집하여 Director에게 근거를 제공하되, 최종 판정은 Director가 내리기 때문이다.
- 왜 PASS_WITH_FIX에서 QualityGate를 bypass하나? (TF-46) Director가 "수정 후 합격" 의도를 표현했는데 QualityGate가 이를 REJECT로 뒤집으면 Director 주권이 침해되기 때문이다.
- 왜 state_updates에서 Director 보정값을 CW보다 우선하나? Director 프롬프트가 CW state_updates를 "기반으로 보정"하여 superset(투자 장르 capital 등)을 반환하기 때문이다.

## Entry Points
- Primary: `Stage4Orchestrator.stage_4_v2_chief_writer(limit_mode=False)` (`modules/core/stage4_orchestrator.py`)
- Secondary:
  - `Stage4Orchestrator._prepare_stage4_session()`
  - `Stage4Orchestrator._run_interview_loop()`
  - `Stage4InterviewRound.run()` (`modules/core/stage4_interview_round.py`)
  - `Stage4PostProcessor.process_pass_result()` (`modules/core/stage4_post_processor.py`)

## Inputs
- Required:
  - `current_project.master_bible`, `current_project.arcs` (없으면 Stage4 세션 시작 중단)
  - `current_project.get_blueprint(next_ep)`로 로드한 회차 Blueprint (DB `blueprints` 테이블 기반)
  - Arc 매핑 정보(`ep_start/ep_end`)와 이전 원고(`db.get_manuscript(next_ep-1)`)
- Optional:
  - Stage0 style guide anchor(`style_guide`) 또는 사용자 스타일 선택 입력
  - 벡터 메모리/WorldState/FactLedger/ReferenceAnchor/품질 대시보드 모듈
  - `limit_mode=True`일 때 target episode 입력

## Outputs
- Files:
  - `projects/{project_name}/drafts/ep_XXXX.txt` (확정 원고 텍스트)
- DB updates:
  - `manuscripts`: `save_manuscript()`
  - `martial_tracker`: `update_martial_tracker()` (state_updates 있을 때)
  - `director_selections`: 매 면담 라운드 선택/점수 기록
  - `episode_bibles`: `save_episode_bible()`
  - `state_logs`: `save_state_log_with_summary()`
  - `anchors`: `chain_link_{ep}`, `world_state`, `fact_ledger`
  - `episode_sentence_hashes`: 크로스 에피소드 반복 감지 해시 저장
  - `episode_satisfaction_tags`: 만족도 태그 저장
  - `episode_pacing`: 호흡 분석 저장
  - `cost_log`: REJECT/PASS 비용 스냅샷 저장
  - VecMemory 경유: `episode_meta`, `vec_episodes`, `sync_status`, `episode_fts`
- In-memory state:
  - 라운드별 `previous_attempt`, `director_feedback`, `time_warnings`
  - HUD 승인 업데이트(`director.on_approve_workflow` 결과 반영)
  - `world_state`/`fact_ledger` 내부 상태 dict 갱신 후 저장

## Dependencies
- Internal modules:
  - `Stage4ContextBuilder`, `Stage4InterviewRound`, `Stage4PostProcessor`
  - `ChiefWriter`, `ManuscriptValidator`, `ConsistencyValidator`, `BlockingValidator`, `ContinuityValidator`
  - Director 에이전트의 `select_and_judge_ensemble()`, `check_manuscript_continuity_with_cache()`, `check_manuscript_history_conflicts()`
  - `DirectorContinuityValidator` (`modules/domain/agents/director_continuity.py`)의 캐시 기반 연속성 검사 구현
  - **Advisory 체인** (LM-A~F, Director 앞단 `_director_mc_parts`에 주입):
    - `TruthGate` (LM-A): 사망NPC/아이템/장소/스킬/카르마/NPC역할/세계법칙 7개 검사
    - `NpcDriftAdvisor` (LM-B): 원고 vs 스냅샷 NPC 속성 표류 LLM advisory
    - `NumericDriftAdvisor` (LM-C): FactLedger 수치 누적 표류 (5화 단위)
    - `FlashbackVerifier` (LM-E): 회상/플래시백 오염 감지 (14개 마커 + VecMemory)
    - `InfoParadoxChecker` (LM-F): 1인칭 시점 정보 역설 (1인칭 전용)
    - `RelationshipDriftAdvisor` (LM-D): NPC 관계도 장기 표류
  - `CentralSchemaBuilder` (TF-45): 장르별 프롬프트 스키마 동적 생성 (비무협 오염 방지)
- External services/models:
  - LLM 호출 (`self.ctx.sys.api_client`, Director/Writer `ask()` 계열)
  - VecMemory 임베딩/검색 경로(환경에 따라 `google genai` + `sqlite-vec`)
  - Hybrid Retrieval (FTS5+RRF): 벡터 검색 + 전문 검색 결합

## State and Cache
- Persistent state:
  - 원고/심사/후처리 산출물은 `project_data.db` 테이블 및 anchors에 누적 저장
- Runtime cache:
  - `Stage4Orchestrator`의 lazy submodule 캐시(`post_processor/context_builder/interview_round`)
  - `ReferenceAnchor` 인스턴스 루프 외부 1회 생성
  - `ChiefWriter` 원고 프리페치 캐시(`_manuscript_cache`), 컨텍스트 캐시(TTL 600초)
  - `DirectorContinuityValidator`의 blueprint/manuscript 캐시(`_cached_*_ep`)
- Invalidation rules:
  - 에피소드 시작마다 `time_warnings` 리셋
  - Director continuity 캐시는 `ep_num` 변경 시 재생성
  - Writer 캐시는 `invalidate_manuscript_cache()`로 명시 무효화 가능(롤백 시 사용)

## Failure and Recovery
- Common failure patterns:
  - Blueprint/Arc 누락 시 집필 루프 중단
  - 후보 원고 전부 실패 시 `EMPTY` 반환 후 다음 라운드 재시도
  - Director PASS라도 `score < scoring.quality_gate_score(90)`이면 REJECT 강등 (**단, PASS_WITH_FIX는 QualityGate bypass** — TF-46)
  - DB 저장 실패 시 트랜잭션 롤백 후 해당 회차 집필 중단
- Recovery flow:
  - 라운드 수는 `retry.director_max_attempts`(기본 5)까지 반복
  - REJECT 시 `previous_attempt` 기반 재생성/패치 경로로 다음 라운드 진행
  - Manager 비동기 정산 실패 시 동기 재시도 폴백
  - **PASS_WITH_FIX 3-tier 라우팅** (TF-33):
    - **inplace**: `_previous_best`가 있고 (fix_scope=="inplace" 또는 score >= INPLACE 임계값) → `chief_writer.inplace_patch()` → Director `audit_manuscript()` 재심사 (최대 3회)
    - **partial**: `_previous_best`가 있고 fix_scope=="partial" → `single_strategy=rejected_strategy`로 해당 전략만 1후보 재생성
    - **full**: `_previous_best` 없거나 fix_scope=="full" → Ensemble 3후보 전면 재생성
  - **InPlace patch state_updates** (TF-46): LLM이 `patch_state_updates` JSON 블록 반환 → 기존 state_updates에 merge (`{**final_state_updates, **_patch_state}`)
  - **patch_state_updates JSON 파싱** (TF-47): `rfind` + `json.loads` 조합으로 중첩 dict 안전 파싱, regex 폴백 유지
- Fallback behavior:
  - 모든 라운드 실패 + 최선 원고 존재 시 사용자 선택으로 진행/건너뛰기
  - 최선 원고도 없으면 인간 검토 필요 메시지 후 세션 반환
  - PASS 후처리의 보조 기능(로그/태깅/분석)은 대부분 비차단 처리

## Manual Intervention Points
- User prompts:
  - `limit_mode` 집필 범위 입력
  - style guide 미존재 시 플랫폼 스타일 선택 입력
  - 라운드 소진 시 `1=최선 결과물 진행 / 2=건너뛰기` 선택
  - 세션 종료 시 TTY 환경에서 Enter 입력 대기
- Approvals:
  - Director PASS가 최종 승인 게이트(이후 CoVe/후검증에서 REJECT 재전환 가능)
- Operator checks:
  - 회차별 Director 점수/사유, QualityGate 강등 로그, 반복/NPC 과잉 경고 확인

## Metrics
- Throughput:
  - Stage4 시도 단위 기록: `pass_rate_monitor.record_attempt(stage=4, episode, attempt_num, success, is_patch, ...)`
- Error rate:
  - `quality_dashboard.record_validation(stage=4)`에 REJECT/EMPTY/PASS 결과 누적
- Latency:
  - `perf_timer`(`generate`, `director` 구간) 및 episode 비용 스냅샷(`cost_log`) 기록

## Tests
- Unit:
  - `tests/test_stage4_context_builder.py`
  - `tests/test_stage4_interview_round.py`
  - `tests/test_stage4_post_processor.py`
  - `tests/test_stage4_orchestrator.py`
  - `tests/test_stage4_cv_context.py`
  - `tests/test_manuscript_validator.py`
- Integration:
  - `tests/test_stage4_context.py`
  - `tests/e2e/test_l3_stage4_smoke.py`
- Regression:
  - `tests/test_director_continuity_sc5.py`
  - `tests/test_director_modules.py`
  - `tests/test_director_bias.py`
  - `tests/test_pre_director_submodules.py`
  - `tests/test_pre_director_checklist_submodules.py`

## Open Risks
- Risk 1: Stage4 패치 진입 조건이 `PatchModeThresholds.REWRITE`(현재 50)로 연결되어 `patch_below`(80) 설정과 동작 불일치 가능성이 있다.
- Risk 2: 후보 생성/Director 응답 파싱 실패가 누적되면 사용자 개입(진행/스킵) 없이는 자동 복구가 제한된다.
- Risk 3: Advisory 체인(LM-A~F) 6개가 순차 실행되므로, LLM 호출 지연이 누적될 수 있다. (현재 advisory는 비차단이므로 실패해도 진행)

## Last Verified
- Date: 2026-03-02
- Commit: `8476bc2`
- Code Sync (Yes/No): Yes
- Verified By: Opus

