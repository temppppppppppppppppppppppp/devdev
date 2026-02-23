# TF-7-D 감사 보고서: Validation Orchestrator 안전성

## 감사 파일 목록
- `modules/validation/validation_orchestrator.py`
- `modules/validation/advisory_validator.py`
- `modules/validation/blocking_validator.py`
- `modules/validation/blocking_validator_scene_checks.py`
- `modules/validation/pre_llm_validator.py`
- `modules/validation/scoring_validator.py`
- `modules/validation/continuity_validator.py`
- `modules/validation/consistency_validator.py`
- `modules/domain/agents/director_auditor.py`
- `modules/core/stage4_post_processor.py`

## 발견 이슈 (총 1건)

### [TF-7-D-1] `validation_context["blueprint"] = None` 입력 시 BLOCKING Scene 체크가 예외로 중단되어 검증 파이프라인이 하드 실패함 (HIGH)
**근거 파일/라인**
- `modules/validation/validation_orchestrator.py:355` (`self.blocking.validate(...)` 동기 경로)
- `modules/validation/validation_orchestrator.py:1087` (`self.blocking.validate(...)` 병렬 경로 Stage1)
- `modules/validation/blocking_validator.py:77` (`_check_required_scenes` 호출)
- `modules/validation/blocking_validator.py:167` (`scene_checks._check_required_scenes(...)` 위임)
- `modules/validation/blocking_validator_scene_checks.py:46` (`blueprint = context.get("blueprint", {})`)
- `modules/validation/blocking_validator_scene_checks.py:47` (`scene_breakdown = blueprint.get(...)` - `None`에서 AttributeError)
- `modules/validation/blocking_validator_scene_checks.py:91`, `modules/validation/blocking_validator_scene_checks.py:164`, `modules/validation/blocking_validator_scene_checks.py:243` (동일한 `blueprint` 비정규화 접근이 반복됨)

**재현 (수동 실행)**
- 실행: `BlockingValidator().validate("테스트 원고", {"mode": "MANUSCRIPT", "blueprint": None})`
- 결과: `AttributeError: 'NoneType' object has no attribute 'get'`
- traceback 핵심:
  - `modules/validation/blocking_validator.py:77`
  - `modules/validation/blocking_validator_scene_checks.py:47`

**문제**
- `blueprint`가 `None`인 입력이 들어오면, BLOCKING의 Scene 체크가 방어 없이 `.get()`를 수행해 예외를 발생시킨다.
- 이 예외는 `BlockingValidator.validate()`에서 흡수되지 않으므로 상위 오케스트레이터 검증 루틴 자체가 중단된다.

**영향**
- Stage4 검증이 REJECT 판단이 아니라 런타임 예외로 종료될 수 있어, 무중단 운영 목표와 충돌한다.
- 특히 `mode="MANUSCRIPT"` 경로에서 필수적으로 Scene 체크를 타므로 회피가 어렵다.

**Caller→Callee 계약 추적**
- Caller: `modules/validation/validation_orchestrator.py:355`, `modules/validation/validation_orchestrator.py:1087`
- Callee: `modules/validation/blocking_validator.py:56` → `modules/validation/blocking_validator.py:77` → `modules/validation/blocking_validator_scene_checks.py:44`
- 위반 계약: `validation_context`의 optional payload(`blueprint`)는 누락/None이어도 validator는 안정적으로 PASS/WARNING fallback 해야 함.

**Bug-vs-intent 근거**
- 같은 파일에서 `scene_breakdown` 미존재 시 PASS fallback 의도가 명시되어 있음 (`modules/validation/blocking_validator_scene_checks.py:49`~`modules/validation/blocking_validator_scene_checks.py:51`).
- 그러나 fallback 이전에 `blueprint.get(...)`로 즉시 접근하여 의도와 구현이 불일치한다.

**권장 수정 방향**
- Scene 체크 진입 시 공통 정규화 추가:
  - `blueprint = context.get("blueprint")`
  - `if not isinstance(blueprint, dict): blueprint = {}`
- 동일 패턴을 `_check_required_scenes`, `_check_scope_overflow`, `_check_scene_completeness`, `_check_cliffhanger_ending`에 일관 적용.
- 회귀 테스트 추가:
  - `blueprint=None`
  - `blueprint=""` (str)
  - `blueprint` 키 누락

## Risk (총 2건)

### [TF-7-D-R1] `prev_hud` 부재 시 CONTINUITY 핵심 체크(1~4)가 스킵되어 탐지력이 급격히 낮아질 위험 (MEDIUM, Risk)
**근거 파일/라인**
- `modules/validation/continuity_validator.py:107`~`modules/validation/continuity_validator.py:114` (`prev_hud` 없으면 경고만 기록)
- `modules/validation/continuity_validator.py:121`, `modules/validation/continuity_validator.py:129`, `modules/validation/continuity_validator.py:137`, `modules/validation/continuity_validator.py:145` (핵심 체크 1~4는 `else` 블록에서만 실행)
- `modules/validation/continuity_validator.py:196`~`modules/validation/continuity_validator.py:214` (`self.context.db` 없으면 이전 HUD 복원 불가)
- `modules/domain/agents/director_auditor.py:232`~`modules/domain/agents/director_auditor.py:236` (오케스트레이터 `context`로 validation dict 주입)

**Risk 판단 근거**
- 현재 구조는 `prev_hud`가 컨텍스트에 주입되지 않으면 BLOCKING급 continuity 검증이 사실상 비활성화된다.
- 즉시 장애 증거는 확인되지 않아 Risk로 분류.

### [TF-7-D-R2] POV 검증에서 `protagonist_name` 미주입으로 3인칭 감지 민감도가 낮아질 위험 (LOW, Risk)
**근거 파일/라인**
- `modules/validation/pre_llm_validator.py:34`~`modules/validation/pre_llm_validator.py:43` (`protagonist_name` 입력 설계)
- `modules/validation/pre_llm_validator.py:434`~`modules/validation/pre_llm_validator.py:437` (주인공명 기반 3인칭 패턴 확장)
- `modules/validation/validation_orchestrator.py:204` (`PreLLMValidator(genre=..., pov=...)`로만 생성)
- `modules/domain/agents/director_auditor.py:241`~`modules/domain/agents/director_auditor.py:243` (런타임 갱신도 `pov`만 수행)

**Risk 판단 근거**
- 검증 기능은 동작하지만 이름 기반 보정이 비활성화되어 오탐/미탐 확률이 증가할 수 있다.

## [FP] 오탐 목록

### [FP-1] 병렬 경로에서 `advisory_result`가 dict가 아니면 상세 피드백 생성 시 크래시한다
- **판정**: 오탐
- **수동 근거**:
  - `modules/validation/validation_orchestrator.py:1144`~`modules/validation/validation_orchestrator.py:1146` (non-dict advisory를 `{"suggestions": []}`로 강제 정규화)
  - `modules/validation/validation_orchestrator.py:828`~`modules/validation/validation_orchestrator.py:834` (`suggestions` 안전 접근)

### [FP-2] Pre-LLM에서 critical issue가 있으면 즉시 REJECT된다
- **판정**: 오탐
- **수동 근거**:
  - `modules/validation/pre_llm_validator.py:127`~`modules/validation/pre_llm_validator.py:134` (`passed=True`, `critical_issues=[]` 고정)
  - `modules/validation/validation_orchestrator.py:313` (PreLLM 결과는 경고/감점용으로만 사용)

### [FP-3] Episode 1에서 `prev_hud`가 없으면 CONTINUITY가 실패한다
- **판정**: 오탐
- **수동 근거**:
  - `modules/validation/continuity_validator.py:96`~`modules/validation/continuity_validator.py:104` (`current_ep <= 1` 즉시 PASS)

## TF-5-K 패치 회귀 확인 (K-1, K-2, K-3)

| 패치 항목 | 결과 | 근거 |
|---|---|---|
| K-1 `required_scenes` 최소치 계산 오류 수정 (`min(4, scene_count)`) | 회귀 없음 | `modules/validation/blocking_validator_scene_checks.py:54`, `modules/validation/blocking_validator_scene_checks.py:55` |
| K-2 필수씬 체크에서 blueprint 미존재 fallback 유지 | 회귀 없음 (단, `blueprint=None` 결함은 TF-7-D-1로 별도 확인) | `modules/validation/blocking_validator_scene_checks.py:49`~`modules/validation/blocking_validator_scene_checks.py:51` |
| K-3 ConsistencyValidator의 Genre Guard 동적 로딩 통합 | 회귀 없음 | `modules/validation/consistency_validator.py:15`, `modules/validation/consistency_validator.py:47`~`modules/validation/consistency_validator.py:54`, `modules/validation/validation_orchestrator.py:214` |

## TF-5-L 패치 회귀 확인 (L-1: quality_dashboard stage=4)

| 패치 항목 | 결과 | 근거 |
|---|---|---|
| L-1 `quality_dashboard.record_validation(stage=4)` 호출 경로 유지 | 회귀 없음 | 호출 위치 유지: `modules/core/stage4_post_processor.py:578`~`modules/core/stage4_post_processor.py:582`; ValidationOrchestrator 내 직접 호출 없음 (`modules/validation/validation_orchestrator.py` 전역 확인) |

## 요약 테이블
| 분류 | 건수 | 항목 |
|---|---:|---|
| HIGH | 1 | `TF-7-D-1` |
| Risk | 2 | `TF-7-D-R1`, `TF-7-D-R2` |
| FP | 3 | `FP-1~3` |
