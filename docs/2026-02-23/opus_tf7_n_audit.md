# TF-7-N 감사 보고서 — 크로스컷 시나리오 스윕

## 시나리오별 결과 요약 테이블

| 시나리오 | 결과 | 이슈 수 | 심각도 |
|---|---|---:|---|
| N-01 Episode 1 초기 진입 | PASS (방어 분기 일치) | 0 | - |
| N-02 롤백 후 상태 재진입 | FAIL | 1 | HIGH |
| N-03 deceased NPC Arc 등장 시도 | FAIL | 1 | HIGH |
| N-04 동적 장르 전환 | RISK | 0 | - |
| N-05 Arc 응답 `{}` | PASS (retry) | 0 | - |
| N-06 Director 다회 REJECT 소진 | PARTIAL | 1 | LOW |
| N-07 Blueprint `scenes=None` 관통 | FAIL 조건부 | 1 | MEDIUM |
| N-08 상태 누적 상한 패치 | PASS (회귀 없음) | 0 | - |
| N-09 `ep_count=1` Flow Guard | PASS (회귀 없음, 설정 드리프트 위험) | 0 | - |
| N-10 Arc Ensemble 타임아웃 | PASS (degrade 처리) | 0 | - |

## 발견 이슈 (총 4건)

### [TF-7-N-02-1] 롤백 후 Stage4 재진입 시 stale world/fact 요약이 주입될 수 있음 (HIGH)
**증거 파일/라인**
- `modules/core/services/project_service.py:220`
- `modules/core/services/project_service.py:221`
- `main_a.py:289`
- `main_a.py:2784`
- `main_a.py:3028`
- `main_a.py:3043`
- `modules/core/stage4_context_builder.py:582`
- `modules/core/stage4_context_builder.py:614`

**수동 근거**
- 롤백 직후 invalidator는 `state_tracker`만 초기화한다.
- Stage4 재진입 시 `world_state`/`fact_ledger`는 `None`일 때만 새로 로드한다.
- mandatory context 구성은 현재 메모리의 world/fact 요약을 우선 주입한다.

**판정**
- N-02 시나리오(롤백→즉시 재집필)에서 이전 상태 잔존 가능성이 있다.
- TF-7-E-1과 동일한 seam 이슈로 Cross-TF HIGH로 확정.

### [TF-7-N-03-1] dead NPC BLOCKING 실패가 후보 탈락이 아닌 경고 텍스트로만 전달됨 (HIGH)
**증거 파일/라인**
- `modules/validation/blocking_validator_entity_checks.py:91`
- `modules/validation/blocking_validator_entity_checks.py:95`
- `modules/validation/blocking_validator.py:138`
- `modules/validation/blocking_validator.py:140`
- `modules/core/stage4_interview_round.py:356`
- `modules/core/stage4_interview_round.py:361`
- `modules/domain/agents/director_ensemble.py:330`
- `modules/domain/agents/director_ensemble.py:352`

**수동 근거**
- dead NPC 행동/대사 탐지는 `passed=False`/`severity=CRITICAL`로 생성된다.
- BlockingValidator 결과는 `passed=False`와 `failures`를 반환한다.
- 하지만 Stage4 면담 루프는 실패를 후보 탈락으로 처리하지 않고 warnings에 누적한다.
- Director 앙상블은 warnings를 프롬프트 텍스트로 전달할 뿐 하드 차단을 수행하지 않는다.

**판정**
- N-03 시나리오에서 “차단 계층”이 advisory로 약화되어 우회 PASS 가능성이 남는다.

### [TF-7-N-07-1] Blueprint 씬 정보 누락 시 장면 검증이 자동 PASS로 전환되는 경로가 존재함 (MEDIUM)
**증거 파일/라인**
- `modules/validation/blocking_validator_scene_checks.py:49`
- `modules/validation/blocking_validator_scene_checks.py:51`
- `modules/validation/blocking_validator_scene_checks.py:167`
- `modules/validation/blocking_validator_scene_checks.py:168`
- `modules/domain/agents/blueprint_ensemble.py:441`
- `modules/domain/agents/blueprint_ensemble.py:442`

**수동 근거**
- Scene 체크 2종(`required_scenes`, `scene_completeness`)은 `scene_breakdown`이 없으면 PASS로 반환한다.
- BlueprintEnsemble 단에서는 필수 필드가 없으면 `None`으로 방어하지만, 상위 경로에서 `None/빈 blueprint`가 유입되면 장면 검증은 스킵 PASS가 된다.

**판정**
- 정상 생성 경로에서는 완화되지만, 비정상/폴백 경로에서 silent PASS seam이 유지된다.

### [TF-7-N-06-1] Director 최대 면담 횟수는 설정 가능하지만 최종 실패 로그 문구가 5회로 고정됨 (LOW)
**증거 파일/라인**
- `modules/core/stage4_orchestrator.py:540`
- `modules/core/stage4_orchestrator.py:543`
- `modules/core/stage4_orchestrator.py:631`

**수동 근거**
- 면담 최대 횟수는 threshold 기반으로 동적 계산한다.
- 그러나 완전 실패 문구는 `5회 면담 모두 실패`로 하드코딩되어 운영 로그와 설정값이 어긋날 수 있다.

## TF-6 패치 회귀 확인 (N-08, N-09)

| 패치 | 확인 여부 | 증거 |
|---|---|---|
| TF-B-1 `resolved_plots` 상한 500 | ✅ | `modules/domain/agents/state_tracker.py:133`, `modules/domain/agents/state_tracker_plots.py:119` |
| TF-B-2 `all_reveals` 상한 500 | ✅ | `modules/core/db_manager.py:903`~`modules/core/db_manager.py:905` |
| TF-B-3 `feedback_log` deque 200 | ✅ | `modules/core/data_collector.py:351` |
| TF-E-1 `ep_count=1` Flow Guard 보정 | ✅ | `modules/core/stage2_validation_pipeline.py:620`, `modules/core/stage2_validation_pipeline.py:632` |

## Cross-TF 이슈 (복수 TF 관련)
- `TF-7-E-1` ↔ `TF-7-N-02-1`: 롤백 이후 상태 객체 동기화 누락
- `TF-7-D-1` ↔ `TF-7-N-07-1`: blueprint 비정상 경로에서 장면 검증 silent PASS
- `TF-7-H-R1` ↔ `TF-7-N-03-1`: dead NPC 차단 경로의 최종 강제성 부족

## Risk (추가 확인 필요)

### [TF-7-N-R1] 동적 장르 확장 이후 Guard/Validator 체인 즉시 재초기화 여부 불명확 (MEDIUM, Risk)
**증거 파일/라인**
- `modules/core/stage2_preflight.py:978`
- `modules/core/stage2_preflight.py:981`
- `modules/domain/agents/state_tracker.py:309`
- `modules/domain/agents/state_tracker.py:312`
- `modules/validation/validation_orchestrator.py:190`
- `modules/validation/validation_orchestrator.py:214`

### [TF-7-N-R2] `ep_count=1` 패치는 적용됐지만 `validation.yaml`에 `scope.min_beats_floor` 키가 없어 코드 fallback 의존 (MEDIUM, Risk)
**증거 파일/라인**
- `modules/core/stage2_validation_pipeline.py:620`
- `modules/core/stage2_validation_pipeline.py:632`
- `config/settings/validation.yaml:25`
- `config/settings/validation.yaml:28`

## [FP] 오탐 목록

### [FP-1] Episode 1에서는 이전 데이터 부재로 연속성 검증이 깨진다
- **판정**: 오탐
- **수동 근거**:
  - `modules/core/stage4_context_builder.py:237`
  - `modules/core/stage4_context_builder.py:277`
  - `modules/validation/continuity_validator.py:97`~`modules/validation/continuity_validator.py:104`

### [FP-2] Arc 응답 `{}`는 Stage2에서 즉시 크래시한다
- **판정**: 오탐
- **수동 근거**:
  - `modules/domain/agents/arc_ensemble.py:454`
  - `modules/core/stage2_validation_pipeline.py:172`~`modules/core/stage2_validation_pipeline.py:180`

### [FP-3] Arc Ensemble 타임아웃은 전체 실패로 직결된다
- **판정**: 오탐
- **수동 근거**:
  - `modules/domain/agents/arc_ensemble.py:179`
  - `modules/domain/agents/arc_ensemble.py:194`
  - `modules/domain/agents/arc_ensemble.py:203`

### [FP-4] Blueprint 생성기는 씬 필수 필드를 검증하지 않는다
- **판정**: 오탐
- **수동 근거**:
  - `modules/domain/agents/blueprint_ensemble.py:441`
  - `modules/domain/agents/blueprint_ensemble.py:442`

## 요약 테이블
| 분류 | 건수 | 항목 |
|---|---:|---|
| HIGH | 2 | `TF-7-N-02-1`, `TF-7-N-03-1` |
| MEDIUM | 1 | `TF-7-N-07-1` |
| LOW | 1 | `TF-7-N-06-1` |
| Risk | 2 | `TF-7-N-R1`, `TF-7-N-R2` |
| FP | 4 | `FP-1~4` |

