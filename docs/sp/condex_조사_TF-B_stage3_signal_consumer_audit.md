# TF-B 조사: Stage 3 신호 x 소비자 존재 여부

- 특별 오더 메모: Stage 3 blueprinting 구간만 분리해서 현재 런타임 코드 기준으로 조사했다.
- 판정 기준은 TF-A와 동일하다.

## 요약

- closed: 4
- advisory: 1
- open: 0
- 핵심 결론: Stage 3의 핵심 신호는 Stage 4 조기 경고, proof/audit 정합성, 운영 통계로 이어진다. 완전히 끊긴 루프는 찾지 못했다.

## 신호별 판정

| 신호 | 생산자 | 소비자 | 실제 영향 | 루프 상태 | 근거 |
| --- | --- | --- | --- | --- | --- |
| Stage 3 retrieval coverage bundle | Stage 3 `_record_retrieval_observation()` | `QualityDashboard.get_retrieval_summary()`와 bridge calibration | retrieval warning 반복 여부가 운영자의 calibration `next_step`에 반영된다 | advisory | `modules/core/stage3_orchestrator.py:447-454`, `modules/core/stage3_orchestrator.py:1234-1261`, `modules/core/quality_dashboard.py:308-373`, `modules/api/bridge_server.py:1074-1080`, `modules/api/bridge_server.py:1422-1429` |
| `quality_risk` / `quality_gate_failed` | Stage 3 success handler가 `_stage3_meta`에 저장 | Stage 4 Director advisory와 V75-D 조기 트리거 | 위험 blueprint면 Stage 4에서 LOGIC_ERROR 1연속만으로도 더 빠른 개입이 걸린다 | closed | `modules/core/stage3_orchestrator.py:1373-1518`, `modules/core/stage4_interview_round.py:1677-1686`, `modules/core/stage4_orchestrator.py:1197-1206` |
| Stage 3 observability flags / advisory flags | `_build_stage3_observability_flags()`와 stage attempt 저장 | session decision log, `save_stage_attempt`, `save_director_selection`, audit proof surface | 단순 저장으로 끝나지 않고 proof/audit 정합성 판단의 입력이 된다 | closed | `modules/core/stage3_orchestrator.py:1375-1490`, `modules/core/services/audit_service.py:226-247`, `modules/api/bridge_server.py:1380-1430` |
| Stage 3 verdict / score | Stage 3 success/failure record | `pass_rate_monitor`, `quality_dashboard`, DB, bridge stage stats | Stage 3 pass rate와 score trend가 운영 대시보드에 반영된다 | closed | `modules/core/stage3_orchestrator.py:1449-1490`, `modules/core/quality_dashboard.py:124-149`, `modules/api/bridge_server.py:1348-1360` |
| Stage 3 `fix_scope`, `fix_scope_reasoning`, `contradictions` | validation 결과에서 `_selection_kwargs`와 advisory로 승격 | `director_selections` 저장 후 audit/proof 정합성 점검 | 자동 분기는 아니지만 rationale 메타데이터와 selection 일관성 감사에 쓰인다 | closed | `modules/core/stage3_orchestrator.py:1819-1827`, `modules/core/stage3_orchestrator.py:1487-1490`, `modules/core/services/audit_service.py:91-110` |

## TF-B 판단

- Stage 3에서 가장 중요한 닫힌 루프는 `quality_risk -> Stage 4 조기 개입`이다.
- retrieval coverage는 존재하지만 현재는 자동 fail-close보다 운영 advisory 성격이 강하다.
- proof/audit surface는 로그 보관이 아니라 later consumer가 실제 존재한다.

## 3pass 감리

- pass1: Stage 3 생산 신호를 retrieval, quality, observability, rationale 4계층으로 나눴다.
- pass2: Stage 4가 실제로 읽는 신호와 proof 계층이 실제로 읽는 신호를 분리해 재검증했다.
- pass3: `advisory`와 `closed` 경계를 다시 점검했고, 테스트 전용 소비자는 제외했다.

최종 confidence: 0.95
