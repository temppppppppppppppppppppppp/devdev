# Quality Warning Root Cause Remediation Execution SSOT

- 작성일: 2026-03-12
- 상태: `execution-ready`
- 문서 역할: [quality-warning-root-cause-full-survey-3pass-final-audit.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/quality-warning-root-cause-full-survey-3pass-final-audit.md) 의 retained `P1/P2`를 실제 수정 오더로 고정하는 단일 실행 SSOT
- 금지사항: 본 문서 자체는 코드 수정, 테스트 실행, rerun 수행 문서가 아니다. 범위 고정과 실행 순서, acceptance 정의까지만 담당한다.

## 1. 기준 문서

- [quality-warning-root-cause-full-survey-execution-order-ssot.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/quality-warning-root-cause-full-survey-execution-order-ssot.md)
- [quality-warning-root-cause-order-3pass-audit.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/quality-warning-root-cause-order-3pass-audit.md)
- [quality-warning-root-cause-full-survey-3pass-final-audit.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/quality-warning-root-cause-full-survey-3pass-final-audit.md)
- [backend-health-full-survey-execution-ssot.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/backend-health-full-survey-execution-ssot.md)
- [stage4-context-contract-full-survey-3pass-audit.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/stage4-context-contract-full-survey-3pass-audit.md)

## 2. 목표

이번 수정 오더의 목표는 아래 4개 retained finding을 코드 수준에서 닫는 것이다.

1. `P1` numeric advisory / NS-3-B / investment advisory가 advisory-only로 남아 selection과 final verdict를 충분히 강제하지 못하는 문제
2. `P1` Director compare fallback이 실패를 `PASS + first candidate`로 변환하는 문제
3. `P2` entity warning family가 registry/alias/threshold 정책과 뒤섞여 noise를 만드는 문제
4. `P2` auto-correct와 PASS_WITH_FIX patch loop가 upstream debt를 흡수만 하고 줄이지 못하는 문제

이번 오더는 `LLM 교체`, `프롬프트 문체 조정`, `미세한 서사 취향 보정`을 목표로 하지 않는다.

## 3. 실행 원칙

### 원칙 A. `LLM 탓` 판정은 마지막에만 한다

- deterministic checker
- registry / alias policy
- sanitize / sync
- patch loop
- fallback semantics

위 5축을 먼저 닫기 전에는 `model-limited`로 올리지 않는다.

### 원칙 B. selection failure는 PASS로 둔갑시키지 않는다

Director compare 실패, parser 실패, ask 예외는 `PASS`로 승격하지 않는다. 최소한 `RETRY`, `REJECT`, `FAIL_CLOSED`, `runtime-visible degraded state` 중 하나로 남겨야 한다.

### 원칙 C. upstream contract를 먼저 고친다

후처리 patch 양을 줄이는 것이 목표가 아니라, patch가 많이 필요해지는 upstream 원인을 먼저 줄인다.

### 원칙 D. warning은 관측치가 아니라 gate로 승격할 수 있어야 한다

numeric advisory, entity mismatch, auto-correct count, patch ratio는 단순 로그가 아니라 selection / score / retry / reject에 반영 가능한 형태여야 한다.

## 4. 실행 범위

### 포함

- Stage 2 candidate qualification
- Stage 2/Director scoring and fallback semantics
- entity continuity registry / alias / severity rules
- auto-correct / sanitize / patch-pressure observability and gating
- 수정 후 targeted regression / rerun gate 정의

### 제외

- LLM provider 교체
- prompt 문체 개편
- Stage 4 manuscript style 개선
- UI / desktop / build 문제
- full/live production rerun

## 5. Work Packages

### E-1. Director compare fallback fail-closed

목표:

- compare/parsing/ask 실패가 더 이상 `PASS + first candidate + 75점`으로 집계되지 않게 한다.

대상 파일:

- [director_ensemble.py](C:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py)
- [director.py](C:/Users/User/Desktop/글도비/modules/domain/agents/director.py)
- [test_director_modules.py](C:/Users/User/Desktop/글도비/tests/test_director_modules.py)

구현 원칙:

- `_fallback_arc_selection()`은 `PASS`를 반환하지 않는다.
- fallback은 명시적 degraded verdict를 남기고, 상위 pipeline이 retry 또는 reject로 처리할 수 있게 해야 한다.
- fallback hit 여부는 로그와 telemetry에서 식별 가능해야 한다.

acceptance:

- compare/parsing/ask 예외 시 `PASS`가 나오지 않는다.
- fallback 여부가 결과 객체와 로그에 명시된다.
- 기존 normal compare path와 fallback path가 테스트에서 분리 검증된다.

### E-2. Numeric advisory / NS-3-B hardening

목표:

- arithmetic / NS-3-B / investment advisory가 selection과 final verdict에 실제 영향을 주도록 만든다.

대상 파일:

- [four_phase_arc_generator.py](C:/Users/User/Desktop/글도비/modules/domain/agents/four_phase_arc_generator.py)
- [investment_arithmetic_checker.py](C:/Users/User/Desktop/글도비/modules/core/investment_arithmetic_checker.py)
- [investment_math_verifier.py](C:/Users/User/Desktop/글도비/modules/core/investment_math_verifier.py)
- 관련 targeted tests

구현 원칙:

- advisory severity를 `candidate qualification`, `score cap`, `retry trigger`, `reject trigger` 중 하나와 연결한다.
- `Python checker` 결과가 있으면 selection path에서 무시되지 않아야 한다.
- `investment_math_verifier` 부재/실패는 보조 verifier 상실로만 취급하고, Python checker 결과를 약화시키지 않는다.

acceptance:

- MAJOR/CRITICAL arithmetic mismatch는 selection 결과에 구조적으로 반영된다.
- advisory generated만 찍히고 PASS로 흘러가는 blind spot이 줄어든다.
- Arc 경계 자본 불연속과 수익 과대/과소는 테스트 가능한 gate가 된다.

### E-3. Entity registry / alias / threshold normalization

목표:

- harmless alias와 진짜 continuity drift를 분리하고, entity warning noise를 낮춘다.

대상 파일:

- [director_continuity.py](C:/Users/User/Desktop/글도비/modules/domain/agents/director_continuity.py)
- [unified_blueprint_validator.py](C:/Users/User/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py)
- 관련 targeted tests

구현 원칙:

- alias/abbreviation/location-variant 규칙을 명시적 policy로 승격한다.
- `WARNING`, `REJECT`, `PASS` 경계는 registry 품질과 별개로 재현 가능해야 한다.
- location 표기 drift는 entity mismatch와 별도 family로 분리 가능한지 검토한다.

acceptance:

- 약칭/동의 표기와 실제 drift가 같은 severity로 뭉개지지 않는다.
- seed evidence에서 보인 `사무실 -> 오피스`류 표기 drift가 어떻게 분류되는지 규칙이 명시된다.
- entity warning이 줄더라도 진짜 continuity 실패는 그대로 잡힌다.

### E-4. Auto-correct / patch pressure discipline

목표:

- auto-correct와 PASS_WITH_FIX가 upstream debt를 감추는 대신, debt를 관측하고 줄이는 방향으로 동작하게 만든다.

대상 파일:

- [stage2_validation_pipeline.py](C:/Users/User/Desktop/글도비/modules/core/stage2_validation_pipeline.py)
- [stage2_optimizer.py](C:/Users/User/Desktop/글도비/modules/core/stage2_optimizer.py)
- [stage2_finalizer.py](C:/Users/User/Desktop/글도비/modules/core/stage2_finalizer.py)
- 관련 targeted tests

구현 원칙:

- auto-correct count, correction category, patch ratio를 verdict/score/retry와 연결 가능한 메타로 남긴다.
- `InPlace change ratio > threshold`는 단순 warning이 아니라 후속 판정에 영향 주는 debt signal이 되어야 한다.
- 이미 적용된 patch context를 재심사에 넣는 현재 계약은 유지하되, 반복 patch의 상위 원인을 구분할 수 있는 관측치를 추가한다.

acceptance:

- auto-correct가 발생했을 때 무엇이 고쳐졌는지 category 수준으로 추적 가능하다.
- patch ratio 초과가 score cap, retry escalation, structural rewrite 전환 조건 중 하나와 연결된다.
- PASS_WITH_FIX가 반복될수록 evidence가 더 쌓이고, 원인 추적은 쉬워진다.

### E-5. Proof Gate And Closure

목표:

- E-1 ~ E-4 수정 후, 실제로 경고 family가 줄고 verdict semantics가 바르게 닫히는지 검증한다.

증명 단계:

1. targeted regression
2. seed evidence 재현 또는 동등 Stage 2 proof run
3. 최종 closure 문서화

acceptance:

- fallback test는 더 이상 `PASS` fallback을 기대하지 않는다.
- arithmetic / entity / patch pressure 관련 regression이 추가된다.
- seed class warning family가 줄거나, 남더라도 명확히 `model-limited residual`로 분리된다.

## 6. 실행 순서

실행 순서는 아래로 고정한다.

1. `E-1 Director compare fallback fail-closed`
2. `E-2 Numeric advisory / NS-3-B hardening`
3. `E-3 Entity registry / alias / threshold normalization`
4. `E-4 Auto-correct / patch pressure discipline`
5. `E-5 Proof Gate And Closure`

이 순서를 택한 이유:

- `E-1`은 품질 해석 자체를 왜곡할 수 있는 P1이다.
- `E-2`는 seed evidence에서 실제로 가장 강하게 반복된 warning family를 직접 친다.
- `E-3`, `E-4`는 noise reduction과 upstream debt 관측 강화를 담당한다.
- proof는 구현 후 한 번에 묶는다.

## 7. 비목표

다음 항목은 이번 수정 오더에 포함하지 않는다.

- residual narrative taste 개선
- 투자 장르 프롬프트 전면 개편
- UI/desktop 개선
- packaged build / codesign
- full/live 5아크 런

## 8. 종료 조건

이번 수정 오더는 아래 조건을 만족할 때 닫는다.

1. retained `P1 2건`, `P2 2건`이 코드/테스트 기준으로 모두 닫힌다.
2. fallback path가 더 이상 success verdict를 위장하지 않는다.
3. arithmetic / entity / patch pressure family가 gateable signal이 된다.
4. 수정 후 proof gate 문서가 `warning family -> root cause -> outcome`을 다시 닫는다.

## 9. 기본 가정

- 이번 턴에서는 문서화와 감리까지만 수행한다.
- 실제 코드 수정, targeted regression, rerun은 후속 실행 단계에서 수행한다.
- 본 문서가 quality-warning root-cause 축의 최상위 실행 SSOT다.
