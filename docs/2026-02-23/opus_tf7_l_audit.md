# TF-7-L 감사 보고서: Quality Dashboard / Metrics / Pass Rate

## 감사 파일 목록
- `modules/core/quality_dashboard.py`
- `modules/core/stage4_post_processor.py`
- `modules/core/stage2_finalizer.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/metrics_collector.py`
- `modules/core/pass_rate_monitor.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage2_validation_pipeline.py`
- `modules/core/stage2_preflight.py`
- `modules/core/stage2_context.py`
- `modules/core/stage4_context.py`
- `modules/core/feedback_system.py`
- `modules/domain/agents/base_agent.py`
- `main_a.py`

## TF-5 L-1 조치 확인 결과 (YES/NO + 증거 줄번호)
| 점검 항목 | 결과 | 근거 |
|---|---|---|
| Stage4 PASS 시 `quality_dashboard.record_validation(stage=4, ...)` 호출 | YES | `modules/core/stage4_post_processor.py:578`, `modules/core/stage4_post_processor.py:581` |
| Stage4 REJECT 시 `quality_dashboard.record_validation(stage=4, ...)` 호출 | NO | Stage4 REJECT 경로는 `PassRateMonitor.record_attempt`만 호출: `modules/core/stage4_interview_round.py:887`, `modules/core/stage4_interview_round.py:950`; Stage4 대시보드 기록은 PASS 처리 블록에만 존재: `modules/core/stage4_post_processor.py:571`, `modules/core/stage4_post_processor.py:578` |

## 발견 이슈 (총 3건)

### [TF-7-L-1] Stage4 REJECT가 QualityDashboard에 누락되어 Stage4 pass_rate가 편향됨 (HIGH)
**증거 파일/라인**
- `modules/core/quality_dashboard.py:76`, `modules/core/quality_dashboard.py:79`, `modules/core/quality_dashboard.py:216`
- `modules/core/stage4_interview_round.py:887`, `modules/core/stage4_interview_round.py:950`
- `modules/core/stage4_orchestrator.py:500`, `modules/core/stage4_orchestrator.py:553`
- `modules/core/stage4_post_processor.py:578`, `modules/core/stage4_post_processor.py:580`

**수동 근거**
- 대시보드는 `decision` 값으로 stage별 `pass/reject`를 집계한다.
- Stage4 REJECT/EMPTY는 면담 라운드에서 `pass_rate_monitor.record_attempt(success=False)`로만 기록된다.
- `quality_dashboard.record_validation(stage=4, ...)`는 PASS 후처리(`process_pass_result`)에서만 실행된다.

**bug-vs-intent 판단**
- Stage2는 PASS/REJECT를 모두 대시보드에 기록한다(`modules/core/stage2_finalizer.py:572`, `modules/core/stage2_finalizer.py:657`).
- 동일한 품질 대시보드 계약에서 Stage4만 REJECT가 빠져 있어 통계 일관성이 깨진다.

---

### [TF-7-L-2] PassRateMonitor 경보 체인이 미연동되어 경보가 소비되지 않음 (MEDIUM)
**증거 파일/라인**
- `modules/core/pass_rate_monitor.py:418`, `modules/core/pass_rate_monitor.py:448`
- `modules/core/stage2_validation_pipeline.py:438`
- `modules/core/stage2_finalizer.py:556`, `modules/core/stage2_finalizer.py:614`
- `modules/core/stage4_interview_round.py:950`
- `main_a.py:2086`
- `modules/core/quality_dashboard.py:66`, `modules/core/quality_dashboard.py:85`

**수동 근거**
- `check_alerts()`는 하락 경보를 문자열 리스트로 생성해 반환한다.
- 실제 호출부는 `record_attempt(...)`와 `save()` 중심이며, `check_alerts()` 소비 지점이 없다.
- QualityDashboard의 저장 레코드 타입은 `validation/hud_anomaly/blueprint_coverage`만 처리하며 pass-rate 경보 입력 타입이 없다.

**bug-vs-intent 판단**
- 모니터의 핵심 기능(경보 생성)이 실행 경로에서 빠져 피드백 루프가 끊긴 상태다.
- 특히 TF-7-L 목표(품질/모니터/경보 연동 점검) 관점에서 기능 미배선으로 판단 가능하다.

---

### [TF-7-L-R1] Stage3는 QualityDashboard 계약(2/3/4 stage 집계) 대비 기록 경로가 없음 (MEDIUM, Risk)
**증거 파일/라인**
- `modules/core/quality_dashboard.py:113`, `modules/core/quality_dashboard.py:216`
- `modules/core/stage3_orchestrator.py:603`, `modules/core/stage3_orchestrator.py:643`
- `modules/core/stage2_finalizer.py:572`, `modules/core/stage4_post_processor.py:578`

**수동 근거**
- 대시보드 시그니처/주석은 Stage 2/3/4를 전제로 한다.
- Stage3 오케스트레이터는 성공/실패를 `audit_event`와 `save_cost_record`에 기록하지만 대시보드 기록은 없다.
- 현재 대시보드 호출은 Stage2/Stage4에만 존재한다.

**bug-vs-intent 판단**
- Stage3 제외가 의도일 수 있어 즉시 Bug로 단정하기보다 Risk로 분류한다.
- 다만 Stage별 일관 통계가 필요하다면 누락된 계측 포인트다.

## 피드백 루프 완결성 다이어그램 (구현 여부 표기)
```text
Stage4 면담 결과
  ├─ PASS
  │   └─ stage4_post_processor.process_pass_result
  │       └─ quality_dashboard.record_validation(stage=4, PASS)          [YES]
  └─ REJECT/EMPTY
      └─ stage4_interview_round._record_s4_attempt
          └─ pass_rate_monitor.record_attempt(stage=4, success=False)    [YES]
          └─ quality_dashboard.record_validation(stage=4, REJECT)        [NO]

PassRateMonitor 데이터
  ├─ get_arc_difficulty()
  │   └─ stage2_preflight -> feedback_system.generate_reverse_feedback_stage4_to_2
  │       └─ Stage2 context 주입                                       [YES]
  └─ check_alerts()
      └─ quality_dashboard / director_ensemble / DB 영속               [NO]

QualityDashboard 분석
  ├─ detect_score_regression(stage=4) -> Stage4 UI warning              [YES]
  └─ detect_quality_drift(stage=4) -> 종료 시 콘솔 advisory             [YES]
```

## [FP] 오탐 목록

### [FP-1] `metrics_collector`와 `quality_dashboard`가 동일 이벤트를 중복 기록한다
- **판정**: 오탐
- **수동 근거**:
  - `metrics_collector`는 에이전트 API 호출 비용/토큰/지연 중심이다 (`modules/core/metrics_collector.py:139`, `modules/core/metrics_collector.py:226`, `modules/core/metrics_collector.py:429`).
  - `quality_dashboard`는 validation decision/score 중심이다 (`modules/core/quality_dashboard.py:106`, `modules/core/quality_dashboard.py:120`).
  - 호출부도 분리되어 있다: `modules/domain/agents/base_agent.py:387`, `modules/domain/agents/base_agent.py:640` vs `modules/core/stage2_finalizer.py:572`, `modules/core/stage4_post_processor.py:578`.

### [FP-2] PassRateMonitor 전체가 dead metric이다
- **판정**: 오탐
- **수동 근거**:
  - Stage4 시도 결과는 실제로 누적된다 (`modules/core/stage4_interview_round.py:950`).
  - 누적된 지표는 Stage2 프리플라이트의 역피드백 입력으로 사용된다 (`modules/core/stage2_preflight.py:516`, `modules/core/feedback_system.py:667`).

## 요약 테이블
| 분류 | 건수 | 항목 |
|---|---:|---|
| 확정 BUG | 2 | `TF-7-L-1`, `TF-7-L-2` |
| Risk | 1 | `TF-7-L-R1` |
| FP | 2 | `FP-1`, `FP-2` |
