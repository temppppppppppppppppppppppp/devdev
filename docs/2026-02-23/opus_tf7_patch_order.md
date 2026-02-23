# TF-7 Patch Order — 24건 확정 패치

> **작성일**: 2026-02-23  
> **기준 문서**: `docs/2026-02-23/opus_tf7_consolidated_report.md`  
> **입력 감사**: `docs/2026-02-23/opus_tf7_{a~n}_audit.md`  
> **목표**: TF-7 확정 이슈를 우선순위(P0/P1/P2)로 일괄 패치하고 회귀를 통과한다.

---

## 0) 실행 원칙
- 중단 없이 `#1 → #24` 순서로 진행.
- 중복 이슈는 단일 패치로 병합:
  - `TF-7-E-1` + `TF-7-N-02-1`
  - `TF-7-D-1` + `TF-7-N-07-1`
- `Risk/FP`는 본 오더에서 제외하고, 마지막에 별도 백로그로 관리.
- 각 패치는 최소 변경 원칙으로 적용.
- 배치 단위 검증:
  - P0 완료 시 1회
  - P1 완료 시 1회
  - P2 완료 시 1회
- 최종 검증:
  - `pytest tests/ -q`
  - `python -m ruff check modules/ tests/ main_a.py`
  - `python -m ruff format --check modules/ tests/ main_a.py`

---

## 1) 진행 테이블

| # | 패치 ID | 우선순위 | 소스 이슈 | 상태 |
|---|---|---|---|---|
| 1 | TF7-P0-01 | P0 | `TF-7-E-1`, `TF-7-N-02-1` | ✅ |
| 2 | TF7-P0-02 | P0 | `TF-7-N-03-1` | ✅ |
| 3 | TF7-P0-03 | P0 | `TF-7-K-1` | ✅ |
| 4 | TF7-P0-04 | P0 | `TF-7-L-1` | ✅ |
| 5 | TF7-P0-05 | P0 | `TF-7-D-1`, `TF-7-N-07-1` | ✅ |
| 6 | TF7-P1-01 | P1 | `TF-7-C-1` | ✅ |
| 7 | TF7-P1-02 | P1 | `TF-7-B-1` | ✅ |
| 8 | TF7-P1-03 | P1 | `TF-7-B-2` | ✅ |
| 9 | TF7-P1-04 | P1 | `TF-7-I-1` | ✅ |
| 10 | TF7-P1-05 | P1 | `TF-7-I-2` | ✅ |
| 11 | TF7-P1-06 | P1 | `TF-7-I-3` | ✅ |
| 12 | TF7-P1-07 | P1 | `TF-7-J-1` | ✅ |
| 13 | TF7-P1-08 | P1 | `TF-7-J-2` | ✅ |
| 14 | TF7-P2-01 | P2 | `TF-7-A-1` | ✅ |
| 15 | TF7-P2-02 | P2 | `TF-7-A-2` | ✅ |
| 16 | TF7-P2-03 | P2 | `TF-7-A-3` | ✅ |
| 17 | TF7-P2-04 | P2 | `TF-7-G-1` | ✅ |
| 18 | TF7-P2-05 | P2 | `TF-7-G-2` | ✅ |
| 19 | TF7-P2-06 | P2 | `TF-7-J-3` | ✅ |
| 20 | TF7-P2-07 | P2 | `TF-7-L-2` | ✅ |
| 21 | TF7-P2-08 | P2 | `TF-7-M-1` | ✅ |
| 22 | TF7-P2-09 | P2 | `TF-7-M-2` | ✅ |
| 23 | TF7-P2-10 | P2 | `TF-7-M-3` | ✅ |
| 24 | TF7-P2-11 | P2 | `TF-7-N-06-1` | ✅ |

---

## 2) P0 (즉시)

### #1 TF7-P0-01 — 롤백 후 world/fact stale 상태 차단
- 대상 파일:
  - `modules/core/services/project_service.py`
  - `main_a.py`
  - `modules/core/stage4_context_builder.py` (검증 확인)
- 변경:
  - rollback 성공 시 `world_state`, `fact_ledger`를 명시적으로 무효화하거나 `rollback_to(target_ep)` 호출.
  - `state_delta_tracker`도 동일 타이밍 초기화/재동기화.
- 완료 기준:
  - rollback 직후 Stage4 진입 시 world/fact가 target ep 기준으로 다시 로드됨.

### #2 TF7-P0-02 — dead NPC BLOCKING을 하드 차단으로 승격
- 대상 파일:
  - `modules/core/stage4_interview_round.py`
  - `modules/validation/blocking_validator.py`
  - `modules/validation/blocking_validator_entity_checks.py`
- 변경:
  - BLOCKING 실패(`severity=CRITICAL`) 후보는 경고 누적이 아니라 즉시 탈락 처리.
  - Director 프롬프트 전달 이전에 후보 필터링.
- 완료 기준:
  - 사망 NPC 행동/대사 검출 시 해당 후보는 최종 선택 대상에서 제외.

### #3 TF7-P0-03 — `preset_state` DB 복원 경로 연결
- 대상 파일:
  - `modules/core/project_manager.py`
  - `main_a.py`
- 변경:
  - `_load_from_db()` 또는 동등 초기화 경로에서 `preset_state` anchor를 `app.preset_registry`로 복원.
  - 롤백 후 `_load_from_db()` 경로에서도 preset 복원 유지.
- 완료 기준:
  - 세션 재기동/롤백 이후에도 Stage2에서 기존 preset 상태를 재사용.

### #4 TF7-P0-04 — Stage4 REJECT도 QualityDashboard 집계
- 대상 파일:
  - `modules/core/stage4_interview_round.py`
  - `modules/core/stage4_post_processor.py`
  - `modules/core/quality_dashboard.py`
- 변경:
  - Stage4 REJECT/EMPTY 분기에서 `quality_dashboard.record_validation(stage=4, decision=REJECT)` 호출.
- 완료 기준:
  - Stage4 pass/reject 집계가 PASS 전용이 아닌 양방향으로 기록.

### #5 TF7-P0-05 — blueprint None/비정규 입력 fail-safe 정규화
- 대상 파일:
  - `modules/validation/blocking_validator_scene_checks.py`
  - `modules/validation/blocking_validator.py`
- 변경:
  - scene 체크 진입부에서 `blueprint`를 dict로 정규화.
  - `blueprint=None`, `blueprint=""`, key 누락 입력에서 예외 없이 명시적 결과 반환.
- 완료 기준:
  - `BlockingValidator().validate(..., {"mode":"MANUSCRIPT","blueprint":None})`가 예외 없이 종료.

---

## 3) P1 (단기)

### #6 TF7-P1-01 — Director Self-Consistency 하드 타임아웃 보장
- 대상 파일: `modules/domain/agents/director_auditor.py`
- 변경:
  - `ThreadPoolExecutor` 종료를 `shutdown(wait=False, cancel_futures=True)`로 제어.
  - timeout 이후 running future 대기 차단.
- 완료 기준:
  - vote timeout 초과 시 함수 전체가 상한 시간 내 반환.

### #7 TF7-P1-02 — Stage4 NPC 토큰 추출 정밀화
- 대상 파일:
  - `modules/core/stage4_context_builder.py`
  - `modules/core/vec_memory.py` (검증 확인)
- 변경:
  - 한국어 일반어 stopword 확장.
  - 가능한 경우 `npc_roster` 우선 전달.
- 완료 기준:
  - 일반어가 core name 슬롯을 점유하지 않음.

### #8 TF7-P1-03 — Stage4 SC budget gate 정렬
- 대상 파일: `modules/core/stage4_context_builder.py`
- 변경:
  - budget trim 조건을 `smart_retrieval.enabled && smart_retrieval.stage4_enabled`로 맞춤.
  - 비-SC 필수 섹션 보호 우선순위 부여.
- 완료 기준:
  - Stage4 SC 비활성 시 mandatory non-SC 컨텍스트가 불필요하게 절삭되지 않음.

### #9 TF7-P1-04 — PassRate 통계를 Director 선택에 연결
- 대상 파일:
  - `modules/core/stage4_interview_round.py`
  - `modules/domain/agents/director_ensemble.py`
  - `modules/core/db_manager.py`
- 변경:
  - 전략별 승률(`get_strategy_win_rates`)을 선택 단계에 주입.
  - Stage4 기록 키를 `ensemble/patch`에서 실제 strategy key 단위로 세분화.
- 완료 기준:
  - 전략 통계가 다음 라운드 선택에 실질 반영됨.

### #10 TF7-P1-05 — AdaptiveRetryManager를 Stage4 재시도 루프에 연결
- 대상 파일:
  - `modules/core/stage4_context.py`
  - `modules/core/stage4_types.py`
  - `modules/core/stage4_interview_round.py`
  - `main_a.py`
- 변경:
  - Stage4 REJECT 시 `record_failure` + `get_injection_prompt` 호출.
  - 다음 라운드 프롬프트에 adaptive guidance 주입.
- 완료 기준:
  - Stage4 루프가 adaptive retry 데이터에 따라 분기.

### #11 TF7-P1-06 — Stage4 실패를 FailureLearner에 기록
- 대상 파일:
  - `modules/core/stage4_interview_round.py`
  - `modules/core/failure_learning.py`
- 변경:
  - REJECT/major warning를 learner 이벤트로 기록.
  - dynamic prompt weighting 입력으로 환류.
- 완료 기준:
  - Stage4 실패 패턴이 learner 히스토리에 누적됨.

### #12 TF7-P1-07 — rollback 시 `director_selections` 정리
- 대상 파일:
  - `modules/core/services/project_service.py`
  - `modules/core/db_manager.py`
- 변경:
  - rollback 삭제 대상에 `director_selections` 포함.
- 완료 기준:
  - target ep 이후 selection log가 제거되고 종료 분석이 오염되지 않음.

### #13 TF7-P1-08 — ForeshadowTracker rollback 동기화
- 대상 파일:
  - `main_a.py`
  - `modules/core/services/project_service.py`
  - `modules/core/foreshadow_tracker.py`
- 변경:
  - rollback 성공 후 foreshadow 상태 clear + target ep 기준 재구성/trim.
- 완료 기준:
  - rollback으로 폐기된 미래 복선이 다음 프롬프트에 주입되지 않음.

---

## 4) P2 (중기)

### #14 TF7-P2-01 — ReverseExpander 저장 원자화
- 대상 파일:
  - `modules/core/stage0/reverse_expander.py`
  - `modules/core/stage01_helpers.py`
- 변경:
  - `persist_to_db()`를 단일 트랜잭션으로 묶고 하위 `_save_*` 개별 commit 제거.

### #15 TF7-P2-02 — Preset 충돌 우선순위 결정화
- 대상 파일: `modules/core/stage0/preset_registry.py`
- 변경:
  - `active_presets`를 순서 보장 구조로 전환.
  - 충돌 시 우선순위 규칙 명시.

### #16 TF7-P2-03 — Style/Work Guard 체인 실연결
- 대상 파일:
  - `modules/core/genre_guards/__init__.py`
  - `modules/validation/consistency_validator.py`
  - `modules/validation/scoring_validator.py`
  - `modules/core/stage01_helpers.py`
- 변경:
  - Guard factory에서 `Genre -> Work -> Style` 래핑 지원.
  - Stage0 저장된 style/work 설정을 validator 소비 경로에 주입.

### #17 TF7-P2-04 — PatternTracker 분석 전 상태 리셋
- 대상 파일: `modules/core/pattern_tracker.py`
- 변경:
  - `analyze_manuscripts()` 시작 시 window 기준 상태 초기화.

### #18 TF7-P2-05 — 플롯 시퀀스 탐지 포인터 매칭
- 대상 파일: `modules/core/pattern_tracker.py`
- 변경:
  - `str.find` 첫 매치 방식에서 순차 포인터 매칭으로 전환.

### #19 TF7-P2-06 — EmotionArcTracker Stage4 배선 완성
- 대상 파일:
  - `modules/core/stage4_context.py`
  - `main_a.py`
  - `modules/core/stage4_post_processor.py`
  - `modules/core/emotion_tracker.py`
- 변경:
  - Stage4 주입, 후처리 갱신, 종료 시 저장, rollback 동기화 경로 추가.

### #20 TF7-P2-07 — PassRateMonitor 경보 소비 체인 연결
- 대상 파일:
  - `modules/core/pass_rate_monitor.py`
  - `main_a.py`
  - `modules/core/quality_dashboard.py`
- 변경:
  - `check_alerts()` 호출 지점을 운영 루프에 연결하고 경보 이벤트를 기록/표시.

### #21 TF7-P2-08 — `validation.yaml` 누락 키 SSOT 보강
- 대상 파일:
  - `config/settings/validation.yaml`
  - `modules/core/config_manager.py`
- 변경:
  - 감사에서 식별된 누락 임계값 키(`scope/scoring/smart_retrieval`) 추가.
  - 누락 키 발견 시 1회 경고 로깅.

### #22 TF7-P2-09 — `settings.json.validation` dead config 정리
- 대상 파일:
  - `config/settings.json`
  - `main_a.py`
  - `modules/domain/agents/director_auditor.py`
- 변경:
  - 실제 소비 경로로 merge하거나 dead key 제거해 단일 설정 소스 유지.

### #23 TF7-P2-10 — Analyst 프롬프트 외부화 완결
- 대상 파일:
  - `config/prompts/analyst.yaml`
  - `modules/domain/agents/analyst_prompt_api.py`
  - `modules/domain/agents/analyst_prompts.py`
- 변경:
  - `RECOVERY_PROMPT`, `VOLUME_STRATEGY_PROMPT`를 YAML로 이관.
  - legacy fallback 정리 또는 deprecation 로그 처리.

### #24 TF7-P2-11 — Director max-rounds 로그 문구 정합화
- 대상 파일: `modules/core/stage4_orchestrator.py`
- 변경:
  - 실패 로그의 “5회” 하드코딩 문구를 `_max_rounds` 동적 값으로 변경.

---

## 5) 배치 검증 체크포인트

| CP | 범위 | 검증 명령 | 상태 |
|---|---|---|---|
| CP-1 | #1~#5 | `pytest tests/ -q` + ruff 2종 | ⬜ |
| CP-2 | #6~#13 | `pytest tests/ -q` + ruff 2종 | ⬜ |
| CP-3 | #14~#24 | `pytest tests/ -q` + ruff 2종 | ⬜ |

---

## 6) 제외 백로그 (Risk/FP)
- Risk 항목은 본 패치 오더에서 직접 수정하지 않음:
  - `TF-7-B-R1`, `TF-7-B-R2`
  - `TF-7-C-R1`, `TF-7-C-R2`
  - `TF-7-D-R1`, `TF-7-D-R2`
  - `TF-7-E-R1`
  - `TF-7-F-R1`
  - `TF-7-G-R1`
  - `TF-7-H-R1`
  - `TF-7-I-R1`
  - `TF-7-J-R1`, `TF-7-J-R2`
  - `TF-7-K-R1`
  - `TF-7-L-R1`
  - `TF-7-M-R1`, `TF-7-M-R2`
  - `TF-7-N-R1`, `TF-7-N-R2`

