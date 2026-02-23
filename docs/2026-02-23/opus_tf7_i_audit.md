# TF-7-I 감사 보고서 — Adaptive Retry / Feedback / Failure Learning

## 감사 파일 목록
- `modules/core/adaptive_retry.py`
- `modules/core/feedback_system.py`
- `modules/core/failure_learning.py`
- `modules/core/reflexion_manager.py`
- `modules/core/pass_rate_monitor.py`
- `modules/core/stage4_interview_round.py`
- `modules/domain/agents/director_ensemble.py`
- `modules/core/stage4_context.py`
- `modules/core/stage4_types.py`
- `modules/core/stage2_validation_pipeline.py`
- `modules/core/stage2_preflight.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/db_manager.py`
- `main_a.py`

## 발견 이슈 (총 3건)

### [TF-7-I-1] PassRateMonitor의 전략 통과율 데이터가 Director 선택 로직에 연결되지 않음 (HIGH)
**근거 파일/줄**
- `modules/core/stage4_interview_round.py:621`~`modules/core/stage4_interview_round.py:634` (Director 선택 호출)
- `modules/core/stage4_interview_round.py:934`~`modules/core/stage4_interview_round.py:958` (Stage4 시도 기록: `generation_method`가 `ensemble/patch`로만 기록)
- `modules/domain/agents/director_ensemble.py:342`~`modules/domain/agents/director_ensemble.py:359` (선택 프롬프트 구성)
- `modules/domain/agents/director_ensemble.py:394`~`modules/domain/agents/director_ensemble.py:413` (LLM 결과로 후보 선택)
- `modules/core/db_manager.py:1811`~`modules/core/db_manager.py:1833` (`get_strategy_win_rates` 존재)
- `main_a.py:2093`~`main_a.py:2111` (`get_selection_analysis`는 종료 시 advisory 출력만 수행)

**문제**
- 모니터에는 Stage4 결과가 저장되지만, Director 후보 선택 시 해당 성공률/전략률을 읽어 반영하는 코드 경로가 없다.
- 기록 단위도 `ensemble/patch` 수준이라 전략 A/B/C별 통과율 학습 자체가 불가능하다.

**영향**
- “전략별 통과율 기반 선택 최적화”가 동작하지 않아 동일 실패 전략 재선택이 반복될 수 있다.
- 데이터는 누적되지만 의사결정에 쓰이지 않는 관측 전용 텔레메트리로 고착된다.

**권장 수정 방향**
- Director 선택 직전에 `get_strategy_win_rates()`/유사 통계를 읽어 프롬프트 또는 사전 스코어링에 반영.
- Stage4 기록 시 `generation_method`를 `ensemble`이 아니라 실제 선택 전략 키(예: `A/B/C` 매핑된 strategy key)로 남기도록 분해.

### [TF-7-I-2] AdaptiveRetryManager가 초기화만 되고 Stage4 재시도 루프에 연결되지 않음 (HIGH)
**근거 파일/줄**
- `main_a.py:323` (`self.adaptive_manager` 선언)
- `main_a.py:1775`~`main_a.py:1779` (AdaptiveRetryManager 초기화 + FailureLearner 연동)
- `modules/core/stage4_interview_round.py:127`~`modules/core/stage4_interview_round.py:166` (재시도 시 `generate_ensemble`/`regenerate_with_feedback`/`patch_with_feedback` 직접 호출)
- `modules/core/stage4_types.py:25`~`modules/core/stage4_types.py:57` (`_RoundContext`에 adaptive manager/가이드 필드 부재)
- `modules/core/stage4_context.py:30`~`modules/core/stage4_context.py:62` (`Stage4Context` 주입 대상에 adaptive manager 부재)

**문제**
- AdaptiveRetryManager는 생성되지만, 실제 Stage4 면담 재시도 경로에서 `record_failure`/`get_retry_guidance`/`get_injection_prompt`를 호출하지 않는다.

**영향**
- 실패 유형 분류/에스컬레이션/필살기 권고(설계 의도)가 실운영 경로에서 비활성화된다.
- 재시도는 Director 텍스트 피드백 중심의 정적 루프로 남아 적응형 개선 이득이 사라진다.

**권장 수정 방향**
- Stage4 REJECT 분기에서 AdaptiveRetryManager에 실패 기록 후, 다음 라운드 프롬프트에 `get_injection_prompt()`를 병합.
- `_RoundContext`/`Stage4Context`에 필요한 핸들 주입 또는 `self.ctx.get_module(...)` 경로로 표준화.

### [TF-7-I-3] FailureLearner가 Stage4 실패를 학습하지 않아 Stage4 가중 프롬프트가 Stage2 편향 데이터에 의존함 (MEDIUM)
**근거 파일/줄**
- `modules/core/stage2_validation_pipeline.py:425`~`modules/core/stage2_validation_pipeline.py:433` (FailureLearner 기록은 Stage2 경로 존재)
- `modules/core/dynamic_prompt_weighting.py:159`~`modules/core/dynamic_prompt_weighting.py:160` (최근 실패 기록으로 가중치 계산)
- `main_a.py:1728` (DynamicPromptWeighter에 FailureLearner 주입)
- `modules/core/stage4_interview_round.py:115`~`modules/core/stage4_interview_round.py:124` (Stage4에서 가중 프롬프트 주입)
- `modules/core/stage4_interview_round.py:781`~`modules/core/stage4_interview_round.py:861` (Stage4 REJECT 처리에 FailureLearner 기록 없음)

**문제**
- Stage4에서 가중 프롬프트를 사용하지만, Stage4 실패 자체는 FailureLearner로 환류되지 않는다.

**영향**
- 장기적으로 Stage4 최적화 신호가 누락되어 가중치가 실제 실패 분포를 반영하지 못한다.

**권장 수정 방향**
- Stage4 REJECT 시 `reject_bucket`, `action_items`, `selection_reason`를 FailureLearner 카테고리로 매핑해 기록.

## Risk (총 1건)

### [TF-7-I-R1] Reflexion 프롬프트는 주입되지만 Stage4 전용 실패 학습 루프는 간접 의존 (MEDIUM, Risk)
**근거 파일/줄**
- `modules/core/stage4_context_builder.py:811`~`modules/core/stage4_context_builder.py:816` (EP20+에서 Reflexion 프롬프트 주입)
- `modules/validation/validation_orchestrator.py:332`, `modules/validation/validation_orchestrator.py:360`, `modules/validation/validation_orchestrator.py:1011` (Reflexion 기록 경로)
- `modules/domain/agents/manuscript_validator.py:18`~`modules/domain/agents/manuscript_validator.py:29` (Stage4 사전검증은 별도 Python validator)

**Risk 판단 근거**
- Reflexion 기록은 ValidationOrchestrator 경로에 묶여 있고, Stage4 실경로는 ManuscriptValidator 중심이라 데이터 유입 수준이 실행 모드에 따라 달라질 수 있다.
- 설계 의도(교차 단계 공유 메모리)일 가능성이 있어 확정 버그가 아닌 Risk로 분류.

## [FP] 오탐 목록

### [FP-1] TF-5 R30 `_failures` 무한 증가 미패치
- **판정**: 오탐
- **수동 근거**:
  - `modules/core/adaptive_retry.py:556`~`modules/core/adaptive_retry.py:559` 에피소드별 `max_history` 슬라이싱 적용
  - `modules/core/adaptive_retry.py:560`~`modules/core/adaptive_retry.py:564` 에피소드 키 상한(50개) 적용

### [FP-2] Backoff `2**n` 오버플로/무한증가 위험
- **판정**: 오탐
- **수동 근거**:
  - `modules/core/adaptive_retry.py:381`~`modules/core/adaptive_retry.py:392` 쿼터 전략은 고정 대기(30초)
  - 지수 연산 기반 backoff 경로가 현재 구현에 존재하지 않음

### [FP-3] `_quota_exhausted_models` 경쟁 상태
- **판정**: 오탐
- **수동 근거**:
  - `modules/domain/agents/base_agent.py:137` (`_quota_lock`)
  - `modules/domain/agents/base_agent.py:328`~`modules/domain/agents/base_agent.py:329` 읽기 잠금
  - `modules/domain/agents/base_agent.py:518`~`modules/domain/agents/base_agent.py:520` 쓰기 잠금

### [FP-4] FailureLearner 세션 재시작 시 비영속
- **판정**: 오탐
- **수동 근거**:
  - 로드: `main_a.py:1614`~`main_a.py:1619`
  - 저장: `main_a.py:2136`~`main_a.py:2142`
  - Stage4 후 저장 보강: `modules/core/stage4_post_processor.py:272`~`modules/core/stage4_post_processor.py:274`

## TF-5 R30 패치 확인 (_failures 상한)
- 확인 결과: **패치 반영됨**
- 증거:
  - `modules/core/adaptive_retry.py:557`~`modules/core/adaptive_retry.py:559` (에피소드별 리스트 상한)
  - `modules/core/adaptive_retry.py:561`~`modules/core/adaptive_retry.py:564` (에피소드 키 상한)

## 피드백 루프 완결성 다이어그램

```text
Stage4 REJECT
  ├─ 현재 경로: Director feedback 문자열 생성
  │   └─ 다음 라운드 regenerate/patch 호출
  ├─ 현재 경로: PassRateMonitor.record_attempt(stage=4)
  │   └─ 종료 시 요약/경고 출력 (advisory)
  └─ 누락 경로: AdaptiveRetryManager.record_failure / get_injection_prompt
      누락 경로: FailureLearner.record_failure(stage=4)

FailureLearner
  ├─ 입력: Stage2 Validation 실패(연결됨)
  ├─ 소비: DynamicPromptWeighter(연결됨)
  └─ 결과: Stage4에도 주입되지만 Stage4 실패 자체는 환류 누락
```

## 요약 테이블

| 심각도 | 건수 | 항목 |
|---|---:|---|
| HIGH | 2 | `TF-7-I-1`, `TF-7-I-2` |
| MEDIUM | 1 | `TF-7-I-3` |
| Risk | 1 | `TF-7-I-R1` |
| FP | 4 | `FP-1~4` |
