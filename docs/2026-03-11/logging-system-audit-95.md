# 로깅 체계 전수 감사 및 95% 확신도 판정

## 최종 판정

2026-03-11 기준 글도비의 현재 로깅 체계는 `실행 사실`, `시도 이력`, `품질 신호`, `LLM I/O`, `Stage 4 round 단위 결과`를 상당 폭 기록하고 있다. 다만 `REJECT` 또는 `PASS_WITH_FIX` 시점의 원문 산출물(`arc`, `blueprint`, `manuscript`)을 stage별 artifact로 구조화 보존하는 레이어는 현재 없다.

따라서 현재 판정은 아래와 같다.

- 현재 로깅 체계의 실행 관측 가능성: `95%`
- 현재 로깅 체계의 artifact-level 회귀/원인분석 완결성: `미완`
- 결론: `현재 체계는 충분히 많이 기록하지만, REJECT/PASS_WITH_FIX 원문 보존은 개발단계 기본ON으로 별도 추가하는 것이 ROI가 높다`

이 문서의 최종 권고는 다음으로 고정한다.

- `Stage 4 manuscript`: 개발단계 기본ON
- `Stage 3 blueprint`: 개발단계 기본ON
- `Stage 2 arc tactical_doc`: 개발단계 기본ON

## 현재 로깅 자산 지도

| 자산 | taxonomy | 무엇이 기록되는가 | 어디에 남는가 | 어느 Stage까지 덮는가 | 재현/원인분석에 충분한가 | confidence |
| --- | --- | --- | --- | --- | --- | --- |
| 세션 콘솔 로그 | logged but fragmented | 콘솔 출력 기반 단계 진행, 경고, 선택 결과, 종료 통계 | `projects/<name>/logs/session_*.log` | Stage 0~4, 세션 종료까지 | 사람 읽기에는 충분하나 구조화 분석에는 분절적 | 높음 |
| structured session log - LLM I/O | confirmed logged | prompt/response/thinking, model, agent, duration, metadata | `projects/<name>/logs/session/llm_io.jsonl` | Stage 2~4 중심, LLM 호출 전반 | 원문 I/O 포렌식에는 강함. 다만 artifact-level semantics는 부족 | 높음 |
| structured session log - decisions | logged but fragmented | 선택/판정 결과와 일부 메타 | `projects/<name>/logs/session/decisions.jsonl` | Stage 2~4 | lean metadata라 후속 조인 없이 단독 분석은 제한적 | 높음 |
| episode 결과 로그 | confirmed logged | Stage 4 round별 verdict, score, warnings, patch flags, strategy budget/count, reject bucket, round time/token/cost | `projects/<name>/logs/episode_production.jsonl` | Stage 4 | Stage 4 원인분석의 주력 자산으로 충분 | 높음 |
| 품질 로그 | confirmed logged | validation, retrieval_observation, CED/AI slop/noise 등 품질 이벤트 | `projects/<name>/logs/quality_metrics.jsonl` | Stage 2~4 | 품질 신호/경고 패턴 분석에 충분 | 높음 |
| runtime audit event log | logged but fragmented | 런타임 감사 이벤트 스트림 | `projects/<name>/logs/runtime_audit.jsonl` | Stage 2~4 | 존재는 확실하나 세밀한 stage/episode audit은 아직 lean | 중간 |
| runtime audit summary | logged but fragmented | 최신 요약 tag, recent events, counts | `projects/<name>/logs/runtime_audit_summary.json` | 현재는 Stage 4 완료까지 | 세션 완료 지점 추적에는 충분. 세부 원인분석은 보조 수준 | 높음 |
| metrics summary | confirmed logged | 총 호출, 성공률, 토큰, 비용, 모델/에이전트별 요약 | `projects/<name>/logs/metrics/metrics_*.json` | 세션 전체 | 세션 총량 분석에 충분 | 높음 |
| DB - llm_calls | logged but fragmented | 호출별 메타, snippet, 비용/시간 | `project_data.db: llm_calls` | 광범위 | 호출 포렌식은 가능하나 full artifact 복원에는 부족 | 높음 |
| DB - stage_attempts | confirmed logged | stage/ep/arc별 attempt verdict, score, reject reason, fix_scope, duration_ms | `project_data.db: stage_attempts` | Stage 2~4 | attempt 이력 분석엔 충분. 일부 stage에서 duration 분절 존재 | 높음 |
| DB - director_selections | confirmed logged | selection_reason, verdict_reason, firewall metadata, advisory warnings | `project_data.db: director_selections` | Stage 2~4 | verdict reasoning 분석엔 충분. candidate artifact linkage는 부족 | 높음 |

## Pass 1. 실제 기록 범위 감사

### 1. 세션 콘솔 로그

- 분류: `logged but fragmented`
- 근거:
  - `main_a.py`는 세션 종료 시 메트릭/비용/실행시간을 요약 출력한다.
  - `projects/00_test_01/logs/session_20260311_183911.log`에는 Stage 2/3/4 진행, PASS/REJECT, 종료 통계가 남아 있다.
- 평가:
  - 사람 검토에는 강하다.
  - 그러나 JSONL/DB처럼 구조화되지 않아 자동 join과 회귀 대조에는 보조 자산이다.

### 2. structured session log (`llm_io.jsonl`, `decisions.jsonl`)

- 분류:
  - `llm_io.jsonl`: `confirmed logged`
  - `decisions.jsonl`: `logged but fragmented`
- 근거:
  - `modules/core/session_logger.py`는 `log_llm_call()`과 `log_decision()`을 JSONL로 저장한다.
  - `projects/00_test_01/logs/session/llm_io.jsonl`에는 agent/model/prompt/response/thinking이 실제로 남아 있다.
  - `projects/00_test_01/logs/session/decisions.jsonl`에는 결과/점수 중심의 lean decision rows가 남아 있다.
- 평가:
  - `llm_io.jsonl`은 원문 I/O 포렌식 자산으로 강력하다.
  - 다만 특정 round의 “선택된 후보 원문”을 안정적으로 찾는 구조화 artifact store는 아니다.

### 3. episode 결과 로그 (`episode_production.jsonl`)

- 분류: `confirmed logged`
- 근거:
  - `stage4_interview_round.py`는 round별로 `episode_production.jsonl`을 append한다.
  - `projects/00_test_01/logs/episode_production.jsonl`에는 아래가 실제 저장된다.
    - `verdict`, `score`, `strategy`, `duration_ms`
    - `round_total_calls`, `round_total_tokens`, `round_total_cost_usd`, `round_model_breakdown`
    - `flags.strategy_budget`, `flags.strategy_count`, `flags.reject_bucket`
    - `warnings`, `score_breakdown`, `open_review`
- 평가:
  - Stage 4 retry/cost/quality 원인분석의 주력 로그로 충분하다.
  - 다만 여전히 “해당 row가 가리키는 manuscript full text snapshot”을 직접 담지는 않는다.

### 4. 품질 로그 (`quality_metrics.jsonl`)

- 분류: `confirmed logged`
- 근거:
  - `projects/00_test_01/logs/quality_metrics.jsonl`에 validation, retrieval_observation, CED/AI slop/noise 유형이 남아 있다.
- 평가:
  - 품질/경고 패턴 비교에는 충분하다.
  - artifact 원문과 직접 결합하는 스키마는 없다.

### 5. runtime audit (`runtime_audit*.json*`)

- 분류: `logged but fragmented`
- 근거:
  - `AuditService`가 `runtime_audit.jsonl`과 `runtime_audit_summary.json`을 생성한다.
  - `projects/00_test_01/logs/runtime_audit_summary.json`은 `stage4_complete` tag까지 기록한다.
- 평가:
  - Stage 완료 지점 기록은 현재 닫혔다.
  - 그러나 event taxonomy는 여전히 lean하고, episode/round 중심 원인분석을 단독으로 감당하진 못한다.

### 6. DB 로깅 (`llm_calls`, `stage_attempts`, `director_selections`)

- `llm_calls`: `logged but fragmented`
  - snippet 중심이라 원문 artifact 저장 레이어로 보기 어렵다.
- `stage_attempts`: `confirmed logged`
  - attempt, verdict, reject_reason, fix_scope, model, duration_ms가 남는다.
  - 다만 `00_test_01` sample에서 일부 Stage 3 row는 `duration_ms`가 비어 있어 분절이 있다.
- `director_selections`: `confirmed logged`
  - selection_reason, verdict_reason, advisory_warnings, firewall metadata가 남는다.
  - 다만 candidate artifact와의 stable linkage가 없다.

## Pass 2. 누락/분절 감사

### 1. Stage 2 `REJECT` arc 후보 원문 보존

- 판정: `missing`
- 근거:
  - 현재 코드는 final arc 산출물/DB 메타는 남기지만, `REJECT` 후보 `tactical_doc` full text를 stage별 artifact로 구조 저장하지 않는다.
- 영향:
  - Arc 설계 실패 원인, PASS_WITH_FIX 전 상태, 후보 간 차이를 후속 회귀에서 직접 비교하기 어렵다.

### 2. Stage 3 `REJECT/PASS_WITH_FIX` blueprint 후보/이전 버전 보존

- 판정: `missing`
- 근거:
  - blueprint 최종 저장본은 남지만, `PASS_WITH_FIX before patch`, `rejected_best`, 후보군 snapshot을 구조화 artifact로 남기는 레이어는 없다.
- 영향:
  - blueprint drift, candidate 간 비교, patch 전후 변화 추적이 어렵다.

### 3. Stage 4 `REJECT/PASS_WITH_FIX` manuscript 원문 보존

- 판정: `missing`
- 근거:
  - `episode_production.jsonl`, `llm_io.jsonl`, `director_selections`는 남지만, round별 선택 manuscript 원문을 `selected_before_fix`, `pass_with_fix_before_patch`, `rejected_best`, `patched_after_fix` 같은 식으로 구조 저장하지 않는다.
- 영향:
  - 가장 ROI 높은 원인분석 자산이 현재 직접 보존되지 않는다.

### 4. `previous_attempt` 메타와 실제 원문/후보 연결

- 판정: `logged but fragmented`
- 근거:
  - `stage4_interview_round.py`는 `selected_strategy_key`, `selection_reason`, `verdict_reason`, `reject_bucket` 등 메타를 유지한다.
  - 하지만 DB/JSONL 어디에도 원문 snapshot path/hash/candidate_key를 일관되게 연결하는 stable linkage가 없다.
- 영향:
  - reasoning은 남아도 “어떤 텍스트에 대한 reasoning인가”를 후속에 완전히 닫기 어렵다.

### 5. 로그/DB/JSONL 간 조인 가능성

- 판정: `logged but fragmented`
- 근거:
  - `ep`, `round`, `attempt_num`, `stage`, `session_id`로 느슨한 조인은 가능하다.
  - 그러나 `candidate_key`나 content hash가 없어 round 내부 후보 수준까지 deterministic join은 어렵다.
- 영향:
  - 사람이 충분히 시간을 들이면 복원 가능하지만, 자동 회귀/학습데이터 파이프라인으로는 약하다.

### 6. `session/llm_io.jsonl`의 분절 문제

- 판정: `logged but fragmented`
- 근거:
  - 존재 자체는 강력하다.
  - 하지만 후속 분석에서 “이 응답이 ep3 round2 selected_before_fix인가”를 바로 알기 어렵다.
- 영향:
  - raw I/O는 많지만 semantic artifact retention은 아직 아니다.

### 누락/분절 결론

현재 체계의 핵심 약점은 “로그가 적어서”가 아니라 “로그와 원문 artifact가 구조적으로 엮여 있지 않아서”다. 즉, 문제는 관측량 부족보다 `artifact linkage`와 `pre-fix snapshot retention` 부재에 더 가깝다.

## Pass 3. ROI 및 권장 정책

### ROI 판단 기준

본 문서는 reject/PASS_WITH_FIX 원문 보존 ROI를 아래 기준으로 평가한다.

- 원인분석 직접성
- 회귀 비교 가능성
- DPO/학습 데이터 전환 가능성
- 스토리지 비용
- 민감도/운영 부담

### Stage별 ROI 판정

| Stage | 현재 상태 | taxonomy | ROI 판단 | 권장 |
| --- | --- | --- | --- | --- |
| Stage 4 manuscript | final draft와 round 메타는 남음, pre-fix/rejected text는 구조 저장 없음 | roi candidate | 가장 높음. retry/patch/firewall 분석, 수동 판독, 학습 데이터 전환에 직결 | 개발단계 기본ON |
| Stage 3 blueprint | 최종 blueprint는 남음, 후보군/patch 전 텍스트는 없음 | roi candidate | 높음. continuity drift, ending hook, structure regression 분석에 유효 | 개발단계 기본ON |
| Stage 2 arc tactical_doc | 최종 arc는 남음, reject/pass_with_fix 후보 원문 없음 | roi candidate | 중상. Stage 2 실패율과 장기 구조 drift 분석에 가치 있음 | 개발단계 기본ON |

### 권장 저장 정책 초안

- 저장 위치:
  - `projects/<name>/logs/artifacts/`
- 저장 단위:
  - `stage`, `ep/arc`, `round`, `verdict`, `candidate_key`
- 기본 저장 대상:
  - `selected_before_fix`
  - `rejected_best`
  - `pass_with_fix_before_patch`
  - `patched_after_fix`

예시 경로:

```text
projects/<name>/logs/artifacts/stage4/ep_0003/round_02/pass_with_fix_before_patch__tension.txt
projects/<name>/logs/artifacts/stage3/ep_0004/round_01/rejected_best__dialogue_focused.txt
projects/<name>/logs/artifacts/stage2/arc_001/round_03/patched_after_fix__creative.json
```

### 최종 정책 권고

- 개발 단계:
  - `full text artifact retention` 기본ON 권고
- 운영 단계:
  - `opt-in` 또는 `selected + rejected_best only` 축소 권고

이 판단의 이유는 다음과 같다.

- 현재 글도비는 아직 개발/검증 단계 성격이 강하다.
- retry, PASS_WITH_FIX, firewall, post-select conflict를 많이 다룬다.
- 지금은 원문 snapshot이 남을수록 회귀 속도와 원인분석 정확도가 높아진다.
- 저장 비용은 텍스트 기반 기준 상대적으로 작고, ROI가 높다.

## 95% 확신도 판정

현재 로깅 체계 감사의 확신도는 `95%`로 판정한다.

그 이유는 아래와 같다.

- 코드 측면:
  - `SessionLogger`, `MetricsCollector`, `PassRateMonitor`, `AuditService`, `stage4_interview_round`, `db_manager` 경로를 실제로 대조했다.
- 런타임 측면:
  - `00_test_01`의 실제 로그/JSONL/DB를 대조해 존재 여부와 구조를 확인했다.
- 결론 측면:
  - 무엇이 `confirmed logged`인지
  - 무엇이 `logged but fragmented`인지
  - 무엇이 실제 `missing`인지
  - 무엇이 `roi candidate`인지
  를 Stage 2/3/4 기준으로 닫았다.

남은 5% 불확실성은 아래 3개로 제한한다.

- artifact retention 구현 시 실제 저장량 증가 추정
- 운영단계에서 어느 수준까지 축소할지에 대한 정책 세분화
- `candidate_key` / content hash / path linkage schema의 최종 설계

## 즉시 구현 후보

1. Stage 2/3/4 공통 artifact retention 레이어 추가
   - `REJECT`, `PASS_WITH_FIX`, `patched_after_fix` 원문 저장

2. `candidate_key` / content hash / artifact path를 `director_selections`, `stage_attempts`, `episode_production.jsonl`에 공통 주입
   - verdict와 artifact의 deterministic join 확보

3. Stage 3 `stage_attempts.duration_ms` 누락 보정
   - Stage 2/4와 동일한 attempt-level timing completeness 확보

4. runtime audit event taxonomy 확장
   - Stage 4 episode/round 단위 핵심 이벤트를 summary에서 더 명확히 읽게 개선

5. 분석 친화 view/index 설계
   - `llm_io.jsonl`, `episode_production.jsonl`, `stage_attempts`, `director_selections`를 같은 key로 조인 가능하게 만들기

## 참고 근거

- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py)
- [session_logger.py](C:/Users/User/Desktop/글도비/modules/core/session_logger.py)
- [metrics_collector.py](C:/Users/User/Desktop/글도비/modules/core/metrics_collector.py)
- [pass_rate_monitor.py](C:/Users/User/Desktop/글도비/modules/core/pass_rate_monitor.py)
- [audit_service.py](C:/Users/User/Desktop/글도비/modules/core/services/audit_service.py)
- [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py)
- [stage4_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py)
- [db_manager.py](C:/Users/User/Desktop/글도비/modules/core/db_manager.py)
- [session_20260311_183911.log](C:/Users/User/Desktop/글도비/projects/00_test_01/logs/session_20260311_183911.log)
- [llm_io.jsonl](C:/Users/User/Desktop/글도비/projects/00_test_01/logs/session/llm_io.jsonl)
- [episode_production.jsonl](C:/Users/User/Desktop/글도비/projects/00_test_01/logs/episode_production.jsonl)
- [quality_metrics.jsonl](C:/Users/User/Desktop/글도비/projects/00_test_01/logs/quality_metrics.jsonl)
- [runtime_audit.jsonl](C:/Users/User/Desktop/글도비/projects/00_test_01/logs/runtime_audit.jsonl)
- [runtime_audit_summary.json](C:/Users/User/Desktop/글도비/projects/00_test_01/logs/runtime_audit_summary.json)
- [pass_rate_monitor.json](C:/Users/User/Desktop/글도비/projects/00_test_01/logs/pass_rate_monitor.json)
- [project_data.db](C:/Users/User/Desktop/글도비/projects/00_test_01/project_data.db)
- [project_data.db](C:/Users/User/Desktop/글도비/projects/00_test_00/project_data.db)

최종 상태: 2026-03-11 기준 로깅 체계 감사 확정본  
감리 수준: 조사 3회 + 문서 3-pass 재감리 완료  
확신도: 95%
