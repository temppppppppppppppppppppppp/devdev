# Backend Health Full Survey Execution SSOT

- 작성일: 2026-03-12
- 상태: execution-ready
- 문서 역할: 백엔드 건강도 전수조사의 범위, 근거 계층, 감리 기준을 잠그는 단일 실행 SSOT
- 금지사항: 코드 수정 금지, 테스트 실행 금지, canary/full/live rerun 금지
- 허용 범위: 읽기, 검색, diff, 문서 작성, tracked 로그/DB/산출물 열람

## 1. 문서 목적

이 문서는 현재 worktree 기준 백엔드 건강도를 읽기 전용으로 전수조사하기 위한 기준 문서다. 목표는 "무엇이 깨져 있는가"를 성급히 단정하는 것이 아니라, 백엔드 계약면을 전량 인벤토리하고 오탐을 제거한 뒤 3-pass 감리 문서에서 방어 가능한 finding만 남기는 것이다.

본 조사에서의 `건강도`는 다음을 뜻한다.

- 진입점과 오케스트레이션이 명시적 계약을 갖는가
- Stage 0~4 handoff와 verdict 의미론이 일관적인가
- DB/log/sink/artifact lineage가 복원 가능한가
- provider/router/telemetry 경로가 설정과 코드에서 같은 의미를 갖는가
- style/work guard/context 계약이 분산되어 있어도 추적 가능한가
- rollback/wipe/reset 같은 운영 복구 경로가 식별 가능하고 문서화 가능한가

## 2. 기준선

- 조사 기준일: 2026-03-12
- 조사 모드: static / read-only
- 최종 목표: 3-pass 감리 후 확신도 `95%` 또는 읽기 전용 조사로 방어 가능한 상한
- 본 문서는 실행 기준만 잠그고, 최종 판정은 별도 감리 문서에서 수행한다

## 3. 참고 문서

- [system-wide-full-survey-3pass-master-audit.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/system-wide-full-survey-3pass-master-audit.md)
- [system-wide-full-audit-3pass-merged-final.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/system-wide-full-audit-3pass-merged-final.md)
- [stage4-context-contract-full-survey-3pass-audit.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/stage4-context-contract-full-survey-3pass-audit.md)
- [today-roadmap-reference-remediation-execution-ssot.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/today-roadmap-reference-remediation-execution-ssot.md)
- [today-roadmap-reference-remediation-execution-ssot-3pass-audit.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/today-roadmap-reference-remediation-execution-ssot-3pass-audit.md)

## 4. 조사 범위

### 포함

- 백엔드 엔트리포인트와 오케스트레이션
- Stage 0~4 핵심 helper/orchestrator/finalizer/interview/selection/post-processing
- DB/log/metrics/failure analysis/quality dashboard에 연결되는 sink
- provider/router/model config/telemetry 계층
- bridge/process runner 중 백엔드 계약에 직접 닿는 구간
- safe-ops, rollback, wipe, reset 같은 운영 복구 경로

### 제외

- 순수 UI 미관 문제
- Electron 렌더러 레이아웃 품질
- 실제 live rerun 품질 평가
- signed installer/SmartScreen 같은 OS 배포 평판 이슈

## 5. 고정 조사 버킷

### B1. 오케스트레이션과 진입점

- 대상: [main_a.py](C:/Users/User/Desktop/글도비/main_a.py), [process_runner.py](C:/Users/User/Desktop/글도비/modules/api/process_runner.py), [bridge_server.py](C:/Users/User/Desktop/글도비/modules/api/bridge_server.py)
- 질문:
  - 메뉴/CLI/IPC 진입점이 같은 작업 의미를 가리키는가
  - workspace/projects root 해석이 일관적인가
  - `6`, `44`, `77`, `88`, `99` 같은 운영 메뉴가 복구/재실행 계약을 명시적으로 가지는가

### B2. Stage 0~4 계약 연속성

- 대상: [stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py), [stage2_finalizer.py](C:/Users/User/Desktop/글도비/modules/core/stage2_finalizer.py), [stage4_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py), [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py), [stage4_post_processor.py](C:/Users/User/Desktop/글도비/modules/core/stage4_post_processor.py)
- 질문:
  - Stage 0 style 추출과 상위 재료가 이후 stage에 실질적으로 이어지는가
  - Stage 2/3/4 사이 handoff와 state merge는 같은 story contract를 유지하는가
  - One-Stop(`6`) 경로가 개별 stage 계약을 우회하지 않는가

### B3. PASS_WITH_FIX와 verdict 의미론

- 대상: [main_a.py](C:/Users/User/Desktop/글도비/main_a.py), [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py), [stage4_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py), [stage2_finalizer.py](C:/Users/User/Desktop/글도비/modules/core/stage2_finalizer.py)
- 질문:
  - `PASS`, `PASS_WITH_FIX`, `FAIL`, final verdict, quality label이 같은 의미 계층을 공유하는가
  - local patch loop와 final selection 메타가 분리돼 있는가
  - 재감리 루프가 reasoning을 과도하게 축약하지 않는가

### B4. DB/log/sink/artifact lineage

- 대상: [db_manager.py](C:/Users/User/Desktop/글도비/modules/core/db_manager.py), [failure_analyzer.py](C:/Users/User/Desktop/글도비/modules/core/failure_analyzer.py), [metrics_collector.py](C:/Users/User/Desktop/글도비/modules/core/metrics_collector.py)
- 질문:
  - `stage_attempts`, `pass_rate_monitor`, `director_selections`, `episode_production`이 같은 attempt lineage를 복원 가능한 형태로 남기는가
  - `attempt_key`, `candidate_key`, `content_hash`, `artifact_path`가 sink 간 동일성을 유지하는가
  - 운영 로그만으로 post-mortem이 가능한가

### B5. Provider / router / telemetry / cost

- 대상: [base_agent.py](C:/Users/User/Desktop/글도비/modules/domain/agents/base_agent.py), [metrics_collector.py](C:/Users/User/Desktop/글도비/modules/core/metrics_collector.py), [models.yaml](C:/Users/User/Desktop/글도비/config/models.yaml)
- 질문:
  - 실제 모델 선택 SSOT가 config-driven으로 유지되는가
  - fallback/rotation/metrics hook이 분리돼도 의미론이 흔들리지 않는가
  - token/cost telemetry가 건강도 판단에 쓸 수 있을 정도로 남는가

### B6. Context / style / work-guard 전파

- 대상: [stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py), [chief_writer_context.py](C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer_context.py), [chief_writer.py](C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer.py), [truth_gate.py](C:/Users/User/Desktop/글도비/modules/core/truth_gate.py)
- 질문:
  - style guide, author directives, work guard가 어디서 생성되고 어디서 소비되는지 추적 가능한가
  - CW/Director/context builder가 같은 상위 품질 계약을 보는가
  - 컨텍스트 분산이 건강도 저하를 부르는 blind spot인지, 아니면 명시적 경계인지 식별 가능한가

### B7. Safe-ops / rollback / wipe / reset 복구성

- 대상: [main_a.py](C:/Users/User/Desktop/글도비/main_a.py), [bridge_server.py](C:/Users/User/Desktop/글도비/modules/api/bridge_server.py), 관련 DB/운영 문서
- 질문:
  - wipe/reset/rollback의 대상 범위가 식별 가능한가
  - backend가 UI/bridge에 안전한 preview 또는 impact signal을 주는가
  - 실패 후 정리와 재실행 경로가 코드상으로는 복원 가능한가

## 6. 증거 계층

각 claim은 아래 계층 중 최소 2개로 재검증한다.

1. 코드
2. 읽기 전용 테스트
3. 운영 문서
4. tracked 로그/산출물/DB schema
5. git diff 또는 최근 수정 흔적

2차 근거가 없는 항목은 `finding`으로 승격하지 않고 `hypothesis` 또는 `runtime-only`로 내린다.

## 7. 산출 형식

최종 감리 문서는 아래 순서를 따른다.

1. Executive Summary
2. 조사 범위와 제외 범위
3. Pass 1 사실 수집
4. Pass 2 교차 검증
5. Pass 3 오탐 제거
6. 확정 findings
7. 기각 findings
8. 확신도 ledger
9. 잔여 불확실성
10. bucket coverage 표

모든 finding은 아래 필드를 가진다.

- id
- severity
- subsystem
- claim
- direct evidence
- counter-evidence review
- status (`confirmed`, `rejected`, `runtime-only`)
- confidence impact

## 8. 확신도 정책

- 시작점: `70`
- 전 버킷 인벤토리 완료: `+10`
- 핵심 계약 2중 근거 확보: `+10`
- 오탐 제거 완료: `+5`
- 문서/코드 의미 불일치 정리: `+5`
- 런타임 부재, 장기 실행 미검증, live 품질 불명확성은 항목별 `-1~-5`

읽기 전용 조사로 닫히지 않는 항목이 남으면 `95%`를 억지로 맞추지 않고 상한을 명시한다.

## 9. 완료 기준

- 고정 버킷 7개 전량 커버
- retained finding과 rejected finding이 명시적으로 분리됨
- `main_a.py`, `process_runner.py`, `bridge_server.py`, `failure_analyzer.py`, `base_agent.py`, `metrics_collector.py`를 포함한 핵심 경로가 증거 index에 포함됨
- `PASS_WITH_FIX`, sink alignment, provider/telemetry, style/work-guard, safe-ops가 모두 별도 섹션으로 닫힘
- 확신도 `95%` 또는 읽기 전용 기준 방어 가능한 상한 도달

## 10. 기본 가정

- 사용자 패턴상 문서 우선, 3-pass 감리, 95% 상한 정책을 그대로 따른다
- 이번 턴은 조사 문서 작성까지가 범위이며 구현 수정은 포함하지 않는다
- frontend/UI/build는 backend-facing contract를 설명하는 범위에서만 보조 증거로 사용한다
