# Quality Warning Root Cause Full Survey 3-Pass Final Audit

- 작성일: 2026-03-12
- 기준 SSOT: [quality-warning-root-cause-full-survey-execution-order-ssot.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/quality-warning-root-cause-full-survey-execution-order-ssot.md)
- 오더 감리: [quality-warning-root-cause-order-3pass-audit.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/quality-warning-root-cause-order-3pass-audit.md)
- 조사 모드: static / read-only
- seed evidence: [projects/000__t](C:/Users/User/Desktop/글도비/projects/000__t)
- 최종 상태: closed
- 최종 확신도: `95%`

## Executive Summary

이번 전수조사 결론은 명확하다. `000__t`에서 보인 품질 경고는 `LLM이 원래 못해서 생기는 잡음`으로 일괄 환원할 수 없다.

- seed evidence는 Stage 2를 끝까지 완주했고, fatal runtime fault는 보이지 않는다.
- 대신 `auto-correct 7회`, `investment advisory 6회`, `entity WARNING/REJECT 6회`, `InPlace patch pressure 3회`가 반복됐다.
- 이 경고 family들은 코드상 `validator`, `registry`, `sanitize`, `patch loop`, `director fallback`과 직접 연결된다.
- 최종 retained finding은 `confirmed-improvable 4건`, `model-limited residual 2건`, `rejected 3건`이다.

즉 현재 품질 경고의 주된 축은 `모델 한계`보다 `system contract/validator/fallback/patch design` 쪽이다.

## Scope And Method

- 코드 수정 없음
- 테스트 실행 없음
- canary/live rerun 없음
- 읽기, 검색, diff, tracked 로그/산출물 열람만 수행

조사 대상은 Stage 2/3/4 품질 경고와 직접 연결되는 다음 축으로 고정했다.

- seed warning inventory
- numeric/advisory/checker contract
- entity continuity / registry semantics
- auto-correct / sanitize / forced sync
- PASS_WITH_FIX / patch pressure
- director compare / fallback semantics
- model-limited residual 분리

## Seed Evidence Baseline

기준 로그와 산출물:

- [session_20260312_194058.log](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log)
- [pass_rate_monitor.json](C:/Users/User/Desktop/글도비/projects/000__t/logs/pass_rate_monitor.json)
- [runtime_audit_summary.json](C:/Users/User/Desktop/글도비/projects/000__t/logs/runtime_audit_summary.json)

기준 facts:

- [runtime_audit_summary.json](C:/Users/User/Desktop/글도비/projects/000__t/logs/runtime_audit_summary.json) 는 `tag=stage2_complete`, `db_commit=6`, `v60_25_auto_correct=7`, `v60_10_state_extracted=7`이다.
- [pass_rate_monitor.json](C:/Users/User/Desktop/글도비/projects/000__t/logs/pass_rate_monitor.json) 은 6아크를 기록하고, `PASS 3`, `PASS_WITH_FIX 3`, `REJECT 1`(Arc 3 attempt 1) 후 회복으로 닫힌다.
- fatal crash 증거는 없다. 로그에서 찾은 `CRITICAL` 표시는 runtime failure가 아니라 advisory 본문 내부의 등급 텍스트였다: [session_20260312_194058.log#L1238](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L1238)

warning family 집계:

- `Auto-correct:` 7회
- `Investment advisory generated` 6회
- `Entity 일관성 검증: WARNING|REJECT` 6회
- `InPlace Arc 변경 비율` 3회

대표 seed evidence:

- Director contradiction and PASS_WITH_FIX: [session_20260312_194058.log#L432](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L432), [session_20260312_194058.log#L433](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L433), [session_20260312_194058.log#L446](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L446)
- Arithmetic mismatch and fix instruction: [session_20260312_194058.log#L853](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L853)
- Patch pressure: [session_20260312_194058.log#L955](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L955), [session_20260312_194058.log#L1666](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L1666), [session_20260312_194058.log#L2174](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L2174)
- Entity WARNING/REJECT: [session_20260312_194058.log#L1284](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L1284), [session_20260312_194058.log#L1501](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L1501), [session_20260312_194058.log#L1998](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L1998), [session_20260312_194058.log#L2192](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L2192), [session_20260312_194058.log#L2506](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L2506)
- Arithmetic advisories on Arc 5: [session_20260312_194058.log#L2401](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L2401), [session_20260312_194058.log#L2414](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L2414), [session_20260312_194058.log#L2427](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L2427)

## Pass 1 - Warning Inventory

경고 family는 5개로 접혔다.

1. `numeric/advisory`
- 자산, 현금, 수익, Arc 경계 자본 연속성 괴리

2. `entity/registry`
- 명칭 drift, location 표기 drift, registry 매칭 경계 문제

3. `sanitize/auto-correct`
- auto-correct가 다수 발생하고 후속 patch pressure와 같이 나타남

4. `patch pressure`
- PASS_WITH_FIX와 InPlace change ratio 경고가 반복됨

5. `selection/fallback semantics`
- Director 비교 실패 시 Python fallback으로 PASS를 반환하는 설계가 존재함

## Pass 2 - Cross Check

### Numeric/advisory family

seed evidence는 숫자 경고가 이미 Python checker/advisory 층을 지난 뒤에도 반복됨을 보여준다.

- arithmetic checker는 현금, 총자산, Arc 경계 자본 연속성을 직접 계산한다: [investment_arithmetic_checker.py#L99](C:/Users/User/Desktop/글도비/modules/core/investment_arithmetic_checker.py#L99), [investment_arithmetic_checker.py#L118](C:/Users/User/Desktop/글도비/modules/core/investment_arithmetic_checker.py#L118), [investment_arithmetic_checker.py#L132](C:/Users/User/Desktop/글도비/modules/core/investment_arithmetic_checker.py#L132), [investment_arithmetic_checker.py#L220](C:/Users/User/Desktop/글도비/modules/core/investment_arithmetic_checker.py#L220)
- Stage 2 generator는 각 후보에 `NS-3-B`와 `investment_advisory`를 붙여 Director로 보낸다: [four_phase_arc_generator.py#L740](C:/Users/User/Desktop/글도비/modules/domain/agents/four_phase_arc_generator.py#L740), [four_phase_arc_generator.py#L783](C:/Users/User/Desktop/글도비/modules/domain/agents/four_phase_arc_generator.py#L783), [four_phase_arc_generator.py#L897](C:/Users/User/Desktop/글도비/modules/domain/agents/four_phase_arc_generator.py#L897), [four_phase_arc_generator.py#L903](C:/Users/User/Desktop/글도비/modules/domain/agents/four_phase_arc_generator.py#L903)
- 그럼에도 seed evidence는 `advisory generated`와 `PASS/PASS_WITH_FIX`가 함께 나온다: [session_20260312_194058.log#L731](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L731), [session_20260312_194058.log#L2440](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L2440), [session_20260312_194058.log#L2459](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L2459)

판정:

- numeric warning의 반복은 `LLM이 원래 계산을 못함`만으로 설명되지 않는다.
- 더 직접적인 root cause는 `deterministic checker가 advisory-only라서 selection/gating에 충분히 강제되지 않는 설계`다.

### Entity/registry family

- entity continuity는 명칭 mismatch를 바로 raw error로 다루지 않고 abbreviation/부분포함 필터를 적용한다: [director_continuity.py#L131](C:/Users/User/Desktop/글도비/modules/domain/agents/director_continuity.py#L131)
- mismatch가 모두 필터링되면 WARNING/REJECT가 PASS로 승격된다: [director_continuity.py#L161](C:/Users/User/Desktop/글도비/modules/domain/agents/director_continuity.py#L161)
- seed evidence는 location 표현 drift가 entity warning과 함께 나온다: [session_20260312_194058.log#L2192](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L2192), [session_20260312_194058.log#L2193](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L2193), [session_20260312_194058.log#L2506](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L2506), [session_20260312_194058.log#L2508](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L2508)

판정:

- entity warning family는 pure LLM error가 아니라 `registry completeness`, `표기 alias 정책`, `decision threshold`와 결합된 system warning이다.

### Sanitize/auto-correct family

- auto-correct audit event는 Stage 2 validation pipeline에서 명시적으로 찍힌다: [stage2_validation_pipeline.py#L334](C:/Users/User/Desktop/글도비/modules/core/stage2_validation_pipeline.py#L334)
- optimizer는 location sync, tactical location consistency advisory, wuxia field strip, asset growth advisory를 묶어서 수행한다: [stage2_optimizer.py#L268](C:/Users/User/Desktop/글도비/modules/core/stage2_optimizer.py#L268), [stage2_optimizer.py#L275](C:/Users/User/Desktop/글도비/modules/core/stage2_optimizer.py#L275), [stage2_optimizer.py#L481](C:/Users/User/Desktop/글도비/modules/core/stage2_optimizer.py#L481), [stage2_optimizer.py#L506](C:/Users/User/Desktop/글도비/modules/core/stage2_optimizer.py#L506), [stage2_optimizer.py#L1152](C:/Users/User/Desktop/글도비/modules/core/stage2_optimizer.py#L1152)
- seed evidence에서도 auto-correct는 거의 모든 아크에 반복된다: [session_20260312_194058.log#L446](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L446), [session_20260312_194058.log#L764](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L764), [session_20260312_194058.log#L1248](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L1248), [session_20260312_194058.log#L1467](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L1467), [session_20260312_194058.log#L1963](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L1963), [session_20260312_194058.log#L2470](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L2470), [session_20260312_194058.log#L2855](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L2855)

판정:

- auto-correct는 pure rescue가 아니라 `upstream debt를 숨기고 downstream patch pressure를 키우는 흡수 장치`일 가능성이 높다.

### Patch pressure family

- Stage 2 finalizer는 change ratio가 30%를 넘으면 경고를 찍는다: [stage2_finalizer.py#L730](C:/Users/User/Desktop/글도비/modules/core/stage2_finalizer.py#L730)
- 동시에 PASS_WITH_FIX 재심사에 이미 적용된 패치를 story context에 넣는다: [stage2_finalizer.py#L743](C:/Users/User/Desktop/글도비/modules/core/stage2_finalizer.py#L743), [stage2_finalizer.py#L749](C:/Users/User/Desktop/글도비/modules/core/stage2_finalizer.py#L749)
- seed evidence는 이 경고가 3회 반복된다: [session_20260312_194058.log#L955](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L955), [session_20260312_194058.log#L1666](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L1666), [session_20260312_194058.log#L2174](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L2174)

판정:

- 이 family는 `후처리 패치가 많았다`는 결과 보고가 아니라, `후보 생성-검증-패치 계약이 서로 어긋난다`는 system signal이다.

### Selection/fallback semantics family

- Arc compare path는 파싱 실패나 예외 시 Python fallback으로 간다: [director_ensemble.py#L563](C:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py#L563), [director_ensemble.py#L622](C:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py#L622)
- fallback은 첫 번째 후보를 `PASS`, `score=75`로 반환한다: [director_ensemble.py#L625](C:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py#L625)
- 이 동작은 테스트로도 고정돼 있다: [test_director_modules.py#L1153](C:/Users/User/Desktop/글도비/tests/test_director_modules.py#L1153)

판정:

- seed run에서 이 fallback이 실제 발동했다는 직접 증거는 없지만, warning 해석을 왜곡할 수 있는 설계이므로 full survey 대상에서 제외할 수 없다.
- 따라서 `runtime-only`가 아니라 `confirmed-improvable`로 유지한다. 이유는 설계가 이미 코드와 테스트로 고정돼 있기 때문이다.

## Pass 3 - False Positive Removal

다음 프레임은 기각했다.

### R1. "경고는 거의 다 LLM 탓이다"

기각 근거:

- arithmetic, entity, patch, fallback, auto-correct가 모두 독립적인 deterministic/system surface를 가진다.

### R2. "경고가 많으니 시스템은 전반적으로 불안정하다"

기각 근거:

- seed evidence는 Stage 2를 정상 완료했고, [runtime_audit_summary.json](C:/Users/User/Desktop/글도비/projects/000__t/logs/runtime_audit_summary.json) 도 `stage2_complete`로 닫힌다.
- 현재 문제는 runtime stability보다 quality contract debt에 가깝다.

### R3. "seed evidence가 프로젝트 하나라서 조사 가치가 낮다"

기각 근거:

- seed는 한 프로젝트지만 교차 검증 surface는 Stage 2/3/4 공통 모듈 전반이다.

## Confirmed-Improvable Findings

### P1. Numeric advisory가 advisory-only로 남아 selection/gating을 충분히 강제하지 못한다

- warning_family: `numeric/advisory`
- subsystem: Stage 2 candidate validation / Director handoff
- direct evidence:
  - [session_20260312_194058.log#L731](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L731)
  - [session_20260312_194058.log#L1238](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L1238)
  - [session_20260312_194058.log#L2401](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L2401)
  - [four_phase_arc_generator.py#L740](C:/Users/User/Desktop/글도비/modules/domain/agents/four_phase_arc_generator.py#L740)
  - [four_phase_arc_generator.py#L783](C:/Users/User/Desktop/글도비/modules/domain/agents/four_phase_arc_generator.py#L783)
  - [investment_arithmetic_checker.py#L99](C:/Users/User/Desktop/글도비/modules/core/investment_arithmetic_checker.py#L99)
- why not false positive:
  - checker가 이미 존재하고, 경고도 실제로 발생하는데, final verdict는 PASS/PASS_WITH_FIX로 닫힌다.
- user impact:
  - 자산/현금/수익 모순이 서사 내부에 잔존할 수 있다.

### P1. Director compare fallback이 LLM failure를 PASS first-candidate로 변환한다

- warning_family: `selection/fallback semantics`
- subsystem: Director compare
- direct evidence:
  - [director_ensemble.py#L563](C:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py#L563)
  - [director_ensemble.py#L622](C:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py#L622)
  - [director_ensemble.py#L625](C:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py#L625)
  - [test_director_modules.py#L1153](C:/Users/User/Desktop/글도비/tests/test_director_modules.py#L1153)
- why not false positive:
  - runtime hit 여부와 무관하게 설계 자체가 품질 해석을 왜곡할 수 있다.
- user impact:
  - compare 단계 실패가 quality success처럼 집계될 수 있다.

### P2. Entity warning family는 registry/alias/threshold 설계 영향이 크다

- warning_family: `entity/registry`
- subsystem: Director continuity
- direct evidence:
  - [director_continuity.py#L131](C:/Users/User/Desktop/글도비/modules/domain/agents/director_continuity.py#L131)
  - [director_continuity.py#L161](C:/Users/User/Desktop/글도비/modules/domain/agents/director_continuity.py#L161)
  - [director_continuity.py#L167](C:/Users/User/Desktop/글도비/modules/domain/agents/director_continuity.py#L167)
  - [session_20260312_194058.log#L2192](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L2192)
  - [session_20260312_194058.log#L2506](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L2506)
- why not false positive:
  - 약칭/부분표기 필터가 decision을 바꾼다. 이건 model output만의 문제가 아니다.
- user impact:
  - 실제 drift와 harmless alias가 뒤섞여 warning noise가 유지될 수 있다.

### P2. Auto-correct와 PASS_WITH_FIX patch loop가 upstream debt를 흡수하지만 줄이지는 못한다

- warning_family: `sanitize/auto-correct`, `patch pressure`
- subsystem: Stage 2 validation/finalize
- direct evidence:
  - [stage2_validation_pipeline.py#L334](C:/Users/User/Desktop/글도비/modules/core/stage2_validation_pipeline.py#L334)
  - [stage2_optimizer.py#L268](C:/Users/User/Desktop/글도비/modules/core/stage2_optimizer.py#L268)
  - [stage2_optimizer.py#L275](C:/Users/User/Desktop/글도비/modules/core/stage2_optimizer.py#L275)
  - [stage2_finalizer.py#L730](C:/Users/User/Desktop/글도비/modules/core/stage2_finalizer.py#L730)
  - [stage2_finalizer.py#L749](C:/Users/User/Desktop/글도비/modules/core/stage2_finalizer.py#L749)
  - [session_20260312_194058.log#L955](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L955)
  - [session_20260312_194058.log#L1666](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L1666)
  - [session_20260312_194058.log#L2174](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log#L2174)
- why not false positive:
  - warning frequency가 patch ratio와 함께 반복된다.
- user impact:
  - 생성 품질 debt가 patch loop와 downstream review 비용으로 전가된다.

## Model-Limited Residuals

### M1. 모든 deterministic root cause를 제거해도 최종 후보 간 문체/템포/감정 밀도 우열은 일부 모델 한계가 남는다

- status: `model-limited`
- severity: `Observation`
- 근거:
  - 현재 checker와 validator가 잡는 것은 수치, 연속성, registry, patch semantics 중심이다.
  - 그 바깥의 미세한 narrative taste는 구조화 검산으로 완전히 환원되지 않는다.

### M2. prose 안쪽의 비정형 금융 표현은 structured extractor 범위를 벗어나는 잔여 오차가 남는다

- status: `model-limited`
- severity: `Observation`
- 근거:
  - [investment_math_verifier.py#L60](C:/Users/User/Desktop/글도비/modules/core/investment_math_verifier.py#L60), [investment_math_verifier.py#L75](C:/Users/User/Desktop/글도비/modules/core/investment_math_verifier.py#L75), [investment_math_verifier.py#L143](C:/Users/User/Desktop/글도비/modules/core/investment_math_verifier.py#L143)
  - secondary LLM verifier는 없거나 실패하면 빈 리스트로 끝난다.

## Rejected Findings

### X1. "품질 경고의 대부분은 그냥 LLM 성능 문제다"

- status: `rejected`
- 이유: deterministic checker, registry, sanitize, patch, fallback 설계 증거가 이미 충분하다.

### X2. "warning 개수만 많으면 runtime failure다"

- status: `rejected`
- 이유: [runtime_audit_summary.json](C:/Users/User/Desktop/글도비/projects/000__t/logs/runtime_audit_summary.json) 는 정상 완료를 보여준다.

### X3. "000__t seed evidence는 샘플 하나라서 의미 없다"

- status: `rejected`
- 이유: sample은 하나지만 code surface cross-check는 시스템 전역 모듈까지 확장됐다.

## Evidence Ledger

| id | warning_family | subsystem | claim | status | severity | confidence_delta |
| --- | --- | --- | --- | --- | --- | --- |
| QW-01 | numeric/advisory | Stage 2 candidate validation | advisory-only gating debt exists | confirmed-improvable | P1 | +6 |
| QW-02 | selection/fallback semantics | Director compare | fallback can misclassify failure as PASS | confirmed-improvable | P1 | +5 |
| QW-03 | entity/registry | Director continuity | registry and alias rules shape warnings | confirmed-improvable | P2 | +4 |
| QW-04 | sanitize/patch pressure | Stage 2 finalize | auto-correct and patch loop absorb debt | confirmed-improvable | P2 | +4 |
| QW-05 | narrative ranking | multi-candidate selection | some taste judgment remains model-limited | model-limited | Observation | -2 |
| QW-06 | free-form finance prose | investment verifier | some residual recall remains model-limited | model-limited | Observation | -2 |
| QW-07 | blanket LLM blame | whole system | warning families are mostly model weakness | rejected | Observation | +2 |
| QW-08 | blanket instability | runtime | warnings imply runtime failure | rejected | Observation | +2 |

## Confidence Ledger

- 시작점: `70`
- seed evidence inventory 완료: `+10`
- code surface 2중 근거 확보: `+10`
- false-positive 제거 완료: `+5`
- confirmed-improvable vs model-limited 분리 완료: `+5`
- rerun/live proof 미실시: `-5`

최종 확신도: `95%`

## Final Conclusion

최종 판정:

- `P0 = 0`
- `P1 = 2`
- `P2 = 2`
- `Observation = 2`

핵심 결론은 `품질 경고를 LLM 성능 문제로만 닫으면 오판`이라는 점이다. 우선순위는 아래 순서가 맞다.

1. arithmetic/NS-3-B advisory를 hard gate 또는 score floor로 승격
2. Director compare fallback을 PASS가 아니라 retry/fail-closed 쪽으로 재설계
3. entity registry/alias/threshold를 재정비
4. auto-correct와 patch ratio를 root-cause 관측 지표로 승격

이번 문서는 read-only 전수조사 결과이며, 코드 수정과 테스트 실행은 수행하지 않았다.
