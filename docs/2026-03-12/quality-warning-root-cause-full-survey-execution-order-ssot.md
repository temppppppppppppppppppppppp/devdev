# Quality Warning Root Cause Full Survey Execution Order SSOT

- 작성일: 2026-03-12
- 상태: execution-ready
- 문서 역할: 품질 경고의 근인이 `LLM 성능 한계`인지, 아니면 `시스템적으로 개선 가능한 원인`이 있는지 전수조사하기 위한 실행 SSOT
- 금지사항: 코드 수정 금지, 테스트 실행 금지, canary/full/live rerun 금지
- 허용 범위: 읽기, 검색, diff, 문서 작성, tracked 로그/DB/산출물 열람, 읽기 전용 테스트 코드 열람

## 1. 목적

이 문서는 Stage 2/3/4에서 반복적으로 보이는 품질 경고를 `LLM이 원래 잘 못해서 생기는 잔여 잡음`으로 볼지, 아니면 `컨텍스트/검산/연속성/패치 루프/검증기 설계` 같은 시스템 요인으로 개선 가능한 문제로 볼지를 구분하기 위한 전수조사 오더 문서다.

핵심 원칙은 하나다.

- `LLM 탓`은 최후의 분류다.
- 먼저 시스템적으로 설명 가능한 축을 전량 조사하고, 그 축들이 반증된 뒤에만 `model-limited`로 내린다.

## 2. 기준선

- 조사 기준일: 2026-03-12
- 조사 모드: static / read-only
- seed evidence 프로젝트: [projects/000__t](C:/Users/User/Desktop/글도비/projects/000__t)
- seed evidence 로그:
  - [session_20260312_194058.log](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log)
  - [pass_rate_monitor.json](C:/Users/User/Desktop/글도비/projects/000__t/logs/pass_rate_monitor.json)
  - [runtime_audit_summary.json](C:/Users/User/Desktop/글도비/projects/000__t/logs/runtime_audit_summary.json)

현재 seed evidence에서 관찰된 경고 축은 아래다.

- 수치/자산 계산 모순
- 위치/상태/시간 마커 연속성 경고
- Entity 일관성 경고 또는 REJECT
- `InPlace Arc 변경 비율 > 30%`
- `Auto-correct`, `ConstraintDB`, `StateExtractor 캐시`, `Director advisory`가 함께 등장하는 구조

이 baseline만 봐도 품질 경고를 곧바로 `LLM이 멍청함`으로 환원할 수는 없다.

## 3. 참고 문서

- [backend-health-full-survey-execution-ssot.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/backend-health-full-survey-execution-ssot.md)
- [backend-health-full-survey-3pass-audit.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/backend-health-full-survey-3pass-audit.md)
- [stage4-context-contract-full-survey-3pass-audit.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/stage4-context-contract-full-survey-3pass-audit.md)
- [system-wide-full-audit-3pass-merged-final.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/system-wide-full-audit-3pass-merged-final.md)
- [mojibake-full-survey-3pass-final-audit.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/mojibake-full-survey-3pass-final-audit.md)

## 4. 조사 범위

### 포함

- Stage 2 아크 생성, 후보 비교, auto-sanitize, advisory, PASS_WITH_FIX 재심사
- Stage 3 blueprint/continuity/entity contract
- Stage 4 manuscript quality warning과 Stage 2/3 upstream contract 연결
- numeric checker, entity continuity, context assembly, patch loop, selection/fallback, observability
- seed evidence 프로젝트와 관련 tracked 로그/산출물

### 제외

- 순수 미문체 취향 논쟁
- “이 문장이 더 재밌냐” 수준의 취향 평가
- provider 일반론, 모델 벤치마크 일반론
- 실제 rerun 실행

## 5. 고정 조사 버킷

### Q1. 경고 인벤토리와 분류

- 대상: [session_20260312_194058.log](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log), [pass_rate_monitor.json](C:/Users/User/Desktop/글도비/projects/000__t/logs/pass_rate_monitor.json)
- 질문:
  - 경고를 `수치`, `연속성`, `entity`, `patch pressure`, `advisory noise`, `runtime fault`로 분류할 수 있는가
  - 반복 패턴이 arc별로 재발하는가

### Q2. 수치 검산과 목표 정렬

- 대상: [four_phase_arc_generator.py](C:/Users/User/Desktop/글도비/modules/domain/agents/four_phase_arc_generator.py), [investment_arithmetic_checker.py](C:/Users/User/Desktop/글도비/modules/core/investment_arithmetic_checker.py), [investment_math_verifier.py](C:/Users/User/Desktop/글도비/modules/core/investment_math_verifier.py), [fact_ledger.py](C:/Users/User/Desktop/글도비/modules/core/fact_ledger.py)
- 질문:
  - 수치 모순이 순수 생성 실수인지, 검산기/목표 정렬 로직의 coverage 부족인지 구분 가능한가
  - `NS-3-B`, 투자 advisory, fact extraction이 실제로 어떤 종류의 오류를 잡고 놓치는가

### Q3. 상태/위치/시간 연속성 계약

- 대상: [four_phase_arc_generator.py](C:/Users/User/Desktop/글도비/modules/domain/agents/four_phase_arc_generator.py), [continuity_arc.py](C:/Users/User/Desktop/글도비/modules/domain/agents/continuity_arc.py), [state_extractor.py](C:/Users/User/Desktop/글도비/modules/domain/agents/state_extractor.py), [stage2_optimizer.py](C:/Users/User/Desktop/글도비/modules/core/stage2_optimizer.py)
- 질문:
  - 위치/시간/상태 모순이 후보 생성 이전의 constraint assembly 문제인지, 생성 이후 patch/sync 문제인지 구분 가능한가
  - `forced location`, `ConstraintDB`, `StateExtractor 캐시`가 경고 감소에 실제 기여하는가

### Q4. Entity 일관성과 registry 품질

- 대상: [director_continuity.py](C:/Users/User/Desktop/글도비/modules/domain/agents/director_continuity.py), [unified_blueprint_validator.py](C:/Users/User/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py), [three_phase_blueprint_generator.py](C:/Users/User/Desktop/글도비/modules/domain/agents/three_phase_blueprint_generator.py)
- 질문:
  - Entity 경고는 진짜 이름 drift인지, registry 품질/약칭 필터/분류 스키마 한계인지 구분 가능한가
  - `WARNING`, `REJECT`, `PASS` 경계가 시스템적으로 과민하거나 둔감한가

### Q5. PASS_WITH_FIX와 patch pressure

- 대상: [stage2_finalizer.py](C:/Users/User/Desktop/글도비/modules/core/stage2_finalizer.py), [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py)
- 질문:
  - `InPlace Arc 변경 비율 > 30%`는 후보 품질 열세인지, patch contract 설계 문제인지 구분 가능한가
  - 재심사에 `already applied patch` 컨텍스트를 주입해도 같은 오류가 재검출되는가

### Q6. Director 비교 선택과 fallback semantics

- 대상: [director_ensemble.py](C:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py), [director.py](C:/Users/User/Desktop/글도비/modules/domain/agents/director.py)
- 질문:
  - Director 비교 경고는 prompt/context 부족인지, 선택 로직/fallback 정책 때문인지 구분 가능한가
  - `Python fallback = 첫 후보 PASS` 같은 정책이 품질 경고 해석을 왜곡할 가능성이 있는가

### Q7. Auto-correct / sanitize / preflight 개입 효과

- 대상: [stage2_validation_pipeline.py](C:/Users/User/Desktop/글도비/modules/core/stage2_validation_pipeline.py), [stage2_preflight.py](C:/Users/User/Desktop/글도비/modules/core/stage2_preflight.py), [stage2_optimizer.py](C:/Users/User/Desktop/글도비/modules/core/stage2_optimizer.py)
- 질문:
  - `Auto-correct`가 경고를 줄이는지, 아니면 원인을 가리고 downstream patch pressure만 높이는지 구분 가능한가
  - sanitize가 특정 장르 필드를 제거하면서 다른 정합성 debt를 만드는가

### Q8. 관측 가능성과 근인 분류 규칙

- 대상: 관련 로그/산출물/테스트/감리 문서 전반
- 질문:
  - 어떤 경고는 deterministic root cause로 닫을 수 있고, 어떤 경고만 `model-limited`로 남겨야 하는가
  - 후속 수정이 가능한 경고와 운영상 허용해야 하는 경고를 분리할 수 있는가

## 6. 판정 규칙

### confirmed-improvable

아래 중 하나라도 성립하면 `개선 가능`으로 올린다.

- validator/registry/checker/patch policy/threshold가 경고 패턴을 구조적으로 유발하거나 증폭함
- context assembly, sync, sanitize, auto-correct가 후보를 왜곡함
- fallback/selection semantics가 경고 해석을 흐림
- observability 부족 때문에 같은 유형 경고가 반복되는데 원인 추적이 어려움

### model-limited

오직 아래 조건을 모두 만족할 때만 `model-limited`로 내린다.

- deterministic/contract root cause가 반증됨
- validator/checker/context/sync/fallback 측 설명이 없음
- 서로 다른 코드 surface에서 같은 경고가 동일하게 남음

### rejected

아래는 단독으로 finding으로 올리지 않는다.

- warning 로그가 있다는 사실 자체
- advisory generated 횟수 자체
- 장시간 실행으로 인한 perf timer 경고 자체

## 7. 조사 흐름

### Pass 1. 경고 지형도 작성

- seed evidence 로그에서 품질 경고를 arc/종류/판정 결과별로 분류
- 해당 경고를 발생시키는 코드 surface를 매핑

### Pass 2. 교차 검증

- 경고마다 최소 2개 증거 계층 확보
- 증거 계층:
  1. 실제 로그/산출물
  2. producer 코드
  3. 읽기 전용 테스트
  4. 감리/운영 문서

### Pass 3. 오탐 제거

- 단순 `모델 한계` 프레이밍 제거
- 경고 noise와 실제 root cause 후보 분리
- 개선 가능 항목과 허용 residual 분리

## 8. 산출물 형식

최종 감리 문서는 아래 구조를 따른다.

1. Executive Summary
2. seed evidence baseline
3. Pass 1 경고 인벤토리
4. Pass 2 교차 검증
5. Pass 3 오탐 제거
6. 개선 가능 findings
7. model-limited residuals
8. 기각 findings
9. 확신도 ledger
10. 다음 수정 우선순위

## 9. 증거 ledger 형식

- id
- warning_family
- subsystem
- seed_evidence
- code_surface
- claim
- status (`confirmed-improvable`, `model-limited`, `rejected`, `runtime-only`)
- severity (`P0`, `P1`, `P2`, `Observation`)
- confidence_delta

## 10. 확신도 정책

- 시작점: `70`
- seed evidence 인벤토리 완료: `+10`
- 코드 surface 2중 매핑 완료: `+10`
- `LLM 탓` 오탐 제거 규칙 반영: `+5`
- 개선 가능 vs model-limited 분리 완료: `+5`
- 실제 rerun 미실행, runtime-only 미검증 항목: `-1~-5`

read-only 조사만으로 닫히지 않는 항목이 남으면 `95%`를 억지로 맞추지 않고 방어 가능한 상한에서 멈춘다.

## 11. 완료 기준

- Q1~Q8 전량 커버
- 품질 경고를 `개선 가능`, `model-limited`, `rejected`, `runtime-only`로 분류
- seed evidence의 대표 경고 패턴이 모두 버킷에 매핑됨
- 최종 확신도 `95%` 또는 방어 가능한 상한 도달

## 12. 기본 가정

- 이번 단계는 오더 문서와 그 감리 문서 확정까지만 수행한다.
- 실제 전수조사 실행과 코드 수정은 후속 지시에서 진행한다.
- seed evidence는 [projects/000__t](C:/Users/User/Desktop/글도비/projects/000__t) 이지만, 최종 조사는 시스템 전역 root cause 프레임으로 확장한다.
