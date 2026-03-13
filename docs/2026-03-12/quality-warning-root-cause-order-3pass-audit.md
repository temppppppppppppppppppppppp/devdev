# Quality Warning Root Cause Order 3-Pass Audit

- 작성일: 2026-03-12
- 대상 SSOT: [quality-warning-root-cause-full-survey-execution-order-ssot.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/quality-warning-root-cause-full-survey-execution-order-ssot.md)
- 조사 모드: static / read-only
- 최종 상태: closed
- 최종 확신도: `95%`

## Executive Summary

이번 오더 문서는 품질 경고를 곧바로 `LLM 성능 탓`으로 환원하지 않고, 시스템적으로 개선 가능한 root cause를 먼저 전량 조사하도록 설계되어 있다. `000__t` seed evidence와 실제 코드 surface를 대조한 결과, 이 방향은 충분히 정당하다.

왜냐하면 현재 코드와 로그에는 이미 아래와 같은 비-LLM 축이 명시적으로 존재하기 때문이다.

- numeric advisory / arithmetic checker
- entity continuity / registry / 약칭 필터
- auto-correct / sanitize / forced location sync
- patch ratio threshold / PASS_WITH_FIX 재심사 컨텍스트
- director fallback 정책

즉, 품질 경고를 `LLM이 못함` 하나로 닫는 것은 오탐 가능성이 높다.

## 1. Pass 1 - 사실 수집

### P1-1. seed evidence가 실제로 비-LLM 원인을 시사한다

직접 근거:

- [session_20260312_194058.log](C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260312_194058.log)
  - `TF-47` 모순 경고
  - `V61` Entity 일관성 WARNING/REJECT
  - `[F-2] InPlace Arc 변경 비율 > 30%`
  - `[V60.25] Auto-correct`
  - `[NS-3-B] Director advisory generated`
  - `[F] Investment advisory generated`

판정:

- `confirmed`

해석:

- 로그 자체가 이미 “경고는 생성 모델 출력 외에도 검산기/연속성기/patch pressure와 연결된다”는 구조를 보여준다.

### P1-2. 오더 문서 버킷은 실제 코드 surface와 맞물린다

직접 근거:

- [four_phase_arc_generator.py](C:/Users/User/Desktop/글도비/modules/domain/agents/four_phase_arc_generator.py): `NS-3-B`, investment advisory, candidate pre-sanitize, forced location
- [director_ensemble.py](C:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py): `TF-47`, fallback semantics
- [director_continuity.py](C:/Users/User/Desktop/글도비/modules/domain/agents/director_continuity.py): `V61` entity mismatch filter
- [stage2_finalizer.py](C:/Users/User/Desktop/글도비/modules/core/stage2_finalizer.py): `InPlace Arc 변경 비율`, PASS_WITH_FIX 재심사 patch context

판정:

- `confirmed`

해석:

- 버킷 Q1~Q8은 추상적 구호가 아니라 실제 producer/validator/finalizer surface에 닿아 있다.

## 2. Pass 2 - 교차 검증

### P2-1. `LLM 탓`을 최후 분류로 미루는 규칙은 타당하다

교차 근거:

- 로그에는 deterministic checker/advisory가 이미 다수 등장한다.
- 코드에는 numeric/entity/patch/fallback 로직이 이미 존재한다.

판정:

- `confirmed`

해석:

- 이 상태에서 품질 경고를 곧바로 `모델 문제`로 내리면 구조적 개선 기회를 놓친다.

### P2-2. seed evidence는 한 프로젝트에 묶여 있지만, 문서 범위는 시스템 전역으로 확장 가능하다

교차 근거:

- seed evidence는 [projects/000__t](C:/Users/User/Desktop/글도비/projects/000__t) 이다.
- 그러나 매핑된 코드 surface는 Stage 2/3/4 전역 모듈이다.

판정:

- `confirmed`

해석:

- 특정 프로젝트 로그를 발판으로 쓰되, 조사 프레임은 시스템 전역 root cause 조사로 올리는 것이 맞다.

### P2-3. 오더 문서는 “지금 바로 수정하자”가 아니라 “먼저 분류 체계를 잠그자”에 충실하다

교차 근거:

- SSOT가 명시적으로 `코드 수정 금지`, `테스트 실행 금지`, `실행은 후속 지시`를 선언한다.
- 버킷과 판정 규칙이 먼저 고정되어 있다.

판정:

- `confirmed`

해석:

- 현재 사용자 패턴과도 일치한다. 문서가 실행 기준을 먼저 잠그는 용도에 맞다.

## 3. Pass 3 - 오탐 제거

### R1. "이번 품질 경고는 대부분 그냥 모델 성능 부족이다"

기각 사유:

- 코드에 numeric/entity/patch/fallback/systemic surface가 이미 존재한다.
- seed evidence도 그 surface들을 실제로 밟고 있다.

상태:

- `rejected`

### R2. "경고 로그가 많으니 시스템은 전체적으로 무조건 불안정하다"

기각 사유:

- seed evidence는 종료 자체로는 정상이며, 경고의 종류가 특정 family에 집중돼 있다.
- blanket failure claim으로 일반화할 근거는 부족하다.

상태:

- `rejected`

### R3. "한 프로젝트 로그만 있으니 이 오더 문서는 의미가 없다"

기각 사유:

- seed evidence는 프로젝트 하나지만, 버킷은 Stage 2/3/4 시스템 surface에 매핑돼 있다.

상태:

- `rejected`

## 4. 확정 판정

이번 감리에서 남는 결론은 아래다.

- 오더 문서는 실제 로그와 코드 surface에 기반하고 있다.
- `LLM 탓` 오탐 제거 규칙이 충분히 명시되어 있다.
- 품질 경고를 `개선 가능`과 `model-limited residual`로 분리하는 구조가 적절하다.
- blocker는 없다.

## 5. retained observation

### O1. 실제 전수조사를 하지 않은 상태라 retained finding 자체는 아직 없다

- 지금 문서는 execution order와 그 감리다.
- 실제 `개선 가능 root cause`의 retained finding은 후속 full survey에서 확정된다.

## 6. 확신도 ledger

- 기본 점수: `70`
- seed evidence baseline 반영: `+10`
- 코드 surface 교차 검증: `+10`
- `LLM 탓` 오탐 제거 규칙 확보: `+5`
- 버킷/증거 ledger/분류 체계 완성: `+5`
- 실제 전수조사 미실행: `-5`

최종 확신도: `95%`

## 7. 결론

- 상태: `execution-ready`
- blocker: 없음
- 다음 단계: 이 SSOT 기준으로 실제 `품질 경고 root cause 전수조사` 수행

이번 턴은 오더 문서와 그 3-pass 감리 문서 확정까지만 수행한다. 실제 조사와 수정은 후속 지시에서 진행한다.
