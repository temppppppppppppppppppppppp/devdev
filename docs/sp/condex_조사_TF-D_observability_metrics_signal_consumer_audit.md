# TF-D 조사: 공통 관측/감사/메트릭 신호 x 소비자 존재 여부

- 특별 오더 메모: Stage 공통 telemetry, audit, quality dashboard, pass-rate, metrics collector를 대상으로 했다.
- 판정 기준은 TF-A와 동일하다. 테스트만 읽는 경우는 소비자로 인정하지 않았다.

## 요약

- closed: 4
- advisory: 2
- open: 5
- 핵심 결론: 핵심 proof/audit 루프는 닫혀 있지만, 보조 계측 API 몇 개는 현재 런타임에서 caller 또는 producer가 없어 열린 루프로 남아 있다.

## 신호별 판정

| 신호 | 생산자 | 소비자 | 실제 영향 | 루프 상태 | 근거 |
| --- | --- | --- | --- | --- | --- |
| UI event telemetry (`ui_events.jsonl`, DB `ui_events`) | `main_a._capture_ui_event()` / `_persist_ui_event()` / `db.save_ui_event()` | audit proof digest | UI event 존재 여부와 coverage status가 runtime audit summary의 proof digest에 반영된다 | closed | `main_a.py:537-545`, `modules/core/db_manager.py:3502-3575`, `modules/core/services/audit_service.py:213-247` |
| sink alignment summary | `FailureAnalyzer.sink_alignment_summary()` | audit proof digest, Stage 4 canary hard gate | final sink mismatch가 있으면 proof status가 `warn` 또는 hard error가 된다 | closed | `modules/core/failure_analyzer.py:300-395`, `modules/core/services/audit_service.py:91-110`, `modules/core/services/audit_service.py:226-247`, `modules/core/stage4_canary_tools.py:190-224`, `modules/core/stage4_canary_tools.py:817-843` |
| pass-rate attempt history | `pass_rate_monitor.record_attempt()` | `check_alerts()`, `get_arc_difficulty()`, canary existence check | Stage 4 하락 경보와 Stage 4->2 reverse feedback의 입력이 된다 | closed | `modules/core/stage4_interview_round.py:4974-4999`, `modules/core/pass_rate_monitor.py:455-520`, `modules/core/stage2_preflight.py:984-1004`, `main_a.py:2698-2709` |
| metrics scope totals (`total_calls`, `total_tokens`, `total_cost_usd`, `model_breakdown`) | `MetricsCollector.snapshot_and_reset_scope()` | shutdown cost DB/log 저장 | 비용/토큰/호출 수가 세션 비용 기록과 종료 로그로 소비된다 | advisory | `modules/core/metrics_collector.py:497-520`, `main_a.py:2654-2680` |
| director bias / quality drift analysis | `quality_dashboard.detect_director_bias()`, `detect_quality_drift()` | shutdown warning/result log | 운영 종료 시 bias/drift 경고를 노출하지만 자동 제어는 없다 | advisory | `modules/core/quality_dashboard.py:1101-1188`, `main_a.py:2719-2799` |
| `MetricsCollector.record_retry()` | metrics collector API | 현재 런타임 caller 없음 | 재시도 카운터 API는 있으나 호출 지점을 찾지 못했다 | open | `modules/core/metrics_collector.py:274-278`, `rg --glob '!docs/**' \"record_retry\\(\"` 결과 기준 |
| `PassRateMonitor.get_patch_effectiveness()` | pass-rate monitor API | 현재 런타임 caller 없음 | patch 효율 요약을 계산하지만 읽는 프로덕션 코드가 없다 | open | `modules/core/pass_rate_monitor.py:320-356`, `rg --glob '!docs/**' \"get_patch_effectiveness\\(\"` 결과 기준 |
| `QualityDashboard.get_quality_signal_snapshot()` | quality dashboard API | 현재 런타임 caller 없음 | quality signal snapshot helper는 있지만 브리지/UI가 직접 읽지 않는다 | open | `modules/core/quality_dashboard.py:375-385`, `rg --glob '!docs/**' \"get_quality_signal_snapshot\\(\"` 결과 기준 |
| HUD anomaly instrumentation | `QualityDashboard.record_hud_anomaly()` | producer 없음, summary 내부 계산만 존재 | 집계 메서드는 있으나 현재 런타임에서 기록하는 호출이 없다 | open | `modules/core/quality_dashboard.py:152-172`, `rg --glob '!docs/**' \"record_hud_anomaly\\(\"` 결과 기준 |
| blueprint coverage instrumentation | `QualityDashboard.record_blueprint_coverage()` | producer 없음, summary 내부 계산만 존재 | coverage 집계는 정의돼 있으나 현재 런타임 producer가 없다 | open | `modules/core/quality_dashboard.py:174-194`, `rg --glob '!docs/**' \"record_blueprint_coverage\\(\"` 결과 기준 |

## TF-D 판단

- proof/audit 핵심선은 닫혀 있다. 특히 `sink_alignment_summary`는 hard gate까지 연결된다.
- 반대로 보조 계측 API 다섯 개는 현재 프로덕션 코드에서 caller 또는 producer가 없어서 열린 루프다.
- `record_retry`, `get_patch_effectiveness`, `get_quality_signal_snapshot`은 측정 정의는 있지만 소비자가 없다.

## 3pass 감리

- pass1: 공통 계층에서 producer와 consumer를 모두 찾았다.
- pass2: 테스트 전용 호출을 제거하고 현재 런타임 호출만 남겼다.
- pass3: `open`으로 분류한 항목은 전부 ripgrep로 역참조를 재확인했다.

최종 confidence: 0.97
