# OPUS TF 5-Terminal Remediation Execution SSOT

- 작성일: 2026-03-13
- 상태: `execution-ready`
- 문서 역할: [OPUS-TF-5terminal-consolidated-findings-3pass-reaudit.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/OPUS-TF-5terminal-consolidated-findings-3pass-reaudit.md) 기준으로 `OPUS TF 5-Terminal` 조사 결과를 실제 수정 오더로 잠그는 단일 실행 SSOT
- 금지사항: 본 문서는 코드 수정, 테스트 실행, rerun 수행 문서가 아니다. 범위 고정, 우선순위 잠금, acceptance 정의까지만 담당한다.

## 1. 기준 문서

- [OPUS-TF-5terminal-consolidated-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/OPUS-TF-5terminal-consolidated-findings.md)
- [OPUS-TF-5terminal-consolidated-findings-3pass-reaudit.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/OPUS-TF-5terminal-consolidated-findings-3pass-reaudit.md)
- [OPUS-TF-5terminal-master-audit-order.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/OPUS-TF-5terminal-master-audit-order.md)
- [OPUS-TF-T1-infrastructure-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/OPUS-TF-T1-infrastructure-findings.md)
- [OPUS-TF-T2-stage0-to-stage2-consolidated-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/OPUS-TF-T2-stage0-to-stage2-consolidated-findings.md)
- [T3-stage3-4-pipeline-audit-report.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/T3-stage3-4-pipeline-audit-report.md)
- [T4-quality-advisory-audit-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/T4-quality-advisory-audit-findings.md)
- [OPUS-TF-T5-domain-auxiliary-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/OPUS-TF-T5-domain-auxiliary-findings.md)

## 2. 목표

이번 실행 오더의 목표는 grand total을 맞추는 것이 아니다. 재감리에서 **독립적으로 신뢰 가능하다고 확인된 P0/P1과 핵심 P2 클러스터**를 실제 수정 순서로 고정하는 것이다.

이번 오더가 닫아야 하는 축은 아래 5개다.

1. `Stage 0 -> Stage 2` 진입 차단 해소
2. `Director 주권` 사후 무효화/우회 클러스터 제거
3. `HUD / FactLedger / Guard` 데이터 무결성 복원
4. `API contract / prompt / 문서 수치` 드리프트 정리
5. `교차 단계 회귀 테스트`와 핵심 단위 테스트 보강

이번 오더는 `정확한 총건수 262/264 논쟁`을 gate로 사용하지 않는다. 실행 기준은 **확정된 고위험군**이다.

## 3. 실행 원칙

### 원칙 A. P0 차단 해소가 가장 먼저다

- `T2-001`이 닫히지 않으면 Stage 2 자체가 빈 `plot_roadmap`로 종료될 수 있다.
- 이 축을 열기 전에는 다른 상위 품질 개선이 실효성을 갖기 어렵다.

### 원칙 B. Director verdict 이후 Python이 판정을 뒤집지 못하게 한다

- `T3-029`, `T4-P1-01`, `T4-P1-02`, `T4-P1-03`, `T4-P1-04`는 같은 family다.
- 구현 방식은 달라도 공통 문제는 “Director 주권 침식”이다.

### 원칙 C. 데이터 무결성은 관측성보다 앞선다

- `T1-01`, `T1-02`, `T1-03`, `T5-WS-016`, `T5-GG-016`, `T5-NAR-08/09/13`은 silent wrong result 또는 잘못된 누적 상태로 이어진다.
- 로깅/문서보다 먼저 닫는다.

### 원칙 D. 중복/총건수 불확실성은 실행 범위를 흔들지 못한다

- `262`가 완전히 입증되지 않았더라도, high-confidence retained set은 충분히 크고 명확하다.
- 따라서 수정 오더는 disputed total이 아니라 **confirmed cluster**로 잠근다.

### 원칙 E. 테스트는 후속이 아니라 같은 묶음의 종료 조건이다

- `T1-13`, `T3-003`, `T3-004`, `T4-P1-07`, `T2-052`는 단순 부가 작업이 아니다.
- 상위 버그 수정과 같은 Work Package의 acceptance로 묶는다.

## 4. Work Packages

### E-1. Stage 0 -> Stage 2 roadmap handoff 복구

대상 finding:

- `T2-001`
- `T2-002`
- 연계 안정화: `T2-021`

대상 파일:

- [stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py)
- [story_expander.py](C:/Users/User/Desktop/글도비/modules/core/stage0/story_expander.py)
- [reverse_expander.py](C:/Users/User/Desktop/글도비/modules/core/stage0/reverse_expander.py)
- 관련 테스트:
  - [test_stage01_helpers.py](C:/Users/User/Desktop/글도비/tests/test_stage01_helpers.py)
  - [test_reverse_expander_g2.py](C:/Users/User/Desktop/글도비/tests/test_reverse_expander_g2.py)
  - Stage 2 handoff regression 추가

구현 원칙:

- 컨셉 플로우와 역설계 플로우 모두 `plot_roadmap`를 결정적으로 주입한다.
- `treatment` 또는 `arc_stubs`가 존재하는데 Stage 2 입력이 빈 배열이 되는 경로를 허용하지 않는다.
- 예외 경로(`T2-021`)도 `UnboundLocalError` 없이 안전하게 닫는다.

acceptance:

- 컨셉 플로우 생성 직후 Bible에 `plot_roadmap`가 존재한다.
- 역설계 플로우도 Stage 2 진입에 필요한 최소 `plot_roadmap` 스텁을 가진다.
- Stage 2가 `total_count=0`으로 즉시 완료되는 회귀가 테스트로 차단된다.

### E-2. Director 주권 복구

대상 finding:

- `T3-029`
- `T4-P1-01`
- `T4-P1-02`
- `T4-P1-03`
- `T4-P1-04`

대상 파일:

- [stage3_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage3_orchestrator.py)
- [validation_orchestrator.py](C:/Users/User/Desktop/글도비/modules/validation/validation_orchestrator.py)
- [director_ensemble.py](C:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py)
- 관련 테스트:
  - [test_stage3_orchestrator.py](C:/Users/User/Desktop/글도비/tests/test_stage3_orchestrator.py)
  - [test_validation.py](C:/Users/User/Desktop/글도비/tests/test_validation.py)
  - [test_director_modules.py](C:/Users/User/Desktop/글도비/tests/test_director_modules.py)

구현 원칙:

- Director PASS 이후 Python 후행 로직이 verdict를 폐기하지 않게 한다.
- `ConsistencyValidator` / `RetrospectiveValidator`의 강한 위반은 advisory 또는 pre-director evidence로만 전달하고 최종 verdict는 Director가 닫게 한다.
- 단일 Blueprint 경로도 Python-only `PASS`로 닫지 않는다.
- adaptive 하향은 `warning / conditional`로 남길 수는 있어도 Director PASS를 `REJECT`로 뒤집는 식으로 끝나면 안 된다.

acceptance:

- Director PASS Blueprint가 continuity pin 미해결만으로 저장 skip 되지 않는다.
- Stage 3 경로에서 validator가 즉시 `REJECT`를 반환하더라도 Director 주권 우회가 남지 않는다.
- single-candidate 경로와 adaptive 경로 모두 “Director 미호출 PASS” 또는 “Director PASS -> Python REJECT” 회귀 테스트를 가진다.

### E-3. HUD / FactLedger / Guard 무결성 복구

대상 finding:

- `T1-01`
- `T1-02`
- `T1-03`
- `T5-WS-016`
- `T5-GG-016`
- `T5-NAR-08`
- `T5-NAR-09`
- `T5-NAR-13`

대상 파일:

- [RESET.py](C:/Users/User/Desktop/글도비/RESET.py)
- [project_manager.py](C:/Users/User/Desktop/글도비/modules/core/project_manager.py)
- [fact_ledger.py](C:/Users/User/Desktop/글도비/modules/core/fact_ledger.py)
- [style_guard.py](C:/Users/User/Desktop/글도비/modules/core/genre_guards/style_guard.py)
- [semantic_item_registry.py](C:/Users/User/Desktop/글도비/modules/core/semantic_item_registry.py)
- [information_diffusion.py](C:/Users/User/Desktop/글도비/modules/core/information_diffusion.py)

관련 테스트:

- RESET/HUD regression 신설
- FactLedger dead-NPC regression 신설
- StyleGuard warning propagation 테스트
- protagonist hardcode 제거 테스트
- faction propagation policy 테스트

구현 원칙:

- 장르별 HUD는 동적 키로만 접근한다.
- dead NPC는 WorldState와 FactLedger 모두에서 동일한 차단 정책을 가진다.
- WorkGuard warning은 StyleGuard에서 소실되지 않는다.
- 주인공명 하드코딩은 파라미터/상태 기반으로 교체한다.
- `should_npc_know`와 `propagate_event`의 관계 단계는 동일 family 정책으로 맞춘다.

acceptance:

- 비무협 장르에서 HUD 롤백/동기화가 MartialHUD 하드코딩 없이 수행된다.
- dead NPC가 ledger 리셋 이후 alive로 재등록되지 않는다.
- warning_violations가 StyleGuard에서 유지된다.
- 특정 이름 하드코딩 없이 protagonist item 추적이 동작한다.
- same_faction / isolated 전파 정책이 테스트로 고정된다.

### E-4. Contract / Prompt / 문서 드리프트 정리

대상 finding:

- `T1-04`
- `T5-API-03`
- `T5-API-04`
- `T5-API-05`
- `T4-P2-CF01`
- `T3-040`

대상 파일:

- [api-contract-v1.yaml](C:/Users/User/Desktop/글도비/docs/implementation/api-contract-v1.yaml)
- [director.yaml](C:/Users/User/Desktop/글도비/config/prompts/director.yaml)
- [CLAUDE.md](C:/Users/User/Desktop/글도비/CLAUDE.md)

구현 원칙:

- API contract는 실제 포트/에러코드/엔드포인트와 일치시킨다.
- `director.yaml`의 NC-3 항목 수는 실제 20개 기준으로 갱신한다.
- `CLAUDE.md`의 Self-Critique 개수 표기와 protagonist_items 통계를 현행화한다.
- 이 묶음은 문서 청소가 아니라 **운영 계약 동기화**로 취급한다.

acceptance:

- `api-contract-v1.yaml`이 실제 브리지 서버 surface와 충돌하지 않는다.
- `director.yaml`과 코드 기준 NC-3 항목 수가 일치한다.
- `CLAUDE.md`의 핵심 운영 수치가 현행 코드와 맞는다.

### E-5. 회귀 테스트 보강

대상 finding:

- `T1-13`
- `T3-003`
- `T3-004`
- `T4-P1-07`
- `T2-052`

대상 테스트:

- [test_stage01_helpers.py](C:/Users/User/Desktop/글도비/tests/test_stage01_helpers.py)
- [test_reverse_expander_g2.py](C:/Users/User/Desktop/글도비/tests/test_reverse_expander_g2.py)
- [test_stage3_orchestrator.py](C:/Users/User/Desktop/글도비/tests/test_stage3_orchestrator.py)
- [test_stage4_interview_round.py](C:/Users/User/Desktop/글도비/tests/test_stage4_interview_round.py)
- [test_continuity_validator.py](C:/Users/User/Desktop/글도비/tests/test_continuity_validator.py)
- Arc agent 전용 테스트 신규 묶음
- RESET 전용 테스트 신규

구현 원칙:

- 각 상위 버그 묶음은 대응 regression test 없이 닫지 않는다.
- 단위 테스트만이 아니라 cross-stage contract 테스트를 포함한다.
- 병렬 실행/timeout/partial failure는 MagicMock 대체가 아니라 실제 경계 동작을 검증한다.

acceptance:

- Stage 3 출력과 Stage 4 입력 간 필드 계약 테스트가 존재한다.
- Advisory 병렬 실행은 success / partial failure / timeout 3경로를 테스트한다.
- ContinuityValidator 5/6 미검증 구간이 보강된다.
- Arc agent 핵심 모듈에 최소 진입 테스트가 추가된다.

### E-6. 선별 P2 안정화 패키지

대상 finding:

- `T2-011`
- `T2-012`
- `T2-015`
- `T2-021`
- `T3-006`
- `T3-007`
- `T3-018`
- `T3-019`

구현 원칙:

- P1을 닫는 과정에서 바로 붙는 저비용 P2는 같은 배치에서 닫는다.
- 반대로 범위가 커지는 P2/P3 전수정리는 이번 오더 밖으로 둔다.

acceptance:

- falsy `or` 패턴, timeline 기본값, reject metric 손실, scene key 정렬, thread race, Self-Critique issue 형식 혼재가 각각 회귀 테스트와 함께 닫힌다.

## 5. 실행 순서

실행 순서는 아래로 고정한다.

1. `E-1 Stage 0 -> Stage 2 roadmap handoff 복구`
2. `E-2 Director 주권 복구`
3. `E-3 HUD / FactLedger / Guard 무결성 복구`
4. `E-4 Contract / Prompt / 문서 드리프트 정리`
5. `E-5 회귀 테스트 보강`
6. `E-6 선별 P2 안정화 패키지`

이 순서를 택한 이유:

- `E-1`은 시스템 진입 차단이다.
- `E-2`는 설계 원칙 위반 클러스터다.
- `E-3`은 silent wrong result를 줄인다.
- `E-4`는 운영 계약을 현재 코드와 다시 맞춘다.
- `E-5`는 앞선 수정의 종료 조건이다.
- `E-6`은 상위 패키지를 건드릴 때 같이 닫는 편이 더 싸다.

## 6. Verification Matrix

### Focused tests

- `test_stage01_helpers.py`
- `test_reverse_expander_g2.py`
- `test_stage3_orchestrator.py`
- `test_validation.py`
- `test_director_modules.py`
- `test_stage4_interview_round.py`
- `test_continuity_validator.py`
- RESET / FactLedger / StyleGuard / semantic_item_registry / information_diffusion 신규 regression

### Required assertions

1. 컨셉/역설계 플로우 모두 `plot_roadmap`를 가진 채 Stage 2에 진입한다.
2. Director PASS 이후 Python continuity pin/validator/adaptive 경로가 verdict를 뒤집지 않는다.
3. 비무협 장르에서도 HUD 롤백/동기화가 정상 동작한다.
4. dead NPC는 FactLedger 재등록 경로를 타지 않는다.
5. WorkGuard warning이 StyleGuard를 통과한 뒤에도 보존된다.
6. protagonist hardcode가 제거되고 테스트로 고정된다.
7. API contract와 실제 서버 surface가 일치한다.
8. cross-stage handoff와 advisory 병렬 실행 테스트가 추가된다.
9. 선별 P2 fix는 대응 regression과 함께 닫힌다.

## 7. 비목표

다음 항목은 이번 실행 SSOT 범위에 포함하지 않는다.

- P3 165건 전수 정리
- UI / desktop 전면 개선
- 대규모 아키텍처 리팩터링
- 모델 교체
- live 전수 rerun
- disputed grand total 재집계만을 위한 별도 통계 작업

## 8. 종료 조건

이번 오더는 아래 조건을 만족할 때 닫는다.

1. `T2-001`과 `T2-002`가 닫히고 Stage 2 진입 차단이 사라진다.
2. Director 주권 클러스터(`T3-029`, `T4-P1-01~04`)가 더 이상 verdict를 침식하지 않는다.
3. HUD / FactLedger / Guard 무결성 클러스터가 회귀 테스트와 함께 닫힌다.
4. API contract / prompt / 문서 수치 드리프트가 현행 코드와 동기화된다.
5. 교차 단계 테스트와 병렬 실행 테스트가 추가되어 같은 family 회귀를 막는다.

## 9. 기본 가정

- 이번 턴에서는 문서 확정까지만 수행한다.
- 실제 코드 수정과 테스트 실행은 후속 실행 단계에서 진행한다.
- 이 문서는 raw `262건`이 아니라 재감리에서 확인한 **고신뢰 retained set**을 기준으로 하는 최상위 실행 SSOT다.
