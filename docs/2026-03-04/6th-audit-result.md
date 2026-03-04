# 6차 전수조사 결과

> 감사일: 2026-03-04

## 감사 범위

A. TF-54 신규 파일 3개 (`pattern_tracker.py`, `writing_directive_generator.py`, `stage4_types.py`)
B. Model SSOT 후속 2개 (`constants.py`, `config_manager.py`)
C. 합격률 개선 후속 2개 (`chief_writer_quality.py`, `stage4_interview_round.py`)
D. 모델 하드코딩 잔여 9개 파일 호출 경로 점검

## A/B/C 점검 결과

- A-1: `PatternTracker.build_report(db=None)` 실행 시 `PatternReport(expression_freq={}, ending_patterns=[], ...)` 반환 확인. 예외 없음.
- A-2: `WritingDirectiveGenerator._parse_response()`에 빈 문자열/비JSON 입력 시 `WritingDirective()` 반환, `expression_ban` 문자열 입력 시 리스트 정규화 확인.
- A-3: `WritingDirective.is_empty()`는 `ending_style/metaphor_avoid/expression_ban` 3필드 기준 동작이며, 관련 테스트 명세(`tests/test_pipeline_wiring.py:163-172`)와 일치.
- B-1: `_load_model_from_yaml()`의 지연 import(`import yaml` in function), broad exception fallback, 빈 문자열 fallback 조건 확인.
- B-2: `ConfigManager` fallback dict가 `models.yaml`과 불일치하여 P1로 분류 후 패치.
- C-1: `setattr(chief_writer, "_current_blueprint", blueprint if isinstance(blueprint, dict) else {})` 가드 확인.
- C-2: `apply_self_critique()` 내 `_self_critique()` 2개 호출 경로 모두 `blueprint/directive/expression_freq` 전달 확인.

## 발견 이슈

| ID | 파일 | 내용 | 등급 | 처리 |
|----|------|------|------|------|
| B-001 | `modules/core/config_manager.py` | `models.yaml` 로드 실패 시 fallback `models` dict가 SSOT `agents`와 불일치(`writer=pro`, 키 누락/과잉) | P1 | 조치 완료 |
| D-001 | `modules/core/reference_anchor.py` | `BaseAgent(... model_tier="gemini-2.5-flash")` 하드코딩. 호출자 주입 경로 없음 | P1 | 조치 완료 |
| D-002 | `modules/core/confidence_calibration.py` | LLM 평가 모델이 클래스 내부 하드코딩되어 호출자 model 주입 불가 | P1 | 조치 완료 |

## 조치 내역

### B-001 `modules/core/config_manager.py`

- before: fallback dict 5개 키(analyst/writer/director/manager/editor), `writer="gemini-2.5-pro"`
- after: fallback dict를 `config/models.yaml` `agents` 구조(20개 키)와 동일하게 정렬, `writer="gemini-2.5-flash"`로 교정

### D-001 `modules/core/reference_anchor.py`

- before: `BaseAgent(... model_tier="gemini-2.5-flash")`
- after: `BaseAgent(... model_tier=AIModels.FLASH_ANALYSIS_MODEL)`

### D-002 `modules/core/confidence_calibration.py`

- before: `self.model = "gemini-2.5-flash"`
- after:
  - `__init__(..., model: str = AIModels.FLASH_ANALYSIS_MODEL)` 인자 추가
  - `self.model = model if isinstance(model, str) and model.strip() else AIModels.FLASH_ANALYSIS_MODEL`

## 검증 결과

- `python -m py_compile modules/core/config_manager.py modules/core/reference_anchor.py modules/core/confidence_calibration.py`: 통과
- `pytest tests/ -q`: **3213 passed, 16 skipped, 0 failed** (warning 1건)
- `ruff check modules/ tests/`: **All checks passed**

## P2 목록 (조치 유보 + 사유)

| 파일 | 라인 | 분류 사유 |
|------|------|----------|
| `modules/core/adversarial_self_play.py` | 136 | 운영 초기화 경로에서 `main_a.py:1929-1932`로 model 명시 주입 |
| `modules/core/chain_of_verification.py` | 122 | 운영 초기화 경로에서 `main_a.py:1904-1907`로 model 명시 주입 |
| `modules/core/cross_agent_verifier.py` | 118 | 운영 초기화 경로에서 `main_a.py:1893-1896`로 model 명시 주입 |
| `modules/core/multi_agent_deliberation.py` | 181 | 운영 초기화 경로에서 `main_a.py:1936-1939`로 model 명시 주입 |
| `modules/domain/agents/arc_corrector.py` | 592 | helper `create_arc_corrector()` 호출부 없음(정의만 존재), 운영 경로는 `main_a.py:1545-1549` 명시 주입 |
| `modules/domain/agents/arc_critic.py` | 131, 368 | 운영 경로 `main_a.py:1528-1530` 명시 주입, helper `create_arc_critic()` 호출부 없음 |
| `modules/domain/agents/arc_ensemble.py` | 113, 890 | 운영 경로 `main_a.py:1512-1514` 명시 주입, helper `create_ensemble_generator()` 호출부 없음 |

## 결론

- 신규 P0: 0건
- 신규 P1: 3건 발견, 3건 패치 완료
- P2: 7개 파일(10개 라인) 유보
- 검증: `py_compile` 통과, `pytest` 3213/16/0, `ruff` 위반 0건
