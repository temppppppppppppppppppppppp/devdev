# TF-C 조사: Stage 4 신호 x 소비자 존재 여부

- 특별 오더 메모: Stage 4 manuscript loop, Director round, post-processor만 대상으로 했다.
- 판정 기준은 TF-A와 동일하다.

## 요약

- closed: 6
- advisory: 3
- open: 0
- 핵심 결론: Stage 4는 가장 강하게 닫힌 루프를 가진 구간이다. 점수/모순/버킷/quality_risk 신호가 실제 patch, blueprint regeneration, Director 경고로 이어진다.

## 신호별 판정

| 신호 | 생산자 | 소비자 | 실제 영향 | 루프 상태 | 근거 |
| --- | --- | --- | --- | --- | --- |
| `_score_history`와 plateau/decline 감지 | Stage 4 orchestrator | `director_feedback`와 `previous_attempt.fix_scope_reasoning` | 반복 하락/plateau가 감지되면 즉시 feedback 문구가 강화된다 | closed | `modules/core/stage4_orchestrator.py:1099-1129` |
| `_logic_error_streak` + `_stage3_meta.quality_risk` | Stage 4 orchestrator | V75-D inplace blueprint patch 분기 | `quality_risk=True`면 streak threshold가 2에서 1로 낮아진다 | closed | `modules/core/stage4_orchestrator.py:1131-1216`, `modules/core/stage3_orchestrator.py:1513-1518` |
| `_bucket_streak` | Stage 4 orchestrator | TF-29 blueprint/arc 재검토 advisory | 동일 reject bucket이 3연속이면 기존 루프를 유지하지 않고 구조 문제로 승격한다 | closed | `modules/core/stage4_orchestrator.py:1137-1163` |
| `_contradiction_type_streak` + `_logic_error_streak` | Stage 4 orchestrator | A-4 Arc 구조 진단 advisory | 동일 모순 유형이 반복되면 Writer 문제가 아니라 Arc 구조 문제로 재해석한다 | closed | `modules/core/stage4_orchestrator.py:1164-1195` |
| `fix_scope` 전략별 합격률 | `db.get_fix_scope_stats()` | Director mandatory context `[A-3]` 주입 | 전략별 성공 이력이 다음 round의 Director 판단 자료로 직접 들어간다 | closed | `modules/core/db_manager.py:3577-3588`, `modules/core/stage4_interview_round.py:1883-1900` |
| inplace 성공률 (`_get_inplace_success_rate`) | `db.get_fix_scope_stats()` 집계 | Stage 4 로그만 기록 | 현재는 진단 로그만 남고 분기에는 직접 쓰지 않는다 | advisory | `modules/core/stage4_interview_round.py:108-130`, `modules/core/stage4_interview_round.py:3033-3039`, `modules/core/stage4_interview_round.py:3757-3763` |
| Stage 4 verdict/score/reject metadata | `record_validation`, `record_attempt`, `save_stage_attempt` | quality dashboard, pass-rate, failure watch | Stage 4 REJECT/PASS가 이후 trend, failure pattern, pass-rate에 누적된다 | closed | `modules/core/stage4_interview_round.py:1542-1555`, `modules/core/stage4_interview_round.py:3650-3664`, `modules/core/stage4_interview_round.py:4974-5039` |
| Final manuscript quality signal bundle (`ced`, `ai_slop`, `compression`, `burstiness`, `complexity`) | `compute_quality_signal_bundle()`와 post-processor 저장 | bridge quality radar, result summary, compare rows | 최근 원고의 상대 신호가 UI 카드와 `signal_alerts`로 올라온다 | closed | `modules/core/quality_signal_metrics.py:171-242`, `modules/core/stage4_post_processor.py:1299-1308`, `modules/core/db_manager.py:2910-3083`, `modules/api/bridge_server.py:833-843`, `modules/api/bridge_server.py:891-943` |
| score regression (`detect_score_regression`) | quality dashboard | Stage 4 UI/log warning | 회귀를 잡아도 현재는 경고만 하고 자동 retry는 없다 | advisory | `modules/core/stage4_post_processor.py:1308-1321`, `modules/core/quality_dashboard.py:870-971` |
| pass-rate alerts (`check_alerts`) | pass-rate monitor | Stage 4 warning log | 하락 경보를 뽑지만 현재는 로그 경고까지만 이어진다 | advisory | `modules/core/stage4_orchestrator.py:911-919`, `modules/core/pass_rate_monitor.py:455-485` |

## TF-C 판단

- Stage 4는 `측정 -> 재해석 -> 재시도 전략 변경`이 실제로 구현된 구간이다.
- `quality_risk`, `logic_error_streak`, `bucket_streak`는 모두 명확한 소비자를 가진다.
- 다만 `detect_score_regression`, `check_alerts`, `_get_inplace_success_rate`는 아직 자동 분기보다 경고/진단 성격이 강하다.

## 3pass 감리

- pass1: retry loop를 중심으로 streak, risk, verdict, signal bundle을 분리했다.
- pass2: advisory-only 신호를 강제 closed로 과대평가하지 않도록 regression/alert/inplace-success-rate를 재분류했다.
- pass3: Stage 4 문서가 bridge/UI 소비와 core retry 소비를 모두 포함하는지 다시 확인했다.

최종 confidence: 0.97
