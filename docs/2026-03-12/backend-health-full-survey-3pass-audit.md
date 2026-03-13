# Backend Health Full Survey 3-Pass Audit

- 작성일: 2026-03-12
- 대상 SSOT: [backend-health-full-survey-execution-ssot.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/backend-health-full-survey-execution-ssot.md)
- 조사 모드: static / read-only
- 최종 상태: closed
- 최종 확신도: `95%`

## Executive Summary

정적 전수조사 기준에서 현재 백엔드 건강도는 `진입점 붕괴`나 `stage 전체 파손`보다 `계약면 분산`과 `관측 가능성 편차`에 더 민감하다. 핵심 엔트리포인트, Stage 0~4 오케스트레이션, provider/router/telemetry, safe-ops 경로는 대부분 명시적 구조를 갖고 있다. 반면 건강도 위험은 다음 축에 집중된다.

- `PASS_WITH_FIX`와 final selection 의미론을 여러 sink가 동시에 공유해야 하는 구간
- style/work-guard/context 계약이 생성 지점과 소비 지점에 분산된 구조
- environment-driven root resolution과 운영 메뉴가 강력한 대신 drift surface가 되는 구간

즉, 현재 백엔드의 주된 위험은 "`무엇을 할 수 없는가`"보다 "`무엇을 나중에 추적하기 어려운가`"에 가깝다.

## 1. 조사 범위

이번 감리는 아래 버킷을 전량 포함했다.

- 오케스트레이션과 진입점
- Stage 0~4 계약 연속성
- PASS_WITH_FIX 및 verdict 의미론
- DB/log/sink/artifact lineage
- Provider/router/telemetry/cost
- Context/style/work-guard 전파
- Safe-ops / rollback / wipe / reset 복구성

제외 범위는 UI 미관, signed installer, 실제 live quality 판정이다.

## 2. Pass 1 - 사실 수집

### P1-1. 진입점과 운영 메뉴는 명시적이다

직접 증거:

- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py) 메뉴는 `0,1,2,3,4,6,44,77,88,99`를 별도 작업 의미로 분리한다
- [process_runner.py](C:/Users/User/Desktop/글도비/modules/api/process_runner.py)는 동일한 의미를 `stdin` 시퀀스로 조립한다
- [bridge_server.py](C:/Users/User/Desktop/글도비/modules/api/bridge_server.py)는 project root와 quality/safe-ops surface를 HTTP 계층으로 노출한다

1차 결론:

- backend는 ad-hoc script 덩어리라기보다, 메뉴/runner/bridge가 같은 core engine을 다른 표면으로 호출하는 구조다

### P1-2. Stage 0 style 경로는 실제로 존재한다

직접 증거:

- [stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py) `phase_0_recovery()`는 `[6] 스타일 추출` 경로를 별도 옵션으로 둔다
- 같은 파일은 기존 Bible/Treatment 선택, AI 생성, 역설계, JSON import, block enrichment를 모두 Stage 0 패밀리로 묶는다

1차 결론:

- style/work material은 "없는 기능"이 아니라 Stage 0과 프로젝트 설정 사이에 분산돼 있다

### P1-3. PASS_WITH_FIX는 최종 품질이 아니라 loop semantics까지 포함한다

직접 증거:

- [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py)
- [stage4_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py)
- [stage2_finalizer.py](C:/Users/User/Desktop/글도비/modules/core/stage2_finalizer.py)

1차 결론:

- PASS_WITH_FIX는 단순 라벨이 아니라 local patch, director review, selection metadata와 결합된 운영 계약이다

### P1-4. sink alignment는 별도 건강도 축이다

직접 증거:

- [failure_analyzer.py](C:/Users/User/Desktop/글도비/modules/core/failure_analyzer.py)는 `stage_attempts`, `pass_rate_monitor`, `director_selections`, `episode_production`을 직접 대조한다
- 비교 키는 `attempt_key`, `candidate_key`, `content_hash`, `artifact_path`, verdict 계열이다

1차 결론:

- backend는 이미 "sink 간 drift"를 1급 위험으로 인식하고 있다

### P1-5. provider/router/telemetry는 config-driven 경향이 강하다

직접 증거:

- [base_agent.py](C:/Users/User/Desktop/글도비/modules/domain/agents/base_agent.py)는 `models.yaml`과 `system.yaml`을 읽고 fallback chain을 로드한다
- [metrics_collector.py](C:/Users/User/Desktop/글도비/modules/core/metrics_collector.py)는 model/provider/token/cost/time 집계를 담당한다
- [models.yaml](C:/Users/User/Desktop/글도비/config/models.yaml)은 실제 모델 SSOT 역할을 한다

1차 결론:

- 모델 라우팅은 하드코딩보다는 설정 중심이며, 건강도 위험은 "구현 누락"보다 "설정 drift" 쪽이다

## 3. Pass 2 - 교차 검증

### P2-1. 오케스트레이션 계약은 메뉴, runner, bridge에서 교차 검증된다

교차 증거:

- 코드: [main_a.py](C:/Users/User/Desktop/글도비/main_a.py), [process_runner.py](C:/Users/User/Desktop/글도비/modules/api/process_runner.py), [bridge_server.py](C:/Users/User/Desktop/글도비/modules/api/bridge_server.py)
- 문서: 기존 실행 로드맵 문서들

판정:

- `confirmed`

해석:

- backend 실행 경로는 여러 진입점이 있어도, root/project/menu 의미론이 완전히 따로 놀지는 않는다

### P2-2. Stage 0 style/work material은 존재하지만 UX 경계가 분산돼 있다

교차 증거:

- 코드: [stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py)
- 문서: [stage4-context-contract-full-survey-3pass-audit.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/stage4-context-contract-full-survey-3pass-audit.md), [ui-feedback-response-survey.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/ui-feedback-response-survey.md)

판정:

- `confirmed`

해석:

- style/work-guard는 backend에 존재한다. 다만 생성 위치와 입력 기회가 분산돼 있어 건강도상 blind spot이 된다.

### P2-3. PASS_WITH_FIX는 sink lineage와 분리해서 볼 수 없다

교차 증거:

- 코드: [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py), [failure_analyzer.py](C:/Users/User/Desktop/글도비/modules/core/failure_analyzer.py)
- 테스트/최근 회귀 맥락: Stage 4 canary-related test surface 및 최근 정렬 작업 문맥

판정:

- `confirmed`

해석:

- PASS_WITH_FIX 건강도는 "모델이 잘 썼는가"보다 "같은 attempt가 모든 sink에서 같은 것으로 남는가"와 직결된다

### P2-4. provider/router/telemetry는 coherent하나 optional hook 편차가 남는다

교차 증거:

- 코드: [base_agent.py](C:/Users/User/Desktop/글도비/modules/domain/agents/base_agent.py), [metrics_collector.py](C:/Users/User/Desktop/글도비/modules/core/metrics_collector.py)
- 보조 문서: [TF-VERTEX-migration-full-audit.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/TF-VERTEX-migration-full-audit.md)

판정:

- `confirmed`

해석:

- 설계상 coherent하지만, metrics collector가 optional integration이라는 점 때문에 "모든 런에서 같은 밀도로 남는다"까지는 정적 근거만으로 단정할 수 없다

### P2-5. 복구성은 존재하지만 강력한 메뉴가 곧 리스크 surface이기도 하다

교차 증거:

- 코드: [main_a.py](C:/Users/User/Desktop/글도비/main_a.py), [bridge_server.py](C:/Users/User/Desktop/글도비/modules/api/bridge_server.py)
- 문서: today roadmap 계열 실행 문서

판정:

- `confirmed`

해석:

- `44/77/88/99` 같은 기능은 운영 강점이다. 동시에 범위를 잘못 이해하면 project state를 크게 되감는 강한 도구이므로, health audit에서는 별도 버킷으로 유지하는 게 맞다

## 4. Pass 3 - 오탐 제거

다음 주장은 이번 정적 조사에서 올리지 않았다.

### R1. "백엔드는 Stage 전반이 불안정하다"

기각 사유:

- 진입점, provider, metrics, failure analysis, safe-ops 모두 코드상으로는 명시적 계층을 갖고 있다
- blanket claim으로 올릴 근거가 부족하다

상태:

- `rejected`

### R2. "style/work-guard는 사실상 미구현이다"

기각 사유:

- Stage 0 helper와 프로젝트 설정/문서에 모두 존재 흔적이 있다
- 문제는 존재 여부가 아니라 분산과 discoverability다

상태:

- `rejected`

### R3. "provider 라우팅은 하드코딩이라 설정은 장식이다"

기각 사유:

- [base_agent.py](C:/Users/User/Desktop/글도비/modules/domain/agents/base_agent.py)와 [models.yaml](C:/Users/User/Desktop/글도비/config/models.yaml) 교차 근거가 존재한다

상태:

- `rejected`

## 5. 확정 Findings

### F1. P1 - Sink lineage는 백엔드 건강도 핵심 축이며 drift 재발 가능성이 구조적으로 높다

- subsystem: Stage 4 / sink alignment
- claim: backend는 `attempt_key/candidate_key/artifact_path`를 여러 sink에 반복 기록하는 구조라, selection/patched/final metadata가 분리되지 않으면 건강도 저하가 곧바로 post-mortem 실패로 이어진다
- direct evidence:
  - [failure_analyzer.py](C:/Users/User/Desktop/글도비/modules/core/failure_analyzer.py)
  - [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py)
- counter-evidence review:
  - analyzer가 존재한다는 사실은 오히려 이 축이 실재하는 위험임을 뒷받침한다
- user impact:
  - canary/live 실패 후 "무슨 attempt가 실제 선택됐는지"를 다시 풀어야 하는 비용이 커진다
- status:
  - `confirmed`

### F2. P2 - Context/style/work-guard 계약은 기능 부재가 아니라 분산 리스크다

- subsystem: Stage 0 / context contract
- claim: style/work-guard는 구현돼 있지만 생성 지점, 설정 지점, 소비 지점이 분산돼 있어 backend health 관점의 추적 비용이 높다
- direct evidence:
  - [stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py)
  - [chief_writer_context.py](C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer_context.py)
  - [truth_gate.py](C:/Users/User/Desktop/글도비/modules/core/truth_gate.py)
- counter-evidence review:
  - 미구현이라는 주장까지는 올라가지 않는다
- user impact:
  - "왜 이 작품은 style이 먹었고 저 작품은 안 먹었는가"를 추적할 때 시간이 오래 걸린다
- status:
  - `confirmed`

### F3. P2 - Environment-driven root resolution은 건강한 명시성이면서 동시에 drift surface다

- subsystem: entrypoints / workspace resolution
- claim: `GEULDOBI_ENGINE_ROOT`, `GEULDOBI_PROJECTS_ROOT`, workspace fallback은 명시적이라 건강하지만, 런타임 환경 차이로 분기될 수 있어 별도 감시 항목이 필요하다
- direct evidence:
  - [process_runner.py](C:/Users/User/Desktop/글도비/modules/api/process_runner.py)
  - [bridge_server.py](C:/Users/User/Desktop/글도비/modules/api/bridge_server.py)
- counter-evidence review:
  - ad-hoc path join보다는 확실히 낫다
  - 따라서 P1까지 올릴 근거는 부족하다
- user impact:
  - 개발/패키지/운영 환경에서 project root가 달라질 때 조용한 drift가 날 수 있다
- status:
  - `confirmed`

### F4. Observation - Provider/telemetry 설계는 coherent하나 런타임 밀도는 정적 조사만으로 다 닫히지 않는다

- subsystem: provider / metrics
- claim: config-driven router와 metrics collector는 구조상 정리돼 있지만, 실제 모든 call site가 동일 밀도로 계측되는지는 live evidence 없이는 100% 못 올린다
- direct evidence:
  - [base_agent.py](C:/Users/User/Desktop/글도비/modules/domain/agents/base_agent.py)
  - [metrics_collector.py](C:/Users/User/Desktop/글도비/modules/core/metrics_collector.py)
- counter-evidence review:
  - 현재 구조를 "telemetry 부실"로 단정할 정도의 정적 근거는 없다
- status:
  - `confirmed`

## 6. 제외된 오탐

- "백엔드는 현재 전반적으로 붕괴 상태다"
- "style/work-guard는 사실상 없다"
- "provider 설정은 죽어 있고 하드코딩이 전부다"

## 7. 확신도 Ledger

- 기본 점수: `70`
- 버킷 7개 전량 인벤토리 완료: `+10`
- 오케스트레이션 / PASS_WITH_FIX / sink alignment / provider router 2중 근거 확보: `+10`
- 오탐 제거 완료: `+5`
- 기존 감사 문서와의 의미 충돌 해소: `+5`
- live rerun, 장기 실행, 실운영 부하 미검증: `-5`

최종 확신도: `95%`

## 8. 잔여 불확실성

- 실제 장기 5아크 live run에서 metrics/log 밀도가 동일하게 유지되는지
- rollback/wipe/reset이 모든 project 상태 조합에서 기대한 impact preview를 유지하는지
- style/work-guard가 UI 입력 동선 차이에도 일관되게 주입되는지

이 세 항목은 정적 조사로는 상한이 `95%`다.

## 9. Bucket Coverage

| Bucket | Covered | Primary Evidence |
| --- | --- | --- |
| B1 오케스트레이션/진입점 | Yes | [main_a.py](C:/Users/User/Desktop/글도비/main_a.py), [process_runner.py](C:/Users/User/Desktop/글도비/modules/api/process_runner.py), [bridge_server.py](C:/Users/User/Desktop/글도비/modules/api/bridge_server.py) |
| B2 Stage 0~4 계약 | Yes | [stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py), [stage2_finalizer.py](C:/Users/User/Desktop/글도비/modules/core/stage2_finalizer.py), [stage4_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py) |
| B3 PASS_WITH_FIX 의미론 | Yes | [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py), [stage4_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py) |
| B4 sink/artifact lineage | Yes | [failure_analyzer.py](C:/Users/User/Desktop/글도비/modules/core/failure_analyzer.py), [db_manager.py](C:/Users/User/Desktop/글도비/modules/core/db_manager.py) |
| B5 provider/router/telemetry | Yes | [base_agent.py](C:/Users/User/Desktop/글도비/modules/domain/agents/base_agent.py), [metrics_collector.py](C:/Users/User/Desktop/글도비/modules/core/metrics_collector.py), [models.yaml](C:/Users/User/Desktop/글도비/config/models.yaml) |
| B6 context/style/work-guard | Yes | [stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py), [chief_writer_context.py](C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer_context.py), [truth_gate.py](C:/Users/User/Desktop/글도비/modules/core/truth_gate.py) |
| B7 safe-ops/복구성 | Yes | [main_a.py](C:/Users/User/Desktop/글도비/main_a.py), [bridge_server.py](C:/Users/User/Desktop/글도비/modules/api/bridge_server.py) |

## 10. 최종 판정

현재 백엔드는 "전반적 붕괴"보다 "강한 기능성과 강한 운영성을 갖되, 일부 계약면이 관측 가능성 중심으로 취약한 구조"에 가깝다. 정적 기준에서 open `P0`는 없고, retained finding은 `P1 1건`, `P2 2건`, `Observation 1건`이다. 이 판정은 읽기 전용 전수조사 기준으로 `95%`까지 방어 가능하다.
