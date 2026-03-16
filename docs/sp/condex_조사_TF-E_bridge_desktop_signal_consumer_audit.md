# TF-E 조사: bridge/desktop/control-plane 신호 x 소비자 존재 여부

- 특별 오더 메모: FastAPI bridge, run control, desktop UI를 대상으로 했다.
- 판정 기준은 TF-A와 동일하다.

## 요약

- closed: 6
- advisory: 1
- open: 1
- 핵심 결론: 브리지와 데스크탑은 대부분 실제 소비 루프가 있다. 예외는 `control-plane provenance`로, 현재는 쓰기만 있고 런타임 reader를 찾지 못했다.

## 신호별 판정

| 신호 | 생산자 | 소비자 | 실제 영향 | 루프 상태 | 근거 |
| --- | --- | --- | --- | --- | --- |
| run validation result (`INVALID_KEY`, `SUB_KEY_REQUIRED`, `INVALID_SUB_KEY`, `SUB_KEY_NOT_ALLOWED`, `RUN_ALREADY_ACTIVE`) | `validate_run_request()` | `/run` endpoint | 잘못된 key/sub_key 또는 active run이면 즉시 HTTP error로 차단 | closed | `modules/api/run_validator.py:56-95`, `modules/api/bridge_server.py:1494-1497` |
| risk approval verdict (`RISK_APPROVAL_REQUIRED`, `RISK_APPROVAL_EXPIRED`, `RISK_APPROVAL_DUAL_CONTROL_REQUIRED`) | `RiskApprovalGate.validate()` | `/run` endpoint | 위험 key는 approval 없으면 실행 자체가 막힌다 | closed | `modules/api/risk_approval.py:100-180`, `modules/api/bridge_server.py:1499-1503` |
| prompt classification metadata (`input_type`, `step_id`, `default`, `options`, `prompt_text`) | `prompt_classifier.classify()`와 `PromptBroker` payload | desktop prompt dialog | 입력 컴포넌트 종류, 버튼 옵션, default가 UI에 직접 렌더된다 | closed | `modules/api/prompt_classifier.py:86-172`, `modules/api/prompt_broker.py:92-143`, `modules/api/bridge_server.py:1519-1537`, `geuldobi-desktop/src/index.html:6252-6484` |
| quality radar signal stats (`ced`, `ai_slop`, `compression`, `burstiness`, `complexity`) | `db.get_quality_signal_summary()`와 bridge payload | desktop quality radar / result summary signal alerts | 최근 원고 신호가 카드 색상, delta, `signal_alerts`로 표시된다 | closed | `modules/core/db_manager.py:3041-3083`, `modules/api/bridge_server.py:833-843`, `modules/api/bridge_server.py:891-943`, `modules/api/bridge_server.py:1392-1423`, `geuldobi-desktop/src/index.html:4269-4325`, `geuldobi-desktop/src/index.html:4328-4389` |
| retrieval summary (`stage_rows`, `top_warnings`, `recent`) | `QualityDashboard.get_retrieval_summary()`와 bridge payload | desktop retrieval inspector | Stage별 summary slot 포함률, relation slice 포함률, 반복 warning이 UI에 표시된다 | closed | `modules/core/quality_dashboard.py:308-373`, `modules/api/bridge_server.py:1359-1360`, `geuldobi-desktop/src/index.html:4142-4235` |
| calibration health counts (`retrieval_observation_rows`, `quality_signal_rows`, `manual_review_rows`) | sidecar health inspection + `_build_calibration_payload()` | desktop calibration desk `next_step` | 관측 부족/수기 review 부족 여부가 다음 액션 문장으로 승격된다 | closed | `modules/core/quality_sidecar_bootstrap.py:132-160`, `modules/api/bridge_server.py:1074-1080`, `modules/api/bridge_server.py:1154-1162`, `geuldobi-desktop/src/index.html:4505-4562` |
| stage stats / failure pattern summary | `dashboard.get_summary()`와 bridge payload | desktop failure watch panel | Stage별 pass rate, 평균 score, top failure type이 운영 패널에 표시된다 | advisory | `modules/core/quality_dashboard.py:242-306`, `modules/api/bridge_server.py:1348-1360`, `geuldobi-desktop/src/index.html:4437-4497` |
| control-plane provenance (`risk_key`, `approval_id`, `run_id`, `mode`) | `_write_control_plane_provenance()` | 현재 런타임 reader 미발견 | JSONL 기록은 남지만 현재 bridge/desktop/core 코드에서 읽는 지점을 찾지 못했다 | open | `modules/api/bridge_server.py:185-208`, `modules/api/bridge_server.py:1566-1577`, `rg --glob '!docs/**' \"control-plane-provenance\"` 결과 기준 |

## TF-E 판단

- `/run` 제어선은 validation과 risk approval이 모두 명시적 hard gate로 닫혀 있다.
- desktop UI는 prompt metadata, quality radar, retrieval summary, calibration next-step을 실제로 렌더한다.
- `control-plane provenance`는 현재 추적용 기록으로는 남지만, production reader가 없어 열린 루프다.

## 3pass 감리

- pass1: bridge payload 생산과 desktop render 지점을 짝지었다.
- pass2: payload만 만들고 UI가 읽지 않는 필드는 소비자로 과대판정하지 않도록 제거했다.
- pass3: `control-plane provenance`는 테스트 호출을 제외하고 production reader가 없는지 다시 확인했다.

최종 confidence: 0.96
